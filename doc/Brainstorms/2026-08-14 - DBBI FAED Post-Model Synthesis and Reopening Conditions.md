---
type: hypothesis
status: live
date: 2026-08-14
topics:
  - brainstorm
  - dbbi
  - faed
  - synthesis
  - reopening-conditions
---

# DBBI/FAED Post-Model Synthesis and Reopening Conditions

> [!info] Scope
> This is a synthesis of the sixteen bounded models executed in
> [[2026-08-14 - Fresh DBBI FAED Decryption Models]]. It proposes no new
> decode and records no new finding. Its purpose is to distinguish live missing
> assumptions from families that should stay closed until new evidence arrives.

## Executive conclusion

Sixteen different object models have now failed within their declared scopes:
lanes, transition matrices, GF(9), base 27, MTF/BWT, base-81 tokens,
factoradics, crib-solved recurrences, arithmetic coding, ANS, finite-state
machines, sequence alignment, audio/spectrograms, matrix barcodes, continued
fractions, and authenticated-string selectors.

The combined result does **not** establish that DBBI/FAED are random, decoys,
or unsolvable. It establishes something narrower and more useful:

> The repository has many candidate consumers but no authenticated
> specification selecting one.

The live frontier is therefore **specification recovery**, not transform
generation. Four missing choices dominate every surviving branch:

1. **operand scope** — DBBI, FAED, both, or a selected DBBI substring;
2. **operator semantics** — what `matrixsumlist` actually instructs here;
3. **alphabet/codebook selector** — especially `{g,i}` versus `{h,e}`;
4. **downstream consumer** — text, a numeric list, `thispassword`, a blob key,
   a route, or another instruction.

Until one of those is supplied independently, chaining more transforms mostly
measures researcher freedom.

## What survives all sixteen negatives

### 1. The page grammar remains real

The authenticated order is still:

```text
DBBI -> matrixsumlist -> FAED -> lastwordsbeforearchichoice -> thispassword
```

DBBI and FAED share one textarea text node, so markup supplies no operand
boundary or polarity. But the macro ordering itself remains stronger evidence
than any free-standing cipher resemblance. A future model should explain why
`matrixsumlist` occurs *between* the streams and how its result feeds the later
macros.

### 2. The two streams remain statistically asymmetric

- DBBI: 91 symbols, IoC about 0.151, unusually structured/key-like.
- FAED: 570 symbols, IoC about 0.118, closer to a high-entropy payload.

This still favors asymmetric roles such as model/key versus data, short
instruction versus long payload, or codebook versus encoded body. It does not
select a particular asymmetric algorithm: transition-table, probability-model,
ANS, FSM, recurrence, and selector realizations all failed.

### 3. The escape-pair conflict remains unresolved

DBBI's best-fit checkerboard escape pair is uniquely `{b,e}`. FAED's
independently best pair is `{g,i}`, while the Architect mirror route predicts
`{h,e}`. Page structure, archive history, and known syntax rules supply no
selector. This is still the sharpest concrete unresolved joint, not something
the sixteen model negatives dissolved.

### 4. The 31-character DBBI selection remains real but consumerless

`ncsyangcahiriasogaleafayanestve` is an authenticated structural checkpoint.
It still lacks all seven fields required to become a `matrixsumlist` operand:
dimensions, value map, traversal, aggregation, list serialization, orientation,
and downstream consumer. Readability or the internal `yang` fragment does not
fill those fields.

### 5. The Chapter-2 `YIN` construction remains a bounded clue-shaped signal

The first three yin-yang-decorated drop caps yield `YIN` under the previously
documented page-minus-letter operation. It has no selected input window and no
`YANG` counterpart. It is therefore a possible external selector surface, not
an operator yet.

### 6. Exact length identities remain descriptions, not instructions

The useful identities survive as checkpoints:

```text
91 = 7 x 13
570 = 6 x 91 + 24
91 = 81 + 10
570 = 2 x 3 x 5 x 19
```

But exact lanes, indel-tolerant lanes, the 24-tail projection, and the canonical
`81+10` state machine were null-like. A length identity should be reopened only
when another clue assigns roles to its parts.

## The remaining assumption tree

### A. DBBI and FAED may not be peer ciphertexts

Plausible surviving role assignments are:

