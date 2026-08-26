#!/usr/bin/env python3
"""Phase 418: solution-complete sealed-target panel for P32TRAILING.

Implements the frozen protocol in the Phase 418 preregistration.  This module
does not invoke solvers.  It extends the exact Phase 416 sealed packet with the
already-solved Phase-3.2.1 and Phase-3.2.2 outputs, reuses Phase 416 parsing,
schema, eligibility, promotion, ordering, and redacted P32 evaluation, and
classifies exact Phase 270 duplicates before any oracle call.
"""

import base64
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase416_p32trailing_sealed_target_reconstruction_audit as phase416  # noqa: E402
import p32_sibling_password_audit as phase270  # noqa: E402
from cb_common import BLOBS  # noqa: E402
from data import (  # noqa: E402
    ALPHA_322,
    P32_TRAILING_BLOB_B64,
    VALIDATION_ANSWER,
    VALIDATION_ESCAPES,
    VALIDATION_NUM,
)
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402


# Phase 416 mechanics are reused by identity, not copied.
MAX_SOLVER_CANDIDATES = phase416.MAX_SOLVER_CANDIDATES
FAMILY_PROMOTION_THRESHOLD = phase416.FAMILY_PROMOTION_THRESHOLD
INVOCATION_CAP = phase416.INVOCATION_CAP
PANEL_TARGET = phase416.PANEL_TARGET
RESIDUE_MARKERS = phase416.RESIDUE_MARKERS
parse_submission = phase416.parse_submission
validate_submission_schema = phase416.validate_submission_schema
eligible_submissions = phase416.eligible_submissions
evaluate_panel = phase416.evaluate_panel
promote_candidates = phase416.promote_candidates
blinding_violations = phase416.blinding_violations
submission_full_text = phase416.submission_full_text
_promotion_sort_key = phase416._promotion_sort_key

INVOCATION_CONFIGURATION = {
    "agent_class": "general-purpose",
    "fork_turns": "none",
    "model_override": None,
    "reasoning_effort_override": None,
    "service_configuration": "default",
}

# Authenticated source/supplement pins.
PHASE32_PLAINTEXT_LENGTH = 2422
PHASE32_PLAINTEXT_SHA256 = "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"
ENCODED_321_START = 447
ENCODED_321_END = 1986
ENCODED_321_SHA256 = "bd7a29432546c67c4170e0c523ddbf43ae82d20ee187d1b4dbf7907a0faf4c7b"
CIPHER_321_LENGTH = 1539
CIPHER_321_SHA256 = "6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e"
ANSWER_321_LENGTH = 1539
ANSWER_321_SHA256 = "56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241"
VALIDATION_NUM_START = 1990
VALIDATION_NUM_END = 2139
VALIDATION_NUM_SHA256 = "71e3af174d533ad2c1c79fce64308f5fdf200f3cc50f059b2f1485a2c5f1765d"
CLUE_322_START = 2143
CLUE_322_END = 2288
CLUE_322_SHA256 = "fe2ee9e1d2218db842b5973f7761760d799ad6992cff4b6037fb0e940c7d358a"
P32_START = 2292
P32_END = 2422
P32_SOURCE_LENGTH = 130
P32_NORMALIZED_LENGTH = 128
P32_NORMALIZED_SHA256 = "b2e3f02fd7b79b9a0a85b9286d2b1f4e0e749171b3107d34ffc6b0b6fc2bdf5e"
ALPHA_322_SHA256 = "f48871f6826fcd56670d412ad9056c7b48caf112fefe50a767063b8d431d745f"
ANSWER_322_LENGTH = 91
ANSWER_322_SHA256 = "878b7afacc9e35412e76b8506cc8297fa5aeba5381e108dc421b71a0ab8993d8"
PHASE270_BASE_COUNT = 25
PHASE270_MATERIAL_COUNT = 50

# Replaced with mechanically rendered values before implementation is frozen.
SEALED_EVIDENCE_PACKET_LENGTH = 12348
SEALED_EVIDENCE_PACKET_SHA256 = "ce0a0979cfe0a16ee6a3bdd5f76f213b3f53533f02340d70db4e17e3ddf6c600"
SOLVER_PROMPT_LENGTH = 14441
SOLVER_PROMPT_SHA256 = "2e5f05164c0b393ba1fb6e14d101728f2c7f037c297050fc791dc34d6816cc63"
EVIDENCE_PACKET_ARTIFACT_PATH = SCRIPT_DIR / "phase418_sealed_evidence_packet.txt"
FROZEN_PROMPT_ARTIFACT_PATH = SCRIPT_DIR / "phase418_frozen_solver_prompt.txt"


