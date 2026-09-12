#!/usr/bin/env python3
"""Blind width-19 joint solver: invariant shortlist plus GPU board screen.

Development only: this module never imports FAED and never uses holdout data.
"""
from __future__ import annotations
import argparse,concurrent.futures,itertools,json,struct,subprocess,time
from pathlib import Path
import numpy as np
import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_gpu_width19_beam_probe as gpu_beam
import phase484o_joint_board_order_ceiling as ceiling
import phase484p_partial_board_recovery_probe as partial
from phase484n_hybrid_prefix_scorer import canonical_blocks,DEFAULT_BINARY
SCRIPT_DIR=Path(__file__).resolve().parent
COARSE_BINARY=SCRIPT_DIR.parents[1]/"_work/phase484q/coarse_board_server"
FULL_BINARY=SCRIPT_DIR.parents[1]/"_work/phase484q/full_board_server"
PERSISTENT_BINARY=SCRIPT_DIR.parents[1]/"_work/phase484w/persistent_board_server"
WIDTH,DEPTH,SHORTLIST,ITERATIONS,RESTARTS=19,8,16384,2000,8
REFINE_KEEP,REFINE_RESTARTS,REFINE_ITERATIONS=64,4,10000
EXTEND_SEEDS,EXTEND_BEAM,TERMINALS_PER_SEED=8,4096,8
FINAL_RESTARTS,FINAL_ITERATIONS=4,10000
T0,T1,SEED=partial.T0,partial.T1,partial.SEED

def shortlist_capacity(depth,keep,final_keep=None):
    return final_keep if final_keep is not None and depth==DEPTH else keep

def build_depth8_shortlist(fixture,invariant_binary=DEFAULT_BINARY,keep=SHORTLIST,models=None,final_keep=None):
    if models is None:models=prefix.train_models(WIDTH)
    blocks=prefix.blocks_from_observed(fixture);pair=tuple(fixture["pair"]);paths=list(itertools.permutations(range(WIDTH),prefix.START_DEPTH))
    for depth in range(prefix.START_DEPTH,DEPTH+1):
        if depth>prefix.START_DEPTH:paths=gpu_beam.expand_bidirectional(beam,WIDTH)
        scores=gpu_beam.score_paths(invariant_binary,blocks,pair,models[depth],paths);beam=gpu_beam.select_diverse_arrays(paths,scores,WIDTH,shortlist_capacity(depth,keep,final_keep))
    return beam

def gpu_coarse_screen(binary,blocks,pair,quad,paths,iterations=ITERATIONS,seed=SEED,t0=T0,t1=T1):
    paths=np.asarray(paths,dtype=np.uint8)
    if paths.ndim!=2 or not 4<=paths.shape[1]<=WIDTH:raise ValueError("paths must be an N x depth array")
    if len(paths)==0 or np.any(paths>=WIDTH):raise ValueError("paths must be nonempty and within width 19")
    process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    payload=b"".join([b"P484QG1\0",canonical_blocks(blocks,pair),np.asarray(quad,dtype="<f8").tobytes(),struct.pack("<IIIQdd",len(paths),paths.shape[1],iterations,seed,t0,t1),np.ascontiguousarray(paths).tobytes()])
    stdout,stderr=process.communicate(payload)
    if process.returncode:raise RuntimeError(f"coarse GPU server exited {process.returncode}: {stderr.decode('utf-8','replace')}")
    sb,wb=len(paths)*8,len(paths)*4;expected=sb+wb+len(paths)*25
    if len(stdout)!=expected:raise RuntimeError(f"coarse GPU server returned {len(stdout)} bytes, expected {expected}")
    scores=np.frombuffer(stdout[:sb],dtype="<f8").copy();windows=np.frombuffer(stdout[sb:sb+wb],dtype="<i4").copy();boards=np.frombuffer(stdout[sb+wb:],dtype=np.uint8).copy().reshape(len(paths),25)
    return scores,windows,boards

def cpu_recompute(blocks,pair,quad,path,board):
    rows=partial.token_rows(blocks,pair,path);windows=partial.row_windows(rows);total=partial.row_score(np.asarray(board,dtype=np.int64),rows,quad);return total/max(1,windows),windows

