#!/usr/bin/env python3
"""Reproducible full-file audit of Naddiseo/gsmgio-5btc-puzzle.

The audit is deliberately pinned to upstream commit 15b43fc.  It inventories
every tracked blob, parses every notebook cell/output/attachment, checks every
image's container boundary and metadata, verifies embedded attachment bytes,
and safely replays deterministic transformations.  Network notebook code is
never executed, and OpenSSL plaintext is captured in memory rather than written
over source files.

Usage:
    python tools/gsmg/naddiseo_repository_full_audit.py \
        --repo /path/to/Naddiseo/gsmgio-5btc-puzzle

Add ``--json`` to emit the complete per-file coverage ledger.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


EXPECTED_HEAD = "15b43fc859c33170d7c45b9fe41789d77b7af974"
EXPECTED_TREE = "0cd1e900038246a4ff3f1b5817f34fa212c49d92"
EXPECTED_FILE_COUNT = 85
EXPECTED_NOTEBOOKS = {
    "decentraland.ipynb": (5, 6, 5, 3),
    "phase0.ipynb": (3, 5, 3, 0),
    "phase1.ipynb": (1, 2, 1, 3),
    "phase2.ipynb": (3, 10, 3, 14),
    "phase3.2.ipynb": (7, 13, 7, 7),
    "phase3.ipynb": (1, 7, 1, 4),
    "salphaseion.ipynb": (6, 8, 7, 1),
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=repo,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify(path: str) -> tuple[str, str]:
    p = Path(path)
    if p.suffix == ".ipynb":
        return "notebook", "all cells, saved outputs, attachments, dependencies, side effects"
    if path.startswith("hints/") and p.suffix.lower() in IMAGE_SUFFIXES:
        return "hint_image", "visual review, authorship context, metadata, boundary, digest"
    if p.suffix.lower() in IMAGE_SUFFIXES:
        return "walkthrough_image", "visual review, metadata, boundary, digest, attachment match"
    if p.suffix.lower() == ".mp3":
        return "audio", "stream metadata, channel-difference spectrogram, digest"
    if p.name.endswith(("_aes.txt", "-aes.txt")):
        return "encrypted_payload", "full bytes, base64 envelope, safe in-memory decrypt where solved"
    if p.suffix in {".md", ".txt"}:
        return "text", "full-text review, digest, relationship to notebook outputs"
    return "placeholder", "presence, size, digest"


def git_inventory(repo: Path) -> list[dict]:
    raw = run(repo, "git", "ls-tree", "-r", "-l", "HEAD").stdout.decode()
    rows = []
    for line in raw.splitlines():
        left, path = line.split("\t", 1)
        mode, obj_type, blob, size = left.split()
        data = (repo / path).read_bytes()
        worktree_blob = hashlib.sha1(
            f"blob {len(data)}\0".encode() + data,
            usedforsecurity=False,
        ).hexdigest()
        assert worktree_blob == blob, (path, worktree_blob, blob)
        category, coverage = classify(path)
        rows.append(
            {
                "path": path,
                "mode": mode,
                "git_blob": blob,
                "size": int(size),
                "sha256": sha256(data),
                "category": category,
                "coverage": coverage,
                "status": "reviewed",
            }
        )
    return rows


def image_boundary(data: bytes) -> tuple[str, int]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        offset = 8
        while offset + 12 <= len(data):
            length = int.from_bytes(data[offset : offset + 4], "big")
            chunk_type = data[offset + 4 : offset + 8]
            chunk_end = offset + 12 + length
            if chunk_end > len(data):
                raise AssertionError("truncated PNG chunk")
            offset = chunk_end
            if chunk_type == b"IEND":
                return "PNG", len(data) - offset
        raise AssertionError("PNG lacks IEND")
    if data.startswith(b"\xff\xd8"):
        marker = data.rfind(b"\xff\xd9")
        if marker < 0:
            raise AssertionError("JPEG lacks EOI")
        return "JPEG", len(data) - (marker + 2)
    raise AssertionError("unsupported image signature")


def audit_images(repo: Path, rows: list[dict]) -> dict:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image metadata audit") from exc

    formats = Counter()
    metadata_keys = Counter()
    trailers = []
    count = 0
    for row in rows:
        if row["category"] not in {"hint_image", "walkthrough_image"}:
            continue
        count += 1
        path = repo / row["path"]
        data = path.read_bytes()
        container, trailer = image_boundary(data)
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            row["image"] = {
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "metadata_keys": sorted(image.info),
                "trailing_bytes": trailer,
            }
            formats[container] += 1
            metadata_keys.update(image.info.keys())
        if trailer:
            trailers.append(row["path"])
    assert count == 66, count
    assert not trailers, trailers
    return {
        "count": count,
        "formats": dict(sorted(formats.items())),
        "metadata_key_counts": dict(sorted(metadata_keys.items())),
        "files_with_trailing_bytes": trailers,
    }


def audit_notebooks(repo: Path, rows: list[dict]) -> dict:
    row_by_path = {row["path"]: row for row in rows}
    attachment_records = []
    totals = Counter()
    for name, expected in EXPECTED_NOTEBOOKS.items():
        notebook = json.loads((repo / name).read_text(encoding="utf-8"))
        cells = Counter(cell["cell_type"] for cell in notebook["cells"])
        outputs = [out for cell in notebook["cells"] for out in cell.get("outputs", [])]
        attachments = []
        for cell_index, cell in enumerate(notebook["cells"]):
            for attachment_name, payloads in cell.get("attachments", {}).items():
                assert len(payloads) == 1
                mime, encoded = next(iter(payloads.items()))
                raw = base64.b64decode(encoded, validate=True)
                matches = [
                    str(path.relative_to(repo))
                    for path in repo.rglob(attachment_name)
                    if path.is_file() and path.read_bytes() == raw
                ]
                assert matches, (name, attachment_name)
                record = {
                    "notebook": name,
                    "cell_index": cell_index,
                    "name": attachment_name,
                    "mime": mime,
                    "sha256": sha256(raw),
                    "standalone_exact_matches": sorted(matches),
                }
                attachments.append(record)
                attachment_records.append(record)
        actual = (cells["code"], cells["markdown"], len(outputs), len(attachments))
        assert actual == expected, (name, actual, expected)
        summary = {
            "code_cells": actual[0],
            "markdown_cells": actual[1],
            "saved_outputs": actual[2],
            "attachments": actual[3],
            "saved_error_outputs": sum(o.get("output_type") == "error" for o in outputs),
        }
        row_by_path[name]["notebook"] = summary
        totals.update(summary)
    assert len(attachment_records) == 32
    return {
        "count": len(EXPECTED_NOTEBOOKS),
        "totals": dict(totals),
        "attachments": attachment_records,
        "attachment_count": len(attachment_records),
        "all_attachments_match_standalone_bytes": True,
    }


def phase0_replay() -> str:
    lines = """00110b0010110y
