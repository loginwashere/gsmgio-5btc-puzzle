#!/usr/bin/env python3
"""Pre-decode keyed-columnar transposition of raw DBBI/FAED, then the
validated `{b,e}`/`{g,i}`-family pad25 checkerboard decode.

`cb_common.py` already defines a keyed columnar transposition
(`keyed_columnar`) sized to each target's exact, non-arbitrary factorization
-- `matrixsumlist` (13 letters, DBBI = 91 = 7x13 exactly) for DBBI, and the
concatenation of the page's own two decimal-transport control strings,
`lastwordsbeforearchichoicethispassword` (38 letters, FAED = 570 = 15x38
exactly), for FAED -- with a comment flagging it as never combined with the
checkerboard model. Grepping the whole repository confirms it: `KEYCOL_DBBI`,
`KEYCOL_FAED`, and `KEYCOL_TRANSFORM_KINDS` have no import site anywhere
outside `cb_common.py` itself; only a bare round-trip self-test exists.

This is a different mechanism from the already-closed Phase 321, which
transposes the *post-checkerboard-decode* 0-24 code-slot sequence using 11
individual `CORE_ALPHABET_SEEDS` keywords (`lastwordsbeforearchichoice` and
`thispassword` included separately, never concatenated). Here the
transposition runs on the *raw* a-i character stream, before any checkerboard
decode, using the one key each target's length exactly factors by.

Closed candidate set: for each target, 2 key spellings (forward, reversed) x
2 `keyed_columnar` directions (encrypt, decrypt) = 4 pre-decode streams (8
total). Each stream is decoded through this project's already-validated
checkerboard path -- exactly `matrixsum_permutation_sweep.py`'s escape pairs
(`TARGET_ESCAPES`) and alphabet seeds (`CORE_ALPHABET_SEEDS`), no new
alphabets or escapes invented -- plus its direct-byte path, and every
candidate is checked through the real AES oracle. A shuffle-based null model
(shuffle the real symbols, rerun the identical pipeline) gates the checkerboard
path's best text-score against multiple-comparisons artifacts, the same
discipline Phase 321 needed for the sibling post-decode transposition.

Usage:
    python3 tools/gsmg/phase514_predecode_keycol_checkerboard_audit.py --self-test
    python3 tools/gsmg/phase514_predecode_keycol_checkerboard_audit.py --shuffle-trials 200
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cb_common import (  # noqa: E402
    KEYCOL_DBBI,
    KEYCOL_FAED,
    aes_try_open,
    answer_forms,
    decode_9ary,
    keyed_columnar,
    keystr_forms,
    pad25,
)
from data import DBBI, FAED  # noqa: E402
from matrixsum_permutation_sweep import (  # noqa: E402
    CORE_ALPHABET_SEEDS,
    TARGET_ESCAPES,
    direct_byte_bodies,
    text_score,
    try_aes_bytes,
    try_aes_text,
)

TARGETS = {"dbbi": (DBBI, KEYCOL_DBBI), "faed": (FAED, KEYCOL_FAED)}
KEY_SPELLINGS = ("forward", "reversed")
DIRECTIONS = ("encrypt", "decrypt")


def stream_variants(target_name, ciphertext):
    """The 4 closed pre-decode keyed-columnar streams for one target."""
    _, key = TARGETS[target_name]
    variants = []
    for spelling in KEY_SPELLINGS:
        spelled_key = key if spelling == "forward" else key[::-1]
        for direction in DIRECTIONS:
            stream = keyed_columnar(ciphertext, spelled_key, direction)
            variants.append((f"{spelling}/{direction}", stream))
    return variants


def checkerboard_candidates(target_name, stream, variant_label):
    candidates = []
    for e1, e2 in TARGET_ESCAPES[target_name]:
        for seed in CORE_ALPHABET_SEEDS:
            alphabet = pad25(seed)
            if len(alphabet) != 25:
                continue
            answer = decode_9ary(stream, alphabet, e1, e2)
            if "?" in answer:
                continue
            candidates.append({
                "variant": variant_label,
                "escapes": f"{e1}{e2}",
                "seed": seed,
                "text": answer,
                "score": round(text_score(answer), 6),
            })
    return candidates


def pipeline_best_score(target_name, ciphertext):
    """Max checkerboard text_score across the full closed cell -- the
    shuffle-gate's max-statistic, no AES (too slow to run per null trial)."""
    best = -1.0
    for variant_label, stream in stream_variants(target_name, ciphertext):
        for e1, e2 in TARGET_ESCAPES[target_name]:
            for seed in CORE_ALPHABET_SEEDS:
                alphabet = pad25(seed)
                if len(alphabet) != 25:
                    continue
                answer = decode_9ary(stream, alphabet, e1, e2)
                if "?" in answer:
                    continue
                best = max(best, text_score(answer))
    return best


def shuffle_gate(target_name, ciphertext, trials, seed=0):
    real_best = pipeline_best_score(target_name, ciphertext)
    rng = random.Random(seed)
    symbols = list(ciphertext)
    null_scores = []
    for _ in range(trials):
        rng.shuffle(symbols)
        null_scores.append(pipeline_best_score(target_name, "".join(symbols)))
    beat_or_matched = sum(1 for score in null_scores if score >= real_best)
    return {
        "real_best_score": round(real_best, 6),
        "trials": trials,
        "null_mean": round(sum(null_scores) / trials, 6) if trials else 0.0,
        "null_max": round(max(null_scores), 6) if null_scores else 0.0,
        "beat_or_matched": beat_or_matched,
        "p_value": round(beat_or_matched / trials, 6) if trials else 1.0,
    }


