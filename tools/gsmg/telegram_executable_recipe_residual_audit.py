#!/usr/bin/env python3
"""Phase 393: executable-recipe residual discovery over the Telegram export.

Phase 388 reviewed the original Stage-1 keyword universe and the 77-message
intersection of a separate technique/surprise sweep.  It did not review the
technique-only messages that sit outside both sets.  This module freezes that
residual *before any message is read for substance*, then applies one fixed
recipe-shape gate:

* the message makes a result/password/key-style claim; and
* it contains executable-looking material (a hash call, key/IV assignment,
  OpenSSL/AES spelling, a 64-hex value, Salted__ Base64, or a Bitcoin address).

The gate is discovery-only.  A selected message is not a candidate or result;
it merely enters a finite full-text review lane.  After the lane was frozen,
all 142 messages were read in full and assigned to the static review groups
below.  The two reproducible constructions are verified separately in Phase
394; this module never generates candidates or performs decrypt testing.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from telegram_export_keyword_sweep import sweep as stage1_sweep
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export
from telegram_export_technique_surprise_sweep import sweep as technique_sweep


# Frozen before reviewing the selected lane.  These patterns are intentionally
# broad enough to retain claims phrased as ordinary prose, but require both an
# assertion-shaped term and an independently executable-looking token.
CLAIM_PATTERN = re.compile(
    r"\b(?:decrypt(?:ed|s|ion)?|password|passphrase|key|result|output|"
    r"works?|worked|found|got|yield(?:s|ed)?|opens?|success(?:ful)?)\b",
    re.IGNORECASE,
)
RECIPE_PATTERN = re.compile(
    r"(?:sha-?256\s*\(|openssl|aes-?256|\bxor\b|"
    r"\b(?:key|iv|password|passphrase)\s*[:=]|"
    r"[0-9a-f]{64}|U2FsdGVkX1|[13][1-9A-HJ-NP-Za-km-z]{25,50})",
    re.IGNORECASE,
)

EXPECTED_TECHNIQUE_HITS = 1629
EXPECTED_TECHNIQUE_OUTSIDE_STAGE1 = 1475
EXPECTED_INTERSECTION_OUTSIDE_STAGE1 = 59
EXPECTED_TECHNIQUE_ONLY_OUTSIDE_STAGE1 = 1416
EXPECTED_REVIEW_LANE = 142

# Filled from the first metadata-only run of the frozen gate, before emitting
# or reviewing any selected message text.  The self-test refuses to bless a
# corpus until both pins are present.
EXPECTED_LANE_ID_DIGEST = "dbc380cde28d6f4847c1c5373165573eac6998df57afc6423a561c4ff6950287"
EXPECTED_LANE_CONTENT_DIGEST = "759e491c5caaacc372cef5cecf997cdab44769641031095bf0d03edf9531c836"


# Frozen only after the ID/content digests above were pinned and every selected
# message was read in full.  Three messages represent two reproducible leads:
# 65082 is the FEFE/GF(2) construction; 66244/66245 are one BIP39 construction
# split across prose and code.  Both receive independent controls in Phase 394.
REVIEW_GROUPS = (
    (
        "covered",
        "authenticated solved step, password, hash, or end-to-end toolchain already documented",
        {
            230, 339, 1478, 1864, 2687, 13526, 18517, 20033, 21198,
            21682, 22877, 24351, 28825, 37936, 37943, 37964, 38133,
            38141, 39104, 39861, 41132, 44105, 47243, 52622, 55639,
            61802, 66086,
        },
    ),
    (
        "covered",
        "technical explanation, false-positive control, test vector, or key-format fact already represented by an existing audit family",
        {
            1475, 1477, 3076, 17383, 29802, 29807, 34397, 35301,
            35302, 38146, 38741, 39886, 39923, 40913, 42526, 42992,
            45782, 45848, 46790, 47757, 47767, 47906, 50624, 51122,
            53208, 60211, 62286, 62404, 62821,
        },
    ),
    (
        "covered",
        "known ciphertext, transaction, address, or on-chain provenance object",
        {5591, 14225, 14395, 24829, 24832, 41358, 43017},
    ),
    (
        "covered",
        "finite cipher, metadata, title-rebus, or key-derivation family already audited",
        {23521, 24836, 40402, 43665, 49433, 51767, 58549},
    ),
    (
        "covered",
        "exact unauthenticated passphrase/key claim closed at zero hits by Phase 394's 31,680-attempt four-blob oracle",
        {
            16950, 20884, 27796, 27831, 28283, 30741, 35283, 36373,
            36623, 41757, 42208, 45817, 51333, 52053, 56807, 57924,
            60232, 62300,
        },
    ),
    (
        "noise_or_incomplete",
        "question, tentative idea, joke, unrelated example, gibberish false positive, or claim missing a reproducible input-operation-output-verifier chain",
        {
            2314, 3249, 4915, 5629, 5642, 7751, 8952, 11759, 13525,
            16235, 16646, 21591, 21614, 21758, 23209, 23592, 24837,
            25539, 26145, 28471, 29421, 29770, 30969, 31945, 33427,
            34290, 34555, 34929, 35215, 35410, 36716, 37711, 40038,
            40953, 44207, 45856, 46899, 47773, 48631, 48758, 50447,
            50630, 50896, 56810, 60067, 60130, 60193, 62506, 64506,
            65123, 66209,
        },
    ),
    (
        "new_lead",
        "Phase 394: reproducible FEFE-cell GF(2) rank/kernel construction; algebra verified, controls close it as non-discriminating",
        {65082},
    ),
    (
        "new_lead",
        "Phase 394: reproducible BTCSEED-rail BIP39 mnemonic construction; checksum verified, selection family and prize-address authentication close negative",
        {66244, 66245},
    ),
)


def _digest_ids(rows):
    payload = ",".join(str(row["id"]) for row in rows).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _digest_content(rows):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(str(row["id"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(row["text_sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def select(data):
    stage1_ids = {row["id"] for row in stage1_sweep(data)}
    technique_report = technique_sweep(data)
    technique_hits = technique_report["technique_hits"]
    intersection_ids = {row["id"] for row in technique_report["intersection"]}

    outside_stage1 = tuple(row for row in technique_hits if row["id"] not in stage1_ids)
    intersection_outside_stage1 = tuple(
        row for row in outside_stage1 if row["id"] in intersection_ids
    )
    residual = tuple(
        row for row in outside_stage1 if row["id"] not in intersection_ids
    )

    lane = []
    for row in residual:
        text = row["text"]
        if not CLAIM_PATTERN.search(text) or not RECIPE_PATTERN.search(text):
            continue
        lane.append({
            "id": row["id"],
            "date": row["date"],
            "date_unixtime": row["date_unixtime"],
            "from": row["from"],
            "technique_terms": row["technique_terms"],
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text": text,
        })

    lane = tuple(lane)
    return {
        "stage1_hit_count": len(stage1_ids),
        "technique_hit_count": len(technique_hits),
        "technique_outside_stage1_count": len(outside_stage1),
        "intersection_outside_stage1_count": len(intersection_outside_stage1),
        "technique_only_outside_stage1_count": len(residual),
        "review_lane_count": len(lane),
        "lane_id_digest": _digest_ids(lane),
        "lane_content_digest": _digest_content(lane),
        "lane": lane,
    }


def classify_lane(lane):
    lookup = {}
    for disposition, reason, message_ids in REVIEW_GROUPS:
        for message_id in message_ids:
            assert message_id not in lookup, f"duplicate review disposition for {message_id}"
            lookup[message_id] = (disposition, reason)

    lane_ids = {row["id"] for row in lane}
    assert set(lookup) == lane_ids, {
        "unclassified": sorted(lane_ids - set(lookup)),
        "not_in_frozen_lane": sorted(set(lookup) - lane_ids),
    }
    ledger = []
    for row in lane:
        disposition, reason = lookup[row["id"]]
        ledger.append({
            "id": row["id"],
            "date": row["date"],
            "from": row["from"],
            "technique_terms": row["technique_terms"],
            "text_sha256": row["text_sha256"],
            "disposition": disposition,
            "reason": reason,
        })
    return tuple(ledger)


def audit(export_dir=DEFAULT_EXPORT_DIR):
    report = select(load_export(export_dir))
    ledger = classify_lane(report["lane"])
    counts = {
        disposition: sum(row["disposition"] == disposition for row in ledger)
        for disposition in ("covered", "noise_or_incomplete", "new_lead")
    }
    return {**report, "classification_counts": counts, "ledger": ledger}


def synthetic_self_test():
    synthetic = {"messages": [
        {"id": 1, "type": "message", "date_unixtime": "1", "text_entities": [
            {"type": "plain", "text": "AES discussion only"}
        ]},
        {"id": 2, "type": "message", "date_unixtime": "2", "text_entities": [
            {"type": "plain", "text": "I found the key = " + "a" * 64}
        ]},
        {"id": 3, "type": "message", "date_unixtime": "3", "text_entities": [
            {"type": "plain", "text": "AES result looks random"}
        ]},
        {"id": 4, "type": "message", "date_unixtime": "4", "text_entities": [
            {"type": "plain", "text": "DBBI AES password=" + "b" * 64}
        ]},
    ]}
    report = select(synthetic)
    # id=2 is technique-free and therefore never enters this axis; id=3 is in
    # the already-reviewed surprise intersection; id=4 is inside Stage 1.
    assert report["review_lane_count"] == 0, report

    direct = CLAIM_PATTERN.search("decrypted key") and RECIPE_PATTERN.search(
        "key=" + "c" * 64
    )
    assert direct


def corpus_self_test(report):
    assert report["stage1_hit_count"] == 1828
    assert report["technique_hit_count"] == EXPECTED_TECHNIQUE_HITS
    assert report["technique_outside_stage1_count"] == EXPECTED_TECHNIQUE_OUTSIDE_STAGE1
    assert report["intersection_outside_stage1_count"] == EXPECTED_INTERSECTION_OUTSIDE_STAGE1
    assert report["technique_only_outside_stage1_count"] == EXPECTED_TECHNIQUE_ONLY_OUTSIDE_STAGE1
    assert report["review_lane_count"] == EXPECTED_REVIEW_LANE
    assert EXPECTED_LANE_ID_DIGEST, "pin EXPECTED_LANE_ID_DIGEST before review"
    assert EXPECTED_LANE_CONTENT_DIGEST, "pin EXPECTED_LANE_CONTENT_DIGEST before review"
    assert report["lane_id_digest"] == EXPECTED_LANE_ID_DIGEST
    assert report["lane_content_digest"] == EXPECTED_LANE_CONTENT_DIGEST
    assert report["classification_counts"] == {
        "covered": 88,
        "noise_or_incomplete": 51,
        "new_lead": 3,
    }
    leads = [row["id"] for row in report["ledger"] if row["disposition"] == "new_lead"]
    assert leads == [65082, 66244, 66245]


def summary(report):
    return {key: value for key, value in report.items() if key not in {"lane", "ledger"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    synthetic_self_test()
    report = audit(args.export_dir)
    print(json.dumps(summary(report), indent=2))

    if args.metadata_only:
        return

    corpus_self_test(report)
    if args.self_test:
        print(
            "[*] self-test OK: frozen 1,416-message residual and 142-message "
            "recipe lane; 88 covered / 51 noise-or-incomplete / 3 messages "
            "forming 2 Phase-394 leads"
        )
        return

    if args.json_out:
        args.json_out.write_text(
            json.dumps(report["ledger"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[*] message-level review ledger written to {args.json_out}")


if __name__ == "__main__":
    main()
