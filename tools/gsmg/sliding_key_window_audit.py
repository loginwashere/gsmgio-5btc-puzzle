#!/usr/bin/env python3
"""A1+A2 from doc/Brainstorms/2026-08-20 - Creative Brute-Force Coverage
Expansion.md (ranked #1 by expected impact): sliding raw-key windows plus
byte-order/packing transforms.

Why distinct from every existing raw-key detector (Phase 328's Bloom-chunk
check, this project's Phase 336 B1 combine-algebra check): both of those
only ever look at ALIGNED 32-byte chunks (offsets 0 and 32). A correct raw
key beginning at any other byte offset within the plaintext -- 1 through
31, say -- is currently invisible to every detector in this project. A1
closes that by sliding a 32-byte window across a bounded plaintext prefix
instead of only checking `chunks_exact(32)`.

Pre-registration (frozen before any real run, matching this document's own
"Decisions"/stop-rule requirement and Phase 336's precedent):

  - Frozen inputs: the same 42 P0A/Phase-335 sentinel candidates, 2 forms
    each (literal, hex SHA-256) -- reused from half_better_half_algebra_
    audit.py for direct comparability with Phase 336, not re-selected here.
  - Frozen crypto scope: identical to Phase 336 -- cb_common.KDF_VARIANTS
    (6, CBC) + ECB_CIPHER_VARIANTS (12) + STREAM_CIPHER_VARIANTS (36) x 4
    blobs = 54 variants x 4 blobs = 216 (variant, blob) pairs/form, bodies
    retained on valid PKCS7 padding (CBC/ECB) or unconditionally (stream),
    minimum 32 bytes (one window's worth).
  - Frozen window bound: the first 64 bytes of each retained body (A1's own
    "first version" suggestion -- 64 or 96 bytes; 64 chosen as the more
    conservative bound, matching this project's habit of a cheap pilot
    before an expensive full sweep). That gives 33 windows per body
    (offsets 0..32 inclusive) -- window 0 and window 32 are exactly the
    two ALIGNED chunks every existing detector already checks; windows
    1..31 are the genuinely new coverage this idea adds.
  - Frozen byte-order family (A2, verbatim): identity (the window itself,
    unmodified) + full-byte reversal + reversal within 4-byte words +
    reversal within 8-byte words + reversal of (4-byte) word order +
    nibble swap within each byte + bit reversal within each byte = 7 forms
    per window. No operation added or dropped after seeing results.
  - Frozen success criterion: identical to Phase 336 -- a valid secp256k1
    scalar whose compressed/uncompressed hash160 matches the live
    production Bloom cache (mandatorily confirmed) or one of Phase 331's 8
    known EC-derived targets (exact, unconditional).
  - Stop rule: run exactly once over the frozen scope above.

Scope note: 33 windows x 7 forms = 231 checks per retained body -- roughly
15x the 15 checks/body Phase 336 needed. This pilot stays on the same
42-candidate corpus (not the full 14,551-keystring core corpus) for exactly
the reason A1's own "Risk" note names: real scale needs GPU batching. This
validates the detector and gets an initial bounded result first.
"""

import argparse
import hashlib
import json
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
    SECP256K1_ORDER,
    BloomCache,
    candidate_list_digest,
    check_scalar,
    confirm_address_live,
    frozen_candidates,
    frozen_candidates_with_provenance,
    passphrase_forms,
    raw_cbc_bodies,
    raw_ecb_bodies,
    raw_stream_bodies,
)

PREFIX_BOUND = 64
WINDOW_SIZE = 32
EXPECTED_WINDOW_COUNT = PREFIX_BOUND - WINDOW_SIZE + 1  # 33


def _reverse_word_bytes(window: bytes, word_size: int) -> bytes:
    out = bytearray(window)
    for start in range(0, len(window), word_size):
        out[start:start + word_size] = window[start:start + word_size][::-1]
    return bytes(out)


def _reverse_word_order(window: bytes, word_size: int) -> bytes:
    words = [window[i:i + word_size] for i in range(0, len(window), word_size)]
    return b"".join(reversed(words))


def _nibble_swap(window: bytes) -> bytes:
    return bytes(((b & 0x0F) << 4) | ((b & 0xF0) >> 4) for b in window)


_BIT_REVERSE_TABLE = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))


def _bit_reversal(window: bytes) -> bytes:
    return bytes(_BIT_REVERSE_TABLE[b] for b in window)


