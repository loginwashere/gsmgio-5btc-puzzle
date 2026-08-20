//! A small, exact (non-probabilistic) target list for the prize public
//! key's EC "neighbors, half and double" -- P+G, P-G, P/2, 2P, i.e. the
//! addresses a decrypt would hash to if it recovered the private key `k+1`,
//! `k-1`, `k/2 mod n`, or `2k mod n` instead of the literal prize key `k`.
//!
//! Background: a Telegram post (@AndyStunt, 2026-07-21) attached an
//! OP_RETURN reading "GSMG.io neighbors, half and double" to four Bitcoin
//! addresses, which HosterjackAGV/gsmg-5btc-puzzle's card
//! `gsmg-ec-half-double-verified` (2026-07-25) verified are exactly those
//! four EC-derived points of the prize pubkey -- rhyming with the confirmed
//! Architect-speech line "the private keys belong to half and better half".
//! Authorship is unsettled (the prize pubkey has been public since the
//! address's first spend, so anyone could compute this), but the math is
//! real, so the four points are worth an unconditional detector target
//! regardless of who posted them.
//!
//! This file does NOT trust that write-up's numbers. The prize pubkey below
//! was independently re-extracted straight from the blockchain: all six
//! transactions that have ever spent from `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7pr
//! Be` (txids `88cdb3cdca12b471551b1b26188508a14ca5fd8a415223ffb7c190381c9b
//! 9df3` and `2aa9a4a90be819d5122d70c993280785a0508f163521e7b38cebb4db0b071
//! b13`, three inputs each, via `blockstream.info/api/address/.../txs/chain`
//! on 2026-08-20) reveal the identical uncompressed pubkey in their scriptSig
//! -- `04f4d1bb...3559` below -- and `tests::pinned_prize_hash160_matches_
//! address` confirms hash160(that pubkey, uncompressed) equals the prize
//! address exactly. The four derived points and their hash160s were then
//! computed independently in this project (see `tests::rederive_from_pubkey`
//! for the same computation run again inside the test, against the pinned
//! constants below) rather than copied from the fork's numbers.
//!
//! New fact not in the fork's write-up: as of 2026-08-20 the four
//! UNCOMPRESSED-form addresses each already hold a real, distinct 5,000-sat
//! marker payment (`funded_txo_sum=5000, spent_txo_sum=0, tx_count=1`,
//! verified via the same Blockstream API) -- i.e. whoever posted the
//! OP_RETURN also funded each target address with a small proof-of-target
//! payment. The four COMPRESSED-form addresses have never been funded. Both
//! encodings are checked here regardless, exactly like every other raw-key
//! candidate in this project checks both address types.
//!
//! Why this needs its own checker rather than just feeding these hash160s
//! into the general Bloom cache: `VerifiedBloomChecker`'s mandatory API step
//! only treats a Bloom hit as real when the address currently holds a
//! positive net balance (`funded_txo_sum > spent_txo_sum`) -- the right rule
//! for a filter built from millions of addresses, where nearly every Bloom
//! hit is a false positive that balance alone can rule back out. These eight
//! hash160s are not database noise; they are a small, deliberately-chosen
//! target set, and a decrypt that recovers k+1, k-1, k/2, or 2k is worth
//! surfacing unconditionally -- independent of whether that specific
//! encoding's address happens to hold a balance right now (four of the eight
//! currently do; four never have).

use super::{BloomChecker, CheckResult, Checker, VerifiedBloomChecker};
use crate::crypto::hash160_to_address;

pub struct TargetAddress {
    pub label: &'static str,
    pub hash160: [u8; 20],
}

/// The prize public key, uncompressed SEC1 form (0x04 || X || Y), extracted
/// from the scriptSig of all six on-chain spends from the prize address --
/// see the module doc comment for the exact txids and how to re-derive this.
pub const PRIZE_PUBKEY_HEX: &str = "04f4d1bbd91e65e2a019566a17574e97dae908b784b388891848007e4f55d5a4649c73d25fc5ed8fd7227cab0be4e576c0c6404db5aa546286563e4be12bf33559";

/// hash160 of `PRIZE_PUBKEY_HEX` (uncompressed) -- must equal the prize
/// address `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`'s payload. Pinned here so
/// `tests::pinned_prize_hash160_matches_address` can cross-check it without
/// a network call.
pub const PRIZE_HASH160: [u8; 20] = [
    0xa9, 0x55, 0x32, 0x69, 0x57, 0x2a, 0x31, 0x7e, 0x39, 0xf0, 0xf5, 0x18, 0xcb, 0x87, 0xc1, 0xa0,
    0xee, 0x1d, 0xba, 0xe4,
];

