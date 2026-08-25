#!/usr/bin/env python3
"""Phase 415: corrected blinded independent reconstruction of P32TRAILING.

See ``doc/Brainstorms/2026-08-25 - Phase 415 P32TRAILING Blinded
Independent Reconstruction Corrected Pre-Registration.md`` for the frozen
protocol this module implements. Supersedes Phase 414
(``phase414_p32trailing_blinded_reconstruction_audit``), which closed
``protocol_invalid``: 3 of its first 5 clean-context solver invocations
failed schema validation, each confirmed by actually running
``parse_submission()``/``validate_submission_schema()`` against the exact
raw response text. All three failures traced to one field:
``preimage_utf8_hex``, a hand-computed lowercase-hex encoding of the
solver's own ``display`` string, required with no tool access. That field
carries zero interpretive content -- a parsed JSON string is already an
exact, unambiguous value -- so requiring solvers to hand-compute its hex
encoding tested manual arithmetic, not the derivation reasoning the
experiment actually cares about.

This module corrects exactly two things and reuses everything else from
``phase414_p32trailing_blinded_reconstruction_audit`` unchanged (imported
directly, not copied): the evidence packet and its pinned hash, blinding
checks, closure validation and its (still empty) preregistered allowlist,
the promotion rule, the redacted oracle-testing pipeline, and the
deterministic candidate ordering.

1. ``preimage_utf8_hex`` is no longer a solver-provided field -- a
   submission that still includes it is rejected wholesale as an
   unexpected key. This module computes it itself, mechanically, as
   ``display.encode("utf-8").hex()``, with no trimming, case-folding, or
   Unicode normalization of ``display`` first.
2. A literal, case-insensitive ``placeholder``, ``todo``, ``fixme``, or
   ``...`` (three-dot ellipsis) in ``display``, ``derivation``,
   ``reasoning_text``, or a present closure's ``instruction_quote`` voids
   the whole submission -- unfinished template residue is syntactically
   valid JSON and would otherwise silently pass through as a real,
   nonsense candidate.

``validate_submission_schema()`` is redefined here to implement those two
corrections. ``eligible_submissions()`` and ``evaluate_panel()`` are also
redefined -- not because their own logic changed, but because they call
``validate_submission_schema()`` by name within their defining module's
own namespace, so Phase 414's versions would otherwise keep calling
Phase 414's schema check regardless of what this module defines.
"""

import phase414_p32trailing_blinded_reconstruction_audit as phase414

# Re-exported unchanged -- see this phase's preregistration's "Deliverable"
# section for the full list of what is reused by direct import rather than
# copied.
build_evidence_packet = phase414.build_evidence_packet
write_evidence_packet = phase414.write_evidence_packet
PHASE32_PLAINTEXT_SHA256 = phase414.PHASE32_PLAINTEXT_SHA256
EVIDENCE_PACKET_SHA256 = phase414.EVIDENCE_PACKET_SHA256
MAX_SOLVER_CANDIDATES = phase414.MAX_SOLVER_CANDIDATES
FAMILY_PROMOTION_THRESHOLD = phase414.FAMILY_PROMOTION_THRESHOLD
INVOCATION_CAP = phase414.INVOCATION_CAP
PANEL_TARGET = phase414.PANEL_TARGET
PHASE410_EXACT_VARIANT = phase414.PHASE410_EXACT_VARIANT
QUALIFYING_CLOSURE_INSTRUCTION_SPANS = phase414.QUALIFYING_CLOSURE_INSTRUCTION_SPANS
FORBIDDEN_VOCAB = phase414.FORBIDDEN_VOCAB
FORBIDDEN_PHASE_RE = phase414.FORBIDDEN_PHASE_RE
ALLOWED_PHASE_NUMBERS = phase414.ALLOWED_PHASE_NUMBERS
GITHUB_URL_RE = phase414.GITHUB_URL_RE
STRUCTURAL_TIERS = phase414.STRUCTURAL_TIERS
DEFAULT_TARGET_ADDRESSES = phase414.DEFAULT_TARGET_ADDRESSES
REQUIRED_CLOSURE_KEYS = phase414.REQUIRED_CLOSURE_KEYS

