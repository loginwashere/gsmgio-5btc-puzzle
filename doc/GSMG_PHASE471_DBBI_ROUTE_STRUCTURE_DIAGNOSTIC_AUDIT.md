---
type: audit
phase: 471
date: 2026-09-02
status: closed
result: bounded_negative
---

# Phase 471 — DBBI Route Canonicalization and Structure Diagnostic Audit

## Result

This phase executed the bounded diagnostic subset of the 2026-09-02
in-session DBBI matrix-hypothesis catalog (234 ideas, 13 families), under a
protocol frozen before execution. Everything ran on the canonical 91-symbol
DBBI stream alone, value map `a=0..i=8`, shapes `7×13`/`13×7`, with no
password materials, decryptions, oracle calls, plaintext alignment, or FAED
usage.

**Route canonicalization census.** The closed route universe — 16 rectangle
reads per shape, all full-period toroidal walks (6×12×91 on `7×13`,
12×6×91 on `13×7`), and all affine index maps `n → an+b mod 91` — comprises
19,690 enumerated routes that collapse to exactly 19,686 distinct
permutations, and those 19,686 permutations give 19,686 distinct output
strings. The only collisions are the identity and the 180° rotation, each
reachable three ways (both rectangle shapes' row-major read/rot180 and the
matching affine map). Two structural facts follow: (a) DBBI's symbol
multiset produces **no accidental string equivalences** between distinct
routes in this universe, so any later route phase must budget for the full
distinct count; and (b) the affine `mod 91` family and the `7×13` toroidal
family are **disjoint** (string overlap 0) — the row-major index is not the
CRT bijection, so "CRT coordinates" and toroidal walks are different
families, not one family under two names. The catalog's suggestion that
they coincide is corrected.

**Finite-field structure.** The `7×13` matrix is full rank (7) over GF(2)
(parity and `{b,e}` planes), GF(3) (mod-3 and high-trit planes), and GF(9)
(full values). No parity-check relation, checksum row, or low-rank
structure exists in any tested field — the error-correcting-code family's
cheapest signals are absent.

**Calibrated 2D statistics.** Against 10,000 count-preserving shuffles
(seed 471), none of the 12 toroidal offset match-rate statistics approaches
the frozen family-corrected bar (two-sided p < 0.001/17 ≈ 5.9e-5). The
smallest p is 0.14 (`{b,e}` matches at offset (2,0), observed 53 vs null
mean 45.2). DBBI's 2D layout is statistically indistinguishable from a
shuffled bag of its own symbols under every tested offset — no periodic
tiling, anisotropy, or vertical coupling.

**Exact-bar packings.** Base-9 line packing: 0 of 8 readings printable.
Seven-segment: 3 of 88 readings decode 13/13 valid glyphs, and all three
are the *inverted* sparse masks (`a`, `d`, `i` — 3, 4, and 5 cells), whose
near-saturated segment states decode overwhelmingly to `8` (e.g.
`88868A8888088`). Since 6 of the 7 single-segment-off states are themselves
valid glyphs, an inverted sparse mask passes the validity bar almost by
construction; these are recorded as degenerate bar-mets, carrying no
message-like content. `{b,e}` bitmask ASCII: 2 of 24 readings printable,
both the inverted dominant-`b` mask on `13×7` rows (`Jvuoi{W>>_^_=` and its
bit-reversal) — a density artifact (66/91 ones keeps 7-bit values in the
printable band), with no recognizable content. Under the memory discipline
these five records are reported as unconfirmed degenerate coincidences, not
leads; any follow-up would first need a preregistered saturation/density-
controlled null, which the frozen protocol correctly forbids adding
post hoc.

The 11 mask renderings in both orientations are stored in the result file
for human inspection; no automated claim is made about them.

## Disposition

`bounded_negative`. The catalog's batch items 1 and 3–7 are now executed
and negative or degenerate at their frozen bars; the census additionally
establishes the equivalence-control infrastructure (19,686 distinct
readings) and corrects the catalog's CRT-coincidence claim. Batch items 2
(interpretive mask reading), 8 (route-aware plaintext alignment), 9
(first-occurrence permutation schedules), and 10 (oracle feeding) remain
deferred and unlicensed. `G-MSL-001` is unchanged — nothing here binds an
operand, transform, or consumer.

## Reproduction

```bash
cd tools/gsmg
python3 phase471_dbbi_route_structure_diagnostic_audit.py
python3 -m unittest test_phase471_dbbi_route_structure_diagnostic_audit
```

Artifacts: frozen protocol
(`doc/Brainstorms/2026-09-02 - Phase 471 DBBI Route Canonicalization and
Structure Diagnostic Protocol.md`), `phase471_manifest.json`,
`phase471_execution_lock.json`, `phase471_result.json`,
`phase471_result_record.json`, and the unittest module.

## Reopen condition

Authenticated creator evidence selecting a specific route, mask, or field
structure; or a separately preregistered saturation-controlled follow-up
protocol for the degenerate exact-bar families.
