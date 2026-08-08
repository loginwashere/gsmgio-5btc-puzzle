#!/usr/bin/env python3
"""Audit the exact 83-guide-token / 83-COSMIC-block alignment.

The recovered DBBI guide has 83 tokens grouped into 23 prime-delimited
chunks.  COSMIC has 83 AES ciphertext blocks; its complete OpenSSL envelope
has 84 blocks because ``Salted__`` plus the eight-byte salt is exactly one
block.  This audit tests the narrow XOR consumer implied by those exact sizes:

1. align guide chunks to COSMIC blocks;
2. XOR-fold the blocks within each of the 23 chunks;
3. XOR-fold those chunk results into the documented blue/yellow 16/7 rails;
4. concatenate the two 16-byte rails into a native 32-byte material.

It also tests the full-envelope geometry's next fixed consumer: divide COSMIC's
84 blocks into fourteen six-block strips and let each historical guide row
select one surviving block using either ``row_sum % 6`` or the guide output's
own zero-based alphabet code modulo six.  The 14 selected blocks are evaluated
directly, by SHA-256, by total XOR, and as fixed odd/even dual XOR rails.

All three documented color profiles are retained: the historical guide colors,
the first-piece colors (which disagree at endpoints 21 and 23), and the
split-final-BE endpoint profile that produces 16 blue / 7 yellow.  The solved Phase 3.2 artifact is run
through the identical prefix fold as a calibration control before any COSMIC
material is evaluated against the established scalar and decryption oracles.
"""

import argparse
import hashlib
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import private_key_details  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    KDF_VARIANTS,
    aes_try_open_bytes,
    printable_z_score,
    raw_key_try_open,
)
from data import PHASE32_BLOB_B64, PHASE32_PASSWORD  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402
from first_piece_color_reconstruction import EXPECTED_COLOR_SEQUENCE  # noqa: E402
from salt_phase_ion_audit import decrypt_phase32_ground_truth, xor_bytes  # noqa: E402
from telegram_yellow_blue_guide_audit import reconstruct_guide  # noqa: E402
from telegram_23167_operation_audit import guide_endpoint_profile  # noqa: E402


KNOWN_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}


def blocks16(data):
    if len(data) % 16:
        raise ValueError(f"input length {len(data)} is not AES-block aligned")
    return tuple(data[offset:offset + 16] for offset in range(0, len(data), 16))


def xor_many(values):
    if not values:
        raise ValueError("cannot XOR-fold an empty sequence")
    result = bytes(16)
    for value in values:
        if len(value) != 16:
            raise ValueError("XOR fold requires 16-byte values")
        result = xor_bytes(result, value)
    return result


def split_final_be(chunks):
    if chunks[-1][-1] != "be":
        raise AssertionError("guide no longer ends in a BE token")
    return chunks[:-1] + (chunks[-1][:-1] + ("b", "e"),)


def fold_by_guide(blocks, chunks, colors, consumer):
    lengths = tuple(len(chunk) for chunk in chunks)
    if sum(lengths) != len(blocks):
        raise ValueError(
            f"guide covers {sum(lengths)} tokens but input has {len(blocks)} blocks"
        )
    chunk_folds = []
    endpoint_blocks = []
    offset = 0
    for length in lengths:
        chunk_blocks = blocks[offset:offset + length]
        chunk_folds.append(xor_many(chunk_blocks))
        endpoint_blocks.append(chunk_blocks[-1])
        offset += length
    if consumer == "all_blocks_by_chunk_color":
        rail_values = chunk_folds
    elif consumer == "endpoint_blocks_only":
        rail_values = endpoint_blocks
    else:
        raise ValueError(f"unknown guide consumer: {consumer}")
    blue = xor_many(tuple(value for value, color in zip(rail_values, colors) if color == "B"))
    yellow = xor_many(tuple(value for value, color in zip(rail_values, colors) if color == "Y"))
    return {
        "consumer": consumer,
        "chunk_lengths": lengths,
        "chunk_folds": tuple(chunk_folds),
        "blue": blue,
        "yellow": yellow,
        "blue_yellow": blue + yellow,
        "yellow_blue": yellow + blue,
        "combined": xor_bytes(blue, yellow),
        "blue_count": colors.count("B"),
        "yellow_count": colors.count("Y"),
    }


def mapping_specs(guide):
    original_chunks = guide["chunks"]
    split_chunks = split_final_be(original_chunks)
    return (
        ("ciphertext83", original_chunks),
        ("full_envelope84", split_chunks),
    )