def complete_token_slots(blocks,pair,order,strict=True):
    raw="".join(blocks[column][row] for row in range(30) for column in order);segmented=base.segment_raw(raw,pair)
    if segmented is None:
        if strict:raise ValueError("complete order did not segment")
        return None
    code_to_slot={code:i for i,code in enumerate(base.slot_codes(pair))}
    return np.asarray([code_to_slot[code] for code in segmented],dtype=np.int64)

def gpu_full_screen(binary,token_rows,quad,iterations,seed):
    lengths=np.asarray([len(row) for row in token_rows],dtype="<u2");tokens=np.zeros((len(token_rows),570),dtype=np.uint8)
    for i,row in enumerate(token_rows):tokens[i,:len(row)]=row
    process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);payload=b"".join([b"P484QF1\0",struct.pack("<IIQdd",len(token_rows),iterations,seed,T0,T1),lengths.tobytes(),tokens.tobytes(),np.asarray(quad,dtype="<f8").tobytes()]);stdout,stderr=process.communicate(payload)
    if process.returncode:raise RuntimeError(f"full GPU server exited {process.returncode}: {stderr.decode('utf-8','replace')}")
    sb=len(token_rows)*8
    if len(stdout)!=sb+len(token_rows)*25:raise RuntimeError("wrong full GPU response size")
    return np.frombuffer(stdout[:sb],dtype="<f8").copy(),np.frombuffer(stdout[sb:],dtype=np.uint8).copy().reshape(len(token_rows),25)

def gpu_full_multistart(binary,token_rows,quad,restarts,iterations,seed=SEED):
    scores=np.full(len(token_rows),-np.inf);boards=None;which=np.zeros(len(token_rows),dtype=np.int64)
    for restart in range(restarts):
        current,current_boards=gpu_full_screen(binary,token_rows,quad,iterations,base.derive_seed(seed,restart));improved=current>scores
        if boards is None:boards=current_boards.copy()
        scores[improved]=current[improved];boards[improved]=current_boards[improved];which[improved]=restart
    return scores,boards,which

def resolve_terminals(blocks,pair,quad,terminals,restarts=FINAL_RESTARTS,iterations=FINAL_ITERATIONS,full_binary=FULL_BINARY):
    valid,skipped=[],[]
    for record in terminals:
        rows=complete_token_slots(blocks,pair,record["order"],strict=False)
        if rows is None:skipped.append(record)
        else:valid.append((record,rows))
    if not valid:return [],skipped
    terminals_valid=[r for r,_ in valid];token_rows=[rows for _,rows in valid]
    scores,boards,best_restarts=gpu_full_multistart(full_binary,token_rows,quad,restarts,iterations);order=np.lexsort((np.arange(len(scores)),-scores));ranked=[]
    for rank,i in enumerate(order,1):
        slots=token_rows[i];plaintext="".join(base.LETTER_ALPHABET[value] for value in boards[i][slots]);ranked.append({"final_rank":rank,"extension_rank":terminals_valid[i]["extension_rank"],"normalized_score":float(scores[i]),"decoded_length":len(plaintext),"plaintext":plaintext,"order":terminals_valid[i]["order"],"board":boards[i].tolist(),"best_restart":int(best_restarts[i]),"quadgram_windows":len(slots)-3})
    return ranked,skipped

def fragment_seed(seed,path):
    value=base.derive_seed(seed,len(path),0)
    for index,column in enumerate(path):value=base.derive_seed(value,int(column)+1,index+1)
    return value

def initial_board(seed,path):return np.asarray(base.PCG32(fragment_seed(seed,path)).permutation(25),dtype=np.uint8)

def gpu_multistart_screen(binary,blocks,pair,quad,paths,restarts=RESTARTS,iterations=ITERATIONS):
    best_scores=np.full(len(paths),-np.inf);best_windows=None;best_boards=None;best_restarts=np.zeros(len(paths),dtype=np.int64)
    for restart in range(restarts):
        restart_seed=base.derive_seed(SEED,restart)
        scores,windows,boards=gpu_coarse_screen(binary,blocks,pair,quad,paths,iterations,seed=restart_seed)
        if best_windows is None:best_windows=windows.copy();best_boards=boards.copy()
        elif not np.array_equal(windows,best_windows):raise AssertionError("window counts changed across restarts")
        improved=scores>best_scores;best_scores[improved]=scores[improved];best_boards[improved]=boards[improved];best_restarts[improved]=restart
    return best_scores,best_windows,best_boards,best_restarts

