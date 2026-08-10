#!/usr/bin/env python3
"""CIAO selection-and-coverage audit (Phase 234).

Two questions only, both narrow:

1. Does either creator export corpus contain a message that selects CIAO/BYE
   as the yin-yang recognition state?  Phase 233 checked "ciao" but only in
   the puzzle-solvers export; Phase 230 established the support-group export
   as a separate, real corpus that must also be searched.
2. Which of the five CIAO/BELLA-family candidates already have documented
   test coverage (checkerboard keyword, direct blob password, autokey seed),
   and which are genuinely untested?  Only genuinely-missing, small, bounded
   cases are run here.  It does not index song lyrics against [23,16,7]
   (no creator instruction binds them there) and does not launch an
   autokey/chain-addition sweep (that requires a frozen algorithm and
   normalization, not attempted in this phase).
"""

import argparse
import json
import re
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
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


CREATOR_ID = "user9815232"
SUPPORT_RESULT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/"
    "ChatExport_2026-07-29 (2)/result.json"
)

SEARCH_TERMS = (
    r"\bciao\b",
    r"\bbella\b",
    r"\bbye\b",
    r"\bgoodbye\b",
    r"\byin\b",
    r"\byang\b",
    r"yinyang",
    r"\bpassword\b",
)

EXPECTED_SOLVER_HITS = {
    r"\bciao\b": (9632, 32773, 66609),
    r"\bbella\b": (),
    r"\bbye\b": (),
    r"\bgoodbye\b": (4272,),
    r"\byin\b": (),
    r"\byang\b": (9599,),
    "yinyang": (),
    r"\bpassword\b": (66909,),
}
EXPECTED_SUPPORT_HITS = {
    r"\bciao\b": (),
    r"\bbella\b": (),
    r"\bbye\b": (58072,),
    r"\bgoodbye\b": (),
    r"\byin\b": (),
    r"\byang\b": (),
    "yinyang": (),
    r"\bpassword\b": (52876,),
}
IRRELEVANT_CLASSIFICATION = {
    4272: "bot command '/goodbye off', not a farewell",
    66909: "BIP 360 wallet-security explainer, unrelated trading content",
    58072: "dismissal of a scammer ('Bye bye scammer'), not a puzzle sign-off",
    52876: "ordinary trading-account support question",
}

CANDIDATES = ("ciao", "bella", "ciaobellao", "obellaciao", "bellaciao")

# Coverage census, established by direct inspection of the existing scripts
# and wordlists (file:line evidence), not by re-running every historical sweep.
COVERAGE = {
    "ciao": {
        "checkerboard_keyword_pad28": False,
        "direct_blob_password": False,
        "autokey_or_chain_addition_seed": False,
        "evidence": ("wordlists/gsmg/chat_mined_words.txt:4235 (mined word only, never swept)",),
    },
    "bella": {
        "checkerboard_keyword_pad28": False,
        "direct_blob_password": False,
        "autokey_or_chain_addition_seed": False,
        "evidence": (
            "wordlists/gsmg/chat_mined_words.txt:2569 (mined word only)",
            "wordlists/gsmg/medium_curated_tier3_broad.txt:1013 (curated list, not a completed oracle sweep)",
        ),
    },
    "ciaobellao": {
        "checkerboard_keyword_pad28": True,
        "direct_blob_password": False,
        "autokey_or_chain_addition_seed": False,
        "evidence": (
            "wordlists/gsmg/phrases.txt:35, part of cosmic_sweep.py DEFAULT_WORDLISTS "
            "(Phase 2: pad28(candidate)->alphabet->decode(dbbi/faed)->AES try, "
            "SALPH+COSMIC only, 0 hits)",
            "alphabet_hypothesis_check.py:31, direct pad28(candidate)==ALPHA_322 check, 0 match",
        ),
    },
    "obellaciao": {
        "checkerboard_keyword_pad28": False,
        "direct_blob_password": False,
        "autokey_or_chain_addition_seed": False,
        "evidence": ("no standalone occurrence found in any tracked wordlist or script",),
    },
    "bellaciao": {
        "checkerboard_keyword_pad28": False,
        "direct_blob_password": False,
        "autokey_or_chain_addition_seed": False,
        "evidence": ("wordlists/gsmg/chat_mined_words.txt:2570 (mined word only, never swept)",),
    },
}
# ciaobella (without trailing o) is documented separately: it is covered the
# same way as ciaobellao (phrases.txt:34; alphabet_hypothesis_check.py:31) but
# is not one of the five candidates carried forward from the BYE->CIAO bridge,
# which uses the exact authenticated tail forms only.

COSMIC_SWEEP_BLOBS_AT_PHASE2 = ("SALPH", "COSMIC")


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
        matched = tuple(
            message["id"]
            for message in payload["messages"]
            if message.get("from_id") == CREATOR_ID and regex.search(flatten_text(message))
        )
        hits[pattern] = matched
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
    results = {}
    total_hits = 0
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
        results[candidate] = {
            "keystring_count": len(keystrings),
            "hits": hits,
            "total_hits": candidate_total,
        }
    return {
        "candidates": candidates,
        "blob_count": len(blobs),
        "per_candidate": results,
        "grand_total_hits": total_hits,
    }


