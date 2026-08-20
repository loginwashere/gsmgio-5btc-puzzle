//! Ported verbatim from ../../../key-seeker's src/checker/bloom.rs. Same
//! BLMCACHE v1 file format the Python side already reads
//! (`tools/gsmg/binary_key_material_backfill.py`'s `BloomCache`) and the
//! same `db/addresses.hash160.bloom` file (copied from key-seeker, see
//! .gitignore) -- one file, two independently-tested readers.

use super::{CheckResult, Checker};
use std::fs::File;
use std::io::{BufRead, BufReader, BufWriter, Read, Write};

/// MurmurHash3_x86_32 for a fixed 20-byte input (Bitcoin hash160).
/// 20 bytes = 5 full 4-byte chunks, no remainder.
fn murmur3_x86_32(data: &[u8; 20], seed: u32) -> u32 {
    const C1: u32 = 0xcc9e2d51;
    const C2: u32 = 0x1b873593;
    let mut h = seed;

    for i in 0..5usize {
        let k = u32::from_le_bytes(data[i * 4..i * 4 + 4].try_into().unwrap());
        let k = k.wrapping_mul(C1).rotate_left(15).wrapping_mul(C2);
        h ^= k;
        h = h.rotate_left(13).wrapping_mul(5).wrapping_add(0xe6546b64);
    }

    h ^= 20u32; // length mix
    h ^= h >> 16;
    h = h.wrapping_mul(0x85ebca6b);
    h ^= h >> 13;
    h = h.wrapping_mul(0xc2b2ae35);
    h ^= h >> 16;
    h
}

/// Standard bloom filter backed by a flat u64 bit array.
/// bit_i = (h1 + i * h2) % m, i in 0..k, h1 = murmur3(data, SEED), h2 = murmur3(data, h1).
pub struct BloomChecker {
    bits: Vec<u64>,
    m: u64,
    k: u32,
}

const MURMUR_SEED: u32 = 0x9747b28c;

impl BloomChecker {
    fn new(expected_entries: usize) -> Self {
        let n = expected_entries.max(1) as f64;
        let p = 0.0001_f64;
        let m_raw = ((-n * p.ln()) / (2_f64.ln().powi(2))).ceil() as u64;
        let m = (m_raw + 63) / 64 * 64;
        let k = ((m as f64 / n) * 2_f64.ln()).ceil() as u32;
        let bits = vec![0u64; (m / 64) as usize];
        Self { bits, m, k }
    }

    fn set_bit(&mut self, bit: u64) {
        self.bits[(bit / 64) as usize] |= 1u64 << (bit % 64);
    }

    fn get_bit(&self, bit: u64) -> bool {
        (self.bits[(bit / 64) as usize] >> (bit % 64)) & 1 == 1
    }

    fn insert(&mut self, data: &[u8; 20]) {
        let h1 = murmur3_x86_32(data, MURMUR_SEED);
        let h2 = murmur3_x86_32(data, h1);
        for i in 0..self.k {
            let bit = ((h1 as u64).wrapping_add((i as u64).wrapping_mul(h2 as u64))) % self.m;
            self.set_bit(bit);
        }
    }

    fn contains(&self, data: &[u8; 20]) -> bool {
        let h1 = murmur3_x86_32(data, MURMUR_SEED);
        let h2 = murmur3_x86_32(data, h1);
        for i in 0..self.k {
            let bit = ((h1 as u64).wrapping_add((i as u64).wrapping_mul(h2 as u64))) % self.m;
            if !self.get_bit(bit) {
                return false;
            }
        }
        true
    }

    pub fn raw_bits(&self) -> &[u64] {
        &self.bits
    }

    pub fn num_bits(&self) -> u64 {
        self.m
    }

    pub fn num_hashes(&self) -> u32 {
        self.k
    }
}

