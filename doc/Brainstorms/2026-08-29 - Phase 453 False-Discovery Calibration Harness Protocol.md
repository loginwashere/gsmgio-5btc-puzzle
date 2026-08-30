---
type: hypothesis
phase: 453
date: 2026-08-29
status: stable
topics:
  - calibration
  - false-discovery
  - matched-null
  - multiple-comparisons
  - symbolic-transforms
  - dual-stream
  - artifact-fingerprint
---

# Phase 453 — False-Discovery Calibration Harness Protocol

> [!info] Executed as Phase 453
> The frozen symbolic lane was executed and recorded in
> [GSMG_P453_FALSE_DISCOVERY_CALIBRATION](../GSMG_P453_FALSE_DISCOVERY_CALIBRATION.md).
> The later dual-stream and artifact lanes remain unexecuted and require their
> own phase numbers and frozen protocols.

## Question

When the project's existing pattern-discovery procedures are applied to
matched null objects, how often do they produce results at least as
exact-looking as the real observations they generated?

The initial target is a symbolic-transform calibration for KIT, FF67, ggn, and
401/400/73. Later dual-stream and artifact-clustering lanes are planned
extensions, but cannot execute until their own manifests and null generators
are frozen.

This phase calibrates discovery procedures, not puzzle truth. It cannot prove
intent, supply a consumer, authenticate a selector, produce a password, or
close an Open Gap Registry row.

## Hypotheses

H0-SYM: after preserving each source object's relevant shape and applying the
same frozen transformation budget used on the real object, exact-looking
semantic or numeric coincidences occur at a rate compatible with matched null
objects.

H1-SYM: at least one real observation is more extreme than its complete
matched-null family under the pre-registered familywise rule.

Rejecting H0-SYM increases corroborative weight only. It does not select the
transform or satisfy an external-evidence closure condition.

Later lanes use distinct nulls:

- H0-STREAM: a proposed DBBI/FAED statistic or topology score is reproduced by
  null streams preserving the marginals and local structure it exploits.
- H0-ARTIFACT: proposed clusters recur among unrelated contemporaneous
  artifacts sharing common tool and format defaults.

## Lane isolation

| Lane | Methods calibrated | Required preservation | Initial status |
|---|---|---|---|
| S: symbolic | arithmetic, reversal, A1Z26, byte/hex, Roman filtering, prefix/rail selection | shape, range/alphabet, ordering, transform budget, endpoint class | executable after manifest freeze |
| D: dual-stream | tokenizer, transition, role-split, directional-generator statistics | lengths, counts, token/run distributions, autocorrelation, fixed boundaries | design only |
| A: artifact | formatting vectors and clustering | format, era, ecosystem defaults, artifact type, missingness | design only |

Evidence from one lane cannot calibrate another.

## Frozen symbolic cases

The initial lane contains exactly four historical cases. Canonical audits and
code must be read during manifest construction; this table declares scope but
does not replace their recorded search spaces.

| Case | Observation | Procedure class | Live gap |
|---|---|---|---|
| S-KIT | second matrix-list difference, A1Z26, reversal gives KIT | paired-list arithmetic, alphabet map, direction | G-KIT-001 |
| S-FF67 | matrix multiplication gives (255,103), serialized as FF67 | matrix arithmetic, ordering, byte/hex | G-MATPROD-001 |
| S-GGN | FEFE tuple {1,4,21} participates in ggn/secp256k1 reading | tuple indexing, case, scalar/group semantics | G-GGN-001 |
| S-ROMAN | Roman projection plus title C gives ordered 401/400; fitted FEFE remains 73 | rail selection, Roman filtering, prefix, numeric conversion | G-PRIME-001 |

No fifth case may be added after null results are inspected. A later case
requires a versioned extension and fresh familywise calculation.

## Step 1 — reconstruct analyst choice budgets

For each case, build a machine-readable transform graph from canonical audits
and code. Label every node:

- source_fixed: authenticated directly by the artifact;
- clue_selected: independently selected before the result;
- analyst_selected: introduced by the discovery path;
- serialization: decimal, alphabetic, byte, hex, case, order, reversal, etc.;
- semantic_target: word, theme word, number, byte pattern, curve object, or
  another endpoint class.

The null receives the same analyst-selected and serialization budget as the
historical discovery, never only the winning path. If that budget cannot be
reconstructed defensibly, return uncalibratable_from_record instead of guessing
a smaller menu.

Required manifest fields:

    case_id:
    canonical_sources:
    source_object_digest:
    source_fixed_nodes:
    clue_selected_nodes:
    analyst_selected_nodes:
    serialization_nodes:
    semantic_target_registry:
    historical_hypothesis_count:
    reconstructability: exact | conservative_upper_bound | uncalibratable

