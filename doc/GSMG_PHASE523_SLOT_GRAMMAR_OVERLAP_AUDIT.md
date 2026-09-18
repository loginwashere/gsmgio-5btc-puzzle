---
type: audit
phase: 523
date: 2026-09-18
status: complete
result: pre-registration
disposition: structural-only
script: tools/gsmg/phase523_slot_grammar_overlap_audit.py
topics:
  - salph
  - closed-system
  - password-grammar
  - overlap-audit
---

# GSMG Phase 523 — Slot-Grammar Password Product for SALPH: Overlap Audit

## Question

The 2026-09-18 closed-system reassessment argued that the creator's own
authenticated statements fix the *shape* of what is left: no internet is
needed to solve (message 9639), the finish after `yinyang` is hours (9599,
39237), the last step is "a true giveaway", and every solved AES stage used
`SHA-256(concatenated riddle answers)` as its passphrase — an instruction the
SalPhaseIon page repeats twice (`sha256 ...`, `shabefanstoo`). SALPH's 80
ciphertext bytes fit a 64-character hex private key exactly. Under that
shape the unknown is a short visible string to hash, not a cipher to break.

The lane this phase pre-registers: enumerate the house-style password grammar
over the creator's macro slots
(`yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice -> yinyang`),
with each slot filled by one already-authenticated checkpoint value or
omitted, joined in macro order under the solved-stage assembly conventions,
and check the whole product against SALPH's exact oracle. Before anything
runs, this phase answers: **which of those passphrase materials have already
been tried against SALPH, and which are genuinely new?**

Why the discipline is different for this lock: the SALPH detector (PKCS#7 +
printable z-score, or the exact 64-byte full-pad shape) has a per-attempt
false-accept rate far below 1e-9. Exhausting a bounded, pre-declared product
against an exact-match lock is not multiple-testing creep; that objection is
about statistical scores. What the pre-registration must still guarantee is
that the value sets were closed before the run and contain only
authenticated checkpoint outputs.

## Frozen inputs

