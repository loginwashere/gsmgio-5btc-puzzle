#!/usr/bin/env python3
"""Bounded P32TRAILING audit from its Phase-3.2 sibling outputs.

The authenticated Phase-3.2 AES plaintext contains, in source order, the
EBCDIC/Beaufort block, the 149-digit VIC/checkerboard stream and its clue,
then the 96-byte OpenSSL ``P32_TRAILING`` envelope.  Earlier audits tested
sentences and selected fragments as independent passphrases.  This module
tests the remaining provenance-native constructions:

* the complete connected Phase-3.2.1 Beaufort plaintext;
* the complete Phase-3.2.1 and 3.2.2 outputs in sibling order;
* the established 23-event/31-character prime walk over the 3.2.2 output;
* the literal zero-based prime-colored Stage-0 cells and their in-range
  projection onto the 91-character 3.2.2 output;
* a small, disclosed set of sibling cipher-parameter concatenations.

P32 has exactly 80 ciphertext bytes (five AES blocks).  The clue-supported
two-private-key hypothesis therefore has one exact padded representation:
64 payload bytes followed by a complete block of sixteen ``0x10`` bytes.
The unconditional probability that a wrong decrypt has that exact last block
is 256^-16 (or 256^-15 conditional on already observing a final byte of 0x10).
No printable-text heuristic is used.

Private bytes and WIFs are never printed or returned.  If a structural hit is
found, only the payload SHA-256 and derived public addresses are reported.
Network lookups are deliberately outside this audit.
"""

import argparse
import base64
import hashlib
import json
import re
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from binary_key_material_backfill import hash160
from cb_common import (
    _load_blob,
    decode,
    evp_bytes_to_key,
    pbkdf2_bytes_to_key,
)
from data import (
    ALPHA_322,
    DBBI,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    P32_TRAILING_BLOB_B64,
    VALIDATION_ANSWER,
    VALIDATION_ESCAPES,
    VALIDATION_NUM,
)
from first_hint_hash_audit import SECP256K1_ORDER, base58check
from first_piece_color_reconstruction import DEFAULT_IMAGE, is_prime, reconstruct
from first_piece_prime_sum_reconstruction import (
    build_walk,
    fitted_prefix,
    first_primes,
    spatial_events,
)
from telegram_23167_operation_audit import guide_endpoint_profile
from telegram_yellow_blue_guide_audit import reconstruct_guide


REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
BEAUFORT_KEY = "THEMATRIXHASYOU"
PHASE32_BLOCK_PREFIX = (
    b"... am I here? Wake up, you... I've designed you a beautiful strategic "
    b"position. One for one, four for one.\r\n\r\n"
)
PHASE322_CLUE = (
    "Raising the stakes without extra chances of winning. A fubcd-king & "
    "oracle-queen, thingky mvps, on a sad board but as wide as the first one seen."
)

# The primary spec exactly matches the solved parent stage.  The remaining
# AES-only specs are cheap compatibility controls for historical OpenSSL
# defaults; they do not change candidate generation.
KDF_SPECS = (
    ("legacy-sha256-aes256", "legacy", "sha256", 32),
    ("legacy-md5-aes256", "legacy", "md5", 32),
    ("legacy-sha1-aes256", "legacy", "sha1", 32),
    ("legacy-sha256-aes192", "legacy", "sha256", 24),
    ("legacy-sha256-aes128", "legacy", "sha256", 16),
    ("pbkdf2-sha256-10000-aes256", "pbkdf2", "sha256", 32),
)

STRICT_SOLVED_OPERATION_INVENTORY = (
    "phase2-aes-cbc",
    "phase3-aes-cbc",
    "phase3.2-aes-cbc",
    "phase3.2.1-beaufort",
    "phase3.2.2-straddling-checkerboard",
)
STRICT_SOLVED_TRANSFORM_INVENTORY = STRICT_SOLVED_OPERATION_INVENTORY + (
    "phase3.2.1-ebcdic-transcode",
    "phase2-sha256-password-derivation",
    "phase3-sha256-password-derivation",
    "phase3.2-sha256-password-derivation",
)


