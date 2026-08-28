#!/usr/bin/env python3
"""Phase 442 -- does precedent from the puzzle's own established prime-rule
uses resolve Phase 437's open `SOURCE CODES` representation gate?

Phase 437 registered two genuinely untested representations as candidate
operands for "REINSERTING THE PRIME BASICS": the raw 1,539-byte Phase 3.2.1
block, and its CP1141-transcoded 1,539-letter Beaufort ciphertext. Neither
was promoted, because nothing fixed which representation, unit, base,
direction, or boundary applies.

This module compares every place a "prime" selection rule is actually
*established* in the solved chain:

1. the original first-piece prime walk (`build_walk`/`fitted_prefix` in
   `first_piece_prime_sum_reconstruction.py`): sequential primes 2,3,5,...
   assigned by spiral-ordered event rank, position = prime + cumulative
   prior-yellow offset, 1-based, forward, applied against DBBI;
2. the Stage-0 "prime cells" reading (`stage0_prime_material`): a
   structurally different rule -- keep spiral-position events whose index
   *itself* is prime, 0-based, no offset;
3. the split-final-BE guide retarget (`split_final_be_guide_material`):
   reuses rule (1) verbatim -- identical sequential-prime-plus-prior-yellow
   mechanics -- against a different, already-established 23-endpoint
   color sequence, selecting from the Phase-3.2.2 answer.

Rule (1)'s mechanics are the only ones ever reused unchanged for a second
purpose. Every application of it -- both original and retargeted -- has
selected from a pure single-case *letter* stream (DBBI, then Phase 3.2.2's
answer). Rule (2) was used exactly once, to derive DBBI/FAED themselves, not
as a "reinsert into a new source" step.

This module checks whether the raw 1,539-byte Phase 3.2.1 block is
consistent with that precedent (it should be a letter-only stream if it is
to receive the same rule the same way everything else has), builds the one
narrow, disclosed candidate family this comparison actually licenses (rule
(1)'s established colors/positions, applied to the one representation that
*is* consistent with precedent -- the CP1141 ciphertext -- instead of
Phase 3.2.2's answer), checks it for duplication against Phase 270's already
-tested material list, and runs it through the same structural two-key
padding oracle. No other representation, unit, base, or boundary choice is
tested: this is a precedent-bound family of three candidates, not a sweep.
"""

import argparse
import hashlib
import json
import re

from data import DBBI
from p32_sibling_password_audit import (
    build_candidates,
    decrypt_phase32_bytes,
    derive_sibling_outputs,
    ebcdic_1141_ciphertext,
    extract_phase32_components,
    first_primes,
    password_materials,
    structural_trials,
)
from telegram_yellow_blue_guide_audit import reconstruct_guide

EXPECTED_RAW_BLOCK_LENGTH = 1539
EXPECTED_CIPHER = "vtkvplmepphluwahtz"  # prefix, cross-checked against Phase 270
EXPECTED_CANDIDATE = "tkpmhlwzjputuzfytnlfajfkloewwu"
EXPECTED_COLORS = "BBBBYBBBYYBBBBYBBYYBBYB"


def split_final_be_colors():
    guide = reconstruct_guide()
    chunks = guide["chunks"]
    if chunks[-1][-1] != "be":
        raise AssertionError("guide no longer ends in the split-final BE token")
    split_chunks = chunks[:-1] + (chunks[-1][:-1] + ("b", "e"),)
    endpoint_tokens = tuple(chunk[-1] for chunk in split_chunks)
    return "".join("Y" if token == "be" else "B" for token in endpoint_tokens)


def prime_rule_select(source_text, colors):
    """The established sequential-prime + prior-yellow-offset rule (rule 1),
    validated against DBBI exactly as every prior use of it has been, then
    projected onto ``source_text``."""
    prior_yellows = 0
    selected = []
    for prime, color in zip(first_primes(len(colors)), colors):
        width = 2 if color == "Y" else 1
        position_1 = prime + prior_yellows
        end_1 = position_1 + width - 1
        required = "be" if color == "Y" else "b"
        actual = DBBI[position_1 - 1:end_1]
        if actual != required:
            raise AssertionError(
                f"established rule validation failed at {position_1}-{end_1}: "
                f"expected {required!r}, got {actual!r}"
            )
        selected.append(source_text[position_1 - 1:end_1])
        prior_yellows += color == "Y"
    return "".join(selected)


