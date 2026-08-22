---
type: hypothesis
status: live
date: 2026-08-20
topics:
  - brainstorm
  - future-work
  - calibration
  - provenance
  - password-oracle
  - output-detection
---

# Post-Phase-340 Future Search Portfolio

> [!caution] Incubation note
> This is a portfolio of possible *future brainstorms*, not an authorization to
> run them. Nothing here is a finding, a candidate promotion, or evidence that
> a named mechanism was used. Each direction needs its own frozen contract
> before execution.

## Desired outcome

Identify the next genuinely different search paths after the four strongest
directions in [Creative Brute-Force Coverage Expansion](2026-08-20%20-%20Creative%20Brute-Force%20Coverage%20Expansion.md)
were run as bounded pilots in Phases 336--340. Prefer work that can select or
reject whole model families over work that merely multiplies decryptions.

## Portfolio audit

### What the recent negatives actually close

- Phase 336 closes the declared 15-operation, within-body two-half algebra on
  the frozen 42-candidate sentinel corpus.
- Phase 337 closes the declared 64-byte-prefix sliding-window and seven-form
  byte-order family on that corpus.
- Phase 338 closes its six embedded-key finders on that corpus. It explicitly
  leaves DER/ASN.1 private-key containers out of scope.
- Phase 340 closes its exact two-seed-form, eight-path, two-hardening BIP32
  scheme. It does not reject the authenticated numbers in other roles.
- None of these pilots closes the full 14,551-candidate corpus. Scaling a
  negative pilot is a coverage decision, not a new hypothesis.

### What should not be mistaken for a compute gap

The live P0 gaps `G-MSL-001`, `G-ESC-001`, and `G-YIN-001` lack an authored
consumer, decoder selector, or cross-stream operator. Another matrix DSL,
checkerboard, or short-program synthesis run cannot supply authorship. Those
rows should remain parked unless a new artifact supplies a selector or an
exact downstream hit makes a narrowly declared model self-validating.

### Underused assets found in the older reports

- The archived Phase-2/3 page itself records the creator-facing rules:
  `aes-256-cbc`, Base64, `sha-256(password)`, local casing/connection notation,
  seven-part order, and “dgst is the password.” The community walkthrough
  supplies the exact solved preimages and working hashes. These are different
  provenance classes: the page authenticates the instructions, while the
  walkthrough documents a reproducible solution.
- Together they expose a repeated solved-stage construction style: clue answers
  are normalized under local instructions, concatenated in declared order,
  hashed with SHA-256, rendered as lowercase hexadecimal, and that 64-character
  text is supplied as the OpenSSL passphrase. No held-out reconstruction audit
  of those rules is recorded.
- The 2026-08-14 P32 attack-surface report still lists authoring-toolchain
  calibration and a blob first-appearance/co-occurrence graph as open.
- The recent detector work repeatedly pays to decrypt the same candidate /
  variant / blob universe. There is no content-addressed retained-body corpus
  with a stable detector interface and coverage manifest.
- The current format scanner covers hex64, WIF, BIP39, decimal scalars, SEC1
  public keys, and xprv/xpub, but not several strongly validated, historically
  plausible secret containers.

## Future brainstorm seeds

### 1. Solved-boundary rule audit with leave-one-out stress tests

> [!info] Executed, tightly bounded pilot (2026-08-20)
> See FINDINGS.md Phase 341 and `tools/gsmg/solved_boundary_rule_audit.py`.
> A frozen instruction-parsing rule engine (component order, no-separator
> concatenation, per-component case/whitespace mode read from each page's
> own `aBa`/`aa`/`enf`/`not enf` annotation, literal `giveit` prefix) was
> applied independently to Phase 2, Phase 3, and Phase 3.2 using only each
> boundary's own local instructions. **All three recovered their exact
> known preimage at rank 1** from a small enumerated hedge over the few
> genuinely text-underdetermined byte choices (6 candidates each for
> Phase 3 and Phase 3.2, 1 for Phase 2) -- well inside the predeclared
> "top 10 of at most 100" gate. Shuffled-component-order controls produced
> zero accidental matches; a naive global casing/whitespace baseline
> (ignoring per-component instructions) found a working combo for each
> boundary, but a *different* combo per boundary, confirming per-boundary
> instruction reading is genuinely necessary. Also corrected this note's
> own manifest table: the page annotates the three Phase 3.2 answers as
> `"aa"` (force lowercase), not `"aaa"`, and Phase 2 carries no
> `aBa`/`enf`-style annotation at all (a single unambiguous component).
> Disposition is explicitly scoped as calibration, not puzzle progress --
> n=3 known boundaries licenses using this exact frozen rule registry on
> currently unresolved boundaries with equivalent local instructions; it
> does not license unbounded grammar expansion or claim a general author
> model.