def decrypt_phase32_bytes():
    """Reproduce and return the authenticated, unpadded Phase-3.2 bytes."""
    salt, ciphertext = _load_blob(PHASE32_BLOB_B64)
    key, iv = evp_bytes_to_key(PHASE32_PASSWORD.encode(), salt, "sha256", 32)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    pad = padded[-1]
    if not (1 <= pad <= 16 and padded[-pad:] == bytes((pad,)) * pad):
        raise AssertionError("authenticated Phase-3.2 decryption lost PKCS7 padding")
    plaintext = padded[:-pad]
    if not plaintext.startswith(b"I've been waiting for you."):
        raise AssertionError("authenticated Phase-3.2 plaintext prefix changed")
    return plaintext


def extract_phase32_components(plaintext):
    """Locate sibling components from authenticated delimiters, not offsets."""
    encoded_start = plaintext.index(PHASE32_BLOCK_PREFIX) + len(PHASE32_BLOCK_PREFIX)
    number_marker = b"\r\n\r\n" + VALIDATION_NUM.encode() + b"\r\n\r\n"
    encoded_end = plaintext.index(number_marker, encoded_start)
    encoded_block = plaintext[encoded_start:encoded_end]
    number_start = encoded_end + 4
    clue_start = number_start + len(VALIDATION_NUM) + 4
    clue_marker = PHASE322_CLUE.encode() + b"\r\n\r\n"
    if not plaintext.startswith(clue_marker, clue_start):
        raise AssertionError("Phase-3.2.2 clue boundary changed")
    p32_text = "\r\n".join(
        (P32_TRAILING_BLOB_B64[:64], P32_TRAILING_BLOB_B64[64:])
    ).encode()
    p32_start = clue_start + len(clue_marker)
    if plaintext[p32_start:] != p32_text:
        raise AssertionError("P32 trailing envelope is not the exact Phase-3.2 tail")
    return {
        "encoded_321": encoded_block,
        "validation_num": plaintext[number_start:number_start + len(VALIDATION_NUM)],
        "clue_322": plaintext[clue_start:clue_start + len(PHASE322_CLUE)],
        "p32_text": plaintext[p32_start:],
        "offsets": {
            "encoded_321_start": encoded_start,
            "encoded_321_end": encoded_end,
            "validation_num_start": number_start,
            "clue_322_start": clue_start,
            "p32_start": p32_start,
        },
    }


def ebcdic_1141_ciphertext(encoded_block):
    """Reproduce the community's ISO-8859-1 -> CP1141 byte conversion.

    Python does not ship a CP1141 codec.  GNU iconv does, and is already a
    repository dependency through the original shell reconstruction preserved
    in the chat corpus.  The result is asserted to be lowercase A-Z text.
    """
    completed = subprocess.run(
        ["iconv", "-f", "ISO-8859-1", "-t", "CP1141"],
        input=encoded_block,
        capture_output=True,
        check=True,
    )
    result = completed.stdout.decode("ascii")
    if not re.fullmatch(r"[a-z]+", result):
        raise AssertionError("CP1141 conversion did not yield lowercase ciphertext")
    return result


def beaufort_decrypt(ciphertext, key=BEAUFORT_KEY):
    """Classical Beaufort plaintext: key minus ciphertext modulo 26."""
    key = key.upper()
    return "".join(
        chr(
            (
                ord(key[index % len(key)]) - ord("A")
                - (ord(character.upper()) - ord("A"))
            )
            % 26
            + ord("A")
        )
        for index, character in enumerate(ciphertext)
    )


def readme_architect_letters(path=README_PATH):
    """Extract the displayed speech solely as an independent transcription check."""
    text = Path(path).read_text(encoding="utf-8")
    start = text.index("YOUR LIFE IS THE SUM OF A REMAINDER")
    end = text.index("HOPE YOURE THE ONE CIAO BELLA O", start)
    displayed = text[start:end + len("HOPE YOURE THE ONE CIAO BELLA O")]
    return re.sub(r"[^A-Za-z]", "", displayed).upper()


