# Phase 507 — FAED terminal AES oracle

Date: 2026-09-15
Status: protocol frozen before manifest and oracle execution

## Question

Do any exact terminal plaintext candidates retained by the completed Phase 489,
504, or 506 FAED searches unlock an authenticated AES consumer even though the
candidate is not readable?

## Candidate universe

- all 4 final candidates from Phase 489 (`{g,i}`, width 30);
- all 5 final candidates from Phase 504 (`{g,i}`, width 19 unrestricted);
- all 34 final candidates from the five Phase-506B pair runs.

Candidates must be nonempty uppercase ASCII letters and are deduplicated by
exact bytes while retaining every provenance record. No case changes, suffixes,
prefixes, whitespace, word mutations, fragments, or combinations are allowed.

Each candidate contributes exactly one password:

`SHA256(candidate_bytes).hexdigest().encode("ascii")`

This is the solved-boundary construction established by Phase 410.

## Consumers and crypto profile

Test exactly `SALPH`, `COSMIC`, and `P32TRAILING` from `cb_common.BLOBS` under
legacy EVP_BytesToKey with SHA-256, AES-256-CBC, and strict PKCS#7 validation.
The quarantined `URLBLOB` is outside scope. A result promotes only as strong
text or the existing structural 64-byte binary class; padding alone is merely
reported.

Expected scope after manifest construction: 43 unique candidates and 129
decryptions. The execution lock pins the manifest, sources, runner, crypto
implementation, targets, validators, and counts before the real oracle runs.

## Stop rule

Zero promoted decryptions is a bounded negative for these exact candidate
bytes, password construction, three consumers, and crypto profile. Do not
expand representations after inspecting the result.
