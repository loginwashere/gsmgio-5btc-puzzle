#!/usr/bin/env python3
"""Bounded hexadecimal-nibble packing audit for the DBBI/FAED streams.

Earlier audits interpreted ``a``-``i`` as ASCII digits, one numeric byte per
symbol, a whole base-9 integer, ternary coordinates, and checkerboard/base-25
codes.  This script tests the distinct representation where each symbol is one
hexadecimal nibble and consecutive symbols are packed into bytes.

The family is deliberately small: zero- and one-based maps, forward/reversed
streams, and high-first/low-first nibble order.  FAED has an even 570 symbols
and therefore yields eight exact 285-byte bodies.  DBBI has 91 symbols, so it
is diagnostic only: every variant leaves one unpaired nibble and no padding is
invented.  Packed FAED bytes and their binary/hex SHA-256 digests are tested as
password material through the repository's complete standard blob oracles.
"""

import argparse
import bz2
import gzip
import hashlib
import json
import lzma
import math
import zlib

from cb_common import (
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    OPENSSL_MENU_GAP_CIPHER_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    _load_blob,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
)
from data import DBBI, FAED, PHASE32_BLOB_B64, PHASE32_PASSWORD


MAPS = {
    "a0i8": {symbol: value for value, symbol in enumerate("abcdefghi")},
    "a1i9": {symbol: value + 1 for value, symbol in enumerate("abcdefghi")},
}
ORIENTATIONS = ("forward", "reverse")
NIBBLE_ORDERS = ("high_low", "low_high")

SIGNATURES = {
    "openssl_salted": b"Salted__",
    "gzip": b"\x1f\x8b",
    "zip": b"PK\x03\x04",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
    "pdf": b"%PDF-",
    "bzip2": b"BZh",
    "xz": b"\xfd7zXZ\x00",
    "elf": b"\x7fELF",
}

CBC_VARIANTS = tuple(
    KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS + OPENSSL_MENU_GAP_CIPHER_VARIANTS
)


def pack_nibbles(text, digit_map, orientation, nibble_order):
    if orientation not in ORIENTATIONS:
        raise ValueError(f"unknown orientation: {orientation}")
    if nibble_order not in NIBBLE_ORDERS:
        raise ValueError(f"unknown nibble order: {nibble_order}")
    source = text if orientation == "forward" else text[::-1]
    values = [digit_map[symbol] for symbol in source]
    body = bytearray()
    for index in range(0, len(values) - 1, 2):
        first, second = values[index:index + 2]
        if nibble_order == "high_low":
            body.append((first << 4) | second)
        else:
            body.append((second << 4) | first)
    leftover = values[-1] if len(values) % 2 else None
    return bytes(body), leftover


def shannon_entropy(body):
    if not body:
        return 0.0
    counts = {byte: body.count(byte) for byte in set(body)}
    return -sum(
        (count / len(body)) * math.log2(count / len(body))
        for count in counts.values()
    )


