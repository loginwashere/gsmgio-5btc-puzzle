#!/usr/bin/env python3
"""Phase 466: exact Phase-1 credential crib audit over DBBI/FAED."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crib_drag import apply_mapping, find_crib_matches
from data import DBBI, FAED
from first_hint_hash_audit import PHASE1_PASSWORD


RESULT_PATH = Path(__file__).with_name("phase466_result.json")
PREFIX = "theflower"
TARGETS = {
    "DBBI": (DBBI, (("b", "e"),)),
    "FAED": (FAED, (("g", "i"), ("h", "e"))),
}


def rotate(text: str, offset: int) -> str:
    offset %= len(text)
    return text[offset:] + text[:offset]


def audit() -> dict:
    credential = PHASE1_PASSWORD.decode("ascii")
    cribs = {
        "full_credential": credential,
        "continuation_after_theflower": credential[len(PREFIX):],
    }
    families = []
    for crib_name, crib in cribs.items():
        for target_name, (raw, pairs) in TARGETS.items():
            for e1, e2 in pairs:
                offsets = []
                for offset in range(len(crib)):
                    matches = find_crib_matches(raw, e1, e2, rotate(crib, offset))
                    offsets.append({
                        "offset": offset,
                        "match_count": len(matches),
                        "matches": [
                            {
                                "start_code_index": start,
                                "forced_mapping": mapping,
                                "partial_decode": apply_mapping(codes, mapping),
                            }
                            for start, mapping, codes in matches
                        ],
                    })
                offset_zero = offsets[0]["match_count"]
                control_matches = sum(row["match_count"] for row in offsets[1:])
                families.append({
                    "crib": crib_name,
                    "crib_length": len(crib),
                    "target": target_name,
                    "escape_pair": [e1, e2],
                    "offset_zero_matches": offset_zero,
                    "nonzero_control_matches": control_matches,
                    "offsets": offsets,
                    "promotion_gate": offset_zero > 0 and control_matches == 0,
                })
    promoted = [row for row in families if row["promotion_gate"]]
    return {
        "phase": 466,
        "credential": credential,
        "prefix": PREFIX,
        "families": families,
        "offset_zero_match_count": sum(row["offset_zero_matches"] for row in families),
        "nonzero_control_match_count": sum(row["nonzero_control_matches"] for row in families),
        "promoted_family_count": len(promoted),
        "oracle_calls": 0,
        "password_candidates": 0,
        "verdict": "promoted_manual_review" if promoted else "exact_crib_negative",
    }


def self_test() -> None:
    credential = PHASE1_PASSWORD.decode("ascii")
    assert credential.startswith(PREFIX)
    assert len(credential) == 53
    assert len(credential[len(PREFIX):]) == 44
    assert rotate("abcd", 1) == "bcda"
    assert rotate("abcd", 4) == "abcd"
    print("[*] Phase 466 self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result = audit()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "offset_zero_match_count": result["offset_zero_match_count"],
        "nonzero_control_match_count": result["nonzero_control_match_count"],
        "promoted_family_count": result["promoted_family_count"],
        "verdict": result["verdict"],
    }, indent=2))
    print(f"[*] wrote {args.output}")


if __name__ == "__main__":
    main()
