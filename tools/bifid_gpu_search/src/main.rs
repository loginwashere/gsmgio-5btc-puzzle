mod checkpoint;
mod cpu;
#[cfg(feature = "cuda")]
mod gpu;

use clap::{Parser, Subcommand};
use serde::Serialize;
#[cfg(feature = "cuda")]
use sha2::{Digest, Sha256};
use std::cmp::Ordering;
use std::path::{Path, PathBuf};
#[cfg(feature = "cuda")]
use std::sync::atomic::AtomicBool;
#[cfg(feature = "cuda")]
use std::sync::Arc;
#[cfg(feature = "cuda")]
use std::time::Instant;

#[cfg(feature = "cuda")]
use checkpoint::{Checkpoint, State};
use checkpoint::{Fingerprint, Winner};
#[cfg(feature = "cuda")]
use cpu::normalized_faed;
use cpu::{
    decode_rank, decoded_cells, score_mean, score_tail, sha256_hex, square_for_rank,
    validate_contract, QuadgramModel, EXPECTED_DECODED_SHA256, FACTORIAL_14, TARGET_PREFIX,
};

#[cfg(feature = "cuda")]
const KERNEL_SOURCE: &str = include_str!("../kernels/bifid_crib_search.cu");
#[cfg(feature = "cuda")]
const DRIVER_SOURCES: &[&str] = &[
    include_str!("main.rs"),
    include_str!("cpu.rs"),
    include_str!("checkpoint.rs"),
    include_str!("gpu.rs"),
];

#[derive(Parser, Debug)]
#[command(
    name = "bifid_gpu_search",
    version,
    about = "GPU search of the sealed-BTCSEED 14! Bifid alphabet family"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// Run mandatory CPU contract tests and, in CUDA builds, CPU/GPU cross-checks.
    SelfTest,
    /// Decode and score one rank with the independent CPU reference.
    CpuScore {
        #[arg(long)]
        rank: u64,
    },
    /// Benchmark a bounded range; does not create a resumable exhaustive checkpoint.
    Benchmark {
        #[arg(long, default_value_t = 100_000_000)]
        candidates: u64,
        #[arg(long, default_value_t = 0)]
        start: u64,
        #[arg(long, default_value_t = 2_048)]
        grid_size: u32,
        #[arg(long, default_value_t = 64)]
        stride: u32,
        #[arg(long, default_value_t = 100)]
        retain_block_winners: usize,
        #[arg(long)]
        output: Option<PathBuf>,
        #[arg(long, default_value_t = false)]
        skip_self_test: bool,
    },
    /// Run or resume a rank interval. Full 14! launch requires explicit invocation.
    Search {
        #[arg(long, default_value_t = 0)]
        start: u64,
        #[arg(long, default_value_t = FACTORIAL_14)]
        end_exclusive: u64,
        #[arg(long, default_value_t = 2_048)]
        grid_size: u32,
        #[arg(long, default_value_t = 64)]
        stride: u32,
        #[arg(long, default_value_t = 1_000)]
        retain_block_winners: usize,
        #[arg(long, default_value = "checkpoints/bifid_14factorial.json")]
        checkpoint: PathBuf,
        #[arg(long, default_value = "output/bifid_14factorial_result.json")]
        output: PathBuf,
        #[arg(long, default_value_t = false)]
        skip_self_test: bool,
    },
}

#[derive(Clone, Debug, Serialize)]
struct DetailedWinner {
    rank: u64,
    score_total: f32,
    score_mean: f64,
    square: String,
    decoded_sha256: String,
    decoded_prefix_64: String,
    tail_prefix_64: String,
    starts_with_btcseed: bool,
}

#[derive(Debug, Serialize)]
struct RunReport {
    tool: &'static str,
    mode: String,
    device: String,
    range_start: u64,
    range_end_exclusive: u64,
    candidates_processed_this_run: u64,
    elapsed_seconds: f64,
    candidates_per_second: f64,
    projected_full_14factorial_seconds: Option<f64>,
    projected_full_14factorial_hours: Option<f64>,
    exact_global_winner_for_completed_range: Option<DetailedWinner>,
    retained_block_winners: Vec<DetailedWinner>,
    shortlist_is_exact_top_k: bool,
    fingerprint: Fingerprint,
    interrupted: bool,
}

