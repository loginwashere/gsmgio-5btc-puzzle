#!/usr/bin/env python3
"""B1 from doc/Brainstorms/2026-08-20 - Creative Brute-Force Coverage
Expansion.md: "take half and better half literally."

Pre-registration (frozen before any real run, per that document's own
"Decisions"/"Experiments and next actions" requirement):

  - Frozen inputs: the 42 P0A-eligible sentinel candidates (models 9, 11,
    15, 16 -- see p1a_sentinel_backfill.py, digest 51afdf5ce033500a), in
    exactly two forms (literal, hex SHA-256 of literal) -- the same
    material-treatment contract p1a_sentinel_backfill.py already uses. This
    is a deliberately small, already-established, no-unauthored-choice
    corpus, NOT the full 14,551-keystring core corpus -- see "Scope note"
    below for why.
  - Frozen crypto scope: cb_common.KDF_VARIANTS (6 CBC variants) +
    cb_common.ECB_CIPHER_VARIANTS (12 ECB variants) +
    cb_common.STREAM_CIPHER_VARIANTS (36 CFB/OFB/CTR variants) x all 4
    tracked blobs (SALPH/COSMIC/P32TRAILING/URLBLOB) = 54 variants x 4
    blobs = 216 (variant, blob) pairs per passphrase form.
  - Frozen combine family: exactly the 15 named operations in
    `combine_pairs()` below, taken verbatim from the brainstorm's B1 list
    (XOR; A+B/A-B/B-A mod n; two interleave directions; two halves-swap
    directions; two nibble-interleave directions; three SHA256 combos; two
    HMAC directions). No operation is added or dropped after seeing data.
  - Frozen success criterion: a resulting 32-byte value is a valid
    secp256k1 scalar (1 <= x < n) AND its compressed or uncompressed
    hash160 matches either the real production Bloom cache (mandatorily
    confirmed live, same as every other Bloom hit in this project) or one
    of Phase 331's 8 known EC-derived target hash160s (exact match, no
    balance check needed -- see checker::known_targets's Rust original;
    mirrored here in Python since this script is CPU-only).
  - Stop rule: run exactly once over the frozen scope above; no adaptive
    follow-up, no threshold tuning after seeing results.

Scope note: this is deliberately a bounded pilot, not the full
14,551-keystring core corpus (Phase 327's exact expanded corpus -- 648
base candidates x answer_forms()/keystr_forms() -- a different, larger
corpus than this script's own 42-candidate x 2-form sentinel set) x 216
(variant, blob) pairs x 15-combine sweep. That upper bound is 14,551 x 216
x 15 = 47,145,240 combine checks if every attempt produced a checkable
body (each needing one EC derivation, not two -- private_key_details()
derives the point once and re-encodes it as both compressed and
uncompressed addresses). In practice only the 144 always-retained stream
(variant, blob) pairs (36 stream variants x 4 blobs) reliably produce a
body; CBC/ECB only add one on the rare valid-pad case, so the realistic
baseline is closer to 14,551 x 144 x 15 = 31,430,160 checks -- tens of
minutes of pure-Python EC work at this project's earlier ~1,900-2,000
derivations/sec benchmark, not the "150M+, many hours" this note
originally (incorrectly) estimated. Still real enough cost that the
brainstorm's own "Open questions" section anticipates a GPU kernel for
comfortable full-corpus scale.
This pilot validates the detector end-to-end (self-test) and runs it over
the smaller, already-vetted corpus first, per this project's habitual
cheap-bounded-pilot-before-expensive-full-sweep discipline.
"""

import argparse
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa: E402

import cb_common  # noqa: E402
from cb_common import BLOBS, KDF_VARIANTS, STREAM_CIPHER_VARIANTS  # noqa: E402
from binary_key_material_backfill import (  # noqa: E402
    BloomCache,
    hash160,
    private_key_details,
)
from extended_cipher_recheck import candidate_list_digest  # noqa: E402
from first_hint_hash_audit import SECP256K1_ORDER  # noqa: E402
import p1a_sentinel_backfill  # noqa: E402