```text
DBBI = selector/model/key       FAED = payload
DBBI = instruction/checksum     FAED = encoded data
DBBI = independent side clue    FAED = main payload
DBBI = validation reference     FAED = object to decode
```

What would reopen this branch:

- creator wording such as “first/second,” “key/data,” “model/message,” or
  “short/long” tied to these exact objects;
- pre-cutoff code taking one stream as configuration and the other as input;
- a transform that predicts withheld FAED material from DBBI without fitted
  parameters;
- an exact downstream-format check, not language score alone.

What does not reopen it: noticing that one stream “looks more random,” since
that asymmetry is already known and was the premise of several failed models.

### B. `matrixsumlist` may produce an intermediate numeric control object

Most failed models asked whether DBBI/FAED directly decode or exhibit structure.
The page grammar permits a different possibility:

```text
operand -> matrixsumlist -> short numeric list -> later macro consumer
```

This remains live only at the role level. It becomes executable when all of the
following are independently fixed:

| Required field | Acceptable selector |
|---|---|
| operand | exact page span or named object |
| dimensions | factorization, authored grid, or code constant |
| cell values | explicit symbol map/codebook |
| traversal | row/column/order instruction |
| operation | sums, products, transitions, ranks, or another named action |
| serialization | delimiters, base, order |
| consumer | exact later text/blob/validation rule |

This is the same seven-field reopening standard as G-MSL-001. Filling only one
or two fields creates another matrix sweep, not a mechanism.

### C. One stream may use a custom checkerboard/codebook supplied elsewhere

Standard checkerboards and broad alphabet families are heavily tested. What
survives is not “try another alphabet”; it is the possibility that an external
artifact supplies the exact alphabet, escapes, and topology.

Minimum reopening packet:

1. the exact ordered alphabet/codebook;
2. the selected escape pair and order;
3. the rule for DBBI versus FAED;
4. a known-positive local control or exact downstream envelope.

An external codebook that selects `{g,i}` or `{h,e}` would simultaneously move
G-ESC-001 and make a decoder test legitimate. Another IC-ranked pair without a
source would not.

### D. The intended output may be non-textual

The output could be a matrix, small number list, route, binary key material, or
another instruction. This remains possible, but “non-text” is not itself a
specification.

Valid oracles include:

- exact checksum/ECC or file/container validation;
- exact re-encoding with a non-tautological terminal state;
- a complete cryptographic envelope match;
- withheld prediction across both streams;
- a numeric result consumed exactly by a later authenticated instruction.

Invalid oracles include scalar validity alone, approximate address resemblance,
printable-byte ratio, or a few suggestive decimal digits.

### E. A source or transcription assumption could be wrong

This has a high evidentiary bar. DBBI/FAED are byte-stable across 16 successful
archive events and frozen by hash. Ordinary copy error, whitespace loss, or
late page drift is therefore not a live explanation.

Reopen only if:

- a genuinely new main-document hash contains different stream bytes;
- a primary pre-page artifact shows intended line breaks/separators;
- creator evidence states that the published bytes contain deliberate error or
  require reinsertion.

Community reformatting or a newly wrapped display does not qualify.

## Model-family reopening matrix

| Closed family | Evidence required to reopen |
|---|---|
| Six lanes / sequence alignment | Authored lane count, boundaries, edit model, or a consumer for the exact 24-symbol tail |
| Transition matrix | Explicit adjacency/transition direction and row/column consumer |
| GF(9) | Authored field-coordinate map, polynomial, component role, or syndrome rule |
| Base 27 | Selected trit order, group offset, and exact 27-character alphabet |
| MTF/BWT | Initial alphabet, BWT primary index/terminator, and direction |
| Base-81 pairs | Pair boundary plus an authenticated 81-entry lookup/codebook |
| Factoradic | Record size, boundaries, terminal-zero convention, and permutation consumer |
| Recurrences | Authenticated crib, placement, algebra, and recurrence order |
| Arithmetic/range coding | Probability model, EOS/output length, normalization, and emission convention |
| ANS | Explicit ANS evidence plus normalized table/spread, state, radix direction, and EOS/length |
| Finite-state machine | State/input/output serialization and trailer roles |
| Audio/spectrogram | Authored pitch/duration/channel map or recovery of the historical renderer/source |
| Matrix barcode | Lossless binary projection, exact format/size, and format-native padding rule |
| Continued fraction | Authored positive quotient map and pre-existing target constant |
| Authenticated-string selector | New authenticated target plus index origin, width, and pair boundary |

