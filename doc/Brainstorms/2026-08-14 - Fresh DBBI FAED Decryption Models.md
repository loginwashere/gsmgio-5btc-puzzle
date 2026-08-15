---
type: hypothesis
status: live
date: 2026-08-14
topics:
  - brainstorm
  - dbbi
  - faed
  - salphaseion
  - cryptanalysis
---

# Fresh DBBI/FAED Decryption Models

> [!info] Brainstorm execution status
> This began as an unexecuted catalogue. Models 1–16 have now each received the
> bounded audit described in their result callout; all are negative within their
> declared scope. Parking-lot ideas and gated cross-model combinations remain
> unexecuted unless explicitly marked otherwise.

> [!info] Result — model 1 executed (2026-08-14)
> `tools/gsmg/dbbi_faed_six_lane_audit.py` tested the exact
> `570 = 6 x 91 + 24` geometry without plaintext scoring. Across 20,000
> independent shuffles preserving the exact DBBI and FAED-body symbol
> profiles, none of eight pre-registered body statistics was exceptional:
> the best raw result was DBBI appearing somewhere in 51/91 six-symbol
> columns (`p=0.119194`), which becomes a conservative family bound of
> `p=0.953552`; all other corrected values are `1.0`. The six direct lane
> match counts are `(7, 11, 11, 8, 14, 9)`. Separately, the 24-symbol tail's
> best possible symbol-consistent blue/yellow projection matches only 17/24
> endpoint colours, equal to the null median (`p=0.676466`), and cannot
> reproduce the mask exactly. **Model 1 is closed for exact aligned lanes,
> the declared consensus/residual/repetition statistics, and a fixed-symbol
> tail projection.** No candidate plaintext or password oracle was run.

> [!info] Result — model 2 executed (2026-08-14)
> `tools/gsmg/dbbi_faed_transition_matrix_audit.py` constructed the unique
> 9x9 directed-bigram matrix for each stream and calibrated nine adjacency
> statistics over 20,000 independent fixed-profile sequence shuffles. It
> separately tested the literal row-sum-plus-column-sum lists against all
> 9! FAED alphabet relabellings. DBBI mutual information was the smallest
> raw p-value (`p=0.053247`), but the ten-test family bound is `p=0.532473`;
> every other corrected result is `1.0`. Cross-matrix residual correlation
> is below the null median, and the exact degree-profile test gives
> `p=0.969224`. **Model 2 is closed for canonical directed transitions, the
> four declared identity/transpose/reversal relations, and literal degree
> sums.** No candidate text or password oracle was used.

> [!info] Result — model 3 executed (2026-08-14)
> `tools/gsmg/dbbi_faed_gf9_audit.py` enumerated all three monic
> irreducible quadratics over GF(3) under both canonical 3x3 coordinate
> orders. Across 1,000 exact-profile shuffle controls, the best full-stream
> linear complexities were 45/91 for DBBI (`p=0.267732`) and 284/570 for
> FAED (`p=0.043956`); the latter becomes `p=0.351648` across the declared
> eight-test family. Both GF(3) coordinates, held-out recurrence prediction,
> DBBI-recurrence transfer into all six FAED lanes, and joint seven-row rank
> are null-like. **Model 3 is closed for these six natural GF(9)
> presentations and linear recurrence/rank tests.** Arbitrary a-i-to-field
> permutations were deliberately not introduced. No candidate text or
> password oracle was used.

> [!info] Result — model 6 gate executed (2026-08-14)
> `tools/gsmg/dbbi_faed_base81_token_audit.py` pairs raw symbols into
> lossless values 0-80, preserving DBBI's unpaired final `e`. Twelve token-
> structure statistics were calibrated over 20,000 raw-symbol shuffles.
> DBBI within-pair mutual information is the strongest raw result
> (`1.183110` bits, `p=0.005450`) but misses the predeclared family gate after
> correction (`p=0.065397`). FAED's nine adjacent repeated tokens give raw
> `p=0.019649`, corrected `p=0.235788`; all other results are weaker.
> **The base-81 structural gate fails, so no ASCII offset, transition-matrix
> lookup, homophonic model, crib placement, or password oracle was run.** The
> DBBI pair-dependence value is retained as a narrow observation, not promoted
> as a decode.

> [!info] Result — model 7 gate executed (2026-08-14)
> Standard Lehmer codes are not self-delimiting, so
> `tools/gsmg/dbbi_faed_factoradic_gate_audit.py` fixes only the two sizes
> supplied by existing structure: `n=6` lanes and `n=9` symbols/matrix rows,
> each with the final zero present or conventionally omitted. Across 20,000
> exact-profile shuffles, neither stream contains a valid full record and the
> few omitted-zero windows are less or equally frequent than their null
> medians. All sixteen corrected p-values are `1.0`. **The record gate fails;
> no alphabet, row, column, or lane permutation was applied and no password
> oracle was used.**

