# Phase 484O — Joint Board/Order Ceiling

Status: development ceiling test; no execution lock; no FAED or holdout use.

Phase 484N showed that GPU acceleration makes large width-19 beams practical,
but the board-invariant statistic loses planted segments at depth 12 even with
a 262,144-state beam.  The next model must use language information from the
checkerboard during order assembly.

The first test supplies the planted synthetic checkerboard as an explicit
oracle.  The existing invariant beam is used only through depth 8.  From depth
9 onward, each candidate segment is tokenized independently within each of the
30 rows, decoded with the planted board, and scored by the frozen 25-letter
English quadgram table.  Row boundaries are not joined while the segment is
incomplete because omitted columns separate them.  The score is normalized by
the number of within-row quadgram windows.

This is an upper-bound sensitivity test, not a usable blind solver.  If the
planted board cannot preserve the planted order, alternating board estimation
cannot rescue this objective.  If it does recover, the next development step
is a population of estimated boards alternated with the same GPU order step.

## Development outcome

The ceiling passed on fixture 23 in both board pools.  With the planted board,
the genuine segment moved to rank 1 immediately at depth 9 and the exact full
order remained rank 1 at depth 19.  On the vic-profile fixture, two disjoint
board swaps (84% slot accuracy) and four swaps (68%) both preserved the full
truth to rank 2.  Six swaps (52%) lost it immediately at depth 9.  The useful
basin therefore lies somewhere between these tested 52% and 68% conditions.

A follow-up partial-board probe annealed boards directly from the twelve true
depth-8 windows.  Under 4x10,000 proposals it recovered one exact board and
eight boards at or above 68% accuracy.  Under a cheap 1x2,000-proposal screen,
the best true window reached 84%; seven of twelve true windows scored above
all 200 random controls, with a 0.457-per-window gap between the true and
random maxima.

The next blind implementation is therefore bounded: apply a GPU coarse board
anneal to the invariant top 16,384 depth-8 fragments; retain a small population
of fragment/board pairs; refine their boards; extend each seed under its own
board-aware objective; then re-solve the board on each completed order.  This
must recover synthetic development fixtures before any holdout or FAED use.

## Phase 484Q implementation boundary

The first blind stage implements the invariant depth-8 shortlist and one
deterministic 2,000-proposal GPU board anneal per fragment. Before a full
development screen, a small synthetic batch must show PCG32 initial-board
parity and CPU recomputation of every returned GPU score. Population-retention
and order-extension rules remain development parameters until the coarse screen
shows where genuine fragments rank; they are not frozen in advance of that
measurement. Holdout fixtures and FAED remain prohibited.

## Phase 484Q fresh-development batch

The completed blind pipeline was evaluated on fixture indices 40--49 in both
board modes.  These indices had not appeared in the Phase 484N--Q development
artifacts when the list was fixed.  Of 20 fixtures, 17 retained at least one
genuine depth-8 segment (85%).  Fourteen recovered the exact order and
plaintext at rank 1: 14/17 conditional on shortlist retention (82.4%), or
14/20 unconditionally (70%).  Vic-profile and broad-random each recovered
7/10, despite retention rates of 8/10 and 9/10 respectively.

The six misses expose three distinct limits.  Fixtures vic-profile 41 and 48
and broad-random 45 lost every genuine segment in the invariant shortlist.
Broad-random 47 and 48 retained genuine segments at coarse ranks 3389 and 103,
outside the 64-fragment refinement cutoff.  Vic-profile 42 retained its true
segment at coarse rank 1 and refined rank 40, but outside the eight-seed
extension cutoff.  The design is therefore not eligible for a holdout lock.
The next development experiment may test wider refinement and extension
populations on these diagnosed misses, then must demonstrate the revised fixed
design on another fresh development batch before any holdout or FAED use.

Artifact: `tools/gsmg/phase484q_dev_batch_result.json`, SHA-256
`6bc97314c9b1410f2428bf748f5e4b4b6f03a57e264033096007d9918f6516c7`.

## Phase 484Q amendment Q1: path-stable annealing seeds

Capacity probing exposed an unfrozen implementation confound: the coarse CUDA
annealer derived each fragment's random seed from its array index.  Increasing
the shortlist therefore changed the annealing trajectory of an unchanged
fragment.  Before further development, the seed was changed to a deterministic
mix of the base seed, fragment depth, and complete ordered column sequence.
The same fragment now receives the same annealing starts regardless of
shortlist size or position.  CUDA/Python initial-board parity and score parity
pass; the maximum CPU/GPU score-recomputation error is
`7.993605777301127e-15`.

The original 40--49 artifact remains a faithful record of the old unfrozen
implementation but is superseded for solver calibration.  Re-running those
same already-open development cells with path-stable seeding and the original
budgets recovered exact order at top 1 in 15/20 cells.  The stable failure
loci were three invariant-shortlist omissions, broad-random 47 at coarse rank
461 (outside 64 refinements), and broad-random 49 at refined rank 14 (outside
eight extension seeds).

Artifact: `tools/gsmg/phase484q_dev_batch_path_seed_result.json`, SHA-256
`7e94460180532e3973b6dd9aa1bec42172a0c21ab62b9a5342c96f76fcd07dbc`.

## Revised capacity and untouched-development validation