_collect_strings = phase414._collect_strings
submission_full_text = phase414.submission_full_text
blinding_violations = phase414.blinding_violations
validate_closure = phase414.validate_closure
promote_candidates = phase414.promote_candidates
classify_plaintext = phase414.classify_plaintext
_is_hit = phase414._is_hit
test_material_cbc = phase414.test_material_cbc
test_material_ecb = phase414.test_material_ecb
test_material_stream = phase414.test_material_stream
test_material_secondary_families = phase414.test_material_secondary_families
test_candidate = phase414.test_candidate
_promotion_sort_key = phase414._promotion_sort_key
test_candidates = phase414.test_candidates
parse_submission = phase414.parse_submission
JSON_FENCE_RE = phase414.JSON_FENCE_RE
_reject_duplicate_keys = phase414._reject_duplicate_keys


# ── Corrected strict submission schema ──────────────────────────────────
#
# Same "reject wholesale, never coerce" discipline as Phase 414. The two
# corrections are: (1) `preimage_utf8_hex` is computed here, not accepted
# from the solver -- its presence as a submitted key is itself a schema
# violation; (2) unfinished template residue is checked in every
# solver-authored free-text field.

REQUIRED_SUBMISSION_KEYS = phase414.REQUIRED_SUBMISSION_KEYS
REQUIRED_CANDIDATE_KEYS = frozenset({"display", "derivation", "rank"})
ALLOWED_CANDIDATE_KEYS = REQUIRED_CANDIDATE_KEYS | {"closure"}

# Case-insensitive; matched as a plain substring, not a regex token
# boundary, so e.g. "TODO:" or "(TODO)" still trips it -- deliberately
# broad, since the point is to catch residue, not to be lenient about its
# exact formatting.
RESIDUE_MARKERS = ("placeholder", "todo", "fixme", "...")


def _residue_violation(text):
    lowered = text.lower()
    for marker in RESIDUE_MARKERS:
        if marker in lowered:
            return marker
    return None


def validate_submission_schema(submission):
    """Returns (True, parsed_candidates) or (False, reason). Never
    normalizes anything -- a submission either matches the frozen shape
    exactly or the whole thing is rejected. See module docstring for the
    two corrections relative to Phase 414's version of this function."""
    if not isinstance(submission, dict) or set(submission.keys()) != REQUIRED_SUBMISSION_KEYS:
        return False, "unexpected or missing top-level keys"
    if not isinstance(submission["tool_used"], bool):
        return False, "tool_used must be an explicit boolean"
    if not isinstance(submission["reasoning_text"], str):
        return False, "reasoning_text must be a string"
    residue = _residue_violation(submission["reasoning_text"])
    if residue:
        return False, f"reasoning_text contains unfinished template residue ({residue!r})"

    raw_candidates = submission["candidates"]
    if not isinstance(raw_candidates, list) or not (1 <= len(raw_candidates) <= MAX_SOLVER_CANDIDATES):
        return False, f"candidates must be a list of 1..{MAX_SOLVER_CANDIDATES} raw entries (before dedup)"

    parsed, ranks, seen_material = [], [], set()
    for candidate in raw_candidates:
        if not isinstance(candidate, dict) or not (REQUIRED_CANDIDATE_KEYS <= set(candidate.keys()) <= ALLOWED_CANDIDATE_KEYS):
            return False, "candidate has unexpected or missing keys"

        display = candidate["display"]
        if not isinstance(display, str) or not display:
            return False, "display must be a non-empty string"
        residue = _residue_violation(display)
        if residue:
            return False, f"display contains unfinished template residue ({residue!r})"

        derivation = candidate["derivation"]
        if not isinstance(derivation, str) or not derivation:
            return False, "derivation must be a non-empty string"
        residue = _residue_violation(derivation)
        if residue:
            return False, f"derivation contains unfinished template residue ({residue!r})"

        # preimage_utf8_hex is deliberately NOT accepted from the solver --
        # it is computed mechanically from `display`, the sole
        # authoritative field, with no normalization of any kind.
        try:
            material = display.encode("utf-8")
        except UnicodeEncodeError:
            return False, "display is not valid UTF-8-encodable text"
        hex_value = material.hex()

        rank = candidate["rank"]
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            return False, "rank must be a positive integer"
        ranks.append(rank)

        closure = candidate.get("closure")
        if closure is not None:
            if not isinstance(closure, dict) or set(closure.keys()) != REQUIRED_CLOSURE_KEYS:
                return False, "closure has unexpected or missing keys"
            if closure["zero_alternatives"] is not True:
                return False, "closure.zero_alternatives must be the literal boolean true whenever present"
            quote = closure["instruction_quote"]
            if not isinstance(quote, str) or not quote:
                return False, "closure.instruction_quote must be a non-empty string"
            residue = _residue_violation(quote)
            if residue:
                return False, f"closure.instruction_quote contains unfinished template residue ({residue!r})"
            for offset_key in ("instruction_offset_start", "instruction_offset_end"):
                offset_value = closure[offset_key]
                if not isinstance(offset_value, int) or isinstance(offset_value, bool) or offset_value < 0:
                    return False, f"closure.{offset_key} must be a nonnegative plain integer"
            if closure["instruction_offset_start"] >= closure["instruction_offset_end"]:
                return False, "closure.instruction_offset_start must be < instruction_offset_end"
            spans = closure["token_spans"]
            if not isinstance(spans, list) or not spans:
                return False, "closure.token_spans must be a non-empty list"
            for span in spans:
                if not isinstance(span, (list, tuple)) or len(span) != 2:
                    return False, "closure.token_spans entries must be exactly [start, end]"
                start, end = span
                if (
                    not isinstance(start, int) or isinstance(start, bool) or start < 0
                    or not isinstance(end, int) or isinstance(end, bool)
                    or start >= end
                ):
                    return False, (
                        "closure.token_spans entries must be nonnegative integer [start, end] pairs "
                        "with start < end"
                    )

        if material in seen_material:
            return False, "duplicate candidate within one submission (display encodes to identical bytes)"
        seen_material.add(material)
        parsed.append({**candidate, "preimage_utf8_hex": hex_value, "material": material})

    if sorted(ranks) != list(range(1, len(raw_candidates) + 1)):
        return False, "ranks must be exactly a 1..n permutation with no duplicates or gaps"

    return True, parsed


