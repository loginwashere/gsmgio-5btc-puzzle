#!/usr/bin/env python3
"""Audit whether the 401/400 color-prime sums select a SalPhaseIon span.

The archived SalPhaseIon textarea is exactly one logical character followed by
one space, repeated, with no trailing space.  Therefore any prefix containing
``n`` logical characters necessarily contains ``n - 1`` spaces.  This audit
checks the specific 401/400 observation without introducing transforms:

* whether two established segment boundaries enclose exactly 401 symbols;
* the direct one-based logical and raw-source indices 401, 400, and 73;
* the channel-ranked reading (401st symbol beside the 400th space); and
* every one-sided 401-symbol window anchored at an established boundary.
"""

import argparse
from pathlib import Path

from page_structure_audit import (
    DEFAULT_HTML,
    TextareaParser,
    normalize_salphaseion,
    segment_salphaseion,
)

VALUES = (401, 400, 73)


def locate(segments, zero_based_index):
    for segment in segments:
        if segment.start <= zero_based_index < segment.end:
            return {
                "segment": segment.name,
                "local_one": zero_based_index - segment.start + 1,
            }
    raise AssertionError(f"index outside segmented stream: {zero_based_index}")


def one_based_index(stream, segments, position):
    zero_based = position - 1
    return {
        "position": position,
        "character": stream[zero_based],
        **locate(segments, zero_based),
    }


def anchored_windows(stream, segments, width):
    boundaries = sorted({0, len(stream), *(s.start for s in segments), *(s.end for s in segments)})
    windows = set()
    for boundary in boundaries:
        if boundary + width <= len(stream):
            windows.add((boundary, boundary + width, "start"))
        if boundary - width >= 0:
            windows.add((boundary - width, boundary, "end"))
    return sorted(windows)


def audit(html_path=DEFAULT_HTML):
    parser = TextareaParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    raw = parser.textareas[0]
    stream = normalize_salphaseion(raw)
    segments = segment_salphaseion(stream)
    boundaries = sorted({0, len(stream), *(s.start for s in segments), *(s.end for s in segments)})
    exact_boundary_spans = [
        (start, end)
        for start in boundaries
        for end in boundaries
        if end - start == 401
    ]

    logical_indices = {
        value: one_based_index(stream, segments, value) for value in VALUES
    }
    reverse_indices = {
        value: one_based_index(stream, segments, len(stream) - value + 1)
        for value in VALUES
    }
    raw_indices = {
        value: {
            "position": value,
            "character": raw[value - 1],
        }
        for value in VALUES
    }

    symbol_401_raw_position = 2 * 401 - 1
    space_400_raw_position = 2 * 400
    return {
        "logical_count": len(stream),
        "space_count": raw.count(" "),
        "source_count": len(raw),
        "single_space_separated": raw == " ".join(stream),
        "exact_boundary_spans": exact_boundary_spans,
        "logical_indices": logical_indices,
        "reverse_indices": reverse_indices,
        "raw_indices": raw_indices,
        "channel_ranked": {
            "space_400_raw_position": space_400_raw_position,
            "symbol_401_raw_position": symbol_401_raw_position,
            "adjacent": symbol_401_raw_position == space_400_raw_position + 1,
            "selected_character": raw[symbol_401_raw_position - 1],
            **locate(segments, 400),
        },
        "prefix_401": {
            "raw_length": len(raw[:symbol_401_raw_position]),
            "logical_length": len(stream[:401]),
            "space_count": raw[:symbol_401_raw_position].count(" "),
            "segment_lengths": {
                "dbbi": 91,
                "matrixsumlist": 104,
                "faed_prefix": 206,
            },
        },
        "anchored_windows": anchored_windows(stream, segments, 401),
    }


def self_test():
    report = audit()
    assert report["logical_count"] == 1075
    assert report["space_count"] == 1074
    assert report["source_count"] == 2149
    assert report["single_space_separated"] is True
    assert report["exact_boundary_spans"] == []
    assert report["logical_indices"][401] == {
        "position": 401,
        "character": "e",
        "segment": "faed",
        "local_one": 206,
    }
    assert report["logical_indices"][400]["character"] == "i"
    assert report["logical_indices"][73]["character"] == "e"
    assert report["reverse_indices"][401]["character"] == "a"
    assert report["reverse_indices"][400]["character"] == "f"
    assert report["reverse_indices"][73]["character"] == "0"
    assert report["raw_indices"][400]["character"] == " "
    assert report["raw_indices"][401]["character"] == "g"
    assert report["channel_ranked"] == {
        "space_400_raw_position": 800,
        "symbol_401_raw_position": 801,
        "adjacent": True,
        "selected_character": "e",
        "segment": "faed",
        "local_one": 206,
    }
    assert report["prefix_401"] == {
        "raw_length": 801,
        "logical_length": 401,
        "space_count": 400,
        "segment_lengths": {
            "dbbi": 91,
            "matrixsumlist": 104,
            "faed_prefix": 206,
        },
    }
    print("[*] self-test OK: 401/400 SalPhaseIon span audit verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=str, default=str(DEFAULT_HTML))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit(Path(args.html))

    print(
        f"[*] textarea: {report['logical_count']} symbols + "
        f"{report['space_count']} spaces = {report['source_count']} characters"
    )
    print(f"[*] established-boundary spans of length 401: {report['exact_boundary_spans']}")
    print(
        "[*] logical forward indices B=401,Y=400,F=73: "
        + "".join(report["logical_indices"][v]["character"] for v in VALUES)
    )
    print(
        "[*] logical reverse indices B=401,Y=400,F=73: "
        + "".join(report["reverse_indices"][v]["character"] for v in VALUES)
    )
    channel = report["channel_ranked"]
    print(
        f"[*] channel-ranked reading: 400th space at raw {channel['space_400_raw_position']}, "
        f"401st symbol at raw {channel['symbol_401_raw_position']} -> "
        f"{channel['selected_character']!r}, {channel['segment']} local {channel['local_one']}"
    )
    print(
        "[*] 401-symbol prefix composition: 91 DBBI + 104 matrixsumlist bits + "
        "206 FAED symbols; the 400 spaces are forced separators"
    )
    print(
        f"[*] one-sided windows anchored at an established boundary: "
        f"{len(report['anchored_windows'])}; none has both ends established"
    )
    print(
        "[*] verdict: 401 symbols necessarily contain 400 internal spaces in this "
        "format, but no established page boundaries select such a span. Direct "
        "indexing yields only EIE forward, AF0 backward, or one FAED symbol E. "
        "The observation does not recover a natural region or instruction."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