def extend_seed(blocks,pair,quad,record,board_binary=ceiling.BOARD_BINARY,beam_width=EXTEND_BEAM):
    beam=[(record["normalized_score"],tuple(record["path"]))];diagnostics=[]
    with ceiling.BoardScorer(board_binary,blocks,pair,bytes(record["board"]),quad) as scorer:
        for depth in range(DEPTH+1,WIDTH+1):
            paths=gpu_beam.expand_bidirectional(beam,WIDTH);scores=scorer.score(paths);beam=gpu_beam.select_diverse_arrays(paths,scores,WIDTH,beam_width);diagnostics.append({"depth":depth,"generated":len(paths),"retained":len(beam)})
    return beam,diagnostics

def _extend_chunk(args):
    blocks,pair,quad,records,board_binary,beam_width=args
    return [(record["rank"],*extend_seed(blocks,pair,quad,record,board_binary,beam_width)) for record in records]

def extend_population(blocks,pair,quad,refined,seed_count=EXTEND_SEEDS,beam_width=EXTEND_BEAM,terminals_per_seed=TERMINALS_PER_SEED,board_binary=ceiling.BOARD_BINARY,workers=1):
    selected=refined[:seed_count]
    if workers<1:raise ValueError("extension workers must be positive")
    if workers==1 or len(selected)<2:
        extended=_extend_chunk((blocks,pair,quad,selected,board_binary,beam_width))
    else:
        worker_count=min(workers,len(selected));chunks=[selected[i::worker_count] for i in range(worker_count)]
        tasks=[(blocks,pair,quad,chunk,board_binary,beam_width) for chunk in chunks]
        with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as pool:
            extended=[item for chunk in pool.map(_extend_chunk,tasks) for item in chunk]
        extended.sort(key=lambda item:item[0])
    terminal={};seed_diagnostics=[]
    records_by_rank={record["rank"]:record for record in selected}
    for rank,beam,diagnostics in extended:
        record=records_by_rank[rank]
        seed_diagnostics.append({"refined_rank":record["rank"],"shortlist_index":record["shortlist_index"],"depths":diagnostics})
        for score,path in beam[:terminals_per_seed]:
            old=terminal.get(path)
            candidate={"extension_score":float(score),"order":list(path),"source_refined_rank":record["rank"],"source_shortlist_index":record["shortlist_index"]}
            if old is None or score>old["extension_score"]:terminal[path]=candidate
    ranked=sorted(terminal.values(),key=lambda r:(-r["extension_score"],r["order"]))
    for rank,record in enumerate(ranked,1):record["extension_rank"]=rank
    return ranked,seed_diagnostics

def run_extension_backend(blocks,pair,quad,refined,seed_count=EXTEND_SEEDS,beam_width=EXTEND_BEAM,terminals_per_seed=TERMINALS_PER_SEED,workers=1,backend="legacy",board_binary=ceiling.BOARD_BINARY,persistent_binary=PERSISTENT_BINARY):
    if backend=="legacy":
        return extend_population(blocks,pair,quad,refined,seed_count=seed_count,beam_width=beam_width,terminals_per_seed=terminals_per_seed,board_binary=board_binary,workers=workers)
    if backend=="persistent":
        import phase484w_persistent_extension as persistent
        return persistent.extend_population(blocks,pair,quad,refined,seed_count=seed_count,workers=workers,binary=persistent_binary,beam_width=beam_width,terminals_per_seed=terminals_per_seed)
    raise ValueError(f"unknown extension backend: {backend}")

