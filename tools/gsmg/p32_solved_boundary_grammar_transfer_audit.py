#!/usr/bin/env python3
"""Forward-transfer test of Phase 341's solved-boundary construction grammar
onto `P32TRAILING`, per the user's exact 2026-08-22 sequencing: freeze the
grammar, generate a manifest WITHOUT querying the blob, diff it against
Phase 270's already-tested candidates (and the curated registry / other P32
sweeps), then query only what is genuinely new.

**Why this is not a trivial re-run of Phase 341.** Phase 341's rule engine
(`solved_boundary_rule_audit.py`) reconstructs Phase 2/3/3.2's passwords by
reading each boundary's own PAGE-LEVEL ANNOTATION -- e.g. Phase 3.2's three
clue answers are each explicitly marked "/(aa, connected enf)" in the
Phase-3 plaintext that names them, which is what licenses force-lowercase +
strip-all-nonalnum as the correct per-component transform, not a guess. That
per-component annotation is the actual load-bearing input to the grammar --
without it, "the frozen rules" have nothing case/whitespace-specific to
freeze.

`P32TRAILING` has NO such annotation. `extract_phase32_components()` (this
project's own byte-exact delimiter-based extraction, reused unmodified
below) shows the Phase-3.2.2 clue text is followed immediately by
`\\r\\n\\r\\n` and then the raw base64 blob -- zero instruction bytes in
between. This is verified programmatically below (`self_test()`), not
assumed.

**What the grammar can therefore honestly say about P32TRAILING:** only the
parts that don't depend on a missing annotation --

  - authenticated component order (3.2.1 -> 3.2.2, matching the page's own
    source order, independently confirmed by `page_structure_audit.py`);
  - no-separator concatenation (matches Phase 2/3/3.2's own convention);
  - NO case-forcing or whitespace-stripping (there is no annotation
    authorizing one -- the "distance 0 / most literal" reading is to leave
    each component exactly as independently re-derived);
  - no explicit literal prefix (none is written on the page, unlike
    Phase 3.2's "giveit");
  - SHA-256 lowercase hex as the OpenSSL passphrase, alongside a raw
    control (matches all three solved boundaries' own established
    profile);
  - the established OpenSSL KDF profile that matches the solved parent
    stage (`legacy-sha256-aes256`), alongside the same compatibility
    variants Phase 270 already used.

  Per Phase 341's own shuffled-order control convention, the reverse
  concatenation order is included as a negative control, not a real
  candidate.

This collapses to exactly 2 base strings x 2 hash treatments = 4 password
materials -- a genuinely small, closed, pre-declared set, per this
project's brainstorm discipline.

Usage:
    python3 tools/gsmg/p32_solved_boundary_grammar_transfer_audit.py
    python3 tools/gsmg/p32_solved_boundary_grammar_transfer_audit.py --self-test
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data import P32_TRAILING_BLOB_B64  # noqa: E402
from extended_cipher_recheck import load_curated_candidates  # noqa: E402
from p32_sibling_password_audit import (  # noqa: E402
    KDF_SPECS,
    build_candidates,
    decrypt_phase32_bytes,
    derive_sibling_outputs,
    password_materials,
    structural_trials,
)

# The two components' page-order concatenation is the grammar's one
# genuinely primary (distance-0) reading; the reverse order is retained
# only as Phase 341's own shuffled-order negative control, not a candidate.
PRIMARY_LABEL = "grammar_transfer_321_then_322"
CONTROL_LABEL = "grammar_transfer_322_then_321_shuffled_control"


def no_instruction_gap(plaintext=None):
    """Byte-exact proof that no instruction text separates the Phase-3.2.2
    clue from the P32TRAILING envelope -- the fact that makes the grammar's
    case/whitespace/prefix axes inapplicable here (see module docstring)."""
    plaintext = decrypt_phase32_bytes() if plaintext is None else plaintext
    from p32_sibling_password_audit import extract_phase32_components
    components = extract_phase32_components(plaintext)
    p32_start = components["offsets"]["p32_start"]
    clue_end = components["offsets"]["clue_322_start"] + len(components["clue_322"])
    gap = plaintext[clue_end:p32_start]
    return gap


def frozen_manifest():
    """The forward-transferred grammar's full, closed candidate set: 2 base
    strings (primary + shuffled control) x 2 hash treatments (raw,
    sha256-hex) = 4 password materials. Generated without any reference to
    P32TRAILING's ciphertext."""
    derived = derive_sibling_outputs()
    answer_321, answer_322 = derived["answer_321"], derived["answer_322"]
    primary = answer_321 + answer_322
    control = answer_322 + answer_321
    manifest = {}
    for label, base in ((PRIMARY_LABEL, primary), (CONTROL_LABEL, control)):
        manifest[(label, "raw")] = base.encode()
        manifest[(label, "sha256-hex")] = hashlib.sha256(base.encode()).hexdigest().encode()
    return manifest, derived


def phase270_known_materials(derived):
    """Every byte-string password material Phase 270's own audit already
    generated and tested, for exact-membership diffing."""
    plaintext = derived["phase32_plaintext"]
    p32_start = derived["components"]["offsets"]["p32_start"]
    candidates, _construction = build_candidates(
        derived["answer_321"], derived["answer_322"], plaintext, p32_start,
    )
    materials = password_materials(candidates)
    return {record["material"] for record in materials}


