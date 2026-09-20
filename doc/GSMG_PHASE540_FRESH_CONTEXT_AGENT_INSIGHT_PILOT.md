# Phase 540 — fresh-context agent insight pilot

2026-09-20. Result: **bounded negative; 0 exact hits from 848 agent-generated candidates**.

## Question

Earlier stages were solved by recognizing a meaning (a riddle answer, a lyric, a
product name) and then verifying it against an oracle. Our sweeps generated
mechanical products of known strings. Can independent fresh-context agents, given
only the puzzle's own artifacts, generate interpretation-type passphrase
candidates that the oracle confirms? Two retro-controls ask whether such agents
can recover a solved stage's answer from that stage's page alone. Protocol:
[doc/Brainstorms/2026-09-20 - Phase 540 ... Protocol.md](Brainstorms/2026-09-20%20-%20Phase%20540%20Fresh-Context%20Agent%20Insight%20Pilot%20Protocol.md),
with dossiers, prompts and scripts hashed into the lock before the first agent ran
(the lock was intact at evaluation).

## Design

Six main-round agents read one history-free dossier (stage clues and answers as the
solver saw them, the decrypted texts, the final page's layout and on-page macro
message; no project phases, no negative results, no chat) through different
lenses: literal reader (A1), Matrix scholar (A2), creator-style modeler (A3),
wordplay specialist (A4), semantic reader of the macro message (A5), minimalist
(A6). Two retro-control agents saw only one solved stage each: the Phase 2 page (R1,
answer `causality`) and the seed page's icon fragments (R2, answer the Logic lyric
line). One prompt each, one round.

## Deviations, disclosed

- **A3 model.** A3's first attempt on Fable 5.1 failed before writing anything
  (monthly spend limit, HTTP 429). It was rerun once on Opus with the identical
  locked prompt. The recorded A3 output is the Opus run.
- **Length filter.** One A1 candidate exceeded the pre-registered 200-character cap
  and was dropped.

## Results

| Agent | Lines | New after dedup | Not previously covered | Already covered |
|---|---:|---:|---:|---:|
| A1 literal | 203 | 202 | 113 | 73 |
| A2 Matrix | 245 | 219 | 197 | 47 |
| A3 creator-style | 246 | 140 | 164 | 76 |
| A4 wordplay | 202 | 76 | 133 | 65 |
| A5 semantic | 223 | 92 | 133 | 76 |
| A6 minimalist | 178 | 119 | 135 | 42 |

848 unique exact strings (805 after case and spacing folding). "Not previously
covered" is Phase 523's classification against the SALPH tested-material map
(fast sources): of 1,296 candidate lines, 875 were new, 11 covered only in letters
form, 31 partially covered, and 379 (29%) were already fully covered by earlier
sweeps. The counts are per line, so they include duplicates across agents.

Lens diversity paid off in non-redundant candidates. Thirteen candidates were
proposed by all six agents and 121 by three or more, but each agent had many
unique ones: A2 183, A6 115, A3 95, A5 83, A4 67, and only 39 for the literal
reader A1. Pairwise overlaps ranged from 13 (A2-A6) to 97 (A1-A5, A3-A4).

**Oracle arm.** All 848 bases expanded to 16,713 passphrase forms on the 60-variant
table against all four tracked blobs (image `gsmg-gpu-oracle:phase524-kt`,
`--newline-variants`, self-test passed, Bloom cache loaded, eight known targets
folded in). Strong 0, structural 0, weak 0, keyshape records 0, known-target
matches 0. Wall time 2 minutes.

**Retro-controls.** R1 (Phase 2 page) produced `causality` at rank 1 out of 80, but
its own report says the answer came from its memory of the puzzle, not from the
dossier, which only supports Matrix-themed fragments. R2 (seed page) produced 150
candidates, including "can you dig it" and "logic", and did not produce the lyric
line. Two controls are an anecdote, and R1 is contaminated by memorization, so
neither measures insight.

## What the pilot supports

- Fresh-context agents give a large, diverse, mostly new candidate set at low cost:
  1,296 lines and 848 unique strings in about 15 minutes.
- Two facts limit it: the agents are trained on this puzzle's public material, so
  a recovered answer can be recall; and 29% of what they propose repeats what
  our sweeps already tested.
- No interpretation-type candidate opens any blob. This bounds only this dossier, these
  six lenses, and one round.

## Scope and stop

One round, one prompt per agent, no second round, no re-prompting from the oracle
result. This closes the pilot, not the interpretation track. A further round needs
something new: a changed dossier (a new artifact or clue reading), or a specific
constraint on which readings to generate. More agents on the same dossier, or
wider lens lists, are not on the table.

## Reproduction

```bash
python3 tools/gsmg/phase540_pilot_build.py        # rebuilds the dossiers and prompts
python3 tools/gsmg/phase540_pilot_eval.py --collect --retro --novelty
python3 tools/gsmg/phase540_pilot_eval.py --verify-oracle
```

The GPU run uses the recipe of Phase 524 run 3 on `candidates_main.txt`, outputs
in `tools/gpu_oracle/output_local/phase540.*` (gitignored). Agent outputs, the
candidate list and the result summary are in `tools/gsmg/phase540_pilot_outputs/`
and `tools/gsmg/phase540_pilot_result.json`. The agent outputs contain only
candidate phrases and readings, no key material.
