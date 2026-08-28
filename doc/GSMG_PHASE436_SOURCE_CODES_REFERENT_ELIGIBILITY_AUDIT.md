---
type: audit
phase: 436
date: 2026-08-28
status: closed
result: protocol-invalid
disposition: no-puzzle-result
script: tools/gsmg/phase436_source_codes_referent_eligibility_audit.py
---

# Phase 436 — `SOURCE CODES` Referent Eligibility Audit

Phase 436 failed closed before evaluating referent eligibility. Its frozen
protocol required a `FINDINGS.md` entry for Phase 418. The Phase 418 protocol
and implementation artifacts exist, and later findings refer to its packet,
but there is no Phase 418 heading or completed result in the findings ledger.

The live run successfully re-derived and pinned the authenticated Phase 3.2
objects and rebuilt Phase 270's 25 base candidates / 50 materials before the
required-findings assertion fired. It then stopped with zero generated
password materials, zero oracle calls, and no GPU activity.

This is a protocol/bookkeeping result, not evidence for or against any
`SOURCE CODES` referent. Phase 437 corrects only the faulty documentary
requirement: it requires the actual Phase 418 protocol artifact and uses
completed Phase 416/417/421/423 findings for execution history. All referent
and eligibility gates remain unchanged.
