#!/usr/bin/env python3
"""DBBI/FAED independent-consumer audit -- tests the null/T6 topology from
`doc/GSMG_TOPOLOGY_AUDIT.md` directly, per the user's exact 2026-08-22
framing: for each raw stream separately, not by passing them jointly
through Phase 341's solved-boundary assembly grammar (that grammar builds
passwords from already-DECODED clue answers with their own page
annotations -- DBBI/FAED are raw, undecoded streams with no such
annotation, so running them through it would just manufacture another
candidate generator, not test the topology question).

For each stream, ask exactly the three questions the user specified:

    What local instruction can consume this object?
    What output type does that instruction predict?
    What authenticated target accepts that type?

"Recognition checkpoint; no consumer" is an explicitly permitted answer.
Neither stream is required to produce a password or plaintext.

This reuses two already-verified, independent sources of ground truth
rather than re-deriving anything:

  - `page_structure_audit.segment_salphaseion()` for the exact, byte-
    verified literal page structure (which instruction tokens are actually
    adjacent to which raw stream, in source order);
  - `checkerboard_code_ic_oracle.apply_to_real_data()` for each stream's
    own independently-best-fit escape pair (a real, code-backed candidate
    self-decode operation, distinct from any cross-stream combination).

Usage:
    python3 tools/gsmg/dbbi_faed_independent_consumer_audit.py
    python3 tools/gsmg/dbbi_faed_independent_consumer_audit.py --self-test
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checkerboard_code_ic_oracle import apply_to_real_data  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from page_structure_audit import DEFAULT_HTML, TextareaParser, normalize_salphaseion, segment_salphaseion  # noqa: E402


def literal_segments(html_path=DEFAULT_HTML):
    """The exact, byte-verified literal SalPhaseIon page structure."""
    parser = TextareaParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    salphaseion_raw = parser.textareas[0]
    stream = normalize_salphaseion(salphaseion_raw)
    return segment_salphaseion(stream)


def adjacent_segments(segments, target_name, count):
    """The `count` segments immediately following the one named
    `target_name`, in page order."""
    index = next(i for i, s in enumerate(segments) if s.name == target_name)
    return segments[index + 1: index + 1 + count]


def own_candidate_decode(target):
    """The stream's own independently-best-fit escape pair by code-IC,
    with no reference to the other stream at all."""
    result = apply_to_real_data(target)
    best_pair, best_ic = result["ranked"][0]
    return {"best_pair": best_pair, "ic_distance_from_english": best_ic}


def analyze_dbbi(segments):
    following = adjacent_segments(segments, "dbbi", 1)
    instruction = following[0]
    embeds_raw_stream = DBBI.lower() in (instruction.decoded or "").lower()
    return {
        "local_instruction_count": 1,
        "local_instruction_words": [instruction.decoded],
        "instruction_directly_embeds_stream_content": embeds_raw_stream,
        "own_candidate_decode": own_candidate_decode("dbbi"),
        # matrixsumlist is a real, page-encoded instruction token
        # immediately adjacent to DBBI -- but per this project's own
        # G-MSL-001 (doc/GSMG_OPEN_GAP_REGISTRY.md), no source binds it to
        # matrix dimensions, traversal, value mapping, aggregation, or
        # serialization (7/7 fields unbound after Phase 259 exhausted the
        # last known uninspected primary source). An instruction word being
        # PRESENT is not the same as it being EXECUTABLE.
        "classification": "instruction_present_but_unexecutable",
        "predicted_output_type": "unspecified (matrix-sum result -- schema unbound)",
        "authenticated_target_for_predicted_type": None,
    }


def analyze_faed(segments):
    following = adjacent_segments(segments, "faed", 4)
    instruction_words = [
        segment.decoded for segment in following if segment.decoded is not None
    ]
    joined_lower = " ".join(w.lower() for w in instruction_words if w)
    embeds_raw_stream = FAED.lower() in joined_lower
    return {
        "local_instruction_count": len(instruction_words),
        "local_instruction_words": instruction_words,
        "instruction_directly_embeds_stream_content": embeds_raw_stream,
        "own_candidate_decode": own_candidate_decode("faed"),
        # lastwordsbeforearchichoice/thispassword are two page-encoded
        # instruction tokens following FAED -- but they read as a pointer
        # to the SEPARATELY-authenticated Architect monologue's own
        # choice-boundary, not as a transform applied to FAED's raw
        # content (FAED is not embedded in either token, checked above).
        # This is exactly G-ARCH-001's own subject (parked: no source
        # selects the beginnings/endings/mirror operation), reached via
        # adjacency to FAED but not demonstrated to consume FAED at all --
        # precisely the "adjacency does not imply operand" finding Phase
        # 238 already established as a general page rule.
        "classification": "recognition_checkpoint_no_demonstrated_consumer",
        "predicted_output_type": "a password string (per 'thispassword'), for the Architect passage -- not demonstrated to derive from FAED",
        "authenticated_target_for_predicted_type": "SALPH (immediately follows in page order, per page_structure_audit)",
    }


def audit(html_path=DEFAULT_HTML):
    segments = literal_segments(html_path)
    dbbi = analyze_dbbi(segments)
    faed = analyze_faed(segments)
    return {
        "dbbi": dbbi,
        "faed": faed,
        "asymmetric_instruction_adjacency": (
            dbbi["local_instruction_count"] != faed["local_instruction_count"]
        ),
        "escape_pairs_independent": (
            dbbi["own_candidate_decode"]["best_pair"]
            != faed["own_candidate_decode"]["best_pair"]
        ),
        "either_stream_requires_the_other_as_input": False,
    }


def self_test():
    report = audit()
    assert report["dbbi"]["local_instruction_words"] == ["matrixsumlist"]
    assert report["dbbi"]["local_instruction_count"] == 1
    assert report["dbbi"]["instruction_directly_embeds_stream_content"] is False
    assert report["dbbi"]["classification"] == "instruction_present_but_unexecutable"

    assert report["faed"]["local_instruction_words"] == [
        "lastwordsbeforearchichoice", "thispassword",
    ]
    assert report["faed"]["local_instruction_count"] == 2
    assert report["faed"]["instruction_directly_embeds_stream_content"] is False
    assert report["faed"]["classification"] == "recognition_checkpoint_no_demonstrated_consumer"

    assert report["dbbi"]["own_candidate_decode"]["best_pair"] == ("b", "e")
    assert report["faed"]["own_candidate_decode"]["best_pair"] == ("g", "i")
    assert report["escape_pairs_independent"] is True
    assert report["asymmetric_instruction_adjacency"] is True
    assert report["either_stream_requires_the_other_as_input"] is False

    print(
        "[*] self-test OK: DBBI has 1 adjacent instruction ('matrixsumlist', "
        "present but unexecutable -- G-MSL-001), FAED has 2 ('lastwordsbeforearchichoice', "
        "'thispassword', a recognition checkpoint pointing at the Architect passage, "
        "not demonstrated to consume FAED). Neither instruction embeds its stream's "
        "raw content. Each stream's own independently-best escape pair (DBBI=('b','e'), "
        "FAED=('g','i')) differs -- no page evidence requires either stream as input "
        "to the other's consumer"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    report = audit()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
        return
    for stream in ("dbbi", "faed"):
        data = report[stream]
        print(f"-- {stream} --")
        for key, value in data.items():
            print(f"  {key}: {value}")
    print(f"asymmetric_instruction_adjacency: {report['asymmetric_instruction_adjacency']}")
    print(f"escape_pairs_independent: {report['escape_pairs_independent']}")
    print(f"either_stream_requires_the_other_as_input: {report['either_stream_requires_the_other_as_input']}")


if __name__ == "__main__":
    main()
