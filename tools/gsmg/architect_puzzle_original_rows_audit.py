#!/usr/bin/env python3
"""Bounded, disclosed passphrase-oracle sweep of the Phase 3.2 Architect
monologue's four "no film equivalent" rows (`doc/Brainstorms/2026-08-17 -
Architect Monologue vs Film Substitution Table.md` rows 6, 7, 14, 15 --
the only rows with zero counterpart anywhere in the Matrix Reloaded source),
plus their natural sub-groupings, as password candidates.

Distinct from prior coverage, not a rephrasing of it:
- Phase 265 (`phase32_monologue_residual_audit.py`) tested a hand-picked
  vocabulary subset -- mostly rows 11/12's technical terms, plus a
  TRUNCATED version of row 6 missing its leading "please"
  (`ifyoufindawaytocompletethelastpartofthepuzzletaketheprivatekeyyouveearnedit`).
  Row 7 and row 14 were never touched by that audit at all.
- Phase 267 (`phase3_chain_full_text_p32_sweep_audit.py`) split the
  punctuation-free Architect speech on its own raw README line breaks
  (an arbitrary transcription boundary), not on logical sentence
  boundaries -- so no candidate there matches the complete row 6/7/14
  sentences as reconstructed in the substitution table.
- Phase 307 (`architect_monologue_whole_block_forward_audit.py`) tested the
  ENTIRE block as one unit, including the four verbatim film-match rows
  (2, 4, 9, 13a) -- not this deliberately curated "zero film content"
  subset.
- Phase 308 (`architect_monologue_wiseman_140_audit.py`) isolated only
  "wiseman"/"hundred fourty" tokens, not row 7 in full.
- "ciao bella o" alone is already closed via `ciao_selection_coverage_audit.py`
  / `bye_ciao_provenance_audit.py` -- not repeated here as a standalone
  candidate, only as the tail of the two multi-row joins below.

Closed, pre-declared candidate set (6 items, no iteration after seeing
results):
    ROW6, ROW7, ROW14                (each a complete logical sentence)
    ROW6_7                           ("appeal" sub-grouping)
    ROW14_15                         ("sign-off" sub-grouping)
    ROW6_7_14_15                     (the full "zero film content" subset)

Exact-match bar: a successful AES decrypt (valid PKCS#7 padding, no OpenSSL
error) against any tracked blob via the standard `passphrase_hits` oracle --
the same bar every prior phase in this project uses. Stop rule: 0 hits
closes this exact 6-candidate set negative; no further variant invention
without a new, separately-justified reason.
"""

import argparse
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

ROW6 = (
    "please if you find a way to complete the last part of the puzzle "
    "take the private key youve earned it"
)
ROW7 = (
    "but please take this to heart that what a wiseman above hinted at "
    "is worth hundred fourty of the investment thats what us guys at "
    "gsmg are trying to accomplish in the end please just help us "
    "build it instead of just waisting your lifetime by hunting for "
    "worthless prices and throphies like this"
)
ROW14 = "good luck nevertheless i really hope youre the one"
ROW15 = "ciao bella o"

ROW6_7 = ROW6 + " " + ROW7
ROW14_15 = ROW14 + " " + ROW15
ROW6_7_14_15 = ROW6 + " " + ROW7 + " " + ROW14 + " " + ROW15

CANDIDATES = {
    "ROW6": ROW6,
    "ROW7": ROW7,
    "ROW14": ROW14,
    "ROW6_7": ROW6_7,
    "ROW14_15": ROW14_15,
    "ROW6_7_14_15": ROW6_7_14_15,
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
        "candidates": {k: v for k, v in CANDIDATES.items()},
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    report = audit()
    assert report["candidate_count"] == 6
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert ROW6_7_14_15.endswith("ciao bella o")
    assert "please" in ROW6
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} disclosed "
        f"puzzle-original-row candidates / {report['unique_material_count']} "
        f"unique key materials against all 4 tracked blobs, 0 hits"
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
