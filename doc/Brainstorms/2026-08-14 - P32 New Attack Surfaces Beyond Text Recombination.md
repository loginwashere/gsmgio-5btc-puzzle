---
type: hypothesis
status: live
date: 2026-08-14
topics:
  - brainstorm
  - p32-trailing
  - password-derivation
  - on-chain-forensics
  - steganography
  - private-keys
---

# P32 New Attack Surfaces Beyond Text Recombination

> [!caution] Incubation note
> This document proposes several independent, bounded test plans and records
> their execution status as work lands. It does not claim a lead exists.
> Each family below is labelled either a genuinely new surface or a narrower
> residual left by earlier work, based on a keyword/context sweep of
> `tools/gsmg/FINDINGS.md` (271 phases) on 2026-08-14.

> [!important] Audit correction
> The initial draft overstated family 1 as a wholly untouched surface. Phases
> 169, 170, and 192 already inventory all five known salts (the four open
> targets plus solved Phase 3.2), test salt-derived key material and
> salt-as-selector rules, and an earlier archive audit records that the open
> blobs have distinct salts and no repeated ciphertext blocks. What remains
> untested is only a small pre-registered *pairwise relationship* table. That
> residual is lower-value than the genuinely new families added below.

> [!info] Result — family 6 executed (2026-08-14)
> Re-pulled the actively-maintained `HosterjackAGV/gsmg-5btc-puzzle` fork's
> full current tree (five documents this project had never read:
> `BLOB-COMBINATION-ANALYSIS.md`, `ENDGAME-ANALYSIS.md`, `LOOSE-ENDS.md`,
> `CREATOR-INTEL.md`, `VERIFIED-SOLUTIONS.md`, plus `chess-vic-lab.js` and
> the raw `content/` sources). Full writeup: FINDINGS.md Phase 271. Two
> concrete results: **family 1 is now closed for its enumerated
> construction set**, superseded by the fork's own independent
> ~35,000-combination salt/cross-blob sweep (all
> salt orderings as direct key/EVP-passphrase/hash, salt XOR/sum, cross-
> blob ciphertext-as-key, full ciphertext-concatenation permutations,
> repeated-block scan — 0 real hits); and **the literal chess-board-
> construction reading of the Architect speech's chess sentence is
> independently dead-ended** (288 phase-3.2-derived strings, the VIC digit
> string, the Phase 2 FEN, and a 370k-word dictionary against
> `p32_trailing`, 0 hits — its only real function is the already-fully-
> consumed VIC alphabet mnemonic). Four narrowly scoped, previously
> untested leads were also surfaced from `LOOSE-ENDS.md`; see family 10.

> [!info] Result — family 11 executed (2026-08-14)
> Hexadecimal-nibble packing of FAED was a real representation gap distinct
> from whole-base-9 conversion. Two conventional maps x two orientations x
> two nibble orders produced eight exact 285-byte streams. None had a file
> signature or decompressed under zlib/gzip/bzip2/xz; 24 raw/SHA-256 password
> materials produced 0 hits across the full standard four-blob oracle. DBBI's
> odd 91-symbol length always leaves one nibble and was not silently padded.
> Full writeup: FINDINGS.md Phase 272.

> [!info] Result — family 12 executed (2026-08-14)
> Applied the exact inverse of the page's known decimal transport to DBBI and
> FAED, calibrated by byte-perfect recovery of `lastwordsbeforearchichoice`
> and `thispassword`. Four bounded orientation variants per source yielded
> 38-byte DBBI and 237-byte FAED outputs, all binary noise: zero signatures,
> decompression results, or full-standard-oracle hits from 24 password
> materials. Full writeup: FINDINGS.md Phase 273.

## Why a new document instead of extending the sibling-output one

[[2026-08-14 - P32 Trailing Sibling-Output Password Path]] closed every
source-grounded *textual recombination* of the Phase 3.2.1/3.2.2 sibling
outputs: 25 candidates, 300 structural trials, 0 hits. That document's own
reopening-conditions list is explicit that what remains there is
under-selected combinatorics (Family D, half/interleave, restored
whitespace) — expanding it further is exactly the "arbitrary permutation"
trap the document itself warns against.

