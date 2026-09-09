---
type: audit
phase: 485
date: 2026-09-07
status: complete
result: conditional-multiplication-selector
disposition: structural-positive-provenance-pending-consumer-open
script: tools/gsmg/phase485_ring_endpoint_747474_audit.py
---

# Phase 485 — Ring endpoints plus `747474` produce multiplication

## Question

Does the solved 14×14 first-piece spiral provide a mechanical six-character
source to which the supplied sequence `747474` can be applied, and does the
result select an operation already present in the project?

This is a retrospective verification of an observed construction, not a
preregistered discovery experiment. Two inputs remain interpretive rather than
authenticated: reading `archi`/arch as the nested structural rings and taking
the last character touched by every completed ring; and the user-supplied
literal `747474`, which has no pinned repository provenance. Conclusions
depending on either remain conditional.

## Fixed source geometry

The already-authenticated top-left, counter-clockwise inward spiral divides
the 14×14 grid into rings of sizes:

```text
14, 12, 10, 8, 6, 4, 2
```

Their lengths are `52,44,36,28,20,12,4`, totaling 196. The first six total
exactly 192 cells—the 24 MSB-first ASCII bytes decoding to
`gsmg.io/theseedisplanted`. Their final spiral positions are:

| Ring | End index | Character | Endpoint bit offset, zero-based |
|---:|---:|---:|---:|
| 14×14 | 51 | `o` | 3 |
| 12×12 | 95 | `s` | 7 |
| 10×10 | 131 | `s` | 3 |
| 8×8 | 159 | `a` | 7 |
| 6×6 | 179 | `e` | 3 |
| 4×4 | 191 | `d` | 7 |

Thus the final character touched by every complete text-bearing ring is
mechanically `ossaed`. The seventh 2×2 ring is positions 192–195, the exact
four-bit residual `0000`, and supplies no character.

The endpoint offsets are recorded for geometry only. `747474` is applied as
zero-based MSB-first bit indices to the six landing characters themselves.

## Extraction

```text
o = 01101111, bit 7 = 1
s = 01110011, bit 4 = 0
s = 01110011, bit 7 = 1
a = 01100001, bit 4 = 0
e = 01100101, bit 7 = 1
d = 01100100, bit 4 = 0

selected bits = 101010
binary value  = 42
ASCII         = *
```

The output is therefore the conventional multiplication operator.

## Frozen nearby controls

These controls prevent silently rotating the selector to obtain a preferred
printable output:

| Rule | Bits | Value | ASCII |
|---|---:|---:|---:|
| exact `747474`, zero-based, outer-to-inner | `101010` | 42 | `*` |
| opposite phase `474747` | `110100` | 52 | `4` |
| exact `747474`, one-based | `111000` | 56 | `8` |
| exact `747474`, reversed rings | `001011` | 11 | non-printable |

Both bit-index base and direction matter. The multiplication result is not a
claim that all nearby conventions agree.

## Existing operation consumer

Phase 199 already fixed the operands without this observation:

```text
M = [[5,7,4], [0,6,1]]
v = [23,16,7]
M @ v = [255,103]
```

Phase 453 subsequently found the `FF` plus ASCII-letter endpoint unusual under
both frozen nulls, while correctly leaving multiplication and a byte consumer
unselected. Phase 485 supplies a direct conditional match to the first missing
semantic step: if `747474` is authenticated, ASCII `*` selects multiplication.
It does not select the later mixed `FF`/ASCII interpretation, byte order, or a
password/salt/IV/key consumer. No cryptographic oracle was run.

## Verdict

The closed-system structural derivation is verified exactly:

```text
six completed ring endings -> ossaed
ossaed[747474, zero-based MSB-first] -> 101010 -> 42 -> '*'
```

Disposition: **structural positive, provenance pending, consumer still open**.

- If both the ring-ending interpretation and literal `747474` are
  independently authenticated, multiplication is no longer an unselected
  operation for the canonical matrix/sum-list pair.
- In the repository as currently recorded, `747474` is unpinned, so the audit
  does not mark the operation selector authenticated.
- `G-MATPROD-001` remains open because no byte consumer is selected even under
  the conditional positive.

## Reproduction

```bash
python3 tools/gsmg/phase485_ring_endpoint_747474_audit.py --self-test
python3 -m unittest tools/gsmg/test_phase485_ring_endpoint_747474_audit.py
python3 tools/gsmg/phase485_ring_endpoint_747474_audit.py --write-result
```

