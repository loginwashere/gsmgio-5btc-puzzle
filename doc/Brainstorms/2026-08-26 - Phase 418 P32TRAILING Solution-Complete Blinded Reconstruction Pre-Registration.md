---
type: worksheet
status: live
date: 2026-08-26
topics:
  - brainstorm
  - p32trailing
  - blinded-experiment
  - external-solvers
  - evidence-acquisition
  - theory-registry
---

# Phase 418 — P32TRAILING Solution-Complete Blinded Reconstruction Pre-Registration

> [!caution] Draft for review; no execution authorized
> Phase 417 closed `calibrated_clean`, licensing this draft. This document is
> being written before the Phase 418 implementation, evidence packet, frozen
> prompt, solver responses, or result exist. No Phase 418 solver may be invoked
> until this preregistration is reviewed, frozen, and committed separately;
> the implementation and its regression fixtures are then committed in a
> second step; and explicit execution authorization is obtained afterward.
> Any substantive protocol correction after the first invocation makes the
> phase `protocol_invalid`. The later macro-clue experiment remains blocked.

## Question

When the calibrated Phase 417 panel instrument receives the sealed Phase 416
P32TRAILING evidence **plus all already-solved nested outputs that Phase 416
omitted**, do at least two of five eligible no-tool solvers independently
converge on a byte-identical, genuinely new preimage that opens the real
P32TRAILING envelope?

This phase tests whether the project's solution-complete upstream state enables
a reproducible new assembly. It does not test whether an unrestricted agent can
search the repository, whether the model remembers the public puzzle, or
whether arbitrary cipher families can brute-force the target.

## Why Phase 418 is licensed, and what changes

Phase 416 remains a valid negative for its exact sealed packet: five eligible
submissions converged on four surface-text candidates and all four tested
negative. Its packet nevertheless omitted the solved Phase-3.2.1 Beaufort
plaintext and supplied Phase 3.2.2 only as an undecoded numeral string and
riddle. That made its candidate-generation result confounded with incomplete
upstream evidence.

Phase 417 tested the same five-replicate, two-vote, no-tool instrument at a
held-out solved boundary. All five eligible submissions returned the exact
known preimage at rank 1, no wrong candidate converged, and the exact evaluator
recovered the committed plaintext. Its `calibrated_clean` result licenses one
solution-complete P32 comparison.

Phase 418 therefore changes **only the disclosed evidence** and the handling of
already-tested candidates:

1. start from Phase 416's sealed P32 packet;
2. add the exact solved Phase-3.2.1 output;
3. add the exact Phase-3.2.2 alphabet, escape pair, and 91-character decode;
4. retain Phase 416's schema, five-eligible/eight-invocation discipline,
   byte-exact canonicalization, and two-vote promotion rule;
5. classify exact Phase 270 duplicates before evaluation and never query them
   again; and
6. evaluate only genuinely new promoted candidates through Phase 416's frozen,
   redacted P32 oracle stack.

Nothing from the creator macro clue, Phase 416's candidate strings or votes,
or any later speculative construction is added. Nothing from Phase 417's
responses or result metadata is added beyond the worked-example material that
was already present in Phase 416's packet.

## Authenticated source and supplement commitments

The implementation must freshly decrypt the pinned Phase 3.2 OpenSSL vector,
locate all components by the delimiter rules in
`p32_sibling_password_audit.extract_phase32_components()`, independently
rederive both solved outputs, and assert the following before rendering any
packet. All strings in this table are ASCII and the hashes are over the exact
bytes described, with no newline added.

