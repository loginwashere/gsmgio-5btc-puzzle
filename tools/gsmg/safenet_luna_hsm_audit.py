#!/usr/bin/env python3
"""Audit the historical SafeNet/Luna HSM vocabulary as an endgame lead."""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402

CANDIDATE_FILE = (
    SCRIPT_DIR.parents[1]
    / "wordlists"
    / "gsmg"
    / "safenet_luna_hsm_candidates.txt"
)

PRODUCT_CHAIN = ("SafeNet", "Luna", "HSM")
PED_ROLE_COLORS = {
    "blue": "HSM Security Officer",
    "red": "cloning domain",
    "black": "Partition Owner/Crypto Officer",
    "gray": "Crypto User",
    "white": "Auditor",
    "orange": "Remote PED",
    "purple": "Secure Recovery",
}
FIRST_PIECE_COLORS = frozenset(("black", "white", "blue", "yellow"))
STAGE1_ICON_COLORS = frozenset(("black", "white", "blue", "red"))
HIGH_VALUE_MECHANICS = (
    "MofN",
    "dual control",
    "cloning domain",
    "partition",
    "private key wrapping",
)
CREATOR_TERM_RE = re.compile(
    r"\b(?:SafeNet|Luna|HSM|Thales|Gemalto|PED|MofN|"
    r"cloning domain|dual control|split knowledge)\b",
    re.IGNORECASE,
)
CREATOR_ID = "user9815232"


def load_candidates(path=CANDIDATE_FILE):
    candidates = []
    seen = set()
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line in seen:
            continue
        seen.add(line)
        candidates.append(line)
    return tuple(candidates)


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def creator_mentions(export_path=DEFAULT_EXPORT_DIR):
    result_path = Path(export_path) / "result.json"
    if not result_path.exists():
        return None
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    matches = []
    for message in payload["messages"]:
        if message.get("from_id") != CREATOR_ID:
            continue
        text = flatten_text(message.get("text", ""))
        terms = tuple(sorted(set(CREATOR_TERM_RE.findall(text)), key=str.lower))
        if terms:
            matches.append(
                {
                    "id": message["id"],
                    "date": message.get("date"),
                    "terms": terms,
                    "text": text,
                }
            )
    return tuple(matches)


def structural_audit(export_path=DEFAULT_EXPORT_DIR):
    first_overlap = FIRST_PIECE_COLORS & PED_ROLE_COLORS.keys()
    stage1_overlap = STAGE1_ICON_COLORS & PED_ROLE_COLORS.keys()
    mentions = creator_mentions(export_path)
    return {
        "product_chain": PRODUCT_CHAIN,
        "historical_context": {
            "gemalto_acquired_by_thales": "2019-04-02",
            "puzzle_launch": "2019-04-20",
            "days_before_launch": 18,
        },
        "ped_role_colors": PED_ROLE_COLORS,
        "first_piece": {
            "colors": tuple(sorted(FIRST_PIECE_COLORS)),
            "overlap": tuple(sorted(first_overlap)),
            "puzzle_only": tuple(sorted(FIRST_PIECE_COLORS - PED_ROLE_COLORS.keys())),
            "ped_only": tuple(sorted(PED_ROLE_COLORS.keys() - FIRST_PIECE_COLORS)),
        },
        "stage1_icons": {
            "colors": tuple(sorted(STAGE1_ICON_COLORS)),
            "overlap": tuple(sorted(stage1_overlap)),
            "puzzle_only": tuple(sorted(STAGE1_ICON_COLORS - PED_ROLE_COLORS.keys())),
            "ped_only": tuple(sorted(PED_ROLE_COLORS.keys() - STAGE1_ICON_COLORS)),
        },
        "high_value_mechanics": HIGH_VALUE_MECHANICS,
        "creator_mentions": mentions,
        "verdict": (
            "The historical product vocabulary is a legitimate source family "
            "because SafeNet/Luna/HSM is an authenticated solved-phase chain "
            "and the Thales acquisition predates the puzzle launch. The PED "
            "color overlap and M-of-N/dual-control/private-key terminology are "
            "suggestive, but no creator-authored message selects this glossary "
            "for the endgame, yellow has no PED role, and no role ordering maps "
            "to an established puzzle operation. Treat exact terms as bounded "
            "coverage, not as a demonstrated transition rule."
        ),
    }


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(
                        keystring,
                        kdf_variants=variants,
                        blobs=blobs,
                    )
                    if result:
                        hits["cbc"].append((candidate, keystring, result))
                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))
                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))
                for result in aes_keywrap_try_open_bytes(
                    keystring.encode(),
                    blobs=blobs,
                ):
                    hits["keywrap"].append((candidate, keystring, result))
    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def self_test():
    candidates = load_candidates()
    assert len(candidates) == 62
    assert candidates[:3] == PRODUCT_CHAIN
    assert len(set(candidates)) == len(candidates)
    for required in (
        "Thales",
        "MofN",
        "dual control",
        "cloning domain",
        "private key wrapping",
        "blue PED Key",
        "purple PED Key",
    ):
        assert required in candidates
    report = structural_audit()
    assert report["historical_context"]["days_before_launch"] == 18
    assert report["first_piece"]["puzzle_only"] == ("yellow",)
    assert report["stage1_icons"]["puzzle_only"] == ()
    if report["creator_mentions"] is not None:
        assert report["creator_mentions"] == ()
    print(
        "[*] self-test OK: historical vocabulary, palettes, timing, "
        "and creator-provenance boundary verified"
    )
    return report


def print_report(report):
    timing = report["historical_context"]
    print(
        "[*] timing: Thales/Gemalto acquisition "
        f"{timing['gemalto_acquired_by_thales']}, puzzle "
        f"{timing['puzzle_launch']} ({timing['days_before_launch']} days)"
    )
    print(f"[*] PED role colors: {report['ped_role_colors']}")
    print(f"[*] first-piece palette: {report['first_piece']}")
    print(f"[*] Stage-1 icon palette: {report['stage1_icons']}")
    print(f"[*] high-value mechanics: {report['high_value_mechanics']}")
    if report["creator_mentions"] is None:
        print("[*] creator-term audit: export unavailable")
    else:
        print(
            "[*] creator-term audit: "
            f"{len(report['creator_mentions'])} matching messages"
        )
    print(f"[*] verdict: {report['verdict']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=CANDIDATE_FILE)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = structural_audit(args.export)
    print_report(report)

    if args.oracle:
        candidates = load_candidates(args.candidates)
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(candidates, blobs)
        total_hits = sum(len(values) for values in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")


if __name__ == "__main__":
    main()
