---
type: audit
status: live
topics:
  - topology-audit
  - frontier-assumption-ledger
---

# GSMG Topology Audit

**Question.** This project has run ~50 cryptanalytic models against DBBI/
FAED and dozens more against SALPH/COSMIC/P32TRAILING/matrixsumlist/
Architect, almost all negative. Each of those phases closes *one specific
model under a specific assumed topology* — but no phase has directly
compared competing topologies against each other, or tested the null
hypothesis that some of these objects don't connect at all. This audit does
that comparison, using [GSMG_FRONTIER_ASSUMPTION_LEDGER](GSMG_FRONTIER_ASSUMPTION_LEDGER.md)
as its evidence base. **No decryption oracle is run here** — every score
below is a structural/evidentiary comparison over already-authenticated
facts and already-completed phases, per the project's own discipline of not
letting candidate-generation choices be tuned by oracle feedback.

**Candidate topologies** (T0 = null, T1-T8 as specified):

- **T0 — Null.** DBBI and FAED (and, by extension, other frontier objects)
  are not established to interact at all. Each may be independently
  consumed, or some may not be consumable objects in the cryptographic
  sense at this stage.
- **T1 — Single linear chain.** All frontier objects feed one sequential
  pipeline in page order.
- **T2 — P32TRAILING parallel.** P32TRAILING is the direct Phase-3.2
  continuation (literally appended to the solved Phase 3.2 plaintext);
  SALPH/COSMIC are a separate, parallel pair not chained to P32.
- **T3 — DBBI/FAED combine symmetrically** (peers, joint decode object).
- **T4 — DBBI instructs FAED** (DBBI is the operator, FAED the operand).
- **T5 — FAED instructs DBBI** (reverse of T4).
- **T6 — DBBI and FAED have separate, independent consumers**; they never
  combine, but each still feeds something downstream.
- **T7 — SALPH self-contained, then its answer feeds COSMIC.**
- **T8 — Some intermediate results are recognition checkpoints, not
  operands** — they confirm you're on the right interpretive path without
  being consumed as cipher/key material for a further transform.

## Scoring

Scored on: authenticated tokens consumed (**Auth**), page/source order
preserved (**Order**), unsupported edges introduced (**Unsup. edges** —
lower is better), unresolved tokens left behind (**Unresolved**),
compatibility with the solved-stage grammar (**Grammar**, per Phase 341),
dependency on external evidence not yet in hand (**Ext. dep.**), and number
of arbitrary orientation/operator choices required (**Arbitrary** — lower
is better). This is a qualitative structural comparison, not a numeric
model score — treat the ratings as reasoning aids, not as a computed
ranking.

