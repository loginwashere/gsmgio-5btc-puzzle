---
type: audit
phase: 469
date: 2026-09-02
status: closed
result: bounded_negative
---

# Phase 469 — DBBI 7×13 Mask-Weighted Sum Audit

## Result

This phase rechecked the exact composition omitted by the earlier separate
audits: overlay the established 31-position mask on the aligned 91-cell DBBI
geometry, then sum selected and complementary cell values by row and column.

The frozen family covered both `7×13` and `13×7` row-major shapes; raw DBBI
under `a=0..i=8` and `a=1..i=9`; aligned plaintext under `a=0..z=25` and
`a=1..z=26`; and the `selected`, `complement`, and whole-stream control
partitions. It also exposed separate `b`/`e` count vectors for the selected
cells. Only direct A1Z26 renderings were allowed—no modular reduction,
padding, route expansion, reversal, cipher, hash, or oracle.

The selected raw cells reproduce exactly 23 `b` plus 8 `e`. Across the
decision-bearing selected/complement family there are zero direct clue-token
hits and zero exact matches to `(23,16,7)`, `(7,13)`, or `(13,7)`. The raw
selected-DBBI totals are 55 under `a=0..i=8` and 86 under `a=1..i=9`; the
aligned selected-plaintext totals are 279 and 310. None supplies a selected
consumer or instruction.

One visually regular descriptive vector appears in the `13×7` selected
`b`-row counts—`(4,2,2,1,2,1,2,1,2,1,2,1,2)`—but it was not a frozen target,
and no direct serialization produces a clue token. It is recorded only as
raw output, not promoted or rescored.

The initial implementation attempt stopped before producing a report because
the historical transcript dependency was absent. Revision 1, frozen before
any output, used Phase 48's already-pinned exact position tuple directly and
verified that it reproduces the established selected plaintext and 23/8
escape counts.

## Disposition

`bounded_negative`. This closes the mask-weighted row/column-sum omission,
not `G-MSL-001`. The remaining untested expansions require an additional
unsupported route or serialization choice.

## Reproduction

```bash
cd tools/gsmg
python3 phase469_dbbi_mask_weighted_sum_audit.py
python3 -m unittest test_phase469_dbbi_mask_weighted_sum_audit
```

