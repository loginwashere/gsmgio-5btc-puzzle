#!/usr/bin/env python3
"""Audit a proposed Phase-One "opposites attract" reading against DBBI/FAED.

The archived Stage-1 song identifies its first stanza as "Phase one" and
states "The seed is planted when opposites attract." Separately, the final
title contains the exact nested decomposition ``SAL[PHASEI]ON``: the inner
text is PHASE I and the outer text is SALON. No creator source establishes
that this decomposition intentionally points back to the earlier stanza.

This audit tests one bounded consequence at the visible native-symbol level:
whether DBBI has an exceptional contiguous alignment with FAED under the
fixed nine-symbol complement a<->i, b<->h, c<->g, d<->f, e<->e. Every FAED
offset and both orientations are included in the max statistic. The null
shuffles FAED's raw symbols while preserving its exact multiset and repeats
the complete offset/orientation search.

No cipher, password, AES oracle, resampling, folding, or alphabet keyword is
used. Identity alignment is reported only as a non-gating diagnostic.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402


TITLE = "SalPhaseIon"
INNER = "PhaseI"
OUTER = "Salon"
NINE = "abcdefghi"
MIRROR = str.maketrans(NINE, NINE[::-1])
EXPECTED_STANZA = (
    "Phase one\n"
    "The seed is planted when opposites attract\n"
    "Can you dig it?\n"
    "It takes the physical to create the physical"
)
CREATOR_ID = 6497
COMMUNITY_ID = 8069
DEFAULT_TRIALS = 20_000
DEFAULT_SEED = 20260728


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def evidence(export_dir=DEFAULT_EXPORT_DIR):
    export_dir = Path(export_dir)
    lyrics = (export_dir / "files" / "lyrics.txt").read_text(
        encoding="utf-8"
    )
    if EXPECTED_STANZA not in lyrics:
        raise AssertionError("the exact Phase-One stanza is missing")

    page_html = (
        export_dir / "files" / "GSMG Puzzle 1.html"
    ).read_text(encoding="utf-8", errors="replace")
    if 'action="https://gsmg.io/phase1verification"' not in page_html:
        raise AssertionError("the authenticated phase1verification action is missing")

    payload = json.loads(
        (export_dir / "result.json").read_text(encoding="utf-8")
    )
    messages = {message["id"]: message for message in payload["messages"]}
    creator_text = flatten_text(messages[CREATOR_ID].get("text", ""))
    community_text = flatten_text(messages[COMMUNITY_ID].get("text", ""))
    if (
        "first stage was cracked" not in creator_text
        or "progress in salphation" not in creator_text
    ):
        raise AssertionError(
            "creator message 6497 no longer contrasts the first stage and salphation"
        )
    if community_text != "sal phase ion, salphase i on, s alpha sion ...":
        raise AssertionError("community message 8069 changed")

    inner_start = TITLE.index(INNER)
    outer = TITLE[:inner_start] + TITLE[inner_start + len(INNER):]
    if outer != OUTER:
        raise AssertionError("SAL[PHASEI]ON decomposition failed")

    return {
        "title": TITLE,
        "nested_rendering": "SAL[PHASE I]ON",
        "inner": INNER,
        "outer": outer,
        "lyrics_stanza": EXPECTED_STANZA,
        "phase1verification": True,
        "creator_stage_contrast_message_id": CREATOR_ID,
        "community_prior_observation_id": COMMUNITY_ID,
        "creator_confirmation_of_title_split": False,
        "creator_confirmation_of_phase_one_back_reference": False,
    }


def encode_symbols(text):
    lookup = np.full(256, 255, dtype=np.uint8)
    for value, symbol in enumerate(NINE.encode("ascii")):
        lookup[symbol] = value
    encoded = lookup[np.frombuffer(text.encode("ascii"), dtype=np.uint8)]
    if np.any(encoded == 255):
        raise ValueError("stream contains symbols outside a-i")
    return encoded


def alignment_scores(sequence, target):
    windows = np.lib.stride_tricks.sliding_window_view(sequence, len(target))
    forward = np.count_nonzero(windows == target, axis=1)
    reverse = np.count_nonzero(windows == target[::-1], axis=1)
    return forward, reverse


def best_alignments(sequence, target):
    forward, reverse = alignment_scores(sequence, target)
    maximum = int(max(forward.max(), reverse.max()))
    matches = []
    for orientation, scores in (("forward", forward), ("reverse", reverse)):
        for offset in np.flatnonzero(scores == maximum):
            matches.append(
                {
                    "orientation": orientation,
                    "offset": int(offset),
                    "score": maximum,
                }
            )
    return maximum, matches


def selected_text(sequence, target, orientation, offset):
    oriented_target = target if orientation == "forward" else target[::-1]
    window = sequence[offset:offset + len(oriented_target)]
    indices = np.flatnonzero(window == oriented_target).tolist()
    plaintext = "".join(VALIDATION_ANSWER[index] for index in indices)
    return {
        "matching_indices_zero_based": indices,
        "aligned_plaintext_selection": plaintext,
    }


def calibrate(sequence, target, real_score, trials, seed):
    rng = np.random.default_rng(seed)
    maxima = np.empty(trials, dtype=np.uint16)
    for trial in range(trials):
        shuffled = rng.permutation(sequence)
        maxima[trial] = best_alignments(shuffled, target)[0]
    exceedances = int(np.count_nonzero(maxima >= real_score))
    return {
        "trials": trials,
        "seed": seed,
        "exceedances": exceedances,
        "empirical_p": (exceedances + 1) / (trials + 1),
        "null_mean": float(maxima.mean()),
        "null_median": float(np.median(maxima)),
        "null_q95": float(np.quantile(maxima, 0.95)),
        "null_max": int(maxima.max()),
    }


def audit(export_dir=DEFAULT_EXPORT_DIR, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    evidence_result = evidence(export_dir)
    dbbi = encode_symbols(DBBI)
    faed = encode_symbols(FAED)
    mirrored_dbbi = 8 - dbbi

    real_score, locations = best_alignments(faed, mirrored_dbbi)
    identity_score, identity_locations = best_alignments(faed, dbbi)
    for location in locations:
        location.update(
            selected_text(
                faed,
                mirrored_dbbi,
                location["orientation"],
                location["offset"],
            )
        )

    calibration = calibrate(faed, mirrored_dbbi, real_score, trials, seed)
    return {
        "evidence": evidence_result,
        "family": {
            "target": "DBBI mirror9",
            "searched_stream": "every contiguous 91-symbol FAED window",
            "orientations": ["forward", "reverse"],
            "windows_per_orientation": len(FAED) - len(DBBI) + 1,
            "null": "shuffle raw FAED symbols, preserving exact multiset",
        },
        "real": {
            "complement_max_score": real_score,
            "complement_fraction": real_score / len(DBBI),
            "complement_locations": locations,
            "identity_diagnostic_max_score": identity_score,
            "identity_diagnostic_locations": identity_locations,
        },
        "calibration": calibration,
        "verdict": (
            "The title has a mechanically exact PHASE I substring/outer-SALON "
            "decomposition, while the earlier authenticated Phase-One lyric "
            "supplies 'opposites attract'. No creator source connects those "
            "separate facts; message 6497 instead contrasts the already-cracked "
            "first stage with later salphation. Under the one fixed native-"
            "symbol consequence tested here, DBBI's best contiguous complement "
            "alignment with FAED is not exceptional if empirical_p >= 0.005. "
            "The broader semantic relationship remains open."
        ),
    }


def self_test():
    if TITLE[3:9] != INNER or TITLE[:3] + TITLE[9:] != OUTER:
        raise AssertionError("title decomposition self-test failed")
    if any(
        ord(symbol) + ord(symbol.translate(MIRROR)) != ord("a") + ord("i")
        for symbol in NINE
    ):
        raise AssertionError("mirror mapping is not a fixed complement")
    if any(symbol.translate(MIRROR).translate(MIRROR) != symbol for symbol in NINE):
        raise AssertionError("mirror mapping is not involutive")

    synthetic_dbbi = encode_symbols("abcdefghi")
    synthetic_faed = encode_symbols("aaaihgfedcbaaaa")
    score, locations = best_alignments(synthetic_faed, 8 - synthetic_dbbi)
    if score != 9:
        raise AssertionError("synthetic planted complement was not recovered")
    if not any(
        location["orientation"] == "forward" and location["offset"] == 3
        for location in locations
    ):
        raise AssertionError("synthetic complement offset was not recovered")

    tiny = calibrate(
        synthetic_faed,
        8 - synthetic_dbbi,
        real_score=9,
        trials=20,
        seed=7,
    )
    if tiny["trials"] != 20 or not 0 < tiny["empirical_p"] <= 1:
        raise AssertionError("calibration self-test failed")
    print("[*] self-test OK")


def print_report(report):
    print("[*] exact title decomposition: SAL[PHASE I]ON -> outer SALON")
    print("[*] authenticated Phase-One line: The seed is planted when opposites attract")
    print(
        "[*] complement family: "
        f"{report['family']['windows_per_orientation']} offsets x "
        f"{len(report['family']['orientations'])} orientations"
    )
    real = report["real"]
    print(
        f"[*] real complement max: {real['complement_max_score']}/"
        f"{len(DBBI)} ({real['complement_fraction']:.3%})"
    )
    for location in real["complement_locations"]:
        print(
            f"    {location['orientation']} offset={location['offset']} "
            f"selection={location['aligned_plaintext_selection']}"
        )
    print(
        "[*] identity diagnostic max: "
        f"{real['identity_diagnostic_max_score']}/{len(DBBI)}"
    )
    calibration = report["calibration"]
    print(
        f"[*] null ({calibration['trials']} trials, seed={calibration['seed']}): "
        f"mean={calibration['null_mean']:.3f}, "
        f"median={calibration['null_median']:.1f}, "
        f"q95={calibration['null_q95']:.1f}, "
        f"max={calibration['null_max']}, "
        f"exceedances={calibration['exceedances']}, "
        f"p={calibration['empirical_p']:.6f}"
    )
    print(f"[*] verdict: {report['verdict']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.trials <= 0:
        parser.error("--trials must be positive")
    if args.self_test:
        self_test()
        return
    report = audit(args.export_dir, args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
