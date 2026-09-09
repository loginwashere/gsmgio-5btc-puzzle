# Phase 484A raw-symbol VIC-order solver development protocol

Date drafted: 2026-09-06

Status: development only; no execution lock and no FAED scoring authorised

## Question

Can a solver recover a standard columnar transposition applied to the raw
570-symbol output of a 25-slot straddling checkerboard, when the checkerboard,
column order, and escape pair are unknown?

This is the historical substitution-then-transposition order reserved as
Phase 477B by Phase 477A. It receives the next available working number,
Phase 484A, without changing Phase 477A's result.

```text
English plaintext -> 25-slot checkerboard -> raw a-i symbols
                  -> standard columnar transposition -> observed symbols
```

Decryption restores raw-symbol order first, segments the restored stream, and
only then solves the board. Consequently, the current `{g,i}` segmentation,
its 436-token length, its code IC, and its code histogram are not evidence in
this model. They are products of segmenting a possibly transposed stream.

## Development boundary

Phase 484A is a synthetic solver-power phase. FAED must not be imported,
scored, ranked, or used to tune the solver. A later, separately locked phase
may score FAED only if recovery passes a frozen holdout gate.

The first implementation milestone is tuning-free infrastructure:

1. Standard exact/ragged columnar geometry for a raw length of 570.
2. All 36 unordered escape pairs over the established `a`-through-`i`
   alphabet. A canonical pair may be used in symmetric power tests, but a
   real run cannot inherit `{g,i}` as a selected pair.
3. Synthetic English fixtures with a random 25-letter board whose encoded
   raw length is exactly 570. Plaintext length is an output of generation,
   not frozen at Model A's 436 tokens.
4. Round-trip assertions covering every width 2 through 40, exact and ragged
   cases, every escape pair, and arbitrary column orders.

No solver family, score, search budget, power threshold, null, or real-data
decision rule is frozen by this development draft.

## Geometry

For plaintext raw-symbol length `n=570` and width `w`:

- `rows = ceil(n/w)`;
- original columns `0 .. (n mod w)-1` are long when the grid is ragged;
- no padding is created;
- encryption writes the raw symbols row-major and emits complete columns in
  a directly specified read-order permutation;
- decryption consumes chunks in that order and restores row-major order.

Exact-grid widths in 2 through 40 are `2, 3, 5, 6, 10, 15, 19, 30, 38`.
All other widths use the same last-columns-short convention as Phase 477A.

## Fixture construction

Fixture source text is local Cosmic Duality prose, reduced to `A-Z` with
`J -> I`. The 25-letter alphabet is `ABCDEFGHIKLMNOPQRSTUVWXYZ`.

For a fixture:

1. choose an escape pair and its 25 code slots (seven one-symbol slots,
   followed by eighteen two-symbol slots);
2. choose a board from one of two reported pools: `vic_profile` assigns the
   seven most frequent letters in the training corpus to the seven single
   slots and shuffles within the single/double groups; `broad_random` assigns
   a uniformly shuffled bijection between all 25 letters and slots;
3. choose a passage start and consume letters until its checkerboard encoding
   reaches exactly 570 symbols; reject that start if it jumps from 569 to 571;
4. choose a uniformly shuffled direct column order and transpose the raw
   encoded stream.

This construction deliberately permits decoded lengths to vary. It does not
condition fixtures on FAED's post-hoc `{g,i}` token histogram or on 436
letters.

The `vic_profile` pool is the historical-model gating candidate; the broader
random-board pool is an explicit robustness diagnostic. Which pool gates must
be frozen before holdout generation.

Development, tuning, and holdout corpus regions and seeds must be disjoint
before any solver-power claim is made. Only development fixtures may be used
until the solver and gate are frozen in an amendment or successor protocol.

## Required infrastructure checks

- Encoding followed by segmentation and board decoding reproduces plaintext.
- Columnar encryption followed by decryption reproduces all 570 raw symbols.
- The complete pipeline round-trips for widths 2 through 40 and all 36 pairs.
- Generated ciphertext preserves the exact raw-symbol multiset.
- Fixtures always have raw length 570, valid segmentation after correct
  untransposition, 25 distinct board assignments, and no `J`.