def _check_bytes(label, value, length, digest):
    if len(value) != length:
        raise AssertionError(f"{label} length drifted: {len(value)} != {length}")
    actual = hashlib.sha256(value).hexdigest()
    if actual != digest:
        raise AssertionError(f"{label} SHA-256 drifted: {actual} != {digest}")


def recover_solution_state():
    """Freshly derive and verify every source and solved-output commitment."""
    derived = phase270.derive_sibling_outputs()
    plaintext = derived["phase32_plaintext"]
    components = derived["components"]
    offsets = components["offsets"]

    _check_bytes(
        "Phase 3.2 plaintext", plaintext,
        PHASE32_PLAINTEXT_LENGTH, PHASE32_PLAINTEXT_SHA256,
    )
    expected_offsets = {
        "encoded_321_start": ENCODED_321_START,
        "encoded_321_end": ENCODED_321_END,
        "validation_num_start": VALIDATION_NUM_START,
        "clue_322_start": CLUE_322_START,
        "p32_start": P32_START,
    }
    if offsets != expected_offsets:
        raise AssertionError(f"Phase 3.2 component offsets drifted: {offsets!r}")

    _check_bytes(
        "raw Phase-3.2.1 block", components["encoded_321"],
        ENCODED_321_END - ENCODED_321_START, ENCODED_321_SHA256,
    )
    cipher_321 = derived["cipher_321"].encode("ascii")
    answer_321 = derived["answer_321"].encode("ascii")
    _check_bytes("Phase-3.2.1 Beaufort ciphertext", cipher_321, CIPHER_321_LENGTH, CIPHER_321_SHA256)
    _check_bytes("Phase-3.2.1 solved answer", answer_321, ANSWER_321_LENGTH, ANSWER_321_SHA256)

    validation_num = components["validation_num"]
    clue_322 = components["clue_322"]
    _check_bytes(
        "Phase-3.2.2 numeral", validation_num,
        VALIDATION_NUM_END - VALIDATION_NUM_START, VALIDATION_NUM_SHA256,
    )
    _check_bytes(
        "Phase-3.2.2 clue", clue_322,
        CLUE_322_END - CLUE_322_START, CLUE_322_SHA256,
    )
    if validation_num != VALIDATION_NUM.encode("ascii"):
        raise AssertionError("Phase-3.2.2 numeral differs from the validation vector")
    if tuple(VALIDATION_ESCAPES) != (1, 4):
        raise AssertionError("Phase-3.2.2 escape pair drifted")
    _check_bytes("Phase-3.2.2 alphabet", ALPHA_322.encode("ascii"), 28, ALPHA_322_SHA256)
    answer_322 = derived["answer_322"].encode("ascii")
    _check_bytes("Phase-3.2.2 solved answer", answer_322, ANSWER_322_LENGTH, ANSWER_322_SHA256)
    if answer_322 != VALIDATION_ANSWER.encode("ascii"):
        raise AssertionError("fresh Phase-3.2.2 decode differs from VALIDATION_ANSWER")

    p32_source = components["p32_text"]
    if len(p32_source) != P32_SOURCE_LENGTH or offsets["p32_start"] + len(p32_source) != P32_END:
        raise AssertionError("P32 source span drifted")
    normalized_p32 = p32_source.replace(b"\r\n", b"")
    _check_bytes(
        "normalized P32 Base64", normalized_p32,
        P32_NORMALIZED_LENGTH, P32_NORMALIZED_SHA256,
    )
    if normalized_p32 != P32_TRAILING_BLOB_B64.encode("ascii"):
        raise AssertionError("structurally extracted P32 Base64 differs from data.py")
    raw = base64.b64decode(normalized_p32, validate=True)
    if not raw.startswith(b"Salted__"):
        raise AssertionError("P32 target no longer has an OpenSSL Salted__ header")

    phase416._verify_commitments()
    salt, ciphertext = BLOBS["P32TRAILING"]
    if raw[8:16] != salt or raw[16:] != ciphertext:
        raise AssertionError("P32 source container differs from the evaluator target")

    return {
        **derived,
        "cipher_321_bytes": cipher_321,
        "answer_321_bytes": answer_321,
        "answer_322_bytes": answer_322,
        "p32_source": p32_source,
        "p32_normalized": normalized_p32,
    }


