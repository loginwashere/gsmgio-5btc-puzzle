# Phase 487 width-30 dual-lane root-lineage audit

Date: 2026-09-10

## Outcome

Dev-only, synthetic, unpowered result. Phase 486 left fixture 19 as a
genuine, unexplained counterexample to the depth-6 board-objective switch
and parent-reserved bridge. This session traced why (its true depth-8
fragment is strong within its own ancestry but globally weak, so a flat
top-K beam discards it), built a root-lineage beam that keeps descendants
per original root and prunes purely by score, and combined it with Phase
486's mechanism into one fixed schedule with two lanes: lane A (Phase 486's
wide parent-local refinement + bridge) and lane B (the new root-lineage
beam, released into the ordinary extension at depth 11), merged by score at
depth 12. Every cut in both lanes and the merge was verified in source to be
score-only; synthetic truth is computed after selection purely for
diagnostics. **4 of 4 dev fixtures tested under this schedule (13, 14, 15,
19) now recover exact order end-to-end**, including fixture 19 for the first
time. Fixture 19's completion reused early checkpoints from a prior
diagnostic run rather than running fully from scratch; a from-scratch
confirmation is queued. No FAED ciphertext was imported and no holdout
fixture was consumed at any point (`faed_scored: false`,
`holdout_consumed: false` throughout).

## Background

Phase 486 fixed fixtures 15, 21, and 22 by switching the invariant-to-board-
objective scoring transition one depth earlier and bridging the depth-10-\>11
cliff with per-parent reservation instead of a flat cut. Fixture 19 was run
under the exact same schedule and failed -- the depth-6 switch made its rank
*worse* (393,204 -\> 499,424), and the failure was left unexplained at the
end of that audit.

## What this session found, in order

**1. Fixture 19 is locally strong, globally weak (diagnosis).**
`phase484am_width30_root_lineage_beam.py` traces one metric the flat beam
throws away: how a candidate ranks among its own ancestor's other children,
not just globally. For fixture 19, this ancestry-local signal was
consistently present even where the global rank was hopeless, unlike a
fixture that is simply unrecoverable at that depth.

**2. Root-lineage beam (mechanism, score-only).** Starting from a depth-7
population where each candidate is tagged with its originating root ID, the
beam expands every root's children, keeps a fixed number of the
best-scoring children *per root* (`select_per_root`, via `np.lexsort` on
score -- never touching synthetic truth), and periodically re-ranks roots by
their single best descendant score and drops the weakest
(`prune_root_population`, same score-only mechanism). This never inspects
which candidate is correct; `true_root_ranks` etc. are computed from the
selected population afterward, for reporting only -- verified by reading
`phase484am_width30_root_lineage_beam.py` and
`phase484an_width30_dual_lane_dev.py` directly, not inferred from behavior.

**3. Traced recovery on fixture 19 (positive, diagnostic run).** Running the
root-lineage beam from depth 7: the true root's global rank moved from
535,849 of 655,360 (depth 8) to 220,778 of 655,360 (depth 9) to 2,636 of
262,144 after pruning to 262,144 roots (depth 10) to 129 of 65,536 after
pruning to 65,536 roots (depth 11). Released into the ordinary rolling
extension at that point (not kept in lineage-protected form indefinitely),
it reached rank 2 of ~10M at depth 12, rank 1 by depth 16, and held there --
`exact_order_final_rank=1`, `plaintext_accuracy=1.0` at depth 30. This first
confirmed that lineage protection has a natural, fixed release depth (11)
rather than needing to be carried through the whole 30-depth search.

**4. One unified schedule, two lanes (mechanism).**
`phase484an_width30_dual_lane_dev.py` packages lane A (Phase 486's mechanism,
depth 7 -\> parent-local depth-8 refine -\> bridge -\> depth 12) and lane B
(the root-lineage beam above, depth 7 -\> depth 12) as one fixed
`SCHEDULE`/`schedule_sha256`, merges their two 262,144-candidate populations
by score to 262,144 at depth 12 (`merge_populations`, also score-only), and
carries the merged population through depth 30 and final resolution with no
branch that depends on which fixture is running.

