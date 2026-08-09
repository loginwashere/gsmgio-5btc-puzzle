#!/usr/bin/env python3
"""Independently reconstruct the first-piece 400/401/73 prime-list split.

This intentionally does not import the existing Flo/Denis prime-walk audit or
the later matrixsumlist color-prime audit.  It rebuilds the narrow construction
from authenticated inputs:

1. sort the 24 colored LSB endpoints and FEFE by spiral position;
2. assign successive primes by event ordinal (the sourced community rule);
3. consume ``b`` for blue/FEFE and ``be`` for yellow against DBBI;
4. stop when the next complete token falls outside the 91-symbol DBBI stream;
5. partition and sum the primes by the retained event types.

The module verifies the arithmetic and its load-bearing boundary/classification
choices.  It does not apply FEFEFE as a bit mask, generate a password, or infer
that ``half and better half`` is the intended semantic reading.
"""

import argparse
import itertools
from fractions import Fraction
from math import comb

from data import DBBI
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct

EXPECTED_EVENT_TYPES = "BBBBYBBBYYBBBBYBBYYBFYYBY"
EXPECTED_FITTED_SUMS = {"B": 401, "Y": 400, "F": 73}
EXPECTED_ALL_SUMS = {"B": 490, "Y": 497, "F": 73}


def is_prime(value):
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def first_primes(count):
    primes = []
    candidate = 2
    while len(primes) < count:
        if is_prime(candidate):
            primes.append(candidate)
        candidate += 1
    return tuple(primes)


def spatial_events(image_path=DEFAULT_IMAGE):
    result = reconstruct(image_path)
    events = [
        {
            "spiral_0": item["spiral_0"],
            "type": "B" if item["color"] == "blue" else "Y",
            "object_1": item["ordinal_1"],
            "character": item["character"],
        }
        for item in result["objects"]
    ]
    events.append(
        {
            "spiral_0": result["fefe"]["spiral_0"],
            "type": "F",
            "object_1": None,
            "character": result["fefe"]["character"],
        }
    )
    return tuple(sorted(events, key=lambda event: event["spiral_0"]))


def token_for(event_type):
    if event_type == "Y":
        return "be"
    if event_type in ("B", "F"):
        return "b"
    raise ValueError(f"unsupported event type: {event_type!r}")


def build_walk(events, consumer=DBBI):
    primes = first_primes(len(events))
    prior_yellows = 0
    records = []
    for ordinal, (event, prime) in enumerate(zip(events, primes), start=1):
        required = token_for(event["type"])
        position_1 = prime + prior_yellows
        end_1 = position_1 + len(required) - 1
        actual = consumer[position_1 - 1:end_1]
        fits = end_1 <= len(consumer)
        records.append(
            {
                **event,
                "ordinal": ordinal,
                "prime": prime,
                "prior_yellows": prior_yellows,
                "position_1": position_1,
                "end_1": end_1,
                "required": required,
                "actual": actual,
                "fits": fits,
                "matches": fits and actual == required,
            }
        )
        if event["type"] == "Y":
            prior_yellows += 1
    return tuple(records)


def fitted_prefix(records):
    length = 0
    for record in records:
        if not record["fits"]:
            break
        length += 1
    if any(record["fits"] for record in records[length:]):
        raise AssertionError("consumer fit is not a single prefix")
    return records[:length]


def prime_groups(records):
    return {
        event_type: tuple(
            record["prime"] for record in records if record["type"] == event_type
        )
        for event_type in ("B", "Y", "F")
    }


def group_sums(groups):
    return {event_type: sum(values) for event_type, values in groups.items()}


def exact_fixed_profile_balance_rate(records, maximum_difference=1):
    """Shuffle B/Y labels over non-F primes, preserving observed counts."""
    non_fefe_primes = tuple(
        record["prime"] for record in records if record["type"] != "F"
    )
    yellow_count = sum(record["type"] == "Y" for record in records)
    total_sum = sum(non_fefe_primes)
    successes = sum(
        abs((total_sum - sum(yellow)) - sum(yellow)) <= maximum_difference
        for yellow in itertools.combinations(non_fefe_primes, yellow_count)
    )
    return Fraction(successes, comb(len(non_fefe_primes), yellow_count))


def prefix_sum_table(records):
    totals = {"B": 0, "Y": 0, "F": 0}
    rows = []
    for record in records:
        totals[record["type"]] += record["prime"]
        rows.append(
            {
                "prefix": record["ordinal"],
                "B": totals["B"],
                "Y": totals["Y"],
                "F": totals["F"],
                "blue_minus_yellow": totals["B"] - totals["Y"],
            }
        )
    return tuple(rows)


