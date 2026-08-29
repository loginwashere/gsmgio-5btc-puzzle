---
type: protocol
phase: 447
date: 2026-08-29
status: frozen-before-migration
topics:
  - findings
  - documentation
  - migration
  - compatibility
---

# Phase 447 — Per-Phase Findings Store Migration Protocol

## Objective

Make one canonical Markdown file per findings phase while preserving the
historical `tools/gsmg/FINDINGS.md` interface for links, anchors, scripts, and
external readers.

## Frozen naming

- Integer Phase N: `P` plus five zero-padded digits, e.g. `P00001.md` and
  `P00447.md`.
- Fractional historical phases: five-digit integer part plus hyphenated
  fraction, e.g. Phase 0.1 → `P00000-1.md`.
- Duplicate phase numbers: retain the existing stable suffix, e.g.
  `P00008-A.md` and `P00008-B.md`.
- Missing phase numbers receive no placeholder file.

## Compatibility requirements

1. The initial split must concatenate back to the exact pre-migration bytes.
2. `FINDINGS.md` remains tracked but is generated from the fragments.
3. Existing GitHub anchors and relative links in the monolith remain valid.
4. Relative links must also resolve when a fragment is viewed directly.
5. Existing stable IDs cannot change.
6. The phase index links to both canonical fragments and compatibility
   anchors.

## Store contract

- `_PREAMBLE.md` owns all text preceding the first phase.
- `manifest.json` owns document order; filename sorting is not authoritative.
- Each listed fragment contains exactly one `## Phase ...` heading.
- Every `P*.md` file is listed once and every manifest entry has a unique
  stable ID.
- New unique phases are appended through `findings_store.py register`.
- Duplicate-number additions fail closed for manual review.

## Verification

- exact reconstruction/drift check;
- filename, manifest-order, heading-count, and stable-ID checks;
- exceptional-name tests for fractional and duplicate phases;
- relative-link existence from both locations;
- all direct findings readers switched to the shared loader;
- phase-index and citation-graph self-tests;
- `git diff --check`.

This is a documentation migration only. No puzzle candidate, oracle, network,
Docker, GPU, or external-agent activity is authorized.
