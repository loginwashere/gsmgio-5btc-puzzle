#!/usr/bin/env python3
"""Freeze and verify the archived chronology of ``favicon_small.png``.

The native-favicon shadow audit established that the sole visible grayscale
source byte is C9 and that one C9/E0 pixel composites to the rendered CE
block.  This follow-up asks the narrower provenance question: did the asset
or those properties change over the favicon's archived history?

The offline audit uses a frozen exact-match CDX row and the byte-identical
repository/mirror copies.  ``--live`` rechecks the exact CDX query and raw
Wayback payload.  It runs no decoding, credential, or blob oracle.
"""

import argparse
import hashlib
import io
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image

from native_favicon_shadow_audit import C9, FAVICON, visible_gray_report

REPO_ROOT = Path(__file__).resolve().parents[2]
MIRROR_ROOT = REPO_ROOT.parent / "gsmg-site-mirror"
MIRROR_MANIFEST = MIRROR_ROOT / "_manifest.json"
MIRROR_FAVICON = MIRROR_ROOT / "img" / "favicon_small.png"

ROUTE = "https://www.gsmg.io/img/favicon_small.png"
CDX_URL = "https://web.archive.org/cdx/search/cdx"
RAW_CAPTURE_TEMPLATE = "https://web.archive.org/web/{timestamp}id_/{route}"
PUZZLE_LAUNCH = date(2019, 4, 20)

CAPTURES = (
    {
        "timestamp": "20190428234709",
        "original": ROUTE,
        "statuscode": "200",
        "mimetype": "image/png",
        "cdx_digest": "JFMWHJ3SIABMV4CKU4BIJ3GHRLV7MCXM",
        # CDX length is the archived response-record size, not PNG payload size.
        "cdx_length": "3427",
        "payload_sha256": (
            "934f46d6a0a168a7ca2af725604d7e1dab8ee825ad0d7c682dbb252cc2be1423"
        ),
        "payload_bytes": 2677,
    },
)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def capture_date(timestamp):
    return date(
        int(timestamp[0:4]),
        int(timestamp[4:6]),
        int(timestamp[6:8]),
    )


def png_report(raw):
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    visible = [rgba for rgba in image.getdata() if rgba[3]]
    points = [
        (x, y, a)
        for y in range(image.height)
        for x in range(image.width)
        for r, g, b, a in (image.getpixel((x, y)),)
        if (r, g, b) == C9 and a
    ]
    return {
        "size": image.size,
        "visible_rgb_count": len({rgba[:3] for rgba in visible}),
        "visible_gray_bytes": tuple(
            sorted({r for r, g, b, _a in visible if r == g == b})
        ),
        "c9_total_rgb_pixels": sum(rgba[:3] == C9 for rgba in image.getdata()),
        "c9_visible_pixels": len(points),
        "c9_opaque_pixels": sum(a == 255 for _x, _y, a in points),
        "c9_distinct_visible_alphas": len({a for _x, _y, a in points}),
        "c9_visible_bbox": (
            min(x for x, _y, _a in points),
            min(y for _x, y, _a in points),
            max(x for x, _y, _a in points),
            max(y for _x, y, _a in points),
        ),
    }


def assert_payload(raw, expected=CAPTURES[0]):
    assert len(raw) == expected["payload_bytes"]
    assert sha256_bytes(raw) == expected["payload_sha256"]
    report = png_report(raw)
    assert report == {
        "size": (48, 48),
        "visible_rgb_count": 233,
        "visible_gray_bytes": (201,),
        "c9_total_rgb_pixels": 264,
        "c9_visible_pixels": 96,
        "c9_opaque_pixels": 0,
        "c9_distinct_visible_alphas": 72,
        "c9_visible_bbox": (4, 12, 42, 46),
    }
    return report


def mirror_manifest_row():
    if not MIRROR_MANIFEST.exists():
        return None
    rows = json.loads(MIRROR_MANIFEST.read_text(encoding="utf-8"))
    matches = [row for row in rows if row.get("orig") == ROUTE]
    assert len(matches) == 1
    row = matches[0]
    assert row["timestamp"] == CAPTURES[0]["timestamp"]
    assert row["mime"] == "image/png"
    assert row["local"] == "img/favicon_small.png"
    assert row["bytes"] == CAPTURES[0]["payload_bytes"]
    return row


