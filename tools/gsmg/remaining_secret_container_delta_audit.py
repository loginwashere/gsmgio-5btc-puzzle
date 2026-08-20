#!/usr/bin/env python3
"""Seed 8 delta: exact secret-container formats not covered by Phase 342.

Frozen before the real run:

* Reuse Phase 342's identical 42-candidate / 12,128-retained-body corpus,
  three scopes (whole body, line, token), and existing strict depth-one
  hex/Base64/gzip/zlib/ZIP decoders. Add no candidates, KDFs, ciphers,
  modes, blobs, retention rules, scopes, or decoder edges.
* Add exactly five validator families absent from Phase 342:
  BIP38 encrypted keys; Casascius mini private keys; Bitcoin mainnet/testnet
  SLIP-132 extended keys; checksummed Bitcoin Core output descriptors; and
  complete logical Bitcoin Core wallet records (`key`, checksum-bearing
  `ckey`, or tightly structured `mkey`). DER, PSBT, and transactions are not
  reimplemented here.
* A structurally valid unrelated container is review material, not a puzzle
  solution. Only a scalar-bearing container whose derived address matches the
  prize/Phase-331 exact target registry is an exact hit. BIP38 is detection
  only: no scrypt or second password semantics are introduced.
* Stop after one run over the frozen corpus. No typo repair, substring tree,
  new decoding layer, or candidate-specific follow-up after seeing results.

Primary contracts (retrieved 2026-08-20): bitcoin/bips BIP-0038;
satoshilabs/slips SLIP-0132; Bitcoin Core descriptor.cpp/descriptors.md,
walletdb.cpp/walletdb.h/serialize.h/crypter.h/pubkey.h/hash.h; and Casascius's
original Bitcoin-Address-Utility Model/MiniKeyPair.cs.
"""

import argparse
import base64
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import key_shape_classifier  # noqa: E402
from first_hint_hash_audit import SECP256K1_ORDER, base58check  # noqa: E402
from half_better_half_algebra_audit import (  # noqa: E402
    EXPECTED_CANDIDATE_DIGEST,
    KNOWN_TARGET_HASH160S,
    candidate_list_digest,
    check_scalar,
    frozen_candidates,
)
from typed_decode_parse_ladder_audit import (  # noqa: E402
    DECODERS,
    extract_scopes,
    iter_retained_bodies,
)

EXPECTED_BODY_COUNT = 12_128
EXPECTED_SEGMENT_COUNT = 150_141
FORMAT_NAMES = ("bip38", "casascius_minikey", "slip132", "descriptor", "bitcoin_core_record")
BASE58_TOKEN_RE = re.compile(rb"^[1-9A-HJ-NP-Za-km-z]+$")
DERIVED_PATH_RE = re.compile(r"^(?:/(?:[0-9]+(?:['h])?|\*|<[^/<>]+>))*$")


# ---------------------------------------------------------------------------
# Shared exact primitives
# ---------------------------------------------------------------------------

def sha256d(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _valid_pubkey(data):
    if len(data) not in (33, 65) or data[0] not in (2, 3, 4):
        return False
    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), data)
        return True
    except ValueError:
        return False


def _scalar_ok(data):
    return len(data) == 32 and 1 <= int.from_bytes(data, "big") < SECP256K1_ORDER


def _base58_payload(token):
    try:
        text = token.decode("ascii") if isinstance(token, bytes) else token
    except UnicodeDecodeError:
        return None
    return key_shape_classifier.base58check_decode(text)


# ---------------------------------------------------------------------------
# 1. BIP38 -- 58 chars, Base58Check, 39-byte payload, exact prefix/flags.
# ---------------------------------------------------------------------------

def parse_bip38(segment):
    if len(segment) != 58 or not segment.startswith(b"6P") or not BASE58_TOKEN_RE.fullmatch(segment):
        return None
    payload = _base58_payload(segment)
    if payload is None or len(payload) != 39:
        return None
    prefix, flag = payload[:2], payload[2]
    if prefix == b"\x01\x42":
        if flag not in (0xC0, 0xE0):
            return None
        mode = "non_ec_multiply"
        lot_sequence = False
    elif prefix == b"\x01\x43":
        if flag not in (0x00, 0x04, 0x20, 0x24):
            return None
        mode = "ec_multiply"
        lot_sequence = bool(flag & 0x04)
    else:
        return None
    return {
        "mode": mode,
        "compressed": bool(flag & 0x20),
        "lot_sequence": lot_sequence,
        "address_hash": payload[3:7].hex(),
    }


