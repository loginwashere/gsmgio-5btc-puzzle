#!/usr/bin/env python3
"""Audit whether creator spelling ``YING/YANG`` selects FAED's {g,i} pair.

The alignment is measured exactly, but promotion requires evidence that the
extra ``g`` is an authored operator rather than one of the creator's typos.
No decoder or AES oracle is run.
"""

import argparse
import json
import re
from pathlib import Path

from checkerboard_code_ic_oracle import apply_to_real_data
from prime_matrixsum_reconstruction import mirror9
from salphaseion_title_rebus_audit import EXPECTED_MACRO, load_macro
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


CREATOR_ID = "user9815232"
PLAIN_YINGYANG_IDS = (9599, 39224)
TYPO_CAVEAT_ID = 1806
HIT_HINT_QUESTION_ID = 9602
BOTH_ANSWER_ID = 9603
NATIVE = frozenset("abcdefghi")


def native_filter(value):
    return "".join(character for character in value.lower() if character in NATIVE)


def pair_key(left, right):
    return frozenset((left, right))


def rank_map(target):
    ranked = apply_to_real_data(target)["ranked"]
    return {
        frozenset(pair): {"rank": rank, "ic": ic}
        for rank, (pair, ic) in enumerate(ranked, 1)
    }


def creator_evidence(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    messages = {message["id"]: message for message in data["messages"]}
    creator = {
        message_id: plain_text(message)
        for message_id, message in messages.items()
        if message.get("from_id") == CREATOR_ID
    }
    pattern = re.compile(r"\bying(?:\s+)?yang\b", re.I)
    ids = tuple(message_id for message_id, text in creator.items() if pattern.search(text))
    if ids != PLAIN_YINGYANG_IDS:
        raise AssertionError(f"creator plain YING/YANG inventory drifted: {ids}")

    expected_fragments = {
        9599: 'Once you hit a "ying yang"',
        39224: "when yingyang is reached",
        TYPO_CAVEAT_ID: "No clues to be found in those typos",
        HIT_HINT_QUESTION_ID: "hit or hint?",
        BOTH_ANSWER_ID: "Both?",
    }
    for message_id, fragment in expected_fragments.items():
        if fragment not in plain_text(messages[message_id]):
            raise AssertionError(f"message {message_id} text drifted")
    if messages[TYPO_CAVEAT_ID].get("from_id") != CREATOR_ID:
        raise AssertionError("typo caveat is no longer creator-authored")
    if messages[BOTH_ANSWER_ID].get("from_id") != CREATOR_ID:
        raise AssertionError("Both? answer is no longer creator-authored")
    if BOTH_ANSWER_ID != HIT_HINT_QUESTION_ID + 1:
        raise AssertionError("hit/hint and Both? are no longer adjacent IDs")

    export_path = Path(export_dir) / "result.json"
    macro = load_macro(export_path)
    if macro != EXPECTED_MACRO or "yinyang" not in macro or "yingyang" in macro:
        raise AssertionError("creator binary macro spelling drifted")
    return {
        "plain_yingyang_message_ids": ids,
        "plain_texts": {message_id: creator[message_id] for message_id in ids},
        "earlier_typo_caveat": {
            "message_id": TYPO_CAVEAT_ID,
            "text": creator[TYPO_CAVEAT_ID],
            "predates_plain_yingyang_uses": TYPO_CAVEAT_ID < min(ids),
        },
        "binary_macro": {
            "message_id": 8446,
            "uses_standard_yinyang": True,
            "macro": macro,
        },
        "hit_hint_exchange": {
            "question_id": HIT_HINT_QUESTION_ID,
            "question": plain_text(messages[HIT_HINT_QUESTION_ID]),
            "answer_id": BOTH_ANSWER_ID,
            "answer": creator[BOTH_ANSWER_ID],
            "reply_edge_present": messages[BOTH_ANSWER_ID].get("reply_to_message_id") == HIT_HINT_QUESTION_ID,
            "immediate_context_referent": "hit and hint, not the two spelling halves",
        },
    }


def ranking_controls(target):
    ranks = rank_map(target)
    rows = []
    for shared in "bcdefgh":
        first = ranks.get(pair_key("i", shared))
        second = ranks.get(pair_key("a", shared))
        rows.append({
            "shared_symbol": shared,
            "ig_shape_rank": first["rank"] if first else None,
            "ag_shape_rank": second["rank"] if second else None,
            "both_segment_cleanly": first is not None and second is not None,
            "rank_sum": first["rank"] + second["rank"] if first and second else None,
            "worst_rank": max(first["rank"], second["rank"]) if first and second else None,
        })
    valid = tuple(row for row in rows if row["both_segment_cleanly"])
    best = min(valid, key=lambda row: (row["worst_rank"], row["rank_sum"]))
    return {"target": target, "rows": tuple(rows), "valid_rows": valid, "best_joint_suffix": best}


def audit(export_dir=DEFAULT_EXPORT_DIR):
    evidence = creator_evidence(export_dir)
    words = ("ying", "yang")
    filtered = tuple(native_filter(word) for word in words)
    if filtered != ("ig", "ag"):
        raise AssertionError("native filtering of YING/YANG changed")
    if mirror9("i") != "a" or mirror9("a") != "i":
        raise AssertionError("native endpoint mirror changed")
    if mirror9("g") == "g":
        raise AssertionError("shared G unexpectedly became a mirror fixed point")

    faed = ranking_controls("faed")
    dbbi = ranking_controls("dbbi")
    faed_ranks = rank_map("faed")
    dbbi_ranks = rank_map("dbbi")
    observed = {
        "ying_pair": ("g", "i"),
        "yang_pair": ("a", "g"),
        "faed_ranks": {
            "gi": faed_ranks[pair_key("g", "i")],
            "ag": faed_ranks[pair_key("a", "g")],
        },
        "dbbi_control_ranks": {
            "gi": dbbi_ranks[pair_key("g", "i")],
            "ag": dbbi_ranks[pair_key("a", "g")],
        },
    }
    gates = {
        "primary_wording": True,
        "deterministic_native_filter": True,
        "faed_specific_rank_alignment": (
            observed["faed_ranks"]["gi"]["rank"] == 1
            and observed["faed_ranks"]["ag"]["rank"] == 5
            and faed["best_joint_suffix"]["shared_symbol"] == "g"
        ),
        "authored_spelling_operator": False,
        "decoder_or_combiner_selected": False,
    }
    return {
        "creator_evidence": evidence,
        "lexical_mechanics": {
            "words": words,
            "native_filtered": filtered,
            "differing_symbols": ("i", "a"),
            "differing_symbols_are_mirror_endpoints": True,
            "shared_symbol": "g",
            "shared_symbol_is_fixed_under_mirror9": False,
        },
        "observed_pair_ranks": observed,
        "shared_suffix_controls": {"faed": faed, "dbbi": dbbi},
        "gates": gates,
        "promotion": {
            "promoted": False,
            "new_compute_authorized": False,
            "reason": (
                "The IG/AG alignment is exact and unusually FAED-specific, but the "
                "creator explicitly disclaimed clues in typos and used standard "
                "yinyang in the authenticated binary macro. Nothing selects the "
                "misspelling as an operator or says how to combine its two parses."
            ),
        },
        "verdict": (
            "Retain YING -> IG as a compact possible explanation for why FAED's "
            "independently ranked pair is {g,i}, but do not promote it to recovered "
            "binding and do not launch an {a,g} or dual-pair brute force."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["lexical_mechanics"]["native_filtered"] == ("ig", "ag")
    assert report["observed_pair_ranks"]["faed_ranks"]["gi"]["rank"] == 1
    assert report["observed_pair_ranks"]["faed_ranks"]["ag"]["rank"] == 5
    assert report["shared_suffix_controls"]["faed"]["best_joint_suffix"]["shared_symbol"] == "g"
    assert report["shared_suffix_controls"]["dbbi"]["best_joint_suffix"]["shared_symbol"] == "b"
    assert not report["gates"]["authored_spelling_operator"]
    assert not report["promotion"]["promoted"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: exact YING/FAED alignment retained without promotion")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export_dir) if args.self_test else audit(args.export_dir)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
