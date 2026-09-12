# Phase 484AO locked FAED width-30 `{g,i}` dual-lane protocol

Date: 2026-09-12

## Question

Does the Phase 487/488 unified dual-lane schedule -- now cleared on both a
10/10 development gate and an 11/12 genuine holdout gate -- produce readable
plaintext on FAED when the escape pair is `{g,i}`, and is any such result
distinguishable from what the same schedule produces on scrambled input with
no real transposition signal?

## Why this supersedes Phase 484AL

Phase 484AL already ran an exploratory, single-execution FAED `{g,i}`
width-30 attempt on 2026-09-10 and got gibberish (`TIOCSIAASATNEICOKEE...`,
normalized score -4.9287), closed as a documented miss under its own
protocol. That attempt used the Phase 484AI early-switch schedule alone,
before the holdout gate existed. This experiment uses the strictly stronger,
now-holdout-validated Phase 487/488 dual-lane schedule
(`phase484an_width30_dual_lane_dev.py`, `schedule_sha256` pinned below) and
adds two checks 484AL never had: agreement across independent board-anneal
seeds, and separation from a shuffled null.

## Frozen scope

- Input: the repository's 570-symbol `data.FAED`, SHA-256
  `066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`.
- Width: exactly 30 (19 rows, exact grid).
- Escape pair: exactly ordered pair `("g", "i")`.
- Search schedule: the complete `SCHEDULE` dict exported by
  `phase484an_width30_dual_lane_dev.py` (`schedule_sha256` pinned in the
  execution lock) -- identical to the schedule that cleared the Phase 488
  dev (10/10) and holdout (11/12) gates. No tuning of this schedule from any
  FAED output is permitted.
- 5 real-input runs, one per pinned board-anneal seed
  (`board_seed = derive_seed(BOARD_SEED_BASE, 0, i)` for i in 0..4), all on
  the unmodified FAED stream.
- 5 shuffled-control runs, one per pinned control. Each control's raw stream
  is built by segmenting FAED into its 436 `{g,i}`-pair tokens
  (`base.segment_raw`) and permuting the *token order* with a fixed seed
  (`derive_seed(TOKEN_SHUFFLE_BASE, i)`), then concatenating. This preserves
  the raw-symbol histogram and the token histogram exactly (each token's
  internal 1- or 2-character shape is untouched, segmentation of the
  concatenation is therefore always valid, and re-verified at run time) while
  destroying any positional/transposition structure a real order search
  could exploit. Each control uses its own pinned board-anneal seed
  (`derive_seed(BOARD_SEED_BASE, 1, i)` for i in 0..4).
- 10 executions total, no reruns, no other pair/width/schedule eligible.
- The wrapper supplies the real or shuffled stream directly to every search
  stage as a sentinel fixture (`observed`/`raw` set to that stream, `order`
  and `plaintext` are structurally-required placeholders with no truth
  content). Training-fixture requests (`width30.TRAIN_INDICES`, dev split)
  pass through unmodified to the original synthetic provider, exactly as in
  Phase 484AL. `sentinel_diagnostics_are_evidential: false` on every output.

## Decision and limits

**Promotion bar (both required, per the standing plan):**
1. At least one real-input run's top-1 plaintext is independently judged
   readable, coherent English (or unambiguously decodable with minor,
   explainable noise) by inspection -- not merely the best-scoring candidate.
2. The real-input runs' top-1 normalized scores must be clearly separated
   from the shuffled-control runs' top-1 normalized score distribution
   (not just nominally higher point-estimate; a real result inside the
   control spread does not clear this bar).

If either fails, this is a bounded, nonclosing miss: it does not mean `{g,i}`
width 30 is formally unsolvable, only that this schedule found nothing
distinguishable from noise on it. No solver tuning is permitted from FAED
output; any later schedule change must be motivated and evaluated on
synthetic development data only, never on FAED text or scores.

Five real-seed runs additionally let us report whether the real-input result
is stable across independent board-anneal restarts (same top plaintext or
materially different ones) -- agreement strengthens a positive; disagreement
is itself informative and must be reported either way.

## Pre-execution notes

This protocol reuses Phase 484AL's real-input adapter pattern
(`width30.width30_fixture` monkey-patched for the sentinel indices only,
raising on any other unexpected request) to avoid repeating that phase's
first-launch failure, where the adapter also rejected the fixed synthetic
training-fixture requests needed to build the invariant models.
