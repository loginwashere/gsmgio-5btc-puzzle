# BTCSEED tail: options for decoding it (brainstorm)

Date: 2026-09-21. Status: ideation only. Nothing here is a result, nothing is promoted, and the
validation design of each option is deferred to its own pre-registration. Two informal
looks at the data (below) were not pre-registered and are not findings.

## What is closed already (do not re-derive)

Phases 386-408 (P91/Z/Q472 typed consumers, control/data machines, BIP39/BIP32, 256-bit
windows, Vigenere over Q472), 419 (validation-answer keyword), 425 (BTCSEED family-wise
p = 1/10001, checkpoint only), 426-428 (tail structure is Bifid digraph mechanics),
429-433 and 441 (all 14! and 16! relabelings, quadgram selection pathology), 476 (P91 second
square), 146 (short-period Bifid/Trifid fractionation), 540-541 (fresh-context agents).
The 100-item idea bank of the 2026-08-25 BTCSEED/P91/Z brainstorm is mostly run.

## Structural facts that shape the options

1. **The decode is a pairwise overlay of the two 285-symbol halves of FAED.** Output letters
   2k and 2k+1 depend only on FAED[k] and FAED[285+k]. The even letter is the cell
   (row of FAED[k], row of FAED[285+k]); the odd letter is (col, col). `BTCSEED` touches only
   symbols 0-3 (`faed`) and 285-288 (`aied`).
2. **The even output rail can only be B, C, D or E.** All nine FAED symbols sit in the first
   two rows of the DBBI-keyed square. Any word at an even offset must have B/C/D/E at its
   alternating positions (BTCSEED does; so would DECODED).
3. **FAED is close to a fair 9-symbol stream.** Order-0 entropy 3.12 of 3.17 bits; the row bit
   is a fair coin (288/282); the two halves are independent (30 agreements vs 33.0 expected,
   chi2 57 on 64 df, shuffle p about 0.74). Informal look, not pre-registered.
4. **A genuine Bifid ciphertext of ordinary text would use about 20+ symbols**, not 9 (rough
   estimate, unverified: English coordinate pairs carry at least about 3.9 bits). So the tail is
   mechanical unless a selector we do not know applies.
5. **Loose lead, not a finding.** Block composition of FAED in 19 blocks of 30: p about 0.003
   unadjusted, about 0.013 after four layouts glanced at. 6x91+24 gave 0.08.

## Options

### A. Sharper instruments

1. **Rail-feasible lexicon scan** (shortlisted; pre-registered as Phase 544). Only words with
   B/C/D/E at alternating positions can appear in the tail. Score dictionary occurrences by
   surprisal under the exact mechanical rail model and calibrate against exact-multiset FAED
   shuffles. The Phase 386 word scan was not rail-aware and used a different null.
2. **Selectivity curve for the prefix** (shortlisted as the gate). Sample random placements of
   a..i in the 5x5 and random alphabets; count how often the prefix is any 7-letter dictionary
   word. Puts BTCSEED's 1e-4 (12 squares) against the whole square space.
3. **Pre-declared block scan of FAED.** Fix the layout family first; test composition
   drift between blocks. Different blocks could mean different keys.

### B. Self-reference and cascade

4. **Keyword fixed point** (shortlisted). Phi(keyword) = Bifid decode of FAED with the square
   keyed by that keyword. Iterate DBBI -> BTCSEED -> Phi(BTCSEED) ... Free parameter: the
   keyword-length rule only.
5. **Tail-derived square** (shortlisted with 4). Deduplicate the decode in order of first
   appearance (B T C S E D O M K A H ...) as DBBI was; apply that square to FAED, DBBI,
   VALIDATION_ANSWER and the other authenticated ciphertext objects.

### C. Native-alphabet analogues

6. **Whole-block Bifid on the project's own 3x3 square** (shortlisted). All 9! arrangements,
   scored with the existing checkerboard fit at the best escape pair {g,i}. Phase 146 only
   tried periods 2-15.
7. **Native bit and quit channels.** Under the DBBI square FAED is a 570-bit row stream plus a
   570-digit base-5 column stream. Read each in native order (30x19 bitmap, base-5 numeral,
   adjacent-pair Polybius). Earlier phases used Bifid order after the Z only.

### D. Method transfer from decipherment

8. **Layout-transposition search with a language-free score** (Zodiac-340 style): 570 = 30x19 =
   15x38 ..., routes scored by conditional-entropy drop, calibrated by shuffles.
9. **Hard-crib solver**: BTCSEED as a fixed constraint over placements of the nine symbols.
   Entropy argument (fact 4) says an English optimum cannot exist; only meaningful with a
   non-English target model.
10. **Change-point / hidden Markov segmentation of the tail** (Z at 97, 98/472, the 285 midpoint).

### Pruned

- Alternative pairings or offsets of the two halves: they are independent (fact 3), so any
  recombination only relabels independent draws.
- Round-2 style operation proposals on the tail: covered by Phase 541.

## Overlap to check before each pre-registration

6 and 7 against Phase 146 and the dual-ternary/dual-quinary sweeps; 8 against Phase 477A;
4-5 against Phase 476 and idea-bank items 99-100; 3 against the existing FAED 6x91+24 notes.

## Order and disposition

Option 1 first (cheapest, sharpest, new instrument). Then 4 and 5 as one pre-registration,
then 6. Option 2 is the gate that decides whether the branch deserves further effort.
Each pre-registration needs a frozen universe, a planted control, an exact bar and a stop
rule, and a one-round scope.
