# Phase 540 — fresh-context agent insight pilot

Status at creation: protocol, written before any agent was started and before any
agent-generated candidate exists. The dossiers, prompts and this protocol are
hashed into `tools/gsmg/phase540_pilot_lock.json` before the first agent runs.

## Question

Earlier stages of the puzzle were solved by recognizing a meaning (a riddle answer,
a song lyric, a product name) and then verifying it against an oracle. Our sweeps
generated mechanical products of known strings instead. Can independent
fresh-context agents, given only the puzzle's own artifacts, generate
interpretation-type passphrase candidates, and does the oracle confirm any? A
second question, answered by two retro-controls: can such agents recover the
known answer of an already solved stage from that stage's page alone?

This is a method pilot. It is not a claim that any candidate is correct, and no
candidate is promoted by agent agreement.

## Design (frozen)

**Main round (6 agents, one round).** Each gets the same history-free dossier
(`_work/phase540_pilot/dossier_main.md`: stage clues and answers as the solver saw
them, the decrypted texts, the final page's stream layout and on-page macro
message; no project phases, no negative results, no chat or creator statements
outside the pages) and a different lens and model.

| Agent | Lens | Model |
|---|---|---|
| A1 | literal reader: only what is visible on pages and texts, simple recombination | sonnet |
| A2 | Matrix trilogy scholar: scenes, characters, quotes, props | opus |
| A3 | creator-style modeler: predict the creator's derivation from the solved chain | fable |
| A4 | wordplay and riddle specialist: acronyms, anagrams, homophones, hidden words, literal extraction of the named phrases | opus |
| A5 | semantic reader of the on-page macro message and "half and better half" | sonnet |
| A6 | minimalist: shortest plausible answers, one to three words | haiku |

Each writes at most 250 JSON lines `{candidate, clue, reading}` to
`_work/phase540_pilot/out/<agent>.jsonl`, using only the dossier, no network, no
other files, and states a distinct reason per candidate (no case or spacing
variants).

**Retro-controls (2 agents).** Same output format, at most 150 candidates, one
solved stage each, dossier limited to that stage's page as originally seen:

- **R1** (sonnet): the Phase 2 page and its URL. Known answer `causality`.
- **R2** (opus): the eight icon fragments of the seed page. Known answer
  `theflowerblossomsthroughwhatseemstobeaconcretesurface` (lyric line, normalized).

Retro success is the known answer appearing among the candidates after
normalization to lowercase letters and digits. Two controls are an anecdote, not
a rate.

## Pipeline and exact bar

1. Collect only the agents' output files. Drop empty lines, non-JSON lines, and
   candidates over 200 characters. Deduplicate by exact string.
2. Report per agent: lines written, unique candidates, and the share already
   covered by Phase 523's tested-material coverage (novelty), if computable
   without ad hoc changes.
3. Run every unique main-round candidate through the GPU oracle (image
   `gsmg-gpu-oracle:phase524-kt`, 60-variant table, all four tracked blobs,
   `--newline-variants`, Bloom raw-key arm, Phase 331 known-target detector).
   Required run hygiene as in Phase 524 run 3.
4. **Exact hit:** any strong or structural record or known-target match. Weak
   rows are reported and classified with the Phase 524 method and do not count.
   Retro candidates are checked only for the known answer, not run through the
   oracle.

## Stop rule

One round, one prompt per agent, no second round, no re-prompting from the
oracle result, no cherry-picking of candidates before the run. Zero exact hits
closes only this pilot. Agent agreement, plausibility and cleverness are not
evidence. An exact hit is a candidate password for separate validation.

## Non-claims

The agents' knowledge of the Matrix films and general culture comes from their
training, not the puzzle's artifacts. That is the same general knowledge a human
solver uses and is treated as part of the closed-system premise for this pilot.
A negative does not bear on any operation-type hypothesis.

## Reproduction

Prompts and the shared template are in `tools/gsmg/phase540_pilot_prompts.json`;
dossiers are rebuilt by `tools/gsmg/phase540_pilot_build.py`; the evaluation is
`tools/gsmg/phase540_pilot_eval.py`.
