# Phase 484AL exploratory FAED width-30 `{g,i}` protocol

Date: 2026-09-10

## Question

Does the fixed Phase 484AI width-30 raw-symbol VIC/checkerboard pipeline produce
readable plaintext on FAED when the escape pair is `{g,i}`?

## Frozen scope

- Input: the repository's 570-symbol `data.FAED`, SHA-256
  `066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`.
- Width: exactly 30 (19 rows, exact grid).
- Escape pair: exactly ordered pair `("g", "i")`.
- Search schedule: the complete canonical schedule exported by
  `phase484ai_width30_early_switch_full_solve.py`; its canonical JSON hash is
  pinned in the execution lock.
- One execution only. No other pair, width, transposition variant, or budget is
  eligible in this run.
- The wrapper supplies FAED directly to every search stage. A sentinel order
  and plaintext exist only because the development helper APIs expose
  synthetic diagnostic fields. Those fields never control the now-truth-blind
  search and are excluded from the real result.

## Decision and limits

A readable, coherent plaintext is a positive candidate requiring independent
cryptographic and semantic verification. Gibberish is an exploratory miss,
not a negative against the model: the current fixed schedule recovered exact
top-1 order on only 2 of the first 3 full non-training development fixtures,
and no holdout power gate has run.

No solver tuning is permitted from FAED output. Any later modification must be
motivated and evaluated on synthetic development data without using FAED
scores or text as its optimization target.

## Pre-execution launcher amendment

The first locked invocation failed before candidate generation or FAED scoring:
the real-input adapter also intercepted and rejected the fixed synthetic
training-fixture requests needed to build the invariant models. No pipeline
artifact or score was produced. The superseded lock hash and this reason are
pinned in the replacement lock. The adapter now passes only development
training indices 3..12 to the original pinned fixture provider, supplies FAED
only for the sentinel real-input request, and rejects every other request.
