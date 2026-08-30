#!/usr/bin/env python3
"""Phase 450 -- oracle-free G-PRIME-001 consumer/selector sweep.

`G-PRIME-001` (`doc/GSMG_OPEN_GAP_REGISTRY.md`) is the exact but unconsumed
Roman-rail correspondence: DBBI/FAED's Roman-letter projections, prefixed
with the *Cosmic Duality* title's `C`, reproduce the fitted color-prime sums
`CDI=401` (blue) and `CD=400` (yellow) (`roman_rail_prime_sum_audit.py`).
No instruction or key consumes the three sums `401/400/73`, no clue selects
Roman-letter filtering or title `C` over the sibling configurations in the
disclosed bounded family, and FEFE's fitted sum `73` is unexplained.

This script does not re-derive 401/400/73 and does not invent a new decoder.
It runs two bounded checks pre-registered in
`doc/Brainstorms/2026-08-29 - Phase 450 G-PRIME-001 Consumer-Selector Sweep
Protocol.md`:

1. apply the exact winning rule (title `C` prefix, Roman-letter projection,
   no new choice) to FEFE itself, to see whether it reproduces `73`;
2. a fixed-keyword sweep of the complete Telegram export for messages
   containing all three standalone target numerals, both target Roman forms,
   or the phrase `roman numeral(s)`/`title initial`.
"""

import argparse
import json
import re
from pathlib import Path

from roman_rail_prime_sum_audit import (
    EXPECTED_FITTED_SUMS,
    apply_context,
    roman_projection,
)
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text

CREATOR_FROM_ID = "user9815232"

TARGET_NUMERALS = (401, 400, 73)
TARGET_ROMAN_FORMS = ("CDI", "CD")
PHRASE_KEYWORDS = ("roman numeral", "roman numerals", "title initial")

NUMBER_PATTERN = re.compile(r"(?<!\d)(401|400|73)(?!\d)")
ROMAN_TOKEN_PATTERN = re.compile(r"(?<![A-Za-z])(CDI|CD)(?![A-Za-z])")


def naive_fefe_extension():
    """Apply the exact winning rule (title `C` prefix) to FEFE, no new choice."""
    numeral, value = apply_context("FEFE", "prefix", "C")
    return {
        "token": "FEFE",
        "roman_projection": roman_projection("FEFE"),
        "numeral": numeral,
        "value": value,
        "target": EXPECTED_FITTED_SUMS["F"],
        "matches_target": value == EXPECTED_FITTED_SUMS["F"],
    }


def has_all_target_numerals(text):
    return {int(value) for value in NUMBER_PATTERN.findall(text)} >= set(TARGET_NUMERALS)


def has_both_roman_forms(text):
    return set(ROMAN_TOKEN_PATTERN.findall(text)) >= set(TARGET_ROMAN_FORMS)


def matched_phrases(text):
    lowered = text.lower()
    return tuple(phrase for phrase in PHRASE_KEYWORDS if phrase in lowered)


