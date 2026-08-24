#!/usr/bin/env python3
"""Phase 387: reproduce and calibrate message 66722's KMODEST checkpoint.

The fixed construction starts from Phase 386's independently reproduced Bifid
decode of FAED.  Its only ``Z`` is at zero-based position 97, so the prefix
through that character has length 98 = 2 * 7 * 7.  Split that prefix into
digraphs, take the second character of each pair, lay the resulting 49 letters
as 7 rows of 7, and reverse row 1.  The result is ``KMODEST``.

The script deliberately separates that reproducible checkpoint from message
66722's acknowledged post-hoc step (delete K, then reinterpret K's Bifid-grid
coordinates 2,5 as B,E to obtain ``BE MODEST``), which is not promoted here.

Two bounded controls are reported:

* fixed-window shuffles preserve FAED's exact multiset, retain the DBBI-derived
  Bifid square and period, and apply the now-frozen 98-character/second-rail/
  reverse-first-7 extraction;
* first-Z geometry shuffles instead require the first Z itself to end a prefix
  of length ``2*n*n`` before applying the same second-rail/reversed-first-row
  rule.  This measures how selective the visually attractive 98=2*7*7 gate is.

English-likeness is scored with the project's frozen quadgram table.  The
Monte Carlo is diagnostic, not a proof of authorial intent: the extraction was
noticed after BTCSEED, Z, and the 7x7 geometry were already visible.
"""

import argparse
import json
import math
import random
from pathlib import Path

from data import FAED
from phase386_btcseed_bifid_faed_decode_audit import (
    audit as btcseed_audit,
    bifid_decrypt,
    build_grid,
)
from data import DBBI


ORIGIN_MESSAGE_ID = 66722
TARGET = "KMODEST"
DEFAULT_TRIALS = 100_000
DEFAULT_SEED = 0x387
QUADGRAM_PATH = Path(__file__).resolve().parent / "data_files" / "english_quadgrams.txt"


def load_quadgrams(path=QUADGRAM_PATH):
    counts = {}
    total = 0
    for line in path.read_text(encoding="ascii").splitlines():
        gram, raw_count = line.split()
        count = int(raw_count)
        counts[gram] = count
        total += count
    floor = math.log10(0.01 / total)
    logs = {gram: math.log10(count / total) for gram, count in counts.items()}
    return logs, floor


def quadgram_score(text, logs, floor):
    text = text.upper()
    return sum(logs.get(text[i : i + 4], floor) for i in range(len(text) - 3))


def quadgram_mean(text, logs, floor):
    grams = len(text) - 3
    return quadgram_score(text, logs, floor) / grams if grams > 0 else float("-inf")


def fixed_candidate(decoded):
    """Frozen after observation: prefix 98, second digraph rail, row 1 reversed."""
    prefix = decoded[:98]
    assert len(prefix) == 98
    second_rail = prefix[1::2]
    assert len(second_rail) == 49
    return second_rail[:7][::-1]


def first_z_geometry_candidate(decoded):
    """Return the structurally gated candidate, or None when the gate fails."""
    try:
        prefix_length = decoded.index("Z") + 1
    except ValueError:
        return None
    if prefix_length % 2:
        return None
    cells = prefix_length // 2
    side = math.isqrt(cells)
    if side < 4 or side * side != cells:
        return None
    second_rail = decoded[1:prefix_length:2]
    return second_rail[:side][::-1]


def observed_report():
    phase386 = btcseed_audit()
    decoded = phase386["decoded"]
    prefix = decoded[:98]
    second_rail = prefix[1::2]
    rows = tuple(second_rail[i : i + 7] for i in range(0, 49, 7))
    return {
        "decoded_prefix": prefix,
        "first_z_index": decoded.index("Z"),
        "prefix_length_through_z": decoded.index("Z") + 1,
        "second_rail": second_rail,
        "second_rail_rows": rows,
        "candidate": fixed_candidate(decoded),
        "geometry_candidate": first_z_geometry_candidate(decoded),
    }


