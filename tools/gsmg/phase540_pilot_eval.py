#!/usr/bin/env python3
"""Phase 540 pilot: lock, collect, retro-check, novelty, oracle verification.

Modes
  --lock         hash protocol, prompts, dossiers and scripts before any agent runs.
  --collect      read agent outputs, normalize and deduplicate the main-round
                 candidates, write the GPU base list (no oracle here).
  --retro        check whether each retro-control agent produced its known answer.
  --novelty      share of main-round candidates already covered by Phase 523's
                 tested-material map (SALPH coverage, fast sources).
  --verify-oracle  summarize the GPU output with the Phase 524 helpers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

ROOT = SCRIPT_DIR.parents[1]
WORK = ROOT / "_work" / "phase540_pilot"
OUT = WORK / "out"
LOCK = SCRIPT_DIR / "phase540_pilot_lock.json"
REPORT = SCRIPT_DIR / "phase540_pilot_result.json"
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-20 - Phase 540 Fresh-Context Agent Insight Pilot Protocol.md"
MAIN_AGENTS = ("A1", "A2", "A3", "A4", "A5", "A6")
RETRO_ANSWERS = {
    "R1": "causality",
    "R2": "theflowerblossomsthroughwhatseemstobeaconcretesurface",
}
MAX_LEN = 200


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def lock_fields():
    files = {
        "protocol": PROTOCOL,
        "prompts": SCRIPT_DIR / "phase540_pilot_prompts.json",
        "build_script": SCRIPT_DIR / "phase540_pilot_build.py",
        "eval_script": Path(__file__),
        "dossier_main": WORK / "dossier_main.md",
        "dossier_r1": WORK / "dossier_r1.md",
        "dossier_r2": WORK / "dossier_r2.md",
    }
    return {k: sha(v) for k, v in files.items()}


def do_lock():
    if LOCK.exists():
        raise SystemExit("lock exists; refusing to overwrite")
    LOCK.write_text(json.dumps({"phase": 540, "sha256": lock_fields()}, indent=2, sort_keys=True) + "\n")
    return json.loads(LOCK.read_text())


def read_agent(name):
    path = OUT / f"{name}.jsonl"
    rows, bad = [], 0
    if not path.exists():
        return rows, None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            cand = str(rec["candidate"]).replace("\r", " ").replace("\n", " ").strip()
        except Exception:
            bad += 1
            continue
        rows.append({"candidate": cand, "clue": str(rec.get("clue", "")), "reading": str(rec.get("reading", ""))})
    return rows, bad


def collect():
    report, seen, ordered = {}, set(), []
    for name in MAIN_AGENTS:
        rows, bad = read_agent(name)
        if bad is None:
            report[name] = {"file": False}
            continue
        kept = [r for r in rows if r["candidate"] and len(r["candidate"]) <= MAX_LEN]
        new = 0
        agent_seen = set()
        for r in kept:
            agent_seen.add(r["candidate"])
            if r["candidate"] not in seen:
                seen.add(r["candidate"])
                ordered.append(r["candidate"])
                new += 1
        report[name] = {"lines": len(rows), "non_json": bad, "kept": len(kept),
                        "unique_in_agent": len(agent_seen), "new_after_dedup": new}
    (WORK / "candidates_main.txt").write_text("\n".join(ordered) + "\n", encoding="utf-8")
    report["unique_total"] = len(ordered)
    report["candidates_sha256"] = hashlib.sha256(("\n".join(ordered) + "\n").encode()).hexdigest()
    return report


def retro():
    out = {}
    for name, answer in RETRO_ANSWERS.items():
        rows, bad = read_agent(name)
        if bad is None:
            out[name] = {"file": False}
            continue
        cands = [norm(r["candidate"]) for r in rows]
        exact = [i for i, c in enumerate(cands) if c == answer]
        partial = [rows[i]["candidate"] for i, c in enumerate(cands) if c != answer and (answer in c or (len(c) > 8 and c in answer))]
        out[name] = {"candidates": len(rows), "known_answer_found": bool(exact),
                     "rank_of_first_hit": (exact[0] + 1) if exact else None, "partial_matches": partial[:5]}
    return out


def novelty():
    import phase523_slot_grammar_overlap_audit as p523
    sources = [s for s in p523.COVERAGE_SOURCES if s["name"] not in p523._SLOW_SOURCES]
    tested, _ = p523.build_tested(sources)
    per = {}
    for name in MAIN_AGENTS:
        rows, bad = read_agent(name)
        if bad is None:
            continue
        counts = {"new": 0, "alpha_only_covered": 0, "literal_partially_covered": 0, "all_covered": 0}
        for r in rows:
            if r["candidate"] and len(r["candidate"]) <= MAX_LEN:
                counts[p523.classify(r["candidate"], tested)[0]] += 1
        per[name] = counts
    return per


def verify_oracle(hits, keyshape, checkpoint):
    import phase524_slot_grammar_sweep_prep as p524
    n = len([l for l in (WORK / "candidates_main.txt").read_text().splitlines() if l.strip()])
    return p524.verify(hits, keyshape, checkpoint, n)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for flag in ("--lock", "--collect", "--retro", "--novelty", "--verify-oracle"):
        ap.add_argument(flag, action="store_true")
    ap.add_argument("--hits", default=str(ROOT / "tools/gpu_oracle/output_local/phase540.hits.jsonl"))
    ap.add_argument("--keyshape", default=str(ROOT / "tools/gpu_oracle/output_local/phase540.keyshape.jsonl"))
    ap.add_argument("--checkpoint", default=str(ROOT / "tools/gpu_oracle/output_local/phase540.checkpoint.jsonl"))
    a = ap.parse_args()
    if a.lock:
        print(json.dumps(do_lock(), indent=2))
    elif a.collect:
        print(json.dumps(collect(), indent=2))
    elif a.retro:
        print(json.dumps(retro(), indent=2))
    elif a.novelty:
        print(json.dumps(novelty(), indent=2))
    elif a.verify_oracle:
        print(json.dumps(verify_oracle(a.hits, a.keyshape, a.checkpoint), indent=2))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
