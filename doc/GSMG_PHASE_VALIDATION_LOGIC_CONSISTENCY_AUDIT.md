---
type: audit
status: closed
result: mixed
disposition: structural-only
topics:
  - validation-logic
  - phase-index
  - meta-audit
---

# GSMG Phase & Brainstorm Validation-Logic Consistency Audit

## Purpose

A full pass over the project's own validation discipline: for every phase in
[tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md) (367 phases, 0.1 through
367) and every dated doc in [Brainstorms](Brainstorms/), does the stated
**premise** match the actual **validation conditions**, and does the
**conclusion** neither over- nor understate what those conditions actually
showed? This is distinct from [GSMG_PHASE_BOUNDARY_REAUDIT](GSMG_PHASE_BOUNDARY_REAUDIT.md)
(tracks which *conclusions* got materially changed, stopped at ~Phase 66) and
[GSMG_PHASE_REOPENING_REASSESSMENT](GSMG_PHASE_REOPENING_REASSESSMENT.md)
(asks which *negatives* deserve a rerun) — this audit instead checks internal
consistency of the record itself: premise vs. method vs. stated result, and
whether corrections a phase makes to itself or to an earlier phase actually
propagate to every artifact that cites it.

## Method

Ten independent reviews (nine ~40-phase FINDINGS.md ranges + one covering all
24 Brainstorm docs), each applying a fixed rubric: premise novelty vs. closed
prior work; closed/pre-declared candidate universes and exact/structural
success bars; conclusion language calibrated to evidence tier (the project's
own hard-won distinction between an authenticated artifact and an
*interpretation* of it — see `feedback_present_unconfirmed_as_unconfirmed`);
FINDINGS.md vs. linked `doc/GSMG_*.md` vs. `GSMG_PHASE_INDEX.md` vs.
`GSMG_FACT_LEDGER.md` agreement; and explicit stop rules / gap registration.
Ambiguities the reviews flagged as needing confirmation (a possible Phase
44/366 conflict, whether pre-Phase-78 candidate lists were ever re-swept, the
disposition of two Phase 163 TODOs, whether the Phase 310 seed bug was
actually fixed) were independently re-verified against the source files
before being written up below — nothing here rests on an unconfirmed batch
report.

## Headline result

This project already self-audits unusually well. Across 367 phases and 24
brainstorm docs, **no case was found of a "confirmed"/"verified"/"proven"
label misapplied to an unconfirmed community coincidence**, no negative
result was found overextended beyond its declared candidate family, and no
brainstorm doc was found missing its required closed-universe/exact-bar/
stop-rule structure. The large majority of what an audit like this looks
for — silent overclaiming, uncorrected drift, unscoped negatives — is
already caught and fixed *by the project itself*, inline, as a matter of
course (Phases 33/34→223, 88→89, 94→95, 97→98/99, 106→112, 131→132,
217→223, 226→230, 260→261, 356–359's same-day scope corrections, etc. are
all real self-corrections that already happened and are already accurate at
the FINDINGS.md prose level).

The issues below are what's left after that self-correction: places where a
correction happened but didn't fully propagate to every artifact that cites
the corrected phase, a handful of genuinely dropped/untracked TODOs, one
latent code bug, and a few loose word choices.

## Finding 1 (systemic, medium priority): corrections don't propagate to the generated Phase Index