def byte_order_forms(window: bytes) -> dict:
    """The exact 7 forms (identity + A2's 6 named transforms). `window`
    must be exactly 32 bytes."""
    assert len(window) == WINDOW_SIZE
    return {
        "identity": window,
        "full_byte_reversal": window[::-1],
        "reverse_4byte_words": _reverse_word_bytes(window, 4),
        "reverse_8byte_words": _reverse_word_bytes(window, 8),
        "reverse_word_order_4byte": _reverse_word_order(window, 4),
        "nibble_swap": _nibble_swap(window),
        "bit_reversal": _bit_reversal(window),
    }


def sliding_windows(body: bytes, prefix_bound: int = PREFIX_BOUND):
    """Every (offset, 32-byte window) within the first `prefix_bound` bytes
    of `body` -- offset 0 and offset 32 are the two ALIGNED chunks every
    existing detector already checks; every other offset is new coverage."""
    prefix = body[:prefix_bound]
    for offset in range(0, len(prefix) - WINDOW_SIZE + 1):
        yield offset, prefix[offset:offset + WINDOW_SIZE]


def run(blobs=None, bloom_path=None, candidates=None, known_targets=None,
        prefix_bound=PREFIX_BOUND, confirm_fn=None):
    active_blobs = BLOBS if blobs is None else blobs
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets
    confirm = confirm_address_live if confirm_fn is None else confirm_fn

    if candidates is None:
        cand_records = frozen_candidates_with_provenance()
    else:
        cand_records = [(i, "external", f"candidate_{i}", text) for i, text in enumerate(candidates)]
    candidate_texts = [text for (_i, _model, _label, text) in cand_records]

    if bloom_path is not None:
        if not Path(bloom_path).exists():
            # Same fail-closed fix as half_better_half_algebra_audit.py's
            # run() -- see that module's docstring/Phase 336 correction for
            # why silently falling back to bloom=None was a real bug.
            raise FileNotFoundError(
                f"Bloom cache requested at {bloom_path!r} but the file does not exist -- "
                "pass bloom_path=None to run without Bloom coverage intentionally."
            )
        bloom = BloomCache(bloom_path)
    else:
        bloom = None

    attempts = 0
    bodies_checked = 0
    windows_checked = 0
    form_checks = 0
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
                    if len(body) < WINDOW_SIZE:
                        continue
                    bodies_checked += 1
                    for offset, window in sliding_windows(body, prefix_bound):
                        windows_checked += 1
                        for form_name, value in byte_order_forms(window).items():
                            form_checks += 1
                            hit = check_scalar(value, bloom, targets)
                            if hit is None:
                                continue
                            if hit["kind"] == "bloom_prefilter":
                                # Mandatory live confirmation, same as
                                # half_better_half_algebra_audit.py's run().
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
                                "offset": offset,
                                "byte_order_form": form_name,
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
        "windows_checked": windows_checked,
        "form_checks": form_checks,
        "bloom_active": bloom is not None,
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    # 1. Byte-order form sanity, on a window with no accidental symmetry.
    window = bytes(range(32))
    forms = byte_order_forms(window)
    assert len(forms) == 7, f"expected 7 named forms (identity + 6), got {len(forms)}"
    assert all(len(v) == 32 for v in forms.values())
    assert forms["identity"] == window
    assert forms["full_byte_reversal"] == window[::-1]
    assert forms["reverse_4byte_words"][:4] == window[:4][::-1]
    assert forms["reverse_4byte_words"][4:8] == window[4:8][::-1]
    assert forms["reverse_8byte_words"][:8] == window[:8][::-1]
    assert forms["reverse_word_order_4byte"][:4] == window[-4:]
    assert forms["reverse_word_order_4byte"][-4:] == window[:4]
    assert forms["nibble_swap"][0] == ((window[0] & 0x0F) << 4) | ((window[0] & 0xF0) >> 4)
    assert forms["bit_reversal"][0] == int(f"{window[0]:08b}"[::-1], 2)
    # bit_reversal and nibble_swap are each involutions (applying twice is identity).
    assert _bit_reversal(_bit_reversal(window)) == window
    assert _nibble_swap(_nibble_swap(window)) == window

    # 2. Sliding-window enumeration sanity: exactly 33 windows over a
    #    64-byte body, window 0 == body[:32], window 32 == body[32:64]
    #    (the two ALIGNED chunks every existing detector already checks).
    body = bytes(range(64))
    windows = list(sliding_windows(body))
    assert len(windows) == EXPECTED_WINDOW_COUNT == 33
    assert windows[0] == (0, body[:32])
    assert windows[32] == (32, body[32:64])
    offsets = [offset for offset, _ in windows]
    assert offsets == list(range(33))

    # 3. End-to-end planted-hit test: a synthetic AES-CFB blob whose body
    #    has a known scalar sitting at an UNALIGNED offset (17, deliberately
    #    not 0 or 32 -- the exact case an aligned-chunk-only detector would
    #    miss) in its natural byte order (form "identity"). Confirms the
    #    real driver -- not just the enumeration/transform math -- finds it.
    import hashlib
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from binary_key_material_backfill import private_key_details
    import cb_common

    target_scalar = (99).to_bytes(32, "big")
    filler = hashlib.sha256(b"filler").digest() * 2  # 64 bytes of non-key noise
    body = filler[:17] + target_scalar + filler[:15]  # 64 bytes; key sits at offset 17
    assert len(body) == 64
    assert body[17:49] == target_scalar

    salt = b"selftst2"
    passwd = b"self-test-password-2"
    key, iv = cb_common.evp_bytes_to_key(passwd, salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    ct = encryptor.update(body) + encryptor.finalize()

    synthetic_blobs = {"SYNTH": (salt, ct)}
    target_addrs = private_key_details(target_scalar)
    synthetic_target = {bytes.fromhex(target_addrs["compressed"]["hash160"]): "planted/compressed"}

    report = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets=synthetic_target)
    assert report["total_hits"] >= 1, "planted unaligned-offset key was not found by the real driver"
    assert any(h["offset"] == 17 and h["byte_order_form"] == "identity" and h["kind"] == "known_target"
               for h in report["hits"]), "the specific planted (offset=17, identity) hit was not recovered"
    planted_hit = next(h for h in report["hits"] if h["offset"] == 17 and h["byte_order_form"] == "identity")
    assert planted_hit["candidate_index"] == 0
    assert planted_hit["candidate_sha256"] == hashlib.sha256(passwd).hexdigest()

    # 4. Negative control.
    wrong_report = run(blobs=synthetic_blobs, candidates=["definitely-not-the-password"],
                       known_targets=synthetic_target)
    assert wrong_report["total_hits"] == 0, "wrong password unexpectedly produced a hit"

    # 5. Fail-closed on a requested-but-missing Bloom cache (same
    #    correctness fix as half_better_half_algebra_audit.py's run()).
    try:
        run(blobs=synthetic_blobs, candidates=[passwd.decode()], bloom_path="/nonexistent/x.bloom")
        raise AssertionError("a missing but explicitly requested Bloom cache must raise")
    except FileNotFoundError:
        pass
    run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets=synthetic_target, bloom_path=None)

    # 6. Bloom hits require live confirmation -- proven both directions
    #    with a padded (non-saturating) temporary Bloom cache, mirroring
    #    half_better_half_algebra_audit.py's own self-test fix.
    import tempfile
    from binary_key_material_backfill import _write_test_bloom

    target_hash160 = bytes.fromhex(target_addrs["compressed"]["hash160"])
    with tempfile.NamedTemporaryFile(suffix=".bloom", delete=False) as tmp:
        tmp_bloom_path = tmp.name
    try:
        padding = [bytes([i]) * 20 for i in range(200)]
        _write_test_bloom(tmp_bloom_path, padding + [target_hash160])

        denied = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets={},
                    bloom_path=tmp_bloom_path, confirm_fn=lambda _addr: False)
        assert denied["total_hits"] == 0, "an unconfirmed Bloom hit must not be counted"

        confirmed = run(blobs=synthetic_blobs, candidates=[passwd.decode()], known_targets={},
                        bloom_path=tmp_bloom_path, confirm_fn=lambda _addr: True)
        assert confirmed["total_hits"] >= 1, "a live-confirmed Bloom hit must be counted"
        assert any(h["kind"] == "bloom_confirmed" and h["offset"] == 17 for h in confirmed["hits"])
    finally:
        Path(tmp_bloom_path).unlink(missing_ok=True)

    # 7. Frozen-corpus contract, digest-enforced (same pin as Phase 336's).
    cands = frozen_candidates()
    assert len(cands) == 42
    assert candidate_list_digest(cands) == EXPECTED_CANDIDATE_DIGEST

    print("[*] self-test OK: 7 byte-order forms, 33-window sliding enumeration confirmed, "
          "planted unaligned-offset (offset=17) hit recovered end-to-end with provenance, "
          "wrong-password control clean, fail-closed missing-Bloom-cache behavior confirmed, "
          "Bloom hits proven to require live confirmation (both directions), "
          f"frozen-corpus digest {EXPECTED_CANDIDATE_DIGEST} enforced, 42 frozen candidates confirmed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--bloom-cache", default=str(SCRIPT_DIR.parent.parent / "db" / "addresses.hash160.bloom"))
    parser.add_argument("--no-bloom", action="store_true",
                        help="Run without Bloom coverage intentionally -- see half_better_half_"
                             "algebra_audit.py's --no-bloom for why this is required now instead "
                             "of a missing --bloom-cache path silently doing the same thing.")
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
