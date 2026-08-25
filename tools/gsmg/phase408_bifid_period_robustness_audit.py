#!/usr/bin/env python3
"""Phase 408: audits whether Phase 386's "btcseed" Bifid checkpoint
survives alternate block/period conventions, or exists only under the
single-570-character-block reading Phase 386 happened to use.

**Origin:** requested directly by the user as the right branch-level
gate before spending further effort on the BTCSEED/P91/Z brainstorm's
autokey/second-square idea-bank items (82-89): if the `BTCSEED` header,
the unique `Z@97`, and the `{B,C,D,E}`-vs-full-alphabet rail alternation
only ever appear under period 570, that checkpoint is weaker
justification for continuing downstream than if it survives independent
period choices. Phase 21's earlier period tests do not close this
question -- they used different decoded-code hypotheses and key
families, not Phase 386's exact raw-`FAED`/`DBBI`-keyed construction.

**Frozen contract (proposed and approved before this script was
written):**

- fixed inputs: ciphertext exactly `FAED` (570 letters), square exactly
  `DBIFHCEGAKLMNOPQRSTUVWXYZ` (Phase 386's `build_grid(DBBI[:13])`),
  Phase 386's row-column Bifid convention; no alternate squares,
  coordinate swaps, reversals, or second passes;
- block schedules: standard periods `7, 13, 49, 91, 98, 472, 570`
  (each period splits the 570-letter stream into fixed-size blocks,
  final block truncated to whatever remains -- the classical period-
  Bifid convention; period 472 naturally yields blocks `[472, 98]`, not
  `[472, 472]`, since only one full period fits before the 98-letter
  remainder); one custom Z-boundary schedule, blocks `[98, 472]`
  (deliberately the reverse split-point of period 472's `[472, 98]`,
  since the boundary position -- not just the multiset of block sizes
  -- determines the Bifid output);
- **8 labeled candidates, closed and enumerated before any output is
  inspected**;
- per-candidate report: SHA-256 and first 32 characters; longest common
  prefix with `BTCSEED`; whether it starts with or contains exact
  `BTCSEED`; count and positions of `Z`; whether `Z` is uniquely at
  index 97; even- and odd-position alphabets; whether the Phase 386
  alternation survives (even positions exactly `{B,C,D,E}`, odd
  positions drawn from -- a subset of, not necessarily covering --
  the complete keyed-square alphabet and not itself restricted to
  `{B,C,D,E}`); character agreement with the period-570 baseline over
  the full 570, the first 98, and the final 472;
- validation: a matching Bifid encryption implemented as the true
  inverse of Phase 386's `bifid_decrypt` (proven, not assumed);
  encrypt<->decrypt round trips required for every standard period and
  the custom schedule, both on the real `FAED` ciphertext and on a
  synthetic `BTCSEED`-prefixed plaintext (the latter also serves as the
  required planted positive for the `starts_with_btcseed` detector);
  period 570 asserted to reproduce Phase 386's `decoded` byte-for-byte;
- explicitly excluded: alternate squares, coordinate swaps, reversals,
  second Bifid passes, English/quadgram scoring, the blob oracle,
  keyword promotion of incidental words -- this phase audits the
  existing checkpoint's period-robustness, it does not search for a
  replacement plaintext;
- interpretation (not a promotion rule -- there is no key/address
  material to check here): if another schedule also starts with
  `BTCSEED`, the checkpoint has real period robustness; if only period
  570 does, it is classified full-block-convention-dependent -- not
  disproven, but weaker justification for continuing downstream.
  Preserving `BTCSEED`, unique `Z@97`, and the rail alternation together
  under an alternate schedule would be substantially stronger evidence
  than preserving the prefix alone.

**Method:** wrote this script, implementing `bifid_encrypt_block()` as
the algebraic inverse of Phase 386's own `bifid_decrypt()` (both derived
from the identical row/column-interleaving construction, verified by
round trip rather than assumed), and generalizing both to block/period
schedules via `bifid_decrypt_periodic()`/`bifid_encrypt_periodic()`,
which independently apply the single-block algorithm to consecutive
slices sized by each schedule. Reuses Phase 386's `build_grid()`,
`ALPHABET_NO_J`, `FAED`, `DBBI`, and `audit()` (for the period-570
baseline) verbatim -- no primitive re-derived.

**Result:** see `self_test()`'s asserted values for the exact pinned
8-candidate manifest, round-trip results, and the period-570-baseline
match.

**Disposition:** descriptive/structural audit only -- there is no
promotion rule to trigger here. The interpretation section of the
generated report states, per the contract above, whether the checkpoint
is period-robust or full-block-convention-dependent; that in turn
informs (but does not itself decide) whether idea-bank items 82-89 stay
parked.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    ALPHABET_NO_J,
    audit as btcseed_audit,
    build_grid,
)

STANDARD_PERIODS = (7, 13, 49, 91, 98, 472, 570)
CUSTOM_SCHEDULE = (98, 472)
TARGET_PREFIX = "BTCSEED"
CIPHERTEXT_LENGTH = 570


def normalize_letters(text):
    letters = [ch.upper() for ch in text if ch.isalpha()]
    return ["I" if ch == "J" else ch for ch in letters]


def block_sizes_for_period(period, total_length):
    full_blocks = total_length // period
    remainder = total_length % period
    sizes = [period] * full_blocks
    if remainder:
        sizes.append(remainder)
    return tuple(sizes)


def bifid_decrypt_block(letters, pos, grid):
    coords = []
    for ch in letters:
        r, c = pos[ch]
        coords.append(r)
        coords.append(c)
    n = len(letters)
    rows, cols = coords[:n], coords[n:]
    return "".join(grid[(r, c)] for r, c in zip(rows, cols))


def bifid_encrypt_block(letters, pos, grid):
    n = len(letters)
    rows, cols = [], []
    for ch in letters:
        r, c = pos[ch]
        rows.append(r)
        cols.append(c)
    combined = rows + cols
    return "".join(grid[(combined[2 * i], combined[2 * i + 1])] for i in range(n))


def bifid_decrypt_periodic(text, pos, grid, block_sizes):
    letters = normalize_letters(text)
    assert sum(block_sizes) == len(letters), (sum(block_sizes), len(letters))
    out = []
    idx = 0
    for size in block_sizes:
        out.append(bifid_decrypt_block(letters[idx : idx + size], pos, grid))
        idx += size
    return "".join(out)


def bifid_encrypt_periodic(text, pos, grid, block_sizes):
    letters = normalize_letters(text)
    assert sum(block_sizes) == len(letters), (sum(block_sizes), len(letters))
    out = []
    idx = 0
    for size in block_sizes:
        out.append(bifid_encrypt_block(letters[idx : idx + size], pos, grid))
        idx += size
    return "".join(out)


def longest_common_prefix_length(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def build_schedules():
    schedules = {f"period_{p}": block_sizes_for_period(p, CIPHERTEXT_LENGTH) for p in STANDARD_PERIODS}
    schedules["custom_98_472"] = CUSTOM_SCHEDULE
    return schedules


def agreement(a, b):
    matches = sum(1 for x, y in zip(a, b) if x == y)
    total = len(b)
    return {"matches": matches, "total": total, "fraction": matches / total if total else 0.0}


def score_candidate(label, block_sizes, pos, grid, baseline):
    decoded_text = bifid_decrypt_periodic(FAED, pos, grid, block_sizes)
    assert len(decoded_text) == CIPHERTEXT_LENGTH

    z_positions = [i for i, ch in enumerate(decoded_text) if ch == "Z"]
    even_alpha = set(decoded_text[0::2])
    odd_alpha = set(decoded_text[1::2])

    real_ciphertext_normalized = "".join(normalize_letters(FAED))
    roundtrip_encrypted = bifid_encrypt_periodic(decoded_text, pos, grid, block_sizes)
    roundtrip_matches_ciphertext = roundtrip_encrypted == real_ciphertext_normalized

    return {
        "label": label,
        "block_sizes": list(block_sizes),
        "decoded_text": decoded_text,
        "sha256_hex": hashlib.sha256(decoded_text.encode("utf-8")).hexdigest(),
        "first_32": decoded_text[:32],
        "lcp_with_btcseed": longest_common_prefix_length(decoded_text, TARGET_PREFIX),
        "starts_with_btcseed": decoded_text.startswith(TARGET_PREFIX),
        "contains_btcseed": TARGET_PREFIX in decoded_text,
        "z_count": len(z_positions),
        "z_positions": z_positions,
        "z_unique_at_97": z_positions == [97],
        "even_alphabet": "".join(sorted(even_alpha)),
        "odd_alphabet": "".join(sorted(odd_alpha)),
        "even_is_bcde": even_alpha == set("BCDE"),
        "odd_subset_of_full_alphabet": odd_alpha <= set(ALPHABET_NO_J),
        "odd_not_restricted_to_bcde": not (odd_alpha <= set("BCDE")),
        "agreement_full570": agreement(decoded_text, baseline),
        "agreement_first98": agreement(decoded_text[:98], baseline[:98]),
        "agreement_final472": agreement(decoded_text[98:], baseline[98:]),
        "roundtrip_matches_real_ciphertext": roundtrip_matches_ciphertext,
    }


def planted_btcseed_roundtrip_positives(pos, grid, schedules):
    """A synthetic BTCSEED-prefixed plaintext, encrypted then decrypted
    through the real periodic pipeline for every schedule -- proves the
    encrypt/decrypt pair is a true inverse under block segmentation and
    that starts_with_btcseed() actually fires when a real hit exists,
    not just that it runs."""
    synthetic_plaintext = (TARGET_PREFIX + "X" * (CIPHERTEXT_LENGTH - len(TARGET_PREFIX)))
    assert len(synthetic_plaintext) == CIPHERTEXT_LENGTH

    results = {}
    for label, block_sizes in schedules.items():
        ciphertext = bifid_encrypt_periodic(synthetic_plaintext, pos, grid, block_sizes)
        recovered = bifid_decrypt_periodic(ciphertext, pos, grid, block_sizes)
        results[label] = {
            "recovered_matches_plaintext": recovered == synthetic_plaintext,
            "recovered_starts_with_btcseed": recovered.startswith(TARGET_PREFIX),
        }
    return results


def audit():
    grid_keyword, grid, pos = build_grid(DBBI[:13])
    assert grid_keyword == "DBIFHCEGAKLMNOPQRSTUVWXYZ"

    baseline_report = btcseed_audit()
    baseline = baseline_report["decoded"]
    assert len(baseline) == CIPHERTEXT_LENGTH

    schedules = build_schedules()
    assert len(schedules) == 8

    candidates = {
        label: score_candidate(label, block_sizes, pos, grid, baseline)
        for label, block_sizes in schedules.items()
    }

    period_570_matches_baseline = candidates["period_570"]["decoded_text"] == baseline

    schedules_starting_with_btcseed = [
        label for label, entry in candidates.items() if entry["starts_with_btcseed"]
    ]
    schedules_containing_btcseed = [
        label for label, entry in candidates.items() if entry["contains_btcseed"]
    ]
    period_robust = any(label != "period_570" for label in schedules_starting_with_btcseed)

    return {
        "grid_keyword": grid_keyword,
        "ciphertext_length": len(FAED),
        "schedule_count": len(schedules),
        "schedules": {label: list(sizes) for label, sizes in schedules.items()},
        "candidates": candidates,
        "period_570_matches_baseline": period_570_matches_baseline,
        "schedules_starting_with_btcseed": schedules_starting_with_btcseed,
        "schedules_containing_btcseed": schedules_containing_btcseed,
        "period_robust": period_robust,
        "planted_btcseed_roundtrip_positives": planted_btcseed_roundtrip_positives(pos, grid, schedules),
    }


def self_test():
    report = audit()

    assert report["grid_keyword"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"
    assert report["ciphertext_length"] == 570
    assert report["schedule_count"] == 8
    assert set(report["candidates"].keys()) == {
        "period_7", "period_13", "period_49", "period_91", "period_98",
        "period_472", "period_570", "custom_98_472",
    }

    assert report["schedules"]["period_570"] == [570]
    assert report["schedules"]["period_472"] == [472, 98]
    assert report["schedules"]["custom_98_472"] == [98, 472]
    assert report["schedules"]["period_98"] == [98, 98, 98, 98, 98, 80]
    assert report["schedules"]["period_91"] == [91, 91, 91, 91, 91, 91, 24]
    assert report["schedules"]["period_49"] == [49] * 11 + [31]
    assert report["schedules"]["period_13"] == [13] * 43 + [11]
    assert report["schedules"]["period_7"] == [7] * 81 + [3]

    for label, entry in report["candidates"].items():
        assert len(entry["decoded_text"]) == 570, label
        assert entry["roundtrip_matches_real_ciphertext"] is True, label

    assert report["period_570_matches_baseline"] is True

    period_570 = report["candidates"]["period_570"]
    assert period_570["starts_with_btcseed"] is True
    assert period_570["z_unique_at_97"] is True
    assert period_570["even_is_bcde"] is True
    assert period_570["odd_not_restricted_to_bcde"] is True

    assert report["schedules_starting_with_btcseed"] == ["period_570"]
    assert report["period_robust"] is False

    planted = report["planted_btcseed_roundtrip_positives"]
    assert len(planted) == 8
    for label, result in planted.items():
        assert result["recovered_matches_plaintext"] is True, label
        assert result["recovered_starts_with_btcseed"] is True, label

    print(
        f"[*] self-test OK: encrypt/decrypt round trips hold on the real "
        f"FAED ciphertext and on the synthetic BTCSEED-prefixed "
        f"plaintext for all 8 schedules; period 570 reproduces Phase "
        f"386's decoded output byte-for-byte and is the only schedule "
        f"whose output starts with BTCSEED "
        f"({report['schedules_starting_with_btcseed']}); "
        f"period_robust={report['period_robust']} -- the checkpoint is "
        f"classified full-block-convention-dependent, not disproven"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