| Topology | Auth | Order | Unsup. edges | Unresolved | Grammar | Ext. dep. | Arbitrary | Real (not inherited) support |
|---|---|---|---|---|---|---|---|---|
| **T0 — Null** | Highest — assumes nothing beyond what's proven | n/a | **Zero** | Reframes rather than leaves gaps | Compatible (each solved boundary is locally self-contained, no cross-object concatenation was ever required) | None | **Zero** | Never directly tested as a first-class hypothesis (see below) — but nothing in the ledger contradicts it, and Phase 289 gestures at it explicitly |
| **T1 — Linear chain** | Real for *order* (Phase 218); false for *operation* | Yes — this IS the page order | High — every specific instantiation tested (11, 12, 217, 238) failed or was corrected | matrixsumlist unbound; `thispassword`'s attachment remains a genuine three-way unresolved tie — `password_for_faed`, `faed_answer_is_password`, and `password_for_salph_blob` each lack a direct role-selecting witness under the three declared primary-evidence tests (literal DOM bytes, solved-stage grammar, creator reply record — Phase 377, corrected same-day), and no hard contradiction was detected under those same declared checks (paraphrase-level creator evidence is explicitly unchecked), but this does not establish the tie is unresolvable by any possible model; no edge here has a standing default | Weak — solved boundaries are locally instructed, not built by concatenating prior-stage plaintext into next-stage key material | Low | High — which operator combines which pair is unresolved and unbounded | **Weakest topology in the ledger.** Phase 238: zero of six adjacency rules survive. Phase 220: no presentational binding. Phase 104: no conserved dual-pole model. The only real support is *order*, not *operation*, and Phase 218 says so itself |
| **T2 — P32TRAILING parallel** | **Highest of any non-null topology** — P32TRAILING's position is a measured structural fact (embedded at the end of the already-solved Phase 3.2 plaintext), not a guess | Compatible — treats P32TRAILING as continuing the *solved* chain, not the unsolved one | **Low** — doesn't require inventing a DBBI/FAED combinator at all | P32TRAILING itself remains unresolved but requires no new topology to attack | **Strong** — directly reuses Phase 341's validated solved-boundary grammar | None new | **Low** — no combinator choice needed; SALPH/COSMIC treated as independently self-contained | Phase 220 (no cross-textarea binding) and Phase 224 (SALPH-self "nearer/unexplained" default) both support treating SALPH/COSMIC as independent rather than P32-chained |
| **T3 — DBBI/FAED symmetric combine** | Moderate | Partial | Moderate-High | matrixsumlist, escape-pair reconciliation | Untested against Phase 341's grammar | None new | High — ~45 distinct operators tried | **Most heavily tested, least surviving.** ~45 negative operator tests (Phases 272-321). Phase 104/112 asymmetry (DBBI's real fit is direct; FAED's needs a code-IC oracle to surface) is evidence *against* treating them as symmetric peers |
| **T4 — DBBI instructs FAED** | Moderate | Consistent with page order (DBBI precedes FAED) | Moderate | Same as T3 | Untested | None new | Moderate | No phase directly tests this vs. T5. Weak, low-confidence lean *toward* T4 from the escape-pair asymmetry (DBBI's `{b,e}` is directly legible; FAED's `{g,i}` only surfaces under a derived oracle, Phase 112) — my own inference from the ledger, not a project finding |
| **T5 — FAED instructs DBBI** | Moderate | Inconsistent with page order | Moderate | Same as T3 | Untested | None new | Moderate | No direct support found; weaker than T4 on the page-order criterion alone |
| **T6 — Independent consumers** | Moderate-High | Compatible (each consumed where it sits) | Low | Reframes matrixsumlist/escape-pair gaps as per-object, not joint | Compatible with the "locally instructed" solved-boundary pattern | None new | Low | Phase 217/223's own finding of **two separate live routes** (six-digit-prime route vs. 31-char DBBI route) rather than one merged chain directly supports this over T1/T3. Phase 289 tests a selector variant of this and goes negative, but the general shape survives |
| **T7 — SALPH self-contained -> COSMIC** | Moderate | Compatible | Low-Moderate (the *specific* tested handoff mechanism failed; the general idea is untested, not falsified) | COSMIC unresolved regardless | Compatible with locally-instructed solved boundaries for the SALPH-self half | None new | Low for the self-contained half; unresolved for the handoff half | Phase 224: SALPH-self reading is the "nearer/unexplained" **standing default** — this is real, if modest, support; the specific DOM-order handoff justification it tested is falsified, not the general claim |
| **T8 — Checkpoints, not operands** | Highest — reframes existing positive results (SALVATION, BUT/HYE, escape pairs, matrixsumlist selection) as confirmed-but-non-consuming | n/a (orthogonal to ordering) | **Zero** — this is a claim about *what kind of thing* a result is, not a new edge | Explicitly reframes "unresolved" results as *not meant to be resolved as key material* | **Strongest compatibility** — matches how the 3 solved boundaries actually work (local instruction, not concatenation of prior artifacts) | None new | **Zero** | **Best-supported topology in the ledger.** Three independent phases converge from different angles: Phase 238 (zero-of-six adjacency rules — the single strongest falsification in this audit), Phase 223 (demotes BUT/HYE from "reaches yinyang" to checkpoint), Phase 96 (frames SALVATION the same way) |

## Verdict

**Per the user's own instruction: retained as ties, not forced to a single
winner.** Three topologies survive this comparison with real (not merely
inherited) support, and they are not mutually exclusive — in fact they
compose:

