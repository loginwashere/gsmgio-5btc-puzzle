#!/usr/bin/env python3
"""Test the creator's binary macro as an operand-scope clue.

The authenticated SalPhaseIon page says:

    sha256 our first hint is your last command

Creator message 8446 is a reversed whole-bitstream macro beginning with
``yellowblueprimes``.  That supplies three bounded, source-grounded readings
that prior direct checks did not cover together:

* the exact binary macro transport or its decoded text is the hint;
* ``yellowblueprimes`` identifies creator message 1710, the first formal hint;
* the exact 31-character result recovered by following that chain is
  ``thispassword`` and therefore the SHA operand.

This audit tests only exact transport/decoded/result representations.  It does
not add dictionary words, anagrams, arbitrary bit orders, or transforms.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
)
from denis_prime_extraction_audit import TARGET as SELECTED_31  # noqa: E402
from salphaseion_title_rebus_audit import (  # noqa: E402
    CREATOR_ID,
    EXPECTED_MACRO,
    MACRO_MESSAGE_ID,
    decode_reversed_bitstream,
    flatten_text,
)
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402

FIRST_FORMAL_HINT_ID = 1710
EXPECTED_FIRST_HINT_PREFIX = "Roses are White but often Red."
EXPECTED_FIRST_HINT_PRIME = "574061"


def load_creator_texts(export_dir=DEFAULT_EXPORT_DIR):
    payload = json.loads(
        (Path(export_dir) / "result.json").read_text(encoding="utf-8")
    )
    messages = {message["id"]: message for message in payload["messages"]}
    selected = {}
    for message_id in (MACRO_MESSAGE_ID, FIRST_FORMAL_HINT_ID):
        message = messages[message_id]
        if message.get("from_id") != CREATOR_ID:
            raise AssertionError(f"message {message_id} is not creator-authored")
        selected[message_id] = flatten_text(message.get("text", ""))
    return selected


def source_operands(export_dir=DEFAULT_EXPORT_DIR):
    messages = load_creator_texts(export_dir)
    macro_transport = messages[MACRO_MESSAGE_ID]
    compact_bits = "".join(macro_transport.split())
    decoded_macro = decode_reversed_bitstream(macro_transport)
    first_hint = messages[FIRST_FORMAL_HINT_ID]
    collapsed_hint = " ".join(first_hint.split())
    letters_hint = "".join(re.findall(r"[A-Za-z]+", first_hint)).lower()

    if decoded_macro != EXPECTED_MACRO:
        raise AssertionError("creator macro no longer decodes to the expected text")
    if not first_hint.startswith(EXPECTED_FIRST_HINT_PREFIX):
        raise AssertionError("first formal hint text changed")
    if not decoded_macro.startswith("yellowblueprimesmatrixsumlist"):
        raise AssertionError("macro no longer identifies the yellow/blue-prime chain")

    return {
        "macro_transport_exact": macro_transport.encode(),
        "macro_transport_compact_bits": compact_bits.encode(),
        "macro_transport_packed": int(compact_bits, 2).to_bytes(
            len(compact_bits) // 8, "big"
        ),
        "macro_decoded": decoded_macro.encode(),
        "first_formal_hint_exact": first_hint.encode(),
        "first_formal_hint_collapsed": collapsed_hint.encode(),
        "first_formal_hint_letters": letters_hint.encode(),
        "first_hint_solved_prime": EXPECTED_FIRST_HINT_PRIME.encode(),
        "selected_31_thispassword": SELECTED_31.encode(),
    }


def operand_materials(operands):
    """Generate only literal, SHA-256, and ``ans too``-style double-SHA forms.

    LF/CRLF are applied to the operand before hashing, matching the established
    ``enter``/shell-command interpretation used elsewhere in this project.
    The double hash follows the known command-state convention: hash the first
    command's lowercase hexadecimal output, not an invented binary-key rule.
    """
    materials = {}
    for operand_label, operand in operands.items():
        for newline_label, suffix in (
            ("none", b""),
            ("lf", b"\n"),
            ("crlf", b"\r\n"),
        ):
            source = operand + suffix
            first_digest = hashlib.sha256(source).digest()
            first_hex = first_digest.hex().encode()
            second_digest = hashlib.sha256(first_hex).digest()
            forms = (
                ("literal", source),
                ("sha256_raw", first_digest),
                ("sha256_hex_lower", first_hex),
                ("sha256_hex_upper", first_hex.upper()),
                ("sha256_ans_too_raw", second_digest),
                ("sha256_ans_too_hex", second_digest.hex().encode()),
            )
            for form_label, material in forms:
                label = f"{operand_label}/{newline_label}/{form_label}"
                materials.setdefault(material, label)
    return materials


def run_oracle(materials, blobs):
    hits = []
    for material, label in materials.items():
        for family, result in (
            ("cbc_legacy", aes_try_open_bytes(material, blobs=blobs)),
            (
                "cbc_extended",
                aes_try_open_bytes(
                    material,
                    kdf_variants=EXTENDED_CIPHER_VARIANTS,
                    blobs=blobs,
                ),
            ),
            ("ecb", aes_try_open_ecb_bytes(material, blobs=blobs)),
            ("stream", aes_try_open_stream_bytes(material, blobs=blobs)),
        ):
            if result:
                hits.append((label, family, result))
        for result in aes_keywrap_try_open_bytes(material, blobs=blobs):
            hits.append((label, "keywrap", result))
    return hits


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    operands = source_operands(export_dir)
    assert set(operands) == {
        "macro_transport_exact",
        "macro_transport_compact_bits",
        "macro_transport_packed",
        "macro_decoded",
        "first_formal_hint_exact",
        "first_formal_hint_collapsed",
        "first_formal_hint_letters",
        "first_hint_solved_prime",
        "selected_31_thispassword",
    }
    assert len(operands["macro_transport_compact_bits"]) == 1288
    assert len(operands["macro_transport_packed"]) == 161
    assert operands["macro_decoded"].decode() == EXPECTED_MACRO
    assert operands["selected_31_thispassword"].decode() == SELECTED_31

    materials = operand_materials(operands)
    assert materials
    selected_sha = hashlib.sha256(SELECTED_31.encode()).hexdigest().encode()
    assert (
        materials[selected_sha]
        == "selected_31_thispassword/none/sha256_hex_lower"
    )
    print(
        "[*] self-test OK: creator provenance, whole-stream reversal, "
        "first-hint linkage, and bounded SHA material generation"
    )
    return operands, materials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    operands, materials = self_test(args.export)
    print(f"[*] operands={len(operands)} unique_materials={len(materials)}")
    if args.self_test or args.no_oracle:
        return

    blobs = dict(BLOBS)
    if args.include_quarantined:
        blobs.update(QUARANTINED_BLOBS)
    hits = run_oracle(materials, blobs)
    print(f"[*] blobs={len(blobs)} hits={len(hits)}")
    for label, family, result in hits:
        print(f"[+++ HIT] {label} {family} {result}")


if __name__ == "__main__":
    main()
