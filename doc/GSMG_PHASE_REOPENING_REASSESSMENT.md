# GSMG Phase Reopening Reassessment

## Purpose

This note asks a narrow question: after later corrections and newly recovered
evidence, which earlier negative phases should be reopened under a materially
different model or better-supported parameter choice?

A phase is not reopened merely because its result was negative. Reopening
requires at least one of:

1. a later phase changed a load-bearing input;
2. the historical run used a now-invalid oracle or target configuration;
3. a bounded, clue-supported scope was never executed.

## Highest-Priority Reopening

### FAED `{g,i}` under the VIC-style chain-addition model

This is the strongest justified computational reopening.

The historical large chain-addition run predates both the corrected AES oracle
and per-target escape-pair support. It therefore did not establish the current
question: whether FAED, segmented with its own `{g,i}` pair, carries a
VIC-style additive keystream.

Later evidence materially changes the prior:

- Phase 112 ranks FAED `{g,i}` first among all 36 escape pairs by distance of
  the segmented-code IC from English.
- The same phase reproduces that selection across three independent
  1,000-trial calibration seeds.
- Phase 113 closes only a **single-layer monoalphabetic English
  substitution** under `{g,i}` (`p=0.0396` against the token-preserving null).
  It does not close an added VIC-style keystream layer.
- `chain_addition_sweep.py` has puzzle-specific mechanical motivation:
  Phase 3.2 already uses VIC/checkerboard machinery, and FAED's unusually low
  raw IC was the original reason this added-layer model was proposed.

The rerun should be narrower than the old backlog:

- target only FAED;
- test only `{g,i}` in both escape/digit orders;
- retain the existing pre-checkerboard base-9 and post-checkerboard base-26
  branches and both signs;
- use the established 338,905 alphabet candidates and 17
  `single_fragments.txt` keystream seeds;
- do not add `{h,e}`, DBBI, new transforms, or new wordlists.

Before a multi-hour run, the driver should be hardened to current project
standards. Its present `--alpha-skip` mechanism is not an exact checkpoint,
and its append-only hit output is not fingerprinted. Add:

- a source/config/candidate fingerprint;
- exact checkpoint/resume by candidate index or digest;
- single-parent checkpoint/hit writes;
- explicit completed/error counts;
- deterministic synthetic positives for both pre and post branches;
- the current strong/weak oracle logging behavior.

This is a **model reopening**, not merely dictionary completion.

## Secondary Background Coverage

### `-nopad` binary-key-material sweep over curated Tier 2

The padded binary-material sweep completed both Tier 1 and Tier 2. The
separate `-nopad` fixed-window sweep completed only Tier 1:

- Tier 1: 24,554 base candidates / 525,436 keystrings, complete and negative;
- Tier 2: 10,590 puzzle-derived candidates / 209,178 keystrings, not run under
  `-nopad`.

The optimized multiprocessing driver already exists and has been reviewed.
At measured Tier-1 throughput, Tier 2 is roughly a 20-30 minute background
job, not a new research direction.

This is defensible because the output-shape hypothesis is creator-clue-adjacent
(`PRIVATE KEYS BELONG TO HALF AND BETTER HALF`) and Tier 2 is a frozen,
provenance-tracked candidate set. It remains lower priority than the targeted
FAED chain-addition test because it expands candidates without changing the
negative Tier-1 model.

## Lower-Priority Coverage

### Large autokey continuation

The unrun `[54,250,338,905)` continuation remains real coverage. Later
support for `{g,i}` improves its relevance slightly, but autokey still has
only thematic motivation; its own module describes the model as not selected
by prior puzzle evidence.

If run at all, narrow it to FAED `{g,i}` rather than reproducing the old
DBBI/`{h,e}` continuation. Run it only after the chain-addition result, and
only after adding the same fingerprinted exact-resume safeguards.

## Phases That Should Stay Closed

- **FAED monoalphabetic recovery under `{g,i}`:** Phase 113 used a proper
  token-preserving null and a pre-registered stopping rule. Do not rerun for a
  friendlier seed or larger trial count.
- **Prime-walk mask consumption:** Phases 48-51 corrected the boundary and
  tested the bounded selected/complement, zero-rendering, matrix, rail,
  `[23,16,7]`, and keyed-columnar family. Reopen only if primary evidence
  supplies a new operator.
- **Exact-mask zeroing:** later exact-mask and bit-4 tests close the obvious
  replacements. The creator's plural wording does not license arbitrary bit
  positions or replacement alphabets.
- **Adjacent difference:** linear lag 1 is negative. Circular and longer lags
  remain untested but have no later selector.
- **Complete-book 312-variant structural sweep:** complete OCR keyword and
  duality-motivated transform subsets are already negative. The remaining
  generic structural axes should wait for evidence from physical pages 57-58.
- **Optional DBBI matrix routes:** row-major 7x13/13x7 is identity and already
  covered; the remaining routes add unsupported reversal/serpentine/column
  choices.
- **`anstoo` 103-to-196 geometry:** no exact width/fill rule was recovered.
  Do not search layouts until one is sourced.
- **SafeNet/Luna/HSM, SoWut, Fresco, SALVATION literals, dates, Phase-4 text
  differences, QR metadata, icons, and external archives:** their corrected,
  bounded audits are negative and no later evidence changes their inputs.

## Primary-Evidence Priority

Physical *Cosmic Duality* pages 57-58 remain the highest-value missing
artifact. Recovering them would outrank every compute expansion because they
could select an operation or passphrase family rather than merely enlarge a
search.

## Recommended Order

1. Recover physical book pages 57-58 if access is possible.
2. Meanwhile, harden and run FAED `{g,i}` chain addition as the highest-value
   computational reopening.
3. Run `-nopad` Tier 2 as background coverage.
4. Consider FAED `{g,i}` autokey only if the first three add nothing.

Everything else should remain closed pending new primary evidence.
