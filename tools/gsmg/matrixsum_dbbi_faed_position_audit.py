#!/usr/bin/env python3
"""`[23,16,7]` as a character-position selector directly into `dbbi`/`faed`.

`[23,16,7]` has been applied to the Telegram matrix partition (Phase 32-34),
the Architect-scene word list (Phase 33/58), and the elemental
`SALPHATION -> SALVATION` delta (Phase 97), but never as a position selector
into the two still-undecoded `dbbi`/`faed` a-i streams themselves. This
reuses Phase 33's own preregistered four-convention family (forward/
backward, one/zero-based) rather than inventing a new one -- the same
indices, the same convention set, a different already-authenticated source.

No direct solved-stage calibration exists for this selector (Phase 3.2's
plaintext has no `dbbi`/`faed`-equivalent substream to rehearse against);
`[23,16,7]` is instead calibrated by its three independent prior
derivations, same standard Phase 33 itself applied to `BUT`.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from remaining_structural_avenues_audit import material_family  # noqa: E402

INDICES = (23, 16, 7)
EXPECTED_LENGTHS = {"DBBI": 91, "FAED": 570}

EXPECTED_CANDIDATES = {
    ("DBBI", "forward_one_based"): "hhb",
    ("DBBI", "forward_zero_based"): "bah",
    ("DBBI", "backward_one_based"): "gib",
    ("DBBI", "backward_zero_based"): "gcg",
    ("FAED", "forward_one_based"): "che",
    ("FAED", "forward_zero_based"): "fhe",
    ("FAED", "backward_one_based"): "bca",
    ("FAED", "backward_zero_based"): "idf",
}


def select(stream, forward, one_based):
    n = len(stream)
    chars = []
    for index in INDICES:
        if forward and one_based:
            position = index - 1
        elif forward and not one_based:
            position = index
        elif not forward and one_based:
            position = n - index
        else:
            position = n - 1 - index
        chars.append(stream[position])
    return "".join(chars)


def candidates():
    streams = {"DBBI": DBBI, "FAED": FAED}
    for label, length in EXPECTED_LENGTHS.items():
        if len(streams[label]) != length:
            raise AssertionError(f"unexpected {label} length: {len(streams[label])}")
    out = {}
    for label, stream in streams.items():
        for forward in (True, False):
            for one_based in (True, False):
                convention = (
                    ("forward" if forward else "backward")
                    + "_"
                    + ("one" if one_based else "zero")
                    + "_based"
                )
                out[(label, convention)] = select(stream, forward, one_based)
    return out


def audit():
    computed = candidates()
    mismatches = {
        key: (value, EXPECTED_CANDIDATES[key])
        for key, value in computed.items()
        if EXPECTED_CANDIDATES[key] != value
    }
    if mismatches:
        raise AssertionError(f"candidate mismatch vs pinned values: {mismatches}")
    unique_strings = sorted(set(computed.values()))
    return {
        "scope": (
            "[23,16,7] as a position selector into dbbi/faed under Phase "
            "33's own four preregistered indexing conventions; no new "
            "convention added"
        ),
        "indices": INDICES,
        "candidates": {f"{label}/{conv}": val for (label, conv), val in sorted(computed.items())},
        "oracle": material_family(unique_strings, BLOBS),
    }


def self_test():
    assert len(EXPECTED_CANDIDATES) == 8
    assert len(set(EXPECTED_CANDIDATES.values())) == 8
    computed = candidates()
    assert computed == EXPECTED_CANDIDATES
    print(
        "[*] self-test OK: 8 pinned [23,16,7] dbbi/faed position candidates "
        "under Phase 33's own four conventions"
    )


def print_report(report):
    oracle = report["oracle"]
    print(f"[*] indices: {report['indices']}")
    for key, value in report["candidates"].items():
        print(f"    {key}: {value}")
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
