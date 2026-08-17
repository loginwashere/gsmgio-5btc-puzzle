#!/usr/bin/env python3
"""Follow-up to Phase 265's Architect-monologue residual-vocabulary sweep
(2026-08-16): isolates the two tokens that sweep never actually separated
out as their own candidates -- "wiseman" and "hundred fourty" (140).

Phase 265's `RESIDUAL_CANDIDATES` tested this monologue's "source
codes"/"prime basics"/"23 ciphers"/"private keynote" phrasing as standalone
substrings, but never isolated the sentence "TAKE THIS TO HEART THAT WHAT A
WISEMAN ABOVE HINTED AT IS WORTH HUNDRED FOURTY OF THE INVESTMENT" this way
-- only the full ~14-word README line got tested as one unit, via Phase
267's mechanical line-based sweep. This closes that specific gap the same
way Phase 265 closed the rest of the passage: verbatim substrings of the
disclosed text, isolated individually, none invented.

Research context (not part of the oracle test): a live web/corpus search
for who "a wiseman" might refer to found no confirmed identification --
neither creator Telegram export uses the word "wiseman" at all (only
"-wise" as an adverbial suffix, e.g. "network wise", ordinary trading-bot
talk); the solver corpus's two "wise man" hits are unrelated banter; the
Cosmic Duality book's one "wise old man" mention is a Nantes Cathedral
statue description with no numeric or investment framing. Page 140 of the
book is simply where its index begins -- an unremarkable coincidence, not
pursued as a lead. "140" already has an established home: `FINDINGS.md`
Phase 214 / `GSMG_MATRIXSUMLIST_HISTORICAL_CODE_AUDIT.md` (a 2025 community
tool's 14x14=196 grid minus 56 already-known password letters = 140,
explicitly echoing this exact phrase) -- real but unselected, parked under
`G-MSL-001`. This audit does not reopen that hypothesis; it only tests the
literal words as direct passphrases, closing a narrow gap in already-
existing coverage.
"""

import argparse
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

CANDIDATES = (
    "wiseman",
    "wisemanabove",
    "hundredfourty",
    "hundredfourtyoftheinvestment",
    "wisemanabovehintedatisworthhundredfourtyoftheinvestment",
    "140",
)


def material_family(candidates, blobs):
    materials = {}
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form):
                materials.setdefault(keystr.encode("utf-8"), set()).add(candidate)
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
    assert "wiseman" in report["candidates"]
    assert "140" in report["candidates"]
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} wiseman/140 candidates / "
        f"{report['unique_material_count']} unique key materials against all 4 "
        f"tracked blobs, 0 hits"
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
