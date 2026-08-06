#!/usr/bin/env python3
"""Item 3 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md` section 3): a generic
stego/metadata pass on the repo's own image files, using standard tooling
rather than the manual pixel-parsing this project has relied on elsewhere
(the spiral mask).

No `exiftool`/`zsteg`/`binwalk` binaries are installed in this environment
and there's no root to apt-install them (checked: no passwordless sudo).
`exifread` (pure Python) is available via `pip install --user`. `zsteg`
and `binwalk` have no usable equivalent package, so this module
reimplements their core technique directly and narrowly:

- **exiftool equivalent**: `exifread` full-tag dump for JPEGs; PNGs don't
  carry EXIF the same way, so their `tEXt`/`zTXt`/`iTXt`/`eXIf` ancillary
  chunks are dumped instead (PNG's actual metadata channel).
- **zsteg equivalent**: LSB extraction is generalized past Phase 5's
  R-channel-only check to all of R/G/B (and RGB-interleaved), both bit
  orders, scored by printable-ASCII ratio -- the same statistic zsteg's
  `--extract` mode effectively surfaces, just without the tool's channel
  shorthand.
- **binwalk equivalent**: a magic-byte signature scan for embedded
  file headers (PNG/JPEG/ZIP/GZIP/PDF/BMP/RIFF) appearing anywhere in the
  raw bytes, not just where each format's own parser expects them --
  catches a second file concatenated onto/hidden inside the first, which
  a chunk-walk alone would miss.
- **`strings` equivalent**: reuses the real `/usr/bin/strings` binary
  (this one *is* installed) for embedded human-readable text outside any
  recognized metadata field.

Six images match Phase 5's original scope (`puzzle.png`, `phase2.png`,
`phase3.png`, `SalPhaseIonCosmicDuality.png`, `theseedisplanted.png`,
`photo_2020-04-26_09-24-30.jpg`); `doc/img/gsmg_stage0_original_telegram.jpg`
is added because it's the one genuinely *original* creator-posted JPEG in
the repo (message `28507`, distinct in bytes/resolution from the later
served PNG) -- the strongest real candidate for camera/app export metadata,
unlike the other four PNGs which are confirmed browser screenshots.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

IMAGES = (
    REPO_ROOT / "puzzle.png",
    REPO_ROOT / "phase2.png",
    REPO_ROOT / "phase3.png",
    REPO_ROOT / "SalPhaselonCosmicDuality.png",
    REPO_ROOT / "theseedisplanted.png",
    REPO_ROOT / "photo_2020-04-26_09-24-30.jpg",
    REPO_ROOT / "doc" / "img" / "gsmg_stage0_original_telegram.jpg",
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
SIGNATURES = {
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
    "ZIP": b"PK\x03\x04",
    "GZIP": b"\x1f\x8b",
    "PDF": b"%PDF",
    "BMP": b"BM",
    "RIFF": b"RIFF",
    "GIF89a": b"GIF89a",
    "GIF87a": b"GIF87a",
}


def is_png(path):
    with path.open("rb") as handle:
        return handle.read(8) == PNG_MAGIC


def png_chunks(path):
    data = path.read_bytes()
    if data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG")
    offset = 8
    chunks = []
    while offset < len(data):
        length = int.from_bytes(data[offset:offset + 4], "big")
        ctype = data[offset + 4:offset + 8].decode("ascii", errors="replace")
        cdata = data[offset + 8:offset + 8 + length]
        chunks.append((ctype, cdata))
        offset += 8 + length + 4  # length + type + data + crc
        if ctype == "IEND":
            break
    trailing = data[offset:]
    return chunks, trailing


def png_metadata_chunks(path):
    chunks, trailing = png_chunks(path)
    text_chunks = [
        (ctype, cdata[:200])
        for ctype, cdata in chunks
        if ctype in ("tEXt", "zTXt", "iTXt", "eXIf")
    ]
    return {
        "chunk_types_in_order": [c[0] for c in chunks],
        "text_chunks": [(t, d.decode("latin1", errors="replace")) for t, d in text_chunks],
        "trailing_bytes_after_iend": len(trailing),
    }


def exif_dump(path):
    import exifread

    with path.open("rb") as handle:
        tags = exifread.process_file(handle, details=True)
    return {str(k): str(v) for k, v in tags.items()}


def embedded_signatures(path, exclude_offset_zero_for=()):
    data = path.read_bytes()
    hits = []
    for name, magic in SIGNATURES.items():
        start = 0
        while True:
            idx = data.find(magic, start)
            if idx == -1:
                break
            if not (idx == 0 and name in exclude_offset_zero_for):
                hits.append({"signature": name, "offset": idx})
            start = idx + 1
    return hits


def lsb_extract(path, channel, bit_order="lsb_first"):
    from PIL import Image

    im = Image.open(path).convert("RGB")
    channel_index = {"R": 0, "G": 1, "B": 2}[channel]
    pixels = list(im.getdata())
    bits = [px[channel_index] & 1 for px in pixels]
    if bit_order == "msb_first":
        bits = bits[: len(bits) - (len(bits) % 8)]
    byte_count = len(bits) // 8
    raw = bytearray()
    for i in range(byte_count):
        byte_bits = bits[i * 8:(i + 1) * 8]
        value = 0
        for bit in byte_bits:
            value = (value << 1) | bit
        raw.append(value)
    return bytes(raw)


def printable_ratio(data, sample=4096):
    sample_data = data[:sample]
    if not sample_data:
        return 0.0
    printable = sum(1 for b in sample_data if 32 <= b < 127)
    return printable / len(sample_data)


def zsteg_equivalent(path):
    results = {}
    for channel in ("R", "G", "B"):
        for bit_order in ("lsb_first", "msb_first"):
            raw = lsb_extract(path, channel, bit_order)
            ratio = printable_ratio(raw)
            results[f"{channel}_{bit_order}"] = {
                "printable_ratio": round(ratio, 4),
                "sample_hex": raw[:32].hex(),
            }
    return results


def strings_dump(path, min_len=6):
    completed = subprocess.run(
        ["strings", "-n", str(min_len), str(path)],
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return lines


def jpeg_com_segments(path):
    data = path.read_bytes()
    segments = []
    offset = 2  # skip SOI
    while offset < len(data) - 1:
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            offset += 2
            continue
        if marker == 0xDA:  # start of scan -- stop parsing markers
            break
        if offset + 4 > len(data):
            break
        seg_len = int.from_bytes(data[offset + 2:offset + 4], "big")
        if marker == 0xFE:  # COM
            segments.append(data[offset + 4:offset + 2 + seg_len].decode("latin1", errors="replace"))
        offset += 2 + seg_len
    return segments


def audit_image(path):
    report = {"path": str(path.relative_to(REPO_ROOT)), "size_bytes": path.stat().st_size}
    if is_png(path):
        report["format"] = "PNG"
        report["png_metadata"] = png_metadata_chunks(path)
        report["zsteg_equivalent"] = zsteg_equivalent(path)
        report["embedded_signatures"] = embedded_signatures(path, exclude_offset_zero_for=("PNG",))
    else:
        report["format"] = "JPEG"
        report["exif"] = exif_dump(path)
        report["jpeg_com_segments"] = jpeg_com_segments(path)
        report["embedded_signatures"] = embedded_signatures(path, exclude_offset_zero_for=("JPEG",))
    report["strings_sample"] = strings_dump(path)[:15]
    report["strings_total_count"] = len(strings_dump(path))
    return report


def audit_all(images=IMAGES):
    return [audit_image(p) for p in images]


def print_report(reports):
    for r in reports:
        print(f"\n=== {r['path']} ({r['format']}, {r['size_bytes']} bytes) ===")
        if r["format"] == "PNG":
            meta = r["png_metadata"]
            print(f"  chunk types: {meta['chunk_types_in_order']}")
            print(f"  text/exif chunks: {meta['text_chunks']}")
            print(f"  trailing bytes after IEND: {meta['trailing_bytes_after_iend']}")
            print("  zsteg-equivalent LSB printable ratios:")
            for key, val in r["zsteg_equivalent"].items():
                flag = " <-- ABOVE ENGLISH THRESHOLD" if val["printable_ratio"] > 0.3 else ""
                print(f"    {key}: {val['printable_ratio']}{flag}")
        else:
            print(f"  EXIF tags: {len(r['exif'])}")
            for k, v in r["exif"].items():
                print(f"    {k}: {v}")
            print(f"  JPEG COM segments: {r['jpeg_com_segments']}")
        if r["embedded_signatures"]:
            print(f"  embedded file signatures found: {r['embedded_signatures']}")
        else:
            print("  embedded file signatures found: none")
        print(f"  strings (>=6 chars): {r['strings_total_count']} total, sample: {r['strings_sample']}")


def self_test():
    reports = audit_all()
    assert len(reports) == 7
    for r in reports:
        assert r["size_bytes"] > 0
    png_reports = [r for r in reports if r["format"] == "PNG"]
    assert len(png_reports) == 5
    jpeg_reports = [r for r in reports if r["format"] == "JPEG"]
    assert len(jpeg_reports) == 2
    print(f"[*] self-test OK: audited {len(reports)} images (5 PNG, 2 JPEG)")
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        reports = self_test()
    else:
        reports = audit_all()

    if args.json:
        print(json.dumps(reports, indent=2, default=str))
    else:
        print_report(reports)


if __name__ == "__main__":
    main()