# Mirrors tools/gpu_oracle/src/checker/known_targets.rs exactly -- see that
# file's module doc comment for full provenance (independently re-derived
# from the six on-chain transactions spending the prize address, not copied
# from any write-up). Kept as a second, independent transcription rather
# than importing the Rust source; `self_test()` below cross-checks all 8
# against fresh Python secp256k1 math computed from the same pinned pubkey.
PRIZE_PUBKEY_HEX = (
    "04f4d1bbd91e65e2a019566a17574e97dae908b784b388891848007e4f55d5a4649c73"
    "d25fc5ed8fd7227cab0be4e576c0c6404db5aa546286563e4be12bf33559"
)
PRIZE_HASH160_HEX = "a9553269572a317e39f0f518cb87c1a0ee1dbae4"

KNOWN_TARGET_HASH160S = {
    # The prize address itself -- P0-P1's review caught that this was
    # defined (PRIZE_HASH160_HEX) but never actually added to the target
    # set, so a decrypt landing on the literal prize key k (not just its
    # EC-derived neighbors) would only ever have been caught via the Bloom
    # cache, silently missed entirely if that cache was absent/stale.
    bytes.fromhex(PRIZE_HASH160_HEX): "prize_address",
    bytes.fromhex("9eb2e43005af77783e41ea702cf3ec3585fcd73d"): "P+G/compressed",
    bytes.fromhex("f8fca692ffc90cba0c330dc56e02fa8da8d2d6e6"): "P+G/uncompressed",
    bytes.fromhex("9570962eadf45c422a2e59ddb9a1d87040ca5907"): "P-G/compressed",
    bytes.fromhex("a4ae210a25bb8e2c359a134fafc2e30c6709dbc0"): "P-G/uncompressed",
    bytes.fromhex("5043bb64b25d3fe6a7a6949ff98f98b26dcd2fa7"): "P/2/compressed",
    bytes.fromhex("3de34fca1bd6b7607243b0316a8102b7598cc9dc"): "P/2/uncompressed",
    bytes.fromhex("286301cde59820851fe92a3a9be4f76f6c3ebff8"): "2P/compressed",
    bytes.fromhex("c889dfbf698413209b6131895250b869f68560e0"): "2P/uncompressed",
}
assert all(len(h) == 20 for h in KNOWN_TARGET_HASH160S), "every pinned hash160 must be 20 bytes"


EXPECTED_CANDIDATE_COUNT = 42
EXPECTED_CANDIDATE_DIGEST = "51afdf5ce033500a"  # p1a_sentinel_backfill.py's own pinned digest
EXPECTED_FORM_COUNT = 2


def frozen_candidates():
    """The exact 42 P0A-eligible sentinel strings, reused from
    p1a_sentinel_backfill.py rather than re-selected here -- see this
    script's own module docstring for why this corpus, not a fresh one."""
    return [text for (_model, _label, text) in p1a_sentinel_backfill.eligible_candidates()]


def frozen_candidates_with_provenance():
    """Same 42 strings as frozen_candidates(), but keeping the (model,
    label) p1a_sentinel_backfill.eligible_candidates() already attaches to
    each one, plus a stable 0-based index -- so a hit record can name which
    hypothesis produced it instead of only the raw candidate text."""
    return [
        (index, model, label, text)
        for index, (model, label, text) in enumerate(p1a_sentinel_backfill.eligible_candidates())
    ]


def passphrase_forms(text):
    return (text, hashlib.sha256(text.encode()).hexdigest())


