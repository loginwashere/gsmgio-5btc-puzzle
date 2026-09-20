# Phase 529 — DBBI payload material overlap audit

Date: 2026-09-20  
Disposition: **90/90 materials genuinely fresh; oracle not yet called**

## Question and scope

Do the five exact payload bases isolated by Phase 528 remain new after applying
only the project's established solved-boundary password forms?

The frozen family contains the 61-symbol residue, the 35- and 25-symbol host
rails, and their two direct concatenation orders. The historical 60-symbol
residue, reversals, separators, interleavings, numeric encodings, and other
transform axes were excluded.

Each pure-letter base was expanded through Phase 523's unchanged standard
registry: lower/upper case × raw/SHA-256-hex/double-SHA-256-hex × no/LF/CRLF.
This yields exactly 18 forms per base and 90 unique materials total.

## Comparator coverage

| Comparator | Scope scanned | Exact hits |
|---|---:|---:|
| Phase 523 historical coverage | 18 sources / 2,456,427 material keys | 0 |
| Phase 524 executed sweep | 133,547 bases / 6,245,429 expansions | 0 |
| Phase 527 executed sweep | 112,624 bases / 5,136,688 expansions | 0 |
| Phase 478 submitted manifest | 1,749,878 byte records | 0 |

No candidate even collided with a Phase-523/524/527 64-bit rejection key. The
Phase-478 comparison was exact bytes. Therefore all **90/90** materials are
fresh, and every one of the five source bases retains all 18 forms.

## Verification

- Five focused tests and the module self-test pass.
- Runtime: 18.622 seconds.
- Oracle calls: zero.
- Result SHA-256:
  `2490cc9363d9af892066ff2eba2d41bca8282d76b2a2f3b306e1745faaeb6527`.
- Frozen five-base list SHA-256:
  `2ac0d46de28a77d30cd670b8f35d7c67b2e22032830018d2c5fd3e820c919c3d`.

## Interpretation

This is a materially different situation from the enormous coordinate family:
the new source consequence collapses to only 90 already-standard materials.
Testing them will not repeat a prior oracle call and does not require GPU-scale
compute. Freshness is not evidence that the bases are correct passwords.

## Next gate

A separately locked Phase 530 may run the five bases through the same fixed
four-blob, 60-variant oracle used in Phase 527, with the Bloom and known-target
checks active. The expected expanded form count is exactly 90. A zero-hit
result closes only these five bases and the standard form registry; it cannot
license additional formatting or transforms.

