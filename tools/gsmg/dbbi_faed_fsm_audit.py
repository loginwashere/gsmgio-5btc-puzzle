#!/usr/bin/env python3
"""Profile-calibrated audit of the canonical DBBI 81+10 Moore machine.

The one tested serialization consumes every DBBI symbol exactly once:

* DBBI[0:81] is a row-major 9-state x 9-input next-state table;
* DBBI[81] is the initial state;
* DBBI[82:91] is a nine-state output-label table;
* FAED is the input tape, with output emitted after each transition.

No alternate table orientation, Mealy output rule, or trailer role is searched.
"""

import argparse
import json
import math
import random
import zlib
from collections import Counter

from data import DBBI, FAED


ALPHABET = "abcdefghi"
TRIALS = 20_000
SEED = 0xDBB1FAED
STAT_SPECS = (
    ("permutation_rows", "high"),
    ("reachable_states", "low"),
    ("driven_states", "low"),
    ("used_state_input_edges", "low"),
    ("output_entropy_bits", "low"),
    ("adjacent_output_repeats", "high"),
    ("longest_output_run", "high"),
    ("compressed_output_bytes", "low"),
    ("final_returns_to_initial", "high"),
)


def digits(text):
    values = tuple(ord(symbol) - ord("a") for symbol in text)
    if any(not 0 <= value < 9 for value in values):
        raise ValueError("machine streams must use only a-i")
    return values


def parse_machine(dbbi=DBBI):
    values = digits(dbbi)
    if len(values) != 91:
        raise ValueError("canonical serialization requires exactly 91 symbols")
    table = tuple(tuple(values[row * 9:(row + 1) * 9]) for row in range(9))
    trailer = values[81:]
    return table, trailer[0], tuple(trailer[1:]), trailer


def run_machine(table, initial_state, output_labels, input_tape):
    state = initial_state
    states = []
    outputs = []
    edges = set()
    for input_symbol in input_tape:
        edges.add((state, input_symbol))
        state = table[state][input_symbol]
        states.append(state)
        outputs.append(output_labels[state])
    return tuple(states), tuple(outputs), state, frozenset(edges)


def reachable_states(table, initial_state):
    reached = {initial_state}
    frontier = [initial_state]
    while frontier:
        state = frontier.pop()
        for next_state in table[state]:
            if next_state not in reached:
                reached.add(next_state)
                frontier.append(next_state)
    return frozenset(reached)


def entropy(values):
    total = len(values)
    return -sum((count / total) * math.log2(count / total)
                for count in Counter(values).values())


def longest_run(values):
    best = current = 0
    previous = None
    for value in values:
        if value == previous:
            current += 1
        else:
            previous = value
            current = 1
        best = max(best, current)
    return best


def machine_statistics(table, initial_state, output_labels, input_tape):
    states, outputs, final_state, edges = run_machine(
        table, initial_state, output_labels, input_tape
    )
    output_bytes = bytes(outputs)
    return {
        "permutation_rows": sum(len(set(row)) == 9 for row in table),
        "reachable_states": len(reachable_states(table, initial_state)),
        "driven_states": len(set(states)),
        "used_state_input_edges": len(edges),
        "output_entropy_bits": entropy(outputs),
        "adjacent_output_repeats": sum(
            left == right for left, right in zip(outputs, outputs[1:])
        ),
        "longest_output_run": longest_run(outputs),
        "compressed_output_bytes": len(zlib.compress(output_bytes, 9)),
        "final_returns_to_initial": int(final_state == initial_state),
    }


def empirical_p(observed, null_values, direction):
    if direction == "high":
        extreme = sum(value >= observed for value in null_values)
    elif direction == "low":
        extreme = sum(value <= observed for value in null_values)
    else:
        raise ValueError(direction)
    return (extreme + 1) / (len(null_values) + 1)


