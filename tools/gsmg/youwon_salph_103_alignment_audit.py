#!/usr/bin/env python3
"""Audit the bounded YOUWON-tail / 103-character SALPH alignment.

This is a structural audit, not a password or decrypt sweep.  It checks the
community-derived subtraction output, the established six SALPH instruction
fragments, four ordinary letter-number serializations, every suffix boundary,
and the native 13x7 ``YOUWONX`` row boundary.
"""

from anstoo_provenance_audit import (
    EXPECTED_INSTRUCTION_LENGTH,
    INSTRUCTION_PARTS,
)
from data import DBBI, VALIDATION_ANSWER
from external_archive_lead_audit import subtract_mod26
from youwon_partition_audit import COLUMNS, EXPECTED_START_0, ROW_TEXT, WORD


EXPECTED_OUTPUT = (
    "VOZIJBDTIQBRGVEOMZNBCYOUWONXCPKWGBNAXDGJGDUNNVMPABTAFPAAXMJYLZBU"
    "WERDNXYDESKUOBXCAMVDJLQTSGA"
)
EXPECTED_A1Z26_STREAM = (
    "243161123721412447107421141422131612201616112413102512262212351841"
    "4242545191121152243113224101217201971"
)
POSITION_TUPLE = (1, 4, 21)


def encode_letters(text, *, base=1, fixed_width=False):
    values = [ord(character) - ord("A") + base for character in text]
    if fixed_width:
        return "".join(f"{value:02d}" for value in values)
    return "".join(str(value) for value in values)


def indexed_letters(text, positions, *, one_based):
    offset = 1 if one_based else 0
    return "".join(text[position - offset] for position in positions)


def suffix_cuts_with_length(text, target_length, *, base, fixed_width):
    return tuple(
        cut
        for cut in range(len(text) + 1)
        if len(
            encode_letters(
                text[cut:], base=base, fixed_width=fixed_width
            )
        )
        == target_length
    )


def aligned_instruction_slices(digits):
    offset = 0
    slices = []
    for instruction in INSTRUCTION_PARTS:
        end = offset + len(instruction)
        slices.append(
            {
                "instruction": instruction,
                "start": offset,
                "end": end,
                "digits": digits[offset:end],
            }
        )
        offset = end
    assert offset == len(digits)
    return tuple(slices)


def audit():
    output = subtract_mod26(DBBI, VALIDATION_ANSWER)
    assert output == EXPECTED_OUTPUT
    assert len(output) == 91
    assert output[EXPECTED_START_0 : EXPECTED_START_0 + COLUMNS] == ROW_TEXT

    lexical_cut = EXPECTED_START_0 + len(WORD)
    native_row_cut = EXPECTED_START_0 + len(ROW_TEXT)
    tail64 = output[lexical_cut:]
    tail63 = output[native_row_cut:]
    assert len(tail64) == 64
    assert len(tail63) == 63

    conventions = {}
    for base, base_label in ((0, "a0z25"), (1, "a1z26")):
        for fixed_width, width_label in (
            (False, "unpadded"),
            (True, "fixed_width_2"),
        ):
            label = f"{base_label}_{width_label}"
            encoded = encode_letters(
                tail64, base=base, fixed_width=fixed_width
            )
            conventions[label] = {
                "tail64_digit_length": len(encoded),
                "suffix_cuts_with_103_digits": suffix_cuts_with_length(
                    output,
                    EXPECTED_INSTRUCTION_LENGTH,
                    base=base,
                    fixed_width=fixed_width,
                ),
            }

    digits = encode_letters(tail64, base=1, fixed_width=False)
    assert digits == EXPECTED_A1Z26_STREAM
    assert len(digits) == EXPECTED_INSTRUCTION_LENGTH
    assert conventions["a1z26_unpadded"]["suffix_cuts_with_103_digits"] == (
        lexical_cut,
    )
    assert all(
        not result["suffix_cuts_with_103_digits"]
        for label, result in conventions.items()
        if label != "a1z26_unpadded"
    )

    native_digits = encode_letters(tail63, base=1, fixed_width=False)
    assert len(native_digits) == 101

    instruction_text = "".join(INSTRUCTION_PARTS)
    assert len(instruction_text) == EXPECTED_INSTRUCTION_LENGTH
    slices = aligned_instruction_slices(digits)
    enter_slice = next(
        item for item in slices if item["instruction"] == "enter"
    )
    assert enter_slice == {
        "instruction": "enter",
        "start": 86,
        "end": 91,
        "digits": "13224",
    }
    occurrences_13224 = tuple(
        offset
        for offset in range(len(digits) - len("13224") + 1)
        if digits[offset : offset + len("13224")] == "13224"
    )
    assert occurrences_13224 == (86,)

    one_based = indexed_letters(output, POSITION_TUPLE, one_based=True)
    zero_based = indexed_letters(output, POSITION_TUPLE, one_based=False)
    assert one_based == "VIC"
    assert zero_based == "OJY"

    return {
        "output": output,
        "position_tuple": POSITION_TUPLE,
        "one_based_letters": one_based,
        "zero_based_letters": zero_based,
        "lexical_cut": lexical_cut,
        "native_row_cut": native_row_cut,
        "tail64": tail64,
        "tail63": tail63,
        "a1z26_digits": digits,
        "native_tail_a1z26_digit_length": len(native_digits),
        "instruction_text": instruction_text,
        "instruction_slices": slices,
        "enter_slice": enter_slice,
        "occurrences_13224": occurrences_13224,
        "conventions": conventions,
    }


def self_test():
    result = audit()
    assert result["conventions"] == {
        "a0z25_unpadded": {
            "tail64_digit_length": 100,
            "suffix_cuts_with_103_digits": (),
        },
        "a0z25_fixed_width_2": {
            "tail64_digit_length": 128,
            "suffix_cuts_with_103_digits": (),
        },
        "a1z26_unpadded": {
            "tail64_digit_length": 103,
            "suffix_cuts_with_103_digits": (27,),
        },
        "a1z26_fixed_width_2": {
            "tail64_digit_length": 128,
            "suffix_cuts_with_103_digits": (),
        },
    }


def main():
    result = audit()
    print(
        f"{{1,4,21}}: one-based={result['one_based_letters']}; "
        f"zero-based={result['zero_based_letters']}"
    )
    print(
        f"YOUWON lexical tail: {len(result['tail64'])} letters -> "
        f"{len(result['a1z26_digits'])} unpadded A1Z26 digits"
    )
    print(
        f"YOUWONX native-row tail: {len(result['tail63'])} letters -> "
        f"{result['native_tail_a1z26_digit_length']} unpadded A1Z26 digits"
    )
    for label, details in result["conventions"].items():
        print(
            f"{label}: tail digits={details['tail64_digit_length']}; "
            f"all 103-digit suffix cuts={details['suffix_cuts_with_103_digits']}"
        )
    for item in result["instruction_slices"]:
        print(f"{item['instruction']}: {item['digits']}")
    print("13224 occurs once, at offset 86, exactly under ENTER.")
    print(
        "Verdict: exact convention-sensitive structural alignment; the "
        "non-native YOUWON|X boundary and EO interpretation remain unconfirmed."
    )


if __name__ == "__main__":
    main()