A conservative upper bound permits at least as much choice as the historical
search. An anti-conservative lower bound that makes the real hit look rarer is
prohibited.

## Step 2 — freeze endpoint classes

Before simulation, freeze detectors independently of winning strings where
possible:

1. **word:** dictionary version, lengths, case, and whether reversal is a
   transform or detector;
2. **theme:** closed vocabulary from authenticated puzzle text dated before the
   observations, with provenance per entry;
3. **numeric:** exact target set or fixed property such as prime, byte range,
   repeated digit, coordinate range, or known puzzle number;
4. **byte/hex:** length, case, leading-zero policy, registered structures;
5. **cryptographic object:** complete semantic validation, not resemblance.

The principal statistic is the best hit against the entire endpoint class an
analyst could have noticed. Do not calibrate only the word KIT after observing
KIT.

## Step 3 — matched null generators

### S-KIT

Generate ordered paired integer lists preserving list lengths, defensible value
range, ordering status, authenticated partitions, and equality/uniqueness
constraints. Apply the complete reconstructed arithmetic/direction/alphabet
menu. Score the best endpoint-class hit per synthetic object.

### S-FF67

Generate matrices preserving dimensions, entry domain and marginal multiset
where defensible, source-selected ordering, and authenticated labels. Apply the
full reconstructed matrix-operation and serialization menu. Count byte-valid,
hex-valid, word-like, thematic, and registered numeric hits.

### S-GGN

Generate tuples preserving length, value domain, ordering, and repetition
pattern. Apply the complete historical indexing, case, scalar, negation, and
group/curve menu, not only the winning narrative. Report earliest linguistic
coincidence separately from end-to-end validated-object rate.

### S-ROMAN

Generate rail tokens preserving lengths, alphabets, rail count, color/order
labels, and title-prefix eligibility. Apply the 14-rail primary family and
disclosed 1,092-configuration control as separate families. Report ordered
exact-pair and permutation matches, best three-value match including FEFE, the
real pattern's rank, and equally concise narratives. Phase 450's result that
the naive winning rule gives FEFE 100 rather than 73 remains visible.

## Step 4 — controls

For each generator, plant synthetic objects containing a known eligible
mechanism. Production code must recover each plant without a special path. At
least one positive per case exercises the full path through serialization and
validation; positives are excluded from null rates.

Negative and integrity controls:

- random objects preserving only dimensions/lengths;
- label shuffles preserving values but breaking authenticated order;
- full historical budget versus winning path alone, with the latter labeled
  anti-conservative and barred from primary inference;
- general dictionary versus authenticated theme vocabulary;
- deterministic replay under the frozen seed;
- digest checks for inputs, vocabularies, registries, and manifests;
- unit tests for every transform and endpoint detector;
- planted ties proving every equal-best result is retained;
- planted no-hit proving the report does not manufacture a winner.

## Step 5 — trial count and seed

Before implementation, estimate the smallest tail worth resolving under the
four-case familywise rule. Freeze:

- N_TRIALS_PER_CASE;
- one literal master pseudorandom seed;
- deterministic case-seed derivation;
- batch and checkpoint format;
- exact enumeration policy for small universes.

Planning target: at least 100,000 independent null objects per case, subject to
a pre-run cost benchmark. If this cannot resolve the desired tail, report an
interval or bound; do not extend after viewing the real rank. Never choose a
seed for convenient controls or a desired result.

## Step 6 — statistics and multiplicity

Define a computable extremeness tuple per case before simulation. Candidate
components:

    endpoint_validator_strength
    number_of_independently_fixed_steps
    negative_analyst_choice_count
    output_specificity
    cross_object_consistency

Every component needs an exact implementation definition. Human impressiveness
ratings are prohibited.

Report the real tuple, complete null distribution or content-addressed
reproducible summary, empirical tail interval, rank among nulls plus real,
equal-or-more-extreme null hits, sensitivity across pre-registered nulls, and
the winning-path-only diagnostic.

Primary inference covers four cases. Use a frozen Holm correction at alpha 0.05
and also report raw empirical values. No global statement that GSMG patterns
are significant is allowed; conclusions remain case- and null-specific.

## Step 7 — decision states

Each case returns exactly one:

- common_under_matched_null;
- unusual_but_unselected;
- sensitive_to_null_design;
- uncalibratable_from_record;
- harness_failure.

The phase result is a four-row table, not a global winner or average.

## Step 8 — interpretation contract

Permitted:

- say whether a specified procedure frequently manufactures comparable hits
  under a specified null;
- reduce, retain, or call null-sensitive an observation's evidentiary weight;
- require this calibration or a versioned extension for future use.

