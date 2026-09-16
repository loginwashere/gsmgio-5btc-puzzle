//! Faithful port of `phase484a_raw_symbol_vic_solver.Geometry.decrypt` and
//! `segment_raw`, specialized to the exact-divisor widths (15/19/30/38) that
//! Phase 512 uses for the 570-symbol FAED stream, where every column has the
//! same length (`rows = length / width`) and `short_count` is always zero.
//!
//! `accepts_token_boundary` (phase512d.py) builds `order` as
//! `order = [0] * width; for column, chunk in enumerate(column_to_chunk): order[chunk] = column`.
//! Unconstrained columns leave `chunk == -1`, and Python's negative indexing
//! sends that write to `order[width - 1]`. This is reproduced exactly below
//! (`idx = width - 1` when `chunk < 0`) rather than "fixed", because the goal
//! is provable byte-for-byte parity with the frozen reference, not a cleaner
//! reimplementation. In practice this path is never exercised for any crib in
//! this phase, since every crib's raw span exceeds every candidate width, so
//! `constrained_columns` always covers all columns and no column is ever left
//! at -1 when a real hit is checked.

pub fn decrypt_raw(
    blocks: &[Vec<u8>],
    width: usize,
    rows: usize,
    column_to_chunk: &[i64],
) -> Option<Vec<u8>> {
    let mut order = vec![0usize; width];
    for (column, &chunk) in column_to_chunk.iter().enumerate() {
        let idx = if chunk < 0 { width - 1 } else { chunk as usize };
        if idx >= width {
            return None;
        }
        order[idx] = column;
    }
    let mut columns: Vec<Option<&[u8]>> = vec![None; width];
    for (chunk_index, &raw_column) in order.iter().enumerate() {
        columns[raw_column] = Some(&blocks[chunk_index]);
    }
    let mut raw = vec![0u8; width * rows];
    for (position, slot) in raw.iter_mut().enumerate() {
        let column = position % width;
        let row = position / width;
        let block = columns[column]?;
        if row >= block.len() {
            return None;
        }
        *slot = block[row];
    }
    Some(raw)
}

pub fn segment_raw_ok(raw: &[u8], escapes: (u8, u8)) -> bool {
    let mut i = 0;
    while i < raw.len() {
        if raw[i] == escapes.0 || raw[i] == escapes.1 {
            if i + 1 >= raw.len() {
                return false;
            }
            i += 2;
        } else {
            i += 1;
        }
    }
    true
}

pub fn accepts_token_boundary(
    column_to_chunk: &[i64],
    blocks: &[Vec<u8>],
    width: usize,
    rows: usize,
    raw_start: usize,
    escapes: (u8, u8),
) -> bool {
    match decrypt_raw(blocks, width, rows, column_to_chunk) {
        None => false,
        Some(raw) => {
            if raw_start > raw.len() {
                return false;
            }
            segment_raw_ok(&raw[..raw_start], escapes) && segment_raw_ok(&raw, escapes)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn segment_raw_ok_accepts_empty_and_plain_symbols() {
        let escapes = (7u8, 8u8);
        assert!(segment_raw_ok(&[], escapes));
        assert!(segment_raw_ok(&[1, 2, 3], escapes));
    }

    #[test]
    fn segment_raw_ok_consumes_two_bytes_after_an_escape_symbol() {
        let escapes = (7u8, 8u8);
        assert!(segment_raw_ok(&[7, 1, 2], escapes));
        assert!(segment_raw_ok(&[1, 8, 2, 3], escapes));
    }

    #[test]
    fn segment_raw_ok_rejects_a_trailing_lone_escape_symbol() {
        let escapes = (7u8, 8u8);
        assert!(!segment_raw_ok(&[7], escapes));
        assert!(!segment_raw_ok(&[1, 2, 8], escapes));
    }

    #[test]
    fn decrypt_raw_inverts_a_known_column_permutation() {
        // Raw row-major stream (width=2, rows=3): column 0 = [0,2,4],
        // column 1 = [1,3,5]. Transposition places raw column 0 at physical
        // chunk 1 and raw column 1 at physical chunk 0.
        let blocks = vec![vec![1u8, 3, 5], vec![0u8, 2, 4]];
        let column_to_chunk = vec![1i64, 0];
        let raw = decrypt_raw(&blocks, 2, 3, &column_to_chunk).expect("decrypt should succeed");
        assert_eq!(raw, vec![0, 1, 2, 3, 4, 5]);
    }

    #[test]
    fn decrypt_raw_rejects_a_chunk_index_past_the_block_count() {
        let blocks = vec![vec![1u8, 3, 5], vec![0u8, 2, 4]];
        let column_to_chunk = vec![5i64, 0];
        assert!(decrypt_raw(&blocks, 2, 3, &column_to_chunk).is_none());
    }
}
