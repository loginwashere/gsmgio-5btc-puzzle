#!/usr/bin/env python3
"""Raw-private-key chunk audit over Phase 378/379's byte-pathway materials.

Preregistered 2026-08-23 during Phase 378/379 review as the best bounded
next step: tests whether the right password could have produced binary
private-key material that this project's ordinary printable-text/
structural-binary oracle gate discards. Ordinary key bytes do not look
like readable text, and most of Phase 378/379's target-blob bodies won't
match `cb_common.is_structural_binary_plaintext`'s narrow (aes, block==16,
pad==16, len==64) two-key shape either, so a correct binary-key decrypt
could currently be silently thrown away by both gates.

Frozen method (declared before running, per this project's Lane B/stop-
rule discipline -- not revised after seeing results):

  - Corpus: the identical Phase 378/379 756-material byte-pathway set. No
    new candidate text or material form is introduced here.
  - Configurations: the 72 non-Key-Wrap configurations already run in
    Phase 378/379 -- 24 CBC (KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS), 12
    ECB, 36 stream (CFB/OFB/CTR). Key Wrap is excluded: a real unwrap
    already returns raw key bytes directly (Phase 379's regression covers
    its result handling), so there is no printable-text gate for Key Wrap
    to fail past in the first place.
  - Retention rule: CBC/ECB retain a body only if it decrypts with a
    valid PKCS7 pad (the one structural check that is not printable-text
    scoring); stream retains every decrypted body unconditionally, since
    CFB/OFB/CTR have no validity check at all. `printable_z_score` is
    deliberately NOT applied as a filter here -- routing around exactly
    that gate is the point of this audit.
  - Inspection: exactly the first two 32-byte chunks of each retained
    body (bytes 0:32, and 32:64 if the body is >=64 bytes long) --
    mirroring doc/GSMG_GPU_ORACLE.md's established "unconditional raw-key
    Bloom check of the first two 32-byte chunks" convention. No sliding
    window, no other offsets.
  - Validity: a chunk counts as a candidate private key only if its
    big-endian integer value is in [1, SECP256K1_ORDER) -- reusing
    `binary_key_material_backfill.private_key_details`, this project's one
    scalar->address implementation.
  - Acceptance: a hit requires an EXACT hash160 match (compressed or
    uncompressed) against the frozen 10-address known-target set --
    PRIZE_ADDRESS and HALVING_ADDRESS (`first_hint_hash_audit.py`) plus
    the 8 EC-derived neighbor hash160s (P+G/P-G/P/2/2P x compressed/
    uncompressed; ported from `tools/gpu_oracle/src/checker/
    known_targets.rs`, itself independently re-derived Phase 331/332 from
    the prize pubkey's 6 real on-chain spends). No funded-balance gate, no
    Bloom filter, no live API call -- this is a small frozen exact-match
    set, not a probabilistic filter.
  - Weak structural observations (a chunk that is a valid scalar but
    matches no known target) are counted, never promoted as hits.
  - Stop rule: this corpus and this target set only. No candidate-
    encoding or target-set expansion regardless of outcome.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cryptography.hazmat.primitives.ciphers import Cipher, modes  # noqa: E402

from binary_key_material_backfill import private_key_details  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    CIPHER_BLOCK_SIZES,
    CIPHER_CLASSES,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    STREAM_MODE_CLASSES,
    _normalize_variant,
    evp_bytes_to_key,
    pbkdf2_bytes_to_key,
)
from extended_cipher_recheck import candidate_list_digest  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS, SECP256K1_ORDER  # noqa: E402
from input_byte_pathway_reconstruction_audit import new_material_forms  # noqa: E402
from key_shape_classifier import base58check_decode  # noqa: E402
from p1a_sentinel_backfill import eligible_candidates  # noqa: E402

CBC_KDF_VARIANTS = KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS  # 24, matches Phase 379

# The 8 EC-derived neighbor hash160s (P+G, P-G, P/2, 2P; compressed and
# uncompressed each), ported byte-for-byte from tools/gpu_oracle/src/
# checker/known_targets.rs (see that file's module doc comment for the
# independent re-derivation off the prize pubkey's 6 real on-chain spends
# -- not copied from any community write-up).
EC_NEIGHBOR_HASH160S = {
    "9eb2e43005af77783e41ea702cf3ec3585fcd73d": "P+G / k+1 / compressed",
    "f8fca692ffc90cba0c330dc56e02fa8da8d2d6e6": "P+G / k+1 / uncompressed",
    "9570962eadf45c422a2e59ddb9a1d87040ca5907": "P-G / k-1 / compressed",
    "a4ae210a25bb8e2c359a134fafc2e30c6709dbc0": "P-G / k-1 / uncompressed",
    "5043bb64b25d3fe6a7a6949ff98f98b26dcd2fa7": "P/2 / half / compressed",
    "3de34fca1bd6b7607243b0316a8102b7598cc9dc": "P/2 / half / uncompressed",
    "286301cde59820851fe92a3a9be4f76f6c3ebff8": "2P / double / compressed",
    "c889dfbf698413209b6131895250b869f68560e0": "2P / double / uncompressed",
}


def _address_hash160(address):
    payload = base58check_decode(address)
    assert payload is not None and len(payload) == 21 and payload[0] == 0x00, address
    return payload[1:].hex()


def known_targets():
    """The frozen 10-address target set: {hash160_hex: label}."""
    targets = dict(EC_NEIGHBOR_HASH160S)
    targets[_address_hash160(PRIZE_ADDRESS)] = "PRIZE_ADDRESS"
    targets[_address_hash160(HALVING_ADDRESS)] = "HALVING_ADDRESS"
    return targets


KNOWN_TARGETS = known_targets()
EXPECTED_TARGET_COUNT = 10

ORACLE_FAMILIES = (
    ("cbc", CBC_KDF_VARIANTS),
    ("ecb", ECB_CIPHER_VARIANTS),
    ("stream", STREAM_CIPHER_VARIANTS),
)
EXPECTED_TOTAL_CONFIGS = 72  # 24 + 12 + 36, matches Phase 378/379's non-keywrap scope


def _derive(cache, kdf_kind, kdf_param, salt, material, needed_len):
    """Cached EVP_BytesToKey/PBKDF2 derivation, keyed by (kdf_kind,
    kdf_param, salt). `cache` must be fresh per `material` -- derivation
    output depends on material too, and this key deliberately omits it.
    Mirrors cb_common.aes_try_open_bytes's derived_cache/max_derived_
    lengths pattern: PBKDF2/EVP_BytesToKey both produce one prefix-stable
    byte stream, so the group sharing (kdf_kind, kdf_param, salt) is
    derived once at its max needed length and sliced per variant -- this
    is the difference between ~4 PBKDF2(10000) calls and dozens per
    material, and is why the naive per-variant version of this script
    was multiple hours slower."""
    key = (kdf_kind, kdf_param, salt)
    cached_len, cached_bytes = cache.get(key, (0, b""))
    if cached_len >= needed_len:
        return cached_bytes
    if kdf_kind == "legacy":
        derived, _ = evp_bytes_to_key(material, salt, kdf_param, needed_len, 0)
    else:
        digest_name, iterations = kdf_param
        derived, _ = pbkdf2_bytes_to_key(material, salt, iterations, digest_name, needed_len, 0)
    cache[key] = (needed_len, derived)
    return derived


def _max_needed_lengths(variants, len_fn):
    """Group `variants` by (kdf_kind, kdf_param) and compute the max
    needed_len for each group, per len_fn(variant) -> int."""
    out = {}
    for v in variants:
        kdf_kind, kdf_param = v[0], v[1]
        out[(kdf_kind, kdf_param)] = max(out.get((kdf_kind, kdf_param), 0), len_fn(v))
    return out


_CBC_NORMALIZED = [_normalize_variant(v) for v in CBC_KDF_VARIANTS]
_CBC_MAX_LENGTHS = _max_needed_lengths(
    _CBC_NORMALIZED, lambda v: v[3] + CIPHER_BLOCK_SIZES[v[2]],
)
_ECB_MAX_LENGTHS = _max_needed_lengths(ECB_CIPHER_VARIANTS, lambda v: v[2])
# Stream variants need key_len + 16 (block/IV size, AES-only): evp_bytes_to_key
# ordinarily returns (key, iv) as two direct slices when called with
# iv_len=16, but here we call it with iv_len=0 and needed_len=key_len+16 so
# _derive's single cached call can serve every variant sharing this
# (kdf_kind, kdf_param) group -- both produce byte-identical output since
# it's the same underlying digest-chain/PBKDF2 stream either way.
_STREAM_MAX_LENGTHS = _max_needed_lengths(STREAM_CIPHER_VARIANTS, lambda v: v[2] + 16)


def _cbc_bodies(material, salt, ct, cache):
    for kdf_kind, kdf_param, cipher, key_len in _CBC_NORMALIZED:
        block = CIPHER_BLOCK_SIZES[cipher]
        if len(ct) % block != 0 or not ct:
            continue
        needed = _CBC_MAX_LENGTHS[(kdf_kind, kdf_param)]
        keyiv = _derive(cache, kdf_kind, kdf_param, salt, material, needed)
        key, iv = keyiv[:key_len], keyiv[key_len:key_len + block]
        decryptor = Cipher(CIPHER_CLASSES[cipher](key), modes.CBC(iv)).decryptor()
        try:
            pt = decryptor.update(ct) + decryptor.finalize()
        except Exception:
            continue
        pad = pt[-1]
        if 1 <= pad <= block and pt[-pad:] == bytes([pad]) * pad:
            body = pt[:-pad]
            if body:
                yield body


def _ecb_bodies(material, salt, ct, cache):
    for kdf_kind, kdf_param, key_len in ECB_CIPHER_VARIANTS:
        if not ct or len(ct) % 16:
            continue
        needed = _ECB_MAX_LENGTHS[(kdf_kind, kdf_param)]
        key = _derive(cache, kdf_kind, kdf_param, salt, material, needed)[:key_len]
        decryptor = Cipher(CIPHER_CLASSES["aes"](key), modes.ECB()).decryptor()
        try:
            pt = decryptor.update(ct) + decryptor.finalize()
        except Exception:
            continue
        pad = pt[-1]
        if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
            body = pt[:-pad]
            if body:
                yield body


def _stream_bodies(material, salt, ct, cache):
    block = 16
    for kdf_kind, kdf_param, key_len, stream_mode in STREAM_CIPHER_VARIANTS:
        if not ct:
            continue
        needed = _STREAM_MAX_LENGTHS[(kdf_kind, kdf_param)]
        keyiv = _derive(cache, kdf_kind, kdf_param, salt, material, needed)
        key, iv = keyiv[:key_len], keyiv[key_len:key_len + block]
        decryptor = Cipher(CIPHER_CLASSES["aes"](key), STREAM_MODE_CLASSES[stream_mode](iv)).decryptor()
        try:
            body = decryptor.update(ct) + decryptor.finalize()
        except Exception:
            continue
        if body:
            yield body


BODY_SOURCES = {"cbc": _cbc_bodies, "ecb": _ecb_bodies, "stream": _stream_bodies}


def chunk_check(body):
    """Exactly the first two 32-byte chunks; returns (valid_scalars, hits)."""
    chunks = [body[:32]]
    if len(body) >= 64:
        chunks.append(body[32:64])
    valid_scalars = 0
    hits = []
    for chunk in chunks:
        value = int.from_bytes(chunk, "big")
        if not (1 <= value < SECP256K1_ORDER):
            continue
        valid_scalars += 1
        details = private_key_details(chunk)
        for address_type, info in details.items():
            label = KNOWN_TARGETS.get(info["hash160"])
            if label is not None:
                hits.append({
                    "address_type": address_type,
                    "target": label,
                    "hash160": info["hash160"],
                    "address": info["address"],
                    "private_key_hex": chunk.hex(),
                })
    return valid_scalars, hits


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]

    bodies_inspected = 0
    valid_scalar_count = 0
    hits = []
    for model, label, text in candidates:
        for form_kind, material in new_material_forms(text):
            cache = {}  # fresh per material: derivation depends on material, not just (kdf, salt)
            for tag, (salt, ct) in active_blobs.items():
                for family_name, _ in ORACLE_FAMILIES:
                    for body in BODY_SOURCES[family_name](material, salt, ct, cache):
                        bodies_inspected += 1
                        valid_scalars, chunk_hits = chunk_check(body)
                        valid_scalar_count += valid_scalars
                        for hit in chunk_hits:
                            hits.append({
                                "model": model,
                                "label": label,
                                "form": form_kind,
                                "family": family_name,
                                "blob": tag,
                                **hit,
                            })

    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(texts),
        "materials": sum(len(new_material_forms(t)) for t in texts),
        "blobs": tuple(active_blobs),
        "oracle_families": [name for name, _ in ORACLE_FAMILIES],
        "total_variant_configs": sum(len(v) for _, v in ORACLE_FAMILIES),
        "known_target_count": len(KNOWN_TARGETS),
        "bodies_inspected": bodies_inspected,
        "valid_scalar_chunks": valid_scalar_count,
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]
    assert len(candidates) == 42
    assert candidate_list_digest(texts) == "51afdf5ce033500a"

    assert len(KNOWN_TARGETS) == EXPECTED_TARGET_COUNT, len(KNOWN_TARGETS)
    total_configs = sum(len(v) for _, v in ORACLE_FAMILIES)
    assert total_configs == EXPECTED_TOTAL_CONFIGS, total_configs

    # Prize address hash160, derived here via base58 decode, must equal the
    # independently pinned constant in tools/gpu_oracle/src/checker/
    # known_targets.rs's PRIZE_HASH160 -- two separate implementations
    # (Python base58 decode vs. Rust's pinned constant, itself re-derived
    # from the prize pubkey's on-chain scriptSig) agreeing catches a
    # broken _address_hash160 here.
    prize_hash160 = _address_hash160(PRIZE_ADDRESS)
    assert len(prize_hash160) == 40, prize_hash160
    assert prize_hash160 == "a9553269572a317e39f0f518cb87c1a0ee1dbae4", prize_hash160

    # chunk_check must recognize a synthetic known-target private key: any
    # scalar whose derived hash160 is in KNOWN_TARGETS. We don't have a
    # known target's actual private key (that's the whole open question),
    # so instead check the *negative* path on a scalar with no relation to
    # any target, plus the *positive* path via a monkeypatched target set
    # containing a key we do know.
    test_key = (1234567890).to_bytes(32, "big")
    test_details = private_key_details(test_key)
    test_hash160 = test_details["compressed"]["hash160"]
    original_targets = dict(KNOWN_TARGETS)
    KNOWN_TARGETS[test_hash160] = "SYNTH_TEST_TARGET"
    try:
        body = test_key + b"\x00" * 32  # 64 bytes: chunk 1 is the test key
        valid_scalars, hits = chunk_check(body)
        assert valid_scalars == 1, valid_scalars  # second chunk (all zero) is not a valid scalar
        assert len(hits) == 1, hits
        assert hits[0]["target"] == "SYNTH_TEST_TARGET"
        assert hits[0]["hash160"] == test_hash160
    finally:
        KNOWN_TARGETS.clear()
        KNOWN_TARGETS.update(original_targets)
    assert len(KNOWN_TARGETS) == EXPECTED_TARGET_COUNT

    # A chunk of all zero bytes is not a valid scalar (0 is excluded).
    valid_scalars, hits = chunk_check(b"\x00" * 64)
    assert valid_scalars == 0 and hits == []

    print(
        f"[*] self-test OK: {EXPECTED_TARGET_COUNT} known targets, "
        f"{EXPECTED_TOTAL_CONFIGS} configs (24 CBC + 12 ECB + 36 stream), "
        f"chunk_check positive/negative paths verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else {"note": "pass --run to execute"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
