"""Phase 478 matcher.

Usage: phase478_run_matcher.py <oracle_lock_json> <manifest_jsonl> <report_json>

This is the ONLY script in Phase 478 that ever computes a candidate's
SHA-256 digest or equality pattern -- see the protocol's two-lock design
and the manifest schema's "No sha256 field" note. It must never be run
against the real manifest before the oracle lock (pinning the manifest's
own SHA-256, the frozen DBBI pattern, and this script's own SHA-256) has
been issued; `run()` enforces this by refusing to proceed unless the
manifest file's hash matches the one named in the supplied oracle lock.

For each `eligible: true` manifest entry: SHA256(bytes).hexdigest(),
compute its equality pattern with the identical `equality_pattern`
function frozen in phase478_common.py, and compare character-for-character
to DBBI's frozen `{b,g}` pattern. Per the protocol's stop rule, only a full
64-position exact match counts as positive; there is no threshold and no
top-N reporting beyond the single best-matching-position count, tracked
purely for descriptive purposes.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase478_common import DBBI_PATTERN, equality_pattern  # noqa: E402


class MatcherError(Exception):
    pass


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _matching_positions(a: str, b: str) -> int:
    return sum(1 for x, y in zip(a, b) if x == y)


def iter_eligible_manifest_entries(manifest_path):
    with open(manifest_path) as f:
        for line in f:
            entry = json.loads(line)
            if entry["eligible"]:
                yield entry


def score_entry(entry, target_pattern: str = DBBI_PATTERN, pattern_fn=equality_pattern):
    """Returns (is_match, matching_positions, pattern) for one manifest
    entry. Never mutates or re-normalizes `bytes_b64` beyond decoding it --
    per the protocol, no additional normalization axis is introduced here."""
    raw_bytes = base64.b64decode(entry["bytes_b64"])
    digest_hex = hashlib.sha256(raw_bytes).hexdigest()
    pattern = pattern_fn(list(digest_hex))
    is_match = pattern == target_pattern
    return is_match, _matching_positions(pattern, target_pattern), pattern


def run_matcher(manifest_path, target_pattern: str = DBBI_PATTERN):
    """Scores every eligible manifest entry exactly once. Returns a report
    dict: whether any exact match was found (and which entry, if so), the
    total eligible count scored, and the single best (highest matching-
    position) miss for descriptive purposes only -- never used as a
    criterion."""
    scored = 0
    hit = None
    best = None  # (matching_positions, entry, pattern)

    for entry in iter_eligible_manifest_entries(manifest_path):
        is_match, positions, pattern = score_entry(entry, target_pattern)
        scored += 1
        if best is None or positions > best[0]:
            best = (positions, entry, pattern)
        if is_match:
            hit = (entry, pattern)
            break  # exact-match stop rule: no need to keep scoring past a hit

    report = {
        "eligible_scored": scored,
        "target_pattern": target_pattern,
        "match_found": hit is not None,
    }
    if hit is not None:
        entry, pattern = hit
        report["match"] = {
            "source_file": entry["source_file"],
            "bytes_b64": entry["bytes_b64"],
            "phase": entry["phase"],
            "construction_label": entry["construction_label"],
            "call_sites": entry["call_sites"],
            "pattern": pattern,
        }
    if best is not None:
        positions, entry, pattern = best
        report["best_miss"] = {
            "matching_positions": positions,
            "source_file": entry["source_file"],
            "bytes_b64": entry["bytes_b64"],
            "phase": entry["phase"],
            "pattern": pattern,
        }
    return report


def verify_oracle_lock(oracle_lock: dict, manifest_path, matcher_script_path) -> None:
    actual_manifest_sha = sha256_file(manifest_path)
    if actual_manifest_sha != oracle_lock["manifest_sha256"]:
        raise MatcherError(
            "manifest file does not match the oracle lock's pinned manifest_sha256: "
            f"locked {oracle_lock['manifest_sha256']}, actual {actual_manifest_sha}"
        )
    if oracle_lock["dbbi_pattern"] != DBBI_PATTERN:
        raise MatcherError(
            "oracle lock's pinned dbbi_pattern does not match phase478_common.DBBI_PATTERN "
            f"-- locked {oracle_lock['dbbi_pattern']}, current {DBBI_PATTERN}"
        )
    actual_matcher_sha = sha256_file(matcher_script_path)
    if actual_matcher_sha != oracle_lock["matcher_script_sha256"]:
        raise MatcherError(
            "this matcher script's own SHA-256 does not match the oracle lock's pinned "
            f"matcher_script_sha256: locked {oracle_lock['matcher_script_sha256']}, "
            f"actual {actual_matcher_sha}"
        )


def run(oracle_lock_path, manifest_path, report_path) -> dict:
    with open(oracle_lock_path) as f:
        oracle_lock = json.load(f)
    verify_oracle_lock(oracle_lock, manifest_path, Path(__file__))
    report = run_matcher(manifest_path)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    return report


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    oracle_lock_path, manifest_path, report_path = sys.argv[1:4]
    report = run(oracle_lock_path, manifest_path, report_path)
    print(json.dumps({k: v for k, v in report.items() if k != "best_miss"}, indent=2))
    if report["match_found"]:
        print("MATCH FOUND -- see", report_path)
    else:
        print("No match. Best miss: see", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
