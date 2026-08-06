#!/usr/bin/env python3
"""Audit primary evidence for what follows the exact 31-character extraction.

Phase 48 reconstructed the selector that maps the 91-character Phase 3.2
plaintext to Denis Golovkin's posted 31-character string. This audit asks the
narrower next question: does the archived transcript specify an operation that
consumes those 31 characters?

The distinction matters:

* selection is mechanically reconstructed;
* literal ``yang`` is present in the selected output;
* Denis proposed anagramming, but explicitly reported that it did not produce
  the key needed to proceed;
* the creator responded only to Denis's abstract pre-reveal claim and did not
  confirm the later concrete extraction or any post-selection operation.

The plain-text archive was produced by a parser that skips messages without a
text node and discards reply metadata. A later Telegram JSON export recovered
Denis's guide as message 60325's reply target (message 39937). This module
continues to audit the narrower textual claim: no creator-supported
post-selection operator follows Denis's concrete extraction. The recovered
guide's separate, DBBI-direct matrix operation is audited elsewhere.
"""

import argparse
import re
from collections import Counter
from pathlib import Path

from denis_prime_extraction_audit import SOURCE, TARGET
from yin_yang_transition_audit import transcript_evidence as yin_yang_transcript_evidence

PROJECTS_ROOT = Path(__file__).resolve().parents[3]
ARCHIVE_ROOT = PROJECTS_ROOT / "gsmgio-5btc-puzzle" / "_work"
DEFAULT_CHAT = ARCHIVE_ROOT / "chat_transcript.txt"
DEFAULT_CREATOR = ARCHIVE_ROOT / "creator_jrk.txt"
DEFAULT_PARSER = ARCHIVE_ROOT / "parse_chat.py"

HEADER_RE = re.compile(r"^=== \[(.*?)\] (.*?)$", re.MULTILINE)

ABSTRACT_CLAIM = (
    "If I say that someone applied specific prime inexes to specific last words "
    'and extracted like 30 to 31 bytes, that include both "ying yang" and '
    '"salvation", would you change your mind?'
)
CREATOR_RESPONSE = (
    "I only need to look at the address. If any of you reaches the next phase, "
    "the price is taken in no-time."
)
GUIDE_CAPTION = (
    "Here was a guide to yellow-blue-primes.\n"
    "Notice that 'B' for blue and both 'BE' for yellow participate."
)
TARGET_REVEAL = (
    'Then, if we extract chars matching "YBprimes" from the "incaseyoumanage..." '
    "string (that pretty aligns with 'dbbibf..' by length), we'd get:\n"
    f"{TARGET}"
)
LITERAL_YANG = "Notice that 'yang' sits here in plain sight."
ANAGRAM_PROPOSAL = (
    "Might be a phrase anagram.\n"
    "I've brute-forced few trillions of anagrams, but didn't find em to be the key to proceed."
)
CHAIN_INTERPRETATION = (
    'We took "yellow blue primes" of dbbi to filter indexes that match B or BE '
    "chars vs indexes that don't match"
)
MANUAL_ANAGRAMS = (
    "reach a safe ying yang salvation case",
    "a safe ying yang race salvation chase",
    "yingyang salvation each caesar safe",
    "a canonical saga say everything safe",
)


def parse_messages(text):
    matches = list(HEADER_RE.finditer(text))
    messages = []
    for index, match in enumerate(matches):
        body_start = match.end() + 1
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        messages.append(
            {
                "timestamp": match.group(1),
                "sender": match.group(2),
                "text": text[body_start:body_end].strip(),
                "offset": match.start(),
            }
        )
    return messages


def find_unique_message(messages, sender, substring):
    matches = [
        message
        for message in messages
        if message["sender"] == sender and substring in message["text"]
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one message from {sender!r} containing {substring!r}, "
            f"found {len(matches)}"
        )
    return matches[0]


def normalize_letters(text):
    return "".join(character for character in text.lower() if character.isalpha())