Prohibited:

- infer creator intent;
- close G-KIT-001, G-MATPROD-001, G-GGN-001, or G-PRIME-001;
- use one lane to validate another family;
- claim non-significance proves meaninglessness;
- let significance authorize passwords, cipher widening, or oracle work.

Registry priorities and closure conditions remain unchanged absent independent
new evidence.

## Later extension D — dual-stream calibration

Required before the two-role escape experiment or asymmetric tournament. Its
own protocol must freeze source bytes and tokenizations, statistics/topology
scores, nulls preserving counts/lengths/token and run distributions/
autocorrelation/boundaries, held-out observables, and familywise handling across
models, directions, pairs, periods, and features. Winners are
corroboration_only. BTCSEED is the control that reproducibility plus a local
checkpoint does not supply a selector.

## Later extension A — artifact calibration

Required before artifact clustering. Its protocol must freeze the puzzle
manifest, provenance, contemporaneous unrelated controls, feature vectors,
missing-value policy, generic-default classification, clustering algorithm,
distance metric, cluster-count policy, stability analysis, and
ecosystem-matched nulls. Maximum inference: shared-toolchain or shared-session
compatibility.

## Implementation plan

If execution is later authorized:

1. Create phase453_symbolic_manifest.json with cases, sources, digests,
   transform graphs, endpoints, nulls, seed, and trial count.
2. Implement deterministic transform/endpoint libraries and puzzle-free unit
   fixtures.
3. Implement four null generators and preservation assertions.
4. Add positive, negative, tie, no-hit, digest, and determinism controls.
5. Run a cost-only benchmark without scoring real observations.
6. Freeze final count and manifest digest before the real run.
7. Execute null populations and content-addressed checkpoints.
8. Score real observations once, after null completion.
9. Generate machine-readable and human audit reports.
10. Record a finding only after every integrity control passes; otherwise
    record harness_failure without interpreting cases.

Proposed artifacts:

    tools/gsmg/phase453_false_discovery_calibration.py
    tools/gsmg/test_phase453_false_discovery_calibration.py
    tools/gsmg/phase453_symbolic_manifest.json
    tools/gsmg/phase453_result.json
    doc/GSMG_P453_FALSE_DISCOVERY_CALIBRATION.md
    tools/gsmg/findings/P00453.md

Later D and A lanes receive separate phase numbers and protocols.

## Required outputs

- manifests and SHA-256 digests for inputs and registries;
- transform-choice audit for every real case;
- null preservation and all control results;
- raw and Holm-adjusted empirical results;
- all equal-or-more-extreme examples or a complete addressed record;
- sensitivity across frozen null variants;
- one decision state per case;
- unchanged gap closure conditions;
- deterministic replay commands and environment.

## Stop rules

- No passwords, keystrings, decryption, blob/address oracle, GPU, Docker,
  network, external search, or external agents.
- No transform, endpoint, null, feature, or case added after any real rank.
- No seed-changing rerun because a result is inconvenient.
- Return harness_failure on any positive, digest, preservation, determinism,
  tie-retention, or no-hit control failure.
- Return uncalibratable_from_record when historical choice budget cannot be
  conservatively reconstructed.
- Do not proceed into later D or A lanes under this protocol.

## Success, disposition, and reopen condition

Scientific success is a reproducible table for all calibratable cases,
regardless of whether observations appear common or unusual. Operational
failure means controls fail or search spaces cannot be reproduced.

The sole phase-level disposition is calibration_only_no_gap_closure.

Version/reopen only when a canonical source corrects a choice budget, a code
audit finds an omitted historical transform, a new discovery family needs a
new null lane, or an implementation/control defect changes a rank. New puzzle
meaning does not alter calibration unless it changes what was independently
fixed at discovery time.

## Related documents

- [Post-Phase-452 Scientific Experiment Portfolio](2026-08-29%20-%20Post-Phase-452%20Scientific%20Experiment%20Portfolio.md)
- [GSMG Open-Gap Registry](../GSMG_OPEN_GAP_REGISTRY.md)
- [GSMG Brainstorm Backlog Ledger](../GSMG_BRAINSTORM_BACKLOG_LEDGER.md)
- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
- [Post-Phase-340 Future Search Portfolio](2026-08-20%20-%20Post-Phase-340%20Future%20Search%20Portfolio.md)
- [Phase 448 — Brute-Force Eligibility](../GSMG_P448_BRUTEFORCE_ELIGIBILITY.md)
- [Phase 450 — G-PRIME-001 Consumer Sweep](../GSMG_P450_G_PRIME_CONSUMER_SELECTOR_SWEEP.md)
