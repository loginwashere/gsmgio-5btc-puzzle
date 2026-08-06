#!/usr/bin/env python3
"""Execute Cosmic Duality clue fragments as a bounded instruction pipeline.

This tests a different reading from the keyword/checkerboard sweeps:

    matrixsumlist -> lastwordsbeforearchichoice -> thispassword -> enter

The 91-symbol dbbi block is paired cell-for-cell with the known 91-character
Phase 3.2.2 plaintext in 7x13 and 13x7 matrices. The script executes literal
matrix sums, rankings, selections, and elementwise operations. It then extracts
words immediately before "choice"/"select" in preceding Matrix-related text and
composes those phrases with the matrix outputs.

Every generated textual candidate can be checked with the existing real AES
oracle. The search is deterministic and contains no dictionary expansion.

Usage:
    python3 tools/gsmg/matrix_instruction_sweep.py --self-test
    python3 tools/gsmg/matrix_instruction_sweep.py --top 30
    python3 tools/gsmg/matrix_instruction_sweep.py --no-aes
    python3 tools/gsmg/matrix_instruction_sweep.py --source-file extra_corpus.txt
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import aes_try_open, answer_forms, keystr_forms  # noqa: E402
from data import DBBI, VALIDATION_ANSWER  # noqa: E402

SHAPES = ((7, 13), (13, 7))
DIGIT_MAPS = {
    "a0i8": {symbol: index for index, symbol in enumerate("abcdefghi")},
    "a1i9": {symbol: index + 1 for index, symbol in enumerate("abcdefghi")},
}
LETTER_MAPS = {
    "a0z25": lambda letter: ord(letter) - 65,
    "a1z26": lambda letter: ord(letter) - 64,
}

BUILTIN_SOURCES = {
    "merovingian": (
        "Morpheus Everything begins with choice. Merovingian No. Wrong. "
        "Choice is an illusion created between those with power and those without."
    ),
    "architect_choice": "The problem is choice.",
    "phase32_architect": (
        "The function of the you is now to return to the source codes allowing a "
        "temporary dissemination of the code you hopefully carry, reinserting the "
        "prime basics, after which you will be required to select from over "
        "twenty-three ciphers, sixteen encryptions and or seven intertwined "
        "passwords to find the actual private key."
    ),
}
MARKERS = {"choice", "select", "architect", "archi"}
COMMON_WORDS = (
    "THE", "THIS", "PASSWORD", "PRIVATE", "KEY", "MATRIX", "SUM", "LIST",
    "CHOICE", "ENTER", "LAST", "WORDS", "BEFORE", "ARCHITECT", "PRIME",
    "HALF", "BETTER", "ANSWER", "SOURCE", "CODE", "YOUR", "YOU",
)


@dataclass(frozen=True)
class Candidate:
    stage: str
    label: str
    value: str
    score: int


def reshape(items, rows, cols):
    if len(items) != rows * cols:
        raise ValueError(f"cannot reshape {len(items)} items as {rows}x{cols}")
    return [list(items[index:index + cols]) for index in range(0, len(items), cols)]


def flatten_rows(matrix):
    return [value for row in matrix for value in row]


def flatten_columns(matrix):
    rows, cols = len(matrix), len(matrix[0])
    return [matrix[row][col] for col in range(cols) for row in range(rows)]


def row_sums(matrix):
    return [sum(row) for row in matrix]


def column_sums(matrix):
    rows, cols = len(matrix), len(matrix[0])
    return [sum(matrix[row][col] for row in range(rows)) for col in range(cols)]


def stable_order(values, reverse=False):
    if reverse:
        return sorted(range(len(values)), key=lambda index: (-values[index], index))
    return sorted(range(len(values)), key=lambda index: (values[index], index))


def read_rows_in_order(matrix, order):
    return "".join("".join(matrix[index]) for index in order)


def read_columns_in_order(matrix, order):
    return "".join(
        str(matrix[row][col])
        for col in order
        for row in range(len(matrix))
    )


def numbers_to_letters(values, one_based=False):
    offset = 1 if one_based else 0
    return "".join(chr(65 + ((value - offset) % 26)) for value in values)


def select_global(text, values, one_based=False):
    offset = 1 if one_based else 0
    return "".join(text[(value - offset) % len(text)] for value in values)


def select_rows(matrix, values, one_based=False):
    offset = 1 if one_based else 0
    return "".join(
        row[(value - offset) % len(row)]
        for row, value in zip(matrix, values)
    )


def select_columns(matrix, values, one_based=False):
    rows, cols = len(matrix), len(matrix[0])
    offset = 1 if one_based else 0
    return "".join(
        matrix[(value - offset) % rows][col]
        for col, value in enumerate(values[:cols])
    )


def elementwise(left, right, operation):
    if operation == "add":
        return [(a + b) % 26 for a, b in zip(left, right)]
    if operation == "plain_minus_digit":
        return [(a - b) % 26 for a, b in zip(left, right)]
    if operation == "digit_minus_plain":
        return [(b - a) % 26 for a, b in zip(left, right)]
    raise ValueError(operation)


def score_value(value):
    upper = value.upper()
    word_score = sum(len(word) * upper.count(word) for word in COMMON_WORDS)
    alpha = sum(character.isalpha() for character in value)
    diversity = len(set(upper)) if value else 0
    return word_score * 10 + min(alpha, 100) + diversity


def add_candidate(store, stage, label, value):
    value = str(value)
    if not value:
        return
    candidate = Candidate(stage, label, value, score_value(value))
    previous = store.get(value)
    if previous is None or candidate.score > previous.score:
        store[value] = candidate


def add_number_list_candidates(store, label, values, source_text):
    for one_based in (False, True):
        base_label = "one" if one_based else "zero"
        add_candidate(
            store,
            "matrix",
            f"{label}/letters_{base_label}",
            numbers_to_letters(values, one_based),
        )
        add_candidate(
            store,
            "matrix",
            f"{label}/global_select_{base_label}",
            select_global(source_text, values, one_based),
        )
    add_candidate(store, "matrix", f"{label}/decimal", "".join(map(str, values)))
    add_candidate(store, "matrix", f"{label}/decimal_spaced", " ".join(map(str, values)))


def generate_matrix_candidates():
    store = {}
    for rows, cols in SHAPES:
        plain_matrix = reshape(VALIDATION_ANSWER, rows, cols)
        for digit_name, digit_map in DIGIT_MAPS.items():
            digits = [digit_map[symbol] for symbol in DBBI]
            digit_matrix = reshape(digits, rows, cols)
            digit_rows = row_sums(digit_matrix)
            digit_cols = column_sums(digit_matrix)

            prefix = f"{rows}x{cols}/{digit_name}"
            add_number_list_candidates(
                store, f"{prefix}/digit_row_sums", digit_rows, VALIDATION_ANSWER
            )
            add_number_list_candidates(
                store, f"{prefix}/digit_col_sums", digit_cols, VALIDATION_ANSWER
            )

            for reverse in (False, True):
                direction = "desc" if reverse else "asc"
                row_order = stable_order(digit_rows, reverse)
                col_order = stable_order(digit_cols, reverse)
                add_candidate(
                    store,
                    "matrix",
                    f"{prefix}/plain_rows_by_digit_sum_{direction}",
                    read_rows_in_order(plain_matrix, row_order),
                )
                add_candidate(
                    store,
                    "matrix",
                    f"{prefix}/plain_cols_by_digit_sum_{direction}",
                    read_columns_in_order(plain_matrix, col_order),
                )

            for one_based in (False, True):
                base_label = "one" if one_based else "zero"
                add_candidate(
                    store,
                    "matrix",
                    f"{prefix}/row_sum_select_{base_label}",
                    select_rows(plain_matrix, digit_rows, one_based),
                )
                add_candidate(
                    store,
                    "matrix",
                    f"{prefix}/col_sum_select_{base_label}",
                    select_columns(plain_matrix, digit_cols, one_based),
                )

                repeated_row_select = []
                repeated_col_select = []
                offset = 1 if one_based else 0
                for row in range(rows):
                    for col in range(cols):
                        digit = digit_matrix[row][col] - offset
                        repeated_row_select.append(plain_matrix[row][digit % cols])
                        repeated_col_select.append(plain_matrix[digit % rows][col])
                add_candidate(
                    store,
                    "matrix",
                    f"{prefix}/cell_digit_select_row_{base_label}",
                    "".join(repeated_row_select),
                )
                add_candidate(
                    store,
                    "matrix",
                    f"{prefix}/cell_digit_select_col_{base_label}",
                    "".join(repeated_col_select),
                )

            for letter_name, letter_map in LETTER_MAPS.items():
                plain_values = [letter_map(letter) for letter in VALIDATION_ANSWER]
                plain_value_matrix = reshape(plain_values, rows, cols)
                plain_rows = row_sums(plain_value_matrix)
                plain_cols = column_sums(plain_value_matrix)
                map_prefix = f"{prefix}/{letter_name}"
                add_number_list_candidates(
                    store, f"{map_prefix}/plain_row_sums", plain_rows, VALIDATION_ANSWER
                )
                add_number_list_candidates(
                    store, f"{map_prefix}/plain_col_sums", plain_cols, VALIDATION_ANSWER
                )
                for operation in ("add", "plain_minus_digit", "digit_minus_plain"):
                    combined = elementwise(plain_values, digits, operation)
                    combined_matrix = reshape(numbers_to_letters(combined), rows, cols)
                    add_candidate(
                        store,
                        "matrix",
                        f"{map_prefix}/{operation}/rows",
                        "".join(flatten_rows(combined_matrix)),
                    )
                    add_candidate(
                        store,
                        "matrix",
                        f"{map_prefix}/{operation}/columns",
                        "".join(flatten_columns(combined_matrix)),
                    )
    return store


def words(text):
    return re.findall(r"[A-Za-z]+", text.lower())


def extraction_candidates(source_name, text, max_words=13):
    tokens = words(text)
    output = []
    marker_positions = [
        index for index, token in enumerate(tokens)
        if token in MARKERS
    ]
    for marker_index in marker_positions:
        marker = tokens[marker_index]
        for width in range(1, min(max_words, marker_index) + 1):
            phrase = tokens[marker_index - width:marker_index]
            output.append((
                f"{source_name}/before_{marker}/last_{width}",
                "".join(phrase),
            ))
            output.append((
                f"{source_name}/before_{marker}/last_{width}_spaced",
                " ".join(phrase),
            ))
    if marker_positions:
        last_words = [tokens[index - 1] for index in marker_positions if index > 0]
        output.append((f"{source_name}/last_word_before_each_marker", "".join(last_words)))
        output.append((
            f"{source_name}/last_word_before_each_marker_spaced",
            " ".join(last_words),
        ))
    return output


def generate_extraction_candidates(extra_sources, max_words):
    store = {}
    sources = dict(BUILTIN_SOURCES)
    sources.update(extra_sources)
    for source_name, text in sources.items():
        for label, value in extraction_candidates(source_name, text, max_words):
            add_candidate(store, "extraction", label, value)
    return store


def phrase_indices(phrase, one_based=False):
    offset = 1 if one_based else 0
    return [
        (ord(character.upper()) - 65 + offset)
        for character in phrase
        if character.isalpha()
    ]


def compose_candidates(matrix_candidates, extraction_candidates):
    store = {}
    for matrix_candidate in matrix_candidates.values():
        matrix_value = re.sub(r"[^A-Za-z0-9]", "", matrix_candidate.value)
        if not matrix_value:
            continue
        for extraction_candidate in extraction_candidates.values():
            phrase_value = re.sub(r"[^A-Za-z0-9]", "", extraction_candidate.value)
            if not phrase_value:
                continue
            label = f"{matrix_candidate.label}+{extraction_candidate.label}"
            add_candidate(
                store,
                "composed",
                f"{label}/matrix_then_phrase",
                matrix_value + phrase_value,
            )
            add_candidate(
                store,
                "composed",
                f"{label}/phrase_then_matrix",
                phrase_value + matrix_value,
            )
            for one_based in (False, True):
                base_label = "one" if one_based else "zero"
                indices = phrase_indices(phrase_value, one_based)
                add_candidate(
                    store,
                    "composed",
                    f"{label}/phrase_indexes_matrix_{base_label}",
                    select_global(matrix_value, indices, one_based),
                )
    return store


def _check_aes_chunk(candidates, newline_variants):
    tested_keystrings = set()
    hits = []
    for candidate in candidates:
        for form in answer_forms(candidate.value):
            if not form:
                continue
            for keystring in keystr_forms(form, newline_variants):
                if keystring in tested_keystrings:
                    continue
                tested_keystrings.add(keystring)
                result = aes_try_open(keystring)
                if result:
                    tag, plaintext, digest_name, key_len = result
                    hits.append({
                        **asdict(candidate),
                        "form": form,
                        "keystring": keystring,
                        "blob": tag,
                        "kdf": f"{digest_name}/aes{key_len * 8}",
                        "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                    })
    return hits, len(tested_keystrings)


def check_aes(candidates, newline_variants, workers=None):
    """Parallelized over candidate chunks (ProcessPoolExecutor, same pattern as
    cosmic_sweep.py/autokey_sweep.py) — a real-script corpus generates far more
    composed candidates than the built-in short quotes, so this stage needs to scale
    the same way the dictionary-scale sweeps already do."""
    values = list(candidates.values())
    if not values:
        return [], 0
    workers = workers or os.cpu_count() or 4
    chunk_size = max(1, math.ceil(len(values) / (workers * 4)))
    chunks = [values[i:i + chunk_size] for i in range(0, len(values), chunk_size)]
    hits = []
    keystring_count = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_check_aes_chunk, chunk, newline_variants) for chunk in chunks]
        for fut in as_completed(futures):
            chunk_hits, chunk_keystrings = fut.result()
            hits.extend(chunk_hits)
            keystring_count += chunk_keystrings
    return hits, keystring_count


def rank_candidates(candidates):
    return sorted(
        candidates.values(),
        key=lambda candidate: (candidate.score, len(candidate.value), candidate.label),
        reverse=True,
    )


def print_ranked(title, candidates, limit):
    print(f"\n=== {title} ({len(candidates):,} unique) ===")
    for rank, candidate in enumerate(rank_candidates(candidates)[:limit], 1):
        preview = candidate.value[:120].replace("\n", "\\n")
        counts = Counter(candidate.value.upper())
        diversity = len(counts)
        print(
            f"[{rank:3d}] score={candidate.score:4d} len={len(candidate.value):3d} "
            f"diversity={diversity:2d} {candidate.label}"
        )
        print(f"      {preview}")


def load_extra_sources(paths):
    sources = {}
    for path_string in paths:
        path = Path(path_string)
        sources[path.stem] = path.read_text(encoding="utf-8", errors="replace")
    return sources


def run_self_tests():
    assert len(DBBI) == len(VALIDATION_ANSWER) == 91
    assert flatten_rows(reshape("ABCDEF", 2, 3)) == list("ABCDEF")
    assert flatten_columns(reshape("ABCDEF", 2, 3)) == list("ADBECF")
    assert row_sums([[1, 2], [3, 4]]) == [3, 7]
    assert column_sums([[1, 2], [3, 4]]) == [4, 6]
    assert stable_order([3, 1, 1, 2]) == [1, 2, 3, 0]
    assert stable_order([3, 1, 1, 2], reverse=True) == [0, 3, 1, 2]
    assert numbers_to_letters([0, 1, 25]) == "ABZ"
    assert numbers_to_letters([1, 2, 26], one_based=True) == "ABZ"
    assert select_rows([list("ABC"), list("DEF")], [0, 1]) == "AE"
    extracts = dict(extraction_candidates(
        "test", "Everything begins with choice", max_words=3
    ))
    assert extracts["test/before_choice/last_3"] == "everythingbeginswith"
    matrix_candidates = generate_matrix_candidates()
    assert matrix_candidates
    print(
        f"[*] matrix-instruction self-tests passed "
        f"({len(matrix_candidates):,} matrix candidates)"
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--max-words", type=int, default=13)
    parser.add_argument(
        "--source-file",
        action="append",
        default=[],
        help="additional text corpus for positional extraction (repeatable)",
    )
    parser.add_argument("--no-aes", action="store_true")
    parser.add_argument(
        "--no-newline-variants",
        action="store_true",
        help="do not apply the clue's 'enter' as LF/CRLF passphrase variants",
    )
    parser.add_argument("--json-out")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--workers", type=int, default=None,
                         help="AES-check worker processes (default: os.cpu_count())")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()

    matrix_candidates = generate_matrix_candidates()
    extraction_candidates_store = generate_extraction_candidates(
        load_extra_sources(args.source_file),
        args.max_words,
    )
    composed_candidates = compose_candidates(
        matrix_candidates,
        extraction_candidates_store,
    )
    all_candidates = {}
    for group in (
        matrix_candidates,
        extraction_candidates_store,
        composed_candidates,
    ):
        for value, candidate in group.items():
            previous = all_candidates.get(value)
            if previous is None or candidate.score > previous.score:
                all_candidates[value] = candidate

    print_ranked("matrix outputs", matrix_candidates, args.top)
    print_ranked("positional extractions", extraction_candidates_store, args.top)
    print_ranked("composed outputs", composed_candidates, args.top)

    hits = []
    keystring_count = 0
    if not args.no_aes:
        print(f"\n[*] checking {len(all_candidates):,} unique textual candidates with AES oracle")
        hits, keystring_count = check_aes(
            all_candidates,
            newline_variants=not args.no_newline_variants,
            workers=args.workers,
        )
        print(f"[*] tested {keystring_count:,} chunk-deduplicated AES keystrings; "
              f"hits={len(hits)}")
        for hit in hits:
            print(f"\n[+++ AES HIT] {hit}\n")

    report = {
        "stats": {
            "matrix_candidates": len(matrix_candidates),
            "extraction_candidates": len(extraction_candidates_store),
            "composed_candidates": len(composed_candidates),
            "all_candidates": len(all_candidates),
            "aes_keystrings": keystring_count,
            "aes_hits": len(hits),
        },
        "hits": hits,
        "matrix": [asdict(candidate) for candidate in rank_candidates(matrix_candidates)],
        "extractions": [
            asdict(candidate) for candidate in rank_candidates(extraction_candidates_store)
        ],
        "composed": [
            asdict(candidate) for candidate in rank_candidates(composed_candidates)
        ],
    }
    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[*] wrote JSON report to {output_path}")

    if not hits:
        print("\n[*] no instruction-pipeline candidate opened either AES blob")


if __name__ == "__main__":
    main()
