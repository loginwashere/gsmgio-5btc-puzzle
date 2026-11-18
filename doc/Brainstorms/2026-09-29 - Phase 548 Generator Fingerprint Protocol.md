# Phase 548 — generator fingerprint of FAED and DBBI

Status at creation: protocol. Written 2026-09-29, before any generator was compared with the real
streams. Everything below is frozen by the execution lock at the end.

## Claim and motivation

Most FAED work since Phase 8 assumes FAED is a nine-symbol checkerboard (or a similar
substitution) over English text, and searches for the key. Phase 412 found that FAED is best
predicted by an independent-symbol model with skewed frequencies and no first-order memory.
Its stop rule did not license a mechanism comparison, because a generic model says nothing about
mechanisms. This phase supplies the missing step. It simulates concrete producers the creator
could have used and asks which of them can produce FAED's statistics, with measured power.

The question is *what kind of object FAED is*, not how to decode it. No decode, key search,
password or oracle is part of this phase.

Justification against Phase 412's stop rule: that rule prevents opening a transform or decode
family on the strength of the IID result. This phase opens none. It calibrates, by simulation,
whether the IID result already excludes the mechanism family most prior phases assumed.

## Streams

- FAED (570 symbols) is **gated**.
- DBBI (91 symbols) is **reported** with the same machinery, but not gated (low power; 23 of its
  25 `b`s belong to the prime-host scaffold, Phase 534).

## Statistics (invariant to relabeling the nine symbols)

For a stream `s` of length `N`, the 14-dimensional statistic vector is:

1. the nine symbol proportions sorted in descending order, first eight kept (8 values);
2. the repeat rate, `P(s_t = s_{t+1})`;
3. the plug-in mutual information of consecutive symbols, in bits;
4. the maximum follow chi-square: for each symbol `x` with at least 5 occurrences in positions
   `1..N-1`, the chi-square of the next-symbol counts after `x` against `n_x` times the
   next-position marginal; take the maximum over `x`;
5. the halves chi-square: the 2 x 9 homogeneity chi-square of first-half vs second-half counts
   (empty columns dropped);
6. the period-2 and period-3 chi-squares: position mod `p` vs symbol, as a `p x 9` contingency
   chi-square (2 values).

## Generators (frozen)

Nine-column straddling checkerboard for G1-G5: symbols 0-6 are single-symbol cells, symbols 7 and
8 are escapes, each followed by one of 9 symbols. That gives 7 + 18 = 25 cells. Stats are
label-invariant, so the choice of escape labels does not matter.

English source: `wordlists/gsmg/cosmic_duality_book_full_text.txt`, with `#` lines dropped,
uppercased, letters only, `J -> I` (25 letters). Each draw takes a random window.

| ID | Generator | Content |
|---|---|---|
| G1 CB-ENG | checkerboard, uniformly random board | English |
| G2 CB-ENG-VIC | checkerboard, the corpus's 7 most frequent letters on the top row (random order), rest random | English |
| G3 CB-HEX | checkerboard, 16 hex characters on 16 random cells | uniform random hex (key-shaped) |
| G4 CB-RAND | checkerboard, random board | uniform random over 25 letters |
| G5 CB-ENG-CHAIN | G1 output, then VIC chain addition mod 9 with a random primer of length 5-10 | English |
| G6 B9-ENG | uppercase letters-only English, each ASCII byte as 3 base-9 digits | English |
| G7 B9-BYTES | uniform random bytes, each as 3 base-9 digits | random |
| R1 UNIF | IID uniform over 9 symbols | reference |
| R2 IID-FIT | IID with FAED's own symbol counts (for DBBI: DBBI's) | reference, fitted |

G1-G7 are the mechanism generators. R1 and R2 are references and are not gated: R2 is fitted to
the stream it is compared with.

## Discrepancy and decision

For generator `G` and stream length `N`, simulate `M = 2000` streams (seed 548). Compute the
mean and covariance of the 14 statistics over those simulations, and the Mahalanobis distance
`D` of each vector (pseudo-inverse of the covariance plus a ridge of 1e-9 times its trace).
The real stream's consistency value is `p_G = (1 + #{D_sim >= D_real}) / (1 + M)`.

- FAED: Holm correction over G1-G7. A generator is **excluded** if its Holm-adjusted `p <= 0.01`,
  otherwise **consistent**.
- Each verdict is read together with its measured power (Controls 3). "Consistent" under a
  generator with low power against the alternatives means little.
- DBBI: raw `p_G` values reported, no verdict.

## Controls (before the lock; none computes a real-stream statistic)

1. **Label invariance:** the statistic vector is unchanged under 100 random symbol permutations of
   a simulated stream.
2. **Calibration (size):** for each generator and `N = 570`, 200 fresh streams from the same
   generator (a different seed) are scored against it. The fraction with `p <= 0.01` must lie in
   `[0, 0.04]`.
3. **Power matrix:** for every ordered pair of generators (including R1, R2 built from each
   planted stream's own counts), 200 planted streams of `N = 570` from the row generator are scored
   against the column generator. The rejection rate at raw `p <= 0.01` is reported. Not gated.
   The R2 row draws IID streams with FAED's symbol counts (already disclosed above, not a
   statistic of this phase). The R2 column is refitted to each planted stream's own counts.
   The key entries are CB-ENG and CB-ENG-VIC as columns against the R2 row: can the test tell a
   FAED-shaped memoryless stream from an English checkerboard at this length?

Controls 1 and 2 must pass, or no lock is written.

## Disclosures and limits

- The generator list was chosen after looking at FAED's unigram counts (g = 107, i = 75, e = 69,
  six others 49-58) and knowing Phase 412's result. It was not chosen after computing any
  statistic of this phase. The list covers the creator's attested habits (checkerboard, VIC chain,
  code-page/encoding layer, letters-only text) plus key-shaped content.
- The English corpus is one book. The board models are uniform or VIC-frequency, not the
  creator's keyword method, and a keyword board lies between the two.
- Excluding a generator excludes *that* generator with these statistics. It does not exclude
  every checkerboard, every language or every keyed variant. "Consistent" is not evidence for a
  generator.
- A Mahalanobis omnibus can be dominated by a single statistic; per-statistic z values are reported
  for interpretation only.

## Stop rule

One run. Do not add generators, statistics, corpora or thresholds after seeing the result.

## Execution lock

`--prepare` runs the controls and writes `tools/gsmg/phase548_fingerprint_lock.json`, pinning this
protocol, the script, the test, `data.py`, the corpus file, seeds, `M`, the thresholds and the
control results. `--run` verifies the lock and scores FAED and DBBI once.

## Reproduction

```bash
python3 tools/gsmg/phase548_generator_fingerprint.py --self-test
python3 tools/gsmg/phase548_generator_fingerprint.py --prepare
python3 tools/gsmg/phase548_generator_fingerprint.py --run
```
