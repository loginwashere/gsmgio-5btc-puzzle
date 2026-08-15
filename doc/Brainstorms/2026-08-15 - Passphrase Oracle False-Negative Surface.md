---
type: hypothesis
status: live
date: 2026-08-15
topics:
  - brainstorm
  - password-oracle
  - statistical-gates
  - multiple-testing
  - false-negatives
  - cryptography
  - coverage
  - cosmic-duality
  - base64
---

# Oracle Pipeline False-Negative Surfaces

> [!caution] Scope
> This is a design and reopening brainstorm, not evidence that any previously
> tested candidate is correct. It distinguishes a negative under a declared
> oracle from proof that a password is wrong. No real candidate was promoted
> while preparing this note.

## Executive result

Yes, through two separate mechanisms that should be combined rather than
confused:

1. **Upstream screening:** a statistical or structural stop-rule can prevent a
   derived output from ever reaching a blob oracle.
2. **Downstream acceptance:** a correct decryption can reach the shared blob
   oracle and still be rejected because its plaintext shape is not one of the
   registered validators.

The first mechanism is likely the more consequential risk for the fresh
DBBI/FAED models because several audits intentionally generated no candidate
and ran no password oracle after their family gate failed. The second remains
real and independently demonstrated below.

This is not only a theoretical concern. A synthetic known-correct password was
run through the repository's real shared functions. The password correctly
decrypted an 80-byte AES-CBC ciphertext to a 65-byte binary body with valid
15-byte PKCS#7 padding, but `aes_try_open_bytes()` returned `None`.

The current oracle recognizes three particularly useful shapes well:

1. sufficiently ASCII-like padded plaintext;
2. exactly 64 arbitrary bytes followed by a complete 16-byte AES padding
   block; and
3. self-authenticating AES-Key-Wrap output.

It does **not** generically recognize “the decryption was correct.” For
unauthenticated CBC/ECB/stream encryption, no generic local test can do that.
The implementation instead applies clue-driven and statistical acceptance
rules. Those rules are valuable filters, but every negative inherits their
blind spots.

The practical conclusion is not “rerun everything.” It is:

- describe negatives as coverage contracts;
- let stop-rules block broad/adaptive follow-up searches while allowing a
  separately bounded sentinel check when one canonical output already exists;
- preserve padding-valid decryptions separately from promoted hits;
- make plaintext validators explicit and composable;
- return all matches rather than the first one;
- replay only the small, high-value candidate families first; and
- reopen a large historical run only when the new validator could detect an
  output shape the old run could not.

## What a “password check” actually contains

The project often speaks about one oracle, but the observable result is a
pipeline with at least seven independent rejection surfaces:

```text
source artifact / model
  -> declared transform and statistical family
  -> structural promotion gate
  -> canonical output or authorized follow-up
  -> source candidate
  -> candidate inclusion
  -> textual normalization / byte encoding
  -> raw, SHA-hex, double-SHA-hex, or other material treatment
  -> target + KDF + cipher + mode selection
  -> decryption and padding handling
  -> plaintext/output validator
  -> hit recording, checkpointing, and reporting
```

A correct intended password can disappear at any arrow. It is useful to name
the resulting classes separately.

| Class | Meaning | Typical example |
|---|---|---|
| Promotion-gate false negative | A real but weak/noisy model is stopped before a candidate exists | corrected p fails, so BWT or gap interpretation never runs |
| Candidate false negative | The intended source string never enters the run | a whole paragraph was split into lines only |
| Material false negative | The string enters, but the intended bytes do not | trailing space disabled; raw SHA-256 digest omitted |
| Cryptographic-model false negative | Correct bytes reach the wrong algorithm | PBKDF2 iteration count or cipher mode not tested |
| Acceptance false negative | Correct plaintext is decrypted and then discarded | binary body fails the printable threshold |
| Accounting false negative | A valid result exists but is hidden or lost | first-match return suppresses later matches; swallowed worker error |

These are different claims and require different remedies. Increasing a
dictionary does nothing for an acceptance false negative. Lowering a
printability threshold does nothing for an omitted KDF.

## Upstream statistical gates

### The concern is valid

Family-wise correction deliberately trades power for false-positive control.
A real but modest structural effect can fail a conservative promotion gate,
especially as more related metrics are registered. If failing the gate also
prevents an independently decisive endpoint from being tried, the gate creates
a pipeline-level false-negative path:

```text
real weak/noisy structure
  -> raw effect survives
  -> family correction fails
  -> downstream transform or candidate withheld
  -> exact endpoint never queried
```

That is more consequential than merely reporting one underpowered p-value. It
changes which hypotheses ever receive the strongest available falsification
test.

The correction itself is not the mistake. It answers whether the structural
family is independently surprising. The questionable step is treating that
answer as an absolute prohibition on a cheap endpoint check when the endpoint
has already been fixed without inspecting the statistical result.

### Important endpoint qualification

“Valid PKCS#7 padding” has essentially no false-negative risk **conditional on
the correct cipher/KDF and an actually PKCS#7-padded plaintext**: the right key
will reproduce the pad exactly. It is not, however, cryptographic
authentication. A random CBC plaintext has valid PKCS#7 with probability close
to `1/255`. The repository's ordinary shared oracle reduces false positives by
adding printability or the exact 64-byte/full-padding structure, which
reintroduces the downstream false-negative surface documented in this report.

The strongest sentinel endpoints are therefore, in descending order:

1. exact P32 64-byte body plus sixteen `0x10` bytes (`2^-128` accidental-pad
   probability), AES-Key-Wrap integrity, an exact known address, checksum, or
   known plaintext;
2. ordinary valid padding plus a predeclared, independently identifying
   plaintext validator; and
3. ordinary shared-oracle printability, useful as a screen but neither exact
   nor false-negative-free.

Any sentinel policy must count its complete candidate × material × target ×
variant family. Calling the endpoint “exact” does not erase multiple testing;
it can make the total accidental-hit probability negligible when its
per-attempt validation is strong enough.

## What the named gated models actually leave behind

The cheap-bypass idea works only if the gated stage already emits one fully
defined byte/string candidate. Several fresh models stop one step earlier:
their failed gate blocks the operation needed to create a candidate at all.