def derive_sibling_outputs(plaintext=None):
    plaintext = decrypt_phase32_bytes() if plaintext is None else plaintext
    components = extract_phase32_components(plaintext)
    cipher_321 = ebcdic_1141_ciphertext(components["encoded_321"])
    answer_321 = beaufort_decrypt(cipher_321)
    answer_322 = decode(
        components["validation_num"].decode(),
        ALPHA_322,
        *VALIDATION_ESCAPES,
    ).replace(".", "")
    if answer_321 != readme_architect_letters():
        raise AssertionError("fresh 3.2.1 derivation differs from README transcription")
    if answer_322 != VALIDATION_ANSWER:
        raise AssertionError("fresh 3.2.2 derivation differs from validation answer")
    return {
        "phase32_plaintext": plaintext,
        "components": components,
        "cipher_321": cipher_321,
        "answer_321": answer_321,
        "answer_322": answer_322,
    }


def established_prime_selection(answer_322):
    records = fitted_prefix(build_walk(spatial_events()))
    selected = "".join(
        answer_322[record["position_1"] - 1:record["end_1"]]
        for record in records
    )
    return selected, records


def stage0_prime_material(answer_322, image_path=DEFAULT_IMAGE):
    """Two literal readings of the already-prime Stage-0 colored cells."""
    result = reconstruct(image_path)
    prime_cells = tuple(
        item for item in result["objects"] if is_prime(item["spiral_0"])
    )
    indices = tuple(item["spiral_0"] for item in prime_cells)
    in_range = tuple(index for index in indices if index < len(answer_322))
    return {
        "indices_0": indices,
        "source_characters": "".join(item["character"] for item in prime_cells).upper(),
        "blue_source_characters": "".join(
            item["character"] for item in prime_cells if item["color"] == "blue"
        ).upper(),
        "yellow_source_characters": "".join(
            item["character"] for item in prime_cells if item["color"] == "yellow"
        ).upper(),
        "in_range_indices_0": in_range,
        "answer_projection": "".join(answer_322[index] for index in in_range),
    }


def pure_prime_selection(text, base):
    if base not in (0, 1):
        raise ValueError("prime-index base must be zero or one")
    return "".join(
        character
        for index, character in enumerate(text)
        if is_prime(index + base)
    )


