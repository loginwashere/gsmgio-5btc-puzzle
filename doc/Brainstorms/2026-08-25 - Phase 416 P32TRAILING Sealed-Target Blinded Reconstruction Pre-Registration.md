---
type: worksheet
status: closed-negative
date: 2026-08-25
topics:
  - brainstorm
  - p32trailing
  - blinded-experiment
  - external-solvers
  - evidence-acquisition
  - theory-registry
---

# Phase 416 — P32TRAILING Sealed-Target Blinded Reconstruction Pre-Registration

> [!failure] Closed `negative` (2026-08-25) -- panel completed, convergence fired, all promoted candidates tested negative
> Six invocations were run (within the 8-invocation cap): invocation 2 was
> schema-rejected (its raw `candidates` list had 11 entries, over the 1-10
> limit -- confirmed by `validate_submission_schema()` directly, not by
> inspection); invocations 1, 3, 4, 5, and 6 were all schema-valid,
> non-tool-using (`tool_used: false`, corroborated by zero tool calls in
> each transcript), and blinding-clean, filling the 5-submission panel on
> the first attempt past invocation 2's rejection. All five eligible
> invocations complied with the tool prohibition (zero recorded tool
> calls each) and no self-testing was observed; the real ciphertext and
> address were absent from the sealed packet and prompt. Solvers retained
> ordinary shared-repository access throughout -- see "Threat model and
> residual exposure" below for what this run does and does not establish
> about that access.
>
> `promote_candidates()` found four hex values with >=2 votes from
> distinct invocation IDs: the bare 149-digit numeral string (unanimous, 5/5 votes), the closing
> riddle sentence lowercased and stripped of punctuation/spaces
> (`afubcdkingoraclequeenthingkymvpsonasadboardbutaswideasthefirstoneseen`,
> 2 votes), `oneforonefourforone` (2 votes), and
> `raisingthestakeswithoutextrachancesofwinning` (2 votes). All four were
> tested against the real `P32TRAILING` blob via `test_candidates()`'s
> full CBC/ECB/stream/secondary-families sweep (72-73 variants each,
> `H`-exact -> `H`-remaining-broad -> `P`-broad order): **all four
> returned `outcome: negative`, no terminal hit, no structural hit.**
> Since none hit, the batch's stop-at-first-hit rule never triggered --
> all four were tested in full, as the deterministic order requires when
> nothing stops it early.
>
> This does not mean `P32TRAILING` is unsolvable, nor that the sealed-
> target architecture failed -- it means five operationally isolated
> replicates (distinct invocation IDs, not statistically independent
> observers) converged on the same handful of surface-level textual
> guesses (the riddle sentence, the digit string, "one for one, four for
> one"), and none of those specific guesses is the real preimage. The
> five solvers largely agreed the closing riddle ("fubcd-king", "oracle-
> queen", "thingky mvps") reads as an intentionally garbled cipher none
> reported cracking by hand under the tool prohibition. That unresolved
> riddle is a plausible candidate-generation bottleneck for why the
> panel converged on guesses rather than the real answer -- this run did
> not compare it against alternative causes, so it is not established as
> the most likely one.

> [!caution] Prepared before any solver is invoked
> This document supersedes
> [Phase 415](2026-08-25%20-%20Phase%20415%20P32TRAILING%20Blinded%20Independent%20Reconstruction%20Corrected%20Pre-Registration.md),
> which is closed `protocol_invalid` for two independent reasons (see its
> own closure note): a schema false positive on ordinary ellipsis
> punctuation, and -- more importantly -- a prompt-only tool restriction
> that invocation 4 demonstrated is not an adequate safety boundary: it
> disclosed running roughly 1,600 local candidate tests via Bash/OpenSSL
> directly against the real `P32TRAILING` ciphertext, outside this
> project's redaction wrapper. Nothing from Phase 415 carries forward:
> invocation 5 is not reused, invocations 1-2 are not retrospectively
> accepted, and no candidate from any of the 5 invocations was tested.
> Invocation 4's transcript remains quarantined (see its own closure note
> and `FINDINGS.md`) -- not opened further, not committed, not copied
> into any documentation beyond aggregate disposition metadata.

## What changed, and why

A prompt instruction ("do not use any tool to look up this puzzle") is
words, not a boundary -- it forecloses external lookup but says nothing
about a solver testing candidates against material the prompt itself
handed over. Phase 416's fix is architectural, not lexical:

**The real ciphertext and the real prize address are never placed in the
evidence packet or prompt text.** Item 1 replaces the final base64
ciphertext block with its position, format, length, and SHA-256
commitments of the real salt and ciphertext bytes. Item 4 replaces the
literal prize address with a SHA-256 commitment of the address string.
Both real values remain available to the ORCHESTRATOR (this phase's own
script, via `cb_common.BLOBS["P32TRAILING"]` and
`first_hint_hash_audit.PRIZE_ADDRESS`, imported normally) for redacted
testing after promotion. This is **packet-level sealing**: a solver that
only reads what it is given cannot decrypt, verify, or self-test against
either target, because the prompt simply does not contain them. This is
**generator/evaluator separation**: solvers propose hypotheses; only the
orchestrator can run the experiment. The frozen prompt's tool
restriction is also broadened (see below) as reinforcement, not as the
only safeguard.

**This is not filesystem or tool isolation, and the claim should not be
read that way** -- see "Threat model and residual exposure" below.

**Corrections, exactly three, relative to Phase 415:**

1. **Sealed target.** As above -- `build_sealed_evidence_packet()`
   replaces the ciphertext block and the prize address with commitments;
   the real values are held only by the orchestrator.
2. **Residue check corrected.** `"..."` is removed from `RESIDUE_MARKERS`
   entirely -- it fired on ordinary ellipsis punctuation, including
   punctuation appearing literally in the evidence packet's own quoted
   plaintext, wholesale-rejecting two otherwise clean Phase 415
   submissions. `placeholder`, `todo`, and `fixme` remain.
3. **`closure` removed from the schema entirely**, not merely gated by
   an empty allowlist as in Phase 414/415. This is a preregistered
   simplification of the promotion rule, not a claim that closure-style
   reasoning is incoherent under a sealed target -- an instruction can in
   principle uniquely determine a preimage without the solver ever
   touching the ciphertext. It is dropped because this phase commits to
   convergence as its sole, simpler promotion discipline.
   **Convergence is the sole promotion path** in this phase: at least 2
   of the 5 eligible submissions independently producing the
   byte-identical `preimage_utf8_hex`.

## Threat model and residual exposure

Packet-level sealing defends against exactly one thing: a solver that
only reads the prompt it is given cannot recover the real ciphertext or
the real prize address, because those bytes are not in the prompt. It
does **not** provide filesystem or tool isolation. This phase's actual
invocation mechanism is the `Agent` tool with `subagent_type:
"general-purpose"`, which grants full tool access (shell, file read,
etc.) in an environment where this repository -- including
`cb_common.BLOBS["P32TRAILING"]` and
`first_hint_hash_audit.PRIZE_ADDRESS` -- is reachable. A solver that
chose to `grep` or `cat` its way around this repository, rather than
reason from the prompt, could in principle recover both real values
directly from the filesystem. This is the same class of gap invocation
4 exploited in Phase 415 (a capable agent using tools the prompt told it
not to use), pointed at the filesystem instead of the prompt.

What actually defends against this, given that constraint:

- **The `tool_used` mechanical exclusion** (retained from Phase
  414/415): any submission disclosing tool use of any kind is excluded
  from the panel regardless of purpose or outcome, no exceptions. This
  is a *disclosure*-based control -- it catches a solver that reports
  using a tool honestly. It does not, and cannot, catch a solver that
  uses a tool and reports `tool_used: false` anyway.
- **Post-hoc blinding checks** (`blinding_violations()`, forbidden
  vocabulary, the `Phase N` regex): catch a submission that leaks
  knowledge of this project's own internal phase numbering or vocabulary
  it should not have, which would be circumstantial evidence of
  out-of-band lookup even absent a `tool_used` disclosure.
- **What is NOT claimed**: that no invoked solver can physically reach
  the real ciphertext or address. That would require running each
  solver in a genuinely isolated environment (no filesystem access
  beyond a scratch directory, no shell) that this project's spawn
  mechanism does not currently provide. If a future phase adds that
  isolation, the stronger claim (sealing "regardless of what tools it
  has access to") would become accurate; until then, this phase's
  guarantee is scoped to a solver that follows the prompt's own
  instructions, backed by disclosure-based and post-hoc detection, not
  physical prevention.

This is a real, acknowledged reduction in what "sealed" can honestly be
said to guarantee here -- worth stating plainly rather than papering
over with confident-sounding language the actual invocation mechanism
cannot back up.

**Everything else is unchanged from Phase 414**, reused by direct import
from `phase414_p32trailing_blinded_reconstruction_audit` where the code
does not depend on the sealed packet or the schema: the three calibration
examples and the generic assembly recipe (Items 2-3, both entirely about
already-solved boundaries, safe to disclose in full as before), the
redacted `classify_plaintext()` and structural tiers, the
`test_material_cbc/ecb/stream/secondary_families()` oracle wrapper and
its no-logging/stop-at-first-hit guarantees, `test_candidate()`'s frozen
`H-exact -> H-remaining-broad -> P-broad` order, `_promotion_sort_key()`
and deterministic batch ordering, `parse_submission()` and its
fullmatch-anchored fence/duplicate-key-rejecting mechanics, blinding
checks (`blinding_violations()`, the forbidden-vocabulary list, the
`Phase N` regex outside `{2, 3, 3.2}`), and the population target (5),
invocation cap (8), and convergence threshold (2) constants. Only
`build_sealed_evidence_packet()`, `validate_submission_schema()`,
`eligible_submissions()`, `evaluate_panel()`, and `promote_candidates()`
are redefined in this phase's own module -- the first because the packet
content itself changed, the middle two because they call
`validate_submission_schema()` by name within their defining module's
own namespace, and `promote_candidates()` because it is now
convergence-only (no closure path exists to gate a second one).

## The sealed evidence packet

Built deterministically by `build_sealed_evidence_packet()` in
`tools/gsmg/phase416_p32trailing_sealed_target_reconstruction_audit.py`,
sourced directly from the same underlying data as Phase 414/415's packet
(no manual retyping of any security-sensitive fixed string), with the
withheld spans located and verified **structurally** (the trailing
paragraph must decode to a `"Salted__"`-prefixed blob of the expected
length whose ciphertext hashes to the pinned commitment) rather than
sliced out at a hardcoded offset.

> [!info] Packet pinned (2026-08-25, revised)
> 9,039 bytes, SHA-256 `21786b66ebd6312622c581338fc124127a998d70974fb4c4eca34126546e62d5`.
> Generated by `build_sealed_evidence_packet()` and pinned as a
> regression in `self_test()`, which also asserts the real prize/halving
> addresses and every length-40 contiguous slice of the real base64 blob
> (every starting offset, not a sampled subset) are absent from the
> packet text. Revised from the first pin to also commit the 8-byte salt
> (see "What changed, and why" and the corrected review below) -- the
> byte count and hash both moved accordingly. No solver has been invoked
> yet.

1. **The Phase 3.2 plaintext up to (not including) the final ciphertext
   block**, identical in content and presentation to Phase 414/415's
   Item 1 (opening passage, hex-dumped embedded sub-block, the 149-digit
   checkerboard numeric string, the Phase 3.2.2 clue sentence) -- all of
   this is already-decrypted, confirmed puzzle output and stays fully
   disclosed. In its place, the final base64 ciphertext block (the sole
   unsolved target) is replaced by a labeled note giving:
   - **format**: base64 of OpenSSL's standard `"Salted__"` + 8-byte salt
     + ciphertext layout (the same format Item 3's recipe names);
   - **length**: 80 bytes of raw ciphertext after the header (5 AES
     blocks of 16 bytes each);
   - **a SHA-256 commitment of the 8-byte salt** (not the ciphertext):
     `6a466725507fbd85afa11f4dedd438e6e7a2ee3079338ebe623f49a4b68546e2`;
   - **a SHA-256 commitment of the raw ciphertext bytes** (not the
     base64 text, not the header, not the salt):
     `cbbf945223b0c7a60e31b6ba7f5dfbc17f68f545bec059e937c11e7465d0117b`.
2. **Three solved AES boundaries, as worked calibration examples**
   (Phase 2, Phase 3, Phase 3.2 itself) -- identical to Phase 414/415's
   Item 2, unchanged, since none of it touches `P32TRAILING`.
3. **The solved-stage assembly instructions** (the recipe) -- identical
   to Phase 414/415's Item 3, unchanged.
4. **The output requirement.** The creator's own description ("a regular
   Bitcoin private key") is retained; the prize address itself is
   replaced by its SHA-256 commitment:
   `951209e1cf5a1feff85eea755e16b3481c174a75f45ddbbb35b67b92b46bfde2`.

**Nothing else is included or referenced**, and none of the three
commitments (salt, ciphertext, address) is usable by a solver to
self-verify anything -- all are one-way hashes of values the solver
never receives.

## Solver protocol

Unchanged from Phase 414/415: population target 5 eligible submissions,
from clean-context agent invocations with no inherited turns from this
project's history; the same "independent is qualified, not claimed
outright" caveat; the same two blinding backstops (disclosed-tool-use
exclusion, post-hoc forbidden-vocabulary/phase-number check, both
retained as defense in depth even though the sealed design no longer
depends on them alone); the same invocation-identity ledger
(orchestrator-assigned ID, dict-keyed, never a bare list); the same
8-invocation cap with `protocol_invalid` as an explicit, predeclared
outcome, cap-enforced before panel readiness is even considered.

**Frozen prompt.** Phase 414's own history -- a hand-copied prompt that
drifted between invocations with no mechanical check catching it -- is
why this phase does not rely on a Markdown code block as the source of
truth. The prompt is built by `build_solver_prompt()` in
`tools/gsmg/phase416_p32trailing_sealed_target_reconstruction_audit.py`
(template + the sealed packet substituted in verbatim), its hash is
pinned as `SOLVER_PROMPT_SHA256`, and the exact byte-for-byte text is
committed as a repo artifact at
`tools/gsmg/phase416_frozen_solver_prompt.txt`, diffed against
`build_solver_prompt()`'s live output on every `self_test()` run. **Every
invocation must be given `build_solver_prompt()`'s return value directly
-- never a hand-copy of the block below**, which is included only for
human readability:

```text
You are looking at a real, currently-unsolved piece of an authenticated
cryptographic puzzle. Below is the evidence you have: an already-decrypted
plaintext from earlier, solved stages of the same puzzle (labeled Phase 2,
Phase 3, Phase 3.2), three fully worked examples of how those earlier
stages each turned some piece of solved text into the next stage's AES
password, and the final output requirement. The actual ciphertext for the
one remaining unsolved block, and the actual address the resulting key
must control, are DELIBERATELY NOT INCLUDED IN THIS PROMPT -- you are
given only their position, format, length, and a one-way cryptographic
commitment (a SHA-256 hash) of each. Do not attempt to retrieve either
value from any local file, this or any other repository, an environment
variable, or any other source outside this prompt -- doing so is a tool-
use violation under the prohibition below regardless of whether you
succeed.

[SEALED EVIDENCE PACKET INSERTED HERE VERBATIM]

Your task: propose up to 10 candidate PREIMAGES for the withheld
ciphertext block described above. A preimage is the string you believe
should be SHA-256 hashed to become the actual AES password -- per the
recipe above, the password itself is H = sha256(P).hexdigest(), not P.
Do not submit an already-hashed string as a candidate; submit P, the
thing to be hashed. You cannot verify your guess from the material
included in this prompt -- the ciphertext and address appear only as
commitments here -- so submit your best reasoned candidates without
expecting confirmation.

Respond with EXACTLY ONE JSON object and nothing else -- no prose
before or after it, and no markdown fence around it unless that fence
wraps only the JSON itself. It must match this exact shape (only these
keys, at both levels -- there is no "closure" field in this version):

{
  "tool_used": <true or false, REQUIRED and explicit -- never omit this>,
  "reasoning_text": "<your overall reasoning, as plain text>",
  "candidates": [
    {
      "display": "<the exact preimage string P -- exact characters, exact case; this is the ONLY place you write P -- do not also hash or hex-encode it yourself, and do not repeat it in hex>",
      "derivation": "<one paragraph: how you got from the evidence to this exact string, and which of Phase 2, Phase 3, or Phase 3.2 licenses each step>",
      "rank": <integer, 1 = most confident; across ALL your candidates the ranks must be exactly 1..n with no duplicates or gaps, fixed now>
    }
  ]
}

Every field you write must be your actual, final, complete answer.
Never leave a placeholder, a "TODO", or a "FIXME" in any field -- if you
are not confident in a candidate, either omit it entirely or give it a
worse (higher-number) rank, rather than submitting an incomplete one.

Include at most 10 entries in "candidates". Do not add any field not
shown above, at either the top level or inside a candidate object -- in
particular, do not add a "closure" field; it is not part of this
version's schema.

Do not use any tool, for any purpose, at any point while answering this:
no file access, no shell or terminal commands, no code execution, no
calculator, no hashing (SHA-256 or otherwise), no encryption or
decryption, no attempt to test, verify, or decrypt any candidate against
anything, no reading or searching any local file or repository, no
reading environment variables, and no web search, web fetch, or lookup
of this puzzle, "GSMG", gsmg.io, Bitcoin puzzle solutions, or any
external source. Neither the ciphertext nor the address is included in
this prompt; do not attempt to locate either one anywhere else -- on
disk, in any repository, in your environment, or externally -- and do
not treat a tool's ability to search your surroundings as license to use
it here. Reason and answer using only your own understanding of the
material given above. If you used any tool for any reason while
answering, set "tool_used" to true and explain why in "reasoning_text"
-- such a submission will not be scored, but honest disclosure is still
required.
```

> [!info] Prompt pinned (2026-08-25, revised a third time)
> Full prompt (sealed packet inserted), 13,059 characters, SHA-256
> `8c6744db05ad5d7fdfb8027186d88a269e129e3740854ef5371a8dfcfc79afca`,
> produced by `build_solver_prompt()` and matched byte-for-byte against
> the committed `tools/gsmg/phase416_frozen_solver_prompt.txt` artifact
> in `self_test()`. `build_solver_prompt()` fails closed (raises) if the
> rendered text no longer matches this pinned hash/length or the
> committed artifact -- covered by its own `self_test()` fixture, which
> deliberately drifts the template and the pinned constants one at a
> time and confirms each is rejected. Revised three times from the
> original pin: first because the underlying packet grew by the added
> salt commitment; second and third because the prompt's own wording was
> corrected to stop claiming solvers have no access to the withheld
> targets -- "DO NOT INCLUDE" language rather than "cannot... even if you
> tried", and "cannot verify... from the material included in this
> prompt" rather than "you have neither the ciphertext nor the address"
> -- see "Threat model and residual exposure" above. `self_test()`
> asserts both retired phrases ("even if" and "you have neither") are
> absent.

**Parsing, invocation identity, and invocation cap**: unchanged from
Phase 414/415, verbatim -- see those documents for the full text.

## Corrected, simplified strict submission schema (frozen; reject wholesale, never coerce)

- **Top level**: exactly `tool_used` (boolean, never defaulted),
  `reasoning_text` (string), `candidates` (1-10 raw entries). Unchanged
  from Phase 414/415.
- **Each candidate**: exactly the keys `display`, `derivation`, `rank` --
  **no other key, including `closure`, is permitted at all.** Its mere
  presence voids the submission as an unexpected key, the same as any
  other schema deviation. `display` must be a non-empty string;
  `preimage_utf8_hex` is computed by this module as
  `display.encode("utf-8").hex()`, with no normalization of `display`
  first (unchanged from Phase 415's correction). `derivation` must be
  non-empty. `rank` must form an exact `1..n` permutation across the
  submission. No two candidates within one submission may encode to the
  same bytes.
- **Residue check**: `display`, `derivation`, and `reasoning_text` are
  each checked, case-insensitive, against `placeholder`, `todo`, and
  `fixme` only -- **not** `"..."`, which is removed from this phase's
  `RESIDUE_MARKERS` after producing two false positives in Phase 415,
  including against ellipsis punctuation appearing literally in the
  packet's own quoted plaintext.
- **Leakage scanning** remains fully recursive over every string value,
  unchanged from Phase 414/415.

## Canonicalization and convergence rule

Unchanged from Phase 415: `preimage_utf8_hex`, computed as above, is the
sole authoritative encoding; no whitespace stripping, case-folding,
separator normalization, or Unicode normalization-form conversion.

## Promotion rule (frozen; convergence only)

A candidate is tested against `P32TRAILING` if, and only if, **at least 2
of the 5 eligible submissions independently produce the byte-identical
`preimage_utf8_hex`.** There is no second (closure) path in this phase --
this is a preregistered simplification to a single promotion discipline,
not a claim that closure reasoning is impossible under a sealed target
(see "What changed, and why" above). `promote_candidates()`
is accordingly simpler than Phase 414/415's version: it computes votes
per `preimage_utf8_hex` and promotes any hex value with `>= 2` votes,
full stop.

## Candidate testing order, testing protocol, redaction contract, structural tiers, interpretation rules

**Unchanged from Phase 414/415, verbatim** -- reused by direct import of
`classify_plaintext()`, `STRUCTURAL_TIERS`,
`test_material_cbc/ecb/stream/secondary_families()`, `test_candidate()`,
`_promotion_sort_key()`, and the same `test_candidates()` batch-ordering
and stop-at-first-hit logic, from
`phase414_p32trailing_blinded_reconstruction_audit`. See that document
for the full text of each; nothing in this correction touches any of
them. The five-way interpretation rules (terminal hit / structural hit /
closed negative / `protocol_invalid` / genuine non-identifiability) are
likewise unchanged.

## Invocation 4 quarantine (carried forward from Phase 415's closure)

Per the standing decision recorded in Phase 415's own closure note and
`FINDINGS.md`: invocation 4's transcript is not opened beyond what the
orchestrator's own task-notification summary already disclosed, not
committed to this repository, and not copied into any documentation
beyond the aggregate description already recorded (invocation ID,
disposition, disclosed behavior, and the observation that three local
decrypt attempts returned ordinary PKCS#7-valid padding with no reported
structural or address-match signal). It is not evidence for or against
the puzzle and is not treated as such in this phase or any future one.

## Deliverable

`tools/gsmg/phase416_p32trailing_sealed_target_reconstruction_audit.py`:
`build_sealed_evidence_packet()` (deterministic, pinned SHA-256,
structurally locates and verifies the withheld salt/ciphertext/address
against their pinned commitments rather than trusting a hardcoded
offset); `_verify_commitments()` (recomputes all three commitments --
salt, ciphertext, address -- from the live `BLOBS`/`PRIZE_ADDRESS`
values on every packet build, so a change to any one raises loudly
rather than silently sealing the wrong target); `_render_solver_prompt()` (unchecked template
rendering, private, used only for intentional regeneration) /
`build_solver_prompt()` (the execution-facing function -- fails closed,
raising `AssertionError`, if the rendered prompt's length, hash, or
byte-for-byte match against the committed
`tools/gsmg/phase416_frozen_solver_prompt.txt` artifact has drifted from
the pinned constants, whether from an edited template or an edited
packet; every invocation must call this, never the private renderer) /
`write_solver_prompt()` (regenerates the committed artifact from the
unchecked renderer, for deliberate re-pinning only) -- added specifically
so the prompt cannot hand-copy-drift the way Phase 414's did, and so a
drifted template fails loudly rather than silently producing a sendable
prompt; `validate_submission_schema()` (the corrected, closure-free
schema above); `eligible_submissions()` / `evaluate_panel()` (redefined
only because they resolve `validate_submission_schema()` by name in
their own module); `promote_candidates()` (convergence-only); everything
else (`parse_submission()`, `blinding_violations()`, the full redacted
oracle-testing stack, `test_candidates()`'s deterministic ordering)
reused unchanged by direct import from
`phase414_p32trailing_blinded_reconstruction_audit`. `self_test()`
covers: the sealed packet's pinned hash and the structural absence of
the real prize/halving addresses and every length-40 contiguous slice of
the real base64 blob (every starting offset); that tampering the salt
alone (leaving the ciphertext untouched) is caught by
`_verify_commitments()`; the frozen prompt's pinned hash/length and its
byte-exact match against the committed artifact; that `build_solver_prompt()`
fails closed -- a drifted template, a stale pinned hash, and a stale
pinned length are each independently tested and confirmed to raise, with
a final call confirming success again once restored; that the prompt
text says the targets are "not included in this prompt" and never claims
a solver "cannot... even if it tried" or "you have neither the
ciphertext nor the address"; `closure` as a
candidate key is rejected outright; `preimage_utf8_hex` is computed
correctly and never solver-provided; `"..."` no longer triggers residue
rejection (including inside a literal quotation of the packet's own
ellipsis-bearing text) while `placeholder`/`todo`/`fixme` still do; no
implicit whitespace normalization; duplicate detection over encoded
bytes; `tool_used` exclusion retained as defense in depth; cap/panel-
validity parity with Phase 414/415; invocation-identity replay-safety;
and an end-to-end smoke test through the real convergence-promotion and
oracle-testing pipeline against a synthetic (never the real
`P32TRAILING`) blob. A regression test is added to
`tools/gsmg/test_recent_audits.py`. Results are recorded in
`tools/gsmg/FINDINGS.md` as Phase 416. The theory registry is updated
only if a branch actually changes a tracked theory's status.

## Related notes

- [Phase 415 P32TRAILING Blinded Independent Reconstruction, Corrected Pre-Registration](2026-08-25%20-%20Phase%20415%20P32TRAILING%20Blinded%20Independent%20Reconstruction%20Corrected%20Pre-Registration.md) (closed `protocol_invalid`; invocation 4 quarantine recorded there)
- [Phase 414 P32TRAILING Blinded Independent Reconstruction Pre-Registration](2026-08-25%20-%20Phase%20414%20P32TRAILING%20Blinded%20Independent%20Reconstruction%20Pre-Registration.md) (closed `protocol_invalid`; original evidence packet and unchanged protocol elements defined there)
- [P32 Trailing Sibling-Output Password Path](2026-08-14%20-%20P32%20Trailing%20Sibling-Output%20Password%20Path.md)
- [Solved Vector Toolchain Provenance Audit](../GSMG_SOLVED_VECTOR_TOOLCHAIN_PROVENANCE_AUDIT.md) (Phase 410)
- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
