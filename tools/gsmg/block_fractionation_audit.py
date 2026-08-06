#!/usr/bin/env python3
"""Short-period Bifid/Trifid-style BLOCK fractionation test for dbbi/faed.

Clarifies and replaces the "true Trifid" framing raised in conversation: a
literal 3-coordinate-per-letter Trifid cube (27 cells) doesn't map onto a
9-symbol raw alphabet without inventing a third coordinate that doesn't exist
in the data -- each raw a-i symbol only supplies TWO ternary digits via the
established dual-ternary factorization (dual_ternary_sweep.py's identity
symmetry: a=00 b=01 c=02 d=10 e=11 f=12 g=20 h=21 i=22), which is a 2D/
Bifid-style factorization, not 3D.

What dual_ternary_sweep.py's "interleave"/"component" streams never tested is
Bifid's actual distinguishing mechanic: a SHORT, FIXED PERIOD block (that
script's whole-message matrix routes matched dbbi's own 7x13/faed's 15x38
dimensions specifically -- effectively one giant "block" the size of the
whole message -- not arbitrary SHORT periods the way Bifid/Trifid are
classically used, often tied to a short keyword length, e.g. 5-15).

Mechanic (classic Bifid, applied to this 9-symbol/3x3-square alphabet instead
of the usual 25-letter/5x5 one): for a block of L raw symbols, write the L
row-trits then the L col-trits as one flat 2L-digit sequence, then re-chunk
that sequence into L NEW (row,col) pairs by taking two CONSECUTIVE digits at
a time, mapping each new pair back to a raw a-i symbol via the same table.
`decrypt_block` is the exact inverse (round-trip self-tested below) -- this is
what you'd apply to CIPHERTEXT to undo a fractionation layer.

Before testing candidate periods against the real dbbi/faed streams,
calibrates whether this test even has power: does fractionating a REAL
English-checkerboard-encoded ciphertext measurably change its segmented-code
IC (checkerboard_code_ic_oracle.py's Phase 106/112 escape-pair oracle)
relative to the unfractionated original? dbbi/faed's ALREADY near-English
code-IC under their established best escape pairs is itself potential
evidence against a fractionation layer -- exactly the same logic already used
in this project to disfavor a VIC-style additive keystream on dbbi
(doc/GSMG_PUZZLE.md's Kasiski/Friedman work: "chain addition would smooth IC
toward uniform; dbbi shows no such smoothing") -- this script checks that
directly for fractionation specifically, rather than assuming the analogy
holds.

Usage: python3 tools/gsmg/block_fractionation_audit.py
"""
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import NINE_SYMS  # noqa: E402
from checkerboard_code_ic_oracle import (  # noqa: E402
    segment_codes, code_ic, ENGLISH_PROSE_IC, length_matched_trial,
)
from data import DBBI, FAED  # noqa: E402
import checkerboard_recovery_calibration as crc  # noqa: E402

