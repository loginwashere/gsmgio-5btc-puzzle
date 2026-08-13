---
type: audit
phase: 254
date: 2026-08-13
status: closed
result: partial
disposition: structural-only
evidence_level: solver-derived
topics:
  - candidate-corpus
  - wordlists
  - provenance
  - openssl
  - seed
related_phases:
  - 22
  - 53
  - 79
  - 253
script: tools/gsmg/curated_candidate_corpus_audit.py
aliases:
  - Phase 254
---

# GSMG Curated-Candidate Corpus Audit

## Result

The phrase **“648 curated candidates” is technically accurate but easy to
misread**. It does not describe 648 candidates individually selected in one
review. It is the exact-string union, in fixed load order, of 23 accumulated
wordlist files plus two in-code seed sources.

The files were curated in the limited sense that they are small, previously
distilled research sets rather than raw dictionaries or mined chat corpora.
They do **not** all have equal evidentiary strength:

| First-source bucket | Candidates | Share | Meaning |
|---|---:|---:|---|
| Direct | 98 | 15.1% | Creator/page text or mechanically fixed puzzle values |
| Bounded | 243 | 37.5% | Limited interpretations of real clues or primary artifacts |
| Thematic | 225 | 34.7% | Matrix/book/wiki/religious vocabulary with weak local selection |
| Mixed | 82 | 12.7% | Legacy lists combining several evidence levels |

This is a descriptive load-order field, now exposed as `first_source_tier`,
not a candidate priority. Each candidate also reports every distinct
`source_tiers` label carried by its sources. The labels are not one ordinal
evidence scale: `mixed` means heterogeneous material, `control` means a known
solved value, and even files historically called `direct` can contain
researcher-generated representations of direct anchors. No `min()` or `max()`
across these labels is treated as a principled candidate classification.

## Exact corpus identity

| Scope | Candidates | Ordered-list SHA-256 prefix |
|---|---:|---|
| Original extended-cipher corpus | 648 | `2d233645ef49a141` |
| Phase-253 SEED scope | 650 | `ab8252005a8388f5` |

The SEED scope appends exactly:

```text
SEED
IZLKESEEDQPPEN
```

They were absent from the original 648 despite `SEED` occurring in the
authenticated `theseedisplanted` URL and in the recovered historical
`IZLKESEEDQPPEN` construction.

## Source-by-source accounting

“Active” excludes blank and comment lines. “New” counts exact strings first
introduced at that point in load order. Case, spaces and punctuation remain
significant during this exact deduplication.