1. **T8 (checkpoints, not operands)** is the best-supported single claim in
   the entire ledger. It is not really a competing *topology* so much as a
   correction to how T1/T3/T4/T5 have been implicitly read: several of the
   project's "unresolved" results (SALVATION, BUT/HYE, the matrixsumlist
   selection, the escape pairs) may already be doing their job — confirming
   the solver is on the right interpretive path — without being intended as
   literal cipher/key material for a further transform. If true, the entire
   "find the right combinator" search direction (T3, the ~45-phase bulk
   block) is aimed at something that was never meant to exist.

2. **T2 (P32TRAILING parallel to a self-contained SALPH/COSMIC pair)** is
   the strongest *actionable* topology — it requires the fewest unsupported
   edges, leans on an already-measured structural fact (P32TRAILING's
   literal position at the end of the solved Phase 3.2 plaintext) rather
   than an assumption, and is the only topology that lets Phase 341's
   validated solved-boundary grammar be applied forward immediately,
   without first resolving DBBI/FAED at all.

3. **T0 (the null topology for DBBI/FAED)** is not "supported" by any
   phase, but critically, **it is also not contradicted by any phase** —
   and the ledger shows it has never actually been tested as a first-class
   hypothesis. This is the sharpest, most concrete form of the user's
   original hunch: *"dozens of later phases searched for ways to make DBBI
   and FAED interact... they do not prove that DBBI and FAED are peers; they
   must be combined."* That is now a ledger-backed finding, not a hunch:
   **~45 phases tested HOW DBBI/FAED combine; zero tested WHETHER they
   should be treated as interacting at all.**

**T1 (single linear chain)** and **T3 (DBBI/FAED symmetric combine)** are
the two topologies this project has invested the most phases in, and they
come out weakest under this scoring — not because they're untested, but
because the *specific* mechanisms other phases needed to make them true
(adjacency-implies-operand, presentational binding, a conserved dual-pole
model, a working combinator) have each been directly tested and failed.
T4/T5/T6/T7 don't have enough direct evidence to rank confidently against
each other; T6 gets modest real support from Phase 217/223's two-separate-
routes finding.

## Recommended next actions — status (updated 2026-08-22)

1. **T2 (P32TRAILING) transferred forward — done, Phase 370.** Phase 341's
   grammar, applied honestly, requires a local page annotation to fix its
   case/whitespace/prefix axes; P32TRAILING has none (byte-verified: the
   gap between the Phase-3.2.2 clue and the envelope is a bare `\r\n\r\n`
   separator). The transfer collapses to 4 closed password materials, all
   4 already exact duplicates of Phase 270's own "whole-text family." Zero
   genuinely new candidates; zero oracle queries made. This is a real,
   useful negative result, not a non-result — it confirms Phase 270 already
   performed this transfer in substance.
2. **T0/T6 (DBBI/FAED independent-consumer audit) — done, Phase 371.**
   *Not* run by feeding DBBI/FAED through Phase 341's grammar (that
   grammar needs decoded, annotated components; DBBI/FAED are raw and
   unannotated — forcing them through it would just be another candidate
   generator). Instead audited per-stream against the literal page
   structure: DBBI has one adjacent instruction (`matrixsumlist`, present
   but unexecutable per `G-MSL-001`); FAED has two (`lastwordsbeforearchichoice`,
   `thispassword`, reading toward the Architect passage generally rather
   than any transform of FAED itself -- Phase 372 later found Phase 101
   already retained three unreconciled roles for this instruction pair, so
   "points at G-ARCH-001's subject" here is a loose description, not a
   settled equivalence). Each stream has its own independent best-fit escape pair
   (`{b,e}` vs. `{g,i}`). No page evidence requires either stream as input
   to the other's consumer, and the two streams are NOT treated
   symmetrically by the page's own structure — the opposite of what T3
   (symmetric combine) would predict. This is not a proof of T0 (a
   negative/inconclusive result was explicitly permitted going in), but it
   is a real, executed test where none existed before.
3. **Do not run a new DBBI/FAED combinator search** (a 46th instantiation
   of T3) — both (1) and (2) are now done, and neither surfaced anything
   the ~45-phase T3 branch was missing. `G-MSL-001` (needs a new primary
   source for `matrixsumlist`'s schema) remains open and source-starved,
   not served by more cryptanalysis. *(Superseded below: this item
   originally also named `G-ARCH-001` as a second live next step in the
   same terms; Phase 372 found the relationship between `thispassword` and
   `G-ARCH-001` is not established — see the corrected Frontier statement.)*
4. `G-YIN-001`'s gap-registry row is sharpened (see
   [GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md)) to record that the
   null/independent-consumer question has now been tested, not merely
   flagged as untested.

