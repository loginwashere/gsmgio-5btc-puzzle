---
type: worksheet
status: live
date: 2026-08-25
topics:
  - brainstorm
  - dbbi
  - faed
  - theory-registry
  - generative-model
  - diagnostic
---

# Phase 413 — I0 vs S0 Signal Localization Pre-Registration

> [!caution] Prepared before computing any diagnostic score
> This is a **diagnostic audit of an already-executed result**
> ([Phase 412](../../tools/gsmg/FINDINGS.md#phase-412), topology
> contrast: `0.0566564`, `p_family=0.000599994`), not a new cipher
> search. It localizes and stress-tests that one result. No new model,
> transform, decode, or oracle is introduced.

## Scope and motivation

Phase 412 found that `I0` (independent per-stream IID) beats `S0`
(shared IID) on held-out predictive loss, significant after correction.
That result says *the two streams have different letter frequencies*
but says nothing about **where** the difference lives — one dominant
letter, one dominant fold, or a genuinely distributed effect. This
phase answers that localization question and nothing else.

**Exclusions (unchanged from Phase 412):** no decoding, keyword search,
dictionary/quadgram scoring, cryptographic oracle, or new
DBBI/FAED combinator. No promotion of any output here into a password
or key candidate.

## Frozen data

Identical to Phase 412: `DBBI` (91 chars), `FAED` (570 chars),
alphabet `a`-`i`, from `tools/gsmg/data.py`. Same five frozen folds:
`DBBI_FOLDS = ((0,19),(19,37),(37,55),(55,73),(73,91))`,
`FAED_FOLDS = ((0,114),(114,228),(228,342),(342,456),(456,570))`.

Diagnostics 1, 2, and 5 reuse Phase 412's `score_models_batch` /
`stream_fold_statistics` / `kt_unigram` (KT alpha `0.5`, K=9)
unmodified. Diagnostic 3 uses a modified, K=8 conditional refit (see
below) — it does not reuse Phase 412's fold-fit code unmodified.

## Diagnostic 1 — letter / stream / fold decomposition

**What is decomposed:** in the real data, `S0` is the winning shared
model (`macro_loss(S0)=3.150641 < macro_loss(S1)=3.184055`) and `I0`
is the winning independent model (`macro_loss(I0)=3.093984 <
macro_loss(I1)=3.100467`), so the observed topology contrast
`0.0566564` equals exactly `macro_loss(S0) - macro_loss(I0)`. This
identity is asserted in code before decomposing, not assumed — if a
future rerun ever changes which model wins each side, the decomposition
target is undefined and the script must stop rather than silently
decompose a different quantity.

**Cell formula.** For stream `s` (`DBBI` or `FAED`), fold `k`, letter
`c`, each cell is a **macro-loss contribution** — already weighted into
the same units as `macro_loss(model)` itself, not a raw bit count:

```text
cell(s, k, c) = weight(s) * held_count[s,k,c] * log2(P_I0[s,k,c] / P_S0[k,c])
weight(DBBI) = 0.5 / 91
weight(FAED) = 0.5 / 570
```

`held_count[s,k,c]` is the number of times letter `c` occurs in stream
`s`'s held-out block for fold `k` (from Phase 412's own
`stream_fold_statistics`). `P_I0[s,k,c]` is the fold-`k` independent
unigram fit for stream `s`; `P_S0[k,c]` is the fold-`k` shared unigram
fit (pooled DBBI+FAED training counts) — both already computed inside
`score_models_batch`. Positive `cell` values mean `I0` is cheaper than
`S0` at that cell (favors independent); this sign convention matches
the topology contrast's own "positive favors independent."

**Reconciliation invariant (hard assertion, not a report field):**
`sum over all (s,k,c) of cell(s,k,c) == 0.0566564` to floating-point
tolerance. If this fails, the implementation has a bug and must stop.
This is an exact algebraic identity on the real data, not a synthetic
fixture.

**Reported aggregates (purely descriptive, no p-values — this is a
decomposition of an already-significant result, not a new test):**

- By letter: 9 values `C_c = sum over s,k of cell(s,k,c)`, each in
  macro-loss units and as percent of the total `0.0566564`.
- By stream: 2 values (`sum over k,c` for each `s`).
- By fold: 5 values `F_k = sum over s,c of cell(s,k,c)` for each `k` —
  this is also Diagnostic 5's raw input (see below).

**Concentration metric (reported, not a branch-decision gate):** using
only positive contributions,

```text
letter_concentration = max(max(C_c, 0) for c in 0..8) / sum(max(C_c, 0) for c in 0..8)
fold_concentration    = max(max(F_k, 0) for k in 0..4) / sum(max(F_k, 0) for k in 0..4)
```

Both ratios are reported (which letter/fold is the top positive
contributor, and its share of total positive mass) as narrative
context for the write-up. Neither has a frozen promotion threshold —
the distributed/localized/mixed classification below is driven
entirely by Diagnostics 3 and 5's exact counts, not by these ratios,
to avoid introducing an unfrozen numeric cutoff.

## Diagnostic 2 — pooled-label permutation test (same-data corroboration)

