# Phase 512A — transposition-aware exact-crib feasibility

Date: 2026-09-15

Status: development-only; no FAED access or execution lock.

## Novel question

Direct checkerboard crib matching is already covered by `crib_drag.py` and
Phase 466. The remaining distinct question is whether a complete authenticated
string can constrain the unknown column order in historical Model B:

`plaintext -> checkerboard raw symbols -> columnar transposition -> observed`.

The exact crib predicate is evaluated only after a proposed order restores the
raw stream and that stream is segmented. It uses equality of checkerboard codes,
not English fluency and not a guessed board alphabet.

## Frozen development cribs

Only complete, independently established strings are eligible:

1. the 91-letter Phase-3.2.2 `VALIDATION_ANSWER`;
2. the 53-letter authenticated Phase-1 credential;
3. the complete 161-letter creator macro message.

No clauses, substrings, reversals, spelling variants, inferred boundaries, or
solver-generated strings are introduced. All three use only the 25-letter
checkerboard alphabet (`A-Z` with `J` omitted).

## Development probe

For widths 15, 19, 30, and 38, construct one deterministic exact-570 fixture
per crib with a random 25-slot board, escape pair `{g,i}`, random column order,
and random checkerboard-representable filler surrounding the exact crib.
Synthetic escape-pair choice is label-equivalent and is not evidence for the
real FAED pair.

For each cell:

- assert the true order produces the exact crib equality-pattern match at its
  planted token offset;
- test 1,000 random wrong orders and record exact matches;
- test every single column-swap neighbor of the truth and record exact matches.

The random-order test measures terminal specificity only. The single-swap test
measures whether the exact predicate supplies a local basin. A predicate that
accepts only the exact solution may be an excellent validator but remains
useless to heuristic search; it would require a purpose-built constraint solver.

## Decision

- Any failure at the true order is an implementation failure.
- Frequent wrong-order matches reject the crib as insufficiently specific.
- Zero or near-zero neighbor matches means do not use exact-hit hill climbing;
  proceed only by deriving partial constraints or a CSP/backtracking algorithm.

This phase cannot authorize FAED. Its purpose is to decide the architecture of
a later powered synthetic recovery experiment.

## Development results

The 12-cell terminal-specificity probe completed in 17.9 seconds:

- all 12 true orders recovered the planted crib at the planted token offset;
- 0 of 12,000 random wrong orders produced any exact crib-pattern match;
- 6 of 4,242 single-swap neighbors produced a match somewhere (all six were
  confined to the shortest, 53-letter credential; the 161-letter macro had
  zero neighbor matches).

Thus the exact predicate is an excellent terminal validator but almost entirely
flat as a search objective.

Two development recovery mechanisms were then tested on the most favorable
nontrivial ceiling: width 15, correct `{g,i}` pair supplied, exact raw crib-start
position supplied, and the 161-letter macro planted.

1. Naive exact backtracking reached its 2,000,000-node limit in 2.37 seconds
   without finding a solution. A truth-first canary found the planted solution
   in 265 nodes, proving constraint correctness and localizing the failure to
   branch ordering rather than an invalid constraint set.
2. Greedy single-swap ascent reached only 14/161 consistent crib letters over
   32 restarts. Plateau-tolerant simulated annealing (32 restarts × 10,000
   steps) improved that to 20/161 in 13.6 seconds, still far from recovery.

These are development failures, not a locked negative. They show that neither
permutation enumeration nor local search makes the transposition-aware crib
cheap. Continuing requires a materially stronger constraint architecture—such
as length-pattern enumeration plus MRV/forward checking, or a compiled SAT/CSP
formulation—not larger heuristic budgets. No FAED test is licensed.

### Length-pattern CSP redesign

The proposed length-pattern/MRV redesign was then implemented and changed the
result materially:

- with the true single/double pattern supplied, the exact width-15 credential
  order was recovered in 16 nodes and the width-19 macro order in 20 nodes;
- enumerating all 26,333 legal credential length patterns at the known start
  found the exact pattern and order at pattern 3,856, after 3,872 total nodes
  and 0.17 seconds, with no earlier false hit;
