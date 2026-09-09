# Phase 484J constructive prefix-beam probe

Date: 2026-09-07

Status: development only; no lock, holdout, or FAED

Phase 484I established that the cheap discriminator assigns the planted order
a better score than all blind-search endpoints, but whole-permutation moves do
not reach its narrow basin. Replace whole-order motion with constructive search.

For each exact width 10, 15, and 19, split the observed stream into equal
column blocks. A candidate path is a left-to-right sequence of block indices.
Train deterministic depth-specific centroid discriminators on genuine
contiguous runs versus random runs, using development fixtures 6 through 15
from both board pools. Features are derived independently within each row so
an unfinished prefix does not invent transitions between rows.

Enumerate every ordered four-block path, retain the best 4,096, and extend the
beam one unused block at a time. At full width, rerank with Phase 484G's fixed
full-order cheap discriminator. Search one fresh development fixture (index
22) per width/board-mode cell.

This is a smoke test. Any exact recovery licenses a broader development power
study. Zero exact recoveries stops this construction. No truth information
enters the beam score or pruning; truth-prefix retention is diagnostic only.
FAED is prohibited.

Amendment J1 after the initial result: the 4,096-path run recovered 3/6 cells.
The failed broad-random truths ranked 8,803 and 13,491 at depth four; the
failed vic-profile width-15 truth began at rank 2,142 but was pruned at depth
five. A bounded rescue therefore retains 16,384 paths only through depth six,
then returns to 4,096, and reruns only those three failed cells. This budget is
driven by recorded prefix ranks, not by FAED.

## Development result

The initial 4,096-path beam recovered three of six fixtures exactly:
vic-profile width 10, broad-random width 10, and vic-profile width 19. The
successful width-19 truth remained in the beam at every depth and ranked first
after terminal reranking. The failed truths were pruned at depth four or five.

The bounded adaptive rescue recovered zero of the three failures. It delayed
the broad-random width-15 loss from depth four to depth six and the
broad-random width-19 loss from depth four to depth five, while vic-profile
width 15 was still lost at depth five. This shows genuine constructive signal
but fails the smoke test as a general solver. Stop beam widening: further work
must change the assembly rule, such as bidirectional/meet-in-the-middle segment
construction, rather than increase this forward beam.

A post-result diagnostic supports that specific next step. In the three failed
fixtures, the left-edge four-column prefix ranked 2,142, 8,803, and 13,491,
while the best genuine internal four-column window ranked 37, 13, and 89.
Respectively 8/12, 11/12, and 5/16 genuine internal windows survived the
original 4,096 cutoff. The signal therefore identifies real internal segments;
the failure comes from forcing every construction to begin at column zero.
