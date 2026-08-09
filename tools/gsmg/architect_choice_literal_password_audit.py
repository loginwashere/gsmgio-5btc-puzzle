#!/usr/bin/env python3
"""Check the strict literal-last-words alternative as a direct password.

The final spoken sentence before the Architect's literal word ``choice`` is
seven words in both frozen sources:

    AS YOU ADEQUATELY PUT THE PROBLEM IS [CHOICE]

Because seven is the final member of the independently derived [23,16,7]
list, test only that exact seven-word phrase, spaced and concatenated.  This
does not generate shorter suffixes, screenplay windows, synonyms, or keys.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from architect_choice_boundary_audit import audit as boundary_audit  # noqa: E402
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


def candidates():
    report = boundary_audit()
    film = report["sources"]["film"]["final_sentence_to_choice"]["tokens"]
    screenplay = report["sources"]["screenplay"]["final_sentence_to_choice"]["tokens"]
    if film != screenplay or len(film) != 7:
        raise AssertionError("literal seven-word boundary is not source-stable")
    return (" ".join(film), "".join(film))


def oracle_check(base_candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in base_candidates:
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
    return {"tested_keystrings": len(tested), "hits": hits}


def self_test():
    result = candidates()
    assert result == (
        "as you adequately put the problem is",
        "asyouadequatelyputtheproblemis",
    )
    print("[*] self-test OK: source-stable literal seven-word candidates verified")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()
    base_candidates = self_test() if args.self_test else candidates()
    print(f"[*] candidates: {base_candidates}")
    if not args.oracle:
        return
    blobs = dict(BLOBS)
    if args.include_quarantined:
        blobs.update(QUARANTINED_BLOBS)
    result = oracle_check(base_candidates, blobs)
    hit_count = sum(len(values) for values in result["hits"].values())
    print(
        f"[*] blobs={len(blobs)} keystrings={result['tested_keystrings']} "
        f"hits={hit_count}"
    )
    for family, hits in result["hits"].items():
        print(f"    {family}: {len(hits)}")
        for hit in hits:
            print(f"      {hit!r}")


if __name__ == "__main__":
    main()
