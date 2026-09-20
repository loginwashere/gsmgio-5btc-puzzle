# DBBI prime-scaffold conditional diagnostic

Written before running the new diagnostic, 2026-09-20.

Question: does DBBI's reported `{b,e}` checkerboard preference provide evidence
beyond the prime-host structure already reconstructed in Phases 53 and 525?

The hypotheses must be separated. A string can contain `b` / `be` at prime
logical positions without being a straddling-checkerboard encryption. Testing
against uniform independent letters does not distinguish those explanations.

Use both complete prime-host parses, 83 and 84 logical tokens. Keep every
prime-position host and its exact `b` versus `be` choice fixed. Permute only the
non-prime symbols, preserving their exact multiset. Reassemble the raw string.
These controls have the same length, raw histogram, and a guaranteed copy of
the observed host grammar; they need not have exactly the same number of
alternative parses. Do not select controls on their checkerboard outcome.

For each parse generate 10,000 controls with independent seeds 534083 and
534084. Also run 10,000 unrestricted exact-histogram shuffles with seed 534091
as a diagnostic baseline. Use the existing Phase-106/113 code-IC statistic:
absolute distance from 0.067, with all 36 unordered escape pairs eligible.

Record `{b,e}` segmentation validity, unique-first rank frequency (ties do not
count), distance at least as close as observed, and the best distance over all
pairs at least as close as the real family maximum. Invalid `{b,e}` parses are
retained as failures, never silently dropped. Report the valid denominator too.
This is a conditional, exploratory diagnostic, not a discovery p-value or an
independent proof of the fitted prime grammar. No decryptions or passwords.

Separately count symbols in the host and non-host rails. Raw histogram
statistics cannot change under these permutations; they therefore cannot be
counted as independent corroboration of the checkerboard interpretation.

Checks: reproduce both historical parses byte-for-byte; preserve the host
positions and exact raw multiset for every generated control; independently
cross-check tokenization and IC against the existing checkerboard code; verify
that a planted non-checkerboard prime-scaffold fixture satisfies the grammar.

Interpretation fixed in advance: frequent rank-one `{b,e}` or ordinary observed
IC under the conditional controls weakens its use as *independent* cipher
evidence. It does not rule out a checkerboard layer or change any recorded
decryption negative. Either outcome leaves FAED's independent statistics
untouched. The useful next search target is whichever structure remains after
subtracting the already-explained scaffold, rather than automatically mirroring
`{b,e}` into a presumed second board.
