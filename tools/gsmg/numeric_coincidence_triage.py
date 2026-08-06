#!/usr/bin/env python3
"""Brainstorm item 9 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md` section 9):
a triage tool, not a finding generator.

Takes every creator-confirmed "load-bearing" number already established
elsewhere in this project (each with its own provenance note below) and
checks pairwise arithmetic relationships (sum, difference, product,
concatenation, division, modular reduction) plus single-number digit sums,
purely to produce a ranked shortlist of "this deserves a human look" --
explicitly NOT to promote any hit without the project's usual null-model
gate (see `doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md`'s repeated apophenia
corrections, e.g. the "matrixsumlist triangle" and cross-phase "yang"
debunks). Every number here already has an independent, cited derivation;
this script only asks whether any of them are *also* related to each other
by simple arithmetic, which would be a genuinely new observation rather
than a restatement of something already known (e.g. 91 = 7x13 is already
established elsewhere and is deliberately not rediscovered as "new" here).

This is intentionally a closed, named registry, not an open numeric search
over "every number that appears anywhere in the puzzle" -- that would have
no principled stopping point and would just manufacture coincidences.
"""

import argparse
import itertools
from collections import defaultdict

# name -> (value, provenance)
NUMBERS = {
    "SPIRAL_PRIME": (574061, "prime formed from the yellow/blue Phase-0 spiral complement (first-piece reconstruction)"),
    "MATRIX_TOTAL": (23, "matrixsumlist total row+col sum, selects BOTH/ULTIMATELY/THE in the Architect speech"),
    "MATRIX_ROW1": (16, "matrixsumlist row-1 sum"),
    "MATRIX_ROW2": (7, "matrixsumlist row-2 sum (= 23 - 16)"),
    "FEFE_SPIRAL_POS": (163, "zero-based spiral position of the anomalous FEFE marker (prime)"),
    "DBBI_LEN": (91, "raw DBBI checkerboard stream length (= 7x13)"),
    "FAED_LEN": (570, "raw FAED checkerboard stream length (= 15x38)"),
    "SALPHASEION_TEXTAREA_LEN": (1075, "total logical character length of the SalPhaseIon textarea"),
    "MATRIXSUMLIST_BITS": (104, "binary-encoded matrixsumlist instruction length in bits"),
    "SALPH_CIPHERTEXT_BYTES": (80, "SALPH / P32TRAILING AES ciphertext length in bytes, post Salted__+salt"),
    "COSMIC_CIPHERTEXT_BYTES": (1328, "COSMIC AES ciphertext length in bytes, post Salted__+salt"),
    "URLBLOB_CIPHERTEXT_BYTES": (96, "quarantined URLBLOB AES ciphertext length in bytes"),
    "DBBI_SELECTION_LEN": (31, "recovered prime-walk selection length from the 91-char Phase 3.2.2 answer"),
    "YOUWON_OFFSET": (21, "zero-based offset where YOUWON begins inside its 91-char host string"),
    "YOUWON_REMAINDER": (64, "characters left after YOUWON in its host string; also each SALPH AES base64 half's length"),
    "LASTWORDS_LEN": (63, "decoded lastwordsbeforearchichoice segment length"),
    "THISPASSWORD_LEN": (29, "decoded thispassword segment length"),
    "COSMIC_LINES": (28, "authored newline-delimited lines in the Cosmic Duality textarea"),
    "SPIRAL_CELLS": (24, "yellow/blue spiral cell count = byte boundaries reconstructed in Phase 0"),
    "AL_ATOMIC_NUMBER": (13, "aluminum atomic number, used in the SALPHATION/SALVATION element-count check"),
}

def digit_sum(n):
    total = 0
    n = abs(n)
    while n:
        total += n % 10
        n //= 10
    return total


def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def registry_lookup():
    by_value = defaultdict(list)
    for name, (value, _note) in NUMBERS.items():
        by_value[value].append(name)
    return by_value