Build a benchmark from solved GSMG boundaries only. For each AES boundary in
turn, hide its exact assembled preimage and give a frozen rule engine the
already-solved component answers plus only the local assembly instructions
available on the page. Measure whether it reconstructs the exact preimage and
how many alternatives rank ahead of it. Candidate rules can include only
behaviors demonstrated in solved stages: component order, connected/no-
separator assembly, instruction-selected casing, literal versus SHA-256-hex,
and declared prefixes such as `giveit`.

This first benchmark deliberately does **not** ask software to solve semantic
riddles such as “Jacque Fresco” or the chess position. Clue solving and byte
assembly are separate failure surfaces; combining them would make a miss
uninterpretable.

**Dataset reality check:** only three AES boundaries currently have exact
preimages and ciphertexts (Phase 2, Phase 3, Phase 3.2). Stage 1 supplies one
direct web-form password but no locally executable historical server oracle.
Four examples are not enough to learn or statistically validate a rich creator
grammar. The admissible claim is narrower: a small rule-coverage audit and
leave-one-boundary stress test can falsify proposed construction rules and
measure their branching cost. It cannot establish a general author model.

The initial frozen boundary manifest should be:

| Holdout | Solved components supplied | Local rule evidence supplied | Exact preimage bytes | Expected SHA-256-hex |
|---|---:|---|---:|---|
| Phase 2 | 1 | `/(aaa, connected enf)` and page-level `sha-256(password)` | 9 | `eb3efb51...e5bf` |
| Phase 3 | 7 | `parts 1..7`, `aBa`, connected `enf` / `not enf`, `sha-256 -> dgst` | 227 | `1a57c572...30d5` |
| Phase 3.2 | 3 | three `aa, connected enf` scopes, explicit `giveit` prefix, “sha256 pw, yet again” | 62 | `250f3772...e4c` |

“Solved components supplied” is deliberate. The benchmark may assemble
`causality`, `Safenet`, the post-move FEN, and the other already-established
answers; it may not reward itself for rediscovering them. The full expected
preimages remain in `GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md` and the walkthrough,
while the manifest can use byte count plus digest to avoid duplicating a
227-byte value in every report.

**Why distinct:** this measures whether candidate-construction rules reproduce
known puzzle behavior before they are used to spray unresolved blobs. It
sharpens F1/F3 from the previous report into a falsifiable calibration without
pretending the sample supports machine learning.

**Smallest test:** rotate the three AES boundaries as holdouts. Freeze a core
rule registry on the other two, then allow the held-out page's explicit local
instructions to parameterize that registry. Compare exact recovery rank and
candidate count against shuffled component order and a naïve Cartesian
normalization baseline. Treat the Stage-1 lyric password as an out-of-domain
direct-password control, not a fourth AES training row.

**Promotion gate:** predeclare normalization, instruction parsing, and ranking
before each holdout. If the rules cannot recover all three exact AES preimages
within a small declared rank, do not use them to generate unresolved-stage
candidates.

#### Proposed seed-1 scoring contract

Record these separately for each holdout:

1. whether the exact preimage is present at all;
2. its rank before querying the ciphertext;
3. total unique byte strings emitted;
4. which page instruction authorized every transformation;
5. the number of equally-ranked strings; and
6. the result under a control where component order is shuffled but the same
   transform budget is preserved.

Do not optimize only for rank. A grammar that emits every permutation, casing,
separator, prefix, and hash representation will contain the answer but has
learned nothing. Prefer the smallest frozen rule set that recovers all three
boundaries and report its branching factor. A reasonable first success gate is
exact recovery in the top ten with at most 100 unique byte strings per
boundary; freeze or revise that number before implementation, not after.

The most informative failures are also predeclared:

- missing Phase 3 indicates failure to respect mixed local whitespace/casing
  scopes or component order;
- missing Phase 3.2 indicates failure to apply an explicit directional prefix
  or the “yet again” hash reuse;
- recovering only Phase 2 is not meaningful because it has one component;
- success only after adding an answer-specific rule is leakage, not recovery.

### 2. Typed decode-and-parse ladder

