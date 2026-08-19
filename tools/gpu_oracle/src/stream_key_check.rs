//! CPU-only Bloom/API check for CFB/OFB/CTR stream-mode decrypts, run
//! unconditionally (no printable/z-score gate) -- closes the blind spot
//! `cpu_oracle.rs::try_open`'s printability gate can't cover: stream modes
//! have no PKCS7 padding at all, so there is no structural signal analogous
//! to CBC/ECB's full-dummy-pad-block check. A correct password whose
//! plaintext is raw binary key material (not text) produces output that will
//! essentially never look printable, so `try_open` silently drops it as
//! `HitKind::None` -- not a bug, just the absence of any decrypt-validity
//! oracle for stream modes. The only substitute is to stop trying to
//! recognize the plaintext at all and instead ask the Bloom filter directly:
//! "does this candidate's derived address exist," which needs no signal from
//! the plaintext's shape.
//!
//! Scope is deliberately bounded to each blob's first `CHUNK_BOUND_BYTES`
//! (the `half`/`better_half` positions, matching the puzzle's own framing)
//! rather than every 32-byte-aligned chunk of the full body the way
//! `keyshape::process_structural_hit` does for CBC/ECB structural hits.
//! Checking every chunk of every stream variant (COSMIC alone would be 41
//! chunks) would multiply an already-large candidate x variant x blob grid
//! by another ~20x for chunks beyond position 1, for a hypothesis
//! (`half`/`better_half`-shaped raw key material specifically) that's
//! already the one this whole pipeline was built around -- not a blanket
//! "check everything" sweep.
//!
//! The AES decrypts are cheap either way; the real cost is the secp256k1
//! point multiplication per chunk. Built with `--features cuda`, that runs
//! on GPU via `secp256k1_gpu.rs` (falling back to CPU only if no GPU is
//! actually reachable at runtime); a CPU-only build always uses the
//! rayon-parallelized CPU path (`run_cpu` below). A plain CPU loop measured
//! ~176 candidates/s aggregate for the full medium_curated_all.txt corpus on
//! this project's dev machine, which is why the GPU path exists at all --
//! that machine's CPU is weak relative to its GPU.

use crate::blobs::{self, Blob, CIPHER_CFB, CIPHER_CTR, CIPHER_OFB};
use crate::checker::Checker;
use crate::cpu_oracle;
use crate::keyshape::{self, KeyShapeWriter};
use rayon::prelude::*;
use secp256k1::Secp256k1;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

/// First two 32-byte chunks only ("half"/"better_half") -- see module doc.
const CHUNK_BOUND_BYTES: usize = 64;

fn stream_variants() -> Vec<(i32, i32, i32)> {
    blobs::variant_table()
        .into_iter()
        .filter(|&(_, _, mode)| mode == CIPHER_CFB || mode == CIPHER_OFB || mode == CIPHER_CTR)
        .collect()
}

/// GPU-accelerated when built with `--features cuda` (see `secp256k1_gpu.rs`)
/// -- falls back to the CPU path below only if no GPU is actually reachable
/// at runtime (e.g. compiling inside a Docker builder stage with no `--gpus`
/// passthrough). CPU-only builds always use `run_cpu` directly. A plain
/// rayon-parallel CPU loop measured ~176 candidates/s aggregate for the full
/// medium_curated_all.txt corpus on this project's dev machine -- a real GPU
/// behind a comparatively weak CPU ("a small micro PC" per the project owner)
/// -- so the GPU path exists specifically because that CPU number is not
/// acceptable as this feature's normal running mode.
#[cfg(feature = "cuda")]
pub fn run(
    candidates: &[String],
    blobs_list: &[Blob],
    secp: &Secp256k1<secp256k1::All>,
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
) -> usize {
    match crate::secp256k1_gpu::GpuKeyDeriver::new() {
        Ok(deriver) => gpu::run(&deriver, candidates, blobs_list, checker, writer),
        Err(e) => {
            eprintln!("[stream_key_check] GPU unavailable ({e}) -- falling back to CPU");
            run_cpu(candidates, blobs_list, secp, checker, writer)
        }
    }
}

