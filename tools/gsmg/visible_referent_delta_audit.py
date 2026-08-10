#!/usr/bin/env python3
"""Audit visible yin-yang referent candidates added after the base inventory.

The original seven-family inventory is retained as the baseline.  This audit
adds only later discoveries or page-local structures that were not separately
gated there.  It runs no password, cipher, or address oracle.

A candidate qualifies only when all five fields are true: it is authenticated
and visible, deterministically recovered, genuinely dual, at the immediate
post-``lastwordsbeforearchichoice`` boundary, and has either a fixed consumer
or an independently discriminating structural property.
"""

import argparse
import base64
import json
from pathlib import Path

import creator_yingyang_faed_pair_audit
import macro_tail_title_insertion_audit
import salphaseion_presentation_binding_audit
import yinyang_artifact_inventory_audit
from data import COSMIC_BLOB_B64, SALPHASEION_BLOB_B64
from page_structure_audit import DEFAULT_HTML, audit as page_audit
from telegram_export_manifest import DEFAULT_EXPORT_DIR


GATE_NAMES = (
    "authenticated_visible",
    "deterministic_recovery",
    "genuine_dual",
    "correct_transition_position",
    "fixed_consumer_or_independent_discriminator",
)


def candidate(candidate_id, observation, gates, evidence, failure):
    if tuple(gates) != GATE_NAMES:
        raise AssertionError(f"{candidate_id} gate schema drifted")
    qualifies = all(gates.values())
    if qualifies and failure:
        raise AssertionError(f"{candidate_id} qualifies but has a failure reason")
    if not qualifies and not failure:
        raise AssertionError(f"{candidate_id} fails without an explicit reason")
    return {
        "candidate_id": candidate_id,
        "observation": observation,
        "evidence": evidence,
        "gates": gates,
        "qualifies": qualifies,
        "failure": failure,
    }


def decoded_segments(page):
    return {
        row["name"]: row.get("decoded")
        for row in page["salphaseion"]["segments"]
    }


