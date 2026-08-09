# GSMG Creator/Operator Vocabulary Audit

**Date:** 2026-08-09  
**Scope:** source analysis only. No transform combinations or password/blob
oracles were tested.

## Question

Do operations demonstrably used in solved GSMG stages, together with the
authenticated endgame instructions, uniquely define how
`matrixsumlist` consumes:

```text
ncsyangcahiriasogaleafayanestve
```

## Result

No. Solved-stage precedents constrain the puzzle's style, but fix zero of the
seven fields required for a complete matrix consumer at this boundary.

The most important negative is not a lack of possible operations. It is a
lack of **local selection**. In solved stages, every parameter-changing
operation is accompanied by a nearby selector:

- Caesar is directly clued and has a fixed shift;
- `reverse` is decoded before the relevant whole-stream reversal;
- `BASE64` labels the payload it consumes;
- `aBa / connected enf` specifies case and whitespace treatment;
- “add `giveit` in front” fixes both prefix and direction;
- EBCDIC `1141` and Beaufort `THEMATRIXHASYOU` are locally identified;
- SHA-256 is applied to an exact, already assembled preimage;
- the Stage-0 spiral has a fixed 14x14 source, corner, direction, and bit
  interpretation.

`matrixsumlist` has no comparable local specification for shape, placement,
values, aggregation axis, serialization, or expected output.

## Demonstrated solved-stage operators

These operations have independently recognizable outputs or open the next
known stage. They are precedents, not automatically reusable defaults.

| Operator | Demonstrated stage | Fixed parameters in that stage | Successful output |
|---|---|---|---|
| Concatenate adjacent streams | Pre-rabbit puzzle | Two creator posts, source order | One 5,368-bit stream |
| Binary to ASCII | Pre-rabbit puzzle; rabbit Stage 0 | MSB-first 8-bit bytes | Command stream; Stage-1 URL |
| Caesar decode | Pre-rabbit puzzle | Shift `-3` selected by Caesar clue | `removethecorrecthint...` |
| Reverse complete stream | Pre-rabbit puzzle | Whole text or whole inner bitstream | `reverse`; labeled Base64 payload |
| Base64 decode | Pre-rabbit puzzle and AES envelopes | Literal payload boundaries | Recognizable URL/ciphertext |
| Map colors to bits | Rabbit Stage 0 | black/blue=`1`; white/yellow/FEFE=`0` | Stage-1 URL |
| Counterclockwise spiral | Rabbit Stage 0 | 14x14, top-left, first move down | `gsmg.io/theseedisplanted` |
| Enter/submit password | Stage 1 form | Exact lyric-derived password | Next authenticated page |
| Concatenate ordered fields | Phase 3 | Seven parts in clue order | Known SHA-256 password |
| Preserve case; remove/retain whitespace | Phase 3 | `aBa`, `connected enf/not enf` | Known SHA-256 password |
| Prefix literal text | Phase 3.2 | `giveit` in front of `justonesecond` | Known SHA-256 password |
| SHA-256 exact bytes | Phases 2, 3, 3.2; extra-door entry | Exact preimage | Four reproduced transition hashes |
| AES-256-CBC decrypt | Phases 2, 3, 3.2 | OpenSSL `Salted__`, solved password | Authenticated plaintext |
| EBCDIC 1141 then Beaufort | Phase 3.2.1 | Code page 1141; `THEMATRIXHASYOU` | Known Architect-derived plaintext |
| Keyed straddling checkerboard | Phase 3.2.2 | 28-symbol alphabet; escapes `1,4` | `INCASEYOUMANAGE...FUNDS TO LIVE` |
| Hash concatenated visible text | Extra-door entry | Banner followed by prize address | Authenticated SalPhaseIon URL |

## Authenticated but unresolved endgame vocabulary

