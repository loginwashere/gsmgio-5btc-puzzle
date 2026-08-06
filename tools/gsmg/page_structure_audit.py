#!/usr/bin/env python3
"""Audit the original SalPhaseIon/Cosmic Duality page structure.

The script reads a raw archived HTML capture, preserves textarea whitespace, and
verifies the exact logical segmentation of the SalPhaseIon stream. It separates
authored line breaks from browser-generated soft wrapping.

Usage:
    python3 tools/gsmg/page_structure_audit.py
    python3 tools/gsmg/page_structure_audit.py --html path/to/capture.html
    python3 tools/gsmg/page_structure_audit.py --json
"""

import argparse
import base64
import json
import os
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import COSMIC_BLOB_B64, DBBI, FAED, SALPHASEION_BLOB_B64  # noqa: E402


DEFAULT_HTML = (
    Path(__file__).resolve().parents[3]
    / "gsmg-site-mirror"
    / "89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32.html"
)

MATRIX_INSTRUCTION = "matrixsumlist"
ENTER_INSTRUCTION = "enter"
DECIMAL_INSTRUCTIONS = (
    "lastwordsbeforearchichoice",
    "thispassword",
)
HASH_PREFIX = "shabefourfirsthintisyourlastcommand"
HASH_SUFFIX = "shabefanstoo"


class TextareaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.in_textarea = False
        self.current = []
        self.textareas = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "textarea":
            self.in_textarea = True
            self.current = []

    def handle_data(self, data):
        if self.in_textarea:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "textarea" and self.in_textarea:
            self.textareas.append("".join(self.current))
            self.in_textarea = False


@dataclass(frozen=True)
class Segment:
    name: str
    start: int
    end: int
    length: int
    alphabet: str
    decoded: str | None = None


def binary_ascii(text):
    return "".join(
        "b" if bit == "1" else "a"
        for character in text
        for bit in f"{ord(character):08b}"
    )


def decimal_transport(text):
    hexadecimal = text.encode("ascii").hex()
    decimal = str(int(hexadecimal, 16))
    return decimal.translate(str.maketrans("1234567890", "abcdefghio"))


def normalize_salphaseion(raw):
    return "".join(raw.split())


def line_lengths(raw):
    return [len(line) for line in raw.splitlines()]


def add_segment(segments, name, stream, cursor, expected, decoded=None):
    actual = stream[cursor:cursor + len(expected)]
    if actual != expected:
        raise ValueError(
            f"{name} mismatch at offset {cursor}: "
            f"expected {expected[:24]!r}, got {actual[:24]!r}"
        )
    segments.append(
        Segment(
            name=name,
            start=cursor,
            end=cursor + len(expected),
            length=len(expected),
            alphabet="".join(sorted(set(expected))),
            decoded=decoded,
        )
    )
    return cursor + len(expected)


def segment_salphaseion(stream):
    matrix_bits = binary_ascii(MATRIX_INSTRUCTION)
    enter_bits = binary_ascii(ENTER_INSTRUCTION)
    decimal_one = decimal_transport(DECIMAL_INSTRUCTIONS[0])
    decimal_two = decimal_transport(DECIMAL_INSTRUCTIONS[1])
    salph_left = SALPHASEION_BLOB_B64[:64]
    salph_right = SALPHASEION_BLOB_B64[64:]

    expected_segments = (
        ("dbbi", DBBI, None),
        ("abba_matrix_instruction", matrix_bits, MATRIX_INSTRUCTION),
        ("faed", FAED, None),
        ("z_separator_1", "z", None),
        ("decimal_instruction_1", decimal_one, DECIMAL_INSTRUCTIONS[0]),
        ("z_separator_2", "z", None),
        ("decimal_instruction_2", decimal_two, DECIMAL_INSTRUCTIONS[1]),
        ("z_separator_3", "z", None),
        ("hash_prefix", HASH_PREFIX, "sha256 our first hint is your last command"),
        ("salphaseion_aes_prefix", salph_left, None),
        ("abba_enter_instruction", enter_bits, ENTER_INSTRUCTION),
        ("salphaseion_aes_suffix", salph_right, None),
        (
            "hash_suffix",
            HASH_SUFFIX,
            "sha256 + unresolved literal anstoo",
        ),
    )

    segments = []
    cursor = 0
    for name, expected, decoded in expected_segments:
        cursor = add_segment(
            segments, name, stream, cursor, expected, decoded=decoded
        )
    if cursor != len(stream):
        raise ValueError(
            f"unclassified SalPhaseIon tail at offset {cursor}: {stream[cursor:]!r}"
        )
    return segments


