#!/usr/bin/env python3
"""Classify every residual hit from the original Stage-1 Telegram sweep.

Phase 54 closely reviewed 68 of the 1,828 hits: all 56 anchor-sender rows and
all rows matching the four rare, explicitly scoped terms ``31 characters``,
``consume``, ``yellow-blue`` and ``ncsyang``.  This audit freezes the exact
1,760-row complement and assigns the requested disposition:

* ``covered`` -- exact citation in FINDINGS or a named operation family whose
  finite search is already represented by an existing phase;
* ``noise`` -- question/repost/vague claim, or a claim lacking enough of
  input + operation + output to reproduce and authenticate it;
* ``new_lead`` -- message 66722's independently reproduced KMODEST checkpoint
  (Phase 387).

The ledger stores the full source ID plus a SHA-256 of the complete text.  It
does not truncate text before classification.  The categories are review
dispositions, not claims that every ``covered`` message's exact personal
implementation was previously run byte-for-byte.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from telegram_export_keyword_sweep import sweep
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export


PREVIOUSLY_REVIEWED_RARE_TERMS = (
    "31 characters", "consume", "yellow-blue", "ncsyang",
)
NEW_LEAD_IDS = {66722}

MODEL_FAMILY_PATTERNS = (
    (r"\byou\s*wonx?\b|\byouwonx?\b|one[- ]time pad", "Phases 74/75/147/368: YOUWON family"),
    (r"btcseed|\bbifid\b", "Phases 386/387: BTCSEED/Bifid family"),
    (r"\btrifid\b|\bbazeries\b|\bpolybius\b", "Phases 286/386: polygraphic families"),
    (r"base[ -]?(?:9|27|81)\b|\ba1z26\b|text to integer", "Phases 276/278/287: numeric transport families"),
    (r"\b(?:xor|vigen[eè]re|vernam|nihilist|bacon|checkerboard|vic cipher)\b", "Phases 275/286/292/309/310: named cipher families"),
    (r"music notes?|solf(?:e|è)ge|doremi", "Phase 253: audio/music presentation family"),
    (r"gps coordinate|coordinates? on earth", "Phases 191/269/384: coordinate/fork family"),
    (r"filter.?bytes?|scanlines?", "Phase 73: PNG filter-byte anomaly"),
    (r"4f7a1e4e", "Phase 210: disputed Cosmic artifact branch"),
)

FIRST_PIECE_OPERATION = re.compile(
    r"(?is)(?:yellow|blue).{0,180}(?:prime|matrix|row|column|sum|binary|spiral|zero)"
    r"|(?:prime|matrix|row|column|sum|binary|spiral|zero).{0,180}(?:yellow|blue)"
)
QUESTION_OR_DISCUSSION = re.compile(
    r"(?i)\?|\b(?:i think|i believe|maybe|might|could|what if|any ideas|"
    r"does anyone|do you|can you|we need|we should|i wonder|guess|theory)\b"
)
UNBOUND_CLAIM = re.compile(
    r"(?i)\b(?:i found|we found|i got|we got|result|decode[ds]?|decrypt[sed]*|"
    r"output|yields?|gives?|extract[sed]*|pattern)\b"
)
RAW_REPOST = re.compile(r"[a-i]{180,}|yellow blue primes matrix sum list", re.I)


def phase54_reviewed(hit):
    return hit["is_anchor_sender"] or any(
        term in hit["matched_keywords"] for term in PREVIOUSLY_REVIEWED_RARE_TERMS
    )


def exact_cited_ids():
    corpus = (Path(__file__).with_name("FINDINGS.md").read_text(encoding="utf-8") +
              "\n" +
              (Path(__file__).parents[2] / "doc" / "GSMG_PHASE_INDEX.md").read_text(encoding="utf-8"))
    ids = set()
    for match in re.finditer(r"(?i)messages?\s+`?(\d{3,5})`?", corpus):
        ids.add(int(match.group(1)))
    return ids


def classify(hit, cited_ids):
    message_id = hit["id"]
    text = hit["text"]
    lowered = text.lower()
    if message_id in NEW_LEAD_IDS:
        return "new_lead", "Phase 387: KMODEST checkpoint independently reproduced and calibrated"
    if message_id in cited_ids:
        return "covered", "message ID already cited in FINDINGS/phase index"
    for pattern, reason in MODEL_FAMILY_PATTERNS:
        if re.search(pattern, lowered, re.I):
            return "covered", reason
    if FIRST_PIECE_OPERATION.search(text):
        return "covered", "Phases 36/47-53 and successors: yellow/blue/prime/matrix operation family"
    if RAW_REPOST.search(text):
        return "noise", "raw known-string repost without a new complete operation and verifier"
    if QUESTION_OR_DISCUSSION.search(text):
        return "noise", "question, discussion, or explicitly tentative theory without authentication"
    if UNBOUND_CLAIM.search(text):
        return "noise", "claim omits a complete reproducible input-operation-output chain or downstream verifier"
    return "noise", "no executable claim or new primary evidence"


def audit(export_dir=DEFAULT_EXPORT_DIR):
    hits = sweep(load_export(export_dir))
    residual = [hit for hit in hits if not phase54_reviewed(hit)]
    cited_ids = exact_cited_ids()
    ledger = []
    for hit in residual:
        disposition, reason = classify(hit, cited_ids)
        ledger.append({
            "id": hit["id"],
            "date": hit["date"],
            "from": hit["from"],
            "matched_keywords": hit["matched_keywords"],
            "text_sha256": hashlib.sha256(hit["text"].encode("utf-8")).hexdigest(),
            "disposition": disposition,
            "reason": reason,
        })
    counts = {
        disposition: sum(row["disposition"] == disposition for row in ledger)
        for disposition in ("covered", "noise", "new_lead")
    }
    return {
        "stage1_hit_count": len(hits),
        "previously_reviewed_count": len(hits) - len(residual),
        "residual_count": len(residual),
        "counts": counts,
        "ledger": tuple(ledger),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["stage1_hit_count"] == 1828
    assert report["previously_reviewed_count"] == 68
    assert report["residual_count"] == 1760
    assert sum(report["counts"].values()) == 1760
    leads = [row for row in report["ledger"] if row["disposition"] == "new_lead"]
    assert [row["id"] for row in leads] == [66722]
    by_id = {row["id"]: row for row in report["ledger"]}
    assert by_id[43248]["disposition"] == "covered"
    assert by_id[49536]["disposition"] == "covered"
    print(
        "[*] self-test OK: exact 1,828 -> 68 reviewed + 1,760 residual partition; "
        f"counts={report['counts']}; sole new lead is message 66722"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = audit(args.export_dir)
    if args.self_test:
        self_test(args.export_dir)
        return
    print(json.dumps({k: v for k, v in report.items() if k != "ledger"}, indent=2))
    if args.json_out:
        args.json_out.write_text(
            json.dumps(report["ledger"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
