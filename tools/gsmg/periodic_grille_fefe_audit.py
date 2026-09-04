#!/usr/bin/env python3
"""Audit the natural 49-aperture completion and its FEFEFE sensitivity.

The family is deliberately small: four physical rotations, proven spiral
order plus row-major control, raw and complementary polarity, and one
sensitivity that changes only the FEFEFE cell from its established light=0
bit to 1.  No padding, byte conversion, language scoring, or oracle is used.
"""

from collections import Counter

from denis_rotation_grille_audit import audit as rotation_audit, rotations
from first_piece_color_reconstruction import (
    COLOR_NAMES,
    DEFAULT_IMAGE,
    base_bit,
    is_prime,
    load_grid,
    spiral_top_left_counterclockwise,
)


EXPECTED_TAG_PATTERN = "MC" * 24 + "M"
EXPECTED_SPIRAL_PRIME_HITS = (
    (0, "colored", "inverse"),
    (1, "colored", "inverse"),
    (3, "missing", "inverse"),
)
EXPECTED_MISSING_VALUES = (8462728, 29105716, 33291838, 139760)
EXPECTED_MISSING_INVERSES = (25091703, 4448715, 262593, 33414671)
EXPECTED_FULL_VALUES = (
    257470650106440,
    553991210863056,
    526510880284158,
    9549155325060,
)
EXPECTED_FULL_INVERSES = (
    305479303314871,
    8958742558255,
    36439073137153,
    553400798096251,
)


def read_bits(grid, ordered_cells, fefe_one=False):
    bits = []
    for row, column in ordered_cells:
        color = COLOR_NAMES[grid[row][column]]
        bit = 1 if fefe_one and color == "fefefe" else base_bit(
            grid[row][column]
        )
        bits.append(str(bit))
    return "".join(bits)


def numeric_record(bits):
    value = int(bits, 2)
    inverse = value ^ ((1 << len(bits)) - 1)
    return {
        "bits": bits,
        "length": len(bits),
        "value": value,
        "inverse_bits": "".join("1" if bit == "0" else "0" for bit in bits),
        "inverse_value": inverse,
        "value_prime": is_prime(value),
        "inverse_prime": is_prime(inverse),
        "weight": bits.count("1"),
    }


def order_records(
    grid,
    colored_rotations,
    missing_rotations,
    completion_rotations,
    order_key,
    fefe_one=False,
):
    records = []
    for turn, (colored, missing, completion) in enumerate(
        zip(colored_rotations, missing_rotations, completion_rotations)
    ):
        if colored & missing or colored | missing != completion:
            raise AssertionError("24/25 rails do not partition completion")
        colored_order = tuple(sorted(colored, key=order_key))
        missing_order = tuple(sorted(missing, key=order_key))
        full_order = tuple(sorted(completion, key=order_key))
        colored_bits = read_bits(grid, colored_order, fefe_one=fefe_one)
        missing_bits = read_bits(grid, missing_order, fefe_one=fefe_one)
        full_bits = read_bits(grid, full_order, fefe_one=fefe_one)
        tags = "".join("C" if cell in colored else "M" for cell in full_order)
        projected_colored = "".join(
            bit for bit, tag in zip(full_bits, tags) if tag == "C"
        )
        projected_missing = "".join(
            bit for bit, tag in zip(full_bits, tags) if tag == "M"
        )
        if (projected_colored, projected_missing) != (
            colored_bits,
            missing_bits,
        ):
            raise AssertionError("full reading does not project to its rails")
        fefe_full_positions = tuple(
            index
            for index, (row, column) in enumerate(full_order)
            if COLOR_NAMES[grid[row][column]] == "fefefe"
        )
        fefe_missing_positions = tuple(
            index
            for index, (row, column) in enumerate(missing_order)
            if COLOR_NAMES[grid[row][column]] == "fefefe"
        )
        records.append(
            {
                "turn": turn,
                "colored": numeric_record(colored_bits),
                "missing": numeric_record(missing_bits),
                "full": numeric_record(full_bits),
                "tags": tags,
                "alternating_missing_first": tags == EXPECTED_TAG_PATTERN,
                "fefe_full_positions": fefe_full_positions,
                "fefe_missing_positions": fefe_missing_positions,
            }
        )
    return tuple(records)


def summarize(records):
    counts = Counter(turns=len(records))
    prime_hits = []
    for record in records:
        counts["alternating_turns"] += record["alternating_missing_first"]
        for rail_name in ("colored", "missing", "full"):
            rail = record[rail_name]
            for polarity, flag in (
                ("raw", rail["value_prime"]),
                ("inverse", rail["inverse_prime"]),
            ):
                counts["tested_numbers"] += 1
                if flag:
                    counts["prime_hits"] += 1
                    prime_hits.append((record["turn"], rail_name, polarity))
    return counts, tuple(prime_hits)


def changed_numeric_records(baseline, sensitivity):
    changes = []
    for order_name in ("spiral", "row_major"):
        for before, after in zip(baseline[order_name], sensitivity[order_name]):
            for rail_name in ("colored", "missing", "full"):
                old = before[rail_name]
                new = after[rail_name]
                if old["bits"] == new["bits"]:
                    continue
                changes.append(
                    {
                        "order": order_name,
                        "turn": before["turn"],
                        "rail": rail_name,
                        "xor": old["value"] ^ new["value"],
                        "old_prime_flags": (
                            old["value_prime"], old["inverse_prime"]
                        ),
                        "new_prime_flags": (
                            new["value_prime"], new["inverse_prime"]
                        ),
                    }
                )
    return tuple(changes)


