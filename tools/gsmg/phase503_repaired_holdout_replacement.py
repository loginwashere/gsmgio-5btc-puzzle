#!/usr/bin/env python3
"""Replacement holdout cell after Phase-502 fixture 4 proved ineligible."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants
import phase499_unrestricted_width19_holdout as phase499
import phase502_repaired_width19_holdout as phase502

SCRIPT_DIR=Path(__file__).resolve().parent
REPO_ROOT=SCRIPT_DIR.parents[1]
PROTOCOL=REPO_ROOT/'doc/Brainstorms/2026-09-13 - Phase 503 Repaired Holdout Replacement Cell.md'
LOCK_PATH=SCRIPT_DIR/'phase503_execution_lock.json'
PRIOR_ROOT=REPO_ROOT/'_work/phase502/i3_s3'
PRIOR_RESULT=PRIOR_ROOT/'phase502_complete_result.json'
WORK_DIR=REPO_ROOT/'_work/phase503/i5_s3'
FIXTURE_INDEX=5
EARLY=dict(phase502.EARLY_SCHEDULE); BASE=dict(phase502.BASE_SCHEDULE)
BRIDGE=dict(phase502.BRIDGE_SCHEDULE)
DEPENDENCIES=(exact,front,continuation,variants,phase499,phase502)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def chash(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def make_fixture():
    old=phase502.FIXTURE_INDICES
    try:
        phase502.FIXTURE_INDICES=(FIXTURE_INDEX,)
        return phase502.make_variant(FIXTURE_INDEX)
    finally:
        phase502.FIXTURE_INDICES=old

def prior_result():
    if not PRIOR_RESULT.is_file(): raise RuntimeError('Phase-502 fixture-3 result absent')
    r=json.loads(PRIOR_RESULT.read_text())
    if not r.get('top1_exact_order') or r.get('exact_order_final_rank')!=1:
        raise RuntimeError('Phase-502 fixture 3 is not the reviewed pass')
    if r.get('marker_sha256')!=sha(PRIOR_ROOT/'objective_marker.json'):
        raise RuntimeError('Phase-502 fixture-3 marker mismatch')
    return r

def expected_lock_payload():
    phase502.verify_lock(); prior_result(); f=make_fixture()
    return {'phase':503,'status':'execution_lock','combined_fixtures':[3,5],
      'replacement_fixture':5,'pass_rule':'2_of_2_exact_top1',
      'protocol_sha256':sha(PROTOCOL),'script_sha256':sha(__file__),
      'phase502_lock_sha256':sha(phase502.LOCK_PATH),
      'phase502_fixture3_result_sha256':sha(PRIOR_RESULT),
      'fixture5_raw_sha256':f['raw_sha256'],
      'fixture5_plaintext_sha256':hashlib.sha256(f['plaintext'].encode()).hexdigest(),
      'fixture5_edit_fraction':f['edit_fraction'],
      'fixture5_normalized_quadgram':f['normalized_quadgram'],
      'dependencies_sha256':{str(Path(m.__file__).relative_to(REPO_ROOT)):sha(m.__file__) for m in DEPENDENCIES},
      'binaries_sha256':{str(p.relative_to(REPO_ROOT)):sha(p) for p in (variants.UNRESTRICTED_BINARY,front.invariant.DEFAULT_BINARY)},
      'early_schedule_sha256':chash(EARLY),'base_schedule_sha256':chash(BASE),
      'bridge_schedule_sha256':chash(BRIDGE)}

def verify_lock():
    if not LOCK_PATH.is_file(): raise RuntimeError('Phase-503 execution lock absent')
    got=json.loads(LOCK_PATH.read_text()); expected=expected_lock_payload()
    if got!=expected: raise RuntimeError('Phase-503 execution lock mismatch')
    return got

def marker_payload():
    verify_lock(); f=make_fixture()
    return {'phase':503,'status':'holdout_checkpoint_marker','fixture_index':5,
      'fixture_raw_sha256':f['raw_sha256'],
      'fixture_plaintext_sha256':hashlib.sha256(f['plaintext'].encode()).hexdigest(),
      'execution_lock_sha256':sha(LOCK_PATH)}

def ensure_marker():
    p=WORK_DIR/'objective_marker.json'; expected=marker_payload()
    if p.exists() and json.loads(p.read_text())!=expected: raise RuntimeError('Phase-503 marker mismatch')
    if not p.exists(): phase499.atomic_json(p,expected)

def validated_front():
    r,c=WORK_DIR/'result.json',WORK_DIR/'depth7_refined.npz'
    if not r.exists() and not c.exists(): return None
    if not r.exists() or not c.exists(): raise RuntimeError('partial Phase-503 front')
    d=json.loads(r.read_text())
    for k,v in {'fixture_index':5,'split':'holdout','schedule_sha256':front.schedule_sha256(),'checkpoint':str(c)}.items():
        if d.get(k)!=v: raise RuntimeError(f'Phase-503 front wrong {k}')
    return c

def run():
    verify_lock(); output=WORK_DIR/'phase503_complete_result.json'
    if output.exists(): return json.loads(output.read_text())
    ensure_marker(); fixture=make_fixture(); models=exact.train_profile_models()
    of,ot,os,osc=exact.make_fixture,exact.train_profile_models,front.constrained_multistart,continuation.SCHEDULE
    def supply(i=0,split='dev'):
        if i==5 and split=='holdout': return fixture
        raise RuntimeError('unexpected fixture request in Phase 503')
    def unrestricted(paths,blocks,pair,quad,restarts,iterations,binary=variants.UNRESTRICTED_BINARY,seed=front.BOARD_SEED):
        return os(paths,blocks,pair,quad,restarts,iterations,binary=variants.UNRESTRICTED_BINARY,seed=seed)
    exact.make_fixture,exact.train_profile_models=supply,lambda:models; front.constrained_multistart=unrestricted
    try:
        source=validated_front()
        if source is None:
            front.run_front(5,'holdout',WORK_DIR,board_binary=variants.UNRESTRICTED_BINARY); source=validated_front()
        continuation.SCHEDULE=EARLY
        cur=continuation.lane_a_depth8(source,5,'holdout',WORK_DIR)
        cur=continuation.global_depth(cur,9,EARLY['lane_a_depth8_keep'],5,'holdout',WORK_DIR,'depth9')
        continuation.SCHEDULE=BASE
        cur=continuation.global_depth(cur,10,BASE['lane_a_depth8_keep'],5,'holdout',WORK_DIR,'depth10')
        continuation.SCHEDULE=BRIDGE
        cur=continuation.bridge_depth(cur,11,BRIDGE['lane_a_bridge_parent_keep'],BRIDGE['lane_a_bridge_children_per_parent'],BRIDGE['lane_a_bridge_parent_keep']*BRIDGE['lane_a_bridge_children_per_parent'],5,'holdout',WORK_DIR,'depth11_bridge')
        continuation.SCHEDULE=BASE
        for depth in range(12,20):
            keep=BASE['depth13_16_keep'] if depth<=16 else BASE['depth17_19_keep']
            cur=continuation.global_depth(cur,depth,keep,5,'holdout',WORK_DIR,f'depth{depth}')
        solved=continuation.final_resolve(cur,5,'holdout',WORK_DIR)
    finally:
        continuation.SCHEDULE=osc; front.constrained_multistart=os; exact.train_profile_models,exact.make_fixture=ot,of
    prior=prior_result(); passed=bool(solved['top1_exact_order'] and prior['top1_exact_order'])
    result={'phase':503,'status':'replacement_gate_complete','faed_scored':False,
      'combined_fixtures':[3,5],'combined_exact_top1':int(prior['top1_exact_order'])+int(solved['top1_exact_order']),
      'gate_passed':passed,'fixture5_top1_exact_order':solved['top1_exact_order'],
      'fixture5_plaintext_accuracy':solved['top1_plaintext_accuracy'],
      'fixture5_exact_order_final_rank':solved['exact_order_final_rank'],
      'marker_sha256':sha(WORK_DIR/'objective_marker.json'),'final_candidates':solved['final_candidates']}
    phase499.atomic_json(output,result); return result

def self_test():
    f=make_fixture()
    if f['fixture_index']!=5 or f['split']!='holdout' or f['edit_fraction']>0.18: raise AssertionError('replacement invalid')
    if {k for k in BRIDGE if BRIDGE[k]!=BASE[k]}!={'coarse_restarts','coarse_iterations'}: raise AssertionError('schedule drift')
    return {'faed_scored':False,'replacement_fixture':5,'eligible':True}

def main():
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test',action='store_true'); g.add_argument('--verify-lock',action='store_true'); g.add_argument('--run',action='store_true')
    a=p.parse_args(); r=self_test() if a.self_test else verify_lock() if a.verify_lock else run(); print(json.dumps(r,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