def curated_registry_materials():
    """The 648-candidate curated wordlist tier, as raw literal bytes only
    (this registry holds short literal words/phrases, not pre-hashed
    forms -- checked for completeness, not because a match is expected)."""
    return {candidate.encode() for candidate in load_curated_candidates()}


def classify(manifest, known_phase270, known_curated):
    """Every manifest entry, tagged exact_duplicate / genuinely_new against
    Phase 270's own tested materials and the curated registry."""
    report = []
    for (label, treatment), material in manifest.items():
        if material in known_phase270:
            status = "exact_duplicate_of_phase270"
        elif material in known_curated:
            status = "exact_duplicate_of_curated_registry"
        else:
            status = "genuinely_new_and_phase341_authorized"
        report.append({
            "label": label,
            "treatment": treatment,
            "material": material,
            "status": status,
        })
    return report


def query_genuinely_new(classified):
    """Runs Phase 270's own exact structural oracle (80-byte P32TRAILING,
    two-private-key/full-padding-block detector) against only the entries
    classified genuinely new -- per the user's exact step 5."""
    new_materials = tuple(
        entry["material"] for entry in classified
        if entry["status"] == "genuinely_new_and_phase341_authorized"
    )
    if not new_materials:
        return {"queried": 0, "hits": []}
    fake_records = tuple({"material": m, "sources": [], "treatments": []} for m in new_materials)
    result = structural_trials(fake_records)
    return {"queried": len(new_materials), "hits": result["hits"]}


def audit():
    manifest, derived = frozen_manifest()
    gap = no_instruction_gap(derived["phase32_plaintext"])
    known_phase270 = phase270_known_materials(derived)
    known_curated = curated_registry_materials()
    classified = classify(manifest, known_phase270, known_curated)
    oracle = query_genuinely_new(classified)
    return {
        "no_instruction_gap": gap,
        "manifest_size": len(manifest),
        "classified": classified,
        "phase270_material_count": len(known_phase270),
        "curated_registry_count": len(known_curated),
        "oracle": oracle,
    }


def self_test():
    gap = no_instruction_gap()
    assert gap == b"\r\n\r\n", (
        f"self-test FAILED: expected zero-instruction 4-byte separator between "
        f"the Phase-3.2.2 clue and P32TRAILING, got {gap!r} ({len(gap)} bytes) -- "
        f"if this is no longer just a separator, the grammar-transfer premise "
        f"in this module's docstring needs to be revisited"
    )

    manifest, derived = frozen_manifest()
    assert len(manifest) == 4, f"self-test FAILED: expected 4 password materials, got {len(manifest)}"
    primary_raw = manifest[(PRIMARY_LABEL, "raw")]
    assert primary_raw == (derived["answer_321"] + derived["answer_322"]).encode()

    report = audit()
    assert report["manifest_size"] == 4
    statuses = {entry["status"] for entry in report["classified"]}
    assert statuses <= {
        "exact_duplicate_of_phase270",
        "exact_duplicate_of_curated_registry",
        "genuinely_new_and_phase341_authorized",
    }
    # The forward-transferred grammar's primary candidate (raw and
    # sha256-hex) is expected to already be exact_duplicate_of_phase270,
    # since Phase 270's own "whole-text family" already tested both
    # sibling-order concatenations in both raw and sha256-hex form --
    # confirming the apparent "unexecuted transfer" was already covered
    # operationally under different labels, not a new gap.
    for entry in report["classified"]:
        assert entry["status"] == "exact_duplicate_of_phase270", (
            f"self-test FAILED: expected every grammar-transfer candidate to "
            f"already be covered by Phase 270, found {entry['status']} for "
            f"{entry['label']}/{entry['treatment']}"
        )
    assert report["oracle"]["queried"] == 0
    assert report["oracle"]["hits"] == []
    print(
        f"[*] self-test OK: {report['manifest_size']} grammar-transferred "
        f"P32TRAILING candidates, all 4 already exact_duplicate_of_phase270 "
        f"(0 genuinely new, 0 queried, {report['phase270_material_count']} "
        f"Phase-270 materials / {report['curated_registry_count']} curated "
        f"registry entries checked against)"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    report = audit()
    print(f"[*] no-instruction gap between 3.2.2 clue and P32TRAILING: {report['no_instruction_gap']!r}")
    print(f"[*] frozen-grammar manifest: {report['manifest_size']} password materials")
    for entry in report["classified"]:
        print(f"    {entry['label']}/{entry['treatment']}: {entry['status']}")
    print(
        f"[*] checked against {report['phase270_material_count']} Phase-270 "
        f"materials and {report['curated_registry_count']} curated registry entries"
    )
    print(f"[*] oracle: {report['oracle']['queried']} genuinely-new materials queried, "
          f"{len(report['oracle']['hits'])} hits")
    if report["oracle"]["hits"]:
        for hit in report["oracle"]["hits"]:
            print(f"\n[+++ HIT] {hit}")


if __name__ == "__main__":
    main()
