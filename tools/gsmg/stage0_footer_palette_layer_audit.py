#!/usr/bin/env python3
"""Audit the alleged second code in the lossless Stage-0 image footer.

The reported four lines are reproduced by selecting exact RGB #383838 pixels
inside the visible banner and Bitcoin-address glyphs.  This audit then applies
the *same fixed glyph boxes* to every exact RGB layer in those two lines.  It
does not treat a visually attractive output as evidence after the fact: the
comparison family and sparsity thresholds are declared here.

The boxes are the ink extents in the archived 1048x1556 PNG.  Spaces and the
dot in ``GSMG.IO 5 BTC PUZZLE CHALLENGE`` are deliberately excluded because
the reported normalized source omits them.  Coordinates use Pillow's
left/top-inclusive, right/bottom-exclusive convention.
"""

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS  # noqa: E402
from remaining_structural_avenues_audit import material_family  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
ROOT_COPY = REPO_ROOT / "puzzle.png"
JPEG_COPY = REPO_ROOT / "doc" / "img" / "gsmg_stage0_original_telegram.jpg"

EXPECTED_SHA256 = "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
TARGET = (56, 56, 56)

BANNER = "GSMGIO5BTCPUZZLECHALLENGE"
BANNER_X = (
    (215, 245), (249, 272), (276, 316), (320, 350), (370, 378),
    (382, 416), (431, 454), (471, 497), (498, 524), (526, 552),
    (567, 591), (595, 624), (627, 652), (653, 677), (680, 700),
    (702, 723), (738, 765), (768, 795), (798, 830), (833, 853),
    (855, 875), (877, 898), (903, 932), (936, 966), (972, 993),
)
BANNER_Y = (1170, 1206)

ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
ADDRESS_X = (
    (278, 295), (297, 319), (322, 340), (342, 373), (376, 398),
    (402, 419), (420, 431), (434, 454), (455, 473), (474, 504),
    (504, 517), (519, 537), (540, 557), (559, 588), (588, 602),
    (602, 631), (631, 655), (657, 675), (676, 695), (694, 704),
    (706, 724), (725, 743), (744, 759), (762, 791), (792, 804),
    (808, 826), (827, 851), (852, 881), (881, 899), (900, 918),
    (921, 939), (942, 954), (956, 975), (977, 995),
)
ADDRESS_Y = (1393, 1427)

EXPECTED_TARGET = (
    ("GSGO5BCPUCG", "41442111214"),
    ("GMGC9g2cPBe", "21221311122"),
)

# The two #383838-selected strings themselves, plus their natural
# concatenations in both orders and both raw digit-count strings -- no
# further transform invented beyond what the extraction itself already
# produced.  Case/hash/newline forms are added by material_family(), not
# declared again here.
ORACLE_CANDIDATES = (
    "GSGO5BCPUCG",
    "GMGC9g2cPBe",
    "GSGO5BCPUCGGMGC9g2cPBe",
    "GMGC9g2cPBeGSGO5BCPUCG",
    "41442111214",
    "21221311122",
    "4144211121421221311122",
    "2122131112241442111214",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glyph_histograms(image, text, x_boxes, y_box):
    assert len(text) == len(x_boxes)
    y0, y1 = y_box
    return [
        Counter(image.crop((x0, y0, x1, y1)).getdata())
        for x0, x1 in x_boxes
    ]


def render_layer(text, histograms, color):
    counts = tuple(histogram[color] for histogram in histograms)
    selected = "".join(char for char, count in zip(text, counts) if count)
    nonzero = tuple(count for count in counts if count)
    compact_counts = "".join(str(count) for count in nonzero)
    return {
        "selected": selected,
        "counts": nonzero,
        "compact_counts": compact_counts,
        "selected_count": len(selected),
        "pixel_count": sum(nonzero),
        "max_per_glyph": max(nonzero, default=0),
    }


def audit():
    assert sha256(IMAGE_PATH) == EXPECTED_SHA256
    assert sha256(ROOT_COPY) == EXPECTED_SHA256
    image = Image.open(IMAGE_PATH).convert("RGB")
    assert image.size == (1048, 1556)

    definitions = (
        (BANNER, BANNER_X, BANNER_Y),
        (ADDRESS, ADDRESS_X, ADDRESS_Y),
    )
    histograms = tuple(
        glyph_histograms(image, text, boxes, y_box)
        for text, boxes, y_box in definitions
    )
    colors = set().union(*(set(hist) for line in histograms for hist in line))

    layers = []
    for color in sorted(colors):
        rendered = tuple(
            render_layer(text, line_histograms, color)
            for (text, _, _), line_histograms in zip(definitions, histograms)
        )
        layers.append(
            {
                "color": color,
                "lines": rendered,
                "pixel_count": sum(line["pixel_count"] for line in rendered),
                "selected_counts": tuple(line["selected_count"] for line in rendered),
                "max_per_glyph": max(line["max_per_glyph"] for line in rendered),
            }
        )

    target = next(layer for layer in layers if layer["color"] == TARGET)
    both = [layer for layer in layers if min(layer["selected_counts"]) > 0]
    sparse = [layer for layer in both if 2 <= layer["pixel_count"] <= 100]
    broad_codes = [
        layer for layer in sparse if min(layer["selected_counts"]) >= 10
    ]
    balanced_11 = [layer for layer in layers if layer["selected_counts"] == (11, 11)]
    sparse_grayscale = [
        layer for layer in sparse if len(set(layer["color"])) == 1
    ]
    g_indices = tuple(
        (line_index, glyph_index)
        for line_index, (text, _, _) in enumerate(definitions)
        for glyph_index, character in enumerate(text)
        if character == "G"
    )
    all_g_layers = []
    for layer in layers:
        color = layer["color"]
        g_counts = tuple(
            histograms[line_index][glyph_index][color]
            for line_index, glyph_index in g_indices
        )
        if all(g_counts):
            all_g_layers.append((layer, g_counts))
    intermediate_grayscale_all_g = tuple(
        (layer["color"], g_counts)
        for layer, g_counts in all_g_layers
        if len(set(layer["color"])) == 1
        and layer["color"] not in ((0, 0, 0), (245, 245, 245))
    )

    global_target = []
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) == TARGET:
                global_target.append((x, y))

    jpeg_exact_target = 0
    if JPEG_COPY.exists():
        jpeg = Image.open(JPEG_COPY).convert("RGB")
        jpeg_exact_target = sum(pixel == TARGET for pixel in jpeg.getdata())

    oracle = material_family(ORACLE_CANDIDATES, BLOBS)

    return {
        "oracle": oracle,
        "target": target,
        "layer_count": len(layers),
        "both_lines_count": len(both),
        "sparse_count": len(sparse),
        "broad_code_count": len(broad_codes),
        "balanced_11_colors": tuple(layer["color"] for layer in balanced_11),
        "sparse_grayscale": tuple(
            (layer["color"], layer["pixel_count"], layer["selected_counts"])
            for layer in sparse_grayscale
        ),
        "all_g_layer_count": len(all_g_layers),
        "intermediate_grayscale_all_g": intermediate_grayscale_all_g,
        "target_g_counts": next(
            g_counts for layer, g_counts in all_g_layers if layer["color"] == TARGET
        ),
        "target_non_g_selected_count": (
            sum(target["selected_counts"]) - len(g_indices)
        ),
        "global_target_count": len(global_target),
        "global_target_bbox": (
            min(x for x, _ in global_target),
            min(y for _, y in global_target),
            max(x for x, _ in global_target),
            max(y for _, y in global_target),
        ),
        "jpeg_exact_target_count": jpeg_exact_target,
        "layers": tuple(layers),
    }