def audit(
    export_dir=DEFAULT_EXPORT_DIR,
    html_path=DEFAULT_HTML,
    dictionary_path=macro_tail_title_insertion_audit.DEFAULT_DICTIONARY,
):
    baseline_table = yinyang_artifact_inventory_audit.QUALIFICATION
    baseline_qualifying = tuple(
        artifact_id
        for artifact_id, gates in baseline_table.items()
        if all(gates[field] for field in ("primary", "visible", "dual", "correct_boundary"))
        and gates["independent_discriminator"]
    )
    if baseline_qualifying:
        raise AssertionError(f"baseline inventory reopened: {baseline_qualifying}")

    page = page_audit(Path(html_path))
    presentation = salphaseion_presentation_binding_audit.audit(Path(html_path))
    title = macro_tail_title_insertion_audit.audit(dictionary_path)
    spelling = creator_yingyang_faed_pair_audit.audit(export_dir)
    segments = decoded_segments(page)

    if presentation["binding_candidates_found"]:
        raise AssertionError("presentation audit unexpectedly recovered a binding")
    if segments["decimal_instruction_2"] != "thispassword":
        raise AssertionError("thispassword instruction drifted")
    if segments["hash_prefix"] != "sha256 our first hint is your last command":
        raise AssertionError("SHA instruction drifted")
    if segments["abba_enter_instruction"] != "enter":
        raise AssertionError("enter instruction drifted")

    authenticated_blobs = {
        "SALPH": SALPHASEION_BLOB_B64,
        "COSMIC": COSMIC_BLOB_B64,
    }
    decoded_fronts = {
        name: base64.b64decode(value, validate=True)[:8]
        for name, value in authenticated_blobs.items()
    }
    if set(decoded_fronts.values()) != {b"Salted__"}:
        raise AssertionError("authenticated OpenSSL envelope marker drifted")

    salph_segments = {
        row["name"]: row for row in page["salphaseion"]["segments"]
    }
    left = salph_segments["salphaseion_aes_prefix"]
    right = salph_segments["salphaseion_aes_suffix"]
    if (left["length"], right["length"]) != (64, 64):
        raise AssertionError("SALPH enter-halves drifted")
    if page["salphaseion"]["embedded_enter_splits_aes_at"] != 64:
        raise AssertionError("SALPH enter split offset drifted")

    rows = (
        candidate(
            "openssl_salted_fronts",
            "Visible Base64 envelopes decode by a solved-stage operation to Salted__ at their front.",
            dict(zip(GATE_NAMES, (True, True, False, False, False))),
            {
                "visible_prefixes": {
                    name: value[:12] for name, value in authenticated_blobs.items()
                },
                "decoded_fronts": {
                    name: value.decode("ascii") for name, value in decoded_fronts.items()
                },
                "operator_precedent": "Base64 decoding and OpenSSL Salted__ envelopes are demonstrated",
            },
            "A shared container marker is neither a dual state nor a password/decoder binding, and it is not produced at the Architect boundary.",
        ),
        candidate(
            "salt_phase_ion_insertion",
            "Inserting t at title position 3 yields salt|phase|ion and resonates with Salted__.",
            dict(zip(GATE_NAMES, (False, False, False, False, False))),
            {
                "family_size": title["family_size"],
                "valid_reading_count": title["valid_reading_count"],
                "camel_boundary_reading_count": len(title["original_camel_boundary_readings"]),
                "selection_status": title["selection_status"],
            },
            "The resulting title is not authored or uniquely selected: lowercase true supplies four letters, and the original title boundary admits both salt and sale.",
        ),
        candidate(
            "creator_ying_ig_ag",
            "Creator YING/YANG wording filters to IG/AG; I and A are mirror endpoints and G is shared.",
            dict(zip(GATE_NAMES, (True, False, True, True, True))),
            {
                "native_filtered": spelling["lexical_mechanics"]["native_filtered"],
                "faed_pair_ranks": spelling["observed_pair_ranks"]["faed_ranks"],
                "faed_best_shared_symbol": spelling["shared_suffix_controls"]["faed"]["best_joint_suffix"]["shared_symbol"],
                "binary_macro_uses_standard_yinyang": spelling["creator_evidence"]["binary_macro"]["uses_standard_yinyang"],
                "authored_spelling_operator": spelling["gates"]["authored_spelling_operator"],
            },
            "The alignment has an independent FAED discriminator, but the spelling is inconsistent across creator channels and is explicitly barred as a typo-derived operator.",
        ),
        candidate(
            "thispassword_sha256_salph_sequence",
            "The authenticated page orders thispassword, the SHA instruction, and the SALPH envelope locally.",
            dict(zip(GATE_NAMES, (True, False, False, False, False))),
            {
                "instruction": segments["decimal_instruction_2"],
                "next_instruction": segments["hash_prefix"],
                "presentation_binding_candidates": presentation["binding_candidates_found"],
                "authored_segment_boundaries": presentation["salphaseion"]["segment_boundaries"],
            },
            "Page order is authentic, but uniform presentation supplies no operand scope, no dual state, and no fixed SHA preimage or SALPH consumer.",
        ),
        candidate(
            "salph_enter_halves",
            "Literal enter separates two visible 64-character halves of one authenticated SALPH envelope.",
            dict(zip(GATE_NAMES, (True, True, True, False, True))),
            {
                "half_lengths": (left["length"], right["length"]),
                "split_offset": page["salphaseion"]["embedded_enter_splits_aes_at"],
                "decoded_instruction": segments["abba_enter_instruction"],
                "consumer": "deterministically reconstructs the known SALPH Base64 envelope",
            },
            "This is a real deterministic dual construction and positive control, but it occurs after thispassword/SHA and is not the state immediately produced by lastwordsbeforearchichoice.",
        ),
    )

    qualifying = tuple(row["candidate_id"] for row in rows if row["qualifies"])
    return {
        "scope": "post-baseline visible-referent delta; no oracle",
        "gate_names": GATE_NAMES,
        "baseline": {
            "artifact_count": len(baseline_table),
            "qualifying_artifacts": baseline_qualifying,
            "source": "yinyang_artifact_inventory_audit.QUALIFICATION",
        },
        "candidates": rows,
        "qualifying_candidates": qualifying,
        "new_compute_authorized": bool(qualifying),
        "excluded_as_already_baselined": (
            "BUT/HYE rails",
            "selected/complement DBBI partition",
            "paired SalPhaseIon/Cosmic page objects",
            "first-piece polarity",
            "Cosmic Duality book",
            "One/Two guides",
            "hypothetical SALPH plaintext key halves",
        ),
        "verdict": (
            "The post-baseline delta contains one genuine deterministic visible "
            "dual construction (SALPH's enter-separated halves), but it is at the "
            "wrong transition position. YING->IG/AG has the strongest boundary "
            "and FAED-specific support but fails deterministic authorship. No "
            "candidate passes all five gates, so no password, decoder, or oracle "
            "expansion is authorized."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR, html_path=DEFAULT_HTML, dictionary_path=macro_tail_title_insertion_audit.DEFAULT_DICTIONARY):
    report = audit(export_dir, html_path, dictionary_path)
    assert report["baseline"]["artifact_count"] == 7
    assert report["baseline"]["qualifying_artifacts"] == ()
    assert len(report["candidates"]) == 5
    assert report["qualifying_candidates"] == ()
    assert not report["new_compute_authorized"]
    by_id = {row["candidate_id"]: row for row in report["candidates"]}
    assert by_id["salph_enter_halves"]["gates"]["genuine_dual"]
    assert not by_id["salph_enter_halves"]["gates"]["correct_transition_position"]
    assert by_id["creator_ying_ig_ag"]["gates"]["fixed_consumer_or_independent_discriminator"]
    assert not by_id["creator_ying_ig_ag"]["gates"]["deterministic_recovery"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: five delta candidates, zero qualifiers, no oracle authorized")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--dictionary", type=Path, default=macro_tail_title_insertion_audit.DEFAULT_DICTIONARY)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export_dir, args.html, args.dictionary) if args.self_test else audit(args.export_dir, args.html, args.dictionary)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
