#!/usr/bin/env python3
"""Bounded Roman-numeral audit for the DBBI/FAED and 401/400 observation.

Keep only standard Roman-numeral letters from each authentic stream prefix,
preserving order, and combine that projection with an order-preserving subset
of the decorated *Cosmic Duality* title initials ``CD``.  Strict canonical
Roman syntax is required; permissive forms such as ``IC`` are rejected.

The observed construction is::

    DBBI -> DI; C + DI -> CDI = 401
    FAED -> D;  C + D  -> CD  = 400

This module measures uniqueness only inside the explicitly disclosed bounded
family.  It does not treat that family as a probability model, does not claim
that the title selects ``C`` alone, and does not explain the FEFE sum 73.
"""

import itertools

from cosmic_duality_dropcap_inventory import TITLE_INITIALS
from first_piece_prime_sum_reconstruction import EXPECTED_FITTED_SUMS


ROMAN_VALUES = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}
ROMAN_DIGITS = tuple(ROMAN_VALUES)

RAILS = ("DBBI", "FAED")

# Authenticated/high-salience labels and literal macro tokens already present
# in the puzzle record.  This is a disclosed sensitivity set, not a random
# sample and therefore not a basis for a chance probability.
CONTROL_TOKENS = (
    "DBBI",
    "FAED",
    "FEFE",
    "yellowblueprime",
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yinyang",
    "thispassword",
    "SalPhaseIon",
    "CosmicDuality",
    "gsmg.io",
    "theseedisplanted",
    "architect",
)


def roman_projection(text):
    return "".join(character for character in text.upper() if character in ROMAN_VALUES)


def to_roman(value):
    if not 0 < value < 4000:
        raise ValueError("canonical Roman range is 1..3999")
    table = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    output = []
    for amount, numeral in table:
        count, value = divmod(value, amount)
        output.append(numeral * count)
    return "".join(output)


def parse_canonical_roman(numeral):
    """Return the value only when *numeral* is strict canonical Roman."""
    if not numeral or any(character not in ROMAN_VALUES for character in numeral):
        return None
    total = 0
    for index, character in enumerate(numeral):
        value = ROMAN_VALUES[character]
        next_value = ROMAN_VALUES[numeral[index + 1]] if index + 1 < len(numeral) else 0
        total += -value if value < next_value else value
    if not 0 < total < 4000 or to_roman(total) != numeral:
        return None
    return total


def order_preserving_subsequences(text):
    return tuple(
        "".join(text[index] for index in range(len(text)) if mask & (1 << index))
        for mask in range(1 << len(text))
    )


def title_contexts():
    """Nonredundant empty/prefix/suffix contexts from title subsequences."""
    subsets = order_preserving_subsequences(TITLE_INITIALS)
    return (("none", ""),) + tuple(
        (placement, subset)
        for subset in subsets
        if subset
        for placement in ("prefix", "suffix")
    )


def apply_context(token, placement, title_fragment):
    projection = roman_projection(token)
    if placement == "none":
        numeral = projection
    elif placement == "prefix":
        numeral = title_fragment + projection
    elif placement == "suffix":
        numeral = projection + title_fragment
    else:
        raise ValueError(placement)
    return numeral, parse_canonical_roman(numeral)


def evaluate_pair(blue_token, yellow_token, placement, title_fragment):
    blue_numeral, blue_value = apply_context(blue_token, placement, title_fragment)
    yellow_numeral, yellow_value = apply_context(yellow_token, placement, title_fragment)
    return {
        "blue_token": blue_token,
        "yellow_token": yellow_token,
        "placement": placement,
        "title_fragment": title_fragment,
        "blue_projection": roman_projection(blue_token),
        "yellow_projection": roman_projection(yellow_token),
        "blue_numeral": blue_numeral,
        "yellow_numeral": yellow_numeral,
        "blue_value": blue_value,
        "yellow_value": yellow_value,
        "ordered_target_match": (
            blue_value == EXPECTED_FITTED_SUMS["B"]
            and yellow_value == EXPECTED_FITTED_SUMS["Y"]
        ),
    }


