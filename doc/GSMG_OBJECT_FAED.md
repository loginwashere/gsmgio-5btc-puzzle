---
type: object
object_id: OBJ-FAED
status: stable
canonical_source: tools/gsmg/data.py
length: 570
alphabet: a-i
encoding: ascii
topics:
  - object
  - faed
  - macro-chain
aliases:
  - FAED
---

# Object: FAED

## What exact bytes this name means

The 570-symbol raw string labeled `FAED` on the authenticated SalPhaseIon
page, frozen verbatim in `tools/gsmg/data.py`:

```text
length:  570
alphabet: a-i (9 symbols)
SHA-256: 066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2
IoC:     0.118 (~uniform / high-entropy payload, per data.py's own annotation)
```

Re-extracted programmatically from the community fork's code, not retyped,
specifically to avoid transcription error in a security-sensitive fixed
string (see `tools/gsmg/data.py`'s header comment).

## Established properties

- 570 = 2×3×5×19 — 8 distinct factor pairs, so no single dimension is
  singled out by factorization alone. See fact `F-OBJ-002` in the
  [Fact Ledger](GSMG_FACT_LEDGER.md).
- Best-fit checkerboard escape pair by code-level Index of Coincidence:
  `{g,i}`, rank 1 of 36 — but this admissibility signature is shared by 5 of
  36 pairs (less distinctive than DBBI's).
- The Architect-boundary mirror (via `BUT/HYE` → mirror9) predicts `{h,e}`
  instead, and this remains unreconciled with `{g,i}`. Neither pair's
  mirror9 image (`{a,c}` / `{c,g}`) validly segments its own origin stream
  — `{c,g}` cannot even segment FAED at all (dangling final escape). Page
  markup supplies no third selector either — DBBI and FAED share one
  `<textarea>` text node with no DOM boundary, identical attributes, no
  distinguishing CSS/JS/comments/whitespace at the join, and this holds
  byte-for-byte across all 5 known Wayback captures spanning 2023-06-01 to
  2026-04-05
  ([GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md),
  Phase 243/244). See fact `F-OBJ-003` in the [Fact Ledger](GSMG_FACT_LEDGER.md).
- Width 38 (from the `#383838`/macro-token-length nesting coincidence) is
  **not** a geometrically exceptional dimension for FAED under any of 3
  null models after correction across all 16 divisor widths — checked
  directly, not merely unconfirmed. See
  [GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT](GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT.md).
- Under any direct bijection of `a`--`i` to base-9 digits 0--8, the smallest
  possible whole-stream integer has bit length 1,801 in either forward or
  reverse order. It therefore cannot be exactly seven concatenated 32-byte
  keys (1,792 bits). This constraint applies only to FAED-as-one-integer, not
  to segmented streams, records, or prior transforms (Phase 330; fact
  `F-OBJ-005`).
- Sits immediately after binary ASCII `matrixsumlist` on the page:
  `DBBI [matrixsumlist] FAED [lastwordsbeforearchichoice] [thispassword]`
  (Phase 101).

## Open gaps referencing this object

- Gap `G-ESC-001` in the [Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md) —
  `{g,i}` vs. `{h,e}` escape-pair reconciliation, the sharpest unresolved
  joint in the whole macro chain.
- Gap `G-YIN-001` in the [Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md) — no
  operator selected between DBBI and FAED at all.

## Phases that examined this object (representative, not exhaustive)

Re-derive with:

```bash
rg -il '\bFAED\b' doc tools/gsmg/FINDINGS.md
```

- Phase 43, 113 — FAED-specific monoalphabetic recovery attempts under
  `{h,e}` and `{g,i}` respectively, both closed negative as full decoders
  (the `{g,i}` *escape-pair* preference itself survives; the decode does not).
- Phase 101 — page structure / operand binding.
- Phase 225 — creator `YING/YANG` typo gives `IG`/`AG`, exact but
  authorship-rejected explanation for the `{g,i}` preference.
- Phase 236 — [GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md), formalizes the complete mirror-orbit table.
- Phase 240 — [GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT](GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT.md), full-divisor geometric calibration, width 38 rejected.
- Phase 243/244 — [GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md), page-markup escape-pair selector branch closed negative, confirmed byte-identical across all 5 known Wayback captures.
- Phase 330 — [GSMG_EXTERNAL_ARCHIVE_AUDIT](GSMG_EXTERNAL_ARCHIVE_AUDIT.md),
  independently verifies the whole-stream seven-key capacity exclusion and
  scopes the external frequency/mod-9 claims.

## Related objects

- [DBBI](GSMG_OBJECT_DBBI.md) — the paired raw stream on the same page.
- `lastwordsbeforearchichoice` / `thispassword` (macro tokens immediately
  following FAED) — see [MOC - Architect and Macro](MOC%20-%20Architect%20and%20Macro.md).
