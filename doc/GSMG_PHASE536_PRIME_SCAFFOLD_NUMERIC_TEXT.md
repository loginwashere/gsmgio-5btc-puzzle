# Phase 536 — exact numeric-text generators inside DBBI's prime scaffold

Date: 2026-09-20. Result: **bounded negative; no full matches**.

## Question

Could DBBI be built by inserting its known prime hosts around a numeric
encoding of already-available text, with an unknown fixed digit substitution?
This is the first executable, closed generator family following the review of
Phases 534–535. It is exploratory, not a creator-selected recipe.

Phase 318 tested whole raw DBBI as a number. Phases 529–530 tested residue and
rail strings as passwords. This experiment instead tests an exact text-to-
residue-to-full-DBBI construction, preserving the terminal `e` in the 84-token
parse. No old negative is reversed.

## Frozen family

Nine local sources: the six Phase-482A documents (solved Phase 2, Phase 3,
Phase 3.2 pre-P32 material, Architect answer, referenced Architect scene, and
existing Cosmic Duality transcription), plus the solved 3.2.2 answer, Stage-0
URL, and Stage-1 flower credential. Documents remain separate. Each has two
ASCII-letter-only lanes, uppercase and lowercase, without J/I merging. Some
source material contains encoded sub-blocks; this is not all natural prose.

Three generators, forward direction only:

| Model | Numeric representation | Source lengths allowed by residue size |
|---|---|---|
| R9 | ASCII bytes as a big-endian integer, ordinary base 9 | 24 letters |
| D10 | Same integer, decimal | 25 letters |
| B9 | Each ASCII byte in three base-9 digits | 20 letters |

The registered 16–40-letter window range collapses to those lengths by exact
numeric bounds. Every possible fixed injective digit relabeling is covered by
equality-pattern matching; permutations need not be enumerated. A window must
use exactly nine distinct digits because both real residues use every `a..i`
symbol. The 60- and 61-symbol targets are both retained.

## Controls and execution lock

All seven mathematically possible model/case/residue-length cells recovered
their planted source window, digit mapping, and complete constructed raw
stream. Five of twelve cells are structurally impossible under the frozen
ASCII-letter normalization. Corrupted patterns, digit aliasing, and incomplete
tail input are rejected. These are exact recovery checks, not an estimate of
power for noisy encodings or unrestricted English plaintext.

The lock was written before the real matcher ran. It pins script, protocol,
test code, extraction dependencies, source files, normalized corpus hashes,
target strings, candidate counts, and the successful planted gate. Execution
recomputed and compared that complete lock.

Lock SHA-256:
`7cadc7400c2fbd5d2f2ce9c5cf5e76a31a4df21f6e1ef63b143cf587bb2a5b1d`.

## Results

| Quantity | Result |
|---|---:|
| R9 source/lane windows | 135,826 |
| D10 source/lane windows | 135,810 |
| B9 source/lane windows | 135,896 |
| Total encoded windows | **407,532** |
| Exact-length windows | 407,532 |
| Windows also containing exactly nine distinct digits | 213,288 |
| Complete symbol-pattern matches | **0** |
| Unresolved-blob oracle calls | 0 |

Counts are source locations and encoding cells, not necessarily unique text
strings. There were no near-match or language-score inspections and no family
expansion after the negative result.

## Scope and stop

The residue is not a digit-renamed instance of these three encodings of any
complete window in these nine normalized sources. That rejects this family,
not the entire prime-insertion hypothesis. Unseen text, punctuation-preserving
sources, byte order reversal, other encodings, or an additional cipher are
outside the experiment and do not become next steps simply because this one
failed. Reinsertion would only check internal consistency, not prove intention.

No generator has been promoted. The registered stop rule has been reached.

## Reproduction and review hygiene

```bash
python3 -m unittest tools.gsmg.test_phase534_dbbi_prime_scaffold_diagnostic \
  tools.gsmg.test_phase535_selection_a_matrix_composition \
  tools.gsmg.test_phase536_prime_scaffold_numeric_text
python3 tools/gsmg/phase536_prime_scaffold_numeric_text.py --run
```

All 12 dedicated tests for Phases 534–536 pass. `--run` verifies the existing
lock; `--prepare` refuses to overwrite one. The new scan and these tests need
no Downloads artifacts: they use Phase 525's pure parser, not its full
provenance audit. Phase 525's historical full audit still requires its pinned
Telegram/Atlas inputs, and its novelty comparators need historical run files.
Those dependencies were not silently removed or copied into the repository.

The original Phase 534 script/result and Phase 535 script/result were not
modified. Review qualifications are addenda; the independent fixed-grammar
rarity replay has its own script/result, with seed reuse explicitly disclosed.
The 534–536 work remains separate from the pre-existing uncommitted 525–533
material; no historical execution lock has been regenerated.

`python3 tools/gsmg/run_frontier_tests.py` runs both styles of frontier tests
with the standard library, including the four `tmp_path` cases. Unsupported
fixtures and an empty selection fail loudly. It does not claim general pytest
compatibility. The full default 525–536 selection retains legacy external/run-
artifact dependencies; `--start 534 --end 536` selects the new local checks.
