#!/usr/bin/env python3
"""Measure whether BUT/HYE independently establishes the yin-yang state."""

import argparse
import itertools
import json

import architect_choice_boundary_audit as boundary
from prime_matrixsum_reconstruction import mirror9


NINE = "abcdefghi"
FIXED_INDICES = (23, 16, 7)


def filtered(value):
    return "".join(char for char in value if char in NINE)


def rails(tokens):
    return (
        "".join(token[0] for token in tokens),
        "".join(token[-1] for token in tokens),
    )


def mirror_set_closed(initials, finals):
    symbols = set(filtered(initials) + filtered(finals))
    return bool(symbols) and {mirror9(symbol) for symbol in symbols} == symbols


def strict_positional_mirror(initials, finals):
    left, right = filtered(initials), filtered(finals)
    return (
        bool(left)
        and len(left) == len(right)
        and "".join(mirror9(char) for char in left) == right
    )


def partial_mirror_plus_fixed_e(initials, finals):
    """The exact special-case rule used by the earlier BUT/HYE narrative."""
    left, right = filtered(initials), filtered(finals)
    return (
        len(left) == 1
        and len(right) == 2
        and mirror9(left) == right[0]
        and mirror9(right[1]) == right[1]
    )


def row(indices, words):
    selected = tuple(words[index - 1] for index in indices)
    initials, finals = rails(selected)
    return {
        "indices": tuple(indices),
        "tokens": selected,
        "initials": initials,
        "finals": finals,
        "filtered_initials": filtered(initials),
        "filtered_finals": filtered(finals),
        "mirror_set_closed": mirror_set_closed(initials, finals),
        "strict_positional_mirror": strict_positional_mirror(initials, finals),
        "partial_mirror_plus_fixed_e": partial_mirror_plus_fixed_e(initials, finals),
    }


def audit():
    base = boundary.audit()
    film = base["sources"]["film"]["moment_to_choice"]["tokens"]
    screenplay = base["sources"]["screenplay"]["moment_to_choice"]["tokens"]
    stable_positions = tuple(
        index + 1
        for index in range(min(len(film), len(screenplay)))
        if film[index] == screenplay[index]
    )

    fixed = row(FIXED_INDICES, film)
    if fixed["tokens"] != ("both", "ultimately", "the"):
        raise AssertionError("fixed Architect selection changed")
    permutations = tuple(
        row(indices, film) for indices in itertools.permutations(FIXED_INDICES)
    )

    but_rows = []
    for indices in itertools.permutations(stable_positions, 3):
        candidate = row(indices, film)
        if candidate["initials"] == "but":
            but_rows.append(candidate)

    counts = {
        "cross_source_stable_positions": len(stable_positions),
        "ordered_distinct_triples": len(stable_positions)
        * (len(stable_positions) - 1)
        * (len(stable_positions) - 2),
        "but_initial_rows": len(but_rows),
        "but_and_exact_hye_rows": sum(item["finals"] == "hye" for item in but_rows),
        "but_and_mirror_closed_rows": sum(item["mirror_set_closed"] for item in but_rows),
        "but_and_partial_rule_rows": sum(
            item["partial_mirror_plus_fixed_e"] for item in but_rows
        ),
        "but_and_strict_positional_rows": sum(
            item["strict_positional_mirror"] for item in but_rows
        ),
    }
    return {
        "fixed_selection": fixed,
        "fixed_word_permutations": permutations,
        "control_counts": counts,
        "conditional_rates": {
            "exact_hye_given_but": counts["but_and_exact_hye_rows"]
            / counts["but_initial_rows"],
            "mirror_closed_given_but": counts["but_and_mirror_closed_rows"]
            / counts["but_initial_rows"],
            "partial_rule_given_but": counts["but_and_partial_rule_rows"]
            / counts["but_initial_rows"],
        },
        "permutation_invariance": {
            "mirror_closed_passes": sum(item["mirror_set_closed"] for item in permutations),
            "partial_rule_passes": sum(
                item["partial_mirror_plus_fixed_e"] for item in permutations
            ),
            "strict_positional_passes": sum(
                item["strict_positional_mirror"] for item in permutations
            ),
        },
        "retained": (
            "[23,16,7] forward-one is cross-source stable",
            "BOTH/ULTIMATELY/THE gives BUT/HYE",
            "BUT equals the literal next spoken word after choice",
        ),
        "downgraded": (
            "filtering the rails to a-i",
            "calling the resulting mirror-closed set the reached yinyang state",
        ),
        "verdict": (
            "BUT/HYE is a robust boundary reconstruction, but the mirror9 "
            "interpretation does not independently establish yinyang. The "
            "strict positional rule fails (B versus HE), the special partial "
            "rule occurs in 10/48 comparable source-stable BUT rows, and set "
            "closure survives all six permutations of the fixed words. Treat "
            "yinyang as not yet mechanically reached."
        ),
    }


def self_test():
    report = audit()
    counts = report["control_counts"]
    assert report["fixed_selection"]["initials"] == "but"
    assert report["fixed_selection"]["finals"] == "hye"
    assert report["fixed_selection"]["mirror_set_closed"]
    assert not report["fixed_selection"]["strict_positional_mirror"]
    assert counts == {
        "cross_source_stable_positions": 34,
        "ordered_distinct_triples": 35904,
        "but_initial_rows": 48,
        "but_and_exact_hye_rows": 5,
        "but_and_mirror_closed_rows": 18,
        "but_and_partial_rule_rows": 10,
        "but_and_strict_positional_rows": 6,
    }
    assert report["permutation_invariance"] == {
        "mirror_closed_passes": 6,
        "partial_rule_passes": 3,
        "strict_positional_passes": 0,
    }
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: BUT retained; yinyang mirror interpretation downgraded")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
