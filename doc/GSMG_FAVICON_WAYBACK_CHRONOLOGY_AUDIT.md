---
type: audit
phase: 241
date: 2026-08-11
status: parked
result: inconclusive
disposition: provenance-only
evidence_level: authenticated-artifact
topics:
  - favicon
  - raster-analysis
  - phase-186
  - wayback
related_phases:
  - 186
  - 239
  - 240
  - 242
script: tools/gsmg/favicon_wayback_chronology_audit.py
aliases:
  - Phase 241
---

# GSMG favicon Wayback chronology audit

Date: 2026-08-11  
Phase: 241  
Scope: exact archived history of `https://www.gsmg.io/img/favicon_small.png`

## Question

Phase 239 verified a native C9 grayscale/alpha family in the served 48x48
favicon and the exact C9/E0 source pixel that renders as the nine-pixel CE
block in the Stage-0 screenshot. If the favicon existed unchanged before the
puzzle, that would favor inherited branding/export provenance over a
puzzle-specific pixel construction. If archived versions changed, their C9
and alpha layers could be compared directly.

This audit therefore asks only:

1. how many exact successful PNG captures Wayback records for the asset;
2. whether their payloads differ;
3. whether the first capture predates the puzzle launch; and
4. whether the archived payload reproduces Phase 239's C9 measurements.

It does not decode alpha bits or run a credential/blob oracle.

## Frozen archive result

The exact CDX query returns one successful PNG capture:

| Field | Value |
|---|---|
| Timestamp | `20190428234709` |
| Original URL | `https://www.gsmg.io/img/favicon_small.png` |
| Status / MIME | `200` / `image/png` |
| CDX digest | `JFMWHJ3SIABMV4CKU4BIJ3GHRLV7MCXM` |
| CDX record length | `3427` |
| PNG payload bytes | `2677` |
| Payload SHA-256 | `934f46d6a0a168a7ca2af725604d7e1dab8ee825ad0d7c682dbb252cc2be1423` |

The CDX `length` is the archived response-record length, not the decoded PNG
payload length. A second exact query without `www` canonicalizes to the same
capture; it does not add another historical version.

The raw Wayback payload, the sibling site's mirrored file, and
`doc/img/icons/favicon_small.png` are byte-for-byte identical. This
authenticates the repository copy to 2019-04-28 and rules out a later local
mutation as the source of C9.

## C9 continuity

Because the archived payload is byte-identical, every native measurement
reproduces exactly:

| Measurement | Archived value |
|---|---:|
| Canvas | `48x48 RGBA` |
| Visible RGB values | `233` |
| Visible grayscale bytes | `C9` only |
| Stored C9 RGB pixels | `264` |
| Visible C9 pixels | `96` |
| Opaque C9 pixels | `0` |
| Distinct visible C9 alpha values | `72` |
| Visible C9 bbox | `(4,12)..(42,46)` |

This confirms presence, not evolution: with one capture, there is no earlier
or later archived payload against which to measure a change.

## Chronology limit

The documented puzzle launch is 2019-04-20. The only capture is dated
2019-04-28, eight days later. It therefore does **not** establish that the
favicon, its C9 edge family, or its alpha distribution predates the puzzle.

The strongest supportable distinctions are:

- **Verified:** the present asset and its C9 properties existed by
  2019-04-28, within the original puzzle period.
- **Not verified:** that the same raster was inherited from pre-puzzle GSMG
  branding.
- **Not testable from Wayback:** whether C9 or the alpha family changed over
  multiple versions, because no alternate version is archived.

The generic Adobe XMP toolkit version string remains non-chronological; this
audit does not reinterpret it as an asset creation date.

## Verdict

**Chronology unresolved; payload provenance strengthened.** The sole archive
capture authenticates the current bytes and Phase 239's C9 measurements to
2019-04-28, but it postdates launch and provides no version series. This
neither falsifies nor strengthens C9 as an intentional puzzle operand, selects
no consumer, and authorizes no additional alpha traversal or oracle.

Reopen the chronology question only if an independently dated pre-2019-04-20
copy appears in a company archive, source/build package, version-control
history, or contemporaneous public branding material.

## Reproduction

Offline frozen audit:

```bash
python3 tools/gsmg/favicon_wayback_chronology_audit.py --self-test
```

Live exact CDX and raw-payload verification:

```bash
python3 tools/gsmg/favicon_wayback_chronology_audit.py --live
```
