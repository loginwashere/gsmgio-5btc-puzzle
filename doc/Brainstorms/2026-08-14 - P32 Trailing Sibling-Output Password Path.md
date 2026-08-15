---
type: hypothesis
status: parked
date: 2026-08-14
topics:
  - brainstorm
  - phase-3.2
  - p32-trailing
  - password-derivation
  - private-keys
---

# P32 Trailing — Sibling-Output Password Path

> [!caution] Incubation note
> This document records a high-priority structural hypothesis and a bounded
> test plan. It is not evidence that a proposed password is correct, and it
> does not promote an oracle hit without exact, reproducible decryption.

> [!info] Result (2026-08-14)
> `tools/gsmg/p32_sibling_password_audit.py` implements and runs the whole-text
> family, grounded prime/Stage-0 readings, the internal-parameter family, the
> exact parent-byte prefix, and the split-final-`be` guide retarget: 25
> candidates, 50 password materials, 300 trials against the true
> 64-byte/16x`0x10`-padding structural oracle
> (secp256k1 scalar validity checked only after a hit, never used to promote
> a candidate — a random 256-bit value is a valid scalar with near-certainty,
> so it carries no filtering power on its own). **0 hits.** Full writeup:
> FINDINGS.md Phase 270. The documented prime-walk and split-guide consumers
> are now tested negative for P32; reopening requires a different operator
> selected by new authenticated evidence.
>
> Every source-grounded construction (Families A, B, C, the structural
> oracle, and exact-byte reconstruction) is now tested. What remains is
> explicitly speculative, not merely unattempted, and is parked rather than
> pursued as an unbounded sweep:
>
> - **Family D** — ordered combinations of salient fragments (e.g.
>   `CIAOBELLAO` + `HALFANDBETTERHALF`) with no clue selecting which
>   fragments or what order;
> - **half/interleave operations** on `half and better half` — no source or
>   split point is authenticated;
> - **full-text variants with manually restored spaces/newlines** — the
>   actual Beaufort output is connected letters, so these are weak;
> - **events 24-25 of the prime walk, matrix-layout, wraparound, or
>   alternative-index variants** — 24-25 exceed the 91-character consumer
>   without inventing wraparound;
> - **double-SHA, HMAC, XORed hashes, or additional cipher/KDF families**
>   for the new composites — gated behind an operator clue, per this
>   document's own hashing-discipline section;
> - **address/on-chain validation** — only activates after a structural hit.
>
> Reopening any of these requires a new authenticated selector, not
> additional endpoint or fragment arithmetic on what's already been tried.

## Core observation

The P32 trailing OpenSSL blob, the Phase 3.2.1 Beaufort material, and the
Phase 3.2.2 VIC/checkerboard material are siblings inside the same authenticated
Phase 3.2 decryption. In source order, the decrypted payload contains:

1. the clue for the EBCDIC-1141/Beaufort operation;
2. the Phase 3.2.1 encoded block, which decodes to the Architect-style speech;
3. the Phase 3.2.2 decimal stream;
4. the keyed-alphabet clue for decoding that stream;
5. `P32_TRAILING`, appended after those materials.

This resembles the established grammar of earlier phases: clue material in one
decrypted stage supplies ordered answer material for the password of a sibling
or following encrypted object.

```text
Phase 2 clue answer       -> SHA-256 -> Phase 2 decryption
Phase 3 ordered answers   -> SHA-256 -> Phase 3 decryption
Phase 3.2 ordered answers -> SHA-256 -> Phase 3.2 decryption
3.2.1 + 3.2.2 siblings    -> ?       -> P32 trailing decryption
```

The most important unresolved question is therefore not whether the two
plaintexts have ever appeared in a candidate corpus. They have. The question is
whether they have been consumed in their provenance-native role as ordered
sibling clues and/or as an operator-plus-data construction for P32.

## Role-separation hypothesis

The cleanest current model assigns the three objects different roles:

```text
Phase 3.2.1 -> password-construction instructions
Phase 3.2.2 -> data reservoir and expected-plaintext description
P32         -> encrypted pair of private keys
```

### Phase 3.2.1 as operator

The Architect parody explicitly says:

```text
RETURN TO THE SOURCE CODES
REINSERTING THE PRIME BASICS
...
TWENTY-THREE CIPHERS
SIXTEEN ENCRYPTIONS
SEVEN INTERTWINED PASSWORDS
TO FIND THE ACTUAL PRIVATE KEYNOTE
```

