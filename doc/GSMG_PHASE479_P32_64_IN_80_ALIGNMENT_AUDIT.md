# Phase 479 — P32TRAILING 64-in-80 exhaustive alignment audit

## Question

Could a correct no-padding decryption of P32TRAILING contain two contiguous
32-byte objects beginning at an offset missed by the existing block-aligned
detector?

The prior detector examined individual windows at offsets 0, 16, 32, and 48,
but paired only offsets 0 and 32. Phase 479 completed the natural geometry:
every start 0 through 16 for a contiguous 64-byte `A || B` payload inside the
80-byte decrypted body. The frozen protocol is
`doc/Brainstorms/2026-09-06 - Phase 479 P32 64-in-80 Alignment Protocol.md`.

## Locked scope

- 648 established curated candidates, digest `2d233645ef49a141`;
- 14,551 deduplicated password byte strings from the established normalization,
  literal/SHA-256/double-SHA-256, and LF/CRLF representation rules;
- P32TRAILING only;
- the creator-calibrated profile reproduced by all three solved encrypted
  stages: legacy `EVP_BytesToKey`/SHA-256, AES-256-CBC;
- all 80 decrypted bytes retained, with no padding decision;
- 17 alignments and, at each, A, B, and Phase 336's 15 frozen combination
  operations;
- exact comparisons against the prize and halving-storage addresses as the
  authenticated tier, and eight P+G/P-G/P/2/2P encodings as a separately
  labelled derived-control tier;
- literal ASCII address and raw 20-byte HASH160 scans;
- no Bloom, vanity-prefix, printable-text, or adaptive validator.

The execution lock SHA-256 is
`96ecc23e15d873541dba58f2afe7af7bb6e97050098bea37ae3f85871cfc05a8`.

## Controls

Five unit-test groups passed before locking. They pin the corpus and container
geometry, reproduce the solved Phase 3.2 vector under the chosen crypto
profile, recover planted A/B keys at every offset, recognize both distinct
target orders, recover a combination-only planted target, recognize literal
address and raw-HASH160 forms, reject a deterministic wrong body, and detect
lock tampering.

## Result

```text
candidates:                       648
password byte strings:         14,551
P32 decryptions:               14,551
alignments/decryption:             17
scalar interpretations/alignment: 17
planned scalar checks:       4,205,239
exact authenticated hits:            0
exact derived-control hits:           0
distinct authenticated pair hits:     0
literal address/HASH160 hits:          0
```

No sensitive-hit file was created. The fail-closed verifier checked every
source hash named by the lock and reproduced the saved result exactly through
a full second computation.

## Disposition

Bounded negative for this 648-candidate/14,551-password universe under the
creator-calibrated CBC profile and the complete contiguous 64-in-80 alignment
family. This closes the non-block-aligned placement blind spot for these
passwords and target addresses.

It does not rule out an unknown password, another KDF/cipher/mode, two
non-contiguous objects, unknown destination addresses, a plaintext that is not
private-key material, or the still-unrun Tier-1 trailing-space backfill.

## Artifacts

- frozen protocol and execution lock;
- `tools/gsmg/phase479_p32_alignment_audit.py`;
- `tools/gsmg/phase479_result.json`;
- `tools/gsmg/phase479_verify_run.py` and `phase479_verification.json`;
- two unittest modules.

