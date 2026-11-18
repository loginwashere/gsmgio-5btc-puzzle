# Phase 550 — board-profiled frequency test of FAED

Status at creation: protocol, 2026-09-29. Follow-up to Phase 549 (the generator fingerprint, locked
under the working filenames `phase548_generator_fingerprint.*` because of a numbering collision with
the parallel Phase 548). Everything below is frozen by the execution lock at the end.

## Question

Phase 549 rejected seven declared generator models for FAED, mainly because FAED lacks the
sequential memory that a straddling checkerboard leaves behind. A transposition of the digit stream
(as in the real VIC cipher) destroys that memory but cannot change symbol counts. So the open question is:

> Can the **symbol-count profile** of FAED be produced by a nine-symbol straddling checkerboard
> over English letters-only plaintext, for **any** board reachable by the declared search, followed
> by any transposition?

The board is a nuisance parameter. The test statistic is profiled over boards, so compatibility
with any admitted board prevents rejection.

## Model

- Board: 7 single-symbol cells, and 2 escape symbols each with 9 follower cells, giving 25 cells.
  25 letters (`J -> I`), one per cell. A letter in a single cell emits its symbol. A letter in escape
  row `e`, column `c`, emits `e` then `c`.
- Plaintext: letters-only, uppercase (the solved-chain habit). No digits, spaces or punctuation.
- Symbol counts are invariant to any transposition of the output and to relabeling the symbols.
  The comparison is therefore between **sorted** count vectors.
- For a board `B` and corpus letter frequencies `q`, the expected symbol proportions are
  `pi_B = A_B q / sum(A_B q)`, where `A_B` is the 9 x 25 emission incidence matrix.
- Out of scope: chain addition (Phase 549's CB-ENG-CHAIN), fractionation, boards with more or fewer
  than 25 cells, non-letter plaintext symbols, and any cipher layer before the checkerboard
  (a letter substitution before the board is absorbed by the board itself).

## Corpora (frozen)

All are uppercased, letters only, `J -> I`.

- **K1 book:** `wordlists/gsmg/cosmic_duality_book_full_text.txt`, `#` lines dropped.
- **K2 screenplay:** `wordlists/gsmg/matrix_script_windows.txt`, rebuilt into running text from
  the one-word-sliding windows, with exact duplicate segments removed.
- **K3 puzzle:** the creator's own solved English. That is the Phase 3.2 plaintext's English lines
  (decrypted from `PHASE32_BLOB_B64`), the Phase 3.2.1 Architect answer (German EBCDIC then
  Beaufort `THEMATRIXHASYOU`, reproduced here) and `VALIDATION_ANSWER`.

## Statistic

`T = min over boards B of X2(sort(O), sort(N * pi_B))`, where `O` is the observed count vector,
`N` its length, and `X2` the Pearson sum `(O - E)^2 / E`.

Search: simulated annealing over letter-to-cell permutations (swap moves, 6 restarts of 4,000
steps, geometric cooling), then 2-swap hill climbing to a local optimum. This is **not exhaustive**.
The conclusion is limited to boards the search reaches, and Control 1 checks it.

## Calibration and decision

For each corpus `k`:

- Board set `B0`: one VIC board (the corpus's 7 most frequent letters in single cells, the rest in
  frequency order), five random boards (seed 550), and, at run time only, `B_hat`, the best board
  found for FAED.
- For each `B0`, simulate `S = 200` streams of length 570 by encoding a random corpus window with
  `B0`, then compute `T_sim` with the same search.
- `p_k(B0) = (1 + #{T_sim >= T_obs}) / (1 + S)` and `p_k = max over B0`. This is conservative for
  rejection.
- Holm correction over K1-K3. Corpus `k` is **excluded** if its Holm-adjusted `p <= 0.01`, otherwise
  **compatible**.
- A rejection means: no board reached by the search, with that corpus's letter distribution, fits
  FAED's count profile. It does not exclude other plaintexts, languages, or chain-added or
  fractionated variants.
- A compatible result keeps transposed checkerboard encoding possible for that corpus. It does not
  identify VIC or promote any key.

DBBI (length 91) is reported with `T_obs` and `p` at `B_hat` and at the VIC board. It is not gated.

## Controls (before the lock; none uses FAED or DBBI)

1. **Search adequacy:** for each corpus, 100 planted streams (half VIC, half random boards). The
   search objective must be `<=` the objective at the true board in at least 99 of 100 cases.
2. **Size:** for each corpus, 200 planted streams from fresh random boards, scored against the
   pooled `T_sim` of the control board set (VIC plus five random). The rejection rate at `p <= 0.01`
   must be `<= 0.04`.
3. **Power, at the Holm first-step threshold `0.01 / 3`:** for each corpus, 100 streams from each
   alternative, scored against the pooled null. The alternatives are uniform nine-symbol IID;
   IID with one doubled symbol (0.2, then 0.1 x 8, "decimal with a merged digit"); and a
   checkerboard over uniform random hex. Reported, not gated.

Controls 1 and 2 must pass, or no lock is written.

## Disclosures

- Phase 549's z-scores are known. FAED's frequency profile was compatible with the VIC-board model
  (z from -1.36 to +1.64) and not with random-board models. This test was designed knowing that.
  Its purpose is to replace "untested" with a bounded answer, not to reach a predicted result.
- The "decimal with a merged digit" profile was a post-hoc observation on Phase 549. It appears
  here only as a power alternative, not as a hypothesis under test.
- The constants pre-screen from the same session was an unsaved inline check. It is not coverage.

## Stop rule

One run. Do not add corpora, board geometries, search settings, statistics or thresholds after
seeing the result.

## Execution lock

`--prepare` runs the controls and writes `tools/gsmg/phase550_board_profile_lock.json`, pinning this
protocol, the script, the test, `data.py`, the corpus files, seeds, `S`, search settings, thresholds
and control results. `--run` verifies the lock and computes everything once.

## Reproduction

```bash
python3 tools/gsmg/phase550_board_profiled_frequency.py --self-test
python3 tools/gsmg/phase550_board_profiled_frequency.py --prepare
python3 tools/gsmg/phase550_board_profiled_frequency.py --run
```
