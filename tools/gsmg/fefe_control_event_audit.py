#!/usr/bin/env python3
"""Replay the frozen FEFE control-event menu; no oracle or language search."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from data import DBBI, FAED, VALIDATION_ANSWER
from first_piece_color_reconstruction import (
    DEFAULT_IMAGE, TARGET, reconstruct, spiral_top_left_counterclockwise,
)
from first_piece_prime_sum_reconstruction import first_primes
from phase525_dbbi_selection_a_reconstruction import enumerate_complete_parses, is_prime

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-30 - FEFE Control Event Protocol.md"
FOLLOWUP_PROTOCOL = ROOT / "doc/Brainstorms/2026-09-30 - FEFE Prime Location Followup.md"
DEFAULT_RESULT = Path(__file__).with_name("fefe_control_event_result.json")
FOLLOWUP_RESULT = Path(__file__).with_name("fefe_control_prime_location_followup.json")
MODELS = (
    "reference", "delimiter_only", "stop_after_fefe", "ignore_marker",
    "silent_prime_slot", "fefe_as_be", "swap_after", "mirror_after",
    "binary_after", "reset_width", "restart_beginning", "restart_suffix",
    "reverse_suffix", "switch_faed_same_clock", "switch_faed_fresh_clock",
    "consume_byte_once", "consume_byte_once_keep_slot", "pure_no_host",
)
COALESCE = {"consume_byte_once", "consume_byte_once_keep_slot", "pure_no_host"}
PRIMES = first_primes(30)


def picture_events(image: dict, marker_spiral: int) -> list[dict]:
    coords = spiral_top_left_counterclockwise()
    events = [
        {"spiral_0": obj["spiral_0"], "source_byte_1": obj["ordinal_1"],
         "character": obj["character"],
         "type": "B" if obj["color"] == "blue" else "Y"}
        for obj in image["objects"]
    ]
    byte, bit = divmod(marker_spiral, 8)
    if not (0 <= byte < len(TARGET)) or bit == 7 or (ord(TARGET[byte]) >> (7-bit)) & 1:
        raise ValueError("marker must be an internal zero-valued URL bit")
    events.append({"spiral_0": marker_spiral, "source_byte_1": byte + 1,
                   "character": TARGET[byte], "type": "F"})
    events.sort(key=lambda event: event["spiral_0"])
    for rank, event in enumerate(events, 1):
        row, col = coords[event["spiral_0"]]
        event.update(event_rank_1=rank, row_1=row+1, column_1=col+1)
    return events


def replay(events: list[dict], model: str, dbbi: str = DBBI, faed: str = FAED,
           answer: str = VALIDATION_ANSWER.lower()) -> dict:
    if model not in MODELS:
        raise ValueError(model)
    marker = next(event for event in events if event["type"] == "F")
    prime_rank = width = 0
    after = False
    bank = "normal"
    target = "DBBI"
    stream = dbbi
    addresses = list(range(1, len(dbbi)+1))
    origin, direction = 0, 1
    rows = []
    prefix = []
    prefix_open = True
    first_divergence = None
    seen: set[tuple[str, int]] = set()

    for event in events:
        row = dict(event)
        is_fefe = event["type"] == "F"
        if after and model in COALESCE and event["source_byte_1"] == marker["source_byte_1"]:
            if model == "consume_byte_once_keep_slot":
                prime_rank += 1
            row.update(action="suppress_same_byte_endpoint", prime_rank_after=prime_rank)
            rows.append(row)
            continue
        if is_fefe and model in {"ignore_marker", "pure_no_host"}:
            row.update(action="no_host_no_prime_slot", prime_rank_after=prime_rank)
            rows.append(row)
            after = True
            continue
        prime_rank += 1
        prime = PRIMES[prime_rank-1]
        if is_fefe and model == "silent_prime_slot":
            row.update(action="silent_prime_slot", prime_rank_after=prime_rank, prime=prime)
            rows.append(row)
            after = True
            continue
        required = "be" if event["type"] == "Y" or (is_fefe and model == "fefe_as_be") else "b"
        if after:
            if bank == "swap":
                required = "b" if event["type"] == "Y" else "be"
            elif bank == "mirror":
                required = required.translate(str.maketrans("abcdefghi", "ihgfedcba"))
            elif bank == "binary":
                required = "a" if event["type"] == "Y" else "b"
        local_start = prime + width
        local_end = local_start + len(required)-1
        actual = stream[local_start-1:local_end]
        fits = local_end <= len(stream)
        positions = addresses[local_start-1:local_end]
        collisions = [pos for pos in positions if (target, pos) in seen]
        seen.update((target, pos) for pos in positions)
        row.update(action="host", target=target, prime_rank_1=prime_rank, prime=prime,
                   width_before=width, local_start_1=local_start, local_end_1=local_end,
                   raw_start_1=origin + direction*local_start,
                   raw_positions_1=positions, required=required, actual=actual,
                   fits=fits, matches=fits and actual == required, reused_positions=collisions)
        rows.append(row)
        if prefix_open:
            if row["matches"]:
                prefix.append(row)
            else:
                first_divergence = {key: row[key] for key in (
                    "event_rank_1", "type", "source_byte_1", "target", "prime",
                    "raw_start_1", "required", "actual", "fits", "reused_positions")}
                prefix_open = False
        width += len(required)-1
        if not is_fefe:
            continue
        after = True
        if model == "stop_after_fefe":
            break
        bank = {"swap_after": "swap", "mirror_after": "mirror", "binary_after": "binary"}.get(model, "normal")
        if model == "reset_width":
            width = 0
        elif model == "restart_beginning":
            prime_rank = width = 0
        elif model in {"restart_suffix", "reverse_suffix"}:
            end = row["raw_positions_1"][-1]
            stream = dbbi[end:]
            addresses = list(range(end+1, len(dbbi)+1))
            origin, direction = end, 1
            if model == "reverse_suffix":
                stream = stream[::-1]
                addresses.reverse()
                origin, direction = len(dbbi)+1, -1
            prime_rank = width = 0
        elif model in {"switch_faed_same_clock", "switch_faed_fresh_clock"}:
            target, stream = "FAED", faed
            addresses = list(range(1, len(faed)+1))
            origin, direction = 0, 1
            if model == "switch_faed_fresh_clock":
                prime_rank = width = 0

    selected = [(row["target"], pos) for row in prefix for pos in row["raw_positions_1"]]
    answer_projection = "".join(answer[pos-1] for name, pos in selected if name == "DBBI" and pos <= len(answer))
    pieces = {}
    for label, relation in (("before", -1), ("marker", 0), ("after", 1)):
        pieces[label] = "".join(
            answer[pos-1] for row in prefix
            if (row["spiral_0"] > marker["spiral_0"]) - (row["spiral_0"] < marker["spiral_0"]) == relation
            and row["target"] == "DBBI"
            for pos in row["raw_positions_1"] if pos <= len(answer))
    prefix_keys = {(row["target"], pos) for row in prefix for pos in row["raw_positions_1"]}
    return {
        "model": model, "matching_prefix_host_events": len(prefix),
        "matching_prefix_symbols": len(selected),
        "matching_prefix_unique_symbols": len(prefix_keys),
        "matching_prefix_host_tokens": [row["required"] for row in prefix],
        "matching_prefix_prime_slots": [row["prime_rank_1"] for row in prefix],
        "matching_prefix_raw_positions": [pos for name, pos in selected if name == "DBBI"],
        "matching_prefix_has_reuse": len(prefix_keys) != len(selected),
        "first_divergence": first_divergence,
        "answer_projection_from_dbbi_coordinates": answer_projection,
        "answer_pieces": pieces,
        "skipped_or_silent_events": [row for row in rows if row["action"] != "host"],
        "rows": rows,
    }


def parse_details(tokens: tuple[str, ...]) -> dict:
    hosts = []
    raw = 1
    for logical, token in enumerate(tokens, 1):
        if is_prime(logical):
            hosts.append({"logical_position_1": logical, "raw_position_1": raw,
                          "token": token, "raw_positions_1": list(range(raw, raw+len(token)))})
        raw += len(token)
    return {"logical_length": len(tokens), "hosts": hosts, "tokens": list(tokens),
            "payload": "".join(token for index, token in enumerate(tokens, 1) if not is_prime(index)),
            "last_token": tokens[-1]}


def matching_parses(result: dict, parses: list[dict]) -> list[int]:
    if result["matching_prefix_has_reuse"]:
        return []
    matches = []
    for parse in parses:
        host_tokens = [host["token"] for host in parse["hosts"]]
        host_positions = [pos for host in parse["hosts"] for pos in host["raw_positions_1"]]
        if (result["matching_prefix_host_tokens"] == host_tokens
                and result["matching_prefix_raw_positions"] == host_positions
                and result["matching_prefix_prime_slots"] == list(range(1, len(host_tokens)+1))):
            matches.append(parse["logical_length"])
    return matches


def audit() -> dict:
    image = reconstruct(DEFAULT_IMAGE)
    marker_spiral = image["fefe"]["spiral_0"]
    events = picture_events(image, marker_spiral)
    parses = [parse_details(tokens) for tokens in enumerate_complete_parses(DBBI)]
    results = []
    for model in MODELS:
        result = replay(events, model)
        result["complete_parse_host_matches"] = matching_parses(result, parses)
        results.append(result)
    locations = []
    for byte, char in enumerate(TARGET):
        for bit in range(7):
            if (ord(char) >> (7-bit)) & 1:
                continue
            spiral = byte*8+bit
            marker_events = picture_events(image, spiral)
            record = {"spiral_0": spiral, "source_byte_1": byte+1, "bit_1": bit+1,
                      "is_actual_marker": spiral == marker_spiral, "models": {}}
            for model in ("reference", "consume_byte_once"):
                result = replay(marker_events, model)
                record["models"][model] = {
                    "matching_prefix_host_events": result["matching_prefix_host_events"],
                    "matching_prefix_symbols": result["matching_prefix_symbols"],
                    "complete_parse_host_matches": matching_parses(result, parses),
                }
            locations.append(record)
    controls = {}
    for model in ("reference", "consume_byte_once"):
        matches = [row for row in locations if row["models"][model]["complete_parse_host_matches"]]
        controls[model] = {
            "matching_location_count": len(matches),
            "matching_source_bytes": sorted({row["source_byte_1"] for row in matches}),
            "matching_locations": [{k: row[k] for k in ("spiral_0", "source_byte_1", "bit_1", "is_actual_marker")}
                                   | {"parse_lengths": row["models"][model]["complete_parse_host_matches"]}
                                   for row in matches],
            "prefix_length_histogram": dict(sorted(Counter(row["models"][model]["matching_prefix_host_events"] for row in locations).items())),
        }
    byte_groups = []
    for byte in range(1, len(TARGET)+1):
        group = [row for row in locations if row["source_byte_1"] == byte]
        if not group:
            continue
        signatures = {json.dumps(row["models"]["consume_byte_once"], sort_keys=True) for row in group}
        byte_groups.append({"source_byte_1": byte, "internal_zero_positions": [row["spiral_0"] for row in group],
                            "replacement_results_identical": len(signatures) == 1})
    return {
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "input_sha256": {
            "image": hashlib.sha256(DEFAULT_IMAGE.read_bytes()).hexdigest(),
            "DBBI": hashlib.sha256(DBBI.encode()).hexdigest(),
            "FAED": hashlib.sha256(FAED.encode()).hexdigest(),
            "answer": hashlib.sha256(VALIDATION_ANSWER.lower().encode()).hexdigest(),
        },
        "marker": image["fefe"], "event_types": "".join(event["type"] for event in events),
        "picture_events": events, "parses": parses, "model_results": results,
        "location_control_count": len(locations), "location_control_summary": controls,
        "source_byte_equivalence_classes": byte_groups, "location_controls": locations,
        "oracle_calls": 0,
    }


def self_test() -> None:
    # A synthetic consumer makes restart semantics distinguishable: FEFE at raw 6,
    # first post-control host at local prime 2 = raw 8 in the remaining suffix.
    events = [
        {"event_rank_1": 1, "type": "B", "source_byte_1": 1, "spiral_0": 7},
        {"event_rank_1": 2, "type": "Y", "source_byte_1": 2, "spiral_0": 15},
        {"event_rank_1": 3, "type": "F", "source_byte_1": 3, "spiral_0": 19},
        {"event_rank_1": 4, "type": "Y", "source_byte_1": 3, "spiral_0": 23},
        {"event_rank_1": 5, "type": "B", "source_byte_1": 4, "spiral_0": 31},
    ]
    # Initial addresses: 2='b', 3..4='be', 6='b' (prime 5 + prior width 1).
    raw = "abbeababeaba"
    suffix = replay(events, "restart_suffix", raw, raw, "abcdefghijkl")
    assert suffix["rows"][2]["raw_start_1"] == 6
    assert suffix["rows"][3]["raw_start_1"] == 8
    reverse = replay(events, "reverse_suffix", raw, raw, "abcdefghijkl")
    assert reverse["rows"][3]["raw_positions_1"] == [11, 10]
    coalesced = replay(events, "consume_byte_once", raw, raw, "abcdefghijkl")
    assert coalesced["rows"][3]["action"] == "suppress_same_byte_endpoint"
    assert coalesced["rows"][4]["prime"] == 7
    kept = replay(events, "consume_byte_once_keep_slot", raw, raw, "abcdefghijkl")
    assert kept["rows"][4]["prime"] == 11
    ignored = replay(events, "ignore_marker", raw, raw, "abcdefghijkl")
    assert ignored["rows"][3]["prime"] == 5
    silent = replay(events, "silent_prime_slot", raw, raw, "abcdefghijkl")
    assert silent["rows"][3]["prime"] == 7
    mirrored = replay(events, "mirror_after", raw, raw, "abcdefghijkl")
    assert mirrored["rows"][3]["required"] == "he"
    switched = replay(events, "switch_faed_fresh_clock", raw, raw, "abcdefghijkl")
    assert switched["rows"][3]["target"] == "FAED"
    assert switched["rows"][3]["prime"] == 2
    # Complete parses must round-trip their exact raw source.
    parses = enumerate_complete_parses(DBBI)
    assert sorted(map(len, parses)) == [83, 84]
    assert all("".join(tokens) == DBBI for tokens in parses)


def verify_report(report: dict) -> None:
    """Verify coordinates and location controls without reusing replay's state."""
    models = {row["model"]: row for row in report["model_results"]}
    for model in models.values():
        for row in model["rows"]:
            if row["action"] != "host":
                continue
            raw = DBBI if row["target"] == "DBBI" else FAED
            actual = "".join(raw[pos-1] for pos in row["raw_positions_1"])
            assert actual == row["actual"]
            assert row["matches"] == (row["fits"] and actual == row["required"])
            if row["fits"]:
                assert len(row["raw_positions_1"]) == len(row["required"])
    expected_colors = {}
    for parse in report["parses"]:
        assert "".join(parse["tokens"]) == DBBI
        hosts, mask = [], []
        offset = 0
        for logical, token in enumerate(parse["tokens"], 1):
            # Intentionally use a separate elementary prime check here.
            prime = logical >= 2 and all(logical % d for d in range(2, logical))
            if prime:
                assert token in ("b", "be")
                hosts.append(token)
                mask.extend(range(offset+1, offset+len(token)+1))
            else:
                assert len(token) == 1
            offset += len(token)
        model = models["reference" if parse["logical_length"] == 83 else "consume_byte_once"]
        assert hosts == model["matching_prefix_host_tokens"]
        assert mask == model["matching_prefix_raw_positions"]
        assert "".join(VALIDATION_ANSWER[pos-1].lower() for pos in mask) == model["answer_projection_from_dbbi_coordinates"]
        expected_colors[parse["logical_length"]] = "".join("Y" if token == "be" else "B" for token in hosts)
    # The replacement colors can also be derived from ASCII parity alone;
    # their identity does not depend on the pixel marker's within-byte bit.
    base = ["B" if ord(char) & 1 else "Y" for char in TARGET]
    for location in report["location_controls"]:
        byte = location["source_byte_1"]-1
        for name in ("reference", "consume_byte_once"):
            colors = (base[:byte] + ["B"] + base[byte:] if name == "reference"
                      else base[:byte] + ["B"] + base[byte+1:])
            matches = [length for length, hosts in expected_colors.items()
                       if "".join(colors[:len(hosts)]) == hosts]
            assert matches == location["models"][name]["complete_parse_host_matches"]
    assert all(group["replacement_results_identical"] for group in report["source_byte_equivalence_classes"])


