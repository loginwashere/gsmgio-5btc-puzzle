#!/usr/bin/env python3
"""Phase 451 -- G-YIN-001/BTCSEED topology synthesis and contradiction audit.

Pure synthesis over already-completed phases: no new decoder, statistical
test, cipher search, or oracle call. This script's only computation is
machine-verifying that every quoted claim below is byte-present (after
whitespace normalization) in the cited phase's own findings-store entry,
then reporting the frozen synthesis conclusions from
`doc/Brainstorms/2026-08-29 - Phase 451 G-YIN-001 BTCSEED Topology
Synthesis Protocol.md`.
"""

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FINDINGS_DIR = REPO_ROOT / "tools/gsmg/findings"

# Every citation this synthesis relies on, keyed by the findings file it must
# appear in.  Checked after collapsing all whitespace runs to one space, so
# markdown line-wrapping cannot cause a false failure or a silent typo.
REQUIRED_CITATIONS = {
    "P00371.md": [
        "either_stream_requires_the_other_as_input = False",
        "no page evidence found requires DBBI's content to feed FAED",
    ],
    "P00386.md": [
        "mechanically real",
        "Does not reopen or narrow any existing gap",
        "DBBI` itself, not an external word, as the Bifid keyword source",
    ],
    "P00408.md": [
        "Z` is uniquely at index 97 only for period 570",
        "Only period 570 produces output starting with",
    ],
    "P00412.md": [
        "does not disprove every asymmetric joint generator",
        "p_family=0.000599994",
    ],
    "P00413.md": [
        "letter-b-driven with partial distributed support",
    ],
}

TOPOLOGY_REFILING = {
    "claim": (
        "BTCSEED (Phases 386-408) structurally instantiates Topology "
        "Audit's T4 ('DBBI instructs FAED'), not T3 ('DBBI/FAED combine "
        "symmetrically')."
    ),
    "mechanism": (
        "Phase 386 builds a Bifid key square by de-duplicating DBBI[:13] "
        "and uses it to decrypt FAED as ciphertext -- DBBI supplies key "
        "material, FAED is the operand. This is a directional, asymmetric "
        "relation (T4's own definition), not a peer/joint-decode relation "
        "(T3's definition)."
    ),
    "prior_filing_gap": (
        "Neither GSMG_TOPOLOGY_AUDIT.md nor GSMG_SCIENTIFIC_THEORY_REGISTRY.md "
        "previously cross-mapped BTCSEED to a Topology Audit letter. The "
        "Topology Audit's own T4 row cited only a weak escape-pair-asymmetry "
        "inference, explicitly flagged 'not a project finding,' unaware of "
        "the executed Phase 386-408 experiment that directly bears on T4."
    ),
    "experiment_outcome": (
        "stopped, not promoted: the only period that reproduces the "
        "BTCSEED/Z@97/alternation package is the one used to discover it "
        "(Phase 408, period_robust=False); zero consumer hits across 12 "
        "frozen families and ~400,000 checks (Phases 397-407); Phase 386's "
        "own disposition states this 'does not reopen or narrow any "
        "existing gap.'"
    ),
}

CONTRADICTION_AUDIT = {
    "phase_371_vs_btcseed": {
        "contradiction_found": False,
        "reasoning": (
            "Phase 371 tests what the page's own literal instruction-token "
            "adjacency licenses; BTCSEED tests a specific, unlicensed "
            "community-proposed construction executed against the raw "
            "streams. Both find no creator-authenticated consumer -- "
            "compatible negatives about different evidence classes, not a "
            "contradiction about the same claim."
        ),
    },
    "phase_412_413_vs_t4": {
        "contradiction_found": False,
        "reasoning": (
            "Phase 412 rejects only the narrow shared/pooled-distribution "
            "null (registry T2 / topology T3) and explicitly disclaims "
            "disproving 'every asymmetric joint generator.' A directional "
            "keying relation like T4 is outside that test's scope, so it "
            "cannot contradict or support T4 either way."
        ),
    },
}

GYIN_001_DISPOSITION = {
    "status": "unchanged: parked, P0",
    "reasoning": (
        "No creator-selected operator exists under either the symmetric "
        "(T3) or asymmetric (T4) framing. BTCSEED supplies one concretely "
        "executed, mechanically real T4-shaped candidate, but that "
        "candidate's own experiment already concluded stopped/not-promoted "
        "for want of an independently selected period and a downstream "
        "consumer -- the same bar every one of the ~45 T3-shaped candidates "
        "(Phases 272-321) already failed. Phase 386's own disposition "
        "states this directly: 'does not reopen or narrow any existing "
        "gap.' This synthesis corrects a documentation gap (BTCSEED was "
        "never cross-filed against the T0-T8 taxonomy), not G-YIN-001's "
        "evidentiary status."
    ),
}


def normalize(text):
    return re.sub(r"\s+", " ", text)


def verify_citations():
    results = {}
    for filename, snippets in REQUIRED_CITATIONS.items():
        text = normalize((FINDINGS_DIR / filename).read_text(encoding="utf-8"))
        results[filename] = {
            snippet: normalize(snippet) in text for snippet in snippets
        }
    return results


def all_citations_verified(results):
    return all(
        present
        for snippets in results.values()
        for present in snippets.values()
    )


def synthesize():
    citation_results = verify_citations()
    return {
        "citations_verified": citation_results,
        "all_citations_verified": all_citations_verified(citation_results),
        "topology_refiling": TOPOLOGY_REFILING,
        "contradiction_audit": CONTRADICTION_AUDIT,
        "gyin_001_disposition": GYIN_001_DISPOSITION,
    }


def self_test():
    report = synthesize()
    assert report["all_citations_verified"] is True, report["citations_verified"]
    assert not report["contradiction_audit"]["phase_371_vs_btcseed"]["contradiction_found"]
    assert not report["contradiction_audit"]["phase_412_413_vs_t4"]["contradiction_found"]
    assert report["gyin_001_disposition"]["status"].startswith("unchanged")
    print(
        "[*] self-test OK: all 8 cross-referenced citations verified "
        "byte-present in their source findings entries; no contradiction "
        "found between Phase 371/412/413 and the BTCSEED branch"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    report = self_test()
    if args.self_test:
        return

    print()
    print(f"[*] topology re-filing claim: {report['topology_refiling']['claim']}")
    print(f"[*] G-YIN-001 disposition: {report['gyin_001_disposition']['status']}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(f"\n[*] full report written to {args.json_out}")


if __name__ == "__main__":
    main()
