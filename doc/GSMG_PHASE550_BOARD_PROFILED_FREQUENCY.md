---
type: audit
phase: 550
date: 2026-09-29
status: complete
result: compatible-low-power
disposition: bounded-uninformative
script: tools/gsmg/phase550_board_profiled_frequency.py
topics:
  - faed
  - checkerboard
  - transposition
---

# Phase 550 — board-profiled frequency test of FAED

2026-09-29. Result: **compatible for all three corpora (Holm 1.0). The test has little power
against skewed alternatives.** Symbol frequencies alone cannot separate a transposed checkerboard
over English from other skewed nine-symbol sources.
Protocol: [Phase 550 protocol](Brainstorms/2026-09-29%20-%20Phase%20550%20Board-Profiled%20Frequency%20Test%20Protocol.md),
locked before any FAED or DBBI statistic was computed (lock verified at run time).

## Question

Phase 549 left transposed checkerboards open. Transposition preserves symbol counts and removes the
adjacency its rejections relied on. So: can FAED's sorted symbol-count profile be produced by a
nine-symbol straddling checkerboard (7 single cells + 2 escape rows of 9) over letters-only
English, for any board the search reaches? The board is profiled out:
`T = min_B X2(sort(O), sort(N * pi_B))`.

## Method

- Corpora: K1, the *Cosmic Duality* book (69,832 letters); K2, the Matrix screenplays rebuilt from
  the sliding windows and deduplicated (894,232); K3, the creator's own solved English (Phase 3.2
  prose, the Phase 3.2.1 Architect answer, `VALIDATION_ANSWER`; 2,085).
- Search: simulated annealing over letter-to-cell permutations (6 restarts x 4,000 steps), then
  2-swap polish. Not exhaustive.
- Calibration: 200 simulations each at a VIC board, five random boards and the fitted board;
  `p = max over boards`. Holm over the three corpora, bar 0.01.

## Controls (before the lock)

| Corpus | Search not worse than truth | Size at p <= 0.01 | Power at 0.01/3: uniform / merged decimal / hex board |
|---|---:|---:|---|
| K1 book | 100/100 | 0.010 | 1.00 / 0.06 / 0.19 |
| K2 screenplay | 100/100 | 0.000 | 0.85 / 0.00 / 0.02 |
| K3 puzzle | 100/100 | 0.025 | 1.00 / 0.18 / 0.25 |

## Result

| Corpus | T_obs | p (max over boards) | Holm | Verdict |
|---|---:|---:|---:|---|
| K1 book | 0.0114 | 0.567 | 1.0 | compatible |
| K2 screenplay | 0.0086 | 0.940 | 1.0 | compatible |
| K3 puzzle | 0.0129 | 0.592 | 1.0 | compatible |

FAED's sorted counts are `107, 75, 69, 58, 57, 54, 52, 49, 49`. The fitted book board predicts
`106.8, 75.1, 69.0, 57.7, 57.0, 53.7, 52.4, 49.4, 48.8`. Near-perfect fits like this are typical:
the median simulated `T` is about 0.01 for every corpus. The fitted boards (for example, book:
single `NTORAEI`, rows `SFPWUQVXZ` / `MHCDBGLYK`) are artifacts of the fit, not key candidates.

DBBI (reported only): K1 p 0.97, K2 p 0.97, K3 p 0.37.

## What this supports, and what it does not

- The 25-cell board family fits almost any skewed nine-symbol count profile. Only near-uniform
  profiles resist. A count-only test therefore cannot exclude a transposed checkerboard over
  English, and it cannot tell one from a "merged decimal" or hex-content source.
- "Compatible" is not support. The measured power against the skewed alternatives is 0-25%.
- Combined with Phase 549, a transposed checkerboard over English stays **open**. It is not
  promoted, and neither VIC nor any board is identified. Distinguishing it from other sources needs
  statistics that survive transposition and are not counts. Under a general transposition none are
  available from a single 570-symbol stream, unless the transposition class is restricted (for
  example, keyed columnar of bounded width, Phase 477A).
- Out of scope, and not excluded: chain addition, fractionation, other board geometries, non-letter
  plaintext symbols.

## Scope and stop

One run. Do not add corpora, geometries, search settings or statistics after seeing this.

## Reproduction

```bash
python3 tools/gsmg/phase550_board_profiled_frequency.py --self-test
python3 tools/gsmg/phase550_board_profiled_frequency.py --run   # verifies the lock first
```
