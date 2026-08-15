#!/usr/bin/env python3
"""Invert the SalPhaseIon decimal transport over DBBI and FAED.

The page's two known decimal instructions were produced as

    ASCII -> hex -> one base-10 integer -> 1234567890 mapped to abcdefghio.

This audit applies that exact inverse to DBBI and FAED.  It admits only two
bounded reversal scopes: reverse the encoded source before inversion, and
reverse the recovered bytes afterward.  Odd-length recovered hex is rejected
rather than repaired with an invented leading zero.  Exact output bytes and
their binary/hex SHA-256 digests are screened for signatures/compression and
tested through the complete standard four-blob passphrase oracle.
"""

import argparse
import hashlib
import json

from data import DBBI, FAED
from nibble_packing_audit import (
    analyze_body,
    evaluate_materials,
    phase32_positive_control,
)
from page_structure_audit import decimal_transport


DIGIT_TRANSLATION = str.maketrans("abcdefghio", "1234567890")
SOURCE_ORIENTATIONS = ("forward", "reverse")
BYTE_ORIENTATIONS = ("forward", "reverse")


def inverse_decimal_transport(encoded):
    invalid = sorted(set(encoded) - set("abcdefghio"))
    if invalid:
        raise ValueError(f"symbols outside decimal-transport alphabet: {invalid}")
    digits = encoded.translate(DIGIT_TRANSLATION)
    value = int(digits, 10)
    hexadecimal = f"{value:x}"
    if len(hexadecimal) % 2:
        return {
            "decimal_digits": digits,
            "hexadecimal": hexadecimal,
            "body": None,
            "rejection": "odd_hex_length",
        }
    return {
        "decimal_digits": digits,
        "hexadecimal": hexadecimal,
        "body": bytes.fromhex(hexadecimal),
        "rejection": None,
    }


def build_rows():
    rows = []
    rejected = []
    for source_name, source in (("DBBI", DBBI), ("FAED", FAED)):
        for source_orientation in SOURCE_ORIENTATIONS:
            oriented = source if source_orientation == "forward" else source[::-1]
            decoded = inverse_decimal_transport(oriented)
            base_label = f"{source_name}/{source_orientation}"
            if decoded["body"] is None:
                rejected.append({
                    "label": base_label,
                    "hex_length": len(decoded["hexadecimal"]),
                    "reason": decoded["rejection"],
                })
                continue
            for byte_orientation in BYTE_ORIENTATIONS:
                body = decoded["body"]
                if byte_orientation == "reverse":
                    body = body[::-1]
                rows.append({
                    "label": f"{base_label}/bytes_{byte_orientation}",
                    "source": source_name,
                    "source_orientation": source_orientation,
                    "byte_orientation": byte_orientation,
                    "decimal_digit_count": len(decoded["decimal_digits"]),
                    "decimal_zero_count": decoded["decimal_digits"].count("0"),
                    "hex_length": len(decoded["hexadecimal"]),
                    "body": body,
                    "analysis": analyze_body(body),
                })
    return rows, rejected


def decimal_material_forms(rows):
    registry = {}
    for row in rows:
        body = row["body"]
        digest = hashlib.sha256(body).digest()
        for treatment, material in (
            ("decoded_raw", body),
            ("sha256_raw", digest),
            ("sha256_hex", digest.hex().encode("ascii")),
        ):
            entry = registry.setdefault(material, {
                "material": material,
                "sources": [],
                "treatments": [],
            })
            entry["sources"].append(row["label"])
            entry["treatments"].append(treatment)
    return tuple(registry.values())


def audit(run_oracles=True):
    if len(DBBI) != 91 or len(FAED) != 570:
        raise AssertionError("DBBI/FAED source lengths changed")
    rows, rejected = build_rows()
    materials = decimal_material_forms(rows)
    hits = evaluate_materials(materials, run_oracles=run_oracles)
    known_controls = {
        plaintext: inverse_decimal_transport(decimal_transport(plaintext))["body"]
        for plaintext in ("lastwordsbeforearchichoice", "thispassword")
    }
    return {
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "source_zero_symbol_counts": {"DBBI": DBBI.count("o"), "FAED": FAED.count("o")},
        "known_transport_controls": {
            plaintext: recovered.decode("ascii")
            for plaintext, recovered in known_controls.items()
        },
        "variant_count": len(rows),
        "rejected_variants": tuple(rejected),
        "rows": tuple({
            "label": row["label"],
            "source": row["source"],
            "source_orientation": row["source_orientation"],
            "byte_orientation": row["byte_orientation"],
            "decimal_digit_count": row["decimal_digit_count"],
            "decimal_zero_count": row["decimal_zero_count"],
            "hex_length": row["hex_length"],
            **row["analysis"],
        } for row in rows),
        "unique_password_material_count": len(materials),
        "material_treatments": ("decoded_raw", "sha256_raw", "sha256_hex"),
        "phase32_positive_control": phase32_positive_control(),
        "hits": hits,
    }


def self_test():
    for plaintext in ("lastwordsbeforearchichoice", "thispassword"):
        encoded = decimal_transport(plaintext)
        decoded = inverse_decimal_transport(encoded)
        assert decoded["rejection"] is None
        assert decoded["body"] == plaintext.encode("ascii")
    report = audit(run_oracles=False)
    assert report["source_lengths"] == {"DBBI": 91, "FAED": 570}
    assert report["source_zero_symbol_counts"] == {"DBBI": 0, "FAED": 0}
    assert report["variant_count"] == 8
    assert report["rejected_variants"] == ()
    assert report["unique_password_material_count"] == 24
    by_label = {row["label"]: row for row in report["rows"]}
    assert by_label["DBBI/forward/bytes_forward"]["byte_length"] == 38
    assert by_label["FAED/forward/bytes_forward"]["byte_length"] == 237
    assert (
        by_label["DBBI/forward/bytes_forward"]["sha256"]
        == "7270ed152fa64b85f144f99b49352ecabeb01c0f0b624fb71cb648f91d1d8b80"
    )
    assert (
        by_label["FAED/forward/bytes_forward"]["sha256"]
        == "7f14db2d90301b8e1d16ff014ad3e84ba75350ef828ad9b8a8a26b1e69302de9"
    )
    assert report["phase32_positive_control"] is True
    print("[*] self-test OK: exact decimal transport and bounded inverse family verified")
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
    by_source = {
        source: [row for row in report["rows"] if row["source"] == source]
        for source in ("DBBI", "FAED")
    }
    print(
        "[*] exact inverse lengths: "
        f"DBBI={by_source['DBBI'][0]['byte_length']} bytes, "
        f"FAED={by_source['FAED'][0]['byte_length']} bytes"
    )
    print(f"[*] bounded variants: {report['variant_count']}")
    print(f"[*] rejected odd-hex variants: {len(report['rejected_variants'])}")
    print(f"[*] unique password materials: {report['unique_password_material_count']}")
    print(f"[*] solved Phase 3.2 control: {report['phase32_positive_control']}")
    print(f"[*] prefix-signature hits: {sum(bool(row['prefix_signatures']) for row in report['rows'])}")
    print(f"[*] exact decompression hits: {sum(bool(row['compression_results']) for row in report['rows'])}")
    print(f"[*] blob-oracle hits: {len(report['hits'])}")


if __name__ == "__main__":
    main()
