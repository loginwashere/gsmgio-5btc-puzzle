#!/usr/bin/env python3
"""`matrixsumlist` as a self-derived permutation key, per
doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md's "matrixsumlist as a Self-Derived
Permutation" section.

The existing instruction pipeline (matrix_instruction_sweep.py) computes
dbbi's row/column sums and turns them into candidate TEXT or SELECTORS over
the known Phase 3.2.2 answer. It never applies the sum-derived order as a
PERMUTATION KEY back onto the ciphertext that produced it. This does that,
and only that -- bounded to the exact, clue-supported matrix factorizations:

  - raw dbbi: 91 symbols = 7x13 or 13x7;
  - {b,e}-segmented dbbi: 63 complete codes = 7x9 or 9x7;
  - raw faed: 570 symbols = 15x38 or 38x15 (no segmented-code matrix for faed
    -- neither 436 nor 469 has a clue-supported factor pair, and the doc is
    explicit: do not invent arbitrary dimensions).

For each of those 6 shapes, row/column sums (a=0..i=8 digit mapping for raw
symbols; the natural 0..24 checkerboard code index for segmented codes -- see
dual_quinary_sweep.py) give a stable sort order. Verified: adding 1 to every
digit (a=1..i=9) changes the sums but not the order, so only one digit mapping
needs testing (asserted in the self-test, not re-swept).

Ten bounded permutations per shape: row/column ascending/descending (gather),
row-then-column (compound), and the inverse (scatter) of each of the four
gather forms. Every resulting reordering is still a valid rearrangement of the
EXACT SAME ciphertext content -- no new characters are invented.

Each permuted stream is fed through:
  - the checkerboard path (decode_9ary, a small clue-motivated alphabet/escape
    set, real AES oracle);
  - the direct-byte path (pack the digit/index stream directly, check
    signatures/printability/AES).

A shuffle-based null-model gate (shuffle the SYMBOL/code content, not the
derived order, then rebuild sums/order/permutation the identical way) must be
cleared before any output is treated as a lead, matching this project's
established practice.

Usage:
    python3 tools/gsmg/matrixsum_permutation_sweep.py --self-test
    python3 tools/gsmg/matrixsum_permutation_sweep.py --top 20
    python3 tools/gsmg/matrixsum_permutation_sweep.py --shuffle-gate --trials 5000 --workers 16
"""
import argparse
import math
import os
import random
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import aes_try_open, answer_forms, decode_9ary, keystr_forms, pad25  # noqa: E402
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402

NINE_SYMS = "abcdefghi"
DIGIT_MAP = {c: i for i, c in enumerate(NINE_SYMS)}

MAGIC_SIGNATURES = {
    b"Salted__": "openssl-salted",
    b"\x1f\x8b": "gzip",
    b"BZh": "bzip2",
    b"\xfd7zXZ\x00": "xz",
    b"PK\x03\x04": "zip",
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"%PDF-": "pdf",
    b"\x7fELF": "elf",
    b"SQLite format 3\x00": "sqlite",
    b"-----BEGIN ": "pem-or-armored",
}

# Clue-motivated alphabets + the established escape hypotheses for each target
# -- deliberately not a dictionary sweep (that space is already saturated).
CORE_ALPHABET_SEEDS = (
    "matrixsumlist", "lastwordsbeforearchichoice", "thispassword", "yinyang",
    "cosmicduality", "salphaseion", "causality", "architect", "choice",
    "enter", VALIDATION_ANSWER,
)
TARGET_ESCAPES = {
    "dbbi": [("b", "e"), ("e", "b")],
    "faed": [("g", "i"), ("i", "g"), ("h", "e"), ("e", "h")],
}


