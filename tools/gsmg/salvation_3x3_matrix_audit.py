#!/usr/bin/env python3
"""Test `SALVATION` read as a 3x3 letter matrix (`SAL`/`VAT`/`ION`).

`SALVATION` has exactly 9 letters -- unlike the archived `SalPhaseIon`
title (11 letters, an uneven `SAL`/`PHASE`/`ION` split), it divides evenly
into three 3-letter rows. This module verifies that structural fact
directly, then tests a small, bounded family of natural matrix readings --
row-major, column-major, both reversed, both diagonals, boustrophedon, and
the one reading order with genuine independent precedent in this puzzle:
the exact top-left/counter-clockwise spiral already validated for the
Stage-0 grid image (`grid_spiral.py`) -- as direct AES passphrases against
the tracked and quarantined blobs.

This is not a new cipher family: it reuses the existing validated oracle
exactly as Phase 96 did for the row-major reading, extended to the other
natural readings of the same 3x3 grid.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from grid_spiral import spiral_tl_ccw  # noqa: E402

TITLE = "SALPHASEION"
TITLE_PARTS = ("SAL", "PHASE", "ION")
TARGET_WORD = "SALVATION"
GRID_ROWS = ("SAL", "VAT", "ION")


def structural_facts():
    if "".join(TITLE_PARTS) != TITLE:
        raise AssertionError("title parts no longer reconstruct SalPhaseIon")
    if "".join(GRID_ROWS) != TARGET_WORD:
        raise AssertionError("grid rows no longer reconstruct SALVATION")
    part_lengths = tuple(len(part) for part in TITLE_PARTS)
    row_lengths = tuple(len(row) for row in GRID_ROWS)
    return {
        "title_length": len(TITLE),
        "title_part_lengths": part_lengths,
        "title_split_even": len(set(part_lengths)) == 1,
        "target_length": len(TARGET_WORD),
        "target_row_lengths": row_lengths,
        "target_split_even": len(set(row_lengths)) == 1,
    }


def matrix_readings():
    grid = [list(row) for row in GRID_ROWS]
    n = len(grid)

    row_major = "".join(TARGET_WORD)
    column_major = "".join(
        grid[row][col] for col in range(n) for row in range(n)
    )
    main_diagonal = "".join(grid[i][i] for i in range(n))
    anti_diagonal = "".join(grid[i][n - 1 - i] for i in range(n))
    boustrophedon = "".join(
        "".join(row if index % 2 == 0 else row[::-1])
        for index, row in enumerate(GRID_ROWS)
    )
    spiral_coords = spiral_tl_ccw(n=n)
    spiral = "".join(grid[r][c] for r, c in spiral_coords)

    readings = {
        "row_major": row_major,
        "row_major_reversed": row_major[::-1],
        "column_major": column_major,
        "column_major_reversed": column_major[::-1],
        "main_diagonal": main_diagonal,
        "anti_diagonal": anti_diagonal,
        "boustrophedon": boustrophedon,
        "spiral_tl_ccw": spiral,
    }
    if readings["row_major"] != TARGET_WORD:
        raise AssertionError("row-major reading no longer equals SALVATION")
    if readings["spiral_tl_ccw"] != "SVIONTLAA":
        raise AssertionError(
            f"spiral reading changed: {readings['spiral_tl_ccw']!r}"
        )
    return readings


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for label, candidate in candidates.items():
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((label, candidate, keystring, result))
                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((label, candidate, keystring, result))
                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((label, candidate, keystring, result))
                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((label, candidate, keystring, result))
    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def audit():
    facts = structural_facts()
    if facts["title_split_even"]:
        raise AssertionError("SalPhaseIon title split is unexpectedly even")
    if not facts["target_split_even"]:
        raise AssertionError("SALVATION grid split is unexpectedly uneven")
    readings = matrix_readings()
    return {"facts": facts, "readings": readings}


def print_report(report):
    facts = report["facts"]
    print("[*] structural fact:")
    print(
        f"    SalPhaseIon ({facts['title_length']} letters) splits "
        f"{facts['title_part_lengths']} -- even={facts['title_split_even']}"
    )
    print(
        f"    SALVATION ({facts['target_length']} letters) splits "
        f"{facts['target_row_lengths']} -- even={facts['target_split_even']}"
    )
    print("[*] matrix readings:")
    for label, reading in report["readings"].items():
        print(f"    {label:<22} {reading}")


def self_test():
    report = audit()
    assert report["facts"]["title_part_lengths"] == (3, 5, 3)
    assert report["facts"]["target_row_lengths"] == (3, 3, 3)
    assert report["readings"]["column_major"] == "SVIAAOLTN"
    assert report["readings"]["spiral_tl_ccw"] == "SVIONTLAA"
    print("[*] self-test OK: structural facts + 8 matrix readings verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit()
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(report["readings"], blobs)
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