Targeted work on the already-open 40--49 failures selected one fixed revised
configuration: a 262,144-fragment invariant shortlist, 8,192 refined
fragments, and 64 extension seeds.  It repaired vic-profile 41 and 48 and
broad-random 49.  Broad-random 45 remained a board-estimation failure: two
genuine fragments survived, but the best reached only 32% board accuracy and
refined rank 3089.  Broad-random 47 likewise remained below the demonstrated
board basin even when widened separately.  No further tuning followed before
the next batch.

The revised configuration then ran unchanged on untouched development fixture
indices 50--59 in both board modes.  All 20 retained genuine depth-8
fragments.  Nineteen placed the exact complete order in the terminal set and
ranked that order first: 10/10 vic-profile and 9/10 broad-random.  Seventeen
also recovered the plaintext byte-for-byte; two exact-order cases decoded at
99.25% and 99.37% character accuracy.  The sole order miss, broad-random 51,
retained 11 genuine fragments, but its best truth reached only 48% board
accuracy and refined rank 252, outside the fixed 64-seed extension set.

This is strong development evidence for the width-19 architecture, but it is
not a holdout result and does not authorize a FAED run.  A separately frozen
holdout gate must distinguish exact-order recovery (19/20 here) from literal
plaintext recovery (17/20 here) and must preserve the path-stable seed rule.

Artifacts:

- `tools/gsmg/phase484q_revised_tuning_result.json`, SHA-256
  `71a6dd4d1ae1374169317da059622ac8c1ac1cafafe35b100e086ecbdf54b70a`.
- `tools/gsmg/phase484q_revised_fresh_result.json`, SHA-256
  `0bc35299ca9d0246da5bbe0417283e30bb98e82f7a416829e958c2b24dd92bd2`.
- `_work/phase484q/coarse_board_server`, SHA-256
  `6253860b17f24a3725fe25d84d73afc942f867b5bb85381ccfef60f4b6623139`.

## Phase 484U exploratory FAED miss and investigation backlog

After the pair-fair high-capacity solver recovered a deliberately hard
broad-random development fixture, the user authorized a solve-first,
exploratory real run before the remaining pair-label calibration.  This was
not a holdout-qualified retirement experiment: a readable hit could have been
confirmed, but a miss is explicitly non-closing.

The width-19 run gave all 36 escape-pair hypotheses the same budget: 262,144
depth-8 fragments, 8,192 refined fragments, 256 board-aware extension seeds,
eight deterministic extension workers, beam 4,096, eight terminals per seed,
and four 10,000-iteration final board restarts.  All outputs were gibberish.
The family best was `{b,c}` at `-4.930466738915061` per quadgram; `{c,f}` was
second at `-4.935981287633309`, a gap of only `0.005514548718248413`.
The historically interesting `{g,i}` pair ranked 36/36 at
`-5.237870147034634`.  All 180 saved top-five candidates were independently
checked for valid order and board permutations, exact segmentation/plaintext
recomputation, score recomputation (maximum absolute error
`2.6645352591003757e-14`), and exact round-trip to the 570-symbol FAED stream.

Artifact: `tools/gsmg/phase484u_exploratory_faed_width19_result.json`,
SHA-256 `9712d9daae7c2188818684dc308d4540084b7ed2b3a16013d9bce319556f16aa`.

The miss leaves the following explanations open, in investigation order:

1. **FAED-profile power gap.** Synthetic calibration did not reproduce
   FAED's exact symbol histogram or its unusually concentrated inferred
   seven-single-slot share.  The previously quoted `0.62--0.658` range is
   reproducible from Phase 477A's hard-profile corpus
   (`GSMG_PHASE477A_TOKEN_COLUMNAR_TRANSPOSITION_AUDIT.md`, sections 5 and
   "Fixture concentration"), but it is not the Phase 484 calibration range.
   Regenerating the actual width-19 development fixtures at indices 40--59,
   61, and 62 for both planted-pair indices 0 and 34 gives single-slot shares
   of `0.515625--0.626506` in `vic_profile` and
   `0.131148--0.394366` in `broad_random`.  The two current `{g,i}` index-62
   fixtures are `222/396 = 0.560606` and `96/333 = 0.288288` respectively.
   FAED's direct `{g,i}` segmentation is `302/436 = 0.692661`, outside every
   Phase 484 development fixture measured here.  Under Model B that observed
   FAED fraction is an imported stress profile, not a true-order measurement.
   Build an exact- or closely matched-histogram synthetic pool and measure
   stage-by-stage recovery before changing the real search.
2. **Early loss of the unknown true path.** A correct path may have fallen
   outside the depth-8 shortlist, coarse/refined population, 256 extension
   seeds, or terminal beam.  Synthetic fixtures can localize this; FAED
   cannot because its true order is unknown.
3. **Wrong width or grid orientation.** Width 19 covers a `19 x 30` exact
   grid.  Width 30 is the complementary exact orientation and requires a
   generalized/recompiled joint solver.  The complete non-trivial exact-width
   list for 570 is 2, 3, 5, 6, 10, 15, 19, 30, 38, 57, 95, 114, 190, and
   285.  Excluding tested width 19 leaves 13 widths.  Complementary pairs are
   `2<->285`, `3<->190`, `5<->114`, `6<->95`, `10<->57`, and `15<->38`,
   with `19<->30`.  Orientation is structurally relevant, so the large
   complements are not removed merely because their small partner was tested.
   The earlier real width-10/15 run also used a weaker solver.
