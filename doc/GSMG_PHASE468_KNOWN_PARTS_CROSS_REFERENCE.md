---
type: audit
phase: 468
date: 2026-09-01
status: closed
result: structural_and_calibrated_negative
---

# Phase 468 — Known-Parts Structural Cross-Reference

## Result

No further hints are coming, so any missing G1 evidence for an open gate
has to already be inside the closed system. This phase cross-referenced
the finite set of already-established puzzle outputs against the finite
set of open-gate unbound slots, mechanically only.

**Output 1 (typed inventory):** applying the slot taxonomy (`operator` /
`parameter_value` / `representation_or_serialization` /
`consumer_interface` / `selector`) to all 9 in-scope registry rows (10
rows minus `G-X2SH-001`, excluded as a closed secondary reading), exactly
**2** slots in the entire registry are genuinely `parameter_value`
(value-fillable): `G-MSL-001`'s matrix dimensions and `G-GGN-001`'s scalar
`k`. Every other gate's slots resolve `not_applicable` for value-filling —
recorded explicitly, not skipped.

**Output 2 (bounded `31` arithmetic, G-MSL-001):** `31` is prime; trial
division confirms **zero** nondegenerate rectangular factorizations
`rows × cols = 31` with both sides `> 1`. The complete operation table over
`{7, 13, 31, 91}` (this project's own established DBBI-wide dimension
facts) produces **nine** flagged equalities against the set, listed in
full in `output_2_arithmetic_31.flagged_equalities_against_established_set`
— none is nontrivial beyond the known `7 × 13 = 91` construction: six are
the trivially-guaranteed `a mod b = a` identity that fires whenever `a <
b` (`7 mod 13/31/91`, `13 mod 31/91`, `31 mod 91`), and two more
(`91 ÷ 7 = 13`, `91 ÷ 13 = 7`) are the same construction restated as
division rather than multiplication. This proves only that an exact,
nondegenerate rectangular layout is impossible for the 31-character
selection — it does **not** rule out padding, a `1×31`/`31×1` rail, ragged
rows, sub-selection of 31 cells from a larger matrix, or dimensions
supplied independently of the stream's own length.

Note: `31` itself (the DBBI selection's own length) is not a catalog entry
in `ESTABLISHED_OUTPUTS` — Output 2 treats it as the arithmetic subject,
not as a candidate value in Output 1's inventory. This is a frozen-catalog
omission, recorded here rather than silently patched into the locked
catalog; a future phase adding it would need its own provenance check and
would not retroactively change this phase's pinned result.

**Output 3, Lane A (FF67 / ASCII / escape-pair conjunction):** two
hypotheses only (`g_i_primary = {103, 105}`; `union_e_g_h_i = {101, 103,
104, 105}`), no third `{h,e}`-only hypothesis, no comparison/selection
claim between them. Replaying `phase453_false_discovery_calibration.py`'s
`multiply`/`orientations` over both a 100,000-sample and the full
151,200-permutation null population:

| Population | Hypothesis | Extreme / trials | Raw p (+1) | Holm p | Rejects (`p < 0.005`) |
|---|---|---:|---:|---:|:---:|
| sampled_100000 | `g_i_primary` | 27 / 100,000 | 0.000280 | 0.000560 | yes |
| sampled_100000 | `union_e_g_h_i` | 38 / 100,000 | 0.000390 | 0.000560 | yes |
| exhaustive_151200 | `g_i_primary` | 48 / 151,200 | 0.000324 | 0.000648 | yes |
| exhaustive_151200 | `union_e_g_h_i` | 60 / 151,200 | 0.000403 | 0.000648 | yes |

Both hypotheses cross `Holm p < 0.005` under both populations at this
phase's own alpha. This is a **post-observation conditional rarity
calibration, not a confirmatory discovery result**: the protocol itself
records that this numeric conjunction (`FF67`'s low byte as ASCII `'g'`
falling in the FAED escape-pair candidates) "turned up during that
inventory" — i.e. it was noticed before the two hypotheses were frozen.
Holm correction covers the 2-hypothesis × 2-population family that was
frozen *after* noticing it; it does not, and cannot, correct for having
selected this particular conjunction out of the much larger space of
numeric relationships visible across the full known-parts inventory. The
reported frequencies (extreme counts, raw/Holm p) are exact and
reproducible; "rejects the null" language overstates what a
post-observation calibration licenses. It is **not** a selection: per the
frozen protocol, this Lane cannot and does not conclude that it "favors
`{g,i}` over `{h,e}`" or "selects an escape pair" — `{h,e}` was never one
of the two tested hypotheses. The observed real digit-tuple
`(5,7,4,0,6,1)` trivially hits both hypotheses (it *is* the source of the
established `(255,103)` endpoint) — that observation is a construction
fact, not part of the null comparison; the calibration measures how rarely
a *different* 6-digit assignment would have produced the same kind of
companion, conditional on this conjunction having been the one flagged for
testing.

Separately, the SALPH-103 chain's `103`-digit length is a **non-random,
enumerated** fact, not folded into the calibration above: among the four
already-tested serialization conventions in
`GSMG_YOUWON_SALPH_103_ALIGNMENT_AUDIT.md`'s own sensitivity table, exactly
**1 of 4** gives `103`. Reported side-by-side, not combined into a joint
p-value.

**Output 3, Lane B (G-GGN-001 scalar delta):** 5 candidates
(`prime_574061`, `prime_311027`, `prime_33414671`, `theflower`,
`salph_103_digit_stream`), 3 interpretations each (direct-bytes-as-scalar,
SHA-256-as-scalar, existing BIP32 seed-form/path enumeration — 2 seed
forms × 8 paths × 2 hardening modes + master-key control = 34 address
checks per candidate for the BIP32 lane), against the pinned 10-address
target set (`raw_key_chunk_audit.known_targets()`). `salph_103_digit_stream`
is `not_applicable_too_long` for direct-scalar (103 bytes > 32-byte cap).
**Zero hits** across all candidates and interpretations. `youwon`/
`exec_order_13224` were excluded (`recognition_only`, ineligible);
`P90`/`P91`/`Q472`/full BTCSEED decode were excluded and cited only — Phase
400 already closed their SHA-256-as-scalar and BIP32-seed interpretations
negative (96,032 checks, 0 hits), and their direct-bytes-as-scalar reading
is `not_applicable_too_long` for all four.

## Typed inventory

Full detail in `tools/gsmg/phase468_result.json`'s
`output_1_typed_inventory`. Eligible established outputs (evidence class
`authenticated_output`/`authenticated_derived`/`reproduced_conditional`):
**18 of the catalog's 26 rows**; the remaining 8 (`recognition_only`,
`candidate_parameter`, `analyst_generated_metadata`, `rule_template`) are
catalogued but excluded from value matching by construction.

