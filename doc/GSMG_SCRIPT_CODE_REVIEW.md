# GSMG Script Code Review

Date: 2026-07-24

Scope: all Python programs under `tools/gsmg`, with emphasis on shared
checkerboard decoding, AES candidate detection, multiprocessing configuration,
candidate validity, result accounting, and statistical claims.

## Confirmed defects fixed

### 1. Dangling checkerboard escapes were silently truncated

`cb_common.decode()` and `decode_9ary()` stopped decoding when the final symbol
was an escape without its required second symbol. The returned prefix looked
valid, and normalization could then send that truncated text to AES.

The decoders now append `?`, the existing invalid-decode marker. Chained,
cross-target, crib-drag, and hill-climbing consumers now reject such candidates
instead of normalizing the marker away.

Impact on old results: this inflated candidate/attempt counts and could create
misleading candidate hits. It does not hide a valid checkerboard decode because
a dangling escape is not a complete code.

### 2. Explicit empty AES scopes expanded to defaults

`aes_try_open_bytes()` selected defaults with:

```python
kdf_variants or KDF_VARIANTS
blobs or BLOBS
```

Therefore an explicit empty KDF list tested all KDF variants, and an explicit
empty blob map tested both open targets. Selection now distinguishes `None`
(use defaults) from an empty collection (test nothing).

This is the same class of silent-default bug previously found in
`cosmic_sweep_9ary.py`.

### 3. Invalid option strings silently selected another algorithm

Several shared helpers treated every unknown value as their `else` branch:

- unknown merge direction became `forward`;
- unknown board topology became `escapes_first`;
- unknown autokey mode became `plaintext`;
- unknown keyed-columnar direction became `decrypt`.

These helpers now validate modes and raise `ValueError`. Column transforms also
reject zero/negative periods, and 9-ary boards validate alphabet length and
distinct `a`-`i` escape symbols.

### 4. 9-ary multiprocessing depended on forked globals

`cosmic_sweep_9ary.py` applied CLI settings by mutating module globals before
creating workers. This works with Linux `fork`, but spawn-based workers import
the module defaults and silently ignore the requested transforms, topologies,
escape pair, KDF scope, and related options.

The sweep now passes an immutable `SweepConfig` to each worker. CLI values are
validated before work starts. A regression test forces the `spawn` start method.

### 5. OpenSSL digest history was incorrect

Comments said `openssl enc` used MD5 by default until OpenSSL 3.0. The default
digest changed from MD5 to SHA-256 in OpenSSL 1.1.0, before the puzzle's 2019
launch. The KDF ordering remains SHA-256 first, with MD5 and SHA-1 retained as
explicit hypotheses. See the
[official OpenSSL `enc` history](https://docs.openssl.org/3.3/man1/openssl-enc/).

### 6. AES hits were described as authenticated conclusions

The AES helper checks PKCS7 padding and unusually printable plaintext. That is a
strong plausibility filter, but CBC provides no authentication and a printable
false positive has already occurred in this investigation.

Messages and documentation now call these candidate/plausibility hits requiring
inspection. The known Phase 3.2 vector remains an end-to-end positive regression.

### 7. Script-specific correctness and accounting defects

- `chain_addition_sweep.py` mixed alphabet-candidate and candidate-pair units in
  progress/ETA reporting; both now use total pairs.
- `lastcommand_probe.py` claimed to test only the SalPhaseIon blob but called the
  two-target helper; it now scopes the call to SalPhaseIon.
- `dual_ternary_sweep.py` counted exact duplicate symmetry-derived streams as
  independent tests. Exact duplicates are now removed, and the overlapping-lag
  z-score is explicitly labeled heuristic.
- `quadgram_solver.py` claimed to AES-check every local optimum but only checked
  the top `TOPN`; its documentation now matches behavior. Hard-coded repository
  paths were replaced with paths derived from `__file__`.
- `door_prime_passport_probe.py` wrote into `hits.txt`, colliding with
  `cosmic_sweep.py`; it now uses `hits_door_prime_passport.txt`.
- `matrix_instruction_sweep.py` deduplicates AES passphrases per worker chunk,
  not globally; output now reports “chunk-deduplicated” checks.
- `grid_spiral.py` now accepts `--image` and derives its default from the user's
  home directory instead of embedding one absolute username path.

## Validation performed

- `python3 -m compileall -q tools/gsmg`
- `python3 tools/gsmg/test_cb_common.py` — 9 tests passed
- known Phase 3.2 AES/KDF/decryption positive vector
- explicit empty KDF and blob scope regressions
- dangling decimal and 9-ary escape regressions
- keyed-columnar round trips and invalid-mode regressions
- forced spawn-process 9-ary configuration regression
- `dual_ternary_sweep.py --self-test --periodicity` smoke test
- one-candidate smoke runs for the 9-ary, chained, chain-addition, autokey, and
  quadgram paths
- last-command probe and crib-drag smoke runs
- `git diff --check`

## Remaining risks

### Append-only hit files

Most long sweeps append to fixed hit files. A file from an earlier run can be
mistaken for a hit from the current run, while a current zero-hit run does not
clear old content. This review did not automatically delete or truncate those
files because they may contain investigation history.

For defensible runs, use a fresh `--hits-out` filename or remove/archive the old
file before starting. A future cleanup should add explicit `--append-hits` and
make per-run output the default.

### AES plausibility false positives

The printable z-score plus valid padding is not an authenticated decryption.
Every hit must still be checked for coherent plaintext, clue fit, reproducibility,
and preferably a known prefix/format. Broader KDF sweeps increase the number of
opportunities for accidental candidates.

### Historical result labels

Negative runs still contain the primary SHA-256/AES-256 hypothesis when they
used the broad shared default, but attempt counts and labels that claimed a
narrower KDF scope should not be trusted without rerunning. The repaired 9-ary
book sweeps are the reliable baseline for that branch.

### Statistical gates

The dual-ternary lag analysis uses overlapping comparisons, so its binomial
z-scores are a ranking heuristic rather than a calibrated proof. Exact duplicate
streams are removed, and the observed negative conclusion remains unchanged,
but a permutation max-statistic would be needed for a stronger formal test.

### Local evidence paths

The screenshot extractor intentionally defaults to the local
`~/Pictures/Screenshots` corpus, and some page/image audit tools expect a separate
site mirror. Their paths are configurable or task-specific, but reproducing those
results requires preserving the source-image manifest and hashes.

## Review conclusion

The shared decoder and AES pipeline now have focused regression coverage, and
the newly repaired book sweeps remain negative. No new solution hit was found.
The most important interpretation change is that AES output is a plausibility
candidate, not proof, and run provenance must include exact KDF/blob scope and a
fresh result file.