def audit(
    chat_path=DEFAULT_CHAT,
    creator_path=DEFAULT_CREATOR,
    parser_path=DEFAULT_PARSER,
):
    chat_text = chat_path.read_text(encoding="utf-8", errors="replace")
    creator_text = creator_path.read_text(encoding="utf-8", errors="replace")
    parser_text = parser_path.read_text(encoding="utf-8", errors="replace")
    messages = parse_messages(chat_text)

    abstract_claim = find_unique_message(messages, "Denis Golovkin", ABSTRACT_CLAIM)
    creator_response = find_unique_message(messages, "Jrk Bgrt", CREATOR_RESPONSE)
    guide_caption = find_unique_message(messages, "Denis Golovkin", GUIDE_CAPTION)
    target_reveal = find_unique_message(messages, "Denis Golovkin", TARGET_REVEAL)
    literal_yang = find_unique_message(messages, "Denis Golovkin", LITERAL_YANG)
    anagram_proposal = find_unique_message(messages, "Denis Golovkin", ANAGRAM_PROPOSAL)
    chain_interpretation = find_unique_message(
        messages,
        "Denis Golovkin",
        CHAIN_INTERPRETATION,
    )

    ordered = (
        abstract_claim,
        creator_response,
        guide_caption,
        target_reveal,
        literal_yang,
        anagram_proposal,
        chain_interpretation,
    )
    if [message["offset"] for message in ordered] != sorted(
        message["offset"] for message in ordered
    ):
        raise AssertionError("transition evidence is absent or out of chronological order")

    manual_anagram_records = []
    for phrase in MANUAL_ANAGRAMS:
        normalized = normalize_letters(phrase)
        manual_anagram_records.append(
            {
                "phrase": phrase,
                "normalized": normalized,
                "length": len(normalized),
                "exact_multiset": Counter(normalized) == Counter(TARGET),
            }
        )

    yin_yang_evidence = yin_yang_transcript_evidence(chat_path)
    creator_after_concrete_reveal = [
        message
        for message in messages
        if (
            message["sender"] == "Jrk Bgrt"
            and target_reveal["offset"] < message["offset"] < chain_interpretation["offset"]
        )
    ]

    parser_skips_non_text = (
        "if not tm:" in parser_text
        and "continue" in parser_text[parser_text.find("if not tm:"):][:100]
    )
    guide_has_attachment_marker = any(
        marker in guide_caption["text"].lower()
        for marker in ("attached", "attachment", ".png", ".jpg", ".jpeg", ".webp", "file:")
    )

    literal_hits = {
        word: word in TARGET
        for word in ("yin", "ying", "yang", "salvation", "everything")
    }

    return {
        "source_length": len(SOURCE),
        "selected_length": len(TARGET),
        "selected": TARGET,
        "selected_occurrences_in_archive": chat_text.count(TARGET),
        "literal_hits": literal_hits,
        "manual_anagrams": tuple(manual_anagram_records),
        "timeline": tuple(
            {
                "timestamp": message["timestamp"],
                "sender": message["sender"],
                "label": label,
            }
            for label, message in (
                ("abstract claim", abstract_claim),
                ("creator response", creator_response),
                ("missing-guide caption", guide_caption),
                ("concrete extraction", target_reveal),
                ("literal yang observation", literal_yang),
                ("failed anagram proposal", anagram_proposal),
                ("community chain interpretation", chain_interpretation),
            )
        ),
        "creator_response_precedes_concrete_reveal": (
            creator_response["offset"] < target_reveal["offset"]
        ),
        "creator_messages_after_concrete_reveal": tuple(creator_after_concrete_reveal),
        "creator_names_target": TARGET in creator_text,
        "creator_names_anagram": "anagram" in creator_text.lower(),
        "bingo_confirms_looking_forward": any(
            "Looking Forward" in step
            for step in yin_yang_evidence["march_2026_order"][1:]
        ),
        "archive_parser_skips_media_only": parser_skips_non_text,
        "guide_caption_contains_attachment_marker": guide_has_attachment_marker,
        "supported_operations": (
            "apply the recovered 31-position mask to the aligned 91-character plaintext",
            "inspect the selected output for literal text",
        ),
        "unsupported_or_failed_operations": (
            "anagram the 31-character multiset (community-proposed and reported unsuccessful)",
            "treat the four manually crafted exact anagrams as unique outputs",
            "apply an unspecified matrixsumlist transform after selection",
        ),
        "verdict": (
            "No creator-supported post-selection operator is present in the archived "
            "text. The 31 characters may be a terminal recognition/checkpoint output; "
            "the archive does not prove that another transform must consume them."
        ),
    }


def self_test():
    report = audit()
    assert report["source_length"] == 91
    assert report["selected_length"] == 31
    assert report["selected_occurrences_in_archive"] == 1
    assert report["literal_hits"] == {
        "yin": False,
        "ying": False,
        "yang": True,
        "salvation": False,
        "everything": False,
    }
    assert all(record["length"] == 31 for record in report["manual_anagrams"])
    assert all(record["exact_multiset"] for record in report["manual_anagrams"])
    assert report["creator_response_precedes_concrete_reveal"]
    assert report["creator_messages_after_concrete_reveal"] == ()
    assert not report["creator_names_target"]
    assert not report["creator_names_anagram"]
    assert not report["bingo_confirms_looking_forward"]
    assert report["archive_parser_skips_media_only"]
    assert not report["guide_caption_contains_attachment_marker"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat", type=Path, default=DEFAULT_CHAT)
    parser.add_argument("--creator", type=Path, default=DEFAULT_CREATOR)
    parser.add_argument("--parser", type=Path, default=DEFAULT_PARSER)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("[*] self-test OK")
        return

    report = audit(args.chat, args.creator, args.parser)
    print(f"[*] selected {report['selected_length']}: {report['selected']}")
    print(f"[*] literal hits: {report['literal_hits']}")
    print("[*] timeline:")
    for item in report["timeline"]:
        print(f"    {item['timestamp']} | {item['sender']}: {item['label']}")
    print("[*] manually crafted anagrams:")
    for item in report["manual_anagrams"]:
        print(
            f"    exact_multiset={item['exact_multiset']} "
            f"length={item['length']} {item['phrase']!r}"
        )
    print(
        "[*] creator response precedes concrete reveal: "
        f"{report['creator_response_precedes_concrete_reveal']}"
    )
    print(
        "[*] creator messages after concrete reveal in bounded exchange: "
        f"{len(report['creator_messages_after_concrete_reveal'])}"
    )
    print(
        "[*] parser skips media-only messages: "
        f"{report['archive_parser_skips_media_only']}"
    )
    print(f"[*] verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
