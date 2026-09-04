#!/usr/bin/env python3
"""Phase 468 known-parts structural cross-reference.

Three outputs, per the frozen protocol (doc/Brainstorms/2026-09-01 -
Phase 468 Known-Parts Cross-Reference Protocol.md):

1. A typed inventory matrix (descriptive only) crossing established
   outputs against open-gate slots; only `parameter_value` slots are
   value-fillable, everything else resolves not_applicable.
2. A bounded arithmetic result on `31` (G-MSL-001 only): no exact
   nondegenerate rectangular factorization exists, plus a finite
   operation-table cross-check against {7,13,91}.
3. Two separated executable lanes: Lane A (FF67/ASCII/escape-pair
   calibration, two hypotheses, no comparison claim) and Lane B (G-GGN-001
   scalar delta, three interpretations reported separately).

No thematic reasoning anywhere -- only mechanical type/arithmetic facts
and calibrated statistics. No password material, decryptions beyond the
existing exact-target address check, or oracle calls.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase453_false_discovery_calibration import (  # noqa: E402
    holm_adjust,
    multiply,
    orientations,
)
from binary_key_material_backfill import private_key_details  # noqa: E402
from raw_key_chunk_audit import known_targets  # noqa: E402
import bip32_authenticated_number_paths_audit as bip32_audit  # noqa: E402

import phase468_known_parts_catalog as catalog  # noqa: E402

MANIFEST_PATH = SCRIPT_DIR / "phase468_manifest.json"
RESULT_PATH = SCRIPT_DIR / "phase468_result.json"
# Frozen once the manifest is written (Fix 5 sequencing); checked on load.
EXPECTED_MANIFEST_SHA256 = "0d52c76f989a326901aeb6a812b3cb0487f455178701030cdb5e2b9a587ec15b"

DIMENSION_FACTS = (7, 13, 31, 91)
OBSERVED_DIGITS = (5, 7, 4, 0, 6, 1)
ASCII_S_PRIMARY = frozenset({103, 105})       # g, i
ASCII_S_UNION = frozenset({101, 103, 104, 105})  # e, g, h, i
ALPHA = 0.005
PRIMARY_TRIALS = 100_000


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def load_manifest() -> dict:
    if sha256_path(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("Phase 468 manifest drifted or is unset")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["phase"] != 468:
        raise AssertionError("invalid Phase 468 manifest")
    for row in manifest["pinned_inputs"]:
        if sha256_path(ROOT / row["path"]) != row["sha256"]:
            raise AssertionError(f"pinned input drifted: {row['path']}")
    return manifest


# --- Output 1: typed inventory (descriptive) --------------------------

VALUE_ELIGIBLE_CLASSES = {"authenticated_output", "authenticated_derived", "reproduced_conditional"}


def typed_inventory() -> dict:
    eligible = [row for row in catalog.ESTABLISHED_OUTPUTS if row["evidence_class"] in VALUE_ELIGIBLE_CLASSES]
    ineligible = [row for row in catalog.ESTABLISHED_OUTPUTS if row["evidence_class"] not in VALUE_ELIGIBLE_CLASSES]
    gate_matrix = {}
    for gate in catalog.OPEN_GATE_SLOTS:
        if gate.get("excluded"):
            gate_matrix[gate["gate"]] = {"excluded": gate["excluded"]}
            continue
        slot_rows = {}
        for slot in gate["slots"]:
            if slot["kind"] != "parameter_value":
                slot_rows[slot["name"]] = {"kind": slot["kind"], "value_fillable": False, "status": "not_applicable"}
            else:
                slot_rows[slot["name"]] = {
                    "kind": slot["kind"],
                    "value_fillable": True,
                    "candidate_established_outputs": [row["id"] for row in eligible],
                }
        gate_matrix[gate["gate"]] = slot_rows
    return {
        "eligible_output_count": len(eligible),
        "ineligible_output_count": len(ineligible),
        "eligible_ids": [row["id"] for row in eligible],
        "ineligible_ids_by_class": {
            cls: [row["id"] for row in ineligible if row["evidence_class"] == cls]
            for cls in sorted({row["evidence_class"] for row in ineligible})
        },
        "gate_slot_matrix": gate_matrix,
        "parameter_value_slot_count": sum(
            1 for gate in catalog.OPEN_GATE_SLOTS if not gate.get("excluded")
            for slot in gate["slots"] if slot["kind"] == "parameter_value"
        ),
    }


# --- Output 2: bounded 31 arithmetic -----------------------------------

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def rectangular_factorizations(n: int) -> list[tuple[int, int]]:
    return [(d, n // d) for d in range(2, n) if n % d == 0 and d <= n // d]


def arithmetic_31() -> dict:
    base = sorted(DIMENSION_FACTS)
    table = []
    flagged = []
    target_set = set(base)
    for a, b in itertools.combinations(base, 2):
        ratio_ab = a / b if b and a % b == 0 else None
        ratio_ba = b / a if a and b % a == 0 else None
        row = {
            "pair": [a, b],
            "sum": a + b,
            "difference": {"a_minus_b": a - b, "b_minus_a": b - a},
            "product": a * b,
            "ratio": {"a_div_b": ratio_ab, "b_div_a": ratio_ba},
            "mod": {"a_mod_b": a % b, "b_mod_a": b % a},
        }
        table.append(row)
        results = [row["sum"], row["difference"]["a_minus_b"], row["difference"]["b_minus_a"],
                   row["product"], row["mod"]["a_mod_b"], row["mod"]["b_mod_a"]]
        if ratio_ab is not None:
            results.append(ratio_ab)
        if ratio_ba is not None:
            results.append(ratio_ba)
        for value in results:
            if value in target_set:
                flagged.append({"pair": [a, b], "value": value})
    return {
        "n": 31,
        "is_prime": is_prime(31),
        "nondegenerate_rectangular_factorizations": rectangular_factorizations(31),
        "operation_table": table,
        "flagged_equalities_against_established_set": flagged,
        "does_not_rule_out": [
            "padding", "1x31_or_31x1_rail", "ragged_rows",
            "sub_selection_from_larger_matrix", "independently_supplied_dimensions",
        ],
    }


# --- Output 3, Lane A: FF67 / ASCII / escape-pair conjunction ----------

def event_hit(pair: tuple[int, int], s: frozenset[int]) -> bool:
    x, y = pair
    return (x == 255 and y in s) or (y == 255 and x in s)


def digit_tuple_rows(digits: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    matrix = (digits[:3], digits[3:])
    vector = (sum(digits), sum(digits[:3]), sum(digits[3:]))
    return tuple(
        multiply(oriented, ordered)
        for oriented in orientations(matrix)
        for ordered in itertools.permutations(vector)
    )


def digit_tuple_hit(digits: tuple[int, ...], s: frozenset[int]) -> bool:
    return any(event_hit(row, s) for row in digit_tuple_rows(digits))


def generate_populations(master_seed: int) -> dict:
    rng = random.Random(master_seed)
    sampled = [tuple(rng.sample(range(10), 6)) for _ in range(PRIMARY_TRIALS)]
    exhaustive = list(itertools.permutations(range(10), 6))
    return {"sampled_100000": sampled, "exhaustive_151200": exhaustive}


def empirical_tail_plus_one(extreme: int, trials: int) -> float:
    return (extreme + 1) / (trials + 1)


def lane_a(populations: dict) -> dict:
    observed = {
        "digits": list(OBSERVED_DIGITS),
        "hit_g_i_primary": digit_tuple_hit(OBSERVED_DIGITS, ASCII_S_PRIMARY),
        "hit_union_e_g_h_i": digit_tuple_hit(OBSERVED_DIGITS, ASCII_S_UNION),
    }
    populations_result = {}
    for pop_name, population in populations.items():
        raw_p = {}
        counts = {}
        for hyp_name, s in (("g_i_primary", ASCII_S_PRIMARY), ("union_e_g_h_i", ASCII_S_UNION)):
            extreme = sum(1 for digits in population if digit_tuple_hit(digits, s))
            trials = len(population)
            raw_p[hyp_name] = empirical_tail_plus_one(extreme, trials)
            counts[hyp_name] = {"extreme_count": extreme, "trials": trials}
        holm_p = holm_adjust(raw_p)
        populations_result[pop_name] = {
            "counts": counts,
            "raw_p": raw_p,
            "holm_p": holm_p,
            "rejections_holm_p_lt_alpha": {h: holm_p[h] < ALPHA for h in holm_p},
        }
    salph_103_convention_fact = {
        "conventions_tested": 4,
        "conventions_giving_103": 1,
        "note": "non-random enumerated fact, not a calibrated p-value; reported side-by-side, not combined",
    }
    return {
        "observed": observed,
        "alpha": ALPHA,
        "decision_rule": "holm_adjusted_p_lt_alpha_strict",
        "hypotheses": {"g_i_primary": sorted(ASCII_S_PRIMARY), "union_e_g_h_i": sorted(ASCII_S_UNION)},
        "populations": populations_result,
        "salph_103_convention_fact": salph_103_convention_fact,
        "conclusion_scope": "bears on FF67/G-ESC-001 relationship only, not G-MSL-001; no pair-selection claim",
    }


# --- Output 3, Lane B: G-GGN-001 scalar delta ---------------------------

def normalize_direct_bytes(candidate: dict) -> bytes | None:
    if candidate.get("direct_scalar_status") == "not_applicable_too_long":
        return None
    if candidate["type"] == "integer":
        value = candidate["value"]
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big") if value else b"\x00"
    elif candidate["type"] == "text":
        raw = candidate["canonical_text"].encode("utf-8")
    else:
        raise ValueError(f"unsupported candidate type: {candidate['type']!r}")
    if len(raw) > 32:
        return None
    return raw.rjust(32, b"\x00")


def scalar_check(key_bytes: bytes | None, targets_bytes: dict[bytes, str]) -> dict:
    if key_bytes is None:
        return {"status": "not_applicable_too_long"}
    details = private_key_details(key_bytes)
    if details is None:
        return {"status": "checked", "valid_scalar": False, "hit": None}
    hit = None
    for address_type, info in details.items():
        h = bytes.fromhex(info["hash160"])
        if h in targets_bytes:
            hit = {"address_type": address_type, "target_label": targets_bytes[h], **info}
    return {"status": "checked", "valid_scalar": True, "hit": hit}


def lane_b() -> dict:
    targets_hex = known_targets()
    targets_bytes = {bytes.fromhex(h): label for h, label in targets_hex.items()}
    records = []
    for cand in catalog.LANE_B_CANDIDATES:
        text = cand["canonical_text"]
        direct_bytes = normalize_direct_bytes(cand)
        sha256_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        record = {
            "id": cand["id"],
            "type": cand["type"],
            "canonical_text": text,
            "direct_bytes_as_scalar": scalar_check(direct_bytes, targets_bytes),
            "sha256_as_scalar": scalar_check(sha256_bytes, targets_bytes),
            "bip32_seed_form_path_enumeration": bip32_audit.run(candidates=[text], known_targets=targets_bytes),
        }
        records.append(record)
    total_hits = sum(
        (1 if r["direct_bytes_as_scalar"].get("hit") else 0)
        + (1 if r["sha256_as_scalar"].get("hit") else 0)
        + r["bip32_seed_form_path_enumeration"]["total_hits"]
        for r in records
    )
    return {
        "target_set_size": len(targets_hex),
        "target_set_source": "raw_key_chunk_audit.known_targets()",
        "candidates": records,
        "excluded_candidates": list(catalog.EXCLUDED_LANE_B_CANDIDATES),
        "total_hits": total_hits,
    }


# --- top-level report ----------------------------------------------------

def build_report(manifest: dict) -> dict:
    populations = generate_populations(manifest["lane_a"]["master_seed"])
    return {
        "phase": 468,
        "date": manifest["date"],
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "output_1_typed_inventory": typed_inventory(),
        "output_2_arithmetic_31": arithmetic_31(),
        "output_3_lane_a": lane_a(populations),
        "output_3_lane_b": lane_b(),
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "decryptions_attempted": 0,
    }


def structural_self_test(manifest: dict) -> None:
    """Invariant checks only -- no outcome-dependent assertions."""
    populations = generate_populations(manifest["lane_a"]["master_seed"])
    assert len(populations["sampled_100000"]) == PRIMARY_TRIALS
    assert len(populations["exhaustive_151200"]) == 151200
    assert len(set(populations["exhaustive_151200"])) == 151200
    assert all(len(t) == 6 and len(set(t)) == 6 for t in populations["exhaustive_151200"][:100])
    inventory = typed_inventory()
    assert inventory["parameter_value_slot_count"] == 2  # G-MSL-001 dims + G-GGN-001 scalar k
    arithmetic = arithmetic_31()
    assert arithmetic["is_prime"] is True
    assert arithmetic["nondegenerate_rectangular_factorizations"] == []
    for cand in catalog.LANE_B_CANDIDATES:
        assert cand["id"] not in {"youwon", "exec_order_13224", "btcseed_p90_p91_q472"}
    print("[*] Phase 468 structural self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--structural-only", action="store_true",
                         help="run only pre-manifest-freeze structural checks")
    args = parser.parse_args()

    if args.structural_only:
        # Bootstrap mode: manifest not frozen yet, use a throwaway seed
        # solely to validate population shape/size before freezing.
        structural_self_test({"lane_a": {"master_seed": 468468468}})
        return

    manifest = load_manifest()
    if args.self_test:
        structural_self_test(manifest)
    report = build_report(manifest)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output_2_is_prime_31": report["output_2_arithmetic_31"]["is_prime"],
        "output_2_factorizations": report["output_2_arithmetic_31"]["nondegenerate_rectangular_factorizations"],
        "lane_a_rejections": {
            pop: r["rejections_holm_p_lt_alpha"]
            for pop, r in report["output_3_lane_a"]["populations"].items()
        },
        "lane_b_total_hits": report["output_3_lane_b"]["total_hits"],
    }, indent=2))


if __name__ == "__main__":
    main()
