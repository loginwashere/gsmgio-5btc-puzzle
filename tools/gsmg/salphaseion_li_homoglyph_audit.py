#!/usr/bin/env python3
"""Test the `l`/`I` homoglyph reading of `SalPhaseIon`.

User-proposed hypothesis: lowercase `l` and uppercase `I` are visually
identical in many fonts (a classic homoglyph pair -- both render as a bare
vertical stroke). The archived title is deliberately mixed-case
(`SalPhaseIon`), and this project has already found the exact casing
meaningful (Phase 96's `Sal|Phase|Ion` word-boundary reading). Removing
the one `l` and the one `I` leaves `SaPhaseon` -- readable as `Sa`/`Phase`/
`on`. This is mechanically distinct from the Phase 96-99 `SALPHATION` word
(the creator's own coined term, differing from the title by a `PH`-vs-`T`
swap, not by dropping `l`/`I`); the two should not be conflated.

This also fits a recurring, creator-authored motif in this puzzle:
characters get flagged and removed/"zeroed out" to reveal an underlying
signal (the "some characters need to be zeroed out" thread, and the
`enter` marker removed to reconstitute the SalPhaseIon AES blob). That
gives this idea real motivation beyond "it happens to look tidy" -- worth
testing directly rather than debating.

Bounded scope, matching how every other title-derived candidate in this
investigation has been tested: verify the removal mechanically, generate a
small declared family of case/spacing variants, and test them as direct AES
passphrases against the tracked and quarantined blobs. No new cipher family.

**Combined follow-up (user-proposed):** apply Phase 97's already-established
`PH -> V` element-pair substitution (there derived from `SALPHATION` ->
`SALVATION`, not from this word) to `SaPhaseon` instead. `Phase` minus its
leading `Ph` plus `V` gives `Vase` -- a real English word -- so the full
remainder becomes `SaVaseon`, readable as `Sa`/`Vase`/`on`. This reuses an
existing, already-motivated substitution rather than inventing a new one,
but it is still exactly as post-hoc as the letter-value schemes flagged in
Phase 98-99: real words are dense enough in English that finding one
inside a 9-letter remainder after a chosen 2-for-1 substitution is not on
its own strong evidence. Tested directly for the same reason every other
cheap candidate in this investigation has been: real oracle test beats
debating plausibility.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from salphaseion_title_rebus_audit import EXPECTED_TITLE  # noqa: E402

REMOVED_CHARACTERS = ("l", "I")
EXPECTED_REMAINDER = "SaPhaseon"
EXPECTED_WORDS = ("Sa", "Phase", "on")

PH_SUBSTRING = "Ph"
V_REPLACEMENT = "V"
EXPECTED_COMBINED_REMAINDER = "SaVaseon"
EXPECTED_COMBINED_WORDS = ("Sa", "Vase", "on")

PHASE_SUBSTRING = "Phase"
VAT_REPLACEMENT = "VAT"
EXPECTED_VAT_REMAINDER = "SaVATon"
EXPECTED_VAT_WORDS = ("Sa", "VAT", "on")
PHONETIC_NEIGHBOR = "Sabaton"


def remove_homoglyphs(title):
    remainder = title
    for character in REMOVED_CHARACTERS:
        remainder = remainder.replace(character, "")
    return remainder


def apply_ph_to_v(remainder):
    if PH_SUBSTRING not in remainder:
        raise AssertionError(f"{PH_SUBSTRING!r} not found in {remainder!r}")
    return remainder.replace(PH_SUBSTRING, V_REPLACEMENT)


def apply_phase_to_vat(remainder):
    if PHASE_SUBSTRING not in remainder:
        raise AssertionError(f"{PHASE_SUBSTRING!r} not found in {remainder!r}")
    return remainder.replace(PHASE_SUBSTRING, VAT_REPLACEMENT)


def word_split(remainder, word_lengths):
    words = []
    cursor = 0
    for length in word_lengths:
        words.append(remainder[cursor:cursor + length])
        cursor += length
    if cursor != len(remainder):
        raise AssertionError("word lengths do not cover the full remainder")
    return words


def candidate_family(words):
    joined = "".join(words)
    spaced = " ".join(words)
    return (
        joined,
        joined.upper(),
        joined.lower(),
        spaced,
        spaced.upper(),
        spaced.lower(),
        "_".join(words),
        "-".join(words),
    )


def audit():
    remainder = remove_homoglyphs(EXPECTED_TITLE)
    if remainder != EXPECTED_REMAINDER:
        raise AssertionError(f"unexpected remainder: {remainder!r}")
    words = word_split(remainder, [len(word) for word in EXPECTED_WORDS])
    if tuple(words) != EXPECTED_WORDS:
        raise AssertionError(f"unexpected word split: {words}")
    candidates = candidate_family(words)

    combined_remainder = apply_ph_to_v(remainder)
    if combined_remainder != EXPECTED_COMBINED_REMAINDER:
        raise AssertionError(f"unexpected combined remainder: {combined_remainder!r}")
    combined_words = word_split(
        combined_remainder, [len(word) for word in EXPECTED_COMBINED_WORDS]
    )
    if tuple(combined_words) != EXPECTED_COMBINED_WORDS:
        raise AssertionError(f"unexpected combined word split: {combined_words}")
    combined_candidates = candidate_family(combined_words)

    vat_remainder = apply_phase_to_vat(remainder)
    if vat_remainder != EXPECTED_VAT_REMAINDER:
        raise AssertionError(f"unexpected VAT remainder: {vat_remainder!r}")
    vat_words = word_split(vat_remainder, [len(word) for word in EXPECTED_VAT_WORDS])
    if tuple(vat_words) != EXPECTED_VAT_WORDS:
        raise AssertionError(f"unexpected VAT word split: {vat_words}")
    vat_candidates = candidate_family(vat_words) + (PHONETIC_NEIGHBOR,)

    return {
        "title": EXPECTED_TITLE,
        "removed_characters": REMOVED_CHARACTERS,
        "remainder": remainder,
        "words": words,
        "candidates": candidates,
        "combined_remainder": combined_remainder,
        "combined_words": combined_words,
        "combined_candidates": combined_candidates,
        "vat_remainder": vat_remainder,
        "vat_words": vat_words,
        "vat_candidates": vat_candidates,
    }


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((candidate, keystring, result))
                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))
                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))
                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((candidate, keystring, result))
    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def print_report(report):
    print(f"[*] title: {report['title']}")
    print(f"[*] removed characters: {report['removed_characters']}")
    print(f"[*] remainder: {report['remainder']}")
    print(f"[*] word split: {report['words']}")
    print("[*] candidates:")
    for candidate in report["candidates"]:
        print(f"    {candidate!r}")
    print(f"[*] combined with Phase 97's PH -> V: {report['combined_remainder']}")
    print(f"[*] combined word split: {report['combined_words']}")
    print("[*] combined candidates:")
    for candidate in report["combined_candidates"]:
        print(f"    {candidate!r}")
    print(f"[*] combined with the title-rebus's Phase -> VAT: {report['vat_remainder']}")
    print(f"[*] VAT word split: {report['vat_words']}")
    print(f"[*] plus phonetic neighbor {PHONETIC_NEIGHBOR!r} (Sabaton, the band):")
    for candidate in report["vat_candidates"]:
        print(f"    {candidate!r}")


def self_test():
    report = audit()
    assert report["remainder"] == "SaPhaseon"
    assert report["words"] == ["Sa", "Phase", "on"]
    assert "SaPhaseon" in report["candidates"]
    assert "Sa Phase on" in report["candidates"]
    assert report["combined_remainder"] == "SaVaseon"
    assert report["combined_words"] == ["Sa", "Vase", "on"]
    assert "SaVaseon" in report["combined_candidates"]
    assert "Sa Vase on" in report["combined_candidates"]
    assert report["vat_remainder"] == "SaVATon"
    assert report["vat_words"] == ["Sa", "VAT", "on"]
    assert "SaVATon" in report["vat_candidates"]
    assert "Sa VAT on" in report["vat_candidates"]
    assert "Sabaton" in report["vat_candidates"]
    print("[*] self-test OK: homoglyph removal + word split + candidate family + PH->V + Phase->VAT combinations verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit()
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        all_candidates = (
            tuple(report["candidates"])
            + tuple(report["combined_candidates"])
            + tuple(report["vat_candidates"])
        )
        result = oracle_check(all_candidates, blobs)
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
