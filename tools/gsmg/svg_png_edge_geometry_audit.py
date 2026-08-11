#!/usr/bin/env python3
"""Test whether the favicon's visible C9 pixels follow served SVG contours.

The SVG and PNG use different canvases, so literal pixel-coordinate comparison
is invalid.  This audit freezes registrations fitted against only the opaque
PNG body (all C9 pixels are non-opaque), then measures C9 pixel centers against
the transformed SVG path segments.  The PNG's ordinary non-C9 silhouette edge
provides the matched distance envelope.  No color decoding or oracle is run.
"""

import argparse
import hashlib
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter

from PIL import Image

from native_favicon_shadow_audit import C9, FAVICON, FAVICON_32, SVG

SVG_SHA256 = "005da0bb8fb64abd76d6b5c203f68cb6b2b80daa99b3b6e40ba1ee3b85e8edb4"

# Direct SVG-coordinate -> PNG-coordinate registrations. They were fitted by
# intensity correlation against alpha>=250 body pixels only. C9 contributes
# zero pixels to that target because every visible C9 alpha is below 255.
REGISTRATIONS = {
    FAVICON: (
        (1.0966600179672241, 0.0024399240501224995, -6.844242572784424),
        (-0.0027242586947977543, 1.0891903638839722, -9.197216033935547),
    ),
    FAVICON_32: (
        (0.7326130270957947, 0.001444876892492175, -4.443699359893799),
        (-0.005078843794763088, 0.7200700044631958, -5.996032238006592),
    ),
}

TOKEN_RE = re.compile(r"[MLVZ]|-?(?:\d+(?:\.\d*)?|\.\d+)")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_linear_path(data):
    """Parse the M/L/V/Z-only geometry used by the two served SVG paths."""
    tokens = TOKEN_RE.findall(data)
    points = []
    command = None
    current_x = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"M", "L", "V", "Z"}:
            command = token
            index += 1
            if command == "Z":
                continue
        if command in {"M", "L"}:
            x = float(tokens[index])
            y = float(tokens[index + 1])
            points.append((x, y))
            current_x = x
            index += 2
            if command == "M":
                command = "L"
        elif command == "V":
            y = float(tokens[index])
            points.append((current_x, y))
            index += 1
        else:
            raise AssertionError(f"unsupported SVG path token near {token!r}")
    # Both source paths spell the initial coordinate again immediately before
    # Z. Keep one geometric vertex; closure is added when segments are built.
    if len(points) > 1 and points[-1] == points[0]:
        points.pop()
    return tuple(points)


def svg_paths():
    assert sha256(SVG) == SVG_SHA256
    root = ET.fromstring(SVG.read_text(encoding="utf-8"))
    rows = [
        parse_linear_path(element.attrib["d"])
        for element in root.findall("{http://www.w3.org/2000/svg}path")
    ]
    assert tuple(map(len, rows)) == (15, 4)
    return tuple(rows)


def transform_point(point, matrix):
    x, y = point
    first, second = matrix
    return (
        first[0] * x + first[1] * y + first[2],
        second[0] * x + second[1] * y + second[2],
    )


def transformed_segments(paths, matrix):
    rows = []
    for path_index, path in enumerate(paths):
        transformed = [transform_point(point, matrix) for point in path]
        for edge_index, (start, end) in enumerate(
            zip(transformed, transformed[1:] + transformed[:1])
        ):
            rows.append((path_index, edge_index, start, end))
    return tuple(rows)


def point_segment_distance(point, start, end):
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    scale = dx * dx + dy * dy
    fraction = ((px - ax) * dx + (py - ay) * dy) / scale
    fraction = min(1.0, max(0.0, fraction))
    closest = (ax + fraction * dx, ay + fraction * dy)
    return math.hypot(px - closest[0], py - closest[1])


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    previous = len(polygon) - 1
    for current, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[previous]
        if (yi > y) != (yj > y):
            crossing_x = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def body_registration_report(image, paths, matrix):
    width, height = image.size
    transformed = [
        tuple(transform_point(point, matrix) for point in path)
        for path in paths
    ]
    predicted = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if any(
            point_in_polygon((x + 0.5, y + 0.5), polygon)
            for polygon in transformed
        )
    }
    opaque = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if image.getpixel((x, y))[3] >= 250
    }
    intersection = predicted & opaque
    union = predicted | opaque
    return {
        "fit_target": "PNG alpha >= 250; contains zero C9 pixels",
        "predicted_body_pixels": len(predicted),
        "opaque_target_pixels": len(opaque),
        "intersection_pixels": len(intersection),
        "union_pixels": len(union),
        "binary_iou": len(intersection) / len(union),
        "disagreement_pixels": len(predicted ^ opaque),
    }


def neighbors(point, width, height, diagonals=False):
    x, y = point
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonals:
        offsets += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    return {
        (x + dx, y + dy)
        for dx, dy in offsets
        if 0 <= x + dx < width and 0 <= y + dy < height
    }


