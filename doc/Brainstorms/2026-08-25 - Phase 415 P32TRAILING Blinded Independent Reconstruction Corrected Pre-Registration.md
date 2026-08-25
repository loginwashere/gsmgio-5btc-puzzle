---
type: worksheet
status: live
date: 2026-08-25
topics:
  - brainstorm
  - p32trailing
  - blinded-experiment
  - external-solvers
  - evidence-acquisition
  - theory-registry
---

# Phase 415 — P32TRAILING Blinded Independent Reconstruction, Corrected Pre-Registration

> [!caution] Prepared before any solver is invoked
> This document supersedes
> [Phase 414](2026-08-25%20-%20Phase%20414%20P32TRAILING%20Blinded%20Independent%20Reconstruction%20Pre-Registration.md),
> which is closed `protocol_invalid`: 3 of its first 5 invocations failed
> schema validation, all three tracing to one avoidable cause (see below).
> No candidate from Phase 414 is carried forward or tested here -- the
> panel is re-run entirely from fresh, clean-context invocations. Phase 414's
> evidence packet, promotion rule, testing protocol, redaction contract,
> invocation-identity/cap machinery, and interpretation rules are inherited
> **unchanged** and are not re-derived in this document except where noted;
> only the submission schema and frozen prompt are corrected.

## What changed, and why

Phase 414 required each solver to submit, per candidate, both a `display`
string (the preimage itself) and a separately hand-computed
`preimage_utf8_hex` (`display`'s UTF-8 bytes as lowercase hex), with the
hex field declared authoritative. Of the first 5 invocations, 3 failed
`parse_submission()`/`validate_submission_schema()` -- confirmed by
actually running those functions against the exact raw text, not by
inspection -- and all three failures were on that one field: a stray
Python-syntax fragment (`.replace(" ", "")`) left uncomputed inside what
should have been a pure hex string, and a garbled hex value trailing off
into literal `"...INVALID"`/`"PLACEHOLDER"` text.

`preimage_utf8_hex` carries **no interpretive content** -- it is a
deterministic, non-semantic transformation of a string the solver already
stated exactly and unambiguously in `display` (a parsed JSON string has no
inherent whitespace/case ambiguity the way scraped prose might). The field
existed only to make an already-exact value doubly precise, and instead
introduced a large, avoidable failure surface: solvers hand-computing long
hex encodings without tool access, under a task that has nothing to do
with the actual reasoning being tested (candidate derivation). This is a
schema/instrument defect, not a finding about `P32TRAILING`.

**Corrections, exactly two:**

1. **`preimage_utf8_hex` is no longer a solver-provided field.** The
   frozen prompt asks only for `display`. This module computes
   `preimage_utf8_hex` itself, mechanically, as
   `display.encode("utf-8").hex()` -- no trimming, case-folding,
   separator normalization, or Unicode normalization-form conversion of
   `display` first. A submission that still includes a
   `preimage_utf8_hex` key is rejected wholesale as an unexpected key
   (the strict "only these keys" schema check applies exactly as before;
   this is not a new leniency).
2. **Unfinished template residue is a schema violation.** A literal,
   case-insensitive `placeholder`, `todo`, `fixme`, or `...` (three-dot
   ellipsis) appearing in `display`, `derivation`, `reasoning_text`, or a
   present closure's `instruction_quote` voids the whole submission. Such
   residue is syntactically valid JSON (a non-empty string) and would
   otherwise silently pass through as a real, if nonsense, candidate --
   this closes exactly the gap that let a `"derivation": "PLACEHOLDER"`
   -shaped submission slip past Phase 414's schema in principle, even
   though Phase 414 actually rejected that one submission on its
   separately-garbled hex field. The frozen prompt is also strengthened
   with an explicit instruction against leaving any field unfinished.

**Everything else is unchanged from Phase 414**, reused by direct import
from `phase414_p32trailing_blinded_reconstruction_audit` where the code
does not depend on the schema: the evidence packet and its pinned SHA-256,
`blinding_violations()`/`submission_full_text()`/`_collect_strings()`,
`validate_closure()` and the (still empty)
`QUALIFYING_CLOSURE_INSTRUCTION_SPANS` allowlist, `promote_candidates()`,
the redacted `classify_plaintext()` and structural tiers, the
`test_material_cbc/ecb/stream/secondary_families()` oracle wrapper and its
no-logging/stop-at-first-hit guarantees, `test_candidate()`'s frozen
`H-exact -> H-remaining-broad -> P-broad` order, `_promotion_sort_key()`
and `test_candidates()`'s deterministic batch order, `parse_submission()`
and its fullmatch-anchored fence/duplicate-key-rejecting mechanics, and
the population target (5), invocation cap (8), and convergence threshold
(2) constants. Only `validate_submission_schema()`, `eligible_submissions()`,
and `evaluate_panel()` are redefined in this phase's own module -- the
latter two only because they call `validate_submission_schema()` by name
within their defining module's own namespace, not because their logic
changed.

## Solver protocol

Unchanged from Phase 414: population target 5 eligible submissions, from
clean-context agent invocations with no inherited turns from this
project's history; the same "independent is qualified, not claimed
outright" caveat; the same two blinding backstops (disclosed-tool-use
exclusion, post-hoc forbidden-vocabulary/phase-number check); the same
invocation-identity ledger (orchestrator-assigned ID, dict-keyed, never a
bare list); the same 8-invocation cap with `protocol_invalid` as an
explicit, predeclared outcome, cap-enforced before panel readiness is even
considered.

