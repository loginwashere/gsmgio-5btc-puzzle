# Phase 488 width-30 dev sweep completion and holdout gate pass

Date: 2026-09-12

## Outcome

Dev-only and holdout-only, synthetic, unpowered result -- no FAED ciphertext
was imported at any point. Following Phase 487, a real split parameter was
threaded through every stage of the dual-lane pipeline (`phase484an`,
`phase484am`, `phase484ad`, `phase484ae`, `phase484ai`), fixing a latent bug
where every call site had hardcoded the literal string `"dev"` regardless of
which corpus split was actually intended. With that fixed, the frozen
schedule (`schedule_sha256=ca219a6b...`) was run cold against **all ten**
remaining development fixtures (13-22): **10/10 exact top-1 recoveries**,
clearing the plan's 9/10 dev gate. It was then run cold against **12
fixtures drawn from the codebase's genuine holdout corpus split**
(`FIXTURE_SPLITS = ("dev", "holdout")`), never touched by any tuning in this
line of work: **11/12 exact top-1 recoveries**, clearing the plan's 10/12
holdout gate. One holdout fixture (index 3) failed outright, losing the true
segment at the very first depth-7 selection stage. `faed_scored: false` and
`holdout_consumed: true` (holdout run only) on every artifact.

## Background

Phase 487 unified Phase 486's parent-reserved bridge (lane A) with a new
root-lineage beam (lane B) into one fixed, mechanically truth-blind
schedule, and validated it end-to-end on 4 of 10 development fixtures
(13, 14, 15, 19). The plan's next two steps were: (1) run the same schedule
on the remaining development fixtures to reach a 9/10 gate, then (2) freeze
it and run a single untouched holdout split of 12 fixtures, requiring 10/12,
before any FAED attempt.

## What this session found, in order

**1. A latent split-parameter bug would have invalidated the holdout gate.**
Before launching the holdout run, a grep across every `width30_fixture(`
call site in the dual-lane chain (`phase484ae`, `phase484am`, `phase484ad`,
`phase484ai`, `phase484an`) showed each one hardcoded `"dev"` -- there was no
`split` parameter anywhere in the chain, despite `width30_fixture()` itself
already supporting one. Running holdout fixture *indices* through this code
unmodified would have silently pulled dev-corpus text back out and mislabeled
every result `holdout_consumed: false`, invalidating the entire holdout gate
without any visible failure. Fixed by threading `split: str = "dev"` through
all five files' relevant functions, verified by: (a) `py_compile` on all five
files, (b) full existing test suites for all five modules passing with zero
regressions, (c) a smoke test confirming `width30_fixture(0, "dev")` and
`width30_fixture(0, "holdout")` produce genuinely different plaintext and
permutation order, and that `dual.run_fixture`/`run_lane_a`/`run_lane_b`/
`lane_a_depth8` all expose `split` with default `"dev"` (no behavior change
for any existing dev-only caller).

**2. Development sweep, fixtures 13-22, fully fresh (positive).** All ten
fixtures run end to end with no fixture-specific branching:

| fixture | top1_exact_order | plaintext accuracy |
|---|---|---|
| 13 | true | 1.0 |
| 14 | true | 0.986 |
| 15 | true | 1.0 |
| 16 | true | 1.0 |
| 17 | true | 1.0 |
| 18 | true | 1.0 |
| 19 | true | 1.0 |
| 20 | true | 1.0 |
| 21 | true | 1.0 |
| 22 | true | 1.0 |

**10/10 exact top-1 recoveries**, clearing the plan's 9/10 gate for this
step.

**3. Holdout sweep, split="holdout", indices 0-11, fully fresh (positive
with one failure).** Same frozen schedule, `schedule_sha256` identical to
the dev runs (split is not part of `SCHEDULE`), pointed at the genuine
holdout corpus pool (24 available passages; indices 0-11 used) for the first
time in this line of work:

