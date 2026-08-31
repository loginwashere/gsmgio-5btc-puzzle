#!/usr/bin/env python3
"""Phase 460: boundary-safe held-out dual-stream escape-pair calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

from data import DBBI, FAED
from phase459_dual_stream_escape_pair_calibration import (
    ALPHABET,
    PAIRS,
    TARGET_IC,
    assert_primary_preservation,
    assert_sensitivity_preservation,
    code_ic,
    endpoint_fixed_shuffle,
    euler_surrogate,
    fixture,
    segment_codes,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("phase460_dual_stream_manifest.json")
DEFAULT_OUTPUT = Path(__file__).with_name("phase460_result.json")
EXPECTED_MANIFEST_SHA256 = "c1a1c09b4859caab39b42a1b8010cdb57492ed3e2cc75980ae96bac0dc66b9e6"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def token_halves(stream: str, pair: tuple[str, str]):
    codes = segment_codes(stream, pair)
    if codes is None:
        return None
    split = len(codes) // 2
    return codes[:split], codes[split:]


def token_loss(tokens) -> float:
    return abs(code_ic(tokens) - TARGET_IC)


def score_streams(streams: dict[str, str]):
    cache = {
        name: {pair: token_halves(stream, pair) for pair in PAIRS}
        for name, stream in streams.items()
    }
    directions = []
    for direction, train_index, held_index in (
        ("left_tokens_train_right_tokens_validate", 0, 1),
        ("right_tokens_train_left_tokens_validate", 1, 0),
    ):
        shared_rows = []
        for pair in PAIRS:
            if any(cache[name][pair] is None for name in ("DBBI", "FAED")):
                continue
            loss = 0.5 * sum(
                token_loss(cache[name][pair][train_index]) for name in ("DBBI", "FAED")
            )
            shared_rows.append((loss, pair))
        shared_best = min(loss for loss, _pair in shared_rows)
        shared_ties = tuple(pair for loss, pair in shared_rows if loss == shared_best)
        shared_pair = shared_ties[0]
        shared_held = 0.5 * sum(
            token_loss(cache[name][shared_pair][held_index]) for name in ("DBBI", "FAED")
        )

        selected, ties_by_stream, train_losses, held_losses = {}, {}, {}, {}
        for name in ("DBBI", "FAED"):
            rows = [
                (token_loss(halves[train_index]), pair)
                for pair, halves in cache[name].items()
                if halves is not None
            ]
            best = min(loss for loss, _pair in rows)
            ties = tuple(pair for loss, pair in rows if loss == best)
            pair = ties[0]
            selected[name] = pair
            ties_by_stream[name] = ties
            train_losses[name] = best
            held_losses[name] = token_loss(cache[name][pair][held_index])
        independent_held = 0.5 * sum(held_losses.values())
        directions.append({
            "direction": direction,
            "shared": {
                "training_loss": shared_best,
                "selected_pair": "".join(shared_pair),
                "all_equal_best_pairs": tuple("".join(pair) for pair in shared_ties),
                "heldout_loss": shared_held,
            },
            "independent": {
                "training_losses": train_losses,
                "selected_pairs": {name: "".join(pair) for name, pair in selected.items()},
                "all_equal_best_pairs": {
                    name: tuple("".join(pair) for pair in ties_by_stream[name])
                    for name in ties_by_stream
                },
                "heldout_losses": held_losses,
                "heldout_loss": independent_held,
            },
            "contrast": shared_held - independent_held,
        })
    return {
        "directions": tuple(directions),
        "contrast": sum(row["contrast"] for row in directions) / 2,
        "shared_heldout_loss": sum(row["shared"]["heldout_loss"] for row in directions) / 2,
        "independent_heldout_loss": sum(row["independent"]["heldout_loss"] for row in directions) / 2,
    }


def null_population(kind: str, trials: int, seed: int):
    rng = random.Random(seed)
    sources = {"DBBI": DBBI, "FAED": FAED}
    values = []
    for trial in range(trials):
        if kind == "euler":
            streams = {name: euler_surrogate(stream, rng) for name, stream in sources.items()}
            if trial < 3:
                for name in sources:
                    assert_primary_preservation(sources[name], streams[name])
        elif kind == "endpoint_shuffle":
            streams = {name: endpoint_fixed_shuffle(stream, rng) for name, stream in sources.items()}
            if trial < 3:
                for name in sources:
                    assert_sensitivity_preservation(sources[name], streams[name])
        else:
            raise ValueError(kind)
        values.append(score_streams(streams)["contrast"])
    return values


def summarize(values, observed):
    ordered = sorted(values)
    extreme = sum(value >= observed for value in values)
    return {
        "trials": len(values),
        "extreme_count": extreme,
        "empirical_p": (extreme + 1) / (len(values) + 1),
        "minimum": ordered[0],
        "q05": ordered[int(0.05 * (len(ordered) - 1))],
        "median": ordered[len(ordered) // 2],
        "q95": ordered[int(0.95 * (len(ordered) - 1))],
        "maximum": ordered[-1],
    }


def verify_manifest():
    assert sha256_file(MANIFEST_PATH) == EXPECTED_MANIFEST_SHA256
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert hashlib.sha256(DBBI.encode()).hexdigest() == manifest["source_streams"]["DBBI"]["sha256_utf8"]
    assert hashlib.sha256(FAED.encode()).hexdigest() == manifest["source_streams"]["FAED"]["sha256_utf8"]
    for relative, expected in manifest["precedent_digests"].items():
        assert sha256_file(ROOT / relative) == expected
    return manifest


def self_test():
    verify_manifest()
    assert ALPHABET == "abcdefghi" and len(PAIRS) == 36
    crossing = "aabeaa"
    assert crossing[:3].endswith("b") and crossing[3] == "e"
    halves = token_halves(crossing, ("b", "e"))
    assert halves is not None and "be" in halves[1]
    assert token_halves("abcd", ("d", "e")) is None

    shared_dbbi, _ = fixture(("b", "e"), 46020, 180)
    shared_faed, _ = fixture(("b", "e"), 46030, 700)
    shared = score_streams({"DBBI": shared_dbbi, "FAED": shared_faed})
    planted_dbbi, _ = fixture(("b", "e"), 46040, 180)
    planted_faed, _ = fixture(("g", "i"), 46050, 700)
    planted = score_streams({"DBBI": planted_dbbi, "FAED": planted_faed})
    assert shared["contrast"] <= 0.002
    assert planted["contrast"] > 0

    rng = random.Random(4601)
    for source in (DBBI, FAED):
        assert_primary_preservation(source, euler_surrogate(source, rng))
        assert_sensitivity_preservation(source, endpoint_fixed_shuffle(source, rng))
    print("[*] Phase 460 self-test OK: boundary-safe token halves, fixtures, digests, and null invariants passed")
    return {"shared_fixture": shared, "specialized_fixture": planted}


def run():
    manifest = verify_manifest()
    self_test()
    count, seed = manifest["trials_per_null"], manifest["master_seed"]
    primary_values = null_population("euler", count, seed + 1)
    sensitivity_values = null_population("endpoint_shuffle", count, seed + 2)
    observed = score_streams({"DBBI": DBBI, "FAED": FAED})
    primary = summarize(primary_values, observed["contrast"])
    sensitivity = summarize(sensitivity_values, observed["contrast"])
    threshold = manifest["promotion_threshold"]
    passes = (primary["empirical_p"] <= threshold, sensitivity["empirical_p"] <= threshold)
    if observed["contrast"] > 0 and all(passes):
        decision = "robust_specialization"
    elif observed["contrast"] > 0 and sum(passes) == 1:
        decision = "null_sensitive"
    else:
        decision = "no_calibrated_specialization"
    return {
        "phase": 460,
        "corrects_phase": 459,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "candidate_pair_count": len(PAIRS),
        "observed": observed,
        "nulls": {"primary_euler": primary, "sensitivity_endpoint_shuffle": sensitivity},
        "promotion_threshold": threshold,
        "decision": decision,
        "maximum_inference": "corroboration_only_no_pair_selection_no_gap_closure",
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "network_touched": False,
        "gpu_touched": False,
        "docker_touched": False,
        "external_agents_used": False,
    }


def benchmark(trials: int):
    self_test()
    start = time.monotonic()
    null_population("euler", trials, 46099)
    elapsed = time.monotonic() - start
    print(f"[*] benchmark: {trials} trials in {elapsed:.3f}s; projected production {elapsed * 40000 / trials:.1f}s")
    print("[*] real streams not scored")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--benchmark", type=int)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.benchmark is not None:
        benchmark(args.benchmark)
    elif args.run:
        result = run()
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"[*] wrote {args.json_out}")
        print(f"[*] contrast={result['observed']['contrast']:.12g} decision={result['decision']}")
    else:
        self_test()


if __name__ == "__main__":
    main()