def self_test():
    report = audit()
    target_lines = report["target"]["lines"]
    actual = tuple(
        (line["selected"], line["compact_counts"]) for line in target_lines
    )
    assert actual == EXPECTED_TARGET, actual
    assert report["target"]["pixel_count"] == 43
    assert report["target"]["selected_counts"] == (11, 11)
    assert report["global_target_count"] == 43
    assert report["global_target_bbox"] == (229, 1170, 989, 1426)
    assert report["layer_count"] == 75
    assert report["both_lines_count"] == 61
    assert report["sparse_count"] == 41
    assert report["broad_code_count"] == 11
    assert report["balanced_11_colors"] == (TARGET,)
    assert report["sparse_grayscale"] == (
        (TARGET, 43, (11, 11)),
        ((210, 210, 210), 9, (7, 1)),
    )
    assert report["all_g_layer_count"] == 35
    assert report["intermediate_grayscale_all_g"] == (
        (TARGET, (4, 4, 4, 2, 2)),
    )
    assert report["target_non_g_selected_count"] == 17
    assert report["oracle"]["candidate_count"] == len(ORACLE_CANDIDATES) == 8
    assert report["oracle"]["hits"] == []
    print("[*] self-test OK: #383838 reproduces both supplied code/count lines")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return

    report = audit()
    print(f"[*] lossless PNG SHA-256: {EXPECTED_SHA256}")
    for label, line in zip(("banner", "address"), report["target"]["lines"]):
        print(f"[*] #383838 {label}: {line['selected']} / {line['compact_counts']}")
    print(
        "[*] #383838 globally: "
        f"{report['global_target_count']} pixels, bbox={report['global_target_bbox']}"
    )
    print(
        "[*] exact-layer family: "
        f"{report['layer_count']} colors touch normalized glyphs; "
        f"{report['both_lines_count']} touch both lines; "
        f"{report['sparse_count']} touch both with 2..100 total pixels; "
        f"{report['broad_code_count']} sparse layers select >=10 glyphs per line"
    )
    print(f"[*] colors selecting exactly 11/11 glyphs: {report['balanced_11_colors']}")
    print(f"[*] sparse grayscale layers: {report['sparse_grayscale']}")
    print(
        "[*] G-shadow predicate: "
        f"{report['all_g_layer_count']} all-color layers touch every G; "
        "intermediate grayscale survivors="
        f"{report['intermediate_grayscale_all_g']}; "
        f"#383838 also selects {report['target_non_g_selected_count']} non-G glyphs"
    )
    print(f"[*] exact #383838 pixels in lossy Telegram JPEG: {report['jpeg_exact_target_count']}")
    oracle = report["oracle"]
    print(
        f"[*] oracle: {oracle['candidate_count']} candidates / "
        f"{oracle['unique_material_count']} materials / {len(oracle['hits'])} hits"
    )


if __name__ == "__main__":
    main()
