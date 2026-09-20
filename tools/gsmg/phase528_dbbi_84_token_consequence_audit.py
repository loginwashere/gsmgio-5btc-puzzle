#!/usr/bin/env python3
"""Phase 528: bounded consequences of DBBI's justified 84-token parse.

This module is deliberately oracle-free.  It reconstructs structural objects,
reruns only Phase 177's invalidated merge/split statistic, and performs exact
membership checks against historical candidate corpora.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI  # noqa: E402
from phase525_dbbi_selection_a_reconstruction import (  # noqa: E402
    enumerate_complete_parses,
    is_prime,
)
from triangular_matrixsumlist_audit import (  # noqa: E402
    BITS,
    LITERAL_BE_STARTS,
    ORIENTATIONS,
    insertion_family,
    paired_bits,
)

PHASE478_MANIFEST = SCRIPT_DIR / "phase478_manifest.jsonl"
PHASE523_BASES = SCRIPT_DIR.parents[1] / "_work/phase523/not_all_covered_bases.txt"
RESULT_PATH = SCRIPT_DIR / "phase528_dbbi_84_token_consequence_result.json"
NULL_TRIALS = 2000
NULL_SEED = 177


def a1i9_sum(text: str) -> int:
    if any(char < "a" or char > "i" for char in text):
        raise ValueError("A1I9 input must contain only a-i")
    return sum(ord(char) - ord("a") + 1 for char in text)


def grouped_parse(tokens: tuple[str, ...]) -> dict:
    groups: list[dict] = []
    payload: list[str] = []
    for logical_position, token in enumerate(tokens, start=1):
        if is_prime(logical_position):
            text = "".join(payload)
            groups.append(
                {
                    "ordinal": len(groups) + 1,
                    "prime_position": logical_position,
                    "host": token,
                    "color": "Y" if token == "be" else "B",
                    "payload": text,
                    "payload_length": len(text),
                    "payload_a1i9_sum": a1i9_sum(text),
                }
            )
            payload = []
        else:
            payload.append(token)
    tail = "".join(payload)
    hosted_residue = "".join(group["payload"] for group in groups)
    rails = {}
    for host in ("b", "be"):
        selected = [group for group in groups if group["host"] == host]
        rails[host] = {
            "group_count": len(selected),
            "group_ordinals": [group["ordinal"] for group in selected],
            "payloads": [group["payload"] for group in selected],
            "payload_lengths": [group["payload_length"] for group in selected],
            "payload_sums": [group["payload_a1i9_sum"] for group in selected],
            "concatenated_payload": "".join(group["payload"] for group in selected),
            "total_payload_length": sum(group["payload_length"] for group in selected),
            "total_a1i9_sum": sum(group["payload_a1i9_sum"] for group in selected),
        }
    return {
        "logical_length": len(tokens),
        "groups": groups,
        "host_colors": "".join(group["color"] for group in groups),
        "hosted_residue": hosted_residue,
        "hosted_residue_length": len(hosted_residue),
        "tail": tail,
        "tail_length": len(tail),
        "full_residue": hosted_residue + tail,
        "full_residue_length": len(hosted_residue) + len(tail),
        "rails": rails,
    }


def parse_family() -> dict[int, dict]:
    family = {
        len(tokens): grouped_parse(tokens)
        for tokens in enumerate_complete_parses(DBBI)
    }
    if sorted(family) != [83, 84]:
        raise AssertionError(f"unexpected parse family: {sorted(family)}")
    return family


def corrected_merge_starts(parse84: dict) -> tuple[int, ...]:
    """Raw offsets of literal BE pairs merged as one 84-parse host token."""
    starts: list[int] = []
    raw_cursor = 0
    for group in parse84["groups"]:
        payload = group["payload"]
        raw_cursor += len(payload)
        if group["host"] == "be":
            starts.append(raw_cursor)
        elif group["host"] != "b":
            raise AssertionError(f"unexpected host: {group['host']!r}")
        raw_cursor += len(group["host"])
    raw_cursor += len(parse84["tail"])
    if raw_cursor != len(DBBI):
        raise AssertionError("84-parse groups and tail do not cover DBBI")
    return tuple(starts)


def merge_gap(bits105: str, orientation: str, merged: set[int]) -> float:
    selectors = paired_bits(bits105, orientation)
    positive = [selectors[index] == "b" for index in LITERAL_BE_STARTS if index in merged]
    negative = [selectors[index] == "b" for index in LITERAL_BE_STARTS if index not in merged]
    return abs(sum(positive) / len(positive) - sum(negative) / len(negative))


def merge_gap_max(bits104: str, merged: set[int]) -> dict:
    best: dict | None = None
    for insertion, bits105 in enumerate(insertion_family(bits104)):
        for orientation in ORIENTATIONS:
            value = merge_gap(bits105, orientation, merged)
            row = {
                "value": value,
                "insertion_zero_based": insertion,
                "orientation": orientation,
            }
            if best is None or (value, -insertion, orientation) > (
                best["value"], -best["insertion_zero_based"], best["orientation"]
            ):
                best = row
    assert best is not None
    return best


def corrected_phase177(parse84: dict, trials: int = NULL_TRIALS, seed: int = NULL_SEED) -> dict:
    merged_tuple = corrected_merge_starts(parse84)
    merged = set(merged_tuple)
    split = tuple(index for index in LITERAL_BE_STARTS if index not in merged)
    real = merge_gap_max(BITS, merged)
    rng = random.Random(seed)
    source = list(BITS)
    exceedances = 0
    for _ in range(trials):
        rng.shuffle(source)
        control = merge_gap_max("".join(source), merged)
        exceedances += control["value"] >= real["value"]
    return {
        "source_phase": 177,
        "changed_metric_only": "merge_gap",
        "merged_be_starts_zero_based": list(merged_tuple),
        "split_be_starts_zero_based": list(split),
        "merged_count": len(merged_tuple),
        "split_count": len(split),
        "real_family_max": real,
        "null_trials": trials,
        "null_seed": seed,
        "tie_inclusive_exceedances": exceedances,
        "familywise_upper_tail_p": (exceedances + 1) / (trials + 1),
        "promotion_bar": 0.005,
        "promoted": (exceedances + 1) / (trials + 1) < 0.005,
    }


def exact_objects(parse83: dict, parse84: dict) -> dict[str, str]:
    blue = parse84["rails"]["b"]["concatenated_payload"]
    yellow = parse84["rails"]["be"]["concatenated_payload"]
    return {
        "historical_hosted_residue_60": parse83["hosted_residue"],
        "parse84_full_residue_61": parse84["full_residue"],
        "parse84_b_host_payload_rail": blue,
        "parse84_be_host_payload_rail": yellow,
        "parse84_b_then_be_payload_rails": blue + yellow,
        "parse84_be_then_b_payload_rails": yellow + blue,
    }


def exact_membership(objects: dict[str, str]) -> dict:
    byte_targets: dict[bytes, list[str]] = {}
    text_targets: dict[str, list[str]] = {}
    for label, value in objects.items():
        byte_targets.setdefault(value.encode("ascii"), []).append(label)
        text_targets.setdefault(value, []).append(label)
    found478 = {label: False for label in objects}
    count478 = 0
    with PHASE478_MANIFEST.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            count478 += 1
            record = json.loads(line)
            raw = base64.b64decode(record["bytes_b64"])
            for label in byte_targets.get(raw, ()):
                found478[label] = True
    found523 = {label: False for label in objects}
    count523 = 0
    with PHASE523_BASES.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            count523 += 1
            value = json.loads(line)
            for label in text_targets.get(value, ()):
                found523[label] = True
    return {
        "phase478_submitted_bytes": {"records": count478, "found": found478},
        "phase523_bases": {"records": count523, "found": found523},
    }


def dependency_inventory() -> list[dict]:
    return [
        {
            "phases": "53/61",
            "object": "historical 83-token guide and 15/8 endpoint profile",
            "effect": "superseded_as_unique_parse_not_numerically_invalidated",
            "reason": "the 83-token parse remains complete, but Phase 525 proves it is not unique",
        },
        {
            "phases": "61/270/442/443/444",
            "object": "split-final-BE 16/7 endpoint-color operator",
            "effect": "strengthened_not_invalidated",
            "reason": "its colors equal the independently justified 84-token host colors exactly",
        },
        {
            "phases": "171/172",
            "object": "83/84 COSMIC block mappings",
            "effect": "already_bran_both_branches_no_rerun",
            "reason": "the full-envelope 84 branch already used the identical final split",
        },
        {
            "phases": "177",
            "object": "eight merged versus two split literal-BE labels",
            "effect": "invalidated_and_rerun",
            "reason": "84-token parsing makes the terminal raw BE split, yielding seven versus three",
        },
        {
            "phases": "270/442/443/444",
            "object": "endpoint projections onto other source strings",
            "effect": "closed_negatives_stand",
            "reason": "their selected color sequence and positioning rule do not change",
        },
    ]


def audit(run_membership: bool = True, trials: int = NULL_TRIALS) -> dict:
    family = parse_family()
    parse83, parse84 = family[83], family[84]
    payloads83 = [group["payload"] for group in parse83["groups"]]
    payloads84 = [group["payload"] for group in parse84["groups"]]
    if payloads83 != payloads84:
        raise AssertionError("group payloads unexpectedly differ between parses")
    if parse84["full_residue"] != parse83["full_residue"] + "e":
        raise AssertionError("84 residue is not the 83 residue plus terminal e")
    objects = exact_objects(parse83, parse84)
    report = {
        "identity": {
            "dbbi_length": len(DBBI),
            "dbbi_sha256": hashlib.sha256(DBBI.encode("ascii")).hexdigest(),
            "complete_parse_lengths": sorted(family),
        },
        "parse83": parse83,
        "parse84": parse84,
        "comparison": {
            "group_payloads_identical": True,
            "hosted_residue_identical": parse83["hosted_residue"] == parse84["hosted_residue"],
            "final_host_change": [parse83["groups"][-1]["host"], parse84["groups"][-1]["host"]],
            "new_unhosted_tail": parse84["tail"],
        },
        "exact_objects": objects,
        "dependency_inventory": dependency_inventory(),
        "corrected_phase177": corrected_phase177(parse84, trials=trials),
        "membership": exact_membership(objects) if run_membership else None,
        "scope": {
            "aes_called": False,
            "faed_accessed": False,
            "password_expansion_performed": False,
            "language_score_used": False,
        },
    }
    return report


def self_test() -> None:
    family = parse_family()
    assert family[83]["host_colors"] == "BBBBYBBBYYBBBBYBBYYBBYY"
    assert family[84]["host_colors"] == "BBBBYBBBYYBBBBYBBYYBBYB"
    assert family[83]["full_residue_length"] == 60
    assert family[84]["full_residue_length"] == 61
    assert family[84]["tail"] == "e"
    assert family[84]["rails"]["b"]["group_count"] == 16
    assert family[84]["rails"]["be"]["group_count"] == 7
    assert corrected_merge_starts(family[84]) == (10, 23, 30, 49, 64, 71, 84)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-membership", action="store_true")
    parser.add_argument("--trials", type=int, default=NULL_TRIALS)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 528 self-test passed")
        return 0
    report = audit(run_membership=not args.no_membership, trials=args.trials)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    corrected = report["corrected_phase177"]
    print(f"[*] wrote {args.output}")
    print(
        "[*] corrected Phase 177 merge-gap: "
        f"{corrected['tie_inclusive_exceedances']}/{corrected['null_trials']}, "
        f"p={corrected['familywise_upper_tail_p']:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
