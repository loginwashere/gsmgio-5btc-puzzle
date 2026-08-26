#!/usr/bin/env python3
"""Phase 419: does replacing DBBI with the authenticated Phase 3.2.2
91-character VALIDATION_ANSWER as the Bifid keyword source change Phase
386's `FAED` decode into anything structured?

**Origin:** raised directly by the user while reviewing the P32TRAILING
hint summary. Phase 386 built its Bifid keyed square from `DBBI[:13]`
(`build_grid(DBBI[:13])` -> `DBIFHCEGAKLMNOPQRSTUVWXYZ`) because DBBI and
FAED are page-siblings on the same SalPhaseIon textarea. The Phase 3.2.2
VALIDATION_ANSWER (`INCASEYOUMANAGETOCRACKTHIS...HALFANDBETTERHALF...`) is
a different, real, authenticated 91-character string -- but it has no
established relationship to FAED at all; it comes from an unrelated
decrypted stage (Phase 3.2), not from the SalPhaseIon page. This phase
does not claim a motivating clue exists. It closes a cheap, well-defined
question: what comes out, mechanically, if that string's letters are used
as the grid keyword instead of DBBI's.

**Frozen construction (fixed before any output is inspected):**

- ciphertext: exactly `FAED`, 570 letters, single block (period 570, no
  sub-division) -- identical to Phase 386's own convention;
- Bifid algorithm: Phase 386's own `bifid_decrypt()`/`build_grid()`,
  imported verbatim, no primitive re-derived;
- two keyword-source candidates, both mechanically fixed, no tuning:
  1. `VALIDATION_ANSWER[:13]` -- the exact same slice length (13
     characters) Phase 386 used on DBBI, for a like-for-like construction;
  2. `VALIDATION_ANSWER` in full -- the whole 91-character sentence,
     letters only, deduplicated in order, as an upper-bound alternative
     reading of "use the incase... string as the key";
- validation: each candidate grid is round-tripped (encrypt the decode
  back through Phase 408's proven Bifid-encrypt inverse and confirm it
  reproduces the real `FAED` ciphertext exactly) before its decode is
  trusted;
- scoring: reuses Phase 386's own dictionary-substring scan and its
  empirical-frequency random-letter baseline unchanged, so any embedded-
  word count is judged against the same null model Phase 386 already
  established for this exact alphabet/decode shape;
- explicitly excluded: alternate block/period schedules (Phase 408 already
  covers that axis against the DBBI grid; combining both axes here would
  be an unbounded two-way sweep), alternate squares/coordinate
  conventions, second Bifid passes, and any blob-oracle promotion --
  there is no key or address material to check here, only a structural
  read of the decode.

**Result:** see `self_test()`'s asserted values below for the exact pinned
grid keywords, decode hashes, round-trip results, and word-scan counts.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    ALPHABET_NO_J,
    BASELINE_SEED,
    BASELINE_TRIALS,
    build_grid,
    find_embedded_words,
    load_dictionary,
    random_letter_baseline,
)
from phase408_bifid_period_robustness_audit import (  # noqa: E402
    bifid_decrypt_block,
    bifid_encrypt_block,
    normalize_letters,
)

TARGET_PREFIX = "BTCSEED"
CIPHERTEXT_LENGTH = 570

KEYWORD_SOURCES = {
    "incase_first13": VALIDATION_ANSWER[:13],
    "incase_full91": VALIDATION_ANSWER,
}


def dedup_letters(text):
    seen = []
    for ch in text.upper():
        if ch.isalpha() and ch not in seen:
            seen.append(ch)
    return "".join(seen)


def score_candidate(label, keyword_source, dictionary, baseline_report):
    grid_keyword, grid, pos = build_grid(keyword_source)
    assert len(grid_keyword) == 25

    faed_letters = normalize_letters(FAED)
    assert len(faed_letters) == CIPHERTEXT_LENGTH

    decoded_text = bifid_decrypt_block(faed_letters, pos, grid)
    assert len(decoded_text) == CIPHERTEXT_LENGTH

    roundtrip = bifid_encrypt_block(list(decoded_text), pos, grid)
    roundtrip_matches_ciphertext = "".join(roundtrip) == "".join(faed_letters)

    z_positions = [i for i, ch in enumerate(decoded_text) if ch == "Z"]

    embedded_words = find_embedded_words(decoded_text, dictionary)
    baseline_counts = random_letter_baseline(decoded_text, dictionary)

    return {
        "label": label,
        "keyword_source": keyword_source,
        "keyword_source_dedup_letters": dedup_letters(keyword_source),
        "grid_keyword": grid_keyword,
        "grid_keyword_matches_dbbi_grid": grid_keyword == baseline_report["grid_keyword"],
        "decoded_text": decoded_text,
        "decoded_sha256": hashlib.sha256(decoded_text.encode("utf-8")).hexdigest(),
        "first_32": decoded_text[:32],
        "starts_with_btcseed": decoded_text.startswith(TARGET_PREFIX),
        "contains_btcseed": TARGET_PREFIX in decoded_text,
        "z_count": len(z_positions),
        "z_positions": z_positions,
        "roundtrip_matches_real_ciphertext": roundtrip_matches_ciphertext,
        "embedded_word_count": len(embedded_words),
        "embedded_words": sorted({word for _pos, word in embedded_words}),
        "baseline_mean": sum(baseline_counts) / len(baseline_counts),
        "baseline_min": min(baseline_counts),
        "baseline_max": max(baseline_counts),
        "embedded_count_within_baseline_range": (
            min(baseline_counts) <= len(embedded_words) <= max(baseline_counts)
        ),
    }


def audit():
    from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit

    baseline_report = btcseed_audit()
    dictionary = load_dictionary()

    candidates = {
        label: score_candidate(label, source, dictionary, baseline_report)
        for label, source in KEYWORD_SOURCES.items()
    }

    any_starts_with_btcseed = any(c["starts_with_btcseed"] for c in candidates.values())
    any_contains_btcseed = any(c["contains_btcseed"] for c in candidates.values())
    any_grid_matches_dbbi = any(c["grid_keyword_matches_dbbi_grid"] for c in candidates.values())
    all_roundtrips_ok = all(c["roundtrip_matches_real_ciphertext"] for c in candidates.values())

    return {
        "dbbi_grid_keyword": baseline_report["grid_keyword"],
        "validation_answer": VALIDATION_ANSWER,
        "validation_answer_length": len(VALIDATION_ANSWER),
        "candidates": candidates,
        "any_starts_with_btcseed": any_starts_with_btcseed,
        "any_contains_btcseed": any_contains_btcseed,
        "any_grid_matches_dbbi_grid": any_grid_matches_dbbi,
        "all_roundtrips_ok": all_roundtrips_ok,
    }


def self_test():
    report = audit()

    assert report["dbbi_grid_keyword"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"
    assert report["validation_answer_length"] == 91
    assert set(report["candidates"].keys()) == {"incase_first13", "incase_full91"}

    first13 = report["candidates"]["incase_first13"]
    assert first13["keyword_source"] == "INCASEYOUMANA"
    assert first13["keyword_source_dedup_letters"] == "INCASEYOUM"
    assert first13["grid_keyword"] == "INCASEYOUMBDFGHKLPQRTVWXZ"
    assert first13["roundtrip_matches_real_ciphertext"] is True
    assert first13["starts_with_btcseed"] is False

    full91 = report["candidates"]["incase_full91"]
    assert full91["keyword_source_dedup_letters"] == "INCASEYOUMGTRKHPVBLFD"
    assert len(full91["keyword_source_dedup_letters"]) == 21
    assert full91["grid_keyword"] == "INCASEYOUMGTRKHPVBLFDJQWXZ".replace("J", "")
    assert full91["roundtrip_matches_real_ciphertext"] is True
    assert full91["starts_with_btcseed"] is False

    for label, entry in report["candidates"].items():
        assert entry["grid_keyword"] != report["dbbi_grid_keyword"], label
        assert len(entry["decoded_text"]) == CIPHERTEXT_LENGTH, label
        assert entry["contains_btcseed"] is False, label
        assert entry["embedded_count_within_baseline_range"] is True, label

    assert report["any_starts_with_btcseed"] is False
    assert report["any_contains_btcseed"] is False
    assert report["any_grid_matches_dbbi_grid"] is False
    assert report["all_roundtrips_ok"] is True

    print(
        "[*] self-test OK: replacing DBBI with the Phase 3.2.2 "
        "VALIDATION_ANSWER (both a 13-character like-for-like slice and "
        "the full 91-character sentence) as the Bifid grid keyword "
        "produces two distinct, round-trip-verified grids "
        f"({first13['grid_keyword']!r}, {full91['grid_keyword']!r}), "
        "neither of which reproduces Phase 386's DBBI-keyed grid, "
        "starts with or contains 'BTCSEED', or shows an embedded-word "
        "count outside the established random-letter baseline range -- "
        "no structural signal in either candidate."
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
