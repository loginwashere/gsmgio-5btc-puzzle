#!/usr/bin/env python3
"""One non-wrapping cumulative `[23,16,7]` stride walk over `dbbi`/`faed`.

Phase 150 already tested literal single-position selection at 23/16/7
(zero/one-based, forward/reverse) against `dbbi`, and `matrixsumlist`
self/fold consumer pairings against `dbbi`/`faed` -- all oracle-negative.
What Phase 150 did not test is cumulative stepping: repeatedly advancing by
the cycle 23, 16, 7, 23, 16, ... and reading the character at each running
total, rather than reading the three literal positions once.

This is deliberately the single narrowest defensible definition of that
walk, not a family:

1. Preserves the authenticated order 23, 16, 7 (no reordering).
2. Reuses the authenticated forward one-based convention from Phase 33's
   `BUT` derivation (no zero-based or backward variant).
3. Advances first, so the first position read is 23, not 0 or 1.
4. Stops the first time the next running total would exceed the stream
   length -- non-wrapping, no rotation of the starting stride, no
   fixed-length cutoff.
5. Runs against complete `dbbi` and complete `faed` separately -- no
   reversal, no wrap-around, no FAED-to-91 fold.

Unlike `BUT`, this walk has no independent output checkpoint of its own; it
is reported as an exploratory negative/hit, not a calibrated consumer. The
authenticated `[23,16,7]` operand does not by itself authenticate a
"stride" operation -- see FINDINGS.md for the full discussion.
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from remaining_structural_avenues_audit import material_family  # noqa: E402

CYCLE = (23, 16, 7)
EXPECTED_LENGTHS = {"DBBI": 91, "FAED": 570}
EXPECTED_POSITIONS = {
    "DBBI": (23, 39, 46, 69, 85),
    "FAED": (
        23, 39, 46, 69, 85, 92, 115, 131, 138, 161, 177, 184, 207, 223, 230,
        253, 269, 276, 299, 315, 322, 345, 361, 368, 391, 407, 414, 437, 453,
        460, 483, 499, 506, 529, 545, 552,
    ),
}
EXPECTED_STRINGS = {
    "DBBI": "hebgb",
    "FAED": "cdefggefaggccifidaicgeghgediheidfhbi",
}


def cumulative_positions(length):
    cycle = itertools.cycle(CYCLE)
    total = 0
    positions = []
    for step in cycle:
        nxt = total + step
        if nxt > length:
            break
        positions.append(nxt)
        total = nxt
    return tuple(positions)


def walk(stream):
    positions = cumulative_positions(len(stream))
    return positions, "".join(stream[p - 1] for p in positions)


def audit():
    streams = {"DBBI": DBBI, "FAED": FAED}
    results = {}
    for label, length in EXPECTED_LENGTHS.items():
        if len(streams[label]) != length:
            raise AssertionError(f"unexpected {label} length: {len(streams[label])}")
        positions, string = walk(streams[label])
        if positions != EXPECTED_POSITIONS[label]:
            raise AssertionError(f"{label} position walk changed: {positions}")
        if string != EXPECTED_STRINGS[label]:
            raise AssertionError(f"{label} walk string changed: {string}")
        results[label] = {"positions": positions, "string": string}
    candidates = tuple(results[label]["string"] for label in ("DBBI", "FAED"))
    return {
        "scope": (
            "one non-wrapping forward one-based cumulative [23,16,7] stride "
            "walk per stream; no wrap/rotate/reverse/fold variants run"
        ),
        "cycle": CYCLE,
        "results": results,
        "oracle": material_family(candidates, BLOBS),
    }


def self_test():
    for label, length in EXPECTED_LENGTHS.items():
        stream = {"DBBI": DBBI, "FAED": FAED}[label]
        assert len(stream) == length
    positions, string = walk(DBBI)
    assert positions == EXPECTED_POSITIONS["DBBI"]
    assert string == EXPECTED_STRINGS["DBBI"]
    positions, string = walk(FAED)
    assert positions == EXPECTED_POSITIONS["FAED"]
    assert string == EXPECTED_STRINGS["FAED"]
    print(
        "[*] self-test OK: pinned non-wrapping cumulative [23,16,7] walks "
        "for DBBI (5 positions) and FAED (36 positions)"
    )


def print_report(report):
    for label, result in report["results"].items():
        print(f"[*] {label}: {len(result['positions'])} positions -> {result['string']!r}")
    oracle = report["oracle"]
    print(
        f"[*] {oracle['candidate_count']} candidates / "
        f"{oracle['unique_material_count']} materials / {len(oracle['hits'])} hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
