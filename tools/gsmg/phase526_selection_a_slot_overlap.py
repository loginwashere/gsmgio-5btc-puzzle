#!/usr/bin/env python3
"""Phase 526A: expanded-material overlap for Selection-A coordinate values.

This module performs no decryption and imports no oracle entrypoint.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import phase523_slot_grammar_overlap_audit as p523  # noqa: E402

P525_RESULT = SCRIPT_DIR / "phase525_selection_a_result.json"
P524_BASES = REPO_ROOT / "_work/phase524/bases.txt"
P478_MANIFEST = SCRIPT_DIR / "phase478_manifest.jsonl"
WORK_DIR = REPO_ROOT / "_work/phase526"

EXPECTED_HASHES = {
    "phase525_result": "82a46dc6c4077ee5626d0578d465ebaf64e141d6627e94848ef34483d02e9253",
    "phase524_bases": "5193ff5249d5444d20707f21de7cd8a668f6714fb00623a12a63e9e995290bdc",
    "phase478_manifest": "0952c327a310b8956fd128d6b6c82581bfdc217188a4d4043fbe19779b4c0145",
}
COORDINATE_LABELS = (
    "selected_coordinates_row_col_pairs",
    "spiral_0_sum",
    "spiral_0_list_compact",
    "spiral_0_list_comma",
    "spiral_1_sum",
    "spiral_1_list_compact",
    "spiral_1_list_comma",
    "row_1_sum",
    "row_1_list_compact",
    "row_1_list_comma",
    "column_1_sum",
    "column_1_list_compact",
    "column_1_list_comma",
    "row_col_flat_1_sum",
    "row_col_flat_1_list_compact",
    "row_col_flat_1_list_comma",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs() -> dict[str, str]:
    actual = {
        "phase525_result": sha256_file(P525_RESULT),
        "phase524_bases": sha256_file(P524_BASES),
        "phase478_manifest": sha256_file(P478_MANIFEST),
    }
    if actual != EXPECTED_HASHES:
        raise AssertionError(f"frozen input hash mismatch: {actual}")
    return actual


def coordinate_values() -> list[tuple[str, str]]:
    payload = json.loads(P525_RESULT.read_text(encoding="utf-8"))
    by_label = {record["label"]: record["value"] for record in payload["representations"]}
    if tuple(label for label in COORDINATE_LABELS if label not in by_label):
        raise AssertionError("a frozen coordinate label is missing")
    selected = [(by_label[label], f"Phase 525 Selection A: {label}") for label in COORDINATE_LABELS]
    values = [value for value, _ in selected]
    if len(values) != 16 or len(set(values)) != 16:
        raise AssertionError("coordinate value family is not 16 unique values")
    return selected


def enumerate_extension_bases() -> tuple[list[tuple[str, str, list[str]]], int]:
    values = p523.slot_values()
    values["matrixsumlist"] = coordinate_values()
    records = []
    seen: set[str] = set()
    duplicate_count = 0
    for cell_id, subset, separator in p523.cells():
        if "matrixsumlist" not in subset:
            continue
        for combo in itertools.product(*[values[slot] for slot in subset]):
            base = separator.join(value for value, _ in combo)
            if base in seen:
                duplicate_count += 1
                continue
            seen.add(base)
            records.append((cell_id, base, [source for _, source in combo]))
    return records, duplicate_count


def prior_material_keys() -> tuple[set[int], dict]:
    started = time.time()
    covered, source_summary = p523.build_tested(p523.COVERAGE_SOURCES)
    after_coverage = len(covered)
    # Phase 523 retains a source-provenance bitmask as each dictionary value.
    # Phase 526 needs only membership before merging later executed corpora.
    prior = set(covered)

    phase524_bases = 0
    phase524_expansions = 0
    with P524_BASES.open("r", encoding="utf-8") as handle:
        for line in handle:
            base = line.rstrip("\n").rstrip("\r")
            if not base:
                continue
            phase524_bases += 1
            for material in p523.expand_std(base, True):
                prior.add(p523._mkey(material))
                phase524_expansions += 1
    after_phase524 = len(prior)

    phase478_records = 0
    with P478_MANIFEST.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            phase478_records += 1
            raw = base64.b64decode(json.loads(line)["bytes_b64"])
            digest = hashlib.blake2b(raw, digest_size=8).digest()
            prior.add(int.from_bytes(digest, "big"))
    return prior, {
        "coverage_source_count": len(source_summary),
        "coverage_material_keys": after_coverage,
        "phase524_bases": phase524_bases,
        "phase524_expansions_seen": phase524_expansions,
        "material_keys_after_phase524": after_phase524,
        "phase478_records": phase478_records,
        "union_material_keys": len(prior),
        "seconds": round(time.time() - started, 3),
    }


def run(write: bool = True) -> dict:
    hashes = verify_inputs()
    records, duplicates = enumerate_extension_bases()
    prior, comparator_counts = prior_material_keys()
    scheduled: set[int] = set()
    kept: list[str] = []
    candidate_expansions = 0
    candidate_unique_materials: set[int] = set()
    source_value_base_counts = {label: 0 for label in COORDINATE_LABELS}
    source_value_kept_counts = {label: 0 for label in COORDINATE_LABELS}
    for _cell, base, provenance in records:
        source = next(item for item in provenance if item.startswith("Phase 525 Selection A:"))
        label = source.split(": ", 1)[1]
        source_value_base_counts[label] += 1
        materials = p523.expand_std(base, True)
        keys = {p523._mkey(material) for material in materials}
        candidate_expansions += len(materials)
        candidate_unique_materials.update(keys)
        fresh = keys - prior - scheduled
        if fresh:
            kept.append(base)
            source_value_kept_counts[label] += 1
            scheduled.update(fresh)

    text = "\n".join(kept) + ("\n" if kept else "")
    report = {
        "phase": "526A",
        "scope": "oracle-free expanded-material overlap for Selection-A coordinate slot values",
        "input_hashes": hashes,
        "coordinate_labels": list(COORDINATE_LABELS),
        "coordinate_values": {label: value for (value, _), label in zip(coordinate_values(), COORDINATE_LABELS)},
        "candidate_bases_before_dedupe": 112_624,
        "candidate_base_duplicates": duplicates,
        "candidate_bases_unique": len(records),
        "candidate_expansions": candidate_expansions,
        "candidate_unique_material_keys": len(candidate_unique_materials),
        "comparators": comparator_counts,
        "retained_covering_bases": len(kept),
        "unique_fresh_material_keys": len(scheduled),
        "retained_base_list_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "source_value_base_counts": source_value_base_counts,
        "source_value_kept_counts": source_value_kept_counts,
        "oracle_calls": 0,
        "disposition": (
            "Stop after overlap inventory. Nonzero fresh material licenses only a "
            "separately locked SALPH-primary execution phase."
        ),
    }
    if write:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        (WORK_DIR / "bases.txt").write_text(text, encoding="utf-8")
        (WORK_DIR / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def self_test() -> dict:
    values = coordinate_values()
    if len(values) != 16:
        raise AssertionError("coordinate value count drifted")
    records, duplicates = enumerate_extension_bases()
    if len(records) + duplicates != 112_624:
        raise AssertionError("extension grammar size drifted")
    if any("MSL" not in cell for cell, _base, _prov in records):
        raise AssertionError("extension emitted a cell without matrixsumlist")
    if any(len([p for p in provenance if p.startswith("Phase 525 Selection A:")]) != 1 for _, _, provenance in records):
        raise AssertionError("extension base does not contain exactly one new source value")
    namespace = globals()
    forbidden = ("aes_try_open_bytes", "aes_try_open_stream_bytes", "raw_key_try_open")
    if any(name in namespace for name in forbidden):
        raise AssertionError("oracle function leaked into overlap module")
    return {"ok": True, "checks": 5, "unique_bases": len(records), "duplicates": duplicates}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if args.run:
        print(json.dumps(run(), indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