#[cfg(not(feature = "cuda"))]
pub fn run(
    candidates: &[String],
    blobs_list: &[Blob],
    secp: &Secp256k1<secp256k1::All>,
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
) -> usize {
    run_cpu(candidates, blobs_list, secp, checker, writer)
}

fn run_cpu(
    candidates: &[String],
    blobs_list: &[Blob],
    secp: &Secp256k1<secp256k1::All>,
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
) -> usize {
    let variants = stream_variants();

    let total = candidates.len();
    println!(
        "[stream_key_check] {total} candidates x {} stream variants x {} blobs = {} decrypts, \
         checking the first {CHUNK_BOUND_BYTES} bytes (half/better_half) of each (CPU)",
        variants.len(),
        blobs_list.len(),
        total * variants.len() * blobs_list.len(),
    );

    let done = AtomicUsize::new(0);
    let confirmed_total = AtomicUsize::new(0);
    let start = Instant::now();

    candidates.par_iter().for_each(|candidate| {
        for &(kdf, key_len, mode) in &variants {
            for blob in blobs_list {
                if let Some(body) = cpu_oracle::stream_decrypt_unconditional(
                    candidate.as_bytes(),
                    kdf,
                    key_len as usize,
                    mode,
                    &blob.salt,
                    &blob.ciphertext,
                ) {
                    let bound = body.len().min(CHUNK_BOUND_BYTES);
                    let variant_label = blobs::variant_label(kdf, key_len, mode);
                    let confirmed = keyshape::process_structural_hit(
                        secp, checker, writer, blob.tag, &variant_label, candidate, &body[..bound],
                    );
                    if confirmed > 0 {
                        confirmed_total.fetch_add(confirmed, Ordering::Relaxed);
                    }
                }
            }
        }
        let n = done.fetch_add(1, Ordering::Relaxed) + 1;
        if n % 4096 == 0 || n == total {
            let elapsed = start.elapsed().as_secs_f64().max(0.001);
            println!(
                "[stream_key_check] {n}/{total} candidates ({:.1}%) | {:.0} candidates/s | {elapsed:.0}s elapsed",
                100.0 * n as f64 / total as f64,
                n as f64 / elapsed,
            );
        }
    });

    let confirmed = confirmed_total.load(Ordering::Relaxed);
    println!("[stream_key_check] complete. {confirmed} confirmed funded address(es).");
    confirmed
}

#[cfg(feature = "cuda")]
mod gpu {
    use super::{stream_variants, CHUNK_BOUND_BYTES};
    use crate::blobs::{self, Blob};
    use crate::checker::Checker;
    use crate::cpu_oracle;
    use crate::keyshape::{self, KeyShapeWriter};
    use crate::secp256k1_gpu::GpuKeyDeriver;
    use rayon::prelude::*;
    use std::time::Instant;

    struct PendingKey {
        candidate_idx: usize,
        blob_idx: usize,
        variant_idx: usize,
        chunk_index: usize,
    }

    /// Candidates processed (AES-decrypted + chunked) per rayon-parallel
    /// group, sized so a group's worst case (every stream variant x blob x
    /// chunk actually valid) lands close to one `KEYS_PER_GPU_BATCH`.
    /// Without this parallelism, PBKDF2-HMAC-SHA256/10000 (9 of the 36
    /// stream variants) alone is expensive enough that a single-threaded
    /// decrypt loop measured slower than the pure-CPU fallback path it's
    /// supposed to beat -- the GPU only helps the point-multiplication step,
    /// not the KDF, so that step still needs all available CPU cores.
    const CANDIDATES_PER_GROUP: usize = 1024;

    /// AES-decrypted chunks accumulated before each `derive_hash160_pairs`
    /// call -- bounds host memory to roughly this many x 32 bytes (plus
    /// small metadata) rather than materializing the full candidate x
    /// variant x blob x chunk grid (up to ~170M entries, several GB) at
    /// once, which matters on this project's resource-constrained dev
    /// machine. Two GPU launches' worth (`GpuKeyDeriver`'s own internal
    /// `BATCH_KEYS`) per flush, so the GPU is never starved waiting on the
    /// CPU-side AES-decrypt loop between launches.
    const KEYS_PER_GPU_BATCH: usize = 524_288;

