---
type: audit
status: live
result: mixed
disposition: structural-only
topics:
  - theory-registry
  - topology-audit
  - open-gap-registry
  - dbbi
  - faed
  - btcseed
---

# GSMG Scientific Theory Registry

**Purpose.** This project's default unit of work has been the single
transformation: "try cipher X with these variants against object Y." That
habit is not wrong — most of the durable facts in this repository (escape
pairs, letter-frequency skews, the `BTCSEED` decode, the solved-boundary
grammar) were found that way — but once a transformation-generating branch
saturates, as the BTCSEED/P91/Z branch did at Phase 408, "try another
variant" stops being informative. This registry reframes the DBBI/FAED/
`matrixsumlist`/BTCSEED frontier as a small set of **competing generative
theories** instead, per the user's 2026-08-25 proposal. Each transformation
this project runs against that frontier from here on should be justified as
an experiment that discriminates between two or more of the theories below,
not as a standalone candidate search.

This does not replace [GSMG_TOPOLOGY_AUDIT](GSMG_TOPOLOGY_AUDIT.md), which
already scores 9 topologies (T0-T8) for DBBI/FAED specifically on a
7-column structural rubric. That audit is this registry's primary evidence
source for T0-T2 below and is cited, not duplicated. This registry adds
three theories the Topology Audit does not frame explicitly (T3-T5, all
specific to the BTCSEED continuation and the solved-stage grammar) and
requires each entry to separate **facts used to construct** a theory from
**facts that could confirm** it — a distinction the Topology Audit's own
scoring columns do not enforce, and the distinction this registry exists to
enforce going forward.

**No new cipher execution accompanies this document.** Per the recommended
first deliverable, every claim below is sourced from phases already
recorded in `tools/gsmg/FINDINGS.md`, `doc/GSMG_OPEN_GAP_REGISTRY.md`, and
the two object pages ([DBBI](GSMG_OBJECT_DBBI.md), [FAED](GSMG_OBJECT_FAED.md)).
Per [[feedback_bounded_negative_verdict_discipline]], "no experiment
currently distinguishes these theories" is recorded as exactly that, not
escalated to "these theories are formally indistinguishable by any
possible future evidence."

## Field definitions

Each theory carries:

- **Authenticated inputs** — only objects with a pinned SHA-256/verified
  extraction (`tools/gsmg/data.py`, `cb_common.py`), not retyped or assumed.
- **Source-supported assumptions** — the specific inferential step the
  theory adds on top of the authenticated inputs.
- **Free parameters** — choices with no independent selector (operator,
  boundary, offset, mapping direction). Counted explicitly; more free
  parameters is a real cost, not a neutral modeling choice.
- **Facts used to construct** — observations that motivated inventing this
  theory. These are explicitly barred from double-counting as confirmation
  (framework rule 2).
- **New predictions** — an outcome the theory implies that was *not* among
  the facts used to construct it, ideally one that discriminates it from a
  rival theory.
- **Falsification conditions** — the specific result that would force the
  theory to lose standing.
- **Completed experiments** — phases that bear on this theory, whether or
  not they were originally framed as testing it.
- **Complexity cost** — a qualitative count of free parameters, for
  comparing theories that explain similar evidence.
- **Current status** — one of: *live* (untested predictions remain
  meaningful), *favored* (survives direct comparative tests better than
  rivals), *weakened* (a predicted discriminator failed, but not formally
  rejected), *stopped* (meets one of the framework's own stop conditions:
  failed prediction, no better than a simpler null, depends on an
  unselected convention, required adding parameters after seeing output,
  or is currently non-identifiable from available evidence and no further
  test is licensed), *blocked* (no path to a candidate without an unsourced
  parameter — a gap-registry state, not a verdict on the theory itself).

## Object definitions used throughout

