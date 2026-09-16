#!/usr/bin/env python3
"""Phase 510A: construct the provenance-locked closed vocabulary manifest."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
from pathlib import Path

from cb_common import _load_blob
from data import PHASE32_BLOB_B64, VALIDATION_ANSWER
import phase410_solved_vector_toolchain_provenance_audit as phase410
from phase468_known_parts_catalog import ESTABLISHED_OUTPUTS


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 510A Closed-System Vocabulary Manifest Protocol.md")
MANIFEST = SCRIPT_DIR / "phase510a_vocabulary_manifest.json"
TOKEN_RE = re.compile(rb"[A-Za-z]+")
MIN_LENGTH = 5


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(Path(path).read_bytes())


def solved_plaintexts() -> dict[str, bytes]:
    textareas = phase410.extract_wayback_textareas(phase410.WAYBACK_ARTIFACT_PATH)
    out = {}
    for key, spec in phase410.VECTORS.items():
        encoded = (textareas[spec["textarea_index"]].decode("ascii")
                   if spec["textarea_index"] is not None else PHASE32_BLOB_B64)
        salt, ciphertext = _load_blob(encoded)
        password = hashlib.sha256(spec["preimage"].encode("utf-8")).hexdigest().encode("ascii")
        _, _, plaintext = phase410.decrypt_container(
            salt, ciphertext, password, "sha256")
        if plaintext is None or not plaintext.startswith(spec["expected_plaintext_prefix"]):
            raise RuntimeError(f"Phase-410 plaintext recovery failed: {key}")
        out[key] = plaintext
    expected = {
        "phase2": "e2f9dd65604a3231f8b3301724e8d713a88fffc4b6c7c4aeeb20f58a582b593a",
        "phase3": "c4ad94559a44a927c1032cc0e024515f9510a0806a2d14458dbf4a360af9865f",
        "phase32": "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34",
    }
    if {key: sha_bytes(value) for key, value in out.items()} != expected:
        raise RuntimeError("solved plaintext hashes changed")
    return out


def literal_regions() -> dict[str, bytes]:
    plaintexts = solved_plaintexts()
    phase3_marker = b"\nU2FsdGVk"
    if plaintexts["phase3"].count(phase3_marker) != 1:
        raise RuntimeError("Phase-3 embedded-ciphertext boundary changed")
    phase3_literal = plaintexts["phase3"].split(phase3_marker, 1)[0]

    phase32 = plaintexts["phase32"]
    if len(phase32) != 2422 or phase32[447:1986] == b"":
        raise RuntimeError("Phase-3.2 literal/binary boundaries changed")
    tail = phase32[1986:]
    if tail.count(phase3_marker) != 1:
        raise RuntimeError("Phase-3.2 trailing-ciphertext boundary changed")
    phase32_literal = phase32[:447] + b"\n" + tail.split(phase3_marker, 1)[0]

    ciao = next(row for row in ESTABLISHED_OUTPUTS if row["id"] == "ciao_bella_o")
    if ciao["evidence_class"] != "authenticated_output":
        raise RuntimeError("CIAO BELLA O evidence class changed")
    return {
        "phase2_solved_plaintext": plaintexts["phase2"],
        "phase3_literal_plaintext": phase3_literal,
        "phase32_literal_plaintext": phase32_literal,
        "ciao_bella_o": ciao["value"].encode("ascii"),
    }


def tokens(value: bytes) -> list[str]:
    return [match.group().decode("ascii").lower()
            for match in TOKEN_RE.finditer(value)
            if len(match.group()) >= MIN_LENGTH]


def exact_sequences() -> list[dict]:
    sequences = {
        "phase2_preimage": phase410.VECTORS["phase2"]["preimage"].encode("utf-8"),
        "phase3_preimage": phase410.VECTORS["phase3"]["preimage"].encode("utf-8"),
        "phase32_preimage": phase410.VECTORS["phase32"]["preimage"].encode("utf-8"),
        "phase322_answer_unspaced": VALIDATION_ANSWER.encode("ascii"),
    }
    return [{
        "id": key,
        "length": len(value),
        "sha256": sha_bytes(value),
        "role": "exact_sequence_control_not_word_segmented",
    } for key, value in sorted(sequences.items())]


def build_manifest() -> dict:
    regions = literal_regions()
    per_source = {key: tokens(value) for key, value in regions.items()}
    term_sources: dict[str, set[str]] = collections.defaultdict(set)
    term_counts = collections.Counter()
    per_source_counts = {}
    for source_id, source_tokens in per_source.items():
        term_counts.update(source_tokens)
        for term in source_tokens:
            term_sources[term].add(source_id)
        other_terms = set().union(*(
            set(values) for other, values in per_source.items()
            if other != source_id))
        covered = sum(term in other_terms for term in source_tokens)
        per_source_counts[source_id] = {
            "literal_region_length": len(regions[source_id]),
            "literal_region_sha256": sha_bytes(regions[source_id]),
            "retained_token_occurrences": len(source_tokens),
            "unique_terms": len(set(source_tokens)),
            "leave_one_document_out_covered_occurrences": covered,
            "leave_one_document_out_coverage": (
                covered / len(source_tokens) if source_tokens else 0.0),
        }
    terms = [{
        "term": term,
        "length": len(term),
        "proposed_length_weight": (len(term) - 4) ** 2,
        "occurrences": term_counts[term],
        "document_frequency": len(term_sources[term]),
        "source_ids": sorted(term_sources[term]),
    } for term in sorted(term_counts)]
    return {
        "phase": "510A",
        "status": "closed_vocabulary_manifest_no_scoring",
        "faed_imported_or_scored": False,
        "minimum_term_length": MIN_LENGTH,
        "normalization": "maximal ASCII [A-Za-z]+ runs, lowercase",
        "proposed_weight": "(length - 4)^2; not authorized for scoring until Phase 510B",
        "source_count": len(regions),
        "source_diagnostics": per_source_counts,
        "term_count": len(terms),
        "terms": terms,
        "exact_sequences": exact_sequences(),
        "exclusions": [
            "findings and brainstorm prose",
            "solver-generated FAED plaintexts",
            "community suggestions and recognition-only terms",
            "dictionaries, password lists, synonyms, stemming, typo repair, OCR",
            "inferred boundaries inside unspaced sequences",
            "Base58 or hex syntax without a compatible representation rule",
        ],
        "input_hashes": {
            "protocol": sha(PROTOCOL),
            "phase410_runner": sha(Path(phase410.__file__)),
            "phase410_wayback_artifact": sha(phase410.WAYBACK_ARTIFACT_PATH),
            "phase468_catalog": sha(SCRIPT_DIR / "phase468_known_parts_catalog.py"),
            "data": sha(SCRIPT_DIR / "data.py"),
        },
    }


def validate_manifest() -> dict:
    if not MANIFEST.is_file():
        raise RuntimeError("Phase-510A manifest is absent")
    actual = json.loads(MANIFEST.read_text())
    if actual != build_manifest():
        raise RuntimeError("Phase-510A manifest mismatch")
    return actual


def atomic_json(path: Path, value: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def self_test() -> dict:
    value = build_manifest()
    if value["term_count"] != 108:
        raise AssertionError(f"expected 108 terms, got {value['term_count']}")
    expected_tokens = {
        "phase2_solved_plaintext": 39,
        "phase3_literal_plaintext": 41,
        "phase32_literal_plaintext": 34,
        "ciao_bella_o": 1,
    }
    actual = {key: row["retained_token_occurrences"]
              for key, row in value["source_diagnostics"].items()}
    if actual != expected_tokens:
        raise AssertionError(f"source token counts changed: {actual}")
    if any(row["leave_one_document_out_coverage"] > 0.08
           for row in value["source_diagnostics"].values()):
        raise AssertionError("coverage diagnostic unexpectedly changed")
    forbidden = {"youwon", "matrixsumlist", "lastwordsbeforearchichoice"}
    if forbidden & {row["term"] for row in value["terms"]}:
        raise AssertionError("excluded recognition/community term entered vocabulary")
    return {
        "self_test": "pass", "term_count": 108,
        "source_count": 4, "maximum_leave_one_out_coverage": max(
            row["leave_one_document_out_coverage"]
            for row in value["source_diagnostics"].values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--write-manifest", action="store_true")
    group.add_argument("--verify-manifest", action="store_true")
    group.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.write_manifest:
        if MANIFEST.exists():
            raise FileExistsError("refusing to overwrite Phase-510A manifest")
        value = build_manifest()
        atomic_json(MANIFEST, value)
        value = {"manifest_sha256": sha(MANIFEST),
                 "term_count": value["term_count"]}
    elif args.verify_manifest:
        value = validate_manifest()
    else:
        built = build_manifest()
        value = {key: built[key] for key in (
            "phase", "status", "source_count", "term_count",
            "source_diagnostics", "exclusions")}
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