> [!info] Executed, bounded pilot (2026-08-20)
> See FINDINGS.md Phase 342 and `tools/gsmg/typed_decode_parse_ladder_
> audit.py`. Scoped per the user's exact freeze: reused the identical
> 42-candidate, 12,128-body Phase 336-338 corpus (no new candidates/KDFs/
> ciphers); allowed strict hex, Base64/Base64URL, gzip/zlib/ZIP decoding,
> depth one; validated with a bounded DER-EC/PKCS8 parser, a PSBT map
> walker, a legacy+segwit Bitcoin-transaction parser, the existing
> key-format scanner (post-decode only, to avoid duplicating Phase 338's
> already-negative direct-body scan), and an exact-target check; three
> explicit scopes (whole-body/line/token), no substring tree; `Salted__`
> treated as a detection-only structural trigger, no decrypt attempted.
> Self-test covered a planted positive and malformed near-positive per
> decoder, a 50MB decompression-bomb rejection, minimal-valid-and-then-
> corrupted DER/PSBT/transaction fixtures, an end-to-end planted hit
> through the real AES pipeline, and 200 random length-matched controls
> (zero parser-valid findings, zero hits). Real run: 150,141 segments
> across the full corpus, a handful of decode triggers (22 hex, 16
> Base64, 225 zlib-header-pattern-but-failed-inflate, 0 gzip/ZIP), **0
> structural findings, 0 exact-target hits.** Percent-decoding and the
> nested-Salted__-decrypt step were explicitly out of this pilot's scope.

Replace A4's generic “decode then rescan” with a typed transition registry.
A transform may run only when its input validates as that type, and its output
must validate as another type:

```text
ASCII hex -> bytes -> DER/ZIP/transaction parser
Base64/Base64URL -> bytes -> Salted__/gzip/PSBT/parser
percent encoding -> bytes -> UTF-8/Base64/hex parser
Salted__ plaintext -> exactly one nested authenticated container
```

Use depth one by default. Permit depth two only when the first edge has a
checksum, exact grammar, or successful parser; “looks printable” is not an
edge.

**Why distinct:** it expands recognition while preventing an adaptive decoder
tree. It can consume retained bodies from any crypto run and has decisive
synthetic controls.

**Smallest test:** the 42-candidate retained bodies already used in Phases
336--338, with planted examples for every registered edge and random-body
false-positive calibration.

#### Proposed seed-2 typed registry

Separate *decoders* from *validators*. A decoder produces bytes; it does not
create a hit. A validator either parses the complete declared object or rejects
it.

| Input trigger | One permitted decode | Required output validation |
|---|---|---|
| whole token is even-length ASCII hex | hex to bytes | complete downstream parser or exact target |
| strict Base64/Base64URL token whose canonical re-encoding agrees | Base64 to bytes | `Salted__`, compression, DER, PSBT, transaction, or key parser |
| token contains at least one literal `%HH` escape and no malformed escape | percent decode | strict UTF-8 followed by one registered token parser |
| gzip/zlib header and bounded declared size | decompress once | checksum/trailer plus size cap, then registered parser |
| ZIP local header plus central directory | extract one bounded member | CRC and complete archive consistency |
| exact `Salted__` header and block-aligned body | one nested decrypt layer | padding plus a decisive parser; never language score alone |
| DER outer sequence with exact consumed length | DER parse | EC/PKCS#8 semantic and scalar/curve validation |

Whole-body, line, and token scope must be three explicit scopes, not an
arbitrary substring scan. Limit expansion per body and deduplicate decoded
bytes by SHA-256. Cap decompressed size and compression ratio to prevent a
planted or accidental decompression bomb. HTML entity decoding should remain
out of the first registry unless an actual retained body contains entity
syntax; otherwise it is a menu item without a trigger.

Controls should include one planted positive for every row through the real
driver, a malformed near-positive, length-matched random bytes, and the real
wrong-password retained-body population. Report trigger count, successful
decode count, parser-valid count, exact-target count, and unique output count
separately. A parser-valid object is review material; only a target relation or
authenticated puzzle context can promote it.

### 3. Solved-vector authoring-toolchain calibration

Complete the still-open 2026-08-14 family 7 before broadening E2/E3. Assemble
every authenticated solved ciphertext/password pair and clearly distinguish
creator-page instructions from community-authored decryption commands. Record
exact password bytes, whether a SHA-256 digest was passed as hex text or raw
bytes, digest/KDF, cipher, padding, newline behavior, and Base64 wrapping.
Reproduce key/IV derivation and plaintext exactly.

**Why distinct:** the puzzle itself says AES-256-CBC/Base64/SHA-256 password
repeatedly. A source-calibrated fingerprint can rank historical implementation
variants; an arbitrary CryptoJS/Node/OpenSSL menu cannot.

**Smallest test:** Phase 2, Phase 3, and Phase 3.2 solved vectors. Add a shell
command only if its creator authorship is independently established; the
repository README commands are community-authored reproducibility evidence,
not creator-toolchain evidence.

**Stop rule:** report one consistent profile or documented incompatibilities.
Do not infer a precise OpenSSL version from random salts.

#### Investigation pass — three-vector KDF profile (2026-08-20)