def combine_pairs(a: bytes, b: bytes) -> dict:
    """The exact 15 named operations from the brainstorm's B1 list. `a` and
    `b` are always 32 bytes each (the "half"/"better_half" chunks)."""
    assert len(a) == len(b) == 32
    n = SECP256K1_ORDER
    ai, bi = int.from_bytes(a, "big"), int.from_bytes(b, "big")

    def be32(value):
        return (value % n).to_bytes(32, "big")

    interleave_even_a = bytes(a[i] if i % 2 == 0 else b[i] for i in range(32))
    interleave_even_b = bytes(b[i] if i % 2 == 0 else a[i] for i in range(32))
    nibble_hi_a_lo_b = bytes((a[i] & 0xF0) | (b[i] & 0x0F) for i in range(32))
    nibble_hi_b_lo_a = bytes((b[i] & 0xF0) | (a[i] & 0x0F) for i in range(32))

    return {
        "xor": bytes(x ^ y for x, y in zip(a, b)),
        "add_mod_n": be32(ai + bi),
        "sub_mod_n_a_minus_b": be32(ai - bi),
        "sub_mod_n_b_minus_a": be32(bi - ai),
        "interleave_even_a_odd_b": interleave_even_a,
        "interleave_even_b_odd_a": interleave_even_b,
        "halves_a_lo_b_hi": a[:16] + b[16:],
        "halves_b_lo_a_hi": b[:16] + a[16:],
        "nibble_hi_a_lo_b": nibble_hi_a_lo_b,
        "nibble_hi_b_lo_a": nibble_hi_b_lo_a,
        "sha256_a_then_b": hashlib.sha256(a + b).digest(),
        "sha256_b_then_a": hashlib.sha256(b + a).digest(),
        "sha256_xor": hashlib.sha256(bytes(x ^ y for x, y in zip(a, b))).digest(),
        "hmac_key_a_msg_b": hmac.new(a, b, hashlib.sha256).digest(),
        "hmac_key_b_msg_a": hmac.new(b, a, hashlib.sha256).digest(),
    }


def _derive_key_iv(kdf_kind, kdf_param, salt, passwd, key_len, iv_len):
    """Handles both KDF_VARIANTS'/ECB_CIPHER_VARIANTS'/STREAM_CIPHER_VARIANTS'
    2-element legacy `kdf_param` (a bare digest name) and pbkdf2's
    `(digest_name, iterations)` form -- see cb_common._normalize_variant,
    not reused directly here because this script needs the raw key/IV
    split, not a decrypt-and-classify call."""
    if kdf_kind == "legacy":
        return cb_common.evp_bytes_to_key(passwd, salt, kdf_param, key_len, iv_len)
    digest_name, iterations = kdf_param
    return cb_common.pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, iv_len)


def _variant_label(kdf_kind, kdf_param, key_len, mode_name):
    kdf_name = kdf_param if kdf_kind == "legacy" else f"pbkdf2-{kdf_param[0]}-{kdf_param[1]}"
    return f"{kdf_kind}-{kdf_name}/aes-{key_len * 8}-{mode_name}"


def raw_cbc_bodies(passwd: bytes, blobs):
    """Every (variant_label, tag, body) where PKCS7 padding validates --
    unlike cb_common.aes_try_open_bytes, this never applies a printability
    gate; a padding-valid body is retained regardless of shape, which is
    the entire point of this detector (see the brainstorm's Idea A / this
    project's false-negative-surface doc). CBC variants only (KDF_VARIANTS,
    6 legacy-KDF entries) -- ECB is handled separately in raw_ecb_bodies."""
    out = []
    for digest_name, key_len in KDF_VARIANTS:
        for tag, (salt, ct) in blobs.items():
            if not ct or len(ct) % 16 != 0:
                continue
            key, iv = cb_common.evp_bytes_to_key(passwd, salt, digest_name, key_len, 16)
            decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
            try:
                pt = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            pad = pt[-1]
            if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
                body = pt[:-pad]
                if len(body) >= 64:
                    out.append((_variant_label("legacy", digest_name, key_len, "cbc"), tag, body))
    return out


