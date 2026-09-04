#!/usr/bin/env python3
"""Phase 464: preregistered creator-provenance audit for the rotated-prime chain.

No cipher, password oracle, or candidate generator is imported or called.
The frozen manifest controls corpus hashes, creator identity, chronology,
selector patterns, exact values, promotion gates, and prohibited work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from telegram_export_overlay_manifest import merge_exports


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name(
    "phase464_rotated_prime_provenance_manifest.json"
)
DEFAULT_RESULT = Path(__file__).with_name("phase464_result.json")
DEFAULT_MEDIA_DETAIL = ROOT / "_work" / "phase464_media_detail.json"
MANUAL_REVIEW_PATH = Path(__file__).with_name("phase464_manual_review.json")
CREATOR_ID = "user9815232"
MEDIA_FRACTIONS = (0.05, 0.25, 0.5, 0.75, 0.95)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["phase"] == 464
    assert manifest["creator_id"] == CREATOR_ID
    for entry in manifest["exports"]:
        source = Path(entry["path"])
        assert source.is_file(), source
        assert sha256_file(source) == entry["sha256"], entry["label"]
    return manifest


def plain_text(message: dict | None) -> str:
    if not message:
        return ""
    entities = message.get("text_entities")
    if entities:
        return "".join(
            entity.get("text", "") if isinstance(entity, dict) else str(entity)
            for entity in entities
        )
    value = message.get("text", "")
    if isinstance(value, str):
        return value
    return "".join(
        part if isinstance(part, str) else part.get("text", "")
        for part in value
    )


def load_corpora(manifest: dict) -> dict:
    export_map = {entry["label"]: Path(entry["path"]).parent for entry in manifest["exports"]}
    solver_messages, source_rows, overlap_rows, conflict_ids = merge_exports(
        [
            export_map["solvers_base"],
            export_map["solvers_overlay_1"],
            export_map["solvers_overlay_2"],
        ]
    )
    support_data = json.loads(
        (export_map["support"] / "result.json").read_text(encoding="utf-8")
    )
    return {
        "solver": {
            "messages": solver_messages,
            "directories": (
                export_map["solvers_overlay_2"],
                export_map["solvers_overlay_1"],
                export_map["solvers_base"],
            ),
            "source_rows": source_rows,
            "overlap_rows": overlap_rows,
            "conflict_ids": conflict_ids,
        },
        "support": {
            "messages": support_data["messages"],
            "directories": (export_map["support"],),
        },
    }


def compile_patterns(manifest: dict) -> dict[str, re.Pattern]:
    return {
        label: re.compile(expression)
        for label, expression in manifest["patterns"].items()
    }


def selector_hits(text: str, patterns: dict[str, re.Pattern]) -> dict[str, list[str]]:
    return {
        label: [match.group(0) for match in pattern.finditer(text)]
        for label, pattern in patterns.items()
        if pattern.search(text)
    }


def chronology(corpus: str, message: dict, cutoff_id: int, cutoff_unix: int) -> str:
    if corpus == "solver":
        return "independent" if message["id"] < cutoff_id else "reaction"
    return (
        "independent"
        if int(message.get("date_unixtime", 0)) < cutoff_unix
        else "reaction"
    )


def context_record(
    corpus: str,
    creator: dict,
    parent: dict | None,
    siblings: list[dict],
    matched_source: str,
    matched_text: str,
    matches: dict[str, list[str]],
    cutoff_id: int,
    cutoff_unix: int,
) -> dict:
    return {
        "corpus": corpus,
        "chronology": chronology(corpus, creator, cutoff_id, cutoff_unix),
        "matched_source": matched_source,
        "matched_selectors": matches,
        "creator": {
            "id": creator["id"],
            "date": creator.get("date"),
            "text": plain_text(creator),
            "reply_to": creator.get("reply_to_message_id"),
        },
        "parent": (
            {
                "id": parent["id"],
                "date": parent.get("date"),
                "from": parent.get("from"),
                "from_id": parent.get("from_id"),
                "text": plain_text(parent),
            }
            if parent
            else None
        ),
        "sibling_replies": [
            {
                "id": sibling["id"],
                "from": sibling.get("from"),
                "from_id": sibling.get("from_id"),
                "text": plain_text(sibling),
            }
            for sibling in siblings
        ],
        "matched_text": matched_text,
    }


def text_audit(corpora: dict, manifest: dict) -> dict:
    patterns = compile_patterns(manifest)
    cutoff_id = manifest["solver_independence_cutoff_id_exclusive"]
    solver_by_id = {message["id"]: message for message in corpora["solver"]["messages"]}
    cutoff_message = solver_by_id[cutoff_id]
    cutoff_unix = int(cutoff_message["date_unixtime"])
    records = []
    exact_records = []
    creator_counts = {}
    creator_reply_counts = {}
    base_rates = {}

    for corpus, corpus_data in corpora.items():
        messages = [m for m in corpus_data["messages"] if m.get("type") == "message"]
        by_id = {m["id"]: m for m in messages}
        children = defaultdict(list)
        for message in messages:
            parent_id = message.get("reply_to_message_id")
            if parent_id is not None:
                children[parent_id].append(message)
        creators = [m for m in messages if m.get("from_id") == CREATOR_ID]
        creator_counts[corpus] = len(creators)
        creator_reply_counts[corpus] = sum(
            m.get("reply_to_message_id") is not None for m in creators
        )

        rate_counts = Counter()
        for message in messages:
            hits = selector_hits(plain_text(message), patterns)
            rate_counts.update(hits.keys())
        base_rates[corpus] = {
            "normal_message_count": len(messages),
            "messages_matching_selector": dict(sorted(rate_counts.items())),
        }

        for creator in creators:
            parent = by_id.get(creator.get("reply_to_message_id"))
            siblings = children.get(parent["id"], []) if parent else []
            for source, text in (
                ("creator_text", plain_text(creator)),
                ("parent_of_creator_reply", plain_text(parent)),
            ):
                if not text:
                    continue
                hits = selector_hits(text, patterns)
                if not hits:
                    continue
                record = context_record(
                    corpus, creator, parent, siblings, source, text, hits,
                    cutoff_id, cutoff_unix,
                )
                records.append(record)
                if any(value.casefold() in text.casefold() for value in manifest["exact_values"]):
                    exact_records.append(record)

    return {
        "cutoff": {
            "solver_id": cutoff_id,
            "date": cutoff_message.get("date"),
            "date_unixtime": cutoff_unix,
        },
        "creator_message_counts": creator_counts,
        "creator_reply_counts": creator_reply_counts,
        "licensed_hit_count": len(records),
        "licensed_hits": records,
        "exact_reference_count": len(exact_records),
        "exact_references": exact_records,
        "base_rates": base_rates,
    }


def media_relative(message: dict) -> str | None:
    return message.get("photo") or message.get("file")


def resolve_media(relative: str, directories: tuple[Path, ...]) -> Path | None:
    for directory in directories:
        path = directory / relative
        if path.is_file():
            return path
    return None


def command_output(command: list[str], timeout: int = 30) -> str:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip()


def ocr_image(path: Path) -> str:
    return command_output(["tesseract", str(path), "stdout"], timeout=45)


def media_mime(path: Path) -> str:
    output = command_output(["file", "--brief", "--mime-type", str(path)])
    return output or (mimetypes.guess_type(path.name)[0] or "application/octet-stream")


def video_duration(path: Path) -> float | None:
    output = command_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ]
    )
    try:
        return float(output)
    except ValueError:
        return None


def ocr_video(path: Path) -> tuple[str, list[str]]:
    duration = video_duration(path)
    if not duration or duration <= 0:
        return "", []
    texts = []
    frame_digests = []
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        for index, fraction in enumerate(MEDIA_FRACTIONS):
            frame = temp / f"frame_{index}.png"
            timestamp = max(0.0, min(duration - 0.001, duration * fraction))
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-ss", f"{timestamp:.6f}",
                    "-i", str(path), "-frames:v", "1", "-y", str(frame),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=45,
                check=False,
            )
            if frame.is_file():
                frame_digests.append(sha256_file(frame))
                text = ocr_image(frame)
                if text:
                    texts.append(text)
    return "\n".join(texts), frame_digests


def extract_media_text(path: Path, mime: str) -> tuple[str, list[str], str]:
    if mime.startswith("image/"):
        return ocr_image(path), [], "image_ocr"
    if mime.startswith("video/") or path.suffix.lower() in {".gif", ".webm", ".mp4", ".mov"}:
        text, digests = ocr_video(path)
        return text, digests, "video_5frame_ocr"
    if mime.startswith("text/") and path.stat().st_size <= 2_000_000:
        return path.read_text(encoding="utf-8", errors="replace"), [], "text_read"
    if mime == "application/pdf":
        return command_output(["pdftotext", str(path), "-"], timeout=45), [], "pdf_text"
    return "", [], "unsupported_binary"


def media_audit(corpora: dict, manifest: dict, extract: bool) -> dict:
    patterns = compile_patterns(manifest)
    cutoff_id = manifest["solver_independence_cutoff_id_exclusive"]
    solver_by_id = {m["id"]: m for m in corpora["solver"]["messages"]}
    cutoff_unix = int(solver_by_id[cutoff_id]["date_unixtime"])
    records = []
    payloads = {}

    for corpus, corpus_data in corpora.items():
        for message in corpus_data["messages"]:
            relative = media_relative(message)
            if (
                message.get("type") != "message"
                or message.get("from_id") != CREATOR_ID
                or not relative
            ):
                continue
            full = resolve_media(relative, corpus_data["directories"])
            digest = sha256_file(full) if full else None
            mime = media_mime(full) if full else None
            caption = plain_text(message)
            extracted = ""
            frame_digests = []
            extraction = "not_run"
            if full and extract:
                extracted, frame_digests, extraction = extract_media_text(full, mime)
            searchable = "\n".join((relative, caption, extracted))
            hits = selector_hits(searchable, patterns)
            record = {
                "corpus": corpus,
                "message_id": message["id"],
                "date": message.get("date"),
                "chronology": chronology(corpus, message, cutoff_id, cutoff_unix),
                "relative_path": relative,
                "exists": full is not None,
                "sha256": digest,
                "size": full.stat().st_size if full else None,
                "mime": mime,
                "caption": caption,
                "extraction": extraction,
                "extracted_text": extracted,
                "frame_sha256": frame_digests,
                "matched_selectors": hits,
            }
            records.append(record)
            if digest:
                payloads.setdefault(digest, []).append((corpus, message["id"]))

    return {
        "record_count": len(records),
        "unique_payload_count": len(payloads),
        "missing_count": sum(not record["exists"] for record in records),
        "extraction_counts": dict(Counter(record["extraction"] for record in records)),
        "selector_hit_count": sum(bool(record["matched_selectors"]) for record in records),
        "selector_hits": [record for record in records if record["matched_selectors"]],
        "records": records,
    }


def automated_gate_summary(text: dict, media: dict) -> dict:
    exact_independent = [
        record for record in text["exact_references"]
        if record["chronology"] == "independent" and record["matched_source"] == "creator_text"
    ]
    exact_media = [
        record for record in media["selector_hits"]
        if record["chronology"] == "independent"
        and any(value.casefold() in (record["caption"] + "\n" + record["extracted_text"]).casefold()
                for value in ("311027", "04BEF3"))
    ]
    two_selector_candidates = []
    for record in text["licensed_hits"]:
        labels = set(record["matched_selectors"])
        if "S1_ROTATION" in labels and labels.intersection(
            {"S2_INVERSE", "S3_PRIME_PAIR", "S4_MATRIX_LIST", "S5_FRAME", "S6_PARITY", "S7_FLOWER_PREFIX"}
        ):
            two_selector_candidates.append(record)
    for record in media["selector_hits"]:
        labels = set(record["matched_selectors"])
        if "S1_ROTATION" in labels and labels.intersection(
            {"S2_INVERSE", "S3_PRIME_PAIR", "S4_MATRIX_LIST", "S5_FRAME", "S6_PARITY", "S7_FLOWER_PREFIX"}
        ):
            two_selector_candidates.append(record)
    return {
        "exact_independent_candidates": exact_independent + exact_media,
        "two_selector_candidates": two_selector_candidates,
        "consumer_witness_automatically_established": False,
        "manual_review_required": bool(exact_independent or exact_media or two_selector_candidates),
    }


def apply_manual_review(result: dict) -> None:
    """Attach a frozen review only if it exhaustively covers generated candidates."""
    if not MANUAL_REVIEW_PATH.is_file():
        return
    review = json.loads(MANUAL_REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["phase"] == 464
    expected_text = {
        f"{row['corpus']}:{row['creator']['id']}:{row['matched_source']}"
        for row in result["automated_gates"]["two_selector_candidates"]
        if "creator" in row
    }
    reviewed_text = {row["key"] for row in review["text_candidate_reviews"]}
    assert reviewed_text == expected_text
    expected_media = {
        f"{row['corpus']}:{row['message_id']}"
        for row in result["media"]["selector_hits"]
    }
    reviewed_media = {row["key"] for row in review["media_hit_reviews"]}
    assert reviewed_media == expected_media
    assert all(row["decision"] == "reject" for row in review["text_candidate_reviews"])
    assert all(row["decision"] == "reject" for row in review["media_hit_reviews"])
    assert not any(review["verdict"]["promotion_gates"].values())
    result["manual_review_sha256"] = sha256_file(MANUAL_REVIEW_PATH)
    result["manual_verdict"] = review["verdict"]


def audit(extract_media: bool = False) -> tuple[dict, dict]:
    manifest = load_manifest()
    corpora = load_corpora(manifest)
    text = text_audit(corpora, manifest)
    media = media_audit(corpora, manifest, extract=extract_media)
    result = {
        "phase": 464,
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "corpus": {
            "solver_messages": len(corpora["solver"]["messages"]),
            "support_messages": len(corpora["support"]["messages"]),
            "solver_source_rows": corpora["solver"]["source_rows"],
            "solver_overlap_rows": corpora["solver"]["overlap_rows"],
            "solver_conflict_ids": corpora["solver"]["conflict_ids"],
        },
        "text": text,
        "media": {
            key: value for key, value in media.items() if key != "records"
        },
        "automated_gates": automated_gate_summary(text, media),
        "oracle_calls": 0,
        "password_candidates": 0,
        "manual_verdict": None,
    }
    apply_manual_review(result)
    return result, media


def self_test() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    patterns = compile_patterns(manifest)
    hits = selector_hits(
        "rotate 90 degrees, invert both primes, then use an outer frame and even rail before THE FLOWER password",
        patterns,
    )
    assert {
        "S1_ROTATION", "S2_INVERSE", "S3_PRIME_PAIR", "S5_FRAME",
        "S6_PARITY", "S7_FLOWER_PREFIX", "CONSUMER",
    } <= set(hits)
    assert selector_hits("311027 and 04BEF3", patterns)["S3_PRIME_PAIR"]
    assert plain_text({"text": ["a", {"text": "b"}]}) == "ab"
    creator = {"id": 10, "date_unixtime": "100", "text": "turn"}
    assert chronology("solver", creator, 11, 200) == "independent"
    assert chronology("support", creator, 11, 200) == "independent"
    print("[*] Phase 464 synthetic self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--extract-media", action="store_true")
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--media-detail", type=Path, default=DEFAULT_MEDIA_DETAIL)
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result, media = audit(extract_media=args.extract_media)
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.media_detail.parent.mkdir(parents=True, exist_ok=True)
    args.media_detail.write_text(json.dumps(media, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "creator_message_counts": result["text"]["creator_message_counts"],
        "licensed_hit_count": result["text"]["licensed_hit_count"],
        "exact_reference_count": result["text"]["exact_reference_count"],
        "media_record_count": result["media"]["record_count"],
        "media_unique_payload_count": result["media"]["unique_payload_count"],
        "media_selector_hit_count": result["media"]["selector_hit_count"],
        "automated_two_selector_candidates": len(result["automated_gates"]["two_selector_candidates"]),
    }, indent=2))
    print(f"[*] wrote {args.result}")
    print(f"[*] wrote {args.media_detail}")


if __name__ == "__main__":
    main()

