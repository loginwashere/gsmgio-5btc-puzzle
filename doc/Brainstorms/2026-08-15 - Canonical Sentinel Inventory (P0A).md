---
type: hypothesis
status: live
date: 2026-08-15
topics:
  - brainstorm
  - dbbi
  - faed
  - sentinel
  - oracle-coverage
  - p0a
---

# Canonical Sentinel Inventory (P0A)

> [!info] Scope
> Executes P0A from
> [Oracle Pipeline False-Negative Surfaces](<2026-08-15 - Passphrase Oracle False-Negative Surface.md>):
> audit all sixteen fresh DBBI/FAED model scripts for outputs that are
> already fully materialized, deterministic, and free of any unauthored
> choice -- without running any new transform and without calling the
> blob-decrypt oracle. This produces a manifest, not a result. No FINDINGS
> phase is added; nothing here is a new executed test.

## Method

Each of the sixteen `tools/gsmg/dbbi_faed_*_audit.py` scripts was read in
full, and its existing `audit()` function was called (no new code, no new
transform) to inspect exactly what its report object already contains. A
candidate is scored against the Lane B sentinel criteria from the
false-negative-surface report:

1. candidate bytes are fully defined without a second search or output
   inspection;
2. no unauthored index, codebook, alphabet, placement, or gap
   interpretation is needed;
3. material treatments and target/variant scope are fixed in advance;
4. the output is not self-flagged degenerate/tautological by the model's
   own diagnostics; and
5. the output was not chosen by picking the best score among several
   computed options.

## Result table

| # | Model | Materialized output(s) | Disqualifier | Verdict |
|---|---|---|---|---|
| 1 | Six-lane geometry | 24-char B/Y projection mask | Not password material (no B/Y-to-byte mapping exists); per-symbol majority vote with an unexplained B-tie-break | Not eligible |
| 2 | 9x9 transition matrix | none (matrices, MI, correlations only) | No candidate at all | Not eligible |
| 3 | GF(9) complexity | none (scalars only) | No candidate at all | Not eligible |
| 4 | Base-27 three-trit | 32 decoded strings/source (8 symmetries x 2 trit orders x 2 alphabets) | No single canonical pick among the 32; picking one now would be a new interpretation | Not eligible |
| 5 | MTF -> BWT gate | Full MTF-decoded a-i string, both sources, both alphabet orders | Not the modeled candidate -- BWT inversion (the actual hypothesis) still needs an unauthored primary index/terminator. Report's own `candidate_text_generated: False` is inaccurate (the text exists) | Not eligible |
| 6 | Base-81 digraph tokens | Full token sequence (45 DBBI / 285 FAED integers 0-80) computed internally by `tokenize()`, but **not retained** in `audit()`'s report (only a top-10 histogram survives) | Report doesn't expose the sequence; recovering it needs calling `tokenize()` directly. Even then, tokens are raw integers -- no byte serialization was authored | Not eligible as-is |
| 7 | Factoradic/Lehmer records | Permutation tuples for every valid window, sizes 6 and 9 | Many permutations per source, no single one selected; permutations aren't yet password bytes (needs a further mapping) | Not eligible |
| 8 | Crib-solved recurrence | Winning `(alpha, beta)` coefficient pairs only | No full-stream decode was ever assembled from the winning pair | Not eligible |
| 9 | Arithmetic/range coding | **8 concrete a-i strings**: `decoded_text` and `canonical_codeword` for {static histogram, first-order Markov} x {length 91, 570} | None found -- all 4 (model, length) combinations computed unconditionally, no scoring | **Eligible** |
| 10 | rANS feasibility | 5 decode attempts (3 terminal states + 2 fixed lengths) | The only one that "reached" its terminal (terminal=0) is self-flagged `degenerate_universal_sink: True`; the two fixed-length "exact reencodes" are self-flagged `reencode_with_residual_is_tautological: True`; the other two terminals never reached (`undershot_terminal`) | Not eligible -- zero non-degenerate outputs |
| 11 | 81+10 FSM | Full FAED-driven output string (570 symbols) + 10-symbol trailer, single fixed serialization, no alternates searched | Report retains only a 160-char `output_prefix`, not the full string -- needs one line exposing `run_machine()`'s full return value. Same `candidate_text_generated: False` inaccuracy as model 5 | **Conditionally eligible** (report plumbing gap, not an interpretive one) |
| 12 | Sequence alignment | Best-of-480 sliding-window alignment | Explicit `min(...)` selection over computed distances -- chosen after seeing the data, the exact pattern the false-negative report's Lane B excludes | Not eligible |
| 13 | Audio/spectrogram | OCR reads of 6 rendered spectrogram PNGs | Script itself marks `ocr_is_promotion_oracle: False`; no direct symbol-to-byte decode exists | Not eligible |
| 14 | Matrix barcode | `base9_bits()` bit-string (whole forward base-9 integer), used only to build 84 grid images | Never packed into bytes or retained as a standalone candidate; QR-grid variant selection is explicit best-of-N. Possible conceptual overlap with Phase 273's decimal-transport-inverse audit if ever constructed -- check before building | Not eligible |
| 15 | Continued fractions | **12 SHA256 hex digests**: numerator + denominator, 2 sources x 3 digit-maps | None found -- all 6 rows computed unconditionally, digests already taken, never run through the oracle | **Eligible** |
| 16 | Authenticated-string selectors | **20 concrete printable ASCII strings**: 2 sources x 5 targets x 2 index modes | None found -- all 20 computed unconditionally; `leaders` only reorders the report, doesn't gate existence | **Eligible** |

