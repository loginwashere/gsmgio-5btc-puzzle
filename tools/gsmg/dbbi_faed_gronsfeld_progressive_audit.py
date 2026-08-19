#!/usr/bin/env python3
"""Three bounded, disclosed exploratory extensions of the Phase 310/311
Nihilist-family probe, testing insertion points and key sources that
Phase 310 (post-segmentation shift, CORE_ALPHABET_SEEDS keywords) and
Phase 311 (post-segmentation shift, Cosmic Duality book running key) did
not cover.

Same bounded exploratory budget as those two phases (800 iters/30 restarts),
same quadgram-fitness hillclimb (`dbbi_faed_nihilist_additive_audit.score`/
`hillclimb_slots`), same verdict standard: a real decode would score
dramatically better than the established unshifted baseline, not just a
handful of points on the ~300-point scale (Phase 310's best shift beat
baseline by only ~7 points -- noise; Phase 311's by only ~8 points -- also
noise).

Three distinct sub-experiments, all reusing existing project machinery
directly (no reimplementation):

(a) Gronsfeld PRE-segmentation shift. Phase 310 shifted the POST-
    segmentation 0-24 code-SLOT sequence (i.e. shifts checkerboard code
    values after the escape-pair structure is already fixed). This shifts
    the RAW a-i SYMBOL stream itself (mod 9, keyword-derived key from the
    same CORE_ALPHABET_SEEDS set) *before* escape-pair segmentation --
    genuinely different insertion point: shifting the raw symbols also
    moves which positions coincide with the escape letters, so the
    resulting segmentation of the shifted stream is not the same partition
    Phase 310 worked with.

(b) Progressive (non-repeating, incrementing) shift on the same raw digit
    stream, no keyword: shift(i) = (start + i*step) mod 9 for step in 1..8,
    start in 0..8 -- exactly 72 combinations, brute-forced in full (small
    enough that "brute forcing might be required" literally applies).

(c) Five extra keyword candidates fed into the ALREADY-EXISTING Phase 310
    mechanism (post-segmentation shift -- reuses apply_shift/hillclimb_slots
    unmodified, just a longer keyword list):
      - "zebras" / "russian" -- the keyword/key pair used in the Nihilist
        cipher's Wikipedia worked example. Disclosed honestly: verified via
        WebFetch that this specific example is NOT attributed on that page
        to David Kahn's "The Codebreakers" (the two citations to Kahn's book
        on that page are for the Cryptanalysis/Later-variants sections, not
        this worked example) -- so this is "the generic textbook-standard
        Nihilist example," not confirmed to be Kahn's own passage. No
        source for Kahn's specific worked example (if he has one distinct
        from this) was found; this pair is included only because it's the
        single most commonly-cited Nihilist example in the literature, not
        because of a confirmed Kahn attribution.
      - "10june" / "june10" -- the confirmed 2017 date MR ROIbot's first
        order hit Poloniex (msg 67741, already-verified creator origin
        story), on the theory that real Nihilist/VIC tradecraft often keys
        elements from a memorized date.
      - "2019" -- the confirmed puzzle build year (same msg).

Reproduce with:
    python3 tools/gsmg/dbbi_faed_gronsfeld_progressive_audit.py --self-test
    python3 tools/gsmg/dbbi_faed_gronsfeld_progressive_audit.py
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import NINE_SYMS  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from dbbi_faed_nihilist_additive_audit import (  # noqa: E402
    TARGETS,
    TOPOLOGIES,
    apply_shift,
    hillclimb_slots,
    keyword_to_key25,
    slot_sequence,
)
from matrixsum_permutation_sweep import (  # noqa: E402
    CORE_ALPHABET_SEEDS,
    natural_code_index,
    segment_codes,
)

EXTRA_KEYWORDS = ("zebras", "russian", "10june", "june10", "2019")
DIGIT9 = {c: i for i, c in enumerate(NINE_SYMS)}


def raw_to_digits(raw):
    return [DIGIT9[c] for c in raw]


def digits_to_raw(digits):
    return "".join(NINE_SYMS[d % 9] for d in digits)


def keyword_to_key9(keyword):
    """A-Z/0-9 -> 0-8 mod 9, simple letter/digit position mapping -- no
    checkerboard-alphabet convention needed here since this operates on the
    raw base-9 symbol stream, not 25-letter code slots."""
    key = []
    for c in keyword.upper():
        if c.isalpha():
            key.append((ord(c) - ord("A")) % 9)
        elif c.isdigit():
            key.append(int(c) % 9)
    return key


def gronsfeld_shift_raw(raw, key9, sign):
    if not key9:
        return None
    digits = raw_to_digits(raw)
    shifted = [(d + sign * key9[i % len(key9)]) % 9 for i, d in enumerate(digits)]
    return digits_to_raw(shifted)


def progressive_shift_raw(raw, start, step):
    digits = raw_to_digits(raw)
    shifted = [(d + start + i * step) % 9 for i, d in enumerate(digits)]
    return digits_to_raw(shifted)


def resegment_slots(shifted_raw, e1, e2, topology):
    codes = segment_codes(shifted_raw, e1, e2)
    if codes is None:
        return None
    idx = natural_code_index(e1, e2, topology)
    return [idx[c] for c in codes]


def self_test():
    # raw<->digit round trip
    digits = raw_to_digits(DBBI)
    assert len(digits) == 91 and all(0 <= d <= 8 for d in digits)
    assert digits_to_raw(digits) == DBBI

    # Gronsfeld shift/unshift round-trips on the raw stream.
    key9 = keyword_to_key9("enter")
    assert key9 == [4, 13 % 9, 19 % 9, 4, 17 % 9], key9  # E,N,T,E,R positions mod 9
    shifted = gronsfeld_shift_raw(DBBI, key9, +1)
    back = gronsfeld_shift_raw(shifted, key9, -1)
    assert back == DBBI, "Gronsfeld raw shift/unshift round-trip failed"

    # Progressive-shift formula sample points.
    assert progressive_shift_raw("a" * 5, start=0, step=0) == "a" * 5
    single = progressive_shift_raw("a", start=3, step=5)
    assert single == NINE_SYMS[3], single  # i=0 -> (0+3+0) % 9 = 3
    two = progressive_shift_raw("aa", start=0, step=2)
    assert two == NINE_SYMS[0] + NINE_SYMS[2], two  # i=0 -> 0, i=1 -> 2

    # Extra-keyword list is exactly the 5 disclosed items, no more.
    assert EXTRA_KEYWORDS == ("zebras", "russian", "10june", "june10", "2019")

    # Sub-experiment (a) must actually change segmentation vs. the untouched
    # baseline for at least one variant (confirms it's a different insertion
    # point than Phase 310, not a no-op).
    baseline = slot_sequence(DBBI, "b", "e", "top_first")
    shifted_raw = gronsfeld_shift_raw(DBBI, keyword_to_key9("matrixsumlist"), +1)
    shifted_slots = resegment_slots(shifted_raw, "b", "e", "top_first")
    assert shifted_slots != baseline

    print("self-test OK: raw<->digit round trip, Gronsfeld shift/unshift "
          "round trip, progressive-shift formula, extra-keyword list, and "
          "sub-experiment (a) resegmentation-differs-from-baseline all verified")


def run_variant(name, raw, e1, e2, topo, iters, restarts, results):
    baseline_slots = slot_sequence(raw, e1, e2, topo)
    if baseline_slots is None:
        return
    base_best = hillclimb_slots(baseline_slots, iters, restarts, seed=0)
    results.append((base_best[0], name, e1, e2, topo, "BASELINE", None))

    # (a) Gronsfeld pre-segmentation shift.
    for kw in CORE_ALPHABET_SEEDS:
        key9 = keyword_to_key9(kw)
        if not key9:
            continue
        for sign, label in ((+1, "+"), (-1, "-")):
            shifted_raw = gronsfeld_shift_raw(raw, key9, sign)
            shifted_slots = resegment_slots(shifted_raw, e1, e2, topo)
            if shifted_slots is None:
                continue
            best = hillclimb_slots(shifted_slots, iters, restarts,
                                    seed=hash(("a", name, e1, e2, topo, kw, sign)) & 0xffff)
            results.append((best[0], name, e1, e2, topo, f"(a){kw}", label))

    # (b) Progressive shift, 72 combinations, no keyword.
    for start in range(9):
        for step in range(1, 9):
            shifted_raw = progressive_shift_raw(raw, start, step)
            shifted_slots = resegment_slots(shifted_raw, e1, e2, topo)
            if shifted_slots is None:
                continue
            best = hillclimb_slots(shifted_slots, iters, restarts,
                                    seed=hash(("b", name, e1, e2, topo, start, step)) & 0xffff)
            results.append((best[0], name, e1, e2, topo, f"(b)start{start}step{step}", None))

    # (c) Extra keywords through the unmodified Phase 310 mechanism.
    for kw in EXTRA_KEYWORDS:
        key25 = keyword_to_key25(kw)
        if not key25:
            continue
        for sign, label in ((+1, "+"), (-1, "-")):
            shifted = apply_shift(baseline_slots, key25, sign)
            best = hillclimb_slots(shifted, iters, restarts,
                                    seed=hash(("c", name, e1, e2, topo, kw, sign)) & 0xffff)
            results.append((best[0], name, e1, e2, topo, f"(c){kw}", label))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--restarts", type=int, default=30)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    results = []
    for name, (raw, pairs) in TARGETS.items():
        for e1, e2 in pairs:
            for topo in TOPOLOGIES:
                run_variant(name, raw, e1, e2, topo, args.iters, args.restarts, results)
                print(f"[{name} {e1}/{e2} {topo}] done")

    results.sort(key=lambda r: -r[0])
    print(f"\n{len(results)} total hillclimbs run.")
    print("Top 20 by score (BASELINE rows show the unshifted reference to beat):")
    for score_, name, e1, e2, topo, kw, label in results[:20]:
        tag = kw if kw == "BASELINE" else (f"{kw}{label}" if label else kw)
        print(f"  {score_:8.1f}  {name} {e1}/{e2} {topo}  key={tag}")


if __name__ == "__main__":
    main()