def edge_report(path, paths, matrix):
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    visible = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if image.getpixel((x, y))[3]
    }
    c9 = {
        point
        for point in visible
        if image.getpixel(point)[:3] == C9
    }
    non_c9 = visible - c9
    opaque = {
        point for point in visible if image.getpixel(point)[3] >= 250
    }
    assert not (c9 & opaque)

    ordinary_edge = {
        point
        for point in non_c9
        if len(neighbors(point, width, height)) < 4
        or any(neighbor not in visible for neighbor in neighbors(point, width, height))
    }
    segments = transformed_segments(paths, matrix)

    def nearest(point):
        center = (point[0] + 0.5, point[1] + 0.5)
        return min(
            (
                point_segment_distance(center, start, end),
                path_index,
                edge_index,
            )
            for path_index, edge_index, start, end in segments
        )

    c9_nearest = {point: nearest(point) for point in c9}
    ordinary_nearest = {point: nearest(point) for point in ordinary_edge}
    ordinary_envelope = max(row[0] for row in ordinary_nearest.values())
    residues = tuple(
        sorted(
            (
                point[0],
                point[1],
                distance,
            )
            for point, (distance, _path, _edge) in c9_nearest.items()
            if distance > ordinary_envelope
        )
    )
    path_counts = Counter(row[1] for row in c9_nearest.values())
    return {
        "path": str(path),
        "size": image.size,
        "registration": matrix,
        "body_registration": body_registration_report(image, paths, matrix),
        "c9_pixels": len(c9),
        "c9_adjacent_non_c9_4_neighbor": sum(
            bool(neighbors(point, width, height) & non_c9) for point in c9
        ),
        "c9_adjacent_opaque_8_neighbor": sum(
            bool(neighbors(point, width, height, diagonals=True) & opaque)
            for point in c9
        ),
        "c9_max_svg_segment_distance": max(row[0] for row in c9_nearest.values()),
        "ordinary_non_c9_edge_pixels": len(ordinary_edge),
        "ordinary_edge_max_svg_segment_distance": ordinary_envelope,
        "c9_within_ordinary_edge_envelope": len(c9) - len(residues),
        "c9_residue": residues,
        "nearest_svg_path_counts": tuple(sorted(path_counts.items())),
    }


def audit():
    paths = svg_paths()
    native = edge_report(FAVICON, paths, REGISTRATIONS[FAVICON])
    control = edge_report(FAVICON_32, paths, REGISTRATIONS[FAVICON_32])
    return {
        "svg": {
            "path": str(SVG),
            "sha256": sha256(SVG),
            "canvas": (55, 60),
            "linear_path_count": len(paths),
            "path_vertex_counts": tuple(map(len, paths)),
            "contour_segments": sum(map(len, paths)),
        },
        "native_48": native,
        "favicon_32_control": control,
        "gates": {
            "registration_independent_of_c9": True,
            "native_body_matches_svg_geometry": native["body_registration"]["binary_iou"] > 0.97,
            "all_native_c9_inside_matched_edge_envelope": not native["c9_residue"],
            "off_contour_c9_residue_found": bool(native["c9_residue"]),
            "c9_hidden_channel_supported": False,
            "decode_or_oracle_authorized": False,
        },
        "verdict": (
            "All 96 visible native C9 pixels trace the independently registered "
            "SVG contours within the PNG's own ordinary antialias-edge envelope; "
            "there is no off-contour C9 residue. Treat C9 as raster edge/export "
            "material, not a hidden spatial channel."
        ),
        "promoted": False,
    }


def self_test():
    report = audit()
    native = report["native_48"]
    control = report["favicon_32_control"]
    assert report["svg"]["path_vertex_counts"] == (15, 4)
    assert report["svg"]["contour_segments"] == 19
    assert native["body_registration"]["predicted_body_pixels"] == 1122
    assert native["body_registration"]["opaque_target_pixels"] == 1112
    assert native["body_registration"]["intersection_pixels"] == 1101
    assert native["body_registration"]["union_pixels"] == 1133
    assert native["body_registration"]["binary_iou"] > 0.971
    assert native["c9_pixels"] == 96
    assert native["c9_adjacent_non_c9_4_neighbor"] == 96
    assert native["c9_adjacent_opaque_8_neighbor"] == 96
    assert native["c9_max_svg_segment_distance"] < 1.005
    assert native["ordinary_non_c9_edge_pixels"] == 135
    assert native["ordinary_edge_max_svg_segment_distance"] > 1.321
    assert native["c9_within_ordinary_edge_envelope"] == 96
    assert native["c9_residue"] == ()
    assert native["nearest_svg_path_counts"] == ((0, 85), (1, 11))
    assert control["c9_pixels"] == 48
    assert control["c9_adjacent_non_c9_4_neighbor"] == 48
    assert control["c9_adjacent_opaque_8_neighbor"] == 48
    assert control["c9_max_svg_segment_distance"] < 1.267
    assert report["gates"]["all_native_c9_inside_matched_edge_envelope"]
    assert not report["gates"]["off_contour_c9_residue_found"]
    assert not report["gates"]["decode_or_oracle_authorized"]
    assert not report["promoted"]
    print("[*] self-test OK: SVG registration accounts for every native C9 pixel")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if not args.self_test:
        native = report["native_48"]
        print(f"[*] body registration IoU: {native['body_registration']['binary_iou']:.6f}")
        print(
            "[*] native C9 contour distance: "
            f"max={native['c9_max_svg_segment_distance']:.6f}; "
            f"ordinary edge max={native['ordinary_edge_max_svg_segment_distance']:.6f}"
        )
        print(f"[*] off-contour residue: {native['c9_residue']}")
        print(f"[*] verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
