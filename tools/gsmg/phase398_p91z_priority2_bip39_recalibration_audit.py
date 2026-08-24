#!/usr/bin/env python3
"""Phase 398: executes Priority 2 of the 2026-08-25 BTCSEED/P91/Z
continuation brainstorm -- recalibrating Phase 394's BIP39 checksum sweep
under the two grid-native symbol-to-2-bit mappings only, instead of all 24
permutations.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`, Priority 2. Phase 394 tried all 24 permutations of
`{b,c,d,e} -> {0,1,2,3}` (24 mappings x 154 windows = 3,696 trials, 13
checksum-valid, versus a uniform expectation of `3696/256 ~= 14.44`). The
brainstorm observes that only 2 of those 24 mappings are "square-native":
reading the keyed square's upper-left `2x2`

```text
D B
C E
```

as a 2-bit value with no axis swap (`value = row*2 + col`, row the more
significant bit) gives row-major `D,B,C,E -> 0,1,2,3`; swapping which axis
is more significant gives column-major `D,C,B,E -> 0,1,2,3`, which is
algebraically identical to Phase 394's posted mapping (`b,c,d,e -> 2,1,0,3`,
equivalently `d,c,b,e -> 0,1,2,3`). This is an evidential recalibration, not
a new wallet sweep: it re-scores the *same* checksum-valid results Phase 394
already found under a narrower, structurally motivated family, and asks
whether Bifid's own coordinate convention favors one of the two over the
other. Address/path authentication is explicitly out of scope here -- Phase
394 already tested the one previously-posted mnemonic against 12,000
derivation checks and found nothing, and that result is not re-litigated.

**Method:** wrote this script, reusing `phase394_telegram_recipe_leads_
authentication_audit.py`'s own `load_bip39_words()`, `bits_to_mnemonic()`,
and `bip39_checksum_valid()` verbatim, and its own rail extraction (the
unique `decoded[0::2]`/`decoded[1::2]` rail whose alphabet is exactly
`{b,c,d,e}`, 285 symbols). Two mappings x 154 windows (`285-132+1`) = 308
trials, enumerated before any output was inspected. Two closed, secondary
questions:

1. **Which mapping is Bifid-native?** Each of `D,B,C,E`'s two coordinates
   in the 5x5 keyed square (`pos[ch] = (row, col)`, exactly the order this
   project's own `bifid_decrypt()` already reads and stores them
   everywhere) are combined with no axis swap. That is precisely the
   row-major reading, not column-major -- column-major requires actively
   swapping which axis is read first, which nothing in Bifid's own
   mechanism does. This is reported as a structural observation, not a
   proof that the puzzle intends row-major; it just establishes which
   reading requires zero extra assumption and which requires one.
2. **Does anything independently select offset 30** (the posted window)?
   A small, pre-declared set of boundary-derived rail offsets is checked
   for an exact match to 30 -- not searched or tuned after seeing 30:
   `0` (rail start), `153` (rail end, `285-132`), `49` (rail index of the
   first symbol of `Q472`, global index 98), `4` (rail index of `P91`'s
   first even-global-index symbol, global index 8), and `77`/`142` (half
   of the window count and half of the rail length, the two "midpoint"
   candidates a boundary-based selection might plausibly produce).

**Result:** 308 trials, expected-under-uniform count `308/256 ~= 1.203`.
Both grid-native mappings' checksum-valid results are recorded in full
(mapping, offset, mnemonic, entropy). Offset 30 does not match any of the 6
pre-declared candidate boundaries. Row-major is the axis-swap-free reading;
column-major (the posted mapping) requires one explicit swap.

**Disposition:** per the brainstorm's own stated expectation -- "if the
mnemonic is one of roughly one or two expected checksum-valid results and
offset 30 remains unselected, close it" -- see `self_test()`'s asserted
counts for whether that holds. This does not repeat or contradict Phase
394's address-authentication result, which stands unchanged.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase394_telegram_recipe_leads_authentication_audit import (  # noqa: E402
    TARGET_MAPPING,
    audit as btcseed_root_audit,
    bip39_checksum_valid,
    bits_to_mnemonic,
    load_bip39_words,
)
from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402

# D B          (row, col) for each square-native symbol, no axis swap:
# C E          D=(0,0) B=(0,1) C=(1,0) E=(1,1)
GRID_COORDS = {"d": (0, 0), "b": (0, 1), "c": (1, 0), "e": (1, 1)}

# value = row*2 + col: the reading Bifid's own (row, col) convention gives
# with no axis swap.
ROW_MAJOR = tuple(
    (GRID_COORDS[sym][0] * 2 + GRID_COORDS[sym][1]) for sym in "bcde"
)
# value = col*2 + row: the axis-swapped reading. Verified below to equal
# Phase 394's posted TARGET_MAPPING.
COLUMN_MAJOR = tuple(
    (GRID_COORDS[sym][1] * 2 + GRID_COORDS[sym][0]) for sym in "bcde"
)
assert COLUMN_MAJOR == TARGET_MAPPING

MAPPINGS = (("row_major", ROW_MAJOR), ("column_major", COLUMN_MAJOR))

WINDOW_LENGTH = 132

# Pre-declared, closed candidate set for "does anything independently
# select offset 30" -- fixed before checking, not tuned afterward.
CANDIDATE_NATURAL_OFFSETS = {
    "rail_start": 0,
    "rail_end": 285 - WINDOW_LENGTH,
    "q472_start_rail_index": 98 // 2,
    "p91_first_even_global_rail_index": 8 // 2,
    "half_window_count": (285 - WINDOW_LENGTH + 1) // 2,
    "half_rail_length": 285 // 2,
}


def extract_rail():
    decoded = btcseed_audit()["decoded"].lower()
    rails = (decoded[0::2], decoded[1::2])
    four_symbol = tuple(rail for rail in rails if set(rail) == set("bcde"))
    assert len(four_symbol) == 1
    rail = four_symbol[0]
    assert len(rail) == 285
    return rail


def sweep(rail, words):
    valid = []
    window_count = len(rail) - WINDOW_LENGTH + 1
    for mapping_name, permutation in MAPPINGS:
        mapping = {symbol: f"{value:02b}" for symbol, value in zip("bcde", permutation)}
        bitstream = "".join(mapping[symbol] for symbol in rail)
        for offset in range(window_count):
            bits = bitstream[2 * offset : 2 * (offset + WINDOW_LENGTH)]
            if not bip39_checksum_valid(bits):
                continue
            mnemonic = bits_to_mnemonic(bits, words)
            valid.append(
                {
                    "mapping": mapping_name,
                    "mapping_bcde": permutation,
                    "offset": offset,
                    "mnemonic": " ".join(mnemonic),
                    "entropy_hex": int(bits[:256], 2).to_bytes(32, "big").hex(),
                }
            )
    return valid, window_count


def audit():
    rail = extract_rail()
    words = load_bip39_words()
    valid, window_count = sweep(rail, words)
    total_trials = window_count * len(MAPPINGS)

    offset30_hits = [entry for entry in valid if entry["offset"] == 30]
    natural_offset_match = next(
        (name for name, value in CANDIDATE_NATURAL_OFFSETS.items() if value == 30),
        None,
    )

    return {
        "rail_length": len(rail),
        "window_length": WINDOW_LENGTH,
        "window_count_per_mapping": window_count,
        "mapping_count": len(MAPPINGS),
        "total_trials": total_trials,
        "expected_valid_under_uniform": total_trials / 256,
        "row_major_bcde": ROW_MAJOR,
        "column_major_bcde": COLUMN_MAJOR,
        "column_major_matches_posted_mapping": COLUMN_MAJOR == TARGET_MAPPING,
        "bifid_native_reading": "row_major",
        "valid_count": len(valid),
        "valid_mnemonics": valid,
        "offset30_hits": offset30_hits,
        "candidate_natural_offsets": CANDIDATE_NATURAL_OFFSETS,
        "natural_offset_selects_30": natural_offset_match,
    }


def self_test():
    report = audit()

    assert report["rail_length"] == 285
    assert report["window_count_per_mapping"] == 154
    assert report["mapping_count"] == 2
    assert report["total_trials"] == 308
    assert abs(report["expected_valid_under_uniform"] - 308 / 256) < 1e-12
    assert report["column_major_matches_posted_mapping"] is True
    assert report["row_major_bcde"] == (1, 2, 0, 3)
    assert report["column_major_bcde"] == (2, 1, 0, 3)

    # Per the brainstorm's own stated expectation.
    assert 0 <= report["valid_count"] <= 4, report["valid_count"]

    assert report["natural_offset_selects_30"] is None

    hits_30 = report["offset30_hits"]
    hit_mappings = {entry["mapping"] for entry in hits_30}
    assert hit_mappings <= {"column_major"}

    print(
        f"[*] self-test OK: Priority 2's reduced 2-mapping x 154-window "
        f"family (308 trials, expected {308/256:.3f}) reproduces "
        f"{report['valid_count']} checksum-valid mnemonic(s); row-major is "
        f"the axis-swap-free reading of the keyed square's own (row, col) "
        f"convention, column-major (the posted mapping) requires one "
        f"explicit swap; offset 30 matches none of "
        f"{len(CANDIDATE_NATURAL_OFFSETS)} pre-declared natural-boundary "
        f"candidates -- remains unselected; address/path authentication is "
        f"out of scope here and unchanged from Phase 394"
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
