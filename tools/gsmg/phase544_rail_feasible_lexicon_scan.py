#!/usr/bin/env python3
"""Phase 544 -- rail-feasible lexicon scan of the BTCSEED Bifid decode.

Protocol: doc/Brainstorms/2026-09-21 - Phase 544 Rail-Feasible Lexicon Scan
Protocol.md (written before the real tail was scored).

Modes
  --self-test   controls (decode reproduction, rail feasibility, probability
                model, planted-word recovery against the frozen null). Never
                scores the real tail.
  --prepare     runs the controls and writes the execution lock.
  --run         verifies the whole lock, then scores the real tail once.

The decode is the community configuration only: DBBI-first-13 keyed square,
one 570-symbol block, row-column reading, forward. Output letters 2k and 2k+1
depend only on FAED[k] and FAED[285+k]; even positions can only be B/C/D/E.
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
from data import DBBI, FAED  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import build_grid, bifid_decrypt  # noqa: E402
from phase396_p91_header_aware_block_audit import TARGET_KEYWORDS  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-21 - Phase 544 Rail-Feasible Lexicon Scan Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase544_rail_lexicon_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase544_rail_lexicon_result.json"
DICT_PATH = Path("/usr/share/dict/words").resolve()

N_FAED = len(FAED)
HALF = N_FAED // 2
PREFIX_LEN = 7                      # BTCSEED; occurrences must start at >= 7
MIN_WORD = 5
MAX_WORD = 20
N_TRIALS = 10_000
NULL_SEED = 544_000
DECODE_SHA256 = "0c5d984f90e9baefc09f1d3888e62acbd101f9b0194887e2ae88fc6c9967745e"
BAR_P = 0.01
PLANT_GATE_LENGTHS = (8,)
PLANT_REPORT_LENGTHS = (6, 8, 10)
PLANT_OFFSETS = {"even": 200, "odd": 301}
L2_WORDS = tuple(w for w in TARGET_KEYWORDS if w != "BTCSEED")

SQUARE, GRID, POS = build_grid(DBBI[:13])
SYMS = sorted(set(FAED.upper()))
ROW = {s: POS[s][0] for s in SYMS}
COL = {s: POS[s][1] for s in SYMS}
CELL_TO_SYM = {POS[s]: s for s in SYMS}
FAED_U = FAED.upper()


# --------------------------------------------------------------------------
# decode and probability model
# --------------------------------------------------------------------------
def decode(stream):
    """Whole-block Bifid decode of a 570-symbol string (uppercase A..I)."""
    return bifid_decrypt(stream, POS, GRID)


def model():
    """Mechanical-null letter probabilities per output parity.

    Even output letter = cell (row of FAED[k], row of FAED[285+k]); odd output
    letter = cell (col of FAED[k], col of FAED[285+k]). Independent draws from
    FAED's own row and column marginals (the halves are independent; see the
    protocol). Fixed by the exact FAED multiset, so identical for the real tail
    and every shuffle.
    """
    n = len(FAED_U)
    prow, pcol = Counter(), Counter()
    for ch in FAED_U:
        prow[ROW[ch]] += 1 / n
        pcol[COL[ch]] += 1 / n
    even, odd = {}, {}
    for r1, p1 in prow.items():
        for r2, p2 in prow.items():
            even[GRID[(r1, r2)]] = even.get(GRID[(r1, r2)], 0) + p1 * p2
    for c1, p1 in pcol.items():
        for c2, p2 in pcol.items():
            odd[GRID[(c1, c2)]] = odd.get(GRID[(c1, c2)], 0) + p1 * p2
    return even, odd


P_EVEN, P_ODD = model()
COST = (
    {ch: -math.log2(p) for ch, p in P_EVEN.items()},
    {ch: -math.log2(p) for ch, p in P_ODD.items()},
)


IMPOSSIBLE_BITS = 100.0   # letter outside the rail's alphabet (never occurs in a real decode)


def cumulative_cost(tail):
    cs = [0.0]
    for q, ch in enumerate(tail):
        cs.append(cs[-1] + COST[q % 2].get(ch, IMPOSSIBLE_BITS))
    return cs


# --------------------------------------------------------------------------
# lexicon and scan
# --------------------------------------------------------------------------
def load_words(path=DICT_PATH):
    words = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            w = line.strip()
            if w.isascii() and w.isalpha() and MIN_WORD <= len(w) <= MAX_WORD:
                u = w.upper()
                if "J" not in u:
                    words.add(u)
    return sorted(words)


def build_trie(words):
    root = {}
    for w in words:
        node = root
        for ch in w:
            node = node.setdefault(ch, {})
        node["$"] = w
    return root


def occurrences(tail, trie, cs=None, start=PREFIX_LEN):
    """All (offset, word, surprisal_bits) with offset >= start."""
    if cs is None:
        cs = cumulative_cost(tail)
    out = []
    n = len(tail)
    for o in range(start, n - MIN_WORD + 1):
        node = trie
        j = o
        while j < n:
            node = node.get(tail[j])
            if node is None:
                break
            j += 1
            w = node.get("$")
            if w is not None:
                out.append((o, w, cs[j] - cs[o]))
    return out


def best_cover(occ):
    """Maximum total surprisal over non-overlapping occurrences."""
    if not occ:
        return 0.0, []
    items = sorted(((o, o + len(w), s, w) for o, w, s in occ), key=lambda x: x[1])
    ends = [it[1] for it in items]
    import bisect
    best = [0.0] * (len(items) + 1)
    take = [None] * (len(items) + 1)
    for i, (a, b, s, w) in enumerate(items, start=1):
        j = bisect.bisect_right(ends, a, 0, i - 1)
        with_it = best[j] + s
        if with_it > best[i - 1]:
            best[i], take[i] = with_it, (j, i - 1)
        else:
            best[i], take[i] = best[i - 1], None
    chosen, i = [], len(items)
    while i > 0:
        if take[i] is None:
            i -= 1
        else:
            j, idx = take[i]
            chosen.append((items[idx][0], items[idx][3], round(items[idx][2], 3)))
            i = j
    return best[-1], sorted(chosen)


def stats(tail, trie):
    occ = occurrences(tail, trie)
    s1 = max((s for _, _, s in occ), default=0.0)
    s2, _ = best_cover(occ)
    return s1, s2, occ


def l2_count(tail, words=L2_WORDS, start=PREFIX_LEN):
    return sum(1 for w in words if tail.find(w, start) != -1)


# --------------------------------------------------------------------------
# null
# --------------------------------------------------------------------------
_TRIE = None
_SYMS_LIST = list(FAED_U)


def _init_worker(words):
    global _TRIE
    _TRIE = build_trie(words)


def _trial(i):
    rng = random.Random(NULL_SEED + i)
    seq = _SYMS_LIST[:]
    rng.shuffle(seq)
    tail = decode("".join(seq))
    s1, s2, _ = stats(tail, _TRIE)
    return s1, s2, l2_count(tail)


def null_pool(words, n=N_TRIALS, workers=None):
    workers = workers or min(8, mp.cpu_count())
    with mp.Pool(workers, initializer=_init_worker, initargs=(words,)) as pool:
        rows = pool.map(_trial, range(n), chunksize=64)
    return rows


def upper_p(value, sample):
    return (1 + sum(1 for x in sample if x >= value - 1e-9)) / (len(sample) + 1)


def family_p(real, pool):
    """Inclusive rank-max correction over (S1, S2), as in Phases 426-428."""
    n = len(pool)
    cols = [[r[k] for r in pool] for k in (0, 1)]

    def fam(vals):
        return min((sum(1 for x in cols[k] if x >= vals[k] - 1e-9)) / n for k in (0, 1))

    real_fam = min((1 + sum(1 for x in cols[k] if x >= real[k] - 1e-9)) / (n + 1) for k in (0, 1))
    hits = sum(1 for r in pool if fam(r) <= real_fam + 1e-12)
    return real_fam, (1 + hits) / (n + 1)


# --------------------------------------------------------------------------
# planting (controls only)
# --------------------------------------------------------------------------
def plant(stream, offset, word):
    """Return stream' whose decode has `word` at `offset`, or None if the
    required (row, col) cells are not FAED symbols."""
    syms = list(stream)
    need_row, need_col = {}, {}
    for j, ch in enumerate(word):
        i = offset + j
        r, c = POS[ch]
        k = i // 2
        if i % 2 == 0:
            need_row[k], need_row[HALF + k] = r, c
        else:
            need_col[k], need_col[HALF + k] = r, c
    for s in set(need_row) | set(need_col):
        r = need_row.get(s, ROW[syms[s]])
        c = need_col.get(s, COL[syms[s]])
        sym = CELL_TO_SYM.get((r, c))
        if sym is None:
            return None
        syms[s] = sym
    out = "".join(syms)
    return out if decode(out)[offset:offset + len(word)] == word else None


def pick_plants(words):
    """Deterministic: first dictionary word (sorted) per (alignment, length)
    that can be planted."""
    plants = {}
    for align, off in PLANT_OFFSETS.items():
        for length in PLANT_REPORT_LENGTHS:
            for w in words:
                if len(w) != length:
                    continue
                if plant(FAED_U, off, w) is not None:
                    plants[f"{align}/{length}"] = {"offset": off, "word": w}
                    break
    return plants


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def control_decode():
    d = decode(FAED_U)
    rng = random.Random(NULL_SEED - 1)
    seq = list(FAED_U)
    rails_ok = True
    for _ in range(200):
        rng.shuffle(seq)
        t = decode("".join(seq))
        rails_ok &= set(t[0::2]) <= set("BCDE")
    return {
        "sha256_matches_phase425": hashlib.sha256(d.encode()).hexdigest() == DECODE_SHA256,
        "prefix_is_BTCSEED": d.startswith("BTCSEED"),
        "even_rail_only_BCDE_real": set(d[0::2]) == set("BCDE"),
        "even_rail_only_BCDE_200_shuffles": bool(rails_ok),
        "length_570": len(d) == 570,
    }


def control_model():
    rng = random.Random(NULL_SEED - 2)
    seq = list(FAED_U)
    ev, od = Counter(), Counter()
    trials = 4000
    for _ in range(trials):
        rng.shuffle(seq)
        t = decode("".join(seq))
        ev.update(t[0::2])
        od.update(t[1::2])
    dev_e = max(abs(ev[ch] / (trials * HALF) - p) for ch, p in P_EVEN.items())
    dev_o = max(abs(od[ch] / (trials * HALF) - p) for ch, p in P_ODD.items())
    direct = sum(COST[q % 2][ch] for q, ch in enumerate("BTCSEED"))
    return {
        "p_even_sums_to_one": abs(sum(P_EVEN.values()) - 1) < 1e-12,
        "p_odd_sums_to_one": abs(sum(P_ODD.values()) - 1) < 1e-12,
        "even_marginal_max_dev_under_0.01": dev_e < 0.01,
        "odd_marginal_max_dev_under_0.01": dev_o < 0.01,
        "surprisal_prefix_matches_direct": abs(
            cumulative_cost("BTCSEED")[-1] - direct) < 1e-9,
    }


def control_scan_and_cover():
    trie = build_trie(["SEEDS", "DECODED", "CODED"])
    tail = "XXXXXXXXDECODEDAXX"
    occ = occurrences(tail, trie, start=7)
    words = sorted(w for _, w, _ in occ)
    total, chosen = best_cover(occ)
    return {
        "finds_expected_words": words == ["CODED", "DECODED"],
        "cover_picks_higher_surprisal": [w for _, w, _ in chosen] == ["DECODED"],
        "cover_total_equals_chosen_sum": abs(total - sum(s for *_, s in chosen)) < 1e-2,
        "prefix_excluded": all(o >= 7 for o, _, _ in occ),
    }


def control_planted(words, pool):
    plants = pick_plants(words)
    trie = build_trie(words)
    rows = {}
    ok = True
    s1_pool = [r[0] for r in pool]
    s2_pool = [r[1] for r in pool]
    for key, info in sorted(plants.items()):
        stream = plant(FAED_U, info["offset"], info["word"])
        tail = decode(stream)
        s1, s2, occ = stats(tail, trie)
        found = any(o == info["offset"] and w == info["word"] for o, w, _ in occ)
        best = max(occ, key=lambda x: x[2]) if occ else None
        argmax_ok = bool(best and best[0] == info["offset"] and best[1] == info["word"])
        fam, corrected = family_p((s1, s2), pool)
        rows[key] = {
            "offset": info["offset"], "word": info["word"], "found": found,
            "argmax_is_plant": argmax_ok, "s1_bits": round(s1, 3), "s2_bits": round(s2, 3),
            "s1_p": upper_p(s1, s1_pool), "s2_p": upper_p(s2, s2_pool),
            "family_p": corrected,
        }
        length = int(key.split("/")[1])
        if length in PLANT_GATE_LENGTHS:
            ok &= found and argmax_ok and corrected <= BAR_P
    gate_keys_present = all(f"{a}/{l}" in rows for a in PLANT_OFFSETS for l in PLANT_GATE_LENGTHS)
    return {"ok": bool(ok and gate_keys_present), "rows": rows}


def null_summary(pool):
    s1 = sorted(r[0] for r in pool)
    s2 = sorted(r[1] for r in pool)
    q = lambda a, f: round(a[int(f * (len(a) - 1))], 3)
    return {
        "trials": len(pool),
        "s1_quantiles": {f"q{int(f * 100)}": q(s1, f) for f in (0.5, 0.9, 0.99)},
        "s2_quantiles": {f"q{int(f * 100)}": q(s2, f) for f in (0.5, 0.9, 0.99)},
        "l2_mean": round(sum(r[2] for r in pool) / len(pool), 4),
        "pool_sha256": hashlib.sha256(
            json.dumps([[round(a, 6), round(b, 6), c] for a, b, c in pool]).encode()).hexdigest(),
    }


def self_test():
    words = load_words()
    checks = {
        "control_decode": control_decode(),
        "control_model": control_model(),
        "control_scan_and_cover": control_scan_and_cover(),
    }
    pool = null_pool(words)
    checks["null"] = null_summary(pool)
    checks["control_planted"] = control_planted(words, pool)
    ok = (all(checks["control_decode"].values()) and all(checks["control_model"].values())
          and all(checks["control_scan_and_cover"].values()) and checks["control_planted"]["ok"])
    return {"ok": bool(ok), "checks": checks, "words": len(words)}


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_fields(words=None):
    words = words or load_words()
    return {
        "phase": 544,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(__file__),
        "test_sha256": sha256_file(SCRIPT_DIR / "test_phase544_rail_feasible_lexicon_scan.py"),
        "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
        "phase386_script_sha256": sha256_file(SCRIPT_DIR / "phase386_btcseed_bifid_faed_decode_audit.py"),
        "phase396_script_sha256": sha256_file(SCRIPT_DIR / "phase396_p91_header_aware_block_audit.py"),
        "dictionary_path": str(DICT_PATH),
        "dictionary_file_sha256": sha256_file(DICT_PATH),
        "lexicon_words": len(words),
        "lexicon_list_sha256": hashlib.sha256("\n".join(words).encode()).hexdigest(),
        "square": SQUARE,
        "faed_sha256": hashlib.sha256(FAED_U.encode()).hexdigest(),
        "l2_words": list(L2_WORDS),
        "n_trials": N_TRIALS,
        "null_seed": NULL_SEED,
        "bar_p": BAR_P,
    }


def prepare():
    if LOCK_PATH.exists():
        raise SystemExit(f"{LOCK_PATH.name} exists; refusing to overwrite")
    st = self_test()
    if not st["ok"]:
        print(json.dumps(st, indent=2))
        raise SystemExit("controls failed; no lock written and the real tail was not scored")
    fields = expected_lock_fields()
    fields["controls"] = st["checks"]
    LOCK_PATH.write_text(json.dumps(fields, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"lock": str(LOCK_PATH), "null": st["checks"]["null"],
            "planted": st["checks"]["control_planted"]["rows"]}


def verify_lock(pool):
    if not LOCK_PATH.exists():
        raise SystemExit("no lock; run --prepare first")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    want = expected_lock_fields()
    bad = [k for k in want if lock.get(k) != want[k]]
    if bad:
        raise SystemExit(f"lock mismatch in: {bad}")
    if null_summary(pool) != lock["controls"]["null"]:
        raise SystemExit("recomputed null pool differs from the locked null")
    if not lock["controls"]["control_planted"]["ok"]:
        raise SystemExit("locked planted recovery did not pass")
    return lock


def run():
    words = load_words()
    pool = null_pool(words)
    verify_lock(pool)
    trie = build_trie(words)
    tail = decode(FAED_U)
    assert hashlib.sha256(tail.encode()).hexdigest() == DECODE_SHA256
    s1, s2, occ = stats(tail, trie)
    _, cover = best_cover(occ)
    real_fam, corrected = family_p((s1, s2), pool)
    l2 = l2_count(tail)
    l2_hits = [w for w in L2_WORDS if tail.find(w, PREFIX_LEN) != -1]
    top = sorted(occ, key=lambda x: -x[2])[:10]
    out = {
        "phase": 544,
        "lock_sha256": sha256_file(LOCK_PATH),
        "occurrences_len_ge_5": len(occ),
        "s1_bits": round(s1, 3),
        "s2_bits": round(s2, 3),
        "s1_p": upper_p(s1, [r[0] for r in pool]),
        "s2_p": upper_p(s2, [r[1] for r in pool]),
        "family_min_p": real_fam,
        "family_corrected_p": corrected,
        "bar_p": BAR_P,
        "outcome": ("embedded_word_signal_positive_checkpoint_only" if corrected <= BAR_P
                    else "null_like"),
        "top_occurrences": [{"offset": o, "word": w, "bits": round(s, 3)} for o, w, s in top],
        "best_cover": [{"offset": o, "word": w, "bits": s} for o, w, s in cover],
        "l2_arm": {"count": l2, "words_present": l2_hits,
                   "p": upper_p(l2, [r[2] for r in pool])},
        "oracle_calls": 0,
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


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
        print(json.dumps(run(), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
