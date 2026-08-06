#!/usr/bin/env python3
"""Bounded exact-phrase oracle check for Jacque Fresco's broader body of
work against the still-unsolved SALPH/COSMIC/P32TRAILING/URLBLOB blobs.

Fresco is CONFIRMED relevant to this puzzle -- "jacquefresco" is one of the
three normalized clue answers concatenated into the verified Phase 3.2 AES
password (data.py `VERIFIED_PRIOR_COMMAND_HASHES["phase32_clues"]`) -- but
that is a solved, already-consumed artifact for a different, earlier stage.
`wordlists/gsmg/jacque_fresco_candidates.txt` extends the existing (and
similarly unconfirmed) `looking_forward_candidates.txt` lead to Fresco's
other books, documentaries, and coined terms/quotes, each sourced and cited
in that file's own comments. Nothing here is creator-confirmed as relevant
to the endgame; this is bounded exploratory coverage, matching the pattern
`yin_yang_transition_audit.py --oracle` already established for the
Looking Forward lead -- kept as a separate file and a separate check rather
than folded into `extended_cipher_recheck.CURATED_FILES`, the same way
looking_forward_candidates.txt itself was kept out of that curated corpus.

Unlike the Looking Forward check (CBC + Key Wrap only), this also covers
AES-ECB and the CFB/OFB/CTR stream modes -- both added to this project
after that check was last run, so giving this newer, broader Fresco lead
the same full coverage the 648-candidate curated corpus already gets is
free (a few hundred candidates x a handful of forms x variants is seconds
of compute, not hours). Also matches the main curated sweeps' newline-
variant coverage (`keystr_forms(..., newline_variants=True)`) -- the first
version of this script left that at its default False, caught on review."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cb_common import (
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)

DEFAULT_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "wordlists" / "gsmg" / "jacque_fresco_candidates.txt"
)


def load_candidates(path):
    seen = set()
    candidates = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line in seen:
            continue
        seen.add(line)
        candidates.append(line)
    return candidates


def run_oracle(candidates, blobs):
    tested_keystrings = set()
    cbc_hits = []
    ecb_hits = []
    stream_hits = []
    keywrap_hits = []

    for candidate in candidates:
        for answer in sorted(answer_forms(candidate)):
            # newline_variants=True to match the main curated-corpus sweeps
            # (legacy_cbc_backfill.py, stream_mode_cipher_sweep.py,
            # binary_key_material_backfill.py, extended_cipher_recheck.py's
            # default) -- the first version of this script left it at the
            # default False, giving this lead less coverage than the main
            # corpus gets, caught on review.
            for keystr in keystr_forms(answer, newline_variants=True):
                if keystr in tested_keystrings:
                    continue
                tested_keystrings.add(keystr)

                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystr, kdf_variants=variants, blobs=blobs)
                    if result:
                        cbc_hits.append((candidate, keystr, variants, result))

                result = aes_try_open_ecb(keystr, blobs=blobs)
                if result:
                    ecb_hits.append((candidate, keystr, result))

                result = aes_try_open_stream(keystr, blobs=blobs)
                if result:
                    stream_hits.append((candidate, keystr, result))

                for result in aes_keywrap_try_open_bytes(keystr.encode(), blobs=blobs):
                    keywrap_hits.append((candidate, keystr, result))

    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "cbc_hits": cbc_hits,
        "ecb_hits": ecb_hits,
        "stream_hits": stream_hits,
        "keywrap_hits": keywrap_hits,
    }


def print_report(result):
    print(
        f"[*] candidates={result['candidate_count']} "
        f"unique_keystrings={result['unique_keystrings']} "
        f"blobs={result['blob_count']}"
    )
    print(
        f"[*] CBC hits={len(result['cbc_hits'])} "
        f"ECB hits={len(result['ecb_hits'])} "
        f"stream hits={len(result['stream_hits'])} "
        f"Key-Wrap hits={len(result['keywrap_hits'])}"
    )
    for label, hits in (
        ("CBC", result["cbc_hits"]),
        ("ECB", result["ecb_hits"]),
        ("stream", result["stream_hits"]),
        ("Key-Wrap", result["keywrap_hits"]),
    ):
        for hit in hits:
            print(f"[+++ {label} HIT] {hit}")


def self_test():
    import hashlib
    import tempfile

    import cb_common
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    # 1) Loader: comments, blank lines, and exact-duplicate lines are all
    # skipped; order and content of the remaining lines is preserved.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "candidates.txt"
        path.write_text(
            "# a comment\n\nJacque Fresco\n\n# another comment\nJacque Fresco\nresource-based economy\n"
        )
        loaded = load_candidates(path)
        assert loaded == ["Jacque Fresco", "resource-based economy"], loaded

    # 2) Wiring: one positive control per oracle path (CBC legacy, ECB,
    # stream, Key Wrap), each built by encrypting a real candidate's derived
    # keystring against a synthetic blob under a known variant, then
    # confirming run_oracle actually finds it -- proves the four oracle
    # calls are wired with the right arguments, not just importable.
    # cb_common's own self-tests (run at import time) already validate the
    # underlying primitives; this only checks this script's own plumbing.
    candidate = "Jacque Fresco"
    keystr = sorted(answer_forms(candidate))[0]
    passwd = keystr_forms(keystr)[0].encode()
    salt = b"01234567"

    # CBC (legacy sha256/AES-256, the first default KDF_VARIANTS entry).
    key, iv = cb_common.evp_bytes_to_key(passwd, salt, "sha256", 32, 16)
    plaintext = b"synthetic plaintext for self-test only, not a real hit."
    pad = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad]) * pad
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    cbc_ct = encryptor.update(padded) + encryptor.finalize()
    cbc_blobs = {"SYNTH_CBC": (salt, cbc_ct)}
    result = run_oracle([candidate], cbc_blobs)
    assert len(result["cbc_hits"]) == 1, result["cbc_hits"]
    assert result["cbc_hits"][0][3][1] == plaintext

    # ECB (legacy sha256/AES-256, the first default ECB_CIPHER_VARIANTS entry).
    ecb_key, _ = cb_common.evp_bytes_to_key(passwd, salt, "sha256", 32, 0)
    ecb_encryptor = Cipher(algorithms.AES(ecb_key), modes.ECB()).encryptor()
    ecb_ct = ecb_encryptor.update(padded) + ecb_encryptor.finalize()
    ecb_blobs = {"SYNTH_ECB": (salt, ecb_ct)}
    result = run_oracle([candidate], ecb_blobs)
    assert len(result["ecb_hits"]) == 1, result["ecb_hits"]
    assert result["ecb_hits"][0][2][1] == plaintext

    # Stream (legacy sha256/AES-256/CFB, the first default STREAM_CIPHER_
    # VARIANTS entry).
    stream_key, stream_iv = cb_common.evp_bytes_to_key(passwd, salt, "sha256", 32, 16)
    stream_encryptor = Cipher(algorithms.AES(stream_key), modes.CFB(stream_iv)).encryptor()
    stream_ct = stream_encryptor.update(plaintext) + stream_encryptor.finalize()
    stream_blobs = {"SYNTH_STREAM": (salt, stream_ct)}
    result = run_oracle([candidate], stream_blobs)
    assert len(result["stream_hits"]) == 1, result["stream_hits"]
    assert result["stream_hits"][0][2][1] == plaintext

    # Key Wrap: real round trip via cb_common's own wrap/derive helpers,
    # rather than reimplementing RFC 3394 here.
    kek, wrap_iv = cb_common.derive_wrap_material("legacy", "sha256", salt, passwd, 32, 8)
    wrapped = cb_common.aes_key_wrap(kek, plaintext[:32])
    keywrap_blobs = {"SYNTH_WRAP": (salt, wrapped)}
    result = run_oracle([candidate], keywrap_blobs)
    assert len(result["keywrap_hits"]) == 1, result["keywrap_hits"]
    assert result["keywrap_hits"][0][2][4] == plaintext[:32]

    # 3) Negative control: an unrelated candidate against real ciphertext-
    # shaped bytes must not produce a hit anywhere. Deterministic (not
    # os.urandom, for reproducibility) but NOT a repeated block: under ECB,
    # repeating a single 32-byte block 5x (an earlier version of this test)
    # collapses to only 32 bytes of real randomness, then repeats whatever
    # printable-looking coincidence occurs in it 5x -- inflating the z-score
    # fivefold over what that same randomness would score unrepeated (this
    # is exactly what happened: it landed at z=8.02, just over the z>=8.0
    # strong threshold, caught by this assertion failing on review). A hash
    # chain avoids that pseudo-replication by construction.
    filler = b""
    block = b"jacque-fresco-negative-control-seed"
    while len(filler) < 160:
        block = hashlib.sha256(block).digest()
        filler += block
    filler = filler[:160]
    random_blobs = {"SYNTH_NEG": (salt, filler)}
    result = run_oracle(["not a real candidate at all"], random_blobs)
    assert not result["cbc_hits"] and not result["ecb_hits"]
    assert not result["stream_hits"] and not result["keywrap_hits"]

    print(
        "[*] self-test OK: candidate loader (comments/blanks/dedup), "
        "CBC/ECB/stream/Key-Wrap oracle wiring each verified via a real "
        "encrypt-then-find round trip, negative control"
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.self_test:
        self_test()
        return
    candidates = load_candidates(args.candidates)
    blobs = {**BLOBS, **QUARANTINED_BLOBS}
    result = run_oracle(candidates, blobs)
    print_report(result)


if __name__ == "__main__":
    main()
