#!/usr/bin/env python3
"""Verify the exact Designing the Future PDF, its page-10 salvation/damnation
text, and a bounded zero-hit keyword sweep across it and Looking Forward."""

import argparse
import hashlib
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import looking_forward_source_audit as lf

SOURCE_URL = (
    "https://files.thevenusproject.com/hotlink-ok/designing_the_future_ebook/"
    "Jacque%20Fresco%20-%20Designing%20the%20Future.pdf"
)
EXPECTED_SHA256 = "6e002f41a5907eccf9004b77195b7688259659b6be5e99b705629da5fd208a28"
EXPECTED_PDF_PAGE = 10
DEFAULT_PDF = Path("/tmp/designing_the_future.pdf")
PAGE_ANCHORS = (
    "the future of the world is our responsibility",
    "it depends upon",
    "decisions we make today",
    "we are our own salvation or damnation",
)

# Puzzle-relevant vocabulary checked for accidental presence in either book.
# Word-boundary matched: naive substring counting produces false positives
# (e.g. "yin" inside "buying", "architect" inside "architecture").
KEYWORD_SWEEP = (
    "matrix",
    "matrixsumlist",
    "yin",
    "yang",
    "duality",
    "cipher",
    "hash",
    "password",
    "checkerboard",
    "architect",
)


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def download_pdf(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        path.write_bytes(response.read())


def extract_pages(path):
    with tempfile.TemporaryDirectory(prefix="gsmg-designing-future-") as directory:
        output = Path(directory) / "book.txt"
        subprocess.run(
            ["pdftotext", "-layout", str(path), str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        return output.read_text(encoding="utf-8", errors="replace").split("\f")


def word_hits(text, keyword):
    return re.findall(r"\b" + re.escape(keyword) + r"\b", text.lower())


def audit_page10(path):
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
        "full_text": "\n".join(pages),
    }


def cross_book_keyword_sweep(designing_future_text, looking_forward_path):
    lf_digest = hashlib.sha256(looking_forward_path.read_bytes()).hexdigest()
    if lf_digest != lf.EXPECTED_SHA256:
        raise AssertionError(
            f"Looking Forward SHA-256 mismatch: expected {lf.EXPECTED_SHA256}, "
            f"got {lf_digest}"
        )
    looking_forward_text = "\n".join(extract_pages(looking_forward_path))

    results = {}
    for label, text in (
        ("designing_the_future", designing_future_text),
        ("looking_forward", looking_forward_text),
    ):
        results[label] = {kw: len(word_hits(text, kw)) for kw in KEYWORD_SWEEP}
        nonzero = {kw: n for kw, n in results[label].items() if n}
        if nonzero:
            raise AssertionError(f"{label} unexpectedly contains: {nonzero}")

    salvation_hits = len(word_hits(designing_future_text, "salvation"))
    damnation_hits = len(word_hits(designing_future_text, "damnation"))
    if salvation_hits != 1 or damnation_hits != 1:
        raise AssertionError(
            "expected exactly one salvation/damnation occurrence in "
            f"Designing the Future, got salvation={salvation_hits} "
            f"damnation={damnation_hits}"
        )
    lf_salvation = len(word_hits(looking_forward_text, "salvation"))
    lf_damnation = len(word_hits(looking_forward_text, "damnation"))
    if lf_salvation or lf_damnation:
        raise AssertionError(
            "expected zero salvation/damnation occurrences in Looking Forward, "
            f"got salvation={lf_salvation} damnation={lf_damnation}"
        )

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--looking-forward-pdf", type=Path, default=lf.DEFAULT_PDF)
    parser.add_argument(
        "--download",
        action="store_true",
        help="download both frozen source URLs before auditing",
    )
    args = parser.parse_args()

    if args.download:
        download_pdf(SOURCE_URL, args.pdf)
        download_pdf(lf.SOURCE_URL, args.looking_forward_pdf)
    if not args.pdf.exists():
        raise SystemExit(f"missing {args.pdf}; pass --download or provide --pdf")
    if not args.looking_forward_pdf.exists():
        raise SystemExit(
            f"missing {args.looking_forward_pdf}; pass --download or "
            "provide --looking-forward-pdf"
        )

    page_result = audit_page10(args.pdf)
    print(f"source: {SOURCE_URL}")
    print(f"file: {page_result['path']}")
    print(f"sha256: {page_result['sha256']}")
    print(f"extracted pages: {page_result['page_count']}")
    print(f"verified PDF page: {page_result['page']}")
    for anchor in page_result["anchors"]:
        print(f"  - {anchor}")

    sweep = cross_book_keyword_sweep(page_result["full_text"], args.looking_forward_pdf)
    print("\ncross-book keyword sweep (word-boundary matched, expect all zero):")
    for label, counts in sweep.items():
        print(f"  {label}: {counts}")
    print("\nsalvation/damnation: designing_the_future=1/1, looking_forward=0/0")


if __name__ == "__main__":
    main()