def natural_code_index(e1, e2, topology="top_first"):
    """Same intrinsic 0..24 checkerboard offset scheme as
    dual_quinary_sweep.py / cb_common.build_board_9ary() -- independent of any
    guessed alphabet."""
    tops = [c for c in NINE_SYMS if c not in (e1, e2)]
    if topology == "top_first":
        top_off, e1_off, e2_off = 0, 7, 16
    else:
        e1_off, e2_off, top_off = 0, 9, 18
    index = {}
    for k, c in enumerate(tops):
        index[c] = top_off + k
    for k, c2 in enumerate(NINE_SYMS):
        index[e1 + c2] = e1_off + k
    for k, c2 in enumerate(NINE_SYMS):
        index[e2 + c2] = e2_off + k
    return index


def segment_codes(s, e1, e2):
    """Split into complete codes, or None for a dangling trailing escape."""
    codes = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in (e1, e2):
            if i + 1 >= len(s):
                return None
            codes.append(s[i:i + 2])
            i += 2
        else:
            codes.append(ch)
            i += 1
    return codes


def reshape(items, rows, cols):
    if len(items) != rows * cols:
        raise ValueError(f"cannot reshape {len(items)} items as {rows}x{cols}")
    return [list(items[i * cols:(i + 1) * cols]) for i in range(rows)]


def row_sums(matrix):
    return [sum(row) for row in matrix]


def col_sums(matrix):
    rows, cols = len(matrix), len(matrix[0])
    return [sum(matrix[r][c] for r in range(rows)) for c in range(cols)]


def stable_order(values, reverse=False):
    if reverse:
        return sorted(range(len(values)), key=lambda i: (-values[i], i))
    return sorted(range(len(values)), key=lambda i: (values[i], i))


def inverse_order(order):
    inv = [0] * len(order)
    for k, idx in enumerate(order):
        inv[idx] = k
    return inv


def gather_rows(matrix, order):
    return [matrix[i] for i in order]


def scatter_rows(matrix, order):
    inv = inverse_order(order)
    return [matrix[inv[i]] for i in range(len(matrix))]


def gather_cols(matrix, order):
    return [[row[c] for c in order] for row in matrix]


def scatter_cols(matrix, order):
    inv = inverse_order(order)
    return [[row[c] for c in inv] for row in matrix]


def flatten(matrix):
    return [v for row in matrix for v in row]


def build_permutations(digit_matrix, content_matrix):
    """The 10 bounded permutations, applied to `content_matrix` (whatever is
    actually being rearranged: symbol characters or code strings) using sums
    computed from `digit_matrix` (always numeric)."""
    rsums, csums = row_sums(digit_matrix), col_sums(digit_matrix)
    row_asc, row_desc = stable_order(rsums), stable_order(rsums, reverse=True)
    col_asc, col_desc = stable_order(csums), stable_order(csums, reverse=True)

    out = {}
    out["row_asc"] = flatten(gather_rows(content_matrix, row_asc))
    out["row_desc"] = flatten(gather_rows(content_matrix, row_desc))
    out["col_asc"] = flatten(gather_cols(content_matrix, col_asc))
    out["col_desc"] = flatten(gather_cols(content_matrix, col_desc))
    out["row_then_col_asc"] = flatten(gather_cols(gather_rows(content_matrix, row_asc), col_asc))
    out["row_then_col_desc"] = flatten(gather_cols(gather_rows(content_matrix, row_desc), col_desc))
    out["inverse_row_asc"] = flatten(scatter_rows(content_matrix, row_asc))
    out["inverse_row_desc"] = flatten(scatter_rows(content_matrix, row_desc))
    out["inverse_col_asc"] = flatten(scatter_cols(content_matrix, col_asc))
    out["inverse_col_desc"] = flatten(scatter_cols(content_matrix, col_desc))
    return out


def raw_symbol_shapes(ciphertext, rows, cols):
    digits = [DIGIT_MAP[c] for c in ciphertext]
    digit_matrix = reshape(digits, rows, cols)
    symbol_matrix = reshape(list(ciphertext), rows, cols)
    permutations = build_permutations(digit_matrix, symbol_matrix)
    return {name: "".join(chars) for name, chars in permutations.items()}


