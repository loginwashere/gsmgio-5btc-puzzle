---
type: audit
phase: 524
date: 2026-09-18
status: complete
result: closed-negative
disposition: rejected
script: tools/gsmg/phase524_slot_grammar_sweep_prep.py
topics:
  - salph
  - closed-system
  - password-grammar
  - gpu-oracle
---

# GSMG Phase 524 — Slot-Grammar Password Sweep (Execution of Phase 523)

## Question

Phase 523 pre-registered a house-style slot-grammar product for SALPH and
showed it was essentially untested. Does any member of that product open
SALPH, or any of the other three tracked blobs, under the project's
standard passphrase oracle?

## Frozen inputs

Exactly the Phase 523 pre-registration: 62 authenticated checkpoint values
across the four macro slots, two join conventions (connected, single
space), fixed macro order, standard `answer_forms() x keystr_forms(newline)`
expansion. Input file: Phase 523's `not_all_covered_bases.txt`, verified
against its recorded SHA-256 `ff5e80e9...092a18` (133,657 bases).

## Method

1. **Decode.** Phase 523's export is JSON-lines. Feeding it to the GPU tool
   raw would have tested every candidate with literal quote characters, so
   the prep script decodes each line and asserts every base is safe for the
   tool's plain-line reader (no leading or trailing whitespace, no `#`, no
   newline).
2. **Deduplicate.** A base is kept only if its expansion contains a
   material neither already tested nor already scheduled. This removed 110
   bases (133,547 kept); an assertion confirms the kept list schedules the
   same set of untested materials as the full list (3,021,886 unique). Most
   redundancy is inside each base's own letters-only forms, so the tool
   still re-tests roughly twice the unique materials. That is wasted GPU
   time, not a coverage gap.
3. **Run.** `tools/gpu_oracle` native binary, self-test passed first, input
   SHA-256 `5193ff52...290bdc`, `--newline-variants`, default 60-variant
   table across all four blobs (a superset of the pre-registered
   SALPH-under-six-legacy-CBC scope; the tool cannot restrict blobs). The
   tool emitted 6,245,712 forms, 283 more than the prep count: the 283
   digit-only bases each produce an empty-string letters-only form that the
   prep count dropped. About 1.5 billion decrypt attempts in 8,436 s at
   about 740 forms per second.
4. **Review weak-tier hits.** The GPU tool records no body for weak hits, so
   the new `--classify-weak` step re-derives each recorded row's body with
   `cb_common`'s KDF helpers and `cryptography`, checks the recomputed
   z-score against the GPU's, and runs `key_shape_classifier.classify_body`
   (its self-test passes first). This step is committed code; Phase 333's
   equivalent was a throwaway.

## Result

| Quantity | Value |
|---|---:|
| Forms tested | 6,245,712 of 6,245,712 (checkpoint complete) |
| Strong hits | 0 |
| Structural hits | 0 |
| Key-shape records written | 0 |
| Weak-tier hits (z 5.00 to 5.93) | 285 |
| Weak hits by blob | SALPH 40, COSMIC 55, P32TRAILING 43, URLBLOB 147 |
| Weak bodies re-derived | 285 of 285, zero padding failures |
| Recomputed z-score mismatches | 0 |
| hex64 / WIF / BIP39 matches in weak bodies | 0 |

The weak rate is 4.6e-5 per form, in line with Phase 328 (43 in 588,942
forms) and Phase 334 (42 in 725,760): the known noise band at this volume.
No SALPH decrypt produced a strong or structural result, including the
exact 64-byte full-pad shape a two-key plaintext would give.

## Limitation: the Bloom cache was not loaded

The run logged that the Bloom cache could not be loaded: the binary's
compile-time default path points at a Docker location (`/repo/...`), and
`tools/gpu_oracle/db/` is empty. Consequences, stated precisely:

- **Unaffected:** the pre-registered detector. The printable z-score gate
  (strong at 8.0) and the exact structural full-pad check run on the GPU
  independent of the Bloom filter, and structural hits are address-derived
  and logged regardless.
- **Not active:** the two secondary raw-key arms, the unconditional Bloom
  check of the first two 32-byte chunks of non-printable, non-structural
  CBC/ECB bodies and of every stream-mode body, and the Phase 331
  known-target detector. Phases 328 and 334 ran with these arms on.

The gap only matters if the true plaintext is raw binary, not 64 bytes, and
not printable. That is possible but unlikely for an 80-byte SALPH
ciphertext. Closing it means rerunning with
`--bloom-cache <repo>/db/addresses.hash160.bloom`, about 2.3 hours. It is
recorded as a reopen condition rather than done here because it is outside
the Phase 523 pre-registration.

## Disposition

Rejected for this candidate universe: the 62 authenticated slot values, two
join conventions, fixed macro order, standard form expansion, four blobs,
AES-CBC/ECB/CFB/OFB/CTR under legacy MD5/SHA-1/SHA-256 and PBKDF2 at three
key sizes, with the Bloom arms inactive. No widening on a negative, per the
pre-registered stop rule.

## Facts affected

None.

## Supersedes/corrects

None. Phase 523's exported base list is JSON-lines, which its own document
did not say; the execution phase decodes it.

## Artifacts

- `tools/gsmg/phase524_slot_grammar_sweep_prep.py` (`--prepare`,
  `--verify`, `--classify-weak`, `--self-test`)
- `tools/gsmg/test_phase524_slot_grammar_sweep_prep.py` (6 tests)
- Runtime outputs, gitignored:
  `tools/gpu_oracle/output_local/phase524.{hits,keyshape,checkpoint}.jsonl`,
  `_work/phase524/{bases.txt,prepare_report.json}`. `output/` and
  `checkpoints/` are root-owned from earlier Docker runs; native runs use
  `output_local/`.

## Reopen condition

Reopens on a new authenticated checkpoint value (a new slot value or a
selector for one), not on re-running these values. Separately, the Bloom
rerun above closes the raw-key gap for this same universe.
