#!/usr/bin/env python3
"""Brainstorm item 2 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md` section 2),
the `matrixsumlist` consumer problem, REVISIT bullet.

`matrix_instruction_sweep.py` (Second Path, closed negative against the real
Matrix screenplay) always pairs DBBI's cell-for-cell digit matrix against the
known Phase 3.2.2 plaintext (`VALIDATION_ANSWER`) as the "plain" side of every
row/column-sum selection. It never pairs DBBI against **itself**
(autocorrelation: read DBBI back through row/column orderings or selections
derived from its own digit sums) or against **FAED folded down to 91**
(`cross_target_coupling_sweep.py` already implements six fold methods for a
different purpose -- reused here, not reinvented). Both are new "plain" sides
for the identical, already-validated matrix-sum-select grammar, so this reuses
`matrix_instruction_sweep.py`'s generic matrix utilities directly rather than
duplicating them.

Also runs the much smaller, complementary literal-index probe: read the
single characters at positions 23, 16, and 7 (both 0- and 1-based, forward
and reverse) directly out of DBBI and the known Phase 3.2.2 plaintext.
`matrixsumlist_31_feasibility_audit.py` (Phase 51) already ran this exact
probe against the 31-character Denis/Flo selection (`TARGET`) -- reproduced
here only as a self-test cross-check, not re-claimed as new -- but never
against the 91-character DBBI/plaintext inputs themselves.
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
from cross_target_coupling_sweep import FOLD_METHODS, fold_faed, to_symbols  # noqa: E402
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
from denis_prime_extraction_audit import SOURCE, TARGET  # noqa: E402
from matrix_instruction_sweep import (  # noqa: E402
    DIGIT_MAPS,
    SHAPES,
    column_sums,
    numbers_to_letters,
    read_columns_in_order,
    read_rows_in_order,
    reshape,
    row_sums,
    select_columns,
    select_rows,
    stable_order,
)

SUM_LIST = (23, 16, 7)
CLUE_WORDS = (
    "yin", "yang", "matrix", "sum", "list", "seed", "key", "enter",
    "password", "salvation", "but", "hye", "hey",
)


def index_probe(text, indices=SUM_LIST):
    outputs = {}
    for reverse in (False, True):
        source = text[::-1] if reverse else text
        direction = "reverse" if reverse else "forward"
        for one_based in (False, True):
            base = "one" if one_based else "zero"
            offset = 1 if one_based else 0
            outputs[f"{direction}/{base}"] = "".join(
                source[(index - offset) % len(source)] for index in indices
            )
    return outputs


def digit_matrix_for(rows, cols, digit_name):
    digit_map = DIGIT_MAPS[digit_name]
    digits = [digit_map[symbol] for symbol in DBBI]
    return reshape(digits, rows, cols)


def plain_matrix_variants():
    """Every new 91-symbol 'plain' side tried against DBBI's own digit sums."""
    variants = {"dbbi_self": list(DBBI)}
    for method in FOLD_METHODS:
        variants[f"faed_fold/{method}"] = list(to_symbols(fold_faed(method)))
    return variants


def matrix_candidates():
    candidates = {}
    for rows, cols in SHAPES:
        for digit_name in DIGIT_MAPS:
            digit_matrix = digit_matrix_for(rows, cols, digit_name)
            digit_rows = row_sums(digit_matrix)
            digit_cols = column_sums(digit_matrix)
            row_order_asc = stable_order(digit_rows, reverse=False)
            row_order_desc = stable_order(digit_rows, reverse=True)
            col_order_asc = stable_order(digit_cols, reverse=False)
            col_order_desc = stable_order(digit_cols, reverse=True)

            for plain_name, plain_symbols in plain_matrix_variants().items():
                plain_matrix = reshape(plain_symbols, rows, cols)
                prefix = f"{rows}x{cols}/{digit_name}/{plain_name}"

                candidates[f"{prefix}/rows_by_digit_sum_asc"] = read_rows_in_order(
                    plain_matrix, row_order_asc
                )
                candidates[f"{prefix}/rows_by_digit_sum_desc"] = read_rows_in_order(
                    plain_matrix, row_order_desc
                )
                candidates[f"{prefix}/cols_by_digit_sum_asc"] = read_columns_in_order(
                    plain_matrix, col_order_asc
                )
                candidates[f"{prefix}/cols_by_digit_sum_desc"] = read_columns_in_order(
                    plain_matrix, col_order_desc
                )

                for one_based in (False, True):
                    base_label = "one" if one_based else "zero"
                    candidates[f"{prefix}/row_sum_select_{base_label}"] = select_rows(
                        plain_matrix, digit_rows, one_based
                    )
                    candidates[f"{prefix}/col_sum_select_{base_label}"] = select_columns(
                        plain_matrix, digit_cols, one_based
                    )

                    offset = 1 if one_based else 0
                    repeated_row_select = []
                    repeated_col_select = []
                    for row in range(rows):
                        for col in range(cols):
                            digit = digit_matrix[row][col] - offset
                            repeated_row_select.append(plain_matrix[row][digit % cols])
                            repeated_col_select.append(plain_matrix[digit % rows][col])
                    candidates[f"{prefix}/cell_digit_select_row_{base_label}"] = "".join(
                        repeated_row_select
                    )
                    candidates[f"{prefix}/cell_digit_select_col_{base_label}"] = "".join(
                        repeated_col_select
                    )
    return candidates