- A wrong column order is allowed to end in a dangling escape; solver code
  must represent that as invalid rather than repair or truncate it.

## Solver design target

The solver must recover enough of all four coupled objects to make its output
meaningful: raw column order, valid segmentation, global board, and plaintext.
Score attainment alone is insufficient because Phase 477A and Phase 483A
showed that false orders can outscore planted orders.

At minimum, holdout reporting must include exact order recovery, Kendall tau,
plaintext character accuracy, board accuracy, decoded length error, escape-pair
recovery, and readable plaintext. The eventual gate must be based on recovery,
not merely a language-score threshold.

## Limits

Even a successful Phase 484A solver would cover one standard columnar
transposition over a single checkerboard and English-like plaintext. It would
not cover disrupted/double transposition, non-columnar reordering, non-English
plaintext, or key material. A failed development search is not a negative on
FAED; only a powered, locked real experiment could produce such a verdict.

## Development amendment A1 (2026-09-07): shortlist replaced by exhaustive board-solving for widths <= 6

Status: development only; still no execution lock and no FAED scoring
authorised. This amendment changes the solver design for the exact widths 2,
3, 5, 6 milestone; it does not change the frozen geometry, fixtures, or
development boundary above.

**Finding that motivated the change.** A 16-item spectral shortlist (Phase
477A's precedent number, and consistent with width 7's development
observation that the planted order always ranked within the top nine) was
tested against width 6 using escape pair `{a,b}` and the `vic_profile` board
pool, 10 development fixtures. Exact order recovery was 6/10. For the 4
inspected misses, the true order's rank in the full spectral ordering (out of
432-600 valid orders per fixture) was 23, 52, 68, and 73 -- outside any
plausible small shortlist. A width-15 genetic search failing outright (noted
in prior Phase 483/484 development discussion) is therefore not directly
comparable: width 6's problem was shortlist coverage, not board-solving
power, and re-running those exact 4 fixtures with every valid order
board-annealed (no shortlist) recovered the exact order in all 4.

**Corrected design.** For any width where `w!` valid orders is tractable to
enumerate in full (2, 3, 5, 6 here; `w! <= 720`), skip the spectral shortlist
entirely: board-anneal every valid order and select the candidate with the
highest quadgram score. The spectral statistic is not used to filter
candidates at these widths, only the final quadgram board score decides. A
shortlist remains necessary at widths where `w!` is not enumerable (`w >= 7`
under the current reference implementation); this amendment does not address
that case.

**Development result (escape pair `{a,b}`, `vic_profile` board pool, 10
fixtures per width, 2 board-anneal restarts of 4,000 proposals each,
`T 20 -> 1`, no shortlist filtering):**

| Width | Exact order recovery | Mean board accuracy | Mean plaintext char. accuracy | Wall time (10 fixtures) |
|---|---|---|---|---|
| 2 | 10/10 | 0.964 | 0.999 | 0.7s |
| 3 | 10/10 | 0.972 | 1.000 | 2.1s |
| 5 | 10/10 | 0.944 | 1.000 | 41.3s |
| 6 | 10/10 | 0.952 | 0.990 | 264.8s |

Order recovery is exact at every fixture and every width tested. Board
accuracy is not exact at every fixture (individual fixtures ranged 0.80-1.00,
i.e. up to 5 of 25 slots wrong even with the correct order and a converged
anneal), which the near-ceiling plaintext accuracy shows is concentrated in
rarely-used letters. Board-anneal convergence at the current budget (4,000
iters x 2 restarts) is not itself demonstrated to be exhausted; a wider board
budget was not tested against this residual.

