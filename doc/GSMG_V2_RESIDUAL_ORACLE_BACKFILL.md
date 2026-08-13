---
type: audit
phase: 257
date: 2026-08-13
status: closed
result: negative
disposition: structural-only
evidence_level: solver-derived
topics:
  - candidate-corpus
  - wordlists
  - openssl
related_phases: [25, 44, 79, 88, 89, 90, 116, 253, 256]
script: tools/gsmg/curated_v2_residual_oracle_backfill.py
aliases:
  - Phase 257
---

# GSMG V2 Residual Oracle Backfill

## Result

No full 508-candidate rerun was necessary. Reviewing Phase 256 against the
actual historical records reduced its broad “136 candidates still need stream
and Key Wrap” statement to two small, different residuals:

1. `SEED` and `IZLKESEEDQPPEN` were absent from the historical 648. Phase 253
   tested them only under Blowfish/Camellia/SEED-CBC, leaving the older
   AES/3DES CBC family plus AES-ECB, AES-CFB/OFB/CTR, and AES Key Wrap.
2. The 19 Looking Forward candidates were tested against all four blobs under
   CBC and Key Wrap in Phase 44, but without newline forms and before the
   stream oracle existed. Phase 256 supplied current newline-aware CBC. The
   remaining conservative closure was newline-aware ECB, stream, and Key Wrap.

Fresco's 55 candidates and SafeNet/Luna's 62 candidates were already recorded
as newline-aware, all-four-blob negatives across CBC, ECB, stream, and Key
Wrap. They were not rerun.

## Fixed scope

```text
SEED candidates:                 2  digest 10da6a91233b3292
Looking Forward candidates:    19  digest bf5116a99829c05f
combined candidates:           21  digest 537635ec6fa1ce0f
SEED unique passphrases:       36
Looking Forward passphrases:  792
combined unique passphrases:  828
tracked blobs:                  4  SALPH/COSMIC/P32TRAILING/URLBLOB
```

Operations:

| Family | Candidate scope | Variants | Effective operations |
|---|---:|---:|---:|
| Older AES/3DES CBC | 2 SEED leads / 36 passphrases | 24 | 3,456 decryptions |
| AES-ECB | all 21 / 828 passphrases | 12 | 39,744 decryptions |
| AES-CFB/OFB/CTR | all 21 / 828 passphrases | 36 | 119,232 decryptions |
| AES Key Wrap | all 21 / 828 passphrases | 12 KDF/KEK variants × 4 unwrap conventions | 158,976 unwrap attempts |
| **Total** |  |  | **321,408 effective operations** |

All passphrase scopes use `answer_forms()` followed by newline-aware
`keystr_forms()` and deduplicate exact bytes before oracle work.

```text
CBC hits:     0
ECB hits:     0
stream hits:  0
Key-Wrap hits: 0
wall time:    3m22.96s
```

## Corrections to Phase 256

- The Phase-256 helper's docstring said 47 CBC variants; the implemented and
  tested arithmetic is `6 + 18 + 20 = 44`.
- P32TRAILING was introduced in Phase 25, not Phase 77.
- Fresco and SafeNet/Luna did not have an outstanding stream/Key-Wrap gap.
- Looking Forward was the only promoted 136-candidate source needing the
  newline-aware non-CBC residual, while the two SEED leads formed a separate
  V2-core gap.

The Phase-256 zero-hit CBC run remains valid. These corrections narrow its
novelty and rationale; they do not invalidate its decryptions.

## Verdict

The V2 corpus now has current direct passphrase-oracle coverage for every
candidate it newly adds to the historical corpus. No full V2 rerun is needed.
Future reruns should be triggered by a registry digest change, a new blob,
or a genuinely new oracle family—not merely by regrouping already-tested
candidates.

## Reproduction

```bash
python3 tools/gsmg/curated_v2_residual_oracle_backfill.py --self-test
python3 tools/gsmg/curated_v2_residual_oracle_backfill.py --run
```
