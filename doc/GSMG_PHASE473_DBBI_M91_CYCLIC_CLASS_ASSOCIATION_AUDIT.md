---
type: audit
phase: 473
date: 2026-09-02
status: closed
result: bounded_negative
---

# Phase 473 — DBBI/M91 Cyclic Class Association Audit

## Result

This phase tested whether DBBI has any categorical association with structural
classes of the authenticated equal-length Phase-3.2.2 plaintext under all 91
cyclic offsets. The protocol was frozen and hashed before one decision-bearing
run. No matching/mismatching letters, arithmetic stream, candidate plaintext,
password, FAED transform, decryption, or oracle input was generated.

The frozen family comprised DBBI as raw nine symbols and as `{b,e}` versus
other; plaintext as vowel/non-vowel and A0Z25 modulo 2, 3, 7, 9, and 13; and
all 91 offsets: `2 × 6 × 91 = 1,092` cells. Each cell used categorical mutual
information, standardized against 5,000 exact DBBI-multiset position shuffles.
The single statistic was the maximum standardized cell, with the complete
1,092-cell maximum recomputed for every null draw. Four fixed 91-character
controls received the identical treatment.

The real target's winning cell was:

```text
DBBI representation:  {b,e} versus other
plaintext feature:    A0Z25 mod 2
cyclic offset:         85 (equivalently -6 mod 91)
raw MI:                0.0705974 nats
cellwise z:            8.30522
raw-cell p:            0.00079984 (3/5000 null exceedances; plus-one)
global family-max p:   0.0591882  (295/5000 null-max exceedances; plus-one)
```

The local cell is superficially strong and exceeds all four controls, but it
does not survive the registered 1,092-cell search. Under the full family null,
approximately 5.9% of shuffled DBBI streams produce a maximum at least this
large. This is the exact multiplicity failure the global max statistic was
pre-registered to detect.

| Target | Maximum z | Global p | Winning family |
|---|---:|---:|---|
| Real Phase 3.2.2 plaintext | **8.305** | **0.05919** | `{b,e}` / mod2 / offset 85 |
| Control offset 0 | 5.319 | 0.51210 | `{b,e}` / mod3 / offset 82 |
| Control offset 273 | 6.787 | 0.22476 | `{b,e}` / vowel / offset 21 |
| Control offset 546 | 6.300 | 0.30514 | `{b,e}` / mod2 / offset 38 |
| Control offset 819 | 6.552 | 0.26355 | `{b,e}` / vowel / offset 75 |

Three diagnostic gates pass: the real maximum z exceeds every control, its
global p is below every control p, and the winning raw-cell p is below 0.001.
The required decision gate does not: real global `p < 0.001` is **false**.
Therefore the conjunction is false and the result is not a lead.

## Disposition

`bounded_negative`. Catalog items 191–193 and 198 are closed at the frozen
class/offset scope. The offset-85 parity cell is retained only as the winning
record of a failed family-wide screen; it must not be re-described as a clue,
candidate mapping, or selected alignment.

Phase 474 held-out validation is **not licensed** by the protocol. Running a
classifier specifically on `{b,e}`/parity/offset-85 after seeing this output
would convert a failed exploratory maximum into a post-hoc confirmatory target.
Catalog items 200–202 and `G-MSL-001` remain unchanged.

## Structural checks

- Exactly 1,092 unique family cells reproduced.
- FFT circular contingencies agree with direct contingency-table mutual
  information at two tested offsets.
- A synthetic perfect categorical dependency is recovered.
- Four Phase-473 unittests pass.

## Reproduction

```bash
cd tools/gsmg
python3 phase473_dbbi_m91_cyclic_class_association_audit.py --structural-only
python3 -m unittest test_phase473_dbbi_m91_cyclic_class_association_audit
python3 phase473_dbbi_m91_cyclic_class_association_audit.py
```

Artifacts: frozen protocol under `doc/Brainstorms/`, audit script,
`phase473_manifest.json`, `phase473_execution_lock.json`,
`phase473_result.json`, `phase473_result_record.json`, and the unittest module.

## Reopen condition

An independently selected plaintext class/offset from authenticated creator
evidence, or a genuinely new held-out object fixed before inspecting its DBBI
relationship. The observed offset-85 winner itself is not reopening evidence.