| Object | Position/length | SHA-256 |
|---|---:|---|
| Recovered Phase 3.2 plaintext | 2,422 bytes | `b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34` |
| Raw Phase-3.2.1 encoded block | `[447:1986]`, 1,539 bytes | `bd7a29432546c67c4170e0c523ddbf43ae82d20ee187d1b4dbf7907a0faf4c7b` |
| CP1141-transcoded Beaufort ciphertext | 1,539 bytes | `6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e` |
| Solved Phase-3.2.1 letters-only plaintext | 1,539 bytes | `56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241` |
| Phase-3.2.2 numeral string | `[1990:2139]`, 149 bytes | `71e3af174d533ad2c1c79fce64308f5fdf200f3cc50f059b2f1485a2c5f1765d` |
| Phase-3.2.2 clue sentence | `[2143:2288]`, 145 bytes | `fe2ee9e1d2218db842b5973f7761760d799ad6992cff4b6037fb0e940c7d358a` |
| Phase-3.2.2 keyed alphabet | 28 bytes | `f48871f6826fcd56670d412ad9056c7b48caf112fefe50a767063b8d431d745f` |
| Solved Phase-3.2.2 letters-only answer | 91 bytes | `878b7afacc9e35412e76b8506cc8297fa5aeba5381e108dc421b71a0ab8993d8` |
| P32TRAILING Base64 text | `[2292:2422]` including one internal CRLF, 130 source bytes; 128 bytes with that CRLF removed | normalized-text SHA-256 `b2e3f02fd7b79b9a0a85b9286d2b1f4e0e749171b3107d34ffc6b0b6fc2bdf5e` |

The packet discloses these solved values exactly:

- Beaufort key: `THEMATRIXHASYOU`;
- Phase-3.2.1 solved plaintext: the exact 1,539-character uppercase
  letters-only output committed above, with a human-readable spaced
  transcription clearly labeled as presentation only if included;
- Phase-3.2.2 alphabet: `FUBCDORA.LETHINGKYMVPS.JQZXW`;
- escape digits, in order: `(1, 4)`;
- Phase-3.2.2 decoded answer:
  `INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE`.

The implementation must obtain these values by the proven toolchain, not by
copying this document. It must prove the 149-digit string decodes to the pinned
91-character answer under the disclosed alphabet and escapes, and prove the
CP1141/Beaufort path reproduces the pinned 1,539-character answer.

## Sealed target inherited from Phase 416

The real target and address remain unavailable in the solver packet. The
implementation must structurally recover and verify them from live repository
constants, then disclose only:

- OpenSSL `Salted__` format and 80-byte raw-ciphertext length;
- SHA-256 of the 8-byte salt:
  `6a466725507fbd85afa11f4dedd438e6e7a2ee3079338ebe623f49a4b68546e2`;
- SHA-256 of the raw ciphertext:
  `cbbf945223b0c7a60e31b6ba7f5dfbc17f68f545bec059e937c11e7465d0117b`;
- the creator-described output shape, a regular Bitcoin private key; and
- SHA-256 of the prize-address string:
  `951209e1cf5a1feff85eea755e16b3481c174a75f45ddbbb35b67b92b46bfde2`.

The literal P32 Base64, decoded container, salt, ciphertext, prize address,
halving address, and any known candidate or response from Phases 414-416 must
be absent. Every length-40 contiguous slice of the real Base64 text, at every
starting offset, must be absent from the packet and prompt. Commitments are not
treated as proof of physical isolation; they only keep target material out of
the supplied prompt.

## Exact evidence packet

The packet contains exactly six classes of evidence:

1. Phase 416 Item 1, byte-for-byte in source content: the already-decrypted
   Phase 3.2 plaintext presentation up to the sealed P32 target, including the
   raw Phase-3.2.1 encoded block, Phase-3.2.2 numeral string, and clue sentence.
2. The new solution-complete supplement above: exact Phase-3.2.1 solved output;
   exact Phase-3.2.2 keyed alphabet, ordered escapes, and exact 91-character
   answer. These are labeled community-derived values authenticated by their
   successful solved boundaries, not creator-authored prose.
3. The same three solved AES worked examples used in Phase 416: Phase 2,
   Phase 3, and Phase 3.2.
4. The same solved-stage assembly recipe used in Phase 416: propose preimage
   `P`; compute lowercase ASCII `SHA256(P).hexdigest()`; feed that string to
   legacy single-round `EVP_BytesToKey`/SHA-256 and AES-256-CBC/PKCS#7.
