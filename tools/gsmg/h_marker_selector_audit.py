#!/usr/bin/env python3
"""Test `h` as a marker/selector inside `dbbi`/`faed`, motivated by the H1/h1 tag-case audit.

Chat context: the SalPhaseIon page's `<H1>` (uppercase) vs Cosmic Duality's
`<h1>` (lowercase) tag-case discrepancy (see Phase 109) prompted the question
"what if h -> H means we also need to change some h into H in the textarea?"

Checked directly first (not assumed): `h` is not rare inside `dbbi`/`faed` --
it is one of the ordinary 9 alphabet letters (`abcdefghi`) both streams are
built from, appearing 8 times in `dbbi` and 58 times in `faed`. And the only
place case is actually load-bearing in this page -- the two Base64 halves of
the real embedded SALPH ciphertext (`salphaseion_aes_prefix`/`_suffix`) --
already contains both an `h` and an `H`, verified byte-for-byte against the
known-good `SALPHASEION_BLOB_B64` constant. Blanket-uppercasing every `h`
would corrupt already-correct ciphertext, and there is no established rule
for selecting a single `h` to change out of 66 ordinary occurrences. So the
literal instruction doesn't have a well-defined target.

What *is* independently motivated (Phase 34/104): `h` is already established
as `faed`'s mirror-hypothesis escape-pair partner (`mirror9('b') == 'h'`,
`e` fixed), derived from a completely different chain (the `BUT`/`HYE`
Architect-dialogue selection), not from this tag-case observation. That
licenses testing `h`'s *positions* as a marker/selector rather than editing
the ciphertext in place -- a bounded, mechanical operation, not a new
open-ended cipher family:

1. Direct transform: `dbbi`/`faed` with every `h` uppercased to `H`, tested
   directly as AES passphrases (the cheapest, most literal version of the
   original idea).
2. Position-selector: `faed`'s 58 `h` positions, taken modulo `len(dbbi)==91`,
   used to index into `dbbi` -- producing a derived 58-character string.
   Same operation run symmetrically (`dbbi`'s 8 `h` positions modulo
   `len(faed)==570`, indexing into `faed`).

Both are declared before testing, both go straight into the same oracle
every other candidate in this project has used.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import page_structure_audit as psa  # noqa: E402
from cb_common import (  # noqa: E402
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

EXPECTED_DBBI_H_COUNT = 8
EXPECTED_FAED_H_COUNT = 58
EXPECTED_DBBI_LENGTH = 91
EXPECTED_FAED_LENGTH = 570


def load_streams():
    html = psa.DEFAULT_HTML.read_text(encoding="utf-8")
    parser = psa.TextareaParser()
    parser.feed(html)
    salph_raw, _cosmic_raw = parser.textareas
    stream = psa.normalize_salphaseion(salph_raw)
    info = psa.audit(psa.DEFAULT_HTML)["salphaseion"]
    segments = {s["name"]: stream[s["start"]:s["end"]] for s in info["segments"]}
    return segments["dbbi"], segments["faed"]


def h_positions(s):
    return [i for i, c in enumerate(s) if c == "h"]


def uppercase_h(s):
    return s.replace("h", "H")


def select_via_positions(source_positions, target, modulus):
    return "".join(target[p % modulus] for p in source_positions)


def audit():
    dbbi, faed = load_streams()
    if len(dbbi) != EXPECTED_DBBI_LENGTH:
        raise AssertionError(f"unexpected dbbi length: {len(dbbi)}")
    if len(faed) != EXPECTED_FAED_LENGTH:
        raise AssertionError(f"unexpected faed length: {len(faed)}")

    dbbi_h_pos = h_positions(dbbi)
    faed_h_pos = h_positions(faed)
    if len(dbbi_h_pos) != EXPECTED_DBBI_H_COUNT:
        raise AssertionError(f"unexpected dbbi h count: {len(dbbi_h_pos)}")
    if len(faed_h_pos) != EXPECTED_FAED_H_COUNT:
        raise AssertionError(f"unexpected faed h count: {len(faed_h_pos)}")

    dbbi_upper = uppercase_h(dbbi)
    faed_upper = uppercase_h(faed)
    combined_upper = dbbi_upper + faed_upper

    faed_to_dbbi = select_via_positions(faed_h_pos, dbbi, EXPECTED_DBBI_LENGTH)
    dbbi_to_faed = select_via_positions(dbbi_h_pos, faed, EXPECTED_FAED_LENGTH)

    return {
        "dbbi_length": len(dbbi),
        "faed_length": len(faed),
        "dbbi_h_positions": dbbi_h_pos,
        "faed_h_positions": faed_h_pos,
        "dbbi_uppercase_h": dbbi_upper,
        "faed_uppercase_h": faed_upper,
        "combined_uppercase_h": combined_upper,
        "faed_h_positions_into_dbbi": faed_to_dbbi,
        "dbbi_h_positions_into_faed": dbbi_to_faed,
    }


def candidate_family(report):
    return (
        report["dbbi_uppercase_h"],
        report["faed_uppercase_h"],
        report["combined_uppercase_h"],
        report["faed_h_positions_into_dbbi"],
        report["dbbi_h_positions_into_faed"],
    )


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
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
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def print_report(report):
    print(f"[*] dbbi: {report['dbbi_length']} chars, {len(report['dbbi_h_positions'])} 'h' at {report['dbbi_h_positions']}")
    print(f"[*] faed: {report['faed_length']} chars, {len(report['faed_h_positions'])} 'h' at {report['faed_h_positions'][:10]}...")
    print(f"[*] dbbi with h->H:  {report['dbbi_uppercase_h']}")
    print(f"[*] faed h-positions mod 91 into dbbi: {report['faed_h_positions_into_dbbi']}")
    print(f"[*] dbbi h-positions mod 570 into faed: {report['dbbi_h_positions_into_faed']}")


def self_test():
    report = audit()
    assert report["dbbi_length"] == 91
    assert report["faed_length"] == 570
    assert len(report["dbbi_h_positions"]) == 8
    assert len(report["faed_h_positions"]) == 58
    assert report["dbbi_uppercase_h"].count("H") == 8
    assert report["dbbi_uppercase_h"].count("h") == 0
    assert report["faed_uppercase_h"].count("H") == 58
    assert len(report["faed_h_positions_into_dbbi"]) == 58
    assert len(report["dbbi_h_positions_into_faed"]) == 8
    print("[*] self-test OK: h positions, uppercase transform, and selector strings verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit()
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(candidate_family(report), blobs)
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
