#!/usr/bin/env python3
"""Audit historical coverage of DBBI `{b,e}` combined with 7x13/13x7.

This separates three often-conflated statements:

1. Merely reshaping DBBI row-major as 7x13 or 13x7 does not alter the stream.
   The resulting checkerboard problem is exactly the already-tested identity
   DBBI problem.
2. `matrixsum_permutation_sweep.py` tested ten sum-derived permutations for
   both shapes under both `{b,e}` orders, but only the default `top_first`
   topology.
3. `dual_ternary_sweep.py` implemented eight ordinary matrix routes for both
   shapes, but it factors raw symbols into trits; it does not decode those
   routed streams as a `{b,e}` checkerboard.

The purpose is provenance accounting, not authorization for another sweep.
"""

import argparse

from cb_common import TRANSFORM_KINDS, transpose
from data import DBBI
from dual_ternary_sweep import ROUTES, route_text
from matrixsum_permutation_sweep import all_shapes

SHAPES = ((7, 13), (13, 7))
ESCAPE_ORDERS = (("b", "e"), ("e", "b"))
TOPOLOGIES = ("top_first", "escapes_first")


def matrix_route_streams():
    streams = {}
    for rows, columns in SHAPES:
        for route in ROUTES:
            stream = route_text(DBBI, rows, columns, route)
            streams.setdefault(stream, []).append(f"{rows}x{columns}/{route}")
    return streams


def implemented_common_transform_streams():
    return {transpose(DBBI, kind): kind for kind in TRANSFORM_KINDS}


def matrixsum_permutation_streams():
    streams = {}
    for shape, permutations in all_shapes("dbbi", DBBI):
        if not shape.startswith("raw_"):
            continue
        for permutation, stream in permutations.items():
            streams.setdefault(stream, []).append(f"{shape}/{permutation}")
    return streams


def audit():
    route_streams = matrix_route_streams()
    common_streams = implemented_common_transform_streams()
    matrixsum_streams = matrixsum_permutation_streams()

    identity_labels = tuple(route_streams[DBBI])
    nonidentity = {
        stream: tuple(labels)
        for stream, labels in route_streams.items()
        if stream != DBBI
    }
    nonidentity_common_overlap = {
        tuple(labels): common_streams[stream]
        for stream, labels in nonidentity.items()
        if stream in common_streams
    }
    nonidentity_matrixsum_overlap = {
        tuple(labels): tuple(matrixsum_streams[stream])
        for stream, labels in nonidentity.items()
        if stream in matrixsum_streams
    }

    return {
        "raw_length": len(DBBI),
        "declared_matrix_route_configs": len(SHAPES) * len(ROUTES),
        "unique_matrix_route_streams": len(route_streams),
        "identity_route_labels": identity_labels,
        "natural_checkerboard_configs": len(ESCAPE_ORDERS) * len(TOPOLOGIES),
        "matrixsum_raw_shape_permutations": sum(
            len(permutations)
            for shape, permutations in all_shapes("dbbi", DBBI)
            if shape.startswith("raw_")
        ),
        "matrixsum_checkerboard_configs_top_first": sum(
            len(permutations)
            for shape, permutations in all_shapes("dbbi", DBBI)
            if shape.startswith("raw_")
        )
        * len(ESCAPE_ORDERS),
        "nonidentity_route_stream_count": len(nonidentity),
        "nonidentity_route_labels": tuple(
            labels for labels in nonidentity.values()
        ),
        "nonidentity_common_overlap": nonidentity_common_overlap,
        "nonidentity_matrixsum_overlap": nonidentity_matrixsum_overlap,
        "optional_uncovered_route_order_topology_cells": (
            len(nonidentity) * len(ESCAPE_ORDERS) * len(TOPOLOGIES)
        ),
    }


def self_test():
    report = audit()
    assert report["raw_length"] == 91
    assert report["declared_matrix_route_configs"] == 16
    assert report["unique_matrix_route_streams"] == 15
    assert report["identity_route_labels"] == ("7x13/rows", "13x7/rows")
    assert report["natural_checkerboard_configs"] == 4
    assert report["matrixsum_raw_shape_permutations"] == 20
    assert report["matrixsum_checkerboard_configs_top_first"] == 40
    assert report["nonidentity_route_stream_count"] == 14
    assert report["nonidentity_common_overlap"] == {}
    assert report["nonidentity_matrixsum_overlap"] == {}
    assert report["optional_uncovered_route_order_topology_cells"] == 56
    print(
        "[*] self-test OK: row-major 7x13 and 13x7 are both identity DBBI; "
        "14 distinct non-row-major matrix streams do not overlap the common "
        "transform or matrixsum-permutation families"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    report = audit()
    print(f"DBBI raw length: {report['raw_length']}")
    print(
        "row-major identity labels: "
        + ", ".join(report["identity_route_labels"])
    )
    print(
        "natural checkerboard structural variants already represented: "
        f"{report['natural_checkerboard_configs']} "
        "(be/eb x top_first/escapes_first)"
    )
    print(
        "matrixsum raw-shape permutations: "
        f"{report['matrixsum_raw_shape_permutations']} "
        f"({report['matrixsum_checkerboard_configs_top_first']} with be/eb; "
        "top_first only)"
    )
    print(
        "ordinary matrix routes: "
        f"{report['declared_matrix_route_configs']} declarations -> "
        f"{report['unique_matrix_route_streams']} unique streams"
    )
    print(
        "nonidentity routes absent from both checkerboard transform families: "
        f"{report['nonidentity_route_stream_count']}"
    )
    for labels in report["nonidentity_route_labels"]:
        print("  " + " = ".join(labels))
    print(
        "optional uncovered route/order/topology cells: "
        f"{report['optional_uncovered_route_order_topology_cells']}"
    )
    print(
        "verdict: the natural coordinate-derived reading ({b,e}, a 7x13 or "
        "13x7 row-major display) is already covered because both shapes leave "
        "DBBI byte-for-byte unchanged, and all four escape-order/topology "
        "variants were attacked in the calibrated monoalphabetic recovery. "
        "Fourteen non-row-major route streams were not composed with the "
        "checkerboard, but neither the coordinates nor another creator clue "
        "selects any of them; they are optional transform expansion, not a "
        "historical coverage defect."
    )


if __name__ == "__main__":
    main()