5. The same sealed-target commitments and output-shape statement above.
6. A scope note stating that obvious direct uses and sibling concatenations
   were already tested in Phase 270 and will be mechanically classified as
   duplicates. The packet does **not** list Phase 270 candidate values or
   labels, because doing so would anchor the panel to prior guesses.

That unavoidably creates a residual behavioral limitation in the opposite
direction: a solver may self-censor a straightforward construction that is not
actually one of Phase 270's exact byte strings because it cannot see the hidden
inventory. The exact-byte classifier prevents mechanical over-exclusion, but
it cannot recover a candidate the panel declines to submit. Candidate diversity
and any negative result must be interpreted with that limitation disclosed.

No candidate-generation rule is invented for the missing P32-local instruction.
Phase 370 proved that only a bare `\r\n\r\n` separator lies between the
Phase-3.2.2 clue and P32TRAILING. Solvers must identify any proposed operation
from the disclosed upstream evidence and explain it in `derivation`.

The final packet and full prompt must be committed as exact artifacts and
pinned by UTF-8 byte length and SHA-256 before any invocation. The execution-
facing builder fails closed on any artifact, length, hash, commitment, or
required/forbidden-content mismatch.

## Solver population and invocation discipline

- Target: **5 eligible submissions** from fresh, no-history invocations using
  the same observable configuration as Phases 416 and 417: general-purpose
  solver class, default service configuration, no explicit model override, and
  no inherited project turns.
- Cap: **8 total preassigned invocation IDs**. Only malformed, tool-using, or
  blinding-invalid submissions may be backfilled with the byte-identical
  prompt. Failure to obtain five eligible submissions by invocation 8 is
  `protocol_invalid`.
- Invocation identity belongs to the orchestrator and is stored in an ID-keyed
  ledger. Replaying an ID cannot create another vote.
- Every invocation receives the exact committed prompt from the fail-closed
  builder. No hand copy, response repair, follow-up coaching, or prompt change
  is permitted after launch.
- Every observable invocation setting and every recorded tool call is persisted.
  Provider-side revisions that are not observable remain a disclosed limitation.

The five invocations are operationally isolated replicates from one environment,
not statistically independent observers. Vote counts receive no p-value.

## Tool prohibition and residual exposure

Reuse Phase 416/417's blanket prohibition unchanged: no file or repository
access, shell, code, calculator, hashing, encryption/decryption, candidate
testing, environment-variable access, web search, or external lookup for any
purpose. `tool_used` is required; `true` excludes the complete submission.
Recorded tool calls are checked against the disclosure. Recursive forbidden-
vocabulary and phase-number checks remain defense in depth.

This is instruction-level and packet-level isolation, not a sandbox. The exact
solved outputs and P32 target exist in the shared repository and public record.
A solver could violate instructions or recall material. Results must report
observed compliance without claiming lookup was impossible.

## Submission schema and canonicalization

Reuse Phase 416's schema and implementation by identity wherever possible:

- top level exactly `tool_used`, `reasoning_text`, `candidates`;
- 1-10 candidates, each exactly `display`, `derivation`, `rank`;
- ranks are the exact contiguous permutation `1..n`;
- non-empty strings and no duplicate candidate bytes within one submission;
- canonical candidate is exactly `display.encode("utf-8")`, represented by the
  orchestrator as lowercase hex, with no trimming, case-folding, separator
  changes, punctuation changes, or Unicode normalization;
- `placeholder`, `todo`, and `fixme` in free text reject the submission, while
  ordinary ellipsis punctuation does not; and
- duplicate JSON keys, prose outside one JSON object/fence, unknown fields,
  malformed types, or any schema deviation reject wholesale.

`derivation` must identify the disclosed source bytes or solved values and the
operation licensing every part of the proposed preimage. This is an eligibility
check only for empty/residual text; the orchestrator does not subjectively score
reasoning quality or promote a singleton because its prose seems persuasive.

