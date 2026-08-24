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
386/387/394 left untested for this specific 91-character object. Because the
Bifid decode and `subtract_mod26()` both emit uppercase A-Z, the as-decoded
and `.upper()` case forms are byte-identical for every one of these five
strings; case variants are deduplicated by value before the oracle sweep
runs, so 5 combinators x 2 distinct case forms x 3 hash forms = 30 unique
materials, not 45 (an earlier version of this script tested 45 labeled rows
without deduplicating, which inflated the reported material/attempt counts
by 50% without changing the zero-hit result).

**Result:** no embedded target keyword (`YOUWON`, `KMODEST`, `BTCSEED`,
`MODEST`, `SATOSHI`, `SEED`, `KEY`, `WALLET`) appears in `P91` or in any of
the four subtraction outputs. Dictionary-word counts (0, 0, 2, 1, 1 across
`P91` and the four subtractions) are compared against each string's own
200-trial random-letter-control baseline (same seed convention as Phase
386), using the empirical tail rate -- the fraction of control trials that
matched or exceeded the real count -- rather than an arbitrary absolute
cutoff. Three of the five counts exceed their control *mean* (`DBBI-P91`:
2 vs. 0.80, tail 39/200 = 19.5%; `P91-M91`: 1 vs. 0.42, tail 65/200 = 32.5%;
`M91-P91`: 1 vs. 0.41, tail 55/200 = 27.5%), but all five tail rates are
far from the extreme tail (>5%), so every count is within baseline
variation -- unremarkable, no sign of a deliberate embedded plaintext.
`P91` and the four subtraction outputs, in their 2 distinct case forms and
as SHA-256/double-SHA-256 hex: 30 unique materials, 14,400 effective
decrypt attempts against all four tracked blobs, zero hits.

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
    z_count = decoded.count("Z")
    z_index = decoded.index("Z")
    p90 = decoded[7:97]
    p91 = decoded[7:98]
    return {
        "decoded_length": len(decoded),
        "z_count": z_count,
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
        observed = len(embedded)
        baseline = random_letter_baseline(text, dictionary)
        keyword_hits = [kw for kw in TARGET_KEYWORDS if kw in text.upper()]
        tail_hits = sum(1 for count in baseline if count >= observed)
        report[label] = {
            "text": text,
            "embedded_word_count": observed,
            "embedded_words": [word for _pos, word in embedded],
            "baseline_mean": sum(baseline) / len(baseline),
            "baseline_trials": len(baseline),
            "baseline_tail_hits": tail_hits,
            "baseline_tail_rate": tail_hits / len(baseline),
            "keyword_hits": keyword_hits,
        }
    return report


def oracle_report(combos):
    hits = []
    attempts = 0
    materials_tried = 0
    for label, entry in combos.items():
        text = entry["text"]
        case_variants = {}
        for case_label, variant in (
            (label, text), (label + "_lower", text.lower()), (label + "_upper", text.upper())
        ):
            # All combinator outputs are already uppercase (Bifid decode and
            # subtract_mod26 both emit A-Z), so the as-decoded and .upper()
            # variants are byte-identical here. Dedupe by value so repeated
            # case forms aren't tested (and counted) twice -- keeps
            # "materials_tried" a true unique-material count, separate from
            # "effective_attempts" x duplicate-case-multiplicity below.
            case_variants.setdefault(variant, case_label)
        for variant, case_label in case_variants.items():
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
    assert structure["z_count"] == 1
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
        # Statistical test, not an arbitrary absolute allowance: the observed
        # count is unremarkable as long as a non-trivial fraction of the
        # random-letter control trials matched or exceeded it. A low tail
        # rate (deep in the extreme tail) would be the actual red flag.
        assert entry["baseline_tail_rate"] > 0.05, (
            label, entry["embedded_word_count"], entry["baseline_tail_rate"]
        )

    if run_oracle:
        oracle = report["oracle"]
        # 5 combinators x 2 distinct case forms (as-decoded/.upper() are
        # byte-identical -- both the Bifid decode and subtract_mod26 emit
        # uppercase A-Z) x 3 hash forms = 30 unique materials, not 45.
        assert oracle["materials_tried"] == 30
        assert oracle["effective_attempts"] == 14400
        assert oracle["total_hits"] == 0

    print(
        f"[*] self-test OK: P91 = decoded[7:98] (the post-BTCSEED block through "
        f"the single, confirmed-unique Z) is 91 characters, matching DBBI/"
        f"VALIDATION_ANSWER length exactly -- a previously-untested alignment; "
        f"no target keyword ({', '.join(TARGET_KEYWORDS)}) found in P91 or any "
        f"of its 4 mod-26 subtraction combinations against DBBI/M91; embedded "
        f"dictionary-word counts are within baseline variation in all 5 "
        f"strings (each observed count's random-letter-control tail rate > "
        f"5%, none in the extreme tail); "
        f"{report.get('oracle', {}).get('effective_attempts', 'skipped')} "
        f"effective decrypt attempts across "
        f"{report.get('oracle', {}).get('materials_tried', 'skipped')} unique "
        f"case/hash-form materials (case-duplicate rows deduped) against all "
        f"4 tracked blobs -- {report.get('oracle', {}).get('total_hits', 'n/a')} hits"
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