def raw_ecb_bodies(passwd: bytes, blobs):
    """Same padding-valid-only retention as raw_cbc_bodies, for AES-ECB
    (cb_common.ECB_CIPHER_VARIANTS, 12 variants: legacy x3 digests + pbkdf2,
    x3 key sizes each). ECB has no IV."""
    out = []
    for kdf_kind, kdf_param, key_len in cb_common.ECB_CIPHER_VARIANTS:
        for tag, (salt, ct) in blobs.items():
            if not ct or len(ct) % 16 != 0:
                continue
            key, _iv = _derive_key_iv(kdf_kind, kdf_param, salt, passwd, key_len, 0)
            decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
            try:
                pt = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            pad = pt[-1]
            if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
                body = pt[:-pad]
                if len(body) >= 64:
                    out.append((_variant_label(kdf_kind, kdf_param, key_len, "ecb"), tag, body))
    return out


def raw_stream_bodies(passwd: bytes, blobs):
    """Every (variant_label, tag, body) for CFB/OFB/CTR (cb_common.
    STREAM_CIPHER_VARIANTS, 36 variants: legacy x3 digests + pbkdf2, x3 key
    sizes, x3 modes) -- no padding to validate, so every decrypt of length
    >= 64 is retained unconditionally."""
    out = []
    for kdf_kind, kdf_param, key_len, stream_mode in STREAM_CIPHER_VARIANTS:
        mode_class = cb_common.STREAM_MODE_CLASSES[stream_mode]
        for tag, (salt, ct) in blobs.items():
            if not ct:
                continue
            key, iv = _derive_key_iv(kdf_kind, kdf_param, salt, passwd, key_len, 16)
            decryptor = Cipher(algorithms.AES(key), mode_class(iv)).decryptor()
            try:
                body = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            if len(body) >= 64:
                out.append((_variant_label(kdf_kind, kdf_param, key_len, stream_mode), tag, body))
    return out


def check_scalar(value_bytes: bytes, bloom, known_targets):
    """Returns a hit record if value_bytes is a valid scalar whose derived
    address matches either the frozen known-target set (exact, unconditional)
    or the Bloom cache (pre-filter only -- caller must still mandatorily
    confirm any Bloom hit live before treating it as real, same house rule
    as every other Bloom check in this project)."""
    value = int.from_bytes(value_bytes, "big")
    if not 1 <= value < SECP256K1_ORDER:
        return None
    addrs = private_key_details(value_bytes)
    if addrs is None:
        return None
    for address_type, info in addrs.items():
        h = bytes.fromhex(info["hash160"])
        if h in known_targets:
            return {"kind": "known_target", "address_type": address_type, **info,
                    "target_label": known_targets[h]}
        if bloom is not None and bloom.contains(h):
            return {"kind": "bloom_prefilter", "address_type": address_type, **info}
    return None


BLOCKSTREAM_API_BASE = "https://blockstream.info/api/address"
API_RATE_LIMIT_SECONDS = 0.35  # matches key-seeker/ApiChecker's own interval


