#!/usr/bin/env python3
"""Path 2 from the 2026-07-24 "Best Remaining Paths" review: a staged oracle
that automatically chains a SALPH plaintext into a COSMIC passphrase attempt,
per the page-grammar reading (derive password -> open SALPH -> hash its
answer -> open COSMIC; "sha256 ans too" already motivates keystr_forms()'s
single/double-SHA256 forms in cb_common.py).

Every prior sweep in this project tests candidates against SALPH and COSMIC
independently. Nothing has ever chained a SALPH plaintext's own content into a
COSMIC attempt automatically -- because SALPH has never actually been opened
(0 hits across every sweep to date, including the newly broadened
extended_cipher_recheck.py). This module is therefore necessarily DORMANT
right now: it has nothing real to chain. Its value is purely to make sure
that the moment any script (this one or a future one) ever does get a SALPH
hit, the COSMIC implication is tested immediately and automatically rather
than requiring a human to notice and manually re-run a chain -- so it is
validated here against a SYNTHETIC scenario with a known answer, the same
discipline this project's other calibration work (see
checkerboard_recovery_calibration.py) established for validating a pipeline
before there is a real target to point it at.

Usage:
    python3 tools/gsmg/staged_pipeline.py --self-test
    python3 tools/gsmg/staged_pipeline.py --check-salph   # confirms SALPH is
        still unopened under every KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS
        combo before reporting the chain as dormant, rather than assuming it
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    aes_try_open,
    aes_try_open_bytes,
    answer_forms,
    evp_bytes_to_key,
    keystr_forms,
    pbkdf2_bytes_to_key,
    CIPHER_BLOCK_SIZES,
    CIPHER_CLASSES,
)
from cryptography.hazmat.primitives.ciphers import Cipher, modes  # noqa: E402

ALL_VARIANTS = list(KDF_VARIANTS) + list(EXTENDED_CIPHER_VARIANTS)


def derive_chain_forms(body: bytes, newline_variants: bool = True):
    """Given a just-decrypted SALPH-stage plaintext, derive candidate
    passphrase forms for the COSMIC stage: the whole decoded text (stripped),
    each individual non-empty line (in case the plaintext is an instruction
    that embeds the real next-stage answer on its own line rather than being
    the answer itself, as Phase 3.2's already-solved plaintext does), and any
    substring following a "password"/"answer"/"key" label -- the exact phrasing
    Phase 3.2's real plaintext uses. Every form is then run through
    answer_forms() (case/punctuation normalization) and keystr_forms()
    (raw/sha256/sha256^2, optionally with trailing newline) exactly like every
    other sweep script in this project, so the derived forms use the same
    normalization the rest of the project already validated."""
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = body.decode("latin-1")
    forms = {text.strip()}
    for line in text.splitlines():
        line = line.strip()
        if line:
            forms.add(line)
        m = re.search(r"(?:password|answer|key)\s*[:=]\s*(.+)", line, re.IGNORECASE)
        if m:
            forms.add(m.group(1).strip())
    forms.discard("")
    out = []
    for form in forms:
        for af in answer_forms(form):
            out.extend(keystr_forms(af, newline_variants=newline_variants))
    return list(dict.fromkeys(out))


def chain_salph_to_cosmic(salph_body: bytes, kdf_variants=None):
    """Test every form derived from a SALPH plaintext against COSMIC only.
    Defaults to the union of KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS -- unlike
    a bulk candidate sweep, this runs once per SALPH hit (there can only ever
    be a handful), so there's no cost reason to narrow cipher/KDF coverage."""
    variants = ALL_VARIANTS if kdf_variants is None else kdf_variants
    cosmic_only = {"COSMIC": BLOBS["COSMIC"]}
    hits = []
    for keystr in derive_chain_forms(salph_body):
        result = aes_try_open(keystr, kdf_variants=variants, blobs=cosmic_only)
        if result:
            hits.append((keystr, result))
    return hits


def check_salph_still_unopened():
    """Confirms (rather than assumes) that no candidate in this project's
    curated recheck opens SALPH under any known cipher/KDF combo -- run before
    reporting the chain as dormant, since "SALPH has never been opened" is a
    claim about the sweep history, not an invariant of the code."""
    salph_only = {"SALPH": BLOBS["SALPH"]}
    probes = [b"test", b"password", b""]
    for p in probes:
        result = aes_try_open_bytes(p, kdf_variants=ALL_VARIANTS, blobs=salph_only)
        assert result is None, f"unexpected: trivial probe {p!r} opened SALPH: {result}"
    return True


def _self_test():
    """Synthetic end-to-end validation: builds a fake SALPH plaintext
    containing an embedded 'password:' line, derives forms from it, confirms
    the embedded answer is among them, then builds a fake COSMIC ciphertext
    keyed on the SHA-256 of that exact answer (the "hash its answer" reading)
    under a cipher/KDF combo only available via EXTENDED_CIPHER_VARIANTS
    (3DES-CBC + PBKDF2), and confirms chain_salph_to_cosmic() recovers it
    end-to-end without being told the answer directly."""
    true_answer = "opensesamecosmicdoor"
    salph_plaintext = f"stage complete.\npassword: {true_answer}\ngood luck.".encode()

    forms = derive_chain_forms(salph_plaintext)
    assert true_answer in forms, (
        f"self-test FAILED: embedded answer {true_answer!r} not found in "
        f"derived forms (label-extraction regex broken?)"
    )
    expected_keystr = keystr_forms(true_answer)[1]  # single-SHA256 form
    assert expected_keystr in forms, (
        "self-test FAILED: expected sha256(true_answer) keystring missing "
        "from derived forms"
    )

    salt = b"abcdefgh"
    kdf_kind, kdf_param, cipher, key_len = "pbkdf2", ("sha256", 10000), "3des", 24
    digest_name, iterations = kdf_param
    block = CIPHER_BLOCK_SIZES[cipher]
    key, iv = pbkdf2_bytes_to_key(expected_keystr.encode(), salt, iterations, digest_name, key_len, block)
    fake_cosmic_plaintext = b"the real cosmic duality answer, found via chaining"
    pad_len = block - (len(fake_cosmic_plaintext) % block)
    padded = fake_cosmic_plaintext + bytes([pad_len]) * pad_len
    encryptor = Cipher(CIPHER_CLASSES[cipher](key), modes.CBC(iv)).encryptor()
    fake_cosmic_ct = encryptor.update(padded) + encryptor.finalize()

    import cb_common
    real_blobs_backup = dict(cb_common.BLOBS)
    cb_common.BLOBS["COSMIC"] = (salt, fake_cosmic_ct)
    try:
        hits = chain_salph_to_cosmic(salph_plaintext)
    finally:
        cb_common.BLOBS.clear()
        cb_common.BLOBS.update(real_blobs_backup)

    assert hits, (
        "self-test FAILED: chain_salph_to_cosmic() did not recover the "
        "synthetic COSMIC vector chained from a synthetic SALPH plaintext"
    )
    matched_keystr, (tag, body, kdf_label, returned_key_len) = hits[0]
    assert body == fake_cosmic_plaintext, (
        f"self-test FAILED: chained hit decrypted to wrong content "
        f"(got {body!r}, want {fake_cosmic_plaintext!r})"
    )
    print(f"[*] self-test OK: chained {matched_keystr!r} -> COSMIC hit "
          f"({kdf_label}/{returned_key_len * 8}bit)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check-salph", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        _self_test()
        return
    if args.check_salph:
        check_salph_still_unopened()
        print("[*] SALPH still unopened under KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS "
              "(trivial probes only -- see extended_cipher_recheck.py for the real sweep)")
        print("[*] staged pipeline is dormant: nothing to chain into COSMIC yet")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
