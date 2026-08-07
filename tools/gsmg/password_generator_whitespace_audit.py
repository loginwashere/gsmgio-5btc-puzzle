#!/usr/bin/env python3
"""Closes the trailing-whitespace gap surfaced by identifying the creator's
own recommended hash-checking tool.

Telegram message 234 (creator-only export, 2019-04-23) is the creator
replying to "how to check a password with a hash?" -- asked in the context of
verifying the phase-1 password -- with a direct link:

    https://passwordsgenerator.net/sha256-hash-generator/

This is their own recommended method for the exact operation this project's
AES oracle performs (candidate -> SHA-256 -> compare/decrypt), not an
incidental URL. The domain no longer resolves (SERVFAIL as of 2026-08-07),
but Wayback has a capture from 2019-04-25, two days after the message. Its
client-side `calc()` function:

    if( strTxt.search("\\r")>0 ) strTxt = replaceAll("\\r", "", strTxt);
    var strHash = hex_sha256( strTxt );
    strHash = strHash.toUpperCase();

strips a literal "\\r" and does nothing else -- no leading/trailing
whitespace trim of any kind. `cb_common.keystr_forms`'s existing
`newline_variants` flag already covers the "\\n"/"\\r\\n" family (the
"pressed Enter" reading), but nothing before this covered a bare trailing
space, which this tool's source shows would silently survive into the hash.

This is Path 1 discipline (same as `extended_cipher_recheck.py`, which this
script deliberately mirrors): recheck the small, already-curated candidate
lists under the new coverage before spending any compute on the much larger
raw mined corpora. See FINDINGS.md Phase 163 for the full writeup and this
run's result.

Usage:
    python3 tools/gsmg/password_generator_whitespace_audit.py
    python3 tools/gsmg/password_generator_whitespace_audit.py --self-test
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    aes_try_open,
    answer_forms,
    keystr_forms,
)
from extended_cipher_recheck import (  # noqa: E402
    candidate_list_digest,
    load_curated_candidates,
)
from staged_pipeline import chain_salph_to_cosmic  # noqa: E402


def sweep(candidates, blobs=None):
    """Every candidate line, through answer_forms() x keystr_forms(newline_
    variants=True, whitespace_variants=True) x EXTENDED_CIPHER_VARIANTS,
    against `blobs`. Combines both flags in one pass rather than splitting
    into separate runs: the added cost over the existing newline_variants-only
    baseline is one extra keystr_forms base (trailing space), not a
    multiplicative blow-up. Returns (attempts, hits)."""
    attempts = 0
    hits = []
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=True, whitespace_variants=True):
                attempts += 1
                result = aes_try_open(keystr, kdf_variants=EXTENDED_CIPHER_VARIANTS, blobs=blobs)
                if result:
                    tag, body, kdf_label, key_len = result
                    hits.append({
                        "candidate": candidate,
                        "form": form,
                        "keystr": keystr,
                        "blob": tag,
                        "kdf": kdf_label,
                        "key_bits": key_len * 8,
                        "plaintext": body[:500],
                    })
    return attempts, hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    candidates = load_curated_candidates()
    print(f"[*] loaded {len(candidates)} curated candidates")
    print(f"[*] candidate-list digest: {candidate_list_digest(candidates)}")

    if args.self_test:
        assert len(candidates) > 500, "self-test FAILED: curated candidate list too small"
        attempts, hits = sweep(candidates[:5])
        assert attempts > 0, "self-test FAILED: sweep() produced zero attempts"
        print(f"[*] self-test OK ({attempts} attempts on 5 candidates, {len(hits)} hits)")
        return

    attempts, hits = sweep(candidates)
    print(f"[*] {attempts:,} attempts across {len(EXTENDED_CIPHER_VARIANTS)} "
          f"extended cipher/KDF variants x {len(BLOBS)} blobs ({', '.join(BLOBS)}), "
          f"newline_variants=True, whitespace_variants=True")
    if not hits:
        print("[*] no candidate opened any blob under any whitespace/newline form")
        return
    for hit in hits:
        print(f"\n[+++ HIT] candidate={hit['candidate']!r} blob={hit['blob']} "
              f"kdf={hit['kdf']}/{hit['key_bits']}bit")
        print(f"    plaintext: {hit['plaintext']!r}")
        if hit["blob"] == "SALPH":
            print("    [*] SALPH hit -- auto-chaining derived forms into COSMIC...")
            chained = chain_salph_to_cosmic(hit["plaintext"])
            if not chained:
                print("    [*] no chained form opened COSMIC")
            for keystr, (tag, body, kdf_label, key_len) in chained:
                print(f"    [+++ CHAINED HIT] via {keystr!r} -> {tag} "
                      f"({kdf_label}/{key_len * 8}bit)")
                print(f"        plaintext: {body[:500]!r}")


if __name__ == "__main__":
    main()
