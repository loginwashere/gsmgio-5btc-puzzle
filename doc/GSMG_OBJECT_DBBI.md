---
type: object
object_id: OBJ-DBBI
status: stable
canonical_source: tools/gsmg/data.py
length: 91
alphabet: a-i
encoding: ascii
topics:
  - object
  - dbbi
  - macro-chain
aliases:
  - DBBI
---

# Object: DBBI

## What exact bytes this name means

The 91-symbol raw string labeled `DBBI` on the authenticated SalPhaseIon
page, frozen verbatim in `tools/gsmg/data.py`:

```text
length:  91
alphabet: a-i (9 symbols)
SHA-256: 71fe46259e270c113529dfaded4b59c59a9dffd826a7202ab07fc498b6a2c5ca
IoC:     0.151 (structured / key-like, per data.py's own annotation)
```

Re-extracted programmatically from the community fork's code, not retyped,
specifically to avoid transcription error in a security-sensitive fixed
string (see `tools/gsmg/data.py`'s header comment).

## Established properties

- 91 = 7 × 13, a semiprime — its **only** nontrivial factor pair, per the
  divisor-legs comparison in Phase 240's
  [GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT](GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT.md)
  (this factorization claim is not itself in the Fact Ledger — see fact
  `F-OBJ-001` in the [Fact Ledger](GSMG_FACT_LEDGER.md) for what is).
- Best-fit checkerboard escape pair by code-level Index of Coincidence:
  `{b,e}`, rank 1 of 36 — an admissibility signature unique among all 36
  pairs (`tools/gsmg/checkerboard_code_ic_oracle.py`).
- Independent confirmation from raw letter frequency alone: DBBI's a-i
  counts (`a:3, b:25, c:8, d:4, e:18, f:10, g:10, h:8, i:5`) reject
  uniformity by chi-square (df=8) at p ≈ 2.89×10⁻⁶ (~1 in 346,000), and `b`
  and `e` together account for ~70% of that deviation
  (`tools/gsmg/dbbi_letter_frequency_chi_square.py`). This is not a new
  signal — it's the same `{b,e}` escape-pair structure above, recovered
  from a simpler statistic, and does not by itself imply anything about
  grid/reshape-dependent patterns (e.g. prime-numbered row/column sums),
  which remain unestablished (Phase 319, negative).
- Direct base-9 capacity is `91 log2(9) = 288.463...` bits. A raw 256-bit
  scalar can fit, but the fixed leading version byte makes a conventional
  uncompressed WIF binary payload 296 bits and a compressed payload 304 bits,
  so neither can be represented directly by the whole 91-symbol stream. This
  says nothing against a raw key or a prior transform (Phase 330; fact
  `F-OBJ-004`).
- Sits immediately before binary ASCII `matrixsumlist` on the page, itself
  immediately before `FAED` — `DBBI [matrixsumlist] FAED`
  (`tools/gsmg/salphaseion_operand_binding_audit.py`, Phase 101).
- Not consumed by any authenticated operation yet — the 31-character
  selection `ncsyangcahiriasogaleafayanestve` (a first-piece-derived
  substring of DBBI) is a real structural checkpoint but has no sourced
  consumer. See fact `F-CHAIN-011` in the [Fact Ledger](GSMG_FACT_LEDGER.md).

## Open gaps referencing this object

- Gap `G-MSL-001` in the [Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md) — no
  source binds the 31-char selection to matrix dimensions/traversal/aggregation.
- Gap `G-YIN-001` in the [Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md) — no
  operator selected between DBBI and FAED at all.

## Phases that examined this object (representative, not exhaustive)

Re-derive with:

```bash
rg -il '\bDBBI\b' doc tools/gsmg/FINDINGS.md
```

- Phase 101 — page structure / operand binding, fixes `DBBI [matrixsumlist] FAED` placement.
- Phase 106, 113 — escape-pair oracle calibration.
- Phase 132 — 31-character selection's broad-word statistical control.
- Phase 236 — [GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md), reclassifies the 31-char selection to structural-only.
- Phase 240 — [GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT](GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT.md), notes `91 = 7×13` in the divisor-legs comparison against FAED.
- Phase 243/244 — [GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md), confirms DBBI and FAED share one text node with no markup boundary between them, byte-identical across all 5 known Wayback captures.
- Phase 330 — [GSMG_EXTERNAL_ARCHIVE_AUDIT](GSMG_EXTERNAL_ARCHIVE_AUDIT.md),
  independently verifies the direct-capacity/WIF bound and rejects broader
  list/zero/private-data inferences from the external compendium.

## Related objects

- [FAED](GSMG_OBJECT_FAED.md) — the paired raw stream on the same page.
- `matrixsumlist` (macro token) — see [MOC - Architect and Macro](MOC%20-%20Architect%20and%20Macro.md).