def screen_observed(observed,pair_index,keep=SHORTLIST,iterations=ITERATIONS,restarts=RESTARTS,refine_keep=REFINE_KEEP,refine_restarts=REFINE_RESTARTS,refine_iterations=REFINE_ITERATIONS,invariant_binary=DEFAULT_BINARY,coarse_binary=COARSE_BINARY,extend_seed_count=EXTEND_SEEDS,extend_beam=EXTEND_BEAM,terminals_per_seed=TERMINALS_PER_SEED,final_restarts=FINAL_RESTARTS,final_iterations=FINAL_ITERATIONS,extend_workers=1,extension_backend="legacy",persistent_binary=PERSISTENT_BINARY,shortlist_models=None,shortlist_final_keep=None):
    if len(observed)!=570:raise ValueError("observed width-19 stream must contain 570 symbols")
    if set(observed)-set("abcdefghi"):raise ValueError("observed stream contains symbols outside a-i")
    if not 0<=pair_index<len(base.ESCAPE_PAIRS):raise ValueError("pair index out of range")
    pair=base.ESCAPE_PAIRS[pair_index];fixture={"observed":observed,"width":WIDTH,"pair":list(pair)}
    blocks=prefix.blocks_from_observed(fixture);quad,_=base.load_language_model()
    began=time.monotonic();beam=build_depth8_shortlist(fixture,invariant_binary,keep,models=shortlist_models,final_keep=shortlist_final_keep);paths=[p for _,p in beam];shortlist_seconds=time.monotonic()-began
    began=time.monotonic();scores,windows,boards,best_restarts=gpu_multistart_screen(coarse_binary,blocks,pair,quad,paths,restarts,iterations);screen_seconds=time.monotonic()-began
    order=np.lexsort((np.arange(len(scores)),-scores));refine_indices=order[:min(refine_keep,len(order))];refine_paths=[paths[i] for i in refine_indices]
    began=time.monotonic();rs,rw,rb,rr=gpu_multistart_screen(coarse_binary,blocks,pair,quad,refine_paths,refine_restarts,refine_iterations);refine_seconds=time.monotonic()-began
    refine_order=np.lexsort((np.arange(len(rs)),-rs));ranks=np.empty(len(scores),dtype=np.int64);ranks[order]=np.arange(1,len(scores)+1);refined=[]
    for rank,j in enumerate(refine_order,1):
        original=int(refine_indices[j]);refined.append({"rank":rank,"coarse_rank":int(ranks[original]),"shortlist_index":original,"normalized_score":float(rs[j]),"best_restart":int(rr[j]),"path":list(paths[original]),"board":rb[j].tolist(),"quadgram_windows":int(rw[j])})
    began=time.monotonic();terminals,extension_diagnostics=run_extension_backend(blocks,pair,quad,refined,seed_count=extend_seed_count,beam_width=extend_beam,terminals_per_seed=terminals_per_seed,workers=extend_workers,backend=extension_backend,persistent_binary=persistent_binary);extension_seconds=time.monotonic()-began
    began=time.monotonic();final,skipped=resolve_terminals(blocks,pair,quad,terminals,restarts=final_restarts,iterations=final_iterations);final_seconds=time.monotonic()-began
    return {"phase":"484U","status":"exploratory_real_cell_complete","pair_index":pair_index,"pair":list(pair),"shortlist_size":len(paths),"restarts_per_fragment":restarts,"iterations_per_restart":iterations,"refine_keep":len(refine_paths),"refine_restarts":refine_restarts,"refine_iterations":refine_iterations,"extension_seed_count":min(extend_seed_count,len(refined)),"extension_workers":extend_workers,"extension_beam":extend_beam,"terminals_per_seed":terminals_per_seed,"final_restarts":final_restarts,"final_iterations":final_iterations,"shortlist_seconds":shortlist_seconds,"gpu_screen_seconds":screen_seconds,"gpu_refine_seconds":refine_seconds,"extension_seconds":extension_seconds,"final_seconds":final_seconds,"best_refined_normalized_score":float(rs[refine_order[0]]) if len(refine_order) else None,"top1_final_normalized_score":final[0]["normalized_score"] if final else None,"terminals_total":len(terminals),"terminals_valid":len(terminals)-len(skipped),"terminals_skipped_invalid_segmentation":len(skipped),"final_candidates":final,"refined_population":refined,"terminal_orders":terminals,"skipped_terminals":skipped,"extension_diagnostics":extension_diagnostics}

