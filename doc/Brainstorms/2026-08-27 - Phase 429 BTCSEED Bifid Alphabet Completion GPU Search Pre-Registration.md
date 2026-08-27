# Phase 429 — BTCSEED Bifid Alphabet-Completion GPU Search Pre-Registration

## Purpose

Build and validate a reproducible GPU search for the bounded `14!` Bifid
alphabet-completion family suggested after Phase 428. This phase implements and
benchmarks the search engine; it does not silently launch the complete sweep.

## Frozen search family

- authenticated input: the 570-letter `FAED` string;
- Bifid convention: Phase 386's one-block, row-then-column decrypt;
- base square: `DBIFHCEGAKLMNOPQRSTUVWXYZ`;
- fixed cells: all nine ciphertext symbols `A` through `I` (with no `J`) plus
  `S` and `T`;
- permuted symbols: `KLMNOPQRUVWXYZ`, assigned to their fourteen original
  free cell positions in lexicographic-permutation order;
- rank domain: `[0, 14!) = [0, 87178291200)` using lexicographic Lehmer
  unranking; rank zero is the original Phase-386 square;
- every candidate must retain exact `BTCSEED` at decoded positions `0:7`;
- score only `decoded[7:]`, never the sealed prefix.

This is the pure output-relabeling family. It does not include the broader
`16!` family in which input-coordinate letters move.

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

- standalone Rust/CUDA crate under `tools/bifid_gpu_search/`;
- candidates generated and scored entirely on-device from `u64` rank ranges;
- no candidate wordlist or per-candidate host/device transfer;
- CPU reference for unranking, square construction, Bifid cell stream, and
  quadgram score;
- mandatory CPU/GPU equality checks at ranks `0`, `1`, `2`, `12345`, and
  `14!-1`, with a documented floating-point tolerance;
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
- benchmark reports candidates/second and extrapolated `14!` duration on the
  attached GPU, without claiming completion.

## Exclusions

- no full `14!` launch in the implementation phase without a separate explicit
  instruction;
- no `16!` coordinate-changing family;
- no dictionary, compression, mutual-information, repeat, password, Bitcoin,
  or blob-oracle scoring in the GPU sweep;
- no promotion from a short word or from the already-sealed `BTCSEED` prefix;
- no claim that block-winner shortlists are an exact top-K beyond the exact
  global maximum.
