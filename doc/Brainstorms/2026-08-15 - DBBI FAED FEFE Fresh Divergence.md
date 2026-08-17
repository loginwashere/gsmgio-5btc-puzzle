---
type: index
status: live
date: 2026-08-15
topics:
  - brainstorm
  - dbbi
  - faed
  - yinyang
  - g-yin-001
---

# Brainstorm — 2026-08-15 — DBBI/FAED fresh divergence toward `G-YIN-001`

> [!caution] Incubation note
> This session is exploratory, not a finding or canonical evidence. Do not add
> it to `GSMG_HOME.md`'s canonical list. Promote surviving work through the
> governed path.

## Desired outcome

A small set of genuinely new, well-motivated candidate directions for
`G-YIN-001` (how `DBBI` and `FAED` relate to reach the creator-confirmed
`yinyang` state) that do not repeat the 16-model campaign already closed in
Phases 274-289, ranked by cost and how directly they're motivated by
already-authenticated puzzle structure rather than free invention.

## Current understanding

### Known facts

- `DBBI` = 91 symbols, alphabet `a`-`i`, structured (IoC ≈ 0.151).
- `FAED` = 570 symbols, same alphabet, near-uniform (IoC ≈ 0.118).
  `570 = 6×91 + 24` exactly.
- Source-page order: `DBBI -> binary(matrixsumlist) -> FAED ->
  decimal(lastwordsbeforearchichoice) -> decimal(thispassword) -> SHA-256...`
- Confirmed creator clue chain: `yellowblueprimes -> matrixsumlist ->
  lastwordsbeforearchichoice -> yinyang`.
- A separate, already-solved part of this same puzzle uses a fixed
  9-symbol involution on the identical `a`-`i` alphabet: mirror pairs
  `B<->H`, `C<->G`, `D<->F`, with `E` fixed (the transform that turned
  `HYE` into `BYE`) — elsewhere in this project's toolkit this exact
  operation is already named `mirror9`.
- `G-MSL-001` establishes that only a 31-character **selection** from
  `DBBI` (not all 91 characters) feeds `matrixsumlist`. The worksheet's
  seven G3 fields (dimensions/placement/traversal/value mapping/
  aggregation/serialization/target) for *that* selection remain unbound,
  but the fact of a partial-not-full consumption is established.
- The master worksheet's own diagnosis: G1 (source) and G2 (input) both
  **PASS** — the data is authenticated. G3 (operation) and G4 (output
  recognition) are the actual failure points. This is a specification
  gap, not a missing-transform gap.
