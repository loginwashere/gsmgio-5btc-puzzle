#!/usr/bin/env python3
"""Exact uniform-subset base-rate audit of a community-derived lead, not a
significance test of the lead's own (non-uniform, not-yet-recovered)
selection rule.

Source (chat_transcript.txt, lines 168547-168675): Denis Golovkin claimed
(20:29:18 UTC-05:00, 2026-03-03) that "specific prime indexes" applied to
"specific last words" extract ~30-31 characters containing "ying yang" and
"salvation". His concrete extraction (20:39:06): from the known 91-char
plaintext `SOURCE` below, "chars matching 'YBprimes'" give
`ncsyangcahiriasogaleafayanestve` (31 chars, TARGET below, quoted exactly).

Checked directly against that exact string: `"yang"` IS a literal
substring. `"ying"` and `"salvation"` are NOT -- they never appear in it.
His 20:48:31 follow-up posts sentences explicitly labeled "Here are some
manually crafted:" -- hand-built anagram sentences from the same 31-letter
multiset (e.g. "reach a safe ying yang salvation case"). So "ying" and
"salvation" are anagram-letter-subset claims, not found substrings. At
20:41:57 he says himself: "Might be a phrase anagram. I've brute-forced few
trillions of anagrams, but didn't find em to be the key to proceed" -- a
large but far from exhaustive search (the 31-letter multiset has
31!/(7!3!3!3!2!2!2!2!) ~= 4.72e26 distinct anagrams; a few trillion covers
roughly 10^-14 of that space).

His clearest method description (20:57:30, lines 168663-168675): "We took
'yellow blue primes' of dbbi to filter indexes that match B or BE chars vs
indexes that don't match... And once we apply chosen indexes to these last
words, we see that selected 31 (or 30) characters includes a 'ying yang'."
That summary is itself inconsistent with his own posted string (no "ying"
in it) -- reason to treat the narrative loosely, not as a precise spec. The
"guide to yellow-blue-primes" image he references (20:36:01) is missing
from this text transcript (no attachment marker near that message, unlike
other points in the transcript where attachments *are* referenced by
filename).

RULE_FAMILY below enumerates 44 selection rules a person could plausibly
build from "B for blue, BE for yellow" x primality, applied to the real
DBBI string. None reproduce Denis's exact output, and none even reproduce
the "yang" substring hit on the real data. The rule was **not recovered
within this declared 44-rule family** -- a bounded negative about that
family, not proof no reconstruction exists (the missing image, or a
differently parameterized family, might still work).

Given that, this module answers a narrower, well-posed question instead:
among all equally-likely order-preserving k-subsets of this specific
91-character source, how common is it for one to contain "yang" (or
"ying") as a contiguous substring? That sidesteps the missing-rule problem
entirely -- it doesn't matter *how* Denis's 31 positions were chosen, only
that an order-preserving 31-of-91 selection containing "yang" is a verified
fact about this string. Computed exactly via dynamic programming (KMP
automaton over source position x subset-size-used x found-flag), not by
sampling.

Usage:
    python3 tools/gsmg/denis_prime_extraction_audit.py
    python3 tools/gsmg/denis_prime_extraction_audit.py --self-test
"""
import itertools
import math
from functools import lru_cache
from math import comb
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI  # noqa: E402

SOURCE = (
    "incaseyoumanagetocrackthistheprivatekeysbelongtohalfandbetterhalf"
    "andtheyalsoneedfundstolive"
)
TARGET = "ncsyangcahiriasogaleafayanestve"
assert len(SOURCE) == len(DBBI) == 91
assert len(TARGET) == 31

NINE_SYMS = "abcdefghi"
MEMBERSHIP_SETS = {
    "b_only": set("b"),
    "be": set("be"),
    "e_only": set("e"),
}


def is_prime(value):
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def _pure_prime_variants():
    for base_name in ("0based", "1based"):
        yield ("pure_prime", base_name, None, None)


def _combinator_variants():
    for op in ("AND", "OR", "XOR"):
        for base_name in ("0based", "1based"):
            for set_name in MEMBERSHIP_SETS:
                for pol_name in ("prime", "nonprime"):
                    yield (op, base_name, set_name, pol_name)


def _filter_then_prime_variants():
    for base_name in ("0based", "1based"):
        for set_name in MEMBERSHIP_SETS:
            yield ("filter_then_prime", base_name, set_name, None)


RULE_FAMILY = tuple(
    itertools.chain(
        _pure_prime_variants(),
        _combinator_variants(),
        _filter_then_prime_variants(),
    )
)
assert len(RULE_FAMILY) == 44, f"expected 44 named rules, got {len(RULE_FAMILY)}"


