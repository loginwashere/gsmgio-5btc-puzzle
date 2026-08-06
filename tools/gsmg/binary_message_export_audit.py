#!/usr/bin/env python3
"""Reproduce the full-export audit for raw binary message payloads."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR

CREATOR_ID = "user9815232"
MIN_BITS = 40
EXPECTED_HIT_COUNT = 25
EXPECTED_CREATOR_IDS = (8446, 53342)
EXPECTED_MESSAGE_IDS = (
    8446,
    15851,
    19126,
    21404,
    21405,
    22084,
    22085,
    26565,
    28024,
    28808,
    31640,
    32447,
    34003,
    45917,
    46923,
    46924,
    50990,
    53342,
    53646,
    57106,
    58401,
    59032,
    59035,
    59738,
    59739,
)
EXPECTED_NEW_YEAR_TEXT = (
    "Happy new year! Make the best of everything. Oh, and here's a "
    '"tiny hint" <3.'
)


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def binary_payload(text):
    compact = "".join(text.split())
    if len(compact) < MIN_BITS or not set(compact) <= {"0", "1"}:
        return None
    return compact


def decode_bytes(bits):
    if len(bits) % 8:
        return None
    return int(bits, 2).to_bytes(len(bits) // 8, "big")


def payload_digest(bits):
    return hashlib.sha256(bits.encode("ascii")).hexdigest()


def audit(export_path=DEFAULT_EXPORT_DIR):
    payload = json.loads(
        (Path(export_path) / "result.json").read_text(encoding="utf-8")
    )
    hits = []
    for message in payload["messages"]:
        bits = binary_payload(flatten_text(message.get("text", "")))
        if bits is None:
            continue
        hits.append(
            {
                "id": message["id"],
                "from_id": message.get("from_id"),
                "bit_length": len(bits),
                "bits": bits,
                "payload_sha256": payload_digest(bits),
            }
        )

    creator_hits = [hit for hit in hits if hit["from_id"] == CREATOR_ID]
    creator_by_id = {hit["id"]: hit for hit in creator_hits}
    macro_digest = creator_by_id[8446]["payload_sha256"]
    new_year_digest = creator_by_id[53342]["payload_sha256"]
    digest_counts = Counter(hit["payload_sha256"] for hit in hits)

    inventory = []
    for hit in hits:
        if hit["id"] == 8446:
            category = "creator_macro"
        elif hit["id"] == 53342:
            category = "creator_new_year"
        elif hit["payload_sha256"] == macro_digest:
            category = "repost_of_creator_macro"
        elif hit["payload_sha256"] == new_year_digest:
            category = "repost_of_creator_new_year"
        elif digest_counts[hit["payload_sha256"]] > 1:
            category = "repeated_noncreator"
        else:
            category = "unique_noncreator"
        inventory.append(
            {
                "id": hit["id"],
                "from_id": hit["from_id"],
                "bit_length": hit["bit_length"],
                "payload_sha256": hit["payload_sha256"],
                "category": category,
            }
        )

    duplicate_groups = []
    for digest, count in sorted(digest_counts.items()):
        if count <= 1:
            continue
        duplicate_groups.append(
            {
                "payload_sha256": digest,
                "message_ids": tuple(
                    hit["id"] for hit in hits
                    if hit["payload_sha256"] == digest
                ),
            }
        )

    new_year = next(hit for hit in creator_hits if hit["id"] == 53342)
    decoded = decode_bytes(new_year["bits"])
    if decoded is None:
        raise AssertionError("message 53342 is no longer byte-aligned")

    return {
        "hit_count": len(hits),
        "unique_payload_count": len({hit["bits"] for hit in hits}),
        "creator_ids": tuple(hit["id"] for hit in creator_hits),
        "new_year_text": decoded.decode("ascii"),
        "inventory": inventory,
        "duplicate_groups": duplicate_groups,
    }


def self_test(export_path=DEFAULT_EXPORT_DIR):
    report = audit(export_path)
    assert report["hit_count"] == EXPECTED_HIT_COUNT
    assert tuple(row["id"] for row in report["inventory"]) == EXPECTED_MESSAGE_IDS
    assert report["creator_ids"] == EXPECTED_CREATOR_IDS
    assert report["new_year_text"] == EXPECTED_NEW_YEAR_TEXT
    categories = Counter(row["category"] for row in report["inventory"])
    assert categories == {
        "creator_macro": 1,
        "creator_new_year": 1,
        "repost_of_creator_macro": 3,
        "repost_of_creator_new_year": 1,
        "repeated_noncreator": 8,
        "unique_noncreator": 11,
    }
    print("[*] self-test OK: full-export binary inventory reproduced")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = self_test(args.export) if args.self_test else audit(args.export)
    print(f"[*] qualifying messages: {report['hit_count']}")
    print(f"[*] unique payloads: {report['unique_payload_count']}")
    print(f"[*] creator message IDs: {report['creator_ids']}")
    print(f"[*] message 53342: {report['new_year_text']!r}")
    print("[*] inventory:")
    for row in report["inventory"]:
        print(
            f"    {row['id']:5} {row['bit_length']:4} bits "
            f"{row['payload_sha256'][:16]} {row['category']}"
        )
    print("[*] duplicate payload groups:")
    for group in report["duplicate_groups"]:
        print(
            f"    {group['payload_sha256'][:16]} "
            f"messages={group['message_ids']}"
        )


if __name__ == "__main__":
    main()
