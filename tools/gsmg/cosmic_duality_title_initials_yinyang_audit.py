#!/usr/bin/env python3
"""User-flagged observation: the *Cosmic Duality* interior title page renders
the initial letters `C` and `D` as miniature yin-yang glyphs (gold/black split
with inverse dots), while every other title letter -- and the same title on
the front cover -- is plain single-color type.

`CD` read as a Roman numeral is `500 - 100 = 400`, exactly matching the
independently-derived (first_piece_prime_sum_reconstruction.py, Phase 196)
yellow color-event prime sum `400` from the `401/400/73` blue/yellow/FEFE
triple. This module makes that observation pixel-verifiable and numerically
precise, and states plainly what it does and does not establish:

- The yin-yang letter styling is confirmed by direct pixel inspection, not
  eyeballing: gold ink is present in two narrow, isolated x-ranges and
  nowhere else in the title, and is entirely absent from the same title's
  rendering on the front cover (same font, uniform silver foil) -- so this
  is a deliberate interior-title-page choice, not a font artifact.
- `CD -> 400` is exact, standard Roman numeral arithmetic, not a fitted or
  chosen reading -- unlike the alternate encodings tested as controls
  (`DC`, hex, ASCII sum, A1Z26 sum), none of which land on an
  independently-established puzzle value.
- This does NOT supply a G3 operation for G-PRIME-001 (`401/400/73` has no
  established consumer) or for G-MSL-001/G-YIN-001. No creator source
  selects "read the title's decorated initials as a Roman numeral" as an
  instruction. It upgrades `400` from an internally-fitted value to one
  independently echoed by an authenticated physical artifact, and it
  reinforces (does not newly establish) `cosmic_duality_book`'s existing
  "explicit yin/yang content" qualification in
  yinyang_artifact_inventory_audit.py.
- No oracle sweep is run here. `400`/`CD`/`"Cosmic Duality"` are not new
  password candidates on their own -- the existing tests already cover the
  title/initials space (spi_cd_initials_audit.py), and a bare numeral has no
  stated consumer to test against.
"""

import argparse
import hashlib
from pathlib import Path

from PIL import Image

from first_piece_prime_sum_reconstruction import EXPECTED_FITTED_SUMS

# These are the user's own local screen-capture photos of the physical book
# (the same 2026-07-12 session that produced cosmic_duality_book_full_text.txt),
# not committed to git -- same convention as this project's Telegram export
# directories: a stable absolute path, existence-checked, not a repo asset.
DEFAULT_TITLE_PAGE = Path(
    "/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-41-28.png"
)
DEFAULT_COVER = Path(
    "/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-41-07.png"
)

EXPECTED_TITLE_PAGE_SHA256 = "4493e8bd47a56d004bba4a4dd33bf077212892e89150807e02800bda8864e86b"
EXPECTED_COVER_SHA256 = "fadab2e6b753030e9e807e70fa52a2d7503b573ac736a6f14fa1f3e1579a6c8c"

TITLE_REGION = (900, 350, 1400, 460)   # (left, top, right, bottom) around "Cosmic Duality"
COSMIC_WORD_X = (954, 1135)            # measured ink extent of "Cosmic" within TITLE_REGION coords
DUALITY_WORD_X = (1145, 1325)          # measured ink extent of "Duality"
COVER_TITLE_REGION = (1050, 90, 1400, 170)

ROMAN_VALUES = {"C": 100, "D": 500}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gold_mask(region_rgb):
    r = region_rgb[:, :, 0].astype(int)
    g = region_rgb[:, :, 1].astype(int)
    b = region_rgb[:, :, 2].astype(int)
    return (r > 40) & (r < 180) & (r > g + 10) & (g > b + 5) & (b < 60)


def gold_x_positions(image_path, box):
    import numpy as np

    img = Image.open(image_path).convert("RGB")
    left, top, right, bottom = box
    region = np.array(img.crop((left, top, right, bottom)))
    mask = gold_mask(region)
    ys, xs = np.where(mask)
    return sorted(set((x + left) for x in xs)), int(mask.sum())


def roman_value(letters):
    """Simple two-symbol reading: additive unless the smaller symbol leads
    (subtractive), matching standard Roman numeral rules for exactly these
    two symbols. Sufficient and correct for C/D; not a general parser."""
    values = [ROMAN_VALUES[ch] for ch in letters]
    if len(values) == 2 and values[0] < values[1]:
        return values[1] - values[0]
    return sum(values)


