---
type: hypothesis
status: live
date: 2026-08-20
topics:
  - brainstorm
  - brute-force
  - password-oracle
  - false-negatives
  - key-detection
  - gpu-oracle
  - dbbi
  - faed
---

# Creative Brute-Force Coverage Expansion

> [!caution] Incubation note
> This session only gathers ideas. Nothing below has been executed, promoted
> to a finding, or accepted as puzzle evidence. A proposed check must receive
> frozen inputs, controls, attempt counts, success criteria, and a stop rule
> before it can graduate to a FINDINGS phase.

## Desired outcome

Identify bounded brute-force checks that could reduce false-negative risk or
test a genuinely different puzzle model, without falling back to unlimited
password spraying or renaming families already exhausted in Phases 271--333.

The central observation is that the strongest opportunities may lie in
**recognizing more kinds of correct output**, not merely generating more
candidate passwords.

## Current understanding

### Known coverage

- The GPU oracle currently covers four standard password KDF configurations,
  AES-128/192/256, and CBC/ECB/CFB/OFB/CTR over all four tracked blobs.
- SEED-CBC is available as an explicit opt-in family.
- CBC/ECB and stream-mode plaintexts receive unconditional checks of the first
  two aligned 32-byte raw-key chunks against the address Bloom/API oracle.
- Phase 331 added exact targets for the prize pubkey's `P+G`, `P-G`, `P/2`,
  and `2P` points in both compressed and uncompressed address forms.
- Phase 327's key-shape classifier recognizes hex64, WIF, and checksum-valid
  BIP39; Phase 333 checked the 43 highest-suspicion weak bodies and found none.
- The CPU oracle covers additional 3DES, Blowfish, Camellia, AES Key Wrap, and
  material-normalization families, but these are not all available on the
  large-corpus GPU path.
- Broad DBBI/FAED transform and coupling families are negative or null-like.
  `G-MSL-001`, `G-ESC-001`, and `G-YIN-001` remain parameter-binding gaps,
  not ordinary compute shortages.

### Constraints

- No private-key-space brute force. Search only clue-derived candidates,
  decrypted material, or tightly bounded transformations.
- Every added detector must have synthetic positive and negative tests.
- Every adaptive family must be calibrated against shuffled/null controls.
- A hit from a weak statistical or language score is a review candidate, not
  proof. Prefer address, checksum, authenticated container, or exact-format
  endpoints.
- New KDF/cipher parameters should be historically plausible or clue-bound;
  arbitrary numeric ranges are out of scope.

## Gaps in scope

- `G-MSL-001`: the 31-character DBBI selection lacks a selected matrix
  consumer.
- `G-ESC-001`: no source selects FAED's `{g,i}` versus `{h,e}` decoding path.
- `G-YIN-001`: no operator is selected between DBBI and FAED.
- Oracle coverage gap: a correct decryption may contain useful key material at
  an unaligned offset, inside another encoding/container, or as a combination
  of two halves while failing current acceptance gates.

Registry: [GSMG_OPEN_GAP_REGISTRY](../GSMG_OPEN_GAP_REGISTRY.md).

## Ideas

### A. Improve decisive-output detection

#### A1. Sliding raw-key windows

> [!info] Executed, bounded pilot (2026-08-20)
> See FINDINGS.md Phase 337 and `tools/gsmg/sliding_key_window_audit.py`.
> A2's full byte-order family run at every offset within the first 64
> bytes (33 windows) of every retained body, against the same 42
> P0A/Phase-335 sentinel candidates and 54-variant x 4-blob scope Phase
> 336 used. Self-test recovers a planted key at an unaligned offset (17)
> that no prior detector in this project could see. **2,801,568 checks, 0
> hits.** Bounded pilot only (same 42-candidate corpus, not the full
> 14,551-candidate core corpus) -- real scale needs GPU batching, per this
> idea's own "Risk" note below.

Test every 32-byte window within a bounded plaintext prefix rather than only
`chunks_exact(32)` at aligned offsets. A first version could freeze the first
64 or 96 plaintext bytes and therefore add only 33 or 65 windows per decrypt.

For each valid scalar, check compressed and uncompressed P2PKH addresses using
the existing Bloom/API and exact-target pipeline.

**Why distinct:** a correct raw key beginning at byte offset 1--31 is
currently invisible to an aligned-chunk detector.