This is a **slot-kind inventory, not a typed compatibility match**. For
each of the two `parameter_value` slots (`G-MSL-001` matrix dimensions,
`G-GGN-001` scalar `k`), `output_1_typed_inventory`'s
`candidate_established_outputs` field lists the identical full 18-item
eligible-outputs list for both slots — the implementation does not consult
an output's own type (integer vs. matrix vs. raw text vs. pair) against
either slot's actual shape requirement. It establishes only *which* slots
are `parameter_value`-kind (2 of the registry's many), not whether any
specific established output — a raw DBBI/FAED string, a `2×3` matrix, a
6-digit prime, a 3-integer sum — structurally fits either slot's real
domain. A genuine type-compatibility pass (e.g. only small integers are
candidates for `matrix_dimensions`; only ≤32-byte-representable values for
`scalar_k`) would need explicit domain rules per slot and is not what this
phase computed.

## Controls and limits

- No thematic/narrative reasoning anywhere — only mechanical type/
  arithmetic facts and calibrated statistics.
- No re-derivation of anything Phase 448/450/453/456/464/465/466/467
  already closed.
- `small_number_coincidence_calibration.py`'s frozen pool was cited
  read-only for the `7/13/91` facts; its own pairwise-sum statistic was
  never reused or repurposed.
- No password material, decryptions beyond the existing exact-target
  address check, or oracle calls: `password_materials_generated = 0`,
  `oracle_calls = 0`, `decryptions_attempted = 0`.
- Lane A's calibrated rejection does not supply `G-MSL-001`'s missing
  operation, `G-ESC-001`'s missing selector, or any consumer — it is
  recorded as a structural/statistical observation only.
- Lane B's negative closes only this specific three-interpretation delta
  for these five candidates; it does not weaken the structural
  observations (`574061`, `311027`, `33414671`, `THEFLOWER`) themselves.
- Post-execution review found and corrected four documentation-accuracy
  defects in an earlier draft of this doc/the findings entry: a wrong
  eligible/ineligible row count (was reported 19+8=27, actually 18+8=26);
  Output 1 described as though it type-matched candidates to slots, when
  it only labels slot kinds (corrected above); Lane A's calibration
  described with unqualified "rejects the null"/"sharper than Phase 453"
  language rather than as a post-observation conditional rarity
  calibration; and Output 2's arithmetic table described as having zero
  flagged equalities when it has nine, all trivial. The locked
  script/catalog/manifest/execution-lock/result files were not changed —
  only this prose was — and all digests still match; see the frozen
  artifacts themselves for the authoritative numbers.

## Reproduction

```bash
cd tools/gsmg
python3 phase468_known_parts_cross_reference.py --self-test
python3 -m unittest test_phase468_known_parts_cross_reference
```

Artifacts: the preregistered protocol
(`doc/Brainstorms/2026-09-01 - Phase 468 Known-Parts Cross-Reference Protocol.md`);
`tools/gsmg/phase468_known_parts_catalog.py`;
`tools/gsmg/phase468_manifest.json`;
`tools/gsmg/phase468_execution_lock.json`;
`tools/gsmg/phase468_known_parts_cross_reference.py`;
`tools/gsmg/phase468_result.json`;
`tools/gsmg/phase468_result_record.json`;
`tools/gsmg/test_phase468_known_parts_cross_reference.py`.
