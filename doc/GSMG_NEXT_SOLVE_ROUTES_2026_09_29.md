# Next solve routes — 2026-09-29

The best next attempt is a small, source-derived transposition key experiment. Several large searches are bounded negatives, but they do not justify the stronger conclusions that FAED cannot encode English, that DBBI cannot supply a key, or that every transposition route has been tried. This review found specific coverage gaps and executed one inexpensive new exact-source test. No puzzle solution, password, or private key was recovered.

## Findings that change the search

**FAED's object type is unresolved.** [Phase 549](../tools/gsmg/findings/P00549.md) rejects seven declared generators largely through adjacency statistics. A later digit transposition removes that adjacency. [Phase 550](../tools/gsmg/findings/P00550.md) cannot close this gap: freely fitted boards match the counts closely, and its controls have little power against other skewed generators. “Fits a memoryless reference” does not identify a key, random payload, or cipher. Conversely, compatibility with an English checkerboard does not identify English.

**A parameter relationship need not produce positional correspondence.** [Phase 518](../tools/gsmg/findings/P00518.md) compares modes in proportional blocks. Its negative concerns that statistic. DBBI could supply a column order, board, seed, or other parameter without its symbols aligning with FAED's symbols. The statement that only independent generators remain uncontradicted is too strong if applied beyond the declared alignment model. This is a reason to test an explicit construction, not evidence that such a construction is intended.

**Prime length does not forbid columnar transposition.** [Phase 520](../tools/gsmg/findings/P00520.md) excludes a filled rectangular grid for the 661-symbol splice, then tests a no-transposition splice. A ragged rectangle remains possible. The existing `cb_common.keyed_columnar` exactly round-tripped all 661 symbols at width 13, leaving an 11-symbol partial row. That is a mathematical counterexample to a blanket prime-length exclusion, not support for joining DBBI and FAED. The joint-splice route remains relatively weak given the independent-profile evidence and lack of a selected combining rule.

**Validity before reordering cannot select the escape pairs after reordering.** A digit transposition can change which symbols begin two-symbol codes. For a raw-symbol experiment, test all 36 pairs *after* undoing the proposed ordering, or filter them with a proved count constraint. The old deferred diagonal-key proposal's 29-pair filter is inappropriate if inherited from native-order segmentation. This differs from an independently selected pair or a pair restriction explicitly stated as a limited experimental scope.

## A new source-first test, executed

[Phase 482](../tools/gsmg/findings/P00482.md) searched exact **25-token** frequency signatures after segmenting FAED into 436 tokens. It tests token-preserving transposition. It explicitly leaves raw-digit transposition open. [Phase 550](../tools/gsmg/findings/P00550.md) compares corpus-average frequencies with fitted boards; it does not ask whether a particular source passage can produce the exact nine observed counts.

An exact source passage offers stronger integer constraints. Assume a nine-symbol checkerboard with seven single-letter cells and two nine-cell escape rows, letters-only text, `J → I`, no padding/nulls, and an arbitrary permutation of the encoded digits. Let:

- `M = 570`: FAED's raw length;
- `N`: candidate plaintext length;
- `D = M − N`: occurrences encoded with two digits;
- `S = 2N − M`: occurrences encoded with one digit;
- `E`: the combined observed counts of a proposed escape pair.

Necessarily `D ≤ E ≤ 2D`. Exactly seven board letters must have occurrence counts summing to `S`. The four cells whose codes both start and end in an escape symbol must have occurrence counts summing to `E − D`. These constraints survive **any** digit permutation; they do not depend on native-order segmentation or English scoring. The subset-sum principle already appears in recovery calibration; its application here is an exact whole-source test under raw-digit transposition.

FAED's counts are:

```text
a54 b49 c52 d49 e69 f57 g107 h58 i75
```

Across all 36 pairs, its whole plaintext must contain **388–521 letters** under this model. Conditional pair bounds are:

| Pair | Possible whole-plaintext length |
| --- | ---: |
| `g,i` | 388–479 |
| `h,e` | 443–506 |
| `b,e` | 452–511 |

