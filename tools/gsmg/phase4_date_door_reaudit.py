#!/usr/bin/env python3
"""Re-audit Phase 4's door/date evidence and close the exact-date oracle gap.

The historical probe treated Neo's passport expiry mainly as the numeric value
September 11, 2001. The complete Telegram export adds two important boundaries:

* ``{1},{4},{21}`` exactly matches the creator post's own European-style date,
  1 April 2021.
* The first passport remark was a playful reply to personal questions, but the
  creator deliberately returned to the expiry date in 2023 while replying to a
  Matrix clip.

This makes the strongest conservative role of the passport clue a date-format
hint. The exact prop-style rendering ``11 SEP 01`` and matching post-date
rendering ``01 APR 21`` were absent from the old candidate family, so this
script tests only those exact inscriptions and punctuation variants through
the project's complete textual oracle family.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

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
from door_prime_passport_probe import CANDIDATES as HISTORICAL_CANDIDATES  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR, plain_text  # noqa: E402

DOOR_HINT_ID = 6884
ZEROING_HINT_ID = 8000
PERSONAL_QUESTION_ID = 8045
PASSPORT_REPLY_ID = 8048
MATRIX_CLIP_ID = 8515
PASSPORT_CALLBACK_ID = 8516
COMMUNITY_COMPARE_ID = 8088

COMPARE_PHOTO_SHA256 = (
    "c33d732ce237f7c493292c4b3aacb44a713a5b6017499cf726763193bcde2fa9"
)
MATRIX_CLIP_SHA256 = (
    "31a9e572c213748a59f7807882c7fa36113d44138238dcf8acdc85f77fd9f2cb"
)

PROP_DATE_FORMS = (
    "11 SEP 01",
    "11SEP01",
    "11-SEP-01",
    "11/SEP/01",
)
POST_DATE_FORMS = (
    "01 APR 21",
    "01APR21",
    "01-APR-21",
    "01/APR/21",
)
BASE_CANDIDATES = PROP_DATE_FORMS + POST_DATE_FORMS


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_export(export_dir):
    payload = json.loads((export_dir / "result.json").read_text(encoding="utf-8"))
    return {message["id"]: message for message in payload["messages"]}


def audit_provenance(export_dir=DEFAULT_EXPORT_DIR):
    messages = load_export(export_dir)
    door = messages[DOOR_HINT_ID]
    zeroing = messages[ZEROING_HINT_ID]
    personal = messages[PERSONAL_QUESTION_ID]
    passport = messages[PASSPORT_REPLY_ID]
    clip = messages[MATRIX_CLIP_ID]
    callback = messages[PASSPORT_CALLBACK_ID]
    compare = messages[COMMUNITY_COMPARE_ID]

    door_date = datetime.fromisoformat(door["date"])
    door_tuple = (door_date.day, door_date.month, door_date.year % 100)
    compare_photo = export_dir / compare["photo"]
    matrix_clip = export_dir / clip["file"]

    with Image.open(compare_photo) as image:
        compare_dimensions = image.size

    report = {
        "door_text": plain_text(door),
        "door_date_tuple": door_tuple,
        "zeroing_text": plain_text(zeroing),
        "personal_question": plain_text(personal),
        "passport_text": plain_text(passport),
        "passport_reply_to": passport.get("reply_to_message_id"),
        "callback_text": plain_text(callback),
        "callback_reply_to": callback.get("reply_to_message_id"),
        "clip_path": clip.get("file"),
        "clip_sha256": sha256_file(matrix_clip),
        "compare_text": plain_text(compare),
        "compare_reply_to": compare.get("reply_to_message_id"),
        "compare_photo_path": compare.get("photo"),
        "compare_photo_sha256": sha256_file(compare_photo),
        "compare_photo_dimensions": compare_dimensions,
        "exact_forms_missing_historically": tuple(
            candidate
            for candidate in BASE_CANDIDATES
            if candidate not in HISTORICAL_CANDIDATES
        ),
    }

    if "{1 },{4} ,{21}" not in report["door_text"]:
        raise AssertionError("creator door-hint text changed")
    if door_tuple != (1, 4, 21):
        raise AssertionError(f"door hint no longer matches its post date: {door_tuple}")
    if "prime numbers" not in report["zeroing_text"]:
        raise AssertionError("creator prime wording changed")
    if "characters need to be 'zeroed out'" not in report["zeroing_text"]:
        raise AssertionError("creator zeroing wording changed")
    if "how old are you?" not in report["personal_question"]:
        raise AssertionError("passport reply context changed")
    if "pk of the puzzle address" not in report["personal_question"]:
        raise AssertionError("passport reply context lost the key question")
    if report["passport_reply_to"] != PERSONAL_QUESTION_ID:
        raise AssertionError("passport remark no longer replies to personal questions")
    if "expiry date of neo's passport" not in report["passport_text"].lower():
        raise AssertionError("passport remark changed")
    if report["callback_reply_to"] != MATRIX_CLIP_ID:
        raise AssertionError("passport callback no longer replies to the Matrix clip")
    if "expiration date of his passport" not in report["callback_text"].lower():
        raise AssertionError("passport callback changed")
    if report["clip_sha256"] != MATRIX_CLIP_SHA256:
        raise AssertionError("referenced Matrix clip bytes changed")
    if "compare against the real Matrix text" not in report["compare_text"]:
        raise AssertionError("community compare instruction changed")
    if "extra chars" not in report["compare_text"]:
        raise AssertionError("community extra-character instruction changed")
    if "think about primes" not in report["compare_text"]:
        raise AssertionError("community prime instruction changed")
    if report["compare_photo_sha256"] != COMPARE_PHOTO_SHA256:
        raise AssertionError("community comparison photo bytes changed")
    if compare_dimensions != (776, 297):
        raise AssertionError(
            f"community comparison photo dimensions changed: {compare_dimensions}"
        )
    if report["exact_forms_missing_historically"] != BASE_CANDIDATES:
        raise AssertionError("one or more exact date forms gained historical coverage")
    return report


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for answer in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(answer, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(
                        keystring,
                        kdf_variants=variants,
                        blobs=blobs,
                    )
                    if result:
                        hits["cbc"].append((candidate, keystring, result))
                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))
                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))
                for result in aes_keywrap_try_open_bytes(
                    keystring.encode(),
                    blobs=blobs,
                ):
                    hits["keywrap"].append((candidate, keystring, result))
    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit_provenance(export_dir)
    assert report["door_date_tuple"] == (1, 4, 21)
    assert len(report["exact_forms_missing_historically"]) == 8
    assert set(PROP_DATE_FORMS).isdisjoint(HISTORICAL_CANDIDATES)
    assert set(POST_DATE_FORMS).isdisjoint(HISTORICAL_CANDIDATES)
    print(
        "[*] self-test OK: creator chronology, reply edges, media hashes, "
        "door-date identity, and exact historical coverage gap verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    report = audit_provenance(args.export_dir)
    if args.self_test:
        self_test(args.export_dir)

    print(f"[*] creator door hint date tuple: {report['door_date_tuple']}")
    print(
        "[*] passport evidence: first remark replies to personal questions; "
        "2023 callback replies to archived Matrix clip"
    )
    print(
        f"[*] community comparison media: {report['compare_photo_path']} "
        f"{report['compare_photo_dimensions']} "
        f"sha256={report['compare_photo_sha256']}"
    )
    print(
        "[*] exact date forms absent from historical probe: "
        + ", ".join(repr(value) for value in report["exact_forms_missing_historically"])
    )

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(BASE_CANDIDATES, blobs)
        total_hits = sum(len(values) for values in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
