mod blobs;
mod checkpoint;
mod cpu_oracle;
mod forms;
mod output;

#[cfg(feature = "cuda")]
mod gpu;
#[cfg(feature = "cuda")]
mod selftest;

use clap::Parser;
use std::io::BufRead;
#[cfg(feature = "cuda")]
use std::io::Write;
use std::path::PathBuf;
#[cfg(feature = "cuda")]
use std::sync::Arc;

/// GSMG.IO puzzle AES/KDF oracle -- GPU-accelerated Phase-1 (AES-CBC) port of
/// tools/gsmg/cb_common.py's aes_try_open_bytes(). See doc/ for scope notes;
/// any hit here still needs re-verification through the Python oracle before
/// being treated as real.
#[derive(Parser, Debug)]
#[command(name = "gpu_oracle")]
struct Cli {
    /// Plain wordlist file, one base candidate per line (e.g.
    /// wordlists/gsmg/curated_v2_core.txt, or a fresh combination list).
    #[arg(long)]
    wordlist: Option<PathBuf>,

    /// Apply the "enter" newline-variant forms (form+"\n", form+"\r\n"),
    /// matching cb_common.keystr_forms(newline_variants=True).
    #[arg(long, default_value_t = false)]
    newline_variants: bool,

    /// Apply the trailing-space whitespace-variant form.
    #[arg(long, default_value_t = false)]
    whitespace_variants: bool,

    /// Checkpoint file (JSONL, fingerprint-bound -- resumes only if the
    /// candidate list / blob set / variant table / kernel all match exactly).
    #[arg(long)]
    checkpoint: Option<PathBuf>,

    /// Hit output file (JSONL, append-only).
    #[arg(long, default_value = "output/hits.jsonl")]
    output: PathBuf,

    /// Run only the mandatory correctness self-test (known-positive vector +
    /// negative cross-check against the CPU reference oracle) and exit.
    #[arg(long, default_value_t = false)]
    self_test: bool,

    /// Skip the self-test before a real run. NOT recommended -- only for
    /// re-running a sweep you've already validated this session.
    #[arg(long, default_value_t = false)]
    skip_self_test: bool,
}

fn main() {
    if let Err(e) = run() {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}

#[cfg(not(feature = "cuda"))]
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let _cli = Cli::parse();
    Err("this binary was built without --features cuda; rebuild via Dockerfile.cuda".into())
}

#[cfg(feature = "cuda")]
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    let gpu = gpu::GpuOracle::new()?;
    println!("[main] GPU device: {}", gpu.device_name()?);

    if !cli.skip_self_test {
        selftest::run(&gpu)?;
    }
    if cli.self_test {
        return Ok(());
    }

    let wordlist_path = cli.wordlist.ok_or("--wordlist is required for a real run (or pass --self-test alone)")?;
    run_sweep(&gpu, &wordlist_path, cli.newline_variants, cli.whitespace_variants, cli.checkpoint, &cli.output)?;

    Ok(())
}

