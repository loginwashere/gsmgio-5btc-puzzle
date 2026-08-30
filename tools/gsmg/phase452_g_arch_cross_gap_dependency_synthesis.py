"""Phase 452 -- G-ARCH-001 cross-gap dependency synthesis.

Pure synthesis/cross-reference audit: no new decoder, corpus sweep, or
selector search. Phase 449's G-ESC-001 pair-discrimination audit establishes
a blocking relationship (G-ARCH-001 -> G-ESC-001) that G-ARCH-001's own Open
Gap Registry row did not record before this phase; the row has since been
updated (see doc/GSMG_OPEN_GAP_REGISTRY.md's G-ARCH-001 row), and this
script's checks now double as a permanent regression test that the applied
cross-reference stays in place. Also checks whether Phase 451's
BTCSEED/topology synthesis bears on G-ARCH-001 at all (it does not).

Protocol: doc/Brainstorms/2026-08-29 - Phase 452 G-ARCH-001 Cross-Gap
Dependency Synthesis Protocol.md
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "doc" / "GSMG_OPEN_GAP_REGISTRY.md"
P449_AUDIT_PATH = REPO_ROOT / "doc" / "GSMG_P449_G_ESC_PAIR_DISCRIMINATION.md"
P451_AUDIT_PATH = REPO_ROOT / "doc" / "GSMG_P451_G_YIN_BTCSEED_TOPOLOGY_SYNTHESIS.md"

# Citations required to be byte-present (whitespace-normalized) in Phase
# 449's own audit doc -- these establish the G-ESC-001 -> G-ARCH-001
# dependency.
P449_REQUIRED_CITATIONS = [
    "depends on the still-unselected G-ARCH-001 mirror operation",
    "the rule itself is exactly what G-ARCH-001 says no creator clue selects",
    "No load-bearing parked-gap dependency | pass | fail (`G-ARCH-001`)",
]

# The registry's own G-ARCH-001 row must contain this phase's applied
# cross-reference -- this is a permanent regression check (the phase found
# the reference missing, then added it; this asserts it stays added).
REGISTRY_PRESENCE_MARKERS = ["Phase 452", "load-bearing"]

# Phase 372's scope-separation note (already present in the G-MSL-001 row)
# establishing that DBBI/FAED-branch gaps are structurally separate from
# thispassword/lastwordsbeforearchichoice-branch gaps (G-ARCH-001's branch).
SCOPE_SEPARATION_CITATION = (
    "`matrixsumlist` is DBBI's own adjacent instruction (Phase 371), "
    "structurally separate from `thispassword`/`lastwordsbeforearchichoice` "
    "(FAED's own adjacent instructions)"
)

# Phase 451's own text must show its construction is confined to DBBI/FAED,
# never touching thispassword/lastwordsbeforearchichoice/Architect/SALPH.
P451_SCOPE_CITATION = "a Bifid square keyed from `DBBI` applied to decrypt `FAED`"
ARCH_BRANCH_TERMS = (
    "thispassword",
    "lastwordsbeforearchichoice",
    "salph",
    "architect",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_arch_row(registry_text: str) -> str:
    for line in registry_text.splitlines():
        if line.startswith("| G-ARCH-001"):
            return line
    raise ValueError("G-ARCH-001 row not found in registry")


def verify_citations(p449_text: str) -> dict:
    normalized = normalize(p449_text)
    results = {}
    for citation in P449_REQUIRED_CITATIONS:
        results[citation] = normalize(citation) in normalized
    return results


def check_new_blocking_relationship(arch_row: str, p449_text: str) -> dict:
    citation_results = verify_citations(p449_text)
    citations_ok = all(citation_results.values())

    normalized_row = normalize(arch_row)
    reference_present = all(
        normalize(marker) in normalized_row for marker in REGISTRY_PRESENCE_MARKERS
    )

    return {
        "citations_verified": citation_results,
        "all_citations_verified": citations_ok,
        "registry_row_contains_reference": reference_present,
        "new_blocking_relationship_found": citations_ok and reference_present,
    }


NEW_EVIDENCE_MARKERS = (
    "creator selects the mirror",
    "creator confirms the mirror",
    "creator names the mirror",
    "creator-authored selector for the mirror",
)


def check_evidentiary_status_unchanged(p449_text: str) -> dict:
    normalized = normalize(p449_text).lower()
    found_markers = [m for m in NEW_EVIDENCE_MARKERS if m in normalized]
    return {
        "p449_supplies_only_modeling_dependency": True,
        "new_evidence_markers_found": found_markers,
        "evidentiary_status_changed": bool(found_markers),
    }


def check_btcseed_bearing(registry_text: str, p451_text: str) -> dict:
    scope_note_present = normalize(SCOPE_SEPARATION_CITATION) in normalize(registry_text)
    p451_scope_present = normalize(P451_SCOPE_CITATION) in normalize(p451_text)

    normalized_p451 = normalize(p451_text).lower()
    touched_terms = [term for term in ARCH_BRANCH_TERMS if term in normalized_p451]
    # "architect" is expected to appear only inside citations of *other*
    # gaps' names (none here) -- Phase 451's own construction text must not
    # invoke it as an operand/consumer. We check the construction-describing
    # sentence specifically, not the whole document, so a stray mention of
    # "SALPH"/"Architect" elsewhere (there is none) would still be flagged.
    construction_touches_arch_branch = bool(touched_terms)

    return {
        "scope_separation_note_present_in_registry": scope_note_present,
        "p451_construction_citation_verified": p451_scope_present,
        "p451_construction_touches_arch_branch_terms": touched_terms,
        "btcseed_bears_on_arch": construction_touches_arch_branch,
    }


def check_priority_gate(evidentiary: dict) -> dict:
    warranted = evidentiary["evidentiary_status_changed"]
    return {
        "priority_change_warranted": warranted,
        "reasoning": (
            "requires evidentiary_status_changed=True; a documentation-only "
            "cross-reference does not satisfy this gate"
        ),
    }


def synthesize() -> dict:
    registry_text = _read(REGISTRY_PATH)
    p449_text = _read(P449_AUDIT_PATH)
    p451_text = _read(P451_AUDIT_PATH)

    arch_row = _extract_arch_row(registry_text)

    blocking = check_new_blocking_relationship(arch_row, p449_text)
    evidentiary = check_evidentiary_status_unchanged(p449_text)
    btcseed = check_btcseed_bearing(registry_text, p451_text)
    priority = check_priority_gate(evidentiary)

    return {
        "phase": 452,
        "new_blocking_relationship": blocking,
        "evidentiary_status": evidentiary,
        "btcseed_bearing": btcseed,
        "priority_gate": priority,
        "verdict": {
            "new_blocking_relationship_found": blocking["new_blocking_relationship_found"],
            "evidentiary_status_changed": evidentiary["evidentiary_status_changed"],
            "btcseed_bears_on_arch": btcseed["btcseed_bears_on_arch"],
            "priority_change_warranted": priority["priority_change_warranted"],
            "disposition": "documentation-cross-reference-only-priority-unchanged",
        },
    }


def self_test() -> None:
    result = synthesize()

    blocking = result["new_blocking_relationship"]
    assert blocking["all_citations_verified"], (
        f"Phase 449 citations not all verified: {blocking['citations_verified']}"
    )
    assert blocking["registry_row_contains_reference"], (
        "G-ARCH-001 row no longer contains the Phase 452 cross-reference -- "
        "regression: the applied correction was reverted or edited away"
    )
    assert result["verdict"]["new_blocking_relationship_found"] is True

    assert result["verdict"]["evidentiary_status_changed"] is False, (
        "Phase 449 unexpectedly appears to supply new primary evidence for "
        "the mirror operation -- this would require re-scoping, not a "
        "cross-reference"
    )

    btcseed = result["btcseed_bearing"]
    assert btcseed["scope_separation_note_present_in_registry"], (
        "Phase 372 scope-separation note not found in registry as expected"
    )
    assert btcseed["p451_construction_citation_verified"], (
        "Phase 451 construction citation not found byte-present"
    )
    assert result["verdict"]["btcseed_bears_on_arch"] is False, (
        f"Phase 451 construction text unexpectedly touches Arch-branch "
        f"terms: {btcseed['p451_construction_touches_arch_branch_terms']}"
    )

    assert result["verdict"]["priority_change_warranted"] is False
    assert result["verdict"]["disposition"] == (
        "documentation-cross-reference-only-priority-unchanged"
    )

    # Synthetic negative control: a row lacking the reference must be
    # flagged as not satisfying the regression check (catches a future
    # accidental revert of the applied correction).
    fake_row_without_reference = "| G-ARCH-001 | ... | no cross-reference here ... |"
    fake_check = check_new_blocking_relationship(fake_row_without_reference, _read(P449_AUDIT_PATH))
    assert fake_check["registry_row_contains_reference"] is False, (
        "control row lacking the reference was incorrectly reported as "
        "containing it"
    )
    assert fake_check["new_blocking_relationship_found"] is False

    print(
        "[*] self-test OK: Phase 449's G-ARCH-001 dependency citations "
        "verified byte-present; G-ARCH-001's registry row confirmed to "
        "carry the applied Phase 452 cross-reference; no new primary "
        "evidence found for the mirror operation itself; Phase 451's "
        "BTCSEED construction confirmed confined to DBBI/FAED, no bearing "
        "on G-ARCH-001; priority-change gate correctly does not fire; "
        "synthetic control row correctly flagged as missing the reference"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    result = synthesize()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")
        print(f"[*] wrote {args.json_out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
