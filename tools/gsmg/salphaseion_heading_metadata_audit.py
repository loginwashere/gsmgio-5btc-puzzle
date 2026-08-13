#!/usr/bin/env python3
"""Audit heading markup and document metadata on the archived SalPhaseIon page.

This closes item 6 of doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md.  The default
run is offline against the authenticated local mirror.  ``--live`` fetches
exactly the five already-registered Wayback captures, verifies their pinned
hashes, and checks the same presentation facts across them.
"""

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from page_structure_audit import DEFAULT_HTML
from salphaseion_wayback_history_audit import (
    CAPTURES,
    RAW_CAPTURE_TEMPLATE,
    ROUTE,
    assert_capture,
    fetch_bytes,
)


class PresentationParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.headings = []
        self.classes = []
        self.inline_styles = []
        self.meta = []
        self.links = []
        self.style_blocks = []
        self.title_parts = []
        self._heading = None
        self._in_title = False
        self._in_style = False
        self._style_parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)
        if "class" in attrs_dict:
            self.classes.append({"tag": tag, "class": attrs_dict["class"]})
        if "style" in attrs_dict:
            self.inline_styles.append({"tag": tag, "style": attrs_dict["style"]})
        if tag == "h1":
            self._heading = {"text_parts": [], "attrs": attrs_dict, "nested_tags": []}
        elif self._heading is not None:
            self._heading["nested_tags"].append(tag)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            self.meta.append(attrs_dict)
        elif tag == "link":
            self.links.append(attrs_dict)
        elif tag == "style":
            self._in_style = True
            self._style_parts = []

    def handle_data(self, data):
        if self._heading is not None:
            self._heading["text_parts"].append(data)
        if self._in_title:
            self.title_parts.append(data)
        if self._in_style:
            self._style_parts.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "h1" and self._heading is not None:
            self.headings.append(
                {
                    "text": "".join(self._heading["text_parts"]).strip(),
                    "attrs": self._heading["attrs"],
                    "nested_tags": self._heading["nested_tags"],
                }
            )
            self._heading = None
        elif tag == "title":
            self._in_title = False
        elif tag == "style":
            self.style_blocks.append("".join(self._style_parts))
            self._in_style = False


def _rel_tokens(link):
    return {token.lower() for token in link.get("rel", "").split()}


def analyze(raw):
    text = raw.decode("ascii") if isinstance(raw, bytes) else raw
    parser = PresentationParser()
    parser.feed(text)

    descriptions = [
        item.get("content", "")
        for item in parser.meta
        if item.get("name", "").lower() == "description"
    ]
    favicon_links = [
        link for link in parser.links if "icon" in _rel_tokens(link)
    ]
    stylesheet_links = [
        link for link in parser.links if "stylesheet" in _rel_tokens(link)
    ]
    authored_css = "\n".join(parser.style_blocks)
    heading_tags = re.findall(r"<h1\b[^>]*>.*?</h1>", text, re.I | re.S)

    report = {
        "title": "".join(parser.title_parts).strip(),
        "meta_description": descriptions,
        "favicon_links": favicon_links,
        "stylesheet_links": stylesheet_links,
        "headings": parser.headings,
        "raw_heading_tags": heading_tags,
        "class_attributes": parser.classes,
        "inline_styles": parser.inline_styles,
        "authored_css": re.sub(r"\s+", " ", authored_css).strip(),
        "css_mentions_letter_spacing": "letter-spacing" in authored_css.lower(),
        "css_mentions_color": bool(re.search(r"(?:^|[;{])\s*color\s*:", authored_css, re.I)),
        "external_stylesheet_count": len(stylesheet_links),
        "explicit_favicon_count": len(favicon_links),
    }
    assert_expected(report)
    return report


def assert_expected(report):
    if report["title"] != "GSMG Puzzle":
        raise AssertionError(f"unexpected title: {report['title']!r}")
    if report["meta_description"] != ["GSMG Puzzle"]:
        raise AssertionError("meta description changed")
    if [item["text"] for item in report["headings"]] != [
        "SalPhaseIon",
        "Cosmic Duality",
    ]:
        raise AssertionError("heading text or order changed")
    if any(item["attrs"] or item["nested_tags"] for item in report["headings"]):
        raise AssertionError("heading gained attributes or nested markup")
    if report["class_attributes"] != [{"tag": "html", "class": "no-js"}]:
        raise AssertionError("class inventory changed")
    if report["inline_styles"] != [
        {"tag": "textarea", "style": "width: 100%; height: 200px"},
        {"tag": "textarea", "style": "width: 100%; height: 200px"},
    ]:
        raise AssertionError("inline-style inventory changed")
    if report["authored_css"] != "body { font-family: 'arial'; }":
        raise AssertionError("authored CSS changed")
    if any(
        (
            report["css_mentions_letter_spacing"],
            report["css_mentions_color"],
            report["external_stylesheet_count"],
            report["explicit_favicon_count"],
        )
    ):
        raise AssertionError("unexpected presentation channel appeared")


def audit(path=DEFAULT_HTML):
    return analyze(Path(path).read_bytes())


def live_audit():
    reports = []
    for expected in CAPTURES:
        url = RAW_CAPTURE_TEMPLATE.format(
            timestamp=expected["timestamp"], route=ROUTE
        )
        raw = fetch_bytes(url)
        assert_capture(raw, expected)
        reports.append({"timestamp": expected["timestamp"], **analyze(raw)})

    stable_keys = (
        "title",
        "meta_description",
        "favicon_links",
        "stylesheet_links",
        "headings",
        "class_attributes",
        "inline_styles",
        "authored_css",
    )
    reference = reports[0]
    if any(
        report[key] != reference[key]
        for report in reports[1:]
        for key in stable_keys
    ):
        raise AssertionError("heading or head metadata differs across captures")
    return {
        "capture_count": len(reports),
        "timestamps": [report["timestamp"] for report in reports],
        "presentation_identical": True,
        "raw_salphaseion_open_tag_variants": sorted(
            {
                re.match(r"<[^>]+>", report["raw_heading_tags"][0]).group(0)
                for report in reports
            }
        ),
        "report": reference,
        "promoted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = live_audit() if args.live else audit(args.html)
    if args.json:
        print(json.dumps(report, indent=2))
        return
    if args.live:
        print(f"captures verified: {report['capture_count']}")
        print(f"presentation identical: {report['presentation_identical']}")
        print(f"raw H1 tag variants: {report['raw_salphaseion_open_tag_variants']}")
        report = report["report"]
    print(f"title: {report['title']}")
    print(f"description: {report['meta_description'][0]}")
    print(f"headings: {[item['text'] for item in report['headings']]}")
    print(f"classes: {report['class_attributes']}")
    print(f"authored CSS: {report['authored_css']}")
    print(f"explicit favicon links: {report['explicit_favicon_count']}")
    print("result: no heading- or head-metadata selector; no promotion")


if __name__ == "__main__":
    main()
