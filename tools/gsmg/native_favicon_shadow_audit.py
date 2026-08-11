#!/usr/bin/env python3
"""Audit the native GSMG favicon shadow selected in the Phase-186 thread.

The community annotator who supplied the later ``#383838``/G-shadow claim
explicitly pointed solvers at ``favicon_small.png``.  This module freezes that
provenance and tests the narrow image claim suggested by it:

* inventory native repeated-gray RGB values in the 48x48 favicon;
* map its sole visible gray, C9C9C9, through the authenticated Stage-0
  alpha-composition and identify the source of the rendered CECECE block;
* compare the PNG with the served SVG and the larger branding raster;
* record, but do not promote, the finite alpha-LSB streams on the C9 edge.

It runs no password, cipher, blob, or address oracle.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from telegram_export_manifest import DEFAULT_EXPORT_DIR, plain_text  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
ICON_DIR = REPO_ROOT / "doc" / "img" / "icons"
FAVICON = ICON_DIR / "favicon_small.png"
FAVICON_32 = ICON_DIR / "favicon.png"
LOGO = ICON_DIR / "logo_medium.png"
SVG = ICON_DIR / "favicon_small.svg"
NIGHT_SVG = ICON_DIR / "favicon_small_night.svg"
STAGE0 = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"

EXPECTED_SHA256 = {
    FAVICON: "934f46d6a0a168a7ca2af725604d7e1dab8ee825ad0d7c682dbb252cc2be1423",
    FAVICON_32: "d493af9e0caaf05a3707ba3f97d92b56813cb183c94c4a63e313edfaf36c362a",
    LOGO: "eb360eeff3501b94e40d8ffc4364e795016fd39acc47a64870b727c119ec3a47",
    SVG: "005da0bb8fb64abd76d6b5c203f68cb6b2b80daa99b3b6e40ba1ee3b85e8edb4",
    NIGHT_SVG: "630b54224f29871fdd0df3b0e1b5a01b46fed5b00af002e17bb8a7f18a4ddf71",
}

C9 = (201, 201, 201)
CE = (206, 206, 206)
BACKGROUND = (245, 245, 245, 255)
RENDER_ORIGIN = (33, 1112)
RENDER_SIZE = (144, 144)

MESSAGE_EXPECTATIONS = {
    47334: ("john_s4d", "favicon_small.png"),
    47335: ("VoVaM", "БИНГО"),
    47336: ("VoVaM", "You're getting close"),
    47355: ("Varholy Viktor", "2017/07/13-01:06:39"),
    47356: ("VoVaM", "Take a fucking look"),
    47357: ("VoVaM", "This is the clue"),
    47367: ("VoVaM", "FEFEFE"),
    47368: ("VoVaM", "beyond FEFEFE"),
}

GLYPH_BOXES = {
    "G1": (26, 552, 78, 613),
    "S": (155, 552, 200, 613),
    "M": (280, 552, 340, 613),
    "G2": (419, 552, 471, 613),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_gray_report(path):
    image = Image.open(path).convert("RGBA")
    visible = [(r, g, b, a) for r, g, b, a in image.getdata() if a]
    gray_bytes = tuple(sorted({r for r, g, b, _a in visible if r == g == b}))
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
        "visible_gray_bytes": gray_bytes,
        "c9_total_rgb_pixels": sum(
            rgba[:3] == C9 for rgba in image.getdata()
        ),
        "c9_visible_pixels": len(points),
        "c9_opaque_pixels": sum(a == 255 for _x, _y, a in points),
        "c9_distinct_visible_alphas": len({a for _x, _y, a in points}),
        "c9_visible_bbox": (
            min(x for x, _y, _a in points),
            min(y for _x, y, _a in points),
            max(x for x, _y, _a in points),
            max(y for _x, y, _a in points),
        ) if points else None,
        "c9_points": tuple(points),
    }


def pack_low_bits(values, width):
    bits = []
    for value in values:
        bits.extend((value >> bit) & 1 for bit in range(width - 1, -1, -1))
    output = bytearray()
    for offset in range(0, len(bits) - 7, 8):
        value = 0
        for bit in bits[offset:offset + 8]:
            value = (value << 1) | bit
        output.append(value)
    return bytes(output)


def alpha_stream_report(points):
    alphas = bytes(alpha for _x, _y, alpha in points)
    streams = {}
    for width in (1, 2):
        packed = pack_low_bits(alphas, width)
        streams[f"lsb{width}"] = {
            "length": len(packed),
            "hex": packed.hex(),
            "printable_count": sum(32 <= value < 127 for value in packed),
        }
    return {
        "selection_order": "native row-major C9 pixels with alpha > 0",
        "alpha_count": len(alphas),
        "alpha_sha256": hashlib.sha256(alphas).hexdigest(),
        "alpha_printable_count": sum(32 <= value < 127 for value in alphas),
        "streams": streams,
        "recognized_signature": None,
    }


def composite_provenance():
    source = Image.open(FAVICON).convert("RGBA")
    ce_sources = []
    output_grays = set()
    for y in range(source.height):
        for x in range(source.width):
            pixel = source.getpixel((x, y))
            one = Image.new("RGBA", (1, 1), BACKGROUND)
            one.alpha_composite(Image.new("RGBA", (1, 1), pixel))
            output = one.convert("RGB").getpixel((0, 0))
            if output[0] == output[1] == output[2]:
                output_grays.add(output[0])
            if output == CE:
                ce_sources.append((x, y, pixel))

    enlarged = source.resize(RENDER_SIZE, Image.Resampling.NEAREST)
    reconstructed = Image.new("RGBA", RENDER_SIZE, BACKGROUND)
    reconstructed.alpha_composite(enlarged)
    reconstructed = reconstructed.convert("RGB")
    x0, y0 = RENDER_ORIGIN
    actual = Image.open(STAGE0).convert("RGB").crop(
        (x0, y0, x0 + RENDER_SIZE[0], y0 + RENDER_SIZE[1])
    )
    differences = [
        abs(expected - observed)
        for expected_pixel, actual_pixel in zip(reconstructed.getdata(), actual.getdata())
        for expected, observed in zip(expected_pixel, actual_pixel)
    ]
    return {
        "background_rgb": BACKGROUND[:3],
        "ce_source_pixels": tuple(ce_sources),
        "native_c9_to_rendered_gray_count": len(output_grays),
        "native_c9_rendered_gray_range": (min(output_grays), max(output_grays)),
        "reconstructed_ce_pixels": sum(pixel == CE for pixel in reconstructed.getdata()),
        "actual_stage0_ce_pixels": sum(pixel == CE for pixel in actual.getdata()),
        "maximum_stage0_channel_difference": max(differences),
    }


def svg_report(path):
    text = path.read_text(encoding="utf-8")
    colors = tuple(sorted(set(re.findall(r"#[0-9A-Fa-f]{6}", text))))
    return {
        "size_literal": re.search(r'<svg width="(\d+)" height="(\d+)"', text).groups(),
        "literal_colors": colors,
        "has_c9": "#C9C9C9" in text.upper(),
        "has_filter_or_shadow": bool(re.search(r"filter|shadow", text, re.I)),
        "path_count": len(re.findall(r"<path\b", text)),
    }


def logo_control():
    image = Image.open(LOGO).convert("RGBA")
    histograms = {
        label: Counter(image.crop(box).getdata())
        for label, box in GLYPH_BOXES.items()
    }
    common_g = {
        rgba for rgba in histograms["G1"]
        if rgba[3] and rgba in histograms["G2"]
    }
    g_only = {
        rgba for rgba in common_g
        if not histograms["S"][rgba] and not histograms["M"][rgba]
    }
    g_only_equal = {
        rgba for rgba in g_only
        if histograms["G1"][rgba] == histograms["G2"][rgba]
    }
    g1 = list(image.crop(GLYPH_BOXES["G1"]).getdata())
    g2 = list(image.crop(GLYPH_BOXES["G2"]).getdata())
    c9_counts = {
        label: {
            "visible": sum(rgba[:3] == C9 and rgba[3] > 0 for rgba in histogram.elements()),
            "opaque": histogram[(201, 201, 201, 255)],
        }
        for label, histogram in histograms.items()
    }
    return {
        "visible_rgba_color_counts": {
            label: len({rgba for rgba in histogram if rgba[3]})
            for label, histogram in histograms.items()
        },
        "shared_g_rgba_layers": len(common_g),
        "g_only_rgba_layers": len(g_only),
        "g_only_equal_count_rgba_layers": len(g_only_equal),
        "g_crop_differing_pixels": sum(left != right for left, right in zip(g1, g2)),
        "c9_glyph_counts": c9_counts,
    }


def message_provenance(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    if not Path(export_path).exists():
        return {"verified": False, "reason": "export unavailable"}
    payload = json.loads(Path(export_path).read_text(encoding="utf-8"))
    messages = {row.get("id"): row for row in payload["messages"]}
    rows = []
    for message_id, (expected_author, fragment) in MESSAGE_EXPECTATIONS.items():
        row = messages[message_id]
        text = plain_text(row)
        assert row.get("from") == expected_author
        assert fragment in text
        rows.append({
            "message_id": message_id,
            "author": row.get("from"),
            "reply_to": row.get("reply_to_message_id"),
            "text": text,
        })
    assert messages[47357].get("reply_to_message_id") == 47355
    return {
        "verified": True,
        "rows": tuple(rows),
        "annotator": "VoVaM",
        "provenance_class": "community annotator, not creator",
        "xmp_timestamp_correction": (
            "2017/07/13-01:06:39 is part of the Adobe XMP Core toolkit "
            "version string, not an asset creation timestamp"
        ),
    }


def audit(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    for path, expected in EXPECTED_SHA256.items():
        assert sha256(path) == expected, path
    favicon = visible_gray_report(FAVICON)
    favicon32 = visible_gray_report(FAVICON_32)
    logo = visible_gray_report(LOGO)
    composite = composite_provenance()
    return {
        "provenance": message_provenance(export_path),
        "favicon": {**favicon, "c9_points": None},
        "favicon32_control": {**favicon32, "c9_points": None},
        "logo_control_gray": {**logo, "c9_points": None},
        "composite": composite,
        "svg": svg_report(SVG),
        "night_svg": svg_report(NIGHT_SVG),
        "logo_glyph_control": logo_control(),
        "alpha_stream": alpha_stream_report(favicon["c9_points"]),
        "gates": {
            "community_annotator_selects_native_favicon": True,
            "native_favicon_has_unique_visible_gray_byte": favicon["visible_gray_bytes"] == (201,),
            "rendered_ce_has_unique_native_source_pixel": len(composite["ce_source_pixels"]) == 1,
            "logo_g_checksum_distinctive": False,
            "alpha_or_lsb_consumer_selected": False,
            "credential_oracle_authorized": False,
        },
        "promoted": False,
    }


def self_test(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    report = audit(export_path)
    favicon = report["favicon"]
    assert favicon["size"] == (48, 48)
    assert favicon["visible_rgb_count"] == 233
    assert favicon["visible_gray_bytes"] == (201,)
    assert favicon["c9_total_rgb_pixels"] == 264
    assert favicon["c9_visible_pixels"] == 96
    assert favicon["c9_opaque_pixels"] == 0
    assert favicon["c9_distinct_visible_alphas"] == 72
    assert favicon["c9_visible_bbox"] == (4, 12, 42, 46)
    assert report["composite"]["ce_source_pixels"] == (
        (27, 26, (201, 201, 201, 224)),
    )
    assert report["composite"]["native_c9_to_rendered_gray_count"] == 37
    assert report["composite"]["native_c9_rendered_gray_range"] == (204, 245)
    assert report["composite"]["reconstructed_ce_pixels"] == 9
    assert report["composite"]["actual_stage0_ce_pixels"] == 9
    assert report["composite"]["maximum_stage0_channel_difference"] == 1
    assert report["alpha_stream"]["alpha_sha256"] == (
        "3a885335d394a1b2186316b329d371d40caaea4ca4a8f19bfaaeac12cf3e9f1e"
    )
    assert report["alpha_stream"]["streams"]["lsb1"]["hex"] == (
        "a1639090a78be66e3d74f366"
    )
    assert report["alpha_stream"]["streams"]["lsb2"]["hex"] == (
        "e603162f6102e12a6ebf48c5fcb69edca7dbbf12f5071e16"
    )
    assert report["svg"]["literal_colors"] == (
        "#0B285C", "#2F529D", "#3374E4", "#679EFD",
    )
    assert not report["svg"]["has_c9"]
    assert not report["svg"]["has_filter_or_shadow"]
    glyphs = report["logo_glyph_control"]
    assert glyphs["shared_g_rgba_layers"] == 116
    assert glyphs["g_only_rgba_layers"] == 42
    assert glyphs["g_only_equal_count_rgba_layers"] == 36
    assert glyphs["g_crop_differing_pixels"] == 688
    assert not report["gates"]["logo_g_checksum_distinctive"]
    assert not report["gates"]["alpha_or_lsb_consumer_selected"]
    assert not report["promoted"]
    print("[*] self-test OK: native C9 shadow, CE provenance, and controls reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_DIR / "result.json")
    args = parser.parse_args()
    if args.self_test:
        self_test(args.export)
        return
    report = audit(args.export)
    print(f"[*] message provenance verified: {report['provenance']['verified']}")
    print(f"[*] favicon visible grays: {report['favicon']['visible_gray_bytes']}")
    print(
        "[*] native C9: "
        f"{report['favicon']['c9_visible_pixels']} visible pixels / "
        f"{report['favicon']['c9_distinct_visible_alphas']} alpha values"
    )
    print(f"[*] CE native source: {report['composite']['ce_source_pixels']}")
    print(f"[*] alpha streams: {report['alpha_stream']['streams']}")
    print(f"[*] logo G-layer control: {report['logo_glyph_control']}")
    print("[*] verdict: structural provenance only; no consumer or oracle authorized")


if __name__ == "__main__":
    main()
