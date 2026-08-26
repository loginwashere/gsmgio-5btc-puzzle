#!/usr/bin/env python3
"""Phase 417: blinded-panel sensitivity calibration on solved Phase 3.2.

Implements the protocol frozen in ``doc/Brainstorms/2026-08-26 - Phase 417
Blinded Panel Sensitivity Calibration Pre-Registration.md``.  This module
builds a solution-complete but target-sealed evidence packet from the
authenticated Phase 3 plaintext, reuses Phase 416's strict submission and
two-vote mechanics, and evaluates promoted candidates only under the known
Phase 410 profile.  It does not invoke solvers.
"""

import base64
import hashlib
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase410_solved_vector_toolchain_provenance_audit as phase410  # noqa: E402
import phase416_p32trailing_sealed_target_reconstruction_audit as phase416  # noqa: E402
from cb_common import _load_blob  # noqa: E402
from data import VERIFIED_PRIOR_COMMAND_HASHES  # noqa: E402
from phase3_sevenpart_permutation_audit import PHASE3_PARTS  # noqa: E402


# Phase 416 mechanics reused unchanged wherever compatible.
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

# Observable invocation fields, frozen before execution.  The external
# orchestrator must assign ``task_name``/ledger identity before spawning, send
# only ``build_solver_prompt()`` output, and leave model/reasoning overrides
# omitted so the service's default configuration matches Phase 416.
INVOCATION_CONFIGURATION = {
    "agent_class": "general-purpose",
    "fork_turns": "none",
    "model_override": None,
    "reasoning_effort_override": None,
    "service_configuration": "default",
}


# Frozen solved-boundary ground truth.  These values never enter the packet or
# prompt; the evaluator holds them for post-panel diagnostics and exact scoring.
GROUND_TRUTH = b"jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple"
GROUND_TRUTH_SHA256 = "250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c"
GROUND_TRUTH_HEX = GROUND_TRUTH.hex()

PHASE3_PLAINTEXT_LENGTH = 4090
PHASE3_PLAINTEXT_SHA256 = "c4ad94559a44a927c1032cc0e024515f9510a0806a2d14458dbf4a360af9865f"
DISCLOSED_PREFIX_START = 0
DISCLOSED_PREFIX_END = 726
DISCLOSED_PREFIX_SHA256 = "71da3ceeccc7af315dcabfc071a3c77f9211a73d88178f5275cde5cf8be06ea3"
WITHHELD_B64_START = 726
WITHHELD_B64_END = 4090
WITHHELD_B64_SHA256 = "265780b6bc80c9a05b9f9caf6a577d7fb91497d7b8c5227338c6f0f1b5ae1266"
CONTAINER_LENGTH = 2448
CONTAINER_SHA256 = "9d172dc017034564b40eb381fa61e31421f509a08430864c77ccf86cfc8fe784"
SALT_LENGTH = 8
SALT_SHA256 = "f350dabeb2157fa917b972e7db5b1e23a6b1c7a55fc5725c716fc357f36aee47"
CIPHERTEXT_LENGTH = 2432
CIPHERTEXT_SHA256 = "48a77592e2f3ed1d508010157bb9af169ec4898cc8f05b9ac7cdd5aeebdb278a"
TARGET_PLAINTEXT_LENGTH = 2422
TARGET_PLAINTEXT_SHA256 = "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"

# Filled only after rendering and review; execution-facing builders reject
# drift from these pins and from the committed artifacts.
SEALED_EVIDENCE_PACKET_SHA256 = "20dad195418cbfb08898dd793d0fba7f44565787de840e4d571695b56d5b58e7"
SEALED_EVIDENCE_PACKET_LENGTH = 5022
SOLVER_PROMPT_SHA256 = "e99a930843f5fbf841d31a07c7273f7232fec221d27ae3d9381b0c008683ec6b"
SOLVER_PROMPT_LENGTH = 6975
EVIDENCE_PACKET_ARTIFACT_PATH = SCRIPT_DIR / "phase417_sealed_evidence_packet.txt"
FROZEN_PROMPT_ARTIFACT_PATH = SCRIPT_DIR / "phase417_frozen_solver_prompt.txt"