**Risk:** large multiplication of secp256k1 work. GPU batching and a strict
prefix bound would be necessary.

#### A2. Byte-order and packing transforms

For each detected 32-byte window, try a small frozen serialization family:

- full-byte reversal;
- reversal within 4-byte and 8-byte words;
- reversal of word order;
- nibble swap within each byte;
- bit reversal within each byte.

These cover common endian/packing mistakes without opening arbitrary byte
permutations.

#### A3. Unconditional embedded key-format scanner

> [!info] Executed, bounded pilot (2026-08-20)
> See FINDINGS.md Phase 338 and `tools/gsmg/embedded_key_format_scanner_audit.py`.
> Hex64/WIF/BIP39 (reused from `key_shape_classifier.py` unchanged) plus
> decimal-scalar, SEC1 pubkey, and xprv/xpub finders, against the same
> 42-candidate/54-variant/4-blob scope Phase 336/337 used. Caught its own
> false-positive-rate bug before recording anything: an early SEC1-pubkey
> finder (curve-membership only, no checksum) produced 17,182 "matches"
> that were confirmed chance noise once address-checked; fixed to require
> a Bloom/known-target address match, same discipline as every other
> detector in this line. **0 real matches** across all 6 finder types.
> DER/ASN.1 EC-key-structure parsing (mentioned above) was not built --
> scoped out for this pilot, noted as a real gap in the phase's reopen
> condition. Bounded pilot only, same 42-candidate corpus, not the full
> core corpus.

Scan arbitrary decrypted bodies, including statistically rejected bodies, for:

- 64 ASCII hexadecimal characters;
- WIF strings with checksum and scalar-range validation;
- checksum-valid BIP39 phrases;
- decimal private scalars;
- `xprv`/`xpub` extended-key payloads with Base58Check validation;
- SEC1 compressed/uncompressed public keys and DER/ASN.1 EC-key structures.

This is the natural completion of Phase 327's open CUDA/full-corpus scope.
Only checksum/curve-valid matches should count as structural hits.

#### A4. Post-decryption decoding cascade

Apply a depth-one, predeclared decoder set to padding-valid or otherwise
retained plaintext:

- Base64 and Base64URL;
- hexadecimal;
- URL/HTML entity decoding;
- gzip, zlib, ZIP, and raw DEFLATE;
- whole-body reversal;
- one additional OpenSSL/CryptoJS `Salted__` container layer.

Run the decisive key/format detectors again after exactly one successful
decode. Depth must remain one to prevent an unlimited transform tree.

#### A5. File/container magic recognition

Recognize authenticated or strongly structured binary output even when it is
not text: PNG/JPEG/GIF, ZIP, gzip, SQLite, DER, JSON, MessagePack, protobuf-like
length structure, QR-sized bitmaps, and Bitcoin transaction/PSBT magic.
Magic alone is weak; parsing or checksum validation should be required for
promotion.

### B. Take “half and better half” literally

#### B1. Two-half algebra within one plaintext

> [!info] Executed, bounded pilot (2026-08-20)
> See FINDINGS.md Phase 336 and `tools/gsmg/half_better_half_algebra_audit.py`.
> All 15 named operations below, run against the 42 P0A/Phase-335 sentinel
> candidates (2 forms each) across CBC+ECB+CFB/OFB/CTR (54 variants) x all 4
> blobs, checked against the live production Bloom cache and Phase 331's 8
> known EC-derived targets. Self-test proves the pipeline end-to-end
> (planted-hit recovery + wrong-password control), not just the combine
> math in isolation. **181,920 combine checks, 0 hits.** This is a bounded
> pilot (the 42-candidate sentinel set), not the full 14,551-candidate core
> corpus -- that scale (~150M+ secp256k1 derivations) needs a GPU port, per
> this idea's own "Open questions" note below.

For two 32-byte blocks `A` and `B`, test a frozen family:

- `A XOR B`;
- `A + B mod n`, `A - B mod n`, and `B - A mod n`;
- alternating-byte interleave/deinterleave;
- `A[:16] || B[16:]` and `B[:16] || A[16:]`;
- high-nibble/low-nibble interleave;
- `SHA256(A || B)`, `SHA256(B || A)`, and `SHA256(A XOR B)`;
- `HMAC-SHA256(key=A, data=B)` and the reverse.

Check every valid resulting scalar against the prize address and the exact EC
target set. This is more clue-bound than generic key mutation and addresses a
real blind spot: the current oracle checks the two chunks independently.