# ---------------------------------------------------------------------------
# 2. Casascius mini private keys -- original utility's exact rules.
# ---------------------------------------------------------------------------

def parse_minikey(segment):
    if len(segment) not in (22, 26, 30) or not segment.startswith(b"S"):
        return None
    if not BASE58_TOKEN_RE.fullmatch(segment):
        return None
    if hashlib.sha256(segment + b"?").digest()[0] != 0:
        return None
    scalar = hashlib.sha256(segment).digest()
    if not _scalar_ok(scalar):
        return None
    return {"length": len(segment), "scalar": scalar}


# ---------------------------------------------------------------------------
# 3. SLIP-132 Bitcoin mainnet/testnet extended keys.
# ---------------------------------------------------------------------------

SLIP132_VERSIONS = {
    bytes.fromhex("049d7cb2"): ("ypub", "public", "mainnet"),
    bytes.fromhex("049d7878"): ("yprv", "private", "mainnet"),
    bytes.fromhex("04b24746"): ("zpub", "public", "mainnet"),
    bytes.fromhex("04b2430c"): ("zprv", "private", "mainnet"),
    bytes.fromhex("0295b43f"): ("Ypub", "public", "mainnet"),
    bytes.fromhex("0295b005"): ("Yprv", "private", "mainnet"),
    bytes.fromhex("02aa7ed3"): ("Zpub", "public", "mainnet"),
    bytes.fromhex("02aa7a99"): ("Zprv", "private", "mainnet"),
    bytes.fromhex("044a5262"): ("upub", "public", "testnet"),
    bytes.fromhex("044a4e28"): ("uprv", "private", "testnet"),
    bytes.fromhex("045f1cf6"): ("vpub", "public", "testnet"),
    bytes.fromhex("045f18bc"): ("vprv", "private", "testnet"),
}


def parse_slip132(segment):
    if not 107 <= len(segment) <= 113 or not BASE58_TOKEN_RE.fullmatch(segment):
        return None
    payload = _base58_payload(segment)
    if payload is None or len(payload) != 78 or payload[:4] not in SLIP132_VERSIONS:
        return None
    label, key_kind, network = SLIP132_VERSIONS[payload[:4]]
    depth = payload[4]
    parent_fingerprint = payload[5:9]
    child_number = payload[9:13]
    chain_code = payload[13:45]
    key_data = payload[45:78]
    if depth == 0 and (parent_fingerprint != b"\x00" * 4 or child_number != b"\x00" * 4):
        return None
    if chain_code == b"\x00" * 32:
        return None
    scalar = None
    if key_kind == "private":
        if key_data[0] != 0 or not _scalar_ok(key_data[1:]):
            return None
        scalar = key_data[1:]
    elif not _valid_pubkey(key_data):
        return None
    return {
        "label": label, "key_kind": key_kind, "network": network,
        "depth": depth, "scalar": scalar,
    }


# ---------------------------------------------------------------------------
# 4. Bitcoin Core output descriptors -- checksum plus bounded full grammar.
# ---------------------------------------------------------------------------

DESCRIPTOR_INPUT_CHARSET = (
    "0123456789()[],'/*abcdefgh@:$%{}"
    "IJKLMNOPQRSTUVWXYZ&+-.;<=>?!^_|~"
    "ijklmnopqrstuvwxyzABCDEFGH`#\"\\ "
)
DESCRIPTOR_CHECKSUM_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _descriptor_polymod(c, value):
    c0 = c >> 35
    c = ((c & 0x7FFFFFFFF) << 5) ^ value
    for bit, generator in enumerate((0xF5DEE51989, 0xA9FDCA3312, 0x1BAB10E32D,
                                     0x3706B1677A, 0x644D626FFD)):
        if c0 & (1 << bit):
            c ^= generator
    return c


def descriptor_checksum(payload):
    c, cls, cls_count = 1, 0, 0
    for character in payload:
        position = DESCRIPTOR_INPUT_CHARSET.find(character)
        if position < 0:
            return None
        c = _descriptor_polymod(c, position & 31)
        cls = cls * 3 + (position >> 5)
        cls_count += 1
        if cls_count == 3:
            c = _descriptor_polymod(c, cls)
            cls = cls_count = 0
    if cls_count:
        c = _descriptor_polymod(c, cls)
    for _ in range(8):
        c = _descriptor_polymod(c, 0)
    c ^= 1
    return "".join(DESCRIPTOR_CHECKSUM_CHARSET[(c >> (5 * (7 - j))) & 31] for j in range(8))


