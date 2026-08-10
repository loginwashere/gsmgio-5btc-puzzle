#!/usr/bin/env python3
"""Architect-passage residual audit (Phase 235).

Closes three small, bounded items left open by the Phase 3.2.1 brainstorm
thread (Phase 118, 232-234) without reopening any of the already-closed
hypotheses:

1. Two words in the custom passage trace to the screenplay draft rather than
   the film soundtrack, while one word-order choice traces the other way.
   This is a provenance texture, not a password.
2. `key`, `note`, `self`, `keynote`, and the literal contiguous `selfself`
   run were already covered as checkerboard keywords (ordinary dictionary
   entries, part of Phase 2's default wordlist sweep) but never as direct
   blob passwords. That gap is closed here, bounded to those five forms.
3. Neither creator export corpus contains any commentary on this specific
   passage's tone (architect / 3.2.1 / matrix text all return zero creator
   hits). The "theatrical misdirection" reading stays an inference from
   general anti-bruteforce guidance, not a documented creator intent.

No decoder, autokey, or new-branch oracle is authorized by any of this.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

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
from telegram_export_manifest import DEFAULT_EXPORT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = (
    PROJECT_ROOT / "wordlists" / "matrix" / "the-matrix-reloaded-2003.pdf"
)
PDF_SHA256 = "2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4"

SRT_PATH = PROJECT_ROOT / "wordlists" / "matrix" / "the-matrix-reloaded-2003.en.srt"

CREATOR_ID = "user9815232"
SUPPORT_RESULT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/"
    "ChatExport_2026-07-29 (2)/result.json"
)

# Custom-puzzle text fragments containing the disputed words, verified against
# the authenticated README walkthrough in the prior brainstorm exchange.
PUZZLE_TEMPORARY = "ALLOWING A TEMPORARY DISSEMINATION OF THE CODE"
PUZZLE_ULTIMATELY = "WILL ULTIMATELY RESULT IN THE EXTINCTION"
PUZZLE_NOW_TO = "THE FUNCTION OF THE YOU IS NOW TO RETURN TO THE SOURCE CODES"

# Film SRT lines (subtitles 1099-1107) confirmed absent both words and using
# "now to" word order; read directly, not re-derived from any prior script.
FILM_DISSEMINATION_LINE = (
    "is now to return to the source, allowing a dissemination of the code "
    "you carry"
)
FILM_EXTINCTION_LINE = (
    "will result in the extinction of the entire human race"
)

CANDIDATES = ("key", "note", "self", "keynote", "selfself")

COVERAGE = {
    "key": {"checkerboard_keyword_dictionary_sweep": True, "direct_blob_password": False},
    "note": {"checkerboard_keyword_dictionary_sweep": True, "direct_blob_password": False},
    "self": {"checkerboard_keyword_dictionary_sweep": True, "direct_blob_password": False},
    "keynote": {"checkerboard_keyword_dictionary_sweep": True, "direct_blob_password": False},
    "selfself": {"checkerboard_keyword_dictionary_sweep": False, "direct_blob_password": False},
}

SEARCH_TERMS = (
    r"\barchitect\b",
    r"3\.2\.1",
    r"matrix text",
    r"\bjoke\b",
    r"\bkidding\b",
    r"\bdramatic\b",
    r"\btheatric",
    r"exaggerat",
    r"\bparody\b",
    r"\bcaricature\b",
)
EXPECTED_SOLVER_HITS = {
    r"\barchitect\b": (),
    r"3\.2\.1": (),
    r"matrix text": (),
    r"\bjoke\b": (66561,),
    r"\bkidding\b": (),
    r"\bdramatic\b": (9550, 9601, 32613),
    r"\btheatric": (),
    r"exaggerat": (),
    r"\bparody\b": (),
    r"\bcaricature\b": (),
}
EXPECTED_SUPPORT_HITS = {
    r"\barchitect\b": (),
    r"3\.2\.1": (),
    r"matrix text": (),
    r"\bjoke\b": (12097, 42342, 63031, 66563),
    r"\bkidding\b": (5285, 13932, 15314, 16016, 23290, 24493, 49023, 55347, 60581),
    r"\bdramatic\b": (),
    r"\btheatric": (),
    r"exaggerat": (),
    r"\bparody\b": (9164,),
    r"\bcaricature\b": (),
}
CLASSIFIED_UNRELATED = {
    9550: "personal safety aside, not the puzzle",
    9601: "unrelated small-chance remark",
    32613: "ASCII-127 trivia aside",
    66561: "already-established spur-of-the-moment/frenzy message (Phase 230)",
    12097: "unrelated IT joke",
    42342: "unrelated disclaimer joke",
    63031: "unrelated wordplay aside",
    66563: "adjacent to the frenzy message, general, not passage-specific",
    9164: "joked-about bitconnect promo-video parody idea, unrelated",
    5285: "unrelated", 13932: "unrelated", 15314: "unrelated", 16016: "unrelated",
    23290: "unrelated", 24493: "unrelated", 49023: "unrelated", 55347: "unrelated",
    60581: "unrelated",
}


def pdftotext_flat(pdf_path=PDF_PATH):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True, capture_output=True, text=True,
    )
    return " ".join(completed.stdout.split())


def screenplay_provenance():
    flat = pdftotext_flat()
    if "a temporary dissemination of the code you carry" not in flat.lower():
        raise AssertionError("screenplay 'temporary dissemination' wording drifted")
    if "will ultimately result in the extinction of the entire human race" not in flat.lower():
        raise AssertionError("screenplay 'ultimately result' wording drifted")
    if "is to now return to the source" not in flat.lower():
        raise AssertionError("screenplay 'to now return' word order drifted")

    srt = " ".join(SRT_PATH.read_text(encoding="utf-8", errors="replace").lower().split())
    if FILM_DISSEMINATION_LINE not in srt or "temporary" in FILM_DISSEMINATION_LINE:
        raise AssertionError("film dissemination line drifted")
    if FILM_EXTINCTION_LINE not in srt or "ultimately" in FILM_EXTINCTION_LINE:
        raise AssertionError("film extinction line drifted")
    if "is now to return to the source" not in srt:
        raise AssertionError("film word order drifted")

    return {
        "temporary": {
            "in_puzzle_text": True,
            "in_screenplay": True,
            "in_film_dialogue": False,
            "puzzle_fragment": PUZZLE_TEMPORARY,
        },
        "ultimately": {
            "in_puzzle_text": True,
            "in_screenplay": True,
            "in_film_dialogue": False,
            "puzzle_fragment": PUZZLE_ULTIMATELY,
        },
        "now_to_word_order": {
            "puzzle_reads": "is now to return",
            "matches_screenplay": False,
            "matches_film": True,
        },
        "interpretation": (
            "The creator's wording is not uniformly sourced from either fixed "
            "document: two content words trace to the screenplay draft and "
            "are absent from the actual film dialogue, while one word-order "
            "choice traces the other way. This is consistent with recollection "
            "blended from both, not a single pinned source text, and matches "
            "the two-sloppy-days construction already established (Phase 230)."
        ),
    }


def flatten_text(message):
    text = message.get("text")
    if isinstance(text, list):
        return "".join(part if isinstance(part, str) else part.get("text", "") for part in text)
    return text or ""


def creator_search(export_path):
    payload = json.loads(Path(export_path).read_text(encoding="utf-8"))
    hits = {}
    for pattern in SEARCH_TERMS:
        regex = re.compile(pattern, re.I)
        hits[pattern] = tuple(
            message["id"]
            for message in payload["messages"]
            if message.get("from_id") == CREATOR_ID and regex.search(flatten_text(message))
        )
    return hits


def candidate_keystrings(candidate):
    return tuple(
        sorted(
            {
                keystring
                for form in answer_forms(candidate)
                for keystring in keystr_forms(form, newline_variants=True)
            }
        )
    )


def direct_password_check(candidates=CANDIDATES, blobs=BLOBS):
    total_hits = 0
    per_candidate = {}
    for candidate in candidates:
        keystrings = candidate_keystrings(candidate)
        hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
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
        candidate_total = sum(len(rows) for rows in hits.values())
        total_hits += candidate_total
        per_candidate[candidate] = {
            "keystring_count": len(keystrings),
            "hits": hits,
            "total_hits": candidate_total,
        }
    return {
        "candidates": candidates,
        "blob_count": len(blobs),
        "per_candidate": per_candidate,
        "grand_total_hits": total_hits,
    }


def audit(export_dir=DEFAULT_EXPORT_DIR, support_result=SUPPORT_RESULT):
    provenance = screenplay_provenance()

    solver_hits = creator_search(Path(export_dir) / "result.json")
    support_hits = creator_search(support_result)
    if solver_hits != EXPECTED_SOLVER_HITS:
        raise AssertionError(f"solver-corpus tone search drifted: {solver_hits}")
    if support_hits != EXPECTED_SUPPORT_HITS:
        raise AssertionError(f"support-corpus tone search drifted: {support_hits}")

    all_hit_ids = sorted(
        {mid for rows in solver_hits.values() for mid in rows}
        | {mid for rows in support_hits.values() for mid in rows}
    )
    for message_id in all_hit_ids:
        if message_id not in CLASSIFIED_UNRELATED:
            raise AssertionError(f"tone-search hit {message_id} lacks a classification")

    oracle = direct_password_check()
    if oracle["grand_total_hits"] != 0:
        raise AssertionError("unexpected direct-password hit; stop and inspect")

    passage_specific_commentary_found = any(
        solver_hits[pattern] or support_hits[pattern]
        for pattern in (r"\barchitect\b", r"3\.2\.1", r"matrix text")
    )

    return {
        "screenplay_provenance": provenance,
        "creator_tone_search": {
            "solver_hits": solver_hits,
            "support_hits": support_hits,
            "all_hit_ids": tuple(all_hit_ids),
            "classification": CLASSIFIED_UNRELATED,
            "passage_specific_commentary_found": passage_specific_commentary_found,
        },
        "coverage_census": COVERAGE,
        "bounded_direct_password_check": oracle,
        "gates": {
            "creator_confirmed_theatrical_misdirection": False,
            "any_bounded_candidate_opens_a_tracked_blob": False,
        },
        "promoted": False,
        "verdict": (
            "Two words in the custom passage (temporary, ultimately) trace to "
            "the screenplay draft and are absent from the film; one word-order "
            "choice (now to) traces the other way -- a real but inconclusive "
            "provenance texture, not a password. Neither creator corpus "
            "contains any passage-specific tone commentary (architect / 3.2.1 "
            "/ matrix text all return zero hits), so the 'theatrical "
            "misdirection' reading in the brainstorm report remains an "
            "inference from general anti-bruteforce guidance, not a "
            "documented creator statement. The direct-password gap for key, "
            "note, self, keynote, and the literal selfself run is now closed: "
            "0 hits across all four tracked blobs."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR, support_result=SUPPORT_RESULT):
    report = audit(export_dir, support_result)
    assert report["screenplay_provenance"]["temporary"]["in_screenplay"]
    assert not report["screenplay_provenance"]["temporary"]["in_film_dialogue"]
    assert not report["screenplay_provenance"]["now_to_word_order"]["matches_screenplay"]
    assert report["screenplay_provenance"]["now_to_word_order"]["matches_film"]
    assert not report["creator_tone_search"]["passage_specific_commentary_found"]
    assert len(report["creator_tone_search"]["all_hit_ids"]) == 18
    assert report["coverage_census"]["keynote"]["checkerboard_keyword_dictionary_sweep"]
    assert not report["coverage_census"]["selfself"]["checkerboard_keyword_dictionary_sweep"]
    assert report["bounded_direct_password_check"]["blob_count"] == 4
    assert report["bounded_direct_password_check"]["grand_total_hits"] == 0
    assert not report["promoted"]
    print(json.dumps(report, indent=2, default=list))
    print("[*] self-test OK: screenplay/film provenance split, tone search negative, oracle negative")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--support-result", type=Path, default=SUPPORT_RESULT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = (
        self_test(args.export_dir, args.support_result)
        if args.self_test
        else audit(args.export_dir, args.support_result)
    )
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2, default=list))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
