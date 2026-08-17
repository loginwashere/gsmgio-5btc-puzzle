#!/usr/bin/env python3
"""Candidate family -- full Phase 3.2.1 plaintext read in reverse (2026-08-15).

Executes the idea from
doc/Brainstorms/2026-08-15 - Phase 3 Part 5-6 Riddle Close Read.md's "Open
item" section: the authenticated Phase 3.2.1 plaintext ends `CIAO BELLA O`,
whose word order community solvers have long read as `O BELLA CIAO` ("oh
beautiful, goodbye") -- see doc/GSMG_BYE_CIAO_PROVENANCE_AUDIT.md. That
local, 3-word reversal has never been extended to the full message. This
project's own history shows the "read the whole stream in reverse" trick is
a real, previously-used mechanism here (FINDINGS.md Phase 7's 2023-02-23
binary message was only crackable reversed as one unit before rechunking),
so this is disclosed-artifact-plus-precedented-operation, not a new
interpretation invented from nothing.

The exact 331-word block is extracted mechanically from README.md between
the same two anchors `p32_sibling_password_audit.py.readme_architect_letters()`
already uses (`YOUR LIFE IS THE SUM OF A REMAINDER` .. `HOPE YOURE THE ONE
CIAO BELLA O`), so there is no transcription risk.

Because "the word split is arbitrary" (raised directly), this builds
multiple independent reversal variants rather than picking one:

  1. full_char_reverse -- reverse the entire normalized string character by
     character (whitespace collapsed to single spaces first). No word-
     boundary assumption at all -- the least interpretive form.
  2. word_reverse_spaced / word_reverse_nospace -- split on whitespace,
     reverse word order, re-join with single spaces or no separator. This is
     the direct extension of the tail's own `CIAO BELLA O -> O BELLA CIAO`
     pattern (word reorder, each word still spelled forward) to the full
     message.
  3. line_reverse -- reverse the order of the ~10 newline-delimited lines
     the README displays the speech in, keeping each line's word order
     intact. A different, equally arbitrary tokenization, included because
     the prompt explicitly flagged word-splitting as arbitrary.

`answer_forms()` is applied to each (giving raw/upper/lower and their
letters-only equivalents -- reversal commutes with the letters-only strip,
so this also covers the "reversed letters only" reading for free) and
`keystr_forms()` adds raw/sha256/double-sha256, matching this project's
standard candidate-form convention. Tested against all four tracked blobs
under the standard CBC oracle only, matching the same bounded discipline as
p32_family10_fork_leads_audit.py.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent

from cb_common import BLOBS, aes_try_open_bytes, answer_forms, keystr_forms  # noqa: E402

README_PATH = REPO_ROOT / "README.md"
START_MARKER = "YOUR LIFE IS THE SUM OF A REMAINDER"
END_MARKER = "HOPE YOURE THE ONE CIAO BELLA O"


def extract_plaintext(path=README_PATH):
    text = path.read_text(encoding="utf-8")
    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start)
    return text[start:end + len(END_MARKER)]


def build_variants(raw_block):
    normalized = re.sub(r"\s+", " ", raw_block).strip()
    words = normalized.split(" ")
    lines = [line.strip() for line in raw_block.splitlines() if line.strip()]

    full_char_reverse = normalized[::-1]
    word_reverse_spaced = " ".join(reversed(words))
    word_reverse_nospace = "".join(reversed(words))
    line_reverse = " ".join(reversed(lines))

    return {
        "forward_normalized": normalized,
        "full_char_reverse": full_char_reverse,
        "word_reverse_spaced": word_reverse_spaced,
        "word_reverse_nospace": word_reverse_nospace,
        "line_reverse": line_reverse,
    }


def all_candidate_strings():
    raw_block = extract_plaintext()
    variants = build_variants(raw_block)
    candidates = {}
    for label, text in variants.items():
        if label == "forward_normalized":
            continue  # already-known plaintext, not a new candidate
        candidates[label] = sorted(answer_forms(text))
    return raw_block, variants, candidates


def run():
    _, _, candidates = all_candidate_strings()
    attempts = []
    hits = []
    for label, forms in candidates.items():
        for form in forms:
            for keystr in keystr_forms(form):
                result = aes_try_open_bytes(keystr.encode())
                attempts.append({"label": label, "form": form, "keystr": keystr})
                if result:
                    tag, body, kdf_label, key_len = result
                    hits.append({
                        "label": label,
                        "form": form,
                        "keystr": keystr,
                        "blob": tag,
                        "kdf": f"{kdf_label}/aes{key_len * 8}",
                        "plaintext_hex": body.hex(),
                    })
    return {
        "candidate_labels": list(candidates.keys()),
        "candidate_string_count": sum(len(v) for v in candidates.values()),
        "passphrase_attempts": len(attempts),
        "blobs": tuple(BLOBS),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    raw_block = extract_plaintext()
    assert raw_block.startswith(START_MARKER)
    assert raw_block.endswith(END_MARKER)
    variants = build_variants(raw_block)
    words = variants["forward_normalized"].split(" ")
    assert len(words) >= 300, f"unexpectedly short extraction: {len(words)} words"
    assert variants["full_char_reverse"][::-1] == variants["forward_normalized"]
    assert variants["word_reverse_spaced"].split(" ")[0] == words[-1]
    assert variants["word_reverse_spaced"].split(" ")[-1] == words[0]
    # The tail's own known community reversal must reproduce exactly from the
    # real extracted text, confirming the word-split convention matches the
    # already-established CIAO BELLA O -> O BELLA CIAO pattern.
    assert variants["word_reverse_spaced"].startswith("O BELLA CIAO")
    print(f"[*] self-test OK: {len(words)}-word block extracted; "
          f"full_char_reverse round-trips; word_reverse_spaced starts "
          f"'O BELLA CIAO' matching the known tail pattern")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show", action="store_true", help="print the extracted text and all reversal variants")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.show:
        raw_block, variants, _ = all_candidate_strings()
        print("=== forward (extracted from README.md) ===")
        print(raw_block)
        print()
        for label in ("full_char_reverse", "word_reverse_spaced", "word_reverse_nospace", "line_reverse"):
            print(f"=== {label} ===")
            print(variants[label])
            print()
        return
    if not args.run:
        parser.print_help()
        return
    report = run()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
