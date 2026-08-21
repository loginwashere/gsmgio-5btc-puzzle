#!/usr/bin/env python3
"""Bounded Braille interpretation of the QR `#FAFAFA` mask and Phase-354 residual.

Exhausts 6-dot (2x3) and 8-dot (2x4) Braille at every grid phase, both
polarities, and identity/horizontal-flip/vertical-flip/180-degree orientation.
No alignment is selected by viewing output. Grade-1 letters only are scored;
Grade-2 contractions are excluded. The same max-over-112-readings freedom is
given to deterministic shuffled controls.
"""

import argparse
import json

import numpy as np

from qr_fafafa_tile_predictability_audit import (
    BANDS, NULL_SEED, full_fit, load_mask, shuffled_mask,
)

LETTER_BITS = {
    "a": 0x01, "b": 0x03, "c": 0x09, "d": 0x19, "e": 0x11,
    "f": 0x0B, "g": 0x1B, "h": 0x13, "i": 0x0A, "j": 0x1A,
    "k": 0x05, "l": 0x07, "m": 0x0D, "n": 0x1D, "o": 0x15,
    "p": 0x0F, "q": 0x1F, "r": 0x17, "s": 0x0E, "t": 0x1E,
    "u": 0x25, "v": 0x27, "w": 0x3A, "x": 0x2D, "y": 0x3D,
    "z": 0x35,
}
BITS_LETTER = {v: k for k, v in LETTER_BITS.items()}
COMMON_BIGRAMS = frozenset(
    "th he in er an re on at en nd ti es or te of ed is it al ar st to nt ng "
    "se ha as ou io le ve co me de hi ri ro ic ne ea ra ce li ch ll be ma si om ur".split()
)
ORIENTATIONS = ("identity", "hflip", "vflip", "rot180")
NULL_TRIALS = 200
EXPECTED_FULL_BEST = (6, "identity", "fafafa_blank", 1, 1, 0.18)
EXPECTED_RESIDUAL_BEST = (6, "hflip", "fafafa_blank", 1, 0, 0.0324705882352941)


def orient(mask, name):
    if name == "identity": return mask
    if name == "hflip": return mask[:, ::-1]
    if name == "vflip": return mask[::-1, :]
    if name == "rot180": return mask[::-1, ::-1]
    raise ValueError(name)


def cells(mask, cell_h, x_phase, y_phase):
    h, w = mask.shape
    rows = []
    for y0 in range(-y_phase, h, cell_h):
        row = []
        for x0 in range(-x_phase, w, 2):
            bits = 0
            positions = [(0, 0, 0), (1, 0, 1), (2, 0, 2),
                         (0, 1, 3), (1, 1, 4), (2, 1, 5)]
            if cell_h == 4:
                positions += [(3, 0, 6), (3, 1, 7)]
            for dy, dx, bit in positions:
                y, x = y0 + dy, x0 + dx
                if 0 <= y < h and 0 <= x < w and mask[y, x]:
                    bits |= 1 << bit
            row.append(bits)
        rows.append(row)
    return rows


def transliterate(rows):
    text_rows = []
    unicode_rows = []
    for row in rows:
        text_rows.append("".join(" " if b == 0 else BITS_LETTER.get(b, "?") for b in row))
        unicode_rows.append("".join(chr(0x2800 + b) for b in row))
    return text_rows, unicode_rows


def score_text(text_rows):
    flat = "".join(text_rows)
    letters = sum(c.isalpha() for c in flat)
    unknown = flat.count("?")
    pairs = []
    longest = 0
    for row in text_rows:
        run = ""
        for c in row:
            if c.isalpha():
                run += c
            else:
                if run:
                    pairs.extend(run[i:i+2] for i in range(len(run)-1))
                    longest = max(longest, len(run))
                run = ""
        if run:
            pairs.extend(run[i:i+2] for i in range(len(run)-1))
            longest = max(longest, len(run))
    common = sum(p in COMMON_BIGRAMS for p in pairs)
    n = max(1, len(flat))
    letter_fraction = letters / n
    bigram_rate = common / max(1, len(pairs))
    # Frozen composite; controls receive the identical maximize-over-readings freedom.
    score = letter_fraction + 0.5 * bigram_rate + 0.1 * (longest / n) - 0.1 * (unknown / n)
    return {"score": score, "cells": len(flat), "letters": letters,
            "unknown": unknown, "letter_fraction": letter_fraction,
            "common_bigrams": common, "bigram_rate": bigram_rate,
            "longest_letter_run": longest}