#[cfg(feature = "cuda")]
fn source_hash(parts: &[&str]) -> String {
    let mut hash = Sha256::new();
    for part in parts {
        hash.update(part.as_bytes());
        hash.update([0u8]);
    }
    hex::encode(hash.finalize())
}

#[cfg(feature = "cuda")]
fn fingerprint(model: &QuadgramModel, cells: &[u8], range_start: u64, end: u64) -> Fingerprint {
    Fingerprint {
        version: 1,
        family: format!(
            "bifid_14factorial_fixed_source_cells_lexicographic;range_start={range_start}"
        ),
        range_end_exclusive: end,
        faed_sha256: sha256_hex(&normalized_faed()),
        decoded_cells_sha256: sha256_hex(cells),
        quadgram_sha256: model.source_sha256.clone(),
        kernel_sha256: sha256_hex(KERNEL_SOURCE.as_bytes()),
        driver_sha256: source_hash(DRIVER_SOURCES),
        cuda_arch: option_env!("BIFID_CUDA_ARCH")
            .unwrap_or("cpu-only")
            .to_string(),
        score: "tail[7:];mean_log10_english_quadgram;f32_accumulation".into(),
    }
}

fn compare_winners(left: &Winner, right: &Winner) -> Ordering {
    right
        .score_total
        .partial_cmp(&left.score_total)
        .unwrap_or(Ordering::Equal)
        .then_with(|| left.rank.cmp(&right.rank))
}

fn merge_winners(
    retained: &mut Vec<Winner>,
    incoming: impl IntoIterator<Item = Winner>,
    limit: usize,
) {
    retained.extend(incoming);
    retained.sort_by(compare_winners);
    retained.dedup_by_key(|winner| winner.rank);
    retained.truncate(limit.max(1));
}

fn detail(winner: &Winner, tail_len: usize) -> DetailedWinner {
    let decoded = decode_rank(winner.rank);
    DetailedWinner {
        rank: winner.rank,
        score_total: winner.score_total,
        score_mean: score_mean(winner.score_total, tail_len),
        square: String::from_utf8(square_for_rank(winner.rank).to_vec()).unwrap(),
        decoded_sha256: sha256_hex(decoded.as_bytes()),
        decoded_prefix_64: decoded.chars().take(64).collect(),
        tail_prefix_64: decoded.chars().skip(TARGET_PREFIX.len()).take(64).collect(),
        starts_with_btcseed: decoded.starts_with(TARGET_PREFIX),
    }
}

#[cfg(feature = "cuda")]
fn write_report(path: &Path, report: &RunReport) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let rendered = serde_json::to_string_pretty(report)? + "\n";
    std::fs::write(path, rendered)?;
    Ok(())
}

fn cpu_self_test() {
    validate_contract();
    let model = QuadgramModel::load_embedded();
    assert_eq!(model.logs.len(), 390_625);
    assert_eq!(model.source_sha256.len(), 64);
    assert!(model.floor < -8.0);
    let cells = decoded_cells();
    let tail = &cells[TARGET_PREFIX.len()..];
    assert_eq!(tail.len(), 563);
    for rank in [0, 1, 2, 12_345, FACTORIAL_14 - 1] {
        let score = score_tail(rank, &model, tail);
        assert!(score.is_finite());
        assert!(decode_rank(rank).starts_with(TARGET_PREFIX));
    }
    assert_eq!(
        sha256_hex(decode_rank(0).as_bytes()),
        EXPECTED_DECODED_SHA256
    );
}

