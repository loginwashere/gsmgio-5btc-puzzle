# Phase 480 — Closed-system address password audit

## Question

Could the two authenticated Bitcoin addresses already present in the puzzle,
optionally preceded by the authenticated puzzle banner, construct the password
for P32TRAILING?

The frozen protocol is
`doc/Brainstorms/2026-09-06 - Phase 480 Closed-System Address Construction Protocol.md`.
This experiment deliberately remained inside already-known puzzle material; it
did not add book OCR, internet vocabulary, transaction fields, separators, or
normalization sweeps.

## Provenance and evidence strength

Phase 410 established the creator-calibrated solved-boundary rule
`SHA256(preimage).hexdigest()` followed by legacy
`EVP_BytesToKey`/SHA-256 and AES-256-CBC/PKCS#7. The SalPhaseIon entry slug
independently uses `SHA256(banner || prize_address).hexdigest()`, although it is
not a solved AES boundary.

The two-address idea itself is community-motivated. The pinned Telegram export
records Anton (`@homeless_phd`) proposing concatenated addresses on 2024-04-20;
the creator did not endorse the proposal. Phase 370 also established that
P32TRAILING has no local instruction bytes selecting an address construction.
These facts keep the family low-prior and make the result strictly bounded.

## Phase 480A — construction and novelty

Four separator-free preimages were frozen:

1. prize address, then halving-storage address;
2. halving-storage address, then prize address;
3. puzzle banner, prize address, halving-storage address;
4. puzzle banner, halving-storage address, prize address.

Each contributed its literal bytes as a representation control and lowercase
ASCII SHA-256 hex as the creator-calibrated primary password: eight exact byte
strings total.

The exact-byte comparator found all eight absent from its named historical
corpora: Phases 265–270, 314, 317, 341, 370, 416, 421 and 478, plus the
historical-648, V2-full and historical-Tier-1 normalized material. It streamed
1,749,878 eligible Phase-478 records and made zero cryptographic-oracle calls.
This is a novelty statement relative to those named corpora, not a claim about
every experiment ever performed.

## Phase 480B — locked oracle

After the construction and validators were frozen, the execution lock pinned:

- the protocol, oracle, verifier, comparator and result, and imported source
  files;
- all eight password byte strings and their hashes;
- P32TRAILING's salt and ciphertext digest;
- the sole Phase-410 cryptographic profile;
- the strong-text threshold and exact 64-byte binary validator.

The execution-lock SHA-256 is
`9206e7fb84537aa880f2acde03ec85749a91e7cad01455aefa42ce3291767285`.

Exactly eight AES decryptions were performed. Strict PKCS#7 validity was
recorded for every result but could not promote a result by itself. Promotion
required either the project's established printable z-score of at least 8 or
the exact 64-byte body plus full 16-byte padding shape.

## Result

```text
constructions:                         4
primary SHA-256-hex passwords:         4
literal-preimage controls:             4
P32 decryptions:                       8
valid-PKCS#7 diagnostics:              0
promoted primary results:              0
promoted representation controls:      0
```

Every decryption failed strict padding. No sensitive-hit artifact was created.
The fail-closed verifier checked all locked dependency hashes and fully
recomputed the eight-result artifact. Verification passed with result SHA-256
`1970e47c260e6fc1941166ed41b2de788a9326a1f5c14da2d04f87a70a80cd77`.

## Disposition

Bounded negative for these four constructions, their two frozen password
representations, P32TRAILING, and the Phase-410 cryptographic profile.

This does not close other closed-system wordlist constructions, selected
address operations, transaction fields, separators or transformations,
alternate cryptographic profiles, or plaintext structures outside the frozen
validators. More importantly, it does not turn the unauthenticated community
proposal into creator evidence: the experiment was worth eight queries because
the candidate bytes were genuinely new, not because the source selector was
strong.

## Artifacts

- frozen protocol and `phase480_execution_lock.json`;
- `phase480_address_novelty_comparator.py` and its result;
- `phase480_p32_address_password_audit.py` and `phase480_result.json`;
- fail-closed verifier and verification record;
- two Phase-480 unittest modules.
