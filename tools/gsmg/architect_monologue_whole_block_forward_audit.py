#!/usr/bin/env python3
"""Candidate family -- full Phase 3.2.1 Architect monologue, forward, as one
unbroken block (2026-08-16).

Closes a specific, concrete gap left open by two prior audits of this same
331-word passage, neither of which actually tested it whole:

  - Phase 267 (`phase3_chain_full_text_p32_sweep_audit.py`) deliberately
    split this exact block into 18 separate line-based candidates. Its own
    write-up says a punctuation split "would have silently collapsed the
    entire ~1,000-word block ... into one candidate" and that this was
    treated as a bug to fix, not a candidate to keep -- so the single whole-
    block reading was actively avoided, not tested.
  - Phase 295 (`phase321_full_text_reversal_audit.py`) extracts this same
    block with the same two anchors, but only submits *reversed* forms
    (`full_char_reverse`, `word_reverse_spaced`, `word_reverse_nospace`,
    `line_reverse`) as candidates. Its own code explicitly labels the
    forward, un-reversed reading `"already-known plaintext, not a new
    candidate"` and skips it.

So the plain, forward, single-string reading of this whole disclosed and
authenticated passage -- no split, no reversal -- has never actually been
run through the standard oracle. Motivation: every other genuinely new
open thread on this passage has already been exhausted this session
(personalization-substitution pattern is pre-existing/documented, not new;
residual vocabulary tested in Phase 265; every sentence tested in Phase
267; every reversal tested in Phase 295) -- this is the one concrete,
disclosed, zero-interpretation reading left.

The exact block is extracted mechanically from README.md between the same
two anchors already used by `p32_sibling_password_audit.py`'s
`readme_architect_letters()` and `phase321_full_text_reversal_audit.py`
(`YOUR LIFE IS THE SUM OF A REMAINDER` .. `HOPE YOURE THE ONE CIAO BELLA
O`), so there is no fresh transcription risk.

One candidate family: the forward block, whitespace-normalized, run through
`answer_forms()` (raw / upper / lower / letters-only alpha variants -- the
same convention Phase 295 used) and `keystr_forms()` (raw / SHA-256 /
double-SHA-256). Tested against all four tracked blobs under the standard
CBC oracle, matching Phase 295's own bounded scope exactly (not the wider
stream/ECB/keywrap oracle, so this is a direct, apples-to-apples extension
of that closed phase, not a new, broader hypothesis).
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
    return text[start : end + len(END_MARKER)]


def forward_block(raw_block=None):
    raw_block = extract_plaintext() if raw_block is None else raw_block
    return re.sub(r"\s+", " ", raw_block).strip()


def all_candidate_strings():
    normalized = forward_block()
    return normalized, sorted(answer_forms(normalized))


def run():
    _, candidates = all_candidate_strings()
    attempts = []
    hits = []
    for form in candidates:
        for keystr in keystr_forms(form):
            result = aes_try_open_bytes(keystr.encode())
            attempts.append({"form": form, "keystr": keystr})
            if result:
                tag, body, kdf_label, key_len = result
                hits.append({
                    "form": form,
                    "keystr": keystr,
                    "blob": tag,
                    "kdf": f"{kdf_label}/aes{key_len * 8}",
                    "plaintext_hex": body.hex(),
                })
    return {
        "candidate_string_count": len(candidates),
        "passphrase_attempts": len(attempts),
        "blobs": tuple(BLOBS),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    raw_block = extract_plaintext()
    assert raw_block.startswith(START_MARKER)
    assert raw_block.endswith(END_MARKER)
    normalized, candidates = all_candidate_strings()
    words = normalized.split(" ")
    assert len(words) >= 300, f"unexpectedly short extraction: {len(words)} words"
    assert normalized in candidates, "raw forward form must be one of the candidates"
    assert normalized.upper() in candidates
    assert normalized.startswith("YOUR LIFE IS THE SUM")
    assert normalized.endswith("CIAO BELLA O")
    # matches Phase 295's own word count for the identical extraction, confirming
    # this is the same block, just read forward instead of reversed
    assert len(words) == 331, f"expected 331 words matching Phase 295, got {len(words)}"
    attempts = sum(len(keystr_forms(form)) for form in candidates)
    print(f"[*] self-test OK: {len(words)}-word forward block extracted, "
          f"{len(candidates)} candidate forms, {attempts} passphrase attempts")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.show:
        normalized, candidates = all_candidate_strings()
        print("=== forward normalized block ===")
        print(normalized)
        print()
        print("=== candidate forms ===")
        for form in candidates:
            print(form)
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
