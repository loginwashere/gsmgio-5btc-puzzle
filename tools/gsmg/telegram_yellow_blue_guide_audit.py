#!/usr/bin/env python3
"""Audit the recovered Telegram yellow-blue-primes guide.

The Telegram JSON reply graph links Denis Golovkin's 2026-03-04 description of
the missing guide to Nik's 2025-05-01 image.  This script preserves that
provenance, reconstructs the guide's DBBI token/chunk arithmetic, verifies the
published 14x14 matrix and its ``IZLKESEEDQPPEN`` row-sum output, and reports
the two distinct unresolved features without repairing either post hoc:

* prime-token colors disagree with the first-piece colors at events 21 and 23;
* the published matrix places prime-token 23 one spiral cell before its
  corresponding colored endpoint, while every other prime endpoint aligns.

The recovered guide is therefore reproducible as an artifact, but its complete
placement rule is not yet fully specified.  A corrected FEFE insertion must not
be run until that historical one-cell shift and a bounded collision policy are
pre-registered.
"""

import argparse
import hashlib
import json
from pathlib import Path

from data import DBBI
from door_prime_passport_probe import nth_prime
from first_piece_color_reconstruction import (
    DEFAULT_IMAGE,
    EXPECTED_COLOR_SEQUENCE,
    reconstruct,
    spiral_top_left_counterclockwise,
)

DEFAULT_EXPORT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26"
)
RESULT_JSON = "result.json"
GUIDE_MESSAGE_ID = 39937
GUIDE_REPLY_ID = 60325
GUIDE_PHOTO = "photos/photo_1300@01-05-2025_00-12-58.jpg"
GUIDE_PHOTO_SHA256 = (
    "475456f9ecf8fd56ef6247f081ba8ee0796eef3f6ed3be0ca01c4a5ee0bfb85a"
)
EXPECTED_GROUP_NAME = "GSMG Puzzle Solvers"
EXPECTED_GROUP_TYPE = "private_supergroup"
EXPECTED_GUIDE_AUTHOR = "Nik"
EXPECTED_GUIDE_REPLY_AUTHOR = "Denis Golovkin"
EXPECTED_GUIDE_REPLY_TEXT = (
    "Here was a guide to yellow-blue-primes.\nNotice that 'B' for blue and "
    "both 'BE' for yellow participate."
)
EXPECTED_CHUNKS = (
    "db",
    "b",
    "ib",
    "fb",
    "hccbe",
    "gb",
    "ihab",
    "eb",
    "eihbe",
    "ggegebe",
    "bb",
    "gehheb",
    "hhfb",
    "ab",
    "fdhbe",
    "ffcdbb",
    "fcccgb",
    "fbe",
    "eggecbe",
    "dcib",
    "fb",
    "ffgigbe",
    "eeabe",
)
EXPECTED_PRIME_COLORS = "BBBBYBBBYYBBBBYBBYYBBYY"
EXPECTED_MATRIX = (
    (0, 0, 0, 0, 0, 2, 7, 0, 0, 0, 0, 0, 0, 25),
    (0, 9, 2, 5, 8, 8, 5, 7, 0, 0, 2, 2, 0, 3),
    (0, 8, 0, 3, 6, 0, 0, 2, 2, 4, 3, 6, 0, 3),
    (0, 1, 0, 3, 2, 9, 3, 4, 0, 0, 0, 6, 0, 8),
    (0, 2, 0, 3, 0, 0, 0, 0, 0, 25, 0, 0, 0, 0),
    (0, 0, 0, 7, 0, 5, 0, 0, 0, 7, 25, 0, 0, 0),
    (4, 0, 8, 2, 0, 5, 0, 0, 0, 9, 3, 25, 0, 0),
    (2, 0, 8, 0, 0, 1, 0, 0, 0, 7, 5, 8, 25, 0),
    (0, 0, 6, 0, 0, 25, 0, 0, 0, 6, 7, 4, 5, 2),
    (0, 0, 2, 0, 0, 6, 2, 0, 0, 6, 7, 6, 7, 6),
    (0, 0, 0, 0, 0, 0, 6, 25, 0, 0, 5, 0, 5, 0),
    (0, 5, 0, 0, 0, 0, 0, 1, 2, 0, 0, 0, 7, 0),
    (0, 2, 0, 0, 0, 5, 9, 8, 25, 0, 0, 0, 7, 0),
    (0, 0, 2, 0, 0, 0, 0, 9, 0, 0, 2, 0, 0, 0),
)
EXPECTED_ROW_SUMS = (34, 51, 37, 36, 30, 44, 56, 56, 55, 42, 41, 15, 56, 13)
EXPECTED_OUTPUT = "IZLKESEEDQPPEN"


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_export(export_path):
    result_path = export_path / RESULT_JSON
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    messages = {message["id"]: message for message in payload["messages"]}
    return payload, messages


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_provenance(export_path):
    payload, messages = load_export(export_path)
    guide = messages[GUIDE_MESSAGE_ID]
    reply = messages[GUIDE_REPLY_ID]
    photo_path = export_path / GUIDE_PHOTO
    report = {
        "group_name": payload["name"],
        "group_type": payload["type"],
        "message_count": len(payload["messages"]),
        "guide_author": guide["from"],
        "guide_date": guide["date"],
        "guide_text": flatten_text(guide.get("text", "")),
        "guide_photo": guide["photo"],
        "reply_author": reply["from"],
        "reply_date": reply["date"],
        "reply_text": flatten_text(reply.get("text", "")),
        "reply_to_message_id": reply["reply_to_message_id"],
        "photo_path": photo_path,
        "photo_sha256": sha256(photo_path),
    }
    if report["group_name"] != EXPECTED_GROUP_NAME:
        raise AssertionError(f"unexpected Telegram group: {report['group_name']!r}")
    if report["group_type"] != EXPECTED_GROUP_TYPE:
        raise AssertionError(f"unexpected Telegram group type: {report['group_type']!r}")
    if report["guide_author"] != EXPECTED_GUIDE_AUTHOR:
        raise AssertionError(f"unexpected guide author: {report['guide_author']!r}")
    if report["guide_photo"] != GUIDE_PHOTO:
        raise AssertionError(f"unexpected guide photo: {report['guide_photo']!r}")
    if report["reply_author"] != EXPECTED_GUIDE_REPLY_AUTHOR:
        raise AssertionError(f"unexpected reply author: {report['reply_author']!r}")
    if report["reply_text"] != EXPECTED_GUIDE_REPLY_TEXT:
        raise AssertionError(f"unexpected guide reply text: {report['reply_text']!r}")
    if report["reply_to_message_id"] != GUIDE_MESSAGE_ID:
        raise AssertionError("guide reply does not point to the guide image message")
    if report["photo_sha256"] != GUIDE_PHOTO_SHA256:
        raise AssertionError(f"guide photo hash mismatch: {report['photo_sha256']}")
    return report