#[cfg(feature = "cuda")]
fn run_sweep(
    gpu: &gpu::GpuOracle,
    wordlist_path: &PathBuf,
    newline_variants: bool,
    whitespace_variants: bool,
    checkpoint_path: Option<PathBuf>,
    output_path: &PathBuf,
) -> Result<(), Box<dyn std::error::Error>> {
    let base_lines = read_wordlist(wordlist_path)?;
    println!("[main] {} base candidates from {}", base_lines.len(), wordlist_path.display());

    // Expand every base line into its answer_forms x keystr_forms passphrase
    // set, keeping a parallel "source" label for the hit record.
    let mut candidates: Vec<String> = Vec::new();
    let mut sources: Vec<String> = Vec::new();
    for line in &base_lines {
        for form in forms::expand_candidate(line, newline_variants, whitespace_variants) {
            candidates.push(form);
            sources.push(line.clone());
        }
    }
    println!(
        "[main] expanded to {} passphrase forms (newline_variants={newline_variants}, whitespace_variants={whitespace_variants})",
        candidates.len()
    );

    let blobs = blobs::load_blobs();
    let variants = blobs::variant_table();

    if let Some(dir) = output_path.parent() {
        if !dir.as_os_str().is_empty() {
            std::fs::create_dir_all(dir)?;
        }
    }
    let writer = Arc::new(output::OutputWriter::new(output_path.to_str().ok_or("bad --output path")?)?);

    // Checkpoint: fingerprint-bound, refuses to resume against a different run.
    let (skip_indices, checkpoint) = if let Some(cp_path) = &checkpoint_path {
        let kernel_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("kernels/aes_kdf_oracle.cu");
        let driver_src_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("src");
        let fingerprint = checkpoint::compute_fingerprint(&candidates, &blobs, &variants, &kernel_path, &driver_src_dir);

        let cp = checkpoint::SweepCheckpoint::new(cp_path.to_str().ok_or("bad --checkpoint path")?);
        let existing = cp.load(&fingerprint)?;
        let skip = existing.unwrap_or_default();
        if !skip.is_empty() {
            println!("[main] resuming: {} candidates already checkpointed as done", skip.len());
        }
        let file = if skip.is_empty() { cp.init_fresh(&fingerprint)? } else { cp.open_append()? };
        (skip, Some(std::sync::Mutex::new(file)))
    } else {
        (std::collections::HashSet::new(), None)
    };

    let interrupted = Arc::new(std::sync::atomic::AtomicBool::new(false));
    {
        let interrupted = Arc::clone(&interrupted);
        ctrlc::set_handler(move || {
            eprintln!("\n[main] interrupt received, will stop after the current batch and checkpoint progress...");
            interrupted.store(true, std::sync::atomic::Ordering::SeqCst);
        })?;
    }

    let writer_ref = Arc::clone(&writer);
    let candidates_ref = &candidates;
    let sources_ref = &sources;
    let variants_ref = &variants;

    gpu.scan(
        &candidates,
        &skip_indices,
        &blobs,
        &variants,
        |hit| {
            let (kdf, key_len) = variants_ref[hit.variant_idx as usize];
            let kind_str = match hit.hit_kind {
                1 => "weak",
                2 => "strong",
                3 => "structural",
                _ => "unknown",
            };
            let record = output::Hit {
                candidate: candidates_ref[hit.candidate_idx as usize].clone(),
                candidate_source: sources_ref[hit.candidate_idx as usize].clone(),
                keystring_form: candidates_ref[hit.candidate_idx as usize].clone(),
                kdf: blobs::variant_label(kdf, key_len),
                key_bits: (key_len * 8) as u32,
                blob_tag: blobs[hit.blob_idx as usize].tag.to_string(),
                hit_kind: kind_str.to_string(),
                z_score: hit.z_score as f64,
                body_preview: String::new(),
            };
            writer_ref.write_hit(&record);
            if hit.hit_kind == 2 || hit.hit_kind == 3 {
                eprintln!(
                    "[main] STRONG/STRUCTURAL hit -- re-verify through the Python oracle before trusting this: {:?}",
                    record
                );
            }
        },
        |done, total, elapsed| {
            let rate = if elapsed > 0.0 { done as f64 / elapsed } else { 0.0 };
            eprint!(
                "\r[main] {done}/{total} candidates ({:.1}%) | {rate:.0} candidates/s | {elapsed:.0}s elapsed   ",
                100.0 * done as f64 / total.max(1) as f64
            );
            let _ = std::io::stderr().flush();
        },
        |batch_indices| {
            // Record the actual original candidate indices completed in this
            // batch -- NOT a cumulative count -- so SweepCheckpoint::load()'s
            // per-index resume logic stays correct.
            if let Some(cp) = &checkpoint {
                if let Ok(mut f) = cp.lock() {
                    for idx in batch_indices {
                        let _ = writeln!(f, "{idx}");
                    }
                    let _ = f.flush();
                }
            }
        },
        &interrupted,
    )?;

    eprintln!("\n[main] sweep complete.");
    Ok(())
}

fn read_wordlist(path: &PathBuf) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let f = std::fs::File::open(path)?;
    let reader = std::io::BufReader::new(f);
    let mut out = Vec::new();
    for line in reader.lines() {
        let line = line?;
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        out.push(trimmed.to_string());
    }
    Ok(out)
}
