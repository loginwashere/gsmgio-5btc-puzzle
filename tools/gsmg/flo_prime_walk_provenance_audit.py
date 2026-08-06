#!/usr/bin/env python3
"""Reproduce and bound Flo Sku's community-derived DBBI prime/color walk.

Primary transcript evidence:

* Denis Golovkin described "yellow-blue-primes" and posted a 31-character
  extraction on 2026-03-03.
* Flo Sku described replacing successive B/BE objects with successive primes
  on 2026-04-13.
* Flo posted a literal DBBI string with 31 capitalized positions on 2026-04-16.
* Mahfooz and Artem objected to mismatches; Flo later said to "ignore the e",
  while Denis described a perfect match only for the first 20 bits.

This audit verifies the literal transcript artifacts and proves that Flo's 31
capitalized positions are exactly the sole B/BE-compatible source-position
mask recovered from Denis's extraction. It also compares two models:

* omitting FEFE makes color object 21 appear to fail at prime 73;
* inserting the independently verified FEFE pixel into its actual spiral
  position makes it event 21, represented by one ``b``. Events 1-23 then
  reproduce Flo's complete 31-position mask exactly, before DBBI is exhausted.

The equality reconstructs Denis's missing mask through Flo's posted artifact
and resolves Phase 47's apparent object-22/23 swap as a modeling error: FEFE
must be inserted before color object 21, not substituted for or removed with
that object. It is not three independent confirmations: the recovered mask is
derived from Denis's output, and the recurrence formalizes Flo's description.
The exact multiset-shuffle rate is therefore descriptive calibration only, not
a discovery p-value and not grounds for AES/cipher escalation.
"""

import argparse
import itertools
from collections import Counter
from fractions import Fraction
from pathlib import Path

from data import DBBI
from denis_prime_extraction_audit import SOURCE, TARGET, recover_position_masks
from door_prime_passport_probe import nth_prime
from first_piece_color_reconstruction import DEFAULT_IMAGE, EXPECTED_COLOR_SEQUENCE, reconstruct
from yellow_blue_mask_convergence_audit import decode_be_pattern

PROJECTS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CHAT = PROJECTS_ROOT / "gsmgio-5btc-puzzle" / "_work" / "chat_transcript.txt"

FLO_HIGHLIGHTED_DBBI = (
    "dBBiBfBhccBEgBihaBeBeihBEggegeBEbBgehheBhhfBaBfdhBE"
    "ffcdbBfcccgBfBEeggecBEdciBfBffgigBEeeaBE"
)
EXPECTED_FLO_POSITIONS_1_INDEXED = (
    2, 3, 5, 7, 11, 12, 14, 18, 20, 24, 25, 31, 32, 34, 40, 44,
    46, 50, 51, 57, 63, 65, 66, 72, 73, 77, 79, 85, 86, 90, 91,
)
EXPECTED_FLO_PATTERN = "bbbbbebbbbebebbbbbebbbebebbbebe"
EXPECTED_FLO_COLORS = "BBBBYBBBYYBBBBYBBYYBBYY"
EXPECTED_SPATIAL_EVENTS = "BBBBYBBBYYBBBBYBBYYBFYYBY"