def audit(shuffle_trials=200, run_aes=True):
    if len(DBBI) != 91 or len(FAED) != 570:
        raise AssertionError("DBBI/FAED source lengths changed")
    if KEYCOL_DBBI != "matrixsumlist" or KEYCOL_FAED != "lastwordsbeforearchichoicethispassword":
        raise AssertionError("cb_common keyed-columnar keys changed")

    report = {}
    for target_name, (ciphertext, key) in TARGETS.items():
        tested = set()
        checkerboard = []
        direct_hits = []
        checkerboard_hits = []
        variants = stream_variants(target_name, ciphertext)
        for variant_label, stream in variants:
            checkerboard.extend(checkerboard_candidates(target_name, stream, variant_label))
            for decoder, body in direct_byte_bodies(stream):
                if run_aes:
                    for hit in try_aes_bytes(body, tested):
                        direct_hits.append({**hit, "variant": variant_label, "path": decoder})

        if run_aes:
            for candidate in checkerboard:
                for hit in try_aes_text(candidate["text"], tested):
                    checkerboard_hits.append({**hit, "variant": candidate["variant"],
                                               "escapes": candidate["escapes"], "seed": candidate["seed"]})

        ranked = sorted(checkerboard, key=lambda c: c["score"], reverse=True)
        report[target_name] = {
            "key": key,
            "variant_count": len(variants),
            "checkerboard_candidate_count": len(checkerboard),
            "top_candidates": ranked[:5],
            "checkerboard_aes_hits": checkerboard_hits,
            "direct_byte_aes_hits": direct_hits,
            "aes_keystrings_tested": len(tested),
            "shuffle_gate": shuffle_gate(target_name, ciphertext, shuffle_trials),
        }
    report["total_aes_hits"] = sum(
        len(report[t]["checkerboard_aes_hits"]) + len(report[t]["direct_byte_aes_hits"])
        for t in TARGETS
    )
    return report


def self_test():
    for target_name, (ciphertext, key) in TARGETS.items():
        variants = stream_variants(target_name, ciphertext)
        assert len(variants) == 4
        labels = [label for label, _ in variants]
        assert labels == ["forward/encrypt", "forward/decrypt", "reversed/encrypt", "reversed/decrypt"]
        for _, stream in variants:
            assert len(stream) == len(ciphertext)
            assert set(stream) <= set("abcdefghi")
        # round trip sanity: encrypt then decrypt with the same key spelling
        # must recover the original stream exactly
        for spelling in KEY_SPELLINGS:
            spelled_key = key if spelling == "forward" else key[::-1]
            encrypted = keyed_columnar(ciphertext, spelled_key, "encrypt")
            assert keyed_columnar(encrypted, spelled_key, "decrypt") == ciphertext

    report = audit(shuffle_trials=20, run_aes=False)
    assert report["dbbi"]["variant_count"] == 4
    assert report["faed"]["variant_count"] == 4
    # Upper bound is 4 variants x escape orders x len(CORE_ALPHABET_SEEDS); some
    # cells are legitimately skipped when a variant's transposed stream leaves a
    # dangling trailing escape (decode_9ary emits "?" and checkerboard_candidates
    # drops it) -- same skip rule matrixsum_permutation_sweep.py already uses.
    assert report["dbbi"]["checkerboard_candidate_count"] == 88
    assert report["dbbi"]["checkerboard_candidate_count"] <= 4 * 2 * len(CORE_ALPHABET_SEEDS)
    assert report["faed"]["checkerboard_candidate_count"] == 110
    assert report["faed"]["checkerboard_candidate_count"] <= 4 * 4 * len(CORE_ALPHABET_SEEDS)
    print("[*] self-test OK: 8 pre-decode keyed-columnar streams round-trip; "
          "closed checkerboard cell sizes match declared candidate set")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--shuffle-trials", type=int, default=200)
    parser.add_argument("--no-aes", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit(shuffle_trials=args.shuffle_trials, run_aes=not args.no_aes)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    for target_name in TARGETS:
        section = report[target_name]
        gate = section["shuffle_gate"]
        print(f"[*] {target_name.upper()} key={section['key']!r}")
        print(f"    checkerboard candidates: {section['checkerboard_candidate_count']}")
        for candidate in section["top_candidates"][:3]:
            print(f"      score={candidate['score']:.1f} {candidate['variant']} "
                  f"escapes={candidate['escapes']} seed={candidate['seed'][:20]} "
                  f"text={candidate['text'][:60]}")
        print(f"    shuffle gate: real_best={gate['real_best_score']:.1f} "
              f"null_mean={gate['null_mean']:.1f} null_max={gate['null_max']:.1f} "
              f"beat_or_matched={gate['beat_or_matched']}/{gate['trials']} "
              f"p={gate['p_value']:.4f}")
        print(f"    AES hits: checkerboard={len(section['checkerboard_aes_hits'])} "
              f"direct_byte={len(section['direct_byte_aes_hits'])}")
    print(f"[*] total AES hits: {report['total_aes_hits']}")


if __name__ == "__main__":
    main()
