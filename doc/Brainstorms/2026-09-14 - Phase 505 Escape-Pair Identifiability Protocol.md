# Phase 505 escape-pair identifiability protocol

Date: 2026-09-14
Status: draft implementation and 72-fixture manifest prepared; execution lock
not issued

## Question

Can the width-19 unrestricted-board English objective distinguish the true
checkerboard escape pair from the other 35 pairs under Model B?

This is the next diagnostic after Phase 504's bounded `{g,i}` miss. Under
Model B, FAED's witnessed segmentation is not transposition-invariant, so
`{g,i}` remains a model-conditioned prior rather than a measured selector.
Another `{g,i}` seed would leave that load-bearing assumption untouched.

## Scope

Phase 505 is synthetic and closed-system. It uses:

- the already-frozen nine-symbol FAED histogram, not FAED's order;
- raw length 570 and exact width 19;
- all 36 unordered pairs from `itertools.combinations("abcdefghi", 2)`;
- the existing closed English corpus and quadgram table;
- an unrestricted 25-slot checkerboard objective;
- deterministic PCG32 seeds.

It does not import or score FAED, call the P32 oracle, inspect community
messages, add vocabulary, or search for new clues.

## Why two gates are required

A true pair can fail for two fundamentally different reasons:

1. **objective non-identifiability:** even with the correct transposition
   order supplied, a wrong segmentation plus a freely optimized board scores
   as well as or better than the true pair;
2. **blind-search failure:** the objective could distinguish the pair at the
   true order, but the order search never reaches comparable candidates.

The first is much cheaper to test and is necessary for the second. Therefore
Phase 505A is implemented first. Phase 505B remains unimplemented and cannot
be locked until 505A passes.

## Phase 505A: known-order pair ceiling

### Fixture construction

For every true-pair index 0--35, construct two development fixtures (logical
indices 0 and 1): 72 fixtures total. For each pair, scan construction
candidate indices upward from zero and retain the first two that pass the
already-frozen edit/language gates and occupy distinct source regions. This
eligibility scan uses no solver score. Candidate index and all rejected
construction reasons are recorded in the pre-lock manifest.

- The hidden raw stream has exactly the frozen symbol counts
  `(54,49,52,49,69,57,107,58,75)` for `a` through `i`.
- For the fixture's true pair, deterministically shuffle that multiset until
  it segments without a dangling escape. Latent token counts are outputs.
- Build the exact minimum-L1 unrestricted board by pairing all 25 passage
  letter frequencies with all 25 sampled code frequencies in descending
  order. There is no seven-single/eighteen-double partition constraint. This
  prevents the old partition from becoming a hidden pair selector and matches
  the hypothesis tested by Phase 504.
- Apply the minimum number of score-aware substitutions required to realize
  the sampled token counts.
- Retain only fixtures satisfying an edit-fraction ceiling `0.21` and the
  existing normalized-quadgram floor `-4.70`. The 0.21 ceiling was set from a
  solver-blind structural scan before any pair score was computed: among the
  first 200 construction candidates per pair, the worst second-best distinct
  source region required `0.2033195021` edits. The earlier 0.18 ceiling was
  calibrated only for `{g,i}` and would exclude several pairs by construction.
- Encrypt with a deterministic independent width-19 column order.

Before a lock, all 72 fixture constructions must be materialized and pass.
If any pair lacks two eligible candidates within the frozen first 200
construction candidates, the universe is revised transparently before
locking; no post-lock replacement is permitted.

### Scoring

Supply the planted transposition order, restoring each fixture's hidden raw
stream. For every one of the 36 assumed escape pairs:

1. segment the same raw stream under that pair;
2. treat a dangling escape as a definite invalid cell;
3. otherwise fit an unrestricted 25-slot board with `8 x 20,000` annealing,
   the budget shown sufficient by Phases 495--496;
4. record normalized quadgram score, decoded length, best restart, and, only
   for the true pair, planted-board accuracy.

Rank all valid pairs by descending normalized score and canonical pair index
as the tie-break. No readability judgment enters the gate.

### Proposed gate (not locked yet)

The draft promotion rule is conjunctive:

- true pair ranks first on at least 65 of 72 fixtures;
- true pair ranks in the top three on all 72 fixtures;
- median true-pair score minus best-wrong-pair score is positive.

These thresholds must be reviewed and frozen before execution. Failure stops
the pair-selection path: a blind FAED pair screen would then be
uninterpretable under this objective.

As a scale reference, under an exchangeable random-ranking null each pair has
probability `1/36` of rank 1 and `3/36` of reaching the top three. If the 72
fixtures were independent, `P(X >= 65)` for rank-1 outcomes would be about
`8.40e-93`, and the probability of 72/72 top-three outcomes would be about
`1.99e-78`. The fixtures share a corpus, histogram, generator, and objective,
so these are explanatory chance references rather than calibrated p-values.
The gate is intentionally a demanding recovery-power requirement, not a null
hypothesis test.

### Runtime projection and checkpoint rule

A pre-lock benchmark on any of the 72 committed fixtures is prohibited: the
timing call would necessarily compute the pair-ranking outcomes that the lock
is meant to protect. Instead, the pre-lock projection uses already-recorded
full-board timings. Phase 503 fit eight terminal boards at `4 x 10,000` in
`6.10 s`; Phase 504 fit five in `11.23 s`. Naive linear scaling to 36 boards
at `8 x 20,000` gives approximately 110--323 seconds per fixture, or 2.2--6.5
hours for 72 fixtures. GPU batching may reduce that, but the lock must not rely
on the optimistic case.

The runner records wall time and writes an atomic progress checkpoint after
every fixture. After the first locked fixture it reports the simple
`72 x first_fixture_seconds` projection. A long runtime may pause and resume
the unchanged run; it may not change budgets, fixtures, scores, or the gate.

## Phase 505B: blind observable selector (conditional, not implemented)

Passing 505A would establish only an objective ceiling. It would not license
ranking FAED pairs, because real FAED does not reveal its order.

The next implementation would train one shared, pair-balanced invariant model
over all 36 pair labels, then run a blind front-stage matrix in which each
fixture is evaluated under every assumed pair. The selection statistic must
use only fields available for unresolved ciphertext (for example the best
refined normalized score and predeclared population summaries), never true
order, board accuracy, or plaintext accuracy.

The full matrix is potentially 1,296 front runs for one fixture per true pair.
Before locking it, benchmark exactly three true-pair rows (108 cells), project
wall time, and either optimize batching or obtain explicit approval for the
frozen cost. The universe may not be narrowed after observing pair outcomes.

Only a locked, powered 505B selector could authorize a real all-36-pair FAED
screen. The real screen would itself be separately locked and would select a
fixed small number of pairs for full solving; it would not silently promote
`{g,i}`.

## Deliverables prepared before execution

- this protocol draft;
- `phase505_escape_pair_identifiability.py`;
- CPU-only unit tests and `self_test()`;
- `phase505_fixture_manifest.json`, containing all 72 accepted fixture
  commitments and all 172 preceding construction rejections;
- an atomic result format for 505A.

The manifest contains 36/36 pairs, 72 unique raw/profile hashes, plaintext
lengths 429--485, edit fractions 0.09469--0.20868, and normalized quadgram
scores -4.50022 to -4.06868. These are construction diagnostics only; no
wrong-pair board score has been computed.

Not prepared yet: execution lock, GPU result, Phase 505B implementation, or
any FAED runner. The `--run-ceiling` path must fail closed until the execution
lock is explicitly issued and verifies.
