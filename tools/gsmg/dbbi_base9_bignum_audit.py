#!/usr/bin/env python3
"""Radical fallback check: what if DBBI/FAED aren't a checkerboard cipher at
all, and the `a`-`i` alphabet is just base-9 digits forming one large number?

Every other hypothesis this project has tried (chain-addition, autokey,
Bifid, Playfair/Two-square/Four-square, Nihilist additive-key, this
session's Gronsfeld/ADFGVX/spiral-route ideas) assumes the straddling-
checkerboard framework is correct and only the details (escape pair,
alphabet keyword, over-encryption layer) are unknown. This drops that
assumption entirely: DBBI's IoC (0.151, "structured/key-like") is reported
relative to a 9-symbol alphabet, and 9 symbols is exactly what a base-9
positional numeral system needs. No checkerboard, no escape pairs, no
segmentation -- just the raw 91-symbol string read as one big number.

Closed, pre-declared candidate set (2 digit mappings x 2 read directions x
1 source string = 4 base integers, per this project's documented "four
unknowns" list in doc/GSMG_PUZZLE.md which already names the a-i digit
mapping (a0i8 vs a1i9) as genuinely unresolved -- not a new ambiguity
invented here):

    mapping a0i8: a=0, b=1, ..., i=8
    mapping a1i9: a=1, b=2, ..., i=9
    direction: forward (as-is) and reversed (character order flipped)

FAED (570 symbols) is included only as a coarse mod-curve-order check --
far too large to plausibly BE a 256-bit key directly without an unmotivated
truncation choice, so it is not treated symmetrically with DBBI (91 symbols,
~288 bits raw -- close enough to 256 bits to be worth a direct check).

Three things are checked per base integer, all mechanical, no new
candidates invented after seeing results:
1. Direct-fit private key: the integer reduced mod secp256k1's order N,
   packed to 32 bytes, checked against both known project addresses
   (prize address, halving-recipient address) via the same
   private_key_details() this project already uses elsewhere.
2. Raw-byte / decimal-string / hex-string forms of the integer run through
   the standard AES passphrase oracle against all four tracked blobs (this
   project's normal exact-match bar for everything else).
3. Byte-length sanity: how close the integer's natural byte length sits to
   32 bytes, reported for context, not treated as a pass/fail gate.

Exact-match bar: address match (for point 1) or a successful AES decrypt
(for point 2). Stop rule: no match on any of the 4 base integers x 3 checks
closes this hypothesis negative for the closed set above; no further digit
mapping or read-direction invention without a new, separately-justified
reason.
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import SECP256K1_ORDER, private_key_details  # noqa: E402
from cb_common import BLOBS, answer_forms, keystr_forms  # noqa: E402
from color_mask_full_stream_audit import passphrase_hits  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402

NINE_SYMS = "abcdefghi"
KNOWN_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}


def digit_map(offset):
    """offset=0 -> a0i8, offset=1 -> a1i9."""
    return {c: i + offset for i, c in enumerate(NINE_SYMS)}


def to_base9_int(raw, offset, reversed_order):
    dmap = digit_map(offset)
    seq = raw[::-1] if reversed_order else raw
    value = 0
    for ch in seq:
        value = value * 9 + dmap[ch]
    return value


def base_integers(raw):
    out = {}
    for offset, mapping_name in ((0, "a0i8"), (1, "a1i9")):
        for reversed_order, dir_name in ((False, "forward"), (True, "reversed")):
            out[f"{mapping_name}_{dir_name}"] = to_base9_int(raw, offset, reversed_order)
    return out


def scalar_hits(value):
    scalar = value % SECP256K1_ORDER
    if scalar == 0:
        return []
    key_bytes = scalar.to_bytes(32, "big")
    details = private_key_details(key_bytes)
    if details is None:
        return []
    hits = []
    for address_type, item in details.items():
        if item["address"] in KNOWN_ADDRESSES:
            hits.append({"address_type": address_type, "address": item["address"]})
    return hits


def passphrase_forms(value):
    forms = set()
    forms.add(str(value).encode("utf-8"))
    forms.add(hex(value)[2:].encode("utf-8"))
    forms.add(hex(value)[2:].upper().encode("utf-8"))
    byte_len = max(1, (value.bit_length() + 7) // 8)
    forms.add(value.to_bytes(byte_len, "big"))
    return forms


def audit():
    report = {"dbbi": {}, "faed_mod_n_only": {}}

    dbbi_ints = base_integers(DBBI)
    for name, value in dbbi_ints.items():
        entry = {
            "bit_length": value.bit_length(),
            "byte_length": (value.bit_length() + 7) // 8,
            "scalar_hits": scalar_hits(value),
            "passphrase_hits": [],
        }
        for material in sorted(passphrase_forms(value)):
            for hit in passphrase_hits(material, BLOBS):
                entry["passphrase_hits"].append({"material_hex": material.hex(), **hit})
            # also run the standard answer_forms/keystr_forms normalization
            # over the decimal-string form, matching this project's usual
            # text-candidate treatment.
        for form in answer_forms(str(value)):
            for keystr in keystr_forms(form):
                material = keystr.encode("utf-8")
                for hit in passphrase_hits(material, BLOBS):
                    entry["passphrase_hits"].append({"material_hex": material.hex(), **hit})
        report["dbbi"][name] = entry

    faed_ints = base_integers(FAED)
    for name, value in faed_ints.items():
        report["faed_mod_n_only"][name] = {
            "bit_length": value.bit_length(),
            "scalar_hits": scalar_hits(value),
        }

    return report


def self_test():
    # a0i8 forward on "aei" -> a=0,e=4,i=8 -> base-9 digits [0,4,8] -> 0*81+4*9+8=44
    assert to_base9_int("aei", 0, False) == 44
    # a1i9 forward on "aei" -> a=1,e=5,i=9 -> [1,5,9] -> 1*81+5*9+9=135
    assert to_base9_int("aei", 1, False) == 135
    # reversed flips read order
    assert to_base9_int("aei", 0, True) == to_base9_int("iea", 0, False)

    dbbi_ints = base_integers(DBBI)
    assert len(dbbi_ints) == 4
    # 91 base-9 digits is at most ceil(91*log2(9)) = 289 bits
    for v in dbbi_ints.values():
        assert v.bit_length() <= 289
        assert v > 0

    faed_ints = base_integers(FAED)
    assert len(faed_ints) == 4

    print("[*] self-test OK: base-9 digit mapping, reversal, and bit-length bounds verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