def transcript_evidence(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    messages = {
        "denis_prime_claim": "someone applied specific prime inexes to specific last words",
        "denis_guide": "Here was a guide to yellow-blue-primes.",
        "flo_method": (
            "Also, in the dbbi string, you can replace the B and BE, in order "
            "and by counting them, with prime numbers"
        ),
        "flo_highlight": f"here is dbbi with highlighted primes : {FLO_HIGHLIGHTED_DBBI}",
        "mahfooz_objection": (
            "Something happened to the 7th and 8th BE , somehow without "
            "hallucinating it got changed to B"
        ),
        "flo_patch": "These two Be are just B's since they are blue in the matrix, just ignore the e",
        "artem_check": "I just wrote it out manually, 7 missed",
        "denis_boundary": "Then you'll get perfect match of first 20 bits.",
    }
    positions = {}
    for label, message in messages.items():
        position = text.find(message)
        if position < 0:
            raise AssertionError(f"missing transcript evidence {label}: {message!r}")
        positions[label] = position

    expected_order = (
        "denis_prime_claim",
        "denis_guide",
        "flo_method",
        "flo_highlight",
        "mahfooz_objection",
        "flo_patch",
        "artem_check",
        "denis_boundary",
    )
    if [positions[label] for label in expected_order] != sorted(
        positions[label] for label in expected_order
    ):
        raise AssertionError("transcript evidence is absent or out of chronological order")

    return {
        "positions": positions,
        "denis_predates_flo": positions["denis_guide"] < positions["flo_method"],
        "contains_community_objections": (
            positions["mahfooz_objection"] < positions["flo_patch"]
            < positions["artem_check"]
        ),
    }


def highlighted_positions_1_indexed(highlighted):
    return tuple(index + 1 for index, character in enumerate(highlighted) if character.isupper())


def walk_consistency(colors, dbbi):
    records = []
    prior_yellows = 0
    for ordinal, color in enumerate(colors, start=1):
        prime = nth_prime(ordinal)
        raw_position = prime + prior_yellows
        if color not in "BYF":
            raise ValueError(f"unsupported event type: {color!r}")
        required = "be" if color == "Y" else "b"
        start = raw_position - 1
        actual = dbbi[start:start + len(required)]
        records.append(
            {
                "ordinal": ordinal,
                "prime": prime,
                "prior_yellows": prior_yellows,
                "raw_position": raw_position,
                "color": color,
                "required": required,
                "actual": actual,
                "consistent": actual == required,
            }
        )
        if color == "Y":
            prior_yellows += 1
    return records


def spatial_event_sequence(image_path=DEFAULT_IMAGE):
    reconstruction = reconstruct(image_path)
    events = [
        (item["spiral_0"], "B" if item["color"] == "blue" else "Y")
        for item in reconstruction["objects"]
    ]
    events.append((reconstruction["fefe"]["spiral_0"], "F"))
    events.sort()
    return "".join(event for _, event in events)


def constraints_for_records(records):
    constraints = {}
    for record in records:
        for offset, character in enumerate(record["required"]):
            position = record["raw_position"] + offset
            previous = constraints.get(position)
            if previous is not None and previous != character:
                raise ValueError(
                    f"conflicting requirements at position {position}: "
                    f"{previous!r} vs {character!r}"
                )
            constraints[position] = character
    return constraints


def falling_factorial(value, count):
    result = 1
    for offset in range(count):
        result *= value - offset
    return result


def exact_profile_preserving_rate(sequence, constraints):
    if any(position < 1 or position > len(sequence) for position in constraints):
        raise ValueError("constraint position falls outside the sequence")

    required_counts = Counter(constraints.values())
    available_counts = Counter(sequence)
    if any(required_counts[character] > available_counts[character] for character in required_counts):
        return Fraction(0, 1)

    numerator = 1
    for character, count in required_counts.items():
        numerator *= falling_factorial(available_counts[character], count)
    denominator = falling_factorial(len(sequence), len(constraints))
    return Fraction(numerator, denominator)


def exhaustive_profile_preserving_rate(sequence, constraints):
    permutations = set(itertools.permutations(sequence))
    successes = sum(
        all(permutation[position - 1] == character for position, character in constraints.items())
        for permutation in permutations
    )
    return Fraction(successes, len(permutations))


def audit(chat_path=DEFAULT_CHAT, image_path=DEFAULT_IMAGE):
    transcript = transcript_evidence(chat_path)
    flo_positions = highlighted_positions_1_indexed(FLO_HIGHLIGHTED_DBBI)
    flo_pattern = "".join(DBBI[position - 1] for position in flo_positions)
    flo_selected_plaintext = "".join(SOURCE[position - 1] for position in flo_positions)

    masks = recover_position_masks(SOURCE, TARGET)
    matching_mask_indices = tuple(
        index
        for index, mask in enumerate(masks)
        if tuple(position + 1 for position in mask) == flo_positions
    )

    omitted_fefe_walk = walk_consistency(EXPECTED_COLOR_SEQUENCE, DBBI)
    omitted_fefe_failure_index = next(
        index for index, record in enumerate(omitted_fefe_walk)
        if not record["consistent"]
    )
    omitted_fefe_failure = omitted_fefe_walk[omitted_fefe_failure_index]

    spatial_events = spatial_event_sequence(image_path)
    spatial_walk = walk_consistency(spatial_events, DBBI)
    fitted_spatial_walk = [
        record for record in spatial_walk
        if record["raw_position"] + len(record["required"]) - 1 <= len(DBBI)
    ]
    first_exhausted_event = spatial_walk[len(fitted_spatial_walk)]
    constraints = constraints_for_records(fitted_spatial_walk)
    constraint_counts = Counter(constraints.values())
    exact_rate = exact_profile_preserving_rate(DBBI, constraints)

    return {
        "transcript": transcript,
        "flo_positions": flo_positions,
        "flo_pattern": flo_pattern,
        "flo_colors": decode_be_pattern(flo_pattern),
        "flo_selected_plaintext": flo_selected_plaintext,
        "matching_mask_indices": matching_mask_indices,
        "omitted_fefe_walk": omitted_fefe_walk,
        "omitted_fefe_failure": omitted_fefe_failure,
        "spatial_events": spatial_events,
        "spatial_walk": spatial_walk,
        "fitted_spatial_walk": fitted_spatial_walk,
        "first_exhausted_event": first_exhausted_event,
        "constraints": constraints,
        "constraint_counts": constraint_counts,
        "exact_rate": exact_rate,
        "constraint_positions": tuple(sorted(constraints)),
    }


def self_test(chat_path=DEFAULT_CHAT):
    synthetic_cases = (
        ("bbex", {1: "b", 2: "e"}),
        ("aabc", {1: "a"}),
        ("aabb", {1: "a", 4: "b"}),
    )
    for sequence, constraints in synthetic_cases:
        exact = exact_profile_preserving_rate(sequence, constraints)
        exhaustive = exhaustive_profile_preserving_rate(sequence, constraints)
        assert exact == exhaustive, (
            f"exact/exhaustive mismatch for {sequence!r}, {constraints}: "
            f"{exact} != {exhaustive}"
        )

    report = audit(chat_path)
    assert report["transcript"]["denis_predates_flo"] is True
    assert report["transcript"]["contains_community_objections"] is True
    assert FLO_HIGHLIGHTED_DBBI.lower() == DBBI
    assert report["flo_positions"] == EXPECTED_FLO_POSITIONS_1_INDEXED
    assert report["flo_pattern"] == EXPECTED_FLO_PATTERN
    assert report["flo_colors"] == EXPECTED_FLO_COLORS
    assert report["flo_selected_plaintext"] == TARGET
    assert report["matching_mask_indices"] == (2,)
    assert report["omitted_fefe_failure"] == {
        "ordinal": 21,
        "prime": 73,
        "prior_yellows": 6,
        "raw_position": 79,
        "color": "Y",
        "required": "be",
        "actual": "bf",
        "consistent": False,
    }
    assert report["spatial_events"] == EXPECTED_SPATIAL_EVENTS
    assert len(report["fitted_spatial_walk"]) == 23
    assert all(record["consistent"] for record in report["fitted_spatial_walk"])
    assert report["fitted_spatial_walk"][20] == {
        "ordinal": 21,
        "prime": 73,
        "prior_yellows": 6,
        "raw_position": 79,
        "color": "F",
        "required": "b",
        "actual": "b",
        "consistent": True,
    }
    assert report["first_exhausted_event"]["ordinal"] == 24
    assert report["first_exhausted_event"]["raw_position"] == 97
    assert len(report["constraints"]) == 31
    assert report["constraint_counts"] == Counter({"b": 23, "e": 8})
    assert report["constraint_positions"] == report["flo_positions"]
    assert report["exact_rate"] == Fraction(1, 1_187_431_764_520_631_732_537_526)
    print(
        "[*] self-test OK: transcript provenance, Flo/Denis mask identity, "
        "spatial FEFE insertion, exact 23-event walk, and exact base rate verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat", type=Path, default=DEFAULT_CHAT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.chat)
    if args.self_test:
        return

    report = audit(args.chat)
    print("[*] Flo prime/color/FEFE walk:")
    print("    evt prime priorY raw type need got ok")
    for record in report["fitted_spatial_walk"]:
        print(
            f"    {record['ordinal']:>3} {record['prime']:>5} "
            f"{record['prior_yellows']:>6} {record['raw_position']:>3} "
            f"{record['color']:>5} {record['required']:>4} "
            f"{record['actual']:>3} {str(record['consistent']):>5}"
        )

    rate = report["exact_rate"]
    print(f"\n[*] Flo capitalized positions: {report['flo_positions']}")
    print(f"[*] selected plaintext: {report['flo_selected_plaintext']}")
    print(f"[*] equals recovered Denis mask index: {report['matching_mask_indices']}")
    print(
        f"[*] exact fitted walk: {len(report['fitted_spatial_walk'])} events, "
        f"{len(report['constraints'])} raw-character constraints "
        f"({dict(report['constraint_counts'])})"
    )
    print(
        f"[*] first event beyond DBBI: {report['first_exhausted_event']['ordinal']} "
        f"at raw position {report['first_exhausted_event']['raw_position']}"
    )
    print(
        f"[*] exact DBBI-multiset shuffle rate: {rate.numerator}/{rate.denominator} "
        f"= {float(rate):.12g}"
    )
    print(
        "[*] verdict: Flo's literal artifact reconstructs Denis's missing mask, "
        "and inserting FEFE at its real spiral position resolves the apparent "
        "object-21 failure and Phase 47 swap. DBBI ends after 23 of 25 events. "
        "Descriptive community provenance only; no cipher escalation."
    )


if __name__ == "__main__":
    main()