| Instruction/token | Provenance | What it fixes | What it does not fix |
|---|---|---|---|
| `yellowblueprimes` | Creator macro `8446`; creator prime/zeroing hints | Color and prime vocabulary upstream | Exact relationship to `matrixsumlist` |
| `matrixsumlist` | Creator macro and authenticated SalPhaseIon bytes | Names a matrix/sum/list relationship | Shape, values, axes, traversal, output |
| `lastwordsbeforearchichoice` | Same two primary sources | A semantic selection phrase | Operand, film-text edition, indexing, relationship to matrix result |
| `yinyang` | Creator macro and later creator recognition messages | Expected reached state/next phase | Executable operation |
| `zeroed out` | Creator message `8000` | Some destructive/filtering action is intended | Which characters, when, and replacement semantics |
| `first or zero` | Creator message `4105` | Bit/index vocabulary | One-based versus zero-based use at this boundary |
| `sha256 our first hint is your last command` | Authenticated page bytes | Hash and command vocabulary | Exact preimage and which artifact consumes the result |
| `enter` | Authenticated page bytes | Valid separator between two equal AES halves | Any matrix placement or summation rule |

The exact creator macro remains:

```text
yellowblueprimes
matrixsumlist
lastwordsbeforearchichoice
yinyang
wewontgiveawaythepassword
itsinfrontofyoureyesbutyourenotseeingit
verylaststepisatruegiveaway
promised
```

## Terms excluded from the authenticated operator inventory

| Term | Reason |
|---|---|
| `XOR` | No verified solved GSMG transition uses it. Its current prominence comes from the spam-linked/community COSMIC construction. |
| `beginnings/endings` | A post-hoc label for the Architect-word indexing side-reading, not creator-authored operational language. |
| subtraction/difference | Brainstorm arithmetic, not a demonstrated transition. |
| `BATCH`/execute | Community rebus hypothesis already parked by its strict gate. |

This does not say those operations are impossible. It says they cannot be
counted as creator design precedent when evaluating G3.

## G3 field audit

| Required field | Closest genuine precedent | Why it remains missing |
|---|---|---|
| Matrix dimensions | Stage 0 is 14x14 | 31 symbols do not fill 196 cells; no padding or placement rule |
| Input placement | Ordered concatenation is common | No row/column/spiral placement of the selected characters |
| Traversal/orientation | Top-left CCW spiral; whole-stream reverse | Two different precedents exist and neither is bound to this instruction |
| Symbol-to-number mapping | Bits and clue-specific numeric alphabets are used elsewhere | No current mapping from the 31 letters to values |
| Aggregation | The word `sum` is authenticated | No solved stage demonstrates matrix row sums, columns, totals, or index sums |
| List serialization | Ordered fields are used elsewhere | Row-only, column-only, row+column, delimiters, and order remain open |
| Next artifact/target | Earlier stages use URLs, hashes, and AES plaintext | No expected hash, URL, plaintext, private-key relation, or blob binding |

Result: **0/7 fields fixed** by authenticated local instructions.

## The surviving grammar ambiguity

The vocabulary audit exposes two distinct readings of the same creator macro.

### Sequential-stage grammar

```text
yellowblueprimes
    -> derive the 31-character DBBI selection
matrixsumlist
    -> consume those 31 characters somehow
```

This is the project's current priority-row model, but the consumer is missing.

### Compound prime-list grammar

```text
yellow / blue prime lists
    -> sum list
```

This naturally matches the independently reconstructed colored-prime totals:

```text
yellow = 400
blue   = 401
FEFE   = 73
```

It uses the authenticated words economically and does not require placing 31
letters into a new matrix. But it leaves `matrix` as the Stage-0 grid/theme,
does not define what consumes `400/401/73`, and is not selected over the
sequential grammar. It therefore remains the existing structural checkpoint,
not a completed transition.

## Verdict

The creator/operator vocabulary does not fix G3. It does, however, make three
constraints firmer:

1. Do not import XOR, beginnings/endings, subtraction, or execution grammar as
   if the solved puzzle had established them.
2. Prefer a future source that supplies a local parameter selector, consistent
   with how earlier GSMG operations were authored.
3. Keep both macro grammars visible. Treating the 31-character string as the
   mandatory matrix operand is plausible, not yet proven.

Reproduce the source checks with:

```bash
python3 tools/gsmg/creator_operator_vocabulary_audit.py --self-test
```