def audit():
    contexts = title_contexts()
    rail_rows = tuple(
        evaluate_pair(blue, yellow, placement, fragment)
        for blue, yellow in itertools.permutations(RAILS)
        for placement, fragment in contexts
    )
    control_rows = tuple(
        evaluate_pair(blue, yellow, placement, fragment)
        for blue, yellow in itertools.permutations(CONTROL_TOKENS, 2)
        for placement, fragment in contexts
    )
    return {
        "title_initials": TITLE_INITIALS,
        "title_contexts": contexts,
        "rail_rows": rail_rows,
        "rail_match_rows": tuple(row for row in rail_rows if row["ordered_target_match"]),
        "control_rows": control_rows,
        "control_match_rows": tuple(row for row in control_rows if row["ordered_target_match"]),
        "fitted_sums": dict(EXPECTED_FITTED_SUMS),
        "fefe_projection": roman_projection("FEFE"),
    }


def self_test():
    report = audit()
    assert report["title_initials"] == "CD"
    assert report["title_contexts"] == (
        ("none", ""),
        ("prefix", "C"), ("suffix", "C"),
        ("prefix", "D"), ("suffix", "D"),
        ("prefix", "CD"), ("suffix", "CD"),
    )
    assert roman_projection("DBBI") == "DI"
    assert roman_projection("FAED") == "D"
    assert roman_projection("FEFE") == ""
    assert parse_canonical_roman("CDI") == 401
    assert parse_canonical_roman("CD") == 400
    assert parse_canonical_roman("IC") is None
    assert len(report["rail_rows"]) == 14
    assert len(report["rail_match_rows"]) == 1
    match = report["rail_match_rows"][0]
    assert (match["blue_token"], match["yellow_token"]) == ("DBBI", "FAED")
    assert (match["placement"], match["title_fragment"]) == ("prefix", "C")
    assert (match["blue_numeral"], match["yellow_numeral"]) == ("CDI", "CD")
    assert (match["blue_value"], match["yellow_value"]) == (401, 400)
    assert len(report["control_rows"]) == 1092
    assert len(report["control_match_rows"]) == 2
    assert tuple(
        (
            row["blue_token"], row["yellow_token"],
            row["placement"], row["title_fragment"],
        )
        for row in report["control_match_rows"]
    ) == (
        ("DBBI", "FAED", "prefix", "C"),
        ("yinyang", "FEFE", "prefix", "CD"),
    )
    assert report["fitted_sums"] == {"B": 401, "Y": 400, "F": 73}
    assert report["fefe_projection"] == ""
    print(
        "[*] self-test OK: C+roman(DBBI)=CDI=401 and "
        "C+roman(FAED)=CD=400 is the unique ordered hit in 14 rail-family "
        "configurations; the 1,092 disclosed token-pair controls contain two "
        "hits (DBBI/FAED and yinyang/FEFE), so the form is not globally unique; "
        "FEFE/73 unresolved"
    )


def main():
    report = audit()
    for row in report["rail_rows"]:
        print(
            f"B={row['blue_token']} Y={row['yellow_token']} "
            f"context={row['placement']}:{row['title_fragment'] or '-'} "
            f"=> {row['blue_numeral'] or '-'}={row['blue_value']} / "
            f"{row['yellow_numeral'] or '-'}={row['yellow_value']} "
            f"match={row['ordered_target_match']}"
        )
    print(f"rail matches: {len(report['rail_match_rows'])}/{len(report['rail_rows'])}")
    print(
        f"control matches: {len(report['control_match_rows'])}/"
        f"{len(report['control_rows'])}"
    )
    print("FEFE Roman projection: empty (73 remains unexplained)")


if __name__ == "__main__":
    self_test()
    main()
