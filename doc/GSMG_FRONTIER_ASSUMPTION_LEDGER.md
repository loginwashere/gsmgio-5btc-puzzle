---
type: audit
status: live
topics:
  - frontier-assumption-ledger
  - topology-audit
---

# GSMG Frontier Assumption Ledger

**Purpose.** A phase closes one specific model under specific inputs,
topology, and oracle — it does not necessarily close the underlying puzzle
path. This ledger exists to make that distinction checkable per phase for
the unsolved frontier only (`DBBI`, `matrixsumlist`, `FAED`,
`lastwordsbeforearchichoice`, `thispassword`, `SALPH`/SalPhaseIon, `anstoo`,
`COSMIC`/Cosmic Duality, `P32TRAILING`, and the Architect/`BUT`/`HYE`/`BYE`/
`CIAO` transition). It is scoped to phases that make a real topology claim —
an assertion, test, or rejection of how two or more of these objects
connect — not every phase that merely mentions one of these tokens. A phase
becomes reopenable only when one of its `load_bearing_assumptions` fields
materially changes (new evidence, corrected oracle, corrected candidate
set); heading/prose rewording alone does not reopen anything.

**Companion document:** [GSMG_TOPOLOGY_AUDIT](GSMG_TOPOLOGY_AUDIT.md) uses
this ledger's `assumed_edges`/`topology_stance` fields as its primary input
and scores eight candidate topologies plus an explicit null topology against
it.

**Schema** (fields left blank/`—` when the phase's own method makes them
not applicable — e.g. a structural/no-oracle audit has no
`candidate_set_digest`; inventing one would misrepresent the phase):

```yaml
phase:
claim_tested:
authenticated_inputs:
assumed_edges:
target_object:
candidate_set:
candidate_set_digest:
crypto_profiles:
oracle_capabilities:
output_detector:
coverage_scope: exact | sentinel | partial | full
result:
load_bearing_assumptions:
later_changes:
current_disposition:
reopen_condition:
```

## Individually load-bearing phases

```yaml
phase: 11
claim_tested: prior SHA-256 command-state chained with SHA256(answer) as the SALPH password
authenticated_inputs: 4 README-documented prior command hashes
assumed_edges: SALPH's password derives from a linear hash chain continuing Phase 2/3/3.2
target_object: SALPH
candidate_set: 11,899 candidates (grammar-generated)
candidate_set_digest: "sha256 425860df33d961d39c2116b5ac477249ceb043ff1ac744e130da55a2b13106ae (1,427,880 no-newline materials, pinned in tools/gsmg/hash_duality_corrected_oracle_backfill.py's EXPECTED_MATERIAL_DIGEST_SHA256; the 4,283,640-material with-newline family is this digest's own materials plus the 2,855,760-material Stage-3 delta, not separately digested)"
crypto_profiles: "the six legacy KDF_VARIANTS combos only -- (sha256,32)/(md5,32)/(sha1,32)/(sha256,16)/(md5,16)/(sha1,16), i.e. SHA-256/MD5/SHA-1 x AES-256/AES-128-CBC. NOT EXTENDED_CIPHER_VARIANTS (AES-192, 3DES, PBKDF2) or the AES Key Wrap oracle -- those remain Stage 4, not run"
oracle_capabilities: pre-Phase-78 printable-gated oracle (corrected rerun: Phase 374, 2026-08-22)
output_detector: printable-ratio gate (Phase 374's rerun uses the current two-tier z-score gate)
coverage_scope: exact
result: negative
load_bearing_assumptions: chain-continuation edge is inherited, not independently proven -- Phase 374's rerun closes ORACLE coverage only, per its own topology caveat; it does not touch this row's `assumed_edges`
later_changes: "Phase 374 (2026-08-22): the flagged-but-unactioned oracle rerun below is now done. Regenerated and digested the frozen 11,899-candidate/4-prior-hash/1,427,880-material manifest (unchanged since Phase 11), reran under the CURRENT CBC oracle (KDF_VARIANTS, pinned explicitly) across all 4 current default blobs (SALPH/COSMIC/P32TRAILING/URLBLOB -- P32TRAILING and URLBLOB post-date Phase 11's original run) -- 1,427,880 attempts, 0 hits. Separately found and closed a second discrepancy: Phase 11's write-up claimed LF/CRLF forms were tested, but the recorded count exactly matched newline_variants=False; the missing delta (2,855,760 materials) was run separately under the same corrected oracle -- 0 hits. Combined 4,283,640 attempts, 0 hits. ECB/stream/AES-Key-Wrap widening (~480M+ nominal combinations) explicitly NOT run -- separately costed, not preregistered"
current_disposition: "closed negative; oracle coverage corrected and widened (Phase 374). The chain-continuation topology assumption itself remains unproven and unresolved (Phases 369-373)"
reopen_condition: a source that selects a specific chain-continuation construction, or a separately preregistered ECB/stream/AES-Key-Wrap widening of this same candidate family (Stage 4, not yet run)
```

