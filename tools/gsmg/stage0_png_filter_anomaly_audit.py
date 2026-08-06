#!/usr/bin/env python3
"""Reproduce and calibrate Telegram message `49536` (k1ng, 2025-09-24)'s claim
about the Stage-0 `gsmg.io/puzzle` PNG (`doc/img/gsmg_puzzle_stage1.png`,
1048x1556, the only PNG this project has that matches "1556 filterbytes").

The message claims: decoding the raw PNG scanline filter bytes gives a
histogram of (0x04=0, 0x03=0, 0x02=1464, 0x01=91, 0x00=1); the lone 0x00 row
sits 127/128 lines into the image's embedded QR code; and simple digit
manipulation of the row number recovers the already-solved Decentraland
coordinates (-41,-16 / -41,-17). Everything numeric here is independently
recomputed directly from the archived PNG bytes and pixels -- nothing is
taken from the message on faith.

This module also checks whether the QR code's own decoded payload contains
anything beyond the expected/visible `blockchain.com` address URL.
"""

import argparse
import hashlib
import struct
import zlib
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

IMAGE_PATH = (
    Path(__file__).resolve().parents[2] / "doc" / "img" / "gsmg_puzzle_stage1.png"
)

EXPECTED_DIMENSIONS = (1048, 1556)
EXPECTED_IMAGE_SHA256 = (
    "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
)
EXPECTED_IHDR = {
    "bit_depth": 8,
    "color_type": 6,
    "compression_method": 0,
    "filter_method": 0,
    "interlace_method": 0,
}
EXPECTED_FILTER_HISTOGRAM = {0: 1, 1: 91, 2: 1464, 3: 0, 4: 0}
EXPECTED_ANOMALY_ROW_0INDEXED = 1416
EXPECTED_QR_TOP_ROW_0INDEXED = 1289
EXPECTED_LINES_INTO_QR_0INDEXED = 127
EXPECTED_QR_MODULE_COUNT = 33  # QR version 4
EXPECTED_QR_PAYLOAD = (
    "https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
)