**Slot value sets** (62 values, each tagged with its ledger/phase source in
the script's `slot_values()`):

| Slot | n | Values (source) |
|---|---:|---|
| `yellowblueprimes` | 15 | `574061` (F-CHAIN-001); `08C26D`, `F73D92` (clue ledger 2020-01-14); `311027`, `04BEF3` (F-CHAIN-019 / G-FLOWER-001); the two authenticated 24-bit strings; `163` (FEFE zero-based prime index); `1421`, `1,4,21` (creator hint); the fitted prime walk's blue list (sum 401) and yellow list (sum 400), each comma-joined and concatenated; the label `yellowblueprimes` |
| `matrixsumlist` | 18 | `23167`, `23,16,7`, `23 16 7`, `46` (F-CHAIN-002); `IZLKESEEDQPPEN` (recovered guide); the 31-character selection (F-CHAIN-011) and its 30-character Phase 270 form; `401`, `400`, `73`, `401400`, `40140073`, `401,400,73` (stage summary sums); `FF67`, `255103`, `255,103` (G-MATPROD-001); `kit` (G-KIT-001); the label |
| `lastwordsbeforearchichoice` | 19 | `BOTH ULTIMATELY THE` / `bothultimatelythe` (F-CHAIN-003); `BUT`, `HYE`, `BUTHYE` (F-CHAIN-004); `BYE` (F-CHAIN-006); the last 1–7 words before the Architect's `choice` in the film/screenplay-stable sentence (Phase 216); `CIAO BELLA O` / `ciaobellao` (F-CHAIN-008); the Stage-1 password (the last words typed before the `choice...` page) and `THEFLOWER` (F-CHAIN-019); `causality`; the label |
| `yinyang` | 10 | `yinyang`, `yin yang`, `yingyang`, `ying yang` (macro + creator spelling); `salvation`; `salphaseion`, `SalPhaseIon`, `cosmicduality`, `Cosmic Duality` (page titles); `thispassword` (page label) |

**Assembly conventions** (Phase 341's solved-boundary grammar): riddle-order
concatenation with no separator (primary) and a single-space join (the page's
own token rendering) as the one hedge axis. Order is fixed to macro order;
no permutations. Every non-empty ordered slot subset is a cell: 15 subsets
connected plus 11 multi-slot subsets spaced = 26 cells.

**Expansion**: the project's standard `answer_forms() x
keystr_forms(newline_variants=True)` — raw / SHA-256 hex / double SHA-256,
each with none / LF / CRLF, over the base and its plain casings and the
letters-only stripping. This is exactly what the Phase 322/334 GPU sweeps
used, so a later run is form-for-form comparable.

**Coverage sources** (18; every one must have had SALPH in scope under a
passphrase oracle, and each is expanded the way its own record says it
expanded): the 648 curated corpus (Phases 79/253/522, newline forms), the
66,433-candidate medium corpus (Phases 323/328, no newline forms), the
Phase 322 and 334 macro-fragment permutation corpora (newline forms), the
V2 registry pool (Phases 253–256), and the script-generated families of
Phases 0.1, 4, 121, 179, 216, 232, 234, 265, 267, 372, and 461, each with
its recorded form space (for instance Phase 4 tried raw + SHA only; Phase
461 tried raw case forms only). Sweeps deliberately **not** counted, with
reasons, are listed in the script's `EXCLUDED_SWEEPS`: Phases 270, 480, 481
(P32TRAILING only), 317 and 268/269 (no shared vocabulary), and every
raw-key-material tier (not passphrases).

## Method

`tools/gsmg/phase523_slot_grammar_overlap_audit.py --run`. Zero oracle
calls: the module imports only the two form-expansion helpers from
`cb_common`, and the unit test asserts that no decrypt function is present
in its namespace. Every tested corpus is expanded into passphrase materials
and stored as 64-bit keys; every candidate base is expanded the same way
and each material looked up. Materials are tagged by derivation
(`literal` family = the base and its plain casings; `alpha` family =
`answer_forms()`' letters-only collapse), because a digit-bearing base such
as `574061kit` collapses to `kit`, and coverage of `kit` says nothing about
whether `574061kit` was ever tried. Classes per base: `new`,
`alpha_only_covered`, `literal_partially_covered`, `all_covered`.

A first version of the classifier reported only covered/not-covered and
showed 8,434 "partially covered" bases; on inspection almost all of that
was the alpha collapse. The tagged classifier replaced it before any result
was recorded.

## Result

| Quantity | Value |
|---|---:|
| Candidate bases (exact-string deduplicated across cells) | 133,696 |
| Expanded materials | 6,245,946 |
| Literal-family materials | 3,137,967 |
| Literal-family materials already tested against SALPH | 726 |
| Bases `new` | 125,167 |
| Bases `alpha_only_covered` | 8,480 |
| Bases `literal_partially_covered` | 10 |
| Bases `all_covered` | 39 |
| Tested-material keys built from the 18 sources | 2,456,427 |

The 39 fully covered bases are 27 single-slot values plus the 12 pure-label
concatenations (`yellowblueprimesmatrixsumlist` and so on) that Phases
79/322/334 already swept. No multi-slot base built from checkpoint
*values* has ever had its literal form tried against SALPH.

Single-slot values never tried against SALPH in any literal form (25):
`163`; the four prime-list serializations; `23,16,7`, `23 16 7`, `46`; the
30-character selection; `401`, `400`, `73`, `401400`, `40140073`,
`401,400,73`; `FF67`, `255103`, `255,103`; `kit`; and the last 1–6 words
before `choice` (only the full seven-word sentence was tested, Phase 216).

Single-slot values tried only in part: `311027` (raw only, Phase 461),
`04BEF3` (raw casings only), `1421` and `1,4,21` (raw + SHA only, Phase 4),
the 31-character selection (lowercase forms only, Phase 121), `THEFLOWER`
(raw casings only, Phase 461), `yin yang` and `yingyang` (no newline
forms). `CIAO BELLA O` and `ying yang` are covered only through their
letters-only collapse.

Artifacts written to `_work/phase523/` (gitignored, reproducible):
`manifest.tsv` (every base with cell, class, and per-value provenance;
SHA-256 `0f2b73fd4656eeb63f596dfb8658bcd8a851aa4970b1faa0badfca06890b6a52`),
`not_all_covered_bases.txt` (133,657 bases; SHA-256
`ff5e80e9ba199fd6046a655c8b45c2f3a6ac0b88aa62ab8422075fc0cd092a18`), and
`report.json`.

## Disposition

Structural-only: this phase makes no claim about any password. It
establishes that the slot-grammar product is essentially untested (0.02% of
its literal-family materials have ever been tried against SALPH) and
freezes the universe a later execution phase would consume.

## Pre-registered execution phase (not run here)

- **Input**: `not_all_covered_bases.txt` by the digest above, expanded with
  the standard newline-variant form space (about 6.2M materials).
- **Target**: SALPH under `KDF_VARIANTS` (6 legacy CBC profiles) as primary;
  the other three blobs may ride along at negligible cost.
- **Detector**: the standard oracle's PKCS#7 + printable-z / exact
  64-byte full-pad shape; any hit is then checked by deriving the address
  from the plaintext and comparing to the prize address.
- **Stop rule**: zero hits closes the lane for these 62 values and two
  join conventions. Do not widen values, add separators, or permute slot
  order on a negative; a new authenticated checkpoint value is the only
  reopen trigger.
- **Cost**: about 37M CBC decrypts for SALPH alone; minutes on the GPU
  oracle, well under an hour on the CPU oracle.

## Facts affected

None.

## Supersedes/corrects

None. Corrects only this phase's own first classifier (see Method).

## Artifacts

- `tools/gsmg/phase523_slot_grammar_overlap_audit.py` (`--self-test`,
  `--run`, `--fast` for development)
- `tools/gsmg/test_phase523_slot_grammar_overlap_audit.py` (4 tests)
- `_work/phase523/{manifest.tsv,not_all_covered_bases.txt,report.json}`

## Reopen condition

The overlap result itself only changes if a prior sweep with SALPH in scope
is found that this phase's source table omits; add it to
`COVERAGE_SOURCES` and rerun rather than editing the numbers.
