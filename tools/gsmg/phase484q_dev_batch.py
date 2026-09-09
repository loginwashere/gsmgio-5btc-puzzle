#!/usr/bin/env python3
"""Fixed fresh-development batch for the Phase 484Q width-19 solver."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import phase484q_blind_joint_width19_solver as solver

SCRIPT_DIR=Path(__file__).resolve().parent
FIXTURE_INDICES=tuple(range(40,50))
BOARD_MODES=("vic_profile","broad_random")

def shortlist_probe(mode,index):
    fixture=solver.base.make_fixture(solver.WIDTH,solver.learned.PAIR_INDEX,index,
        seed=solver.learned.SEED,board_mode=mode,split="dev")
    began=time.monotonic();beam=solver.build_depth8_shortlist(fixture,keep=solver.SHORTLIST);elapsed=time.monotonic()-began
    truth=solver.prefix.order_to_sequence(fixture["order"]);genuine=solver.bidi.true_windows(truth,solver.DEPTH)
    ranks=[rank for rank,(_,path) in enumerate(beam,1) if path in genuine]
    return {"board_mode":mode,"fixture_index":index,"shortlist_size":len(beam),
            "true_segments_retained":len(ranks),
            "best_true_shortlist_rank":min(ranks) if ranks else None,
            "shortlist_seconds":elapsed}

def summarize(cells):
    summary={}
    for mode in (*BOARD_MODES,"all"):
        selected=cells if mode=="all" else [c for c in cells if c["board_mode"]==mode]
        retained=[c for c in selected if c["true_segments_retained"]]
        completed=[c for c in retained if "full_result" in c]
        summary[mode]={"fixtures":len(selected),"shortlist_retained":len(retained),
            "shortlist_retention_rate":len(retained)/len(selected) if selected else None,
            "conditional_full_runs":len(completed),
            "conditional_exact_order_top1":sum(c["full_result"]["top1_exact_order"] for c in completed),
            "conditional_exact_order_top1_rate":sum(c["full_result"]["top1_exact_order"] for c in completed)/len(completed) if completed else None,
            "unconditional_exact_order_top1":sum(c.get("full_result",{}).get("top1_exact_order",False) for c in selected),
            "unconditional_exact_order_top1_rate":sum(c.get("full_result",{}).get("top1_exact_order",False) for c in selected)/len(selected) if selected else None}
    return summary

def run(output):
    cells=[];began=time.monotonic()
    result={"phase":"484Q","status":"development_generalization_batch_in_progress_not_frozen",
            "faed_scored":False,"holdout_consumed":False,
            "fixture_indices":list(FIXTURE_INDICES),"board_modes":list(BOARD_MODES),
            "policy":"full pipeline is run only when truth-based evaluation confirms that a genuine depth-8 window survived; this condition is for development power accounting, not a deployable selector",
            "cells":cells,"summary":summarize(cells)}
    for mode in BOARD_MODES:
        for index in FIXTURE_INDICES:
            cell=shortlist_probe(mode,index);cells.append(cell)
            if cell["true_segments_retained"]:
                cell["full_result"]=solver.screen_fixture(mode,index)
            result["summary"]=summarize(cells);result["wall_seconds_so_far"]=time.monotonic()-began
            output.write_text(json.dumps(result,indent=2)+"\n")
            print(mode,index,"retained",cell["true_segments_retained"],
                  "top1",cell.get("full_result",{}).get("top1_exact_order"),flush=True)
    result["status"]="development_generalization_batch_complete_not_frozen"
    result["wall_seconds"]=time.monotonic()-began;result.pop("wall_seconds_so_far",None)
    result["summary"]=summarize(cells);output.write_text(json.dumps(result,indent=2)+"\n")
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--run",action="store_true");p.add_argument("--output",type=Path,default=SCRIPT_DIR/"phase484q_dev_batch_result.json");a=p.parse_args()
    if not a.run:p.error("use --run")
    result=run(a.output);print(json.dumps(result["summary"],indent=2));print("wrote",a.output);return 0
if __name__=="__main__":raise SystemExit(main())