def screen_fixture(mode="vic_profile",fixture_index=23,keep=SHORTLIST,iterations=ITERATIONS,restarts=RESTARTS,refine_keep=REFINE_KEEP,refine_restarts=REFINE_RESTARTS,refine_iterations=REFINE_ITERATIONS,invariant_binary=DEFAULT_BINARY,coarse_binary=COARSE_BINARY,extend_seed_count=EXTEND_SEEDS,extend_beam=EXTEND_BEAM,terminals_per_seed=TERMINALS_PER_SEED,final_restarts=FINAL_RESTARTS,final_iterations=FINAL_ITERATIONS,hypothesis_pair_index=None,true_pair_index=learned.PAIR_INDEX,split="dev",extend_workers=1,extension_backend="legacy",persistent_binary=PERSISTENT_BINARY,fixture_override=None,shortlist_models=None,shortlist_final_keep=None):
    if fixture_override is None:
        fixture=base.make_fixture(WIDTH,true_pair_index,fixture_index,seed=learned.SEED,board_mode=mode,split=split)
    else:
        fixture=dict(fixture_override);base.verify_fixture(fixture)
        if fixture["width"]!=WIDTH:raise ValueError("fixture override must have width 19")
        mode=fixture["board_mode"];fixture_index=fixture["fixture_index"];split=fixture["split"]
        true_pair_index=base.ESCAPE_PAIRS.index(tuple(fixture["pair"]))
    true_pair=tuple(fixture["pair"])
    if hypothesis_pair_index is None:hypothesis_pair_index=true_pair_index
    if not 0<=hypothesis_pair_index<len(base.ESCAPE_PAIRS):raise ValueError("hypothesis pair index out of range")
    pair=base.ESCAPE_PAIRS[hypothesis_pair_index]
    hypothesis_fixture=dict(fixture);hypothesis_fixture["pair"]=list(pair)
    blocks=prefix.blocks_from_observed(fixture);truth=prefix.order_to_sequence(fixture["order"]);truth_windows=bidi.true_windows(truth,DEPTH)
    began=time.monotonic();beam=build_depth8_shortlist(hypothesis_fixture,invariant_binary,keep,models=shortlist_models,final_keep=shortlist_final_keep);paths=[p for _,p in beam];shortlist_seconds=time.monotonic()-began
    truth_indices=[i for i,p in enumerate(paths) if p in truth_windows];quad,_=base.load_language_model()
    began=time.monotonic();scores,windows,boards,best_restarts=gpu_multistart_screen(coarse_binary,blocks,pair,quad,paths,restarts,iterations);screen_seconds=time.monotonic()-began
    truth_board=np.frombuffer(ceiling.planted_board(fixture),dtype=np.uint8) if pair==true_pair else None
    board_accuracy=lambda board:float(np.mean(board==truth_board)) if truth_board is not None else None
    order=np.lexsort((np.arange(len(scores)),-scores));ranks=np.empty(len(scores),dtype=np.int64);ranks[order]=np.arange(1,len(scores)+1)
    true_records=[{"shortlist_index":i,"coarse_rank":int(ranks[i]),"normalized_score":float(scores[i]),"board_accuracy":board_accuracy(boards[i]),"best_restart":int(best_restarts[i]),"path":list(paths[i])} for i in truth_indices]
    refine_indices=order[:min(refine_keep,len(order))];refine_paths=[paths[i] for i in refine_indices]
    began=time.monotonic();rs,rw,rb,rr=gpu_multistart_screen(coarse_binary,blocks,pair,quad,refine_paths,refine_restarts,refine_iterations);refine_seconds=time.monotonic()-began
    refine_order=np.lexsort((np.arange(len(rs)),-rs));refined=[]
    for rank,j in enumerate(refine_order,1):
        original=int(refine_indices[j]);refined.append({"rank":rank,"coarse_rank":int(ranks[original]),"shortlist_index":original,"is_true_segment":paths[original] in truth_windows,"normalized_score":float(rs[j]),"board_accuracy":board_accuracy(rb[j]),"best_restart":int(rr[j]),"path":list(paths[original]),"board":rb[j].tolist(),"quadgram_windows":int(rw[j])})
    began=time.monotonic();terminals,extension_diagnostics=run_extension_backend(blocks,pair,quad,refined,seed_count=extend_seed_count,beam_width=extend_beam,terminals_per_seed=terminals_per_seed,workers=extend_workers,backend=extension_backend,persistent_binary=persistent_binary);extension_seconds=time.monotonic()-began
    truth_tuple=tuple(truth);truth_terminal=next((r for r in terminals if tuple(r["order"])==truth_tuple),None)
    began=time.monotonic();final,skipped_terminals=resolve_terminals(blocks,pair,quad,terminals,restarts=final_restarts,iterations=final_iterations);final_seconds=time.monotonic()-began
    exact_final=next((r for r in final if tuple(r["order"])==truth_tuple),None);truth_plaintext=fixture["plaintext"]
    for record in final:record["is_exact_order"]=tuple(record["order"])==truth_tuple;record["plaintext_accuracy"]=sum(a==b for a,b in zip(record["plaintext"],truth_plaintext))/max(len(record["plaintext"]),len(truth_plaintext))
    true_board_values=[r["board_accuracy"] for r in true_records if r["board_accuracy"] is not None]
    refined_true_board_values=[r["board_accuracy"] for r in refined if r["is_true_segment"] and r["board_accuracy"] is not None]
    return {"phase":"484Q","status":"development_blind_joint_complete_not_frozen","faed_scored":False,"holdout_consumed":split=="holdout","board_mode":mode,"fixture_index":fixture_index,"split":split,"true_pair":list(true_pair),"true_pair_index":true_pair_index,"hypothesis_pair":list(pair),"hypothesis_pair_index":hypothesis_pair_index,"hypothesis_is_true_pair":pair==true_pair,"shortlist_size":len(paths),"restarts_per_fragment":restarts,"iterations_per_restart":iterations,"refine_keep":len(refine_paths),"refine_restarts":refine_restarts,"refine_iterations":refine_iterations,"extension_seed_count":min(extend_seed_count,len(refined)),"extension_workers":extend_workers,"extension_beam":extend_beam,"terminals_per_seed":terminals_per_seed,"final_restarts":final_restarts,"final_iterations":final_iterations,"shortlist_seconds":shortlist_seconds,"gpu_screen_seconds":screen_seconds,"gpu_refine_seconds":refine_seconds,"extension_seconds":extension_seconds,"final_seconds":final_seconds,"best_refined_normalized_score":float(rs[refine_order[0]]) if len(refine_order) else None,"top1_final_normalized_score":final[0]["normalized_score"] if final else None,"true_segments_retained":len(true_records),"best_true_coarse_rank":min((r["coarse_rank"] for r in true_records),default=None),"best_true_board_accuracy":max(true_board_values,default=None),"best_true_refined_rank":min((r["rank"] for r in refined if r["is_true_segment"]),default=None),"best_true_refined_board_accuracy":max(refined_true_board_values,default=None),"exact_order_in_terminals":truth_terminal is not None,"exact_order_extension_rank":truth_terminal["extension_rank"] if truth_terminal else None,"exact_order_final_rank":exact_final["final_rank"] if exact_final else None,"top1_exact_order":bool(final and final[0]["is_exact_order"]),"top1_plaintext_accuracy":final[0]["plaintext_accuracy"] if final else None,"terminals_total":len(terminals),"terminals_valid":len(terminals)-len(skipped_terminals),"terminals_skipped_invalid_segmentation":len(skipped_terminals),"true_records":true_records,"refined_population":refined,"terminal_orders":terminals,"final_candidates":final,"skipped_terminals":skipped_terminals,"extension_diagnostics":extension_diagnostics}

