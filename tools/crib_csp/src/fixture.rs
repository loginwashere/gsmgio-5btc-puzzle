//! Shared fixture loading/validation used by both the `cell` and `sweep`
//! subcommands. Fixtures are always synthetic JSON exported by
//! `tools/gsmg/phase512i_rust_parity.py` (`phase512a.make_fixture` or
//! `phase512e.make_absent_fixture`) -- this module never touches FAED.

use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::fs;

/// The 25-letter checkerboard alphabet: A-Z with J omitted (matches
/// `phase484a_raw_symbol_vic_solver.LETTER_ALPHABET`).
pub const LETTER_ALPHABET: &str = "ABCDEFGHIKLMNOPQRSTUVWXYZ";

#[derive(Deserialize)]
struct FixtureFile {
    observed: String,
    width: usize,
    crib: String,
    #[serde(default)]
    order: Option<Vec<usize>>,
    #[serde(default)]
    pair: Option<[char; 2]>,
}

pub struct Fixture {
    pub observed_bytes: Vec<u8>, // 0-8 per symbol (a-i)
    pub observed_sha256: String, // of the raw JSON "observed" string, ascii
    pub width: usize,
    pub rows: usize,
    pub crib: String,
    pub blocks: Vec<Vec<u8>>,
    pub default_pair: Option<[char; 2]>,
    pub truth_column_to_chunk: Option<Vec<i64>>,
}

pub fn validate_inputs(
    observed_len: usize,
    width: usize,
    crib: &str,
    pair: &[char; 2],
) -> Result<(), String> {
    if width == 0 {
        return Err("width must be nonzero".to_string());
    }
    if !observed_len.is_multiple_of(width) {
        return Err(format!(
            "width {width} does not exactly divide the observed length {observed_len}"
        ));
    }
    if crib.is_empty() {
        return Err("crib must be non-empty".to_string());
    }
    if let Some(bad) = crib.chars().find(|c| !LETTER_ALPHABET.contains(*c)) {
        return Err(format!(
            "crib contains {bad:?}, which is outside the supported 25-letter checkerboard alphabet"
        ));
    }
    if pair[0] == pair[1] {
        return Err(format!(
            "escape pair must be two distinct symbols, got {pair:?}"
        ));
    }
    for &symbol in pair {
        if !('a'..='i').contains(&symbol) {
            return Err(format!("escape pair symbol {symbol:?} is outside a-i"));
        }
    }
    Ok(())
}

fn observed_blocks(observed: &[u8], width: usize) -> Vec<Vec<u8>> {
    let rows = observed.len() / width;
    (0..width)
        .map(|chunk| observed[chunk * rows..(chunk + 1) * rows].to_vec())
        .collect()
}

fn truth_column_to_chunk(order: &[usize]) -> Vec<i64> {
    let mut result = vec![-1i64; order.len()];
    for (chunk, &column) in order.iter().enumerate() {
        result[column] = chunk as i64;
    }
    result
}

