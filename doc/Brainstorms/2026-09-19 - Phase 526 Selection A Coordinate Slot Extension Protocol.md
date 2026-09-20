# Phase 526A - Selection-A coordinate extension of the frozen slot grammar

Status: frozen oracle-free overlap protocol. No blob may be queried by this
phase. A later execution phase requires a separate lock.

## Question

Phase 525A mechanically reproduced DBBI's conditional 84-token Selection A
and isolated 16 coordinate-derived representations that depend specifically on
that selection. If those 16 values are admitted only as new values of the
existing `matrixsumlist` slot, which fully expanded password materials are
genuinely new relative to material already submitted by this project?

## Frozen source values

The source is `tools/gsmg/phase525_selection_a_result.json`, SHA-256
`82a46dc6c4077ee5626d0578d465ebaf64e141d6627e94848ef34483d02e9253`.
Exactly these 16 labels are eligible:

- `selected_coordinates_row_col_pairs`;
- all three `sum`, `list_compact`, and `list_comma` forms for each of
  `spiral_0`, `spiral_1`, `row_1`, `column_1`, and `row_col_flat_1`.

The URL prefix, color bits, event ranks, and source-byte ordinals are excluded.
They are semantic repeats, restatements of the selector, or tautological under
the one-byte-representative criterion.

## Frozen grammar

Reuse Phase 523 without alteration:

- slot order `yellowblueprimes -> matrixsumlist ->
  lastwordsbeforearchichoice -> yinyang`;
- every non-empty ordered slot subset;
- connected and single-space joins (single-slot forms only once);
- standard `answer_forms() x keystr_forms(newline_variants=True)` expansion.

Enumerate only bases that contain exactly one of the 16 new values in the
`matrixsumlist` slot. All other slot values and provenance strings come from
Phase 523 unchanged. No permutation, reversal, additional separator, base
conversion, coordinate reordering, padding, or case axis is added.

The maximum pre-deduplication base count is:

`16 x (1+15) x (1+19) x (1+10) x 2 - 16 = 112,624`,

where the subtraction removes the duplicate spaced form of the one-slot case.

## Exact expanded-material comparators

Every candidate is expanded first. Its exact material bytes are then compared
against the union of:

1. Phase 523's 18 historical SALPH-scoped coverage sources, reproduced under
   each source's recorded expansion;
2. Phase 524's executed plain base list, SHA-256
   `5193ff5249d5444d20707f21de7cd8a668f6714fb00623a12a63e9e995290bdc`,
   reproduced under the standard newline expansion; and
3. Phase 478's 1,749,878 actually submitted byte strings, manifest SHA-256
   `0952c327a310b8956fd128d6b6c82581bfdc217188a4d4043fbe19779b4c0145`.

Membership uses the same 64-bit BLAKE2b material key as Phase 523. Counts and
the fixed input hashes are recorded. Hash collision risk is negligible for
triage; before any execution lock, every retained material must additionally be
rechecked by exact bytes or by deterministic regeneration from its retained
base.

## Output

Write under `_work/phase526/`:

- a plain one-base-per-line list containing only bases that schedule at least
  one material absent from all three comparators and from earlier retained
  bases;
- a JSON report with input hashes, source values, counts, and output digest.

The base list is an efficient covering set, not a claim that every form emitted
by every retained base is new. The execution tool will inevitably repeat some
covered forms; the report records both emitted forms and unique fresh material
keys.

## Stop rule

- Zero new material: close the coordinate-password lane without touching a
  blob.
- Nonzero new material: stop after writing and verifying the list. Prepare a
  separate Phase 526B execution protocol and lock, with SALPH as the primary
  consumer because `matrixsumlist` is a macro slot on that transition.
- A negative future execution does not license new coordinate encodings.

## Limits

Selection A and its one-byte-representative criterion remain conditional. This
protocol tests the already-frozen house-style password grammar; it does not
show that coordinates are what `matrixsumlist` requests, and it does not study
the 61 non-prime DBBI symbols.