This project has run 271 phases. The overwhelming majority attack the same
evidence base — the decrypted text chain, the Telegram export, the Cosmic
Duality OCR, the Stage-0/Stage-1 images pixel-by-pixel — with an
ever-more-careful selection rule over the *same* candidate alphabet. That is
the right discipline for a fixed evidence base, but it means the marginal
value of one more textual permutation is now low. Being creative here means
changing *what counts as evidence*, not proposing another combination of
what is already in the corpus.

A targeted keyword sweep of FINDINGS.md found these methodological gaps —
things genuinely absent, not merely untested combinations of present things:

| Surface | Evidence in FINDINGS.md | Verdict |
|---|---|---|
| OP_RETURN/dust messages on creator addresses | Phase 156, thorough, closed (spam campaign, not creator) | closed |
| CT-log subdomain enumeration, DNS TXT history | Phase 156 | closed |
| Wayback raw HTTP headers | Phase 156 | closed |
| Image LSB/PNG-filter/iTXt steganography | 17+ phases across the project | extensively covered |
| QR-code scan of images | 5 phases | covered |
| Alternate KDF (scrypt/bcrypt/Argon2) for P32 | 0 mentions | no source support — `Salted__` strongly indicates conventional `openssl enc`, whose relevant paths are already covered; the header does not mathematically forbid a custom KDF, but inventing one is unbounded |
| Cross-blob salts and repeated blocks | Phases 169/170/192 plus external-archive audit: salts inventoried and distinct; salt material/selectors negative; repeated blocks absent | **partially covered; pairwise-relation residual only** |
| Transaction-graph clustering beyond first-hop input-address check | partial (Phase 156 checked OP_RETURN *tx* inputs only) | **gap** |
| Raw binary asset bytes (not their visible content) as password material | 0 mentions | **gap** |
| Systematic external community P32-candidate mining, fabrication-checked | ad hoc only (debunked GitHub/bitcointalk spam, not a deliberate sweep) | **gap** |
| Numeric/temporal metadata as password material | proposed in an earlier general brainstorm, but no bounded P32 execution is recorded | **execution gap** |
| Exact blob-literal context in source code, source maps, and archived responses | provenance checks exist, but no P32-focused surrounding-symbol/context inventory is recorded | **gap** |
| Author OpenSSL/toolchain fingerprint learned from solved stages and creator-authored commands | cipher menus are broad and creator profile was discussed in Phase 253; no single cross-stage profile table is recorded | **partial methodological gap** |
| Transaction serialization/signature/wallet fingerprints | Phase 156 distinguishes inputs from recipients; no `version`/`nLockTime`/sequence/script/signature-style comparison is recorded | **gap** |
| Cross-artifact first-appearance/co-occurrence chronology | individual artifact provenance is strong; no unified blob-centric chronology is recorded | **gap** |

These gaps drive the twelve candidate/evidence families below.

## Candidate family 1 — residual cross-blob envelope relationship audit

**Status: CLOSED for the fork's enumerated ~35,000 salt constructions
(2026-08-14)** — not a claim that no conceivable salt relationship could
ever be probative, only that this specific, broad, pre-registered
construction set is now exhausted. See FINDINGS.md Phase 271. The
independent `HosterjackAGV/gsmg-5btc-puzzle` fork's
`docs/BLOB-COMBINATION-ANALYSIS.md` already ran a strictly broader version
of the pre-registered table below — all 24 salt orderings as a direct
key/EVP-passphrase (raw and hex)/SHA-256 input, 3- and 2-salt
concatenations in the same forms, salt XOR and byte-sum, cross-blob
ciphertext-as-key for every pair, full ciphertext-concatenation
permutations, and a repeated-16-byte-block scan — 0 real hits. This
retires the pre-registered table below and the local script that would
have run it; it does not retire the family as a concept, only leaves it
with no remaining actionable backlog absent a new authenticated selector
(the same reopening bar every other closed family in this project uses).

