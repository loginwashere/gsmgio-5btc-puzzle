# Phase 477A pre-board token columnar transposition protocol

Date frozen: 2026-09-03 (draft; execution lock not yet issued)

## Question

Is FAED, segmented once under `{g,i}` into 436 checkerboard code tokens, an
unknown-order ragged columnar transposition of English-like plaintext under a
single global 25-symbol monoalphabetic board?

## Model under test (Model A only)

```text
plaintext letters -> columnar transposition (unknown width w, unknown order)
                  -> 25-slot straddling checkerboard, escapes {g,i}
                  -> FAED
```

Equivalently: the 436 `{g,i}` code tokens of FAED are a column-permuted
sequence of plaintext letters. This placement retains every existing `{g,i}`
measurement (clean segmentation, rank-1 code IC, token count) because token
identity and frequency are invariant under reordering; only token order is
disturbed.

This is **not** the historical VIC/ADFGVX order (substitution then
transposition of the *digits*). That model, in which the current `{g,i}`
segmentation and code IC carry no evidential weight, is reserved exclusively
for a separate Phase 477B protocol and is not tested here.

## Why this is materially different from Phase 321

Phase 321 permuted the same token sequence but only under 11 keyword-derived
column orders. A 2026-09-03 scratchpad sweep (not a phase) extended that to
14,696 distinct keyword/numeric-derived permutations from the project
wordlists, both placements, both directions: negative. Both are structured
subsets. Phase 477A searches the permutation directly, at a search strength
that must first be demonstrated on locked synthetic fixtures.

Phase 113's `{g,i}` monoalphabetic result (real `-2419.47`, 3/100 shuffled
controls better, p=0.0396) is read only as: no readable or threshold-level
plaintext, with weak above-null sequential structure. It does not by itself
select transposition, and this protocol does not treat it as such.

## Frozen geometry and search family

- Token stream: `segment_codes(FAED, "g", "i")`, 436 tokens, 25 code types,
  mapped to slots 0-24 in the established single-then-`g`-pair-then-`i`-pair
  order (`checkerboard_code_ic_oracle.segment_codes`, Phase 310 slot order).
- Widths: `w = 2 .. 40`. Exact grids exist only at `w = 2, 4` (`436 = 4 x
  109`); every other width is ragged.
- Ragged convention (primary, sole): `rows = ceil(436 / w)`; the final
  `w*rows - 436` columns **by original column index** are short; no padding
  symbol is ever inserted or removed.
- Key: a direct permutation of `range(w)` (column read order). Keyword rank
  conventions are irrelevant because the permutation itself is searched.
- Directions: `untranspose` (observed tokens are the column-read output;
  recover row-major plaintext) and `transpose` (observed tokens are the
  row-major grid; plaintext is the column-read output). For each `(436, w)`
  the implementation must mechanically test whether the two families induce
  identical position-permutation sets and deduplicate only on proven
  equivalence. Since the inverse of a columnar transposition is columnar only
  for a square grid, both directions are expected to be retained at every
  width; the family multiplicity is therefore `2` per width by construction.
- Board: one global bijection from the 25 slots to 25 of the 26 letters
  (`quadgram_solver` convention: 26-letter key, one letter unused).
- Language model: the project's frozen `data_files/english_quadgrams.txt`.

## Optimizer (alternating global search)

For each `(w, direction)` cell and each restart:

1. Initialise a random permutation and a random board.
2. **Order step, conditional on the board:** decode every column under the
   current board, compute the pairwise column-adjacency cost matrix from the
   quadgram model over the row adjacencies, and solve the column order —
   exactly by Held-Karp when `w <= 16`, otherwise by a frozen heuristic
   (2-opt / or-opt with a fixed move budget).
3. **Board step, conditional on the order:** re-solve the single global board
   on the full reconstructed 436-character text by the project's existing
   quadgram hill-climb (`quadgram_solver.hillclimb` search shape, fixed
   iterations).
4. Repeat 2-3 for a fixed number of rounds; keep the best `(order, board)`.
5. Population exchange across restarts and one large-move phase (block
   reversal / block move of the order) at fixed points in the schedule.

Every budget (restarts, rounds, iterations, move counts) is a fixed count,
never wall-clock. The pseudo-random generator is an explicit PCG32
implemented in the reference code, so fixed-seed results are reproducible
across Python/Rust/CUDA implementations.

Statistic per cell: best quadgram score of the reconstructed text divided by
decoded length (436 here; normalised for uniformity with 477B). Family
statistic: the maximum over all **powered** `(w, direction)` cells.

## Synthetic power test (gate, before any FAED search)

Fixtures are generated from held-out English (Cosmic Duality book text,
`wordlists/gsmg/cosmic_duality_book_full_text.txt`, letters only, `J -> I`),
436 letters each, with a random 25-slot board and a uniformly random column
order at the fixture's width, encoded through the identical checkerboard
code and transposition code used on FAED.

