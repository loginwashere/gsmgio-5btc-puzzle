#!/usr/bin/env python3
"""Compare the two live macro grammars and classify their outputs.

This is a structural/disposition audit.  It does not decrypt a payload or run
an AES oracle.  It combines four bounded questions:

* Does the six-digit-prime grammar consume more of the authenticated macro
  than the 31-character-operand grammar without adding more free fields?
* Does the selected word BOTH add internal support for inspecting B/H edges?
* Does the solved puzzle establish non-credential outputs, or specifically a
  terminal puzzle-derived recognition word comparable to BYE?
* How do each stream's best checkerboard pair and its mirror9 image segment
  both DBBI and FAED?
"""

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

import architect_choice_boundary_audit as boundary
import creator_operator_vocabulary_audit as operator_inventory
import minimal_macro_chain_audit
from architect_hye_bye_audit import partial_mirror9, rails
from creator_yingyang_faed_pair_audit import pair_key, rank_map
from prime_matrixsum_reconstruction import mirror9
from telegram_export_manifest import DEFAULT_EXPORT_DIR


SELECTED_31 = "ncsyangcahiriasogaleafayanestve"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TIER1_CANDIDATES = PROJECT_ROOT / "wordlists/gsmg/medium_curated_tier1_primary.txt"

# Frozen Phase-132 load-bearing result.  Recomputing the million-trial Monte
# Carlo is unnecessary here; the real-string statistic and wordlist are
# independently rechecked below.
SELECTED_31_CONTROL = {
    "real_hits": ("gale", "leaf", "nest", "yang"),
    "historical_wordlist": "wordlists/xkcd/words.txt (Phase 132; not retained in this checkout)",
    "trials": 1_000_000,
    "exceedances": 5_469,
    "empirical_p": 0.005469995,
    "promotion_threshold": 0.005,
    "promoted": False,
}

MODEL_A_MISSING_FIELDS = (
    "matrix dimensions",
    "input placement",
    "traversal orientation",
    "symbol-to-number mapping",
    "aggregation",
    "list serialization",
    "next artifact or target",
)

# These roles summarize the verified solved operators already frozen by
# creator_operator_vocabulary_audit.py.  Creator-chat reactions are excluded.
PUZZLE_DERIVED_OUTPUT_ROLES = (
    {
        "stage": "pre-rabbit first puzzle",
        "output": "decoded command stream",
        "role": "instruction",
        "credential": False,
    },
    {
        "stage": "pre-rabbit first puzzle",
        "output": "terminal Rick Astley URL",
        "role": "route",
        "credential": False,
    },
    {
        "stage": "rabbit Stage 0",
        "output": "gsmg.io/theseedisplanted",
        "role": "route",
        "credential": False,
    },
    {
        "stage": "Stage 1 form",
        "output": "lyric-derived string",
        "role": "credential",
        "credential": True,
    },
    {
        "stage": "Phase 3",
        "output": "ordered seven-part value",
        "role": "credential",
        "credential": True,
    },
    {
        "stage": "Phase 3.2.1",
        "output": "Architect-derived plaintext",
        "role": "prose payload / next clue",
        "credential": False,
    },
    {
        "stage": "Phase 3.2.2",
        "output": "validated checkerboard plaintext",
        "role": "prose payload",
        "credential": False,
    },
    {
        "stage": "extra-door entry",
        "output": "hash of concatenated visible text",
        "role": "route",
        "credential": False,
    },
)


def pair_label(pair):
    return "".join(sorted(pair))


def mirror_pair(pair):
    return pair_key(*(mirror9(character) for character in pair))


def pair_result(ranks, pair):
    result = ranks.get(pair_key(*pair))
    return None if result is None else dict(result)