An audit bug or a demonstrably wrong source byte also reopens the affected
family, but only after the correction is specified independently of desired
output.

## Parking-lot models: minimum specifications

These should not be executed merely because the ranked list is finished.

| Parked model | Minimum information needed before implementation |
|---|---|
| Cellular automaton | lattice shape, neighbourhood, rule table/number, boundary condition, generation count, and readout |
| Grammar/substitution system | nine productions, axiom/seed, expansion order, stop condition, and terminal alphabet |
| Two-tape automaton | initial heads, comparison predicate, advance rule, emission rule, and halt state |
| Error-correcting interleave | code family/field, lane roles, parity layout, error capacity, and exact meaning of the 24 tail |
| Musical/spatial gestures | 3x3 layout, absolute versus relative motion, segmentation, timing, and output/readout rule |

If a clue supplies only one field, record it as partial evidence. Do not fill
the remaining fields with a Cartesian product search.

## Cross-model combinations remain gated

The four combinations listed in the original brainstorm are not a hidden
backlog. Their prerequisite structural gates failed:

- transition-matrix order -> MTF;
- GF(9) lane recurrence -> shared seed/syndrome;
- 24-tail endpoint selector -> lane summaries;
- transition matrix -> base-81 lookup.

They reopen only if new evidence independently names the *composition*. At that
point it should be registered as one complete model with a single family-wise
oracle—not justified as “two individually negative ideas might work together.”

## Evidence ladder for future proposals

### Tier A — immediate reopen

- creator-authored instruction naming an operator, role, pair, index, or
  boundary;
- authenticated pre-cutoff code that consumes the exact streams;
- a new primary artifact or page variant with distinct operative content;
- a `YANG` counterpart plus a mechanical selector for the `YIN` window;
- exact downstream validation under a fully declared transform.

### Tier B — warrants a bounded audit, not promotion

- independent community code predating the observed output and fixing most
  serialization fields;
- a unique structural identity that also names its consumer;
- a transform that succeeds on a nearby solved positive control and has at
  most one unresolved convention;
- a corrected prior audit with a concrete coverage gap.

### Tier C — record, do not execute

- a thematic wordplay with multiple missing parameters;
- another exact length factorization without role labels;
- an isolated readable fragment;
- an uncorroborated community assertion.

### Tier D — does not reopen anything

- raw p-values that disappear after family correction;
- arbitrary padding, reversal, rotation, offsets, or base hopping;
- OCR hallucinations from generated images;
- exact round-trips that reuse the recovered residual state;
- state zero as an absorbing decoder endpoint;
- secp256k1 scalar validity without a cryptographic hit;
- expanding targets or wordlists after seeing output.

## Recommended next posture

1. Keep G-MSL-001, G-ESC-001, and G-YIN-001 parked rather than manufacturing
   local work for them.
2. Treat new evidence as a **reopening packet**: source, exact quote/bytes,
   selected model, fixed parameters, consumer, and falsification rule.
3. Prefer source archaeology over new decoder families: creator exports, new
   authenticated artifacts, genuinely distinct archive hashes, or pre-cutoff
   code have much higher information value now.
4. When a packet arrives, rerun only the affected family and its positive
   controls before any blob-password escalation.
5. If no packet arrives, the honest conclusion is “blocked on selector,” not
   “one more transform away.”

## Compact reopening checklist

Before reopening any DBBI/FAED branch, require yes/no answers:

- [ ] Is the evidence new and independently sourced?
- [ ] Does it select the operand scope?
- [ ] Does it select the operator family?
- [ ] Are orientation, indexing, boundary, and alphabet fixed?
- [ ] Is termination/output length fixed where required?
- [ ] Is there an exact downstream consumer or structural oracle?
- [ ] Is the complete tried family declared before output inspection?
- [ ] Is a nearby positive control available?
- [ ] Would failure close the branch without adding more conventions?

If fewer than the first six boxes can be checked, the proposal belongs in the
parking lot, not an implementation queue.

## Bottom line

The sixteen-model campaign changed the question from:

> “What else can these nine symbols mean?”

to:

> “What missing source tells us which meaning was intended?”

That is real progress. The highest-value future discovery is not a cleverer
decoder; it is one authenticated selector that binds role, operation, and
consumer tightly enough for a decoder to become falsifiable.