> [!info] Result — model 8 executed (2026-08-14)
> `tools/gsmg/dbbi_faed_crib_recurrence_audit.py` encodes the fixed cribs
> `yinyang`, `thispassword`, and `seed` with the project's established
> A1Z26-mod-9 rule. Two leading digits solve coefficients for affine lag-1
> and homogeneous lag-2 operators over both `Z/9Z` and canonical
> `GF(9)=GF(3)[x]/(x²+1)`; only the unfitted suffix and the same aligned
> position in the other stream count as evidence. Across 500 complete
> selection-aware profile shuffles, the apparent 7/12 aligned
> `thispassword` match gives raw `p=0.055888`, corrected `p=0.223553`; the
> best own-stream holdout gives `p=0.471058`. **Model 8 is closed for these
> cribs, four fixed operators, and every legal forward placement.** No
> candidate text or password oracle was used.

> [!info] Result — model 9 executed under a canonical convention (2026-08-14)
> Arithmetic coding is not self-terminating from a probability table alone:
> the source supplies no EOS, decoded length, or emission convention.
> `tools/gsmg/dbbi_faed_arithmetic_model_audit.py` nevertheless tests the
> smallest deterministic family using DBBI's static histogram or first-order
> transition table, FAED as an exact base-9 fraction, and output lengths 91
> or 570. Exact rational decoding plus shortest canonical base-9 re-encoding
> yields codeword lengths `81, 516, 62, 392`; none equals FAED and no decoded
> stream equals DBBI/FAED. **Model 9 is closed for these four declarations,
> while custom range-coder conventions remain unspecified rather than tested
> negative.** No plaintext was promoted or password oracle used.

> [!info] Result — model 10 feasibility audit executed (2026-08-14)
> `tools/gsmg/dbbi_faed_rans_feasibility_audit.py` used DBBI's exact
> nine-symbol histogram as an unnormalized static-rANS table and the whole
> forward FAED base-9 integer as final state. Terminal `1` and the paired
> whole-DBBI state are both undershot. Terminal `0` is reached after 618
> symbols, but zero is the decoder's universal absorbing sink, so that exact
> re-encoding is guaranteed rather than evidential. Fixed output lengths 91
> and 570 leave unrelated 489- and 46-digit base-9 residual states; exact
> re-encoding with those recovered residuals is likewise tautological.
> **No nondegenerate endpoint exists, and the source supplies no normalized
> table size, symbol spread, renormalization convention, terminal/initial
> state, or decoded length/EOS.** No candidate or password oracle was run.

> [!info] Result — model 11 canonical machine executed (2026-08-14)
> `tools/gsmg/dbbi_faed_fsm_audit.py` consumes the exact `81+10` split as
> one row-major 9-state x 9-input next-state table, one initial state, and
> nine Moore output labels; FAED drives it and output is emitted after each
> transition. The machine visits all nine states and 79/81 state/input
> edges. Across 20,000 independent exact-profile DBBI/FAED shuffles, none
> of nine declared table/path/output statistics is exceptional: the best
> raw p-value is `0.303785` (longest run), and every Bonferroni value is
> `1.0`. **The canonical structural gate fails; no alternate orientation,
> Mealy rule, trailer role, candidate promotion, or password oracle was
> attempted.**

> [!info] Result — model 12 sequence alignment executed (2026-08-14)
> `tools/gsmg/dbbi_faed_sequence_alignment_audit.py` fixes unit-cost global
> Levenshtein alignment before scoring and searches forward DBBI against all
> 480 length-91 FAED windows, separately retaining the six original fixed
> lanes. The best sliding window starts at 112 and has distance 62 (36
> matches, 48 substitutions, seven insertion/deletion pairs); fixed-lane
> distances are `(71,73,64,70,68,69)`. Across 2,000 complete exact-profile
> shuffles, corrected p-values are `0.847076`, `0.259370`, and `0.544228`.
> **The alignment gate fails. Per the declared stop rule, gap positions were
> not interpreted and no candidate or password oracle was run.**

> [!info] Result — model 13 canonical audio renders executed (2026-08-14)
> `tools/gsmg/dbbi_faed_audio_spectrogram_audit.py` rendered DBBI and FAED
> under three preregistered pitch maps: chromatic from `a`, major from `a`,
> and cyclic major with `i` as root. Deterministic mono WAVs were passed
> through a from-scratch NumPy Hann-STFT, reproducing the core operation
> documented in Phase 8. Visual review of all six spectrograms shows only
> single-note ridges and transition stripes—no text baseline, glyphs, or
> independent shape layer. Tesseract emits inconsistent stripe hallucinations
> (`LMU`, `VIA WAN`, etc.) and is explicitly rejected as an oracle. **Model
> 13 is negative for these mappings.** The historical STFT script and MP3
> are absent, so exact old display parameters cannot be claimed; no arbitrary
> tempo/duration/pitch variants or password oracle were tried.

> [!info] Result — model 14 barcode family executed (2026-08-14)
> The brainstorm's `182/1140 bits` premise was corrected: those are trits.
> `tools/gsmg/dbbi_faed_matrix_barcode_audit.py` uses the lossless whole-
> base-9 integer binary representation (287/1807 bits) and renders the
> nearest fitting standard QR, square Data Matrix, and Aztec grids under
> two fixed-width zero-extension sides, three canonical fills, and both
> polarities: 84 candidates. **Zero candidates pass their mandatory finder
> geometry.** OpenCV loosely detects four QR-like quadrilaterals but decodes
> zero payloads; no Data Matrix/Aztec decoder is needed because none reaches
> that gate. No crops, masks, arbitrary sizes, candidate text, or password
> oracle were tried.

