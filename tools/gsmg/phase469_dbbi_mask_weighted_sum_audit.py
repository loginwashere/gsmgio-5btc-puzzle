#!/usr/bin/env python3
"""Phase 469: bounded DBBI 7x13 selected-mask weighted-sum audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data import DBBI
from denis_prime_extraction_audit import SOURCE, TARGET
from flo_prime_walk_provenance_audit import EXPECTED_FLO_POSITIONS_1_INDEXED

SCRIPT_DIR = Path(__file__).resolve().parent
RESULT_PATH = SCRIPT_DIR / "phase469_result.json"

SHAPES = ((7, 13), (13, 7))
PARTITIONS = ("selected", "complement", "all")
MAPS = {
    "dbbi_a0i8": {c: i for i, c in enumerate("abcdefghi")},
    "dbbi_a1i9": {c: i + 1 for i, c in enumerate("abcdefghi")},
    "plain_a0z25": {c: i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
    "plain_a1z26": {c: i + 1 for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
}
CLUE_WORDS = ("yin", "yang", "matrix", "sum", "list", "seed", "key", "enter", "password")
KNOWN_LISTS = ((23, 16, 7), (7, 13), (13, 7))


def reshape(values, rows: int, columns: int):
    if len(values) != rows * columns:
        raise ValueError("shape does not fit values")
    return tuple(tuple(values[r * columns:(r + 1) * columns]) for r in range(rows))


def axis_sums(values, include, rows: int, columns: int) -> dict:
    value_grid = reshape(values, rows, columns)
    mask_grid = reshape(include, rows, columns)
    row_sums = tuple(
        sum(value for value, keep in zip(value_row, mask_row) if keep)
        for value_row, mask_row in zip(value_grid, mask_grid)
    )
    column_sums = tuple(
        sum(value_grid[r][c] for r in range(rows) if mask_grid[r][c])
        for c in range(columns)
    )
    return {"rows": row_sums, "columns": column_sums, "total": sum(row_sums)}


def direct_a1z26(values) -> str | None:
    if not all(1 <= value <= 26 for value in values):
        return None
    return "".join(chr(64 + value) for value in values)


def decorate(sums: dict) -> dict:
    result = dict(sums)
    for axis in ("rows", "columns"):
        values = sums[axis]
        text = direct_a1z26(values)
        result[f"{axis}_a1z26_direct"] = text
        result[f"{axis}_clue_hits"] = tuple(
            word for word in CLUE_WORDS if text is not None and word in text.lower()
        )
        result[f"{axis}_known_list_matches"] = tuple(
            known for known in KNOWN_LISTS if values == known
        )
    return result


def symbol_counts(symbols: str, include, rows: int, columns: int, symbol: str) -> dict:
    values = tuple(1 if c == symbol else 0 for c in symbols)
    return axis_sums(values, include, rows, columns)


def build_report() -> dict:
    selected_positions = frozenset(EXPECTED_FLO_POSITIONS_1_INDEXED)
    selected = tuple(i in selected_positions for i in range(1, len(DBBI) + 1))
    masks = {
        "selected": selected,
        "complement": tuple(not value for value in selected),
        "all": tuple(True for _ in selected),
    }
    report = {
        "phase": 469,
        "source_lengths": {"dbbi": len(DBBI), "aligned_plaintext": len(SOURCE)},
        "selected_position_count": sum(selected),
        "selected_dbbi_symbols": "".join(c for c, keep in zip(DBBI, selected) if keep),
        "shapes": {},
        "password_materials_generated": 0,
        "decryptions_attempted": 0,
        "oracle_calls": 0,
    }
    selected_plaintext = "".join(c for c, keep in zip(SOURCE, selected) if keep)
    if selected_plaintext != TARGET:
        raise AssertionError("frozen position tuple no longer reproduces TARGET")
    sources = {"dbbi": DBBI, "plain": SOURCE}
    map_names = {"dbbi": ("dbbi_a0i8", "dbbi_a1i9"), "plain": ("plain_a0z25", "plain_a1z26")}
    for rows, columns in SHAPES:
        shape_key = f"{rows}x{columns}"
        shape_result = {"partitions": {}, "selected_escape_counts": {}}
        for partition in PARTITIONS:
            partition_result = {}
            for source_name, source in sources.items():
                for map_name in map_names[source_name]:
                    values = tuple(MAPS[map_name][c] for c in source)
                    partition_result[map_name] = decorate(
                        axis_sums(values, masks[partition], rows, columns)
                    )
            shape_result["partitions"][partition] = partition_result
        for symbol in ("b", "e"):
            shape_result["selected_escape_counts"][symbol] = decorate(
                symbol_counts(DBBI, selected, rows, columns, symbol)
            )
        report["shapes"][shape_key] = shape_result
    return report


def structural_self_test() -> None:
    assert reshape(tuple(range(6)), 2, 3) == ((0, 1, 2), (3, 4, 5))
    assert axis_sums((1, 2, 3, 4), (True, False, True, True), 2, 2) == {
        "rows": (1, 7), "columns": (4, 4), "total": 8
    }
    assert direct_a1z26((1, 26, 3)) == "AZC"
    assert direct_a1z26((0, 1)) is None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--structural-only", action="store_true")
    args = parser.parse_args()
    structural_self_test()
    if args.structural_only:
        print("[*] Phase 469 structural self-test OK")
        return
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    leads = []
    for shape, shape_result in report["shapes"].items():
        for partition, partition_result in shape_result["partitions"].items():
            for map_name, result in partition_result.items():
                for axis in ("rows", "columns"):
                    if result[f"{axis}_clue_hits"] or result[f"{axis}_known_list_matches"]:
                        leads.append({
                            "shape": shape, "partition": partition, "map": map_name,
                            "axis": axis, "values": result[axis],
                            "text": result[f"{axis}_a1z26_direct"],
                            "clue_hits": result[f"{axis}_clue_hits"],
                            "known_list_matches": result[f"{axis}_known_list_matches"],
                        })
    print(json.dumps({"selected_position_count": report["selected_position_count"], "leads": leads}, indent=2))


if __name__ == "__main__":
    main()

