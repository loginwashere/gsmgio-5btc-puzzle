#!/usr/bin/env python3
"""Resumable exploratory FAED width-19 search over all escape pairs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver
from data import FAED

SCRIPT_DIR=Path(__file__).resolve().parent
REPO_ROOT=SCRIPT_DIR.parents[1]
KEEP=262144
REFINE_KEEP=8192
EXTEND_SEEDS=256
EXTEND_WORKERS=8


def sha256_file(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def faed_hash():return hashlib.sha256(FAED.encode("ascii")).hexdigest()


def pinned_files():
    return {
        "runner":Path(__file__),
        "joint_solver":SCRIPT_DIR/"phase484q_blind_joint_width19_solver.py",
        "base_solver":SCRIPT_DIR/"phase484a_raw_symbol_vic_solver.py",
        "prefix_solver":SCRIPT_DIR/"phase484j_constructive_prefix_beam_probe.py",
        "bidirectional_solver":SCRIPT_DIR/"phase484k_bidirectional_segment_assembly_probe.py",
        "gpu_beam":SCRIPT_DIR/"phase484n_gpu_width19_beam_probe.py",
        "hybrid_scorer":SCRIPT_DIR/"phase484n_hybrid_prefix_scorer.py",
        "board_scorer":SCRIPT_DIR/"phase484o_joint_board_order_ceiling.py",
        "coarse_cuda":SCRIPT_DIR/"phase484q_coarse_board_server.cu",
        "full_cuda":SCRIPT_DIR/"phase484q_full_board_server.cu",
        "invariant_binary":solver.DEFAULT_BINARY,
        "board_binary":solver.ceiling.BOARD_BINARY,
        "coarse_binary":solver.COARSE_BINARY,
        "full_binary":solver.FULL_BINARY,
        "quadgrams":solver.base.QUADGRAM_FILE,
    }


def implementation_hashes():return {name:sha256_file(path) for name,path in pinned_files().items()}


def budgets():
    return {"width":19,"pair_count":36,"shortlist":KEEP,"refine_keep":REFINE_KEEP,"extension_seed_count":EXTEND_SEEDS,"extension_workers":EXTEND_WORKERS,"extension_beam":solver.EXTEND_BEAM,"terminals_per_seed":solver.TERMINALS_PER_SEED,"final_restarts":solver.FINAL_RESTARTS,"final_iterations":solver.FINAL_ITERATIONS}


def pair_score(cell):
    value=cell["top1_final_normalized_score"]
    return value if value is not None and math.isfinite(value) else -math.inf


def rank_cells(cells):
    ranked=sorted(cells,key=lambda cell:(-pair_score(cell),cell["pair_index"]))
    for rank,cell in enumerate(ranked,1):cell["family_rank"]=rank
    return ranked


def compact(result):
    candidates=[]
    for record in result["final_candidates"][:5]:
        candidates.append({key:record[key] for key in ("final_rank","normalized_score","decoded_length","plaintext","order","board","best_restart","quadgram_windows")})
    return {"pair_index":result["pair_index"],"pair":result["pair"],"best_refined_normalized_score":result["best_refined_normalized_score"],"top1_final_normalized_score":result["top1_final_normalized_score"],"terminals_total":result["terminals_total"],"terminals_valid":result["terminals_valid"],"terminals_skipped_invalid_segmentation":result["terminals_skipped_invalid_segmentation"],"top_candidates":candidates,"wall_seconds":sum(result[key] for key in ("shortlist_seconds","gpu_screen_seconds","gpu_refine_seconds","extension_seconds","final_seconds"))}


def new_artifact():
    return {"phase":"484U","status":"exploratory_real_in_progress_nonclosing_if_negative","faed_scored":True,"holdout_gate_completed":False,"faed_ascii_sha256":faed_hash(),"implementation_sha256":implementation_hashes(),"budgets":budgets(),"pairs":[list(pair) for pair in solver.base.ESCAPE_PAIRS],"cells":[]}


def write_artifact(path,artifact):
    temporary=path.with_suffix(path.suffix+".tmp");temporary.write_text(json.dumps(artifact,indent=2)+"\n");temporary.replace(path)


def load_or_create(path):
    expected=new_artifact()
    if not path.exists():return expected
    artifact=json.loads(path.read_text())
    for key in ("phase","faed_scored","holdout_gate_completed","faed_ascii_sha256","implementation_sha256","budgets","pairs"):
        if artifact.get(key)!=expected[key]:raise ValueError(f"resume artifact mismatch: {key}")
    indices=[cell["pair_index"] for cell in artifact["cells"]]
    if len(indices)!=len(set(indices)) or any(not 0<=index<36 for index in indices):raise ValueError("invalid saved pair indices")
    return artifact


def run(output):
    artifact=load_or_create(output)
    if artifact["status"]=="exploratory_real_complete":return artifact
    completed={cell["pair_index"] for cell in artifact["cells"]};began=time.monotonic();prior=artifact.get("wall_seconds_so_far",0.0)
    if not output.exists():write_artifact(output,artifact)
    for pair_index in range(36):
        if pair_index in completed:continue
        result=solver.screen_observed(FAED,pair_index,keep=KEEP,refine_keep=REFINE_KEEP,extend_seed_count=EXTEND_SEEDS,extend_workers=EXTEND_WORKERS)
        artifact["cells"].append(compact(result));artifact["cells_so_far_ranked"]=rank_cells([dict(cell) for cell in artifact["cells"]]);artifact["wall_seconds_so_far"]=prior+time.monotonic()-began;write_artifact(output,artifact)
        print(pair_index,result["pair"],result["top1_final_normalized_score"],result["final_candidates"][0]["plaintext"][:120] if result["final_candidates"] else None,flush=True)
    artifact["cells"]=rank_cells(artifact["cells"]);artifact.pop("cells_so_far_ranked",None);artifact["family_best"]=artifact["cells"][0];artifact["status"]="exploratory_real_complete";artifact["wall_seconds"]=prior+time.monotonic()-began;artifact.pop("wall_seconds_so_far",None);write_artifact(output,artifact);return artifact


def self_test():
    assert len(FAED)==570 and set(FAED)==set("abcdefghi")
    assert faed_hash()=="066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
    assert len(solver.base.ESCAPE_PAIRS)==36 and budgets()["pair_count"]==36
    assert set(implementation_hashes())==set(pinned_files())


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True);group.add_argument("--self-test",action="store_true");group.add_argument("--run",action="store_true");parser.add_argument("--output",type=Path,default=SCRIPT_DIR/"phase484u_exploratory_faed_width19_result.json");args=parser.parse_args()
    if args.self_test:self_test();print("self-test: ok");return 0
    result=run(args.output);best=result["family_best"];print("best",best["pair"],best["top1_final_normalized_score"]);print("plaintext",best["top_candidates"][0]["plaintext"]);return 0


if __name__=="__main__":raise SystemExit(main())