4. **Wrong transposition family (catalog only).** Possibilities include double or disrupted
   columnar transposition, a route/spiral order, alternating directions, a
   cyclic start offset, or separate transformations of two portions.  The
   arch/ring/`747474` observation remains motivation only, not a selected
   deterministic rule.  None of these variants is authorized for a parallel
   sweep.  A separate triage must first identify which variants are licensed
   by existing closed-system evidence and freeze a bounded candidate set.
5. **Token-level rather than raw-symbol transposition.** Phase 477A tested a
   bounded Model-A family, but its score-reach and exact-profile calibration
   limitations prevent full retirement.
6. **Different checkerboard mechanics.** The current model fixes seven
   singles, two one-symbol escapes, 18 double codes, 25 letter slots, and no
   null/control codes.  Stateful escapes, padding/nulls, control tokens, or a
   different omitted/merged letter would invalidate current segmentation.
7. **Non-prose plaintext objective.** Passwords, commands, addresses, hashes,
   abbreviations, mixed language, structured data, or another ciphertext may
   not provide the English quadgram basin required by this solver.
8. **Multiple FAED sections.** Two independently encoded halves, or payload
   plus key material, would make one global board and order an invalid
   compromise model.
9. **Boundary or padding mismatch.** A prefix/suffix outside the grid, null
   padding, a cyclic offset, or a split before transposition remains untested.
10. **The checkerboard-transposition hypothesis is wrong.** The direct
    `{g,i}` segmentation evidence may reflect a different code or coincidence.

One concrete objective improvement is reserved after calibration: combine
quadgram score with synthetic-only estimates of decoded length, single/double
code proportion, unigram concentration, and restart stability.  This may
separate coherent solutions from the pseudo-English that wrong pairs produce.
Its weights and decision rule must be developed and frozen without reference
to FAED, because the exploratory real output is now observed.

Before interpreting the FAED miss, finish the fresh pair-label calibration at
fixture index 62 with `{g,i}` planted and all 36 pairs searched blindly in
both `vic_profile` and `broad_random` modes.  VIC-profile recovered `{g,i}` at
rank 1 with exact order/plaintext and a `+0.4829352293636706` per-quadgram gap;
broad-random also recovered `{g,i}` at rank 1 with exact order/plaintext and a
`+0.15814612635661796` gap.  Pair-label bias is therefore not a supported
explanation of the exploratory FAED miss in either calibrated board mode.

## Phase 484W persistent extension optimization

The board-aware extension originally started one CUDA process per refined
seed.  An isolated persistent multi-board server now uploads the blocks and
quadgram table once per worker and accepts successive 25-slot boards and path
batches without recreating the CUDA context.  On the saved broad-random-51
256-seed reference population, eight persistent workers reproduced all 2,048
terminal records and every diagnostic exactly.  Runtime fell from the original
serial `273.95693017699523` seconds to `35.820351635018596` seconds, a
`7.64808042557489x` speedup.  This is also about `1.76x` faster than the prior
eight-worker, non-persistent measurement of `63.18953801700263` seconds.

Artifact: `tools/gsmg/phase484w_persistent_extension_benchmark.json`.
Full-pipeline integration subsequently reproduced every scalar outcome and the
canonical hashes of all six large deterministic structures (`true_records`,
`refined_population`, `terminal_orders`, `final_candidates`,
`skipped_terminals`, and `extension_diagnostics`) from the pinned
broad-random-51 reference.  Total wall time was `150.61974651899072` seconds;
extension time was `34.9375790769991` seconds versus the serial reference's
`273.95693017699523`, a `7.841325512944678x` stage speedup.

Artifact: `tools/gsmg/phase484w_full_pipeline_parity.json`, SHA-256
`5fe9524bb7527c75249b6983388f341e7c2afa93b2f0630b63c65e2705c6b7c8`.

## Phase 484X exact-profile diagnostic and corrected `{g,i}` rerun

The first backlog item was tested directly after the exploratory real miss.
The frozen diagnostic constants reproduce FAED's `{g,i}` marginal profile
exactly: 436 token classes comprising 302 single and 134 double codes, and the
same counts for all 25 codes and all nine raw symbols.  No FAED order or
adjacency information enters fixture construction.  Each plaintext begins as
a non-overlapping closed-corpus development passage and receives the minimum
number of score-aware substitutions required to match the token-count
multiset; the resulting planted scores remained in the normal English basin.

The original shortlist failed on all three first exact-profile fixtures:
`0/3` retained any true depth-8 window.  A profile-conditioned centroid
improved fresh recovery but remained unstable (`2/3` for both a five-fixture
and a ten-fixture training pool).  A two-centroid union at the same total
262,144-path budget also failed on fixture 14.  Depth diagnostics localized
that failure precisely: its best true raw-score ranks were 207, 221, 22,527,
210,084, and 910,973 at depths 4 through 8.  Thus truth survived the 262,144
cap through depth 7 and was removed by score rank—not the diversity selector—
at depth 8.

The bounded correction retained 262,144 paths through depth 7 and expanded
only the final depth-8 population to 1,048,576 before board-aware screening.
It rescued fixture 14 with exact order and 98.6% plaintext accuracy.  More
importantly, it recovered three untouched fixtures (16, 17, and 18) at rank 1
with exact order and 100% plaintext accuracy; they retained 8, 7, and 1 true
depth-8 windows respectively.  This demonstrates that the original real
`{g,i}` run was not calibrated for FAED's marginal profile.