| Symbol | Definition | Source |
|---|---|---|
| `DBBI` | 91-symbol raw string (alphabet a-i), SHA-256 `71fe4625...` | `data.py`, [OBJ-DBBI](GSMG_OBJECT_DBBI.md) |
| `FAED` | 570-symbol raw string (alphabet a-i), SHA-256 `066191b4...` | `data.py`, [OBJ-FAED](GSMG_OBJECT_FAED.md) |
| `decoded` | Bifid-decrypt of `FAED` (570 chars) using a keyed square built by de-duplicating `DBBI[:13]` (`dbbibfbhccbeg` -> `dbifhceg`) and then filling the remaining alphabet (`DBIFHCEGAKLMNOPQRSTUVWXYZ`), row-column order | Phase 386 |
| `P90` / `P91` | `decoded[7:97]` (90 chars) / `decoded[7:98]` (91 chars, header-aware, includes the unique `Z` at index 97) | Phase 386 / Phase 396 |
| `Q472` | `decoded[98:]` (472 chars, everything after `Z`) | Phase 397 |
| `M91` | `VALIDATION_ANSWER`, the authenticated Phase 3.2 plaintext (91 chars) | Phase 3.2 (solved) |
| `A26` | `DBBI - M91 mod 26`, Phase 75's `YOUWON`-bearing difference | Phase 75, reused Phase 401 |
| `CONTROL285` | `decoded[0::2]` (285 symbols, confirmed restricted to `{B,C,D,E}`) | Phase 405/406 |
| `matrixsumlist` | binary-ASCII-encoded instruction token, DBBI's sole adjacent instruction | Phase 101 |

## T0 — Statistical artifact

DBBI and FAED contain real, measurable non-uniform structure caused by
their construction (an intentional password/key or similar material forced
through a 9-symbol alphabet), but that structure does not encode a
`BTCSEED`-headed continuation or any other designed message.

- **Authenticated inputs:** `DBBI`, `FAED` (raw bytes, both pinned).
- **Source-supported assumptions:** the two streams' letter-frequency
  skew is real (chi-square rejects uniformity for both: DBBI
  `p≈2.89×10⁻⁶`, FAED `p≈6.38×10⁻⁷`) but does not itself imply intentional
  plaintext beyond that skew.
- **Free parameters:** none — this is the explanatory null for the
  observed skew itself; it adds no operator, boundary, or selector.
- **Facts used to construct:** the two chi-square results
  ([OBJ-DBBI](GSMG_OBJECT_DBBI.md), [OBJ-FAED](GSMG_OBJECT_FAED.md)) and
  Phase 386's confirmation that FAED's Bifid-decode alphabet skew
  (`B,C,D,E` covering 57% of output) is "a mechanical consequence of
  Bifid-recombining FAED's own 9-symbol source alphabet through a fixed
  grid," not an independent signal.
- **New predictions:** no independently-motivated period/block schedule
  besides the one used to discover `BTCSEED` should reproduce a
  recognizable header or checkpoint; downstream consumer tests (BIP39,
  BIP32, raw scalar, matrix, Base64) should find nothing above chance;
  community "coincidence" claims (e.g. `KMODEST`) should reduce to
  ordinary variance under a permutation null.
- **Falsification conditions:** an authenticated consumer (valid checksum,
  valid typed container, exact target-address hit) is found for any
  construction over `decoded` or its sub-streams.