def readings(mask):
    out = []
    for cell_h in (3, 4):
        for orientation in ORIENTATIONS:
            base = orient(mask, orientation)
            for polarity in ("fafafa_dot", "fafafa_blank"):
                work = base if polarity == "fafafa_dot" else ~base
                for y_phase in range(cell_h):
                    for x_phase in range(2):
                        grid = cells(work, cell_h, x_phase, y_phase)
                        text_rows, unicode_rows = transliterate(grid)
                        report = {"dots": 6 if cell_h == 3 else 8,
                                  "orientation": orientation, "polarity": polarity,
                                  "x_phase": x_phase, "y_phase": y_phase,
                                  "text_rows": text_rows, "unicode_rows": unicode_rows}
                        report.update(score_text(text_rows))
                        out.append(report)
    assert len(out) == 112
    return out


def best_reading(mask):
    return max(readings(mask), key=lambda r: (r["score"], r["letter_fraction"],
                                               r["bigram_rate"], r["longest_letter_run"]))


def residual_mask(mask):
    out = np.zeros_like(mask)
    for y, x in full_fit(mask)["residual_coords"]:
        out[y, x] = True
    return out


def random_residual(mask, rng, count=23):
    coords = []
    for name, (y0, y1, x0, x1) in BANDS.items():
        coords.extend((y, x) for y in range(y0, y1) for x in range(x0, x1))
    chosen = rng.choice(len(coords), count, replace=False)
    out = np.zeros_like(mask)
    for i in chosen:
        out[coords[int(i)]] = True
    return out


def calibrate(mask, trials=NULL_TRIALS):
    rng = np.random.default_rng(NULL_SEED)
    real_full = best_reading(mask)
    real_residual = best_reading(residual_mask(mask))
    null = {"full_row_sums": [], "full_column_sums": [], "residual_density": []}
    for _ in range(trials):
        null["full_row_sums"].append(best_reading(shuffled_mask(mask, rng, "row_sums"))["score"])
        null["full_column_sums"].append(best_reading(shuffled_mask(mask, rng, "column_sums"))["score"])
        null["residual_density"].append(best_reading(random_residual(mask, rng))["score"])
    def summary(real, vals):
        a = np.asarray(vals)
        return {"real": real, "null_mean": float(a.mean()), "null_min": float(a.min()),
                "null_max": float(a.max()),
                "p_ge_real": float((1 + np.sum(a >= real)) / (len(a) + 1))}
    return {"full_best": real_full, "residual_best": real_residual,
            "null_trials": trials,
            "null_summary": {
                "full_row_sums": summary(real_full["score"], null["full_row_sums"]),
                "full_column_sums": summary(real_full["score"], null["full_column_sums"]),
                "residual_density": summary(real_residual["score"], null["residual_density"]),
            }}


def self_test():
    mask = load_mask()
    assert int(mask.sum()) == 345
    residual = residual_mask(mask)
    assert int(residual.sum()) == 23
    rs = readings(mask)
    assert len(rs) == 112
    assert {r["dots"] for r in rs} == {6, 8}
    # Standard dot order must reproduce the Grade-1 alphabet table.
    for letter, bits in LETTER_BITS.items():
        text, uni = transliterate([[bits]])
        assert text == [letter]
        assert ord(uni[0]) == 0x2800 + bits
    planted = np.zeros((3, 2), dtype=bool)
    planted[0, 0] = True  # dot 1 = a
    assert transliterate(cells(planted, 3, 0, 0))[0] == ["a"]
    for actual, expected in (
        (best_reading(mask), EXPECTED_FULL_BEST),
        (best_reading(residual), EXPECTED_RESIDUAL_BEST),
    ):
        got = (actual["dots"], actual["orientation"], actual["polarity"],
               actual["x_phase"], actual["y_phase"], actual["score"])
        assert got == expected, got
    print("[*] self-test OK: full mask=345 pixels, frozen Phase-354 residual=23 pixels, "
          "112 exhaustive Braille readings generated, standard dot order and planted 'a' verified, "
          "and both real best-reading identities/scores pinned.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--trials", type=int, default=NULL_TRIALS)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    self_test()
    if args.self_test: return
    report = calibrate(load_mask(), args.trials)
    if args.json: print(json.dumps(report, indent=2)); return
    for key in ("full_best", "residual_best"):
        r = report[key]
        print(f"[*] {key}: score={r['score']:.6f} dots={r['dots']} {r['orientation']} "
              f"{r['polarity']} phase=({r['x_phase']},{r['y_phase']})")
        print(" / ".join(r["text_rows"]))
    print("[*] null:", report["null_summary"])


if __name__ == "__main__": main()
