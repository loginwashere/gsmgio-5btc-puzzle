# Phase 538 — FAED lanes read through DBBI's host masks

Status at creation: protocol, written before any FAED lane has been read
through either mask. No lane-selected string, gate statistic, or oracle result
exists yet. Everything below is frozen by the execution lock described at the
end; nothing is chosen after a result.

## Claim and novelty

FAED is exactly `6 x 91 + 24` symbols (Phase 274 six-lane structure, tested by
`dbbi_faed_six_lane_audit.py`). DBBI is exactly 91 symbols, and its prime-host
parse fixes which of the 91 raw positions are host characters. The project has
used that 91-position mask on one 91-symbol object only: the Phase 3.2.2
answer (Phase 48 recovered the exact 31-position mask; Phase 49 read its
selected string, complement, rails and 7x13 / 13x7 sums; Phase 474 audited the
selected letters). Nothing has read FAED's six 91-symbol lanes through the
same mask. Related but different work, for the record:

| Prior work | What it did | Why it is not this |
|---|---|---|
| `matrixsum_dbbi_faed_position_audit` (Phase 33 family) | `[23,16,7]` as three indices into DBBI/FAED | uses three numbers, not the 91-position mask |
| `dbbi_faed_authenticated_selector_audit` | DBBI/FAED symbols as indices into five other strings | opposite direction |
| `dbbi_faed_six_lane_audit` | eight lane-vs-DBBI equality/residual measures; 24-symbol tail vs the colour mask | never selects lane positions with the host mask |
| Phase 518 | mutual information between DBBI and FAED proportional block modes | block modes, not host positions |
| Phase 45 | prime-position retention/masking of FAED under checkerboard decode | prime positions of the raw stream, not the DBBI host mask on lanes |
| Phase 534-537 | DBBI scaffold, matrix, numeric text, position function | none reads FAED |
| Phase 13 / 520 / 521 | cross-phase linkage, joint splice, shared board | different constructions |

This is an exploratory hypothesis, motivated by an unverified community remark
(chat message 71986: the DBBI selector overlaid on FAED's rows gives
coordinates that "don't really point at anything"). It is not a creator-selected
recipe, and FAED is undecoded ciphertext, so an extracted string is a string
over `a..i`, not text.

## Objects

