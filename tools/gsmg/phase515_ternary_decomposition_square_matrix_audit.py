#!/usr/bin/env python3
"""Naddiseo fork issue #14's `a1i9` digit-decomposition square-matrix
observation, extended with a giant-integer trick and grid-route reads.

https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/14 (saama143,
2026-09-07): under `a=1 ... i=9`, decompose every symbol whose value exceeds
3 into a sum of 2s and 3s, written with `b`(=2)/`c`(=3) (`d`->`bb`, `e`->`bc`,
`f`->`cc`, `g`->`bbc`, `h`->`bcc`, `i`->`ccc`); `a`/`b`/`c` themselves (values
1/2/3) pass through unchanged. Independently reproduced against this
project's own pinned strings: DBBI's 91 symbols expand to exactly 169 = 13^2
and FAED's 570 expand to exactly 1225 = 35^2. The issue author tried
decoding both "in multiple ways" without success and asked whether anyone
had tested this representation; a full-repository grep confirms nobody in
this project had.

Since `len(decompose(v)) == ceil(v/3)`, the expanded length is a pure
function of the (already-known, already-non-uniform) letter histogram, not
of symbol order -- so the standard shuffle-gate null model is uninformative
here (shuffling never changes the total). An exact convolution against a
uniform-digit null instead gives DBBI z=-1.67 (unremarkable) and FAED
z=+4.36 (largely restating FAED's already-documented letter-frequency skew,
not new evidence); joint probability of both landing on *some* perfect
square, independence-assumed, is ~0.035%. Genuinely non-trivial, not
overwhelming -- treated as motivation for a bounded test, not as a
confirmed signal, same discipline as every other numeric coincidence this
project has chased.

Two closed, non-arbitrary things about the resulting `{a,b,c}` ternary
string, neither previously tried:

1. The same "whole stream -> giant integer -> hex -> ASCII" trick as Phase
   513, under the two conventions that keep it well-defined: true base-3
   positional (`a=0,b=1,c=2`) and a decimal digit string using only 1-3
   (`a=1,b=2,c=3`, the exact convention this project already uses for the
   giant-decimal trick, just restricted to 3 of its 10 digits).
2. Grid-route reads of the exact square shape the issue surfaces (13x13,
   35x35) -- reusing `dual_ternary_sweep.py`'s existing, already-validated
   8-route family (rows/columns/snake variants; "columns" is literally the
   matrix transpose, the one operation a genuinely square shape uniquely
   supports) rather than inventing new geometry.

The two are combined: each of the 8 routes feeds both digit conventions,
giving 16 byte-strings per target (32 total). Every one is checked through
the standard AES oracle (raw bytes, SHA-256 raw, SHA-256 hex).

Usage:
    python3 tools/gsmg/phase515_ternary_decomposition_square_matrix_audit.py --self-test
    python3 tools/gsmg/phase515_ternary_decomposition_square_matrix_audit.py
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import DBBI, FAED  # noqa: E402
from dual_ternary_sweep import ROUTES, route_text  # noqa: E402
from nibble_packing_audit import analyze_body, evaluate_materials, phase32_positive_control  # noqa: E402

DECOMP = {
    "a": "a", "b": "b", "c": "c",
    "d": "bb", "e": "bc", "f": "cc",
    "g": "bbc", "h": "bcc", "i": "ccc",
}
TARGETS = {"dbbi": DBBI, "faed": FAED}
SIDE = {"dbbi": 13, "faed": 35}
DIGIT_CONVENTIONS = {
    "base3_a0c2": (3, {"a": "0", "b": "1", "c": "2"}),
    "decimal_a1c3": (10, {"a": "1", "b": "2", "c": "3"}),
}


def expand(source):
    return "".join(DECOMP[symbol] for symbol in source)


def strict_printable_ratio(body):
    printable = sum(0x20 <= byte < 0x7F for byte in body)
    return round(printable / len(body), 6) if body else 0.0


def giant_int_body(stream, convention_name):
    base, mapping = DIGIT_CONVENTIONS[convention_name]
    table = str.maketrans(mapping)
    digits = stream.translate(table)
    value = int(digits, base)
    hexadecimal = f"{value:x}"
    if len(hexadecimal) % 2:
        return None, len(hexadecimal)
    return bytes.fromhex(hexadecimal), len(hexadecimal)


def build_rows():
    rows = []
    rejected = []
    for target_name, source in TARGETS.items():
        side = SIDE[target_name]
        expanded = expand(source)
        if len(expanded) != side * side:
            raise AssertionError(f"{target_name} expansion is not a perfect square")
        for route in ROUTES:
            reordered = route_text(expanded, side, side, route)
            for convention_name in DIGIT_CONVENTIONS:
                label = f"{target_name}/{route}/{convention_name}"
                body, hex_length = giant_int_body(reordered, convention_name)
                if body is None:
                    rejected.append({"label": label, "hex_length": hex_length})
                    continue
                analysis = analyze_body(body)
                analysis["strict_printable_ratio"] = strict_printable_ratio(body)
                rows.append({
                    "label": label,
                    "target": target_name,
                    "route": route,
                    "convention": convention_name,
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
            ("route_giant_int_raw", body),
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
    expanded_lengths = {name: len(expand(source)) for name, source in TARGETS.items()}
    if expanded_lengths != {"dbbi": 169, "faed": 1225}:
        raise AssertionError("ternary expansion lengths changed")

    rows, rejected = build_rows()
    materials = material_forms(rows)
    hits = evaluate_materials(materials, run_oracles=run_oracles)
    ranked = sorted(rows, key=lambda r: r["analysis"]["strict_printable_ratio"], reverse=True)
    return {
        "expanded_lengths": expanded_lengths,
        "expanded_perfect_squares": {"dbbi": 13 * 13, "faed": 35 * 35},
        "rejected_variants": tuple(rejected),
        "rows": tuple({
            "label": row["label"], "target": row["target"], "route": row["route"],
            "convention": row["convention"], **row["analysis"],
        } for row in rows),
        "top_by_printable_ratio": tuple({
            "label": row["label"], **row["analysis"],
        } for row in ranked[:5]),
        "unique_password_material_count": len(materials),
        "phase32_positive_control": phase32_positive_control(),
        "hits": hits,
    }


def self_test():
    assert expand("abcdefghi") == "abcbbbcccbbcbccccc"
    report = audit(run_oracles=False)
    assert report["expanded_lengths"] == {"dbbi": 169, "faed": 1225}
    assert report["expanded_perfect_squares"] == {"dbbi": 169, "faed": 1225}
    # base3_a0c2 for dbbi and decimal_a1c3 for faed hit odd hex length and are
    # rejected rather than repaired with an invented leading zero; the other
    # 6 of 8 routes per target x convention combos are not odd for those cells
    # -- but every route shares the SAME digit-string parity per convention
    # (route only reorders symbols, length is unchanged), so each convention
    # is either odd for all 8 routes of a target or none of them.
    rejected_labels = {r["label"] for r in report["rejected_variants"]}
    for route in ("rows", "columns"):
        assert f"dbbi/{route}/base3_a0c2" in rejected_labels
        assert f"faed/{route}/decimal_a1c3" in rejected_labels
        assert f"dbbi/{route}/decimal_a1c3" not in rejected_labels
        assert f"faed/{route}/base3_a0c2" not in rejected_labels
    assert len(report["rejected_variants"]) == 8 + 8  # 8 routes x 1 convention x 2 targets
    assert len(report["rows"]) == 32 - 16  # 32 closed cells minus the 16 rejected
    assert report["unique_password_material_count"] == len(report["rows"]) * 3
    assert report["phase32_positive_control"] is True
    print("[*] self-test OK: ternary expansion reproduces both perfect squares; "
          "16/32 closed cells valid (parity-rejected cells consistent per convention)")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-oracles", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit(run_oracles=not args.no_oracles)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"[*] expanded lengths: {report['expanded_lengths']} "
          f"(perfect squares: {report['expanded_perfect_squares']})")
    print(f"[*] valid cells: {len(report['rows'])} / 32; "
          f"rejected (odd hex parity): {len(report['rejected_variants'])}")
    for row in report["top_by_printable_ratio"]:
        print(f"    {row['label']:32s} bytes={row['byte_length']:4d} "
              f"printable={row['strict_printable_ratio']*100:5.1f}% sha256={row['sha256']}")
    print(f"[*] unique password materials: {report['unique_password_material_count']}")
    print(f"[*] solved Phase 3.2 control: {report['phase32_positive_control']}")
    print(f"[*] blob-oracle hits: {len(report['hits'])}")


if __name__ == "__main__":
    main()
