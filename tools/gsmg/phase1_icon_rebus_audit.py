#!/usr/bin/env python3
"""Audit the visible Stage-1 icon rebus and the proposed overlap-number idea.

The eight images on ``gsmg.io/theseedisplanted`` are displayed as four
black/blue fragments followed by four red fragments. Rearranging them into
semantic pairs gives four deliberate text constructions:

* ``LO`` inserted into ``CRYPTO / GIC`` -> ``CRYPTOLOGIC``;
* ``WAR`` + ``N / ING`` -> ``WARNING``;
* ``CA`` + ``N / YOU`` -> ``CAN YOU``;
* ``DIG / I / +`` + ``T / -`` -> ``DIG IT``.

The first two identify the song ``The Warning`` by Logic, exactly as recorded
in the historical 2021 solution README. The last two reproduce the earlier
prompt ``Can you dig it?``.

Separately, test whether the white-pixel overlap areas encode a number. Source
images are center-padded without resizing, and the intended four-pair matching
is compared with all 4! left-to-right perfect matchings.

Finally, measure the colored/white/colored band widths suggested by Telegram
message 670 directly from the original PNGs. The montage itself has
community-added borders and an explicitly uncertain row order, so those
additions are not treated as creator-authored geometry.

A third, narrower follow-up: each row visually splits into three flat color
bands (blue/black, white, red). Measured directly on each file's own unpadded
pixels, the colored bands stay a near-constant 66-70px (consistent with a
fixed icon/text drawing size) while the white gap between the two files
shrinks 28/24/21/19px row-to-row with no clean arithmetic step -- most
consistent with inconsistent manual cropping of the source screenshot, not an
encoded number.
"""

import argparse
import itertools
from pathlib import Path

import numpy as np
from PIL import Image

ICON_DIR = Path(__file__).resolve().parents[2] / "doc" / "img"

ICONS = {
    "lock_lo": ("gsmg_icon_blue_lock_lo.png", ("LO",)),
    "bank_war": ("gsmg_icon_black_banking_war.png", ("WAR",)),
    "ca": ("gsmg_icon_blue_ca.png", ("CA",)),
    "dig_i_plus": ("gsmg_icon_blue_dig_i.png", ("DIG", "I", "+")),
    "crypto_gic": ("gsmg_icon_red_crypto_gic.png", ("CRYPTO", "GIC")),
    "openlock_n_ing": ("gsmg_icon_red_open_lock_n_ing.png", ("N", "ING")),
    "n_you": ("gsmg_icon_red_n_you.png", ("N", "YOU")),
    "t_minus": ("gsmg_icon_red_t.png", ("T", "-")),
}

LEFT_ICONS = ("lock_lo", "bank_war", "ca", "dig_i_plus")
RIGHT_ICONS = ("crypto_gic", "openlock_n_ing", "n_you", "t_minus")
INTENDED_MATCHING = tuple(zip(LEFT_ICONS, RIGHT_ICONS))

CANVAS = (82, 70)
WHITE_THRESHOLD = 200

EXPECTED_CROSS_INTERSECTIONS = {
    "lock_lo": (81, 224, 45, 11),
    "bank_war": (108, 194, 33, 8),
    "ca": (13, 31, 4, 0),
    "dig_i_plus": (22, 54, 35, 0),
}
EXPECTED_INTENDED_SUM = 279
EXPECTED_INTENDED_RANKS = (19, 20)
EXPECTED_AT_LEAST_AS_LARGE = 6

# Follow-up (2026-07-26): measure the three source-native bands suggested by
# the community montage, excluding its added black borders and JPEG artifacts.
WIDTH_THRESHOLD = 200
EXPECTED_ROW_WIDTHS = {
    ("lock_lo", "crypto_gic"): (66, 28, 67),
    ("bank_war", "openlock_n_ing"): (70, 24, 66),
    ("ca", "n_you"): (70, 21, 67),
    ("dig_i_plus", "t_minus"): (70, 19, 67),
}


def white_mask(name):
    file_name, _ = ICONS[name]
    image = Image.open(ICON_DIR / file_name).convert("RGBA")
    if image.width > CANVAS[0] or image.height > CANVAS[1]:
        raise ValueError(f"{file_name} exceeds fixed canvas {CANVAS}: {image.size}")

    array = np.array(image)
    foreground = (array[:, :, :3] > WHITE_THRESHOLD).all(axis=2) & (
        array[:, :, 3] > 0
    )
    mask = np.zeros((CANVAS[1], CANVAS[0]), dtype=bool)
    x_offset = (CANVAS[0] - image.width) // 2
    y_offset = (CANVAS[1] - image.height) // 2
    mask[
        y_offset : y_offset + image.height,
        x_offset : x_offset + image.width,
    ] = foreground
    return mask


def cross_intersections():
    masks = {name: white_mask(name) for name in ICONS}
    return {
        (left, right): int((masks[left] & masks[right]).sum())
        for left in LEFT_ICONS
        for right in RIGHT_ICONS
    }


def matching_scores(intersections=None):
    if intersections is None:
        intersections = cross_intersections()
    scores = []
    for right_order in itertools.permutations(RIGHT_ICONS):
        matching = tuple(zip(LEFT_ICONS, right_order))
        score = sum(intersections[pair] for pair in matching)
        scores.append((score, matching))
    return tuple(sorted(scores))