This cheap calibration was run while deepening the brainstorm; it queries only
known solved artifacts and does not test an unresolved candidate.

The Phase 2 and Phase 3 Base64 bodies were extracted directly from the two
`<textarea>` elements in the local Wayback mirror
`doc/html/choiceisanillusion...iwroteitmyself.html` (file SHA-256
`647744a2957219a4084ede994719124e7445bab1dfdeb68258fbeff2615a8d43`).
The Phase-3.2 body and known password came from the existing end-to-end
positive vector in `tools/gsmg/data.py`. Each known 64-character password was
passed as literal lowercase ASCII hex text. AES-256-CBC was tried under legacy
single-round `EVP_BytesToKey` with SHA-256, MD5, and SHA-1; validity required
correct PKCS#7 padding and the documented plaintext prefix.

| Vector | Salt | Container / ciphertext bytes | SHA-256 | MD5 | SHA-1 |
|---|---|---:|---|---|---|
| Phase 2 | `06286612d43ed7ed` | 672 / 656 | exact plaintext | invalid padding | invalid padding |
| Phase 3 | `9fbc451d13d071f4` | 4,112 / 4,096 | exact plaintext | invalid padding | invalid padding |
| Phase 3.2 | `eefc4c5befc1656a` | 2,448 / 2,432 | exact plaintext | invalid padding | invalid padding |

**Interim conclusion:** three successive solved AES boundaries use the same
observable stack: the SHA-256 digest rendered as lowercase hex text, then
legacy SHA-256 `EVP_BytesToKey`, AES-256-CBC, PKCS#7 padding, and OpenSSL
`Salted__` Base64 serialization. This is strong evidence for the *artifact
profile*. It still does not identify the creator's OpenSSL version, operating
system, command line, or whether encryption was invoked through OpenSSL itself
versus a compatible library.

**Consequence for future work:** E2's broad PBKDF2-count menu and unrelated
historical fingerprints should rank below literal compatibility with this
three-vector profile. They remain possible for later unresolved blobs, but
they are not the creator-calibrated default.

### 4. Content-addressed decrypt transcript and coverage ledger

