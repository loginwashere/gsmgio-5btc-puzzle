---
type: source
phase: 322
date: 2026-08-20
status: live
disposition: operative
evidence_level: solver-derived
topics:
  - gpu
  - oracle
  - tooling
  - openssl
related_phases: [322, 323, 326, 327, 328, 331, 332, 333]
---

# GSMG GPU AES/KDF Oracle

A CUDA-accelerated port of `tools/gsmg/cb_common.py`'s AES-CBC/ECB/CFB/OFB/CTR
oracle plus an opt-in SEED-CBC family, built at `tools/gpu_oracle/` as a
standalone Rust+CUDA project. This is infrastructure, not a phase result by
itself -- see "Sweeps run through this tool" below for the actual
candidate-universe tests it's been used for. Originally built Phase-1-scoped
(AES-CBC only, Phase 322); Phase 328 merged the stream-cipher/ECB modes and
Bloom/API raw-key checking directly into the same kernel (see "Scope" below
for current coverage -- this section is kept current, not a historical
snapshot of the Phase 322 launch state).

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

## Scope (current, as of Phase 332)

`cb_common.py`'s full oracle covers CBC across 5 cipher families (AES/3DES/
Blowfish/Camellia/SEED), plus ECB, CFB/OFB/CTR, and AES Key-Wrap (RFC
3394/5649) -- over 100 variant configs. This tool's **default** variant table
(`blobs::variant_table()`) covers:

- KDF: legacy-MD5, legacy-SHA1, legacy-SHA256 (`EVP_BytesToKey`, single-round
  iterated digest), PBKDF2-HMAC-SHA256/10000 iterations -- 4 KDF configs
- AES key sizes: 128/192/256 -- 3 sizes
- AES cipher modes: **CBC, ECB, CFB, OFB, CTR** -- 5 modes (Phase 322 shipped
  CBC only; Phase 328's kernel merge added the other 4 directly into the same
  `aes_kdf_scan` kernel, not a separate pass)
- 60 variants x 4 tracked blobs (SALPH/COSMIC/P32TRAILING/URLBLOB) = 240
  (variant, blob) pairs per candidate keystring
- Gate, CBC/ECB: PKCS7 pad check → `printable_z_score` (weak ≥5.0 logged
  only, strong ≥8.0 = hit) → `is_structural_binary_plaintext` bypass (full
  dummy PKCS7 pad block, `pad == 16`, any body length) → (Phase 328)
  unconditional raw-key Bloom check of the first two 32-byte chunks even on
  a non-printable, non-structural body, since a real key doesn't have to
  look like English text
- Gate, CFB/OFB/CTR: no padding to check, so straight to `printable_z_score`
  plus the same unconditional raw-key Bloom check (this was the *original*
  motivation for the Bloom-chunk path, generalized to CBC/ECB by Phase 328)
- **Opt-in**, not in the default table: SEED-CBC (`--seed-cbc`, Phase 326,
  4 variants, one per KDF kind, fixed 128-bit key)

