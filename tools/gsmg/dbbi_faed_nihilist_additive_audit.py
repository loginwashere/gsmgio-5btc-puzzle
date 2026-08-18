#!/usr/bin/env python3
"""Tests the Nihilist-cipher hypothesis raised in this session's Kahn
"The Codebreakers" chapter-by-chapter review pass: Chapter 18 (Russian
cryptology) covers the Nihilist cipher -- a straddling-checkerboard-style
Polybius encoding with a REPEATING NUMERIC KEY added on top -- in the exact
same chapter as the "Hayhanen System" (the real historical name for what
this puzzle already uses and this project already calls the VIC cipher/
straddling checkerboard). If the creator worked from a single reference,
Nihilist is the most structurally plausible untried technique: unlike a
brand-new cipher family, it EXTENDS the checkerboard model DBBI/FAED already
show a strong signal for (the {b,e} escape pair, rank 1/36), rather than
replacing it -- so it's compatible with, not competing against, the
strongest existing lead.

Mechanism tested: segment the raw ciphertext into its intrinsic 0-24
checkerboard code-slot sequence (independent of any guessed alphabet, reused
directly from matrixsum_permutation_sweep.py's natural_code_index/
segment_codes), add a repeating numeric key (mod 25) derived from a
candidate keyword, then hill-climb the best 25-slot-to-letter assignment for
the SHIFTED sequence using the exact same quadgram-fitness search this
project already uses for the baseline (unshifted) fit. A real Nihilist layer
would show up as a shift that scores dramatically better than the
established unshifted baseline for that variant.

Candidate keyword universe (closed, per this project's discipline): reuses
CORE_ALPHABET_SEEDS verbatim (matrixsum_permutation_sweep.py) -- the same
11-item, already-motivated set every other DBBI/FAED transform sweep in this
project draws from. Not a dictionary sweep.

This is a bounded exploratory pass (reduced restarts/iters vs. the full
canonical hillclimb budget) to check whether the idea is worth a full run --
not a final closure either way on its own.

Reproduce with:
    python3 tools/gsmg/dbbi_faed_nihilist_additive_audit.py --self-test
    python3 tools/gsmg/dbbi_faed_nihilist_additive_audit.py
"""
import argparse
import math
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import NINE_SYMS  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from matrixsum_permutation_sweep import (  # noqa: E402
    CORE_ALPHABET_SEEDS,
    natural_code_index,
    segment_codes,
)
from quadgram_solver import ALPHABET26, LOGP, FLOOR  # noqa: E402

TARGETS = {
    "DBBI": (DBBI, [("b", "e"), ("e", "b")]),
    "FAED": (FAED, [("g", "i"), ("i", "g"), ("h", "e"), ("e", "h")]),
}
TOPOLOGIES = ("top_first", "escapes_first")


def score(text):
    s = 0.0
    for i in range(len(text) - 3):
        s += LOGP.get(text[i:i + 4], FLOOR)
    return s


def slot_sequence(raw, e1, e2, topology):
    codes = segment_codes(raw, e1, e2)
    if codes is None:
        return None
    idx = natural_code_index(e1, e2, topology)
    return [idx[c] for c in codes]


def keyword_to_key25(keyword):
    """A-Z -> 0-24, collapsing J into I (standard 25-letter checkerboard
    convention, matches this project's existing pad25()/checkerboard alphabet
    treatment elsewhere)."""
    letters = [c for c in keyword.upper() if c.isalpha()]
    out = []
    for c in letters:
        c = "I" if c == "J" else c
        pos = ord(c) - ord("A")
        if c > "J":
            pos -= 1  # collapse the missing J slot
        out.append(pos)
    return out


def apply_shift(slots, key25, sign):
    if not key25:
        return None
    n = len(slots)
    return [(slots[i] + sign * key25[i % len(key25)]) % 25 for i in range(n)]


def decode_slots(slots, key26):
    return "".join(key26[i] for i in slots)


def hillclimb_slots(slots, iters, restarts, seed=None):
    rng = random.Random(seed)
    best = (-1e18, None, None)
    for r in range(restarts):
        key = list(ALPHABET26)
        rng.shuffle(key)
        cur_decode = decode_slots(slots, key)
        cur_score = score(cur_decode)
        T = 2.5
        for _ in range(iters):
            i, j = rng.sample(range(26), 2)
            key[i], key[j] = key[j], key[i]
            cand_decode = decode_slots(slots, key)
            cand_score = score(cand_decode)
            delta = cand_score - cur_score
            if delta >= 0 or rng.random() < math.exp(delta / max(T, 1e-6)):
                cur_score, cur_decode = cand_score, cand_decode
            else:
                key[i], key[j] = key[j], key[i]
            T *= 0.9995
        if cur_score > best[0]:
            best = (cur_score, cur_decode, key[:])
    return best


def self_test():
    slots = slot_sequence(DBBI, "b", "e", "top_first")
    assert slots is not None and len(slots) == 63, f"expected 63 DBBI codes, got {len(slots) if slots else None}"
    assert all(0 <= s <= 24 for s in slots)
    key25 = keyword_to_key25("enter")
    # E=4, N=13->12 (J removed), T=19->18, E=4, R=17->16, all shifted down by
    # 1 for letters after the collapsed J.
    assert key25 == [4, 12, 18, 4, 16], key25
    shifted = apply_shift(slots, key25, +1)
    back = apply_shift(shifted, key25, -1)
    assert back == slots, "shift/unshift round-trip failed"
    print("self-test OK: slot segmentation, keyword mapping, shift round-trip all verified")


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
                base_slots = slot_sequence(raw, e1, e2, topo)
                if base_slots is None:
                    continue
                base_best = hillclimb_slots(base_slots, args.iters, args.restarts, seed=0)
                print(f"[{name} {e1}/{e2} {topo}] BASELINE (no shift) score={base_best[0]:.1f}")
                results.append((base_best[0], name, e1, e2, topo, "BASELINE", None))

                for kw in CORE_ALPHABET_SEEDS:
                    key25 = keyword_to_key25(kw)
                    if not key25:
                        continue
                    for sign, label in ((+1, "+"), (-1, "-")):
                        shifted = apply_shift(base_slots, key25, sign)
                        best = hillclimb_slots(shifted, args.iters, args.restarts,
                                                seed=hash((name, e1, e2, topo, kw, sign)) & 0xffff)
                        results.append((best[0], name, e1, e2, topo, kw, label))

    results.sort(key=lambda r: -r[0])
    print("\nTop 15 by score (BASELINE rows show the unshifted reference to beat):")
    for score_, name, e1, e2, topo, kw, label in results[:15]:
        tag = kw if kw == "BASELINE" else f"{kw}{label}"
        print(f"  {score_:8.1f}  {name} {e1}/{e2} {topo}  key={tag}")


if __name__ == "__main__":
    main()
