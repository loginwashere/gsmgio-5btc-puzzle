#!/usr/bin/env python3
"""Phase 444 -- sealed source-bound Architect AND/OR rail audit."""

import argparse
import hashlib
import json

from data import DBBI
from p32_sibling_password_audit import (
    decrypt_phase32_bytes,
    derive_sibling_outputs,
    ebcdic_1141_ciphertext,
    extract_phase32_components,
    first_primes,
    password_materials,
    structural_trials,
)
from phase442_prime_basics_representation_precedent_audit import (
    build_new_candidate_family as build_phase442_candidate_family,
    existing_phase270_materials,
    prime_rule_select,
    split_final_be_colors,
)
from phase443_answer321_prime_basics_followup import (
    build_answer321_candidate_family,
    phase442_material_values,
)

EXPECTED_COLORS = "BBBBYBBBYYBBBBYBBYYBBYB"
EXPECTED_SOURCES = {
    "cp1141": {
        "length": 1539,
        "sha256": "6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e",
        "blue_only": "tkpmwzjzfytfaoeu",
        "yellow_only": "hlputunljfklww",
        "blue_then_yellow": "tkpmwzjzfytfaoeuhlputunljfklww",
        "intertwined": "tkpmhlwzjputuzfytnlfajfkloewwu",
    },
    "answer_321": {
        "length": 1539,
        "sha256": "56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241",
        "blue_only": "OULFSFRNCQANETIA",
        "yellow_only": "THINANNIROINLE",
        "blue_then_yellow": "OULFSFRNCQANETIATHINANNIROINLE",
        "intertwined": "OULFTHSFRINANNCQANINEROINTILEA",
    },
}


def derive_sources():
    derived = derive_sibling_outputs()
    raw_block = extract_phase32_components(decrypt_phase32_bytes())["encoded_321"]
    return derived, {
        "cp1141": ebcdic_1141_ciphertext(raw_block),
        "answer_321": derived["answer_321"],
    }


def split_rails(source_text, colors):
    """Apply the frozen rule once, then serialize its color partition."""
    prior_yellows = 0
    blue_parts = []
    yellow_parts = []
    intertwined_parts = []
    records = []

    for ordinal, (prime, color) in enumerate(
        zip(first_primes(len(colors)), colors), start=1
    ):
        width = 2 if color == "Y" else 1
        position_1 = prime + prior_yellows
        end_1 = position_1 + width - 1
        required = "be" if color == "Y" else "b"
        actual = DBBI[position_1 - 1:end_1]
        if actual != required:
            raise AssertionError(
                f"event {ordinal} expected {required!r} at "
                f"{position_1}-{end_1}, got {actual!r}"
            )
        part = source_text[position_1 - 1:end_1]
        intertwined_parts.append(part)
        (yellow_parts if color == "Y" else blue_parts).append(part)
        records.append(
            {
                "ordinal": ordinal,
                "prime": prime,
                "color": color,
                "position_1": position_1,
                "end_1": end_1,
                "selected": part,
            }
        )
        prior_yellows += color == "Y"

    if len(blue_parts) != 16 or len(yellow_parts) != 7:
        raise AssertionError("split-final-BE event partition changed")

    rails = {
        "blue_only": "".join(blue_parts),
        "yellow_only": "".join(yellow_parts),
        "blue_then_yellow": "".join(blue_parts + yellow_parts),
        "intertwined": "".join(intertwined_parts),
    }
    if rails["intertwined"] != prime_rule_select(source_text, colors):
        raise AssertionError("intertwined regression disagrees with Phase 442 rule")
    return rails, records


def build_candidates(answer_321, answer_322, source_rails):
    """18 candidates fixed by the protocol: 2 x 3 rails x 3 outer forms."""
    candidates = []
    for source_id in ("cp1141", "answer_321"):
        for rail_id in ("blue_only", "yellow_only", "blue_then_yellow"):
            rail = source_rails[source_id][rail_id]
            outer = build_phase442_candidate_family(answer_321, answer_322, rail)
            suffixes = ("alone", "then_322", "after_321")
            for suffix, candidate in zip(suffixes, outer):
                candidates.append(
                    {
                        "labels": (f"{source_id}_{rail_id}_{suffix}",),
                        "value": candidate["value"],
                    }
                )
    return tuple(candidates)


