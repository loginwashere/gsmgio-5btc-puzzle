#!/usr/bin/env python3
"""Phase 403: executes a user-identified coverage gap in the 2026-08-25
BTCSEED/P91/Z continuation brainstorm's now-exhausted ranked queue --
Phase 397's eight raw 59-byte control-channel outputs, consumed directly
as BIP32 seed material, never hashed or reinterpreted.

**Origin:** identified in a 2026-08-25 follow-up survey of the
brainstorm's 100-item idea bank (not itself part of the ranked queue,
Priorities 1-6, all closed negative as Phases 397-402): Phase 397 only
ever ran typed-container/key-format scanners on its eight 59-byte
candidates; Phase 400 tested `SHA256(P90/P91/Q472/FULL570)` digests as
BIP32 seeds, never the raw Phase-397 bytes themselves. 59 bytes = 472
bits sits inside BIP32's standard 128-512-bit seed range, and the stream
begins `BTCSEED`, so this specific gap is unusually well grounded rather
than another control/data-machine variant.

**Frozen contract (as proposed and approved before this script was
written):**

- exactly Phase 397's eight 59-byte candidates (2 grid-native symbol
  mappings x 2 directions x 2 bit-packings), reused verbatim, byte-for-
  byte, with no hashing or reinterpretation;
- BIP32 consumer only: `HMAC-SHA512("Bitcoin seed", raw_59_bytes)`,
  Phase 400's identical six frozen derivation path templates
  (`m/44'/0'/0'/0/i`, `m/44'/0'/0'/1/i`, `m/0'/0/i`, `m/0'/1/i`, `m/0/i`,
  `m/1/i`) through index 999;
- compressed and uncompressed P2PKH against the exact prize address;
- explicitly excluded: direct-scalar interpretation of the raw bytes
  (that is a different consumer, not frozen here), BIP39, alternate
  coins, SegWit, arbitrary paths, blob-oracle tests;
- exact scope: 8 masters x 2 encodings = 16 master checks; 8 seeds x 6
  paths x 1,000 indices = 48,000 child keys x 2 encodings = 96,000 child
  address checks; **96,016 total address checks**;
- promotion requires an exact prize-address match only.

**Method:** wrote this script, reusing Phase 397's `build_candidates()`
(and its underlying `ROW_MAJOR`/`COLUMN_MAJOR`/`pack_bits()`) to
regenerate the exact eight 59-byte strings byte-for-byte, and Phase 400's
`target_hash160()`, `address_matches()`, `PATH_TEMPLATES`, `INDEX_COUNT`,
`derive_children_and_check()` verbatim -- no primitive re-derived. A
planted BIP32-path positive (a synthetic seed's own child key at a fixed
path/index, checked against its own known address, run through the
identical 6-path/1,000-index loop the real sweep uses) proves the
detection pipeline actually fires before trusting a negative result.

**Result:** see `self_test()`'s asserted counts for the exact pinned
8-candidate manifest and the total address-check tally.

**Disposition:** decided strictly by the contract above -- only an exact
prize-address match promotes. Otherwise this closes negative without
reopening or widening Phase 397's already-closed typed-container family.
"""

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402
from phase394_telegram_recipe_leads_authentication_audit import (  # noqa: E402
    SECP256K1_ORDER,
    child_private_key,
    derive_path,
    hash160,
    public_key,
)
from phase397_p91z_priority1_control_channel_audit import (  # noqa: E402
    DIRECTIONS,
    MAPPINGS,
    PACKINGS,
    build_candidates,
)
from phase400_p91z_priority4_direct_bitcoin_consumer_audit import (  # noqa: E402
    INDEX_COUNT,
    PATH_TEMPLATES,
    address_matches,
    derive_children_and_check,
    target_hash160,
)


def bip32_master_from_seed(seed_bytes, targets):
    master_digest = hmac.new(b"Bitcoin seed", seed_bytes, hashlib.sha512).digest()
    master_key = int.from_bytes(master_digest[:32], "big")
    master_chain = master_digest[32:]
    in_range = 1 <= master_key < SECP256K1_ORDER
    hits = address_matches(master_key, targets) if in_range else []
    return {"in_range": in_range, "hits": hits}, (master_key, master_chain)