```yaml
phase: 12
claim_tested: reverse-chain candidate -> decode FAED -> derive board -> decode DBBI -> AES; plus content-independent raw folding
authenticated_inputs: escape pairs known at the time
assumed_edges: DBBI/FAED combine (topology 3); FAED can feed DBBI (topology 5-shaped)
target_object: SALPH / COSMIC / P32TRAILING / URLBLOB
candidate_set: 1.77M attempts
candidate_set_digest: —
crypto_profiles: AES-CBC
oracle_capabilities: pre-Phase-78 printable-gated oracle
output_detector: printable-ratio gate
coverage_scope: exact
result: negative
load_bearing_assumptions: assumes both the combine edge and a FAED->DBBI feed direction simultaneously; neither independently established
later_changes: none recorded
current_disposition: closed negative
reopen_condition: independent evidence for either edge
```

```yaml
phase: 33
claim_tested: Architect-choice extraction (BUT/HYE -> EOL), rail-family literal forms
authenticated_inputs: BOTH/ULTIMATELY/THE position selection
assumed_edges: none new
target_object: SALPH / COSMIC / P32TRAILING / URLBLOB
candidate_set: 216 CBC + 306 Key Wrap forms
candidate_set_digest: —
crypto_profiles: AES-CBC, AES Key Wrap
oracle_capabilities: current at time of run
output_detector: printable-ratio / structural
coverage_scope: exact
result: negative
load_bearing_assumptions: weakly supports topology 8 (checkpoint, not operand) by elimination
later_changes: none recorded
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: 96
claim_tested: case-sensitive SalPhaseIon -> SalVATIon -> SALVATION title rebus as a direct password
authenticated_inputs: HTML heading exact case; msg 8446 stream
assumed_edges: none — explicitly flags the reading family as post-hoc-motivated, not assumed
target_object: SALPH / COSMIC / P32TRAILING / URLBLOB
candidate_set: 117 keystrings
candidate_set_digest: —
crypto_profiles: AES-CBC
oracle_capabilities: current at time of run
output_detector: printable-ratio / structural
coverage_scope: exact
result: negative
load_bearing_assumptions: none — this phase is evidence, not an assumption; frames SALVATION as an unconsumed recognition state (supports topology 8)
later_changes: none recorded
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: 104
claim_tested: does one conserved dual-pole model (yellow/blue, row1/row2, DBBI/FAED, half/better-half, etc.) survive across 7 "dual" artifact pairs?
authenticated_inputs: yellow-one prime, matrix rows, BUT/HYE, escape pairs
assumed_edges: explicitly rejects bridging "half and better half" to SalPhaseIon/Cosmic textarea pairing (an already-falsified Phase 54 reading)
target_object: — (structural audit, no oracle)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: structural comparison across 7 artifact pairs
coverage_scope: full
result: negative — no conserved 2-pole model
load_bearing_assumptions: establishes DBBI's real best-fit escape pair is {b,e} (direct); FAED's mirror-predicted pair {h,e} does NOT match FAED's own real best fit {g,i} — origin of the G-ESC-001 unreconciled-pair problem
later_changes: none recorded
current_disposition: closed negative; escape-pair asymmetry remains open (G-ESC-001)
reopen_condition: a source reconciling {g,i} vs {h,e}
```

```yaml
phase: 112
claim_tested: code-index-of-coincidence as a calibrated partial escape-pair oracle (review correction of Phase 106)
authenticated_inputs: —
assumed_edges: none
target_object: FAED escape pair {g,i}
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: code-IC ranking, not a decrypt oracle
output_detector: IC ranking
coverage_scope: full
result: positive — {g,i} ranks 1st under this partial oracle
load_bearing_assumptions: supports FAED's own-best-fit differing from the Architect-mirror-predicted pair
later_changes: supersedes Phase 106's inverted framing (same-day correction)
current_disposition: positive partial oracle, retained
reopen_condition: —
```

