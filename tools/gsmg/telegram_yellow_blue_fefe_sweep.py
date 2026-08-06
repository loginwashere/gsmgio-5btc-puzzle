#!/usr/bin/env python3
"""Test the recovered yellow-blue-primes guide under corrected FEFE insertion.

The historical guide places 23 DBBI prime chunks into a 14x14 spiral and sums
rows modulo 26.  The corrected first-piece event stream has 25 spatial events:
24 colored character endpoints plus FEFE at spiral index 163.  Its final two
events cross directly into the following binary-ASCII ``matrixsumlist`` page
segment, as established by ``prime_walk_page_boundary_audit.py``.

FEFE creates one unavoidable collision: the prime-73 chunk ending at FEFE and
the prime-79 chunk ending four cells later require overlapping cells.  This
script pre-registers three bounded policies before scoring:

* ``later_wins``: later contiguous chunks overwrite earlier cells;
* ``earlier_wins``: later contiguous chunks leave occupied cells unchanged;
* ``skip_occupied``: later chunks scan backward past occupied cells.

All policies are included inside the same max-statistic null.  The null
preserves the complete 25-chunk multiset, chunk boundaries, endpoint geometry,
row-sum operation, and policy family, while randomly assigning chunks to the
25 endpoints.  It tests whether the real chunk/endpoint association has
exceptional English quadgram fitness; it is not a general model of every
possible guide construction.
"""

import argparse
import random
from dataclasses import dataclass

from data import DBBI
from door_prime_passport_probe import nth_prime
from first_piece_color_reconstruction import (
    DEFAULT_IMAGE,
    reconstruct,
    spiral_top_left_counterclockwise,
)
from page_structure_audit import MATRIX_INSTRUCTION, binary_ascii
from quadgram_solver import score as quadgram_score
from telegram_yellow_blue_guide_audit import (
    EXPECTED_OUTPUT,
    guide_chunks,
    output_from_row_sums,
    token_value,
    tokenize_dbbi,
)

POLICIES = ("later_wins", "earlier_wins", "skip_occupied")
N = 14


@dataclass(frozen=True)
class Candidate:
    policy: str
    output: str
    score: float
    occupied_cells: int
    collisions: int


def spatial_events(image_path=DEFAULT_IMAGE):
    image = reconstruct(image_path)
    events = [
        (
            item["spiral_0"],
            "B" if item["color"] == "blue" else "Y",
        )
        for item in image["objects"]
    ]
    events.append((image["fefe"]["spiral_0"], "F"))
    events.sort()
    return tuple(events)


def corrected_chunks(events):
    matrix_bits = binary_ascii(MATRIX_INSTRUCTION)
    source = DBBI + matrix_bits
    chunks = []
    start = 0
    yellow_count = 0
    records = []
    for ordinal, (spiral_endpoint, event_type) in enumerate(events, start=1):
        prime = nth_prime(ordinal)
        raw_position = prime + yellow_count
        raw_index = raw_position - 1
        if raw_position <= len(DBBI):
            expected = "be" if event_type == "Y" else "b"
            if not source.startswith(expected, raw_index):
                raise AssertionError(
                    f"event {ordinal} expected {expected!r} at raw position "
                    f"{raw_position}, found {source[raw_index:raw_index + 2]!r}"
                )
            end = raw_index + len(expected)
            values = tuple(token_value(token) for token in tokenize_dbbi(source[start:end]))
            yellow_count += event_type == "Y"
        else:
            expected = "a" if event_type == "Y" else "b"
            if source[raw_index] != expected:
                raise AssertionError(
                    f"event {ordinal} expected page bit {expected!r} at raw "
                    f"position {raw_position}, found {source[raw_index]!r}"
                )
            end = raw_index + 1
            values = tuple(token_value(character) for character in source[start:end])
        chunks.append(values)
        records.append(
            {
                "ordinal": ordinal,
                "event_type": event_type,
                "prime": prime,
                "raw_position": raw_position,
                "spiral_endpoint": spiral_endpoint,
                "source": source[start:end],
                "values": values,
            }
        )
        start = end
    return tuple(chunks), tuple(records)


def historical_inputs(image_path=DEFAULT_IMAGE):
    image = reconstruct(image_path)
    endpoints = tuple(item["spiral_0"] for item in image["objects"][:23])
    chunk_strings = guide_chunks(DBBI, image["color_sequence"][:23])
    chunks = tuple(
        tuple(token_value(token) for token in tokenize_dbbi(chunk))
        for chunk in chunk_strings
    )
    return chunks, endpoints


def historical_baseline(image_path=DEFAULT_IMAGE):
    chunks, endpoints = historical_inputs(image_path)
    candidate = place_and_score(chunks, endpoints, "later_wins")
    if candidate.output != EXPECTED_OUTPUT:
        raise AssertionError(
            f"canonical historical placement differs: {candidate.output!r}"
        )
    return candidate


def place_chunks(chunks, endpoints, policy):
    if policy not in POLICIES:
        raise ValueError(f"unsupported collision policy: {policy!r}")
    if len(chunks) != len(endpoints):
        raise ValueError("chunks and endpoints differ in length")
    cells = [0] * (N * N)
    collisions = 0
    for chunk, endpoint in zip(chunks, endpoints):
        if policy == "skip_occupied":
            cursor = endpoint
            for value in reversed(chunk):
                while cursor >= 0 and cells[cursor]:
                    collisions += 1
                    cursor -= 1
                if cursor < 0:
                    raise ValueError("skip-occupied placement ran before matrix start")
                cells[cursor] = value
                cursor -= 1
            continue

        start = endpoint - len(chunk) + 1
        if start < 0:
            raise ValueError("contiguous placement ran before matrix start")
        for position, value in zip(range(start, endpoint + 1), chunk):
            if cells[position]:
                collisions += 1
                if policy == "earlier_wins":
                    continue
            cells[position] = value
    return tuple(cells), collisions