def inspect_png(path=IMAGE_PATH):
    data = path.read_bytes()
    image_sha256 = hashlib.sha256(data).hexdigest()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    ihdr = None
    saw_iend = False
    while pos < len(data):
        assert pos + 12 <= len(data), "truncated PNG chunk header"
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_end = pos + 12 + length
        assert chunk_end <= len(data), f"truncated {chunk_type!r} chunk"
        chunk_data = data[pos + 8 : pos + 8 + length]
        stored_crc = struct.unpack(">I", data[pos + 8 + length : chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        assert stored_crc == actual_crc, f"CRC mismatch in {chunk_type!r}"
        if chunk_type == b"IHDR":
            assert ihdr is None, "multiple IHDR chunks"
            assert length == 13, f"invalid IHDR length: {length}"
            (
                width,
                height,
                bit_depth,
                color_type,
                compression_method,
                filter_method,
                interlace_method,
            ) = struct.unpack(">IIBBBBB", chunk_data)
            ihdr = {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "compression_method": compression_method,
                "filter_method": filter_method,
                "interlace_method": interlace_method,
            }
        if chunk_type == b"IDAT":
            idat += chunk_data
        pos = chunk_end
        if chunk_type == b"IEND":
            saw_iend = True
            break

    assert ihdr is not None, "missing IHDR"
    assert idat, "missing IDAT"
    assert saw_iend, "missing IEND"
    assert pos == len(data), "trailing bytes after IEND"

    raw = zlib.decompress(idat)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ihdr["color_type"]]
    bits_per_row = ihdr["width"] * channels * ihdr["bit_depth"]
    assert bits_per_row % 8 == 0, "packed PNG rows are outside this audit's scope"
    stride = bits_per_row // 8
    expected_raw_length = ihdr["height"] * (1 + stride)
    assert len(raw) == expected_raw_length, (
        f"unexpected decompressed length: {len(raw)} != {expected_raw_length}"
    )

    filter_bytes = []
    offset = 0
    for _ in range(ihdr["height"]):
        filter_bytes.append(raw[offset])
        offset += 1 + stride
    assert offset == len(raw)
    return ihdr, filter_bytes, image_sha256


def read_png_filter_bytes(path=IMAGE_PATH):
    ihdr, filter_bytes, _ = inspect_png(path)
    return (ihdr["width"], ihdr["height"]), filter_bytes


def find_qr_top_row(path=IMAGE_PATH):
    """Detect the QR code's bounding quad and return its top-left y (0-indexed
    absolute pixel row), independent of the filter-byte analysis above."""
    image = cv2.imread(str(path))
    detector = cv2.QRCodeDetector()
    _, points, _ = detector.detectAndDecode(image)
    assert points is not None, "QR code not detected in the source image"
    corners = points[0]
    return int(round(min(corner[1] for corner in corners)))


def decode_qr_payload(path=IMAGE_PATH):
    image = cv2.imread(str(path))
    detector = cv2.QRCodeDetector()
    _, points, _ = detector.detectAndDecode(image)
    corners = points[0].astype(np.float32)
    size = 400
    destination = np.array(
        [[0, 0], [size, 0], [size, size], [0, size]], dtype=np.float32
    )
    matrix = cv2.getPerspectiveTransform(corners, destination)
    warped = cv2.warpPerspective(image, matrix, (size, size))
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    padded = cv2.copyMakeBorder(thresh, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    bgr = cv2.cvtColor(padded, cv2.COLOR_GRAY2BGR)
    ok, quad = detector.detect(bgr)
    assert ok, "QR re-detection on the rectified crop failed"
    payload, module_grid = detector.decode(bgr, quad)
    return payload, module_grid


def digit_trick(row_1indexed):
    """The message's own manual transform: split the 4-digit row number in
    half, reverse the first half. Recorded here exactly as described, not
    generalized -- this is a single specific reading of a single number, not
    a validated method."""
    text = str(row_1indexed)
    first_half, second_half = text[:2], text[2:]
    return int(first_half[::-1]), int(second_half)


def self_test():
    ihdr, filter_bytes, image_sha256 = inspect_png()
    dimensions = (ihdr["width"], ihdr["height"])
    assert image_sha256 == EXPECTED_IMAGE_SHA256, image_sha256
    assert dimensions == EXPECTED_DIMENSIONS, dimensions
    assert {field: ihdr[field] for field in EXPECTED_IHDR} == EXPECTED_IHDR, ihdr
    histogram = {value: filter_bytes.count(value) for value in range(5)}
    assert histogram == EXPECTED_FILTER_HISTOGRAM, histogram

    anomaly_rows = [index for index, value in enumerate(filter_bytes) if value == 0]
    assert anomaly_rows == [EXPECTED_ANOMALY_ROW_0INDEXED], anomaly_rows

    qr_top = find_qr_top_row()
    assert qr_top == EXPECTED_QR_TOP_ROW_0INDEXED, qr_top
    lines_into_qr = EXPECTED_ANOMALY_ROW_0INDEXED - qr_top
    assert lines_into_qr == EXPECTED_LINES_INTO_QR_0INDEXED, lines_into_qr

    payload, module_grid = decode_qr_payload()
    assert payload == EXPECTED_QR_PAYLOAD, payload
    assert module_grid.shape[0] == EXPECTED_QR_MODULE_COUNT, module_grid.shape

    reversed_first_half, second_half = digit_trick(EXPECTED_ANOMALY_ROW_0INDEXED + 1)
    assert (reversed_first_half, second_half) == (41, 17), (reversed_first_half, second_half)

    print(
        "[*] self-test OK: filter-byte histogram and lone 0x00 row (index "
        f"{EXPECTED_ANOMALY_ROW_0INDEXED}) reproduce exactly; independently "
        f"detected QR top row is {qr_top}, placing the anomaly "
        f"{lines_into_qr} lines into the QR code, matching the message's "
        "127/128 claim. QR payload decodes cleanly to the expected/visible "
        "blockchain.com address URL (no hidden secondary content). The exact "
        "source hash and PNG metadata also match; interlace method 0 directly "
        "rules out Adam7 for this artifact."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    ihdr, filter_bytes, image_sha256 = inspect_png()
    dimensions = (ihdr["width"], ihdr["height"])
    histogram = {value: filter_bytes.count(value) for value in range(5)}
    print(f"[*] image SHA-256: {image_sha256}")
    print(f"[*] image dimensions: {dimensions}")
    print(f"[*] IHDR: {ihdr}")
    print(f"[*] filter-byte histogram: {histogram}")

    anomaly_row = EXPECTED_ANOMALY_ROW_0INDEXED
    qr_top = find_qr_top_row()
    print(f"[*] lone 0x00 filter row (0-indexed): {anomaly_row}")
    print(f"[*] QR code top row (0-indexed, independently detected): {qr_top}")
    print(f"[*] lines into QR code: {anomaly_row - qr_top}")

    reversed_first_half, second_half = digit_trick(anomaly_row + 1)
    print(f"[*] digit trick on row {anomaly_row + 1}: ({reversed_first_half}, {second_half})")

    payload, module_grid = decode_qr_payload()
    print(f"[*] QR payload: {payload!r}")
    print(f"[*] QR module grid: {module_grid.shape}")


if __name__ == "__main__":
    main()
