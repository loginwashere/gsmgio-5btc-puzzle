#!/usr/bin/env python3
"""Stage 3: OCR/read the Stage 2 shortlist only (not all ~4,900 media files).

Reuses the preprocessing already validated in
`extract_cosmic_duality_screenshots.py` (grayscale, autocontrast, invert if
the mean brightness is low) rather than a fresh implementation. Text-type
attachments (.py/.txt/.md) are read directly -- they are already text, not
images, so running an OCR engine on them would be pointless indirection.
MIDI/video attachments are recorded as out of scope for this pass, not
silently skipped.
"""

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageOps, ImageStat

from telegram_export_anchor_media_triage import audit as triage_audit
from telegram_export_manifest import DEFAULT_EXPORT_DIR

TEXT_EXTENSIONS = {".py", ".txt", ".md"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
OUT_OF_SCOPE_EXTENSIONS = {".mid", ".mp4"}

DEFAULT_TESSERACT = "tesseract"
DEFAULT_TMP_DIR = Path("/tmp/claude-1000/-home-loginwashere-projects-key-seeker/4dac29c7-ae9f-4faa-81ed-c975dfa68248/scratchpad/telegram_ocr")


def classify(path):
    suffix = Path(path).suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return "text"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in OUT_OF_SCOPE_EXTENSIONS:
        return "out_of_scope"
    return "unknown"


def read_text_file(export_dir, media_path):
    full_path = Path(export_dir) / media_path
    try:
        return full_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None


def preprocess(image_path, tmp_path):
    image = Image.open(image_path).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    if ImageStat.Stat(image).mean[0] < 105:
        image = ImageOps.invert(image)
    image.save(tmp_path)


def ocr_image(export_dir, media_path, message_id, tesseract, tmp_dir, psm=6):
    source_path = Path(export_dir) / media_path
    if not source_path.exists():
        return None
    tmp_dir.mkdir(parents=True, exist_ok=True)
    prepped = tmp_dir / f"{message_id}_prepped.png"
    output_base = tmp_dir / f"{message_id}_out"
    preprocess(source_path, prepped)
    result = subprocess.run(
        [tesseract, str(prepped), str(output_base), "-l", "eng", "--psm", str(psm),
         "-c", "preserve_interword_spaces=1"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    text_path = output_base.with_suffix(".txt")
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    prepped.unlink(missing_ok=True)
    text_path.unlink(missing_ok=True)
    if result.returncode != 0:
        return f"<tesseract error: {result.stderr.strip()}>"
    return text.strip()


def run(export_dir=DEFAULT_EXPORT_DIR, tesseract=DEFAULT_TESSERACT, tmp_dir=DEFAULT_TMP_DIR):
    report = triage_audit(export_dir)
    results = []
    for item in report["shortlist"]:
        kind = classify(item["media_path"])
        entry = {"id": item["id"], "date": item["date"], "from": item["from"],
                  "media_path": item["media_path"], "caption": item["caption"], "kind": kind}
        if kind == "text":
            entry["content"] = read_text_file(export_dir, item["media_path"])
        elif kind == "image":
            entry["ocr_text"] = ocr_image(export_dir, item["media_path"], item["id"], tesseract, tmp_dir)
        else:
            entry["note"] = "out of scope for this pass (midi/video, not image/text)"
        results.append(entry)
    return results


def self_test():
    assert classify("files/foo.py") == "text"
    assert classify("photos/photo_1@x.jpg") == "image"
    assert classify("files/song.mid") == "out_of_scope"
    assert classify("video_files/x.mp4") == "out_of_scope"
    print("[*] self-test OK: classification of text/image/out-of-scope extensions verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--tesseract", default=DEFAULT_TESSERACT)
    parser.add_argument("--tmp-dir", type=Path, default=DEFAULT_TMP_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    results = run(args.export_dir, args.tesseract, args.tmp_dir)
    by_kind = {}
    for entry in results:
        by_kind.setdefault(entry["kind"], 0)
        by_kind[entry["kind"]] += 1
    print(f"[*] processed {len(results)} shortlisted items: {by_kind}")
    for entry in results:
        print(f"\n=== id={entry['id']} {entry['date']} {entry['from']!r} kind={entry['kind']} {entry['media_path']}")
        print(f"    caption: {entry['caption'][:150]!r}")
        if entry["kind"] == "text":
            print(f"    content ({len(entry['content'] or '')} chars): {(entry['content'] or '')[:500]!r}")
        elif entry["kind"] == "image":
            ocr = entry["ocr_text"] or ""
            print(f"    ocr ({len(ocr)} chars): {ocr[:500]!r}")
        else:
            print(f"    {entry['note']}")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(results, handle, ensure_ascii=False, indent=2)
        print(f"\n[*] full results written to {args.json_out}")


if __name__ == "__main__":
    main()
