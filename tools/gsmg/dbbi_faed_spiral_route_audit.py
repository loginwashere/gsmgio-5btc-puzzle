#!/usr/bin/env python3
"""Spiral/boustrophedon ROUTE reads of the exact same grid shapes
`matrixsum_permutation_sweep.py` already established as bounded and
clue-supported -- no new dimensions invented here.

That sibling script fixes the only shapes this material is allowed to be
reshaped into (per its own docstring, citing
doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md): raw DBBI = 91 symbols = 7x13 or
13x7; {b,e}-segmented DBBI = 63 complete codes = 7x9 or 9x7; raw FAED = 570
symbols = 15x38 or 38x15 (explicitly no segmented-code matrix for FAED --
neither 436 nor 469 has a clue-supported factor pair). It then tests 10
bounded SORT-BY-SUM permutations per shape (row/col ascending/descending
gather, compound, and their inverses).

What it never tested: a ROUTE transposition -- how you READ the cells out,
independent of any row/column sum. This puzzle's own Stage 0 ("the seed is
planted") already used exactly this mechanic: a spiral read over a grid
image to extract the next-stage URL (doc/GSMG_PUZZLE.md's Stage 0 section).
Applying the same device to DBBI/FAED reuses a mechanic the creator is
independently confirmed to reach for, rather than inventing a new one.

Closed, bounded route family -- 5 distinct route geometries x 2 read
directions (forward, reverse) = 10 route-permutations per shape, chosen to
match the sibling script's own "10 bounded permutations per shape" scale
exactly (same order of magnitude, not an expanding search):

    spiral_cw_topleft       -- clockwise inward spiral, start top-left, first move right
    spiral_ccw_topleft      -- counter-clockwise inward spiral, start top-left, first move down
    spiral_topright_mirror  -- horizontal mirror of spiral_cw_topleft, start top-right
    snake_row_major         -- boustrophedon, row 0 L->R, row 1 R->L, ...
    snake_col_major         -- boustrophedon, col 0 T->B, col 1 B->T, ...

    each also read in reverse (a reversed inward spiral is an outward spiral
    from center -- reusing forward's coordinate list rather than writing a
    second generator is deliberate, not a shortcut: it is still bounded and
    disclosed, and it doubles coverage for free).

Every resulting reordering is still the exact same ciphertext content, no
new characters invented -- verified in the self-test the same way the
sibling script verifies its own permutations (sorted multiset equality).

Reuses matrixsum_permutation_sweep.py's reshape/segment_codes/DIGIT_MAP/
NINE_SYMS/CORE_ALPHABET_SEEDS/TARGET_ESCAPES, its Candidate dataclass and
scoring (make_candidate/text_score/score_output/direct_byte_bodies), its
MAGIC_SIGNATURES-driven signature check, and cb_common's decode_9ary/pad25/
aes_try_open/answer_forms/keystr_forms -- none of that is reimplemented
here, only the permutation-generation step (route reads instead of
sum-sorts) and the sweep/shuffle-gate loops that call it.

Usage:
    python3 tools/gsmg/dbbi_faed_spiral_route_audit.py --self-test
    python3 tools/gsmg/dbbi_faed_spiral_route_audit.py --top 20
    python3 tools/gsmg/dbbi_faed_spiral_route_audit.py --shuffle-gate --trials 300
"""
import argparse
import random
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from matrixsum_permutation_sweep import (  # noqa: E402
    CORE_ALPHABET_SEEDS,
    TARGET_ESCAPES,
    Candidate,
    direct_byte_bodies,
    make_candidate,
    print_candidate,
    reshape,
    score_output,
    segment_codes,
    text_score,
)
from cb_common import aes_try_open, answer_forms, decode_9ary, keystr_forms, pad25  # noqa: E402,F401


# ---------------------------------------------------------------------------
# Route generators: each returns a flat list of (row, col) read-order coords.
# ---------------------------------------------------------------------------

def spiral_cw_topleft(rows, cols):
    coords = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            coords.append((top, c))
        top += 1
        for r in range(top, bottom + 1):
            coords.append((r, right))
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                coords.append((bottom, c))
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                coords.append((r, left))
            left += 1
    return coords


