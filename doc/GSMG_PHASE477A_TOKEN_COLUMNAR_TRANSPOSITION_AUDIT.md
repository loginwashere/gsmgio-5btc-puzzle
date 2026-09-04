# Phase 477A: pre-board token columnar transposition of FAED `{g,i}`

Date: 2026-09-04. Protocol: `doc/Brainstorms/2026-09-03 - Phase 477A Token
Columnar Transposition Protocol.md` (draft of 2026-09-03 plus the pre-lock
amendments A1-A6 of 2026-09-04).

## Question

Is FAED, segmented once under `{g,i}` into 436 checkerboard code tokens, a
ragged columnar transposition (unknown width `2..40`, unknown column order)
of English-like plaintext under a single global 25-symbol monoalphabetic
board?

Only Model A (transposition of plaintext letters before the checkerboard)
is tested. The historical VIC/ADFGVX order (transposition of the raw digit
stream after substitution) is reserved for Phase 477B and is not addressed.

## Frozen construction

- Token stream: `segment_codes(FAED, "g", "i")`, 436 tokens, 25 code types,
  slots ordered singles (`a b c d e f h`), then `g`-pairs, then `i`-pairs.
- Widths `w = 2..40`; ragged convention `rows = ceil(436 / w)`, the last
  `w * rows - 436` columns by original index one short, no padding.
- Two directions per width. The mechanical direction-equivalence test
  (exhaustive for `w <= 7`, 200 sampled orders otherwise) found no width at
  which the transpose family's position permutations lie inside the
  untranspose family, so both directions are retained at every width.
- One global 26-letter key (25 slots plus one unused letter), scored with
  the project's frozen `english_quadgrams.txt`; the cell statistic is the
  best total quadgram log-probability divided by 436.
- Randomness: explicit PCG32 (XSH-RR) with fixed seeds; all budgets are
  fixed counts.

### Untranspose search (observed tokens are the column-read output)

Every one of the `w!` column orders is enumerated for `w <= 11`. Orders are
ranked by a substitution-invariant coincidence statistic of the
reconstructed token sequence, `pairs(digraphs) + 3 * pairs(trigraphs)` with
`pairs = sum C(n, 2)`, and the top 16 orders each receive a board anneal
(2 restarts, 30,000 proposals, `T 20 -> 1`). Untranspose widths `12..40`
are not enumerable and are excluded from the family (`not_enumerable`).

### Transpose search (observed tokens are the row-major grid)

Each column is a contiguous plaintext chunk, so the board is annealed on
within-column quadgram windows (16 restarts, 10,000 proposals,
`T 20 -> 1`); for the best 4 boards the order is solved on the junction
gain matrix (Held-Karp for `w <= 16`, greedy plus or-opt/2-opt improvement
above), then 3,000 full-score polish moves and 3 refine rounds of 4,000
board proposals.

## Development history (before the lock)

The optimiser in the 2026-09-03 draft (alternating Held-Karp order step on
bigram adjacency and board hill-climb) was implemented first and failed
its own planted-positive checks above `w = 4` in the untranspose direction.
The following facts were established on development fixtures (seed
`0x477A0DE`) and drove amendments A1-A6:

1. **Flat order landscape.** With the board re-solved from scratch, a
   planted order damaged by one column swap scores `-5.02` (`w = 12`) and
   `-4.83` (`w = 20`) per token against the planted `-4.52`; two or more
   swaps score `-5.2` to `-5.6`, indistinguishable from the best board fit
   to a random order (`-5.2` to `-5.4`). Joint simulated annealing over
   (order, board) solved `w = 9` and half of `w = 12` at 300,000 proposals
   and nothing at `w >= 16` even at 3,000,000; nested order-outer /
   board-inner annealing and annealing of the invariant statistic also
   failed. Local search over the order is therefore not used.
2. **Bigram-conditional objectives are not identifiable.** Annealing the
   board against either a successor-relaxation or an exact best-path bigram
   objective produced wrong boards scoring *above* the true board at every
   width tested, so the board cannot be solved before the order in the
   untranspose direction.
3. **Exhaustive ranking works.** Under the coincidence statistic the
   planted order ranked first, second or third among all `w!` orders on 24
   of 24 development fixtures at `w = 5..10` (both pools) and first on 3 of
   3 at `w = 11`.
