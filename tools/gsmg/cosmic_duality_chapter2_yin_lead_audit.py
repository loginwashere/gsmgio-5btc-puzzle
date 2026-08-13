#!/usr/bin/env python3
"""User-flagged observation: applying `(page_number - A1Z26(drop_cap_letter))
mod 26` to Chapter 2's first three yin-yang-decorated drop caps ("The Battle
of the Sexes," the book's chapter about gender duality) spells `YIN`.

Independently re-verified against the actual photographed pages (not taken
on report): Chapter 2 opens on page 48 with a gold/black yin-yang "W" drop
cap ("hen the gods created the human race..."); page 50 has an "O" drop cap
("ther researchers, however..."); page 55 has an "O" drop cap ("ther myths
recorded..."). All three pixel-confirmed as the same gold-upper/black-lower
yin-yang design used throughout the book (Phase 260/261). The arithmetic:

    W, p.48: 48 - A1Z26(W)=23 = 25          -> Y
    O, p.50: 50 - A1Z26(O)=15 = 35 mod 26=9 -> I
    O, p.55: 55 - A1Z26(O)=15 = 40 mod 26=14 -> N

This module pins the photo hashes, the pixel-confirmed presence of gold ink
at each drop cap's location, and the arithmetic that produces `YIN` -- so
the positive part of the claim is a reproducible regression, not a one-off
visual read.

**"No YANG counterpart" independently re-confirmed**, using
`cosmic_duality_dropcap_inventory.py`'s full 39-entry page/letter inventory
(self-consistent, and its own three Chapter-2 entries match this module's
photo-verified page 48/50/55 W/O/O exactly): applying the same formula to
all 39 book-wide drop caps and concatenating by chapter reproduces the
reported `VYVWXKALOH` / `YINJMNNJMV` / `IJSCNJVPL` / `THYRRWWQWV` output
exactly, and neither `YANG` nor its reverse appears anywhere in the
39-letter concatenation. This is a logical/arithmetic re-derivation from the
inventory's claimed letters, not a fresh photo-by-photo re-verification of
all 39 drop caps -- only the three Chapter-2 entries used above were
independently checked against the raw photographs.

**What this still does NOT establish:**

- Nothing selects "the first three decorated initials of Chapter 2" as the
  input scope over any other window or chapter.
- Alternate operations (page+letter, reversed subtraction, page mod 26,
  digit sums, gaps, parity, prime/composite separation) were reported
  negative but not independently re-tested here.
- Phase 260/261 already established the drop-cap design is a book-wide house
  style, not title-unique; this reuses A1Z26 on body letters where the
  earlier CD=400 finding used Roman numeral values -- a different, weaker-
  precedent operation switch the report itself flags.

**Verdict carried over unchanged from the report, not softened or
strengthened here:** `YIN` is a legitimate, pixel-and-arithmetic-verified
bounded lead worth recording -- genuinely interesting given the book's own
yin/yang subject matter and G-YIN-001's open "creator's yinyang state"
question -- but not sufficient to claim an intended encoding. No oracle
sweep is run: `YIN` alone has no stated consumer, and this is not promoted
to G-YIN-001's operator question without either a `YANG` counterpart or a
clue selecting this exact window.
"""

import argparse
import hashlib
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_P48 = Path(
    "/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-44-14.png"
)
DEFAULT_P50 = Path(
    "/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-44-19.png"
)
DEFAULT_P55 = Path(
    "/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-44-33.png"
)

# (label, letter, page_number, image_path, gold-check crop box (l,t,r,b))
DROP_CAPS = (
    ("p48_W", "W", 48, DEFAULT_P48, (175, 370, 300, 490)),
    ("p50_O", "O", 50, DEFAULT_P50, (420, 255, 480, 355)),
    ("p55_O", "O", 55, DEFAULT_P55, (790, 830, 870, 930)),
)

EXPECTED_IMAGE_SHA256 = {
    DEFAULT_P48: "821efce3382c910573f355be2dc84c3f6de41da2add65a85cc6ae4fbc535b998",
    DEFAULT_P50: "11401601e1f58e614defacd8cf2d6650a80fa9ec0b11add3ff14db0ce458c8a5",
    DEFAULT_P55: "8471b9587afe78bea37dedab214b44ca5b07b92b136fd5bb9d1e116deaa789bd",
}

EXPECTED_GOLD_PIXELS = {"p48_W": 7344, "p50_O": 1158, "p55_O": 874}
EXPECTED_SEQUENCE = "YIN"


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gold_pixel_count(image_path, box):
    import numpy as np

    region = np.array(Image.open(image_path).convert("RGB").crop(box))
    r, g, b = region[:, :, 0].astype(int), region[:, :, 1].astype(int), region[:, :, 2].astype(int)
    mask = (r > 40) & (r < 180) & (r > g + 10) & (g > b + 5) & (b < 60)
    return int(mask.sum())


def a1z26(letter):
    return ord(letter.upper()) - ord("A") + 1


def transform(page, letter):
    value = (page - a1z26(letter)) % 26
    if value == 0:
        value = 26
    return chr(value - 1 + ord("A"))


def analyze():
    rows = []
    for label, letter, page, path, box in DROP_CAPS:
        rows.append({
            "label": label,
            "letter": letter,
            "page": page,
            "image_sha256": sha256_file(path),
            "gold_pixel_count": gold_pixel_count(path, box),
            "transformed": transform(page, letter),
        })
    sequence = "".join(row["transformed"] for row in rows)
    return {"rows": rows, "sequence": sequence}


def self_test():
    report = analyze()
    for row in report["rows"]:
        _label, letter, page, path, _box = next(d for d in DROP_CAPS if d[0] == row["label"])
        assert row["image_sha256"] == EXPECTED_IMAGE_SHA256[path], row["label"]
        assert row["gold_pixel_count"] == EXPECTED_GOLD_PIXELS[row["label"]], row["label"]
        assert row["gold_pixel_count"] > 0
    assert report["sequence"] == EXPECTED_SEQUENCE
    print(
        f"[*] self-test OK: Chapter 2's first three pixel-confirmed drop caps "
        f"(W/48, O/50, O/55) transform to {report['sequence']!r} -- bounded "
        f"lead, not a solved mechanism (no YANG counterpart established)"
    )


def print_report(report):
    for row in report["rows"]:
        print(
            f"{row['label']}: letter={row['letter']} page={row['page']} "
            f"gold_px={row['gold_pixel_count']} -> {row['transformed']}"
        )
    print(f"sequence: {report['sequence']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print_report(analyze())


if __name__ == "__main__":
    main()