def spiral_ccw_topleft(rows, cols):
    coords = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    while top <= bottom and left <= right:
        for r in range(top, bottom + 1):
            coords.append((r, left))
        left += 1
        for c in range(left, right + 1):
            coords.append((bottom, c))
        bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                coords.append((r, right))
            right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                coords.append((top, c))
            top += 1
    return coords


def spiral_topright_mirror(rows, cols):
    """Horizontal mirror of spiral_cw_topleft: start top-right, sweep the
    top row leftward first, then down, etc."""
    base = spiral_cw_topleft(rows, cols)
    return [(r, cols - 1 - c) for (r, c) in base]


def snake_row_major(rows, cols):
    coords = []
    for r in range(rows):
        cs = range(cols) if r % 2 == 0 else range(cols - 1, -1, -1)
        for c in cs:
            coords.append((r, c))
    return coords


def snake_col_major(rows, cols):
    coords = []
    for c in range(cols):
        rs = range(rows) if c % 2 == 0 else range(rows - 1, -1, -1)
        for r in rs:
            coords.append((r, c))
    return coords


ROUTE_GENERATORS = {
    "spiral_cw_topleft": spiral_cw_topleft,
    "spiral_ccw_topleft": spiral_ccw_topleft,
    "spiral_topright_mirror": spiral_topright_mirror,
    "snake_row_major": snake_row_major,
    "snake_col_major": snake_col_major,
}


def build_route_permutations(content_matrix, rows, cols):
    """10 bounded route-permutations (5 geometries x forward/reverse),
    applied to `content_matrix` -- mirrors the sibling script's
    build_permutations() signature/output shape (dict of name -> flat list),
    just with route reads instead of sum-sorts."""
    out = {}
    for name, generator in ROUTE_GENERATORS.items():
        coords = generator(rows, cols)
        forward = [content_matrix[r][c] for (r, c) in coords]
        out[name] = forward
        out[f"{name}_rev"] = list(reversed(forward))
    return out


def raw_symbol_route_shapes(ciphertext, rows, cols):
    symbol_matrix = reshape(list(ciphertext), rows, cols)
    permutations = build_route_permutations(symbol_matrix, rows, cols)
    return {name: "".join(chars) for name, chars in permutations.items()}


def segmented_code_route_shapes(ciphertext, e1, e2, rows, cols):
    codes = segment_codes(ciphertext, e1, e2)
    if codes is None or len(codes) != rows * cols:
        return None
    code_matrix = reshape(codes, rows, cols)
    permutations = build_route_permutations(code_matrix, rows, cols)
    return {name: "".join(chunks) for name, chunks in permutations.items()}


def all_route_shapes(target_name, ciphertext):
    """Yield (shape_label, {route_permutation_name: new_9ary_string}) -- the
    exact same 6 shapes as matrixsum_permutation_sweep.all_shapes(), route
    reads instead of sum-sort reads."""
    if target_name == "dbbi":
        for rows, cols in ((7, 13), (13, 7)):
            yield f"raw_{rows}x{cols}", raw_symbol_route_shapes(ciphertext, rows, cols)
        for rows, cols in ((7, 9), (9, 7)):
            result = segmented_code_route_shapes(ciphertext, "b", "e", rows, cols)
            if result is not None:
                yield f"segmented_be_{rows}x{cols}", result
    elif target_name == "faed":
        for rows, cols in ((15, 38), (38, 15)):
            yield f"raw_{rows}x{cols}", raw_symbol_route_shapes(ciphertext, rows, cols)


# ---------------------------------------------------------------------------
# Sweep / scoring -- identical logic to matrixsum_permutation_sweep.py's
# sweep_target/top_signal_stat/shuffle_gate, only swapping all_shapes() for
# all_route_shapes(). Not reimported directly since they close over the
# sibling module's own all_shapes; duplicated here at minimal size rather
# than monkey-patched, to keep this file independently readable.
# ---------------------------------------------------------------------------

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
    from matrixsum_permutation_sweep import printable_ratio
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

    for shape_label, permutations in all_route_shapes(target_name, ciphertext):
        for perm_name, new_stream in permutations.items():
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