| Model | Best raw result | What was withheld | One canonical candidate already exists? | Sentinel disposition |
|---|---:|---|---|---|
| MTF → BWT | minimum raw `p=0.128894`; most measures much larger | 91 + 570 primary-index inversions and selection among them | **No.** MTF emits two direct streams, but BWT inversion still requires an unauthored primary index/terminator | Keep BWT stop-rule. Testing a “best BWT output” would first require the prohibited scan |
| Base-81 tokens | DBBI pair MI `p=0.005450` → corrected `0.065397`; FAED adjacent repeats `p=0.019649` → `0.235788` | lookup, crib, homophonic meaning, or password material | **Not semantically.** The token integers are fixed, but no byte/text serialization or consumer is authored | Eligible only for an explicitly labeled raw-token-byte sentinel, not for lookup/codebook mining |
| GF(9) FAED complexity | `p=0.043956` → corrected `0.351648` | alternate field mapping, syndrome, recurrence consumer | **No.** Low complexity is a property/statistic, not decoded plaintext | Do not invent a polynomial/complexity password merely to reach the oracle |
| Crib recurrence | aligned-other surprisal `p=0.055888` → corrected `0.223553` | promotion of a fitted recurrence/placement | **Almost, but not yet.** A winning coefficient row exists; a full-stream decode and serialization were not registered as password material | A bounded sentinel is defensible only after freezing which leader, source, span, and serialization—without choosing by oracle outcome |
| Arithmetic coding | no p-value; four exact declarations fail canonical/source round-trip and lack authored termination | use of diagnostic fixed-length decodes as plaintext/passwords | **Yes, four declared diagnostic strings exist**, but the problem is under-specification rather than Type-II screening | Optional four-output diagnostic sentinel; it cannot repair missing EOS/normalization or validate the general arithmetic model |
| Sequence alignment | best fixed-lane `p=0.086457` → corrected `0.259370`; best sliding `p=0.282359` | interpretation of seven insertion/deletion pairs | **No.** The alignment is fixed, but password bytes require a new rule selecting operations, residues, gaps, or aligned text | Keep the interpretation stop-rule unless a single serialization is frozen independently |

Two corrections to the initial intuition matter:

- MTF and sequence alignment were not near misses in their tested family
  statistics; their raw minima were about `0.129` and `0.086`, respectively.
- Arithmetic coding did not fail a multiple-testing correction. It failed an
  exact declared round-trip/termination specification and therefore belongs to
  a different risk class.

Base-81 is the clearest statistical near-signal: its DBBI pair mutual
information is raw `p=0.00545` but misses the twelve-test `0.01` family gate
after correction. Yet even there, the gate did not suppress a ready-made word;
it suppressed choosing a codebook or interpretation. The endpoint oracle
cannot rescue an output that has not been uniquely defined.

## Combined stop-rule policy

The best hedge is a two-lane policy, not a one-off exception made only for raw
p-values that looked interesting after the fact.

### Lane A — confirmatory structural promotion

Keep the present corrected family gate. Passing it can authorize the broader
next stage described in the model: a BWT index scan, codebook family, gap
interpretation, parameter expansion, or downstream composition.

Failing it continues to mean:

- the structural evidence did not validate the model family; and
- no adaptive or multi-branch continuation is authorized.

### Lane B — unconditional canonical sentinel

For future models, allow one sentinel output per model regardless of the
p-value **only when it is frozen in the model specification before null
calibration**. The sentinel may receive the existing bounded material forms and
blob targets, with every cryptographic attempt counted.

A sentinel must satisfy all of:

1. candidate bytes are fully defined without a second search or output
   inspection;
2. no unauthored index, codebook, alphabet, placement, or gap interpretation
   is needed;
3. material treatments and target/variant scope are fixed in advance;
4. endpoint evidence is strong enough for the resulting attempt count; and
5. a negative sentinel does not strengthen the p-value result beyond its
   actual scope, while a hit requires independent reproduction and inspection.

This preserves the reason for the stop-rule while closing the sharpest
pipeline false-negative path. The statistical gate decides whether a *family
expands*; it does not veto a fixed, nearly free endpoint query.

### Retrospective backfill rule

Selecting only the models with attractive raw p-values now is necessarily
post-hoc. It can be useful as exploratory coverage, but it cannot be presented
as a preregistered confirmation. A cleaner one-time backfill is:

- inventory all sixteen model audits;
- include every already-materialized canonical output, not only low-p models;
- exclude models requiring a new interpretation or branch search;
- deduplicate exact candidate bytes;
- run one disclosed material/target/variant contract; and
- label the result “sentinel backfill,” not model promotion.

This should remain small. The purpose is to catch a model whose unremarkable
structure nevertheless lands exactly on the final lock, not to convert the
blob oracle into a selector across thousands of undefined transforms.

### Recommendation on the proposed bypass

**Worth doing, with a modification:** do not bypass based solely on “raw
`p < 0.05` before correction,” and do not override stop-rules that prevent
candidate creation. Add the unconditional canonical-sentinel lane, then run a
transparent retrospective backfill only for outputs already fixed by their
audits.

For the specifically named models:

- arithmetic coding's four fixed diagnostic outputs are cheap and eligible;
- base-81's raw token bytes are arguable but must be labeled a new byte
  serialization, not a decoded token meaning;
- crib recurrence needs one frozen full-stream construction before it becomes
  eligible;
- MTF→BWT, GF(9) complexity, and sequence-gap interpretation should remain
  stopped because no single downstream candidate presently exists.

The stop-rule discipline therefore still holds where it prevents adaptive
search. It need not be interpreted as forbidding every independently bounded
sentinel query.

## Direct synthetic controls run on 2026-08-15

The following controls used the real `cb_common` functions and the real
`cryptography` backend. Every case used a known password and ciphertext built
from the stated plaintext. `accepted=False` therefore means a demonstrated
oracle false negative, not a guessed risk.

