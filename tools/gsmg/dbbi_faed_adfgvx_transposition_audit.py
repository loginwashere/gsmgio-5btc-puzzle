#!/usr/bin/env python3
"""Tests a keyed COLUMNAR TRANSPOSITION layer on DBBI/FAED -- the real
second stage of the historical WWI ADFGVX cipher (fractionate via a
Polybius-style grid, then transpose the resulting digit/letter stream by a
keyword's alphabetical column order). Distinct from Phase 310's Nihilist
additive-key test (dbbi_faed_nihilist_additive_audit.py): that mechanism
ADDS a numeric key to the checkerboard code-slot sequence; this one
PERMUTES the same sequence -- a different operation entirely, motivated by
`doc/GSMG_PUZZLE.md`'s own "unknown #4" (a transposition/over-encryption
keystream layered on top of the checkerboard), here made concrete as the
specific historical ADFGVX recipe rather than an unspecified transposition.

Mechanism tested: segment DBBI/FAED into their intrinsic 0-24 checkerboard
code-slot sequence exactly as Phase 310 does (slot_sequence(), reused
directly, same escape-pair/topology variants). For each of the 11
CORE_ALPHABET_SEEDS keywords, write the slot sequence into a grid of
len(keyword) columns (row-major, ragged last row), read columns out in the
keyword's alphabetical rank order (ties broken left-to-right) -- classic
columnar transposition. Both directions are tested against the given
(already-ciphertext) slot sequence, since it's unknown which direction the
puzzle would need:
  - `transpose`: treat the given slots as the pre-transposition order and
    apply the encrypt-direction column readout.
  - `untranspose`: treat the given slots as the post-transposition
    (already-scrambled) order and apply the decrypt-direction column
    fill/row readout.
Each of the two resulting reorderings is then hill-climbed for the best
25-slot-to-letter assignment using Phase 310's exact quadgram-fitness
search (score()/hillclimb_slots(), reused directly, not reimplemented). A
real transposition layer would show up as a reordering that scores
dramatically better than the established unshifted baseline for that
variant -- same standard Phase 310/311 already established (their best
shifted scores beat baseline by only ~7-8 points on a ~300-point scale =
no signal; a genuine decode should separate by a much wider margin).

This is a bounded exploratory pass (same 800 iters/30 restarts budget as
Phase 310/311) to check whether the idea is worth a full canonical run --
not a final closure either way on its own.

Per-search seeds use a deterministic hash (hashlib.md5 of a repr string,
not Python's built-in hash()) specifically so results are reproducible
across separate process invocations -- Python randomizes str/tuple hash()
per-process by default (PYTHONHASHSEED), so the built-in hash() used for
this purpose in dbbi_faed_nihilist_additive_audit.py's Phase 310 run makes
that script's per-keyword seeds (and therefore which keyword's hillclimb
lands best) non-reproducible from run to run. Confirmed directly: two
otherwise-identical runs of this script's predecessor design produced
different top keywords (+22.4 under lastwordsbeforearchichoice/untranspose
vs. +31.5 under yinyang/transpose on a separate invocation) purely from
that non-determinism, not from any property of the keys themselves --
itself evidence pointing toward "generic artifact of a many-way search,"
not "one specific key stands out." Not fixed in the already-logged Phase
310/311 script itself (would silently change already-recorded, closed-
phase output); fixed here since this script's results were not yet logged.

Reproduce with:
    python3 tools/gsmg/dbbi_faed_adfgvx_transposition_audit.py --self-test
    python3 tools/gsmg/dbbi_faed_adfgvx_transposition_audit.py
"""
import argparse
import hashlib
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from dbbi_faed_nihilist_additive_audit import (  # noqa: E402
    TARGETS,
    TOPOLOGIES,
    hillclimb_slots,
    slot_sequence,
)
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS  # noqa: E402


def stable_seed(*parts):
    """Deterministic across process invocations, unlike Python's built-in
    hash() on str/tuple (randomized per-process via PYTHONHASHSEED)."""
    digest = hashlib.md5(repr(parts).encode()).hexdigest()
    return int(digest, 16) & 0xffff


def rank_order(keyword):
    """Column read order for a columnar transposition keyword: sort column
    indices by (letter, original index), ties broken left-to-right -- the
    standard convention (e.g. keyword ZEBRA -> letters Z,E,B,R,A -> read
    order [4,2,1,3,0], since alphabetically A<B<E<R<Z)."""
    letters = [c for c in keyword.upper() if c.isalpha()]
    return sorted(range(len(letters)), key=lambda i: (letters[i], i)), letters