TRIT_MAP = {sym: (i // 3, i % 3) for i, sym in enumerate(NINE_SYMS)}
INV_TRIT_MAP = {v: k for k, v in TRIT_MAP.items()}

BEST_ESCAPES = {"dbbi": ("b", "e"), "faed": ("g", "i")}
PERIODS = list(range(2, 16))  # classic Bifid/Trifid periods are short, often keyword-length


def encrypt_block(block):
    """Classic Bifid-style forward fractionation of one block."""
    L = len(block)
    if L < 2:
        return block
    rows = [TRIT_MAP[c][0] for c in block]
    cols = [TRIT_MAP[c][1] for c in block]
    combined = rows + cols
    return "".join(
        INV_TRIT_MAP[(combined[2 * i], combined[2 * i + 1])] for i in range(L)
    )


def decrypt_block(block):
    """Exact inverse of encrypt_block -- what you'd apply to ciphertext to
    undo a fractionation layer of this period."""
    L = len(block)
    if L < 2:
        return block
    pairs = [TRIT_MAP[c] for c in block]
    combined = [v for pair in pairs for v in pair]
    rows, cols = combined[:L], combined[L:]
    return "".join(INV_TRIT_MAP[(rows[i], cols[i])] for i in range(L))


def apply_blockwise(stream, period, op):
    return "".join(op(stream[i:i + period]) for i in range(0, len(stream), period))


def fractionate(stream, period, direction):
    op = encrypt_block if direction == "encrypt" else decrypt_block
    return apply_blockwise(stream, period, op)


def self_test():
    rng = random.Random(42)
    for _ in range(200):
        length = rng.randint(0, 40)
        stream = "".join(rng.choice(NINE_SYMS) for _ in range(length))
        for period in (2, 3, 5, 7, 11, 13):
            enc = fractionate(stream, period, "encrypt")
            back = fractionate(enc, period, "decrypt")
            assert back == stream, (
                f"self-test FAILED: decrypt_block(encrypt_block(x)) != x "
                f"(period={period}, stream={stream!r})"
            )
    print("[*] self-test passed: decrypt_block/encrypt_block round-trip exactly "
          "across 200 random streams x 6 periods")


def code_ic_under_best(stream, target_name):
    e1, e2 = BEST_ESCAPES[target_name]
    codes = segment_codes(stream, e1, e2)
    if codes is None:
        return None
    return code_ic(codes)


def build_calibration_ciphertext(target_name, seed=7):
    """A real English-checkerboard-encoded ciphertext close to the target's
    raw length, under its established best escape pair -- ground truth for
    calibrating whether fractionation is detectable at all with this test.
    Uses checkerboard_code_ic_oracle.py's own length_matched_trial() (dbbi's
    exact-profile match is impractical to reuse here too since faed's exact
    25/25-type profile essentially never occurs in real English samples --
    already established in that module's own docstring; code-level IC only
    depends on the resulting code-frequency distribution, not on which
    letters specifically sit in which board slot, so this doesn't change what
    is being measured, only how cheaply a matching synthetic is built)."""
    rng = random.Random(seed)
    crc.apply_profile(target_name)
    corpus_letters = {
        name: crc.load_letters(path, stride)
        for name, (path, stride) in crc.CORPUS_SOURCES.items()
    }
    ciphertext, _ = length_matched_trial(target_name, corpus_letters, rng)
    return ciphertext


def calibrate_power(target_name):
    """Does fractionating (then correctly un-fractionating with the WRONG
    period, or leaving it fractionated) a real checkerboard ciphertext
    measurably degrade its code-IC relative to the clean original? This
    establishes what a genuine fractionation signature would look like before
    hunting for one in the real dbbi/faed streams."""
    clean = build_calibration_ciphertext(target_name)
    clean_ic = code_ic_under_best(clean, target_name)
    print(f"  calibration ciphertext (real English, len={len(clean)}): "
          f"unfractionated code-IC={clean_ic:.5f}")
    for period in (3, 5, 7, 10, 13):
        fractionated = fractionate(clean, period, "encrypt")
        frac_ic = code_ic_under_best(fractionated, target_name)
        frac_ic_str = f"{frac_ic:.5f}" if frac_ic is not None else "N/A (dangling escape)"
        print(f"    period={period:2d}: after fractionation, code-IC={frac_ic_str}")


def null_calibration_periods(target_name, trials=500, seed=20260806):
    """Shuffles the real stream's own symbol multiset and re-runs the same
    'best-of-len(PERIODS) periods' un-fractionation search on each shuffle --
    the multiple-testing baseline for 'is any one period exceptionally good'."""
    rng = random.Random(seed)
    stream = DBBI if target_name == "dbbi" else FAED
    symbols = list(stream)
    null_bests = []
    for _ in range(trials):
        rng.shuffle(symbols)
        shuffled = "".join(symbols)
        best = None
        for period in PERIODS:
            undone = fractionate(shuffled, period, "decrypt")
            ic = code_ic_under_best(undone, target_name)
            if ic is not None:
                dist = abs(ic - ENGLISH_PROSE_IC)
                if best is None or dist < best:
                    best = dist
        if best is not None:
            null_bests.append(best)
    null_bests.sort()
    return null_bests


def main():
    self_test()

    print("\n=== Power calibration: does fractionation degrade code-IC on a "
          "REAL checkerboard ciphertext? ===")
    for target_name in ("dbbi", "faed"):
        print(f"-- {target_name} --")
        calibrate_power(target_name)

    print("\n=== Real dbbi/faed: un-fractionating across candidate short "
          "periods, code-IC under the established best escape pair ===")
    for target_name, stream in [("dbbi", DBBI), ("faed", FAED)]:
        raw_ic = code_ic_under_best(stream, target_name)
        print(f"\n-- {target_name} (raw len={len(stream)}) -- "
              f"UNFRACTIONATED baseline code-IC={raw_ic:.5f} "
              f"(dist-from-English={abs(raw_ic - ENGLISH_PROSE_IC):.5f}) --")
        results = []
        for period in PERIODS:
            undone = fractionate(stream, period, "decrypt")
            ic = code_ic_under_best(undone, target_name)
            if ic is None:
                print(f"   period={period:2d}: dangling escape after "
                      f"un-fractionation, invalid")
                continue
            dist = abs(ic - ENGLISH_PROSE_IC)
            results.append((period, ic, dist))
            print(f"   period={period:2d}: code-IC={ic:.5f}  dist-from-English={dist:.5f}")
        best_period, best_ic, best_dist = min(results, key=lambda r: r[2])
        print(f"   best period={best_period} (dist={best_dist:.5f}) vs. "
              f"unfractionated baseline (dist={abs(raw_ic - ENGLISH_PROSE_IC):.5f})")

        null = null_calibration_periods(target_name, trials=500)
        p = sum(1 for d in null if d <= best_dist) / len(null)
        print(f"   null calibration (500 shuffles, best-of-{len(PERIODS)}-periods "
              f"each): null median dist={null[len(null)//2]:.5f}, "
              f"real best dist={best_dist:.5f}  ==>  p={p:.4f} "
              f"({'REAL beats the null -- worth a closer look' if p < 0.05 else 'NOT exceptional vs. multiple-testing noise'})")


if __name__ == "__main__":
    main()