| Case | Body bytes | PKCS#7 pad | Printable z | Accepted |
|---|---:|---:|---:|---:|
| CBC, 65 ASCII `A` bytes | 65 | 15 | 10.237 | yes |
| CBC, arbitrary binary bytes 0–63 | 64 | 16 | 2.700 | yes, exact structural exception |
| CBC, arbitrary binary bytes 0–64 | 65 | 15 | 2.837 | **no** |
| CBC, valid UTF-8 Cyrillic text | 66 | 14 | -6.398 | **no** |
| ECB, 65 ASCII `A` bytes | 65 | 15 | 10.237 | yes |
| ECB, arbitrary binary bytes 0–64 | 65 | 15 | 2.837 | **no** |
| CFB, 80 ASCII `A` bytes | 80 | none | 11.357 | yes |
| CFB, arbitrary binary bytes 0–79 | 80 | none | 4.687 | **no** |
| Raw AES key, CBC binary body of 65 bytes | 65 | 15 | 2.837 | **no** |

The primary reproducer used password `b"known-correct-password"`, salt
`b"12345678"`, body `bytes(range(65))`, legacy SHA-256 EVP_BytesToKey, and
AES-256-CBC. Encrypting the body with ordinary PKCS#7 produced 80 ciphertext
bytes. Calling the real helper with exactly that password, variant, salt, and
ciphertext returned `None`; direct decryption recovered the original body and
valid fifteen-byte padding.

The controls do not imply that Cyrillic or a 65-byte binary payload is likely
for GSMG. They prove that the oracle's result is conditional on output shape,
even when password, KDF, cipher, salt, IV, mode, and padding are all correct.

The shared built-in self-tests and the ten tests in `test_cb_common.py` also
passed during this review. There is no observed regression in the paths those
tests cover. The issue is incompleteness of the acceptance contract, not a
failure of the established positive vectors.

## Confirmed acceptance boundary

### Padded CBC

`aes_try_open_bytes()` first requires valid PKCS#7 padding. It then returns a
hit only when either:

- the plaintext reaches printable `z >= 8`; or
- it has the exact AES shape `pad=16` and `len(body)=64`.

Bodies with `5 <= z < 8` are appended to the global weak-candidate log but are
not returned. Bodies below `z=5` disappear completely.

For an 80-byte ciphertext such as SALPH or P32TRAILING, ordinary PKCS#7 permits
body lengths 64 through 79. The strong printable threshold is demanding at
these lengths:

| Body length | Printable bytes needed for `z >= 8` | Required ratio |
|---:|---:|---:|
| 64 | 56 | 87.5% |
| 65 | 57 | 87.7% |
| 72 | 61 | 84.7% |
| 79 | 65 | 82.3% |

The 64-byte full-padding exception protects the clue-supported “two raw
private keys” shape. The other fifteen valid lengths receive no general binary
exception. A nested ciphertext, compressed record, serialized object, mixed
text/binary message, or non-ASCII text can therefore decrypt correctly and
still be reported as no hit.

COSMIC's much longer body needs only about 49% recognized printable bytes to
reach `z=8`, so long mixed messages receive substantially more tolerance than
short ones. Truly high-entropy binary still fails.

### ECB

The ECB helper uses the same padding, printability, and exact-64-byte
structural rules. It therefore has the same demonstrated 65-byte binary false
negative.

### Stream-like CFB/OFB/CTR

These modes have no padding oracle. Every output goes directly to the
printability score. A correct binary or non-ASCII output has no generic route
to a hit. The synthetic 80-byte CFB binary control was rejected.

### Direct raw keys

`raw_key_try_open()` validates padding and then applies only the printable
thresholds. It does not use the exact 64-byte structural exception that the
passphrase-derived CBC/ECB helpers use. The same clue-compatible binary shape
can therefore be retained through one entry point and discarded through
another.

### AES Key Wrap

Key Wrap is the strongest current pattern. RFC 3394/5649 integrity validation
is part of the mode, and every successful unwrap is returned without a
printability gate. This is the right separation: cryptographic validity first,
plaintext interpretation afterward.

### `-nopad` CBC/ECB

The specialized `nopad_window_sweep.py` is not a generic no-padding plaintext
oracle. It searches pre-registered private-key representations and relations:

- aligned 32-byte windows;
- operations over the selected half-pair;
- secp256k1 public-point forms;
- aligned ASCII-hex keys;
- checksum-valid WIF strings;
- known, funded/Bloom, and vanity-address signals.

This provides important overlapping protection for “P32 decrypts to keys,”
including cases where padding is not stripped first. It does not recognize an
arbitrary unpadded readable message, compressed object, nested ciphertext, or
binary record without one of those key structures.

## Target-specific implications

### P32TRAILING

The exact two-raw-key hypothesis is better protected than the synthetic
65-byte counterexample might initially suggest:

- padded CBC/ECB recognizes exactly 64 bytes plus full padding;
- the no-pad path examines raw fixed windows and clue-supported half
  operations without depending on PKCS#7; and
- post-hit address checks provide a possible external confirmation layer.

Accordingly, completed runs that used both paths against the same candidate
materials should not be reopened merely because generic binary output can be
missed.

However, recent focused audits did not all use both paths:

- Phase 265/267/269-style “standard oracle” calls use the printable/structural
  shared oracle, not the no-pad address oracle;
- Phase 270's sibling-output audit deliberately recognizes only the exact
  64-byte/two-key/full-padding model and only six declared AES/KDF specs; and
- a correct P32 plaintext of 65–79 bytes that is not highly printable and is
  not represented by the fixed key windows remains outside those conclusions.

That does not falsify the Phase 270 result. It narrows its wording to what the
code actually tested: the exact two-key structural model, not every possible
correct decryption of P32.

### SALPH

SALPH has the same 80-byte ciphertext geometry but lacks an equally strong,
uniquely selected plaintext format. It therefore has the largest practical
acceptance blind spot among the short targets: 65–79-byte low-printability
decryptions are discarded unless another dedicated script happens to
recognize their content.

### URLBLOB

Its 96-byte ciphertext permits bodies of 80–95 bytes. There is no exact
64-byte structural exception at any permitted length. Correct short binary or
non-ASCII plaintext is therefore governed entirely by the printable gate or a
separate specialized checker.

### COSMIC

Length makes its printable z threshold more forgiving, and the known Phase
3.2 control demonstrates that a long mixed text/binary message can clear it.
The remaining concern is a predominantly binary payload, nested encrypted
stage, or file-like object.

## Candidate/material coverage is not uniform

The name “standard oracle” currently hides materially different candidate
contracts.

`answer_forms()` supplies:

- the input as given;
- whole-string upper/lower case;
- letters-only input;
- letters-only upper/lower case.

