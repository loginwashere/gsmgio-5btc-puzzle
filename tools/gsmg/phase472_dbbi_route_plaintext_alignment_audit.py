#!/usr/bin/env python3
"""Phase 472: family-max DBBI route/plaintext alignment audit.

Association only: no derived-text inspection, passwords, decryptions, FAED, or
oracle calls. See the frozen Phase 472 protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np

from data import DBBI, VALIDATION_ANSWER
from phase471_dbbi_route_structure_diagnostic_audit import (
    N,
    SHAPES,
    cell_index,
    rectangle_routes,
    toroidal_route,
)

SCRIPT_DIR = Path(__file__).resolve().parent
RESULT_PATH = SCRIPT_DIR / "phase472_result.json"
LEDGER_PATH = SCRIPT_DIR / "phase421_invocation_ledger.json"

N_ROUTES = 19686
N_NULL = 2000
RNG_SEEDS = (472, 473, 474, 475, 476)
CONTROL_OFFSETS = (0, 273, 546, 819)
TOP_RECORDS = 20
LEAD_ALPHA = 0.001


def canonical_route_registry() -> tuple[np.ndarray, list[str]]:
    """Rebuild and globally deduplicate Phase 471's exact route universe."""
    registry: dict[tuple[int, ...], str] = {}

    def add(perm, label: str) -> None:
        perm = tuple(perm)
        if len(perm) != N or len(set(perm)) != N or min(perm) != 0 or max(perm) != N - 1:
            raise AssertionError(f"invalid route: {label}")
        registry.setdefault(perm, label)

    for rows, columns in SHAPES:
        for name, coords in rectangle_routes(rows, columns).items():
            add(
                (cell_index(r, c, columns) for r, c in coords),
                f"rectangle_{rows}x{columns}:{name}",
            )
        for dr in range(1, rows):
            for dc in range(1, columns):
                for r0 in range(rows):
                    for c0 in range(columns):
                        add(
                            toroidal_route(rows, columns, r0, c0, dr, dc),
                            f"toroidal_{rows}x{columns}:start={r0},{c0}:step={dr},{dc}",
                        )
    for a in range(1, N):
        if math.gcd(a, N) != 1:
            continue
        for b in range(N):
            add(
                ((a * n + b) % N for n in range(N)),
                f"linear_mod91:a={a}:b={b}",
            )

    if len(registry) != N_ROUTES:
        raise AssertionError(f"route registry changed: {len(registry)} != {N_ROUTES}")
    perms = np.asarray(list(registry), dtype=np.uint8)
    labels = list(registry.values())
    return perms, labels


def registry_sha256(perms: np.ndarray) -> str:
    return hashlib.sha256(perms.tobytes(order="C")).hexdigest()


def normalized_control_windows() -> list[tuple[str, str]]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    long_text = ledger["records"]["phase421_invocation_3"]["candidate_displays"][0]
    if not long_text.startswith("YOURLIFEISTHESUMOFAREMAINDER"):
        raise AssertionError("control source changed")
    if not long_text.isalpha() or not long_text.isupper() or len(long_text) <= max(CONTROL_OFFSETS) + N:
        raise AssertionError("control source invariant failed")
    return [
        (f"control_offset_{offset}", long_text[offset:offset + N])
        for offset in CONTROL_OFFSETS
    ]


def target_residues(text: str) -> tuple[np.ndarray, np.ndarray]:
    if len(text) != N or not text.isalpha() or not text.isupper():
        raise AssertionError("target must be exactly 91 uppercase A-Z characters")
    a0 = np.fromiter(((ord(c) - ord("A")) % 9 for c in text), dtype=np.uint8, count=N)
    return a0, (a0 + 1) % 9