def self_test(binary=COARSE_BINARY):
    fixture=base.make_fixture(WIDTH,learned.PAIR_INDEX,23,seed=learned.SEED,board_mode="vic_profile",split="dev");blocks=prefix.blocks_from_observed(fixture);pair=tuple(fixture["pair"]);quad,_=base.load_language_model();paths=np.asarray(list(itertools.islice(itertools.permutations(range(WIDTH),DEPTH),16)),dtype=np.uint8);_,_,boards0=gpu_coarse_screen(binary,blocks,pair,quad,paths,iterations=0)
    for i,(path,b) in enumerate(zip(paths,boards0)):
        if not np.array_equal(b,initial_board(SEED,path)):raise AssertionError(f"initial board mismatch at {i}")
    reversed_paths=paths[::-1].copy();_,_,reversed_boards=gpu_coarse_screen(binary,blocks,pair,quad,reversed_paths,iterations=0)
    board_by_path={tuple(path):board for path,board in zip(paths,boards0)}
    for path,board in zip(reversed_paths,reversed_boards):
        if not np.array_equal(board,board_by_path[tuple(path)]):raise AssertionError("fragment seed changed after reordering")
    scores,windows,boards=gpu_coarse_screen(binary,blocks,pair,quad,paths,iterations=37);errors=[]
    for i,(path,board) in enumerate(zip(paths,boards)):
        expected,ew=cpu_recompute(blocks,pair,quad,path,board);errors.append(abs(expected-scores[i]))
        if ew!=windows[i]:raise AssertionError((ew,windows[i]))
        if sorted(board.tolist())!=list(range(25)):raise AssertionError("board is not a permutation")
    slots=complete_token_slots(blocks,pair,prefix.order_to_sequence(fixture["order"]));fs,fb=gpu_full_screen(FULL_BINARY,[slots],quad,37,SEED);expected=base.score_indices(fb[0][slots].astype(np.int64),quad)/max(1,len(slots)-3);errors.append(abs(expected-fs[0]))
    if errors[-1]>1e-10:raise AssertionError(f"full-stream score mismatch: {errors[-1]}")
    return {"paths":len(paths),"initial_rng_parity":True,"path_reordering_invariant":True,"score_recomputation_max_abs_error":max(errors)}

