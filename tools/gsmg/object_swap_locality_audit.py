#!/usr/bin/env python3
"""HISTORICAL PHASE-47 FOLLOW-UP, superseded by Phase 48.

The locality calculations remain reproducible, but the swap was an artifact
of removing color object 21 instead of inserting FEFE before it. Do not use
this module's transcription-slip verdict as a current conclusion.

Narrow, without resolving, Phase 47's residual object-22/23 discrepancy.

Phase 47 found that removing the FEFE-addressed object and encoding the
remaining first-piece colors as `B -> b`, `Y -> be` matches one of Denis
Golovkin's recovered DBBI masks in 29 of 31 positions, with the only two
mismatches explained by an adjacent swap of reduced color-object positions
21/22 (original objects 22/23). That swap has no creator-authored support.
This module checks four further, narrower facts about that specific gap
rather than searching for a way to explain it away:

1. Is our own encoded color string -- not Denis's posted string -- itself
   findable anywhere in the 91-character source plaintext as an
   order-preserving subsequence? If not, the convergence is specifically
   tied to Denis's exact posted characters, not something recoverable
   directly from the source independent of his (possibly imperfect)
   transcription.
2. Which source positions produced the two mismatched output characters,
   and are those source positions adjacent to each other? If they are, no
   alternate *selection rule* could ever produce them in the other order --
   any order-preserving mask must read the source left to right, so an
   explanation has to be a transcription-level event (or something
   about our own reconstruction at that exact boundary), not a
   different-rule artifact.
3. Do the two mismatched output positions fall within one color-object's
   two-character `be` code, or do they span a boundary between two
   different objects? A within-code artifact and a whole-object swap call
   for different explanations.
4. Do the mismatched positions overlap the `"yang"` substring (the one
   mechanically confirmed fact from Phase 46)? If they don't, whichever
   explanation is right, it doesn't threaten that one confirmed hit.

None of this resolves the discrepancy. It rules out one class of
explanation (an alternate selection rule) and confirms the gap is
localized and orthogonal to the one already-confirmed fact.
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from denis_prime_extraction_audit import SOURCE, TARGET, recover_position_masks  # noqa: E402
from yellow_blue_mask_convergence_audit import audit as convergence_audit  # noqa: E402

EXPECTED_COMPATIBLE_MASK_INDEX = 2
EXPECTED_MISMATCH_OUTPUT_POSITIONS_1_INDEXED = (28, 29)
EXPECTED_SOURCE_POSITIONS_1_INDEXED = (85, 86)
EXPECTED_SOURCE_CHARACTERS = ("s", "t")
EXPECTED_REDUCED_OBJECT_INDICES_0_INDEXED = (20, 21)


def own_string_findable_in_source(encoded_colors):
    masks = recover_position_masks(SOURCE, encoded_colors)
    return masks


def mismatch_source_positions(compatible_mask, mismatch_output_positions_0_indexed):
    return tuple(compatible_mask[position] for position in mismatch_output_positions_0_indexed)


def reduced_object_for_output_position(reduced_colors, output_position_0_indexed):
    """Which 0-indexed object in reduced_colors produced encoded output
    character at output_position_0_indexed, under B->'b', Y->'be'?"""
    cursor = 0
    for object_index, color in enumerate(reduced_colors):
        code_length = 1 if color == "B" else 2
        if cursor <= output_position_0_indexed < cursor + code_length:
            return object_index
        cursor += code_length
    raise AssertionError("output position out of range")


def yang_position_range_1_indexed(target):
    start = target.index("yang")
    return start + 1, start + len("yang")


def run_audit():
    convergence = convergence_audit()
    encoded_colors = convergence["encoded_colors"]
    reduced_colors = convergence["reduced_colors"]
    masks, patterns = convergence["masks"], convergence["patterns"]
    compatible_index = convergence["compatible_index"]
    compatible_mask = masks[compatible_index]

    own_matches = own_string_findable_in_source(encoded_colors)

    mismatch_output_1_indexed = [
        position + 1
        for position, (a, b) in enumerate(zip(encoded_colors, patterns[compatible_index]))
        if a != b
    ]
    mismatch_output_0_indexed = [position - 1 for position in mismatch_output_1_indexed]

    source_positions_0_indexed = mismatch_source_positions(compatible_mask, mismatch_output_0_indexed)
    source_positions_1_indexed = tuple(position + 1 for position in source_positions_0_indexed)
    source_characters = tuple(SOURCE[position] for position in source_positions_0_indexed)
    adjacent_in_source = source_positions_0_indexed[1] - source_positions_0_indexed[0] == 1

    reduced_object_indices = tuple(
        reduced_object_for_output_position(reduced_colors, position)
        for position in mismatch_output_0_indexed
    )
    spans_two_objects = len(set(reduced_object_indices)) == 2

    yang_start, yang_end = yang_position_range_1_indexed(TARGET)
    overlaps_yang = any(
        yang_start <= position <= yang_end for position in mismatch_output_1_indexed
    )

    return {
        "own_string_matches_in_source": len(own_matches),
        "compatible_index": compatible_index,
        "mismatch_output_1_indexed": mismatch_output_1_indexed,
        "source_positions_1_indexed": source_positions_1_indexed,
        "source_characters": source_characters,
        "adjacent_in_source": adjacent_in_source,
        "reduced_object_indices_0_indexed": reduced_object_indices,
        "spans_two_objects": spans_two_objects,
        "yang_position_range_1_indexed": (yang_start, yang_end),
        "overlaps_yang": overlaps_yang,
    }


def self_test():
    report = run_audit()
    assert report["own_string_matches_in_source"] == 0, (
        f"expected our own encoded color string to be unfindable in SOURCE, "
        f"got {report['own_string_matches_in_source']} matches"
    )
    assert report["compatible_index"] == EXPECTED_COMPATIBLE_MASK_INDEX
    assert tuple(report["mismatch_output_1_indexed"]) == EXPECTED_MISMATCH_OUTPUT_POSITIONS_1_INDEXED
    assert report["source_positions_1_indexed"] == EXPECTED_SOURCE_POSITIONS_1_INDEXED
    assert report["source_characters"] == EXPECTED_SOURCE_CHARACTERS
    assert report["adjacent_in_source"] is True
    assert report["reduced_object_indices_0_indexed"] == EXPECTED_REDUCED_OBJECT_INDICES_0_INDEXED
    assert report["spans_two_objects"] is True
    assert report["overlaps_yang"] is False
    print(
        "[*] self-test OK: own string unfindable in source (0 matches); "
        "mismatch traces to adjacent source positions 85/86 ('s','t'); "
        "spans two distinct color-objects, not a code-boundary artifact; "
        "does not overlap the confirmed 'yang' substring"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    print(
        "[!] HISTORICAL PHASE-47 FOLLOW-UP: the locality calculations are "
        "valid, but the swap premise is superseded"
    )
    self_test()
    if args.self_test:
        return

    report = run_audit()
    print(f"[*] our own encoded color string found in SOURCE: {report['own_string_matches_in_source']} times "
          "(0 means the convergence is tied to Denis's exact posted string, not independently findable)")
    print(f"[*] mismatch at output positions (1-indexed): {report['mismatch_output_1_indexed']}")
    print(f"[*] those come from SOURCE positions (1-indexed): {report['source_positions_1_indexed']} "
          f"= characters {report['source_characters']}")
    print(f"[*] adjacent in source: {report['adjacent_in_source']} "
          "(any order-preserving mask is forced to read them in this order)")
    print(f"[*] spans two distinct color-objects (0-indexed): {report['reduced_object_indices_0_indexed']} "
          f"-> {report['spans_two_objects']} (not a single code's internal artifact)")
    print(f"[*] 'yang' occupies output positions {report['yang_position_range_1_indexed']}; "
          f"overlaps mismatch: {report['overlaps_yang']}")
    print(
        "\n[*] verdict: the discrepancy cannot come from an alternate selection "
        "rule (source order is fixed); it is localized to one adjacent "
        "object-pair swap and does not threaten the confirmed 'yang' hit. "
        "This narrows but does not resolve the gap -- it remains unsupported "
        "without Denis's missing guide image or another external source."
    )


if __name__ == "__main__":
    main()
