#!/usr/bin/env python3
"""Phase 273's "whole stream -> giant decimal -> hex -> ASCII" trick, rerun
under the project's other open a-i digit-mapping convention.

Phase 273 (`decimal_transport_inverse_audit.py`) inverted the page's own
worked decimal-transport examples (``a=1 ... h=8, i=9, o=0``) over the whole
raw DBBI/FAED strings: substitute each symbol for its digit, read the
resulting digit string as one big base-10 integer, convert that integer to
hex, decode the hex as ASCII. Closed negative (calibrated binary-noise
output, 0 blob-oracle hits).

DBBI and FAED only ever use the nine symbols ``a``-``i`` (no ``o``), so
Phase 273's ``a=1 ... i=9`` half of its mapping is exactly this project's
already-swept ``a1i9`` escape-pair digit convention (see `cb_common.MAPS`,
`nibble_packing_audit.MAPS`, `dbbi_base9_bignum_audit.py`). Running the
Phase 273 trick again under `a1i9` therefore reproduces Phase 273's DBBI/FAED
forward bodies byte-for-byte -- this script's self-test asserts that
equality directly against Phase 273's own pinned hashes. It is not new
evidence; it is included only so the two closed audits stay checkably
consistent with each other.

The one cell Phase 273 did not cover is `a0i8` (``a=0 ... i=8``): a
different, equally-open digit convention this project already tracks
(`doc/GSMG_PUZZLE.md`'s "four unknowns"), but never combined with the
giant-decimal-integer trick specifically -- Phase 318's base-9-bignum
audit tested `a0i8`/`a1i9` under different arithmetic (each symbol a base-9
positional digit) and a different exact-match bar (direct secp256k1 key fit
plus raw/decimal/hex passphrase oracle forms), not this base-10-digit-string
construction. `a0i8` produces two bodies (DBBI 38 bytes, FAED 237 bytes)
that do not match any hash on record anywhere else in this project.

Exact-match bar: same as every other passphrase-material audit in this
project -- a successful open against one of the four tracked blobs via
`nibble_packing_audit.evaluate_materials()`'s standard AES family sweep
(CBC/stream/ECB/key-wrap), run against the raw decoded bytes and their
SHA-256 (raw + hex) forms. Printable-byte ratio (strict 0x20-0x7E only, no
tab/newline/CR) is reported for descriptive comparison against the README's
own worked examples (100% printable when decoded correctly) -- it is not
itself a pass/fail gate.
"""

import argparse
import hashlib
import json

from data import DBBI, FAED
from nibble_packing_audit import (
    MAPS,
    analyze_body,
    evaluate_materials,
    phase32_positive_control,
)

PHASE273_KNOWN_HASHES = {
    "DBBI": "7270ed152fa64b85f144f99b49352ecabeb01c0f0b624fb71cb648f91d1d8b80",
    "FAED": "7f14db2d90301b8e1d16ff014ad3e84ba75350ef828ad9b8a8a26b1e69302de9",
}


def strict_printable_ratio(body):
    printable = sum(0x20 <= byte < 0x7F for byte in body)
    return round(printable / len(body), 6) if body else 0.0


def giant_decimal_body(source, map_name):
    table = str.maketrans({symbol: str(value) for symbol, value in MAPS[map_name].items()})
    digits = source.translate(table)
    value = int(digits, 10)
    hexadecimal = f"{value:x}"
    if len(hexadecimal) % 2:
        return None, len(hexadecimal)
    return bytes.fromhex(hexadecimal), len(hexadecimal)


def build_rows():
    rows = []
    rejected = []
    for source_name, source in (("DBBI", DBBI), ("FAED", FAED)):
        for map_name in ("a1i9", "a0i8"):
            body, hex_length = giant_decimal_body(source, map_name)
            label = f"{source_name}/{map_name}"
            if body is None:
                rejected.append({"label": label, "hex_length": hex_length})
                continue
            analysis = analyze_body(body)
            analysis["strict_printable_ratio"] = strict_printable_ratio(body)
            rows.append({
                "label": label,
                "source": source_name,
                "map_name": map_name,
                "body": body,
                "analysis": analysis,
            })
    return rows, rejected


