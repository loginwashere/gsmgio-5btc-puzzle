#!/usr/bin/env python3
"""Path 1 from the 2026-07-24 "Best Remaining Paths" review: recheck this
project's already-curated candidate lists against the newly broadened AES
oracle (cb_common.EXTENDED_CIPHER_VARIANTS -- AES-192-CBC, 3DES-CBC at all
three key sizes, and PBKDF2-HMAC-SHA256 at OpenSSL's default 10000
iterations), before spending any compute on new candidate generation.

The premise: `Salted__` identifies the OpenSSL container, not which
cipher/KDF produced it. Every prior sweep in this project (dozens, per
FINDINGS.md) only ever tested AES-128/256-CBC with the legacy MD5/SHA1/SHA256
EVP_BytesToKey derivation. If SALPH or COSMIC used a different cipher or
PBKDF2, a correct passphrase would have silently failed every single one of
those sweeps -- indistinguishable from a wrong passphrase.

Deliberately bounded to CURATED sources only (small, already-distilled
candidate lists this project has produced over time -- not the raw multi-
megabyte mined corpora like chat_mined_lines.txt or matrix_script_windows.txt,
which would turn a cheap recheck into an expensive new sweep and defeats the
point of doing this FIRST). If nothing turns up here, the next step is
deciding whether to extend coverage to a bigger source, not assumed here.

Follow-up (2026-07-24): cb_common.BLOBS gained a third target, "P32TRAILING"
(see data.P32_TRAILING_BLOB_B64) -- confirmed real GSMG provenance via
independent path-3 chat-archive triage. This module automatically sweeps
against it too, no changes needed here beyond this note.

Usage:
    python3 tools/gsmg/extended_cipher_recheck.py
    python3 tools/gsmg/extended_cipher_recheck.py --self-test
"""
import argparse
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_try_open,
    answer_forms,
    keystr_forms,
)
from data import VALIDATION_ANSWER  # noqa: E402
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS  # noqa: E402
from staged_pipeline import chain_salph_to_cosmic  # noqa: E402

WORDLIST_DIR = Path(__file__).resolve().parent.parent.parent / "wordlists" / "gsmg"

# Small, already-distilled candidate lists -- each the product of an earlier
# targeted investigation in this project (mnemonic phrases, riddle-derived
# fragments, architect/oracle wordplay, discovered URL paths, etc.), NOT the
# raw mined corpora. See the module docstring for why that boundary matters.
CURATED_FILES = [
    "last_command.txt",
    "salphaseion_own_keywords_combined.txt",
    "single_fragments.txt",
    "other_half_candidates.txt",
    "three_sexes_candidates.txt",
    "hegel_marx_candidates.txt",
    "original_riddle_candidates.txt",
    "discovered_paths.txt",
    "yellowblueprime_matrixsumlist_variants.txt",
    "phrases.txt",
    "phrases-joined.txt",
    "riddle_combinations.txt",
    "yinyang_matrix_symbolism.txt",
    "architect_coded.txt",
    "architect_gnostic_synonyms.txt",
    "architect_wiki_deepdive.txt",
    "oracle_coded.txt",
    "matrix_trilogy.txt",
    "blockchain_metadata_candidates.txt",
    "first_piece_color_candidates.txt",
    "matrixsumlist_choice_candidates.txt",
    "fefe_plated_seed_candidates.txt",
    "full_macro_clue_chain_candidates.txt",
]


def load_curated_candidates():
    """Every non-empty, non-comment line from CURATED_FILES, plus the small
    in-code seed lists (CORE_ALPHABET_SEEDS, VALIDATION_ANSWER) already used
    elsewhere in this project as high-confidence keyword/passphrase material."""
    seen = set()
    candidates = []

    def add(line):
        line = line.strip()
        if not line or line.startswith("#") or line in seen:
            return
        seen.add(line)
        candidates.append(line)

    for name in CURATED_FILES:
        path = WORDLIST_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"expected curated wordlist missing: {path}")
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                add(line)
    for seed in CORE_ALPHABET_SEEDS:
        add(seed)
    add(VALIDATION_ANSWER)
    return candidates


def candidate_list_digest(candidates):
    """SHA-256 of the exact ordered candidate list, so a sweep's console
    output records precisely which candidate set produced a given result --
    CURATED_FILES is a mutable, growing corpus (e.g. blockchain_metadata_
    candidates.txt joined it 2026-07-24), so "N candidates" alone doesn't
    pin down which N. Order-sensitive on purpose: a silent reordering could
    hide a duplicate/drop that a plain sorted-set hash would miss."""
    return hashlib.sha256("\n".join(candidates).encode()).hexdigest()[:16]


def sweep(candidates, newline_variants=True, blobs=None):
    """Every candidate line, through answer_forms() x keystr_forms() x
    EXTENDED_CIPHER_VARIANTS, against `blobs` (aes_try_open's BLOBS default,
    unless the caller opts a quarantined target in -- see
    cb_common.QUARANTINED_BLOBS). Returns (attempts, hits)."""
    attempts = 0
    hits = []
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=newline_variants):
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
    ap.add_argument("--self-test", action="store_true",
                     help="verify candidate loading + sweep plumbing, then exit")
    ap.add_argument("--include-quarantined", action="store_true",
                     help="also sweep cb_common.QUARANTINED_BLOBS (e.g. urlblob) "
                          "-- opt-in since their puzzle provenance is weaker than "
                          "the default BLOBS")
    args = ap.parse_args()

    candidates = load_curated_candidates()
    print(f"[*] loaded {len(candidates)} curated candidates from "
          f"{len(CURATED_FILES)} files + seed lists")
    print(f"[*] candidate-list digest: {candidate_list_digest(candidates)}")

    blobs = {**BLOBS, **QUARANTINED_BLOBS} if args.include_quarantined else None
    active_blobs = blobs if blobs is not None else BLOBS

    if args.self_test:
        assert len(candidates) > 500, (
            f"self-test FAILED: expected >500 curated candidates, got {len(candidates)} "
            f"-- a wordlist file is probably missing or empty"
        )
        assert "salphaseion" in candidates, (
            "self-test FAILED: expected seed candidate 'salphaseion' not found"
        )
        attempts, hits = sweep(candidates[:5], newline_variants=False, blobs=blobs)
        assert attempts > 0, "self-test FAILED: sweep() produced zero attempts"
        print(f"[*] self-test OK ({attempts} attempts on 5 candidates, "
              f"{len(hits)} hits)")
        return

    attempts, hits = sweep(candidates, blobs=blobs)
    print(f"[*] {attempts:,} attempts across {len(EXTENDED_CIPHER_VARIANTS)} "
          f"extended cipher/KDF variants x {len(active_blobs)} blobs "
          f"({', '.join(active_blobs)})")
    if not hits:
        print("[*] no candidate opened any blob under any extended cipher/KDF variant")
        return
    for hit in hits:
        print(f"\n[+++ HIT] candidate={hit['candidate']!r} blob={hit['blob']} "
              f"kdf={hit['kdf']}/{hit['key_bits']}bit")
        print(f"    plaintext: {hit['plaintext']!r}")
        if hit["blob"] == "SALPH":
            # Path 2: automatically chain a SALPH hit into a COSMIC attempt
            # rather than requiring a human to notice and manually re-run --
            # see staged_pipeline.py.
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