> [!info] Result — model 15 continued fractions executed (2026-08-14)
> `tools/gsmg/dbbi_faed_continued_fraction_audit.py` computes the complete
> convergent for DBBI and FAED under exactly three positive maps: direct
> 1–9, transposed 3x3 coordinates, and mirror-9. Six rationals are compared
> against a preregistered 17-item authenticated integer/ratio registry;
> “near” was fixed at absolute error `<=10^-12`. **There are zero exact
> value hits, zero near hits, and zero numerator/denominator hits.** The
> closest result—transposed DBBI versus `16/7`—is still `0.050055...` away.
> No decimal substring search, candidate text, or password oracle was run.

> [!info] Result — model 16 authenticated selectors executed (2026-08-14)
> `tools/gsmg/dbbi_faed_authenticated_selector_audit.py` applies zero-based
> single symbols and boundary-aligned base-81 pairs from both streams to five
> frozen strings in four authenticated categories: solved URL, prize address,
> native row/column sum digits, and validation answer. Across 20 outputs and
> 5,000 complete exact-profile shuffles, corrected p-values are `1.0`, `1.0`,
> `0.719856`, and `0.185563`. The apparent `GSMG` fragment in the address
> output is null-median (`p=0.509098`) because single indexing only reaches
> the address's first nine characters, which already contain `GSMG`.
> **Zero exact target hits; the gate fails.** Diagnostic outputs were retained,
> but none was promoted and no password oracle was run.

> [!info] Result — model 4 executed (2026-08-14)
> A direct code audit confirmed prior dual-ternary work never grouped three
> trits into base 27. `tools/gsmg/dbbi_faed_base27_audit.py` therefore tested
> the exact residual: 8 square symmetries x 2 within-symbol trit orders x 2
> conventional 27-character alphabets. The 32 declarations collapse to 16
> unique outputs per source. FAED decodes to 380 characters exactly; DBBI
> decodes to 60 while preserving two unconsumed trits. Across 5,000 exact-
> profile shuffles, the best DBBI score gives `p=0.488502`, FAED gives
> `p=0.493901`, and the combined whole-family maximum gives `p=0.503699`.
> **Model 4 is closed for boundary-aligned three-trit grouping under this
> declared natural family.** No padding, fragment selection, or password
> oracle was used.

> [!info] Result — model 5 gate executed (2026-08-14)
> Repository coverage contains no earlier MTF/BWT audit.
> `tools/gsmg/dbbi_faed_mtf_gate_audit.py` decodes `a-i` as ranks 0-8 and
> calibrates adjacent repeats, longest run, symbol concentration, transition
> mutual information, and zlib length for each stream over 20,000 exact-rank-
> profile shuffles. Initial alphabet order is proven to be only a global
> relabeling for these measures. Every one of the ten family-corrected
> p-values is `1.0`; neither stream acquires BWT-like run or compression
> structure. **The MTF gate fails, so the declared stop rule prohibits BWT
> primary-index scanning (`0` indices scanned).** No candidate text or
> password oracle was used.

## Fixed boundary

- `dbbi` is 91 symbols long and uses all nine letters `a` through `i`.
- `faed` is 570 symbols long and also uses all nine letters.
- Their source-page order is approximately:
  `dbbi -> binary(matrixsumlist) -> faed -> decimal(lastwordsbeforearchichoice)
  -> decimal(thispassword) -> SHA-256...`.
- The creator's macro vocabulary includes `matrixsumlist` and `yinyang`, so a
  matrix, paired representation, or relationship between the two streams has
  better source support than a free-standing classical cipher guess.
- A historical community 14x14 construction emits `IZLKESEEDQPPEN`, but it is
  partly fitted and has no validated downstream use. It is not assumed here.
- Standard checkerboards, monoalphabetic/digraphic substitutions, ordinary
  fractionation, VIC/chain-addition families, raw base-9/base-3 conversion,
  generic matrix reshapes, adjacent differences, mod-9 add/subtract coupling,
  nibble packing, and inversion of the known decimal transport have already
  received bounded negative tests. This note does not silently reopen them.

The central question is therefore not merely “what number is `a`?” It is:

> What *kind of object* are these streams—data, model, program, state,
> permutation schedule, error-correcting code, or two interacting tapes?

## Highest-value new models

### 1. Six FAED lanes keyed by DBBI, plus a 24-symbol control tail

**Status: executed negative.** See the result callout above and FINDINGS.md
Phase 274. Sequence alignment (model 12) is now eligible under its stated
reopening condition, but is not part of this exact-lane result.

The strongest unused length identity is exact:

```text
570 = 6 x 91 + 24
```

#### New assumption

The first 546 FAED symbols are six aligned records of DBBI's exact length,
while the final 24 symbols have a different role: selector, checksum, route,
polarity mask, initial state, or endpoint instructions. The number 24 also
matches the established count of Stage-0 coloured endpoints, making the tail
more interesting than an arbitrary remainder.

This is distinct from repeating DBBI across all 570 positions and trying
symbolwise mod-9 addition/subtraction. Six aligned lanes permit operations that
the repeated-key model does not:

- compare each FAED column to the corresponding DBBI symbol;
- treat each column's six values as a small observation set;
- select one of six lanes using a control sequence;
- rank or sort the six lane values rather than add them;
- use agreement/disagreement with DBBI as bits;
- aggregate each column by mode, median, parity, or missing symbol;
- apply the 24-symbol tail only after the 6x91 construction.

