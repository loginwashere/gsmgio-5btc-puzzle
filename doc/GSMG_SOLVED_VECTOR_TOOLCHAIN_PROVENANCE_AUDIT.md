---
type: audit
status: closed
date: 2026-08-25
topics:
  - provenance
  - aes
  - kdf
  - oracle-guidance
  - p32-family-7
  - post-phase-340-seed-3
---

# Solved-Vector Authoring-Toolchain Provenance Audit

**Phase:** [410](../tools/gsmg/FINDINGS.md#phase-410----p32-family-7--post-phase-340-seed-3-solved-vector-authoring-toolchain-provenance-audit-one-consistent-three-vector-profile-2026-08-25)
**Script:** `tools/gsmg/phase410_solved_vector_toolchain_provenance_audit.py`
**Manifest:** `tools/gsmg/solved_vector_manifest.json`

This is the standalone deliverable that closes P32 Family 7
(`doc/Brainstorms/2026-08-14 - P32 New Attack Surfaces Beyond Text
Recombination.md`) and its duplicate, Post-Phase-340 Seed 3
(`doc/Brainstorms/2026-08-20 - Post-Phase-340 Future Search
Portfolio.md`). Both items reached the same conclusion in a 2026-08-20
in-document investigation pass but were never consolidated into a
dedicated, machine-verified artifact. It generates no new password
candidate. Its purpose is to establish, with full provenance and a
mechanical control matrix, exactly which cryptographic construction this
puzzle's creator has *demonstrably* used across all three of its solved
AES-256-CBC boundaries -- and to rank future oracle KDF priority
accordingly, without deleting any lower-ranked variant already in the
oracle's own code.

## Scope and stopping rule

Three vectors only: Phase 2, Phase 3, Phase 3.2 -- every AES-256-CBC
boundary in this puzzle chain that has an authenticated, known-plaintext
solution. No unresolved blob (SALPH, COSMIC, P32TRAILING, URLBLOB) is
touched here; this is calibration, not a search. No PBKDF2 iteration
sweep was run: a successful exact `EVP_BytesToKey` reproduction already
establishes compatibility with that construction, and the *absence* of a
PBKDF2 hit could never prove every iteration count/digest/salt-length
combination impossible, so that sweep would not have changed the
conclusion and was explicitly out of scope. The stopping rule is to
report either one consistent three-vector profile, or an explicit
incompatibility -- not to infer an OpenSSL version, operating system,
command line, or creator tooling beyond what the authenticated artifacts
themselves demonstrate.

## Inputs and their provenance tier

| Vector | Ciphertext source | Provenance tier |
|---|---|---|
| Phase 2 | `<textarea>` #1, `doc/html/choiceisanillusion...html` | **Creator-authored, directly authenticated.** File SHA-256 `647744a2957219a4084ede994719124e7445bab1dfdeb68258fbeff2615a8d43`, confirmed byte-for-byte against the pinned copy before extraction. |
| Phase 3 | `<textarea>` #2, same artifact | **Creator-authored, directly authenticated.** Same file; this artifact also contains, verbatim, the Phase-3 password-derivation *structure* ("parts 1..7 -> sha-256 -> dgst is the password") and part 7's pre-move chess FEN/riddle text. |
| Phase 3.2 | `data.PHASE32_BLOB_B64` (pinned project data) | **One tier lower.** This project's own `data.py` documents this blob as "copied verbatim from the primary public `puzzlehunt/gsmgio-5btc-puzzle` README (fetched fresh via `gh api`, not retyped)" -- a community-repo transcription of creator content, not an independently Wayback-authenticated capture pinned alongside the Phase-2/3 artifact. |

Every password **preimage** has a further, separate provenance question
from the ciphertext:

- **Phase 2** (`causality`): the *value* comes from the community README
  (`puzzlehunt/gsmgio-5btc-puzzle`, lines 92-105) -- the Matrix Reloaded
  quote and "The password is causality" line are not present verbatim in
  this specific pinned Wayback artifact, which contains only the Phase-2
  ciphertext and the Phase-2-to-Phase-3 riddle text. A separate archived
  page (this project's earlier `gsmg.io/puzzle` capture) is the likely
  creator-authored source but was not re-authenticated as part of this
  phase's frozen input scope.
- **Phase 3** (the 7-part concatenation): the derivation *structure* is
  creator-authored and directly present in the pinned artifact. Parts
  1-6's literal values and the worked concatenation come from the
  community README's own solved computation (lines 172-192); part 7's
  pre-move FEN and the "find the non-mate move" instruction are creator-
  authored and present in the artifact, but the *post-move* FEN (part
  7's actual value) requires solving the chess problem the artifact
  poses -- its answer is not stated in the artifact itself.
- **Phase 3.2** (`jacquefrescogiveitjustonesecond` +
  `heisenbergsuncertaintyprinciple`): both clue-answer tokens come from
  the community README per `data.py`'s own comment; no separate
  Wayback-authenticated capture of the Phase-3.2 entry page is pinned in
  this project.

**The `openssl enc -aes-256-cbc -d -a ...` shell commands shown in the
community README are community-authored reproduction instructions, not
creator-toolchain evidence** -- this project has no authenticated record
of the creator invoking OpenSSL's CLI, a specific OpenSSL version, or any
particular operating system. The mechanical facts below (cipher, key
size, KDF, digest, padding) are established by reproducing the exact
bytes independently in Python (`cryptography` + a hand-rolled legacy
`EVP_BytesToKey`), not by trusting the README's own command line.

## Exact Base64 layout, per vector

| Vector | Total chars | Full-line length | Last line | Trailing newline | CR present |
|---|---:|---:|---:|---|---|
| Phase 2 | 910 | 64 | 64 (blank final split) | **yes** | no |
| Phase 3 | 5,569 | 64 | 44 | no | no |
| Phase 3.2 | 3,264 | n/a (1 line) | 3,264 | no | no |

Phase 2's textarea body ends with an extra `\n` after its final full
64-character line (14 lines x 64 chars, then one more newline before
`</textarea>`); Phase 3's does not -- it ends immediately after its
final, partial 44-character line. Both use bare `\n` line endings (no
`\r`), consistent with standard OpenSSL `-A`/default 64-column Base64
wrapping. Phase 3.2's value is stored pre-flattened (all whitespace
already stripped) in `data.py`; its original page-native wrapping is not
independently pinned by this audit.

## Mechanical verification result

All three vectors decrypt **exactly** under the identical construction:

```text
password  = SHA256(preimage).hexdigest().encode("ascii")   # lowercase, 64 bytes
KDF       = legacy EVP_BytesToKey, single round, SHA-256 digest
cipher    = AES-256-CBC
padding   = PKCS#7
container = b"Salted__" + salt(8) + ciphertext
```

| Vector | Salt | Container / ciphertext bytes | Password (SHA-256 hex) | Plaintext SHA-256 |
|---|---|---:|---|---|
| Phase 2 | `06286612d43ed7ed` | 672 / 656 | `eb3efb51...07e5bf` | `e2f9dd65...582b593a` |
| Phase 3 | `9fbc451d13d071f4` | 4,112 / 4,096 | `1a57c572...2ec30d5` | `c4ad9455...60af9865f` |
| Phase 3.2 | `eefc4c5befc1656a` | 2,448 / 2,432 | `250f3772...d61ce4c` | `b82afeb8...0d2d0e408a34` |

Each recovered plaintext starts with its independently-documented
prefix (README "Decryption result" text for Phase 2/3; `data.
PHASE32_PLAINTEXT_PREFIX` for Phase 3.2). Each was then **re-encrypted**
using its own original salt and the same password/KDF, and the result
reproduced the **complete original container byte-for-byte** (`Salted__`
header, salt, and all ciphertext bytes) for all three vectors -- this is
not merely "padding is valid," it is a full round-trip identity.

Full byte-level details (exact key/IV digests, plaintext digests, full
control-matrix results) are in `tools/gsmg/solved_vector_manifest.json`,
keyed by content digest per the project's convention of never storing
raw plaintext or derived key material directly in a checked-in artifact.

## Control matrix: representation and KDF

For each vector, 8 controls were run (24 total): 6 password
*representations* of the correct preimage under the correct KDF
(SHA-256), plus 2 *KDF* variants (MD5, SHA-1 `EVP_BytesToKey`) under the
one representation that worked. **Exactly one of the 8 succeeds, for all
three vectors, and it is the same one:**

| Control | Phase 2 | Phase 3 | Phase 3.2 |
|---|:-:|:-:|:-:|
| lowercase hex (correct) | ✅ | ✅ | ✅ |
| uppercase hex | ❌ | ❌ | ❌ |
| raw 32-byte digest | ❌ | ❌ | ❌ |
| lowercase hex + `\n` | ❌ | ❌ | ❌ |
| lowercase hex + `\r\n` | ❌ | ❌ | ❌ |
| literal preimage bytes | ❌ | ❌ | ❌ |
| lowercase hex, KDF=MD5 | ❌ | ❌ | ❌ |
| lowercase hex, KDF=SHA-1 | ❌ | ❌ | ❌ |

This reproduces and formalizes the 2026-08-20 investigation pass's own
finding (same MD5/SHA-1 "invalid padding" result for all three vectors)
under a complete, pre-declared control set rather than an ad hoc check.

## Ranked oracle guidance

This is guidance for prioritizing `cb_common.KDF_VARIANTS` entries in
future sweeps against the still-unresolved blobs (SALPH, COSMIC,
P32TRAILING) -- **it does not delete, reorder, or disable any existing
variant.** All entries remain available; this only documents which is
empirically supported by creator behavior and which are speculative
compatibility coverage.

1. **`("sha256", 32)`** -- legacy `EVP_BytesToKey`/SHA-256/AES-256-CBC.
   Demonstrated three separate times across this puzzle's entire solved
   history (Phase 2, Phase 3, Phase 3.2), with zero exceptions. This is
   the creator's one observed construction, not one hypothesis among
   several equally likely ones.
2. **`("sha256", 16)`** (AES-128-CBC, same digest) -- untested directly,
   but shares the demonstrated digest; retained as the next-most-
   plausible variant on general OpenSSL-compatibility grounds only, not
   because any evidence points to it.
3. **`("md5", 32)`, `("md5", 16)`, `("sha1", 32)`, `("sha1", 16)`** --
   explicitly falsified as the KDF digest for all three solved vectors
   (this audit's own control matrix). Retained in the oracle purely as
   historical-OpenSSL-version compatibility coverage for the *unsolved*
   blobs, which could in principle predate or postdate the solved
   vectors' toolchain; there is no positive evidence for any of them.
4. **PBKDF2 variants** (`pbkdf2_bytes_to_key`, any iteration count) --
   never demonstrated and, per this audit's own stopping rule,
   deliberately not swept here. Nothing in this audit either supports or
   rules them out; they remain exactly as plausible (or implausible) as
   before this phase ran.

## Disposition

**One consistent three-vector profile, no incompatibility.** This
formally closes P32 Family 7 and Post-Phase-340 Seed 3 as executed. Per
the user's own instruction, active searching pauses after this phase
pending independent evidence -- this artifact organizes and ranks
already-known evidence; it is not itself a new lead.

## Reopen condition

A fourth authenticated solved AES boundary appears (creator-confirmed
plaintext + known password), or new evidence establishes the creator's
actual command-line/OpenSSL-version/operating-system toolchain beyond
the mechanical KDF/cipher/padding facts already pinned here.
