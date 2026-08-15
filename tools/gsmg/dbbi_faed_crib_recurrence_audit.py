#!/usr/bin/env python3
"""Crib-solved low-order recurrence audit for DBBI/FAED.

Three authenticated words are encoded with the project's established
A1Z26-mod-9 rule.  At every legal placement, two leading crib digits solve
two coefficients for one of four fixed operators:

  * affine lag-1 over Z/9Z and canonical GF(9):
      P[i] = C[i] - alpha*C[i-1] - beta
  * homogeneous lag-2 over the same two algebras:
      P[i] = C[i] - alpha*C[i-1] - beta*C[i-2]

Only the unfitted crib suffix is evidence.  The same solved coefficients are
also tested at the identical position in the other stream.  The complete
best-of-crib/placement/operator/coefficient family is calibrated against
independently shuffled DBBI and FAED streams preserving exact symbol profiles.
No language score or password oracle is used.
"""

import argparse
import json
import math
import random

from cb_common import keyword_to_seed
from data import DBBI, FAED
from dbbi_faed_gf9_audit import gf9


CRIBS = ("yinyang", "thispassword", "seed")
FIT_DIGITS = 2
ALGEBRAS = ("z9", "gf9_x2_plus_1")
MODELS = ("affine_lag1", "homogeneous_lag2")
SPECIFICATIONS = tuple(
    (algebra, model) for algebra in ALGEBRAS for model in MODELS
)
METRIC_ALTERNATIVES = {
    "max_holdout_surprisal": "high",
    "max_aligned_other_surprisal": "high",
    "max_joint_surprisal": "high",
    "perfect_holdout_max_crib_length": "high",
}
FAMILY_SIZE = len(METRIC_ALTERNATIVES)
GF9 = gf9(0, 1)
SOLUTION_CACHE = {}


def values(stream):
    result = tuple(ord(symbol) - ord("a") for symbol in stream)
    if any(not 0 <= value < 9 for value in result):
        raise ValueError("stream contains symbols outside a-i")
    return result


def crib_digits(crib):
    return tuple(keyword_to_seed(crib, 9))


def history_length(model):
    if model == "affine_lag1":
        return 1
    if model == "homogeneous_lag2":
        return 2
    raise ValueError(f"unknown model: {model}")


def sub(algebra, left, right):
    return (left - right) % 9 if algebra == "z9" else GF9.sub(left, right)


def mul(algebra, left, right):
    return (left * right) % 9 if algebra == "z9" else GF9.mul(left, right)


def decode_at(cipher, index, alpha, beta, algebra, model):
    result = cipher[index]
    result = sub(algebra, result, mul(algebra, alpha, cipher[index - 1]))
    if model == "affine_lag1":
        return sub(algebra, result, beta)
    if model == "homogeneous_lag2":
        return sub(algebra, result, mul(algebra, beta, cipher[index - 2]))
    raise ValueError(f"unknown model: {model}")


def local_context(cipher, start, model):
    history = history_length(model)
    return tuple(cipher[start - history:start + FIT_DIGITS])


def coefficient_solutions(cipher, start, target_prefix, algebra, model):
    context = local_context(cipher, start, model)
    cache_key = (algebra, model, context, tuple(target_prefix))
    if cache_key not in SOLUTION_CACHE:
        # Rebuild a tiny local cipher whose fitted positions begin at `history`.
        history = history_length(model)
        local = context
        solutions = []
        for alpha in range(9):
            for beta in range(9):
                decoded = tuple(
                    decode_at(local, history + offset, alpha, beta, algebra, model)
                    for offset in range(FIT_DIGITS)
                )
                if decoded == tuple(target_prefix):
                    solutions.append((alpha, beta))
        SOLUTION_CACHE[cache_key] = tuple(solutions)
    return SOLUTION_CACHE[cache_key]


