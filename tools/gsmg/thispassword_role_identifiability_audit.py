#!/usr/bin/env python3
"""Steps 2-5 of the topology-identifiability audit (Step 1:
`topology_identifiability_evidence_freeze.py`), per the user's exact
2026-08-22 five-step spec:

  2. For each surviving topology/role, state what observable fact would
     uniquely distinguish it.
  3. Check whether that fact exists in the frozen evidence universe.
  4. Use hard contradictions only -- no weighted scoring, no password
     generation.
  5. If no discriminant exists, formally mark the topology unidentifiable
     from present evidence and stop internal phase churn until new
     primary evidence appears.

> **Correction (same-day review):** the first version of this file
> over-claimed on three counts, all fixed here:
> 1. The literal-stream check asserted `any_directional_marker_present =
>    False` unconditionally, without actually inspecting decoded
>    instruction semantics. That claim was also imprecise on its own
>    terms: the decoded stream DOES contain directional/deictic
>    vocabulary ('before', 'this', 'first', 'last', confirmed by decoding
>    `decimal_instruction_1`/`_2` and reading the legible `hash_prefix`/
>    `hash_suffix` segments). What is actually absent is a distinct,
>    EXPLICIT ATTACHMENT marker -- a structural connector (arrow, colon,
>    equals sign, an explicit 'skip'/'label'/'attach' token) that would
>    select a specific binding direction. `check_literal_stream_markers`
>    now checks for both, separately and honestly.
> 2. `observable_present_in_frozen_evidence` was hard-set to `False` for
>    all three roles regardless of any sub-check's result, so the
>    verdict was structurally guaranteed rather than derived. Each
>    role's value is now computed from real per-role predicates (see
>    `evaluate_role_observable()`).
> 3. The verdict claimed "formally unidentifiable... no model could
>    resolve it." The three declared observables are POSSIBLE sufficient
>    witnesses, not a proof they are the only ones a model could ever
>    use -- their absence shows no direct role-selecting witness turned
>    up under these three specific tests; it does not show no witness
>    could exist under some other model built from the same frozen
>    evidence (the ordered stream FAED -> instruction-1 -> instruction-2
>    -> hash_prefix -> SALPH is itself asymmetric, and Phase 373 already
>    demonstrated that different grammar models read that order
>    differently). The verdict is corrected to the defensible claim: no
>    direct witness found, no hard contradiction either, role remains
>    underdetermined, park pending new evidence -- not a claim about
>    what every possible model could or could not do.
>
> Also narrowed the corpus claim: zero creator messages containing the
> exact token 'thispassword' is a real, checked fact, but it is not the
> same as total creator silence about the role (a paraphrase, or a bare
> reply to a community reading, would not be caught by an exact-token
> search). A narrower, stronger check was added: none of the 148
> mechanically-extracted creator reply edges has a PARENT message
> containing the literal token either -- i.e. the creator has never been
> observed replying to a community message that used the word. Broader
> semantic-paraphrase coverage across the full corpus remains unproven.
>
> **P2 follow-up (same day):** two further refinements, neither changing
> the result. (a) "No hard contradiction eliminates any role" is scoped
> throughout to "no hard contradiction was detected under the declared
> checks" -- paraphrase-level creator evidence is explicitly unchecked,
> so the broader phrasing overstated what was actually verified. (b)
> Word-like attachment markers ('attach', 'label', 'skip') are now
> searched against the DECODED instruction words and legible
> hash_prefix/hash_suffix segments specifically, not the raw
> 1075-character cipher stream -- a substring hit against undecoded
> letter-cipher text would be a coincidence, not an instruction.
> Symbolic markers ('->', ':', '=') remain checked against the raw
> stream, since those could only appear there as literal punctuation.

**Scope note.** "Surviving topology" is read here as the specific,
already-narrowed tie this project has open: Phase 101's three
`thispassword` roles (`password_for_faed`, `faed_answer_is_password`,
`password_for_salph_blob`), which `doc/GSMG_TOPOLOGY_AUDIT.md`'s T1 row
calls "a genuine three-way unresolved tie... no edge here has a standing
default." Step 1's evidence classes (literal DOM bytes, solved-stage
grammar, creator reply edges) are specifically the evidence relevant to
this attachment question. The broader T0/T2/T8 macro-topology
comparison in that same document is a SEPARATE, already-closed
question -- its own Verdict section explicitly retains T0/T2/T8 as a
deliberate non-forced composition ("retained as ties, not forced to a
single winner," per the user's own prior instruction), not an open tie
awaiting a discriminant. It is out of scope here.

This module performs NO scoring (does not import or call
`TopologyCandidate.score`/`classify_ranking`/`run_role_discrimination`
from `thispassword_role_topology_discrimination_audit.py`), NO
candidate generation, and NO oracle query. It only asks, per role, under
three declared tests: would a specific, independently-checkable fact
exist in the Step-1 frozen evidence if this role were correct -- and
does it. A negative result across three declared tests is evidence of
absence-under-those-tests, not proof of absence-under-any-possible-test.

Usage:
    python3 tools/gsmg/thispassword_role_identifiability_audit.py --self-test
    python3 tools/gsmg/thispassword_role_identifiability_audit.py --json
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from page_structure_audit import DECIMAL_INSTRUCTIONS, DEFAULT_HTML, TextareaParser  # noqa: E402
from page_structure_audit import normalize_salphaseion, segment_salphaseion  # noqa: E402
from salphaseion_operand_binding_audit import EXPECTED_SEGMENTS  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402
from thispassword_role_topology_discrimination_audit import (  # noqa: E402
    CALIBRATION_ANALOG_AVAILABLE,
)
from topology_identifiability_evidence_freeze import (  # noqa: E402
    CREATOR_ACCOUNT_ID,
    creator_reply_universe,
    verify_creator_reply_edges,
)

ROLES = ("password_for_faed", "faed_answer_is_password", "password_for_salph_blob")

# ---------------------------------------------------------------------------
# Step 2: the discriminating observable each role would need.
# ---------------------------------------------------------------------------

DISCRIMINATING_OBSERVABLE = {
    "password_for_faed": (
        "An explicit attachment marker in the literal SalPhaseIon DOM "
        "stream reaching from decimal_instruction_2 (thispassword) past "
        "decimal_instruction_1 (lastwordsbeforearchichoice) onto `faed` "
        "-- OR a creator-authored message that names 'thispassword' "
        "together with FAED."
    ),
    "faed_answer_is_password": (
        "An explicit attachment marker binding decimal_instruction_2 "
        "(thispassword) directly onto decimal_instruction_1's own "
        "result with no further claimed object, in the literal DOM "
        "stream -- OR an analogous trailing-bare-noun-as-retroactive-"
        "label pattern already present in a SOLVED boundary's own "
        "grammar (Phase 2/3/3.2)."
    ),
    "password_for_salph_blob": (
        "An explicit attachment marker or creator statement connecting "
        "decimal_instruction_2 (thispassword) specifically to "
        "`salphaseion_aes_prefix` (the SALPH blob itself, not "
        "hash_prefix -- a separately-scoped instruction with its own "
        "SHA operand per Phase 121/372)."
    ),
}


# ---------------------------------------------------------------------------
# Step 3a: literal DOM stream check.
# ---------------------------------------------------------------------------

DEICTIC_VOCABULARY = ("before", "this", "first", "last")
# Symbolic markers are checked against the raw 1075-character stream
# (they could only ever appear there as literal punctuation, and the
# stream is otherwise letter-cipher/base64, so a hit would be
# unambiguous). Word-like markers are checked against the DECODED
# instruction words and the already-legible hash_prefix/hash_suffix
# segments instead -- the raw stream is cipher-encoded letters, so
# searching it for English words like 'label' would only ever find
# meaningless substring coincidences, not an actual instruction.
SYMBOLIC_ATTACHMENT_MARKERS = ("->", ":", "=")
WORD_ATTACHMENT_MARKERS = ("attach", "label", "skip")


def literal_stream_segments(html_path=DEFAULT_HTML):
    parser = TextareaParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    stream = normalize_salphaseion(parser.textareas[0])
    segments = segment_salphaseion(stream)
    observed_names = tuple(s.name for s in segments)
    if observed_names != EXPECTED_SEGMENTS:
        raise AssertionError("authenticated SalPhaseIon segment order changed")
    return stream, segments


def check_literal_stream_markers(html_path=DEFAULT_HTML):
    """Independently re-derives the literal byte content around
    thispassword and checks it for two DISTINCT things, not one:

    1. Directional/deictic VOCABULARY within the decoded instruction
       words themselves (decimal_instruction_1/2 are decoded via the
       same `decimal_transport` this project's own
       page_structure_audit.py uses; hash_prefix/hash_suffix are
       already-legible segments, not decimal-cipher). This vocabulary
       IS present -- it is not evidence either way about attachment
       direction, since 'before'/'this'/'first'/'last' each appear
       regardless of which role is correct.
    2. An explicit ATTACHMENT marker, checked as two separate kinds:
       symbolic markers (arrow, colon, equals) against the raw
       1075-character stream, since those could only appear there as
       literal punctuation; and word-like markers ('attach', 'label',
       'skip') against the DECODED/legible words only, not the raw
       cipher stream -- searching cipher-encoded letters for English
       substrings would find only coincidences, not an instruction.
    """
    stream, segments = literal_stream_segments(html_path)
    by_name = {s.name: stream[s.start:s.end] for s in segments}

    separator_contents = {
        name: content
        for name, content in by_name.items()
        if name.startswith("z_separator")
    }
    separators_uniform = len(set(separator_contents.values())) == 1

    # decimal_instruction_1/2's raw segment bytes are cipher-encoded, not
    # plaintext; DECIMAL_INSTRUCTIONS holds the already-established
    # decode (page_structure_audit.py), reused here rather than re-run.
    words = {
        "decimal_instruction_1": DECIMAL_INSTRUCTIONS[0],
        "decimal_instruction_2": DECIMAL_INSTRUCTIONS[1],
        "hash_prefix": by_name["hash_prefix"],
        "hash_suffix": by_name["hash_suffix"],
    }
    deictic_hits_by_segment = {
        name: tuple(w for w in DEICTIC_VOCABULARY if w in text)
        for name, text in words.items()
    }
    deictic_vocabulary_present = any(hits for hits in deictic_hits_by_segment.values())

    symbolic_marker_hits = tuple(m for m in SYMBOLIC_ATTACHMENT_MARKERS if m in stream)
    word_marker_hits_by_segment = {
        name: tuple(w for w in WORD_ATTACHMENT_MARKERS if w in text)
        for name, text in words.items()
    }
    word_marker_present = any(hits for hits in word_marker_hits_by_segment.values())
    symbolic_marker_present = bool(symbolic_marker_hits)
    explicit_attachment_marker_present = symbolic_marker_present or word_marker_present
    attachment_marker_hits = symbolic_marker_hits + tuple(
        w for hits in word_marker_hits_by_segment.values() for w in hits
    )

    return {
        "separator_contents": separator_contents,
        "separators_all_uniform": separators_uniform,
        "deictic_vocabulary_present": deictic_vocabulary_present,
        "deictic_hits_by_segment": deictic_hits_by_segment,
        "symbolic_marker_hits": symbolic_marker_hits,
        "word_marker_hits_by_segment": word_marker_hits_by_segment,
        "explicit_attachment_marker_present": explicit_attachment_marker_present,
        "attachment_marker_hits": attachment_marker_hits,
        "reasoning": (
            "The decoded instruction words DO carry directional/deictic "
            "vocabulary -- 'before' and 'last' in "
            "'lastwordsbeforearchichoice', 'this' in 'thispassword', "
            "'first' and 'last' again in the legible hash_prefix segment "
            "('...firsthintisyourlastcommand'). That vocabulary is "
            "present but not discriminating: each word appears "
            "regardless of which role is correct, so it does not by "
            "itself select an attachment direction. What is checked "
            "separately, and found absent, is a distinct EXPLICIT "
            "ATTACHMENT marker: symbolic markers (arrow, colon, equals "
            "sign) anywhere in the full 1075-character raw stream, and "
            "word-like markers ('skip'/'label'/'attach') within the "
            "DECODED/legible words specifically (not the raw cipher "
            "stream, where an English-word substring hit would be a "
            "coincidence, not an instruction). None of either kind was "
            "found. The three z-separators remain uniform single-"
            "character delimiters with no directional information of "
            "their own."
        ),
    }


# ---------------------------------------------------------------------------
# Step 3b: solved-stage grammar check.
# ---------------------------------------------------------------------------

def check_solved_stage_grammar_analog():
    """Reuses Phase 373's own finding (CALIBRATION_ANALOG_AVAILABLE),
    re-asserted here rather than re-derived, since the underlying fact
    (Phase 2 = single component, no order question; Phase 3/3.2 both use
    explicit forward imperative instructions -- 'perform SHA256',
    'giveit' -- never a bare trailing noun) has not changed since Phase
    373 established it."""
    return {
        "postpositive_label_analog_exists": CALIBRATION_ANALOG_AVAILABLE,
        "reasoning": (
            "Phase 3 and Phase 3.2 (Phase 2 excluded -- a single "
            "component has no order/attachment question) both use "
            "explicit forward imperative instruction tokens ('perform "
            "SHA256', 'giveit') that name their operation directly. "
            "Neither exhibits a bare trailing noun functioning as a "
            "retroactive label on a preceding result -- the specific "
            "structure faed_answer_is_password requires as precedent. "
            "No solved GSMG boundary in this project's holdings has "
            "this shape."
        ),
    }


# ---------------------------------------------------------------------------
# Step 3c: creator evidence check -- exact-token search, PLUS a narrower
# reply-parent check, PLUS role-specific co-occurrence checks. All are
# exact-token searches; none establishes semantic silence via paraphrase.
# ---------------------------------------------------------------------------

def _text_of(message):
    v = message.get("text", "")
    if isinstance(v, str):
        return v
    return "".join(i if isinstance(i, str) else i.get("text", "") for i in v)


def check_creator_mentions(export_dir=DEFAULT_EXPORT_DIR):
    payload = json.loads((Path(export_dir) / "result.json").read_text(encoding="utf-8"))
    messages = payload["messages"]
    by_id = {m["id"]: m for m in messages}

    creator_hits = [
        m["id"] for m in messages
        if m.get("from_id") == CREATOR_ACCOUNT_ID and "thispassword" in _text_of(m).lower()
    ]
    all_hits = [m["id"] for m in messages if "thispassword" in _text_of(m).lower()]

    faed_co_occurrence = [
        m["id"] for m in messages
        if m.get("from_id") == CREATOR_ACCOUNT_ID
        and "thispassword" in _text_of(m).lower() and "faed" in _text_of(m).lower()
    ]
    salph_co_occurrence = [
        m["id"] for m in messages
        if m.get("from_id") == CREATOR_ACCOUNT_ID
        and "thispassword" in _text_of(m).lower() and "salph" in _text_of(m).lower()
    ]

    universe = creator_reply_universe()
    reply_parent_hits = []
    for row in universe["rows"]:
        parent = by_id.get(row["reply_to_message_id"])
        if parent is not None and "thispassword" in _text_of(parent).lower():
            reply_parent_hits.append(row["id"])

    return {
        "creator_messages_mentioning_thispassword": len(creator_hits),
        "creator_hit_ids": tuple(creator_hits),
        "total_messages_mentioning_thispassword_any_author": len(all_hits),
        "creator_thispassword_faed_co_occurrence": tuple(faed_co_occurrence),
        "creator_thispassword_salph_co_occurrence": tuple(salph_co_occurrence),
        "creator_reply_rows_checked_for_thispassword_in_parent": len(universe["rows"]),
        "creator_reply_rows_with_thispassword_in_parent": tuple(reply_parent_hits),
        "note": (
            "Exact-token search only, in three forms: (a) the full "
            "export for any creator message containing 'thispassword' -- "
            "zero hits, out of 73 total mentions, all community-authored; "
            "(b) creator messages containing BOTH 'thispassword' and "
            "'faed'/'salph' -- zero, trivially, given (a); (c) the "
            f"{len(universe['rows'])}-row mechanically-extracted creator "
            "reply universe, checking whether the PARENT (community) "
            "message being replied to contains 'thispassword' -- zero "
            "hits, meaning the creator has never been observed directly "
            "replying to a community message that used the term. None of "
            "these three checks establishes full semantic silence: a "
            "paraphrase, or a reply that does not quote the term back, "
            "would not be caught by any of them."
        ),
    }


# ---------------------------------------------------------------------------
# Step 3 combined: map each role's declared observable onto the computed
# sub-check results above -- not a hardcoded assignment.
# ---------------------------------------------------------------------------

def evaluate_role_observable(role, stream_check, grammar_check, creator_check):
    if role == "password_for_faed":
        structural = stream_check["explicit_attachment_marker_present"]
        creator = bool(creator_check["creator_thispassword_faed_co_occurrence"])
        present = structural or creator
        detail = {"structural_marker_found": structural, "creator_co_occurrence_found": creator}
    elif role == "faed_answer_is_password":
        structural = stream_check["explicit_attachment_marker_present"]
        grammar_analog = grammar_check["postpositive_label_analog_exists"]
        present = structural or grammar_analog
        detail = {"structural_marker_found": structural, "solved_grammar_analog_found": grammar_analog}
    elif role == "password_for_salph_blob":
        structural = stream_check["explicit_attachment_marker_present"]
        creator = bool(creator_check["creator_thispassword_salph_co_occurrence"])
        present = structural or creator
        detail = {"structural_marker_found": structural, "creator_co_occurrence_found": creator}
    else:
        raise ValueError(f"unknown role: {role}")
    return present, detail


# ---------------------------------------------------------------------------
# Step 4: hard-contradiction check.
# ---------------------------------------------------------------------------

def check_hard_contradictions(stream_check, creator_check):
    """A role would be hard-contradicted if the frozen evidence
    positively asserted something incompatible with it (e.g. a creator
    statement saying thispassword does NOT refer to FAED, or a literal
    page marker explicitly blocking a skip). No such positive assertion
    exists anywhere in the frozen evidence for any of the three roles --
    the literal stream has no explicit attachment marker of any kind
    (for OR against any role), and the creator evidence is silent under
    every exact-token check run, not contradicting. This does not use
    the presence of deictic vocabulary as a contradiction signal either
    -- that vocabulary is common ground, not evidence against any role."""
    contradictions = {role: () for role in ROLES}
    if stream_check["explicit_attachment_marker_present"]:
        raise AssertionError(
            "an explicit attachment marker was found -- hard-contradiction "
            "logic must be revisited against its actual content and "
            "direction before concluding anything"
        )
    if creator_check["creator_messages_mentioning_thispassword"] != 0:
        raise AssertionError(
            "a creator message mentioning 'thispassword' was found -- "
            "hard-contradiction logic must be revisited against its "
            "actual content"
        )
    return {
        "contradictions_found": contradictions,
        "any_role_hard_contradicted": False,
        "reasoning": (
            "No frozen fact positively asserts anything about "
            "thispassword's target -- the literal stream has no explicit "
            "attachment marker under any of the three declared tests, "
            "and the creator record is silent under every exact-token "
            "check run (full-export search, role-specific co-occurrence, "
            "and reply-parent search). Silence under these tests is "
            "absence of a found witness, not a positive contradiction; "
            "Phase 373's corrected modeling already recorded each role's "
            "unsupported-edge count honestly without promoting any of "
            "them to 'falsified.' Nothing here changes that."
        ),
    }


# ---------------------------------------------------------------------------
# Step 5: bounded verdict -- no direct witness found under the three
# declared tests; no hard contradiction; underdetermined, not "formally
# unidentifiable by any model."
# ---------------------------------------------------------------------------

def run(html_path=DEFAULT_HTML, export_dir=DEFAULT_EXPORT_DIR):
    stream_check = check_literal_stream_markers(html_path)
    grammar_check = check_solved_stage_grammar_analog()
    creator_check = check_creator_mentions(export_dir)
    contradiction_check = check_hard_contradictions(stream_check, creator_check)

    per_role = {}
    for role in ROLES:
        observable_present, detail = evaluate_role_observable(
            role, stream_check, grammar_check, creator_check
        )
        per_role[role] = {
            "discriminating_observable": DISCRIMINATING_OBSERVABLE[role],
            "observable_present_in_frozen_evidence": observable_present,
            "observable_check_detail": detail,
            "hard_contradiction_present": bool(contradiction_check["contradictions_found"][role]),
        }

    no_witness_found = all(
        not r["observable_present_in_frozen_evidence"] for r in per_role.values()
    )
    no_hard_contradiction = not contradiction_check["any_role_hard_contradicted"]

    if no_witness_found and no_hard_contradiction:
        verdict = (
            "No direct role-selecting witness was found under the three "
            "declared primary-evidence tests (literal DOM stream, "
            "solved-stage grammar, creator reply record), and no hard "
            "contradiction was detected under those same declared checks "
            "(paraphrase-level creator evidence is explicitly unchecked, "
            "so this does not claim no contradiction could ever be found). "
            "The role remains underdetermined. Further "
            "internal scoring is not licensed, so park it until new "
            "primary evidence appears. This does NOT claim that no "
            "possible model built from the frozen evidence could ever "
            "distinguish the roles -- the three declared observables were "
            "possible sufficient witnesses, not proven necessary "
            "conditions, and the literal ordered stream itself (FAED -> "
            "instruction-1 -> instruction-2 -> hash_prefix -> SALPH) is "
            "asymmetric; a different grammar model could in principle "
            "read that order differently, exactly as Phase 373's two "
            "disagreeing modelings already demonstrated. This result is "
            "consistent with, not stronger than, Phase 373's inconclusive/"
            "model-dependent verdict."
        )
    else:
        verdict = (
            "Not the bounded-underdetermined case: at least one role has "
            "either a present discriminating observable or a hard "
            "contradiction -- see per-role detail."
        )

    return {
        "roles": per_role,
        "literal_stream_check": stream_check,
        "solved_stage_grammar_check": grammar_check,
        "creator_mentions_check": creator_check,
        "hard_contradiction_check": contradiction_check,
        "no_direct_witness_found_under_declared_tests": no_witness_found,
        "no_hard_contradiction": no_hard_contradiction,
        "verdict": verdict,
    }


def self_test():
    report = run()

    # Step 2: exactly the three known roles, each with a stated observable.
    assert set(report["roles"]) == set(ROLES)
    for role in ROLES:
        assert report["roles"][role]["discriminating_observable"]

    # Step 3a: literal stream re-derived from the live mirror, not
    # hardcoded. Deictic vocabulary IS present (this is now a checked
    # fact, not an omission); an explicit attachment marker is not.
    stream_check = report["literal_stream_check"]
    assert stream_check["separators_all_uniform"] is True
    assert set(stream_check["separator_contents"].values()) == {"z"}
    assert stream_check["deictic_vocabulary_present"] is True
    assert stream_check["deictic_hits_by_segment"]["decimal_instruction_1"] == ("before", "last")
    assert stream_check["deictic_hits_by_segment"]["decimal_instruction_2"] == ("this",)
    assert stream_check["deictic_hits_by_segment"]["hash_prefix"] == ("first", "last")
    assert stream_check["deictic_hits_by_segment"]["hash_suffix"] == ()
    # Symbolic markers checked against the raw stream; word-like markers
    # checked against the decoded/legible words only -- both empty, and
    # both are real, exercised checks (not one blanket assertion).
    assert stream_check["symbolic_marker_hits"] == ()
    assert stream_check["word_marker_hits_by_segment"] == {
        "decimal_instruction_1": (), "decimal_instruction_2": (),
        "hash_prefix": (), "hash_suffix": (),
    }
    assert stream_check["explicit_attachment_marker_present"] is False
    assert stream_check["attachment_marker_hits"] == ()

    # Step 3b: no calibration analog -- reused from Phase 373, not
    # silently re-derived differently.
    assert report["solved_stage_grammar_check"]["postpositive_label_analog_exists"] is False

    # Step 3c: creator checks against the real export, not assumed --
    # skip only if the export mirror is unavailable.
    if (DEFAULT_EXPORT_DIR / "result.json").exists():
        creator_check = report["creator_mentions_check"]
        assert creator_check["creator_messages_mentioning_thispassword"] == 0
        assert creator_check["creator_hit_ids"] == ()
        assert creator_check["total_messages_mentioning_thispassword_any_author"] == 73
        assert creator_check["creator_thispassword_faed_co_occurrence"] == ()
        assert creator_check["creator_thispassword_salph_co_occurrence"] == ()
        assert creator_check["creator_reply_rows_checked_for_thispassword_in_parent"] == 148
        assert creator_check["creator_reply_rows_with_thispassword_in_parent"] == ()

        # Cross-check against Step 1's own frozen artifacts.
        universe = creator_reply_universe()
        assert universe["row_count"] == 148
        candidate_subset = verify_creator_reply_edges(DEFAULT_EXPORT_DIR)
        assert candidate_subset["reply_edge_messages"] == 7

    # Step 3 combined: each role's observable presence is COMPUTED, not
    # hard-set -- confirm the detail dict actually reflects the sub-checks
    # (this would fail if evaluate_role_observable() were ever replaced
    # with a constant again).
    for role in ROLES:
        detail = report["roles"][role]["observable_check_detail"]
        assert detail["structural_marker_found"] is False
        assert report["roles"][role]["observable_present_in_frozen_evidence"] is False
    assert report["roles"]["faed_answer_is_password"]["observable_check_detail"][
        "solved_grammar_analog_found"
    ] is False
    if (DEFAULT_EXPORT_DIR / "result.json").exists():
        assert report["roles"]["password_for_faed"]["observable_check_detail"][
            "creator_co_occurrence_found"
        ] is False
        assert report["roles"]["password_for_salph_blob"]["observable_check_detail"][
            "creator_co_occurrence_found"
        ] is False

    # Step 4: hard-contradiction check is a real, exercised assertion
    # path (would raise if a marker/mention were ever found), not a
    # narrated absence.
    assert report["hard_contradiction_check"]["any_role_hard_contradicted"] is False
    for role in ROLES:
        assert report["roles"][role]["hard_contradiction_present"] is False

    # Step 5: bounded verdict only -- no overclaim to formal
    # unidentifiability, no claim about every possible model.
    assert report["no_direct_witness_found_under_declared_tests"] is True
    assert report["no_hard_contradiction"] is True
    assert report["verdict"].startswith("No direct role-selecting witness was found")
    assert "formally unidentifiable" not in report["verdict"].lower()
    assert "no model" not in report["verdict"].lower()

    # No scoring or candidate generation performed by this module: it
    # imports only the boolean calibration-gap flag from the scoring
    # file, never its scoring primitives (TopologyCandidate,
    # classify_ranking, role_candidates_*, run_role_discrimination).
    import ast
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    scoring_module_name = "thispassword_role_topology_discrimination_audit"
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == scoring_module_name
        for alias in node.names
    }
    assert imported_names == {"CALIBRATION_ANALOG_AVAILABLE"}, imported_names

    print(
        "[*] self-test OK: Steps 2-5 complete, corrected same-day. "
        "Directional/deictic vocabulary IS present in the decoded "
        "stream (before/this/first/last) but is not discriminating; no "
        "explicit ATTACHMENT marker was found under any of the three "
        "declared tests (literal stream, solved-stage grammar analog, "
        "creator record -- including a narrower reply-parent check "
        "across all 148 mechanically-extracted creator replies). No "
        "hard contradiction was detected under the declared checks. "
        "Verdict (bounded, not "
        "over-claimed): no direct role-selecting witness found under "
        "these three tests; role remains underdetermined; park pending "
        "new primary evidence. Consistent with, not stronger than, "
        "Phase 373's inconclusive/model-dependent verdict."
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    report = run()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for role, detail in report["roles"].items():
            print(f"-- {role} --")
            print(f"  observable: {detail['discriminating_observable']}")
            print(f"  present in evidence: {detail['observable_present_in_frozen_evidence']}")
        print(f"\nverdict: {report['verdict']}")


if __name__ == "__main__":
    main()
