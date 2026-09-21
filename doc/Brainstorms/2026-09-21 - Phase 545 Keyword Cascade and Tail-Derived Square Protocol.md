# Phase 545 — keyword cascade and tail-derived squares

Status at creation: protocol, written before any cascade decode was scored. Options 4 and 5 of
the [BTCSEED tail options brainstorm](2026-09-21%20-%20BTCSEED%20Tail%20Decoding%20Options%20Brainstorm.md).
Everything below is frozen by the execution lock at the end.

## Claim and novelty

The community decode uses a square keyed by `DBBI[:13]`. Its output `D0` begins `BTCSEED`.
The same keyed-square construction can be applied to output-derived keywords, which no phase
has done to FAED: Phase 425 explicitly excluded "output-derived words"; Phase 419 swapped in
`VALIDATION_ANSWER` as the keyword (an outside string); Phase 476 used the deduplicated `P91`
as a second square over `Q472` (a different consumer, one keyword). This phase asks two
questions in one closed universe:

- **Cascade (option 4).** Iterating "decode FAED, take a prefix of the output as the next
  keyword": does any step produce something unusual?
- **Tail-derived squares (option 5).** Do those output-derived squares turn the project's
  other 91-symbol strings into something unusual?

Prior is low; both are deterministic, parameter-free once the rule is fixed, and cheap.

## Universe (closed)

**Keyword rules.** With `K_0 = DBBI[:13]` and `D_0 = decode(FAED, square(K_0))` (Phase 425's
decode): for rule `r` in {7, 13, full}, `K_{t+1} = D_t[:r]` (`full`: the whole decode, then
first-appearance deduplication as for DBBI), `D_{t+1} = decode(FAED, square(K_{t+1}))`, for
`t = 1..3`. `square(K)` is Phase 386's `build_grid` after `J -> I`. That is 9 FAED decodes.

**Objects under the derived squares.** FAED (the cascade itself), `DBBI` (91 symbols) and
`VALIDATION_ANSWER` (91 letters, Phase 3.2.2), each Bifid-decoded as one block, row-column,
forward, under every distinct derived square (excluding the baseline square). No other
object, period, direction, orientation, keyword length or iteration depth.

Layout, computed from the real cascade before the lock (squares and cycle flags only, no
statistic): 27 cells (9 FAED cascade cells, 9 distinct new squares x 2 objects); the three
chains do not cycle or return to the baseline within depth 3.

## Statistics and null

Each decode is scored with Phase 544's rail-aware lexicon statistics, generalised to any
square and any block length: dictionary words of 5-20 letters (Phase 544's lexicon,
pinned), occurrence surprisal from the object's own row and column marginals (output
letter i is the cell of coordinates `i` and `n + i`), `S1` = rarest occurrence and `S2` =
best non-overlapping cover. Occurrences may start anywhere (no prefix exclusion).

Null, 10,000 trials with fixed seeds:

- FAED cascade cells: exact-multiset shuffles of FAED with the whole cascade regenerated
  (dynamic squares), as in Phase 476.
- DBBI and `VALIDATION_ANSWER` cells: exact-multiset shuffles of the object, decoded under
  the same fixed squares.

One inclusive rank-max family correction over all 27 cells x 2 statistics, per null trial
(cells sharing an object share that trial's shuffle).

## Exact bar

**Positive checkpoint:** family-corrected p <= 0.01, and only that: a checkpoint for a
separate held-out study, never a decode, password or key. Otherwise **null_like**. Reported,
not gated: per-cell S1/S2 and top occurrences, and whether any chain repeats a square.
There is no oracle arm; keyed-alphabet strings were never proposed as phrases.

## Controls (before the lock; none scores the real cascade)

1. **Construction.** `D_0` reproduces the Phase 425 SHA-256; `square(dedup(D_0[7:98]))`
   reproduces Phase 476's `DEOMCKAHBSVXPRIQNGLUZFTWY`; the baseline square is
   `DBIFHCEGAKLMNOPQRSTUVWXYZ`; rule 7 yields keyword `BTCSEED`; the `full` square uses 25
   distinct letters.
2. **Model and round trip.** Encrypt/decode round trips for random squares at block lengths
   570, 91 and 90; the generalised model equals Phase 544's on FAED; per-type tables sum to 1;
   on an odd-length object the model matches 6,000 shuffled decodes within 0.02.
3. **Cascade logic.** Determinism, depth, first step uses the decode's own prefix, `J -> I`.
4. **Planted recovery.** A dictionary word planted into a synthetic random object encrypted
   under the square keyed `BTCSEED`, at block lengths 570 (8 letters) and 91 (10 letters):
   decoded under the right square it must be the top occurrence with corrected p <= 0.01
   against the same kind of shuffle null; decoded under a wrong square (the baseline) the
   corrected p must exceed 0.01.

## Stop rule

One universe, one run. Do not add rules, depths, objects, blocks/periods, directions,
squares, lexicons or statistics after seeing the result. A positive would need a separate
held-out protocol. A null closes only this cascade and these squares.

## Disclosures and limits

- The real cascade's squares and cycle flags were computed before the lock (to size the
  family); no decoded text or statistic of any cascade output was printed or scored.
- Phase 544's null-like tail result was seen. Power at n = 91 is low (few 5-letter
  occurrences); the 91-symbol cells mainly bound gross effects.
- The dynamic FAED null does not condition on `BTCSEED` being the observed prefix, so it
  measures cascades in general, not this prefix's selection.
- An outcome of null is not a statement about Bifid, BTCSEED as plaintext, or any blob.

## Execution lock

`--prepare` runs the controls and writes `tools/gsmg/phase545_cascade_lock.json` pinning this
protocol, the script, test, Phase 544 and 386 scripts, `data.py`, the dictionary and lexicon
hashes, rules, depth, trial count, seed and control results. `--run` verifies the lock, then
scores the real cells and the null once.

## Reproduction

```bash
python3 tools/gsmg/phase545_keyword_cascade_tail_square.py --self-test
python3 tools/gsmg/phase545_keyword_cascade_tail_square.py --prepare
python3 tools/gsmg/phase545_keyword_cascade_tail_square.py --run
```
