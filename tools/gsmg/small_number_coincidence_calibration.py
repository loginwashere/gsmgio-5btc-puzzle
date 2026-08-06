#!/usr/bin/env python3
"""Calibrate how surprising it is that -41 + -17 = -58 lands on another
already-established puzzle number (58, the confirmed real Cosmic Duality
book page cross-referenced from page 56 -- Phase 8/36).

The pool below is every small integer this project has independently
established as a real, cited puzzle-derived value BEFORE this calibration
was written (not chosen afterward to make the result come out a particular
way): DBBI's matrix dimensions, the `[23,16,7]` partition and its sum, the
recovered mask length, the Decentraland coordinates, the confirmed book
page, and the five prime-walk event primes. This checks one question only:
across all pairs from this exact, pre-registered pool, how often does a
pairwise sum coincide with a *different* member of the same pool? That is
the base rate against which 41+17=58 should be judged, not an intuition
about whether 58 "feels" meaningful.
"""

import argparse
from itertools import combinations

ESTABLISHED_NUMBERS = {
    7: "DBBI matrix rows (91 = 7x13); 4th prime",
    13: "DBBI matrix columns (91 = 7x13); 6th prime",
    16: "[23,16,7] blue-endpoint count (Phase 58/61)",
    17: "Decentraland |y| coordinate; 7th prime",
    23: "[23,16,7] total guide endpoints (Phase 58/61)",
    24: "gsmg.io/theseedisplanted character count",
    31: "recovered exact mask length (Phase 48)",
    41: "Decentraland |x| coordinate; 13th prime",
    46: "sum of [23,16,7] (Phase 58/61)",
    58: "confirmed real Cosmic Duality book page (Phase 8/36)",
    73: "prime-walk event 21 (Phase 48)",
    79: "prime-walk event 22 (Phase 48)",
    83: "prime-walk event 23 (Phase 48); 23rd prime",
    89: "prime-walk event 24 (Phase 50)",
    91: "DBBI/SOURCE length",
    97: "prime-walk event 25 (Phase 50)",
    104: "abba(matrixsumlist) bit length (13x8, Phase 50)",
    163: "FEFE spiral position (Phase 48)",
}

TARGET_PAIR = (41, 17)
TARGET_SUM = 58

EXPECTED_POOL_SIZE = 18
EXPECTED_TOTAL_PAIRS = 153
EXPECTED_HIT_COUNT = 12
EXPECTED_HIT_PAIRS = (
    (7, 16), (7, 17), (7, 24), (7, 97), (13, 91), (16, 73),
    (17, 24), (17, 41), (24, 73), (31, 58), (31, 73), (46, 58),
)
TAUTOLOGICAL_HIT = (7, 16, 23)  # 16 blue + 7 yellow = 23 total, by construction (Phase 58/61)


def pairwise_sum_hits(pool):
    values = sorted(pool)
    hits = []
    for a, b in combinations(values, 2):
        total = a + b
        if total in pool and total not in (a, b):
            hits.append((a, b, total))
    return tuple(hits)


def audit(pool=ESTABLISHED_NUMBERS):
    values = set(pool)
    all_pairs = tuple(combinations(sorted(values), 2))
    hits = pairwise_sum_hits(values)
    hit_pairs = [(a, b) for a, b, _ in hits]
    target_hit = TARGET_PAIR in hit_pairs or tuple(reversed(TARGET_PAIR)) in hit_pairs
    non_tautological_hits = tuple(hit for hit in hits if hit != TAUTOLOGICAL_HIT)
    return {
        "pool_size": len(values),
        "total_pairs": len(all_pairs),
        "hits": hits,
        "hit_rate": len(hits) / len(all_pairs),
        "non_tautological_hit_rate": len(non_tautological_hits) / (len(all_pairs) - 1),
        "target_pair_is_a_hit": target_hit,
    }


def self_test():
    report = audit()
    assert report["pool_size"] == EXPECTED_POOL_SIZE
    assert report["total_pairs"] == EXPECTED_TOTAL_PAIRS
    assert len(report["hits"]) == EXPECTED_HIT_COUNT, report["hits"]
    assert tuple((a, b) for a, b, _ in report["hits"]) == EXPECTED_HIT_PAIRS
    assert report["target_pair_is_a_hit"] is True
    print(
        f"[*] self-test OK: {report['pool_size']}-number pool, "
        f"{report['total_pairs']} pairs, {len(report['hits'])} pairwise-sum "
        f"coincidences found (empirical rate {report['hit_rate']:.1%}) -- "
        "41+17=58 is one of many, not a rare outlier"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    report = audit()
    print(f"[*] pool: {report['pool_size']} established numbers, "
          f"{report['total_pairs']} pairs")
    print(f"[*] pairwise-sum coincidences (sum lands on a different pool member):")
    for a, b, total in report["hits"]:
        print(f"    {a} + {b} = {total}  ({ESTABLISHED_NUMBERS[a]}) + "
              f"({ESTABLISHED_NUMBERS[b]}) -> ({ESTABLISHED_NUMBERS[total]})")
    print(f"[*] empirical hit rate: {len(report['hits'])}/{report['total_pairs']} "
          f"= {report['hit_rate']:.1%}")
    print(f"[*] excluding the one tautological hit (16 blue + 7 yellow = 23 "
          f"total, true by construction, not an independent coincidence): "
          f"{report['non_tautological_hit_rate']:.1%}")
    print(f"[*] the pair in question, 41+17=58, is one hit among the other 11")
    print(
        "\n[*] verdict: this base rate is NOT low. Roughly 1 in 13 pairs from "
        "this project's own established small-number pool coincidentally "
        "sums to a different pool member -- 41+17=58 is unremarkable in that "
        "light, not distinctive. This is the opposite of what a naive guess "
        "at this rate might suggest, and it is exactly the failure mode this "
        "project has flagged before (Phase 13, Phase 36): a puzzle this "
        "dense with small derived numbers will produce this kind of overlap "
        "routinely. No creator or community source links Decentraland "
        "coordinates to a book page number, and this calibration gives no "
        "reason to promote the idea that one exists. Closed negative."
    )


if __name__ == "__main__":
    main()
