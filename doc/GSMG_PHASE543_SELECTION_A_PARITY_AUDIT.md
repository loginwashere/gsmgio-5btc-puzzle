---
type: audit
phase: 543
date: 2026-09-21
status: complete
result: closed-negative
disposition: rejected
script: tools/gsmg/phase543_selection_a_parity_audit.py
topics:
  - selection-a
  - matrixsumlist
  - slot-grammar
  - password-oracle
---

# Phase 543 — Selection A parity audit

## Question

The historical `IZLKESEEDQPPEN` construction received matrix-direction,
Caesar, direct-cipher and macro-slot tests that were not all repeated for
Selection A's `IZLKESKGGIPPEN` or its terminal-`e` completion
`IZLKEXKGGIPPEN`. Do those bounded parity checks produce a lead?

## Structural family

The audit rebuilds both Selection A matrices from repository code. It applies
the same four literal directions as Phase 140 and every uniform Caesar shift
as Phase 141. Its null shuffles the 23 fixed DBBI groups over Selection A's
fixed endpoints and accepts only collision-free placements. The completed arm
also requires the fixed event-25 destination to remain empty before placing
`e=5`. Each arm uses 20,000 accepted permutations, seed `20260921`.

| Matrix | Rows forward | Columns forward | Direction p | Caesar-family p |
|---|---|---|---:|---:|
| 83 cells | `IZLKESKGGIPPEN` | `GBCXYGAWMUHFEV` | 0.17134 | 0.60312 |
| 84 cells | `IZLKEXKGGIPPEN` | `GBCXYGFWMUHFEV` | 0.40958 | 0.74236 |

The best Caesar outputs are `JALLECCGOAGHVE` and `JALLECCGTAGHVE`.
Neither matrix is exceptional under its complete declared family.

## Exact direct-cipher parity

Both row outputs expand to 36 distinct newline-aware passphrase materials.
Against `SALPH`, `COSMIC`, `P32TRAILING` and `URLBLOB`, the audit ran:

- 24 AES/3DES CBC variants;
- 12 AES-ECB variants;
- 36 AES-CFB/OFB/CTR variants;
- 12 AES Key Wrap KDF/KEK variants under four unwrap conventions; and
- 20 Blowfish/Camellia/SEED-CBC menu-gap variants.

That is 20,160 effective operations. Every family returned zero hits.

## Targeted slot-grammar delta

For each new row output, the audit substitutes only that value into Phase
523/524's `matrixsumlist` slot while leaving the other three slot vocabularies,
macro order, connected/spaced joins and standard newline-aware expansion
unchanged. This produces 7,039 bases per output, 14,078 unique bases total and
381,672 distinct passphrase materials. The frozen base list has SHA-256
`8b76b4c4659617fd41794121fdf55607d8cdb1912dfbac5e526bc76369b51f3f`.

CUDA was unavailable, so a CPU fallback was added to `tools/gpu_oracle`. It
globally deduplicates materials and caches each KDF result across AES key sizes
and modes. A regression test proves its cached path agrees with the existing
CPU reference for all 60 default variants. The complete run performed
91,601,280 decryptions:

```text
weak:       32
strong:      0
structural:  0
```

All 32 weak rows were rederived through `cb_common` with zero padding or score
mismatches. None contains a hex64, WIF or BIP39 key shape. Maximum weak score:
6.35167, within the expected noise tier.

The CPU run applies the standard printable and structural gates. It does not
duplicate the CUDA oracle's unconditional Bloom/known-target check on every
raw stream-mode body; therefore this result does not claim raw-binary address
coverage for the new slot delta. That separate detector does not affect the
zero strong/structural password result or the classification of all recorded
weak rows.

## Disposition

Closed negative for the declared structural family, the historical direct
cipher families, and the targeted four-slot password grammar. These parity
checks provide no reason to prefer either Selection A output and no reason to
replace the historical community construction. Reopen only for an
authenticated consumer or, for the explicitly disclosed raw-stream detector
remainder, restored CUDA access.

## Reproduction

```bash
python3 tools/gsmg/phase543_selection_a_parity_audit.py --self-test
python3 tools/gsmg/phase543_selection_a_parity_audit.py --all --write
cargo test --release cpu_oracle::tests -- --nocapture \
  --manifest-path tools/gpu_oracle/Cargo.toml
tools/gpu_oracle/target/release/gpu_oracle \
  --cpu-sweep \
  --wordlist _work/phase543/slot_bases.txt \
  --newline-variants \
  --output _work/phase543/slot_cpu.hits.jsonl
python3 tools/gsmg/phase543_selection_a_parity_audit.py \
  --all --write --slot-hits _work/phase543/slot_cpu.hits.jsonl
```