def audit(image_path=DEFAULT_IMAGE):
    events = spatial_events(image_path)
    records = build_walk(events)
    fitted = fitted_prefix(records)
    fitted_groups = prime_groups(fitted)
    all_groups = prime_groups(records)
    fitted_sums = group_sums(fitted_groups)
    all_sums = group_sums(all_groups)
    prefix_table = prefix_sum_table(records)
    near_balance_prefixes = tuple(
        row["prefix"] for row in prefix_table
        if abs(row["blue_minus_yellow"]) <= 1
    )
    first_outside = records[len(fitted)]

    return {
        "event_types": "".join(event["type"] for event in events),
        "events": events,
        "records": records,
        "fitted_records": fitted,
        "fitted_groups": fitted_groups,
        "fitted_sums": fitted_sums,
        "all_groups": all_groups,
        "all_sums": all_sums,
        "fitted_event_count": len(fitted),
        "first_outside": first_outside,
        "all_fitted_match": all(record["matches"] for record in fitted),
        "balance_difference": abs(fitted_sums["B"] - fitted_sums["Y"]),
        "balance_rate": exact_fixed_profile_balance_rate(fitted),
        "prefix_sum_table": prefix_table,
        "near_balance_prefixes": near_balance_prefixes,
        "fefe_record": next(record for record in records if record["type"] == "F"),
        "fefe_folded_into_blue_sums": {
            "B": fitted_sums["B"] + fitted_sums["F"],
            "Y": fitted_sums["Y"],
        },
        "consumer_length": len(DBBI),
        "same_prefix_consumer_lengths": tuple(
            length
            for length in range(fitted[-1]["end_1"], first_outside["end_1"])
            if fitted[-1]["end_1"] <= length < first_outside["end_1"]
        ),
    }


def self_test():
    assert first_primes(10) == (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
    report = audit()
    assert report["event_types"] == EXPECTED_EVENT_TYPES
    assert report["fitted_event_count"] == 23
    assert report["all_fitted_match"] is True
    assert report["fitted_groups"] == {
        "B": (2, 3, 5, 7, 13, 17, 19, 31, 37, 41, 43, 53, 59, 71),
        "Y": (11, 23, 29, 47, 61, 67, 79, 83),
        "F": (73,),
    }
    assert report["fitted_sums"] == EXPECTED_FITTED_SUMS
    assert report["all_sums"] == EXPECTED_ALL_SUMS
    assert report["balance_difference"] == 1
    assert report["balance_rate"] == Fraction(813, 319_770)
    assert report["near_balance_prefixes"] == (23,)
    assert report["fefe_record"]["ordinal"] == 21
    assert report["fefe_record"]["prime"] == 73
    assert report["fefe_record"]["position_1"] == 79
    assert report["fefe_record"]["matches"] is True
    assert report["first_outside"]["ordinal"] == 24
    assert report["first_outside"]["prime"] == 89
    assert report["first_outside"]["position_1"] == 97
    assert report["fefe_folded_into_blue_sums"] == {"B": 474, "Y": 400}
    assert report["same_prefix_consumer_lengths"] == tuple(range(91, 97))
    print("[*] self-test OK: independent 400/401/73 prime-list reconstruction reproduces")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()

    print(f"[*] spatial event types: {report['event_types']}")
    print("[*] event table:")
    print("    evt prime type spiral object char priorY position-end need got fit/match")
    for row in report["records"]:
        print(
            f"    {row['ordinal']:>3} {row['prime']:>5} {row['type']:>4} "
            f"{row['spiral_0']:>6} {str(row['object_1']):>6} {row['character']!r:>4} "
            f"{row['prior_yellows']:>6} {row['position_1']:>3}-{row['end_1']:<3} "
            f"{row['required']!r:>4} {row['actual']!r:>4} "
            f"{row['fits']}/{row['matches']}"
        )
    print(f"[*] fitted groups: {report['fitted_groups']}")
    print(f"[*] fitted sums: {report['fitted_sums']}")
    print(f"[*] all-25 sums: {report['all_sums']}")
    rate = report["balance_rate"]
    print(
        f"[*] exact fixed-profile |B-Y|<=1 rate: "
        f"{rate.numerator}/{rate.denominator} = {float(rate):.9f}"
    )
    print(f"[*] prefixes with |B-Y|<=1: {report['near_balance_prefixes']}")
    print(
        f"[*] DBBI length={report['consumer_length']}; same 23-event cutoff for "
        f"consumer lengths {report['same_prefix_consumer_lengths']}"
    )
    print(
        "[*] verdict: 400/401/73 reproduces from the sourced successive-prime "
        "walk and the independently fixed DBBI boundary. It depends on keeping "
        "FEFE separate and on the community-sourced B/BE token grammar. No FE "
        "bit-mask composition is selected by this reconstruction."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