PHASE3_PART_LABELS = (
    "part 1 (Phase 2's solved password)",
    "part 2",
    "part 3",
    "part 4",
    "part 5",
    "part 6 (hex token)",
    "part 7 (post-move chess FEN)",
)


def recover_boundary():
    """Recover and verify the authenticated Phase 3 -> Phase 3.2 boundary."""
    artifact = phase410.WAYBACK_ARTIFACT_PATH.read_bytes()
    if hashlib.sha256(artifact).hexdigest() != phase410.WAYBACK_ARTIFACT_SHA256:
        raise AssertionError("authenticated Wayback artifact commitment drifted")
    textareas = phase410.extract_wayback_textareas(phase410.WAYBACK_ARTIFACT_PATH)
    if len(textareas) != 2:
        raise AssertionError("expected exactly two ciphertext textareas")

    phase3_salt, phase3_ciphertext = _load_blob(textareas[1].decode("ascii"))
    phase3_password = hashlib.sha256(phase410.PHASE3_PREIMAGE.encode("utf-8")).hexdigest()
    if phase3_password != VERIFIED_PRIOR_COMMAND_HASHES["phase3_parts"]:
        raise AssertionError("Phase 3 preimage/password vector drifted")
    _, _, plaintext = phase410.decrypt_container(
        phase3_salt, phase3_ciphertext, phase3_password.encode("ascii"), "sha256"
    )
    del phase3_password
    if plaintext is None:
        raise AssertionError("authenticated Phase 3 vector no longer decrypts")
    if len(plaintext) != PHASE3_PLAINTEXT_LENGTH:
        raise AssertionError("Phase 3 plaintext length drifted")
    if hashlib.sha256(plaintext).hexdigest() != PHASE3_PLAINTEXT_SHA256:
        raise AssertionError("Phase 3 plaintext commitment drifted")

    # Locate the unique trailing OpenSSL envelope structurally.  The numeric
    # offsets are then asserted rather than used as the locating mechanism.
    marker = b"U2FsdGVkX1"
    if plaintext.count(marker) != 1:
        raise AssertionError("Phase 3 plaintext does not contain one unique OpenSSL Base64 marker")
    located_start = plaintext.index(marker)
    if located_start != WITHHELD_B64_START or len(plaintext) != WITHHELD_B64_END:
        raise AssertionError("structurally located Phase 3.2 envelope offsets drifted")
    prefix = plaintext[:located_start]
    withheld_b64 = plaintext[located_start:]
    try:
        container = base64.b64decode(b"".join(withheld_b64.split()), validate=True)
    except Exception as exc:
        raise AssertionError("trailing span is not strict Base64") from exc
    if not container.startswith(b"Salted__"):
        raise AssertionError("trailing Base64 does not decode to an OpenSSL Salted__ container")
    salt = container[8:16]
    ciphertext = container[16:]

    checks = (
        (len(prefix), DISCLOSED_PREFIX_END, "disclosed prefix length"),
        (hashlib.sha256(prefix).hexdigest(), DISCLOSED_PREFIX_SHA256, "disclosed prefix"),
        (len(withheld_b64), WITHHELD_B64_END - WITHHELD_B64_START, "withheld Base64 length"),
        (hashlib.sha256(withheld_b64).hexdigest(), WITHHELD_B64_SHA256, "withheld Base64"),
        (len(container), CONTAINER_LENGTH, "container length"),
        (hashlib.sha256(container).hexdigest(), CONTAINER_SHA256, "container"),
        (len(salt), SALT_LENGTH, "salt length"),
        (hashlib.sha256(salt).hexdigest(), SALT_SHA256, "salt"),
        (len(ciphertext), CIPHERTEXT_LENGTH, "ciphertext length"),
        (hashlib.sha256(ciphertext).hexdigest(), CIPHERTEXT_SHA256, "ciphertext"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise AssertionError(f"{label} commitment drifted: {actual!r} != {expected!r}")

    password = hashlib.sha256(GROUND_TRUTH).hexdigest().encode("ascii")
    if password.decode("ascii") != GROUND_TRUTH_SHA256:
        raise AssertionError("ground-truth digest drifted")
    _, _, target_plaintext = phase410.decrypt_container(salt, ciphertext, password, "sha256")
    del password
    if target_plaintext is None:
        raise AssertionError("ground truth no longer decrypts the target")
    if len(target_plaintext) != TARGET_PLAINTEXT_LENGTH:
        raise AssertionError("target plaintext length drifted")
    if hashlib.sha256(target_plaintext).hexdigest() != TARGET_PLAINTEXT_SHA256:
        raise AssertionError("target plaintext commitment drifted")

    return {
        "phase3_plaintext": plaintext,
        "prefix": prefix,
        "withheld_b64": withheld_b64,
        "container": container,
        "salt": salt,
        "ciphertext": ciphertext,
        "target_plaintext": target_plaintext,
    }


def build_sealed_evidence_packet():
    boundary = recover_boundary()
    prefix_text = boundary["prefix"].decode("ascii")
    phase2_preimage = "causality"
    phase2_hash = hashlib.sha256(phase2_preimage.encode("utf-8")).hexdigest()
    phase3_preimage = "".join(PHASE3_PARTS)
    phase3_hash = hashlib.sha256(phase3_preimage.encode("utf-8")).hexdigest()
    if phase2_hash != VERIFIED_PRIOR_COMMAND_HASHES["phase2_causality"]:
        raise AssertionError("Phase 2 worked example drifted")
    if phase3_hash != VERIFIED_PRIOR_COMMAND_HASHES["phase3_parts"]:
        raise AssertionError("Phase 3 worked example drifted")

    parts = [
        "=" * 78,
        "ITEM 1 -- Exact authenticated Phase 3 plaintext prefix preceding the",
        "held-out Phase 3.2 OpenSSL envelope (bytes [0:726], 726 bytes).",
        "=" * 78,
        "",
        prefix_text,
        "",
        "=" * 78,
        "ITEM 2 -- Already-solved component supplement.",
        "=" * 78,
        "",
        "These values are community-derived interpretations authenticated by the",
        "known successful Phase 3.2 decrypt; they are not creator-authored solution prose:",
        "  clue 1 answer: Jacque Fresco",
        "  clue 2 answer before its locally instructed prefix: just one second",
        "  clue 3 answer: Heisenberg's uncertainty principle",
        "",
        "For this solved boundary only, the empirically authenticated assembly is:",
        "force the component values to lowercase; remove spaces and the possessive",
        "apostrophe; apply the prefix instruction in the disclosed clue text by",
        "prepending the literal letters giveit directly to clue 2's normalized answer;",
        "then concatenate the three resulting clue components in clue order with no",
        "separator bytes. This is not a universal definition of connected enf.",
        "",
        "=" * 78,
        "ITEM 3 -- Two prior solved boundary examples (not the held-out target).",
        "=" * 78,
        "",
        "Phase 2:",
        f"  exact preimage: {phase2_preimage}",
        f"  SHA-256 hex digest used as the literal AES password: {phase2_hash}",
        "",
        "Phase 3 (seven parts, fixed order, no separators):",
    ]
    for label, value in zip(PHASE3_PART_LABELS, PHASE3_PARTS):
        parts.append(f"  {label}: {value}")
    parts.extend([
        f"  exact full preimage: {phase3_preimage}",
        f"  SHA-256 hex digest used as the literal AES password: {phase3_hash}",
        "",
        "=" * 78,
        "ITEM 4 -- Solved-stage cryptographic recipe.",
        "=" * 78,
        "",
        "  1. Assemble preimage P exactly according to the local clue instructions.",
        "  2. Compute lowercase ASCII SHA256(P).hexdigest(); that 64-character",
        "     digest string, not P and not the raw 32-byte digest, is the password.",
        "  3. Use legacy single-round EVP_BytesToKey with SHA-256 and the target's",
        "     own 8-byte salt to derive the AES-256 key and CBC IV.",
        "  4. Decrypt with AES-256-CBC and remove strict PKCS#7 padding.",
        "",
        "=" * 78,
        "ITEM 5 -- Structurally located sealed target.",
        "=" * 78,
        "",
        "The unique trailing OpenSSL envelope begins at byte 726 of the recovered",
        "4,090-byte Phase 3 plaintext. Bytes [726:4090] are withheld. They are the",
        "literal Base64 span, including original line breaks, of a standard OpenSSL",
        "Salted__ container. The evaluator, not the solver, holds the target bytes.",
        f"  disclosed prefix [0:726]: 726 bytes, SHA-256 {DISCLOSED_PREFIX_SHA256}",
        f"  withheld Base64 [726:4090]: 3,364 bytes, SHA-256 {WITHHELD_B64_SHA256}",
        f"  decoded Salted__ container: 2,448 bytes, SHA-256 {CONTAINER_SHA256}",
        f"  container salt: 8 bytes, SHA-256 {SALT_SHA256}",
        f"  raw ciphertext: 2,432 bytes, SHA-256 {CIPHERTEXT_SHA256}",
        f"  recovered target plaintext: 2,422 bytes, SHA-256 {TARGET_PLAINTEXT_SHA256}",
        "These commitments fix the target identity but do not enable candidate testing.",
        "",
    ])
    packet_text = "\n".join(parts)
    _assert_secrets_absent(packet_text, boundary)
    return packet_text, hashlib.sha256(packet_text.encode("utf-8")).hexdigest()


_SOLVER_PROMPT_TEMPLATE = """You are completing a blinded positive-control reconstruction task on a
known solved cryptographic-puzzle boundary. The target ciphertext, recovered
plaintext, exact assembled preimage, and password digest are deliberately
withheld. You are given the exact preceding clue text, the three already-solved
component values, their local normalization/assembly instructions, two prior
worked boundary examples, the exact cryptographic recipe, and commitments that
fix the sealed target's identity.

{packet}

Your task is to propose from 1 to 10 candidate preimages P for this held-out
boundary. Follow the supplied component and local assembly instructions. Do not
submit SHA256(P), a hex encoding of P, or an AES password; submit the exact text P
whose UTF-8 bytes should be hashed. Your derivation must identify which disclosed
component and local instruction licenses every piece of each candidate.

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

Use no tool for any purpose while answering: no files or repository access, shell,
code, calculator, hashing, encryption/decryption, candidate testing, environment
variables, web search, or external lookup. Use only the material in this prompt.
If you used any tool for any reason, set tool_used to true and explain why; that
submission will be excluded. Do not leave placeholder, TODO, or FIXME text in any
field. Do not add fields, repair the schema, repeat a candidate, normalize a
candidate, or provide prose outside the JSON object."""


def _assert_secrets_absent(text, boundary):
    encoded = text.encode("utf-8")
    forbidden = {
        "ground-truth preimage": GROUND_TRUTH,
        "ground-truth UTF-8 hex": GROUND_TRUTH_HEX.encode("ascii"),
        "ground-truth password digest": GROUND_TRUTH_SHA256.encode("ascii"),
        "withheld literal Base64 span": boundary["withheld_b64"],
        "recovered target plaintext": boundary["target_plaintext"],
    }
    for label, value in forbidden.items():
        if value in encoded:
            raise AssertionError(f"{label} leaked into solver-visible text")


def _render_solver_prompt():
    packet_text, _ = build_sealed_evidence_packet()
    prompt = _SOLVER_PROMPT_TEMPLATE.format(packet=packet_text)
    _assert_secrets_absent(prompt, recover_boundary())
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
        text, digest, SEALED_EVIDENCE_PACKET_LENGTH,
        SEALED_EVIDENCE_PACKET_SHA256, EVIDENCE_PACKET_ARTIFACT_PATH,
        "Phase 417 evidence packet",
    )


def build_solver_prompt():
    packet_text, packet_digest = build_evidence_packet()
    prompt, digest = _render_solver_prompt()
    if packet_text not in prompt or packet_digest != SEALED_EVIDENCE_PACKET_SHA256:
        raise AssertionError("checked packet is not embedded byte-exactly in prompt")
    return _checked_artifact(
        prompt, digest, SOLVER_PROMPT_LENGTH, SOLVER_PROMPT_SHA256,
        FROZEN_PROMPT_ARTIFACT_PATH, "Phase 417 solver prompt",
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


def evaluate_exact_candidate(material):
    """Evaluate one candidate under only the known Phase 410 profile.

    Returns redacted classification only; plaintext and password bytes do not
    escape this function.
    """
    if not isinstance(material, bytes):
        raise TypeError("candidate material must be bytes")
    boundary = recover_boundary()
    password = hashlib.sha256(material).hexdigest().encode("ascii")
    _, _, plaintext = phase410.decrypt_container(
        boundary["salt"], boundary["ciphertext"], password, "sha256"
    )
    del password
    if plaintext is None:
        return {
            "padding_valid": False,
            "plaintext_length": None,
            "plaintext_sha256": None,
            "correct": False,
        }
    length = len(plaintext)
    digest = hashlib.sha256(plaintext).hexdigest()
    correct = length == TARGET_PLAINTEXT_LENGTH and digest == TARGET_PLAINTEXT_SHA256
    del plaintext
    return {
        "padding_valid": True,
        "plaintext_length": length,
        "plaintext_sha256": digest,
        "correct": correct,
    }


def ground_truth_diagnostic(eligible):
    ranks = []
    for submission in eligible:
        for candidate in submission["accepted"]:
            if candidate["material"] == GROUND_TRUTH:
                ranks.append(candidate["rank"])
    return {
        "ground_truth_vote_count": len(ranks),
        "ground_truth_best_rank": min(ranks) if ranks else None,
    }


def classify_completed_panel(eligible):
    if len(eligible) != PANEL_TARGET:
        raise ValueError("outcome classification requires exactly five eligible submissions")
    promoted = promote_candidates(eligible)
    evaluations = {}
    for hex_value, promotion in sorted(promoted.items(), key=_promotion_sort_key):
        evaluations[hex_value] = {
            **promotion,
            **evaluate_exact_candidate(bytes.fromhex(hex_value)),
        }
    diagnostic = ground_truth_diagnostic(eligible)
    ground_result = evaluations.get(GROUND_TRUTH_HEX)
    wrong_promoted = [h for h in evaluations if h != GROUND_TRUTH_HEX]
    if ground_result is not None and not ground_result["correct"]:
        branch = "protocol_invalid"
        reason = "ground truth promoted but exact evaluator failed"
    elif ground_result is not None:
        branch = "calibrated_with_spurious_convergence" if wrong_promoted else "calibrated_clean"
        reason = None
    elif evaluations:
        branch = "wrong_convergence"
        reason = None
    else:
        branch = "no_convergence"
        reason = None
    return {
        "outcome": branch,
        **diagnostic,
        "promoted_count": len(evaluations),
        "wrong_promoted_count": len(wrong_promoted),
        "evaluations": evaluations,
        "protocol_invalid_reason": reason,
    }


def close_phase(invocation_records, invocations_used):
    try:
        panel = evaluate_panel(invocation_records, invocations_used)
    except ValueError as exc:
        return {"outcome": "protocol_invalid", "protocol_invalid_reason": str(exc)}
    if panel["status"] == "protocol_invalid":
        return {
            "outcome": "protocol_invalid",
            "protocol_invalid_reason": "five eligible submissions not obtained within eight invocations",
            "eligible_count": len(panel["eligible"]),
        }
    if panel["status"] == "need_more":
        return {"outcome": "need_more", "eligible_count": len(panel["eligible"])}
    return classify_completed_panel(panel["eligible"])


def invocation_task_name(invocation_number):
    """Return the pre-spawn identity for one of the at-most-eight attempts."""
    if not isinstance(invocation_number, int) or isinstance(invocation_number, bool):
        raise TypeError("invocation number must be a plain integer")
    if not 1 <= invocation_number <= INVOCATION_CAP:
        raise ValueError("invocation number is outside the frozen 1..8 cap")
    return f"phase417_invocation_{invocation_number}"


def _candidate(display, rank=1):
    return {
        "display": display,
        "derivation": "assembled from the disclosed components and local instructions",
        "rank": rank,
    }


def _submission(*displays):
    return {
        "tool_used": False,
        "reasoning_text": "packet-local assembly reasoning",
        "candidates": [_candidate(display, rank + 1) for rank, display in enumerate(displays)],
    }


def _eligible_fixture(displays):
    records = {f"inv-{i + 1}": _submission(*row) for i, row in enumerate(displays)}
    eligible = eligible_submissions(records)
    assert len(eligible) == PANEL_TARGET
    return eligible


def self_test():
    boundary = recover_boundary()
    assert len(GROUND_TRUTH) == 62
    assert hashlib.sha256(GROUND_TRUTH).hexdigest() == GROUND_TRUTH_SHA256

    packet, packet_digest = build_evidence_packet()
    prompt, prompt_digest = build_solver_prompt()
    assert packet_digest == SEALED_EVIDENCE_PACKET_SHA256
    assert prompt_digest == SOLVER_PROMPT_SHA256
    assert packet.encode("utf-8") == EVIDENCE_PACKET_ARTIFACT_PATH.read_bytes()
    assert prompt.encode("utf-8") == FROZEN_PROMPT_ARTIFACT_PATH.read_bytes()
    _assert_secrets_absent(packet, boundary)
    _assert_secrets_absent(prompt, boundary)
    prefix = boundary["prefix"]
    assert prefix
    assert prefix.decode("ascii") in packet
    assert "Phase 3.2 (four parts" not in packet

    # Exact positive and the preregistered valid-padding wrong-password guard.
    positive = evaluate_exact_candidate(GROUND_TRUTH)
    assert positive == {
        "padding_valid": True,
        "plaintext_length": TARGET_PLAINTEXT_LENGTH,
        "plaintext_sha256": TARGET_PLAINTEXT_SHA256,
        "correct": True,
    }
    wrong_padding = evaluate_exact_candidate(b"phase417-wrong-padding-fixture-119")
    assert wrong_padding["padding_valid"] is True
    assert wrong_padding["plaintext_length"] == 2431
    assert wrong_padding["plaintext_sha256"] == "6d8273c346d0aa4fef66c7da674b3688aa64908e9ce34e7a3b4616363778b03e"
    assert wrong_padding["correct"] is False

    gt = GROUND_TRUTH.decode("ascii")
    clean = _eligible_fixture([(gt,), (gt,), ("unique-a",), ("unique-b",), ("unique-c",)])
    assert classify_completed_panel(clean)["outcome"] == "calibrated_clean"
    spurious = _eligible_fixture([(gt,), (gt,), ("wrong-shared",), ("wrong-shared",), ("unique",)])
    assert classify_completed_panel(spurious)["outcome"] == "calibrated_with_spurious_convergence"
    wrong = _eligible_fixture([(gt,), ("wrong-shared",), ("wrong-shared",), ("unique-a",), ("unique-b",)])
    wrong_result = classify_completed_panel(wrong)
    assert wrong_result["outcome"] == "wrong_convergence"
    assert wrong_result["ground_truth_vote_count"] == 1
    singleton = _eligible_fixture([(gt,), ("unique-a",), ("unique-b",), ("unique-c",), ("unique-d",)])
    singleton_result = classify_completed_panel(singleton)
    assert singleton_result["outcome"] == "no_convergence"
    assert singleton_result["ground_truth_vote_count"] == 1
    zero = _eligible_fixture([("unique-a",), ("unique-b",), ("unique-c",), ("unique-d",), ("unique-e",)])
    zero_result = classify_completed_panel(zero)
    assert zero_result["outcome"] == "no_convergence"
    assert zero_result["ground_truth_vote_count"] == 0
    invalid = close_phase({}, INVOCATION_CAP + 1)
    assert invalid["outcome"] == "protocol_invalid"

    assert INVOCATION_CONFIGURATION == {
        "agent_class": "general-purpose",
        "fork_turns": "none",
        "model_override": None,
        "reasoning_effort_override": None,
        "service_configuration": "default",
    }
    assert invocation_task_name(1) == "phase417_invocation_1"
    assert invocation_task_name(8) == "phase417_invocation_8"

    # Prompt and pin drift fail closed.
    global SOLVER_PROMPT_LENGTH
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
        "phase3_plaintext_length": len(boundary["phase3_plaintext"]),
        "target_plaintext_length": TARGET_PLAINTEXT_LENGTH,
        "solver_invocations": 0,
    }


def main():
    import argparse
    import json

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
            "packet_length": len(packet), "packet_sha256": packet_digest,
            "prompt_length": len(prompt), "prompt_sha256": prompt_digest,
        }, indent=2, sort_keys=True))
    else:
        print(json.dumps(self_test(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