```yaml
phase: 123
claim_tested: FAED {g,i} VIC-style chain-addition reopening
authenticated_inputs: {g,i} pair
assumed_edges: DBBI/FAED combine via VIC-style chain-addition (topology 3)
target_object: SALPH / COSMIC / P32TRAILING / URLBLOB
candidate_set: full scope (VIC chain-addition parameter space)
candidate_set_digest: —
crypto_profiles: AES-CBC
oracle_capabilities: current at time of run
output_detector: printable-ratio / structural
coverage_scope: full
result: negative
load_bearing_assumptions: assumes topology 3 (symmetric combine) without independently testing it
later_changes: none recorded
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: "217/223"
claim_tested: does the minimal creator-macro chain (six-digit prime) reach `yinyang`, and separately, does the 31-char DBBI selection reach it as matrixsumlist's operand?
authenticated_inputs: msg 8446 macro prefix; yellow/blue prime
assumed_edges: Phase 217 originally merged two distinct routes into one chain (later found circular); Phase 223 (same day) corrects this
target_object: — (structural, no oracle)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: structural / mirror9 check
coverage_scope: full
result: "217: positive-then-self-corrected; 223: negative correction"
load_bearing_assumptions: rejects the DBBI-selection-as-matrixsumlist-operand version of the chain (contradicts topology 1); demotes BUT/HYE from \"reaches yinyang\" to \"recognition checkpoint only\" (supports topology 8)
later_changes: "Phase 223 corrects Phase 217's own same-day circular H|YE|BUT construction"
current_disposition: closed; BUT/HYE checkpoint status stands
reopen_condition: —
```

```yaml
phase: 218
claim_tested: what is the actual, measured page order of the frontier objects?
authenticated_inputs: byte-verified page order via page_structure_audit.py
assumed_edges: none for the order fact itself — this is the one edge in the whole ledger that is MEASURED, not assumed
target_object: — (structural fact)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: DOM/byte-order scan
coverage_scope: full
result: "positive (order fact): dbbi -> [matrixsumlist] -> faed -> [lastwordsbeforearchichoice] -> [thispassword] -> [sha256 hint] -> SALPH-prefix -> [enter] -> SALPH-suffix -> [sha256+anstoo]"
load_bearing_assumptions: explicitly does NOT claim this order implies a combining operation — quotes its own text, "neither role is upgraded by elimination of the others"
later_changes: none recorded
current_disposition: retained as the one authenticated ordering fact; not promoted to a topology claim
reopen_condition: n/a (already the strongest fact available on ordering)
```

```yaml
phase: 220
claim_tested: does HTML presentation (spans/CSS/newlines) bind DBBI/FAED into any grid or pairing?
authenticated_inputs: full HTML/CSS capture, SHA-pinned
assumed_edges: none — direct test of a presentational-binding assumption
target_object: — (structural)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: DOM/CSS structural comparison
coverage_scope: full
result: negative
load_bearing_assumptions: directly undercuts any topology relying on presentational/DOM binding between DBBI/FAED; Cosmic Duality's authored 28x64 fixed-line textarea vs. SalPhaseIon's zero authored structure is a real internal control against symmetric treatment
later_changes: none recorded
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: 224
claim_tested: does the creator's "it's the next phase" mean SALPH's password applies cross-textarea to COSMIC?
authenticated_inputs: single-textarea structure; 13-message corpus census
assumed_edges: tests (and rejects) a DOM-order-based handoff mechanism specifically
target_object: SALPH self vs. COSMIC
candidate_set: n/a (corpus census, not a cipher sweep)
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: corpus census
coverage_scope: full
result: negative (for the tested DOM-order justification)
load_bearing_assumptions: "explicitly leaves the SALPH-self-contained reading as \"nearer/unexplained\" — i.e. still the standing default, just not proven to hand off to COSMIC"
later_changes: none recorded
current_disposition: closed negative for the specific tested mechanism; SALPH-self-first remains the unfalsified default
reopen_condition: a source that actually specifies a handoff mechanism (untested ones remain open)
```

```yaml
phase: 225
claim_tested: does the creator's own YING/YANG typo spelling align with FAED's real best-fit {g,i} pair?
authenticated_inputs: 2 creator messages (9599, 39224)
assumed_edges: none
target_object: FAED escape pair
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: lexical match
coverage_scope: full
result: "positive-but-unauthorized: exact, unusually target-specific match, but fails the authorship gate (msg 1806 explicitly says no typo clues)"
load_bearing_assumptions: near-miss on G-ESC-001, explicitly not promoted per this project's authorship-gate discipline
later_changes: none recorded
current_disposition: parked, flagged not promoted
reopen_condition: creator lifts or clarifies the no-typo-clues statement
```

