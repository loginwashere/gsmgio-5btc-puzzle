#!/usr/bin/env python3
"""Exhaustive, identity-safe audit of Denis Golovkin's Telegram corpus.

This is deliberately broader than the historical keyword sweeps.  It merges
the pinned complete export with the two current overlays, selects the Telegram
account id (never the display name), preserves every message and reply edge,
and inventories every posted attachment.  Text attachments are read directly,
images are OCR'd, archives are listed and their bounded text members extracted,
and videos are sampled at fixed fractions for OCR.

The outputs are an evidence corpus, not a claim that community-authored ideas
are creator-confirmed puzzle instructions.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import re
import subprocess
import tarfile
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, ImageStat

from telegram_export_overlay_manifest import DEFAULT_EXPORTS, load_and_validate


DENIS_FROM_ID = "user398109413"
DENIS_DISPLAY_NAME = "Denis Golovkin"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "_work" / "denis_full_corpus"

TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".patch", ".diff", ".json", ".csv", ".tsv",
    ".html", ".htm", ".js", ".css", ".xml", ".yaml", ".yml", ".log",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".gif"}
ARCHIVE_SUFFIXES = {".xz", ".txz"}

TOPICS = {
    "yellow_blue_primes": (
        "yellowblue", "yellow blue", "yellow-blue", "blue prime", "yellow prime",
    ),
    "matrix_sum_list": ("matrixsumlist", "matrix sum list", "matrix", "sum list"),
    "dbbi_faed": ("dbbi", "faed"),
    "yin_yang": ("yin yang", "ying yang", "yinyang", "yingyang", "yang"),
    "architect_choice": ("architect", "archi choice", "archichoice", "choice"),
    "fefe": ("fefefe", "fefe", "zeroed out"),
    "rabbit_seed": ("rabbit", "theseedisplanted", "seed is planted", "seed"),
    "cosmic_duality": ("cosmic duality", "puzzle book", "salphation", "salvation"),
    "crypto_oracle": (
        "openssl", "aes", "password", "passphrase", "decrypt", "encrypt", "private key",
    ),
    "prime_indexing": ("prime index", "prime position", "prime number", "primes"),
    "creator_provenance": ("jrk", "creator", "author", "confirmed", "confirmation"),
    "negative_or_uncertain": (
        "no result", "nothing more", "doesn't work", "does not work", "didn't work",
        "dont know", "don't know", "not sure", "assume", "maybe", "probably",
        "i think", "i believe", "brute", "mismatch", "missmatch",
    ),
}

PUZZLE_TERMS = tuple(sorted({term for terms in TOPICS.values() for term in terms}))
URL_RE = re.compile(r"https?://[^\s<>\]\[()]+", re.I)
LONG_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_./+=:-]{16,}(?![A-Za-z0-9])")


def flatten_text(value) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else str(item.get("text", ""))
        for item in value
    )


def message_text(message: dict) -> str:
    entities = message.get("text_entities")
    if entities:
        return flatten_text(entities)
    return flatten_text(message.get("text", ""))


def merge_with_provenance(export_dirs=DEFAULT_EXPORTS):
    by_id = {}
    history = defaultdict(list)
    for export_dir in map(Path, export_dirs):
        data = load_and_validate(export_dir)
        for message in data["messages"]:
            message_id = message["id"]
            history[message_id].append(str(export_dir))
            by_id[message_id] = {**message, "_source_export": str(export_dir)}
    messages = sorted(by_id.values(), key=lambda row: (int(row["date_unixtime"]), row["id"]))
    return messages, history


def attachment_relative_path(message: dict) -> str | None:
    if message.get("photo"):
        return message["photo"]
    if message.get("file"):
        return message["file"]
    return None


def resolve_attachment(message: dict, export_dirs=DEFAULT_EXPORTS) -> Path | None:
    relative = attachment_relative_path(message)
    if not relative or relative == "(File not included. Change data exporting settings to download.)":
        return None
    preferred = Path(message["_source_export"]) / relative
    if preferred.exists():
        return preferred
    for export_dir in reversed(tuple(map(Path, export_dirs))):
        candidate = export_dir / relative
        if candidate.exists():
            return candidate
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_ocr_image(source: Path, destination: Path):
    image = Image.open(source).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    if ImageStat.Stat(image).mean[0] < 105:
        image = ImageOps.invert(image)
    image.save(destination)


def tesseract_ocr(source: Path, tmp_dir: Path, stem: str, psm: int = 6) -> dict:
    prepared = tmp_dir / f"{stem}.png"
    output_base = tmp_dir / f"{stem}_ocr"
    try:
        normalize_ocr_image(source, prepared)
    except Exception as exc:  # corrupt/unsupported image is evidence too
        return {"status": "image_error", "error": str(exc), "text": ""}
    result = subprocess.run(
        [
            "tesseract", str(prepared), str(output_base), "-l", "eng",
            "--psm", str(psm), "-c", "preserve_interword_spaces=1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    text_path = output_base.with_suffix(".txt")
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
    prepared.unlink(missing_ok=True)
    text_path.unlink(missing_ok=True)
    return {
        "status": "ok" if result.returncode == 0 else "tesseract_error",
        "error": result.stderr.strip() if result.returncode else "",
        "text": text.strip(),
    }


def ffprobe_duration(path: Path) -> float | None:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    try:
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except ValueError:
        return None


def video_ocr(path: Path, tmp_dir: Path, message_id: int) -> dict:
    duration = ffprobe_duration(path)
    if duration is None:
        return {"status": "ffprobe_error", "duration": None, "frames": []}
    fractions = (0.08, 0.27, 0.50, 0.73, 0.92)
    frames = []
    for frame_index, fraction in enumerate(fractions):
        timestamp = max(0.0, min(duration * fraction, max(0.0, duration - 0.01)))
        frame_path = tmp_dir / f"video_{message_id}_{frame_index}.png"
        result = subprocess.run(
            [
                "ffmpeg", "-v", "error", "-ss", f"{timestamp:.3f}", "-i", str(path),
                "-frames:v", "1", "-y", str(frame_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode or not frame_path.exists():
            frames.append({"fraction": fraction, "timestamp": timestamp, "status": "ffmpeg_error", "text": ""})
            continue
        ocr = tesseract_ocr(frame_path, tmp_dir, f"video_{message_id}_{frame_index}_prepared")
        frame_path.unlink(missing_ok=True)
        frames.append({"fraction": fraction, "timestamp": timestamp, **ocr})
    combined = "\n".join(frame["text"] for frame in frames if frame.get("text"))
    return {"status": "ok", "duration": duration, "frames": frames, "text": combined}


def archive_extract(path: Path, max_member_bytes: int = 2_000_000) -> dict:
    members = []
    extracted_texts = []
    try:
        with tarfile.open(path, mode="r:xz") as archive:
            for member in archive.getmembers():
                record = {"name": member.name, "size": member.size, "type": "file" if member.isfile() else "other"}
                members.append(record)
                if not member.isfile() or member.size > max_member_bytes:
                    continue
                suffix = Path(member.name).suffix.lower()
                if suffix not in TEXT_SUFFIXES:
                    continue
                handle = archive.extractfile(member)
                if handle is None:
                    continue
                content = handle.read(max_member_bytes + 1).decode("utf-8", errors="replace")
                extracted_texts.append({"name": member.name, "text": content[:max_member_bytes]})
    except Exception as exc:
        return {"status": "archive_error", "error": str(exc), "members": [], "texts": []}
    return {"status": "ok", "members": members, "texts": extracted_texts}


def strip_html_text(raw: str) -> str:
    without_scripts = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    without_tags = re.sub(r"(?s)<[^>]+>", " ", without_scripts)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def classify_topics(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(name for name, terms in TOPICS.items() if any(term in lowered for term in terms))


def extract_attachment(message: dict, export_dirs, tmp_dir: Path) -> dict:
    relative = attachment_relative_path(message)
    path = resolve_attachment(message, export_dirs)
    result = {
        "message_id": message["id"],
        "relative_path": relative,
        "file_name": message.get("file_name"),
        "media_type": message.get("media_type") or ("photo" if message.get("photo") else "file"),
        "mime_type": message.get("mime_type"),
        "available": path is not None,
        "resolved_path": str(path) if path else None,
    }
    if path is None:
        result.update({"kind": "missing", "extracted_text": "", "topics": ()})
        return result

    suffix = path.suffix.lower()
    guessed_mime = mimetypes.guess_type(path.name)[0]
    result.update({"size": path.stat().st_size, "sha256": sha256(path), "suffix": suffix, "guessed_mime": guessed_mime})
    extracted_text = ""
    if suffix in TEXT_SUFFIXES or (message.get("mime_type") or "").startswith("text/"):
        raw = path.read_text(encoding="utf-8", errors="replace")
        result["kind"] = "text"
        result["text_length"] = len(raw)
        result["raw_text"] = raw
        extracted_text = strip_html_text(raw) if suffix in {".html", ".htm"} else raw
    elif suffix in IMAGE_SUFFIXES:
        result["kind"] = "image"
        with Image.open(path) as image:
            result["dimensions"] = list(image.size)
        result["ocr"] = tesseract_ocr(path, tmp_dir, f"image_{message['id']}")
        extracted_text = result["ocr"].get("text", "")
    elif suffix in VIDEO_SUFFIXES or (message.get("mime_type") or "").startswith("video/"):
        result["kind"] = "video"
        result["video_ocr"] = video_ocr(path, tmp_dir, message["id"])
        extracted_text = result["video_ocr"].get("text", "")
    elif suffix in ARCHIVE_SUFFIXES or message.get("mime_type") == "application/x-xz":
        result["kind"] = "archive"
        result["archive"] = archive_extract(path)
        extracted_text = "\n".join(item["text"] for item in result["archive"].get("texts", []))
    else:
        result["kind"] = "binary"
    result["extracted_text"] = extracted_text
    result["topics"] = classify_topics(extracted_text)
    result["urls"] = tuple(URL_RE.findall(extracted_text))
    return result


def message_record(message: dict, all_by_id: dict, incoming_replies: dict) -> dict:
    text = message_text(message)
    parent_id = message.get("reply_to_message_id")
    parent = all_by_id.get(parent_id) if parent_id else None
    return {
        "id": message["id"],
        "date": message.get("date"),
        "date_unixtime": int(message["date_unixtime"]),
        "from": message.get("from"),
        "from_id": message.get("from_id"),
        "edited": message.get("edited"),
        "edited_unixtime": int(message["edited_unixtime"]) if message.get("edited_unixtime") else None,
        "reply_to_message_id": parent_id,
        "reply_to_from": parent.get("from") if parent else None,
        "reply_to_from_id": parent.get("from_id") if parent else None,
        "reply_to_text": message_text(parent) if parent else "",
        "incoming_reply_ids": tuple(sorted(incoming_replies.get(message["id"], ()))),
        "forwarded_from": message.get("forwarded_from"),
        "text": text,
        "text_length": len(text),
        "topics": classify_topics(text),
        "urls": tuple(URL_RE.findall(text)),
        "long_tokens": tuple(dict.fromkeys(LONG_TOKEN_RE.findall(text))),
        "has_attachment": attachment_relative_path(message) is not None,
        "attachment_path": attachment_relative_path(message),
        "source_export": message["_source_export"],
    }


def write_jsonl(path: Path, records):
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def audit(export_dirs=DEFAULT_EXPORTS, output_dir=DEFAULT_OUTPUT_DIR, extract_media=True):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    messages, history = merge_with_provenance(export_dirs)
    all_by_id = {message["id"]: message for message in messages}
    incoming_replies = defaultdict(list)
    for message in messages:
        parent_id = message.get("reply_to_message_id")
        if parent_id is not None:
            incoming_replies[parent_id].append(message["id"])

    denis_messages = [message for message in messages if message.get("from_id") == DENIS_FROM_ID]
    records = [message_record(message, all_by_id, incoming_replies) for message in denis_messages]

    attachments = []
    media_messages = [message for message in denis_messages if attachment_relative_path(message)]
    with tempfile.TemporaryDirectory(prefix="gsmg-denis-audit-") as tmp:
        tmp_dir = Path(tmp)
        for message in media_messages:
            if extract_media:
                attachments.append(extract_attachment(message, export_dirs, tmp_dir))
            else:
                path = resolve_attachment(message, export_dirs)
                attachments.append(
                    {
                        "message_id": message["id"],
                        "relative_path": attachment_relative_path(message),
                        "available": path is not None,
                        "resolved_path": str(path) if path else None,
                    }
                )

    topic_ids = {
        topic: tuple(record["id"] for record in records if topic in record["topics"])
        for topic in TOPICS
    }
    attachment_topic_ids = {
        topic: tuple(item["message_id"] for item in attachments if topic in item.get("topics", ()))
        for topic in TOPICS
    }
    yearly = Counter(datetime.fromtimestamp(record["date_unixtime"], timezone.utc).year for record in records)
    kind_counts = Counter(item.get("kind", "unextracted") for item in attachments)
    sha_groups = defaultdict(list)
    for item in attachments:
        if item.get("sha256"):
            sha_groups[item["sha256"]].append(item["message_id"])
    duplicate_groups = {digest: tuple(ids) for digest, ids in sha_groups.items() if len(ids) > 1}

    summary = {
        "account": {"from_id": DENIS_FROM_ID, "expected_display_name": DENIS_DISPLAY_NAME},
        "exports": tuple(str(Path(path)) for path in export_dirs),
        "merged_message_count": len(messages),
        "denis_message_count": len(records),
        "denis_id_min": min(record["id"] for record in records),
        "denis_id_max": max(record["id"] for record in records),
        "denis_first_date": records[0]["date"],
        "denis_last_date": records[-1]["date"],
        "display_names": dict(Counter(record["from"] for record in records)),
        "edited_count": sum(record["edited"] is not None for record in records),
        "outgoing_reply_count": sum(record["reply_to_message_id"] is not None for record in records),
        "messages_receiving_replies": sum(bool(record["incoming_reply_ids"]) for record in records),
        "incoming_reply_edge_count": sum(len(record["incoming_reply_ids"]) for record in records),
        "attachment_message_count": len(attachments),
        "attachment_available_count": sum(item["available"] for item in attachments),
        "attachment_kind_counts": dict(kind_counts),
        "attachment_unique_sha256_count": len(sha_groups),
        "attachment_duplicate_groups": duplicate_groups,
        "messages_per_year": dict(sorted(yearly.items())),
        "topic_counts": {topic: len(ids) for topic, ids in topic_ids.items()},
        "topic_message_ids": topic_ids,
        "attachment_topic_counts": {topic: len(ids) for topic, ids in attachment_topic_ids.items()},
        "attachment_topic_message_ids": attachment_topic_ids,
        "messages_with_urls": sum(bool(record["urls"]) for record in records),
        "messages_with_long_tokens": sum(bool(record["long_tokens"]) for record in records),
        "messages_with_export_overlap": sum(len(history[record["id"]]) > 1 for record in records),
    }

    write_jsonl(output_dir / "messages.jsonl", records)
    (output_dir / "attachments.json").write_text(
        json.dumps(attachments, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return records, attachments, summary


def self_test():
    assert flatten_text(["a", {"type": "plain", "text": "b"}]) == "ab"
    assert classify_topics("Maybe DBBI uses yellow-blue prime positions") == (
        "yellow_blue_primes", "dbbi_faed", "prime_indexing", "negative_or_uncertain"
    )
    assert strip_html_text("<b>A&amp;B</b><script>bad()</script>") == "A&B"
    synthetic = {
        "id": 2,
        "date": "2026-01-01T00:00:00",
        "date_unixtime": "1767225600",
        "from": DENIS_DISPLAY_NAME,
        "from_id": DENIS_FROM_ID,
        "text": "DBBI",
        "reply_to_message_id": 1,
        "_source_export": "/tmp/example",
    }
    parent = {"id": 1, "from": "Other", "from_id": "user1", "text": "hello"}
    record = message_record(synthetic, {1: parent, 2: synthetic}, {2: [3]})
    assert record["reply_to_text"] == "hello"
    assert record["incoming_reply_ids"] == (3,)
    assert record["topics"] == ("dbbi_faed",)
    print("[*] self-test OK: identity-safe message, topic, HTML, and reply extraction")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", action="append", type=Path, dest="export_dirs")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-media-extraction", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    export_dirs = args.export_dirs or DEFAULT_EXPORTS
    records, attachments, summary = audit(
        export_dirs=export_dirs,
        output_dir=args.output_dir,
        extract_media=not args.skip_media_extraction,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[*] wrote {len(records)} messages and {len(attachments)} attachments to {args.output_dir}")


if __name__ == "__main__":
    main()
