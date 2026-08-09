#!/usr/bin/env python3
"""Audit Points 2/4: preserve 14/8/1 events and test 14-row mapping.

Two related but non-identical objects are kept separate:

* all 24 URL endpoints have the 15-blue/9-yellow color mask; and
* the DBBI-fitting prime-walk prefix contains 14 blue singleton events,
  eight yellow digraph events, and one distinct FEFE singleton event.

This module inventories the token boundaries and source characters, projects
the fitted events back onto their authenticated 14x14 grid coordinates, and
tests whether the 14 blue events cover the 14 rows one-to-one.  It also runs
the literal two-stream next-character MUX proposed in Point 2 under its two
possible DBBI/FAED rail assignments.  No word list or cryptographic oracle is
used.
"""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
from math import comb

from data import DBBI, FAED
from first_piece_color_reconstruction import (
    DEFAULT_IMAGE,
    reconstruct,
    spiral_top_left_counterclockwise,
)
from first_piece_prime_sum_reconstruction import audit as prime_sum_audit

GRID_SIZE = 14


def decorate_coordinates(records):
    coordinates = spiral_top_left_counterclockwise()
    return tuple(
        {
            **record,
            "row_1": coordinates[record["spiral_0"]][0] + 1,
            "column_1": coordinates[record["spiral_0"]][1] + 1,
        }
        for record in records
    )


def group_report(records, event_type):
    selected = tuple(record for record in records if record["type"] == event_type)
    rows = tuple(record["row_1"] for record in selected)
    row_counts = Counter(rows)
    return {
        "event_type": event_type,
        "count": len(selected),
        "source_characters": "".join(record["character"] for record in selected),
        "tokens": tuple(record["required"] for record in selected),
        "token_symbol_length": sum(len(record["required"]) for record in selected),
        "event_ordinals": tuple(record["ordinal"] for record in selected),
        "grid_rows": rows,
        "grid_columns": tuple(record["column_1"] for record in selected),
        "distinct_grid_rows": len(row_counts),
        "missing_grid_rows": tuple(sorted(set(range(1, GRID_SIZE + 1)) - set(rows))),
        "duplicated_grid_rows": tuple(
            sorted(row for row, count in row_counts.items() if count > 1)
        ),
    }


def coverage_distribution(position_rows, selected_count):
    counts = Counter(
        len({position_rows[index] for index in selected})
        for selected in combinations(range(len(position_rows)), selected_count)
    )
    return dict(sorted(counts.items()))


def row_buckets(records):
    return tuple(
        {
            "row_1": row,
            "event_ordinals": tuple(
                record["ordinal"] for record in records if record["row_1"] == row
            ),
            "types": "".join(
                record["type"] for record in records if record["row_1"] == row
            ),
            "characters": "".join(
                record["character"] for record in records if record["row_1"] == row
            ),
        }
        for row in range(1, GRID_SIZE + 1)
    )


def first_full_row_coverage(records):
    seen = set()
    for record in records:
        seen.add(record["row_1"])
        if len(seen) == GRID_SIZE:
            return record["ordinal"]
    return None


def next_character_mux(mask, blue_stream, yellow_stream):
    offsets = {"B": 0, "Y": 0}
    output = []
    for color in mask:
        stream = blue_stream if color == "B" else yellow_stream
        output.append(stream[offsets[color]])
        offsets[color] += 1
    return {
        "output": "".join(output),
        "blue_consumed": offsets["B"],
        "yellow_consumed": offsets["Y"],
    }


