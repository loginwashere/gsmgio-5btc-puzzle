# Phase 544 — rail-feasible lexicon scan of the BTCSEED decode

Status at creation: protocol, written before the real tail was scored for this statistic.
Everything below is frozen by the execution lock described at the end. Source: option A1 of
[BTCSEED tail decoding options](2026-09-21%20-%20BTCSEED%20Tail%20Decoding%20Options%20Brainstorm.md).

## Claim and novelty

The community decode (DBBI-first-13 keyed square `DBIFHCEGAKLMNOPQRSTUVWXYZ`, one 570-symbol
block, row-column, forward) produces `BTCSEED...`. Phases 426-428 tested whole-tail
statistics and found only Bifid digraph mechanics. Phase 386's addendum scanned for embedded
dictionary words with a random-letter baseline that ignores the decode's structure. Two facts
make a sharper test possible:

- output letters 2k and 2k+1 depend only on FAED[k] and FAED[285+k];
- FAED's nine symbols occupy the first two square rows, so the even output rail can only be
  B, C, D or E.

Consequently an embedded word is only possible where its letters at rail-even positions are in
`BCDE`, and its chance rate under the mechanical null is exactly computable. This phase scores
every dictionary occurrence by its **surprisal under that exact model** and calibrates against
exact-multiset FAED shuffles. It asks one narrow question: does the tail contain dictionary
words rarer than the mechanical null produces?

Not new: the decode, the word scan (Phase 386 addendum), the shuffle-null style (Phases 425-428).
New: rail-aware surprisal scoring and a maximum-cover statistic. Prior is low; the value is a
calibrated, exact instrument.

## Object (one configuration)

The real decode `D` only (SHA-256 `0c5d984f...7745e`, reproduced from `data.py`). No other square,
period, direction or orientation. Occurrences may not overlap positions 0-6 (`BTCSEED`).

## Lexicon (closed)

`/usr/share/dict/words` (resolved file hash pinned in the lock): entries that are ASCII
alphabetic, 5 to 20 letters, uppercased, without `J`.

## Statistics

Mechanical rail model, fixed by the exact FAED multiset: `P_even(x)` for `x in {B,C,D,E}` and
`P_odd(y)` for the 25 letters are products of FAED's row marginals (even) and column marginals
(odd) at the cell of each letter. An occurrence of word `w` at offset `o` has surprisal
`sum_j -log2 P_{parity(o+j)}(w_j)` bits. Letters outside the rail alphabet cannot occur in a
decode.

- **S1** = maximum surprisal over all occurrences (offset >= 7).
- **S2** = maximum total surprisal over sets of non-overlapping occurrences (weighted interval
  scheduling).

Null: 10,000 exact-multiset shuffles of the 570 FAED symbols (seed 544000 + trial index), each
decoded with the same square and scored identically. Family correction over `(S1, S2)` by the
inclusive rank-max rule used in Phases 426-428: each statistic's upper-tail rank, the minimum
over the two, compared with the same quantity computed for every null trial.

## Exact bar

**Positive checkpoint:** corrected family p <= 0.01. Even then the result is only "the tail
contains dictionary words rarer than the mechanical null", a checkpoint for a separate
held-out study. It is not a decode, a password, a key, or any statement about a blob.
Otherwise the result is **null_like**.

Reported, not gated: the ten highest-surprisal occurrences, the best cover, individual p-values
of S1 and S2, and an arm on the closed puzzle word list of Phase 396 (`YOUWON`, `KMODEST`,
`MODEST`, `SATOSHI`, `SEED`, `KEY`, `WALLET`; `BTCSEED` excluded because it is the prefix):
count of distinct words present at offset >= 7, calibrated against the same shuffles.

## Controls (before the lock; none scores the real tail)

1. **Decode.** The real decode reproduces the Phase 425 SHA-256 and begins `BTCSEED`; its even
   rail is exactly `{B,C,D,E}`; 200 shuffled decodes never place another letter at an even
   position.
2. **Probability model.** Both rail models sum to 1; over 4,000 shuffled decodes each letter's
   empirical rail frequency is within 0.01 of the model; the surprisal of `BTCSEED` equals the
   direct sum.
3. **Scan and cover.** A toy tail with two known overlapping words returns exactly the expected
   occurrences and the cover picks the higher-surprisal one.
4. **Planted recovery.** For each alignment (even offset 200, odd offset 301) and each length in
   {6, 8, 10}, the first sorted dictionary word that can be planted (edited into FAED symbols so
   that the decode contains it exactly at that offset) is planted in the real FAED. Requirement,
   **for length 8 in both alignments**: the plant appears among occurrences, is the
   maximum-surprisal occurrence, and the family-corrected p against the frozen null is <= 0.01.
   Lengths 6 and 10 are reported (an alignment/length with no plantable word is reported as
   absent). Failure of the gate stops the phase.

## Stop rule

One configuration, one lexicon, two statistics, one run. Zero positive closes only this
instrument on this decode. Do not add other dictionaries, lengths, squares, periods,
orientations, statistics or an odd-only or even-only rail read after seeing the result. A
positive result would need a separate held-out protocol before any further use.

## Non-claims and disclosures

- Nothing here says the tail is plaintext. A null result does not retract Phase 425.
- **What was seen before the lock.** Development ran only null shuffles and planted words (to
  size the null and the gate); the real tail's S1/S2 were not computed. The real tail had
  previously been dictionary-scanned in Phase 386 (embedded words such as `SEED`, `MEDEA`,
  `DEAD` were noted as chance-level), so the outcome is not blind in that sense.
- The gate length (8) was fixed after seeing that the null S1 99th percentile is about 20.7
  bits and that plantable 6-letter words already pass; no real-tail number informed it.

## Execution lock

`--prepare` runs the controls and writes `tools/gsmg/phase544_rail_lexicon_lock.json` pinning
this protocol's hash, the script, test, `data.py`, the Phase 386 and 396 scripts it imports, the
dictionary file and lexicon list hashes, the square, the FAED hash, the null seed and trial
count, the L2 word list and the control results including the null pool digest. `--run`
recomputes the null and compares the whole lock before scoring the real tail.

## Reproduction

```bash
python3 tools/gsmg/phase544_rail_feasible_lexicon_scan.py --self-test
python3 tools/gsmg/phase544_rail_feasible_lexicon_scan.py --prepare
python3 tools/gsmg/phase544_rail_feasible_lexicon_scan.py --run
```