The pilot freshly reproduced the native 1,539-letter Architect answer, without using README spaces. Its original SHA-256 is `56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241`. `SELECT` occurs once, at zero-based letter offset 1143. The two exploratory source anchors were the end immediately before `SELECT`, and the native speech end. Neither is asserted to be the creator-selected interpretation of `lastwordsbeforearchichoice`.

Of 268 suffixes of lengths 388–521 ending at those anchors, **31** pass the seven-single-letter subset constraint, leaving **51** suffix/pair cases. These were enumerated before inspecting transposition results.

One particularly concrete candidate, the complete `SELECT`-to-end instruction tail, has 396 letters. It requires 222 single-code occurrences and 174 double-code occurrences. Its only possible escape pair is `g,i`: the competing count-eligible `e,g` pair would require four distinct letters totaling two occurrences, which the source histogram cannot supply. An exact count-assignment solver found a full legal board matching FAED's nine counts under `g,i`. This is **feasibility**, not a recognition or a decode: many arrangements can share counts.

The candidate was then tested for the actual ordering. The existing exact crib CSP completed all four possible seven-single-letter sets at rectangular widths `2,3,5,6,10,15,19,30,38`, with no match. Planted full-passage controls using a count-compatible board recovered and round-tripped at every width. The same exact CSP then checked all 31 previously enumerated suffixes, their count-eligible pairs, and those widths: **2,655 cells, zero hits, zero node-limited cells**. Every real cell rejected at its initial column check.

This closes that exploratory suffix/source/normalization/single-columnar family. It does not cover ragged widths, larger widths, double/disrupted transposition, different source passages, different alphabet conventions, or newly composed text. A count match alone should never be promoted.

Reproduction and complete results:

- [Count feasibility probe](../_work/next_routes_review_2026_09_29/exact_count_probe.py) and [exact SELECT-tail counts](../_work/next_routes_review_2026_09_29/exact_select_tail_counts.json).
- [Initial suffix count inventory](../_work/next_routes_review_2026_09_29/source_count_necessary_conditions.json).
- [Whole-tail columnar probe](../_work/next_routes_review_2026_09_29/select_tail_columnar_probe.py) and [result](../_work/next_routes_review_2026_09_29/select_tail_columnar_result.json).
- [Count-filtered suffix columnar probe](../_work/next_routes_review_2026_09_29/suffix_columnar_probe.py) and [complete result](../_work/next_routes_review_2026_09_29/suffix_columnar_result.json).

## Ranked routes still worth attempting