def _split_args(text):
    args, start = [], 0
    depths = {"(": 0, "[": 0, "{": 0, "<": 0}
    close_to_open = {")": "(", "]": "[", "}": "{", ">": "<"}
    for index, character in enumerate(text):
        if character in depths:
            depths[character] += 1
        elif character in close_to_open:
            opener = close_to_open[character]
            depths[opener] -= 1
            if depths[opener] < 0:
                return None
        elif character == "," and not any(depths.values()):
            args.append(text[start:index])
            start = index + 1
    if any(depths.values()):
        return None
    args.append(text[start:])
    return args if all(arg != "" for arg in args) else None


def _parse_wif(text):
    payload = _base58_payload(text)
    if payload is None or len(payload) not in (33, 34) or payload[0] not in (0x80, 0xEF):
        return None
    if len(payload) == 34 and payload[-1] != 1:
        return None
    scalar = payload[1:33]
    return scalar if _scalar_ok(scalar) else None


def _parse_descriptor_key(text):
    if text.startswith("["):
        end = text.find("]")
        if end < 0 or not re.fullmatch(r"[0-9a-fA-F]{8}(?:/[0-9]+(?:['h])?)*", text[1:end]):
            return None
        text = text[end + 1:]
    slash = text.find("/")
    base, suffix = (text, "") if slash < 0 else (text[:slash], text[slash:])
    if not DERIVED_PATH_RE.fullmatch(suffix):
        return None
    scalar = _parse_wif(base)
    if scalar is not None:
        return {"kind": "wif", "scalar": scalar}
    try:
        encoded = base.encode("ascii", "strict")
    except UnicodeEncodeError:
        return None
    slip = parse_slip132(encoded)
    if slip is not None:
        return {"kind": slip["label"], "scalar": slip["scalar"]}
    payload = _base58_payload(base)
    if payload is not None and len(payload) == 78 and payload[:4] in (
            bytes.fromhex("0488ade4"), bytes.fromhex("0488b21e"),
            bytes.fromhex("04358394"), bytes.fromhex("043587cf")):
        key_data = payload[45:]
        if key_data[0] == 0 and _scalar_ok(key_data[1:]):
            return {"kind": "xprv_or_tprv", "scalar": key_data[1:]}
        if _valid_pubkey(key_data):
            return {"kind": "xpub_or_tpub", "scalar": None}
        return None
    try:
        raw = bytes.fromhex(base)
    except ValueError:
        return None
    if _valid_pubkey(raw):
        return {"kind": "pubkey", "scalar": None}
    if len(raw) == 32:
        x = int.from_bytes(raw, "big")
        p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        if x < p and pow((pow(x, 3, p) + 7) % p, (p - 1) // 2, p) == 1:
            return {"kind": "xonly_pubkey", "scalar": None}
    return None


def _parse_descriptor_expr(text):
    match = re.fullmatch(r"([a-z_]+)\((.*)\)", text)
    if not match:
        return None
    name, inner = match.groups()
    args = _split_args(inner)
    if args is None:
        return None
    key_funcs = {"pk", "pkh", "wpkh", "combo", "rawtr"}
    wrap_funcs = {"sh", "wsh"}
    multi_funcs = {"multi", "sortedmulti", "multi_a", "sortedmulti_a"}
    if name in key_funcs and len(args) == 1:
        key = _parse_descriptor_key(args[0])
        return None if key is None else {"functions": [name], "keys": [key]}
    if name in wrap_funcs and len(args) == 1:
        child = _parse_descriptor_expr(args[0])
        return None if child is None else {"functions": [name] + child["functions"], "keys": child["keys"]}
    if name in multi_funcs and len(args) >= 2 and args[0].isdigit():
        threshold = int(args[0])
        keys = [_parse_descriptor_key(arg) for arg in args[1:]]
        if not 1 <= threshold <= len(keys) or any(key is None for key in keys):
            return None
        return {"functions": [name], "keys": keys}
    if name == "tr" and len(args) == 1:
        key = _parse_descriptor_key(args[0])
        return None if key is None else {"functions": [name], "keys": [key]}
    if name == "raw" and len(args) == 1 and len(args[0]) % 2 == 0:
        try:
            bytes.fromhex(args[0])
            return {"functions": [name], "keys": []}
        except ValueError:
            return None
    return None


def parse_descriptor(segment):
    try:
        text = segment.decode("ascii")
    except UnicodeDecodeError:
        return None
    if text.count("#") != 1:
        return None
    payload, supplied = text.rsplit("#", 1)
    if len(supplied) != 8 or descriptor_checksum(payload) != supplied:
        return None
    parsed = _parse_descriptor_expr(payload)
    if parsed is None:
        return None
    return {
        "functions": parsed["functions"],
        "key_kinds": [key["kind"] for key in parsed["keys"]],
        "scalars": [key["scalar"] for key in parsed["keys"] if key["scalar"] is not None],
    }


# ---------------------------------------------------------------------------
# 5. Complete logical Bitcoin Core wallet key/value records.
# ---------------------------------------------------------------------------

def _compact_size(data, position):
    if position >= len(data):
        raise ValueError("missing CompactSize")
    marker = data[position]
    position += 1
    if marker < 253:
        return marker, position
    sizes = {253: 2, 254: 4, 255: 8}
    width = sizes[marker]
    if position + width > len(data):
        raise ValueError("truncated CompactSize")
    value = int.from_bytes(data[position:position + width], "little")
    minimum = {253: 253, 254: 0x10000, 255: 0x100000000}[marker]
    if value < minimum or value > 0x02000000:
        raise ValueError("noncanonical/oversized CompactSize")
    return value, position + width


def _vector(data, position, maximum=4096):
    length, position = _compact_size(data, position)
    if length > maximum or position + length > len(data):
        raise ValueError("invalid vector length")
    return data[position:position + length], position + length


def _core_tag(data, position=0):
    raw, position = _vector(data, position, maximum=32)
    try:
        return raw.decode("ascii"), position
    except UnicodeDecodeError as exc:
        raise ValueError("non-ASCII wallet tag") from exc


def _core_key_record(data, position, encrypted):
    pubkey, position = _vector(data, position, maximum=65)
    if not _valid_pubkey(pubkey):
        return None
    secret, position = _vector(data, position, maximum=1024)
    if encrypted:
        if len(secret) < 32 or len(secret) % 16 or position + 32 != len(data):
            return None
        checksum = data[position:]
        if checksum != sha256d(secret):
            return None
        return {"record_type": "ckey", "pubkey_kind": "compressed" if len(pubkey) == 33 else "uncompressed",
                "scalar": None, "has_checksum": True}
    if position not in (len(data), len(data) - 32):
        return None
    if position + 32 == len(data) and data[position:] != sha256d(pubkey + secret):
        return None
    try:
        private = serialization.load_der_private_key(secret, password=None)
    except (TypeError, ValueError):
        return None
    if not isinstance(private, ec.EllipticCurvePrivateKey) or not isinstance(private.curve, ec.SECP256K1):
        return None
    scalar = private.private_numbers().private_value.to_bytes(32, "big")
    derived = private.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.CompressedPoint if len(pubkey) == 33 else serialization.PublicFormat.UncompressedPoint,
    )
    if derived != pubkey:
        return None
    return {"record_type": "key", "pubkey_kind": "compressed" if len(pubkey) == 33 else "uncompressed",
            "scalar": scalar, "has_checksum": position + 32 == len(data)}


