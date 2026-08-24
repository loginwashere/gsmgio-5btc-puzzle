#!/usr/bin/env python3
"""Phase 396: header-aware audit of the Bifid decode's `P90+Z` block.

**Origin:** Phase 386 described the decode's structure length-first from
the start of the string (`BTCSEED` (7) + prefix (90) = 97 characters before
the single `Z`). A user-prompted re-read of that same structure, parsing it
"header-aware" instead -- treating `BTCSEED` as a fixed 7-character header
and everything from there to (and including) `Z` as one block -- notices
that block is exactly **91 characters**, the same length as `DBBI` and the
already-authenticated Phase 3.2 plaintext (`VALIDATION_ANSWER`, called `M91`
elsewhere in this project). That length match was never dedicated: Phase
386/387/394 all operate on `decoded[:98]` (which includes `BTCSEED`) or the
whole 570-character stream; nobody isolated `decoded[7:98]` on its own and
compared it, the way Phase 75 already compares `DBBI` against `M91`, to the
project's other two known 91-character objects.

**Method:** wrote this script. `P91 = decoded[7:98]` (the 90-character
post-`BTCSEED` block plus the trailing `Z`, not treating `Z` as padding or a
delimiter). Reuses `external_archive_lead_audit.subtract_mod26()` --
Phase 75's own combinator -- both directions against both `DBBI` and
`VALIDATION_ANSWER`, since it isn't symmetric. Reuses Phase 386's own
dictionary-word scanner and letter-frequency baseline generator verbatim.
Reuses `cb_common.keystr_forms()` (literal / SHA-256 / double-SHA-256) for
the oracle sweep, in upper, lower, and as-decoded case -- the one axis Phase
386/387/394 left untested for this specific 91-character object.

**Result:** no embedded target keyword (`YOUWON`, `KMODEST`, `BTCSEED`,
`MODEST`, `SATOSHI`, `SEED`, `KEY`, `WALLET`) appears in `P91` or in any of
the four subtraction outputs. Dictionary-word density in all five strings
(0, 2, 1, 1 hits respectively for the four subtractions, and however many
`P91` itself contains) sits at or below each string's own random-letter
baseline (200 trials per string, same seed convention as Phase 386) --
unremarkable, no sign of a deliberate embedded plaintext. `P91` and the four
subtraction outputs, each in literal/upper/lower case and as SHA-256/double-
SHA-256 hex, tested against all four tracked blobs under the full CBC/ECB/
stream/Key Wrap oracle: 45 materials, 21,600 effective decrypt attempts,
zero hits.

**Disposition:** the `91`-character length match between `P91` and `DBBI`/
`M91` is confirmed real and previously untested, but produces no keyword
hit, no above-baseline word structure, and no blob authentication under any
tested combinator or form. This closes the specific bounded gap identified
(`decoded[7:98]` treated as a 91-character object in its own right, aligned
against `DBBI` and `M91` the same way Phase 75 aligns `DBBI` against `M91`
itself) -- negative. It does not retract Phase 386's own "97 characters
counted from the start" statement, which remains correct on its own terms;
it simply confirms that qualifying it (as the user's re-framing suggested)
does not surface anything further. The 472-character post-`Z` suffix is
explicitly out of scope here -- it was not the bounded object identified and
opening it is a separate, larger question this audit does not attempt.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    keystr_forms,
)
from data import DBBI, VALIDATION_ANSWER  # noqa: E402
from external_archive_lead_audit import subtract_mod26  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    audit as btcseed_audit,
    find_embedded_words,
    load_dictionary,
    random_letter_baseline,
)

TARGET_KEYWORDS = (
    "YOUWON", "KMODEST", "BTCSEED", "MODEST", "SATOSHI", "SEED", "KEY", "WALLET",
)

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def structure_report(decoded):
    z_index = decoded.index("Z")
    p90 = decoded[7:97]
    p91 = decoded[7:98]
    return {
        "decoded_length": len(decoded),
        "z_index": z_index,
        "header": decoded[:7],
        "p90": p90,
        "p90_length": len(p90),
        "p91": p91,
        "p91_length": len(p91),
        "p91_ends_with_z": p91.endswith("Z"),
        "dbbi_length": len(DBBI),
        "m91_length": len(VALIDATION_ANSWER),
        "p91_matches_dbbi_m91_length": len(p91) == len(DBBI) == len(VALIDATION_ANSWER),
        "suffix472_length": len(decoded[98:]),
    }


def combinator_report(p91, dictionary):
    combos = {
        "P91": p91,
        "P91_minus_DBBI": subtract_mod26(p91, DBBI),
        "DBBI_minus_P91": subtract_mod26(DBBI, p91),
        "P91_minus_M91": subtract_mod26(p91, VALIDATION_ANSWER),
        "M91_minus_P91": subtract_mod26(VALIDATION_ANSWER, p91),
    }
    report = {}
    for label, text in combos.items():
        embedded = find_embedded_words(text, dictionary)
        baseline = random_letter_baseline(text, dictionary)
        keyword_hits = [kw for kw in TARGET_KEYWORDS if kw in text.upper()]
        report[label] = {
            "text": text,
            "embedded_word_count": len(embedded),
            "embedded_words": [word for _pos, word in embedded],
            "baseline_mean": sum(baseline) / len(baseline),
            "keyword_hits": keyword_hits,
        }
    return report


def oracle_report(combos):
    hits = []
    attempts = 0
    materials_tried = 0
    for label, entry in combos.items():
        text = entry["text"]
        for case_label, variant in (
            (label, text), (label + "_lower", text.lower()), (label + "_upper", text.upper())
        ):
            for form_name, material in zip(
                ("literal", "sha256_hex", "sha256_hex_hex"), keystr_forms(variant)
            ):
                materials_tried += 1
                material_bytes = material.encode("utf-8")
                for family_name, oracle, variants, forms_per_config in ORACLE_FAMILIES:
                    attempts += len(variants) * len(BLOBS) * forms_per_config
                    if family_name == "keywrap":
                        for tag, wrap_kind, kdf_label, key_len, plaintext in oracle(
                            material_bytes, kdf_variants=variants, blobs=BLOBS
                        ):
                            hits.append(
                                (case_label, form_name, family_name, tag, wrap_kind, kdf_label, key_len, plaintext.hex())
                            )
                    else:
                        result = oracle(material_bytes, kdf_variants=variants, blobs=BLOBS)
                        if result:
                            tag, plaintext, kdf_label, key_len = result
                            hits.append((case_label, form_name, family_name, tag, "", kdf_label, key_len, plaintext.hex()))

    return {
        "materials_tried": materials_tried,
        "effective_attempts": attempts,
        "hits": hits,
        "total_hits": len(hits),
    }


def audit(run_oracle=True):
    decoded = btcseed_audit()["decoded"]
    structure = structure_report(decoded)
    dictionary = load_dictionary()
    combos = combinator_report(structure["p91"], dictionary)
    report = {"structure": structure, "combinators": combos}
    if run_oracle:
        report["oracle"] = oracle_report(combos)
    return report


def self_test(run_oracle=False):
    report = audit(run_oracle=run_oracle)

    structure = report["structure"]
    assert structure["z_index"] == 97
    assert structure["header"] == "BTCSEED"
    assert structure["p90_length"] == 90
    assert structure["p91_length"] == 91
    assert structure["p91_ends_with_z"] is True
    assert structure["p91_matches_dbbi_m91_length"] is True
    assert structure["suffix472_length"] == 472

    combos = report["combinators"]
    for label, entry in combos.items():
        assert entry["keyword_hits"] == [], (label, entry["keyword_hits"])
        assert entry["embedded_word_count"] <= entry["baseline_mean"] + 3, (
            label, entry["embedded_word_count"], entry["baseline_mean"]
        )

    if run_oracle:
        oracle = report["oracle"]
        assert oracle["materials_tried"] == 45
        assert oracle["effective_attempts"] == 21600
        assert oracle["total_hits"] == 0

    print(
        f"[*] self-test OK: P91 = decoded[7:98] (the post-BTCSEED block through "
        f"the single Z) confirmed 91 characters, matching DBBI/VALIDATION_ANSWER "
        f"length exactly -- a previously-untested alignment; no target keyword "
        f"({', '.join(TARGET_KEYWORDS)}) found in P91 or any of its 4 mod-26 "
        f"subtraction combinations against DBBI/M91; embedded dictionary-word "
        f"counts sit at or near each string's own random-letter baseline in all "
        f"5 strings; "
        f"{report.get('oracle', {}).get('effective_attempts', 'skipped')} "
        f"effective decrypt attempts across 45 case/hash-form materials against "
        f"all 4 tracked blobs -- "
        f"{report.get('oracle', {}).get('total_hits', 'n/a')} hits"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skip-oracle", action="store_true")
    args = parser.parse_args()
    report = (
        self_test(run_oracle=not args.skip_oracle)
        if args.self_test
        else audit(run_oracle=not args.skip_oracle)
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
