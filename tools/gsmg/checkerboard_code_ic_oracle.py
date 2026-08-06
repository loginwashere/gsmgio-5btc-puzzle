#!/usr/bin/env python3
"""A partial, alphabet-independent oracle for the checkerboard escape pair.

Every prior attack on `dbbi`/`faed` needed a full candidate alphabet before
producing any signal at all (quadgram fitness, AES success) -- a wrong
alphabet and a right one both just look like noise until everything lines
up simultaneously. This module asks whether a *weaker* signal exists that
needs only an escape-pair hypothesis, not a full alphabet: the Index of
Coincidence (IC) of the SEGMENTED CODE stream (not the raw a-i symbols,
which earlier phases already found unremarkable).

The reasoning: IC is invariant under monoalphabetic substitution -- it
depends only on the multiset of symbol frequencies, not their labels. A
real straddling-checkerboard encoding of English, correctly segmented into
its 25 possible codes, should therefore show roughly the same IC as English
prose itself (~0.067), regardless of which candidate alphabet you use --
you don't need the alphabet at all to compute it. Segmenting the SAME
ciphertext under a WRONG escape pair scrambles which raw symbols get paired
into two-symbol codes, which should generally destroy that structure. If
so, ranking IC across all 36 escape-pair hypotheses could identify the
right one without ever guessing a keyword. Topology has no effect on this
statistic: it only changes which code maps to which letter, never which
raw substrings count as one code, so only the 36 escape pairs are tested,
not escape pair x topology.

This is calibrated on synthetic ciphertexts BEFORE touching the real data,
reusing `checkerboard_recovery_calibration.py`'s already-validated
profile-matched board construction (same corpora, same exact
raw-length/code-count/type-count profile as the real target) so any result
reflects this technique's real power at `dbbi`/`faed`'s actual length, not
an easier synthetic case.
"""

import argparse
import itertools
import random
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import checkerboard_recovery_calibration as crc  # noqa: E402
from cb_common import NINE_SYMS  # noqa: E402
from data import DBBI, FAED  # noqa: E402

ALL_ESCAPE_PAIRS = tuple(itertools.combinations(NINE_SYMS, 2))  # 36 pairs
ENGLISH_PROSE_IC = 0.067


def segment_codes(stream, e1, e2):
    """Raw-code tokenization only -- no alphabet, no topology. Returns None
    on a dangling final escape (that escape pair cannot validly segment this
    stream at all)."""
    codes = []
    i, n = 0, len(stream)
    while i < n:
        ch = stream[i]
        if ch in (e1, e2):
            if i + 1 >= n:
                return None
            codes.append(stream[i:i + 2])
            i += 2
        else:
            codes.append(ch)
            i += 1
    return codes


def code_ic(codes):
    n = len(codes)
    if n < 2:
        return 0.0
    counts = Counter(codes)
    numerator = sum(count * (count - 1) for count in counts.values())
    return numerator / (n * (n - 1))


def ic_by_escape_pair(stream):
    result = {}
    for e1, e2 in ALL_ESCAPE_PAIRS:
        codes = segment_codes(stream, e1, e2)
        if codes is not None:
            result[(e1, e2)] = code_ic(codes)
    return result


def rank_of_pair(ic_map, pair):
    ranked = sorted(
        ic_map.items(),
        key=lambda kv: abs(kv[1] - ENGLISH_PROSE_IC),
    )
    target = frozenset(pair)
    for candidate, value in ranked:
        if frozenset(candidate) == target:
            distance = abs(value - ENGLISH_PROSE_IC)
            closer = sum(
                abs(candidate_ic - ENGLISH_PROSE_IC) < distance
                for candidate_ic in ic_map.values()
            )
            tied = sum(
                abs(candidate_ic - ENGLISH_PROSE_IC) == distance
                for candidate_ic in ic_map.values()
            )
            average_rank = closer + (tied + 1) / 2
            return average_rank, value, ranked, tied
    raise ValueError(f"{pair} did not validly segment this stream")


def load_corpus_letters():
    return {
        name: crc.load_letters(path, stride)
        for name, (path, stride) in crc.CORPUS_SOURCES.items()
    }