def mirror_orbit_audit():
    ranks = {target: rank_map(target) for target in ("dbbi", "faed")}
    cases = []
    for origin, pair in (("dbbi", "be"), ("faed", "gi")):
        mirrored = mirror_pair(pair)
        cases.append(
            {
                "origin": origin,
                "best_pair": pair_label(pair),
                "best_pair_results": {
                    target: pair_result(ranks[target], pair)
                    for target in ("dbbi", "faed")
                },
                "mirror_pair": pair_label(mirrored),
                "mirror_pair_results": {
                    target: pair_result(ranks[target], mirrored)
                    for target in ("dbbi", "faed")
                },
            }
        )

    signature_counts = Counter()
    for pair in itertools.combinations("abcdefghi", 2):
        mirrored = mirror_pair(pair)
        signature = (
            pair_key(*pair) in ranks["dbbi"],
            pair_key(*pair) in ranks["faed"],
            mirrored in ranks["dbbi"],
            mirrored in ranks["faed"],
        )
        signature_counts[signature] += 1

    be_signature = (True, True, False, True)
    gi_signature = (True, True, True, False)
    return {
        "cases": tuple(cases),
        "signature_definition": (
            "pair valid on DBBI, pair valid on FAED, mirror valid on DBBI, "
            "mirror valid on FAED"
        ),
        "be_signature": be_signature,
        "be_signature_count_among_36": signature_counts[be_signature],
        "gi_signature": gi_signature,
        "gi_signature_count_among_36": signature_counts[gi_signature],
        "both_pair_and_mirror_valid_on_both_count": signature_counts[
            (True, True, True, True)
        ],
        "interpretation": (
            "Each stream's best pair is valid on both streams and its mirror "
            "fails on the origin stream while remaining valid on the other. "
            "The DBBI-best signature is unique among 36 pairs; the FAED-best "
            "signature is shared by five. The low opposite-stream mirror ranks "
            "and completed {h,e} negatives prevent promotion to a decoder."
        ),
    }


def both_endpoint_audit():
    report = boundary.audit()
    film = report["sources"]["film"]["moment_to_choice"]["tokens"]
    screenplay = report["sources"]["screenplay"]["moment_to_choice"]["tokens"]
    stable_positions = tuple(
        index + 1
        for index in range(min(len(film), len(screenplay)))
        if film[index] == screenplay[index]
    )
    first_block = " ".join(film[:26])
    expected_block = (
        "which brings us at last to the moment of truth wherein the fundamental "
        "flaw is ultimately expressed and the anomaly revealed as both beginning and end"
    )
    if first_block != expected_block:
        raise AssertionError("affirmative BOTH clause or its boundary changed")

    but_rows = []
    for indices in itertools.permutations(stable_positions, 3):
        row = rails(film, indices)
        if row["initials"] != "but":
            continue
        mixed_edge = row["tokens"][0][0] + row["tokens"][1][-1] + row["tokens"][2][-1]
        but_rows.append(
            {
                **row,
                "partial_mirror_finals": partial_mirror9(row["finals"]),
                "mixed_first_beginning_other_endings": mixed_edge,
            }
        )

    first_words = Counter(row["tokens"][0] for row in but_rows)
    mirror_endpoint_words = tuple(
        sorted(
            word
            for word in first_words
            if word[0] in "abcdefghi"
            and word[-1] in "abcdefghi"
            and mirror9(word[0]) == word[-1]
        )
    )
    bye_rows = tuple(row for row in but_rows if row["partial_mirror_finals"] == "bye")
    mixed_bye_rows = tuple(
        row
        for row in but_rows
        if row["mixed_first_beginning_other_endings"] == "bye"
    )
    return {
        "exact_clause": first_block,
        "clause_polarity": "affirmative, not negated or conditional",
        "two_door_ultimatum_occurs_after_clause": True,
        "selected_words": ("both", "ultimately", "the"),
        "selected_both_endpoints": ("b", "h"),
        "selected_both_endpoints_are_mirror9": mirror9("b") == "h",
        "but_rows": len(but_rows),
        "first_word_counts": dict(sorted(first_words.items())),
        "first_words_with_mirror9_endpoints": mirror_endpoint_words,
        "partial_mirror_bye_rows": len(bye_rows),
        "all_partial_mirror_bye_rows_start_with_both": all(
            row["tokens"][0] == "both" for row in bye_rows
        ),
        "mixed_edge_bye_rows": len(mixed_bye_rows),
        "interpretation": (
            "BOTH is the only eligible B-initial word whose own endpoints are "
            "a mirror9 pair, and every partial-mirror BYE control row starts "
            "with BOTH. This adds internal support for inspecting B/H edges. "
            "It does not authenticate transforming the endings rail: the "
            "simpler mixed-edge rule yields BYE in 15/48 rows and is weaker."
        ),
    }


