---
type: audit
phase: 434
date: 2026-08-28
status: complete
result: synthesis
disposition: gated
script: tools/gsmg/phase434_architect_instruction_coverage_matrix.py
---

# Phase 434 — Architect Instruction and Coverage Matrix

> **Subsequent update (Phase 444):** Phases 442–443 fixed two eligible source
> strings and the exact split-final-BE prime mapping. Phase 444 therefore ran
> the previously gated minimal source-bound AND/OR rail family for both
> sources: blue alone, yellow alone, and blue-then-yellow, with the intertwined
> weave retained as an already-tested regression. All 216 structural trials
> were negative.

This is a dated addendum to
[P32 Trailing — Sibling-Output Password Path](Brainstorms/2026-08-14%20-%20P32%20Trailing%20Sibling-Output%20Password%20Path.md),
not a rewrite of that historical hypothesis. It incorporates the closures
recorded after Phase 270, especially Phases 307, 308, 314, and 370.

The script freshly derives the connected Phase 3.2.1 Beaufort plaintext from
the authenticated Phase 3.2 AES payload and asserts that all eight clauses
below occur in order. Spaces remain README transcription boundaries, not
cryptographically authenticated punctuation. The phase generates no password
material and makes no oracle calls.

## Clause matrix

| Clause | Best-supported instruction role | What is actually fixed | Existing coverage | Current disposition |
|---|---|---|---|---|
| `THE FUNCTION OF THE YOU IS` | Addressing/routing frame | Film's ONE→YOU parody is visible | Line, whole-block, and creator-row password families negative | Thematic frame; no general substitution consumer |
| `NOW TO RETURN TO THE SOURCE CODES` | Possible source selection | Only the pluralization of film's SOURCE is visible | Literal forms negative; earlier reinsertion readings unstable | Underdefined until source, unit, order, and boundary are fixed |
| `ALLOWING A TEMPORARY ... HOPEFULLY CARRY` | Provenance/narrative texture | TEMPORARY is screenplay-derived; HOPEFULLY creator-added | Phase 235 provenance plus direct/whole-text negatives | Recognition-only |
| `REINSERTING THE PRIME BASICS` | Prime-selection candidate | Prime vocabulary, but no local rail/base/serialization | Phase 265 literal negative; Phase 270 prime walk, pure prime, Stage-0, and split-guide consumers negative | Tested constructions closed; general phrase still underdefined |
| `AFTER WHICH ... BE REQUIRED TO SELECT FROM` | Operator framing | SELECT is explicit; rule and object are absent | Phase 270 selection constructions negative | Phase 435 finds the repetition real but non-selecting |
| `23 CIPHERS / 16 ENCRYPTIONS / 7 ... PASSWORDS` | Structural checkpoint | Inherited film count; split guide has 23 endpoints = 16 blue + 7 yellow | Phase 61 classification; Phase 270 direct consumers negative | Checkpoint real, downstream consumer unbound |
| `TO FIND THE ACTUAL PRIVATE KEYNOTE THAT ALSO` | Output type plus possible meta-boundary | Connected letters only; README prints KEYNOTE | KEY/NOTE/SELF/KEYNOTE direct forms and whole blocks negative | Read `PRIVATE KEY` as output and `NOTE THAT` as meta-instruction, not password material |
| `BRUTE FORCING MIGHT BE REQUIRED` | Method warning | Creator-added method language | Literal phrase negative; no finite local search space specified | Brute force is authorized only after a sealed construction exists |

## Model comparison

| Model | Fit after current evidence | Disposition |
|---|---|---|
| Passage is a literal passphrase reservoir | Weak: word, phrase, line, reverse, original-row, and whole-block families are negative | Closed absent a new authenticated material boundary |
| Passage routes the established macro chain | Partial: 23/16/7 is a real checkpoint and the Architect dialogue is a known indexed source | Retain only the already-solved routing; it does not select a new P32 consumer |
| 3.2.1 supplies operator, 3.2.2 supplies data, P32 supplies two-key output | Architecturally plausible, operationally unsupported | Phase 270's 25 candidates / 50 materials / 6 specs were negative; parked pending a new selector |
| Passage is semantic instruction | Strongest line-by-line reading | `PRIVATE KEY` = output, `NOTE` = likely meta-transition, `BRUTE FORCING` = method; still insufficient for candidate generation |

## `AND/OR` gate

At the set level, blue and yellow already partition the 23 split-guide
endpoints. Their union is all 23 and their intersection is empty, so that
source-free calculation adds no information. Producing *strings* called blue
and yellow is a different experiment: it needs a source object, endpoint-to-
character mapping, direction, boundary convention, and serialization. None is
selected here. The source-bound `AND/OR` experiment therefore remains gated.

## Net conclusion

The passage is most useful as a role declaration, not as another bag of
password words. `PRIME BASICS` and `SELECT FROM` name operation classes, but
do not bind their operands. The numeric triple is a genuine structural
checkpoint whose direct consumers are already negative. `PRIVATE KEY`,
`NOTE`, and `BRUTE FORCING` are best retained respectively as output type,
meta-instruction marker, and method. Phase 435 ran the only new bounded textual
selector test authorized by this matrix and did not promote it.

Reproduce:

```bash
python3 tools/gsmg/phase434_architect_instruction_coverage_matrix.py --self-test
python3 tools/gsmg/phase434_architect_instruction_coverage_matrix.py \
  --output tools/gsmg/phase434_result.json
```