def audit(export_dir=DEFAULT_EXPORT_DIR, support_result=SUPPORT_RESULT):
    solver_hits = creator_search(Path(export_dir) / "result.json")
    support_hits = creator_search(support_result)
    if solver_hits != EXPECTED_SOLVER_HITS:
        raise AssertionError(f"solver-corpus creator search drifted: {solver_hits}")
    if support_hits != EXPECTED_SUPPORT_HITS:
        raise AssertionError(f"support-corpus creator search drifted: {support_hits}")

    data = load_export(export_dir)
    texts = {message["id"]: plain_text(message) for message in data["messages"]}
    support_payload = json.loads(Path(support_result).read_text(encoding="utf-8"))
    support_texts = {message["id"]: flatten_text(message) for message in support_payload["messages"]}

    new_hit_ids = tuple(
        sorted(
            set(EXPECTED_SOLVER_HITS[r"\bgoodbye\b"])
            | set(EXPECTED_SOLVER_HITS[r"\bpassword\b"])
            | set(EXPECTED_SUPPORT_HITS[r"\bbye\b"])
            | set(EXPECTED_SUPPORT_HITS[r"\bpassword\b"])
        )
    )
    for message_id in new_hit_ids:
        if message_id not in IRRELEVANT_CLASSIFICATION:
            raise AssertionError(f"new creator hit {message_id} lacks a classification")

    oracle = direct_password_check()
    if oracle["grand_total_hits"] != 0:
        raise AssertionError("unexpected direct-password hit; stop and inspect")

    selection_found = any(
        message_id not in IRRELEVANT_CLASSIFICATION for message_id in new_hit_ids
    )

    return {
        "two_corpus_creator_search": {
            "solver_hits": solver_hits,
            "support_hits": support_hits,
            "already_established": {
                "solver_ciao_signoffs": EXPECTED_SOLVER_HITS[r"\bciao\b"],
                "solver_yingyang_mentions": (9599, 39224),
            },
            "new_hits_this_phase": tuple(
                {
                    "message_id": message_id,
                    "corpus": "solver" if message_id in texts else "support",
                    "text": texts.get(message_id) or support_texts.get(message_id),
                    "classification": IRRELEVANT_CLASSIFICATION[message_id],
                }
                for message_id in new_hit_ids
            ),
            "support_corpus_adds_no_ciao_or_yinyang_mention": True,
            "creator_selection_found": selection_found,
        },
        "coverage_census": COVERAGE,
        "cosmic_sweep_phase2_blob_scope": COSMIC_SWEEP_BLOBS_AT_PHASE2,
        "bounded_direct_password_check": oracle,
        "not_run_this_phase": (
            "song-lyric indexing under [23,16,7]: no creator instruction binds "
            "those indices to Bella Ciao, unlike the macro's literal "
            "lastwordsbeforearchichoice binding to the Architect text",
            "autokey/chain-addition seeding with these candidates: requires a "
            "frozen algorithm and normalization first, not attempted here",
            "checkerboard-keyword route against P32TRAILING/URLBLOB for "
            "ciaobella/ciaobellao: Phase 2's cosmic_sweep only covered "
            "SALPH+COSMIC; this residual gap is flagged, not closed, here",
        ),
        "gates": {
            "creator_selected_ciao_or_bye_as_yinyang": False,
            "any_bounded_candidate_opens_a_tracked_blob": False,
        },
        "promoted": False,
        "verdict": (
            "Neither creator corpus contains a message selecting CIAO or BYE as "
            "the yin-yang recognition state; the support-group export adds no "
            "new ciao/bella/yinyang signal. ciaobella/ciaobellao were already "
            "tested as checkerboard keywords (0 hits, SALPH+COSMIC only); ciao, "
            "bella, obellaciao, and bellaciao had no prior test coverage at all. "
            "The newly-run bounded direct-password check closes that specific "
            "gap for all five candidates against all four tracked blobs: 0 hits. "
            "Autokey/chain-addition seeding and P32TRAILING/URLBLOB checkerboard "
            "coverage remain open but are not launched without a frozen design."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR, support_result=SUPPORT_RESULT):
    report = audit(export_dir, support_result)
    assert report["two_corpus_creator_search"]["support_corpus_adds_no_ciao_or_yinyang_mention"]
    assert not report["two_corpus_creator_search"]["creator_selection_found"]
    assert len(report["two_corpus_creator_search"]["new_hits_this_phase"]) == 4
    assert report["coverage_census"]["ciaobellao"]["checkerboard_keyword_pad28"]
    assert not report["coverage_census"]["ciao"]["checkerboard_keyword_pad28"]
    assert not report["coverage_census"]["obellaciao"]["checkerboard_keyword_pad28"]
    for candidate in CANDIDATES:
        assert not report["coverage_census"][candidate]["direct_blob_password"]
    assert report["bounded_direct_password_check"]["grand_total_hits"] == 0
    assert report["bounded_direct_password_check"]["blob_count"] == 4
    assert len(report["not_run_this_phase"]) == 3
    assert not report["promoted"]
    print(json.dumps(report, indent=2, default=list))
    print("[*] self-test OK: two-corpus creator search negative, coverage census pinned, bounded oracle negative")
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
