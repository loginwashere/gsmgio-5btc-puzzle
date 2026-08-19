//! Hit writer -- adapted from key-seeker's src/output/mod.rs (Mutex<File>,
//! append-only, thread-safe) but emitting JSONL hit records with this
//! project's fields instead of key/address pairs.

use serde::Serialize;
use std::fs::OpenOptions;
use std::io::{self, Write};
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize)]
pub struct Hit {
    pub candidate: String,
    pub candidate_source: String, // the original wordlist line this keystring was derived from
    pub keystring_form: String,
    pub kdf: String,
    pub key_bits: u32,
    pub blob_tag: String,
    pub hit_kind: String, // "weak" | "strong" | "structural"
    pub z_score: f64,
    pub body_preview: String, // first 64 bytes of the decrypted body, lossy-UTF8, for quick eyeballing
}

pub struct OutputWriter {
    file: Mutex<std::fs::File>,
}

impl OutputWriter {
    pub fn new(path: &str) -> io::Result<Self> {
        let file = OpenOptions::new().create(true).append(true).open(path)?;
        Ok(Self { file: Mutex::new(file) })
    }

    /// Write one hit. Thread-safe; never panics on a transient I/O error
    /// (logged to stderr instead, matching key-seeker's own tolerance for a
    /// long-running batch job, but NOT silently swallowed).
    pub fn write_hit(&self, hit: &Hit) {
        let line = match serde_json::to_string(hit) {
            Ok(l) => l,
            Err(e) => {
                eprintln!("[output] failed to serialize hit: {e}");
                return;
            }
        };
        if let Ok(mut f) = self.file.lock() {
            if let Err(e) = writeln!(f, "{line}") {
                eprintln!("[output] failed to write hit to file: {e}");
            }
        }
        println!(
            "[HIT:{}] candidate={:?} kdf={} blob={} z={:.2}",
            hit.hit_kind, hit.candidate, hit.kdf, hit.blob_tag, hit.z_score
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_hit() -> Hit {
        Hit {
            candidate: "yellowblueprimes".into(),
            candidate_source: "yellowblueprimes".into(),
            keystring_form: "yellowblueprimes".into(),
            kdf: "legacy-sha256".into(),
            key_bits: 256,
            blob_tag: "SALPH".into(),
            hit_kind: "weak".into(),
            z_score: 5.4,
            body_preview: "".into(),
        }
    }

    #[test]
    fn write_hit_appends_valid_jsonl() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("hits.jsonl");
        let w = OutputWriter::new(path.to_str().unwrap()).unwrap();
        w.write_hit(&sample_hit());
        w.write_hit(&sample_hit());
        let content = std::fs::read_to_string(&path).unwrap();
        let lines: Vec<&str> = content.lines().collect();
        assert_eq!(lines.len(), 2);
        for line in lines {
            let v: serde_json::Value = serde_json::from_str(line).unwrap();
            assert_eq!(v["blob_tag"], "SALPH");
        }
    }

    #[test]
    fn new_appends_to_existing_file() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("hits.jsonl");
        std::fs::write(&path, "{\"existing\":true}\n").unwrap();
        let w = OutputWriter::new(path.to_str().unwrap()).unwrap();
        w.write_hit(&sample_hit());
        let content = std::fs::read_to_string(&path).unwrap();
        assert!(content.starts_with("{\"existing\":true}\n"));
        assert_eq!(content.lines().count(), 2);
    }
}
