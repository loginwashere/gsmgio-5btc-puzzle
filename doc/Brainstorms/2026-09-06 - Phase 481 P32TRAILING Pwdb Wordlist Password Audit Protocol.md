---
type: protocol
phase: 481
date: 2026-09-06
status: frozen-before-real-run
topics:
  - p32trailing
  - closed-system-passwords
  - wordlist-dictionary-attack
  - solved-boundary-grammar
---

# Phase 481 — P32TRAILING Pwdb Wordlist Password Audit Protocol

## Question

Does any single entry in a large, externally sourced real-world password
frequency list, tried literally as the AES passphrase under the Phase-410
solved-boundary crypto profile, open P32TRAILING?

This is the user-directed continuation of Phase 480: same target, same
crypto profile, same frozen validators, only the candidate universe changes
— from Phase 480's four derived address constructions to a fixed, hash-
pinned external wordlist file. This is a standard dictionary attack, not a
new hypothesis about puzzle structure; it carries no claim that any entry is
puzzle-motivated.

## Evidence and limitations

The creator-calibrated profile comes from Phase 410: all three solved AES
boundaries use legacy single-round `EVP_BytesToKey` with SHA-256, AES-256-CBC,
and PKCS#7. This protocol tests only that profile against only P32TRAILING —
it does not add other blobs (SALPH, COSMIC, URLBLOB), other KDF digests, other
key sizes, other cipher modes, or a SHA-256-hex representation layer. Those
remain untested by this phase, exactly as Phase 480 stated for its own scope.

The wordlist itself carries no puzzle provenance. It is a generic top-10M
real-world password frequency corpus
(`/home/loginwashere/projects/key-seeker/wordlists/Pwdb_top-10000000.txt`,
external to this repository), supplied directly by the user as the candidate
source for this run. A negative result closes only "does a top-10M generic
password open this blob under this profile," not any puzzle-specific
hypothesis.

## Candidate universe

Frozen by content hash, not by construction: the wordlist file, SHA-256
`18dc49ca32b62455a61e3398f4ab9f93eb700ff142fa0d4b9fd11a727f3b80e4`, exactly
10,000,000 lines, verified before the real run to contain zero blank lines
and zero duplicate lines. Each line is read as raw bytes with only its
trailing `\n` terminator stripped (no other trimming, no case folding, no
encoding renormalization) — 75 lines carry meaningful leading/trailing
whitespace and must survive unmodified. No line combination, concatenation,
truncation, or transformation is eligible; each line is exactly one password
candidate, tried exactly once.

## Frozen oracle

Target P32TRAILING only. For each of the 10,000,000 candidate byte strings,
perform one decryption:

- parse the existing OpenSSL `Salted__` envelope;
- legacy single-round `EVP_BytesToKey` with SHA-256;
- AES-256-CBC;
- strict PKCS#7 validation.

This is exactly 10,000,000 decryptions. No alternate blob, KDF digest,
cipher, key size, mode, representation form, or address lookup is part of
this experiment.

## Frozen validators

Identical to Phase 480: strict-padding validity is recorded but is only a
diagnostic. A public positive requires either:

1. valid PKCS#7 and `cb_common.printable_z_score(body) >= 8`; or
2. the established exact binary shape: AES block size 16, padding length 16,
   and a 64-byte body.

Any positive is written to a separate mode-0600 sensitive file and requires
manual review. Bodies scoring in the weak band (`5 <= z < 8`) are recorded
(bounded expectation under a uniform-random null of roughly 3 across 10M
attempts) but not promoted and not treated as evidence on their own.

## Controls and execution lock

Before the real run, the implementation must prove:

- the wordlist's SHA-256, line count, blank-line count, and duplicate count
  match the frozen values above;
- the Phase 3.2 solved vector opens under the selected profile and
  strong-text validator;
- synthetic strong text and exact 64-byte binary bodies are accepted;
- invalid padding and padding-valid weak noise are not promoted;
- only P32TRAILING is selected, and only the sole Phase-410 profile is used.

Then write an execution lock pinning this protocol, implementation, verifier,
`cb_common`/`data` dependencies, the wordlist's path/hash/line-count, P32
salt and ciphertext digest, profile, and validators. Only after the lock
verifies may the real run start. Because 10,000,000 per-attempt records
cannot reasonably be stored, the result records only aggregate counts
(attempts, padding-valid diagnostics, weak-tier count, promoted counts) plus
any promoted/weak records in full. A separate fail-closed verifier must
validate all locked hashes and fully recompute the aggregate result by
re-streaming the same locked wordlist.

## Decision and stop rule

- At least one strong validated result: `positive_requires_sensitive_review`;
- no strong result: `bounded_negative`.

A negative closes only this exact wordlist file (by content hash), this
literal-byte representation, P32TRAILING, and the Phase-410 crypto profile.
It does not close other wordlists, other representations (case variants,
SHA-256-hex, newline-appended forms), other blobs, or other cipher/KDF
profiles.
