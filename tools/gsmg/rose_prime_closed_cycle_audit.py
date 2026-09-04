#!/usr/bin/env python3
"""Audit the bounded rotation/type family that uniquely produces THEFLOWER.

The family is fixed by existing rules: four physical grille rotations, both
bit polarities, both turn directions, six-decimal-digit matrix eligibility,
elementwise matrix addition, framed edges, TRUE parity rails, and all nine
selected-word affixes.  F73D92's prior rose/pink interpretation is reported
only as provenance for the winning anchor, not counted as an independent
semantic validation.
"""

from collections import Counter

from denis_rotation_grille_audit import audit as rotation_audit
from first_hint_hash_audit import PHASE1_PASSWORD
from first_piece_color_reconstruction import is_prime
from flower_prefix_checkpoint_audit import (
    EXPECTED_PREFIX,
    affix_family,
    parity_compositions,
)
from prime_matrixsum_reconstruction import load_architect_words
from second_prime_matrixsumlist_audit import (
    framed_edges,
    matrix_sum_list,
    selected_words,
)


F73D92_SOURCE_WORD = "F73D92"
ROSE_RGB = (247, 61, 146)
EXPECTED_ELIGIBLE_VALUES = (574061, 311027)


def polarity_value(raw_word, polarity):
    raw = int(raw_word, 16)
    if polarity == "raw_dark_one":
        return raw, raw_word
    if polarity == "inverse_light_one":
        inverse = raw ^ 0xFFFFFF
        return inverse, f"{inverse:06X}"
    raise ValueError(f"unknown polarity: {polarity}")


def is_six_decimal_digits(value):
    return 100000 <= value <= 999999


def add_matrices(left, right):
    return tuple(
        tuple(a + b for a, b in zip(left_row, right_row))
        for left_row, right_row in zip(left, right)
    )


def matrix_indices(matrix):
    return (
        sum(sum(row) for row in matrix),
        *(sum(row) for row in matrix),
    )


def enumerate_geometry_paths(words):
    """Four starts x two directions x two polarities."""
    for polarity in ("raw_dark_one", "inverse_light_one"):
        for start in range(4):
            for direction, step in (("cw", 1), ("ccw", -1)):
                partner = (start + step) % 4
                anchor_value, anchor_word = polarity_value(words[start], polarity)
                partner_value, partner_word = polarity_value(
                    words[partner], polarity
                )
                yield {
                    "polarity": polarity,
                    "direction": direction,
                    "start_turn": start,
                    "partner_turn": partner,
                    "source_anchor_word": words[start],
                    "source_partner_word": words[partner],
                    "anchor_word": anchor_word,
                    "partner_word": partner_word,
                    "anchor_value": anchor_value,
                    "partner_value": partner_value,
                    "anchor_six_digit": is_six_decimal_digits(anchor_value),
                    "partner_six_digit": is_six_decimal_digits(partner_value),
                    "anchor_prime": is_prime(anchor_value),
                    "partner_prime": is_prime(partner_value),
                }


def expand_matrix_path(path, tokens):
    anchor_matrix, anchor_indices = matrix_sum_list(path["anchor_value"])
    partner_matrix, partner_indices = matrix_sum_list(path["partner_value"])
    combined_matrix = add_matrices(anchor_matrix, partner_matrix)
    combined_indices = matrix_indices(combined_matrix)
    all_indices = (*anchor_indices, *partner_indices, *combined_indices)
    if min(all_indices) < 1 or max(all_indices) > len(tokens):
        return {**path, "indexable": False}

    anchor_words = selected_words(tokens, anchor_indices)
    partner_words = selected_words(tokens, partner_indices)
    combined_words = selected_words(tokens, combined_indices)
    frames = tuple(
        framed_edges(words)
        for words in (anchor_words, partner_words, combined_words)
    )
    compositions = parity_compositions(frames[1], frames[2])
    affixes = affix_family(
        compositions, anchor_words + partner_words + combined_words
    )
    prefix_hits = tuple(
        item for item in affixes if item["value"] == EXPECTED_PREFIX
    )
    return {
        **path,
        "indexable": True,
        "anchor_matrix": anchor_matrix,
        "partner_matrix": partner_matrix,
        "combined_matrix": combined_matrix,
        "anchor_indices": anchor_indices,
        "partner_indices": partner_indices,
        "combined_indices": combined_indices,
        "anchor_words": anchor_words,
        "partner_words": partner_words,
        "combined_words": combined_words,
        "frames": frames,
        "compositions": compositions,
        "affixes": affixes,
        "prefix_hits": prefix_hits,
    }


