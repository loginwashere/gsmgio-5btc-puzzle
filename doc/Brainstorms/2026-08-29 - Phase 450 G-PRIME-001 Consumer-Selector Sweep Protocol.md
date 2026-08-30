---
type: hypothesis
phase: 450
date: 2026-08-29
status: stable
topics:
  - G-PRIME-001
  - roman-rail
  - prime-sums
  - consumer
  - selector
---

# Phase 450 — G-PRIME-001 Consumer/Selector Sweep Protocol

## Question

Does any evidence already authenticated in this repository, or newly
recoverable from the complete Telegram export by a bounded pre-registered
search, supply (a) a downstream consumer for all three fitted prime sums
`401`/`400`/`73`, (b) an independent selector for the winning Roman-letter
projection + title-`C` construction (`GSMG_ROMAN_RAIL_PRIME_SUM_AUDIT.md`),
or (c) an account of FEFE's fitted sum `73` under that construction or any
other already-authenticated construction?

This is a selector/consumer sweep, not a new cipher search. It does not
re-derive the 401/400/73 values themselves (frozen since Phase 260/261/263)
and does not invent a new decoder.

## Frozen inputs

- `EXPECTED_FITTED_SUMS = {"B": 401, "Y": 400, "F": 73}`
  (`first_piece_prime_sum_reconstruction.py`), unchanged.
- The unique winning rail configuration: DBBI/FAED Roman-letter projection,
  title `C` prefixed, giving `CDI=401` (blue) / `CD=400` (yellow)
  (`roman_rail_prime_sum_audit.py`), unchanged.
- The disclosed 1,092-configuration control, which additionally hits
  `yinyang`/`FEFE` with prefix `CD` (also `401/400`), unchanged.

## Frozen evidence classes

1. `naive_extension`: applying the exact winning rule (title `C` prefix +
   Roman-letter projection, no new choice) to FEFE itself, to see whether it
   reproduces `73` without any new decision;
2. `standalone_numeral_corpus`: messages in the complete Telegram export
   containing all three standalone target numerals in decimal form;
3. `roman_form_corpus`: messages containing both target Roman forms (`CDI`
   and `CD`) as standalone tokens;
4. `phrase_corpus`: messages containing the phrase `roman numeral(s)` or
   `title initial` (case-insensitive), which would indicate the creator or
   community ever named the operation this construction requires;
5. `creator_authorship`: for any hit surfaced by classes 2-4, whether the
   sender is the creator account, and whether the creator ever replied to a
   community hit.

Class 1 requires no corpus access; classes 2-4 require one pass over the
57,729-message export using pre-registered, exact substring/regex matches
fixed before the script runs. No fuzzy matching, no semantic search, no
per-message LLM judgment.

## Decision gates

Return `consumer_found` only if a message (creator-authored, or with a
creator reply endorsing it) states or performs an operation that consumes
`401` and `400` and `73` together.

Return `selector_found` only if a message (creator-authored, or with a
creator reply endorsing it) names Roman-numeral filtering, the title's `C`
specifically, or otherwise forces the winning construction over its sibling
configurations.

Return `fefe_explained` only if class 1 reproduces `73` under the winning
rule with no new choice, or a corpus hit from classes 2-4 supplies an
explicit, sourced account of FEFE's `73` under any already-authenticated
construction.

If none of the three gates is met, return `remains_unconsumed` — the
Phase 448 disposition (`2/7` gates, no consumer) stands unchanged.

## Required outputs

- the exact result of applying the winning rule to FEFE (class 1), stated as
  pass/fail against `73`;
- the complete standalone-numeral and Roman-form hit lists (classes 2-3),
  every hit inspected, not summarized away;
- the complete phrase-corpus hit list (class 4);
- creator-authorship/reply status for every hit;
- an exact statement of what new evidence would reopen the gap, unchanged
  from `GSMG_OPEN_GAP_REGISTRY.md` unless a gate is met.

## Stop rules

- No new cipher menu, decoder, password generation, blob/address oracle,
  brute force, GPU, Docker, network, or external agent.
- The corpus pass is a single fixed-keyword sweep over already-authenticated
  export data; no per-hit follow-up search beyond reading the matched
  message's own thread (reply parent/children already in the export).
- A community (non-creator, non-creator-endorsed) hit cannot itself satisfy
  any gate; it may only be recorded as context.
