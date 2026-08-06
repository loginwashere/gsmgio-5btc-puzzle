"""Content-agnostic classical cryptanalysis on dbbi/faed: Kasiski examination
(repeated-substring spacing) and a Friedman-style native-IC Monte Carlo baseline.

Neither of these requires guessing a keyword or riddle sentence -- they test
whether there's statistical evidence of a periodic keystream/transposition layer
sitting on top of the already-validated {b,e}/pad25/top_first straddling
checkerboard model, independent of what that layer's key might be.

See doc/GSMG_PUZZLE.md ("Option B: Kasiski/Friedman") for the reasoning. Key
caveat baked into the design: with only a 9-symbol alphabet, chance repeated
substrings are common even in a non-periodic string (birthday-paradox effect),
so raw Kasiski counts alone are not trustworthy here -- everything is compared
against a null baseline (random 9-symbol strings of the same length) rather than
interpreted at face value.
"""
import math
import random
from collections import Counter, defaultdict

from data import DBBI, FAED

random.seed(1234)  # reproducible

# Standard English letter frequencies (%), classic reference table.
ENGLISH_FREQ = {
    "E": 12.70, "T": 9.06, "A": 8.17, "O": 7.51, "I": 6.97, "N": 6.75, "S": 6.33,
    "H": 6.09, "R": 5.99, "D": 4.25, "L": 4.03, "C": 2.78, "U": 2.76, "M": 2.41,
    "W": 2.36, "F": 2.23, "G": 2.02, "Y": 1.97, "P": 1.93, "B": 1.49, "V": 0.98,
    "K": 0.77, "J": 0.15, "X": 0.15, "Q": 0.10, "Z": 0.07,
}

NINE = "abcdefghi"


def merged_freq(drop="J"):
    """Matches cb_common.pad25()'s merge rule: drop letter folded into its
    alphabetically-preceding letter, giving a 25-entry frequency table."""
    merge_into = chr(ord(drop) - 1) if drop != "A" else "B"
    f = dict(ENGLISH_FREQ)
    f[merge_into] = f.get(merge_into, 0) + f.pop(drop)
    assert len(f) == 25
    return f


def index_of_coincidence(s):
    n = len(s)
    if n < 2:
        return 0.0
    counts = Counter(s)
    num = sum(c * (c - 1) for c in counts.values())
    return num / (n * (n - 1))


# ---------- Kasiski examination ----------

def kasiski(s, gram_lens=(3, 4)):
    factor_hits = Counter()
    for glen in gram_lens:
        pos = defaultdict(list)
        for i in range(len(s) - glen + 1):
            pos[s[i:i + glen]].append(i)
        for positions in pos.values():
            if len(positions) < 2:
                continue
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    d = positions[j] - positions[i]
                    for f in range(2, 21):
                        if d % f == 0:
                            factor_hits[f] += 1
    return factor_hits


def null_kasiski_baseline(length, trials=300, gram_lens=(3, 4)):
    """Expected factor-hit counts under a random (non-periodic) 9-symbol string of
    the same length -- the reference everything else gets compared against."""
    agg = Counter()
    for _ in range(trials):
        s = "".join(random.choice(NINE) for _ in range(length))
        for f, c in kasiski(s, gram_lens).items():
            agg[f] += c
    return {f: agg[f] / trials for f in range(2, 21)}


# ---------- Native-IC Monte Carlo baseline for pure single-layer checkerboard ----------

def simulate_native_ic(target_len, trials=20000, drop="J", escapes=("b", "e")):
    """For `trials` random keyword-order boards (matching the validated
    {b,e}/pad25/top_first construction), encode i.i.d. English-frequency-sampled
    plaintext and measure the resulting ciphertext's IC. This is the IC a *pure*
    checkerboard (no extra keystream/transposition) would naturally produce --
    the natural-language letter-frequency skew is the only source of the IC
    elevation above uniform (1/9), since the *specific* letters landing in the
    single-symbol top row are keyword-driven, not frequency-optimized."""
    freq = merged_freq(drop)
    letters = list(freq.keys())
    total = sum(freq.values())
    probs = [freq[c] / total for c in letters]
    idx = {c: i for i, c in enumerate(letters)}

    e1, e2 = escapes
    tops_syms = [c for c in NINE if c not in escapes]

    ics, lens = [], []
    for _ in range(trials):
        order = letters[:]
        random.shuffle(order)
        top_letters, e1_letters, e2_letters = order[:7], order[7:16], order[16:25]

        code = {}
        for k, letter in enumerate(top_letters):
            code[letter] = tops_syms[k]
        for k, letter in enumerate(e1_letters):
            code[letter] = e1 + NINE[k]
        for k, letter in enumerate(e2_letters):
            code[letter] = e2 + NINE[k]

        p_top = sum(probs[idx[l]] for l in top_letters)
        expansion = 2 - p_top  # avg symbols-per-letter for this board
        L = max(1, round(target_len / expansion))

        plaintext = random.choices(letters, weights=probs, k=L)
        cipher = "".join(code[c] for c in plaintext)

        ics.append(index_of_coincidence(cipher))
        lens.append(len(cipher))
    return ics, lens


def summarize(name, ciphertext):
    observed_ic = index_of_coincidence(ciphertext)
    print(f"\n=== {name} (len={len(ciphertext)}, observed IC={observed_ic:.4f}) ===")

    fh = kasiski(ciphertext)
    baseline = null_kasiski_baseline(len(ciphertext))
    print("Kasiski factor hits, observed vs null (random 9-symbol string, same length):")
    ranked = sorted(fh.items(), key=lambda kv: -kv[1])[:8]
    for f, c in ranked:
        b = baseline.get(f, 0)
        flag = "  <-- above null" if c > b * 1.3 else ""
        print(f"  factor {f:2d}: observed={c:5d}  null_baseline={b:7.1f}{flag}")

    ics, _ = simulate_native_ic(len(ciphertext))
    mean_ic = sum(ics) / len(ics)
    sd_ic = math.sqrt(sum((x - mean_ic) ** 2 for x in ics) / len(ics))
    pctile = sum(1 for x in ics if x <= observed_ic) / len(ics) * 100
    z = (observed_ic - mean_ic) / sd_ic
    print(f"Native single-layer-checkerboard IC baseline (n={len(ics)} random-board trials): "
          f"mean={mean_ic:.4f} sd={sd_ic:.4f}")
    print(f"Observed IC {observed_ic:.4f} -> percentile {pctile:.1f}%, z={z:+.2f}")

    ic_random = 1 / 9
    if observed_ic > ic_random:
        est_len = (mean_ic - ic_random) / (observed_ic - ic_random)
        print(f"Classical Friedman formula (Ic_plain = simulated mean): "
              f"estimated key length ~ {est_len:.2f}")
    else:
        print("Observed IC <= 1/9 (uniform) -- Friedman formula not meaningful here.")


if __name__ == "__main__":
    summarize("dbbi", DBBI)
    summarize("faed", FAED)
