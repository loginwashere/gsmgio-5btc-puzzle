#!/usr/bin/env python3
"""Audit Telegram claims about how the intended [23,16,7] list is consumed.

The complete Telegram export contains many quotations of the Architect text.
This audit first counts every message containing all three standalone numbers,
then inspects a frozen, message-ID-scoped subset that states an arithmetic,
logical, cryptographic, or structural interpretation.  It does not generate
new transforms or send any derived value to a cipher oracle.

The strongest structural message is Denis Golovkin's ``83=b, 84=e`` note.  The
recovered yellow-blue-primes guide has 83 tokens when its final ``be`` remains
one token.  Splitting that final token makes token 83 ``b`` and token 84 ``e``;
the 23 guide endpoints then count as exactly 16 blue and 7 yellow.  This
reproduces ``7/16/23`` as a guide profile, not as a downstream operation.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from first_piece_color_reconstruction import is_prime
from telegram_export_manifest import DEFAULT_EXPORT_DIR
from telegram_yellow_blue_guide_audit import reconstruct_guide

CREATOR_FROM_ID = "user9815232"
EXPECTED_LIST_HIT_COUNT = 56

OPERATION_MESSAGE_IDS = (
    6115,   # decimal digit sums
    16726,  # 16 + 7 = 23
    22530,  # XOR wording
    26922,  # AND/OR interpretation
    34076,  # "take away"; explicitly LLM-aided
    36002,  # decimal concatenation -> 23167
    45848,  # imported BIP38 mechanics
    45849,  # BIP38 analogy to 23/16/7
    46522,  # unrelated sum including 140
    47688,  # expanded BIP38 analogy
    50381,  # 1327 = 23*57+16 after alleged seven-pass XOR
    53997,  # recovered-guide endpoint profile
    60893,  # sum 46
    66395,  # URL lengths 24/16/7, not 23/16/7
)

EXPECTED_TEXT_SNIPPETS = {
    6115: "23 ciphers = 2+3=5 (prime)",
    16726: "16+7=23 as well",
    22530: "16 encryptions XOR 7 intertwined passwords",
    26922: "i think AND OR is important here",
    34076: "P.P.S just realized, it was LLM aided",
    36002: "23,16,7 = 23167 is also a prime number",
    45848: "Bip 38",
    45849: "23, 16, 7 parts, xor",
    46522: "140+16+23+7=186",
    47688: "could be instructions for BIP38",
    50381: "1327 = 23x57 + 16",
    53997: "consider 83=b, 84=e",
    60893: "46 digits (matrix text 23+16+7)",
    66395: "gsmg.io/theseedisplanted = 24",
}

NUMBER_PATTERN = re.compile(r"(?<!\d)(7|16|23)(?!\d)")


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_messages(export_dir):
    payload = json.loads(
        (Path(export_dir) / "result.json").read_text(encoding="utf-8")
    )
    messages = {message["id"]: message for message in payload["messages"]}
    return payload, messages


def has_full_list(text):
    return {int(value) for value in NUMBER_PATTERN.findall(text)} >= {7, 16, 23}


def media_reference(message):
    return message.get("photo") or message.get("file")


def guide_endpoint_profile():
    guide = reconstruct_guide()
    chunks = guide["chunks"]
    tokens = guide["tokens"]
    if len(chunks) != 23 or len(tokens) != 83:
        raise AssertionError("recovered guide dimensions changed")
    if chunks[-1][-1] != "be" or tokens[-1] != "be":
        raise AssertionError("recovered guide no longer ends in one be token")

    split_tokens = tokens[:-1] + ("b", "e")
    split_chunks = chunks[:-1] + (chunks[-1][:-1] + ("b",),)
    endpoint_tokens = tuple(chunk[-1] for chunk in split_chunks)
    endpoint_colors = tuple(
        "Y" if token == "be" else "B"
        for token in endpoint_tokens
    )
    counts = Counter(endpoint_colors)
    return {
        "original_token_count": len(tokens),
        "split_token_count": len(split_tokens),
        "token_83": split_tokens[82],
        "token_84": split_tokens[83],
        "endpoint_count": len(endpoint_tokens),
        "endpoint_colors": "".join(endpoint_colors),
        "blue_endpoints": counts["B"],
        "yellow_endpoints": counts["Y"],
        "profile_7_16_23": (
            counts["Y"],
            counts["B"],
            len(endpoint_tokens),
        ),
    }


def audit(export_dir=DEFAULT_EXPORT_DIR):
    payload, messages = load_messages(export_dir)
    list_hits = tuple(
        message["id"]
        for message in payload["messages"]
        if has_full_list(flatten_text(message.get("text", "")))
    )
    records = []
    for message_id in OPERATION_MESSAGE_IDS:
        message = messages[message_id]
        message_text = flatten_text(message.get("text", ""))
        expected = EXPECTED_TEXT_SNIPPETS[message_id]
        if expected not in message_text:
            raise AssertionError(f"message {message_id} text changed")
        children = tuple(
            child
            for child in payload["messages"]
            if child.get("reply_to_message_id") == message_id
        )
        records.append(
            {
                "id": message_id,
                "date": message["date"],
                "from": message.get("from"),
                "from_id": message.get("from_id"),
                "reply_to": message.get("reply_to_message_id"),
                "text": message_text,
                "media": media_reference(message),
                "child_ids": tuple(child["id"] for child in children),
                "creator_child_ids": tuple(
                    child["id"]
                    for child in children
                    if child.get("from_id") == CREATOR_FROM_ID
                ),
            }
        )

    profile = guide_endpoint_profile()
    arithmetic = {
        "sum": 23 + 16 + 7,
        "subset_identity": 16 + 7,
        "xor": 23 ^ 16 ^ 7,
        "decimal_concatenation": int("23167"),
        "decimal_concatenation_is_prime": is_prime(int("23167")),
        "bip38_claimed_total": 23 + 16,
        "introduced_57_identity": 23 * 57 + 16,
        "url_profile": (
            len("gsmg.io/theseedisplanted"),
            len("theseedisplanted"),
            len("gsmg.io"),
        ),
    }
    creator_authored = tuple(
        record["id"]
        for record in records
        if record["from_id"] == CREATOR_FROM_ID
    )
    creator_replies = tuple(
        child_id
        for record in records
        for child_id in record["creator_child_ids"]
    )
    media_messages = tuple(
        record["id"] for record in records if record["media"]
    )

    return {
        "group_name": payload["name"],
        "list_hit_ids": list_hits,
        "operation_records": tuple(records),
        "guide_profile": profile,
        "arithmetic": arithmetic,
        "creator_authored_operation_ids": creator_authored,
        "creator_reply_ids": creator_replies,
        "operation_media_ids": media_messages,
        "classification": {
            "structural_checkpoint": (53997,),
            "arithmetic_numerology": (6115, 16726, 36002, 46522, 50381, 60893),
            "imported_cipher_analogy": (45848, 45849, 47688),
            "logical_or_subtractive_speculation": (22530, 26922, 34076),
            "different_24_16_7_profile": (66395,),
        },
        "operation_selected": False,
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert len(report["list_hit_ids"]) == EXPECTED_LIST_HIT_COUNT
    assert report["guide_profile"] == {
        "original_token_count": 83,
        "split_token_count": 84,
        "token_83": "b",
        "token_84": "e",
        "endpoint_count": 23,
        "endpoint_colors": "BBBBYBBBYYBBBBYBBYYBBYB",
        "blue_endpoints": 16,
        "yellow_endpoints": 7,
        "profile_7_16_23": (7, 16, 23),
    }
    assert report["arithmetic"] == {
        "sum": 46,
        "subset_identity": 23,
        "xor": 0,
        "decimal_concatenation": 23167,
        "decimal_concatenation_is_prime": True,
        "bip38_claimed_total": 39,
        "introduced_57_identity": 1327,
        "url_profile": (24, 16, 7),
    }
    assert not report["creator_authored_operation_ids"]
    assert not report["creator_reply_ids"]
    assert not report["operation_media_ids"]
    assert report["operation_selected"] is False
    print(
        "[*] self-test OK: full-list census, exact guide 7/16/23 profile, "
        "frozen operation claims, and creator/reply/media negatives verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.export_dir)
    print(
        f"[*] messages containing standalone 7, 16, and 23: "
        f"{len(report['list_hit_ids'])}"
    )
    print("[*] frozen operation-bearing records:")
    for record in report["operation_records"]:
        print(
            f"    {record['id']} {record['date']} {record['from']!r} "
            f"reply={record['reply_to']} children={record['child_ids']}"
        )
    print(f"[*] exact guide endpoint profile: {report['guide_profile']}")
    print(f"[*] stated arithmetic: {report['arithmetic']}")
    print(f"[*] classification: {report['classification']}")
    print(
        f"[*] creator-authored operation messages: "
        f"{report['creator_authored_operation_ids']}"
    )
    print(f"[*] creator replies to operation messages: {report['creator_reply_ids']}")
    print(f"[*] attached media on operation messages: {report['operation_media_ids']}")
    print(
        "[*] verdict: Telegram independently preserves [7,16,23] as the "
        "recovered guide's endpoint-count profile. It supplies no creator-backed "
        "consumer: sum, XOR, concatenation, subtraction, BIP38, and URL-length "
        "uses remain community proposals. Treat the list as counts/checkpoint "
        "data, not as authorization for another transform or AES test."
    )
    if args.self_test:
        self_test(args.export_dir)


if __name__ == "__main__":
    main()
