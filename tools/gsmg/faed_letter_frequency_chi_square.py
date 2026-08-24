#!/usr/bin/env python3
"""Chi-square test of FAED's raw a-i letter frequencies against uniform.

Parallels `dbbi_letter_frequency_chi_square.py`. FAED's already-established
escape pair is `{g,i}` (frequency analysis + code-level IC, rank 1/36 --
see `doc/GSMG_OBJECT_FAED.md`), contested by an unresolved `{h,e}` mirror
hypothesis (Gap G-ESC-001, the sharpest unreconciled joint in the macro
chain). This script quantifies how lopsided the raw-frequency evidence is
between those two pairs: it does not resolve the gap (the `{h,e}` argument
is structural/authorial, not a frequency claim), but it shows the frequency
signal offers `{h,e}` almost no support.

df=8 is even, so the chi-square survival function has a closed form
(no scipy dependency needed):
    Q(k, x/2) = e^(-x/2) * sum_{i=0}^{k-1} (x/2)^i / i!   where k = df/2
"""

import math
from collections import Counter

from data import FAED

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


def per_symbol_contributions(counts, alphabet=NINE_SYMS):
    total = sum(counts.get(ch, 0) for ch in alphabet)
    expected = total / len(alphabet)
    return {ch: (counts.get(ch, 0) - expected) ** 2 / expected for ch in alphabet}


def main():
    counts = Counter(FAED)
    chi2, p = chi_square_p_value(counts)
    contrib = per_symbol_contributions(counts)
    print(f"FAED length: {len(FAED)}")
    print("Letter counts:", ", ".join(f"{ch}:{counts.get(ch, 0)}" for ch in NINE_SYMS))
    print(f"chi2 (df=8) = {chi2:.4f}")
    print(f"p-value = {p:.8g}  (~1 in {1 / p:,.0f})")
    gi_share = (contrib["g"] + contrib["i"]) / chi2
    he_share = (contrib["h"] + contrib["e"]) / chi2
    print(f"{{g,i}} share of deviation = {gi_share:.4f}")
    print(f"{{h,e}} share of deviation = {he_share:.4f}")


def _self_test():
    counts = Counter(FAED)
    assert sum(counts.values()) == 570
    assert dict(counts) == {
        "a": 54, "b": 49, "c": 52, "d": 49, "e": 69,
        "f": 57, "g": 107, "h": 58, "i": 75,
    }
    chi2, p = chi_square_p_value(counts)
    assert abs(chi2 - 43.7368) < 1e-3
    assert abs(p - 6.379e-7) < 1e-9
    contrib = per_symbol_contributions(counts)
    assert abs(contrib["g"] - 30.107) < 1e-2
    gi_share = (contrib["g"] + contrib["i"]) / chi2
    he_share = (contrib["h"] + contrib["e"]) / chi2
    assert gi_share > 0.70
    assert he_share < 0.05
    print("self-test OK")


if __name__ == "__main__":
    import sys

    if "--self-test" in sys.argv:
        _self_test()
    else:
        main()