**Frozen prompt (verbatim, sent unmodified to all invocations):**

```text
You are looking at a real, currently-unsolved piece of an authenticated
cryptographic puzzle. Below is the complete evidence you have: an
already-decrypted plaintext from earlier, solved stages of the same
puzzle (labeled Phase 2, Phase 3, Phase 3.2), three fully worked
examples of how those earlier stages each turned some piece of solved
text into the next stage's AES password, and the final output
requirement.

[EVIDENCE PACKET INSERTED HERE VERBATIM]

Your task: propose up to 10 candidate PREIMAGES for the one remaining
encrypted block (the final base64 block in the plaintext above). A
preimage is the string you believe should be SHA-256 hashed to become
the actual AES password -- per the recipe above, the password itself is
H = sha256(P).hexdigest(), not P. Do not submit an already-hashed
string as a candidate; submit P, the thing to be hashed.

Respond with EXACTLY ONE JSON object and nothing else -- no prose
before or after it, and no markdown fence around it unless that fence
wraps only the JSON itself. It must match this exact shape (only these
keys, at both levels):

{
  "tool_used": <true or false, REQUIRED and explicit -- never omit this>,
  "reasoning_text": "<your overall reasoning, as plain text>",
  "candidates": [
    {
      "display": "<the exact preimage string P -- exact characters, exact case; this is the ONLY place you write P -- do not also hash or hex-encode it yourself, and do not repeat it in hex>",
      "derivation": "<one paragraph: how you got from the evidence to this exact string, and which of Phase 2, Phase 3, or Phase 3.2 licenses each step>",
      "rank": <integer, 1 = most confident; across ALL your candidates the ranks must be exactly 1..n with no duplicates or gaps, fixed now>,
      "closure": null
    }
  ]
}

Every field you write must be your actual, final, complete answer.
Never leave a placeholder, a "TODO", a "FIXME", an ellipsis ("..."), or
any other unfinished residue in any field -- if you are not confident in
a candidate, either omit it entirely or give it a worse (higher-number)
rank, rather than submitting an incomplete one.

Include at most 10 entries in "candidates". Only set "closure" to
something other than null if you believe every parameter of that one
candidate's derivation is fixed by an explicit instruction elsewhere in
the packet with zero remaining alternatives -- in that case, replace it
with an object of exactly this shape: {"instruction_offset_start":
<int>, "instruction_offset_end": <int>, "instruction_quote": "<the
verbatim text at that exact character range in the packet above>",
"token_spans": [[<start>, <end>], ...], "zero_alternatives": true}.
Otherwise leave "closure" as null. Do not add any field not shown
above, at either the top level or inside a candidate or closure object.

Do not use any tool (file access, shell commands, web search, web
fetch, or any other tool) to look up this puzzle, "GSMG", gsmg.io,
Bitcoin puzzle solutions, or any external source. Work only from the
material given above. If you used any tool for any reason while
answering, set "tool_used" to true and explain why in "reasoning_text"
-- such a submission will not be scored, but honest disclosure is still
required.
```

## Corrected strict submission schema (frozen; reject wholesale, never coerce)

Identical to Phase 414's except as follows:

- **Each candidate**: exactly the keys `display`, `derivation`, `rank`,
  and optionally `closure` -- `preimage_utf8_hex` is **not** a permitted
  key; its presence voids the submission the same as any other
  unexpected key would. `display` must be a non-empty string.
  `preimage_utf8_hex` is computed by this module as
  `display.encode("utf-8").hex()`, with no normalization of `display`
  first -- two candidates whose `display` differs only in whitespace,
  case, or Unicode normalization form therefore encode to different
  bytes and are never treated as the same candidate.
