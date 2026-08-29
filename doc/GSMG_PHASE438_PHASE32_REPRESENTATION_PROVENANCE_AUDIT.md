---
type: audit
phase: 438
date: 2026-08-28
status: complete
result: workflow-privilege-without-downstream-binding
disposition: gated
script: tools/gsmg/phase438_phase32_representation_provenance_audit.py
---

# Phase 438 — Phase 3.2 Representation Provenance Audit

> **Subsequent update (Phase 445):** Applying a distinct transport-role gate
> across the full native Phase-3.2 graph does not choose among Phase 438's
> three 3.2.1 representations alone. It identifies decoded `answer_321` and
> sibling decoded `answer_322` as two eligible carried outputs, with no
> established binding or transform from either one to P32.

The Phase 3.2 solve workflow privileges three different roles, but no primary
evidence identifies any one of them as the downstream operand of `SOURCE CODES`.

## Representation comparison

| Representation | Length | SHA-256 | Evidence class | Established role |
|---|---:|---|---|---|
| Raw encoded 3.2.1 block | 1,539 bytes | `bd7a29432546c67c4170e0c523ddbf43ae82d20ee187d1b4dbf7907a0faf4c7b` | creator-delivered | encoded input |
| CP1141-labelled lowercase text | 1,539 letters | `6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e` | clue-selected derived | Beaufort ciphertext intermediate |
| Decoded Architect text | 1,539 letters | `56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241` | decoded output | plaintext containing the instruction |

The raw block has exactly 26 distinct symbols. GNU iconv conversion through
CP273 and CP1141 produces byte-identical lowercase ciphertext on this block:
1,539 equal positions and zero differences. Both equal the repository's pinned
Beaufort ciphertext. Thus `one for one, four for one` supports the historical
CP1141 route, but the number `1141` does not select a letter stream different
from CP273 for the bytes actually present.

## Historical solve workflow

The local `naddiseo/master` history first adds `phase3.2.ipynb` in commit
`dcb66952de3157f6e68cb00aa047dd2e4ff8ae39` on 2023-08-19. The notebook says
the puzzle had been solved to this point by the end of 2019. It reproducibly:

1. reads the raw Phase 3.2 bytes;
2. isolates the 26-symbol block;
3. reports CP273 and CP1141 as 100% ASCII conversions;
4. chooses CP1141 from `one for one, four for one`;
5. reads `beautiful strategic position` as Beaufort;
6. decrypts with `THEMATRIXHASYOU` to the Architect text.

This is strong evidence for the community solve chronology and the role of each
representation. It is not creator-primary evidence that the later phrase
`SOURCE CODES` loops back to one of those representations.

## Creator-evidence check

The frozen case-insensitive terms were `1141`, `ebcdic`, `beaufort`,
`one for one`, and `source codes`. Their union contains 201 messages in the
pinned complete `GSMG Puzzle Solvers` export.

| Term | Hits | Earliest message |
|---|---:|---:|
| `1141` | 65 | 3301 |
| `ebcdic` | 20 | 3856 |
| `beaufort` | 51 | 6215 |
| `one for one` | 23 | 2872 |
| `source codes` | 67 | 5881 |

Zero fixed-term hits were authored by creator ID `user9815232`. Zero creator
messages directly reply to any of those 201 hits. The export therefore contains
community interpretations, but no creator-primary edge selecting raw bytes,
transcoded letters, or decoded letters as the downstream operand.

## Effect on Phase 437

Phase 437's word `authenticated` should be read as “exactly reproducible from
authenticated puzzle material,” not as a claim that raw and transcoded objects
have identical provenance. Phase 438 refines the distinction without promoting
either uncovered family:

- raw bytes are primary delivered material, but `SOURCE CODES` does not select them;
- CP1141 letters are an exact, clue-supported intermediate, but not a separately
  creator-published downstream source;
- decoded letters contain the instruction and remain an unselected self-source.

All three still fail Phase 437's `locally_selected` and
`unique_representation` gates. Prime unit, base, direction, rail, boundary, and
consumer also remain unfixed.

## Verdict

Disposition: `workflow_privilege_without_downstream_binding`.

This makes the representation ambiguity better defined, not executable. No
prime rail or password material was generated, no oracle call occurred, and the
GPU run was untouched.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase438_phase32_representation_provenance_audit.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase438_phase32_representation_provenance_audit.py \
  --output tools/gsmg/phase438_result.json
```