def audit(html_path):
    parser = TextareaParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    if len(parser.textareas) != 2:
        raise ValueError(f"expected 2 textareas, found {len(parser.textareas)}")

    salphaseion_raw, cosmic_raw = parser.textareas
    salphaseion = normalize_salphaseion(salphaseion_raw)
    cosmic = "".join(cosmic_raw.splitlines())
    if cosmic != COSMIC_BLOB_B64:
        raise ValueError("Cosmic Duality textarea does not match known ciphertext")

    segments = segment_salphaseion(salphaseion)
    salphaseion_ciphertext = base64.b64decode(SALPHASEION_BLOB_B64, validate=True)
    cosmic_ciphertext = base64.b64decode(cosmic, validate=True)
    if not salphaseion_ciphertext.startswith(b"Salted__"):
        raise ValueError("SalPhaseIon blob lacks the OpenSSL Salted__ header")
    if not cosmic_ciphertext.startswith(b"Salted__"):
        raise ValueError("Cosmic Duality blob lacks the OpenSSL Salted__ header")
    return {
        "source": str(html_path),
        "dom_order": ["SalPhaseIon", "Cosmic Duality"],
        "salphaseion": {
            "source_characters": len(salphaseion_raw),
            "logical_characters": len(salphaseion),
            "authored_line_breaks": salphaseion_raw.count("\n"),
            "whitespace_is_single_character_separation": (
                salphaseion_raw == " ".join(salphaseion)
            ),
            "embedded_enter_splits_aes_at": 64,
            "embedded_enter_aes_half_lengths": [64, 64],
            "aes_decoded_bytes": len(salphaseion_ciphertext),
            "segments": [asdict(segment) for segment in segments],
        },
        "cosmic_duality": {
            "logical_characters": len(cosmic),
            "authored_line_breaks": cosmic_raw.count("\n"),
            "line_lengths": line_lengths(cosmic_raw),
            "aes_decoded_bytes": len(cosmic_ciphertext),
            "matches_known_blob": True,
        },
    }


def print_report(report):
    salphaseion = report["salphaseion"]
    cosmic = report["cosmic_duality"]
    print(f"source: {report['source']}")
    print(f"DOM order: {' -> '.join(report['dom_order'])}")
    print(
        "SalPhaseIon: "
        f"{salphaseion['logical_characters']} logical characters; "
        f"{salphaseion['authored_line_breaks']} authored line breaks; "
        "single-space character separation="
        f"{salphaseion['whitespace_is_single_character_separation']}"
    )
    print("segments (zero-based half-open offsets):")
    for segment in salphaseion["segments"]:
        decoded = f" -> {segment['decoded']}" if segment["decoded"] else ""
        print(
            f"  {segment['start']:4}:{segment['end']:<4} "
            f"{segment['name']:<28} len={segment['length']:<4}{decoded}"
        )
    print(
        "Cosmic Duality: "
        f"{cosmic['logical_characters']} logical characters; "
        f"{cosmic['authored_line_breaks']} authored line breaks; "
        f"line lengths={cosmic['line_lengths']}"
    )
    print(
        "structural inference: abba('enter') separates two 64-character "
        "SalPhaseIon AES lines, matching the Cosmic 64-column convention"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = audit(args.html)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