#### B2. Cross-blob body combinations

When one password/KDF/mode decrypts two blobs, combine corresponding 32-byte
blocks by XOR and modular add/subtract. Freeze same-offset combinations only,
and require the identical candidate and crypto configuration on both blobs.

**Risk:** distinct salts do not prove shared passwords or paired plaintexts.
This should remain lower priority than within-body combinations.

#### B3. Split-secret formats

Check whether multiple valid-looking bodies encode Shamir shares, XOR shares,
or two halves of a 64-byte seed. Only standard share formats or an
authenticated clue-selected split count should be accepted; do not search
arbitrary reconstruction polynomials.

### C. Wallet and elliptic-curve derivations

#### C1. BIP32 paths from authenticated numbers

> [!info] Executed, tightly bounded pilot (2026-08-20)
> See FINDINGS.md Phase 340 and `tools/gsmg/bip32_authenticated_number_
> paths_audit.py`. Ran only the first 5 sources below (not "seven-part-
> password indices" -- explicitly dropped from this pilot's frozen scope
> by the user); `574061` contributed 3 declared readings (single index,
> the established `[[5,7,4],[0,6,1]]` grouping as one 6-level path, and
> as two independent 3-level halves) for 8 total paths x 2 seed forms x 2
> hardening modes, final child + master control only, checked against the
> prize address and Phase 331's 8 known targets exactly (no Bloom, no
> scoring). Self-test verified against the official BIP32 Test Vector 1
> fetched from the BIP repository. **1,428 address checks, 0 hits.**
> Disposition explicitly scoped: negative on this exact wallet-derivation
> scheme, not on the underlying numbers. Per the user's instruction, D1
> and A4 were deliberately not started automatically after this result.

Treat a recovered phrase/body as a BIP32 seed and test a frozen registry of
paths built from already-authenticated values:

- `23/16/7`;
- `401/400/73`;
- `1/4/21`;
- `14/8/1`;
- `574061` as one index or grouped digits;
- seven-part-password indices.

Test hardened and non-hardened variants, but predeclare the exact path grammar
and total count. Check derived compressed/uncompressed P2PKH keys against the
prize target.

#### C2. Clue-bound scalar algebra

For a recovered scalar `x`, test `n-x`, `x^-1 mod n`, `x+c`, `x-c`, `x*c`,
and `x/c`, where `c` comes only from the authenticated numeric registry above.
This generalizes the neighbor/half/double idea without searching an arbitrary
radius around a key.

#### C3. EC-coordinate recognition

Interpret 32/33/64/65-byte bodies as x-coordinates or SEC1 points. Validate
them on secp256k1 and check whether a simple, predeclared point operation lands
on the prize pubkey or one of the exact Phase-331 points.

### D. Score candidates jointly instead of per blob

#### D1. Multi-blob aggregate weak scoring

For an identical candidate and crypto configuration, retain the vector of
per-blob language/structure scores and test whether two or more moderately
plausible outputs jointly exceed a null-calibrated threshold. This could catch
a shared password whose separate outputs each fall below the current cutoff.

Controls must preserve blob lengths, modes, and the total candidate family.
Distinct salts/containers do not justify assuming the password is shared.

#### D2. Cross-output structural consistency

Look for the same validated encoding, record width, delimiter placement, or
key-format offset across multiple blobs under one candidate. Require a fixed
feature registry and compare against wrong-password controls.

### E. Bounded KDF and cipher expansion

#### E1. Historically plausible password-byte encodings

Add UTF-16LE, UTF-16BE, NUL-terminated bytes, Unicode NFC/NFKC, URL encoding,
HTML entity forms, and component-local CR/LF/CRLF variants. Freeze these as
material treatments rather than multiplying the source wordlist itself.

#### E2. Clue-derived PBKDF2 parameters

Test PBKDF2-HMAC-SHA1/SHA256/SHA512 with iteration counts drawn only from the
authenticated number registry (`73`, `400`, `401`, `23167`, `574061`, etc.).
Also retain OpenSSL's standard/default counts as controls. Do not scan an
unbounded numeric interval.

#### E3. Historical implementation fingerprints

Reproduce a short registry of exact, period-appropriate implementations:

- OpenSSL `enc` digest-default changes (MD5/SHA256);
- CryptoJS OpenSSL-compatible password AES;
- Node.js legacy `createCipher` behavior;
- direct `SHA256(password)` key with zero/fixed/derived IV;
- salt-as-IV and key/IV truncation mistakes seen in simple web code.