def top_signal_stat(target_name, ciphertext):
    best = -1e18
    for shape_label, permutations in all_route_shapes(target_name, ciphertext):
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


def shuffle_gate(target_name, ciphertext, trials, seed=0):
    start = time.time()
    real_best = top_signal_stat(target_name, ciphertext)
    real_elapsed = time.time() - start
    _, _, real_stats = sweep_target(target_name, ciphertext, use_aes=False)

    rng = random.Random(seed)
    trial_start = time.time()
    null_bests = []
    for _ in range(trials):
        symbols = list(ciphertext)
        rng.shuffle(symbols)
        null_bests.append(top_signal_stat(target_name, "".join(symbols)))
    trial_elapsed = time.time() - trial_start
    at_least_as_good = sum(s >= real_best for s in null_bests)
    p_value = (at_least_as_good + 1) / (trials + 1)
    return {
        "target": target_name, "seed": seed, "trials": trials,
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


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def run_self_tests():
    # Hand-verified 3x3 grid (values 0..8, row-major) route orders.
    assert spiral_cw_topleft(3, 3) == [
        (0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (1, 1),
    ]
    assert spiral_ccw_topleft(3, 3) == [
        (0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (1, 1),
    ]
    assert spiral_topright_mirror(3, 3) == [
        (0, 2), (0, 1), (0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (1, 1),
    ]
    assert snake_row_major(3, 3) == [
        (0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0), (2, 0), (2, 1), (2, 2),
    ]
    assert snake_col_major(3, 3) == [
        (0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1), (0, 2), (1, 2), (2, 2),
    ]

    # Non-square 2x3 sanity check (rows != cols, matches this project's own
    # segmented-code shapes which are never square either).
    assert spiral_cw_topleft(2, 3) == [(0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0)]
    assert snake_row_major(2, 3) == [(0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0)]

    # No content lost/duplicated, for every one of the 6 real established
    # shapes -- exact multiset equality against the untouched source, same
    # check the sibling script runs on its own sum-sort permutations.
    for rows, cols in ((7, 13), (13, 7)):
        perms = raw_symbol_route_shapes(DBBI, rows, cols)
        assert len(perms) == 10, f"expected 10 route-permutations, got {len(perms)}"
        assert all(len(v) == 91 for v in perms.values())
        for v in perms.values():
            assert sorted(v) == sorted(DBBI)
    for rows, cols in ((7, 9), (9, 7)):
        seg = segmented_code_route_shapes(DBBI, "b", "e", rows, cols)
        assert seg is not None
        assert len(seg) == 10
        assert all(len(v) == 91 for v in seg.values())
        for v in seg.values():
            assert sorted(v) == sorted(DBBI)
    for rows, cols in ((15, 38), (38, 15)):
        perms = raw_symbol_route_shapes(FAED, rows, cols)
        assert len(perms) == 10
        assert all(len(v) == 570 for v in perms.values())
        for v in perms.values():
            assert sorted(v) == sorted(FAED)

    shapes = dict(all_route_shapes("dbbi", DBBI))
    assert set(shapes) == {"raw_7x13", "raw_13x7", "segmented_be_7x9", "segmented_be_9x7"}
    faed_shapes = dict(all_route_shapes("faed", FAED))
    assert set(faed_shapes) == {"raw_15x38", "raw_38x15"}

    print("[*] spiral/route self-tests passed: 5 geometries x fwd/rev = 10 "
          "route-permutations per shape, hand-verified on 3x3/2x3, no "
          "content lost/duplicated across all 6 established shapes")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", choices=("dbbi", "faed", "both"), default="both")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--no-aes", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--shuffle-gate", action="store_true")
    parser.add_argument("--trials", type=int, default=300)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    targets = {"dbbi": DBBI, "faed": FAED}
    selected = targets if args.target == "both" else {args.target: targets[args.target]}

    if args.shuffle_gate:
        for target_name, ciphertext in selected.items():
            result = shuffle_gate(target_name, ciphertext, args.trials, args.seed)
            print(f"[*] {target_name}: seed={result['seed']} trials={result['trials']:,}")
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
        print(f"\n[*] route-sweeping {target_name}: {len(ciphertext)} symbols")
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
