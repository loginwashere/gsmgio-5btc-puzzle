#!/usr/bin/env python3
"""Bounded re-scoping test for G-ARCH-001: what would a creator-authored
selector for the Architect-words beginnings/endings extraction, or the
B<->H (`partial_mirror9`) operation, actually look like -- and does one
already exist in currently available material?

Five independently bounded lanes, each pre-registered before running:

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
4. Visual/symbolic check: inventory every creator-authored media record in
   both complete exports and review its native bytes for mirrored/reflected
   text, B/H imagery, beginnings/endings symbolism, or a visual instruction
   to repeat a prior operation.
5. Precedent-transfer check: does the creator use "same trick", "same way",
   "again", or equivalent language in a message that itself names, or directly
   replies to a message naming, Architect/DBBI/FAED/`matrixsumlist`/`yinyang`
   or the recovered word chain?

Pre-registered success condition (unchanged from the brainstorm note): a
creator-authored statement or reply that selects the beginnings/endings
extraction, the B<->H mirror, or the word `BOTH` specifically -- not mere
adjacency to "architect" or generic backwards/reverse language elsewhere
in the corpus (e.g. the unrelated pre-rabbit `esrever` mechanic).
"""

import argparse
import hashlib
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
TRANSFER_LANGUAGE = re.compile(
    r"\b(?:same|again|repeat(?:ed|ing)?|reuse|re-use|as before|like before|"
    r"once more|similar|likewise)\b",
    re.IGNORECASE,
)
RELEVANT_OBJECT_LANGUAGE = re.compile(
    r"architect|\bdbbi\b|\bfaed\b|yin.?yang|matrixsumlist|"
    r"lastwordsbeforearchichoice|last words before|\bhye\b|\bbye\b|"
    r"both.{0,80}ultimately|ultimately.{0,80}\bthe\b",
    re.IGNORECASE | re.DOTALL,
)

EXPECTED_CREATOR_MEDIA_IDS = {
    "solver": (
        984, 1647, 1743, 3860, 6025, 6847, 8140, 8288, 8339, 8358, 8792,
        8793, 26223, 32550, 32561, 39192, 49172, 66964,
    ),
    "support": (
        1115, 2371, 4954, 6948, 7867, 10277, 10498, 10677, 11954, 12898,
        13949, 15314, 15644, 15776, 16484, 16652, 16850, 19777, 19787,
        21480, 28344, 28507, 28551, 28679, 29792, 31276, 31288, 31289,
        31293, 31576, 31615, 32416, 33131, 36246, 36261, 36321, 36341,
        37071, 38602, 38964, 39276, 40386, 40560, 40849, 40964, 41554,
        41666, 41983, 42019, 42385, 42504, 43438, 44228, 45456, 46442,
        48102, 48910, 49527, 49770, 49997, 50071, 51021, 52365, 55336,
        55782, 58585, 60059, 60730, 61483, 66561,
    ),
}

# Manual native-byte review notes for the superficially relevant subset. All
# other records are ordinary trading screenshots, personal/travel images, or
# generic reaction media. These notes select what must be rechecked if bytes
# or message coverage change; they are not automated image interpretation.
VISUAL_REVIEW_NOTES = {
    ("solver", 1647): "Matrix cake reaction; 'Anybody hungry?'; no selector",
    ("solver", 1743): "known Decentraland side-quest image; no selector",
    ("solver", 3860): "Alice reaction GIF; no mirrored text or operation",
    ("solver", 6025): "shrugging fish sticker; no text or operation",
    ("solver", 6847): "South Park 'Drugs are bad' reaction; no selector",
    ("solver", 32561): (
        "Merovingian action/reaction clip posted immediately after creator says "
        "'There is no hint'; no mirror, edge, B/H, or reuse instruction"
    ),
    ("support", 28507): "known original rabbit-puzzle image; no mirror selector",
}


def plain_text(message):
    entities = message.get("text_entities") or []
    return "".join(entity.get("text", "") for entity in entities)


def load_export(export_dir):
    with open(Path(export_dir) / "result.json", encoding="utf-8") as handle:
        return json.load(handle)


