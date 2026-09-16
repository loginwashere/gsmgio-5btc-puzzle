#!/usr/bin/env python3
"""Phase 512M -- drives Phase 512L's locked real-FAED sweep across a chosen
subset of (crib, width) combinations not yet run.

Widths 19 and 30 only, per operator request: width-38 runs (especially the
credential's ~2.7-hour outlier) are deferred given thermal concerns raised
about the host machine during the width-19/30/38 matrix's first attempt.
Width 15 was already run for all three cribs (credential by Phase 512G,
validation answer and macro by Phase 512L itself).

Cheapest combination first, by measured (not projected) per-start cost, so
a hit stops the remaining, more expensive combinations from running
unnecessarily. Stops immediately on any hit_count > 0 rather than
continuing through the rest of the scope. A combination with a partial
checkpoint from an interrupted prior attempt (e.g. credential/width-30,
stopped mid-run for the same thermal reason) resumes rather than restarts.
"""
from __future__ import annotations

import json
from pathlib import Path

import phase512l_locked_faed_rust_sweep as phase512l


SCRIPT_DIR = Path(__file__).resolve().parent
RESULT = SCRIPT_DIR / "phase512m_result.json"

# (crib_id, width), ascending by measured per-combination full-family time.
# Width 38 intentionally excluded from this scope -- see module docstring.
ORDER = (
    ("phase1_credential", 19),
    ("phase1_credential", 30),
    ("phase322_validation_answer", 19),
    ("creator_macro_message", 19),
    ("phase322_validation_answer", 30),
    ("creator_macro_message", 30),
)


def already_done(crib_id: str, width: int) -> bool:
    label = phase512l.label_for(crib_id, width)
    return phase512l.result_path(label).exists()


def run_matrix() -> dict:
    rows = []
    stopped_early = False
    for crib_id, width in ORDER:
        if already_done(crib_id, width):
            label = phase512l.label_for(crib_id, width)
            result = json.loads(phase512l.result_path(label).read_text())
            rows.append({"crib_id": crib_id, "width": width, "skipped": True, **result})
            continue
        result = phase512l.resume_or_run_one(crib_id, width)
        rows.append({"crib_id": crib_id, "width": width, "skipped": False, **result})
        RESULT.write_text(json.dumps({
            "phase": "512M", "status": "in_progress", "rows": rows,
        }, indent=2, sort_keys=True) + "\n")
        if result["hit_count"] > 0:
            stopped_early = True
            break

    total_hits = sum(row["hit_count"] for row in rows)
    final = {
        "phase": "512M",
        "status": "complete",
        "combinations_run": len(rows),
        "combinations_total": len(ORDER),
        "stopped_early_on_hit": stopped_early,
        "total_hit_count": total_hits,
        "rows": rows,
    }
    RESULT.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n")
    return final


if __name__ == "__main__":
    print(json.dumps(run_matrix(), indent=2, sort_keys=True))
