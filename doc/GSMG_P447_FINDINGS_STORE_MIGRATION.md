---
type: audit
phase: 447
date: 2026-08-29
status: complete
result: canonical-per-phase-store-with-generated-compatibility-view
disposition: infrastructure
script: tools/gsmg/findings_store.py
---

# Phase 447 — Canonical Per-Phase Findings Store

## Result

`tools/gsmg/findings/` is now the canonical findings source. The migration
split all 441 pre-existing headings into one file each and reconstructed the
pre-migration `FINDINGS.md` byte-for-byte before any migration notice or Phase
447 entry was added. The 441-entry compatibility SHA-256 was
`f9c8754031656406edf74f2ac0e6c26c2c83dd51ca27154c6a11773251d6fda4`, pinned
in the manifest's migration provenance. Phase 447 is registered as the 442nd
canonical entry.

The requested five-digit scheme is enforced:

| Case | Filename |
|---|---|
| Phase 1 naming rule | `P00001.md` (no file exists because the history has no Phase 1 heading) |
| Phase 25 | `P00025.md` |
| Phase 446 | `P00446.md` |
| Phase 447 | `P00447.md` |
| Phase 0.1 | `P00000-1.md` |
| duplicate Phase 8 | `P00008-A.md`, `P00008-B.md` |
| duplicate Phase 19 | `P00019-A.md`, `P00019-B.md` |

Missing numbers are intentionally absent rather than represented by empty
placeholder files.

## Compatibility design

`manifest.json` preserves historical document order, which filename sorting
cannot reproduce because Phase 8 and Phase 19 each occur twice. `_PREAMBLE.md`
owns the title/TL;DR text before the first heading.

`findings_store.py build` concatenates the canonical entries into the tracked
`tools/gsmg/FINDINGS.md`. Existing links and heading anchors therefore remain
available. Canonical files are one directory deeper, so the store maintains
their relative Markdown links at fragment depth and mechanically removes one
`../` segment only in the generated view. All 95 historical relative links
were checked from both locations.

The phase index now exposes both links:

- **Source** opens the canonical `P*.md` fragment;
- **FINDINGS** opens the historical generated-file anchor.

## Reader migration

The index generator, phase citation graph, and Phases 434, 436, 437, and 446
now read through `read_findings()`, as does the duplicate-phase regression in
`test_recent_audits.py`. The loader reconstructs from fragments when the
manifest exists and retains a bootstrap fallback to the monolith before a
store has been created.

## Workflow

Add a normal new phase with:

```bash
python3 tools/gsmg/findings_store.py register P00448.md
python3 tools/gsmg/findings_store.py build
python3 tools/gsmg/generate_phase_index.py
```

Then enforce drift and structure:

```bash
python3 tools/gsmg/findings_store.py validate
python3 tools/gsmg/findings_store.py build --check
python3 tools/gsmg/generate_phase_index.py --check
```

Duplicate-number registration deliberately fails closed because it would need
new explicit stable IDs and reviewed filename changes.

## Verdict

Disposition: `canonical_per_phase_store_with_generated_compatibility_view`.

The migration changes storage and navigation, not any historical finding.
No puzzle candidate or password material was generated and no oracle, network,
Docker, GPU, or external agent was used.