def tokenize_dbbi(value):
    tokens = []
    offset = 0
    while offset < len(value):
        if value.startswith("be", offset):
            tokens.append("be")
            offset += 2
        else:
            tokens.append(value[offset])
            offset += 1
    return tuple(tokens)


def token_value(token):
    if token == "be":
        return 25
    if len(token) != 1 or token < "a" or token > "i":
        raise ValueError(f"unsupported guide token: {token!r}")
    return ord(token) - ord("a") + 1


def guide_chunks(source, colors):
    chunks = []
    start = 0
    yellow_count = 0
    for ordinal, color in enumerate(colors, start=1):
        end = nth_prime(ordinal)
        raw_position = end + yellow_count
        raw_index = raw_position - 1
        required = "be" if color == "Y" else "b"
        alternate = "b" if required == "be" else "be"
        if ordinal == len(colors):
            chunk_end = len(source)
            actual = "be" if source.endswith("be") else "b"
        elif source.startswith(required, raw_index):
            actual = required
            chunk_end = raw_index + len(actual)
        elif source.startswith(alternate, raw_index):
            actual = alternate
            chunk_end = raw_index + len(actual)
        else:
            raise AssertionError(
                f"neither B nor BE occurs at event {ordinal}, "
                f"raw position {raw_position}"
            )
        chunks.append(source[start:chunk_end])
        start = chunk_end
        yellow_count += actual == "be"
    if start != len(source):
        raise AssertionError(f"guide has an unassigned suffix: {source[start:]!r}")
    return tuple(chunks)


def matrix_spiral_values(matrix):
    return tuple(
        matrix[row][column]
        for row, column in spiral_top_left_counterclockwise()
    )


def output_from_row_sums(row_sums):
    return "".join(chr(value % 26 + ord("A")) for value in row_sums)


