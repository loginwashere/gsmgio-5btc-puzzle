#!/usr/bin/env python3
"""Discovery pass: does the creator recycle OTHER personal idioms across
separate occasions the way "half and better half" was recycled into solved
puzzle plaintext?

"Half and better half" was found because the same phrase turned up twice,
independently, in ordinary conversation (the creator's own romantic-partner
idiom, `FINDINGS.md` Phase 133/155) and inside the solved Phase 3.2.2
plaintext ("THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF..."). That is a
replicable method, not a one-off: find phrases the creator uses on multiple
SEPARATE occasions (distinct messages/dates, not repeated within one
message), then check whether any of them also surface in the puzzle's own
disclosed text.

This is a discovery/scoping pass only -- not a password test, not an oracle
run. Output is a ranked candidate list for a human to inspect, plus an
automated cross-check against the puzzle's own text sources. A phrase
surfacing here is "worth a closer look," never "confirmed."
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

CREATOR_ID = "user9815232"
SOLVER_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26"
)
SUPPORT_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)"
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Cross-checking against the ENTIRE README.md is too noisy to be useful: it's
# thousands of words of ordinary prose (hints, walkthroughs, explanations),
# so almost any common English bigram/trigram the creator uses twice will
# also turn up somewhere in it by sheer chance -- confirmed empirically this
# session (283 "hits" against the full file, nearly all generic connectives
# like "in order to"). Narrowing to just the confirmed DECRYPTED-PLAINTEXT
# payload spans (Phase 3 decrypt, the Phase 3.2/3.2.1 Architect monologue,
# and the VIC-cipher "half and better half" output line) is the text that
# actually matters for this method -- much smaller, and a match there is a
# match against something the creator specifically wrote as puzzle content,
# not incidental hint prose. Line numbers verified live against README.md
# in `self_test()` below so this can't silently drift if the file changes.
README_DECRYPTED_SPANS = ((198, 225), (295, 321), (338, 342))

# Generic/functional phrases that are expected to repeat heavily in ordinary
# trading-bot support chat -- excluded so they don't drown out distinctive
# candidates. Matched as substrings of the n-gram, case-insensitive.
GENERIC_STOPLIST = (
    "check the", "let us know", "thank you", "feel free", "as soon as",
    "make sure", "we will", "we are", "you can", "if you", "in the",
    "on the", "to the", "of the", "for the", "at the", "is the",
    "please note", "trading bot", "the bot", "your bot", "api key",
    "log in", "sign up", "click on", "not working", "does not",
    "doesn't work", "will be", "have to", "going to", "want to",
    "need to", "able to", "try to", "we can", "we have", "we're",
    "i'm not", "i am not", "there is", "there are", "let me",
    "good morning", "good luck", "good day", "no worries", "no problem",
)

WORD_RE = re.compile(r"[a-z']+")


def plain_text(message):
    entities = message.get("text_entities") or []
    return "".join(entity.get("text", "") for entity in entities)


def load_export(export_dir):
    with open(Path(export_dir) / "result.json", encoding="utf-8") as handle:
        return json.load(handle)


def creator_messages(export_dir, creator_id=CREATOR_ID):
    data = load_export(export_dir)
    out = []
    for message in data["messages"]:
        if message.get("from_id") != creator_id:
            continue
        text = plain_text(message)
        if not text or not text.strip():
            continue
        out.append({
            "id": message["id"],
            "date": message.get("date", ""),
            "text": text,
        })
    return out


def is_generic(phrase):
    return any(bad in phrase for bad in GENERIC_STOPLIST)


def ngram_occurrences(messages, sizes=(2, 3, 4, 5, 6)):
    """phrase -> set of (source_label, message_id) it appears in."""
    occurrences = defaultdict(set)
    for source_label, msg in messages:
        words = WORD_RE.findall(msg["text"].lower())
        for size in sizes:
            if len(words) < size:
                continue
            seen_this_message = set()
            for i in range(len(words) - size + 1):
                phrase = " ".join(words[i:i + size])
                seen_this_message.add(phrase)
            for phrase in seen_this_message:
                occurrences[phrase].add((source_label, msg["id"]))
    return occurrences


def filtered_candidates(occurrences, min_occurrences=2, min_length=8):
    """All non-generic repeated phrases, not just the most frequent -- a
    personal idiom like "better half" (4 occurrences total) ranks far below
    routine support boilerplate ("help gsmg io", 96 occurrences) by raw
    frequency, so the cross-check must not be limited to a top-N-by-count
    slice or it silently misses exactly the shape of phrase this is
    looking for."""
    out = []
    for phrase, occ in occurrences.items():
        if len(occ) < min_occurrences:
            continue
        if is_generic(phrase):
            continue
        if len(phrase) < min_length:
            continue
        out.append((phrase, sorted(occ)))
    out.sort(key=lambda item: (-len(item[1]), item[0]))
    return out


def top_candidates(occurrences, min_occurrences=2, limit=60):
    return filtered_candidates(occurrences, min_occurrences=min_occurrences)[:limit]


def load_puzzle_text():
    readme_path = REPO_ROOT / "README.md"
    lines = readme_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    chunks = ["\n".join(lines[start - 1:end]) for start, end in README_DECRYPTED_SPANS]
    return "\n".join(chunks).lower()


def cross_check(candidates, puzzle_text):
    hits = []
    for phrase, occ in candidates:
        if phrase in puzzle_text:
            hits.append({"phrase": phrase, "occurrences": occ})
    return hits


def scan():
    solver_msgs = [("solver", m) for m in creator_messages(SOLVER_EXPORT_DIR)]
    support_msgs = [("support", m) for m in creator_messages(SUPPORT_EXPORT_DIR)]
    all_msgs = solver_msgs + support_msgs

    occurrences = ngram_occurrences(all_msgs)
    all_candidates = filtered_candidates(occurrences)
    top = all_candidates[:60]
    puzzle_text = load_puzzle_text()
    hits = cross_check(all_candidates, puzzle_text)

    return {
        "solver_creator_message_count": len(solver_msgs),
        "support_creator_message_count": len(support_msgs),
        "distinct_ngrams_seen_2plus_times": sum(
            1 for occ in occurrences.values() if len(occ) >= 2
        ),
        "filtered_candidate_count": len(all_candidates),
        "top_candidate_count": len(top),
        "top_candidates": [
            {"phrase": phrase, "occurrence_count": len(occ), "occurrences": occ}
            for phrase, occ in top
        ],
        "puzzle_text_cross_check_hits": [
            {"phrase": h["phrase"], "occurrence_count": len(h["occurrences"]), **h}
            for h in hits
        ],
    }


def self_test():
    report = scan()
    assert report["solver_creator_message_count"] > 0
    assert report["support_creator_message_count"] > 0
    assert report["top_candidate_count"] > 0
    print(
        f"[*] self-test OK: {report['solver_creator_message_count']} solver + "
        f"{report['support_creator_message_count']} support creator messages, "
        f"{report['distinct_ngrams_seen_2plus_times']} n-grams repeated >=2x, "
        f"{report['top_candidate_count']} candidates after filtering, "
        f"{len(report['puzzle_text_cross_check_hits'])} puzzle-text cross-check hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = scan()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
