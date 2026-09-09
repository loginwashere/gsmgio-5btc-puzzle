#!/usr/bin/env python3
"""Compare four closed-system address constructions with prior P32 materials.

This is discovery/reconnaissance for a possible Phase 480 protocol.  It never
calls a cryptographic oracle and never reads P32TRAILING ciphertext.  Historical
candidate generators are reused only to reconstruct the exact password bytes
they previously submitted; the Phase 478 manifest is streamed by exact
``bytes_b64`` membership.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import (  # noqa: E402
    load_candidates,
    normalized_keystrings,
)
from cb_common import answer_forms, keystr_forms  # noqa: E402
from curated_candidate_corpus_audit import active_lines  # noqa: E402
from extended_cipher_recheck import load_curated_candidates  # noqa: E402
from first_hint_hash_audit import (  # noqa: E402
    HALVING_ADDRESS,
    PRIZE_ADDRESS,
    PUZZLE_BANNER,
)


PHASE478_MANIFEST = SCRIPT_DIR / "phase478_manifest.jsonl"
WORDLIST_DIR = REPO_ROOT / "wordlists" / "gsmg"
V2_FULL = WORDLIST_DIR / "curated_v2_full.txt"
MEDIUM_TIER1 = WORDLIST_DIR / "medium_curated_tier1_primary.txt"


def proposed_preimages() -> dict[str, bytes]:
    prize = PRIZE_ADDRESS.encode("ascii")
    halving = HALVING_ADDRESS.encode("ascii")
    return {
        "prize_then_halving": prize + halving,
        "halving_then_prize": halving + prize,
        "banner_prize_halving": PUZZLE_BANNER + prize + halving,
        "banner_halving_prize": PUZZLE_BANNER + halving + prize,
    }


def proposed_materials() -> dict[bytes, list[dict[str, str]]]:
    out: dict[bytes, list[dict[str, str]]] = defaultdict(list)
    for label, preimage in proposed_preimages().items():
        out[preimage].append({"construction": label, "level": "preimage"})
        password = hashlib.sha256(preimage).hexdigest().encode("ascii")
        out[password].append({"construction": label, "level": "sha256_hex_password"})
    return dict(out)


def _record_matches(
    source: str,
    materials,
    targets: dict[bytes, list[dict[str, str]]],
    matches: list[dict],
) -> dict[str, int]:
    seen = set()
    emitted = 0
    for material in materials:
        if material in seen:
            continue
        seen.add(material)
        if material not in targets:
            continue
        emitted += 1
        matches.append({
            "source": source,
            "material_b64": base64.b64encode(material).decode("ascii"),
            "targets": targets[material],
        })
    return {"unique_materials": len(seen), "matched_materials": emitted}


def _shared_materials(candidates, *, newline=False, whitespace=False):
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystring in keystr_forms(
                form,
                newline_variants=newline,
                whitespace_variants=whitespace,
            ):
                yield keystring.encode("utf-8")


def _phase_specific_sources():
    """Yield (source label, exact previously generated password materials)."""
    import architect_puzzle_original_rows_audit as p314
    import phase32_monologue_residual_audit as p265
    import phase3_chain_full_text_p32_sweep_audit as p267
    import phase3_sevenpart_p32_reuse_audit as p266
    import phase3_sevenpart_permutation_audit as p317
    import p32_sibling_password_audit as p270
    import p32_solved_boundary_grammar_transfer_audit as p370
    import x2sh4y0qb15_p32_candidate_audit as p268

    yield "P265", _shared_materials(p265.RESIDUAL_CANDIDATES)

    phase3_concat = p266.phase3_concat()
    p266_candidates = (phase3_concat, hashlib.sha256(phase3_concat.encode()).hexdigest())
    p266_materials = list(_shared_materials(p266_candidates, newline=True, whitespace=True))
    p266_materials.append(hashlib.sha256(phase3_concat.encode()).digest())
    yield "P266", iter(p266_materials)

    yield "P267", _shared_materials(p267.candidate_sentences(), newline=True)

    def p268_materials():
        for candidate in p268.CANDIDATES:
            for form in answer_forms(candidate):
                if not form:
                    continue
                for keystring in keystr_forms(
                    form,
                    newline_variants=True,
                    whitespace_variants=True,
                ):
                    yield keystring.encode("utf-8")
            yield hashlib.sha256(candidate.encode()).digest()

    yield "P268-P269", p268_materials()

    derived = p270.derive_sibling_outputs()
    candidates, _ = p270.build_candidates(
        derived["answer_321"],
        derived["answer_322"],
        derived["phase32_plaintext"],
        derived["components"]["offsets"]["p32_start"],
    )
    yield "P270", (row["material"] for row in p270.password_materials(candidates))

    yield "P314", _shared_materials(p314.CANDIDATES.values())

    def p317_materials():
        for ordering in p317.all_orderings():
            yield from p317.materials_for_ordering(ordering)

    yield "P317", p317_materials()

    # P370 made no new oracle calls, but including its frozen four-entry
    # manifest verifies the expected exact duplication with P270.
    manifest, _ = p370.frozen_manifest()
    yield "P370_nonquery_manifest", iter(manifest.values())


def _phase421_candidate_superset():
    """Every submitted panel string; tested promotions are a subset of this."""
    import phase421_execution_replay as p421

    for rows in p421.candidate_rows().values():
        for candidate in rows:
            yield candidate.encode("utf-8")


def _phase341_calibration_materials():
    """Main and control materials generated by P341; no P32 query occurred."""
    import solved_boundary_rule_audit as p341

    builders = (
        p341.phase2_candidates,
        p341.phase2_shuffled_candidates,
        p341.phase2_naive_candidates,
        p341.phase3_candidates,
        p341.phase3_shuffled_candidates,
        p341.phase3_naive_candidates,
        p341.phase32_candidates,
        p341.phase32_shuffled_candidates,
        p341.phase32_naive_candidates,
    )
    for builder in builders:
        for candidate, _metadata in builder():
            preimage = candidate.encode("utf-8")
            yield preimage
            yield hashlib.sha256(preimage).hexdigest().encode("ascii")


def _phase416_tested_materials():
    """The four exact promoted preimages recorded verbatim in P00416."""
    from data import VALIDATION_NUM

    preimages = (
        VALIDATION_NUM,
        "afubcdkingoraclequeenthingkymvpsonasadboardbutaswideasthefirstoneseen",
        "oneforonefourforone",
        "raisingthestakeswithoutextrachancesofwinning",
    )
    for candidate in preimages:
        preimage = candidate.encode("utf-8")
        yield preimage
        yield hashlib.sha256(preimage).hexdigest().encode("ascii")


def _phase421_evaluated_materials():
    """Reconstruct P421's eight evaluated preimages from its pinned hashes."""
    import phase421_execution_replay as p421

    result = json.loads((SCRIPT_DIR / "phase421_result.json").read_text(encoding="utf-8"))
    wanted = {
        (row["candidate_length"], row["candidate_sha256"])
        for row in result["evaluations"]
    }
    recovered = {}
    for rows in p421.candidate_rows().values():
        for candidate in rows:
            preimage = candidate.encode("utf-8")
            key = (len(preimage), hashlib.sha256(preimage).hexdigest())
            if key in wanted:
                recovered[key] = preimage
    if set(recovered) != wanted:
        raise AssertionError(
            f"P421 evaluated-preimage reconstruction drift: recovered "
            f"{len(recovered)} of {len(wanted)} pinned records"
        )
    for preimage in recovered.values():
        yield preimage
        yield hashlib.sha256(preimage).hexdigest().encode("ascii")

