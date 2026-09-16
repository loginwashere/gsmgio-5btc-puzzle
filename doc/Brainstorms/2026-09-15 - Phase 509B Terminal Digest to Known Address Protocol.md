# Phase 509B — terminal digest to known-address protocol

Date: 2026-09-15
Status: frozen before address derivation

## Question

Does the raw SHA-256 digest of any of the 43 exact Phase-507 FAED terminal
strings constitute the secp256k1 private key for either directly known puzzle
address?

## Frozen family

- Inputs: the unchanged 43 unique terminal byte strings in the locked
  Phase-507 candidate manifest.
- Transformation: exactly `SHA256(terminal).digest()`.
- Consumer: interpret the 32 bytes as a big-endian secp256k1 private scalar.
- Derivations: legacy mainnet P2PKH for both compressed and uncompressed public
  keys.
- Targets: exactly `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe` and
  `17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa`.
- Acceptance: exact derived-address equality only.

There are 86 derived addresses and 172 exact address comparisons. No
substring, case change, alternate hash, double hash, scalar arithmetic,
neighbor target, AES query, balance lookup, Bloom filter, or network request
is permitted.

The public result records candidate identifiers and derived addresses, not a
new plaintext interpretation. Any exact hit is written separately with mode
0600 and requires immediate verification through the independently
implemented address derivation already present in the project.

## Interpretation

An exact hit is overwhelming evidence: the simple random-oracle union bound is
`172/2^160`, approximately `1.18e-46`. A miss closes only this one
digest-to-private-key interpretation of these 43 already-produced terminals.
It does not validate or reject their transposition solver, Model B, other
terminal candidates, or other key constructions.

