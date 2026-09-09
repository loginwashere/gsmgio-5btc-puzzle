# Phase 484A raw-symbol VIC solver power audit

Date: 2026-09-07

## Outcome

The blind small-width Model-B solver passed its frozen synthetic holdout gate.
All 80 fixtures recovered the planted escape pair and exact column order and
also cleared the frozen plaintext, board, and decoded-length requirements.
The preregistered threshold was at least 8 of 10 passes in every width/pool
cell; every cell passed 10 of 10.

This powers a separately locked real FAED experiment at widths 2, 3, 5, and
6 across all 36 escape pairs. It does not power widths 7 through 40 and is
not itself a result on FAED.

## Locked family

- Historical Model B: checkerboard substitution, then raw-symbol standard
  columnar transposition.
- Raw length: 570 symbols.
- Widths: 2, 3, 5, 6.
- Board pools: `vic_profile` and `broad_random`.
- Ten fixtures per width/pool cell, 80 total.
- Planted pair indices: 0, 1, 5, 9, 14, 18, 23, 27, 32, 35.
- Joint shortlist: first 1,536 valid escape-pair/order hypotheses under the
  substitution-invariant spectral score.
- Board search: two 6,000-proposal anneals per hypothesis, `T 20 -> 1`.

A fixture passed only when pair and order recovery were exact, decoded length
was exact, plaintext character accuracy was at least 0.95, and board accuracy
was at least 0.80. Every cell required at least 8 of 10 passes.

## Results

| Board pool | Width 2 | Width 3 | Width 5 | Width 6 |
|---|---:|---:|---:|---:|
| `vic_profile` | 10/10 | 10/10 | 10/10 | 10/10 |
| `broad_random` | 10/10 | 10/10 | 10/10 | 10/10 |

Across all 80 fixtures:

- exact joint pair/order recovery: 80/80;
- planted hypothesis retained by the 1,536 shortlist: 80/80;
- minimum plaintext character accuracy: 0.9908256880733946;
- minimum board accuracy: 0.84.

The fail-closed verifier reconstructed the exact frozen job set, recomputed
every fixture and cell decision, checked all pinned file hashes, and reported
`consistent: true`.

## Lock history

The first lock draft (`ec419753...`) failed before execution because the
hexadecimal holdout seed had been transcribed to the wrong decimal value.
No holdout fixture or result existed. The corrected lock records this event
in `amendment_history`, pins the actual decimal value 1212825629, and
self-verified before the one holdout execution.

- Corrected execution lock SHA-256:
  `d104efe4d7ed00c7d72d2b136cbeec63009a52ba8702198232c883e8ab91b9a4`
- Holdout result SHA-256:
  `31b2e78c5ebf92cc894b8ad48c44cbf56b718221df9f7179d2d07d16ca87c393`

## Limits

The calibration plaintext comes from the local Cosmic Duality corpus and is
English-like. The powered family is one standard columnar transposition over
one 25-slot checkerboard, at widths no greater than 6. It does not cover
larger widths, disrupted or double transposition, non-columnar permutations,
another plaintext language/model, or a different substitution topology.

The holdout did not score FAED. A real run requires its own frozen input hash,
candidate ranking/output policy, and decision rule. Passing synthetic power
does not guarantee the model is true; it establishes that a negative real
result is not caused by inability to recover this bounded planted family.
