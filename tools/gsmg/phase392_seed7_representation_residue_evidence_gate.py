#!/usr/bin/env python3
"""Phase 392: Seed 7's representation-residue evidence gate.

Post-Phase-340 Seed 7 (`input_byte_pathway_reconstruction_audit.py`, Phase
378/379) deliberately left three byte-pathway hypotheses unrun --
DOM-`textContent`-vs-copied-text divergence, HTML-entity decoding, and a
JavaScript UTF-16/low-byte conversion -- because grepping this project's
own records found no puzzle-era evidence for any of them, and running an
open-ended encoding-menu sweep without evidence would violate this
project's closed-candidate-universe discipline. That left them formally
*unrun*, not disproven.

This phase closes that ambiguity the right way: examine the actual
archived HTML source DBBI/FAED live in, and determine directly whether it
gives any of the three pathways something to act on. It tests only the
source, not new candidate strings.

Source: the same SHA-256-pinned local mirror file
`salphaseion_presentation_binding_audit.py`/`page_structure_audit.py`
already use as this project's authenticated SalPhaseIon page copy
(`gsmg-site-mirror/89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32.html`).

Evidence checks, each targeting exactly one pathway:

  1. **HTML entities.** A regex scan of the raw source for any
     `&name;`/`&#N;`/`&#xN;` reference. If none exist, there is nothing an
     entity-decoding step could act on -- the pathway requires the source
     to actually contain an entity in the first place.
  2. **Non-ASCII bytes.** A byte-level scan of the raw file for any byte
     `> 0x7F`. A JavaScript UTF-16/low-byte conversion pathway needs a
     multi-byte or non-ASCII source character to produce a divergent
     result in the first place; over pure ASCII, UTF-16 code units and
     UTF-8 bytes and Latin-1 bytes are all identical to the ASCII byte
     itself, so this pathway is moot even if some inline script existed.
  3. **Inline scripts.** Parses every `<script>` tag and separately checks
     each *inline* one (no `src`) for byte/encoding-conversion-relevant
     tokens (`charCodeAt`, `fromCharCode`, `TextEncoder`, `TextDecoder`,
     `normalize`, `utf16`, `utf-16`, `btoa`, `atob`). Confirms whether any
     such code exists to run at all.
  4. **Textarea DOM structure.** Parses the two `<textarea>` elements that
     hold DBBI/FAED and confirms neither has any nested child tag between
     its open and close tag. A textarea with no child markup has an
     `.value`/`.textContent` that is byte-identical to its flat source
     text -- there is no CSS-generated content, `<br>`, or hidden span
     that could make "what a user copies" differ from "what the DOM
     reports," independent of the entity/non-ASCII questions above.

Per the declared rule: a pathway with supporting evidence would be tested
next; a pathway with none is marked inapplicable to *this* source and left
there, not swept anyway and not declared formally impossible.
"""

import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from page_structure_audit import DEFAULT_HTML  # noqa: E402

EXPECTED_HTML_SHA256 = "b13cbc5c2935dc3e9ff8bf71681f2ef61317fefdce04159129877244a92a3947"

ENTITY_RE = re.compile(r"&(?:[a-zA-Z][a-zA-Z0-9]*|#[0-9]+|#x[0-9a-fA-F]+);")

BYTE_CONVERSION_TOKENS = (
    "charCodeAt", "fromCharCode", "TextEncoder", "TextDecoder",
    "normalize", "utf16", "utf-16", "btoa", "atob",
)


class _ScriptAndTextareaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []  # list of {"attrs": ..., "inline_text": str}
        self.textareas = []  # list of {"attrs": ..., "had_child_tag": bool}
        self._active_script = None
        self._active_textarea = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "script":
            self._active_script = {"attrs": dict(attrs), "inline_text": ""}
        elif tag == "textarea":
            self._active_textarea = {"attrs": dict(attrs), "had_child_tag": False}
        elif self._active_textarea is not None:
            self._active_textarea["had_child_tag"] = True

    def handle_startendtag(self, tag, attrs):
        if self._active_textarea is not None:
            self._active_textarea["had_child_tag"] = True

    def handle_data(self, data):
        if self._active_script is not None:
            self._active_script["inline_text"] += data

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "script" and self._active_script is not None:
            self.scripts.append(self._active_script)
            self._active_script = None
        elif tag == "textarea" and self._active_textarea is not None:
            self.textareas.append(self._active_textarea)
            self._active_textarea = None


def load_source(path=DEFAULT_HTML):
    raw = path.read_bytes()
    return raw, raw.decode("utf-8")


def check_html_entities(html_text):
    return ENTITY_RE.findall(html_text)


def check_non_ascii_bytes(raw_bytes):
    return [(i, b) for i, b in enumerate(raw_bytes) if b > 0x7F]


def check_inline_scripts(html_text):
    parser = _ScriptAndTextareaParser()
    parser.feed(html_text)
    inline = [s for s in parser.scripts if "src" not in s["attrs"]]
    flagged = []
    for s in inline:
        hits = [tok for tok in BYTE_CONVERSION_TOKENS if tok.lower() in s["inline_text"].lower()]
        if hits:
            flagged.append({"tokens": hits, "text_preview": s["inline_text"][:200]})
    return {
        "total_scripts": len(parser.scripts),
        "inline_scripts": len(inline),
        "external_scripts": len(parser.scripts) - len(inline),
        "flagged_inline_scripts": flagged,
    }, parser.textareas


def evidence_gate_report(path=DEFAULT_HTML):
    raw, text = load_source(path)
    sha256 = hashlib.sha256(raw).hexdigest()
    entities = check_html_entities(text)
    non_ascii = check_non_ascii_bytes(raw)
    script_report, textareas = check_inline_scripts(text)
    textarea_children = [t for t in textareas if t["had_child_tag"]]

    return {
        "source_path": str(path),
        "source_sha256": sha256,
        "html_entities_found": entities,
        "non_ascii_byte_count": len(non_ascii),
        "non_ascii_byte_offsets": non_ascii[:20],
        "script_report": script_report,
        "textarea_count": len(textareas),
        "textareas_with_child_tags": len(textarea_children),
        "verdict": {
            "html_entity_pathway_applicable": len(entities) > 0,
            "utf16_low_byte_pathway_applicable": len(non_ascii) > 0
                and len(script_report["flagged_inline_scripts"]) > 0,
            "textcontent_vs_copy_pathway_applicable": len(textarea_children) > 0,
        },
    }


def self_test():
    report = evidence_gate_report()
    assert report["source_sha256"] == EXPECTED_HTML_SHA256
    assert report["html_entities_found"] == []
    assert report["non_ascii_byte_count"] == 0
    assert report["script_report"]["total_scripts"] == 1
    assert report["script_report"]["inline_scripts"] == 0
    assert report["script_report"]["external_scripts"] == 1
    assert report["script_report"]["flagged_inline_scripts"] == []
    assert report["textarea_count"] == 2
    assert report["textareas_with_child_tags"] == 0
    v = report["verdict"]
    assert v["html_entity_pathway_applicable"] is False
    assert v["utf16_low_byte_pathway_applicable"] is False
    assert v["textcontent_vs_copy_pathway_applicable"] is False
    print(
        "[*] self-test OK: 0 HTML entities, 0 non-ASCII bytes, 0 inline "
        "scripts (1 external Cloudflare beacon only), 0 textarea child tags "
        "-- all three Seed 7 pathways inapplicable to the authenticated "
        "source, no encoding sweep warranted"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(evidence_gate_report(), indent=2))


if __name__ == "__main__":
    main()