    pub fn run(
        deriver: &GpuKeyDeriver,
        candidates: &[String],
        blobs_list: &[Blob],
        checker: Option<&dyn Checker>,
        writer: &KeyShapeWriter,
    ) -> usize {
        if let Ok(name) = deriver.device_name() {
            println!("[stream_key_check] GPU device: {name}");
        }

        let variants = stream_variants();
        let total = candidates.len();
        println!(
            "[stream_key_check] {total} candidates x {} stream variants x {} blobs = {} decrypts, \
             checking the first {CHUNK_BOUND_BYTES} bytes (half/better_half) of each (GPU)",
            variants.len(),
            blobs_list.len(),
            total * variants.len() * blobs_list.len(),
        );

        let mut key_buf: Vec<[u8; 32]> = Vec::with_capacity(KEYS_PER_GPU_BATCH);
        let mut meta_buf: Vec<PendingKey> = Vec::with_capacity(KEYS_PER_GPU_BATCH);
        let mut confirmed_total = 0usize;
        let mut done = 0usize;
        let start = Instant::now();

        for group in candidates.chunks(CANDIDATES_PER_GROUP) {
            let group_start_idx = done;

            // CPU-bound AES-decrypt + KDF derivation, parallelized across
            // all cores -- this, not the point multiplication, is why the
            // plain sequential version of this loop was slower than the
            // pure-CPU fallback path.
            let group_keys: Vec<([u8; 32], PendingKey)> = group
                .par_iter()
                .enumerate()
                .flat_map_iter(|(local_idx, candidate)| {
                    let candidate_idx = group_start_idx + local_idx;
                    let mut out = Vec::new();
                    for (variant_idx, &(kdf, key_len, mode)) in variants.iter().enumerate() {
                        for (blob_idx, blob) in blobs_list.iter().enumerate() {
                            if let Some(body) = cpu_oracle::stream_decrypt_unconditional(
                                candidate.as_bytes(),
                                kdf,
                                key_len as usize,
                                mode,
                                &blob.salt,
                                &blob.ciphertext,
                            ) {
                                let bound = body.len().min(CHUNK_BOUND_BYTES);
                                for (chunk_index, key_slice) in body[..bound].chunks_exact(32).enumerate() {
                                    let key: [u8; 32] = key_slice.try_into().expect("exactly 32 bytes");
                                    out.push((key, PendingKey { candidate_idx, blob_idx, variant_idx, chunk_index }));
                                }
                            }
                        }
                    }
                    out
                })
                .collect();

            for (key, meta) in group_keys {
                key_buf.push(key);
                meta_buf.push(meta);
            }

            done += group.len();
            if key_buf.len() >= KEYS_PER_GPU_BATCH || (done == total && !key_buf.is_empty()) {
                confirmed_total +=
                    flush_batch(deriver, &mut key_buf, &mut meta_buf, &variants, blobs_list, candidates, checker, writer);
            }

            let elapsed = start.elapsed().as_secs_f64().max(0.001);
            println!(
                "[stream_key_check] {done}/{total} candidates ({:.1}%) | {:.0} candidates/s | {elapsed:.0}s elapsed",
                100.0 * done as f64 / total as f64,
                done as f64 / elapsed,
            );
        }

        println!("[stream_key_check] complete. {confirmed_total} confirmed funded address(es).");
        confirmed_total
    }