- **Completed experiments:** Phase 386 (decode is mechanically real, but
  both concrete improbability arguments for treating `BTCSEED` as
  intentional fail direct recount — 97-not-91-character pre-`Z` segment,
  same-position match probability ~190× more likely than the "1 in 8
  billion" claim once real letter frequencies are used); Phase 408
  (`period_robust = False` — the `BTCSEED`/`Z@97`/alternation package
  exists only under the single period used to discover it); Phases
  397-407 (twelve distinct, frozen consumer families over `P90`/`P91`/
  `Q472`/`CONTROL285`/`decoded` — zero exact hits, and every
  statistically-scored family's real result sits at 6%-90% under its
  own multiset-preserving shuffle null, nowhere near the 0.5% promotion
  bound).
- **Complexity cost:** lowest of all six theories (zero free parameters).
- **Current status:** **favored.** No prediction has failed; twelve
  independent consumer families (Phases 397-407) and the period-robustness
  audit (Phase 408) all land exactly where T0 predicts they would.

## T1 — Independent consumers

DBBI and FAED are separate objects, each with its own (possibly still
undiscovered) consumer; they are not required to combine with each other.

- **Authenticated inputs:** the literal page segmentation
  (`page_structure_audit.segment_salphaseion()`, byte-verified against the
  live HTML capture): `DBBI [matrixsumlist] FAED [lastwordsbeforearchichoice] [thispassword]`.
- **Source-supported assumptions:** adjacency to an instruction token
  signals a candidate consumer for the *adjacent* object, not for the
  other raw stream (Phase 238's general page rule, reconfirmed
  stream-specific by Phase 371).
- **Free parameters:** none for the topology claim itself; each object's
  own downstream consumer (`matrixsumlist`'s 7 unbound fields, the
  Architect-choice role) still carries its own free parameters, tracked
  separately under T4/gap `G-ARCH-001`.
- **Facts used to construct:** Phase 371's direct test —
  `asymmetric_instruction_adjacency = True` (DBBI has 1 adjacent
  instruction, FAED has 2), `escape_pairs_independent = True` (DBBI's
  best fit is `{b,e}`, FAED's is `{g,i}`, computed independently),
  `either_stream_requires_the_other_as_input = False`.
- **New predictions:** no future evidence should require DBBI's raw
  content to appear inside FAED's consumer or vice versa; the two
  streams' escape pairs should remain independently motivated rather than
  converging under a shared selector.
- **Falsification conditions:** a page instruction or creator clue is
  found that explicitly binds one stream's content into the other's
  consumption, or a cross-stream statistical dependence (mutual
  information, shared boundary) is found significant against a
  permutation null.
- **Completed experiments:** Phase 371 (the direct topology test);
  Phases 271-321 (~45 combinatorial cross-stream models — transition
  matrices, mirror9 substitution, positional co-occurrence, GF(9)/
  base-27/base-81/FSM presentations, Bacon, Nihilist, Bellaso, ADFGVX,
  Gronsfeld — essentially all negative or null-like, none supplying a
  required joint construction).
- **Complexity cost:** low (no combinator invented).
- **Current status:** **favored**, jointly with T0. Corresponds to the
  Topology Audit's **T6** (Independent consumers), which the audit itself
  ranks second only to T8 (checkpoints, not operands) on real, non-inherited
  support.
- **Compatibility note:** T0 and T1 are not competitors. T0 is a claim
  about whether internal structure implies *any* designed continuation;
  T1 is a claim about whether the two streams must combine with *each
  other*. Both can be simultaneously true (as the evidence currently
  suggests) or T1 could hold while some other, not-yet-tested design
  exists within one stream alone.

## T2 — Joint Yin/Yang generator

DBBI and FAED are paired outputs of one generating mechanism (motivated by
the page's own `yinyang` framing), predicting a shared boundary,
complementary parameters, or measurable cross-stream dependence.

- **Authenticated inputs:** same raw streams as T0/T1; Phase 262's
  authenticated pixel-confirmed drop-cap positions (Chapter 2, positions
  48/50/55 of the *Cosmic Duality* book).
- **Source-supported assumptions:** the creator's own `yinyang` naming
  for this pairing (target of gap `G-YIN-001`) implies a literal joint
  construction, not merely a thematic label.
- **Free parameters:** which operator combines the streams (~45 tried
  across Phases 271-321); the scope of any shared-selector claim (e.g.
  "first three Chapter-2 drop caps" was never independently selected, per
  gap `G-YIN-001`'s own text).
- **Facts used to construct:** Phase 262's `(page - A1Z26(letter)) mod 26`
  over the three drop caps spelling `YIN` exactly.
- **New predictions:** a `YANG` counterpart under the same or a related
  construction; a shared boundary or complementary segmentation between
  DBBI and FAED; significant cross-stream mutual information.
- **Falsification conditions:** exhaustive search for a `YANG`
  counterpart fails; the ~45-model combinatorial sweep finds no required
  joint construction; geometric comparison finds no shared exceptional
  dimension.
- **Completed experiments:** Phase 262 itself (no `YANG` counterpart
  found, and nothing selects the three-drop-cap window as the input
  scope); Phase 240 (91=7×13 vs. 570=2×3×5×19 divisor-leg comparison —
  no shared factor structure; width 38 rejected as exceptional under 3
  null models across all 16 divisor widths); Phases 271-321 (~45 models,
  all negative, including several explicit cross-stream coupling
  presentations); Phase 371 (`escape_pairs_independent = True`,
  `either_stream_requires_the_other_as_input = False`).
- **Complexity cost:** highest of T0-T2 (an operator plus a scope
  selector, both unresolved).
- **Current status:** **stopped** — meets two of the framework's own stop
  conditions simultaneously: it performs no better than the simpler T0/T1
  null (identical downstream evidence, more free parameters), and its one
  piece of real supporting evidence (`YIN`) requires an unselected scope
  parameter that was never independently supplied. Corresponds to the
  Topology Audit's **T3** (DBBI/FAED symmetric combine), which that audit
  independently calls "most heavily tested, least surviving."

## T3 — BTCSEED typed stream

The full-570-character single-block Bifid result is the creator's intended
reading, and the material after the unique `Z` at index 97 (`Q472`, 472
characters) encodes a seed, container, or further instruction.

- **Authenticated inputs:** `FAED`, `DBBI` (for the keyed square), the
  Bifid decode itself (`decoded`, reproduced exactly by Phase 386's
  from-scratch reimplementation).
- **Source-supported assumptions:** that the single-570-character-block
  period is the intended block/period convention, and that a `BTCSEED`
  header specifically implies downstream Bitcoin-seed material rather
  than being a self-terminating recognition string.
- **Free parameters:** block/period choice (8 tested by Phase 408, only
  one preserves the checkpoint); consumer construction — mapping
  direction, bit order, byte-packing convention, window offset, and
  combinator, each separately enumerated across Phases 397-407.
- **Facts used to construct:** the `BTCSEED` prefix itself and the unique
  `Z` at index 97 — both of these are the *only* evidence that period 570
  is the right convention, and both were used to select it. Per this
  registry's own rule, they cannot also count as this theory's
  confirmation.
- **New predictions:** an authenticated downstream consumer — a valid
  BIP39 checksum with independent offset selection, a valid typed
  container (`Salted__`, DER, PSBT), a raw-scalar or BIP32-derived
  address match, or a structural match to the authenticated Stage-0
  matrix — should exist for some non-arbitrary construction of the
  post-header material.
- **Falsification conditions:** the checkpoint fails to reproduce under
  any independently-motivated period/block convention other than the one
  used to discover it (this is now observed, Phase 408); a broad,
  frozen family of natural consumer constructions is exhausted with zero
  hits and zero statistically significant results (also now observed,
  Phases 397-407).
- **Completed experiments:** Phase 386 (decode + improbability recheck);
  Phase 387 (`KMODEST` secondary checkpoint — real but not promoted; its
  own continuation to `BE MODEST` is explicitly post-hoc per its
  author); Phase 396 (`P91` header-aware isolation, no signal); Phases
  397-407 (twelve frozen consumer families: raw 59-byte control channel,
  BIP39 recalibration, 14×14 coordinate matrix, direct-scalar/BIP32 of
  `P90`/`P91`/`Q472`/full-stream, control/data digraph machines, raw
  BIP32 seed of control bytes, native data-rail identity, Base64 sextet
  channel, four natural-boundary 256-bit windows, `P91`-repeated-as-
  Vigenère-key — zero hits across roughly 400,000 cumulative address/
  oracle checks, and every statistically-scored family's shuffle-null
  p-value between 0.06 and 0.90); Phase 408 (period-robustness — only
  period 570 reproduces the `BTCSEED`/`Z@97`/alternation package;
  `period_robust = False`).
- **Complexity cost:** highest of all six theories — a period choice plus
  an unbounded family of consumer-construction parameters, the majority
  of which have now been tried and exhausted.
- **Current status:** **stopped**, per the framework's own third stop
  condition: this theory's central checkpoint depends on an unselected
  convention (Phase 408 shows the package does not survive any period
  other than the one used to discover it). Not formally rejected — period
  570 is a real, independently motivated boundary (the whole ciphertext
  length) and remains a legitimate checkpoint — but every tested
  prediction of an authenticated *consumer* has failed. This is the
  branch the user's own 2026-08-25 instruction paused after Phase 408,
  and this registry entry records the same disposition in the framework's
  vocabulary rather than reopening it.

## T4 — Matrix instruction pipeline

DBBI's 31-character first-piece-derived selection
(`ncsyangcahiriasogaleafayanestve`) is deliberately consumed by the
adjacent `matrixsumlist` instruction token.

- **Authenticated inputs:** the `matrixsumlist` token itself (binary-
  ASCII-decoded, verified, Phase 101); the 31-character DBBI selection
  (Phase 132's broad-word statistical control).
- **Source-supported assumptions:** that the selection is the intended
  operand for `matrixsumlist`, and that a primary source exists
  specifying matrix dimensions, traversal, value mapping, aggregation,
  and serialization.
- **Free parameters:** all 7/7 of gap `G-MSL-001`'s required fields —
  dimensions, placement, traversal, value mapping, aggregation,
  serialization, and target — remain unbound. The selection-to-operand
  binding is an additional unresolved premise of this theory.
- **Facts used to construct:** the DBBI/`matrixsumlist`/FAED page
  adjacency (Phase 101); the 31-character selection's own first-piece
  derivation.
- **New predictions:** a uniquely recoverable matrix schema that produces
  the authenticated Stage-0 matrix, a valid key, or a valid checksum.
- **Falsification conditions:** the only remaining unreviewed primary
  source is reviewed and found to carry no matrix/dimension/traversal
  content (this occurred — Phase 259 reviewed *Cosmic Duality* pages
  57-58, the book's only remaining uninspected primary source, and found
  ordinary narrative content, no operational numeric schema).
- **Completed experiments:** Phase 259 (book-page review, negative);
  Phase 399 (the closest executed proxy under this frontier — a frozen
  14×14 coordinate-matrix construction from the BTCSEED-branch decode,
  not literally `matrixsumlist`'s own operand, tested against the
  authenticated Stage-0 matrix: best candidate 107/196 cell agreement,
  47.06% of shuffles reach the same agreement, closed negative).
- **Complexity cost:** highest possible among the six (7 fully free
  parameters, none sourced).
- **Current status:** **blocked**, not stopped by a failed prediction —
  gap `G-MSL-001` is P0/`parked` in the Open Gap Registry precisely
  because the last known primary source was reviewed and found empty.
  This theory is non-identifiable from currently available evidence: no
  experiment can currently distinguish "the pipeline exists but is
  unsourced" from "the pipeline does not exist," and per the framework's
  own rule 5, inventing another transformation to force a decision here
  would not be informative. Revisit only if gap `G-MSL-001`'s closure
  condition (a new creator clue, recovered guide step, or pre-cutoff code
  artifact) is met.

## T5 — Solved-stage creator grammar

Unresolved boundaries reuse the same construction grammar (component
order, casing/whitespace rules, literal-prefix handling) and cryptographic
profile (KDF, cipher, padding) that the three *solved* boundaries
(Phase 2, Phase 3, Phase 3.2) demonstrably used.

- **Authenticated inputs:** the three solved AES boundaries' preimages
  and ciphertexts used by Phase 341's community-README calibration;
  independently for Phase 410, the Phase 2 and Phase 3 ciphertexts were
  extracted from the Wayback-authenticated SalPhaseIon HTML artifact
  (SHA-256 `647744a2...`), while Phase 3.2 used the project's pinned
  positive vector. Phase 410 keeps the community-authored reproduction
  commands separate from creator-authenticated ciphertext and derivation
  evidence.
- **Source-supported assumptions:** that a boundary-local instruction set
  (order, casing, whitespace, literal prefixes) plus a fixed
  cryptographic profile generalizes to boundaries whose plaintext is
  still unknown.
- **Free parameters:** none for the grammar/profile itself (both are
  *derived*, not invented — see below); applying either to a specific
  unresolved boundary still requires that boundary to locally supply its
  own component list, ordering instruction, and SHA/password referent,
  exactly as the solved boundaries did.
- **Facts used to construct:** the three solved boundaries' own literal
  page instructions and ciphertexts — but critically, this theory was
  *validated*, not merely constructed, via **leave-one-stage-out
  calibration**: Phase 341's frozen rule engine reconstructs each of the
  three known preimages at rank 1 using only that boundary's own local
  annotations, rejects 0/6 shuffled-component-order controls for both
  non-trivial boundaries, and shows no single global casing/whitespace
  rule covers more than one boundary at a time (each boundary needs a
  *different* one) — i.e. the grammar is falsifiable in exactly the way
  the framework's step 2 requires, and it survived.
- **New predictions:** any future genuinely-unresolved boundary that has
  all five grammar fields locally bound (authenticated components, order,
  casing/whitespace, SHA/password referent, expected output type) should
  decrypt under the identical cryptographic profile Phase 410 measured
  across all three solved boundaries: lowercase-hex `SHA256(preimage)`
  password, single-round legacy `EVP_BytesToKey`, AES-256-CBC, PKCS#7.
- **Falsification conditions:** a fourth genuinely solved boundary is
  found that uses a different KDF/cipher profile, or whose password does
  not follow the order/case/whitespace convention its own page
  instructions specify. No such boundary is currently known.
- **Completed experiments:** Phase 341 (grammar calibration — positive,
  explicitly scoped as calibration, not puzzle progress); Phase 372
  (SALPH eligibility audit — the `hash_prefix` branch's literal
  self-referential reading has all 5 grammar fields locally bound,
  generating an 18-candidate manifest, cross-checked as exact duplicates
  of Phase 0.1's own sweep, then widened to ECB/stream/Key Wrap: 0 hits;
  the `thispassword` branch's role remains three-way unreconciled per
  Phase 101/373/376-377, so the grammar has no second field set to apply
  there yet); Phase 410 (cryptographic-profile calibration — one
  consistent three-vector profile, all three solved boundaries share
  identical construction, 24-test control matrix with exactly 3
  successes, ranked non-deleting oracle guidance recorded).
- **Complexity cost:** lowest of the theories that make an active,
  ongoing prediction (T0 is lower still, but T0 makes no positive
  construction claim at all) — precisely because this theory was derived
  from held-out validation on real solved data rather than invented to
  fit DBBI/FAED.
- **Current status:** **validated methodological tool, no further
  eligible target.** This is less a rival explanation of DBBI/FAED than
  the calibration instrument the framework's own step 2 describes. It has
  been applied everywhere currently eligible (SALPH's literal branch) and
  found nothing further — not because the theory failed, but because
  every other candidate boundary (DBBI/FAED, `thispassword`'s SALPH role,
  COSMIC) is blocked by its own separate unresolved gap
  (`G-MSL-001`/`G-YIN-001`/`G-ESC-001`/`G-ARCH-001`), not by a limit of
  this grammar. It remains the frozen consumer profile any future
  candidate on a newly-eligible boundary should be checked against first,
  per Phase 410's own ranked-oracle-guidance deliverable.

## Cross-theory summary

| Theory | Free params | Status | Key discriminating result |
|---|---|---|---|
| T0 — Statistical artifact | 0 | favored | 12 consumer families (Phases 397-407), all negative at 6-90% shuffle-null p |
| T1 — Independent consumers | ~0 (topology itself) | favored | Phase 371: asymmetric adjacency, independent escape pairs, no forced cross-dependency |
| T2 — Joint Yin/Yang generator | operator + scope | stopped | Phase 262: no `YANG`; Phase 240: no shared geometric dimension; ~45 models negative |
| T3 — BTCSEED typed stream | period + consumer family | stopped | Phase 408: package survives only under the period used to discover it |
| T4 — Matrix instruction pipeline | 7/7 unbound | blocked | Phase 259: last primary source reviewed, empty |
| T5 — Solved-stage creator grammar | 0 (derived) | validated, no eligible target | Phase 341/410: leave-one-out calibration passes on all 3 solved boundaries |

T0, T1, and T5 are jointly consistent and currently the best-supported
reading of the frontier: the DBBI/FAED anomaly is real but does not
demonstrate a designed cross-stream or BTCSEED-continuation payload (T0),
the two streams are not shown to require each other (T1), and the one
theory validated by held-out prediction on real solved data (T5) has
already been applied everywhere it currently can be. T2-T4 are not
disproven in the sense of a certain negative — T2 and T3 fail their own
predicted discriminators under the framework's stop rules, and T4 is
blocked on missing primary evidence, not falsified.

## Reopen conditions (per theory)

- **T0/T1:** a demonstrated cross-stream statistical dependence, or an
  authenticated consumer for either stream individually.
- **T2:** a `YANG` counterpart to Phase 262's finding, or a page/creator
  source that independently selects a combining operator or scope.
- **T3:** an independently-motivated period (not `570`, not selected
  after seeing `BTCSEED`) that reproduces a comparable checkpoint, or any
  exact consumer hit within the already-tested families.
- **T4:** gap `G-MSL-001`'s closure condition — a new creator clue,
  recovered guide step, or pre-cutoff code artifact fixing the 7 unbound
  fields.
- **T5:** a fourth genuinely solved AES boundary (would strengthen, not
  reopen — this theory is not currently weakened); or a newly-eligible
  unresolved boundary gaining all 5 required local grammar fields (would
  license a fresh, separately-scoped candidate generation, not a change
  to this entry).

## Relationship to active-searching pause

Per the user's 2026-08-25 instruction (`GSMG_BRAINSTORM_BACKLOG_LEDGER.md`,
"Active searching paused"), this registry is documentation, not a new
search. None of the reopen conditions above are met by existing evidence,
so none license new candidate generation on their own. The next genuinely
scientific experiment this framework recommends — comparing generative
models of DBBI/FAED's full letter and transition distributions against
held-out positions — is deliberately not started here; it is a distinct,
separately-scoped deliverable the user would need to authorize.

## Related documents

- [GSMG Topology Audit](GSMG_TOPOLOGY_AUDIT.md) — the 9-topology structural
  scoring this registry's T0-T2 build on.
- [GSMG Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md) — `G-MSL-001`
  (T4), `G-ESC-001`/`G-YIN-001` (T1/T2), `G-ARCH-001` (T5's blocked
  `thispassword` branch).
- [GSMG Brainstorm Backlog Ledger](GSMG_BRAINSTORM_BACKLOG_LEDGER.md) —
  execution status of every phase cited above.
- [GSMG Solved-Vector Toolchain Provenance Audit](GSMG_SOLVED_VECTOR_TOOLCHAIN_PROVENANCE_AUDIT.md) —
  T5's cryptographic-profile calibration in full.
- [2026-08-25 - BTCSEED P91 Z Continuation Brainstorm](Brainstorms/2026-08-25%20-%20BTCSEED%20P91%20Z%20Continuation%20Brainstorm.md) —
  T3's full execution history (Phases 397-408).