def color_specs(guide):
    return {
        "guide_prime_colors": guide["prime_colors"],
        "first_piece_colors": EXPECTED_COLOR_SEQUENCE[:23],
        "split_endpoint_16_7": guide_endpoint_profile()["endpoint_colors"],
    }


def derived_folds(data_by_mapping, guide):
    reports = {}
    for mapping_name, chunks in mapping_specs(guide):
        mapping_blocks = data_by_mapping[mapping_name]
        for color_name, colors in color_specs(guide).items():
            for consumer in ("all_blocks_by_chunk_color", "endpoint_blocks_only"):
                reports[f"{mapping_name}:{color_name}:{consumer}"] = fold_by_guide(
                    mapping_blocks, chunks, colors, consumer
                )
    return reports


def six_block_strips(blocks):
    if len(blocks) != 84:
        raise ValueError(f"six-block strip selector requires 84 blocks, got {len(blocks)}")
    return tuple(tuple(blocks[offset:offset + 6]) for offset in range(0, 84, 6))


def strip_selector_specs(guide):
    row_sum_mod6 = tuple(value % 6 for value in guide["row_sums"])
    # output_from_row_sums() renders sum%26 as A=0 ... Z=25.  Preserve that
    # exact historical encoding; calling this A1Z26 would be off by one.
    output_code_mod6 = tuple((ord(char) - ord("A")) % 6 for char in guide["output"])
    return {
        "row_sum_mod6": row_sum_mod6,
        "output_A0Z25_mod6": output_code_mod6,
    }


def select_one_per_strip(blocks, selectors):
    strips = six_block_strips(blocks)
    if len(selectors) != len(strips):
        raise ValueError("selector count does not match six-block strip count")
    selected = tuple(strip[index] for strip, index in zip(strips, selectors))
    odd = xor_many(selected[0::2])
    even = xor_many(selected[1::2])
    stream = b"".join(selected)
    return {
        "selectors": tuple(selectors),
        "selected_blocks": selected,
        "selected_stream": stream,
        "sha256_selected_stream": hashlib.sha256(stream).digest(),
        "xor_all": xor_many(selected),
        "odd": odd,
        "even": even,
        "odd_even": odd + even,
        "even_odd": even + odd,
    }


def derived_strip_selections(blocks, guide):
    return {
        name: select_one_per_strip(blocks, selectors)
        for name, selectors in strip_selector_specs(guide).items()
    }


def calibration(guide):
    salt, ciphertext, plaintext, correct_key = decrypt_phase32_ground_truth()
    full_envelope = b"Salted__" + salt + ciphertext
    data_sets = {
        "ciphertext": {
            "ciphertext83": blocks16(ciphertext)[:83],
            "full_envelope84": blocks16(full_envelope)[:84],
        },
        "plaintext": {
            "ciphertext83": blocks16(plaintext[:83 * 16]),
            "full_envelope84": blocks16(plaintext[:84 * 16]),
        },
    }
    phase_blobs = {"PHASE32": (salt, ciphertext)}
    known_password_bytes = bytes.fromhex(PHASE32_PASSWORD)
    reports = {}
    for source_name, mapping_data in data_sets.items():
        folds = derived_folds(mapping_data, guide)
        reports[source_name] = {}
        for name, fold in folds.items():
            candidates = (fold["blue_yellow"], fold["yellow_blue"])
            reports[source_name][name] = {
                "blue_yellow": fold["blue_yellow"].hex(),
                "yellow_blue": fold["yellow_blue"].hex(),
                "matches_correct_derived_key": correct_key in candidates,
                "matches_password_hash_bytes": known_password_bytes in candidates,
                "phase32_passphrase_hits": sum(
                    bool(aes_try_open_bytes(candidate, blobs=phase_blobs))
                    for candidate in candidates
                ),
                "phase32_raw_key_hits": sum(
                    bool(raw_key_try_open(candidate, blobs=phase_blobs))
                    for candidate in candidates
                ),
                "phase32_color_pair_hits": len(
                    evaluate_color_key_iv_pairs(
                        fold, phase_blobs, known_prefix=b"I've been waiting for you."
                    )
                ),
            }
    return reports


def decrypt_key_iv(ciphertext, key, iv):
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    pad = padded[-1]
    if not (1 <= pad <= 16 and padded[-pad:] == bytes([pad]) * pad):
        return None
    return padded[:-pad]