A clearly labeled post-miss exploratory FAED rerun then used the corrected
profile model and asymmetric shortlist.  It did not solve.  The best score was
`-5.202558550866717` per quadgram, only modestly above the original `{g,i}`
cell's `-5.237870147034634` and far below the exact-profile planted range; its
449-letter output was frequency-shaped gibberish.  All 1,795 saved final
candidates were independently checked for valid order/board permutations,
segmentation and plaintext recomputation, exact FAED round-trip, and score
recomputation (maximum absolute error `3.019806626980426e-14`).

Artifact: `tools/gsmg/phase484x_corrected_faed_gi_result.json`, SHA-256
`b9406ca6b3c058fec376a1978a0247a84def32b12a0ec516281a161b37ec45fc`.

This remains a non-closing miss: the calibration was designed after observing
the earlier real miss, and the exact-profile fixtures use frequency-aligned,
minimum-edit English rather than an authenticated FAED plaintext family.  It
does, however, retire further width-19 `{g,i}` capacity scaling as the immediate
next action.  The next structural discriminator is the complementary exact
orientation at width 30, using synthetic power calibration before any real
run.

## Phase 484Y width-30 planted-board ceiling map

The complementary orientation swaps the 19x30 grid: each of the 30 columns is
now a fragment position and each row holds 19 raw symbols.  Before porting any
joint board/order machinery, this is the same kind of upper-bound sensitivity
test as 484O -- does the true column order, decoded through the true planted
`{g,i}` board, separate from noise at depths short of the full width -- run at
depths 8, 10, and 13 on six untouched exact-profile fixtures (indices 13--18)
against 50,000 deterministic random-order controls and every one-column
corruption of the true order at each depth (3,978--4,200 corruptions per
fixture per depth).

**Implementation confound found and fixed.** Porting 484O's board-score CUDA
kernel to width 30 exposed a latent indexing bug in the shared kernel
(`tools/gsmg/phase484o_board_score_server.cu`): the two-symbol escape code's
second digit was mapped to a board slot by treating `canonical_blocks`'s
pair-relative relabeling (`pair[0]->0, pair[1]->1`, remaining symbols in
absolute alphabet order -> 2..8) as if it were the absolute alphabet order
`slot_codes()` uses to lay out the board.  Those two orderings coincide only
for the `{a,b}` pair (canonical index 0), which is the only pair the existing
484O/Q/W/X development and ceiling fixtures use, so no prior result changes.
The new width-30 kernel targets the real FAED pair `{g,i}`, where they
diverge, and a CPU/GPU parity self-test caught it immediately (max error
`1.46`, not `1e-10`).  The fix adds an explicit canonical-to-absolute
`NEXT_INDEX` table, derived directly from `canonical_blocks`'s relabeling
rule rather than fit to pass the test; both the original `{a,b}`-width-19 and
new `{g,i}`-width-30 parity checks now pass at `4.4e-15` and `1.8e-15`
respectively. `phase484q_blind_joint_width19_solver.py`'s coarse-anneal and
extension stages were checked separately and are unaffected: they never
compare against the absolute-alphabet board, only against boards they
annealed themselves under the same (self-consistent) indexing, and the final
per-candidate decode re-derives slot indices independently in pure Python.
One related but unexercised risk was noted for later: `phase484q`'s
`screen_fixture()` computes a `board_accuracy` diagnostic by comparing a
true absolute-alphabet board against an annealed canonical-slot board, which
is only meaningful for pair `{a,b}`; nothing currently reads that field when
a non-`{a,b}` hypothesis pair is passed (`phase484s`/`phase484t`), so no
reported result is affected, but the field should not be trusted if that
changes.

**Result.** The true order beat every one of the 50,000 random controls at
every depth on all six fixtures (18/18 cells), with a per-quadgram-window gap
of `0.79` to `1.29` over the best random control. Against the far harder
one-column-corruption controls, the true order beat every corruption in 16 of
18 cells (5/6 at depth 8, 6/6 at depth 10, 5/6 at depth 13); the two
exceptions were narrow, single-corruption losses (fixture 18 depth 8, gap
`-0.015`, true order ranked 3rd of 4,049 pooled; fixture 17 depth 13, gap
`-0.001`, ranked 3rd of 3,979).

**Disposition.** The width-30 orientation preserves a strong true-order signal
under the oracle board at depths 8, 10, and 13, matching (and at these depths
exceeding) the width-19 ceiling's behavior before its depth-12 breakdown.
This clears the width-30 orientation to proceed to the same bounded next step
484O did: port the coarse-anneal/refine/extend/re-solve pipeline (484Q) to
width 30 and demonstrate it recovers synthetic development fixtures before
any holdout or FAED use. It does not by itself indicate where (or whether)
the width-30 objective degrades at greater depths, since only three sample
depths out of 30 were tested.

Artifact: `tools/gsmg/phase484y_width30_board_ceiling_13_18.json`, SHA-256
`ff07d98543aece1dd504fed766ca467f9512e87d454a6e827e2d95e1ce3e60ca`.

## Phase 484Y width-30 blind joint solver: first dev cells

