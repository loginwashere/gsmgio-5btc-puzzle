#!/usr/bin/env python3
"""Development search using exact-crib consistent-prefix length as objective."""
from __future__ import annotations

import argparse
import json
import math

import phase484a_raw_symbol_vic_solver as base
import phase512a_transposition_crib_feasibility as phase512a


SEED = 0x512C001


def consistent_prefix_length(observed: str, width: int, order,
                             pair: tuple[str, str], crib: str,
                             raw_start: int) -> int:
    raw = base.Geometry(len(observed), width).decrypt(observed, order)
    code_to_letter = {}
    letter_to_code = {}
    position = raw_start
    matched = 0
    escapes = frozenset(pair)
    while matched < len(crib) and position < len(raw):
        first = raw[position]
        if first in escapes:
            if position + 1 >= len(raw):
                break
            code = raw[position:position + 2]
            position += 2
        else:
            code = first
            position += 1
        letter = crib[matched]
        if code in code_to_letter and code_to_letter[code] != letter:
            break
        if letter in letter_to_code and letter_to_code[letter] != code:
            break
        code_to_letter[code] = letter
        letter_to_code[letter] = code
        matched += 1
    return matched


def greedy_search(fixture: dict, restarts: int = 32,
                  max_rounds: int = 100) -> dict:
    width = fixture["width"]
    truth = tuple(fixture["order"])
    best = None
    traces = []
    for restart in range(restarts):
        rng = base.PCG32(base.derive_seed(
            SEED, width, tuple(phase512a.CRIBS).index(fixture["crib_id"]), restart))
        order = rng.permutation(width)
        current = consistent_prefix_length(
            fixture["observed"], width, order, phase512a.PAIR,
            fixture["crib"], fixture["planted_raw_offset"])
        trace = [current]
        for _ in range(max_rounds):
            choices = []
            for left in range(width - 1):
                for right in range(left + 1, width):
                    candidate = list(order)
                    candidate[left], candidate[right] = candidate[right], candidate[left]
                    score = consistent_prefix_length(
                        fixture["observed"], width, candidate, phase512a.PAIR,
                        fixture["crib"], fixture["planted_raw_offset"])
                    if score > current:
                        choices.append((score, -left, -right, candidate))
            if not choices:
                break
            score, _, _, order = max(choices)
            current = score
            trace.append(current)
            if current == len(fixture["crib"]):
                break
        record = {
            "restart": restart,
            "prefix_length": current,
            "exact_crib": current == len(fixture["crib"]),
            "exact_order": tuple(order) == truth,
            "trace": trace,
            "order": order,
        }
        traces.append(record)
        if best is None or (record["prefix_length"], record["exact_order"]) > (
                best["prefix_length"], best["exact_order"]):
            best = record
    return {
        "crib_id": fixture["crib_id"],
        "width": width,
        "restarts": restarts,
        "best_prefix_length": best["prefix_length"],
        "crib_length": len(fixture["crib"]),
        "exact_crib_recovered": any(row["exact_crib"] for row in traces),
        "exact_order_recovered": any(row["exact_order"] for row in traces),
        "best": best,
        "restart_summaries": [{key: row[key] for key in (
            "restart", "prefix_length", "exact_crib", "exact_order", "trace")}
            for row in traces],
    }


def anneal_search(fixture: dict, restarts: int = 32,
                  steps: int = 10000) -> dict:
    width = fixture["width"]
    truth = tuple(fixture["order"])
    records = []
    overall = None
    for restart in range(restarts):
        rng = base.PCG32(base.derive_seed(
            SEED, 1, width, tuple(phase512a.CRIBS).index(fixture["crib_id"]),
            restart))
        order = rng.permutation(width)
        current = consistent_prefix_length(
            fixture["observed"], width, order, phase512a.PAIR,
            fixture["crib"], fixture["planted_raw_offset"])
        best_score, best_order = current, list(order)
        for step in range(steps):
            left = rng.below(width)
            right = rng.below(width - 1)
            if right >= left:
                right += 1
            order[left], order[right] = order[right], order[left]
            candidate = consistent_prefix_length(
                fixture["observed"], width, order, phase512a.PAIR,
                fixture["crib"], fixture["planted_raw_offset"])
            temperature = max(0.35, 3.0 * (1.0 - step / steps))
            delta = candidate - current
            accept = (delta >= 0 or
                      rng.random() < math.exp(delta / temperature))
            if accept:
                current = candidate
                if current > best_score:
                    best_score, best_order = current, list(order)
                    if best_score == len(fixture["crib"]):
                        break
            else:
                order[left], order[right] = order[right], order[left]
        record = {
            "restart": restart,
            "best_prefix_length": best_score,
            "exact_crib": best_score == len(fixture["crib"]),
            "exact_order": tuple(best_order) == truth,
            "best_order": best_order,
        }
        records.append(record)
        if overall is None or (record["best_prefix_length"], record["exact_order"]) > (
                overall["best_prefix_length"], overall["exact_order"]):
            overall = record
        if record["exact_crib"]:
            break
    return {
        "crib_id": fixture["crib_id"], "width": width,
        "method": "plateau_tolerant_simulated_annealing",
        "restarts_budget": restarts, "steps_per_restart": steps,
        "restarts_executed": len(records), "crib_length": len(fixture["crib"]),
        "best_prefix_length": overall["best_prefix_length"],
        "exact_crib_recovered": any(row["exact_crib"] for row in records),
        "exact_order_recovered": any(row["exact_order"] for row in records),
        "best": overall,
        "restart_summaries": [{key: row[key] for key in (
            "restart", "best_prefix_length", "exact_crib", "exact_order")}
            for row in records],
    }


def run_cell(crib_id: str, width: int, restarts: int) -> dict:
    return greedy_search(phase512a.make_fixture(crib_id, width), restarts)


def self_test() -> dict:
    fixture = phase512a.make_fixture("phase1_credential", 15)
    truth = consistent_prefix_length(
        fixture["observed"], 15, fixture["order"], phase512a.PAIR,
        fixture["crib"], fixture["planted_raw_offset"])
    if truth != len(fixture["crib"]):
        raise AssertionError("true order does not maximize prefix constraint")
    wrong = list(fixture["order"])
    wrong[0], wrong[1] = wrong[1], wrong[0]
    if consistent_prefix_length(
            fixture["observed"], 15, wrong, phase512a.PAIR,
            fixture["crib"], fixture["planted_raw_offset"]) >= truth:
        raise AssertionError("wrong order was not degraded")
    return {"self_test": "pass", "truth_prefix": truth}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--crib", choices=tuple(phase512a.CRIBS))
    parser.add_argument("--width", type=int, choices=phase512a.WIDTHS)
    parser.add_argument("--restarts", type=int, default=32)
    parser.add_argument("--steps", type=int, default=10000)
    parser.add_argument("--method", choices=("greedy", "anneal"), default="greedy")
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.crib is not None and args.width is not None:
        fixture = phase512a.make_fixture(args.crib, args.width)
        value = (greedy_search(fixture, args.restarts) if args.method == "greedy"
                 else anneal_search(fixture, args.restarts, args.steps))
    else:
        parser.error("use --self-test or provide --crib and --width")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