**Superseded by review.** This table's candidate selection used the raw
summed quadgram log-probability per candidate order, not a per-quadgram-window
average. Different candidate orders decode to different token counts (Model
B's segmentation is adjacency-dependent, not just a multiset property), so a
candidate that happens to decode shorter accumulates fewer, less-negative
summed terms and is unfairly favoured on raw totals alone, independent of fit
quality. All 40 fixtures here happened to still pick the true order despite
this bias, but that is not a demonstration that the bias is harmless at
uninspected pairs, board pools, or larger samples. See Amendment A2 for the
corrected scoring, a first-class reproducible `--exhaustive` CLI mode (this
table was produced by an ad hoc script, not the committed `dev-batch` entry
point, which still defaulted to a shortlist of 16 and would not have
reproduced it), and a rerun on fixtures untouched by this tuning pass.

**What this does not yet cover.** Only one escape pair (`{a,b}`, chosen as an
explicit non-`{g,i}` canonical pair per the frozen protocol) and only the
`vic_profile` board pool were run. The `broad_random` board pool, the
remaining 35 escape pairs, and a frozen disjoint-holdout confirmation are all
still open. This result is a development-split scoping run, not a holdout
gate pass, and does not by itself license freezing budgets or scoring FAED.

**Artifacts.** `tools/gsmg/phase484a_raw_symbol_vic_solver.py` gained
`load_language_model`, `score_indices`, `kendall_tau`, `anneal_board`,
`solve_fixture`, and `run_dev_batch`; `tools/gsmg/phase484a_dev_batch_result.json`
holds the full per-fixture record set for the table above; 7 new tests in
`tools/gsmg/test_phase484a_raw_symbol_vic_solver.py` (23 total in that module)
cover the quadgram table, Kendall tau, board-anneal monotonicity, and that
the planted (order, board) pair is never beaten in quadgram score by every
shortlisted alternative when supplied as an annealing seed.

## Development amendment A2 (2026-09-07): normalized selection, reproducible exhaustive CLI, both board pools, fresh fixtures

Status: development only; still no execution lock and no FAED scoring
authorised. This amendment corrects three issues in A1 and its supporting
code, found on review, before any holdout budget is frozen.

**1. Candidate selection no longer uses raw quadgram totals.** Different
candidate orders decode to different token counts (Model B segmentation is
adjacency-dependent), so raw summed log-probability favoured shorter
decodings independent of fit quality. `solve_fixture` now selects the winner
by `normalized_quadgram_score = quadgram_total / max(1, decoded_length - 3)`
(per-quadgram-window average), and rejects any candidate whose decoded
length falls below `MIN_DECODED_LENGTH = ceil(RAW_LENGTH / 2) = 285` -- the
mathematical floor when every code is a two-symbol pair -- before selection,
returning `solved: false` if no candidate clears it.

**2. Exhaustive mode is now an explicit, reproducible, fail-closed CLI
path.** `solve_fixture` and `run_dev_batch` take an `exhaustive: bool`
argument (raising `ValueError` above `EXHAUSTIVE_MAX_WIDTH = 6`, where full
`w!` enumeration stops being affordable in this reference implementation)
instead of a silent `shortlist_keep=16` default. The `dev-batch` CLI now
refuses to run without an explicit `--exhaustive` flag, so the shortlist
default can no longer silently overwrite an exhaustive artifact. `--start=N`
selects the first development-fixture index, and `--both-pools` runs both
board pools in one invocation; the result JSON records `shortlist_mode`,
`board_modes`, and `budgets.fixture_index_start` so it is self-describing.

**3. `vic_profile` is not the historical board model and does not gate
alone.** The solved Phase 3.2.2 straddling checkerboard's actual alphabet is
`FUBCDORA.LETHINGKYMVPS.JQZXW` (`tools/gsmg/FINDINGS.md`), not a
frequency-sorted board -- so a frequency-optimistic `vic_profile` pool cannot
by itself power a claim about historical construction, and Model B already
forfeits FAED's `{g,i}` single-slot density evidence. `broad_random` (a
uniformly shuffled 25-letter board, uncorrelated with training-corpus
frequency) is now run as a second gating pool alongside `vic_profile` in
every batch, via `--both-pools`.

**4. Escape-pair coverage is handled by proof, not by 35 more power runs.**
`relabel_symbol_map`/`relabel_string` construct the bijection on the 9-symbol
alphabet mapping any escape pair onto any other while preserving the relative
order of the remaining 7 symbols, and `test_relabeling_equivalence_across_escape_pairs`
mechanically demonstrates that a fixture built on one pair decodes identically
to its relabeled counterpart built on another pair. This holds only for
synthetic fixtures, where which two of the nine symbols play "escape" is a
free labeling choice made at fixture-construction time. It does not extend to
real FAED, whose a-i symbol frequencies are fixed and authenticated, not
relabeled -- the eventual real experiment must still test all 36 pairs.

