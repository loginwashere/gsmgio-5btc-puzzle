# Phase 484D powered width-7 raw-symbol VIC real protocol

Date: 2026-09-07

Status: freeze before execution; FAED not yet scored by this phase

## Scope

Test real FAED at ragged width 7 under the historical Model-B construction
powered by Phase 484C. Search all 36 unordered escape pairs and all 5,040
column orders per pair, rank all valid hypotheses by the frozen spectral
statistic, retain 1,536, and apply two 6,000-proposal board anneals (`T 20 ->
1`) to each. Rank by normalized quadgram score and retain the best ten.

The successful Phase-484C holdout winners had scores from
`-4.507065492983351` to `-4.152474344553966`. A real maximum at or above the
lower value triggers readability review and a separate confirmation; it is
not automatic promotion. Phase 484C also produced a false-order holdout
winner at `-4.282063`, proving that score alone cannot identify a solution.

If no coherent plaintext appears, record
`no_powered_width7_solve_no_calibrated_null_claim` and do not retune or rerun.
No shuffled family-wide null is included, so this phase cannot claim a
multiplicity-calibrated statistical negative.

The lock pins the exact 570 FAED bytes, this protocol, runner, verifier,
Phase-484C solver/lock/holdout, the byte-locked base solver, data source,
corpus, and quadgram table. Widths other than 7 are outside this phase.