def apply_rule(rule, source, dbbi):
    kind, base_name, set_name, pol_name = rule
    base = 0 if base_name == "0based" else 1
    membership = MEMBERSHIP_SETS.get(set_name) if set_name else None

    if kind == "pure_prime":
        return "".join(c for i, c in enumerate(source) if is_prime(i + base))

    if kind == "filter_then_prime":
        subsequence = [sc for sc, dc in zip(source, dbbi) if dc in membership]
        return "".join(c for i, c in enumerate(subsequence) if is_prime(i + base))

    want_prime = pol_name == "prime"
    out = []
    for i, (sc, dc) in enumerate(zip(source, dbbi)):
        prime_here = is_prime(i + base)
        member_here = dc in membership
        if kind == "AND" and (prime_here == want_prime) and member_here:
            out.append(sc)
        elif kind == "OR" and ((prime_here == want_prime) or member_here):
            out.append(sc)
        elif kind == "XOR" and ((prime_here == want_prime) != member_here):
            out.append(sc)
    return "".join(out)


def rule_family_report(source, dbbi, target_substring="yang"):
    outputs = [apply_rule(rule, source, dbbi) for rule in RULE_FAMILY]
    unique_outputs = set(outputs)
    contains_target = sum(1 for out in outputs if target_substring in out)
    reproduces_denis = sum(1 for out in outputs if out == TARGET)
    return {
        "total_rules": len(RULE_FAMILY),
        "unique_outputs": len(unique_outputs),
        "contains_target": contains_target,
        "reproduces_denis": reproduces_denis,
    }


def recover_position_masks(source, target):
    """Every strictly-increasing sequence of len(target) source positions
    whose characters equal target exactly, via DP-backed backtracking."""
    n = len(source)
    m = len(target)

    @lru_cache(maxsize=None)
    def count_ways(i, j):
        if j == m:
            return 1
        if i == n or (m - j) > (n - i):
            return 0
        total = count_ways(i + 1, j)
        if source[i] == target[j]:
            total += count_ways(i + 1, j + 1)
        return total

    total = count_ways(0, 0)
    count_ways.cache_clear()

    masks = []

    def backtrack(i, j, chosen):
        if j == m:
            masks.append(tuple(chosen))
            return
        if i == n or (m - j) > (n - i):
            return
        backtrack(i + 1, j, chosen)
        if source[i] == target[j]:
            chosen.append(i)
            backtrack(i + 1, j + 1, chosen)
            chosen.pop()

    backtrack(0, 0, [])
    assert len(masks) == total, "backtracking enumeration missed matches the DP counted"
    return masks


def mask_differences(masks):
    diffs = []
    for a, b in itertools.combinations(range(len(masks)), 2):
        diff = [
            (masks[a][k] + 1, masks[b][k] + 1)
            for k in range(len(masks[a]))
            if masks[a][k] != masks[b][k]
        ]
        diffs.append((a, b, diff))
    return diffs


