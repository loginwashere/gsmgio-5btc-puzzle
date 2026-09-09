# Phase 486 width-30 depth-6 board-objective switch audit

Date: 2026-09-09

## Outcome

Dev-only, synthetic, unpowered result. Starting from Phase 484's width-30
raw-symbol VIC order+board joint solver (a packed-key collision fix already
let it fully recover any fixture whose true depth-8 fragment survives the
coarse shortlist, but only ~3/10 fresh dev fixtures retained that survival),
this session's work moved the invariant-to-board-objective scoring switch one
depth earlier (depth 6 instead of depth 7) and combined it with a
parent-reserved beam-reservation bridge at the depth-10->11->12 transition.
Under the full pipeline, **3 of 4 tested fresh dev fixtures (15, 21, 22) now
recover the exact true order end-to-end with 100% plaintext accuracy**, up
from roughly 3/10 surviving even to a partial shortlist before this session.
Fixture 19 remains a genuine, unexplained counterexample. No FAED ciphertext
was imported and no holdout fixture was consumed at any point
(`faed_scored: false`, `holdout_consumed: false` throughout).

## Background

Phase 484's width-30 pipeline narrows the 30! column-order search with a
beam: score depth-N column-prefixes, keep the top-K, extend by one column,
repeat. Early depths (4-7) score candidates with a cheap permutation-invariant
order statistic; from a switch depth onward, candidates are scored by
fitting a 25-slot checkerboard with GPU simulated annealing and using the
quadgram log-likelihood under the best fit ("the board objective"). A prior
session fixed a packed-key collision bug in the selector that was silently
merging distinct paths past depth 12; once fixed, the pipeline achieved exact
recovery on fixtures 16 and 20 whenever their true depth-8 fragment survived
to the refined population — but that survival itself was the bottleneck,
happening for only about 3 of 10 fresh fixtures.

## What this session found, in order

**1. Row cross-validation (negative).** Tested whether fitting a board on a
subset of rows and scoring only held-out rows would separate true window
candidates from structurally unrelated background candidates better than
plain full-row board fitting. On a background-pool test (23 true depth-8
windows vs. up to 400 random unrelated depth-8 candidates), cross-validation
showed a small, non-robust improvement on median-case ranking but *worse*
best/worst-case ranks than the plain baseline, and giving it 3x the annealing
budget made every metric worse, not better. This line was closed as not
outperforming plain full-row fitting.

**2. The depth-10-\>11 "cliff" (from a parallel continuation of this work).**
A rolling-extension probe on fixture 15 showed the true window's rank
improving steadily through depth 10 (1,098,233 -\> 218,117 -\> 77,317 -\>
45,288 across depths 8-10) then collapsing to 1,174,176 at depth 11 and being
cut by the top-262,144 selection — a single-step shock after being
consistently strong, not a gradual decline.

**3. A reproducibility gap (methodological caveat).** Attempting to replay
this cliff to measure the true child's rank among only its own parent's local
extensions failed: the identical script, arguments, input population, and
binary (verified by SHA-256) reproducibly gave a *different* depth-7
board-objective rank across two separate time windows roughly 30 minutes
apart (180,915 vs. 508,396), while being perfectly self-consistent *within*
each window across repeated process launches. The per-candidate GPU
simulated-annealing seed was confirmed, by reading the CUDA kernel directly,
to be a pure deterministic function of path content (not batch position or
any hash-randomized value), so this is not a seeding-logic bug. No dependency
file changed between the two windows. The root cause was not identified. Any
single reported rank number anywhere in this investigative arc should be read
with this caveat; the qualitative, repeatedly-reproduced conclusions below
(steady erosion vs. single-step cliff; "rescued" vs. "not rescued") are more
robust than any individual number.

**4. Parent-reserved bridge (positive; fixture 15 fully solved).** Instead of
a single flat global top-K cut at the depth-10-\>11 step, the fix takes the
top-scored depth-10 parents and reserves each one's own best few children
before any global cut. Applied to fixture 15: the true depth-11 fragment
barely survived reservation (rank 351,881 of 495,495 — would have been cut by
a flat top-262,144), then recovered to rank 29,973 by depth 12. Carried
through a checkpointed rolling extension to depth 30 and a final
multi-restart resolution pass, fixture 15 reached **exact_order_final_rank =
1, top1_plaintext_accuracy = 1.0** — full exact-order, exact-plaintext
recovery.

**5. Fixed-schedule generalization test (negative on 3/3).** The exact same
schedule, unmodified, applied to three fresh untuned dev fixtures (19, 21,
22): all three failed completely (plaintext accuracy 0.08-0.26, no
exact-order match). All three lost the true window at the very first
invariant-only selection cut at depth 7 — well before the depth-10-\>11
bridge mechanism is ever reached, so the bridge was never actually tested for
these three.