This vocabulary can describe a construction rather than a literal passphrase.
The `[23,16,7]` recurrence was initially compared with the reconstructed
first-piece prime walk. A direct recount corrects that comparison:

- 23 selecting events;
- 15 single-character selections;
- 8 two-character selections;
- 31 selected characters in total.

The number triple is also inherited directly from the source Architect speech's
`23 individuals / 16 female / 7 male`, with only the trailing nouns replaced.
It is therefore not independent evidence of an operator. An exact `23/16/7`
profile does exist elsewhere, but in a different construction: splitting the
recovered guide's final `be` produces 23 endpoints partitioned as 16 blue and
7 yellow. That is a community-recovered structural checkpoint, not the
23-event prime walk and not a creator-specified P32 operation. The earlier
conflation materially weakens the proposal that this sentence directly
describes the P32 password derivation.

### Phase 3.2.2 as data and validation

The normalized 91-character VIC/checkerboard output is:

```text
INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE
```

It may serve two compatible purposes:

1. a character reservoir for a selection directed by Phase 3.2.1; and
2. a description of the expected P32 plaintext: two Bitcoin private keys.

The second role is particularly useful as an oracle. The decoded OpenSSL
envelope is 96 bytes: 8 bytes `Salted__`, 8 bytes of salt, and exactly 80 bytes
of ciphertext, or five AES blocks. A plaintext consisting of two raw 32-byte
private keys is exactly 64 bytes and therefore has one unique PKCS#7
representation at that ciphertext length: a complete fifth block of sixteen
`0x10` bytes. The unconditional probability that a wrong decrypt reproduces
that exact block is `256^-16 = 2^-128` (`256^-15 = 2^-120` after conditioning
on the last byte already being `0x10`). This is a strong cryptographic oracle
even if the payload is not printable text.

Almost every uniformly random 32-byte string is a valid secp256k1 scalar
because the curve order is extremely close to `2^256`; scalar range validity
alone adds negligible evidence after the padding test. Derived public addresses
and real on-chain relationships can provide secondary confirmation, but only
after the exact padding oracle fires.

The phrase `half and better half` should therefore not automatically be forced
into the password derivation. Its most literal local role may be to describe
the two-key output.

## Existing coverage versus the real gap

Existing audits establish useful negative boundaries:

- the complete normalized Phase 3.2.2 answer and selected fragments, including
  `halfandbetterhalf`, were tested as direct password candidates;
- selected Phase 3.2.1 phrases were tested as direct password candidates;
- the Phase 3.2.1 speech was mechanically split into individual README lines,
  and those lines were tested separately;
- candidates received common case/letters-only forms plus raw, SHA-256-hex,
  and double-SHA-256-hex password treatment;
- those families produced no hit against P32 under the recorded oracle.

Those negative results close direct reuse of the tested strings. They do not
exhaust:

- the complete exact Phase 3.2.1 Beaufort plaintext as one hash preimage;
- the complete Phase 3.2.1 and 3.2.2 outputs concatenated in source order;
- an operation specified by 3.2.1 and applied to the 3.2.2 output;
- ordered combinations of independently solved sibling answer parts;
- exact byte-level whitespace and line-ending variants from the authenticated
  Phase 3.2 decryption rather than its README transcription.

Accordingly, the earlier statement that the readily available P32 password
material is exhausted should be read narrowly: direct sentence/fragment reuse
has broad negative coverage, but the sibling-composition model remains open.

## Ranked candidate families

| Priority | Proposed password preimage | Motivation | Main ambiguity |
|---|---|---|---|
| 1 | Prime-selected text from the 91-character 3.2.2 output | Direct operator/data relationship between the siblings | Exact source rail, event boundary, and indexing |
| 2 | Complete exact 3.2.1 Beaufort plaintext | Prior phases hash complete answer constructions; existing sweep split the speech into lines | Exact original bytes and normalization |
| 3 | Complete 3.2.1 plaintext followed by complete 3.2.2 plaintext | Preserves authenticated sibling order | Whether full texts or only solved answers are intended |
| 4 | Grounded 3.2.1-derived selection followed by the salient 3.2.2 answer | Mirrors ordered-answer concatenation in prior stages | Which selected result is authenticated enough to use |
| 5 | The two internal cipher-solution parameter sets in order | Treats the sibling mini-solves as heterogeneous answer parts, like Phase 3's seven parts | Which parameters count as answers |
| 6 | Half/interleave constructions over an independently fixed source | Gives `half and better half` an operational role | No current clue fixes the source or split operation |

## Candidate family A — operator plus 3.2.2 data

