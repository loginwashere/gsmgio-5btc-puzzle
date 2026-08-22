#!/usr/bin/env python3
"""Step 1 of the topology-identifiability audit, per the user's exact
2026-08-22 framing: freeze ONLY primary evidence -- exact page/DOM bytes,
the 5 historical Wayback captures, solved-stage syntax, and creator
messages with real reply edges -- explicitly excluding community
interpretation and prior-phase PROSE conclusions. Where a prior phase's
claim is reused, this script independently re-derives or re-verifies the
underlying primary artifact itself rather than citing the phase's prose.

This produces no scoring, no ranking, and no cryptanalysis. It is a
frozen evidence manifest for Steps 2-5 to consume.

> **Correction (same-day review):** the first version of this file had
> three defects, all fixed here:
> 1. `verify_wayback_captures()` never read capture bytes or derived a
>    textarea digest -- it compared a hard-coded dict to itself. Fixed by
>    a real live-fetch + `TextareaParser` extraction, pinned as
>    `topology_identifiability_wayback_textarea_freeze.json`
>    (full SHA-256, not truncated), with a `--live` re-verification path.
> 2. `edited` timestamps were recorded but never asserted. Fixed in
>    `verify_creator_reply_edges()`.
> 3. The 7-message reply-edge set was manually curated with no
>    reproducible inclusion rule. Fixed by mechanically extracting the
>    FULL universe of creator replies (every message with
>    `from_id == CREATOR_ACCOUNT_ID` and a non-null
>    `reply_to_message_id`, plus its parent) into
>    `topology_identifiability_creator_reply_universe.json` (148 rows).
>    The original 7-message set is now labeled explicitly as a candidate
>    subset pending Step 2's preregistered relevance rule, not as "the"
>    frozen reply-edge evidence.
>
> Also added: a witness layer for the three standalone/edited creator
> messages (1710, 8446, 6497), each checked against independently-located
> earlier copies to establish how far back the current bytes are
> witnessed. Full SHA-256 values are used throughout; 16-character
> prefixes have been replaced.

Five evidence classes, each independently re-verified this session:

1. **Wayback captures + textarea content.** All 5 pinned captures
   (`salphaseion_wayback_history_audit.CAPTURES`) were re-fetched live
   from web.archive.org on 2026-08-22; full-page sha256/byte_count/
   heading matched the pinned values, AND both textareas (SalPhaseIon,
   Cosmic Duality) were independently extracted via
   `page_structure_audit.TextareaParser` and hashed -- both are
   byte-identical across all 5 captures, spanning 2023-06-01 to
   2026-04-05. Pinned in `topology_identifiability_wayback_textarea_
   freeze.json`. The only diff across all 5 raw captures is one heading
   capitalization change (`<h1>` -> `<H1>` for SalPhaseIon, between
   capture 1 and 2) plus unrelated page-shell/analytics-script churn.

2. **Current live DOM segmentation.** Reuses `page_structure_audit`'s
   byte-verified textarea parse and `salphaseion_operand_binding_audit`'s
   `EXPECTED_SEGMENTS` tuple.

3. **Solved-stage syntax.** Reuses `solved_boundary_rule_audit`'s
   ground-truth hashes (Phase 2/3/3.2).

4. **Full creator reply-edge universe.** Mechanically extracted from the
   raw Telegram export JSON (`topology_identifiability_creator_reply_
   universe.json`): every message where `from_id == CREATOR_ACCOUNT_ID`
   and `reply_to_message_id` is not null, plus that parent's `from_id`
   -- 148 rows, no manual topic selection. A small candidate subset
   (`REPLY_EDGE_MESSAGES`) is separately retained from the earlier pass
   as a Step-2 starting point, but is explicitly NOT presented as the
   full frozen universe. Standalone creator broadcasts with no
   `reply_to_message_id` at all (8446, 1710) are recorded separately and
   are, by definition, absent from the reply-edge universe.

5. **Witness layer for edited/standalone creator messages.** For each of
   1710, 8446, and 6497 (all of which carry non-null `edited`
   timestamps), independently located earlier messages that reproduce or
   witness their content, classified by exactly how strong that witness
   is (byte-identical vs same-substance-different-formatting, and how
   far back it reaches relative to the recorded edit date). Pinned in
   `topology_identifiability_witness_layer.json`.

Usage:
    python3 tools/gsmg/topology_identifiability_evidence_freeze.py --self-test
    python3 tools/gsmg/topology_identifiability_evidence_freeze.py --json
    python3 tools/gsmg/topology_identifiability_evidence_freeze.py --live
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from page_structure_audit import DEFAULT_HTML  # noqa: E402
from page_structure_audit import TextareaParser  # noqa: E402
from page_structure_audit import audit as audit_page  # noqa: E402
from salphaseion_operand_binding_audit import EXPECTED_SEGMENTS  # noqa: E402
from salphaseion_wayback_history_audit import CAPTURES  # noqa: E402
from salphaseion_wayback_history_audit import RAW_CAPTURE_TEMPLATE, ROUTE  # noqa: E402
from salphaseion_wayback_history_audit import assert_capture, fetch_bytes  # noqa: E402
from solved_boundary_rule_audit import EXPECTED_HASHES  # noqa: E402
from solved_boundary_rule_audit import run as run_solved_boundary_audit  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402

MODULE_DIR = Path(__file__).resolve().parent
WAYBACK_TEXTAREA_FREEZE_PATH = MODULE_DIR / "topology_identifiability_wayback_textarea_freeze.json"
CREATOR_REPLY_UNIVERSE_PATH = MODULE_DIR / "topology_identifiability_creator_reply_universe.json"
WITNESS_LAYER_PATH = MODULE_DIR / "topology_identifiability_witness_layer.json"

CREATOR_ACCOUNT_ID = "user9815232"

# ---------------------------------------------------------------------------
# 1. Wayback captures + textarea content
# ---------------------------------------------------------------------------

def verify_wayback_captures():
    """Confirms the pinned capture manifest is internally consistent (5
    captures, monotonically non-decreasing byte counts, exactly one
    heading-case difference between the first two). Structural only --
    see verify_wayback_textarea_content() for actual content bytes."""
    if len(CAPTURES) != 5:
        raise AssertionError(f"expected 5 pinned captures, found {len(CAPTURES)}")
    byte_counts = [c["byte_count"] for c in CAPTURES]
    if byte_counts != sorted(byte_counts):
        raise AssertionError("capture byte counts are not monotonically non-decreasing")
    if CAPTURES[0]["salphaseion_heading"] == CAPTURES[1]["salphaseion_heading"]:
        raise AssertionError("expected a heading-case difference between captures 1 and 2")
    for capture in CAPTURES[1:]:
        if capture["salphaseion_heading"] != CAPTURES[1]["salphaseion_heading"]:
            raise AssertionError("heading case changed again after capture 2 -- re-verify")
    return {
        "capture_count": 5,
        "timestamps": tuple(c["timestamp"] for c in CAPTURES),
        "sha256_per_capture": tuple(c["sha256"] for c in CAPTURES),
        "only_diff_capture_1_to_2": "SalPhaseIon heading case: <h1> -> <H1>",
        "content_stability_window": "2023-06-01 to 2026-04-05 (all 5 captures)",
    }


def _extract_textareas(raw_bytes):
    parser = TextareaParser()
    parser.feed(raw_bytes.decode("ascii"))
    if len(parser.textareas) != 2:
        raise AssertionError(f"expected 2 textareas, found {len(parser.textareas)}")
    salph_raw, cosmic_raw = parser.textareas
    return {
        "salphaseion_sha256": hashlib.sha256(salph_raw.encode()).hexdigest(),
        "cosmic_duality_sha256": hashlib.sha256(cosmic_raw.encode()).hexdigest(),
    }


def verify_wayback_textarea_content_live():
    """Network-dependent: re-fetches all 5 pinned captures now, extracts
    both textareas via TextareaParser, and asserts byte-identity across
    all 5 -- the actual check the original version of this file only
    claimed to perform."""
    reports = []
    for expected in CAPTURES:
        url = RAW_CAPTURE_TEMPLATE.format(timestamp=expected["timestamp"], route=ROUTE)
        raw = fetch_bytes(url)
        assert_capture(raw, expected)
        reports.append({"timestamp": expected["timestamp"], **_extract_textareas(raw)})
    return _aggregate_textarea_reports(reports)


def verify_wayback_textarea_content_local(capture_dir):
    """Same check from a local capture-dir mirror (no network)."""
    reports = []
    for expected in CAPTURES:
        raw = (Path(capture_dir) / f"{expected['timestamp']}.html").read_bytes()
        assert_capture(raw, expected)
        reports.append({"timestamp": expected["timestamp"], **_extract_textareas(raw)})
    return _aggregate_textarea_reports(reports)


def _aggregate_textarea_reports(reports):
    salph = {r["salphaseion_sha256"] for r in reports}
    cosmic = {r["cosmic_duality_sha256"] for r in reports}
    if len(salph) != 1:
        raise AssertionError(f"SalPhaseIon textarea NOT byte-identical across captures: {salph}")
    if len(cosmic) != 1:
        raise AssertionError(f"Cosmic Duality textarea NOT byte-identical across captures: {cosmic}")
    return {
        "per_capture": reports,
        "salphaseion_sha256_all_5_identical": salph.pop(),
        "cosmic_duality_sha256_all_5_identical": cosmic.pop(),
    }


def verify_wayback_textarea_content_pinned():
    """Offline: loads the artifact generated by a real live fetch on
    2026-08-22 and re-checks its own internal consistency (all 5
    per-capture digests actually agree). Use --live to re-derive from
    the network on demand instead of trusting the pin."""
    pinned = json.loads(WAYBACK_TEXTAREA_FREEZE_PATH.read_text())
    recomputed = _aggregate_textarea_reports(pinned["per_capture"])
    if recomputed["salphaseion_sha256_all_5_identical"] != pinned["salphaseion_sha256_all_5_identical"]:
        raise AssertionError("pinned salphaseion digest inconsistent with its own per-capture rows")
    if recomputed["cosmic_duality_sha256_all_5_identical"] != pinned["cosmic_duality_sha256_all_5_identical"]:
        raise AssertionError("pinned cosmic_duality digest inconsistent with its own per-capture rows")
    return pinned


# ---------------------------------------------------------------------------
# 2. Current live DOM segmentation
# ---------------------------------------------------------------------------

def verify_current_page_structure(html_path=DEFAULT_HTML):
    page_report = audit_page(html_path)
    observed_segments = tuple(
        segment["name"] for segment in page_report["salphaseion"]["segments"]
    )
    if observed_segments != EXPECTED_SEGMENTS:
        raise AssertionError("authenticated SalPhaseIon segment order changed")
    return {
        "segments_in_order": observed_segments,
        "cosmic_duality_matches_known_blob": page_report["cosmic_duality"]["matches_known_blob"],
        "salphaseion_source_bytes": page_report["salphaseion"]["source_characters"],
    }


# ---------------------------------------------------------------------------
# 3. Solved-stage syntax
# ---------------------------------------------------------------------------

def verify_solved_stage_syntax():
    report = run_solved_boundary_audit()
    if not report["promotion_gate_passed"]:
        raise AssertionError("solved-boundary rule engine no longer reproduces the known hashes")
    return {
        "boundaries": tuple(b["boundary"] for b in report["boundaries"]),
        "expected_hashes": dict(EXPECTED_HASHES),
        "all_recovered_at_rank_1": all(b["rank"] == 1 for b in report["boundaries"]),
    }


# ---------------------------------------------------------------------------
# 4. Creator messages with real reply edges
# ---------------------------------------------------------------------------

# A candidate subset flagged during the first pass over the export, kept
# only as a Step-2 starting point -- NOT presented as the full frozen
# reply-edge universe (see creator_reply_universe() for that).
REPLY_EDGE_MESSAGES = (
    {"id": 6496, "from_id": "user980067088", "reply_to_message_id": 6495,
     "edited": "2024-06-07T17:25:20",
     "text_sha256": "e2aded25dc6a3ed278faca84208b7f66acd6e000155782c756cac26806fcc937",
     "is_creator": False, "role": "community message 6497 replies to"},
    {"id": 6497, "from_id": "user9815232", "reply_to_message_id": 6496,
     "edited": "2025-06-26T11:42:30",
     "text_sha256": "fcf24bee5043aaa776e11daf3d64f50587f573c0c311b404acfb630e54e5bda5",
     "is_creator": True, "role": "creator reply containing 'Breaking salphation...' (Phase 97's PH->V premise)"},
    {"id": 20221, "from_id": "user6501279574", "reply_to_message_id": None,
     "edited": None,
     "text_sha256": "7f3c990e16cf95635322d7c1e09dcdf4a896ffe8b1933a8ce43fbf887e28c73c",
     "is_creator": False, "role": "asks 'what format key' -- what 20223 actually answers"},
    {"id": 20222, "from_id": "user6246033427", "reply_to_message_id": None,
     "edited": None,
     "text_sha256": "9e31a7741851f5f0d21badb2cb03807bee817fc3bffb06d55435e438e755c99b",
     "is_creator": False, "role": "asks about 'our first hint is your last command'"},
    {"id": 20223, "from_id": "user9815232", "reply_to_message_id": 20221,
     "edited": None,
     "text_sha256": "5fbb8083afcff8a5e269063dfa93964812b9610bce7419b42eeb01c7b86c26bf",
     "is_creator": True, "role": "creator reply to 20221 (answers a DIFFERENT question than 20222)"},
    {"id": 20224, "from_id": "user9815232", "reply_to_message_id": 20222,
     "edited": None,
     "text_sha256": "9235c4fb32f2256c06129b9b462c428aaea9872264c141e6c8b3cc217a987012",
     "is_creator": True, "role": "creator's single-emoji reply to 20222 -- an explicit decline"},
    {"id": 20226, "from_id": "user6246033427", "reply_to_message_id": 20224,
     "edited": "2024-06-07T16:41:42",
     "text_sha256": "a0e492aed4a4803dc02aa50744ee665495841a9a95d4c836a18d8a4665340e30",
     "is_creator": False, "role": "follow-up to the decline, asking who 'our' refers to -- never answered anywhere in the export"},
)

# Standalone creator broadcasts -- explicitly NOT reply-edge evidence
# (no reply_to_message_id at all). See topology_identifiability_witness_
# layer.json for how far back their content is independently witnessed.
STANDALONE_CREATOR_BROADCASTS = (
    {"id": 8446, "from_id": "user9815232", "edited": "2023-12-03T00:47:40",
     "text_sha256": "db5584dc1a7a24d4d8d219192deeed03e7d41a70d5e322fc430ba61d9fa9c375",
     "role": "1,288-bit reversed binary macro -- yellowblueprimes/matrixsumlist/lastwordsbeforearchichoice order"},
    {"id": 1710, "from_id": "user9815232", "edited": "2024-04-24T09:58:18",
     "text_sha256": "0499da8d2eb85062b529a71eb7ab305a4c8c87e830538b14d1f2b42953fb5c69",
     "role": "first formal 2020 hint"},
)


def _flatten_text(message):
    value = message.get("text", "")
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def verify_creator_reply_edges(export_dir=DEFAULT_EXPORT_DIR):
    """Independently re-extracts structural (not interpretive) facts for
    every message in the candidate reply-edge and standalone-broadcast
    sets, from the raw export JSON, and asserts they match what was
    recorded in this file -- including the edited timestamp, which the
    first version of this check omitted."""
    payload = json.loads((Path(export_dir) / "result.json").read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in payload["messages"]}

    mismatches = []
    for expected in REPLY_EDGE_MESSAGES + STANDALONE_CREATOR_BROADCASTS:
        actual = by_id.get(expected["id"])
        if actual is None:
            mismatches.append((expected["id"], "message not found in export"))
            continue
        actual_hash = hashlib.sha256(_flatten_text(actual).encode()).hexdigest()
        if actual.get("from_id") != expected["from_id"]:
            mismatches.append((expected["id"], "from_id mismatch"))
        if actual.get("reply_to_message_id") != expected.get("reply_to_message_id"):
            mismatches.append((expected["id"], "reply_to_message_id mismatch"))
        if actual.get("edited") != expected.get("edited"):
            mismatches.append((expected["id"], "edited timestamp mismatch"))
        if actual_hash != expected["text_sha256"]:
            mismatches.append((expected["id"], "text content changed"))
    if mismatches:
        raise AssertionError(f"frozen reply-edge evidence drifted: {mismatches}")

    creator_ids = {m["id"] for m in REPLY_EDGE_MESSAGES if m["is_creator"]}
    creator_ids |= {m["id"] for m in STANDALONE_CREATOR_BROADCASTS}
    creator_from_ids = {by_id[mid]["from_id"] for mid in creator_ids}
    if creator_from_ids != {CREATOR_ACCOUNT_ID}:
        raise AssertionError(f"creator messages don't share one consistent from_id: {creator_from_ids}")

    return {
        "reply_edge_messages": len(REPLY_EDGE_MESSAGES),
        "standalone_creator_broadcasts": len(STANDALONE_CREATOR_BROADCASTS),
        "creator_account_id": CREATOR_ACCOUNT_ID,
        "creator_identity_consistent": True,
        "note": (
            "This is a Step-2 candidate SUBSET, not the full reply-edge "
            "universe -- see creator_reply_universe()."
        ),
        "sharp_finding": (
            "message 20223 (creator) replies to 20221, NOT 20222 -- it "
            "answers a different question ('what format key') than the "
            "one immediately before it ('our first hint is your last "
            "command'). 20222's actual reply is 20224 (a bare decline "
            "emoji); the follow-up 20226 is never answered anywhere in "
            "the export."
        ),
        "epistemic_caveat": (
            "6497, 8446, and 1710 all carry non-null 'edited' timestamps "
            "well after their original post dates -- see "
            "witness_layer() for how far back each is independently "
            "witnessed."
        ),
    }


def creator_reply_universe():
    """Loads the mechanically-extracted FULL universe of creator reply
    edges (every message with from_id == CREATOR_ACCOUNT_ID and a
    non-null reply_to_message_id, plus its parent's from_id) -- 148 rows,
    no manual topic selection. Fixes the earlier version's manually-
    curated 7-message set standing in for "the" evidence."""
    return json.loads(CREATOR_REPLY_UNIVERSE_PATH.read_text())


def verify_creator_reply_universe(export_dir=DEFAULT_EXPORT_DIR):
    """Re-derives the full universe from the raw export and asserts it
    matches the pinned artifact exactly (row count, structure digest,
    and source export digest)."""
    pinned = creator_reply_universe()
    payload = json.loads((Path(export_dir) / "result.json").read_text(encoding="utf-8"))
    source_sha256 = hashlib.sha256((Path(export_dir) / "result.json").read_bytes()).hexdigest()
    if source_sha256 != pinned["source_export_sha256"]:
        raise AssertionError("Telegram export file has changed since the universe was frozen")

    messages = payload["messages"]
    by_id = {m["id"]: m for m in messages}
    creator_replies = sorted(
        (m for m in messages if m.get("from_id") == CREATOR_ACCOUNT_ID and m.get("reply_to_message_id")),
        key=lambda m: m["id"],
    )
    rows = []
    for m in creator_replies:
        parent = by_id.get(m["reply_to_message_id"])
        rows.append({
            "id": m["id"],
            "date": m.get("date"),
            "edited": m.get("edited"),
            "reply_to_message_id": m["reply_to_message_id"],
            "parent_from_id": parent.get("from_id") if parent else None,
            "parent_exists_in_export": parent is not None,
            "text_sha256": hashlib.sha256(_flatten_text(m).encode()).hexdigest(),
        })
    structure_sha256 = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    if len(rows) != pinned["row_count"]:
        raise AssertionError(f"row count drifted: pinned {pinned['row_count']}, actual {len(rows)}")
    if structure_sha256 != pinned["structure_sha256"]:
        raise AssertionError("creator reply universe structure drifted from pinned artifact")
    return pinned


# ---------------------------------------------------------------------------
# 5. Witness layer for edited/standalone creator messages
# ---------------------------------------------------------------------------

def witness_layer():
    """Loads the pinned witness records for 1710, 8446, and 6497 -- each
    checked against independently-located earlier messages to establish
    how far back the current bytes are witnessed relative to the
    recorded edit date."""
    return json.loads(WITNESS_LAYER_PATH.read_text())


# Exact expected target/witness ids per entry, asserted against the pinned
# artifact so a silently dropped or swapped witness fails loudly rather
# than passing on whatever happens to be in the JSON file.
EXPECTED_WITNESS_IDS = {
    "1710": {"target": 1710, "witnesses": (3388, 3644)},
    "8446": {"target": 8446, "witnesses": (8448, 15851)},
    "6497": {"target": 6497, "witnesses": (27274,)},
}


def _normalize_for_containment(text):
    """Strips quote marks and an optional leading 'old hint:' line so a
    paraphrase-level community reproduction can be compared to the
    creator's original wording on substance, not exact formatting."""
    text = text.replace('"', "")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    if lines and lines[0].rstrip(":").lower() == "old hint":
        lines = lines[1:]
    return " ".join(lines)


def verify_witness_layer(export_dir=DEFAULT_EXPORT_DIR):
    pinned = witness_layer()
    if set(pinned) != set(EXPECTED_WITNESS_IDS):
        raise AssertionError(f"witness layer covers unexpected targets: {sorted(pinned)}")

    payload = json.loads((Path(export_dir) / "result.json").read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in payload["messages"]}

    mismatches = []
    actual_text = {}
    for target_id, entry in pinned.items():
        expected = EXPECTED_WITNESS_IDS[target_id]
        if entry["target"]["id"] != expected["target"]:
            mismatches.append((target_id, "target id does not match expected"))
        actual_witness_ids = tuple(w["id"] for w in entry["witnesses"])
        if actual_witness_ids != expected["witnesses"]:
            mismatches.append((target_id, f"witness ids {actual_witness_ids} != expected {expected['witnesses']}"))

        for record in (entry["target"], *entry["witnesses"]):
            actual = by_id.get(record["id"])
            if actual is None:
                mismatches.append((record["id"], "message not found in export"))
                continue
            if actual.get("from_id") != record["from_id"]:
                mismatches.append((record["id"], "from_id mismatch"))
            if actual.get("date") != record["date"]:
                mismatches.append((record["id"], "date mismatch"))
            if actual.get("edited") != record["edited"]:
                mismatches.append((record["id"], "edited timestamp mismatch"))
            text = _flatten_text(actual)
            actual_text[record["id"]] = text
            actual_hash = hashlib.sha256(text.encode()).hexdigest()
            if actual_hash != record["text_sha256"]:
                mismatches.append((record["id"], "text content changed"))
    if mismatches:
        raise AssertionError(f"witness layer drifted: {mismatches}")

    # Temporal-order assertion: every witness must predate the edit it is
    # supposed to be witnessing around, or it proves nothing.
    for target_id, entry in pinned.items():
        target_edited = datetime.datetime.fromisoformat(entry["target"]["edited"])
        for witness in entry["witnesses"]:
            witness_date = datetime.datetime.fromisoformat(witness["date"])
            if not witness_date < target_edited:
                raise AssertionError(
                    f"{target_id}: witness {witness['id']} ({witness_date}) does not "
                    f"predate target {target_id}'s edit ({target_edited})"
                )

    if pinned["1710"]["target"]["text_sha256"] in {w["text_sha256"] for w in pinned["1710"]["witnesses"]}:
        raise AssertionError("1710's witnesses were expected to be paraphrase-level, not byte-identical")
    normalized_1710 = _normalize_for_containment(actual_text[1710])
    for witness_id in (3388, 3644):
        normalized_witness = _normalize_for_containment(actual_text[witness_id])
        if normalized_witness != normalized_1710:
            raise AssertionError(
                f"1710's normalized content does not match witness {witness_id}: "
                f"{normalized_witness!r} != {normalized_1710!r}"
            )

    if pinned["8446"]["target"]["text_sha256"] not in {w["text_sha256"] for w in pinned["8446"]["witnesses"]}:
        raise AssertionError("8446 was expected to have a byte-identical pre-edit witness (15851)")
    if pinned["6497"]["target"]["text_sha256"] not in {w["text_sha256"] for w in pinned["6497"]["witnesses"]}:
        raise AssertionError("6497 was expected to have a byte-identical witness (27274)")

    return {
        "1710": pinned["1710"]["classification"],
        "8446": pinned["8446"]["classification"],
        "6497": pinned["6497"]["classification"],
    }


# ---------------------------------------------------------------------------
# Full freeze
# ---------------------------------------------------------------------------

def freeze(html_path=DEFAULT_HTML, export_dir=DEFAULT_EXPORT_DIR):
    return {
        "wayback_captures": verify_wayback_captures(),
        "wayback_textarea_content": verify_wayback_textarea_content_pinned(),
        "current_page_structure": verify_current_page_structure(html_path),
        "solved_stage_syntax": verify_solved_stage_syntax(),
        "creator_reply_edges_candidate_subset": verify_creator_reply_edges(export_dir),
        "creator_reply_universe": verify_creator_reply_universe(export_dir),
        "witness_layer": verify_witness_layer(export_dir),
        "explicitly_excluded": (
            "all community-authored interpretation (SALVATION/SALVATION-"
            "OF-ZION readings, 'Salphation' folk etymology, numerology, "
            "atomic-number rebuses); all prior-phase PROSE conclusions "
            "not re-derived from a primary artifact above; any candidate "
            "topology's scoring or ranking (that is Steps 2-5, not this "
            "freeze); Step 2's relevance filter over the 148-row reply "
            "universe (also not this freeze)"
        ),
    }


def self_test():
    frozen = {
        "wayback_captures": verify_wayback_captures(),
        "wayback_textarea_content": verify_wayback_textarea_content_pinned(),
        "current_page_structure": verify_current_page_structure(),
        "solved_stage_syntax": verify_solved_stage_syntax(),
    }
    assert frozen["wayback_captures"]["capture_count"] == 5
    assert len(frozen["wayback_textarea_content"]["per_capture"]) == 5
    assert frozen["current_page_structure"]["segments_in_order"] == EXPECTED_SEGMENTS
    assert frozen["current_page_structure"]["cosmic_duality_matches_known_blob"] is True
    assert frozen["solved_stage_syntax"]["all_recovered_at_rank_1"] is True
    assert frozen["solved_stage_syntax"]["boundaries"] == ("phase2", "phase3", "phase3_2")

    export_available = (DEFAULT_EXPORT_DIR / "result.json").exists()
    if export_available:
        reply_edges = verify_creator_reply_edges()
        assert reply_edges["creator_identity_consistent"] is True
        assert reply_edges["reply_edge_messages"] == 7
        assert reply_edges["standalone_creator_broadcasts"] == 2

        universe = verify_creator_reply_universe()
        assert universe["row_count"] == 148

        witnesses = verify_witness_layer()
        assert witnesses["1710"] == "contemporaneously witnessed; operational content stable"
        assert witnesses["8446"] == (
            "contemporaneously decoded and pre-edit byte-witnessed; operational order stable"
        )
        assert witnesses["6497"] == (
            "creator-authored final text, witnessed by 2024; original-2021 wording unresolved"
        )

    print(
        "[*] self-test OK: 5 Wayback captures internally consistent, both "
        "textareas byte-identical across the full 2023-06-01 to 2026-04-05 "
        "observation window (pinned from the recorded live verification; "
        "re-run --live to re-check over the network); live DOM "
        "segmentation matches the authenticated 13-segment order; "
        "solved-stage syntax (Phase 2/3/3.2) reproduces all 3 known "
        "hashes at rank 1"
        + (
            "; 7-message candidate subset + full 148-row creator reply "
            "universe + 3-message witness layer all verified against the "
            "raw export"
            if export_available
            else " (Telegram export unavailable -- reply-edge checks skipped)"
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    network_group = parser.add_mutually_exclusive_group()
    network_group.add_argument(
        "--live", action="store_true",
        help="re-verify Wayback textarea content over the network",
    )
    network_group.add_argument(
        "--local-capture-dir", type=Path,
        help="re-verify Wayback textarea content from a local capture-dir mirror (no network)",
    )
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.live:
        report = verify_wayback_textarea_content_live()
        print(json.dumps(report, indent=2))
        return
    if args.local_capture_dir:
        report = verify_wayback_textarea_content_local(args.local_capture_dir)
        print(json.dumps(report, indent=2))
        return
    result = freeze()
    if args.json:
        print(json.dumps(result, indent=2, default=repr))
    else:
        for key, value in result.items():
            print(f"-- {key} --")
            print(value)


if __name__ == "__main__":
    main()
