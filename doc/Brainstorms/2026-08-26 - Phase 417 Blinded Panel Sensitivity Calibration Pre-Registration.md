---
type: worksheet
status: closed
date: 2026-08-26
topics:
  - brainstorm
  - p32trailing
  - blinded-experiment
  - external-solvers
  - positive-control
  - theory-registry
---

# Phase 417 — Blinded Panel Sensitivity Calibration Pre-Registration

> [!success] Closed `calibrated_clean` (2026-08-26)
> Five fresh, no-history `general-purpose` invocations were used, so no
> backfill was needed within the eight-invocation cap. All five raw responses
> parsed, matched the exact Phase 416 schema, reported `tool_used: false`, had
> zero recorded tool calls, and passed the frozen blinding checks. Each
> submitted exactly one rank-1 candidate, and all five candidates were the
> byte-identical ground-truth preimage. The two-vote gate therefore promoted
> one candidate with 5/5 votes; no wrong candidate converged. The exact
> Phase-410-only evaluator recovered a 2,422-byte plaintext with SHA-256
> `b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34`.
> The result is `calibrated_clean`, not merely a positive decrypt: observed
> sensitivity passed and this panel showed no spurious convergence. This does
> not make the five same-environment invocations statistically independent or
> prove filesystem isolation, and it does not establish that P32TRAILING is
> identifiable. It licenses drafting the separately preregistered,
> solution-complete Phase 418 packet; the macro-clue experiment remains
> blocked. Raw responses and dispositions are pinned in
> `tools/gsmg/phase417_invocation_ledger.json` and
> `tools/gsmg/phase417_result.json`.

> [!note] Frozen before execution; retained as the preregistration record
> This document is being written before the Phase 417 implementation,
> frozen prompt, or solver responses exist. No solver has been invoked and
> no score has been computed. The numeric commitments below were
> mechanically derived from the already-pinned Phase 3/3.2 vectors for
> review; the eventual implementation must recompute and assert every one
> before this protocol can be frozen. Any correction made after the first
> solver invocation voids the phase as `protocol_invalid` rather than
> silently amending it in place.

## Question

Can the same five-replicate, convergence-gated, no-tool reconstruction
instrument used by Phase 416 recover a **known solved boundary** when it is
given all of that boundary's already-solved component values and local
assembly instructions, while the target ciphertext and recovered plaintext
are sealed in the same way as Phase 416's unknown target?

This is a positive-control calibration of the **panel method**, not a new
puzzle solve and not a cryptanalytic search. The held-out target is the
already-solved Phase 3.2 preimage. The instrument passes only if the exact
known byte string survives the same two-vote convergence gate that Phase 416
used. A plausible answer, a padding-valid wrong decrypt, or one correct but
unpromoted singleton does not count as a calibrated pass.

## Why this phase is required before another P32TRAILING panel

Phase 416's raw result remains valid for its exact packet: five eligible
replicates converged on four surface-text candidates, and all four tested
negative. Its interpretation had a real confound, however. The packet gave
solvers the raw Phase-3.2.2 numeral string and riddle but omitted the
repository's already-known keyed alphabet, escape pair, and 91-character
decode; it likewise omitted the already-solved Phase-3.2.1 Beaufort output.
The project-level riddle was solved, but the no-tool panel was not given its
solution.

Before testing a corrected, solution-complete P32TRAILING packet, this phase
asks whether the panel instrument can recover a known preimage from a
locally instructed, solution-complete boundary at all. Phase 341 calibrated
a deterministic rule engine on the three solved boundaries; it did **not**
calibrate the external-agent panel introduced in Phases 414-416. A negative
from an uncalibrated candidate generator cannot distinguish missing puzzle
evidence from insufficient instrument sensitivity.

## Held-out boundary and provenance

The target is the Phase 3.2 OpenSSL envelope embedded at the end of the
already-decrypted Phase 3 plaintext.

- The Phase 3 ciphertext and its derivation structure are present in the
  pinned Wayback-authenticated HTML artifact. Phase 410 independently
  decrypts it and byte-for-byte round-trips the original container.
- Its recovered 4,090-byte plaintext contains the three Phase 3.2 clue
  paragraphs, their local `/(aa, connected enf)` annotations, the literal
  `giveit` prefix instruction, the statement that Phase 3.2 again uses
  SHA-256/AES-256-CBC/Base64, and finally the embedded Phase 3.2 envelope.
- The three component answers are community-derived interpretations, not
  verbatim creator text: `Jacque Fresco`, `just one second`, and
  `Heisenberg's uncertainty principle`. Their exact normalized assembly is
  empirically authenticated because it decrypts the embedded envelope to
  the pinned 2,422-byte plaintext and re-encrypts with the original salt to
  reproduce the complete original container byte for byte (Phase 410).

