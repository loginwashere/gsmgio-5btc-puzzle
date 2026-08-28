---
type: audit
phase: 435
date: 2026-08-28
status: complete
result: negative
disposition: closed-exact-reading
script: tools/gsmg/phase435_be_required_operator_selector_audit.py
---

# Phase 435 — `BE REQUIRED` Operator-Selector Audit

The doubled phrase is real, but it does not select a new operation.

This audit was frozen before execution in
[the Phase 435 protocol](Brainstorms/2026-08-28%20-%20Phase%20435%20BE%20REQUIRED%20Operator-Selector%20Audit%20Protocol.md).
It freshly derived the 1,539 connected Phase 3.2.1 letters from the
authenticated Phase 3.2 payload, then admitted README spaces only after those
letters matched exactly. It generated no passwords, queried no blob oracle,
and did not inspect or touch the GPU run.

## Exact counts

| Unit | Count or positions |
|---|---|
| Connected `BEREQUIRED` | 2 occurrences, zero-based 1131 and 1277; one-based 1132 and 1278 |
| README whole-word `BE REQUIRED` | word-pair starts zero-based 256 and 283; one-based 257 and 284 |
| Whole-word `BE` | 3 |
| Raw connected substring `BE` | 7 |
| Repeated word bigrams | 9 |
| Repeated word trigrams | 0 |

The first occurrence is inside the Matrix-derived sentence skeleton:

```text
AFTER WHICH YOU WILL BE REQUIRED TO SELECT
```

The second is inside creator-added language absent from the film:

```text
BRUTE FORCING MIGHT BE REQUIRED
```

This makes the repetition noticeable, but not unique under the frozen
mixed-provenance comparator. `RESULT IN` also repeats twice, once in a
creator-added consequence and once in the inherited extinction sentence.

## Registered-mechanism comparison

| Mechanism | Why it does not consume two `BE REQUIRED` markers |
|---|---|
| Phase 3.2.2 escapes `(1,4)` | Numeric checkerboard escapes, not phrase markers |
| DBBI `B/BE` tokenization | Token alphabet/segmentation, with no instruction to use exactly two `BE`s |
| Split-final-`BE` guide | One terminal `BE` token becomes `B`,`E`; it is not two `BE` tokens |
| Architect `BUT/HYE` choice | Already solved dialogue boundary with different markers and consumer |

No registered unresolved consumer independently asks for two markers or two
rails. The phrase also fails to specify an operand, selection boundary,
direction, indexing convention, or serialization. Only the first frozen
promotion condition—exact repetition with authenticated letters—passes.

## Verdict

`BE REQUIRED` is a genuine textual feature and a reasonable reason to look,
but it is **not an actionable operator selector**. This closes the exact
"two `BE REQUIRED` occurrences select an operation" reading. Reopening it
requires new evidence that independently fixes both an operation and a
two-marker consumer; it cannot be reopened merely by associating the letters
`B/E` with the already-known guide.

The source-bound blue/yellow `AND/OR` string experiment therefore remains
gated. At the set level, blue and yellow already partition the 23 endpoints,
so union gives all 23 and intersection gives none; extracting strings still
requires an independently fixed source, direction, boundary, and mapping.

Reproduce:

```bash
python3 tools/gsmg/phase435_be_required_operator_selector_audit.py --self-test
python3 tools/gsmg/phase435_be_required_operator_selector_audit.py \
  --output tools/gsmg/phase435_result.json
```
