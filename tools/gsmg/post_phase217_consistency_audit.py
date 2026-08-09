#!/usr/bin/env python3
"""Regression guard for the Phase-217 circular-rebus correction."""

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER = PROJECT_ROOT / "doc" / "GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md"
LEGACY_DOCS = (
    PROJECT_ROOT / "doc" / "GSMG_NON_BLOB_LOCK_AUDIT.md",
    PROJECT_ROOT / "doc" / "GSMG_MATRIXSUMLIST_CHECKPOINT.md",
    PROJECT_ROOT / "doc" / "GSMG_YINYANG_ARTIFACT_IDENTIFICATION_PLAN.md",
    PROJECT_ROOT / "doc" / "GSMG_YIN_YANG_TRANSITION_AUDIT.md",
    PROJECT_ROOT / "doc" / "GSMG_BIRD_VIEW_REASSESSMENT.md",
    PROJECT_ROOT / "doc" / "GSMG_YINYANG_ARTIFACT_INVENTORY.md",
)


def audit():
    ledger = LEDGER.read_text(encoding="utf-8")
    forbidden_ledger_forms = ("H | YE | BUT", "H|YE|BUT")
    residual = tuple(form for form in forbidden_ledger_forms if form in ledger)
    if residual:
        raise AssertionError(f"canonical ledger retains circular rebus: {residual}")
    required_ledger_phrases = (
        "cross-source-stable forward-one indexing",
        "removed in Phase 217 as circular",
        "UNKNOWN operation after the recognition checkpoint",
    )
    missing = tuple(item for item in required_ledger_phrases if item not in ledger)
    if missing:
        raise AssertionError(f"canonical ledger correction incomplete: {missing}")

    notices = []
    for path in LEGACY_DOCS:
        text = path.read_text(encoding="utf-8")
        opening = "\n".join(text.splitlines()[:12]).lower()
        if "217" not in opening or "circular" not in opening:
            raise AssertionError(f"legacy document lacks correction notice: {path.name}")
        notices.append(path.name)
    return {
        "canonical_ledger": LEDGER.name,
        "forbidden_rebus_forms_present": residual,
        "corrected_legacy_documents": tuple(notices),
        "retained_checkpoint": "BUT/HYE; mirror9 b<->h with e fixed",
        "excluded_transition": "H plus selected initials of your eyes plus BUT",
        "verdict": (
            "The active creator ledger no longer promotes the circular rebus, "
            "and every legacy synthesis document that contains it is marked at "
            "the top. BUT/HYE remains a recognition checkpoint; it supplies no "
            "post-yinyang operator."
        ),
    }


def self_test():
    report = audit()
    assert not report["forbidden_rebus_forms_present"]
    assert len(report["corrected_legacy_documents"]) == 6
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: Phase-217 correction propagated")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