    #[allow(clippy::too_many_arguments)]
    fn flush_batch(
        deriver: &GpuKeyDeriver,
        key_buf: &mut Vec<[u8; 32]>,
        meta_buf: &mut Vec<PendingKey>,
        variants: &[(i32, i32, i32)],
        blobs_list: &[Blob],
        candidates: &[String],
        checker: Option<&dyn Checker>,
        writer: &KeyShapeWriter,
    ) -> usize {
        let results = match deriver.derive_hash160_pairs(key_buf) {
            Ok(r) => r,
            Err(e) => {
                eprintln!(
                    "[stream_key_check] GPU derive failed ({e}) -- dropping this batch of {} keys \
                     unchecked rather than falling back to CPU mid-run",
                    key_buf.len()
                );
                key_buf.clear();
                meta_buf.clear();
                return 0;
            }
        };
        let mut confirmed = 0usize;
        for ((key, meta), (compressed, uncompressed)) in key_buf.iter().zip(meta_buf.iter()).zip(results.iter()) {
            let (kdf, key_len, mode) = variants[meta.variant_idx];
            let variant_label = blobs::variant_label(kdf, key_len, mode);
            confirmed += keyshape::record_precomputed_hit(
                checker,
                writer,
                blobs_list[meta.blob_idx].tag,
                &variant_label,
                &candidates[meta.candidate_idx],
                meta.chunk_index,
                *key,
                *compressed,
                *uncompressed,
            );
        }
        key_buf.clear();
        meta_buf.clear();
        confirmed
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::checker::{BloomChecker, CheckResult};

    struct ConstChecker(bool);
    impl Checker for ConstChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            if self.0 { CheckResult::Hit } else { CheckResult::Miss }
        }
    }

    fn one_blob() -> Blob {
        Blob { tag: "SYNTH", salt: [0x55u8; 8], ciphertext: vec![0u8; 80] }
    }

    #[test]
    fn no_checker_never_confirms_but_still_scans_every_stream_variant() {
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let writer = KeyShapeWriter::new(dir.path().join("hits.jsonl").to_str().unwrap()).unwrap();
        let candidates = vec!["password1".to_string(), "password2".to_string()];
        let blobs_list = vec![one_blob()];
        let confirmed = run(&candidates, &blobs_list, &secp, None, &writer);
        assert_eq!(confirmed, 0);
        // 2 candidates x 36 stream variants (4 KDF x 3 key sizes x 3 modes) x
        // 1 blob x up to 2 chunks x 2 address types -- most chunks won't be
        // valid secp256k1 scalars by chance, but the file must be non-empty,
        // proving the loop actually ran the full stream-variant grid.
        let contents = std::fs::read_to_string(dir.path().join("hits.jsonl")).unwrap();
        assert!(!contents.is_empty());
    }

    #[test]
    fn checker_that_always_hits_confirms_and_bound_is_respected() {
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let writer = KeyShapeWriter::new(dir.path().join("hits.jsonl").to_str().unwrap()).unwrap();
        let candidates = vec!["password1".to_string()];
        let blobs_list = vec![one_blob()];
        let confirmed = run(&candidates, &blobs_list, &secp, Some(&ConstChecker(true)), &writer);
        // Every valid-scalar chunk x address-type pair gets "confirmed" --
        // at most 2 chunks (half/better_half) x 2 types x 36 variants = 144,
        // fewer in practice since not every chunk is a valid scalar.
        assert!(confirmed > 0);
        assert!(confirmed <= 144);
        let contents = std::fs::read_to_string(dir.path().join("hits.jsonl")).unwrap();
        assert!(!contents.contains("\"half\":\"chunk_2\""), "must never see a third chunk -- CHUNK_BOUND_BYTES=64 caps at two");
    }

    #[test]
    fn real_bloom_checker_wiring_does_not_panic() {
        // Note: a real (not `ConstChecker`-mocked) `BloomChecker::
        // from_hash160_list` sized for just one entry saturates most of its
        // bits (n=1 -> m=64, k=45 -> see checker/bloom.rs) and reports most
        // lookups as Hit at this scale -- the same small-filter-saturation
        // behavior already documented on the Python side
        // (key_shape_sweep.py's self-test). A raw `BloomChecker` alone (not
        // wrapped in `VerifiedBloomChecker`) has no API-confirmation step to
        // filter those false positives back out, so with 36 stream variants
        // x up to 2 chunks x 2 address types worth of lookups here, a
        // nonzero "confirmed" count is expected, not a sign anything is
        // broken -- this test only proves the `&dyn Checker` trait object
        // plumbing reaches the real `BloomChecker` type without panicking.
        let secp = Secp256k1::new();
        let unrelated_hash160 = [0x77u8; 20];
        let bloom = BloomChecker::from_hash160_list(&[unrelated_hash160]);
        let dir = tempfile::tempdir().unwrap();
        let writer = KeyShapeWriter::new(dir.path().join("hits.jsonl").to_str().unwrap()).unwrap();
        let candidates = vec!["some_candidate".to_string()];
        let blobs_list = vec![one_blob()];
        let _confirmed = run(&candidates, &blobs_list, &secp, Some(&bloom), &writer);
    }
}
