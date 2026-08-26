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

# Phase 421 — P32TRAILING Escalated One-File Bootstrap Pre-Registration

> [!caution] Frozen before implementation; no panel execution authorized
> Phase 420 closed `protocol_invalid` because all eight default-sandbox reads
> failed before prompt delivery. Phase 421 changes only the tool-call envelope:
> the same read-only command is requested with `sandbox_permissions` set to
> `require_escalated`. Implementation must be committed separately. A later
> explicit authorization is required to launch the panel.

## Pre-registration diagnostic

Before this document was written, one fresh, no-history invocation was labeled
`phase421_escalated_read_diagnostic` and asked to read only the 423-character
Phase 420 launcher using one escalated `sed` call. It succeeded and reported the
launcher's first line. It received no puzzle evidence or solver prompt, was not
asked for candidates, and is permanently excluded from Phase 421's invocation
IDs, eligibility, votes, and eight-ID cap. Its sole purpose was to establish
that the corrected execution envelope works before freezing another panel.

## Inherited experiment

Phase 421 asks Phase 418/420's unchanged question about convergent reconstruction
of a P32TRAILING preimage from the solution-complete Phase-3.2 evidence.

It imports without modification:

- Phase 420's committed 14,717-character, 219-line solver prompt;
- Phase 418's byte-identical evidence packet and sealed-target commitments;
- Phase 420's four-key disclosure schema;
- five eligible fresh/no-history invocations within eight preassigned IDs;
- exact UTF-8 canonicalization and the two-vote convergence gate;
- Phase 270 duplicate classification;
- Phase 416's redacted evaluator; and
- Phase 418's six result branches and stopping rules.

The macro-clue experiment remains blocked and out of scope.

## Exact launcher and permitted tool call

The implementation must commit and pin a short Phase 421 launcher containing
the following instructions and no puzzle evidence:

```text
Read the complete solver prompt using exactly one exec_command tool call with
these parameters and no other tool call:
- cmd: sed -n '1,260p' /home/loginwashere/projects/gsmgio-5btc-puzzle/tools/gsmg/phase420_frozen_solver_prompt.txt
- workdir: /home/loginwashere/projects/gsmgio-5btc-puzzle
- sandbox_permissions: require_escalated
- justification: May I perform the preregistered read-only prompt bootstrap outside the unavailable sandbox?

The read above is the only permitted bootstrap action. Follow the file exactly.
Return only the JSON object it requests. Do not inspect any other file, run any
other command, use any other tool, or retrieve external information.
```

Every solver receives those exact bytes. The tool-call command still reads only
the Phase 420 prompt file; escalation changes sandbox execution, not filesystem
scope or prompt content. No `prefix_rule` is requested. Any denial or failure
consumes the invocation ID and is ineligible.

The implementation must pin the launcher's UTF-8 length and SHA-256, verify the
Phase 420 prompt byte-for-byte through its existing fail-closed builder, and
assert that the fixed `1,260p` range covers all 219 lines.

## Eligibility and enforcement boundary

Phase 420's schema and record validator apply unchanged. Eligible solvers must
report `bootstrap_read_used: true` and `other_tool_used: false`. If tool-call
telemetry is exposed, it must show exactly the permitted read; if the
orchestrator receives no telemetry, the ledger records
`tool_telemetry_available: false` and compliance is self-attested.

Escalation is not one-file filesystem isolation. A solver process could
technically request or attempt other access. The protocol constrains behavior
by exact instruction and disclosure, and the result must not claim stronger
containment than the available telemetry proves.

## Outcomes and stopping rule

Phase 420's panel classification, duplicate handling, oracle evaluation,
redaction, and mutually exclusive outcome branches are imported unchanged.
Launcher drift, prompt drift, a different command or execution envelope, or
fewer than five eligible submissions within eight IDs yields
`protocol_invalid`. No malformed response is repaired or reused.

Terminal or structural hits stop the batch under the inherited rules. A
negative, duplicate-only, or no-convergence result has exactly Phase 418's
preregistered interpretation. Prize handling and external action remain out of
scope.

## Required implementation controls

Before execution authorization, the separately committed implementation must:

1. pin and byte-verify the Phase 421 launcher;
2. prove the imported Phase 420 prompt and Phase 418 evidence commitments;
3. assert the exact command, workdir, escalation mode, and justification;
4. reuse Phase 420 parsing, revised schema, eligibility, panel, classification,
   and redaction code by identity;
5. test drift rejection, invocation IDs 1 and 8, cap failure, and a five-record
   panel fixture reaching the inherited evaluator;
6. run focused Phase 416/418/420/421 regressions, compilation, JSON checks, and
   `git diff --check`; and
7. report zero Phase 421 panel invocations during implementation.

No panel invocation is authorized by this document.
