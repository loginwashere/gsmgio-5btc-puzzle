---
type: index
status: live
topics:
  - phase-template
---

# GSMG Phase Description Template

Standard fields for new `tools/gsmg/FINDINGS.md` entries going forward. Not
retroactive — existing phases keep their current prose form. A dedicated
audit document (`doc/GSMG_*.md`) is still only worth creating when the phase
introduces substantial methodology, controls, code, or a conclusion likely
to be reused; most phases stay as a FINDINGS.md-only entry.

```markdown
## Phase 243 — concise subject (2026-08-12)

**Question:**
**Frozen inputs:**
**Method:**
**Result:**
**Disposition:**
**Facts affected:**
**Supersedes/corrects:**
**Artifacts:**
**Reopen condition:**
```

Field notes:

- **Facts affected** — list any [GSMG_FACT_LEDGER](GSMG_FACT_LEDGER.md) fact
  IDs this phase establishes, tests, or revises (e.g. `F-CHAIN-006`). Add new
  rows to the ledger only if the fact meets its stated inclusion criteria.
- **Supersedes/corrects** — phase number(s), if any, whose claim this phase
  changes. Phase 223's correction of Phase 33/216 is the model case.
- **Disposition** — use the same controlled vocabulary as the worksheet and
  fact ledger (`operative`, `recognition-only`, `structural-only`,
  `provenance-only`, `rejected`), not a free-text summary.
- **Reopen condition** — required even for negative results; state what new
  evidence would change the verdict, not just that none currently exists.

Once enough phases use these explicit fields,
`tools/gsmg/generate_phase_index.py` can be extended to read them directly
instead of inferring subject/result from the heading text — its current
heuristic is a reasonable default, not a long-term replacement.