| Source | Tier | Active | Unique locally | New | Already present | Why selected |
|---|---|---:|---:|---:|---:|---|
| `last_command.txt` | direct | 16 | 16 | 16 | 0 | Authenticated last-command/hash material and bounded terminal renderings |
| `salphaseion_own_keywords_combined.txt` | bounded | 48 | 48 | 48 | 0 | Permutations of four literal page tokens; ordering is unselected |
| `single_fragments.txt` | direct | 17 | 17 | 17 | 0 | Literal creator/page fragments used as alphabet or keystream seeds |
| `other_half_candidates.txt` | bounded | 22 | 22 | 22 | 0 | Cosmic Duality text connected to solved HALF AND BETTER HALF |
| `three_sexes_candidates.txt` | bounded | 12 | 12 | 12 | 0 | Plato/three-sexes source-text phrases |
| `hegel_marx_candidates.txt` | thematic | 14 | 14 | 14 | 0 | Dialectic and religious-duality vocabulary |
| `original_riddle_candidates.txt` | thematic | 24 | 24 | 24 | 0 | Researcher-written riddle imitations, not creator text |
| `discovered_paths.txt` | bounded | 49 | 49 | 48 | 1 | Archived paths and tightly related path/quote forms |
| `yellowblueprime_matrixsumlist_variants.txt` | direct | 25 | 25 | 25 | 0 | Authenticated anchors plus researcher-generated representation/order variants; the historical file bucket does not make every complete string literal creator text |
| `phrases.txt` | mixed | 83 | 83 | 69 | 14 | Legacy mixture of clues, solved text, titles, lore and chat phrases |
| `phrases-joined.txt` | mixed | 25 | 25 | 11 | 14 | Joined/normalized companions to the legacy phrase list |
| `riddle_combinations.txt` | bounded | 55 | 55 | 55 | 0 | Hand-bounded combinations of clue anchors and creator hints |
| `yinyang_matrix_symbolism.txt` | thematic | 20 | 20 | 20 | 0 | Matrix-franchise yin/yang interpretations |
| `architect_coded.txt` | thematic | 31 | 31 | 30 | 1 | Researcher-defined Architect/order vocabulary half |
| `architect_gnostic_synonyms.txt` | bounded | 47 | 47 | 22 | 25 | Gnostic expansion motivated by creator remarks |
| `architect_wiki_deepdive.txt` | thematic | 35 | 35 | 30 | 5 | Matrix wiki mythology and trivia expansion |
| `oracle_coded.txt` | thematic | 26 | 26 | 0 | 26 | Oracle/change half; adds no exact strings in current order |
| `matrix_trilogy.txt` | thematic | 114 | 114 | 103 | 11 | Broad franchise names, objects, places, ships and quotations |
| `blockchain_metadata_candidates.txt` | bounded | 22 | 22 | 22 | 0 | Verified address/transaction fields and clue-bounded halves |
| `first_piece_color_candidates.txt` | direct | 20 | 20 | 20 | 0 | Reproduced bits, RGB, hex, decimal and prime values |
| `matrixsumlist_choice_candidates.txt` | bounded | 14 | 14 | 14 | 0 | Exact reconstruction outputs plus narrow edge readings |
| `fefe_plated_seed_candidates.txt` | thematic | 4 | 4 | 4 | 0 | Four literal FE coatings from an unconfirmed rebus |
| `full_macro_clue_chain_candidates.txt` | direct | 30 | 27 | 20 | 7 | Creator-authored anchors plus researcher-generated pairs, cumulative prefixes/suffixes and full chain |
| `CORE_ALPHABET_SEEDS` | mixed | 11 | 11 | 2 | 9 | Reused in-code precedent list; only two entries are new |
| `VALIDATION_ANSWER` | control | 1 | 1 | 0 | 1 | Known solution, already present through `CORE_ALPHABET_SEEDS` |
| **Total base corpus** |  | **765** |  | **648** |  |  |

The largest single addition is `matrix_trilogy.txt` at 103 candidates. The
entire `oracle_coded.txt` file is redundant in this loader order. These are
not errors—the source membership can still document why a string was
considered—but they show why the raw file count is not a probability model.

Ninety-four candidates occur in more than one named source, and 64 touch
sources carrying more than one bucket label. The latter is reported as a
descriptive conflict, not resolved by choosing a supposedly strongest label.
For reference, the previously discussed 28 consists of 25 first-thematic
candidates also present in a bounded source, two first-bounded candidates also
present in a direct source, and the first-mixed validation answer also present
as a control. Calling these 28 “promotions” would require an unsupported total
ordering of the labels, so the audit does not perform one.

## Explicit inclusion/exclusion manifest

The directory currently contains 46 `.txt` wordlists: 23 are in
`CURATED_FILES`, and the following 23 are explicitly outside it. This is not a
freeze-date distinction. The loader and four of the five small files discussed
in review (`looking_forward`, book pages 8–9, Fresco, and SafeNet/Luna) were
introduced together in commit `6aaa220`; only the cached Architect scene was
added later. Exclusion therefore needs an affirmative reason.

