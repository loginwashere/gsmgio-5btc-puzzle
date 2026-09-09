---
type: protocol
phase: 480
date: 2026-09-06
status: frozen-before-real-run
topics:
  - p32trailing
  - closed-system-passwords
  - bitcoin-addresses
  - solved-boundary-grammar
---

# Phase 480 — Closed-System Address Construction Protocol

## Question

Do the two authenticated Bitcoin addresses already present in this puzzle,
optionally preceded by the authenticated puzzle banner, supply the preimage or
password for P32TRAILING?

This is a small source-bound experiment, not a general wordlist expansion. It
tests the only surviving constructions from the Phase 480 exact-byte novelty
comparison. No book OCR, external vocabulary, separator sweep, case sweep, or
newly invented token is admitted.

## Evidence and limitations

The creator-calibrated construction comes from Phase 410: all three solved AES
boundaries use

```text
password = SHA256(preimage).hexdigest().encode("ascii")
```

with legacy single-round `EVP_BytesToKey`/SHA-256 and AES-256-CBC/PKCS#7.
The SalPhaseIon entry slug independently confirms the related preimage
construction `SHA256(banner || prize_address).hexdigest()`, but it is an entry
URL, not a fourth solved AES boundary.

The two-address proposal is community motivation, not creator evidence. It is
recorded in the Telegram export `files/Msgs.txt`, SHA-256
`645da52bce92e3de7fc29b77b21f0f946411c706f0fba805c6b84330f999cc8c`,
line 67235: Anton (`@homeless_phd`), 2024-04-20 12:51 UTC. The following
creator message does not endorse the password proposal. Consequently the
address-only constructions remain low-prior controls even though their
components are authenticated puzzle facts.

Phase 370 established that the byte gap before P32TRAILING is only
`b"\r\n\r\n"`, with zero local instruction bytes. Nothing at the P32 boundary
selects these constructions. A negative therefore closes only this exact
finite family.

## Phase 480A — frozen construction and novelty audit

Use the constants already pinned by `first_hint_hash_audit.py`:

```text
B = b"GSMGIO5BTCPUZZLECHALLENGE"
P = b"1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
H = b"17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa"
```

The complete preimage family is exactly:

1. `P || H` (`prize_then_halving`);
2. `H || P` (`halving_then_prize`, order control);
3. `B || P || H` (`banner_prize_halving`);
4. `B || H || P` (`banner_halving_prize`, order control).

Each contributes exactly two password byte strings:

- the literal preimage, labelled `preimage` and treated as a representation
  control;
- lowercase ASCII `SHA256(preimage).hexdigest()`, labelled
  `sha256_hex_password` and treated as the creator-calibrated primary form.

No delimiter, whitespace, case, raw-digest, double-hash, address abbreviation,
transaction field, or extra banner placement is eligible.

The already-completed reconnaissance comparator must be pinned unchanged. It
found all 8 materials absent by exact byte membership from the named Phase
265–270, 314, 317, 341, 370, 416, 421, 478, historical-648, V2-full, and
historical-Tier-1 corpora. That establishes novelty relative to those named
corpora only; it does not claim a universal history of every byte ever tried.
The comparator made zero oracle calls and never read P32TRAILING.

## Phase 480B — frozen oracle

Target P32TRAILING only. For each of the 8 password byte strings, perform one
decryption under the sole Phase-410 profile:

- parse the existing OpenSSL `Salted__` envelope;
- legacy single-round `EVP_BytesToKey` with SHA-256;
- AES-256-CBC;
- strict PKCS#7 validation.

This is exactly 8 decryptions. No alternate blob, KDF digest, cipher, key size,
mode, no-padding interpretation, alignment, key operation, or address lookup is
part of this experiment.

## Frozen validators

Record strict-padding validity for every attempt, but padding alone is only a
diagnostic. A public positive requires either:

1. valid PKCS#7 and the established `cb_common.printable_z_score(body) >= 8`;
   or
2. the established exact binary shape: AES block size 16, padding length 16,
   and a 64-byte body.

Any positive is written to a separate mode-0600 sensitive file and requires
manual review. A merely padding-valid weak body is reported without plaintext
and is not promoted.

## Controls and execution lock

Before the real run, the implementation must prove:

- the four exact preimages and their lengths (68, 68, 93, 93);
- the eight exact material hashes match the frozen Phase 480A result;
- the two tiers contain four distinct entries each;
- the Phase 3.2 solved vector opens under the selected profile and strong-text
  validator;
- synthetic strong text and exact 64-byte binary bodies are accepted;
- invalid padding and padding-valid weak noise are not promoted;
- only P32TRAILING is selected.

Then write an execution lock pinning this protocol, implementation, Phase 480A
comparator and result, imported construction/crypto/data files, exact material
manifest, P32 salt and ciphertext digest, profile, and validators. Only after
the lock verifies may the 8 real decryptions run. A separate fail-closed
verifier must validate all locked hashes and fully recompute the result.

## Decision and stop rule

- At least one strong validated result: `positive_requires_sensitive_review`;
- no strong result: `bounded_negative`.

The primary and representation-control tiers are reported separately. A
control-tier hit remains cryptographically real if verified, but does not
retroactively validate the solved-boundary hash grammar.

A negative closes only these four constructions, their two frozen
representations, P32TRAILING, and the Phase-410 crypto profile. It does not
close other wordlist sources, address-derived operations, transaction fields,
other password transformations, other cipher/KDF profiles, or non-text/non-64-
byte plaintext structures.