```yaml
phase: 238
claim_tested: does any of 6 candidate house-style rules (uniform prefix/postfix, between-means-join, transport-fixes-role, nearest-neighbor operand, SHA bracket, +1 more) hold across all 6 instruction slots on the page?
authenticated_inputs: full page segmentation
assumed_edges: this phase directly TESTS the "adjacency implies operand" assumption other phases inherit
target_object: — (structural, no oracle)
candidate_set: 6 rules x 6 instruction slots
candidate_set_digest: —
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: rule-survival check per slot
coverage_scope: full
result: "negative — zero of six rules survive across all slots"
load_bearing_assumptions: "the single strongest falsification in this ledger: it demonstrates that assuming a linear/adjacent chain (topology 1) or any adjacency-implies-operand rule is unsupported by the page's own actual grammar, not merely untested"
later_changes: none recorded
current_disposition: closed negative; treated as load-bearing evidence against topology 1's justification
reopen_condition: —
```

```yaml
phase: "243/244"
claim_tested: is there a DBBI/FAED page-boundary selector (markup/CSS/JS)? Is the page stable across archive captures?
authenticated_inputs: full DOM; 5 Wayback captures, byte-identical
assumed_edges: none
target_object: FAED escape pair selection
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: DOM/CSS/JS structural scan; cross-capture byte comparison
coverage_scope: full
result: negative — no selector found; page stable across all captures
load_bearing_assumptions: closes the page-boundary branch of G-ESC-001
later_changes: none recorded
current_disposition: closed negative
reopen_condition: a new archive capture with a different main-document hash
```

```yaml
phase: "247/248"
claim_tested: Architect beginnings/endings/mirror selector, tested against 88 creator media records and precedent-transfer language
authenticated_inputs: 88 creator media records
assumed_edges: none
target_object: G-ARCH-001 operation selection
candidate_set: 88 media records + 5 brainstorm lanes
candidate_set_digest: —
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: corpus/media review
coverage_scope: full
result: negative — no operation selected
load_bearing_assumptions: supports topology 8 by elimination — no creator source has ever selected an operand-transforming operation for this checkpoint
later_changes: none recorded
current_disposition: closed negative; G-ARCH-001 parked
reopen_condition: new Telegram export, creator-media payload, or corpus
```

```yaml
phase: 259
claim_tested: does the Cosmic Duality book's photographed pp.57-58 (the last uninspected primary source) supply matrixsumlist's dimensions/traversal/aggregation?
authenticated_inputs: photographed physical book pages
assumed_edges: none
target_object: matrixsumlist (G-MSL-001)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: manual transcription review
coverage_scope: full
result: negative — no matrix/dimension/traversal content
load_bearing_assumptions: all 7/7 G-MSL-001 fields remain unbound after this, the last known uninspected primary source
later_changes: none recorded
current_disposition: closed negative; G-MSL-001 parked, source-exhausted
reopen_condition: a new primary source
```

```yaml
phase: 262
claim_tested: does (page - A1Z26(letter)) mod 26 over Chapter 2's first 3 yin-yang drop caps spell YIN?
authenticated_inputs: pixel-confirmed drop-cap letters (W/48, O/50, O/55)
assumed_edges: "\"first 3 of Chapter 2\" is an unselected scope choice — not itself justified by any clue"
target_object: G-YIN-001 (DBBI/FAED -> yinyang operator)
candidate_set: bounded (3 drop caps)
candidate_set_digest: —
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: exact string match ("YIN")
coverage_scope: bounded
result: positive lead, no YANG counterpart, not promoted
load_bearing_assumptions: real near-miss on G-YIN-001; explicitly a bounded lead, not a mechanism — scope selection itself is the missing justification
later_changes: none recorded
current_disposition: parked, not promoted
reopen_condition: a source that selects "first 3 of Chapter 2" as the correct scope, or a genuine YANG counterpart
```

