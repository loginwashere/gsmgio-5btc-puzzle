#!/usr/bin/env python3
"""Test whether P32TRAILING reuses the already-solved Phase 3 seven-part
password construction, as suggested by the Phase 3.2 monologue's "seven
intertwined passwords" line (itself a rewrite of the Matrix Reloaded
Architect's "23 individuals, 16 female, 7 male").

Phase 3's SHA-256 password is a literal ordered concatenation of exactly
seven parts (README.md, already solved):

    causality | Safenet | Luna | HSM | 11110 | <142-char hex> | <chess FEN>

This is the only canonically identified set of exactly seven password-level
items in the solved chain. The narrow hypothesis tested here is that P32's
password is that same concatenation, or its SHA-256, reused verbatim or in a
normalized/newline-adjusted form -- not a differently-chosen set of seven
values (no such set is uniquely identified; assembling one from URLs,
answers, hashes, and cipher keywords would require an arbitrary choice this
module deliberately does not make).
"""

import argparse
import hashlib
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

PHASE3_PARTS = (
    "causality",
    "Safenet",
    "Luna",
    "HSM",
    "11110",
    "0x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E697262"
    "206E6F20726F6C6C65636E61684320393030322F6E614A2F33302073656D695420656854",
    "B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1",
)
EXPECTED_CONCAT_LENGTH = 227
EXPECTED_PHASE3_SHA256 = (
    "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5"
)


def phase3_concat():
    return "".join(PHASE3_PARTS)


def material_family(candidates, blobs):
    materials = {}
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=True, whitespace_variants=True):
                materials.setdefault(keystr.encode("utf-8"), set()).add(candidate)
    # SHA-256 raw 32-byte digest used directly as key material (not text).
    digest = hashlib.sha256(phase3_concat().encode()).digest()
    materials.setdefault(digest, set()).add("phase3-sha256-raw-bytes")

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
    concat = phase3_concat()
    digest_hex = hashlib.sha256(concat.encode()).hexdigest()
    candidates = (concat, digest_hex)
    report = material_family(candidates, BLOBS)
    return {
        "concat_length": len(concat),
        "concat_sha256": digest_hex,
        "candidates": candidates,
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    report = audit()
    assert report["concat_length"] == EXPECTED_CONCAT_LENGTH
    assert report["concat_sha256"] == EXPECTED_PHASE3_SHA256
    assert report["candidate_count"] == 2
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: Phase 3's exact 227-char seven-part concatenation "
        f"(SHA-256 {report['concat_sha256'][:12]}...) and its digest, "
        f"{report['unique_material_count']} unique key materials, "
        f"against all 4 tracked blobs, 0 hits"
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