`keystr_forms()` supplies, for each enabled base:

- raw text bytes;
- SHA-256 hexadecimal text;
- SHA-256 of that hexadecimal text, again represented as hex;
- optional LF and CRLF forms; and
- optional trailing-space forms.

Important exclusions or inconsistencies include:

- newline and trailing-space forms are caller options, not universal;
- many loaders call `.strip()`, making original leading/trailing whitespace
  unrecoverable before optional forms are generated;
- raw SHA-256 digest bytes are added by some focused audits but not by
  `keystr_forms()` itself;
- Unicode normalization is not explicit;
- UTF-8 is assumed by text wrappers;
- tab, multiple-space, leading-space, and other exact source-byte variants are
  not a bounded shared family; and
- historical full-text, line, sentence, and fragment boundaries differ by
  audit.

This is not an argument to multiply arbitrary whitespace. It is an argument
that a result must state exactly which material forms were tested.

## Cipher/KDF coverage is also layered

The shared default CBC helper is narrower than the wrapper commonly described
as the full standard oracle.

| Layer | Included scope |
|---|---|
| `KDF_VARIANTS` | legacy EVP_BytesToKey; SHA-256/MD5/SHA-1; AES-256/128-CBC |
| `EXTENDED_CIPHER_VARIANTS` | AES-192 and 3DES CBC; legacy and PBKDF2-SHA256/10000 |
| menu-gap variants | Blowfish, Camellia, and SEED CBC; opt-in |
| stream variants | AES CFB/OFB/CTR; legacy and PBKDF2-SHA256/10000 |
| ECB variants | AES ECB; legacy and PBKDF2-SHA256/10000 |
| Key Wrap variants | AES RFC/OpenSSL wrap forms; legacy and PBKDF2-SHA256/10000 |

`color_mask_full_stream_audit.passphrase_hits()`, reused by many recent
audits, includes CBC default + extended, stream, ECB, and Key Wrap. It does
not include the menu-gap CBC family. Phase 269 adds that family explicitly;
several other audits do not.

Still-unmodeled possibilities include non-default PBKDF2 iteration counts,
other PBKDF2 digests, explicit/raw keys under modes beyond the current raw-key
helper, unsalted containers, alternate padding conventions, and algorithms
outside the bounded OpenSSL-era menu. Most are weak without a clue. Their
existence means “all cryptographic possibilities” should never be inferred
from “all registered variants.”

One already-documented corpus gap also remains relevant: FINDINGS Phase 163
states that the combined Tier-1/2/3 corpus of 66,441 candidates has never been
run through padded CBC/ECB `EXTENDED_CIPHER_VARIANTS`; only the curated 648
have. That is a candidate-by-variant coverage gap, separate from the
acceptance-gate issue established here.

## Result and accounting hazards

### First match wins

The CBC, ECB, and stream helpers return immediately on the first strong match.
They do not yield every matching `(material, target, variant)` result. For an
ordinary zero-hit question this usually makes no difference. At very large
attempt counts, an accidental earlier plausibility hit can suppress a later,
more meaningful target/variant result for the same material.

All-hit iteration is safer and makes target coverage auditable.

### Weak-log ambiguity

The weak log is global and append-only. A `z=5..8` result is not returned to
the caller, and the log itself is not tied to the caller's run manifest in the
same way newer checkpointed sweep outputs are. A report can therefore say
“zero hits” while a weak candidate was written elsewhere. Bodies below `z=5`
leave no trace at all.

### Broad exception suppression

Several decrypt paths catch `Exception` around backend finalization and simply
continue. Invalid geometry is already checked separately, so unexpected
backend errors should be counted and should fail or taint a run rather than be
indistinguishable from a wrong password.

### Wrapper drift

Multiple audit files locally reimplement `material_family()` or `run_oracle()`.
They differ in newline forms, spaces, raw digests, menu-gap variants, target
scope, and result handling. This is how honest labels such as “full standard
oracle” gradually stop meaning one reproducible thing.

There is also a result-shape bug pattern worth cleaning up separately:
`aes_try_open_bytes()` returns one 4-tuple, while Key Wrap returns a list.
Some callers iterate `oracle(...) or ()` uniformly, thereby iterating the four
fields of a CBC hit as if they were four hits. That is primarily a hit-reporting
bug rather than a zero-hit false negative, but it demonstrates that the shared
API types are too easy to misuse.

## Why simply lowering the z threshold is insufficient

Lowering `z=8` to `z=5` would recover some mixed plaintext while restoring the
known large-sweep false positives already observed around `z=5.03`. It still
would not recover:

- mostly binary bodies;
- non-ASCII UTF-8;
- compressed/encrypted payloads;
- short output under stream modes; or
- a correct candidate omitted before decryption.

The design problem is categorical, not merely numeric. Printability should be
one validator and ranking feature, not the definition of successful
decryption.

## Proposed oracle architecture

### 1. Separate decryption evidence from promotion

Introduce an iterator with a stable result record for every attempted variant:

```text
DecryptResult
  target
  cipher / mode / KDF / key length
  material identifier
  outcome: geometry-invalid | decrypt-error | padding-invalid |
           padding-valid | integrity-valid
  padding length
  body length and SHA-256
  feature measurements
  validator matches
```

For CBC/ECB, `padding-valid` is evidence worth retaining, not a solution. For
Key Wrap, `integrity-valid` is much stronger. Promotion becomes a separate
policy operating on these records.

### 2. Make validators explicit

Validators should be independently named, tested, and selected before a run:

- ASCII/null-model score;
- exact 64-byte/two-key/full-padding structure;
- known plaintext prefix or delimiter;
- UTF-8 validity and Unicode text score;
- nested `Salted__` envelope;
- common file signatures, only if file output is clue-supported;
- WIF/Base58Check checksum;
- secp256k1 point relation;
- exact known/funded address;
- high-entropy binary retention, as a diagnostic tier rather than promotion.

No union of heuristic validators proves correctness. It makes the acceptance
scope legible and prevents one heuristic from silently vetoing all others.

### 3. Return all matches

CBC, ECB, and stream functions should yield lists/iterators like Key Wrap.
Callers can then record every target/variant match and cannot suppress a later
result through ordering.

### 4. Preserve padding-valid telemetry securely

