---
type: audit
phase: 252
date: 2026-08-13
status: closed
result: partial
disposition: recognition-only
evidence_level: solver-derived
topics:
  - salphaseion
  - page-structure
  - dns
  - game-of-logic
  - cosmic-duality-book
related_phases:
  - 156
  - 220
  - 239
  - 243
  - 244
  - 249
script: tools/gsmg/salphaseion_heading_metadata_audit.py
aliases:
  - Phase 252
---

# GSMG Fresh-Brainstorm Residual Audit

This closes or sharply bounds the three locally actionable residuals from
`GSMG_FRESH_BRAINSTORM_2026-08-06.md`, while preserving the physical-book
work as an explicit arrival-day checklist.

## 1. Heading and head-metadata channel — closed negative

Reproduce locally, or against exactly the five registered captures:

```bash
python3 tools/gsmg/salphaseion_heading_metadata_audit.py
python3 tools/gsmg/salphaseion_heading_metadata_audit.py --live
```

All five authenticated Wayback captures, spanning 2023-06-01 through
2026-04-05, have identical presentation facts:

- `SalPhaseIon` and `Cosmic Duality` are bare, text-only `<h1>` elements with
  no attributes, nested spans, per-character markup, or inline styles.
- The only class is generic `class="no-js"` on `<html>`.
- The only authored CSS is `body { font-family: 'arial'; }`, inherited equally
  by both headings. There is no color or `letter-spacing` declaration and no
  external stylesheet.
- `<title>` and meta description both say `GSMG Puzzle`.
- There is no explicit favicon `<link>`. The browser-default `/favicon.ico`
  artifact is already independently covered by Phases 239-242.
- The only raw heading variation is the known first-capture `<h1>` versus
  later `<H1>` capitalization of the SalPhaseIon opening tag. It supplies no
  per-character channel or selector.

No heading or head-metadata feature is promoted.

## 2. Historical DNS TXT — narrowed capability gap

Queries performed 2026-08-13:

| Owner/source | Result |
|---|---|
| live `gsmg.io` | `v=spf1 mx include:webhost-mail-out.dynadot.com include:spf.webhost.dynadot.com ~all` |
| live `www.gsmg.io` | no TXT |
| live `beta.gsmg.io` | no TXT |
| live `slack-invite.gsmg.io` | no TXT |
| live wildcard owner `*.gsmg.io` | no TXT |
| free WhoisFreaks history surface | 2026-04-21: `MS=ms93497059` plus Microsoft 365 SPF; older TXT values account-gated |

The exposed values are ordinary mail/domain-verification administration and
postdate the active puzzle period. This is not a puzzle-era negative: the
historical service confirms TXT coverage exists but does not freely reveal the
relevant older rows. The residual remains a documented external/tooling gap.

## 3. `_work/gameoflogic_ocr.txt` — recovered, recognition only

The filename was absent from this clone because it belongs to the separately
cited `halbgott29a` fork. Fetching that fork recovered the exact file from its
originating commit `8d043ad115ec7736ecff65f33812c7344ccf0221`:

- 90,139 bytes / 2,861 lines
- SHA-256 `e269153ec9d502dc25986e54169a1c211841a4f7256b460e4a017bae3242a002`
- reproducible with `python3 tools/gsmg/gameoflogic_source_audit.py --download`

The OCR contains a real structural resemblance: “nine counters — four of one
colour and five of another,” specifically four red and five grey, plus repeated
smaller/larger diagrams and half-diagram operations. Word-boundary counts are
`diagram=50`, `counter/counters=37`, `half=29`, `red=103`, and `grey=12`.

However, `matrix` occurs zero times, as do all registered puzzle-specific
terms and phrases (`matrixsumlist`, `yellowblueprimes`, `Cosmic Duality`,
`SalPhaseIon`, `sha256`, `first hint`, `last command`, `better half`, `white
rabbit`, `password`, and `architect`). The source was introduced in the same
AI-assisted analysis burst, and no authenticated creator clue selects it.

Disposition: retain the red/grey counter and half-diagram resemblance as
recognition evidence only. It does not authorize a new cipher alphabet,
candidate-string extraction, or oracle sweep.

## 4. Physical-book paratext — queued, externally blocked

The arrival checklist now separately requires ISBN/LCCN/Dewey/edition and
printing codes, dust-jacket price, and copy-specific markings/inserts. This is
captured alongside the gatefold but remains a distinct inspection pass. No
claim is made until the physical copy is available.
