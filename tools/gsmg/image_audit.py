#!/usr/bin/env python3
"""Phase 5 — independent forensic audit of the GSMG puzzle images: PNG chunk
structure + CRC verification, trailing data after IEND, text/ancillary chunks,
JPEG EXIF, and an R-channel LSB printable-ratio sanity check.

The community fork's "no steganography" claim (see FINDINGS.md) was only ever
demonstrated for the earlier-stage images. This re-runs the same checks directly
against every doc/img/gsmg_*.{png,jpg} image in this repo, including the
Cosmic-Duality-era ones that were never explicitly covered.

Usage:
    python3 tools/gsmg/image_audit.py
"""
import struct
import zlib
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

IMG_DIR = Path(__file__).resolve().parent.parent.parent / "doc" / "img"
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def audit_png(path):
    data = path.read_bytes()
    print(f"\n=== {path.name} ({len(data)} bytes) ===")
    if data[:8] != PNG_SIG:
        print("  NOT a valid PNG signature!")
        return
    pos = 8
    chunks = []
    while pos < len(data):
        if pos + 8 > len(data):
            print(f"  [!] truncated chunk header at {pos}")
            break
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8].decode("ascii", "replace")
        cdata = data[pos + 8:pos + 8 + length]
        crc_stored = data[pos + 8 + length:pos + 12 + length]
        crc_calc = zlib.crc32(data[pos + 4:pos + 8 + length]).to_bytes(4, "big")
        crc_ok = crc_stored == crc_calc
        chunks.append((ctype, length, crc_ok, cdata))
        pos += 12 + length
        if ctype == "IEND":
            break
    for ctype, length, crc_ok, _ in chunks:
        flag = "" if crc_ok else "  <-- CRC MISMATCH"
        print(f"  chunk {ctype:6s} len={length:8d}{flag}")
    trailing = data[pos:]
    print(f"  bytes after IEND: {len(trailing)}")
    if trailing:
        print(f"    trailing hex: {trailing[:200].hex()}")
    text_chunks = [c for c in chunks if c[0] in ("tEXt", "zTXt", "iTXt", "eXIf")]
    if not text_chunks:
        print("  no tEXt/zTXt/iTXt/eXIf chunks")
    for ctype, _, _, cdata in text_chunks:
        if ctype == "tEXt":
            print(f"    tEXt content: {cdata!r}")
        elif ctype == "zTXt":
            keyword, _, comp = cdata.partition(b"\x00")
            print(f"    zTXt [{keyword}]: {zlib.decompress(comp[1:])!r}")
        elif ctype == "iTXt":
            print(f"    iTXt content: {cdata!r}")


def lsb_summary(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    bits = [px[x, y][0] & 1 for y in range(h) for x in range(w)]
    nbytes = len(bits) // 8
    by = bytearray(
        sum(b << (7 - k) for k, b in enumerate(bits[i * 8:i * 8 + 8]))
        for i in range(nbytes)
    )
    sample = by[:2000]
    printable = sum(1 for c in sample if 32 <= c < 127)
    print(f"  size={w}x{h}  R-LSB printable ratio (first {len(sample)}B): "
          f"{printable / max(1, len(sample)):.3f}")


def audit_jpeg(path):
    print(f"\n=== {path.name} (JPEG, {path.stat().st_size} bytes) ===")
    im = Image.open(path)
    exif = im.getexif()
    if exif:
        for tag_id, value in exif.items():
            print(f"  EXIF {TAGS.get(tag_id, tag_id)}: {value!r}")
    else:
        print("  no EXIF data")
    data = path.read_bytes()
    idx = data.rfind(b"\xff\xd9")
    trailing = data[idx + 2:]
    print(f"  bytes after final FFD9 (EOI): {len(trailing)}")
    lsb_summary(path)


def main():
    if not IMG_DIR.exists():
        print(f"[!] {IMG_DIR} not found")
        return
    for p in sorted(IMG_DIR.glob("gsmg_*")):
        if p.suffix.lower() == ".png":
            audit_png(p)
            lsb_summary(p)
        elif p.suffix.lower() in (".jpg", ".jpeg"):
            audit_jpeg(p)


if __name__ == "__main__":
    main()