def clue_hits(candidates):
    return {
        label: tuple(word for word in CLUE_WORDS if word in value.lower())
        for label, value in candidates.items()
        if any(word in value.lower() for word in CLUE_WORDS)
    }


def oracle_check(values, blobs):
    tested_keystrings = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for label, value in values.items():
        for form in sorted(answer_forms(value)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested_keystrings:
                    continue
                tested_keystrings.add(keystring)

                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((label, keystring, result))

                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((label, keystring, result))

                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((label, keystring, result))

                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((label, keystring, result))

    return {
        "candidate_count": len(values),
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "hits": hits,
    }


def audit():
    index_outputs = {
        "target(Phase51-crosscheck)": index_probe(TARGET),
        "dbbi": index_probe(DBBI),
        "source(phase3.2.2 plaintext)": index_probe(SOURCE),
        "validation_answer": index_probe(VALIDATION_ANSWER),
    }
    matrix = matrix_candidates()
    return {
        "index_outputs": index_outputs,
        "index_clue_hits": {
            source: clue_hits(outputs) for source, outputs in index_outputs.items()
        },
        "matrix_candidates": matrix,
        "matrix_clue_hits": clue_hits(matrix),
    }


def print_report(report):
    print("[*] literal-index probe (positions 23, 16, 7 into each source):")
    for source, outputs in report["index_outputs"].items():
        print(f"    {source}:")
        for label, value in outputs.items():
            print(f"        {label}: {value!r}")
    print("[*] index-probe clue hits:")
    for source, hits in report["index_clue_hits"].items():
        if hits:
            print(f"    {source}: {hits}")
    if not any(report["index_clue_hits"].values()):
        print("    none")
    print(f"[*] matrix candidates generated: {len(report['matrix_candidates'])}")
    print("[*] matrix candidate clue hits:")
    if report["matrix_clue_hits"]:
        for label, hits in report["matrix_clue_hits"].items():
            print(f"    {label}: {hits} <- {report['matrix_candidates'][label]!r}")
    else:
        print("    none")


def self_test():
    assert len(DBBI) == len(SOURCE) == len(VALIDATION_ANSWER) == 91
    assert len(TARGET) == 31
    # Phase 51 cross-check: this script's index_probe must reproduce the
    # already-published Phase 51 result for the one source it also covered.
    probe = index_probe(TARGET)
    assert probe["forward/zero"] == TARGET[23] + TARGET[16] + TARGET[7]
    assert probe["forward/one"] == TARGET[22] + TARGET[15] + TARGET[6]
    variants = plain_matrix_variants()
    assert len(variants) == 1 + len(FOLD_METHODS)
    for symbols in variants.values():
        assert len(symbols) == 91
        assert set(symbols) <= set("abcdefghi")
    candidates = matrix_candidates()
    # 2 shapes x 2 digit maps x 7 plain variants x 12 output kinds = 336
    # (4 order-based reads + 2 one-based variants x 4 selection kinds)
    assert len(candidates) == 2 * 2 * 7 * 12
    print("[*] self-test OK: index probe matches Phase 51 on TARGET; "
          f"{len(variants)} plain-matrix variants; {len(candidates)} matrix candidates")


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
        all_values = dict(report["matrix_candidates"])
        for source, outputs in report["index_outputs"].items():
            for label, value in outputs.items():
                all_values[f"index/{source}/{label}"] = value
        result = oracle_check(all_values, blobs)
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
