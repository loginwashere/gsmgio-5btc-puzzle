# Phase 541 — fresh-context agents, round 2: derived facts and operation proposals

2026-09-20. Result: **bounded negative; 0 exact hits from 12,633 bases and 6,979 key-shaped strings**.

## Question

Phase 540 closed round 1 for its dossier. Its reopen condition was a changed dossier or
a new constraint. Round 2 gave six fresh agents the closed-system objects this project
reconstructed (prime-host parse and payload strings, the image's 25 events, the 31-letter
selection, the Selection A matrix, the Bifid reading of FAED, size coincidences) and
asked each for operation proposals as executable code with a named check, plus
passphrase candidates. Protocol:
[doc/Brainstorms/2026-09-20 - Phase 541 ... Protocol.md](Brainstorms/2026-09-20%20-%20Phase%20541%20Fresh-Context%20Agent%20Round%202%20Protocol.md).
The dossier, data file, prompts, harness and protocol were hashed into a lock before the
first agent ran; it verified before collection.

## Design

Six agents, one prompt each: classical cryptographer (B1, opus), grid and addressing
(B2, sonnet), numbers and bases (B3, sonnet), text extraction (B4, opus),
consumer-first (B5, opus), interpretive reader (B6, sonnet). Up to 10 proposals
(`run(data)` Python) and 150 candidates each. Proposals ran exactly as written in an
isolated process under an import whitelist, static checks, resource limits, an empty
environment and no file writes. This is a guard against accidents, not a security
boundary against adversarial code. Failures would be recorded, never repaired.

## Results

| Agent | Proposals | Ran OK | Outputs returned | Tried as passphrases | Candidates |
|---|---:|---:|---:|---:|---:|
| B1 cryptographer | 10 | 10 | 990 | 724 | 141 |
| B2 grid | 10 | 10 | 3,053 | 3,053 | 148 |
| B3 numbers | 10 | 10 | 4,824 | 3,358 | 115 |
| B4 extraction | 10 | 10 | 690 | 690 | 145 |
| B5 consumer-first | 10 | 10 | 2,310 | 2,206 | 147 |
| B6 interpretive | 10 | 10 | 2,355 | 2,355 | 126 |

All 60 proposals passed the static check and ran without error, which shows the
interface was usable. The per-proposal cap (1,000) and per-agent cap (6,000) trimmed
B1, B3 and B5.

**Bases.** 12,633 unique bases, 12,191 not in round 1. Against Phase 523's SALPH coverage
map, 12,284 (97%) were new, 147 partially covered, 66 covered only in letters form, 136
fully covered. String novelty is higher than round 1's 68% because operation outputs are
mechanical strings rather than phrases.

**Key-shape scan** (64-hex, WIF, BIP39, raw halves via the project's classifier) of every
returned string and candidate: 6,979 key-shaped strings, 0 matches against the eleven
target hash160s (prize in both encodings, halving address, eight EC neighbors), 0
Bloom-context hits. Several proposals (brainwallet-style SHA-256 keys of puzzle phrases,
hash splices, decimation-derived base-9 scalars, rabbit-grid bit reads) targeted this
check directly.

**Oracle arm.** The GPU tool read 12,593 bases (it trims lines and skips any starting
with `#`; 40 ASCII-noise strings were skipped and 21 were trimmed), expanded to
386,685 passphrase forms on the 60-variant table against all four tracked blobs (image
`gsmg-gpu-oracle:phase524-kt`, `--newline-variants`, self-test passed, Bloom cache
loaded, eight known targets folded in). **Strong 0, structural 0, known-target 0.**
Weak-tier rows: 23, all re-derived (0 padding failures, 0 z-score mismatches) by the
Phase 524 method, none key-shaped. That rate matches earlier sweeps and is expected
noise. One stream-mode Bloom hit on COSMIC was a false positive after the API check
(the derived address has no history); the derived-address query sends addresses, not
keys or passphrases. Wall time about 10 minutes.

## What the pilot supports

- Fresh-context agents can produce runnable operation proposals from derived facts
  (60 of 60 executed) and 12.6 thousand mostly new candidate strings in about 15 minutes.
- Several proposals restated families the project has already closed (Nihilist, Playfair,
  checkerboard, Bifid, matrix sums, base-9 scalars) despite the "already tested" list. I did not
  audit which of the rest are new mechanisms: the 97% figure measures string novelty against
  earlier password coverage, not mechanism novelty. None opened a blob or matched a target.
- Agents tested their code only on data typed from the dossier; the real data shapes
  were handled, because nothing failed.
- No proposal produced a self-verifying intermediate. This bounds only this dossier,
  these six lenses, and one round.

## Scope and stop

One round, one prompt per agent, no repair, no second prompt from any result. This
closes round 2 for this dossier. A round 3 needs a changed dossier or a new constraint
(for example a new artifact, or a specific operation type chosen in advance), not more
agents or wider lenses. Nothing here bears on any fact about a blob, key or address.

## Reproduction

```bash
python3 tools/gsmg/phase541_round2_build.py
python3 tools/gsmg/phase541_round2_exec.py --self-test
python3 tools/gsmg/phase541_round2_exec.py --collect      # verifies the lock first
python3 tools/gsmg/phase541_round2_exec.py --verify-oracle
# weak rows: phase524_slot_grammar_sweep_prep.classify_weak(<phase541.hits.jsonl>) from tools/gsmg
```

The GPU run uses the Phase 524 run 3 recipe on `_work/phase541_round2/bases.txt` (digest
in `phase541_round2_result.json`); its outputs are gitignored. Agent outputs, the
per-proposal execution summary and the dossier are in
`tools/gsmg/phase541_round2_outputs/`.