This evidence separation must remain explicit in the packet: creator-
authenticated raw clue/instruction bytes are not relabeled as creator-
authored solution prose; the community-derived component answers are
labeled as already-solved values authenticated by the successful boundary.

## Frozen internal ground truth — never included in the solver prompt

The evaluator's exact expected preimage is:

```text
jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple
```

- UTF-8 length: **62 bytes**.
- SHA-256: `250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c`.
- The digest's lowercase hexadecimal ASCII representation is the literal
  password to the known Phase 3.2 OpenSSL envelope.

The full preimage, its UTF-8 hex encoding, and its SHA-256 digest are barred
from the solver prompt. The three component values and their local assembly
instructions are disclosed, because assembling those known fragments is the
capability being calibrated. The implementation must assert that the full
preimage and the 64-character digest do not occur verbatim in the rendered
prompt.

The exact ground truth is necessarily present elsewhere in this shared
repository and in the public community walkthrough. As in Phase 416, this is
not filesystem isolation. Tool-use exclusion, post-hoc blinding checks, and
fresh no-history invocations are residual controls, not proof that a solver
could not retrieve or remember the public answer. A correct result therefore
demonstrates operational sensitivity under the observed protocol; it does
not establish statistically independent rediscovery or rule out model-memory
contamination.

## Structurally equivalent sealed target

The packet is built from the freshly recovered 4,090-byte Phase 3 plaintext,
not from a README transcription. The embedded Phase 3.2 Base64 span is
located structurally by parsing the unique trailing OpenSSL envelope and
verifying it against the pinned solved vector. The packet retains bytes
`[0:726]` exactly and replaces bytes `[726:4090]` with a sealed-target note.

The implementation must recompute and assert all of the following before it
can render a prompt:

| Object | Position/length | SHA-256 commitment |
|---|---:|---|
| Disclosed Phase 3 plaintext prefix | `[0:726]`, 726 bytes | `71da3ceeccc7af315dcabfc071a3c77f9211a73d88178f5275cde5cf8be06ea3` |
| Withheld literal Base64 span, including its original line breaks | `[726:4090]`, 3,364 bytes | `265780b6bc80c9a05b9f9caf6a577d7fb91497d7b8c5227338c6f0f1b5ae1266` |
| Decoded `Salted__` container | 2,448 bytes | `9d172dc017034564b40eb381fa61e31421f509a08430864c77ccf86cfc8fe784` |
| Container salt | 8 bytes | `f350dabeb2157fa917b972e7db5b1e23a6b1c7a55fc5725c716fc357f36aee47` |
| Raw ciphertext | 2,432 bytes | `48a77592e2f3ed1d508010157bb9af169ec4898cc8f05b9ac7cdd5aeebdb278a` |
| Withheld recovered target plaintext | 2,422 bytes | `b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34` |

The solver receives the positions, formats, lengths, and commitments, but
not the literal withheld Base64 span, salt, ciphertext, recovered plaintext,
preimage, or password digest. This mirrors Phase 416's generator/evaluator
separation: solvers generate candidates from disclosed clue evidence; only
the orchestrator holds the target and evaluates promoted candidates.

## Evidence packet contents

The solver packet contains exactly five classes of evidence:

1. **The exact 726-byte Phase 3 plaintext prefix** preceding the embedded
   Phase 3.2 envelope. This includes all three clue paragraphs, all three
   local `/(aa, connected enf)` annotations, the `giveit` prefix instruction,
   and the statement of the next boundary's crypto format.
2. **An already-solved component supplement**, labeled as community-derived
   values authenticated by the known successful decrypt:
   - clue 1 answer: `Jacque Fresco`;
   - clue 2 answer before its locally instructed prefix: `just one second`;
   - clue 3 answer: `Heisenberg's uncertainty principle`.
   The supplement states the empirically authenticated normalization for
   this solved boundary: force lowercase, remove spaces and the possessive
   apostrophe, and prepend the literal letters `giveit` directly to clue 2's
   normalized answer. It must not generalize that punctuation treatment into
   a universal definition of `connected enf`; Phase 341 found the source text
   underdetermines that byte-level detail and the known decrypt resolves it
   only for this boundary.
3. **Two prior worked boundary examples only** — Phase 2 and Phase 3. Phase
   3.2 is the held-out target and must not appear as a worked example.
4. **The solved-stage cryptographic recipe:** assemble preimage `P` according
   to the local instructions; compute lowercase ASCII
   `SHA256(P).hexdigest()`; use that digest string with the target salt under
   legacy single-round `EVP_BytesToKey`/SHA-256, AES-256-CBC, and PKCS#7.
5. **The sealed-target note** containing only the commitments and structural
   facts in the preceding section.

