---
type: worksheet
status: live
date: 2026-08-09
topics:
  - gates
  - evidence-discipline
aliases:
  - Strict Transition Worksheet
  - Transition Worksheet
---

# GSMG Strict Transition Worksheet

**Date:** 2026-08-09  
**Purpose:** prevent a reproducible or thematic side-reading from being
silently promoted into a puzzle instruction, password, or cipher consumer.

## Current boundary

The strongest unresolved creator-grounded transition is:

```text
yellowblueprimes
-> exact 31-position DBBI selection
-> ncsyangcahiriasogaleafayanestve
-> matrixsumlist
-> UNKNOWN OPERATION
```

The worksheet does not assume that every exact pattern must be consumed. A
candidate advances only when its provenance, input, and complete operation are
fixed before its output is interpreted.

## Evidence labels

| Label | Meaning |
|---|---|
| **PASS** | The gate is fixed by authenticated creator material or a reproducible source with no remaining choice relevant to this gate. |
| **PARTIAL** | Some real source support exists, but at least one interpretation or provenance dependency remains. |
| **FAIL** | The gate depends on a retrospective association, unsupported parameter, spam-linked source, or missing consumer. |
| **NEGATIVE** | A properly bounded implementation was run and failed its declared output/calibration condition. |

“Community sourced” means the proposal's origin is known. It does not mean the
creator selected it. Community provenance must remain visibly distinct from
creator provenance.

## Five mandatory gates

### G1 — Source justification

Record the exact creator clue, recovered guide, community post, code commit, or
image feature that proposes the operation. Include its date and provenance
class. A later post quoting an earlier claim is not independent support.

**Pass condition:** the source actually supplies or clearly names the proposed
relationship. A theme match discovered after viewing an output is at most
partial.

### G2 — Unique input

Freeze the exact bytes, symbols, token boundaries, cutoff, and source artifact.
State whether the input is plaintext, ciphertext, image data, or a derived
object.

**Pass condition:** another investigator can construct one identical input
without seeing the proposed output.

### G3 — Fixed operation

Freeze every parameter that can change the result:

- orientation and traversal;
- zero- versus one-based indexing;
- byte order and bit order;
- polarity, reversal, and complement;
- alphabet and escape symbols;
- padding, KDF, digest, cipher, and mode;
- output serialization and split boundaries.

**Pass condition:** one complete algorithm exists before output inspection. If
eight orientations or two index conventions survive, the operation is not
fixed.

### G4 — Recognizable or authenticated output

The result must be one of:

- coherent creator-relevant language under a predeclared decoding;
- a known solved-stage value not used to choose the algorithm;
- a valid decrypt with independently expected structure;
- a hash, signature, address, or artifact established before the candidate was
  generated;
- an exact input to the next authenticated puzzle stage.

Same-branch hashes, self-published invariants, valid PKCS#7 padding, vanity
addresses controlled by the claimant, and thematic substrings noticed after
decoding do not pass independently.

### G5 — Matched controls and calibration

Declare the comparison family before promotion. Preserve the same source
length, symbol counts, candidate count, traversal choices, and scoring rule.
Report family-wise results rather than the best isolated member.

The project's usual promotion threshold is `p < 0.005` when an empirical
calibration is appropriate. A post-hoc descriptive rate is retained as such,
not relabeled a discovery p-value.

## Action rules

### Bounded structural audit may run when

- G1 is at least **PARTIAL**;
- G2 and G3 are **PASS**;
- the family and stop rule are declared first.

### Authenticated blob/address oracle may run when

- G1, G2, and G3 are all **PASS**; and
- the expected output class and validation rule are declared first.

An oracle must not be used to choose an orientation, KDF, token list, or
password representation and then presented as confirmation of that choice.

### A transition may be promoted when

- G1 through G4 are **PASS**;
- G5 is **PASS**, or the output is cryptographically authenticated by an
  independent target;
- no result depends on a choice introduced after viewing the output.

### A closed row may reopen only when

- new primary evidence fixes a previously missing parameter;
- a load-bearing source artifact changes;
- the historical audit used a demonstrably incorrect implementation or oracle;
- an independent target predating the candidate becomes available.