## Frozen convergence rule

One eligible invocation contributes at most one vote to a byte-identical
candidate. A candidate is promoted if and only if at least **2 of the 5 eligible
invocation IDs** submit it. Deterministic order is: best rank ascending, vote
count descending, UTF-8 hex ascending. This rule is computed without reference
to Phase 270 membership or oracle outcome.

The result records all promoted candidates in redacted form: UTF-8 byte length,
SHA-256 of candidate bytes, vote count, best rank, and duplicate disposition.
Raw candidate bytes remain in the committed invocation ledger needed for
reproducibility but are not copied into `FINDINGS.md`; because this is a shared
repository, that ledger is evidence preservation rather than access control.

## Frozen Phase 270 duplicate classifier

Before any P32 oracle call, the implementation reruns Phase 270's live
`derive_sibling_outputs()`, `build_candidates()`, and `password_materials()`.
The frozen inventory must contain **25 unique base candidate byte strings** and
**50 unique password-material byte strings**. Drift in either count is
`protocol_invalid`.

For each promoted preimage `P`, compute `H = SHA256(P).hexdigest().encode()`.
Classify it `exact_duplicate_of_phase270` if **either `P` or `H` is an exact
member of Phase 270's 50-material set**. No normalization or semantic/fuzzy
matching is allowed. This definition covers the direct raw and SHA-256-hex
treatments Phase 270 actually queried. A duplicate inherits only Phase 270's
recorded negative for those exact bytes/profile combinations and is not sent to
the oracle again. Its votes and rank remain reported.

All other promoted candidates are `genuinely_new`. Classification is performed
only after the five-submission panel closes, so it cannot influence eligibility,
backfilling, votes, or solver behavior.

## Frozen evaluation of genuinely new promotions

Only `genuinely_new` promoted candidates enter Phase 416's existing redacted
P32 evaluator, imported rather than reimplemented. Candidate order is the
promotion order above. For each candidate, Phase 416's fixed order remains:
`H` under the solved exact profile first, then its preregistered remaining
broad profiles and structural tiers. The batch stops at the first terminal hit,
exactly as Phase 416 did; if no terminal hit occurs, every genuinely new
promotion is evaluated fully.

Raw decrypted plaintext, passwords, private scalars, and addresses are never
written to a response or result artifact. Outcomes expose only Phase 416's
redacted classifications:

- **terminal hit:** the recovered key material satisfies the full committed
  address relationship;
- **structural hit:** the exact two-key/full-`0x10`-padding shape or another
  preregistered structural tier fires without terminal confirmation; or
- **negative:** no preregistered structural tier fires.

No profile, heuristic, address, or candidate may be added after responses are
seen. A structural hit stops interpretation and requires a separately frozen
confirmation phase; it is not promoted rhetorically to a solve.

## Frozen mutually exclusive outcome branches

Branches are evaluated in this order:

1. **`protocol_invalid`** — fewer than five eligible submissions within eight
   IDs; prompt/configuration drift after launch; packet/commitment/duplicate-
   inventory validation failure; schema or ledger invariant violation; or any
   other preregistered execution invariant fails. No puzzle inference follows.
2. **`terminal_hit`** — at least one genuinely new promoted candidate produces
   Phase 416's terminal address-confirmed result. Stop at the first hit and
   report all earlier dispositions; this is candidate evidence requiring
   independent reproduction before any prize-handling action.
3. **`structural_hit`** — no terminal hit occurs, but at least one genuinely new
   promotion fires a preregistered structural tier. Stop and preregister a
   confirmation phase; do not launch the macro-clue panel.
4. **`novel_convergence_negative`** — at least one genuinely new candidate is
   promoted, all such candidates are evaluated as negative, and no hit occurs.
   This is the direct solution-complete counterpart to Phase 416's negative.
5. **`duplicate_only_convergence`** — one or more candidates are promoted, but
   every promotion is an exact Phase 270 duplicate. Zero oracle calls occur.
   Report vote/rank distributions; the panel stabilized only on prior-tested
   material and generated no convergent new construction.
