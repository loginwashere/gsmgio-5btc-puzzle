#!/usr/bin/env python3
"""Close Point 8's literal 14x14 ink-matrix sum-list proposal.

The matrix and bit rule are already fixed by the authenticated spiral decode:
black/blue=1 and white/yellow/FEFE=0.  This audit takes native row and column
popcounts without inversion.  The complete D4 family is retained only as an
orientation control; it can swap/reverse the same two lists but cannot create
new sums.
"""

import argparse

from first_piece_color_reconstruction import DEFAULT_IMAGE, N, base_bit, load_grid


def a1z26(values):
    return "".join(chr(64 + value) if 1 <= value <= 26 else "?" for value in values)


def d4_sum_list_pairs(rows, columns):
    rows_reverse = tuple(reversed(rows))
    columns_reverse = tuple(reversed(columns))
    return (
        ("identity", rows, columns),
        ("rotate_90", columns_reverse, rows),
        ("rotate_180", rows_reverse, columns_reverse),
        ("rotate_270", columns, rows_reverse),
        ("reflect_vertical", rows, columns_reverse),
        ("reflect_horizontal", rows_reverse, columns),
        ("reflect_main_diagonal", columns, rows),
        ("reflect_anti_diagonal", columns_reverse, rows_reverse),
    )


def audit(path=DEFAULT_IMAGE):
    grid = load_grid(path)
    matrix = tuple(tuple(base_bit(cell) for cell in row) for row in grid)
    rows = tuple(sum(row) for row in matrix)
    columns = tuple(sum(matrix[row][column] for row in range(N)) for column in range(N))
    orientations = tuple(
        {
            "name": name,
            "rows": oriented_rows,
            "columns": oriented_columns,
            "rows_a1z26": a1z26(oriented_rows),
            "columns_a1z26": a1z26(oriented_columns),
        }
        for name, oriented_rows, oriented_columns in d4_sum_list_pairs(rows, columns)
    )
    unique_lists = {
        values
        for orientation in orientations
        for values in (orientation["rows"], orientation["columns"])
    }
    return {
        "matrix": matrix,
        "dimensions": (len(matrix), len(matrix[0])),
        "row_sums": rows,
        "column_sums": columns,
        "total": sum(rows),
        "row_a1z26": a1z26(rows),
        "column_a1z26": a1z26(columns),
        "d4_orientations": orientations,
        "d4_orientation_count": len(orientations),
        "d4_unique_list_count": len(unique_lists),
        "all_orientations_preserve_total": all(
            sum(row["rows"]) == sum(row["columns"]) == sum(rows)
            for row in orientations
        ),
        "consumer_selected": False,
        "oracle_run": False,
    }


def self_test():
    report = audit()
    assert report["dimensions"] == (14, 14)
    assert report["row_sums"] == (6, 10, 8, 7, 6, 6, 5, 4, 9, 9, 7, 8, 7, 9)
    assert report["column_sums"] == (8, 10, 8, 10, 8, 7, 3, 6, 7, 5, 9, 6, 6, 8)
    assert report["total"] == 101
    assert report["row_a1z26"] == "FJHGFFEDIIGHGI"
    assert report["column_a1z26"] == "HJHJHGCFGEIFFH"
    assert report["d4_orientation_count"] == 8
    assert report["d4_unique_list_count"] == 4
    assert report["all_orientations_preserve_total"]
    assert not report["consumer_selected"] and not report["oracle_run"]
    print("[*] self-test OK: Point 8 native row/column sum lists reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    print(f"[*] dimensions: {report['dimensions']}; total ink bits={report['total']}")
    print(f"[*] row sums:    {report['row_sums']} -> {report['row_a1z26']}")
    print(f"[*] column sums: {report['column_sums']} -> {report['column_a1z26']}")
    print(
        f"[*] D4 control: {report['d4_orientation_count']} orientations, "
        f"{report['d4_unique_list_count']} unique directed lists"
    )


if __name__ == "__main__":
    main()
