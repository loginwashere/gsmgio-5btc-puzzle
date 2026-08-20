#!/usr/bin/env python3
"""Seed 6: bounded multi-blob structural concordance audit.

Pre-registration (frozen before the real run):

* Corpus: the identical 42-candidate x literal/SHA256-passphrase x 54-variant
  x 4-blob retained-body universe used by Phases 336--338 and 342. No new
  candidates, KDFs, ciphers, modes, blobs, or retention rules.
* Unit: two independently decrypted blobs under the same candidate, material
  form, and exact crypto variant. Groups with fewer than two retained blobs do
  not contribute a pair.
* Whole-body feature registry only:
    1. complete parser-valid type, including one strict depth-one decode;
    2. a valid SHA256/SHA256d/CRC32 four-byte trailer family;
    3. exact delimiter geometry in the first 64 bytes, or exact fixed-width
       record geometry (both require at least two delimiters / three records);
    4. a secp256k1 scalar at offset 0 or 32 in one body whose compressed or
       uncompressed HASH160 occurs at offset 0, 20, 32, 44, or 64 in the
       other body.
  There is no language score, printability threshold, arbitrary substring
  scan, adaptive offset, or candidate-specific inspection.
* Statistic: the maximum number of registered exact-concordance events on any
  candidate/variant/blob pair. This single maximum automatically includes all
  feature families and offsets tested.
* Null: 1,000 deterministic label permutations. Within every
  (form, variant, blob) stratum, retained bodies are reassigned across the
  existing candidate-label slots. This preserves blob, cipher/mode, form,
  body length multiset, and the exact missing-retention pattern. Each trial
  records its global maximum, so the empirical p-value is family-wise:
  (1 + null maxima >= real maximum) / (1 + trials).
* Inspection gate: disclose candidate provenance only if p <= 0.05. Otherwise
  report aggregate maxima/histograms only. Stop after this one frozen run; do
  not add features or inspect a top candidate after seeing the result.

This is deliberately a safer precursor to D1's aggregate weak-language score,
not an implementation of D1.
"""

import argparse
import hashlib
import json
import random
import sys
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import private_key_details  # noqa: E402
from first_hint_hash_audit import SECP256K1_ORDER  # noqa: E402
from half_better_half_algebra_audit import (  # noqa: E402
    EXPECTED_CANDIDATE_DIGEST,
    candidate_list_digest,
    frozen_candidates,
)
from typed_decode_parse_ladder_audit import (  # noqa: E402
    DECODERS,
    is_parser_valid,
    iter_retained_bodies,
    validate_full,
    validate_structural,
)

NULL_TRIALS = 1_000
NULL_SEED = 20260820
ALPHA = 0.05
EXPECTED_BODY_COUNT = 12_128
DELIMITERS = frozenset(b"\n\r\t ,;:|/\\=()[]{}<>")
SCALAR_OFFSETS = (0, 32)
HASH160_OFFSETS = (0, 20, 32, 44, 64)


@dataclass(frozen=True)
class Features:
    validated_types: frozenset
    checksum_families: frozenset
    delimiter_geometry: tuple | None
    record_geometries: frozenset
    scalar_hash160s: tuple
    hash160_windows: tuple


@dataclass(frozen=True)
class Record:
    candidate_index: int
    candidate_model: str
    candidate_label: str
    candidate_sha256: str
    form_kind: str
    variant: str
    blob: str
    body_length: int
    body_sha256: str
    features: Features


def _structural_type_names(validation, prefix="raw"):
    names = set()
    if validation.get("der_ec") is not None:
        names.add(f"{prefix}:der_ec")
    if validation.get("psbt") is not None:
        names.add(f"{prefix}:psbt")
    if validation.get("bitcoin_tx") is not None:
        names.add(f"{prefix}:bitcoin_tx")
    if validation.get("salted_header"):
        names.add(f"{prefix}:salted_header")
    for key_format in validation.get("key_format_matches", []):
        names.add(f"{prefix}:key:{key_format}")
    return names


def validated_types(body):
    """Complete raw validators plus one strict whole-body decode hop."""
    names = _structural_type_names(validate_structural(body))
    for decoder_name, (trigger, decode) in DECODERS.items():
        if not trigger(body):
            continue
        decoded = decode(body)
        if decoded is None:
            continue
        validation = validate_full(decoded)
        if is_parser_valid(validation):
            names.update(_structural_type_names(validation, f"decoded:{decoder_name}"))
    return frozenset(names)


