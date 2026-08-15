#!/usr/bin/env python3
"""Minimal unnormalized-rANS feasibility audit for the `anstoo` hypothesis.

The clue reading is explicitly low provenance: prior work found zero
creator-authored explanations of literal `anstoo`.  This module tests only the
fully determined rANS core:

  * DBBI's exact a-i histogram supplies frequencies and cumulative ranges;
  * FAED as one whole base-9 integer supplies the final state;
  * canonical terminal states 0 and 1, plus whole-base-9 DBBI as paired state;
  * fixed diagnostic output lengths 91 and 570.

Renormalized rANS/tANS is not guessed: the source supplies no lower bound,
radix digit direction, normalized table size, symbol spread, or initial state.
"""

import argparse
import json
from collections import Counter

from data import DBBI, FAED


ALPHABET = "abcdefghi"
FIXED_LENGTHS = (len(DBBI), len(FAED))


def base9_integer(stream):
    value = 0
    for symbol in stream:
        digit = ord(symbol) - ord("a")
        if not 0 <= digit < 9:
            raise ValueError(f"symbol outside a-i: {symbol!r}")
        value = value * 9 + digit
    return value


def base9_digit_length(value):
    """Return a compact size diagnostic without printing enormous states."""
    if value == 0:
        return 1
    digits = 0
    while value:
        value //= 9
        digits += 1
    return digits


def frequency_model(stream=DBBI):
    counts = Counter(stream)
    frequencies = tuple(counts[symbol] for symbol in ALPHABET)
    cumulative = []
    running = 0
    for frequency in frequencies:
        cumulative.append(running)
        running += frequency
    return frequencies, tuple(cumulative), running


