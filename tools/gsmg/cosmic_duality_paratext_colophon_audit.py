#!/usr/bin/env python3
"""Candidate family -- Cosmic Duality colophon/copyright-page paratext (2026-08-15).

Executes item 1 of doc/Brainstorms/2026-08-15 - New Book Approaches
brainstorm: the 2026-08-12 acquisition worksheet pre-registered a paratext
pass (ISBN/LCCN/Dewey/edition/printing codes) that was never actually run --
its "Result" section is still blank. The user pointed directly at one of the
existing 73 2026-07-12 photos (`Screenshot from 2026-07-12 14-48-32.png`,
the book's p.144 copyright/colophon page) rather than taking a new one, so
this closes that queued item using already-captured evidence.

Transcribed directly from the photo (not OCR'd -- this page's small print
and multi-column layout make hand-transcription more reliable):

  Title (catalog form): "Cosmic Duality / by the editors of Time-Life Books."
  ISBN (trade):   0-8094-6516-7
  ISBN (library): 0-8094-6517-5
  LCCN: 90-28806, CIP
  LC call number: BF1999.C6975 1991
  Dewey: 147'.4--dc20
  Copyright: 1991 Time-Life Books. First printing. Printed in U.S.A.
  Colophon page number: 144

The ISBNs were misread as `0-8094-6616-7`/`0-8094-6617-5` from an earlier,
lower-resolution photo (`Screenshot from 2026-07-12 14-48-32.png`); a
sharper, directly-lit photo of the same page corrected the third block's
second digit `6516`/`6517` (not `6616`/`6617`). Independently confirmed by
ISBN-10 checksum: the corrected digits pass (`sum(d_i * (10-i)) mod 11 ==
0`); the original misread digits fail. This is the checksum-verified,
corrected transcription.

Each identifier is tried in several literal forms (hyphenated as printed,
digits-only, and any distinct sub-groupings) through `answer_forms()` +
`keystr_forms()`, matching this project's standard candidate-form
convention, against all four tracked blobs under the standard CBC oracle.
This is a bounded, disclosed test of the literal printed identifiers --
not a cipher construction, since no creator source instructs any operation
on them beyond "these are the artifact's identifiers."
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent

from cb_common import BLOBS, aes_try_open_bytes, answer_forms, keystr_forms  # noqa: E402

RAW_CANDIDATES = {
    "isbn_trade_hyphenated": "0-8094-6516-7",
    "isbn_trade_digits": "0809465167",
    "isbn_library_hyphenated": "0-8094-6517-5",
    "isbn_library_digits": "0809465175",
    "lccn_hyphenated": "90-28806",
    "lccn_digits": "9028806",
    "lc_call_number": "BF1999.C6975 1991",
    "lc_call_number_nospace": "BF1999.C69751991",
    "lc_call_number_core": "1999.6975",
    "dewey": "147.4",
    "dewey_full": "147.4--dc20",
    "colophon_page_number": "144",
    "copyright_year": "1991",
}


def all_candidate_strings():
    candidates = {}
    for label, raw in RAW_CANDIDATES.items():
        candidates[label] = sorted(answer_forms(raw))
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
    candidates = all_candidate_strings()
    assert set(candidates.keys()) == set(RAW_CANDIDATES.keys())
    for label, forms in candidates.items():
        assert forms, f"{label} produced no candidate forms"
    print(f"[*] self-test OK: {len(RAW_CANDIDATES)} raw identifiers, "
          f"{sum(len(v) for v in candidates.values())} total candidate strings")


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
        for label, raw in RAW_CANDIDATES.items():
            print(f"{label}: {raw!r}")
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