#### Smallest future test

Reshape only `FAED[:546]` as 6x91. Record, without language scoring:

1. equality masks against DBBI for each lane;
2. the six mod-9 residual histograms;
3. per-column agreement counts and repeated/missing-symbol patterns;
4. whether any fixed lane or simple lane consensus is anomalous relative to
   shuffled controls preserving each stream's unigram counts;
5. whether the untouched 24-symbol tail maps naturally to the fixed 24-item
   endpoint ordering already used elsewhere.

#### Stop rule

Do not search arbitrary lane permutations or 6^91 selectors. Continue only if
one pre-registered statistic is exceptional under matched nulls, or the tail
has a unique source-defined interpretation.

### 2. A symbol-transition matrix, not a spatial reshape

**Status: executed negative.** See the result callout above and FINDINGS.md
Phase 275. Reopening requires a source-selected non-adjacency matrix operation;
turning these row/column sums into passwords is not supported by this result.

Nine symbols have exactly 81 directed bigrams. Counting transitions produces a
canonical 9x9 matrix with no choice of width, padding, or geometry.

#### New assumption

`matrixsumlist` means: build the transition matrix, sum its rows/columns, and
list the result. DBBI and FAED might supply two matrices whose sum, difference,
transpose, complement, or row/column order expresses `yinyang`.

Possible outputs are tightly bounded:

- row sums and column sums (out-degree/in-degree profiles);
- diagonal versus off-diagonal counts;
- FAED-minus-DBBI residual matrix after length normalization;
- one matrix used to order the rows or columns of the other;
- stationary distribution or dominant transition cycle;
- symmetric and antisymmetric halves: `M + M^T` and `M - M^T`.

#### Why this is genuinely different

Earlier matrix work primarily placed sequential symbols into rectangular
grids. A transition matrix encodes adjacency statistics; it does not depend on
inventing a page width.

#### Smallest future test and stop rule

Construct the two 9x9 count matrices, compare them to order-shuffled streams
with identical symbol counts, and inspect only canonical row/column summaries.
Stop if neither stream nor their relationship is exceptional. Do not turn 81
counts into a free-form password list without an independently selected rule.

### 3. Arithmetic over GF(9), not integers modulo 9

**Status: executed negative.** See the result callout above and FINDINGS.md
Phase 276. Reopening requires an authored field-element mapping outside the
two natural 3x3 coordinate orders, or a nonlinear operation selected by a
new clue; arbitrary symbol permutations are not a residual of this test.

Nine symbols are unusually natural elements of the finite field
`GF(9) = GF(3^2)`. Each symbol becomes a pair of trits, while multiplication
and division become meaningful—operations unavailable in plain `Z/9Z`.

#### New assumption

`yinyang` refers to the two GF(3) coordinates of each symbol. One stream may be
a linear recurrence, codeword, syndrome, or keystream over GF(9), and the other
may define its seed or parity checks.

Candidate questions:

- Does either stream have unexpectedly low linear complexity under
  Berlekamp–Massey over GF(3) or GF(9)?
- Can DBBI predict aligned portions of the six 91-symbol FAED lanes through a
  low-order field recurrence?
- Is DBBI a syndrome/parity record for the 546-symbol body of FAED?
- Do the two trit-coordinate streams have complementary recurrences?

#### Freedom to control

GF(9) requires choosing an irreducible quadratic and a mapping of `a-i` to
field elements. A real test should enumerate the small complete equivalence
class, collapse isomorphic duplicates, and judge the best result against the
best result from shuffled controls. A basis that is chosen after seeing English
is not evidence.

#### Stop rule

Require a short recurrence, strong out-of-sample prediction, or a zero/low
syndrome fixed before plaintext scoring. Mere differences in linear complexity
are not enough.

### 4. Three-trit regrouping into a 27-character plaintext alphabet

**Status: executed negative.** See the result callout above and FINDINGS.md
Phase 277. Reopening requires an authored offset, alternate alphabet, or rule
for DBBI's two residual trits; padding or selecting short readable fragments
does not reopen this exact family.

Every nine-valued symbol can be represented as two trits. Consequently:

```text
FAED: 570 symbols -> 1140 trits -> 380 exact groups of 3 trits
DBBI:  91 symbols ->  182 trits -> 60 groups plus 2 trits
```

#### New assumption

The intended plaintext alphabet is 27 symbols—naturally `A-Z` plus space—not
bytes or hexadecimal. FAED is especially clean because it needs no padding.
The two residual DBBI trits could be a header, checksum, or evidence that this
model applies only to FAED; they must not be silently padded away.

#### Bounded variants

- the small geometric symmetries of the 3x3 symbol-to-trit grid;
- left/right trit order;
- `space,A-Z` versus `A-Z,space`.

This should first be checked against prior dual-ternary code to ensure the exact
three-trit family was not already subsumed. Five-trit/base-243 and whole-base-3
tests do not automatically cover it.

#### Stop rule

Use language scores calibrated on shuffled controls and correct for the entire
variant family. Do not promote isolated fragments of two or three letters.

## Medium-priority alternate object types

### 5. Move-to-front indices followed by a Burrows-Wheeler inverse

**Status: MTF gate executed negative; BWT correctly not executed.** See the
result callout above and FINDINGS.md Phase 278. Reopening BWT requires an
independent primary index or an authored reason to bypass the failed MTF gate.