def split_final_be_guide_material(answer_322, image_path=DEFAULT_IMAGE):
    """Project the exact 23/16/7 guide referent onto the aligned 3.2.2 text.

    Three readings are kept separate:

    * replay its B/BE endpoint colors through the already-established
      sequential-prime plus prior-yellow positioning rule;
    * select the answer at the guide's cumulative token endpoints;
    * select it at the guide's cumulative raw DBBI-character endpoints.

    The first is the direct operator retarget.  The latter two are literal
    endpoint projections and controls; no modulo or wraparound is introduced.
    """
    guide = reconstruct_guide(image_path)
    chunks = guide["chunks"]
    if chunks[-1][-1] != "be":
        raise AssertionError("guide no longer ends in the split-final BE token")
    split_chunks = chunks[:-1] + (chunks[-1][:-1] + ("b", "e"),)
    endpoint_tokens = tuple(chunk[-1] for chunk in split_chunks)
    colors = "".join("Y" if token == "be" else "B" for token in endpoint_tokens)
    profile = guide_endpoint_profile()
    if colors != profile["endpoint_colors"]:
        raise AssertionError("split-final-BE endpoint colors disagree across audits")

    prior_yellows = 0
    records = []
    selected_parts = []
    for ordinal, (prime, color) in enumerate(zip(first_primes(23), colors), start=1):
        width = 2 if color == "Y" else 1
        position_1 = prime + prior_yellows
        end_1 = position_1 + width - 1
        required = "be" if color == "Y" else "b"
        actual = DBBI[position_1 - 1:end_1]
        if actual != required:
            raise AssertionError(
                f"split guide event {ordinal} expected {required!r} at "
                f"{position_1}-{end_1}, got {actual!r}"
            )
        selected = answer_322[position_1 - 1:end_1]
        selected_parts.append(selected)
        records.append({
            "ordinal": ordinal,
            "prime": prime,
            "color": color,
            "position_1": position_1,
            "end_1": end_1,
            "selected": selected,
        })
        prior_yellows += color == "Y"

    token_endpoints = []
    token_offset = 0
    for chunk in split_chunks:
        token_offset += len(chunk)
        token_endpoints.append(token_offset)

    raw_endpoints = []
    raw_offset = 0
    for chunk in chunks:
        raw_offset += sum(len(token) for token in chunk)
        raw_endpoints.append(raw_offset)
    if raw_offset != len(DBBI) or max(token_endpoints) > len(answer_322):
        raise AssertionError("guide endpoint projection exceeds its aligned source")

    return {
        "colors": colors,
        "blue_count": colors.count("B"),
        "yellow_count": colors.count("Y"),
        "prime_rule_records": tuple(records),
        "prime_rule_selection": "".join(selected_parts),
        "token_endpoints_1": tuple(token_endpoints),
        "token_endpoint_projection": "".join(
            answer_322[position - 1] for position in token_endpoints
        ),
        "raw_endpoints_1": tuple(raw_endpoints),
        "raw_endpoint_projection": "".join(
            answer_322[position - 1] for position in raw_endpoints
        ),
    }


def add_candidate(store, label, value, family):
    value_bytes = value.encode() if isinstance(value, str) else bytes(value)
    if not value_bytes:
        raise ValueError(f"empty candidate: {label}")
    existing = store.get(value_bytes)
    if existing is None:
        store[value_bytes] = {
            "value": value_bytes,
            "labels": [label],
            "families": [family],
        }
    else:
        if label not in existing["labels"]:
            existing["labels"].append(label)
        if family not in existing["families"]:
            existing["families"].append(family)