| Excluded source | Active lines | Category | Why outside the 648 |
|---|---:|---|---|
| `anchor_x_vocab_combos.txt` | 5,576 | medium input | Large generated combinations incorporated into medium Tier 2 |
| `chat_mined_lines.txt` | 63,565 | broad input | Raw community messages |
| `chat_mined_words.txt` | 25,700 | broad input | Raw community vocabulary |
| `chat_theme_content_words.txt` | 2,622 | medium input | Generated theme reductions incorporated into medium Tier 2 |
| `chat_theme_lines_raw.txt` | 1,408 | broad input | Community-chat input to later filtering |
| `content_word_filtered.txt` | 236 | broad input | Intermediate filtered vocabulary, not a reviewed shortlist |
| `cosmic_duality_book_candidates.txt` | 2,091 | medium input | Large book-derived set incorporated into medium Tier 2 |
| `cosmic_duality_book_full_text.txt` | 1,128 | broad input | Primary-text extraction, not a password shortlist |
| `cosmic_duality_book_p6_11_candidates.txt` | 219 | medium input | Book-page derivations incorporated into medium Tier 2 |
| `cosmic_duality_book_p8_9.txt` | 36 | medium input | Page transcription incorporated into the medium workflow |
| `cosmic_duality_book_screenshot_ocr.txt` | 6,932 | broad input | Raw OCR normalized into medium Tier 1 |
| `jacque_fresco_candidates.txt` | 55 | dedicated audit | Separately swept in Phases 88–90 |
| `looking_forward_candidates.txt` | 19 | dedicated audit | Separately swept by `yin_yang_transition_audit.py` and included in medium Tier 2 |
| `matrix_architect_scene_through_choice_words.txt` | 1 | dedicated audit | One line caches 1,326 scene words for `salt_selector_permutation_audit.py`; it is not one candidate |
| `matrix_script_windows.txt` | 464,586 | broad input | Overlapping screenplay windows bounded by later filtering |
| `matrix_scripts_words.txt` | 7,594 | broad input | Broad screenplay vocabulary |
| `medium_curated_all.txt` | 66,433 | generated output | Separately digested and checkpointed combined medium corpus |
| `medium_curated_provenance.txt` | 66,441 | generated output | Provenance sidecar, not candidate input |
| `medium_curated_tier1_primary.txt` | 24,550 | generated output | Separately swept medium Tier 1 |
| `medium_curated_tier2_derived.txt` | 10,590 | generated output | Separately swept medium Tier 2 |
| `medium_curated_tier3_broad.txt` | 31,293 | generated output | Broad medium Tier 3 output |
| `safenet_luna_hsm_candidates.txt` | 62 | dedicated audit | Separately swept by `safenet_luna_hsm_audit.py` |
| `session_combined_for_chain.txt` | 8,036 | medium input | Large generated chain combinations incorporated into medium Tier 2 |

The script checks that every on-disk `.txt` file appears in exactly one side
of this manifest. Adding, removing, or silently moving a wordlist makes the
self-test fail until its scope decision is documented.

## Exact deduplication and actual oracle overlap

The loader removes only exact duplicates. Earlier draft accounting separately
removed non-alphanumeric characters while retaining digits, but that did not
match `answer_forms()`, which removes every non-letter—including digits.
Overlap is now derived from the exact newline-aware passphrase byte strings
actually scheduled through `answer_forms()` and `keystr_forms()`. In the base
corpus:

- 94 exact candidates occur in more than one named source;
- 104 connected oracle-overlap groups contain 245 candidates;
- 1,973 unique generated passphrases are produced by more than one exact
  candidate;
- `answer_forms()` and newline-aware `keystr_forms()` schedule 17,037
  candidate/form evaluations;
- those evaluations contain only 14,551 distinct passphrase byte strings;
- therefore 2,486 evaluations repeat a passphrase already generated elsewhere.

This repetition does not invalidate a zero-hit result, but “17,037 attempts”
is not the same as 17,037 distinct passphrases. For the revised 650-candidate
SEED scope, the corresponding values are 17,073 evaluations and 14,587 unique
passphrases.

## Review judgment

The corpus was reasonable for its original purpose: cheaply rechecking every
small research list when a new cipher/KDF oracle was added. It should not be
described as a ranked shortlist or as exhaustive evidence that 648 equally
plausible passwords failed.

For future work, keep the existing corpus immutable for reproducibility. Do
not use the file-level bucket labels as a `--tier` execution filter: their
categories are non-ordinal and several files mix literal anchors with generated
forms. If a future expensive cipher sweep needs prioritization, add one reviewed
candidate-level `sweep_priority` field with a rationale and regression tests at
that time. Until then, the audit reports provenance without manufacturing a
ranking.

## Inspecting every candidate

Summary and source accounting:

```bash
python3 tools/gsmg/curated_candidate_corpus_audit.py
```

Full ordered 648-candidate list, with all source memberships, all source
buckets, and the descriptive first-source bucket:

```bash
python3 tools/gsmg/curated_candidate_corpus_audit.py --list
```

Revised 650-candidate SEED list:

```bash
python3 tools/gsmg/curated_candidate_corpus_audit.py --include-seed --list
```

One exact candidate’s provenance:

```bash
python3 tools/gsmg/curated_candidate_corpus_audit.py --candidate matrixsumlist
```

Complete machine-readable report:

```bash
python3 tools/gsmg/curated_candidate_corpus_audit.py --include-seed --json
```