#[cfg(feature = "cuda")]
fn gpu_self_test() -> Result<(), Box<dyn std::error::Error>> {
    cpu_self_test();
    let model = QuadgramModel::load_embedded();
    let cells = decoded_cells();
    let tail = &cells[TARGET_PREFIX.len()..];
    let gpu = gpu::GpuSearcher::new(tail, &model.logs)?;
    eprintln!("[self-test] GPU: {}", gpu.device_name()?);
    for rank in [0, 1, 2, 12_345, FACTORIAL_14 - 1] {
        let expected = score_tail(rank, &model, tail);
        let observed = gpu.score_one(rank)?;
        if observed.rank != rank || observed.valid == 0 || (observed.score - expected).abs() > 0.05
        {
            return Err(format!(
                "CPU/GPU mismatch at rank {rank}: CPU={expected}, GPU={observed:?}"
            )
            .into());
        }
    }

    let replay = |gpu: &gpu::GpuSearcher| -> Result<Winner, Box<dyn std::error::Error>> {
        let interrupted = AtomicBool::new(false);
        let mut winners = Vec::new();
        gpu.scan(0, 10_000, 8, 8, &interrupted, |_start, _count, rows| {
            merge_winners(
                &mut winners,
                rows.iter().filter(|row| row.valid != 0).map(|row| Winner {
                    rank: row.rank,
                    score_total: row.score,
                }),
                1,
            );
            Ok(())
        })?;
        winners
            .into_iter()
            .next()
            .ok_or_else(|| "empty replay winner".into())
    };
    let first = replay(&gpu)?;
    let second = replay(&gpu)?;
    if first.rank != second.rank || first.score_total.to_bits() != second.score_total.to_bits() {
        return Err(format!("deterministic GPU replay mismatch: {first:?} vs {second:?}").into());
    }
    let mut cpu_best = Winner {
        rank: 0,
        score_total: score_tail(0, &model, tail),
    };
    for rank in 1..10_000 {
        let candidate = Winner {
            rank,
            score_total: score_tail(rank, &model, tail),
        };
        if compare_winners(&candidate, &cpu_best) == Ordering::Less {
            cpu_best = candidate;
        }
    }
    if first.rank != cpu_best.rank || (first.score_total - cpu_best.score_total).abs() > 0.05 {
        return Err(
            format!("GPU reduction/range mismatch: GPU={first:?}, CPU={cpu_best:?}").into(),
        );
    }
    eprintln!("[self-test] CPU/GPU probes and deterministic replay PASSED");
    Ok(())
}

#[cfg(not(feature = "cuda"))]
fn gpu_self_test() -> Result<(), Box<dyn std::error::Error>> {
    cpu_self_test();
    eprintln!("[self-test] CPU contract PASSED (binary built without CUDA feature)");
    Ok(())
}

#[cfg(feature = "cuda")]
#[allow(clippy::too_many_arguments)]
fn execute_gpu_range(
    mode: &str,
    start: u64,
    end: u64,
    grid_size: u32,
    stride: u32,
    retain_limit: usize,
    checkpoint_path: Option<&Path>,
    output_path: Option<&Path>,
) -> Result<RunReport, Box<dyn std::error::Error>> {
    if start >= end || end > FACTORIAL_14 {
        return Err(
            format!("invalid range [{start}, {end}); family ends at {FACTORIAL_14}").into(),
        );
    }
    let model = QuadgramModel::load_embedded();
    let cells = decoded_cells();
    let tail = &cells[TARGET_PREFIX.len()..];
    let fingerprint = fingerprint(&model, &cells, start, end);
    let checkpoint = checkpoint_path.map(Checkpoint::new);
    let mut retained = Vec::new();
    let mut resume = start;
    if let Some(checkpoint) = &checkpoint {
        if let Some(state) = checkpoint.load(&fingerprint)? {
            if state.next_rank < start || state.next_rank > end {
                return Err("checkpoint next_rank lies outside requested range".into());
            }
            resume = state.next_rank;
            retained = state.block_winners;
            eprintln!(
                "[resume] next rank {resume}; {} retained block winners",
                retained.len()
            );
        }
    }

    let gpu = gpu::GpuSearcher::new(tail, &model.logs)?;
    let device = gpu.device_name()?;
    eprintln!("[gpu] {device}");
    eprintln!(
        "[range] {resume}..{end} grid={grid_size} block={} stride={stride}",
        gpu::BLOCK_SIZE
    );
    let interrupted = Arc::new(AtomicBool::new(false));
    {
        let interrupted = Arc::clone(&interrupted);
        ctrlc::set_handler(move || {
            eprintln!("\n[interrupt] stopping after in-flight GPU batch");
            interrupted.store(true, std::sync::atomic::Ordering::SeqCst);
        })?;
    }
    let timer = Instant::now();
    let expected = end - resume;
    let completed = gpu.scan(
        resume,
        end,
        grid_size,
        stride,
        &interrupted,
        |batch_start, batch_count, rows| {
            merge_winners(
                &mut retained,
                rows.iter().filter(|row| row.valid != 0).map(|row| Winner {
                    rank: row.rank,
                    score_total: row.score,
                }),
                retain_limit,
            );
            let next_rank = batch_start + batch_count;
            if let Some(checkpoint) = &checkpoint {
                checkpoint.save(&State {
                    fingerprint: fingerprint.clone(),
                    next_rank,
                    block_winners: retained.clone(),
                })?;
            }
            let progressed = next_rank - resume;
            let elapsed = timer.elapsed().as_secs_f64().max(f64::EPSILON);
            eprintln!(
                "[progress] {progressed}/{expected} ({:.2}%) {:.3} M/s",
                progressed as f64 * 100.0 / expected.max(1) as f64,
                progressed as f64 / elapsed / 1_000_000.0
            );
            Ok(())
        },
    )?;
    let elapsed = timer.elapsed().as_secs_f64();
    let processed = completed.saturating_sub(resume);
    let rate = processed as f64 / elapsed.max(f64::EPSILON);
    retained.sort_by(compare_winners);
    let detailed: Vec<_> = retained
        .iter()
        .map(|winner| detail(winner, tail.len()))
        .collect();
    let report = RunReport {
        tool: "bifid_gpu_search",
        mode: mode.into(),
        device,
        range_start: resume,
        range_end_exclusive: completed,
        candidates_processed_this_run: processed,
        elapsed_seconds: elapsed,
        candidates_per_second: rate,
        projected_full_14factorial_seconds: (rate > 0.0).then_some(FACTORIAL_14 as f64 / rate),
        projected_full_14factorial_hours: (rate > 0.0)
            .then_some(FACTORIAL_14 as f64 / rate / 3600.0),
        exact_global_winner_for_completed_range: detailed.first().cloned(),
        retained_block_winners: detailed,
        shortlist_is_exact_top_k: false,
        fingerprint,
        interrupted: completed < end,
    };
    if let Some(path) = output_path {
        write_report(path, &report)?;
    }
    Ok(report)
}