**Rerun result (fresh fixtures 10-19, untouched by the A1 tuning pass;
2 board-anneal restarts of 6,000 proposals each, `T 20 -> 1`; escape pair
`{a,b}`; produced by `python3 phase484a_raw_symbol_vic_solver.py dev-batch
--exhaustive --both-pools --start=10`, not an ad hoc script):**

| Board pool | Width | Exact order recovery | Mean board accuracy | Mean plaintext char. accuracy |
|---|---|---|---|---|
| vic_profile | 2 | 10/10 | 0.992 | 0.9998 |
| vic_profile | 3 | 10/10 | 0.952 | 0.9990 |
| vic_profile | 5 | 10/10 | 0.936 | 0.9978 |
| vic_profile | 6 | 10/10 | 0.964 | 0.9993 |
| broad_random | 2 | 10/10 | 0.936 | 0.9997 |
| broad_random | 3 | 10/10 | 0.952 | 0.9997 |
| broad_random | 5 | 10/10 | 0.956 | 0.9982 |
| broad_random | 6 | 10/10 | 0.952 | 1.0000 |

Exact order recovery is 10/10 at every width under both board pools with the
corrected, length-normalized, minimum-length-gated selection rule -- the A1
result was not an artifact of the raw-total bias on this evidence. Board
accuracy remains imperfect at some fixtures (as in A1); plaintext accuracy
stays near-ceiling throughout.

**Still open, not resolved by this amendment.** Board-anneal convergence at
the current budget is not separately demonstrated to be exhausted (no wider
budget was tested against the residual board-accuracy gap). Only escape pair
`{a,b}` was run empirically; the other 35 are covered only by the relabeling
proof above, not by execution. A frozen disjoint-holdout confirmation has
not been run. This remains a development-split scoping result and does not
by itself license freezing budgets or spending holdout fixtures.

**Artifacts.** 5 more tests added (28 total in the module; 36 across the
483A+484A test set): quadgram-table/Kendall-tau sanity, the minimum-length
rejection path, the normalized-score ordering property, the exhaustive-width
guard, the `dev-batch` shortlist-mode recording, and the escape-pair
relabeling equivalence. `tools/gsmg/phase484a_dev_batch_result.json` was
overwritten with this rerun's full per-fixture records.

## Development amendment A3 (2026-09-07): blind escape-pair/order search

Status: development only; no execution lock, holdout consumption, or FAED
scoring authorised.

A2's recovery results supplied the planted escape pair to the solver. Symbol
relabeling proves that each pair has the same synthetic difficulty when it is
supplied, but does not prove that the correct pair can be selected over 35
wrong pairs on one fixed observed stream. A3 therefore ranks the full joint
space of all 36 escape pairs and every column order at widths 2, 3, 5, and 6,
before any board is solved.

On five new development fixtures (indices 20--24) in each board pool, planted
one-based joint spectral ranks were:

| Pool | w=2 | w=3 | w=5 | w=6 |
|---|---|---|---|---|
| `vic_profile` | 1,1,2,2,1 | 3,2,2,4,2 | 1,2,21,2,1 | 3,1145,1,1,16 |
| `broad_random` | 1,1,1,1,1 | 1,6,1,1,6 | 4,58,1,4,95 | 105,32,37,1003,126 |

The width-6 tail disproves a small global shortlist: two planted hypotheses
ranked 1,003 and 1,145. Both deliberately selected hard-tail fixtures were
then board-solved with a 1,536-hypothesis joint shortlist, two 6,000-proposal
restarts per hypothesis, and `T 20 -> 1`. Both recovered the exact escape
pair, exact order, exact board, and exact plaintext. This establishes
feasibility of blind joint recovery on the two inspected tail cases; it is
not a power estimate.

Before a holdout lock, the 1,536 cutoff must be evaluated on a broader fresh
development batch, including its rate of excluding the planted hypothesis
and its end-to-end joint recovery rate. Widths 7--40 remain unsolved because
their order spaces cannot use the exact enumerator. The eventual real run
must search all 36 escape pairs on the fixed FAED symbols; synthetic relabeling
does not reduce that real family.

