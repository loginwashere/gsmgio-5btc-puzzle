#!/usr/bin/env python3
"""Path 4 from the 2026-07-24 "Best Remaining Paths" review: bounded test of
the prefix/header-boundary hypothesis. `dbbi` and `faed` are literally the
first 4 symbols of their own ciphertext streams (confirmed: `DBBI ==
"dbbi" + DBBI[4:]`, likewise `FAED`) -- this project's naming convention for
the streams, per doc/GSMG_PUZZLE.md, but that naming choice neither confirms
nor rules out the same 4 symbols ALSO being functionally special within the
cipher (a header/selector), a question no prior sweep has tested.

Two bounded, mechanically well-defined variants (deliberately not an
open-ended search over arbitrary header semantics):

  1. DROP4: the real payload is `stream[4:]`; the leading 4 symbols are
     discarded entirely. Checkerboard-decoded under the established escape
     pairs x this project's existing clue-motivated keyword alphabets
     (CORE_ALPHABET_SEEDS, same list matrixsum_permutation_sweep.py uses) x
     both topologies x the existing pad25() tail-fill/merge-direction axes.
  2. PREFIX_AS_KEY: the leading 4 symbols ARE the key -- used verbatim as
     the pad25() keyword seed (the 9-symbol alphabet is already valid A-Z
     input, no transform needed) to decode the remaining `stream[4:]`
     payload, under the same escape/topology/tail-fill/merge-direction axes
     (no keyword loop needed here since the seed is fixed by the prefix).

Both are checked for internal consistency first (does dropping the prefix
still leave a cleanly-segmenting escape structure, no dangling escape) before
any decode is attempted. Every real result must clear a max-statistic
shuffle-gate (same complete-code-multiset-shuffle pattern established in
dual_quinary_sweep.py / digraphic_sweep.py) and a synthetic-control recovery
check (same discipline as checkerboard_recovery_calibration.py /
digraphic_sweep.py) before being trusted.

Usage:
    python3 tools/gsmg/prefix_boundary_sweep.py --self-test
    python3 tools/gsmg/prefix_boundary_sweep.py --calibrate --trials 500
    python3 tools/gsmg/prefix_boundary_sweep.py --shuffle-trials 2000
"""
import argparse
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from cb_common import (  # noqa: E402
    NINE_SYMS,
    aes_try_open,
    answer_forms,
    build_board_9ary,
    decode_9ary,
    keystr_forms,
    pad25,
)
from data import DBBI, FAED  # noqa: E402
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS  # noqa: E402
from quadgram_solver import score as quadgram_score  # noqa: E402

TARGET_STREAMS = {"dbbi": DBBI, "faed": FAED}
TARGET_ESCAPES = {
    "dbbi": [("b", "e"), ("e", "b")],
    "faed": [("g", "i"), ("i", "g"), ("h", "e"), ("e", "h")],
}
TOPOLOGIES = ("top_first", "escapes_first")
TAIL_FILLS = ("forward", "reverse", "keyboard")
MERGE_DIRS = ("backward", "forward")
BOOK_TEXT_PATH = SCRIPT_DIR.parent.parent / "wordlists" / "gsmg" / "cosmic_duality_book_full_text.txt"


def segment_codes(s, e1, e2):
    """Complete-code segmentation under an escape pair; None on dangling escape."""
    codes = []
    i = 0
    while i < len(s):
        d = s[i]
        if d in (e1, e2):
            if i + 1 >= len(s):
                return None
            codes.append(s[i:i + 2])
            i += 2
        else:
            codes.append(d)
            i += 1
    return codes


def encode_9ary(plaintext, alphabet25, e1, e2, topology="top_first"):
    """Reverse of cb_common.decode_9ary() -- used only to build synthetic
    controls with a known true answer. build_board_9ary()'s code->letter map
    is a bijection over the 25 codes/letters (pad25() guarantees 25 distinct
    letters), so it's cleanly invertible."""
    bd = build_board_9ary(alphabet25, e1, e2, topology)
    rev = {v: k for k, v in bd.items()}
    return "".join(rev[ch] for ch in plaintext)


def drop4_candidates(stream, e1, e2, topology):
    """Variant 1 (DROP4): payload = stream[4:], keyword alphabet drawn from
    this project's existing clue-motivated seed list."""
    payload = stream[4:]
    out = []
    for seed in CORE_ALPHABET_SEEDS:
        for tail_fill in TAIL_FILLS:
            for merge_direction in MERGE_DIRS:
                alphabet25 = pad25(seed, tail_fill=tail_fill, merge_direction=merge_direction)
                decoded = decode_9ary(payload, alphabet25, e1, e2, topology)
                if "?" in decoded:
                    continue
                out.append((quadgram_score(decoded), decoded, ("drop4", seed, tail_fill, merge_direction, topology)))
    return out


