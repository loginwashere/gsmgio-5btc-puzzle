#!/usr/bin/env python3
"""Verify the exact Looking Forward PDF and the bounded page-37 text claim."""

import argparse
import hashlib
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://www.aiai.ed.ac.uk/~bat/IMG/SEA-CITY/JF/"
    "Jacque_Fresco-Looking_Forward.pdf"
)
EXPECTED_SHA256 = "59c9d888a0c6f5f45cfe6ef874b88d9f29b520f396ce613d93b241ed79996e85"
EXPECTED_PDF_PAGE = 37
DEFAULT_PDF = Path("/tmp/Jacque_Fresco-Looking_Forward.pdf")
PAGE_ANCHORS = (
    "no two things in this world are",
    "the closer we look",
    "think in terms of degrees",
    "implies polar opposites",
    "black or white",
    "shades of grey",
)


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def download_pdf(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        path.write_bytes(response.read())


def extract_pages(path):
    with tempfile.TemporaryDirectory(prefix="gsmg-looking-forward-") as directory:
        output = Path(directory) / "book.txt"
        subprocess.run(
            ["pdftotext", "-layout", str(path), str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        return output.read_text(encoding="utf-8", errors="replace").split("\f")


def audit(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise AssertionError(
            f"PDF SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}"
        )

    pages = extract_pages(path)
    if len(pages) < EXPECTED_PDF_PAGE:
        raise AssertionError(f"PDF has only {len(pages)} extracted pages")
    page = normalize(pages[EXPECTED_PDF_PAGE - 1])
    missing = [anchor for anchor in PAGE_ANCHORS if anchor not in page]
    if missing:
        raise AssertionError(f"page {EXPECTED_PDF_PAGE} missing anchors: {missing}")

    return {
        "path": path,
        "sha256": digest,
        "page_count": len(pages),
        "page": EXPECTED_PDF_PAGE,
        "anchors": PAGE_ANCHORS,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument(
        "--download",
        action="store_true",
        help="download the frozen source URL to --pdf before auditing",
    )
    args = parser.parse_args()

    if args.download:
        download_pdf(args.pdf)
    if not args.pdf.exists():
        raise SystemExit(
            f"missing {args.pdf}; pass --download or provide an existing file with --pdf"
        )

    result = audit(args.pdf)
    print(f"source: {SOURCE_URL}")
    print(f"file: {result['path']}")
    print(f"sha256: {result['sha256']}")
    print(f"extracted pages: {result['page_count']}")
    print(f"verified PDF page: {result['page']}")
    for anchor in result["anchors"]:
        print(f"  - {anchor}")


if __name__ == "__main__":
    main()
