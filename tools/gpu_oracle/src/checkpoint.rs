//! Checkpoint: an atomic resume-cursor (copied from key-seeker's
//! `checkpoint/mod.rs`) plus a fingerprint header matching this project's
//! existing Python sweep convention (stream_mode_cipher_sweep.py /
//! nopad_window_sweep.py): candidate/blob/variant/oracle-source digests,
//! refusing (hard error) to resume a checkpoint whose header doesn't match
//! byte-for-byte.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

// Note: unlike key-seeker's single-value byte-offset Checkpoint (a linear
// scan cursor), this tool processes candidates in batches and needs a set of
// completed indices, so SweepCheckpoint below tracks that directly instead
// of wrapping a single u64 cursor.

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Fingerprint {
    pub version: u32,
    pub candidate_count: usize,
    pub candidate_digest: String,
    pub blob_digest: String,
    pub variant_digest: String,
    pub kernel_sha256: String,
    pub driver_sha256: String,
}

fn sha256_hex_truncated16(bytes: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(bytes);
    hex::encode(h.finalize())[..16].to_string()
}

pub fn candidate_list_digest(candidates: &[String]) -> String {
    sha256_hex_truncated16(candidates.join("\n").as_bytes())
}

pub fn blob_digest(blobs: &[crate::blobs::Blob]) -> String {
    let mut h = Sha256::new();
    for b in blobs {
        h.update(b.tag.as_bytes());
        h.update([0u8]);
        h.update(b.salt);
        h.update(&b.ciphertext);
    }
    hex::encode(h.finalize())[..16].to_string()
}

pub fn variant_digest(variants: &[(i32, i32)]) -> String {
    sha256_hex_truncated16(format!("{variants:?}").as_bytes())
}

fn file_sha256_truncated16(path: &Path) -> io::Result<String> {
    let bytes = fs::read(path)?;
    Ok(sha256_hex_truncated16(&bytes))
}

/// Hashes the kernel source and this binary's own source tree (best-effort --
/// falls back to the running executable's bytes if source files aren't
/// present, e.g. inside a trimmed runtime container image).
pub fn compute_fingerprint(
    candidates: &[String],
    blobs: &[crate::blobs::Blob],
    variants: &[(i32, i32)],
    kernel_path: &Path,
    driver_source_dir: &Path,
) -> Fingerprint {
    let kernel_sha256 = file_sha256_truncated16(kernel_path).unwrap_or_else(|_| "unavailable".into());
    let driver_sha256 = hash_dir_best_effort(driver_source_dir)
        .unwrap_or_else(|| std::env::current_exe().ok().and_then(|p| file_sha256_truncated16(&p).ok()).unwrap_or_else(|| "unavailable".into()));

    Fingerprint {
        version: 1,
        candidate_count: candidates.len(),
        candidate_digest: candidate_list_digest(candidates),
        blob_digest: blob_digest(blobs),
        variant_digest: variant_digest(variants),
        kernel_sha256,
        driver_sha256,
    }
}

fn hash_dir_best_effort(dir: &Path) -> Option<String> {
    let mut entries: Vec<PathBuf> = fs::read_dir(dir).ok()?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|e| e.to_str()) == Some("rs"))
        .collect();
    entries.sort();
    let mut h = Sha256::new();
    for p in entries {
        h.update(fs::read(&p).ok()?);
    }
    Some(hex::encode(h.finalize())[..16].to_string())
}

/// Sweep checkpoint: JSONL file, first line `{"header": true, ...fingerprint}`,
/// subsequent lines are per-candidate-index "done" markers (index only -- the
/// actual hit records live in the separate hits output file via OutputWriter).
pub struct SweepCheckpoint {
    path: PathBuf,
}

impl SweepCheckpoint {
    pub fn new(path: &str) -> Self {
        Self { path: PathBuf::from(path) }
    }

