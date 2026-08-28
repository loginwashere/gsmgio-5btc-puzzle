#!/usr/bin/env python3
"""Phase 441: analyze the exact completed Phase-430 16! GPU search."""

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path

import phase431_bifid16_equivalence_class_audit as phase431
import phase432_bifid16_candidate_reviewer as phase432
import phase433_quadgram_score_pathology_audit as phase433
from phase387_btcseed_kmodest_checkpoint_audit import load_quadgrams


REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_PATH = REPO_ROOT / "tools/bifid_gpu_search16/checkpoints/bifid_16factorial.json"
FINAL_RESULT_PATH = REPO_ROOT / "tools/bifid_gpu_search16/output/bifid_16factorial_result.json"
FINAL_REVIEW_PATH = REPO_ROOT / "tools/gsmg/phase432_final_review.json"
PHASE433_PATH = REPO_ROOT / "tools/gsmg/phase433_result.json"
LIVE_REVIEW_PATH = REPO_ROOT / "tools/gsmg/phase432_live_review.json"
EXPECTED_HASHES = {
    CHECKPOINT_PATH: "2735d25f3b06805f02a0bb2981cd0d60d3db724317ddf598e720f57519d17770",
    FINAL_RESULT_PATH: "0b389df0c7c2f14a6ad228da483b80246537889879d960268e0730c78e785de3",
    FINAL_REVIEW_PATH: "2b8a9cead5cd3df6d33b01972931be0360ae001912c5171e38c2bdce60b1fcae",
    PHASE433_PATH: "5f33f313aae25001a2f4a688d3d8de3520d037180a974a2d5625d714117fa93d",
    LIVE_REVIEW_PATH: "16b8741207589af9ed3b5a56ef42b3c4e10d15bb79920d6e949a0fb2e340663e",
}
DICTIONARY_SHA256 = "9f513f1ceadb6a01c5485b7dbdfd5118dc66cd70b59cae2851292112d4066a32"
TRIALS = 1_000
RANK_SAMPLES = 10_000
SEED = 0x441


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_pinned_json(path):
    raw = path.read_bytes()
    if sha256(raw) != EXPECTED_HASHES[path]:
        raise AssertionError(f"pinned artifact drifted: {path}")
    return json.loads(raw)


def consensus_analysis(collapsed, final_review):
    tails = [row["decoded"][len(phase432.TARGET):] for row in collapsed]
    if {len(tail) for tail in tails} != {563}:
        raise AssertionError("distinct tail lengths drifted")
    consensus = []
    invariant_positions = []
    for index, column in enumerate(zip(*tails)):
        if len(set(column)) == 1:
            consensus.append(column[0])
            invariant_positions.append(index)
        else:
            consensus.append("?")
    distances = sorted(
        sum(a != b for a, b in zip(tails[left], tails[right]))
        for left in range(len(tails))
        for right in range(left + 1, len(tails))
    )
    reviewed = final_review["distinct_candidates"]
    hit_sets = [
        {(hit["start"], hit["word"]) for hit in row["dictionary_hits_5_to_12"]}
        for row in reviewed
    ]
    shared_hits = sorted(set.intersection(*hit_sets)) if hit_sets else []
    keyword_union = sorted({
        (hit["keyword"], start)
        for row in reviewed for hit in row["keyword_hits"] for start in hit["starts"]
    })
    return {
        "distinct_decode_count": len(tails),
        "invariant_position_count": len(invariant_positions),
        "invariant_fraction": len(invariant_positions) / 563,
        "invariant_positions_zero_based": invariant_positions,
        "consensus_question_mark_for_variable": "".join(consensus),
        "pairwise_hamming": {
            "pair_count": len(distances),
            "minimum": distances[0],
            "median": statistics.median(distances),
            "maximum": distances[-1],
        },
        "shared_dictionary_hits": [
            {"start": start, "word": word} for start, word in shared_hits
        ],
        "fixed_keyword_union": [
            {"keyword": keyword, "start": start} for keyword, start in keyword_union
        ],
        "class_sizes_descending": sorted(
            (row["raw_member_count"] for row in collapsed), reverse=True
        ),
        "score_range": {
            "best": max(row["best_score_total"] for row in collapsed),
            "worst": min(row["best_score_total"] for row in collapsed),
        },
    }