def routed_dbbi(perms: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.fromiter((ord(c) - ord("a") for c in DBBI), dtype=np.uint8, count=N)
    routed = values[perms]
    return routed, 8 - routed


MAPPING_NAMES = (
    "dbbi_a0i8__plaintext_a0z25_mod9",
    "dbbi_a0i8__plaintext_a1z26_mod9",
    "dbbi_reversed__plaintext_a0z25_mod9",
    "dbbi_reversed__plaintext_a1z26_mod9",
)


def score_vector(
    routed: np.ndarray,
    routed_reversed: np.ndarray,
    target_a0: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    target_a1 = (target_a0 + 1) % 9
    candidates = (
        np.count_nonzero(routed == target_a0, axis=1),
        np.count_nonzero(routed == target_a1, axis=1),
        np.count_nonzero(routed_reversed == target_a0, axis=1),
        np.count_nonzero(routed_reversed == target_a1, axis=1),
    )
    scores = np.stack(candidates, axis=1)
    mapping_indices = np.argmax(scores, axis=1)
    route_scores = scores[np.arange(scores.shape[0]), mapping_indices]
    return route_scores, mapping_indices


def top_records(
    scores: np.ndarray,
    mapping_indices: np.ndarray,
    labels: list[str],
) -> list[dict]:
    order = sorted(range(len(scores)), key=lambda i: (-int(scores[i]), labels[i]))[:TOP_RECORDS]
    return [
        {
            "rank": rank,
            "matches": int(scores[i]),
            "route_index": i,
            "route": labels[i],
            "mapping": MAPPING_NAMES[int(mapping_indices[i])],
        }
        for rank, i in enumerate(order, 1)
    ]


def evaluate_target(
    name: str,
    text: str,
    seed: int,
    routed: np.ndarray,
    routed_reversed: np.ndarray,
    labels: list[str],
) -> dict:
    a0, _ = target_residues(text)
    observed_scores, observed_mappings = score_vector(routed, routed_reversed, a0)
    observed_max = int(observed_scores.max())

    rng = random.Random(seed)
    shuffled = list(map(int, a0))
    null_maxima = []
    for _ in range(N_NULL):
        rng.shuffle(shuffled)
        null_scores, _ = score_vector(
            routed,
            routed_reversed,
            np.asarray(shuffled, dtype=np.uint8),
        )
        null_maxima.append(int(null_scores.max()))
    exceedances = sum(value >= observed_max for value in null_maxima)
    p_upper = (1 + exceedances) / (N_NULL + 1)
    mean = sum(null_maxima) / N_NULL
    variance = sum((value - mean) ** 2 for value in null_maxima) / N_NULL
    return {
        "name": name,
        "text_sha256": hashlib.sha256(text.encode("ascii")).hexdigest(),
        "residue_counts_a0": [int(np.count_nonzero(a0 == v)) for v in range(9)],
        "observed_max_matches": observed_max,
        "observed_match_fraction": observed_max / N,
        "null_exceedances_ge_observed": exceedances,
        "p_upper_plus_one": p_upper,
        "null_max_min": min(null_maxima),
        "null_max_max": max(null_maxima),
        "null_max_mean": mean,
        "null_max_sd": variance ** 0.5,
        "null_max_histogram": {
            str(value): null_maxima.count(value) for value in sorted(set(null_maxima))
        },
        "top_records": top_records(observed_scores, observed_mappings, labels),
    }


def build_report() -> dict:
    if len(DBBI) != N or set(DBBI) != set("abcdefghi"):
        raise AssertionError("canonical DBBI changed")
    if len(VALIDATION_ANSWER) != N:
        raise AssertionError("canonical validation answer changed")

    perms, labels = canonical_route_registry()
    routed, routed_reversed = routed_dbbi(perms)
    targets = [("real_validation_answer", VALIDATION_ANSWER)] + normalized_control_windows()
    evaluations = [
        evaluate_target(name, text, seed, routed, routed_reversed, labels)
        for (name, text), seed in zip(targets, RNG_SEEDS)
    ]
    real = evaluations[0]
    controls = evaluations[1:]
    gates = {
        "real_p_below_alpha": real["p_upper_plus_one"] < LEAD_ALPHA,
        "real_max_strictly_above_all_controls": all(
            real["observed_max_matches"] > control["observed_max_matches"]
            for control in controls
        ),
        "real_p_strictly_below_all_controls": all(
            real["p_upper_plus_one"] < control["p_upper_plus_one"]
            for control in controls
        ),
    }
    gates["lead"] = all(gates.values())
    return {
        "phase": 472,
        "route_count": len(labels),
        "route_registry_sha256": registry_sha256(perms),
        "mapping_count": len(MAPPING_NAMES),
        "route_mapping_combinations_per_target": len(labels) * len(MAPPING_NAMES),
        "n_null_per_target": N_NULL,
        "rng_seeds": list(RNG_SEEDS),
        "control_offsets": list(CONTROL_OFFSETS),
        "evaluations": evaluations,
        "decision_gates": gates,
        "derived_texts_serialized": 0,
        "password_materials_generated": 0,
        "decryptions_attempted": 0,
        "faed_uses": 0,
        "oracle_calls": 0,
    }


def structural_self_test() -> None:
    perms, labels = canonical_route_registry()
    assert perms.shape == (N_ROUTES, N)
    assert len(labels) == N_ROUTES and len(set(map(tuple, perms.tolist()))) == N_ROUTES
    assert DBBI in {"".join(DBBI[i] for i in perm) for perm in perms[:40]}  # identity is first
    assert len(normalized_control_windows()) == 4
    sample = np.zeros((2, N), dtype=np.uint8)
    sample[1] = np.arange(N, dtype=np.uint8) % 9
    scores, mappings = score_vector(sample, 8 - sample, np.arange(N, dtype=np.uint8) % 9)
    assert int(scores[1]) == N and int(mappings[1]) == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--structural-only", action="store_true")
    args = parser.parse_args()
    structural_self_test()
    if args.structural_only:
        print("[*] Phase 472 structural self-test OK")
        return
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "route_count": report["route_count"],
        "evaluations": [
            {
                "name": item["name"],
                "observed_max_matches": item["observed_max_matches"],
                "p_upper_plus_one": item["p_upper_plus_one"],
            }
            for item in report["evaluations"]
        ],
        "decision_gates": report["decision_gates"],
    }, indent=2))


if __name__ == "__main__":
    main()
