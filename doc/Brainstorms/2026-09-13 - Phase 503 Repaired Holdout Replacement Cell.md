# Phase 503 repaired holdout replacement cell

Date: 2026-09-13
Status: frozen design; execution lock issued separately

Phase 502 predeclared holdout fixtures 3 and 4 but its pre-lock self-test only
validated fixture 3.  Fixture 3 subsequently passed exact top-1 recovery.
Fixture 4 failed construction before any objective marker, solver scoring, or
GPU work because its edit fraction is `0.1879350348`, above the frozen `0.18`
gate.  Phase 502 is therefore infeasible as written, not solver-negative.

Before any additional solver run, indices from 4 upward were screened only by
the already-frozen construction gates.  Index 5 is the first eligible
successor: edit fraction `0.1624129930`, normalized quadgram `-4.5617931713`.
Phase 503 preserves Phase 502 fixture 3's locked result and runs only fixture
5 under the identical repaired schedule.  The combined decision is exact
top-1 recovery on both pre-outcome-selected valid fixtures 3 and 5.

No schedule field changes.  Depth 11 alone uses unrestricted `8 x 20,000`;
all other board-aware depths use the Phase-502 budgets.  The execution lock
pins the Phase-502 lock/result, fixture-5 bytes and plaintext, all code and
binaries, and the exact schedules.

- Both fixtures exact top-1: gate passes and licenses a separately locked
  single FAED `{g,i}`, width-19 run.
- Fixture 5 misses: gate fails and no FAED run follows.

This repair does not reinterpret fixture 4 as a pass or erase the Phase-502
protocol error.  FAED and P32 are unavailable here.