Consistent with this project's brainstorm discipline: items 1-2 were each
closed-candidate-universe, exact-match-bar experiments with their own stop
rule — their negative/inconclusive results do not reopen T1/T3, they
complete this audit's own coverage.

## Frontier statement (updated 2026-08-22, Phase 372, corrected same-day)

Per the user's own proposed reframing, tested directly rather than
asserted: with DBBI/FAED, BUT/HYE, and the 31-character selection treated
as checkpoints unless independently consumed (Phases 369-371), Phase 372
ran a Phase-341 eligibility check on SALPH and COSMIC separately. Phase
372's first write-up overclaimed the result (asserting `thispassword`
requires `G-ARCH-001` specifically, and calling that gap the "sole"
remaining P0 boundary while the registry already carried two others at
P0); corrected here after review.

- **SALPH's hash_prefix branch's literal self-referential reading**
  ("our first hint is your last command," read as its own password) is
  Phase-341 grammar-eligible and is now **fully exhausted** — 18
  candidates, all exact duplicates of Phase 0.1's original sweep, widened
  to every established cipher family (CBC/ECB/stream/Key Wrap) across all
  4 blobs, 0 hits. The broader source-grounded SHA-operand readings were
  already separately closed by Phase 121, not by this manifest.
- **`thispassword`'s role is underdetermined, not "blocked on one named
  gap."** Phase 101 retained three unreconciled roles (password for FAED,
  FAED's answer merely labeled "password," or password for SALPH); no
  source selects among them. Only the third role would make this a SALPH
  dependency at all, and even then its operand is not established to be
  `G-ARCH-001`'s specific mirror-operation hypothesis rather than some
  other reading of "words before Architect choice." No candidate is
  generated for this branch.
- **COSMIC fails Phase-341 eligibility entirely** (0/5 fields bound; its
  textarea is byte-verified to be exactly the raw ciphertext, nothing
  else) — self-contained, with no demonstrated connection to SALPH.
- **`G-MSL-001` (`matrixsumlist`) is not shown to gate SALPH either way**,
  regardless of which `thispassword` role wins — it is DBBI's own separate
  adjacent instruction (Phase 371). This is a scope observation, not a
  relative-priority argument, and its own P0 rating (independent of SALPH)
  is unchanged.

**Frontier statement (corrected):** SALPH's literal hash-hint-as-password
reading is fully covered and negative. COSMIC contains no local
instruction. The role and operand of `thispassword` remain underdetermined;
`G-ARCH-001` is one possible dependency, not an established sole
bottleneck. `G-ARCH-001`'s priority is reverted to P1 (see
[GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md)).

**Next bounded audit:** discriminate Phase 101's three `thispassword`
roles using topology and solved-stage grammar, without generating
passwords. Only if `password_for_salph_blob` wins independently should
its possible operands — including, but not limited to, `G-ARCH-001` —
be ranked. **Run: see "Role discrimination result" (Phase 373) and
"Topology-identifiability result" (Phases 376-377) below.**

## Role discrimination result (updated 2026-08-22, Phase 373, corrected same-day)

The bounded audit above has been run and its original conclusion
retracted on review. `tools/gsmg/thispassword_role_topology_discrimination_audit.py`
scores the three roles on the seven frozen dimensions the user specified,
gated on a calibration step: the identical rule, unit-weighted, uniquely
recovers `linear_consumed` as the known topology of both Phase 3 and
Phase 3.2 (score 5 vs. 3 vs. -1) using only textual/structural evidence.
That gate passes — but it validates only "is this explicitly,
unambiguously consumed at all," a different, easier question than the
postpositive/ambiguous attachment `thispassword` actually poses. No
solved GSMG boundary in this project calibrates that specific attachment
question, so `CALIBRATION_ANALOG_AVAILABLE = False`.

