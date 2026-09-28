#!/usr/bin/env python3
"""Phase 547 -- nine-symbol origin census.

Protocol: doc/Brainstorms/2026-09-24 - Phase 547 Nine-Symbol Origin Census Protocol.md
(written before the M1/M2 real statistics were computed).

Members (all over DBBI and FAED, symbols a..i):

  M1  keyed Trifid coordinates: every bijection a..i -> (hi, lo) trit pair (9!),
      trits regrouped in threes at offsets 0/1/2; statistic = 27-cell index of
      coincidence (invariant to the unknown cube). FAED gated, DBBI reported.
  M2  phone multi-tap: one symbol is X (pause C1 / space C2), the other eight
      are keys 2..9 (9 x 8! maps); each key run is one letter; statistic =
      normalized quadgram score of the decode, max over valid maps. Gated.
  M3  Morbit (9! pair maps) and M4 Pollux (3^9 maps): exact Morse validity.

Modes: --self-test (controls only), --prepare (controls + lock), --run.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import multiprocessing as mp
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI, FAED  # noqa: E402
from phase3_chain_full_text_p32_sweep_audit import PHASE32_ARCHITECT_SPEECH_LINES  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-24 - Phase 547 Nine-Symbol Origin Census Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase547_census_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase547_census_result.json"
QUAD_PATH = SCRIPT_DIR / "data_files" / "english_quadgrams.txt"
TEXT_SOURCE = SCRIPT_DIR / "phase3_chain_full_text_p32_sweep_audit.py"
TEST_PATH = SCRIPT_DIR / "test_phase547_nine_symbol_origin_census.py"

SYMS = "abcdefghi"
M1_SEED, M1_NULLS = 547, 1000
M2_SEED, M2_NULLS = 5471, 500
CONTROL_SEED = 54700
BAR = 0.01
WORKERS = min(16, mp.cpu_count())

ALL9 = np.array(list(itertools.permutations(range(9))), dtype=np.int8)  # (362880, 9)
KEY8 = np.array(list(itertools.permutations(range(8))), dtype=np.int8)  # (40320, 8)

ARCH_TEXT = " ".join(PHASE32_ARCHITECT_SPEECH_LINES).upper()
ARCH_WORDS = ["".join(c for c in w if c.isalpha()) for w in ARCH_TEXT.split()]
ARCH_WORDS = [w for w in ARCH_WORDS if w]
ARCH_LETTERS = "".join(ARCH_WORDS)


def to_idx(s):
    return np.array([SYMS.index(c) for c in s], dtype=np.int8)


# --------------------------------------------------------------------------
# M1 keyed Trifid coordinates
# --------------------------------------------------------------------------
def m1_terms(s, offset):
    """Group the triples of stream s (symbol indices) at a trit offset into
    (pattern, symbol tuple) -> count. pattern = ((relative symbol, part), ...)."""
    n_trits = 2 * len(s)
    terms = Counter()
    j = 0
    while offset + 3 * j + 2 < n_trits:
        ps = [offset + 3 * j + i for i in range(3)]
        k0 = ps[0] // 2
        ks = sorted({p // 2 for p in ps})
        pattern = tuple((p // 2 - k0, p % 2) for p in ps)
        terms[(pattern, tuple(int(s[k]) for k in ks))] += 1
        j += 1
    return terms, j


def m1_ioc_all(s, offset, maps=ALL9):
    """IoC27 for every map (rows of maps: symbol -> pair value 0..8)."""
    terms, n = m1_terms(s, offset)
    hi, lo = maps // 3, maps % 3
    hist = np.zeros((maps.shape[0], 27), dtype=np.int32)
    rows = np.arange(maps.shape[0])
    for (pattern, symtuple), w in terms.items():
        code = np.zeros(maps.shape[0], dtype=np.int32)
        for i, (rel, part) in enumerate(pattern):
            sym = symtuple[rel]
            trit = hi[:, sym] if part == 0 else lo[:, sym]
            code += trit.astype(np.int32) * (3 ** (2 - i))
        hist[rows, code] += w
    hist = hist.astype(np.float64)
    return (hist * (hist - 1)).sum(axis=1) / (n * (n - 1)), n


def m1_family(s):
    best = (-1.0, None, None)
    for off in range(3):
        ioc, _ = m1_ioc_all(s, off)
        m = int(np.argmax(ioc))
        if ioc[m] > best[0]:
            best = (float(ioc[m]), m, off)
    return best


def m1_direct(s, mapping, offset):
    trits = []
    for c in s:
        v = int(mapping[c])
        trits += [v // 3, v % 3]
    trits = trits[offset:]
    codes = [trits[i] * 9 + trits[i + 1] * 3 + trits[i + 2] for i in range(0, len(trits) - 2, 3)]
    n = len(codes)
    return sum(v * (v - 1) for v in Counter(codes).values()) / (n * (n - 1))


# --------------------------------------------------------------------------
# M2 phone multi-tap
# --------------------------------------------------------------------------
KEY_LETTERS = ["ABC", "DEF", "GHI", "JKL", "MNO", "PQRS", "TUV", "WXYZ"]
CAPS = np.array([len(k) for k in KEY_LETTERS], dtype=np.int8)
LUT = np.full((8, 5), -1, dtype=np.int16)
for _k, _letters in enumerate(KEY_LETTERS):
    for _t, _ch in enumerate(_letters):
        LUT[_k, _t + 1] = ord(_ch) - 65


def load_quad():
    counts = {}
    total = 0
    for line in QUAD_PATH.read_text().split("\n"):
        line = line.strip()
        if line:
            q, c = line.split()
            counts[q] = int(c)
            total += int(c)
    floor = math.log10(0.01 / total)
    arr = np.full(26 ** 4, floor, dtype=np.float32)
    for q, c in counts.items():
        arr[((ord(q[0]) - 65) * 26 + ord(q[1]) - 65) * 676 + (ord(q[2]) - 65) * 26 + ord(q[3]) - 65] = math.log10(c / total)
    return arr


QUAD = load_quad()


def runs_of(s):
    out = []
    for k, g in itertools.groupby(s.tolist()):
        out.append((k, len(list(g))))
    return out


def c1_ok(runs, x):
    """Pause convention: X runs have length 1, are interior, same key symbol both sides."""
    for i, (sym, ln) in enumerate(runs):
        if sym != x:
            continue
        if ln != 1 or i == 0 or i == len(runs) - 1 or runs[i - 1][0] != runs[i + 1][0]:
            return False
    return True


def m2_scores_for_x(s, x, chunk=10080):
    """Scores (normalized quadgram) for all 8! key maps with symbol x as X.
    Returns (scores with -inf for invalid, c1_structurally_ok, others list)."""
    runs = runs_of(s)
    others = [v for v in range(9) if v != x]
    pos = {v: i for i, v in enumerate(others)}
    kruns = [(pos[sym], ln) for sym, ln in runs if sym != x]
    rsym = np.array([r[0] for r in kruns], dtype=np.int64)
    rlen = np.array([r[1] for r in kruns], dtype=np.int64)
    maxrun = np.zeros(8, dtype=np.int64)
    for sym, ln in kruns:
        maxrun[sym] = max(maxrun[sym], ln)
    out = np.full(KEY8.shape[0], -np.inf)
    nlet = len(kruns)
    if nlet < 4 or rlen.max() > 4:
        return out, c1_ok(runs, x), others
    for a in range(0, KEY8.shape[0], chunk):
        km = KEY8[a:a + chunk].astype(np.int64)          # (m, 8): other-symbol -> key
        valid = np.all(CAPS[km] >= maxrun[None, :], axis=1)
        keys = km[:, rsym]                                 # (m, R)
        let = LUT[keys, rlen[None, :]].astype(np.int64)   # (m, R)
        let = np.where(let < 0, 0, let)
        q = ((let[:, :-3] * 26 + let[:, 1:-2]) * 26 + let[:, 2:-1]) * 26 + let[:, 3:]
        sc = QUAD[q].sum(axis=1) / (nlet - 3)
        out[a:a + chunk] = np.where(valid, sc, -np.inf)
    return out, c1_ok(runs, x), others


def m2_family(s):
    best = {"C1": (-math.inf, None), "C2": (-math.inf, None)}
    for x in range(9):
        sc, c1, _ = m2_scores_for_x(s, x)
        m = int(np.argmax(sc))
        if sc[m] > best["C2"][0]:
            best["C2"] = (float(sc[m]), (x, m))
        if c1 and sc[m] > best["C1"][0]:
            best["C1"] = (float(sc[m]), (x, m))
    stat = max(best["C1"][0], best["C2"][0])
    return stat, best


def m2_decode_direct(s, x, keymap_row):
    """Direct per-map decode: keymap_row maps others-index -> key index."""
    others = [v for v in range(9) if v != x]
    pos = {v: i for i, v in enumerate(others)}
    letters = []
    for sym, ln in runs_of(s):
        if sym == x:
            continue
        k = int(keymap_row[pos[sym]])
        if ln > len(KEY_LETTERS[k]):
            return None
        letters.append(KEY_LETTERS[k][ln - 1])
    return "".join(letters)


def quad_norm(text):
    q = [((ord(text[i]) - 65) * 26 + ord(text[i + 1]) - 65) * 676 + (ord(text[i + 2]) - 65) * 26 + ord(text[i + 3]) - 65
         for i in range(len(text) - 3)]
    return float(QUAD[q].sum() / (len(text) - 3))


# --------------------------------------------------------------------------
# M3 Morbit / M4 Pollux
# --------------------------------------------------------------------------
MORSE = {'.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F', '--.': 'G', '....': 'H',
         '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P',
         '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
         '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
         '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9', '.-.-.-': '.', '--..--': ',',
         '..--..': '?', '-..-.': '/', '-....-': '-', '-...-': '=', '.-.-.': '+', '---...': ':', '.----.': "'"}
MORSE_INV = {v: k for k, v in MORSE.items()}
PREF = {k[:i] for k in MORSE for i in range(1, len(k) + 1)}
PAIRS = ['..', '.-', '.x', '-.', '--', '-x', 'x.', 'x-', 'xx']


def morse_valid(stream):
    out, cur, xs = [], '', 0
    for c in stream:
        if c == 'x':
            if cur:
                if cur not in MORSE:
                    return None
                out.append(MORSE[cur])
                cur, xs = '', 1
            else:
                xs += 1
                if xs >= 3:
                    return None
                if xs == 2:
                    out.append(' ')
        else:
            cur += c
            if cur not in PREF:
                return None
    if cur:
        if cur not in MORSE:
            return None
        out.append(MORSE[cur])
    return ''.join(out)


def morbit_valid_maps(s):
    hits = []
    for perm in itertools.permutations(PAIRS):
        m = dict(zip(SYMS, perm))
        r = morse_valid(''.join(m[c] for c in s))
        if r is not None:
            hits.append((perm, r))
    return hits


def pollux_valid_maps(s):
    hits = []
    for assign in itertools.product('.-x', repeat=9):
        if len(set(assign)) < 3:
            continue
        m = dict(zip(SYMS, assign))
        r = morse_valid(''.join(m[c] for c in s))
        if r is not None:
            hits.append((assign, r))
    return hits


def morse_encode(letters):
    ms = 'x'.join(MORSE_INV[c] for c in letters) + 'x'
    if len(ms) % 2:
        ms += 'x'
    return ms


# --------------------------------------------------------------------------
# nulls (parallel)
# --------------------------------------------------------------------------
def _m1_null_worker(args):
    s, seed = args
    rng = np.random.default_rng(seed)
    t = s.copy()
    rng.shuffle(t)
    return m1_family(t)[0]


def _m2_null_worker(args):
    s, seed = args
    rng = np.random.default_rng(seed)
    t = s.copy()
    rng.shuffle(t)
    return m2_family(t)[0]


def null_dist(worker, s, n, seed):
    seeds = np.random.SeedSequence(seed).generate_state(n).tolist()
    with mp.get_context("fork").Pool(WORKERS) as pool:
        return pool.map(worker, [(s, sd) for sd in seeds], chunksize=1)


def pval(real, nulls):
    return (1 + sum(v >= real for v in nulls)) / (1 + len(nulls))


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def plant_m1(start, rng):
    letters = ARCH_LETTERS[start:start + 380]
    assert len(letters) == 380
    cube = rng.permutation(27)
    trits = []
    for c in letters:
        cell = int(cube[ord(c) - 65])
        trits += [cell // 9, (cell // 3) % 3, cell % 3]
    symmap = rng.permutation(9)             # symbol index -> pair value
    inv = {int(v): k for k, v in enumerate(symmap)}
    s = np.array([inv[trits[i] * 3 + trits[i + 1]] for i in range(0, len(trits), 2)], dtype=np.int8)
    return s, symmap


def control_m1_planted(n_null=200):
    rng = np.random.default_rng(CONTROL_SEED)
    out = []
    for start in (0, 100, 200, 300, 400):
        s, symmap = plant_m1(start, rng)
        mapping = {SYMS[k]: int(symmap[k]) for k in range(9)}
        true_ioc = m1_direct("".join(SYMS[v] for v in s), mapping, 0)
        fam = m1_family(s)
        nulls = null_dist(_m1_null_worker, s, n_null, CONTROL_SEED + start)
        p99 = float(np.quantile(nulls, 0.99))
        out.append({"start": start, "true_ioc": true_ioc, "family_max": fam[0],
                    "null_p99": p99, "true_reaches_max": abs(true_ioc - fam[0]) < 1e-12,
                    "exceeds_p99": fam[0] > p99})
    return out


def plant_m2(conv, rng):
    key_of = {ch: k for k, letters in enumerate(KEY_LETTERS) for ch in letters}
    x = int(rng.integers(9))
    others = [v for v in range(9) if v != x]
    km = rng.permutation(8)                 # others-index -> key
    sym_of_key = {int(km[i]): others[i] for i in range(8)}
    seq, prev_key = [], None
    for w in ARCH_WORDS:
        if conv == "C2" and seq:
            seq.append(x)
            prev_key = None
        for ch in w:
            k = key_of[ch]
            if prev_key == k:
                seq.append(x)
            seq += [sym_of_key[k]] * (KEY_LETTERS[k].index(ch) + 1)
            prev_key = k
    seq = seq[:570]
    while seq and seq[-1] == x:
        seq.pop()
    s = np.array(seq, dtype=np.int8)
    row = int(np.flatnonzero(np.all(KEY8 == km.astype(np.int8), axis=1))[0])
    return s, x, row


def control_m2_planted(n_null=100):
    rng = np.random.default_rng(CONTROL_SEED + 2)
    out = []
    for conv in ("C1", "C2"):
        s, x, row = plant_m2(conv, rng)
        sc, c1, _ = m2_scores_for_x(s, x)
        stat, best = m2_family(s)
        nulls = null_dist(_m2_null_worker, s, n_null, CONTROL_SEED + 3 + len(conv))
        out.append({"convention": conv, "true_valid": bool(np.isfinite(sc[row])), "true_score": float(sc[row]),
                    "c1_structure_ok": c1, "family_max": stat, "null_max": float(max(nulls)),
                    "true_reaches_max": abs(float(sc[row]) - stat) < 1e-6,
                    "exceeds_all_nulls": stat > max(nulls)})
    return out


def control_morse_planted():
    rng = np.random.default_rng(CONTROL_SEED + 4)
    ms = morse_encode(ARCH_LETTERS[:120])
    perm = list(PAIRS)
    rng.shuffle(perm)
    enc = "".join(SYMS[perm.index(ms[i:i + 2])] for i in range(0, len(ms), 2))
    mh = morbit_valid_maps(enc)
    groups = rng.permutation(9)
    digs = {'.': [SYMS[g] for g in groups[:3]], '-': [SYMS[g] for g in groups[3:6]], 'x': [SYMS[g] for g in groups[6:]]}
    enc2 = "".join(digs[c][int(rng.integers(3))] for c in ms)
    ph = pollux_valid_maps(enc2)
    return {"morbit_valid": len(mh), "morbit_true_key_found": any(list(p) == perm for p, _ in mh),
            "pollux_valid": len(ph)}


def control_machinery():
    rng = np.random.default_rng(CONTROL_SEED + 5)
    ok_m1 = True
    for s in (rng.permutation(to_idx(FAED[:120])), rng.permutation(to_idx(DBBI))):
        rows = rng.integers(0, ALL9.shape[0], 100)
        for off in range(3):
            vec, _ = m1_ioc_all(s, off, ALL9[rows])
            text = "".join(SYMS[v] for v in s)
            for r, v in zip(rows, vec):
                d = m1_direct(text, {SYMS[k]: int(ALL9[r][k]) for k in range(9)}, off)
                ok_m1 &= abs(d - v) < 1e-12
    ok_m2 = True
    checked = 0
    s = rng.permutation(to_idx(FAED))  # shuffled: no real-stream statistic before the lock
    for x in range(9):
        sc, _, _ = m2_scores_for_x(s, x)
        for r in rng.integers(0, KEY8.shape[0], 34):
            text = m2_decode_direct(s, x, KEY8[r])
            if text is None:
                ok_m2 &= not np.isfinite(sc[r])
            else:
                ok_m2 &= abs(quad_norm(text) - sc[r]) < 1e-3
            checked += 1
    return {"m1_vectorized_equals_direct": bool(ok_m1), "m2_vectorized_equals_direct": bool(ok_m2),
            "m2_checked": checked}


def self_test():
    res = {"machinery": control_machinery(), "morse_planted": control_morse_planted(),
           "m1_planted": control_m1_planted(), "m2_planted": control_m2_planted()}
    ok = (res["machinery"]["m1_vectorized_equals_direct"] and res["machinery"]["m2_vectorized_equals_direct"]
          and res["morse_planted"]["morbit_true_key_found"] and res["morse_planted"]["pollux_valid"] >= 1
          and all(r["true_reaches_max"] and r["exceeds_p99"] for r in res["m1_planted"])
          and all(r["true_valid"] and r["true_reaches_max"] and r["exceeds_all_nulls"] for r in res["m2_planted"]))
    res["all_passed"] = bool(ok)
    return res


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_fields():
    return {
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(__file__),
        "test_sha256": sha256_file(TEST_PATH),
        "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
        "quadgram_sha256": sha256_file(QUAD_PATH),
        "text_source_sha256": sha256_file(TEXT_SOURCE),
        "m1": {"seed": M1_SEED, "nulls": M1_NULLS}, "m2": {"seed": M2_SEED, "nulls": M2_NULLS},
        "bar_holm": BAR,
    }


def prepare():
    res = self_test()
    print(json.dumps(res, indent=2))
    if not res["all_passed"]:
        raise SystemExit("controls failed; no lock written")
    lock = expected_lock_fields()
    lock["controls"] = res
    LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print("lock written", LOCK_PATH)


def verify_lock():
    if not LOCK_PATH.exists():
        raise SystemExit("no lock; run --prepare first")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    want = expected_lock_fields()
    bad = [k for k in want if lock.get(k) != want[k]]
    if bad:
        raise SystemExit(f"lock mismatch in: {bad}")
    if not lock["controls"]["all_passed"]:
        raise SystemExit("locked controls did not pass")


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def run():
    verify_lock()
    streams = {"FAED": to_idx(FAED), "DBBI": to_idx(DBBI)}
    result = {"lock_sha256": sha256_file(LOCK_PATH), "m1": {}, "m2": {}, "m3_morbit": {}, "m4_pollux": {}}

    for name, s in streams.items():
        ioc, m, off = m1_family(s)
        nulls = null_dist(_m1_null_worker, s, M1_NULLS, M1_SEED + (0 if name == "FAED" else 1))
        result["m1"][name] = {"max_ioc": ioc, "map": ALL9[m].tolist(), "offset": off,
                              "null_median": float(np.median(nulls)), "null_p99": float(np.quantile(nulls, 0.99)),
                              "p": pval(ioc, nulls), "gated": name == "FAED"}
        print("M1", name, result["m1"][name], flush=True)

    for name, s in streams.items():
        stat, best = m2_family(s)
        entry = {"stat": stat, "C1_max": best["C1"][0], "C2_max": best["C2"][0]}
        for conv in ("C1", "C2"):
            if best[conv][1] is not None:
                x, row = best[conv][1]
                entry[f"{conv}_x"] = SYMS[x]
                entry[f"{conv}_decode"] = m2_decode_direct(s, x, KEY8[row])[:120]
        if math.isfinite(stat):
            nulls = null_dist(_m2_null_worker, s, M2_NULLS, M2_SEED + (0 if name == "FAED" else 1))
            finite = [v for v in nulls if math.isfinite(v)]
            entry.update({"null_median": float(np.median(finite)) if finite else None,
                          "null_valid_fraction": len(finite) / len(nulls), "p": pval(stat, nulls)})
        else:
            entry.update({"p": 1.0, "note": "no valid map; statistic -inf"})
        result["m2"][name] = entry
        print("M2", name, entry, flush=True)

    for name, s in (("FAED", FAED), ("DBBI", DBBI)):
        for lab, t in (("fwd", s), ("rev", s[::-1])):
            mh, ph = morbit_valid_maps(t), pollux_valid_maps(t)
            result["m3_morbit"][f"{name}_{lab}"] = {"valid": len(mh), "examples": [r[:80] for _, r in mh[:3]]}
            result["m4_pollux"][f"{name}_{lab}"] = {"valid": len(ph), "examples": [r[:80] for _, r in ph[:3]]}
            print("M3/M4", name, lab, len(mh), len(ph), flush=True)

    cells = [("M1-FAED", result["m1"]["FAED"]["p"]), ("M2-FAED", result["m2"]["FAED"]["p"]),
             ("M2-DBBI", result["m2"]["DBBI"]["p"])]
    adj = holm([p for _, p in cells])
    result["gate"] = {c: {"p": p, "holm": a, "outcome": "checkpoint" if a <= BAR else "null_like"}
                      for (c, p), a in zip(cells, adj)}
    exact_zero = all(v["valid"] == 0 for v in result["m3_morbit"].values()) and \
        all(v["valid"] == 0 for v in result["m4_pollux"].values())
    result["census_verdict"] = ("no_untested_native_nine_producer_in_census"
                                if exact_zero and all(g["outcome"] == "null_like" for g in result["gate"].values())
                                else "signal_or_valid_map_reported")
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate"], indent=2), result["census_verdict"])


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--prepare", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        res = self_test()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["all_passed"] else 1)
    if a.prepare:
        prepare()
    else:
        run()


if __name__ == "__main__":
    main()
