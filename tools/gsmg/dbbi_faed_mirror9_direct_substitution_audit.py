#!/usr/bin/env python3
"""Candidate family -- mirror9 direct substitution on full DBBI/FAED (2026-08-15).

Executes idea 3 from
doc/Brainstorms/2026-08-15 - DBBI FAED FEFE Fresh Divergence.md, against the
FULL raw streams (idea 1's "remainder" framing was checked first and found
unexecutable -- see that doc's corrected idea 1 entry -- so this runs
against all of DBBI/FAED, not a hypothetical partial selection).

`mirror9` (a<->i, b<->h, c<->g, d<->f, e fixed) is not invented for this
audit: it is the exact involution already authenticated elsewhere in this
project on this same a-i alphabet, the operation that turned `HYE` into
`BYE` in the solved Architect-choice chain. Applying it as a plain
substitution cipher directly to the raw DBBI/FAED text -- rather than as
part of heavier GF(9) arithmetic (already closed, Phase 276) -- has not been
tried by the 16-model DBBI/FAED campaign (Phases 274-289).

Small, disclosed, bounded transform family: three independent binary toggles
(mirror9 on/off, reverse on/off, halfswap on/off) = 8 combinations per
stream. `halfswap` swaps the string's first and second halves (the same
"yin/yang halves" swap used elsewhere in this project's book-transform
sweep), matching the duality theme rather than an arbitrarily invented cut.
`answer_forms()` + `keystr_forms()` are applied per this project's standard
candidate-form convention; tested against all four tracked blobs under the
standard CBC oracle only.
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent

from cb_common import BLOBS, aes_try_open_bytes, answer_forms, keystr_forms  # noqa: E402
from data import DBBI, FAED  # noqa: E402

NINE_SYMBOLS = "abcdefghi"


def mirror9(text):
    return "".join(NINE_SYMBOLS[-NINE_SYMBOLS.index(c) - 1] for c in text)


def halfswap(text):
    mid = len(text) // 2
    return text[mid:] + text[:mid]


def transform_variants(text):
    variants = {}
    for use_mirror, use_reverse, use_halfswap in itertools.product([False, True], repeat=3):
        label_parts = []
        out = text
        if use_mirror:
            out = mirror9(out)
            label_parts.append("mirror9")
        if use_reverse:
            out = out[::-1]
            label_parts.append("reverse")
        if use_halfswap:
            out = halfswap(out)
            label_parts.append("halfswap")
        label = "+".join(label_parts) if label_parts else "identity"
        variants[label] = out
    return variants


def all_candidate_strings():
    candidates = {}
    for stream_name, stream in (("dbbi", DBBI), ("faed", FAED)):
        for label, text in transform_variants(stream).items():
            candidates[f"{stream_name}/{label}"] = sorted(answer_forms(text))
    return candidates


def run():
    candidates = all_candidate_strings()
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
    assert mirror9("a") == "i"
    assert mirror9("e") == "e"
    assert mirror9("bhcgdf") == "hbgcfd"
    assert mirror9(mirror9(DBBI)) == DBBI, "mirror9 must be an involution"
    assert halfswap("abcd") == "cdab"
    assert halfswap("abcde") == "cdeab"  # mid=2 -> text[2:]+text[:2]
    candidates = all_candidate_strings()
    assert len(candidates) == 16, f"expected 16 labels (8 transforms x 2 streams), got {len(candidates)}"
    for label, forms in candidates.items():
        assert forms, f"{label} produced no candidate forms"
    print(f"[*] self-test OK: mirror9 involution verified, halfswap verified, "
          f"{len(candidates)} labels, {sum(len(v) for v in candidates.values())} total candidate strings")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.show:
        for stream_name, stream in (("dbbi", DBBI), ("faed", FAED)):
            for label, text in transform_variants(stream).items():
                print(f"{stream_name}/{label}: {text}")
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
