# Phases 499--504 width-19 unrestricted gate and real-run audit

Date: 2026-09-14

## Outcome

This chain established that the unrestricted-checkerboard, Model-B width-19
solver can recover two pre-outcome-selected, valid synthetic holdout fixtures
at exact final rank 1, then produced a bounded miss on real FAED under the
single frozen cell `{g,i}`, width 19, raw-digit columnar direction, English
quadgram objective, and the qualified annealing schedule.

The real run returned five valid terminal decodings from eight terminal
orders.  Every decoding was gibberish.  The best normalized quadgram score was
`-5.1551914835`; the two exact synthetic holdout winners scored
`-4.6751413500` and `-4.5617931713`.  This is evidence against that one cell,
not against Model B as a family.  In particular, it does not select or reject
other escape pairs, widths, transposition directions, language models, or
checkerboard/transposition variants.

## Evidence chain

| Phase | Role | Result | Scientific status |
|---|---|---|---|
| 499 | First locked unrestricted width-19 holdout gate | Fixture 0 failed; exact order absent, top-1 plaintext accuracy `0.14554` | Gate failed; fixtures 1 and 2 remained unspent |
| 500 | Post-hoc diagnosis on consumed fixture 0 | Higher budget repaired depth 9 and separately moved the two correct depth-11 children from local ranks 16/11 to 2/1 | Diagnostic only; Phase 499 remained failed |
| 501 | Two schedule investigations sharing the same working number | Corrected-depth-9 gate failed on fresh fixture 2; the independent depth-11-only repair recovered consumed fixture 0 exactly | First is a failed gate; second is post-hoc engineering evidence only |
| 502 | Locked depth-11-repaired gate | Fixture 3 recovered exactly; fixture 4 failed the frozen construction gate before scoring | Protocol infeasible as written, not solver-negative |
| 503 | Locked replacement cell | First mechanically eligible successor, fixture 5, recovered exactly; combined fixtures 3 and 5 passed `2/2` | Small operational-power gate passed |
| 504 | Locked real FAED run | Five valid decodings, all gibberish; best score `-5.1551914835` | Bounded miss for the frozen cell |

## Phase 499: first holdout failure

Phase 499 froze holdout fixtures 0, 1, and 2 and required exact top-1 order
recovery on all three.  It stopped correctly after fixture 0 failed.  The
true lineage survived the early stages but was discarded at the depth-11
parent-reserved bridge: before selection there were two true fragments, with
best rank `674,463` of `1,179,648`; after selection there were none.  Final
top-1 plaintext accuracy was `0.1455399061`, and no exact order reached the
terminal population.

Authoritative result:
`_work/phase499/i0_s3/phase499_complete_result.json`, SHA-256
`7aae457ceec332ef4ad5fe18c678cfebddcf48473ddb9622bf377e6479d3a870`.

## Phase 500: post-hoc diagnosis

Two diagnostics examined already-consumed fixture 0 without spending another
holdout fixture or touching FAED.

First, rescoring depth 9 at `3 x 10,000` iterations improved the true
fragment from original ranks `45,203` before / `31,532` after selection to
rank 1 both before and after selection, retaining seven true fragments.  This
showed that depth 9 was under-annealed in the original schedule, but did not
repair the later depth-11 failure.

Second, the local depth-11 sibling diagnostic found one true parent, 18
children, and two true children.  Under the production `3 x 10,000` budget,
the true children ranked 16th and 11th locally and reached board accuracies
`0.08` and `0.44`.  Under `8 x 20,000`, they ranked 2nd and 1st and both
reached board accuracy `0.88`.  The planted-board ceiling ranked them 2nd and
1st.  The bridge's eight-child reservation was therefore adequate when the
board objective was sufficiently optimized.

Authoritative diagnostic hashes:

- depth-9 rescue result: `2714658c9f0fe7f20410f352ad832f77f61d3e1f357a8153c4b1805c66fd59ff`;
- depth-11 local result: `bc5309092ed642733237eb06aaf5d70e3656e41144fefeecc054ef705ab43a17`.

## Phase 501: two distinct repair experiments

Two experiments retained the working number 501 and must not be conflated.

The corrected-depth-9 holdout gate raised the `global_depth` budget to
`3 x 10,000` starting at depth 9 and selected fixtures 2, 3, and 5.  It failed
on its first fixture, index 2.  That fixture already ranked `34,019` after the
depth-8 selection, then fell to rank `3,408,289` before depth-9 selection and
was discarded.  A host OOM occurred during or approaching depth 12, but the
gate outcome was already logically fixed because later stages only extend the
surviving population.  Fixtures 3 and 5 were not spent.  Early-stop record
SHA-256: `e5706326e66ccc852dc4011fa0c741a03be8408e7c0df6c1e5fc5aae054a2380`.