```yaml
phase: 289
claim_tested: are DBBI/FAED authenticated-string selectors (an index into some other already-authenticated string), rather than direct cipher material?
authenticated_inputs: —
assumed_edges: still assumes SOME kind of consumption relationship, but is the closest existing phase to testing topology 6 (independent consumers) and gestures at the null topology in passing
target_object: 20 candidate output strings
candidate_set: 20 outputs
candidate_set_digest: —
crypto_profiles: n/a (selection model, not cipher)
oracle_capabilities: n/a
output_detector: string-selection validity check
coverage_scope: full
result: negative
load_bearing_assumptions: "explicitly states DBBI/FAED-jointly is only the next-nearest alternative \"if yin-yang names a relationship between the two streams rather than a single decode\" -- the closest any phase gets to stating the null topology as a live alternative, without actually testing it as a first-class hypothesis"
later_changes: none recorded
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: 291
claim_tested: bounded primary-source delta search (Hosterjack fork re-pull + fresh Wayback CDX query) for any new DBBI/FAED evidence
authenticated_inputs: fork commit log; live CDX query
assumed_edges: none
target_object: G-ESC-001 / G-YIN-001
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: source-diff review
coverage_scope: full
result: "negative — no new source since prior check"
load_bearing_assumptions: "confirms the gap is source-starvation, not under-testing of known material -- matches this project's own repeated meta-conclusion"
later_changes: none recorded
current_disposition: parked; branch formally closed pending new source
reopen_condition: new Hosterjack fork content or new archive capture
```

```yaml
phase: 341
claim_tested: does a frozen construction-rule registry (order, no-separator concatenation, per-component case/whitespace mode, literal-prefix handling), reverse-engineered from the 3 solved AES boundaries, reproduce all 3 exact preimages under leave-one-out?
authenticated_inputs: the 3 solved AES boundaries (Phase 2, 3, 3.2)
assumed_edges: none — this is calibration on already-solved ground truth
target_object: n/a (calibration only; no unresolved blob queried)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: AES-CBC (reconstruction, not a sweep)
oracle_capabilities: n/a
output_detector: exact preimage match
coverage_scope: full (3/3 solved boundaries)
result: "positive — all 3 exact preimages recovered, 6 near-miss alternatives per non-trivial boundary correctly rejected"
load_bearing_assumptions: "validated backward only at the time this phase ran; forward transfer to P32TRAILING was then executed by Phase 370 (see below) -- 0 genuinely new candidates, subsumed by Phase 270"
later_changes: "forward-transfer reopen trigger closed by Phase 370"
current_disposition: "positive calibration result, retained; forward transfer complete (Phase 370), no further application pending"
reopen_condition: a new primary source that supplies an unresolved boundary (SALPH/COSMIC/URLBLOB) with its own local construction instruction eligible under this grammar
```

```yaml
phase: 366
claim_tested: does the "in front of your eyes" chronology match a creator-confirmed 31-character transition?
authenticated_inputs: message chronology facts
assumed_edges: assumes a specific chronological reading of the transition claim
target_object: — (chronology check)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: chronology comparison
coverage_scope: full
result: rejected
load_bearing_assumptions: directly contradicts topology 1 (the specific transition-as-chain-link reading tested)
later_changes: none recorded
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: 367
claim_tested: does the repository state praised by the creator (msg 8352), plus the `theory of everything` clue, plus the 2026 `tiny hint`, form a dependency closure with exactly one missing object?
authenticated_inputs: frozen commit fb92dd1, 7 pinned git blob IDs
assumed_edges: none — direct closure test
target_object: — (closure test over 5 payload objects)
candidate_set: n/a
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: dependency-closure count
coverage_scope: full
result: "rejected — 5 open payloads (P32TRAILING, DBBI, FAED, SALPH, COSMIC) across 3 clusters, not 1"
load_bearing_assumptions: directly falsifies any "one missing piece" framing of the current frontier — the most recent and most direct test of that specific hope
later_changes: none recorded
current_disposition: closed negative; tiny hint parked as directional/non-operational
reopen_condition: pre-edit message recovery, creator clarification, or a new primary artifact that independently selects an operation
```

```yaml
phase: 368
claim_tested: does YOUWON/YOUWONX (Phase 75's DBBI-row-derived candidates) open any tracked blob under the current, corrected (post-Phase-78) oracle across every established cipher family?
authenticated_inputs: DBBI 13x7 row geometry (Phase 75)
assumed_edges: none — pure oracle-coverage correction, no new topology claim
target_object: SALPH / COSMIC / P32TRAILING / URLBLOB
candidate_set: 18 unique passphrase forms
candidate_set_digest: —
crypto_profiles: AES-CBC (24 variants), AES-ECB (12), stream (36), AES Key Wrap (12 KDF)
oracle_capabilities: current, post-Phase-78 binary-safe oracle
output_detector: structural-binary-plaintext / printable-ratio gate
coverage_scope: exact
result: negative — 0 hits across 8,640 effective operations
load_bearing_assumptions: none
later_changes: closes GSMG_PHASE_VALIDATION_LOGIC_CONSISTENCY_AUDIT.md Finding 2
current_disposition: closed negative
reopen_condition: —
```