def checksum_families(body):
    if len(body) < 8:
        return frozenset()
    payload, trailer = body[:-4], body[-4:]
    out = set()
    if hashlib.sha256(payload).digest()[:4] == trailer:
        out.add("sha256_first4")
    if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] == trailer:
        out.add("sha256d_first4")
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    if crc.to_bytes(4, "little") == trailer:
        out.add("crc32_le")
    if crc.to_bytes(4, "big") == trailer:
        out.add("crc32_be")
    return frozenset(out)


def delimiter_geometry(body):
    geometry = tuple((offset, value) for offset, value in enumerate(body[:64]) if value in DELIMITERS)
    return geometry if len(geometry) >= 2 else None


def record_geometries(body):
    out = set()
    for name, separator in (("lf", b"\n"), ("nul", b"\x00"), ("pipe", b"|")):
        pieces = body.split(separator)
        if len(pieces) < 3:
            continue
        lengths = tuple(len(piece) for piece in pieces)
        if len(set(lengths)) == 1 and lengths[0] > 0:
            out.add((name, lengths[0], len(lengths)))
    return frozenset(out)


def scalar_hash160s(body):
    out = []
    for offset in SCALAR_OFFSETS:
        scalar = body[offset:offset + 32]
        if len(scalar) != 32:
            continue
        value = int.from_bytes(scalar, "big")
        if not 1 <= value < SECP256K1_ORDER:
            continue
        details = private_key_details(scalar)
        out.append((offset, "compressed", bytes.fromhex(details["compressed"]["hash160"])))
        out.append((offset, "uncompressed", bytes.fromhex(details["uncompressed"]["hash160"])))
    return tuple(out)


def hash160_windows(body):
    return tuple(
        (offset, body[offset:offset + 20])
        for offset in HASH160_OFFSETS
        if len(body[offset:offset + 20]) == 20
    )


def extract_features(body):
    return Features(
        validated_types(body),
        checksum_families(body),
        delimiter_geometry(body),
        record_geometries(body),
        scalar_hash160s(body),
        hash160_windows(body),
    )


def concordance_events(left, right):
    """Return exact registered pair events. Direction is made explicit for
    scalar->HASH160 relations; symmetric categorical matches are counted once."""
    events = set()
    for name in left.validated_types & right.validated_types:
        events.add(f"validated_type:{name}")
    for name in left.checksum_families & right.checksum_families:
        events.add(f"checksum_family:{name}")
    if left.delimiter_geometry is not None and left.delimiter_geometry == right.delimiter_geometry:
        events.add("delimiter_geometry:first64_exact")
    for geometry in left.record_geometries & right.record_geometries:
        events.add(f"record_geometry:{geometry[0]}:{geometry[1]}:{geometry[2]}")

    def directional(source, target, direction):
        for scalar_offset, encoding, value in source.scalar_hash160s:
            for target_offset, target_value in target.hash160_windows:
                if value == target_value:
                    events.add(
                        f"scalar_hash160:{direction}:scalar@{scalar_offset}:{encoding}"
                        f"->hash160@{target_offset}"
                    )

    directional(left, right, "left_to_right")
    directional(right, left, "right_to_left")
    return tuple(sorted(events))


def collect_records(blobs=None, candidates=None):
    records = []
    for index, model, label, candidate_sha256, form_kind, variant, blob, body in iter_retained_bodies(
            blobs=blobs, candidates=candidates):
        records.append(Record(
            index, model, label, candidate_sha256, form_kind, variant, blob,
            len(body), hashlib.sha256(body).hexdigest(), extract_features(body),
        ))
    return records


def _assignment_from_records(records):
    return {
        (record.form_kind, record.variant, record.blob, record.candidate_index): record
        for record in records
    }


def _score_assignment(assignment):
    groups = defaultdict(list)
    for (form, variant, _blob, candidate_index), record in assignment.items():
        groups[(candidate_index, form, variant)].append(record)

    maximum = 0
    maximizing = []
    pair_count = 0
    event_family_counts = Counter()
    for group_key, group_records in groups.items():
        ordered = sorted(group_records, key=lambda record: record.blob)
        for left_index in range(len(ordered)):
            for right_index in range(left_index + 1, len(ordered)):
                left, right = ordered[left_index], ordered[right_index]
                pair_count += 1
                events = concordance_events(left.features, right.features)
                for event in events:
                    event_family_counts[event.split(":", 1)[0]] += 1
                score = len(events)
                if score > maximum:
                    maximum = score
                    maximizing = [(group_key, left, right, events)]
                elif score == maximum and score > 0:
                    maximizing.append((group_key, left, right, events))
    return maximum, maximizing, pair_count, event_family_counts


