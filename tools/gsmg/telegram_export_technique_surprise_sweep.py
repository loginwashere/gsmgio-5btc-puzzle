#!/usr/bin/env python3
"""Token-aware Telegram sweep for technique-plus-surprise discussions.

This is a separate, pre-declared axis from ``telegram_export_keyword_sweep``:
the old list names puzzle objects, while this list targets messages that both
name a cryptographic technique and discuss how surprising a result is.  The
intersection is intentionally the primary review set; technique-only and
surprise-only counts are retained as calibration context.
"""

import argparse
import json
import re
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


TECHNIQUES = (
    "bifid", "trifid", "playfair", "vigenere", "atbash", "vernam",
    "xor", "wif", "bip38", "mnemonic", "checksum", "bazeries",
    "polybius", "nihilist", "aes", "sha256", "base58", "bip39",
)
SURPRISE = (
    "odds", "1 in", "probability", "unlikely", "coincidence", "random",
    "chance", "can't make this", "cannot make this", "red herring",
    "anomaly", "surprising",
)


def token_match(text, term):
    return re.search(
        rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text, re.IGNORECASE
    ) is not None


def matched(text, terms):
    return tuple(term for term in terms if token_match(text, term))


def sweep(data):
    technique_hits = []
    surprise_hits = []
    intersection = []
    for message in data["messages"]:
        if message.get("type") != "message":
            continue
        text = plain_text(message)
        technique_terms = matched(text, TECHNIQUES)
        surprise_terms = matched(text, SURPRISE)
        if not technique_terms and not surprise_terms:
            continue
        row = {
            "id": message["id"],
            "date": message.get("date"),
            "date_unixtime": int(message["date_unixtime"]),
            "from": message.get("from"),
            "technique_terms": technique_terms,
            "surprise_terms": surprise_terms,
            "text": text,
        }
        if technique_terms:
            technique_hits.append(row)
        if surprise_terms:
            surprise_hits.append(row)
        if technique_terms and surprise_terms:
            intersection.append(row)
    return {
        "technique_hits": tuple(technique_hits),
        "surprise_hits": tuple(surprise_hits),
        "intersection": tuple(intersection),
    }


def audit(export_dir=DEFAULT_EXPORT_DIR):
    return sweep(load_export(export_dir))


def self_test():
    synthetic = {"messages": [
        {"id": 1, "type": "message", "date_unixtime": "1", "text_entities": [
            {"type": "plain", "text": "WIFi is random"}
        ]},
        {"id": 2, "type": "message", "date_unixtime": "2", "text_entities": [
            {"type": "plain", "text": "Bifid: what are the odds?"}
        ]},
        {"id": 3, "type": "message", "date_unixtime": "3", "text_entities": [
            {"type": "plain", "text": "XOR checksum"}
        ]},
    ]}
    report = sweep(synthetic)
    assert [row["id"] for row in report["intersection"]] == [2]
    assert [row["id"] for row in report["technique_hits"]] == [2, 3]
    # Token boundaries prevent WIF from matching the start of "WIFi".
    assert [row["id"] for row in report["surprise_hits"]] == [1, 2]
    print("[*] self-test OK: token boundaries and technique/surprise intersection")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit(args.export_dir)
    print(f"[*] technique hits: {len(report['technique_hits'])}")
    print(f"[*] surprise hits: {len(report['surprise_hits'])}")
    print(f"[*] intersection (primary review set): {len(report['intersection'])}")
    for row in report["intersection"]:
        print(
            f"    {row['id']} {row['date']} {row['from']!r} "
            f"technique={row['technique_terms']} surprise={row['surprise_terms']}"
        )
    if args.json_out:
        args.json_out.write_text(
            json.dumps(report["intersection"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