- **Residue check.** `display`, `derivation`, `reasoning_text`, and (if
  present) `closure.instruction_quote` are each checked, case-insensitive,
  against the literal substrings `placeholder`, `todo`, `fixme`, and
  `...` -- a match voids the whole submission. This is necessary but not
  exhaustive (a solver could in principle still submit vacuous but
  residue-free text); it closes the specific, observed failure mode, not
  every conceivable one.
- **Duplicate check** is now stated over encoded bytes rather than a
  solver-supplied field: no two candidates within one submission may
  encode (`display.encode("utf-8")`) to the same bytes.
- All other checks (top-level key set, `tool_used` an explicit boolean,
  1..10 raw candidates before dedup, `derivation` non-empty, `rank` an
  exact `1..n` permutation, closure key-set/type/offset/`zero_alternatives
  is True`/non-empty-quote/`token_spans` checks) are unchanged from Phase
  414, verbatim.

## Canonicalization and convergence rule

**`preimage_utf8_hex`, computed as above, is the sole authoritative
encoding** -- unchanged in spirit from Phase 414, only in how the value is
obtained (computed by this module from `display`, never solver-supplied).
No whitespace stripping, no case-folding, no separator normalization, no
Unicode normalization-form conversion of `display` before encoding. Two
candidates converge only if their computed `preimage_utf8_hex` values are
byte-identical, drawn only from schema-valid submissions.

## Promotion rule, candidate testing order, testing protocol, redaction contract, structural tiers, interpretation rules

**Unchanged from Phase 414, verbatim** -- reused by direct import of
`promote_candidates()`, `validate_closure()`,
`QUALIFYING_CLOSURE_INSTRUCTION_SPANS` (still empty; no new preregistered
span has been added), `classify_plaintext()`, `STRUCTURAL_TIERS`,
`test_material_cbc/ecb/stream/secondary_families()`,
`test_candidate()`, `_promotion_sort_key()`, and `test_candidates()` from
`phase414_p32trailing_blinded_reconstruction_audit`. See that document for
the full text of each; nothing in this correction touches any of them.

## Deliverable

`tools/gsmg/phase415_p32trailing_blinded_reconstruction_audit.py`: imports
the unaffected pipeline directly from
`phase414_p32trailing_blinded_reconstruction_audit` (evidence packet,
`blinding_violations()`, `validate_closure()`, `promote_candidates()`, the
full oracle-testing stack, `parse_submission()`); defines its own
`validate_submission_schema()` (drops `preimage_utf8_hex` as a permitted
key, computes it mechanically from `display`, adds the residue check, and
restates duplicate-detection over encoded bytes) and, because they call
`validate_submission_schema()` by name in their own defining module, its
own `eligible_submissions()` and `evaluate_panel()` -- otherwise identical
to Phase 414's. `self_test()` covers: a valid submission without
`preimage_utf8_hex` is accepted and its hex is computed correctly; a
submission that still includes `preimage_utf8_hex` is rejected as an
unexpected key; each of `placeholder`/`todo`/`fixme`/`...` is rejected in
turn, individually, in each of `display`, `derivation`, `reasoning_text`,
and `closure.instruction_quote`; two `display` strings differing only by
trailing whitespace, or by Unicode NFC vs. NFD normalization form of the
same visual text, encode to different bytes and are not treated as
duplicates or as convergent; the duplicate-within-submission check fires
on identical `display` bytes; the invocation-cap/panel-validity behavior
matches Phase 414's (reused test shapes, re-verified against the new
schema); and an end-to-end smoke test feeding phase415-shaped eligible
submissions through the directly-imported `promote_candidates()` /
`test_candidates()` pipeline against a synthetic blob. A regression test
is added to `tools/gsmg/test_recent_audits.py`. Results (including this
phase's own panel outcome) are recorded in `tools/gsmg/FINDINGS.md` as
Phase 415. The theory registry is updated only if a branch actually
changes a tracked theory's status.

## Related notes

- [Phase 414 P32TRAILING Blinded Independent Reconstruction Pre-Registration](2026-08-25%20-%20Phase%20414%20P32TRAILING%20Blinded%20Independent%20Reconstruction%20Pre-Registration.md) (closed `protocol_invalid`; evidence packet and unchanged protocol elements defined there)
- [P32 Trailing Sibling-Output Password Path](2026-08-14%20-%20P32%20Trailing%20Sibling-Output%20Password%20Path.md)
- [Solved Vector Toolchain Provenance Audit](../GSMG_SOLVED_VECTOR_TOOLCHAIN_PROVENANCE_AUDIT.md) (Phase 410)
- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
