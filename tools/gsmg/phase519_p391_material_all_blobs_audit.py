#!/usr/bin/env python3
"""Phase 519: extend Phase 391's numeric/temporal material to all four blobs.

Phase 391 froze a 69-material manifest (15 authenticated milestone numbers
x 4 representations, plus 9 literal date/HTTP-date strings) and ran it
against P32TRAILING only, by explicit declared scope. This is the same
"single-blob scope creep" pattern Phase 381 had (fixed by Phase 517 item 8):
a material family gets built and tested against one blob and never
re-checked against the other three. No new material, representation, or
oracle family is added here -- this widens the blob set only, reusing
Phase 391's manifest and oracle-calling code exactly as written.
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS  # noqa: E402
import phase391_bounded_numeric_temporal_p32trailing_audit as p391  # noqa: E402

ALL_BLOBS = BLOBS


def run_all_blobs():
    return p391.run_oracle(blobs=ALL_BLOBS)


def self_test():
    # Reproduce Phase 391 exactly (P32TRAILING-only, default scope) first.
    original = p391.run_oracle()
    assert original["material_count"] == 69, original["material_count"]
    assert original["blobs"] == ("P32TRAILING",)
    assert original["total_hits"] == 0, original["hits"]

    # Now widen to all four blobs with the identical manifest/oracle code.
    result = run_all_blobs()
    assert result["material_count"] == 69, result["material_count"]
    assert set(result["blobs"]) == {"SALPH", "COSMIC", "P32TRAILING", "URLBLOB"}
    assert result["effective_decrypt_attempts"] == original["effective_decrypt_attempts"] * 4

    print(
        "[*] self-test OK: Phase 391 reproduced exactly (69 materials, "
        "P32TRAILING-only, 0 hits); scope-widened rerun against all four "
        f"blobs made {result['effective_decrypt_attempts']} attempts, "
        f"{result['total_hits']} hits"
    )
    return {"original": original, "widened": result}


def main():
    result = run_all_blobs()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
