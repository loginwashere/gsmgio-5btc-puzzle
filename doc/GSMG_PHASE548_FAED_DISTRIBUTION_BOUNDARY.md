---
type: audit
phase: 548
date: 2026-09-29
status: complete
result: bounded-negative
script: tools/gsmg/phase548_faed_distribution_boundary.py
---

# Phase 548 — FAED distribution boundary pilot

No supported cut or layout was identified. The maximum over 42 distinct
partitions has exact-multiset Monte Carlo p = **0.027**, above the frozen
0.01 bar. This is a bounded negative, not evidence that FAED is random or
that every kind of internal boundary is absent.

The [protocol](Brainstorms/2026-09-29%20-%20Phase%20548%20FAED%20Distribution%20Boundary%20Protocol.md)
was written before real scoring. It executes the distribution-change question
in Path 2 of the September 24 microstep brainstorm. Cuts come from factors
of 570 and their complements, plus DBBI's 91 and its complement, with at
least 30 symbols per side. Row/column homogeneity tests cover all exact
nontrivial rectangular factorizations. Duplicate partitions are removed.

Each partition uses a nine-symbol count table and a standardized Pearson
statistic. The standardized score has no assumed normal or chi-square
sampling law; sparse-layout effects are handled by recomputing the entire
family on every multiset shuffle. The gate is on the family maximum, not a
single convenient cut.

## Controls and result

Optimized count statistics agreed with an independent direct implementation
on synthetic input, and symbol relabeling preserved every score. Ten balanced
two-regime plants were tested at each distribution difference, with 199 own
multiset nulls per plant and the same family-wide 0.01 bar:

| Total-variation difference between regimes | Detections / 10 |
|---|---:|
| 0.05 | 1 |
| 0.10 | 7 |
| 0.15 | 10 |
| 0.20 | 10 |

The strongest-effect control passed the required 9/10 threshold. The smallest
tested effect achieving 9/10 was 0.15. Ten trials per effect are a pilot,
not a precise power estimate. These controls cover balanced changes in two
symbol probabilities, not arbitrary change sizes, locations or mechanisms.

The execution lock was written after controls, before scoring FAED, and
verified by the run. Its SHA-256 is
`200a947fb8f65292543f434507e3cb6861a388e2f85dd456ea952a826436df8c`.

The real run used 1,999 shuffles with seed 54801. Best descriptive partition
was cut 540 (last 30 symbols), score 4.0082394712. **53 of 1,999** null family
maxima were at least as large, yielding `(1+53)/2000 = 0.027`. It is not a
selected boundary. The 19×30 row partition was also tested within this same
family; its score was 2.9023260873 and cannot be promoted separately.

All partition scores and null maxima are retained in
`tools/gsmg/phase548_boundary_result.json`; controls and hashes are in
`tools/gsmg/phase548_boundary_lock.json`. No cuts, scoring functions or
thresholds were added after inspection.

## What this changes

No evidence within this test supports cutting FAED to rescue an unreadable
Bifid tail. The test does not cover changes that preserve symbol frequencies,
transition changes, every possible cut, or a short embedded message. It does
not establish a cipher, plaintext or password.

The completed Phase 547 census is also negative within its declared models.
Together these results favor returning to source construction and missing
operands rather than widening these decoder families.

## Companion source audit: ANTIYBCORETNT

The September 28 review's exact extraction was checked again against a freshly
reproduced Phase 3.2.1 answer via the existing EBCDIC/Beaufort pipeline.
The native answer is **1,539 uppercase letters, with no spaces and no literal
CHOICE; SELECT occurs once**. SHA-256:
`56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241`.
It agrees exactly with the README display after removing nonletters.

Thus `ANTIYBCORETNT` reproduces under the README's word segmentation and
the proposed SELECT boundary. Word segmentation and treating SELECT as the
Architect-choice boundary remain construction assumptions. These observations
do not invalidate ordinary word recovery from unspaced text, but the assumed
word boundaries should not be mistaken for authenticated source bytes.
The proposed meanings of ANTI/YB/CORE, handling of TNT, downstream operation
and independent output check remain unfixed. No continuation or statistical
significance is claimed. Details are retained in
`_work/telegram_2026_09_28/anti_source_audit.json`.

## Next research direction

Audit unconsumed native information at solved boundaries (Path 4 of the
September 24 brainstorm). Build a compact ledger of actual source ranges,
their demonstrated consumers and unused complements, without treating
community-added whitespace or generated transforms as native information.
Promote a construction only when it accounts for a whole object and predicts
an independent existing artifact or exact target. This is a research method,
not an assertion that a winning construction has already been identified.

The AES portion of Path 1's authoring-fingerprint idea substantially overlaps
the already-completed Phase 410: three exact ciphertext round-trips and 24
representation/KDF controls established lowercase SHA-256 hex passwords with
legacy SHA-256 EVP and AES-256-CBC. Repeating that inventory is not a new lead.

## Reproduction

```bash
# Original preparation, performed once before scoring:
python3 tools/gsmg/phase548_faed_distribution_boundary.py prepare
python3 tools/gsmg/phase548_faed_distribution_boundary.py run
```

The CLI refuses to overwrite existing lock/result files. Existing artifacts
retain the completed run; any reproduction should use a separate checkout.
