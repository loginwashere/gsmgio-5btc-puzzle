# Phase 492 FAED-terminal P32 oracle protocol

Date: 2026-09-13
Status: frozen before candidate-manifest construction and oracle execution

## Question

Does any plaintext candidate already produced by the completed FAED width-30
or width-19 `{g,i}` runs act as the preimage for the unresolved
`P32TRAILING` password under the independently solved Phase-410 construction?

## Frozen candidate and transformation rules

- Candidate sources are exactly the four valid final candidates in
  `phase489_faed_width30_gi_result.json` and the six valid final candidates in
  the completed Phase-490R width-19 result. The two width-19 terminal orders
  rejected for invalid checkerboard segmentation contribute no plaintext and
  are excluded by construction.
- Candidate bytes are their saved uppercase ASCII plaintext fields exactly.
  No case changes, whitespace, affixes, corrections, words, or mutations are
  permitted.
- Each candidate contributes exactly one password:
  `SHA256(candidate_bytes).hexdigest().encode("ascii")` -- lowercase 64-byte
  hexadecimal text. This is the construction mechanically reproduced at all
  three solved boundaries by Phase 410.
- The sole consumer is `P32TRAILING`, using legacy one-round
  `EVP_BytesToKey` with SHA-256, AES-256-CBC, and strict PKCS#7 unpadding.
- Promotion requires either the existing strong printable-text threshold or
  the existing structural 64-byte binary validator. Padding alone is logged
  but never promotes.

The manifest is written and structurally reviewed before the execution lock.
The lock pins both source artifacts, the manifest, this protocol, the runner,
the shared oracle implementation, and the exact target ciphertext. One run,
ten decryptions, and no fallback variants are authorized.

## Interpretation

An authenticated decrypt is a strong lead requiring sensitive-output review.
No hit is a bounded negative for these ten exact candidate bytes under this
one solved password construction. It says nothing about other FAED orders,
boards, pairs, widths, plaintext transformations, or P32 password grammars.
