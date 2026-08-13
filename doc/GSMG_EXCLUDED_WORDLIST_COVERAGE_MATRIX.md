---
type: audit
phase: 255
date: 2026-08-13
status: closed
result: negative
disposition: structural-only
evidence_level: solver-derived
topics:
  - candidate-corpus
  - wordlists
  - openssl
  - seed
related_phases:
  - 44
  - 81
  - 83
  - 90
  - 94
  - 116
  - 144
  - 164
  - 174
  - 192
  - 253
  - 254
script: tools/gsmg/excluded_wordlist_coverage_audit.py
aliases:
  - Phase 255
---

# GSMG Excluded-Wordlist Coverage Matrix

## Result

Phase 254 established why 23 of the 46 on-disk wordlists are outside the
historical 648-candidate loader. “Excluded” does not mean “untested”: some
files feed the medium tiers, some have dedicated audits, some are raw inputs,
and several are generated outputs rather than independent sources.

The important current gap was narrower. None of those consumers uses Phase
253's opt-in `OPENSSL_MENU_GAP_CIPHER_VARIANTS`. A bounded union of six small,
candidate-like excluded files was therefore run against Blowfish-CBC,
Camellia-CBC, and SEED-CBC under all 20 declared KDF/cipher combinations and
all four tracked blobs:

```text
files:                    6
active source lines:      627
ordered exact candidates: 625
candidate digest:         854bffab41ecb1ef
scheduled evaluations:    17,163
unique passphrases:        16,101
cipher/KDF variants:       20
tracked blobs:             4
concrete decryptions:      1,373,040
strong hits:               0
```

This closes the new menu-gap family for the six selected lists. It does not
promote raw chat/OCR/screenplay corpora or generated medium outputs into a new
large sweep.

## Coverage matrix

“Derived” means that the source fed a later generator or selector; it does not
claim every raw source line was tried verbatim. The phases shown are the latest
load-bearing completed coverage, not every phase that ever mentioned a file.

| Excluded source | Handling / consumer | Recorded direct or derived coverage | Phase(s) | Phase-253 menu gap |
|---|---|---|---|---|
| `anchor_x_vocab_combos.txt` | Medium Tier 2 input | Derived candidates: padded binary CBC/ECB against SALPH/P32TRAILING; nopad windows; full-medium literal raw-key run against SALPH/COSMIC/P32TRAILING | 90, 144, 164 | Deferred: 5,576 generated lines |
| `chat_mined_lines.txt` | Filtered medium Tier 3 input | Selected derivatives reached the full-medium literal raw-key run; 63,565 raw lines were not exhaustively promoted | 164 | Deferred raw corpus |
| `chat_mined_words.txt` | Filtered medium Tier 3 input | Selected derivatives reached the full-medium literal raw-key run | 164 | Deferred broad corpus |
| `chat_theme_content_words.txt` | Medium Tier 2 input | Derived candidates: padded binary CBC/ECB, nopad windows, literal raw key | 90, 144, 164 | Deferred: 2,622 generated lines |
| `chat_theme_lines_raw.txt` | Intermediate raw source; no direct candidate consumer | No claim that every raw line was swept | — | Not selected |
| `content_word_filtered.txt` | Medium Tier 2 exact input | Padded binary CBC/ECB, nopad windows, literal raw key | 90, 144, 164 | **Run here** |
| `cosmic_duality_book_candidates.txt` | Medium Tier 2 exact input | Padded binary CBC/ECB, nopad windows, literal raw key | 90, 144, 164 | Deferred: 2,091 derived lines |
| `cosmic_duality_book_full_text.txt` | Primary-text input to targeted book/checkerboard tools | Targeted transformations only; no claim every raw line was a passphrase | multiple | Not selected |
| `cosmic_duality_book_p6_11_candidates.txt` | Medium Tier 2 exact input | Padded binary CBC/ECB, nopad windows, literal raw key | 90, 144, 164 | **Run here** |
| `cosmic_duality_book_p8_9.txt` | Medium Tier 2 exact input | Padded binary CBC/ECB, nopad windows, literal raw key | 90, 144, 164 | **Run here** |
| `cosmic_duality_book_screenshot_ocr.txt` | Normalized into medium Tier 1 | Line/reduction derivatives: padded binary CBC/ECB, nopad windows, literal raw key | 83, 94, 164 | Deferred raw OCR |
| `jacque_fresco_candidates.txt` | Dedicated exact-list audit | All four blobs; legacy/extended CBC, AES-ECB, AES-CFB/OFB/CTR, AES Key Wrap; newline forms | 88–90 | **Run here** |
| `looking_forward_candidates.txt` | Dedicated audit plus medium Tier 2 | Dedicated all-four-blob legacy/extended CBC and AES Key Wrap without newline forms; medium binary/nopad/raw-key coverage | 44, 90, 144, 164 | **Run here**, including newline forms |
| `matrix_architect_scene_through_choice_words.txt` | One-line cache consumed as 1,326 selector words | Salt-selected outputs, bound to supplying blobs: legacy/extended CBC, AES-ECB/stream/Key Wrap; later includes URLBLOB | 174, 192 | Not a literal candidate list |
| `matrix_script_windows.txt` | Fixed-stride filtered medium Tier 3 input | Selected derivatives reached literal raw-key coverage; 464,586 overlapping windows were not swept flat | 164 | Deferred raw corpus |
| `matrix_scripts_words.txt` | Filtered medium Tier 3 input | Selected derivatives reached literal raw-key coverage | 164 | Deferred broad corpus |
| `medium_curated_all.txt` | Generated union | All tiers under literal raw-key AES/3DES against SALPH/COSMIC/P32TRAILING | 164 | Not rerun as a 66,433-candidate union |
| `medium_curated_provenance.txt` | Generated JSONL sidecar | Metadata only, never candidate input | 81 | Not applicable |
| `medium_curated_tier1_primary.txt` | Generated Tier 1 | SALPH/P32TRAILING padded binary CBC/ECB and nopad windows; literal raw key through combined union | 83, 94, 164 | Deferred large tier |
| `medium_curated_tier2_derived.txt` | Generated Tier 2 | SALPH/P32TRAILING padded binary CBC/ECB and nopad windows; literal raw key through combined union | 90, 144, 164 | Six small component files sampled here; full tier deferred |
| `medium_curated_tier3_broad.txt` | Generated Tier 3 | Literal raw key through combined union | 164 | Deferred broad tier |
| `safenet_luna_hsm_candidates.txt` | Dedicated exact-list audit | All four blobs; legacy/extended CBC, AES-ECB, AES-CFB/OFB/CTR, AES Key Wrap; newline forms | 116 | **Run here** |
| `session_combined_for_chain.txt` | Medium Tier 2 input | Derived candidates: padded binary CBC/ECB, nopad windows, literal raw key | 90, 144, 164 | Deferred: 8,036 generated lines |