def prime_location_followup(report: dict, result_path: Path) -> dict:
    """Apply only the two indexing conventions in the adaptive follow-up."""
    followup = {
        "source_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "followup_protocol_sha256": hashlib.sha256(FOLLOWUP_PROTOCOL.read_bytes()).hexdigest(),
        "adaptive_followup": True, "oracle_calls": 0, "index_conventions": {},
    }
    for base in (0, 1):
        eligible = [loc for loc in report["location_controls"] if is_prime(loc["spiral_0"]+base)]
        survivors = {
            model: [loc for loc in summary["matching_locations"] if is_prime(loc["spiral_0"]+base)]
            for model, summary in report["location_control_summary"].items()
        }
        followup["index_conventions"][str(base)] = {
            "prime_internal_zero_location_count": len(eligible),
            "model_survivors": survivors,
            "actual_marker_is_prime": is_prime(report["marker"]["spiral_0"]+base),
        }
    return followup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--prime-followup", action="store_true")
    args = parser.parse_args()
    self_test()
    report = audit()
    verify_report(report)
    baseline = report["model_results"][0]
    assert report["event_types"] == "BBBBYBBBYYBBBBYBBYYBFYYBY"
    assert baseline["matching_prefix_host_events"] == 23
    assert baseline["matching_prefix_symbols"] == 31
    assert baseline["answer_projection_from_dbbi_coordinates"] == "ncsyangcahiriasogaleafayanestve"
    assert baseline["complete_parse_host_matches"] == [83]
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("model | matching prefix hosts/symbols | complete parse | first divergence")
    for row in report["model_results"]:
        print(f"{row['model']} | {row['matching_prefix_host_events']}/{row['matching_prefix_symbols']}"
              f" | {row['complete_parse_host_matches']} | {row['first_divergence']}")
    print("Location controls:", json.dumps(report["location_control_summary"], sort_keys=True))
    print("Internal zero locations:", report["location_control_count"])
    print("Output:", args.output)
    if args.prime_followup:
        followup = prime_location_followup(report, args.output)
        FOLLOWUP_RESULT.write_text(json.dumps(followup, indent=2, sort_keys=True) + "\n")
        print("Adaptive prime-location follow-up:", json.dumps(followup, sort_keys=True))


if __name__ == "__main__":
    main()
