# Phase 484I blind discriminator search probe

Date: 2026-09-07

Status: development only; no lock, holdout, or FAED

Phase 484H passed its gate: the planted order was a strict one-swap local
optimum in 29 of 30 evaluation fixtures, at least four of five in every cell,
and globally rare under random-order sampling. Test whether multi-start
annealing on that fixed cheap discriminator can recover planted orders from
blind starts.

Use one fresh development fixture (index 21) in each width/board-mode cell.
Starts comprise the top four valid orders from a 256-order blind population
and four additional random valid orders. No controlled or truth-derived start
is allowed. Anneal with the same four permutation moves used in Phase 484F,
then perform deterministic best-swap refinement.

This is a smoke test, not a power gate. Any exact recovery licenses a broader
development batch; zero exact recoveries stops this search implementation
without spending holdout fixtures. FAED is prohibited.

## Development result

Failed: zero of six cells recovered the planted order. Best endpoint Kendall
tau ranged from 0.105 to 0.467. This was not classifier reward hacking: in all
six cells the planted objective score remained above the best search endpoint,
by 0.296 to 2.416 points. The discriminator supplies a selective target with a
narrow correct basin, but whole-permutation simulated annealing cannot reach
that basin from blind starts under this budget. Stop this search implementation;
do not expand it to holdout or FAED.
