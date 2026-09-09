# Phase 484K bidirectional segment-assembly probe

Date: 2026-09-07

Status: development only; no lock, holdout, or FAED

Phase 484J recovered 3/6 blind fixtures but failed whenever the true
column-zero prefix was pruned. In those failures, genuine internal four-column
windows ranked as high as 37, 13, and 89. Test the load-bearing change:
construct from internal segments and extend on either end.

Reuse 484J's depth-specific prefix features and training fixtures. Enumerate
all ordered four-block segments. At each depth, extend every path with every
unused block on both the left and right, deduplicate identical paths, and score
with the matching depth model. Half of the 4,096-path beam is reserved
approximately evenly across ordered endpoint pairs; the remainder is filled
globally by score. At full width, use Phase 484G's cheap full-order
discriminator.

The initial run covers only 484J's three failed development fixtures. Any exact
recovery licenses running all six cells and then a broader development batch.
Zero exact recoveries stops this assembly rule. Truth-segment retention is
diagnostic only and never affects selection. FAED is prohibited.

Amendment K1 after the failed-cell run: bidirectional assembly recovered two
of the three forward-beam failures exactly. Before defining a larger
development power batch, repeat the unchanged bidirectional solver once on
all six width/board-mode cells using fresh development fixture index 23. Run
cells in parallel for compute only; every scientific budget remains unchanged.

Amendment K2 after the fresh replication: widths 10 and 15 recovered both
board pools exactly; width 19 recovered neither. Across indices 22 and 23,
widths 10/15 are 8/8 exact while width 19 is 1/4. Width 19 is therefore
ineligible for promotion under this mechanism. Run a five-fixture development
batch at widths 10 and 15 only, indices 23 through 27, with the unchanged
solver. A cell passes at four of five exact recoveries; every cell must pass
before any holdout protocol may be drafted.

## Development disposition

The five-fixture batch passed every eligible cell: vic-profile width 10 was
5/5, vic-profile width 15 was 4/5, broad-random width 10 was 5/5, and
broad-random width 15 was 5/5. This licenses a separately locked holdout gate
for widths 10 and 15 only. Width 19 remains development-unpowered.
