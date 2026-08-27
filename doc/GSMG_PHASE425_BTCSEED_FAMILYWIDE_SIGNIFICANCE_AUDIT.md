# GSMG Phase 425 — BTCSEED Family-Wide Significance Audit

## Result

**Outcome:** `family_corrected_positive_checkpoint_only`

Phase 386's exact `BTCSEED` prefix survives correction across the frozen,
page-local Bifid family. The real FAED stream reaches all seven target letters.
None of 10,000 exact-multiset FAED shuffles reaches seven; the strongest null
reaches six. The add-one empirical family-wise tail estimate is
`1/10001 = 0.00009999`.

This upgrades `BTCSEED` as a reproducible Bifid checkpoint within the declared
family. It does **not** establish that the remaining 563 characters are
plaintext, identify the intended FAED decoder, or promote `KMODEST`, a
password, or any Bitcoin/AES consumer.

## Frozen family

The pre-registration was written before the implementation or output was
inspected. It admitted ten literal page-local keyword sources, each under a
first-13 and full-source scope. Deduplication produced 12 distinct keyed
squares. Each square was evaluated under:

- eight Phase-408 block schedules;
- decrypt and the proven encryption inverse;
- row-column and column-row coordinate-stream conventions;
- forward and reversed ciphertext orientation; and
- forward and reversed decoded-output orientation.

That is `12 x 8 x 2 x 2 x 2 x 2 = 1,536` labeled configurations. They produced
1,248 distinct complete outputs on real FAED. The family includes the original
Phase-386 configuration and reproduces its output byte-for-byte.

The eligible keyword sources were `DBBI`, `FAED`, `matrixsumlist`,
`lastwordsbeforearchichoice`, `thispassword`, `enter`, both literal SHA rails,
`SalPhaseIon`, and `Cosmic Duality`. Output-derived words and arbitrary square
permutations were excluded. Phase 3.2.2's validation answer was excluded as
non-local and already tested separately in Phase 419.

## Observed result

Exactly one distinct output starts with or contains `BTCSEED`:

```text
BTCSEEDDEOEMCKEADHBSCHDKBDCSDKDV...
```

Its SHA-256 is
`0c5d984f90e9baefc09f1d3888e62acbd101f9b0194887e2ae88fc6c9967745e`.
It is represented by two symmetry-equivalent labels:

- `square_00/period_570/decrypt/rc/forward/forward`;
- `square_00/period_570/decrypt/cr/reverse/reverse`.

`square_00` is the DBBI-derived keyed alphabet
`DBIFHCEGAKLMNOPQRSTUVWXYZ`. No other distinct output contains the target.

## Matched control

Every null trial shuffled the exact 570-letter FAED multiset, then applied the
complete 1,536-configuration family and retained its maximum leading match to
`BTCSEED`.

| Family-maximum prefix length | Null trials |
|---:|---:|
| 1 | 3,737 |
| 2 | 5,065 |
| 3 | 1,156 |
| 4 | 37 |
| 5 | 4 |
| 6 | 1 |
| 7 | 0 |

The primary observed statistic is seven. Therefore the registered add-one
estimate is `(0+1)/(10000+1) = 0.00009999`, passing the `p <= 0.01` positive
gate. A planted `BTCSEED` plaintext round-trips through the same primitives and
is recovered with prefix length seven.

## Interpretation

The result rejects the narrow explanation that the exact prefix is ordinary
under FAED's letter multiset once the declared page-local Bifid choices are
made. It is materially stronger than Phase 386's single-configuration
empirical-letter estimate and complements Phase 408's finding that only the
full-block convention preserves the prefix.

Three limits remain important:

1. The target was historically noticed after multiple techniques were tried.
   This audit corrects the frozen Bifid family, not every unrecorded historical
   cipher experiment.
2. Period 570 remains the only successful block schedule. The checkpoint is
   still full-block-convention-dependent.
3. Phase 386 found the continuation's dictionary-word density null-like, and
   Phases 397–407 found no downstream consumer. A seven-letter checkpoint alone
   is not an end-to-end decode.

The appropriate next experiment is the separately frozen held-out continuation
test: leave the decoder and `BTCSEED` untouched, and ask whether positions
7 onward contain independently measurable structure without tuning parameters
against that continuation.

## Verification and artifacts

- 12 distinct squares, 1,536 configurations, 1,248 distinct real outputs;
- all square/schedule/coordinate-order decrypt-encrypt round trips pass;
- accelerated first/last-boundary calculations match full transforms;
- Phase 386 output reproduced byte-for-byte;
- three focused unit tests pass;
- zero oracle calls.

Artifacts:

- `tools/gsmg/phase425_btcseed_familywide_significance_audit.py`
- `tools/gsmg/test_phase425_btcseed_familywide_significance_audit.py`
- `tools/gsmg/phase425_result.json`
- `doc/Brainstorms/2026-08-27 - Phase 425 BTCSEED Family-Wide Significance Audit Pre-Registration.md`