def build_candidates(
    answer_321,
    answer_322,
    phase32_plaintext,
    p32_start,
    image_path=DEFAULT_IMAGE,
):
    candidates = {}
    selected, records = established_prime_selection(answer_322)
    stage0 = stage0_prime_material(answer_322, image_path)
    split_guide = split_final_be_guide_material(answer_322, image_path)

    add_candidate(candidates, "complete_321", answer_321, "whole-text")
    add_candidate(candidates, "complete_322_control", answer_322, "whole-text")
    add_candidate(candidates, "complete_321_then_322", answer_321 + answer_322, "whole-text")
    add_candidate(candidates, "complete_322_then_321_control", answer_322 + answer_321, "whole-text")

    add_candidate(candidates, "established_23_event_selection", selected, "operator-data")
    add_candidate(candidates, "selection_then_322", selected + answer_322, "operator-data")
    add_candidate(candidates, "321_then_selection", answer_321 + selected, "operator-data")
    add_candidate(
        candidates,
        "pure_prime_0based_322_control",
        pure_prime_selection(answer_322, 0),
        "operator-data-control",
    )
    add_candidate(
        candidates,
        "pure_prime_1based_322_control",
        pure_prime_selection(answer_322, 1),
        "operator-data-control",
    )

    add_candidate(candidates, "stage0_prime_source_chars", stage0["source_characters"], "stage0-primes")
    add_candidate(candidates, "stage0_blue_prime_source_chars", stage0["blue_source_characters"], "stage0-primes")
    add_candidate(candidates, "stage0_yellow_prime_source_chars", stage0["yellow_source_characters"], "stage0-primes")
    add_candidate(candidates, "stage0_prime_indices_projected_to_322", stage0["answer_projection"], "stage0-primes")
    add_candidate(candidates, "stage0_prime_source_then_322", stage0["source_characters"] + answer_322, "stage0-primes")

    parameter_candidates = {
        "keys_321_then_322": BEAUFORT_KEY + ALPHA_322 + "14",
        "parameters_321_then_322": "1141" + BEAUFORT_KEY + ALPHA_322 + "14",
        "operations_321_then_322": "EBCDIC1141BEAUFORTVIC14",
        "full_operations_321_then_322": "EBCDIC1141BEAUFORTSTRADDLINGCHECKERBOARD14",
    }
    for label, value in parameter_candidates.items():
        add_candidate(candidates, label, value, "sibling-parameters")

    prefix_with_separator = phase32_plaintext[:p32_start]
    if not prefix_with_separator.endswith(b"\r\n\r\n"):
        raise AssertionError("P32 parent prefix no longer ends in the expected separator")
    add_candidate(
        candidates,
        "exact_parent_bytes_before_p32_with_separator",
        prefix_with_separator,
        "parent-byte-prefix",
    )
    add_candidate(
        candidates,
        "exact_parent_bytes_before_p32_without_separator",
        prefix_with_separator[:-4],
        "parent-byte-prefix",
    )

    guide_selection = split_guide["prime_rule_selection"]
    add_candidate(
        candidates,
        "split_final_be_prime_rule_selection",
        guide_selection,
        "split-final-be-guide",
    )
    add_candidate(
        candidates,
        "split_final_be_selection_then_322",
        guide_selection + answer_322,
        "split-final-be-guide",
    )
    add_candidate(
        candidates,
        "321_then_split_final_be_selection",
        answer_321 + guide_selection,
        "split-final-be-guide",
    )
    add_candidate(
        candidates,
        "split_final_be_token_endpoint_projection",
        split_guide["token_endpoint_projection"],
        "split-final-be-guide",
    )
    add_candidate(
        candidates,
        "split_final_be_raw_endpoint_projection",
        split_guide["raw_endpoint_projection"],
        "split-final-be-guide",
    )

    return tuple(candidates.values()), {
        "established_selection": selected,
        "established_event_count": len(records),
        "established_single_count": sum(len(record["required"]) == 1 for record in records),
        "established_digraph_count": sum(len(record["required"]) == 2 for record in records),
        "established_event_types": "".join(record["type"] for record in records),
        "established_selected_length": sum(len(record["required"]) for record in records),
        "stage0": stage0,
        "split_final_be_guide": split_guide,
    }


def password_materials(candidates):
    """Raw controls plus the chain-native single-SHA256-hex passwords."""
    materials = {}
    for candidate in candidates:
        value = candidate["value"]
        forms = (
            ("raw", value),
            ("sha256-hex", hashlib.sha256(value).hexdigest().encode()),
        )
        for treatment, material in forms:
            key = material
            record = materials.setdefault(
                key,
                {"material": material, "sources": [], "treatments": []},
            )
            record["sources"].extend(
                label for label in candidate["labels"] if label not in record["sources"]
            )
            if treatment not in record["treatments"]:
                record["treatments"].append(treatment)
    return tuple(materials.values())


def derive_aes_key_iv(password, salt, spec):
    _label, kind, digest, key_len = spec
    if kind == "legacy":
        return evp_bytes_to_key(password, salt, digest, key_len)
    if kind == "pbkdf2":
        return pbkdf2_bytes_to_key(password, salt, 10000, digest, key_len, 16)
    raise ValueError(f"unknown KDF kind: {kind}")


def public_addresses(private_key):
    value = int.from_bytes(private_key, "big")
    if not 1 <= value < SECP256K1_ORDER:
        return None
    public = ec.derive_private_key(value, ec.SECP256K1()).public_key().public_numbers()
    x = public.x.to_bytes(32, "big")
    uncompressed = b"\x04" + x + public.y.to_bytes(32, "big")
    compressed = bytes((2 + (public.y & 1),)) + x
    return {
        "compressed_p2pkh": base58check(b"\x00" + hash160(compressed)),
        "uncompressed_p2pkh": base58check(b"\x00" + hash160(uncompressed)),
    }