#### New assumption

The letters `a-i` are not symbols at all but indices 0-8 into an adaptive
nine-item alphabet. Move-to-front decoding produces an intermediate stream;
that stream may then be a Burrows-Wheeler transform requiring a primary index.

This is attractive because a high-entropy-looking small alphabet is a normal
shape for transformed/compressed text, and MTF makes every digit meaningful
without an arbitrary base conversion.

#### Minimal future test

Apply MTF alone under only canonical initial alphabet orders and ask whether
run length, entropy, or repeated-word structure improves against nulls. Attempt
BWT inversion only after such a signal. If a primary index is not supplied,
scanning all 570 indices is finite but its maximum score must be compared with
the maximum from equally scanned controls.

#### Stop rule

No signal after MTF means no BWT escalation. Do not derive an alphabet order or
primary index from the candidate plaintext itself.

### 6. Natural radix-81 digraph tokens

**Status: structural gate executed negative.** See the result callout above
and FINDINGS.md Phase 279. DBBI's raw within-pair dependence is recorded but
does not survive the declared family correction. A consumer requires a new
source-selected lookup or independently fixed crib—not an arbitrary ASCII
offset.

Pairing two base-9 symbols creates a value from 0 through 80:

```text
FAED -> 285 exact base-81 tokens
DBBI -> 45 tokens plus one unpaired symbol
```

#### New assumption

Each pair is one token in a homophonic code, syllabary, dictionary index, or
small byte-like alphabet. This differs from the already-negative hexadecimal
nibble packing: base 81 preserves all nine-symbol information and introduces
no illegal digit values.

#### Sensible tests

- token frequency and repeated-token spacing;
- whether the 81 tokens form nine visibly related groups;
- a source-selected 9x9 lookup, such as the transition matrix above;
- a bounded homophonic-substitution model constrained by authenticated cribs.

Mapping 0-80 to ASCII by adding an arbitrary offset is not a meaningful test.
DBBI's unpaired symbol must remain visible as a possible mode/header marker.

### 7. Factoradic / Lehmer-code permutation instructions

**Status: record-validity gate executed negative.** See the result callout
above and FINDINGS.md Phase 280. The original “self-delimiting” wording is
corrected: a standard Lehmer stream needs an external size/boundary. Reopening
requires an authored record size other than the tested six or nine, or an
explicit boundary/consumer.

#### New assumption

The small digits encode reorderings rather than characters. A valid Lehmer
code has successively shrinking radices and deterministically names a
permutation. This fits the puzzle's repeated emphasis on ordering and could
make DBBI a permutation schedule applied to FAED blocks.

Possible bounded roles:

- reorder the nine-symbol alphabet per block;
- reorder rows/columns of a 9x9 object;
- reorder six FAED lanes using short permutation records;
- encode a route through previously established endpoint lists.

#### Stop rule

First ask whether the stream contains self-delimiting valid factoradic records
at a rate above matched random streams. If not, stop. Do not invent block
boundaries solely because one boundary yields readable text.

### 8. A low-order linear stream cipher solved from authenticated cribs

**Status: executed negative.** See the result callout above and FINDINGS.md
Phase 281. Reopening requires a newly authenticated crib, authored placement,
or different recurrence selected before output inspection; moving the same
three cribs to more hand-picked positions is not a residual.

#### New assumption

The cipher is not keyword substitution but a tiny recurrence, for example over
GF(9):

```text
P[i] = C[i] - alpha*C[i-1] - beta*C[i-2]
```

or a 2x2/3x3 Hill-like transform. Known puzzle words such as `yinyang`,
`thispassword`, or `seed` could determine the small coefficient set
algebraically rather than through a wordlist.

This is not the already-tested lag-1 adjacent difference. The novelty is a
low-order field recurrence plus coefficients solved from a pre-declared crib.

#### Stop rule

Crib text, placement policy, recurrence order, and field representation must be
declared before scoring. A coefficient set must explain withheld material or
both streams, not merely reproduce the crib used to solve it.

### 9. DBBI as a probability model; FAED as arithmetic-coded data

**Status: canonical exact-rational family executed negative.** See the result
callout above and FINDINGS.md Phase 282. Reopening requires an authored EOS or
output length and coder normalization/emission convention; adding another
implementation convention after inspecting its output is not warranted.

#### New assumption

DBBI supplies either a nine-symbol histogram or 9x9 conditional-frequency
table, and FAED is the output of an arithmetic/range coder using that model.
This makes one stream “rules” and the other “data,” a potentially literal
`yinyang` relationship.

#### Minimal future test

Use only models deterministically obtained from DBBI—its histogram or transition
matrix—and a canonical arithmetic decoder. Require an unambiguous termination
condition and exact encoder round-trip. Without those, the hypothesis has too
many degrees of freedom.

#### Complexity warning

This is possible but relatively implausible for a quickly assembled puzzle.
It should rank below the six-lane and transition-matrix models.

### 10. `anstoo` as “ANS too”: asymmetric numeral systems

**Status: minimal unnormalized-rANS feasibility family executed negative.**
See the result callout above and FINDINGS.md Phase 283. Reopening requires a
source-selected normalized table/spread, renormalization convention, terminal
state, and decoded length/EOS; the wordplay alone does not choose them.