Narrative appeal, another exact arithmetic identity, or repetition by more
community accounts is not a reopening condition.

## Master worksheet

| Candidate transition | G1 source | G2 input | G3 operation | G4 output | G5 controls | Current disposition | Reopen trigger |
|---|---|---|---|---|---|---|---|
| 31-character DBBI selection -> proposed `matrixsumlist` consumer | **PARTIAL**: the selection and following macro token are real, but their operand relationship is not | **PASS**: `ncsyangcahiriasogaleafayanestve` | **FAIL**: no source binds the input to dimensions, traversal, values, and sum/index semantics (book pages 57–58, the only remaining uninspected primary source, reviewed Phase 259: no matrix content, 0/7 G3 fields fixed) | **FAIL**: no next-stage artifact; its broad-word cluster misses the promotion threshold (`p=0.005469995`) | **PASS** for disposition: seven G3 fields remain unbound and many bounded consumers are negative | **Structural checkpoint; parked (Phase 236, reviewed Phase 259)** | Primary evidence fixing the complete operation — a creator clue, recovered guide step, or pre-cutoff code artifact; the book's pages 57–58 no longer qualify as unexamined |
| Historical 14x14 DBBI row sums -> `IZLKESEEDQPPEN` | **PASS**: recovered Telegram guide | **PASS**: exact matrix/token chunks | **PASS** for historical row-major sums | **FAIL**: non-language; opens no target | **PASS**: directions and Caesar family calibrated; `p≈0.119`/`0.713` | **Closed negative** | New clue selecting a distinct consumer, not another direction |
| Prime lists -> `401/400/73` | **PARTIAL**: exact prime walk and literal list grammar, but alternative to historical guide | **PASS**: 14 blue, 8 yellow, 1 FEFE lists | **PASS**: partition and sums are fixed | **FAIL**: no instruction/key or downstream consumer (Phase 260: book title page's yin-yang-styled `C`/`D` initials read as Roman `CD=400` match the yellow sum; Phase 261 correction: the same design recurs on ordinary body drop caps book-wide, so this is a book-wide house style reused on the title, not a title-specific selection of `CD` -- graded as coincidence/corroboration, not an independent echo, and still no consumer) | **PASS**: fixed-profile rate documented; FE normalization shown dependent | **Structural checkpoint only** | Explicit clue consuming the three sums |
| Decimal matrix -> `[23,16,7]` -> Architect words | **PASS** for matrix sums and sourced dialogue | **PASS**: fixed matrix/list and scene | **PARTIAL**: word indexing fixed; beginnings/endings and polarity are not. Phase 232's bounded `partial_mirror9` (B↔H/D↔F/C↔G) audit found `HYE -> BYE` as the unique dictionary output (5/48 `BUT` rows; 36/35,904 stable triples; 1/6 fixed-word permutations). Phase 236 adds that only selected `BOTH`, among the three eligible B-initial words, has mirror endpoints B/H. This is real structural evidence, not a creator-selected operation | **PARTIAL**: `CIAO BELLA O` is authenticated page text; the `BYE -> Bella Ciao` association has genuine historical community precedent; their linkage is structurally supported, but not creator-selected. Phase 234 confirmed neither creator corpus ever selects CIAO, BELLA, or BYE as the yin-yang state. Still no authenticated consumer | **PASS**: associated FAED `{h,e}` model negative; direct-password checks for the CIAO/BELLA and KEY/NOTE/SELF families were negative (Phases 234-235); Phase 237 closed their legacy `pad28` checkerboard-keyword gap against P32TRAILING/URLBLOB (2,160 decoder configurations, 171,936 blob/KDF decryptions, zero strong or weak hits) | **Recognition checkpoint; parked** | Clue selecting beginnings/endings or B↔H operation — approached structurally by Phases 232/236, but remains evidentially unmet: no creator clue selects this operation or this output |
| DBBI/FAED -> creator's `yinyang` state | **PASS**: creator describes yin-yang as reached state | **PASS**: authenticated DBBI and FAED streams | **FAIL**: no relationship/operator selected | **FAIL**: state is recognizable only semantically | **PASS** for several specific negative coupling families | **Live semantic boundary, not executable** | Creator evidence defining how the streams interact |
| FAED `{g,i}` monoalphabetic/VIC chain-addition | **PARTIAL**: cipher-family precedent plus calibrated escape-pair ranking | **PASS**: fixed FAED and `{g,i}` orders | **PASS** for each registered model | **NEGATIVE** | **PASS**: monoalphabetic `p=0.0396`; 5,761,385 chain pairs, zero hits | **Specific models closed** | New keystream/operator evidence, not a larger dictionary |
| COSMIC raw32/MD5/103x103/base-38 construction | **FAIL** as creator transition: community code, mutually citing network, spam-linked keys | **PASS**: exact COSMIC envelope and token tuple | **PASS**: complete published algorithm reproduced | **FAIL** independently: random-shaped payload and claimant-controlled spam addresses | **PASS**: four representations, 210-family, offsets, entropy/padding, on-chain provenance | **Reproducible negative control; fabrication strongly supported** | Creator-authenticated pre-2025 anchor or output tied to real prize key |
| Matrix product -> `(255,103)` / `FF67` | **PARTIAL**: operands are real; multiplication is not named | **PASS**: `[[5,7,4],[0,6,1]]` and `[23,16,7]` | **FAIL**: reusing the sum list as vector and byte serialization are unselected | **PARTIAL**: `FF`/`g` thematic only | **PASS**: permutation/orientation family; exact class `1/720` descriptive | **Strong arithmetic checkpoint; parked** | Clue selecting multiplication and a byte consumer |
| Second matrix list difference -> reversed `KIT` | **PARTIAL**: both source lists reproduce; subtraction/reversal not sourced | **PASS**: `[43,25,18]` and `[23,16,7]` | **FAIL**: subtraction, A1Z26, and reversal are three unselected steps | **PARTIAL**: young-rabbit word is thematic | **PASS**: one of eight bounded orientations; checksum forced | **Parked; never a password** | Clue explicitly asking for difference/reversal or a young rabbit |
| FEFE tuple `{1,4,21}` -> `ggn` -> secp256k1 | **PARTIAL**: hierarchical tuple is real; flattening is not sourced | **PASS** for tuple; **PARTIAL** for peer URL indices | **FAIL**: indexing convention, `g→G`, scalar `k`, negation, and curve are unselected | **PARTIAL**: exact `ggn`, but generic group narrative | **PASS**: 2,024 triples calibrated; uniqueness common | **Narrative hypothesis; parked** | Independent clue supplies `k` and selects group order/negation |
| `BaTcH` -> `BATCH` | **PARTIAL**: community G-shadow/element rebus with real source pixels | **PASS** for extracted counts/glyphs | **FAIL**: inverse atomic lookup, order, singleton H, and execution grammar unselected | **PARTIAL**: exact English checkpoint | **PASS**: ordering family `1/6`; direct consumers negative | **Recognition-only; closed as instruction** | Creator clue explicitly selects element symbols and batch execution |
| `86420/13579` -> `igecabdfh` | **FAIL**: values have heterogeneous provenance; terminal zero supplied too freely | **FAIL**: full five-digit even rail not independently recovered | **FAIL**: eight orientation alternatives and trailing 9 role | **PARTIAL**: exact `a-i` permutation, with symmetric rival | **PASS**: strict gate and orientation family measured | **Closed** | Independent recovery of all digits and orientation |
| `Ce/Fe` -> checkerboard seed | **FAIL**: CE is render-composited, not a native source-favicon color | **PARTIAL**: arithmetic values exact | **FAIL**: source choice, element typing, seed order, and board tail unselected | **FAIL** | **PASS**: 2,430 board variants before arbitrary tails | **Closed** | Native CE source plus explicit construction rules |
| Token-preserved 14/8/1 rails -> 14 matrix rows | **PARTIAL**: event inventory exact; row mapping proposed afterward | **PASS**: 14 blue, 8 yellow, 1 FEFE events | **FAIL**: proposed direct mapping covers 12/14 rows, duplicates two | **NEGATIVE** | **PASS**: row coverage and MUX controls reproduced | **Closed** | Explicit traversal resolving missing/duplicate rows |
| Two 11-item shadow rails -> column operations | **PARTIAL**: rails are ordinal, not physical columns | **PASS**: two fixed 11-item count sequences | **PASS** only for declared larger/smaller/equality/sum/difference family | **NEGATIVE** | **PASS**: bounded operations and alignment calibration | **Closed** | Clue explicitly zipping the two rows or breaking ties |
| Cardan overlay | **FAIL**: no creator registration/target clue | **FAIL**: targets differ in dimensions; aperture mapping ambiguous | **FAIL**: at least 72 variants before registration choices | **NEGATIVE** | **PASS**: bounded minimum family documented | **Closed** | Explicit target, registration, orientation, and aperture rule |
| DNA/genetic decoding | **FAIL**: no genetic-code clue | **PASS** for packed endpoint bytes only | **FAIL**: 72 translations before downstream choices | **NEGATIVE** | **PASS**: complete declared convention family | **Closed** | Explicit DNA/codon/frame clue |
| RGB-vector geometry | **FAIL**: no consumer selects vector arithmetic | **PASS**: exact source colors and `(7,193,108)` difference | **FAIL**: channel, modulus, ordering, and alphabet choices | **NEGATIVE** | **PASS**: proposed mappings audited, `NIQ` inconsistency exposed | **Closed; retain exact vector only** | Explicit RGB arithmetic and output alphabet |

## Parked structural row: selected 31 -> proposed `matrixsumlist`

The selection and following macro token are both real, but Phase 236 shows
that treating the selection as `matrixsumlist`'s operand is not the default
macro grammar. The missing object under this still-possible model is narrowly
defined:

```text
input:
ncsyangcahiriasogaleafayanestve

needed:
one sourced operation specifying how matrixsumlist consumes it
```

The following do **not** fill that gap:

- noticing another word inside the selection;
- arranging 31 characters into a convenient rectangle with padding;
- choosing row/column/reversal after inspecting outputs;
- importing `KIT`, `ggn`, `BATCH`, or `FF67` as an alphabet/key;
- testing a candidate against AES and using padding to choose its rules.

The next valid evidence would look like a recovered guide step, creator reply,
code predating the output, or another authenticated artifact that uniquely
fixes matrix dimensions, traversal, and operation.

Phase 236 formally compares this model with the six-digit-prime grammar. The
selected-31 model consumes only `yellowblueprimes` before stopping at seven
unbound G3 fields. The prime model consumes `yellowblueprimes ->
matrixsumlist -> lastwordsbeforearchichoice` and reaches the cross-source
`BUT/HYE` boundary with three visible judgment calls. Neither establishes
`yinyang`, but the prime model is the default working grammar. Phase 132's
load-bearing broad-word control for the selected text (`gale`, `leaf`, `nest`,
`yang`) gives `p=0.005469995`, just outside the fixed `p<0.005` threshold, so
the selected text cannot be promoted to a recognition checkpoint. Its exact
disposition is **Structural checkpoint; parked**.

The 2026-08-09 provenance refresh is recorded in
[doc/GSMG_MATRIXSUMLIST_PROVENANCE_REFRESH.md](GSMG_MATRIXSUMLIST_PROVENANCE_REFRESH.md). It checked the full Telegram
export, the newest incremental export, the recovered guide neighborhood, a
2024 community code attachment, the walkthrough history, and the transcribed
*Cosmic Duality* book. None fixes G3. At that time the only genuine
uninspected source in that set was the physical book's pages 57–58 (bound
past the previously-photographed spread). Phase 259 (2026-08-13) closes that
gap: photographed and transcribed, they contain page 57 (a full-page repeat
of the already-known Franz Stuck "Sin" plate) and page 58 (Eve/Tertullian/
Council-of-Mâcon narrative continuation plus a Black Madonna sidebar) — no
matrix, dimension, or traversal content. G3 remains 0/7 fixed. A source-only
Telegram request, with explicit reply-classification rules, is prepared in
that report; posting it does not change any gate until a qualifying artifact
is recovered.

