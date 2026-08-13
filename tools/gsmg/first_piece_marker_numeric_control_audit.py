#!/usr/bin/env python3
"""Close Point 7's queued 254/56 numeric-registry extension.

The exact arithmetic screen uses the Phase-149 operation family: sum,
absolute difference, product, both decimal concatenations, and exact integer
division.  Algebraic restatements of the same additive or multiplicative
triple count once.  Distinctiveness is calibrated over all 256 possible byte
values against the fixed original 20-number registry; this is the native
comparison family for repeated grayscale channel bytes.
"""

import argparse
from collections import Counter, defaultdict

from numeric_coincidence_triage import NUMBERS, PHASE_149_NAMES


def legacy_registry():
    return {name: NUMBERS[name] for name in PHASE_149_NAMES}


def relation_signatures(candidate, registry):
    by_value = defaultdict(list)
    for name, (value, _provenance) in registry.items():
        by_value[value].append(name)

    relations = {}
    for operand_name, (operand, _provenance) in registry.items():
        lo, hi = sorted((candidate, operand))
        candidates = (
            ("sum", candidate + operand),
            ("abs_diff", abs(candidate - operand)),
            ("product", candidate * operand),
            ("concat_candidate_operand", int(f"{candidate}{operand}")),
            ("concat_operand_candidate", int(f"{operand}{candidate}")),
            ("exact_division", hi // lo if lo and hi % lo == 0 else None),
        )
        for operation, result in candidates:
            if result is None:
                continue
            matches = tuple(
                name for name in by_value.get(result, ()) if name != operand_name
            )
            if not matches:
                continue
            if operation in ("sum", "abs_diff"):
                signature = ("additive", tuple(sorted((candidate, operand, result))))
            elif operation in ("product", "exact_division"):
                signature = (
                    "multiplicative",
                    tuple(sorted((candidate, operand, result))),
                )
            else:
                signature = (operation, candidate, operand, result)
            relations[signature] = {
                "signature": signature,
                "operand_name": operand_name,
                "operand": operand,
                "operation": operation,
                "result": result,
                "matches": matches,
            }
    return tuple(relations[key] for key in sorted(relations, key=str))


def audit():
    registry = legacy_registry()
    controls = tuple(
        len(relation_signatures(candidate, registry)) for candidate in range(256)
    )
    markers = {}
    for name in ("FEFE_CHANNEL", "SHADOW_CHANNEL"):
        value = NUMBERS[name][0]
        relations = relation_signatures(value, registry)
        count = len(relations)
        tail_count = sum(control_count >= count for control_count in controls)
        markers[name] = {
            "value": value,
            "hex": f"{value:02X}",
            "ascii_if_printable": chr(value) if 32 <= value <= 126 else None,
            "relations": relations,
            "deduplicated_relation_count": count,
            "byte_family_tail_count": tail_count,
            "byte_family_size": len(controls),
            "byte_family_tail_rate": tail_count / len(controls),
        }
    return {
        "legacy_registry_size": len(registry),
        "extended_registry_size": len(NUMBERS),
        "operation_family": (
            "sum",
            "absolute_difference",
            "product",
            "decimal_concatenation_both_orders",
            "exact_integer_division",
        ),
        "byte_control_histogram": tuple(sorted(Counter(controls).items())),
        "markers": markers,
        "promoted": False,
        "oracle_run": False,
    }


def self_test():
    report = audit()
    assert report["legacy_registry_size"] == 20
    assert report["extended_registry_size"] == 22
    fefe = report["markers"]["FEFE_CHANNEL"]
    shadow = report["markers"]["SHADOW_CHANNEL"]
    assert fefe["hex"] == "FE" and fefe["ascii_if_printable"] is None
    assert shadow["hex"] == "38" and shadow["ascii_if_printable"] == "8"
    assert fefe["deduplicated_relation_count"] == 1
    assert fefe["relations"][0]["signature"] == ("additive", (91, 163, 254))
    assert fefe["byte_family_tail_count"] == 147
    assert shadow["deduplicated_relation_count"] == 2
    assert {row["signature"] for row in shadow["relations"]} == {
        ("additive", (7, 56, 63)),
        ("additive", (24, 56, 80)),
    }
    assert shadow["byte_family_tail_count"] == 70
    assert report["byte_control_histogram"] == (
        (0, 109),
        (1, 77),
        (2, 40),
        (3, 18),
        (4, 9),
        (5, 1),
        (6, 2),
    )
    assert not report["promoted"] and not report["oracle_run"]
    print("[*] self-test OK: Point 7 registry extension is calibrated and negative")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    print(
        f"[*] registry: {report['legacy_registry_size']} -> "
        f"{report['extended_registry_size']} values"
    )
    for name, marker in report["markers"].items():
        print(
            f"[*] {name}={marker['value']} (0x{marker['hex']}): "
            f"{marker['deduplicated_relation_count']} relation(s), "
            f"byte-family tail={marker['byte_family_tail_count']}/"
            f"{marker['byte_family_size']} "
            f"({marker['byte_family_tail_rate']:.6f})"
        )
        for relation in marker["relations"]:
            print(f"    {relation['signature']}")


if __name__ == "__main__":
    main()
