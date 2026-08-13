#!/usr/bin/env python3
"""Close Point 15's bounded ``G``-as-generator/operator proposals.

The authenticated #383838 layer fixes two selected glyph rails and row-local
uppercase-G counts 4 and 2.  This audit checks only the applications named in
the brainstorm: adjacency as scalar syntax, G removal, count-based selectors,
count-based strides/chunks, and the literal scalars 4/2 on secp256k1.  It does
not invent a missing k, fold arbitrary characters into integers, or launch a
private-key search.
"""

import argparse
import hashlib
import re

from stage0_footer_palette_layer_audit import ADDRESS, BANNER
from stage0_g_shadow_consumer_audit import audit as shadow_audit

SECP_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
SECP_G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)
TARGET_ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
CLUE_TERMS = (
    "seed",
    "rabbit",
    "matrix",
    "sum",
    "list",
    "yin",
    "yang",
    "enter",
    "batch",
    "key",
    "bitcoin",
)


def point_add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % SECP_P == 0:
        return None
    if left == right:
        slope = (3 * x1 * x1) * pow(2 * y1, -1, SECP_P) % SECP_P
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, SECP_P) % SECP_P
    x3 = (slope * slope - x1 - x2) % SECP_P
    y3 = (slope * (x1 - x3) - y1) % SECP_P
    return x3, y3


def scalar_multiply(scalar):
    result = None
    addend = SECP_G
    while scalar:
        if scalar & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        scalar >>= 1
    return result


def base58check(payload):
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    value = int.from_bytes(payload + checksum, "big")
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = alphabet[remainder] + encoded
    leading_zeroes = len(payload + checksum) - len((payload + checksum).lstrip(b"\0"))
    return "1" * leading_zeroes + encoded


def bitcoin_address(point, compressed):
    x, y = point
    if compressed:
        public_key = bytes((2 + (y & 1),)) + x.to_bytes(32, "big")
    else:
        public_key = b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")
    sha = hashlib.sha256(public_key).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    return public_key.hex().upper(), base58check(b"\x00" + ripe)


def adjacency_contexts(text, selected_text):
    def contexts(source):
        return tuple(
            {
                "index_0": index,
                "left": source[index - 1] if index else None,
                "right": source[index + 1] if index + 1 < len(source) else None,
                "numeric_neighbor_count": sum(
                    character is not None and character.isdigit()
                    for character in (
                        source[index - 1] if index else None,
                        source[index + 1] if index + 1 < len(source) else None,
                    )
                ),
            }
            for index, character in enumerate(source)
            if character == "G"
        )

    return {"source": contexts(text), "selected": contexts(selected_text)}


def stride_variants(operand, step):
    variants = []
    for direction, directed in (("forward", operand), ("reverse", operand[::-1])):
        for offset in range(step):
            variants.append(
                {
                    "direction": direction,
                    "offset": offset,
                    "text": directed[offset::step],
                }
            )
    return tuple(variants)


def audit():
    shadow = shadow_audit()
    source_texts = (BANNER, ADDRESS)
    rails = []
    for source_text, row in zip(source_texts, shadow["rows"]):
        selected = row["selected_text"]
        operand = selected.replace("G", "")
        reference = row["reference_count"]
        variants = stride_variants(operand, reference)
        rails.append(
            {
                "label": row["label"],
                "source_text": source_text,
                "selected_text": selected,
                "g_count": selected.count("G"),
                "reference_count": reference,
                "operand_after_removing_G": operand,
                "whole_operand_is_decimal": operand.isdecimal(),
                "whole_operand_is_hex": bool(re.fullmatch(r"[0-9A-Fa-f]+", operand)),
                "numeric_runs": tuple(re.findall(r"\d+", operand)),
                "adjacency": adjacency_contexts(source_text, selected),
                "zero_based_selector": operand[reference],
                "one_based_selector": operand[reference - 1],
                "chunk_partition": tuple(
                    operand[offset : offset + reference]
                    for offset in range(0, len(operand), reference)
                ),
                "stride_variants": variants,
            }
        )

    combined_stride_outputs = set()
    for first, second in ((rails[0], rails[1]), (rails[1], rails[0])):
        for left in first["stride_variants"]:
            for right in second["stride_variants"]:
                combined_stride_outputs.add(left["text"] + right["text"])
    term_hits = tuple(
        (output, term)
        for output in sorted(combined_stride_outputs)
        for term in CLUE_TERMS
        if term in output.lower()
    )

    scalar_addresses = {}
    for scalar in sorted({row["reference_count"] for row in rails}):
        point = scalar_multiply(scalar)
        compressed_key, compressed_address = bitcoin_address(point, True)
        uncompressed_key, uncompressed_address = bitcoin_address(point, False)
        scalar_addresses[scalar] = {
            "compressed_public_key": compressed_key,
            "compressed_address": compressed_address,
            "uncompressed_public_key": uncompressed_key,
            "uncompressed_address": uncompressed_address,
            "matches_stage0_address": TARGET_ADDRESS
            in (compressed_address, uncompressed_address),
        }

    all_adjacencies = tuple(
        context
        for rail in rails
        for family in ("source", "selected")
        for context in rail["adjacency"][family]
    )
    return {
        "rails": tuple(rails),
        "combined_stride_output_count": len(combined_stride_outputs),
        "combined_stride_term_hits": term_hits,
        "all_G_anchors_have_numeric_neighbor": all(
            context["numeric_neighbor_count"] for context in all_adjacencies
        ),
        "scalar_addresses": scalar_addresses,
        "literal_scalar_count": len(scalar_addresses),
        "any_scalar_address_match": any(
            row["matches_stage0_address"] for row in scalar_addresses.values()
        ),
        "curve_semantics_selected": False,
        "oracle_run": False,
        "promoted": False,
    }


