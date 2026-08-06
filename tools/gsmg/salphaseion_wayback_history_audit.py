#!/usr/bin/env python3
"""Reproduce the archived history of the SalPhaseIon/Cosmic Duality page."""

import argparse
import gzip
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from page_structure_audit import DEFAULT_HTML

ROUTE = (
    "https://gsmg.io/"
    "89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32"
)
CDX_URL = "https://web.archive.org/cdx/search/cdx"
RAW_CAPTURE_TEMPLATE = "https://web.archive.org/web/{timestamp}id_/{route}"

CAPTURES = (
    {
        "timestamp": "20230601222752",
        "cdx_digest": "PIS4DL63U4TW723SKYUPDAVRLEUS4IBC",
        "sha256": "18a8369df1364911d5e94fcac341ef85480ff194f4500f509fbed34f19e6308b",
        "byte_count": 4556,
        "salphaseion_heading": "<h1> SalPhaseIon </H1>",
        "cosmic_heading": "<h1> Cosmic Duality </h1>",
    },
    {
        "timestamp": "20231127181947",
        "cdx_digest": "C5CE3I64NAW5SQYHXKU5RSB7BNNWCB5K",
        "sha256": "ed6c395890553a2ef3e156f91111ef0ab503951c631717cb60ab1f72858459af",
        "byte_count": 4556,
        "salphaseion_heading": "<H1> SalPhaseIon </H1>",
        "cosmic_heading": "<h1> Cosmic Duality </h1>",
    },
    {
        "timestamp": "20241123015038",
        "cdx_digest": "UWTLTBB72FEHBG5FODOFR7QHO5JKYWJN",
        "sha256": "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0",
        "byte_count": 4588,
        "salphaseion_heading": "<H1> SalPhaseIon </H1>",
        "cosmic_heading": "<h1> Cosmic Duality </h1>",
    },
    {
        "timestamp": "20251031153559",
        "cdx_digest": "SEC427LCGQGUFTQMRMHO77A4BP2F6CHO",
        "sha256": "af81c08fc26db392eec925ba22a8ba4f6abe03e5512344ca648d5cf136b30603",
        "byte_count": 5092,
        "salphaseion_heading": "<H1> SalPhaseIon </H1>",
        "cosmic_heading": "<h1> Cosmic Duality </h1>",
    },
    {
        "timestamp": "20260405154227",
        "cdx_digest": "VAK2OQL45FHW4P3E3CBJPDOHFHZTXS6M",
        "sha256": "b13cbc5c2935dc3e9ff8bf71681f2ef61317fefdce04159129877244a92a3947",
        "byte_count": 5092,
        "salphaseion_heading": "<H1> SalPhaseIon </H1>",
        "cosmic_heading": "<h1> Cosmic Duality </h1>",
    },
)

HEADING_RE = re.compile(rb"<h1>.*?</h1>", re.IGNORECASE)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def analyze(raw):
    if b"\r" in raw:
        raise AssertionError("capture unexpectedly contains CR bytes")
    if b"\t" in raw:
        raise AssertionError("capture unexpectedly contains tab bytes")
    try:
        raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise AssertionError("capture is no longer ASCII-only") from exc
    headings = [
        match.group(0).decode("ascii")
        for match in HEADING_RE.finditer(raw)
    ]
    salphaseion = next(
        heading for heading in headings if "SalPhaseIon" in heading
    )
    cosmic = next(
        heading for heading in headings if "Cosmic Duality" in heading
    )
    return {
        "sha256": sha256_bytes(raw),
        "byte_count": len(raw),
        "salphaseion_heading": salphaseion,
        "cosmic_heading": cosmic,
    }


def assert_capture(raw, expected):
    actual = analyze(raw)
    for key in (
        "sha256",
        "byte_count",
        "salphaseion_heading",
        "cosmic_heading",
    ):
        if actual[key] != expected[key]:
            raise AssertionError(
                f"{expected['timestamp']} {key}: "
                f"expected {expected[key]!r}, got {actual[key]!r}"
            )
    return actual