> [!info] Executed, ledger half only (2026-08-20)
> See FINDINGS.md Phase 343 and `tools/gsmg/coverage_ledger.py` /
> `tools/gsmg/coverage_ledger.json`. Per the user's explicit instruction,
> only the coverage-ledger half was built; the plaintext-transcript-cache
> half remains deferred pending a separate storage/sensitive-data-boundary
> decision. One machine-readable row per Phase 336-342 experiment
> (digests/counts/structural metadata only -- self-test mechanically
> confirms no row leaks a real candidate literal or a WIF-shaped string),
> plus a 3-corpus x 5-detector coverage cube distinguishing covered cells,
> sentinel-only-awaiting-full-corpus-scale cells, deliberately-excluded
> formats, evidence-blocked models, and -- computed by set difference, not
> hand-curated -- genuinely untested cells with no declared reason.
> Automated reconciliation cross-checks the ledger against live code
> (corpus digest, retained-body count, and optionally every sibling
> script's own self-test) rather than trusting hand-transcribed numbers.
> **Result: infrastructure, not a hypothesis test.** The one substantive
> finding it surfaced: BIP32-path derivation (Phase 340) was never run
> against the 648- or 14,551-candidate core corpora, and unlike the four
> AES-body detectors this is cheap (~495,000 checks at full scale, no GPU
> needed) -- simply never scoped, not excluded, not compute-blocked.

Persist a privacy-safe, local corpus keyed by hashes of candidate manifest,
candidate bytes, variant registry, blob bytes, and code version. Store bounded
plaintext prefixes or encrypted-at-rest sensitive bodies, plus typed features
and provenance. Give downstream detectors a stable iterator so A3/A4/A5/D1
families do not reimplement or rerun decryption.

Alongside it, maintain a machine-readable coverage cube:

```text
candidate corpus x material form x KDF x cipher/mode x blob x retention rule
                 x detector x transform depth x exact target set
```

**Why distinct:** this does not solve the puzzle directly. It prevents false
claims of “full coverage,” exposes genuinely empty cells, and makes later
detectors cheap and directly comparable.

**Smallest test:** ingest Phases 336--338 and prove their recorded attempt/body
counts and manifest digest can be reconstructed without storing passphrases or
private keys in ordinary logs.

### 5. Blob chronology and dependency graph

> [!info] Executed (2026-08-20)
> See FINDINGS.md Phase 344 and
> `tools/gsmg/blob_chronology_dependency_graph.py` /
> `tools/gsmg/blob_chronology_dependency_graph.json`. 22 nodes across the
> requested six types (blob/solved_boundary/page_revision/telegram_artifact/
> repo_appearance/clue), 26 edges across exactly the three requested types
> (`contains`, `published_before`, `same_authenticated_object`), three
> separate date fields per node (`observed_at`/`probably_authored_at`/
> `first_publicly_seen`), every date or bound cited to a FINDINGS.md phase or
> `doc/GSMG_*.md` audit -- no guessed timestamp anywhere. The restored
> (2026-08) live `gsmg.io` deployment is mechanically pinned to
> `attribution="unknown"` per instruction (Phase 329 left operator identity
> unresolved), proven non-vacuous by flip-and-catch in self-test. The solved
> Phase 2->3->3.2 chain is included as the positive chronology control and
> is accepted without exact dates rather than either being ignored or
> falsely flagged. **Result:** zero chronology violations among the 11
> well-dated `published_before` edges (a checked, bounded negative on
> anachronism, not a general proof); one genuinely new adjacency surfaced --
> the creator's 2021-12-26 "zeroed out"/prime-numbers hint precedes the
> earliest documented public capture of the SalPhaseIon page (2023-05-31) by
> roughly 17 months, a gap this project had never previously stated because
> the two supporting facts lived in separate phases (FINDINGS Phase 2's
> hint writeup and Phase 244/249's capture chronology) until this graph
> joined them. Primarily a synthesis/formalization pass over already-
> documented facts; the BIP32-in-page-hint-vs-capture gap is flagged as a
> scoping candidate for a future phase, not authorized to run by this result
> alone. In the course of scoping this, corrected `coverage_ledger.py`'s
> stale `cosmic_duality_book_interior` note (it described the physical
> book's pages 57-58 as unrecovered; they were recovered and reviewed
> negative in Phase 259) -- see Phase 343's Supersedes/corrects.

Complete the older family 8 as an evidence-selection project. Give every blob,
clue, page revision, solved output, Telegram attachment, and creator-authored
command a first-seen interval and authenticated containing object. Allow only
`contains`, `published-before`, and `same-authenticated-object` edges.

**Why distinct:** a password source published after a ciphertext is impossible
unless delayed publication or later modification is evidenced. Chronology can
eliminate whole candidate families before brute force and may reveal a
same-object adjacency missed by wordlist-oriented reviews.

**Smallest test:** P32TRAILING, SALPH, COSMIC, URLBLOB, and the known Phase-3.2
plaintext, with uncertainty intervals retained rather than guessed dates.

### 6. Multi-blob concordance before aggregate language scoring

> [!info] Executed, bounded structural-only pilot (2026-08-20)
> See FINDINGS.md Phase 348 and `tools/gsmg/multi_blob_structural_
> concordance_audit.py` / `multi_blob_structural_concordance_report.json`.
> Reused the exact 42-candidate, 12,128-body Phase 336--338/342 corpus;
> added no candidate, KDF, cipher, mode, blob, retention rule, or language
> statistic. Four whole-body families were frozen before running: complete
> parser-valid type (raw or one strict decode hop), valid four-byte checksum
> family, exact first-64-byte delimiter / fixed-record geometry, and
> secp256k1-scalar-to-HASH160 relations at a small fixed offset registry.
> The statistic was the global maximum number of exact events on any same-
> candidate/same-form/same-variant blob pair. A 1,000-trial deterministic
> label-permutation null preserved blob, form, variant, body-length multiset,
> and missing-retention pattern; every trial contributed its global maximum,
> correcting across all features, offsets, candidates, and pairs. Candidate
> provenance was gated behind family-wise `p <= 0.05`. **Result: 18,144 pair
> hypotheses, real maximum 0 events; all 1,000 null maxima also 0; p=1.0;
> no candidate disclosed or inspected.** This closes only this exact
> structural-concordance registry on the sentinel corpus. It neither runs nor
> licenses D1's weak aggregate-language scoring.

Reframe D1/D2 so exact shared structure comes first. Under the identical
candidate and crypto variant, test whether two blobs independently produce the
same validated type, delimiter geometry, embedded checksum family, or
key/address relationship at predeclared offsets. Only after that calibration
should a joint weak-language statistic be considered.

**Why distinct:** two moderate English scores are easy to obtain by chance;
two independently parsed, structurally related outputs are rarer and more
auditable.

**Controls:** permute candidate labels between blobs, preserve each blob's
length/mode distribution, and correct across every feature and offset tested.

**Stop rule:** no candidate-specific inspection until the real maximum is
compared with the complete permutation/null maximum distribution.

### 7. Input-byte pathway reconstruction

> [!info] Result -- scoped subset executed (2026-08-23)
> See FINDINGS.md Phase 378 / `tools/gsmg/input_byte_pathway_reconstruction_audit.py`.
> Only the pathways with real evidence in this project were run: raw
> SHA-256 digest bytes (the COSMIC precedent), and trailing space/LF/CRLF
> bases (the Phase 163 hash-tool finding) -- 756 new materials against the
> frozen 42-candidate P0A/P1A corpus, full oracle, all 4 blobs. **0 hits.**
> The rest of this entry's concept list -- `textContent` vs. copied
> selection, HTML entity decoding, and any UTF-16/low-byte path -- has no
> puzzle-era evidence found (grepped, zero hits) and remains genuinely
> unrun, not disproven.

The oracle accepts bytes, while solvers usually see rendered text. Reconstruct
only historically plausible paths from authored page text to password bytes:
textarea `textContent` versus copied selection, HTML entity decoding, line
ending conversion, terminal newline, UTF-8 versus a demonstrated JavaScript
UTF-16/low-byte mistake, and shell `echo` versus `printf` behavior.

**Why distinct:** E1's encoding list is too easy to turn into a menu. Browser
source, archived JavaScript, creator commands, and solved vectors can select a
small subset before any unresolved blob is queried.

**Smallest test:** reproduce solved passwords through each evidenced UI/CLI
path and retain only pathways that match known ciphertexts or authenticated
instructions.

### 8. Remaining exact secret-container formats

> [!info] Executed as a strict Phase-342 delta (Phase 350, 2026-08-20)
> DER/PKCS#8, PSBT, and complete transactions were already covered by Phase
> 342, so they were not rerun or reimplemented. Phase 350 added only the five
> still-missing families: BIP38, Casascius mini keys, all 12 Bitcoin
> mainnet/testnet SLIP-132 versions, checksummed output descriptors under a
> frozen bounded grammar, and complete logical Bitcoin Core `key`, checksum-
> bearing `ckey`, and tightly structured `mkey` records. It reused Phase 342's
> exact 42-candidate/12,128-body corpus, three scopes, and depth-one decoders;
> no candidate, crypto, retention, scope, or decoder expansion was permitted.
> The real pass checked 150,141 segments and made 750,895 validator
> invocations. **Zero structurally valid containers and zero exact-target
> hits.** See FINDINGS.md Phase 350 and
> `tools/gsmg/remaining_secret_container_delta_audit.py`.

Add parsers only for formats with strong internal validation and plausible
Bitcoin-era use:

- DER/ASN.1 EC private-key and PKCS#8 structures;
- Casascius-style mini private keys, including their `?` checksum rule;
- BIP38 payloads with Base58Check and exact version/flag validation;
- Bitcoin Core wallet serialization fragments only when a complete record can
  be parsed;
- SLIP-132 extended keys (`ypub`/`zpub` families) with version and checksum;
- descriptors, PSBTs, and complete Bitcoin transactions with parser-level
  validation.

**Why distinct:** Phase 338's scanner explicitly leaves DER out, and arbitrary
binary plaintext can resemble a SEC1 public key. These formats offer much
stronger validation than curve membership or magic bytes alone.

**Guardrail:** a valid but unrelated object is a structural hit, not a puzzle
solution. Promotion still requires a prize/known-target relation or compelling
authenticated context.

### 9. Checksum-guided one-error repair

For an otherwise exact WIF, Base58Check extended key, Bech32 string, mini key,
or BIP39 phrase, test a single substitution/deletion/insertion only when the
format's checksum can decide the repair. Freeze the alphabet, edit distance,
body region, and maximum number of reported repairs.

**Why distinct:** OCR or transcription damage is plausible in copied puzzle
material, but generic typo mutation is unlimited. A checksum converts this
into a bounded error-correction problem.

**Smallest test:** authenticated source strings and retained plaintext only;
no mutations of the full password corpus. Compare repair counts against
length-matched random strings.

### 10. Ciphertext-length and output-role compatibility matrix

Use the exact ciphertext sizes and padding semantics to record which proposed
plaintext roles are even possible. For example, a CBC ciphertext length fixes
the unpadded plaintext to a 16-byte interval; that can accept or reject a
single WIF, two hex scalars, an extended key, a short instruction, or a nested
container before any candidate search.

**Why distinct:** this is an inexpensive model-pruning tool. It cannot identify
the plaintext, but it can stop incompatible stories from repeatedly entering
the candidate queue.

**Guardrail:** compression and stream modes change the inference, so every row
must name its cipher/mode/padding assumptions explicitly.

#### Investigation pass — CBC/PKCS#7 length envelope (2026-08-20)

For a block-aligned CBC ciphertext of `C` bytes with valid PKCS#7 padding, the
unpadded plaintext length is exactly in `[C-16, C-1]`. Applying only that
arithmetic gives:

| Blob | Ciphertext bytes | Permitted plaintext bytes under CBC/PKCS#7 | Immediate role implications |
|---|---:|---:|---|
| SALPH | 80 | 64--79 | admits hex64 or two raw 32-byte chunks; excludes standalone 51/52-char WIF, 58-char BIP38, 22/30-char mini key, and 111-char xprv/xpub |
| P32TRAILING | 80 | 64--79 | same envelope as SALPH |
| URLBLOB | 96 | 80--95 | excludes those standalone fixed-length text formats and a bare hex64; may admit a framed or variable-length object |
| COSMIC | 1,328 | 1,312--1,327 | document, multi-record, or large nested-container roles remain possible; single-secret format arguments are weak |

The exclusions are for a *standalone exact object*. A prefix, suffix, label,
newline, JSON wrapper, binary container, compression layer, or different
cipher mode changes the conclusion and must be declared as a different row.
DER and mnemonic phrases are variable-length and therefore cannot be rejected
from this table alone.

This explains why the two-raw-half and hex64 detectors were especially natural
for SALPH/P32TRAILING. Their negative pilots do not make the short blobs
incompatible with key material; they close only the registered corpus and
transform family. Conversely, future xprv/BIP38/mini-key proposals should not
be tested against the 80-byte ciphertexts as bare whole plaintexts—the length
model rejects that story before decryption.

### 11. New-evidence diff watch, not another static scrape

> [!info] Executed and made repeat-safe (Phases 347 and 349, 2026-08-20)
> Phase 347 established the three-URL passive baseline. Phase 349 repaired
> two repeat-run defects before enabling a low-frequency heartbeat: previous
> live hashes were read from the wrong JSON level, and the bare-root Wayback
> result was neither compared nor eligible to alert. The schema now keeps
> last-known-good live/archive state across transport failures, compares root
> captures by stable identity, advances an accepted Hosterjack HEAD without
> repeat alerts, writes atomically only under manual `--run`, and exposes a
> read-only `--check` for automation. The documented 140-entry root Wayback
> reference is now actually persisted (Phase 347's committed JSON contained a
> 503/empty result despite its prose). A live repaired run found both gsmg.io
> pages unchanged and Hosterjack HEAD unchanged; GitHub's dynamic rendered-HTML
> drift is retained as informational rather than puzzle evidence. A monthly
> read-only heartbeat now runs on the first day of the month and cannot update,
> commit, or push repository state.

The restored `gsmg.io` and the Hosterjack compendium are now known surfaces.
A future provenance brainstorm should define content hashes and a low-frequency
diff protocol for creator attribution, changed assets, new source maps, or new
clue text. Only changed bytes should trigger human review.

**Why distinct:** the parked P0 gaps genuinely require external evidence. A
bounded change detector is more rational than repeatedly searching unchanged
archives or treating a third-party reconstruction as creator-authored.

**Safety:** passive GETs only, strict rate limiting, no forms, wallet actions,
scripts, downloads that execute, or attempts to contact/identify an operator.

## Connections and challenges

### Productive combinations

- Seed 1 should generate a small, calibrated candidate corpus; seed 3 should
  select its byte/KDF pathway; seed 2 should inspect the resulting bodies.
- Seed 4 makes seeds 2, 6, 8, and 9 cheap to iterate without widening crypto
  scope each time.
- Seed 5 can remove anachronistic inputs from seed 1 before candidate creation.
- Seed 10 should annotate every proposed output role in seeds 2 and 8.
- Seed 11 is the only item here that could directly reopen the evidence-blocked
  P0 gaps without a downstream cryptographic hit.

### Combinations to avoid

- Do not run a new candidate grammar, new KDF menu, nested decoder tree, and
  joint score in one phase. A negative would be uninterpretable and a positive
  would have an undisclosed multiple-testing burden.
- Do not mix checksum repair with generic password mutation.
- Do not treat the transcript cache or coverage ledger as evidence; they are
  reproducibility infrastructure.
- Do not promote a parser-valid wallet object solely because it is rare.
- Do not send the parked DBBI/FAED streams through every new detector unless a
  declared serialization produces bytes that the detector is designed for.

## Ranked next brainstorms

| Rank | Future brainstorm | Status after this pass | Value | Effort | Reason |
|---:|---|---|---|---|---|
| 1 | Solved-boundary rule audit + leave-one-out stress test | executed, Phase 341, positive/calibration-only | high | medium | Tests candidate-construction rules against authenticated instructions and working vectors before another spray |
| 2 | Typed decode-and-parse ladder | executed, Phase 342, negative | high | medium | Closes a concrete output-recognition gap with parser/checksum endpoints |
| 3 | Solved-vector authoring-toolchain calibration | core three-vector profile complete; provenance formalization remains | high | low | Selects the legacy-SHA256/AES256 compatibility baseline using primary puzzle artifacts |
| 4 | Coverage ledger + decrypt transcript | executed, ledger half only, Phase 343 | high enabling value | medium-high | Prevents duplicated crypto work and makes untested cells explicit |
| 5 | Blob chronology/dependency graph | executed, Phase 344 | medium-high | medium | Can rule out anachronistic candidate sources without decryption |
| 6 | Multi-blob structural concordance | executed, Phase 348, negative | medium | medium | Exact structural precursor completed; no shared event, so D1 remains unlicensed |
| 7 | Input-byte pathway reconstruction | concept only | medium | medium | Turns a broad encoding menu into evidence-selected variants |
| 8 | Remaining exact secret containers | executed as Phase-342 delta, Phase 350, negative | medium | medium | Five residual parser/checksum families closed on the sentinel corpus; DER/PSBT/transactions were not duplicated |
| 9 | Ciphertext-length compatibility matrix | first CBC envelope completed | medium enabling value | low | Cheaply prunes impossible output-role stories |
| 10 | Checksum-guided one-error repair | gated on a near-valid object | low-medium | medium | Bounded damage recovery, but only after a near-valid object exists |
| 11 | New-evidence diff watch | executed, Phases 347/349; monthly read-only heartbeat active | variable | low recurring | Repeat-safe last-known-good monitor is active; only changed evidence triggers review |

## Recommended sequencing

The next standalone brainstorm should be **seed 1**, because it asks whether
the project's candidate-generation habits can recover known GSMG preimages
from their explicit local rules. That result determines whether building more
candidates from the same grammar is justified at all.

Seed 3's central cryptographic question is now answered inside this incubation
note: all three solved vectors select the same observable legacy-SHA256/AES256
profile. A later formal audit can consolidate provenance, but no new broad KDF
run is justified by that result. The next downstream experiment to scope is
therefore **seed 2**. Build seed 4 only once the exact storage and sensitive-
data boundary is agreed; it is useful infrastructure but should not delay the
small rule audit or typed-parser design.

D1-style aggregate scoring should not be next. It has a weaker endpoint and a
larger multiple-testing burden than the three calibration/typed-parser paths
above.

## Experiments and next actions

> [!info] Status reconciled (2026-08-23)
> The checkboxes below were left unchecked when written; three of five are
> now done. See `doc/GSMG_BRAINSTORM_BACKLOG_LEDGER.md` for the full
> cross-brainstorm reconciliation.

- [x] Draft the solved-boundary/leave-one-out dataset: solved boundary, available clue
      components, exact expected preimage, exact expected password bytes.
      **Done — Phase 341.**
- [ ] Inventory authenticated solved ciphertext/password vectors and commands
      for toolchain calibration; record missing provenance rather than filling
      it by assumption. **Core cryptographic finding done** (the seed-3
      investigation pass above: all three solved vectors share one legacy
      SHA-256/AES-256-CBC profile) **but not yet consolidated into a
      standalone, complete provenance audit** — genuinely unrun as a
      dedicated artifact.
- [x] Freeze a typed decoder/parser registry and false-positive controls before
      applying it to any real retained body. **Done — Phase 342.**
- [ ] Decide whether a reusable transcript may store raw bodies; if not, define
      encrypted storage or feature-only records before implementation.
      **Still deferred — Phase 343 built only the coverage-ledger half; the
      raw-body transcript half needs a sensitive-data policy decision first.**
- [x] Keep every seed as its own phase. No execution is scheduled by this note.
      **Followed throughout (Phases 341-350).**

## Promotion

This document remains in `Brainstorms/`. A seed graduates only after it has a
frozen input manifest, controls, attempt or hypothesis count, success rule,
failure rule, and stop rule. Executed work belongs in a new FINDINGS phase; a
brainstorm link alone does not promote it to `GSMG_HOME.md` or the Fact Ledger.

## Related notes

- [Creative Brute-Force Coverage Expansion](2026-08-20%20-%20Creative%20Brute-Force%20Coverage%20Expansion.md)
- [P32 New Attack Surfaces Beyond Text Recombination](2026-08-14%20-%20P32%20New%20Attack%20Surfaces%20Beyond%20Text%20Recombination.md)
- [Oracle Pipeline False-Negative Surfaces](2026-08-15%20-%20Passphrase%20Oracle%20False-Negative%20Surface.md)
- [Canonical Sentinel Inventory](2026-08-15%20-%20Canonical%20Sentinel%20Inventory%20%28P0A%29.md)
- [GSMG Open-Gap Registry](../GSMG_OPEN_GAP_REGISTRY.md)