Nothing from Phase 416's P32TRAILING plaintext, ciphertext, prize address,
panel responses, promoted candidates, or result is included. Nothing from
the later creator macro clue is included. Phase 417 calibrates the instrument
on one known boundary; it is not a disguised P32 candidate-generation run.

## Solver population and invocation discipline

- Target: **5 eligible submissions** from 5 fresh, operationally isolated
  clean-context invocations using the same observable configuration as Phase
  416: the same general-purpose solver class, default service configuration,
  no explicit model override, and no inherited turns from this project.
- Cap: **8 total invocation IDs**. Malformed, tool-using, or blinding-invalid
  submissions may be backfilled only by sending the byte-identical frozen
  prompt to a new invocation ID. If five eligible submissions are not
  obtained by invocation 8, the outcome is `protocol_invalid`.
- Invocation identity is assigned by the orchestrator and stored in an
  ID-keyed ledger. A response cannot create its own identity, and replaying
  one invocation ID cannot create an additional vote.
- Every invocation receives the byte-exact output of a fail-closed prompt
  builder. The eventual packet artifact, prompt artifact, lengths, and
  SHA-256 pins must be committed and regression-tested before any invocation.
  No hand-copied prompt and no prompt amendment after launch is permitted.
- Solvers remain operationally isolated replicates from the same agent/model
  environment, **not statistically independent observers**. No inferential
  p-value is attached to vote counts.

The implementation record must pin every solver configuration field exposed
by the invocation mechanism. A provider-side model revision that is not
observable or selectable cannot honestly be frozen; it is a residual
comparability limitation, not silently described as controlled. Any
observable model/configuration change relative to Phase 416 must be declared
before freezing this document. An undisclosed observable change after launch
makes the comparison `protocol_invalid`.

## Tool prohibition and residual exposure

Use Phase 416's exact blanket prohibition: no file or repository access, no
shell, code, calculator, hashing, encryption/decryption, candidate testing,
environment-variable access, web search, or external lookup for any purpose.
`tool_used` remains a required explicit boolean; `true` excludes the entire
submission regardless of why a tool was used. Recorded tool calls are checked
against that disclosure. Post-hoc forbidden-vocabulary and phase-number scans
remain defense in depth.

This is still instruction-level isolation, not a physical sandbox. A solver
with ordinary shared-repository access could violate the prompt and retrieve
the known answer. The result must therefore report observed tool compliance
and blinding checks without claiming physical impossibility of lookup.

## Submission schema and canonicalization

Reuse Phase 416's strict JSON schema unchanged:

- top level: exactly `tool_used`, `reasoning_text`, `candidates`;
- 1-10 raw candidate entries;
- candidate keys: exactly `display`, `derivation`, `rank`;
- ranks form the exact contiguous permutation `1..n`;
- no duplicate candidate bytes within one submission;
- orchestrator computes `display.encode("utf-8").hex()` without trimming,
  case-folding, separator changes, or Unicode normalization;
- `placeholder`, `todo`, and `fixme` in any free-text field reject the whole
  submission; ordinary ellipsis punctuation does not;
- duplicate JSON keys, prose outside a single JSON object/fence, unknown
  fields, malformed types, or any other schema deviation reject wholesale;
  nothing is manually repaired or coerced.

The `derivation` field must identify which disclosed component and local
instruction licenses every piece of the proposed byte string. This is a
packet-local reasoning check, not a second promotion path. Convergence remains
the sole promotion rule.

## Frozen promotion and evaluation

One invocation contributes at most one vote to any byte-identical candidate.
A candidate is promoted if and only if it receives votes from at least **2 of
the 5 eligible invocation IDs**. Candidate order is deterministic: best
(lowest) solver rank ascending, then vote count descending, then UTF-8 hex
ascending as a final tie-break.

After the five-submission panel is complete:

1. Record the exact ground-truth preimage's vote count and best rank across
   all eligible submissions. This diagnostic is computed only after the panel
   closes and never changes eligibility, backfilling, or promotion.
2. Promote candidates using the frozen two-vote rule without reference to the
   ground truth.
3. Evaluate promoted candidates under **only** the known Phase-410 profile for
   this boundary: `H = SHA256(P).hexdigest()` as lowercase ASCII -> legacy
   `EVP_BytesToKey`/SHA-256 -> AES-256-CBC -> PKCS#7.
4. A candidate is correct only if the recovered plaintext is exactly 2,422
   bytes and its SHA-256 equals
   `b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34`.
   Padding validity, printable text, a prefix match, or a structural shape is
   insufficient. Raw plaintext and password material are immediately
   discarded after redacted classification.

No broad CBC/ECB/stream/Key-Wrap sweep is run. The target's exact crypto
profile is already known; adding alternative cipher/KDF families would test a
different instrument and create false opportunities for wrong candidates.