The page-syntax fallback was also checked. Binary ASCII `matrixsumlist` between
DBBI/FAED exactly parallels binary ASCII `enter` between the two AES pieces,
but only the latter has equal operands and an independently validated join.
The page uses mixed prefix/postfix/infix instruction placement elsewhere, so
postfix-to-DBBI, prefix-to-FAED, and infix DBBI/FAED roles all survive. This
parallel is structural evidence, not enough to change G3.

Phase 238 extends that comparison across every decoded instruction slot. Six
candidate house rules—uniform prefix, uniform postfix, between-means-join,
transport-fixes-role, nearest-neighbor operand, and complete SHA bracketing—
all fail an internal control. `enter` remains the sole locally fixed slot
because its equal 64-character neighbors independently reconstitute an
authenticated blob. Under working Model B, Phase 101's 54 models can be
conditionally projected to 18 password/SHA/tail models, but this projection
is not creator-authenticated and zero source-strict model results. Page syntax
therefore supplies no reopen evidence for this row.

The chronological code audit in
[doc/GSMG_MATRIXSUMLIST_HISTORICAL_CODE_AUDIT.md](GSMG_MATRIXSUMLIST_HISTORICAL_CODE_AUDIT.md) used Denis's first exact
31-character publication on 2026-03-04 as its cutoff. Across the public
walkthrough/notebook history, the pre-cutoff fork delta, and 83 Telegram code
or text attachments, zero pre-cutoff artifact contains the selected string.
An early 2025 14x14 explorer exposes ten competing traversals. A later 14x14
tool fixes a top-left counterclockwise positional spiral and row/column prime
sums, but its calculation ignores the grid bits and displayed letters, yielding
the fixed constants `ANTLGHQESHKTPG` and `OQOJWHCJPHZ-US`. It therefore cannot
serve as the missing consumer without a new source explicitly binding that
historical tool to the later input.