The 484Q coarse-anneal/refine/extend/re-solve pipeline was ported to the
30-column orientation: a new per-fragment coarse-anneal kernel
(`phase484y_width30_coarse_board_server.cu`, geometry swapped from 484Q's) and
a new fixed-board extension kernel (`phase484y_width30_extend_board_server.cu`,
built from 484O's generic template with the default identity convention, not
the `{g,i}`-corrected one used only for the ceiling-map oracle) feed a new
`phase484y_width30_blind_joint_solver.py` that reuses the already-validated
depth-8 invariant shortlist (`phase484y_width30_feasibility_probe.py`) and the
existing, geometry-agnostic full-stream re-anneal
(`phase484q_full_board_server.cu`, reused unmodified). Unlike the width-19
solver, the escape pair is not blindly searched: it is fixed to `{g,i}`, since
that pair is a property of the raw stream, not the transposition orientation.

Porting exposed the same convention confound the ceiling map already
diagnosed: the coarse-anneal kernel indexes its board via
`canonical_blocks`'s pair-relabeled symbols with no absolute-alphabet
correction, so `phase484p_partial_board_recovery_probe.token_rows` (built for
the true `slot_codes()` convention) is the wrong CPU reference for it. A
`cpu_recompute` written against the wrong convention initially self-tested
with a 0.87-per-window error; a canonical-convention `cpu_recompute` fixed it
to `7.99e-15`, matching 484Q's own parity figure. A regression test now
asserts the two conventions differ for `{g,i}` so this cannot silently
regress. All 24 unit tests (13 new) and the CPU/GPU self-test pass.

Two dev fixtures were then run at full production scale (keep 262,144,
depth-8 final keep 1,048,576, 8x2,000 coarse restarts, 64-wide refine at
4x10,000, 8-seed/4,096-wide extension, 4x10,000 final resolve) -- the only two
of the five untouched fixtures probed so far (13, 14, 15, 16, 17, 18) that the
feasibility probe found retain a true depth-8 segment at all:

- Fixture 13: the true segment retained coarse rank 7,468 (score
  `-4.361503553451324`), well outside the 64-wide refine cutoff. It never
  reached extension.
- Fixture 16: the true segment retained coarse rank **1** and refined rank
  **1** (score `-4.026667421999068`) -- a clean, unambiguous top-rank
  recovery through refine. Extension from depth 9 to 30 then lost it: the
  8-seed/4,096-wide beam was saturating well before depth 30 (e.g. 15,020
  generated vs. 4,096 retained at depth 29), and the exact order never
  reappeared among the 64 extension terminals. The best final decode was
  fluent-looking fragments in an otherwise wrong stream (`...YSAYINGINTHE...
  MEXICAN...FROM...`), the same pseudo-English-from-a-wrong-board risk 484O's
  backlog already flagged.

**Disposition.** The port is mechanically correct -- fixture 16's rank-1/rank-1
result on a genuine true segment is strong evidence the coarse anneal and
canonicalization are wired correctly, not a coincidence -- but the pipeline
does not yet recover either tested fixture end to end. This is not evidence
against the width-30 orientation itself (the ceiling map already showed the
signal exists at these depths); it is an unturned pipeline, exactly the state
484Q was in before its own path-stable-seed and budget amendments. The
immediate next development step is diagnosing and widening whatever stage
loses fixture 16's segment during extension (wider beam, more extension
seeds, or a diversity-aware selector) before any further fixtures, holdout,
or FAED use.

Artifacts: `tools/gsmg/phase484y_width30_blind_dev_i13_k262144_f1048576.json`,
SHA-256 `c292a6b60e9428ab06b2fd5ca2bffe479a5d791543c52085b87b16df11dece8f`;
`tools/gsmg/phase484y_width30_blind_dev_i16_k262144_f1048576.json`, SHA-256
`b3d2a8b91b992fe80640a3390d5a3f911c832ab4ff3f7e70ea3b59b266d757f0`.

## Phase 484Y width-30 extension: beam width is not the bottleneck

Widening fixture 16's extension beam 8x (4,096 -> 32,768, same coarse/refine
inputs) did not recover the exact order, so a direct instrumented trace
replayed just the extension stage for the rank-1 refined true segment,
checking true-window membership before and after selection at every depth.
The true continuation survived cleanly through depth 13 (`true_pre` growing
2, 4, 6, 8, 10 as expected), then collapsed: at depth 14 all 10 still-live
true-consistent candidates were generated, but only 1 survived selection
(`true_post` 10 -> 1) among roughly 264,000 competitors; the last survivor
died by depth 16.

Widening the beam 4x further (32,768 -> 131,072) only bought one more depth
(death moved from 16 to 17) while generated-candidate counts exploded to the
millions (3.1M at depth 13). At depth 14 with this wider beam, 9 of 10
true-consistent candidates still lost to the top ~131,072 (about 15%) of
roughly 860,000 competitors. Beam width is therefore not the bottleneck: the
true continuation's fixed-board quadgram score is not competitive at this
specific depth range regardless of how much beam room it is given.