def main():
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--run",action="store_true");p.add_argument("--mode",choices=base.BOARD_MODES,default="vic_profile");p.add_argument("--fixture-index",type=int,default=23);p.add_argument("--keep",type=int,default=SHORTLIST);p.add_argument("--iterations",type=int,default=ITERATIONS);p.add_argument("--restarts",type=int,default=RESTARTS);p.add_argument("--refine-keep",type=int,default=REFINE_KEEP);p.add_argument("--refine-restarts",type=int,default=REFINE_RESTARTS);p.add_argument("--refine-iterations",type=int,default=REFINE_ITERATIONS);p.add_argument("--extend-seeds",type=int,default=EXTEND_SEEDS);p.add_argument("--extend-workers",type=int,default=1);p.add_argument("--extend-beam",type=int,default=EXTEND_BEAM);p.add_argument("--terminals-per-seed",type=int,default=TERMINALS_PER_SEED);p.add_argument("--final-restarts",type=int,default=FINAL_RESTARTS);p.add_argument("--final-iterations",type=int,default=FINAL_ITERATIONS);p.add_argument("--hypothesis-pair-index",type=int);p.add_argument("--true-pair-index",type=int,default=learned.PAIR_INDEX);p.add_argument("--invariant-binary",type=Path,default=DEFAULT_BINARY);p.add_argument("--coarse-binary",type=Path,default=COARSE_BINARY);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:print(self_test(a.coarse_binary));return 0
    if not a.run:p.error("use --self-test or --run")
    result=screen_fixture(
        mode=a.mode,fixture_index=a.fixture_index,keep=a.keep,
        iterations=a.iterations,restarts=a.restarts,
        refine_keep=a.refine_keep,refine_restarts=a.refine_restarts,
        refine_iterations=a.refine_iterations,
        invariant_binary=a.invariant_binary,coarse_binary=a.coarse_binary,
        extend_seed_count=a.extend_seeds,extend_beam=a.extend_beam,
        terminals_per_seed=a.terminals_per_seed,
        final_restarts=a.final_restarts,final_iterations=a.final_iterations,
        hypothesis_pair_index=a.hypothesis_pair_index,
        true_pair_index=a.true_pair_index,extend_workers=a.extend_workers)
    output=a.output or SCRIPT_DIR/f"phase484q_coarse_{a.mode}_i{a.fixture_index}_k{a.keep}_r{a.restarts}_n{a.iterations}.json";output.write_text(json.dumps(result,indent=2)+"\n");print("true",result["true_segments_retained"],"coarse rank",result["best_true_coarse_rank"],"coarse accuracy",result["best_true_board_accuracy"],"refined rank",result["best_true_refined_rank"],"refined accuracy",result["best_true_refined_board_accuracy"],"gpu seconds",round(result["gpu_screen_seconds"]+result["gpu_refine_seconds"],3));print("wrote",output);return 0
if __name__=="__main__":raise SystemExit(main())
