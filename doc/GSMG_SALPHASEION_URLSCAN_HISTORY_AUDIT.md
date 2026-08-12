---
type: audit
phase: 249
date: 2026-08-12
status: closed
result: negative
disposition: rejected
evidence_level: authenticated-artifact
topics:
  - salphaseion
  - urlscan
  - archive
  - escape-pair
related_phases:
  - 243
  - 244
script: tools/gsmg/salphaseion_urlscan_history_audit.py
aliases:
  - Phase 249
---

# GSMG SalPhaseIon urlscan History Audit

Bounded follow-up to the non-Wayback archive brainstorm and to
[G-ESC-001](GSMG_OPEN_GAP_REGISTRY.md). Reproduce offline or recheck the
public index with:

```bash
python3 tools/gsmg/salphaseion_urlscan_history_audit.py --self-test
python3 tools/gsmg/salphaseion_urlscan_history_audit.py --live
```

## Scope and result

The exact urlscan search for the SalPhaseIon route returns 12 scans. Eleven
are successful page responses; the 2026-05-05 scan is an HTTP 503 error page
and is not counted as puzzle content. Contrary to the brainstorm ledger's
initial date summary, the earliest scan is **2023-05-31 02:49:16 UTC**, about
43 hours before the earliest Wayback capture (`2023-06-01 22:27:52`).

urlscan labels each captured response with a resource hash. Every successful
main-document hash exactly equals one of the raw-HTML SHA-256 values already
pinned and byte-verified by Phase 244:

| urlscan dates | Count | Exact authenticated variant |
|---|---:|---|
| 2023-05-31 | 1 | `18a8369d…6308b` (Wayback capture 1) |
| 2024-03-04 through 2024-04-16 | 3 | `ed6c3958…59af` (Wayback capture 2) |
| 2024-12-04 through 2026-02-11 | 7 | `0eeb42e3…c4d0` (Wayback capture 3) |

Thus the 11 new capture events add no new page variant: their complete HTML,
including the SalPhaseIon textarea, is byte-for-byte identical to already
authenticated material. Combined archive coverage is now 16 successful
capture events (5 Wayback + 11 urlscan), spanning 2023-05-31 to 2026-04-05.

**Pre-registered condition: not met.** No DBBI/FAED difference, escape-pair
selector, or new puzzle content appears. The new capture source triggered
G-ESC-001's reopen condition and was checked; the gap returns to `parked`.

## Reopen condition

A capture whose main-document resource hash is not one of the five pinned
Wayback variants, or a genuinely external creator/primary source that selects
between `{g,i}` and `{h,e}`. More capture dates carrying these same hashes do
not reopen the branch.
