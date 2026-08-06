#!/usr/bin/env python3
"""Test the creator's Telegram handle, `SoWut`, standalone against the AES oracle.

`SoWut` is the real admin handle used throughout the Telegram export from the
early messages onward (first hit 2019-05-14, `@SoWut give me the solution`
-- a community member addressing them, not the creator introducing it as a
reveal). The exact normalized word `sowut` already occurs in the Tier-1
candidate corpus and was therefore covered by the completed padded and
no-padding binary-key-material sweeps. What had not been separately
reported was a small direct-textual oracle check of the literal handle and
its natural spoken expansion, "so what." No creator message explains the
name or selects it as puzzle input, so this is low-prior coverage rather
than a promoted clue.

Not a new cipher family or a new idea about what the name means -- just the
missing standalone data point.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

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

# Base strings covering the handle as it actually appears in chat plus the
# natural expansion ("wut" -> "what"), their spaced/punctuated literal forms,
# and the handle's reversal. `answer_forms` also supplies punctuation-stripped
# and case-normalized forms, but preserves each literal spelling as a distinct
# passphrase before doing so.
BASE_WORDS = (
    "SoWut",
    "So Wut",
    "sowhat",
    "so what",
    "so what?",
    "tuWoS",  # SoWut reversed
)


def candidate_family(words):
    seen = {}
    for word in words:
        for form in (word, word.upper(), word.lower(), word.capitalize()):
            seen.setdefault(form, None)
    return tuple(seen)


def audit():
    return {
        "words": BASE_WORDS,
        "candidates": candidate_family(BASE_WORDS),
    }


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
    print(f"[*] words: {report['words']!r}")
    print("[*] candidates:")
    for candidate in report["candidates"]:
        print(f"    {candidate!r}")


def self_test():
    report = audit()
    assert "SoWut" in report["candidates"]
    assert "SOWUT" in report["candidates"]
    assert "sowut" in report["candidates"]
    assert "sowhat" in report["candidates"]
    assert "SOWHAT" in report["candidates"]
    assert "so what" in report["candidates"]
    assert "so what?" in report["candidates"]
    assert "tuWoS" in report["candidates"]
    assert "tuwos" in report["candidates"]
    print(f"[*] self-test OK: {len(report['candidates'])} candidates from {len(report['words'])} base words")
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
        result = oracle_check(report["candidates"], blobs)
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