The most likely cause is board accuracy, not order search: the extension
board is annealed once from the depth-8 refine stage's roughly 150 quadgram
windows (30 rows x up to 5 windows) and then frozen for the entire depths
9-30 walk. 484O's own ceiling test already showed this orientation's
sensitivity to exactly this -- 84%-accurate boards preserved the truth to
rank 2, 68% also held, 52% lost it immediately -- and width 30 gives a
partially-wrong board roughly twice as many depths (22 vs. width-19's 11) in
which its errors can compound before the order search finishes. 484O's own
backlog anticipated this fallback: "a population of estimated boards
alternated with the same GPU order step," i.e. periodically re-anneal the
board using the windows accumulated so far during extension, rather than
freezing it at depth 8.

**Disposition.** Non-closing. The port is mechanically sound and the ceiling
signal is real, but the frozen-board extension design that worked for
width-19's shorter 9-19 walk does not carry cleanly to width-30's longer 9-30
walk. The next development step is not another parameter sweep on the
current design; it is testing whether a periodic (or continuous) board
re-anneal during extension keeps the true continuation competitive through
the depth-14-17 range before any further fixtures, holdout, or FAED use.

## Phase 484Y width-30 extension: rolling board re-anneal, a strong partial result

Implemented the fallback above directly: `extend_seed_reanneal` (new,
`phase484y_width30_blind_joint_solver.py`) replaces the frozen board at every
depth from 9 to 30 with an independent per-candidate anneal via
`gpu_multistart_screen` -- the same coarse-anneal kernel already used at
depth 8, called again at every subsequent depth instead of once. This needed
no new kernel; `run_extension_backend` now defaults to this ("reanneal"),
keeping the original frozen-board design ("frozen",
`phase484y_width30_extend_board_server.cu`) available for comparison. 17
unit tests (6 new) pass.

Re-running the same fixture-16 rank-1/rank-1 true segment through the new
backend, at the depth-8 refine stage's own anneal strength (4 restarts x
10,000 iterations per depth, beam 4,096):

- The true continuation held a stable single survivor for **9 consecutive
  depths** (14 through 22) before finally dying at depth 23 -- six to seven
  depths short of the finish, versus depth 16-17 for the frozen board at the
  same beam width, and versus depth 14 for the same reanneal design run
  under-powered (1,000 iterations, the first thing tried).
- Doubling the restarts (4 -> 8, same 10,000 iterations) produced an
  **identical** result -- same depth-by-depth survival counts, same death at
  depth 23 -- indicating restarts were already saturated; the true
  candidate's score is not held back by anneal randomness, but by anneal
  depth (iterations) or by a genuinely thin margin at that specific
  boundary. The shrinking `true_pre` count near the death point (2 -> 1) is
  expected geometry, not a bug: as the surviving window approaches an edge
  of the length-30 truth, only one of its two bidirectional extensions can
  still be a valid true window.

The default `REANNEAL_RESTARTS`/`REANNEAL_ITERATIONS` were set to 4/10,000
(matching the refine stage) rather than left at the first (weaker, 1,000
iteration) guess, since that guess is now known to perform worse.

**Disposition.** Recorded as a strong partial result, not a closed recovery:
reanneal-based extension is a real, substantial improvement over the frozen
board (roughly doubling the surviving depth range). The 4-vs-8 restart tie
shows that additional restarts at the tested seeds did not help; it does not
by itself prove iteration count is the cause. Iterations are the next
controlled lever, alongside a genuinely thin objective margin or selector
loss at that boundary. The solver has not yet been pushed far enough (or
combined with a beam widened specifically at the failure boundary) to
demonstrate full recovery. Further tuning is deferred rather than pursued
immediately, given the compounding per-step cost of testing higher iteration
counts (~30s/depth at 10,000 iterations for one seed already). The next
development step, when resumed, is either substantially more iterations or a
boundary-targeted beam widening, followed by a fresh dev-batch validation
(not just fixture 16) before any holdout or FAED use.

### Correction: depth-13 packed-key overflow and full recovery

The preceding frozen/reanneal extension survival claims are superseded. A
reproducible trace exposed an impossible condition (a true path ranked first
before selection but absent afterward). The cause was a 5-bit-per-column
`uint64` identity key inherited by the width-30 selector: it is collision-free
only through depth 12. At depth 13 and beyond it overflowed and silently
merged distinct paths. The selector now uses the packed key only through
depth 12 and exact row identity afterward; a regression fixture contains two
distinct depth-13 paths that collide under the old representation.

With collision-free identity, fixture 16 needs neither a wider beam nor more
iterations. At 4 restarts x 10,000 iterations and beam 4,096, the true path
survived every depth through 30, finishing extension rank 2. A fully blind
one-seed run selected the genuine depth-8 fragment at coarse/refined rank
1/1; the independent full-stream board solve promoted the exact order to
final rank 1 with plaintext accuracy 1.0 and an exact 570-symbol round trip.

Fixture 20 independently generalized this result. Its only retained true
depth-8 fragment ranked 16 after coarse screening and 2 after refinement. A
blind two-seed run extended score-ranked seeds 1 and 2; the exact order
finished extension rank 1 and final rank 1, again with plaintext accuracy
1.0 and an exact round trip. Thus the corrected extension is 2/2 on fixtures
whose true segment entered the 64-entry refined population. The remaining
bottleneck is earlier recall, not depths 9-30: across fresh fixtures 13-22,
only 3/10 retained a true depth-8 fragment, and fixture 13's true fragment
was coarse rank 7,468, outside the 64-entry refine cutoff.

Artifacts:

