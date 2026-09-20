# Phase 538 — FAED lanes read through DBBI's host masks

2026-09-20. Result: **bounded negative; zero oracle hits and no calibrated lead**.

## Question

FAED is `6 x 91 + 24` symbols and DBBI is 91. DBBI's prime-host parse fixes
which raw positions are host characters. Phase 48 recovered that 31-position
mask and Phases 49 and 474 applied it to one 91-character object, the
Phase 3.2.2 answer. Does the same mask, or Selection A's 30-position mask,
select anything meaningful from FAED's six 91-symbol lanes? Nothing in
Phases 33, 45, 274, 518, 520-521 or 525-537 did this (comparison table in the
protocol). Exploratory; motivated by an unverified community remark
(chat message 71986), not a creator-selected recipe. Protocol:
[doc/Brainstorms/2026-09-20 - Phase 538 ... Protocol.md](Brainstorms/2026-09-20%20-%20Phase%20538%20FAED%20Lane%20Host-Mask%20Extraction%20Protocol.md),
written and locked before any real lane was read through a mask.

## Frozen family

Masks `M31` (83-token parse; identical to Phase 48's recorded 31 positions) and
`M30` (84-token parse, Selection A; `M31` without position 91). Per mask and
lane: host `H`, complement `C`, single-`b` hosts `Hb`, `be` hosts `Hy`; six
lanes plus lane-major and position-major pooling: **64 unique base strings**
(no A1Z26, case, reversal or other transform). The 24-symbol tail was excluded.

## Controls (before any real lane was read)

- **Precedent:** `M31` on the 91-character Phase 3.2.2 answer reproduces
  `ncsyangcahiriasogaleafayanestve`, the Phase 49 complement, the yellow rail
  and the blue-plus-FEFE rail multiset. (The `...irivasoalbefay...` string in
  the untaken-paths note is a misprint; the repository's own Phase 48 mask gives
  `...iriasogaleafay...`.)
- **Extraction exactness:** all 64 reads return the expected elements in the
  expected order on a 570-element stream of distinct values.
- **Gate recovery:** planted concentrated-pair and identical-column masks were
  detected in 20/20 trials at 0%, 25% and 50% noise (2,000 replicates; the
  smallest add-one tail 1/2001 is below the 0.0005 threshold, which 1,000
  replicates could never reach, so the protocol was corrected before locking).
- **False-positive context:** 100 shuffled FAED streams: 0 S1 leads, 1 S2 lead
  (about what a two-sided test at this threshold gives across 100 draws).

## Results

**Arm 1, oracle.** 64 bases expanded to 1,152 passphrase forms (18 per base) on
the 60-variant table against all authenticated blobs, Docker image
`gsmg-gpu-oracle:phase524-kt`, `--newline-variants`. Self-test passed, the
Bloom cache loaded and the eight known targets were folded in. Strong 0,
structural 0, weak 0, keyshape records 0, known-target matches 0. The
checkpoint recorded all 1,152 forms; wall time 75 s.

**Arm 2, structural gate** (20,000 replicates, seed 538):

| Statistic | Cells | Family-max z | Cell | Add-one tail | Lead |
|---|---:|---:|---|---:|---|
| S1 top-2 concentration | 28 | 2.54 | `M31/L4/C` | 0.210 | no |
| S2 cross-lane column agreement | 4 | 0.10 | `M30/H` | 0.995 | no |

The `M31/L4/C` concentration is what a family maximum over 28 partly
dependent cells is expected to look like under the null. Host columns are, if
anything, indistinguishable from random columns in cross-lane agreement.

## Scope and stop

FAED read through DBBI's host mask over six forward 91-symbol lanes is not a
source of a password, a checkpoint or lane structure. This rejects this family,
not the idea that DBBI and FAED are related. Other masks (including the
historical event-start selection), other partitions such as `2 x 285`, the
tail, reversal, offsets and symbol mappings were outside the family and do not
become next steps because this one failed. FAED remains undecoded and no fact
about any blob, key or address changes.

## Reproduction

```bash
python3 tools/gsmg/phase538_faed_lane_extraction.py --self-test
python3 tools/gsmg/phase538_faed_lane_extraction.py --run-gate   # verifies the lock first
# GPU arm (recipe as in Phase 524 run 3), outputs in tools/gpu_oracle/output_local/phase538.*
python3 tools/gsmg/phase538_faed_lane_extraction.py --verify-oracle
python3 tools/gsmg/phase538_faed_lane_extraction.py --classify-weak
python3 tools/gsmg/run_frontier_tests.py --start 538 --end 538
```

Files: `tools/gsmg/phase538_faed_lane_extraction.py`,
`test_phase538_faed_lane_extraction.py` (9 tests), `phase538_faed_lane_lock.json`
(SHA-256 `9247fb1f...9cc2a08`), `phase538_faed_lane_gate_result.json`, base list
`_work/phase538/bases.txt` (gitignored, digest in the lock). The GPU outputs are
gitignored; `--verify-oracle` reports the expected base count 64 under
`expected_forms` because it forwards the lock's candidate count, while the
checkpoint holds the 1,152 expanded forms.
