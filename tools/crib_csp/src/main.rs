//! CLI driver for the Rust parity port of Phase-512D/E's exact-crib CSP.
//!
//! Fixtures are always synthetic JSON exported by
//! `tools/gsmg/phase512i_rust_parity.py` (never real FAED at this stage).
//!
//! `cell` solves one `{raw_start, pair}` cell without parallelism (step 1-2
//! of the Rust-port plan) and prints a result whose fields line up 1:1 with
//! `phase512d.search_lengths_at_start`'s Python return dict, for direct
//! diffing (see `phase512i_rust_parity.py`).
//!
//! `sweep` runs an in-process deterministic parallel batch over a
//! `{raw_start range} x {pair range}` family (step 4), mirroring
//! `phase512e_parallel_blind_crib.scan_fixture`'s raw-start-major,
//! every-pair-retained-before-advancing architecture, with a resumable
//! checkpoint.

mod csp;
mod fixture;
mod geometry;
mod sweep;

use clap::{Parser, Subcommand};
use serde::Serialize;
use std::time::Instant;

use fixture::{load_fixture, resolve_pair};

#[derive(Parser)]
#[command(name = "crib_csp")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Solve one {raw_start, pair} cell (no parallelism).
    Cell(CellArgs),
    /// Deterministic in-process parallel sweep over a start x pair range.
    Sweep(SweepArgs),
}

#[derive(clap::Args)]
struct CellArgs {
    /// Path to a fixture JSON exported by phase512i_rust_parity.py.
    #[arg(long)]
    fixture: String,
    /// Raw-stream start offset to test (matches Python's raw_start).
    #[arg(long)]
    raw_start: usize,
    /// Escape pair as two lowercase a-i letters, e.g. "gi". Defaults to the
    /// fixture's own planted pair if omitted.
    #[arg(long)]
    pair: Option<String>,
    #[arg(long, default_value_t = 2_000_000)]
    node_limit: u64,
}

#[derive(clap::Args)]
struct SweepArgs {
    #[arg(long)]
    fixture: String,
    #[arg(long, default_value_t = 0)]
    start_begin: usize,
    /// Number of raw starts to cover. Defaults to the full family:
    /// observed_length - crib_length + 1 - start_begin.
    #[arg(long)]
    start_count: Option<usize>,
    #[arg(long, default_value_t = 0)]
    pair_begin: usize,
    #[arg(long, default_value_t = 36)]
    pair_count: usize,
    #[arg(long, default_value_t = 2_000_000)]
    node_limit: u64,
    #[arg(long, default_value_t = 16)]
    workers: usize,
    /// Optional resumable checkpoint path.
    #[arg(long)]
    checkpoint: Option<String>,
}

#[derive(Serialize)]
struct HitOut {
    pattern_index: usize,
    single_letters: String,
    column_to_chunk: Vec<i64>,
    exact_truth: Option<bool>,
    nodes_for_pattern: u64,
}

#[derive(Serialize)]
struct ResultOut {
    raw_start: usize,
    pair: [char; 2],
    legal_length_pattern_count: usize,
    patterns_tested: usize,
    total_nodes: u64,
    global_node_limit: u64,
    node_limit_reached: bool,
    search_complete: bool,
    hit_count: usize,
    hits: Vec<HitOut>,
    first_hit_exact_truth: Option<bool>,
    elapsed_seconds: f64,
}

fn fail(message: impl AsRef<str>) -> ! {
    eprintln!("error: {}", message.as_ref());
    std::process::exit(1);
}

fn run_cell(args: CellArgs) {
    let started = Instant::now();
    let fix = load_fixture(&args.fixture).unwrap_or_else(|e| fail(e));
    let pair_chars = resolve_pair(&fix, &args.pair).unwrap_or_else(|e| fail(e));
    if let Err(message) =
        fixture::validate_inputs(fix.observed_bytes.len(), fix.width, &fix.crib, &pair_chars)
    {
        fail(message);
    }
    let escapes: (u8, u8) = (pair_chars[0] as u8 - b'a', pair_chars[1] as u8 - b'a');

    let shape = csp::crib_shape(&fix.crib);
    let patterns = csp::length_patterns(shape.k);

    let result = csp::search_lengths_at_start(
        &shape,
        &patterns,
        &fix.blocks,
        fix.width,
        fix.rows,
        escapes,
        args.raw_start,
        fix.observed_bytes.len(),
        args.node_limit,
        fix.truth_column_to_chunk.as_deref(),
    );

    let hits: Vec<HitOut> = result
        .hits
        .into_iter()
        .map(|h| HitOut {
            pattern_index: h.pattern_index,
            single_letters: h.single_letters,
            column_to_chunk: h.column_to_chunk,
            exact_truth: h.exact_truth,
            nodes_for_pattern: h.nodes_for_pattern,
        })
        .collect();
    let first_hit_exact_truth = hits.first().and_then(|h| h.exact_truth);

    let out = ResultOut {
        raw_start: args.raw_start,
        pair: pair_chars,
        legal_length_pattern_count: result.legal_length_pattern_count,
        patterns_tested: result.patterns_tested,
        total_nodes: result.total_nodes,
        global_node_limit: args.node_limit,
        node_limit_reached: result.node_limit_reached,
        search_complete: result.search_complete,
        hit_count: hits.len(),
        hits,
        first_hit_exact_truth,
        elapsed_seconds: started.elapsed().as_secs_f64(),
    };
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}

fn run_sweep(args: SweepArgs) {
    let fix = load_fixture(&args.fixture).unwrap_or_else(|e| fail(e));
    let crib_raw_span_minimum = fix.crib.chars().count();
    let maximum_start = fix
        .observed_bytes
        .len()
        .saturating_sub(crib_raw_span_minimum);
    let start_count = args
        .start_count
        .unwrap_or_else(|| (maximum_start + 1).saturating_sub(args.start_begin));

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.workers.max(1))
        .build_global()
        .unwrap_or_else(|e| fail(format!("failed to build thread pool: {e}")));

    let sweep_args = sweep::SweepArgs {
        start_begin: args.start_begin,
        start_count,
        pair_begin: args.pair_begin,
        pair_count: args.pair_count,
        node_limit: args.node_limit,
        checkpoint_path: args.checkpoint,
    };
    let checkpoint = sweep::run_sweep(&fix, sweep_args).unwrap_or_else(|e| fail(e));
    println!("{}", serde_json::to_string_pretty(&checkpoint).unwrap());
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Command::Cell(args) => run_cell(args),
        Command::Sweep(args) => run_sweep(args),
    }
}
