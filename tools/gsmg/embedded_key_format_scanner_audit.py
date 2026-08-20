#!/usr/bin/env python3
"""A3 from doc/Brainstorms/2026-08-20 - Creative Brute-Force Coverage
Expansion.md: "unconditional embedded key-format scanner."

Ranked #3 by expected impact ("completes Phase 327's open CUDA/full-corpus
scope"). Phase 327 built `key_shape_classifier.py` (hex64, WIF, checksum-
valid BIP39) and ran it against the 648-candidate core corpus; Phase 333
ran it again against Phase 328's 43 highest-suspicion weak-hit bodies. A3
asks a broader question than either: scan EVERY retained body (not just
weak-hit survivors) for a wider set of key-shaped encodings, including ones
`key_shape_classifier.py` does not implement -- decimal private scalars,
SEC1 compressed/uncompressed public keys, and BIP32 extended key
(`xprv`/`xpub`) payloads.

Pre-registration (frozen before any real run, matching Phase 336/337's
precedent):

  - Frozen inputs, crypto scope, and retention rule: identical to Phase
    336/337 -- the same 42 P0A/Phase-335 sentinel candidates x 2 forms, the
    same 54 variants (KDF_VARIANTS/ECB_CIPHER_VARIANTS/STREAM_CIPHER_
    VARIANTS) x 4 blobs, bodies retained on valid PKCS7 padding (CBC/ECB)
    or unconditionally (stream) -- reused directly from
    half_better_half_algebra_audit.py, not re-selected.
  - Frozen finder set: `key_shape_classifier.classify_body()` (hex64, WIF,
    checksum-valid BIP39, raw 64-byte halves) UNCHANGED, plus three new
    finders below (decimal scalar, SEC1 pubkey, xprv/xpub), each exact/
    checksum-gated -- no approximate or fuzzy matching, matching this
    project's classifier discipline throughout.
  - Frozen success criterion: any classifier match is itself the result
    (a checksum/curve-valid key-shaped string inside a decrypt is
    newsworthy on its own -- see "Result" below for how this differs from
    Phase 336/337's Bloom/known-target address check).
  - Stop rule: run exactly once over the frozen scope above.

Scope note: full-corpus/GPU scale is explicitly out of scope here too (same
reason as every other idea from this brainstorm run so far) -- this is the
bounded pilot Phase 327's own reopen condition anticipated before a CUDA
port becomes worth building.
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from half_better_half_algebra_audit import (  # noqa: E402
    API_RATE_LIMIT_SECONDS,
    BLOBS,
    EXPECTED_CANDIDATE_DIGEST,
    KNOWN_TARGET_HASH160S,
    BloomCache,
    candidate_list_digest,
    confirm_address_live,
    frozen_candidates,
    frozen_candidates_with_provenance,
    passphrase_forms,
    raw_cbc_bodies,
    raw_ecb_bodies,
    raw_stream_bodies,
)
from binary_key_material_backfill import SECP256K1_FIELD, hash160, private_key_details  # noqa: E402
from first_hint_hash_audit import BASE58_ALPHABET, SECP256K1_ORDER, base58check  # noqa: E402
import key_shape_classifier  # noqa: E402

# Decimal scalar: boundary-anchored ASCII digit run. secp256k1's order n has
# at most 78 decimal digits (n ~= 1.158e77); bounded to >=60 digits to keep
# the false-positive volume from short number runs manageable -- a shorter
# digit run is astronomically unlikely to be a meaningful scalar and would
# just be noise (this is a declared bound, not a tuned-after-results one).
DECIMAL_SCALAR_RE = re.compile(rb"(?<![0-9])[0-9]{60,78}(?![0-9])")

# BIP32 extended-key version bytes (mainnet).
XPRV_VERSION = bytes.fromhex("0488ADE4")
XPUB_VERSION = bytes.fromhex("0488B21E")
# Typical xprv/xpub Base58Check string length range (78-byte payload + 4-byte
# checksum, base58-encoded -- varies by leading-zero-byte count, hence a
# range rather than one fixed length).
EXTENDED_KEY_RE = re.compile(
    rb"(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{107,113}(?![1-9A-HJ-NP-Za-km-z])"
)


def find_decimal_scalars(body: bytes):
    found = []
    for match in DECIMAL_SCALAR_RE.finditer(body):
        value = int(match.group())
        if 1 <= value < SECP256K1_ORDER:
            found.append(("decimal_scalar", value.to_bytes(32, "big")))
    return found


def _mod_sqrt(a: int, p: int):
    """p (secp256k1's field prime) is 3 mod 4, so sqrt(a) = a^((p+1)/4) mod p
    when a is a quadratic residue -- verified by squaring the result."""
    if a == 0:
        return 0
    candidate = pow(a, (p + 1) // 4, p)
    if (candidate * candidate) % p != a:
        return None
    return candidate


def find_sec1_pubkeys(body: bytes, bloom=None, known_targets=None):
    """Scans raw bytes (not ASCII) for a SEC1 compressed (33-byte,
    0x02/0x03 prefix) or uncompressed (65-byte, 0x04 prefix) public key.

    Curve membership ALONE is not a meaningful filter here, unlike every
    other finder in this module: a compressed point's x-coordinate is a
    quadratic residue for ~50% of arbitrary 32-byte values (there is no
    checksum, unlike WIF/xprv/xpub's 4 bytes or BIP39's 11-bit checksum),
    so a curve-valid-only version of this finder produced 17,182 "matches"
    against this run's corpus in an earlier draft -- confirmed (not
    theorized) chance noise, not a signal, once the address-level check
    below was added and every one of those 17,182 candidates turned out to
    hash to neither the Bloom cache nor a known target. The real filter is
    therefore the same one every other detector in this project's Phase
    331/336/337 lineage uses: derive the actual hash160 from the candidate
    pubkey bytes and require a Bloom cache or known-target match before
    counting it as a result at all."""
    found = []
    p = SECP256K1_FIELD
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets
    known_curve_valid = 0
    for i in range(len(body)):
        prefix = body[i]
        pubkey_bytes = None
        kind = None
        if prefix in (0x02, 0x03) and i + 33 <= len(body):
            x = int.from_bytes(body[i + 1:i + 33], "big")
            if x >= p:
                continue
            y_squared = (pow(x, 3, p) + 7) % p
            if _mod_sqrt(y_squared, p) is None:
                continue
            pubkey_bytes, kind = body[i:i + 33], "sec1_compressed"
        elif prefix == 0x04 and i + 65 <= len(body):
            x = int.from_bytes(body[i + 1:i + 33], "big")
            y = int.from_bytes(body[i + 33:i + 65], "big")
            if not (x < p and y < p and (y * y - (pow(x, 3, p) + 7)) % p == 0):
                continue
            pubkey_bytes, kind = body[i:i + 65], "sec1_uncompressed"
        if pubkey_bytes is None:
            continue
        known_curve_valid += 1
        h = hash160(pubkey_bytes)
        if h in targets:
            found.append((kind, (i, pubkey_bytes.hex(), "known_target", targets[h])))
        elif bloom is not None and bloom.contains(h):
            # 4th element is the derived address (not a label) for this
            # kind -- run() needs it to mandatorily live-confirm before
            # counting, same as every other Bloom hit in this project.
            found.append((kind, (i, pubkey_bytes.hex(), "bloom_prefilter", base58check(b"\x00" + h))))
    return found, known_curve_valid


def find_extended_keys(body: bytes):
    found = []
    for match in EXTENDED_KEY_RE.finditer(body):
        token = match.group().decode("ascii")
        payload = key_shape_classifier.base58check_decode(token)
        if payload is None or len(payload) != 78:
            continue
        version = payload[:4]
        if version == XPRV_VERSION:
            found.append(("xprv", token))
        elif version == XPUB_VERSION:
            found.append(("xpub", token))
    return found


def classify_body_extended(body: bytes, bloom=None, known_targets=None):
    """key_shape_classifier's existing finders, unchanged, plus the three
    new ones this idea adds. Returns (matches, sec1_curve_valid_count) --
    the second number is diagnostic only (see find_sec1_pubkeys's doc
    comment for why raw curve validity is reported separately from real
    matches)."""
    found = list(key_shape_classifier.classify_body(body))
    found.extend(find_decimal_scalars(body))
    sec1_found, sec1_curve_valid = find_sec1_pubkeys(body, bloom, known_targets)
    found.extend(sec1_found)
    found.extend(find_extended_keys(body))
    return found, sec1_curve_valid


def run(blobs=None, candidates=None, bloom_path=None, known_targets=None, confirm_fn=None):
    active_blobs = BLOBS if blobs is None else blobs
    confirm = confirm_address_live if confirm_fn is None else confirm_fn

    if candidates is None:
        cand_records = frozen_candidates_with_provenance()
    else:
        cand_records = [(i, "external", f"candidate_{i}", text) for i, text in enumerate(candidates)]
    candidate_texts = [text for (_i, _model, _label, text) in cand_records]

    if bloom_path is not None:
        if not Path(bloom_path).exists():
            # Same fail-closed fix as half_better_half_algebra_audit.py's
            # run() (Phase 336's correction) -- a requested-but-missing
            # Bloom cache must not silently leave every sec1_* candidate
            # unchecked against it.
            raise FileNotFoundError(
                f"Bloom cache requested at {bloom_path!r} but the file does not exist -- "
                "pass bloom_path=None to run without Bloom coverage intentionally."
            )
        bloom = BloomCache(bloom_path)
    else:
        bloom = None

    attempts = 0
    bodies_checked = 0
    sec1_curve_valid_total = 0
    matches = []
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
                    found, sec1_curve_valid = classify_body_extended(body, bloom, known_targets)
                    sec1_curve_valid_total += sec1_curve_valid
                    for kind, payload in found:
                        if (kind in ("sec1_compressed", "sec1_uncompressed")
                                and isinstance(payload, tuple) and payload[2] == "bloom_prefilter"):
                            # Mandatory live confirmation before counting --
                            # same discipline as Phase 336/337's run().
                            address = payload[3]
                            time.sleep(API_RATE_LIMIT_SECONDS)
                            if not confirm(address):
                                continue
                            payload = (payload[0], payload[1], "bloom_confirmed", address)
                        matches.append({
                            "candidate_index": index,
                            "candidate_model": model,
                            "candidate_label": label,
                            "candidate_sha256": candidate_sha256,
                            "candidate_form": form_kind,
                            "variant": variant_label,
                            "blob": tag,
                            "kind": kind,
                            "payload": payload.hex() if isinstance(payload, bytes) else payload,
                        })
    finally:
        if bloom is not None:
            bloom.close()

    return {
        "candidate_count": len(cand_records),
        "candidate_digest": candidate_list_digest(candidate_texts),
        "passphrase_attempts": attempts,
        "bodies_checked": bodies_checked,
        "bloom_active": bloom is not None,
        "sec1_curve_valid_diagnostic_only": sec1_curve_valid_total,
        "matches": matches,
        "total_matches": len(matches),
    }


def self_test():
    # 1. Decimal scalar: planted valid and invalid (>= n) runs.
    valid_scalar = 12345678901234567890123456789012345678901234567890123456789012  # 62 digits, < n
    body_valid = b"noise" + str(valid_scalar).encode() + b"noise"
    found = find_decimal_scalars(body_valid)
    assert any(int.from_bytes(k, "big") == valid_scalar for _, k in found), "planted decimal scalar not found"

    too_big = SECP256K1_ORDER + 5  # >= n, must NOT be reported
    body_invalid = b"noise" + str(too_big).encode() + b"noise"
    assert find_decimal_scalars(body_invalid) == [], "out-of-range scalar must not be reported"

    # 2. SEC1 pubkey: derive a real compressed+uncompressed pubkey from a
    #    known private key, embed each inside unrelated filler bytes, and
    #    confirm the ADDRESS-GATED finder recognizes each only when its
    #    hash160 is a known target -- and reports nothing at all for the
    #    exact same bytes when it isn't (proving curve-membership alone
    #    does not produce a "match", per find_sec1_pubkeys's own doc
    #    comment about the 17,182-false-positive draft this replaced).
    from cryptography.hazmat.primitives.asymmetric import ec
    priv = 7
    pub = ec.derive_private_key(priv, ec.SECP256K1()).public_key().public_numbers()
    x_bytes, y_bytes = pub.x.to_bytes(32, "big"), pub.y.to_bytes(32, "big")
    compressed = bytes([2 + (pub.y & 1)]) + x_bytes
    uncompressed = b"\x04" + x_bytes + y_bytes

    filler = b"\xAA" * 10
    body_c = filler + compressed + filler
    body_u = filler + uncompressed + filler

    # Without a matching target: curve-valid, but zero reported matches --
    # only the diagnostic curve-valid count is nonzero.
    found_none, curve_valid_none = find_sec1_pubkeys(body_c)
    assert found_none == [], "an untargeted curve-valid pubkey must not be reported as a match"
    assert curve_valid_none >= 1, "the diagnostic curve-valid count must still see it"

    # With the planted pubkey's own hash160 as a known target: now it's a match.
    synthetic_pubkey_target = {hash160(compressed): "planted/compressed"}
    found_c, _ = find_sec1_pubkeys(body_c, known_targets=synthetic_pubkey_target)
    assert any(kind == "sec1_compressed" and offset == len(filler)
               for kind, (offset, _hexval, match_kind, _label) in found_c
               if match_kind == "known_target"), "planted compressed pubkey not matched once it's a known target"

    synthetic_pubkey_target_u = {hash160(uncompressed): "planted/uncompressed"}
    found_u, _ = find_sec1_pubkeys(body_u, known_targets=synthetic_pubkey_target_u)
    assert any(kind == "sec1_uncompressed" and offset == len(filler)
               for kind, (offset, _hexval, match_kind, _label) in found_u
               if match_kind == "known_target"), "planted uncompressed pubkey not matched once it's a known target"

    # Negative control: random bytes of the right length essentially never land on-curve.
    found_random, curve_valid_random = find_sec1_pubkeys(b"\x02" + bytes(range(32)))
    assert found_random == [] and curve_valid_random == 0, (
        "an arbitrary non-curve x-coordinate must not be reported as valid at all"
    )

    # 3. Extended keys: build a real xprv from a known seed via
    #    key_shape_classifier's own BIP32 implementation and confirm it's
    #    recognized; a version-byte-corrupted token must not be.
    seed = key_shape_classifier.mnemonic_seed(
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about".split()
    )
    master_key, master_chain = key_shape_classifier.bip32_master(seed)
    from first_hint_hash_audit import base58check
    xprv_payload = XPRV_VERSION + b"\x00" * 5 + b"\x00\x00\x00\x00" + master_chain + b"\x00" + master_key
    assert len(xprv_payload) == 78
    xprv_token = base58check(xprv_payload)
    # "0" (not "prefix"/"suffix") as filler: 0/O/I/l are excluded from the
    # base58 alphabet, so this actually delimits the token boundary --
    # ordinary letters would silently merge with the token's own base58
    # characters and never hit the regex's boundary lookaround at all.
    found_x = find_extended_keys(b"000" + xprv_token.encode() + b"000")
    assert any(kind == "xprv" and token == xprv_token for kind, token in found_x), "planted xprv not recognized"

    corrupted = base58check(b"\x00\x00\x00\x00" + xprv_payload[4:])  # wrong version bytes
    assert find_extended_keys(corrupted.encode()) == [], "wrong version bytes must not be reported as xprv/xpub"

    # 4. classify_body_extended must include the pre-existing
    #    key_shape_classifier coverage, the decimal-scalar finder
    #    unconditionally, and the SEC1 finder once a target is supplied.
    combo_body = filler + compressed + b"filler" + str(valid_scalar).encode()
    combo, combo_curve_valid = classify_body_extended(combo_body, known_targets=synthetic_pubkey_target)
    kinds = {k for k, _ in combo}
    assert "sec1_compressed" in kinds and "decimal_scalar" in kinds
    assert combo_curve_valid >= 1

    # 5. End-to-end: run() through the real decrypt pipeline, with the
    #    planted compressed pubkey inside a synthetic AES-CFB body, proving
    #    a Bloom-only sec1 hit is (a) never counted without live
    #    confirmation and (b) counted with candidate provenance once
    #    confirmed -- mirrors Phase 336/337's own run()-level fixes.
    import cb_common
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    synth_passwd = b"self-test-password-3"
    synth_salt = b"selftst3"
    # >= 64 bytes total: raw_cbc_bodies/raw_ecb_bodies/raw_stream_bodies
    # (shared with Phase 336/337) only retain bodies at that length or
    # longer, so the trailing filler is padded out well past it.
    synth_body = filler + compressed + filler * 3
    assert len(synth_body) >= 64
    key, iv = cb_common.evp_bytes_to_key(synth_passwd, synth_salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    ct = encryptor.update(synth_body) + encryptor.finalize()
    synthetic_blobs = {"SYNTH": (synth_salt, ct)}

    import tempfile
    from binary_key_material_backfill import _write_test_bloom

    target_hash160 = hash160(compressed)
    with tempfile.NamedTemporaryFile(suffix=".bloom", delete=False) as tmp:
        tmp_bloom_path = tmp.name
    try:
        padding = [bytes([i]) * 20 for i in range(200)]
        _write_test_bloom(tmp_bloom_path, padding + [target_hash160])

        denied = run(blobs=synthetic_blobs, candidates=[synth_passwd.decode()], known_targets={},
                    bloom_path=tmp_bloom_path, confirm_fn=lambda _addr: False)
        assert denied["total_matches"] == 0, "an unconfirmed Bloom sec1 hit must not be counted"

        confirmed = run(blobs=synthetic_blobs, candidates=[synth_passwd.decode()], known_targets={},
                        bloom_path=tmp_bloom_path, confirm_fn=lambda _addr: True)
        assert confirmed["total_matches"] >= 1, "a live-confirmed Bloom sec1 hit must be counted"
        hit = next(m for m in confirmed["matches"] if m["kind"] == "sec1_compressed")
        assert hit["payload"][2] == "bloom_confirmed"
        assert hit["candidate_index"] == 0
        assert hit["candidate_sha256"] == hashlib.sha256(synth_passwd).hexdigest()
    finally:
        Path(tmp_bloom_path).unlink(missing_ok=True)

    # 6. Fail-closed on a requested-but-missing Bloom cache.
    try:
        run(blobs=synthetic_blobs, candidates=[synth_passwd.decode()], bloom_path="/nonexistent/x.bloom")
        raise AssertionError("a missing but explicitly requested Bloom cache must raise")
    except FileNotFoundError:
        pass
    run(blobs=synthetic_blobs, candidates=[synth_passwd.decode()], bloom_path=None)

    # 7. Frozen-corpus contract, digest-enforced (same pin as Phase 336/337's).
    cands = frozen_candidates()
    assert len(cands) == 42
    assert candidate_list_digest(cands) == EXPECTED_CANDIDATE_DIGEST

    print("[*] self-test OK: decimal-scalar range gate, SEC1 compressed+uncompressed pubkey "
          "recognition at correct offset (with a non-curve negative control), xprv version-byte "
          "gate (with a corrupted-version negative control), combined classifier coverage, "
          "Bloom sec1 hits proven to require live confirmation end-to-end with provenance, "
          "fail-closed missing-Bloom-cache behavior confirmed, "
          f"frozen-corpus digest {EXPECTED_CANDIDATE_DIGEST} enforced, 42 frozen candidates confirmed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--bloom-cache", default=str(SCRIPT_DIR.parent.parent / "db" / "addresses.hash160.bloom"))
    parser.add_argument("--no-bloom", action="store_true",
                        help="Run without Bloom coverage intentionally -- see half_better_half_"
                             "algebra_audit.py's --no-bloom for why this is required now.")
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
            if key == "matches":
                continue
            print(f"{key}: {value}")
        for match in report.get("matches", []):
            print("MATCH:", match)


if __name__ == "__main__":
    main()
