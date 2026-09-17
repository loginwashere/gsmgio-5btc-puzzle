# Phase 516 — DBBI unrestricted-order transposition scoping

Date: 2026-09-16

Status: **executed and closed** — see
[GSMG_PHASE516_DBBI_WIDTH7_UNRESTRICTED_AUDIT](../GSMG_PHASE516_DBBI_WIDTH7_UNRESTRICTED_AUDIT.md)
for the full writeup. Summary: the naive single-stage design scoped below
failed its own self-test (under-annealing, diagnosed and fixed with a
two-stage cheap-rank/expensive-refine architecture); the real width-7 run
(all 36 pairs, exhaustive order search) found no candidate beating any of
3 shuffled-DBBI null trials — closed negative, calibrated. Width 13 remains
out of scope per the reasoning below, now confirmed by a direct cost
benchmark rather than estimated.

## Novel question

The unrestricted-order columnar-transposition solver line (Phase 477 onward:
token transposition feasibility, the width-19/30 CSP/annealing board search,
the Phase 512 exact-crib CSP architecture) has only ever been pointed at
`FAED`. `DBBI`'s own transposition-shaped work stopped at Phase 319, which
tested only a small family of *fixed, named* routes (spiral, boustrophedon,
row-major, column-major) over `DBBI`'s known `7x13` grid and found nothing —
a search of a handful of candidates, not the unknown-column-order
search-over-all-permutations that `FAED` received starting Phase 477.

`DBBI` and `FAED` are the same cipher construction (checkerboard escape-pair
substitution) on the same page. If the "plaintext -> checkerboard raw
symbols -> columnar transposition -> observed" model (Model B) is real for
this scheme at all, it should be tested on both streams, not only one. This
phase scopes — but does not yet execute — that test: does an unknown column
order exist under which `DBBI`'s raw stream, untransposed and then
escape-pair-segmented and checkerboard-decoded, produces readable plaintext?

This is a symmetry check, not a `G-YIN-001` or `G-MSL-001` closer by itself.
A negative result closes "`DBBI` also needs unknown-order transposition"
the same way Phase 477-504 closed it for `FAED`. A positive result would be
unprecedented and would require immediate, separate re-scoping (consumer
identification, cross-check against `matrixsumlist`, etc.) — out of scope
here.

## Why this is a materially smaller, more tractable search than FAED's

`FAED` is 570 raw symbols (`570 = 2 x 3 x 5 x 19`, sixteen divisors — Phase
477-504 used widths 19 and 30, both exact divisors, and still needed
simulated annealing / CSP search because `19!`/`30!` are far too large to
enumerate). `DBBI` is 91 raw symbols with exactly one nontrivial
factorization: `91 = 7 x 13` (divisors `{1, 7, 13, 91}`, confirmed by direct
computation against the pinned `DBBI` string in `tools/gsmg/data.py`). That
means the only two nontrivial rectangular widths are 7 and 13:

- width 7 (13 rows): `7! = 5,040` orders per escape pair — trivially
  exhaustible, almost certainly in well under a second per pair even in
  pure Python.
- width 13 (7 rows): `13! = 6,227,020,800` orders per escape pair — large,
  but roughly three orders of magnitude below `FAED`'s smallest tested
  width (`19!`), and within the demonstrated throughput class of this
  project's existing GPU/Rust infrastructure (Phase 429's Bifid GPU search
  benchmarked ~1 billion candidates/second, and the Phase 512 Rust CSP
  engine already does MRV/forward-checking pruning of exactly this shape
  of search). Whether a straight port of that infrastructure reaches full
  exhaustion per pair in minutes or hours is a real open engineering
  question for the development pass below, not asserted here.

Both widths admit **exhaustive or near-exhaustive** search, not merely
annealed/heuristic search. That's a strictly stronger guarantee than what
`FAED` received — there is no "a smarter search might have found it"
residual doubt if this phase actually completes at both widths.

## Frozen inputs

- `DBBI` raw stream, pinned by its own SHA-256 (already pinned elsewhere in
  the project; a Phase 516 execution lock must re-pin it independently
  before any real run, per this project's standard discipline).
- Widths: `(width=7, rows=13)` and `(width=13, rows=7)` — both orientations,
  since they are genuinely different transpositions and the cost of testing
  both is negligible at these sizes.
- Escape pairs: all pairs that validly segment `DBBI`'s as-observed (no
  transposition applied) raw stream via the existing, already-validated
  `segment_raw()` — **29 of the 36 possible pairs**, confirmed by direct
  execution against the pinned `DBBI` string (`phase484a_raw_symbol_vic_solver.segment_raw`).
  `DBBI`'s established code-IC-best pair `{b,e}` (rank 1 of 36, per
  `checkerboard_code_ic_oracle.py` and `GSMG_OBJECT_DBBI.md`) is among the
  29 valid pairs (63 tokens under identity order). This identity-order check
  is a tooling sanity check, not the search itself — validity and token
  count for a given candidate order must be re-evaluated per-candidate
  during the actual search, exactly as it implicitly is for `FAED`'s solver.
