---
type: audit
phase: 549
date: 2026-09-29
status: complete
result: seven-declared-generators-rejected
disposition: bounded-negative
script: tools/gsmg/phase548_generator_fingerprint.py
topics:
  - faed
  - dbbi
  - checkerboard
  - generator-model
---

# Phase 549 — generator fingerprint of FAED and DBBI

2026-09-29. Result: **FAED rejects all seven declared generator models** (Holm-adjusted p = 0.0035
each, bar 0.01). Only the reference fitted to FAED's own symbol counts is compatible (p = 0.43).
Protocol: [generator fingerprint protocol](Brainstorms/2026-09-29%20-%20Phase%20548%20Generator%20Fingerprint%20Protocol.md),
locked before any real-stream comparison (lock verified at run time).

**Numbering note.** This study was locked under the working name "Phase 548"
(`phase548_generator_fingerprint.py`, `phase548_fingerprint_lock.json`,
`phase548_fingerprint_result.json`, `test_phase548_generator_fingerprint.py`, and the protocol file
name). A parallel session filed the FAED distribution-boundary pilot as Phase 548. To keep the lock
hashes valid, the locked files keep their names, and this study is Phase 549.

## Question

Which concrete producers of a nine-symbol stream can generate FAED's label-invariant statistics?
The statistics are sorted symbol proportions, repeat rate, consecutive-symbol mutual information,
maximum follow chi-square, halves chi-square, and period-2 and period-3 chi-squares. The comparison
is a Mahalanobis omnibus, calibrated by 2,000 simulations per generator. No decode, key search or
oracle.

## Generators

All checkerboards are 9-column: 7 single cells plus 2 escape rows. The English source is the
*Cosmic Duality* book.

| ID | Model |
|---|---|
| CB-ENG | checkerboard, uniformly random board, English |
| CB-ENG-VIC | checkerboard, 7 most frequent letters in single cells, English |
| CB-HEX | checkerboard, random board, uniform random hex |
| CB-RAND | checkerboard, random board, uniform random letters |
| CB-ENG-CHAIN | CB-ENG, then VIC chain addition mod 9 |
| B9-ENG | letters-only English bytes, 3 base-9 digits per byte |
| B9-BYTES | random bytes, 3 base-9 digits per byte |
| UNIF / IID-FIT | references: uniform IID; IID fitted to the stream's own counts |

## Controls (before the lock)

- Statistics are invariant to relabeling the symbols (100 checks).
- Size at raw p <= 0.01, from 200 planted streams per generator: 0.000-0.020, all within the 0.04 bar.
- Power matrix: 200 planted streams per cell, measured at **raw p <= 0.01, not at the
  Holm-corrected threshold** used for the decision. A memoryless stream with FAED's counts was
  rejected by CB-ENG in 100% of controls, by CB-HEX in 100%, and by **CB-ENG-VIC in only 71%**.
  CB-ENG and CB-HEX barely separate from each other (1-4% cross-rejection). CB-ENG-CHAIN and UNIF
  do not separate (1%).

## Result

| Generator | FAED p | Holm | Verdict | DBBI p (reported) |
|---|---:|---:|---|---:|
| CB-ENG | 0.0005 | 0.0035 | rejected | 0.343 |
| CB-ENG-VIC | 0.0020 | 0.0035 | rejected | 0.188 |
| CB-HEX | 0.0010 | 0.0035 | rejected | 0.421 |
| CB-RAND | 0.0005 | 0.0035 | rejected | 0.105 |
| CB-ENG-CHAIN | 0.0005 | 0.0035 | rejected | 0.001 |
| B9-ENG | 0.0005 | 0.0035 | rejected | 0.0005 |
| B9-BYTES | 0.0005 | 0.0035 | rejected | 0.0085 |
| UNIF (reference) | 0.0005 | — | — | 0.003 |
| IID-FIT (reference) | 0.434 | — | — | 0.752 |

Largest per-statistic deviations for FAED (z against each generator's simulations):

- **Checkerboards:** mutual information too low (CB-ENG -3.5, CB-ENG-VIC -3.9, CB-HEX -3.2).
  CB-ENG and CB-HEX also have too flat a frequency tail (sorted p7 +3.7 / +3.3) and too weak a top
  symbol (-2.8 / -3.1). **CB-ENG-VIC's sorted-frequency z-scores stay between -1.36 and +1.64.** Its
  rejection rests on memory, not on frequencies.
- **CB-ENG-CHAIN:** the top symbol is too strong (+7.5).
- **B9-BYTES:** period-3 structure absent (-10.8).

## What this supports, and what it does not

- FAED rejects **these seven declared generator models**, each with the stated board population,
  corpus and statistics. It does not exclude every board, every plaintext, every keyword or every
  English source. The random-board models are distributions over constructions, not the union of
  them.
- **Transposition gap (open).** Transposing the digit stream after the checkerboard, as the real VIC
  cipher does, preserves symbol counts and destroys adjacency and periodicity. The checkerboard
  rejections rest mainly on adjacency, so a transposed checkerboard over English is **not** excluded.
  For the VIC-style board, the frequency profile alone is compatible with FAED. Phase 550 tests
  the count profile with the board profiled out.
- Non-rejection identifies nothing. The IID-FIT reference being compatible does not establish that
  FAED is key or number material. DBBI's non-rejection under checkerboard models does not establish
  text, especially given its prime scaffold (Phase 534).
- A same-session inline check found no exact digit-to-symbol match of FAED or DBBI against seven
  mathematical constants. It had no saved script and is **not** recorded as coverage.

## Scope and stop

One run; the generator set, statistics and thresholds are frozen by the lock. Do not add generators
to this run.

## Reproduction

```bash
python3 tools/gsmg/phase548_generator_fingerprint.py --self-test
python3 tools/gsmg/phase548_generator_fingerprint.py --run   # verifies the lock first
```
