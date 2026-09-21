#!/usr/bin/env python3
"""Phase 546 -- selectivity curve for the BTCSEED prefix over Bifid squares.

Protocol: doc/Brainstorms/2026-09-21 - Phase 546 Prefix Selectivity Curve Protocol.md
(written before any class rate was computed for the real FAED).

Option 2 of the BTCSEED tail brainstorm. FAED and the decoder are fixed (the
community configuration: whole 570-symbol block, row-column, forward). Only the
25-letter square varies. Two populations:

  Arm A (exact)   all 9! = 362,880 squares whose first nine cells hold the FAED
                  symbols A..I in any order, followed by K..Z alphabetically
                  (the DBBI-keyed square is one of them).
  Arm B (sample)  20,000,000 uniformly random 25-letter squares.

For each square only the first seven decoded letters are needed; they depend on
FAED[0:4] and FAED[285:289]. Prefix classes (nested):

  E1  prefix == BTCSEED
  E2  prefix is a 7-letter dictionary word
  E3  E2, or a 3-letter token followed by a 4-letter dictionary word (or the
      reverse); 3-letter tokens = dictionary 3-letter words plus BTC

Modes: --self-test (controls on toy classes, no real class rate), --prepare (lock),
--run (verify lock, compute the rates once).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI, FAED  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import build_grid, bifid_decrypt  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-21 - Phase 546 Prefix Selectivity Curve Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase546_selectivity_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase546_selectivity_result.json"
DICT_PATH = Path("/usr/share/dict/words").resolve()

ALPHA = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
IDX = {c: i for i, c in enumerate(ALPHA)}
FAED_U = FAED.upper()
HALF = len(FAED_U) // 2
PREFIX = 7
TARGET = "BTCSEED"
N_B = 20_000_000
BATCH = 250_000
SEED = 546
T_MAX = 10_000
CHERRY_MIN_COUNT = 37          # rate >= 1e-4 of 362,880 (expected >= 1 event in T_MAX squares)
SELECTIVE_MAX_COUNT = 3        # rate <= 8.3e-6 (expected <= 0.083 events in T_MAX squares)
DECODE_SHA256 = "0c5d984f90e9baefc09f1d3888e62acbd101f9b0194887e2ae88fc6c9967745e"

SYM_IDX = [IDX[FAED_U[k]] for k in range(4)] + [IDX[FAED_U[HALF + k]] for k in range(4)]
POW = np.array([25 ** (PREFIX - 1 - i) for i in range(PREFIX)], dtype=np.int64)


# --------------------------------------------------------------------------
# prefix from a batch of squares
# --------------------------------------------------------------------------
def prefix_codes(perm):
    """perm: (M, 25) int array, letter index held by each cell. Returns int64
    base-25 codes of the decoded first seven letters (community decode)."""
    perm = perm.astype(np.int16, copy=False)
    inv = np.argsort(perm, axis=1).astype(np.int16)
    m = perm.shape[0]
    rows = np.arange(m)
    code = np.zeros(m, dtype=np.int64)
    for i in range(PREFIX):
        k = i // 2
        cell_a = inv[rows, SYM_IDX[k]]
        cell_b = inv[rows, SYM_IDX[4 + k]]
        if i % 2 == 0:
            x, y = cell_a // 5, cell_b // 5           # row coordinates
        else:
            x, y = cell_a % 5, cell_b % 5             # column coordinates
        letter = perm[rows, x * 5 + y]
        code += letter.astype(np.int64) * POW[i]
    return code


def encode(word):
    return sum(IDX[c] * 25 ** (len(word) - 1 - i) for i, c in enumerate(word))


def decode_code(code):
    out = []
    for _ in range(PREFIX):
        out.append(ALPHA[code % 25])
        code //= 25
    return "".join(reversed(out))


def slow_prefix(perm_row):
    """Reference: full Bifid decode of FAED under the square, first 7 letters."""
    letters = "".join(ALPHA[i] for i in perm_row)
    grid, pos = {}, {}
    for i, ch in enumerate(letters):
        r, c = divmod(i, 5)
        grid[(r, c)] = ch
        pos[ch] = (r, c)
    return bifid_decrypt(FAED_U, pos, grid)[:PREFIX]


# --------------------------------------------------------------------------
# classes
# --------------------------------------------------------------------------
def load_words():
    by_len = {3: set(), 4: set(), 7: set()}
    with DICT_PATH.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            w = line.strip()
            if w.isascii() and w.isalpha() and len(w) in by_len:
                u = w.upper()
                if "J" not in u:
                    by_len[len(u)].add(u)
    return {k: sorted(v) for k, v in by_len.items()}


def class_codes(words):
    d3 = sorted(set(words[3]) | {"BTC"})
    d4, d7 = words[4], words[7]
    c3 = np.array([encode(w) for w in d3], dtype=np.int64)
    c4 = np.array([encode(w) for w in d4], dtype=np.int64)
    c7 = np.array([encode(w) for w in d7], dtype=np.int64)
    p4, p3 = 25 ** 4, 25 ** 3
    tok_first = (c3[:, None] * p4 + c4[None, :]).ravel()      # 3 + 4
    tok_second = (c4[:, None] * p3 + c3[None, :]).ravel()     # 4 + 3
    e1 = np.array([encode(TARGET)], dtype=np.int64)
    e2 = np.unique(c7)
    e3 = np.unique(np.concatenate([c7, tok_first, tok_second]))
    return {"E1": e1, "E2": e2, "E3": e3}


def member(codes, sorted_set):
    idx = np.searchsorted(sorted_set, codes)
    idx[idx == len(sorted_set)] = len(sorted_set) - 1
    return sorted_set[idx] == codes


# --------------------------------------------------------------------------
# arms
# --------------------------------------------------------------------------
def arm_a_perms():
    p = np.array(list(itertools.permutations(range(9))), dtype=np.int16)
    tail = np.tile(np.arange(9, 25, dtype=np.int16), (p.shape[0], 1))
    return np.concatenate([p, tail], axis=1)


def arm_b_batches(n=N_B, batch=BATCH, seed=SEED):
    rng = np.random.default_rng(seed)
    done = 0
    while done < n:
        m = min(batch, n - done)
        yield np.argsort(rng.random((m, 25)), axis=1).astype(np.int16)
        done += m


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


# --------------------------------------------------------------------------
# controls (toy classes only; no real class rate is computed here)
# --------------------------------------------------------------------------
def control_fast_vs_slow():
    rng = np.random.default_rng(SEED - 1)
    perm = np.argsort(rng.random((400, 25)), axis=1).astype(np.int16)
    fast = [decode_code(int(c)) for c in prefix_codes(perm)]
    slow = [slow_prefix(p) for p in perm]
    a = arm_a_perms()[np.random.default_rng(SEED - 2).integers(0, 362880, 200)]
    fast_a = [decode_code(int(c)) for c in prefix_codes(a)]
    slow_a = [slow_prefix(p) for p in a]
    return {"random_squares_match_full_decode": fast == slow,
            "arm_a_squares_match_full_decode": fast_a == slow_a}


def control_real_square():
    d = "DBIFHCEGA"
    real = np.array([[IDX[c] for c in d] + list(range(9, 25))], dtype=np.int16)
    code = int(prefix_codes(real)[0])
    letters, grid, pos = build_grid(DBBI[:13])
    return {
        "real_ordering_prefix_is_BTCSEED": decode_code(code) == TARGET,
        "real_square_is_dbifh": letters == "".join(ALPHA[i] for i in real[0]),
        "real_decode_hash_matches": hashlib.sha256(
            bifid_decrypt(FAED_U, pos, grid).encode()).hexdigest() == DECODE_SHA256,
    }


def control_class_machinery(words):
    classes = class_codes(words)
    d4 = set(words[4])
    ok_members = (
        member(np.array([encode("BTCSEED")]), classes["E1"])[0]
        and member(np.array([encode("BTCSEED")]), classes["E3"])[0]
        and ("SEED" in d4)
        and not member(np.array([encode("BTCSEED")]), classes["E2"])[0]
        and set(classes["E2"]) <= set(classes["E3"])
        and not member(np.array([encode("ZZZZZZZ")]), classes["E3"])[0]
    )
    return {"btcseed_in_E1_E3_not_E2": bool(ok_members),
            "class_sizes": {k: int(len(v)) for k, v in classes.items()}}


def control_counting():
    """Exact Arm A count vs a Monte Carlo draw from the same population, and the
    batch path vs a plain per-square path. The toy classes are prefixes of random
    squares (non-vacuous by construction) and say nothing about E1-E3."""
    rng = np.random.default_rng(SEED - 3)
    a = arm_a_perms()
    toy_a = np.unique(prefix_codes(a[rng.integers(0, a.shape[0], 3000)]))
    exact = int(member(prefix_codes(a), toy_a).sum())
    n = 1_000_000
    mc = int(member(prefix_codes(a[rng.integers(0, a.shape[0], n)]), toy_a).sum())
    p = exact / a.shape[0]
    sigma = math.sqrt(n * p * (1 - p))
    perm = np.argsort(rng.random((3000, 25)), axis=1).astype(np.int16)
    toy_b = np.unique(prefix_codes(perm[:300]))
    batch_hits = int(member(prefix_codes(perm), toy_b).sum())
    toy_b_strings = {decode_code(int(c)) for c in toy_b}
    plain_hits = sum(1 for row in perm if slow_prefix(row) in toy_b_strings)
    return {
        "arm_a_size": int(a.shape[0]),
        "toy_exact_count_nonvacuous": exact >= 1000,
        "mc_within_4_sigma_of_exact": abs(mc - n * p) <= 4 * sigma + 1,
        "batch_hits_nonvacuous": batch_hits >= 300,
        "batch_equals_plain_count": batch_hits == plain_hits,
    }


def self_test():
    words = load_words()
    checks = {
        "fast_vs_slow": control_fast_vs_slow(),
        "real_square": control_real_square(),
        "class_machinery": control_class_machinery(words),
        "counting": control_counting(),
    }
    ok = (all(checks["fast_vs_slow"].values())
          and checks["real_square"]["real_ordering_prefix_is_BTCSEED"]
          and checks["real_square"]["real_square_is_dbifh"]
          and checks["real_square"]["real_decode_hash_matches"]
          and checks["class_machinery"]["btcseed_in_E1_E3_not_E2"]
          and checks["counting"]["toy_exact_count_nonvacuous"]
          and checks["counting"]["mc_within_4_sigma_of_exact"]
          and checks["counting"]["batch_hits_nonvacuous"]
          and checks["counting"]["batch_equals_plain_count"])
    return {"ok": bool(ok), "checks": checks}


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_fields(words=None):
    words = words or load_words()
    classes = class_codes(words)
    return {
        "phase": 546,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(__file__),
        "test_sha256": sha256_file(SCRIPT_DIR / "test_phase546_prefix_selectivity_curve.py"),
        "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
        "phase386_script_sha256": sha256_file(SCRIPT_DIR / "phase386_btcseed_bifid_faed_decode_audit.py"),
        "dictionary_file_sha256": sha256_file(DICT_PATH),
        "word_counts": {str(k): len(v) for k, v in words.items()},
        "class_sizes": {k: int(len(v)) for k, v in classes.items()},
        "class_digests": {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in classes.items()},
        "faed_sha256": hashlib.sha256(FAED_U.encode()).hexdigest(),
        "n_b": N_B, "seed": SEED, "batch": BATCH, "t_max": T_MAX,
        "cherry_min_count": CHERRY_MIN_COUNT, "selective_max_count": SELECTIVE_MAX_COUNT,
    }


def prepare():
    if LOCK_PATH.exists():
        raise SystemExit(f"{LOCK_PATH.name} exists; refusing to overwrite")
    st = self_test()
    if not st["ok"]:
        print(json.dumps(st, indent=2))
        raise SystemExit("controls failed; no lock written and no real class rate computed")
    fields = expected_lock_fields()
    fields["controls"] = st["checks"]
    LOCK_PATH.write_text(json.dumps(fields, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"lock": str(LOCK_PATH), "classes": fields["class_sizes"]}


def verify_lock():
    if not LOCK_PATH.exists():
        raise SystemExit("no lock; run --prepare first")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    want = expected_lock_fields()
    bad = [k for k in want if lock.get(k) != want[k]]
    if bad:
        raise SystemExit(f"lock mismatch in: {bad}")
    return lock


def run():
    verify_lock()
    words = load_words()
    classes = class_codes(words)
    # Arm A: exact
    a = arm_a_perms()
    ca = prefix_codes(a)
    n_a = int(a.shape[0])
    real = int(np.flatnonzero((a[:, :9] == np.array([IDX[c] for c in "DBIFHCEGA"])).all(axis=1))[0])
    arm_a = {c: int(member(ca, s).sum()) for c, s in classes.items()}
    real_prefix = decode_code(int(ca[real]))
    e3_mask = member(ca, classes["E3"])
    uniq, cnt = np.unique(ca[e3_mask], return_counts=True)
    order = np.argsort(-cnt)[:10]
    top_a = [{"prefix": decode_code(int(uniq[i])), "orderings": int(cnt[i])} for i in order]
    distinct_prefixes_a = int(len(np.unique(ca)))
    # Arm B: sample
    counts_b = {c: 0 for c in classes}
    seen = 0
    for perm in arm_b_batches():
        cb = prefix_codes(perm)
        for c, s in classes.items():
            counts_b[c] += int(member(cb, s).sum())
        seen += perm.shape[0]
    assert seen == N_B
    k3 = arm_a["E3"]
    if k3 >= CHERRY_MIN_COUNT:
        outcome = "cherry_pickable"
    elif k3 <= SELECTIVE_MAX_COUNT:
        outcome = "selective"
    else:
        outcome = "indeterminate"

    def rates(counts, n):
        return {c: {"count": counts[c], "rate": counts[c] / n, "wilson95": wilson(counts[c], n)}
                for c in counts}

    def expected(rate):
        return {str(t): round(1 - (1 - rate) ** t, 6) for t in (12, 1248, 10_000, 1_000_000)}

    out = {
        "phase": 546,
        "lock_sha256": sha256_file(LOCK_PATH),
        "real_ordering_prefix": real_prefix,
        "arm_a": {"squares": n_a, "distinct_prefixes": distinct_prefixes_a,
                  "rates": rates(arm_a, n_a),
                  "top_E3_prefixes": top_a,
                  "at_least_one_E3_in_T": expected(arm_a["E3"] / n_a)},
        "arm_b": {"squares": N_B, "rates": rates(counts_b, N_B),
                  "at_least_one_E3_in_T": expected(counts_b["E3"] / N_B)},
        "t_max": T_MAX,
        "thresholds": {"cherry_min_count": CHERRY_MIN_COUNT, "selective_max_count": SELECTIVE_MAX_COUNT},
        "outcome": outcome,
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
