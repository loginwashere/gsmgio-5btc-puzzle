#!/usr/bin/env python3
"""Audit the bounded Stage-0 convergence OCBe -> 864, G counts 4/2, FEFE -> 0.

This does not infer 2 and 0 merely from the arithmetic progression.  It joins
three already measured streams, requiring the atomic sequence's final 4 to
equal the first row-local G reference count.  Only the resulting forward
string is sent to the standard blob oracle; no reversal or permutation family
is introduced.

The final digit is also checked against the rest of the established grid
palette: `base_bit()` only isolates black/blue ink from everything else, so
FEFE's `0` is shared with white and yellow and is not, by itself, a
FEFE-specific measurement -- see `palette_base_bits` below.
"""

import argparse

from cb_common import BLOBS, QUARANTINED_BLOBS
from first_piece_color_reconstruction import (
    COLOR_NAMES,
    DEFAULT_IMAGE,
    base_bit,
    reconstruct,
)
from remaining_structural_avenues_audit import material_family
from stage0_g_shadow_consumer_audit import audit as shadow_audit


def audit():
    shadow = shadow_audit()
    atomic = shadow["atomic_numbers"]
    g_references = tuple(row["reference_count"] for row in shadow["rows"])
    fefe = reconstruct(DEFAULT_IMAGE)["fefe"]

    overlap = atomic[-1] == g_references[0]
    joined = atomic + g_references[1:] + (fefe["value"],) if overlap else ()
    steps = tuple(right - left for left, right in zip(joined, joined[1:]))
    candidate = "".join(str(value) for value in joined)

    # base_bit() is a two-way ink/non-ink split, not a per-color fingerprint --
    # record how many of the five established grid colors share FEFE's final
    # digit, so that digit isn't read as FEFE-specific evidence when it is
    # really just "not black, not blue".
    palette_base_bits = {name: base_bit(color) for color, name in COLOR_NAMES.items()}
    fefe_value_shared_with = tuple(
        sorted(name for name, bit in palette_base_bits.items() if bit == fefe["value"])
    )

    return {
        "atomic_numbers": atomic,
        "g_reference_counts": g_references,
        "overlap": overlap,
        "fefe_value": fefe["value"],
        "joined": joined,
        "steps": steps,
        "candidate": candidate,
        "palette_base_bits": palette_base_bits,
        "fefe_value_shared_with": fefe_value_shared_with,
        "oracle": material_family((candidate,), BLOBS),
        "quarantined_oracle": material_family((candidate,), QUARANTINED_BLOBS),
    }


def self_test():
    report = audit()
    assert report["atomic_numbers"] == (8, 6, 4)
    assert report["g_reference_counts"] == (4, 2)
    assert report["overlap"] is True
    assert report["fefe_value"] == 0
    assert report["joined"] == (8, 6, 4, 2, 0)
    assert report["steps"] == (-2, -2, -2, -2)
    assert report["candidate"] == "86420"
    assert report["palette_base_bits"] == {
        "black": 1,
        "white": 0,
        "blue": 1,
        "yellow": 0,
        "fefefe": 0,
    }
    assert report["fefe_value_shared_with"] == ("fefefe", "white", "yellow")
    assert report["oracle"]["candidate_count"] == 1
    assert report["oracle"]["hits"] == []
    assert report["quarantined_oracle"]["candidate_count"] == 1
    assert report["quarantined_oracle"]["hits"] == []
    print("[*] self-test OK: 864 + overlapping G refs 4/2 + FEFE 0 -> 86420")
    print(
        "[*] scope note: FEFE's final-digit value 0 is shared by "
        f"{report['fefe_value_shared_with']} -- base_bit() only isolates "
        "black/blue ink, so 0 is not FEFE-specific"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    print(
        f"[*] atomic={report['atomic_numbers']}; G refs={report['g_reference_counts']}; "
        f"FEFE={report['fefe_value']}"
    )
    print(
        f"[*] overlap={report['overlap']}; joined={report['joined']}; "
        f"steps={report['steps']}; candidate={report['candidate']}"
    )
    print(
        f"[*] palette base bits: {report['palette_base_bits']}; "
        f"FEFE's 0 shared with {report['fefe_value_shared_with']}"
    )
    oracle = report["oracle"]
    print(
        f"[*] oracle: {oracle['candidate_count']} candidate / "
        f"{oracle['unique_material_count']} materials / {len(oracle['hits'])} hits"
    )
    quarantined = report["quarantined_oracle"]
    print(
        f"[*] quarantined URLBLOB oracle: {quarantined['candidate_count']} candidate / "
        f"{quarantined['unique_material_count']} materials / "
        f"{len(quarantined['hits'])} hits"
    )


if __name__ == "__main__":
    main()