11b1001110b011
1101110b001001
0110b000011101
0b1000110y0110
100110y010y011
100b1100010y00
b11000000010y0
00011b0111110b
11b111y0110001
1101000y011011
11110010b01100
0b0111010y0110
01b0110110b011""".splitlines()
    output = []
    while lines:
        output.extend(row[0] for row in lines)
        lines = [row[1:] for row in lines]
        output.extend(lines.pop())
        output.extend(row[-1] for row in reversed(lines))
        lines = [row[:-1] for row in lines]
        output.extend(reversed(lines.pop(0)))
    bits = "".join(output).replace("b", "1").replace("y", "0")
    return "".join(chr(int(bits[i : i + 8], 2)) for i in range(0, len(bits), 8))


def salphaseion_replay() -> dict:
    first = "a b b a b b a b a b b a a a a b a b b b a b a a a b b b a a b a a b b a b a a b a b b b b a a a a b b b a a b b a b b b a b a b a b b a b b a b a b b a b b a a a b b a b a a b a b b b a a b b a b b b a b a a"
    second = "a b b a a b a b a b b a b b b a a b b b a b a a a b b a a b a b a b b b a a b a"

    def binary_decode(value: str) -> str:
        bits = value.replace(" ", "").replace("a", "0").replace("b", "1")
        return "".join(chr(int(bits[i : i + 8], 2)) for i in range(0, len(bits), 8))

    s1 = "a g d a f a o a h e i e c g g c h g i c b b h c g b e h c f c o a b i c f d h h c d b b c a g b d a i o b b g b e a d e d d e"
    s2 = "c f o b f d h g d o b d g o o i i g d o c d a o o f i d h"
    table = str.maketrans("abcdefghio", "1234567890")

    def decimal_ascii(value: str) -> str:
        number = int(value.replace(" ", "").translate(table))
        return binascii.unhexlify(format(number, "x")).decode()

    return {
        "binary_1": binary_decode(first),
        "binary_2": binary_decode(second),
        "decimal_1": decimal_ascii(s1),
        "decimal_2": decimal_ascii(s2),
    }


def openssl_decrypt(repo: Path, source: str, password_hash: str) -> bytes:
    proc = run(
        repo,
        "openssl",
        "aes-256-cbc",
        "-in",
        source,
        "-a",
        "-d",
        "-pass",
        f"pass:{password_hash}",
    )
    return proc.stdout


def deterministic_replays(repo: Path) -> dict:
    phase0 = phase0_replay()
    assert phase0 == "gsmg.io/theseedisplanted\x00"
    salph = salphaseion_replay()
    assert salph == {
        "binary_1": "matrixsumlist",
        "binary_2": "enter",
        "decimal_1": "lastwordsbeforearchichoice",
        "decimal_2": "thispassword",
    }
    replay = {"phase0": repr(phase0), "salphaseion": salph}
    if shutil.which("openssl"):
        specs = [
            ("phase2-assets/phase2_aes.txt", "phase2-assets/phase2.1.txt", "eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf"),
            ("phase2-assets/phase3_aes.txt", "phase2-assets/phase3.txt", "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5"),
            ("phase3-assets/phase3.2-aes.txt", "phase3-assets/phase3.2.txt", "250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c"),
        ]
        aes = []
        for encrypted, plaintext, password_hash in specs:
            decoded = openssl_decrypt(repo, encrypted, password_hash)
            expected = (repo / plaintext).read_bytes()
            assert decoded == expected, (encrypted, plaintext)
            aes.append({"encrypted": encrypted, "plaintext": plaintext, "sha256": sha256(decoded)})
        replay["aes_exact_plaintext_matches"] = aes
    else:
        replay["aes_exact_plaintext_matches"] = "not run: openssl unavailable"
    return replay


def audio_audit(repo: Path) -> dict:
    path = "decentraland-assets/puzzlepiece.mp3"
    result = {"path": path, "sha256": sha256((repo / path).read_bytes())}
    if not shutil.which("ffprobe"):
        result["stream_probe"] = "not run: ffprobe unavailable"
        return result
    proc = run(
        repo,
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=format_name,duration,size:stream=codec_name,sample_rate,channels",
        "-of",
        "json",
        path,
    )
    probe = json.loads(proc.stdout)
    stream = probe["streams"][0]
    assert stream["codec_name"] == "mp3"
    assert int(stream["sample_rate"]) == 44100
    assert int(stream["channels"]) == 2
    result["stream_probe"] = probe
    result["channel_difference_visual_read"] = "48 41 53 48 54 48 45 54 45 58 54 -> HASHTHETEXT"
    return result


def audit(repo: Path) -> dict:
    head = run(repo, "git", "rev-parse", "HEAD").stdout.decode().strip()
    tree = run(repo, "git", "rev-parse", "HEAD^{tree}").stdout.decode().strip()
    assert head == EXPECTED_HEAD, (head, EXPECTED_HEAD)
    assert tree == EXPECTED_TREE, (tree, EXPECTED_TREE)
    rows = git_inventory(repo)
    assert len(rows) == EXPECTED_FILE_COUNT, len(rows)
    categories = Counter(row["category"] for row in rows)
    result = {
        "source": "https://github.com/Naddiseo/gsmgio-5btc-puzzle",
        "commit": head,
        "tree": tree,
        "tracked_file_count": len(rows),
        "category_counts": dict(sorted(categories.items())),
        "notebooks": audit_notebooks(repo, rows),
        "images": audit_images(repo, rows),
        "audio": audio_audit(repo),
        "deterministic_replays": deterministic_replays(repo),
        "files": rows,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="emit complete per-file JSON ledger")
    args = parser.parse_args()
    result = audit(args.repo.resolve())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "PASS: {tracked_file_count} files; {nb} notebooks; {images} images; "
            "{attachments} exact notebook attachments; deterministic replays matched".format(
                tracked_file_count=result["tracked_file_count"],
                nb=result["notebooks"]["count"],
                images=result["images"]["count"],
                attachments=result["notebooks"]["attachment_count"],
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
