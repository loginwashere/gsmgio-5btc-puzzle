#!/usr/bin/env python3
"""Phase 386: independently verifies the community "btcseed" Bifid-decode
theory and checks it against JRK's 2023-08-03 "Are you really looking for
just the btc...?" hint (Telegram message `8774`, sender "Jrk Bgrt",
authenticated directly against the raw export).

**Origin, traced from the raw export, not assumed:** the theory was first
posted by "Sycorax" on 2025-06-12 (message `43248`), over a year before this
audit, and circulated on and off through 2026-01. It is not new. The
Stage-1 keyword sweep (`telegram_export_keyword_sweep.py`) technically
contains both the origin message (`43248`) and the message that names the
result outright (`43671`, "[dbbi] and [faed] already deciphered into
'btcseed...'") -- both match the pre-registered `dbbi`/`faed` keywords --
but that sweep returns 1,828 hits and was explicitly scoped (per its own
docstring) to a different question, the 31-character prime-walk consumption
question. The only trace of this thread that reached this project's more
closely-reviewed material is one tangential image caption in
`doc/GSMG_TELEGRAM_MEDIA_SHORTLIST.md` (message `61439`, "dbbi has the same
length as the first string in btcseed") -- never followed up. `bifid` and
`btcseed` were never in the pre-registered keyword list at all.

**The construction, reproduced independently:** take `DBBI`'s own first 13
characters, de-duplicate in order (`dbbibfbhccbeg` -> `dbifhceg`), fill the
rest of a 5x5 grid with the remaining alphabet (`J` dropped, the standard
Bifid convention) -> keyed alphabet `DBIFHCEGAKLMNOPQRSTUVWXYZ`. Bifid-
decrypt `FAED` as one 570-character block (not sub-divided into periods) in
row-column reading order. This script re-implements Bifid decryption from
scratch (no dependency on the community's own tooling or the dCode web
tool) and confirms the output is exactly reproducible: 570 characters,
starting with `BTCSEED`.

**What does NOT hold up, checked directly against the real output:**
- A separately-circulated claim (`doc/GSMG_TELEGRAM_MEDIA_SHORTLIST.md`
  message `61439`) that the segment before the decode's one `Z` character
  is the same length as `DBBI` (91 chars) is false: it is **97** characters.
- The "1 in 8 billion" improbability figure repeated in the chat (messages
  `43451`, `43678`, `44024`) is consistent with a naive `25^7`-style
  uniform-letter estimate. The actual decode output is heavily skewed (this
  script computes the true empirical letter frequencies: `C`, `D`, `E`, `B`
  alone make up 57% of all 570 output characters, a mechanical consequence
  of feeding FAED's own 9-symbol alphabet through a fixed keyed grid) --
  under those real frequencies a same-position 7-character match is many
  orders of magnitude more likely than 1-in-8-billion, before even
  accounting for the multiple techniques (Bifid, Trifid, XOR) and keyword
  lengths the chat shows were tried in the same session (message `43258`).
- No coherent continuation was ever found in the remaining 563 characters,
  across 14+ months of intermittent community effort (message `43677`:
  "the next 563 characters are going to be hard to understand").

This script does not search for a continuation itself -- that would be an
open-ended, unbounded decode search this project's own discipline rejects.
It closes the specific, bounded question asked: is the decode mechanically
real, and do the improbability arguments for treating it as an intentional
plaintext hold up.

**Addendum (same day):** does the 570-character output look like it is split
into several deliberate word-like parts (as "BTCSEED" at the very start
suggests), or does it read as one continuous noise stream? Substring-scanned
the full output against the system dictionary (`/usr/share/dict/words`,
already this project's established convention -- see
`salvation_anagram_audit.py`/`salphaseion_aphelion_anagram_audit.py`) for
every embedded word of length 4-12. Result: 13 hits (`seed` at position 3 --
the tail of `btcseed` -- then `medea`, `dead`, `dues`, `rene`, `cubs`,
`endue`, `back`, `bsds`, `bier`, `geld`, `meld`/`melds`, spread roughly
evenly through the remaining 567 characters, not clustered near the start).
Generated 200 random strings from the decode's own empirical letter
frequencies and ran the identical scan: mean 9.82 hits, population stdev
3.63. The real decode's 13 hits sits under 1 standard deviation above that
mean -- statistically unremarkable. The output does not show deliberate
word-segmentation; it has exactly the background rate of incidental
dictionary-word substrings this alphabet's letter composition predicts.
`BTCSEED` is not distinguishable in kind from `GELD`/`BIER`/`MELD` found
elsewhere -- it is simply the one hit that is thematically loaded (`btc`
immediately precedes it), which is why people notice it and not the others.
"""

