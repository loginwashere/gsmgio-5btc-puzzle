#!/usr/bin/env python3
"""Apply the two authenticated 24-bit color masks to full DBBI/FAED streams.

This closes one narrow coverage gap left by Phase 169-170.  Those phases used
F73D92/08C26D over the 31-byte selection and Phase 3.2 control material, while
their full DBBI/FAED XOR pass tested only literal word keys.  Here each mask is
repeated over the exact ASCII bytes of DBBI and FAED.  Only the complete binary
stream, its SHA-256, and its first/last 32 bytes are consumed.  No alternate
symbol encoding, shift, offset, cross-channel combination, or color arithmetic
is introduced.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import private_key_details  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    raw_key_try_open,
)
from data import DBBI, FAED, PHASE32_PASSWORD, PHASE32_PLAINTEXT_PREFIX  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402
from salt_phase_ion_audit import (  # noqa: E402
    BLUE_MASK,
    YELLOW_MASK,
    decrypt_phase32_ground_truth,
    phase32_calibration,
    printable_ratio,
    repeating_xor,
    xor_bytes,
)


MASKS = {"blue_F73D92": BLUE_MASK, "yellow_08C26D": YELLOW_MASK}
SOURCES = {"DBBI": DBBI.encode("ascii"), "FAED": FAED.encode("ascii")}
KNOWN_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}
MARKERS = (b"Salted__", PHASE32_PLAINTEXT_PREFIX.encode(), b"bitcoin", b"private key")


def longest_printable_run(data):
    best = current = 0
    for value in data:
        if value in (9, 10, 13) or 32 <= value <= 126:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def derived_forms(transformed):
    if len(transformed) < 32:
        raise ValueError("full-stream color-mask source is shorter than 32 bytes")
    return {
        "sha256": hashlib.sha256(transformed).digest(),
        "first32": transformed[:32],
        "last32": transformed[-32:],
    }


def passphrase_hits(material, blobs):
    families = (
        ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS),
        ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS),
        ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS),
        ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS),
    )
    hits = []
    for family, oracle, variants in families:
        result = oracle(material, kdf_variants=variants, blobs=blobs)
        if result:
            hits.append({"family": family, "result": repr(result)})
    return hits


def scalar_hits(material):
    details = private_key_details(material)
    if details is None:
        return []
    return [
        {"address_type": address_type, "address": item["address"]}
        for address_type, item in details.items()
        if item["address"] in KNOWN_ADDRESSES
    ]


def analyze_transform(source_name, source, mask_name, mask):
    transformed = repeating_xor(source, mask)
    marker_hits = tuple(
        marker.decode("ascii", errors="replace")
        for marker in MARKERS
        if marker.lower() in transformed.lower()
    )
    forms = derived_forms(transformed)
    return {
        "source": source_name,
        "mask": mask_name,
        "source_length": len(source),
        "transformed_sha256": hashlib.sha256(transformed).hexdigest(),
        "printable_ratio": printable_ratio(transformed),
        "longest_printable_run": longest_printable_run(transformed),
        "marker_hits": marker_hits,
        "whole_passphrase_hits": passphrase_hits(transformed, BLOBS),
        "forms": {
            form_name: {
                "hex": material.hex(),
                "passphrase_hits": passphrase_hits(material, BLOBS),
                "raw_key_hits": [repr(item) for item in raw_key_try_open(material)],
                "scalar_hits": scalar_hits(material),
            }
            for form_name, material in forms.items()
        },
        "transformed": transformed,
    }


def phase32_control():
    salt, ciphertext, plaintext, _key = decrypt_phase32_ground_truth()
    existing = phase32_calibration()
    existing_masks = {
        item["operand"]: item
        for item in existing["xor_reports"]
        if item["operand"] in ("blue_mask", "yellow_mask")
    }
    blob = {"PHASE32": (salt, ciphertext)}
    rows = []
    for source_name, source in (("ciphertext", ciphertext), ("known_plaintext", plaintext)):
        for mask_name, mask in MASKS.items():
            transformed = repeating_xor(source, mask)
            forms = derived_forms(transformed)
            rows.append({
                "source": source_name,
                "mask": mask_name,
                "whole_passphrase_hits": passphrase_hits(transformed, blob),
                "forms": {
                    form_name: {
                        "equals_known_password": material == PHASE32_PASSWORD.encode("ascii"),
                        "passphrase_hits": passphrase_hits(material, blob),
                        "raw_key_hits": [
                            repr(item) for item in raw_key_try_open(material, blobs=blob)
                        ],
                    }
                    for form_name, material in forms.items()
                },
            })
    return {
        "aes_positive": existing["positive_control"],
        "direct_decoder_checks": existing_masks,
        "consumer_rows": rows,
    }


def strip_binary(report):
    cleaned = dict(report)
    cleaned.pop("transformed", None)
    return cleaned


def audit():
    calibration = phase32_control()
    reports = [
        analyze_transform(source_name, source, mask_name, mask)
        for source_name, source in SOURCES.items()
        for mask_name, mask in MASKS.items()
    ]
    by_source = {
        source_name: {
            report["mask"]: report["transformed"]
            for report in reports
            if report["source"] == source_name
        }
        for source_name in SOURCES
    }
    complement_checks = {
        source_name: xor_bytes(values["blue_F73D92"], values["yellow_08C26D"])
        == bytes([0xFF]) * len(SOURCES[source_name])
        for source_name, values in by_source.items()
    }
    clean_reports = [strip_binary(report) for report in reports]
    return {
        "masks": {name: value.hex() for name, value in MASKS.items()},
        "mask_xor": xor_bytes(BLUE_MASK, YELLOW_MASK).hex(),
        "sources": {name: len(value) for name, value in SOURCES.items()},
        "transform_count": len(clean_reports),
        "derived_32byte_material_count": len(clean_reports) * 3,
        "complement_checks": complement_checks,
        "phase32_control": calibration,
        "reports": clean_reports,
        "marker_hit_count": sum(len(report["marker_hits"]) for report in clean_reports),
        "whole_passphrase_hit_count": sum(
            len(report["whole_passphrase_hits"]) for report in clean_reports
        ),
        "derived_passphrase_hit_count": sum(
            len(form["passphrase_hits"])
            for report in clean_reports
            for form in report["forms"].values()
        ),
        "raw_key_hit_count": sum(
            len(form["raw_key_hits"])
            for report in clean_reports
            for form in report["forms"].values()
        ),
        "scalar_hit_count": sum(
            len(form["scalar_hits"])
            for report in clean_reports
            for form in report["forms"].values()
        ),
    }


def self_test():
    assert repeating_xor(b"abcdef", bytes.fromhex("010203")) == bytes.fromhex(
        "606060656765"
    )
    assert xor_bytes(BLUE_MASK, YELLOW_MASK) == b"\xff\xff\xff"
    forms = derived_forms(bytes(range(40)))
    assert forms["first32"] == bytes(range(32))
    assert forms["last32"] == bytes(range(8, 40))
    report = audit()
    assert report["sources"] == {"DBBI": 91, "FAED": 570}
    assert report["transform_count"] == 4
    assert report["derived_32byte_material_count"] == 12
    assert all(report["complement_checks"].values())
    assert report["phase32_control"]["aes_positive"]
    print("[*] self-test OK: exact masks, full source lengths, complement identity, and Phase 3.2 control")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report = audit()
    print(
        f"[*] masks: {report['masks']}; XOR={report['mask_xor']}; "
        f"sources={report['sources']}"
    )
    print(
        f"[*] Phase 3.2 AES positive={report['phase32_control']['aes_positive']}; "
        "direct mask decoder matches="
        f"{sum(item['ciphertext_to_known_prefix'] or item['known_xor_stream_is_periodic_operand'] for item in report['phase32_control']['direct_decoder_checks'].values())}"
    )
    for item in report["reports"]:
        print(
            f"    {item['source']}/{item['mask']}: sha256={item['transformed_sha256']} "
            f"printable={item['printable_ratio']:.6f} "
            f"longest_run={item['longest_printable_run']} markers={len(item['marker_hits'])}"
        )
    print(
        f"[*] hits: markers={report['marker_hit_count']} "
        f"whole_passphrase={report['whole_passphrase_hit_count']} "
        f"derived_passphrase={report['derived_passphrase_hit_count']} "
        f"raw_key={report['raw_key_hit_count']} scalar={report['scalar_hit_count']}"
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