def planted_bip32_path_positive():
    """A synthetic seed's own child key at a fixed path/index, checked
    against its own known address, run through the identical derivation
    loop the real sweep uses -- proves the BIP32-path detector fires."""
    seed = hashlib.sha256(b"phase403-planted-seed-positive").digest()
    master_digest = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    master = (int.from_bytes(master_digest[:32], "big"), master_digest[32:])
    target_label, target_prefix = PATH_TEMPLATES[0]
    target_index = 5
    parent_key, parent_chain = derive_path(master, target_prefix)
    child_key, _ = child_private_key(parent_key, parent_chain, target_index)
    own_hash160 = hash160(public_key(child_key, compressed=True))
    hits, checked = derive_children_and_check(
        master, {own_hash160}, path_templates=((target_label, target_prefix),)
    )
    return {"hits": hits, "checked": checked, "expected_path": target_label, "expected_index": target_index}


def audit():
    decoded = btcseed_audit()["decoded"]
    q472 = decoded[98:]
    assert len(q472) == 472
    control = q472[0::2]
    assert len(control) == 236
    assert set(control) == set("BCDE")

    candidates = build_candidates(control)
    assert len(candidates) == 8
    for label, data in candidates.items():
        assert len(data) == 59, (label, len(data))

    targets = {target_hash160()}

    manifest = {}
    master_hits = []
    child_hits = []
    total_child_checked = 0

    for label, seed_bytes in candidates.items():
        manifest[label] = {
            "length": len(seed_bytes),
            "sha256_hex": hashlib.sha256(seed_bytes).hexdigest(),
        }

        master_result, master = bip32_master_from_seed(seed_bytes, targets)
        manifest[label]["bip32_master_in_range"] = master_result["in_range"]
        manifest[label]["bip32_master_hits"] = master_result["hits"]
        master_hits.extend({"root": label, **h} for h in master_result["hits"])

        hits, checked = derive_children_and_check(master, targets)
        total_child_checked += checked
        manifest[label]["child_keys_checked"] = checked
        manifest[label]["child_hits"] = hits
        child_hits.extend({"root": label, **h} for h in hits)

    bip32_master_checks = len(candidates) * 2
    child_address_checks = total_child_checked * 2
    total_address_checks = bip32_master_checks + child_address_checks

    return {
        "candidate_count": len(candidates),
        "manifest": manifest,
        "bip32_master_checks": bip32_master_checks,
        "total_child_keys": total_child_checked,
        "child_address_checks": child_address_checks,
        "total_address_checks": total_address_checks,
        "master_hits": master_hits,
        "child_hits": child_hits,
        "any_hit": bool(master_hits or child_hits),
        "planted_bip32_path_positive": planted_bip32_path_positive(),
    }


def self_test():
    report = audit()

    assert report["candidate_count"] == 8
    assert set(report["manifest"].keys()) == {
        f"{m}_{d}_{p}" for m, _ in MAPPINGS for d in DIRECTIONS for p in PACKINGS
    }
    for label, entry in report["manifest"].items():
        assert entry["length"] == 59, (label, entry["length"])

    assert report["bip32_master_checks"] == 16
    assert report["total_child_keys"] == 48000
    assert report["child_address_checks"] == 96000
    assert report["total_address_checks"] == 96016

    assert report["any_hit"] is False

    planted = report["planted_bip32_path_positive"]
    assert planted["checked"] == 1000
    assert len(planted["hits"]) == 1
    assert planted["hits"][0]["path"] == planted["expected_path"]
    assert planted["hits"][0]["index"] == planted["expected_index"]

    print(
        f"[*] self-test OK: Phase 397's 8 raw 59-byte control-channel "
        f"candidates reproduced byte-for-byte, consumed directly as BIP32 "
        f"seed material (no hashing/reinterpretation); planted BIP32-path "
        f"positive fires exactly at its known index/path; "
        f"{report['total_address_checks']:,} total address checks (16 "
        f"BIP32 masters + 96,000 child addresses across 48,000 derived "
        f"keys, 8 seeds x 6 paths x 1,000 indices) against the exact "
        f"prize address -- "
        f"{len(report['master_hits']) + len(report['child_hits'])} hits"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