def eligible_submissions(invocation_records):
    """Identical in logic to Phase 414's version -- redefined only because
    it must call THIS module's `validate_submission_schema()`, not Phase
    414's, and Python resolves a bare name against the function's own
    defining module's globals, not the caller's."""
    eligible = []
    for invocation_id, submission in invocation_records.items():
        ok, parsed_or_reason = validate_submission_schema(submission)
        if not ok:
            continue
        if submission["tool_used"]:
            continue
        if blinding_violations(submission_full_text(submission)):
            continue
        eligible.append({"invocation_id": invocation_id, **submission, "accepted": parsed_or_reason})
    return eligible


def evaluate_panel(invocation_records, invocations_used):
    """Identical in logic to Phase 414's version -- redefined only because
    it calls this module's own `eligible_submissions()` (see above)."""
    if invocations_used < len(invocation_records):
        raise ValueError("invocations_used cannot be smaller than the number of collected records")
    if invocations_used > INVOCATION_CAP:
        raise ValueError(
            f"invocations_used ({invocations_used}) exceeds the frozen cap ({INVOCATION_CAP}) -- "
            "the orchestrator must never call evaluate_panel() past the cap; this is a ledger bug, "
            "not a phase result, and must not be allowed to reach panel_ready"
        )
    eligible = eligible_submissions(invocation_records)
    if len(eligible) >= PANEL_TARGET:
        return {"status": "panel_ready", "eligible": eligible[:PANEL_TARGET]}
    if invocations_used >= INVOCATION_CAP:
        return {"status": "protocol_invalid", "eligible": eligible}
    return {"status": "need_more", "eligible": eligible}


def run_solvers():
    """See `phase414_p32trailing_blinded_reconstruction_audit.run_solvers`'s
    docstring -- identical contract, this phase's own `parse_submission()`
    and `evaluate_panel()` drive the same external spawn loop."""
    raise NotImplementedError(
        "run_solvers() cannot spawn agents from inside this script -- see its "
        "docstring. Use parse_submission() and evaluate_panel() to drive the "
        "external spawn loop."
    )


# ── Self-test ─────────────────────────────────────────────────────────────

