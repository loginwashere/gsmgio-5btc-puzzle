---
type: preregistration
status: frozen
date: 2026-09-01
phase: 468
topics:
  - known-parts-cross-reference
  - G-MSL-001
  - G-GGN-001
  - G-ESC-001
---

# Phase 468 — Known-Parts Cross-Reference Protocol

Frozen before any scoring runs. The creator has stated no further hints
are coming, so any missing G1 evidence for an open gate has to already be
inside the closed system. This phase checks, mechanically only (no
thematic reasoning), whether any already-established output structurally
fits an open gate's unbound slot, and calibrates two specific numeric
observations that turned up during that inventory.

## Question

1. Does any established puzzle output structurally fill an open gate's
   `parameter_value` slot (the only slot kind a raw value can occupy)?
2. Is `31` (the DBBI selection's length) arithmetically related to this
   project's own established `7`/`13`/`91` dimension facts?
3. Is the `FF67`/`(255,103)` matrix-product endpoint's ASCII-escape
   coincidence with `G-ESC-001`'s candidate pairs unusual under a matched
   null?
4. Do any of today's newly-established checkpoint values work as
   secp256k1 key material against the frozen known-target address set,
   under interpretations not already closed by a prior phase?

## Frozen inputs

- List 1 (established outputs) and List 2 (open-gate slots), frozen in
  `tools/gsmg/phase468_known_parts_catalog.py` — `ESTABLISHED_OUTPUTS` and
  `OPEN_GATE_SLOTS`. Evidence-class tags: `authenticated_output`,
  `authenticated_derived`, `reproduced_conditional`, `recognition_only`,
  `candidate_parameter`, `analyst_generated_metadata`, `rule_template`.
  Only the first three are eligible for Output-3 value matching. Slot-kind
  tags: `operator`, `parameter_value`, `representation_or_serialization`,
  `consumer_interface`, `selector`. Only `parameter_value` is value-
  fillable. Applying this taxonomy, the only genuine `parameter_value`
  slots in the whole registry are `G-MSL-001`'s matrix dimensions and
  `G-GGN-001`'s scalar `k`. All other gates resolve `not_applicable` for
  value-filling and are recorded as such, not skipped.
- `31` (the DBBI selection length) and `{7, 13, 91}` (this project's own
  established DBBI-wide dimension facts, cited read-only from
  `tools/gsmg/small_number_coincidence_calibration.py`'s frozen pool —
  that module's pairwise-sum statistic is not reused, only its cited
  facts).
- The observed (non-null) `FF67` source digit tuple: `(5, 7, 4, 0, 6, 1)`.
- Lane-B candidate byte records, frozen in
  `tools/gsmg/phase468_known_parts_catalog.py` — `LANE_B_CANDIDATES` and
  `EXCLUDED_LANE_B_CANDIDATES`. Provenance audit (grep across
  `tools/gsmg/*.py`, `tools/gsmg/*.json`, `tools/gsmg/findings/*.md`,
  `doc/GSMG_*.md`) found: `574061` appears extensively as BIP32 *path-
  index* material (`bip32_authenticated_number_paths_audit.py`'s
  `PATH_REGISTRY`) and, per `phase375_reopenability_ledger.json`, was
  earlier "tested only as a raw/derived passphrase" (an AES-KDF
  passphrase family, distinct from this phase's three interpretations);
  neither overlaps direct-bytes-as-scalar, SHA-256-as-scalar, or the
  existing BIP32 seed-form/path enumeration applied to the literal text
  `"574061"` as a *seed*. `311027`/`33414671`/`THEFLOWER` returned no
  scalar/seed/BIP32 hits in the audited sources. `P90`/`P91`/`Q472`/full
  BTCSEED decode were already tested as SHA-256-as-scalar and HMAC-SHA512-
  BIP32-seed by Phase 400 (`tools/gsmg/findings/P00400.md`, 96,032 checks,
  0 hits) — cited, not re-run; their direct-bytes-as-scalar interpretation
  is `not_applicable_too_long` (90/91/472/570 bytes each, exceeds the
  frozen 32-byte cap). The bounded label this audit is allowed to record
  is exactly: *"No prior exact candidate × encoding × derivation test
  identified in the audited sources"* — never proof of global absence.

## Method

### Output 1 — typed inventory (descriptive, not a search)

Cross `ESTABLISHED_OUTPUTS` (eligible classes only) against
`OPEN_GATE_SLOTS`. Every slot not tagged `parameter_value` resolves
`not_applicable: <slot_kind>`. This is an inventory, not a claim of
exhaustive search — only Output 3's specific lanes below execute anything.

### Output 2 — bounded `31` arithmetic (G-MSL-001 only)

1. Trial-division primality check on `31`.
2. Enumerate nondegenerate rectangular factorizations `rows × cols = 31`
   with both sides `> 1` — expected: none.
3. Complete operation table over unordered pairs from `{7, 13, 31, 91}`:
   for each pair `(a, b)` with `a < b`, report `a+b`; the signed-difference
   pair `(a−b, b−a)` together as one row; `a×b`; the ratio pair
   (`a÷b`, `b÷a`) together as one row, only where either is an exact
   integer; the modulus pair (`a mod b`, `b mod a`) together as one row.
   Flag mechanically any result landing exactly on another member of
   `{7, 13, 31, 91}`.
4. States explicitly what a factorization-impossibility result does *not*
   rule out: padding, a `1×31`/`31×1` rail, ragged rows, sub-selection of
   31 cells from a larger matrix, or dimensions supplied independently of
   the stream's own length.

No p-value attaches to Output 2 — it is arithmetic fact-checking.

### Output 3, Lane A — FF67 / ASCII / escape-pair conjunction

**Event, frozen in code-equivalent form:** for a digit-tuple, build all 24
`(orientation, permutation)` rows exactly as
`phase453_false_discovery_calibration.py`'s `score_ff67` does internally
(`multiply`/`orientations`, `matrix = (digits[:3], digits[3:])`,
`vector = (sum(digits), sum(digits[:3]), sum(digits[3:]))`,
`itertools.permutations(vector)`) — these two pure functions are imported
unchanged from that module (`tools/gsmg/phase453_false_discovery_calibration.py:101-114`).
The tuple hits hypothesis `S` if any row `(x, y)` satisfies
`(x == 255 and y in S) or (y == 255 and x in S)`. `(255, 255)` gets no
special case — it simply fails since `255 ∉ S` under either hypothesis.

**Exactly two hypotheses**, held fixed for the whole phase — no `{h,e}`-
only third hypothesis, and no comparison/selection claim between them:
- `g_i_primary`: `S = {103, 105}` (ASCII `g`, `i`).
- `union_e_g_h_i`: `S = {101, 103, 104, 105}` (ASCII `e`, `g`, `h`, `i`).

**Two null populations**, both reported, not combined:
- `sampled_100000`: `rng.sample(range(10), 6)` for `100000` draws, using
  Phase 468's own frozen master seed (not Phase 453's — that seed belongs
  to an already-closed phase). Generator/seed choice matches Phase 453's
  own call shape (`phase453_false_discovery_calibration.py:220`) for
  consistency, applied to a new seed value.
- `exhaustive_151200`: `itertools.permutations(range(10), 6)`, unmodified
  — all `151200` 6-permutations of 10 digits.

Both populations are generated and their sizes/shape verified as
*structural* self-tests before any scoring runs — population generation
is deterministic given the seed and is treated as a frozen input, not part
of the outcome.

**p-value convention**, matched exactly to
`phase453_false_discovery_calibration.py`'s `empirical_tail` (line ~346):
`p_plus_one = (extreme_count + 1) / (trials + 1)` (Laplace/plus-one
estimator). **Holm correction**: `phase453_false_discovery_calibration.py`'s
`holm_adjust` (line ~364), applied **only across the 2-hypothesis axis,
separately within each population** — 2 Holm-corrected values from the
sampled population, 2 from the exhaustive population; the two populations
are a robustness pair (matching how Phase 453 itself treats primary/
sensitivity), not an extra multiple-comparison axis.

**Decision rule, frozen explicitly:** reject (label `unusual`) iff
`Holm-adjusted p < 0.005` (**strict** less-than; a value exactly at 0.005
does not reject). This alpha is **Phase 468's own new decision threshold**,
distinct from and not comparable to Phase 453's own alpha=0.05 Holm family
(whose `S-FF67` case is cited for its raw/Holm numbers, not reused as this
phase's threshold).

**Serialization convention** for any population/result digest:
`json.dumps(obj, sort_keys=True, separators=(",", ":"))`, UTF-8 encoded,
SHA-256 over the resulting bytes.

**What this Lane can and cannot conclude:** even a rejection under either
hypothesis would only mean the `FF67` endpoint's ASCII-escape coincidence
is statistically unusual — like Phase 453's own `S-FF67` finding — not
that it supplies `G-MSL-001`'s missing operation or `G-ESC-001`'s missing
selector. `G-ESC-001`'s Phase-468 citation is frozen verbatim: *"Records
the observed calibration result; absent a preregistered surviving
selection criterion, it does not select an escape pair or operator."*

The SALPH-103 chain's `103`-digit length is **not** folded into Lane A's
random-null calibration: it is a separate, non-random, enumerated fact —
among the four already-tested serialization conventions in
`GSMG_YOUWON_SALPH_103_ALIGNMENT_AUDIT.md`'s own sensitivity table (`100`,
`128`, `103`, `128`), exactly 1 of 4 gives `103`. This is reported
side-by-side with Lane A's calibrated result, never combined into one
p-value.

### Output 3, Lane B — G-GGN-001 scalar delta

**Candidates:** `LANE_B_CANDIDATES` from the catalog module —
`prime_574061`, `prime_311027`, `prime_33414671`, `theflower`,
`salph_103_digit_stream` (text-only, `direct_scalar_status:
not_applicable_too_long`). `youwon`/`exec_order_13224` excluded
(`recognition_only`). `btcseed_p90_p91_q472` excluded (cited, not
re-run — see Frozen inputs).

**Per-type direct-scalar encoding**, no inference, no truncation ever
(reject oversized inputs instead):
- `integer` → minimal unsigned big-endian of the value, reject if `> 32`
  bytes, else left-pad to 32 with zero bytes.
- `text` → exact UTF-8 bytes of `canonical_text`, same reject/left-pad
  rule.
- `matrices`/sequences → excluded entirely (no authenticated
  serialization exists); none of the finalized candidates are this type.

**Target set, pinned:** `raw_key_chunk_audit.known_targets()`'s 10-address
map (`EC_NEIGHBOR_HASH160S` + `PRIZE_ADDRESS` + `HALVING_ADDRESS`,
`EXPECTED_TARGET_COUNT = 10` at `raw_key_chunk_audit.py:118`), passed
explicitly to all three interpretations. The BIP32 script's own 9-target
default (`half_better_half_algebra_audit.KNOWN_TARGET_HASH160S`) is never
used as a fallback.

**Three interpretations, reported separately per candidate:**
1. **direct-bytes-as-scalar** — the candidate's own 32-byte-normalized
   bytes fed into `private_key_details()`
   (`tools/gsmg/binary_key_material_backfill.py:169`). If the resulting
   integer falls outside `[1, SECP256K1_ORDER)`, the function itself
   returns `None` (reject, no modular reduction) — this behavior is used
   as-is, not modified.
2. **SHA-256-as-scalar** — `SHA-256(canonical_text)` fed into the same
   `private_key_details()`, same reject-outside-range behavior.
3. **existing SHA-derived BIP32 seed-form/path enumeration** —
   `bip32_authenticated_number_paths_audit.run(candidates=[canonical_text],
   known_targets=<pinned 10-map>)` (`bip32_authenticated_number_paths_audit.py:144`),
   used unmodified. This applies that module's own existing 2 seed forms
   (`sha256`, `sha512`) × 8 paths × 2 hardening modes to the literal
   candidate text — not a new "text-as-one-seed" construction. Results are
   reported broken out by seed form, hardening mode, and path exactly as
   that function's own return value already does (per-hit records carry
   `seed_form`/`path_name`/`hardening`).

Expected outcome, per this project's own history: 0 hits across all three
interpretations for all candidates. A negative result here closes only
this specific, narrow delta — it does not weaken the structural
observations (`574061`, `311027`, `33414671`, `THEFLOWER`) themselves.

## Promotion gate and stop rule

- Output 2: no p-value; a factorization-impossibility fact either holds or
  doesn't, checked once.
- Lane A: `Holm-adjusted p < 0.005` (strict) rejects the null for that
  hypothesis/population cell; anything else is `common_under_matched_null`.
- Lane B: only an exact hit against the pinned 10-target set promotes
  anything; a negative closes the delta, not the candidates' broader
  significance.
- **One pass.** No threshold shopping, no post-hoc hypothesis addition, no
  re-running with a different seed if the first result is unwelcome.
- **Reopen condition (required regardless of outcome):** a new
  authenticated primary source names an operation/consumer for
  `G-MSL-001`/`G-GGN-001`/`G-ESC-001`; or a new established output enters
  `ESTABLISHED_OUTPUTS` that wasn't in this frozen catalog; or a
  genuinely new Lane-B interpretation is proposed and separately
  preregistered.
