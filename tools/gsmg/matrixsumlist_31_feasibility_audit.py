#!/usr/bin/env python3
"""Can authenticated ``matrixsumlist`` mechanics consume the exact 31 chars?

The admissible family is frozen to mechanics already present before this
audit:

* natural matrix dimensions from exact lengths;
* the reconstructed matrix sum list ``[23,16,7]`` as indices;
* the same list repeated as Caesar add/subtract values;
* classical keyed-columnar encrypt/decrypt with key ``matrixsumlist``;
* the exact corrected walk profile: total fitted events, yellow characters,
  and blue digraphs.

No padding, rotations, arbitrary matrix shapes, anagrams, language
hill-climbing, hashes, or cipher-oracle escalation are included. The audit
asks whether the operation is uniquely specified and produces a literal
instruction. A negative result means transition evidence is still required.
"""

import argparse
from fractions import Fraction
from math import comb

from cb_common import keyed_columnar
from denis_prime_extraction_audit import TARGET
from first_piece_color_reconstruction import DEFAULT_IMAGE
from flo_prime_walk_provenance_audit import audit as prime_walk_audit
from prime_matrixsum_reconstruction import EXPECTED_PRIME, matrixsumlist

MATRIX_KEY = "matrixsumlist"
SUM_LIST = (23, 16, 7)
CLUE_WORDS = (
    "yin", "yang", "matrix", "sum", "list", "seed", "key", "enter", "password",
)