def phase443_material_values(answer_321, answer_322):
    colors = split_final_be_colors()
    selection = prime_rule_select(answer_321, colors)
    candidates = build_answer321_candidate_family(answer_321, answer_322, selection)
    return {entry["material"] for entry in password_materials(candidates)}


def audit():
    derived, sources = derive_sources()
    colors = split_final_be_colors()
    source_rails = {}
    source_reports = {}

    for source_id, source_text in sources.items():
        rails, records = split_rails(source_text, colors)
        source_rails[source_id] = rails
        source_reports[source_id] = {
            "length": len(source_text),
            "sha256": hashlib.sha256(source_text.encode()).hexdigest(),
            "blue_event_count": sum(record["color"] == "B" for record in records),
            "yellow_event_count": sum(record["color"] == "Y" for record in records),
            "rails": rails,
            "intertwined_regression_only": True,
        }

    candidates = build_candidates(
        derived["answer_321"], derived["answer_322"], source_rails
    )
    materials = password_materials(candidates)

    prior_sets = {
        "phase270": existing_phase270_materials(),
        "phase442": phase442_material_values(
            derived["answer_321"], derived["answer_322"]
        ),
        "phase443": phase443_material_values(
            derived["answer_321"], derived["answer_322"]
        ),
    }
    prior_union = set().union(*prior_sets.values())
    overlaps = {
        phase: sum(entry["material"] in values for entry in materials)
        for phase, values in prior_sets.items()
    }
    new_materials = tuple(
        entry for entry in materials if entry["material"] not in prior_union
    )
    structural = structural_trials(new_materials)

    return {
        "protocol": {
            "sources": 2,
            "new_rail_serializations_per_source": 3,
            "outer_forms_per_rail": 3,
            "treatments_per_candidate": 2,
            "kdf_specs_per_material": 6,
            "excluded_regression": "intertwined",
        },
        "colors": colors,
        "sources": source_reports,
        "candidate_count": len(candidates),
        "material_count": len(materials),
        "candidate_summaries": [
            {
                "label": candidate["labels"][0],
                "length": len(candidate["value"]),
                "sha256": hashlib.sha256(candidate["value"]).hexdigest(),
            }
            for candidate in candidates
        ],
        "prior_overlap_material_counts": overlaps,
        "new_material_count": len(new_materials),
        "structural_oracle": {
            "trial_count": structural["trial_count"],
            "hits": len(structural["hits"]),
        },
        "disposition": "bounded_two_source_and_or_rail_family_negative",
    }


def self_test():
    result = audit()
    assert result["colors"] == EXPECTED_COLORS
    for source_id, expected in EXPECTED_SOURCES.items():
        actual = result["sources"][source_id]
        assert actual["length"] == expected["length"]
        assert actual["sha256"] == expected["sha256"]
        assert actual["blue_event_count"] == 16
        assert actual["yellow_event_count"] == 7
        assert actual["rails"] == {
            key: expected[key]
            for key in (
                "blue_only",
                "yellow_only",
                "blue_then_yellow",
                "intertwined",
            )
        }
        assert actual["intertwined_regression_only"] is True
    assert result["candidate_count"] == 18
    assert result["material_count"] == 36
    assert result["prior_overlap_material_counts"] == {
        "phase270": 0,
        "phase442": 0,
        "phase443": 0,
    }
    assert result["new_material_count"] == 36
    assert result["structural_oracle"] == {"trial_count": 216, "hits": 0}
    print(
        "[*] self-test OK: 2 sources x 3 rails x 3 forms; "
        "36 new materials; 216 trials; 0 hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", type=argparse.FileType("w"))
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    result = audit()
    text = json.dumps(result, indent=2)
    if args.json:
        args.json.write(text)
        args.json.write("\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
