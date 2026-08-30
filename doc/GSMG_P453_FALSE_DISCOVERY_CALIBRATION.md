---
type: audit
phase: 453
date: 2026-08-29
status: complete
result: one-unusual-three-null-sensitive-or-common
disposition: calibration
script: tools/gsmg/phase453_false_discovery_calibration.py
---

# Phase 453 — Symbolic False-Discovery Calibration

## Question

When the project's existing symbolic discovery procedures are applied to
matched null objects, how often do they produce observations at least as
exact-looking as `KIT`, `FF67`, `ggn`, and `401/400/73`?

Protocol:
[Phase 453 False-Discovery Calibration Harness Protocol](Brainstorms/2026-08-29%20-%20Phase%20453%20False-Discovery%20Calibration%20Harness%20Protocol.md).

This phase calibrates evidentiary weight. It does not test creator intent,
provide a missing selector or consumer, generate a password, or modify an Open
Gap Registry closure condition.

## Frozen inputs

The symbolic manifest was frozen before implementation and real scoring:

    tools/gsmg/phase453_symbolic_manifest.json
    SHA-256 22365a0e343f251921b053230f0e1eb1e50cf7cf99f8a3051a47ad1a51ff63af

It pins:

- the four cases and canonical audit/code digests;
- the repository's BIP39 list as the three-letter word endpoint;
- a literal master seed, `45320260829`;
- 100,000 Monte Carlo objects per stochastic null;
- complete historical choice budgets;
- primary and sensitivity nulls;
- real score definitions;
- Holm correction across four symbolic cases at alpha 0.05;
- controls, decision states, interpretation limits, and stop rules.

The source digest check includes the Phase 450 update to the Roman audit and
does not modify that existing work.

## Choice-budget reconstruction

### S-KIT

The historical family independently allows each source's two rows to retain or
swap order, followed by direct or reverse traversal: `2 x 2 x 2 = 8` outputs.
The primary null draws four ordered positive row sums uniformly from `1..25`,
forms two additive total/row1/row2 triples, and applies all eight outputs. A hit
is any valid A1Z26 output in the pinned three-letter BIP39 vocabulary, not only
the post-hoc word `KIT`.

The sensitivity family exactly assigns the observed row-sum multiset
`{25,18,16,7}` to the four source-row positions in all 24 ways.

### S-FF67

Every null object is a 2x3 matrix of six distinct decimal digits. Its
total/row1/row2 vector is derived from that matrix, then the full four rectangle
orientations and six vector orders are evaluated: 24 outputs.

The primary null samples 100,000 ordered distinct-digit matrices. The
sensitivity null exactly enumerates all `10P6 = 151,200` such matrices.

The real score of 2 requires an output containing 255 and an ASCII letter.
Score 1 is deliberately broader: two unsigned bytes with at least one
printable byte. Exact ordered `(255,103)`, either-order `{255,103}`, and FF plus
letter remain diagnostics rather than the sole endpoint.

### S-GGN

The independently sourced tuple `{1,4,21}` is held fixed. The primary null
uniformly shuffles the complete 24-character source multiset and applies both
recorded index bases. Score 2 requires first-pair-equal/distinct-third with the
third character globally unique; score 1 requires only the repeated first
pair.

The sensitivity family is the canonical audit's exact 2,024 increasing triples
from the fixed source. The later curve narrative remains explicitly
uncalibrated because its scalar, negation, and secp256k1 choices were never a
closed historical search space.

### S-ROMAN

Each null object contains two distinct four-character tokens. The full two rail
polarities and seven title contexts are evaluated, preserving the historical
14-output family and strict canonical Roman parsing.

The primary null draws characters from the empirical uppercase alphabetic
distribution of the 13 frozen high-salience labels. The sensitivity null draws
uniformly from `A..Z`. The target `(401,400)` was frozen from the prior fitted
sums. Phase 450's negative remains explicit: applying the winning rule to FEFE
yields 100, not 73.

## Controls

All controls passed:

- non-puzzle full-path positives: `LEG`, `(97,255)`, a
  repeated-pair/unique-third string, and `DIBB/DAEF` producing the Roman target;
- no-hit and no-strong-hit controls;
- all-equal-best tie retention;
- manifest, source, and vocabulary digests;
- deterministic seed replay;
- transform and endpoint regression tests.

The 1,000-object-per-case cost-only benchmark took approximately 0.13 seconds
and explicitly reported `real_cases_scored=false`. Null populations completed
before canonical cases were evaluated.

## Results

