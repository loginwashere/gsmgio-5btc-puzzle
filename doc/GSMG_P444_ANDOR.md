---
type: audit
phase: 444
date: 2026-08-29
status: complete
result: bounded-two-source-and-or-rail-family-negative
disposition: closed-bounded-reading
script: tools/gsmg/phase444_source_bound_and_or_rail_audit.py
related_phases:
  - 270
  - 434
  - 435
  - 437
  - 442
  - 443
---

# Phase 444 — Source-Bound AND/OR Rail Audit

## Why this branch became executable

Phases 434, 435, and 437 correctly kept the blue/yellow AND/OR string
experiment gated: a source, endpoint-to-character mapping, direction,
boundary, and serialization were not all fixed.

Phases 442 and 443 changed that local state. They identified and tested two
pure single-case Phase-3.2.1 letter streams under the same zero-deviation
split-final-BE prime rule:

- the 1,539-letter CP1141 Beaufort ciphertext;
- the 1,539-letter decoded Architect plaintext, answer_321.

That rule fixes 23 forward events partitioned into exactly 16 blue selections
and 7 yellow digraph selections. Phase 444 therefore freezes and tests the
smallest conventional reading of SIXTEEN ... AND OR SEVEN:

- OR means blue alone or yellow alone;
- AND means blue followed by yellow in the sentence's 16-then-7 order;
- the original event-order weave is a regression already covered by Phases
  442 and 443 and is not resubmitted.

The protocol was frozen before oracle evaluation:

[Phase 444 Source-Bound AND/OR Rail Protocol](Brainstorms/2026-08-29%20-%20Phase%20444%20Source-Bound%20AND-OR%20Rail%20Protocol.md).

## Deterministic rails

| Source | Blue-only: 16 events | Yellow-only: 7 digraphs | Blue then yellow | Intertwined regression |
|---|---|---|---|---|
| CP1141 | tkpmwzjzfytfaoeu | hlputunljfklww | tkpmwzjzfytfaoeuhlputunljfklww | tkpmhlwzjputuzfytnlfajfkloewwu |
| answer_321 | OULFSFRNCQANETIA | THINANNIROINLE | OULFSFRNCQANETIATHINANNIROINLE | OULFTHSFRINANNCQANINEROINTILEA |

Both intertwined regressions exactly reproduce the Phase 442 and Phase 443
selections. They were assertions only, not new password candidates.

## Sealed candidate inventory

Each of the three new rail serializations received Phase 442's unchanged
three-form outer grammar:

1. rail alone;
2. rail followed by answer_322;
3. answer_321 followed by rail.

The final inventory was:

    2 sources x 3 rails x 3 forms = 18 candidates
    18 candidates x raw/SHA-256-hex = 36 materials
    36 materials x 6 fixed specifications = 216 trials

All 36 materials had zero overlap with the complete Phase 270, 442, and 443
material inventories.

## Result

    candidate count:                  18
    material count:                   36
    overlap with Phase 270:            0
    overlap with Phase 442:            0
    overlap with Phase 443:            0
    new material count:               36
    structural oracle trials:        216
    exact padding hits:                0

No candidate produced the exact fifth AES plaintext block of sixteen 0x10
bytes required by the authenticated 64-byte two-key interpretation.

## Verdict

The bounded two-source AND/OR rail family is negative. The source-bound branch
left open by Phases 434, 435, and 437 is no longer merely unexecuted under this
minimal serialization: blue alone, yellow alone, blue-then-yellow, and the
already-tested intertwined weave are all covered for both precedent-eligible
letter streams.

This does not prove that AND/OR denotes string concatenation or independent
rail choice. Yellow-first, reversal, alternate interleaving, other prime
operators, and other source representations remain logically possible, but
none is fixed by current evidence and none was licensed by this protocol.
Reopening requires evidence selecting one of those alternatives.

No GPU work occurred. No live-leader or P32TRAILING state was mutated; this
was a read-only decrypt attempt against already-authenticated ciphertext.

Reproduce:

    python3 tools/gsmg/phase444_source_bound_and_or_rail_audit.py --self-test
    python3 tools/gsmg/phase444_source_bound_and_or_rail_audit.py \
      --json tools/gsmg/phase444_result.json