def structural_trials(materials):
    raw = base64.b64decode(P32_TRAILING_BLOB_B64, validate=True)
    if len(raw) != 96 or raw[:8] != b"Salted__":
        raise AssertionError("P32 envelope geometry changed")
    salt, ciphertext = raw[8:16], raw[16:]
    if len(ciphertext) != 80:
        raise AssertionError("P32 ciphertext is no longer exactly five AES blocks")

    hits = []
    trial_count = 0
    for entry in materials:
        for spec in KDF_SPECS:
            trial_count += 1
            key, iv = derive_aes_key_iv(entry["material"], salt, spec)
            decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
            padded = decryptor.update(ciphertext) + decryptor.finalize()
            if padded[-16:] != b"\x10" * 16:
                continue
            payload = padded[:64]
            halves = (payload[:32], payload[32:])
            addresses = tuple(public_addresses(half) for half in halves)
            hits.append({
                "sources": tuple(entry["sources"]),
                "treatments": tuple(entry["treatments"]),
                "password_material_sha256": hashlib.sha256(entry["material"]).hexdigest(),
                "kdf": spec[0],
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "both_valid_scalars": all(address is not None for address in addresses),
                "addresses": addresses,
            })
    return {
        "envelope_bytes": len(raw),
        "ciphertext_bytes": len(ciphertext),
        "ciphertext_blocks": len(ciphertext) // 16,
        "two_key_payload_bytes": 64,
        "required_padding_hex": (b"\x10" * 16).hex(),
        "unconditional_false_positive_probability": "2^-128",
        "conditional_on_last_byte_0x10_probability": "2^-120",
        "trial_count": trial_count,
        "hits": hits,
    }


def interpretation_checks(derived, construction):
    # The 23/16/7 wording is inherited from the Matrix screenplay; the puzzle
    # substitutes ciphers/encryptions/passwords for individuals/female/male.
    # The strict inventories make the alternative "literal recap count" claim
    # falsifiable under a disclosed policy instead of freely counting steps.
    guide_profile = guide_endpoint_profile()
    return {
        "triple": (23, 16, 7),
        "architect_source_triple": (23, 16, 7),
        "prime_walk_profile_events_singles_digraphs": (
            construction["established_event_count"],
            construction["established_single_count"],
            construction["established_digraph_count"],
        ),
        "split_final_be_guide_profile_endpoints_blue_yellow": (
            guide_profile["endpoint_count"],
            guide_profile["blue_endpoints"],
            guide_profile["yellow_endpoints"],
        ),
        "inherited_from_screenplay": True,
        "prime_walk_matches_23_16_7": (
            construction["established_event_count"],
            construction["established_single_count"],
            construction["established_digraph_count"],
        ) == (23, 16, 7),
        "split_final_be_guide_matches_23_16_7": (
            guide_profile["endpoint_count"],
            guide_profile["blue_endpoints"],
            guide_profile["yellow_endpoints"],
        ) == (23, 16, 7),
        "strict_solved_crypto_operation_count": len(STRICT_SOLVED_OPERATION_INVENTORY),
        "strict_solved_crypto_operations": STRICT_SOLVED_OPERATION_INVENTORY,
        "strict_solved_transform_count": len(STRICT_SOLVED_TRANSFORM_INVENTORY),
        "strict_solved_transforms": STRICT_SOLVED_TRANSFORM_INVENTORY,
        "recap_matches_23_or_16": len(STRICT_SOLVED_OPERATION_INVENTORY) in (23, 16)
        or len(STRICT_SOLVED_TRANSFORM_INVENTORY) in (23, 16),
        "assessment": (
            "The number triple is exact screenplay inheritance and the disclosed "
            "solved-chain inventories do not approach 23 or 16. The established "
            "prime walk is 23/15/8, not 23/16/7; the exact 23/16/7 recurrence "
            "belongs to the separate community-recovered split-final-BE guide. "
            "Neither makes the parody sentence a standalone P32 instruction."
        ),
        "answer_321_length": len(derived["answer_321"]),
        "answer_322_length": len(derived["answer_322"]),
    }