```yaml
phase: 370
claim_tested: does Phase 341's solved-boundary grammar, transferred forward to P32TRAILING, generate any genuinely new candidate?
authenticated_inputs: P32TRAILING's literal position (end of the solved Phase 3.2 plaintext); the re-derived, README-verified 3.2.1/3.2.2 sibling answers
assumed_edges: none -- explicitly checked (not assumed) whether P32TRAILING carries a local annotation before applying any grammar axis
target_object: P32TRAILING
candidate_set: 4 password materials (2 base strings x raw/sha256-hex)
candidate_set_digest: —
crypto_profiles: AES-CBC, established OpenSSL KDF profile matching the solved parent stage
oracle_capabilities: exact structural (80-byte envelope, 2^-128 false-positive two-key/full-padding-block detector) -- same oracle as Phase 270
output_detector: exact full-padding-block structural match
coverage_scope: exact
result: "0 genuinely new candidates -- all 4 are exact byte-string duplicates of Phase 270's own already-tested materials; 0 oracle queries made"
load_bearing_assumptions: none remaining -- P32TRAILING has no local case/whitespace/prefix annotation (byte-verified: bare \r\n\r\n separator), so the grammar's non-order axes are inapplicable here
later_changes: closes Phase 341's own reopen condition
current_disposition: closed; forward transfer complete, subsumed by Phase 270
reopen_condition: a new primary source that supplies P32TRAILING with its own local construction instruction
```

```yaml
phase: 371
claim_tested: "for DBBI and FAED separately: what local instruction consumes it, what output type does that predict, what authenticated target accepts that type -- testing topology T0/T6 directly"
authenticated_inputs: byte-verified literal page segmentation (page_structure_audit.segment_salphaseion); each stream's own code-IC best-fit escape pair (checkerboard_code_ic_oracle.apply_to_real_data)
assumed_edges: none -- this phase exists specifically to stop assuming an edge and test for one
target_object: DBBI, FAED (each independently)
candidate_set: n/a (structural audit, no oracle)
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: structural adjacency + substring-embedding check
coverage_scope: full
result: "inconclusive by design (checkpoint/no-consumer was an explicitly permitted answer): DBBI has 1 adjacent instruction (matrixsumlist, unexecutable per G-MSL-001); FAED has 2 (lastwordsbeforearchichoice/thispassword, pointing at G-ARCH-001, not demonstrated to consume FAED); escape pairs differ ({b,e} vs {g,i}); no evidence either stream requires the other as input"
load_bearing_assumptions: "directly falsifies the IMPLICIT premise behind topology T3 (symmetric combine) at the page-structure level -- DBBI and FAED are not treated symmetrically by the page's own adjacency structure"
later_changes: sharpens G-YIN-001 to record this as executed, not merely recommended
current_disposition: closed; T0/T6 tested, inconclusive as designed, no new combinator search warranted
reopen_condition: a new primary source, or a demonstrated embedding of one stream's content in the other's adjacent instruction
```

