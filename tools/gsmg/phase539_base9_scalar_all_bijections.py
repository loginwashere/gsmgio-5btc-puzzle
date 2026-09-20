#!/usr/bin/env python3
"""Phase 539 -- DBBI and its payload as base-9 scalars under every digit bijection.

Protocol: doc/Brainstorms/2026-09-20 - Phase 539 Base-9 Scalar All-Bijections
Protocol.md (written before any real target was scanned).

Modes
  --self-test   controls 1-3 (validator, planted recovery over all 12 cells,
                Phase 318 digit arithmetic). Scans no real target.
  --prepare     runs the controls, then writes the execution lock.
  --run         verifies the whole lock, then scans the real targets.

Exact bar only: a scalar whose compressed or uncompressed hash160 is one of
the eleven target hash160s. No statistical arm, no oracle. Any match is written
to a mode-0600 file under _work/phase539/ and never printed or committed.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import os
import random
import re
import sys
from pathlib import Path

import coincurve

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI  # noqa: E402
from phase538_faed_lane_extraction import build_masks  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-20 - Phase 539 Base-9 Scalar All-Bijections Protocol.md"
KNOWN_TARGETS_RS = ROOT / "tools/gpu_oracle/src/checker/known_targets.rs"
LOCK_PATH = SCRIPT_DIR / "phase539_base9_scalar_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase539_base9_scalar_result.json"
WORK_DIR = ROOT / "_work" / "phase539"
SYMS = "abcdefghi"
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PRIZE_ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
HALVING_ADDRESS = "17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa"
DIRECTIONS = ("forward", "reversed")
CONVENTIONS = ("D0", "D1")
PERM_COUNT = 362_880
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
G_UNCOMPRESSED_HASH160 = "91b24bf9f5288532960ac687abb035127b1d28a5"
G_COMPRESSED_HASH160 = "751e76e8199196d454941c45d1b3a323f1433bd6"


# --------------------------------------------------------------------------
# targets
# --------------------------------------------------------------------------
def hash160(data):
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).digest()


def b58decode_payload(address):
    num = 0
    for ch in address:
        num = num * 58 + B58.index(ch)
    raw = num.to_bytes(25, "big")
    assert hashlib.sha256(hashlib.sha256(raw[:21]).digest()).digest()[:4] == raw[21:]
    return raw[1:21]


def _rust_constants():
    src = KNOWN_TARGETS_RS.read_text(encoding="utf-8")
    pub = re.search(r'PRIZE_PUBKEY_HEX: &str = "([0-9a-f]+)"', src).group(1)
    body = src.split("pub const KNOWN_TARGETS")[1]
    hashes = [
        bytes(int(x, 16) for x in re.findall(r"0x([0-9a-f]{2})", blk))
        for blk in re.findall(r"hash160: \[(.*?)\]", body, re.S)
    ]
    return pub, hashes


def derive_targets():
    """{hash160 bytes: label}: eleven target hashes, derived independently."""
    pub_hex, rust_neighbors = _rust_constants()
    P = coincurve.PublicKey(bytes.fromhex(pub_hex))
    G = coincurve.PublicKey.from_secret((1).to_bytes(32, "big"))
    negG = coincurve.PublicKey.from_secret((N - 1).to_bytes(32, "big"))
    inv2 = ((N + 1) // 2).to_bytes(32, "big")
    points = {
        "P+G": coincurve.PublicKey.combine_keys([P, G]),
        "P-G": coincurve.PublicKey.combine_keys([P, negG]),
        "P/2": P.multiply(inv2),
        "2P": coincurve.PublicKey.combine_keys([P, P]),
    }
    targets, neighbor_hashes = {}, []
    for name, pt in points.items():
        for enc, compressed in (("compressed", True), ("uncompressed", False)):
            h = hash160(pt.format(compressed=compressed))
            targets[h] = f"{name}/{enc}"
            neighbor_hashes.append(h)
    targets[hash160(P.format(compressed=False))] = "prize/uncompressed"
    targets[hash160(P.format(compressed=True))] = "prize/compressed"
    targets[b58decode_payload(HALVING_ADDRESS)] = "halving"
    assert len(targets) == 11
    return targets, neighbor_hashes, rust_neighbors, b58decode_payload(PRIZE_ADDRESS), hash160(P.format(compressed=False))


def target_strings():
    masks = build_masks()
    return {
        "P83": "".join(DBBI[p - 1] for p in masks["M31"]["C"]),
        "P84": "".join(DBBI[p - 1] for p in masks["M30"]["C"]),
        "DBBI": DBBI,
    }


# --------------------------------------------------------------------------
# scan
# --------------------------------------------------------------------------
def weights(symbols, direction):
    seq = symbols[::-1] if direction == "reversed" else symbols
    L = len(seq)
    w = [0] * 9
    for i, ch in enumerate(seq):
        w[SYMS.index(ch)] += 9 ** (L - 1 - i)
    return w, (9 ** L - 1) // 8


def scalar(w, r, conv, sigma):
    v = sum(s * wc for s, wc in zip(sigma, w))
    return (v + r if conv == "D1" else v) % N


def _work(args):
    w, r, conv, x, y, target_hashes = args
    rest = [d for d in range(9) if d not in (x, y)]
    base = x * w[0] + y * w[1]
    checked, found = 0, []
    sha, rip = hashlib.sha256, hashlib.new
    for p in itertools.permutations(rest):
        v = base
        for c in range(7):
            v += p[c] * w[c + 2]
        k = ((v + r) if conv == "D1" else v) % N
        checked += 1
        if k == 0:
            continue
        pk = coincurve.PublicKey.from_secret(k.to_bytes(32, "big"))
        for enc, compressed in (("compressed", True), ("uncompressed", False)):
            h = rip("ripemd160", sha(pk.format(compressed=compressed)).digest()).digest()
            if h in target_hashes:
                found.append((k, (x, y) + p, enc, h))
    return checked, found


def scan(symbols, direction, conv, targets, pairs=None, workers=None):
    """Scan all 9! bijections (or only tasks whose first two digits are in `pairs`).

    Returns (checked, matches); matches carry the scalar and are never printed."""
    w, r = weights(symbols, direction)
    hashes = frozenset(targets)
    pair_list = pairs if pairs is not None else [(x, y) for x in range(9) for y in range(9) if x != y]
    tasks = [(w, r, conv, x, y, hashes) for x, y in pair_list]
    workers = workers or min(os.cpu_count() or 1, 16)
    ctx = mp.get_context("fork")
    checked, matches = 0, []
    with ctx.Pool(workers) as pool:
        for c, f in pool.imap_unordered(_work, tasks):
            checked += c
            matches.extend(f)
    return checked, matches


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def control_validator():
    targets, derived, rust, prize_addr_hash, prize_unc_hash = derive_targets()
    g = coincurve.PublicKey.from_secret((1).to_bytes(32, "big"))
    return {
        "generator_hashes": hash160(g.format(compressed=False)).hex() == G_UNCOMPRESSED_HASH160
        and hash160(g.format(compressed=True)).hex() == G_COMPRESSED_HASH160,
        "prize_pubkey_matches_address": prize_addr_hash == prize_unc_hash,
        "neighbors_match_phase331_constants": sorted(derived) == sorted(rust) and len(rust) == 8,
        "eleven_distinct_targets": len(targets) == 11,
    }


def control_digit_arithmetic():
    import dbbi_base9_bignum_audit as p318
    ok = True
    for direction in DIRECTIONS:
        w, r = weights(DBBI, direction)
        ident = tuple(range(9))
        ok &= scalar(w, r, "D0", ident) == p318.to_base9_int(DBBI, 0, direction == "reversed") % N
        ok &= scalar(w, r, "D1", ident) == p318.to_base9_int(DBBI, 1, direction == "reversed") % N
    return bool(ok)


def control_recovery():
    strings = target_strings()
    out, ok = {}, True
    for ti, (tname, s) in enumerate(strings.items()):
        for di, direction in enumerate(DIRECTIONS):
            for ci, conv in enumerate(CONVENTIONS):
                rng = random.Random(539_000 + 100 * ti + 10 * di + ci)
                sigma = tuple(rng.sample(range(9), 9))
                w, r = weights(s, direction)
                k = scalar(w, r, conv, sigma)
                pk = coincurve.PublicKey.from_secret(k.to_bytes(32, "big"))
                synthetic = {hash160(pk.format(compressed=True)): "planted/c", hash160(pk.format(compressed=False)): "planted/u"}
                checked, matches = scan(s, direction, conv, synthetic)
                got = {m[1] for m in matches}
                cell_ok = checked == PERM_COUNT and got == {sigma} and {m[2] for m in matches} == {"compressed", "uncompressed"}
                out[f"{tname}/{direction}/{conv}"] = cell_ok
                ok &= cell_ok
    return out, bool(ok)


def self_test():
    checks = {"control1_validator": control_validator(), "control3_digit_arithmetic": control_digit_arithmetic()}
    rec, rec_ok = control_recovery()
    checks["control2_planted_recovery"] = rec
    ok = all(checks["control1_validator"].values()) and checks["control3_digit_arithmetic"] and rec_ok
    return {"ok": bool(ok), "checks": checks}


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_lock_fields():
    targets = derive_targets()[0]
    strings = target_strings()
    return {
        "phase": 539,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(__file__),
        "test_sha256": sha256_file(SCRIPT_DIR / "test_phase539_base9_scalar_all_bijections.py"),
        "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
        "phase537_parser_sha256": sha256_file(SCRIPT_DIR / "phase537_payload_position_function.py"),
        "phase538_masks_sha256": sha256_file(SCRIPT_DIR / "phase538_faed_lane_extraction.py"),
        "phase318_script_sha256": sha256_file(SCRIPT_DIR / "dbbi_base9_bignum_audit.py"),
        "known_targets_rs_sha256": sha256_file(KNOWN_TARGETS_RS),
        "target_string_sha256": {k: sha256_text(v) for k, v in strings.items()},
        "target_string_lengths": {k: len(v) for k, v in strings.items()},
        "target_hash160": sorted([h.hex(), label] for h, label in targets.items()),
        "candidate_scalars": len(strings) * len(DIRECTIONS) * len(CONVENTIONS) * PERM_COUNT,
    }


def prepare():
    if LOCK_PATH.exists():
        raise SystemExit(f"{LOCK_PATH.name} exists; refusing to overwrite")
    st = self_test()
    if not st["ok"]:
        print(json.dumps(st, indent=2))
        raise SystemExit("controls failed; no lock written and no real target scanned")
    fields = expected_lock_fields()
    fields["controls"] = st["checks"]
    LOCK_PATH.write_text(json.dumps(fields, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"lock": str(LOCK_PATH), "candidate_scalars": fields["candidate_scalars"]}


def verify_lock():
    if not LOCK_PATH.exists():
        raise SystemExit("no lock; run --prepare first")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    want = expected_lock_fields()
    bad = [k for k in want if lock.get(k) != want[k]]
    if bad:
        raise SystemExit(f"lock mismatch in: {bad}")
    if not all(control_validator().values()) or not control_digit_arithmetic():
        raise SystemExit("controls 1 and 3 no longer pass")
    if not all(lock["controls"]["control2_planted_recovery"].values()):
        raise SystemExit("locked planted recovery did not pass")
    return lock


def run():
    verify_lock()
    targets = derive_targets()[0]
    cells, total, all_matches = {}, 0, []
    for tname, s in target_strings().items():
        for direction in DIRECTIONS:
            for conv in CONVENTIONS:
                checked, matches = scan(s, direction, conv, targets)
                assert checked == PERM_COUNT
                cells[f"{tname}/{direction}/{conv}"] = {"checked": checked, "matches": len(matches)}
                total += checked
                all_matches += [(tname, direction, conv, *m) for m in matches]
    out = {
        "phase": 539,
        "lock_sha256": sha256_file(LOCK_PATH),
        "cells": cells,
        "scalars_checked": total,
        "exact_hits": len(all_matches),
        "oracle_calls": 0,
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    if all_matches:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        path = WORK_DIR / "matches.jsonl"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            for tname, direction, conv, k, sigma, enc, h in all_matches:
                fh.write(json.dumps({"target": tname, "direction": direction, "convention": conv,
                                     "digits": "".join(map(str, sigma)), "encoding": enc,
                                     "hash160": h.hex(), "scalar_hex": f"{k:064x}"}) + "\n")
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
        out = run()
        print(json.dumps({k: v for k, v in out.items() if k != "cells"}, indent=2))
        if out["exact_hits"]:
            print(f"EXACT HIT: candidate key(s) written to {WORK_DIR / 'matches.jsonl'} (mode 0600). Do not commit; tell the user.")
            return 2
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