    /// Loads the set of completed candidate indices, verifying the header
    /// fingerprint matches exactly. Returns Ok(None) if no checkpoint exists
    /// yet. Returns Err if a checkpoint exists but its header doesn't match
    /// the current run's fingerprint (refuse-to-resume, never silently reuse).
    pub fn load(&self, expected: &Fingerprint) -> io::Result<Option<std::collections::HashSet<u64>>> {
        if !self.path.exists() {
            return Ok(None);
        }
        let f = fs::File::open(&self.path)?;
        let mut lines = BufReader::new(f).lines();

        let header_line = match lines.next() {
            Some(l) => l?,
            None => return Ok(Some(Default::default())), // empty file, treat as fresh
        };
        let header: serde_json::Value = serde_json::from_str(&header_line)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, format!("checkpoint header parse error: {e}")))?;
        let stored: Fingerprint = serde_json::from_value(header.clone())
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, format!("checkpoint header fields missing: {e}")))?;

        if stored != *expected {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!(
                    "checkpoint fingerprint mismatch -- refusing to resume against a different \
                     candidate list/blob set/variant table/kernel. Delete '{}' to start fresh.\n\
                     stored:   {stored:?}\nexpected: {expected:?}",
                    self.path.display()
                ),
            ));
        }

        let mut done = std::collections::HashSet::new();
        for line in lines {
            let line = line?;
            if line.trim().is_empty() {
                continue;
            }
            if let Ok(idx) = line.trim().parse::<u64>() {
                done.insert(idx);
            }
        }
        Ok(Some(done))
    }

    /// Writes the header line, truncating any existing checkpoint. Call only
    /// when starting a fresh run (no existing checkpoint, or after the
    /// fingerprint mismatch above was already surfaced to the user).
    pub fn init_fresh(&self, fingerprint: &Fingerprint) -> io::Result<fs::File> {
        let mut f = fs::OpenOptions::new().create(true).write(true).truncate(true).open(&self.path)?;
        let mut header = serde_json::to_value(fingerprint).unwrap();
        header["header"] = serde_json::Value::Bool(true);
        writeln!(f, "{header}")?;
        f.flush()?;
        Ok(fs::OpenOptions::new().append(true).open(&self.path)?)
    }

    /// Appends to an existing valid checkpoint (fingerprint already verified via load()).
    pub fn open_append(&self) -> io::Result<fs::File> {
        fs::OpenOptions::new().create(true).append(true).open(&self.path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fingerprint_mismatch_is_refused() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("test.checkpoint");
        let cp = SweepCheckpoint::new(path.to_str().unwrap());

        let fp_a = Fingerprint {
            version: 1, candidate_count: 3, candidate_digest: "aaa".into(),
            blob_digest: "bbb".into(), variant_digest: "ccc".into(),
            kernel_sha256: "ddd".into(), driver_sha256: "eee".into(),
        };
        cp.init_fresh(&fp_a).unwrap();

        let fp_b = Fingerprint { candidate_count: 4, ..fp_a.clone() };
        let result = cp.load(&fp_b);
        assert!(result.is_err(), "mismatched fingerprint must be refused, not silently reused");
    }

    #[test]
    fn matching_fingerprint_loads_cleanly() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("test.checkpoint");
        let cp = SweepCheckpoint::new(path.to_str().unwrap());

        let fp = Fingerprint {
            version: 1, candidate_count: 3, candidate_digest: "aaa".into(),
            blob_digest: "bbb".into(), variant_digest: "ccc".into(),
            kernel_sha256: "ddd".into(), driver_sha256: "eee".into(),
        };
        {
            let mut f = cp.init_fresh(&fp).unwrap();
            writeln!(f, "0").unwrap();
            writeln!(f, "1").unwrap();
        }
        let done = cp.load(&fp).unwrap().unwrap();
        assert_eq!(done.len(), 2);
        assert!(done.contains(&0) && done.contains(&1));
    }

    #[test]
    fn missing_checkpoint_returns_none() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("missing.checkpoint");
        let cp = SweepCheckpoint::new(path.to_str().unwrap());
        let fp = Fingerprint {
            version: 1, candidate_count: 0, candidate_digest: "x".into(),
            blob_digest: "x".into(), variant_digest: "x".into(),
            kernel_sha256: "x".into(), driver_sha256: "x".into(),
        };
        assert!(cp.load(&fp).unwrap().is_none());
    }
}