**6. Diagnosing the early failure.** A per-depth true-rank trace for fixture
22 under the pure invariant score showed steady, multiplicative erosion, not
a cliff: rank 25 (depth 4) -\> 6,032 (depth 5) -\> 55,156 (depth 6) -\>
1,652,569 (depth 7) — roughly 10x worse in percentile terms at every step.
A follow-up check found the true depth-7 extensions ranked only mid-pack
(5th-24th of 48) among their own true depth-6 parent's local children —  a
real but weak local signal, unlike the depth-10 cliff's "locally strong,
globally unlucky" pattern. A generous parent-reservation variant at this
earlier depth (top 65,536 parents by score, top 16 children each) still
failed to keep any true window alive to depth 7: only 1 of fixture 22's 3
true depth-6 parents even survived the top-65,536-by-score parent
pre-filter, and its true children still missed the local top-16.

**7. Depth-6 board-objective switch (positive).** Switching to board-
objective scoring one depth earlier — at depth 6 instead of depth 7 — tests
whether the *invariant metric itself* was the weak link, rather than the
selection mechanism. For fixture 22, the same depth-6 population that scored
rank 31,857 under the invariant metric jumped to **rank 7** under the board
objective, then **rank 1 of 12,582,912 candidates** by depth 7. Fixture 21
showed the same pattern, less extreme (rank 284,271 -\> rank 2,079 -\> rank
475 of 12.6M). Fixture 19 was a genuine counterexample: board-objective
scoring made its rank *worse*, not better (393,204 -\> 499,424), and it still
failed to survive selection.

**8. Full pipeline on the two rescued fixtures.** Running the complete
schedule (depth-6 switch, strong re-anneal refine, rolling extension through
depth 10, the parent-reserved bridge, rolling extension through depth 30,
final resolution) on fixtures 21 and 22: **both reached
exact_order_final_rank = 1 and top1_plaintext_accuracy = 1.0.** In both
cases the true window did not just survive but dominated — rank 1-6 of
roughly 12.6 million candidates at every depth from 8 through 12 — with none
of the near-miss drama fixture 15's original run needed at the bridge step.

## Results table

| fixture | invariant-only outcome | depth-6-switch outcome | full-pipeline final result |
|---|---|---|---|
| 15 | (already board-switched at depth 7; needed the bridge to survive a depth-11 cliff) | not re-tested | exact rank 1, 100% plaintext |
| 21 | fails at depth 7 (invariant rank not tested to exhaustion) | depth-6 rank 284,271 -\> board rank 2,079 -\> depth-7 rank 475/12.6M | exact rank 1, 100% plaintext |
| 22 | fails at depth 7 (invariant rank 1,652,569, outside 1,048,576 keep) | depth-6 rank 31,857 -\> board rank 7 -\> depth-7 rank 1/12.6M | exact rank 1, 100% plaintext |
| 19 | fails at depth 7 | depth-6 rank 393,204 -\> board rank 499,424 (worse) | not reached; still fails |

## Limits

- Entirely synthetic development work. No FAED ciphertext was imported and
  no holdout fixture was consumed at any stage (`faed_scored: false`,
  `holdout_consumed: false` on every result artifact produced this session).
- Not powered or locked. None of Phases 484Z or 484AA-AI ran under an
  execution-lock/verify_run gate; there is no frozen holdout family and no
  calibrated null distribution behind any of these numbers.
- Only 4 fixtures were tested, and not as a pre-registered random sample —
  they were the fixtures already in use from earlier sessions. The true
  success rate of this pipeline over a properly sampled fixture population is
  unknown; the natural next step is running the same fixed schedule across a
  larger, explicitly enumerated dev fixture set.
- Fixture 19's failure under the depth-6 switch is unexplained. Whether an
  even earlier switch (depth 5), a different early-selection score, or some
  fixture-specific property would rescue it is untested.
- The reproducibility gap in the GPU board-annealing scorer described above
  (item 3) was not root-caused. It did not visibly affect the depth-6-switch
  and full-pipeline results (each of which is a single continuous process
  run, internally consistent), but no cross-run bit-for-bit reproducibility
  guarantee currently exists for this codebase's board-objective scoring.
- The row cross-validation approach (item 1) is closed as not outperforming
  plain full-row board fitting and is not part of what worked here.

## Reproduction

```bash
cd tools/gsmg
# earlier-switch smoke test (depth 6 vs the prior depth-7 switch), one fixture:
python3 phase484ah_width30_early_switch_depth_probe.py --run --fixture-index 22 --switch-depth 6

# full pipeline (depth-6 switch -> refine -> rolling to d10 -> parent-reserved
# bridge -> rolling to d30 -> final resolve), one fixture:
python3 phase484ai_width30_early_switch_full_solve.py --run --fixture-index 22 \
    --work-dir ../../_work/phase484ai/i22

# parent-reserved bridge alone, generalized to the earlier depth-6->7 step
# (the negative early-reservation-only result, item 6):
python3 phase484ag_width30_early_parent_reserved_probe.py --run --fixture-index 22

# row cross-validation background-pool test (the closed negative, item 1):
python3 phase484z_width30_row_holdout_probe.py --run --mode background --fixture-index 15
```