def phase270_inventory(state=None):
    """Rebuild the exact Phase 270 material inventory and assert its size."""
    state = recover_solution_state() if state is None else state
    candidates, _ = phase270.build_candidates(
        state["answer_321"],
        state["answer_322"],
        state["phase32_plaintext"],
        state["components"]["offsets"]["p32_start"],
    )
    base_values = frozenset(record["value"] for record in candidates)
    materials = phase270.password_materials(candidates)
    material_values = frozenset(record["material"] for record in materials)
    if len(candidates) != PHASE270_BASE_COUNT or len(base_values) != PHASE270_BASE_COUNT:
        raise AssertionError("Phase 270 base inventory drifted from 25 unique values")
    if len(materials) != PHASE270_MATERIAL_COUNT or len(material_values) != PHASE270_MATERIAL_COUNT:
        raise AssertionError("Phase 270 material inventory drifted from 50 unique values")
    return {"base_values": base_values, "materials": material_values}


def classify_phase270_duplicate(material, inventory=None):
    if not isinstance(material, bytes):
        raise TypeError("candidate material must be bytes")
    inventory = phase270_inventory() if inventory is None else inventory
    digest_material = hashlib.sha256(material).hexdigest().encode("ascii")
    if material in inventory["materials"] or digest_material in inventory["materials"]:
        return "exact_duplicate_of_phase270"
    return "genuinely_new"


def _supplement_text(state):
    answer_321 = state["answer_321"]
    answer_322 = state["answer_322"]
    return "\n".join([
        "=" * 78,
        "ITEM 1B -- Solution-complete supplement for the nested solved stages.",
        "=" * 78,
        "",
        "These are community-derived values authenticated by their successful solved",
        "boundaries. They are not relabeled as creator-authored solution prose.",
        "",
        "Phase 3.2.1:",
        "  CP1141 conversion followed by Beaufort with key THEMATRIXHASYOU yields",
        "  this exact 1,539-character uppercase letters-only plaintext:",
        f"  {answer_321}",
        f"  SHA-256 commitment: {ANSWER_321_SHA256}",
        "",
        "Phase 3.2.2:",
        f"  exact keyed alphabet: {ALPHA_322}",
        "  ordered escape digits: (1, 4)",
        f"  exact 91-character decoded answer: {answer_322}",
        f"  SHA-256 commitment: {ANSWER_322_SHA256}",
        "",
    ])


def _scope_note():
    return "\n".join([
        "=" * 78,
        "ITEM 5 -- Prior-coverage scope note.",
        "=" * 78,
        "",
        "Obvious direct uses and sibling concatenations were already tested in an",
        "earlier bounded audit. This packet deliberately does not list those candidate",
        "values or labels, because doing so would anchor reconstruction to prior guesses.",
        "The orchestrator will compare every convergent candidate by exact bytes against",
        "that prior inventory and will not test an exact duplicate again.",
        "",
        "Do not self-censor a candidate merely because it appears straightforward or",
        "possibly prior-tested: submit every packet-supported candidate you actually",
        "judge among your best. Exact duplicate handling is mechanical and happens only",
        "after the five-submission panel closes.",
        "",
    ])


def build_sealed_evidence_packet():
    """Extend Phase 416's exact sealed packet with only the solved supplement."""
    state = recover_solution_state()
    base_packet, base_digest = phase416.build_sealed_evidence_packet()
    if base_digest != phase416.SEALED_EVIDENCE_PACKET_SHA256:
        raise AssertionError("Phase 416 base packet commitment drifted")
    marker = "\n" + "=" * 78 + "\nITEM 2 -- Three solved AES boundaries"
    if base_packet.count(marker) != 1:
        raise AssertionError("Phase 416 ITEM 2 insertion boundary drifted")
    before, after = base_packet.split(marker, 1)
    packet = before + "\n" + _supplement_text(state) + marker + after + "\n" + _scope_note()
    # The authenticated source commitments remain over original bytes; only the
    # human-readable UTF-8 artifact presentation is normalized to portable LF.
    packet = packet.replace("\r\n", "\n")
    _assert_solver_visible_content(packet, state)
    return packet, hashlib.sha256(packet.encode("utf-8")).hexdigest()


