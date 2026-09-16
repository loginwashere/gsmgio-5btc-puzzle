#!/usr/bin/env python3
"""Phase 512A development probe for exact cribs behind Model-B transposition."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import phase484a_raw_symbol_vic_solver as base
from crib_drag import pattern
from data import VALIDATION_ANSWER
from first_hint_hash_audit import PHASE1_PASSWORD
from salphaseion_title_rebus_audit import EXPECTED_MACRO


SCRIPT_DIR = Path(__file__).resolve().parent
RESULT = SCRIPT_DIR / "phase512a_development_result.json"
WIDTHS = (15, 19, 30, 38)
PAIR = ("g", "i")
RANDOM_ORDERS = 1000
SEED = 0x512A001
CRIBS = {
    "phase1_credential": PHASE1_PASSWORD.decode("ascii").upper(),
    "phase322_validation_answer": VALIDATION_ANSWER.upper(),
    "creator_macro_message": EXPECTED_MACRO.upper(),
}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_cribs() -> None:
    expected_lengths = {
        "phase1_credential": 53,
        "phase322_validation_answer": 91,
        "creator_macro_message": 161,
    }
    if {key: len(value) for key, value in CRIBS.items()} != expected_lengths:
        raise AssertionError("crib lengths changed")
    allowed = set(base.LETTER_ALPHABET)
    if any(not set(value) <= allowed for value in CRIBS.values()):
        raise AssertionError("a crib is not representable by the 25-letter board")


def random_board(rng: base.PCG32) -> dict[str, str]:
    letters = list(base.LETTER_ALPHABET)
    rng.shuffle(letters)
    return dict(zip(letters, base.slot_codes(PAIR)))


def filler_for_raw_length(target: int, board: dict[str, str],
                          rng: base.PCG32) -> str:
    if target < 0:
        raise ValueError("negative filler length")
    by_length = {
        length: [letter for letter, code in board.items() if len(code) == length]
        for length in (1, 2)
    }
    output = []
    remaining = target
    while remaining:
        choices = [length for length in (1, 2)
                   if length <= remaining and by_length[length]]
        length = choices[rng.below(len(choices))]
        letters = by_length[length]
        output.append(letters[rng.below(len(letters))])
        remaining -= length
    return "".join(output)


def make_fixture(crib_id: str, width: int, fixture_index: int = 0) -> dict:
    if crib_id not in CRIBS or width not in WIDTHS:
        raise ValueError("unknown crib or width")
    if fixture_index < 0:
        raise ValueError("fixture_index must be non-negative")
    crib = CRIBS[crib_id]
    seed_parts = (WIDTHS.index(width), tuple(CRIBS).index(crib_id))
    # Preserve every Phase-512A fixture byte-for-byte at fixture_index zero.
    # Additional deterministic fixtures extend, rather than rewrite, that set.
    if fixture_index:
        seed_parts += (fixture_index,)
    rng = base.PCG32(base.derive_seed(SEED, *seed_parts))
    board = random_board(rng)
    crib_raw = base.encode_plaintext(crib, board)
    remaining = base.RAW_LENGTH - len(crib_raw)
    if remaining < 2:
        raise AssertionError("crib leaves no room for surrounding filler")
    prefix_target = remaining // 3
    prefix = filler_for_raw_length(prefix_target, board, rng)
    suffix = filler_for_raw_length(remaining - prefix_target, board, rng)
    plaintext = prefix + crib + suffix
    raw = base.encode_plaintext(plaintext, board)
    if len(raw) != base.RAW_LENGTH:
        raise AssertionError("fixture raw length is not 570")
    order = rng.permutation(width)
    observed = base.Geometry(len(raw), width).encrypt(raw, order)
    return {
        "crib_id": crib_id,
        "fixture_index": fixture_index,
        "crib": crib,
        "width": width,
        "pair": list(PAIR),
        "board": board,
        "plaintext": plaintext,
        "planted_token_offset": len(prefix),
        "planted_raw_offset": len(base.encode_plaintext(prefix, board)),
        "crib_raw_length": len(crib_raw),
        "raw": raw,
        "order": order,
        "observed": observed,
    }


def crib_matches_for_order(observed: str, width: int, order,
                           pair: tuple[str, str], crib: str) -> tuple[int, ...]:
    raw = base.Geometry(len(observed), width).decrypt(observed, order)
    codes = base.segment_raw(raw, pair)
    if codes is None or len(codes) < len(crib):
        return ()
    wanted = pattern(crib)
    return tuple(start for start in range(len(codes) - len(crib) + 1)
                 if pattern(codes[start:start + len(crib)]) == wanted)


def random_wrong_orders(fixture: dict, count: int = RANDOM_ORDERS):
    rng = base.PCG32(base.derive_seed(SEED, 99, fixture["width"],
                                     tuple(CRIBS).index(fixture["crib_id"])))
    truth = tuple(fixture["order"])
    made = set()
    while len(made) < count:
        candidate = tuple(rng.permutation(fixture["width"]))
        if candidate != truth:
            made.add(candidate)
    return tuple(sorted(made))


def swap_neighbors(order) -> tuple[tuple[int, ...], ...]:
    order = tuple(order)
    output = []
    for left, right in itertools.combinations(range(len(order)), 2):
        candidate = list(order)
        candidate[left], candidate[right] = candidate[right], candidate[left]
        output.append(tuple(candidate))
    return tuple(output)


def evaluate_fixture(crib_id: str, width: int) -> dict:
    fixture = make_fixture(crib_id, width)
    arguments = (fixture["observed"], width, PAIR, fixture["crib"])
    truth_matches = crib_matches_for_order(
        arguments[0], arguments[1], fixture["order"], arguments[2], arguments[3])
    if fixture["planted_token_offset"] not in truth_matches:
        raise AssertionError("true order did not recover planted crib")
    random_hits = []
    for index, order in enumerate(random_wrong_orders(fixture)):
        matches = crib_matches_for_order(arguments[0], arguments[1], order,
                                         arguments[2], arguments[3])
        if matches:
            random_hits.append({"sample_index": index, "matches": list(matches)})
    neighbor_hits = []
    neighbors = swap_neighbors(fixture["order"])
    for index, order in enumerate(neighbors):
        matches = crib_matches_for_order(arguments[0], arguments[1], order,
                                         arguments[2], arguments[3])
        if matches:
            neighbor_hits.append({"neighbor_index": index, "matches": list(matches)})
    return {
        "crib_id": crib_id,
        "crib_length": len(fixture["crib"]),
        "crib_sha256": sha_bytes(fixture["crib"].encode("ascii")),
        "width": width,
        "true_match_offsets": list(truth_matches),
        "planted_token_offset": fixture["planted_token_offset"],
        "planted_raw_offset": fixture["planted_raw_offset"],
        "crib_raw_length": fixture["crib_raw_length"],
        "random_wrong_orders_tested": RANDOM_ORDERS,
        "random_wrong_order_hit_count": len(random_hits),
        "random_wrong_order_hits": random_hits,
        "single_swap_neighbors_tested": len(neighbors),
        "single_swap_neighbor_hit_count": len(neighbor_hits),
        "single_swap_neighbor_hits": neighbor_hits,
        "raw_sha256": sha_bytes(fixture["raw"].encode("ascii")),
        "observed_sha256": sha_bytes(fixture["observed"].encode("ascii")),
    }


def run() -> dict:
    validate_cribs()
    rows = [evaluate_fixture(crib_id, width)
            for crib_id in CRIBS for width in WIDTHS]
    result = {
        "phase": "512A",
        "status": "development_terminal_specificity_and_local_basin",
        "faed_imported_or_scored": False,
        "cells": rows,
        "all_true_orders_match": all(
            row["planted_token_offset"] in row["true_match_offsets"] for row in rows),
        "total_random_wrong_order_hits": sum(
            row["random_wrong_order_hit_count"] for row in rows),
        "total_single_swap_neighbor_hits": sum(
            row["single_swap_neighbor_hit_count"] for row in rows),
        "disposition": "exact_hit_is_terminal_validator_not_local_search_objective",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def self_test() -> dict:
    validate_cribs()
    toy = make_fixture("phase1_credential", 15)
    matches = crib_matches_for_order(toy["observed"], 15, toy["order"],
                                     PAIR, toy["crib"])
    if toy["planted_token_offset"] not in matches:
        raise AssertionError("round trip did not retain exact crib")
    if len(swap_neighbors(range(5))) != 10:
        raise AssertionError("swap neighborhood size changed")
    filler = filler_for_raw_length(37, toy["board"], base.PCG32(1))
    if len(base.encode_plaintext(filler, toy["board"])) != 37:
        raise AssertionError("filler missed target raw length")
    return {"self_test": "pass", "cribs": len(CRIBS),
            "widths": list(WIDTHS), "cells": len(CRIBS) * len(WIDTHS)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-development", action="store_true")
    args = parser.parse_args()
    if args.self_test == args.run_development:
        parser.error("choose exactly one action")
    value = self_test() if args.self_test else run()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