| Rank | Concrete route | Why it differs from completed work | Next check and success condition |
| --- | --- | --- | --- |
| 1 | **DBBI diagonal sums order FAED's 19 columns.** A 7×13 DBBI rectangle has 19 diagonals; FAED is 19×30. | [Phase 517](../tools/gsmg/findings/P00517.md) explicitly deferred this route. [Phase 514](../tools/gsmg/findings/P00514.md) tried literal keyword orders; [Phase 538](../tools/gsmg/findings/P00538.md) tried host-mask extraction. Neither tests these sum-derived keys. | Repair and execute the already-defined small family: both DBBI orientations, both diagonal directions, `a0i8`/`a1i9`, rank direction, tie convention, and transform direction. Deduplicate keys; check all 36 post-reordering pairs. Test board recovery on planted examples first. A whole coherent instruction with independent validation, an exact downstream decryption, or a known-address match would advance it. |
| 2 | **DBBI supplies two transposition keys: its row sums and column sums.** Undo two raw-digit columnar stages of widths 7 and 13 on FAED. | The inspected findings catalogue double/disrupted transposition as outside their tested families. This uses two native sum lists and a finite key grammar rather than arbitrary pairs of keywords. FAED need not be divisible by 7 or 13: these stages are ragged. | Freeze the two list orders, ties, stage order and inverse conventions. Verify encryption/decryption against planted two-stage examples, then fit the board only after both inverses. Do not vary dates, personal numbers, or arbitrary keywords. It is an exploratory hypothesis with weaker selection evidence than Rank 1. |
| 3 | **DBBI width 13, with an exact-format or exact-source solver.** | [Phase 516](../tools/gsmg/findings/P00516.md) exhausts width 7 and explicitly leaves width 13 open. Its 13! brute-force estimate is a cost of that architecture, not a proof of intractability. | Use the existing CSP architecture with only source-authenticated long cribs or a fixed output grammar. First demonstrate recovery on 48–69-letter, 91-digit plants, including wrong-source controls. An exact source/order match is preferable to a best English score at this short length. The expected instruction/format is currently missing, so do not invent one to make the solver run. |
| 4 | **Source identity before cipher order, using exact raw-count constraints.** | Phase 482's token signature and Phase 550's corpus-average fit leave this problem open. The pilot above demonstrates a cheap rejection path and narrows board-length patterns enough for an exact CSP. | Extend only to separately named source boundaries, such as the actual film/screenplay choice boundary, with provenance and normalization fixed before checking. Require a full board/order reproduction. Do not rescan the tested modified-speech suffixes or interpret a histogram witness as plaintext. |
| 5 | **Native source-range inventory at solved boundaries.** | [Phase 548](GSMG_PHASE548_FAED_DISTRIBUTION_BOUNDARY.md) recommends it, but no completed comprehensive bit/byte consumption ledger was located in the inspected records. This is different from listing unresolved claims. | Record exactly which authored ranges fed each solved transition and which ranges have no demonstrated consumer. Give priority to residual instructions adjacent to the actual input of an unresolved step. Exclude screenshots, community whitespace, and generated derivatives from native bytes. A useful result must connect a residual to another artifact through an explicit operation; a leftover by itself is not a clue. |

The two-stage route is motivated by a real distinction: historical VIC combines a checkerboard with modified double transposition, while a checkerboard-only or single-columnar test covers less. The [American Cryptogram Association's course](https://www.cryptogram.org/downloads/LANAKI%20Crypto%20Lessons/LESSON6.pdf) describes that construction. This does **not** establish historical VIC as the GSMG generator; the observed nine-symbol board is already a model adaptation, and the full historical key derivation has no selected puzzle parameters.

## Repair the deferred protocol before running it

The Rank-1 [original proposal](Brainstorms/2026-09-17%20-%20Closed-System%20Untried%20Theory%20Classes.md) names 64 key cells × 29 native-valid pairs and 100 shuffled controls at `p ≤ 0.005`. Two repairs are necessary:

1. Test all 36 pairs after inverse transposition, rather than prefiltering from the observed order. The nominal pre-deduplication count becomes 64×36 = **2,304** cells.
2. With an add-one Monte Carlo p-value, 100 controls have minimum p `1/101 ≈ 0.0099`; the stated 0.005 gate is unattainable. At least 199 controls are needed merely to reach 0.005, and 999 give a more useful grid. Calibrate the maximum over the same full family if promoting a statistical result. A screen with no readable or exact match can stop as a bounded no-solve without claiming a calibrated exclusion.

The hypothesis that DBBI supplies these keys remains unproven. Its structural motivation is the adjacent `matrixsumlist` token and the 19-diagonal/19-column correspondence. Phase 518's alignment negative neither selects nor rejects it.

## Recommended sequence

Execute Rank 1 after those two repairs. If it returns no complete instruction or exact consumer hit, stop that fixed family. Then investigate Rank 2 as a separate, explicitly exploratory construction, or Rank 4 if an independently grounded source boundary can be named. Keep Rank 3 behind an actual output grammar. The native consumption inventory can proceed alongside these choices without treating it as another solve result.

The main methodological change is to recover **relations and source identity** using exact structural constraints where possible, rather than using another marginal-frequency statistic or an attractive word fragment to decide what the puzzle means. An exploratory construction need not await a new creator message, but it must be reported as exploratory until it makes an independent exact prediction.
