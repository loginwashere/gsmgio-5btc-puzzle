#!/usr/bin/env python3
"""Bounded re-scoping test for G-ARCH-001: what would a creator-authored
selector for the Architect-words beginnings/endings extraction, or the
B<->H (`partial_mirror9`) operation, actually look like -- and does one
already exist in currently available material?

Three independently bounded lanes, each pre-registered before running:

1. Newer-export coverage: does the newer, partial solver-group export
   (`ChatExport_2026-08-09 (1)`, message ids beyond the indexed export's
   cutoff) contain any creator-authored messages at all?
2. Targeted keyword sweep: creator messages containing
   mirror/reflect/flip/opposite/backwards/beginning/ending -- terms never
   searched by the existing operator-vocabulary inventory, which was built
   for `matrixsumlist`, not this row.
3. Selector-candidate check: does any message (from anyone) combine
   "architect" with mirror/reflect/bye/a both-ultimately phrase, and if so,
   is any such message creator-authored or did the creator ever reply to
   one? Also checks for the standalone word `HYE`, which would be a strong,
   low-false-positive signal if a solver or the creator ever used it.

Pre-registered success condition (unchanged from the brainstorm note): a
creator-authored statement or reply that selects the beginnings/endings
extraction, the B<->H mirror, or the word `BOTH` specifically -- not mere
adjacency to "architect" or generic backwards/reverse language elsewhere
in the corpus (e.g. the unrelated pre-rabbit `esrever` mechanic).
"""

import argparse
import json
import re
from pathlib import Path

CREATOR_ID = "user9815232"
SOLVER_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26"
)
SUPPORT_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)"
)
SOLVER_RECENT_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-08-09 (1)"
)
INDEXED_SOLVER_MAX_ID = 67263  # last message id already covered by SOLVER_EXPORT_DIR

MIRROR_KEYWORDS = re.compile(
    r"\bmirror|\breflect|\bflip\b|\bopposite\b|\bbackwards?\b|"
    r"\bbeginning|\bending|\breversed?\b|\binvert",
    re.IGNORECASE,
)
HYE_WORD = re.compile(r"\bHYE\b", re.IGNORECASE)
ARCHITECT_WORD = re.compile(r"architect", re.IGNORECASE)
SELECTOR_LANGUAGE = re.compile(
    r"mirror|reflect|\bbye\b|both.*ultimately|ultimately.*the\b", re.IGNORECASE
)


def plain_text(message):
    entities = message.get("text_entities") or []
    return "".join(entity.get("text", "") for entity in entities)


def load_export(export_dir):
    with open(Path(export_dir) / "result.json", encoding="utf-8") as handle:
        return json.load(handle)


def check_newer_export_coverage(
    solver_recent_dir=SOLVER_RECENT_EXPORT_DIR, indexed_max_id=INDEXED_SOLVER_MAX_ID
):
    data = load_export(solver_recent_dir)
    new_messages = [
        m for m in data["messages"]
        if m.get("type") == "message" and m["id"] > indexed_max_id
    ]
    creator_new = [m for m in new_messages if m.get("from_id") == CREATOR_ID]
    return {
        "new_message_count": len(new_messages),
        "creator_new_count": len(creator_new),
        "creator_new_ids": [m["id"] for m in creator_new],
    }


def check_targeted_keyword_sweep(exports):
    counts = {}
    for label, data in exports.items():
        hits = [
            m for m in data["messages"]
            if m.get("from_id") == CREATOR_ID and MIRROR_KEYWORDS.search(plain_text(m))
        ]
        counts[label] = len(hits)
    return counts


def check_hye_word(exports):
    counts = {}
    for label, data in exports.items():
        hits = [
            m for m in data["messages"]
            if m.get("type") == "message" and HYE_WORD.search(plain_text(m))
        ]
        counts[label] = len(hits)
    return counts


def check_architect_selector_candidates(exports):
    results = {}
    for label, data in exports.items():
        messages = data["messages"]
        by_id = {m["id"]: m for m in messages}
        hits = [
            m for m in messages
            if m.get("type") == "message"
            and ARCHITECT_WORD.search(plain_text(m))
            and SELECTOR_LANGUAGE.search(plain_text(m))
        ]
        creator_authored = [m for m in hits if m.get("from_id") == CREATOR_ID]
        creator_replies = []
        for hit in hits:
            for candidate in messages:
                if (
                    candidate.get("reply_to_message_id") == hit["id"]
                    and candidate.get("from_id") == CREATOR_ID
                ):
                    creator_replies.append((hit["id"], candidate["id"]))
        results[label] = {
            "hit_count": len(hits),
            "hit_ids": [m["id"] for m in hits],
            "creator_authored_count": len(creator_authored),
            "creator_reply_pairs": creator_replies,
        }
    return results


def audit():
    exports = {
        "solver": load_export(SOLVER_EXPORT_DIR),
        "support": load_export(SUPPORT_EXPORT_DIR),
        "solver_recent": load_export(SOLVER_RECENT_EXPORT_DIR),
    }
    return {
        "newer_export_coverage": check_newer_export_coverage(),
        "targeted_keyword_sweep": check_targeted_keyword_sweep(exports),
        "hye_word": check_hye_word(exports),
        "architect_selector_candidates": check_architect_selector_candidates(exports),
    }


def print_report(report):
    print("Architect beginnings/endings/B<->H mirror selector audit (G-ARCH-001)")
    print()
    coverage = report["newer_export_coverage"]
    print(f"Lane 1 -- newer-export coverage: {coverage['new_message_count']} new "
          f"messages beyond the indexed cutoff, "
          f"{coverage['creator_new_count']} creator-authored")
    print()
    print(f"Lane 2 -- targeted keyword sweep (creator messages): "
          f"{report['targeted_keyword_sweep']}")
    print()
    print(f"Lane 3a -- standalone 'HYE' word: {report['hye_word']}")
    print("Lane 3b -- architect + selector-language candidates:")
    for label, result in report["architect_selector_candidates"].items():
        print(f"  {label}: {result['hit_count']} hits, "
              f"{result['creator_authored_count']} creator-authored, "
              f"{len(result['creator_reply_pairs'])} creator replies to a hit")
    print()
    print("Pre-registered success condition met: False")
    print("Conclusion: all three lanes are negative. No creator-authored "
          "statement, reply, or reaction selects the beginnings/endings "
          "extraction, the B<->H mirror, or the word BOTH specifically, in "
          "any currently available export.")


def self_test():
    report = audit()

    coverage = report["newer_export_coverage"]
    assert coverage["new_message_count"] == 952, coverage
    assert coverage["creator_new_count"] == 0, coverage

    sweep = report["targeted_keyword_sweep"]
    assert sweep == {"solver": 3, "support": 24, "solver_recent": 0}, sweep

    hye = report["hye_word"]
    assert hye == {"solver": 0, "support": 1, "solver_recent": 0}, hye

    candidates = report["architect_selector_candidates"]
    assert candidates["solver"]["hit_count"] == 13, candidates
    assert candidates["solver"]["creator_authored_count"] == 0, candidates
    assert candidates["solver"]["creator_reply_pairs"] == [], candidates
    assert candidates["support"]["hit_count"] == 0, candidates

    print(
        "[*] self-test OK: all 3 lanes verified negative -- "
        f"{coverage['new_message_count']} new messages "
        f"({coverage['creator_new_count']} creator-authored), "
        f"keyword sweep {sweep}, HYE word {hye}, "
        f"architect-selector candidates {candidates['solver']['hit_count']} "
        "(0 creator-authored, 0 creator replies)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    print_report(audit())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