def path_family(words, tokens):
    counts = Counter()
    paths = tuple(enumerate_geometry_paths(words))
    eligible = []
    expanded = []
    prefix_hits = []
    rose_pole_anchor_hits = []
    for path in paths:
        counts["geometry_paths"] += 1
        if not (path["anchor_six_digit"] and path["partner_six_digit"]):
            continue
        counts["six_digit_paths"] += 1
        eligible.append(path)
        if path["anchor_prime"] and path["partner_prime"]:
            counts["two_prime_paths"] += 1
        item = expand_matrix_path(path, tokens)
        expanded.append(item)
        if not item["indexable"]:
            counts["unindexable_matrix_paths"] += 1
            continue
        counts["indexable_matrix_paths"] += 1
        counts["composition_variants"] += len(item["compositions"])
        counts["affix_variants"] += len(item["affixes"])
        for hit in item["prefix_hits"]:
            record = {"path": item, "affix": hit}
            prefix_hits.append(record)
            counts["theflower_hits"] += 1
            if item["source_anchor_word"] == F73D92_SOURCE_WORD:
                rose_pole_anchor_hits.append(record)
                counts["theflower_at_rose_pole_anchor"] += 1
    return {
        "counts": counts,
        "paths": paths,
        "eligible": tuple(eligible),
        "expanded": tuple(expanded),
        "prefix_hits": tuple(prefix_hits),
        "rose_pole_anchor_hits": tuple(rose_pole_anchor_hits),
    }


def audit():
    rotation = rotation_audit()
    tokens, _ = load_architect_words()
    spiral = path_family(rotation["spiral_words"], tokens)
    row_major = path_family(rotation["row_major_words"], tokens)
    inverse_six_digit_values = tuple(
        value
        for value in rotation["inverse_values"]
        if is_six_decimal_digits(value)
    )
    return {
        "spiral_words": rotation["spiral_words"],
        "inverse_words": rotation["inverse_words"],
        "inverse_values": rotation["inverse_values"],
        "inverse_six_digit_values": inverse_six_digit_values,
        "f73d92_source_word": F73D92_SOURCE_WORD,
        "rose_rgb": ROSE_RGB,
        "spiral": spiral,
        "row_major": row_major,
        "phase1_password": PHASE1_PASSWORD.decode(),
    }


def self_test():
    result = audit()
    assert result["spiral_words"] == (
        "F73D92", "FB410C", "ADAFEF", "2FF081"
    )
    assert result["inverse_values"] == (574061, 311027, 5394448, 13635454)
    assert result["inverse_six_digit_values"] == EXPECTED_ELIGIBLE_VALUES
    assert result["rose_rgb"] == (247, 61, 146)

    counts = result["spiral"]["counts"]
    assert counts == Counter(
        geometry_paths=16,
        six_digit_paths=2,
        two_prime_paths=2,
        indexable_matrix_paths=2,
        composition_variants=32,
        affix_variants=576,
        theflower_hits=1,
        theflower_at_rose_pole_anchor=1,
    )
    assert tuple(
        (path["start_turn"], path["direction"], path["polarity"])
        for path in result["spiral"]["eligible"]
    ) == (
        (0, "cw", "inverse_light_one"),
        (1, "ccw", "inverse_light_one"),
    )
    hit = result["spiral"]["rose_pole_anchor_hits"][0]
    path = hit["path"]
    affix = hit["affix"]
    assert (path["anchor_value"], path["partner_value"]) == (574061, 311027)
    assert path["frames"] == ("buth", "flow", "true")
    assert path["combined_matrix"] == ((8, 8, 5), (0, 8, 8))
    assert (
        affix["composition"]["value"],
        affix["word"],
        affix["side"],
        affix["value"],
    ) == ("flower", "the", "prefix", "theflower")
    assert result["phase1_password"].startswith("theflower")
    assert result["row_major"]["counts"] == Counter(geometry_paths=16)
    assert result["row_major"]["eligible"] == ()
    assert result["row_major"]["rose_pole_anchor_hits"] == ()


def main():
    self_test()
    result = audit()
    print("spiral rotations:")
    for turn, (raw, inverse, value) in enumerate(
        zip(
            result["spiral_words"],
            result["inverse_words"],
            result["inverse_values"],
        )
    ):
        print(
            f"  {turn * 90:3d} deg: {raw} -> {inverse} = {value} "
            f"(digits={len(str(value))}, prime={is_prime(value)})"
        )
    counts = result["spiral"]["counts"]
    print(
        "geometry/type gate:",
        f"{counts['six_digit_paths']}/{counts['geometry_paths']} paths;",
        f"two-prime={counts['two_prime_paths']}",
    )
    print(
        "composition family:",
        f"{counts['theflower_hits']}/{counts['affix_variants']} THEFLOWER;",
        "THEFLOWER hits anchored at F73D92=",
        counts["theflower_at_rose_pole_anchor"],
    )
    hit = result["spiral"]["rose_pole_anchor_hits"][0]
    path = hit["path"]
    print(
        "unique THEFLOWER path:",
        f"{path['source_anchor_word']} (prior rose/pink label) -> ",
        f"{path['anchor_value']} -> {path['partner_value']} -> ",
        f"{'/'.join(frame.upper() for frame in path['frames'])} -> ",
        hit["affix"]["value"].upper(),
    )
    print(
        "row-major control:",
        f"six-digit paths={result['row_major']['counts']['six_digit_paths']}",
    )


if __name__ == "__main__":
    main()