import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402

SYSTEM_DICT_PATH = Path("/usr/share/dict/words")
WORD_SCAN_MIN_LEN = 4
WORD_SCAN_MAX_LEN = 12
BASELINE_TRIALS = 200
BASELINE_SEED = 12345

JRK_QUOTE_MESSAGE_ID = 8774
JRK_QUOTE_DATE = "2023-08-03T22:51:33"
JRK_QUOTE_SENDER = "Jrk Bgrt"
JRK_QUOTE_TEXT = "Are you really looking for just the btc...?"

ORIGIN_MESSAGE_ID = 43248
ORIGIN_SENDER = "Sycorax"
ORIGIN_DATE = "2025-06-12T03:30:31"

NAMED_RESULT_MESSAGE_ID = 43671
FALSE_LENGTH_COINCIDENCE_MESSAGE_ID = 61439
NAIVE_PROBABILITY_MESSAGE_IDS = (43451, 43678, 44024)

ALPHABET_NO_J = "ABCDEFGHIKLMNOPQRSTUVWXYZ"


def build_grid(keyword_source):
    prefix = []
    for ch in keyword_source.upper():
        if ch not in prefix:
            prefix.append(ch)
    grid_letters = prefix + [c for c in ALPHABET_NO_J if c not in prefix]
    assert len(grid_letters) == 25, grid_letters
    grid, pos = {}, {}
    for i, ch in enumerate(grid_letters):
        r, c = divmod(i, 5)
        grid[(r, c)] = ch
        pos[ch] = (r, c)
    return "".join(grid_letters), grid, pos


def bifid_decrypt(ciphertext, pos, grid):
    letters = [ch.upper() for ch in ciphertext if ch.isalpha()]
    letters = ["I" if ch == "J" else ch for ch in letters]
    coords = []
    for ch in letters:
        r, c = pos[ch]
        coords.append(r)
        coords.append(c)
    n = len(letters)
    rows, cols = coords[:n], coords[n:]
    return "".join(grid[(r, c)] for r, c in zip(rows, cols))


def load_dictionary(dict_path=SYSTEM_DICT_PATH):
    words = set()
    with dict_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            word = line.strip()
            if word.isalpha():
                words.add(word.lower())
    return words


def find_embedded_words(text, dictionary, min_len=WORD_SCAN_MIN_LEN, max_len=WORD_SCAN_MAX_LEN):
    lowered = text.lower()
    n = len(lowered)
    hits = []
    for i in range(n):
        for length in range(min_len, min(max_len, n - i) + 1):
            substring = lowered[i:i + length]
            if substring in dictionary:
                hits.append((i, substring))
    return hits


def random_letter_baseline(text, dictionary, trials=BASELINE_TRIALS, seed=BASELINE_SEED):
    freq = Counter(text.lower())
    letters = list(freq.keys())
    weights = [freq[ch] for ch in letters]
    rng = random.Random(seed)
    counts = []
    for _ in range(trials):
        sample = "".join(rng.choices(letters, weights=weights, k=len(text)))
        counts.append(len(find_embedded_words(sample, dictionary)))
    return counts


