#!/usr/bin/env python3
"""Bounded native-9ary prime/character-zeroing sweep for DBBI and FAED.

The creator said prime numbers are required and that some *characters*
(plural) must be "zeroed out." The historical probe tested an obsolete
decimal stand-in. This pass stays in the native a-i system and interprets
"zeroed out" as masked from the retained stream, not replaced by `a`:
native `a` is an ordinary checkerboard code, so replacement would not mean
absence.

The complete pre-registered family is:
  - units: raw a-i symbols or complete checkerboard codes;
  - indexing: zero-based or one-based prime positions;
  - polarity: retain prime positions or retain their complement;
  - escape hypotheses: DBBI {b,e}; FAED {g,i} and {h,e};
  - both escape orders and both established board topologies.

Every null trial preserves the relevant multiset (raw symbols for raw-unit
branches, complete codes for code-unit branches), applies the *entire*
transform family, and records its maximum normalized language score.
Stage 1 is a 500-trial screen. Only p<0.02 advances to an independent
5,000-trial confirmation; significance requires p<0.005 per target.
Only a confirmed target is escalated to the CBC and AES-Key-Wrap oracles.
"""

import argparse
import multiprocessing
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from aes_key_wrap_sweep import chain_unwrapped  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    answer_forms,
    build_board_9ary,
    keystr_forms,
    pad25,
)
from data import DBBI, FAED  # noqa: E402
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS  # noqa: E402
from prefix_boundary_sweep import (  # noqa: E402
    MERGE_DIRS,
    TAIL_FILLS,
    TOPOLOGIES,
    _clean_book_sample,
    encode_9ary,
    segment_codes,
)
from quadgram_solver import score as quadgram_score  # noqa: E402

TARGET_STREAMS = {"dbbi": DBBI, "faed": FAED}
TARGET_PAIRS = {
    "dbbi": (("b", "e"),),
    "faed": (("g", "i"), ("h", "e")),
}
UNITS = ("raw", "codes")
INDEX_BASES = (0, 1)
POLARITIES = ("keep_primes", "keep_nonprimes")
SEED_BASE_1 = 202607251
SEED_BASE_2 = 202607252000
ALL_CBC_VARIANTS = None, EXTENDED_CIPHER_VARIANTS


def is_prime(value):
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def retain_units(units, index_base, polarity):
    retained = []
    for index, unit in enumerate(units):
        prime = is_prime(index + index_base)
        keep = prime if polarity == "keep_primes" else not prime
        if keep:
            retained.append(unit)
    return retained


def ordered_pairs(pair):
    left, right = pair
    return ((left, right), (right, left))


def alphabet_candidates():
    seen = {}
    for seed in CORE_ALPHABET_SEEDS:
        for tail_fill in TAIL_FILLS:
            for merge_direction in MERGE_DIRS:
                alphabet = pad25(
                    seed,
                    tail_fill=tail_fill,
                    merge_direction=merge_direction,
                )
                seen.setdefault(
                    alphabet,
                    (seed, tail_fill, merge_direction),
                )
    return tuple((alphabet, metadata) for alphabet, metadata in seen.items())


ALPHABET_CANDIDATES = alphabet_candidates()


def normalized_score(text):
    return quadgram_score(text) / max(1, len(text) - 3)


def decode_codes(codes, alphabet, e1, e2, topology):
    board = build_board_9ary(alphabet, e1, e2, topology)
    try:
        return "".join(board[code] for code in codes)
    except KeyError:
        return None


def transformed_streams(stream, target):
    """Return every unique transformed stream with all generating labels."""
    variants = {}
    raw_units = list(stream)
    for pair in TARGET_PAIRS[target]:
        codes = segment_codes(stream, *pair)
        if codes is None:
            continue
        for unit_name, source_units in (("raw", raw_units), ("codes", codes)):
            for index_base in INDEX_BASES:
                for polarity in POLARITIES:
                    retained = retain_units(source_units, index_base, polarity)
                    if not retained:
                        continue
                    transformed = "".join(retained)
                    key = (pair, transformed)
                    variants.setdefault(key, []).append(
                        (unit_name, index_base, polarity)
                    )
    return variants


def all_candidates(stream, target):
    candidates = []
    for (pair, transformed), transform_labels in transformed_streams(
        stream, target
    ).items():
        codes = segment_codes(transformed, *pair)
        if codes is None or len(codes) < 4:
            continue
        for e1, e2 in ordered_pairs(pair):
            for topology in TOPOLOGIES:
                for alphabet, alphabet_meta in ALPHABET_CANDIDATES:
                    decoded = decode_codes(codes, alphabet, e1, e2, topology)
                    if decoded is None:
                        continue
                    candidates.append(
                        (
                            normalized_score(decoded),
                            decoded,
                            {
                                "pair": pair,
                                "escape_order": (e1, e2),
                                "topology": topology,
                                "transforms": tuple(transform_labels),
                                "alphabet": alphabet_meta,
                                "decoded_length": len(decoded),
                            },
                        )
                    )
    return candidates