#### New assumption

The unresolved nearby token `anstoo` literally hints “ANS too,” where ANS is
Asymmetric Numeral Systems. DBBI could define the frequency table or state and
FAED could be an rANS/tANS-coded stream.

This is deliberately a low-prior wordplay hypothesis. “ans” may simply mean
answer or a calculator's last result, and ANS would be a surprisingly modern,
technical choice for the apparent construction style.

#### Bounded future test

Only try canonical ANS variants when the symbol-frequency table, alphabet
order, initial/final state, and output length can all be derived from existing
exact artefacts. Success must mean valid termination plus exact re-encoding,
not merely printable decoder output.

### 11. DBBI as a finite-state transducer table

**Status: one complete canonical `81+10` Moore serialization executed
negative.** See the result callout above and FINDINGS.md Phase 284. Reopening
requires an authenticated selector for a different orientation, Mealy/Moore
role, or trailer interpretation; those remain different hypotheses rather
than untested variants of this result.

The identity `91 = 81 + 10` offers a speculative but crisp partition:

- 81 entries for a 9-state x 9-input table;
- 10 remaining symbols for an initial state, terminal state, mode, or decimal
  output mapping.

#### New assumption

The first 81 DBBI symbols serialize a machine; FAED drives it. Depending on the
machine convention, each entry could identify the next state or an output
symbol. This treats DBBI as executable instructions instead of ciphertext.

#### Main risk and stop rule

There are too many choices of row order, next-state/output role, and use of the
ten-symbol trailer. Park this model unless another clue explicitly selects
“state,” “source code,” “table,” or a decimal terminator. If reopened, test one
fully specified serialization, not a transducer search.

## Round 2 — object types not yet on the list

The eleven models above answer "what kind of object" with: reshape, matrix,
field element, alphabet, compression state, token, permutation, keystream,
coding model. Five more answers to the same question, each tied to something
this puzzle has already demonstrated it does elsewhere with *other*
artifacts—so applying the identical technique to DBBI/FAED specifically is
new, not the technique itself.

### 12. Sequence alignment between DBBI and FAED, not exact tiling

**Status: fixed unit-cost global-alignment family executed negative.** See the
result callout above and FINDINGS.md Phase 285. Reopening requires an authored
cost model, orientation, or non-91 boundary; tuning gap penalties after this
result would be a new, unselected family.

Model 1 assumes FAED splits into exactly six clean 91-symbol lanes. That is
the cleanest case of a weaker, more general idea: DBBI is a short reference
and FAED is six-ish noisy or edited copies of it.

#### New assumption

`570 / 91 ≈ 6.26`, not an integer. If the intended relationship allows
insertions or deletions—copyist noise, a checksum symbol inserted per lane, a
deliberate per-copy edit—forcing an exact 6x91 grid would silently discard
the signal. A bioinformatics-style pairwise alignment (Needleman-Wunsch
global or Smith-Waterman local, scored on exact symbol match since there is
no meaningful substitution cost model yet) recovers the best correspondence
under a declared gap penalty instead of assuming one.

#### Why this differs from model 1

Model 1 is a special case of this one with zero permitted edits. This model
is only worth running *if* model 1's clean 6x91 reshape fails its own
anomaly test—an unaligned but structured relationship is exactly what
alignment would recover and a fixed reshape would miss.

#### Minimal future test

Align DBBI against each candidate 91-symbol window of FAED (sliding, then
the six non-overlapping windows), record edit distance and gap positions
against shuffled-control alignments with identical unigram counts. A real
relationship should show a small number of high-scoring, low-edit-distance
windows, not a flat distribution.

#### Stop rule

Do not tune gap/mismatch costs after seeing which choice produces the
lowest distance. Fix the cost model before scoring. If no window's score is
exceptional against matched nulls, stop—do not chain into per-gap
interpretation.

### 13. Render the streams as audio and re-run the puzzle's own spectrogram pipeline

**Status: three canonical pitch mappings rendered and visually screened
negative.** See the result callout above and FINDINGS.md Phase 286. Reopening
requires the missing historical renderer/source asset or an authored mapping,
tempo, duration, amplitude, or channel rule; arbitrary audiovisual tuning is
excluded by the stop rule.

#### New assumption

This puzzle has already hidden a message in an audio file's spectrogram
(the Decentraland `(-41,-17)` clue -> `HASHTHETEXT`). DBBI/FAED could be a
note/duration sequence—nine symbols as scale degrees or MIDI pitch classes,
or as (pitch, duration) pairs—whose *rendered waveform's spectrogram*, not
the symbol values themselves, carries the payload, the same trick reused on
a new carrier.

#### Why this differs from the parking-lot "musical event stream" idea

That entry was parked as unconstrained. This version is falsifiable because
it reuses the exact, already-validated spectrogram-extraction pipeline from
the Decentraland clue rather than inventing a new analysis method—the only
new choice is the symbol-to-note mapping, which should be limited to a
small number of canonical scales (chromatic, diatonic-major-on-`i`-as-root)
before rendering.

#### Minimal future test

Render 2-3 canonical mappings to WAV, run the existing validated
spectrogram tool against each, and check only for the same kind of
structured artifact (embedded text/shape) that the Decentraland clue
produced—not a generic "does it sound musical" judgment.

#### Stop rule