4. **Transpose order is not identifiable but the statistic is searchable.**
   Only `3 (w - 1)` of the 433 quadgram windows depend on the order, so the
   planted score is reached at every width while the planted order is
   recovered only at small widths. The gate was therefore changed to score
   reach (A3).
5. **Fixture corpus.** At the draft's `0.65` top-7 threshold, 20 of the 25
   eligible windows in the full transcription lie inside the book's index
   pages. Fixtures now use prose sections only (56,292 letters) and a
   `0.62` threshold (82 separated starts). No prose window reaches FAED's
   `0.693` single-slot fraction (corpus maximum `0.658`).

## Power gate (holdout, seed `0x477A401D`, 10 hard + 5 broad per cell)

**What the gate certifies.** The gate criterion is score reach: the search
attains at least the planted fixture's normalised quadgram score. It
demonstrates attainment of the known planted score, not recovery of the
planted transposition or plaintext. Recovery is reported separately below.

**Score reach.** All 49 retained primary cells passed the 80% rule: 489 of
490 hard fixtures and 244 of 245 broad fixtures reached the planted score
(the single misses are one `w = 18` transpose hard fixture and one `w = 18`
transpose broad fixture). Both secondary `{h,e}` width-7 cells passed 10/10
and 5/5. The `trivially_powered` label carried by widths 2-4 in the JSON
records is a programmatic width tag inherited from the draft protocol, not
a separate criterion; those cells passed the same score-reach gate as every
other cell.

**Recovery, per direction (holdout hard pool).**

| Direction | Fixtures | Reach | Exact order | Median char. accuracy | Median Kendall tau |
|---|---|---|---|---|---|
| untranspose (`w = 2..11`) | 100 | 100 | 87 | 1.000 | 1.000 |
| transpose (`w = 2..40`) | 390 | 389 | 28 | 0.076 | 0.056 |

Untranspose recovery is exact in most cells; widths 3 and 6 have mean
character accuracies of 0.706 and 0.517 because a different order/board
pair scored at or above the planted one (5 of 10 fixtures at each width).
In the transpose direction the solver almost always attains the planted
score with a different pseudo-English column order, as expected from the
non-identifiability of the order (development fact 4). The transpose gate
therefore validates a score-based detector only; it does not demonstrate
key or plaintext recovery.

**Fixture concentration.** The hard-pool fixtures span top-7 letter shares
of 0.6216 to 0.656 (corpus maximum 0.658). FAED's `{g,i}` single-slot
fraction is 302/436 = 0.6927. All 49 cells are therefore score-reach
powered on the available 0.62-0.658 concentration fixtures; recovery power
at FAED's exact 0.693 concentration was not established. The null preserves
FAED's exact histogram, so the p-value is valid for the chosen statistic;
what remains uncertain is false-negative sensitivity to an English-like
construction with FAED's unusually concentrated histogram.

**Omission.** The draft protocol listed separation from paired shuffled
power fixtures as a reported (non-gating) quantity. The implementation
generates no paired shuffled power fixtures and that quantity was not
reported. This does not affect the real-versus-null statistic.

One complete family search costs about 1,470 CPU-seconds (holdout mean per
cell summed), so the Python reference was the decision implementation
(amendment A6).

Records: `tools/gsmg/phase477a_dev_power.json`,
`phase477a_holdout_power.json`, `phase477a_he_dev_power.json`,
`phase477a_he_holdout_power.json`. Lock:
`tools/gsmg/phase477a_execution_lock.json` (script SHA-256
`c95fa414...91c2f`, protocol SHA-256 `8dde7cec...ba5f6`), written after the
holdout gate and before any FAED search. Post-run lock consistency is
checked by `tools/gsmg/phase477a_verify_run.py`, which is fail-closed:
every expected value (trial count, promotion bar, real/null seeds, token
length, retained cell set) is read from the locked manifest and from the
locked script itself, imported only after its hash is confirmed, never
from a command-line argument or a hardcoded default, so the check cannot
be relaxed by the caller (it takes only a pair name, `gi` or `he`, and
rejects anything else). It checks all pinned-input, script, protocol and
manifest hashes; the real and null artifacts' pair label, token length,
seed, budget, and cell set against the locked manifest and script
constants (not against each other); exactly 200 trials numbered 0-199 with
the locked cell set in every trial; each trial's `family_max` against its
own cells; and tie-inclusive exceedance counting. Its output records
include the real and null artifacts' own SHA-256 hashes and are
`phase477a_verification.json` and `phase477a_he_verification.json`.