def self_test():
    report = audit()
    banner, address = report["rails"]
    assert banner["selected_text"] == "GSGO5BCPUCG"
    assert address["selected_text"] == "GMGC9g2cPBe"
    assert banner["operand_after_removing_G"] == "SO5BCPUC"
    assert address["operand_after_removing_G"] == "MC9g2cPBe"
    assert (banner["reference_count"], address["reference_count"]) == (4, 2)
    assert banner["numeric_runs"] == ("5",)
    assert address["numeric_runs"] == ("9", "2")
    assert not banner["whole_operand_is_decimal"] and not banner["whole_operand_is_hex"]
    assert not address["whole_operand_is_decimal"] and not address["whole_operand_is_hex"]
    assert (banner["zero_based_selector"], banner["one_based_selector"]) == ("C", "B")
    assert (address["zero_based_selector"], address["one_based_selector"]) == ("9", "C")
    assert banner["chunk_partition"] == ("SO5B", "CPUC")
    assert address["chunk_partition"] == ("MC", "9g", "2c", "PB", "e")
    assert report["combined_stride_output_count"] == 64
    assert report["combined_stride_term_hits"] == ()
    assert not report["all_G_anchors_have_numeric_neighbor"]
    assert tuple(report["scalar_addresses"]) == (2, 4)
    assert scalar_multiply(1) == SECP_G
    assert report["scalar_addresses"][2]["compressed_address"] == (
        "1cMh228HTCiwS8ZsaakH8A8wze1JR5ZsP"
    )
    assert report["scalar_addresses"][2]["uncompressed_address"] == (
        "1LagHJk2FyCV2VzrNHVqg3gYG4TSYwDV4m"
    )
    assert report["scalar_addresses"][4]["compressed_address"] == (
        "1JtK9CQw1syfWj1WtFMWomrYdV3W2tWBF9"
    )
    assert report["scalar_addresses"][4]["uncompressed_address"] == (
        "1MnyqgrXCmcWJHBYEsAWf7oMyqJAS81eC"
    )
    assert not report["any_scalar_address_match"]
    assert not report["curve_semantics_selected"]
    assert not report["oracle_run"] and not report["promoted"]
    print("[*] self-test OK: Point 15 G/operator gate is bounded and negative")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    for rail in report["rails"]:
        print(
            f"[*] {rail['label']}: selected={rail['selected_text']} "
            f"operand={rail['operand_after_removing_G']} "
            f"reference={rail['reference_count']} runs={rail['numeric_runs']}"
        )
    print(
        f"[*] stride family: {report['combined_stride_output_count']} unique joins; "
        f"clue-term hits={report['combined_stride_term_hits']}"
    )
    for scalar, row in report["scalar_addresses"].items():
        print(
            f"[*] {scalar}G: compressed={row['compressed_address']} "
            f"uncompressed={row['uncompressed_address']} "
            f"target_match={row['matches_stage0_address']}"
        )


if __name__ == "__main__":
    main()
