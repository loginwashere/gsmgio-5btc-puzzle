#!/usr/bin/env python3
"""Chi-square test of DBBI's raw a-i letter frequencies against uniform.

Independent-of-alphabet confirmation of the `{b,e}` escape-pair finding
already established by `checkerboard_code_ic_oracle.py`: if DBBI were drawn
uniformly at random over its 9-symbol alphabet, its observed letter counts
would be this improbable. `b` and `e` account for most (~70%) of the
deviation, which is exactly the signature expected of a straddling
checkerboard's two escape symbols (each escape symbol prefixes every
two-symbol code it participates in, so it appears far more often than a
non-escape symbol).

df=8 is even, so the chi-square survival function has a closed form
(no scipy dependency needed):
    Q(k, x/2) = e^(-x/2) * sum_{i=0}^{k-1} (x/2)^i / i!   where k = df/2
"""

import math
from collections import Counter

from data import DBBI

NINE_SYMS = "abcdefghi"


def chi_square_p_value(counts, alphabet=NINE_SYMS):
    total = sum(counts.get(ch, 0) for ch in alphabet)
    expected = total / len(alphabet)
    chi2 = sum((counts.get(ch, 0) - expected) ** 2 / expected for ch in alphabet)
    df = len(alphabet) - 1
    assert df % 2 == 0, "closed-form survival function below assumes even df"
    k = df // 2
    half = chi2 / 2
    p = math.exp(-half) * sum(half**i / math.factorial(i) for i in range(k))
    return chi2, p


def main():
    counts = Counter(DBBI)
    chi2, p = chi_square_p_value(counts)
    print(f"DBBI length: {len(DBBI)}")
    print("Letter counts:", ", ".join(f"{ch}:{counts.get(ch, 0)}" for ch in NINE_SYMS))
    print(f"chi2 (df=8) = {chi2:.4f}")
    print(f"p-value = {p:.8g}  (~1 in {1 / p:,.0f})")


def _self_test():
    counts = Counter(DBBI)
    assert sum(counts.values()) == 91
    assert dict(counts) == {
        "a": 3, "b": 25, "c": 8, "d": 4, "e": 18,
        "f": 10, "g": 10, "h": 8, "i": 5,
    }
    chi2, p = chi_square_p_value(counts)
    assert abs(chi2 - 40.2418) < 1e-3
    assert abs(p - 2.888e-6) < 1e-8
    # b and e together account for most, though not all, of the deviation.
    per_symbol = {
        ch: (counts.get(ch, 0) - 91 / 9) ** 2 / (91 / 9) for ch in NINE_SYMS
    }
    be_share = (per_symbol["b"] + per_symbol["e"]) / chi2
    assert be_share > 0.65
    print("self-test OK")


if __name__ == "__main__":
    import sys

    if "--self-test" in sys.argv:
        _self_test()
    else:
        main()