def compare_phase478(targets, matches):
    wanted = {
        base64.b64encode(material).decode("ascii"): material
        for material in targets
    }
    records = 0
    eligible_records = 0
    found = set()
    with PHASE478_MANIFEST.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if "bytes_b64" not in row:
                continue
            records += 1
            if row.get("eligible") is True:
                eligible_records += 1
            encoded = row["bytes_b64"]
            material = wanted.get(encoded)
            if material is None:
                continue
            found.add(material)
            matches.append({
                "source": "P478_manifest",
                "material_b64": encoded,
                "targets": targets[material],
                "provenance_source_file": row.get("source_file"),
                "eligible": row.get("eligible"),
            })
    return {
        "candidate_records": records,
        "eligible_records": eligible_records,
        "matched_materials": len(found),
    }


def audit():
    targets = proposed_materials()
    matches: list[dict] = []
    sources = {}

    sources["P478_manifest"] = compare_phase478(targets, matches)
    p478_counts = sources["P478_manifest"]
    if (
        p478_counts["candidate_records"],
        p478_counts["eligible_records"],
    ) != (1_749_878, 1_749_878):
        raise AssertionError(f"P478 manifest corpus drift: {p478_counts}")

    sources["historical_648_normalized"] = _record_matches(
        "historical_648_normalized",
        (keystring.encode("utf-8") for _, _, keystring in normalized_keystrings(
            load_curated_candidates(), whitespace_variants=False
        )),
        targets,
        matches,
    )

    v2_candidates = active_lines(V2_FULL)
    sources["V2_full_normalized"] = _record_matches(
        "V2_full_normalized",
        (keystring.encode("utf-8") for _, _, keystring in normalized_keystrings(
            v2_candidates, whitespace_variants=False
        )),
        targets,
        matches,
    )

    # Reproduce Phase 94's actual loader exactly. It did not skip comment
    # lines, so four OCR provenance headers were historically tested as
    # candidates and account for 99 of the 525,436 unique password forms.
    tier1_candidates = load_candidates(MEDIUM_TIER1)
    sources["historical_Tier1_normalized"] = _record_matches(
        "historical_Tier1_normalized",
        (keystring.encode("utf-8") for _, _, keystring in normalized_keystrings(
            tier1_candidates, whitespace_variants=False
        )),
        targets,
        matches,
    )

    for source, materials in _phase_specific_sources():
        sources[source] = _record_matches(source, materials, targets, matches)

    sources["P341_calibration_nonquery"] = _record_matches(
        "P341_calibration_nonquery",
        _phase341_calibration_materials(),
        targets,
        matches,
    )

    sources["P416_evaluated"] = _record_matches(
        "P416_evaluated",
        _phase416_tested_materials(),
        targets,
        matches,
    )

    sources["P421_evaluated"] = _record_matches(
        "P421_evaluated",
        _phase421_evaluated_materials(),
        targets,
        matches,
    )
    sources["P421_submitted_candidate_superset"] = _record_matches(
        "P421_submitted_candidate_superset",
        _phase421_candidate_superset(),
        targets,
        matches,
    )

    expected_counts = {
        "P265": 105,
        "P266": 119,
        "P267": 2196,
        "P268-P269": 1362,
        "P270": 50,
        "P314": 72,
        "P317": 10080,
        "P370_nonquery_manifest": 4,
        "P341_calibration_nonquery": 60,
        "P416_evaluated": 8,
        "P421_evaluated": 16,
        "P421_submitted_candidate_superset": 27,
        "historical_648_normalized": 14551,
        "V2_full_normalized": 14272,
        "historical_Tier1_normalized": 525436,
    }
    for source, expected in expected_counts.items():
        actual = sources[source]["unique_materials"]
        if actual != expected:
            raise AssertionError(
                f"{source} comparator drift: expected {expected} unique materials, got {actual}"
            )

    matched_target_b64 = {row["material_b64"] for row in matches}
    target_rows = []
    for material, labels in targets.items():
        encoded = base64.b64encode(material).decode("ascii")
        target_rows.append({
            "labels": labels,
            "length": len(material),
            "sha256": hashlib.sha256(material).hexdigest(),
            "material_b64": encoded,
            "historical_match": encoded in matched_target_b64,
        })

    return {
        "purpose": "historical exact-byte novelty comparison only; no oracle",
        "target_count": len(targets),
        "targets": target_rows,
        "sources": sources,
        "matches": matches,
        "matched_target_count": len(matched_target_b64),
        "novel_target_count": len(targets) - len(matched_target_b64),
        "oracle_calls": 0,
    }


def self_test():
    preimages = proposed_preimages()
    assert len(preimages) == 4
    assert len(set(preimages.values())) == 4
    assert len(proposed_materials()) == 8
    assert len(preimages["prize_then_halving"]) == 68
    assert len(PUZZLE_BANNER) == 25
    assert len(preimages["banner_prize_halving"]) == 93
    assert preimages["prize_then_halving"] == (
        PRIZE_ADDRESS + HALVING_ADDRESS
    ).encode("ascii")
    assert preimages["halving_then_prize"] == (
        HALVING_ADDRESS + PRIZE_ADDRESS
    ).encode("ascii")
    print("[*] Phase 480 address novelty comparator self-test passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
