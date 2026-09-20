#!/usr/bin/env python3
"""Phase 529: oracle-free overlap audit for Phase 528 payload materials."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import phase523_slot_grammar_overlap_audit as p523  # noqa: E402

P528_RESULT = SCRIPT_DIR / "phase528_dbbi_84_token_consequence_result.json"
P524_BASES = REPO_ROOT / "_work/phase524/bases.txt"
P527_BASES = REPO_ROOT / "_work/phase526/bases.txt"
P478_MANIFEST = SCRIPT_DIR / "phase478_manifest.jsonl"
WORK_DIR = REPO_ROOT / "_work/phase529"
RESULT_PATH = SCRIPT_DIR / "phase529_dbbi_payload_material_overlap_result.json"

EXPECTED_HASHES = {
    "phase528_result": "ac30ee6810e85a62ac29028c18321f1dde2a5919cbc01bfdc6d49d8e84f4a86b",
    "phase524_executed_bases": "5193ff5249d5444d20707f21de7cd8a668f6714fb00623a12a63e9e995290bdc",
    "phase527_executed_bases": "800e7a181a015416725d399059e8369c556a4f9e4e2fffe9e71f18f9fcd7ea36",
    "phase478_manifest": "0952c327a310b8956fd128d6b6c82581bfdc217188a4d4043fbe19779b4c0145",
}

BASE_LABELS = (
    "parse84_full_residue_61",
    "parse84_b_host_payload_rail",
    "parse84_be_host_payload_rail",
    "parse84_b_then_be_payload_rails",
    "parse84_be_then_b_payload_rails",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs() -> dict[str, str]:
    actual = {
        "phase528_result": sha256_file(P528_RESULT),
        "phase524_executed_bases": sha256_file(P524_BASES),
        "phase527_executed_bases": sha256_file(P527_BASES),
        "phase478_manifest": sha256_file(P478_MANIFEST),
    }
    if actual != EXPECTED_HASHES:
        raise AssertionError(f"frozen input hash mismatch: {actual}")
    return actual


def frozen_bases() -> dict[str, str]:
    result = json.loads(P528_RESULT.read_text(encoding="utf-8"))
    objects = result["exact_objects"]
    bases = {label: objects[label] for label in BASE_LABELS}
    if len(bases) != 5 or len(set(bases.values())) != 5:
        raise AssertionError("Phase 529 base family is not five unique values")
    if any(not value.isalpha() or not value.islower() for value in bases.values()):
        raise AssertionError("Phase 529 bases must remain lowercase pure letters")
    return bases


def candidate_materials() -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    by_base: dict[str, dict[str, str]] = {}
    material_sources: dict[str, list[str]] = {}
    for label, base in frozen_bases().items():
        tagged = p523.tagged_materials(base)
        if set(tagged) != p523.expand_std(base, True):
            raise AssertionError(f"tagged expansion differs for {label}")
        if len(tagged) != 18:
            raise AssertionError(f"{label} emitted {len(tagged)} forms instead of 18")
        by_base[label] = dict(sorted(tagged.items()))
        for material in tagged:
            material_sources.setdefault(material, []).append(label)
    if len(material_sources) != 90:
        raise AssertionError(f"candidate material union drifted: {len(material_sources)}")
    return by_base, material_sources


def exact_source_hits(source: dict, targets: set[str]) -> set[str]:
    hits: set[str] = set()
    for base in source["loader"]():
        hits.update(targets.intersection(p523._expand_source(source, base)))
    return hits


def scan_historical(targets: set[str]) -> dict:
    tested, summaries = p523.build_tested(p523.COVERAGE_SOURCES)
    target_by_key = {p523._mkey(material): material for material in targets}
    key_hits = {key for key in target_by_key if key in tested}
    exact_hits: set[str] = set()
    exact_sources: dict[str, list[str]] = {}
    if key_hits:
        keyed_targets = {target_by_key[key] for key in key_hits}
        for source in p523.COVERAGE_SOURCES:
            source_hits = exact_source_hits(source, keyed_targets)
            for material in source_hits:
                exact_hits.add(material)
                exact_sources.setdefault(material, []).append(source["name"])
    return {
        "source_count": len(summaries),
        "material_keys": len(tested),
        "target_key_hits": len(key_hits),
        "exact_hits": sorted(exact_hits),
        "exact_sources": exact_sources,
    }


def scan_base_file(path: Path, targets: set[str]) -> dict:
    target_by_key = {p523._mkey(material): material for material in targets}
    key_hits: set[int] = set()
    exact_hits: set[str] = set()
    bases = 0
    expansions = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            base = line.rstrip("\n").rstrip("\r")
            if not base:
                continue
            bases += 1
            materials = p523.expand_std(base, True)
            expansions += len(materials)
            for material in materials:
                key = p523._mkey(material)
                if key in target_by_key:
                    key_hits.add(key)
                    if material == target_by_key[key]:
                        exact_hits.add(material)
    return {
        "bases": bases,
        "expansions_seen": expansions,
        "target_key_hits": len(key_hits),
        "exact_hits": sorted(exact_hits),
    }


def scan_phase478(targets: set[str]) -> dict:
    target_bytes = {material.encode("utf-8"): material for material in targets}
    hits: set[str] = set()
    records = 0
    with P478_MANIFEST.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records += 1
            raw = base64.b64decode(json.loads(line)["bytes_b64"])
            if raw in target_bytes:
                hits.add(target_bytes[raw])
    return {"records": records, "exact_hits": sorted(hits)}


def audit(write: bool = True) -> dict:
    started = time.time()
    hashes = verify_inputs()
    by_base, sources = candidate_materials()
    targets = set(sources)
    comparators = {
        "phase523_historical": scan_historical(targets),
        "phase524_executed": scan_base_file(P524_BASES, targets),
        "phase527_executed": scan_base_file(P527_BASES, targets),
        "phase478_submitted": scan_phase478(targets),
    }
    covered = set()
    for comparator in comparators.values():
        covered.update(comparator["exact_hits"])
    fresh = sorted(targets - covered)
    manifest = []
    for material in sorted(targets):
        manifest.append(
            {
                "material": material,
                "material_sha256": hashlib.sha256(material.encode()).hexdigest(),
                "source_bases": sorted(sources[material]),
                "derivation_tags": sorted(
                    by_base[label][material]
                    for label in sources[material]
                ),
                "covered": material in covered,
            }
        )
    report = {
        "phase": 529,
        "scope": "oracle-free solved-boundary material overlap for Phase-528 payload objects",
        "input_hashes": hashes,
        "base_labels": list(BASE_LABELS),
        "bases": frozen_bases(),
        "forms_per_base": {label: len(forms) for label, forms in by_base.items()},
        "candidate_forms_total": sum(len(forms) for forms in by_base.values()),
        "candidate_materials_unique": len(targets),
        "comparators": comparators,
        "covered_materials": len(covered),
        "fresh_materials": len(fresh),
        "all_five_bases_retain_fresh_material": all(
            any(material in fresh for material in forms) for forms in by_base.values()
        ),
        "manifest": manifest,
        "oracle_calls": 0,
        "elapsed_seconds": round(time.time() - started, 3),
        "disposition": (
            "stop_after_overlap_inventory; fresh material requires a separately "
            "named and execution-locked consumer"
        ),
    }
    if write:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        base_text = "\n".join(frozen_bases().values()) + "\n"
        (WORK_DIR / "bases.txt").write_text(base_text, encoding="utf-8")
        RESULT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def self_test() -> None:
    bases = frozen_bases()
    by_base, materials = candidate_materials()
    assert len(bases) == 5
    assert all(len(forms) == 18 for forms in by_base.values())
    assert len(materials) == 90
    assert not any(
        name in globals()
        for name in ("aes_try_open_bytes", "aes_try_open_stream_bytes", "raw_key_try_open")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 529 self-test passed")
        return 0
    if args.run:
        result = audit()
        print(json.dumps({k: result[k] for k in (
            "candidate_materials_unique", "covered_materials", "fresh_materials",
            "all_five_bases_retain_fresh_material", "elapsed_seconds", "oracle_calls",
        )}, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

