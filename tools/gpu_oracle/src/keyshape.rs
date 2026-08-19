//! Structural-hit (raw 32-byte-aligned private-key-shaped body) address
//! derivation + Bloom/API verification, invoked from `main.rs`'s per-hit GPU
//! callback for `hit_kind == 3` only -- the CUDA kernel already guarantees a
//! complete PKCS7 padding block (`pad == 16`) before reporting it, so no
//! further classification is needed here, unlike a "strong" printable hit
//! (see `main.rs`'s comment on why `hit_kind == 2` stays with
//! `tools/gsmg/key_shape_sweep.py`'s hex64/WIF/BIP39 text classifier instead
//! of duplicating it in Rust). The body itself can be any length that's a
//! multiple of 16 (any of the 4 tracked blobs, not just SALPH/P32TRAILING's
//! 64-byte case) -- see `process_structural_hit`'s chunking below.
//!
//! Mirrors `tools/gsmg/binary_key_material_backfill.py`'s `record_hit()`
//! (same half/better_half split for the common 2-chunk case, same
//! compressed+uncompressed address pair per chunk) but runs inline in the
//! Rust pipeline via `checker::VerifiedBloomChecker` instead of requiring a
//! separate Python re-run: a Bloom hit here is confirmed or discarded by one
//! live Blockstream API call before this function returns, not queued for a
//! later `--verify-queue` pass.

use crate::checker::{CheckResult, Checker};
use crate::crypto;
use secp256k1::Secp256k1;
use serde::Serialize;
use std::fs::OpenOptions;
use std::io::Write;
use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
use std::sync::Mutex;

#[derive(Debug, Serialize)]
pub struct KeyShapeHit {
    pub blob_tag: String,
    pub variant: String,
    pub candidate: String,
    pub half: String,
    pub address_type: &'static str,
    pub private_key_hex: String,
    pub address: String,
    pub hash160: String,
    pub confirmed_funded: bool,
}

/// "half"/"better_half" for the common 2-chunk (64-byte) case -- matches the
/// project's existing terminology (see FINDINGS.md's "half | better_half"
/// convention) -- "chunk_N" beyond that, e.g. for COSMIC's 41-chunk
/// (1312-byte) structural bodies once the `pad == 16` gate stopped requiring
/// exactly 64 bytes (see cpu_oracle.rs::try_open).
fn chunk_label(index: usize) -> String {
    match index {
        0 => "half".to_string(),
        1 => "better_half".to_string(),
        n => format!("chunk_{n}"),
    }
}

/// Append-only, mode-0600 sensitive JSONL writer -- same convention as the
/// Python side's `append_jsonl(..., sensitive=True)` (private keys never go
/// into the ordinary world-readable hits/checkpoint files).
pub struct KeyShapeWriter {
    file: Mutex<std::fs::File>,
}

impl KeyShapeWriter {
    pub fn new(path: &str) -> std::io::Result<Self> {
        let file = OpenOptions::new().create(true).append(true).mode(0o600).open(path)?;
        std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600))?;
        Ok(Self { file: Mutex::new(file) })
    }

    pub fn write(&self, hit: &KeyShapeHit) {
        let line = match serde_json::to_string(hit) {
            Ok(l) => l,
            Err(e) => {
                eprintln!("[keyshape] failed to serialize hit: {e}");
                return;
            }
        };
        if let Ok(mut f) = self.file.lock() {
            if let Err(e) = writeln!(f, "{line}") {
                eprintln!("[keyshape] failed to write hit: {e}");
            }
        }
    }
}