def _permuted_assignment(records, rng):
    strata = defaultdict(list)
    for record in records:
        strata[(record.form_kind, record.variant, record.blob)].append(record)
    assignment = {}
    for (form, variant, blob), stratum in strata.items():
        slots = sorted(record.candidate_index for record in stratum)
        shuffled = list(stratum)
        rng.shuffle(shuffled)
        for candidate_index, record in zip(slots, shuffled):
            assignment[(form, variant, blob, candidate_index)] = record
    return assignment


def analyze_records(records, null_trials=NULL_TRIALS, null_seed=NULL_SEED):
    real_max, maximizing, pair_count, family_counts = _score_assignment(_assignment_from_records(records))
    rng = random.Random(null_seed)
    null_maxima = []
    for _trial in range(null_trials):
        null_max, _rows, _pairs, _counts = _score_assignment(_permuted_assignment(records, rng))
        null_maxima.append(null_max)
    exceedances = sum(value >= real_max for value in null_maxima)
    p_value = (1 + exceedances) / (1 + null_trials)
    promoted = real_max > 0 and p_value <= ALPHA

    disclosed = []
    if promoted:
        for (candidate_index, form, variant), left, right, events in maximizing:
            disclosed.append({
                "candidate_index": candidate_index,
                "candidate_model": left.candidate_model,
                "candidate_label": left.candidate_label,
                "candidate_sha256": left.candidate_sha256,
                "candidate_form": form,
                "variant": variant,
                "blob_pair": [left.blob, right.blob],
                "body_lengths": [left.body_length, right.body_length],
                "body_sha256s": [left.body_sha256, right.body_sha256],
                "events": list(events),
            })

    return {
        "record_count": len(records),
        "pair_hypotheses": pair_count,
        "feature_registry": {
            "validated_type": "complete whole-body parser, raw or one strict decode hop",
            "checksum_family": ["sha256_first4", "sha256d_first4", "crc32_le", "crc32_be"],
            "delimiter_geometry": "exact (offset,byte) tuple in first 64 bytes; >=2 delimiters",
            "record_geometry": "equal-width LF/NUL/pipe records; >=3 non-empty records",
            "scalar_hash160": {"scalar_offsets": list(SCALAR_OFFSETS),
                               "hash160_offsets": list(HASH160_OFFSETS),
                               "encodings": ["compressed", "uncompressed"]},
        },
        "real_maximum_event_count": real_max,
        "real_maximizer_count": len(maximizing),
        "real_event_family_counts": dict(sorted(family_counts.items())),
        "null_trials": null_trials,
        "null_seed": null_seed,
        "null_maximum_histogram": {
            str(key): value for key, value in sorted(Counter(null_maxima).items())
        },
        "null_maximum_min": min(null_maxima) if null_maxima else None,
        "null_maximum_max": max(null_maxima) if null_maxima else None,
        "familywise_empirical_p": p_value,
        "alpha": ALPHA,
        "promoted_for_candidate_inspection": promoted,
        "candidate_specific_results_disclosed": promoted,
        "promoted_rows": disclosed,
    }


def run(null_trials=NULL_TRIALS):
    candidates = frozen_candidates()
    if len(candidates) != 42 or candidate_list_digest(candidates) != EXPECTED_CANDIDATE_DIGEST:
        raise AssertionError("frozen Phase 336--338 candidate manifest drifted")
    records = collect_records()
    if len(records) != EXPECTED_BODY_COUNT:
        raise AssertionError(f"expected {EXPECTED_BODY_COUNT} retained bodies, got {len(records)}")
    report = analyze_records(records, null_trials=null_trials)
    report.update({
        "candidate_count": len(candidates),
        "candidate_digest": EXPECTED_CANDIDATE_DIGEST,
        "candidate_forms": ["literal", "sha256"],
        "blob_count": 4,
        "crypto_variant_count": 54,
        "stop_rule_applied": True,
    })
    return report