If no canonical mapping's spectrogram shows a structured artifact, stop.
Do not iterate through arbitrary pitch/duration/tempo mappings hunting for
one that looks like something.

### 14. Render the streams as a 2D matrix barcode

**Status: representation corrected and nearest-standard-grid family executed
negative.** See the result callout above and FINDINGS.md Phase 287. Reopening
requires an authenticated binary projection or barcode padding rule; the raw
`182/1140 bits` premise cannot stand because the values are trits.

#### New assumption

This puzzle has already used a real, decodable QR code as a carrier (the
genesis image). DBBI (182 trits) or FAED (1140 trits) could, after an
independently selected binary projection, be raw module
data for a small standard 2D barcode—QR, Data Matrix, or Aztec—at one of
the handful of standard sizes those bit counts are close to, rather than
being interpreted as characters at all.

#### Why this is genuinely different

Every model above treats the streams as a linear sequence to decode.
This one asks whether the sequence is a *2D bitmap* whose validity is
checked by a barcode format's own error-correction and finder-pattern
structure—an external, mechanical validity check with no language scoring
involved.

#### Minimal future test

For each stream, try rendering its bits (in each of the small number of
canonical fill orders: row-major, column-major, boustrophedon) into the
module grids of the nearest-sized standard QR/Data Matrix/Aztec symbol and
attempt a real decode. A hit is binary: the decoder either validates the
format and error-correction and returns data, or it does not.

#### Stop rule

Try only sizes the bit count is close to (allowing the format's own
required padding/terminator bits, not invented padding). If no canonical
fill order produces a decodable symbol at a correctly sized candidate,
stop—do not search arbitrary crops, masks, or non-standard sizes.

### 15. The streams as continued-fraction partial quotients

**Status: three-map, closed-registry family executed negative.** See the
result callout above and FINDINGS.md Phase 288. Reopening requires an authored
positive digit map or a newly authenticated comparison constant; scanning
decimal substrings or additional permutations is outside this result.

#### New assumption

Map each symbol to a positive integer digit (1-9, avoiding zero as a
partial quotient, which continued fractions disallow after the first term)
and read DBBI or FAED as the partial-quotient sequence of a continued
fraction, producing one specific rational or converging real number rather
than a byte stream. This fits the puzzle's own recurring math-flavored
hints (`"the theory of everything is a valid path"`, the `sqrt(-1)`/
imaginary-number nudge, `"prime number is very important"`) better than an
arbitrary base conversion does—a continued fraction is a natural, keyless
way to turn a short digit sequence into one distinguished number.

#### Minimal future test

Compute the convergent for each stream under 2-3 canonical digit maps
(direct 1-9, and the field/trit maps already defined for other models,
excluding zero-valued digits). Check the resulting numerator/denominator
or decimal expansion against every already-authenticated puzzle number
(block heights, the `140`, `91`, `570`, `23/16/7`, prime lists, address
fragments)—an exact or near-exact match to something already established
is the only meaningful signal here.

#### Stop rule

Do not go hunting for a match by trying many digit maps until some
convergent "looks close" to something. Fix the comparison set of
already-authenticated numbers before computing convergents.

### 16. DBBI/FAED as index/selector sequences into already-authenticated strings

**Status: closed five-string/two-index-mode family executed negative.** See
the result callout above and FINDINGS.md Phase 289. Reopening requires a newly
authenticated target or independent one-based/pair-boundary selector; adding
strings after inspecting weak fragments violates the stop rule.

#### New assumption

Community chat records the still-uncredited-to-the-creator line "if you
know how the ARRAY IS INDEXED"—already in this project's fact base as a
genuine, if unconfirmed, community inference (Phase 53/61/etc. context).
This model takes it as a structural hypothesis rather than plaintext: each
DBBI/FAED symbol is not a value to decode but a 0-8 (or, paired, 0-80)
index selecting one character from an already-*authenticated* fixed
string—not a generic wordlist, a small closed set: the puzzle URL, the
prize address, the `matrixsumlist` row/col-sum digit strings, and
`VALIDATION_ANSWER`—reframing both streams as control/pointer data rather
than payload.

#### Why this differs from prior indexing work

Earlier prime-indexing work in this project selects characters *from*
DBBI/FAED using an external index (a prime list). This model inverts that:
DBBI/FAED symbols themselves are the indices, applied *to* other already-
known strings, and is restricted to strings this project has already
authenticated end-to-end—not a new source.

#### Minimal future test

For each candidate target string and each stream, take symbol values mod
the target's length, extract the indexed characters, and check only for
non-random structure (repeats, partial words, a length matching a known
answer) against a shuffled-index control.

#### Stop rule

Restrict the target set to the four already-authenticated strings named
above before running anything. Do not expand the target list after a weak
result to go looking for a better-fitting string.

## Parking-lot models

These are creative but currently too unconstrained to justify execution:

- **Cellular automaton:** DBBI is a local rule and FAED an initial state (or
  vice versa), evolving under mod-9 neighbourhoods.
- **Grammar/substitution system:** each of nine symbols names a production;
  one stream is the rule schedule and the other its expansion history.
- **Two-tape automaton:** consume DBBI and FAED asynchronously, with equality,
  ordering, or trit polarity deciding which head advances.