## Bounded menu-gap scope

The six files were selected before the run using mechanical boundaries:

- each is candidate-like rather than raw chat/OCR/full text or a generated
  medium output;
- each contains at most 236 active lines;
- four are the small exclusions highlighted during Phase 254 review;
- the remaining two are comparably small exact Tier-2 book/content lists;
- the Architect scene cache is excluded because its single physical line is
  semantically 1,326 selector words, not one passphrase candidate.

Source accounting in fixed order:

| Source | Local exact | New exact | Prior duplicate |
|---|---:|---:|---:|
| `content_word_filtered.txt` | 236 | 236 | 0 |
| `cosmic_duality_book_p6_11_candidates.txt` | 219 | 217 | 2 |
| `cosmic_duality_book_p8_9.txt` | 36 | 36 | 0 |
| `jacque_fresco_candidates.txt` | 55 | 55 | 0 |
| `looking_forward_candidates.txt` | 19 | 19 | 0 |
| `safenet_luna_hsm_candidates.txt` | 62 | 62 | 0 |

The passphrase expansion exactly matches Phase 253:
`answer_forms(candidate)` followed by newline-aware `keystr_forms()`. The
20 variants are Blowfish-128, Camellia-128/192/256, and SEED-128, each under
legacy MD5/SHA-1/SHA-256 and PBKDF2-HMAC-SHA256 at 10,000 iterations. Every
evaluation targeted current `BLOBS`: SALPH, COSMIC, P32TRAILING, and URLBLOB.

## Judgment

The six-list negative is worth recording because it closes a real code-level
coverage gap at essentially the same scale as Phase 253. It does not justify a
full medium-corpus menu sweep. Most remaining volume is generated expansion or
raw community/screenplay/OCR material, and Blowfish/Camellia remain weakly
motivated while SEED's clue support has already received the strongest exact
candidate treatment.

No candidate-level `sweep_priority` taxonomy is needed for this decision: the
run was bounded directly by file semantics, active-line count, and prior
coverage. Revisit classification only if a future expensive cipher hypothesis
has a stronger local selector.

## Reproduction

```bash
python3 tools/gsmg/excluded_wordlist_coverage_audit.py --self-test
python3 tools/gsmg/excluded_wordlist_coverage_audit.py
python3 tools/gsmg/excluded_wordlist_coverage_audit.py --menu-gap-sweep
```