Every OpenSSL `Salted__` blob in this project (SALPH, COSMIC, P32TRAILING,
URLBLOB, plus solved Phase 3.2 as a control) carries its own 8-byte salt in
the clear, immediately after the 8-byte magic string. Earlier work already
establishes that the salts are distinct, that ciphertext blocks do not
repeat, and that direct salt-derived password/key and selector families are
negative. Do not rerun those claims.

The only residual worth a tiny audit is whether the five fixed salts have a
relationship under a *pre-declared* table:

- pairwise XOR and modular subtraction in big- and little-endian order;
- byte reversal and four-byte-half swap before the same comparison;
- equality of high or low 32-bit halves;
- equality to an *existing, frozen* eight-byte constant inventory.

ASCII/base64 storytelling, arbitrary constants, bit rotations, and searches
for attractive decimal substrings are excluded. Exact equality is already a
known negative, not a new trial. A nonzero difference or XOR is not a “hit”
merely because it can be rendered as a date or word after the fact.

This does not directly yield a password. Even an exact relation would be a
candidate structural fact, not an authenticated selector, until an authored
consumer explains why that relation matters. It could then satisfy the kind
of new-evidence condition required to reopen the sibling-output branch.

Bounded execution: extract the five salts as raw bytes and big/little-endian
integers, freeze the comparison table and constant inventory in the script,
and emit the complete matrix. A clean negative closes only these simple
pairwise relations; it cannot rule out all hand-picked-salt channels.
This local execution step is now moot given the fork's broader closure above.

## Candidate family 2 — transaction-graph trace beyond the first hop

**Priority: 2.**

Phase 156 established a real, validated discriminator: an address is only
creator-signal if it is the *signing input* of a transaction, not merely a
payment recipient (that is exactly how the 105 OP_RETURN messages were
correctly dismissed as third-party graffiti). It applied that discriminator
only to the OP_RETURN-bearing transaction set. It did not apply
common-input-ownership clustering or output-following to the two
known-genuine creator addresses' full 125+44 transaction histories.

This is a different kind of evidence than "message hidden in a
transaction" — it is "where did creator-signed transactions actually send
money, and does any output address, change pattern, or later-spent status
correlate with anything already in this project's fact ledger" (e.g., an
address that later becomes the input of a transaction with a round/special
value, timing that lines up with a phase-release date, or a common-input
cluster that reveals a previously-unknown creator-controlled address worth
checking against the existing OSINT/handle work).

Bounded execution, using the same third-party-cross-check discipline Phase
156 already validated (never trust one explorer):

1. For each of the two known creator addresses, enumerate every transaction
   where that address is a **signing input** (not a recipient).
2. For each such transaction, record all output addresses and amounts.
3. Apply the common-input-ownership heuristic (addresses co-spent as inputs
   in the same transaction are *often* controlled by the same party) to find
   candidate additional creator-controlled addresses. Mark CoinJoin,
   collaborative-spend, exchange, and consolidation patterns explicitly;
   common-input membership is evidence, not proof.
4. Check whether any newly found address, or any output, matches an
   already-known puzzle artifact (dates as amounts in sats, addresses
   appearing anywhere in the Telegram export or README).
5. Explicitly stop at "does this reveal a new authenticated fact," not
   "does this look thematically resonant" — the OP_RETURN false-alarm is
   the standing cautionary example for over-reading on-chain data.

This does not promise a P32 password. It promises either a new fact (closes
a gap) or a clean negative (documents that the two known addresses' own
graph carries no further signal), either of which is real progress this
project currently lacks.

## Candidate family 3 — raw binary asset bytes as password material

**Priority: 3.**

Extensive work exists on the *pixel content* of every image (steganography,
alpha channels, palette structure, QR scans). No phase hashes the *raw file
bytes* of a downloadable asset — the literal bytes on disk, including any
metadata, chunk structure, and encoder fingerprint — as password preimage
material. This is a structurally different signal than pixel content: two
visually identical PNGs can have different raw bytes depending on encoder,
and a raw-byte hash is trivial to authenticate (no interpretive judgment
call) unlike text selection.

