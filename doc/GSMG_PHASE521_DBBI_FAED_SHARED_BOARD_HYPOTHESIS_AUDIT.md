---
type: audit
phase: 521
date: 2026-09-17
status: complete
result: no-calibrated-shared-board-consistency
disposition: corroboration-only-no-gap-closure
script: tools/gsmg/phase521_dbbi_faed_shared_board_hypothesis_audit.py
---

# GSMG Phase 521 — DBBI+FAED Shared-Board Hypothesis

## Question

Follow-up to Phase 520, which forced ONE shared escape pair on the raw
`DBBI+FAED` concatenation and found no coherence. The user's refined
question: escape-pair choice and board-key choice are logically separate
steps of a straddling checkerboard — the pair only decides which raw
symbols are escapes (and therefore how the raw stream segments into
codes); the board decides which letter sits in which of the 25 slots.
What if each stream keeps its own already-established, independently-best
escape pair (DBBI: `be`; FAED: `gi`) for segmentation, and only the board
key is hypothesized to be shared?

This speaks directly to a fact Phase 371/`G-ESC-001` already recorded —
"each stream's own independently-best escape pair differs" — previously
read as evidence against a joint construction. This phase tests whether it
has to be: a genuine single-board construction could legitimately use
different escape pairs per segment while still sharing one underlying
board.

## Method

`tools/gsmg/phase521_dbbi_faed_shared_board_hypothesis_audit.py`. Statistic:
`cost_of_sharing = S_independent - S_shared`, where `S_independent` is the
sum of each stream's own independently-annealed best board score, and
`S_shared` is the best score achievable by ONE board key annealed jointly
to fit both streams' own-pair-segmented code sequences at once (each
stream scored on its own contiguous quadgram windows only — no spurious
cross-boundary window is ever formed). `cost_of_sharing >= 0` always, by
construction, since independent optimization is a strict superset of the
shared-key search space.

Matched nulls: independent Euler-traversal and endpoint-fixed-shuffle
surrogates of DBBI/FAED (reusing Phase 459/460's exact validated
generators), each surrogate pair's own best escape pair re-selected the
same way as the real data (not forced to `be`/`gi`), then the same
`cost_of_sharing` statistic computed. Because the joint annealer is
expensive, this reuses Phase 516's own established two-tier discipline: a
**cheap** budget (6,000 iterations × 2 restarts, Phase 516's
`CHEAP_ITERS`/`CHEAP_RESTARTS`) for the real primary statistic *and* every
one of 500 null replicates per null (matched budget — an apples-to-apples
comparison), plus a separate **expensive** budget (60,000 × 30, Phase
516's `REFINE_*`) confirmation of the real statistic only, reported as a
robustness diagnostic and never directly p-compared against the cheap
null.

## Result

| | Pairs | `S_independent` | `S_shared` | `cost_raw` | `cost_normalized` |
|---|---|---:|---:|---:|---:|
| Real (cheap budget) | `be`/`gi` | `-2755.22` | `-2807.32` | `52.10` | `0.1057` |
| Real (expensive budget, diagnostic) | `be`/`gi` | `-2697.68` | `-2791.23` | `93.55` | `0.1898` |

| Null (cheap budget, 500 trials) | Extreme count | One-sided p | Median | Max |
|---|---:|---:|---:|---:|
| Euler-traversal (primary) | 26/500 | `p=0.053892` | `0.1830` | `0.3618` |
| Endpoint-fixed shuffle (sensitivity) | 11/500 | `p=0.023952` | `0.1945` | `0.4096` |

The real cost-of-sharing sits below both nulls' medians and neither
reaches the pre-registered `p<=0.005` promotion bar, though both land in
the `p<0.1` range rather than dead-center on the null (unlike Phase 520's
flatly unremarkable `p=0.43`). **Decision: `no_calibrated_shared_board_consistency`**
— using the same controlled-vocabulary distinction Phase 460 established
for "positive-looking but not robust under both matched nulls at the
declared bound," not a flat "nothing at all" result.

The expensive-budget diagnostic cautions against reading the cheap-budget's
mild trend as a real signal: with 10× the search budget, `cost_of_sharing`
nearly *doubles* (`0.1057` → `0.1898`) rather than shrinking. More search
finds a better independent optimum for each stream separately faster than
it improves the constrained joint search's ability to close the gap —
exactly the pattern expected if there is no real shared board to find, and
the cheap-budget's small null-beating margin is annealing noise at that
budget rather than a genuine effect.

## Disposition

No calibrated evidence that DBBI and FAED could share one board key while
each keeps its own independently-best escape pair. The result is not as
flatly negative as Phase 520's literal-concatenation test, but the
expensive-budget diagnostic gives a specific, mechanistic reason not to
promote the cheap-budget's mild trend: it moves the wrong direction as
search quality improves. This is **corroboration_only** — it does not
select a board, does not reconcile `G-ESC-001`'s differing-pair
observation, and does not reopen or close `G-YIN-001`. It also does not
rule out every joint-board idea (e.g. a shared board discovered by a
different optimization method, or one that requires transposition first);
it rules out the specific "single board, escape pairs unconstrained,
annealing-search-discoverable" version tested here.

## Facts affected

None.

## Supersedes/corrects

None.

## Artifacts

- `tools/gsmg/phase521_dbbi_faed_shared_board_hypothesis_audit.py` —
  implementation, self-test.
- `tools/gsmg/test_phase521_dbbi_faed_shared_board_hypothesis_audit.py` —
  4 tests (<2s, excludes the expensive null/joint-anneal run).
- `tools/gsmg/phase521_result.json` — full real-data result (cheap and
  expensive budgets, both null summaries).

## Reopen condition

Only on a new primary source or authenticated selector specifically
licensing a shared-board construction, or a genuinely different
(non-annealing) board-recovery method with demonstrated power this
annealing search lacks — not on re-running this construction again with a
larger cheap-budget trial count or different annealing schedule.
