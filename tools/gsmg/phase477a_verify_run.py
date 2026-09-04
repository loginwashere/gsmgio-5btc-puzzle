#!/usr/bin/env python3
"""Phase 477A post-run consistency check.

The run driver records its parameters but does not enforce the execution
lock. This script is fail-closed: every expected value (trial count,
promotion bar, seeds, token length, retained cell set) is derived from the
locked manifest and the locked audit script itself -- never from a CLI
argument or a hardcoded default -- so the check cannot be relaxed by the
caller. It verifies that the real and null artifacts were produced under
the locked script/protocol/manifest, that the null set is exactly the
locked trial count with unique consecutive trial numbers and the identical
locked cell set as the real run, that budgets and seeds match the lock
chain, and it recomputes the tie-inclusive exceedance count and p-value.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SCRIPT_PATH = SCRIPT_DIR / "phase477a_token_columnar_transposition_audit.py"
LOCK_PATH = SCRIPT_DIR / "phase477a_execution_lock.json"
MANIFEST_PATH = SCRIPT_DIR / "phase477a_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(cond, msg, failures):
    if not cond:
        failures.append(msg)
    return cond


def load_locked_module(expected_hash: str):
    """Import the audit script only after its hash is confirmed to match
    the lock, so every constant read from it below is provably the frozen
    one that actually produced the real/null artifacts -- not whatever
    happens to be on disk."""
    if sha256(SCRIPT_PATH) != expected_hash:
        raise RuntimeError("audit script hash does not match the lock; refusing to trust its constants")
    spec = importlib.util.spec_from_file_location("phase477a_locked", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(pair: str) -> dict:
    failures = []
    lock = json.loads(LOCK_PATH.read_text())
    manifest = json.loads(MANIFEST_PATH.read_text())

    # 1. lock chain hashes still hold, for every file the verdict depends on.
    script_hash = sha256(SCRIPT_PATH)
    proto_hash = sha256(REPO_ROOT / manifest["protocol"]["path"])
    manifest_hash = sha256(MANIFEST_PATH)
    check(script_hash == lock["audit_script_sha256"] == manifest["audit_script"]["sha256"],
          "audit script hash differs from lock/manifest", failures)
    check(proto_hash == lock["protocol_sha256"] == manifest["protocol"]["sha256"],
          "protocol hash differs from lock/manifest", failures)
    check(manifest_hash == lock["manifest_sha256"], "manifest hash differs from lock", failures)
    for entry in manifest["pinned_inputs"] + manifest["power_records"]:
        check(sha256(REPO_ROOT / entry["path"]) == entry["sha256"], f"pinned input changed: {entry['path']}", failures)
    if failures:
        # Constants below are only trustworthy once the script hash check
        # above has passed; stop rather than import an unverified script.
        return {"pair": pair, "consistent": False, "promoted": False, "failures": failures}

    module = load_locked_module(lock["audit_script_sha256"])
    module.configure_pair(pair[0], pair[1])
    expected_length = module.L
    expected_seed_base = module.pair_seed(module.SEED_NULL)
    expected_real_seed = module.pair_seed(module.SEED_REAL)
    expected_trials = module.NULL_TRIALS
    promotion_p = module.PROMOTION_P
    expected_budget = module.BUDGET
    status_key = "holdout_cell_status" if pair == "gi" else "secondary_holdout_cell_status"
    expected_cells = sorted((w, d) for w, d, _status in manifest["power_gate"][status_key])

    # 2. artifacts, checked against the locked expectations above -- not
    # against each other, and not against any value the caller can supply.
    suffix = "" if pair == "gi" else "_he"
    real_path = SCRIPT_DIR / f"phase477a{suffix}_real.json"
    null_path = SCRIPT_DIR / f"phase477a{suffix}_null.json"
    real = json.loads(real_path.read_text())
    null = json.loads(null_path.read_text())
    real_artifact_hash = sha256(real_path)
    null_artifact_hash = sha256(null_path)

    check(real.get("pair") == pair, f"real artifact pair label is {real.get('pair')!r}, expected {pair!r}", failures)
    check(null.get("pair") == pair, f"null artifact pair label is {null.get('pair')!r}, expected {pair!r}", failures)
    check(real.get("length") == expected_length, "real artifact token length does not match the locked pair length", failures)
    check(null.get("length") == expected_length, "null artifact token length does not match the locked pair length", failures)
    check(real.get("seed") == expected_real_seed, "real artifact seed does not match the locked derivation", failures)
    check(null.get("seed_base") == expected_seed_base, "null artifact seed base does not match the locked derivation", failures)
    check(real.get("budget") == expected_budget, "real artifact budget differs from the locked budget", failures)
    check(null.get("budget") == expected_budget, "null artifact budget differs from the locked budget", failures)

    real_cells = sorted((c["width"], c["direction"]) for c in real["cells"])
    check(real_cells == expected_cells, "real cell set does not match the manifest's locked powered-cell list", failures)
    check(sorted(tuple(c) for c in real["cells_run"]) == real_cells, "real cells_run does not match cell results", failures)
    check(sorted(tuple(c) for c in null["cells_run"]) == real_cells, "null cells_run differs from the locked cell set", failures)

    # 3. trials: exactly the locked count, uniquely numbered 0..trials-1,
    # each covering exactly the locked cell set with a correctly-derived
    # per-trial seed and a self-consistent family_max.
    numbers = [t["trial"] for t in null["trials"]]
    check(len(numbers) == expected_trials, f"expected {expected_trials} locked trials, found {len(numbers)}", failures)
    check(numbers == list(range(expected_trials)), "trial numbers are not exactly 0..trials-1 with no gaps or duplicates", failures)
    for t in null["trials"]:
        cells = sorted((c["width"], c["direction"]) for c in t["cells"])
        check(cells == expected_cells, f"trial {t['trial']} cell set differs from the locked cell set", failures)
        check(abs(max(c["normalised"] for c in t["cells"]) - t["family_max"]) < 1e-12,
              f"trial {t['trial']} family_max is not the max of its own cells", failures)

    # 4. real family max and tie-inclusive exceedances, on the locked trial
    # count and promotion bar only.
    real_max = max(c["normalised"] for c in real["cells"])
    check(abs(real_max - real["family_max"]) < 1e-12, "real family_max is not the max of its cells", failures)
    null_max = [t["family_max"] for t in null["trials"]]
    exceed = sum(1 for x in null_max if x >= real_max)
    p = (exceed + 1) / (expected_trials + 1)

    return {
        "pair": pair,
        "real_path": str(real_path.relative_to(REPO_ROOT)),
        "null_path": str(null_path.relative_to(REPO_ROOT)),
        "real_artifact_sha256": real_artifact_hash,
        "null_artifact_sha256": null_artifact_hash,
        "lock_status": lock["status"],
        "audit_script_sha256": script_hash,
        "protocol_sha256": proto_hash,
        "expected_length": expected_length,
        "expected_real_seed": expected_real_seed,
        "expected_null_seed_base": expected_seed_base,
        "cells": len(real_cells),
        "trials": len(numbers),
        "locked_trials": expected_trials,
        "real_family_max": real_max,
        "null_family_max_min": min(null_max) if null_max else None,
        "null_family_max_median": sorted(null_max)[len(null_max) // 2] if null_max else None,
        "null_family_max_max": max(null_max) if null_max else None,
        "exceedances_tie_inclusive": exceed,
        "p_value": p,
        "promotion_bar": promotion_p,
        "promoted": p <= promotion_p and not failures,
        "failures": failures,
        "consistent": not failures,
    }


def main():
    if len(sys.argv) not in (1, 2) or (len(sys.argv) == 2 and sys.argv[1] not in ("gi", "he")):
        print("usage: phase477a_verify_run.py [gi|he]  (runs both if omitted; no other arguments accepted)", file=sys.stderr)
        sys.exit(2)
    pairs = [sys.argv[1]] if len(sys.argv) == 2 else ["gi", "he"]
    all_ok = True
    for pair in pairs:
        report = verify(pair)
        out_path = SCRIPT_DIR / f"phase477a{'':s}_verification.json" if pair == "gi" else SCRIPT_DIR / "phase477a_he_verification.json"
        if pair != "gi":
            out_path = SCRIPT_DIR / "phase477a_he_verification.json"
        else:
            out_path = SCRIPT_DIR / "phase477a_verification.json"
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        all_ok = all_ok and report["consistent"]
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
