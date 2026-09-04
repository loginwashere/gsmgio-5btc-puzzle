#!/usr/bin/env python3
"""Phase 465: closed-system Phase-1 credential running-key audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from data import DBBI, FAED
from dbbi_faed_gronsfeld_progressive_audit import (
    gronsfeld_shift_raw,
    keyword_to_key9,
    resegment_slots,
)
from dbbi_faed_nihilist_additive_audit import (
    apply_shift,
    hillclimb_slots,
    keyword_to_key25,
    slot_sequence,
)
from first_hint_hash_audit import PHASE1_PASSWORD


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("phase465_phase1_running_key_manifest.json")
RESULT_PATH = Path(__file__).with_name("phase465_result.json")
RAW_TARGETS = {"DBBI": DBBI, "FAED": FAED}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["phase"] == 465
    for row in manifest["inputs"]:
        path = ROOT / row["path"]
        assert path.is_file(), path
        assert sha256_file(path) == row["sha256"], row["path"]
    credential = PHASE1_PASSWORD.decode("ascii")
    assert credential == manifest["credential"]
    assert credential.startswith(manifest["prefix"])
    return manifest


def cyclic(values: list[int], offset: int) -> list[int]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def code_ic(slots: list[int]) -> float:
    if len(slots) < 2:
        return 0.0
    counts = Counter(slots)
    numerator = sum(count * (count - 1) for count in counts.values())
    return numerator / (len(slots) * (len(slots) - 1))


def key_scopes(manifest: dict) -> dict[str, str]:
    credential = manifest["credential"]
    prefix = manifest["prefix"]
    return {
        "full_credential": credential,
        "continuation_after_theflower": credential[len(prefix):],
    }


def routes(manifest: dict, target: str) -> list[tuple[str, str, str]]:
    return [
        (e1, e2, topology)
        for e1, e2 in manifest["targets"][target]["escape_pairs"]
        for topology in manifest["topologies"]
    ]


def transformed_slots(
    raw: str,
    insertion: str,
    key: str,
    offset: int,
    sign: int,
    route: tuple[str, str, str],
) -> list[int] | None:
    e1, e2, topology = route
    if insertion == "raw_base9":
        key_values = cyclic(keyword_to_key9(key), offset)
        shifted = gronsfeld_shift_raw(raw, key_values, sign)
        return resegment_slots(shifted, e1, e2, topology)
    if insertion == "code_slot25":
        base = slot_sequence(raw, e1, e2, topology)
        if base is None:
            return None
        key_values = cyclic(keyword_to_key25(key), offset)
        return apply_shift(base, key_values, sign)
    raise AssertionError(insertion)


def structural_config(
    manifest: dict,
    target: str,
    scope_name: str,
    key: str,
    insertion: str,
    sign: int,
) -> dict:
    expected_ic = manifest["english_code_ic"]
    raw = RAW_TARGETS[target]
    offset_rows = []
    for offset in range(len(key)):
        candidates = []
        for route in routes(manifest, target):
            slots = transformed_slots(raw, insertion, key, offset, sign, route)
            if slots is None:
                continue
            ic = code_ic(slots)
            candidates.append({
                "route": list(route),
                "slot_count": len(slots),
                "code_ic": ic,
                "ic_distance": abs(ic - expected_ic),
                "slots": slots,
            })
        if not candidates:
            offset_rows.append({"offset": offset, "valid": False})
            continue
        best = min(candidates, key=lambda row: (row["ic_distance"], row["route"]))
        offset_rows.append({"offset": offset, "valid": True, **best})

    valid = [row for row in offset_rows if row["valid"]]
    ranked = sorted(valid, key=lambda row: (row["ic_distance"], row["offset"]))
    for rank, row in enumerate(ranked, 1):
        row["structural_rank"] = rank
    zero = next(row for row in offset_rows if row["offset"] == 0)
    return {
        "target": target,
        "key_scope": scope_name,
        "key_length": len(key),
        "insertion": insertion,
        "sign": sign,
        "valid_offset_count": len(valid),
        "offset_zero_rank": zero.get("structural_rank"),
        "offset_zero": {key: value for key, value in zero.items() if key != "slots"},
        "ranked_offsets": [
            {key: value for key, value in row.items() if key != "slots"}
            for row in ranked
        ],
        "_offset_rows": offset_rows,
    }


def tier2_review(manifest: dict, config: dict) -> dict:
    budget = manifest["tier2_budget"]
    rows = config["_offset_rows"]
    controls = [row for row in rows if row["valid"] and row["offset"] != 0]
    controls.sort(key=lambda row: (row["ic_distance"], row["offset"]))
    selected = [next(row for row in rows if row["offset"] == 0)] + controls[
        : manifest["tier2_control_count"]
    ]
    seed_passes = []
    for seed in budget["seed_passes"]:
        scored = []
        for row in selected:
            best = hillclimb_slots(
                row["slots"],
                budget["iterations"],
                budget["restarts"],
                seed=seed,
            )
            scored.append({
                "offset": row["offset"],
                "route": row["route"],
                "score": best[0],
                "decoded": best[1],
            })
        ranked = sorted(scored, key=lambda row: (-row["score"], row["offset"]))
        seed_passes.append({
            "seed": seed,
            "offset_zero_rank": next(
                rank for rank, row in enumerate(ranked, 1) if row["offset"] == 0
            ),
            "ranked": ranked,
        })
    return {
        "target": config["target"],
        "key_scope": config["key_scope"],
        "insertion": config["insertion"],
        "sign": config["sign"],
        "seed_passes": seed_passes,
        "offset_zero_tier2_rank1_both_seeds": all(
            row["offset_zero_rank"] == 1 for row in seed_passes
        ),
        "manual_plaintext_gate": None,
    }


def audit(run_tier2: bool = True) -> dict:
    manifest = load_manifest()
    configs = []
    for target in manifest["targets"]:
        for scope_name, key in key_scopes(manifest).items():
            for insertion in manifest["insertions"]:
                for sign in manifest["signs"]:
                    configs.append(
                        structural_config(
                            manifest, target, scope_name, key, insertion, sign
                        )
                    )
    eligible = [
        row for row in configs
        if row["target"] == "FAED" and row["offset_zero_rank"] == 1
    ]
    tier2 = [tier2_review(manifest, row) for row in eligible] if run_tier2 else []
    public_configs = []
    for row in configs:
        public_configs.append({key: value for key, value in row.items() if key != "_offset_rows"})
    return {
        "phase": 465,
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "input_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "key_lengths": {name: len(key) for name, key in key_scopes(manifest).items()},
        "structural_configs": public_configs,
        "faed_offset_zero_rank1_count": len(eligible),
        "tier2_reviews": tier2,
        "automatic_promotion": False,
        "oracle_calls": 0,
        "password_candidates": 0,
        "verdict": (
            "manual_review_required" if tier2 else "no_offset_zero_structural_gate"
        ),
    }


def self_test() -> None:
    manifest = load_manifest()
    scopes = key_scopes(manifest)
    assert len(scopes["full_credential"]) == 53
    assert len(scopes["continuation_after_theflower"]) == 44
    assert cyclic([1, 2, 3], 1) == [2, 3, 1]
    assert abs(code_ic([0, 0, 1, 1]) - 1 / 3) < 1e-15
    key = scopes["full_credential"]
    shifted = transformed_slots(DBBI, "raw_base9", key, 0, 1, ("b", "e", "top_first"))
    assert shifted is None or all(0 <= value < 25 for value in shifted)
    base = transformed_slots(DBBI, "code_slot25", key, 0, 1, ("b", "e", "top_first"))
    assert base and all(0 <= value < 25 for value in base)
    print("[*] Phase 465 self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--structural-only", action="store_true")
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result = audit(run_tier2=not args.structural_only)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "faed_offset_zero_rank1_count": result["faed_offset_zero_rank1_count"],
        "tier2_review_count": len(result["tier2_reviews"]),
        "verdict": result["verdict"],
        "oracle_calls": result["oracle_calls"],
    }, indent=2))
    print(f"[*] wrote {args.output}")


if __name__ == "__main__":
    main()
