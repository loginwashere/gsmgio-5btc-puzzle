# Phase 534 — DBBI prime-scaffold conditional diagnostic

2026-09-20. Exploratory structural diagnostic; no puzzle solution.

## Finding

The `{b,e}` checkerboard preference is not strong independent evidence once
DBBI's known structure is retained in the comparison. Its exact rank remains
correct; its interpretation needs more care.

In both complete prime-host parses, **23 of DBBI's 25 `b` symbols are hosts**.
The 83-token parse additionally puts eight `e` symbols in hosts; the 84-token
parse puts seven there. Thus the unusual raw histogram and the prime-host
pattern are overlapping observations, not independent corroboration of a
checkerboard cipher.

The real `{b,e}` segmentation has 63 tokens, 19 types, and IC
`0.0670762928827445`, very close to the historical English reference `0.067`.
We kept each prime host at its exact logical position, including its `b`/`be`
choice, shuffled only non-host symbols, and reassembled the raw stream. Every
control preserves all raw symbol counts and the designated grammatical parse.

| Controls, 10,000 each | `{b,e}` uniquely first | Valid `{b,e}` segmentations | Fixed-pair distance tail* | Best-of-36 distance tail* |
|---|---:|---:|---:|---:|
| 83-token scaffold | 1,795 | 8,380 | 66/10001 = 0.00660 | 549/10001 = 0.05489 |
| 84-token scaffold | 1,824 | 9,663 | 70/10001 = 0.00700 | 654/10001 = 0.06539 |
| Unrestricted raw histogram shuffle | 2,561 | 6,773 | 43/10001 = 0.00430 | 177/10001 = 0.01770 |

*Add-one tails, including invalid pair segmentations as failures. A tail
counts controls whose distance to 0.067 is no greater than the real distance.
The best-of-36 comparison reflects the historical search over escape pairs;
the fixed-pair column must not replace it after observing `{b,e}` as winner.
The comparison conditions on already-observed structure and is not an
unconditional discovery p-value. No claim of formal equivalence is made.

The average valid `{b,e}` IC under the two scaffold controls is `0.06809` and
`0.06482`. Non-cipher constructions retaining the known scaffold naturally
produce the purported English-like statistic. Even unrestricted histogram
shuffles often rank `{b,e}` first. Ranking first is therefore a weak discriminator
between these explanations.

## Consequence

Keep checkerboard as a hypothesis; stop treating its fitted pair as a known
decoder component that must have a mirrored partner in FAED. In particular,
reconciling `{b,e}` → `{h,e}` with FAED's `{g,i}` is not established as a
required puzzle step. The Architect's separate `BUT/HYE` observation survives
this diagnostic; Phase 534 does not test or refute it. Binding those letters to
FAED as an escape pair still depends on an unproved interpretation.
FAED's own statistics and all earlier bounded decoder failures remain intact.

The diagnostic does not establish that the prime grammar is creator-intended,
that its residue is plaintext, or that DBBI is not a checkerboard. It identifies
confounding and a more appropriate baseline for future model comparisons.

## Verification and reproduction

The protocol was written before the diagnostic run. All 36 segmentations and
IC values were cross-checked against the existing checkerboard implementation
on DBBI and generated fixtures. Both parses reproduce DBBI exactly; all 30,000
controls are included; the two scaffold generators check host and histogram
invariants on every draw. A literal toy prime scaffold verifies that the
grammar can exist without a checkerboard construction.

```bash
python3 tools/gsmg/phase534_dbbi_prime_scaffold_diagnostic.py --self-test
python3 tools/gsmg/phase534_dbbi_prime_scaffold_diagnostic.py \
  --output tools/gsmg/phase534_dbbi_prime_scaffold_result.json
```

The result records script/protocol/input hashes, seeds, counts, and zero oracle
calls. No password candidates or FAED transformations were produced.

## Review qualification

The 0.055–0.065 conditional tails leave residual uncertainty; this diagnostic
does not prove all checkerboard signal is explained. A separate scaffold-rarity
check, independently reproduced during review with seed 20260920, found zero
complete prime-host parses in 300,000 exact-histogram shuffles. Its reproducible
addendum is `phase534_scaffold_rarity_addendum.py`. This tests a different null
from the original diagnostic. The fixed grammar is unusual under that null,
with a zero-hit one-sided 95% binomial upper bound about 0.000009986. The
historical grammar-discovery search is not corrected, so this is not proof of
creator intent. Replaying the review seed is verification, not a fresh replicate.