def median(values):
    ordered = sorted(values)
    size = len(ordered)
    if size % 2:
        return ordered[size // 2]
    return (ordered[size // 2 - 1] + ordered[size // 2]) / 2


def audit(trials=TRIALS, seed=SEED):
    table, initial_state, output_labels, trailer = parse_machine()
    input_tape = digits(FAED)
    states, outputs, final_state, edges = run_machine(
        table, initial_state, output_labels, input_tape
    )
    observed = machine_statistics(table, initial_state, output_labels, input_tape)

    rng = random.Random(seed)
    dbbi_profile = list(digits(DBBI))
    faed_profile = list(input_tape)
    null = {name: [] for name, _ in STAT_SPECS}
    for _ in range(trials):
        rng.shuffle(dbbi_profile)
        rng.shuffle(faed_profile)
        shuffled = "".join(ALPHABET[value] for value in dbbi_profile)
        null_table, null_initial, null_labels, _ = parse_machine(shuffled)
        row = machine_statistics(
            null_table, null_initial, null_labels, tuple(faed_profile)
        )
        for name, _direction in STAT_SPECS:
            null[name].append(row[name])

    statistic_rows = []
    family_size = len(STAT_SPECS)
    for name, direction in STAT_SPECS:
        raw_p = empirical_p(observed[name], null[name], direction)
        statistic_rows.append({
            "name": name,
            "direction": direction,
            "observed": observed[name],
            "null_median": median(null[name]),
            "raw_p": raw_p,
            "family_p": min(1.0, raw_p * family_size),
        })

    output_text = "".join(ALPHABET[value] for value in outputs)
    corrected_minimum = min(row["family_p"] for row in statistic_rows)
    return {
        "serialization": {
            "table": "DBBI[0:81], row-major state x input",
            "initial_state": "DBBI[81]",
            "output_labels": "DBBI[82:91], one per state",
            "emission": "Moore label after transition",
            "alternate_conventions_tested": 0,
        },
        "trailer_text": DBBI[81:],
        "trailer_values": trailer,
        "initial_state": initial_state,
        "output_labels": output_labels,
        "final_state": final_state,
        "visited_state_count": len(set(states)),
        "used_edge_count": len(edges),
        "output_distinct_symbols": len(set(outputs)),
        "output_prefix": output_text[:160],
        "output_equals_faed": output_text == FAED,
        "output_prefix_equals_dbbi": output_text[:len(DBBI)] == DBBI,
        "output_contains_dbbi": DBBI in output_text,
        "trials": trials,
        "seed": seed,
        "statistic_rows": tuple(statistic_rows),
        "corrected_minimum": corrected_minimum,
        "gate_threshold": 0.01,
        "gate_passed": corrected_minimum < 0.01,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    identity_input_table = tuple(tuple(range(9)) for _ in range(9))
    tape = (8, 3, 4, 0, 7)
    states, outputs, final_state, edges = run_machine(
        identity_input_table, 2, tuple(range(9)), tape
    )
    assert states == outputs == tape
    assert final_state == 7
    assert len(edges) == len(tape)
    table, initial, labels, trailer = parse_machine()
    assert len(table) == 9 and all(len(row) == 9 for row in table)
    assert (initial,) + labels == trailer
    report = audit()
    assert len(report["statistic_rows"]) == len(STAT_SPECS) == 9
    assert not report["candidate_text_generated"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: canonical 81+10 Moore serialization and controls verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(trials=args.trials)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] serialization:", report["serialization"])
    print("[*] trailer:", report["trailer_text"], report["trailer_values"])
    print(
        "[*] final/visited/edges/output symbols:", report["final_state"],
        report["visited_state_count"], report["used_edge_count"],
        report["output_distinct_symbols"]
    )
    for row in report["statistic_rows"]:
        print(
            f"[*] {row['name']}: observed={row['observed']} "
            f"null_median={row['null_median']} raw_p={row['raw_p']:.6f} "
            f"family_p={row['family_p']:.6f}"
        )
    print("[*] output prefix:", report["output_prefix"])
    print("[*] gate passed:", report["gate_passed"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()
