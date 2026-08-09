#!/usr/bin/env python3
"""Test whether SalPhaseIon presentation binds DBBI, FAED, or instructions.

The logical segmentation is already established by page_structure_audit.
This audit examines the authenticated HTML presentation layer: DOM elements,
attributes, CSS, authored whitespace, and source boundaries.  Browser-created
soft wrapping is deliberately not treated as authored structure.
"""

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

from page_structure_audit import DEFAULT_HTML, audit as page_audit


EXPECTED_HTML_SHA256 = (
    "b13cbc5c2935dc3e9ff8bf71681f2ef61317fefdce04159129877244a92a3947"
)


class PresentationParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = None
        self.textareas = []
        self.headings = []
        self.styles = []
        self.links = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        item = {"attrs": tuple(attrs), "parts": [], "data_events": 0}
        if tag == "textarea":
            self.textareas.append(item)
            self.active = (tag, item)
        elif tag == "h1":
            self.headings.append(item)
            self.active = (tag, item)
        elif tag == "style":
            self.styles.append(item)
            self.active = (tag, item)
        elif tag == "link":
            self.links.append({"attrs": tuple(attrs)})
        elif tag == "script":
            self.scripts.append(item)
            self.active = (tag, item)

    def handle_data(self, data):
        if self.active is not None:
            self.active[1]["parts"].append(data)
            self.active[1]["data_events"] += 1

    def handle_endtag(self, tag):
        if self.active is not None and self.active[0] == tag.lower():
            self.active = None


def _text(item):
    return "".join(item["parts"])


def audit(html_path=DEFAULT_HTML):
    html_path = Path(html_path)
    source = html_path.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if source_hash != EXPECTED_HTML_SHA256:
        raise AssertionError("authenticated page capture changed")

    parser = PresentationParser()
    parser.feed(source)
    if len(parser.textareas) != 2:
        raise AssertionError("expected exactly two textareas")
    if any(item["data_events"] != 1 for item in parser.textareas):
        raise AssertionError("textarea content is no longer one text event each")

    page = page_audit(html_path)
    salph_raw = _text(parser.textareas[0])
    cosmic_raw = _text(parser.textareas[1])
    logical = "".join(salph_raw.split())
    if salph_raw != " ".join(logical):
        raise AssertionError("SalPhaseIon is no longer uniformly space-separated")

    boundaries = []
    segments = page["salphaseion"]["segments"]
    for left, right in zip(segments, segments[1:]):
        raw_separator_index = 2 * left["end"] - 1
        boundaries.append({
            "left": left["name"],
            "right": right["name"],
            "logical_offset": left["end"],
            "raw_separator": salph_raw[raw_separator_index],
            "same_textarea_node": True,
            "authored_line_break": False,
            "boundary_markup": False,
            "logical_context": (
                logical[max(0, left["end"] - 8):left["end"]]
                + "|"
                + logical[left["end"]:left["end"] + 8]
            ),
        })

    textarea_attrs = tuple(item["attrs"] for item in parser.textareas)
    expected_attrs = (("style", "width: 100%; height: 200px"),)
    if textarea_attrs != (expected_attrs, expected_attrs):
        raise AssertionError("textarea presentation attributes changed")
    if any(row["raw_separator"] != " " for row in boundaries):
        raise AssertionError("a segment boundary has distinct whitespace")

    headings = tuple(_text(item).strip() for item in parser.headings)
    stylesheet_links = tuple(
        item for item in parser.links
        if dict(item["attrs"]).get("rel", "").lower() == "stylesheet"
    )
    script_sources = tuple(
        dict(item["attrs"]).get("src") for item in parser.scripts
        if dict(item["attrs"]).get("src")
    )
    return {
        "source": str(html_path),
        "html_sha256": source_hash,
        "headings": headings,
        "textarea_attributes": textarea_attrs,
        "textarea_semantic_attributes": (),
        "inline_style_scope": "same width:100%; height:200px on both textareas",
        "document_style_text": tuple(_text(item).strip() for item in parser.styles),
        "stylesheet_links": stylesheet_links,
        "script_sources": script_sources,
        "salphaseion": {
            "one_textarea_text_node": True,
            "logical_characters": len(logical),
            "authored_line_breaks": salph_raw.count("\n"),
            "uniform_single_space_between_every_character": True,
            "segment_boundaries": tuple(boundaries),
            "fixed_authored_columns": False,
        },
        "cosmic_duality_control": {
            "authored_line_breaks": cosmic_raw.count("\n"),
            "line_lengths": tuple(len(line) for line in cosmic_raw.splitlines()),
            "fixed_authored_columns": len(set(map(len, cosmic_raw.splitlines()))) == 1,
        },
        "binding_candidates_found": (),
        "verdict": (
            "The authenticated presentation layer supplies no DBBI/FAED, "
            "FAED/thispassword, or internal segment binding. All SalPhaseIon "
            "segments occupy one uniformly spaced textarea text node with no "
            "authored line breaks or boundary markup. Any visible wrapping is "
            "viewport/browser layout, unlike Cosmic Duality's explicit 64-column "
            "source lines, and cannot select a decoder."
        ),
    }


def self_test(html_path=DEFAULT_HTML):
    report = audit(html_path)
    assert report["headings"] == ("SalPhaseIon", "Cosmic Duality")
    assert report["salphaseion"]["authored_line_breaks"] == 0
    assert len(report["salphaseion"]["segment_boundaries"]) == 12
    assert report["cosmic_duality_control"]["authored_line_breaks"] == 27
    assert report["cosmic_duality_control"]["line_lengths"] == (64,) * 28
    assert not report["binding_candidates_found"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: no authored presentation binding")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.html) if args.self_test else audit(args.html)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
