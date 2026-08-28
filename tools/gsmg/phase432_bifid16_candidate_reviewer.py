#!/usr/bin/env python3
"""CPU-only semantic reviewer for live Phase-430 checkpoint shortlists."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

import phase431_bifid16_equivalence_class_audit as phase431
from phase426_btcseed_heldout_continuation_structure_audit import longest_repeated_substring


TARGET = "BTCSEED"
TOTAL_RANKS = math.factorial(16)
DEFAULT_DICTIONARY = Path("/usr/share/dict/words")
DEFAULT_TRIALS = 200
DEFAULT_REVIEW_LIMIT = 25
SEED = 0x432
EXPECTED_FINGERPRINT = {
    "version": 1,
    "family": "bifid_16factorial_prefix_dependency_fixed_dynamic_coordinates_lexicographic;range_start=0",
    "range_end_exclusive": TOTAL_RANKS,
    "faed_sha256": phase431.FAED_SHA256,
    "decoded_cells_sha256": "b0bf2115116590f790cff303467413073c66a48843f2a0d7de95011545a8d85a",
    "quadgram_sha256": "b461953d6ad3b5e1f0f07c133102b7656a205529cb8697a8ecda8d45311f7a55",
    "kernel_sha256": "7649eb12be187fa09ebfc76c18144e6e3227a9611c046e28deecdefa3fbac5b0",
    "driver_sha256": "a8cbbda5b7cdacb90486bc52e0f3e4901a10c93401c62ab8638570cacd4b97d3",
    "cuda_arch": "sm_120",
    "score": "tail[7:];mean_log10_english_quadgram;f32_accumulation",
}
KEYWORDS = (
    "ADDRESS", "ARCHITECT", "BITCOIN", "BLOCK", "BLUE", "CHOICE",
    "CIPHER", "COIN", "FAED", "FEFE", "KEY", "MATRIX", "PASSWORD",
    "PRIME", "PRIVATE", "PUBLIC", "SALVATION", "SATOSHI", "SEED",
    "SPIRAL", "WALLET", "YELLOW", "YINYANG",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_checkpoint(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()  # one read of the atomically-renamed checkpoint
    state = json.loads(raw)
    if state.get("fingerprint") != EXPECTED_FINGERPRINT:
        raise ValueError("Phase-430 checkpoint fingerprint mismatch")
    if not 0 <= state.get("next_rank", -1) <= TOTAL_RANKS:
        raise ValueError("checkpoint next_rank outside 16! domain")
    if not state.get("block_winners"):
        raise ValueError("checkpoint has no retained winners")
    return state, raw


def square_for_rank(rank: int) -> str:
    if not 0 <= rank < TOTAL_RANKS:
        raise ValueError("winner rank outside 16! domain")
    available = list(phase431.FREE_SYMBOLS)
    permutation = []
    for position in range(16):
        factor = math.factorial(15 - position)
        selected, rank = divmod(rank, factor)
        permutation.append(available.pop(selected))
    square = list(phase431.BASE_SQUARE)
    for cell, symbol in zip(phase431.FREE_POSITIONS, permutation):
        square[cell] = symbol
    return "".join(square)


def decode_rank(rank: int) -> tuple[str, str]:
    square = square_for_rank(rank)
    decoded = phase431.decode_square(square)
    if not decoded.startswith(TARGET):
        raise ValueError(f"rank {rank} violated sealed BTCSEED prefix")
    return square, decoded


def load_dictionary(path: Path) -> tuple[set[str], str]:
    raw = path.read_bytes()
    words = {
        line.strip().upper()
        for line in raw.decode("utf-8", errors="replace").splitlines()
        if line.strip().isalpha() and 4 <= len(line.strip()) <= 12
    }
    if not words:
        raise ValueError("dictionary is empty")
    return words, sha256(raw)


def dictionary_hits(text: str, words: set[str], minimum: int = 5) -> list[dict]:
    hits = []
    for start in range(len(text)):
        for length in range(minimum, min(12, len(text) - start) + 1):
            word = text[start:start + length]
            if word in words:
                hits.append({"start": start, "word": word})
    return hits


def segment(text: str, words: set[str]) -> dict:
    # Dynamic programming: maximize sum(length^2), then covered characters.
    n = len(text)
    best = [(0, 0, []) for _ in range(n + 1)]
    for end in range(1, n + 1):
        best[end] = best[end - 1]
        for length in range(4, min(12, end) + 1):
            word = text[end - length:end]
            if word not in words:
                continue
            prior = best[end - length]
            candidate = (prior[0] + length * length, prior[1] + length,
                         prior[2] + [{"start": end - length, "word": word}])
            if candidate[:2] > best[end][:2]:
                best[end] = candidate
    score, covered, tokens = best[n]
    return {"score": score, "covered_characters": covered,
            "covered_fraction": covered / max(1, n), "tokens": tokens}


def index_of_coincidence(text: str) -> float:
    counts = Counter(text)
    n = len(text)
    return sum(value * (value - 1) for value in counts.values()) / max(1, n * (n - 1))


def lag_profile(text: str) -> list[dict]:
    rows = []
    for lag in range(1, min(40, len(text) - 1) + 1):
        matches = sum(a == b for a, b in zip(text, text[lag:]))
        rows.append({"lag": lag, "matches": matches, "fraction": matches / (len(text) - lag)})
    return sorted(rows, key=lambda row: (-row["fraction"], row["lag"]))[:5]


def repeated_ngrams(text: str) -> list[dict]:
    rows = []
    for length in range(4, 13):
        counts = Counter(text[i:i + length] for i in range(len(text) - length + 1))
        for gram, count in counts.items():
            if count > 1:
                rows.append({"ngram": gram, "length": length, "count": count})
    return sorted(rows, key=lambda row: (-row["length"], -row["count"], row["ngram"]))[:10]


def exact_keywords(text: str) -> list[dict]:
    return [{"keyword": word, "starts": [i for i in range(len(text)) if text.startswith(word, i)]}
            for word in KEYWORDS if word in text]


def calibrated_dictionary(text: str, words: set[str], trials: int, digest: str) -> dict:
    observed_hits = len(dictionary_hits(text, words))
    observed_segment = segment(text, words)
    seed = SEED ^ int(digest[:16], 16)
    rng = random.Random(seed)
    letters = list(text)
    null_hits, null_segments = [], []
    for _ in range(trials):
        rng.shuffle(letters)
        shuffled = "".join(letters)
        null_hits.append(len(dictionary_hits(shuffled, words)))
        null_segments.append(segment(shuffled, words)["score"])
    return {
        "trials": trials,
        "seed": seed,
        "substring_count": observed_hits,
        "substring_inclusive_p": (1 + sum(value >= observed_hits for value in null_hits)) / (trials + 1),
        "segmentation": observed_segment,
        "segmentation_inclusive_p": (1 + sum(value >= observed_segment["score"] for value in null_segments)) / (trials + 1),
        "null_substring_count": {"min": min(null_hits), "max": max(null_hits), "mean": sum(null_hits) / trials},
        "null_segmentation_score": {"min": min(null_segments), "max": max(null_segments), "mean": sum(null_segments) / trials},
    }


def collapse_winners(winners: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for winner in winners:
        rank, score = int(winner["rank"]), float(winner["score_total"])
        square, decoded = decode_rank(rank)
        digest = sha256(decoded.encode("ascii"))
        group = groups.setdefault(digest, {"decoded_sha256": digest, "decoded": decoded,
                                           "best_rank": rank, "best_score_total": score,
                                           "square": square, "member_ranks": []})
        if abs(score - group["best_score_total"]) > 1e-3:
            raise ValueError("identical decode has inconsistent GPU scores")
        group["member_ranks"].append(rank)
        if rank < group["best_rank"]:
            group["best_rank"], group["square"] = rank, square
    rows = list(groups.values())
    for row in rows:
        row["raw_member_count"] = len(row.pop("member_ranks"))
    return sorted(rows, key=lambda row: (-row["best_score_total"], row["best_rank"]))


def deltas(current: list[dict], previous: dict | None) -> dict | None:
    if previous is None:
        return None
    old = previous["distinct_candidates"]
    current_hashes = {row["decoded_sha256"] for row in current}
    old_hashes = {row["decoded_sha256"] for row in old}
    return {
        "leader_changed": current[0]["decoded_sha256"] != old[0]["decoded_sha256"],
        "leader_score_delta": current[0]["best_score_total"] - old[0]["best_score_total"],
        "new_decoded_sha256": sorted(current_hashes - old_hashes),
        "departed_decoded_sha256": sorted(old_hashes - current_hashes),
    }


def review(checkpoint: Path, dictionary_path: Path = DEFAULT_DICTIONARY,
           trials: int = DEFAULT_TRIALS, review_limit: int = DEFAULT_REVIEW_LIMIT,
           previous: dict | None = None) -> dict:
    if trials < 1 or review_limit < 1:
        raise ValueError("trials and review_limit must be positive")
    state, raw = load_checkpoint(checkpoint)
    words, dictionary_hash = load_dictionary(dictionary_path)
    collapsed = collapse_winners(state["block_winners"])
    for row in collapsed[:review_limit]:
        tail = row.pop("decoded")[len(TARGET):]
        digest = row["decoded_sha256"]
        row.update({
            "decoded_prefix_72": TARGET + tail[:65],
            "tail_sha256": sha256(tail.encode("ascii")),
            "dictionary_hits_5_to_12": dictionary_hits(tail, words),
            "dictionary_calibration": calibrated_dictionary(tail, words, trials, digest),
            "keyword_hits": exact_keywords(tail),
            "index_of_coincidence": index_of_coincidence(tail),
            "strongest_lags_1_to_40": lag_profile(tail),
            "longest_repeated_substring": longest_repeated_substring(tail),
            "strongest_repeated_ngrams": repeated_ngrams(tail),
        })
    # Remove full text from unreviewed rows too; hashes preserve identity.
    for row in collapsed[review_limit:]:
        row.pop("decoded")
    return {
        "phase": 432,
        "checkpoint": {"path": str(checkpoint), "snapshot_sha256": sha256(raw),
                       "next_rank": state["next_rank"],
                       "full_progress_fraction": state["next_rank"] / TOTAL_RANKS,
                       "retained_rows": len(state["block_winners"])},
        "protocol": {"tail_start": 7, "review_limit": review_limit, "trials": trials,
                     "dictionary_path": str(dictionary_path), "dictionary_sha256": dictionary_hash,
                     "keywords": list(KEYWORDS), "oracle_calls": 0,
                     "shortlist_is_exact_top_k": False},
        "summary": {"distinct_decodes": len(collapsed),
                    "duplicate_rows_collapsed": len(state["block_winners"]) - len(collapsed),
                    "reviewed_distinct_decodes": min(review_limit, len(collapsed))},
        "delta_from_previous": deltas(collapsed, previous),
        "distinct_candidates": collapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--review-limit", type=int, default=DEFAULT_REVIEW_LIMIT)
    args = parser.parse_args()
    previous = json.loads(args.previous.read_text()) if args.previous else None
    result = review(args.checkpoint, args.dictionary, args.trials, args.review_limit, previous)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({"checkpoint": result["checkpoint"], "summary": result["summary"],
                      "leader": result["distinct_candidates"][0],
                      "delta_from_previous": result["delta_from_previous"]}, indent=2))


if __name__ == "__main__":
    main()