- enumerating raw starts with `{g,i}` supplied exhaustively rejected starts
  0–157, then recovered the exact start, length pattern, and order at start 158:
  4,164,509 nodes in 180.45 seconds, no earlier false hit;
- enumerating all escape pairs at the known start rejected the first 34 pairs
  and recovered `{g,i}` at pair index 34: 899,195 nodes in 34.58 seconds;
- one fully blind wrong-start benchmark covering all 36 pairs × 26,333 length
  patterns took 33.81 seconds, 947,988 nodes, and produced zero false hits.

This establishes a working exact-constraint architecture. At the measured
serial rate, reaching the planted width-15 start in the full pair×start family
would take about 90 minutes. Since escape-pair cells are independent, the next
engineering step is bounded multiprocessing across pairs, followed by a small
multi-fixture synthetic recovery batch. No FAED run should precede that batch.

### Parallel search implementation

`phase512e_parallel_blind_crib.py` implements a deterministic, checkpointed
start-major scheduler. It completes and retains every escape-pair branch at a
raw start before advancing or stopping, so operating-system worker completion
order cannot select the reported solution. Checkpoints pin the observed-text,
crib, length-pattern, pair-family, width, start-range, and node-budget fields
and reject mismatched resumes.

Serial/parallel parity passes exactly. A complete 36-pair search at the planted
width-15 credential start recovered only the exact `{g,i}` solution and took
4.68 seconds with 16 workers. The same complete pair family at one start of a
deterministic filler-only, crib-absent fixture took 4.43 seconds and returned
zero hits. All 72 cells were exhaustive under the per-cell node budget. This
projects to roughly 12 minutes to reach a planted offset near 158 and roughly
38 minutes to exhaust all 518 possible starts of a negative fixture, before
checkpoint serialization overhead.

These are implementation benchmarks, not a power gate. The next stage remains
a multi-fixture blind synthetic batch with positive and crib-absent controls.

### Width-38 compute amendment

The first multi-fixture batch recovered the credential exactly, with no earlier
false hit, at widths 15, 19, and 30. Width 38 exposed a qualitatively different
cost regime: four fully exhausted starts averaged roughly 9.8 minutes each,
projecting about 26 hours to its planted start. Node accounting localized the
cost: the four heaviest escape-pair branches consumed about 59–61% of all
nodes, leaving most workers idle behind a few pathological branches.

A pattern-sharded scheduler was implemented and verified against the serial
solution. On the identical width-38 start it reduced wall time from roughly
9.8 minutes to 7.9 minutes, only about 20%. This rejects load balancing as a
sufficient repair; the remaining cost is algorithmic branching inside the
length-pattern CSP. The width-38 batch was therefore interrupted before seeing
its planted start and remains unpowered. Completed width-15/19/30 results are
retained. The next bounded lane is the complete width-15 crib-absent control;
width 38 requires a different CSP implementation or stronger pruning before it
can re-enter an eligible real-search family.

### Locked width-15 credential result and longer-crib cost

Phase 512G then exhaustively searched real FAED at width 15/untranspose for the
complete Phase-1 credential. All 518 starts × 36 pairs = 18,648 cells completed
with zero hits and zero incomplete cells in 2,622 seconds. A separate verifier
recomputed the lock, checkpoint, result, pair labels, start continuity, and
cell totals successfully. This is a bounded negative for that exact crib only.

Before attempting another real crib, one complete absent-fixture start was
benchmarked for each longer authenticated string:

- Phase-3.2.2 validation answer: 198,208 length patterns, 48.2 seconds/start,
  projecting roughly 6.4 hours for 480 starts;
- creator macro: 278,806 length patterns, 115.1 seconds/start, projecting
  roughly 13.1 hours for 410 starts.

A development static-most-constrained-column solver preserved the exact known
solution and matched the reference on a pattern prefix, but the validation
benchmark remained 47.6 seconds. The absent cells already die at their first
search node; the cost is Python construction/dispatch across millions of
patterns, not deep backtracking or bad MRV ordering. No longer-crib FAED run is
licensed at this cost. The next engineering step is a native implementation of
the unchanged exact CSP, with cell-level parity against the frozen Python
reference before it may support another lock.
