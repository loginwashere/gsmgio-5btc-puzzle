#!/usr/bin/env python3
"""Bounded, disclosed passphrase-oracle sweep of anti-banking/monetary-
sovereignty candidate strings surfaced by the 2026-08-18 "Two Sloppy Days x
Creator Background Profile" brainstorm (ideas 15/17-19).

Two direct creator quotes, both newly surfaced this session and never
tested before (confirmed via grep against FINDINGS.md): msg 67741's full
retrospective states anti-banking sentiment as literally GSMG's founding
motivation ("That disrespect for the old banking system? Still burns to
this day... Give the power back to the little guy"); msg 25493
(2019-03-28, inside the construction window) states "Printing money is
changing numbers with a keyboard, so is deleting money(debt)."

Plus two already-catalogued-but-untested candidates from `doc/Brainstorms/
2026-08-15 - GSMG Media and Citation Inventory.md`'s "round 3" section:
"Proof of Keys" (Trace Mayer's campaign, launched 3 Jan 2019 -- the same
date as the already-confirmed Times headline this puzzle uses for Phase 3
part 6) and the QuadrigaCX collapse (Gerald Cotten died holding the only
keys to ~$190M CAD, Dec 2018-Feb 2019).
"""

import argparse
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

CANDIDATES = {
    "DISRESPECT_BANKING": "disrespect for the old banking system",
    "POWER_TO_LITTLE_GUY": "give the power back to the little guy",
    "PRINTING_MONEY": "printing money is changing numbers with a keyboard",
    "DELETING_MONEY_DEBT": "deleting money debt",
    "PROOF_OF_KEYS": "proof of keys",
    "NOT_YOUR_KEYS": "not your keys not your coins",
    "QUADRIGA": "quadriga",
    "GERALD_COTTEN": "gerald cotten",
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
    assert report["candidate_count"] == 8
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} anti-bank-theme "
        f"candidates / {report['unique_material_count']} unique key "
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
