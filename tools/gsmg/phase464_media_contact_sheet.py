#!/usr/bin/env python3
"""Render creator-media contact sheets for the Phase 464 manual audit."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("phase464_rotated_prime_provenance_manifest.json")
DETAIL = ROOT / "_work" / "phase464_media_detail.json"
OUTPUT = ROOT / "_work" / "phase464_contact_sheets"
COLS = 4
ROWS = 5
TILE_W = 360
TILE_H = 260
IMAGE_H = 210


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_directories() -> dict[str, tuple[Path, ...]]:
    entries = {
        row["label"]: Path(row["path"]).parent
        for row in json.loads(MANIFEST.read_text(encoding="utf-8"))["exports"]
    }
    return {
        "solver": (
            entries["solvers_overlay_2"],
            entries["solvers_overlay_1"],
            entries["solvers_base"],
        ),
        "support": (entries["support"],),
    }


def resolve(relative: str, directories: tuple[Path, ...]) -> Path:
    for directory in directories:
        candidate = directory / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def video_preview(path: Path, target: Path) -> Path | None:
    duration = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    try:
        timestamp = float(duration) * 0.5
    except ValueError:
        timestamp = 0.0
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-ss", f"{timestamp:.6f}", "-i", str(path),
            "-frames:v", "1", "-y", str(target),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return target if target.is_file() else None


def preview(path: Path, mime: str, temporary: Path) -> Image.Image:
    source = path
    if mime.startswith("video/") or path.suffix.lower() in {".gif", ".mp4", ".mov", ".webm"}:
        source = video_preview(path, temporary / f"{digest(path)}.png") or path
    try:
        with Image.open(source) as image:
            converted = ImageOps.exif_transpose(image).convert("RGB")
            converted.thumbnail((TILE_W - 12, IMAGE_H - 12), Image.Resampling.LANCZOS)
            return converted.copy()
    except Exception:
        fallback = Image.new("RGB", (TILE_W - 12, IMAGE_H - 12), "#252525")
        ImageDraw.Draw(fallback).text((12, 12), "NO RASTER PREVIEW", fill="white")
        return fallback


def main() -> None:
    records = json.loads(DETAIL.read_text(encoding="utf-8"))["records"]
    directories = export_directories()
    unique = []
    seen = set()
    for record in records:
        if record["sha256"] in seen:
            continue
        seen.add(record["sha256"])
        unique.append(record)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    with tempfile.TemporaryDirectory() as temp_name:
        temporary = Path(temp_name)
        for page_start in range(0, len(unique), COLS * ROWS):
            page_records = unique[page_start:page_start + COLS * ROWS]
            sheet = Image.new("RGB", (COLS * TILE_W, ROWS * TILE_H), "#111111")
            draw = ImageDraw.Draw(sheet)
            for index, record in enumerate(page_records):
                row, col = divmod(index, COLS)
                x, y = col * TILE_W, row * TILE_H
                path = resolve(record["relative_path"], directories[record["corpus"]])
                image = preview(path, record["mime"], temporary)
                image_x = x + (TILE_W - image.width) // 2
                image_y = y + 4 + (IMAGE_H - image.height) // 2
                sheet.paste(image, (image_x, image_y))
                label = (
                    f"{page_start + index + 1:02d} {record['corpus']}:{record['message_id']} "
                    f"{path.name[:34]}"
                )
                draw.rectangle((x, y + IMAGE_H, x + TILE_W, y + TILE_H), fill="#202020")
                draw.text((x + 6, y + IMAGE_H + 7), label, font=font, fill="white")
                draw.text(
                    (x + 6, y + IMAGE_H + 25),
                    f"{record['mime']}  {record['sha256'][:12]}",
                    font=font,
                    fill="#bdbdbd",
                )
            output = OUTPUT / f"creator_media_{page_start // (COLS * ROWS) + 1:02d}.jpg"
            sheet.save(output, quality=92)
            print(output)
    print(f"rendered {len(unique)} unique payloads from {len(records)} records")


if __name__ == "__main__":
    main()