def color_key_iv_pairs(fold):
    blue, yellow = fold["blue"], fold["yellow"]
    return {
        "aes128:key_blue:iv_yellow": (blue, yellow),
        "aes128:key_yellow:iv_blue": (yellow, blue),
        "aes256:key_blue_yellow:iv_blue": (blue + yellow, blue),
        "aes256:key_blue_yellow:iv_yellow": (blue + yellow, yellow),
        "aes256:key_yellow_blue:iv_blue": (yellow + blue, blue),
        "aes256:key_yellow_blue:iv_yellow": (yellow + blue, yellow),
    }


def evaluate_color_key_iv_pairs(fold, blobs, known_prefix=None):
    hits = []
    for form, (key, iv) in color_key_iv_pairs(fold).items():
        for tag, (_salt, ciphertext) in blobs.items():
            plaintext = decrypt_key_iv(ciphertext, key, iv)
            if plaintext is None:
                continue
            z_score = printable_z_score(plaintext)
            if (known_prefix and plaintext.startswith(known_prefix)) or z_score >= 8.0:
                hits.append((form, tag, z_score, plaintext[:120]))
    return hits


def selection_materials(selection):
    return {
        "selected_stream": selection["selected_stream"],
        "sha256_selected_stream": selection["sha256_selected_stream"],
        "xor_all": selection["xor_all"],
        "odd_even": selection["odd_even"],
        "even_odd": selection["even_odd"],
    }


def selection_as_color_fold(selection):
    return {
        "blue": selection["odd"],
        "yellow": selection["even"],
    }


def calibrate_strip_selections(guide):
    salt, ciphertext, plaintext, correct_key = decrypt_phase32_ground_truth()
    full_envelope = b"Salted__" + salt + ciphertext
    sources = {
        "ciphertext_prefix84": blocks16(full_envelope)[:84],
        "plaintext_prefix84": blocks16(plaintext[:84 * 16]),
    }
    phase_blobs = {"PHASE32": (salt, ciphertext)}
    password_hash_bytes = bytes.fromhex(PHASE32_PASSWORD)
    reports = {}
    for source_name, source_blocks in sources.items():
        reports[source_name] = {}
        for selector_name, selection in derived_strip_selections(source_blocks, guide).items():
            materials = selection_materials(selection)
            reports[source_name][selector_name] = {
                "selectors": selection["selectors"],
                "matches_correct_derived_key": any(
                    material == correct_key for material in materials.values()
                ),
                "matches_password_hash_bytes": any(
                    material == password_hash_bytes for material in materials.values()
                ),
                "phase32_passphrase_hits": sum(
                    bool(aes_try_open_bytes(material, blobs=phase_blobs))
                    for material in materials.values()
                ),
                "phase32_raw_key_hits": sum(
                    bool(raw_key_try_open(material, blobs=phase_blobs))
                    for material in materials.values()
                    if len(material) in (16, 24, 32)
                ),
                "phase32_odd_even_key_iv_hits": len(
                    evaluate_color_key_iv_pairs(
                        selection_as_color_fold(selection),
                        phase_blobs,
                        known_prefix=b"I've been waiting for you.",
                    )
                ),
            }
    return reports


def evaluate_strip_selections(selections):
    address_hits = []
    raw_key_hits = []
    passphrase_hits = []
    odd_even_key_iv_hits = []
    attempt_count = 0
    for selector_name, selection in selections.items():
        odd_even_key_iv_hits.extend(
            (selector_name,) + hit
            for hit in evaluate_color_key_iv_pairs(selection_as_color_fold(selection), BLOBS)
        )
        for form, material in selection_materials(selection).items():
            attempt_count += 1
            if len(material) == 32:
                details = private_key_details(material)
                if details:
                    for address_type, address_data in details.items():
                        if address_data["address"] in KNOWN_ADDRESSES:
                            address_hits.append(
                                (selector_name, form, address_type, address_data["address"])
                            )
            if len(material) in (16, 24, 32):
                for tag, cipher, plaintext, z_score in raw_key_try_open(material):
                    raw_key_hits.append(
                        (selector_name, form, tag, cipher, z_score, plaintext[:120])
                    )
            for result in aes_try_open_bytes(material, kdf_variants=KDF_VARIANTS) or ():
                passphrase_hits.append((selector_name, form, repr(result)))
    return {
        "material_attempts": attempt_count,
        "address_hits": address_hits,
        "raw_key_hits": raw_key_hits,
        "passphrase_hits": passphrase_hits,
        "odd_even_key_iv_hits": odd_even_key_iv_hits,
    }


