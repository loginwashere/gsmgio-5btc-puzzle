#!/usr/bin/env python3
"""Phase 443 -- close Phase 442's omitted pure-letter representation.

Phase 442 correctly eliminated the raw Phase-3.2.1 byte block under the
precedent "the reused prime rule has only consumed pure single-case letter
streams", but then treated the CP1141 ciphertext as the only surviving
representation. The decoded Phase-3.2.1 Architect answer is also a pure
single-case 1,539-letter stream. Phase 270 tested many readings of that
answer, but not this exact split-final-BE sequential-prime-plus-prior-yellow
selection.

This follow-up changes exactly one operand in Phase 442. It applies the same
colors, positions, direction, widths, validation against DBBI, three-candidate
grammar, raw/SHA256-hex material treatments, and structural two-key padding
oracle to answer_321. No alternate rule or extra combination is added.
"""

import argparse
import hashlib
import json
import re

from p32_sibling_password_audit import (
    decrypt_phase32_bytes,
    derive_sibling_outputs,
    ebcdic_1141_ciphertext,
    extract_phase32_components,
    password_materials,
    structural_trials,
)
from phase442_prime_basics_representation_precedent_audit import (
    build_new_candidate_family as build_phase442_candidate_family,
    existing_phase270_materials,
    prime_rule_select,
    split_final_be_colors,
)

EXPECTED_ANSWER_LENGTH = 1539
EXPECTED_ANSWER_SHA256 = (
    "56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241"
)
EXPECTED_COLORS = "BBBBYBBBYYBBBBYBBYYBBYB"
EXPECTED_SELECTION = "OULFTHSFRINANNCQANINEROINTILEA"


def build_answer321_candidate_family(answer_321, answer_322, selection):
    """Phase 442's exact three-candidate grammar with one changed operand."""
    candidates = build_phase442_candidate_family(answer_321, answer_322, selection)
    labels = (
        "answer321_prime_rule_selection",
        "answer321_selection_then_322",
        "321_then_answer321_selection",
    )
    return tuple(
        {"labels": (label,), "value": candidate["value"]}
        for label, candidate in zip(labels, candidates)
    )


def phase442_material_values(answer_321, answer_322):
    plaintext = decrypt_phase32_bytes()
    raw_block = extract_phase32_components(plaintext)["encoded_321"]
    cipher = ebcdic_1141_ciphertext(raw_block)
    selection = prime_rule_select(cipher, split_final_be_colors())
    candidates = build_phase442_candidate_family(answer_321, answer_322, selection)
    return {entry["material"] for entry in password_materials(candidates)}


def audit():
    derived = derive_sibling_outputs()
    answer_321 = derived["answer_321"]
    answer_322 = derived["answer_322"]

    colors = split_final_be_colors()
    selection = prime_rule_select(answer_321, colors)
    candidates = build_answer321_candidate_family(answer_321, answer_322, selection)
    materials = password_materials(candidates)
    material_values = {entry["material"] for entry in materials}

    phase270_overlap = material_values & existing_phase270_materials()
    phase442_overlap = material_values & phase442_material_values(answer_321, answer_322)
    structural = structural_trials(materials)

    return {
        "correction": (
            "Phase 442's pure-single-case-letter precedent leaves two eligible "
            "Phase-3.2.1 representations, not one: CP1141 ciphertext and "
            "decoded answer_321."
        ),
        "source": {
            "id": "decoded_answer_321",
            "length": len(answer_321),
            "sha256": hashlib.sha256(answer_321.encode()).hexdigest(),
            "is_pure_uppercase_letters": bool(re.fullmatch(r"[A-Z]+", answer_321)),
        },
        "colors": colors,
        "answer321_prime_rule_selection": selection,
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
        "overlap_with_phase270_materials": len(phase270_overlap),
        "overlap_with_phase442_materials": len(phase442_overlap),
        "structural_oracle": {
            "trial_count": structural["trial_count"],
            "hits": len(structural["hits"]),
        },
        "disposition": "two_representation_precedent_family_exhausted_negative",
    }


def self_test():
    result = audit()
    source = result["source"]
    assert source["length"] == EXPECTED_ANSWER_LENGTH
    assert source["sha256"] == EXPECTED_ANSWER_SHA256
    assert source["is_pure_uppercase_letters"] is True
    assert result["colors"] == EXPECTED_COLORS
    assert result["answer321_prime_rule_selection"] == EXPECTED_SELECTION
    assert result["candidate_count"] == 3
    assert result["material_count"] == 6
    assert result["overlap_with_phase270_materials"] == 0
    assert result["overlap_with_phase442_materials"] == 0
    assert result["structural_oracle"]["trial_count"] == 36
    assert result["structural_oracle"]["hits"] == 0
    print(
        "[*] self-test OK: answer_321 pure-letter omission corrected; "
        "3 candidates / 6 materials; 0 prior overlap; 36 trials; 0 hits"
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
