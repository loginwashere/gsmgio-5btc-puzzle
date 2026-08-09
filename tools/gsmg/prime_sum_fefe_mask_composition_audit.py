#!/usr/bin/env python3
"""Compose the verified 400/401/73 list with the FE byte mask, without selectors.

The only declared operation is the one verified in Phase 195: apply repeated
``0xFE`` to every byte of every list value.  All three values receive the same
operation.  Fixed-width and minimal-width big/little-endian encodings are
checked for invariance; no byte, value, direction, or arithmetic result is
selected after inspection.

The audit also calibrates the recognized ``144,144,72`` relation over the
complete color-profile family.  It distinguishes the relevant conditioned
family (FEFE's event/prime is already fixed) from a larger descriptive family
that also lets the exceptional event occupy any of the 23 prime positions.
"""

import argparse
import itertools
from fractions import Fraction
from math import comb

from first_piece_prime_sum_reconstruction import audit as reconstruct_sums


def byte_width(value):
    return max(1, (value.bit_length() + 7) // 8)


def repeated_fe_mask(value, width=None, byteorder="big"):
    width = byte_width(value) if width is None else width
    if value >= 1 << (8 * width):
        raise ValueError(f"value {value} does not fit in {width} bytes")
    encoded = value.to_bytes(width, byteorder)
    masked = bytes(byte & 0xFE for byte in encoded)
    return {
        "width": width,
        "byteorder": byteorder,
        "input_hex": encoded.hex().upper(),
        "mask_hex": (b"\xFE" * width).hex().upper(),
        "output_hex": masked.hex().upper(),
        "output_value": int.from_bytes(masked, byteorder),
    }


def scalar_lsb_mask(value):
    """Control alternative: clear only the integer's single terminal bit."""
    return value & ~1


def assignment_calibration(primes, fefe_prime, yellow_count=8):
    remaining = list(primes)
    remaining.remove(fefe_prime)
    total = sum(remaining)
    target = repeated_fe_mask(fefe_prime)["output_value"] * 2
    successes = 0
    near_balances = 0
    output_pairs = set()
    for yellow_values in itertools.combinations(remaining, yellow_count):
        yellow = sum(yellow_values)
        blue = total - yellow
        if abs(blue - yellow) <= 1:
            near_balances += 1
        if (
            repeated_fe_mask(blue)["output_value"] == target
            and repeated_fe_mask(yellow)["output_value"] == target
        ):
            successes += 1
            output_pairs.add((blue, yellow))
    denominator = comb(len(remaining), yellow_count)
    return {
        "successes": successes,
        "near_balances": near_balances,
        "total": denominator,
        "rate": Fraction(successes, denominator),
        "successful_sum_pairs": tuple(sorted(output_pairs)),
    }


def floating_fefe_calibration(primes, yellow_count=8):
    rows = []
    for fefe_prime in primes:
        report = assignment_calibration(primes, fefe_prime, yellow_count)
        if report["successes"]:
            rows.append({"fefe_prime": fefe_prime, **report})
    total = len(primes) * comb(len(primes) - 1, yellow_count)
    successes = sum(row["successes"] for row in rows)
    return {
        "successful_fefe_rows": tuple(rows),
        "successes": successes,
        "total": total,
        "rate": Fraction(successes, total),
    }


def audit():
    reconstruction = reconstruct_sums()
    sums = reconstruction["fitted_sums"]
    ordered_values = (sums["B"], sums["Y"], sums["F"])
    encodings = {
        f"{width}byte_{byteorder}": tuple(
            repeated_fe_mask(value, width, byteorder)
            for value in ordered_values
        )
        for width in (2, 3)
        for byteorder in ("big", "little")
    }
    minimal = tuple(repeated_fe_mask(value) for value in ordered_values)
    outputs = tuple(row["output_value"] for row in minimal)
    scalar_control = tuple(scalar_lsb_mask(value) for value in ordered_values)
    primes = tuple(record["prime"] for record in reconstruction["fitted_records"])
    fixed = assignment_calibration(primes, sums["F"])
    floating = floating_fefe_calibration(primes)

    return {
        "input_values_BYF": ordered_values,
        "minimal_encodings": minimal,
        "fixed_encodings": encodings,
        "repeated_fe_outputs_BYF": outputs,
        "equal_halves": outputs[0] == outputs[1],
        "fefe_is_half": outputs[0] == 2 * outputs[2],
        "scalar_lsb_only_control_BYF": scalar_control,
        "fixed_fefe_calibration": fixed,
        "floating_fefe_calibration": floating,
    }


def self_test():
    report = audit()
    assert report["input_values_BYF"] == (401, 400, 73)
    assert report["repeated_fe_outputs_BYF"] == (144, 144, 72)
    assert report["equal_halves"] is True
    assert report["fefe_is_half"] is True
    assert report["scalar_lsb_only_control_BYF"] == (400, 400, 72)
    for rows in report["fixed_encodings"].values():
        assert tuple(row["output_value"] for row in rows) == (144, 144, 72)
    fixed = report["fixed_fefe_calibration"]
    assert fixed["successes"] == fixed["near_balances"] == 813
    assert fixed["total"] == 319_770
    assert fixed["successful_sum_pairs"] == ((400, 401), (401, 400))
    floating = report["floating_fefe_calibration"]
    assert floating["successes"] == 813
    assert floating["total"] == 7_354_710
    assert tuple(
        row["fefe_prime"] for row in floating["successful_fefe_rows"]
    ) == (73,)
    print("[*] self-test OK: selector-free FE composition and calibrations reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    print(f"[*] input B/Y/F sums: {report['input_values_BYF']}")
    print(f"[*] repeated-FE outputs: {report['repeated_fe_outputs_BYF']}")
    print(f"[*] scalar-LSB-only control: {report['scalar_lsb_only_control_BYF']}")
    print(
        f"[*] equal halves={report['equal_halves']}; "
        f"FEFE channel is half={report['fefe_is_half']}"
    )
    fixed = report["fixed_fefe_calibration"]
    print(
        "[*] fixed-FEFE profile calibration: "
        f"{fixed['successes']}/{fixed['total']} = {float(fixed['rate']):.9f}; "
        f"near-balance count={fixed['near_balances']}"
    )
    floating = report["floating_fefe_calibration"]
    print(
        "[*] floating-FEFE descriptive calibration: "
        f"{floating['successes']}/{floating['total']} = "
        f"{float(floating['rate']):.9f}; successful FE primes="
        f"{tuple(row['fefe_prime'] for row in floating['successful_fefe_rows'])}"
    )
    print(
        "[*] verdict: applying FE uniformly produces 144/144/72 without a "
        "selector and is encoding-width/endianness invariant. Conditioned on "
        "the fixed FE event, this is exactly the same 813-member family as the "
        "400/401 near-balance, so it adds no independent statistical support."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