def output_role_audit():
    solved_names = {row["operator"] for row in operator_inventory.SOLVED_OPERATORS}
    required = {
        "decode 8-bit binary as ASCII",
        "Base64 decode",
        "enter/submit literal password",
        "concatenate ordered fields",
        "EBCDIC 1141 then Beaufort",
        "keyed straddling-checkerboard decode",
        "hash concatenated visible text",
    }
    if not required <= solved_names:
        raise AssertionError("solved operator inventory no longer supports role census")

    tier1 = {
        line.strip().lower()
        for line in TIER1_CANDIDATES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    role_counts = Counter(row["role"] for row in PUZZLE_DERIVED_OUTPUT_ROLES)
    return {
        "puzzle_derived_outputs": PUZZLE_DERIVED_OUTPUT_ROLES,
        "role_counts": dict(sorted(role_counts.items())),
        "credential_count": sum(row["credential"] for row in PUZZLE_DERIVED_OUTPUT_ROLES),
        "noncredential_count": sum(
            not row["credential"] for row in PUZZLE_DERIVED_OUTPUT_ROLES
        ),
        "pure_terminal_recognition_word_precedents": (),
        "bingo_control": {
            "source_class": "external creator confirmation, not puzzle-derived output",
            "comparable_to_bye": False,
            "present_in_tier1_candidate_corpus": "bingo" in tier1,
        },
        "interpretation": (
            "Solved GSMG stages clearly emit non-credentials (instructions, "
            "routes, and prose), so an output need not become a password. They "
            "do not establish a clean puzzle-derived terminal recognition-word "
            "precedent. Bingo is an external confirmation and later entered a "
            "candidate corpus, so it cannot serve as the proposed control."
        ),
    }


def model_comparison(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    minimal = minimal_macro_chain_audit.audit(export_path)
    if minimal["macro_steps"] != (
        "yellowblueprimes",
        "matrixsumlist",
        "lastwordsbeforearchichoice",
        "yinyang",
    ):
        raise AssertionError("authenticated macro prefix changed")

    if not all(word in SELECTED_31 for word in SELECTED_31_CONTROL["real_hits"]):
        raise AssertionError("selected-31 historical word hits changed")

    models = {
        "A_selected_31_operand": {
            "consumed_macro_tokens": ("yellowblueprimes",),
            "next_token_status": "matrixsumlist has no sourced consumer",
            "completed_macro_edges": 1,
            "missing_operation_fields": MODEL_A_MISSING_FIELDS,
            "reaches_but_hye": False,
            "reaches_yinyang": False,
            "output": SELECTED_31,
        },
        "B_six_digit_prime": {
            "consumed_macro_tokens": (
                "yellowblueprimes",
                "matrixsumlist",
                "lastwordsbeforearchichoice",
            ),
            "next_token_status": "yinyang recognition remains unverified",
            "completed_macro_edges": 3,
            "remaining_judgment_calls": minimal["scope_comparison"]
            ["minimal_prime_operand"]["remaining_judgment_calls"],
            "reaches_but_hye": True,
            "reaches_yinyang": False,
            "output": "BUT/HYE (BYE remains conditional)",
        },
    }
    return {
        "models": models,
        "default_working_model": "B_six_digit_prime",
        "why": (
            "Model B consumes three consecutive authenticated macro tokens and "
            "reaches the cross-source-stable BUT/HYE boundary with three visible "
            "judgment calls. Model A consumes one token and then requires seven "
            "unfixed G3 fields. Neither reaches authenticated yinyang."
        ),
        "selected_31_control": SELECTED_31_CONTROL,
        "selected_31_disposition": "structural checkpoint; parked",
        "selected_31_recognition_promoted": False,
        "selected_31_priority_row": False,
        "selected_31_reopen_trigger": (
            "primary evidence binding the exact selection to matrix dimensions, "
            "placement, values, aggregation, serialization, and a target"
        ),
    }


def audit(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    comparison = model_comparison(export_path)
    both = both_endpoint_audit()
    roles = output_role_audit()
    mirrors = mirror_orbit_audit()
    return {
        "model_comparison": comparison,
        "both_endpoint_control": both,
        "output_role_inventory": roles,
        "mirror_orbit_table": mirrors,
        "promotion": {
            "model_b_becomes_default": True,
            "selected_31_disposition_changes": True,
            "bye_becomes_credential": False,
            "bye_becomes_creator_confirmed_recognition": False,
            "new_decoder_or_oracle_authorized": False,
        },
        "verdict": (
            "Use the six-digit-prime grammar as the default macro model and "
            "reclassify the exact 31-character extraction as a structural "
            "checkpoint, parked pending a complete source binding. BOTH supplies "
            "real internal B/H endpoint support, but BYE remains conditional and "
            "non-credential. The mirror table is descriptive and authorizes no "
            "new FAED/DBBI decoder or blob oracle."
        ),
    }


def self_test(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    report = audit(export_path)
    comparison = report["model_comparison"]
    assert comparison["models"]["A_selected_31_operand"]["completed_macro_edges"] == 1
    assert comparison["models"]["B_six_digit_prime"]["completed_macro_edges"] == 3
    assert comparison["selected_31_disposition"] == "structural checkpoint; parked"
    assert not comparison["selected_31_recognition_promoted"]

    both = report["both_endpoint_control"]
    assert both["clause_polarity"] == "affirmative, not negated or conditional"
    assert both["first_word_counts"] == {"beginning": 16, "both": 16, "brings": 16}
    assert both["first_words_with_mirror9_endpoints"] == ("both",)
    assert both["partial_mirror_bye_rows"] == 5
    assert both["all_partial_mirror_bye_rows_start_with_both"]
    assert both["mixed_edge_bye_rows"] == 15

    roles = report["output_role_inventory"]
    assert roles["credential_count"] == 2
    assert roles["noncredential_count"] == 6
    assert roles["pure_terminal_recognition_word_precedents"] == ()
    assert roles["bingo_control"]["present_in_tier1_candidate_corpus"]

    mirrors = report["mirror_orbit_table"]
    dbbi_case, faed_case = mirrors["cases"]
    assert dbbi_case["best_pair_results"]["dbbi"]["rank"] == 1
    assert dbbi_case["mirror_pair"] == "eh"
    assert dbbi_case["mirror_pair_results"]["dbbi"] is None
    assert dbbi_case["mirror_pair_results"]["faed"]["rank"] == 16
    assert faed_case["best_pair_results"]["faed"]["rank"] == 1
    assert faed_case["mirror_pair"] == "ac"
    assert faed_case["mirror_pair_results"]["dbbi"]["rank"] == 24
    assert faed_case["mirror_pair_results"]["faed"] is None
    assert mirrors["be_signature_count_among_36"] == 1
    assert mirrors["gi_signature_count_among_36"] == 5
    assert not report["promotion"]["new_decoder_or_oracle_authorized"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: macro models, BOTH control, output roles, and mirror table")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=DEFAULT_EXPORT_DIR / "result.json",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export) if args.self_test else audit(args.export)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