The creator/operator vocabulary inventory in
[doc/GSMG_CREATOR_OPERATOR_VOCABULARY_AUDIT.md](GSMG_CREATOR_OPERATOR_VOCABULARY_AUDIT.md) adds a separate source-only
constraint. Sixteen solved-stage operator families were retained only when
they lead to a recognizable or authenticated result. GSMG normally supplies
local parameter selectors (`reverse`, Caesar, `BASE64`, case/whitespace
syntax, “in front,” EBCDIC 1141, a fixed Beaufort key, or an exact hash
preimage). At the current boundary, those precedents fix **0/7** required G3
fields: dimensions, placement, traversal, value mapping, aggregation,
serialization, and target all remain unbound. XOR and beginnings/endings do
not qualify as demonstrated creator operators. The macro also permits a
competing `yellow/blue prime lists -> sum list` grammar, matching the existing
`400/401/73` checkpoint; that ambiguity weakens, rather than fixes, the claim
that the 31-character string must be the matrix operand.

## Recognition-checkpoint row: Architect words -> BYE -> CIAO BELLA O

Phases 232-235 (2026-08-10) extended this row's structural audit without
changing its disposition.

Phase 232 ran the B↔H/D↔F/C↔G involution (`partial_mirror9`) as one
fully-declared operation over the complete 48-row `but`-family and found
`HYE -> BYE` as the unique dictionary-word output (5/48 `BUT` rows; 36 of
35,904 stable triples; 1/6 fixed-word permutations). Phase 233 traced an
adjacency from `BYE` to sourced
`CIAO BELLA O` page text and the historically-attested *Bella Ciao*
farewell-song precedent already circulating in the solver corpus.
`CIAO BELLA O` is authenticated page text; the `BYE -> Bella Ciao`
association has genuine historical community precedent; their linkage is
structurally supported, but not creator-selected — neither corpus ever
names CIAO, BELLA, or BYE as the yin-yang state (Phase 234).

