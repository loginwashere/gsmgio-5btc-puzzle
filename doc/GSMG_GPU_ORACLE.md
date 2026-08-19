---
type: audit
phase: 322
date: 2026-08-19
status: live
result: infrastructure
disposition: operative
evidence_level: solver-derived
topics:
  - gpu
  - oracle
  - tooling
  - openssl
related_phases: [322]
---

# GSMG GPU AES/KDF Oracle

A CUDA-accelerated, Phase-1-scoped port of `tools/gsmg/cb_common.py`'s
`aes_try_open_bytes()` (the AES-CBC branch), built at `tools/gpu_oracle/` as a
standalone Rust+CUDA project. This is infrastructure, not a phase result by
itself -- see "First real sweep" below for the actual candidate-universe test
this tool was built for.

## Why this exists

Password-candidate sweeps in this project run entirely on CPU. That's fine at
the scale most sweeps operate at (tens of thousands to low millions of
keystrings), but the project wanted a GPU path invested in once so future,
larger sweeps get real speedup rather than re-deriving this each time.

The sibling repo `../key-seeker` (a mature Rust+CUDA Bitcoin weak-key tool) was
checked for reusable pieces first. It does no AES or KDF hashing at all -- its
only kernel is secp256k1 elliptic-curve math for a different problem
(passphrase → private key → address, not passphrase → AES key → decrypt). What
*was* reusable is its host-side Rust/CUDA scaffolding (`cudarc` wiring, the
`build.rs` nvcc→PTX pattern, checkpoint/output conventions, the
fixed-capacity-hit-buffer GPU launch pattern from `src/gpu/milksad.rs`) --
copied into `tools/gpu_oracle/` and adapted; the actual crypto kernel is
written fresh.

## Scope: Phase 1, AES-CBC only

`cb_common.py`'s full oracle covers CBC across 5 cipher families (AES/3DES/
Blowfish/Camellia/SEED), plus ECB, CFB/OFB/CTR, and AES Key-Wrap (RFC
3394/5649) -- over 100 variant configs. This tool covers exactly the union of
`KDF_VARIANTS` and the AES portion of `EXTENDED_CIPHER_VARIANTS`:

- KDF: legacy-MD5, legacy-SHA1, legacy-SHA256 (`EVP_BytesToKey`, single-round
  iterated digest), PBKDF2-HMAC-SHA256/10000 iterations -- 4 KDF configs
- AES key sizes: 128/192/256 -- 3 sizes
- 12 variants x 4 tracked blobs (SALPH/COSMIC/P32TRAILING/URLBLOB) = 48
  (variant, blob) pairs per candidate keystring
- Gate: PKCS7 pad check → `printable_z_score` (weak ≥5.0 logged only, strong
  ≥8.0 = hit) → `is_structural_binary_plaintext` bypass (SALPH/P32TRAILING's
  64-byte-body/full-pad case), matching `cb_common.py` exactly

**Explicitly out of scope, not abandoned:** AES-ECB/CFB/OFB/CTR (cheap
follow-up -- same AES core, different chaining) and 3DES/Blowfish/Camellia/
SEED/Key-Wrap (bigger lift, different cipher algorithms, lower historical hit
priority per this project's own docs). A wordlist run through this tool is
**not** equivalent to the CPU oracle's full coverage -- it's the AES-CBC
subset only.

## Correctness validation

A subtly wrong AES/KDF port would silently produce false negatives across an
entire sweep -- worse than a crash, since it looks like a clean completed run.
`--self-test` (run automatically before every real sweep unless
`--skip-self-test` is passed) checks two things against an independent CPU
reference oracle (`src/cpu_oracle.rs`, built from well-tested RustCrypto
crates, not a second hand-rolled implementation):

1. The known-positive Phase 3.2 vector (`data.PHASE32_BLOB_B64`, password
   `SHA256("jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple")`)
   must produce a Strong hit on GPU with a z-score matching the CPU reference
   within 0.05.
2. A batch of known-negative candidates (the 8 creator macro-clue fragments
   plus a few generic strings) must produce **identical**
   (candidate, variant, blob) → hit-kind classification between GPU and CPU,
   across every Phase-1 variant and every tracked blob.

Both passed on first real run (2026-08-19): GPU reproduced z=21.77 on the
known-positive vector (matching CPU exactly within tolerance), and 100%
GPU/CPU agreement across the 12-candidate x 12-variant x 4-blob negative grid
(576 combinations, including the PBKDF2 variants).

## Checkpoint fingerprinting

Matches this project's existing Python sweep convention
(`stream_mode_cipher_sweep.py`, `nopad_window_sweep.py`): every checkpoint's
JSONL header binds `candidate_digest` (sha256 of the ordered candidate list),
`blob_digest`, `variant_digest`, and source hashes for the kernel and driver.
Loading a checkpoint whose header doesn't match byte-for-byte is a hard
error, never a silent reuse -- see `src/checkpoint.rs`.

## Performance

Measured on this project's dev machine (NVIDIA RTX 5070, compute capability
12.0), single-stream, no other GPU load:

- ~2,200-3,800 candidates/sec depending on batch composition (throughput
  drops as more of a batch's variant/blob combinations reach the PBKDF2/10000
  branch, which is ~30-100x more expensive per candidate than the legacy-KDF
  branches by design -- that's PBKDF2 working as intended, not a bug).
- For comparison, this project's CPU sweeps have historically run
  ~20-25 keystrings/sec single-threaded, ~125-190/sec at 8 workers, for a
  comparable variant/blob scope.

Any hit (weak, strong, or structural) is written to the output JSONL and
printed, but **must still be re-verified through the Python `cb_common.py`
oracle before being treated as real** -- this tool is a faster finder, not a
replacement source of truth, same house rule as every other candidate this
project has ever tested.

## Reproduction

```bash
cd tools/gpu_oracle
docker compose build
docker compose run --rm gpu-oracle --self-test
docker compose run --rm gpu-oracle \
  --wordlist /data/wordlists/gsmg/<file>.txt \
  --newline-variants \
  --checkpoint /data/checkpoints/<name>.checkpoint \
  --output /data/output/<name>.jsonl
```

`docker-compose.yml` mounts the repo's own `wordlists/` directory read-write
into the container, so any existing candidate corpus under `wordlists/gsmg/`
is usable directly by path.

## First real sweep: creator-authored macro-clue fragment combinations

See FINDINGS.md Phase 322. `tools/gsmg/macro_clue_permutation_combinations.py`
generates every order-sensitive combination (P(8,k), k=1..7, no repeats) of
the 8 fragments in `promised_standalone_audit.MACRO_CLUE` -- the only strings
this project has established as literally the creator's own authored text
(decoded from their binary Telegram message), as opposed to solver-derived
numeric artifacts or third-party movie-quote reconstructions. 69,280 base
combinations, expanded via `answer_forms()`/`keystr_forms(newline_variants=
True)` to 1,247,040 passphrase forms, swept against all 48 (variant, blob)
pairs (~59.9M decrypt attempts) in 9m27s. **Zero hits** -- not one weak,
strong, or structural hit anywhere in the space.