```yaml
phase: 372
claim_tested: "are SALPH and COSMIC, inspected separately, Phase-341 grammar-eligible (5/5 required fields locally bound)? Generate candidates only where eligible; diff before querying"
authenticated_inputs: byte-verified literal page segmentation (page_structure_audit); Cosmic Duality textarea byte-identity to COSMIC_BLOB_B64
assumed_edges: none -- DBBI/FAED/BUT-HYE/31-char selection explicitly treated as checkpoints, not re-derived
target_object: SALPH (two branches), COSMIC
candidate_set: 18 password materials (SALPH hash_prefix branch only; thispassword branch generates none, ineligible)
candidate_set_digest: —
crypto_profiles: AES-CBC (24 variants), AES-ECB (12), stream (36), AES Key Wrap (12 KDF)
oracle_capabilities: current, post-Phase-78 oracle, all 4 blobs
output_detector: structural-binary-plaintext / printable-ratio gate
coverage_scope: exact (hash_prefix branch); n/a (thispassword branch, ineligible; COSMIC, ineligible)
result: "hash_prefix branch's literal self-referential reading: 0 genuinely new candidates, 0 hits across widened oracle (broader SHA-operand readings already closed by Phase 121). thispassword branch: no executable candidate, ROLE unresolved (Phase 101's 3 unreconciled readings), not a single named component. COSMIC: 0/5 fields bound, self-contained, no demonstrated connection"
load_bearing_assumptions: "corrected same-day: the original version asserted thispassword requires G-ARCH-001's specific output as its sole component -- Phase 101 retained 3 unreconciled roles, only one of which even targets SALPH, and G-ARCH-001 is one candidate reading of that role's operand, not a proven equivalence"
later_changes: "original version raised G-ARCH-001 P1->P0 and demoted G-MSL-001 P0->P1 on the retracted 'sole bottleneck' claim -- both reverted same-day (G-ARCH-001 back to P1, G-MSL-001 back to P0)"
current_disposition: "closed; corrected, softened frontier statement adopted in GSMG_TOPOLOGY_AUDIT.md. The bounded audit this phase called for (discriminate Phase 101's 3 thispassword roles via topology/solved-stage grammar, no password generation) was run by Phase 373 (see block below), then Phases 376-377 (Phase 377 corrected twice, same day; not separately tabulated in this ledger -- see GSMG_TOPOLOGY_AUDIT.md's \"Topology-identifiability result\" section). Bounded verdict: no direct role-selecting witness found under three declared primary-evidence tests, no hard contradiction detected under those checks, role remains underdetermined and parked"
reopen_condition: "G-ARCH-001 closing (creator-selected Architect operation found) makes the thispassword branch eligible; a new primary source for COSMIC's own object would reopen its eligibility check; new primary evidence (creator statement naming thispassword, changed Wayback capture, or a new macro-chain source) would reopen the role-discrimination question itself"
```

```yaml
phase: 373
claim_tested: "discriminate Phase 101's three thispassword roles (password_for_faed, faed_answer_is_password, password_for_salph_blob) by scoring dataflow topology on 7 frozen dimensions, gated on a calibration step against the known solved-boundary topology"
authenticated_inputs: byte-verified literal page segmentation (page_structure_audit.segment_salphaseion, content-order distances computed live, not hardcoded); Phase 3/Phase 3.2 known construction rules (solved_boundary_rule_audit.py) as calibration ground truth; Phase 121's creator-authenticated message-8446 order chain as leave-one-out precedent
assumed_edges: none -- the 3 roles are Phase 101's own unresolved axis, not re-derived; scoring inputs are textual/structural only, never a hash-match outcome (calibration would be circular otherwise)
target_object: the password_role axis of thispassword/lastwordsbeforearchichoice (Phase 101's salphaseion_operand_binding_audit.py)
candidate_set: n/a (structural scoring audit, no oracle, no password generated)
candidate_set_digest: n/a
crypto_profiles: n/a
oracle_capabilities: n/a
output_detector: n/a
coverage_scope: full (all 3 roles scored; calibration run first as a gate)
result: "corrected same-day: original write-up reported password_for_salph_blob winning uniquely (score 3 vs -1 vs -2). Retracted -- that scoring measured password_for_salph_blob against hash_prefix (a separate, already-scoped SHA instruction, Phase 121/372) rather than the actual SALPH blob, and scored faed_answer_is_password as needing to skip lastwordsbeforearchichoice to bind on raw FAED when its natural graph labels that instruction's own output directly, no skip required. Corrected modeling instead ranks faed_answer_is_password first (score 2), ahead of password_for_salph_blob (-1) and password_for_faed (-2, unchanged) -- the two modelings disagree on the winner, now an asserted checked fact in self_test()"
load_bearing_assumptions: "CALIBRATION_ANALOG_AVAILABLE=False (asserted): Phase 3/Phase 3.2 calibrate only explicit-consumption-vs-checkpoint, not the postpositive/ambiguous attachment thispassword actually poses -- no solved GSMG boundary calibrates that specific structure, so operand_ranking_licensed is False unconditionally regardless of any single modeling's raw score"
later_changes: "original version's 'licenses operand ranking as a separate follow-up' claim is retracted; operand_ranking_licensed forced False; doc/GSMG_OPEN_GAP_REGISTRY.md's 'thispassword structurally targets SALPH' statement removed"
current_disposition: "closed; inconclusive/model-dependent. Phase 101's three thispassword roles remain unresolved. Per the user's explicit stop rule, no new 'comparable' solved boundary was invented to force the calibration gate closed for this specific ambiguity"
reopen_condition: a new primary source that changes the page's literal segmentation, supplies a direct creator statement about thispassword's role specifically, or a genuine solved-boundary analog for postpositive/ambiguous instruction attachment is identified to properly calibrate this distinction
```