Two pools, both reported:

- **Broad pool:** random passage; the 7 single-digit slots assigned to 7
  random letters.
- **Hard-profile pool (gating pool):** passage whose top-7 letter share is
  `>= 0.65`, and the 7 single-digit slots assigned to that passage's 7 most
  frequent letters (VIC convention). This reproduces FAED's measured 69.3%
  single-slot token fraction, which Phase 43 showed only 0.34% of English
  windows reach under a random assignment.

Development fixtures (seed `0x477A_DEV`) are unrestricted and may be used
for solver tuning. Holdout fixtures (seed `0x477A_HOLD`, fixed count per
cell, identical across competing implementations) are generated once, their
file hash is recorded in the manifest before tuning ends, and they are run
exactly the number of times recorded in the execution lock.

Success for one fixture is conjunctive:

```text
Kendall tau (induced plaintext column order, equivalents quotiented) >= 0.90
AND recovered plaintext character accuracy >= 0.90
```

A `(w, direction)` cell is **powered** only if `>= 80%` of its hard-profile
holdout fixtures succeed. Broad-pool power, exact permutation recovery, board
accuracy, normalised score, and separation from paired shuffled fixtures are
reported per cell but do not gate. Widths `2-4` will pass near-trivially and
are labelled `trivially_powered`.

Only powered cells enter the real family maximum and every null family
maximum. Unpowered cells are reported as `underpowered`, never as closed.

## Controls and decision rule

Token-preserving null: shuffle the 436 real tokens (same multiset, same
length, same code histogram), then run the identical complete powered family
(all powered widths, retained directions, same budgets, same best-of
selection) and record its family maximum. **Exactly 200 null trials**, seeds
`0x477A_NULL + k`.

```text
p = (exceedances + 1) / 201
promote iff p <= 0.005   (i.e. 0/200 exceedances)
```

Readable plaintext is corroborative; it is never the decision statistic. If
the real family maximum is exceeded by any null trial the family is closed
negative for the powered cells.

## Secondary diagnostic: `{h,e}` at width 7 only

`469 = 7 x 67` is an exact grid, so the 5,040 column orders are enumerated
exhaustively (order dimension exact; board re-solved per order with the
fixed hill-climb budget). This family has its own hard-profile power test,
its own 200 token-preserving controls, and its own `p <= 0.005` bar. It is
**never pooled** with the primary family and does not participate in the
Phase 477A promotion decision. A readable or threshold-level result triggers
a separately locked confirmation run with new seeds, not a promotion.

## Compute decision rule (before execution lock)

1. Freeze the algorithm and all budgets.
2. Benchmark complete-family searches on 8 fixed development fixtures and 8
   matched shuffles; record CPU-seconds per family.
3. Project, at 16-way parallelism: remaining holdout fixtures, one real
   family search, 200 null family searches.
4. Python/16-core CPU only if the projected decision run is `<= 24 h`;
   otherwise port the hot loop to Rust with deterministic parallelism; if
   Rust projects `> 48 h`, implement CUDA. Phase 322's GPU scaffold is
   reusable infrastructure only; its AES throughput is not an estimate for
   this solver.
5. Any port must match the Python reference exactly on small exhaustive
   fixtures and on fixed-seed searches where deterministic equivalence is
   expected.

## Required checks

- Round-trip: encode -> transpose -> untranspose -> decode reproduces every
  synthetic plaintext exactly, for every width, both directions, ragged and
  exact.
- Direction-equivalence test executed and recorded for every `(436, w)`.
- Held-Karp inner solver validated against brute force at `w <= 8`.
- Planted positive: a hard-profile fixture at a mid width passes the full
  pipeline end to end before the lock is issued.
- Multiset invariance: every null trial's token histogram equals the real one.

## Limits of the conclusion

Phase 477A tests a single standard ragged columnar permutation of the
`{g,i}`-segmented 436-token stream, followed by one global monoalphabetic
checkerboard mapping, for English-like plaintext under the project's
`english_quadgrams.txt` model, over synthetically powered widths only.

A negative retires that model for the powered cells. It does not retire
historical raw-digit transposition (477B), unpowered widths, double or
disrupted transposition, non-English or key-material plaintext, or any
non-columnar reordering. The unexplained `{g,i}` code IC of 0.0743 (English
0.067) is invariant under this model and is neither explained nor addressed
by it.

No password material, ciphertext-oracle calls, address derivations, or
Bitcoin endpoint checks are performed in this phase.

## Amendments before lock (2026-09-04)

Development work on the reference implementation
(`tools/gsmg/phase477a_token_columnar_transposition_audit.py`) established
facts that change the search family, the power gate, and the fixture pool.
Each amendment below replaces the corresponding text above. No FAED family
search and no null trial were run before these amendments were written.

