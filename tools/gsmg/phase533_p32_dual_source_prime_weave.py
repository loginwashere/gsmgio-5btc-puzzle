#!/usr/bin/env python3
"""Phase 533: locked P32 dual-source-code prime/weave audit."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from data import P32_TRAILING_BLOB_B64, VALIDATION_NUM
from p32_sibling_password_audit import (
    decrypt_phase32_bytes,
    derive_sibling_outputs,
    ebcdic_1141_ciphertext,
    extract_phase32_components,
    password_materials,
    structural_trials,
)
from phase442_prime_basics_representation_precedent_audit import (
    existing_phase270_materials,
    split_final_be_colors,
)
from phase443_answer321_prime_basics_followup import (
    phase442_material_values,
    build_answer321_candidate_family,
)
from phase444_source_bound_and_or_rail_audit import (
    build_candidates as build_phase444_candidates,
    derive_sources,
    split_rails,
)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL_PATH = (
    REPO_ROOT
    / "doc/Brainstorms/2026-09-20 - Phase 533 P32 Dual Source-Code Prime Weave Protocol.md"
)
LOCK_PATH = SCRIPT_DIR / "phase533_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase533_p32_dual_source_prime_weave_result.json"

EXPECTED_COLORS = "BBBBYBBBYYBBBBYBBYYBBYB"
EXPECTED_CP1141 = "tkpmhlwzjputuzfytnlfajfkloewwu"
EXPECTED_DIGITS = "515419219215114118132941773106"
EXPECTED_DIGIT_BLUE = "5154219141132736"
EXPECTED_DIGIT_YELLOW = "19215181941710"
EXPECTED_WEAVE_CP_DIGIT = (
    "t5k1p5m4hl19w2z1j9pu21tu51z1f4y1t1nl81f3a2jf94kl17o7e3ww10u6"
)
EXPECTED_WEAVE_DIGIT_CP = (
    "5t1k5p4m19hl2w1z9j21pu51tu1z4f1y1t81nl3f2a94jf17kl7o3e10ww6u"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(records: tuple[dict, ...]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(record["label"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(record["value"])
        digest.update(b"\n")
    return digest.hexdigest()


def source_chunks(source: str, colors: str) -> tuple[str, ...]:
    _rails, records = split_rails(source, colors)
    return tuple(record["selected"] for record in records)


def build_bases() -> tuple[dict, ...]:
    derived = derive_sibling_outputs()
    raw_block = extract_phase32_components(decrypt_phase32_bytes())["encoded_321"]
    cp1141 = ebcdic_1141_ciphertext(raw_block)
    colors = split_final_be_colors()
    cp_rails, _cp_records = split_rails(cp1141, colors)
    digit_rails, _digit_records = split_rails(VALIDATION_NUM, colors)
    cp_chunks = source_chunks(cp1141, colors)
    digit_chunks = source_chunks(VALIDATION_NUM, colors)
    weave_cp_digit = "".join(a + b for a, b in zip(cp_chunks, digit_chunks))
    weave_digit_cp = "".join(b + a for a, b in zip(cp_chunks, digit_chunks))

    values = (
        ("digit_event_order", digit_rails["intertwined"]),
        ("digit_blue_only", digit_rails["blue_only"]),
        ("digit_yellow_only", digit_rails["yellow_only"]),
        ("digit_blue_then_yellow", digit_rails["blue_then_yellow"]),
        ("cp1141_then_digit", cp_rails["intertwined"] + digit_rails["intertwined"]),
        ("digit_then_cp1141", digit_rails["intertwined"] + cp_rails["intertwined"]),
        ("event_weave_cp1141_digit", weave_cp_digit),
        ("event_weave_digit_cp1141", weave_digit_cp),
    )
    return tuple({"label": label, "value": value.encode("ascii")} for label, value in values)


def build_material_records() -> tuple[dict, ...]:
    candidates = tuple(
        {"labels": (base["label"],), "value": base["value"]} for base in build_bases()
    )
    records = []
    for entry in password_materials(candidates):
        records.append(
            {
                "label": entry["sources"][0] + ":" + entry["treatments"][0],
                "value": entry["material"],
                "sources": entry["sources"],
                "treatments": entry["treatments"],
            }
        )
    return tuple(records)


def phase444_material_values() -> set[bytes]:
    derived, sources = derive_sources()
    colors = split_final_be_colors()
    source_rails = {name: split_rails(value, colors)[0] for name, value in sources.items()}
    candidates = build_phase444_candidates(
        derived["answer_321"], derived["answer_322"], source_rails
    )
    return {entry["material"] for entry in password_materials(candidates)}


def phase443_material_values(answer_321: str, answer_322: str) -> set[bytes]:
    colors = split_final_be_colors()
    selection = split_rails(answer_321, colors)[0]["intertwined"]
    candidates = build_answer321_candidate_family(answer_321, answer_322, selection)
    return {entry["material"] for entry in password_materials(candidates)}


def overlap_report(records: tuple[dict, ...]) -> dict:
    derived = derive_sibling_outputs()
    prior = {
        "phase270": existing_phase270_materials(),
        "phase442": phase442_material_values(
            derived["answer_321"], derived["answer_322"]
        ),
        "phase443": phase443_material_values(
            derived["answer_321"], derived["answer_322"]
        ),
        "phase444": phase444_material_values(),
    }
    return {
        phase: [record["label"] for record in records if record["value"] in values]
        for phase, values in prior.items()
    }


def manifest() -> dict:
    bases = build_bases()
    materials = build_material_records()
    overlaps = overlap_report(materials)
    overlap_labels = {label for labels in overlaps.values() for label in labels}
    fresh = tuple(record for record in materials if record["label"] not in overlap_labels)
    return {
        "colors": split_final_be_colors(),
        "bases": [
            {
                "label": base["label"],
                "length": len(base["value"]),
                "sha256": hashlib.sha256(base["value"]).hexdigest(),
                "ascii": base["value"].decode("ascii"),
            }
            for base in bases
        ],
        "base_count": len(bases),
        "material_count": len(materials),
        "overlap_labels": overlaps,
        "fresh_material_count": len(fresh),
        "fresh_material_digest": canonical_digest(fresh),
        "fresh_records": fresh,
    }


def self_test() -> None:
    data = manifest()
    bases = {entry["label"]: entry["ascii"] for entry in data["bases"]}
    assert data["colors"] == EXPECTED_COLORS
    assert bases["digit_event_order"] == EXPECTED_DIGITS
    assert bases["digit_blue_only"] == EXPECTED_DIGIT_BLUE
    assert bases["digit_yellow_only"] == EXPECTED_DIGIT_YELLOW
    assert bases["event_weave_cp1141_digit"] == EXPECTED_WEAVE_CP_DIGIT
    assert bases["event_weave_digit_cp1141"] == EXPECTED_WEAVE_DIGIT_CP
    assert bases["cp1141_then_digit"].startswith(EXPECTED_CP1141)
    assert data["base_count"] == 8
    assert data["material_count"] == 16
    assert not any(data["overlap_labels"].values())
    assert data["fresh_material_count"] == 16


def lock_payload() -> dict:
    data = manifest()
    raw_p32 = base64.b64decode(P32_TRAILING_BLOB_B64, validate=True)
    return {
        "phase": 533,
        "script_sha256": sha256_file(Path(__file__)),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "evidence_sha256": {
            name: sha256_file(SCRIPT_DIR / "findings" / name)
            for name in ("P00270.md", "P00442.md", "P00443.md", "P00444.md")
        },
        "p32_envelope_sha256": hashlib.sha256(raw_p32).hexdigest(),
        "colors": data["colors"],
        "base_count": data["base_count"],
        "fresh_material_count": data["fresh_material_count"],
        "fresh_material_digest": data["fresh_material_digest"],
        "kdf_spec_count": 6,
        "expected_trial_count": data["fresh_material_count"] * 6,
    }


def write_lock() -> None:
    self_test()
    if LOCK_PATH.exists():
        raise RuntimeError("Phase-533 execution lock already exists")
    LOCK_PATH.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")


def verify_lock() -> dict:
    if not LOCK_PATH.exists():
        raise RuntimeError("Phase-533 execution lock is absent")
    saved = json.loads(LOCK_PATH.read_text())
    current = lock_payload()
    if saved != current:
        raise RuntimeError("Phase-533 execution lock mismatch")
    return saved


def run() -> dict:
    lock = verify_lock()
    data = manifest()
    entries = tuple(
        {
            "material": record["value"],
            "sources": list(record["sources"]),
            "treatments": list(record["treatments"]),
        }
        for record in data["fresh_records"]
    )
    structural = structural_trials(entries)
    result = {
        "phase": 533,
        "lock_sha256": sha256_file(LOCK_PATH),
        "base_count": data["base_count"],
        "material_count": data["fresh_material_count"],
        "material_digest": data["fresh_material_digest"],
        "overlap_labels": data["overlap_labels"],
        "trial_count": structural["trial_count"],
        "hit_count": len(structural["hits"]),
        "hits": structural["hits"],
        "disposition": (
            "promoted_exact_two_key_padding_hit"
            if structural["hits"]
            else "bounded_negative_dual_source_prime_weave"
        ),
        "scope": "eight frozen bases; raw and sha256-hex; six Phase-270 KDF specs; P32 only",
        "expected_trial_count": lock["expected_trial_count"],
    }
    if result["trial_count"] != result["expected_trial_count"]:
        raise AssertionError("trial count differs from locked expectation")
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--verify-lock", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    selected = sum((args.self_test, args.write_lock, args.verify_lock, args.run))
    if selected != 1:
        parser.error("choose exactly one action")
    if args.self_test:
        self_test()
        print("[*] Phase 533 self-test passed")
    elif args.write_lock:
        write_lock()
        print(f"[*] wrote {LOCK_PATH}")
    elif args.verify_lock:
        verify_lock()
        print("[*] Phase 533 execution lock verified")
    else:
        result = run()
        print(json.dumps({key: result[key] for key in ("trial_count", "hit_count", "disposition")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
