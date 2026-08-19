# GSMG Medium Candidate Curation

> **Superseded (Phase 256, 2026-08-13):** the file-level tiering this doc
> describes was replaced by candidate-level `core`/`bounded`/`excluded`
> classification. See [GSMG_V2_CANDIDATE_REGISTRY](GSMG_V2_CANDIDATE_REGISTRY.md)
> for the current registry; this doc is kept for the provenance/volume
> reasoning behind the original 648-candidate default, which is still
> accurate.

## Purpose

The existing direct-blob rechecks use 648 deliberately small, previously
distilled candidates. The remaining `wordlists/gsmg` material contains about
575,000 additional unique lines, but most of that volume is not equivalent to
575,000 plausible passwords:

- `matrix_script_windows.txt` alone contains 464,586 one-word-sliding,
  heavily overlapping screenplay windows;
- `chat_mined_lines.txt` contains 63,565 community messages, including code,
  speculation, copied ciphertext, and unrelated conversation;
- raw OCR contains duplicated marginal text and recognition errors;
- several files are generated combinations of the same underlying phrases.

`tools/gsmg/build_medium_curated_candidates.py` builds a reproducible staged
corpus rather than treating all of those lines as one flat password list. It
does not modify `extended_cipher_recheck.CURATED_FILES`; the 648-candidate
default remains unchanged.

## Tier Rules

### Tier 1: Primary and High-Confidence

- all 648 existing curated candidates;
- every complete Cosmic Duality screenshot-OCR line in raw, letters-only, and
  validated content-word-reduction forms;
- all 80 indexed creator clue/confirmation messages;
- the community messages directly replied to by those creator messages;
- contiguous one-to-six-content-word n-grams from those Telegram exchanges.

This tier intentionally includes creator caveats and meta statements from the
audited index. Creator authorship does not make each phrase a likely password,
but it gives them stronger provenance than unrestricted community chat.

### Tier 2: Puzzle-Derived Combinations

Complete contents of the already-generated bounded derivation sets:

- `anchor_x_vocab_combos.txt`;
- `session_combined_for_chain.txt`;
- `chat_theme_content_words.txt`;
- the prior book candidate/reduction files;
- the Kenneth Keyes / Looking Forward candidate file.

These are not primary text, but each resulted from an earlier puzzle-specific
operation rather than generic dictionary mining.

### Tier 3: Filtered Broad Material

- standalone chat and Matrix-script words accepted by the installed English
  dictionaries, the known project vocabulary, cross-source occurrence, or a
  bounded two-to-three-word compound segmentation;
- chat lines containing a high-specificity puzzle anchor, or at least two
  separate generic clue anchors;
- Matrix screenplay lines from a fixed non-overlapping 15-word partition,
  restricted to Architect/Oracle/choice-scene vocabulary.

The fixed screenplay stride is important: the source contains 15 near-duplicate
sliding windows around each word. Keeping all matching windows would inflate
volume without adding comparable evidence.

## Current Output

Generated from the 2026-07-26 Telegram export and current local wordlists:

| Tier | Base candidates | Unique normalized passphrase byte strings | Cumulative |
|---|---:|---:|---:|
| 1 | 24,554 | 525,436 | 525,436 |
| 2 | 10,590 | 209,178 | 733,264 |
| 3 | 31,297 | 686,574 | 1,397,158 |
| **Total** | **66,441** | — | **1,397,158** |

Combined ordered-candidate digest:

```text
d5cedf48b254d195
```

Full-file SHA-256:

```text
medium_curated_all.txt:
a7168c9a43fd899b2a65ec9447febaea6118851f69a1ad518a824d49b412b4ce

medium_curated_provenance.txt:
4ec54fc8d4d785222f9950721e905179a98a0a671e04c23278c915b096bdaf2d
```

The generator reproduced both hashes exactly across separate process runs.
Every combined candidate is unique and has at least one JSONL provenance
record; 13,978 candidates have multiple supporting sources.

Generated local outputs:

```text
wordlists/gsmg/medium_curated_tier1_primary.txt
wordlists/gsmg/medium_curated_tier2_derived.txt
wordlists/gsmg/medium_curated_tier3_broad.txt
wordlists/gsmg/medium_curated_all.txt
wordlists/gsmg/medium_curated_provenance.txt
```

Wordlist outputs remain gitignored like the repository's other generated
candidate data. The generator and this methodology document are the
reproducible source artifacts.

## Compute Boundary

Using the measured binary-material CBC/ECB backfill throughput
(approximately 24.7 normalized keystrings/second for 72 operations per
keystring):

| Scope | Decrypt operations | Approximate wall time |
|---|---:|---:|
| Tier 1 | 37.8 million | 5.9 hours |
| Tiers 1–2 | 52.8 million | 8.3 hours |
| Tiers 1–3 | 100.6 million | 15.7 hours |

These estimates apply specifically to the two-target, 24-CBC-plus-12-ECB
binary-material sweep. CFB/OFB/CTR against four blobs is a different and
larger operation matrix and should not be silently bundled into the same run.

## Recommended Sequence

1. Tier 1 completed on 2026-07-27: 525,436 keystrings and 37,831,392
   decrypt operations in 6h12m, with zero hits.
2. No readable, structural, Bloom, or API-queue candidate was produced.
3. Tier 2 completed on 2026-07-27: 209,178 standalone keystrings and
   15,060,816 decrypt operations in 2h25m10s, with zero hits. Its 1,350-form
   overlap with Tier 1 leaves 733,264 cumulative unique keystrings.
4. Treat Tier 3 as unattended coverage, not an equally strong clue lead.
5. Do not add the full 464,586-window screenplay corpus or every raw community
   line unless new evidence specifically selects those source families.

Tier 1 was launched without changing the default corpus or overwriting the
completed 648-candidate checkpoint:

```bash
python3 tools/gsmg/binary_key_material_backfill.py \
  --candidate-file wordlists/gsmg/medium_curated_tier1_primary.txt \
  --checkpoint tools/gsmg/binary_key_material_tier1_checkpoint.jsonl \
  --hits tools/gsmg/binary_key_material_tier1_hits.jsonl \
  --queue tools/gsmg/binary_key_material_tier1_api_queue.jsonl
```

Both the binary-material and stream-mode drivers bind new checkpoints to the
exact candidate digest, blob digest, variant digest, `cb_common.py` source
hash, and driver source hash. Any oracle or driver edit therefore requires a
new checkpoint instead of silently reusing results produced by different
code. Stream-mode sweeps now also checkpoint each unique keystring and accept
the same literal `--candidate-file` input.

This curation improves passphrase coverage by roughly two orders of magnitude
while preserving source tiers and an explicit stopping rule. It does not turn
community speculation or OCR volume into creator evidence.