**5. The merge survives dilution (the decisive check).** The open question
after (3) was whether lane A's much larger, always-present competing
population would crowd lane B's fragile rank-2 truth out of the merge cut.
Re-running lane B under the committed schedule (reusing the depth-7/lane-A
checkpoints from the diagnostic run, since they were already produced under
matching schedule constants) reproduced the depth-9 root rank bit-for-bit
(220,778) and confirmed the merge does not dilute it: lane A's 262,144
candidates carried zero true segments through depth 12, yet the merged
262,144 population still carried lane B's truth through depths 13-30 to
`exact_order_final_rank=1`, `plaintext_accuracy=1.0`.

**6. Fixture 15 under the identical unified schedule (positive, and a
useful negative for lane B).** Run fully fresh (no reused checkpoints) end
to end: lane B actually *lost* fixture 15's truth by depth 8
(`true_roots_after: []` from depth 8 onward) -- the root-lineage beam does
not rescue fixture 15, lane A does, exactly as expected since fixture 15 was
already solved by Phase 486's mechanism alone. The merged run still reached
`exact_order_final_rank=1`, `plaintext_accuracy=1.0`, confirming the two
lanes are complementary rather than one lane silently doing all the work on
every fixture.

**7. Fixtures 13 and 14, no special-casing (positive).** Run fully fresh
under the same unified schedule with no fixture-specific tuning: both
reached exact top-1 (plaintext accuracy 1.0 and 0.986 respectively, ~71
minutes each).

## Results table

| fixture | provenance | lane A alone (prior work) | lane B (root-lineage) | merged result |
|---|---|---|---|---|
| 13 | fully fresh, this session | not separately tested | not separately tested | exact rank 1, 100% plaintext |
| 14 | fully fresh, this session | not separately tested | not separately tested | exact rank 1, 98.6% plaintext |
| 15 | fully fresh, this session | already solved (Phase 486) | loses truth by depth 8 | exact rank 1, 100% plaintext |
| 19 | depth-7/lane-A checkpoints reused; lane B, merge, d13-30 fresh | fails (Phase 486, unexplained) | rank 220,778 -\> 2,636 -\> 129 -\> released -\> rank 2 (d12) -\> rank 1 (d16) | exact rank 1, 100% plaintext |

## Limits

- Entirely synthetic development work. No FAED ciphertext was imported and
  no holdout fixture was consumed at any stage (`faed_scored: false`,
  `holdout_consumed: false` on every artifact produced this session).
- Not powered or locked. No execution-lock/verify_run gate, no frozen
  holdout family, no calibrated null distribution.
- Fixture 19's confirmation under the unified schedule reused its depth-7
  population and lane-A-through-depth-12 checkpoints from an earlier
  diagnostic run rather than invoking `run_fixture()` fully from scratch.
  The schedule constants match and the code path is identical, but this has
  not been verified byte-for-byte against a from-scratch run. A fully fresh
  `run_fixture(19, ...)` with no reused state is queued as part of item
  below.
- Only 4 of the ten development fixtures used for this line of work (13-22)
  have been run under the exact unified schedule; the remaining six
  (16, 17, 18, 20, 21, 22) have not. Fixtures 21 and 22 already solved under
  Phase 486's mechanism alone and are expected to pass again (lane B should
  behave like it did for fixture 15 -- irrelevant, not harmful), but that is
  an expectation, not a measurement. The plan's own gate for this step is
  9/10 exact recoveries across 13-22; that has not yet been evaluated.
- No frozen holdout split has been generated or run. Per the standing plan,
  FAED must not be attempted until a fresh, previously untouched holdout
  split clears its own gate (provisionally 10/12).
- Runtime is substantial: each fresh fixture takes roughly 70-75 minutes on
  the one available GPU, dominated by lane B's root-lineage expansion at
  depths 9-11 (each root-count chunk requires its own GPU-annealed board
  fit). A full 10-fixture sweep is on the order of half a day of sequential
  compute.

## Reproduction

```bash
cd tools/gsmg

# root-lineage beam alone, one depth step (score-only selection; truth is
# reported afterward for diagnostics only):
python3 -c "
import phase484am_width30_root_lineage_beam as lineage
lineage.run_depth('<depth7-or-later-checkpoint>.npz', fixture_index=19,
                   descendants_per_root=4, root_chunk=16384)
"

# full unified dual-lane schedule, fully fresh, one fixture:
python3 phase484an_width30_dual_lane_dev.py --run --fixture-index 19 \
    --work-dir ../../_work/phase484an_sweep/i19

# regression tests for both new modules:
python3 -m unittest test_phase484am_width30_root_lineage_beam
python3 -m unittest test_phase484an_width30_dual_lane_dev
```