## Bulk block: Phases 272-321 — DBBI/FAED direct combinator sweep (~45 phases)

Nearly all of these **structurally assume topology 3** (DBBI and FAED are
meant to combine into one joint object) and then test one specific
combining operator: hex-nibble packing (272), decimal transport inverse
(273), 6-lane geometry (274), 9x9 transition matrices (275), GF(9)/
recurrence (276), base-27 (277), move-to-front (278), base-81 digraph
(279), factoradic/Lehmer (280), crib-solved recurrences (281), probability
model/arithmetic coding (282), `anstoo`/ANS feasibility (283), finite-state
machine (284), sequence alignment (285), audio/spectrogram render (286),
matrix-barcode render (287), continued fractions (288), authenticated-
string selectors (289 — tabulated above, closest to the null topology),
canonical-sentinel backfill (290), primary-source delta (291 — tabulated
above), fork-surfaced residual leads (292), `mirror9` direct substitution
(293), colophon/copyright IDs (294), Phase 3.2.1 reversal (295), joint
positional co-occurrence (297), Bacon cipher (309), Nihilist additive-key
(310), Cosmic Duality running key (311), Bellaso reciprocal (312), raw
base-9 bignums (318), spiral/boustrophedon transposition (319), Gronsfeld/
progressive shift (320), ADFGVX transposition (321).

```yaml
phase: "272-321 (bulk, ~45 phases)"
claim_tested: "~45 distinct operators for combining DBBI and FAED into one joint decode object"
authenticated_inputs: DBBI, FAED raw streams; known escape-pair candidates
assumed_edges: "topology 3 (DBBI/FAED combine) assumed by construction in every one of these phases -- none tests whether combination is warranted at all"
target_object: SALPH / COSMIC / P32TRAILING / URLBLOB (where a decode succeeded structurally, oracle-tested)
candidate_set: not separately extracted per phase in this pass
candidate_set_digest: n/a
crypto_profiles: varies by phase; several are structural/no-oracle (rejected before reaching a cipher sweep)
oracle_capabilities: varies by phase, current at time of each run
output_detector: varies (structural validity, then printable-ratio gate where applicable)
coverage_scope: full (per operator), but the OPERATOR SET itself is not closed/pre-declared -- an open-ended list of combinators, contrary to this project's own brainstorm discipline
result: "all ~45 negative or null-like"
load_bearing_assumptions: "this is the central finding of the whole ledger: ~45 phases tested HOW DBBI/FAED combine; ZERO phases tested WHETHER they should be treated as interacting at all (the null topology). Phase 291 explicitly frames this: \"sixteen decoder-family models ... found nothing that isolates DBBI's or FAED's intended consumer,\" and formally parks the branch -- without ever having tested the premise underneath all sixteen (plus ~30 more) models."
later_changes: none recorded
current_disposition: branch formally parked (G-YIN-001, G-ESC-001)
reopen_condition: "per this ledger's own topology audit -- see GSMG_TOPOLOGY_AUDIT.md's recommended next action: test the null topology directly before adding a 46th combinator"
```

QR finder-ring-texture (296, 298-306) and Architect-monologue-substring
(307-308, 313-317) phases are candidate-derivation work on *other* objects
(QR pixel texture, film dialogue) — excluded here as out of scope for
frontier-object topology.

## Summary

See [GSMG_TOPOLOGY_AUDIT](GSMG_TOPOLOGY_AUDIT.md) for the scored comparison
this ledger feeds. In short: the best-evidenced claim in this whole ledger
is **negative** — Phase 238's "zero of six adjacency rules survive" result,
independently corroborated by Phases 96, 217/223, and 289's own framing.
The worst-evidenced claim was the one most later phases silently
inherited — that DBBI and FAED must combine at all (topology 3) — which
this ledger's own summary once flagged as never itself tested, only ~45
specific instantiations of it. That gap was closed by Phase 371, which
tests DBBI and FAED's local instruction adjacency independently (T0/T6)
rather than assuming a joint object: result inconclusive by design
(checkpoint/no-consumer was an explicitly permitted answer), but it
directly falsifies the *implicit* premise that DBBI/FAED are treated
symmetrically by the page's own structure. See Phase 371's block above.