`GSMG_PHASE_INDEX.md`'s Result column is generated from each phase's
original `## Phase N` heading text
([GSMG_PHASE_TEMPLATE](GSMG_PHASE_TEMPLATE.md) notes this is a "reasonable
default," not a long-term design). When a phase corrects *itself* same-day,
or a *later* phase corrects an *earlier* one, that correction is reliably
written into FINDINGS.md (inline banners, addenda, "Later correction"
notes) — but the heading text that feeds the generator is not retroactively
edited, so the Index row, and in one case a dedicated audit doc's lead
section, can keep showing the pre-correction claim to a reader who only
skims the table.

| Phase(s) | What the Index/doc row still says | What FINDINGS.md itself already says | Where the accurate version lives |
|---|---|---|---|
| 106 | "a calibrated partial oracle for the checkerboard escape pair \| real idea, real calibration, real negative" | Superseded by Phase 112 — the objective was inverted; code-IC is actually a validated *positive* partial oracle | Phase 106's own FINDINGS banner; Phase 112's correct Index row |
| 94 / 95 | "real launch (clean negative) + vanity-substring classification added" reads as if exercised together | The classifier was added but explicitly not applied retroactively to the completed run; Phase 95 replaced the logic before it was ever run for real | Phase 94/95 FINDINGS prose |
| 197 | Index links Phase 197 to `GSMG_ARCHITECT_PASSAGE_RESIDUAL_AUDIT.md` | Phase 197's own entry names its real canonical doc: `GSMG_FIRST_PIECE_BITPLANE_VERIFICATION.md` | Phase 197 FINDINGS text |
| 217 + `GSMG_MINIMAL_MACRO_CHAIN_AUDIT.md` | Heading/Index/doc's `## Result` section: chain unconditionally "reaches `yinyang`" | Phase 223 (same day) downgrades this — the mirror reading reaches BUT/HYE but does not establish `yinyang` was reached | FINDINGS "Later correction (Phase 223)" note; the doc's own "Revised boundary" section (buried below the unhedged `## Result`) |
| 260 | Index Result: Roman `CD=400` "independently echoes" the yellow prime sum | Phase 261 (next phase) corrects this to "corroboration only," since the drop-cap style is book-wide, not title-specific | `GSMG_ROMAN_RAIL_PRIME_SUM_AUDIT.md` already has the corrected wording |
| 356, 357, 358, 359 | Headings/Index still claim e.g. "one native 7x7-pixel module," "no independent asset" | Each has a same-day "Scope correction" appended narrowing the claim to the single canonical variant, not all six | End of each phase's own FINDINGS entry |

**Suggested resolution:** these are all narrow, identifiable edits (add a
one-line "superseded by Phase N" note to each affected Index Result cell and
add a corrective blockquote to `GSMG_MINIMAL_MACRO_CHAIN_AUDIT.md`'s top,
matching the convention already used by `GSMG_PHASE_BOUNDARY_REAUDIT.md`,
`GSMG_POST_YINYANG_DATAFLOW_AUDIT.md`, and `GSMG_CREATOR_FEASIBILITY_ENVELOPE_AUDIT.md`).
Longer-term, `generate_phase_index.py` has no way to know a phase was
corrected after the fact — worth a `Superseded-by:` field once
`GSMG_PHASE_TEMPLATE.md`'s structured fields are more widely adopted, per
that doc's own noted future-extension path.

## Finding 2 (medium): a candidate list tested before the Phase 78 oracle fix was never confirmed re-swept

Phase 78 fixed a real false-negative in `aes_try_open_bytes()`: it had been
discarding correct AES decrypts whose plaintext body is binary
(non-printable) key material — exactly the shape implied by the
authenticated "half and better half" plaintext. Checking which pre-Phase-78
candidate lists were later folded into the curated corpus that received the
post-fix re-sweep:

- `looking_forward_candidates.txt` and `fefe_plated_seed_candidates.txt` —
  **confirmed registered** in `curated_candidate_registry.py` /
  `curated_candidate_corpus_audit.py`, so these did receive later coverage.
- Phase 75's `YOUWON`/`YOUWONX` candidates — **confirmed not present** in
  either registry file. Phase 75 itself tested them directly against
  SALPH/COSMIC/P32TRAILING, but only under the pre-fix, printable-gated
  oracle; Phase 147's later follow-up tested a different reading (a raw
  private-key tail), not these candidates as passwords under the corrected
  oracle.

**Suggested resolution:** a small bounded re-sweep of exactly `YOUWON` and
`YOUWONX` (the same forms Phase 75 already enumerated) against the
post-Phase-78 (or current GPU) oracle would close this identifiable,
narrow gap rather than an assumed one.

## Finding 3 (low-medium): two Phase 163 TODOs, one substantially closed, one still open and untracked

Phase 163 flagged two coverage gaps explicitly in its own text:

1. A full Tier-1 nopad rerun (24,554 candidates) with
   `--whitespace-variants` — **still appears unrun at that scope.** Later
   phases (165–167) only exercised `--whitespace-variants` at the smaller
   648-candidate curated tier, not the full Tier-1 set. Not present in
   `GSMG_OPEN_GAP_REGISTRY.md`.
2. The full padded `EXTENDED_CIPHER_VARIANTS` oracle sweep of the
   Tier1-3 union (~66,441 candidates) — **substantially closed**, just not
   cross-referenced: Phase 323/328's GPU-oracle backfill later ran the
   "medium-curated Tier 1-3 union" (66,433 candidates — same corpus, later
   count) through the AES-CBC/KDF oracle, negative. Phase 163's original
   TODO is never explicitly marked resolved by that later work.

**Suggested resolution:** for (1), either run the bounded Tier-1
`--whitespace-variants` rerun or add one sentence somewhere explicit that
it's deprioritized (low puzzle-priority, already-negative oracle family) so
it stops reading as silently dropped. For (2), a one-line cross-reference
from Phase 163 (or the Fact Ledger) to Phase 323/328 would close the loop.

## Finding 4 (low-medium): a self-disclosed, still-unfixed non-reproducible seed