## Frozen outcome branches

The branches are mutually exclusive and evaluated in this order:

1. **`protocol_invalid`** — five eligible submissions are not obtained within
   eight invocation IDs; a prompt or observable model/configuration changes
   after launch; commitment/prompt validation fails; the known ground-truth
   preimage is promoted but the exact evaluator fails to recover the committed
   plaintext (an evaluator/fixture contradiction); or any other preregistered
   execution invariant is violated. No sensitivity inference is made.
2. **`calibrated_clean`** — the exact ground-truth preimage is promoted and
   exact-decrypts to the committed plaintext, and no wrong candidate also
   converges.
3. **`calibrated_with_spurious_convergence`** — the exact ground-truth
   preimage is promoted and exact-decrypts correctly, but at least one wrong
   candidate also reaches the two-vote threshold. Sensitivity is demonstrated,
   but specificity is visibly limited.
4. **`wrong_convergence`** — one or more candidates converge, but the exact
   ground-truth preimage is not promoted. This includes the informative mixed
   case where the correct preimage appears only once while a wrong candidate
   receives two or more votes. Report `ground_truth_vote_count` and
   `ground_truth_best_rank` so that singleton case remains visible.
5. **`no_convergence`** — no candidate receives two votes. Report whether the
   exact ground truth appeared once or zero times. Either value is a calibration
   failure under the frozen convergence instrument, but they diagnose different
   weaknesses: a singleton indicates aggregation-threshold failure; zero
   indicates candidate-generation failure on an instruction-complete boundary.

The distinction between branches 4 and 5 is load-bearing. `wrong_convergence`
shows shared surface-pattern bias can dominate even when sufficient evidence
is present; `no_convergence` shows the panel cannot stabilize on any answer.
Neither may be summarized merely as "negative."

## Interpretation and stopping rule

- `calibrated_clean` licenses drafting the separately preregistered
  solution-complete P32TRAILING panel: Phase 416's packet plus the exact solved
  Phase-3.2.1 output and Phase-3.2.2 alphabet/escapes/91-character answer, with
  Phase 270 duplicates classified rather than re-tested.
- `calibrated_with_spurious_convergence` licenses that same next experiment
  only with an explicit low-specificity caveat. A P32 negative would remain
  weaker than under `calibrated_clean`, and wrong convergence patterns must be
  compared descriptively.
- `wrong_convergence` or `no_convergence` stops the external-panel line. Phase
  416 is then retained as an exact-packet negative but treated as inconclusive
  about reconstructability; no solution-complete P32 panel and no macro-clue
  panel is launched with this instrument unchanged.
- `protocol_invalid` licenses only a newly numbered correction phase addressing
  the exact protocol defect. It does not license accepting or repairing any
  Phase 417 submission post hoc.

Even a clean pass does not prove P32TRAILING is identifiable: this positive
control has explicit local assembly instructions, while P32TRAILING presently
has none (Phase 370). It establishes only that the panel can recover a known,
instruction-complete construction of the relevant task type.

## Required implementation controls before execution authorization

The eventual implementation must include, at minimum:

1. deterministic extraction/decryption of the authenticated Phase 3 vector and
   structural location of the unique trailing Phase 3.2 envelope;
2. hard assertions for every commitment and byte boundary in this document;
3. a committed evidence-packet artifact and frozen-prompt artifact, each pinned
   by length and SHA-256, with a fail-closed execution-facing builder;
4. structural absence checks for the full ground-truth preimage, its UTF-8 hex,
   its SHA-256 digest, the withheld Base64 span, and recovered target plaintext;
5. exact reuse of Phase 416 parsing, schema, invocation identity, eligibility,
   and convergence mechanics wherever compatible rather than reimplementation;
6. an end-to-end exact positive proving the known preimage reaches the committed
   plaintext hash through the real evaluator;
7. a wrong-password fixture that happens to have valid PKCS#7 padding but is
   rejected because the exact plaintext commitment does not match;
8. branch fixtures for `calibrated_clean`,
   `calibrated_with_spurious_convergence`, `wrong_convergence` (including a
   correct singleton), `no_convergence` (both singleton and zero-ground-truth
   diagnostics), and `protocol_invalid` at invocation 9;
9. byte-exact regression checks proving every invocation uses the committed
   prompt artifact and no response is manually rewritten.

## Sequencing

1. Review and correct this draft without running any solver.
2. Freeze and commit the preregistration separately.
3. Implement the packet, prompt, evaluator, and regressions in a second commit.
4. Obtain explicit execution authorization.
5. Launch the panel once under the frozen protocol and close the phase under
   exactly one branch above.

The Phase 418 solution-complete P32TRAILING experiment and the later full-
macro-clue augmentation remain unstarted and unfrozen until Phase 417 closes.
