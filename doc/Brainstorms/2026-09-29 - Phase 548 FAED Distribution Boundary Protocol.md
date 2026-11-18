# Phase 548 — FAED distribution boundary pilot

Frozen before scoring FAED. Executes Path 2 of the September 24 microstep
brainstorm. No plaintext, password or new decoder is searched.

Input: the complete native FAED, 570 symbols. Candidate cuts are divisors of
570 and their complements, with at least 30 symbols on each side, plus 91
and 479 (DBBI length and complement). Layouts: every nontrivial exact
row-major rectangular factorization of 570, testing row and column groups.
Identical group partitions are deduplicated before scoring.

For each partition, form its group-by-symbol count table. Use Pearson's
homogeneity X² with expected counts derived from that stream's symbol
marginals, then Z = (X²-df)/sqrt(2df), df=(groups-1)(present symbols-1).
This normalization only makes scales comparable; it is NOT an asymptotic
p-value. Sparse groups are permitted. The family statistic is max Z.
Null: 1,999 exact-multiset shuffles, seed 54801, recomputing the whole family.
Monte Carlo p=(1+number of null maxima >= real maximum)/2,000.
Checkpoint if p <= .01; otherwise bounded negative for these marginal
distribution tests. A checkpoint selects structure for a separate test;
it does not license treating a cut as plaintext or changing a Bifid period.

Controls before the real run: optimized counts/statistics equal an independent
direct implementation on synthetic inputs; symmetry under symbol relabeling;
10 planted streams at each total-variation difference .05/.10/.15/.20.
Each plant has 285 symbols per side, uniform baseline and opposite shifts
of effect/2 between symbols a and i. Each plant is tested against 199 own
multiset shuffles at the same .01 family bar. Report detection counts; require
at least 9/10 recovery at .20 before real scoring. These controls measure
this particular balanced distribution change, not all possible boundaries.
Smallest tested effect with >=9/10 detections is descriptive, not a rigorous
minimum detectable effect. If strongest controls fail, stop without scoring
FAED. No post-result parameter adjustment.

Preparation writes a hash lock pinning protocol, script, data.py and controls.
The run verifies it. One real run; retain all partition scores and all null
maxima. No added cuts, statistics, layouts, clipping, or tail rescue after it.