def self_test():
    # 1. Every feature family has a planted positive and near-negative.
    payload = b"payload-for-checksum"
    checked = payload + hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    assert checksum_families(checked) == {"sha256d_first4"}
    assert not checksum_families(checked[:-1] + bytes([checked[-1] ^ 1]))

    geometry_body = b"A|B,C;" + b"x" * 58
    assert delimiter_geometry(geometry_body) is not None
    assert delimiter_geometry(geometry_body) != delimiter_geometry(b"A|B.C;" + b"x" * 58)
    assert ("pipe", 3, 3) in record_geometries(b"abc|def|ghi")
    assert not record_geometries(b"abc|de|ghi")

    # 2. Fixed-offset scalar->HASH160 relation, both directions guarded.
    scalar = (1234567).to_bytes(32, "big")
    compressed_h160 = bytes.fromhex(private_key_details(scalar)["compressed"]["hash160"])
    left = extract_features(scalar + b"L" * 48)
    right = extract_features(compressed_h160 + b"R" * 60)
    events = concordance_events(left, right)
    assert "scalar_hash160:left_to_right:scalar@0:compressed->hash160@0" in events
    wrong = extract_features(bytes([compressed_h160[0] ^ 1]) + compressed_h160[1:] + b"R" * 60)
    assert not any(event.startswith("scalar_hash160:") for event in concordance_events(left, wrong))

    # 3. Complete structural validation is inherited from Seed 2, not magic-byte-only.
    salted = b"Salted__" + b"12345678" + b"x" * 32
    assert "raw:salted_header" in validated_types(salted)
    assert "raw:salted_header" not in validated_types(salted[:-1])

    # 4. Statistical engine: 40 labels, only one true aligned pair. Label
    # permutation should recover the planted pair in roughly 1/40 trials;
    # the family-wise gate must promote it without ever using a candidate
    # literal in the statistic.
    records = []
    empty = extract_features(b"Z" * 80)
    for index in range(40):
        for blob in ("A", "B"):
            features = empty
            if index == 7 and blob == "A":
                features = left
            elif index == 7 and blob == "B":
                features = right
            records.append(Record(index, "synthetic", f"label_{index}",
                                  hashlib.sha256(f"candidate-{index}".encode()).hexdigest(),
                                  "literal", "synthetic/cfb", blob, 80,
                                  hashlib.sha256(f"body-{index}-{blob}".encode()).hexdigest(), features))
    report = analyze_records(records, null_trials=400, null_seed=17)
    assert report["real_maximum_event_count"] == 1
    assert report["promoted_for_candidate_inspection"]
    assert report["promoted_rows"][0]["candidate_index"] == 7

    # 5. A null-only population must not disclose candidate provenance.
    null_records = [record for record in records if record.candidate_index != 7]
    null_report = analyze_records(null_records, null_trials=50, null_seed=17)
    assert null_report["real_maximum_event_count"] == 0
    assert not null_report["promoted_for_candidate_inspection"]
    assert null_report["promoted_rows"] == []

    # 6. Label permutation preserves every stratum's label slots and exact
    # body-length multiset, including sparse/missing-retention strata.
    sparse = records[:-1]
    permuted = _permuted_assignment(sparse, random.Random(1))
    original = _assignment_from_records(sparse)
    assert set(permuted) == set(original)
    for stratum in {(key[0], key[1], key[2]) for key in original}:
        before = sorted(record.body_length for key, record in original.items() if key[:3] == stratum)
        after = sorted(record.body_length for key, record in permuted.items() if key[:3] == stratum)
        assert before == after

    # 7. Frozen input manifest and retained-body count, mechanically live.
    candidates = frozen_candidates()
    assert len(candidates) == 42
    assert candidate_list_digest(candidates) == EXPECTED_CANDIDATE_DIGEST
    assert sum(1 for _ in iter_retained_bodies()) == EXPECTED_BODY_COUNT

    print("[*] self-test OK: four frozen structural families have planted positives and near-"
          "negatives; fixed-offset scalar->HASH160 relation and complete Salted__ validation "
          "verified; planted aligned-pair driver passes the family-wise permutation gate; null "
          "population discloses no candidate; permutation preserves strata/length/missingness; "
          f"candidate digest {EXPECTED_CANDIDATE_DIGEST} and {EXPECTED_BODY_COUNT} bodies enforced")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--null-trials", type=int, default=NULL_TRIALS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run(args.null_trials) if args.run else {"note": "pass --run to execute the frozen audit"}
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.json:
        print(rendered)
    else:
        for key, value in report.items():
            if key not in ("promoted_rows", "feature_registry"):
                print(f"{key}: {value}")


if __name__ == "__main__":
    main()
