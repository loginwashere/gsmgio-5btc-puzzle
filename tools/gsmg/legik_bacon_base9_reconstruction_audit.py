#!/usr/bin/env python3
"""Reconstructs and closes a community lead flagged but never actually
checked by this project: message 17790 (2023-12-19, solver "Legik",
`doc/telegram_shortlist_fullsize/17790.txt`), captioned "it turned out
something like the Bacon cipher" against DBBI, with an attached data file
containing four derived strings (`one`, `one9`, `one2`, `oneAB`). The
shortlist triage flagged this message by keyword but the actual claim was
never reproduced or verified anywhere in FINDINGS.md (`grep -i bacon` over
the whole file returns zero hits before this phase) -- three years sitting
unchecked, not closed.

Reconstruction (all four relationships verified exactly against the raw
attachment before this docstring was written):

1. `one`   = DBBI's raw 91-symbol string.
2. `one9`  = per-character digit substitution a=0,b=1,...,i=8 -- a genuine
             base-9 mapping. NOT the same convention as this puzzle's own
             established `a1i9` (a=1...i=9) used elsewhere in SalPhaseIon's
             z-delimited segments; Legik used his own zero-indexed version.
3. `one2`  = the entire 91-digit `one9` string interpreted as ONE giant
             base-9 integer (`int(one9, 9)`), converted whole to binary.
4. `oneAB` = `one2` with 0->a, 1->b (a Baconian-looking two-symbol
             relabeling).

Why this doesn't hold up as a real Bacon-cipher path, checked directly
rather than assumed from the surface resemblance:

- A real Baconian cipher encodes each plaintext letter as a fixed 5-bit
  A/B group. DBBI's resulting bit length (287) is not a multiple of 5.
- Converting all 91 digits as ONE base-9 integer before taking the binary
  representation is positional arithmetic across the whole number at once.
  Since 9 is not a power of 2, there is no bit offset where "these bits
  came from this one original character" -- the operation destroys
  per-symbol correspondence rather than preserving it, unlike a real
  per-character encoding (e.g. each digit 0-8 -> its own fixed-width
  binary group, which would at least stay aligned).
- Applying the identical method to FAED (570 symbols) gives 1807 bits --
  also not a multiple of 5 (remainder 2, same remainder as DBBI's 287,
  which is a property of the conversion method rather than either
  ciphertext's specific length).

Reproduce with:
    python3 tools/gsmg/legik_bacon_base9_reconstruction_audit.py --self-test
    python3 tools/gsmg/legik_bacon_base9_reconstruction_audit.py
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import data  # noqa: E402

DBBI = data.DBBI if hasattr(data, "DBBI") else None
FAED = data.FAED

# Legik's original attachment (doc/telegram_shortlist_fullsize/17790.txt),
# reproduced verbatim for the self-test's ground truth.
LEGIK_ONE = (
    "dbbibfbhccbegbihabebeihbeggegebebbgehhebhhfbabfdhbeffcdbbfcccg"
    "bfbeeggecbedcibfbffgigbeeeabe"
)
LEGIK_ONE9 = (
    "31181517221461870141487146646414116477417751015371455231152226"
    "15144664214328151556861444014"
)
LEGIK_ONE2 = (
    "1111010111010110100010001011000111100010001011101011000000010"
    "0111001011100100001100001111011110100001100101101011010101010"
    "101000111111110000010101111111000001101011001010011101111101"
    "001001011100001110111000111100001011100100011010000110101100"
    "001011001101001101100001101101010010100010011"
)
LEGIK_ONEAB = LEGIK_ONE2.replace("0", "a").replace("1", "b")

A0I8 = {chr(ord("a") + i): str(i) for i in range(9)}


def base9_digits(symbols: str) -> str:
    return "".join(A0I8[c] for c in symbols)


def base9_giant_int_binary(symbols: str) -> str:
    digits = base9_digits(symbols)
    n = int(digits, 9)
    return bin(n)[2:]


def report(name: str, symbols: str) -> None:
    b = base9_giant_int_binary(symbols)
    rem = len(b) % 5
    print(f"{name}: {len(symbols)} symbols -> {len(b)} bits "
          f"(mod 5 = {rem}, {'DIVIDES EVENLY' if rem == 0 else 'does not divide evenly'})")


def self_test() -> None:
    assert base9_digits(LEGIK_ONE) == LEGIK_ONE9, "a=0..i=8 mapping mismatch"
    n = int(LEGIK_ONE9, 9)
    b = bin(n)[2:]
    assert b == LEGIK_ONE2, "base-9-giant-int-to-binary mismatch"
    ab = LEGIK_ONE2.replace("0", "a").replace("1", "b")
    assert ab == LEGIK_ONEAB, "0/1 -> a/b relabeling mismatch"
    print("self-test OK: Legik's one/one9/one2/oneAB relationships reproduced exactly")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    if DBBI:
        report("DBBI", DBBI)
    report("FAED", FAED)
    print()
    print("Verdict: closed negative for both objects. The base-9-giant-integer "
          "conversion is not a per-character transform (9 is not a power of 2), "
          "so it cannot preserve letter-by-letter structure regardless of bit "
          "count; failing the /5 check on both objects independently confirms "
          "this is a property of the method, not either ciphertext's length.")


if __name__ == "__main__":
    main()