def evaluate_cosmic_folds(folds):
    address_hits = []
    decrypt_hits = []
    passphrase_hits = []
    color_pair_hits = []
    seen = set()
    for source, fold in folds.items():
        color_pair_hits.extend(
            (source,) + hit for hit in evaluate_color_key_iv_pairs(fold, BLOBS)
        )
        materials = {
            "blue": fold["blue"],
            "yellow": fold["yellow"],
            "combined": fold["combined"],
            "blue_yellow": fold["blue_yellow"],
            "yellow_blue": fold["yellow_blue"],
        }
        for form, material in materials.items():
            identity = (form, material)
            if identity in seen:
                continue
            seen.add(identity)
            if len(material) == 32:
                details = private_key_details(material)
                if details:
                    for address_type, address_data in details.items():
                        if address_data["address"] in KNOWN_ADDRESSES:
                            address_hits.append((source, form, address_type, address_data["address"]))
            for tag, cipher, plaintext, z_score in raw_key_try_open(material):
                decrypt_hits.append((source, form, tag, cipher, z_score, plaintext[:120]))
            for result in aes_try_open_bytes(material, kdf_variants=KDF_VARIANTS) or ():
                passphrase_hits.append((source, form, repr(result)))
    return {
        "unique_materials": len(seen),
        "address_hits": address_hits,
        "raw_key_hits": decrypt_hits,
        "passphrase_hits": passphrase_hits,
        "color_pair_hits": color_pair_hits,
    }


def audit():
    guide = reconstruct_guide()
    cosmic_salt, cosmic_ciphertext = BLOBS["COSMIC"]
    full_envelope = b"Salted__" + cosmic_salt + cosmic_ciphertext
    cosmic_data = {
        "ciphertext83": blocks16(cosmic_ciphertext),
        "full_envelope84": blocks16(full_envelope),
    }
    folds = derived_folds(cosmic_data, guide)
    strip_selections = derived_strip_selections(blocks16(full_envelope), guide)
    full_block_counts = {
        tag: len(blocks16(b"Salted__" + salt + ciphertext))
        for tag, (salt, ciphertext) in BLOBS.items()
    }
    return {
        "guide_token_count": len(guide["tokens"]),
        "guide_split_token_count": sum(len(chunk) for chunk in split_final_be(guide["chunks"])),
        "guide_chunk_count": len(guide["chunks"]),
        "cosmic_ciphertext_blocks": len(blocks16(cosmic_ciphertext)),
        "cosmic_full_envelope_blocks": len(blocks16(full_envelope)),
        "full_envelope_block_counts": full_block_counts,
        "six_block_strip_counts": {
            tag: count // 6 for tag, count in full_block_counts.items()
        },
        "combined_full_envelope_blocks": sum(full_block_counts.values()),
        "folds": folds,
        "calibration": calibration(guide),
        "evaluation": evaluate_cosmic_folds(folds),
        "strip_selectors": strip_selector_specs(guide),
        "strip_selections": strip_selections,
        "strip_selection_calibration": calibrate_strip_selections(guide),
        "strip_selection_evaluation": evaluate_strip_selections(strip_selections),
    }


def self_test():
    report = audit()
    assert (
        report["guide_token_count"],
        report["guide_split_token_count"],
        report["guide_chunk_count"],
    ) == (83, 84, 23)
    assert (
        report["cosmic_ciphertext_blocks"],
        report["cosmic_full_envelope_blocks"],
    ) == (83, 84)
    assert tuple(report["full_envelope_block_counts"].values()) == (6, 84, 6)
    assert tuple(report["six_block_strip_counts"].values()) == (1, 14, 1)
    assert report["combined_full_envelope_blocks"] == 16 * 6
    assert report["strip_selectors"] == {
        "row_sum_mod6": (4, 3, 1, 0, 0, 2, 2, 2, 1, 0, 5, 3, 2, 1),
        "output_A0Z25_mod6": (2, 1, 5, 4, 4, 0, 4, 4, 3, 4, 3, 3, 4, 1),
    }
    assert len(report["folds"]) == 12
    assert all(
        fold["blue_count"] == 16 and fold["yellow_count"] == 7
        for name, fold in report["folds"].items()
        if ":split_endpoint_16_7:" in name
    )
    assert not any(
        item["matches_correct_derived_key"]
        or item["matches_password_hash_bytes"]
        or item["phase32_passphrase_hits"]
        or item["phase32_raw_key_hits"]
        or item["phase32_color_pair_hits"]
        for source in report["calibration"].values()
        for item in source.values()
    )
    assert not any(
        item["matches_correct_derived_key"]
        or item["matches_password_hash_bytes"]
        or item["phase32_passphrase_hits"]
        or item["phase32_raw_key_hits"]
        or item["phase32_odd_even_key_iv_hits"]
        for source in report["strip_selection_calibration"].values()
        for item in source.values()
    )
    print(
        "[*] self-test OK: exact 83/84 guide-to-envelope alignments, 23-chunk "
        "XOR folds, six-block row selectors, Phase 3.2 calibration, and bounded "
        "oracles verified"
    )


