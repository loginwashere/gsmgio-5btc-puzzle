---
type: hypothesis
phase: 449
date: 2026-08-29
status: stable
topics:
  - G-ESC-001
  - DBBI
  - FAED
  - escape-pair
  - selector
---

# Phase 449 — G-ESC-001 Pair-Discrimination Protocol

## Question

Can the evidence already authenticated in this repository select or contradict
either of FAED's two standing escape-pair hypotheses, `{g,i}` and `{h,e}`,
without inventing a new decoder, consumer, or scoring rule?

This is a selector/contradiction audit, not another cipher sweep.

## Frozen candidates

1. `GI`: unordered FAED escape pair `{g,i}`, originally selected from FAED's
   internal frequency/code-IC behavior.
2. `HE`: unordered FAED escape pair `{h,e}`, derived by applying the standing
   `mirror9` relation to DBBI's `{b,e}` pair through the Architect
   `BUT/HYE` construction.

Escape order, checkerboard topology, alphabet completion, plaintext model,
password material, and downstream consumer are outside this audit. Existing
results involving those choices are evidence about a model instantiated with
a pair, not automatically evidence against the pair itself.

## Frozen evidence classes

Every usable observation must be assigned to exactly one primary class so the
same underlying fact is not counted repeatedly:

1. `raw_admissibility`: whether the pair segments the authenticated raw stream;
2. `internal_statistic`: statistics computed only from FAED and a declared
   segmentation, including code IC and escape-symbol frequency;
3. `rule_derivation`: an exact puzzle-derived rule that outputs a pair;
4. `presentation_or_provenance`: page markup, boundaries, archive variants,
   chronology, or creator-source evidence;
5. `downstream_model`: a specific decoder/transform/consumer result;
6. `cross_representation`: a result derived from FAED under a representation
   that does not use the disputed escape pair.

Correlated measurements may be listed separately but share one independence
group. Negative decoder/oracle results cannot contradict an escape pair unless
the decoder, serialization, consumer, and validator were independently fixed.

## Decision gates

Return `select_gi` or `select_he` only if all four gates hold for that pair:

1. `valid_on_faed`: it segments the complete authenticated FAED stream;
2. `independent_selector`: at least one authenticated clue or forced structural
   rule selects it independently of an analyst-chosen decoder or score target;
3. `rival_excluded_or_reconciled`: the same evidence either contradicts the
   rival pair or explains why the candidates answer different roles;
4. `no_load_bearing_open_dependency`: the selection does not depend on another
   parked gap such as G-ARCH-001.

If neither pair passes all four, return `remain_unreconciled`. A ranking may be
reported separately from selection.

## Required outputs

- a compact candidate-by-constraint comparison table;
- an evidence-independence table showing which observations share a source;
- an explicit contradiction audit distinguishing pair-level falsification from
  decoder-level negatives;
- the strongest justified ranking, if any;
- an exact statement of what new evidence would reopen the gap.

## Stop rules

- No new cipher menu, hill climb, password generation, blob/address oracle,
  brute force, GPU, Docker, network, or external agent.
- Existing artifacts may be recomputed only to verify pinned counts/ranks.
- A suggestive plaintext fragment from an escape-independent representation
  cannot select either pair unless a sourced bridge to the escape grammar exists.
