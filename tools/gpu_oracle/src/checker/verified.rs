//! Ported from ../../../key-seeker's src/checker/verified.rs. Same
//! "Bloom pre-filters, API mandatorily confirms" contract the Python side's
//! `binary_key_material_backfill.py` queue/`--verify-queue` split already
//! enforces -- a Bloom hit alone is never treated as a real hit here either.

use super::api::ApiChecker;
use super::{BloomChecker, CheckResult, Checker};
use crate::crypto::hash160_to_address;
use std::sync::Arc;

pub struct VerifiedBloomChecker {
    bloom: BloomChecker,
    verifier: Arc<dyn Checker>,
}

impl VerifiedBloomChecker {
    pub fn new(bloom: BloomChecker) -> Self {
        Self { bloom, verifier: Arc::new(ApiChecker::new()) }
    }

    #[cfg(test)]
    pub fn new_with_verifier(bloom: BloomChecker, verifier: Arc<dyn Checker>) -> Self {
        Self { bloom, verifier }
    }

    /// The raw Bloom filter, without the mandatory-API-confirmation wrapper
    /// -- used to upload the filter's bits to GPU memory once for
    /// `gpu.rs::scan`'s on-device stream-mode check (which still routes any
    /// resulting hit back through this same `VerifiedBloomChecker` via
    /// `keyshape::record_precomputed_hit`'s `checker` argument for the
    /// actual API confirmation, so the "Bloom alone is never a real hit"
    /// contract is unaffected).
    pub fn bloom(&self) -> &BloomChecker {
        &self.bloom
    }
}

impl Checker for VerifiedBloomChecker {
    fn check(&self, hash160: &[u8; 20]) -> CheckResult {
        if let CheckResult::Miss = self.bloom.check(hash160) {
            return CheckResult::Miss;
        }

        let address = hash160_to_address(hash160);
        eprintln!("[verify] Bloom hit for {address} -- querying Blockstream API...");

        match self.verifier.check(hash160) {
            CheckResult::Hit => {
                eprintln!("[verify] CONFIRMED funded address: {address}");
                CheckResult::Hit
            }
            CheckResult::Miss => {
                eprintln!("[verify] False positive discarded: {address}");
                CheckResult::Miss
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicBool, Ordering};

    struct ConstChecker(bool);
    impl Checker for ConstChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            if self.0 { CheckResult::Hit } else { CheckResult::Miss }
        }
    }

    struct PanicChecker;
    impl Checker for PanicChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            panic!("verifier must not be called on a bloom miss");
        }
    }

    struct SpyChecker { called: Arc<AtomicBool>, result: bool }
    impl Checker for SpyChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            self.called.store(true, Ordering::SeqCst);
            if self.result { CheckResult::Hit } else { CheckResult::Miss }
        }
    }

    fn h_in_bloom() -> [u8; 20] { [0x01u8; 20] }
    fn h_not_in_bloom() -> [u8; 20] { [0x02u8; 20] }

    fn bloom_with(h: [u8; 20]) -> BloomChecker {
        BloomChecker::from_hash160_list(&[h])
    }

    #[test]
    fn bloom_miss_skips_verifier() {
        let checker = VerifiedBloomChecker::new_with_verifier(bloom_with(h_in_bloom()), Arc::new(PanicChecker));
        assert!(matches!(checker.check(&h_not_in_bloom()), CheckResult::Miss));
    }

    #[test]
    fn bloom_hit_and_verifier_hit_is_hit() {
        let checker =
            VerifiedBloomChecker::new_with_verifier(bloom_with(h_in_bloom()), Arc::new(ConstChecker(true)));
        assert!(matches!(checker.check(&h_in_bloom()), CheckResult::Hit));
    }

    #[test]
    fn bloom_hit_and_verifier_miss_is_miss() {
        let checker =
            VerifiedBloomChecker::new_with_verifier(bloom_with(h_in_bloom()), Arc::new(ConstChecker(false)));
        assert!(matches!(checker.check(&h_in_bloom()), CheckResult::Miss));
    }

    #[test]
    fn new_constructor_creates_checker_without_panic() {
        let bloom = bloom_with(h_in_bloom());
        let _checker = VerifiedBloomChecker::new(bloom);
    }

    #[test]
    fn verifier_called_on_bloom_hit() {
        let called = Arc::new(AtomicBool::new(false));
        let spy = SpyChecker { called: Arc::clone(&called), result: false };
        let checker = VerifiedBloomChecker::new_with_verifier(bloom_with(h_in_bloom()), Arc::new(spy));
        let _ = checker.check(&h_in_bloom());
        assert!(called.load(Ordering::SeqCst), "verifier must be called on a bloom hit");
    }
}