Random CBC decryptions produce valid PKCS#7 padding with probability close to
`1/255`, so retaining full bodies for hundreds of millions of attempts is
costly and potentially sensitive. A workable two-level record is:

1. always retain a mode-0600 manifest entry containing material ID, target,
   variant, pad length, body length/hash, and validator features;
2. retain or deterministically reproduce the full body only for pre-registered
   validators, focused small runs, or manual review queues.

Candidate list digests and stable material IDs are mandatory if bodies are to
be reproduced later. A mutable wordlist plus an index is insufficient.

### 5. Count errors

Every run summary should include attempted, geometry-skipped,
padding-invalid, padding-valid, integrity-valid, promoted, weak, and error
counts. A run with errors is incomplete, not negative.

### 6. Emit a coverage contract

Every negative report should serialize:

```text
candidate source digest
candidate boundary policy
material-form policy
targets
cipher/KDF/mode variants
padding policy
validators and thresholds
oracle/driver source digests
completed/error counts
```

The prose verdict can then say: “zero promoted results under contract X.”

## Ranked experiment queue

### P0A — canonical-sentinel inventory

> [!info] Executed (2026-08-15)
> See [Canonical Sentinel Inventory (P0A)](<2026-08-15 - Canonical Sentinel Inventory (P0A).md>).
> 40 already-materialized candidates pass all five Lane B criteria (models
> 9, 15, 16), plus 2 more pending a one-line report fix (model 11). Model
> 10's outputs are self-flagged degenerate/tautological rather than merely
> weak -- excluded regardless of policy. No oracle call was made.

Audit the sixteen fresh DBBI/FAED model reports without running any new
transform. For each, record:

- every exact output already materialized by the declared model;
- whether its byte serialization was fixed before calibration;
- whether producing a candidate would require a new choice;
- exact duplicates across models; and
- the strongest applicable endpoint validator.

This inventory determines the retrospective backfill scope without selecting
only attractive raw p-values. It should produce a small manifest or establish
that a model has no oracle-ready candidate.

### P0B — regression harness, no historical reruns

Build permanent tests from the synthetic table above. The desired behavior is
not necessarily to promote all binary bodies. It is to prove that the new
low-level iterator records them as `padding-valid` while the promotion layer
classifies them separately.

Also add:

- a correct result under a later target/variant to prove all-hit iteration;
- a forced backend error that increments an error count and invalidates the
  run;
- raw-key exact-64-byte binary parity with passphrase CBC/ECB;
- a Unicode text validator control; and
- one wrapper contract test asserting the exact registered variant and form
  sets.

### P1A — bounded statistical-gate sentinel backfill

> [!info] Executed (2026-08-15)
> `tools/gsmg/p1a_sentinel_backfill.py`, FINDINGS.md Phase 290. All 40 P0A-eligible
> candidates (models 9, 15, 16), each in exactly two disclosed forms (literal,
> hex SHA-256 of literal), against all four tracked blobs under the default
> six KDF variants: 80 passphrase attempts, 1,920 effective decrypt attempts.
> **0 hits, 0 weak candidates (z >= 5).** Closed negative. No adaptive
> follow-up. Model 11's 2 conditionally-eligible candidates are not included
> (report plumbing fix still pending).

Run the P0A manifest through one disclosed material/target/variant contract.
Keep broad follow-up branches disabled. Record ordinary padding-valid events
separately from strong endpoint hits and charge every attempt to the backfill
family.

At minimum, the four already-fixed arithmetic diagnostic strings qualify.
Base-81 raw token bytes should enter only if the manifest explicitly records
that byte packing is a new diagnostic serialization. Do not include BWT rows,
GF(9) statistic-derived passwords, recurrence expansions, or alignment-gap
readings until one candidate is independently frozen.

### P1B — replay only recent, small, high-value P32 families

Before touching large dictionaries, replay the Phase 265–270 focused materials
against P32 with:

- all registered CBC variants, including menu gaps;
- ECB variants;
- both ordinary PKCS#7 classification and exact no-pad/key-structure checks;
- newline, CRLF, trailing-space, and explicitly justified raw-digest forms;
- all padding-valid telemetry, regardless of z-score.

This is the highest-value check because these candidates are locally selected,
small, and some were evaluated only through one acceptance shape. Expected
random padding-valid events must be reported as such and inspected without
promotion.

### P2 — SALPH short-binary focused replay

Replay the curated 648 against SALPH with the retention oracle. SALPH has the
same short geometry as P32 but no equally complete structural backstop. Rank
padding-valid bodies using pre-registered validators:

- readable/Unicode text;
- nested OpenSSL envelope;
- exact file signatures;
- 32/64-byte key layouts and WIF/Base58Check structures; and
- entropy/mixed-region diagnostics.

Do not invent a validator after viewing a body and then call it confirmatory.

### P3 — unify wrappers before any broad replay

Replace local `material_family()` copies with one manifest-producing runner.
Until this is done, a broad rerun risks producing another result whose exact
scope must be reconstructed from source archaeology.

### P4 — decide the documented 66,441-candidate padded gap explicitly

The full Tier-1/2/3 padded extended-CBC/ECB gap is real, but it is a substantial
candidate expansion rather than a clue-selected new model. Estimate operations
and wall time from the final unified contract, then decide separately whether
to run it. Do not let this implementation audit silently authorize a large
compute job.

### P5 — broaden cryptographic models only with evidence

Non-default PBKDF2 iterations, alternate padding, more ciphers, and unsalted
models remain possible. They should be added only when source provenance or a
specific implementation fingerprint selects them. Otherwise the multiple-
testing surface grows faster than the evidence.

## Ideas to avoid

- **Treat every valid pad as a hit.** At scale this creates large numbers of
  expected coincidences. Record it as evidence, not confirmation.
- **Lower printability until something appears.** This changes the test after
  observing the data and still misses truly binary output.
- **Add dozens of file signatures post hoc.** Signatures are useful only as a
  declared family with an appropriate family-wise interpretation.
- **Rerun all historical sweeps immediately.** First identify which negative
  depended on the changed acceptance rule and whether another specialized
  oracle already overlapped it.
- **Bypass only the low raw p-values.** Chosen retrospectively, that makes the
  sentinel itself another selection step. Inventory every already-canonical
  model output instead.
