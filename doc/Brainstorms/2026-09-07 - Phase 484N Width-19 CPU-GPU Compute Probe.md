# Phase 484N — Width-19 CPU/GPU Compute Probe

Status: development benchmark; no execution lock; no FAED and no holdout fixtures.

## Question

Can the exact Phase 484J/K 20-feature prefix statistic be evaluated quickly
enough to support substantially wider width-19 beams?  Existing Python runs at
beam 4,096 take about 227–240 seconds per fixture and lose planted segments at
depth 8–10.

## Frozen benchmark shape

- Width 19, 30 rows, escape symbols 0 and 1.
- Deterministic valid partial permutations at depths 8 and 15.
- The CUDA and CPU kernels implement the same tokenization, 25 token counts,
  25x25 transition counts, entropy terms, boundary terms, raw-equality term,
  and token-lag coincidences 1 through 8 used by
  `phase484j_constructive_prefix_beam_probe.prefix_features`.
- Compare every GPU score against the CPU reference before accepting timing.
- Benchmark at least 65,536 paths, with warm-up excluded from timing.
- No puzzle stream, checkerboard solve, holdout fixture, or oracle is used.

## Decision rule

Use a hybrid CPU/GPU Phase 484N solver only if numerical parity holds and GPU
throughput is at least 10x the single-thread native CPU reference.  Beam state
generation, deduplication, endpoint/coverage diversity, and fragment stitching
remain on CPU; only dense score batches move to GPU.  Final complete orders are
rescored on CPU.

If the threshold fails, prefer a native/vectorized CPU implementation.  This
benchmark makes no cryptanalytic claim and cannot promote or retire a cipher
family.

## Development outcome

The compute gate passed: 24.9x–35.4x over the optimized single-thread native
CPU reference, with standalone CPU/GPU error below 9e-16 and end-to-end Python
adapter error below 2.8e-14.  At 262,144 paths the GPU evaluates roughly
9.3–11.0 million paths per second.  The hybrid scorer is therefore retained.

The wider search did not pass a cryptanalytic gate.  On the known failing
vic-profile development fixture, endpoint-diverse beams of 65,536, 131,072,
and 262,144 all lost the last genuine segment at depth 12.  The truth's depth-11
rank worsened to 205,670 at the largest beam.  The matched broad-random fixture
also lost truth at depth 12 with beam 65,536.

Coverage-set diversity, sums of overlapping fixed-depth windows (depths 6, 7,
and 8), and cumulative depth-specific scores (decays 0.5 and 0.1) did not
improve this boundary.  They lost truth between depths 9 and 12.  Thus GPU
acceleration solved the compute bottleneck but not the information/ranking
bottleneck.  No holdout fixture or FAED width-19 cell was used, and no current
design is eligible to advance to either.