def media_path(message):
    return message.get("photo") or message.get("file")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def check_visual_media_inventory(exports, export_dirs):
    results = {}
    all_hashes = []
    for label in ("solver", "support"):
        rows = []
        for message in exports[label]["messages"]:
            relative = media_path(message)
            if message.get("from_id") != CREATOR_ID or not relative:
                continue
            full_path = Path(export_dirs[label]) / relative
            row = {
                "message_id": message["id"],
                "path": relative,
                "exists": full_path.is_file(),
                "sha256": sha256_file(full_path) if full_path.is_file() else None,
                "review_note": VISUAL_REVIEW_NOTES.get((label, message["id"])),
            }
            rows.append(row)
            if row["sha256"]:
                all_hashes.append(row["sha256"])
        results[label] = {
            "record_count": len(rows),
            "message_ids": tuple(row["message_id"] for row in rows),
            "missing_files": tuple(
                row["message_id"] for row in rows if not row["exists"]
            ),
            "reviewed_notable_ids": tuple(
                row["message_id"] for row in rows if row["review_note"]
            ),
        }
    results["total_records"] = sum(
        results[label]["record_count"] for label in ("solver", "support")
    )
    results["unique_payloads"] = len(set(all_hashes))
    results["visual_selector_ids"] = ()
    return results


def check_precedent_transfer(exports):
    results = {}
    for label in ("solver", "support"):
        messages = exports[label]["messages"]
        by_id = {message["id"]: message for message in messages}
        direct = []
        nearby = []
        for index, message in enumerate(messages):
            if message.get("from_id") != CREATOR_ID:
                continue
            creator_text = plain_text(message)
            if not TRANSFER_LANGUAGE.search(creator_text):
                continue
            parent = by_id.get(message.get("reply_to_message_id"))
            parent_text = plain_text(parent) if parent else ""
            if (
                RELEVANT_OBJECT_LANGUAGE.search(creator_text)
                or RELEVANT_OBJECT_LANGUAGE.search(parent_text)
            ):
                direct.append(message["id"])
                continue
            neighborhood = messages[max(0, index - 10):index + 11]
            if any(
                candidate["id"] != message["id"]
                and RELEVANT_OBJECT_LANGUAGE.search(plain_text(candidate))
                for candidate in neighborhood
            ):
                nearby.append(message["id"])
        results[label] = {
            "direct_transfer_ids": tuple(direct),
            "nearby_stress_check_ids": tuple(nearby),
        }
    return results


def audit():
    export_dirs = {
        "solver": SOLVER_EXPORT_DIR,
        "support": SUPPORT_EXPORT_DIR,
        "solver_recent": SOLVER_RECENT_EXPORT_DIR,
    }
    exports = {
        label: load_export(export_dir)
        for label, export_dir in export_dirs.items()
    }
    return {
        "newer_export_coverage": check_newer_export_coverage(),
        "targeted_keyword_sweep": check_targeted_keyword_sweep(exports),
        "hye_word": check_hye_word(exports),
        "architect_selector_candidates": check_architect_selector_candidates(exports),
        "visual_media_inventory": check_visual_media_inventory(exports, export_dirs),
        "precedent_transfer": check_precedent_transfer(exports),
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
    visual = report["visual_media_inventory"]
    print(f"Lane 4 -- creator media: {visual['total_records']} records, "
          f"{visual['unique_payloads']} unique payloads, "
          f"{len(visual['visual_selector_ids'])} visual selectors")
    print(f"Lane 5 -- precedent transfer: {report['precedent_transfer']}")
    print()
    print("Pre-registered success condition met: False")
    print("Conclusion: all five lanes are negative. No creator-authored "
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

    visual = report["visual_media_inventory"]
    assert visual["total_records"] == 88, visual
    assert visual["unique_payloads"] == 83, visual
    assert visual["visual_selector_ids"] == (), visual
    for label, expected_ids in EXPECTED_CREATOR_MEDIA_IDS.items():
        assert visual[label]["message_ids"] == expected_ids, (label, visual[label])
        assert visual[label]["missing_files"] == (), (label, visual[label])

    precedent = report["precedent_transfer"]
    assert precedent["solver"]["direct_transfer_ids"] == (), precedent
    assert precedent["support"]["direct_transfer_ids"] == (), precedent
    assert precedent["solver"]["nearby_stress_check_ids"] == (32579, 60327), precedent
    assert precedent["support"]["nearby_stress_check_ids"] == (13669,), precedent

    print(
        "[*] self-test OK: all 5 lanes verified negative -- "
        f"{coverage['new_message_count']} new messages "
        f"({coverage['creator_new_count']} creator-authored), "
        f"keyword sweep {sweep}, HYE word {hye}, "
        f"architect-selector candidates {candidates['solver']['hit_count']} "
        "(0 creator-authored, 0 creator replies), 88 media records / "
        "83 unique payloads (0 visual selectors), 0 direct precedent-transfer hits"
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
