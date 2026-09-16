# Phase 506 FAED top-five escape-pair gamble

Date: 2026-09-14
Status: ranking implementation; execution lock not yet issued

## Decision

At the user's direction, this is a bounded real-data gamble rather than a
powered pair-identification experiment. It does not inherit a calibration
claim from Phase 505E: that pilot placed all three planted pairs in the top
three, but it was development-only and used only three rows.

Phase 506A scores real FAED under all 36 unordered escape pairs using the
unchanged Phase-505E depth-6 primary selector: the maximum unrestricted-board
normalised quadgram score after the pair-balanced invariant front end. It then
ranks pairs by descending score, with pair index as the deterministic tie
break. The already fully searched pair `{g,i}` is excluded after ranking. The
first five remaining pairs are the fixed Phase-506B run set.

Phase 506B will run the locked width-19 unrestricted full pipeline separately
and sequentially for those five pairs. Every pair gets its own atomic stage
checkpoints and result. Exact uppercase candidate bytes are retained for
manual readability review; no mutations or extra language models are added.

## Stop rule

If none of the five full runs produces readable plaintext, stop. Do not extend
to pair six, add seeds, or reinterpret the ranking. Reassess whether a powered
pair calibration is required before spending more compute.

## Scope

This tests only Model B, width 19, standard columnar geometry, the Phase-504
unrestricted-board pipeline and English quadgram objective. A miss does not
close other widths, transposition variants, checkerboard constructions,
objectives, or escape pairs outside the selected five.