def synthetic_trial(profile_name, corpus_letters, rng, max_attempts=8000):
    """Exact profile match (dbbi's real 35-top/28-escape split etc.), reusing
    `checkerboard_recovery_calibration`'s validated subset-sum board
    construction unchanged. Practical for dbbi; for faed this exact-sum
    constraint turns out to be too rare in real English samples to hit in
    reasonable time (measured: 0 successes in 3,000+ attempts even with a
    fast DP subset-sum, versus this module's exhaustive-combinations
    version) -- see `length_matched_trial` for the profile used instead."""
    crc.apply_profile(profile_name)
    for _ in range(max_attempts):
        source = rng.choice(list(corpus_letters))
        letters = corpus_letters[source]
        if len(letters) <= crc.PLAINTEXT_LEN:
            continue
        start = rng.randrange(0, len(letters) - crc.PLAINTEXT_LEN)
        plaintext = letters[start:start + crc.PLAINTEXT_LEN]
        alphabet25 = crc.build_profile_matched_board(plaintext, rng)
        if alphabet25 is None:
            continue
        ciphertext = crc.encode(
            plaintext, alphabet25, crc.ENCODE_E1, crc.ENCODE_E2, crc.ENCODE_TOPOLOGY
        )
        if ciphertext is None:
            continue
        return ciphertext, (crc.ENCODE_E1, crc.ENCODE_E2)
    raise RuntimeError(f"could not build a synthetic {profile_name!r} trial")


LENGTH_TOLERANCE = 0.03  # +/-3% of the real target's raw length


def random_25_alphabet(rng):
    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    rng.shuffle(letters)
    return "".join(letters[:25])


def length_matched_trial(profile_name, corpus_letters, rng, max_attempts=20000):
    """Approximation used only where the exact profile match is impractical
    (faed). Drops the requirement that the board reproduce faed's exact
    35/28-style top/escape split and 25-distinct-type histogram; keeps the
    two things this experiment actually needs -- real English plaintext and
    a resulting RAW ciphertext length within +/-3% of the real target's raw
    length -- via a fully random (not profile-matched) 25-letter alphabet
    and adaptive plaintext-length search. Code-level IC does not depend on
    which specific letters sit in the top vs escape rows, only on the
    resulting code-frequency distribution, so this does not change what is
    being measured -- only how expensive it is to construct a matching
    synthetic ciphertext."""
    crc.apply_profile(profile_name)
    target_raw = crc.RAW_LEN
    low, high = int(target_raw * (1 - LENGTH_TOLERANCE)), int(target_raw * (1 + LENGTH_TOLERANCE))
    plaintext_len = crc.PLAINTEXT_LEN
    for _ in range(max_attempts):
        source = rng.choice(list(corpus_letters))
        letters = corpus_letters[source]
        if len(letters) <= plaintext_len:
            continue
        start = rng.randrange(0, len(letters) - plaintext_len)
        plaintext = letters[start:start + plaintext_len]
        alphabet25 = random_25_alphabet(rng)
        ciphertext = crc.encode(
            plaintext, alphabet25, crc.ENCODE_E1, crc.ENCODE_E2, crc.ENCODE_TOPOLOGY
        )
        if ciphertext is None:
            continue
        if low <= len(ciphertext) <= high:
            return ciphertext, (crc.ENCODE_E1, crc.ENCODE_E2)
        # nudge plaintext length toward the target and try again
        if len(ciphertext) < low:
            plaintext_len += 1
        elif len(ciphertext) > high:
            plaintext_len -= 1
    raise RuntimeError(f"could not build a length-matched synthetic {profile_name!r} trial")


def null_trial(profile_name, rng):
    crc.apply_profile(profile_name)
    return "".join(rng.choice(NINE_SYMS) for _ in range(crc.RAW_LEN))


EXACT_PROFILE_MATCH = {"dbbi": True, "faed": False}


def run_calibration(profile_name, trials, seed):
    rng = random.Random(seed)
    corpus_letters = load_corpus_letters()
    trial_fn = synthetic_trial if EXACT_PROFILE_MATCH[profile_name] else length_matched_trial
    english_ranks, english_true_ics, english_best_ics = [], [], []
    for _ in range(trials):
        ciphertext, true_pair = trial_fn(profile_name, corpus_letters, rng)
        ic_map = ic_by_escape_pair(ciphertext)
        rank, true_ic, ranked, tied = rank_of_pair(ic_map, true_pair)
        english_ranks.append(rank)
        english_true_ics.append(true_ic)
        english_best_ics.append(ranked[0][1])

    null_ranks, null_true_ics = [], []
    fixed_pair = ALL_ESCAPE_PAIRS[0]
    while len(null_ranks) < trials:
        stream = null_trial(profile_name, rng)
        ic_map = ic_by_escape_pair(stream)
        if frozenset(fixed_pair) not in {frozenset(p) for p in ic_map}:
            continue  # fixed_pair happened to dangle on this random stream
        rank, true_ic, _ranked, tied = rank_of_pair(ic_map, fixed_pair)
        null_ranks.append(rank)
        null_true_ics.append(true_ic)

    return {
        "profile": profile_name,
        "trials": trials,
        "english_rank_1_rate": sum(r == 1 for r in english_ranks) / trials,
        "english_rank_top5_rate": sum(r <= 5 for r in english_ranks) / trials,
        "english_mean_rank": sum(english_ranks) / trials,
        "english_mean_true_ic": sum(english_true_ics) / trials,
        "english_mean_best_ic": sum(english_best_ics) / trials,
        "null_mean_rank": sum(null_ranks) / trials,
        "null_rank_1_rate": sum(r == 1 for r in null_ranks) / trials,
        "null_rank_top5_rate": sum(r <= 5 for r in null_ranks) / trials,
        "null_mean_true_ic": sum(null_true_ics) / trials,
    }


