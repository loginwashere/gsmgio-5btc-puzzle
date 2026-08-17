#!/usr/bin/env python3
"""Candidate family -- QR Code Monkey custom eye-style sweep (2026-08-16).

Follow-up to Phase 298 (`qr_finder_ring_texture_generator_comparison_audit.py`),
which found that QR Code Monkey's *default* style confines antialiasing to
the three finder-pattern eyes (matching the puzzle's own framing-question
fact (a)) but with a texture -- a simple 1px-wide vector edge outline --
structurally unlike the puzzle's 7-row-deep period-4 banded texture. That
result left one explicitly-noted open question: whether a *custom* eye
style (the generator exposes distinct "frame"/"eyeBall" shape catalogs)
comes closer.

The live API (`api.qrcode-monkey.com/qr/custom`) was queried on 2026-08-16
with the puzzle's exact payload for the **full, pre-registered catalog** of
eye styles, extracted directly from the generator's own client-side asset
bundle (`www.qrcode-monkey.com/dist/website.dist.js`, grep for
`"frame[0-9]+"`/`"ball[0-9]+"` literals) rather than guessed or
cherry-picked after seeing results:

  - Sweep A: all 16 valid `eye` (frame) values (`frame0`..`frame14`,
    `frame16` -- `frame15` does not exist in the asset bundle), `eyeBall`
    held at the default `ball0`.
  - Sweep B: all 20 valid `eyeBall` values (`ball0`..`ball19`), `eye` held
    at the default `frame0`.

This is a one-factor-at-a-time sweep of the full declared catalog (36
renders), not the full 16x20=320 cross product, and not a subjective
"looks close" subset -- both dimensions are exhaustively covered
independently. Each render's top-left finder-square region was visually
inspected (row/column pixel-grid dump, the same method used throughout this
investigation) for the puzzle's specific signature: multi-row *periodic*
banding with repeated near-white/light-gray value pairs, as opposed to a
thin vector-edge antialiasing outline.

Three renders are saved locally as representative exemplars for
reproducibility without live network access:
`doc/img/qr_generator_comparison_qrcode_monkey_frame3_ball0.png` (a plain
square frame, smallest gray-pixel count in the sweep),
`doc/img/qr_generator_comparison_qrcode_monkey_frame8_ball0.png` (largest
gray-pixel count / most complex curved shape in the sweep), and
`doc/img/qr_generator_comparison_qrcode_monkey_frame16_ball0.png` (a
"dotted border" style -- the frame is drawn as separate disconnected dot
segments rather than one solid outline; still only thin per-segment edge
AA, not a zero-antialiasing case). The full 36-image sweep was not
committed to the repo to avoid bloat; its qualitative finding (every config
produces 1-2px vector-edge antialiasing, never the puzzle's periodic
multi-row banding) is recorded in `tools/gsmg/FINDINGS.md` Phase 299 and
reproducible by re-running the two curl sweeps described in that entry.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
IMG_DIR = REPO_ROOT / "doc" / "img"

EXEMPLARS = {
    "frame3_ball0": IMG_DIR / "qr_generator_comparison_qrcode_monkey_frame3_ball0.png",
    "frame8_ball0": IMG_DIR / "qr_generator_comparison_qrcode_monkey_frame8_ball0.png",
    "frame16_ball0": IMG_DIR / "qr_generator_comparison_qrcode_monkey_frame16_ball0.png",
}

# Full declared eye-style catalog, extracted from the generator's own client asset
# bundle (see docstring) -- pinned here so the sweep is reproducible/re-runnable.
FRAME_VALUES = [f"frame{i}" for i in range(15) if i != 15] + ["frame16"]
BALL_VALUES = [f"ball{i}" for i in range(20)]


def gray_pixel_count(path):
    """Gray (non-black/white) pixel count within the top-left ~90x90px corner,
    which contains the top-left finder-square eye at this render size -- matches
    the region inspected by the pixel-grid dumps this finding is based on.
    Deliberately excludes the data body, where some frames (e.g. frame16) use a
    dot/rounded module style with its own unrelated antialiasing."""
    im = Image.open(path).convert("RGB")
    arr = np.array(im)
    region = arr[0:90, 0:90]
    gray = region.mean(axis=2)
    return int(((gray != 0) & (gray != 255)).sum())


def self_test():
    assert len(FRAME_VALUES) == 16, f"expected 16 frame values, got {len(FRAME_VALUES)}"
    assert len(BALL_VALUES) == 20, f"expected 20 ball values, got {len(BALL_VALUES)}"
    assert "frame15" not in FRAME_VALUES
    for name, path in EXEMPLARS.items():
        assert path.exists(), f"missing saved exemplar for {name}: {path}"
    counts = {name: gray_pixel_count(path) for name, path in EXEMPLARS.items()}
    assert all(v > 0 for v in counts.values()), f"all exemplars must have some eye-region AA, got {counts}"
    print(f"[*] self-test OK: 16 frame values + 20 ball values pinned (36-combination sweep), "
          f"3 exemplars present, gray counts {counts}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    parser.print_help()


if __name__ == "__main__":
    main()
