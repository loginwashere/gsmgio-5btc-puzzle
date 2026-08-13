#!/usr/bin/env python3
"""Bounded, disclosed passphrase-oracle sweep of the Phase 3.2 Architect
monologue's own residual vocabulary against all four tracked blobs.

`remaining_structural_avenues_audit.py` (Phase 179) already ran the VIC-cipher
output itself (`VALIDATION_ANSWER`, "incaseyoumanagetocrackthis",
"theprivatekeysbelongtohalfandbetterhalf", "halfandbetterhalf") through the
standard passphrase pipeline against P32TRAILING -- negative. This module
does not repeat those.

What it adds is the phrasing from the *same* decrypted monologue that
`GSMG_EXCLUDED_WORDLIST_COVERAGE_MATRIX.md` shows only ever reached padded-
binary/literal-raw-key coverage (bytes used directly as AES key material),
never the standard `openssl -pass pass:X` style passphrase-to-KDF pipeline
that every other solved stage in this puzzle actually used:

    "RETURN TO THE SOURCE CODES REINSERTING THE PRIME BASICS AFTER WHICH YOU
    WILL BE REQUIRED TO SELECT FROM OVER TWENTY-THREE CIPHERS SIXTEEN
    ENCRYPTIONS AND OR SEVEN INTERTWINED PASSWORDS TO FIND THE ACTUAL PRIVATE
    KEYNOTE THAT ALSO BRUTE FORCING MIGHT BE REQUIRED"
    "IF YOU FIND A WAY TO COMPLETE THE LAST PART OF THE PUZZLE TAKE THE
    PRIVATE KEY YOUVE EARNED IT"

It also adds the raw 149-digit `VALIDATION_NUM` decimal stream itself as a
literal passphrase candidate -- used everywhere else in this project only as
the checkerboard *ciphertext* that decodes to the half/better-half sentence,
never tried as a password in its own right -- and the bare "23"/"16"/"7"
tokens the monologue names explicitly. Every candidate is a verbatim
substring of the disclosed README plaintext; none are invented.
"""

import argparse
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits
from data import VALIDATION_NUM

RESIDUAL_CANDIDATES = (
    "sourcecodes",
    "returntothesourcecodes",
    "primebasics",
    "reinsertingtheprimebasics",
    "returntothesourcecodesreinsertingtheprimebasics",
    "twentythreeciphers",
    "sixteenencryptions",
    "sevenintertwinedpasswords",
    "twentythreecipherssixteenencryptionsandorsevenintertwinedpasswords",
    "actualprivatekeynote",
    "findtheactualprivatekeynote",
    "bruteforcingmightberequired",
    "findtheactualprivatekeynotethatalsobruteforcingmightberequired",
    "taketheprivatekeyyouveearnedit",
    "ifyoufindawaytocompletethelastpartofthepuzzletaketheprivatekeyyouveearnedit",
    "23",
    "16",
    "7",
    VALIDATION_NUM,
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
    report = material_family(RESIDUAL_CANDIDATES, BLOBS)
    return {
        "candidates": RESIDUAL_CANDIDATES,
        "validation_num_length": len(VALIDATION_NUM),
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    report = audit()
    assert report["candidate_count"] == 19
    assert "sourcecodes" in report["candidates"]
    assert VALIDATION_NUM in report["candidates"]
    assert report["validation_num_length"] == 149
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} disclosed monologue-"
        f"residual candidates / {report['unique_material_count']} unique key "
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