def monte_carlo(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    _keyword, grid, pos = build_grid(DBBI[:13])
    logs, floor = load_quadgrams()
    target_score = quadgram_score(TARGET, logs, floor)
    target_mean = quadgram_mean(TARGET, logs, floor)
    rng = random.Random(seed)
    chars = list(FAED)

    fixed_score_ge = 0
    fixed_exact = 0
    geometry_eligible = 0
    geometry_side_histogram = {}
    geometry_side7 = 0
    geometry_side7_score_ge = 0
    geometry_score_ge = 0
    geometry_exact = 0

    for _ in range(trials):
        rng.shuffle(chars)
        decoded = bifid_decrypt(chars, pos, grid)

        candidate = fixed_candidate(decoded)
        fixed_exact += candidate == TARGET
        fixed_score_ge += quadgram_score(candidate, logs, floor) >= target_score

        geometry_candidate = first_z_geometry_candidate(decoded)
        if geometry_candidate is None:
            continue
        geometry_eligible += 1
        side = len(geometry_candidate)
        geometry_side_histogram[side] = geometry_side_histogram.get(side, 0) + 1
        geometry_side7 += side == 7
        geometry_exact += geometry_candidate == TARGET
        if len(geometry_candidate) >= 4:
            geometry_score_ge += (
                quadgram_mean(geometry_candidate, logs, floor) >= target_mean
            )
        if side == 7:
            geometry_side7_score_ge += (
                quadgram_score(geometry_candidate, logs, floor) >= target_score
            )

    return {
        "trials": trials,
        "seed": seed,
        "target_quadgram_score": target_score,
        "target_quadgram_mean": target_mean,
        "fixed_exact": fixed_exact,
        "fixed_score_ge_target": fixed_score_ge,
        "fixed_score_ge_rate": fixed_score_ge / trials,
        "geometry_eligible": geometry_eligible,
        "geometry_eligible_rate": geometry_eligible / trials,
        "geometry_side_histogram": geometry_side_histogram,
        "geometry_side7": geometry_side7,
        "geometry_side7_rate": geometry_side7 / trials,
        "geometry_side7_score_ge_target": geometry_side7_score_ge,
        "geometry_side7_score_ge_rate_unconditional": geometry_side7_score_ge / trials,
        "geometry_side7_score_ge_rate_conditional": (
            geometry_side7_score_ge / geometry_side7 if geometry_side7 else None
        ),
        "geometry_exact": geometry_exact,
        "geometry_score_ge_target": geometry_score_ge,
        "geometry_score_ge_rate_unconditional": geometry_score_ge / trials,
        "geometry_score_ge_rate_conditional": (
            geometry_score_ge / geometry_eligible if geometry_eligible else None
        ),
    }


def audit(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    return {"observed": observed_report(), "control": monte_carlo(trials, seed)}


def self_test():
    observed = observed_report()
    assert observed["first_z_index"] == 97
    assert observed["prefix_length_through_z"] == 98
    assert observed["second_rail"].startswith("TSEDOMK")
    assert observed["candidate"] == TARGET
    assert observed["geometry_candidate"] == TARGET
    assert observed["second_rail_rows"] == (
        "TSEDOMK",
        "AHSHKDS",
        "KVXPOHR",
        "IIQEDBN",
        "SDPGPNN",
        "SSGDLNM",
        "UUQADLZ",
    )

    # Small deterministic smoke control; the substantive run uses --trials.
    control = monte_carlo(trials=100, seed=DEFAULT_SEED)
    assert control["trials"] == 100
    assert 0 <= control["geometry_eligible"] <= 100
    print(
        "[*] self-test OK: first Z at 97 -> 98 chars -> 49 digraphs -> "
        "second rail 7x7; reversed first row is KMODEST"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(audit(args.trials, args.seed), indent=2))


if __name__ == "__main__":
    main()