- FAED: the exact 570-symbol repository stream; DBBI: the exact 91-symbol stream.
- Lanes `L1..L6`: `FAED[91*(j-1) : 91*j]`. The 24-symbol tail is excluded
  (its length cannot carry a 91-position mask; its colour-mask test is Phase 274's).
- Two masks over raw 1-based DBBI positions, derived by the independent
  prime-host parser of Phase 537 (logical prime positions carry `b` or `be`):
  - `M31` (83-token parse), 15 single-`b` hosts and 8 `be` hosts, 31 positions,
    identical to the Phase 48 recorded mask:
    `2 3 5 7 11 12 14 18 20 24 25 31 32 34 40 44 46 50 51 57 63 65 66 72 73 77 79 85 86 90 91`
  - `M30` (84-token parse, Selection A's parse), 16 `b` hosts and 7 `be` hosts,
    30 positions, `M31` without position 91 (the unhosted terminal `e`).
- For a mask: `H` = selected positions ascending; `C` = the complement
  ascending (60 or 61 positions); `Hb` = positions of one-character hosts;
  `Hy` = positions of two-character hosts.

## Candidate strings (closed, 64 before deduplication)

Per mask, per lane: `H`, `C`, `Hb`, `Hy` read from that lane in ascending
position order: 24 strings. Pooled across the six lanes, in two orders:
lane-major (`L1`'s selection, then `L2`'s ...) and position-major (for each
selected position ascending, lanes 1..6): 4 sets x 2 orders = 8 strings. That
is 32 per mask, 64 in total, deduplicated by exact string. Raw `a..i` symbols
only: no A1Z26 mapping, case variant, reversal, or other transform is added by
this phase (the GPU tool's standard password-form expansion applies, exactly as
in Phase 524).

## Arm 1 — oracle (exact bar)

The 64 strings (deduplicated) are the entire base list. They are run through
the existing GPU oracle (Docker image `gsmg-gpu-oracle:phase524-kt`, 60-variant
table, all authenticated blobs, `--newline-variants`, Bloom raw-key arm and the
Phase 331 known-target detector). Required run hygiene, as in Phase 524 run 3:
Bloom cache loaded from `db/addresses.hash160.bloom`; the eight known targets
folded in; fingerprint-bound checkpoint; user-owned output directory.

**Exact hit:** any strong or structural record, or any known-target /
confirmed-address record. A hit is a candidate, not a solution, and is frozen
for a separate validation. Weak-tier rows are reported and classified by the
Phase 524 `--classify-weak` method; they do not count.

## Arm 2 — structural gate (calibrated lead, weaker)

Two symbol-agnostic statistics, each with its own family and null. Symbols are
the raw `a..i` FAED symbols.

**S1, top-2 concentration.** For a selection string, the share of its two most
frequent symbols. Cells: 2 masks x {`H`,`C`} x (6 lanes + the six-lane pool) = 28.
Null: for each mask size (31, 30) and each lane, a uniformly random subset of
that size of the lane's 91 positions replaces the mask; `H` is the subset and
`C` its complement; pooled cells use the six lane draws.

**S2, cross-lane column agreement.** For a position set `Q`, the number of
equal lane pairs (of the 15 pairs among six lanes) summed over `q` in `Q`.
Cells: 2 masks x {`H`,`C`} = 4. Null: uniformly random position subsets of the
same size.

Both nulls use 20,000 replicates with fixed seed 538, standardize each cell
against its own null mean and standard deviation, take the family maximum, and
compare it with the same statistic recomputed on each replicate (add-one tail).
This is slightly generous to the null because the same replicates standardize
and score, as in Phase 537, and is disclosed rather than corrected.

**Calibrated lead:** an add-one tail at most `0.0005` (the 0.001 of Phase 537,
halved for two statistics) in S1 or in S2. A lead is not a promotion and
selects no operator, password, or key.

## Controls (run before any real FAED lane is read)

1. **Precedent reproduction.** `M31` applied to the exact 91-character
   Phase 3.2.2 answer must give `ncsyangcahiriasogaleafayanestve` (the
   Phase 48 / 474 selection; the Phase 13 note's `...irivasoalbefay...` is a
   misprint that this repository's own Phase 48 disproved), the Phase 49
   complement, `Hy = anhirialfayastve`, and `Hb` equal, as a multiset, to
   Phase 49's blue plus FEFE rails. Failure stops the phase.
2. **Extraction exactness.** On a synthetic 570-element stream of distinct
   values, every candidate reader (lane, `H/C/Hb/Hy`, lane-major and
   position-major pooling) must return exactly the expected elements in the
   expected order.
3. **Gate recovery.** Plant, on lane-sized synthetic streams drawn from FAED's
   symbol histogram, (a) a mask whose host positions carry a concentrated pair
   of symbols and (b) a mask whose host columns are identical across lanes.
   Noise levels 0%, 25%, 50% of planted positions replaced by uniform symbols,
   20 fixed-seed trials each, 2,000 replicates per scoring (the smallest add-one tail is then 1/2001, below the 0.0005 threshold; 1,000 could never reach it). **Requirement:**
   every 0%-noise plant is a calibrated lead for its statistic. Power at 25%
   and 50% is reported, not required.
4. **False-positive check.** 100 histogram-preserving shuffles of the whole
   real FAED stream, scored with the identical pipeline (2,000 replicates), are
   reported: how many reach the lead threshold. Expected about zero; reported
   context, not a gate.

If control 1, 2 or 3 fails, stop without reading any real lane.

## Stop rule

Zero exact hits in Arm 1 and no calibrated lead in Arm 2 closes only this
family: two masks, six 91-symbol lanes, forward reading, the four selection
kinds and two pooling orders above. Do not add masks (including the historical
event-start selection), other lane partitions such as 2 x 285, the tail,
reversal, offsets, symbol mappings, other pooling orders, or a different
statistic after seeing results. A positive arm is a candidate for a separately
locked follow-up, not a result.

## Non-claims

FAED remains undecoded. Neither arm tests that FAED is intended to be read
through DBBI's mask. The Doober remark that motivated this is unverified
community text. No fact about any blob, password, key, or address changes on a
negative.

## Execution lock

`--prepare` writes `tools/gsmg/phase538_faed_lane_lock.json` pinning: this
protocol's SHA-256, the script and its test file, `data.py`, the SHA-256 of
FAED and DBBI, both masks, the candidate list digest and count, the gate
parameters, and the results of controls 1-3. `--run-gate` recomputes and
compares the whole lock before reading any real lane. The GPU base list is
`_work/phase538/bases.txt`, pinned by digest in the lock.

## Reproduction

```bash
python3 tools/gsmg/phase538_faed_lane_extraction.py --self-test
python3 tools/gsmg/phase538_faed_lane_extraction.py --prepare
python3 tools/gsmg/phase538_faed_lane_extraction.py --run-gate
```