- **Call scalar range validity authentication.** Almost every random 256-bit
  value is a valid secp256k1 scalar; address or pair relations carry the useful
  evidence.
- **Conflate candidate exhaustion with password impossibility.** A finite
  source corpus can be exhausted under a contract; the unknown password space
  cannot.

## New reopening lead: COSMIC Base64 row 4 case imbalance

### The observation is exact and locally unusual

The fourth authored 64-character row of the Cosmic Duality blob is:

```text
SATSFO7IFBiAMz7dDqIETKuGlTAP4EmMQUZrQNtfbJsURATW6V5VSbtZB5RFk0O+
```

Its complete Base64-category counts are:

| Category | Observed | Uniform-Base64 expectation in 64 characters |
|---|---:|---:|
| `A-Z` | 41 | 26 |
| `a-z` | 15 | 26 |
| `0-9` | 7 | 10 |
| `+` | 1 | 1 |
| `/` | 0 | 1 |

The user-supplied `41/15/7` count is therefore correct, with the omitted 64th
character being one `+`. No other COSMIC row is close: the next-largest
uppercase count is 33. The known-solved Phase-3.2 control has 51 complete
64-character rows and a maximum uppercase count of 36.

### Cross-blob controls: unique maximum, weaker global evidence

A follow-up scan applied the identical fixed 64-character chunking and
category count to every authenticated solved AES blob and every tracked
unresolved blob available locally. Phase 2 and Phase 3 were extracted from
the authenticated archived `choice...` HTML; Phase 3.2 is the known-positive
README vector; SALPH, P32-trailing, and COSMIC are authenticated unresolved
artifacts; URLBLOB is retained separately as quarantined/unresolved.

| Blob | Status | Complete 64-char rows | Maximum uppercase | Row | Counts `U/L/D/+//` |
|---|---|---:|---:|---:|---|
| Phase 2 | solved | 14 | 32 | 1 | `32/22/10/0/0` |
| Phase 3 | solved | 85 | 37 | 25 | `37/19/5/2/1` |
| Phase 3.2 | solved | 51 | 36 | 5 | `36/21/5/2/0` |
| SALPH | unresolved | 2 | 32 | 1 | `32/21/10/1/0` |
| P32 trailing | unresolved | 2 | 22 | 2 | `22/25/15/0/2` |
| COSMIC | unresolved | 28 | **41** | **4** | **`41/15/7/1/0`** |
| URLBLOB | quarantined/unresolved | 2 | 24 | 2 | `24/25/14/0/1` |

Across all 184 complete rows, COSMIC row 4 is the **only** row with at least
41 uppercase characters. This confirms that the same directional event does
not recur in any solved control or other tracked unresolved target. Expanding
the directional look-elsewhere family from COSMIC's 28 rows to all 184 rows,
however, raises the uniform-row calibration for at least one `U >= 41` row to
`0.023688` (Bonferroni `0.023972`). Excluding each envelope's non-random first
`Salted__` row leaves 177 ciphertext-only rows and almost the same values:
Sidak `0.022797`, Bonferroni `0.023060`. It is unique but no longer below a
conventional `0.01` global gate.

The symmetric case-imbalance control is also important. The second-smallest
raw conditional case p-value occurs naturally in solved Phase 3, row 31:

```text
Phase 3 row 31: U=14, L=36, two-sided conditional p=0.002602
COSMIC row 4:   U=41, L=15, two-sided conditional p=0.0006856
```

Phase 3's event is not unusual after its 85-row family is counted
(`Sidak ~= 0.199`). COSMIC remains the strongest individual case split, but a
conservative correction of its two-sided p-value over all 184 inspected rows
is about `0.126`. This demonstrates directly that pronounced-looking case
imbalance can occur in a correctly generated, solved ciphertext.

Nor does the solved-versus-unresolved split currently distinguish the
classes. There are 34 complete rows among the four unresolved/quarantined
targets and 150 among the three solved controls. Conditional on exactly one
`U >= 41` event among 184 exchangeable rows, its chance of landing in the
unresolved group is `34/184 = 0.1848`. This is only a descriptive allocation
check—the first envelope rows are not identically distributed—but one event is
in any case too little evidence for a modification process specific to
unresolved blobs.

The scope deliberately excludes the many OpenSSL strings pasted or generated
inside community-chat logs: most are guesses, demonstrations, malformed
fragments, or newly encrypted examples rather than authenticated puzzle
artifacts. URLBLOB was never authored as wrapped Base64 (its source was a hex
URL path), so its 64-character chunks are analytical controls rather than a
claim about visual line layout. Phase 3 also has a final 44-character tail and
URLBLOB a final 24-character tail; incomplete rows are excluded from this
fixed-length comparison.

**Updated interpretation:** row 4 is the unique uppercase maximum in the
relevant local corpus, so the observation should not be discarded. The
expanded solved controls materially weaken a count-only intention claim,
because solved Phase 3 contains a comparably conspicuous opposite-direction
case split and the all-row corrections fail. The Bitcoin-relevant literal
`SATS` prefix and any authenticated evidence of manual edits—not the category
count alone—must carry the reopening case.

For a ciphertext-only interior row, treating each Base64 sextet as uniform is
the natural cryptographic null. Under that null:

- `P(U >= 41)` for one fixed row, with `U ~ Binomial(64, 26/64)`, is
  `0.00013028` (about 1 in 7,676);
- scanning all 28 COSMIC rows gives a Sidak family probability of `0.003641`
  (Bonferroni `0.003648`);
- conditional on the observed 56 letters, the one-sided case split
  `P(Binomial(56, 1/2) >= 41)` is `0.00034278`;
- making that case test two-sided and correcting over 28 rows gives about
  `0.0190` (Bonferroni `0.0192`).

These are descriptive calibrations, not a clean discovery p-value. Row 4,
uppercase direction, category count, case imbalance, runs, columns, and other
Base64 textures were not registered in advance. The true retrospective search
family is therefore larger than 28 rows and cannot be honestly reconstructed
from this observation alone. Conversely, if independently sourced evidence
really establishes that the author manually altered COSMIC's displayed
Base64, the directional uppercase test becomes much better motivated and the
observation deserves more weight.

### The conspicuous `SATS` prefix is separate evidence, but post hoc