_SOLVER_PROMPT_TEMPLATE = """You are looking at a real, currently-unsolved piece of an authenticated
cryptographic puzzle. The evidence packet contains the already-decrypted parent
plaintext, all currently solved nested outputs, three worked solved boundaries,
the established password recipe, and the final output requirement. The actual
target ciphertext and prize address are deliberately not included; only their
shape and SHA-256 commitments are supplied. Do not retrieve them elsewhere.

{packet}

Propose from 1 to 10 candidate PREIMAGES P for the withheld target. The AES
password is lowercase ASCII SHA256(P).hexdigest(), not P. Submit exact P, not
its hash or UTF-8 hex. Explain which disclosed source or solved value and which
operation licenses every byte. The target has no local construction annotation,
so do not invent one silently. An earlier audit covered some obvious direct uses
and sibling concatenations, but its hidden exact-byte inventory is filtered only
after the panel closes. Do not omit a strong candidate merely because it seems
obvious or possibly prior-tested.

Respond with exactly one JSON object and nothing else. A single JSON markdown
fence is accepted only if it contains the entire response. Use exactly this shape:

{{
  "tool_used": <true or false, required and explicit>,
  "reasoning_text": "<your final overall reasoning>",
  "candidates": [
    {{
      "display": "<exact preimage P, exact characters and case>",
      "derivation": "<packet-local derivation licensing every piece of P>",
      "rank": <integer; ranks across all candidates must be exactly 1..n>
    }}
  ]
}}

Use no tool for any purpose while answering: no files or repository access,
shell, code, calculator, hashing, encryption/decryption, candidate testing,
environment variables, web search, or external lookup. Use only this prompt.
If you used any tool for any reason, set tool_used to true and explain why; the
submission will be excluded. Do not leave placeholder, TODO, or FIXME text in
any field. Do not add fields, repair the schema, repeat or normalize a candidate,
or provide prose outside the JSON object."""


def _assert_solver_visible_content(text, state):
    encoded = text.encode("utf-8")
    salt, ciphertext = BLOBS["P32TRAILING"]
    compact_b64 = base64.b64encode(b"Salted__" + salt + ciphertext).decode("ascii")
    for index in range(len(compact_b64) - 40 + 1):
        if compact_b64[index:index + 40] in text:
            raise AssertionError("P32 Base64 window leaked into solver-visible text")
    forbidden_strings = {
        "prize address": PRIZE_ADDRESS,
        "halving address": HALVING_ADDRESS,
    }
    for label, value in forbidden_strings.items():
        if value in text:
            raise AssertionError(f"{label} leaked into solver-visible text")
    if salt in encoded or ciphertext in encoded:
        raise AssertionError("raw P32 salt/ciphertext leaked into solver-visible text")
    required = (
        state["answer_321"],
        state["answer_322"],
        ALPHA_322,
        "(1, 4)",
        phase416.SALT_COMMITMENT_SHA256,
        phase416.CIPHERTEXT_COMMITMENT_SHA256,
        phase416.ADDRESS_COMMITMENT_SHA256,
    )
    for value in required:
        if value not in text:
            raise AssertionError(f"required solution-complete value absent: {value[:40]!r}")


def _render_solver_prompt():
    packet, _ = build_sealed_evidence_packet()
    prompt = _SOLVER_PROMPT_TEMPLATE.format(packet=packet)
    _assert_solver_visible_content(prompt, recover_solution_state())
    return prompt, hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _checked_artifact(text, digest, pinned_length, pinned_digest, path, label):
    if len(text) != pinned_length:
        raise AssertionError(f"{label} length drifted: {len(text)} != {pinned_length}")
    if digest != pinned_digest:
        raise AssertionError(f"{label} SHA-256 drifted: {digest} != {pinned_digest}")
    if path.read_bytes() != text.encode("utf-8"):
        raise AssertionError(f"{label} no longer matches committed artifact {path}")
    return text, digest


def build_evidence_packet():
    text, digest = build_sealed_evidence_packet()
    return _checked_artifact(
        text, digest, SEALED_EVIDENCE_PACKET_LENGTH, SEALED_EVIDENCE_PACKET_SHA256,
        EVIDENCE_PACKET_ARTIFACT_PATH, "Phase 418 evidence packet",
    )