def apply_to_real_data(target, expected_topology_note=""):
    stream = {"dbbi": DBBI, "faed": FAED}[target]
    ic_map = ic_by_escape_pair(stream)
    ranked = sorted(
        ic_map.items(),
        key=lambda kv: abs(kv[1] - ENGLISH_PROSE_IC),
    )
    return {"target": target, "ranked": ranked}


def print_calibration(result):
    print(f"[*] calibration for profile={result['profile']!r}, {result['trials']} trials each")
    print(
        "    real-English true pair: "
        f"rank=1 rate={result['english_rank_1_rate']:.3f}, "
        f"top-5 rate={result['english_rank_top5_rate']:.3f}, "
        f"mean rank={result['english_mean_rank']:.2f}/36, "
        f"mean IC={result['english_mean_true_ic']:.4f} "
        f"(mean closest IC across all 36 pairs="
        f"{result['english_mean_best_ic']:.4f}, "
        f"English prose reference={ENGLISH_PROSE_IC})"
    )
    print(
        "    random-noise control:   "
        f"rank=1 rate={result['null_rank_1_rate']:.3f}, "
        f"top-5 rate={result['null_rank_top5_rate']:.3f}, "
        f"mean rank={result['null_mean_rank']:.2f}/36, "
        f"mean IC={result['null_mean_true_ic']:.4f}"
    )


def print_real_data(result):
    print(
        f"[*] real {result['target']} -- all 36 escape pairs ranked by "
        f"distance to English IC={ENGLISH_PROSE_IC}:"
    )
    for rank, (pair, ic) in enumerate(result["ranked"][:10], start=1):
        print(
            f"    {rank:2}. {''.join(pair)}: IC={ic:.4f}, "
            f"|delta|={abs(ic - ENGLISH_PROSE_IC):.4f}"
        )


def self_test():
    codes = ["a", "a", "bc", "a", "bc"]
    assert abs(code_ic(codes) - (3 * 2 + 2 * 1) / (5 * 4)) < 1e-12
    stream = "aabcabc"
    segmented = segment_codes(stream, "b", "c")
    assert segmented == ["a", "a", "bc", "a", "bc"]
    assert segment_codes("ab", "b", "c") is None
    ic_map = {
        ("a", "b"): ENGLISH_PROSE_IC,
        ("a", "c"): ENGLISH_PROSE_IC + 0.01,
        ("a", "d"): ENGLISH_PROSE_IC + 0.01,
        ("a", "e"): ENGLISH_PROSE_IC + 0.02,
    }
    rank, value, ranked, tied = rank_of_pair(ic_map, ("a", "c"))
    assert rank == 2.5
    assert tied == 2
    best_rank, best_value, _, best_tied = rank_of_pair(ic_map, ("a", "b"))
    assert best_rank == 1
    assert best_value == ENGLISH_PROSE_IC
    assert best_tied == 1
    assert ranked[0][1] == ENGLISH_PROSE_IC
    real_dbbi = apply_to_real_data("dbbi")
    top_pairs = {frozenset(pair) for pair, _ic in real_dbbi["ranked"][:5]}
    print("[*] self-test OK: code IC, segmentation, and ranking all verified")
    print(
        "    (real dbbi top-5 escape pairs by distance to English IC: "
        f"{sorted(''.join(sorted(p)) for p in top_pairs)})"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--calibrate", choices=("dbbi", "faed"), default=None)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--real", choices=("dbbi", "faed"), default=None)
    args = parser.parse_args()

    if args.self_test:
        self_test()

    if args.calibrate:
        result = run_calibration(args.calibrate, args.trials, args.seed)
        print_calibration(result)

    if args.real:
        result = apply_to_real_data(args.real)
        print_real_data(result)


if __name__ == "__main__":
    main()