def segmented_code_shapes(ciphertext, e1, e2, rows, cols):
    codes = segment_codes(ciphertext, e1, e2)
    if codes is None or len(codes) != rows * cols:
        return None
    index_map = natural_code_index(e1, e2)
    indices = [index_map[c] for c in codes]
    digit_matrix = reshape(indices, rows, cols)
    code_matrix = reshape(codes, rows, cols)
    permutations = build_permutations(digit_matrix, code_matrix)
    return {name: "".join(chunks) for name, chunks in permutations.items()}


def all_shapes(target_name, ciphertext):
    """Yield (shape_label, {permutation_name: new_9ary_string})."""
    if target_name == "dbbi":
        for rows, cols in ((7, 13), (13, 7)):
            yield f"raw_{rows}x{cols}", raw_symbol_shapes(ciphertext, rows, cols)
        for rows, cols in ((7, 9), (9, 7)):
            result = segmented_code_shapes(ciphertext, "b", "e", rows, cols)
            if result is not None:
                yield f"segmented_be_{rows}x{cols}", result
    elif target_name == "faed":
        for rows, cols in ((15, 38), (38, 15)):
            yield f"raw_{rows}x{cols}", raw_symbol_shapes(ciphertext, rows, cols)


@dataclass(frozen=True)
class Candidate:
    target: str
    shape: str
    permutation: str
    path: str
    detail: str
    length: int
    printable_ratio: float
    entropy: float
    longest_printable_run: int
    signature: str
    score: float
    hex_preview: str
    text_preview: str


def shannon_entropy(body):
    if not body:
        return 0.0
    counts = Counter(body)
    return -sum((c / len(body)) * math.log2(c / len(body)) for c in counts.values())


def printable_ratio(body):
    if not body:
        return 0.0
    return sum(b in (9, 10, 13) or 32 <= b < 127 for b in body) / len(body)


def longest_printable_run(body):
    return max((len(r) for r in re.findall(rb"[ -~]{2,}", body)), default=0)


def signature_name(body):
    for sig, name in MAGIC_SIGNATURES.items():
        if body.startswith(sig):
            return name
    return ""


def text_preview(body, limit=96):
    return "".join(chr(b) if 32 <= b < 127 else "." for b in body[:limit])


def score_output(body):
    """Byte-oriented score for the direct-byte path, where a high printable
    ratio/long run is itself informative (most byte content is NOT printable
    by chance)."""
    ratio, run, sig = printable_ratio(body), longest_printable_run(body), signature_name(body)
    score = ratio * 100 + min(run, 40) * 1.5 + (1000 if sig else 0)
    return score, ratio, run, sig


# checkerboard-path candidates are ALWAYS pure A-Z letters (decode_9ary never
# emits anything else once "?" is excluded) -- printable_ratio/longest_run are
# trivially saturated (ratio=1.0, run=full length) for every single valid
# decode, real or shuffled. Confirmed via the shuffle gate itself: without a
# language-content score, real_best/null_mean/null_max were all identically
# 160.0 (the byte-score ceiling), giving a meaningless p=1.0 for BOTH targets
# -- not evidence of a clean negative, evidence the statistic couldn't
# measure anything. Needs real word-content scoring instead, same idea as
# matrix_instruction_sweep.py's COMMON_WORDS bonus.
COMMON_WORDS = (
    "THE", "THIS", "PASSWORD", "PRIVATE", "KEY", "MATRIX", "SUM", "LIST",
    "CHOICE", "ENTER", "LAST", "WORDS", "BEFORE", "ARCHITECT", "PRIME",
    "HALF", "BETTER", "ANSWER", "SOURCE", "CODE", "YOUR", "YOU", "DUALITY",
    "COSMIC", "YIN", "YANG",
)


def text_score(text):
    upper = text.upper()
    word_score = sum(len(word) * upper.count(word) for word in COMMON_WORDS)
    diversity = len(set(upper)) if text else 0
    return word_score * 10 + diversity


