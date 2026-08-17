#!/usr/bin/env python3
"""Candidate family -- joint DBBI x FAED positional co-occurrence matrix (2026-08-16).

Executes idea 2 from
doc/Brainstorms/2026-08-15 - DBBI FAED FEFE Fresh Divergence.md, unblocked
by that doc's dedup check: the closed six-lane audit
(`dbbi_faed_six_lane_audit.py`) scores 8 per-lane/per-column equality and
residual measures, none of which build or sum a joint co-occurrence matrix,
so this is a genuinely different statistic, not a re-run of closed ground.

A literal reading of "matrixsumlist" is executed here: walk `DBBI` and
`FAED` in lockstep, treat each `(DBBI[i], FAED[j])` symbol pair as a
`(row, col)` coordinate into a 9x9 grid over the canonical `a`-`i` alphabet
(index order, `a`=0 .. `i`=8 -- the single default indexing already used
elsewhere in this project's DBBI/FAED work, not a second variant), and
literally sum the resulting matrix's rows, columns, and both diagonals, as
"matrixsumlist" names.

There is no authenticated rule for exactly how DBBI (91 symbols) and FAED
(570 symbols = 6x91+24) should be paired index-for-index, so two -- and
only two -- pre-registered, mechanically distinct pairings are tried, both
literal readings of "walk in lockstep":

  A. wrap_full   -- DBBI cycles (`DBBI[i % 91]`) against the full 570-symbol
                    FAED, one matrix over all 570 pairs.
  B. pool_lanes   -- DBBI paired index-for-index against each of FAED's six
                    91-symbol lanes (`DBBI[i]` vs `lane_k[i]`), all 6x91=546
                    pairs pooled into a single matrix (FAED's 24-symbol tail
                    is excluded, matching the six-lane audit's own scope).

For each of the 2 matrices, 6 candidate strings are derived by a fixed,
pre-declared rule (not tuned after inspection): the 9 row sums
zero-padded/concatenated, the 9 column sums zero-padded/concatenated, the
main-diagonal sum, the anti-diagonal sum, their concatenation, and the
row-then-column concatenation. 12 candidates total, each run through
`keystr_forms()` (raw / SHA-256 / double-SHA-256, this project's standard
"hash of a computed artifact" convention) against all four tracked blobs
under the standard CBC oracle: 36 passphrase attempts.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent

from cb_common import BLOBS, aes_try_open_bytes, keystr_forms  # noqa: E402
from data import DBBI, FAED  # noqa: E402

ALPHABET = "abcdefghi"
LANE_COUNT = 6
LANE_WIDTH = 91


def build_matrix(pairs):
    m = [[0] * 9 for _ in range(9)]
    for a, b in pairs:
        r, c = ALPHABET.index(a), ALPHABET.index(b)
        m[r][c] += 1
    return m


def wrap_full_pairs():
    return [(DBBI[i % len(DBBI)], FAED[i]) for i in range(len(FAED))]


def pool_lanes_pairs():
    pairs = []
    for k in range(LANE_COUNT):
        lane = FAED[k * LANE_WIDTH : (k + 1) * LANE_WIDTH]
        pairs.extend((DBBI[i], lane[i]) for i in range(LANE_WIDTH))
    return pairs


def matrix_models():
    return {
        "wrap_full": build_matrix(wrap_full_pairs()),
        "pool_lanes": build_matrix(pool_lanes_pairs()),
    }


def matrix_candidates(matrix):
    row_sums = [sum(row) for row in matrix]
    col_sums = [sum(matrix[r][c] for r in range(9)) for c in range(9)]
    diag_main = sum(matrix[i][i] for i in range(9))
    diag_anti = sum(matrix[i][8 - i] for i in range(9))

    row_str = "".join(f"{v:03d}" for v in row_sums)
    col_str = "".join(f"{v:03d}" for v in col_sums)

    return {
        "row_sums": row_str,
        "col_sums": col_str,
        "diag_main": str(diag_main),
        "diag_anti": str(diag_anti),
        "diag_concat": f"{diag_main}{diag_anti}",
        "row_col_concat": row_str + col_str,
    }


def all_candidate_strings():
    candidates = {}
    for model_name, matrix in matrix_models().items():
        for stat_name, value in matrix_candidates(matrix).items():
            candidates[f"{model_name}/{stat_name}"] = value
    return candidates


def run():
    candidates = all_candidate_strings()
    attempts = []
    hits = []
    for label, form in candidates.items():
        for keystr in keystr_forms(form):
            result = aes_try_open_bytes(keystr.encode())
            attempts.append({"label": label, "form": form, "keystr": keystr})
            if result:
                tag, body, kdf_label, key_len = result
                hits.append({
                    "label": label,
                    "form": form,
                    "keystr": keystr,
                    "blob": tag,
                    "kdf": f"{kdf_label}/aes{key_len * 8}",
                    "plaintext_hex": body.hex(),
                })
    return {
        "candidate_labels": list(candidates.keys()),
        "candidate_string_count": len(candidates),
        "passphrase_attempts": len(attempts),
        "blobs": tuple(BLOBS),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    models = matrix_models()
    assert set(models) == {"wrap_full", "pool_lanes"}
    for name, m in models.items():
        assert len(m) == 9 and all(len(row) == 9 for row in m), f"{name} must be 9x9"
    total_wrap = sum(sum(row) for row in models["wrap_full"])
    total_pool = sum(sum(row) for row in models["pool_lanes"])
    assert total_wrap == len(FAED), f"wrap_full must cover all {len(FAED)} FAED symbols, got {total_wrap}"
    assert total_pool == LANE_COUNT * LANE_WIDTH, f"pool_lanes must cover {LANE_COUNT * LANE_WIDTH} pairs, got {total_pool}"

    candidates = all_candidate_strings()
    assert len(candidates) == 12, f"expected 12 candidates (2 models x 6 stats), got {len(candidates)}"
    for label, form in candidates.items():
        assert form, f"{label} produced an empty candidate"

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 36, f"expected 36 passphrase attempts (12 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: 2 matrix models, totals {total_wrap}/{total_pool} pairs covered, "
          f"{len(candidates)} candidates, {attempts} passphrase attempts")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    if args.show:
        for label, form in all_candidate_strings().items():
            print(f"{label}: {form}")
        return

    if not args.run:
        parser.print_help()
        return

    report = run()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
