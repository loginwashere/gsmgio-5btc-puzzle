#!/usr/bin/env python3
"""Phase 525A: reconstruct DBBI Selection A and audit exact-byte novelty.

No decryption or password oracle is imported or called by this module.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import itertools
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI  # noqa: E402
from first_piece_color_reconstruction import (  # noqa: E402
    DEFAULT_IMAGE,
    reconstruct,
)

EXPORT_RESULT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/"
    "ChatExport_2026-09-19/result.json"
)
ATLAS_PDF = EXPORT_RESULT.parent / "files/GSMG IO ATLAS.pdf"
PHASE478_MANIFEST = SCRIPT_DIR / "phase478_manifest.jsonl"
PHASE523_BASES = REPO_ROOT / "_work/phase523/not_all_covered_bases.txt"
RESULT_PATH = SCRIPT_DIR / "phase525_selection_a_result.json"

EXPECTED_HASHES = {
    "export_result": "e17ae0de8411ce63caf1ff77f1ffd0f111503c9b6a120fac9e7770849288e8ec",
    "atlas_pdf": "b21dffa6be14661c0060e9a3d36fe6befd6e1ed9e48e1e971a5342dc9a8c9c14",
    "stage0_image": "5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f",
}
EXPECTED_EVENT_COLORS = "BBBBYBBBYYBBBBYBBYYBFYYBY"
EXPECTED_PARSE_SUMMARY = {
    83: (15, 8, "BBBBYBBBYYBBBBYBBYYBBYY"),
    84: (16, 7, "BBBBYBBBYYBBBBYBBYYBBYB"),
}
EXPECTED_MATCHES_84 = ((22, 25), (23, 25))
SELECTION_A_OMITTED = (22, 25)
SELECTION_B_OMITTED = (23, 25)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def enumerate_complete_parses(raw: str) -> list[tuple[str, ...]]:
    """Enumerate the prime-host grammar without assuming logical length."""
    solutions: list[tuple[str, ...]] = []

    def visit(raw_offset: int, logical_position: int, tokens: tuple[str, ...]) -> None:
        if raw_offset == len(raw):
            solutions.append(tokens)
            return
        if raw_offset > len(raw):
            return
        if is_prime(logical_position):
            if raw.startswith("b", raw_offset):
                visit(raw_offset + 1, logical_position + 1, tokens + ("b",))
            if raw.startswith("be", raw_offset):
                visit(raw_offset + 2, logical_position + 1, tokens + ("be",))
            return
        symbol = raw[raw_offset]
        if symbol < "a" or symbol > "i":
            return
        visit(raw_offset + 1, logical_position + 1, tokens + (symbol,))

    visit(0, 1, ())
    return sorted(solutions, key=len)


def parse_record(tokens: tuple[str, ...]) -> dict:
    hosts = [token for index, token in enumerate(tokens, start=1) if is_prime(index)]
    colors = "".join("Y" if token == "be" else "B" for token in hosts)
    return {
        "logical_length": len(tokens),
        "host_count": len(hosts),
        "b_hosts": hosts.count("b"),
        "be_hosts": hosts.count("be"),
        "nonprime_symbols": len(tokens) - len(hosts),
        "host_colors": colors,
        "final_token": tokens[-1],
        "tokens": list(tokens),
    }


def picture_events(image_path: Path = DEFAULT_IMAGE) -> list[dict]:
    image = reconstruct(image_path)
    events = []
    for item in image["objects"]:
        events.append(
            {
                "kind": "ordinary_endpoint",
                "source_byte": item["ordinal_1"],
                "character": item["character"],
                "color": "B" if item["color"] == "blue" else "Y",
                "match_color": "B" if item["color"] == "blue" else "Y",
                "spiral_0": item["spiral_0"],
                "spiral_1": item["spiral_1"],
                "row_1": item["row_1"],
                "column_1": item["column_1"],
            }
        )
    fefe = image["fefe"]
    events.append(
        {
            "kind": "fefe",
            "source_byte": fefe["character_1"],
            "character": fefe["character"],
            "color": "F",
            "match_color": "B",
            "spiral_0": fefe["spiral_0"],
            "spiral_1": fefe["spiral_1"],
            "row_1": fefe["row_1"],
            "column_1": fefe["column_1"],
        }
    )
    events.sort(key=lambda event: event["spiral_0"])
    for rank, event in enumerate(events, start=1):
        event["event_rank"] = rank
    colors = "".join(event["color"] for event in events)
    if colors != EXPECTED_EVENT_COLORS:
        raise AssertionError(f"25-event color sequence drifted: {colors}")
    return events


def compatible_selections(events: list[dict], colors: str) -> list[dict]:
    matches = []
    for omitted in itertools.combinations(range(1, len(events) + 1), 2):
        kept = [event for event in events if event["event_rank"] not in omitted]
        observed = "".join(event["match_color"] for event in kept)
        if observed == colors:
            source_bytes = [event["source_byte"] for event in kept]
            matches.append(
                {
                    "omitted_event_ranks": list(omitted),
                    "kept_event_ranks": [event["event_rank"] for event in kept],
                    "distinct_source_bytes": len(set(source_bytes)),
                    "source_bytes": source_bytes,
                    "represents_source_bytes_1_through_23_once": (
                        sorted(source_bytes) == list(range(1, 24))
                    ),
                }
            )
    return matches


def serialize_vector(label: str, values: list[int]) -> list[dict]:
    return [
        {"label": f"{label}_sum", "value": str(sum(values)), "kind": "sum"},
        {
            "label": f"{label}_list_compact",
            "value": "".join(map(str, values)),
            "kind": "list_compact",
        },
        {
            "label": f"{label}_list_comma",
            "value": ",".join(map(str, values)),
            "kind": "list_comma",
        },
    ]


def representations(selected: list[dict]) -> list[dict]:
    colors = "".join(event["match_color"] for event in selected)
    records = [
        {"label": "selected_url_bytes", "value": "".join(e["character"] for e in selected), "kind": "text"},
        {"label": "selected_colors_by", "value": colors, "kind": "colors"},
        {"label": "selected_colors_blue1", "value": colors.translate(str.maketrans("BY", "10")), "kind": "bits"},
        {"label": "selected_coordinates_row_col_pairs", "value": ";".join(f"{e['row_1']},{e['column_1']}" for e in selected), "kind": "coordinate_pairs"},
    ]
    vectors = {
        "event_rank": [e["event_rank"] for e in selected],
        "source_byte": [e["source_byte"] for e in selected],
        "spiral_0": [e["spiral_0"] for e in selected],
        "spiral_1": [e["spiral_1"] for e in selected],
        "row_1": [e["row_1"] for e in selected],
        "column_1": [e["column_1"] for e in selected],
        "row_col_flat_1": list(
            itertools.chain.from_iterable((e["row_1"], e["column_1"]) for e in selected)
        ),
    }
    for label, values in vectors.items():
        records.extend(serialize_vector(label, values))
    if len({record["label"] for record in records}) != len(records):
        raise AssertionError("duplicate representation labels")
    return records


def scan_phase478(targets: dict[bytes, list[str]]) -> tuple[int, dict[str, bool]]:
    found = {label: False for labels in targets.values() for label in labels}
    records = 0
    with PHASE478_MANIFEST.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records += 1
            record = json.loads(line)
            raw = base64.b64decode(record["bytes_b64"])
            for label in targets.get(raw, ()):  # exact submitted bytes only
                found[label] = True
    return records, found


def scan_phase523(targets: dict[str, list[str]]) -> tuple[int, dict[str, bool]]:
    found = {label: False for labels in targets.values() for label in labels}
    records = 0
    with PHASE523_BASES.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records += 1
            value = json.loads(line)
            for label in targets.get(value, ()):  # exact base, before Phase-524 expansion
                found[label] = True
    return records, found


def audit(run_comparators: bool = True) -> dict:
    actual_hashes = {
        "export_result": sha256_file(EXPORT_RESULT),
        "atlas_pdf": sha256_file(ATLAS_PDF),
        "stage0_image": sha256_file(DEFAULT_IMAGE),
    }
    if actual_hashes != EXPECTED_HASHES:
        raise AssertionError(f"pinned input hash mismatch: {actual_hashes}")

    parses = [parse_record(tokens) for tokens in enumerate_complete_parses(DBBI)]
    summary = {
        record["logical_length"]: (
            record["b_hosts"], record["be_hosts"], record["host_colors"]
        )
        for record in parses
    }
    if summary != EXPECTED_PARSE_SUMMARY:
        raise AssertionError(f"DBBI parse family drifted: {summary}")

    events = picture_events()
    parse_matches = {
        str(record["logical_length"]): compatible_selections(events, record["host_colors"])
        for record in parses
    }
    matches84 = tuple(
        tuple(item["omitted_event_ranks"]) for item in parse_matches["84"]
    )
    if matches84 != EXPECTED_MATCHES_84:
        raise AssertionError(f"84-token picture matches drifted: {matches84}")

    selection_a = [e for e in events if e["event_rank"] not in SELECTION_A_OMITTED]
    source_bytes = [e["source_byte"] for e in selection_a]
    if source_bytes != list(range(1, 24)):
        raise AssertionError(f"Selection A is not byte-representative: {source_bytes}")
    selection_b = [e for e in events if e["event_rank"] not in SELECTION_B_OMITTED]
    if len(set(e["source_byte"] for e in selection_b)) != 22:
        raise AssertionError("Selection B control unexpectedly represents 23 distinct bytes")

    candidates = representations(selection_a)
    comparator_summary = {
        "executed": run_comparators,
        "phase478_records": None,
        "phase523_records": None,
    }
    if run_comparators:
        byte_targets: dict[bytes, list[str]] = {}
        text_targets: dict[str, list[str]] = {}
        for candidate in candidates:
            byte_targets.setdefault(candidate["value"].encode("utf-8"), []).append(candidate["label"])
            text_targets.setdefault(candidate["value"], []).append(candidate["label"])
        count478, found478 = scan_phase478(byte_targets)
        count523, found523 = scan_phase523(text_targets)
        comparator_summary.update(
            {"phase478_records": count478, "phase523_records": count523}
        )
        for candidate in candidates:
            candidate["phase478_exact_submitted_bytes"] = found478[candidate["label"]]
            candidate["phase523_exact_base"] = found523[candidate["label"]]
            candidate["new_to_named_exact_comparators"] = not (
                found478[candidate["label"]] or found523[candidate["label"]]
            )

    return {
        "phase": "525A",
        "scope": "oracle-free DBBI Selection-A reconstruction and exact-byte novelty audit",
        "pinned_hashes": actual_hashes,
        "dbbi_raw_length": len(DBBI),
        "dbbi_sha256_utf8": hashlib.sha256(DBBI.encode()).hexdigest(),
        "complete_parse_count": len(parses),
        "parses": parses,
        "picture_events": events,
        "picture_compatible_selections": parse_matches,
        "selection_a": {
            "omitted_event_ranks": list(SELECTION_A_OMITTED),
            "selected_events": selection_a,
            "distinct_source_bytes": len(set(source_bytes)),
            "represents_source_bytes_1_through_23_once": True,
        },
        "selection_b_control": {
            "omitted_event_ranks": list(SELECTION_B_OMITTED),
            "distinct_source_bytes": len(set(e["source_byte"] for e in selection_b)),
            "represents_source_bytes_1_through_23_once": False,
        },
        "representations": candidates,
        "comparators": comparator_summary,
        "disposition": (
            "Selection A is mechanically reproduced. New exact serializations, if any, "
            "are inventory only; a separately locked Phase 525B must select a consumer."
        ),
    }


def self_test() -> dict:
    toy = "ab"
    toy_parses = enumerate_complete_parses(toy)
    if not toy_parses:
        raise AssertionError("toy grammar produced no complete parse")
    parses = enumerate_complete_parses(DBBI)
    if [len(tokens) for tokens in parses] != [83, 84]:
        raise AssertionError("real DBBI parse lengths changed")
    events = picture_events()
    if len(events) != 25 or events[20]["kind"] != "fefe":
        raise AssertionError("FEFE is not event rank 21")
    result = audit(run_comparators=False)
    if not result["selection_a"]["represents_source_bytes_1_through_23_once"]:
        raise AssertionError("Selection A invariant failed")
    return {"ok": True, "checks": 4}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if args.audit:
        result = audit(run_comparators=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "output": str(args.output),
            "complete_parse_count": result["complete_parse_count"],
            "representations": len(result["representations"]),
            "new_exact": sum(r["new_to_named_exact_comparators"] for r in result["representations"]),
        }, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