| fixture | top1_exact_order | plaintext accuracy |
|---|---|---|
| 0 | true | 1.0 |
| 1 | true | 1.0 |
| 2 | true | 1.0 |
| 3 | **false** | 0.117 |
| 4 | true | 1.0 |
| 5 | true | 1.0 |
| 6 | true | 1.0 |
| 7 | true | 1.0 |
| 8 | true | 1.0 |
| 9 | true | 1.0 |
| 10 | true | 1.0 |
| 11 | true | 1.0 |

**11/12 exact top-1 recoveries**, clearing the plan's 10/12 holdout gate.
`holdout_consumed: true` on all 12.

**4. Fixture 3's failure mode (negative, single case).** Its
`initial_depth7_true_segments` field is `0` -- the true segment did not
survive the very first depth-7 selection stage, before lane A/lane B even
diverge. This is a different failure shape from Phase 486's fixture-19
counterexample (which stayed locally strong through depth 8+ and was rescued
by lineage protection); here the schedule appears to have lost the signal
before either lane's mechanism could act on it at all. No root-cause probing
has been done beyond reading this one field.

**5. Runtime was consistent with Phase 487's estimate.** All 12 holdout
fixtures completed in 4159-5108s (roughly 70-85 minutes) each; total holdout
sweep wall time was approximately 14.5 hours sequential on the one available
GPU. The sweep survived one deliberate immediate kill (fixture 3, killed
mid-run at explicit user request, later recomputed fully fresh) and two
session/process restarts (including a full PC power-off) without losing any
completed-fixture progress, via the resumable `summary.json` pattern.

## Results table

| stage | fixtures tested | exact top-1 | gate | verdict |
|---|---|---|---|---|
| dev sweep (13-22) | 10 | 10 | >=9/10 | PASS |
| holdout sweep (0-11, split="holdout") | 12 | 11 | >=10/12 | PASS |

## Limits

- Entirely synthetic development and holdout work by this project's own
  definition of those terms: no FAED ciphertext was imported at any stage
  (`faed_scored: false` throughout). The holdout sweep did consume real
  holdout-split synthetic fixtures for the first time (`holdout_consumed:
  true`), which is exactly what the plan's gate is designed to spend
  precisely once.
- Not powered or calibrated. No null distribution, no restart-agreement
  check, no shuffled control -- those are reserved for the locked FAED
  experiment this gate unlocks.
- Fixture 3's failure has not been root-caused beyond the single
  `initial_depth7_true_segments: 0` diagnostic field. Whether this reflects
  an inherent limit of the depth-7 stage on some passages, or something
  fixable, is unknown.
- The holdout pool has 24 available fixtures; only the first 12 (indices
  0-11) were drawn for this gate, per the plan's specified sample size. The
  remaining 12 (indices 12-23) have never been touched and remain available
  as a second, still-untouched holdout draw if ever needed.
- This holdout split, once consumed, cannot be reused as a fresh gate again
  per the plan's own methodology (step 5's gate is meant to be spent once
  before a FAED attempt).

## Reproduction

```bash
cd tools/gsmg

# one dev fixture, fully fresh:
python3 phase484an_width30_dual_lane_dev.py --run --fixture-index 13 \
    --work-dir ../../_work/phase484an_sweep/i13 --split dev

# one holdout fixture, fully fresh:
python3 phase484an_width30_dual_lane_dev.py --run --fixture-index 0 \
    --work-dir ../../_work/phase484an_holdout/i0 --split holdout

# regression tests for the split-parameter threading:
python3 -m unittest test_phase484ad_width30_parent_reserved_bridge
python3 -m unittest test_phase484ae_width30_checkpointed_rolling
python3 -m unittest test_phase484ai_width30_early_switch_full_solve
python3 -m unittest test_phase484am_width30_root_lineage_beam
python3 -m unittest test_phase484an_width30_dual_lane_dev
```