## Eligible candidates, precisely

40 already-computed strings/digests pass all five Lane B criteria and have
never been run through the blob-decrypt oracle (only self-referential
equality checks against their own source data, which is a materially
weaker test):

- **Model 9** -- 8 a-i strings: 4x `decoded_text` (lengths 91, 570, 91, 570)
  and 4x `canonical_codeword` (lengths 81, 516, 62, 392).
- **Model 15** -- 12 SHA256 digests (64 hex chars each): numerator and
  denominator for each of 6 (source, digit-map) rows.
- **Model 16** -- 20 printable ASCII strings (lengths 45 or 91, mixed
  case/digits): 2 sources x {`solved_url`, `prize_address`,
  `native_row_sum_digits`, `native_column_sum_digits`,
  `validation_answer`} x {single-index, paired-base81} modes.

Model 11 (FSM) adds 2 more (full output string + trailer) once its report
is extended to retain the full string rather than a 160-char prefix -- a
one-line change to expose an already-computed value, not a new transform.

## Cross-model notes

- **`candidate_text_generated: False` is unreliable as a signal.** Three
  scripts (models 5, 11, 16) assert this field while their own reports
  simultaneously contain concrete, fully-defined candidate text elsewhere
  in the same object. The field appears to mean "nothing was *promoted* to
  the oracle," not "nothing was generated" -- worth renaming or splitting
  in a future pass so it stops reading as a coverage claim it doesn't
  support.
- **Tautology/degeneracy is a stronger disqualifier than a weak p-value.**
  Model 10's outputs weren't screened out by statistics at all -- they're
  self-flagged as structurally non-informative by the model's own
  diagnostics (`degenerate_universal_sink`,
  `reencode_with_residual_is_tautological`). No sentinel policy should
  promote these regardless of Lane B, since testing them would not actually
  test the rANS hypothesis.
- **No exact duplicates found** among the 40 eligible strings/digests
  (spot-checked; a full pairwise hash comparison should still run as part
  of P1A before any oracle call, per the retrospective-backfill rule's
  deduplication step).
- **Two disjoint gap classes.** Models 2/3/8/12/13 have no candidate
  because assembling one requires a genuinely new step (full-stream
  decode, gap collapse, bit-packing). Models 4/6/7/10/14 *do* compute
  candidate-shaped material internally, but it's either multi-valued with
  no canonical pick, discarded before reaching the report, or
  self-disqualified. These need different remedies -- the first class needs
  a frozen construction rule declared in advance (out of scope for a
  backfill); the second needs either a one-line plumbing fix (model 11) or
  stays excluded (4/6/7/10/14, each for its own stated reason).

## Next step

> [!info] Executed (2026-08-15)
> P1A ran: `tools/gsmg/p1a_sentinel_backfill.py`, FINDINGS.md Phase 290. All
> 40 candidates above, in exactly the two declared forms, against all four
> blobs. **0/80 passphrase attempts hit; 0 weak candidates.** Closed
> negative. Model 11's 2 candidates were not included (report-plumbing fix
> still pending).

This inventory is P0A only -- no candidate here has been run against
`cb_common.py`'s oracle. P1A (bounded statistical-gate sentinel backfill)
is the next queued item if this scope is approved: run the 40 (or 42, with
model 11's fix) candidates above, as literal passphrases and as
`sha256(candidate)` key material, against all four tracked blobs, with
every attempt counted and no adaptive follow-up authorized regardless of
outcome.