def print_report(report):
    print(
        f"[*] guide tokens={report['guide_token_count']} / split={report['guide_split_token_count']}; "
        f"chunks={report['guide_chunk_count']}"
    )
    print(
        f"[*] COSMIC blocks: ciphertext={report['cosmic_ciphertext_blocks']}, "
        f"full Salted__ envelope={report['cosmic_full_envelope_blocks']}"
    )
    print(
        f"[*] full-envelope geometry: blocks={report['full_envelope_block_counts']}, "
        f"six-block strips={report['six_block_strip_counts']}, "
        f"combined={report['combined_full_envelope_blocks']}=16x6"
    )
    for name, fold in report["folds"].items():
        print(
            f"[*] {name}: B/Y={fold['blue_count']}/{fold['yellow_count']} "
            f"blue={fold['blue'].hex()} yellow={fold['yellow'].hex()} "
            f"B||Y={fold['blue_yellow'].hex()}"
        )
    calibration_hits = sum(
        item["matches_correct_derived_key"]
        + item["matches_password_hash_bytes"]
        + item["phase32_passphrase_hits"]
        + item["phase32_raw_key_hits"]
        + item["phase32_color_pair_hits"]
        for source in report["calibration"].values()
        for item in source.values()
    )
    print(f"[*] Phase 3.2 calibration hits: {calibration_hits}")
    result = report["evaluation"]
    print(
        f"[*] COSMIC-derived materials={result['unique_materials']}; "
        f"address hits={len(result['address_hits'])}; "
        f"raw-key openings={len(result['raw_key_hits'])}; "
        f"passphrase openings={len(result['passphrase_hits'])}; "
        f"color-key/IV openings={len(result['color_pair_hits'])}"
    )
    for kind in ("address_hits", "raw_key_hits", "passphrase_hits", "color_pair_hits"):
        for hit in result[kind]:
            print(f"[+++ {kind}] {hit}")
    strip_calibration_hits = sum(
        item["matches_correct_derived_key"]
        + item["matches_password_hash_bytes"]
        + item["phase32_passphrase_hits"]
        + item["phase32_raw_key_hits"]
        + item["phase32_odd_even_key_iv_hits"]
        for source in report["strip_selection_calibration"].values()
        for item in source.values()
    )
    print(f"[*] six-block selectors: {report['strip_selectors']}")
    for name, selection in report["strip_selections"].items():
        print(
            f"[*] {name}: selected_stream_sha256="
            f"{selection['sha256_selected_stream'].hex()} "
            f"xor_all={selection['xor_all'].hex()} "
            f"odd||even={selection['odd_even'].hex()}"
        )
    strip_result = report["strip_selection_evaluation"]
    print(
        f"[*] six-block selector Phase 3.2 calibration hits={strip_calibration_hits}; "
        f"materials={strip_result['material_attempts']}; "
        f"address hits={len(strip_result['address_hits'])}; "
        f"raw-key openings={len(strip_result['raw_key_hits'])}; "
        f"passphrase openings={len(strip_result['passphrase_hits'])}; "
        f"odd/even key-IV openings={len(strip_result['odd_even_key_iv_hits'])}"
    )
    for kind in (
        "address_hits", "raw_key_hits", "passphrase_hits", "odd_even_key_iv_hits"
    ):
        for hit in strip_result[kind]:
            print(f"[+++ strip {kind}] {hit}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        print_report(audit())


if __name__ == "__main__":
    main()
