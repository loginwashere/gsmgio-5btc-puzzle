#!/usr/bin/env python3
"""Phase 459: held-out dual-stream escape-pair calibration.

The frozen protocol and manifest define one contrast: whether independently
selected DBBI/FAED escape pairs beat a single shared pair on opposite held-out
halves. Null populations are completed before the real contrast is scored.
No alphabet completion, plaintext, password, or cryptographic oracle is used.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import time
from collections import Counter
from pathlib import Path

from data import DBBI, FAED


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("phase459_dual_stream_manifest.json")
DEFAULT_OUTPUT = Path(__file__).with_name("phase459_result.json")
EXPECTED_MANIFEST_SHA256 = "41da7f847d319368b7eba0916805a139f660cac032b43e12a4e40bf01551d2ab"

ALPHABET = "abcdefghi"
PAIRS = tuple(itertools.combinations(ALPHABET, 2))
TARGET_IC = 0.067
INVALID_LOSS = 1.0
REAL_SPLITS = {"DBBI": 45, "FAED": 285}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def segment_codes(stream: str, pair: tuple[str, str]):
    escapes = frozenset(pair)
    codes = []
    index = 0
    while index < len(stream):
        if stream[index] in escapes:
            if index + 1 == len(stream):
                return None
            codes.append(stream[index : index + 2])
            index += 2
        else:
            codes.append(stream[index])
            index += 1
    return tuple(codes)


def code_ic(codes) -> float:
    if codes is None or len(codes) < 2:
        return 0.0
    counts = Counter(codes)
    size = len(codes)
    return sum(value * (value - 1) for value in counts.values()) / (size * (size - 1))


def pair_loss(stream: str, pair: tuple[str, str]) -> float:
    codes = segment_codes(stream, pair)
    if codes is None:
        return INVALID_LOSS
    return abs(code_ic(codes) - TARGET_IC)


def best_pairs(stream: str):
    rows = tuple((pair_loss(stream, pair), pair) for pair in PAIRS)
    best = min(loss for loss, _pair in rows)
    ties = tuple(pair for loss, pair in rows if loss == best)
    return best, ties


def direction_score(streams: dict[str, str], splits: dict[str, int], direction: str):
    if direction not in {"left_train_right_validate", "right_train_left_validate"}:
        raise ValueError(direction)
    train, validate = {}, {}
    for name, stream in streams.items():
        left, right = stream[: splits[name]], stream[splits[name] :]
        if direction == "left_train_right_validate":
            train[name], validate[name] = left, right
        else:
            train[name], validate[name] = right, left

    shared_rows = []
    for pair in PAIRS:
        loss = 0.5 * (pair_loss(train["DBBI"], pair) + pair_loss(train["FAED"], pair))
        shared_rows.append((loss, pair))
    shared_best = min(loss for loss, _pair in shared_rows)
    shared_ties = tuple(pair for loss, pair in shared_rows if loss == shared_best)
    shared_pair = shared_ties[0]
    shared_held = 0.5 * (
        pair_loss(validate["DBBI"], shared_pair)
        + pair_loss(validate["FAED"], shared_pair)
    )

    independent_pairs = {}
    independent_ties = {}
    independent_train_losses = {}
    independent_held_losses = {}
    for name in ("DBBI", "FAED"):
        training_loss, ties = best_pairs(train[name])
        pair = ties[0]
        independent_pairs[name] = pair
        independent_ties[name] = ties
        independent_train_losses[name] = training_loss
        independent_held_losses[name] = pair_loss(validate[name], pair)
    independent_held = 0.5 * sum(independent_held_losses.values())

    return {
        "direction": direction,
        "shared": {
            "training_loss": shared_best,
            "selected_pair": "".join(shared_pair),
            "all_equal_best_pairs": tuple("".join(pair) for pair in shared_ties),
            "heldout_loss": shared_held,
        },
        "independent": {
            "training_losses": independent_train_losses,
            "selected_pairs": {
                name: "".join(pair) for name, pair in independent_pairs.items()
            },
            "all_equal_best_pairs": {
                name: tuple("".join(pair) for pair in independent_ties[name])
                for name in independent_ties
            },
            "heldout_losses": independent_held_losses,
            "heldout_loss": independent_held,
        },
        "contrast": shared_held - independent_held,
    }


def score_streams(streams: dict[str, str], splits: dict[str, int] = REAL_SPLITS):
    rows = tuple(
        direction_score(streams, splits, direction)
        for direction in ("left_train_right_validate", "right_train_left_validate")
    )
    return {
        "directions": rows,
        "contrast": sum(row["contrast"] for row in rows) / len(rows),
        "shared_heldout_loss": sum(row["shared"]["heldout_loss"] for row in rows) / len(rows),
        "independent_heldout_loss": sum(
            row["independent"]["heldout_loss"] for row in rows
        ) / len(rows),
    }


def transition_counts(stream: str):
    return Counter(zip(stream, stream[1:]))


def run_count(stream: str) -> int:
    return 0 if not stream else 1 + sum(a != b for a, b in zip(stream, stream[1:]))


def euler_surrogate(stream: str, rng: random.Random) -> str:
    outgoing = {symbol: [] for symbol in ALPHABET}
    for left, right in zip(stream, stream[1:]):
        outgoing[left].append(right)
    for edges in outgoing.values():
        rng.shuffle(edges)
    stack = [stream[0]]
    circuit = []
    while stack:
        current = stack[-1]
        if outgoing[current]:
            stack.append(outgoing[current].pop())
        else:
            circuit.append(stack.pop())
    surrogate = "".join(reversed(circuit))
    if len(surrogate) != len(stream):
        raise AssertionError("Euler traversal length changed")
    return surrogate


def endpoint_fixed_shuffle(stream: str, rng: random.Random) -> str:
    interior = list(stream[1:-1])
    rng.shuffle(interior)
    return stream[0] + "".join(interior) + stream[-1]


def assert_primary_preservation(source: str, surrogate: str):
    assert len(source) == len(surrogate)
    assert Counter(source) == Counter(surrogate)
    assert source[0] == surrogate[0] and source[-1] == surrogate[-1]
    assert transition_counts(source) == transition_counts(surrogate)
    assert run_count(source) == run_count(surrogate)


def assert_sensitivity_preservation(source: str, surrogate: str):
    assert len(source) == len(surrogate)
    assert Counter(source) == Counter(surrogate)
    assert source[0] == surrogate[0] and source[-1] == surrogate[-1]


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
            streams = {
                name: endpoint_fixed_shuffle(stream, rng) for name, stream in sources.items()
            }
            if trial < 3:
                for name in sources:
                    assert_sensitivity_preservation(sources[name], streams[name])
        else:
            raise ValueError(kind)
        values.append(score_streams(streams)["contrast"])
    return values


def summarize_null(values, observed):
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


def full_data_diagnostics():
    output = {}
    for name, stream in (("DBBI", DBBI), ("FAED", FAED)):
        rows = sorted((pair_loss(stream, pair), "".join(pair)) for pair in PAIRS)
        output[name] = {
            "best_pair": rows[0][1],
            "best_loss": rows[0][0],
            "standing_pair_ranks": {
                target: next(index for index, (_loss, pair) in enumerate(rows, 1) if pair == target)
                for target in (("be",) if name == "DBBI" else ("gi", "eh"))
            },
        }
    return output


def _fixture_stream(pair: tuple[str, str], seed: int, token_count: int):
    top = tuple(symbol for symbol in ALPHABET if symbol not in pair)
    codes = top + tuple(first + second for first in pair for second in ALPHABET)
    weights = (82, 15, 28, 43, 127, 22, 20, 61, 70, 2, 8, 40, 24,
               67, 75, 19, 1, 60, 63, 91, 28, 10, 24, 2, 20)
    total = sum(weights)
    counts = [max(1, round(token_count * weight / total)) for weight in weights]
    tokens = [code for code, count in zip(codes, counts) for _ in range(count)]
    rng = random.Random(seed)
    rng.shuffle(tokens)
    return "".join(tokens)


def fixture(pair: tuple[str, str], seed: int, tokens_per_half: int):
    left = _fixture_stream(pair, seed, tokens_per_half)
    right = _fixture_stream(pair, seed + 1, tokens_per_half)
    return left + right, len(left)


def verify_manifest():
    assert sha256_file(MANIFEST_PATH) == EXPECTED_MANIFEST_SHA256
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["trials_per_null"] == 20_000
    assert manifest["master_seed"] == 45_920_260_830
    assert sha256_bytes(DBBI.encode()) == manifest["source_streams"]["DBBI"]["sha256_utf8"]
    assert sha256_bytes(FAED.encode()) == manifest["source_streams"]["FAED"]["sha256_utf8"]
    for relative, expected in manifest["precedent_digests"].items():
        assert sha256_file(ROOT / relative) == expected
    return manifest


def self_test():
    manifest = verify_manifest()
    assert len(PAIRS) == 36 and PAIRS[0] == ("a", "b") and PAIRS[-1] == ("h", "i")

    from checkerboard_code_ic_oracle import code_ic as precedent_ic
    from checkerboard_code_ic_oracle import segment_codes as precedent_segment

    for stream, pair in ((DBBI, ("b", "e")), (FAED, ("g", "i"))):
        ours = segment_codes(stream, pair)
        theirs = precedent_segment(stream, *pair)
        assert list(ours) == theirs
        assert code_ic(ours) == precedent_ic(theirs)

    rng = random.Random(4591)
    for source in (DBBI, FAED):
        primary = euler_surrogate(source, rng)
        sensitivity = endpoint_fixed_shuffle(source, rng)
        assert_primary_preservation(source, primary)
        assert_sensitivity_preservation(source, sensitivity)
        assert euler_surrogate(source, random.Random(99)) == euler_surrogate(
            source, random.Random(99)
        )

    assert pair_loss("abcd", ("d", "e")) == INVALID_LOSS

    shared_dbbi, shared_dbbi_split = fixture(("b", "e"), 45920, 180)
    shared_faed, shared_faed_split = fixture(("b", "e"), 45930, 700)
    shared = score_streams(
        {"DBBI": shared_dbbi, "FAED": shared_faed},
        {"DBBI": shared_dbbi_split, "FAED": shared_faed_split},
    )
    planted_dbbi, planted_dbbi_split = fixture(("b", "e"), 45940, 180)
    planted_faed, planted_faed_split = fixture(("g", "i"), 45950, 700)
    planted = score_streams(
        {"DBBI": planted_dbbi, "FAED": planted_faed},
        {"DBBI": planted_dbbi_split, "FAED": planted_faed_split},
    )
    assert shared["contrast"] <= 0.002
    assert planted["contrast"] > 0

    print(
        "[*] Phase 459 self-test OK: manifest/source digests, 36-pair universe, "
        "precedent tokenization/IC, null preservation, determinism, dangling loss, "
        "and shared/specialized fixtures passed"
    )
    return {"manifest": manifest, "shared_fixture": shared, "specialized_fixture": planted}


def run(trials: int | None = None):
    manifest = verify_manifest()
    count = manifest["trials_per_null"] if trials is None else trials
    if count != manifest["trials_per_null"]:
        raise ValueError("production run must use the frozen trial count")
    self_test()
    seed = manifest["master_seed"]

    # Frozen ordering: both null populations finish before real scoring.
    primary_values = null_population("euler", count, seed + 1)
    sensitivity_values = null_population("endpoint_shuffle", count, seed + 2)
    observed = score_streams({"DBBI": DBBI, "FAED": FAED})
    contrast = observed["contrast"]
    primary = summarize_null(primary_values, contrast)
    sensitivity = summarize_null(sensitivity_values, contrast)
    threshold = manifest["promotion_threshold"]
    passes = [primary["empirical_p"] <= threshold, sensitivity["empirical_p"] <= threshold]
    if contrast > 0 and all(passes):
        decision = "robust_specialization"
    elif contrast > 0 and sum(passes) == 1:
        decision = "null_sensitive"
    else:
        decision = "no_calibrated_specialization"

    return {
        "phase": 459,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "candidate_pair_count": len(PAIRS),
        "observed": observed,
        "full_data_diagnostics_only": full_data_diagnostics(),
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
    started = time.monotonic()
    null_population("euler", trials, 45999)
    elapsed = time.monotonic() - started
    projected = elapsed * 2 * 20_000 / trials
    print(f"[*] benchmark: {trials} primary-null trials in {elapsed:.3f}s")
    print(f"[*] projected two-null production time: {projected:.1f}s")
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
