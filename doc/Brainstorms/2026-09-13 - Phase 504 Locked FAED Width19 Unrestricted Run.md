# Phase 504 locked FAED width-19 unrestricted run

Date: 2026-09-13
Status: frozen real-run design; execution lock issued separately

## Authorization

The repaired unrestricted solver recovered two pre-outcome-selected valid
holdout fixtures (Phase 502 fixture 3 and Phase 503 fixture 5) at exact final
rank 1 with 100% plaintext accuracy.  Phase 504 applies precisely that solver
once to FAED.

## Frozen cell

- observed bytes: the repository's exact FAED string, SHA-256 pinned;
- Model B raw-digit columnar direction;
- width 19, 30 rows, exact 570-symbol grid;
- escape pair `{g,i}`;
- unrestricted 25-slot checkerboard;
- original invariant front through depth 5;
- unrestricted original budgets through refined depth 7 and depths 8--10;
- depth-11 parent-reserved bridge only: `8 x 20,000`;
- depths 12--19: `3 x 10,000`;
- existing final top-8 unrestricted board resolution.

Training models are materialized from the closed synthetic training corpus
before the real-fixture adapter is installed.  Synthetic sentinel truth fields
are never used for selection and are removed from each authoritative real
checkpoint.  All stages are atomically checkpointed and resumable.

## Decision

Inspect every valid final candidate, not only rank 1.  A readable, coherent
plaintext is a solve candidate requiring independent structural confirmation.
Gibberish is a bounded miss for this one pair, width, direction, schedule, and
seed.  It does not reject other pairs, widths, directions, plaintext models,
or transposition families.  No parameter is changed after locking and there
is exactly one run.
