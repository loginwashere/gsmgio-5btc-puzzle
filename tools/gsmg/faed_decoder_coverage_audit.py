#!/usr/bin/env python3
"""Separate closed FAED decoder families from merely unbounded search space.

This is a coverage/provenance audit, not a new cipher sweep.  It recomputes
the stable FAED facts, carries forward only explicitly identified historical
experiments, and derives whether any *clue-supported* model remains untested.
An imaginable parameter variant is not counted as a coverage gap unless an
authenticated puzzle artifact selects that variant.
"""

import argparse
import hashlib
import json

from checkerboard_code_ic_oracle import apply_to_real_data, segment_codes
from data import FAED


EXPECTED_FAED_SHA256 = (
    "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
)

# Historical results are documentary claims, not silently rerun here.  The
# phase references make that boundary explicit and keep unlike negatives from
# being presented as one exhaustive brute-force result.
FAMILIES = (
    {
        "family": "plain_checkerboard_monoalphabetic",
        "scope": "FAED under {h,e} and corrected best pair {g,i}",
        "status": "closed_calibrated_negative",
        "evidence": "Phases 43 and 113; token-shuffle p=.63366 and p=.0396",
        "creator_selected": False,
    },
    {
        "family": "standard_digraphic_over_25_codes",
        "scope": "Playfair/Two-square/Four-square/Bifid, fixed clue keywords and periods",
        "status": "closed_calibrated_negative",
        "evidence": "Phase 21; 2,268 FAED candidates, familywise p=.94261",
        "creator_selected": False,
    },
    {
        "family": "vic_chain_addition",
        "scope": "FAED {g,i}, both orders, raw9/postdecode, both signs",
        "status": "closed_exhaustive_registered_scope",
        "evidence": "Phase 123; 5,761,385 pairs, about 46,091,080 decodes, zero hits",
        "creator_selected": False,
    },
    {
        "family": "adjacent_difference_self_sync",
        "scope": "four lag-1 linear transforms, both directions and board axes",
        "status": "screen_negative",
        "evidence": "Phase 29; FAED stage-1 familywise p=.87824",
        "creator_selected": False,
    },
    {
        "family": "nonstandard_escape_count",
        "scope": "N=3 and N=4 escape leaders, including restricted topology check",
        "status": "closed_calibrated_negative",
        "evidence": "Phase 145; FAED p=.375/.400 and restricted winners impossible",
        "creator_selected": False,
    },
    {
        "family": "short_period_raw_fractionation",
        "scope": "Bifid-style 3x3 raw-symbol periods 2 through 15",
        "status": "closed_calibrated_negative",
        "evidence": "Phase 146; FAED familywise p=.4680",
        "creator_selected": False,
    },
    {
        "family": "clue_derived_fixed_operands",
        "scope": "selected-31 keyword/keystream, color masks, i-neighbors, [23,16,7] positions",
        "status": "closed_bounded_negative",
        "evidence": "Phases 175, 176, 178, 179, and 185",
        "creator_selected": True,
    },
    {
        "family": "large_dictionary_autokey_continuation",
        "scope": "historical alpha range [54,250,338,905)",
        "status": "partial_compute_unjustified",
        "evidence": "Phases 18, 144, and 146; 4,839,135 registered pairs unrun",
        "creator_selected": False,
    },
)

UNTESTED_VARIANTS = (
    {
        "variant": "circular adjacent differences or lags greater than one",
        "why_not_a_gap": "no clue selects circular closure or a lag",
    },
    {
        "variant": "arbitrary extra alphabets, keywords, periods, and transpositions",
        "why_not_a_gap": "an open parameter universe is not a bounded hypothesis",
    },
    {
        "variant": "an unspecified DBBI/FAED combining operation",
        "why_not_a_gap": "the operand binding and operator are both missing",
    },
)


def audit():
    digest = hashlib.sha256(FAED.encode("ascii")).hexdigest()
    if digest != EXPECTED_FAED_SHA256:
        raise AssertionError("FAED source stream changed")

    ranked = apply_to_real_data("faed")["ranked"]
    best_pair, best_ic = ranked[0]
    codes = segment_codes(FAED, *best_pair)
    if best_pair != ("g", "i") or codes is None:
        raise AssertionError("FAED code-IC checkpoint changed")

    admitted_open = tuple(
        row for row in FAMILIES
        if row["status"].startswith("partial") and row["creator_selected"]
    )
    incomplete_compute = tuple(
        row for row in FAMILIES if row["status"].startswith("partial")
    )
    return {
        "faed_checkpoint": {
            "raw_length": len(FAED),
            "sha256": digest,
            "best_escape_pair": best_pair,
            "best_pair_rank": 1,
            "best_pair_ic": best_ic,
            "segmented_code_count": len(codes),
            "distinct_code_count": len(set(codes)),
        },
        "coverage_families": FAMILIES,
        "known_incomplete_compute": incomplete_compute,
        "admitted_clue_supported_open_models": admitted_open,
        "unbounded_variants_not_counted_as_gaps": UNTESTED_VARIANTS,
        "next_evidence_required": (
            "an authenticated binding that selects a FAED transform, alphabet, "
            "or DBBI/FAED relationship"
        ),
        "verdict": (
            "No clue-supported decoder model remains untested in the registered "
            "coverage. The dictionary-autokey continuation is genuinely "
            "unfinished, but it is thematic search without a recovered local "
            "selector and is therefore not admitted as the next run. The live "
            "gap is decoder binding/provenance, not brute-force completion. "
            "This does not claim that every imaginable cipher is exhausted."
        ),
    }


def self_test():
    report = audit()
    checkpoint = report["faed_checkpoint"]
    assert checkpoint["raw_length"] == 570
    assert checkpoint["best_escape_pair"] == ("g", "i")
    assert checkpoint["segmented_code_count"] == 436
    assert checkpoint["distinct_code_count"] == 25
    assert len(report["known_incomplete_compute"]) == 1
    assert not report["admitted_clue_supported_open_models"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: no clue-supported untested FAED model")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