Each model must be a byte-exact implementation fingerprint, not an arbitrary
mix-and-match KDF menu.

#### E4. Large-corpus cipher parity

Port or batch the remaining CPU-oracle families—3DES, Blowfish, Camellia, and
AES Key Wrap—only for candidate corpora already worth revisiting. This closes
a compute-parity gap but adds less conceptual value than better output
detection.

#### E5. Padding and damaged-tail variants

Consider zero padding, ANSI X9.23, ISO/IEC 7816-4, and plaintext recovery when
only the final block/padding is corrupted. Any such run must preserve raw
decrypted bytes and rely on decisive embedded-key/container validation rather
than relaxed printability alone.

### F. Candidate construction without unlimited spraying

#### F1. Solved-stage password grammar

Infer a small grammar from already-solved GSMG passwords: ordered clue-answer
concatenation, exact casing, raw and SHA-hex forms, whole-string reversal, and
line-ending boundaries. Generate new candidates only by applying those known
construction rules to authenticated unresolved tokens.

#### F2. Component-boundary variants

For a fixed token sequence, vary only boundary separators (`""`, space,
newline, CRLF, `_`, `-`, `/`, `:`), casing by whole component, and optional
terminal newline. Avoid arbitrary character mutation.

#### F3. Creator-language phrase grammar

Generate phrases from actual creator-authored sentence adjacency or dependency
structure, rather than bags of keywords. Hold out known solved phrases to
measure whether the grammar recovers authentic construction patterns better
than shuffled creator text.

#### F4. Page-order partial orders

Replace all-permutation searches with topological orders constrained by page
position, binary-decoded instruction order, first/last polarity, and explicit
yin/yang pairings. This may reduce noise while preserving plausible order
ambiguity.

### G. Structural synthesis over DBBI/FAED

#### G1. Frozen matrix-operation DSL

For the 31-character DBBI selection, enumerate a deliberately tiny language:

```text
shape -> traversal -> value map -> aggregate -> serialization
```

- shapes: exact divisors and at most one declared padded near-square;
- traversals: row, column, spiral, boustrophedon;
- maps: 0--8, 1--9, A1Z26 where defined;
- aggregates: row/column sums, differences, main diagonals;
- outputs: decimal, bytes, A1Z26 letters, hexadecimal.

Only promote exact downstream hits, and run the entire DSL against shuffled
controls. This is compute coverage, not a substitute for the seven missing
`G-MSL-001` bindings.

#### G2. Short DBBI/FAED program synthesis

Enumerate programs of at most three operations from a frozen grammar such as
tokenize, reverse, rotate by authenticated constant, mirror9, align, add/sub
mod 9, prime-position select, reshape by true factors, and serialize. Rank
English/key-format/address results against identical shuffled-stream searches.

This could unify scattered one-off transforms, but has high overlap with the
~50 negative families already cataloged; a coverage-deduplication pass is a
prerequisite.

#### G3. Checkerboard crib constraints

Use constraint solving or simulated annealing to test whether a declared crib
(`yinyang`, `thispassword`, `matrixsumlist`, `salvation`, `privatekey`,
`youwon`, `half`, `rabbit`) can appear under a registered checkerboard model.
Require the real-stream optimum to beat random cribs and shuffled streams
after correction across all crib positions and alphabets.

### H. Additional experimental detectors

- Search retained outputs for valid Bitcoin transactions, PSBTs, descriptors,
  scripts, and Base58Check/Bech32 strings.
- Test whether a 32-byte body is a valid private scalar only after one-byte
  insertion/deletion or a tightly bounded OCR substitution, when the body is
  otherwise strongly key-shaped.
- Use a compact language model only as a review ranker; require classical
  n-gram, checksum, parser, or exact-address confirmation before promotion.
- Test repeated structure at the same offset across blobs, with permutation
  controls.
- Extend the exact target registry only with independently verified,
  clue-derived addresses or EC points; do not indiscriminately add nearby
  keys.

## Connections and challenges

### Combinations

- A1 sliding windows should feed A2 byte transforms and A3 format validation.
- B1 half combiners should feed the existing address oracle and C1 BIP32 path
  derivation, but not both adaptively in one first experiment.