- `G-ESC-001` (FAED's decoder escape-pair `{g,i}` vs `{h,e}`) is a
  separate, adjacent, also-parked gap that has never been touched by the
  DBBI/FAED coupling campaign at all — it's about the *decoder alphabet*,
  not the relationship between the two streams.
- Chapter 2's first three yin-yang-decorated drop caps give `(page −
  A1Z26(letter)) mod 26` = `YIN` exactly (Phase 262). Applying the same
  formula to all 39 book-wide drop caps, concatenated **by chapter**,
  contains no `YANG` or its reverse. Only chapter-anchored, same-signed
  windows were tested.

### Do not re-propose (closed, Phases 274-289)

Six-lane FAED/DBBI geometry · per-stream 9×9 bigram transition matrices ·
GF(9) arithmetic (3 irreducibles × 2 orders) · base-27 three-trit D4-symmetry
regrouping · move-to-front gate (BWT itself remains technically unexecuted,
see below) · base-81 digraph mutual information · factoradic/Lehmer codes ·
crib-solved lag-1/lag-2 recurrences · arithmetic/range coding · asymmetric
numeral systems · finite-state transducer · sequence alignment · audio/
spectrogram rendering · 2D matrix-barcode rendering · continued fractions
against 17 authenticated numbers · index/selector into other solved strings.
All statistically null after multiple-testing correction; none crossed
p<0.01.

### Assumptions to challenge

- That any single transform of the **entirety** of both streams is the
  right shape of answer, rather than a transform of the parts each stream
  has *left over* after its own named stage consumes a subset.
- That `matrixsumlist` names an operation on `DBBI` alone, rather than a
  joint construction that positionally pairs `DBBI` against `FAED`.
- That the escape-pair choice for `G-ESC-001` needs external creator
  evidence, rather than being resolvable from FAED's own internal symbol
  statistics (an escape code should behave differently in-stream than an
  ordinary data symbol).
- That the drop-cap `YIN` result is exhausted because chapter-anchored
  readings were tried — an unanchored sliding window and the arithmetic
  complement (`+` instead of `−`) were not.

## Divergence pass — raw idea inbox

Do not rank or reject during this pass.

1. **Complementary-remainder operand.** `G-MSL-001` establishes
   `matrixsumlist` consumes a 31-character *selection* from `DBBI`'s 91,
   not all of it. Test whether the **unused 60 characters** (in original
   position order, and in complement-position order) — not the full
   91-character string — is the correct operand for whatever relates to
   `yinyang`. Symmetrically check whether `lastwordsbeforearchichoice`
   consumes all 570 characters of `FAED` or only part of it, and if a
   remainder exists, test that remainder the same way. This reframes the
   gap as "what's left over after the named stages take their cut,"
   which no closed model tested — all 16 treated DBBI/FAED as fully
   consumed by whatever transform was under test.
2. **Joint positional matrix, not two separate ones.** Closed model 2
   built a 9×9 transition matrix *per stream*. A literal reading of
   "matrixsumlist" could instead mean: walk `DBBI` and `FAED` **in
   lockstep** (position *i* of each, wrapping the shorter one or using
   only the first 91 of each of FAED's six 91-symbol lanes), treat each
   pair as a `(row, col)` coordinate into a 9×9 grid, increment that
   cell, and sum rows/columns/diagonals of the resulting joint
   co-occurrence matrix. This differs from the closed six-lane geometry
   test (which scored lane-vs-DBBI correlation statistics) by literally
   building the described object — a matrix — and literally summing it,
   rather than testing for structural correlation between lanes. Needs a
   check against `dbbi_faed_six_lane_audit.py`'s exact statistic
   list before running, in case this is already covered.
3. **`mirror9` applied directly as a substitution cipher.** The `a`-`i`
   mirror `B<->H, C<->G, D<->F, E fixed` is not invented for this
   brainstorm — it's the exact transform already authenticated elsewhere
   in this project on this exact alphabet (the `HYE -> BYE` result). None
   of the 16 closed models applied it as a plain letter-substitution
   cipher directly to `DBBI`/`FAED` and oracle-tested the output; GF(9)
   arithmetic (model 3) is a different, heavier operation. Generate
   `mirror9`/`reverse`/`halfswap` variants of both raw strings (and their
   31-char/remainder sub-selections from idea 1) and run them through the
   standard `answer_forms()`/`keystr_forms()` oracle — cheap, bounded,
   directly precedented by this exact puzzle's own prior solve.
4. **Escape-pair resolution from FAED's own statistics.** `G-ESC-001`
   (`{g,i}` vs `{h,e}`) has never been touched by the DBBI/FAED coupling
   work — it's a separate question about the decoder's escape alphabet.
   A checkerboard/straddling decoder's escape codes are typically rare
   by construction (they're control symbols, not data). Compute raw
   symbol frequency of `g`,`i`,`h`,`e` in FAED; if one pair is
   markedly rarer than the other three-plus symbols and the other pair
   is not, that is intrinsic (not external) evidence for which pair is
   the escape pair — resolvable from data already in hand, no new
   primary source needed.
5. **Sliding-window and complement-operation sweep for `YANG`.** Phase
   262 only tested chapter-anchored concatenations of the 39 drop caps
   with the *same* subtraction formula. Two narrow, cheap extensions
   neither one tried: (a) slide the `(page − A1Z26(letter)) mod 26`
   window across **all** 37 possible 3-consecutive-entry windows in the
   full 39-entry sequence (not just chapter starts) looking for `YANG`
   or its reverse; (b) test the **arithmetic complement**, `(page +
   A1Z26(letter)) mod 26`, on the same windows — thematically motivated
   since yin and yang are described as complementary, so if yin comes
   from subtraction, yang emerging from addition (the literal opposite
   operation) is a directly analogous, not arbitrary, hypothesis.
6. **`lastwordsbeforearchichoice` reuses the already-solved BYE
   mechanism.** The stage name references the Matrix Architect's "choice"
   scene, which is also where the authenticated `mirror9`/`BUT->HYE->BYE`
   chain originates. Test whether the *exact* already-authenticated
   operation (mirror `a`-`i` symbols, preserve `Y`-equivalent positions)
   applied to `FAED` — not the endings rail it was originally derived
   from — reproduces something recognizable, rather than treating
   `mirror9` as a free choice invented fresh for this brainstorm (idea 3
   applies it to both streams generically; this idea is narrower and
   specifically tied to the `lastwordsbeforearchichoice` stage name).
7. **BWT reopening condition, made concrete.** Move-to-front's gate
   failed, so BWT was correctly never run. Rather than leaving this as an
   abstract "needs authenticated index/terminator," enumerate the small
   set of already-authenticated numbers that could plausibly serve as a
   primary index (91, 570, 31, 7, 16, 23, 24, 574061 mod 91, mod 570) and
   pre-register which of those, if any, would count as authenticating a
   specific row before inverting — so this stays a bounded, disclosed
   test rather than a post hoc scan of all 661 rows if it's ever reopened.

## Connections and challenges

### Combinations

- Ideas 1 + 3: apply `mirror9` to the *remainder* strings from idea 1,
  not just the full raw streams — a smaller, more targeted candidate set
  than either idea alone.
- Ideas 1 + 2: if a remainder split exists, the joint matrix in idea 2
  could be built from the two remainders instead of the two full streams.

### Contradictions

- Idea 2 may substantially overlap with the closed six-lane geometry
  model (both are "relate DBBI to reshaped FAED via a grid/matrix");
  needs explicit differentiation from that audit's exact statistics
  before being treated as new, or it risks re-closing the same ground
  under a different name.

### Missing assumptions

- None of ideas 1-7 assume new primary evidence will appear — all are
  reachable from data already in hand. That's deliberate: the
  post-model synthesis doc already concluded Telegram corpora and page
  syntax are exhausted, so anything requiring a new creator statement is
  not a near-term experiment.

## Promising directions

Ranked by cost (cheapest first) and how directly each is forced by
already-authenticated structure rather than invented:

1. **Idea 5 (drop-cap sliding-window + complement-operation sweep for
   `YANG`)** — cheapest, minutes of compute, directly extends a result
   that's already real (not hypothetical), thematically motivated by
   yin/yang complementarity rather than arbitrary.
2. **Idea 4 (escape-pair frequency argument)** — cheap, resolves a
   different but adjacent gap (`G-ESC-001`) from data already in hand,
   no oracle sweep needed, just a frequency count.
3. **Idea 1 (complementary-remainder operand)** — reframes what "the
   input" even is, directly forced by `G-MSL-001`'s own established
   31-of-91 partial consumption; feeds ideas 3 and 6 as smaller,
   better-motivated candidate sets than testing the full raw streams.
4. **Idea 3 / Idea 6 (`mirror9` direct substitution, generic and
   BYE-mechanism-specific)** — cheap oracle-testable candidates, directly
   precedented by this exact puzzle's own prior solve on this exact
   alphabet, not a new cipher invented for this brainstorm.
5. **Idea 2 (joint positional matrix)** — needs a differentiation check
   against the closed six-lane audit first; do not run until confirmed
   non-duplicate.
6. **Idea 7 (BWT reopening pre-registration)** — not an experiment by
   itself, but worth writing down now so BWT isn't reopened on a post hoc
   basis later.

## Decisions

- Idea 5 executed as designed and closed negative.
- Idea 4 turned out to duplicate already-closed prior work once checked
  against the actual escape-pair literature in this repo (see below) —
  not executed as a new test; superseded in place.
- Idea 1's premise was wrong and is corrected in place (see below) — not
  executed as originally described; the corrected question is now a
  precondition for ideas 3/6, not yet answered.

## Experiments and next actions

- [x] **Idea 5 — closed, negative (2026-08-15).** Full 37-window ×
      {`-`,`+`} × {`YIN`/`NIY` (3-wide), `YANG`/`GNAY` (4-wide)} sweep
      over all 39 drop caps, both formulas applied at every offset (not
      just chapter starts). Subtract sequence:
      `VYVWXKALOHYINJMNNJMVGHSQYJVPLTHYRRWWQWV`; add (complement)
      sequence: `JKXYZOIZCPSMRXABHNOJSVSWQPHPXJBODFIKSQX`. Only hit: the
      already-known `YIN` at index 10 (Chapter 2's first three). No
      `YANG`/`GNAY`/`NIY` anywhere, and the complement operation produces
      no recognizable word at all. The `YIN` result stays a bounded,
      unexplained curiosity; it does not extend into a `YANG` pair by
      either generalization tested here.
- [x] **Idea 4 — superseded by prior work, not a new result (2026-08-15).**
      Before running the planned raw-frequency count, checked
      `doc/GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT.md` and
      `faed_monoalphabetic_sweep.py`: FAED's escape pair was already
      independently ranked across **all 36 candidate pairs** by proper
      escape-share methodology back in Phase 106/112, with `{g,i}`
      landing rank 1/36 — a far more rigorous version of what this idea
      proposed to compute freshly. `{h,e}` was never a data-driven
      competitor; it's a theory-driven prediction from applying the
      already-authenticated `mirror9` involution to DBBI's solved
      `{b,e}` escape pair. The actual open question (recorded in that
      audit's own "Consequence" section) is sharper than "which pair
      fits FAED's statistics better" (settled: `{g,i}`) — it's *why*
      FAED's own data prefers a different pair than the Architect-mirror
      theory predicts, which frequency counting alone cannot answer.
      Ran the raw count anyway for completeness (`g`=107, `i`=75 vs
      `h`=58, `e`=69 out of 570; `{g,i}` sits well above the per-symbol
      mean of 63.3, `{h,e}` sits almost exactly on it) — consistent with,
      but strictly weaker than, the existing rank-1/36 result. **No new
      evidence produced; `G-ESC-001` unchanged.**
- [x] **Idea 1 — premise corrected, not executable as stated (2026-08-15).**
      Checked `denis_prime_extraction_audit.py` before computing any
      "remainder": the 31-character string
      (`ncsyangcahiriasogaleafayanestve`) is **not** a decode of a
      DBBI substring. It's a community member's (Denis Golovkin's)
      claimed order-preserving 31-of-91 selection from a *different*,
      already-known 91-character sentence (`incaseyoumanage...`),
      using DBBI only as an index/filter source via primality + B/BE
      membership — and this project's own 44-rule sweep of that exact
      family **failed to reproduce his claimed output**. There is no
      authenticated mapping from DBBI's raw positions to "characters
      consumed by matrixsumlist," so there is no principled "60
      leftover DBBI characters" to compute — doing so would mean
      picking one of the 44-already-rejected (or a 45th, unmotivated)
      rules and treating its output as ground truth. **Corrected
      question, still open:** ideas 3 and 6 (`mirror9` substitution)
      should be tried against the **full** DBBI/FAED strings, not a
      hypothetical remainder — the remainder framing does not survive
      contact with `G-MSL-001`'s actual documented state.
- [x] **Idea 3 — closed, negative (2026-08-15).** `mirror9`/`reverse`/
      `halfswap` and all 8 combinations, applied directly as a
      substitution/permutation to the full raw `DBBI` and `FAED`
      strings (per idea 1's correction: full streams, not a
      hypothetical remainder), oracle-tested via the standard
      `answer_forms()`/`keystr_forms()` pipeline.
      `dbbi_faed_mirror9_direct_substitution_audit.py`: 16 labels, 32
      candidate strings, 96 passphrase attempts, 0 hits against all four
      blobs. Idea 6 (the narrower, `lastwordsbeforearchichoice`-specific
      framing of the same transform) is subsumed by this run — the
      `faed/mirror9` row is exactly that test.
- [x] **Dedup check for idea 2 — passed, idea 2 confirmed non-duplicate
      (2026-08-16).** The filename this item originally cited
      (`dbbi_faed_lane_correlation_audit.py`) doesn't exist; the actual
      closed six-lane script is `dbbi_faed_six_lane_audit.py` (fixed
      above). Its 8 `BODY_METRIC_NAMES` — `max_lane_match`,
      `max_lane_match_run`, `any_lane_match_columns`, `unique_mode_matches`,
      `max_residual_bin`, `column_collision_excess`, `max_lane_pair_matches`,
      `max_lane_pair_match_run` — are all per-lane/per-column equality or
      residual measures. None build or sum a joint DBBI×FAED 9×9
      co-occurrence matrix. Idea 2 is a genuinely different statistic, not
      covered by the closed six-lane audit.
- [x] **Idea 2 — closed, negative (2026-08-16).**
      `dbbi_faed_joint_positional_matrix_audit.py`: two pre-registered
      pairings (`wrap_full`, `pool_lanes`), 6 candidate derivations per
      matrix, 12 candidates, 36 passphrase attempts against all four
      blobs. 0 hits. See `tools/gsmg/FINDINGS.md` Phase 297. This closes
      the last unexecuted idea in this document's idea list.

## Related notes

- [[2026-08-14 - Fresh DBBI FAED Decryption Models]]
- [[2026-08-14 - DBBI FAED Post-Model Synthesis and Reopening Conditions]]
- [[2026-08-15 - Canonical Sentinel Inventory (P0A)]]
- [[GSMG_OPEN_GAP_REGISTRY]]
- [[GSMG_STRICT_TRANSITION_WORKSHEET]]
