#!/usr/bin/env python3
"""Reconstruct and audit the creator's pre-rabbit GSMG puzzle announcement."""

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aes_key_wrap_sweep import ALL_CBC_VARIANTS  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    raw_key_try_open,
)
from first_hint_hash_audit import (  # noqa: E402
    HALVING_ADDRESS,
    PRIZE_ADDRESS,
    p2pkh_addresses,
)

DEFAULT_EXPORT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/"
    "ChatExport_2026-07-26/result.json"
)
ANNOUNCEMENT = (
    "Here is the GSMG Puzzle! First to crack the code and retrieve a private "
    "key may keep the hidden bitcoins. Good luck to you all!"
)
QUESTION = (
    "HOW_DID_CAESAR_SEND_HIS_MESSAGES?AND_WHAT_IF_13_IS_DEFAULT_AND_THE_"
    "NUMBER_C_IS_THE_2ND_HINT?"
)
INSTRUCTION = "removethecorrecthinttoproceedtothenextstage"
FINAL_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
FIRST_EXTERNAL_HINT_URL = (
    "http://lmgtfy.com/?q=How+did+caesar+send+his+messages%3F"
)
FIRST_EXTERNAL_HINT_QUERY = "How did caesar send his messages?"


def caesar(text, shift):
    output = []
    for character in text:
        if character.isalpha():
            base = ord("a") if character.islower() else ord("A")
            output.append(chr((ord(character) - base + shift) % 26 + base))
        else:
            output.append(character)
    return "".join(output)


def extract_forwarded_payload(export_path):
    data = json.loads(Path(export_path).read_text())
    messages = data["messages"]
    for index, message in enumerate(messages[:-2]):
        if message.get("text") != ANNOUNCEMENT:
            continue
        if message.get("forwarded_from") != "Jrk Bgrt":
            continue
        following = messages[index + 1 : index + 3]
        if all(
            item.get("forwarded_from") == "Jrk Bgrt"
            and isinstance(item.get("text"), str)
            and re.fullmatch(r"[01]+", item["text"])
            for item in following
        ):
            return message, "".join(item["text"] for item in following)
    raise ValueError("no complete creator-forwarded announcement payload found")


def reconstruct(binary_text):
    assert len(binary_text) % 8 == 0
    outer = bytes(
        int(binary_text[index : index + 8], 2)
        for index in range(0, len(binary_text), 8)
    )
    outer_text = outer.decode("ascii")
    match = re.fullmatch(r"(.+?)([01]{100,})([^01]+)", outer_text)
    assert match
    prefix, inner_bits, suffix = match.groups()
    reversed_question, shifted_instruction = prefix.split("|", 1)
    question = reversed_question[::-1]
    instruction = caesar(shifted_instruction, -3)
    reverse_instruction = caesar(suffix, -3)[::-1]
    reversed_inner = bytes(
        int(inner_bits[::-1][index : index + 8], 2)
        for index in range(0, len(inner_bits), 8)
    ).decode("ascii")
    assert reversed_inner.startswith("BASE64")
    payload = reversed_inner.removeprefix("BASE64")
    final_url = base64.b64decode(payload).decode("ascii")

    assert question == QUESTION
    assert instruction == INSTRUCTION
    assert reverse_instruction == "reverse"
    assert final_url == FINAL_URL
    return {
        "announcement_caption": ANNOUNCEMENT.encode(),
        # Support-group message 26065 labels this exact URL the "First
        # external hint." The decoded query is included as the only equally
        # literal content-level reading; no URL/case/punctuation variants.
        "first_external_hint_url": FIRST_EXTERNAL_HINT_URL.encode(),
        "first_external_hint_query": FIRST_EXTERNAL_HINT_QUERY.encode(),
        "two_message_binary": binary_text.encode(),
        "outer_binary_decode": outer,
        "caesar_question": question.encode(),
        "caesar_instruction": instruction.encode(),
        "reverse_command": reverse_instruction.encode(),
        "reversed_inner_ascii": reversed_inner.encode(),
        "base64_command": b"BASE64",
        "base64_payload": payload.encode(),
        "final_url": final_url.encode(),
    }


def audit(materials):
    blobs = {**BLOBS, **QUARANTINED_BLOBS}
    known_addresses = {PRIZE_ADDRESS, HALVING_ADDRESS}
    totals = {"address": 0, "cbc": 0, "wrap": 0, "raw_key": 0}
    for label, material in materials.items():
        digest = hashlib.sha256(material).digest()
        addresses = p2pkh_addresses(digest)
        address_hits = known_addresses.intersection(addresses.values())
        cbc_hits = []
        wrap_hits = []
        for passphrase in (digest, digest.hex().encode()):
            hit = aes_try_open_bytes(
                passphrase,
                kdf_variants=ALL_CBC_VARIANTS,
                blobs=blobs,
            )
            if hit:
                cbc_hits.append(hit)
            wrap_hits.extend(aes_keywrap_try_open_bytes(passphrase, blobs=blobs))
        raw_key_hits = raw_key_try_open(digest, blobs=blobs)
        totals["address"] += len(address_hits)
        totals["cbc"] += len(cbc_hits)
        totals["wrap"] += len(wrap_hits)
        totals["raw_key"] += len(raw_key_hits)
        print(
            label,
            hashlib.sha256(material).hexdigest(),
            f"address={len(address_hits)}",
            f"cbc={len(cbc_hits)}",
            f"wrap={len(wrap_hits)}",
            f"raw_key={len(raw_key_hits)}",
        )
    print("totals:", " ".join(f"{key}={value}" for key, value in totals.items()))
    return totals


def self_test():
    assert caesar("uhpryh", -3) == "remove"
    assert caesar("hvuhyhu", -3)[::-1] == "reverse"
    assert base64.b64decode(
        "aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g/dj1kUXc0dzlXZ1hjUQ=="
    ).decode() == FINAL_URL
    assert FIRST_EXTERNAL_HINT_URL.partition("?q=")[2].replace("+", " ").replace(
        "%3F", "?"
    ) == FIRST_EXTERNAL_HINT_QUERY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print("[*] self-test OK")
        return
    message, binary_text = extract_forwarded_payload(args.export)
    materials = reconstruct(binary_text)
    print(
        f"[*] forwarded copy message={message['id']} date={message['date']} "
        f"binary_bits={len(binary_text)}"
    )
    totals = audit(materials)
    if any(totals.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