def audit():
    keyword_source = DBBI[:13]
    grid_keyword, grid, pos = build_grid(keyword_source)
    decoded = bifid_decrypt(FAED, pos, grid)

    dictionary = load_dictionary()
    embedded_words = find_embedded_words(decoded, dictionary)
    baseline_counts = random_letter_baseline(decoded, dictionary)

    z_positions = [i for i, ch in enumerate(decoded) if ch == "Z"]
    pre_z_length = z_positions[0] if z_positions else None

    freq = Counter(decoded)
    total = len(decoded)
    top4 = freq.most_common(4)
    top4_share = sum(count for _, count in top4) / total

    target = "BTCSEED"
    naive_uniform_probability = 25 ** -len(target)
    empirical_probability = 1.0
    for ch in target:
        empirical_probability *= freq[ch] / total

    return {
        "grid_keyword": grid_keyword,
        "keyword_source": keyword_source,
        "decoded": decoded,
        "decoded_length": len(decoded),
        "starts_with_btcseed": decoded.startswith(target),
        "z_count": len(z_positions),
        "pre_z_length": pre_z_length,
        "dbbi_length": len(DBBI),
        "pre_z_matches_dbbi_length": pre_z_length == len(DBBI),
        "top4_letters": top4,
        "top4_share": top4_share,
        "naive_uniform_probability": naive_uniform_probability,
        "empirical_same_position_probability": empirical_probability,
        "embedded_words": embedded_words,
        "embedded_word_count": len(embedded_words),
        "baseline_mean": statistics.mean(baseline_counts),
        "baseline_stdev": statistics.pstdev(baseline_counts),
        "baseline_min": min(baseline_counts),
        "baseline_max": max(baseline_counts),
    }


def self_test():
    report = audit()

    assert report["grid_keyword"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"
    assert report["keyword_source"] == "dbbibfbhccbeg"
    assert report["decoded_length"] == 570
    assert report["starts_with_btcseed"] is True
    assert report["decoded"].startswith("BTCSEEDDEOEMCKEADHBSCHDKBDCSDKDVBXCPCOCHCRDIC")

    # The claimed DBBI-length coincidence (message 61439) does not hold.
    assert report["z_count"] == 1
    assert report["pre_z_length"] == 97
    assert report["dbbi_length"] == 91
    assert report["pre_z_matches_dbbi_length"] is False

    # The output alphabet is heavily skewed, undermining a uniform-letter
    # probability model for how surprising the "BTCSEED" prefix really is.
    top4_letters = {letter for letter, _count in report["top4_letters"]}
    assert top4_letters == {"C", "D", "E", "B"}
    assert report["top4_share"] > 0.55

    assert report["empirical_same_position_probability"] > 100 * report["naive_uniform_probability"]

    # Addendum: embedded-word density is not unusual -- the output does not
    # look deliberately split into parts.
    assert report["embedded_word_count"] == 13
    found_words = {word for _pos, word in report["embedded_words"]}
    assert found_words == {
        "seed", "medea", "dead", "dues", "rene", "cubs",
        "endue", "back", "bsds", "bier", "geld", "meld", "melds",
    }
    seed_hit = next(pos for pos, word in report["embedded_words"] if word == "seed")
    assert seed_hit == 3
    other_positions = [pos for pos, word in report["embedded_words"] if word != "seed"]
    assert min(other_positions) > 100  # not clustered near the start
    assert report["baseline_mean"] == 9.82
    assert abs(report["baseline_stdev"] - 3.628718782159896) < 1e-9
    # Observed count is under 1 stdev above the random-letter baseline mean.
    assert report["embedded_word_count"] < report["baseline_mean"] + report["baseline_stdev"]

    print(
        f"[*] self-test OK: Bifid-decrypted FAED (grid={report['grid_keyword']}) "
        f"reproduces the community's 'BTCSEED' prefix exactly; pre-Z segment is "
        f"{report['pre_z_length']} chars (not DBBI's {report['dbbi_length']}, "
        f"the claimed coincidence is false); top-4 output letters "
        f"{sorted(top4_letters)} cover {report['top4_share']:.0%} of the output, "
        f"vs. naive-uniform p={report['naive_uniform_probability']:.2e} the "
        f"empirical same-position estimate is p="
        f"{report['empirical_same_position_probability']:.2e}; "
        f"{report['embedded_word_count']} embedded dictionary words found "
        f"vs. random-letter baseline mean {report['baseline_mean']:.2f} "
        f"(stdev {report['baseline_stdev']:.2f}) -- unremarkable, no "
        f"deliberate word-segmentation structure"
    )
    return report


def main():
    import argparse

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