/// `body` must be the already-unpadded structural plaintext
/// (`cpu_oracle::try_open`'s `HitKind::Structural` body) -- any length now
/// that the `pad == 16` gate no longer requires exactly 64 bytes (see
/// cpu_oracle.rs). Derives both address types for each complete 32-byte
/// chunk (trailing bytes shorter than 32 are not a valid secp256k1 scalar
/// candidate and are ignored), checks each hash160 through `checker` (Bloom
/// pre-filter + mandatory API verification when `Some`; always Miss when
/// `None`, e.g. no local Bloom cache available), and writes every checked
/// address -- hit or miss -- to `writer` for later audit. Returns the number
/// of addresses `checker` confirmed funded (expected 0 for every run to
/// date; nonzero is the actual goal). `variant` is a `blobs::variant_label`-
/// shaped string (e.g. "legacy-sha256/aes-256-cbc") -- recorded so JSONL rows
/// stay disambiguated when the same (candidate, blob) pair is checked under
/// more than one KDF/cipher variant, which `stream_key_check.rs` does
/// routinely (every CFB/OFB/CTR variant, not just whichever one the GPU
/// kernel happened to classify as a hit).
pub fn process_structural_hit(
    secp: &Secp256k1<secp256k1::All>,
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
    blob_tag: &str,
    variant: &str,
    candidate: &str,
    body: &[u8],
) -> usize {
    let mut confirmed = 0usize;
    for (chunk_index, key_slice) in body.chunks_exact(32).enumerate() {
        let half_label = chunk_label(chunk_index);
        let key: [u8; 32] = key_slice.try_into().expect("exactly 32 bytes");
        let Some(addrs) = crypto::privkey_to_addresses(secp, &key) else {
            continue; // not a valid secp256k1 scalar -- not a real key candidate
        };
        confirmed += check_and_record(
            checker, writer, blob_tag, variant, candidate, &half_label, key, addrs.compressed_hash160, addrs.uncompressed_hash160,
        );
    }
    confirmed
}

/// Same Bloom/API check + JSONL write as `process_structural_hit`'s inner
/// loop, but for a `(private_key, compressed_hash160, uncompressed_hash160)`
/// triple already derived elsewhere -- used by `stream_key_check.rs`'s GPU
/// path (`secp256k1_gpu.rs`'s `GpuKeyDeriver`), which computes hash160s on
/// the GPU instead of via `crypto::privkey_to_addresses`'s CPU secp256k1
/// call. No secp256k1 scalar validity check is needed here: the GPU kernel
/// ran `scalar_mul_G` unconditionally on `key`, exactly as
/// `crypto::privkey_to_addresses` would have -- if `key` weren't a valid
/// scalar there'd be no meaningful curve point either way, but in practice
/// nearly every 32-byte value is a valid scalar (the curve order is within
/// 2^-127 of 2^256), so this is not a meaningful source of divergence from
/// the CPU path.
pub fn record_precomputed_hit(
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
    blob_tag: &str,
    variant: &str,
    candidate: &str,
    chunk_index: usize,
    key: [u8; 32],
    compressed_hash160: [u8; 20],
    uncompressed_hash160: [u8; 20],
) -> usize {
    let half_label = chunk_label(chunk_index);
    check_and_record(checker, writer, blob_tag, variant, candidate, &half_label, key, compressed_hash160, uncompressed_hash160)
}

#[allow(clippy::too_many_arguments)]
fn check_and_record(
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
    blob_tag: &str,
    variant: &str,
    candidate: &str,
    half_label: &str,
    key: [u8; 32],
    compressed_hash160: [u8; 20],
    uncompressed_hash160: [u8; 20],
) -> usize {
    let mut confirmed = 0usize;
    for (address_type, hash160) in [("compressed", compressed_hash160), ("uncompressed", uncompressed_hash160)] {
        confirmed += record_one(checker, writer, blob_tag, variant, candidate, half_label, address_type, key, hash160);
    }
    confirmed
}

