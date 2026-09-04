---
type: preregistration
status: frozen
date: 2026-09-02
phase: 469
topics:
  - DBBI
  - matrixsumlist
  - 7x13
  - selected-31-mask
---

# Phase 469 — DBBI 7×13 Mask-Weighted Sum Protocol

## Question

Earlier audits separately computed (a) row/column sums of all 91 DBBI
symbols and (b) row/column counts of the exact 31-position mask. Did they
omit the direct composition: applying the mask to the aligned 7×13 grid and
summing the selected or complementary cell values?

## Frozen inputs

- The canonical 91-symbol raw `DBBI` stream from `tools/gsmg/data.py`.
- The aligned 91-character plaintext `SOURCE` from
  `tools/gsmg/denis_prime_extraction_audit.py`.
- The exact 31-position tuple `EXPECTED_FLO_POSITIONS_1_INDEXED`, already
  recovered and regression-pinned by
  `tools/gsmg/flo_prime_walk_provenance_audit.py`. The audit uses this
  constant directly because the historical transcript dependency is absent
  from this checkout; it verifies that the tuple selects 23 `b` + 8 `e`
  cells and reproduces the established 31-character plaintext.
- Shapes `7×13` and `13×7`, row-major placement only. These are the two
  labels for DBBI's unique nondegenerate factorization and introduce no
  extra route choice.

## Frozen family

For each shape and each of `selected`, `complement`, and `all`:

1. Sum raw-DBBI cell values by rows and columns under `a=0..i=8` and
   `a=1..i=9`.
2. Sum aligned-plaintext cell values by rows and columns under `a=0..z=25`
   and `a=1..z=26`.
3. For the selected raw-DBBI cells, report row/column counts separately for
   `b` and `e`; Phase 48 already establishes that all 31 selected cells are
   exactly 23 `b` cells plus 8 `e` cells.
4. Serialize a sum list to letters only when every element is already in
   `1..26` (`A1Z26` direct). No modular reduction, truncation, padding,
   reversal, rotation, serpentine route, cipher, hash, password generation,
   or decryption is allowed.
5. Search direct letter renderings only for the frozen clue tokens
   `yin`, `yang`, `matrix`, `sum`, `list`, `seed`, `key`, `enter`, and
   `password`. Also report exact equality with the established numeric lists
   `(23,16,7)`, `(7,13)`, and `(13,7)`.

The `all` partition is a coverage control reproducing the already-tested
whole-stream sums; the decision-bearing delta is `selected` and
`complement` only.

## Decision rule and stop rule

- An exact clue token in a direct (non-modular) rendering or exact equality
  with a frozen numeric list is a lead requiring a separately preregistered
  calibration. It is not promoted here.
- Otherwise this closes only the mask-weighted row/column-sum omission.
- One execution. No output-driven serialization additions.

## Pre-output implementation revision

The first attempted execution stopped before constructing the report because
the provenance module's full `audit()` requires `_work/chat_transcript.txt`,
which is absent from this checkout. No result was produced or inspected. The
input route was revised to import that module's already-frozen exact position
constant directly; the tested family and decision rule are unchanged.