def assert_initial_heading_only_change(first_raw, second_raw):
    first_lines = first_raw.splitlines()
    second_lines = second_raw.splitlines()
    if len(first_lines) != len(second_lines):
        raise AssertionError("first two captures no longer have equal line counts")
    differences = [
        (index, first, second)
        for index, (first, second) in enumerate(
            zip(first_lines, second_lines),
            start=1,
        )
        if first != second
    ]
    expected = [
        (
            next(
                index
                for index, line in enumerate(first_lines, start=1)
                if line == b"<h1> SalPhaseIon </H1>"
            ),
            b"<h1> SalPhaseIon </H1>",
            b"<H1> SalPhaseIon </H1>",
        )
    ]
    if differences != expected:
        raise AssertionError(
            f"unexpected first-to-second capture diff: {differences!r}"
        )


def audit_capture_dir(capture_dir):
    capture_dir = Path(capture_dir)
    raw_by_timestamp = {}
    reports = []
    for expected in CAPTURES:
        path = capture_dir / f"{expected['timestamp']}.html"
        raw = path.read_bytes()
        raw_by_timestamp[expected["timestamp"]] = raw
        reports.append({"timestamp": expected["timestamp"], **assert_capture(raw, expected)})
    assert_initial_heading_only_change(
        raw_by_timestamp[CAPTURES[0]["timestamp"]],
        raw_by_timestamp[CAPTURES[1]["timestamp"]],
    )
    return reports


def audit_local_mirror(path=DEFAULT_HTML):
    raw = Path(path).read_bytes()
    latest = CAPTURES[-1]
    report = assert_capture(raw, latest)
    return {"path": str(path), "timestamp": latest["timestamp"], **report}


def fetch_bytes(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "key-seeker GSMG provenance audit"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    return gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw


def fetch_cdx_rows():
    query = urllib.parse.urlencode(
        {
            "url": ROUTE,
            "output": "json",
            "fl": "timestamp,digest,statuscode,mimetype",
            "filter": ["statuscode:200", "mimetype:text/html"],
            "collapse": "digest",
        },
        doseq=True,
    )
    rows = json.loads(fetch_bytes(f"{CDX_URL}?{query}").decode("utf-8"))
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:]]


def live_audit():
    rows = fetch_cdx_rows()
    expected_pairs = [
        (capture["timestamp"], capture["cdx_digest"])
        for capture in CAPTURES
    ]
    actual_pairs = [
        (row["timestamp"], row["digest"])
        for row in rows
    ]
    if actual_pairs != expected_pairs:
        raise AssertionError(
            f"Wayback CDX history changed: {actual_pairs!r}"
        )
    reports = []
    for expected in CAPTURES:
        url = RAW_CAPTURE_TEMPLATE.format(
            timestamp=expected["timestamp"],
            route=ROUTE,
        )
        reports.append(
            {
                "timestamp": expected["timestamp"],
                **assert_capture(fetch_bytes(url), expected),
            }
        )
    return reports


def self_test():
    assert len(CAPTURES) == 5
    assert len({capture["timestamp"] for capture in CAPTURES}) == 5
    assert len({capture["sha256"] for capture in CAPTURES}) == 5
    report = audit_local_mirror()
    assert report["sha256"] == CAPTURES[-1]["sha256"]
    print("[*] self-test OK: frozen capture table and local mirror verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
    if args.capture_dir:
        reports = audit_capture_dir(args.capture_dir)
        print(f"[*] local archived captures verified: {len(reports)}")
    if args.live:
        reports = live_audit()
        print(f"[*] live Wayback captures verified: {len(reports)}")
    if not any((args.self_test, args.capture_dir, args.live)):
        report = audit_local_mirror()
        print(
            f"[*] local mirror matches {report['timestamp']}: "
            f"{report['sha256']}"
        )


if __name__ == "__main__":
    main()
