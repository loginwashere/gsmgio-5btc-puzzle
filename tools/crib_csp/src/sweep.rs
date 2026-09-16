//! In-process deterministic parallel batch runner (Rust-port plan step 4).
//!
//! Mirrors `phase512e_parallel_blind_crib.scan_fixture`'s architecture:
//! raw-start-major scheduling, every escape-pair branch at a start completed
//! and retained (in pair-index order, not worker-completion order) before
//! the search advances or stops, and a resumable JSON checkpoint. Unlike
//! Python's `ProcessPoolExecutor`, the fixture (including the length-pattern
//! table, which can be hundreds of thousands of entries) is built once and
//! shared read-only across a rayon thread pool instead of being re-sent to
//! a fresh OS process per cell.

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;
use std::time::Instant;

use crate::csp::{self, CribShape, PatternMask};
use crate::fixture::{escape_pairs, Fixture};

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct SweepIdentity {
    pub schema: String,
    pub observed_sha256: String,
    pub crib_sha256: String,
    pub width: usize,
    pub legal_length_pattern_count: usize,
    pub patterns_sha256: String,
    pub start_begin: usize,
    pub start_count: usize,
    pub pair_begin: usize,
    pub pair_count: usize,
    pub node_limit: u64,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct CellHit {
    pub pattern_index: usize,
    pub single_letters: String,
    pub column_to_chunk: Vec<i64>,
    pub exact_truth: Option<bool>,
    pub nodes_for_pattern: u64,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct CellSummary {
    pub pair_index: usize,
    pub pair: [char; 2],
    pub legal_length_pattern_count: usize,
    pub patterns_tested: usize,
    pub total_nodes: u64,
    pub node_limit_reached: bool,
    pub search_complete: bool,
    pub hit_count: usize,
    pub hits: Vec<CellHit>,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct StartRow {
    pub raw_start: usize,
    pub cells: Vec<CellSummary>,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct HitRef {
    pub raw_start: usize,
    pub pair_index: usize,
    pub pair: [char; 2],
    pub hits: Vec<CellHit>,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct IncompleteRef {
    pub raw_start: usize,
    pub pair_index: usize,
    pub total_nodes: u64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Checkpoint {
    pub identity: SweepIdentity,
    pub completed_starts: Vec<StartRow>,
    pub status: String,
    pub hit_cells: Vec<HitRef>,
    pub incomplete_cells: Vec<IncompleteRef>,
    pub starts_completed: usize,
    pub pair_start_cells_completed: usize,
    pub last_session_elapsed_seconds: f64,
}

fn sha256_hex(data: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_bytes());
    format!("{:x}", hasher.finalize())
}

fn solve_cell(
    fixture: &Fixture,
    shape: &CribShape,
    patterns: &[PatternMask],
    pair_index: usize,
    pair: (char, char),
    raw_start: usize,
    node_limit: u64,
) -> CellSummary {
    let escapes: (u8, u8) = (pair.0 as u8 - b'a', pair.1 as u8 - b'a');
    let result = csp::search_lengths_at_start(
        shape,
        patterns,
        &fixture.blocks,
        fixture.width,
        fixture.rows,
        escapes,
        raw_start,
        fixture.observed_bytes.len(),
        node_limit,
        fixture.truth_column_to_chunk.as_deref(),
    );
    CellSummary {
        pair_index,
        pair: [pair.0, pair.1],
        legal_length_pattern_count: result.legal_length_pattern_count,
        patterns_tested: result.patterns_tested,
        total_nodes: result.total_nodes,
        node_limit_reached: result.node_limit_reached,
        search_complete: result.search_complete,
        hit_count: result.hits.len(),
        hits: result
            .hits
            .into_iter()
            .map(|h| CellHit {
                pattern_index: h.pattern_index,
                single_letters: h.single_letters,
                column_to_chunk: h.column_to_chunk,
                exact_truth: h.exact_truth,
                nodes_for_pattern: h.nodes_for_pattern,
            })
            .collect(),
    }
}

fn summarize(checkpoint: &mut Checkpoint) {
    let mut hits = Vec::new();
    let mut incomplete = Vec::new();
    for row in &checkpoint.completed_starts {
        for cell in &row.cells {
            if cell.hit_count > 0 {
                hits.push(HitRef {
                    raw_start: row.raw_start,
                    pair_index: cell.pair_index,
                    pair: cell.pair,
                    hits: cell.hits.clone(),
                });
            }
            if !cell.search_complete {
                incomplete.push(IncompleteRef {
                    raw_start: row.raw_start,
                    pair_index: cell.pair_index,
                    total_nodes: cell.total_nodes,
                });
            }
        }
    }
    checkpoint.starts_completed = checkpoint.completed_starts.len();
    checkpoint.pair_start_cells_completed = checkpoint
        .completed_starts
        .iter()
        .map(|r| r.cells.len())
        .sum();
    checkpoint.status = if !incomplete.is_empty() {
        "incomplete_node_limit".to_string()
    } else if !hits.is_empty() {
        "hit_at_earliest_completed_start".to_string()
    } else if checkpoint.starts_completed == checkpoint.identity.start_count {
        "no_hit_in_complete_requested_family".to_string()
    } else {
        "in_progress".to_string()
    };
    checkpoint.hit_cells = hits;
    checkpoint.incomplete_cells = incomplete;
}

fn atomic_write_json<T: Serialize>(path: &Path, value: &T) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let tmp = path.with_extension("tmp");
    let text = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(&tmp, text).map_err(|e| e.to_string())?;
    fs::rename(&tmp, path).map_err(|e| e.to_string())?;
    Ok(())
}

pub struct SweepArgs {
    pub start_begin: usize,
    pub start_count: usize,
    pub pair_begin: usize,
    pub pair_count: usize,
    pub node_limit: u64,
    pub checkpoint_path: Option<String>,
}

/// Mirrors Python's `maximum_start = len(observed) - len(crib)` bound
/// (`phase512d.run_blind_start_and_lengths`, `phase512e.scan_fixture`):
/// the crib's letter count is the minimum possible raw span (every letter
/// single-coded), so no start past this point can ever fit.
fn maximum_start(fixture: &Fixture) -> usize {
    fixture
        .observed_bytes
        .len()
        .saturating_sub(fixture.crib.chars().count())
}

fn patterns_sha256(patterns: &[PatternMask]) -> String {
    let mut hasher = Sha256::new();
    for (index, &mask) in patterns.iter().enumerate() {
        if index > 0 {
            hasher.update(b",");
        }
        hasher.update(mask.to_string().as_bytes());
    }
    format!("{:x}", hasher.finalize())
}

/// Fail-closed re-derivation of a loaded checkpoint's structure: contiguous
/// starts, the exact requested pair set in order, and matching pair labels.
/// Never trusts the checkpoint's own stored `status`/`hit_cells`/
/// `incomplete_cells` -- those are recomputed by `summarize` after this
/// passes, exactly like Python's `_validate_checkpoint` + `_summarize`.
fn validate_checkpoint_structure(
    checkpoint: &Checkpoint,
    all_pairs: &[(char, char)],
) -> Result<(), String> {
    let identity = &checkpoint.identity;
    if checkpoint.completed_starts.len() > identity.start_count {
        return Err(format!(
            "checkpoint has {} completed starts, more than the requested start_count {}",
            checkpoint.completed_starts.len(),
            identity.start_count
        ));
    }
    let expected_pair_indices: Vec<usize> =
        (identity.pair_begin..identity.pair_begin + identity.pair_count).collect();
    for (offset, row) in checkpoint.completed_starts.iter().enumerate() {
        let expected_start = identity.start_begin + offset;
        if row.raw_start != expected_start {
            return Err(format!(
                "checkpoint starts are not contiguous: row {offset} has raw_start {}, expected {expected_start}",
                row.raw_start
            ));
        }
        let actual_pair_indices: Vec<usize> = row.cells.iter().map(|c| c.pair_index).collect();
        if actual_pair_indices != expected_pair_indices {
            return Err(format!(
                "checkpoint pair set/order is incomplete or wrong at raw_start {expected_start}"
            ));
        }
        for cell in &row.cells {
            let expected = all_pairs[cell.pair_index];
            if cell.pair != [expected.0, expected.1] {
                return Err(format!(
                    "checkpoint pair label mismatch at raw_start {expected_start}, pair_index {}",
                    cell.pair_index
                ));
            }
        }
    }
    Ok(())
}

pub fn run_sweep(fixture: &Fixture, args: SweepArgs) -> Result<Checkpoint, String> {
    let all_pairs = escape_pairs();
    if args.pair_begin + args.pair_count > all_pairs.len() {
        return Err(format!(
            "pair range [{}, {}) exceeds the 36-pair family",
            args.pair_begin,
            args.pair_begin + args.pair_count
        ));
    }
    if args.start_count == 0 {
        return Err("start_count must be positive".to_string());
    }
    if args.pair_count == 0 {
        return Err("pair_count must be positive".to_string());
    }
    let legal_maximum_start = maximum_start(fixture);
    let last_requested_start = args
        .start_begin
        .checked_add(args.start_count)
        .and_then(|end| end.checked_sub(1))
        .ok_or_else(|| "start_begin + start_count overflowed".to_string())?;
    if last_requested_start > legal_maximum_start {
        return Err(format!(
            "start range [{}, {}) exceeds the legal family [0, {}] (crib length {} vs observed length {})",
            args.start_begin,
            args.start_begin + args.start_count,
            legal_maximum_start,
            fixture.crib.chars().count(),
            fixture.observed_bytes.len()
        ));
    }
    let pair_slice = &all_pairs[args.pair_begin..args.pair_begin + args.pair_count];

    let shape = csp::crib_shape(&fixture.crib);
    let patterns = csp::length_patterns(shape.k);

    let identity = SweepIdentity {
        schema: "crib_csp-sweep-v1".to_string(),
        observed_sha256: fixture.observed_sha256.clone(),
        crib_sha256: sha256_hex(&fixture.crib),
        width: fixture.width,
        legal_length_pattern_count: patterns.len(),
        patterns_sha256: patterns_sha256(&patterns),
        start_begin: args.start_begin,
        start_count: args.start_count,
        pair_begin: args.pair_begin,
        pair_count: args.pair_count,
        node_limit: args.node_limit,
    };

    let mut checkpoint = match &args.checkpoint_path {
        Some(path) if Path::new(path).exists() => {
            let text =
                fs::read_to_string(path).map_err(|e| format!("failed to read checkpoint: {e}"))?;
            let mut existing: Checkpoint = serde_json::from_str(&text)
                .map_err(|e| format!("failed to parse checkpoint: {e}"))?;
            if existing.identity != identity {
                return Err(
                    "checkpoint identity does not match this sweep's parameters".to_string()
                );
            }
            validate_checkpoint_structure(&existing, &all_pairs)?;
            // Never trust the checkpoint's own stored status/hit/incomplete
            // fields -- recompute them from the validated raw cells.
            summarize(&mut existing);
            existing
        }
        _ => Checkpoint {
            identity: identity.clone(),
            completed_starts: Vec::new(),
            status: "in_progress".to_string(),
            hit_cells: Vec::new(),
            incomplete_cells: Vec::new(),
            starts_completed: 0,
            pair_start_cells_completed: 0,
            last_session_elapsed_seconds: 0.0,
        },
    };
    if checkpoint.status != "in_progress" {
        return Ok(checkpoint);
    }

    let started = Instant::now();
    let first_unfinished = args.start_begin + checkpoint.completed_starts.len();
    let stop = args.start_begin + args.start_count;

    for raw_start in first_unfinished..stop {
        let mut cells: Vec<CellSummary> = pair_slice
            .par_iter()
            .enumerate()
            .map(|(offset, &pair)| {
                let pair_index = args.pair_begin + offset;
                solve_cell(
                    fixture,
                    &shape,
                    &patterns,
                    pair_index,
                    pair,
                    raw_start,
                    args.node_limit,
                )
            })
            .collect();
        cells.sort_by_key(|c| c.pair_index);
        checkpoint
            .completed_starts
            .push(StartRow { raw_start, cells });
        summarize(&mut checkpoint);
        checkpoint.last_session_elapsed_seconds = started.elapsed().as_secs_f64();
        if let Some(path) = &args.checkpoint_path {
            atomic_write_json(Path::new(path), &checkpoint)?;
        }
        if checkpoint.status != "in_progress" {
            break;
        }
    }
    summarize(&mut checkpoint);
    checkpoint.last_session_elapsed_seconds = started.elapsed().as_secs_f64();
    if let Some(path) = &args.checkpoint_path {
        atomic_write_json(Path::new(path), &checkpoint)?;
    }
    Ok(checkpoint)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::fixture::Fixture;

    /// A tiny, structurally valid fixture (not a real Model-B round trip --
    /// these tests only exercise `run_sweep`'s range/checkpoint validation,
    /// never real search correctness, which is covered by `csp`'s own tests
    /// and the Python parity battery).
    fn tiny_fixture() -> Fixture {
        let observed_bytes: Vec<u8> = vec![0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 1, 2];
        let width = 3;
        let rows = 4;
        let blocks = (0..width)
            .map(|c| observed_bytes[c * rows..(c + 1) * rows].to_vec())
            .collect();
        Fixture {
            observed_bytes,
            observed_sha256: "test".to_string(),
            width,
            rows,
            crib: "AB".to_string(),
            blocks,
            default_pair: Some(['a', 'b']),
            truth_column_to_chunk: None,
        }
    }

    #[test]
    fn run_sweep_rejects_a_start_range_past_the_legal_family() {
        let fixture = tiny_fixture();
        // maximum_start = observed_len(12) - crib_len(2) = 10, so start 11 is illegal.
        let args = SweepArgs {
            start_begin: 11,
            start_count: 1,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: None,
        };
        let result = run_sweep(&fixture, args);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("exceeds the legal family"));
    }

    #[test]
    fn run_sweep_rejects_zero_start_count() {
        let fixture = tiny_fixture();
        let args = SweepArgs {
            start_begin: 0,
            start_count: 0,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: None,
        };
        assert!(run_sweep(&fixture, args).is_err());
    }

    #[test]
    fn run_sweep_accepts_a_valid_start_range() {
        let fixture = tiny_fixture();
        let args = SweepArgs {
            start_begin: 0,
            start_count: 1,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: None,
        };
        let result = run_sweep(&fixture, args);
        assert!(result.is_ok());
    }

    #[test]
    fn run_sweep_rejects_zero_pair_count() {
        // A zero pair_count must not report a hollow "complete" result --
        // it would have tested nothing.
        let fixture = tiny_fixture();
        let args = SweepArgs {
            start_begin: 0,
            start_count: 1,
            pair_begin: 0,
            pair_count: 0,
            node_limit: 1000,
            checkpoint_path: None,
        };
        assert!(run_sweep(&fixture, args).is_err());
    }

    #[test]
    fn run_sweep_rejects_a_checkpoint_with_more_rows_than_requested_start_count() {
        // Built by hand rather than by running two real starts and hoping
        // for a particular hit/no-hit outcome: this test only exercises
        // run_sweep's own bookkeeping, not the tiny fixture's incidental
        // search result.
        let fixture = tiny_fixture();
        let dir = tempfile::tempdir().unwrap();
        let path = dir
            .path()
            .join("checkpoint.json")
            .to_str()
            .unwrap()
            .to_string();

        // Match exactly what run_sweep will independently recompute, so the
        // identity comparison passes and the test actually reaches (and
        // exercises) validate_checkpoint_structure.
        let shape = csp::crib_shape(&fixture.crib);
        let real_patterns = csp::length_patterns(shape.k);

        let cell = CellSummary {
            pair_index: 0,
            pair: ['a', 'b'],
            legal_length_pattern_count: real_patterns.len(),
            patterns_tested: real_patterns.len(),
            total_nodes: 1,
            node_limit_reached: false,
            search_complete: true,
            hit_count: 0,
            hits: Vec::new(),
        };
        let identity = SweepIdentity {
            schema: "crib_csp-sweep-v1".to_string(),
            observed_sha256: fixture.observed_sha256.clone(),
            crib_sha256: sha256_hex(&fixture.crib),
            width: fixture.width,
            legal_length_pattern_count: real_patterns.len(),
            patterns_sha256: patterns_sha256(&real_patterns),
            start_begin: 0,
            // Claims only 1 start is in scope...
            start_count: 1,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
        };
        let bogus = Checkpoint {
            identity: identity.clone(),
            // ...but ships 2 completed rows anyway.
            completed_starts: vec![
                StartRow {
                    raw_start: 0,
                    cells: vec![cell.clone()],
                },
                StartRow {
                    raw_start: 1,
                    cells: vec![cell],
                },
            ],
            status: "in_progress".to_string(),
            hit_cells: Vec::new(),
            incomplete_cells: Vec::new(),
            starts_completed: 2,
            pair_start_cells_completed: 2,
            last_session_elapsed_seconds: 0.0,
        };
        fs::write(&path, serde_json::to_string(&bogus).unwrap()).unwrap();

        let resume_args = SweepArgs {
            start_begin: identity.start_begin,
            start_count: identity.start_count,
            pair_begin: identity.pair_begin,
            pair_count: identity.pair_count,
            node_limit: identity.node_limit,
            checkpoint_path: Some(path),
        };
        let result = run_sweep(&fixture, resume_args);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .contains("more than the requested start_count"));
    }

    #[test]
    fn run_sweep_rejects_a_checkpoint_with_a_noncontiguous_start() {
        let fixture = tiny_fixture();
        let dir = tempfile::tempdir().unwrap();
        let path = dir
            .path()
            .join("checkpoint.json")
            .to_str()
            .unwrap()
            .to_string();

        let args = SweepArgs {
            start_begin: 0,
            start_count: 2,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: Some(path.clone()),
        };
        let first = run_sweep(&fixture, args).unwrap();
        assert!(!first.completed_starts.is_empty());

        // Corrupt the checkpoint on disk: rewrite the first row's raw_start
        // and force status back to "in_progress" (as if resuming), exactly
        // mirroring the manual corruption used to find this bug.
        let mut corrupted: Checkpoint =
            serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        corrupted.status = "in_progress".to_string();
        corrupted.completed_starts[0].raw_start = 999;
        fs::write(&path, serde_json::to_string(&corrupted).unwrap()).unwrap();

        let resume_args = SweepArgs {
            start_begin: 0,
            start_count: 2,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: Some(path),
        };
        let result = run_sweep(&fixture, resume_args);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("not contiguous"));
    }

    #[test]
    fn run_sweep_recomputes_status_instead_of_trusting_a_stored_lie() {
        let fixture = tiny_fixture();
        let dir = tempfile::tempdir().unwrap();
        let path = dir
            .path()
            .join("checkpoint.json")
            .to_str()
            .unwrap()
            .to_string();

        let args = SweepArgs {
            start_begin: 0,
            start_count: 1,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: Some(path.clone()),
        };
        let first = run_sweep(&fixture, args).unwrap();
        let true_status = first.status.clone();
        // Whatever this tiny, structurally-valid-but-not-a-real-Model-B
        // fixture actually resolves to (this test only cares about
        // checkpoint plumbing, not search correctness), it must be settled,
        // not "in_progress".
        assert_ne!(true_status, "in_progress");

        // Plant a lie in the *opposite* direction of what really happened,
        // and force status back to "in_progress" so run_sweep treats this
        // as a resumable checkpoint. A structurally valid but semantically
        // false stored status/summary must not survive a resume:
        // summarize() always overwrites it from the real per-cell data.
        let mut lied: Checkpoint =
            serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        lied.status = "in_progress".to_string();
        if true_status == "no_hit_in_complete_requested_family" {
            lied.hit_cells.push(HitRef {
                raw_start: 0,
                pair_index: 0,
                pair: ['a', 'b'],
                hits: Vec::new(),
            });
        } else {
            lied.hit_cells.clear();
            lied.incomplete_cells.push(IncompleteRef {
                raw_start: 0,
                pair_index: 0,
                total_nodes: 0,
            });
        }
        fs::write(&path, serde_json::to_string(&lied).unwrap()).unwrap();

        let resume_args = SweepArgs {
            start_begin: 0,
            start_count: 1,
            pair_begin: 0,
            pair_count: 1,
            node_limit: 1000,
            checkpoint_path: Some(path),
        };
        let result = run_sweep(&fixture, resume_args).unwrap();
        assert_eq!(result.status, true_status);
    }
}