def _core_master_record(data, position):
    if position + 4 > len(data):
        return None
    key_id = int.from_bytes(data[position:position + 4], "little")
    position += 4
    try:
        encrypted_key, position = _vector(data, position, maximum=128)
        salt, position = _vector(data, position, maximum=32)
        if position + 8 > len(data):
            return None
        method = int.from_bytes(data[position:position + 4], "little")
        iterations = int.from_bytes(data[position + 4:position + 8], "little")
        position += 8
        other, position = _vector(data, position, maximum=128)
    except ValueError:
        return None
    if position != len(data) or len(encrypted_key) != 48 or len(salt) != 8:
        return None
    if method != 0 or not 1_000 <= iterations <= 100_000_000 or other:
        return None
    return {"record_type": "mkey", "key_id": key_id, "derivation_method": method,
            "iterations": iterations, "scalar": None}


def parse_bitcoin_core_record(segment):
    try:
        tag, position = _core_tag(segment)
    except ValueError:
        return None
    if tag == "key":
        return _core_key_record(segment, position, encrypted=False)
    if tag == "ckey":
        return _core_key_record(segment, position, encrypted=True)
    if tag == "mkey":
        return _core_master_record(segment, position)
    return None


# ---------------------------------------------------------------------------
# Unified delta validator and driver
# ---------------------------------------------------------------------------

