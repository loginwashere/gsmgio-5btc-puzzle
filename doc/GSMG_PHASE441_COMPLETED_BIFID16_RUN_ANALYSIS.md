---
type: audit
phase: 441
date: 2026-08-28
status: complete
result: exact-16factorial-negative
disposition: rejected
script: tools/gsmg/phase441_completed_bifid16_run_analysis.py
---

# Phase 441 — Completed Bifid-16 Run Analysis

The `16!` search completed exactly. It did not recover coherent plaintext after
the sealed `BTCSEED` crib. The full result strengthens Phase 433's conclusion:
quadgram maximization is selecting locally favorable relabelings, not language.

## Completion and performance

| Field | Final value |
|---|---:|
| Search domain | `[0, 20,922,789,888,000)` = exact `16!` |
| Checkpoint next rank | `20,922,789,888,000` |
| Completion | 100% |
| Interrupted | no |
| GPU | NVIDIA GeForce RTX 5070 |
| Resume start | `7,960,654,774,272` |
| Candidates in final invocation | `12,962,135,113,728` |
| Final-invocation elapsed time | `30,879.58 s` = 8 h 34 m 40 s |
| Throughput | `419,763,980 candidates/s` |
| Full-domain projection at measured rate | 13 h 50 m 44 s |

The final winner lies only `81,306,767,328` ranks after the resume point,
roughly 3 minutes 14 seconds of work at the measured speed. The following
8.5 hours did not beat it; completing them is what makes the maximum exact.

The 1,000 retained rows remain block-winner samples, not an exact global top-K.
Only the first row is guaranteed to be the exact global maximum.

## Exact winner

| Field | Value |
|---|---|
| Rank | `8,041,961,541,600` |
| Square | `DBIFKCEOAMRGLHPUNSTQVWXYZ` |
| GPU total | `-3465.5264` |
| GPU mean | `-6.18843994` |
| Decode SHA-256 | `602a9a9ab1504ab4d9c6db471eb26f5502fe678d01f58423a402594819858d32` |

Exact decode:

```text
BTCSEEDDGAGEOAEAIFINOFIABDCSIARULNLARAOFCNDICIBUEEBDDBRODSBDLADOLADLROCSONCODDRCLEBGOTITCU
CACDGCLTGCREEFDFONDHRNOAGTOTGNBAONGNIGGEEDEADHBNLAIEBURAOEINLEONBRBTONDAIHITONLACNEAROOACS
CDROBEIAOACTRCBNLELECCOEGCROOTINIEONOBLEITEFDDBAOADLINDSONCNINEBBRIBENRURABDCCOEINGAGUGUCD
GELACSCOGCDIOEDARNRTCALAOELEGTEBCORCCNDBBNDODBDGENROCODTCDIGCFRCLADLBNBBEBROENENGEGCDSDADR
LECUBHOFDUDOLNOECFOTEEOBDACIEADHCTDLOBOEDEGCDEGCBGOAEDBBEARERADNGECCRECSCODBRAREDTDRBGCDBG
BGIHINDLINRTGAGACILEINGAIBCBBBROROECITCIBECCCODHREEEITIGDEGCBRBALALARERSRSDNDOCBREDLDNDDEC
RNEAIFBTDICULADHEFIFDORSIHCIGC
```

Nothing after `BTCSEED` forms a coherent sentence, key instruction, Bitcoin
object, or puzzle phrase.

## Score improvement versus language

| Profile | Quadgram mean | Alphabet | Vowels | IoC | Lag-1 MI | Longest repeat |
|---|---:|---:|---:|---:|---:|---:|
| Rank zero | -6.9863 | 25 | 0.229 | 0.0938 | 0.789 | 5 |
| Phase-429 exact winner | -6.8126 | 25 | 0.238 | 0.0938 | 0.789 | 5 |
| 38% snapshot leader | -6.2636 | 16 | 0.323 | 0.0715 | 0.689 | 5 |
| **Final exact winner** | **-6.1884** | **16** | **0.362** | **0.0769** | **0.572** | **5** |
| Pinned English | **-4.4620** | 24 | 0.378 | 0.0673 | **1.076** | **10** |

The final score improves by `42.0717` total units over the 38% leader, only
about `0.0751` per quadgram. It remains `1.72644` log10 units per window below
English—about a 53-fold likelihood deficit on every local window.

More importantly, the non-optimized sequential signal gets worse: lag-1 mutual
information falls from `0.689` to `0.572`, while English is `1.076`. The final
tail still has longest repeat five and 543 distinct quadgrams out of 560,
compared with English's longer repeated lexical structure and 480 distinct
quadgrams. Optimization improved the target statistic without building syntax.

## Frozen control results

| Null | Trials | Final winner upper-tail p | Interpretation |
|---|---:|---:|---|
| Exact letter-multiset shuffle | 1,000 | `0.00799` | Better than most arbitrary arrangements |
| Intact aligned-digraph shuffle | 1,000 | `0.09191` | Not exceptional after preserving Bifid pair structure |
| Same `G/H` cells, other letters randomized | 10,000 | `0.00019998` | One sampled equivalent/tie; optimized choice expected to lead |
| Uniform global ranks | 10,000 | `0.00009999` | Beats all samples, as expected for a `16!` maximum |

These are descriptive controls, not discovery p-values: the winner was chosen
by maximizing the same quadgram score over 20.9 trillion ranks. The particularly
important control is the intact-digraph null. Its non-exceptional `p≈0.092`
shows that much of the remaining local structure comes from the fixed Bifid
pair ordering itself.

The score gain is also diffuse. The ten largest repeated-quadgram contributions
provide only 4.60% of above-floor score. There is no one phrase or crib carrying
the improvement.

## Equivalence classes and the misleading dictionary signal

The independent CPU reviewer collapsed 1,000 retained rows to nine decodes:

```text
524, 469, 1, 1, 1, 1, 1, 1, 1
```

Thus 993/1,000 retained rows belong to only two decoded-output classes. Across
all nine decodes:

- 423/563 tail positions (75.13%) are identical;
- pairwise Hamming distances range from 14 to 140, median 51.5;
- no fixed Bitcoin/puzzle keyword occurs in any tail;
- every tail's longest repeated substring is five;
- `BRIBE` at offset 237, `BEARER` at 408, and `RARED` at 429 occur in all nine.

Those shared same-position words explain why several 200-trial dictionary
calibrations hit their minimum possible p-value. They are properties of the
shared optimized template, not nine independent English confirmations. The
within-candidate shuffle test also does not correct for choosing candidates by
quadgram score from `16!` possibilities.

## Decision

All four frozen promotion conditions fail:

- no fixed keyword outside `BTCSEED`;
- no non-template word-scale structure longer than five;
- quadgram gap to English is 1.726, not below 0.5;
- lag-1 mutual information is only 53.2% of English, not at least 90%.

Disposition:
`exact_16factorial_negative_quadgram_selection_pathology_confirmed`.

This closes the sealed Phase-430 16-factorial family under its declared Bifid
construction and quadgram objective. A new run is not warranted merely to use
another language score; reopening requires an independently selected operation,
alphabet constraint, or held-out coherent continuation.

No passwords or downstream oracle calls were generated. Phase 441 performed
CPU-only analysis and did not launch Docker or new GPU work.

## Artifacts

- frozen Phase-441 protocol in `doc/Brainstorms/`;
- `tools/gsmg/phase432_final_review.json`;
- `tools/gsmg/phase441_completed_bifid16_run_analysis.py`;
- `tools/gsmg/test_phase441_completed_bifid16_run_analysis.py`;
- `tools/gsmg/phase441_result.json`.
