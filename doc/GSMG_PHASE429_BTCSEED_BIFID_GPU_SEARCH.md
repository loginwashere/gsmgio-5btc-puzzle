# GSMG Phase 429 — Reproducible BTCSEED Bifid GPU Search

Date: 2026-08-27

## Scope

Phase 429 implements the bounded `14! = 87,178,291,200` pure-relabeling
experiment proposed after Phases 425–428. It is an implementation and benchmark
phase, not authorization to start the full run.

The fixed Bifid grid retains the cells for every `FAED` source symbol
`A,B,C,D,E,F,G,H,I` and the remaining crib symbols `S,T`. The fourteen symbols
`KLMNOPQRUVWXYZ` are permuted over their original free cells. Since input
coordinates and all cells needed by the prefix remain fixed, every candidate
decodes positions `0:7` as exact `BTCSEED`. Only positions `7:570` are scored.

## Architecture

- standalone Rust crate and CUDA kernel under `tools/bifid_gpu_search/`;
- lexicographic `u64` Lehmer ranks, where rank zero is the original Bifid square;
- candidate generation and quadgram scoring entirely on the GPU;
- dense 25-letter quadgram table embedded from the pinned repository source;
- per-block maximum reduction, making the completed-range global maximum exact;
- double-buffered CUDA streams and compact block-result transfers, appropriate
  for the machine's OCuLink x4 connection;
- independent CPU reference and mandatory CPU/GPU probes at five ranks;
- deterministic fixed-range replay;
- atomic, fingerprint-bound resume checkpoint;
- pinned CUDA/Rust Docker build targeting the attached RTX 5070 (`sm_120`).

The retained block-winner shortlist is explicitly not an exact global top-K;
only its first entry—the maximum across all returned block maxima—is exact for
the completed range.

## Safety and interpretation

The GPU score is only frozen English quadgram likelihood over the held-out
tail. It makes no password, Bitcoin, or blob-oracle calls. A high-scoring square
would require CPU reproduction, matched null calibration, and coherent
held-out interpretation before promotion. The implementation does not broaden
the family to coordinate-changing `16!` squares.

## Reproduction

See `tools/bifid_gpu_search/README.md`. The standard sequence is container
build, mandatory self-test, bounded benchmark, review, and only then a separately
authorized full search.

## Validation and bounded benchmark

The final pinned image is
`sha256:3cc7e84cd9cf15072daf9728adad0bf218a01ef9a87570443467088bf8d97bad`.
Its container build executed all six Rust unit tests. On the attached NVIDIA
GeForce RTX 5070, the mandatory self-test passed isolated CPU/GPU score probes,
two bit-identical GPU replays, and an exhaustive CPU-versus-GPU winner check
over ranks `0:10000`. A separate one-million-rank search wrote an atomic
checkpoint and a second invocation resumed the already-complete interval
without rescanning it.

The final bounded one-billion-candidate benchmark took `0.891254796` seconds,
or `1,122,013,597.56` candidates/second. Linear extrapolation gives `77.70`
seconds of scan time for `14!`; a checkpointed full run will take longer due to
container startup, initialization, progress output, and checkpoint writes.
The exact winner only within the benchmarked range `0:1,000,000,000` was rank
`974015582`, score mean `-6.82801557`, square
`DBIFHCEGAKNLRUOPMSTWXYVQZ`. This bounded winner has no interpretive status.

## Full sweep result

After separate explicit authorization, the full `[0,14!)` sweep completed on
2026-08-27 without interruption. It covered all `87,178,291,200` candidates in
`78.354445772` seconds at `1,112,614,483.34` candidates/second. The terminal
checkpoint cursor is exactly `87178291200`.

The exact global quadgram maximum is rank `1013932382`, total score
`-3815.068`, mean score `-6.812621634`, square
`DBIFHCEGAKNMRUOPLSTWXYVQZ`, and decoded SHA-256
`fd016e0dd19b4246142833ffca8cd1905db49a4899acfa6d0d23ee8f2e060f2f`.
The independent CPU reference reproduces it exactly. Its continuation begins
`DEUEMCKEADHBSCHDKBDCSDKDXBVCOCUCHCLDICIBPEEBDDBCRDSBDCODGCODRCRC`;
the leading candidates remain mechanically structured rather than readable
plaintext, so this score maximum is not promoted as a puzzle solution.

The complete result is `phase429_full_result.json` (SHA-256
`f0986a841dff6bfc2b3230c0c39011a90ea31da90f4edfc148953623d2c8dd99`),
with terminal checkpoint `phase429_terminal_checkpoint.json` (SHA-256
`4af3d8a5b608884d54f7f42bb8a4b30c36046d8d6e14d66515d4978b84e0307a`).
Benchmark manifests remain preserved alongside them.
