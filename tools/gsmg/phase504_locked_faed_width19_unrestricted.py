#!/usr/bin/env python3
"""Locked real FAED run using the Phase-503-qualified unrestricted schedule."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase484n_hybrid_prefix_scorer as invariant
import phase484q_blind_joint_width19_solver as joint
import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants
import phase499_unrestricted_width19_holdout as phase499
import phase503_repaired_holdout_replacement as phase503

SCRIPT_DIR=Path(__file__).resolve().parent
REPO_ROOT=SCRIPT_DIR.parents[1]
PROTOCOL=REPO_ROOT/'doc/Brainstorms/2026-09-13 - Phase 504 Locked FAED Width19 Unrestricted Run.md'
LOCK=SCRIPT_DIR/'phase504_execution_lock.json'
WORK_DIR=REPO_ROOT/'_work/phase504/real_gi_w19_unrestricted'
PHASE503_RESULT=REPO_ROOT/'_work/phase503/i5_s3/phase503_complete_result.json'
FAED_SHA256='066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2'
PAIR=('g','i'); WIDTH,ROWS=19,30; SENTINEL=504019
EARLY=dict(phase503.EARLY); BASE=dict(phase503.BASE); BRIDGE=dict(phase503.BRIDGE)
SOURCE_MODULES=(base,invariant,joint,exact,front,continuation,variants,phase499,phase503)
BINARY_PATHS=(Path(invariant.DEFAULT_BINARY),Path(variants.UNRESTRICTED_BINARY),Path(joint.FULL_BINARY))

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def chash(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def atomic(path,value): phase499.atomic_json(Path(path),value)

def input_checks():
    digest=hashlib.sha256(FAED.encode('ascii')).hexdigest()
    if digest!=FAED_SHA256 or len(FAED)!=WIDTH*ROWS: raise AssertionError('FAED identity changed')
    tokens=base.segment_raw(FAED,PAIR)
    if tokens is None or len(tokens)!=436: raise AssertionError('FAED segmentation changed')
    return {'faed_ascii_sha256':digest,'raw_length':len(FAED),
      'observed_token_length':len(tokens),'observed_single_count':sum(len(x)==1 for x in tokens),
      'raw_counts':dict(sorted(collections.Counter(FAED).items())),
      'pair':list(PAIR),'width':WIDTH,'rows':ROWS,'direction':'model_b_columnar_raw_digits'}

def real_fixture():
    return {'fixture_index':SENTINEL,'width':WIDTH,'pair':list(PAIR),
      'board_mode':'unknown_real_unrestricted','split':'dev','observed':FAED,'raw':FAED,
      'order':list(range(WIDTH)),'plaintext':'?'*436}

def qualified_result():
    phase503.verify_lock()
    if not PHASE503_RESULT.is_file(): raise RuntimeError('Phase-503 result absent')
    r=json.loads(PHASE503_RESULT.read_text())
    if not r.get('gate_passed') or r.get('combined_exact_top1')!=2:
        raise RuntimeError('Phase-503 gate is not the reviewed pass')
    return r

def lock_payload():
    qualified_result(); sources={}
    for p in (Path(__file__),PROTOCOL,SCRIPT_DIR/'data.py',base.CORPUS_FILE,base.QUADGRAM_FILE):
        sources[str(Path(p).relative_to(REPO_ROOT))]=sha(p)
    for m in SOURCE_MODULES: sources[str(Path(m.__file__).relative_to(REPO_ROOT))]=sha(m.__file__)
    return {'phase':504,'status':'real_execution_lock','input':input_checks(),
      'sentinel_fixture_index':SENTINEL,'phase503_lock_sha256':sha(phase503.LOCK_PATH),
      'phase503_result_sha256':sha(PHASE503_RESULT),'sources_sha256':sources,
      'binaries_sha256':{str(p.relative_to(REPO_ROOT)):sha(p) for p in BINARY_PATHS},
      'early_schedule_sha256':chash(EARLY),'base_schedule_sha256':chash(BASE),
      'bridge_schedule_sha256':chash(BRIDGE),'board_seed':front.BOARD_SEED,
      'run_count':1,'checkpoint_policy':'atomic_npz_plus_json_per_stage',
      'decision_rule':'manual_readability_review_of_every_valid_final_candidate'}

def verify_lock():
    if not LOCK.is_file(): raise RuntimeError('Phase-504 execution lock absent')
    got=json.loads(LOCK.read_text())
    if got!=lock_payload(): raise RuntimeError('Phase-504 execution lock mismatch')
    return got

def sanitize(work_dir):
    for path in (Path(work_dir)/'continuation').glob('*.json'):
        r=json.loads(path.read_text()); r['status']='locked_real_unrestricted_checkpoint'
        r['faed_scored']=True; r['holdout_consumed']=False; r['sentinel_diagnostics_are_evidential']=False
        for box in (r,r.get('before_selection',{}),r.get('after_selection',{})):
            if isinstance(box,dict):
                for k in list(box):
                    if k.startswith('true_') or k.startswith('best_true'): box.pop(k)
        if path.name=='final_resolve.json':
            for c in r.get('final_candidates',[]): c.pop('is_exact_order',None); c.pop('plaintext_accuracy',None)
            for k in ('exact_order_final_rank','top1_exact_order','top1_plaintext_accuracy'): r.pop(k,None)
        atomic(path,r)

def validate_front():
    pop,raw,mark=WORK_DIR/'depth7_refined.npz',WORK_DIR/'result.json',WORK_DIR/'real_front_checkpoint.json'
    if not pop.exists() and not raw.exists() and not mark.exists(): return None
    if not pop.is_file() or not raw.is_file() or not mark.is_file(): raise RuntimeError('partial real front')
    r=json.loads(mark.read_text()); expected={'phase':504,'stage':'front_depth7_refined','faed_scored':True,
      'execution_lock_sha256':sha(LOCK),'population_sha256':sha(pop),'front_record_sha256':sha(raw),
      'front_schedule_sha256':front.schedule_sha256()}
    if r!=expected: raise RuntimeError('real front marker mismatch')
    continuation.load_population(pop,min_depth=7,max_depth=7); return pop

def mark_front():
    pop,raw=WORK_DIR/'depth7_refined.npz',WORK_DIR/'result.json'; r=json.loads(raw.read_text())
    r.update(status='locked_real_unrestricted_front',faed_scored=True,holdout_consumed=False,
             sentinel_diagnostics_are_evidential=False)
    for section in ('depth6_board','depth7_coarse','depth7_refine'):
        for box in (r.get(section,{}).get('before_selection',{}),r.get(section,{}).get('after_selection',{})):
            for k in list(box):
                if k.startswith('true_') or k.startswith('best_true'): box.pop(k)
    atomic(raw,r); atomic(WORK_DIR/'real_front_checkpoint.json',{'phase':504,'stage':'front_depth7_refined',
      'faed_scored':True,'execution_lock_sha256':sha(LOCK),'population_sha256':sha(pop),
      'front_record_sha256':sha(raw),'front_schedule_sha256':front.schedule_sha256()})

def run():
    verify_lock(); result_path=WORK_DIR/'phase504_real_result.json'
    if result_path.exists(): raise FileExistsError('refusing to overwrite real result')
    WORK_DIR.mkdir(parents=True,exist_ok=True); models=exact.train_profile_models()
    of,ot,os,osc,oc=exact.make_fixture,exact.train_profile_models,front.constrained_multistart,continuation.SCHEDULE,continuation.commit_stage
    calls=[]
    def supply(i=0,split='dev'):
        if i==SENTINEL and split=='dev': calls.append((i,split)); return real_fixture()
        raise RuntimeError('unexpected fixture request after real adapter installation')
    def unrestricted(paths,blocks,pair,quad,restarts,iterations,binary=variants.UNRESTRICTED_BINARY,seed=front.BOARD_SEED):
        return os(paths,blocks,pair,quad,restarts,iterations,binary=variants.UNRESTRICTED_BINARY,seed=seed)
    def real_commit(*args,**kwargs):
        out=oc(*args,**kwargs); sanitize(Path(args[0])); return out
    exact.make_fixture,exact.train_profile_models=supply,lambda:models
    front.constrained_multistart=unrestricted; continuation.commit_stage=real_commit
    try:
        source=validate_front()
        if source is None:
            front.run_front(SENTINEL,'dev',WORK_DIR,board_binary=variants.UNRESTRICTED_BINARY); mark_front(); source=validate_front()
        continuation.SCHEDULE=EARLY
        cur=continuation.lane_a_depth8(source,SENTINEL,'dev',WORK_DIR)
        cur=continuation.global_depth(cur,9,EARLY['lane_a_depth8_keep'],SENTINEL,'dev',WORK_DIR,'depth9')
        continuation.SCHEDULE=BASE
        cur=continuation.global_depth(cur,10,BASE['lane_a_depth8_keep'],SENTINEL,'dev',WORK_DIR,'depth10')
        continuation.SCHEDULE=BRIDGE
        cur=continuation.bridge_depth(cur,11,BRIDGE['lane_a_bridge_parent_keep'],BRIDGE['lane_a_bridge_children_per_parent'],BRIDGE['lane_a_bridge_parent_keep']*BRIDGE['lane_a_bridge_children_per_parent'],SENTINEL,'dev',WORK_DIR,'depth11_bridge')
        continuation.SCHEDULE=BASE
        for depth in range(12,20):
            keep=BASE['depth13_16_keep'] if depth<=16 else BASE['depth17_19_keep']
            cur=continuation.global_depth(cur,depth,keep,SENTINEL,'dev',WORK_DIR,f'depth{depth}')
        continuation.final_resolve(cur,SENTINEL,'dev',WORK_DIR); sanitize(WORK_DIR)
    finally:
        continuation.SCHEDULE=osc; continuation.commit_stage=oc; front.constrained_multistart=os
        exact.train_profile_models,exact.make_fixture=ot,of
    final=json.loads((WORK_DIR/'continuation/final_resolve.json').read_text()); candidates=final.get('final_candidates',[])
    result={'phase':504,'status':'real_faed_width19_unrestricted_complete','faed_scored':True,
      'input':input_checks(),'execution_lock_sha256':sha(LOCK),'fixture_api_calls':len(calls),
      'sentinel_diagnostics_are_evidential':False,'terminal_candidates':final.get('terminal_candidates',[]),
      'skipped_terminals':final.get('skipped_terminals',[]),'final_candidates':candidates,
      'top1_normalized_score':candidates[0]['normalized_score'] if candidates else None,
      'top1_plaintext':candidates[0]['plaintext'] if candidates else None,
      'disposition':'requires_manual_readability_review'}
    atomic(result_path,result); return result

def self_test():
    c=input_checks(); qualified_result()
    if {k for k in BRIDGE if BRIDGE[k]!=BASE[k]}!={'coarse_restarts','coarse_iterations'}: raise AssertionError('schedule drift')
    if real_fixture()['observed']!=FAED or real_fixture()['plaintext']!='?'*436: raise AssertionError('adapter drift')
    return {**c,'qualified':True,'checkpointed':True}

def main():
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(required=True)
    for x in ('self-test','verify-lock','run'): g.add_argument('--'+x,action='store_true')
    a=p.parse_args(); r=self_test() if a.self_test else verify_lock() if a.verify_lock else run(); print(json.dumps(r,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

