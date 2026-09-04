# Phase 475 — dependency-aware direct DBBI/P91 audit

Date: 2026-09-03  
Outcome: `closed_negative`

## Result

The direct 91-to-91 comparison does not promote. The observed maximum English
quadgram score across the frozen six-operation family is `-610.5786026`, from
coordinate-wise `P91 + DBBI` in the Phase-386 DBBI-derived 5x5 square.
Exactly 7,887 of 100,000 dependency-aware controls reach or exceed it:

- raw tail fraction: `0.07887`;
- add-one empirical p-value: `0.0788792112`;
- frozen promotion threshold: `0.005`.

There are no hits from the frozen Phase-396 keyword list in any observed
output. No password, ciphertext-oracle, address, or private-key tests were
made.

## What was tested

The observed `P91` is reproduced exactly as Phase 386's full-block Bifid
decode at `decoded[7:98]`:

```text
DEOEMCKEADHBSCHDKBDCSDKDVBXCPCOCHCRDICIBQEEBDDBCNDSBDCPDGCPDNCNCSESCGDDCLENBMCUDUCQCACDELDZ
```

It was combined positionally with the 91-character DBBI string using exactly
six pre-frozen operations:

1. `P91-DBBI`, `P91+DBBI`, and `DBBI-P91` modulo 26;
2. the same three operations on row/column coordinates modulo 5 in the fixed
   `DBIFHCEGAKLMNOPQRSTUVWXYZ` square.

The winning observed output was:

```text
DGPANACCOCDGZEBHNIEEYIABBAHMRMPMDEYEBKAIUCKIABHCMBYHFLPBAAUCSNOATNYNPECERESFNAQFSNSNKMENTBD
```

It is not plaintext and contains no frozen target keyword.

## Why this control is stronger than Phase 401 for this question

Phase 401 permuted P91's observed letters and operated on the derived
`DBBI-M91` difference. Phase 475 instead tests P91 directly against DBBI and
regenerates every synthetic P91 upstream: each trial permutes the exact
570-letter FAED multiset, reruns the fixed full-block Bifid transform, and
only then takes positions 7 through 97. DBBI stays fixed in both of its real
roles—as square source and comparison operand.

This matters because the family is strongly asymmetric under its own null.
Coordinate-wise addition wins the six-way maximum in 86,399 of 100,000
controls. Its being the observed winner is therefore expected behavior of the
DBBI-derived square and letter distributions, not independent evidence.

## Interpretation and limits

The real result is around the 92nd percentile of this frozen family, mildly
English-like but not exceptional after the declared six-way correction. It
provides no evidence that P91 was deliberately made DBBI-sized for direct
modular or same-square coordinate arithmetic.

The result is conditional on the already-selected Phase-386 decoder and fixed
`[7:98]` boundary. It does not correct for the historical search that found
`BTCSEED`, and the unconditional FAED-permutation null does not condition
controls on also reproducing that seven-letter prefix. It also does not test
unselected row/column cross-splices. Those variants should not be added after
seeing this result without a new independent selector and a newly frozen
family-wide control.

## Verification

- The vectorized extraction matches Phase 386 byte for byte.
- Vectorized quadgram values match the frozen scalar scorer.
- Mod-26 and coordinate subtraction inverse identities pass.
- A planted English/SATOSHI positive passes through an eligible operation.
- The deterministic full run used 100,000 trials and seed `0x475`.

Artifacts:

- `tools/gsmg/phase475_dbbi_p91_dependency_aware_audit.py`
- `tools/gsmg/test_phase475_dbbi_p91_dependency_aware_audit.py`
- `tools/gsmg/phase475_result.json`
- `doc/Brainstorms/2026-09-03 - Phase 475 Dependency-Aware DBBI P91 Protocol.md`