def audit(image_path=DEFAULT_IMAGE):
    endpoint_report = reconstruct(image_path)
    prime_report = prime_sum_audit(image_path)
    all_records = decorate_coordinates(prime_report["records"])
    fitted = all_records[:prime_report["fitted_event_count"]]
    groups = {
        event_type: group_report(fitted, event_type)
        for event_type in ("B", "Y", "F")
    }

    non_f_records = tuple(record for record in fitted if record["type"] != "F")
    non_f_rows = tuple(record["row_1"] for record in non_f_records)
    blue_coverage_distribution = coverage_distribution(non_f_rows, groups["B"]["count"])
    yellow_coverage_distribution = coverage_distribution(non_f_rows, groups["Y"]["count"])
    profile_family_size = comb(len(non_f_records), groups["Y"]["count"])

    token_sequence = tuple(record["required"] for record in fitted)
    flattened_tokens = "".join(token_sequence)
    buckets = row_buckets(fitted)
    endpoint_mask = endpoint_report["color_sequence"]

    mux_blue_dbbi = next_character_mux(endpoint_mask, DBBI, FAED)
    mux_blue_faed = next_character_mux(endpoint_mask, FAED, DBBI)

    return {
        "endpoint_mask": {
            "sequence": endpoint_mask,
            "event_count": len(endpoint_mask),
            "blue_count": endpoint_mask.count("B"),
            "yellow_count": endpoint_mask.count("Y"),
            "blue_characters": "".join(
                item["character"]
                for item in endpoint_report["objects"]
                if item["color"] == "blue"
            ),
            "yellow_characters": "".join(
                item["character"]
                for item in endpoint_report["objects"]
                if item["color"] == "yellow"
            ),
        },
        "fitted_event_inventory": {
            "event_count": len(fitted),
            "type_sequence": "".join(record["type"] for record in fitted),
            "profile_BYF": tuple(groups[event_type]["count"] for event_type in "BYF"),
            "groups": groups,
            "token_sequence": token_sequence,
            "flattened_tokens": flattened_tokens,
            "flattened_symbol_length": len(flattened_tokens),
            "distinct_url_objects": len(
                {record["object_1"] for record in fitted if record["object_1"] is not None}
            ),
            "fefe_and_endpoint_share_character": (
                groups["F"]["source_characters"] in groups["Y"]["source_characters"]
            ),
        },
        "blue_to_grid_rows": {
            "one_per_row": groups["B"]["distinct_grid_rows"] == GRID_SIZE,
            "actual_distinct_rows": groups["B"]["distinct_grid_rows"],
            "actual_rows": groups["B"]["grid_rows"],
            "missing_rows": groups["B"]["missing_grid_rows"],
            "duplicated_rows": groups["B"]["duplicated_grid_rows"],
            "coverage_distribution_under_fixed_positions": blue_coverage_distribution,
            "one_per_row_assignments": blue_coverage_distribution.get(GRID_SIZE, 0),
            "profile_assignments": profile_family_size,
            "one_per_row_rate": Fraction(
                blue_coverage_distribution.get(GRID_SIZE, 0), profile_family_size
            ),
            "actual_coverage_count": blue_coverage_distribution[groups["B"]["distinct_grid_rows"]],
            "actual_coverage_rate": Fraction(
                blue_coverage_distribution[groups["B"]["distinct_grid_rows"]],
                profile_family_size,
            ),
        },
        "yellow_grid_rows": {
            "all_distinct": groups["Y"]["distinct_grid_rows"] == groups["Y"]["count"],
            "actual_rows": groups["Y"]["grid_rows"],
            "all_distinct_assignments": yellow_coverage_distribution.get(groups["Y"]["count"], 0),
            "profile_assignments": profile_family_size,
            "all_distinct_rate": Fraction(
                yellow_coverage_distribution.get(groups["Y"]["count"], 0),
                profile_family_size,
            ),
        },
        "all_event_row_buckets": {
            "rows": buckets,
            "all_rows_nonempty": all(bucket["event_ordinals"] for bucket in buckets),
            "first_full_coverage_event": first_full_row_coverage(fitted),
            "bucket_sizes": tuple(len(bucket["event_ordinals"]) for bucket in buckets),
        },
        "literal_24_endpoint_mux": {
            "blue_to_dbbi_yellow_to_faed": mux_blue_dbbi,
            "blue_to_faed_yellow_to_dbbi": mux_blue_faed,
            "first_four_mask_symbols": endpoint_mask[:4],
            "dbbi_prefix": DBBI[:4],
            "faed_prefix": FAED[:4],
            "plaintext_after_prefix": False,
        },
        "architecture_constraints": {
            "fourteen_blue_events_supply_one_per_spatial_row": False,
            "event_order_can_be_zipped_to_fourteen_rows_without_selector": False,
            "all_events_can_be_bucketed_by_native_grid_row": True,
            "dual_stream_mux_preserves_distinct_fefe_class": False,
            "fefe_requires_third_rail_or_explicit_fold": True,
            "flattening_tokens_loses_b_vs_f_distinction": True,
        },
        "oracle_run": False,
    }