def colored_extent(name):
    """(left_margin, colored_width, right_margin, total_width) for one icon,
    measured directly on its own (unpadded, unresized) pixels."""
    file_name, _ = ICONS[name]
    image = Image.open(ICON_DIR / file_name).convert("RGBA")
    array = np.array(image)
    rgb = array[:, :, :3]
    alpha = array[:, :, 3]
    is_white = (rgb[:, :, 0] > WIDTH_THRESHOLD) & (rgb[:, :, 1] > WIDTH_THRESHOLD) & (
        rgb[:, :, 2] > WIDTH_THRESHOLD
    )
    is_background = is_white | (alpha < 10)
    colored_columns = ~np.all(is_background, axis=0)
    xs = np.where(colored_columns)[0]
    left_margin = int(xs.min())
    right_margin = int(image.width - 1 - xs.max())
    colored_width = int(xs.max() - xs.min() + 1)
    return left_margin, colored_width, right_margin, image.width


def row_band_widths():
    widths = {}
    for left, right in INTENDED_MATCHING:
        _, left_colored, left_right_margin, _ = colored_extent(left)
        right_left_margin, right_colored, _, _ = colored_extent(right)
        white_width = left_right_margin + right_left_margin
        widths[(left, right)] = (left_colored, white_width, right_colored)
    return widths


def rebus_outputs():
    return {
        "song": "WAR" + "N" + "ING",
        "artist": "CRYPTO" + "LO" + "GIC",
        "prompt": ("CA" + "N" + "YOU", "DIG" + "I" + "T"),
    }


def self_test():
    intersections = cross_intersections()
    for left, expected_row in EXPECTED_CROSS_INTERSECTIONS.items():
        actual_row = tuple(intersections[(left, right)] for right in RIGHT_ICONS)
        assert actual_row == expected_row, (left, actual_row, expected_row)

    scores = matching_scores(intersections)
    intended_score = next(
        score for score, matching in scores if matching == INTENDED_MATCHING
    )
    intended_ranks = tuple(
        index
        for index, (score, _matching) in enumerate(scores, start=1)
        if score == intended_score
    )
    at_least_as_large = sum(score >= intended_score for score, _ in scores)
    assert len(scores) == 24
    assert intended_score == EXPECTED_INTENDED_SUM
    assert intended_ranks == EXPECTED_INTENDED_RANKS
    assert at_least_as_large == EXPECTED_AT_LEAST_AS_LARGE

    outputs = rebus_outputs()
    assert outputs == {
        "song": "WARNING",
        "artist": "CRYPTOLOGIC",
        "prompt": ("CANYOU", "DIGIT"),
    }

    widths = row_band_widths()
    assert widths == EXPECTED_ROW_WIDTHS, widths
    colored_widths = tuple(w[0] for w in widths.values()) + tuple(
        w[2] for w in widths.values()
    )
    white_widths = tuple(w[1] for w in widths.values())
    assert min(colored_widths) >= 66 and max(colored_widths) <= 70, colored_widths
    assert white_widths == (28, 24, 21, 19), white_widths
    assert tuple(
        white_widths[index + 1] - white_widths[index]
        for index in range(len(white_widths) - 1)
    ) == (-4, -3, -2)
    assert "".join(
        chr(left + right - white) for left, white, right in widths.values()
    ) == "iptv"

    print(
        "[*] self-test OK: all four icon pairs resolve; WAR+NING identifies "
        "THE WARNING, LO inserted into CRYPTO/GIC identifies LOGIC, and the "
        "remaining pairs reproduce CAN YOU / DIG IT. The intended white-mask "
        f"matching scores {intended_score}, ranks {intended_ranks[0]}-"
        f"{intended_ranks[-1]} of 24, and has {at_least_as_large}/24 "
        "matchings at least as large (overlay area is not a distinctive "
        "number source). Row band widths measured directly on unpadded "
        "pixels are 66/28/67, 70/24/66, 70/21/67, and 70/19/67. "
        "The white sequence has real -4/-3/-2 steps, but the row order and "
        "borders came from a community member who explicitly said the "
        "sequence might be wrong; direct numeric readings yield no "
        "instruction."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    intersections = cross_intersections()
    print("\n[*] left-to-right white-mask intersection matrix:")
    print(" " * 19 + " ".join(f"{name:>15s}" for name in RIGHT_ICONS))
    for left in LEFT_ICONS:
        values = " ".join(
            f"{intersections[(left, right)]:15d}" for right in RIGHT_ICONS
        )
        print(f"    {left:15s}{values}")

    scores = matching_scores(intersections)
    intended_score = next(
        score for score, matching in scores if matching == INTENDED_MATCHING
    )
    at_least_as_large = sum(score >= intended_score for score, _ in scores)
    print(
        f"\n[*] intended matching overlap sum: {intended_score}; "
        f"{at_least_as_large}/24 perfect matchings score at least as high"
    )

    outputs = rebus_outputs()
    print("\n[*] visible rebus:")
    print(f"    song:   {outputs['song']} -> THE WARNING")
    print(f"    artist: {outputs['artist']} -> (CRYPTO)LOGIC")
    print(f"    prompt: {outputs['prompt'][0]} / {outputs['prompt'][1]} -> CAN YOU DIG IT?")

    print("\n[*] row band widths in px (blue/black, white, red), measured "
          "directly on each file's own unpadded pixels:")
    for (left, right), (colored_l, white_w, colored_r) in row_band_widths().items():
        print(f"    {left:15s} {right:15s} -> ({colored_l}, {white_w}, {colored_r})")
    print(
        "    middle widths: 28, 24, 21, 19 (differences -4, -3, -2); "
        "raw A1Z26/ASCII is invalid, while left+right-white gives 'iptv'"
    )


if __name__ == "__main__":
    main()
