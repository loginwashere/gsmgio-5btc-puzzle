# BTCSEED Bifid GPU Search

Standalone Rust/CUDA implementation of Phase 429's frozen `14!` alphabet-
completion search. It keeps all nine `FAED` source-symbol cells plus `S,T`
fixed, permutes `KLMNOPQRUVWXYZ` over fourteen free cells, guarantees the
decoded prefix remains `BTCSEED`, and scores only the 563-character tail with
the repository's pinned English quadgram model.

The GPU receives rank ranges, not candidate strings. It performs lexicographic
Lehmer unranking, output relabeling, and all 560 quadgram lookups per candidate
on-device. Each CUDA block returns its exact maximum. Consequently the final
global maximum over a completed range is exact; the additional retained block
winners are an inspection shortlist and are not asserted to be the exact
global top-K.

## Reproducible container build

The Dockerfile pins CUDA builder/runtime image digests, Rust `1.94.1`, the
locked Cargo dependency graph, and the RTX-5070 `sm_120` target.

```bash
cd tools/bifid_gpu_search
docker compose build
docker compose run --rm bifid-search self-test
```

The NVIDIA host driver remains external to the image. Every result manifest
records the GPU name, source/input/model hashes, CUDA architecture, range, and
measured throughput.

## Bounded benchmark

The benchmark runs the mandatory self-test first unless explicitly disabled:

```bash
docker compose run --rm bifid-search benchmark \
  --candidates 100000000 \
  --output /data/output/benchmark_100m.json
```

For quick tuning, vary `--grid-size` and `--stride`. Defaults are grid 2048,
block 256 (frozen in the kernel), and stride 64.

The repository preserves final bounded manifests as
`benchmark_100m_result.json` and `benchmark_1b_result.json`. These are
performance/validation artifacts, not full-family search results.

## Search and resume

A complete run is never started by the container automatically. It requires an
explicit command:

```bash
docker compose run --rm bifid-search search \
  --start 0 \
  --end-exclusive 87178291200 \
  --checkpoint /data/checkpoints/bifid_14factorial.json \
  --output /data/output/bifid_14factorial_result.json
```

Ctrl-C stops after the in-flight batch. The checkpoint is atomically replaced
and refuses resume if the family, range start/end, FAED data, decoded cell
stream, quadgram model, kernel, host driver, architecture, or score contract
changes.

The authorized Phase 429 full sweep is preserved as
`phase429_full_result.json`, with its completed resume state in
`phase429_terminal_checkpoint.json`.

## CPU reference

CPU-only validation does not require CUDA:

```bash
cargo test --manifest-path tools/bifid_gpu_search/Cargo.toml --offline
cargo run --manifest-path tools/bifid_gpu_search/Cargo.toml -- cpu-score --rank 0
```

Rank zero must reproduce decoded SHA-256
`0c5d984f90e9baefc09f1d3888e62acbd101f9b0194887e2ae88fc6c9967745e`.
