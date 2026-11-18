# FEFE as a control event: bounded investigation

Frozen before execution on 2026-09-30. Exploratory, not a new canonical phase.

## Question

Can the unique FEFE marker supply a concrete control operation in the established image-to-DBBI prime walk, rather than another numerical password operand?

Inputs: the authenticated Stage-0 image, the canonical DBBI and FAED strings, and the solved 91-character Stage-3.2.2 answer. Reconstruct the image events directly. Maintain zero-/one-based coordinate labels explicitly. No password, ciphertext, language-optimization, or web-route search.

## Fixed reference

There are 24 colored byte endpoints and one internal FEFE event, spatially sorted. Blue maps to `b`, yellow to `be`, FEFE to the exceptional `b` in the community recurrence. Event rank selects the corresponding successive prime; previous emitted digraphs shift the raw address by one each. The first 20 events precede FEFE. FEFE is event 21, source byte 21, and raw DBBI position 79 in the reference walk.

Reproduce the reference's 23 matching, fitting events, 31 selected raw positions, and selected answer. Also enumerate both complete DBBI prime-host parses independently of picture-event choice using the existing exhaustive parser.

## Closed model menu

Each rule is fixed here before its output is inspected. All rules retain the unchanged reference prefix before FEFE.

1. **Reference:** FEFE emits `b`; nothing else changes.
2. **Delimiter only:** reference addressing and tokens, but expose separate before/at/after-FEFE output pieces. This adds no constraint and cannot demonstrate a decoder change.
3. **Stop after FEFE:** consume its reference `b`, then stop. A shorter matching prefix is not success.
4. **Ignore marker:** remove FEFE completely; later event ranks shift down one.
5. **Silent prime slot:** FEFE advances the prime-event rank but emits nothing and adds no digraph width. This removes a constraint; compare, do not promote merely for matching.
6. **FEFE is a digraph:** emit `be` at FEFE and count its extra raw width.
7. **Swap after marker:** consume reference FEFE; then exchange blue=`b` and yellow=`be`.
8. **Mirror after marker:** consume reference FEFE; then apply the already-used nine-symbol mirror to token letters, giving blue=`h`, yellow=`he`.
9. **Binary after marker:** consume reference FEFE; then blue=`b`, yellow=`a`, both width one, in the same DBBI stream.
10. **Reset width correction:** consume reference FEFE; retain global prime ranks but clear accumulated digraph width.
11. **Restart at beginning:** consume reference FEFE; restart prime rank and width at the beginning of DBBI. Report rereading/collisions rather than treating reused symbols as fresh data.
12. **Restart in the remaining suffix:** consume reference FEFE; restart prime rank and width in DBBI immediately after the marker's consumed raw position. Local position 1 is the next raw character; the first new prime is local position 2. No offset search.
13. **Reverse remaining suffix:** consume reference FEFE; traverse the remaining DBBI suffix from its right end, restarting prime rank and width. Tokens are read in this descending traversal order. No reversal of each expected token.
14. **Switch to FAED, keep clock:** consume reference FEFE; later events address FAED with unchanged global prime rank and width.
15. **Switch to FAED, fresh clock:** consume reference FEFE; later events address FAED from its start with prime rank and width reset.
16. **Consume source byte once:** FEFE emits `b` as source byte 21's representative; suppress that same byte's later ordinary endpoint. Suppressed endpoint advances neither prime rank nor width. This is a single native source-byte rule, not a search over omitted endpoints.
17. **Consume byte once but keep suppressed slot:** same endpoint suppression, but its prime slot still advances. Separates grouping from timing.
18. **Pure no-host instruction:** FEFE emits nothing and advances no prime rank; suppress its byte's ordinary endpoint as well. Tests removal of the entire marked byte, rather than replacement by an exceptional host.

No combinations beyond this menu. Pure delimiter/stop/silent-slot models are deliberately included as weaker explanations, not competitors that can win by having fewer constraints.

## Outputs and evaluation

For every model retain all attempted event records, target stream, actual/expected tokens, raw coordinates, fits, collisions/reused positions, first divergence, exact matching prefix, and prefix answer projection when it stays in aligned DBBI coordinates. Show suffix records explicitly; do not rank by words in the projection. Distinguish omitted events, silent slots, stopping, and out-of-range events.

A decoder change is interesting only if it preserves the prior constraints and explains additional structure, such as a complete existing parse or the source-byte duplication, without freely selected offsets. A complete parse already has prior provenance; recovering it is not a new solve.

For the source-byte replacement model, compare its complete prefix tokens against both exhaustive parses. Expose any unhosted tail; do not force it into another event or automatically escalate to the already-tested matrix consumer.

## Location controls

Enumerate every zero-valued **internal** bit of the 24 decoded bytes (exclude colored LSB endpoints and the four leftover central cells). Move only the exceptional label to each such position in turn, leaving the underlying bits unchanged. Test both reference insertion and consume-byte-once replacement. Retain all matching-prefix summaries, group by source byte, and compare exact prefix hosts with both DBBI parses.

This is a counterfactual-location inventory, not a discovery p-value. Positions within the same byte may be observationally equivalent; disclose those equivalence classes. In particular, a byte-level control interpretation may select byte 21 without distinguishing which of its zero bits was specially marked.

## Prior coverage and stop

Reference insertion: Phase 48. Event metadata versus flat token strings: Phase 201. Both complete parses and Selection A: Phase 525. Completed Selection-A matrix and negative consumers: Phases 535, 542, 543. Literal FEFE-bit suffix reads: Phase 44, negative. Raw deletion/bit-zeroing and Fe-plated interpretation: Phases 41–42. These are not newly untested ideas.

The present extension is the explicit control-rule comparison and counterfactual-location inventory. If ordinary reset/switch rules fail, report that. If consume-byte-once reproduces Selection A, report the exact equivalence and its limitations. No oracle run follows merely from these results.