def confirm_address_live(address, api_base=BLOCKSTREAM_API_BASE, timeout=10):
    """Mandatory live confirmation for a Bloom pre-filter hit -- the same
    funded>spent rule and Blockstream endpoint binary_key_material_backfill.
    py's verify_pending_queue() already uses, called synchronously here
    instead of queued, since a bounded pilot expects at most a handful of
    Bloom hits. Any network error or false-positive returns False; a Bloom
    hit is never promoted to a real result just because this call failed
    open -- see run()'s caller, which only counts a bloom_prefilter kind as
    a hit after this returns True."""
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/{address}",
        headers={"User-Agent": "gsmg-half-better-half-audit/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        print(f"[!] live confirmation failed for {address}: {exc}")
        return False
    chain = payload.get("chain_stats", {})
    mempool = payload.get("mempool_stats", {})
    funded = int(chain.get("funded_txo_sum", 0)) + int(mempool.get("funded_txo_sum", 0))
    spent = int(chain.get("spent_txo_sum", 0)) + int(mempool.get("spent_txo_sum", 0))
    return funded > spent


def run(blobs=None, bloom_path=None, candidates=None, known_targets=None, confirm_fn=None):
    active_blobs = BLOBS if blobs is None else blobs
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets
    confirm = confirm_address_live if confirm_fn is None else confirm_fn

    if candidates is None:
        cand_records = frozen_candidates_with_provenance()
    else:
        # A caller-supplied plain-string list (every self-test in this
        # module and its two sibling scripts) has no P0A model/label --
        # still index/hash them so hit records stay uniformly shaped.
        cand_records = [(i, "external", f"candidate_{i}", text) for i, text in enumerate(candidates)]
    candidate_texts = [text for (_i, _model, _label, text) in cand_records]

    if bloom_path is not None:
        if not Path(bloom_path).exists():
            # Fail closed, not silently continue with bloom=None: a
            # requested-but-missing Bloom cache would otherwise leave
            # everything except the handful of pinned known targets
            # unchecked, and a resulting "0 hits" would look identical to
            # a real negative. Pass bloom_path=None explicitly (not a path
            # that might not exist) to intentionally run without Bloom
            # coverage.
            raise FileNotFoundError(
                f"Bloom cache requested at {bloom_path!r} but the file does not exist -- "
                "pass bloom_path=None to run without Bloom coverage intentionally, or fix "
                "the path. Silently continuing without it was a real correctness bug here."
            )
        bloom = BloomCache(bloom_path)
    else:
        bloom = None

    attempts = 0
    bodies_checked = 0
    combine_checks = 0
    hits = []
    try:
        for index, model, label, text in cand_records:
            candidate_sha256 = hashlib.sha256(text.encode()).hexdigest()
            for form_kind, form_text in zip(("literal", "sha256"), passphrase_forms(text)):
                passwd = form_text.encode()
                bodies = (raw_cbc_bodies(passwd, active_blobs)
                          + raw_ecb_bodies(passwd, active_blobs)
                          + raw_stream_bodies(passwd, active_blobs))
                attempts += 1
                for variant_label, tag, body in bodies:
                    bodies_checked += 1
                    a, b = body[:32], body[32:64]
                    for op_name, result in combine_pairs(a, b).items():
                        combine_checks += 1
                        hit = check_scalar(result, bloom, targets)
                        if hit is None:
                            continue
                        if hit["kind"] == "bloom_prefilter":
                            # Mandatory live confirmation before counting --
                            # a bare Bloom containment test has a nonzero
                            # false-positive rate by construction.
                            time.sleep(API_RATE_LIMIT_SECONDS)
                            if not confirm(hit["address"]):
                                continue
                            hit = {**hit, "kind": "bloom_confirmed"}
                        hits.append({
                            "candidate_index": index,
                            "candidate_model": model,
                            "candidate_label": label,
                            "candidate_sha256": candidate_sha256,
                            "candidate_form": form_kind,
                            "variant": variant_label,
                            "blob": tag,
                            "operation": op_name,
                            **hit,
                        })
    finally:
        if bloom is not None:
            bloom.close()

    return {
        "candidate_count": len(cand_records),
        "candidate_digest": candidate_list_digest(candidate_texts),
        "passphrase_attempts": attempts,
        "bodies_checked": bodies_checked,
        "combine_checks": combine_checks,
        "bloom_active": bloom is not None,
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    # 1. Combine-family sanity: XOR is self-inverse, halves-swap round-trips.
    a = bytes(range(32))
    b = bytes((x * 7 + 3) % 256 for x in range(32))
    forms = combine_pairs(a, b)
    # xor(1) + add/sub-a-b/sub-b-a(3) + interleave x2(2) + halves x2(2) +
    # nibble x2(2) + sha256 x3(3) + hmac x2(2) = 15, exactly B1's list.
    assert len(forms) == 15, f"expected 15 named combine forms, got {len(forms)}"
    assert all(len(v) == 32 for v in forms.values())
    assert bytes(x ^ y for x, y in zip(forms["xor"], b)) == a, "xor must be self-inverse"
    assert forms["halves_a_lo_b_hi"][:16] == a[:16] and forms["halves_a_lo_b_hi"][16:] == b[16:]
    n = SECP256K1_ORDER
    ai, bi = int.from_bytes(a, "big"), int.from_bytes(b, "big")
    assert int.from_bytes(forms["add_mod_n"], "big") == (ai + bi) % n

    # 2. Known-target constants cross-checked independently in Python
    #    (secp256k1 point add/negate/halve/double against the pinned pubkey)
    #    -- same cross-check tests::rederive_from_pubkey does in Rust,
    #    done again here with a completely separate implementation path.
    from cryptography.hazmat.primitives.asymmetric import ec

    curve = ec.SECP256K1()
    pub_bytes = bytes.fromhex(PRIZE_PUBKEY_HEX)
    pub = ec.EllipticCurvePublicKey.from_encoded_point(curve, pub_bytes)
    assert hash160(pub_bytes).hex() == PRIZE_HASH160_HEX == "a9553269572a317e39f0f518cb87c1a0ee1dbae4"

    p = pub.public_numbers().x, pub.public_numbers().y
    field_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

    def point_add(p1, p2):
        if p1 is None:
            return p2
        if p2 is None:
            return p1
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2 and (y1 + y2) % field_p == 0:
            return None
        if p1 == p2:
            lam = (3 * x1 * x1) * pow(2 * y1, -1, field_p) % field_p
        else:
            lam = (y2 - y1) * pow((x2 - x1) % field_p, -1, field_p) % field_p
        x3 = (lam * lam - x1 - x2) % field_p
        y3 = (lam * (x1 - x3) - y1) % field_p
        return (x3, y3)

    # Derived from the library itself (private key 1) rather than a
    # hand-typed literal -- exactly the class of transcription risk this
    # project's own discipline warns about (an earlier draft of this
    # self-test hand-copied Gy one hex digit short, caught only because
    # the on-curve check below failed loudly instead of silently).
    g_numbers = ec.derive_private_key(1, curve).public_key().public_numbers()
    g = (g_numbers.x, g_numbers.y)
    neg_g = (g_numbers.x, (-g_numbers.y) % field_p)

    def hash160_of_point(point, compressed):
        x, y = point
        if compressed:
            pk = bytes([2 + (y & 1)]) + x.to_bytes(32, "big")
        else:
            pk = b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")
        return hash160(pk)

    plus_g = point_add(p, g)
    minus_g = point_add(p, neg_g)

    def scalar_mul(point, k):
        result = None
        addend = point
        while k:
            if k & 1:
                result = point_add(result, addend)
            addend = point_add(addend, addend)
            k >>= 1
        return result

    inv2 = pow(2, -1, SECP256K1_ORDER)
    half = scalar_mul(p, inv2)
    double = scalar_mul(p, 2)

    computed = {
        hash160_of_point(plus_g, True): "P+G/compressed",
        hash160_of_point(plus_g, False): "P+G/uncompressed",
        hash160_of_point(minus_g, True): "P-G/compressed",
        hash160_of_point(minus_g, False): "P-G/uncompressed",
        hash160_of_point(half, True): "P/2/compressed",
        hash160_of_point(half, False): "P/2/uncompressed",
        hash160_of_point(double, True): "2P/compressed",
        hash160_of_point(double, False): "2P/uncompressed",
    }
    assert len(computed) == 8
    for h, label in computed.items():
        assert h in KNOWN_TARGET_HASH160S, f"{label}: {h.hex()} not in pinned KNOWN_TARGET_HASH160S"
        assert KNOWN_TARGET_HASH160S[h] == label, f"label mismatch for {h.hex()}"

    # 3. End-to-end planted-hit test: build a synthetic 80-byte blob whose
    #    body's XOR combine lands exactly on a known scalar's address, and
    #    confirm the real driver (decrypt -> extract A/B -> combine -> check)
    #    actually finds it -- not just that the math above is correct in
    #    isolation.
    target_scalar = (7).to_bytes(32, "big")
    a_planted = bytes(range(32))
    b_planted = bytes(x ^ y for x, y in zip(a_planted, target_scalar))  # xor(a,b) == target
    body = a_planted + b_planted  # exactly 64 bytes, no padding needed for CFB
    salt = b"selftst!"
    passwd = b"self-test-password"
    key, iv = cb_common.evp_bytes_to_key(passwd, salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    ct = encryptor.update(body) + encryptor.finalize()

    synthetic_blobs = {"SYNTH": (salt, ct)}
    target_addrs = private_key_details(target_scalar)
    synthetic_target = {bytes.fromhex(target_addrs["compressed"]["hash160"]): "planted/compressed"}

    report = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets=synthetic_target)

    assert report["total_hits"] >= 1, "planted xor-combine hit was not found by the real driver"
    assert any(h["operation"] == "xor" and h["kind"] == "known_target" for h in report["hits"]), (
        "the specific planted xor hit was not recovered"
    )

    # Every hit now also carries candidate provenance, not just literal/sha256.
    hit = next(h for h in report["hits"] if h["operation"] == "xor" and h["kind"] == "known_target")
    assert hit["candidate_index"] == 0
    assert hit["candidate_sha256"] == hashlib.sha256(passwd).hexdigest()

    # 4. Negative control: an unrelated password against the same synthetic
    #    blob must not produce any hit (sanity that the pipeline isn't
    #    trivially promoting everything).
    wrong_report = run(blobs=synthetic_blobs, candidates=["definitely-not-the-password"],
                       known_targets=synthetic_target)
    assert wrong_report["total_hits"] == 0, "wrong password unexpectedly produced a hit"

    # 5. Fail-closed on a requested-but-missing Bloom cache -- a real
    #    correctness bug in an earlier draft: bloom_path silently fell back
    #    to bloom=None, so a real run against a stale/absent cache path
    #    would have quietly checked only the pinned known targets and
    #    reported a misleadingly clean "0 hits".
    missing_path = "/nonexistent/path/does-not-exist.bloom"
    try:
        run(blobs=synthetic_blobs, candidates=[passwd.decode()], bloom_path=missing_path)
        raise AssertionError("a missing but explicitly requested Bloom cache must raise, not fall back silently")
    except FileNotFoundError:
        pass
    # bloom_path=None (not merely a path that happens to be missing) is the
    # explicit "run without Bloom coverage" opt-out and must NOT raise.
    run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets=synthetic_target, bloom_path=None)

    # 6. Bloom hits are live-confirmed, not counted on containment alone --
    #    a real correctness gap in an earlier draft (check_scalar's
    #    "bloom_prefilter" kind was appended straight to hits/total_hits,
    #    with nothing performing the mandatory API confirmation the
    #    docstring promised). Build a real temporary Bloom cache (the same
    #    _write_test_bloom helper key_shape_sweep.py already reuses
    #    cross-module for this) containing the planted target's hash160,
    #    with an EMPTY known_targets so the hit can only be found via the
    #    Bloom path, and inject a fake confirm_fn to prove both directions:
    #    False must drop the hit, True must promote it to "bloom_confirmed".
    import tempfile
    from binary_key_material_backfill import _write_test_bloom

    target_hash160 = bytes.fromhex(target_addrs["compressed"]["hash160"])
    with tempfile.NamedTemporaryFile(suffix=".bloom", delete=False) as tmp:
        tmp_bloom_path = tmp.name
    try:
        # A filter sized for just one entry saturates almost every lookup
        # (documented elsewhere in this project's own Bloom tests) -- every
        # one of the run's ~1,000+ combine checks would then "hit" and
        # trigger a real API_RATE_LIMIT_SECONDS sleep each, which is exactly
        # what made an earlier draft of this self-test hang for tens of
        # minutes. Padding to a realistic size (bytes 0..200, distinct from
        # target_hash160 below) restores real selectivity.
        padding = [bytes([i]) * 20 for i in range(200)]
        _write_test_bloom(tmp_bloom_path, padding + [target_hash160])

        confirm_calls = []

        def fake_confirm_false(address):
            confirm_calls.append(address)
            return False

        denied_report = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets={},
                            bloom_path=tmp_bloom_path, confirm_fn=fake_confirm_false)
        assert denied_report["total_hits"] == 0, "an unconfirmed Bloom hit must not be counted"
        assert len(confirm_calls) >= 1, "confirm_fn was never actually invoked on the Bloom hit"

        def fake_confirm_true(_address):
            return True

        confirmed_report = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets={},
                               bloom_path=tmp_bloom_path, confirm_fn=fake_confirm_true)
        assert confirmed_report["total_hits"] >= 1, "a live-confirmed Bloom hit must be counted"
        assert any(h["kind"] == "bloom_confirmed" and h["operation"] == "xor"
                   for h in confirmed_report["hits"]), "the confirmed hit must be labeled bloom_confirmed"
    finally:
        Path(tmp_bloom_path).unlink(missing_ok=True)

    # 7. The prize address itself is a known target now (an earlier draft
    #    defined PRIZE_HASH160_HEX but never added it to KNOWN_TARGET_HASH160S).
    assert bytes.fromhex(PRIZE_HASH160_HEX) in KNOWN_TARGET_HASH160S
    assert KNOWN_TARGET_HASH160S[bytes.fromhex(PRIZE_HASH160_HEX)] == "prize_address"

    # 8. Frozen-corpus contract, now digest-enforced (count alone would
    #    pass for 42 modified or duplicate candidates).
    cands = frozen_candidates()
    assert len(cands) == EXPECTED_CANDIDATE_COUNT
    assert len(set(cands)) == EXPECTED_CANDIDATE_COUNT, "duplicate candidate text in the frozen corpus"
    assert candidate_list_digest(cands) == EXPECTED_CANDIDATE_DIGEST, (
        f"frozen corpus digest changed -- expected {EXPECTED_CANDIDATE_DIGEST}, "
        "p1a_sentinel_backfill.py's manifest must have drifted upstream"
    )
    assert len(passphrase_forms(cands[0])) == EXPECTED_FORM_COUNT
    real_report_shape = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets=synthetic_target)
    assert real_report_shape["candidate_digest"] == candidate_list_digest([passwd.decode()])

    print("[*] self-test OK: 15 combine forms, 9 known-target constants (8 EC-derived + prize) "
          "independently re-derived, planted xor-combine hit recovered end-to-end with provenance, "
          "wrong-password control clean, fail-closed missing-Bloom-cache behavior confirmed, "
          "Bloom hits proven to require live confirmation (both directions), frozen-corpus digest "
          f"{EXPECTED_CANDIDATE_DIGEST} enforced, {EXPECTED_CANDIDATE_COUNT} frozen candidates confirmed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--bloom-cache", default=str(SCRIPT_DIR.parent.parent / "db" / "addresses.hash160.bloom"))
    parser.add_argument("--no-bloom", action="store_true",
                        help="Run without Bloom coverage intentionally (only the pinned known "
                             "targets are still checked) -- the explicit opt-out; omitting this "
                             "with a missing --bloom-cache path now raises instead of silently "
                             "continuing without it.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    bloom_path = None if args.no_bloom else args.bloom_cache
    report = run(bloom_path=bloom_path) if args.run else {"note": "pass --run to execute against the oracle"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            if key == "hits":
                continue
            print(f"{key}: {value}")
        for hit in report.get("hits", []):
            print("HIT:", hit)


if __name__ == "__main__":
    main()
