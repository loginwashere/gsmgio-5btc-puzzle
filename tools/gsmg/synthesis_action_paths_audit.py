#!/usr/bin/env python3
"""Audit the three genuinely distinct actions from the latest synthesis.

Path A's padded/ragged matrix proposals are coverage-only: Phase 51 already
establishes that 31 is prime and rejects an invented 32nd cell.  This module
therefore executes only:

* Path B: the sourced final Architect sentence before Neo takes the left door;
* Path C: the exact 31-character selection as a classic-J ``pad25`` keyword
  for FAED under the two already-established escape-pair hypotheses;
* Path D: canonical a=0..i=8 base-9 integers for DBBI and FAED, added modulo
  the secp256k1 group order and checked against the known GSMG addresses.

The commonly quoted Neo reply ``Not if I can help it`` is recorded but not
tested: it does not occur in the repository's sourced Matrix Reloaded script.
No padding dimension, alternate radix, byte order, scalar hash, or extra
key-combination operator is introduced.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import (  # noqa: E402
    SECP256K1_ORDER,
    private_key_details,
)
from cb_common import (  # noqa: E402
    BLOBS,
    answer_forms,
    decode_9ary,
    keystr_forms,
    pad25,
)
from color_mask_full_stream_audit import (  # noqa: E402
    KNOWN_ADDRESSES,
    passphrase_hits,
)
from data import DBBI, FAED  # noqa: E402
from denis_prime_extraction_audit import TARGET  # noqa: E402
from salt_selector_permutation_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
)


SCRIPT_WINDOWS = ROOT / "wordlists/gsmg/matrix_script_windows.txt"
ARCHITECT_FINAL = "she is going to die and there is nothing you can do to stop it"
UNSOURCED_NEO_REPLY = "not if i can help it"
ESCAPE_ORDERS = (("g", "i"), ("i", "g"), ("b", "e"), ("e", "b"))
TOPOLOGIES = ("top_first", "escapes_first")
MARKERS = ("private", "bitcoin", "password", "matrix", "choice", "salvation")


def source_provenance(path=SCRIPT_WINDOWS):
    text = " ".join(path.read_text(encoding="utf-8", errors="replace").lower().split())
    return {
        "path": str(path),
        "architect_final_present": ARCHITECT_FINAL in text,
        "proposed_neo_reply_present": UNSOURCED_NEO_REPLY in text,
    }


def passphrase_family(candidate):
    materials = {
        keystr.encode("utf-8")
        for form in answer_forms(candidate)
        for keystr in keystr_forms(form)
    }
    hits = []
    for material in sorted(materials):
        for hit in passphrase_hits(material, BLOBS):
            hits.append({"material_hex": material.hex(), **hit})
    return {"material_count": len(materials), "hits": hits}


def path_b():
    provenance = source_provenance()
    if not provenance["architect_final_present"]:
        raise AssertionError("sourced Architect sentence is absent")
    if provenance["proposed_neo_reply_present"]:
        raise AssertionError("the supposedly unsourced Neo reply unexpectedly exists")
    tested = passphrase_family(ARCHITECT_FINAL)
    return {
        "provenance": provenance,
        "tested_sentence": ARCHITECT_FINAL,
        "rejected_unsourced_sentence": UNSOURCED_NEO_REPLY,
        **tested,
    }


def path_c(model):
    alphabet = pad25(TARGET, drop="J", tail_fill="forward", merge_direction="backward")
    outputs = []
    all_materials = set()
    hits = []
    for escapes in ESCAPE_ORDERS:
        for topology in TOPOLOGIES:
            decoded = decode_9ary(FAED, alphabet, *escapes, topology=topology)
            if "?" in decoded:
                raise AssertionError(f"FAED does not segment under {escapes}/{topology}")
            materials = {
                keystr.encode("utf-8")
                for form in answer_forms(decoded)
                for keystr in keystr_forms(form)
            }
            all_materials.update(materials)
            row_hits = []
            for material in sorted(materials):
                for hit in passphrase_hits(material, BLOBS):
                    record = {"material_hex": material.hex(), **hit}
                    row_hits.append(record)
                    hits.append({"escapes": escapes, "topology": topology, **record})
            outputs.append({
                "escapes": escapes,
                "topology": topology,
                "length": len(decoded),
                "sha256": hashlib.sha256(decoded.encode("ascii")).hexdigest(),
                "preview": decoded[:120],
                "normalized_quadgram_score": quadgram_score(
                    decoded.encode("ascii"), model
                ),
                "marker_hits": tuple(marker for marker in MARKERS if marker in decoded.lower()),
                "material_count": len(materials),
                "oracle_hits": row_hits,
            })
    return {
        "keyword": TARGET,
        "keyword_length": len(TARGET),
        "alphabet": alphabet,
        "alphabet_length": len(alphabet),
        "drop": "J",
        "tail_fill": "forward",
        "merge_direction": "backward",
        "outputs": outputs,
        "unique_material_count": len(all_materials),
        "hits": hits,
    }


def base9_integer(stream):
    digits = "".join(str(ord(char) - ord("a")) for char in stream)
    if any(digit not in "012345678" for digit in digits):
        raise ValueError("stream is not canonical a=0..i=8 base 9")
    return int(digits, 9)


def scalar_report(label, value):
    reduced = value % SECP256K1_ORDER
    if reduced == 0:
        return {"label": label, "scalar_hex": "00" * 32, "valid": False, "addresses": {}}
    material = reduced.to_bytes(32, "big")
    details = private_key_details(material)
    addresses = {
        address_type: item["address"]
        for address_type, item in details.items()
    }
    return {
        "label": label,
        "scalar_hex": material.hex(),
        "valid": True,
        "addresses": addresses,
        "known_address_hits": tuple(
            address
            for address in addresses.values()
            if address in KNOWN_ADDRESSES
        ),
    }


def path_d():
    dbbi = base9_integer(DBBI)
    faed = base9_integer(FAED)
    return {
        "digit_map": "a=0,b=1,...,i=8",
        "radix": 9,
        "byte_order": "source-order / most-significant digit first",
        "reports": (
            scalar_report("DBBI_mod_n", dbbi),
            scalar_report("FAED_mod_n", faed),
            scalar_report("DBBI_plus_FAED_mod_n", dbbi + faed),
        ),
    }


def audit():
    model = load_quadgrams()
    return {
        "path_a": {
            "status": "already_closed_phase_51",
            "reason": "31 is prime; 4x8 or 5x6+1 requires an unauthenticated padding cell",
        },
        "path_b": path_b(),
        "path_c": path_c(model),
        "path_d": path_d(),
    }


def self_test():
    assert base9_integer("a") == 0
    assert base9_integer("bi") == 17
    assert len(TARGET) == 31
    alphabet = pad25(TARGET)
    assert alphabet == "NCSYAGHIROLEFTVBDKMPQUWXZ"
    assert len(alphabet) == len(set(alphabet)) == 25
    provenance = source_provenance()
    assert provenance["architect_final_present"] is True
    assert provenance["proposed_neo_reply_present"] is False
    for report in path_d()["reports"]:
        assert report["valid"] is True
        assert set(report["addresses"]) == {"compressed", "uncompressed"}
    print(
        "[*] self-test OK: sourced door line, exact selected-text pad25 alphabet, "
        "and canonical base-9 scalar addition"
    )


def print_report(report):
    print(f"[*] Path A: {report['path_a']['status']} -- {report['path_a']['reason']}")
    path_b_report = report["path_b"]
    print(
        f"[*] Path B: {path_b_report['material_count']} exact/hash materials, "
        f"hits={len(path_b_report['hits'])}; proposed Neo reply sourced="
        f"{path_b_report['provenance']['proposed_neo_reply_present']}"
    )
    path_c_report = report["path_c"]
    print(
        f"[*] Path C: keyword={path_c_report['keyword']} -> "
        f"alphabet={path_c_report['alphabet']}; "
        f"unique materials={path_c_report['unique_material_count']}, "
        f"hits={len(path_c_report['hits'])}"
    )
    for row in path_c_report["outputs"]:
        print(
            f"    escapes={row['escapes']} topology={row['topology']} "
            f"len={row['length']} score={row['normalized_quadgram_score']:.6f} "
            f"markers={row['marker_hits']} sha256={row['sha256']} "
            f"preview={row['preview']}"
        )
    print("[*] Path D:")
    for row in report["path_d"]["reports"]:
        print(
            f"    {row['label']}: {row['scalar_hex']} "
            f"addresses={row['addresses']} known_hits={row['known_address_hits']}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