## Result: primary `{g,i}` family

Real FAED family maximum: `-5.2928` per token, from the `w = 38`
transpose cell; the best untranspose cell (`w = 10`) scored `-5.5299`. The
family median across the 49 cells was `-5.525`. Every cell's best text is
gibberish (the `w = 38` transpose output begins
`IWBSTOACEOOFYAETVERGTSTOPRSETIRTRONSEESCARLNATUGOLOAGNPSYSTARR...`).
For scale, planted English fixtures score `-4.2` to `-4.6` per token under
the same pipeline.

Token-preserving null (200 trials, identical 49-cell family): family
maxima ranged `-5.4183` to `-5.2567`, median `-5.3349`. `14` of 200 null
maxima equal or exceed the real maximum, so `p = 15/201 = 0.0746`. The real
maximum sits at rank 15 of 201 in the null family-maximum distribution; it
is not promoted (`p > 0.005`). The verifier (`phase477a_verification.json`)
confirms the locked hashes, budgets, exactly 200 unique trials numbered
0-199, the identical 49-cell set in every trial, and tie-inclusive
exceedance counting; no partial or alternate null run was combined.

**Seed-formula discrepancy, disclosed.** The protocol text (draft
paragraph, before amendments A1-A6) describes the null seeds informally as
"seeds `0x477A_NULL + k`". This is a pre-lock protocol/implementation
discrepancy: the locked script (`audit_script_sha256` in the execution
lock) never used integer addition. It derives each trial's shuffle seed as
`derive_seed(pair_seed(SEED_NULL), k)` and each trial's solver seed as
`derive_seed(pair_seed(SEED_NULL), k, 1)`, where `derive_seed` is the
SplitMix64-style deterministic mixing function defined in the script (xor
with each part, multiply by the fixed odd constant `0x9E3779B97F4A7C15`,
xorshift by 29, repeated once per part) and `pair_seed` is the identity for
`{g,i}` and a further mixed derivation for `{h,e}`. What was actually
frozen and executed is this mixing function, not the additive shorthand in
the protocol prose; the two produce unrelated integers (e.g. for `{g,i}`
trial `k = 0`, the shorthand's `SEED_NULL + 0 = 0x477A0000 = 1199177728`
versus the actual `derive_seed(SEED_NULL, 0) = 8409436475319422791`). This
does not affect the null
test's validity: the script, not the prose description, was what was
hashed into the lock and what ran all 200 trials, and every trial's seed
is independently reproducible and was confirmed by the verifier (which
imports the locked script and recomputes `expected_null_seed_base` and
`expected_real_seed` from it, rather than trusting either document's prose).

Two descriptive, non-preregistered observations, reported without a claim:
(i) the null family maximum came from a transpose cell in 200 of 200 trials,
and at the real maximum's own cell (`w = 38` transpose) 0 of 200 null values
reach the real value (null cell maximum `-5.2985`); this is a
post-selection comparison at the argmax cell and is subsumed by the
family-maximum test. (ii) The real untranspose subfamily maximum
(`-5.5299`, over `w = 2..11`) lies below every null trial's untranspose
subfamily maximum (minimum `-5.5279`), while per cell the real
untranspose values sit at unremarkable ranks (38 to 195 of 200 nulls at or
above). Neither observation was a preregistered statistic.

## Result: secondary `{h,e}` width-7 diagnostic (never pooled)

FAED under `{h,e}` segments into 469 tokens, an exact `7 x 67` grid. Real
family maximum `-5.2443` per token (untranspose; transpose `-5.4067`), text
gibberish (`NRRESINNLTUATEERRSUSELZEREAKFIENEERSSTEVAINISENOVRUNASZTXIRRRRE...`).
Its own 200 token-preserving controls gave family maxima with median
`-5.3323` and maximum `-5.2217`; 2 of 200 equal or exceed the real value
(tie-inclusive), so `p = 3/201 = 0.0149`. The verifier confirms 200 unique
trials, the identical 2-cell set in every trial, and locked budgets. This does not meet the `p <= 0.005` bar and is not a
threshold-level result under the protocol, so no confirmation run is
triggered. It is recorded as an upper-tail (rank 3 of 201) but unpromoted
observation with an unreadable output.

## Disposition

**Bounded negative** for the 49 retained cells under the locked
normalised-quadgram statistic and the available synthetic score-reach
calibration (`p = 15/201 = 0.0746` against a `0.005` promotion bar). Model
A, as a single ragged columnar permutation of the `{g,i}` token stream at
widths 2-40 (transpose direction) and 2-11 (untranspose direction) under one
global English-scored board, is not supported by FAED. Phase 477A does not
exhaust arbitrary token-columnar English recovery: the unmatched 0.693
concentration profile and the unenumerated untranspose widths 12-40 remain
explicit limits, and the `{h,e}` width-7 diagnostic is unpromoted at
`p = 0.0149`.

## Limits of the conclusion

- The power calibration is score-reach on fixtures whose letter
  concentration (0.62-0.658) is below FAED's 0.693; recovery power at
  FAED's exact profile was not established. The missing experiment for a
  stronger retirement is a separately locked exact-histogram sensitivity
  test: construct high-scoring planted sequences using precisely FAED's
  25-token multiset, transpose them, and test whether this solver reaches
  at least their planted score. That closes the power gap without rerunning
  real FAED.
- Untranspose widths `12..40` were not searched. Exhaustive enumeration is
  infeasible there in the reference implementation and no local search
  demonstrated power on planted fixtures. These cells are `not_enumerable`,
  not closed; a Rust port would reach `w = 12` (`4.8e8` orders) and perhaps
  `w = 13`, but not beyond.
- The model is a single standard ragged columnar permutation of the `{g,i}`
  token stream under one global 25-letter board scored by English quadgrams.
  Double or disrupted transposition, non-columnar reorderings, key-material
  or non-English plaintext, and the raw-digit VIC/ADFGVX order (Phase 477B)
  are untouched.
- The hard-profile fixtures reach a top-7 share of at most `0.658`; FAED's
  `0.693` single-slot fraction is above every 436-letter prose window in
  the reference corpus. The power test therefore certifies the search on
  English prose that is slightly less skewed than FAED, not on a
  distribution that matches FAED's skew exactly.
- The unexplained `{g,i}` code IC of `0.0743` is invariant under this model
  and is neither explained nor addressed.
- No password material, ciphertext-oracle calls, address derivations, or
  Bitcoin endpoint checks were performed.

## Verification

- `phase477a_token_columnar_transposition_audit.py selftest`: round trip
  for every width and direction, Held-Karp against brute force, batched
  invariant against the scalar definition, direction-equivalence at all 39
  widths.
- `phase477a_verify_run.py`: post-run lock consistency (see Power gate).
- `test_phase477a_token_columnar_transposition_audit.py`: 18 unit tests
  (PCG32 reference stream, geometry, fixtures, hard-profile construction,
  prose-only corpus, enumeration ranking, planted positives in both
  directions, `not_enumerable` handling, secondary-pair configuration, null
  histogram invariance).
- Every null trial's token histogram equals the real one (asserted in the
  run).

Artifacts:

- `tools/gsmg/phase477a_token_columnar_transposition_audit.py`
- `tools/gsmg/test_phase477a_token_columnar_transposition_audit.py`
- `tools/gsmg/phase477a_verify_run.py`, `phase477a_verification.json`,
  `phase477a_he_verification.json`
- `tools/gsmg/phase477a_manifest.json`, `phase477a_execution_lock.json`
- `tools/gsmg/phase477a_{dev,holdout,he_dev,he_holdout}_power.json`
- `tools/gsmg/phase477a_real.json`, `phase477a_null.json`,
  `phase477a_he_real.json`, `phase477a_he_null.json`
- `doc/Brainstorms/2026-09-03 - Phase 477A Token Columnar Transposition Protocol.md`
