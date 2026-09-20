#!/usr/bin/env python3
"""Phase 538 -- FAED's six 91-symbol lanes read through DBBI's host masks.

Protocol: doc/Brainstorms/2026-09-20 - Phase 538 FAED Lane Host-Mask
Extraction Protocol.md (written before any real lane was read).

Modes
  --self-test   controls 1-4 (precedent reproduction, extraction exactness,
                gate recovery on planted streams, false-positive context).
                Reads no real FAED lane through a mask.
  --prepare     runs the controls, then writes the execution lock and the GPU
                base list (`_work/phase538/bases.txt`). Refuses to overwrite.
  --run-gate    verifies the whole lock, then scores the real lanes (arm 2).
  --verify-oracle / --classify-weak
                summarize the GPU output for arm 1 (Phase 524 helpers).

The oracle itself is run outside this script (tools/gpu_oracle); no decrypt
function is imported here.
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
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
from phase537_payload_position_function import is_prime, parse_all  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-20 - Phase 538 FAED Lane Host-Mask Extraction Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase538_faed_lane_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase538_faed_lane_gate_result.json"
WORK_DIR = ROOT / "_work" / "phase538"
SYMS = "abcdefghi"
LANE_LEN = 91
N_LANES = 6
SEED = 538
REAL_REPLICATES = 20_000
CONTROL_REPLICATES = 2_000
LEAD_TAIL = 0.0005
KINDS = ("H", "C", "Hb", "Hy")

PHASE48_MASK = [
    2, 3, 5, 7, 11, 12, 14, 18, 20, 24, 25, 31, 32, 34, 40, 44,
    46, 50, 51, 57, 63, 65, 66, 72, 73, 77, 79, 85, 86, 90, 91,
]
PRECEDENT_SELECTED = "ncsyangcahiriasogaleafayanestve"
PRECEDENT_COMPLEMENT = "iaeoumaetorcktsthepvtekeybelntohfandbtterhlndthelsoedfundoli"
PRECEDENT_YELLOW = "anhirialfayastve"
PRECEDENT_BLUE_PLUS_FEFE = "ncsygcaasogean" + "e"


# --------------------------------------------------------------------------
# masks and readers
# --------------------------------------------------------------------------
def build_masks():
    """Both masks over raw 1-based DBBI positions, from the prime-host parses."""
    parses = parse_all(DBBI)
    assert [len(p) for p in parses] == [83, 84], [len(p) for p in parses]
    masks = {}
    for name, toks in zip(("M31", "M30"), parses):
        single, pair, off = [], [], 0
        for pos, tok in enumerate(toks, 1):
            if is_prime(pos):
                raw = [off + i + 1 for i in range(len(tok))]
                (single if len(tok) == 1 else pair).append(raw)
            off += len(tok)
        hosts = sorted(p for h in single + pair for p in h)
        masks[name] = {
            "H": hosts,
            "C": [p for p in range(1, LANE_LEN + 1) if p not in set(hosts)],
            "Hb": sorted(p for h in single for p in h),
            "Hy": sorted(p for h in pair for p in h),
        }
    assert masks["M31"]["H"] == PHASE48_MASK
    assert masks["M30"]["H"] == PHASE48_MASK[:-1]
    return masks


def lanes_of(stream):
    assert len(stream) == LANE_LEN * N_LANES + 24
    return [list(stream[LANE_LEN * j: LANE_LEN * (j + 1)]) for j in range(N_LANES)]


def read(lane, positions):
    return [lane[p - 1] for p in positions]


def candidates(lanes, masks):
    """Ordered {name: element list}; the closed 64-string family."""
    out = {}
    for mname in ("M31", "M30"):
        for kind in KINDS:
            pos = masks[mname][kind]
            for j, lane in enumerate(lanes, 1):
                out[f"{mname}/L{j}/{kind}"] = read(lane, pos)
            out[f"{mname}/pool-lane/{kind}"] = [x for lane in lanes for x in read(lane, pos)]
            out[f"{mname}/pool-pos/{kind}"] = [lane[p - 1] for p in pos for lane in lanes]
    return out


def candidate_strings(stream):
    """Unique base strings in first-occurrence order (symbols joined)."""
    seen, out = set(), []
    for elems in candidates(lanes_of(stream), build_masks()).values():
        s = "".join(elems)
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


# --------------------------------------------------------------------------
# arm 2 gate
# --------------------------------------------------------------------------
def _onehot(lane_arr):
    oh = np.zeros((LANE_LEN, 9), dtype=np.int32)
    oh[np.arange(LANE_LEN), lane_arr] = 1
    return oh


def _top2_share(counts, size):
    return np.sort(counts, axis=-1)[..., -2:].sum(axis=-1) / size


def _mask_index(masks, mname, kind):
    return np.array(masks[mname][kind], dtype=np.int64) - 1


def gate_scores(arr, replicates, seed):
    """arr: (6, 91) int lane symbols. Returns per-statistic cell tables."""
    masks = build_masks()
    rng = np.random.default_rng(seed)
    oh = [_onehot(arr[j]) for j in range(N_LANES)]
    tot = [o.sum(axis=0) for o in oh]  # per-lane symbol totals
    sizes = {m: len(masks[m]["H"]) for m in ("M31", "M30")}

    # ---- S1: top-2 concentration -------------------------------------
    cells1, obs1, null1 = [], [], []
    for mname in ("M31", "M30"):
        k = sizes[mname]
        idx_real = {kd: _mask_index(masks, mname, kd) for kd in ("H", "C")}
        # null subsets: one random k-subset per lane per replicate
        draws = [np.argsort(rng.random((replicates, LANE_LEN)), axis=1)[:, :k] for _ in range(N_LANES)]
        h_cnt_null = [oh[j][draws[j]].sum(axis=1) for j in range(N_LANES)]  # (R, 9)
        for kind in ("H", "C"):
            size = k if kind == "H" else LANE_LEN - k
            real_cnt = [oh[j][idx_real[kind]].sum(axis=0) for j in range(N_LANES)]
            nul_cnt = [h_cnt_null[j] if kind == "H" else tot[j][None, :] - h_cnt_null[j] for j in range(N_LANES)]
            for j in range(N_LANES):
                cells1.append(f"{mname}/L{j+1}/{kind}")
                obs1.append(float(_top2_share(real_cnt[j], size)))
                null1.append(_top2_share(nul_cnt[j], size))
            cells1.append(f"{mname}/pool/{kind}")
            obs1.append(float(_top2_share(sum(real_cnt), size * N_LANES)))
            null1.append(_top2_share(sum(nul_cnt), size * N_LANES))
    s1 = _family(cells1, obs1, np.stack(null1, axis=1))

    # ---- S2: cross-lane column agreement ------------------------------
    g = np.zeros(LANE_LEN, dtype=np.int64)
    for a in range(N_LANES):
        for b in range(a + 1, N_LANES):
            g += (arr[a] == arr[b]).astype(np.int64)
    cells2, obs2, null2 = [], [], []
    total_g = int(g.sum())
    for mname in ("M31", "M30"):
        k = sizes[mname]
        draws = np.argsort(rng.random((replicates, LANE_LEN)), axis=1)[:, :k]
        h_null = g[draws].sum(axis=1)
        for kind in ("H", "C"):
            real = int(g[_mask_index(masks, mname, kind)].sum())
            cells2.append(f"{mname}/{kind}")
            obs2.append(float(real))
            null2.append((h_null if kind == "H" else total_g - h_null).astype(float))
    s2 = _family(cells2, obs2, np.stack(null2, axis=1))
    return {"S1": s1, "S2": s2}


def _family(cells, obs, null):
    """null: (R, ncells). Standardize per cell; family max; add-one tail."""
    obs = np.asarray(obs, dtype=float)
    mean = null.mean(axis=0)
    sd = null.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    z_obs = (obs - mean) / sd
    z_null_max = ((null - mean) / sd).max(axis=1)
    obs_max = float(z_obs.max())
    tail = (1 + int((z_null_max >= obs_max).sum())) / (null.shape[0] + 1)
    top = int(z_obs.argmax())
    return {
        "cells": cells,
        "observed": [float(x) for x in obs],
        "null_mean": [float(x) for x in mean],
        "z": [float(x) for x in z_obs],
        "max_z": obs_max,
        "max_cell": cells[top],
        "tail": tail,
        "lead": bool(tail <= LEAD_TAIL),
    }


def to_array(lanes):
    return np.array([[SYMS.index(c) for c in lane] for lane in lanes], dtype=np.int64)


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def control_precedent():
    masks = build_masks()
    m = masks["M31"]
    ans = VALIDATION_ANSWER
    sel = "".join(read(ans, m["H"])).lower()
    comp = "".join(read(ans, m["C"])).lower()
    yel = "".join(read(ans, m["Hy"])).lower()
    blue = "".join(read(ans, m["Hb"])).lower()
    return {
        "selected": sel == PRECEDENT_SELECTED,
        "complement": comp == PRECEDENT_COMPLEMENT and len(comp) == 60,
        "yellow_rail": yel == PRECEDENT_YELLOW,
        "blue_plus_fefe_multiset": sorted(blue) == sorted(PRECEDENT_BLUE_PLUS_FEFE),
    }


def control_extraction():
    masks = build_masks()
    stream = list(range(570))
    lanes = lanes_of(stream)
    cands = candidates(lanes, masks)
    ok = len(cands) == 64
    for mname in ("M31", "M30"):
        for kind in KINDS:
            pos = masks[mname][kind]
            for j in range(N_LANES):
                ok &= cands[f"{mname}/L{j+1}/{kind}"] == [91 * j + p - 1 for p in pos]
            ok &= cands[f"{mname}/pool-lane/{kind}"] == [91 * j + p - 1 for j in range(N_LANES) for p in pos]
            ok &= cands[f"{mname}/pool-pos/{kind}"] == [91 * j + p - 1 for p in pos for j in range(N_LANES)]
    sizes = {kind: len(masks["M31"][kind]) for kind in KINDS}
    ok &= sizes == {"H": 31, "C": 60, "Hb": 15, "Hy": 16}
    sizes30 = {kind: len(masks["M30"][kind]) for kind in KINDS}
    ok &= sizes30 == {"H": 30, "C": 61, "Hb": 16, "Hy": 14}
    return bool(ok)


def _hist_lane(rng):
    syms = np.array(sorted(FAED))
    idx = np.array([SYMS.index(c) for c in syms])
    return rng.choice(idx, size=(N_LANES, LANE_LEN))


def plant(kind, noise, rng, mask="M31"):
    arr = _hist_lane(rng)
    pos = np.array(build_masks()[mask]["H"]) - 1
    if kind == "pair":  # host positions carry a concentrated pair {g,i}
        for j in range(N_LANES):
            arr[j, pos] = rng.choice([SYMS.index("g"), SYMS.index("i")], size=len(pos))
    else:  # host columns identical across lanes
        col = rng.choice(np.array([SYMS.index(c) for c in FAED]), size=len(pos))
        for j in range(N_LANES):
            arr[j, pos] = col
    if noise:
        flip = rng.random((N_LANES, len(pos))) < noise
        sub = arr[:, pos]
        sub[flip] = rng.integers(0, 9, size=int(flip.sum()))
        arr[:, pos] = sub
    return arr


def control_recovery(trials=20, replicates=CONTROL_REPLICATES):
    rng = np.random.default_rng(SEED + 1)
    out = {}
    for kind, stat in (("pair", "S1"), ("column", "S2")):
        for noise in (0.0, 0.25, 0.5):
            hits = 0
            for t in range(trials):
                arr = plant(kind, noise, rng)
                res = gate_scores(arr, replicates, SEED + 100 * t + int(noise * 100))
                hits += res[stat]["lead"]
            out[f"{kind}/noise{int(noise * 100)}"] = {"statistic": stat, "detected": hits, "trials": trials}
    return out


def control_false_positive(shuffles=100, replicates=CONTROL_REPLICATES):
    rng = np.random.default_rng(SEED + 2)
    leads = {"S1": 0, "S2": 0}
    chars = list(FAED)
    for i in range(shuffles):
        rng.shuffle(chars)
        res = gate_scores(to_array(lanes_of(chars)), replicates, SEED + 10_000 + i)
        for s in leads:
            leads[s] += res[s]["lead"]
    return {"shuffles": shuffles, "lead_counts": leads}


def self_test(full=True):
    checks = {}
    checks["control1_precedent"] = control_precedent()
    checks["control2_extraction"] = control_extraction()
    ok = all(checks["control1_precedent"].values()) and checks["control2_extraction"]
    if full:
        rec = control_recovery()
        checks["control3_recovery"] = rec
        ok &= all(v["detected"] == v["trials"] for k, v in rec.items() if k.endswith("noise0"))
        checks["control4_false_positive"] = control_false_positive()
    return {"ok": bool(ok), "checks": checks}


# --------------------------------------------------------------------------
# lock and run
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_lock_fields():
    masks = build_masks()
    cands = candidate_strings(FAED)
    return {
        "phase": 538,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(__file__),
        "test_sha256": sha256_file(SCRIPT_DIR / "test_phase538_faed_lane_extraction.py"),
        "data_py_sha256": sha256_file(SCRIPT_DIR / "data.py"),
        "phase537_parser_sha256": sha256_file(SCRIPT_DIR / "phase537_payload_position_function.py"),
        "faed_sha256": sha256_text(FAED),
        "dbbi_sha256": sha256_text(DBBI),
        "masks": {m: {k: v for k, v in d.items()} for m, d in masks.items()},
        "candidate_count": len(cands),
        "candidate_list_sha256": sha256_text("\n".join(cands) + "\n"),
        "gate": {
            "seed": SEED,
            "real_replicates": REAL_REPLICATES,
            "control_replicates": CONTROL_REPLICATES,
            "lead_tail": LEAD_TAIL,
        },
    }


def prepare():
    if LOCK_PATH.exists():
        raise SystemExit(f"{LOCK_PATH.name} exists; refusing to overwrite")
    st = self_test(full=True)
    if not st["ok"]:
        print(json.dumps(st, indent=2))
        raise SystemExit("controls failed; no lock written and no real lane read")
    fields = expected_lock_fields()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    cands = candidate_strings(FAED)
    (WORK_DIR / "bases.txt").write_text("\n".join(cands) + "\n", encoding="utf-8")
    fields["controls"] = st["checks"]
    LOCK_PATH.write_text(json.dumps(fields, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"lock": str(LOCK_PATH), "bases": str(WORK_DIR / "bases.txt"), "candidates": len(cands),
            "candidate_list_sha256": fields["candidate_list_sha256"]}


def verify_lock():
    if not LOCK_PATH.exists():
        raise SystemExit("no lock; run --prepare first")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    want = expected_lock_fields()
    bad = [k for k in want if lock.get(k) != want[k]]
    if bad:
        raise SystemExit(f"lock mismatch in: {bad}")
    if not (control_extraction() and all(control_precedent().values())):
        raise SystemExit("controls 1-2 no longer pass")
    rec = lock["controls"]["control3_recovery"]
    if not all(v["detected"] == v["trials"] for k, v in rec.items() if k.endswith("noise0")):
        raise SystemExit("locked control 3 did not pass")
    bases = (WORK_DIR / "bases.txt").read_text(encoding="utf-8")
    if sha256_text(bases) != lock["candidate_list_sha256"]:
        raise SystemExit("bases.txt digest differs from lock")
    return lock


def run_gate():
    lock = verify_lock()
    arr = to_array(lanes_of(FAED))
    res = gate_scores(arr, REAL_REPLICATES, SEED)
    out = {
        "phase": 538,
        "lock_sha256": sha256_file(LOCK_PATH),
        "replicates": REAL_REPLICATES,
        "S1": res["S1"],
        "S2": res["S2"],
        "calibrated_lead": bool(res["S1"]["lead"] or res["S2"]["lead"]),
        "oracle_calls": 0,
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return {k: (out[k] if k in ("calibrated_lead", "oracle_calls") else
                {"max_z": out[k]["max_z"], "max_cell": out[k]["max_cell"], "tail": out[k]["tail"], "lead": out[k]["lead"]})
            for k in ("S1", "S2", "calibrated_lead", "oracle_calls")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--run-gate", action="store_true")
    ap.add_argument("--verify-oracle", action="store_true")
    ap.add_argument("--classify-weak", action="store_true")
    ap.add_argument("--hits", default=str(ROOT / "tools/gpu_oracle/output_local/phase538.hits.jsonl"))
    ap.add_argument("--keyshape", default=str(ROOT / "tools/gpu_oracle/output_local/phase538.keyshape.jsonl"))
    ap.add_argument("--checkpoint", default=str(ROOT / "tools/gpu_oracle/output_local/phase538.checkpoint.jsonl"))
    args = ap.parse_args()
    if args.self_test:
        r = self_test()
        print(json.dumps(r, indent=2))
        return 0 if r["ok"] else 1
    if args.prepare:
        print(json.dumps(prepare(), indent=2))
        return 0
    if args.run_gate:
        print(json.dumps(run_gate(), indent=2))
        return 0
    if args.verify_oracle or args.classify_weak:
        import phase524_slot_grammar_sweep_prep as p524
        if args.classify_weak:
            print(json.dumps(p524.classify_weak(args.hits), indent=2))
        else:
            lock = verify_lock()
            print(json.dumps(p524.verify(args.hits, args.keyshape, args.checkpoint, lock["candidate_count"]), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
