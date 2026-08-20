//! Bloom + API funded-address checking, ported from
//! ../../../key-seeker's src/checker/{mod,bloom,api,verified}.rs -- reused
//! rather than reimplemented so this project has one tested Bloom/API code
//! path instead of a second one drifting alongside the Python
//! `binary_key_material_backfill.py`/`key_shape_sweep.py` pipeline.
//! `combined.rs` and `puzzle.rs` are not ported: this project only needs
//! "Bloom, then mandatory API verification", not an OR-combine, and
//! `puzzle.rs` targets a different (Bitcoin Puzzle #N) project.

pub mod api;
pub mod bloom;
pub mod known_targets;
pub mod verified;

pub enum CheckResult {
    Hit,
    Miss,
}

/// Common trait for all checker backends. Takes only hash160 -- no address
/// string computed in the hot path; the caller derives it only on a Hit.
pub trait Checker: Send + Sync {
    fn check(&self, hash160: &[u8; 20]) -> CheckResult;
}

pub use api::ApiChecker;
pub use bloom::BloomChecker;
pub use known_targets::KnownTargetsChecker;
pub use verified::VerifiedBloomChecker;
