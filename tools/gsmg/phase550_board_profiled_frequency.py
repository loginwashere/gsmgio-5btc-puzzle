#!/usr/bin/env python3
"""Phase 550 -- board-profiled frequency test of FAED.

Protocol: doc/Brainstorms/2026-09-29 - Phase 550 Board-Profiled Frequency Test Protocol.md

Can FAED's sorted symbol-count profile (invariant to any transposition of the
output and to relabeling) be produced by a nine-symbol straddling checkerboard
(7 single cells + 2 escape rows of 9) over letters-only English, for any board
the declared search reaches? The board is profiled out:
T = min_B X2(sort(O), sort(N * pi_B)). Calibration by simulation at several
boards; p is the maximum over them. No decode, key search or oracle.

Modes: --self-test (controls only), --prepare (controls + lock), --run.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI, FAED, PHASE32_BLOB_B64, PHASE32_PASSWORD, VALIDATION_ANSWER  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-29 - Phase 550 Board-Profiled Frequency Test Protocol.md"
BOOK = ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
SCREEN = ROOT / "wordlists/gsmg/matrix_script_windows.txt"
LOCK_PATH = SCRIPT_DIR / "phase550_board_profile_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase550_board_profile_result.json"
TEST_PATH = SCRIPT_DIR / "test_phase550_board_profiled_frequency.py"

SEED, S = 550, 200
CONTROL_SEED = 5500
N_ADEQ, N_SIZE, N_POWER = 100, 200, 100
RESTARTS, STEPS, T_HI, T_LO = 6, 4000, 5.0, 0.01
BAR, SIZE_MAX, ADEQ_MIN = 0.01, 0.04, 99
WORKERS = min(16, mp.cpu_count())
SYMS = "abcdefghi"
LETTERS25 = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
LIDX = {c: i for i, c in enumerate(LETTERS25)}

# cells 0..6 single (symbol = cell); 7..15 escape row 7, column c; 16..24 escape row 8, column c
CELL_CODES = [(i,) for i in range(7)] + [(7, c) for c in range(9)] + [(8, c) for c in range(9)]
A = np.zeros((9, 25))
for _k, _code in enumerate(CELL_CODES):
    for _sym in _code:
        A[_sym, _k] += 1


# --------------------------------------------------------------------------
# corpora
# --------------------------------------------------------------------------
def norm25(text):
    return "".join(c for c in text.upper() if "A" <= c <= "Z").replace("J", "I")


def corpus_book():
    return norm25(" ".join(ln for ln in BOOK.read_text(encoding="utf-8").splitlines() if not ln.startswith("#")))


def corpus_screen():
    segs, cur, prev = [], None, None
    with SCREEN.open(encoding="utf-8") as fh:
        for ln in fh:
            w = ln.split()
            if prev is not None and w[:-1] == prev[1:]:
                cur.append(w[-1])
            else:
                if cur:
                    segs.append(" ".join(cur))
                cur = list(w)
            prev = w
    segs.append(" ".join(cur))
    return norm25(" ".join(dict.fromkeys(segs)))


def phase32_plaintext():
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    raw = base64.b64decode(PHASE32_BLOB_B64)
    salt, ct = raw[8:16], raw[16:]
    d, prev = b"", b""
    while len(d) < 48:
        prev = hashlib.sha256(prev + PHASE32_PASSWORD.encode() + salt).digest()
        d += prev
    pt = Cipher(algorithms.AES(d[:32]), modes.CBC(d[32:48])).decryptor().update(ct)
    return pt[:-pt[-1]]


def answer_321(pt):
    cipher = pt.split(b"\r\n\r\n")[2].decode("latin-1").encode("cp273").decode("ascii")
    key = "THEMATRIXHASYOU"
    return "".join(chr((ord(key[i % 15]) - ord(c.upper())) % 26 + 65) for i, c in enumerate(cipher))


def corpus_puzzle():
    pt = phase32_plaintext()
    parts = pt.split(b"\r\n\r\n")
    english = " ".join(parts[i].decode("latin-1") for i in (0, 1, 4))
    return norm25(english + answer_321(pt) + VALIDATION_ANSWER)


CORPUS_FUNCS = {"K1_book": corpus_book, "K2_screenplay": corpus_screen, "K3_puzzle": corpus_puzzle}
_CORPORA = {}


def corpus(name):
    if name not in _CORPORA:
        text = CORPUS_FUNCS[name]()
        idx = np.array([LIDX[c] for c in text], dtype=np.int64)
        q = np.bincount(idx, minlength=25).astype(np.float64)
        _CORPORA[name] = (idx, q / q.sum())
    return _CORPORA[name]


# --------------------------------------------------------------------------
# boards, encoding, statistic
# --------------------------------------------------------------------------
def vic_board(q):
    """cell -> letter: 7 most frequent letters in single cells, rest in frequency order."""
    return np.argsort(-q, kind="stable").astype(np.int64)


def random_board(rng):
    return rng.permutation(25).astype(np.int64)


def encode_counts(letters, board, n):
    """Counts of the first n symbols when letter indices are encoded with board (cell -> letter)."""
    cell_of = np.empty(25, dtype=np.int64)
    cell_of[board] = np.arange(25)
    out = []
    for L in letters:
        out.extend(CELL_CODES[cell_of[L]])
        if len(out) >= n:
            break
    return np.bincount(np.array(out[:n]), minlength=9).astype(np.float64)


def sample_counts(name, board, n, rng):
    idx, _ = corpus(name)
    start = int(rng.integers(0, len(idx) - n))
    return encode_counts(idx[start:start + n], board, n)


def x2_sorted(obs_sorted, w):
    e = np.sort(w / w.sum())[::-1] * obs_sorted.sum()
    return float(np.sum((obs_sorted - e) ** 2 / np.maximum(e, 1e-12)))


def objective(board, q, obs_sorted):
    return x2_sorted(obs_sorted, A @ q[board])


def search(obs, q, rng, restarts=RESTARTS, steps=STEPS):
    """Annealing over cell->letter permutations, then 2-swap polish. Returns (T, board)."""
    obs_sorted = np.sort(np.asarray(obs, dtype=np.float64))[::-1]
    best_f, best_b = math.inf, None
    temps = T_HI * (T_LO / T_HI) ** (np.arange(steps) / max(steps - 1, 1))
    for _ in range(restarts):
        b = rng.permutation(25).astype(np.int64)
        w = A @ q[b]
        f = x2_sorted(obs_sorted, w)
        ij = rng.integers(0, 25, size=(steps, 2))
        us = rng.random(steps)
        for t in range(steps):
            i, j = ij[t]
            if i == j:
                continue
            w2 = w + (q[b[j]] - q[b[i]]) * (A[:, i] - A[:, j])
            f2 = x2_sorted(obs_sorted, w2)
            if f2 <= f or us[t] < math.exp((f - f2) / temps[t]):
                b[i], b[j] = b[j], b[i]
                w, f = w2, f2
        improved = True
        while improved:
            improved = False
            for i in range(25):
                for j in range(i + 1, 25):
                    w2 = w + (q[b[j]] - q[b[i]]) * (A[:, i] - A[:, j])
                    f2 = x2_sorted(obs_sorted, w2)
                    if f2 < f - 1e-12:
                        b[i], b[j] = b[j], b[i]
                        w, f, improved = w2, f2, True
        if f < best_f:
            best_f, best_b = f, b.copy()
    return best_f, best_b


# --------------------------------------------------------------------------
# parallel simulation
# --------------------------------------------------------------------------
def _sim_task(args):
    name, board, n, seed = args
    rng = np.random.default_rng(seed)
    obs = sample_counts(name, np.asarray(board), n, rng)
    return search(obs, corpus(name)[1], rng)[0]


def _search_task(args):
    name, obs, seed = args
    return search(np.asarray(obs), corpus(name)[1], np.random.default_rng(seed))[0]


def pool_map(fn, tasks):
    for name in CORPUS_FUNCS:
        corpus(name)  # load before fork
    with mp.get_context("fork").Pool(WORKERS) as pool:
        return pool.map(fn, tasks, chunksize=1)


def seeds(tag, n):
    return np.random.SeedSequence([SEED, tag]).generate_state(n).tolist()


def control_boards(name):
    q = corpus(name)[1]
    rng = np.random.default_rng([SEED, 1, list(CORPUS_FUNCS).index(name)])
    return [("VIC", vic_board(q))] + [(f"R{i}", random_board(rng)) for i in range(5)]


def null_dist(name, board, n, tag):
    return pool_map(_sim_task, [(name, board.tolist(), n, sd) for sd in seeds(tag, S)])


def pval(t, sims):
    return (1 + sum(v >= t for v in sims)) / (1 + len(sims))


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def control_adequacy(name, k):
    rng = np.random.default_rng([CONTROL_SEED, 1, k])
    q = corpus(name)[1]
    boards = [vic_board(q) if i % 2 == 0 else random_board(rng) for i in range(N_ADEQ)]
    obs = [sample_counts(name, b, 570, rng) for b in boards]
    truth = [objective(b, q, np.sort(o)[::-1]) for b, o in zip(boards, obs)]
    found = pool_map(_search_task, [(name, o.tolist(), sd) for o, sd in
                                    zip(obs, np.random.SeedSequence([CONTROL_SEED, 2, k]).generate_state(N_ADEQ).tolist())])
    ok = sum(f <= t + 1e-9 for f, t in zip(found, truth))
    return {"not_worse_than_truth": int(ok), "of": N_ADEQ, "pass": ok >= ADEQ_MIN}


def pooled_null(name, k):
    out = {}
    for j, (label, b) in enumerate(control_boards(name)):
        out[label] = null_dist(name, b, 570, 100 + 10 * k + j)
    return out


def stream_counts_alt(kind, rng, n=570):
    if kind == "uniform9":
        return np.bincount(rng.integers(0, 9, n), minlength=9).astype(np.float64)
    if kind == "merged_decimal":
        p = np.array([0.2] + [0.1] * 8)
        return np.bincount(rng.choice(9, n, p=p), minlength=9).astype(np.float64)
    if kind == "cb_hex":
        board = rng.permutation(25)[:16]
        letters = rng.integers(0, 16, n)
        out = []
        for L in letters:
            out.extend(CELL_CODES[board[L]])
            if len(out) >= n:
                break
        return np.bincount(np.array(out[:n]), minlength=9).astype(np.float64)
    raise ValueError(kind)


def control_size_power(name, k, pooled):
    null = [v for vals in pooled.values() for v in vals]
    rng = np.random.default_rng([CONTROL_SEED, 3, k])
    size_obs = [sample_counts(name, random_board(rng), 570, rng) for _ in range(N_SIZE)]
    alts = {kind: [stream_counts_alt(kind, rng) for _ in range(N_POWER)]
            for kind in ("uniform9", "merged_decimal", "cb_hex")}
    tasks = [(name, o.tolist(), sd) for o, sd in
             zip(size_obs, np.random.SeedSequence([CONTROL_SEED, 4, k]).generate_state(N_SIZE).tolist())]
    for j, kind in enumerate(alts):
        tasks += [(name, o.tolist(), sd) for o, sd in
                  zip(alts[kind], np.random.SeedSequence([CONTROL_SEED, 5, k, j]).generate_state(N_POWER).tolist())]
    ts = pool_map(_search_task, tasks)
    size_rate = sum(pval(t, null) <= BAR for t in ts[:N_SIZE]) / N_SIZE
    power = {}
    for j, kind in enumerate(alts):
        chunk = ts[N_SIZE + j * N_POWER:N_SIZE + (j + 1) * N_POWER]
        power[kind] = sum(pval(t, null) <= BAR / 3 for t in chunk) / N_POWER
    return {"size_rate": size_rate, "size_pass": size_rate <= SIZE_MAX, "power_at_holm_first_step": power,
            "null_median": float(np.median(null)), "null_p99": float(np.quantile(null, 0.99))}


def self_test():
    res = {}
    for k, name in enumerate(CORPUS_FUNCS):
        adeq = control_adequacy(name, k)
        pooled = pooled_null(name, k)
        sp = control_size_power(name, k, pooled)
        res[name] = {"letters": int(len(corpus(name)[0])), "adequacy": adeq, "size_power": sp}
        print(name, json.dumps(res[name]), flush=True)
    res["all_passed"] = bool(all(res[n]["adequacy"]["pass"] and res[n]["size_power"]["size_pass"]
                                 for n in CORPUS_FUNCS))
    return res


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_fields():
    return {"protocol_sha256": sha256_file(PROTOCOL), "script_sha256": sha256_file(__file__),
            "test_sha256": sha256_file(TEST_PATH), "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
            "book_sha256": sha256_file(BOOK), "screen_sha256": sha256_file(SCREEN),
            "seed": SEED, "S": S, "search": [RESTARTS, STEPS, T_HI, T_LO], "bar_holm": BAR}


def prepare():
    res = self_test()
    if not res["all_passed"]:
        print(json.dumps(res, indent=2))
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
    return lock


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def board_text(board):
    letters = [LETTERS25[i] for i in board]
    return {"single": "".join(letters[:7]), "row7": "".join(letters[7:16]), "row8": "".join(letters[16:25])}


def run():
    verify_lock()
    faed = np.bincount([SYMS.index(c) for c in FAED], minlength=9).astype(np.float64)
    dbbi = np.bincount([SYMS.index(c) for c in DBBI], minlength=9).astype(np.float64)
    result = {"lock_sha256": sha256_file(LOCK_PATH), "faed_sorted_counts": np.sort(faed)[::-1].tolist(),
              "corpora": {}}
    for k, name in enumerate(CORPUS_FUNCS):
        q = corpus(name)[1]
        t_obs, b_hat = search(faed, q, np.random.default_rng([SEED, 2, k]))
        e_hat = (np.sort(A @ q[b_hat] / (A @ q[b_hat]).sum())[::-1] * 570).round(1).tolist()
        boards = control_boards(name) + [("B_hat", b_hat)]
        per_board = {}
        for j, (label, b) in enumerate(boards):
            sims = null_dist(name, b, 570, 300 + 10 * k + j)
            per_board[label] = {"p": pval(t_obs, sims), "sim_median": float(np.median(sims))}
        p_max = max(v["p"] for v in per_board.values())
        # DBBI, reported only
        t_d, b_d = search(dbbi, q, np.random.default_rng([SEED, 3, k]))
        dbbi_p = {}
        for j, (label, b) in enumerate((("VIC", vic_board(q)), ("B_hat_dbbi", b_d))):
            sims = null_dist(name, b, 91, 400 + 10 * k + j)
            dbbi_p[label] = pval(t_d, sims)
        result["corpora"][name] = {"T_obs": t_obs, "B_hat": board_text(b_hat), "E_hat_sorted": e_hat,
                                   "per_board": per_board, "p_max": p_max,
                                   "dbbi": {"T_obs": t_d, "B_hat": board_text(b_d), "p": dbbi_p}}
        print(name, json.dumps(result["corpora"][name]), flush=True)
    names = list(CORPUS_FUNCS)
    adj = holm([result["corpora"][n]["p_max"] for n in names])
    result["gate"] = {n: {"p_max": result["corpora"][n]["p_max"], "holm": a,
                          "verdict": "excluded" if a <= BAR else "compatible"} for n, a in zip(names, adj)}
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate"], indent=2))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--prepare", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        res = self_test()
        sys.exit(0 if res["all_passed"] else 1)
    if a.prepare:
        prepare()
    else:
        run()


if __name__ == "__main__":
    main()
