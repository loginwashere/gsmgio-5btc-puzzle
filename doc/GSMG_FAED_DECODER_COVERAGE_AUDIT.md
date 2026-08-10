# FAED decoder coverage audit

> **Phase-223 condition:** the FAED-as-`thispassword` role is a page-order
> hypothesis, not a proven post-yinyang step. BUT/HYE survives, but the mirror
> interpretation that placed it after `yinyang` is not distinctive.

Phase 218 made FAED plaintext the nearest live local role before
`thispassword`; it did not identify a decoder. This audit separates a real
untested hypothesis from the unlimited ability to add cipher parameters.

The live stream checkpoint reproduces exactly: FAED is 570 raw symbols,
SHA-256 `066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`.
The alphabet-independent code-IC ranking again puts `{g,i}` first of 36
escape pairs (IC `0.07429083623325952`), producing 436 tokens and all 25 code
types. This supports a checkerboard-like tokenization, but does not name its
alphabet or any layer above it.

The mechanically frozen registry in `faed_decoder_coverage_audit.py` keeps
the materially different prior families separate: plain monoalphabetic
recovery, standard digraphics, VIC-style chain addition, lag-1
self-synchronizing transforms, N=3/N=4 escape topologies, short-period raw
fractionation, and exact clue-derived operands. Their calibrated or bounded
negative results are not evidence that every conceivable cipher is closed.

One registered computation really is incomplete: Phase 18's large-dictionary
autokey continuation over alphabet indices `[54,250,338,905)`, 4,839,135
pairs. Phases 144 and 146 correctly left it deprioritized. Nothing on the
authenticated page, in the corrected BUT/HYE boundary, or in a solved stage
selects that dictionary, autokey convention, or range. It is therefore
unfinished compute, but not a clue-supported next experiment.

Likewise, circular adjacent differences, lags above one, arbitrary new
alphabets/periods/transpositions, and unspecified DBBI/FAED combination rules
remain imaginable. They are not bounded coverage gaps because the puzzle has
not supplied the parameter that would distinguish one from indefinitely many
neighbors.

Verdict: no clue-supported decoder model remains untested in the registered
FAED coverage. The next useful discovery must bind an authenticated artifact
to a FAED transform/alphabet or to a specific DBBI/FAED relationship. Until
that happens, spending hours finishing the dictionary-autokey continuation
would increase compute coverage without reducing the central ambiguity.
