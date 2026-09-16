#!/usr/bin/env python3
"""Phase 510B: held-out authentic-plaintext gate for the Phase-510A lexicon."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import phase510a_closed_vocabulary_manifest as phase510a


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 510B Held-Out Vocabulary Signal Protocol.md")
LOCK = SCRIPT_DIR / "phase510b_execution_lock.json"
RESULT = SCRIPT_DIR / "phase510b_result.json"
EVALUATION_SOURCES = (
    "phase2_solved_plaintext",
    "phase3_literal_plaintext",
    "phase32_literal_plaintext",
)
MIN_COVERAGE = 0.05
NULL_TRIALS = 200
NULL_SEED = 0x510B11


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PCG32:
    def __init__(self, seed: int):
        self.state = 0
        self.inc = 0xDA3E39CB94B95BDB
        self.next_u32()
        self.state = (self.state + seed) & ((1 << 64) - 1)
        self.next_u32()

    def next_u32(self) -> int:
        old = self.state
        self.state = (old * 6364136223846793005 + (self.inc | 1)) & ((1 << 64) - 1)
        xorshifted = ((old >> 18) ^ old) >> 27
        rotation = old >> 59
        return ((xorshifted >> rotation) |
                (xorshifted << ((-rotation) & 31))) & 0xFFFFFFFF

    def randbelow(self, bound: int) -> int:
        if bound <= 0:
            raise ValueError("bound must be positive")
        threshold = ((1 << 32) - bound) % bound
        while True:
            value = self.next_u32()
            if value >= threshold:
                return value % bound

    def shuffle(self, values: list[str]) -> None:
        for index in range(len(values) - 1, 0, -1):
            other = self.randbelow(index + 1)
            values[index], values[other] = values[other], values[index]


def derive_seed(base: int, fixture_index: int, trial_index: int) -> int:
    payload = f"{base}:{fixture_index}:{trial_index}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def normalized(value: bytes) -> str:
    return "".join(chr(byte + 32) if 65 <= byte <= 90 else chr(byte)
                   for byte in value if 65 <= byte <= 90 or 97 <= byte <= 122)


def heldout_terms(manifest: dict, source_id: str) -> list[tuple[str, int]]:
    return [(row["term"], row["proposed_length_weight"])
            for row in manifest["terms"]
            if any(other != source_id for other in row["source_ids"])]


def score(text: str, terms: list[tuple[str, int]]) -> dict:
    by_first = {}
    for term, weight in terms:
        by_first.setdefault(term[0], []).append((term, weight))
    n = len(text)
    best = [0] * (n + 1)
    choices = [None] * n
    for index in range(n - 1, -1, -1):
        best[index] = best[index + 1]
        for term, weight in by_first.get(text[index], ()):
            end = index + len(term)
            value = weight + (best[end] if end <= n else -10**18)
            if end <= n and text.startswith(term, index) and value > best[index]:
                best[index] = value
                choices[index] = (term, weight, end)
    matches = []
    index = 0
    while index < n:
        choice = choices[index]
        if choice is not None and choice[1] + best[choice[2]] == best[index]:
            term, weight, end = choice
            matches.append({"start": index, "end": end,
                            "term": term, "weight": weight})
            index = end
        else:
            index += 1
    matched = sum(item["end"] - item["start"] for item in matches)
    return {
        "raw_weight": best[0],
        "normalized_weight": best[0] / n if n else 0.0,
        "matched_characters": matched,
        "matched_character_coverage": matched / n if n else 0.0,
        "matches": matches,
    }


def lock_payload() -> dict:
    manifest = phase510a.validate_manifest()
    regions = phase510a.literal_regions()
    return {
        "phase": "510B",
        "status": "locked_before_heldout_scoring",
        "files_sha256": {
            "protocol": sha(PROTOCOL),
            "runner": sha(Path(__file__)),
            "phase510a_builder": sha(Path(phase510a.__file__)),
            "phase510a_manifest": sha(phase510a.MANIFEST),
        },
        "evaluation_sources": list(EVALUATION_SOURCES),
        "evaluation_region_sha256": {
            source: hashlib.sha256(regions[source]).hexdigest()
            for source in EVALUATION_SOURCES},
        "term_count": manifest["term_count"],
        "scorer": "maximum-weight non-overlapping exact terms; weight=(length-4)^2; normalize by letters",
        "minimum_coverage": MIN_COVERAGE,
        "null": "exact normalized-letter-multiset PCG32 Fisher-Yates shuffle",
        "null_trials_if_coverage_passes": NULL_TRIALS,
        "null_seed": NULL_SEED,
        "ties_are_exceedances": True,
        "gate": "all three fixtures coverage>=0.05 and 0/200 null exceedances",
        "faed_scored": False,
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-510B execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-510B execution lock mismatch")
    return actual


def atomic_json(path: Path, value: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise


def run() -> dict:
    verify_lock()
    if RESULT.exists():
        raise FileExistsError("refusing to repeat Phase-510B")
    manifest = phase510a.validate_manifest()
    regions = phase510a.literal_regions()
    fixtures = []
    coverage_failed = False
    for fixture_index, source_id in enumerate(EVALUATION_SOURCES):
        text = normalized(regions[source_id])
        terms = heldout_terms(manifest, source_id)
        real = score(text, terms)
        row = {"source_id": source_id, "normalized_length": len(text),
               "heldout_term_count": len(terms), "real": real,
               "coverage_gate_passed": real["matched_character_coverage"] >= MIN_COVERAGE,
               "null_trials": [], "null_exceedances": None}
        if not row["coverage_gate_passed"]:
            coverage_failed = True
        fixtures.append(row)
    if not coverage_failed:
        for fixture_index, row in enumerate(fixtures):
            text = normalized(regions[row["source_id"]])
            terms = heldout_terms(manifest, row["source_id"])
            for trial_index in range(NULL_TRIALS):
                chars = list(text)
                PCG32(derive_seed(NULL_SEED, fixture_index, trial_index)).shuffle(chars)
                control = score("".join(chars), terms)
                row["null_trials"].append({
                    "trial_index": trial_index,
                    "normalized_weight": control["normalized_weight"],
                    "tie_inclusive_exceedance": (
                        control["normalized_weight"] >= row["real"]["normalized_weight"]),
                })
            row["null_exceedances"] = sum(
                trial["tie_inclusive_exceedance"] for trial in row["null_trials"])
    passed = (not coverage_failed and
              all(row["null_exceedances"] == 0 for row in fixtures))
    result = {
        "phase": "510B", "status": "heldout_signal_gate_complete",
        "execution_lock_sha256": sha(LOCK), "faed_scored": False,
        "fixtures": fixtures, "coverage_gate_passed_all": not coverage_failed,
        "null_stage_executed": not coverage_failed,
        "gate_passed": passed,
        "verdict": ("licenses_known_order_ceiling" if passed
                    else "exact_vocabulary_objective_stops_before_checkerboard_integration"),
    }
    atomic_json(RESULT, result)
    return result


def self_test() -> dict:
    simple = score("xxalphayybetazz", [("alpha", 1), ("beta", 2)])
    if [row["term"] for row in simple["matches"]] != ["alpha", "beta"]:
        raise AssertionError("non-overlap scorer failed")
    overlap = score("abcdef", [("abcde", 1), ("bcdef", 5)])
    if [row["term"] for row in overlap["matches"]] != ["bcdef"]:
        raise AssertionError("weighted overlap choice failed")
    chars = list("aaabbbccc")
    PCG32(derive_seed(NULL_SEED, 0, 0)).shuffle(chars)
    if sorted(chars) != sorted("aaabbbccc") or "".join(chars) == "aaabbbccc":
        raise AssertionError("shuffle control failed")
    return {"self_test": "pass", "fixtures": 3,
            "minimum_coverage": MIN_COVERAGE, "conditional_nulls": 600}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test: value = self_test()
    elif args.print_lock: value = lock_payload()
    elif args.verify_lock: value = verify_lock()
    else: value = run()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
