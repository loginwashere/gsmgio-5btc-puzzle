# Phase 490 width-19 dual-lane port protocol

Date: 2026-09-12
Status: development protocol; not locked; FAED execution requires the single-fixture gate below

## Question

Can the width-30 solver architecture that cleared Phase 488's synthetic gates
be transferred to the distinct width-19 exact-grid geometry while retaining
the exact FAED `{g,i}` marginal profile?

This is not a continuation of Phase 489's width-30 seeds. Width 19 changes the
grid from 19 rows by 30 columns to 30 rows by 19 columns. A mechanical
permutation-family check confirms that complementary widths and inverse
directions are not equivalent families except at the identity-order special
case.

## Frozen inputs for development

- Synthetic fixtures only, from
  `phase484x_exact_faed_profile_power_probe.make_fixture()`.
- Escape pair `{g,i}` only.
- Raw length 570 and decoded length 436, reproducing all 25 token counts and
  all nine raw-symbol counts of FAED exactly. No FAED ordering or adjacency is
  imported.
- Standard Model-B direction only: checkerboard digits are written row-major
  and read by permuted columns.
- The seven-single/eighteen-double board partition remains the existing
  closed-training-corpus partition. No partition is learned from FAED.

## Staged implementation

1. Preserve and verify the Phase 488/489 terminal records that previously
   existed only under ignored `_work/` paths.
2. Port the partition-constrained CUDA scorer by changing only the exact-grid
   geometry from `WIDTH=30, ROWS=19` to `WIDTH=19, ROWS=30`; validate initial
   boards, window counts, returned partitions, and CPU/GPU score parity.
3. Run the completed width-19 schedule once, end to end, on exact-profile
   development fixture 14. This is an already-exposed hard fixture: its
   original width-19 run retained zero true fragments and reached only
   0.1121 plaintext accuracy; an earlier special run recovered it only after
   widening the shortlist to 1,048,576. Persist every stage needed to diagnose
   a miss. This is a proof-of-operation gate, not a recovery-rate estimate.
4. Pass only on exact top-1 order recovery. If it fails, remain synthetic-only
   and diagnose or revise the solver. Do not compensate by trying easier
   fixtures until one passes.
5. If fixture 14 passes, freeze the exact executable, parameters, seed, input
   hashes, and decision rule in a separate exploratory-real lock. Then run
   FAED once at `{g,i}`, width 19, using that one frozen schedule.
6. Inspect the complete ranked terminal set, not only rank 1. A readable,
   internally coherent plaintext is a lead requiring independent confirmation.
   A gibberish result is only a one-seed exploratory miss.
7. Additional synthetic campaigns, alternate seeds, shuffled controls, escape
   pairs, or widths require a later decision. They are deliberately not a
   prerequisite for this single solve-first screen and are not authorized by
   this protocol.

## Stop rules

- Failure to recover fixture 14 exactly at top 1 sends the work back to
  synthetic-only diagnosis; it does not authorize widening based on FAED.
- A real gibberish result is a single-run miss, not a formal rejection of the
  model, pair, or width.
- No other escape pair, width, inverse direction, split transform, or
  non-prose objective enters Phase 490.

## Current implementation checkpoint

- `phase490_width19_constrained_board_server.cu` is a minimal geometry/wire-
  magic port of the previously validated constrained kernel.
- `phase490_width19_dual_lane_dev.py` implements the development front stage
  and array/selection mechanics without importing FAED.
- CPU-side self-tests pass. The first CUDA build exposed that the copied
  width-30 kernel still expected magic `P484YQ1`; the width-19 client uses
  `P484QG1`. The mismatch failed closed before scoring and was corrected.
- The corrected CUDA binary was built locally from the cached CUDA 13 image;
  SHA-256 `bbc1788b57b5aac5a8f98b028b1af29a17acda84f4794d1c4f1030bda8600d49`.
  The initial sandbox did not expose the host device, but an approved host-GPU
  execution did. Runtime parity passes on eight exact-profile paths: exact
  initial boards, identical window counts, partition-respecting returned
  boards, and maximum CPU/GPU score error `3.552713678800501e-15`.
- The first front-stage launch was stopped at the user's request. It revealed
  no GPU failure: a post-score truth diagnostic was iterating millions of
  paths in Python. That non-evidential diagnostic and repeated-column
  validation are now vectorized; a 2.8-million-row diagnostic benchmark takes
  about 0.6 seconds. Solver scoring and selection are unchanged. No fixture
  result or checkpoint was produced before the stop.
- The earlier 9/10 development plus 10/12 holdout proposal was withdrawn in
  favor of the user's solve-first sequence above. No large calibration campaign
  is required before the one exploratory FAED run, and no strong negative claim
  can be drawn from that shortcut.
- `phase490_width19_checkpointed_dual_lane.py` ports the Phase-488 dual-lane
  continuation and commits an atomically hashed NPZ plus JSON record after
  every completed depth. On restart it validates the schedule, fixture, split,
  source hash, output hash, array geometry, scores, and column uniqueness before
  skipping a completed stage. An interruption after an NPZ rename but before
  its JSON commit causes that untrusted stage to be recomputed.
- Exact-profile development fixture 14 passed the proof-of-operation gate.
  The true fragment ranked first at the depth-6 and depth-7 board stages, the
  dual-lane continuation retained truth at every depth, and the exact complete
  order ranked first after independent final board resolution. Top-1 plaintext
  accuracy was `0.9862385321100917`; no holdout or FAED data was scored.
- Measured runtime was 278.05 seconds for the front stage and 2,489.92 seconds
  summed across continuation stages (about 46.1 minutes total). A complete
  restart audit skipped all 22 continuation/final stages and reproduced the
  result without GPU recomputation. The next action is the separately locked
  one-run exploratory FAED screen described in step 5; it has not started.

## Real-run implementation boundary

`phase490_locked_faed_width19_gi.py` is the separate real adapter required by
step 5. It freezes one `{g,i}`, width-19, Model-B run with the exact schedule
and seed that recovered development fixture 14. The exact-profile prefix
models are materialized from the closed synthetic training fixtures before the
FAED sentinel adapter is installed; an unexpected fixture request thereafter
fails closed. The lock pins the FAED digest, protocol, solver sources, corpus,
quadgram table, schedules, seed, and all three GPU binaries.

The front population and every continuation depth are restartable. Synthetic
truth diagnostics attached to the identity sentinel are explicitly
non-evidential and are removed from the authoritative result. All eight final
terminal candidates are retained for readability review. A miss remains one
exploratory seed only and does not close the pair, width, or cipher family.