/// The eight EC-derived target hash160s (four points x two address
/// encodings). Recomputed independently in `tests::rederive_from_pubkey`
/// from `PRIZE_PUBKEY_HEX` -- these are not hand-copied from any write-up.
pub const KNOWN_TARGETS: &[TargetAddress] = &[
    TargetAddress {
        label: "P+G / k+1 / compressed (never funded)",
        hash160: [
            0x9e, 0xb2, 0xe4, 0x30, 0x05, 0xaf, 0x77, 0x78, 0x3e, 0x41, 0xea, 0x70, 0x2c, 0xf3,
            0xec, 0x35, 0x85, 0xfc, 0xd7, 0x3d,
        ],
    },
    TargetAddress {
        label: "P+G / k+1 / uncompressed (funded 5,000 sats)",
        hash160: [
            0xf8, 0xfc, 0xa6, 0x92, 0xff, 0xc9, 0x0c, 0xba, 0x0c, 0x33, 0x0d, 0xc5, 0x6e, 0x02,
            0xfa, 0x8d, 0xa8, 0xd2, 0xd6, 0xe6,
        ],
    },
    TargetAddress {
        label: "P-G / k-1 / compressed (never funded)",
        hash160: [
            0x95, 0x70, 0x96, 0x2e, 0xad, 0xf4, 0x5c, 0x42, 0x2a, 0x2e, 0x59, 0xdd, 0xb9, 0xa1,
            0xd8, 0x70, 0x40, 0xca, 0x59, 0x07,
        ],
    },
    TargetAddress {
        label: "P-G / k-1 / uncompressed (funded 5,000 sats)",
        hash160: [
            0xa4, 0xae, 0x21, 0x0a, 0x25, 0xbb, 0x8e, 0x2c, 0x35, 0x9a, 0x13, 0x4f, 0xaf, 0xc2,
            0xe3, 0x0c, 0x67, 0x09, 0xdb, 0xc0,
        ],
    },
    TargetAddress {
        label: "P/2 / half / compressed (never funded)",
        hash160: [
            0x50, 0x43, 0xbb, 0x64, 0xb2, 0x5d, 0x3f, 0xe6, 0xa7, 0xa6, 0x94, 0x9f, 0xf9, 0x8f,
            0x98, 0xb2, 0x6d, 0xcd, 0x2f, 0xa7,
        ],
    },
    TargetAddress {
        label: "P/2 / half / uncompressed (funded 5,000 sats)",
        hash160: [
            0x3d, 0xe3, 0x4f, 0xca, 0x1b, 0xd6, 0xb7, 0x60, 0x72, 0x43, 0xb0, 0x31, 0x6a, 0x81,
            0x02, 0xb7, 0x59, 0x8c, 0xc9, 0xdc,
        ],
    },
    TargetAddress {
        label: "2P / double / compressed (never funded)",
        hash160: [
            0x28, 0x63, 0x01, 0xcd, 0xe5, 0x98, 0x20, 0x85, 0x1f, 0xe9, 0x2a, 0x3a, 0x9b, 0xe4,
            0xf7, 0x6f, 0x6c, 0x3e, 0xbf, 0xf8,
        ],
    },
    TargetAddress {
        label: "2P / double / uncompressed (funded 5,000 sats)",
        hash160: [
            0xc8, 0x89, 0xdf, 0xbf, 0x69, 0x84, 0x13, 0x20, 0x9b, 0x61, 0x31, 0x89, 0x52, 0x50,
            0xb8, 0x69, 0xf6, 0x85, 0x60, 0xe0,
        ],
    },
];

fn known_target_label(hash160: &[u8; 20]) -> Option<&'static str> {
    KNOWN_TARGETS
        .iter()
        .find(|t| &t.hash160 == hash160)
        .map(|t| t.label)
}

/// Wraps a `VerifiedBloomChecker` and intercepts an exact match against
/// `KNOWN_TARGETS` before delegating -- see the module doc comment for why
/// these eight addresses must never be silently dropped by the inner
/// checker's funded-balance gate. Concrete (not generic over `Checker`) so
/// `bloom()` can pass through to the real `BloomChecker` underneath, the
/// same one `main.rs::setup_keyshape` uploads to the GPU for the on-device
/// pre-filter -- this struct is meant as a drop-in replacement for
/// `VerifiedBloomChecker` at every call site that previously held one.
pub struct KnownTargetsChecker {
    inner: VerifiedBloomChecker,
}