def corpus_sweep(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    messages = tuple(m for m in data["messages"] if m.get("type") == "message")
    by_id = {message["id"]: message for message in messages}

    numeral_hits, roman_hits, phrase_hits = [], [], []
    for message in messages:
        text = plain_text(message)
        if not text:
            continue
        base = {
            "id": message["id"],
            "date": message.get("date"),
            "from": message.get("from"),
            "from_id": message.get("from_id"),
            "text": text,
        }
        if has_all_target_numerals(text):
            numeral_hits.append(dict(base))
        if has_both_roman_forms(text):
            roman_hits.append(dict(base))
        phrases = matched_phrases(text)
        if phrases:
            phrase_hits.append({**base, "matched_phrases": phrases})

    def with_creator_status(hit):
        children = tuple(
            message for message in messages
            if message.get("reply_to_message_id") == hit["id"]
        )
        return {
            **hit,
            "is_creator": hit.get("from_id") == CREATOR_FROM_ID,
            "has_creator_reply": any(
                child.get("from_id") == CREATOR_FROM_ID for child in children
            ),
        }

    return {
        "message_count": len(messages),
        "numeral_hits": tuple(with_creator_status(hit) for hit in numeral_hits),
        "roman_hits": tuple(with_creator_status(hit) for hit in roman_hits),
        "phrase_hits": tuple(with_creator_status(hit) for hit in phrase_hits),
    }


def _licenses_gate(hit):
    """A hit can only license a gate if creator-authored or creator-endorsed."""
    return hit["is_creator"] or hit["has_creator_reply"]


def audit(export_dir=DEFAULT_EXPORT_DIR):
    fefe = naive_fefe_extension()
    corpus = corpus_sweep(export_dir)

    consumer_found = any(_licenses_gate(hit) for hit in corpus["numeral_hits"])
    selector_found = any(_licenses_gate(hit) for hit in corpus["roman_hits"]) or any(
        _licenses_gate(hit) for hit in corpus["phrase_hits"]
    )
    fefe_explained = fefe["matches_target"]

    if consumer_found:
        verdict = "consumer_found"
    elif selector_found:
        verdict = "selector_found"
    elif fefe_explained:
        verdict = "fefe_explained"
    else:
        verdict = "remains_unconsumed"

    return {
        "fefe_naive_extension": fefe,
        "corpus": corpus,
        "consumer_found": consumer_found,
        "selector_found": selector_found,
        "fefe_explained": fefe_explained,
        "verdict": verdict,
    }


def self_test():
    fefe = naive_fefe_extension()
    assert fefe["roman_projection"] == ""
    assert fefe["numeral"] == "C"
    assert fefe["value"] == 100
    assert fefe["target"] == 73
    assert fefe["matches_target"] is False

    synthetic = {
        "messages": [
            {"id": 1, "type": "message", "date": "2020-01-01T00:00:00",
             "from": "Nobody", "from_id": "userX",
             "text_entities": [{"type": "plain", "text": "just chatting"}]},
            {"id": 2, "type": "message", "date": "2020-01-01T00:00:01",
             "from": "Denis Golovkin", "from_id": CREATOR_FROM_ID,
             "text_entities": [{"type": "plain",
                                 "text": "sum 401 and 400 and 73 together"}]},
            {"id": 3, "type": "message", "date": "2020-01-01T00:00:02",
             "from": "Someone Else", "from_id": "userY",
             "text_entities": [{"type": "plain",
                                 "text": "CDI is 401 and CD is 400, curious"}]},
            {"id": 4, "type": "message", "date": "2020-01-01T00:00:03",
             "from": "Someone Else", "from_id": "userY",
             "text_entities": [{"type": "plain",
                                 "text": "what about roman numerals here"}]},
            {"id": 5, "type": "message", "date": "2020-01-01T00:00:04",
             "from": "Nobody", "from_id": "userX",
             "text_entities": [{"type": "plain", "text": "cd into the dir, 2400 is unrelated"}]},
        ]
    }
    export_path = _write_synthetic(synthetic)
    try:
        corpus = corpus_sweep(export_path.parent)
        result = audit(export_path.parent)
    finally:
        export_path.unlink()
        export_path.parent.rmdir()

    assert corpus["message_count"] == 5
    assert [hit["id"] for hit in corpus["numeral_hits"]] == [2]
    assert corpus["numeral_hits"][0]["is_creator"] is True
    assert [hit["id"] for hit in corpus["roman_hits"]] == [3]
    assert corpus["roman_hits"][0]["is_creator"] is False
    assert corpus["roman_hits"][0]["has_creator_reply"] is False
    assert [hit["id"] for hit in corpus["phrase_hits"]] == [4]

    assert result["verdict"] == "consumer_found"
    assert result["consumer_found"] is True
    assert result["selector_found"] is False
    assert result["fefe_explained"] is False
    print(
        "[*] self-test OK: FEFE under the winning rule gives C=100, not 73; "
        "synthetic corpus sweep correctly isolates standalone-triple, "
        "roman-form, and phrase hits and gates them on creator authorship"
    )
    return result


def _write_synthetic(payload):
    import tempfile
    directory = Path(tempfile.mkdtemp())
    path = directory / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    report = audit(args.export_dir)
    fefe = report["fefe_naive_extension"]
    print(
        f"[*] naive FEFE extension: roman({fefe['token']!r})="
        f"{fefe['roman_projection']!r} -> C+..={fefe['numeral']!r}="
        f"{fefe['value']} (target {fefe['target']}, "
        f"matches={fefe['matches_target']})"
    )
    corpus = report["corpus"]
    print(
        f"[*] corpus: {corpus['message_count']} messages; "
        f"{len(corpus['numeral_hits'])} standalone-triple hits, "
        f"{len(corpus['roman_hits'])} roman-form hits, "
        f"{len(corpus['phrase_hits'])} phrase hits"
    )
    for label, hits in (
        ("numeral", corpus["numeral_hits"]),
        ("roman", corpus["roman_hits"]),
        ("phrase", corpus["phrase_hits"]),
    ):
        for hit in hits:
            print(
                f"    [{label}] id={hit['id']} {hit['date']} {hit['from']!r} "
                f"creator={hit['is_creator']} creator_reply={hit['has_creator_reply']}"
            )
            print(f"        {hit['text'][:300]!r}")
    print(f"[*] verdict: {report['verdict']}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, default=list)
        print(f"\n[*] full report written to {args.json_out}")


if __name__ == "__main__":
    main()