### A1. Untranspose direction: exhaustive order enumeration, not local search

Development fixtures showed that the full quadgram score over (order, board)
is flat beyond a single column swap: at `w = 12` and `w = 20`, a planted
order damaged by two swaps scores no better under its best board than a
random order under its best board (`-5.2` to `-5.6` per token against
`-4.5` for the planted order). Alternating Held-Karp/board steps, joint
simulated annealing over (order, board) up to 3,000,000 proposals, nested
order-outer/board-inner annealing, and annealing of a substitution-invariant
statistic all failed to reach the planted optimum at `w >= 16` and were
unreliable at `w = 12`. The optimiser described above is therefore replaced.

Frozen untranspose search:

1. Enumerate every one of the `w!` column orders for `w <= 11`
   (`ENUM_MAX_WIDTH`).
2. Rank orders by the substitution-invariant coincidence statistic of the
   reconstructed token sequence: `pairs(digraph codes) + 3 * pairs(trigraph
   codes)`, where `pairs` counts coincident pairs `sum C(n, 2)`. On 24 of 24
   development fixtures at `w = 5 .. 10` (both pools) the planted order
   ranked within the top three of all orders (first in 17, second in 6,
   third in 1).
3. Anneal the board (`2` restarts, `30,000` proposals, `T 20 -> 1`) on each
   of the top `16` orders; the cell result is the best score.

Untranspose cells with `w >= 12` are **not enumerable** (`12! = 4.8e8`
orders at `14 us` each exceeds the compute rule per trial across 200 nulls)
and no local search has demonstrated power there. They are excluded from
the family and reported as `not_enumerable`, never as closed. This is the
main limit of the conclusion.

### A2. Transpose direction: board first, order second; order not identifiable

In the transpose direction every column is a contiguous plaintext chunk, so
the board is annealed on within-column quadgram windows first (`16`
restarts, `10,000` proposals, `T 20 -> 1`), then the column order is solved
on junction gains by Held-Karp (`w <= 16`) or greedy construction followed
by deterministic or-opt/2-opt improvement (at most `200` sweeps), followed
by `3,000` full-score polish moves and `3` refine rounds (`4,000` board
proposals each, `T 5 -> 0.5`) on the best `4` boards. This budget was fixed
after a first development pass with `8` restarts, `3` boards, `2` rounds
and `500` polish moves left eight wide transpose cells at 3/4 hard
fixtures, all near-misses with the board at least 88% correct. Because only the `3 (w - 1)` junction
windows out of `433` depend on the order, the order is not identifiable
from the statistic at 436 tokens; the search reaches the planted score at
every width tested while recovering the planted order only at small widths.

### A3. Power gate is score-reach, recovery is reported

Success for one fixture is now:

```text
found normalised score >= planted normalised score   (reach)
```

The decision statistic is the family maximum of the normalised score, so the
gate must certify that the search attains the planted optimum of that
statistic. Kendall tau, character accuracy, exact-order recovery, and board
accuracy are reported per fixture and per cell but do not gate. The
conjunctive tau/accuracy criterion above would label every transpose cell
underpowered for a reason unrelated to search power (A2). Kendall tau is
computed directly on the column-read permutation; the direction-equivalence
test retains both directions at every width, so no quotienting is applied.

### A4. Fixture corpus and hard-profile threshold

Fixtures are drawn only from prose sections of
`wordlists/gsmg/cosmic_duality_book_full_text.txt`; front matter, table of
contents, index, acknowledgments, colophon and back matter are excluded
(56,292 letters remain). At the original `0.65` top-7 share threshold the
full file yields 25 separated windows, 20 of them inside the index pages.
The hard-profile threshold is therefore `0.62` (2,474 raw prose windows,
82 separated starts). The maximum top-7 share of any 436-letter prose window
in this corpus is `0.658`; FAED's single-slot fraction of `0.693` is not
matched by any prose window, which is recorded as a limit of the fixtures,
not as evidence about FAED.

Holdout fixtures: `10` hard-profile and `5` broad per cell (seed
`0x477A401D`). Development fixtures (seed `0x477A0DE`, `4` hard and `2`
broad per cell) are unrestricted and were used for all tuning above.

### A6. Compute decision

One complete family search (all 49 retained cells) costs about `1,100`
CPU-seconds in the Python reference implementation, dominated by the
`w = 11` enumeration (`~670 s`). The holdout gate, the real search and 200
null trials project to under `5` hours at 16-way parallelism, so the Python
reference is the decision implementation; no Rust or CUDA port is made.

### A5. Secondary `{h,e}` width-7 diagnostic

Runs with the identical enumeration-plus-board pipeline (5,040 orders,
same ranking, same top-16 board budget), its own hard-profile power test,
its own 200 token-preserving controls, and its own `p <= 0.005` bar. It is
never pooled with the primary family.
