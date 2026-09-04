#!/usr/bin/env python3
"""Phase 471: DBBI route canonicalization census and structure diagnostics.

Purely diagnostic: no password materials, no decryptions, no oracle calls,
no plaintext alignment, no FAED usage. See the frozen Phase 471 protocol.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from data import DBBI

SCRIPT_DIR = Path(__file__).resolve().parent
RESULT_PATH = SCRIPT_DIR / "phase471_result.json"

N = 91
SHAPES = ((7, 13), (13, 7))
VALUES = {c: i for i, c in enumerate("abcdefghi")}
N_SHUFFLES = 10000
RNG_SEED = 471
CALIBRATED_FAMILY_SIZE = 17
CALIBRATED_ALPHA = 0.001 / CALIBRATED_FAMILY_SIZE

MASK_NAMES = tuple("abcdefghi") + ("be", "odd")
OFFSETS = ((0, 1), (1, 0), (1, 1), (1, -1), (2, 0), (0, 2))

SEGMENTS = "abcdefg"
SEVEN_SEGMENT_TABLE = {
    frozenset(s): glyph
    for glyph, s in {
        "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
        "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
        "A": "abcefg", "b": "cdefg", "C": "adef", "d": "bcdeg",
        "E": "adefg", "F": "aefg",
    }.items()
}


# ---------------------------------------------------------------- geometry

def cell_index(r: int, c: int, columns: int) -> int:
    return r * columns + c


def rectangle_routes(rows: int, columns: int) -> dict:
    """The sixteen frozen rectangle reads as coordinate lists."""
    routes = {}
    routes["rows"] = [(r, c) for r in range(rows) for c in range(columns)]
    routes["rows_each_reversed"] = [
        (r, c) for r in range(rows) for c in reversed(range(columns))
    ]
    routes["rows_reverse_row_order"] = [
        (r, c) for r in reversed(range(rows)) for c in range(columns)
    ]
    routes["cols"] = [(r, c) for c in range(columns) for r in range(rows)]
    routes["cols_each_reversed"] = [
        (r, c) for c in range(columns) for r in reversed(range(rows))
    ]
    routes["cols_reverse_col_order"] = [
        (r, c) for c in reversed(range(columns)) for r in range(rows)
    ]
    routes["rot180"] = [
        (r, c) for r in reversed(range(rows)) for c in reversed(range(columns))
    ]
    routes["boustro_rows_lr"] = [
        (r, c) for r in range(rows)
        for c in (range(columns) if r % 2 == 0 else reversed(range(columns)))
    ]
    routes["boustro_rows_rl"] = [
        (r, c) for r in range(rows)
        for c in (reversed(range(columns)) if r % 2 == 0 else range(columns))
    ]
    routes["boustro_cols_tb"] = [
        (r, c) for c in range(columns)
        for r in (range(rows) if c % 2 == 0 else reversed(range(rows)))
    ]
    routes["boustro_cols_bt"] = [
        (r, c) for c in range(columns)
        for r in (reversed(range(rows)) if c % 2 == 0 else range(rows))
    ]
    routes["diag_nwse"] = [
        (r, r + s) for s in range(-(rows - 1), columns)
        for r in range(rows) if 0 <= r + s < columns
    ]
    routes["antidiag"] = [
        (r, s - r) for s in range(rows + columns - 1)
        for r in range(rows) if 0 <= s - r < columns
    ]
    routes["spiral_in_cw"] = spiral(rows, columns, clockwise=True)
    routes["spiral_in_ccw"] = spiral(rows, columns, clockwise=False)
    routes["spiral_out_cw"] = list(reversed(routes["spiral_in_cw"]))
    routes["spiral_out_ccw"] = list(reversed(routes["spiral_in_ccw"]))
    return routes


def spiral(rows: int, columns: int, clockwise: bool) -> list:
    if clockwise:
        directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
    else:
        directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    seen = set()
    r = c = 0
    d = 0
    path = []
    for _ in range(rows * columns):
        path.append((r, c))
        seen.add((r, c))
        nr, nc = r + directions[d][0], c + directions[d][1]
        if not (0 <= nr < rows and 0 <= nc < columns and (nr, nc) not in seen):
            d = (d + 1) % 4
            nr, nc = r + directions[d][0], c + directions[d][1]
        r, c = nr, nc
    return path


def toroidal_route(rows, columns, r0, c0, dr, dc) -> tuple:
    return tuple(
        cell_index((r0 + k * dr) % rows, (c0 + k * dc) % columns, columns)
        for k in range(rows * columns)
    )


def route_census() -> dict:
    all_perms = set()
    all_strings = set()
    per_family = {}

    def add(family: str, perm: tuple) -> None:
        if sorted(perm) != list(range(N)):
            raise AssertionError(f"route in {family} is not a permutation")
        all_perms.add(perm)
        text = "".join(DBBI[i] for i in perm)
        all_strings.add(text)
        bucket = per_family.setdefault(family, {"perms": set(), "strings": set()})
        bucket["perms"].add(perm)
        bucket["strings"].add(text)

    for rows, columns in SHAPES:
        family = f"rectangle_{rows}x{columns}"
        for coords in rectangle_routes(rows, columns).values():
            add(family, tuple(cell_index(r, c, columns) for r, c in coords))
        family = f"toroidal_{rows}x{columns}"
        for dr in range(1, rows):
            for dc in range(1, columns):
                for r0 in range(rows):
                    for c0 in range(columns):
                        add(family, toroidal_route(rows, columns, r0, c0, dr, dc))
    for a in range(1, N):
        if a % 7 == 0 or a % 13 == 0:
            continue
        for b in range(N):
            add("linear_mod91", tuple((a * n + b) % N for n in range(N)))

    linear_strings = per_family["linear_mod91"]["strings"]
    toroidal_7x13_strings = per_family["toroidal_7x13"]["strings"]
    report = {
        "total_routes_enumerated": sum(
            len(v["perms"]) for v in per_family.values()
        ),
        "unique_permutations": len(all_perms),
        "unique_output_strings": len(all_strings),
        "identity_string_present": DBBI in all_strings,
        "families": {
            name: {
                "unique_permutations": len(v["perms"]),
                "unique_output_strings": len(v["strings"]),
            }
            for name, v in sorted(per_family.items())
        },
        "crt_claim_linear_equals_toroidal_7x13_strings":
            linear_strings == toroidal_7x13_strings,
        "linear_toroidal_string_overlap":
            len(linear_strings & toroidal_7x13_strings),
    }
    return report


# ------------------------------------------------------------------- masks

def mask_bits(name: str) -> tuple:
    if name == "be":
        return tuple(1 if c in "be" else 0 for c in DBBI)
    if name == "odd":
        return tuple(VALUES[c] % 2 for c in DBBI)
    return tuple(1 if c == name else 0 for c in DBBI)


def render_mask(bits, rows: int, columns: int) -> list:
    return [
        "".join("#" if bits[cell_index(r, c, columns)] else "." for c in range(columns))
        for r in range(rows)
    ]


# ----------------------------------------------------------- seven-segment

def seven_segment_readings() -> list:
    readings = []
    for mask_name in MASK_NAMES:
        bits = mask_bits(mask_name)
        for shape_name, glyph_states in (
            ("7x13_columns", [
                tuple(bits[cell_index(r, j, 13)] for r in range(7))
                for j in range(13)
            ]),
            ("13x7_rows", [
                tuple(bits[cell_index(i, k, 7)] for k in range(7))
                for i in range(13)
            ]),
        ):
            for order_name, order in (("forward", range(7)), ("reversed", reversed(range(7)))):
                order = tuple(order)
                for polarity in (1, 0):
                    glyphs = []
                    valid = 0
                    for state in glyph_states:
                        on = frozenset(
                            SEGMENTS[pos]
                            for pos, source in enumerate(order)
                            if state[source] == polarity
                        )
                        glyph = SEVEN_SEGMENT_TABLE.get(on)
                        glyphs.append(glyph if glyph is not None else "?")
                        valid += glyph is not None
                    readings.append({
                        "mask": mask_name, "orientation": shape_name,
                        "segment_order": order_name, "on_polarity": polarity,
                        "valid_glyphs": valid,
                        "decoded": "".join(glyphs),
                        "exact_bar_met": valid == 13,
                    })
    return readings


# ------------------------------------------------------------ finite fields

def gf_tables(p: int):
    add = [[(x + y) % p for y in range(p)] for x in range(p)]
    mul = [[(x * y) % p for y in range(p)] for x in range(p)]
    inv = [0] * p
    for x in range(1, p):
        inv[x] = next(y for y in range(1, p) if x * y % p == 1)
    return add, mul, inv


def gf9_tables():
    """GF(9) = GF(3)[x]/(x^2+1); element h*x + l encoded as 3*h + l."""
    def mul_elem(u, v):
        hu, lu = divmod(u, 3)
        hv, lv = divmod(v, 3)
        high = (hu * lv + lu * hv) % 3
        low = (lu * lv + 2 * hu * hv) % 3  # x^2 = -1 = 2
        return 3 * high + low

    add = [[3 * ((x // 3 + y // 3) % 3) + (x % 3 + y % 3) % 3 for y in range(9)]
           for x in range(9)]
    mul = [[mul_elem(x, y) for y in range(9)] for x in range(9)]
    inv = [0] * 9
    for x in range(1, 9):
        inv[x] = next(y for y in range(1, 9) if mul[x][y] == 1)
    return add, mul, inv


def matrix_rank(cells, rows: int, columns: int, tables) -> int:
    add, mul, inv = tables
    neg = [next(y for y in range(len(add)) if add[x][y] == 0) for x in range(len(add))]
    grid = [list(cells[r * columns:(r + 1) * columns]) for r in range(rows)]
    rank = 0
    for col in range(columns):
        pivot = next((r for r in range(rank, rows) if grid[r][col] != 0), None)
        if pivot is None:
            continue
        grid[rank], grid[pivot] = grid[pivot], grid[rank]
        scale = inv[grid[rank][col]]
        grid[rank] = [mul[scale][v] for v in grid[rank]]
        for r in range(rows):
            if r != rank and grid[r][col] != 0:
                factor = neg[grid[r][col]]
                grid[r] = [add[v][mul[factor][w]] for v, w in zip(grid[r], grid[rank])]
        rank += 1
        if rank == rows:
            break
    return rank


GF2 = gf_tables(2)
GF3 = gf_tables(3)
GF9 = gf9_tables()

RANK_STATS = (
    ("rank_gf2_parity", GF2, lambda values: [v % 2 for v in values]),
    ("rank_gf2_be", GF2, None),  # placeholder handled in rank_vector
    ("rank_gf3_mod3", GF3, lambda values: [v % 3 for v in values]),
    ("rank_gf3_high_trit", GF3, lambda values: [v // 3 for v in values]),
    ("rank_gf9_full", GF9, lambda values: list(values)),
)


def rank_vector(symbols) -> dict:
    values = [VALUES[c] for c in symbols]
    out = {}
    for name, tables, transform in RANK_STATS:
        if name == "rank_gf2_be":
            cells = [1 if c in "be" else 0 for c in symbols]
        else:
            cells = transform(values)
        out[name] = matrix_rank(cells, 7, 13, tables)
    return out


# ---------------------------------------------------------- offset statistics

def offset_permutations() -> dict:
    perms = {}
    for dr, dc in OFFSETS:
        perms[(dr, dc)] = tuple(
            cell_index((r + dr) % 7, (c + dc) % 13, 13)
            for r in range(7) for c in range(13)
        )
    return perms


OFFSET_PERMS = offset_permutations()


def offset_vector(symbols) -> dict:
    be = [1 if c in "be" else 0 for c in symbols]
    out = {}
    for (dr, dc), perm in OFFSET_PERMS.items():
        out[f"match_full_{dr}_{dc}"] = sum(
            symbols[i] == symbols[perm[i]] for i in range(N)
        )
        out[f"match_be_{dr}_{dc}"] = sum(be[i] == be[perm[i]] for i in range(N))
    return out


def calibrate() -> dict:
    observed = {**rank_vector(DBBI), **offset_vector(DBBI)}
    rng = random.Random(RNG_SEED)
    pool = list(DBBI)
    tallies = {name: [] for name in observed}
    for _ in range(N_SHUFFLES):
        rng.shuffle(pool)
        shuffled = "".join(pool)
        sample = {**rank_vector(shuffled), **offset_vector(shuffled)}
        for name, value in sample.items():
            tallies[name].append(value)
    results = {}
    for name, obs in observed.items():
        values = tallies[name]
        le = sum(v <= obs for v in values) / N_SHUFFLES
        ge = sum(v >= obs for v in values) / N_SHUFFLES
        two_sided = min(1.0, 2 * min(le, ge))
        results[name] = {
            "observed": obs,
            "null_min": min(values), "null_max": max(values),
            "null_mean": sum(values) / N_SHUFFLES,
            "p_le": le, "p_ge": ge, "p_two_sided": two_sided,
            "lead": two_sided < CALIBRATED_ALPHA,
        }
    return results


# --------------------------------------------------------------- packings

def printable(byte_values) -> bool:
    return all(0x20 <= b <= 0x7E for b in byte_values)


def base9_readings() -> list:
    readings = []
    values = [VALUES[c] for c in DBBI]
    for rows, columns in SHAPES:
        lines = {
            "rows": [
                [values[cell_index(r, c, columns)] for c in range(columns)]
                for r in range(rows)
            ],
            "cols": [
                [values[cell_index(r, c, columns)] for r in range(rows)]
                for c in range(columns)
            ],
        }
        for axis, line_list in lines.items():
            for order_name in ("forward", "reversed"):
                rendered = []
                all_printable = True
                for digits in line_list:
                    if order_name == "reversed":
                        digits = digits[::-1]
                    number = 0
                    for digit in digits:
                        number = number * 9 + digit
                    raw = number.to_bytes(max(1, (number.bit_length() + 7) // 8), "big")
                    ok = printable(raw)
                    all_printable = all_printable and ok
                    rendered.append(raw.decode("ascii") if ok else raw.hex())
                readings.append({
                    "shape": f"{rows}x{columns}", "axis": axis,
                    "digit_order": order_name,
                    "lines_rendered": rendered,
                    "exact_bar_met": all_printable,
                })
    return readings


def bitmask_readings() -> list:
    readings = []
    for mask_name in ("b", "e", "be"):
        bits = mask_bits(mask_name)
        for shape_name, line_states in (
            ("7x13_columns", [
                [bits[cell_index(r, j, 13)] for r in range(7)] for j in range(13)
            ]),
            ("13x7_rows", [
                [bits[cell_index(i, k, 7)] for k in range(7)] for i in range(13)
            ]),
        ):
            for order_name in ("msb_first", "lsb_first"):
                for polarity in (1, 0):
                    byte_values = []
                    for state in line_states:
                        ordered = state if order_name == "msb_first" else state[::-1]
                        value = 0
                        for bit in ordered:
                            value = value * 2 + (1 if bit == polarity else 0)
                        byte_values.append(value)
                    ok = printable(byte_values)
                    readings.append({
                        "mask": mask_name, "orientation": shape_name,
                        "bit_order": order_name, "on_polarity": polarity,
                        "values": byte_values,
                        "ascii": "".join(map(chr, byte_values)) if ok else None,
                        "exact_bar_met": ok,
                    })
    return readings


# ------------------------------------------------------------------ report

def build_report() -> dict:
    if len(DBBI) != N or set(DBBI) != set("abcdefghi"):
        raise AssertionError("canonical DBBI stream changed")
    seven_segment = seven_segment_readings()
    base9 = base9_readings()
    bitmask = bitmask_readings()
    calibration = calibrate()
    report = {
        "phase": 471,
        "rng_seed": RNG_SEED,
        "n_shuffles": N_SHUFFLES,
        "calibrated_family_size": CALIBRATED_FAMILY_SIZE,
        "calibrated_alpha_per_test": CALIBRATED_ALPHA,
        "route_census": route_census(),
        "mask_renderings": {
            name: {
                f"{rows}x{columns}": render_mask(mask_bits(name), rows, columns)
                for rows, columns in SHAPES
            }
            for name in MASK_NAMES
        },
        "seven_segment": seven_segment,
        "calibration": calibration,
        "base9_line_packing": base9,
        "be_bitmask_readings": bitmask,
        "leads": {
            "seven_segment_exact": [x for x in seven_segment if x["exact_bar_met"]],
            "base9_exact": [x for x in base9 if x["exact_bar_met"]],
            "bitmask_exact": [x for x in bitmask if x["exact_bar_met"]],
            "calibrated": {
                name: stats for name, stats in calibration.items() if stats["lead"]
            },
        },
        "password_materials_generated": 0,
        "decryptions_attempted": 0,
        "oracle_calls": 0,
    }
    return report


def structural_self_test() -> None:
    assert spiral(3, 3, clockwise=True) == [
        (0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (1, 1)
    ]
    perm = toroidal_route(7, 13, 0, 0, 1, 1)
    assert sorted(perm) == list(range(91))
    assert SEVEN_SEGMENT_TABLE[frozenset("abcdefg")] == "8"
    assert SEVEN_SEGMENT_TABLE[frozenset("bc")] == "1"
    identity3 = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert matrix_rank(identity3, 3, 3, GF3) == 3
    assert matrix_rank([0] * 9, 3, 3, GF3) == 0
    assert matrix_rank(identity3, 3, 3, GF9) == 3
    add, mul, inv = GF9
    for x in range(1, 9):
        assert mul[x][inv[x]] == 1
    assert printable(b"abc") and not printable(b"\x01")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--structural-only", action="store_true")
    args = parser.parse_args()
    structural_self_test()
    if args.structural_only:
        print("[*] Phase 471 structural self-test OK")
        return
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "route_census": report["route_census"],
        "leads": {
            "seven_segment_exact": len(report["leads"]["seven_segment_exact"]),
            "base9_exact": len(report["leads"]["base9_exact"]),
            "bitmask_exact": len(report["leads"]["bitmask_exact"]),
            "calibrated": list(report["leads"]["calibrated"]),
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
