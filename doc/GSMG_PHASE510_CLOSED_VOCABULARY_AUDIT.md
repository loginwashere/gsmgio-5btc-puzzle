# Phase 510 closed-system vocabulary audit

Date: 2026-09-15

## Outcome

The exact closed-system vocabulary is too sparse to serve as a standalone
FAED search objective. Phase 510A mechanically produced 108 unique terms of
length at least five from four eligible literal sources. Phase 510B then held
out each of the three substantial solved plaintexts and scored it using only
terms available from the other documents.

All three fixtures failed the frozen 5% matched-character coverage gate:

| held-out plaintext | normalized length | matched characters | coverage |
|---|---:|---:|---:|
| Phase 2 | 440 | 17 | 3.8636% |
| Phase 3 | 534 | 22 | 4.1199% |
| Phase 3.2 | 455 | 6 | 1.3187% |

Because Gate A failed, the protocol stopped before its conditional shuffle
stage. Zero null trials ran. No FAED data was imported or scored, no
checkerboard or transposition search ran, and no GPU work occurred.

## Phase 510A corpus discipline

Eligible material was restricted to literal regions of the three solved AES
plaintexts byte-for-byte verified by Phase 410 and authenticated `CIAO BELLA
O` page text. Embedded ciphertext/binary regions were excluded. Exact solved
preimages and the unspaced Phase-3.2.2 answer were retained only as hashed
exact-sequence controls; they were not split using inferred word boundaries.

The manifest excludes findings/brainstorm prose, solver outputs, community
suggestions, recognition-only terms, dictionaries, password lists, synonyms,
stemming, typo repair, OCR, and representation-incompatible Base58/hex syntax.

Manifest SHA-256:
`1f6cde61ca1b2adff89fa2ede1cef001b0f24a046b6d94572513d4cd8a68a5fb`

## Phase 510B gate

The scorer normalized each held-out plaintext to lowercase letters, assigned
term weight `(length-4)^2`, and selected maximum-weight non-overlapping exact
matches. It was required to cover at least 5% of every held-out plaintext
before any shuffle comparison. The few matches were mostly generic overlaps
such as `which`, `answer`, and `puzzle`; Phase 3 also matched `human` inside
`humanity`. This is insufficient demonstrated transfer to unseen authentic
puzzle text.

## Disposition

Do not integrate this exact-word vocabulary as a standalone checkerboard or
transposition objective, and do not score FAED with it. A same-corpus planted
fixture would be circular because it would be constructed from words the
objective already contains.

This does not close all domain adaptation. A character-level model or a small
frozen vocabulary bonus layered onto another independently calibrated
objective could generalize across unseen words. Any such proposal must first
pass the same leave-one-document-out authentic-text test and then a
family-wide real-versus-shuffle calibration before selecting GPU runs.

## Verification

The result was recomputed from the locked manifest and literal regions. All
three score/match records reproduced exactly, all null arrays were confirmed
empty, and 8/8 focused Phase-510 tests pass.

- Execution-lock SHA-256:
  `8a64869563286d4a7f82a1e8e6e75b37be7e1cf978d3dbd440eb5304cf96f133`
- Result SHA-256:
  `631573912e3bc058e3c367b1d5181c261ed9f5446c6acfe8a212411e28bc5550`

