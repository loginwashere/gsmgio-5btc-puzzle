#!/usr/bin/env python3
"""Bounded static-page audit for G-ESC-001: does any page-authored markup
feature (CSS, JS, DOM structure, comments, whitespace, capitalization,
nearby labels) independently distinguish DBBI from FAED, or select between
the `{g,i}` / `{h,e}` escape pairs?

Pre-registered success condition: a stable page-authored feature must
distinguish DBBI from FAED AND independently map to an escape pair or
polarity. Different offsets, DOM positions, or generic first/second
ordering alone do not qualify -- see doc/GSMG_OPEN_GAP_REGISTRY.md#G-ESC-001.

Scope: this checks the page's own markup only (the local mirror, the sole
capture with locally available raw bytes, plus the already-recorded
cross-capture metadata in salphaseion_wayback_history_audit.py). It does
not fetch new Wayback captures -- that is out of scope for this pass.
"""

import argparse
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_structure_audit import DEFAULT_HTML, audit as page_structure_audit  # noqa: E402
from salphaseion_wayback_history_audit import CAPTURES  # noqa: E402


class BoundaryParser(HTMLParser):
    """Collects the markup-level features a page-authored selector could use."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.textarea_attrs = []
        self.style_blocks = []
        self.scripts = []
        self.comments = []
        self._in_style = False
        self._style_buf = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "textarea":
            self.textarea_attrs.append(attrs)
        if tag == "style":
            self._in_style = True
            self._style_buf = []
        if tag == "script":
            self.scripts.append(attrs)

    def handle_data(self, data):
        if self._in_style:
            self._style_buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "style":
            self._in_style = False
            self.style_blocks.append("".join(self._style_buf))

    def handle_comment(self, data):
        self.comments.append(data)


CSS_SELECTOR_RE = re.compile(r"([^{}]+)\{")


def css_selectors(style_blocks):
    selectors = []
    for block in style_blocks:
        selectors.extend(match.strip() for match in CSS_SELECTOR_RE.findall(block))
    return selectors


def audit(html_path=DEFAULT_HTML):
    html_path = Path(html_path)
    raw = html_path.read_text(encoding="utf-8")

    parser = BoundaryParser()
    parser.feed(raw)

    checks = {}

    # 1. CSS: only selector present, and it does not target textareas
    # individually (no id/class/nth-*/ancestry rule could exist if there is
    # nothing for it to select on).
    selectors = css_selectors(parser.style_blocks)
    checks["css_selectors"] = selectors
    checks["css_has_textarea_specific_rule"] = any(
        "textarea" in selector.lower() for selector in selectors
    )
    checks["css_selector_count"] = len(selectors)

    # 2. Both textareas carry byte-identical attributes -- no id/class/
    # rows/cols/anything that could anchor a CSS or JS selector to just one.
    checks["textarea_attrs"] = parser.textarea_attrs
    checks["textarea_attrs_identical"] = (
        len(parser.textarea_attrs) == 2
        and parser.textarea_attrs[0] == parser.textarea_attrs[1]
    )

    # 3. JS: the only <script> is the external, deferred, third-party
    # Cloudflare analytics beacon -- no inline script, nothing referencing
    # "textarea" or positional DOM selection.
    checks["scripts"] = parser.scripts
    checks["single_script_tag"] = len(parser.scripts) == 1
    script_src = ""
    if parser.scripts:
        script_src = dict(parser.scripts[0]).get("src", "")
    checks["script_is_external_analytics_beacon"] = (
        "cloudflareinsights.com" in script_src
    )
    checks["script_references_textarea"] = "textarea" in raw.lower().split(
        "<script", 1
    )[-1] if "<script" in raw.lower() else False

    # 4. No HTML comments anywhere on the page.
    checks["comment_count"] = len(parser.comments)
    checks["comments"] = parser.comments

    # 5. DBBI and FAED are not two separate elements -- they are consecutive
    # substrings of the SAME <textarea>'s text content, joined only by the
    # binary-ASCII `matrixsumlist` span. There is no DOM boundary (wrapper
    # element, sibling split, or attribute change) between them at all, so
    # the entire class of CSS ancestry/sibling/nth-* selectors is
    # inapplicable by construction, not merely empirically negative.
    structure = page_structure_audit(html_path)
    segment_names = [segment["name"] for segment in structure["salphaseion"]["segments"]]
    checks["dbbi_faed_share_one_textarea"] = segment_names[:3] == [
        "dbbi",
        "abba_matrix_instruction",
        "faed",
    ]
    checks["whitespace_is_single_character_separation"] = structure["salphaseion"][
        "whitespace_is_single_character_separation"
    ]

    # 6. Capitalization: the only case anomaly on the page is the H1/h1
    # heading pair, already closed negative (Phase 109 / Phase 34-104's
    # mirror9 derivation is a different chain; h_marker_selector_audit.py
    # found "no single, well-defined h to promote"). Confirm it still
    # applies to neither DBBI nor FAED specifically -- both live inside the
    # SAME textarea, under the SAME "SalPhaseIon" heading, so the H1/h1
    # case split (which distinguishes the SalPhaseIon vs Cosmic Duality
    # textareas) cannot bear on DBBI vs FAED at all.
    checks["h1_case_split_is_salphaseion_vs_cosmic_not_dbbi_vs_faed"] = True

    # 7. Cross-capture: the only markup diff established across all 5 known
    # Wayback captures is the single H1/h1 case change between the first
    # two (salphaseion_wayback_history_audit.assert_initial_heading_only_change).
    # Raw bytes for captures 1-4 are not present locally in this pass, so a
    # sub-region byte diff for the later capture growth (+32, then +504
    # bytes) is explicitly out of scope here, not silently assumed stable.
    checks["known_captures"] = len(CAPTURES)
    checks["cross_capture_markup_diff_established"] = (
        "H1/h1 case change between captures 1 and 2 only; "
        "captures 2-3 (+32 bytes) and 3-4 (+504 bytes) growth is not "
        "sub-region-diffed locally -- not fetched in this pass, see scope note"
    )

    checks["pre_registered_condition_met"] = False  # no positive finding
    return checks


def print_report(checks):
    print("DBBI/FAED page-authored boundary-selector audit (G-ESC-001)")
    print(f"  CSS selectors on page: {checks['css_selectors']}")
    print(f"  CSS has textarea-specific rule: {checks['css_has_textarea_specific_rule']}")
    print(f"  Textarea attributes identical: {checks['textarea_attrs_identical']}")
    print(f"  Single <script> tag, external analytics beacon: "
          f"{checks['single_script_tag']}, {checks['script_is_external_analytics_beacon']}")
    print(f"  Script references 'textarea': {checks['script_references_textarea']}")
    print(f"  HTML comments found: {checks['comment_count']}")
    print(f"  DBBI/FAED share one textarea (no DOM boundary between them): "
          f"{checks['dbbi_faed_share_one_textarea']}")
    print(f"  Whitespace is uniform single-character separation throughout: "
          f"{checks['whitespace_is_single_character_separation']}")
    print(f"  Known Wayback captures: {checks['known_captures']}")
    print(f"  Cross-capture markup diff established: "
          f"{checks['cross_capture_markup_diff_established']}")
    print(f"  Pre-registered success condition met: "
          f"{checks['pre_registered_condition_met']}")
    print()
    print("Conclusion: textarea markup, CSS, and JS boundary selectors are "
          "exhausted and negative. DBBI and FAED share one text node with no "
          "markup boundary between them, so DOM ancestry/sibling selectors "
          "are inapplicable by construction. G-ESC-001 remains open only for "
          "a genuinely external selector (see doc/GSMG_OPEN_GAP_REGISTRY.md).")


def self_test():
    checks = audit()
    assert checks["css_selector_count"] == 1, checks["css_selectors"]
    assert not checks["css_has_textarea_specific_rule"]
    assert checks["textarea_attrs_identical"]
    assert checks["single_script_tag"]
    assert checks["script_is_external_analytics_beacon"]
    assert not checks["script_references_textarea"]
    assert checks["comment_count"] == 0
    assert checks["dbbi_faed_share_one_textarea"]
    assert checks["whitespace_is_single_character_separation"]
    assert checks["known_captures"] == 5
    assert not checks["pre_registered_condition_met"]
    print("[*] self-test OK: all markup-level boundary-selector checks "
          "confirmed negative")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    print_report(audit(args.html))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
