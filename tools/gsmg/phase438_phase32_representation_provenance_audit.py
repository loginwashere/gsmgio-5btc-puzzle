#!/usr/bin/env python3
"""Phase 438: provenance of the three Phase-3.2.1 representations."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from p32_sibling_password_audit import derive_sibling_outputs
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


REPO_ROOT = Path(__file__).resolve().parents[2]
CREATOR_ID = "user9815232"
TERMS = ("1141", "ebcdic", "beaufort", "one for one", "source codes")
EXPECTED_TERM_COUNTS = {
    "1141": (65, 3301),
    "ebcdic": (20, 3856),
    "beaufort": (51, 6215),
    "one for one": (23, 2872),
    "source codes": (67, 5881),
}
EXPECTED_UNION_COUNT = 201
FIRST_NOTEBOOK_COMMIT = "dcb66952de3157f6e68cb00aa047dd2e4ff8ae39"
NOTEBOOK_ANCHORS = (
    "cp273 1.0",
    "cp1141 1.0",
    "one** for **one**, **four** for **one",
    "encode('cp1141')",
    "beautiful strategic position",
    "**beau**fort",
    "There isn't really a puzzle in that, but maybe it'll be useful in the future",
    "The puzzle was solved to this point by the end of 2019",
)


def digest_record(value):
    payload = value.encode("ascii") if isinstance(value, str) else bytes(value)
    return {"length": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def iconv(encoded, codec):
    completed = subprocess.run(
        ["iconv", "-f", "ISO-8859-1", "-t", codec],
        input=encoded,
        capture_output=True,
        check=True,
    )
    return completed.stdout


def notebook_evidence():
    history_text = subprocess.run(
        [
            "git", "log", "--follow", "--reverse",
            "--format=%H%x09%aI%x09%s", "naddiseo/master", "--",
            "phase3.2.ipynb",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    history = []
    for line in history_text.splitlines():
        commit, timestamp, subject = line.split("\t", 2)
        history.append({"commit": commit, "timestamp": timestamp, "subject": subject})
    if not history or history[0]["commit"] != FIRST_NOTEBOOK_COMMIT:
        raise AssertionError("Phase 3.2 notebook first commit drifted")
    notebook = subprocess.run(
        ["git", "show", f"{FIRST_NOTEBOOK_COMMIT}:phase3.2.ipynb"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    anchors = {anchor: anchor in notebook for anchor in NOTEBOOK_ANCHORS}
    if not all(anchors.values()):
        raise AssertionError("historical notebook workflow anchors drifted")
    return {
        "repository_role": "community_solve_walkthrough_not_creator_primary",
        "history": history,
        "first_commit": history[0],
        "workflow_anchors": anchors,
    }


def telegram_evidence(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    messages = data["messages"]
    hits = []
    for message in messages:
        text = plain_text(message).lower()
        matched = tuple(term for term in TERMS if term in text)
        if matched:
            hits.append((message, matched))
    hit_ids = {message["id"] for message, _ in hits}
    creator_hits = [message["id"] for message, _ in hits if message.get("from_id") == CREATOR_ID]
    creator_replies = [
        message["id"] for message in messages
        if message.get("from_id") == CREATOR_ID
        and message.get("reply_to_message_id") in hit_ids
    ]
    per_term = {}
    for term in TERMS:
        term_hits = [message for message, matched in hits if term in matched]
        per_term[term] = {
            "count": len(term_hits),
            "earliest_id": term_hits[0]["id"],
            "earliest_date": term_hits[0]["date"],
        }
        if (len(term_hits), term_hits[0]["id"]) != EXPECTED_TERM_COUNTS[term]:
            raise AssertionError(f"Telegram fixed-term evidence drifted for {term}")
    if len(hits) != EXPECTED_UNION_COUNT:
        raise AssertionError("Telegram fixed-term union drifted")
    return {
        "export_group": data.get("name"),
        "export_group_id": data.get("id"),
        "fixed_terms": TERMS,
        "union_hit_count": len(hits),
        "per_term": per_term,
        "creator_authored_hit_ids": creator_hits,
        "creator_direct_reply_ids": creator_replies,
    }


def audit(export_dir=DEFAULT_EXPORT_DIR):
    derived = derive_sibling_outputs()
    raw = derived["components"]["encoded_321"]
    cp273 = iconv(raw, "CP273")
    cp1141 = iconv(raw, "CP1141")
    pinned_cipher = derived["cipher_321"].encode("ascii")
    differences = tuple(index for index, pair in enumerate(zip(cp273, cp1141)) if pair[0] != pair[1])
    if not (len(raw) == len(cp273) == len(cp1141) == len(pinned_cipher) == 1539):
        raise AssertionError("Phase 3.2.1 representation length drifted")
    if len(set(raw)) != 26:
        raise AssertionError("raw Phase 3.2.1 alphabet drifted")

    notebook = notebook_evidence()
    telegram = telegram_evidence(export_dir)
    creator_binding = bool(
        telegram["creator_authored_hit_ids"] or telegram["creator_direct_reply_ids"]
    )
    if creator_binding:
        decision = "downstream_representation_bound"
    elif all(notebook["workflow_anchors"].values()):
        decision = "workflow_privilege_without_downstream_binding"
    else:
        decision = "no_reproducible_workflow_privilege"

    return {
        "phase": 438,
        "representations": {
            "raw_encoded_321": {
                **digest_record(raw),
                "distinct_symbols": len(set(raw)),
                "evidence_class": "creator_delivered",
                "workflow_role": "encoded input",
            },
            "cp1141_beaufort_ciphertext": {
                **digest_record(cp1141),
                "distinct_symbols": len(set(cp1141)),
                "evidence_class": "clue_selected_derived",
                "workflow_role": "Beaufort ciphertext intermediate",
            },
            "decoded_architect_letters": {
                **digest_record(derived["answer_321"]),
                "distinct_symbols": len(set(derived["answer_321"])),
                "evidence_class": "decoded_output",
                "workflow_role": "plaintext containing SOURCE CODES instruction",
            },
        },
        "transcoding_comparison": {
            "cp273_equals_cp1141": cp273 == cp1141,
            "differing_position_count": len(differences),
            "differing_positions": differences,
            "cp273_equals_pinned_ciphertext": cp273 == pinned_cipher,
            "cp1141_equals_pinned_ciphertext": cp1141 == pinned_cipher,
            "implication": "CP1141 labels the clue-selected route but does not uniquely select a different letter stream from CP273 on these bytes",
        },
        "notebook": notebook,
        "telegram": telegram,
        "creator_primary_downstream_binding_found": creator_binding,
        "phase437_gate_updates": {
            "raw_encoded_321": {"locally_selected": False, "unique_representation": False},
            "cp1141_beaufort_ciphertext": {"locally_selected": False, "unique_representation": False},
            "decoded_answer_321": {"locally_selected": False, "unique_representation": False},
        },
        "decision": decision,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["transcoding_comparison"]["cp273_equals_cp1141"] is True
    assert report["transcoding_comparison"]["differing_position_count"] == 0
    assert report["transcoding_comparison"]["cp273_equals_pinned_ciphertext"] is True
    assert report["transcoding_comparison"]["cp1141_equals_pinned_ciphertext"] is True
    assert report["telegram"]["union_hit_count"] == 201
    assert report["telegram"]["creator_authored_hit_ids"] == []
    assert report["telegram"]["creator_direct_reply_ids"] == []
    assert report["creator_primary_downstream_binding_found"] is False
    assert report["decision"] == "workflow_privilege_without_downstream_binding"
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    print("[*] Phase 438 self-test OK: workflow roles reproduced; no creator-primary downstream representation binding")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.export_dir)
    if args.self_test:
        self_test(args.export_dir)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    elif not args.self_test:
        print(payload, end="")


if __name__ == "__main__":
    main()
