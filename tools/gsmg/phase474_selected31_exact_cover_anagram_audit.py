#!/usr/bin/env python3
"""Phase 474: bounded exact-cover anagram audit of the selected 31 letters.

No phrase ordering, password generation, decryption, FAED use, or oracle call.
See the frozen Phase-474 protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np

from data import VALIDATION_ANSWER
from denis_prime_extraction_audit import TARGET as RECONSTRUCTED_TARGET
from transition_evidence_recovery_audit import MANUAL_ANAGRAMS, normalize_letters

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
RESULT_PATH = SCRIPT_DIR / "phase474_result.json"
BIP39_PATH = ROOT / "wordlists" / "bip39" / "english.txt"
CHAT_WORDS_PATH = ROOT / "wordlists" / "gsmg" / "chat_mined_words.txt"

TARGET = "ncsyangcahiriasogaleafayanestve"
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
MAX_WORDS = 8
MAX_SERIALIZED_BAGS = 200
N_CONTROLS = 200
RNG_SEED = 474
ALPHA = 0.005
DISCOVERY_RE = re.compile(r"[a-z]{3,12}")
INF = MAX_WORDS + 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def vector(text: str) -> tuple[int, ...]:
    counts = Counter(text)
    if set(counts) - set(ALPHABET):
        raise ValueError(f"non-lowercase-ascii input: {text!r}")
    return tuple(counts.get(letter, 0) for letter in ALPHABET)


def fits(word_vector: tuple[int, ...], state: tuple[int, ...]) -> bool:
    return all(w <= s for w, s in zip(word_vector, state))


def subtract(state: tuple[int, ...], word_vector: tuple[int, ...]) -> tuple[int, ...]:
    if not fits(word_vector, state):
        raise ValueError("word does not fit remaining multiset")
    return tuple(s - w for s, w in zip(state, word_vector))


def load_independent_words() -> tuple[str, ...]:
    words = {
        line.strip().lower()
        for line in BIP39_PATH.read_text(encoding="utf-8").splitlines()
        if re.fullmatch(r"[a-z]+", line.strip().lower())
    }
    words.update(("a", "i"))
    words.discard(TARGET)
    return tuple(sorted(words))


def load_discovery_words() -> tuple[str, ...]:
    words = set(load_independent_words())
    for line in CHAT_WORDS_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        word = line.strip().lower()
        if DISCOVERY_RE.fullmatch(word):
            words.add(word)
    words.discard(TARGET)
    return tuple(sorted(words))


def target_candidates(words: tuple[str, ...], text: str) -> tuple[tuple[str, tuple[int, ...]], ...]:
    state = vector(text)
    rows = []
    for word in words:
        word_vector = vector(word)
        if fits(word_vector, state):
            rows.append((word, word_vector))
    return tuple(rows)


class ExactCoverSolver:
    def __init__(self, words: tuple[str, ...], text: str):
        self.target_state = vector(text)
        self.candidates = target_candidates(words, text)
        self.by_letter = tuple(
            tuple(i for i, (_word, counts) in enumerate(self.candidates) if counts[j])
            for j in range(26)
        )

    def _branches(self, state: tuple[int, ...]) -> tuple[int, ...]:
        options = []
        for letter, remaining in enumerate(state):
            if not remaining:
                continue
            fitting = tuple(
                index
                for index in self.by_letter[letter]
                if fits(self.candidates[index][1], state)
            )
            if not fitting:
                return ()
            options.append(fitting)
        return min(options, key=lambda row: (len(row), row))

    def minimum_words(self) -> int | None:
        groups: dict[tuple[int, ...], list[str]] = {}
        for word, counts in self.candidates:
            groups.setdefault(counts, []).append(word)
        signatures = sorted(groups)
        for words in groups.values():
            words.sort()

        target = self.target_state
        bags: set[tuple[str, ...]] = set()
        if target in groups:
            for word in groups[target][:MAX_SERIALIZED_BAGS]:
                bags.add((word,))
            self._minimum_bags = sorted(bags)
            return 1

        pair_witness: dict[tuple[int, ...], tuple[str, str]] = {}
        for left_index, left in enumerate(signatures):
            for right in signatures[left_index:]:
                combined = tuple(a + b for a, b in zip(left, right))
                if not fits(combined, target):
                    continue
                bag = tuple(sorted((groups[left][0], groups[right][0])))
                previous = pair_witness.get(combined)
                if previous is None or bag < previous:
                    pair_witness[combined] = bag

        if target in pair_witness:
            self._minimum_bags = [pair_witness[target]]
            return 2

        for signature in signatures:
            remainder = subtract(target, signature)
            pair = pair_witness.get(remainder)
            if pair is not None:
                bags.add(tuple(sorted((groups[signature][0], *pair))))
                if len(bags) >= MAX_SERIALIZED_BAGS:
                    break
        if bags:
            self._minimum_bags = sorted(bags)
            return 3

        for signature, pair in sorted(pair_witness.items()):
            remainder = subtract(target, signature)
            other = pair_witness.get(remainder)
            if other is not None:
                bags.add(tuple(sorted((*pair, *other))))
                if len(bags) >= MAX_SERIALIZED_BAGS:
                    break
        if bags:
            self._minimum_bags = sorted(bags)
            return 4

        zero = (0,) * 26

        @lru_cache(maxsize=None)
        def find_cover(state: tuple[int, ...], slots: int) -> tuple[str, ...] | None:
            if state == zero:
                return ()
            if not slots:
                return None
            branches = sorted(
                self._branches(state),
                key=lambda index: (-len(self.candidates[index][0]), self.candidates[index][0]),
            )
            for index in branches:
                word, word_vector = self.candidates[index]
                suffix = find_cover(subtract(state, word_vector), slots - 1)
                if suffix is not None:
                    return tuple(sorted((word, *suffix)))
            return None

        for word_count in range(5, MAX_WORDS + 1):
            bag = find_cover(target, word_count)
            if bag is not None:
                self._minimum_bags = [bag]
                return word_count
        self._minimum_bags = []
        return None

    def minimum_bags(self, minimum: int | None) -> list[list[str]]:
        if minimum is None:
            return []
        return [list(bag) for bag in self._minimum_bags[:MAX_SERIALIZED_BAGS]]


def solve_text(words: tuple[str, ...], text: str, include_bags: bool) -> dict:
    solver = ExactCoverSolver(words, text)
    minimum = solver.minimum_words()
    bags = solver.minimum_bags(minimum) if include_bags else []
    for bag in bags:
        if Counter("".join(bag)) != Counter(text):
            raise AssertionError("serialized bag is not an exact cover")
    return {
        "candidate_word_count": len(solver.candidates),
        "minimum_words": minimum,
        "minimum_bags_serialized": bags,
        "minimum_bags_serialized_count": len(bags),
        "minimum_bags_serialization_cap": MAX_SERIALIZED_BAGS,
    }


def manual_phrase_checks(discovery_words: tuple[str, ...]) -> list[dict]:
    lexicon = set(discovery_words)
    rows = []
    for phrase in MANUAL_ANAGRAMS:
        tokens = tuple(phrase.lower().split())
        rows.append({
            "phrase": phrase,
            "tokens": list(tokens),
            "exact_multiset": Counter(normalize_letters(phrase)) == Counter(TARGET),
            "all_tokens_in_discovery_lexicon": all(token in lexicon for token in tokens),
        })
    return rows


def build_report() -> dict:
    if RECONSTRUCTED_TARGET != TARGET or len(TARGET) != 31:
        raise AssertionError("canonical selected-31 target changed")
    if len(VALIDATION_ANSWER) != 91 or not VALIDATION_ANSWER.isalpha():
        raise AssertionError("canonical 91-character plaintext changed")

    independent_words = load_independent_words()
    discovery_words = load_discovery_words()
    real_independent = solve_text(independent_words, TARGET, include_bags=True)
    real_discovery = solve_text(discovery_words, TARGET, include_bags=True)

    rng = np.random.default_rng(RNG_SEED)
    controls = []
    for index in range(N_CONTROLS):
        positions = np.sort(rng.choice(len(VALIDATION_ANSWER), size=len(TARGET), replace=False))
        text = "".join(VALIDATION_ANSWER[int(position)].lower() for position in positions)
        result = solve_text(independent_words, text, include_bags=False)
        controls.append({
            "index": index,
            "positions": [int(position) for position in positions],
            "text_sha256": hashlib.sha256(text.encode("ascii")).hexdigest(),
            "minimum_words": result["minimum_words"],
            "candidate_word_count": result["candidate_word_count"],
        })

    target_score = real_independent["minimum_words"]
    target_numeric = INF if target_score is None else target_score
    control_numeric = [INF if row["minimum_words"] is None else row["minimum_words"] for row in controls]
    exceedances = sum(score <= target_numeric for score in control_numeric)
    p_value = (1 + exceedances) / (N_CONTROLS + 1)
    finite_controls = [score for score in control_numeric if score != INF]
    gates = {
        "independent_exact_cover_within_cap": target_score is not None,
        "p_below_alpha": p_value < ALPHA,
        "strictly_better_than_every_control": all(target_numeric < score for score in control_numeric),
    }
    gates["lead"] = all(gates.values())

    return {
        "phase": 474,
        "target": TARGET,
        "target_sorted_letters": "".join(sorted(TARGET)),
        "target_sha256": hashlib.sha256(TARGET.encode("ascii")).hexdigest(),
        "lexicons": {
            "independent": {
                "path": str(BIP39_PATH.relative_to(ROOT)),
                "file_sha256": sha256_file(BIP39_PATH),
                "word_count_with_a_i": len(independent_words),
            },
            "discovery_contaminated": {
                "path": str(CHAT_WORDS_PATH.relative_to(ROOT)),
                "file_sha256": sha256_file(CHAT_WORDS_PATH),
                "word_count_after_rule": len(discovery_words),
            },
        },
        "grammar": {
            "minimum_words": 1,
            "maximum_words": MAX_WORDS,
            "repetition_allowed": True,
            "exact_full_multiset": True,
            "phrase_order_scored": False,
        },
        "real_independent": real_independent,
        "real_discovery": real_discovery,
        "historical_manual_phrases": manual_phrase_checks(discovery_words),
        "calibration": {
            "rng_seed": RNG_SEED,
            "control_count": N_CONTROLS,
            "control_rule": "31 positions sampled without replacement from VALIDATION_ANSWER",
            "finite_control_count": len(finite_controls),
            "control_minimum_words_histogram": {
                str(score): control_numeric.count(score) for score in sorted(set(control_numeric))
            },
            "target_minimum_words": target_score,
            "controls_as_or_better": exceedances,
            "p_lower_plus_one": p_value,
            "alpha": ALPHA,
            "controls": controls,
        },
        "decision_gates": gates,
        "disposition": "lexical_compressibility_lead" if gates["lead"] else "bounded_negative",
        "phrase_selected": False,
        "password_materials_generated": 0,
        "faed_uses": 0,
        "decryptions_attempted": 0,
        "oracle_calls": 0,
    }


def structural_self_test() -> None:
    assert vector("aabc")[:3] == (2, 1, 1)
    assert subtract(vector("aabc"), vector("ab")) == vector("ac")
    words = ("a", "ab", "bc", "cab")
    one = ExactCoverSolver(words, "abc")
    assert one.minimum_words() == 1
    assert one.minimum_bags(1) == [["cab"]]
    two = ExactCoverSolver(("ab", "bc"), "abbc")
    assert two.minimum_words() == 2
    assert two.minimum_bags(2) == [["ab", "bc"]]
    repeat = ExactCoverSolver(("ab",), "aabb")
    assert repeat.minimum_words() == 2
    assert repeat.minimum_bags(2) == [["ab", "ab"]]
    impossible = ExactCoverSolver(("ab",), "abc")
    assert impossible.minimum_words() is None
    assert Counter(normalize_letters(MANUAL_ANAGRAMS[0])) == Counter(TARGET)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--structural-only", action="store_true")
    args = parser.parse_args()
    structural_self_test()
    if args.structural_only:
        print("[*] Phase 474 structural self-test OK")
        return
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "independent": report["real_independent"],
        "discovery": report["real_discovery"],
        "calibration": {
            key: value for key, value in report["calibration"].items() if key != "controls"
        },
        "decision_gates": report["decision_gates"],
        "disposition": report["disposition"],
    }, indent=2))


if __name__ == "__main__":
    main()