Phase 234 also withdrew an earlier `BELLA -> {b,e}` reading as post-hoc
(filtering `BELLA` to the page's native alphabet gives three letters,
`bea`, not a pair) and ran a bounded direct-password check — 90 keystring
forms x 4 tracked blobs, 0 hits — for the `ciao`/`bella`/`ciaobellao`/
`obellaciao`/`bellaciao` family. Phase 235 ran a separate bounded
direct-password check — its own 90 keystring forms x 4 tracked blobs,
0 hits — for the unrelated `key`/`note`/`self`/`keynote`/`selfself` family
raised by the same Architect-passage brainstorm. These are two independent
negative-control families, not one combined candidate set.

Phase 237 then froze the original Phase-2 legacy route—`pad28`, both decimal
`a-i` mappings, all 45 escape pairs, DBBI and FAED, inherited answer/keystring
normalization, and legacy AES-CBC—and changed only the blob scope to
P32TRAILING/URLBLOB. Across 12 exact candidates the audit ran 2,160 decoder
configurations and 171,936 blob/KDF primitive decryptions: zero strong hits
and zero weak records. This closes the explicitly retained checkerboard-
keyword coverage gap. It does not authenticate a consumer or weaken the
recognition evidence; the row remains parked for the same G3/G4 reasons.