VALIDATORS = {
    "bip38": parse_bip38,
    "casascius_minikey": parse_minikey,
    "slip132": parse_slip132,
    "descriptor": parse_descriptor,
    "bitcoin_core_record": parse_bitcoin_core_record,
}


def validate_delta(segment):
    findings = []
    for name, validator in VALIDATORS.items():
        parsed = validator(segment)
        if parsed is not None:
            findings.append((name, parsed))
    return findings


def _scalars(parsed):
    if parsed.get("scalar") is not None:
        yield parsed["scalar"]
    yield from parsed.get("scalars", [])


def run(blobs=None, candidates=None, known_targets=None):
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets
    counters = Counter()
    per_format = defaultdict(Counter)
    structural_findings = []
    exact_target_hits = []
    candidate_texts = frozen_candidates() if candidates is None else candidates

    def inspect(segment, provenance, scopes, route):
        counters["validator_invocations"] += len(VALIDATORS)
        matches = validate_delta(segment)
        for format_name, parsed in matches:
            per_format[format_name][f"{route}_valid"] += 1
            record = {
                **provenance, "scopes": sorted(scopes), "route": route,
                "format": format_name, "segment_length": len(segment),
                "segment_sha256": hashlib.sha256(segment).hexdigest(),
                "detail": {key: value for key, value in parsed.items()
                           if key not in ("scalar", "scalars")},
            }
            hits = []
            for scalar in _scalars(parsed):
                hit = check_scalar(scalar, None, targets)
                if hit is not None:
                    hits.append(hit)
            if hits:
                for hit in hits:
                    exact_target_hits.append({**record, **hit})
            else:
                structural_findings.append(record)

    for index, model, label, candidate_sha256, form_kind, variant, blob, body in iter_retained_bodies(
            blobs=blobs, candidates=candidates):
        counters["bodies_checked"] += 1
        provenance = {
            "candidate_index": index, "candidate_model": model, "candidate_label": label,
            "candidate_sha256": candidate_sha256, "candidate_form": form_kind,
            "variant": variant, "blob": blob,
        }
        for segment, scopes in extract_scopes(body).items():
            counters["segments_checked"] += 1
            inspect(segment, provenance, scopes, "direct")
            for decoder_name, (trigger, decode) in DECODERS.items():
                if not trigger(segment):
                    continue
                counters[f"decoder_{decoder_name}_trigger"] += 1
                decoded = decode(segment)
                if decoded is None:
                    continue
                counters[f"decoder_{decoder_name}_ok"] += 1
                inspect(decoded, provenance, scopes, f"decoded:{decoder_name}")

    return {
        "candidate_count": len(candidate_texts),
        "candidate_digest": candidate_list_digest(candidate_texts),
        "format_registry": list(FORMAT_NAMES),
        "counters": dict(sorted(counters.items())),
        "per_format": {name: dict(sorted(per_format[name].items())) for name in FORMAT_NAMES},
        "structural_findings_count": len(structural_findings),
        "structural_findings": structural_findings,
        "exact_target_hits_count": len(exact_target_hits),
        "exact_target_hits": exact_target_hits,
    }


