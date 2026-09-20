#!/usr/bin/env python3
"""Phase 537 -- is DBBI's non-host payload an arithmetic function of its position?

Protocol: doc/Brainstorms/2026-09-20 - Phase 537 Prime Scaffold Payload
Position Function Protocol.md (written before any real-payload result).
Zero oracle calls: no decrypt function, password, or blob is imported.

Pipeline
  1. Parse DBBI with an independent prime-host solver (logical position p
     prime -> token 'b' or 'be'; other positions -> one symbol a..i).
  2. Payload = tokens at non-prime logical positions. Coordinates per payload
     symbol: logical index n, raw 1-based offset r, payload ordinal k.
  3. Closed family of functions g, two variants (g, g mod 9), class vectors
     with at most nine classes.
  4. Exact bar: equality pattern of a class vector equals the payload's.
  5. Calibrated lead: per-cell purity standardized on histogram-preserving
     shuffles; family maximum compared with the same statistic on shuffles.
  6. Planted-recovery controls run before the real payload is scored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-20 - Phase 537 Prime Scaffold Payload Position Function Protocol.md"
RESULT = SCRIPT_DIR / "phase537_payload_position_result.json"
SYMS = "abcdefghi"
NULL_SHUFFLES = 5000
POWER_SHUFFLES = 1000
LEAD_TAIL = 0.001


# --------------------------------------------------------------------------
# number theory (values stay below 200)
# --------------------------------------------------------------------------
LIMIT = 400
_sieve = [True] * (LIMIT + 1)
_sieve[0] = _sieve[1] = False
for _i in range(2, int(LIMIT ** 0.5) + 1):
    if _sieve[_i]:
        for _j in range(_i * _i, LIMIT + 1, _i):
            _sieve[_j] = False
PRIMES = [i for i, v in enumerate(_sieve) if v]


def is_prime(n):
    return 0 <= n <= LIMIT and _sieve[n]


def factorize(n):
    out = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def d_count(n):
    r = 1
    for e in factorize(n).values():
        r *= e + 1
    return r


def sigma(n):
    return sum(i for i in range(1, n + 1) if n % i == 0)


def phi(n):
    r = n
    for p in factorize(n):
        r = r // p * (p - 1)
    return r


def bigomega(n):
    return sum(factorize(n).values())


def omega(n):
    return len(factorize(n))


def spf(n):
    f = factorize(n)
    return min(f) if f else 1


def gpf(n):
    f = factorize(n)
    return max(f) if f else 1


def mobius(n):
    f = factorize(n)
    if any(e > 1 for e in f.values()):
        return 0
    return -1 if len(f) % 2 else 1


def pi_count(n):
    return sum(1 for p in PRIMES if p <= n)


def prev_prime_lt(n):
    c = [p for p in PRIMES if p < n]
    return c[-1] if c else 0


def next_prime_gt(n):
    return next(p for p in PRIMES if p > n)


def back_gap(n):
    c = [p for p in PRIMES if p <= n]
    return n - (c[-1] if c else 0)


def forward_gap(n):
    return next(p for p in PRIMES if p >= n) - n


def span(n):
    return next_prime_gt(n) - prev_prime_lt(n)


FUNCTIONS = {
    "identity": lambda n: n,
    "square": lambda n: n * n,
    "cube": lambda n: n ** 3,
    "triangular": lambda n: n * (n + 1) // 2,
    "divisor_count": d_count,
    "divisor_sum": sigma,
    "totient": phi,
    "bigomega": bigomega,
    "omega": omega,
    "spf": spf,
    "gpf": gpf,
    "mobius": mobius,
    "pi": pi_count,
    "back_gap": back_gap,
    "forward_gap": forward_gap,
    "prime_span": span,
    "popcount": lambda n: bin(n).count("1"),
    "bit_length": lambda n: n.bit_length(),
    "digit_sum10": lambda n: sum(int(c) for c in str(n)),
}
GEOMETRY = {  # raw coordinate only, on r-1
    "geom_div13": lambda n: (n - 1) // 13,
    "geom_mod13": lambda n: (n - 1) % 13,
    "geom_div7": lambda n: (n - 1) // 7,
    "geom_mod7": lambda n: (n - 1) % 7,
}


# --------------------------------------------------------------------------
# independent parser and payload extraction
# --------------------------------------------------------------------------
def parse_all(raw):
    out = []

    def go(off, pos, toks):
        if off == len(raw):
            out.append(tuple(toks))
            return
        if is_prime(pos):
            if raw[off] == "b":
                toks.append("b")
                go(off + 1, pos + 1, toks)
                toks.pop()
                if raw.startswith("be", off):
                    toks.append("be")
                    go(off + 2, pos + 1, toks)
                    toks.pop()
            return
        toks.append(raw[off])
        go(off + 1, pos + 1, toks)
        toks.pop()

    go(0, 1, [])
    return sorted(out, key=len)


def payload_targets(raw=DBBI):
    targets = []
    for tokens in parse_all(raw):
        offset = 1
        symbols, n_list, r_list, k_list = [], [], [], []
        k = 0
        for n, tok in enumerate(tokens, 1):
            if not is_prime(n):
                k += 1
                symbols.append(tok)
                n_list.append(n)
                r_list.append(offset)
                k_list.append(k)
            offset += len(tok)
        targets.append({"logical_length": len(tokens), "symbols": "".join(symbols),
                        "coords": {"n": n_list, "r": r_list, "k": k_list}})
    return targets


# --------------------------------------------------------------------------
# cells
# --------------------------------------------------------------------------
def pattern(seq):
    labels = {}
    return tuple(labels.setdefault(x, len(labels)) for x in seq)


def build_cells(coords):
    """coords: dict n/r/k -> list of ints. Returns list of cells (deduplicated
    by class-vector pattern) and the count of collapsed duplicates."""
    cells, seen, dup = [], {}, 0
    for cname, values in coords.items():
        funcs = dict(FUNCTIONS)
        if cname == "r":
            funcs.update(GEOMETRY)
        for fname, g in funcs.items():
            gv = [g(v) for v in values]
            variants = []
            if len(set(gv)) <= 9:
                variants.append(("raw", pattern(gv)))
            variants.append(("mod9", pattern([x % 9 for x in gv])))
            for vname, pat in variants:
                label = f"{cname}:{fname}:{vname}"
                if pat in seen:
                    cells[seen[pat]]["aliases"].append(label)
                    dup += 1
                    continue
                seen[pat] = len(cells)
                cells.append({"label": label, "classes": pat, "n_classes": max(pat) + 1,
                              "aliases": [], "coord": cname, "function": fname, "variant": vname})
    return cells, dup


def class_matrix(cells, length):
    """(cells) list of C_i x N indicator matrices."""
    mats = []
    for cell in cells:
        c = cell["n_classes"]
        m = np.zeros((c, length), dtype=np.float32)
        for pos, cls in enumerate(cell["classes"]):
            m[cls, pos] = 1.0
        mats.append(m)
    return mats


def onehot(sym_array):
    """(S, N) int array of symbol ids -> (N, S*9) float32."""
    s, n = sym_array.shape
    oh = np.zeros((n, s, 9), dtype=np.float32)
    for k in range(9):
        oh[:, :, k] = (sym_array.T == k)
    return oh.reshape(n, s * 9)


def purity_matrix(mats, sym_array):
    """purities[cell, shuffle] = sum over classes of max symbol count / N."""
    s, n = sym_array.shape
    oh = onehot(sym_array)
    out = np.empty((len(mats), s), dtype=np.float64)
    for i, m in enumerate(mats):
        counts = (m @ oh).reshape(m.shape[0], s, 9)
        out[i] = counts.max(axis=2).sum(axis=0) / n
    return out


def real_purity(mats, sym_array_1):
    return purity_matrix(mats, sym_array_1[None, :])[:, 0]


def sym_ids(symbols):
    return np.array([SYMS.index(c) for c in symbols], dtype=np.int64)


def null_shuffles(ids, count, seed):
    rng = np.random.default_rng(seed)
    out = np.empty((count, len(ids)), dtype=np.int64)
    for i in range(count):
        out[i] = rng.permutation(ids)
    return out


def score_target(symbols, cells, mats, shuffles, seed):
    ids = sym_ids(symbols)
    pat = pattern(ids.tolist())
    exact = [c["label"] for c in cells if c["classes"] == pat and c["n_classes"] == 9]
    sh = null_shuffles(ids, shuffles, seed)
    null_p = purity_matrix(mats, sh)
    mean = null_p.mean(axis=1)
    sd = null_p.std(axis=1)
    sd = np.where(sd < 1e-12, 1e-12, sd)
    real = real_purity(mats, ids)
    z_real = (real - mean) / sd
    z_null = (null_p - mean[:, None]) / sd[:, None]
    fam_real = float(z_real.max())
    fam_null = z_null.max(axis=0)
    tail = (1 + int((fam_null >= fam_real).sum())) / (shuffles + 1)
    top = np.argsort(-z_real)[:5]
    return {"exact_cells": exact, "family_max_z": fam_real, "family_tail_add_one": tail,
            "top_cells": [{"label": cells[i]["label"], "z": float(z_real[i]), "purity": float(real[i])} for i in top],
            "z_real": z_real, "real_purity": real}


def held_out_final_symbol(target84, cells84, cell_label):
    """Fit the class->majority symbol map on positions before the last and
    predict the last symbol. Returns (predicted, actual) or None."""
    cell = next(c for c in cells84 if c["label"] == cell_label)
    syms = target84["symbols"]
    fit_classes, fit_syms = cell["classes"][:-1], syms[:-1]
    last_class = cell["classes"][-1]
    votes = {}
    for cl, s in zip(fit_classes, fit_syms):
        votes.setdefault(cl, {}).setdefault(s, 0)
        votes[cl][s] += 1
    if last_class not in votes:
        return None
    predicted = max(sorted(votes[last_class]), key=lambda s: votes[last_class][s])
    return predicted, syms[-1]


# --------------------------------------------------------------------------
# planted-recovery controls
# --------------------------------------------------------------------------
def planted_payload(cell, rng, noise):
    perm = list(SYMS)
    rng.shuffle(perm)
    symbols = [perm[c] for c in cell["classes"]]
    n = len(symbols)
    for i in rng.sample(range(n), int(round(noise * n))):
        symbols[i] = rng.choice(SYMS)
    return "".join(symbols)


def pick_planting_cells(cells):
    """Eight nine-class cells, taken round-robin over coordinates n, r, k in
    (variant, function) order, chosen deterministically before any real
    result exists. (A first version of this picker returned five cells; it was
    corrected to the protocol's eight before the real payload was scored.)"""
    pools = {coord: sorted((c for c in cells if c["coord"] == coord and c["n_classes"] == 9),
                           key=lambda c: (c["variant"], c["function"])) for coord in ("n", "r", "k")}
    chosen, index = [], {coord: 0 for coord in pools}
    order = ["n", "r", "k"]
    while len(chosen) < 8:
        progressed = False
        for coord in order:
            if len(chosen) == 8:
                break
            if index[coord] < len(pools[coord]):
                chosen.append(pools[coord][index[coord]])
                index[coord] += 1
                progressed = True
        if not progressed:
            break
    return chosen


def planted_controls(targets):
    report = {"exact_recovery": [], "power": []}
    for target in targets:
        cells, _ = build_cells(target["coords"])
        rng = random.Random(537000 + target["logical_length"])
        for cell in pick_planting_cells(cells):
            ok = 0
            for _ in range(20):
                payload = planted_payload(cell, rng, 0.0)
                pat = pattern(payload)
                hit = [c["label"] for c in cells if c["classes"] == pat and c["n_classes"] == 9]
                ok += cell["label"] in hit
            report["exact_recovery"].append({"logical_length": target["logical_length"],
                                             "cell": cell["label"], "recovered": ok, "trials": 20})
    target = targets[0]  # power trials use the shorter (83-token) coordinates
    cells, _ = build_cells(target["coords"])
    mats = class_matrix(cells, len(target["symbols"]))
    rng = random.Random(537083)
    for cell in pick_planting_cells(cells):
        for noise in (0.10, 0.25):
            detected = 0
            for t in range(20):
                payload = planted_payload(cell, rng, noise)
                res = score_target(payload, cells, mats, POWER_SHUFFLES, 5370000 + t)
                detected += res["family_tail_add_one"] <= LEAD_TAIL
            report["power"].append({"cell": cell["label"], "noise": noise, "detected": detected, "trials": 20})
    report["gate_passed"] = all(r["recovered"] == r["trials"] for r in report["exact_recovery"])
    return report


# --------------------------------------------------------------------------
def self_test():
    checks = {}
    checks["pi_83_is_23"] = pi_count(83) == 23
    checks["number_theory"] = (d_count(12) == 6 and sigma(12) == 28 and phi(12) == 4 and bigomega(12) == 3
                               and omega(12) == 2 and spf(1) == 1 and gpf(1) == 1 and mobius(30) == -1
                               and mobius(12) == 0 and back_gap(1) == 1 and span(1) == 2 and back_gap(7) == 0
                               and forward_gap(8) == 3 and span(8) == 4)
    parses = parse_all(DBBI)
    checks["two_parses"] = [len(p) for p in parses] == [83, 84]
    targets = payload_targets()
    checks["payload_lengths"] = [len(t["symbols"]) for t in targets] == [60, 61]
    checks["all_nine_symbols"] = all(set(t["symbols"]) == set(SYMS) for t in targets)
    for t in targets:
        checks[f"coords_consistent_{t['logical_length']}"] = (
            len(t["coords"]["n"]) == len(t["coords"]["r"]) == len(t["coords"]["k"]) == len(t["symbols"]))
        checks[f"raw_offsets_index_dbbi_{t['logical_length']}"] = all(
            DBBI[r - 1] == s for r, s in zip(t["coords"]["r"], t["symbols"]))
    try:  # cross-check against Phase 525's parser when it is importable
        from phase525_dbbi_selection_a_reconstruction import enumerate_complete_parses
        checks["matches_phase525_parser"] = [tuple(p) for p in enumerate_complete_parses(DBBI)] == parses
    except Exception as exc:  # pragma: no cover
        checks["matches_phase525_parser"] = f"skipped: {type(exc).__name__}"
    # a literal planted case scores as exact on a tiny synthetic target
    cells, _ = build_cells({"n": list(range(1, 61)), "r": list(range(1, 61)), "k": list(range(1, 61))})
    cell = next(c for c in cells if c["coord"] == "n" and c["function"] == "identity" and c["variant"] == "mod9")
    payload = planted_payload(cell, random.Random(1), 0.0)
    checks["planted_exact_synthetic"] = cell["label"] in [c["label"] for c in cells
                                                          if c["classes"] == pattern(payload) and c["n_classes"] == 9]
    real_cells = [build_cells(t["coords"])[0] for t in targets]
    checks["eight_planting_cells"] = all(
        len(pick_planting_cells(rc)) == 8 and len({c["label"] for c in pick_planting_cells(rc)}) == 8
        for rc in real_cells)
    checks["no_oracle_imported"] = not any(n in globals() for n in ("aes_try_open", "BLOBS", "passphrase_hits"))
    return {"ok": all(v is True or (isinstance(v, str) and v.startswith("skipped")) for v in checks.values()),
            "checks": checks}


def run():
    st = self_test()
    if not st["ok"]:
        raise SystemExit(f"self-test failed: {st['checks']}")
    targets = payload_targets()
    started = {}
    controls = planted_controls(targets)
    result = {
        "phase": 537,
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dbbi_sha256": hashlib.sha256(DBBI.encode()).hexdigest(),
        "self_test": st,
        "planted_controls": controls,
        "oracle_calls": 0,
    }
    if not controls["gate_passed"]:
        result["real_payload_scored"] = False
        RESULT.write_text(json.dumps(result, indent=1) + "\n")
        print("planted-recovery gate FAILED; real payload not scored")
        return 1
    result["real_payload_scored"] = True
    parses = []
    for target in targets:
        cells, dup = build_cells(target["coords"])
        mats = class_matrix(cells, len(target["symbols"]))
        res = score_target(target["symbols"], cells, mats, NULL_SHUFFLES, 5370000 + target["logical_length"])
        entry = {"logical_length": target["logical_length"], "payload": target["symbols"],
                 "cells": len(cells), "collapsed_duplicates": dup,
                 "exact_cells": res["exact_cells"], "family_max_z": res["family_max_z"],
                 "family_tail_add_one": res["family_tail_add_one"], "top_cells": res["top_cells"]}
        # context only: exact cells on shuffled payloads
        ids = sym_ids(target["symbols"])
        sh = null_shuffles(ids, 2000, 5379000 + target["logical_length"])
        exact_shuffles = 0
        cell_patterns = {c["classes"] for c in cells if c["n_classes"] == 9}
        for row in sh:
            exact_shuffles += pattern(row.tolist()) in cell_patterns
        entry["shuffled_payloads_exact_in_some_cell"] = exact_shuffles
        if target["logical_length"] == 84:
            entry["held_out_final_e"] = {}
            for top in res["top_cells"][:3]:
                entry["held_out_final_e"][top["label"]] = held_out_final_symbol(target, cells, top["label"])
        entry["lead"] = bool(res["family_tail_add_one"] <= LEAD_TAIL)
        parses.append(entry)
    result["targets"] = parses
    result["any_exact"] = any(p["exact_cells"] for p in parses)
    result["any_lead"] = any(p["lead"] for p in parses)
    RESULT.write_text(json.dumps(result, indent=1) + "\n")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        r = self_test()
        print(json.dumps(r, indent=1))
        return 0 if r["ok"] else 1
    if args.run:
        return run()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