impl KnownTargetsChecker {
    pub fn new(inner: VerifiedBloomChecker) -> Self {
        Self { inner }
    }

    /// Passthrough to the wrapped `VerifiedBloomChecker`'s raw Bloom filter
    /// -- see `VerifiedBloomChecker::bloom`'s own doc comment for why the
    /// GPU needs this.
    pub fn bloom(&self) -> &BloomChecker {
        self.inner.bloom()
    }
}

impl Checker for KnownTargetsChecker {
    fn check(&self, hash160: &[u8; 20]) -> CheckResult {
        if let Some(label) = known_target_label(hash160) {
            let address = hash160_to_address(hash160);
            eprintln!(
                "[known-targets] !!! EXACT MATCH on EC-derived target: {label} -- {address} !!! \
                 (bypassing the funded-balance gate -- this hit is real regardless of current balance)"
            );
            return CheckResult::Hit;
        }
        self.inner.check(hash160)
    }
}

/// A small exact-match list this size needs no Bloom bit array of its own to
/// stay fast; every candidate's derived hash160 is compared directly. This
/// function returns the same eight entries for insertion into the GPU-
/// uploaded Bloom filter (see `main.rs::setup_keyshape`) so the on-device
/// pre-filter (`bloom_check_key_chunks` in `aes_kdf_oracle.cu`) can also
/// flag them -- the host-side `check()` above is the final, exact word;
/// the Bloom insertion only ensures the GPU doesn't filter a real match out
/// before it ever reaches this host-side check.
pub fn all_hash160s() -> Vec<[u8; 20]> {
    KNOWN_TARGETS.iter().map(|t| t.hash160).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::{pubkey_to_hash160, pubkey_to_hash160_uncompressed};
    use secp256k1::{PublicKey, Scalar, Secp256k1, SecretKey};
    use std::sync::atomic::{AtomicBool, Ordering};

    #[test]
    fn pinned_prize_hash160_matches_address() {
        assert_eq!(
            hash160_to_address(&PRIZE_HASH160),
            "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
        );
    }

    /// Re-derives all eight `KNOWN_TARGETS` hash160s from `PRIZE_PUBKEY_HEX`
    /// using this crate's own secp256k1 dependency -- an independent
    /// recomputation of the constants above, not a copy of them. Also
    /// confirms `PRIZE_PUBKEY_HEX` itself hashes to `PRIZE_HASH160` (and so,
    /// via the test above, to the real prize address), tying the whole
    /// module to on-chain-verifiable provenance rather than a pasted number.
    #[test]
    fn rederive_from_pubkey() {
        let secp = Secp256k1::new();
        let pubkey_bytes = hex::decode(PRIZE_PUBKEY_HEX).unwrap();
        let p = PublicKey::from_slice(&pubkey_bytes).unwrap();

        assert_eq!(
            pubkey_to_hash160_uncompressed(&p),
            PRIZE_HASH160,
            "pinned pubkey must hash to the pinned prize hash160"
        );

        let one = {
            let mut b = [0u8; 32];
            b[31] = 1;
            b
        };
        let g = PublicKey::from_secret_key(&secp, &SecretKey::from_slice(&one).unwrap());
        let neg_g = g.negate(&secp);

        let p_plus_g = p.combine(&g).unwrap();
        let p_minus_g = p.combine(&neg_g).unwrap();

        // inv(2) mod n == (n+1)/2 since the secp256k1 group order n is odd:
        // 2 * (n+1)/2 = n+1 == 1 (mod n).
        let inv2_bytes =
            hex::decode("7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a1")
                .unwrap();
        let inv2 = Scalar::from_be_bytes(inv2_bytes.try_into().unwrap()).unwrap();
        let p_half = p.mul_tweak(&secp, &inv2).unwrap();

        let two = Scalar::from_be_bytes({
            let mut b = [0u8; 32];
            b[31] = 2;
            b
        })
        .unwrap();
        let p_double = p.mul_tweak(&secp, &two).unwrap();

        let expect = |point: &PublicKey, compressed_label: &str, uncompressed_label: &str| {
            let hc = pubkey_to_hash160(point);
            let hu = pubkey_to_hash160_uncompressed(point);
            assert_eq!(
                hc,
                KNOWN_TARGETS
                    .iter()
                    .find(|t| t.label == compressed_label)
                    .unwrap()
                    .hash160,
                "{compressed_label}"
            );
            assert_eq!(
                hu,
                KNOWN_TARGETS
                    .iter()
                    .find(|t| t.label == uncompressed_label)
                    .unwrap()
                    .hash160,
                "{uncompressed_label}"
            );
        };

        expect(
            &p_plus_g,
            "P+G / k+1 / compressed (never funded)",
            "P+G / k+1 / uncompressed (funded 5,000 sats)",
        );
        expect(
            &p_minus_g,
            "P-G / k-1 / compressed (never funded)",
            "P-G / k-1 / uncompressed (funded 5,000 sats)",
        );
        expect(
            &p_half,
            "P/2 / half / compressed (never funded)",
            "P/2 / half / uncompressed (funded 5,000 sats)",
        );
        expect(
            &p_double,
            "2P / double / compressed (never funded)",
            "2P / double / uncompressed (funded 5,000 sats)",
        );
    }

    #[test]
    fn all_hash160s_returns_all_eight() {
        assert_eq!(all_hash160s().len(), 8);
    }

    struct ConstChecker(bool);
    impl Checker for ConstChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            if self.0 {
                CheckResult::Hit
            } else {
                CheckResult::Miss
            }
        }
    }

    struct SpyChecker {
        called: std::sync::Arc<AtomicBool>,
    }
    impl Checker for SpyChecker {
        fn check(&self, _: &[u8; 20]) -> CheckResult {
            self.called.store(true, Ordering::SeqCst);
            CheckResult::Miss
        }
    }

    fn verified_with_verifier(
        bloom: BloomChecker,
        verifier: std::sync::Arc<dyn Checker>,
    ) -> VerifiedBloomChecker {
        VerifiedBloomChecker::new_with_verifier(bloom, verifier)
    }

    #[test]
    fn known_target_hits_even_when_inner_would_miss() {
        // Inner's Bloom filter has never seen any of our targets, and its
        // verifier always says Miss -- a stand-in for "this address has
        // never been funded," which is literally true for 4 of the 8.
        let unrelated = [0x11u8; 20];
        let inner = verified_with_verifier(
            BloomChecker::from_hash160_list(&[unrelated]),
            std::sync::Arc::new(ConstChecker(false)),
        );
        let checker = KnownTargetsChecker::new(inner);
        let h = KNOWN_TARGETS[0].hash160;
        assert!(
            matches!(checker.check(&h), CheckResult::Hit),
            "an exact known-target match must always be a Hit, regardless of the inner checker's balance/Bloom verdict"
        );
    }

    #[test]
    fn known_target_match_never_calls_inner_verifier() {
        let called = std::sync::Arc::new(AtomicBool::new(false));
        let spy = SpyChecker {
            called: called.clone(),
        };
        let inner = verified_with_verifier(
            BloomChecker::from_hash160_list(&[[0x11u8; 20]]),
            std::sync::Arc::new(spy),
        );
        let checker = KnownTargetsChecker::new(inner);
        let h = KNOWN_TARGETS[3].hash160;
        let _ = checker.check(&h);
        assert!(!called.load(Ordering::SeqCst), "a known-target exact match must short-circuit before ever reaching the inner checker's API verifier");
    }

    #[test]
    fn unrelated_hash160_falls_through_to_inner() {
        let unrelated = [0x77u8; 20];
        let hit_inner = verified_with_verifier(
            BloomChecker::from_hash160_list(&[unrelated]),
            std::sync::Arc::new(ConstChecker(true)),
        );
        let checker = KnownTargetsChecker::new(hit_inner);
        assert!(matches!(checker.check(&unrelated), CheckResult::Hit));

        let other = [0x88u8; 20];
        let miss_inner = verified_with_verifier(
            BloomChecker::from_hash160_list(&[unrelated]),
            std::sync::Arc::new(ConstChecker(true)),
        );
        let checker_miss = KnownTargetsChecker::new(miss_inner);
        assert!(
            matches!(checker_miss.check(&other), CheckResult::Miss),
            "a hash160 outside both the known-target list and the inner Bloom filter must miss"
        );
    }

    #[test]
    fn bloom_passthrough_reaches_inner_filter() {
        let target = [0x99u8; 20];
        let inner = verified_with_verifier(
            BloomChecker::from_hash160_list(&[target]),
            std::sync::Arc::new(ConstChecker(true)),
        );
        let checker = KnownTargetsChecker::new(inner);
        assert!(matches!(checker.bloom().check(&target), CheckResult::Hit));
    }

    #[test]
    fn all_eight_targets_are_distinct() {
        let mut seen = std::collections::HashSet::new();
        for t in KNOWN_TARGETS {
            assert!(seen.insert(t.hash160), "duplicate hash160 for {}", t.label);
        }
    }
}
