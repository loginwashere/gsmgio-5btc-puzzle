#!/usr/bin/env python3
"""Phase 548 -- generator fingerprint of FAED and DBBI.

Protocol: doc/Brainstorms/2026-09-29 - Phase 548 Generator Fingerprint Protocol.md
(written before any generator was compared with the real streams).

Simulates concrete nine-symbol producers (checkerboards over English / hex /
random letters, VIC chain addition, base-9 byte encodings, plus IID references)
and asks which of them can produce FAED's label-invariant statistics, with the
power of each comparison measured on planted streams. No decode, key search or
oracle.

Modes: --self-test (controls only), --prepare (controls + lock), --run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI, FAED  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-29 - Phase 548 Generator Fingerprint Protocol.md"
CORPUS = ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
LOCK_PATH = SCRIPT_DIR / "phase548_fingerprint_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase548_fingerprint_result.json"
TEST_PATH = SCRIPT_DIR / "test_phase548_generator_fingerprint.py"

SYMS = "abcdefghi"
SEED, M = 548, 2000
CONTROL_SEED, N_PLANT = 5480, 200
BAR = 0.01
SIZE_MAX = 0.04
MECHANISMS = ["CB-ENG", "CB-ENG-VIC", "CB-HEX", "CB-RAND", "CB-ENG-CHAIN", "B9-ENG", "B9-BYTES"]
REFERENCES = ["UNIF", "IID-FIT"]
GENERATORS = MECHANISMS + REFERENCES
FAED_COUNTS = np.array([FAED.count(c) for c in SYMS], dtype=np.float64)  # disclosed in protocol


def to_idx(s):
    return np.array([SYMS.index(c) for c in s], dtype=np.int64)


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------
def load_corpus():
    lines = [ln for ln in CORPUS.read_text(encoding="utf-8").splitlines() if not ln.startswith("#")]
    text = "".join(c for c in " ".join(lines).upper() if "A" <= c <= "Z")
    return text


ENGLISH = load_corpus()
ENG25 = ENGLISH.replace("J", "I")
LETTERS25 = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
TOP7 = [c for c, _ in sorted(((c, ENG25.count(c)) for c in LETTERS25), key=lambda t: -t[1])[:7]]
CELLS = [(d,) for d in range(7)] + [(e, d) for e in (7, 8) for d in range(9)]  # 25 cells


def english_window(rng, n_letters, alphabet25=True):
    src = ENG25 if alphabet25 else ENGLISH
    start = int(rng.integers(0, len(src) - n_letters))
    return src[start:start + n_letters]


# --------------------------------------------------------------------------
# generators: each returns an int array of exactly n symbols in 0..8
# --------------------------------------------------------------------------
def encode_board(text, board, n):
    out = []
    for ch in text:
        out.extend(board[ch])
        if len(out) >= n:
            break
    return np.array(out[:n], dtype=np.int64)


def random_board(rng, letters):
    perm = rng.permutation(len(CELLS))[:len(letters)]
    return {ch: CELLS[int(k)] for ch, k in zip(letters, perm)}


def vic_board(rng):
    top = list(rng.permutation(TOP7))
    rest = [c for c in LETTERS25 if c not in TOP7]
    rest = [rest[int(k)] for k in rng.permutation(len(rest))]
    board = {ch: CELLS[i] for i, ch in enumerate(top)}
    board.update({ch: CELLS[7 + i] for i, ch in enumerate(rest)})
    return board


def gen_cb_eng(rng, n):
    return encode_board(english_window(rng, n), random_board(rng, LETTERS25), n)


def gen_cb_eng_vic(rng, n):
    return encode_board(english_window(rng, n), vic_board(rng), n)


def gen_cb_hex(rng, n):
    hexc = "0123456789ABCDEF"
    text = "".join(hexc[int(v)] for v in rng.integers(0, 16, n))
    return encode_board(text, random_board(rng, hexc), n)


def gen_cb_rand(rng, n):
    text = "".join(LETTERS25[int(v)] for v in rng.integers(0, 25, n))
    return encode_board(text, random_board(rng, LETTERS25), n)


def gen_cb_eng_chain(rng, n):
    d = gen_cb_eng(rng, n)
    L = int(rng.integers(5, 11))
    k = list(rng.integers(0, 9, L))
    while len(k) < n:
        k.append((k[-L] + k[-L + 1]) % 9)
    return (d + np.array(k[:n], dtype=np.int64)) % 9


def bytes_base9(bs, n):
    out = []
    for b in bs:
        out += [b // 81, (b // 9) % 9, b % 9]
    return np.array(out[:n], dtype=np.int64)


def gen_b9_eng(rng, n):
    return bytes_base9(english_window(rng, n // 3 + 1, alphabet25=False).encode("ascii"), n)


def gen_b9_bytes(rng, n):
    return bytes_base9(rng.integers(0, 256, n // 3 + 1).tolist(), n)


def gen_unif(rng, n):
    return rng.integers(0, 9, n).astype(np.int64)


def make_iid(counts):
    p = np.asarray(counts, dtype=np.float64)
    p = p / p.sum()

    def gen(rng, n):
        return rng.choice(9, size=n, p=p).astype(np.int64)
    return gen


GEN_FUNCS = {"CB-ENG": gen_cb_eng, "CB-ENG-VIC": gen_cb_eng_vic, "CB-HEX": gen_cb_hex,
             "CB-RAND": gen_cb_rand, "CB-ENG-CHAIN": gen_cb_eng_chain, "B9-ENG": gen_b9_eng,
             "B9-BYTES": gen_b9_bytes, "UNIF": gen_unif}


def generator(name, fit_counts=None):
    if name == "IID-FIT":
        return make_iid(fit_counts)
    return GEN_FUNCS[name]


# --------------------------------------------------------------------------
# statistics (label-invariant), 14 values
# --------------------------------------------------------------------------
STAT_NAMES = [f"sorted_p{i}" for i in range(8)] + ["repeat", "mi", "max_follow_chi2", "halves_chi2",
                                                    "period2_chi2", "period3_chi2"]


def contingency_chi2(table):
    table = table[:, table.sum(axis=0) > 0]
    if table.shape[1] < 2:
        return 0.0
    rows, cols, tot = table.sum(axis=1, keepdims=True), table.sum(axis=0, keepdims=True), table.sum()
    exp = rows * cols / tot
    with np.errstate(divide="ignore", invalid="ignore"):
        return float(np.nansum(np.where(exp > 0, (table - exp) ** 2 / exp, 0.0)))


def stats(s):
    s = np.asarray(s, dtype=np.int64)
    n = len(s)
    cnt = np.bincount(s, minlength=9).astype(np.float64)
    sp = np.sort(cnt / n)[::-1][:8]
    a, b = s[:-1], s[1:]
    repeat = float(np.mean(a == b))
    joint = np.zeros((9, 9))
    np.add.at(joint, (a, b), 1)
    pj = joint / joint.sum()
    pa, pb = pj.sum(axis=1, keepdims=True), pj.sum(axis=0, keepdims=True)
    nz = pj > 0
    mi = float(np.sum(pj[nz] * np.log2(pj[nz] / (pa @ pb)[nz])))
    marg = joint.sum(axis=0) / joint.sum()
    best = 0.0
    for x in range(9):
        nx = joint[x].sum()
        if nx < 5:
            continue
        exp = nx * marg
        m = exp > 0
        best = max(best, float(np.sum((joint[x][m] - exp[m]) ** 2 / exp[m])))
    half = n // 2
    halves = contingency_chi2(np.vstack([np.bincount(s[:half], minlength=9),
                                         np.bincount(s[half:], minlength=9)]).astype(np.float64))
    per = []
    for p in (2, 3):
        per.append(contingency_chi2(np.vstack([np.bincount(s[r::p], minlength=9)
                                               for r in range(p)]).astype(np.float64)))
    return np.concatenate([sp, [repeat, mi, best, halves], per])


# --------------------------------------------------------------------------
# reference distribution and consistency value
# --------------------------------------------------------------------------
class Reference:
    def __init__(self, name, n, rng, fit_counts=None, m=M):
        gen = generator(name, fit_counts)
        self.sims = np.array([stats(gen(rng, n)) for _ in range(m)])
        self.mu = self.sims.mean(axis=0)
        cov = np.cov(self.sims, rowvar=False)
        cov = cov + np.eye(cov.shape[0]) * 1e-9 * max(np.trace(cov), 1e-12)
        self.icov = np.linalg.pinv(cov)
        self.sd = np.sqrt(np.maximum(np.diag(cov), 1e-24))
        self.d_sims = self.dist(self.sims)

    def dist(self, x):
        x = np.atleast_2d(x) - self.mu
        return np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", x, self.icov, x), 0.0))

    def pvalue(self, x):
        d = float(self.dist(x)[0])
        return (1 + int(np.sum(self.d_sims >= d))) / (1 + len(self.d_sims)), d

    def zscores(self, x):
        return ((np.asarray(x) - self.mu) / self.sd).tolist()


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def control_label_invariance():
    rng = np.random.default_rng(CONTROL_SEED)
    ok = True
    for _ in range(100):
        s = gen_cb_eng(rng, 570)
        perm = rng.permutation(9)
        ok &= bool(np.allclose(stats(s), stats(perm[s]), atol=1e-12))
    return {"label_invariant": bool(ok)}


def control_size_and_power(n_plant=N_PLANT, m=M):
    """Size (diagonal) and power matrix at N=570. Rows = planted source, columns = reference."""
    rng = np.random.default_rng(CONTROL_SEED + 1)
    refs = {g: Reference(g, 570, rng, m=m) for g in GENERATORS if g != "IID-FIT"}
    matrix = {}
    for row in GENERATORS:
        gen = generator(row, FAED_COUNTS)
        planted = [gen(rng, 570) for _ in range(n_plant)]
        pst = [stats(s) for s in planted]
        rates = {}
        for col in GENERATORS:
            if col == "IID-FIT":
                rej = 0
                for s, st in zip(planted, pst):
                    ref = Reference("IID-FIT", 570, rng, fit_counts=np.bincount(s, minlength=9), m=m)
                    rej += ref.pvalue(st)[0] <= BAR
            else:
                rej = sum(refs[col].pvalue(st)[0] <= BAR for st in pst)
            rates[col] = rej / n_plant
        matrix[row] = rates
    size = {g: matrix[g][g] for g in GENERATORS if g != "IID-FIT"}
    return {"power_matrix": matrix, "size": size,
            "size_ok": bool(all(v <= SIZE_MAX for v in size.values()))}


def self_test():
    res = {"label": control_label_invariance(), "size_power": control_size_and_power()}
    res["all_passed"] = bool(res["label"]["label_invariant"] and res["size_power"]["size_ok"])
    return res


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_fields():
    return {"protocol_sha256": sha256_file(PROTOCOL), "script_sha256": sha256_file(__file__),
            "test_sha256": sha256_file(TEST_PATH), "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
            "corpus_sha256": sha256_file(CORPUS), "seed": SEED, "m": M, "bar_holm": BAR,
            "control_seed": CONTROL_SEED, "n_plant": N_PLANT}


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


def score_stream(s, rng):
    x = stats(s)
    out = {"stats": dict(zip(STAT_NAMES, x.tolist())), "generators": {}}
    for g in GENERATORS:
        ref = Reference(g, len(s), rng, fit_counts=np.bincount(s, minlength=9))
        p, d = ref.pvalue(x)
        out["generators"][g] = {"p": p, "D": d, "D_sim_median": float(np.median(ref.d_sims)),
                                "z": dict(zip(STAT_NAMES, [round(v, 3) for v in ref.zscores(x)]))}
    return out


def run():
    verify_lock()
    rng = np.random.default_rng(SEED)
    result = {"lock_sha256": sha256_file(LOCK_PATH)}
    for name, s in (("FAED", to_idx(FAED)), ("DBBI", to_idx(DBBI))):
        result[name] = score_stream(s, rng)
        print(name, {g: round(v["p"], 4) for g, v in result[name]["generators"].items()}, flush=True)
    ps = [result["FAED"]["generators"][g]["p"] for g in MECHANISMS]
    adj = holm(ps)
    result["gate_faed"] = {g: {"p": p, "holm": a, "verdict": "excluded" if a <= BAR else "consistent"}
                           for g, p, a in zip(MECHANISMS, ps, adj)}
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate_faed"], indent=2))


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
