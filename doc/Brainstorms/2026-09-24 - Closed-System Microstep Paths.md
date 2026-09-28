# Closed-system microstep paths — 2026-09-24

Status: brainstorm and test designs only. No new decode, statistical result, or
password claim is made here. This page uses the existing repository and its
authenticated artifacts; it does not require the restored website, a new hint,
or an internet lookup.

## What the creator's constraints actually imply

Messages 9607/9639/16624 say the information required for solving is already
available offline. Messages 9599/32579/39237 say that *after* reaching the
yin-yang phase, completion should be quick. The creator's two-sloppy-days
retrospective favors short, ordinary construction methods, but does not prove
one. Thus the best search target is a small missing **selection or recognition
step** that makes an existing operand and operation unambiguous, followed by a
fast exact check. It is not a license to try a larger password vocabulary.

The current obstruction is specific: `matrixsumlist` lacks an operation and
consumer; `lastwordsbeforearchichoice` and `thispassword` have unresolved
attachment; and no source requires DBBI and FAED to combine. Phase 546's broad
prefix class does not make exact `BTCSEED` ordinary, but no tail consumer has
been found. Keep all these alternatives live until an independent prediction
separates them.

## Path 1 — Recover the maker's *construction signature* from solved stages

**Idea.** The solved stages may expose accidental habits of the rushed maker:
how he serialized text, numbered positions, handled `J/I`, included whitespace,
reversed bit streams, or copied output from a cipher tool. Re-encrypting solved
plaintext and checking byte-for-byte against its known ciphertext can reveal
which quirks were actually used. A repeated quirk may then select one currently
ambiguous final-stage setting.

**Difference from prior work.** Phase 341 calibrated password assembly and
Phase 456 checked whether specific proposed unresolved rules transfer. This
would examine *authoring fingerprints* at the representation boundary, and
first demand exact reproduction on solved material. It should not infer a
general rule from a single solved example.

**Closed pilot.** Inventory only the three solved AES boundaries and the
already-reproduced first-piece/3.2 encodings. Freeze each boundary's original
bytes and a tiny menu of conventions already present in its own source code or
guide (case, spaces/newline, zero/one indexing, `J/I`, bit direction). Record
which convention reproduces each original byte string exactly. Promote a
convention for frontier use only if it is independently repeated in at least
two solved constructions *and* resolves a named live choice without adding a
new parameter. Otherwise stop at an authoring inventory. No blob oracle is
needed for the pilot.

**Risk.** Different stages may have been made with different tools. A common
habit would be a prior, not proof of the final operation.

## Path 2 — Determine whether FAED changes *regime* before decoding it

**Idea.** A 570-symbol object might be several concatenated pieces or use a
different setting partway through. A global English score and a whole-block
Bifid decode can miss that. Ask the smaller structural question: does the
native nine-symbol stream have one stationary generating process?

**Provenance.** The 2026-09-21 BTCSEED brainstorm listed a block-composition
scan as option 3 but did not execute it. Its informal 19-by-30 observation was
looked at after the fact and is not evidence. This path is a fresh, frozen test,
not a promotion of that observation.

**Closed pilot.** Use cuts at factors of 570 that leave at least 30 symbols on
both sides, their complementary cuts, and the independently existing
91-symbol DBBI length (also its complement). Score the maximum difference in
the nine-symbol distribution on either side of a cut and the maximum
within-row/column distribution difference over the exact rectangular factor
layouts. Correct over the *whole frozen family* using exact-multiset shuffles
of FAED. Before real scoring, verify recovery of planted distribution changes
of declared sizes and report the smallest detectable effect. A positive only
selects a boundary for a separate held-out test; it does not decode a word.
If family-corrected p exceeds 0.01, close this regime-change family and stop.

**Why it could matter.** A strong boundary could specify the missing scope or
period of an existing transform. A negative would save further attempts to
rescue the `BTCSEED` tail by arbitrary cutting.

## Path 3 — Let DBBI's own matrix supply a 19-position FAED key

**Idea.** A 7-by-13 DBBI layout has 19 diagonals; 570 also admits a 19-by-30
layout. The diagonal sums could order FAED's 19 columns. This is a compact
cross-object rule tied to `matrixsumlist`, rather than another free keyword.

**Provenance.** This is item 2 of the 2026-09-17 closed-system theory brainstorm,
explicitly deferred by Phase 517. It has not earned priority from the observed
data; its appeal is the exact 19-to-19 fit and the page order.

**Closed pilot.** Execute that document's 64 fixed diagonal-order keys over
the valid FAED escape pairs, with direction and ties included in the frozen
family. Use the existing planted-recovery check and a family-maximum shuffle
null. Corrected p <= 0.005 is only a structural checkpoint. Promotion to a
solve path requires an exact independent consumer, such as a preselected
output format or known address. No word fragment, best-looking row, or password
padding alone counts. If the gate fails, stop; do not add ragged layouts or
new numeric keys.

**Risk.** The 19 fit may be coincidental, and the matrix dimensions still
lack a creator-selected source for the 31-character selection.

## Path 4 — Audit *unconsumed native information* at each solved boundary

**Idea.** The extra door was found by revisiting an existing first-piece
artifact, not by obtaining a new URL. Instead of collecting all odd remnants,
trace exactly which authored bits/bytes were consumed at each solved boundary
and which were left visible. Search for a residual that is both structured and
adjacent to the unresolved macro step.

**Closed pilot.** Use only the original first-piece image, solved-stage
plaintexts/ciphertexts, the creator's 161-byte macro message, and the
authenticated SalPhaseIon page bytes. For each, record source provenance,
native bit/byte range, established consumer, and untouched complement.
Exclude generated transforms and community reconstructions from the candidate
pool. A candidate advances only if a rule selected from its *own* source
predicts an exact feature in a different authenticated artifact whose values
did not shape the rule. Since much of this corpus has already been seen,
record such checks as exploratory unless a genuine holdout exists. Otherwise
the result is an inventory, not a clue.

**Difference from prior work.** The gap registry tracks unresolved *claims*;
this would track unused *source material*. It may show that an apparent
frontier input is merely a checksum, or that a local source byte has never
been given a consumer. It must avoid rediscovering the heavily audited FEFE,
QR, page-wrap, and 31-character branches as though they were new.

## Path 5 — Check whether `23 / 16 / 7` counts progress or merely echoes film

The 2026-09-17 brainstorm's item 5 remains a deferred reading task. Make two
complete, explicit ledgers of the *already solved* chain: count operations per
stage and encrypted artifacts per stage, with each item tied to an actual
source/output. Compare each ledger to the Architect's 23 ciphers, 16
encryptions, and 7 passwords. If neither convention yields one stable residual
count, stop using the phrase as a progress meter. If one does,
it can constrain the number of remaining operations but cannot select their
parameters. This is cheap and should come after Path 1's exact stage inventory.

## Order and discipline

1. Path 1 and Path 4 are read-only provenance work; they have the best chance
   of revealing a missing selector without tuning to a target.
2. Run Path 2 as the first numerical pilot: it tests one structural premise
   and could decisively narrow FAED's scope.
3. Run Path 3 only if the original deferred protocol still passes an overlap
   check against Phases 514/518/520/521/538 and its planted control has power.
4. Use Path 5 as a bookkeeping constraint, not a cipher generator.

For every executed path, preserve the frozen candidate set, all outputs,
controls, exact success criterion and stop rule. A new address or exact key
match would be decisive; a short word, suggestive number, or uncalibrated
ranking would not.