- `tools/gsmg/phase484y_width30_trace_i16_reanneal_rr4_ri1000_b4096_collisionfixed.json`, SHA-256 `df7a9027570c7b105640b09f07bac9ff5eec861f18f1f2fee47931d62c417e8d`.
- `tools/gsmg/phase484y_width30_trace_i16_reanneal_rr4_ri10000_b4096_collisionfixed.json`, SHA-256 `9dbfa54471a441a526857dc8c893f3793842b06f7fbadf70a5a16ae651e08526`.
- `tools/gsmg/phase484y_width30_blind_dev_i16_collisionfixed_reanneal_seed1.json`, SHA-256 `73638c8a473054e067a0fc5d143c253f7fe8216b2d066e33f085ed16f9057d05`.
- `tools/gsmg/phase484y_width30_blind_dev_i20_collisionfixed_reanneal_seed2.json`, SHA-256 `0a0e3c63d7914dcf51a78e64bfd52eaa23ab43fbde29810b1a0d863f38b931c5`.

## Phase 484Z row-held-out board fitting: development negative

A three-fold row-held-out objective was tested on fixture 15 to reduce the
short-fragment board overfitting exposed by the early depth-7/8 experiments.
The implementation fits a board on 12--13 of the 19 rows and scores it only
on the omitted rows, rotating all three folds. Against the same deterministic
panel of 23 true depth-8 windows and 400 uniformly random false paths, the
light CV budget improved median background exceedances (25 -> 12) but did not
improve standardized separation. Increasing the CV fit from 3 restarts x
2,000 iterations to 4 x 6,000 made every recorded rank statistic worse:
best/worst true rank 3/245 -> 6/339, mean exceedances 49.04 -> 65.87, and
median exceedances 12 -> 31. Using the explicitly stated background-standard-
deviation denominator, effect sizes are 1.398 for the full-row baseline,
1.384 for light CV, and 1.242 for boosted CV.

This is a negative for the row-CV implementation as an immediate scaling
candidate, not a formal closure of every held-out-board objective. It used one
development fixture and uniform random controls rather than the actual
shortlist's highest-scoring false paths. The first implementation also seeded
annealing by candidate list index and omitted the seed/pool identity and
per-candidate background scores from its compact artifacts. The code now uses
path-derived seeds and records those provenance fields for any future rerun;
the existing artifacts remain historical outputs and are not rewritten.

The next bounded diagnostic uses actual shortlist hard negatives and asks a
different question: whether independently annealed boards agree on decoded
letters more often for genuine paths. Only a positive, replicated development
result would justify a GPU-scale implementation or any holdout/FAED use.

## Phases 484AA/AB: hard-negative reliability objectives do not improve recall

The follow-up used fixture 16's actual one-million-entry depth-8 invariant
shortlist. An independently seeded one-restart board screen supplied the 400
highest-scoring false fragments; all 23 genuine depth-8 windows were then added
for diagnostic measurement. The resulting 423-path pool is pinned by SHA-256
`236f1594d67d1bff1857ee7a0eed351f7e0df1a92366900bca94d346499b246c`.

Eight independent 2,000-iteration board fits were first compared by their
token-frequency-weighted decoded-letter agreement. Agreement was worse than
the existing raw full-row objective: best/worst true rank 10/404 versus
1/421, median false paths ahead 102 versus 42, and standardized mean
separation 0.567 versus 1.083. Restart consensus therefore failed its first
development gate and was not replicated or scaled.

A second diagnostic fitted each real fragment and two deterministic within-row
token shuffles with paired path/control-derived annealing seeds. Subtraction of
the mean optimized null score improved upon that experiment's weak CPU
observed-score comparator (median false paths ahead 151 -> 145; standardized
separation 0.111 -> 0.502), but remained substantially worse than the existing
GPU raw objective on the identical pool (median 42; separation 1.083). It too
failed the development gate and was not replicated or scaled.

These are bounded development negatives for the two stated reliability
statistics, not evidence against width 30. Together with the planted-board
rank-1 ceiling at depths 7 and 8, they sharpen the remaining problem: the true
board/order signal exists, but allowing every short fragment an unconstrained
25-letter board creates false optima that neither row-CV, restart agreement,
nor token-shuffle normalization removes. A next objective must reduce or share
board freedom rather than merely renormalize the same independent fit.

Artifacts:

- `tools/gsmg/phase484aa_width30_stability_i16_h400_r8_n2000.json`, SHA-256
  `057794c812b3291884cc66530a1f65620cc1635a0505ff18fc4936d26ba73cc7`.
- `tools/gsmg/phase484ab_width30_null_margin_i16_c2_r3_n2000.json`, SHA-256
  `13dc121f5ee9b6d65266a55cf2679c521d0c89ec00aa43fdcabe0f4f05f6b60e`.

## Phases 484AC/AD: partition constraint and parent-reserved bridge

The exact-profile and VIC-profile fixture generators already freeze a useful
board constraint: the seven single-digit slots encode the training corpus's
seven most frequent letters (`E,A,T,I,O,N,S` in the generator's frozen
ordering), while the remaining eighteen letters occupy only double-digit
slots. Phase 484AC therefore anneals permutations within those two groups and
never swaps a letter across the single/double boundary. This reduces board
freedom from 25! to 7! x 18! without importing FAED or holdout data.

On actual depth-8 shortlist hard-negative pools for development fixtures 13,
15, 16, and 20, the constrained CPU objective improved the best genuine rank
against both the matched unconstrained CPU fit and the historical GPU score.
Best true ranks were 1, 5, 1, and 1 on the 400-hard-negative panels. The CUDA
port passes exact initial-board parity, partition checks, window-count parity,
and returned-board score recomputation to `2.7e-15`. An apparent CUDA score
failure during validation was a checker bug: the returned wire board was
`uint8`, causing overflow in NumPy's base-25 quadgram-key arithmetic. Casting
to `int64` before recomputation fixes it and is regression-tested.

