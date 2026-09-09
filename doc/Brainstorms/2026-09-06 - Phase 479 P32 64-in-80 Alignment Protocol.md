---
type: protocol
phase: 479
date: 2026-09-06
status: frozen-before-real-run
topics:
  - p32trailing
  - no-padding
  - private-keys
  - alignment
---

# Phase 479 — P32TRAILING 64-in-80 Exhaustive Alignment Protocol

## Question

Could the correct decryption of the 80-byte P32TRAILING ciphertext contain
two contiguous 32-byte objects at a non-block-aligned offset that the existing
`-nopad` detector missed?

The existing detector checks raw 32-byte windows at offsets 0, 16, 32, and 48
and applies its paired operations only to offsets 0 and 32. A contiguous
64-byte payload can begin at any offset 0 through 16 inside an 80-byte body.
Offsets 1 through 15 have therefore not received the same exact-address test.

## Frozen password universe

Use `extended_cipher_recheck.load_curated_candidates()` exactly as shipped:
648 ordered candidates, digest `2d233645ef49a141`. Expand them with
`binary_key_material_backfill.normalized_keystrings(...,
whitespace_variants=False)`: the established `answer_forms()` normalizations,
literal/single-SHA-256-hex/double-SHA-256-hex representations, and LF/CRLF
variants. The deduplicated total must be exactly 14,551 password byte strings.

No new candidate, wordlist, separator, or whitespace form may be added after
this protocol is frozen.

## Frozen cryptographic profile

Only the profile reproduced byte-for-byte by all three solved encrypted
boundaries in Phase 410 is eligible:

- OpenSSL `Salted__` container salt already parsed by `cb_common.BLOBS`;
- lowercase candidate bytes as supplied by the frozen representation layer;
- legacy single-round `EVP_BytesToKey` with SHA-256;
- AES-256-CBC;
- no padding removal: retain the complete 80 decrypted bytes.

This deliberately does not multiply the alignment experiment by alternate
KDFs, key sizes, modes, or ciphers.

## Frozen body interpretations

For every decrypted body and every start `s` in `0..16`, define:

```text
A = body[s:s+32]
B = body[s+32:s+64]
```

Check A and B independently, then the 15 operations already frozen in Phase
336: XOR; addition and both directed subtractions modulo secp256k1 order; both
byte-interleaves; both half-splices; both nibble-interleaves; SHA-256 of A||B,
B||A, and A XOR B; and both directed HMAC-SHA-256 forms.

For every valid scalar, derive compressed and uncompressed P2PKH HASH160s and
compare against two disjoint target tiers:

1. authenticated: prize address and halving-storage address;
2. derived controls: P+G, P-G, P/2, and 2P, compressed and uncompressed.

Also scan the complete 80-byte body for the literal ASCII form and decoded
20-byte HASH160 of each frozen target. A pair hit means A and B independently
reach the two different authenticated addresses in either order. Equality of
the two halves or addresses is never required.

## Positive controls and lock

Before the real run, the implementation must prove:

- exact corpus count and digest;
- exact P32 container geometry;
- Phase 3.2's solved vector decrypts under the frozen crypto profile;
- planted A and B hits are recovered at every offset 0 through 16;
- both pair orders are recognized;
- a planted combination-only hit is recovered;
- literal-address and raw-HASH160 hits are recovered;
- a deterministic wrong body yields no target hit.

After those tests pass, write an execution lock pinning this protocol, the
audit script, relevant imported implementation files, the candidate digest,
the P32 blob digest, and both target tiers. Only then may `--run` evaluate the
real P32 corpus.

## Decision and handling

An exact authenticated-target match is a positive. An exact derived-control
match is separately labelled and is not silently promoted to an authenticated
puzzle-address hit. Vanity-prefix or Bloom-filter membership is excluded.

The public result contains candidate/passphrase hashes and structural labels,
not recovered private-key bytes. Any exact hit material is written separately
with mode `0600` and must be reviewed before publication.

No hit is a bounded negative for this password universe, crypto profile,
64-in-80 geometry, operations, and target registry. It does not rule out an
unknown password, another cipher/KDF, non-contiguous keys, unknown destination
addresses, or non-key plaintext.