impl BloomChecker {
    /// Build from a file of hex-encoded hash160 values, one per line.
    #[cfg_attr(not(test), allow(dead_code))]
    pub fn from_hash160_file(path: &str, expected_entries: usize) -> std::io::Result<Self> {
        let mut checker = Self::new(expected_entries);
        let file = File::open(path)?;
        let reader = BufReader::new(file);
        for line in reader.lines().map_while(Result::ok) {
            let trimmed = line.trim().to_lowercase();
            if trimmed.len() == 40 {
                if let Ok(bytes) = hex::decode(&trimmed) {
                    if let Ok(arr) = bytes.as_slice().try_into() {
                        checker.insert(arr);
                    }
                }
            }
        }
        Ok(checker)
    }

    /// Format: magic (8) + version (1) + m as u64 LE (8) + k as u32 LE (4) + bits as LE u64 words.
    #[cfg_attr(not(test), allow(dead_code))]
    pub fn save_to_file(&self, path: &str) -> std::io::Result<()> {
        let file = File::create(path)?;
        let mut w = BufWriter::new(file);
        w.write_all(b"BLMCACHE")?;
        w.write_all(&[1u8])?;
        w.write_all(&self.m.to_le_bytes())?;
        w.write_all(&self.k.to_le_bytes())?;
        for word in &self.bits {
            w.write_all(&word.to_le_bytes())?;
        }
        Ok(())
    }

    /// Load a bloom filter from a binary cache file produced by `save_to_file`
    /// (or by the Python `_write_test_bloom`/production build -- same format).
    pub fn load_from_file(path: &str) -> std::io::Result<Self> {
        let file = File::open(path)?;
        let mut r = BufReader::new(file);

        let mut magic = [0u8; 8];
        r.read_exact(&mut magic)?;
        if &magic != b"BLMCACHE" {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "bad magic"));
        }

        let mut ver = [0u8; 1];
        r.read_exact(&mut ver)?;
        if ver[0] != 1 {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "unsupported version"));
        }

        let mut buf8 = [0u8; 8];
        r.read_exact(&mut buf8)?;
        let m = u64::from_le_bytes(buf8);
        if m == 0 || m % 64 != 0 {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "invalid m"));
        }

        let mut buf4 = [0u8; 4];
        r.read_exact(&mut buf4)?;
        let k = u32::from_le_bytes(buf4);
        if k == 0 {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "invalid k"));
        }

        let n_words = (m / 64) as usize;
        let mut bytes = vec![0u8; n_words * 8];
        r.read_exact(&mut bytes)?;
        let bits: Vec<u64> = bytes
            .chunks_exact(8)
            .map(|c| u64::from_le_bytes(c.try_into().unwrap()))
            .collect();

        Ok(Self { bits, m, k })
    }

    /// Tiny in-memory Bloom filter over an exact hash160 list -- used by
    /// tests and by selftest.rs's synthetic-vector GPU/CPU cross-checks
    /// (no real Bloom cache file needed for a one-entry known-positive).
    pub fn from_hash160_list(entries: &[[u8; 20]]) -> Self {
        let mut checker = Self::new(entries.len().max(1));
        for h in entries {
            checker.insert(h);
        }
        checker
    }

    /// Sets a few extra entries' bits in an already-built (e.g. loaded from
    /// a large file) filter -- used to fold `checker::known_targets`'s eight
    /// EC-derived addresses into the real production Bloom cache after
    /// loading it, so the GPU-side on-device pre-filter
    /// (`bloom_check_key_chunks` in `aes_kdf_oracle.cu`) can flag them too,
    /// not just the host-side `KnownTargetsChecker::check` exact match. `m`
    /// and `k` stay whatever they were sized for at construction; inserting
    /// a handful of extra entries into a filter built for millions raises
    /// the false-positive rate by an immeasurable amount.
    pub fn insert_extra(&mut self, entries: &[[u8; 20]]) {
        for h in entries {
            self.insert(h);
        }
    }
}

