---
type: audit
phase: 243
date: 2026-08-11
status: closed
result: negative
disposition: rejected
evidence_level: authenticated-artifact
topics:
  - dbbi
  - faed
  - escape-pair
  - page-structure
related_phases:
  - 101
  - 109
  - 113
  - 225
  - 236
  - 238
script: tools/gsmg/dbbi_faed_boundary_selector_audit.py
aliases:
  - Phase 243
---

# GSMG DBBI/FAED Boundary Page-Selector Audit

Bounded static-page test of [G-ESC-001](GSMG_OPEN_GAP_REGISTRY.md): does any
page-authored markup feature independently select between FAED's
IC-oracle-best `{g,i}` escape pair and the Architect-mirror-predicted `{h,e}`
pair, without relying on either derivation itself?

Reproduce with:

```bash
python3 tools/gsmg/dbbi_faed_boundary_selector_audit.py --self-test
```

## Pre-registered success condition

A stable page-authored feature must distinguish DBBI from FAED **and**
independently map to an escape pair or polarity. Different byte offsets, DOM
positions, or generic first/second ordering alone do not qualify — those are
descriptive, not selective.

## Scope

The local mirror (`gsmg-site-mirror/89727c...html`, the 2026-04-05 capture,
the sole raw HTML present locally) checked for:

- CSS rules that could distinguish the two textareas: ancestry, sibling
  position, `:first-*`/`:nth-*`, inherited styles, surrounding elements.
- JavaScript references to textareas or positional DOM selection.
- Wrapper DOM, comments, whitespace, capitalization, nearby labels.
- Cross-capture stability, using the metadata already established in
  `tools/gsmg/salphaseion_wayback_history_audit.py`'s `CAPTURES` table (no
  new Wayback fetch performed).

Raw byte offsets are recorded as descriptive evidence only; no arithmetic on
them is promoted without an independent clue, per the pre-registered
condition above.

## Result

The entire page is 54 lines: a `<title>`, five `<meta>` tags, one generic
`<style>` block, two headings, two `<textarea>`s, and one external script.

| Check | Finding |
|---|---|
| CSS selectors on the page | `body` only (`font-family: arial`) — no id/class/nth-*/textarea-specific rule exists to target either textarea |
| Textarea attributes | Byte-identical on both: `style="width: 100%; height: 200px"`, no `id`, `class`, `rows`, `cols`, or any other attribute |
| `<script>` tags | Exactly one: external, `defer`, third-party Cloudflare analytics beacon (`static.cloudflareinsights.com`) — no inline script, nothing referencing `textarea` |
| HTML comments | Zero, anywhere on the page |
| DOM boundary between DBBI and FAED | **None** — both are consecutive substrings of the *same* `<textarea>`'s text content, joined only by the binary-ASCII `matrixsumlist` span (confirmed via `page_structure_audit.py`'s segmentation: `dbbi -> abba_matrix_instruction -> faed`) |
| Whitespace | Uniform single-character separation (`raw == " ".join(logical)`) across the entire textarea; no double-space, tab, or pattern break at the DBBI/FAED join |
| Capitalization | The page's only case anomaly is the `H1`/`h1` heading pair, which distinguishes the *SalPhaseIon* textarea from the *Cosmic Duality* textarea — not DBBI from FAED, which sit inside the same SalPhaseIon textarea under the same heading. Already closed negative (Phase 109, `h_marker_selector_audit.py`: "no single, well-defined `h` to promote") |
| Cross-capture stability | The only markup diff established across all 5 known Wayback captures is that same `H1`/`h1` case change, between captures 1 and 2 (`assert_initial_heading_only_change`). Captures 2→3 (+32 bytes) and 3→4 (+504 bytes) are not sub-region-diffed locally in this pass — their raw bytes are not present outside the CDX/sha256 metadata, and fetching them was out of scope for this bounded static-page check |

**Pre-registered condition: not met.**

## Interpretation

Because DBBI and FAED are not separate DOM elements — they are consecutive
characters inside one `<textarea>`'s text node — the entire class of CSS
ancestry/sibling/`:nth-*` selectors is inapplicable **by construction**, not
merely empirically negative: there is no element boundary for such a rule to
attach to. Combined with the identical textarea attributes, the absent
inline/referencing JS, the absence of comments, and the uniform whitespace,
textarea markup and broader CSS/JS boundary selectors are exhausted for this
gap.

This closes one specific branch of G-ESC-001 (page-authored markup as an
independent selector) without resolving the gap itself. It does not weaken
or promote either escape-pair candidate, and it does not touch the
still-untested class of genuinely external selectors (a creator clue, a
different capture's content, or a source outside this page entirely).
[GSMG_FACT_LEDGER#F-OBJ-003](GSMG_FACT_LEDGER.md) is extended with this
scope note rather than given a new row.

## Reopen condition

A new Wayback capture, a creator source, or any primary artifact supplying a
page-authored (or otherwise independent) feature that selects between
`{g,i}` and `{h,e}` would reopen this specific branch. Byte-level diffing of
captures 2-4 against capture 1/5, if their raw HTML becomes available, is the
most direct concrete next step within this same branch.
