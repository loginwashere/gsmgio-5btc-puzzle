# Phase 547 — nine-symbol origin census

Status at creation: protocol. Path 2 of the 2026-09-24 chat brainstorm ("finish the census of
ciphers that natively produce nine symbols"). Everything below is frozen by the execution lock
at the end.

## Claim and novelty

The page's own numeric transport writes `a..i` for 1-9 and `o` for 0. DBBI and FAED together
have 661 symbols and no `o`; as page-transport decimals that has probability about
`0.9^661 ~ 1e-30`. The nine-symbol alphabet is therefore native to whatever produced the two
streams, and the candidate producers form a finite list. The main one, a nine-column straddling
checkerboard, is the subject of most prior work. This phase closes the members that have
never been tested, each with an exact or key-invariant statistic and planted controls.

Prior coverage checked before writing:

- **Phase 277** grouped trits in threes, but only at offset 0, with the eight D4 square
  symmetries, and with two fixed 27-letter alphabets (`[space,A-Z]`, `[A-Z,space]`). Its
  reopening condition names "an authored grouping offset, alternate alphabet". A keyed Trifid
  cube is an unknown 27-cell substitution, and its index of coincidence (IoC) does not depend on
  the key. Member M1 therefore covers every alphabet at once, all 9! symbol-to-trit-pair maps,
  and all three offsets.
- **Phase 146** tested short-period Bifid/Trifid block fractionation, not coordinate regrouping.
- **Phone multi-tap**: no prior test (the repo mentions "phone keypad" only as a letter-value
  scheme in the periodic-table sensitivity table and a T9 ordering for the 3.2.2 alphabet).
- **Morbit and Pollux**: no prior repository coverage. Both were pre-screened today in a
  scratchpad without a lock (0 valid keys for both streams); see Disclosures. They are re-run
  here under the lock with planted controls so that the record is formal.

## Members

### M1 — keyed Trifid coordinates (key-invariant IoC)

Model: plaintext letters sit in a keyed 3x3x3 cube; each letter is written as three trits; the
trit stream is displayed two trits per symbol (`a..i` = a bijection onto `{0,1,2}^2`).

- Maps: all 9! bijections `a..i -> (hi, lo)`, with hi written first.
- Offsets: drop 0, 1 or 2 leading trits; group the rest in threes, drop an incomplete tail.
- Statistic: `IoC27 = sum n_c (n_c - 1) / (N (N - 1))` over the 27 triple codes. It is
  invariant to the unknown cube, so no key search is needed. Family statistic: the maximum
  over maps x offsets.
- FAED (1,140 trits, 380/379/379 triples) is **gated**. DBBI (182 trits, 60 triples) is reported
  with its own null but **not gated**, because 60 letters give low power.
- Reference values: uniform 27 cells 0.0370; English letters about 0.066.

### M2 — phone multi-tap

Model: letters are typed on a phone keypad (2 ABC, 3 DEF, 4 GHI, 5 JKL, 6 MNO, 7 PQRS, 8 TUV,
9 WXYZ); the ninth symbol `X` is not a letter key. One of the nine symbols is `X` (9 choices) and
the other eight are a bijection onto keys 2-9 (8!), giving 362,880 maps. Each maximal run of a
key symbol is one letter (run length = tap count), so a run longer than the key's letter count
(4 for keys 7 and 9, otherwise 3) is invalid. `X` runs are removed before decoding.

- Convention C1 (`X` = pause): every `X` run has length 1, is not at either end, and has the
  same key symbol on both sides.
- Convention C2 (`X` = word space): `X` runs of any length, anywhere.

Letters are scored with the repository quadgram model (`quadgram_solver.py`, normalized: total
log10 / (letters - 3)). Family statistic per stream: the maximum over valid maps x {C1, C2};
if no map is valid the statistic is `-inf`. FAED and DBBI are both **gated**.

### M3 — Morbit, M4 — Pollux (exact validity)

- Morbit: the nine Morse pairs `.. .- .x -. -- -x x. x- xx` in bijection with `a..i` (9!).
- Pollux: each of `a..i` mapped to one of `. - x` (3^9, all three symbols used).
- Validity (exact): no `xxx`; every dot/dash run between separators is an International Morse
  code (26 letters, 10 digits, `. , ? / - = + : '`). DBBI and FAED, forward and reversed.
- Outcome: the number of valid maps. Zero closes the member. A non-zero count is reported with
  decoded text and its quadgram score; it is not gated or promoted in this phase.

### Excluded by definition, not run

Monome-Dinome and Tridigital (ACA) use ten-digit ciphertext alphabets by their standard
definitions (stated from memory, not re-sourced here), so they are not native nine-symbol
producers. Predictive T9 needs dictionary segmentation, with no exact validator; it is out of
scope.

## Nulls and gate

- Null: exact-multiset shuffles of the stream, with the whole family recomputed per shuffle.
  M1: 1,000 shuffles per stream (numpy seed 547). M2: 500 shuffles per stream (seed 5471).
  `p = (1 + #{null >= real}) / (1 + n)`.
- Gated cells: M1-FAED, M2-FAED, M2-DBBI. Holm correction over these three.
  **Checkpoint** if Holm-adjusted p <= 0.01; otherwise **null-like**. A checkpoint only records
  a structural signal; this phase decodes nothing further and tests no blob.
- M3/M4: exact outcome as above.
- Census verdict: if every gated cell is null-like and M3/M4 have zero valid maps, no untested
  native nine-symbol producer remains in this declared census.

## Controls (before the lock; none computes a real-stream statistic)

1. **M1 planted:** five texts (the solved Phase 3.2 Architect plaintext in `A-Z`, 380 letters
   starting at offsets 0, 100, 200, 300, 400) encoded with a random cube, random symbol map and
   offset 0. Each must (a) have the true map/offset reach the family maximum IoC and
   (b) exceed the 99th percentile of 200 M1 nulls built from shuffles of the same planted stream.
2. **M2 planted:** Architect text encoded under C1 (pause between same-key letters, no spaces)
   and under C2 (spaces as `X`, a space also inserted between same-key letters), truncated to
   570 symbols with a random map. The true map must be valid, reach the family maximum, and
   exceed all of 100 nulls from shuffles of the planted stream.
3. **M3/M4 planted:** the Architect text Morse-encoded and put through a random Morbit key and a
   random Pollux assignment must give at least one valid map, and the true Morbit key must be
   among the valid maps.
4. **Machinery:** the vectorized M1 IoC equals a direct per-map computation on 300 random maps
   and all three offsets; the vectorized M2 decode equals a direct decode on 300 random maps.

## Disclosures and limits

- Morbit and Pollux were pre-screened today, unlocked, with the result known (0 valid maps for
  both streams). Lo Shu trigram bits, 3x3 keypad adjacency, mod-9/EBCDIC reductions, 9x9 pair
  alphabets, `C(14,2)` pairwise-row statistics and zeroed page transport were also pre-screened
  today; they are not part of this phase and remain scratchpad observations.
- M1 and M2 real statistics had not been computed when this protocol was written.
- The IoC is a first-order statistic; a Trifid with a period (true fractionation) is not the M1
  model, and Phase 146 covers short periods.
- M2's "one run = one letter" rule cannot represent two consecutive letters on one key without
  `X`; that is the model, not a bug.
- A negative closes only these members, maps, conventions and statistics.

## Stop rule

One run. Do not add maps, offsets, conventions, keypad layouts, statistics or members after
seeing the result.

## Execution lock

`--prepare` runs the controls and writes `tools/gsmg/phase547_census_lock.json`, pinning this
protocol, the script, the test, `data.py`, the quadgram file, the planted-text source, the seeds,
null sizes, thresholds and control results. `--run` verifies the lock and computes every member
once.

## Reproduction

```bash
python3 tools/gsmg/phase547_nine_symbol_origin_census.py --self-test
python3 tools/gsmg/phase547_nine_symbol_origin_census.py --prepare
python3 tools/gsmg/phase547_nine_symbol_origin_census.py --run
```
