#!/usr/bin/env python3
"""Test whether creator-authored ``yinyang`` binds the next COSMIC textarea.

This is a structural/provenance audit, not a password oracle.  It gives the
nearer SalPhaseIon self-binding and creator usage of "next phase" explicit
falsification gates before allowing the semantic Cosmic Duality match to carry
any downstream interpretation.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import cosmic_raw_digest_checkpoint_audit as disputed
import salphaseion_presentation_binding_audit as presentation
from page_structure_audit import DEFAULT_HTML, audit as page_audit
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


ROOT = Path(__file__).resolve().parents[2]
BOOK_PATH = ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
BOOK_SHA256 = "69e8021309957a204628c3c0045108b8f69f50b0a1da7a76abfe6783b36d4c3d"
CREATOR_ID = "user9815232"
TERM_IDS = (231, 660, 866, 874, 879, 898, 2024, 3348, 4694, 4771, 6497, 39237, 60314)
NEXT_IDS = (3348, 4694, 4771, 39237, 60314)
QUESTION_ID = 39233
ANSWER_ID = 39237


def normalized(text):
    return " ".join(text.split())


def creator_usage(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    messages = {message["id"]: message for message in data["messages"]}
    creator = {
        message_id: plain_text(message)
        for message_id, message in messages.items()
        if message.get("from_id") == CREATOR_ID
    }
    singular_term = re.compile(r"\b(?:phase|stage|page|section)\b", re.I)
    next_term = re.compile(r"\bnext\s+(?:phase|stage|page|section)\b", re.I)
    term_ids = tuple(message_id for message_id, text in creator.items() if singular_term.search(text))
    next_ids = tuple(message_id for message_id, text in creator.items() if next_term.search(text))
    if term_ids != TERM_IDS or next_ids != NEXT_IDS:
        raise AssertionError("creator phase/stage/page/section inventory drifted")

    question = plain_text(messages[QUESTION_ID])
    answer = plain_text(messages[ANSWER_ID])
    if messages[ANSWER_ID].get("reply_to_message_id") != QUESTION_ID:
        raise AssertionError("creator next-phase reply edge drifted")
    if question != "is yinyang found after decoding an AES ciphertext?":
        raise AssertionError("yin-yang question text drifted")
    if answer != "It’s the next phase, but I await the day someone finally gets there.":
        raise AssertionError("creator next-phase answer text drifted")

    rows = tuple(
        {
            "message_id": message_id,
            "text": creator[message_id],
            "classification": "solver_progression",
        }
        for message_id in next_ids
    )
    page_or_section = tuple(
        row for row in rows
        if re.search(r"\bnext\s+(?:page|section)\b", row["text"], re.I)
    )
    return {
        "singular_term_message_ids": term_ids,
        "next_term_message_ids": next_ids,
        "next_term_rows": rows,
        "next_page_or_section_rows": page_or_section,
        "direct_exchange": {
            "question_id": QUESTION_ID,
            "question": question,
            "answer_id": ANSWER_ID,
            "answer": answer,
            "answer_classification": "solve progression; no yes/no AES or DOM referent",
        },
        "dom_usage_precedent_found": bool(page_or_section),
    }


def book_semantics(book_path=BOOK_PATH):
    book_path = Path(book_path)
    text = book_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != BOOK_SHA256:
        raise AssertionError(f"book transcript hash drifted: {digest}")
    anchors = (
        '## p.8-9 — sidebar "Harmony from a Divided Universe"',
        "yin and yang embody almost every conceivable duality.",
        "a state of cosmic balance gracefully depicted in the classical image at far left.",
    )
    flat = normalized(text)
    if any(normalized(anchor) not in flat for anchor in anchors):
        raise AssertionError("book semantic anchors drifted")
    return {
        "path": str(book_path),
        "sha256": digest,
        "page": "8-9",
        "heading": "Harmony from a Divided Universe",
        "exact_anchors": anchors[1:],
        "supports": "semantic association between yin-yang and cosmic duality/balance",
        "does_not_supply": "a ciphertext consumer edge or password operation",
    }


def audit(export_dir=DEFAULT_EXPORT_DIR, html_path=DEFAULT_HTML, book_path=BOOK_PATH):
    page = page_audit(Path(html_path))
    shown = presentation.audit(Path(html_path))
    names = tuple(segment["name"] for segment in page["salphaseion"]["segments"])
    local_tail = (
        "decimal_instruction_2", "z_separator_3", "hash_prefix",
        "salphaseion_aes_prefix", "abba_enter_instruction",
        "salphaseion_aes_suffix", "hash_suffix",
    )
    if names[-7:] != local_tail:
        raise AssertionError("SalPhaseIon local instruction/ciphertext order drifted")
    if tuple(page["dom_order"]) != ("SalPhaseIon", "Cosmic Duality"):
        raise AssertionError("page DOM order drifted")

    usage = creator_usage(export_dir)
    semantics = book_semantics(book_path)
    contamination = {
        "scope": "only the disputed Phase-210 community derivation",
        "tokens": disputed.TOKENS,
        "xor_hex": disputed.EXPECTED_XOR_HEX,
        "payload_sha256": disputed.EXPECTED_PAYLOAD_SHA256,
        "addresses": disputed.EXPECTED_ADDRESSES,
        "excluded_from_support": True,
        "cosmic_blob_authenticated": (
            page["cosmic_duality"]["matches_known_blob"]
            and shown["headings"][-1] == "Cosmic Duality"
        ),
    }
    gates = {
        "1_structural_binding": {
            "pass": False,
            "reason": (
                "thispassword, sha256, enter, and both halves of SALPH occur in one "
                "SalPhaseIon stream; no redirect binds those instructions to COSMIC"
            ),
        },
        "2_book_semantics": {
            "pass": True,
            "weight": "supportive_not_dispositive",
            "reason": "pages 8-9 explicitly connect yin-yang, duality, and cosmic balance",
        },
        "3_creator_usage_precedent": {
            "pass": usage["dom_usage_precedent_found"],
            "reason": (
                "all five exact 'next phase/stage' uses describe solver progression; "
                "none says next page or next section"
            ),
        },
        "4_dom_adjacency": {
            "pass": True,
            "weight": "necessary_but_trivial",
            "reason": "Cosmic Duality is the second of exactly two headings/textareas",
        },
        "5_contamination_guard": {
            "pass": contamination["cosmic_blob_authenticated"],
            "reason": (
                "COSMIC itself is authenticated; only the exact seven-token Phase-210 "
                "pipeline, checkpoint, and derived addresses are excluded"
            ),
        },
    }
    promoted = gates["1_structural_binding"]["pass"] and gates["3_creator_usage_precedent"]["pass"]
    return {
        "hypothesis": "creator yinyang/next-phase label redirects SalPhaseIon instructions to COSMIC",
        "salphaseion_local_tail": local_tail,
        "creator_usage": usage,
        "book_semantics": semantics,
        "presentation": {
            "dom_order": tuple(page["dom_order"]),
            "headings": shown["headings"],
            "binding_candidates_found": shown["binding_candidates_found"],
        },
        "contamination_guard": contamination,
        "gates": gates,
        "promotion": {
            "promoted": promoted,
            "required_gates": ("1_structural_binding", "3_creator_usage_precedent"),
        },
        "verdict": (
            "Do not promote SalPhaseIon -> COSMIC. The title/book resonance is real "
            "and COSMIC has clean authenticated provenance, but the nearer same-stream "
            "SALPH binding is structurally stronger and creator usage supplies no "
            "precedent for reading 'next phase' as the next DOM section."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR, html_path=DEFAULT_HTML, book_path=BOOK_PATH):
    report = audit(export_dir, html_path, book_path)
    assert not report["gates"]["1_structural_binding"]["pass"]
    assert report["gates"]["2_book_semantics"]["pass"]
    assert not report["gates"]["3_creator_usage_precedent"]["pass"]
    assert report["gates"]["4_dom_adjacency"]["weight"] == "necessary_but_trivial"
    assert report["gates"]["5_contamination_guard"]["pass"]
    assert not report["promotion"]["promoted"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: semantic match retained; cross-textarea promotion rejected")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--book", type=Path, default=BOOK_PATH)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export_dir, args.html, args.book) if args.self_test else audit(args.export_dir, args.html, args.book)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
