#!/usr/bin/env python3
"""Regenerate local preview copies for the Stage 2 media shortlist.

VS Code's Markdown preview sandboxes both resource loading (images) and link
navigation to the workspace, so `doc/GSMG_TELEGRAM_MEDIA_SHORTLIST.md` cannot
embed or link to files directly from the Telegram export folder (outside the
repo) -- neither `<img src="file://...">` nor a plain `[open](file://...)`
link to it works in the preview. This copies every shortlisted file (all
~3MB of it) into two gitignored local directories so both work:

* `doc/telegram_shortlist_thumbnails/<id>.jpg` -- a small resized JPEG, for
  every image-type item, used as the inline thumbnail;
* `doc/telegram_shortlist_fullsize/<id><original extension>` -- an exact copy
  of the original file, for every item regardless of type, used as the
  "open" link target.
"""

import argparse
import shutil
from pathlib import Path

from PIL import Image

from telegram_export_anchor_media_triage import audit as triage_audit
from telegram_export_manifest import DEFAULT_EXPORT_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_THUMBNAIL_DIR = (
    Path(__file__).resolve().parents[2] / "doc" / "telegram_shortlist_thumbnails"
)
DEFAULT_FULLSIZE_DIR = (
    Path(__file__).resolve().parents[2] / "doc" / "telegram_shortlist_fullsize"
)
DEFAULT_WIDTH = 180


def generate(
    export_dir=DEFAULT_EXPORT_DIR,
    thumbnail_dir=DEFAULT_THUMBNAIL_DIR,
    fullsize_dir=DEFAULT_FULLSIZE_DIR,
    width=DEFAULT_WIDTH,
):
    report = triage_audit(export_dir)
    thumbnail_dir = Path(thumbnail_dir)
    fullsize_dir = Path(fullsize_dir)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    fullsize_dir.mkdir(parents=True, exist_ok=True)

    thumbnails, fullsize_copies, skipped_missing = [], [], []
    for item in report["shortlist"]:
        source = Path(export_dir) / item["media_path"]
        if not source.exists():
            skipped_missing.append(item["id"])
            continue

        fullsize_path = fullsize_dir / f"{item['id']}{source.suffix.lower()}"
        shutil.copyfile(source, fullsize_path)
        fullsize_copies.append(item["id"])

        if source.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        image = Image.open(source).convert("RGB")
        source_width, source_height = image.size
        target_height = max(1, round(source_height * width / source_width))
        image = image.resize((width, target_height), Image.LANCZOS)
        thumbnail_path = thumbnail_dir / f"{item['id']}.jpg"
        image.save(thumbnail_path, "JPEG", quality=80)
        thumbnails.append(item["id"])

    return {
        "thumbnail_dir": thumbnail_dir,
        "fullsize_dir": fullsize_dir,
        "thumbnails": tuple(thumbnails),
        "fullsize_copies": tuple(fullsize_copies),
        "skipped_missing": tuple(skipped_missing),
    }


def self_test():
    report = generate()
    assert len(report["thumbnails"]) == 40, len(report["thumbnails"])
    assert len(report["fullsize_copies"]) == 50, len(report["fullsize_copies"])
    assert not report["skipped_missing"]
    for message_id in report["thumbnails"]:
        thumbnail = report["thumbnail_dir"] / f"{message_id}.jpg"
        assert thumbnail.exists(), thumbnail
        with Image.open(thumbnail) as image:
            assert image.width == DEFAULT_WIDTH
    for message_id in report["fullsize_copies"]:
        matches = list(report["fullsize_dir"].glob(f"{message_id}.*"))
        assert len(matches) == 1, (message_id, matches)
    print(
        f"[*] self-test OK: 40 image thumbnails regenerated at width={DEFAULT_WIDTH}, "
        "50 full-size copies made for the 'open' links, none missing"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--thumbnail-dir", type=Path, default=DEFAULT_THUMBNAIL_DIR)
    parser.add_argument("--fullsize-dir", type=Path, default=DEFAULT_FULLSIZE_DIR)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    report = generate(args.export_dir, args.thumbnail_dir, args.fullsize_dir, args.width)
    print(f"[*] thumbnails written to {report['thumbnail_dir']}: {len(report['thumbnails'])}")
    print(f"[*] full-size copies written to {report['fullsize_dir']}: {len(report['fullsize_copies'])}")
    if report["skipped_missing"]:
        print(f"[*] WARNING skipped (file missing on disk): {report['skipped_missing']}")


if __name__ == "__main__":
    main()
