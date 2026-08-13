#!/usr/bin/env python3
"""Recover and triage the fork's previously-unexamined Game of Logic OCR."""

import argparse
import hashlib
import re
import urllib.request
from pathlib import Path


SOURCE_COMMIT = "8d043ad115ec7736ecff65f33812c7344ccf0221"
SOURCE_URL = (
    "https://raw.githubusercontent.com/halbgott29a/gsmgio-5btc-puzzle/"
    f"{SOURCE_COMMIT}/_work/gameoflogic_ocr.txt"
)
EXPECTED_SHA256 = "e269153ec9d502dc25986e54169a1c211841a4f7256b460e4a017bae3242a002"
DEFAULT_OCR = Path("/tmp/gameoflogic_ocr.txt")

PUZZLE_SPECIFIC = (
    "matrixsumlist",
    "yellowblueprimes",
    "cosmic duality",
    "salphaseion",
    "sha256",
    "first hint",
    "last command",
    "better half",
    "white rabbit",
    "password",
    "architect",
)

STRUCTURAL_TERMS = (
    "matrix",
    "diagram",
    "counter",
    "counters",
    "half",
    "red",
    "grey",
    "gray",
    "white",
    "black",
    "yellow",
    "blue",
    "logic",
)

REQUIRED_ANCHORS = (
    "this game requires nine counters",
    "four red and five grey",
    "half of smaller diagram",
    "red counter in a compartment",
    "grey counter in a compartment",
)


def download(path=DEFAULT_OCR):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "GSMG source provenance audit"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())
    return path


def normalize(text):
    text = text.lower().replace("——", " ").replace("—", " ")
    return re.sub(r"\s+", " ", text)


def count_term(text, term):
    return len(re.findall(r"\b" + re.escape(term) + r"\b", text))


def audit(path=DEFAULT_OCR):
    path = Path(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise AssertionError(
            f"OCR SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}"
        )
    text = raw.decode("utf-8")
    normalized = normalize(text)
    missing = [anchor for anchor in REQUIRED_ANCHORS if anchor not in normalized]
    if missing:
        raise AssertionError(f"OCR missing expected anchors: {missing}")

    specific = {term: count_term(normalized, term) for term in PUZZLE_SPECIFIC}
    structural = {term: count_term(normalized, term) for term in STRUCTURAL_TERMS}
    if any(specific.values()):
        raise AssertionError(f"unexpected puzzle-specific vocabulary: {specific}")

    return {
        "source_commit": SOURCE_COMMIT,
        "sha256": digest,
        "bytes": len(raw),
        "lines": len(text.splitlines()),
        "puzzle_specific_counts": specific,
        "structural_counts": structural,
        "anchors": REQUIRED_ANCHORS,
        "creator_selected": False,
        "recognition_only": True,
        "promoted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocr", type=Path, default=DEFAULT_OCR)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        download(args.ocr)
    if not args.ocr.exists():
        raise SystemExit(f"missing {args.ocr}; pass --download or --ocr PATH")

    report = audit(args.ocr)
    print(f"source commit: {report['source_commit']}")
    print(f"sha256: {report['sha256']}")
    print(f"size: {report['bytes']} bytes, {report['lines']} lines")
    print(f"puzzle-specific vocabulary: {report['puzzle_specific_counts']}")
    print(f"structural vocabulary: {report['structural_counts']}")
    print("result: source recovered; structural resemblance only; no promotion")


if __name__ == "__main__":
    main()
