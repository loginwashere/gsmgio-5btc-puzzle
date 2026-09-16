# Phase 506B top-five full width-19 runs

Date: 2026-09-14
Status: implementation in progress; execution lock not issued

## Frozen intent

The input pair set is exactly `selected_for_phase506b` from the completed,
locked Phase-506A result. The set is not manually edited. `{g,i}` is ineligible
because Phase 504 already searched it with this full pipeline.

Each selected pair receives the unchanged Phase-504 width-19 unrestricted-board
pipeline, schedules, board seed, English quadgram objective, and manual
readability decision. Runs are sequential and independently checkpointed. The
runner refuses pair indices outside the selected set and refuses to overwrite a
completed result.

No synthetic calibration claim is made. This is the bounded five-pair gamble
authorized by the user. If all five outputs are unreadable, execution stops and
the need for calibration is reassessed before any further pair is run.