Candidates, each tested in exactly three byte forms — literal file bytes,
binary SHA-256 digest, and lowercase SHA-256 hex — form a new, previously
untested password-material class:

- every locally-mirrored image asset's exact on-disk bytes;
- the favicon specifically, since it already carries the project's most
  scrutinized single-pixel signal (Phase 239's `CE`/`C9` correspondence) —
  if that pixel-level significance is real, the file's own hash is a cheap
  adjacent test;
- any non-image binary asset already downloaded for this project (fonts,
  if any were mirrored) that has not yet been through this specific
  treatment.

This family should explicitly **not** expand into re-fetching new assets
from the live site or Wayback beyond what is already locally mirrored.
Before testing, divide the files into provenance classes: authenticated
historical response bytes, Telegram-export originals, community copies, and
locally generated derivatives. Only the first two are core candidates.
Deduplicate by content hash, exclude thumbnails/OCR/rendered derivatives,
and pin the manifest so “every file” does not quietly include research
outputs created after the puzzle.

## Candidate family 4 — numeric/temporal metadata as password material

**Priority: 4.**

The existing password-material pipeline is built almost entirely around
*text* (clue answers, hashed strings). This project's own fact ledger is
full of exact numbers that have never been fed through that pipeline as
numeric/date material:

- Telegram message IDs and Unix timestamps at the specific milestone
  messages already cited by phase number in FINDINGS.md (e.g., the message
  that supplies `HASHTHETEXT`, the `[23,16,7]` message, the recovered-guide
  message) — as decimal, hex, and ISO-8601 date strings;
- Bitcoin block heights at key dates already established in the project
  (puzzle launch, each phase-release date, the halving-recipient address's
  first-seen date) — decimal and hex;
- Wayback/CDX capture times and authenticated HTTP `Last-Modified` values for
  the specific locally mirrored responses already tied to puzzle artifacts.

Local filesystem mtimes are explicitly excluded. A Wayback capture date can
authenticate an upper bound on appearance, but it does not authenticate the
local file's mtime or prove the server created the content at capture time.

Each numeric value should be tested in a small number of *declared*
serializations (decimal string, zero-padded, hex, ISO date `YYYY-MM-DD`) —
not an open-ended format sweep, to avoid the same unbounded-combinatorics
trap already flagged in the sibling-output document.

## Candidate family 5 — external community candidate mining, fabrication-checked

**Status: EXECUTED (2026-08-25).** See FINDINGS.md Phase 409 for the full
writeup. Result: 15 search queries, ~12 sources fetched (6 GitHub issues,
1 bitcointalk topic, 3 newly-discovered forks, a full `HosterjackAGV`
re-mine at 153 files), every claim considered and dispositioned against
the four mandatory checks below, zero candidates both targeted
`P32TRAILING` specifically and were independent of the documented spam/
fabrication network. Search saturated; zero reached the local oracle.
Below is the original pre-registered method, preserved for how to repeat
this if a genuinely new external source appears later.

**Priority: 9, lowest — high noise, but occasionally real signal, and cheap to bound.**

This project has already demonstrated, more than once (the debunked
GitHub-issue/bitcointalk "SOLVED" spam campaign, the OP_RETURN graffiti),
that public claims about this puzzle are mostly noise or fabrication. That
is a reason to check with skepticism, not a reason to skip the channel
entirely — a genuine outside researcher may have found or proposed a
password candidate this project's self-generated reasoning would not
produce.

Bounded execution: search specifically for candidate *passwords or
password-construction claims* aimed at the P32/trailing blob (not general
puzzle discussion, which is already covered by the Telegram/README corpus).
Apply the exact same provenance discipline already established in this
project for suspicious claims:

1. Require the claim to name a specific, reproducible candidate string or
   construction, not a vague "I think it's X"-style claim.
2. Cross-check the claimant's identity/address pattern against the
   already-documented spam-campaign addresses/handles before treating a
   claim as independent.
3. Test each surviving candidate through the existing structural oracle
   only — never treat "someone else believes this" as sufficient to skip
   the padding/decrypt check.
4. Record every claim considered and its disposition (tested-negative,
   discarded-as-spam, discarded-as-unreproducible), so this does not become
   an unbounded rolling search.

## Candidate family 6 — exact blob-literal and code-context archaeology

**Status: EXECUTED (2026-08-14), against the pinned HosterjackAGV fork
tree.** See FINDINGS.md Phase 271 for the full writeup. Result: no hidden
decrypt call, ordering, or parameter beyond what this project already
knows. `P32TRAILING`'s base64 literal appears once in `content/demos.js`
and once in `content/attempts.js`; `URLBLOB`'s appears once in
`content/demos.js`; both are narrative walkthrough-copy strings (an
`output:` message describing the discovery), not live code paths. The
salt hex constants appear only inside the same narrative strings and one
`const SALTS4 = [...]` display array ordered `cosmic · salph_inner ·
p32_trailing · urlblob` — the same ordering this project already uses, no
new information. The real payoff of this pass was two documents, not
code: `BLOB-COMBINATION-ANALYSIS.md` (closes family 1, see above) and
`ENDGAME-ANALYSIS.md` (closes the literal chess-board-construction
reading and surfaces the four leads in family 10). Below is the original
pre-registered method, preserved for how to repeat this against a
different or future source (e.g. a later fork push, or a different
community repository not yet checked this way).

**Priority: 1 (local, deterministic, and capable of yielding an authored
label or consumer rather than another guessed password).**

The project has established where the blobs were recovered, but provenance
and *use-site context* are different questions. URLBLOB, for example, exists
as both an archived URL-path payload and a literal in a `demos.js` copy. A
frozen search should ask whether any authenticated HTML, JavaScript, source
map, JSON, native Telegram attachment, or historical repository object
contains any target in one of its native representations:

- full Base64, unwrapped Base64, raw bytes, or full hex;
- the exact eight-byte salt or first/last ciphertext block;
- a split literal reconstructed by adjacent source-code tokens.

For every exact occurrence, record the containing artifact's provenance and
the nearest syntactic context: variable/property name, function call,
neighboring literals, comment, route, array position, and sibling object
fields. The purpose is not to hash arbitrary nearby words. A useful hit would
be an authored semantic label, an actual decrypt/derive call, an ordering
relationship among blobs, or a parameter passed with the ciphertext.

Bounded execution: search only the pinned historical-site manifest, its
locally preserved source maps, native Telegram media, and repository objects
predating the relevant cutoff. Deduplicate copied bundles and quoted community
posts by content/provenance lineage. Report exact occurrences and stop; do not
expand to fuzzy fragments shorter than a full salt or AES block.

## Candidate family 7 — authoring-toolchain calibration from solved stages

**Priority: 3 (mainly a ranking tool, but it can eliminate unjustified KDF
and byte-encoding branches from future work).**

Broad cipher menus answer “could this container have been produced this
way?” They do not answer “how did this author demonstrably produce solved
containers?” Build a single evidence table from the known Phase 3.2 vector,
earlier solved encrypted phases, and creator-authored command examples only:

- cipher and mode;
- legacy `EVP_BytesToKey` digest versus PBKDF2 and iteration count;
- whether passwords were literal text, hex text, or binary digest bytes;
- newline/trailing-byte behavior of the preimage and password input;
- Base64 wrapping and container serialization at the authenticated source.

Reproduce every available solved ciphertext byte-for-byte when its salt and
exact password are known. Where random salt prevents byte-for-byte recreation,
decrypt the original and reproduce its key/IV derivation exactly instead.
Then assign P32 cipher/KDF variants a provenance rank; do not delete variants
solely because the solved sample used another default.

This cannot identify an OpenSSL version from five random salts, and the one
known Phase 3.2 vector alone cannot prove every blob shares a toolchain. Its
success condition is narrower: a reproducible cross-stage author profile or a
documented inconsistency showing that the blobs were not generated alike.

## Candidate family 8 — blob-centric first-appearance and co-occurrence graph

> [!info] Result — family 8 executed (2026-08-20)
> Completed as Post-Phase-340 Seed 5. See FINDINGS.md Phase 344 and
> `tools/gsmg/blob_chronology_dependency_graph.py`. 22 nodes, 26 edges
> across exactly the three declared relations. **Zero chronology
> violations** among 11 well-dated `published-before` edges; one genuinely
> new adjacency surfaced (the creator's 2021-12-26 hint precedes the
> earliest documented SalPhaseIon capture by ~17 months), flagged as a
> scoping candidate, not itself authorized to run further work.

**Priority: 4 (evidence selection rather than direct password spraying).**

Individual artifacts have strong provenance notes, but no single timeline
currently answers which clues, blobs, assets, transactions, and source-code
versions demonstrably coexisted when each encrypted object first appeared.
That matters because a password dependency cannot point to material published
later unless there is independent evidence the creator intended a delayed
unlock.

Build one graph with a node for each of the five blobs and only authenticated
events: first known publication/capture, exact containing artifact, adjacent
clue text, relevant site revision, and creator-signed transaction window.
Edges must mean one of three declared relations: `contains`, `published-before`,
or `same-authenticated-object`. Unknown first-publication dates remain ranges,
not guessed timestamps.

A successful result is either a new same-object adjacency that selects a
consumer, or a chronology contradiction that rules out an existing candidate
source. Merely sharing a calendar date or being “close in time” is not a hit.

## Candidate family 9 — transaction serialization and wallet-style fingerprint

**Priority: 8 (bounded and objective, but indirect and potentially noisy).**

Family 2 follows value flow. A separate pass can compare the raw transaction
features of transactions genuinely signed by the two known creator addresses:

- transaction version, `nLockTime`, input sequence, script and address type;
- compressed versus uncompressed public keys, sighash flags, strict-DER and
  low-S conventions;
- input/output ordering, fee-rate band, and change-output pattern;
- exact repeated ECDSA `r` values as a cryptographic anomaly flag.

These fields can corroborate whether two public address histories were likely
produced by the same wallet/software workflow and can improve family 2's
change-address classification. They are not themselves a password generator,
and a wallet-style match is not proof of common ownership.

Bounded execution: analyze only transactions in which a known puzzle address
actually signs an input; pin raw transaction IDs and bytes; obtain the same
serialization from two independent sources or verify it locally. Report exact
feature counts and anomalies. Do not attempt private-key extraction, fund
movement, or identity attribution from a fingerprint.

## Candidate family 10 — fork-surfaced residual leads (2026-08-14)

> [!info] Result — family 10 executed (2026-08-15)
> `tools/gsmg/p32_family10_fork_leads_audit.py`, FINDINGS.md Phase 292. All
> four leads tested against all four tracked blobs, 15 candidates in the
> two declared forms, 720 effective decrypt attempts. **0/4 hits on every
> lead.** Lead 2 (Safenet/Luna/HSM digit-glued ordering) remains formally
> unexecuted as an ordering-key reading specifically — only the literal
> digit-glued substrings were testable without inventing a reordering rule
> this project does not have; leads 1, 3, and 4 are fully closed negative.

**Priority: 2 (source-grounded, cheap to test, but third-party-sourced —
apply the same fabrication/provenance discipline as family 5 before
running).**

Surfaced by family 6's execution against `docs/LOOSE-ENDS.md`, an internal
working document of the `HosterjackAGV/gsmg-5btc-puzzle` fork listing
"used vs. potential" readings for every disclosed puzzle artifact. Its
author explicitly marks each item's actual-use status, which is what makes
these four worth recording: each is a source-grounded artifact this
project already has authenticated, paired with a specific, narrow,
previously-untested *operation* on it — not a new artifact and not an
open-ended reinterpretation.

1. **The VIC alphabet's alternate reconstruction.** The recovered
   alphabet has two textually plausible reconstructions
   (`...JQZXW` vs. `...ZJQWX.`); only the canonical one has been used as
   a monoalphabetic key over `dbbi`/`faed`/`p32_trailing`. The alternate
   has not. Provenance-native (it comes directly from the same
   already-authenticated reconstruction ambiguity) and mechanically
   fixed — no open-ended variant space. Run first.
2. **Safenet/Luna/HSM digit-glued numbers as an ordering key.** The
   digits embedded in that clue's fragments are currently read as plain
   narrative digits. Read instead as a position/ordering key over the
   password parts they're glued to — the same mechanism already
   established elsewhere in this puzzle for a different clue (digits
   indexing password parts) — and not yet tried here. Test only against
   the already-defined ordered operand set (the four known password
   parts); do not invent a new operand list to order.
3. **Genesis coinbase hex, decoded rather than raw.** The Bitcoin genesis
   coinbase hex (`main.cpp` line 1616) reversed-byte decodes to the
   well-known headline "The Times 03/Jan/2009 Chancellor on brink of
   second bailout for banks." This project has hashed the *raw hex
   string* as password material; the *decoded headline text* itself has
   not. Test only the exact canonical headline text in its documented
   normalizations (raw, letters-only, uppercase) — not the adjacent
   unused numeric data (date, block height, `nBits`), which has no
   declared serialization and would reopen family 4's open-ended-format
   risk if added here.
4. **The orphan trailing "O" in "CIAO BELLA O."** Currently read as part
   of the sign-off phrase. Test it instead as a discrete token/index/
   terminator character (e.g. `O` = `0`, consistent with this puzzle's
   established zero-out vocabulary), separate from the phrase it trails.
   Bound this strictly to the token-vs-phrase question already declared
   — do not let it grow into new CIAO/BELLA/O permutations or anagram
   variants; that would repeat the Family D trap the sibling-output
   document already warned against.

Each candidate should be tested through the existing structural oracle
only, following the same normalization/hashing discipline as every other
family here (raw and SHA-256 hex, no open-ended format sweep), and its
disposition recorded in FINDINGS.md regardless of outcome.

## Candidate family 11 — hexadecimal-nibble packing of the 9-ary streams

**Status: CLOSED NEGATIVE (2026-08-14), FINDINGS.md Phase 272.**

Earlier base-conversion work treated `a`-`i` as digit text, individual numeric
bytes, a whole base-9 integer rendered as bytes/hex, ternary coordinates, or
checkerboard/base-25 codes. It had not treated each mapped value as one literal
hexadecimal nibble and paired consecutive symbols into bytes.

`tools/gsmg/nibble_packing_audit.py` fixes the complete source-grounded family:

- `a=0..i=8` and `a=1..i=9`;
- forward and reversed source order;
- first symbol as high and low nibble.

FAED yields eight exact 285-byte bodies. DBBI yields 45 bytes plus one unpaired
nibble under every variant, so no DBBI body was promoted by inventing padding.
The FAED bodies produced zero file signatures, zero exact standard-compression
decodes, and zero blob hits from 24 literal/binary-SHA/hex-SHA materials under
the complete standard oracle. Arbitrary alphabet rotations and DBBI padding
remain excluded absent a creator-selected rule.

## Candidate family 12 — exact inverse of the page's decimal transport

**Status: CLOSED NEGATIVE (2026-08-14), FINDINGS.md Phase 273.**

The known `lastwordsbeforearchichoice` and `thispassword` islands use a
specific transport: ASCII to hex, the whole hex value to one base-10 integer,
then digits `1234567890` mapped to `abcdefghio`. Earlier numeric DBBI/FAED
work did not invert this exact page-native grammar.

`tools/gsmg/decimal_transport_inverse_audit.py` first round-trips both known
instructions as positive controls. It then applies the exact inverse to DBBI
and FAED under forward/reversed source order and forward/reversed output bytes,
rejecting rather than repairing odd recovered hex. All eight variants serialize
cleanly (DBBI 38 bytes, FAED 237 bytes), but none has a recognized signature,
decompresses, or opens a tracked blob from its raw/binary-SHA/hex-SHA forms.

Both sources also lack the transport's `o=0` symbol entirely, whereas the two
known instructions contain it 3 and 7 times. Alternate mappings or chunked
decimal parses are excluded because they no longer reproduce the known page
transport that selected this family.

## Cross-family calibration gate

Every password-producing family should run through the solved Phase 3.2 blob
as an implementation control, but not as a claim that the candidate-generation
rule ought to recover its password. Every pattern-producing family should
publish its complete comparison table, not only its best-looking row. Where a
score or similarity is used, freeze a matched null/control family and multiple-
testing correction before inspecting results.

## Success criteria

Unchanged from the sibling-output document's standard: a candidate is only
promoted on reproducible P32 decryption with either coherent self-
identifying plaintext, or the exact 64-byte-plus-full-padding-block
structural oracle, or (for evidence families 1/2/6/7/8/9) a new fact meeting
normal provenance standards for this project (cross-checked across
independent sources, not asserted from one tool response). Families 1 and
6 are now closed/executed (2026-08-14); their success criteria are
retained for families 2/7/8/9 and for any future re-execution of family 6
against a different source.

## What not to do

- Do not treat a salt or transaction-graph observation as meaningful until
  the underlying artifact/transaction bytes are independently authenticated
  and the observation meets its pre-registered success rule.
- Do not re-run the already-exhausted steganography/QR/OP_RETURN/CT-log/DNS
  channels — they are closed, not merely quiet.
- Do not expand family 4's numeric serializations into an open-ended format
  sweep.
- Do not treat an external community claim as evidence without the
  fabrication check in family 5, step 2.
- Do not treat common-input clustering, change heuristics, or wallet-style
  similarity as proof of ownership or personal identity.
- Do not infer an OpenSSL version or RNG family from a handful of salts.
- Do not move, import, sweep, or otherwise use a recovered private key on a
  network during validation.

## Proposed execution order

0. ~~Family 6 (exact blob-literal context)~~ — **executed 2026-08-14**, see
   above. ~~Family 1 (residual salt relations)~~ — **closed for its
   enumerated construction set, 2026-08-14** as a direct result.
   ~~Family 11 (hexadecimal-nibble packing)~~ — **closed negative
   2026-08-14**, see FINDINGS.md Phase 272. ~~Family 12 (exact decimal-
   transport inverse)~~ — **closed negative 2026-08-14**, see FINDINGS.md
   Phase 273.
1. ~~Family 10 (fork-surfaced residual leads)~~ — **executed 2026-08-15,
   negative**, see FINDINGS.md Phase 292 above.
2. ~~Family 3 (raw authenticated asset bytes)~~ — **executed 2026-08-23,
   negative**, see FINDINGS.md Phase 381 and `doc/GSMG_BRAINSTORM_BACKLOG_
   LEDGER.md`.
3. Family 7 (authoring-toolchain calibration) — narrows future cryptographic
   assumptions using solved controls. **Core cryptographic finding complete**
   (Post-Phase-340 Seed 3's three-vector profile, 2026-08-20) **but not
   consolidated into a standalone audit** — see backlog ledger.
4. ~~Family 8 (first-appearance/co-occurrence graph)~~ — **executed
   2026-08-20 as Post-Phase-340 Seed 5**, see FINDINGS.md Phase 344 above.
5. Family 4 (numeric/temporal metadata) — reuses the existing pipeline with
   a small declared serialization set. Still genuinely unrun.
6. Family 2 (transaction-graph trace) — more expensive (external API calls,
   provenance cross-checks), higher potential value. Still genuinely unrun.
7. Family 9 (transaction serialization fingerprint) — best run from the raw
   transaction cache produced by family 2. Still genuinely unrun.
8. ~~Family 5 (external community mining)~~ — **executed 2026-08-25**, see
   FINDINGS.md Phase 409: 15 queries, ~12 sources fetched, zero survivors
   after the frozen 4-step provenance discipline.

Record candidate counts, exact byte/number sources, and negative results
for each family in FINDINGS.md as it is run, following this project's
existing phase-writeup convention.