def build_solver_prompt():
    packet, packet_digest = build_evidence_packet()
    prompt, digest = _render_solver_prompt()
    if packet not in prompt or packet_digest != SEALED_EVIDENCE_PACKET_SHA256:
        raise AssertionError("checked packet is not embedded byte-exactly in prompt")
    return _checked_artifact(
        prompt, digest, SOLVER_PROMPT_LENGTH, SOLVER_PROMPT_SHA256,
        FROZEN_PROMPT_ARTIFACT_PATH, "Phase 418 solver prompt",
    )


def write_artifacts():
    packet, packet_digest = build_sealed_evidence_packet()
    prompt, prompt_digest = _render_solver_prompt()
    EVIDENCE_PACKET_ARTIFACT_PATH.write_bytes(packet.encode("utf-8"))
    FROZEN_PROMPT_ARTIFACT_PATH.write_bytes(prompt.encode("utf-8"))
    return {
        "packet_length": len(packet),
        "packet_sha256": packet_digest,
        "prompt_length": len(prompt),
        "prompt_sha256": prompt_digest,
    }


def _redacted_promotion(material, promotion, disposition):
    return {
        "candidate_length": len(material),
        "candidate_sha256": hashlib.sha256(material).hexdigest(),
        "path": promotion["path"],
        "votes": promotion["votes"],
        "ranks": list(promotion["ranks"]),
        "best_rank": min(promotion["ranks"]),
        "phase270_disposition": disposition,
    }


def evaluate_candidate(material):
    """Call Phase 416's real full redacted P32 evaluator."""
    return phase416.test_candidate(material, "P32TRAILING")


def _assert_evaluation_redacted(evaluation):
    if evaluation.get("outcome") not in {"negative", "structural_hit", "terminal_hit"}:
        raise AssertionError("evaluator returned an unknown outcome")
    serialized = json.dumps(evaluation, sort_keys=True)
    for secret in (PRIZE_ADDRESS, HALVING_ADDRESS, P32_TRAILING_BLOB_B64):
        if secret in serialized:
            raise AssertionError("evaluator result leaked target material")
    forbidden_keys = {"plaintext", "password", "private_key", "private_keys", "address"}
    stack = [evaluation]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if forbidden_keys & set(value):
                raise AssertionError("evaluator result contains a forbidden sensitive field")
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)


def classify_completed_panel(eligible, evaluator=None):
    """Classify exactly five eligible submissions under the six frozen branches."""
    if len(eligible) != PANEL_TARGET:
        raise ValueError("outcome classification requires exactly five eligible submissions")
    evaluator = evaluate_candidate if evaluator is None else evaluator
    inventory = phase270_inventory()
    promoted = promote_candidates(eligible)

    all_materials = {
        candidate["material"]
        for submission in eligible
        for candidate in submission["accepted"]
    }
    duplicate_singleton_present = any(
        classify_phase270_duplicate(material, inventory) == "exact_duplicate_of_phase270"
        for material in all_materials
        if sum(
            candidate["material"] == material
            for submission in eligible
            for candidate in submission["accepted"]
        ) == 1
    )

    manifest = []
    internal_new = []
    for hex_value, promotion in sorted(promoted.items(), key=_promotion_sort_key):
        material = bytes.fromhex(hex_value)
        disposition = classify_phase270_duplicate(material, inventory)
        manifest.append(_redacted_promotion(material, promotion, disposition))
        if disposition == "genuinely_new":
            internal_new.append((material, promotion))

    evaluations = []
    stop_outcome = None
    for material, promotion in internal_new:
        evaluation = evaluator(material)
        _assert_evaluation_redacted(evaluation)
        if evaluation.get("material_sha256") not in (None, hashlib.sha256(material).hexdigest()):
            raise AssertionError("evaluator material digest disagrees with candidate")
        evaluations.append({
            **_redacted_promotion(material, promotion, "genuinely_new"),
            "evaluation": evaluation,
        })
        if evaluation["outcome"] in {"terminal_hit", "structural_hit"}:
            stop_outcome = evaluation["outcome"]
            break

    if stop_outcome == "terminal_hit":
        outcome = "terminal_hit"
    elif stop_outcome == "structural_hit":
        outcome = "structural_hit"
    elif internal_new:
        outcome = "novel_convergence_negative"
    elif manifest:
        outcome = "duplicate_only_convergence"
    else:
        outcome = "no_convergence"

    return {
        "outcome": outcome,
        "eligible_count": len(eligible),
        "distinct_candidate_count": len(all_materials),
        "promoted_count": len(manifest),
        "duplicate_promoted_count": sum(
            item["phase270_disposition"] == "exact_duplicate_of_phase270"
            for item in manifest
        ),
        "genuinely_new_promoted_count": len(internal_new),
        "evaluated_new_count": len(evaluations),
        "unevaluated_new_after_stop": len(internal_new) - len(evaluations),
        "phase270_duplicate_singleton_present": duplicate_singleton_present,
        "promoted": manifest,
        "evaluations": evaluations,
        "protocol_invalid_reason": None,
    }