def reconstruct_guide(image_path=DEFAULT_IMAGE):
    chunk_strings = guide_chunks(DBBI, EXPECTED_COLOR_SEQUENCE[:23])
    chunks = tuple(tokenize_dbbi(chunk) for chunk in chunk_strings)
    tokens = tuple(token for chunk in chunks for token in chunk)
    token_values = tuple(token_value(token) for token in tokens)
    chunk_values = tuple(
        tuple(token_value(token) for token in chunk)
        for chunk in chunks
    )
    prime_colors = "".join("Y" if chunk[-1] == "be" else "B" for chunk in chunks)
    spiral_values = matrix_spiral_values(EXPECTED_MATRIX)
    filtered_values = tuple(value for value in spiral_values if value)
    row_sums = tuple(sum(row) for row in EXPECTED_MATRIX)
    output = output_from_row_sums(row_sums)

    image = reconstruct(image_path)
    object_endpoints = tuple(item["spiral_0"] for item in image["objects"])
    prime_endpoint_positions = []
    nonzero_rank = 0
    prime_ranks = {nth_prime(index) for index in range(1, len(chunks) + 1)}
    for spiral_index, value in enumerate(spiral_values):
        if not value:
            continue
        nonzero_rank += 1
        if nonzero_rank in prime_ranks:
            prime_endpoint_positions.append(spiral_index)

    color_mismatches = tuple(
        index + 1
        for index, (actual, expected) in enumerate(
            zip(prime_colors, EXPECTED_COLOR_SEQUENCE)
        )
        if actual != expected
    )
    placement_mismatches = tuple(
        {
            "event": index + 1,
            "prime": nth_prime(index + 1),
            "published_spiral_0": published,
            "color_endpoint_spiral_0": expected,
            "delta": published - expected,
        }
        for index, (published, expected) in enumerate(
            zip(prime_endpoint_positions, object_endpoints)
        )
        if published != expected
    )

    report = {
        "tokens": tokens,
        "token_values": token_values,
        "chunks": chunks,
        "chunk_strings": chunk_strings,
        "chunk_values": chunk_values,
        "prime_colors": prime_colors,
        "color_mismatches": color_mismatches,
        "spiral_values": spiral_values,
        "filtered_values": filtered_values,
        "row_sums": row_sums,
        "output": output,
        "prime_endpoint_positions": tuple(prime_endpoint_positions),
        "object_endpoints": object_endpoints,
        "placement_mismatches": placement_mismatches,
        "fefe_spiral_0": image["fefe"]["spiral_0"],
    }
    if len(tokens) != 83:
        raise AssertionError(f"unexpected DBBI token count: {len(tokens)}")
    if report["chunk_strings"] != EXPECTED_CHUNKS:
        raise AssertionError(f"guide chunks differ: {report['chunk_strings']}")
    if report["prime_colors"] != EXPECTED_PRIME_COLORS:
        raise AssertionError(f"prime colors differ: {report['prime_colors']}")
    if report["filtered_values"] != report["token_values"]:
        raise AssertionError("published matrix does not preserve the DBBI token stream")
    if report["row_sums"] != EXPECTED_ROW_SUMS:
        raise AssertionError(f"published row sums differ: {report['row_sums']}")
    if report["output"] != EXPECTED_OUTPUT:
        raise AssertionError(f"published output differs: {report['output']}")
    if report["color_mismatches"] != (21, 23):
        raise AssertionError(f"unexpected color mismatches: {report['color_mismatches']}")
    if report["placement_mismatches"] != (
        {
            "event": 9,
            "prime": 23,
            "published_spiral_0": 70,
            "color_endpoint_spiral_0": 71,
            "delta": -1,
        },
    ):
        raise AssertionError(
            f"unexpected placement mismatches: {report['placement_mismatches']}"
        )
    return report


def self_test():
    assert flatten_text(["a", {"type": "bold", "text": "b"}]) == "ab"
    assert tokenize_dbbi("dbebe") == ("d", "be", "be")
    assert token_value("a") == 1
    assert token_value("i") == 9
    assert token_value("be") == 25
    assert output_from_row_sums((34, 51, 37)) == "IZL"
    report = reconstruct_guide()
    assert len(report["chunks"]) == 23
    assert report["fefe_spiral_0"] == 163
    print(
        "[*] self-test OK: recovered guide has 83 DBBI tokens, 23 prime "
        "chunks, output IZLKESEEDQPPEN, color mismatches 21/23, and one "
        "published placement shift at event 9"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--skip-provenance", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    if not args.skip_provenance:
        provenance = audit_provenance(args.export)
        print(
            f"[*] Telegram: {provenance['group_name']} "
            f"({provenance['group_type']}), {provenance['message_count']} messages"
        )
        print(
            f"[*] guide message {GUIDE_MESSAGE_ID}: {provenance['guide_author']} "
            f"{provenance['guide_date']} -> {provenance['guide_photo']}"
        )
        print(
            f"[*] guide reply {GUIDE_REPLY_ID}: {provenance['reply_author']} "
            f"{provenance['reply_date']} -> reply_to={provenance['reply_to_message_id']}"
        )
        print(f"[*] guide SHA-256: {provenance['photo_sha256']}")

    report = reconstruct_guide(args.image)
    print(f"[*] DBBI guide tokens/chunks: {len(report['tokens'])}/{len(report['chunks'])}")
    print(f"[*] prime colors: {report['prime_colors']}")
    print(f"[*] first-piece colors: {EXPECTED_COLOR_SEQUENCE}")
    print(f"[*] color mismatches: {report['color_mismatches']}")
    print(f"[*] row sums: {report['row_sums']}")
    print(f"[*] row-sum output: {report['output']}")
    print(f"[*] placement mismatches: {report['placement_mismatches']}")
    print(f"[*] corrected FEFE event spiral index: {report['fefe_spiral_0']}")
    print(
        "[*] verdict: the recovered historical artifact is reproducible, but "
        "its event-9 one-cell shift is unexplained. Freeze that rule before "
        "testing corrected FEFE collision policies."
    )


if __name__ == "__main__":
    main()