This is a **deliberately different, simpler statistic** from Phase
412's cross-validated contrast — permutation validity comes from label
exchangeability under the null, not from a held-out split, so no
train/test partition or fold structure is used here at all. Because it
runs on the same 661 characters Phase 412 and this phase's other
diagnostics already use, its result is reported as **same-data
corroboration of Diagnostic 1's separation, not as independent
confirmation** — an independent discriminator would need data this
project does not have (see Phase 412's own held-out-vs-historically-
blind caveat, which applies here too).

**Statistic (in-sample, full-data, no CV):** for any assignment of the
661 pooled real characters into a group `A` of size 91 and a group `B`
of size 570,

```text
P_A      = KT-smoothed unigram (alpha=0.5) fit on group A's letters, full data, no folds
P_B      = KT-smoothed unigram fit on group B's letters
P_pooled = KT-smoothed unigram fit on all 661 letters together
stat(A,B) = sum_{x in pooled}(-log2 P_pooled[x]) - [sum_{x in A}(-log2 P_A[x]) + sum_{x in B}(-log2 P_B[x])]
```

`stat` is the codelength saved by splitting into two groups instead of
one pooled model — non-negative in the noiseless-fit case, always
computed the same way for observed and permuted assignments.

**Observed statistic:** `A` = the real 91 DBBI characters, `B` = the
real 570 FAED characters (as an unordered multiset — position within
the stream is irrelevant to this statistic).

**Null generation:** 100,000 trials. Each trial calls
`rng.choice(661, size=91, replace=False)` (frozen call, exactly this
form — no equivalent-shuffle substitute) to select the 91 pooled
positions assigned to `A`; the remaining 570 form `B`. Seed `0x413A0`
(`numpy.random.default_rng`).

**p-value:** one-sided upper tail, same add-one form as Phase 412:
`p_raw = (1 + count(null_stat >= observed_stat)) / 100001`. This is
one test (no family), so `p_family = p_raw`; promotion threshold
`p_raw <= 0.005` for consistency with the project's standing bound.

**Required fixtures (two, both must pass before the real result is
trusted):**

- *Positive fixture:* group A drawn from
  `[.03,.28,.08,.04,.22,.10,.10,.09,.06]` (Phase 412's
  `INDEPENDENT_IID_DBBI_PROBS`), group B from
  `[.09,.08,.09,.08,.12,.10,.19,.10,.15]` (`INDEPENDENT_IID_FAED_PROBS`),
  same 91/570 sizes, generation seed `0x413A1`. Must yield `p_raw <=
  0.005`.
- *Negative fixture:* both groups drawn from the same distribution,
  `SHARED_IID_PROBS = [.30,.20,.15,.10,.08,.06,.05,.04,.02]`,
  generation seed `0x413A2`. Must yield `p_raw > 0.005`.

Each fixture regenerates once (not per-trial) and runs the full
100,000-trial permutation null against it, seed `0x413A3` (positive
fixture's null) / `0x413A4` (negative fixture's null) — distinct from
the real-data null seed `0x413A0`.

## Diagnostic 3 — nine leave-one-letter-out (LOLO) sensitivities, conditional K=8

**This is a true conditional refit, not a K=9 scoring-only mask.**
Letter frequencies are compositional (they sum to 1 over the fitted
alphabet), so scoring-only exclusion under a K=9 fit still lets a
single outlier letter's presence distort the *other* eight letters'
fitted probabilities. Removing letter `L` from both training and
scoring, then refitting over the remaining eight symbols, is required
to actually isolate what the other eight letters say on their own.

**Masking and refit rule (frozen), per dropped letter `L`:**

- Remove `L` from **both** training and scoring — the 8 surviving
  letters' training counts are unchanged by `L`'s removal (they are
  independent counts, not renormalized against `L`), but `L`'s own
  count dimension is dropped entirely before fitting.
- Refit `S0` (pooled DBBI+FAED training counts) and `I0` (per-stream
  training counts) over the remaining eight symbols with KT smoothing,
  `alpha=0.5`, **K=8**: `P(c) = (count[c] + 0.5) / (N_no_L + 4.0)`
  where `N_no_L` is the total non-`L` training characters in that
  fold/stream (for `S0`, pooled across both streams).
- **Fold boundaries and positions are retained exactly as in Phase
  412** (`(0,19),(19,37),...`) — occurrences of `L` are not spliced
  out and the stream is not re-indexed or compacted; a held-out
  position whose true character is `L` is simply skipped (contributes
  neither bits nor a character to the length denominator). Positions
  are never joined across a removed `L` occurrence. Diagnostic 3 only
  ever compares `S0`/`I0` (IID models, no transition structure), so no
  question of bridging a transition across a removed position arises
  here.
- `macro_loss_L(model) = 0.5 * (DBBI_bits_L(model)/DBBI_length_L +
  FAED_bits_L(model)/FAED_length_L)`, `DBBI_length_L = 91 -
  count(DBBI==L)`, `FAED_length_L = 570 - count(FAED==L)`.
  `contrast_L = macro_loss_L(S0) - macro_loss_L(I0)`.