- Scoring objective: reuse the same English quadgram/IoC board-search
  objective already validated for `FAED`'s width-19/30 solver
  (`phase484a`/`phase484q`/`phase490`/`phase499` family), not a new
  invented metric.
- Null calibration: reuse this project's standard shuffle-gate methodology
  (e.g. Phase 319, Phase 477) — run the identical search against the exact
  `DBBI` symbol multiset shuffled, to establish the real chance-level best
  score at each width before judging any real candidate.

## What the development pass (before any real DBBI run) must establish

Following this project's standing discipline (development phase before
locked real run — see Phase 512A before 512G, Phase 484's small-width
powering before its real FAED test), a follow-up development phase must
close these before a real `DBBI` run is authorized:

1. **Adapter, not full rewrite.** Confirm whether the existing width-19/30
   pipeline's scoring/search internals are genuinely width-agnostic under a
   parameter change, or whether `WIDTH`/`ROWS`/target are hardcoded deeply
   enough (as they are in the outer wrapper scripts, e.g.
   `phase504_locked_faed_width19_unrestricted.py`'s module-level
   `PAIR=('g','i'); WIDTH,ROWS=19,30`) that a dedicated `DBBI` variant needs
   to be written rather than parameterized. Either is fine; this just needs
   to be known before committing to an implementation shape.
2. **Width-7 exhaustive pass, all 29 valid pairs, synthetic-planted
   controls first.** Plant a known short phrase into a synthetic width-7
   board built from `DBBI`'s own multiset, confirm the exhaustive search
   recovers it at rank 1, exactly as Phase 484's small-width powering did
   for `FAED`'s solver before any real run.
3. **Width-13 feasibility benchmark.** Measure real per-pair wall-clock
   cost for a `13!`-order exhaustive sweep on the actual available hardware
   (CPU/Rust/GPU) before committing to full 29-pair coverage. If full
   exhaustion per pair is cheap (per the Phase 429/512 throughput
   precedent), run all 29 pairs; if not, escalate coverage the same way the
   `FAED` line did — start with `{b,e}` alone, expand only if cost allows,
   and say explicitly which pairs were actually completed versus deferred.
4. **Shuffle-null baseline at both widths**, run before the real `DBBI`
   pass, not after, so any real-candidate score is judged against a
   pre-registered chance distribution rather than eyeballed post hoc.

## Decision rule

- A candidate is only a genuine positive if its score clears the
  pre-registered shuffle-null threshold (not merely "looks vaguely
  English" — this project's own history, e.g. the BTCSEED `16!` search's
  "quadgram gain is selection-driven relabeling, not plaintext" finding
  (Phase 433), is a direct warning against treating raw quadgram-score
  wins as evidence at this search scale without a null).
- If width 7 and width 13 both complete exhaustively (all planned pairs,
  both orientations) with no candidate clearing the null, this closes the
  "`DBBI` needs unknown-order transposition too" hypothesis at the same
  confidence level Phase 477-504 closed it for `FAED` — arguably stronger,
  given exhaustive rather than annealed coverage.
- This phase does not by itself reopen or close `G-YIN-001` or `G-MSL-001`;
  it only removes one specific technique-class gap this project's own
  coverage matrix flagged
  ([GSMG_TECHNIQUE_TARGET_COVERAGE_MATRIX](../GSMG_TECHNIQUE_TARGET_COVERAGE_MATRIX.md)).

## Non-goals

- Does not assume `{b,e}` is DBBI's correct pair — all 29 valid pairs are
  in scope for width 7 at minimum, matching the all-36-pair discipline
  `FAED`'s solver used.
- Does not introduce padding, ragged rows, or non-rectangular layouts for
  `DBBI` — `G-MSL-001`'s own registry text already notes no source
  licenses those, and this phase stays inside the exact `7x13`/`13x7`
  rectangular factorization the same way `FAED`'s widths were exact
  divisors of 570.
- Does not attempt a crib-based (Phase 512-style) validator for `DBBI` —
  today's session already found the only candidate crib
  (`ncsyangcahiriasogaleafayanestve`) has unresolved, multiply-caveated
  provenance (it is a subsequence of an *unrelated* earlier-stage
  plaintext, index-selected by an unreproduced community rule, not `DBBI`'s
  own content) and does not clear this project's exact-crib motivation bar.
  Scoring stays quadgram/IoC-plus-null, the same class of validator
  `FAED`'s solver used.