def best_score(stream, target):
    return max(
        (candidate[0] for candidate in all_candidates(stream, target)),
        default=float("-inf"),
    )


def shuffled_sources(stream, target, seed):
    rng = random.Random(seed)
    raw = list(stream)
    rng.shuffle(raw)
    code_streams = {}
    for pair in TARGET_PAIRS[target]:
        codes = segment_codes(stream, *pair)
        if codes is None:
            continue
        shuffled = list(codes)
        rng.shuffle(shuffled)
        rejoined = "".join(shuffled)
        if segment_codes(rejoined, *pair) != shuffled:
            raise AssertionError(f"{target}/{pair}: shuffled codes did not re-segment")
        code_streams[pair] = shuffled
    return raw, code_streams


def transformed_shuffled_streams(stream, target, seed):
    raw, code_streams = shuffled_sources(stream, target, seed)
    variants = {}
    for pair in TARGET_PAIRS[target]:
        if pair not in code_streams:
            continue
        for unit_name, source_units in (
            ("raw", raw),
            ("codes", code_streams[pair]),
        ):
            for index_base in INDEX_BASES:
                for polarity in POLARITIES:
                    retained = retain_units(source_units, index_base, polarity)
                    if not retained:
                        continue
                    transformed = "".join(retained)
                    key = (pair, transformed)
                    variants.setdefault(key, []).append(
                        (unit_name, index_base, polarity)
                    )
    return variants


def candidates_from_variants(variants):
    candidates = []
    for (pair, transformed), transform_labels in variants.items():
        codes = segment_codes(transformed, *pair)
        if codes is None or len(codes) < 4:
            continue
        for e1, e2 in ordered_pairs(pair):
            for topology in TOPOLOGIES:
                for alphabet, alphabet_meta in ALPHABET_CANDIDATES:
                    decoded = decode_codes(codes, alphabet, e1, e2, topology)
                    if decoded is None:
                        continue
                    candidates.append(
                        (
                            normalized_score(decoded),
                            decoded,
                            {
                                "pair": pair,
                                "escape_order": (e1, e2),
                                "topology": topology,
                                "transforms": tuple(transform_labels),
                                "alphabet": alphabet_meta,
                                "decoded_length": len(decoded),
                            },
                        )
                    )
    return candidates


def _shuffle_trial(job):
    stream, target, seed = job
    variants = transformed_shuffled_streams(stream, target, seed)
    return max(
        (candidate[0] for candidate in candidates_from_variants(variants)),
        default=float("-inf"),
    )


def seed_ranges_overlap(base1, count1, base2, count2):
    """True if the half-open seed ranges [base1, base1+count1) and
    [base2, base2+count2) share any integer. Stage 1/Stage 2 must draw
    disjoint shuffle seeds for Stage 2 to be an actually-independent
    confirmation (random.Random(seed) is deterministic, so an overlapping
    seed reruns the identical null trial, not a fresh one)."""
    return max(base1, base2) < min(base1 + count1, base2 + count2)