- A4 decoding should feed A3 parsers/checksums, not a language-only threshold.
- D1 joint scoring becomes safer when paired with A3/A5 exact structural
  validators.
- E1/E3 describe candidate-byte/KDF coverage; they should reuse the same
  downstream detectors rather than invent new hit criteria.

### Contradictions and overlap

- G1/G2 cannot resolve missing authorship or operator selection; at best they
  surface a candidate with a decisive downstream hit.
- G2 overlaps many Phases 271--321 and must begin with a machine-readable
  coverage comparison.
- B2 assumes a relationship between blobs that distinct salts do not prove.
- C2 can become disguised private-key-neighborhood brute force unless the
  constant registry and operations are frozen very narrowly.
- E4 may consume substantial engineering time while adding only algorithmic
  parity with the already-available CPU oracle.

## Promising directions

Ranked by expected impact, evidence discipline, effort, and reversibility:

| Rank | Direction | Impact | Effort | Why first/later |
|---:|---|---|---|---|
| 1 | A1 sliding key windows + A2 byte-order transforms | high | medium | Closes a concrete detector blind spot with exact-address endpoints |
| 2 | B1 within-body half/better-half combinations | high | medium | Strong clue connection; current chunks are checked independently |
| 3 | A3 unconditional embedded key-format scanner | high | high | Completes Phase 327's full-corpus false-negative scope |
| 4 | C1 authenticated-number BIP32 paths | medium-high | medium | Bounded and exact-address checked, but wallet semantics are not authored |
| 5 | D1 multi-blob aggregate scoring | medium | medium | Could rescue sub-threshold shared-password outputs; requires careful null calibration |
| 6 | A4 depth-one post-decryption decoding | medium | medium | Common container pattern with a controllable transform tree |
| 7 | E2/E3 clue-bound KDF and implementation fingerprints | medium | medium-high | Historically plausible; weaker clue binding than detector improvements |
| 8 | G1 frozen matrix DSL | low-medium | medium | Could surface an exact hit but does not repair missing operation evidence |
| 9 | G2 DBBI/FAED program synthesis | low | high | Broadest overlap and highest multiple-testing risk |

## Decisions

- This note records ideas only; no experiment is authorized by its creation.
- Better exact-output detection currently outranks larger password dictionaries.
- The two disposable weak-hit review dumps remain review material, not inputs
  or findings merely because they exist locally.
- Any future implementation should split the ranked directions into separate
  phases so a success or failure has a precise coverage contract.

## Experiments and next actions

- [ ] None scheduled. Select one ranked direction in a later session.
- [ ] Before promotion, inventory exact overlap with Phases 271--333.
- [ ] Write a pre-registration specifying frozen inputs, attempt count,
      synthetic positive controls, null controls, hit rule, and stop rule.
- [ ] Only then create a FINDINGS phase using the standard template.

## Open questions

- Does the merged GPU kernel expose enough raw plaintext to test sliding
  windows without a large host round-trip?
- Can an ASCII key-format detector be made cheap enough to run before
  printability gating?
- Which one interpretation of “half and better half” is sufficiently literal
  to deserve the first bounded test?
- Should BIP32 paths consume numeric clues as one path or several independent
  paths? This must be frozen without outcome-driven selection.
- Which existing corpora are valuable enough to justify full CPU/GPU cipher
  parity?

## Promotion

This note stays in `Brainstorms/` until one idea receives a concrete,
reproducible experiment with frozen controls and success/failure criteria.
Promotion creates a new phase in `tools/gsmg/FINDINGS.md`; this note itself
must not be added to the Fact Ledger or canonical HOME list.

## Related notes

- [Oracle Pipeline False-Negative Surfaces](2026-08-15%20-%20Passphrase%20Oracle%20False-Negative%20Surface.md)
- [Canonical Sentinel Inventory](2026-08-15%20-%20Canonical%20Sentinel%20Inventory%20%28P0A%29.md)
- [Fresh DBBI FAED Decryption Models](2026-08-14%20-%20Fresh%20DBBI%20FAED%20Decryption%20Models.md)
- [DBBI FAED Post-Model Synthesis and Reopening Conditions](2026-08-14%20-%20DBBI%20FAED%20Post-Model%20Synthesis%20and%20Reopening%20Conditions.md)
- [GSMG GPU Oracle](../GSMG_GPU_ORACLE.md)
- [GSMG Open Gap Registry](../GSMG_OPEN_GAP_REGISTRY.md)