The originally-published (disputed) modeling ranked `password_for_salph_blob`
first (score 3) by measuring adjacency/vocabulary against `hash_prefix` —
a separate instruction with its own already-scoped SHA operand (Phase
121/372) — rather than the actual SALPH blob, and by scoring
`faed_answer_is_password` as though it had to skip
`lastwordsbeforearchichoice` to bind directly on raw FAED, when its
natural graph is `FAED -> lastwordsbeforearchichoice -> answer ->
postpositive "thispassword" label`, requiring no skip at all. A corrected
modeling — fixing both defects, and no longer awarding message-8446's
order-only precedent asymmetrically to one role — instead ranks
`faed_answer_is_password` first (score 2), ahead of `password_for_salph_blob`
(-1) and `password_for_faed` (-2). **The two modelings disagree on the
winner.** That disagreement is itself the evidence that the original
ranking reflected disputed feature assignments, not independently
extracted structure — the script's self-test now asserts it as a checked
fact.

**Verdict: inconclusive/model-dependent.** `operand_ranking_licensed` is
`False`. No password, transform, or hash comparison was run in either
modeling, and no operand (including `G-ARCH-001`) is asserted as a
winner — the script's own self-test caps and checks every occurrence of
`G-ARCH-001` in its source to guard against reintroducing Phase 372's
retracted overclaim. Per the user's explicit stop rule, no new
"comparable" solved boundary was invented to force the calibration gate
closed for this specific ambiguity. Phase 101's three `thispassword`
roles remain unresolved, and operand ranking (in which `G-ARCH-001` would
enter as one candidate family among possibly others) is not licensed.

## Topology-identifiability result (2026-08-22, Phases 376-377, Phase 377 corrected same-day)

Phase 373 asked whether the three `thispassword` roles could be *scored*
apart; Phases 376-377 asked a different question — whether a direct
role-selecting witness for any of them exists anywhere in this project's
frozen primary evidence, under three declared tests, with no scoring and
no password generation. Step 1 (Phase 376, sound, unchanged) froze the
literal DOM stream (live-re-verified across all 5 Wayback captures,
2023-06-01 to 2026-04-05, zero content changes), the solved-stage
grammar (Phase 2/3/3.2), and the full creator reply record (148-row
mechanically-extracted universe, no manual topic selection). Step 2-5
(Phase 377) stated what observable fact each role would need and checked
for it, finding none: the literal stream does carry directional/deictic
*vocabulary* (`before`, `this`, `first`, `last` all appear in the decoded
instruction words), but that vocabulary is common to all three roles and
does not discriminate between them; a distinct, explicit *attachment*
marker is what's actually absent, checked as two kinds -- symbolic
markers (arrow, colon, equals sign) against the raw cipher stream, and
word-like markers (skip/label/attach) against the decoded instruction
words and legible segments specifically, not the raw stream. No solved
boundary exhibits the postpositive-label pattern
`faed_answer_is_password` would need as precedent. The creator account
never uses the word `thispassword` anywhere in the export under three
exact-token checks (full-export scan, role-specific co-occurrence, and
— narrower — a check that none of the 148 creator reply edges has a
parent message containing the term either); paraphrase-level discussion
remains unchecked. No hard contradiction was detected under these
declared checks.

**Bounded verdict: no direct witness found; underdetermined; parked.**
Phase 377's first write-up overclaimed this as "formally unidentifiable
... unresolvable by any model," which was corrected on review: the three
declared observables are possible sufficient witnesses, not proven
necessary conditions, so their absence shows no witness turned up under
these three tests — it does not show no witness could exist under some
other model built from the same frozen evidence. (The literal ordered
stream — FAED → instruction-1 → instruction-2 → hash_prefix → SALPH — is
itself asymmetric, and Phase 373's two disagreeing modelings already
demonstrated that different grammar models read that order differently.)
The result is consistent with, not stronger than, Phase 373's
inconclusive/model-dependent verdict. Per the user's Step 5 instruction,
internal phase churn on this specific tie should still stop until new
primary evidence appears (a newly surfaced creator statement naming
`thispassword`, a changed Wayback capture, or an authenticated
macro-chain source not previously in scope) — the practical stop rule
holds even though the stronger ontological claim does not.
