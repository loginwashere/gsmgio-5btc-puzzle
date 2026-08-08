#!/usr/bin/env python3
"""Calibrate Phase 143's Cosmic Duality last-column decode against a solved blob.

Phase 143 found that Cosmic Duality's guide text, read as a 28x64 Base64
rectangle (28 authored 64-character lines), decodes its last column to
`7a20fe...` -- real, reproducible structure, but oracle-negative as a
password or key. This module asks the calibration question Phase 143 left
open: does the SAME operation, applied to a blob whose password and
plaintext are already fully solved, also produce rectangle/last-column
structure with an apparent signal (a literal MD5, an isolated FE byte,
above-noise printable ratio)? If a known-uninteresting solved blob shows the
same texture, that lowers confidence that Cosmic Duality's version is an
intentional secondary encoding rather than an ordinary side effect of
OpenSSL's 64-character Base64 line width.

`data.PHASE32_BLOB_B64` is the only other blob (besides COSMIC) stored with
enough source rows for this operation to be meaningful: its literal Python
source lines are themselves 64 characters each (51 of them, matching the
original README's own wrapping) -- unlike SALPH/P32TRAILING/URLBLOB, which
are only 2-3 lines long and too short for a column to carry any signal.

No new password candidate is proposed or tested here -- Phase 3.2 is already
solved, and this module's purpose is a structural/statistical comparison,
not an oracle sweep.
"""

import argparse
import base64
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import printable_z_score  # noqa: E402
from data import COSMIC_BLOB_B64, PHASE32_BLOB_B64  # noqa: E402

FE = 0xFE
EXPECTED_LAST_COLUMN_HEX = (
    "4f6319ba40764810ef9f6c7da2057b9bc10b166b486de97d29b282c0b09e49f23042cf48e193"
)
EXPECTED_FE_COLUMNS = (19, 21, 31, 32, 42, 52, 53, 58)
EXPECTED_PRINTABLE_COUNT = 17
COSMIC_EXPECTED_FE_COLUMNS = (1, 8, 33, 34, 63)


def wrap_columns(blob_b64, width=64):
    raw = "".join(blob_b64.split())
    if len(raw) % width:
        raise ValueError(f"blob is not an exact multiple of {width} Base64 characters")
    rows = [raw[i : i + width] for i in range(0, len(raw), width)]
    return tuple(
        "".join(row[column] for row in rows) for column in range(width)
    )


def decode_column(column):
    padding = (-len(column)) % 4
    return base64.b64decode(column + "=" * padding)


def expected_fe_columns(byte_length, column_count=64):
    """Expected count of columns containing >=1 byte==0xFE under a uniform
    random-byte null, given each column decodes to `byte_length` bytes."""
    p_at_least_one = 1 - (255 / 256) ** byte_length
    return column_count * p_at_least_one


def analyze(blob_b64, width=64):
    columns = wrap_columns(blob_b64, width)
    decoded = [decode_column(c) for c in columns]
    byte_length = len(decoded[0])
    if any(len(d) != byte_length for d in decoded):
        raise AssertionError("column decode lengths are not uniform")

    md5_columns = tuple(i for i, d in enumerate(decoded) if b"MD5" in d)
    fe_columns = tuple(i for i, d in enumerate(decoded) if FE in d)
    z_scores = tuple(printable_z_score(d) for d in decoded)

    return {
        "row_count": len(columns[0]),
        "column_width": width,
        "bytes_per_column": byte_length,
        "last_column_hex": decoded[-1].hex(),
        "last_column_printable_count": sum(
            1 for c in decoded[-1] if 32 <= c < 127 or c in (9, 10, 13)
        ),
        "last_column_z": z_scores[-1],
        "md5_columns": md5_columns,
        "fe_columns": fe_columns,
        "last_column_has_fe": (len(columns) - 1) in fe_columns,
        "expected_fe_columns": expected_fe_columns(byte_length),
        "max_z": max(z_scores),
        "max_z_column": max(range(64), key=lambda i: z_scores[i]),
    }


def audit():
    cosmic = analyze(COSMIC_BLOB_B64)
    phase32 = analyze(PHASE32_BLOB_B64)
    return {"cosmic": cosmic, "phase32": phase32}


def self_test():
    report = audit()
    phase32 = report["phase32"]
    assert phase32["row_count"] == 51
    assert phase32["bytes_per_column"] == 38
    assert phase32["last_column_hex"] == EXPECTED_LAST_COLUMN_HEX
    assert phase32["last_column_printable_count"] == EXPECTED_PRINTABLE_COUNT
    assert phase32["md5_columns"] == ()
    assert phase32["fe_columns"] == EXPECTED_FE_COLUMNS
    assert len(phase32["fe_columns"]) == 8
    assert phase32["last_column_has_fe"] is False
    assert abs(phase32["expected_fe_columns"] - 8.845) < 0.01

    cosmic = report["cosmic"]
    assert cosmic["row_count"] == 28
    assert cosmic["bytes_per_column"] == 21
    assert cosmic["last_column_hex"].startswith("7a20fe")
    assert cosmic["fe_columns"] == COSMIC_EXPECTED_FE_COLUMNS
    assert cosmic["last_column_has_fe"] is True
    assert abs(cosmic["expected_fe_columns"] - 5.050) < 0.01

    # Both observed FE-column counts sit within one column of their
    # uniform-random-byte expectation -- no excess signal in either blob.
    for report_entry in (cosmic, phase32):
        assert abs(len(report_entry["fe_columns"]) - report_entry["expected_fe_columns"]) < 1.0

    print(
        "[*] self-test OK: solved-blob PHASE32 shows the same rectangle/"
        "column texture as COSMIC (no MD5, FE-column count consistent with "
        "chance in both), with a pinned 38-byte last-column decode"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return

    report = audit()
    for label, entry in report.items():
        print(f"[*] {label}: {entry['row_count']} rows x 64 cols, "
              f"{entry['bytes_per_column']} bytes/column")
        print(f"    last column hex: {entry['last_column_hex']}")
        print(f"    last column printable: {entry['last_column_printable_count']}/"
              f"{entry['bytes_per_column']}, z={entry['last_column_z']:.3f}")
        print(f"    MD5 columns: {entry['md5_columns']}")
        print(f"    FE columns: {entry['fe_columns']} "
              f"(observed={len(entry['fe_columns'])}, "
              f"expected-by-chance={entry['expected_fe_columns']:.2f}, "
              f"last_column_has_fe={entry['last_column_has_fe']})")
        print(f"    max printable z-score: {entry['max_z']:.3f} "
              f"at column {entry['max_z_column']}")


if __name__ == "__main__":
    main()