def shuffle_gate(target, trials, seed_base, workers):
    stream = TARGET_STREAMS[target]
    real_candidates = all_candidates(stream, target)
    real_best = max(real_candidates, key=lambda item: item[0])
    jobs = [
        (stream, target, seed_base + trial)
        for trial in range(trials)
    ]
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as executor:
        null_scores = list(
            executor.map(
                _shuffle_trial,
                jobs,
                chunksize=max(1, trials // max(1, workers * 4)),
            )
        )
    exceedances = sum(score >= real_best[0] for score in null_scores)
    return {
        "real_best": real_best,
        "null_mean": sum(null_scores) / len(null_scores),
        "null_max": max(null_scores),
        "exceedances": exceedances,
        "trials": trials,
        "p": (exceedances + 1) / (trials + 1),
    }


def retained_count(length, index_base, polarity):
    return len(retain_units([None] * length, index_base, polarity))


def encoded_prefix_for_raw_slots(slots, alphabet, e1, e2, topology):
    """Build a real-English plaintext whose encoding is EXACTLY `slots` raw
    a-i symbols, by construction rather than by hoping a fixed book-sample
    walk happens to land on the target. Each plaintext letter encodes to 1
    (top-row) or 2 (escape-row) symbols, so a greedy walk can overshoot by
    exactly 1 symbol at the last step; the only such step is fixed by
    substituting a guaranteed single-symbol top-row letter (build_board_9ary
    always assigns exactly 7 top-row codes, for any alphabet/pair/topology)
    instead of the natural next book character."""
    if slots == 0:
        return "", []
    board = build_board_9ary(alphabet, e1, e2, topology)
    rev = {v: k for k, v in board.items()}
    top_letter = next(ch for ch in alphabet if len(rev[ch]) == 1)
    sample = _clean_book_sample(slots + 50)
    chars = []
    total = 0
    for ch in sample:
        code_len = len(rev[ch])
        if total + code_len > slots:
            assert total == slots - 1 and code_len == 2, (
                f"unexpected overshoot: total={total} slots={slots} code_len={code_len}"
            )
            chars.append(top_letter)
            total += 1
            break
        chars.append(ch)
        total += code_len
        if total == slots:
            break
    else:
        raise AssertionError(f"book sample exhausted before reaching {slots} raw symbols")
    plaintext = "".join(chars)
    encoded = encode_9ary(plaintext, alphabet, e1, e2, topology)
    assert len(encoded) == slots, f"exact-slot construction invariant failed: {len(encoded)} != {slots}"
    return plaintext, list(encoded)


def build_control(target, pair, unit_name, index_base, polarity):
    e1, e2 = pair
    topology = "top_first"
    alphabet = pad25("matrixsumlist")
    real_stream = TARGET_STREAMS[target]
    if unit_name == "raw":
        total_units = len(real_stream)
        slots = retained_count(total_units, index_base, polarity)
        plaintext, encoded_units = encoded_prefix_for_raw_slots(
            slots, alphabet, e1, e2, topology
        )
    else:
        real_codes = segment_codes(real_stream, e1, e2)
        total_units = len(real_codes)
        slots = retained_count(total_units, index_base, polarity)
        plaintext = _clean_book_sample(slots)[:slots]
        encoded = encode_9ary(plaintext, alphabet, e1, e2, topology)
        encoded_units = segment_codes(encoded, e1, e2)
        if len(encoded_units) != slots:
            raise AssertionError("one-code-per-letter control invariant failed")

    retained_indices = [
        index
        for index in range(total_units)
        if (
            is_prime(index + index_base)
            if polarity == "keep_primes"
            else not is_prime(index + index_base)
        )
    ]
    assert len(encoded_units) == len(retained_indices), (
        f"pre-zip invariant failed: {len(encoded_units)} encoded units != "
        f"{len(retained_indices)} retained positions"
    )
    observed_units = ["a"] * total_units
    for index, encoded_unit in zip(retained_indices, encoded_units):
        observed_units[index] = encoded_unit
    observed = "".join(observed_units)
    return observed, plaintext, alphabet, topology


def run_self_tests():
    assert retain_units(list("abcdefghi"), 0, "keep_primes") == list("cdfh")
    assert retain_units(list("abcdefghi"), 1, "keep_primes") == list("bceg")
    assert retain_units(list("abcdefghi"), 0, "keep_nonprimes") == list("abegi")
    assert retain_units(list("abcdefghi"), 1, "keep_nonprimes") == list("adfhi")

    stage1_seeds = {SEED_BASE_1 + i for i in range(500)}
    stage2_seeds = {SEED_BASE_2 + i for i in range(5000)}
    assert stage1_seeds.isdisjoint(stage2_seeds), (
        "Stage 1/Stage 2 default seed ranges overlap -- Stage 2 would not "
        "be an independent confirmation"
    )
    assert not seed_ranges_overlap(SEED_BASE_1, 500, SEED_BASE_2, 5000)
    assert seed_ranges_overlap(SEED_BASE_1, 500, SEED_BASE_1 + 100, 500)

    for target, pairs in TARGET_PAIRS.items():
        for pair in pairs:
            real_codes = segment_codes(TARGET_STREAMS[target], *pair)
            assert real_codes is not None
            assert segment_codes("".join(real_codes), *pair) == real_codes
            for unit_name in UNITS:
                for index_base in INDEX_BASES:
                    for polarity in POLARITIES:
                        observed, plaintext, alphabet, topology = build_control(
                            target, pair, unit_name, index_base, polarity
                        )
                        variants = transformed_streams(observed, target)
                        wanted_label = (unit_name, index_base, polarity)
                        matching = [
                            transformed
                            for (candidate_pair, transformed), labels in variants.items()
                            if candidate_pair == pair and wanted_label in labels
                        ]
                        assert matching, (
                            f"missing control branch {target}/{pair}/{wanted_label}"
                        )
                        recovered_codes = segment_codes(matching[0], *pair)
                        recovered = decode_codes(
                            recovered_codes,
                            alphabet,
                            pair[0],
                            pair[1],
                            topology,
                        )
                        assert recovered == plaintext, (
                            f"control failed {target}/{pair}/{wanted_label}: "
                            f"{recovered!r} != {plaintext!r}"
                        )
                        candidates = all_candidates(observed, target)
                        ranked = sorted(
                            candidates, key=lambda item: item[0], reverse=True
                        )
                        assert ranked and ranked[0][1] == plaintext, (
                            f"end-to-end candidate family did not recover "
                            f"control {target}/{pair}/{wanted_label} as the "
                            f"TOP-1 scorer (matches the max-statistic "
                            f"shuffle_gate() actually compares against): "
                            f"got {ranked[0][1]!r} (score {ranked[0][0]:.4f}) "
                            f"want {plaintext!r}"
                        )
    print("[*] self-tests passed: masks, segmentation, and all synthetic controls")


def unique_top_candidates(target, limit=20):
    ranked = sorted(
        all_candidates(TARGET_STREAMS[target], target),
        key=lambda item: item[0],
        reverse=True,
    )
    unique = []
    seen = set()
    for score, decoded, metadata in ranked:
        if decoded in seen:
            continue
        seen.add(decoded)
        unique.append((score, decoded, metadata))
        if len(unique) == limit:
            break
    return unique


def escalate(target, include_quarantined=False):
    blobs = (
        {**BLOBS, **QUARANTINED_BLOBS}
        if include_quarantined
        else BLOBS
    )
    hits = []
    for score, decoded, metadata in unique_top_candidates(target):
        for form in answer_forms(decoded):
            for keystr in keystr_forms(form):
                for variants in ALL_CBC_VARIANTS:
                    result = aes_try_open(
                        keystr,
                        kdf_variants=variants,
                        blobs=blobs,
                    )
                    if result:
                        hits.append(
                            ("cbc", score, decoded, metadata, keystr, result)
                        )
                for unwrap in aes_keywrap_try_open_bytes(
                    keystr.encode(),
                    blobs=blobs,
                ):
                    raw_hits, passphrase_hits = chain_unwrapped(
                        unwrap[-1],
                        unwrap[0],
                        blobs=blobs,
                    )
                    hits.append(
                        (
                            "keywrap",
                            score,
                            decoded,
                            metadata,
                            keystr,
                            unwrap,
                            raw_hits,
                            passphrase_hits,
                        )
                    )
    return hits


def run_target(
    target,
    workers,
    trials_1,
    trials_2,
    include_quarantined,
):
    gate1 = shuffle_gate(target, trials_1, SEED_BASE_1, workers)
    print(
        f"[stage 1] {target}: real={gate1['real_best'][0]:.6f} "
        f"null_mean={gate1['null_mean']:.6f} "
        f"null_max={gate1['null_max']:.6f} "
        f"p={gate1['p']:.6f} "
        f"({gate1['exceedances']}/{trials_1})"
    )
    print(f"  best metadata: {gate1['real_best'][2]}")
    print(f"  best decode: {gate1['real_best'][1]!r}")
    if gate1["p"] >= 0.02:
        print(f"[*] {target}: stopped after Stage 1 (p >= 0.02)")
        return {"gate1": gate1, "gate2": None, "hits": []}

    if seed_ranges_overlap(SEED_BASE_1, trials_1, SEED_BASE_2, trials_2):
        raise AssertionError(
            f"Stage 1/Stage 2 shuffle seed ranges overlap for trials_1={trials_1}, "
            f"trials_2={trials_2}: Stage 2 would not be an independent confirmation"
        )
    gate2 = shuffle_gate(target, trials_2, SEED_BASE_2, workers)
    print(
        f"[stage 2] {target}: real={gate2['real_best'][0]:.6f} "
        f"null_mean={gate2['null_mean']:.6f} "
        f"null_max={gate2['null_max']:.6f} "
        f"p={gate2['p']:.6f} "
        f"({gate2['exceedances']}/{trials_2})"
    )
    if gate2["p"] >= 0.005:
        print(f"[*] {target}: not significant at p < 0.005; no oracle escalation")
        return {"gate1": gate1, "gate2": gate2, "hits": []}

    hits = escalate(target, include_quarantined)
    print(f"[*] {target}: oracle escalation complete, hits={len(hits)}")
    return {"gate1": gate1, "gate2": gate2, "hits": hits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--target", choices=("dbbi", "faed", "both"), default="both")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--trials-1", type=int, default=500)
    parser.add_argument("--trials-2", type=int, default=5000)
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    run_self_tests()
    if args.self_test:
        return

    targets = TARGET_STREAMS if args.target == "both" else (args.target,)
    for target in targets:
        run_target(
            target,
            workers=args.workers,
            trials_1=args.trials_1,
            trials_2=args.trials_2,
            include_quarantined=args.include_quarantined,
        )


if __name__ == "__main__":
    main()
