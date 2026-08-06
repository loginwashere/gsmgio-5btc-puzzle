#!/usr/bin/env python3
"""OCR the July 12 Cosmic Duality screenshots into a separate raw transcript.

Each screenshot is split into left and right pages before OCR. Dark pages are
inverted, and every output block retains its source filename and page side.

Usage:
    python3 tools/gsmg/extract_cosmic_duality_screenshots.py \
      --tesseract /path/to/tesseract
"""

import argparse
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps, ImageStat


DEFAULT_SCREENSHOTS = Path("/home/loginwashere/Pictures/Screenshots")
DEFAULT_OUTPUT = Path("wordlists/gsmg/cosmic_duality_book_screenshot_ocr.txt")
PATTERN = "Screenshot from 2026-07-12 14-*.png"
SUPPLEMENTAL_CROPS = {
    "Screenshot from 2026-07-12 14-45-17.png": [
        ("p73 essay text", (1230, 75, 1530, 550)),
    ],
    "Screenshot from 2026-07-12 14-45-28.png": [
        ("p75 essay text", (1230, 75, 1530, 555)),
    ],
    "Screenshot from 2026-07-12 14-45-37.png": [
        ("p77 essay text", (1225, 78, 1520, 555)),
    ],
    "Screenshot from 2026-07-12 14-46-37.png": [
        ("p101 caption", (1110, 590, 1340, 980)),
    ],
    "Screenshot from 2026-07-12 14-46-42.png": [
        ("p102 caption", (145, 50, 345, 435)),
    ],
    "Screenshot from 2026-07-12 14-46-48.png": [
        ("p104 caption", (125, 585, 335, 975)),
    ],
}


def prepare_page(image, side, output, scale):
    midpoint = image.width // 2
    box = (0, 0, midpoint, image.height) if side == "left" else (
        midpoint,
        0,
        image.width,
        image.height,
    )
    page = image.crop(box).convert("L")
    page = ImageOps.autocontrast(page, cutoff=1)
    if ImageStat.Stat(page).mean[0] < 105:
        page = ImageOps.invert(page)
    if scale != 1:
        page = page.resize(
            (page.width * scale, page.height * scale),
            Image.Resampling.LANCZOS,
        )
    page.save(output)


def prepare_crop(image, box, output):
    crop = ImageOps.autocontrast(image.crop(box).convert("L"), cutoff=1)
    crop = crop.resize(
        (crop.width * 4, crop.height * 4),
        Image.Resampling.LANCZOS,
    )
    crop.save(output)


def run_tesseract(tesseract, image_path, output_base, psm):
    result = subprocess.run(
        [
            tesseract,
            str(image_path),
            str(output_base),
            "-l",
            "eng",
            "--psm",
            str(psm),
            "-c",
            "preserve_interword_spaces=1",
        ],
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    text_path = output_base.with_suffix(".txt")
    text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
    image_path.unlink(missing_ok=True)
    text_path.unlink(missing_ok=True)
    return result.returncode, result.stderr.strip(), text.strip()


def ocr_screenshot(task):
    index, image_path, tesseract, temp_root, scale = task
    blocks = []
    with Image.open(image_path) as image:
        for side in ("left", "right"):
            page_path = temp_root / f"{index:03d}-{side}.png"
            output_base = temp_root / f"{index:03d}-{side}"
            prepare_page(image, side, page_path, scale)
            returncode, stderr, text = run_tesseract(
                tesseract, page_path, output_base, psm=3
            )
            blocks.append((f"{side} page", returncode, stderr, text))
        for crop_index, (label, box) in enumerate(
            SUPPLEMENTAL_CROPS.get(image_path.name, ())
        ):
            crop_path = temp_root / f"{index:03d}-crop-{crop_index}.png"
            output_base = temp_root / f"{index:03d}-crop-{crop_index}"
            prepare_crop(image, box, crop_path)
            returncode, stderr, text = run_tesseract(
                tesseract, crop_path, output_base, psm=6
            )
            blocks.append((label, returncode, stderr, text))
    return index, image_path.name, blocks


def resolve_tesseract(value):
    if value:
        return str(Path(value).resolve())
    executable = shutil.which("tesseract")
    if executable:
        return executable
    raise SystemExit("tesseract not found; provide --tesseract")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshots", type=Path, default=DEFAULT_SCREENSHOTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tesseract")
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 1, 4))
    parser.add_argument("--scale", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()

    screenshots = sorted(args.screenshots.glob(PATTERN))
    if not screenshots:
        raise SystemExit(f"no screenshots matched {args.screenshots / PATTERN}")
    tesseract = resolve_tesseract(args.tesseract)

    with tempfile.TemporaryDirectory(prefix="cosmic-duality-ocr-") as temp_dir:
        temp_root = Path(temp_dir)
        tasks = [
            (index, path, tesseract, temp_root, args.scale)
            for index, path in enumerate(screenshots, start=1)
        ]
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            results = sorted(executor.map(ocr_screenshot, tasks))

    lines = [
        "# Cosmic Duality — raw OCR from July 12 screenshots",
        "#",
        "# Generated from 73 user-owned screenshots without modifying the curated",
        "# cosmic_duality_book_full_text.txt. OCR errors and duplicated marginal",
        "# text are preserved; source filename and page side delimit every block.",
        "",
    ]
    failures = []
    for index, filename, blocks in results:
        lines.append(f"===== SCREENSHOT {index:02d}: {filename} =====")
        for label, returncode, stderr, text in blocks:
            lines.append(f"----- {label.upper()} -----")
            lines.append(text or "[NO OCR TEXT]")
            lines.append("")
            if returncode:
                failures.append(f"{filename} {label}: {stderr}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(
        f"wrote {args.output}: {len(screenshots)} screenshots, "
        f"{len(screenshots) * 2} page images, {len(failures)} OCR failures"
    )
    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
