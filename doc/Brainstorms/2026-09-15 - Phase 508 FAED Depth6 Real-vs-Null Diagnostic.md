# Phase 508 — FAED depth-6 real-versus-null diagnostic

Date: 2026-09-15
Status: protocol frozen before null execution

## Question

Does the already-observed Phase-506A real FAED family maximum look unusual
under exact raw-symbol-multiset shuffles when every shuffled trial receives the
same complete 36-pair depth-6 search budget?

This tests the Phase-506A proxy, not Model B. A failure means only that this
shallow English/unrestricted-board statistic cannot distinguish FAED from its
positional null. It does not retire deeper searches, other objectives, widths,
directions, boards, or cipher models. Because the real score was observed
before this protocol, even a successful separation is diagnostic rather than
pristine confirmatory evidence.

## Frozen method

- Real statistic: Phase-506A's family maximum, including all 36 pairs.
- Null: Fisher-Yates shuffle of FAED's exact 570-symbol list using the project's
  PCG32 and `derive_seed(0x508A11, trial_index)` for trials 0 through 199.
- Each trial: unchanged Phase-505E pair-balanced model, depth-6 schedule,
  unrestricted-board CUDA objective, all 36 pairs, and the maximum pair score.
- Ties count as exceedances.
- Each pair cell and completed null trial is written atomically and can resume.

## Sequential futility rule

Stop immediately after the first null family maximum greater than or equal to
the real maximum. With the frozen 200-trial budget, one exceedance gives a best
possible final add-one p-value of `2/201 = 0.00995`, which cannot meet the
project's `p < 0.005` bar. If no exceedance occurs, complete all 200 trials and
report `1/201 = 0.004975` descriptively, subject to the post-observation caveat.

No FAED decode, candidate mutation, AES query, width change, or deeper search is
performed in this phase.