**Bloom/API address checking** (ported from `../../../key-seeker`, Phase 332
retroactively numbered -- see `checker/`): any raw-key-shaped 32-byte chunk
recovered by the paths above is hashed to a P2PKH address (compressed and
uncompressed) and checked against a Bloom filter of funded/used addresses,
loaded from `db/addresses.hash160.bloom`; a Bloom hit is *never* treated as
real on its own -- it's mandatorily re-confirmed against the live
Blockstream API before counting. Phase 331 additionally folds in 8 specific
target hash160s (the prize public key's on-chain "neighbors, half and
double" -- see `checker::known_targets`) that bypass the funded-balance gate
entirely on an exact match, since a decrypt landing on one of those specific
points is worth surfacing regardless of whether that address currently holds
a balance.

**Explicitly out of scope, not abandoned:** 3DES/Blowfish/Camellia/AES
Key-Wrap (bigger lift, different cipher algorithms or modes, lower
historical hit priority per this project's own docs). A wordlist run through
this tool with default settings is **not** equivalent to the CPU oracle's
full coverage -- it's the AES-CBC/ECB/CFB/OFB/CTR subset (plus opt-in
SEED-CBC), not the full cipher-family list.

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
   across every default variant and every tracked blob.
3. (Phase 326) A synthetic SEED-CBC positive vector must recover as
   Structural on GPU; a negative probe grid must agree between GPU and CPU.
4. (Phase 328) A synthetic AES-CBC body shaped as [private key | filler |
   PKCS7 pad != block size] (non-printable, non-structural, so the CPU
   z-score gate alone sees no hit at all) must still be recovered by the GPU
   via the unconditional raw-key Bloom-chunk path.

All four run automatically before every real sweep (`--skip-self-test` to
bypass, not recommended). First validated 2026-08-19: GPU reproduced z=21.77
on the known-positive vector (matching CPU exactly within tolerance), and
100% GPU/CPU agreement across the 12-candidate x 12-variant x 4-blob negative
grid (576 combinations, including the PBKDF2 variants) -- the negative grid
now runs against the full 60-variant default table. Checks 3-4 added Phase
326/328 and still pass as of the Phase 332/333 changes.

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

## Second sweep: medium-curated Tier 1-3 union, all 4 blobs

See FINDINGS.md Phase 323. Before running anything, audited which oracle(s)
`wordlists/gsmg/medium_curated_all.txt` (66,433 base candidates, the Tier
1+2+3 union) had actually already been tested under: Phase 83/90's
`binary_key_material_backfill.py` covered Tier 1+2 (35,144 candidates)
against SALPH/P32TRAILING only, using this same 12-variant AES-CBC/KDF scope
-- but never touched COSMIC/URLBLOB, and Tier 3 (31,297 candidates) had only
ever been tested under a *different* hypothesis (Phase 164's raw-key oracle,
no KDF derivation at all), never the password/KDF oracle against any blob.
Ran the full union against all 4 blobs in one sweep: 588,942 expanded forms,
~28.3M decrypt attempts, 3m16s. **Zero hits.** Closes real gaps (COSMIC +
URLBLOB for the whole union; SALPH + P32TRAILING for Tier 3 specifically) and
confirms (does not newly close) SALPH/P32TRAILING for Tier 1+2, already
covered by Phase 83/90.

## SEED-CBC cipher family, GPU-ported

See FINDINGS.md Phase 326. Ported OpenSSL's SEED cipher
(`crypto/seed/{seed_local.h,seed.c}`) to both a Rust CPU reference
(`src/seed_cipher.rs`, pinned against all 4 RFC 4269 known-answer vectors)
and a CUDA device port in `kernels/aes_kdf_oracle.cu`, as `CIPHER_SEED_CBC`
-- an opt-in 4-variant table (`--seed-cbc`), not merged into the default
60-variant AES table. Closes the one gap Phase 255 explicitly declined to
run for cost reasons: `medium_curated_all.txt`'s 66,433 candidates had never
had SEED-CBC coverage. 588,942 forms x 4 variants x 4 blobs = 9.4M decrypt
attempts in 40s. **Zero hits.** Blowfish/Camellia/3DES/AES-Key-Wrap remain
deferred (not GPU-ported).

## Stream-cipher/ECB merge into the main kernel, and raw-key Bloom coverage

See FINDINGS.md Phase 328 (and Phase 332 for the earlier work -- kernel
merge, Bloom/API port, key-shape classifier -- this section's predecessor,
retroactively documented after its in-code comments were found citing two
phase numbers FINDINGS.md never actually used). ECB/CFB/OFB/CTR were merged
into `aes_kdf_scan` alongside CBC (see "Scope" above); a raw-key Bloom check
of the first two 32-byte chunks, previously only run on CFB/OFB/CTR
candidates, was extended to CBC/ECB/SEED_CBC too, unconditionally (i.e. even
on a non-printable, non-structural body -- a real key doesn't have to look
like readable text). Re-ran `medium_curated_all.txt` (66,433 candidates)
under the full 60-variant default table with the extended Bloom coverage:
588,942 forms, 240 (variant, blob) pairs, 921s. **43 weak hits (Phase
333 formally swept all 43 through the hex64/WIF/BIP39 key-shape classifier:
zero matches), 0 strong, 0 structural, 3 Bloom hits (all from the
pre-existing stream-mode path), all 3 rejected by the mandatory live API
check.**

## Known-target detector: prize pubkey's EC neighbors, half and double

See FINDINGS.md Phase 331. Eight specific hash160s -- the prize public key's
`P+G`, `P-G`, `P/2`, and `2P` points (compressed and uncompressed), matching
a community-posted OP_RETURN reading "GSMG.io neighbors, half and double" --
are folded into the Bloom filter uploaded to the GPU (`BloomChecker::
insert_extra`) and additionally checked host-side via `checker::
KnownTargetsChecker`, which returns a Hit on an exact match unconditionally,
bypassing the ordinary funded-balance gate (4 of the 8 addresses have never
been funded and would otherwise be silently dropped as false positives).
The prize pubkey was independently re-derived from the six real on-chain
transactions that spend from the prize address, not copied from the
community post. No sweep hit this target set as of Phase 331/332/333.

## Third sweep: k=8 macro-clue permutations

See FINDINGS.md Phase 334. Phase 322's `MAX_K = 7` deliberately excluded
all-8-fragment permutations; `macro_clue_permutation_combinations.py
--write-k8` generates the omitted P(8,8) = 40,320-combination space as a
separate, explicitly opt-in corpus -- `wordlists/gsmg/
macro_clue_permutation_combinations_k8.txt` -- rather than silently widening
the k=1..7 corpus Phase 322 already swept. Run against the current default
60-variant table (all 4 blobs, Bloom/API pipeline including Phase 331's
known targets active): 725,760 expanded forms x 240 (variant, blob) pairs =
174,182,400 decrypt attempts in 3,021s. **42 weak hits (same noise band as
every prior sweep at this scale), 0 strong, 0 structural, 5 Bloom hits, all
5 rejected by live API confirmation, 0 confirmed funded, 0 matches against
the known EC-derived targets.** Closes Phase 322's explicit k=8 reopen
condition -- the macro-clue-concatenation hypothesis is now exhausted at
every subset size, k=1..8.