def representation_letter_check(raw_block, cipher):
    """Does each candidate representation match the precedent -- every rule-1
    application has always selected from a pure single-case letter stream?"""
    raw_text = raw_block.decode("latin1")
    return {
        "raw_block_length": len(raw_block),
        "raw_block_is_pure_letters": bool(re.fullmatch(r"[A-Za-z]+", raw_text)),
        "raw_block_charset_sample": "".join(sorted(set(raw_text))[:12]),
        "cipher_length": len(cipher),
        "cipher_is_pure_letters": bool(re.fullmatch(r"[a-z]+", cipher)),
        "verdict": (
            "raw_block_fails_letter_precedent_cipher_passes"
            if not re.fullmatch(r"[A-Za-z]+", raw_text)
            and re.fullmatch(r"[a-z]+", cipher)
            else "inconclusive"
        ),
    }


def build_new_candidate_family(answer_321, answer_322, cp1141_selection):
    """Exactly three candidates: the new selection alone, plus the same two
    natural sibling-order combinations Phase 270 already used for the
    answer_322-sourced version of this same rule. No other combination is
    declared."""
    return (
        {
            "labels": ("cp1141_prime_rule_selection",),
            "value": cp1141_selection.encode(),
        },
        {
            "labels": ("cp1141_selection_then_322",),
            "value": (cp1141_selection + answer_322).encode(),
        },
        {
            "labels": ("321_then_cp1141_selection",),
            "value": (answer_321 + cp1141_selection).encode(),
        },
    )


def existing_phase270_materials():
    derived = derive_sibling_outputs()
    candidates, _construction = build_candidates(
        derived["answer_321"],
        derived["answer_322"],
        derived["phase32_plaintext"],
        derived["components"]["offsets"]["p32_start"],
    )
    materials = password_materials(candidates)
    return {entry["material"] for entry in materials}


def audit():
    derived = derive_sibling_outputs()
    answer_321 = derived["answer_321"]
    answer_322 = derived["answer_322"]

    plaintext = decrypt_phase32_bytes()
    components = extract_phase32_components(plaintext)
    raw_block = components["encoded_321"]
    cipher = ebcdic_1141_ciphertext(raw_block)

    letter_check = representation_letter_check(raw_block, cipher)

    colors = split_final_be_colors()
    cp1141_selection = prime_rule_select(cipher, colors)

    new_candidates = build_new_candidate_family(answer_321, answer_322, cp1141_selection)
    new_materials = password_materials(new_candidates)

    prior_materials = existing_phase270_materials()
    new_material_values = {entry["material"] for entry in new_materials}
    overlap = prior_materials & new_material_values

    structural = structural_trials(new_materials)

    return {
        "colors": colors,
        "cp1141_prime_rule_selection": cp1141_selection,
        "representation_letter_check": letter_check,
        "new_candidate_count": len(new_candidates),
        "new_material_count": len(new_materials),
        "overlap_with_phase270_materials": len(overlap),
        "structural_oracle": {
            "trial_count": structural["trial_count"],
            "hits": len(structural["hits"]),
        },
    }


def self_test():
    result = audit()
    assert result["colors"] == EXPECTED_COLORS
    assert result["cp1141_prime_rule_selection"] == EXPECTED_CANDIDATE
    letter_check = result["representation_letter_check"]
    assert letter_check["raw_block_length"] == EXPECTED_RAW_BLOCK_LENGTH
    assert letter_check["raw_block_is_pure_letters"] is False
    assert letter_check["cipher_is_pure_letters"] is True
    assert letter_check["verdict"] == "raw_block_fails_letter_precedent_cipher_passes"
    assert result["new_candidate_count"] == 3
    assert result["new_material_count"] == 6
    assert result["overlap_with_phase270_materials"] == 0
    assert result["structural_oracle"]["trial_count"] == 36
    assert result["structural_oracle"]["hits"] == 0
    print(
        "[*] self-test OK: precedent comparison, representation elimination, "
        "3-candidate/6-material disclosed family, 0 overlap, 0 oracle hits"
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
    else:
        print(text)


if __name__ == "__main__":
    main()