| Case | Primary extreme / trials | Raw primary p | Holm primary p | Sensitivity extreme / trials | Raw sensitivity p | Holm sensitivity p | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| S-KIT | 1,608 / 100,000 | 0.016090 | 0.048270 | 8 / 24 | 0.360000 | 0.360000 | sensitive_to_null_design |
| S-FF67 | 348 / 100,000 | 0.003490 | 0.013960 | 492 / 151,200 | 0.003261 | 0.013042 | unusual_but_unselected |
| S-GGN | 3,770 / 100,000 | 0.037710 | 0.075419 | 36 / 2,024 | 0.018272 | 0.054815 | common_under_matched_null |
| S-ROMAN | 6,749 / 100,000 | 0.067499 | 0.075419 | 3,489 / 100,000 | 0.034900 | 0.069799 | common_under_matched_null |

Empirical p-values use the plus-one rule. The recorded normal intervals are
descriptive Monte Carlo intervals; exact sensitivity families retain the same
plus-one convention for a uniform reporting contract.

### KIT

The broad additive-triple null makes some three-letter BIP39 word in the
eight-output family uncommon enough to pass the primary four-case Holm
threshold narrowly. But eight of the 24 exact assignments of the observed four
row sums produce some vocabulary hit. The conclusion therefore changes under a
pre-registered defensible null: KIT is null-sensitive, not calibrated unusual.

This also demonstrates why the earlier exact KIT `1/8` or `1/6` fixed-target
rates were not discovery probabilities.

### FF67

The FF-plus-ASCII-letter endpoint appears in 348/100,000 primary draws and
492/151,200 objects in the exact distinct-decimal-matrix universe. Both
four-case Holm-adjusted values remain below 0.05.

FF67 is therefore genuinely unusual under both frozen nulls. The result does
not fix the six unselected semantic steps recorded by its canonical audit:
matrix-product reuse, multiplication, dimension alignment, FF/white
interpretation, ASCII interpretation, and byte serialization. It remains an
unusual but unselected recognition checkpoint, not key material.

### GGN

The repeated-first-pair/unique-third structure occurs in 3.77% of shuffled
sources and 36/2,024 fixed-source triples. Neither survives four-case Holm
correction. The exact string `ggn` remains uniquely located, but that
fixed-target uniqueness is post-hoc and the secp256k1 narrative is outside the
calibratable closed family.

### Roman 401/400

The exact target pair appears for 6.749% of empirical-character token pairs and
3.489% of uniform-A..Z pairs after all 14 contexts. Neither survives four-case
Holm correction. The observation is common under the frozen full-choice
families, and FEFE remains 100 rather than 73 under the winning rule.

## Same-run correction

The first generated decision layer Holm-corrected the four primary p-values but
compared sensitivity p-values to raw alpha. That inconsistent multiplicity
treatment initially labeled GGN and Roman `sensitive_to_null_design`. Raw null
histograms, random seed, manifest, transforms, and real scores were unaffected.

Before documentation or findings integration, the decision layer was corrected
to Holm-adjust both four-case families. Deterministic regeneration changed GGN
and Roman to `common_under_matched_null`. KIT and FF67 were unchanged. The
final result digest is:

    tools/gsmg/phase453_result.json
    SHA-256 3c0f920827c8de319a92266e84875f33a9249e15fc4f498c7eded0dfe7a4e94c

## Disposition

`calibration_only_no_gap_closure`.

- `G-MATPROD-001` gains calibrated corroborative weight, but remains parked
  because multiplication and a byte consumer are unselected.
- `G-KIT-001` remains a null-sensitive thematic fold.
- `G-GGN-001` remains a post-hoc exact extraction with an uncalibrated curve
  narrative.
- `G-PRIME-001` remains common under the declared symbolic nulls and has no
  selector or consumer.

No priority, state, next action, or closure condition changes.

## Stop rules honored

Zero passwords or keystrings, decryptions, blob/address oracle calls, GPU,
Docker, network, external search, or external agents. The dual-stream and
artifact-fingerprint lanes were not executed.

Reproduce:

    python3 tools/gsmg/phase453_false_discovery_calibration.py --self-test
    python3 -m unittest tools/gsmg/test_phase453_false_discovery_calibration.py
    python3 tools/gsmg/phase453_false_discovery_calibration.py --benchmark 1000
    python3 tools/gsmg/phase453_false_discovery_calibration.py --run

## Reopen condition

Version this calibration only if a canonical source corrects a historical
choice budget, code review finds an omitted transform, a new discovery family
requires a new null lane, or an implementation/control defect changes a rank.
New semantic evidence does not retroactively alter what was independently
fixed at discovery time.
