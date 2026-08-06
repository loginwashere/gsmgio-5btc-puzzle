#!/usr/bin/env python3
"""Brainstorm item 7 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md` section 7):
a semantic, not structural, reading of "half and better half".

The brainstorm bullet actually proposed THREE roles for `NEO`/`TRINITY`/the
exact screenplay line: (1) a literal AES passphrase, (2) a KDF salt/context
string, (3) a checkerboard alphabet seed. The first `--oracle` pass in this
file's history only covered (1). `--context` and `--checkerboard` below cover
(2) and (3) so the bullet is actually fully tested, not just its easiest
third.

Phase 78 (`binary_key_material_backfill.py`) already tests the *structural*
reading (a 32|32-byte raw private-key shape inside the 80-byte SALPH/
P32TRAILING ciphertexts) against the full 648-candidate curated corpus,
including bare `NEO`/`TRINITY` (via `matrix_trilogy.txt`) and the literal
clue phrase `halfandbetterhalf` itself (via multiple wordlists) -- all
already exhausted, 0 hits.

What was never tried is a *specific* real screenplay quote where Neo and
Trinity are explicitly framed as counterparts, rather than the bare names.
Searching the real script text (not memory, not paraphrase -- see
`verify_quote()` below, which re-extracts the exact passage from the source
PDF at run time via `pdftotext`) for lines combining "half"/"belong"/
"complete" near NEO/TRINITY finds no literal "other half" line, but does
find something more specific: Trinity's resurrection speech over Neo's body
in the first film literally opens with "I promised to tell you the rest" --
the exact word `promised` is also the final, still-functionally-unused token
of the creator's own eight-item macro clue (brainstorm item 11). That
convergence, not a generic "Neo and Trinity are a couple" association, is
the actual motivation for this candidate family. It is intentionally a small,
quote-derived set, not a dictionary expansion.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import hashlib

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_bytes,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    decode_9ary,
    keystr_forms,
    pad25,
)
from hash_duality_sweep import CORE_CANDIDATES, material_forms, operation_materials  # noqa: E402
from data import DBBI, FAED  # noqa: E402

CLUE_WORDS = (
    "yin", "yang", "matrix", "sum", "list", "seed", "key", "enter",
    "password", "salvation", "neo", "trinity", "promise", "but", "hye",
)

CHECKERBOARD_SEEDS = (
    "NEO",
    "TRINITY",
    "NEOTRINITY",
    "TRINITYNEO",
    "IPROMISEDTOTELLYOUTHEREST",
)

# Established best-fit escape pairs from the project's own prior calibration
# (doc/GSMG_PUZZLE.md, cb_common.py's own module docstring): {b,e} is the
# decisive fit for DBBI; {g,i} is FAED's own best frequency fit, {h,e} its
# tested mirror. No new escape-pair search is introduced here.
DBBI_ESCAPE_PAIRS = (("b", "e"),)
FAED_ESCAPE_PAIRS = (("g", "i"), ("h", "e"))

# Local copy of the working PDF location on this machine -- the repo's own
# `wordlists/matrix/` is not populated in this checkout (same gap as the
# Telegram `_work/` export used by other provenance scripts), but the source
# PDFs used by the project's earlier real-screenplay sweep are still present
# in a sibling project directory.
PDF_PATH = Path(
    "/home/loginwashere/projects/key-seeker/wordlists/matrix/the-matrix-1999.pdf"
)

EXPECTED_QUOTE = (
    "Neo, please, listen to me. I promised to tell you the rest. The "
    "Oracle, she told me that I'd fall in love and that man, the man I "
    "loved would be the one. You see? You can't be dead, Neo, you can't "
    "be because I love you. You hear me? I love you!"
)

FIXED_CANDIDATES = (
    "NEOTRINITY",
    "TRINITYNEO",
    "NEO AND TRINITY",
    "TRINITY AND NEO",
    "I PROMISED TO TELL YOU THE REST",
    "I LOVE YOU",
    "YOU CAN'T BE DEAD",
    "THE MAN I LOVED WOULD BE THE ONE",
    EXPECTED_QUOTE,
)


def extract_pdf_text(path):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return re.sub(r"\s+", " ", completed.stdout)


def verify_quote(path=PDF_PATH):
    normalized_text = extract_pdf_text(path)
    normalized_quote = re.sub(r"\s+", " ", EXPECTED_QUOTE)
    if normalized_quote not in normalized_text:
        raise AssertionError(
            "expected Trinity resurrection quote not found verbatim in the "
            "source screenplay PDF -- do not trust EXPECTED_QUOTE without "
            "fixing this first"
        )
    return True


def oracle_check(candidates, blobs):
    tested_keystrings = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested_keystrings:
                    continue
                tested_keystrings.add(keystring)

                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((candidate, keystring, result))

                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))

                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))

                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((candidate, keystring, result))

    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "hits": hits,
    }


def context_check(candidates, blobs, newline_variants=False):
    """Role 2: NEO/TRINITY/the quote as a KDF salt/context string, not a
    literal passphrase. These blobs are confirmed-genuine OpenSSL `Salted__`
    containers with a fixed embedded salt, so a literal alternate-salt KDF
    call is a guaranteed miss regardless of passphrase (the real ciphertext
    was encrypted under its own actual salt, full stop) -- that framing has
    no real operational form. The literal testable form of "context string"
    is the one `hash_duality_sweep.py` already implements for a different
    context value (the four verified prior command hashes): combine a
    SHA-256 of the candidate with each of a small established set of
    recognized-state answers via concatenation/XOR/HMAC, in both binary and
    hex representations, then test the combined material directly as
    passphrase bytes. Reused directly, not reimplemented."""
    tested = set()
    hits = []
    attempts = 0
    for candidate in candidates:
        previous_hex = hashlib.sha256(candidate.encode()).hexdigest()
        for answer_label, answer in CORE_CANDIDATES.items():
            for operation, material in operation_materials(previous_hex, answer).items():
                for representation, passphrase in material_forms(material, newline_variants):
                    if passphrase in tested:
                        continue
                    tested.add(passphrase)
                    attempts += 1
                    for variants in (None, EXTENDED_CIPHER_VARIANTS):
                        result = aes_try_open_bytes(passphrase, kdf_variants=variants, blobs=blobs)
                        if result:
                            hits.append({
                                "trinity_candidate": candidate,
                                "core_answer": answer_label,
                                "operation": operation,
                                "representation": representation,
                                "passphrase_hex": passphrase.hex(),
                                "result": result,
                            })
    return {"attempts": attempts, "unique_materials": len(tested), "hits": hits}


def checkerboard_check(seeds, blobs):
    """Role 3: NEO/TRINITY/the quote as a keyed checkerboard alphabet seed.
    Confirmed absent from every wordlist this project's existing keyword-
    checkerboard sweeps actually draw from (neither the default
    cypherpunk/bitcoin-historical/Gutenberg wordlists nor the 8,036-candidate
    `session_combined_for_chain.txt` contain bare `neo`/`trinity`), so this
    really is untested territory, unlike the bare-name passphrase role."""
    decodes = {}
    for seed in seeds:
        alphabet25 = pad25(seed)
        for e1, e2 in DBBI_ESCAPE_PAIRS:
            decodes[f"{seed}/dbbi/{e1}{e2}"] = decode_9ary(DBBI, alphabet25, e1, e2)
        for e1, e2 in FAED_ESCAPE_PAIRS:
            decodes[f"{seed}/faed/{e1}{e2}"] = decode_9ary(FAED, alphabet25, e1, e2)

    clue_hits = {
        label: tuple(word for word in CLUE_WORDS if word in value.lower())
        for label, value in decodes.items()
        if any(word in value.lower() for word in CLUE_WORDS)
    }

    hits = []
    for label, value in decodes.items():
        for form in sorted(answer_forms(value)):
            for keystring in keystr_forms(form, newline_variants=True):
                result = aes_try_open(keystring, blobs=blobs)
                if result:
                    hits.append((label, keystring, result))

    return {"decodes": decodes, "clue_hits": clue_hits, "hits": hits}


def print_report(quote_verified, result=None, context_result=None, board_result=None):
    print(f"[*] Trinity resurrection quote verified against source PDF: {quote_verified}")
    print(f"[*] fixed candidate family ({len(FIXED_CANDIDATES)}):")
    for candidate in FIXED_CANDIDATES:
        print(f"    {candidate!r}")
    if result is not None:
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] role 1 (literal passphrase) oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")
    if context_result is not None:
        print(
            f"[*] role 2 (KDF salt/context) check: attempts={context_result['attempts']} "
            f"unique_materials={context_result['unique_materials']} "
            f"hits={len(context_result['hits'])}"
        )
        for hit in context_result["hits"]:
            print(f"    {hit!r}")
    if board_result is not None:
        print(f"[*] role 3 (checkerboard seed) decodes: {len(board_result['decodes'])}")
        print("    clue hits:")
        if board_result["clue_hits"]:
            for label, words in board_result["clue_hits"].items():
                print(f"      {label}: {words} <- {board_result['decodes'][label]!r}")
        else:
            print("      none")
        print(f"    oracle hits: {len(board_result['hits'])}")
        for hit in board_result["hits"]:
            print(f"      {hit!r}")


def self_test():
    assert verify_quote()
    assert len(FIXED_CANDIDATES) == 9
    assert "PROMISED" in EXPECTED_QUOTE.upper()
    assert set("NEO") <= set("abcdefghijklmnopqrstuvwxyz".upper())
    print("[*] self-test OK: quote verified verbatim against source PDF")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=PDF_PATH)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--context", action="store_true")
    parser.add_argument("--checkerboard", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    quote_verified = verify_quote(args.pdf)

    blobs = dict(BLOBS)
    if args.include_quarantined:
        blobs.update(QUARANTINED_BLOBS)

    result = oracle_check(FIXED_CANDIDATES, blobs) if args.oracle else None
    context_result = context_check(FIXED_CANDIDATES, blobs) if args.context else None
    board_result = checkerboard_check(CHECKERBOARD_SEEDS, blobs) if args.checkerboard else None

    print_report(quote_verified, result, context_result, board_result)


if __name__ == "__main__":
    main()