def audit(image_path=DEFAULT_IMAGE):
    derived = derive_sibling_outputs()
    candidates, construction = build_candidates(
        derived["answer_321"],
        derived["answer_322"],
        derived["phase32_plaintext"],
        derived["components"]["offsets"]["p32_start"],
        image_path,
    )
    materials = password_materials(candidates)
    structural = structural_trials(materials)
    candidate_manifest = tuple(
        {
            "labels": tuple(candidate["labels"]),
            "families": tuple(candidate["families"]),
            "length": len(candidate["value"]),
            "sha256": hashlib.sha256(candidate["value"]).hexdigest(),
        }
        for candidate in candidates
    )
    return {
        "phase32_plaintext_bytes": len(derived["phase32_plaintext"]),
        "phase32_plaintext_sha256": hashlib.sha256(
            derived["phase32_plaintext"]
        ).hexdigest(),
        "component_offsets": derived["components"]["offsets"],
        "encoded_321_bytes": len(derived["components"]["encoded_321"]),
        "cipher_321_length": len(derived["cipher_321"]),
        "answer_321_length": len(derived["answer_321"]),
        "answer_321_sha256": hashlib.sha256(derived["answer_321"].encode()).hexdigest(),
        "answer_322_length": len(derived["answer_322"]),
        "answer_322_sha256": hashlib.sha256(derived["answer_322"].encode()).hexdigest(),
        "candidate_count": len(candidates),
        "password_material_count": len(materials),
        "candidate_manifest": candidate_manifest,
        "construction": construction,
        "interpretation": interpretation_checks(derived, construction),
        "structural_oracle": structural,
    }


def self_test():
    assert beaufort_decrypt("vtkvplme", BEAUFORT_KEY) == "YOURLIFE"
    report = audit()
    assert report["phase32_plaintext_bytes"] == 2422
    assert report["phase32_plaintext_sha256"] == (
        "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"
    )
    assert report["encoded_321_bytes"] == 1539
    assert report["cipher_321_length"] == report["answer_321_length"] == 1539
    assert report["answer_322_length"] == 91
    assert report["construction"]["established_event_count"] == 23
    assert report["construction"]["established_single_count"] == 15
    assert report["construction"]["established_digraph_count"] == 8
    assert report["construction"]["established_selected_length"] == 31
    assert report["construction"]["established_selection"] == (
        "NCSYANGCAHIRIASOGALEAFAYANESTVE"
    )
    assert report["construction"]["stage0"]["indices_0"] == (
        7, 23, 31, 47, 71, 79, 103, 127, 151, 167, 191,
    )
    split_guide = report["construction"]["split_final_be_guide"]
    assert (split_guide["blue_count"], split_guide["yellow_count"]) == (16, 7)
    assert split_guide["prime_rule_selection"] == (
        "NCSYANGCAHIRIASOGALEAFAYANESTV"
    )
    assert split_guide["token_endpoint_projection"] == "NCSYAAORTERKBLTATRNEAED"
    assert split_guide["raw_endpoint_projection"] == "NCSYNGCAIIASOGLEAAANETE"
    assert report["structural_oracle"]["ciphertext_bytes"] == 80
    assert report["structural_oracle"]["ciphertext_blocks"] == 5
    assert report["structural_oracle"]["trial_count"] == (
        report["password_material_count"] * len(KDF_SPECS)
    )
    assert not report["interpretation"]["prime_walk_matches_23_16_7"]
    assert report["interpretation"]["split_final_be_guide_matches_23_16_7"]
    print(
        "[*] self-test OK: exact sibling derivation, disclosed candidates, "
        "five-block/two-key oracle, and interpretation controls reproduce"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit(args.image)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
