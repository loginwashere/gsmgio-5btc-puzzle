---
type: index
status: live
topics:
  - open-gap-registry
---

# GSMG Open-Gap Registry

Exactly what's blocking progress, one gap per row, each with a stable ID.
Distinct from [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md)
(per-*candidate* rows, what operation might advance) and
[GSMG_FACT_LEDGER](GSMG_FACT_LEDGER.md) (per-*claim* rows, what's currently
accepted). This is per-*gap*: what specific missing evidence would unblock
something, independent of which candidate depends on it. A gap closing does
not mean a candidate is promoted — it means the worksheet's G1–G5 gates can
now be re-evaluated with that evidence in hand.

Most rows here restate a worksheet row's "Reopen trigger" column with a
stable ID and cross-link, rather than duplicating its reasoning — see the
linked row/audit for why the gap exists. Add a row only when it is not
already fully covered by an existing one.

## Registry

`Category` groups gaps by the kind of evidence that would close them.
`Priority` is P0 (blocks the live frontier directly) through P2
(narrative/speculative branch, no active work expected). `State` says
whether the gap is currently actionable: `open` (something can be done now
— a search, a re-derivation), `external` (blocked on a source outside our
control, e.g. an unphotographed book page), or `parked` (no near-term path
to evidence; revisit only if new material surfaces).

