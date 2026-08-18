#!/usr/bin/env python3
"""Bounded, disclosed passphrase-oracle sweep of Mr. Robot-sourced candidate
strings surfaced by the 2026-08-18 "Two Sloppy Days x Creator Background
Profile" brainstorm (ideas 11-15): the creator's confirmed, personally-
invested engagement with the show (msg 67741's "MR. ROIbot" naming, msg
9592's direct 2023 quote about the show's last scene) plus two already-
confirmed in-puzzle Mr. Robot citations (Qwerty->Q=82, Safenet/Luna/HSM)
motivate checking a handful of specific, well-known show elements that have
never been tried here: the "red wheelbarrow" security-question poem, the
show's own recurring dialogue ("Hello, friend" / "Hello, Elliot"), the
"Mastermind" persona name, the "who are you" tagline question, and the
"5/9" hack designation. Confirmed via grep against FINDINGS.md: none of
these six strings has ever been tested against any tracked blob.

Distinct from prior Mr. Robot coverage: Phase-level history already tested
"Whiterose"/"whiteroseredqueen" (closed negative, URL-guess context) and
consumed "Qwerty"/"HSM"/"Safenet"/"Luna" as already-solved password
material -- none of those overlap with the six candidates here.
"""

import argparse
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

CANDIDATES = {
    "RED_WHEELBARROW": "red wheelbarrow",
    "HELLO_FRIEND": "hello friend",
    "HELLO_ELLIOT": "hello elliot",
    "MASTERMIND": "mastermind",
    "WHO_ARE_YOU": "who are you",
    "FIVE_NINE": "5/9",
}


def material_family(candidates, blobs):
    materials = {}
    for name, candidate in candidates.items():
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form):
                materials.setdefault(keystr.encode("utf-8"), set()).add(name)
    hits = []
    for material, sources in sorted(materials.items()):
        for hit in passphrase_hits(material, blobs):
            hits.append({
                "sources": tuple(sorted(sources)),
                "material_hex": material.hex(),
                **hit,
            })
    return {
        "candidate_count": len(candidates),
        "unique_material_count": len(materials),
        "hits": hits,
    }


def audit():
    report = material_family(CANDIDATES, BLOBS)
    return {
        "candidates": CANDIDATES,
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    report = audit()
    assert report["candidate_count"] == 6
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} Mr. Robot identity-"
        f"theme candidates / {report['unique_material_count']} unique key "
        f"materials against all 4 tracked blobs, 0 hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    print(json.dumps({k: v for k, v in report.items() if k != "candidates"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