def close_phase(invocation_records, invocations_used, evaluator=None):
    try:
        panel = evaluate_panel(invocation_records, invocations_used)
        if panel["status"] == "protocol_invalid":
            return {
                "outcome": "protocol_invalid",
                "protocol_invalid_reason": (
                    "five eligible submissions not obtained within eight invocations"
                ),
                "eligible_count": len(panel["eligible"]),
            }
        if panel["status"] == "need_more":
            return {"outcome": "need_more", "eligible_count": len(panel["eligible"])}
        return classify_completed_panel(panel["eligible"], evaluator=evaluator)
    except (AssertionError, ValueError, TypeError) as exc:
        return {"outcome": "protocol_invalid", "protocol_invalid_reason": str(exc)}


def invocation_task_name(invocation_number):
    if not isinstance(invocation_number, int) or isinstance(invocation_number, bool):
        raise TypeError("invocation number must be a plain integer")
    if not 1 <= invocation_number <= INVOCATION_CAP:
        raise ValueError("invocation number is outside the frozen 1..8 cap")
    return f"phase418_invocation_{invocation_number}"


def _candidate(display, rank=1):
    return {
        "display": display,
        "derivation": "derived only from the disclosed solved components",
        "rank": rank,
    }


def _submission(*displays):
    return {
        "tool_used": False,
        "reasoning_text": "packet-local reconstruction reasoning",
        "candidates": [_candidate(display, rank + 1) for rank, display in enumerate(displays)],
    }


def _eligible_fixture(rows):
    records = {f"inv-{i + 1}": _submission(*row) for i, row in enumerate(rows)}
    eligible = eligible_submissions(records)
    if len(eligible) != PANEL_TARGET:
        raise AssertionError("fixture did not produce five eligible submissions")
    return eligible


def _fixture_evaluator(outcomes, calls):
    def evaluate(material):
        calls.append(material)
        outcome = outcomes.get(material, "negative")
        return {
            "material_sha256": hashlib.sha256(material).hexdigest(),
            "outcome": outcome,
            "records": [],
        }
    return evaluate


