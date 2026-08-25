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
---

# DBBI/FAED Generative Model Comparison — Pre-Registration

> [!caution] Prepared before computing any model scores
> This freezes every model, fold boundary, scoring rule, control, and
> promotion threshold before any score is computed, so the comparison
> cannot be tuned after seeing suggestive output. Deviating from this list
> mid-run would turn a held-out predictive test back into the same
> transformation-hunting pattern the
> [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
> exists to move away from.

## Scope and motivation

[GSMG_SCIENTIFIC_THEORY_REGISTRY](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
(Phase 411) names this as its recommended next experiment. The question is
narrower than "what do DBBI/FAED decode to" and does not attempt to answer
that:

> Are `DBBI` and `FAED` better predicted as independent emissions,
> emissions from one shared generator, or sequences with meaningful
> transition memory?

This directly discriminates two axes already load-bearing in the theory
registry and [GSMG_TOPOLOGY_AUDIT](../GSMG_TOPOLOGY_AUDIT.md): **shared
vs. independent generator** (registry T2 vs. T0/T1; audit T3/T6) and
**memoryless vs. sequential** (bears on how much residual signal T0's
"statistical artifact" reading leaves on the table). No decoding,
keyword search, plaintext scoring, or cryptographic oracle is in scope —
this is a pure model-comparison exercise over the raw symbol streams.

## Frozen data

- `DBBI`, exact 91-character string, alphabet `a`-`i`, from `tools/gsmg/data.py`.
- `FAED`, exact 570-character string, alphabet `a`-`i`, from `tools/gsmg/data.py`.
- No reshaping, decoding, keyword scan, plaintext scoring, or cryptographic
  oracle at any stage.

## Five competing models

All learned probabilities use fixed Krichevsky-Trofimov smoothing,
`alpha=0.5`, applied identically everywhere below — no tuned
hyperparameters, no per-model or per-fold adjustment.

1. **U0 — uniform IID.** Every symbol probability `1/9`. Zero fitted
   parameters; not smoothed (nothing is fit).
2. **S0 — shared IID.** One pooled 9-letter distribution, fit on the
   pooled training characters from both streams' training folds for the
   fold in question.
3. **I0 — independent IID.** Separate 9-letter distributions for DBBI and
   FAED, each fit only on that stream's own training folds.
4. **S1 — shared first-order Markov.** One pooled 9x9 transition model,
   fit on the pooled training transitions from both streams. **Pooling
   never counts a transition from DBBI's last training character into
   FAED's first training character (or vice versa)** — DBBI and FAED are
   treated as two separate contiguous chunks for transition-counting
   purposes, exactly like the within-stream fold-boundary rule below,
   even though S1 pools their unigram/transition *counts* into one model.
5. **I1 — independent first-order Markov.** Separate 9x9 transition
   models for DBBI and FAED, each fit only on that stream's own training
   transitions.

KT smoothing for a unigram cell: `P(symbol) = (count + alpha) / (N + 9*alpha)`.
For a Markov row (given previous symbol `p`): `P(next|p) = (count(p,next) + alpha) / (count(p,*) + 9*alpha)`,
computed independently per row (a previous symbol never observed in
training gets the uniform-over-alpha row, i.e. `alpha/(9*alpha) = 1/9` for
every next symbol).

## Held-out protocol

Fixed contiguous five-fold cross-validation, folds frozen before any
score is computed:

- DBBI folds (91 chars): sizes `19, 18, 18, 18, 18`, contiguous, in
  stream order, no overlap.
- FAED folds (570 chars): five contiguous blocks of `114`, in stream
  order, no overlap.

Fold index `k` (`0..4`) pairs DBBI's `k`-th block with FAED's `k`-th
block: for the shared models (`S0`/`S1`), fold `k`'s training set pools
DBBI's four non-`k` blocks with FAED's four non-`k` blocks, and fold
`k`'s held-out set is DBBI's `k`-th block plus FAED's `k`-th block,
scored separately per stream (so each stream still contributes its own
`DBBI_total_bits`/`FAED_total_bits` term to the primary score above, even
under a shared model). For the independent models (`I0`/`I1`), each
stream's fold `k` is fit and scored using only that stream's own data —
the pairing by index has no effect on `I0`/`I1`, it only keeps reporting
aligned across models.

For each fold, for each stream:

- Train on the concatenation of the other four blocks (for `S0`/`S1`,
  additionally pooled with the other stream's own other-four-blocks
  concatenation, per the paragraph above). Removing one contiguous block
  from a linear string leaves at most two contiguous training chunks
  (one chunk if the removed block is at either end); Markov training
  counts transitions **within** each surviving chunk only — never across
  the gap where the held-out block was removed, never wrapping from a
  stream's end back to its own start, and (for `S0`/`S1`) never bridging
  DBBI's chunks into FAED's chunks or vice versa, per the `S1` model
  definition above.
- Score the held-out block in bits per character (`-log2(P)` per symbol,
  summed over the block, divided by the block's length).
- **Markov scoring rule:** the held-out block's first character is scored
  under the fitted **unigram** distribution (from the same fold's IID
  model of the same topology — shared or independent), never under a
  transition row, even though the real preceding character exists in the
  original string just before the removed block. This keeps the boundary
  treatment consistent with the training rule above (that boundary
  transition was never counted during fitting) rather than mixing a
  counted-nowhere transition into scoring. Every other character in the
  held-out block is scored under the transition row keyed by the actual
  preceding character **within that same held-out block** (a real,
  non-artificial transition).

**Primary score (frozen formula):**

```text
macro_loss(model) = 0.5 * (DBBI_total_bits(model) / 91 + FAED_total_bits(model) / 570)
```

where `DBBI_total_bits(model)` is the sum of `-log2(P)` over all 91 held-out
DBBI characters across its 5 folds (the 5 folds partition DBBI exactly, so
every character is scored exactly once), and `FAED_total_bits(model)` is
the identical sum over all 570 held-out FAED characters across its 5
folds. Each stream is **character-weighted within itself** (total bits
divided by total characters, so a 19-character fold and an 18-character
fold contribute proportionally to their size, not as an unweighted
mean-of-five-fold-means) — the two streams are then combined with equal
50/50 weight regardless of their different lengths. This replaces and
fully specifies the earlier, ambiguous "mean per-fold bits-per-character"
description; do not average DBBI's fold-level means unweighted.

**Secondary score:** ordinary length-weighted micro-average,
`(DBBI_total_bits(model) + FAED_total_bits(model)) / 661` (all 661
held-out characters pooled), reported alongside but not used for
promotion.

## Two preregistered comparisons

Both contrasts are computed on each model's **primary macro score**
(`macro_loss(model)` above) and are **frozen independently of each
other** — neither is conditioned on the other's outcome.

1. **Topology contrast:**

   ```text
   topology_contrast = min(macro_loss(S0), macro_loss(S1)) - min(macro_loss(I0), macro_loss(I1))
   ```

   Positive values favor independent generators.

2. **Memory contrast:**

   ```text
   memory_contrast = min(macro_loss(S0), macro_loss(I0)) - min(macro_loss(S1), macro_loss(I1))
   ```

   Positive values favor sequential dependence. This is computed
   unconditionally over all four non-uniform models — **not** restricted
   to whichever topology (shared/independent) happened to win the first
   contrast. The two contrasts may disagree about which topology
   contributes the winning IID/Markov pair; that disagreement is itself
   reported, not resolved by conditioning.

## Calibration

100,000 parametric-bootstrap replicates per contrast, **rerunning the
complete fold-and-model-selection procedure each time** (not resampling
the already-computed losses) — i.e. each replicate's pair of synthetic
DBBI/FAED-length streams is fit and scored from scratch through all five
models and the full 5-fold protocol above, and that replicate's own
`topology_contrast`/`memory_contrast` value is recorded, building a
100,000-value null distribution per contrast.

**Null-model selection and fitting (frozen):**

- **Topology null generator:** whichever of `{S0, S1}` achieves the
  lower **real-data** `macro_loss` (i.e. selected once, by real-data
  cross-validated loss, before any bootstrap replicate runs). That
  selected model is then **refit on the complete real streams** (all 91
  DBBI characters, all 570 FAED characters — no folds, no held-out
  split) to obtain the single set of generating parameters used for
  every topology-null replicate.
- **Memory null generator:** whichever of `{S0, I0}` achieves the lower
  real-data `macro_loss`, selected and refit on the complete real
  streams the same way.
- If the selected generator is `S1` (shared Markov), the same
  DBBI/FAED-boundary transition exclusion from the model definition
  above applies to its full-data refit: no DBBI-to-FAED transition is
  counted.
- **Stream generation from a Markov generator:** the initial character
  of each synthetic stream (DBBI-length or FAED-length) is drawn from
  the generator's **fitted KT unigram distribution** (not uniform — this
  applies to bootstrap-null generation only, distinct from the four
  required controls' fixed generation rule below). Every subsequent
  character is drawn from the generator's transition matrix, conditioned
  on the immediately preceding **generated** character.
- **Stream generation from an IID generator** (`S0`/`I0`): every
  character, including the first, is drawn independently from the
  generator's fitted unigram distribution.
- Each replicate regenerates **both** a DBBI-length and a FAED-length
  stream from the same selected generator (for `S0`/`S1`, one shared
  distribution/matrix generates both; for `I0` used as the memory-null
  generator, `I0` already has separate DBBI/FAED-fitted parameters, so
  each stream uses its own).

**p-value (frozen, one-sided upper tail):**

```text
p_raw     = (1 + count(null_contrast >= observed_contrast)) / 100001
p_family  = min(1, 2 * p_raw)
```

`p_raw` uses the standard add-one correction over 100,000 replicates
(denominator `100001`). `p_family` applies a Bonferroni correction across
exactly the two contrasts (multiply by 2), computed identically for both
contrasts — not selected after seeing which correction yields
significance.

**Promotion threshold:** `p_family <= 0.005` for the contrast in
question, matching this project's existing convention for every other
statistically-scored family in the BTCSEED branch (Phases 399, 401, 402,
404, 407).

**Real-data bootstrap seeds (frozen):** topology-null replicates use
seed `0x412A0`; memory-null replicates use seed `0x412A1` (see the
Required Controls section below for the parallel fixture-bootstrap
seeds).

## Required controls

Before trusting any real-data result, the implementation must demonstrate
recovery on four synthetic fixtures, generated independently of the real
DBBI/FAED data, each run through the identical fold/fit/score/bootstrap
pipeline. States are indexed `0..8` corresponding to `a..i`. **All
fixture ground-truth parameters and seeds are frozen numerically below —
none may be tuned, and if a fixture fails to recover its planted
structure, the protocol stops; the probabilities or seeds themselves must
not be adjusted to make it pass.**

| j | Fixture | Ground truth | Must recover |
|---|---|---|---|
| 0 | Shared IID | one distribution `[.30,.20,.15,.10,.08,.06,.05,.04,.02]` generates both a 91-char and a 570-char stream | topology contrast favors shared (not significant in the independent direction) |
| 1 | Independent IID | DBBI: `[.03,.28,.08,.04,.22,.10,.10,.09,.06]`; FAED: `[.09,.08,.09,.08,.12,.10,.19,.10,.15]` | topology contrast significantly favors independent (`p_family <= 0.005`) |
| 2 | Shared Markov | one 9x9 transition matrix generates both streams: row `i` has `P(i)=.55`, `P((i+1) mod 9)=.35`, and the remaining seven states each get `.10/7` | topology contrast favors shared; memory contrast significantly favors Markov (`p_family <= 0.005`) |
| 3 | Independent Markov | DBBI uses fixture 2's forward-cycle matrix (`(i+1) mod 9` at `.35`); FAED uses the same row shape but substitutes `(i-1) mod 9` for the `.35` transition | topology contrast significantly favors independent; memory contrast significantly favors Markov (both `p_family <= 0.005`) |

Each row's stated probabilities sum to `1.0` exactly (verified by
`self_test()` before use). For fixtures 2/3, the **initial character**
of each generated synthetic stream is drawn **uniformly** over the 9
states (this fixture-generation rule is deliberately different from the
bootstrap-null generation rule above, which seeds from a fitted unigram
instead — fixtures use known ground truth, not a fitted model).

**Frozen seeds (deterministic, `numpy.random.default_rng(seed)` or
equivalent, one independent generator per named use — never reused
across rows):**

```text
fixture generation:  0x412B0 + j        (j = 0,1,2,3, one per fixture above)
real bootstraps:     0x412A0 (topology), 0x412A1 (memory)
fixture bootstraps:  0x412C0 + 2*j (topology), 0x412C1 + 2*j (memory)
```

So fixture 0 (Shared IID) uses generation seed `0x412B0` and bootstrap
seeds `0x412C0`/`0x412C1`; fixture 1 (Independent IID) uses `0x412B1` and
`0x412C2`/`0x412C3`; fixture 2 (Shared Markov) uses `0x412B2` and
`0x412C4`/`0x412C5`; fixture 3 (Independent Markov) uses `0x412B3` and
`0x412C6`/`0x412C7`. Each fixture runs its **own** full 100,000-replicate
bootstrap calibration (not just a sign check on the observed contrast),
so a fixture's "must recover" column above is judged by the same
`p_family <= 0.005` promotion bound used for real data, not a looser
qualitative check.

These four fixtures jointly confirm the sample sizes — especially DBBI's
91 characters, the tightest constraint in this design — provide enough
power for whatever conclusion the real data produces. A real-data result
is only interpreted once all four fixtures recover their planted
structure exactly as specified in the table above.

## Interpretation rules

Both contrasts are one-sided tests whose null hypothesis is the *simpler*
member of the pair being compared (shared for topology, IID for memory).
That asymmetry matters for reading the results: only "independent beats
shared" and "Markov beats IID" are outcomes this design can actually
confirm as significant. The reverse directions (shared not rejected, IID
not rejected) are non-rejections, not confirmations — see the corrected
shared-model rule below.

- **Topology contrast significant (favors independent), memory contrast
  not significant:** T1 (independent consumers) gains support, but
  narrowly — "different independent frequency profiles," not predictive
  sequential language. Update the registry's T1 entry to note this
  specific evidence; do not treat it as new support for T3/T4/T5.
- **Topology contrast significant (favors independent) AND memory
  contrast significant (favors Markov):** the strongest evidence this
  design can produce — distinct sequential generators per stream. This
  licenses exactly one separately frozen follow-up phase (a mechanism
  comparison — e.g. which specific Markov order or construction), not an
  open-ended new search.
- **Topology contrast does not clear `p_family <= 0.005` (i.e. does not
  significantly favor independent):** this is **compatibility with a
  shared generator, not positive evidence for T2.** The topology null is
  itself generated *from* the best shared model (Calibration above), so
  this test is constructed only to detect whether independent parameters
  fit significantly better — it cannot, by its own one-sided design,
  confirm that shared parameters are correct or sufficient, only that
  independent ones were not shown to be required. Do not describe this
  outcome as "a shared model won" in the registry; record it as "the
  independent-generator alternative was not supported," and do not
  reopen T2's ~45-model operator search (gap `G-YIN-001`) on this basis.
  A genuine test of whether shared is *preferred* (not merely
  not-rejected) would need a differently designed comparison (e.g. an
  information-criterion-based model selection), which this pre-
  registration does not authorize.
- **Neither contrast clears `p_family <= 0.005`:** retain T0/T1 as
  currently stated in the registry, record this experiment as executed
  evidence for them, and do not open another transform family on this
  branch.
- **Memory contrast significant (favors Markov), regardless of the
  topology outcome:** update
  [GSMG_SCIENTIFIC_THEORY_REGISTRY](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
  first. Per the registry's own explanation/confirmation separation, a
  significant Markov result is evidence about *predictability*, not
  itself a password or key candidate — it must not be immediately
  converted into candidate generation without its own separately frozen
  contract.

## Caveat (explicit, not a footnote)

This is **computationally held out, not historically blind** — DBBI and
FAED have already been studied extensively by this project and the wider
community for years before this comparison is run. It can compare
predictive models against each other under a fair, pre-registered
protocol; it **cannot** count as wholly independent external confirmation
of whatever it finds, in the same sense Phase 410's provenance work
distinguishes creator-authenticated evidence from community-derived
readings. Any positive result here still needs an independent,
out-of-sample discriminator before being promoted further.

## Exclusions

- No decoding, keyword search, dictionary scoring, or quadgram scoring of
  any kind.
- No cryptographic oracle (blob decrypt, address check, BIP32/BIP39) —
  this experiment produces a model-comparison verdict, not key material.
- No fold-boundary or smoothing-parameter tuning after seeing any score.
- No Markov order beyond first-order (bigram) — a higher-order comparison
  is a separate, not-yet-authorized experiment.
- No promotion of a significant memory-contrast (Markov) result into
  password candidates without a new, separately frozen contract (see
  interpretation rules above).

## Expansion rule

None. This is a closed, one-shot comparison over five frozen models, two
frozen contrasts, and four frozen controls. Any follow-up implied by the
interpretation rules (the I1-wins mechanism-comparison phase) is its own
separately numbered phase with its own contract, not an amendment to this
one.

## Deliverable

`tools/gsmg/phase412_dbbi_faed_generative_model_comparison_audit.py`,
implementing exactly the protocol above, with:

- a `self_test()` that runs all four required controls and asserts each
  recovers its planted structure before the real-data run is trusted;
- the real-data macro/micro losses for all five models across all ten
  folds (5 DBBI + 5 FAED);
- both contrasts' bootstrap p-values, pre- and post- family-wise
  correction;
- a permanent regression in `tools/gsmg/test_recent_audits.py`.

Results will be recorded in `tools/gsmg/FINDINGS.md` as Phase 412 once
computed, and the theory registry updated per whichever interpretation
rule above actually applies.

## Related notes

- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
- [GSMG Topology Audit](../GSMG_TOPOLOGY_AUDIT.md)
- [GSMG Object: DBBI](../GSMG_OBJECT_DBBI.md)
- [GSMG Object: FAED](../GSMG_OBJECT_FAED.md)
- [GSMG Open Gap Registry](../GSMG_OPEN_GAP_REGISTRY.md) (`G-YIN-001`,
  `G-ESC-001`)