This is the leading family.

```text
authenticated source/prime event rail
-> Phase 3.2.1-directed selection
-> positions in the 91-character Phase 3.2.2 output
-> selected password text
-> SHA-256 hex
-> OpenSSL decryption of P32_TRAILING
```

Only source-grounded alternatives should be admitted. Candidate variants must
declare, before decryption:

- the source that fixes the event rail;
- whether positions are zero- or one-based and why;
- whether exactly 23 or all 25 reconstructed events are consumed;
- how the actual 15 single selections and 8 double selections are serialized;
- whether the 91-character output is connected uppercase text or retains
  spaces;
- whether a 7x13 or 13x7 layout is required and what clue fixes it;
- whether the selected text itself or its SHA-256 hex is passed to OpenSSL.

An English-looking selection is not required. Correct P32 decryption, not the
appearance of the candidate preimage, is the endpoint oracle.

## Candidate family B — whole solved texts

The existing sentence-level audit did not treat the entire Beaufort speech as
one exact candidate. The smallest bounded whole-text family is:

1. complete 3.2.1 plaintext alone;
2. complete 3.2.2 plaintext alone as a regression against existing coverage;
3. complete 3.2.1 followed by complete 3.2.2;
4. complete 3.2.2 followed by complete 3.2.1 as a lower-priority control.

For each, use only documented normalization forms:

- exact decrypted bytes;
- original text with canonical LF line endings;
- connected text with whitespace removed;
- letters-only text;
- source casing and uppercase;
- a final newline only where the historical hashing workflow motivates it.

The exact byte source should be the authenticated Phase 3.2 AES plaintext,
freshly decrypted with the known password. README text is useful for display
and anchors but should not silently define trailing spaces or line endings.

## Candidate family C — internal solution parameters

The two sibling mini-solves require compact, independently identified answer
parts.

Phase 3.2.1 supplies or uses:

```text
EBCDIC
1141
BEAUFORT
THEMATRIXHASYOU
```

Phase 3.2.2 supplies or uses:

```text
VIC / STRADDLING CHECKERBOARD
FUBCDORA.LETHINGKYMVPS.JQZXW
1
4
```

A narrowly bounded concatenation family may preserve those parts in source
order, for example:

```text
THEMATRIXHASYOUFUBCDORA.LETHINGKYMVPS.JQZXW14
1141THEMATRIXHASYOUFUBCDORA.LETHINGKYMVPS.JQZXW14
EBCDIC1141BEAUFORTVIC14
```

These are hypotheses, not privileged candidates. Every included token must be
classified as a clue answer, cipher parameter, or operation name. Do not mix
classes freely or permute them without a selector.

## Candidate family D — ordered salient outputs

The 3.2.1 plaintext contains several conspicuous terminal or instruction-like
pieces:

```text
SOURCE CODES
PRIME BASICS
23 / 16 / 7
ACTUAL PRIVATE KEYNOTE
CIAO BELLA O
```

The 3.2.2 output contains:

```text
IN CASE YOU MANAGE TO CRACK THIS
THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF
THEY ALSO NEED FUNDS TO LIVE
```

Most of these have already failed individually. Their remaining justified role
is as ordered answer parts in a composition, not as an unrestricted Cartesian
product. A candidate in this family needs a textual reason for both inclusion
and ordering.

## Hashing and KDF discipline

The default first test should match the established chain:

```text
preimage = normalized ordered answer material
password = SHA256(preimage).hexdigest()
decrypt  = OpenSSL-compatible salted AES-256-CBC
```

Historical OpenSSL digest/KDF variants may remain regression coverage, but they
should not obscure the primary test. Passing a newly computed raw digest,
double-hashing, XORing sibling hashes, HMAC, or using alternate ciphers belongs
in a secondary tier unless an authenticated clue selects that operation.

The creator's `HASHTHETEXT` hint is already accounted for in the documented
route to the SalPhaseIon URL: it instructs hashing the Stage-0 banner text and
prize address. It should not be misrepresented as a direct P32 instruction.
It nevertheless confirms that literal text hashing is part of the puzzle's
established operator vocabulary.

## Success criteria

A candidate is promoted only if it produces reproducible P32 decryption with
one of these strong outcomes:

1. coherent plaintext that identifies itself and fits the surrounding clues;
2. exactly 64 payload bytes followed by a complete 16-byte PKCS#7 padding
   block, with both 32-byte halves valid as Bitcoin private-key scalars;
3. another cryptographically strong internal structure fixed before the test.

For a two-key result, validation must include:

- each scalar is in the valid secp256k1 private-key range;
- derived public keys and addresses are computed reproducibly;
- any claimed relationship to known puzzle addresses is exact;
- no funds are moved and no external transaction is attempted as part of
  validation.

Printable padding alone, an isolated English fragment, or a thematically
suggestive wrong-length output is not sufficient.

## Proposed bounded execution order

1. Re-decrypt Phase 3.2 and preserve the exact plaintext bytes and digest.
2. Extract exact byte ranges for the 3.2.1 encoded block, decimal stream,
   sibling clue text, and trailing blob.
3. Reconstruct the complete 3.2.1 and 3.2.2 solved plaintexts with explicit
   provenance for every normalization.
4. Run the whole-text family before constructing new transformations.
5. Run the operator-plus-data prime-selection family with every ambiguity
   declared in advance.
6. Run the compact internal-parameter concatenations.
7. Run only independently justified salient-output compositions.
8. Record candidate counts, unique preimages, hash preimages, exact OpenSSL
   parameters, and negative results so later work cannot overstate coverage.

## What not to do

- Do not treat prior line-level negative tests as proof that full sibling
  composition is exhausted.
- Do not generate arbitrary permutations of phrases from the two plaintexts.
- Do not infer names or personal details from `half and better half`.
- Do not expand into general Matrix quotations without a local selector.
- Do not accept readable noise without exact padding and structural checks.
- Do not move, import, sweep, or otherwise use a recovered private key on a
  network during validation.

## Current assessment

The highest-value reading is:

```text
3.2.1 = how to construct or select the password
3.2.2 = what to select from and what successful plaintext represents
P32    = the encrypted two-key payload
```

This model explains why the three objects are siblings, why the Architect
speech contains operational language, why the VIC output explicitly mentions
two private keys, and why P32's ciphertext length is compatible with two raw
32-byte scalars. It is not yet a solution, but it defines a smaller and more
faithful search space than treating every phrase as an independent password.

## Execution update — 2026-08-14

`tools/gsmg/p32_sibling_password_audit.py` now performs the bounded first pass.
It independently reproduced:

- the 2,422-byte authenticated Phase 3.2 plaintext, SHA-256
  `b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34`;
- the exact 1,539-byte embedded Phase 3.2.1 block;
- the ISO-8859-1 to CP1141 conversion and 1,539-letter Beaufort output;
- the 91-character Phase 3.2.2 checkerboard output;
- the trailing blob as the exact final bytes of the decrypted parent payload;
- the five-block P32 geometry and full-block `0x10` oracle.

The script tested 25 disclosed preimages, each raw and as a single SHA-256 hex
password, under six bounded AES/OpenSSL KDF specifications: 300 structural
trials in total. The tested families were complete sibling texts in both
orders, the established 31-character selection and two combinations, literal
Stage-0 zero-based prime-colored-cell material, its in-range projection onto
the 91-character answer, zero- and one-based pure-prime-index controls over the
91-character answer, four compact sibling-parameter constructions, and the
exact authenticated parent bytes preceding P32 both with and without the final
CRLF separator, and five direct split-final-`be` guide consumers.

**Result: zero exact full-padding/two-key hits.** This closes those 25 named
preimages under the six recorded KDF specifications. It does not close an
unknown selection rule, arbitrary cross-products of phrases, or a different
cipher/KDF without independent support.

The distinctiveness check also corrected the motivating count claim. The
prime walk is `23 events / 15 singles / 8 digraphs`; the exact `23/16/7`
profile belongs to the separate split-final-`be` guide. Under a strict declared
inventory, the solved chain through Phase 3.2.2 contains five cryptographic
operations, or nine transforms after including EBCDIC transcoding and the
three SHA-256 password derivations—neither approaches 16 or 23. This favors
screenplay inheritance or thematic reuse over a literal whole-puzzle operation
count, while leaving the sibling/operator-data hypothesis open in forms not
yet specified by an authenticated selector.

The split-guide prime retarget produces
`NCSYANGCAHIRIASOGALEAFAYANESTV`, exactly the established 31-character
selection minus its terminal `E` and consistent with the historical “30 or
31” description. Literal cumulative guide-token and raw-character endpoints
produce `NCSYAAORTERKBLTATRNEAED` and `NCSYNGCAIIASOGLEAAANETE` respectively.
All three strings, plus the two parity sibling combinations of the
30-character result, are negative under the structural oracle. The exact
`23/16/7` referent is real but does not yield the P32 password through these
direct consumers.
