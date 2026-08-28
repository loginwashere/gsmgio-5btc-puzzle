# Phase 433 — Phase-430 Quadgram Score Pathology Audit

## Question

Why does the best Phase-430 quadgram score improve while the decoded tail
remains unreadable? Phase 433 applies the protocol frozen before inspecting
any leader newer than the Phase-432 snapshot.

## Controls

The audit compares Phase-430 rank zero, the completed Phase-429 winner, and the
Phase-432 snapshot leader against 1,000 exact-multiset shuffles, 1,000 intact
Bifid-digraph shuffles, 10,000 uniform Phase-430 ranks, and 10,000 random
non-`G/H` assignments conditional on the candidate's exact `G/H` cells. A
pinned 563-letter slice of the existing Phase-425 report supplies an absolute
English-prose reference. Every metric excludes `BTCSEED`.

## Main comparison

| Metric | Rank zero | Phase-429 winner | Phase-432 leader | Pinned English |
|---|---:|---:|---:|---:|
| Quadgram mean | -6.9863 | -6.8126 | **-6.2636** | **-4.4620** |
| Unseen-floor fraction | 0.0089 | 0.0036 | 0 | 0 |
| Alphabet size | 25 | 25 | **16** | 24 |
| Character entropy | 3.881 | 3.881 | 3.860 | 4.141 |
| Vowel fraction | 0.229 | 0.238 | **0.323** | 0.378 |
| Index of coincidence | 0.0938 | 0.0938 | **0.0715** | 0.0673 |
| Lag-1 mutual information | 0.789 | 0.789 | **0.689** | **1.076** |
| Distinct quadgrams / 560 | 539 | 539 | **543** | 480 |
| Longest repeated substring | 5 | 5 | **5** | **10** |

The optimized leader remains `1.80157` log10 units per quadgram below the
English control, roughly a 63-fold likelihood gap on each local window. It
does eliminate unseen quadgrams and moves vowel frequency and IC toward
English, but it does so with only sixteen output letters and without acquiring
English's sequential dependence or repeated lexical structure.

## Selection controls

The Phase-432 leader beats all 10,000 sampled global ranks and all 10,000
assignments conditional on its `G/H` placement (`p=1/10001` for each). This is
not independent plaintext evidence: it is the statistic optimized over
trillions of ranks.

Against controls that retain the leader's exact letter multiset, its score has
`p=0.002997`; against intact aligned Bifid-digraph permutations it has
`p=0.009990`. The Phase-429 exact winner behaves similarly (`p=0.004995` and
`0.011988`). Rank zero is null-like under both (`p=0.322` and `0.376`). Thus
optimization finds relabelings that exploit the fixed Bifid ordering, but the
same phenomenon already occurs in the completed, unreadable Phase-429 family.

## Score decomposition

The gain is not supplied by one apparent word or repeated phrase. The leader's
ten largest repeated-quadgram contributions provide only 4.33% of its total
score above the unseen floor, less concentration than English's 7.52%. Its 543
distinct quadgrams and repeat length five show that the gain is distributed
across many locally less-impossible windows. Examples such as `ITHT`, `ORDO`,
`LORD`, and `DOIT` are isolated and do not join into prose.

The mechanism is therefore:

1. moving `G/H` changes the mechanical coordinate projection and can restrict
   which output cells are visible;
2. alphabet permutation tunes marginal letter identities and thousands-way
   local quadgram choices;
3. exhaustive maximum selection promotes the best aggregate collection of
   weak seen quadgrams;
4. this improves the declared score without creating word-scale syntax.

## Disposition

`quadgram_gain_is_selection_driven_local_relabeling_not_plaintext`.

The quadgram objective is functioning as implemented, but its absolute gap to
English and failure on broader sequential metrics show that the current gain
is not a weak readable message. Phase 433 does not invalidate the exact GPU
maximum; it constrains its interpretation. Further promotion would need a
separately selected operation or coherent held-out language, not a still
higher maximum of the same score.

## Artifacts

- frozen Phase-433 protocol in `doc/Brainstorms/`;
- `tools/gsmg/phase433_quadgram_score_pathology_audit.py`;
- `tools/gsmg/test_phase433_quadgram_score_pathology_audit.py`;
- `tools/gsmg/phase433_result.json`.