Row 4 begins with the literal uppercase token `SATS`, a Bitcoin-relevant
abbreviation. That makes the row more interesting than a count-only outlier.
It must not be multiplied into the count p-value as though the token had been
specified in advance: it was recognized in the same inspected string, and the
space of potentially meaningful short tokens is large. Record it as semantic
texture and a possible selector, not independent confirmation.

Minimal secondary-channel readings do not immediately decode to text:

```text
uppercase positions over all 64 chars: FD D8 BD 75 EC 5F 59 B2
lowercase positions over all 64 chars: 00 25 42 82 13 A0 06 08
uppercase/lowercase over letters only: FF B2 F5 EF 62 FF 3D
```

The extracted uppercase-letter subsequence and lowercase-letter subsequence
also show no immediate plaintext. This rules out only the most literal bitmap
and case-bit readings; it does not justify searching arbitrary rotations,
transpositions, alphabets, or bit packings.

### Why manual Base64 editing is cryptographically possible

The row decodes to 48 bytes at full-envelope offsets `144..191`, equivalently
COSMIC ciphertext offsets `128..175`: zero-based ciphertext blocks 8, 9, and
10. In unauthenticated AES-CBC, changing those Base64 characters changes the
ciphertext but does not invalidate the envelope or necessarily disturb its
final PKCS#7 padding. If blocks 8-10 were edited, plaintext blocks 8-10 would
be garbled and block 11 would receive the corresponding CBC XOR delta; later
blocks, including the final padding block, would remain unaffected.

That yields two important consequences:

1. A deliberately modified early ciphertext can carry a visible Base64-side
   channel while still producing valid final padding under the correct key.
2. The padding sentinel should still discover the correct key. For a long,
   mostly textual 1,328-byte plaintext, corrupting at most four 16-byte blocks
   would probably still clear the shared printability gate as well. The row-4
   anomaly therefore does not by itself create a likely password-oracle false
   negative; it chiefly raises the possibility that a correct decryption may
   contain a localized damaged region or that the displayed ciphertext has a
   second channel.

If the manual changes instead happened before encryption, the ciphertext case
imbalance has no direct relation to the modification; proper encryption should
remove that structure. The precise provenance of the claimed manual changes is
therefore load-bearing.

### Bounded next test

Retain this as a **live, medium-priority reopening lead** and avoid a general
case-pattern transform sweep. The next admissible packet should be:

1. authenticate an older or alternate copy of the COSMIC Base64 from a
   primary archive, source file, or creator post;
2. byte-diff it against the current authenticated textarea;
3. test whether changes concentrate in row 4 and whether they are specifically
   case substitutions;
4. map any changed sextets to exact ciphertext and CBC plaintext-block effects;
5. predeclare at most the literal changed-position mask, its complement, and
   the changed characters as sentinel materials before querying any oracle.

Without an earlier version, freeze only the obvious diagnostics above. Do not
case-normalize row 4 and call the result a repaired ciphertext: there are many
possible original case assignments, and an oracle-guided repair would be an
enormous adaptive padding-oracle search. A future correct COSMIC decryption
should, however, be inspected explicitly for localized corruption in plaintext
blocks 8-11 rather than rejected solely because that region is noisy.

### Broader structural sweep, all seven tracked blobs: no additional anomaly

Five structural/statistical channels (charset, repeated ciphertext blocks,
salt bytes, base64 formatting, and bit-level randomness) were run against
all seven blobs -- Phase 2, Phase 3, and Phase 3.2 (solved; Phase 2/3 pulled
directly from the archived
`doc/html/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html`
mirror, not previously in `data.py`) alongside SALPH, P32-trailing, COSMIC,
and URLBLOB. None surfaces anything beyond the row-4 case-count texture
already documented above; several double as positive controls confirming
the methodology doesn't false-positive on known-genuine ciphertext.

| Blob | B64 len | Full 64-char rows | CT bytes | Entropy (bits/B) | Chi2 (255 dof) | Max upper | Dup 16B blocks |
|---|---:|---:|---:|---:|---:|---:|---:|
| Phase 2 (solved) | 896 | 14 | 656 | 7.667 | 256.4 | 32 | 0 |
| Phase 3 (solved) | 5484 | 85 | 4096 | 7.954 | 266.9 | 37 | 0 |
| Phase 3.2 (solved) | 3264 | 51 | 2432 | 7.931 | 224.6 | 36 | 0 |
| SALPH (unresolved) | 128 | 2 | 80 | 5.972 | 278.4 | 32 | 0 |
| P32-trailing (unresolved) | 128 | 2 | 80 | 5.928 | 284.8 | 22 | 0 |
| COSMIC (unresolved) | 1792 | 28 | 1328 | 7.864 | 249.3 | **41** | 0 |
| URLBLOB (quarantined) | 152 | 2 | 96 | 6.285 | 240.0 | 24 | 0 |

- **Charset/homoglyph.** All 7 blobs are pure ASCII and strictly within the
  base64 alphabet (`A-Za-z0-9+/=`). No visually-substituted Unicode
  lookalikes anywhere.
- **Repeated 16-byte ciphertext blocks.** Zero within any single blob and
  zero across all seven combined (83 + 5 + 5 + 6 + 41 + 256 + 152 blocks
  checked pairwise). Rules out shared plaintext blocks or IV/key reuse
  linking any two artifacts, solved or unsolved.
- **Salt bytes** (the 8 bytes following `Salted__`). All 7 salts are
  distinct. Byte diversity (7-8 unique bytes of 8) and printable-ASCII
  counts (2-5 of 8) are both consistent with ordinary random bytes; the two
  salts with one repeated byte (SALPH, URLBLOB) match birthday-paradox
  expectations at n=8 (~10% chance per salt) and are not individually
  meaningful.
- **Base64 formatting.** Every blob's ciphertext is cleanly 16-byte
  block-aligned. Phase 2/3's *source* HTML line-wrapping (read directly
  from the textarea, not the repo's re-wrapped constant) is uniform 64-char
  rows plus the expected short final row (44 chars for Phase 3). Padding
  (`=`) counts match each blob's byte length exactly. Nothing irregular.
