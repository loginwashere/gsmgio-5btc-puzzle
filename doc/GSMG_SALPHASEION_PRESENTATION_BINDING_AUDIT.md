# SalPhaseIon presentation-binding audit

Phase 219 found that the missing evidence is a binding to a FAED decoder or a
specific DBBI/FAED relationship. The page's presentation layer was therefore
checked before proposing another content transform.

The authenticated HTML capture has SHA-256
`b13cbc5c2935dc3e9ff8bf71681f2ef61317fefdce04159129877244a92a3947`.
Its puzzle body is minimal: an `H1`, one textarea for SalPhaseIon, a second
`H1`, and one textarea for Cosmic Duality. Both textareas have the identical
inline declaration `width: 100%; height: 200px`. Neither has an ID, class,
name, `wrap`, `rows`, `cols`, data attribute, color, or event handler. The
only authored document CSS sets the body's font to Arial; there is no linked
stylesheet. The sole external script is Cloudflare's telemetry beacon, not a
puzzle interaction.

More importantly, the entire 1,075-character normalized SalPhaseIon stream is
one textarea text node. Its 2,149 source characters are exactly the logical
characters separated by one ASCII space. It contains zero authored newlines.
All twelve known segment boundaries—including DBBI → binary
`matrixsumlist`, binary instruction → FAED, FAED → `z`, and decoded
`thispassword` → `z`—have precisely the same single-space separator as every
within-segment character. There is no nested markup inside the textarea and
no boundary-specific whitespace.

Cosmic Duality supplies a useful control on the same page: its textarea has
27 authored newlines producing exactly 28 lines of 64 characters. The author
therefore did preserve a fixed-column layout when one was intended. No such
layout exists in SalPhaseIon. Apparent rows in a screenshot are soft wraps
caused by the percentage-width textarea, viewport, font metrics, and browser;
they cannot authenticate a column, alignment, or pairing rule.

Verdict: presentation supplies no DBBI/FAED or FAED/`thispassword` binding.
The page-order relation from Phase 218 remains valid, but cannot be upgraded
into a decoder selector using rendered alignment, color, DOM grouping, or
source formatting. The next search must move to a different authenticated
artifact rather than mine browser-dependent wrapping.