def binomial_tail_probability(matches, opportunities, probability=1 / 9):
    if opportunities <= 0:
        return 1.0
    return sum(
        math.comb(opportunities, successes)
        * probability ** successes
        * (1 - probability) ** (opportunities - successes)
        for successes in range(matches, opportunities + 1)
    )


def surprisal(matches, opportunities):
    probability = binomial_tail_probability(matches, opportunities)
    return -math.log10(max(probability, 1e-300))


def decoded_matches(cipher, start, target, alpha, beta, algebra, model,
                    offset=0):
    matches = 0
    for relative in range(offset, len(target)):
        matches += decode_at(
            cipher, start + relative, alpha, beta, algebra, model
        ) == target[relative]
    return matches, len(target) - offset


def observation(dbbi, faed, keep_top=10):
    streams = {"DBBI": values(dbbi), "FAED": values(faed)}
    targets = {crib: crib_digits(crib) for crib in CRIBS}
    top_rows = []
    fit_candidate_count = 0
    metrics = {
        "max_holdout_surprisal": 0.0,
        "max_aligned_other_surprisal": 0.0,
        "max_joint_surprisal": 0.0,
        "perfect_holdout_max_crib_length": 0,
    }

    for source_name, cipher in streams.items():
        other_name = "FAED" if source_name == "DBBI" else "DBBI"
        other = streams[other_name]
        for algebra, model in SPECIFICATIONS:
            history = history_length(model)
            for crib, target in targets.items():
                for start in range(history, len(cipher) - len(target) + 1):
                    solutions = coefficient_solutions(
                        cipher, start, target[:FIT_DIGITS], algebra, model
                    )
                    for alpha, beta in solutions:
                        fit_candidate_count += 1
                        holdout = decoded_matches(
                            cipher, start, target, alpha, beta, algebra, model,
                            offset=FIT_DIGITS,
                        )
                        holdout_score = surprisal(*holdout)
                        if start + len(target) <= len(other):
                            aligned = decoded_matches(
                                other, start, target, alpha, beta, algebra, model
                            )
                        else:
                            aligned = (0, 0)
                        aligned_score = surprisal(*aligned)
                        joint_score = holdout_score + aligned_score
                        metrics["max_holdout_surprisal"] = max(
                            metrics["max_holdout_surprisal"], holdout_score
                        )
                        metrics["max_aligned_other_surprisal"] = max(
                            metrics["max_aligned_other_surprisal"], aligned_score
                        )
                        metrics["max_joint_surprisal"] = max(
                            metrics["max_joint_surprisal"], joint_score
                        )
                        if holdout[0] == holdout[1]:
                            metrics["perfect_holdout_max_crib_length"] = max(
                                metrics["perfect_holdout_max_crib_length"], len(target)
                            )
                        if keep_top:
                            row = {
                                "source": source_name,
                                "other_source": other_name,
                                "algebra": algebra,
                                "model": model,
                                "crib": crib,
                                "start_0": start,
                                "alpha": alpha,
                                "beta": beta,
                                "fit_matches": FIT_DIGITS,
                                "holdout_matches": holdout[0],
                                "holdout_opportunities": holdout[1],
                                "holdout_surprisal": holdout_score,
                                "aligned_other_matches": aligned[0],
                                "aligned_other_opportunities": aligned[1],
                                "aligned_other_surprisal": aligned_score,
                                "joint_surprisal": joint_score,
                            }
                            top_rows.append(row)
    top_rows.sort(
        key=lambda row: (
            row["joint_surprisal"], row["holdout_surprisal"],
            row["aligned_other_surprisal"], -row["start_0"],
        ),
        reverse=True,
    )
    if tuple(metrics) != tuple(METRIC_ALTERNATIVES):
        raise AssertionError("crib-recurrence metric registry/order drifted")
    return {
        "metrics": metrics,
        "fit_candidate_count": fit_candidate_count,
        "top_rows": tuple(top_rows[:keep_top]),
    }


