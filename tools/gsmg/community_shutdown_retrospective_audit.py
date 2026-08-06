#!/usr/bin/env python3
"""Follow-up to item 5's OSINT check (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md`
section 5 / `FINDINGS.md` Phase 154): a second Telegram export exists that
Phase 154 never covered.

`ChatExport_2026-07-26` ("GSMG Puzzle Solvers", 57,729 messages, 482 from the
creator) is the only corpus every prior phase in this project has ever used.
A separate, much larger export exists locally: "GSMG - Community & support
group" (public_supergroup id 1246576180), with three incremental snapshots on
disk -- `ChatExport_2026-07-29` (22,400 msgs) and `ChatExport_2026-07-29 (1)`
(12,300 msgs) are both strict prefixes of `ChatExport_2026-07-29 (2)`
(52,851 msgs, message ids 1-68682, spanning 2018-04-17 to 2026-07-28), which
is therefore the only one worth using. The creator has 5,419 messages there --
more than 10x the puzzle-solvers corpus.

This chat is the general trading-bot support group, not the puzzle channel,
and the creator actively enforces a "no puzzle talk here" house rule
throughout it (confirmed: 47 creator messages mention puzzle-adjacent terms,
nearly all of them exactly that rule being restated over 2019-2025). It is
NOT a hidden trove of puzzle clues. It does, however, contain the single most
candid message the creator has ever posted: an announcement (message 67741,
2026-04-13) that the GSMG.io company itself is shutting down after ~9 years,
including an origin-story retrospective that directly answers part of item 5
and bears on item 7:

* first-party confirmation the puzzle was "inspired by other crypto puzzles"
  and built in "two sloppy days ... zero polish" -- strengthens, doesn't
  contradict, Phase 154's existing "not a professional ARG designer" framing;
* the literal phrase "the better half" used autobiographically, for a real
  romantic partner ("JRK was visiting Sydney with the better half") -- this
  does NOT reopen the AES-negative results in Phase 151/152 (those tested
  specific candidate families, which remain negative regardless of
  interpretation), but it is important interpretive context: "half and
  better half" may be autobiographical rather than a Matrix/Symposium-style
  literary rebus. This script deliberately stops at testing PUBLIC phrases
  the creator chose to post themselves -- it does not attempt to identify
  real names, dates, or any other detail about the partner, which would be
  doxxing and out of scope regardless of puzzle relevance;
* confirms the puzzle is explicitly being kept running independently of the
  now-shut-down company ("That thing is still running, and we are keeping it
  alive");
* confirms the literal GSMG acronym expansion: "Globally Supporting My
  Generation" -- previously undocumented anywhere in this project.

This script verifies the exact quotes against the live export at run time
(never hardcoded from memory) and tests a small, bounded family of first-party
phrases from this specific message -- not a dictionary expansion.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)

COMMUNITY_EXPORT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)/result.json"
)
CREATOR_ID = "user9815232"
SHUTDOWN_MESSAGE_ID = 67741
EXPECTED_SUBSTRINGS = (
    "JRK was visiting Sydney with the better half",
    "Globally Supporting My Generation",
    "JRK got inspired by other crypto puzzles and spent two sloppy days "
    "throwing one together",
    "The very first name for this script was MR. ROIbot",
    "That thing is still running, and we are keeping it alive",
)

FIXED_CANDIDATES = (
    "SYDNEY",
    "THEBETTERHALF",
    "GLOBALLYSUPPORTINGMYGENERATION",
    "MRROIBOT",
    "ALLGOODTHINGSCOMETOANEND",
    "NINEYEARCHAOSTOUR",
    "TWOSLOPPYDAYS",
)


def flatten(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_message(message_id, export_path=COMMUNITY_EXPORT):
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    for message in payload["messages"]:
        if message.get("id") == message_id:
            if message.get("from_id") != CREATOR_ID:
                raise AssertionError(f"message {message_id} is not creator-authored")
            return flatten(message.get("text", ""))
    raise AssertionError(f"message {message_id} not found in {export_path}")


def verify_quote(export_path=COMMUNITY_EXPORT):
    text = load_message(SHUTDOWN_MESSAGE_ID, export_path)
    normalized = re.sub(r"\s+", " ", text)
    missing = [s for s in EXPECTED_SUBSTRINGS if s not in normalized]
    if missing:
        raise AssertionError(f"expected substrings not found verbatim: {missing}")
    return True


def oracle_check(candidates, blobs):
    tested_keystrings = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested_keystrings:
                    continue
                tested_keystrings.add(keystring)

                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((candidate, keystring, result))

                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))

                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))

                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((candidate, keystring, result))

    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "hits": hits,
    }


def print_report(quote_verified, result=None):
    print(f"[*] shutdown retrospective quote verified against live export: {quote_verified}")
    print(f"[*] fixed candidate family ({len(FIXED_CANDIDATES)}):")
    for candidate in FIXED_CANDIDATES:
        print(f"    {candidate!r}")
    if result is not None:
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


def self_test():
    assert verify_quote()
    assert len(FIXED_CANDIDATES) == 7
    print("[*] self-test OK: shutdown retrospective quote verified verbatim")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=COMMUNITY_EXPORT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    quote_verified = verify_quote(args.export)

    result = None
    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(FIXED_CANDIDATES, blobs)

    print_report(quote_verified, result)


if __name__ == "__main__":
    main()