def material_forms(rows):
    registry = {}
    for row in rows:
        body = row["body"]
        digest = hashlib.sha256(body).digest()
        for treatment, material in (
            ("giant_decimal_raw", body),
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
    if set(DBBI) != set("abcdefghi") or set(FAED) != set("abcdefghi"):
        raise AssertionError("DBBI/FAED nine-symbol alphabet changed")
    if len(DBBI) != 91 or len(FAED) != 570:
        raise AssertionError("DBBI/FAED source lengths changed")
    rows, rejected = build_rows()
    materials = material_forms(rows)
    hits = evaluate_materials(materials, run_oracles=run_oracles)
    by_label = {row["label"]: row for row in rows}
    reused_from_phase273 = {
        source: by_label[f"{source}/a1i9"]["analysis"]["sha256"] == PHASE273_KNOWN_HASHES[source]
        for source in ("DBBI", "FAED")
    }
    return {
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "rejected_variants": tuple(rejected),
        "rows": tuple({
            "label": row["label"],
            "source": row["source"],
            "map_name": row["map_name"],
            **row["analysis"],
        } for row in rows),
        "a1i9_reused_from_phase273": reused_from_phase273,
        "unique_password_material_count": len(materials),
        "phase32_positive_control": phase32_positive_control(),
        "hits": hits,
    }


def self_test():
    report = audit(run_oracles=False)
    assert report["source_lengths"] == {"DBBI": 91, "FAED": 570}
    assert report["rejected_variants"] == ()
    assert len(report["rows"]) == 4
    assert report["unique_password_material_count"] == 12
    by_label = {row["label"]: row for row in report["rows"]}

    # a1i9 must reproduce Phase 273's DBBI/FAED forward bodies byte-for-byte:
    # DBBI/FAED only use symbols a-i, so Phase 273's known "a=1..h=8,i=9,o=0"
    # transport table and this project's a1i9 escape-pair convention agree on
    # every symbol these strings actually contain.
    assert report["a1i9_reused_from_phase273"] == {"DBBI": True, "FAED": True}
    assert by_label["DBBI/a1i9"]["sha256"] == PHASE273_KNOWN_HASHES["DBBI"]
    assert by_label["FAED/a1i9"]["sha256"] == PHASE273_KNOWN_HASHES["FAED"]
    assert by_label["DBBI/a1i9"]["byte_length"] == 38
    assert by_label["FAED/a1i9"]["byte_length"] == 237
    assert by_label["DBBI/a1i9"]["strict_printable_ratio"] == 0.421053
    assert by_label["FAED/a1i9"]["strict_printable_ratio"] == 0.329114

    # a0i8 is the genuinely new cell: distinct bytes, distinct hashes.
    assert by_label["DBBI/a0i8"]["byte_length"] == 38
    assert by_label["FAED/a0i8"]["byte_length"] == 237
    assert by_label["DBBI/a0i8"]["sha256"] == (
        "38f51afc69242ea4a9a6ab7e9f05166956f66b24820e91c835abed48e138b920"
    )
    assert by_label["FAED/a0i8"]["sha256"] == (
        "4eb87c8314f06db20cc88ced00895535c2d3a59ccce81b1520d570a0965a4c6b"
    )
    assert by_label["DBBI/a0i8"]["strict_printable_ratio"] == 0.394737
    assert by_label["FAED/a0i8"]["strict_printable_ratio"] == 0.295359
    assert report["phase32_positive_control"] is True
    print("[*] self-test OK: a1i9 reproduces Phase 273 exactly; a0i8 is new and distinct")
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
    for row in report["rows"]:
        reused = (
            " (== Phase 273)"
            if row["map_name"] == "a1i9" and report["a1i9_reused_from_phase273"][row["source"]]
            else ""
        )
        print(
            f"[*] {row['label']:10s} bytes={row['byte_length']:4d} "
            f"printable={row['strict_printable_ratio']*100:5.1f}% "
            f"sha256={row['sha256']}{reused}"
        )
    print(f"[*] unique password materials: {report['unique_password_material_count']}")
    print(f"[*] solved Phase 3.2 control: {report['phase32_positive_control']}")
    print(f"[*] blob-oracle hits: {len(report['hits'])}")


if __name__ == "__main__":
    main()
