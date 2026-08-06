#!/usr/bin/env python3
"""Audit the complete GSMG support-group export and its puzzle evidence."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


DEFAULT_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)"
)
DEFAULT_TRUNCATED_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29"
)
DEFAULT_SOLVER_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26"
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVED_RABBIT_JPEG = PROJECT_ROOT / "doc" / "img" / "gsmg_stage0_original_telegram.jpg"

EXPECTED_GROUP_NAME = "GSMG - Community & support group"
EXPECTED_GROUP_TYPE = "public_supergroup"
EXPECTED_GROUP_ID = 1246576180
EXPECTED_MESSAGE_COUNT = 52_851
EXPECTED_TYPE_COUNTS = {"message": 50_249, "service": 2_602}
EXPECTED_FIRST = (1, "2018-04-17T17:53:43")
EXPECTED_LAST = (68_682, "2026-07-28T18:06:33")
CREATOR_ID = "user9815232"
EXPECTED_CREATOR_COUNT = 5_419
EXPECTED_RABBIT_JPEG_SHA256 = (
    "9e2a1473933636ea041581e4e0d795c75298b3a8fac52a21cc048e40e9d903a3"
)

ANNOUNCEMENT_IDS = (25_986, 25_987, 25_988)
FORWARDED_ANNOUNCEMENT_IDS = (21_403, 21_404, 21_405)
EXPECTED_ANNOUNCEMENT_LENGTHS = (127, 4096, 1272)
EXPECTED_ANNOUNCEMENT_SHA256 = (
    "98656462fec7c2fa2a28d3caafee6fb6ed378107fc90a27533a0db5308f2b84d",
    "57e1a122d839c94553bc329791861aed9af5b2f3143d1faf54ead62232889e86",
    "208b29e20b90939a76f016bfcb8e774ef188f259b43cb1fd86a79482f51217f9",
)

# Original support-group IDs are distinct from the solver-group IDs used by
# telegram_creator_clue_index_audit.py.
REQUIRED_MESSAGES = {
    25_986: ("Here is the GSMG Puzzle!", None, None),
    26_065: ("First external hint:", None, None),
    26_083: ("Use that hint on the 2nd binary code.", 26_082, None),
    28_507: ("Well, good luck I guess.", None, "photos/photo_962@19-04-2019_20-36-30.jpg"),
    28_512: ("puzzle hasn't been solved yet", None, None),
    28_522: ("Follow the white rabbit.", 28_521, None),
    28_526: ("few seconds", 28_525, None),
    28_527: ("Only 4 chars.", None, None),
    28_534: ("1 private key is hidden in there.", 28_533, None),
    28_571: ("In the end of the puzzle a private key.", 28_566, None),
    28_703: ("against bruteforcing", None, None),
    28_794: ("Won't work", 28_791, None),
    28_812: ("All the info you need is there.", None, None),
    28_866: ("I can only show you the door.", None, None),
    28_961: ("tiny one in the music channel on slack", None, None),
    29_066: ("5ac407837447fba24ba2802e4d1e9aec", 29_063, None),
    29_123: ("same as you'd crack any other hash", None, None),
    29_132: ("Hash won't help you anyhow.", None, None),
    31_990: ("mistake in phase III", None, None),
    32_043: ("unbelievable amount of progress", None, None),
    32_044: ("we'll release a tiny hint", None, None),
    42_540: ("Didn't do it entirely myself though.", 42_539, None),
    67_741: ("two sloppy days throwing one together", None, None),
    67_742: ("The puzzle is still unsolved.", None, None),
}


def load_export(export_dir):
    with open(Path(export_dir) / "result.json", encoding="utf-8") as handle:
        return json.load(handle)


def plain_text(message):
    return "".join(
        entity.get("text", "") for entity in (message.get("text_entities") or [])
    )


def message_signature(message):
    return (
        message.get("date"),
        message.get("type"),
        message.get("from_id"),
        message.get("reply_to_message_id"),
        message.get("forwarded_from"),
        message.get("photo"),
        message.get("file"),
        message.get("file_name"),
        plain_text(message),
    )


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def validate_required_messages(messages_by_id):
    rows = []
    for message_id, (fragment, reply_id, media_path) in REQUIRED_MESSAGES.items():
        message = messages_by_id[message_id]
        assert message.get("from_id") == CREATOR_ID, message_id
        text = plain_text(message)
        assert fragment in text, (message_id, fragment, text)
        if reply_id is not None:
            assert message.get("reply_to_message_id") == reply_id, message_id
        if media_path is not None:
            assert message.get("photo") == media_path, message_id
        rows.append(
            {
                "id": message_id,
                "date": message["date"],
                "reply_to": message.get("reply_to_message_id"),
                "media": message.get("photo") or message.get("file"),
                "text": text,
            }
        )
    return tuple(rows)


def compare_truncated_prefix(full_data, truncated_data):
    full_by_id = {message["id"]: message for message in full_data["messages"]}
    for old_message in truncated_data["messages"]:
        full_message = full_by_id.get(old_message["id"])
        assert full_message is not None, old_message["id"]
        assert message_signature(old_message) == message_signature(full_message), old_message["id"]
    return len(truncated_data["messages"])


def compare_forwarded_announcement(full_data, solver_data):
    full_by_id = {message["id"]: message for message in full_data["messages"]}
    solver_by_id = {message["id"]: message for message in solver_data["messages"]}
    originals = tuple(plain_text(full_by_id[message_id]) for message_id in ANNOUNCEMENT_IDS)
    forwards = tuple(
        plain_text(solver_by_id[message_id]) for message_id in FORWARDED_ANNOUNCEMENT_IDS
    )
    assert originals == forwards
    for message_id in FORWARDED_ANNOUNCEMENT_IDS:
        assert solver_by_id[message_id].get("forwarded_from") == "Jrk Bgrt"
    return originals


def audit(
    export_dir=DEFAULT_EXPORT_DIR,
    truncated_export_dir=DEFAULT_TRUNCATED_EXPORT_DIR,
    solver_export_dir=DEFAULT_SOLVER_EXPORT_DIR,
):
    data = load_export(export_dir)
    assert data.get("name") == EXPECTED_GROUP_NAME
    assert data.get("type") == EXPECTED_GROUP_TYPE
    assert data.get("id") == EXPECTED_GROUP_ID
    messages = data["messages"]
    assert len(messages) == EXPECTED_MESSAGE_COUNT
    assert Counter(message.get("type") for message in messages) == EXPECTED_TYPE_COUNTS
    assert (messages[0]["id"], messages[0]["date"]) == EXPECTED_FIRST
    assert (messages[-1]["id"], messages[-1]["date"]) == EXPECTED_LAST
    creator_count = sum(message.get("from_id") == CREATOR_ID for message in messages)
    assert creator_count == EXPECTED_CREATOR_COUNT

    messages_by_id = {message["id"]: message for message in messages}
    evidence = validate_required_messages(messages_by_id)

    originals = tuple(plain_text(messages_by_id[message_id]) for message_id in ANNOUNCEMENT_IDS)
    assert tuple(map(len, originals)) == EXPECTED_ANNOUNCEMENT_LENGTHS
    assert tuple(map(sha256_text, originals)) == EXPECTED_ANNOUNCEMENT_SHA256

    truncated_count = None
    if (Path(truncated_export_dir) / "result.json").exists():
        truncated_count = compare_truncated_prefix(data, load_export(truncated_export_dir))

    forwarded_match = None
    if (Path(solver_export_dir) / "result.json").exists():
        compare_forwarded_announcement(data, load_export(solver_export_dir))
        forwarded_match = True

    rabbit_jpeg_hash = hashlib.sha256(ARCHIVED_RABBIT_JPEG.read_bytes()).hexdigest()
    assert rabbit_jpeg_hash == EXPECTED_RABBIT_JPEG_SHA256

    return {
        "message_count": len(messages),
        "creator_count": creator_count,
        "first": EXPECTED_FIRST,
        "last": EXPECTED_LAST,
        "truncated_prefix_count": truncated_count,
        "forwarded_announcement_match": forwarded_match,
        "announcement_lengths": EXPECTED_ANNOUNCEMENT_LENGTHS,
        "announcement_sha256": EXPECTED_ANNOUNCEMENT_SHA256,
        "rabbit_jpeg_sha256": rabbit_jpeg_hash,
        "evidence": evidence,
    }


def self_test():
    synthetic = {
        "date": "2020-01-01T00:00:00",
        "type": "message",
        "from_id": CREATOR_ID,
        "reply_to_message_id": 7,
        "forwarded_from": None,
        "photo": "photos/example.jpg",
        "text_entities": [
            {"type": "plain", "text": "Follow "},
            {"type": "bold", "text": "the rabbit"},
        ],
    }
    assert plain_text(synthetic) == "Follow the rabbit"
    signature = message_signature(synthetic)
    assert signature[0] == synthetic["date"]
    assert signature[3] == 7
    assert signature[5] == "photos/example.jpg"
    assert signature[-1] == "Follow the rabbit"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument(
        "--truncated-export-dir", type=Path, default=DEFAULT_TRUNCATED_EXPORT_DIR
    )
    parser.add_argument("--solver-export-dir", type=Path, default=DEFAULT_SOLVER_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        print("[*] self-test OK")
        return

    report = audit(args.export_dir, args.truncated_export_dir, args.solver_export_dir)
    print(
        f"[*] support export: {report['message_count']:,} messages, "
        f"{report['creator_count']:,} creator records, "
        f"{report['first']} -> {report['last']}"
    )
    print(
        f"[*] old export exact prefix: {report['truncated_prefix_count']}; "
        f"announcement matches solver forwards: "
        f"{report['forwarded_announcement_match']}"
    )
    print(
        f"[*] announcement lengths: {report['announcement_lengths']}; "
        f"rabbit JPEG sha256: {report['rabbit_jpeg_sha256']}"
    )
    print(f"[*] validated {len(report['evidence'])} bounded creator evidence records")


if __name__ == "__main__":
    main()