Separately, the depth-11-only repair replayed already-consumed Phase-499
fixture 0 with `8 x 20,000` only at the bridge and retained `3 x 10,000`
afterward.  It recovered the exact order at final rank 1 with plaintext
accuracy `1.0`.  Because the fixture had motivated the change, this was
post-hoc engineering evidence and explicitly did not repair either failed
gate.  Result SHA-256:
`5cc48975bd70a1136878eb5b98c7cf2cbaf5c17bb2b5e0a0c5ee32bbb52ad1cc`.

## Phases 502--503: qualified operational-power gate

Phase 502 froze the depth-11-only repair against fixtures 3 and 4.  Fixture 3
recovered the exact order at rank 1 with plaintext accuracy `1.0` and score
`-4.6751413500`.  Fixture 4 then failed construction before any objective
marker, solver score, or GPU work: its edit fraction `0.1879350348` exceeded
the frozen `0.18` ceiling.  This exposed a pre-lock validation omission.  The
literal Phase-502 `2/2` protocol was infeasible, not solver-negative, and was
not silently amended.  Fixture-3 result SHA-256:
`c8fa0ba363d9bdee920d8bb9f26c25fc2c35d06d2f4246e15234b3f37b94a2a8`.

Phase 503 preserved the locked fixture-3 result and selected the first
mechanically eligible successor after fixture 4.  Fixture 5 had edit fraction
`0.1624129930` and normalized source score `-4.5617931713`.  Under the
unchanged repaired schedule it recovered the exact order at rank 1 with
plaintext accuracy `1.0`.  The combined `[3, 5]` gate therefore passed `2/2`.
Result SHA-256:
`0b132d531bcbf7b6684628a488672868d4bfca68f8a8bfcfa414bbf8a537ef32`.

This is a small operational-power demonstration, not a population recovery
estimate.  Both fixtures use the same `{g,i}`, width-19, English, Model-B
construction family and deterministic three-swap partition violation.

## Phase 504: real FAED result

Phase 504 froze exactly the schedule that passed the qualified gate:

- input SHA-256:
  `066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`;
- raw length 570, width 19, 30 rows;
- escape pair `{g,i}`;
- Model-B raw-digit columnar direction;
- unrestricted 25-slot checkerboard;
- invariant front through depth 5;
- original unrestricted budgets through depths 6--10;
- depth-11 bridge only at `8 x 20,000`;
- depths 12--19 at `3 x 10,000`;
- final top-eight unrestricted board resolution.

The run produced eight terminal orders.  Three did not segment validly under
`{g,i}`; the other five decoded to lengths 439, 440, 440, 440, and 437.  Their
normalized scores were:

1. `-5.1551914835`
2. `-5.1918546636`
3. `-5.2541354457`
4. `-5.2553659680`
5. `-5.2903119772`

All five strings were gibberish.  The top result begins
`NEHASAHATTEDATMISLTERDAYSYREIBHORSE...`; apparent short English fragments
do not form coherent plaintext.  The earlier constrained Phase-490 winner
reappeared as the second unrestricted result at effectively the same score,
which is descriptive evidence of a stable false optimum rather than a solve.

Authoritative result:
`_work/phase504/real_gi_w19_unrestricted/phase504_real_result.json`, SHA-256
`c22336ff7def3c337e2700b7506fc0d0bb30173c6006d95b11c483a9b6b4b17f`.
The execution-lock SHA-256 embedded in that result is
`b642081f66586cb54ee62c5a462bd3fdcd48c6c5bf41d667f358046f4d7cdb3d`.

## Interpretation and limits

The chain did what it was designed to do: a specific synthetic failure was
diagnosed, a one-field repair was demonstrated post hoc, the repair was then
tested on new valid fixtures, and only after that gate passed was FAED scored.
The real miss is consequently more informative than an uncalibrated solver
failure.

It remains bounded because several load-bearing assumptions are shared by the
calibration and real cell:

- `{g,i}` is only a model-conditioned prior under Model B; witnessed
  checkerboard segmentation is not invariant under raw-symbol transposition;
- width 19 is only one exact-grid geometry;
- the objective assumes ordinary English-like quadgram structure;
- the search uses one frozen schedule and seed family;
- the synthetic fixtures establish only limited operational power, not a
  calibrated false-negative probability for FAED;
- no shuffle-null significance claim was preregistered or computed.

Accordingly, Phase 504 is a bounded no-solve.  It does not close Model B or
the broader FAED puzzle.

## Next experiment

Before another expensive FAED run, test whether the current observable
front-stage score can identify the planted escape pair.  A synthetic
all-36-pair identifiability gate should precede any real all-pair screen.  If
the true pair cannot be selected reliably on planted fixtures, FAED pair
ranking would be uninterpretable and should not be run.