Fixture 15 is the hard end-to-end development case. With 3 restarts x 2,000
iterations, the constraint moved its genuine depth-7 fragment from invariant
rank 656,072 to 180,915, inside the 262,144 cut. At depth 8 the genuine rank
was 1,098,233, narrowly outside the old 1,048,576 capacity; widening only that
cut to 1,310,720 retained it. A 4 x 10,000 constrained re-fit improved it to
218,117, after which fixed 262,144 rolling selection produced ranks 77,317 at
depth 9 and 45,288 at depth 10. It then suffered a sharp global rank collapse
to 1,174,176 at depth 11 and was lost.

That collapse is cross-parent competition, not a locally wrong extension.
Across all genuine parents at depths 8--11, a correct child ranked no worse
than 40, 24, 15, and 5 respectively among its own siblings. The exact retained
depth-10 parent for fixture 15 ranked 45,288 globally and its correct child
ranked 7 of 40 locally. Phase 484AD therefore froze a small bridge: retain the
top 65,536 parents, score their children, and reserve the best eight per
parent. This retained the genuine depth-11 child among 495,495 unique reserved
paths. At depth 12, ordinary constrained global scoring recovered strongly:
the genuine child ranked 29,973 of 18,828,810 generated candidates and survived
the standard 262,144 cut.

The six original depth-7 artifacts and a fresh official CLI replay all return
rank 180,915 exactly. A separate reconstructed run's 508,396 result therefore
does not establish nondeterministic CUDA behavior; it did not reproduce the
official pipeline. Retained populations are now optionally persisted as NPZ
checkpoints, and best genuine path/score are recorded after each development
cut, so future bridge tests can resume from exact arrays.

Resuming from the saved depth-12 population with ordinary constrained global
selection produced true ranks 198, 407, 1, and 1 at depths 13--16. Once rank 1
was reached, a conservative 4,096 beam retained the true order through every
remaining depth: its worst later rank was 7 at depth 20 and it finished rank 1
at depth 30. An independent full-stream board solve over the top eight terminal
orders placed the exact order at final rank 1 and recovered the 436-letter
plaintext with accuracy 1.0. Four of the eight terminals failed strict complete
segmentation and were recorded as skipped, not scored.

**Disposition.** This is the first width-30 mechanism to recover the hard
fixture end to end from the original raw-symbol search. It remains development
evidence on one fixture, not a powered result. The architecture is now concrete:
partition-constrained recall, a parent-reserved bridge at a measured global
ranking cliff, ordinary constrained rolling selection, then an independent
full-stream board solve. It must reproduce on multiple fresh development
fixtures before any holdout freeze or FAED use.

Current artifacts:

- `tools/gsmg/phase484ac_width30_i15_checkpointed_d10.json`, SHA-256
  `2622bca382584135165a64ad72d859332d4c93298a9f654f04f351631e03a54d`.
- `tools/gsmg/phase484ad_width30_i15_bridge_result.json`, SHA-256
  `fc25553d0638a64817020f73553c594f57e225712f21a2de376a97c4d11e0b7b`.
- `tools/gsmg/phase484ae_width30_i15_d12_to_d16.json`, SHA-256
  `ad701fdf5417eaca7e6bee905b974c076e038afd419014cc4eb2b1485a4bf5e4`.
- `tools/gsmg/phase484ae_width30_i15_d16_to_d30.json`, SHA-256
  `0f73b1c79e2480db401931d8d1f3eba11253b8783628aee5d430715700204521`.
- `tools/gsmg/phase484ae_width30_i15_final_resolve.json`, SHA-256
  `aa1d36e4e664b5980f720d285cfd83a06fcb937fca8920bb71fe247b290977a4`.

## Phase 484AF: fixed-schedule development generalization

Before any further fixture was scored, the successful fixture-15 architecture
was consolidated into one runner and its schedule frozen. The runner never
stops or changes a budget based on synthetic truth survival; truth is used only
to report retrospective development metrics. The frozen schedule is: invariant
search through depth 7; partition-constrained 3 x 2,000 scoring with retained
populations 262,144 at depth 7 and 1,310,720 at depth 8; depth-8 refit at
4 x 10,000 retaining 262,144; ordinary 262,144 selection at depths 9 and 10;
the depth-11 parent-reserved bridge with 65,536 parents and eight children per
parent; ordinary 262,144 selection through depth 16; a 4,096 beam through depth
30; and independent 4 x 10,000 full-board resolution of the top eight orders.

The canonical schedule SHA-256 is
`8aba55be72a86f6ff2de838f0bb422562af318b0c2488ec48834c6bb9a091af0`.
The exact-profile development pool contains only indices 0--22, so the
initially proposed indices 24--26 do not exist and failed before scoring. The
unchanged transfer set is therefore development indices 19, 21, and 22. They
are outside the invariant model's training indices and did not tune this
partition/bridge schedule, but they have appeared in older development probes;
they are not pristine holdout fixtures. No parameter may be changed between
them. A miss is recorded at the first lost depth, but the blind pipeline still
runs to completion. This is a weaker transfer/generalization check, not a
powered gate and not authorization to score FAED.