Phase 310's `dbbi_faed_nihilist_additive_audit.py` seeds its hillclimb with
Python's built-in `hash()` on a str/tuple (`hash((name, e1, e2, topo, kw,
sign)) & 0xffff`), which is `PYTHONHASHSEED`-randomized per process. Phase
310's own dated addendum (added while building Phase 321) discloses this
honestly and confirms empirically that reruns produce different "best
keyword" attributions, and correctly argues the *phase's negative verdict*
is unaffected (the profile was uniform/near-baseline, not a narrow spike a
seeding artifact could manufacture). Checked the current script directly:
the `hash()` call is still present and unfixed — only documented, not
corrected in code.

**Suggested resolution:** switch the seed derivation to something
process-stable (e.g. `hashlib.sha256` on a canonical string) or add an
explicit code comment/TODO, so a future reuse of this script as a template
doesn't silently inherit the non-reproducibility.

## Finding 5 (low, cosmetic): language-calibration and index-linking nitpicks

| Item | Note |
|---|---|
| Phase 258 | Uses "confirmed" for the icons' "opposites attract" reading — an interpretive (if strong) reading, not a creator/byte-level fact; stricter elsewhere in the same range (e.g. Phase 253). Consider "established"/"well-supported." |
| Brainstorm: `2026-08-18 - Two Sloppy Days...` item 11 | "ROIBOT is literally ROBOT with an I inserted... harder to justify as coincidental" overstates a naming pun with no test attached, against the doc's own otherwise careful weak/moderate/strong grading. |
| `GSMG_FACT_LEDGER.md` F-CHAIN-002 | Could add Phase 58 (independent *Matrix Reloaded* dialogue-count route to the same `[23,16,7]`) to "Established by," per the ledger's own 3+-dependent-docs inclusion bar. Optional completeness, not an error. |
| Phase 366 heading | "chronology rejects a creator-confirmed 31-character transition" misparses on a skim; body text is unambiguous and correctly calibrated. Reword only if the heading is ever revisited. |
| Phases 179/180, 181/182 in FINDINGS.md | Physically out of numeric order in the file (each pair's higher number appears first), though the Phase Index lists them correctly. Cosmetic; would only matter to a future tool assuming monotonic file order. |
| Audit-doc column mismatches (Phases 40, 153, 155, 196, ~14 phases in 281–320, several in 321–367) | `GSMG_PHASE_INDEX.md`'s keyword-matched "Audit doc" column points to topically-unrelated docs at real scale. **Already explicitly disclosed** in the Index's own header ("best-effort... not guaranteed correct... FINDINGS.md link is authoritative"), so not a hidden inconsistency — listed here only because of its frequency. Phase 197 (Finding 1's table) is the one case where this is a direct *conflict* with the phase's own self-declared doc, not just an absence of coverage, and is worth prioritizing over the rest. |

## Not issues (checked and cleared)

- **Phase 44 vs. Phase 366**: both concern "in front of your eyes" but test
  different claims (Phase 44: AES/Key-Wrap coverage of *Looking Forward*
  candidates; Phase 366: whether the 2026 `Bingo` exchange authenticates the
  31-character mask/prime chain). Verified directly against FINDINGS.md —
  Phase 366 does not reference or correct Phase 44.

## Status (2026-08-22): corrections applied

The mechanical/documentation-level fixes above were applied:

- `generate_phase_index.py` gained an `index_note`/`audit_doc_override`
  marker mechanism (stacked HTML-comment lines directly above a `## Phase N`
  heading) so a correction survives regeneration instead of being silently
  overwritten. Phases 94, 106, 217, 260, 356, 357, 358, 359 now carry
  `index_note` markers; Phase 197 carries an `audit_doc_override`.
  `doc/GSMG_PHASE_INDEX.md` was regenerated and `--check` confirms it is
  stable (deterministic re-runs produce byte-identical output).
- `GSMG_MINIMAL_MACRO_CHAIN_AUDIT.md` gained the missing Phase-223-correction
  blockquote, matching its sibling docs' convention.
- `GSMG_FACT_LEDGER.md` F-CHAIN-002 now cites Phase 58 alongside 32/97/250.
- Phase 75's `YOUWON`/`YOUWONX` gap and Phase 163's two TODOs each got an
  explicit disposition note in FINDINGS.md (one closed by cross-reference to
  Phase 323/328, the other left open but now explicitly, not silently).
- Phase 258's "confirmed" was softened to "established"; the Brainstorm
  ROIBOT sentence was softened to "secondary, unverified."
- `dbbi_faed_nihilist_additive_audit.py`'s non-reproducible `hash()`-based
  seed was fixed to a stable `hashlib`-derived seed (self-test passes).

**Update (2026-08-22):** Finding 2's actual bounded re-sweep was pursued as
its own phase -- FINDINGS.md Phase 368 (`tools/gsmg/youwon_full_oracle_backfill.py`)
reused Phase 75's exact candidate forms under the current oracle across
CBC/ECB/stream/Key Wrap and all 4 blobs: 0 hits. Finding 2 is closed.

**Left as-is:** the Phase 366 heading reword and the Phase 179/180
file-ordering cosmetic issue (low value, and heading edits change GitHub
anchor slugs).

Full project regression suite (`tools/gsmg/test_recent_audits.py`, 122
tests) passes after these changes.