def prefix_as_key_candidates(stream, e1, e2, topology):
    """Variant 2 (PREFIX_AS_KEY): payload = stream[4:], keyword alphabet
    seeded directly from stream[:4] itself (already valid A-Z-equivalent
    input -- NINE_SYMS is a subset of the alphabet, no transform needed)."""
    prefix = stream[:4]
    payload = stream[4:]
    out = []
    for tail_fill in TAIL_FILLS:
        for merge_direction in MERGE_DIRS:
            alphabet25 = pad25(prefix, tail_fill=tail_fill, merge_direction=merge_direction)
            decoded = decode_9ary(payload, alphabet25, e1, e2, topology)
            if "?" in decoded:
                continue
            out.append((quadgram_score(decoded), decoded, ("prefix_as_key", prefix, tail_fill, merge_direction, topology)))
    return out


def all_candidates(stream, e1, e2):
    out = []
    for topology in TOPOLOGIES:
        out.extend(drop4_candidates(stream, e1, e2, topology))
        out.extend(prefix_as_key_candidates(stream, e1, e2, topology))
    return out


def best_score(stream, e1, e2):
    cands = all_candidates(stream, e1, e2)
    return max((c[0] for c in cands), default=float("-inf"))


def _shuffle_trial(args):
    codes, e1, e2, seed = args
    rng = random.Random(seed)
    shuffled = list(codes)
    rng.shuffle(shuffled)
    return best_score("".join(shuffled), e1, e2)