6. **`no_convergence`** — no candidate reaches two votes. Report total distinct
   candidates and whether any Phase 270 duplicate appeared as a singleton, but
   make zero oracle calls.

The distinction among branches 4-6 is load-bearing. They diagnose, respectively,
a reproducible new construction that fails, stabilization only on old material,
and failure to stabilize at all.

## Interpretation and stopping rule

- `terminal_hit` or `structural_hit` blocks all unrelated follow-up until the
  exact result is independently confirmed under a separately frozen protocol.
- `novel_convergence_negative` closes the solution-complete external-panel
  comparison negative under this instrument. Phase 416 may then be described as
  directionally corroborated, while retaining its incomplete-packet confound.
- `duplicate_only_convergence` or `no_convergence` does not prove P32TRAILING
  non-identifiable. It shows that even after supplying all known nested outputs,
  this calibrated panel produced no reproducible new candidate.
- `protocol_invalid` licenses only a newly numbered correction addressing the
  exact defect; no response may be repaired or reused.

The **macro-clue experiment remains blocked under every Phase 418 branch in
this document**. A later decision to test it requires its own rationale,
preregistration, packet, contamination analysis, and explicit authorization;
Phase 418 does not pre-authorize that experiment.

## Required implementation controls before execution authorization

At minimum, the implementation must provide:

1. deterministic Phase-3.2 decryption and delimiter-based extraction, with all
   commitments and positions above asserted;
2. independent CP1141/Beaufort and checkerboard reconstructions of both solved
   supplements;
3. exact reuse-by-identity tests for Phase 416 parsing, schema, eligibility,
   canonicalization, promotion, ordering, and redacted evaluator functions;
4. committed packet and prompt artifacts with pinned lengths/hashes and a
   fail-closed execution-facing builder;
5. exhaustive absence checks for target/address material and forbidden prior
   candidate/result content, plus required-presence checks for the supplement;
6. a live Phase 270 inventory reconstruction asserting 25 unique base values and
   50 unique materials, with exact `P`/`H` duplicate fixtures and near-miss
   fixtures proving there is no fuzzy classification;
7. fixtures proving duplicates receive votes but zero oracle calls, while a
   genuinely new promoted candidate reaches the real redacted evaluator;
8. branch fixtures for all six outcomes, including mixed duplicate/new panels,
   the invocation-9 cap failure, structural-stop, and terminal-stop ordering;
9. deterministic candidate/redaction ordering and proof that raw plaintext and
   sensitive key/address material never enter result artifacts; and
10. byte-exact persistence of every raw response and invocation setting, with
    no manual rewriting.

Focused Phase 414-418 regressions, metadata validation, Python compilation,
JSON validation for any fixtures, and `git diff --check` must pass before an
execution request is made.

## Sequencing

1. Review and correct this draft without invoking a solver.
2. Freeze and commit this preregistration separately from implementation.
3. Implement and commit the packet, prompt, evaluator adapter, and regressions.
4. Obtain explicit Phase 418 execution authorization.
5. Launch the panel once and close under exactly one frozen branch.

No Phase 418 execution, macro-clue experiment, prize action, or external message
is authorized by this draft.

## Related notes

- [Phase 417 Blinded Panel Sensitivity Calibration Pre-Registration](2026-08-26%20-%20Phase%20417%20Blinded%20Panel%20Sensitivity%20Calibration%20Pre-Registration.md) (closed `calibrated_clean`; licenses this draft)
- [Phase 416 P32TRAILING Sealed-Target Blinded Reconstruction Pre-Registration](2026-08-25%20-%20Phase%20416%20P32TRAILING%20Sealed-Target%20Blinded%20Reconstruction%20Pre-Registration.md) (closed `negative`; exact incomplete-packet comparator)
- [P32 Trailing Sibling-Output Password Path](2026-08-14%20-%20P32%20Trailing%20Sibling-Output%20Password%20Path.md) (Phase 270 family and limitations)
- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
