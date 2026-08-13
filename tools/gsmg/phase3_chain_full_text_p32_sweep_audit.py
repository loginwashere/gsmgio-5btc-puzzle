#!/usr/bin/env python3
"""Comprehensive, non-cherry-picked sentence-level sweep of the ENTIRE Phase
2 -> Phase 3 -> Phase 3.2 decrypted text chain against all four blobs.

Phase 265 tested only a hand-picked subset of the Phase 3.2 monologue
("source codes"/"prime basics"/"23 ciphers"/etc.). Phase 266 tested only
reuse of Phase 3's seven password *parts*. Neither covers the much larger
body of ordinary prose in this same decrypted chain -- the Phase 2 result,
the Phase 3 result that leads into 3.2, and the rest of the Phase 3.2
Architect monologue beyond the one sentence Phase 265 focused on. This
module closes that gap by taking every decrypted-text sentence mechanically
(split on `.`/`?`/`!`, not hand-selected) rather than picking phrases that
looked interesting.

Every source string below is copied verbatim from README.md (re-read via
the file itself in `self_test`, not retyped from memory) and is one of:
  - the Phase 2 AES-decrypted result (SHA256(causality)),
  - the Phase 3 AES-decrypted result that leads into Phase 3.2,
  - the Phase 3.2 AES-decrypted Architect monologue, both the EBCDIC/
    Beaufort-decoded "YOUR LIFE IS THE SUM..." speech and the plain
    surrounding text ("Raising the stakes...").
Non-text material in the same decrypted payload (the garbled EBCDIC block
before Beaufort decode, the raw digit stream, the base64 blobs themselves)
is excluded -- it isn't prose and has its own dedicated coverage elsewhere.
"""

import argparse
import json
import re
from pathlib import Path

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"

PHASE2_TEXT = (
    "The ironic 2name of the keymakers trying to protect the current "
    "digital powers which are still in severe danger due to the "
    "keymaker's way of security by hiding, nearly unprotected, in plain "
    "sight. {eps3.4_[in one of the valleys of Phillip]runtime-error.r00., "
    "where daughters hit magic keypads} When this fails.. Crypto finally "
    "to the latin 3Moon? Tell me, 4How so mate?"
)

PHASE3_TEXT = (
    "What if the merovingian is wrong. What instead of causality "
    "something else could be ours? Therefor, if so, the ...... is ours. "
    "The thinker's 1name behind all of that would grant you access to "
    "the next step (of humanity). Definitely look into his works might "
    "you have time. "
    "I just passed a cheshire cat and I'm getting fed up with this "
    "puzzle.. It's taking forever. But, How long is forever? I don't "
    "know, but just add giveit in front of the answer and you can fall "
    "in the keyhole. "
    "3.The fundamental limit to the precision with which certain pairs "
    "of physical properties are know. "
    "Phase 3.2 is ciphered with aes-256-cbc base64 and a sha256 pw, yet "
    "again."
)

PHASE32_PLAIN_TEXT = (
    "I've been waiting for you. You have many questions, and although "
    "the process has altered your consciousness, you remain irrevocably "
    "human. Ergo, some of my answers you will understand, and some of "
    "them you will not. Concordantly, while your first question may be "
    "the most pertinent, you may or may not realize it is also "
    "irrelevant. "
    "... am I here? Wake up, you... I've designed you a beautiful "
    "strategic position. One for one, four for one. "
    "Raising the stakes without extra chances of winning. A fubcd-king "
    "& oracle-queen, thingky mvps, on a sad board but as wide as the "
    "first one seen."
)

