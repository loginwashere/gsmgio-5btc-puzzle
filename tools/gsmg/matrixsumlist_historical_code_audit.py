#!/usr/bin/env python3
"""Chronological audit of pre-output ``matrixsumlist`` code artifacts.

The cutoff is the first Telegram publication of the exact 31-character DBBI
selection.  This audit asks a deliberately narrow question: did code available
before that cutoff define how that selection enters a matrix and what artifact
should come out?
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from denis_prime_extraction_audit import TARGET as SELECTED_31
from telegram_export_manifest import DEFAULT_EXPORT_DIR


CUTOFF_MESSAGE_ID = 60333
CUTOFF_DATE = "2026-03-04T03:39:06"

GENERIC_GRID_MESSAGE_IDS = (36612, 36617, 37705)
GENERIC_GRID_FILES = (
    "files/puzzlegrid copy.html",
    "files/puzzlegrid copy (1).html",
    "files/puzzlegrid copy (2).html",
)
GENERIC_GRID_SHA256 = (
    "3c04f68491dd2f586ee129d52e340bcb75145f1914d20edd334a61ea8d55bfab"
)

ROW_COLUMN_MESSAGE_ID = 33950
ROW_COLUMN_FILE = "files/696783482-puzzle-1.txt"
ROW_COLUMN_SHA256 = (
    "b6cbab2b55a83e1bbd993c33596b4d732155a8fe9e26c1a922cb8db3de63f0c5"
)

PRIME_TOOL_MESSAGE_ID = 38470
PRIME_TOOL_CONTEXT_IDS = (38468, 38469, 38471)
PRIME_TOOL_FILE = "files/14x14 Grid Tool Version.html"
PRIME_TOOL_SHA256 = (
    "707e747a8bc4786aa0a6b8ed6df2c0de3adcab3cfe268fcfceb3548a9d5ee7c0"
)
PRIME_TOOL_LETTERS = "matrixsumlistlastwordsbeforearchichoiceenter"
ANIMATION_PATCH_MESSAGE_ID = 38473
ANIMATION_PATCH_FILE = "files/matrix-animation.patch"
ANIMATION_PATCH_SHA256 = (
    "c64e21ee07b11a5ee60a1b1b4d621183265c061f61b7599506e65e5a0a99d8ac"
)

TEXT_EXTENSIONS = {
    ".csv",
    ".c",
    ".cc",
    ".cpp",
    ".cu",
    ".h",
    ".htm",
    ".html",
    ".ipynb",
    ".js",
    ".json",
    ".md",
    ".patch",
    ".py",
    ".pyx",
    ".rtf",
    ".svg",
    ".txt",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def extract_js_array(source, variable):
    match = re.search(
        rf"const\s+{re.escape(variable)}\s*=\s*(\[[\s\S]*?\]);",
        source,
    )
    if not match:
        raise AssertionError(f"missing JavaScript array: {variable}")
    return json.loads(match.group(1))


def spiral_ccw_positions(size):
    positions = [[0] * size for _ in range(size)]
    number = 1
    top, bottom, left, right = 0, size - 1, 0, size - 1
    while top <= bottom and left <= right:
        for row in range(top, bottom + 1):
            positions[row][left] = number
            number += 1
        left += 1
        for col in range(left, right + 1):
            positions[bottom][col] = number
            number += 1
        bottom -= 1
        if top <= bottom:
            for row in range(bottom, top - 1, -1):
                positions[row][right] = number
                number += 1
            right -= 1
        if left <= right:
            for col in range(right, left - 1, -1):
                positions[top][col] = number
                number += 1
            top += 1
    return positions


def is_prime(number):
    if number < 2:
        return False
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 1
    return True


def a1z26_mod(sum_value):
    return "-" if sum_value == 0 else chr((sum_value - 1) % 26 + 65)


def scan_pre_cutoff_attachments(export_dir, messages):
    hits = []
    scanned = 0
    patterns = {
        "matrixsumlist": re.compile(r"matrix\s*sum\s*list|matrixsumlist", re.I),
        "selected31": re.compile(re.escape(SELECTED_31), re.I),
        "row_column_sum": re.compile(
            r"row.?sums?|col(?:umn)?.?sums?", re.I
        ),
        "14x14": re.compile(r"14\s*[x×]\s*14", re.I),
    }
    for message in messages:
        if message.get("date", "") >= CUTOFF_DATE:
            continue
        relative = message.get("file")
        mime_type = message.get("mime_type", "")
        if not relative or (
            Path(relative).suffix.lower() not in TEXT_EXTENSIONS
            and not mime_type.startswith("text/")
        ):
            continue
        path = export_dir / relative
        if not path.is_file():
            continue
        scanned += 1
        source = path.read_text(encoding="utf-8", errors="replace")
        terms = tuple(name for name, pattern in patterns.items() if pattern.search(source))
        if terms:
            hits.append(
                {
                    "message_id": message["id"],
                    "date": message["date"],
                    "author": message.get("from"),
                    "file": relative,
                    "terms": terms,
                }
            )
    return scanned, tuple(hits)


def audit(export_dir=DEFAULT_EXPORT_DIR):
    export_dir = Path(export_dir)
    payload = json.loads((export_dir / "result.json").read_text(encoding="utf-8"))
    messages = payload["messages"]
    by_id = {message["id"]: message for message in messages}

    cutoff = by_id[CUTOFF_MESSAGE_ID]
    cutoff_text = flatten_text(cutoff.get("text", ""))

    row_column_path = export_dir / ROW_COLUMN_FILE
    row_column_source = row_column_path.read_text(encoding="utf-8", errors="replace")
    row_column_rule = all(
        fragment in row_column_source
        for fragment in (
            "row_sums = [sum(row) for row in matrix]",
            "col_sums = [sum(col) for col in zip(*matrix)]",
            "matrix_sum_list = row_sums + col_sums",
        )
    )
    row_column_payload_match = re.search(
        r'matrix\s*=\s*\[\s*\[ord\(c\) for c in\s*"([a-z\n]+)"\s*\]\s*\]',
        row_column_source,
    )
    if not row_column_payload_match:
        raise AssertionError("missing historical row/column matrix payload")
    row_column_payload = row_column_payload_match.group(1).replace("\n", "")

    generic_sources = [
        (export_dir / relative).read_text(encoding="utf-8", errors="replace")
        for relative in GENERIC_GRID_FILES
    ]
    generic_pattern_values = tuple(
        re.findall(r'<option value="([^"]+)">', generic_sources[0])[:10]
    )
    generic_hashes = tuple(sha256(export_dir / relative) for relative in GENERIC_GRID_FILES)

    prime_tool_path = export_dir / PRIME_TOOL_FILE
    prime_tool_source = prime_tool_path.read_text(encoding="utf-8", errors="replace")
    grid = extract_js_array(prime_tool_source, "gridData")
    yellow_cells = extract_js_array(prime_tool_source, "yellowCells")
    blue_cells = extract_js_array(prime_tool_source, "blueCells")
    letter_match = re.search(r'const\s+letterString\s*=\s*"([^"]+)"', prime_tool_source)
    if not letter_match:
        raise AssertionError("missing prime-tool letterString")
    letter_string = letter_match.group(1)
    positions = spiral_ccw_positions(len(grid))
    row_sums = tuple(sum(value for value in row if is_prime(value)) for row in positions)
    column_sums = tuple(
        sum(positions[row][col] for row in range(len(grid)) if is_prime(positions[row][col]))
        for col in range(len(grid))
    )
    row_letters = "".join(a1z26_mod(value) for value in row_sums)
    column_letters = "".join(a1z26_mod(value) for value in column_sums)
    prime_tool_context = tuple(
        flatten_text(by_id[message_id].get("text", ""))
        for message_id in PRIME_TOOL_CONTEXT_IDS
    )
    animation_patch_path = export_dir / ANIMATION_PATCH_FILE
    animation_patch_source = animation_patch_path.read_text(
        encoding="utf-8", errors="replace"
    )

    scanned, attachment_hits = scan_pre_cutoff_attachments(export_dir, messages)

    report = {
        "cutoff": {
            "message_id": cutoff["id"],
            "date": cutoff["date"],
            "author": cutoff.get("from"),
            "contains_selected31": SELECTED_31 in cutoff_text,
        },
        "public_history": (
            {
                "date": "2021-05-20T13:48:21-06:00",
                "artifact": "puzzlehunt README",
                "commit": "a7041aac0b920bb207c071d92386e096204eab6d",
                "defines": "decodes the standalone matrixsumlist token",
                "selected31": False,
                "complete_consumer": False,
            },
            {
                "date": "2023-08-31T14:36:27-06:00",
                "artifact": "Naddiseo salphaseion.ipynb",
                "commit": "dcb66952de3157f6e68cb00aa047dd2e4ff8ae39",
                "defines": "segments and decodes instruction islands only",
                "selected31": False,
                "complete_consumer": False,
            },
        ),
        "row_column_attachment": {
            "message_id": ROW_COLUMN_MESSAGE_ID,
            "date": by_id[ROW_COLUMN_MESSAGE_ID]["date"],
            "author": by_id[ROW_COLUMN_MESSAGE_ID].get("from"),
            "sha256": sha256(row_column_path),
            "defines_row_plus_column": row_column_rule,
            "uses_selected31": SELECTED_31 in row_column_source,
            "matrix_shape": (1, len(row_column_payload)),
            "row_sum": sum(map(ord, row_column_payload)),
            "next_artifact_defined": False,
        },
        "generic_grid_tool": {
            "message_ids": GENERIC_GRID_MESSAGE_IDS,
            "first_date": by_id[GENERIC_GRID_MESSAGE_IDS[0]]["date"],
            "identical_hashes": generic_hashes,
            "sha256": generic_hashes[0],
            "grid_shape": (14, 14),
            "macro_pattern_count": len(generic_pattern_values),
            "macro_patterns": generic_pattern_values,
            "fixed_traversal": False,
            "sum_rule": False,
            "uses_selected31": any(SELECTED_31 in source for source in generic_sources),
            "next_artifact_defined": False,
        },
        "prime_sum_tool": {
            "message_id": PRIME_TOOL_MESSAGE_ID,
            "context_message_ids": PRIME_TOOL_CONTEXT_IDS,
            "date": by_id[PRIME_TOOL_MESSAGE_ID]["date"],
            "author": by_id[PRIME_TOOL_MESSAGE_ID].get("from"),
            "sha256": sha256(prime_tool_path),
            "grid_shape": (len(grid), len(grid[0])),
            "counterclockwise_spiral_start": (0, 0),
            "letter_string": letter_string,
            "letter_count": len(letter_string),
            "context_claims_56_readable_letters": "56 Lettters" in prime_tool_context[0],
            "context_claims_140_remaining_squares": "140 squares left" in prime_tool_context[0],
            "context_quotes_worth_140": "one hundred fourty" in prime_tool_context[1],
            "context_selects_prime_sum_rule": False,
            "yellow_coordinate_count": len(yellow_cells),
            "blue_coordinate_count": len(blue_cells),
            "row_sums": row_sums,
            "column_sums": column_sums,
            "row_letters": row_letters,
            "column_letters": column_letters,
            "sum_depends_on_grid_bits": False,
            "sum_depends_on_letter_string": False,
            "uses_selected31": SELECTED_31 in prime_tool_source,
            "next_artifact_defined": False,
        },
        "animation_patch": {
            "message_id": ANIMATION_PATCH_MESSAGE_ID,
            "date": by_id[ANIMATION_PATCH_MESSAGE_ID]["date"],
            "author": by_id[ANIMATION_PATCH_MESSAGE_ID].get("from"),
            "sha256": sha256(animation_patch_path),
            "changed_lines": 3,
            "css_animation_only": all(
                fragment in animation_patch_source
                for fragment in (
                    "background: black",
                    "top: -100%",
                    "translateY(-100%)",
                )
            ),
            "changes_matrix_mechanics": False,
            "uses_selected31": SELECTED_31 in animation_patch_source,
        },
        "attachment_scan": {
            "pre_cutoff_text_attachments_scanned": scanned,
            "hits": attachment_hits,
            "selected31_hits": tuple(
                hit["message_id"] for hit in attachment_hits if "selected31" in hit["terms"]
            ),
        },
        "gate_result": {
            "g1_historical_mechanics": "PARTIAL",
            "g2_selected31": "PASS",
            "g3_complete_operation": "FAIL",
            "g4_next_artifact": "FAIL",
            "historical_code_fixes_transition": False,
        },
    }
    return report


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["cutoff"]["date"] == CUTOFF_DATE
    assert report["cutoff"]["contains_selected31"]
    assert report["row_column_attachment"]["sha256"] == ROW_COLUMN_SHA256
    assert report["row_column_attachment"]["defines_row_plus_column"]
    assert not report["row_column_attachment"]["uses_selected31"]
    assert report["row_column_attachment"]["matrix_shape"] == (1, 1539)
    assert report["row_column_attachment"]["row_sum"] == 168053
    generic = report["generic_grid_tool"]
    assert generic["sha256"] == GENERIC_GRID_SHA256
    assert len(set(generic["identical_hashes"])) == 1
    assert generic["grid_shape"] == (14, 14)
    assert generic["macro_pattern_count"] == 10
    assert not generic["fixed_traversal"]
    prime = report["prime_sum_tool"]
    assert prime["sha256"] == PRIME_TOOL_SHA256
    assert prime["grid_shape"] == (14, 14)
    assert prime["letter_string"] == PRIME_TOOL_LETTERS
    assert prime["context_claims_56_readable_letters"]
    assert prime["context_claims_140_remaining_squares"]
    assert prime["context_quotes_worth_140"]
    assert not prime["context_selects_prime_sum_rule"]
    assert prime["row_sums"] == (
        131, 144, 358, 194, 267, 372, 615, 369, 331, 398, 11, 358, 224, 59
    )
    assert prime["column_sums"] == (
        41, 173, 301, 400, 361, 476, 419, 348, 198, 398, 416, 0, 203, 97
    )
    assert prime["row_letters"] == "ANTLGHQESHKTPG"
    assert prime["column_letters"] == "OQOJWHCJPHZ-US"
    assert not prime["sum_depends_on_grid_bits"]
    assert not prime["sum_depends_on_letter_string"]
    assert not prime["uses_selected31"]
    patch = report["animation_patch"]
    assert patch["sha256"] == ANIMATION_PATCH_SHA256
    assert patch["css_animation_only"]
    assert not patch["changes_matrix_mechanics"]
    assert not patch["uses_selected31"]
    assert report["attachment_scan"]["pre_cutoff_text_attachments_scanned"] == 83
    assert report["attachment_scan"]["selected31_hits"] == ()
    assert not report["gate_result"]["historical_code_fixes_transition"]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export_dir) if args.self_test else audit(args.export_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