| Gap ID | Blocks | What's missing | Evidence type needed | Category | Priority | State | Next action | Closure condition | Canonical reference |
|---|---|---|---|---|---|---|---|---|---|
| G-MSL-001 | 31-char DBBI selection → `matrixsumlist` | No source binds the selection to matrix dimensions, traversal, value mapping, aggregation, or serialization (7/7 G3 fields unbound). The *Cosmic Duality* book's pages 57–58 were photographed and transcribed 2026-08-13 (Phase 259): page 57 is a full-page plate reprint of the already-known Franz Stuck "Sin" painting, page 58 continues the Eve/Tertullian/Council-of-Mâcon narrative and a Black Madonna sidebar — no matrix, dimension, or traversal content, and no operational numeric schema (the page's own dates/counts — 1893, 1656, 585, fifty-nine bishops, a majority of one — are ordinary historical narrative, not a selected/consumed value). All 7/7 G3 fields remain unbound after review | Primary source other than the *Cosmic Duality* book — a creator clue, recovered guide step, or code predating the output that uniquely fixes matrix dimensions, traversal, and operation | primary-source | P0 | parked | None planned; the book's pages 57–58 (the only remaining genuinely uninspected primary source) are now reviewed and negative. Revisit only if a new creator source, recovered guide, or pre-cutoff code artifact surfaces | A creator clue, recovered guide step, or code artifact is found that fixes the 7 G3 fields against the 31-character selection | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet) |
| G-ARCH-001 | Architect words → BYE → CIAO BELLA O | No creator clue selects the beginnings/endings reading or the B↔H mirror operation itself. Phases 247–248 ran all five bounded brainstorm lanes: newer-export coverage, targeted selector vocabulary, Architect+selector replies/reactions, all 88 creator-authored media records (83 unique payloads), and direct precedent-transfer language — all negative | Creator clue (Telegram, either corpus) explicitly selecting this operation | creator-clue | P1 | parked | None planned; all five narrower lanes are exhausted alongside the general corpus sweep. Revisit only if a new Telegram export, creator-media payload, or corpus surfaces (checked and discarded so far: `ChatExport_2026-08-07` is unrelated, `2026-08-09` is a 98-byte unfinished header, `2026-08-09 (1)`'s new window has zero creator messages) | A creator message/media object is found that names or visually selects this operation, transfers a prior operation to this boundary, or replies to/reacts on a solver message proposing it | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet); [GSMG_ARCHITECT_MIRROR_SELECTOR_AUDIT](GSMG_ARCHITECT_MIRROR_SELECTOR_AUDIT.md) |
| G-ESC-001 | FAED decoder selection | FAED's independently-best `{g,i}` escape pair and the Architect-mirror-predicted `{h,e}` pair remain unreconciled; neither pair's mirror9 image validly segments its own origin stream. Phases 243/244/249 closed the entire page-boundary branch: textarea attributes, CSS, JS, comments, whitespace, and byte-verified content across 16 successful archive capture events (5 Wayback + 11 urlscan, 2023-05-31 to 2026-04-05) supply no selector; DOM ancestry/sibling selectors are inapplicable by construction since DBBI/FAED share one text node | A genuinely external source — a creator clue, a primary artifact outside this page, or a capture with a main-document hash outside the 5 authenticated Wayback variants — that independently selects one pair, or explains why the two pairs need not reconcile | derivation | P0 | parked | None planned; the page-boundary branch and both known archive surfaces are exhausted. Revisit only if a new creator source, primary artifact, or genuinely new page variant surfaces | A genuinely external source agrees with one pair, or explains why reconciliation is not required | [GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT](GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT.md); [GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md); [GSMG_SALPHASEION_URLSCAN_HISTORY_AUDIT](GSMG_SALPHASEION_URLSCAN_HISTORY_AUDIT.md) |
| G-YIN-001 | DBBI/FAED → creator's `yinyang` state | No operator/relationship is selected between the two raw streams at all — a live semantic boundary, not yet executable | Creator evidence defining how the two streams interact | creator-clue | P0 | parked | None planned; the Telegram corpora (Phase 52, 124, 215) and every decoded-slot page-syntax house rule (Phase 238) are already exhausted for this row — revisit only if a new export or a genuinely new page artifact surfaces | A creator source, or a structurally forced single reading not already ruled out by Phase 238, selects an operator | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet) |
| G-PRIME-001 | Prime lists → `401/400/73` | No instruction or key consumes the three sums; no downstream target. Phase 260 (2026-08-13) found the *Cosmic Duality* book's interior title page renders only its `C`/`D` initials as miniature yin-yang glyphs (pixel-confirmed, absent from the front cover's plain rendering of the same title); Roman `CD = 400` exactly matches the independently-derived yellow sum. This upgrades `400` from internally-fitted to independently echoed by an authenticated physical artifact, but supplies no G3 operation or consumer for any of the three sums | Explicit clue consuming the three sums | creator-clue | P2 | parked | None planned; revisit only if a new consumer candidate is proposed | A clue or downstream artifact is shown to consume these three sums | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet) |
| G-MATPROD-001 | Matrix product → `(255,103)` / `FF67` | Multiplication as the operation, and a byte consumer, are both unselected | Clue selecting multiplication and a byte consumer | derivation | P2 | parked | None planned; revisit only if a new consumer candidate is proposed | A clue selects multiplication and names a byte consumer | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet) |
| G-KIT-001 | Second matrix list difference → reversed `KIT` | Subtraction, A1Z26, and reversal are three unselected steps | Clue explicitly asking for difference/reversal or a young rabbit | creator-clue | P2 | parked | None planned; revisit only if a new consumer candidate is proposed | A clue explicitly requests difference/reversal or names the rabbit reading | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet) |
| G-GGN-001 | FEFE tuple `{1,4,21}` → `ggn` → secp256k1 | Indexing convention, `g→G`, scalar `k`, negation, and curve are all unselected | Independent clue supplying `k` and selecting group order/negation | creator-clue | P2 | parked | None planned; revisit only if a new consumer candidate is proposed | An independent clue supplies `k` and selects group order/negation | [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md#master-worksheet) |

## Adding a gap

A gap earns a row only if it is genuinely open (not one of the worksheet's
closed rows — those need primary evidence fixing a missing parameter or a
demonstrably incorrect prior audit to reopen at all, per the worksheet's own
rules, and belong in [MOC - Negative Results](MOC%20-%20Negative%20Results.md)
instead) and is not already covered by an existing row. Close a row (set
`status: closed`, do not delete it) when its "Evidence type needed" is
actually supplied — closing a gap is not the same as promoting the
candidate it blocks, which still needs its own G1–G5 pass.
