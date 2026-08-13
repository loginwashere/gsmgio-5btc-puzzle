#!/usr/bin/env python3
"""User-flagged observation: the *Cosmic Duality* interior title page renders
the initial letters `C` and `D` as miniature yin-yang glyphs (gold/black split
with inverse dots), while every other title letter -- and the same title on
the front cover -- is plain single-color type.

**Phase 261 correction (2026-08-13):** a fuller review of the book's other
photographed pages found the same gold/black yin-yang drop-cap design reused
on ordinary body-paragraph capitals elsewhere in the book (confirmed here
against one such instance, the page-26 "O" opening "One ancient creed...",
pixel-verified at the same gold-detection threshold). The title page's `C`/`D`
are therefore a *miniature reuse of a book-wide typographic design system*,
not initials singled out for decoration. This materially downgrades the
original claim:

- The yin-yang letter styling itself, and its total absence from the front
  cover's plain-silver rendering of the same title, are both still true and
  still pixel-confirmed.
- `CD -> 400` (Roman `500 - 100`) is still exact, unforced arithmetic that
  matches the independently-derived (first_piece_prime_sum_reconstruction.py,
  Phase 196) yellow color-event prime sum from the `401/400/73` triple.
- What no longer holds: the typography does **not** independently *select*
  `CD` for a Roman-numeral reading. Because the same design decorates many
  ordinary body capitals (a book-wide house style, not a title-specific
  choice), its presence on `C` and `D` is exactly what a page's own initials
  would look like regardless of what those letters happened to be -- the
  match to `400` is best graded an interesting possible coincidence or
  corroboration, not an independent physical echo.
- This still supplies no G3 operation for G-PRIME-001 (`401/400/73` has no
  established consumer) or for G-MSL-001/G-YIN-001. No creator source selects
  "read the title's decorated initials as a Roman numeral." It still mildly
  reinforces `cosmic_duality_book`'s existing "explicit yin/yang content"
  qualification in yinyang_artifact_inventory_audit.py (the motif recurs
  throughout the book, not just once), but not as strongly as a title-unique
  treatment would have.
- Recovered pages 57-58 (Phase 259) add nothing here: neither page opens a
  new subsection, so neither has (or would be expected to have) a drop cap.
- No oracle sweep is run here. `400`/`CD`/`"Cosmic Duality"` are not new
  password candidates on their own -- the existing tests already cover the
  title/initials space (spi_cd_initials_audit.py), and a bare numeral has no
  stated consumer to test against.

The exact total count of book-wide yin-yang drop caps (a user report puts it
at 39, one per subsection across the four chapters, sampled but not
exhaustively re-verified here) is not independently re-derived by this
module -- only the single cross-check instance needed to confirm the design
is reused (not title-unique) is pixel-verified below.
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
# Page 26-27 spread: an ordinary body-paragraph opening ("One ancient creed
# ..."), used as the cross-check that the yin-yang gold/black drop cap is a
# book-wide design, not something applied only to the title's C/D.
DEFAULT_BODY_SAMPLE = Path(
    "/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-42-56.png"
)

EXPECTED_TITLE_PAGE_SHA256 = "4493e8bd47a56d004bba4a4dd33bf077212892e89150807e02800bda8864e86b"
EXPECTED_COVER_SHA256 = "fadab2e6b753030e9e807e70fa52a2d7503b573ac736a6f14fa1f3e1579a6c8c"
EXPECTED_BODY_SAMPLE_SHA256 = "5c22f796a470d23ec1532393d6d3a6c5644b90fcd750998329c7c31f3a74f030"

TITLE_REGION = (900, 350, 1400, 460)   # (left, top, right, bottom) around "Cosmic Duality"
COSMIC_WORD_X = (954, 1135)            # measured ink extent of "Cosmic" within TITLE_REGION coords
DUALITY_WORD_X = (1145, 1325)          # measured ink extent of "Duality"
COVER_TITLE_REGION = (1050, 90, 1400, 170)
BODY_SAMPLE_REGION = (0, 615, 75, 715)  # page-26 "O" drop cap ("One ancient creed...")

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


def analyze(title_page=DEFAULT_TITLE_PAGE, cover=DEFAULT_COVER, body_sample=DEFAULT_BODY_SAMPLE):
    title_hash = sha256_file(title_page)
    cover_hash = sha256_file(cover)
    body_sample_hash = sha256_file(body_sample)

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
    _body_gold_x, body_sample_gold_px = gold_x_positions(body_sample, BODY_SAMPLE_REGION)

    roman_cd = roman_value("CD")
    roman_dc = roman_value("DC")
    hex_cd = int("CD", 16)
    ascii_sum = ord("C") + ord("D")
    a1z26_sum = (ord("C") - ord("A") + 1) + (ord("D") - ord("A") + 1)

    return {
        "title_page_sha256": title_hash,
        "cover_sha256": cover_hash,
        "body_sample_sha256": body_sample_hash,
        "body_sample_gold_pixel_count": body_sample_gold_px,
        "design_is_book_wide_not_title_unique": body_sample_gold_px > 0,
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
    assert report["body_sample_sha256"] == EXPECTED_BODY_SAMPLE_SHA256
    assert report["body_sample_gold_pixel_count"] > 0, (
        "page-26 body drop cap should also show the gold yin-yang treatment "
        "-- if this fails, the design-is-book-wide correction needs revisiting"
    )
    assert report["design_is_book_wide_not_title_unique"] is True
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
        "title initials, absent from the front cover, but ALSO present on an "
        "ordinary body drop cap (page 26) -- book-wide design, not title-unique. "
        "CD=400 Roman still matches the yellow sum 400, graded as corroboration, "
        "not an independent echo"
    )


def print_report(report):
    for key, value in report.items():
        print(f"{key}: {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--title-page", type=Path, default=DEFAULT_TITLE_PAGE)
    parser.add_argument("--cover", type=Path, default=DEFAULT_COVER)
    parser.add_argument("--body-sample", type=Path, default=DEFAULT_BODY_SAMPLE)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print_report(analyze(args.title_page, args.cover, args.body_sample))


if __name__ == "__main__":
    main()