def longest_printable_run(body):
    best = current = 0
    for byte in body:
        if 32 <= byte < 127 or byte in (9, 10, 13):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def compression_results(body):
    decompressors = {
        "zlib": zlib.decompress,
        "gzip": gzip.decompress,
        "bzip2": bz2.decompress,
        "xz_lzma": lzma.decompress,
    }
    results = []
    for label, decompressor in decompressors.items():
        try:
            decoded = decompressor(body)
        except (OSError, EOFError, ValueError, zlib.error, lzma.LZMAError):
            continue
        results.append({
            "codec": label,
            "decoded_length": len(decoded),
            "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        })
    return results


def analyze_body(body):
    printable_count = sum(
        byte in (9, 10, 13) or 32 <= byte < 127 for byte in body
    )
    return {
        "byte_length": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "distinct_bytes": len(set(body)),
        "entropy_bits_per_byte": round(shannon_entropy(body), 6),
        "printable_ratio": round(printable_count / len(body), 6),
        "longest_printable_run": longest_printable_run(body),
        "prefix_signatures": tuple(
            label for label, signature in SIGNATURES.items()
            if body.startswith(signature)
        ),
        "embedded_marker_offsets": {
            label: body.find(signature)
            for label, signature in SIGNATURES.items()
            if body.find(signature) >= 0
        },
        "compression_results": compression_results(body),
        "hex_prefix": body[:32].hex(),
    }


def material_forms(rows):
    registry = {}
    for row in rows:
        body = row["body"]
        digest = hashlib.sha256(body).digest()
        forms = {
            "packed_raw": body,
            "sha256_raw": digest,
            "sha256_hex": digest.hex().encode("ascii"),
        }
        for treatment, material in forms.items():
            entry = registry.setdefault(material, {
                "material": material,
                "sources": [],
                "treatments": [],
            })
            entry["sources"].append(row["label"])
            entry["treatments"].append(treatment)
    return tuple(registry.values())


def sanitize_hit(family, result):
    if not result:
        return ()
    if family == "keywrap":
        return tuple({
            "family": family,
            "blob": tag,
            "mode": mode,
            "kdf": kdf,
            "key_bits": key_len * 8,
            "plaintext_length": len(plaintext),
            "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
        } for tag, mode, kdf, key_len, plaintext in result)
    tag, plaintext, kdf, key_len = result
    return ({
        "family": family,
        "blob": tag,
        "kdf": kdf,
        "key_bits": key_len * 8,
        "plaintext_length": len(plaintext),
        "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
    },)


def evaluate_materials(materials, run_oracles=True):
    hits = []
    if not run_oracles:
        return hits
    for entry in materials:
        material = entry["material"]
        material_hash = hashlib.sha256(material).hexdigest()
        families = (
            ("cbc", aes_try_open_bytes(material, CBC_VARIANTS)),
            ("stream", aes_try_open_stream_bytes(material, STREAM_CIPHER_VARIANTS)),
            ("ecb", aes_try_open_ecb_bytes(material, ECB_CIPHER_VARIANTS)),
            ("keywrap", aes_keywrap_try_open_bytes(material, KEY_WRAP_KDF_VARIANTS)),
        )
        for family, result in families:
            for hit in sanitize_hit(family, result):
                hits.append({
                    "sources": tuple(entry["sources"]),
                    "treatments": tuple(entry["treatments"]),
                    "password_material_sha256": material_hash,
                    **hit,
                })
    return hits


def phase32_positive_control():
    blob = _load_blob(PHASE32_BLOB_B64)
    result = aes_try_open_bytes(
        PHASE32_PASSWORD.encode("ascii"),
        blobs={"PHASE32_SOLVED": blob},
    )
    return result is not None


def audit(run_oracles=True):
    if set(DBBI) != set("abcdefghi") or set(FAED) != set("abcdefghi"):
        raise AssertionError("DBBI/FAED nine-symbol alphabet changed")
    if len(DBBI) != 91 or len(FAED) != 570:
        raise AssertionError("DBBI/FAED source lengths changed")

    dbbi_rows = []
    faed_rows = []
    for map_name, digit_map in MAPS.items():
        for orientation in ORIENTATIONS:
            for nibble_order in NIBBLE_ORDERS:
                label = f"{map_name}/{orientation}/{nibble_order}"
                dbbi_body, dbbi_leftover = pack_nibbles(
                    DBBI, digit_map, orientation, nibble_order,
                )
                dbbi_rows.append({
                    "label": label,
                    "packed_byte_length": len(dbbi_body),
                    "leftover_nibble": dbbi_leftover,
                    "packed_sha256_diagnostic": hashlib.sha256(dbbi_body).hexdigest(),
                })
                faed_body, faed_leftover = pack_nibbles(
                    FAED, digit_map, orientation, nibble_order,
                )
                if faed_leftover is not None:
                    raise AssertionError("even-length FAED unexpectedly left a nibble")
                faed_rows.append({
                    "label": label,
                    "body": faed_body,
                    "analysis": analyze_body(faed_body),
                })

    materials = material_forms(faed_rows)
    hits = evaluate_materials(materials, run_oracles=run_oracles)
    return {
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "variant_count": len(faed_rows),
        "faed_packed_byte_length": len(faed_rows[0]["body"]),
        "dbbi_diagnostic_rows": tuple(dbbi_rows),
        "faed_rows": tuple({
            "label": row["label"],
            **row["analysis"],
        } for row in faed_rows),
        "unique_password_material_count": len(materials),
        "material_treatments": ("packed_raw", "sha256_raw", "sha256_hex"),
        "oracle_scope": {
            "blob_count": len(BLOBS),
            "cbc_specs": len(CBC_VARIANTS),
            "stream_specs": len(STREAM_CIPHER_VARIANTS),
            "ecb_specs": len(ECB_CIPHER_VARIANTS),
            "keywrap_kdf_specs": len(KEY_WRAP_KDF_VARIANTS),
        },
        "phase32_positive_control": phase32_positive_control(),
        "hits": hits,
    }


def self_test():
    zero_map = MAPS["a0i8"]
    assert pack_nibbles("abci", zero_map, "forward", "high_low") == (
        bytes.fromhex("0128"), None,
    )
    assert pack_nibbles("abci", zero_map, "forward", "low_high") == (
        bytes.fromhex("1082"), None,
    )
    assert pack_nibbles("abc", zero_map, "forward", "high_low") == (
        bytes.fromhex("01"), 2,
    )
    report = audit(run_oracles=False)
    assert report["source_lengths"] == {"DBBI": 91, "FAED": 570}
    assert report["variant_count"] == 8
    assert report["faed_packed_byte_length"] == 285
    assert len(report["dbbi_diagnostic_rows"]) == 8
    assert all(row["packed_byte_length"] == 45 for row in report["dbbi_diagnostic_rows"])
    assert all(row["leftover_nibble"] is not None for row in report["dbbi_diagnostic_rows"])
    assert report["unique_password_material_count"] == 24
    assert report["phase32_positive_control"] is True
    print("[*] self-test OK: nibble packing family and solved control verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-oracles", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report = audit(run_oracles=not args.no_oracles)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(
        f"[*] FAED: {report['variant_count']} exact variants x "
        f"{report['faed_packed_byte_length']} bytes"
    )
    print(
        f"[*] DBBI: {len(report['dbbi_diagnostic_rows'])} diagnostic variants; "
        "45 bytes + one unpaired nibble each (not promoted)"
    )
    print(f"[*] unique password materials: {report['unique_password_material_count']}")
    print(f"[*] solved Phase 3.2 control: {report['phase32_positive_control']}")
    print(f"[*] prefix-signature hits: {sum(bool(row['prefix_signatures']) for row in report['faed_rows'])}")
    print(f"[*] exact decompression hits: {sum(bool(row['compression_results']) for row in report['faed_rows'])}")
    print(f"[*] blob-oracle hits: {len(report['hits'])}")


if __name__ == "__main__":
    main()