- **Error-correcting interleave:** six 91-symbol FAED lanes are noisy copies and
  DBBI is parity or a reference codeword; the 24-tail stores error positions.
- **Musical or spatial event stream:** nine symbols are 3x3 gestures/notes and
  information lies in motion between symbols, not symbol values. This needs a
  source clue selecting a layout before it becomes testable.

They should be reopened only when a clue fixes the rule family or serialization.

## Cross-model combinations that remain disciplined

Some ideas compose without creating an unlimited search:

1. Build the two transition matrices, then use their row/column order as the
   initial alphabet for move-to-front decoding.
2. Treat each of the six FAED lanes as a GF(9) sequence and ask whether DBBI is
   a shared recurrence seed or syndrome.
3. Use the exact 24-symbol FAED tail as a selector over the established
   24-endpoint list, then apply the resulting fixed order to six-lane summaries.
4. Interpret the 9x9 transition matrix as the only source-grounded base-81
   token lookup rather than inventing an ASCII offset.

Each combination should run only if its first stage independently passes its
own anomaly test. Chaining two negative transforms is not a new positive lead.

## Recommended future execution order

| Rank | Model | Reason |
|---:|---|---|
| 1 | Six 91-symbol lanes + 24 tail | Exact length identity, low complexity, source-linked 24 |
| 2 | 9x9 transition matrix | Canonical matrix with no invented width; fits `matrixsumlist` |
| 3 | GF(9) recurrence/syndrome | Native nine-symbol algebra and literal paired trits |
| 4 | Base-27 three-trit regrouping | Tiny bounded family; FAED divides exactly |
| 5 | MTF, then conditional BWT | Different object model; finite and null-testable |
| 6 | Base-81 token analysis | Natural pairing, but interpretation remains open |
| 7 | Factoradic permutation records | Puzzle-native ordering, weaker serialization clue |
| 8 | Crib-solved low-order recurrence | Testable, but multiple-testing risk |
| 9 | Arithmetic coding | Requires more conventions than the source supplies |
| 10 | ANS | Creative clue reading, historically/technically low prior |
| 11 | Finite-state transducer | Attractive 81+10 count, too many role choices today |
| 12 | Sequence alignment (DBBI vs. FAED) | Generalizes model 1; only run if model 1's exact reshape fails its own test |
| 13 | Audio/spectrogram rendering | Reuses this puzzle's own validated Decentraland pipeline on a new carrier |
| 14 | 2D matrix-barcode rendering | Mechanical pass/fail via format+ECC; reuses this puzzle's own QR precedent |
| 15 | Continued-fraction partial quotients | Fits the puzzle's math/number-theory thematic hints; needs a fixed comparison set |
| 16 | Index/selector into authenticated strings | Directly operationalizes a genuine, if unconfirmed, community hint fragment |

## Evidence discipline for any later audit

- Preserve the exact DBBI and FAED source bytes and lengths; never add padding
  without recording it as a separate hypothesis.
- Use profile-preserving shuffled controls, not generic random text, whenever a
  statistic depends on symbol frequencies.
- Correct for the best result across the entire tried family, including all
  orientations, bases, indices, and crib positions.
- Prefer structural oracles: exact round-trip, valid terminal state, low
  syndrome, withheld prediction, checksum, or known cryptographic envelope.
- Treat readable fragments as triage only. They are not confirmation.
- Do not escalate derived fragments to blob-password sweeps unless the transform
  has an independent reason to be correct.
- When possible, apply the proposed decoder to an already-solved nearby stream
  as a calibration control before interpreting DBBI/FAED.

## What this brainstorm intentionally avoids

- another arbitrary mapping of `a-i` to hexadecimal;
- unconstrained base hopping;
- generic wordlists and keyword permutations;
- arbitrary rectangular widths or route ciphers;
- padding DBBI to make a favoured block size fit;
- accepting `IZLKESEEDQPPEN` as ground truth;
- using a language score alone as a success oracle;
- multiplying speculative transformations until something looks English.

## Bottom line

The clearest fresh direction is relational and structural: **FAED naturally
splits into six DBBI-length lanes plus an exact 24-symbol tail**. The next best
idea is that `matrixsumlist` names the canonical 9x9 *transition* matrix rather
than another spatial grid. GF(9) is the strongest genuinely new algebraic model.
Base-27, MTF/BWT, base-81, factoradics, arithmetic coding, ANS, and finite-state
machines are useful creative reserves, but should remain behind those three
simple falsifiable tests.

> [!info] Post-execution synthesis
> All sixteen ranked models have since been executed within their declared
> scopes. Remaining assumptions and exact reopening conditions are consolidated
> in [[2026-08-14 - DBBI FAED Post-Model Synthesis and Reopening Conditions]].

Of the round-2 additions, two stand out for reusing mechanisms this puzzle has
already proven it uses elsewhere rather than importing a technique from
nowhere: **spectrogram rendering** (this puzzle has already hidden a message
this way, on a different carrier) and **2D matrix-barcode rendering** (this
puzzle has already used a real, decodable QR code as a carrier). Both have a
mechanical, language-score-free pass/fail. **Sequence alignment** is the right
generalization of model 1 if its exact 6x91 reshape comes back clean under
its own test. **Index/selector into authenticated strings** is the only
round-2 model directly grounded in existing puzzle-adjacent text (the "array
is indexed" fragment) rather than in a generic mathematical object.