**Bootstrap null per letter:** generate 100,000 synthetic replicate
streams from the **full K=9 shared S0 null** — the same generator
Phase 412 already establishes (fit on the complete real 91/570-length
streams, unaware of which letter will later be dropped) — then apply
the **identical K=8 removal/refit procedure** above to each replicate
before computing its own `contrast_L`. Seed `0x413B0 + L` (`L` = 0..8,
`a` uses `0x413B0`, `i` uses `0x413B8`).

**p-value and correction:** `p_raw_L = (1 + count(null_L >=
observed_L)) / 100001`; Bonferroni across all 9 letters:
`p_family_L = min(1, 9 * p_raw_L)`. Promotion threshold `p_family_L <=
0.005`, computed identically for all 9.

**Required fixture (concentration-detection sanity check):** DBBI
drawn from `[.50,.0625,.0625,.0625,.0625,.0625,.0625,.0625,.0625]`,
FAED drawn from the uniform `[1/9]*9`, sizes 91/570, generation seed
`0x413B9`. Under the conditional K=8 refit, removing letter `a`
(index 0) leaves DBBI's remaining eight probabilities exactly uniform
(`1/8` each, since they were already equal) and FAED's remaining eight
conditionally uniform too (`1/8` each, since FAED was already exactly
`1/9` everywhere) — so `S0` and `I0` become identical after
conditioning on non-`a`, and `contrast_0` must collapse to
non-significant (`p_family_0 > 0.005`). At least one other LOLO index
(any of `b`-`i`) must remain significant, since removing a
non-dominant letter leaves `a`'s asymmetry intact. This validates that
the K=8 procedure can actually detect single-letter concentration when
it is known to exist, before trusting its verdict on the real streams.
(A K=9 scoring-only version of this same fixture would **not** cleanly
validate the procedure, since changing `a` from `1/9` to `.50`
necessarily changes the fitted probability of every other letter too
under an uncorrected 9-symbol normalization.)

## Diagnostic 4 — b/e reporting (not privileged)

`b` (alphabet index 1) and `e` (index 4) are reported as ordinary rows
in Diagnostic 3's 9-row table — same columns, same correction, same
threshold as the other seven letters. No separate test, no separate
threshold, no bolding or reordering that would visually privilege them
over `c`, `f`, or any other letter.

## Diagnostic 5 — per-fold direction check

Descriptive input (`F_k`, `k=0..4`) comes directly from Diagnostic 1.
Reports the sign of each `F_k` and how many of the 5 folds share the
overall contrast's positive (favors-independent) sign — this count is
also one of the two frozen gates in the interpretation rules below.
Not itself a hypothesis test (no p-value, no correction) beyond that
gate.

## Interpretation rules (exact, three-way, mutually exclusive)

Let `lolo_significant` = count of the 9 `p_family_L <= 0.005` results
in Diagnostic 3, and `fold_agree` = count of the 5 `F_k` with the same
sign as the overall `0.0566564` contrast (Diagnostic 5).

- **Distributed** — `lolo_significant >= 7` **and** `fold_agree >= 4`.
  T1's "distinct emission profiles" reading is robust. Diagnostic 2's
  same-data permutation result is reported alongside as corroboration.
  Per your instruction, the next useful evidence is external provenance
  or identification of the two independent consumers, **not** another
  transform or combinator on this branch.
- **Localized** — `lolo_significant <= 6` **and** `fold_agree <= 3`.
  Phase 412's result is downgraded in the registry to a localized
  frequency anomaly, not general structural evidence for T1. (Five
  folds sharing the same sign is evidence of *consistency*, not
  localization, by itself — localization here always requires the
  paired LOLO condition too, never the fold count alone.)
- **Mixed/inconclusive** — every other combination (e.g.
  `lolo_significant >= 7` with `fold_agree <= 3`, or
  `lolo_significant <= 6` with `fold_agree >= 4`): the two diagnostics
  disagree. Record both counts and the concentration metrics in the
  registry as an open, explicitly unresolved localization question;
  license no follow-up beyond what the "neither outcome" rule below
  already excludes.

**Neither outcome** (regardless of branch) licenses plaintext
generation, a new DBBI/FAED combinator, or a key search — stated
explicitly per your instruction, not left implicit.

## Deliverable

`tools/gsmg/phase413_i0_s0_signal_localization_audit.py`, with a
`self_test()` running the three required synthetic fixtures (Diagnostic
2 positive, Diagnostic 2 negative, Diagnostic 3 concentration) plus
Diagnostic 1's reconciliation invariant before the real-data diagnostics
run, a regression test in `tools/gsmg/test_recent_audits.py`, and
results recorded in `tools/gsmg/FINDINGS.md` as Phase 413. The registry
is updated only under whichever interpretation branch above the result
actually falls into.

## Related notes

- [DBBI/FAED Generative Model Comparison Pre-Registration](2026-08-25%20-%20DBBI%20FAED%20Generative%20Model%20Comparison%20Pre-Registration.md)
  (Phase 412)
- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