def factor_pairs(length):
    return tuple(
        (rows, length // rows)
        for rows in range(1, length + 1)
        if length % rows == 0
    )


def index_family(text, indices):
    outputs = {}
    for reverse in (False, True):
        source = text[::-1] if reverse else text
        direction = "reverse" if reverse else "forward"
        for one_based in (False, True):
            base = "one" if one_based else "zero"
            offset = 1 if one_based else 0
            outputs[f"{direction}/{base}"] = "".join(
                source[(index - offset) % len(source)]
                for index in indices
            )
    return outputs


def repeated_caesar(text, values, operation):
    output = []
    for index, character in enumerate(text):
        letter = ord(character) - ord("a")
        value = values[index % len(values)]
        if operation == "add":
            result = letter + value
        elif operation == "text_minus_list":
            result = letter - value
        elif operation == "list_minus_text":
            result = value - letter
        else:
            raise ValueError(f"unknown operation: {operation!r}")
        output.append(chr(ord("a") + result % 26))
    return "".join(output)


def exact_profile_rate():
    """Shuffle 9 Y / 15 B over the 24 endpoint slots, with FEFE fixed between
    slots 20 and 21. The real profile occurs exactly when the last two endpoint
    slots contain one Y and one B, leaving 8 Y / 14 B before DBBI exhausts."""
    favorable = comb(22, 8) * comb(2, 1)
    total = comb(24, 9)
    return Fraction(favorable, total)


def walk_profile(report):
    fitted = report["fitted_spatial_walk"]
    yellow_characters = sum(
        len(record["required"]) for record in fitted if record["color"] == "Y"
    )
    blue_characters = sum(
        len(record["required"]) for record in fitted if record["color"] == "B"
    )
    return {
        "events": len(fitted),
        "yellow_characters": yellow_characters,
        "blue_characters": blue_characters,
        "blue_digraphs": blue_characters // 2,
        "fefe_characters": sum(
            len(record["required"]) for record in fitted if record["color"] == "F"
        ),
    }


def clue_hits(outputs):
    return {
        label: tuple(word for word in CLUE_WORDS if word in value.lower())
        for label, value in outputs.items()
    }


def audit(image_path=DEFAULT_IMAGE):
    matrix, reconstructed_sum_list = matrixsumlist(EXPECTED_PRIME)
    prime_walk = prime_walk_audit(image_path=image_path)
    profile = walk_profile(prime_walk)

    indexed = index_family(TARGET, reconstructed_sum_list)
    caesar = {
        operation: repeated_caesar(TARGET, reconstructed_sum_list, operation)
        for operation in ("add", "text_minus_list", "list_minus_text")
    }
    columnar = {
        direction: keyed_columnar(TARGET, MATRIX_KEY, direction)
        for direction in ("encrypt", "decrypt")
    }
    transformed = {
        **{f"index/{label}": value for label, value in indexed.items()},
        **{f"caesar/{label}": value for label, value in caesar.items()},
        **{f"columnar/{label}": value for label, value in columnar.items()},
    }

    selected_shapes = factor_pairs(len(TARGET))
    nontrivial_selected_shapes = tuple(
        shape for shape in selected_shapes if 1 not in shape
    )
    instruction_bits_length = len(MATRIX_KEY) * 8
    natural_instruction_shape = (len(MATRIX_KEY), 8)
    profile_tuple = (
        profile["events"],
        profile["yellow_characters"],
        profile["blue_digraphs"],
    )
    sum_list_tuple = tuple(reconstructed_sum_list)

    return {
        "input": TARGET,
        "input_length": len(TARGET),
        "input_shapes": selected_shapes,
        "nontrivial_input_shapes": nontrivial_selected_shapes,
        "matrix": matrix,
        "sum_list": sum_list_tuple,
        "index_outputs": indexed,
        "caesar_outputs": caesar,
        "columnar_outputs": columnar,
        "all_transformed_outputs": transformed,
        "clue_hits": clue_hits(transformed),
        "matrix_key_length": len(MATRIX_KEY),
        "columnar_remainder": len(TARGET) % len(MATRIX_KEY),
        "instruction_bits_length": instruction_bits_length,
        "natural_instruction_shape": natural_instruction_shape,
        "walk_profile": profile,
        "profile_tuple": profile_tuple,
        "profile_matches_sum_list": profile_tuple == sum_list_tuple,
        "profile_rate": exact_profile_rate(),
        "operation_uniquely_fixed": False,
        "blocking_reasons": (
            "31 has no nontrivial rectangular factorization",
            "13-column matrixsumlist key leaves a ragged 31 mod 13 = 5 layout",
            "[23,16,7] supports multiple established mechanics",
            "the 104 instruction bits have no authenticated projection onto 31 characters",
            "all bounded transformed outputs are non-language",
        ),
    }


def self_test(image_path=DEFAULT_IMAGE):
    assert factor_pairs(6) == ((1, 6), (2, 3), (3, 2), (6, 1))
    sample = "attackatdawnx"
    encrypted = keyed_columnar(sample, MATRIX_KEY, "encrypt")
    assert keyed_columnar(encrypted, MATRIX_KEY, "decrypt") == sample
    shifted = repeated_caesar(sample, SUM_LIST, "add")
    assert repeated_caesar(shifted, SUM_LIST, "text_minus_list") == sample

    report = audit(image_path)
    assert report["input"] == "ncsyangcahiriasogaleafayanestve"
    assert report["input_length"] == 31
    assert report["input_shapes"] == ((1, 31), (31, 1))
    assert report["nontrivial_input_shapes"] == ()
    assert report["matrix"] == [[5, 7, 4], [0, 6, 1]]
    assert report["sum_list"] == SUM_LIST
    assert report["index_outputs"] == {
        "forward/zero": "ygc",
        "forward/one": "aog",
        "reverse/zero": "csy",
        "reverse/one": "aoa",
    }
    assert report["caesar_outputs"] == {
        "add": "kszvqudsheyyfqzlwhiuhcqfxdlpjcb",
        "text_minus_list": "qmlbkgjmtksklklrqtootikrdxxvdoh",
        "list_minus_text": "kopzqurohqiqpqpjkhmmhsqjxddfxmt",
    }
    assert report["columnar_outputs"] == {
        "encrypt": "cssaaeiyhanaeafygvgerasotincanl",
        "decrypt": "inaoyvlsaaganrcygaeetshcfeisaan",
    }
    assert report["columnar_remainder"] == 5
    assert report["instruction_bits_length"] == 104
    assert report["natural_instruction_shape"] == (13, 8)
    assert report["walk_profile"] == {
        "events": 23,
        "yellow_characters": 16,
        "blue_characters": 14,
        "blue_digraphs": 7,
        "fefe_characters": 1,
    }
    assert report["profile_tuple"] == report["sum_list"] == SUM_LIST
    assert report["profile_matches_sum_list"] is True
    assert report["profile_rate"] == Fraction(45, 92)
    assert not any(report["clue_hits"].values())
    assert report["operation_uniquely_fixed"] is False
    print(
        "[*] self-test OK: dimensions, [23,16,7] index/Caesar family, "
        "ragged keyed-columnar forms, exact walk profile, and 45/92 null verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.image)
    if args.self_test:
        return

    report = audit(args.image)
    print(f"[*] input ({report['input_length']}): {report['input']}")
    print(f"[*] exact factor pairs: {report['input_shapes']}")
    print(f"[*] matrix/sum list: {report['matrix']} -> {report['sum_list']}")
    print(f"[*] walk profile: {report['profile_tuple']} matches={report['profile_matches_sum_list']}")
    rate = report["profile_rate"]
    print(
        f"[*] exact profile-preserving rate: {rate.numerator}/{rate.denominator} "
        f"= {float(rate):.6f}"
    )
    print("[*] bounded outputs:")
    for label, value in report["all_transformed_outputs"].items():
        print(f"    {label}: {value}")
    print("[*] blockers:")
    for reason in report["blocking_reasons"]:
        print(f"    - {reason}")
    print(
        "[*] verdict: matrixsumlist is a strong boundary/profile checkpoint, "
        "but no unique operation consumes the 31 characters. Stop computation "
        "and prioritize transition-evidence recovery."
    )


if __name__ == "__main__":
    main()