/// Loads and validates a fixture JSON file. Fails closed: any malformed or
/// out-of-alphabet input is an error, not a best-effort guess.
pub fn load_fixture(path: &str) -> Result<Fixture, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("failed to read fixture file: {e}"))?;
    let file: FixtureFile =
        serde_json::from_str(&raw).map_err(|e| format!("failed to parse fixture JSON: {e}"))?;

    if let Some(bad) = file.observed.bytes().find(|b| !(b'a'..=b'i').contains(b)) {
        return Err(format!("observed symbol {:?} is outside a-i", bad as char));
    }
    let observed_bytes: Vec<u8> = file.observed.bytes().map(|b| b - b'a').collect();
    let observed_sha256 = {
        let mut hasher = Sha256::new();
        hasher.update(file.observed.as_bytes());
        format!("{:x}", hasher.finalize())
    };

    let default_pair = file.pair;
    if let Some(pair) = &default_pair {
        validate_inputs(observed_bytes.len(), file.width, &file.crib, pair)?;
    } else {
        // Width/crib-alphabet checks that don't depend on a pair.
        if file.width == 0 || !observed_bytes.len().is_multiple_of(file.width) {
            return Err(format!(
                "width {} does not exactly divide the observed length {}",
                file.width,
                observed_bytes.len()
            ));
        }
        if file.crib.is_empty() || file.crib.chars().any(|c| !LETTER_ALPHABET.contains(c)) {
            return Err("crib is empty or outside the supported checkerboard alphabet".to_string());
        }
    }

    let rows = observed_bytes.len() / file.width;
    let blocks = observed_blocks(&observed_bytes, file.width);
    let truth = file.order.map(|order| truth_column_to_chunk(&order));

    Ok(Fixture {
        observed_bytes,
        observed_sha256,
        width: file.width,
        rows,
        crib: file.crib,
        blocks,
        default_pair,
        truth_column_to_chunk: truth,
    })
}

pub fn resolve_pair(fixture: &Fixture, requested: &Option<String>) -> Result<[char; 2], String> {
    if let Some(p) = requested {
        let chars: Vec<char> = p.chars().collect();
        if chars.len() != 2 {
            return Err(format!("--pair must be exactly two characters, got {p:?}"));
        }
        Ok([chars[0], chars[1]])
    } else {
        fixture
            .default_pair
            .ok_or_else(|| "fixture has no default pair; pass --pair".to_string())
    }
}

/// The 36 unordered pairs from the 9 symbols a-i, in the same order as
/// Python's `itertools.combinations("abcdefghi", 2)`
/// (`phase484a_raw_symbol_vic_solver.ESCAPE_PAIRS`).
pub fn escape_pairs() -> Vec<(char, char)> {
    let symbols: Vec<char> = "abcdefghi".chars().collect();
    let mut pairs = Vec::with_capacity(36);
    for i in 0..symbols.len() {
        for j in (i + 1)..symbols.len() {
            pairs.push((symbols[i], symbols[j]));
        }
    }
    pairs
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn escape_pairs_has_36_entries_in_itertools_order() {
        let pairs = escape_pairs();
        assert_eq!(pairs.len(), 36);
        assert_eq!(pairs[0], ('a', 'b'));
        assert_eq!(pairs[1], ('a', 'c'));
        assert_eq!(pairs[7], ('a', 'i'));
        assert_eq!(pairs[8], ('b', 'c'));
        assert_eq!(pairs[35], ('h', 'i'));
    }

    #[test]
    fn validate_inputs_accepts_a_well_formed_cell() {
        assert!(validate_inputs(570, 15, "THEFLOWER", &['g', 'i']).is_ok());
    }

    #[test]
    fn validate_inputs_rejects_zero_width() {
        assert!(validate_inputs(570, 0, "THEFLOWER", &['g', 'i']).is_err());
    }

    #[test]
    fn validate_inputs_rejects_a_non_divisor_width() {
        assert!(validate_inputs(570, 7, "THEFLOWER", &['g', 'i']).is_err());
    }

    #[test]
    fn validate_inputs_rejects_an_empty_crib() {
        assert!(validate_inputs(570, 15, "", &['g', 'i']).is_err());
    }

    #[test]
    fn validate_inputs_rejects_a_letter_outside_the_checkerboard_alphabet() {
        // 'J' is not in the 25-letter checkerboard alphabet.
        assert!(validate_inputs(570, 15, "JOKER", &['g', 'i']).is_err());
    }

    #[test]
    fn validate_inputs_rejects_an_identical_pair() {
        assert!(validate_inputs(570, 15, "THEFLOWER", &['g', 'g']).is_err());
    }

    #[test]
    fn validate_inputs_rejects_a_pair_symbol_outside_a_to_i() {
        assert!(validate_inputs(570, 15, "THEFLOWER", &['g', 'z']).is_err());
    }
}