def final_controls(square, trials, rank_samples):
    logs, floor = load_quadgrams()
    decoded = phase431.decode_square(square)
    if not decoded.startswith(phase432.TARGET):
        raise AssertionError("final square violates BTCSEED")
    tail = decoded[len(phase432.TARGET):]
    observed = phase433.score(tail, logs, floor)
    rng = random.Random(SEED)
    global_null = phase433.global_scores(
        random.Random(SEED ^ 0xA11), rank_samples, logs, floor
    )
    return {
        "profile": phase433.profile(tail, logs, floor),
        "exact_multiset_shuffle": phase433.summarize(
            phase433.exact_shuffle_scores(tail, rng, trials, logs, floor), observed
        ),
        "intact_digraph_shuffle": phase433.summarize(
            phase433.digraph_shuffle_scores(tail, rng, trials, logs, floor), observed
        ),
        "conditional_same_g_h_placement": phase433.summarize(
            phase433.conditional_scores(square, rng, rank_samples, logs, floor), observed
        ),
        "uniform_global_rank": phase433.summarize(global_null, observed),
    }


def audit(trials=TRIALS, rank_samples=RANK_SAMPLES):
    if trials < 1 or rank_samples < 1:
        raise ValueError("control counts must be positive")
    checkpoint = load_pinned_json(CHECKPOINT_PATH)
    final_result = load_pinned_json(FINAL_RESULT_PATH)
    final_review = load_pinned_json(FINAL_REVIEW_PATH)
    prior_pathology = load_pinned_json(PHASE433_PATH)
    live_review = load_pinned_json(LIVE_REVIEW_PATH)
    if checkpoint["fingerprint"] != phase432.EXPECTED_FINGERPRINT:
        raise AssertionError("checkpoint fingerprint mismatch")
    if checkpoint["next_rank"] != phase431.TOTAL_RANKS:
        raise AssertionError("checkpoint is not exactly complete")
    if final_result["range_end_exclusive"] != phase431.TOTAL_RANKS or final_result["interrupted"]:
        raise AssertionError("final result is incomplete or interrupted")
    if final_result["fingerprint"] != checkpoint["fingerprint"]:
        raise AssertionError("checkpoint/result fingerprints differ")
    if sha256(phase432.DEFAULT_DICTIONARY.read_bytes()) != DICTIONARY_SHA256:
        raise AssertionError("review dictionary drifted")

    collapsed = phase432.collapse_winners(checkpoint["block_winners"])
    if len(collapsed) != 9 or sum(row["raw_member_count"] for row in collapsed) != 1000:
        raise AssertionError("final equivalence collapse drifted")
    winner = final_result["exact_global_winner_for_completed_range"]
    leader = final_review["distinct_candidates"][0]
    if not (
        winner["rank"] == collapsed[0]["best_rank"] == leader["best_rank"]
        and winner["decoded_sha256"] == collapsed[0]["decoded_sha256"] == leader["decoded_sha256"]
        and abs(winner["score_total"] - collapsed[0]["best_score_total"]) < 1e-3
    ):
        raise AssertionError("result/checkpoint/reviewer winner mismatch")

    invariance = consensus_analysis(collapsed, final_review)
    controls = final_controls(winner["square"], trials, rank_samples)
    old_profiles = {
        row["label"]: row["profile"] for row in prior_pathology["candidates"]
    }
    english = prior_pathology["english_control"]["profile"]
    final_profile = controls["profile"]
    comparison = {
        "phase430_rank_zero": old_profiles["phase430_rank_zero"],
        "phase429_exact_winner": old_profiles["phase429_exact_winner"],
        "phase432_snapshot_leader": old_profiles["phase432_snapshot_leader"],
        "phase441_final_exact_winner": final_profile,
        "pinned_english": english,
    }
    gap = english["quadgram_mean"] - final_profile["quadgram_mean"]
    keyword_present = bool(invariance["fixed_keyword_union"])
    non_template_long_structure = (
        max(row["longest_repeated_substring"] for row in final_review["distinct_candidates"]) > 5
    )
    coherent = (
        keyword_present
        and non_template_long_structure
        and gap < 0.5
        and final_profile["lag1_mutual_information_bits"] >= 0.9 * english["lag1_mutual_information_bits"]
    )
    decision = (
        "coherent_plaintext_evidence" if coherent
        else "exact_16factorial_negative_quadgram_selection_pathology_confirmed"
    )
    return {
        "phase": 441,
        "completion": {
            "domain_start": 0,
            "domain_end_exclusive": phase431.TOTAL_RANKS,
            "checkpoint_next_rank": checkpoint["next_rank"],
            "complete_fraction": checkpoint["next_rank"] / phase431.TOTAL_RANKS,
            "interrupted": final_result["interrupted"],
            "device": final_result["device"],
            "resume_range_start": final_result["range_start"],
            "candidates_processed_this_run": final_result["candidates_processed_this_run"],
            "elapsed_seconds_this_run": final_result["elapsed_seconds"],
            "candidates_per_second": final_result["candidates_per_second"],
            "projected_full_hours_at_measured_speed": final_result["projected_full_16factorial_hours"],
            "shortlist_is_exact_top_k": final_result["shortlist_is_exact_top_k"],
            "fingerprint": checkpoint["fingerprint"],
        },
        "exact_winner": winner,
        "exact_winner_decoded": collapsed[0]["decoded"],
        "snapshot_delta": {
            "progress_before": live_review["checkpoint"]["full_progress_fraction"],
            "leader_changed": final_review["delta_from_previous"]["leader_changed"],
            "gpu_total_score_improvement": final_review["delta_from_previous"]["leader_score_delta"],
        },
        "equivalence_and_invariance": invariance,
        "final_winner_controls": controls,
        "absolute_profile_comparison": comparison,
        "english_quadgram_mean_gap": gap,
        "english_per_window_likelihood_ratio": 10 ** gap,
        "dictionary_interpretation": (
            "saved p-values are within-candidate exact-multiset calibrations, not corrections for selecting the candidates by quadgram score from 16! ranks; shared same-position hits diagnose an optimized template"
        ),
        "decision_criteria": {
            "fixed_keyword_outside_crib": keyword_present,
            "non_template_word_scale_structure_longer_than_5": non_template_long_structure,
            "absolute_quadgram_gap_below_0_5": gap < 0.5,
            "lag1_mi_at_least_90pct_english": final_profile["lag1_mutual_information_bits"] >= 0.9 * english["lag1_mutual_information_bits"],
        },
        "decision": decision,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "new_gpu_work": False,
        "docker_mutated": False,
    }


def self_test():
    report = audit(trials=20, rank_samples=100)
    assert report["completion"]["complete_fraction"] == 1.0
    assert report["completion"]["shortlist_is_exact_top_k"] is False
    assert report["exact_winner"]["rank"] == 8_041_961_541_600
    eq = report["equivalence_and_invariance"]
    assert eq["distinct_decode_count"] == 9
    assert eq["class_sizes_descending"] == [524, 469, 1, 1, 1, 1, 1, 1, 1]
    assert eq["fixed_keyword_union"] == []
    assert report["decision"] == "exact_16factorial_negative_quadgram_selection_pathology_confirmed"
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["new_gpu_work"] is report["docker_mutated"] is False
    print("[*] Phase 441 self-test OK: exact 16! complete; 9 decodes; no coherent plaintext evidence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--rank-samples", type=int, default=RANK_SAMPLES)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.trials, args.rank_samples)
    if args.self_test:
        self_test()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    elif not args.self_test:
        print(payload, end="")


if __name__ == "__main__":
    main()