def _valid_submission(candidates):
    return {"tool_used": False, "reasoning_text": "reasoning", "candidates": candidates}


def _candidate(display, rank, closure=None):
    entry = {"display": display, "derivation": f"derivation for {display!r}", "rank": rank}
    if closure is not None:
        entry["closure"] = closure
    return entry


def self_test():
    # -- Corrected schema: preimage_utf8_hex is computed, not accepted --
    submission = _valid_submission([_candidate("onefortwoforthree", 1)])
    ok, parsed = validate_submission_schema(submission)
    assert ok, parsed
    expected_hex = "onefortwoforthree".encode("utf-8").hex()
    assert parsed[0]["preimage_utf8_hex"] == expected_hex
    assert parsed[0]["material"] == b"onefortwoforthree"

    # A submission that still includes preimage_utf8_hex is rejected as an
    # unexpected key -- not silently accepted or stripped.
    poisoned = _valid_submission([
        {**_candidate("oops", 1), "preimage_utf8_hex": "6f6f7073"}
    ])
    ok, reason = validate_submission_schema(poisoned)
    assert not ok and "unexpected" in reason, (ok, reason)

    # -- Residue markers, one at a time, in every free-text field --
    for marker in ("placeholder", "TODO", "FiXmE", "the answer is..."):
        bad = _valid_submission([_candidate(f"candidate with {marker} inside", 1)])
        ok, reason = validate_submission_schema(bad)
        assert not ok and "residue" in reason, (marker, ok, reason)

        bad_derivation = _valid_submission([
            {**_candidate("cleandisplay", 1), "derivation": f"derivation with {marker}"}
        ])
        ok, reason = validate_submission_schema(bad_derivation)
        assert not ok and "residue" in reason, (marker, ok, reason)

        bad_reasoning = {
            "tool_used": False,
            "reasoning_text": f"overall reasoning with {marker}",
            "candidates": [_candidate("cleandisplay", 1)],
        }
        ok, reason = validate_submission_schema(bad_reasoning)
        assert not ok and "residue" in reason, (marker, ok, reason)

        bad_closure = _valid_submission([
            _candidate("cleandisplay", 1, closure={
                "instruction_offset_start": 0, "instruction_offset_end": 5,
                "instruction_quote": f"quote with {marker}",
                "token_spans": [[0, 5]], "zero_alternatives": True,
            })
        ])
        ok, reason = validate_submission_schema(bad_closure)
        assert not ok and "residue" in reason, (marker, ok, reason)

    # A benign use of literal "..." style punctuation still trips it --
    # deliberately broad, documented as intentional, not a false positive
    # to special-case away.
    ok, reason = validate_submission_schema(
        _valid_submission([_candidate("well, this is one possibility...", 1)])
    )
    assert not ok

    # -- No implicit normalization: whitespace and Unicode form matter --
    trailing_ws = _candidate("causality ", 1)
    no_ws = _candidate("causality", 1)
    ok1, parsed1 = validate_submission_schema(_valid_submission([trailing_ws]))
    ok2, parsed2 = validate_submission_schema(_valid_submission([no_ws]))
    assert ok1 and ok2
    assert parsed1[0]["preimage_utf8_hex"] != parsed2[0]["preimage_utf8_hex"]

    nfc = "café"       # NFC: e-acute as one code point
    nfd = "café"      # NFD: e + combining acute accent
    assert nfc != nfd  # sanity: genuinely distinct code point sequences
    ok3, parsed3 = validate_submission_schema(_valid_submission([_candidate(nfc, 1)]))
    ok4, parsed4 = validate_submission_schema(_valid_submission([_candidate(nfd, 1)]))
    assert ok3 and ok4
    assert parsed3[0]["preimage_utf8_hex"] != parsed4[0]["preimage_utf8_hex"]

    # -- Duplicate detection over encoded bytes, not a submitted field --
    dup = _valid_submission([_candidate("same", 1), _candidate("same", 2)])
    ok, reason = validate_submission_schema(dup)
    assert not ok and "duplicate" in reason, (ok, reason)

    # -- Rank permutation, closure gating, and top-level checks still hold
    bad_ranks = _valid_submission([_candidate("a", 1), _candidate("b", 1)])
    ok, reason = validate_submission_schema(bad_ranks)
    assert not ok and "rank" in reason

    bad_closure_false = _valid_submission([
        _candidate("a", 1, closure={
            "instruction_offset_start": 0, "instruction_offset_end": 5,
            "instruction_quote": "quote", "token_spans": [[0, 5]],
            "zero_alternatives": False,
        })
    ])
    ok, reason = validate_submission_schema(bad_closure_false)
    assert not ok and "zero_alternatives" in reason

    missing_tool_used = {"reasoning_text": "x", "candidates": [_candidate("a", 1)]}
    ok, reason = validate_submission_schema(missing_tool_used)
    assert not ok and "top-level" in reason

    # -- eligible_submissions / evaluate_panel reuse this module's own
    #    validate_submission_schema, and the cap/panel-readiness behavior
    #    matches Phase 414's --
    good_records = {
        f"inv-{i}": _valid_submission([_candidate(f"candidate-{i}", 1)])
        for i in range(5)
    }
    result = evaluate_panel(good_records, 5)
    assert result["status"] == "panel_ready" and len(result["eligible"]) == 5

    mixed_records = dict(list(good_records.items())[:2])
    mixed_records["inv-bad"] = poisoned
    result = evaluate_panel(mixed_records, 3)
    assert result["status"] == "need_more" and len(result["eligible"]) == 2

    result = evaluate_panel(mixed_records, INVOCATION_CAP)
    assert result["status"] == "protocol_invalid"

    try:
        evaluate_panel(good_records, INVOCATION_CAP + 1)
        raise AssertionError("evaluate_panel() must raise past the invocation cap")
    except ValueError:
        pass

    # A replayed invocation ID never inflates convergence -- same guarantee
    # as Phase 414, exercised here against this module's own
    # eligible_submissions().
    replayed = {"inv-1": good_records["inv-0"], "inv-1-again": good_records["inv-0"]}
    # Same dict key reused: only one entry can ever exist.
    single_key = {"inv-1": good_records["inv-0"]}
    assert len(eligible_submissions(single_key)) == 1
    assert len(eligible_submissions(replayed)) == 2  # two DIFFERENT ids, real convergence

    # -- End-to-end smoke test: phase415-produced candidates flow through
    #    the directly-imported Phase 414 promotion/testing pipeline --
    converging_records = {
        "inv-a": _valid_submission([_candidate("sharedguess", 1)]),
        "inv-b": _valid_submission([_candidate("sharedguess", 1)]),
    }
    eligible = eligible_submissions(converging_records)
    assert len(eligible) == 2
    packet_text, _ = build_evidence_packet()
    promoted = promote_candidates(eligible, packet_text)
    shared_hex = "sharedguess".encode("utf-8").hex()
    assert shared_hex in promoted
    assert promoted[shared_hex]["path"] == "convergence"
    assert promoted[shared_hex]["votes"] == 2

    # Test against a synthetic (not the real) blob so this smoke test
    # neither depends on nor reveals anything about P32TRAILING itself --
    # only confirms the plumbing between this module's schema output and
    # the imported oracle wrapper. The blob is deliberately encrypted with
    # the SAME password under test, so a correct round-trip recovers
    # printable English text -- a real, affirmative structural_hit
    # (strong_text tier), which is the pipeline behaving correctly, not a
    # false positive to explain away.
    import hashlib as _hashlib

    body = b"synthetic phase415 smoke-test plaintext, not a real secret"
    salt, ciphertext = phase414._make_cbc_blob(
        _hashlib.sha256(b"sharedguess").hexdigest().encode("ascii"), body
    )
    result = test_candidate(b"sharedguess", blob=(salt, ciphertext))
    assert result["outcome"] == "structural_hit", result
    assert result["records"][0]["structural_tier"] == "strong_text", result
    assert result["records"][0]["padding_tier"] == "ordinary_valid", result
    assert result["records"][0]["kdf_label"], result

    print("phase415_p32trailing_blinded_reconstruction_audit.self_test(): all checks passed")


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-packet", metavar="PATH")
    args = parser.parse_args()

    if args.write_packet:
        digest = write_evidence_packet(args.write_packet)
        print(f"wrote {args.write_packet} sha256={digest}")
        return

    self_test()


if __name__ == "__main__":
    main()
