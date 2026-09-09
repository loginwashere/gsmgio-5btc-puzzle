# Phase 484H discriminator landscape probe

Date: 2026-09-07

Status: development only; no lock, holdout, or FAED

Phase 484G's 20-feature segmentation/transition/lag ablation ranked the planted
order first in all 30 disjoint development fixtures. Before building a search,
test whether the planted order is also a strict one-swap local optimum and
globally unusual among 2,000 random valid orders.

The classifier and feature indices are loaded directly from the Phase 484G
result. All five evaluation fixtures in each width/board-mode cell are used.
No classifier fitting occurs here.

Proceed to a blind search probe only if the planted order is a strict local
optimum in at least four of five fixtures in every cell. Random-order ranks are
descriptive and diagnose global selectivity. FAED is prohibited.

## Development result

Passed. The planted order was a strict one-swap local optimum in 29 of 30
fixtures: five of five in every cell except vic-profile width 19, which scored
four of five. Every cell's median tie-inclusive empirical top fraction was
1/2,001, the minimum measurable under this diagnostic. This licensed the blind
Phase 484I search smoke test.
