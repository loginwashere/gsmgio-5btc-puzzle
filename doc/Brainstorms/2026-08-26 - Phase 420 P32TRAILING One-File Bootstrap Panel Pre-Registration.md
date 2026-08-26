---
type: worksheet
status: frozen
date: 2026-08-26
topics:
  - brainstorm
  - p32trailing
  - blinded-experiment
  - external-solvers
  - prompt-delivery
---

# Phase 420 — P32TRAILING One-File Bootstrap Panel Pre-Registration

> [!caution] Frozen before implementation; no solver execution authorized
> Phase 418's solution-complete protocol and artifacts remain unchanged and
> unexecuted. Its 14,441-character prompt cannot be reliably transported in a
> fresh delegated task, while a fresh solver cannot receive it through inherited
> history. Phase 420 changes only prompt delivery and the tool-disclosure schema.
> Implementation, fixtures, and exact artifacts must be committed separately.
> Solver execution requires a later explicit authorization.

## Question and inherited scientific design

Phase 420 asks Phase 418's exact question: when the calibrated panel receives
the solution-complete Phase-3.2 state, do at least two of five eligible fresh
solvers converge byte-for-byte on a genuinely new preimage that opens
`P32TRAILING`?

All scientific controls are inherited unchanged from Phase 418:

- the solution-complete evidence and its source commitments;
- the sealed P32 target and prize-address commitments;
- five eligible fresh/no-history invocations within eight preassigned IDs;
- one vote per invocation and the two-vote convergence gate;
- exact UTF-8 candidate canonicalization and deterministic ordering;
- the exact Phase 270 duplicate classifier;
- the Phase 416 redacted evaluator for genuinely new promotions; and
- the six mutually exclusive result branches and stopping rules.

The creator macro-clue experiment remains out of scope and blocked.

## Why this is a new phase

Phase 418 requires its full frozen prompt to be sent directly to every solver
and prohibits all tools. The current delegated-task transport cannot reliably
carry that long prompt, and the no-history solvers cannot otherwise obtain it.
No Phase 418 invocation was launched, so Phase 418 is not a failed or
`protocol_invalid` experiment; it is implemented but operationally unexecuted.

Changing its delivery rule in place would violate its frozen protocol. Phase
420 therefore introduces a narrow bootstrap exception: each solver may use one
read-only shell call to read one committed prompt artifact at one exact absolute
path. No puzzle data appears in the short launcher beyond that path and the
bootstrap rules.

## Frozen prompt and launcher

The implementation must generate and commit
`tools/gsmg/phase420_frozen_solver_prompt.txt`. Its evidence content must be
byte-identical to Phase 418's evidence packet. Its task language may differ only
where needed to describe the bootstrap exception and revised disclosure fields.
The implementation must pin the prompt's UTF-8 byte length and SHA-256 digest
and fail closed on drift.

Every invocation receives the same short launcher, also committed and pinned:

```text
Read the complete solver prompt using exactly one shell tool call and no other
tool: sed -n '1,260p' /home/loginwashere/projects/gsmgio-5btc-puzzle/tools/gsmg/phase420_frozen_solver_prompt.txt

The read above is the only permitted bootstrap action. Follow the file exactly.
Return only the JSON object it requests. Do not inspect any other file, run any
other command, use any other tool, or retrieve external information.
```

The exact permitted command is:

```text
sed -n '1,260p' /home/loginwashere/projects/gsmgio-5btc-puzzle/tools/gsmg/phase420_frozen_solver_prompt.txt
```

The file must contain at most 260 lines so this one command returns it in full.
The launcher is byte-identical across invocations. Invocation identity comes
from the orchestrator-assigned task name and ledger, not launcher text.

If the execution environment cannot perform that exact read as one call, the
invocation is ineligible. It may be backfilled with the same launcher under the
existing eight-ID cap. The launcher and prompt may not be split, shortened,
paraphrased, pasted through inherited conversation history, or repaired after a
response.

## Revised submission schema

The Phase 420 top-level object has exactly four keys:

```json
{
  "bootstrap_read_used": true,
  "other_tool_used": false,
  "reasoning_text": "final packet-local reasoning",
  "candidates": [
    {
      "display": "exact preimage P",
      "derivation": "operation and disclosed source licensing every byte",
      "rank": 1
    }
  ]
}
```

`bootstrap_read_used` and `other_tool_used` must be explicit booleans. An
eligible submission must report `bootstrap_read_used: true` and
`other_tool_used: false`. Phase 418's candidate schema, 1..10 limit, contiguous
ranks, duplicate rejection, UTF-8 byte preservation, residue checks, duplicate
JSON-key rejection, and prose-outside-JSON rejection remain unchanged.

The prompt defines the bootstrap read as tool use. A solver must not report it
as `other_tool_used`. Any second command, filesystem read, repository search,
code/calculator/hash/cipher operation, environment inspection, web access, or
other tool for any reason requires `other_tool_used: true` and excludes the
submission.

## Enforcement boundary

This is an instruction-level capability restriction, not an OS-enforced
one-file sandbox. The solver process can technically access the shared
repository. Phase 420 can validate the submitted disclosure and any tool-call
metadata exposed to the orchestrator, but it cannot prove that undeclared reads
were physically impossible. This limitation must appear in the result.

The implementation must represent recorded tool calls, when the invocation
mechanism exposes them, as an ordered list in each ledger record. Eligibility
requires either:

1. one recorded shell call whose command exactly equals the permitted command
   and no other recorded call; or
2. when the mechanism exposes no call metadata, an explicit
   `tool_telemetry_available: false` marker plus the required self-disclosure.

The second case is eligible but must be reported as self-attested bootstrap
compliance, never as independently verified one-file isolation. A contradiction
between available telemetry and the disclosure rejects the submission.

## Frozen outcome logic

After eligibility, Phase 420 imports Phase 418's panel evaluation, promotion,
Phase 270 classification, redacted oracle evaluation, branch ordering, and
stopping rules without modification. The only new `protocol_invalid` causes
are launcher/prompt drift and bootstrap-policy invariant failure.

No raw candidate, target plaintext, password, private key, or address may enter
the public result artifact or `FINDINGS.md`. Raw solver responses remain only in
the reproducibility ledger, as in Phase 418.

## Required implementation controls

Before execution authorization, the separately committed implementation must:

1. prove Phase 420's evidence packet is byte-identical to Phase 418's;
2. pin and verify the new prompt and launcher artifacts byte-for-byte;
3. prove the prompt fits within the launcher's fixed 260-line read;
4. validate the revised four-key schema and all Phase 418 candidate invariants;
5. test eligible exact-bootstrap, missing-bootstrap, other-tool, extra-call,
   wrong-command, contradictory-telemetry, and unavailable-telemetry cases;
6. prove Phase 418's panel, duplicate, evaluator, result-branch, and redaction
   behavior is imported unchanged after eligibility;
7. run focused Phase 416-420 regressions, compilation, JSON validation, and
   `git diff --check`; and
8. report zero solver invocations during implementation and testing.

No solver invocation or external action is authorized by this preregistration.
