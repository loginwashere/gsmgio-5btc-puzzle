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

## Related objects

- [FAED](GSMG_OBJECT_FAED.md) — the paired raw stream on the same page.
- `matrixsumlist` (macro token) — see [MOC - Architect and Macro](MOC%20-%20Architect%20and%20Macro.md).