def empirical_upper_p(observed, null_values):
    return (1 + sum(value >= observed for value in null_values)) / (
        len(null_values) + 1
    )


def null_calibration(observed, trials, seed):
    rng = random.Random(seed)
    shuffled_dbbi = list(DBBI)
    shuffled_faed = list(FAED)
    nulls = {name: [] for name in METRIC_ALTERNATIVES}
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_faed)
        row = observation(
            "".join(shuffled_dbbi), "".join(shuffled_faed), keep_top=0
        )["metrics"]
        for name in nulls:
            nulls[name].append(row[name])
    rows = {}
    for name in METRIC_ALTERNATIVES:
        values = sorted(nulls[name])
        raw_p = empirical_upper_p(observed["metrics"][name], values)
        rows[name] = {
            "observed": observed["metrics"][name],
            "null_median": values[len(values) // 2],
            "null_95th_percentile": values[(95 * len(values)) // 100],
            "empirical_p": raw_p,
            "family_bonferroni_p": min(1.0, raw_p * FAMILY_SIZE),
        }
    return rows


def audit(trials=500, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    observed = observation(DBBI, FAED)
    calibration = null_calibration(observed, trials, seed)
    family_p = min(row["family_bonferroni_p"] for row in calibration.values())
    threshold = 0.01
    promoted = family_p < threshold
    return {
        "cribs": {
            crib: crib_digits(crib) for crib in CRIBS
        },
        "crib_encoding": "A1Z26 modulo 9 via cb_common.keyword_to_seed",
        "fit_digits": FIT_DIGITS,
        "algebras": ALGEBRAS,
        "models": MODELS,
        "specification_count": len(SPECIFICATIONS),
        "placement_policy": "every legal forward placement; same start_0 for other-stream validation",
        "observation": observed,
        "calibration": {
            "trials": trials,
            "seed": seed,
            "null_model": "independent DBBI/FAED shuffles preserving exact profiles; complete crib/placement/spec/coefficient maximum per trial",
            "metric_count": FAMILY_SIZE,
            "rows": calibration,
            "family_bonferroni_p_bound": family_p,
            "promotion_threshold": threshold,
            "promoted": promoted,
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    assert crib_digits("AI") == (1, 0)
    # Synthetic affine Z9 stream with alpha=2, beta=3 and chosen plaintext.
    plaintext = (1, 4, 2, 8, 0, 5)
    cipher = [7]
    for target in plaintext:
        cipher.append((target + 2 * cipher[-1] + 3) % 9)
    recovered = tuple(
        decode_at(tuple(cipher), index, 2, 3, "z9", "affine_lag1")
        for index in range(1, len(cipher))
    )
    assert recovered == plaintext
    solutions = coefficient_solutions(
        tuple(cipher), 1, plaintext[:2], "z9", "affine_lag1"
    )
    assert (2, 3) in solutions
    assert decoded_matches(
        tuple(cipher), 1, plaintext, 2, 3, "z9", "affine_lag1", FIT_DIGITS
    ) == (4, 4)
    report = audit(trials=3)
    assert report["specification_count"] == 4
    assert report["calibration"]["metric_count"] == 4
    assert not report["candidate_text_generated"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: crib encoding, coefficient recovery, holdout, and null gate verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] cribs:", report["cribs"])
    print("[*] fitted coefficient candidates:", report["observation"]["fit_candidate_count"])
    for row in report["observation"]["top_rows"][:5]:
        print("    top:", row)
    for name, row in report["calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']:.9g} "
            f"null_median={row['null_median']:.9g} "
            f"raw_p={row['empirical_p']:.6g} "
            f"corrected_p={row['family_bonferroni_p']:.6g}"
        )
    print(
        "[*] family p-bound:",
        f"{report['calibration']['family_bonferroni_p_bound']:.6g}",
        "promoted=" + str(report["calibration"]["promoted"]),
    )
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()