def analyze(title_page=DEFAULT_TITLE_PAGE, cover=DEFAULT_COVER):
    title_hash = sha256_file(title_page)
    cover_hash = sha256_file(cover)

    all_gold_x, total_gold_px = gold_x_positions(title_page, TITLE_REGION)
    cosmic_gold = [x for x in all_gold_x if COSMIC_WORD_X[0] <= x <= COSMIC_WORD_X[1]]
    duality_gold = [x for x in all_gold_x if DUALITY_WORD_X[0] <= x <= DUALITY_WORD_X[1]]
    outside_gold = [
        x for x in all_gold_x
        if not (COSMIC_WORD_X[0] <= x <= COSMIC_WORD_X[1])
        and not (DUALITY_WORD_X[0] <= x <= DUALITY_WORD_X[1])
    ]
    # gold within each word must cluster at the word's leading edge (the
    # initial capital), not be scattered across the whole word.
    cosmic_gold_span = (min(cosmic_gold), max(cosmic_gold)) if cosmic_gold else None
    duality_gold_span = (min(duality_gold), max(duality_gold)) if duality_gold else None

    cover_gold_x, cover_gold_px = gold_x_positions(cover, COVER_TITLE_REGION)

    roman_cd = roman_value("CD")
    roman_dc = roman_value("DC")
    hex_cd = int("CD", 16)
    ascii_sum = ord("C") + ord("D")
    a1z26_sum = (ord("C") - ord("A") + 1) + (ord("D") - ord("A") + 1)

    return {
        "title_page_sha256": title_hash,
        "cover_sha256": cover_hash,
        "total_gold_pixels": total_gold_px,
        "cosmic_word_gold_pixel_count": len(cosmic_gold),
        "cosmic_word_gold_span": cosmic_gold_span,
        "duality_word_gold_pixel_count": len(duality_gold),
        "duality_word_gold_span": duality_gold_span,
        "gold_outside_either_initial_count": len(outside_gold),
        "cover_title_gold_pixel_count": cover_gold_px,
        "roman_cd": roman_cd,
        "roman_dc": roman_dc,
        "hex_cd": hex_cd,
        "ascii_sum_cd": ascii_sum,
        "a1z26_sum_cd": a1z26_sum,
        "fitted_sums": dict(EXPECTED_FITTED_SUMS),
        "cd_matches_yellow_sum": roman_cd == EXPECTED_FITTED_SUMS["Y"],
    }


def self_test():
    report = analyze()
    assert report["title_page_sha256"] == EXPECTED_TITLE_PAGE_SHA256
    assert report["cover_sha256"] == EXPECTED_COVER_SHA256
    assert report["cosmic_word_gold_pixel_count"] > 0
    assert report["duality_word_gold_pixel_count"] > 0
    assert report["gold_outside_either_initial_count"] == 0
    # gold confined to a narrow leading span within each word (the initial
    # capital's glyph box), not spread across the whole word's width
    c_span = report["cosmic_word_gold_span"]
    d_span = report["duality_word_gold_span"]
    assert c_span[1] - c_span[0] < 40, c_span
    assert d_span[1] - d_span[0] < 45, d_span
    assert c_span[0] - COSMIC_WORD_X[0] < 5, "gold C span should start at word's leading edge"
    assert d_span[0] - DUALITY_WORD_X[0] < 15, "gold D span should start near word's leading edge"
    assert report["cover_title_gold_pixel_count"] == 0
    assert report["roman_cd"] == 400
    assert report["roman_dc"] == 600
    assert report["hex_cd"] == 205
    assert report["ascii_sum_cd"] == 135
    assert report["a1z26_sum_cd"] == 7
    assert report["fitted_sums"] == {"B": 401, "Y": 400, "F": 73}
    assert report["cd_matches_yellow_sum"] is True
    print(
        "[*] self-test OK: yin-yang C/D confirmed pixel-isolated to the two "
        "initials, absent from the front cover; CD=400 Roman matches the "
        "independently-derived yellow sum 400"
    )


def print_report(report):
    for key, value in report.items():
        print(f"{key}: {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--title-page", type=Path, default=DEFAULT_TITLE_PAGE)
    parser.add_argument("--cover", type=Path, default=DEFAULT_COVER)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print_report(analyze(args.title_page, args.cover))


if __name__ == "__main__":
    main()
