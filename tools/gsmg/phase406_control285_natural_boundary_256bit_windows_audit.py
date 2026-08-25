#!/usr/bin/env python3
"""Phase 406: tests four 128-symbol (256-bit) windows of the full
285-symbol control rail, each anchored to an existing structural
boundary rather than an arbitrarily chosen offset.

**Origin:** a residual after Phase 405 closed the Base64-sextet reading
of the full and P91-scoped control rails negative. `CONTROL285 =
decoded[0::2]` (285 symbols, `{B,C,D,E}`) is longer than the 236-symbol
`Q472` control rail Phase 397 already byte-packed (`236*2=472` bits
exactly), but 285 symbols do not themselves divide evenly into
256-bit/32-byte units (`285*2=570` bits, not a multiple of 256). Rather
than pick an arbitrary 128-symbol sub-window, this phase restricts to
the four offsets independently produced by boundaries this project has
already established: the stream start, the first control symbol after
the 7-character `BTCSEED` header, the first control symbol after the
stream's unique `Z` (at `decoded[97]`, the last character of `P91`), and
the end-aligned window. Offset 21 and other unspecified "grid edges" are
explicitly excluded -- neither is independently selected by any
already-frozen boundary.

**Frozen contract (proposed and approved before this script was
written):**

- `CONTROL285 = decoded[0::2]`; asserted length 285 and alphabet exactly
  `{B,C,D,E}`; the unique `Z` asserted to remain at `decoded[97]`
  (unaffected by the control-rail slice, since 97 is odd);
- four 128-symbol windows of `CONTROL285`, each independently anchored:
  offset 0 (stream-start aligned), offset 4 (first control index after
  the 7-character header -- header occupies `decoded[0:7]`, first even
  index after that is 8, `8/2=4`), offset 49 (first control index after
  `decoded[97]` -- first even index after 97 is 98, `98/2=49`, which is
  also `Q472`'s own start), offset 157 (end-aligned, `285-128=157`);
- two symbol->2-bit mappings, Phase 397's exact grid-native pair:
  row-major (`D,B,C,E -> 0,1,2,3`) and column-major (`D,C,B,E ->
  0,1,2,3`);
- two intra-byte packings, Phase 397's exact `pack_bits()`: MSB-first
  and LSB-first;
- native forward window order only, no reversal;
- 4 windows x 2 mappings x 2 packings = **16 labeled candidates, closed
  and enumerated before any output is inspected**; each is exactly 32
  bytes (`128*2=256` bits); interpreted as a big-endian unsigned integer
  where a numeric interpretation is needed;
- direct-scalar consumer: reject (not reduce) outside `1 <= k < n`;
  compressed and uncompressed P2PKH; 16 candidates x 2 encodings = 32
  address checks;
- BIP32 consumer: the raw 32 bytes used directly as
  `HMAC-SHA512("Bitcoin seed", seed)` -- no hashing or reinterpretation
  first; master compressed/uncompressed P2PKH; Phase 400's identical six
  frozen derivation path templates through index 999; 16 candidates x 2
  encodings = 32 master checks, plus 16 candidates x 6 paths x 1,000
  indices x 2 encodings = 192,000 child address checks;
- **192,064 total address checks** if every candidate produces an
  in-range master (32 direct-scalar + 32 BIP32-master + 192,000 child);
- explicitly excluded: hashing, little-endian interpretation, byte
  reversal, additional offsets beyond the four listed, BIP39,
  passphrases, additional derivation paths;
- exact-byte uniqueness reported across the 16 candidates, but all 16
  labels retained and checked regardless of duplication;
- promotion requires an exact prize-address match only.

**Method:** wrote this script, reusing Phase 397's `ROW_MAJOR`/
`COLUMN_MAJOR`/`pack_bits()` and Phase 400's `target_hash160()`,
`address_matches()`, `direct_scalar_check()`, `bip32_master_check()`,
`derive_children_and_check()`, `PATH_TEMPLATES`, `INDEX_COUNT`,
`planted_direct_key_positive()`, and `planted_bip32_path_positive()`
verbatim -- no crypto primitive re-derived. A planted control-symbol to
32-byte round trip (a SHA-256 digest of a fixed label, inverse-mapped
through row-major/MSB-first into a synthetic 128-symbol sequence, then
re-run through the real forward `pack_bits()`) proves the packing
pipeline round-trips correctly. Phase 400's own planted direct-key and
BIP32-path positives are reused unmodified to prove the two consumer
pipelines fire before trusting a negative result.

**Result:** see `self_test()`'s asserted counts for the exact pinned
16-candidate manifest and the total address-check tally.

**Disposition:** decided strictly by the contract above -- only an exact
prize-address match promotes. Otherwise this closes negative without
widening to unanchored offsets, additional windows, hashed/reinterpreted
seed material, or additional derivation paths. If this closes negative,
the next candidate per the user's own stated plan is P91 repeated over
Q472 (Bifid-period sensitivity), treated as a robustness audit of
`BTCSEED` rather than another key search.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402
from phase397_p91z_priority1_control_channel_audit import (  # noqa: E402
    COLUMN_MAJOR,
    PACKINGS,
    ROW_MAJOR,
    pack_bits,
)
from phase400_p91z_priority4_direct_bitcoin_consumer_audit import (  # noqa: E402
    address_matches,
    bip32_master_check,
    derive_children_and_check,
    direct_scalar_check,
    planted_bip32_path_positive,
    planted_direct_key_positive,
    target_hash160,
)

MAPPINGS = (("row_major", ROW_MAJOR), ("column_major", COLUMN_MAJOR))
WINDOW_LENGTH = 128
OFFSETS = (0, 4, 49, 157)


def build_windows(control285):
    assert len(control285) == 285
    windows = {}
    for offset in OFFSETS:
        window = control285[offset : offset + WINDOW_LENGTH]
        assert len(window) == WINDOW_LENGTH, (offset, len(window))
        windows[offset] = window
    return windows


def build_candidates(windows):
    candidates = {}
    for offset, window in windows.items():
        for mapping_name, mapping in MAPPINGS:
            for packing in PACKINGS:
                label = f"offset{offset}_{mapping_name}_{packing}"
                candidates[label] = pack_bits(window, mapping, packing)
    return candidates


def planted_roundtrip_positive():
    """A SHA-256 digest inverse-mapped through row-major/MSB-first into a
    synthetic 128-symbol control sequence, then re-run through the real
    forward `pack_bits()` -- proves the window-packing pipeline
    round-trips correctly, not just that it runs."""
    target_bytes = hashlib.sha256(b"phase406-planted-roundtrip").digest()
    assert len(target_bytes) == 32
    inverse_row_major = {v: k for k, v in ROW_MAJOR.items()}
    symbols = []
    for byte in target_bytes:
        v0 = (byte >> 6) & 0b11
        v1 = (byte >> 4) & 0b11
        v2 = (byte >> 2) & 0b11
        v3 = byte & 0b11
        symbols.extend(inverse_row_major[v] for v in (v0, v1, v2, v3))
    assert len(symbols) == WINDOW_LENGTH
    recovered = pack_bits(symbols, ROW_MAJOR, "msb_first")
    return {
        "target_hex": target_bytes.hex(),
        "recovered_hex": recovered.hex(),
        "matches": recovered == target_bytes,
    }


def audit():
    decoded = btcseed_audit()["decoded"]
    control285 = decoded[0::2]
    assert len(control285) == 285
    assert set(control285) == set("BCDE")
    assert decoded[97] == "Z"
    assert decoded.count("Z") == 1

    windows = build_windows(control285)
    assert set(windows.keys()) == set(OFFSETS)

    candidates = build_candidates(windows)
    assert len(candidates) == 16
    for label, data in candidates.items():
        assert len(data) == 32, (label, len(data))

    unique_bytes = {}
    for label, data in candidates.items():
        unique_bytes.setdefault(data, []).append(label)

    targets = {target_hash160()}

    manifest = {}
    direct_hits = []
    master_hits = []
    child_hits = []
    total_child_checked = 0

    for label, data in candidates.items():
        manifest[label] = {"hex": data.hex()}

        direct = direct_scalar_check(data, targets)
        manifest[label]["direct_scalar_in_range"] = direct["in_range"]
        manifest[label]["direct_scalar_hits"] = direct["hits"]
        direct_hits.extend({"candidate": label, **h} for h in direct["hits"])

        master_result, master = bip32_master_check(data, targets)
        manifest[label]["bip32_master_in_range"] = master_result["in_range"]
        manifest[label]["bip32_master_hits"] = master_result["hits"]
        master_hits.extend({"candidate": label, **h} for h in master_result["hits"])

        hits, checked = derive_children_and_check(master, targets)
        total_child_checked += checked
        manifest[label]["child_keys_checked"] = checked
        manifest[label]["child_hits"] = hits
        child_hits.extend({"candidate": label, **h} for h in hits)

    direct_scalar_checks = len(candidates) * 2
    bip32_master_checks = len(candidates) * 2
    child_address_checks = total_child_checked * 2
    total_address_checks = direct_scalar_checks + bip32_master_checks + child_address_checks

    return {
        "control285_length": len(control285),
        "window_offsets": list(OFFSETS),
        "candidate_count": len(candidates),
        "unique_candidate_count": len(unique_bytes),
        "manifest": manifest,
        "direct_scalar_checks": direct_scalar_checks,
        "bip32_master_checks": bip32_master_checks,
        "total_child_keys": total_child_checked,
        "child_address_checks": child_address_checks,
        "total_address_checks": total_address_checks,
        "direct_hits": direct_hits,
        "master_hits": master_hits,
        "child_hits": child_hits,
        "any_hit": bool(direct_hits or master_hits or child_hits),
        "planted_roundtrip_positive": planted_roundtrip_positive(),
        "planted_direct_key_positive": planted_direct_key_positive(),
        "planted_bip32_path_positive": planted_bip32_path_positive(),
    }


def self_test():
    report = audit()

    assert report["control285_length"] == 285
    assert report["window_offsets"] == [0, 4, 49, 157]
    assert report["candidate_count"] == 16
    assert set(report["manifest"].keys()) == {
        f"offset{o}_{m}_{p}" for o in OFFSETS for m, _ in MAPPINGS for p in PACKINGS
    }
    for label, entry in report["manifest"].items():
        assert len(bytes.fromhex(entry["hex"])) == 32, (label, entry["hex"])

    assert report["direct_scalar_checks"] == 32
    assert report["bip32_master_checks"] == 32
    assert report["total_child_keys"] == 96000
    assert report["child_address_checks"] == 192000
    assert report["total_address_checks"] == 192064

    assert report["any_hit"] is False

    roundtrip = report["planted_roundtrip_positive"]
    assert roundtrip["matches"] is True

    planted_direct = report["planted_direct_key_positive"]
    assert planted_direct["in_range"] is True
    assert len(planted_direct["hits"]) == 1
    assert planted_direct["hits"][0]["compressed"] is True

    planted_path = report["planted_bip32_path_positive"]
    assert planted_path["checked"] == 1000
    assert len(planted_path["hits"]) == 1
    assert planted_path["hits"][0]["path"] == planted_path["expected_path"]
    assert planted_path["hits"][0]["index"] == planted_path["expected_index"]

    print(
        f"[*] self-test OK: planted round-trip and both Phase-400 planted "
        f"positives (direct-scalar, BIP32-path) fire correctly; 16 "
        f"candidates (4 structurally-anchored 128-symbol windows x 2 "
        f"grid-native mappings x 2 bit-packings) reproduced as 32-byte "
        f"strings, {report['unique_candidate_count']}/16 unique; "
        f"{report['total_address_checks']:,} total address checks (32 "
        f"direct scalars + 32 BIP32 masters + 192,000 child addresses "
        f"across 96,000 derived keys, 16 seeds x 6 paths x 1,000 indices) "
        f"against the exact prize address -- "
        f"{len(report['direct_hits']) + len(report['master_hits']) + len(report['child_hits'])} hits"
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