def self_test():
    state = recover_solution_state()

    # Reuse-by-identity is load-bearing.
    assert parse_submission is phase416.parse_submission
    assert validate_submission_schema is phase416.validate_submission_schema
    assert eligible_submissions is phase416.eligible_submissions
    assert evaluate_panel is phase416.evaluate_panel
    assert promote_candidates is phase416.promote_candidates
    assert _promotion_sort_key is phase416._promotion_sort_key
    global SOLVER_PROMPT_LENGTH

    packet, packet_digest = build_evidence_packet()
    prompt, prompt_digest = build_solver_prompt()
    assert len(packet) == SEALED_EVIDENCE_PACKET_LENGTH
    assert packet_digest == SEALED_EVIDENCE_PACKET_SHA256
    assert len(prompt) == SOLVER_PROMPT_LENGTH
    assert prompt_digest == SOLVER_PROMPT_SHA256
    assert EVIDENCE_PACKET_ARTIFACT_PATH.read_bytes() == packet.encode("utf-8")
    assert FROZEN_PROMPT_ARTIFACT_PATH.read_bytes() == prompt.encode("utf-8")
    _assert_solver_visible_content(packet, state)
    _assert_solver_visible_content(prompt, state)
    assert state["answer_321"] in packet
    assert state["answer_322"] in packet
    assert "Do not self-censor" in packet
    assert "Do not omit a strong candidate" in prompt

    inventory = phase270_inventory(state)
    assert len(inventory["base_values"]) == PHASE270_BASE_COUNT
    assert len(inventory["materials"]) == PHASE270_MATERIAL_COUNT
    duplicate = state["answer_322"].encode("ascii")
    assert classify_phase270_duplicate(duplicate, inventory) == "exact_duplicate_of_phase270"
    duplicate_hash = hashlib.sha256(duplicate).hexdigest().encode("ascii")
    assert duplicate_hash in inventory["materials"]
    assert classify_phase270_duplicate(duplicate + b"X", inventory) == "genuinely_new"

    no_convergence = _eligible_fixture([
        ("unique-a",), ("unique-b",), ("unique-c",), ("unique-d",), ("unique-e",),
    ])
    result = classify_completed_panel(no_convergence)
    assert result["outcome"] == "no_convergence"
    assert result["evaluated_new_count"] == 0

    duplicate_text = state["answer_322"]
    duplicate_only = _eligible_fixture([
        (duplicate_text,), (duplicate_text,), ("unique-c",), ("unique-d",), ("unique-e",),
    ])
    calls = []
    result = classify_completed_panel(duplicate_only, evaluator=_fixture_evaluator({}, calls))
    assert result["outcome"] == "duplicate_only_convergence"
    assert result["duplicate_promoted_count"] == 1
    assert result["evaluated_new_count"] == 0 and calls == []

    novel = "novelnegativefixture"
    mixed = _eligible_fixture([
        (duplicate_text, novel), (duplicate_text, novel),
        ("unique-c",), ("unique-d",), ("unique-e",),
    ])
    calls = []
    result = classify_completed_panel(mixed, evaluator=_fixture_evaluator({}, calls))
    assert result["outcome"] == "novel_convergence_negative"
    assert result["duplicate_promoted_count"] == 1
    assert result["genuinely_new_promoted_count"] == 1
    assert calls == [novel.encode("ascii")]

    structural = "structuralfixture"
    structural_panel = _eligible_fixture([
        (structural,), (structural,), ("unique-c",), ("unique-d",), ("unique-e",),
    ])
    calls = []
    result = classify_completed_panel(
        structural_panel,
        evaluator=_fixture_evaluator({structural.encode(): "structural_hit"}, calls),
    )
    assert result["outcome"] == "structural_hit" and len(calls) == 1

    terminal = "terminalfixture"
    terminal_panel = _eligible_fixture([
        (terminal,), (terminal,), ("unique-c",), ("unique-d",), ("unique-e",),
    ])
    calls = []
    result = classify_completed_panel(
        terminal_panel,
        evaluator=_fixture_evaluator({terminal.encode(): "terminal_hit"}, calls),
    )
    assert result["outcome"] == "terminal_hit" and len(calls) == 1

    # The adapter reaches Phase 416's real redacted evaluator.
    real = evaluate_candidate(b"phase418-real-evaluator-fixture")
    _assert_evaluation_redacted(real)
    assert real["material_sha256"] == hashlib.sha256(
        b"phase418-real-evaluator-fixture"
    ).hexdigest()
    assert real["outcome"] == "negative"

    invalid = close_phase({}, INVOCATION_CAP + 1)
    assert invalid["outcome"] == "protocol_invalid"
    assert invocation_task_name(1) == "phase418_invocation_1"
    assert invocation_task_name(8) == "phase418_invocation_8"
    assert INVOCATION_CONFIGURATION == {
        "agent_class": "general-purpose",
        "fork_turns": "none",
        "model_override": None,
        "reasoning_effort_override": None,
        "service_configuration": "default",
    }

    # Execution-facing builders fail closed if a pin drifts.
    original_length = SOLVER_PROMPT_LENGTH
    try:
        SOLVER_PROMPT_LENGTH = -1
        try:
            build_solver_prompt()
            raise AssertionError("prompt builder accepted a drifted length pin")
        except AssertionError as exc:
            assert "length drifted" in str(exc)
    finally:
        SOLVER_PROMPT_LENGTH = original_length
    build_solver_prompt()

    return {
        "packet_length": len(packet),
        "packet_sha256": packet_digest,
        "prompt_length": len(prompt),
        "prompt_sha256": prompt_digest,
        "phase270_base_candidates": len(inventory["base_values"]),
        "phase270_materials": len(inventory["materials"]),
        "solver_invocations": 0,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--show-digests", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.write_artifacts:
        print(json.dumps(write_artifacts(), indent=2, sort_keys=True))
    elif args.show_digests:
        packet, packet_digest = build_sealed_evidence_packet()
        prompt, prompt_digest = _render_solver_prompt()
        print(json.dumps({
            "packet_length": len(packet),
            "packet_sha256": packet_digest,
            "prompt_length": len(prompt),
            "prompt_sha256": prompt_digest,
        }, indent=2, sort_keys=True))
    else:
        print(json.dumps(self_test(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