- **Entropy is bias-explained, not suspicious.** SALPH/P32-trailing/URLBLOB's
  low raw entropy (5.9-6.3 bits/byte) tracks the theoretical finite-sample
  bias curve for genuinely random bytes almost exactly (expected ~5.70 at
  n=80, ~6.08 at n=96) -- confirmed by solved Phase 2 (656 bytes, unquestionably
  genuine) landing on the same curve at 7.667 vs. a ~7.72 prediction. Small
  blobs looking less random is a sample-size artifact common to solved and
  unsolved blobs alike, not a marker of tampering.
- **Chi-square (byte-value uniformity), monobit, and runs tests** (255 dof;
  bit-level NIST-style tests on ciphertext bytes) are non-significant for
  all 7 blobs, including the large, unquestionably genuine Phase 3 (4096
  bytes) and Phase 3.2 (2432 bytes). Phase 2's runs-test p-value (0.032) is
  the one borderline value in the set -- and it belongs to solved, genuine
  ciphertext, which is a useful reminder that occasional p<0.05 noise is
  expected and not itself informative without correction. COSMIC's own
  runs-test p-value (0.56) is unremarkable. Lag-1 byte autocorrelation is
  near zero for all seven (-0.09 to +0.09).

**Conclusion:** none of these five channels adds anything to the row-4 case
observation, and several strengthen confidence that the observation is
narrowly scoped. COSMIC's salt, block structure, formatting, and bit/byte-level
statistics are statistically indistinguishable from the solved controls --
the anomaly stays confined to the base64-character-case mapping of one
48-byte ciphertext span, not a broader property of the blob. This leaves the
bounded next test above (find and diff an authenticated earlier COSMIC copy)
as the only avenue that could actually move this lead forward.

## Suggested wording for future findings

Prefer:

> The run completed with zero promoted decryptions under the recorded
> candidate/material/variant/validator contract. It does not exclude omitted
> password forms, cryptographic models, or plaintext shapes.

For a gated model with no canonical output, prefer:

> The corrected structural gate failed, so the registered branching follow-up
> was not executed. No uniquely defined candidate existed for an endpoint
> sentinel; the downstream transform remains untested rather than negative.

For a model with an unconditional sentinel, prefer:

> The structural family did not promote, but its predeclared canonical output
> was independently checked under the sentinel contract and produced no
> endpoint hit. This does not validate or exhaust broader continuations of the
> model.

For the exact two-key model, stronger wording is justified:

> No tested material produced the exact 64-byte/two-key/full-PKCS#7 structure
> under the recorded variants. This closes that structural model for this
> candidate set; it does not close every possible P32 plaintext format.

Avoid:

> The password is wrong.

unless an external authenticator, exact known plaintext, or other
self-validating structure makes that statement warranted.

## Decision summary

| Decision | Recommendation |
|---|---|
| Can statistical gates create pipeline false negatives? | Yes; they intentionally trade power for error control and can block downstream tests |
| Should a failed gate still block adaptive family expansion? | Yes |
| Should it block one predeclared canonical sentinel? | No, when the endpoint family is fully counted and sufficiently strong |
| Should retrospective bypass select only low raw p-values? | No; inventory all already-canonical outputs |
| Which named model is the clearest raw near-signal? | Base-81 DBBI pair MI: raw `0.005450`, corrected `0.065397`, but no authored consumer |
| Do all named models have one candidate ready? | No; MTF→BWT, GF(9), crib recurrence, and sequence gaps still need choices |
| Is there a downstream acceptance false-negative class? | Yes; demonstrated end to end |
| Are the existing known-positive paths broken? | No; current controls pass |
| Is exact P32 two-key/full-padding coverage invalidated? | No; that narrow structure is protected |
| Are generic short binary/non-ASCII outputs covered? | No |
| Should all old sweeps be rerun? | No |
| First scope task | Inventory canonical outputs from all sixteen model audits |
| First implementation task | Add the sentinel contract; separately split decryption evidence from promotion |
| First model replay | Canonical-output sentinel backfill, then small Phase 265–270 P32 materials |
| First broader replay | Curated-648 SALPH retention run |
| Large corpus action | Estimate and authorize separately after wrapper unification |
| COSMIC row-4 uppercase anomaly | Retain as a real descriptive outlier; seek an authenticated earlier ciphertext before any repair/search |

## Reopening rules

For an upstream gated model, add a sentinel without reopening its broader
family only when:

1. exact candidate bytes already exist independently of the failed gate;
2. reaching them requires no new index, codebook, interpretation, or search;
3. the endpoint contract is bounded and its complete attempt family counted;
4. the result is labeled sentinel coverage, not structural promotion.

For a downstream password-oracle negative, reopen only when:

1. the candidate/material was actually present;
2. the old contract would reject the newly considered correct-output shape or
   omitted the newly justified cryptographic variant; and
3. no completed specialized oracle already tested an equivalent or stronger
   structural condition for that same material.

Together these rules turn the false-negative discovery into targeted evidence
work rather than an invitation to repeat the whole search.

## Related repository evidence

- `tools/gsmg/cb_common.py` — shared decryption and acceptance rules.
- `tools/gsmg/test_cb_common.py` — focused positive controls.
- `tools/gsmg/FINDINGS.md`, Phase 14 — historical 85%-printability false
  negative proven with the real Phase 3.2 plaintext.
- `tools/gsmg/FINDINGS.md`, Phase 78 — exact 64-byte binary-key exception.
- `tools/gsmg/FINDINGS.md`, Phases 94/100/144 — bounded no-pad key/address
  coverage.
- `tools/gsmg/FINDINGS.md`, Phase 163 — whitespace and broader padded-corpus
  gaps.
- `tools/gsmg/FINDINGS.md`, Phases 276/278/279/281/282/285 — GF(9), MTF/BWT,
  base-81, crib recurrence, arithmetic coding, and sequence-alignment gates.
- `doc/Brainstorms/2026-08-14 - DBBI FAED Post-Model Synthesis and Reopening
  Conditions.md` — current model-family reopening rules and evidence ladder.
- `tools/gsmg/p32_sibling_password_audit.py` — exact two-key P32 structural
  model.
- `tools/gsmg/nopad_window_sweep.py` — specialized no-pad key recognizers.
- `tools/gsmg/color_mask_full_stream_audit.py` — current reusable
  `passphrase_hits()` wrapper.
- `doc/GSMG_SCRIPT_CODE_REVIEW.md` — earlier shared-oracle correctness review.