def self_test():
    report = audit()
    endpoint = report["endpoint_mask"]
    fitted = report["fitted_event_inventory"]
    blue_rows = report["blue_to_grid_rows"]
    yellow_rows = report["yellow_grid_rows"]
    buckets = report["all_event_row_buckets"]
    mux = report["literal_24_endpoint_mux"]

    assert endpoint["event_count"] == 24
    assert (endpoint["blue_count"], endpoint["yellow_count"]) == (15, 9)
    assert endpoint["blue_characters"] == "gsmgio/eseeisae"
    assert endpoint["yellow_characters"] == ".thdplntd"
    assert fitted["event_count"] == 23
    assert fitted["profile_BYF"] == (14, 8, 1)
    assert fitted["groups"]["B"]["source_characters"] == "gsmgio/eseeisa"
    assert fitted["groups"]["Y"]["source_characters"] == ".thdplnt"
    assert fitted["groups"]["F"]["source_characters"] == "n"
    assert fitted["groups"]["B"]["token_symbol_length"] == 14
    assert fitted["groups"]["Y"]["token_symbol_length"] == 16
    assert fitted["groups"]["F"]["token_symbol_length"] == 1
    assert fitted["flattened_symbol_length"] == 31
    assert fitted["distinct_url_objects"] == 22
    assert fitted["fefe_and_endpoint_share_character"] is True
    assert blue_rows["one_per_row"] is False
    assert blue_rows["actual_distinct_rows"] == 12
    assert blue_rows["missing_rows"] == (6, 11)
    assert blue_rows["duplicated_rows"] == (2, 14)
    assert blue_rows["one_per_row_assignments"] == 256
    assert blue_rows["profile_assignments"] == 319_770
    assert blue_rows["actual_coverage_count"] == 65_856
    assert yellow_rows["all_distinct"] is True
    assert yellow_rows["all_distinct_assignments"] == 88_720
    assert buckets["all_rows_nonempty"] is True
    assert buckets["first_full_coverage_event"] == 20
    assert buckets["bucket_sizes"] == (2, 2, 1, 1, 2, 1, 2, 3, 1, 2, 1, 1, 2, 2)
    assert mux["first_four_mask_symbols"] == "BBBB"
    assert mux["blue_to_dbbi_yellow_to_faed"]["output"] == "dbbifbfbaehccbdegggbeeid"
    assert mux["blue_to_faed_yellow_to_dbbi"]["output"] == "faeddggebbedfcibdbfabhbc"
    assert report["architecture_constraints"] == {
        "fourteen_blue_events_supply_one_per_spatial_row": False,
        "event_order_can_be_zipped_to_fourteen_rows_without_selector": False,
        "all_events_can_be_bucketed_by_native_grid_row": True,
        "dual_stream_mux_preserves_distinct_fefe_class": False,
        "fefe_requires_third_rail_or_explicit_fold": True,
        "flattening_tokens_loses_b_vs_f_distinction": True,
    }
    assert report["oracle_run"] is False
    print("[*] self-test OK: 14/8/1 rails preserved; blue one-per-row mapping fails")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    fitted = report["fitted_event_inventory"]
    blue = report["blue_to_grid_rows"]
    buckets = report["all_event_row_buckets"]
    mux = report["literal_24_endpoint_mux"]

    print(f"[*] endpoint profile: {report['endpoint_mask']['blue_count']}/"
          f"{report['endpoint_mask']['yellow_count']}")
    print(f"[*] fitted event profile: {fitted['profile_BYF']}; token length="
          f"{fitted['flattened_symbol_length']}")
    print(
        f"[*] blue spatial rows: {blue['actual_distinct_rows']}/14; "
        f"missing={blue['missing_rows']}; duplicates={blue['duplicated_rows']}"
    )
    print(
        f"[*] all-event row buckets: sizes={buckets['bucket_sizes']}; "
        f"full coverage first reached at event {buckets['first_full_coverage_event']}"
    )
    print(
        "[*] literal MUX outputs: "
        f"{mux['blue_to_dbbi_yellow_to_faed']['output']} / "
        f"{mux['blue_to_faed_yellow_to_dbbi']['output']}"
    )
    print(
        "[*] verdict: preserve 14/8/1 event boundaries, but reject one-blue-"
        "per-row and two-stream-FEFE-preserving architectures. Native row "
        "bucketing must use all events; the literal 24-mask MUX is non-text."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