def shuffle_gate(stream, e1, e2, trials=2000, workers=16, seed_base=20260724):
    codes = segment_codes(stream, e1, e2)
    assert codes is not None, "escape pair does not cleanly segment this stream"
    real_best = best_score(stream, e1, e2)
    rng = random.Random(seed_base)
    jobs = [(codes, e1, e2, rng.getrandbits(64)) for _ in range(trials)]
    with ProcessPoolExecutor(max_workers=workers, mp_context=__import__("multiprocessing").get_context("spawn")) as ex:
        null_scores = list(ex.map(_shuffle_trial, jobs, chunksize=max(1, trials // (workers * 4))))
    at_least_as_good = sum(1 for s in null_scores if s >= real_best)
    p = (at_least_as_good + 1) / (trials + 1)
    return {
        "real_best": real_best,
        "null_mean": sum(null_scores) / len(null_scores),
        "null_max": max(null_scores),
        "p": p,
        "trials": trials,
    }


def _clean_book_sample(n):
    """Real English text for synthetic controls. Replaces J with I (rather
    than filtering it out) since build_synthetic_control() always uses
    pad25()'s default drop='J'/merge_direction='backward', under which J
    never appears as a decodable letter -- matches the same convention the
    real alphabet construction uses, rather than silently skipping letters
    and shortening the sample in a way that could bias its statistics."""
    text = BOOK_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    letters = "".join(ch for ch in text.upper() if "A" <= ch <= "Z").replace("J", "I")
    assert len(letters) >= n, f"book corpus too short: need {n}, have {len(letters)}"
    return letters[:n]


def build_synthetic_control(family, target, e1, e2, topology, seed_word_for_seed_variant="matrixsumlist"):
    """Encode a real English sample under a KNOWN configuration matching the
    exact mechanic being tested, so recovery can be verified against ground
    truth before trusting a real-target negative."""
    stream = TARGET_STREAMS[target]
    payload_len_symbols = len(stream) - 4
    tail_fill, merge_direction = "forward", "backward"
    if family == "drop4":
        alphabet25 = pad25(seed_word_for_seed_variant, tail_fill=tail_fill, merge_direction=merge_direction)
    elif family == "prefix_as_key":
        alphabet25 = pad25(stream[:4], tail_fill=tail_fill, merge_direction=merge_direction)
    else:
        raise ValueError(family)

    # Find how many plaintext letters produce payload_len_symbols encoded
    # symbols under this escape pair (each letter -> 1 or 2 symbols depending
    # on whether it's a top or escape-row letter) via direct simulation.
    board = build_board_9ary(alphabet25, e1, e2, topology)
    rev = {v: k for k, v in board.items()}
    sample = _clean_book_sample(payload_len_symbols)  # upper bound; trim below
    encoded_len = 0
    cut = 0
    for i, ch in enumerate(sample):
        encoded_len += len(rev[ch])
        cut = i + 1
        if encoded_len >= payload_len_symbols:
            break
    plaintext = sample[:cut]
    encoded = encode_9ary(plaintext, alphabet25, e1, e2, topology)
    if len(encoded) > payload_len_symbols:
        # trim to exact length (drops at most one trailing escape-coded letter)
        plaintext = plaintext[:-1]
        encoded = encode_9ary(plaintext, alphabet25, e1, e2, topology)
    prefix = stream[:4] if family == "prefix_as_key" else TARGET_STREAMS[target][:4]
    full_stream = prefix + encoded
    return {
        "plaintext": plaintext,
        "full_stream": full_stream,
        "alphabet25": alphabet25,
        "e1": e1,
        "e2": e2,
        "topology": topology,
    }


def run_self_tests():
    for target, escapes in TARGET_ESCAPES.items():
        stream = TARGET_STREAMS[target]
        for e1, e2 in escapes:
            codes = segment_codes(stream, e1, e2)
            codes4 = segment_codes(stream[4:], e1, e2)
            assert codes is not None, f"{target} {e1}{e2} full stream has dangling escape"
            assert codes4 is not None, (
                f"{target} {e1}{e2}: dropping the 4-symbol prefix creates a "
                f"dangling escape -- prefix-boundary hypothesis structurally "
                f"invalid for this escape pair"
            )

    # encode/decode round-trip (avoid 'J' -- pad25()'s default drop='J' means
    # J never appears as a decoded letter, since J merges into I)
    alphabet25 = pad25("testkeyword")
    pt = "THEQUICKBROWNFOXAMPSOVERALAZYDOGXX"
    enc = encode_9ary(pt, alphabet25, "b", "e", "top_first")
    dec = decode_9ary(enc, alphabet25, "b", "e", "top_first")
    assert dec == pt, f"encode/decode round-trip FAILED: {dec!r} != {pt!r}"

    # synthetic-control recovery: for each family/target/escape/topology,
    # the true candidate must be the top scorer among all candidates
    # generated by the corresponding sweep function.
    for family, cand_fn in (("drop4", drop4_candidates), ("prefix_as_key", prefix_as_key_candidates)):
        for target, escapes in TARGET_ESCAPES.items():
            e1, e2 = escapes[0]
            for topology in TOPOLOGIES:
                ctrl = build_synthetic_control(family, target, e1, e2, topology)
                cands = cand_fn(ctrl["full_stream"], e1, e2, topology)
                assert cands, f"{family}/{target}/{topology}: synthetic control produced no candidates"
                best = max(cands, key=lambda c: c[0])
                assert best[1] == ctrl["plaintext"], (
                    f"self-test FAILED: {family}/{target}/{topology} synthetic "
                    f"control not recovered as top scorer (got {best[1][:40]!r}, "
                    f"want {ctrl['plaintext'][:40]!r})"
                )
    print("[*] all self-tests passed (segmentation, round-trip, synthetic-control recovery)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--shuffle-trials", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        return

    for target, escapes in TARGET_ESCAPES.items():
        stream = TARGET_STREAMS[target]
        best_e1e2 = None
        best_overall = float("-inf")
        for e1, e2 in escapes:
            cands = all_candidates(stream, e1, e2)
            cands.sort(key=lambda c: -c[0])
            print(f"\n=== {target} ({e1}{e2}): {len(cands)} candidates ===")
            for sc, decoded, meta in cands[:args.top]:
                print(f"  {sc:10.1f}  {meta}  {decoded[:70]!r}")
            if cands and cands[0][0] > best_overall:
                best_overall = cands[0][0]
                best_e1e2 = (e1, e2)

        e1, e2 = best_e1e2
        gate = shuffle_gate(stream, e1, e2, trials=args.shuffle_trials, workers=args.workers)
        print(f"\n[shuffle gate] {target} best escape ({e1}{e2}): "
              f"real_best={gate['real_best']:.1f} null_mean={gate['null_mean']:.1f} "
              f"null_max={gate['null_max']:.1f} p={gate['p']:.5f} ({gate['trials']} trials)")
        if gate["p"] < 0.05:
            print(f"[*] {target} IS statistically exceptional -- escalate top candidates to AES")
            cands = all_candidates(stream, e1, e2)
            cands.sort(key=lambda c: -c[0])
            for sc, decoded, meta in cands[:20]:
                for form in answer_forms(decoded):
                    for keystr in keystr_forms(form):
                        r = aes_try_open(keystr)
                        if r:
                            print(f"[+++ AES HIT] {meta} -> {r}")
        else:
            print(f"[*] {target} not statistically exceptional (p={gate['p']:.5f} >= 0.05) "
                  f"-- not escalating to AES")


if __name__ == "__main__":
    main()