def _kmp_automaton(pattern):
    fail = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k > 0 and pattern[i] != pattern[k]:
            k = fail[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        fail[i] = k
    alphabet = set(pattern) | set(NINE_SYMS) | set("abcdefghijklmnopqrstuvwxyz")
    trans = {}
    for state in range(len(pattern)):
        for c in alphabet:
            s = state
            while True:
                if c == pattern[s]:
                    trans[(state, c)] = s + 1
                    break
                elif s == 0:
                    trans[(state, c)] = 0
                    break
                else:
                    s = fail[s - 1]
    return trans


def exact_subset_rate(source, k, target):
    """Exact (hit_count, total_subsets, rate) for a uniform-random
    order-preserving k-subset of source containing target as a contiguous
    substring, via DP: state = (position, subset-size-used, KMP-automaton
    state, found-flag)."""
    n = len(source)
    trans = _kmp_automaton(target)
    match_len = len(target)

    @lru_cache(maxsize=None)
    def rec(i, used, state, found):
        if i == n:
            return 1 if (used == k and found) else 0
        if used > k or (n - i) < (k - used):
            return 0
        total = rec(i + 1, used, state, found)
        if used < k:
            if found:
                total += rec(i + 1, used + 1, state, True)
            else:
                next_state = trans[(state, source[i])]
                next_found = next_state == match_len
                total += rec(
                    i + 1, used + 1, 0 if next_found else next_state, next_found
                )
        return total

    hit_count = rec(0, 0, 0, False)
    rec.cache_clear()
    total_subsets = comb(n, k)
    return hit_count, total_subsets, hit_count / total_subsets


def attempts_for_probability(rate, p):
    return math.ceil(math.log(1 - p) / math.log(1 - rate))


def _brute_force_rate(source, k, target):
    n = len(source)
    hits = 0
    total = 0
    for combo in itertools.combinations(range(n), k):
        total += 1
        s = "".join(source[i] for i in combo)
        if target in s:
            hits += 1
    return hits, total, (hits / total if total else 0.0)


def self_test():
    # Exact DP must match brute-force itertools.combinations enumeration
    # on several tiny synthetic cases.
    tiny_cases = [
        ("aabbccyangzz", 4, "yang"),
        ("yangyangyang", 4, "yang"),
        ("abcdefghijkl", 5, "xyz"),
        ("yayangang", 4, "yang"),
    ]
    for src, k, tgt in tiny_cases:
        dp_hits, dp_total, dp_rate = exact_subset_rate(src, k, tgt)
        bf_hits, bf_total, bf_rate = _brute_force_rate(src, k, tgt)
        assert dp_total == bf_total, f"{src}/{k}/{tgt}: total mismatch {dp_total} != {bf_total}"
        assert dp_hits == bf_hits, f"{src}/{k}/{tgt}: DP {dp_hits} != brute-force {bf_hits}"

    # Real data: recover_position_masks must find exactly 4 masks with the
    # known 57/60, 78/79 (1-based) diff pattern.
    masks = recover_position_masks(SOURCE, TARGET)
    assert len(masks) == 4, f"expected 4 masks, got {len(masks)}"
    diffs = mask_differences(masks)
    diff_positions = set()
    for _, _, diff in diffs:
        for a, b in diff:
            diff_positions.add(frozenset((a, b)))
    assert diff_positions == {frozenset((57, 60)), frozenset((78, 79))}, (
        f"unexpected mask-difference positions: {diff_positions}"
    )

    # RULE_FAMILY on real data: 44 unique outputs, 0 contain "yang", 0
    # reproduce Denis's literal output.
    report = rule_family_report(SOURCE, DBBI)
    assert report["total_rules"] == 44
    assert report["unique_outputs"] == 44, f"expected 44 unique outputs, got {report['unique_outputs']}"
    assert report["contains_target"] == 0, f"expected 0/44 to contain 'yang', got {report['contains_target']}"
    assert report["reproduces_denis"] == 0, f"expected 0/44 to reproduce Denis's output, got {report['reproduces_denis']}"

    # "yang" must be a literal substring of Denis's own posted string;
    # "ying" and "salvation" must not.
    assert "yang" in TARGET
    assert "ying" not in TARGET
    assert "salvation" not in TARGET

    print("[*] self-test OK: DP matches brute force, 4 masks recovered "
          "(57/60, 78/79 ambiguity confirmed), rule family 44/44 unique "
          "with 0 hits, target-substring facts confirmed")


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    print(f"[*] SOURCE ({len(SOURCE)} chars): {SOURCE}")
    print(f"[*] TARGET (Denis's posted 31-char extraction): {TARGET!r}")
    print(f"[*] 'yang' in TARGET: {'yang' in TARGET}   'ying' in TARGET: {'ying' in TARGET}   "
          f"'salvation' in TARGET: {'salvation' in TARGET}")

    report = rule_family_report(SOURCE, DBBI)
    print(f"\n[*] 44-rule family on real data: {report['unique_outputs']}/44 unique outputs, "
          f"{report['contains_target']}/44 contain 'yang', "
          f"{report['reproduces_denis']}/44 reproduce Denis's literal output")

    masks = recover_position_masks(SOURCE, TARGET)
    print(f"\n[*] recovered {len(masks)} order-preserving position masks that reproduce TARGET exactly:")
    for mask in masks:
        print("   ", [i + 1 for i in mask])
    for a, b, diff in mask_differences(masks):
        print(f"    mask {a} vs mask {b} differ only at (1-based): {diff}")

    print("\n[*] exact uniform-subset base rates (not a p-value for Denis's actual rule):")
    for target in ("yang", "ying"):
        for k in (31, 30):
            hits, total, rate = exact_subset_rate(SOURCE, k, target)
            label = "PRIMARY" if (target == "yang" and k == 31) else "secondary/exploratory"
            print(f"    target={target!r:10s} k={k}  rate={rate:.6e}  ({label})")

    _, _, primary_rate = exact_subset_rate(SOURCE, 31, "yang")
    n50 = attempts_for_probability(primary_rate, 0.5)
    n90 = attempts_for_probability(primary_rate, 0.9)
    print(f"\n[*] hypothetical attempt counts at the primary rate ({primary_rate:.9f}):")
    print(f"    {n50} independent order-preserving 31-subsets would give a 50% chance of >=1 'yang' hit")
    print(f"    {n90} independent order-preserving 31-subsets would give a 90% chance of >=1 'yang' hit")
    print("    (NOT a claim about how many extraction rules Denis actually tried -- that count is unknown)")


if __name__ == "__main__":
    main()
