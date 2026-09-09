# Phase 481 — P32TRAILING Pwdb wordlist password audit

## Question

Does any entry in a large, externally sourced real-world password frequency
list open P32TRAILING when tried literally under the Phase-410 solved-boundary
crypto profile?

The frozen protocol is
`doc/Brainstorms/2026-09-06 - Phase 481 P32TRAILING Pwdb Wordlist Password Audit Protocol.md`.
This is the user-directed continuation of Phase 480: same target, same crypto
profile, same frozen validators — only the candidate universe changed, from
Phase 480's four derived address constructions to a fixed, hash-pinned
external wordlist file. It is a standard dictionary attack, not a new
structural hypothesis, and carries no claim that any entry is puzzle-motivated.

## Provenance and evidence strength

Phase 410 established the creator-calibrated solved-boundary profile: legacy
single-round `EVP_BytesToKey` with SHA-256, AES-256-CBC, and PKCS#7. This
audit tests only that profile against only P32TRAILING — it does not add
other blobs (SALPH, COSMIC, URLBLOB), other KDF digests, other key sizes,
other cipher modes, or a SHA-256-hex representation layer.

The wordlist carries no puzzle provenance: it is a generic top-10,000,000
real-world password frequency corpus,
`/home/loginwashere/projects/key-seeker/wordlists/Pwdb_top-10000000.txt`
(external to this repository), supplied directly by the user as the
candidate source. A negative result closes only "does a top-10M generic
password open this blob under this profile," not any puzzle-specific
hypothesis.

## Candidate universe

Frozen by content hash: SHA-256
`18dc49ca32b62455a61e3398f4ab9f93eb700ff142fa0d4b9fd11a727f3b80e4`, exactly
10,000,000 lines, verified to contain zero blank lines and zero exact
duplicate lines. Each line was read as raw bytes with only its trailing `\n`
stripped — no case folding, trimming, or re-encoding — so the 75 lines that
carry meaningful leading/trailing whitespace were tried unmodified. Each line
was exactly one password candidate, tried exactly once, with no
concatenation, truncation, or other transform.

## Frozen oracle and validators

Target P32TRAILING only. For each of the 10,000,000 candidates: parse the
existing OpenSSL `Salted__` envelope, derive via legacy single-round
`EVP_BytesToKey`/SHA-256, decrypt AES-256-CBC, and strictly validate PKCS#7.
Padding validity alone was recorded as a diagnostic only. A public positive
required either the established printable z-score ≥ 8, or the exact 64-byte
body plus full 16-byte padding shape (the two validators already established
by Phase 410/480).

## Execution lock

Because 10,000,000 per-attempt records are not a reviewable artifact, the
result records aggregate counts rather than one record per attempt (any
promoted or weak-tier record would still be captured in full). Before the
real run, the execution lock pinned:

- the protocol, audit script, verifier, and imported `cb_common`/`data`
  source files;
- the wordlist's path, SHA-256, line count, blank-line count, and
  duplicate-line count;
- P32TRAILING's salt and ciphertext digest;
- the sole Phase-410 cryptographic profile and its two validators.

The execution-lock SHA-256 is
`dcc8268fee3cf7c9cefe543cf31c4515511f3e4fc3cd8fa83a9e467c178bb738`.

## Result

```text
candidates attempted:                  10,000,000
valid-PKCS#7 diagnostics:              39,460
weak-tier bodies (5 <= z < 8):         0
strong-text promotions (z >= 8):       0
structural-binary promotions:          0
elapsed:                               111.6s (~89,600/s)
```

The observed valid-PKCS#7 diagnostic count (39,460 of 10,000,000, ≈1/253) is
consistent with the ~1/255 false-accept rate expected from a uniform-random
null model under a wrong key — not evidence of any partial match. Zero
candidates reached either promotion tier. No sensitive-hit or weak-candidate
file was created. The fail-closed verifier checked every locked dependency
hash and fully recomputed the aggregate result from an independent
re-streaming pass of the same locked wordlist, in 118.7s, with zero
discrepancies. Result SHA-256 `594749d958caa6528510ae1f857d88a65b484a1eef8f75fc772298033b8ae852`.

## Disposition

Bounded negative for this exact wordlist (by content hash), this
literal-byte representation, P32TRAILING, and the Phase-410 cryptographic
profile.

This does not close: other wordlists or password-database sources; other
representations of these same 10,000,000 strings (case variants, SHA-256-hex,
newline-appended, or other whitespace/normalization forms); other blobs
(SALPH, COSMIC, URLBLOB); or other cipher/KDF profiles. No candidate wordlist
entry is claimed to carry puzzle provenance — this was a standard external
dictionary attack, not a structural hypothesis about the puzzle.

## Artifacts

- frozen protocol and `phase481_execution_lock.json`;
- `phase481_p32_pwdb_wordlist_audit.py` and `phase481_result.json`;
- fail-closed verifier (`phase481_verify_run.py`) and `phase481_verification.json`;
- two Phase-481 unittest modules.