def make_candidate(target, shape, permutation, path, detail, body, text=None):
    """`text` (the decoded A-Z answer) is only set for the checkerboard path;
    when present it drives the actual ranking score, since byte-level
    printable-ratio/run stats are uninformative there (see above). The
    direct-byte path (text=None) keeps the original byte-oriented score."""
    ratio, run, sig = printable_ratio(body), longest_printable_run(body), signature_name(body)
    score = text_score(text) if text is not None else score_output(body)[0]
    return Candidate(
        target=target, shape=shape, permutation=permutation, path=path, detail=detail,
        length=len(body), printable_ratio=round(ratio, 6), entropy=round(shannon_entropy(body), 6),
        longest_printable_run=run, signature=sig, score=round(score, 6),
        hex_preview=body[:48].hex(), text_preview=text_preview(body),
    )


def direct_byte_bodies(new_stream):
    """Direct-byte path: the permuted digit/index values packed directly."""
    digits = [DIGIT_MAP.get(c) for c in new_stream]
    if all(d is not None for d in digits):
        yield "digits_as_bytes", bytes(digits)
        value = 0
        for d in digits:
            value = value * 9 + d
        byte_length = max(1, (value.bit_length() + 7) // 8)
        yield "whole_base9", value.to_bytes(byte_length, "big")


def try_aes_text(text, tested):
    hits = []
    for form in answer_forms(text):
        if not form:
            continue
        for keystring in keystr_forms(form):
            if keystring in tested:
                continue
            tested.add(keystring)
            result = aes_try_open(keystring)
            if result:
                tag, plaintext, digest_name, key_len = result
                hits.append({
                    "form": form, "keystring": keystring, "blob": tag,
                    "kdf": f"{digest_name}/aes{key_len * 8}",
                    "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                })
    return hits


def try_aes_bytes(body, tested):
    if printable_ratio(body) < 0.85:
        return []
    try:
        text = body.decode("ascii")
    except UnicodeDecodeError:
        return []
    return try_aes_text(text, tested)


def sweep_target(target_name, ciphertext, use_aes=True):
    results_by_body = {}
    hits = []
    tested = set()

    for shape_label, permutations in all_shapes(target_name, ciphertext):
        for perm_name, new_stream in permutations.items():
            # checkerboard path
            for e1, e2 in TARGET_ESCAPES[target_name]:
                for seed in CORE_ALPHABET_SEEDS:
                    alphabet = pad25(seed)
                    if len(alphabet) != 25:
                        continue
                    answer = decode_9ary(new_stream, alphabet, e1, e2)
                    if "?" in answer:
                        continue
                    body = answer.encode()
                    candidate = make_candidate(
                        target_name, shape_label, perm_name, "checkerboard",
                        f"escapes={e1}{e2} seed={seed[:20]}", body, text=answer,
                    )
                    previous = results_by_body.get(body)
                    if previous is None or candidate.score > previous.score:
                        results_by_body[body] = candidate
                    if use_aes:
                        for hit in try_aes_text(answer, tested):
                            hits.append({**hit, "target": target_name, "shape": shape_label,
                                         "permutation": perm_name, "path": "checkerboard"})

            # direct-byte path
            for decoder, body in direct_byte_bodies(new_stream):
                candidate = make_candidate(
                    target_name, shape_label, perm_name, "direct_byte", decoder, body,
                )
                previous = results_by_body.get(body)
                if previous is None or candidate.score > previous.score:
                    results_by_body[body] = candidate
                if use_aes:
                    for hit in try_aes_bytes(body, tested):
                        hits.append({**hit, "target": target_name, "shape": shape_label,
                                     "permutation": perm_name, "path": "direct_byte"})

    ranked = sorted(
        results_by_body.values(),
        key=lambda c: (c.score, c.printable_ratio, c.longest_printable_run),
        reverse=True,
    )
    stats = {"unique_outputs": len(ranked), "aes_keystrings": len(tested), "aes_hits": len(hits)}
    return ranked, hits, stats


def print_candidate(candidate, rank):
    flags = []
    if candidate.signature:
        flags.append(f"signature={candidate.signature}")
    flags.append(f"print={candidate.printable_ratio:.3f}")
    flags.append(f"entropy={candidate.entropy:.3f}")
    flags.append(f"run={candidate.longest_printable_run}")
    print(
        f"[{rank:3d}] score={candidate.score:7.2f} {candidate.target} {candidate.shape} "
        f"{candidate.permutation}/{candidate.path} ({candidate.detail}) "
        f"len={candidate.length} {' '.join(flags)}"
    )
    print(f"      text: {candidate.text_preview}")


def top_signal_stat(target_name, ciphertext):
    """Max score across every shape/permutation/path -- the max-statistic
    used by the shuffle gate."""
    best = -1e18
    for shape_label, permutations in all_shapes(target_name, ciphertext):
        for perm_name, new_stream in permutations.items():
            for e1, e2 in TARGET_ESCAPES[target_name]:
                for seed in CORE_ALPHABET_SEEDS:
                    alphabet = pad25(seed)
                    if len(alphabet) != 25:
                        continue
                    answer = decode_9ary(new_stream, alphabet, e1, e2)
                    if "?" in answer:
                        continue
                    best = max(best, text_score(answer))
            for _, body in direct_byte_bodies(new_stream):
                best = max(best, score_output(body)[0])
    return best


def _trial_best(args):
    target_name, ciphertext, trial_seed = args
    rng = random.Random(trial_seed)
    symbols = list(ciphertext)
    rng.shuffle(symbols)
    return top_signal_stat(target_name, "".join(symbols))


def shuffle_gate(target_name, ciphertext, trials, seed=0, workers=1):
    import time as _time

    start = _time.time()
    real_best = top_signal_stat(target_name, ciphertext)
    real_elapsed = _time.time() - start
    _, _, real_stats = sweep_target(target_name, ciphertext, use_aes=False)

    rng = random.Random(seed)
    trial_args = [(target_name, ciphertext, rng.getrandbits(64)) for _ in range(trials)]
    trial_start = _time.time()
    if workers == 1:
        null_bests = [_trial_best(a) for a in trial_args]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            null_bests = list(
                ex.map(_trial_best, trial_args, chunksize=max(1, trials // (workers * 8)))
            )
    trial_elapsed = _time.time() - trial_start
    at_least_as_good = sum(s >= real_best for s in null_bests)
    p_value = (at_least_as_good + 1) / (trials + 1)
    return {
        "target": target_name, "seed": seed, "trials": trials, "workers": workers,
        "unique_outputs_after_dedup": real_stats["unique_outputs"],
        "real_best_score": round(real_best, 4),
        "null_mean": round(sum(null_bests) / len(null_bests), 4),
        "null_max": round(max(null_bests), 4),
        "at_least_as_good_count": at_least_as_good,
        "empirical_p_family_wise": round(p_value, 5),
        "seconds_per_trial": round(trial_elapsed / trials, 4),
        "real_stat_compute_seconds": round(real_elapsed, 4),
        "total_shuffle_seconds": round(trial_elapsed, 2),
    }


def run_self_tests():
    assert reshape([1, 2, 3, 4, 5, 6], 2, 3) == [[1, 2, 3], [4, 5, 6]]
    assert row_sums([[1, 2], [3, 4]]) == [3, 7]
    assert col_sums([[1, 2], [3, 4]]) == [4, 6]
    assert stable_order([3, 1, 1, 2]) == [1, 2, 3, 0]
    assert stable_order([3, 1, 1, 2], reverse=True) == [0, 3, 1, 2]
    order = stable_order([3, 1, 2])
    assert inverse_order(order)[order[0]] == 0

    m = [["a", "b"], ["c", "d"]]
    assert gather_rows(m, [1, 0]) == [["c", "d"], ["a", "b"]]
    assert scatter_rows(gather_rows(m, [1, 0]), [1, 0]) == m  # round trip
    assert gather_cols(m, [1, 0]) == [["b", "a"], ["d", "c"]]
    assert scatter_cols(gather_cols(m, [1, 0]), [1, 0]) == m  # round trip
    assert flatten(m) == ["a", "b", "c", "d"]

    # Verified 2026-07-23: exact column sums/order for raw dbbi under a=0..i=8.
    digits = [DIGIT_MAP[c] for c in DBBI]
    dm = reshape(digits, 7, 13)
    assert col_sums(dm) == [21, 31, 35, 30, 17, 26, 8, 27, 28, 32, 19, 26, 31]
    assert stable_order(col_sums(dm)) == [6, 4, 10, 0, 5, 11, 7, 8, 3, 1, 12, 9, 2]
    # a=1..i=9 changes sums but not order (doc's stated invariant) -- checked,
    # not separately swept.
    digits_plus1 = [d + 1 for d in digits]
    dm_plus1 = reshape(digits_plus1, 7, 13)
    assert stable_order(col_sums(dm_plus1)) == stable_order(col_sums(dm))

    codes = segment_codes(DBBI, "b", "e")
    assert len(codes) == 63
    perms = raw_symbol_shapes(DBBI, 7, 13)
    assert len(perms) == 10
    assert all(len(v) == 91 for v in perms.values())
    assert sorted(perms["row_asc"]) == sorted(DBBI)  # same multiset, reordered
    seg = segmented_code_shapes(DBBI, "b", "e", 7, 9)
    assert seg is not None
    assert all(len(v) == 91 for v in seg.values())
    assert sorted(seg["row_asc"]) == sorted(DBBI)

    shapes = dict(all_shapes("dbbi", DBBI))
    assert set(shapes) == {"raw_7x13", "raw_13x7", "segmented_be_7x9", "segmented_be_9x7"}
    faed_shapes = dict(all_shapes("faed", FAED))
    assert set(faed_shapes) == {"raw_15x38", "raw_38x15"}

    print("[*] matrixsum-permutation self-tests passed")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", choices=("dbbi", "faed", "both"), default="both")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--no-aes", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--shuffle-gate", action="store_true")
    parser.add_argument("--trials", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()

    targets = {"dbbi": DBBI, "faed": FAED}
    selected = targets if args.target == "both" else {args.target: targets[args.target]}

    if args.shuffle_gate:
        for target_name, ciphertext in selected.items():
            result = shuffle_gate(target_name, ciphertext, args.trials, args.seed, args.workers)
            print(f"[*] {target_name}: seed={result['seed']} trials={result['trials']:,} workers={result['workers']}")
            print(f"    unique_outputs_after_dedup={result['unique_outputs_after_dedup']:,}")
            print(f"    real_best_score={result['real_best_score']}")
            print(
                f"    null_mean={result['null_mean']} null_max={result['null_max']} "
                f"at_least_as_good={result['at_least_as_good_count']}/{result['trials']}"
            )
            print(f"    empirical_p_family_wise={result['empirical_p_family_wise']}")
            print(
                f"    seconds_per_trial={result['seconds_per_trial']} "
                f"(real_stat={result['real_stat_compute_seconds']}s, "
                f"total_shuffle={result['total_shuffle_seconds']}s)"
            )
        return

    total_hits = 0
    for target_name, ciphertext in selected.items():
        print(f"\n[*] sweeping {target_name}: {len(ciphertext)} symbols")
        ranked, hits, stats = sweep_target(target_name, ciphertext, use_aes=not args.no_aes)
        print(
            f"[*] {stats['unique_outputs']:,} unique outputs, "
            f"{stats['aes_keystrings']:,} AES keystrings, {stats['aes_hits']} hits"
        )
        for rank, candidate in enumerate(ranked[:args.top], 1):
            print_candidate(candidate, rank)
        for hit in hits:
            print(f"\n[+++ AES HIT] {hit}\n")
        total_hits += len(hits)

    if total_hits == 0:
        print("\n[*] no candidate opened either AES blob")


if __name__ == "__main__":
    main()