/// Bloom-hit-so-far already reported by the GPU's on-device
/// `bloom_check` (aes_kdf_oracle.cu's stream-mode branch, via
/// `gpu.rs::scan`'s `on_stream_key_hit`) for exactly one
/// (chunk, address_type) pair -- unlike every other entry point into this
/// module, there is no "log every checked address, hit or miss" audit trail
/// for this path: the whole point of checking Bloom membership on-device is
/// to avoid transferring every checked address back to the host, so only
/// actual Bloom hits (which this function then still puts through the exact
/// same mandatory live API confirmation as any other Bloom hit -- the
/// on-device bloom_check alone is never sufficient) ever reach here.
#[allow(clippy::too_many_arguments)]
pub fn record_gpu_stream_hit(
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
    blob_tag: &str,
    variant: &str,
    candidate: &str,
    chunk_index: usize,
    address_type: &'static str,
    key: [u8; 32],
    hash160: [u8; 20],
) -> usize {
    let half_label = chunk_label(chunk_index);
    record_one(checker, writer, blob_tag, variant, candidate, &half_label, address_type, key, hash160)
}

#[allow(clippy::too_many_arguments)]
fn record_one(
    checker: Option<&dyn Checker>,
    writer: &KeyShapeWriter,
    blob_tag: &str,
    variant: &str,
    candidate: &str,
    half_label: &str,
    address_type: &'static str,
    key: [u8; 32],
    hash160: [u8; 20],
) -> usize {
    let address = crypto::hash160_to_address(&hash160);
    let confirmed_funded = match checker {
        Some(c) => matches!(c.check(&hash160), CheckResult::Hit),
        None => false,
    };
    if confirmed_funded {
        eprintln!("[keyshape] *** CONFIRMED FUNDED: {blob_tag} {variant} {half_label}/{address_type} {address} ***");
    }
    writer.write(&KeyShapeHit {
        blob_tag: blob_tag.to_string(),
        variant: variant.to_string(),
        candidate: candidate.to_string(),
        half: half_label.to_string(),
        address_type,
        private_key_hex: hex::encode(key),
        address,
        hash160: hex::encode(hash160),
        confirmed_funded,
    });
    confirmed_funded as usize
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::checker::BloomChecker;

    struct ConstChecker(bool);
    impl Checker for ConstChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            if self.0 { CheckResult::Hit } else { CheckResult::Miss }
        }
    }

    fn synthetic_body() -> Vec<u8> {
        // private keys 1 and 2 -- known addresses asserted in crypto::tests.
        let mut body = vec![0u8; 64];
        body[31] = 1;
        body[63] = 2;
        body
    }

    #[test]
    fn body_shorter_than_one_chunk_is_ignored() {
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let writer = KeyShapeWriter::new(dir.path().join("hits.jsonl").to_str().unwrap()).unwrap();
        let confirmed = process_structural_hit(&secp, None, &writer, "SYNTH", "legacy-sha256/aes-256-cbc", "cand", &[0u8; 31]);
        assert_eq!(confirmed, 0);
        assert!(std::fs::read_to_string(dir.path().join("hits.jsonl")).unwrap().is_empty());
    }

    #[test]
    fn trailing_incomplete_chunk_is_ignored() {
        // Regression test for the broadened (no-longer-64-byte-pinned) gate:
        // a body whose length isn't a multiple of 32 must still process its
        // complete leading chunks and simply drop the incomplete tail, not
        // panic or silently drop everything the way the old exact-64 check
        // would have.
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("hits.jsonl");
        let writer = KeyShapeWriter::new(path.to_str().unwrap()).unwrap();
        let mut body = vec![0u8; 32];
        body[31] = 1; // private key 1 -- one complete, valid chunk
        body.extend(vec![0u8; 31]); // incomplete trailing chunk
        let confirmed = process_structural_hit(&secp, None, &writer, "SYNTH", "legacy-sha256/aes-256-cbc", "cand", &body);
        assert_eq!(confirmed, 0); // no checker
        let lines: Vec<_> = std::fs::read_to_string(&path).unwrap().lines().map(String::from).collect();
        assert_eq!(lines.len(), 2); // exactly one chunk's compressed+uncompressed pair
        assert!(lines.iter().any(|l| l.contains("1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH")));
    }

    #[test]
    fn third_chunk_beyond_the_two_halves_is_labeled_chunk_2() {
        // Proves the gate no longer stops at exactly two 32-byte chunks --
        // e.g. COSMIC's 1312-byte structural body now produces 41 chunks,
        // not just the first two.
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("hits.jsonl");
        let writer = KeyShapeWriter::new(path.to_str().unwrap()).unwrap();
        let mut body = synthetic_body(); // keys 1, 2
        let mut key3 = vec![0u8; 32];
        key3[31] = 3;
        body.extend(key3);
        let confirmed = process_structural_hit(&secp, None, &writer, "SYNTH", "legacy-sha256/aes-256-cbc", "cand", &body);
        assert_eq!(confirmed, 0); // no checker
        let contents = std::fs::read_to_string(&path).unwrap();
        assert_eq!(contents.lines().count(), 6); // 3 chunks x 2 address types
        assert!(contents.contains("\"half\":\"chunk_2\""));
        assert!(contents.contains("\"half\":\"half\"")); // sanity: "half"/"better_half" still used for the first two
        assert!(contents.contains("\"half\":\"better_half\""));
    }

    #[test]
    fn four_addresses_written_no_checker() {
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("hits.jsonl");
        let writer = KeyShapeWriter::new(path.to_str().unwrap()).unwrap();
        let confirmed = process_structural_hit(&secp, None, &writer, "SYNTH", "legacy-sha256/aes-256-cbc", "cand", &synthetic_body());
        assert_eq!(confirmed, 0); // no checker -> nothing is ever "confirmed"
        let lines: Vec<_> = std::fs::read_to_string(&path).unwrap().lines().map(String::from).collect();
        assert_eq!(lines.len(), 4); // 2 halves x 2 address types
        assert!(lines.iter().any(|l| l.contains("1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH")));
        assert!(lines.iter().any(|l| l.contains("1cMh228HTCiwS8ZsaakH8A8wze1JR5ZsP")));
        // private key hex is present in the sensitive file (unlike the Python
        // side's Bloom queue, which deliberately omits it).
        let mut half_key = [0u8; 32];
        half_key[31] = 1;
        assert!(lines.iter().any(|l| l.contains(&hex::encode(half_key))));
        let perms = std::fs::metadata(&path).unwrap().permissions();
        use std::os::unix::fs::PermissionsExt;
        assert_eq!(perms.mode() & 0o777, 0o600);
    }

    #[test]
    fn checker_hit_is_confirmed_and_counted() {
        let secp = Secp256k1::new();
        let dir = tempfile::tempdir().unwrap();
        let writer = KeyShapeWriter::new(dir.path().join("hits.jsonl").to_str().unwrap()).unwrap();
        let confirmed =
            process_structural_hit(&secp, Some(&ConstChecker(true)), &writer, "SYNTH", "legacy-sha256/aes-256-cbc", "cand", &synthetic_body());
        assert_eq!(confirmed, 4); // every derived address "confirmed" by a checker that always hits
    }

    #[test]
    fn real_bloom_checker_integration_no_confirmed_hit() {
        // End-to-end wiring check with a real (tiny, synthetic) Bloom filter
        // standing in for checker::VerifiedBloomChecker's bloom half --
        // confirms process_structural_hit's Checker trait object plumbing
        // works against the actual BloomChecker type, not just a test double.
        let secp = Secp256k1::new();
        let unrelated_hash160 = [0x99u8; 20];
        let bloom = BloomChecker::from_hash160_list(&[unrelated_hash160]);
        let dir = tempfile::tempdir().unwrap();
        let writer = KeyShapeWriter::new(dir.path().join("hits.jsonl").to_str().unwrap()).unwrap();
        let confirmed = process_structural_hit(&secp, Some(&bloom), &writer, "SYNTH", "legacy-sha256/aes-256-cbc", "cand", &synthetic_body());
        assert_eq!(confirmed, 0); // bloom.check() implements Checker directly (Hit==Miss semantics
                                  // here since BloomChecker alone, not wrapped in VerifiedBloomChecker,
                                  // has no API step -- still proves the trait object call succeeds)
    }
}
