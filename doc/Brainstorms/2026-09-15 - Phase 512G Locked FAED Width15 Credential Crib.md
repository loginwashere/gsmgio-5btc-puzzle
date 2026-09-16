# Phase 512G — locked FAED width-15 credential crib

Date: 2026-09-15

Status: protocol frozen before any Phase-512 crib search touches FAED.

## Question

Under historical Model B's untranspose geometry at exact width 15, can the
observed 570-symbol FAED stream be restored so that a legal 25-slot
checkerboard decodes one contiguous region to the complete, independently
authenticated Phase-1 credential?

The exact uppercase crib is:

`THEFLOWERBLOSSOMSTHROUGHWHATSEEMSTOBEACONCRETESURFACE`

It has 53 letters and uses only the 25-letter checkerboard alphabet. No clause,
substring, spelling, case, separator, reversal, or mutation variants are
eligible.

## Frozen search family

- Input: the exact 570 ASCII characters in `data.FAED`, hash-pinned in the
  execution lock.
- Geometry: width 15, exact 38-row rectangle, `Geometry.decrypt` untranspose
  direction only.
- Escape pairs: all 36 unordered pairs from the nine symbols `a` through `i`.
- Raw starts: every integer 0 through 517 inclusive.
- Board structure: seven single codes and eighteen double codes. For the 16
  distinct crib letters, enumerate all 26,333 legal assignments of letters to
  the single/double classes; unused board slots need only admit a legal
  completion.
- Search: Phase-512D MRV/forward-checking CSP, start-major and pair-parallel.
- Per-pair/start node ceiling: 2,000,000. Any incomplete cell makes the result
  non-interpretable rather than negative.
- Workers: 16. Pattern sharding: 1.
- Checkpointing: after every fully completed raw start. A resume must match all
  identity fields before continuing.

The family contains 518 × 36 = 18,648 pair/start cells. The length-pattern
enumeration is internal to every cell.

## Calibration basis

Before lock:

- the complete blind width-15 synthetic positive recovered the exact planted
  start, `{g,i}` pair, column order, and length pattern with no earlier false
  hit;
- a complete crib-absent width-15 control exhausted all 18,648 pair/start
  cells with zero hits and zero incomplete cells;
- serial/parallel parity and checkpoint fail-closed tests passed.

Widths 19 and 30 also recovered synthetic positives, but are outside this
experiment. Width 38 was stopped for prohibitive development cost and is not
eligible. No synthetic result establishes that this crib is actually present
in FAED.

## Acceptance and stop rule

Any exact CSP hit is retained for manual and mechanical verification. A hit
must reconstruct a valid column permutation and a partial injective board whose
decoded window is exactly the complete crib. All hits at the earliest matching
raw start are retained; operating-system worker completion order cannot choose
the answer.

If all 18,648 cells complete with zero hits, the verdict is a bounded negative
for this exact crib, width, and direction only. It does not reject Model B,
other cribs, widths, directions, route systems, or non-checkerboard models.

No scoring threshold, English model, near-match, or post-run expansion exists.