The row's **Reopen trigger** — a clue selecting beginnings/endings or the
B↔H operation — is approached structurally (Phase 232 ran exactly a
B↔H-family operation), but remains evidentially unmet: no creator clue
selects this operation or this output. Disposition stays
**Recognition checkpoint; parked**.

Phase 236 adds one internal control: the three eligible first words in the 48
`BUT` rows are `BRINGS`, `BOTH`, and `BEGINNING` (16 rows each), and only
`BOTH` has mirror9 endpoints (`B...H`). Every one of the five partial-mirror
`BYE` rows starts with `BOTH`. The exact source clause is affirmative—“the
anomaly revealed as both beginning and end”—not a negated impossible-`both`
construction. This strengthens the edge reading but still does not authenticate
the endings-rail transform or a consumer; a simpler mixed-edge rule produces
`BYE` in 15/48 rows.

Full detail: `tools/gsmg/architect_hye_bye_audit.py`,
`tools/gsmg/bye_ciao_provenance_audit.py`,
`tools/gsmg/ciao_selection_coverage_audit.py`,
`tools/gsmg/architect_passage_residual_audit.py`,
`tools/gsmg/checkerboard_keyword_blob_gap_audit.py`; docs
`GSMG_ARCHITECT_HYE_BYE_AUDIT.md`, `GSMG_BYE_CIAO_PROVENANCE_AUDIT.md`,
`GSMG_CIAO_SELECTION_COVERAGE_AUDIT.md`,
`GSMG_ARCHITECT_PASSAGE_RESIDUAL_AUDIT.md`,
`GSMG_CHECKERBOARD_KEYWORD_BLOB_GAP_AUDIT.md`; FINDINGS.md Phases 232-237.

## Candidate submission template

Copy this block before implementing a new transition:

```text
Candidate name:

G1 source justification:
- source artifact/message:
- date and author:
- exact quoted or mechanically extracted instruction:
- creator / recovered guide / community hypothesis / spam-linked:

G2 unique input:
- exact bytes or symbols:
- construction and cutoff:
- source digest/version:

G3 fixed operation:
- traversal/orientation:
- indexing:
- polarity/byte order/bit order:
- alphabet/escapes:
- serialization:
- remaining alternatives: MUST BE ZERO

G4 declared output condition:
- expected form:
- independent anchor:
- authenticated target:

G5 controls:
- comparison family:
- family size:
- null or negative controls:
- promotion threshold:
- stop rule:

Decision:
- reject before implementation / bounded structural audit / oracle-authorized
```

## Working conclusion

No current side-reading passes all five gates. The six-digit-prime grammar is
the default macro model through `BUT/HYE`; it still does not establish
`yinyang`. The exact 31-character DBBI selection remains a real structural
checkpoint but is parked, not the sole priority transition input. Reopen it
only with primary evidence fixing all seven consumer fields, not another
transform over the already-exhausted output.
