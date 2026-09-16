#!/usr/bin/env python3
"""Phase 509A: closed-system consumer/validator feasibility inventory."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

import cb_common
import key_shape_classifier as shapes
import phase507_faed_terminal_aes_oracle as phase507
import raw_key_chunk_audit as raw_keys
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validators() -> list[dict]:
    """Frozen classification; none of these entries executes an oracle."""
    return [
        {
            "id": "exact_known_p2pkh_address",
            "consumer": "32-byte secp256k1 scalar -> compressed/uncompressed P2PKH",
            "role": "terminal_confirmation",
            "search_gradient": "none",
            "strength": "exact 160-bit hash target; two independently known puzzle addresses",
            "false_accept_bound_per_derived_address": "2/2^160",
            "eligible_for_promotion_alone": True,
            "implementation": "binary_key_material_backfill.private_key_details",
        },
        {
            "id": "aes_phase410_cbc",
            "consumer": "EVP_BytesToKey/SHA-256 -> AES-256-CBC -> PKCS7",
            "role": "terminal_confirmation_with_classifier",
            "search_gradient": "none",
            "strength": "padding alone about 1/255; Phase-507 promotion additionally requires z>=8 text or exact 64-byte/full-block binary shape",
            "false_accept_bound_per_attempt": "classifier-dependent; padding alone is not promotable",
            "eligible_for_promotion_alone": False,
            "implementation": "phase480_p32_address_password_audit.classify_padded",
        },
        {
            "id": "aes_keywrap_integrity",
            "consumer": "RFC3394/RFC5649 or OpenSSL-compatible AES key unwrap",
            "role": "terminal_confirmation",
            "search_gradient": "none",
            "strength": "built-in integrity value; substantially stronger than CBC padding",
            "false_accept_bound_per_attempt": "at most about 2^-32 for the weakest padded integrity-prefix case; usually stronger",
            "eligible_for_promotion_alone": True,
            "implementation": "cb_common.aes_keywrap_try_open_bytes",
        },
        {
            "id": "wif_base58check",
            "consumer": "mainnet WIF -> scalar",
            "role": "format_filter_then_address_confirmation",
            "search_gradient": "none",
            "strength": "32-bit Base58Check plus fixed version/length; unrelated valid WIF is not the puzzle solution",
            "false_accept_bound_per_candidate": "no better than about 2^-32 before address matching",
            "eligible_for_promotion_alone": False,
            "implementation": "key_shape_classifier.wif_to_private_key",
        },
        {
            "id": "bip39_checksum",
            "consumer": "12/15/18/21/24 BIP39 words -> master and BIP44 key",
            "role": "format_filter_then_address_confirmation",
            "search_gradient": "none",
            "strength": "only 4-8 checksum bits before exact derived-address comparison",
            "false_accept_bound_per_word_window": "2^-4 through 2^-8 after every word is in the 2048-word list",
            "eligible_for_promotion_alone": False,
            "implementation": "key_shape_classifier.find_bip39",
        },
        {
            "id": "base58check_container",
            "consumer": "Base58Check WIF/BIP38/extended-key-shaped text",
            "role": "format_filter",
            "search_gradient": "none",
            "strength": "32-bit checksum plus type-specific structure",
            "false_accept_bound_per_candidate": "approximately 2^-32 before type fields",
            "eligible_for_promotion_alone": False,
            "implementation": "key_shape_classifier.base58check_decode",
        },
        {
            "id": "raw_or_hex_scalar_shape",
            "consumer": "32 raw bytes or exactly 64 hex characters",
            "role": "shape_only",
            "search_gradient": "none",
            "strength": "nearly every uniformly random 32-byte value is a valid secp256k1 scalar",
            "false_accept_bound_per_candidate": "approximately 1",
            "eligible_for_promotion_alone": False,
            "implementation": "key_shape_classifier.raw_binary_halves/find_hex64",
        },
        {
            "id": "printability_or_language",
            "consumer": "decrypted bytes or decoded symbol stream",
            "role": "soft_proxy",
            "search_gradient": "yes, but only heuristic",
            "strength": "must earn a same-budget real-versus-null calibration before prioritizing searches",
            "false_accept_bound_per_candidate": "objective- and family-size-dependent",
            "eligible_for_promotion_alone": False,
            "implementation": "cb_common.printable_z_score / quadgram objectives",
        },
    ]


def phase507_coverage() -> dict:
    manifest = phase507.validate_manifest()
    result = json.loads(phase507.RESULT.read_text())
    if result.get("verdict") != "bounded_negative":
        raise RuntimeError("Phase-507 result disposition changed")
    if result.get("candidate_count") != 43 or result.get("decryptions") != 129:
        raise RuntimeError("Phase-507 coverage changed")
    lengths = []
    for row in manifest["candidates"]:
        raw = base64.b64decode(row["preimage_b64"], validate=True)
        if not raw.isalpha() or not raw.isupper():
            raise RuntimeError("Phase-507 terminal byte shape changed")
        lengths.append(len(raw))
    return {
        "candidate_count": 43,
        "terminal_length_min": min(lengths),
        "terminal_length_max": max(lengths),
        "covered": {
            "candidate_material": "SHA256(terminal).hexdigest().encode('ascii')",
            "consumer": "Phase-410 legacy SHA256 EVP_BytesToKey/AES-256-CBC",
            "targets": ["SALPH", "COSMIC", "P32TRAILING"],
            "decryptions": 129,
            "padding_valid": result["padding_valid_diagnostic_count"],
            "promoted": result["promoted_count"],
        },
        "not_covered_for_these_43_terminals": [
            "SHA256(terminal).digest() as a secp256k1 scalar matched to the two known addresses",
            "raw terminal bytes as a passphrase",
            "alternate KDF/cipher/mode or AES Key Wrap",
            "URLBLOB",
            "candidate mutation or substring extraction",
        ],
    }


def recommended_next_family() -> dict:
    return {
        "id": "phase509b_terminal_digest_to_known_address",
        "inputs": "the unchanged 43 exact Phase-507 terminal byte strings",
        "transformation": "SHA256(terminal).digest()",
        "consumer": "secp256k1 private scalar; derive compressed and uncompressed P2PKH",
        "targets": [PRIZE_ADDRESS, HALVING_ADDRESS],
        "derived_addresses": 43 * 2,
        "exact_address_comparisons": 43 * 2 * 2,
        "family_false_accept_union_bound": "172/2^160 (approximately 1.18e-46)",
        "search_gradient": "none; exact terminal oracle only",
        "mutations": "none",
        "reason": "Phase 410 independently fixes SHA-256 at solved boundaries; the puzzle goal and two target addresses independently fix the consumer",
    }


def report() -> dict:
    registry = validators()
    coverage = phase507_coverage()
    if len(raw_keys.KNOWN_TARGETS) != 10:
        raise RuntimeError("raw-key target registry changed")
    for address in (PRIZE_ADDRESS, HALVING_ADDRESS):
        payload = shapes.base58check_decode(address)
        if payload is None or len(payload) != 21 or payload[0] != 0:
            raise RuntimeError("known address is not a valid mainnet P2PKH target")
    return {
        "phase": "509A",
        "status": "feasibility_audit_complete_no_oracle_run",
        "faed_scored": False,
        "gpu_used": False,
        "validator_count": len(registry),
        "validators": registry,
        "phase507_coverage": coverage,
        "recommended_next_family": recommended_next_family(),
        "key_conclusion": "terminal validators can confirm completed candidates but cannot guide transposition search",
        "source_hashes": {
            "cb_common": sha(Path(cb_common.__file__)),
            "key_shape_classifier": sha(Path(shapes.__file__)),
            "phase507_runner": sha(Path(phase507.__file__)),
            "phase507_manifest": sha(phase507.MANIFEST),
            "phase507_result": sha(phase507.RESULT),
            "raw_key_chunk_audit": sha(Path(raw_keys.__file__)),
        },
    }


def self_test() -> dict:
    value = report()
    ids = [row["id"] for row in value["validators"]]
    if len(ids) != len(set(ids)) or len(ids) != 8:
        raise AssertionError("validator registry is not eight unique entries")
    terminal = [row for row in value["validators"]
                if row["role"].startswith("terminal_confirmation")]
    if any(row["search_gradient"] != "none" for row in terminal):
        raise AssertionError("terminal validator was mislabeled as a gradient")
    next_family = value["recommended_next_family"]
    if next_family["derived_addresses"] != 86 or next_family["exact_address_comparisons"] != 172:
        raise AssertionError("Phase-509B budget changed")
    return {"self_test": "pass", "validator_count": len(ids),
            "phase507_candidates": 43, "phase509b_comparisons": 172}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.self_test == args.report:
        parser.error("choose exactly one of --self-test or --report")
    value = self_test() if args.self_test else report()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