def transpose(slots, keyword):
    """Encrypt-direction columnar transposition: write `slots` row-major
    into a grid of len(keyword) columns, read columns out in the keyword's
    alphabetical rank order. Ragged last row -- no padding value is ever
    emitted, output length always equals len(slots)."""
    order, letters = rank_order(keyword)
    ncols = len(letters)
    if ncols == 0:
        return None
    nrows = -(-len(slots) // ncols)
    padded = list(slots) + [None] * (nrows * ncols - len(slots))
    grid = [padded[r * ncols:(r + 1) * ncols] for r in range(nrows)]
    out = []
    for c in order:
        for r in range(nrows):
            v = grid[r][c]
            if v is not None:
                out.append(v)
    return out


def _col_real_counts(nrows, ncols, pad_count):
    counts = {c: nrows for c in range(ncols)}
    for c in range(ncols - pad_count, ncols):
        counts[c] = nrows - 1
    return counts


def untranspose(slots, keyword, original_length=None):
    """Decrypt-direction columnar transposition: treat `slots` as already
    being in transposed (column-read) order and restore row-major order.
    `original_length` defaults to len(slots) (the normal use here: treating
    the given ciphertext slot sequence itself as the transposed stream)."""
    if original_length is None:
        original_length = len(slots)
    order, letters = rank_order(keyword)
    ncols = len(letters)
    if ncols == 0:
        return None
    nrows = -(-original_length // ncols)
    pad_count = nrows * ncols - original_length
    counts = _col_real_counts(nrows, ncols, pad_count)

    grid = [[None] * ncols for _ in range(nrows)]
    pos = 0
    for c in order:
        cnt = counts[c]
        for r in range(cnt):
            grid[r][c] = slots[pos]
            pos += 1
    if pos != len(slots):
        return None  # length mismatch -- not a valid transposed stream at this length

    out = []
    for r in range(nrows):
        for c in range(ncols):
            v = grid[r][c]
            if v is not None:
                out.append(v)
    return out


def self_test():
    # Independently hand-derived: keyword ZEBRA -> letters Z,E,B,R,A ->
    # alphabetical order A(idx4),B(idx2),E(idx1),R(idx3),Z(idx0) -> rank
    # order (columns to read, in order) = [4,2,1,3,0].
    order, letters = rank_order("ZEBRA")
    assert letters == list("ZEBRA")
    assert order == [4, 2, 1, 3, 0], order

    # 13 items into 5 columns -> 3 rows, ragged (pad_count=2, so columns 3
    # and 4 have only 2 real rows). Grid (row-major):
    #   row0: 0 1 2 3 4
    #   row1: 5 6 7 8 9
    #   row2: 10 11 12 _ _
    # Read order [4,2,1,3,0] ->
    #   col4(2 rows): 4,9 | col2(3 rows): 2,7,12 | col1(3 rows): 1,6,11
    #   col3(2 rows): 3,8 | col0(3 rows): 0,5,10
    expected = [4, 9, 2, 7, 12, 1, 6, 11, 3, 8, 0, 5, 10]
    slots = list(range(13))
    got = transpose(slots, "ZEBRA")
    assert got == expected, (got, expected)

    # No value invented or dropped -- same multiset, same length.
    assert sorted(got) == sorted(slots)
    assert len(got) == len(slots)

    # Round trip: untranspose(transpose(x)) == x.
    back = untranspose(got, "ZEBRA", original_length=len(slots))
    assert back == slots, (back, slots)

    # Round trip also holds for a real DBBI slot sequence and a
    # CORE_ALPHABET_SEEDS keyword (including a length-91 keyword against a
    # 63-element sequence -- ncols > len(slots), degenerate but must still
    # round-trip cleanly).
    dbbi_raw = TARGETS["DBBI"][0]
    real_slots = slot_sequence(dbbi_raw, "b", "e", "top_first")
    for kw in list(CORE_ALPHABET_SEEDS) + ["a"]:
        t = transpose(real_slots, kw)
        assert sorted(t) == sorted(real_slots), kw
        u = untranspose(t, kw, original_length=len(real_slots))
        assert u == real_slots, kw

    print("self-test OK: rank order, hand-derived transpose example, "
          "no-value-lost invariant, and forward/inverse round-trip "
          "(including the degenerate 91-letter-keyword case) all verified")


def build_candidates():
    """(name, e1, e2, topo, base_slots) for every Phase-310 variant."""
    variants = []
    for name, (raw, pairs) in TARGETS.items():
        for e1, e2 in pairs:
            for topo in TOPOLOGIES:
                base = slot_sequence(raw, e1, e2, topo)
                if base is not None:
                    variants.append((name, e1, e2, topo, base))
    return variants


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--restarts", type=int, default=30)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    variants = build_candidates()
    total_searches = len(variants) * (1 + len(CORE_ALPHABET_SEEDS) * 2)
    print(f"[*] {len(variants)} escape-pair/topology variants x "
          f"(1 baseline + {len(CORE_ALPHABET_SEEDS)} keywords x 2 directions) "
          f"= {total_searches} hillclimb searches")

    results = []
    for name, e1, e2, topo, base_slots in variants:
        base_best = hillclimb_slots(base_slots, args.iters, args.restarts, seed=0)
        print(f"[{name} {e1}/{e2} {topo}] BASELINE (no transposition) score={base_best[0]:.1f}")
        results.append((base_best[0], name, e1, e2, topo, "BASELINE", None))

        for kw in CORE_ALPHABET_SEEDS:
            for direction, fn in (("transpose", transpose), ("untranspose", untranspose)):
                reordered = fn(base_slots, kw) if direction == "transpose" \
                    else fn(base_slots, kw, original_length=len(base_slots))
                if reordered is None or sorted(reordered) != sorted(base_slots):
                    continue
                seed = stable_seed(name, e1, e2, topo, kw, direction)
                best = hillclimb_slots(reordered, args.iters, args.restarts, seed=seed)
                results.append((best[0], name, e1, e2, topo, kw, direction))

    results.sort(key=lambda r: -r[0])
    print(f"\n[*] {len(results)} total results (incl. baselines). Top 15 by score "
          f"(BASELINE rows show the unshifted reference to beat):")
    for score_, name, e1, e2, topo, kw, label in results[:15]:
        tag = kw if kw == "BASELINE" else f"{kw}/{label}"
        print(f"  {score_:8.1f}  {name} {e1}/{e2} {topo}  key={tag}")


if __name__ == "__main__":
    main()
