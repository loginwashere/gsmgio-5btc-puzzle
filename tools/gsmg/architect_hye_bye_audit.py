#!/usr/bin/env python3
"""Audit the full-rail consequence HYE -> BYE under the existing mirror9 map.

The operation maps a-i symbols through mirror9 and passes symbols outside that
alphabet unchanged.  It is a natural partial substitution, but not an
authenticated instruction; this audit therefore calibrates the output before
allowing one exact candidate through the already-established blob oracle.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import architect_choice_boundary_audit as boundary
from cb_common import (
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from macro_tail_title_insertion_audit import (
    DEFAULT_DICTIONARY,
    EXPECTED_DICTIONARY_SHA256,
)
from prime_matrixsum_reconstruction import mirror9


NINE = "abcdefghi"
FIXED_INDICES = (23, 16, 7)
CANDIDATE = "bye"


def partial_mirror9(value):
    return "".join(mirror9(char) if char in NINE else char for char in value)


def rails(words, indices):
    selected = tuple(words[index - 1] for index in indices)
    return {
        "indices": tuple(indices),
        "tokens": selected,
        "initials": "".join(word[0] for word in selected),
        "finals": "".join(word[-1] for word in selected),
    }


def load_dictionary(path=DEFAULT_DICTIONARY):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_DICTIONARY_SHA256:
        raise AssertionError("dictionary corpus changed")
    words = {
        line.strip().lower()
        for line in raw.decode("utf-8", errors="ignore").splitlines()
        if line.strip().isalpha()
    }
    return words, digest


def structural_audit(dictionary_path=DEFAULT_DICTIONARY):
    base = boundary.audit()
    film = base["sources"]["film"]["moment_to_choice"]["tokens"]
    screenplay = base["sources"]["screenplay"]["moment_to_choice"]["tokens"]
    stable_positions = tuple(
        index + 1
        for index in range(min(len(film), len(screenplay)))
        if film[index] == screenplay[index]
    )
    words, dictionary_hash = load_dictionary(dictionary_path)

    fixed = rails(film, FIXED_INDICES)
    fixed["partial_mirror_finals"] = partial_mirror9(fixed["finals"])
    if fixed != {
        "indices": FIXED_INDICES,
        "tokens": ("both", "ultimately", "the"),
        "initials": "but",
        "finals": "hye",
        "partial_mirror_finals": "bye",
    }:
        raise AssertionError("fixed Architect rail changed")

    but_rows = []
    all_bye_rows = 0
    for indices in itertools.permutations(stable_positions, 3):
        row = rails(film, indices)
        transformed = partial_mirror9(row["finals"])
        if transformed == CANDIDATE:
            all_bye_rows += 1
        if row["initials"] == "but":
            row["partial_mirror_finals"] = transformed
            row["dictionary_output"] = transformed in words
            but_rows.append(row)

    output_counts = {}
    for row in but_rows:
        output = row["partial_mirror_finals"]
        output_counts[output] = output_counts.get(output, 0) + 1
    dictionary_rows = tuple(row for row in but_rows if row["dictionary_output"])
    dictionary_outputs = tuple(sorted({row["partial_mirror_finals"] for row in dictionary_rows}))

    permutations = []
    for indices in itertools.permutations(FIXED_INDICES):
        row = rails(film, indices)
        row["partial_mirror_finals"] = partial_mirror9(row["finals"])
        row["dictionary_output"] = row["partial_mirror_finals"] in words
        permutations.append(row)

    return {
        "operation": "mirror a-i through a<->i; preserve non-a-i symbols",
        "operation_authored": False,
        "fixed": fixed,
        "controls": {
            "stable_positions": len(stable_positions),
            "ordered_distinct_triples": len(stable_positions)
            * (len(stable_positions) - 1)
            * (len(stable_positions) - 2),
            "but_rows": len(but_rows),
            "distinct_partial_mirror_outputs_given_but": len(output_counts),
            "dictionary_rows_given_but": len(dictionary_rows),
            "dictionary_outputs_given_but": dictionary_outputs,
            "exact_bye_rows_all_triples": all_bye_rows,
            "exact_bye_rows_given_but": output_counts.get(CANDIDATE, 0),
        },
        "fixed_word_permutations": tuple(permutations),
        "dictionary_sha256": dictionary_hash,
        "semantic_support": {
            "last_command": (
                "BYE is naturally terminal language, but the page does not "
                "identify a command environment or explicitly name BYE"
            ),
            "authenticated_prior_plaintext": (
                "the solved Phase 3.2.1 plaintext ends CIAO BELLA O; this is "
                "thematic support, not a source-selected translation/operator"
            ),
            "creator_confirmation": False,
        },
        "promotion": {
            "status": "strong_recognition_candidate_not_transition_proof",
            "bounded_oracle_authorized": True,
            "reason": (
                "fixed source inputs plus the existing mirror9 map yield the "
                "only dictionary output in the 48-row BUT control family; one "
                "small exact candidate check is proportionate despite the "
                "unproved pass-through/polarity convention"
            ),
        },
    }


def candidate_keystrings():
    return tuple(
        sorted(
            {
                keystring
                for form in answer_forms(CANDIDATE)
                for keystring in keystr_forms(form, newline_variants=True)
            }
        )
    )


def oracle_check(blobs=BLOBS):
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    keystrings = candidate_keystrings()
    for keystring in keystrings:
        for variants in (None, EXTENDED_CIPHER_VARIANTS):
            result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
            if result:
                hits["cbc"].append((keystring, result))
        result = aes_try_open_ecb(keystring, blobs=blobs)
        if result:
            hits["ecb"].append((keystring, result))
        result = aes_try_open_stream(keystring, blobs=blobs)
        if result:
            hits["stream"].append((keystring, result))
        for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
            hits["keywrap"].append((keystring, result))
    return {
        "candidate": CANDIDATE,
        "keystring_count": len(keystrings),
        "blob_count": len(blobs),
        "hits": hits,
        "total_hits": sum(len(rows) for rows in hits.values()),
    }


def audit(dictionary_path=DEFAULT_DICTIONARY, run_oracle=True):
    structural = structural_audit(dictionary_path)
    oracle = oracle_check() if run_oracle else None
    return {
        "structural": structural,
        "oracle": oracle,
        "verdict": (
            "HYE -> BYE is a real, rare controlled recognition result and the "
            "best new consequence of the full rail. It does not prove the "
            "yin-yang transition because preserving Y and transforming only "
            "the endings rail are not authenticated. The bounded BYE direct/"
            "SHA family does not open a tracked blob."
            if oracle is not None and oracle["total_hits"] == 0
            else "Structural BYE recognition audited; oracle not run or produced a hit."
        ),
    }


def self_test(dictionary_path=DEFAULT_DICTIONARY):
    report = audit(dictionary_path, run_oracle=True)
    controls = report["structural"]["controls"]
    assert partial_mirror9("hye") == "bye"
    assert report["structural"]["fixed"]["partial_mirror_finals"] == "bye"
    assert controls["but_rows"] == 48
    assert controls["distinct_partial_mirror_outputs_given_but"] == 18
    assert controls["dictionary_rows_given_but"] == 5
    assert controls["dictionary_outputs_given_but"] == ("bye",)
    assert controls["exact_bye_rows_all_triples"] == 36
    assert controls["exact_bye_rows_given_but"] == 5
    assert sum(row["dictionary_output"] for row in report["structural"]["fixed_word_permutations"]) == 1
    assert report["oracle"]["keystring_count"] == 18
    assert report["oracle"]["blob_count"] == 4
    assert report["oracle"]["total_hits"] == 0
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: HYE->BYE controls and bounded four-blob oracle verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-oracle", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = (
        self_test(args.dictionary)
        if args.self_test
        else audit(args.dictionary, run_oracle=not args.no_oracle)
    )
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
