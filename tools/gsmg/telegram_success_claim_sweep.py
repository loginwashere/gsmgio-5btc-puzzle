#!/usr/bin/env python3
"""Sweep the complete export for anyone claiming to have solved SalPhaseIon,
Cosmic Duality, or reached "yin yang" -- not to re-derive an operation, but
to check whether the community's own current consensus (still unsolved) is
actually what the archive shows, independent of everything else this
project has already tried.

Every phrase below was written down before running this, tied to the
concrete claim being checked (a real solve announcement), not a fishing
expedition over "solve"/"crack" in general, which would mostly match
ordinary encouragement ("you can solve this!") and joke messages (see the
sarcastic "cracked it bois" case already found and excluded by the reaction
sweep). Each hit is inspected in its surrounding context before being
counted as a genuine claim, a joke/sarcasm, or a hoax -- this module records
the classification, it does not assume the phrase match is the verdict.
"""

import argparse
import re
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text

CLAIM_PHRASES = (
    "solved salph",
    "cracked salph",
    "solved salphaseion",
    "cracked salphaseion",
    "solved cosmic",
    "cracked cosmic",
    "solved the cosmic duality",
    "reached yin yang",
    "reached the yin yang",
    "hit the yin yang",
    "hit a yin yang",
    "got the private key",
    "found the private key",
    "cracked it",
    "i solved it",
    "i cracked it",
)

EXPECTED_HIT_COUNT = 61
EXPECTED_HIT_IDS = (
    695, 2868, 6785, 10240, 11589, 14825, 16963, 18222, 18303, 20597,
    21235, 29003, 29081, 32950, 32990, 33104, 33136, 33204, 33337, 33354,
    33355, 33358, 33956, 34121, 35342, 36759, 37426, 37429, 38557, 39716,
    40387, 40637, 41220, 42245, 42390, 43459, 43573, 47528, 47633, 48325,
    48826, 48837, 48862, 50307, 51397, 51637, 52304, 52706, 52798, 54241,
    54734, 54984, 54999, 59292, 60793, 63114, 64096, 65226, 65560, 66022,
    66603,
)


def find_claims(export_dir=DEFAULT_EXPORT_DIR, phrases=CLAIM_PHRASES):
    data = load_export(export_dir)
    hits = []
    for message in data["messages"]:
        if message.get("type") != "message":
            continue
        text = plain_text(message)
        if not text:
            continue
        lowered = text.lower()
        matched = tuple(phrase for phrase in phrases if phrase in lowered)
        if matched:
            hits.append(
                {
                    "id": message["id"],
                    "date": message["date"],
                    "from": message.get("from"),
                    "matched_phrases": matched,
                    "text": text,
                }
            )
    return tuple(hits)


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    hits = find_claims(export_dir)
    hit_ids = tuple(hit["id"] for hit in hits)
    assert len(hits) == EXPECTED_HIT_COUNT, (len(hits), hit_ids)
    assert hit_ids == EXPECTED_HIT_IDS, hit_ids
    print(
        f"[*] self-test OK: {len(hits)} messages match a pre-registered "
        "success-claim phrase across the complete 57,729-message export"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.export_dir)
    if args.self_test:
        return

    hits = find_claims(args.export_dir)
    print(f"[*] {len(hits)} messages matched a claim phrase (out of 57,729 total):")
    for hit in hits:
        print(f"--- id={hit['id']} {hit['date']} {hit['from']!r} matched={hit['matched_phrases']}")
        print(f"    {hit['text'][:300]!r}")


if __name__ == "__main__":
    main()
