#!/usr/bin/env python3
"""Phase 545 -- keyword cascade and tail-derived squares over the project's 91/570 strings.

Protocol: doc/Brainstorms/2026-09-21 - Phase 545 Keyword Cascade and Tail-Derived
Square Protocol.md (written before any cascade output was scored).

Options 4 and 5 of the BTCSEED tail brainstorm, one closed universe:

  Squares  K^r_t for rule r in {7, 13, full} and t = 1..3, where K^r_0 = DBBI[:13],
           D^r_t = Bifid-decode(FAED, square(K^r_t)), K^r_{t+1} = D^r_t[:r]
           ("full" = the whole decode, deduplicated).
  Objects  FAED (the cascade itself) and, under every distinct square, DBBI and
           the 91-letter VALIDATION_ANSWER.

Every decode is scored with Phase 544's rail-aware lexicon statistics (S1, S2),
generalised to any square and any even/odd block length, and calibrated by
exact-multiset shuffles. FAED cascade cells regenerate the whole cascade on each
shuffle (dynamic squares); other-object cells shuffle the object under the
fixed squares. One rank-max family correction over all cells and both statistics.

Modes: --self-test (controls, real cascade never scored), --prepare (lock),
--run (verify lock, score once).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import random
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase544_rail_feasible_lexicon_scan as p544  # noqa: E402
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import build_grid, bifid_decrypt  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-21 - Phase 545 Keyword Cascade and Tail-Derived Square Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase545_cascade_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase545_cascade_result.json"

RULES = (7, 13, "full")
DEPTH = 3
N_TRIALS = 10_000
NULL_SEED = 545_000
BAR_P = 0.01
BASE_KEYWORD = DBBI[:13]
FAED_U = FAED.upper()
DBBI_U = DBBI.upper()
VALANS_U = VALIDATION_ANSWER.upper()
P476_P91_SQUARE = "DEOMCKAHBSVXPRIQNGLUZFTWY"     # Phase 476: dedup of decoded[7:98]
IMPOSSIBLE_BITS = p544.IMPOSSIBLE_BITS


# --------------------------------------------------------------------------
# squares, decode, cascade
# --------------------------------------------------------------------------
def make_square(keyword):
    kw = "".join(c for c in keyword.upper().replace("J", "I") if c.isalpha())
    return build_grid(kw)          # (letters, grid, pos)


def decode_with(obj, grid, pos):
    return bifid_decrypt(obj, pos, grid)


def encrypt_with(plain, grid, pos):
    rows = [pos[c][0] for c in plain]
    cols = [pos[c][1] for c in plain]
    s = rows + cols
    return "".join(grid[(s[2 * k], s[2 * k + 1])] for k in range(len(plain)))


def keyword_from(decoded, rule):
    return decoded if rule == "full" else decoded[:rule]


def cascade(obj, rule, depth=DEPTH):
    """[(square_letters, decoded)] for t = 1..depth, starting from DBBI[:13]."""
    letters, grid, pos = make_square(BASE_KEYWORD)
    dec = decode_with(obj, grid, pos)
    out = []
    for _ in range(depth):
        letters, grid, pos = make_square(keyword_from(dec, rule))
        dec = decode_with(obj, grid, pos)
        out.append((letters, dec))
    return out


# --------------------------------------------------------------------------
# generalised rail-aware model
# --------------------------------------------------------------------------
def cost_tables(obj, grid, pos):
    """Bits per output letter for each position type (i % 2, (n + i) % 2).

    Output letter i is the cell (coords[i], coords[n + i]); coordinate j is the
    row of symbol j // 2 when j is even and its column when j is odd.
    """
    n = len(obj)
    prow, pcol = Counter(), Counter()
    for ch in obj:
        r, c = pos["I" if ch == "J" else ch]
        prow[r] += 1 / n
        pcol[c] += 1 / n
    tables = {}
    for a in (0, 1):
        for b in (0, 1):
            px = prow if a == 0 else pcol
            py = prow if b == 0 else pcol
            table = {}
            for (r, c), letter in grid.items():
                p = px.get(r, 0) * py.get(c, 0)
                if p > 0:
                    table[letter] = -math.log2(p)
            tables[(a, b)] = table
    return tables


def cumulative(tail, tables, n):
    cs = [0.0]
    for i, ch in enumerate(tail):
        cs.append(cs[-1] + tables[(i % 2, (n + i) % 2)].get(ch, IMPOSSIBLE_BITS))
    return cs


def cell_stats(obj, grid, pos, trie):
    tail = decode_with(obj, grid, pos)
    cs = cumulative(tail, cost_tables(obj, grid, pos), len(obj))
    occ = p544.occurrences(tail, trie, cs, start=0)
    s1 = max((s for _, _, s in occ), default=0.0)
    s2, _ = p544.best_cover(occ)
    return s1, s2, occ, tail


# --------------------------------------------------------------------------
# family layout
# --------------------------------------------------------------------------
def real_layout():
    """Cell list from the real cascade: FAED cells and the distinct squares."""
    cells, chains = [], {}
    squares = {}
    for rule in RULES:
        chain = cascade(FAED_U, rule)
        chains[str(rule)] = [sq for sq, _ in chain]
        for t, (sq, _) in enumerate(chain, start=1):
            cells.append(("faed", str(rule), t))
            squares.setdefault(sq, (str(rule), t))
    base = make_square(BASE_KEYWORD)[0]
    squares.pop(base, None)
    ordered = sorted(squares)
    cells += [("dbbi", sq, 0) for sq in ordered]
    cells += [("valans", sq, 0) for sq in ordered]
    return cells, chains, ordered


# --------------------------------------------------------------------------
# null
# --------------------------------------------------------------------------
_STATE = {}


def _init_worker(words, squares):
    _STATE["trie"] = p544.build_trie(words)
    # a 25-letter square string reproduces itself as a keyword
    _STATE["squares"] = [(sq, make_square(sq)[1], make_square(sq)[2]) for sq in squares]


def _trial(i):
    trie = _STATE["trie"]
    rng = random.Random(NULL_SEED + i)
    seq = list(FAED_U)
    rng.shuffle(seq)
    seq = "".join(seq)
    row = []
    for rule in RULES:
        for _, dec in _cascade_stats(seq, rule, trie):
            row.extend(dec)
    for name, obj in (("dbbi", DBBI_U), ("valans", VALANS_U)):
        r2 = random.Random(NULL_SEED + 7_000_000 + (1 if name == "valans" else 0) * 1_000_000 + i)
        seq2 = list(obj)
        r2.shuffle(seq2)
        seq2 = "".join(seq2)
        for sq, grid, pos in _STATE["squares"]:
            s1, s2, _, _ = cell_stats(seq2, grid, pos, trie)
            row.extend([s1, s2])
    return row


def _cascade_stats(seq, rule, trie):
    letters, grid, pos = make_square(BASE_KEYWORD)
    dec = decode_with(seq, grid, pos)
    out = []
    for _ in range(DEPTH):
        letters, grid, pos = make_square(keyword_from(dec, rule))
        s1, s2, _, dec = cell_stats(seq, grid, pos, trie)
        out.append((letters, [s1, s2]))
    return out


def null_pool(words, squares, n=N_TRIALS, workers=None):
    workers = workers or min(8, mp.cpu_count())
    with mp.Pool(workers, initializer=_init_worker, initargs=(words, squares)) as pool:
        return pool.map(_trial, range(n), chunksize=64)


def ordered_null_columns(cells):
    """Column order of _trial rows: FAED cells (rule-major, t = 1..3) then, per
    object, the distinct squares."""
    cols = [c for c in cells if c[0] == "faed"]
    cols += [c for c in cells if c[0] == "dbbi"]
    cols += [c for c in cells if c[0] == "valans"]
    return cols


def family_p(real_vec, pool):
    """Inclusive rank-max over every (cell, statistic) column."""
    n = len(pool)
    m = len(real_vec)
    cols = [[row[j] for row in pool] for j in range(m)]
    real_p = [(1 + sum(1 for x in cols[j] if x >= real_vec[j] - 1e-9)) / (n + 1) for j in range(m)]
    real_fam = min(real_p)
    # each null trial's own family value against the same null columns
    sorted_cols = [sorted(c) for c in cols]
    import bisect

    def ge(j, v):
        return n - bisect.bisect_left(sorted_cols[j], v - 1e-9)

    hits = 0
    for row in pool:
        fam = min(ge(j, row[j]) / n for j in range(m))
        if fam <= real_fam + 1e-12:
            hits += 1
    return real_p, real_fam, (1 + hits) / (n + 1)


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def control_construction():
    d0 = decode_with(FAED_U, *make_square(BASE_KEYWORD)[1:])
    p91 = d0[7:98]
    return {
        "d0_sha256_matches_phase425": hashlib.sha256(d0.encode()).hexdigest() == p544.DECODE_SHA256,
        "phase476_p91_square_reproduced": make_square(p91)[0] == P476_P91_SQUARE,
        "base_square_is_dbifh": make_square(BASE_KEYWORD)[0] == "DBIFHCEGAKLMNOPQRSTUVWXYZ",
        "rule7_keyword_is_btcseed": keyword_from(d0, 7) == "BTCSEED",
        "rule_full_square_is_25_distinct": len(set(make_square(keyword_from(d0, "full"))[0])) == 25,
    }


def control_roundtrip_and_model():
    rng = random.Random(NULL_SEED - 1)
    alpha = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    ok_rt = True
    for n in (570, 91, 90):
        for _ in range(5):
            kw = "".join(rng.choice(alpha) for _ in range(8))
            _, grid, pos = make_square(kw)
            plain = "".join(rng.choice(alpha) for _ in range(n))
            ok_rt &= decode_with(encrypt_with(plain, grid, pos), grid, pos) == plain
    # Phase 544's fixed even-rail model equals the generalised model on FAED
    _, grid, pos = make_square(BASE_KEYWORD)
    tables = cost_tables(FAED_U, grid, pos)
    same_as_544 = all(abs(tables[(0, 0)].get(c, 0) - p544.COST[0][c]) < 1e-9 for c in p544.COST[0]) \
        and all(abs(tables[(1, 1)].get(c, 0) - p544.COST[1][c]) < 1e-9 for c in p544.COST[1])
    tail = decode_with(FAED_U, grid, pos)
    cum_same = abs(cumulative(tail, tables, 570)[-1] - p544.cumulative_cost(tail)[-1]) < 1e-6
    # empirical check on an odd-length object under a non-base square
    _, g2, p2 = make_square("BTCSEED")
    tab = cost_tables(DBBI_U, g2, p2)
    n = len(DBBI_U)
    emp, tot = {}, Counter()
    seq = list(DBBI_U)
    trials = 6000
    for _ in range(trials):
        rng.shuffle(seq)
        t = decode_with("".join(seq), g2, p2)
        for i, ch in enumerate(t):
            typ = (i % 2, (n + i) % 2)
            emp.setdefault(typ, Counter())[ch] += 1
            tot[typ] += 1
    dev = 0.0
    for typ, counter in emp.items():
        for ch, cnt in counter.items():
            p = 2 ** -tab[typ][ch]
            dev = max(dev, abs(cnt / tot[typ] - p))
    sums_ok = all(abs(sum(2 ** -v for v in tab[t].values()) - 1) < 1e-9 for t in tab)
    return {
        "roundtrip_570_91_90": bool(ok_rt),
        "model_equals_phase544_on_faed": bool(same_as_544 and cum_same),
        "odd_length_model_within_0.02": dev < 0.02,
        "type_tables_sum_to_one": bool(sums_ok),
    }


def control_cascade_logic():
    a = cascade(FAED_U, 7)
    b = cascade(FAED_U, 7)
    d0 = decode_with(FAED_U, *make_square(BASE_KEYWORD)[1:])
    first_sq = make_square(d0[:7])[0]
    letters, grid, pos = make_square("ABCDE")
    return {
        "deterministic": a == b,
        "first_step_uses_d0_prefix": a[0][0] == first_sq,
        "depth": len(a) == DEPTH,
        "keyword_j_maps_to_i": make_square("JUMP")[0] == make_square("IUMP")[0],
    }


def plant_object(n, word, offset, seed, keyword="BTCSEED"):
    rng = random.Random(seed)
    alpha = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    plain = [rng.choice(alpha) for _ in range(n)]
    plain[offset:offset + len(word)] = list(word)
    _, grid, pos = make_square(keyword)
    return encrypt_with("".join(plain), grid, pos), "".join(plain)


def control_planted(words, trie, n_null=N_TRIALS):
    """Planted dictionary word in a synthetic object, decoded under its own square
    (must be recovered and reach the bar) and under a wrong square (must not)."""
    rows = {}
    ok = True
    by_len = {}
    for w in words:
        by_len.setdefault(len(w), w)
    for n, length, offset in ((570, 8, 200), (91, 10, 40)):
        word = by_len[length]
        obj, plain = plant_object(n, word, offset, seed=NULL_SEED + n)
        for label, kw in (("right_square", "BTCSEED"), ("wrong_square", BASE_KEYWORD)):
            _, grid, pos = make_square(kw)
            s1, s2, occ, tail = cell_stats(obj, grid, pos, trie)
            rng = random.Random(NULL_SEED + 50 + n)
            seq = list(obj)
            pool = []
            for _ in range(n_null):
                rng.shuffle(seq)
                a, b, _, _ = cell_stats("".join(seq), grid, pos, trie)
                pool.append([a, b])
            _, fam, corr = family_p([s1, s2], pool)
            found = any(o == offset and w == word for o, w, _ in occ)
            argmax = bool(occ) and max(occ, key=lambda x: x[2])[:2] == (offset, word)
            rows[f"n{n}/{label}"] = {"word": word, "offset": offset, "found": found,
                                     "argmax": argmax, "s1": round(s1, 2), "s2": round(s2, 2),
                                     "corrected_p": corr}
            if label == "right_square":
                ok &= found and argmax and corr <= BAR_P
            else:
                ok &= corr > BAR_P
    return {"ok": bool(ok), "rows": rows}


def null_summary(pool):
    flat = hashlib.sha256(json.dumps([[round(x, 6) for x in r] for r in pool]).encode()).hexdigest()
    m = len(pool[0])
    med = sorted(r[0] for r in pool)[len(pool) // 2]
    return {"trials": len(pool), "columns": m, "col0_median": round(med, 3), "pool_sha256": flat}


def self_test():
    words = p544.load_words()
    trie = p544.build_trie(words)
    checks = {
        "construction": control_construction(),
        "roundtrip_and_model": control_roundtrip_and_model(),
        "cascade_logic": control_cascade_logic(),
    }
    checks["planted"] = control_planted(words, trie)
    ok = (all(checks["construction"].values()) and all(checks["roundtrip_and_model"].values())
          and all(checks["cascade_logic"].values()) and checks["planted"]["ok"])
    return {"ok": bool(ok), "checks": checks}


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_fields():
    words = p544.load_words()
    return {
        "phase": 545,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(__file__),
        "test_sha256": sha256_file(SCRIPT_DIR / "test_phase545_keyword_cascade_tail_square.py"),
        "phase544_script_sha256": sha256_file(SCRIPT_DIR / "phase544_rail_feasible_lexicon_scan.py"),
        "phase386_script_sha256": sha256_file(SCRIPT_DIR / "phase386_btcseed_bifid_faed_decode_audit.py"),
        "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
        "dictionary_file_sha256": sha256_file(p544.DICT_PATH),
        "lexicon_list_sha256": hashlib.sha256("\n".join(words).encode()).hexdigest(),
        "rules": [str(r) for r in RULES],
        "depth": DEPTH,
        "n_trials": N_TRIALS,
        "null_seed": NULL_SEED,
        "bar_p": BAR_P,
        "objects": {"FAED": len(FAED_U), "DBBI": len(DBBI_U), "VALIDATION_ANSWER": len(VALANS_U)},
    }


def prepare():
    if LOCK_PATH.exists():
        raise SystemExit(f"{LOCK_PATH.name} exists; refusing to overwrite")
    st = self_test()
    if not st["ok"]:
        print(json.dumps(st, indent=2))
        raise SystemExit("controls failed; no lock written and no real cascade was scored")
    fields = expected_lock_fields()
    fields["controls"] = st["checks"]
    LOCK_PATH.write_text(json.dumps(fields, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"lock": str(LOCK_PATH), "planted": st["checks"]["planted"]["rows"]}


def verify_lock():
    if not LOCK_PATH.exists():
        raise SystemExit("no lock; run --prepare first")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    want = expected_lock_fields()
    bad = [k for k in want if lock.get(k) != want[k]]
    if bad:
        raise SystemExit(f"lock mismatch in: {bad}")
    if not lock["controls"]["planted"]["ok"]:
        raise SystemExit("locked planted recovery did not pass")
    return lock


def run():
    verify_lock()
    words = p544.load_words()
    trie = p544.build_trie(words)
    cells, chains, squares = real_layout()
    cols = ordered_null_columns(cells)
    # real vector in the same column order as _trial
    real_vec, detail = [], []
    for cell in cols:
        kind, key, t = cell
        if kind == "faed":
            letters, dec = cascade(FAED_U, int(key) if key != "full" else "full")[t - 1]
            grid, pos = make_square_from_letters(letters)
            s1, s2, occ, tail = cell_stats(FAED_U, grid, pos, trie)
        else:
            grid, pos = make_square_from_letters(key)
            obj = DBBI_U if kind == "dbbi" else VALANS_U
            s1, s2, occ, tail = cell_stats(obj, grid, pos, trie)
        real_vec.extend([s1, s2])
        top = sorted(occ, key=lambda x: -x[2])[:3]
        detail.append({"cell": list(cell), "s1": round(s1, 3), "s2": round(s2, 3),
                       "occurrences": len(occ),
                       "top": [{"offset": o, "word": w, "bits": round(s, 3)} for o, w, s in top]})
    pool = null_pool(words, squares)
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    summ = null_summary(pool)
    real_p, real_fam, corrected = family_p(real_vec, pool)
    for i, d in enumerate(detail):
        d["s1_p"], d["s2_p"] = real_p[2 * i], real_p[2 * i + 1]
    fixed = {}
    for rule, chain in chains.items():
        fixed[rule] = {"squares": chain,
                       "fixed_point": len(set(chain)) < len(chain) or chain[0] == make_square(BASE_KEYWORD)[0]}
    out = {
        "phase": 545,
        "lock_sha256": sha256_file(LOCK_PATH),
        "cells": len(cols),
        "statistic_columns": len(real_vec),
        "distinct_new_squares": len(squares),
        "chains": fixed,
        "null": summ,
        "family_min_p": real_fam,
        "family_corrected_p": corrected,
        "bar_p": BAR_P,
        "outcome": ("cascade_signal_positive_checkpoint_only" if corrected <= BAR_P else "null_like"),
        "cell_detail": detail,
        "oracle_calls": 0,
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def make_square_from_letters(letters):
    grid, pos = {}, {}
    for i, ch in enumerate(letters):
        r, c = divmod(i, 5)
        grid[(r, c)] = ch
        pos[ch] = (r, c)
    return grid, pos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        r = self_test()
        print(json.dumps(r, indent=2))
        return 0 if r["ok"] else 1
    if args.prepare:
        print(json.dumps(prepare(), indent=2))
        return 0
    if args.run:
        out = run()
        print(json.dumps({k: v for k, v in out.items() if k != "cell_detail"}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