def row_sums_from_spiral(values):
    matrix = [[0] * N for _ in range(N)]
    for value, (row, column) in zip(values, spiral_top_left_counterclockwise()):
        matrix[row][column] = value
    return tuple(sum(row) for row in matrix)


def normalized_quadgram_score(text):
    windows = max(1, len(text) - 3)
    return quadgram_score(text) / windows


def place_and_score(chunks, endpoints, policy):
    values, collisions = place_chunks(chunks, endpoints, policy)
    output = output_from_row_sums(row_sums_from_spiral(values))
    return Candidate(
        policy=policy,
        output=output,
        score=normalized_quadgram_score(output),
        occupied_cells=sum(bool(value) for value in values),
        collisions=collisions,
    )


def real_candidates(image_path=DEFAULT_IMAGE):
    events = spatial_events(image_path)
    chunks, records = corrected_chunks(events)
    endpoints = tuple(endpoint for endpoint, _ in events)
    candidates = tuple(
        place_and_score(chunks, endpoints, policy)
        for policy in POLICIES
    )
    return candidates, chunks, endpoints, records


def shuffle_gate(chunks, endpoints, real_best, trials, seed):
    rng = random.Random(seed)
    at_least_as_good = 0
    null_scores = []
    indices = list(range(len(chunks)))
    for _ in range(trials):
        rng.shuffle(indices)
        shuffled = tuple(chunks[index] for index in indices)
        trial_best = max(
            place_and_score(shuffled, endpoints, policy).score
            for policy in POLICIES
        )
        null_scores.append(trial_best)
        at_least_as_good += trial_best >= real_best
    empirical_p = (at_least_as_good + 1) / (trials + 1)
    return {
        "trials": trials,
        "seed": seed,
        "at_least_as_good": at_least_as_good,
        "empirical_p": empirical_p,
        "null_mean": sum(null_scores) / len(null_scores),
        "null_max": max(null_scores),
    }


def self_test(image_path=DEFAULT_IMAGE):
    baseline = historical_baseline(image_path)
    assert baseline.output == EXPECTED_OUTPUT
    assert baseline.collisions == 0

    tiny_chunks = ((1, 2), (3, 4))
    tiny_endpoints = (2, 3)
    later, later_collisions = place_chunks(tiny_chunks, tiny_endpoints, "later_wins")
    earlier, earlier_collisions = place_chunks(tiny_chunks, tiny_endpoints, "earlier_wins")
    skipped, skipped_collisions = place_chunks(tiny_chunks, tiny_endpoints, "skip_occupied")
    assert later[:4] == (0, 1, 3, 4)
    assert earlier[:4] == (0, 1, 2, 4)
    assert skipped[:4] == (3, 1, 2, 4)
    assert (later_collisions, earlier_collisions, skipped_collisions) == (1, 1, 2)

    candidates, chunks, endpoints, records = real_candidates(image_path)
    assert len(chunks) == len(endpoints) == len(records) == 25
    assert records[20]["event_type"] == "F"
    assert records[20]["prime"] == 73
    assert records[20]["raw_position"] == 79
    assert records[20]["spiral_endpoint"] == 163
    assert records[23]["source"] == "abbabb"
    assert records[24]["source"] == "ababbaaa"
    assert tuple(candidate.output for candidate in candidates) == (
        "IZLKHMELLRPPEN",
        "IZLKHMEHLRPPEN",
        "IZLKNSEHLRPPEN",
    )
    print(
        "[*] self-test OK: historical output reproduced; corrected FEFE walk "
        "produces three fixed collision-policy outputs"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--trials", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260726)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.image)
    if args.self_test:
        return

    baseline = historical_baseline(args.image)
    print(
        f"[*] historical canonical baseline: {baseline.output} "
        f"score={baseline.score:.6f}"
    )
    candidates, chunks, endpoints, records = real_candidates(args.image)
    for candidate in candidates:
        print(
            f"[*] corrected {candidate.policy}: {candidate.output} "
            f"score={candidate.score:.6f} occupied={candidate.occupied_cells} "
            f"collisions={candidate.collisions}"
        )
    real_best = max(candidate.score for candidate in candidates)
    historical_chunks, historical_endpoints = historical_inputs(args.image)
    control_gate = shuffle_gate(
        historical_chunks,
        historical_endpoints,
        baseline.score,
        args.trials,
        args.seed,
    )
    print(
        f"[*] historical-control null: trials={control_gate['trials']} "
        f"seed={control_gate['seed']} real={baseline.score:.6f} "
        f"null_mean={control_gate['null_mean']:.6f} "
        f"null_max={control_gate['null_max']:.6f} "
        f"at_least={control_gate['at_least_as_good']}/{control_gate['trials']} "
        f"p={control_gate['empirical_p']:.6f}"
    )
    gate = shuffle_gate(chunks, endpoints, real_best, args.trials, args.seed)
    print(
        f"[*] endpoint-assignment null: trials={gate['trials']} seed={gate['seed']} "
        f"real_best={real_best:.6f} null_mean={gate['null_mean']:.6f} "
        f"null_max={gate['null_max']:.6f} "
        f"at_least={gate['at_least_as_good']}/{gate['trials']} "
        f"p={gate['empirical_p']:.6f}"
    )
    print(
        "[*] verdict: promote only if the corrected real association is "
        "exceptional under the full three-policy max statistic; otherwise "
        "record the recovered historical guide but close this FEFE correction."
    )


if __name__ == "__main__":
    main()
