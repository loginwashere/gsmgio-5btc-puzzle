---
type: audit
phase: 472
date: 2026-09-02
status: closed
result: bounded_negative
---

# Phase 472 — DBBI Route-Aware Plaintext Alignment Audit

## Result

This phase executed item 8 of the 2026-09-02 DBBI experimental catalog:
whether one of Phase 471's 19,686 canonical DBBI readings aligns unusually
well with the authenticated, equal-length Phase 3.2.2 plaintext. The protocol
was frozen and hashed before one decision-bearing run. No derived text,
password material, hash candidate, decryption, FAED transform, or oracle input
was generated or inspected.

For each target, the statistic maximized exact mod-9 position matches over all
19,686 routes and four frozen numeric conventions (`a0i8`/reversed DBBI
against A0Z25/A1Z26 mod 9): 78,744 route/mapping combinations. Calibration
used 2,000 position shuffles preserving each target's exact residue multiset;
the complete family maximum was recomputed inside every null draw. Four fixed,
non-overlapping 91-character corpus windows received the identical analysis.

The real plaintext reached **25/91** matches. Its null maxima average 25.549
(SD 1.072, range 23–30), giving upper-tail plus-one
`p = 0.8640679660`. It is therefore slightly *below* an ordinary family
maximum, not an exceptional alignment. A fixed control at offset 546 reached
27/91 (`p = 0.1239380310`).

| Target | Max matches | Null mean ± SD | Upper-tail p |
|---|---:|---:|---:|
| Real Phase 3.2.2 plaintext | 25 | 25.549 ± 1.072 | **0.864068** |
| Control offset 0 | 24 | 24.064 ± 1.049 | 0.687156 |
| Control offset 273 | 25 | 24.969 ± 1.075 | 0.640680 |
| Control offset 546 | 27 | 25.257 ± 1.088 | 0.123938 |
| Control offset 819 | 24 | 24.800 ± 1.068 | 0.924038 |

All three frozen promotion gates fail:

- real `p < 0.001`: **false**;
- real maximum strictly above every control: **false**;
- real p strictly below every control p: **false**.

The winning real record was a `13x7` toroidal reading (start `(2,2)`, step
`(4,3)`) under DBBI `a0i8` versus plaintext A0Z25 mod 9, but it carries no
interpretive status: the family-max null shows that a record at least this
good occurs in roughly 86% of shuffled targets.

## Structural checks

- The globally deduplicated registry reproduced exactly 19,686 permutations.
- Registry SHA-256:
  `6efd826575b64e533275db3aa5151d2557edbdaaed5f6af1463c5194c16c63e6`.
- Four unittests pass, including route uniqueness, fixed-target provenance,
  and a synthetic perfect-alignment recovery control.
- Exactly one locked result run was made after protocol/script hashing.

## Disposition

`bounded_negative`. The equal 91-character lengths do not support a positional
DBBI/Phase-3.2.2 relationship anywhere in the complete Phase-471 route family
under the four frozen mod-9 conventions. This closes catalog item 8 at the
registered scope. It does not prove that no other operator could relate the
objects, but expanding maps or scoring functions after this result would be a
new, unsupported family.

Catalog item 9 (first-occurrence permutation schedules) remains separately
testable. Item 10 (oracle feeding) remains unlicensed. `G-MSL-001` is unchanged.

## Reproduction

```bash
cd tools/gsmg
python3 phase472_dbbi_route_plaintext_alignment_audit.py --structural-only
python3 -m unittest test_phase472_dbbi_route_plaintext_alignment_audit
python3 phase472_dbbi_route_plaintext_alignment_audit.py
```

Artifacts: frozen protocol under `doc/Brainstorms/`,
`phase472_dbbi_route_plaintext_alignment_audit.py`, `phase472_manifest.json`,
`phase472_execution_lock.json`, `phase472_result.json`,
`phase472_result_record.json`, and the unittest module.

## Reopen condition

Authenticated creator evidence selecting a new mapping/operator or a specific
route before output inspection. Equal length, a new unsourced scoring function,
or a visually attractive near-winner is insufficient.
