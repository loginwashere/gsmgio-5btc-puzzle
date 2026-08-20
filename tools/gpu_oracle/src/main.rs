mod blobs;
mod checker;
mod checkpoint;
mod cpu_oracle;
mod crypto;
mod forms;
mod gtable;
mod keyshape;
mod output;
mod seed_cipher;
mod stream_key_check;

#[cfg(feature = "cuda")]
mod gpu;
#[cfg(feature = "cuda")]
mod secp256k1_gpu;
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
/// tools/gsmg/cb_common.py's aes_try_open_bytes(). See doc/ for scope notes.
/// A structural hit (a full dummy PKCS7 pad block, any body length that's a
/// multiple of 32 bytes -- not just SALPH/P32TRAILING's 64-byte case) is now
/// automatically address-derived and Bloom/API-checked inline (see
/// `keyshape.rs`, ported from ../../key-seeker's checker module) -- no
/// manual Python re-run needed for that case. A strong (printable) hit still needs
/// `tools/gsmg/key_shape_sweep.py` to check whether its text is itself a
/// key (hex64/WIF/BIP39 mnemonic); that classifier isn't duplicated here.
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

    /// Sensitive (mode-0600) JSONL file for structural hits' derived
    /// private keys/addresses -- see `keyshape::KeyShapeHit`.
    #[arg(long, default_value = "output/keyshape_hits.jsonl")]
    keyshape_hits: PathBuf,

    /// BLMCACHE-format Bloom cache of funded/used address hash160s. Default
    /// is this repo's copy of key-seeker's `db/addresses.hash160.bloom`
    /// (gitignored -- see .gitignore's `db/*.bloom`). Missing file is a
    /// warning, not an error: structural hits are still derived and logged,
    /// just never Bloom/API-checked.
    #[arg(long)]
    bloom_cache: Option<PathBuf>,

    /// Disable Bloom/API checking of structural hits entirely (addresses are
    /// still derived and written to --keyshape-hits).
    #[arg(long, default_value_t = false)]
    no_bloom_verify: bool,

    /// Run only the mandatory correctness self-test (known-positive vector +
    /// negative cross-check against the CPU reference oracle) and exit.
    #[arg(long, default_value_t = false)]
    self_test: bool,

    /// Skip the self-test before a real run. NOT recommended -- only for
    /// re-running a sweep you've already validated this session.
    #[arg(long, default_value_t = false)]
    skip_self_test: bool,

    /// Also (or instead, if built without --features cuda) run every
    /// CFB/OFB/CTR stream-mode candidate's decrypt through Bloom/API address
    /// checking unconditionally -- bypassing the printable/z-score gate that
    /// would otherwise silently drop a correct password whose plaintext is
    /// raw binary key material rather than text (stream modes have no PKCS7
    /// padding, so there's no structural signal to bypass it with the way
    /// CBC/ECB's full-dummy-pad-block check does). CPU-only, does not need a
    /// GPU. Bounded to each blob's first 64 bytes (the half/better_half
    /// positions) per candidate x variant x blob -- see stream_key_check.rs.
    #[arg(long, default_value_t = false)]
    stream_half_check: bool,

    /// Run the opt-in SEED-CBC variant family (4 variants: one per KDF kind,
    /// fixed 128-bit key) instead of the default 60-variant AES table.
    /// Thematically motivated by Phase 253 (gsmg.io/theseedisplanted,
    /// IZLKESEEDQPPEN) but never merged into the default sweep -- same
    /// "opt-in, don't silently expand existing sweeps" discipline. See
    /// blobs::seed_variant_table().
    #[arg(long, default_value_t = false)]
    seed_cbc: bool,
}

fn main() {
    if let Err(e) = run() {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}

#[cfg(not(feature = "cuda"))]
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    if cli.stream_half_check {
        return run_stream_half_check(&cli);
    }
    Err("this binary was built without --features cuda; rebuild via Dockerfile.cuda \
         (or pass --stream-half-check alone for the CPU-only stream-cipher Bloom \
         check, which needs no GPU)"
        .into())
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

    if cli.wordlist.is_none() {
        return Err("--wordlist is required for a real run (or pass --self-test alone)".into());
    }
    run_sweep(&gpu, &cli)?;

    if cli.stream_half_check {
        run_stream_half_check(&cli)?;
    }

    Ok(())
}