#[cfg(not(feature = "cuda"))]
fn execute_gpu_range(
    _mode: &str,
    _start: u64,
    _end: u64,
    _grid_size: u32,
    _stride: u32,
    _retain_limit: usize,
    _checkpoint_path: Option<&Path>,
    _output_path: Option<&Path>,
) -> Result<RunReport, Box<dyn std::error::Error>> {
    Err("binary built without CUDA; use Dockerfile.cuda or --features cuda".into())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("error: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.command {
        Command::SelfTest => gpu_self_test(),
        Command::CpuScore { rank } => {
            if rank >= FACTORIAL_14 {
                return Err(format!("rank must be below {FACTORIAL_14}").into());
            }
            cpu_self_test();
            let model = QuadgramModel::load_embedded();
            let cells = decoded_cells();
            let score = score_tail(rank, &model, &cells[TARGET_PREFIX.len()..]);
            let winner = Winner {
                rank,
                score_total: score,
            };
            println!("{}", serde_json::to_string_pretty(&detail(&winner, 563))?);
            Ok(())
        }
        Command::Benchmark {
            candidates,
            start,
            grid_size,
            stride,
            retain_block_winners,
            output,
            skip_self_test,
        } => {
            if !skip_self_test {
                gpu_self_test()?;
            }
            let end = start
                .checked_add(candidates)
                .ok_or("benchmark range overflow")?
                .min(FACTORIAL_14);
            let report = execute_gpu_range(
                "benchmark",
                start,
                end,
                grid_size,
                stride,
                retain_block_winners,
                None,
                output.as_deref(),
            )?;
            println!("{}", serde_json::to_string_pretty(&report)?);
            Ok(())
        }
        Command::Search {
            start,
            end_exclusive,
            grid_size,
            stride,
            retain_block_winners,
            checkpoint,
            output,
            skip_self_test,
        } => {
            if !skip_self_test {
                gpu_self_test()?;
            }
            let report = execute_gpu_range(
                "search",
                start,
                end_exclusive,
                grid_size,
                stride,
                retain_block_winners,
                Some(&checkpoint),
                Some(&output),
            )?;
            println!("{}", serde_json::to_string_pretty(&report)?);
            Ok(())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cpu_contract() {
        cpu_self_test();
    }

    #[test]
    fn winner_merge_keeps_exact_best() {
        let mut retained = vec![Winner {
            rank: 2,
            score_total: -10.0,
        }];
        merge_winners(
            &mut retained,
            [
                Winner {
                    rank: 1,
                    score_total: -9.0,
                },
                Winner {
                    rank: 3,
                    score_total: -11.0,
                },
            ],
            2,
        );
        assert_eq!(
            retained
                .iter()
                .map(|winner| winner.rank)
                .collect::<Vec<_>>(),
            vec![1, 2]
        );
    }
}