impl Checker for BloomChecker {
    fn check(&self, hash160: &[u8; 20]) -> CheckResult {
        if self.contains(hash160) {
            CheckResult::Hit
        } else {
            CheckResult::Miss
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn inserted_hash160_hits() {
        let h: [u8; 20] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];
        let checker = BloomChecker::from_hash160_list(&[h]);
        assert!(matches!(checker.check(&h), CheckResult::Hit));
    }

    #[test]
    fn non_inserted_hash160_misses() {
        let h1: [u8; 20] = [1u8; 20];
        let h2: [u8; 20] = [2u8; 20];
        let checker = BloomChecker::from_hash160_list(&[h1]);
        assert!(matches!(checker.check(&h2), CheckResult::Miss));
    }

    #[test]
    fn loads_from_hex_file() {
        let h: [u8; 20] = [0xab; 20];
        let hex_line = hex::encode(h);

        let mut tmp = tempfile::NamedTempFile::new().unwrap();
        writeln!(tmp, "{hex_line}").unwrap();

        let checker = BloomChecker::from_hash160_file(tmp.path().to_str().unwrap(), 10).unwrap();
        assert!(matches!(checker.check(&h), CheckResult::Hit));

        let other = [0xcd; 20];
        assert!(matches!(checker.check(&other), CheckResult::Miss));
    }

    #[test]
    fn murmur3_deterministic() {
        let data = [0xabu8; 20];
        let h1 = murmur3_x86_32(&data, MURMUR_SEED);
        let h2 = murmur3_x86_32(&data, MURMUR_SEED);
        assert_eq!(h1, h2);
    }

    /// hash160 of private key 1 (compressed) -- same vector `crypto.rs`'s
    /// tests assert the address for, cross-checking the two modules agree
    /// on what "key 1" hashes to.
    #[test]
    fn bloom_insert_sets_correct_bit_positions() {
        let h: [u8; 20] = [
            0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54, 0x94, 0x1c, 0x45, 0xd1, 0xb3,
            0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6,
        ];
        let checker = BloomChecker::from_hash160_list(&[h]);
        let m = checker.num_bits();
        let k = checker.num_hashes();
        let bits = checker.raw_bits();

        let h1 = murmur3_x86_32(&h, MURMUR_SEED) as u64;
        let h2 = murmur3_x86_32(&h, h1 as u32) as u64;

        for i in 0..k as u64 {
            let bit = h1.wrapping_add(i.wrapping_mul(h2)) % m;
            let word = (bit / 64) as usize;
            let shift = bit % 64;
            assert!((bits[word] >> shift) & 1 == 1, "bit {bit} (hash fn {i}) must be set after insert");
        }
    }

    #[test]
    fn insert_extra_adds_new_hits_without_disturbing_existing_ones() {
        // A filter sized for just one or two entries saturates most of its
        // bits (see stream_key_check.rs's `real_bloom_checker_wiring_does_
        // not_panic` doc comment) and can't demonstrate real selectivity, so
        // this pads the filter to a realistic size first -- closer to how
        // `insert_extra` is actually used (folding a handful of entries into
        // a Bloom cache sized for millions). Padding fills bytes 0..200;
        // `original`/`extra_a`/`extra_b`/`untouched` all use bytes >= 200 so
        // none of them collide with a padding entry.
        let padding: Vec<[u8; 20]> = (0u8..200).map(|i| [i; 20]).collect();
        let original: [u8; 20] = [0xffu8; 20]; // 255
        let mut entries = padding.clone();
        entries.push(original);
        let mut checker = BloomChecker::from_hash160_list(&entries);
        assert!(matches!(checker.check(&original), CheckResult::Hit));

        let extra_a: [u8; 20] = [0xc8u8; 20]; // 200
        let extra_b: [u8; 20] = [0xc9u8; 20]; // 201
        let untouched: [u8; 20] = [0xcau8; 20]; // 202
        assert!(matches!(checker.check(&extra_a), CheckResult::Miss));
        assert!(matches!(checker.check(&untouched), CheckResult::Miss));

        checker.insert_extra(&[extra_a, extra_b]);

        assert!(matches!(checker.check(&original), CheckResult::Hit), "insert_extra must not disturb pre-existing entries");
        assert!(matches!(checker.check(&extra_a), CheckResult::Hit));
        assert!(matches!(checker.check(&extra_b), CheckResult::Hit));
        assert!(matches!(checker.check(&untouched), CheckResult::Miss));
    }

    #[test]
    fn raw_bits_roundtrip() {
        let h: [u8; 20] = [0x42u8; 20];
        let checker = BloomChecker::from_hash160_list(&[h]);
        assert!(!checker.raw_bits().is_empty());
        assert_eq!(checker.num_bits(), checker.raw_bits().len() as u64 * 64);
        assert!(checker.num_hashes() > 0);
    }

    #[test]
    fn save_and_load_roundtrip() {
        let h: [u8; 20] = [0xdeu8; 20];
        let original = BloomChecker::from_hash160_list(&[h]);

        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        original.save_to_file(path).unwrap();

        let loaded = BloomChecker::load_from_file(path).unwrap();
        assert!(matches!(loaded.check(&h), CheckResult::Hit), "loaded filter must hit inserted entry");
        assert_eq!(loaded.num_bits(), original.num_bits());
        assert_eq!(loaded.num_hashes(), original.num_hashes());
        assert_eq!(loaded.raw_bits(), original.raw_bits());
    }

    #[test]
    fn load_bad_magic_returns_err() {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        std::fs::write(path, b"BADMAGIC").unwrap();
        let err = BloomChecker::load_from_file(path).err().unwrap();
        assert_eq!(err.kind(), std::io::ErrorKind::InvalidData);
    }

    #[test]
    fn load_unsupported_version_returns_err() {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        let mut data = b"BLMCACHE".to_vec();
        data.push(2);
        std::fs::write(path, data).unwrap();
        let err = BloomChecker::load_from_file(path).err().unwrap();
        assert_eq!(err.kind(), std::io::ErrorKind::InvalidData);
    }

    #[test]
    fn load_m_zero_returns_err() {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        let mut data = b"BLMCACHE".to_vec();
        data.push(1);
        data.extend_from_slice(&0u64.to_le_bytes());
        data.extend_from_slice(&1u32.to_le_bytes());
        std::fs::write(path, data).unwrap();
        assert!(BloomChecker::load_from_file(path).is_err());
    }

    #[test]
    fn load_m_not_multiple_of_64_returns_err() {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        let mut data = b"BLMCACHE".to_vec();
        data.push(1);
        data.extend_from_slice(&63u64.to_le_bytes());
        data.extend_from_slice(&1u32.to_le_bytes());
        std::fs::write(path, data).unwrap();
        assert!(BloomChecker::load_from_file(path).is_err());
    }

    #[test]
    fn load_k_zero_returns_err() {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        let mut data = b"BLMCACHE".to_vec();
        data.push(1);
        data.extend_from_slice(&64u64.to_le_bytes());
        data.extend_from_slice(&0u32.to_le_bytes());
        std::fs::write(path, data).unwrap();
        assert!(BloomChecker::load_from_file(path).is_err());
    }

    #[test]
    fn load_truncated_bits_returns_err() {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_str().unwrap();
        let mut data = b"BLMCACHE".to_vec();
        data.push(1);
        data.extend_from_slice(&128u64.to_le_bytes());
        data.extend_from_slice(&1u32.to_le_bytes());
        data.extend_from_slice(&0u64.to_le_bytes());
        std::fs::write(path, data).unwrap();
        assert!(BloomChecker::load_from_file(path).is_err());
    }

    #[test]
    fn load_missing_file_returns_err() {
        assert!(BloomChecker::load_from_file("/nonexistent/bloom.cache").is_err());
    }

    /// Loads the real production Bloom cache this project copied from
    /// key-seeker (see .gitignore's `db/*.bloom` entry) and checks a
    /// well-known funded/used address's hash160 (the genesis block coinbase
    /// output) -- an end-to-end check that this Rust reader and the file the
    /// Python reader already validated agree. Skipped (not failed) if the
    /// file hasn't been placed locally, since it's a large external asset
    /// intentionally excluded from git.
    #[test]
    fn real_bloom_cache_recognizes_genesis_address() {
        let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../../db/addresses.hash160.bloom");
        if !std::path::Path::new(path).exists() {
            eprintln!("[skip] {path} not present locally");
            return;
        }
        let checker = BloomChecker::load_from_file(path).unwrap();
        // 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
        let known_hash160: [u8; 20] =
            hex::decode("62e907b15cbf27d5425399ebf6f0fb50ebb88f18").unwrap().try_into().unwrap();
        assert!(matches!(checker.check(&known_hash160), CheckResult::Hit));
    }
}