# The Beaufort-decoded Architect speech has NO punctuation at all in the
# README (unlike every other decrypted text here) -- classical-cipher
# decodes typically drop it. A period/question-mark split therefore
# collapses this whole ~1,000-word block into a single "sentence," silently
# dropping the mechanical-splitting principle for exactly the block with the
# most untested prose. Split on its own original line breaks instead (each
# line below is one verbatim README.md line, in order) -- still a mechanical,
# source-defined boundary, just a different one dictated by the absence of
# punctuation rather than by hand-picking clause breaks.
PHASE32_ARCHITECT_SPEECH_LINES = (
    "YOUR LIFE IS THE SUM OF A REMAINDER OF AN UNBALANCED EQUATION INHERENT TO THE PROGRAMMING OF THIS PUZZLE",
    "YOU ARE THE EVENTUALITY OF AN ANOMALY WHICH DESPITE MY SINCEREST EFFORTS I HAVE BEEN UNABLE TO ELIMINATE",
    "FROM WHAT IS OTHERWISE A HARMONY OF MATHEMATICAL PRECISION WHILE IT REMAINS A BURDEN TO SEDULOUSLY AVOID IT",
    "IT IS NOT UNEXPECTED AND THUS NOT BEYOND A MEASURE OF CONTROL WHICH HAS LED YOU INEXORABLY HERE YOU",
    "YOU HAVEN'T ANSWERED MY QUESTION ME QUITE RIGHT INTERESTING THAT WAS QUICKER THAN THE OTHERS PLEASE IF YOU",
    "FIND A WAY TO COMPLETE THE LAST PART OF THE PUZZLE TAKE THE PRIVATE KEY YOUVE EARNED IT BUT PLEASE TAKE",
    "THIS TO HEART THAT WHAT A WISEMAN ABOVE HINTED AT IS WORTH HUNDRED FOURTY OF THE INVESTMENT THAT'S",
    "WHAT US GUYS AT GSMG ARE TRYING TO ACCOMPLISH IN THE END PLEASE JUST HELP US BUILD IT INSTEAD OF JUST",
    "WAISTING YOUR LIFETIME BY HUNTING FOR WORTHLESS PRICES AND THROPHIES LIKE THIS I'M SORRY TO",
    "TELL YOU THAT YOUVE COME THIS FAR BUT YOU'LL NEVER FINISH THE LAST TASK I EXPECT YOU TO SAY BULLSHIT",
    "WELL DENIAL IS THE MOST PREDICTABLE OF ALL HUMAN RESPONSES BUT REST ASSURED THIS WILL NOT BE THE LAST TIME",
    "I HAVE DESTROYED A RESTLESS SOUL AND I HAVE BECOME EXCEEDINGLY EFFICIENT AT IT THE FUNCTION OF THE YOU IS",
    "NOW TO RETURN TO THE SOURCE CODES ALLOWING A TEMPORARY DISSEMINATION OF THE CODE YOU HOPEFULLY CARRY",
    "REINSERTING THE PRIME BASICS AFTER WHICH YOU WILL BE REQUIRED TO SELECT FROM OVER TWENTY-THREE CIPHERS",
    "SIXTEEN ENCRYPTIONS AND OR SEVEN INTERTWINED PASSWORDS TO FIND THE ACTUAL PRIVATE KEYNOTE THAT ALSO",
    "BRUTE FORCING MIGHT BE REQUIRED FAILURE TO COMPLY WITH THIS PROCESS WILL RESULT IN A CATACLYSMIC",
    "SYSTEM CRASH KILLING YOUR WILLPOWER WHICH COUPLED WITH THE EXTERMINATION OF YOUR WILL TO LIVE AND WILL",
    "ULTIMATELY RESULT IN THE EXTINCTION OF THE ENTIRENESS OF YOURSELF SELF GOOD LUCK NEVERTHELESS I REALLY",
    "HOPE YOURE THE ONE CIAO BELLA O",
)

SOURCE_TEXTS = {
    "phase2": PHASE2_TEXT,
    "phase3": PHASE3_TEXT,
    "phase32_plain": PHASE32_PLAIN_TEXT,
}

# README.md excerpts each source text must still contain verbatim, so this
# module fails loudly rather than silently drifting from the live document.
README_ANCHORS = (
    "The ironic 2name of the keymakers",
    "What if the merovingian is wrong",
    "I've been waiting for you",
    "YOUR LIFE IS THE SUM OF A REMAINDER",
    "HOPE YOURE THE ONE CIAO BELLA O",
)

SENTENCE_SPLIT_RE = re.compile(r"[.?!]+")


def sentences(text):
    """Mechanically split on sentence-ending punctuation; no hand selection."""
    pieces = SENTENCE_SPLIT_RE.split(text)
    return tuple(
        piece.strip() for piece in pieces if len(piece.strip()) >= 4
    )


def candidate_sentences():
    seen = set()
    ordered = []
    for source, text in SOURCE_TEXTS.items():
        for sentence in sentences(text):
            key = sentence.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(sentence)
    for line in PHASE32_ARCHITECT_SPEECH_LINES:
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(line)
    return tuple(ordered)


def material_family(candidates, blobs):
    materials = {}
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=True):
                materials.setdefault(keystr.encode("utf-8"), set()).add(candidate)
    hits = []
    for material, sources in sorted(materials.items()):
        for hit in passphrase_hits(material, blobs):
            hits.append({
                "sources": tuple(sorted(sources)),
                "material_hex": material.hex(),
                **hit,
            })
    return {
        "candidate_count": len(candidates),
        "unique_material_count": len(materials),
        "hits": hits,
    }


def audit():
    candidates = candidate_sentences()
    report = material_family(candidates, BLOBS)
    return {
        "candidates": candidates,
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    readme_text = README_PATH.read_text(encoding="utf-8")
    for anchor in README_ANCHORS:
        if anchor not in readme_text:
            raise AssertionError(f"README.md anchor drifted: {anchor!r}")

    report = audit()
    assert report["candidate_count"] == len(candidate_sentences())
    assert report["candidate_count"] >= 45, report["candidate_count"]
    assert any("SIXTEEN ENCRYPTIONS" in c for c in report["candidates"])
    assert any("SOURCE CODES" in c for c in report["candidates"])
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} mechanically-split "
        f"sentences from the full Phase 2/3/3.2 decrypted text chain "
        f"(README.md anchors verified live) / "
        f"{report['unique_material_count']} unique key materials against "
        f"all 4 tracked blobs, 0 hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    print(json.dumps({k: v for k, v in report.items() if k != "candidates"}, indent=2, ensure_ascii=False))
    print(f"candidates: {len(report['candidates'])}")


if __name__ == "__main__":
    main()
