#!/usr/bin/env python3
"""Phase 518: positional cross-stream correspondence gate for DBBI/FAED.

Prerequisite gate for the Post-Phase-452 Portfolio's asymmetric DBBI/FAED
generator tournament (item 1). Tests whether *any* undirected positional
correspondence exists between DBBI and FAED at coarse, DBBI-native block
granularities, beyond what each stream's own internal structure explains.
No operator is proposed, no plaintext/password/key material is generated,
and no AES oracle or English-language score is used. Any result is
corroboration_only and cannot reopen or close G-YIN-001.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
import zlib
from pathlib import Path

from data import DBBI, FAED
from dbbi_faed_base81_token_audit import mutual_information
from phase459_dual_stream_escape_pair_calibration import (
    assert_primary_preservation,
    assert_sensitivity_preservation,
    euler_surrogate,
    endpoint_fixed_shuffle,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("phase518_manifest.json")
DEFAULT_OUTPUT = Path(__file__).with_name("phase518_result.json")
ALPHABET = "abcdefghi"
GRANULARITIES = (91, 13)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def blocks(stream: str, k: int):
    n = len(stream)
    bounds = [(j * n) // k for j in range(k + 1)]
    return tuple(stream[bounds[j] : bounds[j + 1]] for j in range(k))


def mode_symbol(block: str) -> str:
    counts = {symbol: 0 for symbol in ALPHABET}
    for symbol in block:
        counts[symbol] += 1
    best = max(counts.values())
    for symbol in ALPHABET:
        if counts[symbol] == best:
            return symbol
    raise AssertionError("unreachable")


def block_mode_sequence(stream: str, k: int):
    return tuple(mode_symbol(block) for block in blocks(stream, k))


def observed_statistic(dbbi: str, faed: str, k: int) -> float:
    dbbi_modes = block_mode_sequence(dbbi, k)
    faed_modes = block_mode_sequence(faed, k)
    assert len(dbbi_modes) == len(faed_modes) == k
    return mutual_information(tuple(zip(dbbi_modes, faed_modes)))


def observed_all(dbbi: str, faed: str):
    return {k: observed_statistic(dbbi, faed, k) for k in GRANULARITIES}


def null_population(kind: str, k: int, trials: int, seed: int):
    rng = random.Random(seed)
    values = []
    for trial in range(trials):
        if kind == "euler":
            dbbi_s = euler_surrogate(DBBI, rng)
            faed_s = euler_surrogate(FAED, rng)
            if trial < 3:
                assert_primary_preservation(DBBI, dbbi_s)
                assert_primary_preservation(FAED, faed_s)
        elif kind == "endpoint_shuffle":
            dbbi_s = endpoint_fixed_shuffle(DBBI, rng)
            faed_s = endpoint_fixed_shuffle(FAED, rng)
            if trial < 3:
                assert_sensitivity_preservation(DBBI, dbbi_s)
                assert_sensitivity_preservation(FAED, faed_s)
        else:
            raise ValueError(kind)
        values.append(observed_statistic(dbbi_s, faed_s, k))
    return values


def summarize(values, observed):
    ordered = sorted(values)
    extreme = sum(value >= observed for value in values)
    return {
        "trials": len(values),
        "extreme_count": extreme,
        "empirical_p": (extreme + 1) / (len(values) + 1),
        "minimum": ordered[0],
        "median": ordered[len(ordered) // 2],
        "q95": ordered[int(0.95 * (len(ordered) - 1))],
        "maximum": ordered[-1],
    }


def decide_k(observed, primary_summary, sensitivity_summary, threshold):
    passes = (
        primary_summary["empirical_p"] <= threshold,
        sensitivity_summary["empirical_p"] <= threshold,
    )
    above_medians = observed > primary_summary["median"] and observed > sensitivity_summary["median"]
    if above_medians and all(passes):
        return "robust_correspondence"
    if above_medians and sum(passes) == 1:
        return "null_sensitive"
    return "no_calibrated_correspondence"


def phase_level_decision(decisions_by_k):
    """K=91 is the sole primary gate (corrected same-day, see protocol doc:
    K=13 gives only 13 aligned samples, too few for the MI estimator to
    reliably clear p<=0.005 even under a by-construction perfect fixture).
    K=13 is reported for diagnostic consistency only."""
    return decisions_by_k[91]


def verify_manifest():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["trials_per_null"] == 20_000
    assert manifest["master_seed"] == 51_820_260_917
    assert manifest["granularities"] == [91, 13]
    assert sha256_bytes(DBBI.encode()) == manifest["source_streams"]["DBBI"]["sha256_utf8"]
    assert sha256_bytes(FAED.encode()) == manifest["source_streams"]["FAED"]["sha256_utf8"]
    for relative, expected in manifest["precedent_digests"].items():
        assert sha256_file(ROOT / relative) == expected
    protocol_path = ROOT / manifest["protocol"]
    assert sha256_file(protocol_path) == manifest["protocol_sha256"]
    return manifest


def run_gate(streams: dict, k: int, trials: int, seed: int):
    primary_values = null_population("euler", k, trials, seed + 1)
    sensitivity_values = null_population("endpoint_shuffle", k, trials, seed + 2)
    observed = observed_statistic(streams["DBBI"], streams["FAED"], k)
    primary = summarize(primary_values, observed)
    sensitivity = summarize(sensitivity_values, observed)
    decision = decide_k(observed, primary, sensitivity, 0.005)
    return {
        "k": k,
        "observed_mi_bits": observed,
        "primary_euler": primary,
        "sensitivity_endpoint_shuffle": sensitivity,
        "decision": decision,
    }


# ---------------------------------------------------------------------------
# Fixtures for the required pre-interpretation controls.
# ---------------------------------------------------------------------------

def _weighted_stream(rng: random.Random, length: int, weights):
    symbols = list(ALPHABET)
    return "".join(rng.choices(symbols, weights=weights, k=length))


def independent_fixture(seed: int):
    """Two streams, matching lengths/marginals, no positional relationship."""
    rng = random.Random(seed)
    weights = (9, 8, 7, 6, 5, 4, 3, 2, 1)
    dbbi = _weighted_stream(rng, 91, weights)
    faed = _weighted_stream(rng, 570, weights)
    return {"DBBI": dbbi, "FAED": faed}


def planted_correspondence_fixture(seed: int):
    """DBBI-like stream whose symbols deterministically drive FAED-like blocks."""
    rng = random.Random(seed)
    dbbi = "".join(rng.choice(ALPHABET) for _ in range(91))
    faed_blocks = []
    n = 570
    k = 91
    for j in range(k):
        lo, hi = (j * n) // k, ((j + 1) * n) // k
        block_len = hi - lo
        driver = dbbi[j]
        # deterministic: repeat the driver symbol plus one off-symbol filler
        filler = ALPHABET[(ALPHABET.index(driver) + 1) % 9]
        block = (driver * (block_len - 1) + filler) if block_len > 0 else ""
        faed_blocks.append(block)
    faed = "".join(faed_blocks)
    assert len(faed) == 570
    return {"DBBI": dbbi, "FAED": faed}


def self_test():
    manifest = verify_manifest()

    # Block partition tiling determinism.
    for length in (91, 570):
        for k in GRANULARITIES:
            n = [(j * length) // k for j in range(k + 1)]
            assert n[0] == 0 and n[-1] == length
            assert all(b <= c for b, c in zip(n, n[1:]))
    assert len(blocks(DBBI, 91)) == 91
    assert all(len(b) == 1 for b in blocks(DBBI, 91))
    assert len(blocks(DBBI, 13)) == 13
    assert all(len(b) == 7 for b in blocks(DBBI, 13))
    assert len(blocks(FAED, 91)) == 91
    assert len(blocks(FAED, 13)) == 13
    assert sum(len(b) for b in blocks(FAED, 91)) == 570
    assert sum(len(b) for b in blocks(FAED, 13)) == 570

    # mutual_information self-test reproduction.
    dependent = tuple((index, index) for index in range(9) for _ in range(3))
    independent = tuple((left, right) for left in range(9) for right in range(9))
    assert mutual_information(dependent) > mutual_information(independent)

    # Null invariants.
    rng = random.Random(5182)
    for source in (DBBI, FAED):
        assert_primary_preservation(source, euler_surrogate(source, rng))
        assert_sensitivity_preservation(source, endpoint_fixed_shuffle(source, rng))

    # Determinism.
    assert euler_surrogate(DBBI, random.Random(99)) == euler_surrogate(DBBI, random.Random(99))

    # mode_symbol tie-break.
    assert mode_symbol("aabb") == "a"
    assert mode_symbol("bcca") == "c"

    print("[*] Phase 518 self-test OK: manifest/protocol digests, block tiling, "
          "MI self-test, null invariants, and determinism passed")
    return {"manifest_present": True}


def run_controls(trials: int, seed: int):
    independent = independent_fixture(seed + 1000)
    planted = planted_correspondence_fixture(seed + 2000)
    results = {}
    for name, streams in (("independent_fixture", independent), ("planted_fixture", planted)):
        # For fixtures we run a reduced trial count for speed; the phase-level
        # decision logic is identical to the production path.
        by_k = {}
        for k in GRANULARITIES:
            observed = observed_statistic(streams["DBBI"], streams["FAED"], k)
            primary_rng_seed = seed + zlib.crc32(f"{name}:{k}:euler".encode()) % 1_000_000
            sensitivity_rng_seed = seed + zlib.crc32(f"{name}:{k}:shuffle".encode()) % 1_000_000
            primary_values = _fixture_null(streams, k, trials, primary_rng_seed, "euler")
            sensitivity_values = _fixture_null(streams, k, trials, sensitivity_rng_seed, "endpoint_shuffle")
            primary = summarize(primary_values, observed)
            sensitivity = summarize(sensitivity_values, observed)
            by_k[k] = {
                "observed_mi_bits": observed,
                "decision": decide_k(observed, primary, sensitivity, 0.005),
            }
        results[name] = {
            "by_k": by_k,
            "phase_level_decision": phase_level_decision({k: row["decision"] for k, row in by_k.items()}),
        }
    return results


def _fixture_null(streams: dict, k: int, trials: int, seed: int, kind: str):
    rng = random.Random(seed)
    values = []
    for _ in range(trials):
        if kind == "euler":
            dbbi_s = euler_surrogate(streams["DBBI"], rng)
            faed_s = euler_surrogate(streams["FAED"], rng)
        else:
            dbbi_s = endpoint_fixed_shuffle(streams["DBBI"], rng)
            faed_s = endpoint_fixed_shuffle(streams["FAED"], rng)
        values.append(observed_statistic(dbbi_s, faed_s, k))
    return values


def run(trials: int | None = None):
    manifest = verify_manifest()
    self_test()
    count = manifest["trials_per_null"] if trials is None else trials
    seed = manifest["master_seed"]

    control_results = run_controls(2_000, seed + 500_000)
    assert control_results["independent_fixture"]["phase_level_decision"] == "no_calibrated_correspondence", (
        "harness_failure: independent fixture manufactured correspondence"
    )
    assert control_results["planted_fixture"]["phase_level_decision"] == "robust_correspondence", (
        "harness_failure: planted-correspondence fixture failed to promote"
    )

    streams = {"DBBI": DBBI, "FAED": FAED}
    by_k = {}
    for index, k in enumerate(GRANULARITIES):
        by_k[k] = run_gate(streams, k, count, seed + 10 * (index + 1))

    phase_decision = phase_level_decision({k: row["decision"] for k, row in by_k.items()})

    return {
        "phase": 518,
        "manifest_protocol_sha256": manifest["protocol_sha256"],
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "granularities": GRANULARITIES,
        "controls": control_results,
        "by_k": {str(k): row for k, row in by_k.items()},
        "phase_level_decision": phase_decision,
        "maximum_inference": "corroboration_only_no_gap_closure_no_operator_selection",
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
    null_population("euler", 91, trials, 51899)
    elapsed = time.monotonic() - start
    projected = elapsed * 4 * 20_000 / trials
    print(f"[*] benchmark: {trials} K=91 euler-null trials in {elapsed:.3f}s")
    print(f"[*] projected full production (2 K x 2 nulls x 20000): {projected:.1f}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--benchmark", type=int)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--trials", type=int, default=None)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.benchmark is not None:
        benchmark(args.benchmark)
    elif args.run:
        result = run(args.trials)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"[*] wrote {args.json_out}")
        print(f"[*] phase_level_decision={result['phase_level_decision']}")
        for k, row in result["by_k"].items():
            print(f"    K={k}: observed={row['observed_mi_bits']:.6g} decision={row['decision']}")
    else:
        self_test()


if __name__ == "__main__":
    main()
