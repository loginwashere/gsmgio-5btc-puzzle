# Phase 430 — BTCSEED Bifid Dynamic-Coordinate Alphabet GPU Search Pre-Registration

## Purpose

Build and validate a reproducible GPU search for the bounded `16!` Bifid
dynamic-coordinate alphabet family defined after Phase 429. Implementation and validation must pass before the separately authorized complete sweep starts.

## Frozen search family

- authenticated input: the 570-letter `FAED` string;
- Bifid convention: Phase 386's one-block, row-then-column decrypt;
- base square: `DBIFHCEGAKLMNOPQRSTUVWXYZ`;
- fixed symbols: `ABCDEFIST` in their Phase-386 cells. `ADEFI` are the
  unique FAED symbols feeding the first seven row/column coordinate pairs;
  `BCDEST` are the unique output symbols spelling `BTCSEED`; their union has
  nine symbols;
- permuted symbols: `GHKLMNOPQRUVWXYZ`, assigned to their sixteen original
  cells in lexicographic-permutation order;
- rank domain: `[0, 16!) = [0, 20922789888000)` using lexicographic Lehmer
  unranking; rank zero is the original Phase-386 square;
- every candidate must retain exact `BTCSEED` at decoded positions `0:7`;
- score only `decoded[7:]`, never the sealed prefix.

This is the dependency-derived coordinate-changing family: moving `G` or `H`
changes tail input coordinates, while the frozen dependency union proves that
every candidate retains exact `BTCSEED`.

## Frozen primary score

Average English log10 quadgram likelihood over all 560 overlapping quadgrams
of the 563-character tail, using the repository's existing
`tools/gsmg/data_files/english_quadgrams.txt` table and its established unseen
floor `log10(0.01 / total_count)`. Higher is better.

The GPU may retain block winners to make result transfer bounded. The global
maximum remains exact because every CUDA block returns its maximum and the host
compares every returned block maximum. Any retained lower-ranked block winners
are an inspection shortlist, not a claim of exact global top-K ordering.

## Implementation and validation gates

- standalone Rust/CUDA crate under `tools/bifid_gpu_search16/`;
- candidates generated and scored entirely on-device from `u64` rank ranges;
- no candidate wordlist or per-candidate host/device transfer;
- CPU reference for unranking, square construction, Bifid cell stream, and
  quadgram score;
- mandatory CPU/GPU equality checks at ranks `0`, `1`, `2`, `12345`,
  `15!`, `2*15!`, and `16!-1`, with a documented floating-point tolerance;
- rank zero must reproduce Phase 386's complete decoded SHA-256 and exact
  prefix;
- deterministic fixed-range replay must return the same winner;
- range bounds, block-result validity, and checkpoint fingerprints are hard
  failures, never warnings;
- checkpoints store an atomic next-rank cursor and retained winners, bound to
  input, model, kernel, driver, family, and score hashes;
- Docker build pins CUDA base-image digests, Rust version, `Cargo.lock`, and
  native `sm_120` target; Compose exposes only output/checkpoint directories as
  writable volumes;
- benchmark reports candidates/second and extrapolated `16!` duration on the
  attached GPU, without claiming completion.

## Exclusions

- no full `16!` launch in the implementation phase without a separate explicit
  instruction;
- no square outside this exact nine-fixed, sixteen-permuted family;
- no dictionary, compression, mutual-information, repeat, password, Bitcoin,
  or blob-oracle scoring in the GPU sweep;
- no promotion from a short word or from the already-sealed `BTCSEED` prefix;
- no claim that block-winner shortlists are an exact top-K beyond the exact
  global maximum.