def assert_report_safe(report, candidate_texts=None):
    """Fail closed if a report ever gains literal candidates, WIFs, or bodies."""
    candidates = set(frozen_candidates() if candidate_texts is None else candidate_texts)
    wif_like = re.compile(
        r"(?<![1-9A-HJ-NP-Za-km-z])(?:5[1-9A-HJ-NP-Za-km-z]{50}|"
        r"[KL][1-9A-HJ-NP-Za-km-z]{51})(?![1-9A-HJ-NP-Za-km-z])"
    )
    forbidden_fields = {"body", "plaintext", "passphrase", "private_key", "wif"}

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in forbidden_fields:
                    raise AssertionError("report schema contains a secret-bearing field")
                yield str(key)
                yield from strings(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from strings(item)

    for value in strings(report):
        if value in candidates:
            raise AssertionError("report leaks a frozen candidate literal")
        if wif_like.search(value):
            raise AssertionError("report contains a WIF-shaped string")


# ---------------------------------------------------------------------------
# Self-test fixtures and controls
# ---------------------------------------------------------------------------

def _compact(value):
    if value < 253:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    return b"\xfe" + value.to_bytes(4, "little")


def _ser_vector(value):
    return _compact(len(value)) + value


def _core_key_fixture(scalar_value=777):
    private = ec.derive_private_key(scalar_value, ec.SECP256K1())
    pubkey = private.public_key().public_bytes(serialization.Encoding.X962,
                                               serialization.PublicFormat.CompressedPoint)
    der = private.private_bytes(serialization.Encoding.DER,
                                serialization.PrivateFormat.TraditionalOpenSSL,
                                serialization.NoEncryption())
    return _ser_vector(b"key") + _ser_vector(pubkey) + _ser_vector(der) + sha256d(pubkey + der)


def self_test():
    # BIP38 official test vector; checksum-corrupted and reserved-flag near negatives.
    bip38 = b"6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg"
    assert parse_bip38(bip38)["mode"] == "non_ec_multiply"
    assert parse_bip38(bip38[:-1] + b"h") is None
    bip_payload = _base58_payload(bip38)
    assert parse_bip38(base58check(bip_payload[:2] + b"\xd0" + bip_payload[3:]).encode()) is None

    # Casascius original 30-char vector and typo-check failure.
    minikey = b"S6c56bnXQiBjk9mqSYE7ykVQ7NzrRy"
    mini = parse_minikey(minikey)
    assert mini is not None and mini["length"] == 30
    assert parse_minikey(minikey[:-1] + b"z") is None

    # Official SLIP-132 ypub vector; checksum and invalid-chain-code controls.
    ypub = (b"ypub6Ww3ibxVfGzLrAH1PNcjyAWenMTbbAosGNB6VvmSEgytSER9azLDWCxoJwW7"
            b"Ke7icmizBMXrzBx9979FfaHxHcrArf3zbeJJJUZPf663zsP")
    assert parse_slip132(ypub)["label"] == "ypub"
    assert parse_slip132(ypub[:-1] + b"Q") is None
    ypayload = _base58_payload(ypub)
    assert parse_slip132(base58check(ypayload[:13] + b"\x00" * 32 + ypayload[45:]).encode()) is None
    for version, (label, key_kind, _) in SLIP132_VERSIONS.items():
        key_data = ypayload[45:] if key_kind == "public" else b"\x00" + (1).to_bytes(32, "big")
        variant = base58check(version + ypayload[4:45] + key_data).encode()
        assert parse_slip132(variant)["label"] == label

    # Bitcoin Core checksum implementation and bounded descriptor grammar.
    assert descriptor_checksum("raw(deadbeef)") == "89f8spxm"
    generator = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
    descriptor_payload = f"wpkh({generator})"
    descriptor = f"{descriptor_payload}#{descriptor_checksum(descriptor_payload)}".encode()
    parsed_descriptor = parse_descriptor(descriptor)
    assert parsed_descriptor is not None and parsed_descriptor["functions"] == ["wpkh"]
    assert parse_descriptor(descriptor[:-1] + b"q") is None
    unsupported_payload = f"unknown({generator})"
    unsupported = f"{unsupported_payload}#{descriptor_checksum(unsupported_payload)}".encode()
    assert parse_descriptor(unsupported) is None, "checksum-valid but unsupported grammar must reject"

    # Complete Core key/ckey/mkey records and truncated/checksum near negatives.
    core_key = _core_key_fixture()
    core_parsed = parse_bitcoin_core_record(core_key)
    assert core_parsed is not None and core_parsed["record_type"] == "key"
    assert parse_bitcoin_core_record(core_key[:-1]) is None
    private = ec.derive_private_key(888, ec.SECP256K1())
    pubkey = private.public_key().public_bytes(serialization.Encoding.X962,
                                               serialization.PublicFormat.CompressedPoint)
    encrypted = bytes(range(48))
    ckey = _ser_vector(b"ckey") + _ser_vector(pubkey) + _ser_vector(encrypted) + sha256d(encrypted)
    assert parse_bitcoin_core_record(ckey)["record_type"] == "ckey"
    assert parse_bitcoin_core_record(ckey[:-1] + bytes([ckey[-1] ^ 1])) is None
    mkey = (_ser_vector(b"mkey") + (1).to_bytes(4, "little") + _ser_vector(b"E" * 48)
            + _ser_vector(b"S" * 8) + (0).to_bytes(4, "little")
            + (25_000).to_bytes(4, "little") + _ser_vector(b""))
    assert parse_bitcoin_core_record(mkey)["record_type"] == "mkey"
    assert parse_bitcoin_core_record(mkey[:-1]) is None

    # End-to-end through the real AES corpus driver: direct text formats plus
    # Base64(Core key record), proving the inherited depth-one route too.
    import cb_common
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    scalar = (999_983).to_bytes(32, "big")
    wif = base58check(b"\x80" + scalar + b"\x01")
    secret_payload = f"wpkh({wif})"
    secret_descriptor = f"{secret_payload}#{descriptor_checksum(secret_payload)}".encode()
    synthetic_body = b"\n".join((bip38, minikey, ypub, secret_descriptor, base64.b64encode(core_key)))
    password, salt = b"seed8-delta-self-test", b"seed8slt"
    key, iv = cb_common.evp_bytes_to_key(password, salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    ciphertext = encryptor.update(synthetic_body) + encryptor.finalize()
    target = check_scalar(scalar, None, {})
    assert target is None
    from binary_key_material_backfill import private_key_details
    target_hash = bytes.fromhex(private_key_details(scalar)["compressed"]["hash160"])
    report = run(blobs={"SYNTH": (salt, ciphertext)}, candidates=[password.decode()],
                 known_targets={target_hash: "planted/compressed"})
    found_formats = {row["format"] for row in report["structural_findings"] + report["exact_target_hits"]}
    assert set(FORMAT_NAMES) <= found_formats
    assert any(row["format"] == "bitcoin_core_record" and row["route"] == "decoded:base64"
               for row in report["structural_findings"] + report["exact_target_hits"])
    assert any(row["format"] == "descriptor" and row.get("target_label") == "planted/compressed"
               for row in report["exact_target_hits"])
    wrong = run(blobs={"SYNTH": (salt, ciphertext)}, candidates=["definitely-not-the-password"],
                known_targets={target_hash: "planted/compressed"})
    assert wrong["structural_findings_count"] == 0 and wrong["exact_target_hits_count"] == 0

    # Random length-matched controls: exact checksums/grammars must suppress noise.
    import random
    rng = random.Random(20260820)
    for _ in range(300):
        random_body = bytes(rng.randrange(256)
                            for _ in range(rng.choice((22, 30, 58, 80, 111, 1328))))
        assert validate_delta(random_body) == []

    candidates = frozen_candidates()
    assert len(candidates) == 42 and candidate_list_digest(candidates) == EXPECTED_CANDIDATE_DIGEST
    assert sum(1 for _ in iter_retained_bodies()) == EXPECTED_BODY_COUNT
    assert_report_safe({"candidate_digest": EXPECTED_CANDIDATE_DIGEST, "findings": []}, candidates)
    try:
        assert_report_safe({"plaintext": "planted"}, candidates)
        raise AssertionError("report-safety control is vacuous")
    except AssertionError as exc:
        assert "schema" in str(exc)

    print("[*] self-test OK: BIP38, Casascius mini-key, all-version SLIP-132 structure, "
          "checksummed bounded descriptors, and complete Core key/ckey/mkey records have planted "
          "positives and near-negatives; real AES driver recovers all five including depth-one "
          "Base64(Core record) and an exact descriptor target; wrong-password and 300 random controls "
          f"clean; frozen digest {EXPECTED_CANDIDATE_DIGEST} and {EXPECTED_BODY_COUNT} bodies enforced")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else {"note": "pass --run to execute the frozen delta audit"}
    if args.run:
        if report["counters"].get("bodies_checked") != EXPECTED_BODY_COUNT:
            raise RuntimeError("frozen retained-body count drift")
        if report["counters"].get("segments_checked") != EXPECTED_SEGMENT_COUNT:
            raise RuntimeError("frozen segment count drift")
        assert_report_safe(report)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.json:
        print(rendered)
    else:
        for key, value in report.items():
            if key not in ("structural_findings", "exact_target_hits"):
                print(f"{key}: {value}")


if __name__ == "__main__":
    main()