def decode_symbol(state, frequencies, cumulative, total):
    slot = state % total
    for symbol, (frequency, start) in enumerate(zip(frequencies, cumulative)):
        if start <= slot < start + frequency:
            previous_state = frequency * (state // total) + (slot - start)
            return symbol, previous_state
    raise AssertionError("rANS slot is outside cumulative model")


def encode_symbol(state, symbol, frequencies, cumulative, total):
    frequency = frequencies[symbol]
    start = cumulative[symbol]
    return (state // frequency) * total + start + (state % frequency)


def encode_sequence(sequence, initial_state, frequencies, cumulative, total):
    state = initial_state
    for symbol in reversed(sequence):
        state = encode_symbol(state, symbol, frequencies, cumulative, total)
    return state


def decode_fixed(final_state, length, frequencies, cumulative, total):
    state = final_state
    output = []
    for _ in range(length):
        symbol, state = decode_symbol(state, frequencies, cumulative, total)
        output.append(symbol)
    return tuple(output), state


def decode_until(final_state, terminal_state, frequencies, cumulative, total,
                 maximum_steps=5000):
    state = final_state
    output = []
    seen = set()
    reason = None
    for _ in range(maximum_steps + 1):
        if state == terminal_state:
            reason = "reached_terminal"
            break
        if state < terminal_state:
            reason = "undershot_terminal"
            break
        if state in seen:
            reason = "state_cycle_or_stall"
            break
        seen.add(state)
        symbol, next_state = decode_symbol(state, frequencies, cumulative, total)
        output.append(symbol)
        state = next_state
    else:
        reason = "step_limit"
    reached = state == terminal_state
    roundtrip = (
        encode_sequence(output, terminal_state, frequencies, cumulative, total)
        == final_state
        if reached else False
    )
    return {
        "terminal_state_label": None,
        "reached": reached,
        "reason": reason,
        "decoded_length": len(output),
        "decoded_text": "".join(chr(97 + symbol) for symbol in output),
        "decoded_prefix": "".join(chr(97 + symbol) for symbol in output[:120]),
        "residual_state": state,
        "exact_reencode": roundtrip,
    }


def audit():
    frequencies, cumulative, total = frequency_model()
    final_state = base9_integer(FAED)
    dbbi_state = base9_integer(DBBI)
    terminal_states = (
        ("zero", 0),
        ("one", 1),
        ("dbbi_whole_base9", dbbi_state),
    )
    terminal_rows = []
    for label, terminal in terminal_states:
        row = decode_until(
            final_state, terminal, frequencies, cumulative, total
        )
        row["terminal_state_label"] = label
        row["decoded_equals_dbbi"] = row["decoded_text"] == DBBI
        row["decoded_equals_faed"] = row["decoded_text"] == FAED
        row["residual_base9_digits"] = base9_digit_length(row["residual_state"])
        row["degenerate_universal_sink"] = label == "zero"
        terminal_rows.append(row)

    fixed_rows = []
    for length in FIXED_LENGTHS:
        decoded, residual = decode_fixed(
            final_state, length, frequencies, cumulative, total
        )
        text = "".join(chr(97 + symbol) for symbol in decoded)
        fixed_rows.append({
            "output_length": length,
            "decoded_text": text,
            "decoded_prefix": text[:120],
            "residual_state": residual,
            "residual_base9_digits": base9_digit_length(residual),
            "residual_equals_zero": residual == 0,
            "residual_equals_one": residual == 1,
            "residual_equals_dbbi_state": residual == dbbi_state,
            "decoded_equals_same_length_source": text == (
                DBBI if length == len(DBBI) else FAED
            ),
            "reencode_with_residual_is_exact": encode_sequence(
                decoded, residual, frequencies, cumulative, total
            ) == final_state,
            "reencode_with_residual_is_tautological": True,
        })

    hits = tuple(
        row["terminal_state_label"]
        for row in terminal_rows
        if row["reached"] and row["exact_reencode"]
    )
    nondegenerate_hits = tuple(
        row["terminal_state_label"]
        for row in terminal_rows
        if (row["reached"] and row["exact_reencode"]
            and not row["degenerate_universal_sink"])
    )
    return {
        "provenance": {
            "literal_anstoo_creator_explanations": 0,
            "ans_too_is_new_wordplay": True,
            "reference": "FINDINGS.md Phase 102",
        },
        "model": {
            "kind": "unnormalized static rANS core",
            "frequencies": frequencies,
            "cumulative": cumulative,
            "total": total,
            "alphabet_order": ALPHABET,
            "final_state": "whole forward FAED base-9 integer",
        },
        "missing_for_renormalized_rans_or_tans": {
            "normalization_lower_bound": True,
            "renormalization_radix_and_digit_direction": True,
            "normalized_table_size": True,
            "tans_symbol_spread": True,
            "initial_or_terminal_state": True,
            "decoded_length_or_eos": True,
        },
        "terminal_rows": tuple(terminal_rows),
        "fixed_length_rows": tuple(fixed_rows),
        "exact_terminal_roundtrip_hits": hits,
        "nondegenerate_terminal_roundtrip_hits": nondegenerate_hits,
        "promotion": {
            "required": "source selects terminal/length and exact re-encoding is non-ambiguous",
            "promoted": False,
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    frequencies, cumulative, total = frequency_model()
    plaintext = tuple(ALPHABET.index(symbol) for symbol in "abcdefedcba")
    final_state = encode_sequence(plaintext, 1, frequencies, cumulative, total)
    decoded, residual = decode_fixed(
        final_state, len(plaintext), frequencies, cumulative, total
    )
    assert decoded == plaintext
    assert residual == 1
    assert encode_sequence(decoded, residual, frequencies, cumulative, total) == final_state
    report = audit()
    assert report["model"]["total"] == len(DBBI) == 91
    assert len(report["terminal_rows"]) == 3
    assert len(report["fixed_length_rows"]) == 2
    assert all(row["reencode_with_residual_is_exact"]
               for row in report["fixed_length_rows"])
    assert report["exact_terminal_roundtrip_hits"] == ("zero",)
    assert report["nondegenerate_terminal_roundtrip_hits"] == ()
    assert not report["password_oracle_run"]
    print("[*] self-test OK: rANS core roundtrip, three terminals, and fixed-length diagnostics verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] provenance:", report["provenance"])
    print("[*] missing rANS/tANS fields:", report["missing_for_renormalized_rans_or_tans"])
    for row in report["terminal_rows"]:
        print(
            f"[*] terminal={row['terminal_state_label']}: reached={row['reached']} "
            f"reason={row['reason']} decoded_len={row['decoded_length']} "
            f"residual_base9_digits={row['residual_base9_digits']} "
            f"degenerate_sink={row['degenerate_universal_sink']} "
            f"prefix={row['decoded_prefix']!r}"
        )
    for row in report["fixed_length_rows"]:
        print(
            f"[*] fixed n={row['output_length']}: "
            f"residual_base9_digits={row['residual_base9_digits']} "
            f"source_hit={row['decoded_equals_same_length_source']} "
            f"prefix={row['decoded_prefix']!r}"
        )
    print("[*] exact terminal hits:", report["exact_terminal_roundtrip_hits"])
    print("[*] nondegenerate terminal hits:", report["nondegenerate_terminal_roundtrip_hits"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()