def single_number_facts(by_value):
    facts = []
    for name, (value, note) in NUMBERS.items():
        ds = digit_sum(value)
        if ds in by_value:
            facts.append({
                "kind": "digit_sum",
                "expression": f"digit_sum({name}={value}) = {ds}",
                "matches": [n for n in by_value[ds] if n != name],
                "value": ds,
            })
        if is_prime(value):
            facts.append({
                "kind": "primality",
                "expression": f"{name}={value} is prime",
                "matches": [],
                "value": value,
            })
    return facts


def pairwise_facts(by_value):
    facts = []
    names = list(NUMBERS)
    for name_a, name_b in itertools.combinations(names, 2):
        a, _ = NUMBERS[name_a]
        b, _ = NUMBERS[name_b]
        lo, hi = (a, b) if a <= b else (b, a)
        candidates = [
            ("sum", a + b),
            ("abs_diff", abs(a - b)),
            ("product", a * b),
            ("concat_ab", int(f"{a}{b}")),
            ("concat_ba", int(f"{b}{a}")),
            ("floordiv", hi // lo if lo and hi % lo == 0 else None),
        ]
        for op, result in candidates:
            if result is None:
                continue
            if result in by_value:
                matches = [n for n in by_value[result] if n not in (name_a, name_b)]
                if not matches:
                    continue
                facts.append({
                    "kind": "pairwise",
                    "expression": f"{op}({name_a}={a}, {name_b}={b}) = {result}",
                    "matches": matches,
                    "value": result,
                })
    return facts


def rank(facts):
    scored = defaultdict(list)
    for fact in facts:
        if not fact["matches"] and fact["kind"] != "primality":
            continue
        scored[fact["value"]].append(fact)
    ranked = sorted(scored.items(), key=lambda kv: -len(kv[1]))
    return ranked


def print_report(pairwise, singles):
    print(f"[*] registry: {len(NUMBERS)} numbers, {len(list(itertools.combinations(NUMBERS, 2)))} pairs")
    print()
    print("[*] single-number facts (primality, digit sums that hit the registry):")
    for fact in singles:
        marker = f"  <-- matches {fact['matches']}" if fact["matches"] else ""
        print(f"    {fact['expression']}{marker}")
    print()
    print("[*] pairwise coincidences that land on another registry value (ranked by recurrence):")
    ranked = rank(pairwise)
    if not ranked:
        print("    none")
    for value, facts in ranked:
        target_names = registry_lookup()[value]
        print(f"    -> {value} ({', '.join(target_names)}), {len(facts)} independent derivation(s):")
        for fact in facts:
            print(f"       {fact['expression']}")
    print()
    print(
        "[*] NOTE: this is a screening list, not a finding. Any entry worth acting "
        "on still needs the project's usual null-model / base-rate gate (Phase 98 "
        "style) before being treated as signal. Modular-reduction operations were "
        "deliberately excluded from this sweep: an earlier draft tested sum/product "
        "mod each of 9 small primes and produced dozens of pigeonhole-guaranteed "
        "hits on the registry's small values (7, 13, 16, ...), which is noise, not "
        "signal -- any two numbers have roughly a 1/p chance of colliding mod a "
        "small prime p, so testing 9 primes across ~190 pairs manufactures hits by "
        "construction. Only exact operations (sum, difference, product, "
        "concatenation, and *exact* integer division) are reported here."
    )


def self_test():
    by_value = registry_lookup()
    assert NUMBERS["SPIRAL_PRIME"][0] == 574061
    assert digit_sum(574061) == 23
    assert 23 in by_value  # the already-known digit-sum match
    assert is_prime(163)
    assert is_prime(574061)
    print("[*] self-test OK: registry values and known digit-sum match verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    by_value = registry_lookup()
    singles = single_number_facts(by_value)
    pairwise = pairwise_facts(by_value)
    print_report(pairwise, singles)


if __name__ == "__main__":
    main()