#[cfg(feature = "cuda")]
fn run_sweep(gpu: &gpu::GpuOracle, cli: &Cli) -> Result<(), Box<dyn std::error::Error>> {
    let (candidates, sources) = expand_wordlist_candidates(cli)?;

    let blobs = blobs::load_blobs();
    let variants = if cli.seed_cbc { blobs::seed_variant_table() } else { blobs::variant_table() };

    if let Some(dir) = cli.output.parent() {
        if !dir.as_os_str().is_empty() {
            std::fs::create_dir_all(dir)?;
        }
    }
    let writer = Arc::new(output::OutputWriter::new(cli.output.to_str().ok_or("bad --output path")?)?);

    let (secp, bloom_checker, keyshape_writer) = setup_keyshape(cli)?;
    let bloom_checker_ref: Option<&dyn checker::Checker> =
        bloom_checker.as_ref().map(|c| c as &dyn checker::Checker);

    // Checkpoint: fingerprint-bound, refuses to resume against a different run.
    let (skip_indices, checkpoint) = if let Some(cp_path) = &cli.checkpoint {
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
    let blobs_ref = &blobs;

    gpu.scan(
        &candidates,
        &skip_indices,
        &blobs,
        &variants,
        bloom_checker.as_ref().map(|vc| vc.bloom()),
        |hit| {
            let (kdf, key_len, mode) = variants_ref[hit.variant_idx as usize];
            let kind_str = match hit.hit_kind {
                1 => "weak",
                2 => "strong",
                3 => "structural",
                _ => "unknown",
            };
            let candidate = candidates_ref[hit.candidate_idx as usize].clone();
            let blob = &blobs_ref[hit.blob_idx as usize];

            // Recompute the exact (candidate, variant, blob) decrypt on the
            // CPU reference oracle for strong/structural hits: the CUDA
            // kernel deliberately never copies the plaintext body back (see
            // output.rs), so this is the only way to get real bytes to
            // classify. Rare by construction -- only fires once the kernel's
            // own z-score/structural gate already passed -- so the CPU
            // recompute cost here is negligible.
            let body = if hit.hit_kind == 2 || hit.hit_kind == 3 {
                cpu_oracle::try_open(candidate.as_bytes(), kdf, key_len as usize, mode, &blob.salt, &blob.ciphertext).1
            } else {
                None
            };

            let record = output::Hit {
                candidate: candidate.clone(),
                candidate_source: sources_ref[hit.candidate_idx as usize].clone(),
                keystring_form: candidate.clone(),
                kdf: blobs::variant_label(kdf, key_len, mode),
                key_bits: (key_len * 8) as u32,
                blob_tag: blob.tag.to_string(),
                hit_kind: kind_str.to_string(),
                z_score: hit.z_score as f64,
                body_preview: body
                    .as_deref()
                    .map(|b| String::from_utf8_lossy(&b[..b.len().min(64)]).into_owned())
                    .unwrap_or_default(),
            };
            writer_ref.write_hit(&record);

            match (hit.hit_kind, &body) {
                (3, Some(body)) => {
                    // Structural shape (complete PKCS7 padding block; any
                    // body length that's a multiple of 32 bytes) is
                    // guaranteed by the kernel already -- no further
                    // classification needed, straight to chunked address
                    // derivation + Bloom/API. See keyshape.rs.
                    let variant_label = blobs::variant_label(kdf, key_len, mode);
                    let confirmed = keyshape::process_structural_hit(
                        &secp, bloom_checker_ref, &keyshape_writer, blob.tag, &variant_label, &candidate, body,
                    );
                    if confirmed > 0 {
                        eprintln!(
                            "[main] *** {confirmed} CONFIRMED FUNDED ADDRESS(ES) from a structural hit -- see {} ***",
                            cli.keyshape_hits.display()
                        );
                    } else {
                        eprintln!("[main] structural hit, Bloom/API-checked, 0 funded: {record:?}");
                    }
                }
                (2, Some(_)) => {
                    // Readable body: could itself be a hex64/WIF/BIP39
                    // mnemonic private key, but that classifier lives in
                    // tools/gsmg/key_shape_sweep.py, not duplicated here.
                    eprintln!(
                        "[main] strong hit -- check body_preview for key-shaped text via \
                         tools/gsmg/key_shape_sweep.py: {record:?}"
                    );
                }
                (2, None) | (3, None) => {
                    eprintln!(
                        "[main] STRONG/STRUCTURAL hit but the CPU reference oracle did not \
                         reproduce it -- kernel/CPU disagreement, needs investigation: {record:?}"
                    );
                }
                _ => {}
            }
        },
        |stream_hit| {
            let (kdf, key_len, mode) = variants_ref[stream_hit.variant_idx as usize];
            let variant_label = blobs::variant_label(kdf, key_len, mode);
            let blob_tag = blobs_ref[stream_hit.blob_idx as usize].tag;
            let candidate = &candidates_ref[stream_hit.candidate_idx as usize];
            let address_type = if stream_hit.address_type == 0 { "compressed" } else { "uncompressed" };
            let confirmed = keyshape::record_gpu_stream_hit(
                bloom_checker_ref,
                &keyshape_writer,
                blob_tag,
                &variant_label,
                candidate,
                stream_hit.chunk_index as usize,
                address_type,
                stream_hit.private_key,
                stream_hit.hash160,
            );
            if confirmed > 0 {
                eprintln!(
                    "[main] *** {confirmed} CONFIRMED FUNDED ADDRESS(ES) from a stream-mode Bloom hit -- see {} ***",
                    cli.keyshape_hits.display()
                );
            } else {
                eprintln!(
                    "[main] stream-mode Bloom hit (false positive after API check): {blob_tag} {variant_label} \
                     candidate={candidate:?} chunk={} type={address_type}",
                    stream_hit.chunk_index
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

/// Where to look for the Bloom cache when `--bloom-cache` isn't passed. Two
/// deployments need two different defaults, since `env!("CARGO_MANIFEST_DIR")`
/// is baked in at *compile* time and means nothing at *run* time in a
/// container built from Dockerfile.cuda (there it's `/build`, a path that
/// doesn't exist in the runtime stage at all):
///
/// * Docker (the documented deployment, see Dockerfile.cuda): WORKDIR is
///   `/data`, and `docker run -v host/db:/data/db:ro` mounts the cache at
///   `/data/db/addresses.hash160.bloom` -- a path relative to the *runtime*
///   working directory, checked first.
/// * Local `cargo run --features cuda` from `tools/gpu_oracle/`: falls back
///   to the compile-time-known path from the crate to the repo-root `db/`
///   this project's own copy of key-seeker's Bloom cache lives in (see
///   .gitignore's `db/*.bloom`).
fn default_bloom_cache_path() -> PathBuf {
    let cwd_relative = PathBuf::from("db/addresses.hash160.bloom");
    if cwd_relative.exists() {
        return cwd_relative;
    }
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../db/addresses.hash160.bloom")
}

#[cfg(test)]
mod default_bloom_cache_path_tests {
    use super::*;

    /// Falls back to the repo-root path when no `db/addresses.hash160.bloom`
    /// exists relative to cwd (true for `cargo test`'s cwd, the crate root)
    /// -- and that fallback must resolve to the real file this project
    /// copied from key-seeker (see .gitignore's `db/*.bloom`), not just any
    /// path.
    #[test]
    fn falls_back_to_repo_root_path_when_no_cwd_relative_file() {
        assert!(!PathBuf::from("db/addresses.hash160.bloom").exists());
        let resolved = default_bloom_cache_path();
        assert!(resolved.ends_with("db/addresses.hash160.bloom"));
        assert!(resolved.exists(), "{resolved:?} should be this repo's copied Bloom cache");
    }

    /// Docker's case: WORKDIR is a plain directory with `db/` mounted under
    /// it -- a `db/addresses.hash160.bloom` relative to cwd must be found
    /// and preferred over the compile-time repo-root fallback. Single test
    /// that touches the process cwd; every other test in this binary uses
    /// absolute paths (tempfile, or CARGO_MANIFEST_DIR-derived), so this
    /// doesn't race with them.
    #[test]
    fn prefers_cwd_relative_file_when_present() {
        let dir = tempfile::tempdir().unwrap();
        std::fs::create_dir(dir.path().join("db")).unwrap();
        let fake_bloom = dir.path().join("db/addresses.hash160.bloom");
        std::fs::write(&fake_bloom, b"not a real bloom file, just needs to exist").unwrap();

        let original_cwd = std::env::current_dir().unwrap();
        std::env::set_current_dir(dir.path()).unwrap();
        let resolved = default_bloom_cache_path();
        std::env::set_current_dir(original_cwd).unwrap();

        assert_eq!(resolved, PathBuf::from("db/addresses.hash160.bloom"));
    }
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

/// Reads `--wordlist` and expands every base line into its answer_forms x
/// keystr_forms passphrase set, keeping a parallel "source" label for the
/// hit record. Shared by `run_sweep` (GPU) and `run_stream_half_check`
/// (CPU-only) so both operate over the exact same candidate set for a given
/// `--wordlist`/`--newline-variants`/`--whitespace-variants` combination.
fn expand_wordlist_candidates(cli: &Cli) -> Result<(Vec<String>, Vec<String>), Box<dyn std::error::Error>> {
    let wordlist_path = cli.wordlist.as_ref().ok_or("--wordlist is required")?;
    let base_lines = read_wordlist(wordlist_path)?;
    println!("[main] {} base candidates from {}", base_lines.len(), wordlist_path.display());

    let mut candidates: Vec<String> = Vec::new();
    let mut sources: Vec<String> = Vec::new();
    for line in &base_lines {
        for form in forms::expand_candidate(line, cli.newline_variants, cli.whitespace_variants) {
            candidates.push(form);
            sources.push(line.clone());
        }
    }
    println!(
        "[main] expanded to {} passphrase forms (newline_variants={}, whitespace_variants={})",
        candidates.len(), cli.newline_variants, cli.whitespace_variants
    );
    Ok((candidates, sources))
}

/// Sets up the pieces shared by both Bloom/API consumers (`keyshape::
/// process_structural_hit` via `run_sweep`'s structural hits, and
/// `stream_key_check::run`): the keyshape JSONL writer, the secp256k1
/// context, and the Bloom checker (`None` if `--no-bloom-verify` or the
/// cache failed to load -- a warning, not a hard error, in either case).
fn setup_keyshape(
    cli: &Cli,
) -> Result<(secp256k1::Secp256k1<secp256k1::All>, Option<checker::KnownTargetsChecker>, keyshape::KeyShapeWriter), Box<dyn std::error::Error>>
{
    if let Some(dir) = cli.keyshape_hits.parent() {
        if !dir.as_os_str().is_empty() {
            std::fs::create_dir_all(dir)?;
        }
    }
    let keyshape_writer =
        keyshape::KeyShapeWriter::new(cli.keyshape_hits.to_str().ok_or("bad --keyshape-hits path")?)?;

    let secp = secp256k1::Secp256k1::new();
    let bloom_checker: Option<checker::KnownTargetsChecker> = if cli.no_bloom_verify {
        None
    } else {
        let bloom_path = cli.bloom_cache.clone().unwrap_or_else(default_bloom_cache_path);
        match checker::BloomChecker::load_from_file(bloom_path.to_string_lossy().as_ref()) {
            Ok(mut bloom) => {
                println!("[main] Bloom cache loaded: {}", bloom_path.display());
                // Fold in the prize pubkey's EC "neighbors, half and
                // double" (Phase 331) so the GPU's on-device Bloom
                // pre-filter (bloom_check_key_chunks) can flag them too --
                // see checker::known_targets for what these are and why.
                let extras = checker::known_targets::all_hash160s();
                bloom.insert_extra(&extras);
                println!("[main] folded in {} known EC-derived target address(es) (see checker::known_targets)", extras.len());
                Some(checker::KnownTargetsChecker::new(checker::VerifiedBloomChecker::new(bloom)))
            }
            Err(e) => {
                eprintln!(
                    "[main] WARNING: could not load Bloom cache at {} ({e}) -- structural/stream hits \
                     will still be derived and logged, but never Bloom/API-checked. Pass \
                     --bloom-cache <path> or --no-bloom-verify to silence this.",
                    bloom_path.display()
                );
                None
            }
        }
    };
    Ok((secp, bloom_checker, keyshape_writer))
}

/// CPU-only (no `--features cuda` needed): see `stream_key_check.rs`.
fn run_stream_half_check(cli: &Cli) -> Result<(), Box<dyn std::error::Error>> {
    let (candidates, _sources) = expand_wordlist_candidates(cli)?;
    let blobs = blobs::load_blobs();
    let (secp, bloom_checker, keyshape_writer) = setup_keyshape(cli)?;
    let bloom_checker_ref: Option<&dyn checker::Checker> =
        bloom_checker.as_ref().map(|c| c as &dyn checker::Checker);
    stream_key_check::run(&candidates, &blobs, &secp, bloom_checker_ref, &keyshape_writer);
    Ok(())
}