def audit():
    expected = CAPTURES[0]
    repo_raw = FAVICON.read_bytes()
    c9 = assert_payload(repo_raw, expected)
    native = visible_gray_report(FAVICON)
    for key, value in c9.items():
        assert native[key] == value

    manifest = mirror_manifest_row()
    mirror = None
    if MIRROR_FAVICON.exists():
        mirror_raw = MIRROR_FAVICON.read_bytes()
        assert mirror_raw == repo_raw
        assert_payload(mirror_raw, expected)
        mirror = {
            "path": str(MIRROR_FAVICON),
            "byte_identical_to_repository_copy": True,
            "manifest_verified": manifest is not None,
        }

    first_date = capture_date(expected["timestamp"])
    days_after = (first_date - PUZZLE_LAUNCH).days
    assert days_after == 8
    return {
        "route": ROUTE,
        "archive": {
            "exact_200_png_capture_count": len(CAPTURES),
            "distinct_cdx_digests": len({row["cdx_digest"] for row in CAPTURES}),
            "captures": CAPTURES,
        },
        "repository_copy": {
            "path": str(FAVICON),
            "sha256": sha256_bytes(repo_raw),
            "bytes": len(repo_raw),
        },
        "mirror_copy": mirror,
        "chronology": {
            "puzzle_launch": PUZZLE_LAUNCH.isoformat(),
            "first_capture_date": first_date.isoformat(),
            "days_after_launch": days_after,
            "predates_puzzle": first_date < PUZZLE_LAUNCH,
            "pre_puzzle_capture_available": False,
            "version_comparison_possible": len(CAPTURES) > 1,
        },
        "c9_properties": c9,
        "gates": {
            "repository_copy_authenticated_to_2019_04_28": True,
            "c9_properties_verified_in_archived_payload": True,
            "pre_puzzle_branding_provenance_established": False,
            "historical_c9_evolution_testable": False,
            "new_operand_or_consumer_selected": False,
        },
        "verdict": (
            "The sole exact archived PNG authenticates the current bytes and C9 "
            "properties to 2019-04-28, eight days after launch. With no pre-puzzle "
            "or alternate-version capture, chronology cannot distinguish inherited "
            "branding from a puzzle-era export and does not promote C9 as an operand."
        ),
        "promoted": False,
    }


def fetch_bytes(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "key-seeker GSMG favicon chronology audit"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def fetch_cdx_rows():
    query = urllib.parse.urlencode(
        {
            "url": "www.gsmg.io/img/favicon_small.png",
            "matchType": "exact",
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype,digest,length",
            "filter": ["statuscode:200", "mimetype:image/png"],
        },
        doseq=True,
    )
    rows = json.loads(fetch_bytes(f"{CDX_URL}?{query}").decode("utf-8"))
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:]]


def live_audit():
    rows = fetch_cdx_rows()
    expected_rows = [
        {
            "timestamp": row["timestamp"],
            "original": row["original"],
            "statuscode": row["statuscode"],
            "mimetype": row["mimetype"],
            "digest": row["cdx_digest"],
            "length": row["cdx_length"],
        }
        for row in CAPTURES
    ]
    assert rows == expected_rows, f"Wayback CDX history changed: {rows!r}"
    expected = CAPTURES[0]
    raw_url = RAW_CAPTURE_TEMPLATE.format(
        timestamp=expected["timestamp"],
        route=ROUTE,
    )
    c9 = assert_payload(fetch_bytes(raw_url), expected)
    return {"cdx_rows": rows, "raw_url": raw_url, "c9_properties": c9}


def self_test():
    report = audit()
    assert report["archive"]["exact_200_png_capture_count"] == 1
    assert report["archive"]["distinct_cdx_digests"] == 1
    assert report["chronology"]["days_after_launch"] == 8
    assert not report["chronology"]["predates_puzzle"]
    assert not report["chronology"]["version_comparison_possible"]
    assert report["gates"]["repository_copy_authenticated_to_2019_04_28"]
    assert report["gates"]["c9_properties_verified_in_archived_payload"]
    assert not report["gates"]["pre_puzzle_branding_provenance_established"]
    assert not report["promoted"]
    print("[*] self-test OK: sole archived favicon and chronology verdict reproduce")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.live:
        report = live_audit()
        print(f"[*] live exact captures verified: {len(report['cdx_rows'])}")
        print(f"[*] raw payload verified: {report['raw_url']}")
    if not args.self_test and not args.live:
        report = audit()
        print(f"[*] captures: {report['archive']['exact_200_png_capture_count']}")
        print(f"[*] chronology: {report['chronology']}")
        print(f"[*] verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