def audit(image_path=DEFAULT_IMAGE):
    geometry = rotation_audit(image_path)
    grid = load_grid(image_path)
    colored_rotations = geometry["rotations"]
    missing_rotations = rotations(geometry["missing"])
    completion_rotations = geometry["completion_rotations"]
    spiral = spiral_top_left_counterclockwise()
    spiral_index = {coordinate: index for index, coordinate in enumerate(spiral)}

    modes = {}
    for mode, fefe_one in (("baseline_fefe_zero", False), ("fefe_one", True)):
        mode_records = {
            "spiral": order_records(
                grid,
                colored_rotations,
                missing_rotations,
                completion_rotations,
                spiral_index.__getitem__,
                fefe_one=fefe_one,
            ),
            "row_major": order_records(
                grid,
                colored_rotations,
                missing_rotations,
                completion_rotations,
                lambda coordinate: coordinate,
                fefe_one=fefe_one,
            ),
        }
        for order_name in ("spiral", "row_major"):
            counts, prime_hits = summarize(mode_records[order_name])
            mode_records[f"{order_name}_counts"] = counts
            mode_records[f"{order_name}_prime_hits"] = prime_hits
        modes[mode] = mode_records

    return {
        "colored_count": len(geometry["colored"]),
        "missing_count": len(geometry["missing"]),
        "completion_count": len(geometry["periodic_completion"]),
        "completion_union_size": geometry["completion_union_size"],
        "missing_palette": geometry["missing_palette"],
        "modes": modes,
        "sensitivity_changes": changed_numeric_records(
            modes["baseline_fefe_zero"], modes["fefe_one"]
        ),
    }


def self_test():
    result = audit()
    assert (
        result["colored_count"],
        result["missing_count"],
        result["completion_count"],
        result["completion_union_size"],
    ) == (24, 25, 49, 196)
    assert result["missing_palette"] == Counter(white=18, black=6, fefefe=1)
    baseline = result["modes"]["baseline_fefe_zero"]
    sensitivity = result["modes"]["fefe_one"]
    for mode in (baseline, sensitivity):
        assert all(record["colored"]["length"] == 24 for record in mode["spiral"])
        assert all(record["missing"]["length"] == 25 for record in mode["spiral"])
        assert all(record["full"]["length"] == 49 for record in mode["spiral"])
        assert mode["spiral_counts"]["tested_numbers"] == 24
        assert mode["row_major_counts"]["tested_numbers"] == 24
    assert baseline["spiral"][0]["fefe_missing_positions"] == (20,)
    assert baseline["spiral"][0]["fefe_full_positions"] == (40,)
    assert sum(
        bool(record["fefe_missing_positions"])
        for record in baseline["spiral"]
    ) == 1
    assert all(
        before["colored"]["bits"] == after["colored"]["bits"]
        for before, after in zip(baseline["spiral"], sensitivity["spiral"])
    )
    assert len(result["sensitivity_changes"]) == 4
    assert baseline["spiral_counts"] == Counter(
        turns=4, alternating_turns=1, tested_numbers=24, prime_hits=3
    )
    assert baseline["row_major_counts"] == Counter(
        turns=4, tested_numbers=24
    )
    assert sensitivity["spiral_counts"] == baseline["spiral_counts"]
    assert sensitivity["row_major_counts"] == baseline["row_major_counts"]
    assert baseline["spiral_prime_hits"] == EXPECTED_SPIRAL_PRIME_HITS
    assert sensitivity["spiral_prime_hits"] == EXPECTED_SPIRAL_PRIME_HITS
    assert baseline["row_major_prime_hits"] == ()
    assert sensitivity["row_major_prime_hits"] == ()
    assert tuple(
        record["missing"]["value"] for record in baseline["spiral"]
    ) == EXPECTED_MISSING_VALUES
    assert tuple(
        record["missing"]["inverse_value"] for record in baseline["spiral"]
    ) == EXPECTED_MISSING_INVERSES
    assert tuple(
        record["full"]["value"] for record in baseline["spiral"]
    ) == EXPECTED_FULL_VALUES
    assert tuple(
        record["full"]["inverse_value"] for record in baseline["spiral"]
    ) == EXPECTED_FULL_INVERSES
    assert not any(
        record["full"]["value_prime"] or record["full"]["inverse_prime"]
        for mode in (baseline, sensitivity)
        for record in mode["spiral"]
    )
    assert tuple(
        (change["order"], change["turn"], change["rail"], change["xor"])
        for change in result["sensitivity_changes"]
    ) == (
        ("spiral", 0, "missing", 16),
        ("spiral", 0, "full", 256),
        ("row_major", 0, "missing", 4096),
        ("row_major", 0, "full", 8388608),
    )
    assert all(
        change["old_prime_flags"] == change["new_prime_flags"]
        == (False, False)
        for change in result["sensitivity_changes"]
    )


def main():
    self_test()
    result = audit()
    print(
        "geometry:",
        f"{result['colored_count']} colored + {result['missing_count']} added = ",
        f"{result['completion_count']}; rotations cover {result['completion_union_size']}",
    )
    for mode_name, mode in result["modes"].items():
        print(mode_name + ":")
        for order_name in ("spiral", "row_major"):
            counts = mode[f"{order_name}_counts"]
            print(
                f"  {order_name}: primes={counts['prime_hits']}/",
                f"{counts['tested_numbers']}; hits=",
                mode[f"{order_name}_prime_hits"],
            )
        for record in mode["spiral"]:
            print(
                f"  turn {record['turn'] * 90:3d}: ",
                f"C={record['colored']['value']}/~{record['colored']['inverse_value']} ",
                f"M={record['missing']['value']}/~{record['missing']['inverse_value']} ",
                f"F={record['full']['value']}/~{record['full']['inverse_value']} ",
                f"alternating={record['alternating_missing_first']}",
            )
    print("FEFE sensitivity changes:", result["sensitivity_changes"])


if __name__ == "__main__":
    main()
