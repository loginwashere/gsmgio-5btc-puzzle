#!/usr/bin/env python3
"""Provenance follow-up to `promised_standalone_audit.py` (Phase 109) and
brainstorm item 11 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md`).

Item 11 asks two things about `promised`, the macro clue's final,
still-unconsumed token: (1) has it been given an operational role anywhere
(closed negative in Phase 109 as a literal passphrase, and in Phases
151/152 via the Trinity-quote convergence -- KDF context and checkerboard
seed too), and (2) "check whether the creator ever explains, gets asked
about, or reuses the literal word `promised` elsewhere in the export" --
the same treatment `anstoo_provenance_audit.py` (Phase 102) gave `anstoo`.
That second half was still open. Phase 155 already checked the creator's
own usage across both corpora (2 unrelated hits, both ordinary trading-bot
language); this module completes the picture by reading every *community*
mention as well, the way Phase 102 read all 93 `anstoo` mentions rather
than just counting them.

Runs no cipher/transform/AES check -- pure text-provenance, following this
project's `\\bword\\b` convention (a naive substring scan over-counts:
"compromised" contains "promised").
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

CREATOR_ID = "user9815232"
WORD_RE = re.compile(r"\bpromised\b", re.IGNORECASE)

EXPORTS = {
    "puzzle_solvers": Path(
        "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26/result.json"
    ),
    "community": Path(
        "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)/result.json"
    ),
}

# The recycled macro-clue string itself, in any of its community-quoted
# spellings/spacings -- these mentions are just re-pasting the already-known
# creator artifact, not new theorizing about `promised` specifically.
MACRO_ECHO_MARKERS = ("yellowblueprime", "yellow blue prime")

# The two substantive, non-echo community readings found by this audit.
# Quoted and asserted against the live export, not paraphrased from memory.
NOTABLE_MESSAGE_IDS = {
    "puzzle_solvers": (30526, 48341),
}
EXPECTED_SNIPPETS = {
    30526: "Hell of a lot of give aways going on here",
    48341: "maybe the promise is not the give away meaning prize",
}


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_export(path):
    return json.loads(path.read_text(encoding="utf-8"))


def scan(payload):
    hits = []
    for message in payload["messages"]:
        text = flatten_text(message.get("text", ""))
        if WORD_RE.search(text):
            hits.append(message)
    return hits


def classify(hits):
    creator, macro_echo, other = [], [], []
    for m in hits:
        text = flatten_text(m.get("text", ""))
        if m.get("from_id") == CREATOR_ID:
            creator.append(m)
        elif any(marker in text.lower() for marker in MACRO_ECHO_MARKERS):
            macro_echo.append(m)
        else:
            other.append(m)
    return creator, macro_echo, other


def audit():
    report = {}
    for name, path in EXPORTS.items():
        payload = load_export(path)
        hits = scan(payload)
        creator, macro_echo, other = classify(hits)
        by_id = {m["id"]: m for m in payload["messages"]}
        notable = []
        for mid in NOTABLE_MESSAGE_IDS.get(name, ()):
            text = flatten_text(by_id[mid].get("text", ""))
            if EXPECTED_SNIPPETS[mid] not in text:
                raise AssertionError(f"message {mid} no longer contains expected snippet")
            notable.append({"id": mid, "text": text})
        report[name] = {
            "total_messages": len(payload["messages"]),
            "word_boundary_hits": len(hits),
            "creator_hits": len(creator),
            "macro_echo_hits": len(macro_echo),
            "other_hits": len(other),
            "notable": notable,
        }
    return report


def print_report(report):
    for name, data in report.items():
        print(f"[*] {name}: {data['total_messages']} messages")
        print(f"    'promised' (word-boundary) hits: {data['word_boundary_hits']}")
        print(f"    creator-authored: {data['creator_hits']}")
        print(f"    macro-clue-string echo (re-pasting the known artifact): {data['macro_echo_hits']}")
        print(f"    other (ordinary usage / unrelated): {data['other_hits']}")
        for item in data["notable"]:
            print(f"    notable [{item['id']}]: {item['text'][:200]!r}")
    print(
        "\n[*] verdict: the creator never engages with 'promised' as a "
        "keyword (0 puzzle-solvers mentions; 2 community mentions, both "
        "ordinary trading-bot language, already noted in Phase 155). "
        "Community usage is dominated by re-pasting the known macro-clue "
        "string verbatim. The one substantive theory on record (message "
        "48341, Pomyk) reads 'promised' as a colloquial grammatical tag on "
        "'a true giveaway' ('...is a true giveaway, promised' = an "
        "assurance, not a discrete keyword) rather than an independent "
        "8th token -- consistent with, not contradicted by, three separate "
        "negative oracle results (Phase 109 literal passphrase; Phase "
        "151/152 Trinity-quote KDF-context and checkerboard-seed roles). "
        "No new operational lever found; 'promised' most plausibly isn't "
        "a discrete instructional fragment at all."
    )


def self_test():
    report = audit()
    assert report["puzzle_solvers"]["creator_hits"] == 0
    assert report["community"]["creator_hits"] == 2
    assert len(report["puzzle_solvers"]["notable"]) == 2
    print("[*] self-test OK: creator-hit counts and notable messages verified live")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit()
    print_report(report)


if __name__ == "__main__":
    main()
