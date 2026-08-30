#!/usr/bin/env python3
"""Phase 453 symbolic false-discovery calibration.

The four lanes reproduce the choice budgets frozen in the Phase 453 manifest.
Null populations finish before canonical observations are scored. Results
calibrate evidentiary weight only; no password, decryption, Bitcoin, network,
or language-model oracle is present.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import time
from collections import Counter
from pathlib import Path

import first_piece_ggn_distinctiveness_audit as ggn_audit
import first_piece_matrix_product_audit as ff67_audit
import first_piece_second_matrixsumlist_audit as kit_audit
import roman_rail_prime_sum_audit as roman_audit


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = SCRIPT_DIR / "phase453_symbolic_manifest.json"
RESULT_PATH = SCRIPT_DIR / "phase453_result.json"
EXPECTED_MANIFEST_SHA256 = "22365a0e343f251921b053230f0e1eb1e50cf7cf99f8a3051a47ad1a51ff63af"
CASE_IDS = ("S-KIT", "S-FF67", "S-GGN", "S-ROMAN")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    if sha256_path(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("Phase 453 manifest digest drifted")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if tuple(manifest["cases"]) != CASE_IDS:
        raise AssertionError("case order or scope drifted")
    for relative, expected in manifest["source_digests"].items():
        actual = sha256_path(ROOT / relative)
        if actual != expected:
            raise AssertionError(f"source digest drifted: {relative}")
    return manifest


def derived_seed(master_seed: int, case_id: str, variant: str) -> int:
    material = f"{master_seed}:{case_id}:{variant}".encode("ascii")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


def bip39_three_letter_words(manifest: dict) -> frozenset[str]:
    registry = manifest["endpoint_registries"]["word"]
    words = {
        line.strip().lower()
        for line in (ROOT / registry["path"]).read_text(encoding="utf-8").splitlines()
        if len(line.strip()) == registry["length"]
    }
    if "kit" not in words:
        raise AssertionError("pinned endpoint vocabulary no longer contains kit")
    return frozenset(words)


def a1z26(values: tuple[int, ...]) -> str | None:
    if not all(1 <= value <= 26 for value in values):
        return None
    return "".join(chr(96 + value) for value in values)


def kit_outputs(new_rows: tuple[int, int], old_rows: tuple[int, int]) -> tuple[str, ...]:
    outputs = []
    for ordered_new in (new_rows, tuple(reversed(new_rows))):
        for ordered_old in (old_rows, tuple(reversed(old_rows))):
            delta = (
                sum(new_rows) - sum(old_rows),
                ordered_new[0] - ordered_old[0],
                ordered_new[1] - ordered_old[1],
            )
            for values in (delta, tuple(reversed(delta))):
                text = a1z26(values)
                if text is not None:
                    outputs.append(text)
    return tuple(outputs)


def score_kit(new_rows, old_rows, words) -> tuple[int, tuple[str, ...]]:
    hits = tuple(sorted(set(kit_outputs(new_rows, old_rows)) & words))
    return int(bool(hits)), hits


def multiply(matrix, vector):
    return tuple(sum(value * coefficient for value, coefficient in zip(row, vector))
                 for row in matrix)


def orientations(matrix):
    top, bottom = matrix
    return (
        matrix,
        (tuple(reversed(top)), tuple(reversed(bottom))),
        (bottom, top),
        (tuple(reversed(bottom)), tuple(reversed(top))),
    )


def ascii_letter(value: int) -> bool:
    return 65 <= value <= 90 or 97 <= value <= 122


def printable(value: int) -> bool:
    return 32 <= value <= 126


def ff67_output_score(output: tuple[int, int]) -> int:
    if 255 in output and any(ascii_letter(v) for v in output if v != 255):
        return 2
    if all(0 <= v <= 255 for v in output) and any(printable(v) for v in output):
        return 1
    return 0


def score_ff67(digits: tuple[int, ...]) -> tuple[int, tuple[tuple[int, int], ...]]:
    matrix = (digits[:3], digits[3:])
    vector = (sum(digits), sum(digits[:3]), sum(digits[3:]))
    rows = tuple(
        multiply(oriented, ordered)
        for oriented in orientations(matrix)
        for ordered in itertools.permutations(vector)
    )
    best = max(map(ff67_output_score, rows))
    hits = tuple(sorted(set(row for row in rows if ff67_output_score(row) == best)))
    return best, hits


def extract_tuple(source: str, base: int) -> str:
    indices = (1, 4, 21)
    return "".join(source[index - base] for index in indices)


def ggn_text_score(text: str, counts: Counter) -> int:
    if len(text) != 3 or not (text[0] == text[1] != text[2]):
        return 0
    return 2 if counts[text[2]] == 1 else 1


def score_ggn(source: str) -> tuple[int, tuple[str, ...]]:
    counts = Counter(source)
    rows = (extract_tuple(source, 1), extract_tuple(source, 0))
    best = max(ggn_text_score(row, counts) for row in rows)
    hits = tuple(row for row in rows if ggn_text_score(row, counts) == best)
    return best, hits


def roman_score(tokens: tuple[str, str]) -> tuple[int, tuple[dict, ...]]:
    rows = tuple(
        roman_audit.evaluate_pair(blue, yellow, placement, fragment)
        for blue, yellow in itertools.permutations(tokens)
        for placement, fragment in roman_audit.title_contexts()
    )
    ordered = tuple(row for row in rows if row["ordered_target_match"])
    if ordered:
        return 2, ordered
    either = tuple(
        row for row in rows
        if {row["blue_value"], row["yellow_value"]} == {400, 401}
    )
    return (1, either) if either else (0, ())


def update_histogram(histogram, score, hits, example_limit=20):
    histogram["scores"][str(score)] += 1
    if hits and len(histogram["examples"][str(score)]) < example_limit:
        histogram["examples"][str(score)].append(hits)


def empty_histogram() -> dict:
    return {
        "scores": {"0": 0, "1": 0, "2": 0},
        "examples": {"0": [], "1": [], "2": []},
    }


def run_kit_null(manifest, trials, variant):
    words = bip39_three_letter_words(manifest)
    histogram = empty_histogram()
    if variant == "primary":
        rng = random.Random(derived_seed(manifest["master_seed"], "S-KIT", variant))
        objects = (
            ((rng.randint(1, 25), rng.randint(1, 25)),
             (rng.randint(1, 25), rng.randint(1, 25)))
            for _ in range(trials)
        )
    elif variant == "sensitivity":
        values = manifest["cases"]["S-KIT"]["sensitivity_null"]["values"]
        objects = ((order[:2], order[2:]) for order in itertools.permutations(values))
    else:
        raise ValueError(variant)
    count = 0
    for new_rows, old_rows in objects:
        score, hits = score_kit(tuple(new_rows), tuple(old_rows), words)
        update_histogram(histogram, score, hits)
        count += 1
    histogram["trials"] = count
    return histogram


def run_ff67_null(manifest, trials, variant):
    histogram = empty_histogram()
    if variant == "primary":
        rng = random.Random(derived_seed(manifest["master_seed"], "S-FF67", variant))
        objects = (tuple(rng.sample(range(10), 6)) for _ in range(trials))
    elif variant == "sensitivity":
        objects = itertools.permutations(range(10), 6)
    else:
        raise ValueError(variant)
    count = 0
    for digits in objects:
        score, hits = score_ff67(tuple(digits))
        update_histogram(histogram, score, hits)
        count += 1
    histogram["trials"] = count
    return histogram


def run_ggn_null(manifest, trials, variant):
    histogram = empty_histogram()
    source = manifest["cases"]["S-GGN"]["real_source"]["text"]
    if variant == "primary":
        rng = random.Random(derived_seed(manifest["master_seed"], "S-GGN", variant))

        def shuffled_sources():
            for _ in range(trials):
                values = list(source)
                rng.shuffle(values)
                yield "".join(values)

        objects = shuffled_sources()
        scorer = score_ggn
    elif variant == "sensitivity":
        counts = Counter(source)
        objects = (
            "".join(source[index] for index in positions)
            for positions in itertools.combinations(range(len(source)), 3)
        )

        def scorer(text):
            score = ggn_text_score(text, counts)
            return score, (text,) if score else ()
    else:
        raise ValueError(variant)
    count = 0
    for item in objects:
        score, hits = scorer(item)
        update_histogram(histogram, score, hits)
        count += 1
    histogram["trials"] = count
    return histogram


def empirical_roman_characters(manifest):
    tokens = manifest["cases"]["S-ROMAN"]["empirical_control"]["tokens"]
    characters = "".join(character for token in tokens
                         for character in token.upper() if "A" <= character <= "Z")
    if not characters:
        raise AssertionError("empty empirical Roman character population")
    return characters


def run_roman_null(manifest, trials, variant):
    histogram = empty_histogram()
    rng = random.Random(derived_seed(manifest["master_seed"], "S-ROMAN", variant))
    alphabet = (empirical_roman_characters(manifest)
                if variant == "primary" else "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for _ in range(trials):
        first = "".join(rng.choice(alphabet) for _ in range(4))
        second = "".join(rng.choice(alphabet) for _ in range(4))
        while second == first:
            second = "".join(rng.choice(alphabet) for _ in range(4))
        score, hits = roman_score((first, second))
        compact_hits = tuple(
            (
                row["blue_token"], row["yellow_token"], row["placement"],
                row["title_fragment"], row["blue_value"], row["yellow_value"],
            )
            for row in hits
        )
        update_histogram(histogram, score, compact_hits)
    histogram["trials"] = trials
    return histogram


NULL_RUNNERS = {
    "S-KIT": run_kit_null,
    "S-FF67": run_ff67_null,
    "S-GGN": run_ggn_null,
    "S-ROMAN": run_roman_null,
}


def score_real_cases(manifest):
    words = bip39_three_letter_words(manifest)
    kit = kit_audit.audit()
    ff67 = ff67_audit.audit()
    ggn = ggn_audit.audit()
    roman = roman_audit.audit()
    kit_score, kit_hits = score_kit(
        tuple(kit["source"]["shadow_matrixsumlist"][1:]),
        tuple(kit["source"]["prime_matrixsumlist"][1:]),
        words,
    )
    ff_score, ff_hits = score_ff67(tuple(ff67["source"]["digits"]))
    ggn_score, ggn_hits = score_ggn(ggn["source"])
    roman_value, roman_hits = roman_score(tuple(roman_audit.RAILS))
    results = {
        "S-KIT": {"score": kit_score, "hits": kit_hits},
        "S-FF67": {"score": ff_score, "hits": ff_hits},
        "S-GGN": {"score": ggn_score, "hits": ggn_hits,
                  "curve_narrative_calibrated": False},
        "S-ROMAN": {
            "score": roman_value,
            "hits": tuple(
                (row["blue_token"], row["yellow_token"], row["placement"],
                 row["title_fragment"], row["blue_value"], row["yellow_value"])
                for row in roman_hits
            ),
            "fefe_under_winning_rule": 100,
            "fitted_fefe": 73,
        },
    }
    for case_id, result in results.items():
        if result["score"] != manifest["cases"][case_id]["real_score"]:
            raise AssertionError(f"real score drifted for {case_id}")
    return results


def empirical_tail(histogram, threshold):
    extreme = sum(count for score, count in histogram["scores"].items()
                  if int(score) >= threshold)
    trials = histogram["trials"]
    probability = (extreme + 1) / (trials + 1)
    standard_error = math.sqrt(probability * (1 - probability) / (trials + 1))
    return {
        "extreme_count": extreme,
        "trials": trials,
        "p_plus_one": probability,
        "normal_95_interval": [
            max(0.0, probability - 1.96 * standard_error),
            min(1.0, probability + 1.96 * standard_error),
        ],
        "real_rank_best_is_1": extreme + 1,
    }


def holm_adjust(raw):
    ordered = sorted(raw, key=raw.get)
    adjusted = {}
    running = 0.0
    count = len(ordered)
    for index, case_id in enumerate(ordered):
        value = min(1.0, (count - index) * raw[case_id])
        running = max(running, value)
        adjusted[case_id] = running
    return adjusted


def controls(manifest):
    words = bip39_three_letter_words(manifest)
    kit_positive = score_kit((6, 8), (1, 1), words)
    if kit_positive[0] != 1 or "leg" not in kit_positive[1]:
        raise AssertionError("KIT-lane planted positive failed")
    if score_kit((1, 1), (1, 1), words)[0] != 0:
        raise AssertionError("KIT-lane planted no-hit failed")
    ff_positive = score_ff67((0, 1, 4, 3, 8, 7))
    if ff_positive[0] != 2 or (97, 255) not in ff_positive[1]:
        raise AssertionError("FF67-lane planted positive failed")
    if score_ff67((0, 1, 2, 3, 4, 5))[0] > 1:
        raise AssertionError("FF67-lane planted no-strong-hit failed")
    planted = list("ABCDEFGHIJKLMNOPQRSTUVWX")
    planted[3] = planted[0]
    ggn_positive = score_ggn("".join(planted))
    if ggn_positive[0] != 2:
        raise AssertionError("GGN-lane planted positive failed")
    roman_positive = roman_score(("DIBB", "DAEF"))
    if roman_positive[0] != 2:
        raise AssertionError("Roman-lane planted positive failed")
    if roman_score(("AAAA", "BBBB"))[0] != 0:
        raise AssertionError("Roman-lane planted no-hit failed")
    tie_score, tie_hits = score_kit((6, 8), (1, 1), words | {"gel"})
    if tie_score != 1 or len(tie_hits) < 2:
        raise AssertionError("tie-retention control failed")
    first = run_kit_null(manifest, 100, "primary")
    second = run_kit_null(manifest, 100, "primary")
    if first != second:
        raise AssertionError("determinism control failed")
    return {
        "kit_positive": {"score": kit_positive[0], "contains": "leg"},
        "ff67_positive": {"score": ff_positive[0], "contains": [97, 255]},
        "ggn_positive": {"score": ggn_positive[0]},
        "roman_positive": {"score": roman_positive[0]},
        "tie_retention": {"score": tie_score, "hit_count": len(tie_hits)},
        "no_hit_controls": "passed",
        "digest_controls": "passed",
        "determinism": "passed",
    }


def benchmark(manifest, trials):
    started = time.monotonic()
    summaries = {}
    for case_id in CASE_IDS:
        case_started = time.monotonic()
        NULL_RUNNERS[case_id](manifest, trials, "primary")
        summaries[case_id] = time.monotonic() - case_started
    return {
        "trials_per_case": trials,
        "case_seconds": summaries,
        "total_seconds": time.monotonic() - started,
        "real_cases_scored": False,
    }


def run(manifest):
    control_report = controls(manifest)
    nulls = {}
    for case_id in CASE_IDS:
        runner = NULL_RUNNERS[case_id]
        nulls[case_id] = {
            "primary": runner(
                manifest, manifest["trials_per_monte_carlo_null"], "primary"
            ),
            "sensitivity": runner(
                manifest, manifest["trials_per_monte_carlo_null"], "sensitivity"
            ),
        }
    real = score_real_cases(manifest)
    tails = {}
    raw_primary = {}
    for case_id in CASE_IDS:
        threshold = real[case_id]["score"]
        tails[case_id] = {
            variant: empirical_tail(histogram, threshold)
            for variant, histogram in nulls[case_id].items()
        }
        raw_primary[case_id] = tails[case_id]["primary"]["p_plus_one"]
    adjusted = holm_adjust(raw_primary)
    raw_sensitivity = {
        case_id: tails[case_id]["sensitivity"]["p_plus_one"]
        for case_id in CASE_IDS
    }
    adjusted_sensitivity = holm_adjust(raw_sensitivity)
    decisions = {}
    alpha = manifest["alpha"]
    for case_id in CASE_IDS:
        primary_significant = adjusted[case_id] < alpha
        sensitivity_significant = adjusted_sensitivity[case_id] < alpha
        if primary_significant != sensitivity_significant:
            state = "sensitive_to_null_design"
        elif primary_significant:
            state = "unusual_but_unselected"
        else:
            state = "common_under_matched_null"
        decisions[case_id] = {
            "state": state,
            "raw_primary_p": raw_primary[case_id],
            "holm_adjusted_primary_p": adjusted[case_id],
            "raw_sensitivity_p": raw_sensitivity[case_id],
            "holm_adjusted_sensitivity_p": adjusted_sensitivity[case_id],
            "gap_closed": False,
        }
    report = {
        "phase": 453,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "scope": "symbolic_lane_only",
        "nulls_completed_before_real_scoring": True,
        "controls": control_report,
        "null_distributions": nulls,
        "real_cases": real,
        "tails": tails,
        "decisions": decisions,
        "phase_level_disposition": "calibration_only_no_gap_closure",
        "oracle_run": False,
        "network_used": False,
        "password_materials_generated": 0,
    }
    RESULT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def self_test(manifest):
    control_report = controls(manifest)
    if set(control_report) != {
        "kit_positive", "ff67_positive", "ggn_positive", "roman_positive",
        "tie_retention", "no_hit_controls", "digest_controls", "determinism",
    }:
        raise AssertionError("control report shape drifted")
    if holm_adjust({"a": 0.01, "b": 0.03, "c": 0.20, "d": 0.50}) != {
        "a": 0.04, "b": 0.09, "c": 0.4, "d": 0.5,
    }:
        raise AssertionError("Holm correction drifted")
    print("[*] Phase 453 self-test OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--benchmark", type=int, metavar="TRIALS")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if sum((args.self_test, args.benchmark is not None, args.run)) != 1:
        parser.error("choose exactly one of --self-test, --benchmark, or --run")
    manifest = load_manifest()
    if args.self_test:
        self_test(manifest)
    elif args.benchmark is not None:
        if args.benchmark <= 0:
            parser.error("--benchmark must be positive")
        print(json.dumps(benchmark(manifest, args.benchmark), indent=2))
    else:
        report = run(manifest)
        print(json.dumps({
            "decisions": report["decisions"],
            "result_path": str(RESULT_PATH.relative_to(ROOT)),
            "disposition": report["phase_level_disposition"],
        }, indent=2))


if __name__ == "__main__":
    main()