Implementation safeguards added in A3: fixture generation now explicitly
selects `dev` or `holdout`; board-search seeds are keyed to the actual pair
and permutation rather than mutable shortlist rank; and the blind joint
solver reports pair, order, board, and plaintext recovery separately. The
module now has 31 tests (40 across Phase 483A and 484A).

**A3 continuation.** A reproducible board-free run on 40 additional fresh
width-6 development fixtures (indices 25--44, 20 per pool) found planted-rank
medians/maxima of 6/140 for `vic_profile` and 17/175 for `broad_random`.
All 40 lay within the 1,536 cutoff. Across the original and continuation
surveys, all 50 inspected width-6 fixtures lay within 1,536; the observed
maximum remains 1,145.

The two highest-ranked new fixtures in each pool were then selected using
only that board-free artifact and solved end-to-end under the unchanged
1,536-hypothesis, 2-restart, 6,000-proposal budget. All four recovered the
exact escape pair and exact order (one-based planted ranks 140, 108, 175,
and 88); all four have perfect plaintext accuracy, while board accuracy is
perfect in three and 0.88 in one because rare unused/near-unused slots remain
ambiguous.
Together with the two earlier extreme-tail tests, blind end-to-end recovery
is 6/6 on deliberately selected development tails. This is strong scoping
evidence for a frozen small-width holdout design, but selection of hard cases
is not a population power estimate and no holdout has yet been consumed.

The continuation artifacts are
`tools/gsmg/phase484a_joint_rank_batch_result.json` and
`tools/gsmg/phase484a_joint_tail_batch_result.json`. The module now has 33
tests (42 across Phase 483A and 484A).

Finally, three `broad_random` width-6 fixtures at development index 45
planted representative noncanonical escape-pair indices 7 (`{a,i}`), 17
(`{c,f}`), and 35 (`{h,i}`). Their planted joint ranks were 12, 19, and 1.
Under the same 1,536 x 2 x 6,000 budget, all three recovered the exact pair,
order, and plaintext; board accuracies were 0.92, 0.92, and 0.88. Thus the
end-to-end blind development total is 9/9 across six selected rank-tail cases
and three pair-position cases. The record is
`tools/gsmg/phase484a_pair_position_dev_result.json`.

## Holdout amendment A4 (2026-09-07): frozen small-width recovery gate

Status: frozen design pending execution lock; no holdout fixture has been
generated and FAED remains prohibited.

The holdout family is widths 2, 3, 5, and 6 crossed with both `vic_profile`
and `broad_random`, ten fixtures per cell (80 total). Fixture indices 0--9
use planted pair indices `0,1,5,9,14,18,23,27,32,35`, spanning the direct
36-pair enumeration. All fixtures use the untouched `holdout` corpus split
and `SEED_HOLDOUT = 0x484A401D`.

Every fixture is solved blind over all escape pairs. The board-free joint
ranking retains 1,536 valid pair/order hypotheses, followed by two independent
6,000-proposal board anneals per hypothesis with `T 20 -> 1`. A fixture passes
only when all four conditions hold: exact escape-pair recovery, exact order
recovery, plaintext character accuracy at least 0.95, board accuracy at least
0.80, and decoded length equal to planted plaintext length. (The first two
are represented jointly by `joint_recovery`.) Each of the eight width/pool
cells must pass at least 8 of 10 fixtures. This conjunctive recovery gate,
not language-score attainment, determines power.

Execution uses eight worker processes. Seeds are derived independently from
the frozen holdout seed, width, fixture index, planted pair index, candidate
pair, candidate order, and restart; scheduling therefore cannot change a
candidate's random stream. Any worker failure prevents atomic publication of
the result. The verifier requires the exact 80-job set, recomputes every
fixture pass and cell aggregate, checks the lock chain, and fails closed.

Passing A4 powers only this blind solver at widths 2, 3, 5, and 6 under the
two synthetic board pools. It does not power widths 7--40 and does not itself
authorise FAED scoring; a separately locked real experiment is still required.
