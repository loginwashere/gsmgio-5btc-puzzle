#!/usr/bin/env python3
"""Phase 420: one-file-bootstrap delivery correction for Phase 418.

This module does not invoke solvers. It preserves Phase 418's evidence,
promotion, duplicate-classification, evaluator, and outcome logic while
allowing a fresh solver exactly one self-disclosed bootstrap read of this
phase's committed prompt artifact.
"""

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase416_p32trailing_sealed_target_reconstruction_audit as phase416  # noqa: E402
import phase418_p32trailing_solution_complete_blinded_reconstruction_audit as phase418  # noqa: E402


MAX_SOLVER_CANDIDATES = phase418.MAX_SOLVER_CANDIDATES
INVOCATION_CAP = phase418.INVOCATION_CAP
PANEL_TARGET = phase418.PANEL_TARGET
parse_submission = phase416.parse_submission
promote_candidates = phase418.promote_candidates
classify_completed_panel = phase418.classify_completed_panel

PROMPT_PATH = SCRIPT_DIR / "phase420_frozen_solver_prompt.txt"
LAUNCHER_PATH = SCRIPT_DIR / "phase420_frozen_launcher.txt"
PERMITTED_COMMAND = (
    "sed -n '1,260p' "
    "/home/loginwashere/projects/gsmgio-5btc-puzzle/tools/gsmg/"
    "phase420_frozen_solver_prompt.txt"
)

LAUNCHER_TEXT = f"""Read the complete solver prompt using exactly one shell tool call and no other
tool: {PERMITTED_COMMAND}

The read above is the only permitted bootstrap action. Follow the file exactly.
Return only the JSON object it requests. Do not inspect any other file, run any
other command, use any other tool, or retrieve external information.
"""

# Filled from the mechanically rendered artifacts before this implementation
# is committed. Builders fail closed against all four pins.
PROMPT_LENGTH = 14717
PROMPT_SHA256 = "f7d42eab83697f5d88495e27c7e25dd68c02ab7afe94afe17ee7d99642a96c3f"
PROMPT_LINE_COUNT = 219
LAUNCHER_LENGTH = 423
LAUNCHER_SHA256 = "09c38bdf8c30ff0713854a24f88b007b8d71d611470fd8e277d9180eb8df965c"

INVOCATION_CONFIGURATION = {
    "agent_class": "general-purpose",
    "fork_turns": "none",
    "model_override": None,
    "reasoning_effort_override": None,
    "service_configuration": "default",
    "delivery": "one_file_bootstrap",
    "permitted_command": PERMITTED_COMMAND,
}

OLD_SCHEMA = '''{
  "tool_used": <true or false, required and explicit>,
  "reasoning_text": "<your final overall reasoning>",
  "candidates": [
    {
      "display": "<exact preimage P, exact characters and case>",
      "derivation": "<packet-local derivation licensing every piece of P>",
      "rank": <integer; ranks across all candidates must be exactly 1..n>
    }
  ]
}'''

NEW_SCHEMA = '''{
  "bootstrap_read_used": true,
  "other_tool_used": false,
  "reasoning_text": "<your final overall reasoning>",
  "candidates": [
    {
      "display": "<exact preimage P, exact characters and case>",
      "derivation": "<packet-local derivation licensing every piece of P>",
      "rank": <integer; ranks across all candidates must be exactly 1..n>
    }
  ]
}'''

OLD_TOOL_RULE = """Use no tool for any purpose while answering: no files or repository access,
shell, code, calculator, hashing, encryption/decryption, candidate testing,
environment variables, web search, or external lookup. Use only this prompt.
If you used any tool for any reason, set tool_used to true and explain why; the
submission will be excluded. Do not leave placeholder, TODO, or FIXME text in
any field. Do not add fields, repair the schema, repeat or normalize a candidate,
or provide prose outside the JSON object."""

NEW_TOOL_RULE = f"""The single bootstrap read that delivered this file is permitted and must be
reported as bootstrap_read_used: true. Use no other tool for any purpose: no
second file or repository read, shell command, code, calculator, hashing,
encryption/decryption, candidate testing, environment inspection, web search,
or external lookup. If you used anything beyond the exact bootstrap command
{PERMITTED_COMMAND!r}, set other_tool_used to true and explain why; the
submission will be excluded. Otherwise set other_tool_used to false. Do not
leave placeholder, TODO, or FIXME text in any field. Do not add fields, repair
the schema, repeat or normalize a candidate, or provide prose outside the JSON
object."""


def _render_prompt():
    """Mechanically change only Phase 418's schema and tool rule."""
    source = phase418.FROZEN_PROMPT_ARTIFACT_PATH.read_text(encoding="utf-8")
    if source.count(OLD_SCHEMA) != 1:
        raise AssertionError("Phase 418 schema replacement boundary drifted")
    if source.count(OLD_TOOL_RULE) != 1:
        raise AssertionError("Phase 418 tool-rule replacement boundary drifted")
    prompt = source.replace(OLD_SCHEMA, NEW_SCHEMA).replace(OLD_TOOL_RULE, NEW_TOOL_RULE)
    return prompt, hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def write_artifacts():
    prompt, prompt_digest = _render_prompt()
    PROMPT_PATH.write_bytes(prompt.encode("utf-8"))
    LAUNCHER_PATH.write_bytes(LAUNCHER_TEXT.encode("utf-8"))
    return {
        "prompt_length": len(prompt),
        "prompt_sha256": prompt_digest,
        "prompt_line_count": len(prompt.splitlines()),
        "launcher_length": len(LAUNCHER_TEXT),
        "launcher_sha256": hashlib.sha256(LAUNCHER_TEXT.encode("utf-8")).hexdigest(),
    }


def _checked_artifact(text, path, length, digest, label):
    actual_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if len(text) != length:
        raise AssertionError(f"{label} length drifted: {len(text)} != {length}")
    if actual_digest != digest:
        raise AssertionError(f"{label} SHA-256 drifted: {actual_digest} != {digest}")
    if path.read_bytes() != text.encode("utf-8"):
        raise AssertionError(f"{label} differs from committed artifact")
    return text, actual_digest


def build_prompt():
    prompt, _digest = _render_prompt()
    if len(prompt.splitlines()) != PROMPT_LINE_COUNT:
        raise AssertionError("prompt line count drifted")
    if PROMPT_LINE_COUNT > 260:
        raise AssertionError("prompt no longer fits the fixed bootstrap read")
    # The evidence itself is inherited byte-exactly, not reconstructed here.
    packet, packet_digest = phase418.build_evidence_packet()
    if packet_digest != phase418.SEALED_EVIDENCE_PACKET_SHA256 or packet not in prompt:
        raise AssertionError("Phase 418 evidence packet is not embedded byte-exactly")
    return _checked_artifact(prompt, PROMPT_PATH, PROMPT_LENGTH, PROMPT_SHA256, "prompt")


def build_launcher():
    if PERMITTED_COMMAND not in LAUNCHER_TEXT:
        raise AssertionError("permitted command absent from launcher")
    return _checked_artifact(
        LAUNCHER_TEXT, LAUNCHER_PATH, LAUNCHER_LENGTH, LAUNCHER_SHA256, "launcher"
    )


REQUIRED_SUBMISSION_KEYS = frozenset({
    "bootstrap_read_used", "other_tool_used", "reasoning_text", "candidates",
})
REQUIRED_RECORD_KEYS = frozenset({
    "submission", "tool_telemetry_available", "recorded_tool_calls",
})
EXPECTED_RECORDED_CALL = {"tool": "exec_command", "command": PERMITTED_COMMAND}


def validate_submission_schema(submission):
    """Adapt Phase 420's disclosure fields to Phase 416's frozen validator."""
    if not isinstance(submission, dict) or set(submission) != REQUIRED_SUBMISSION_KEYS:
        return False, "unexpected or missing top-level keys"
    if not isinstance(submission["bootstrap_read_used"], bool):
        return False, "bootstrap_read_used must be an explicit boolean"
    if not isinstance(submission["other_tool_used"], bool):
        return False, "other_tool_used must be an explicit boolean"
    legacy = {
        "tool_used": submission["other_tool_used"],
        "reasoning_text": submission["reasoning_text"],
        "candidates": submission["candidates"],
    }
    return phase416.validate_submission_schema(legacy)


def validate_invocation_record(record):
    if not isinstance(record, dict) or set(record) != REQUIRED_RECORD_KEYS:
        return False, "unexpected or missing invocation-record keys"
    submission = record["submission"]
    ok, parsed_or_reason = validate_submission_schema(submission)
    if not ok:
        return False, parsed_or_reason
    if not submission["bootstrap_read_used"]:
        return False, "bootstrap read was not disclosed"
    if submission["other_tool_used"]:
        return False, "other tool use was disclosed"
    telemetry = record["tool_telemetry_available"]
    calls = record["recorded_tool_calls"]
    if not isinstance(telemetry, bool):
        return False, "tool_telemetry_available must be an explicit boolean"
    if not isinstance(calls, list):
        return False, "recorded_tool_calls must be a list"
    if telemetry:
        if calls != [EXPECTED_RECORDED_CALL]:
            return False, "available telemetry does not show exactly the permitted bootstrap call"
    elif calls:
        return False, "unavailable telemetry must not claim recorded calls"
    if phase416.blinding_violations(phase416.submission_full_text(submission)):
        return False, "submission contains blinded-target residue"
    return True, parsed_or_reason


def eligible_submissions(invocation_records):
    eligible = []
    for invocation_id, record in invocation_records.items():
        ok, parsed_or_reason = validate_invocation_record(record)
        if not ok:
            continue
        submission = record["submission"]
        eligible.append({
            "invocation_id": invocation_id,
            **submission,
            "tool_telemetry_available": record["tool_telemetry_available"],
            "accepted": parsed_or_reason,
        })
    return eligible


def evaluate_panel(invocation_records, invocations_used):
    if invocations_used < len(invocation_records):
        raise ValueError("invocations_used cannot be smaller than collected records")
    if invocations_used > INVOCATION_CAP:
        raise ValueError("invocations_used exceeds the frozen cap")
    eligible = eligible_submissions(invocation_records)
    if len(eligible) >= PANEL_TARGET:
        return {"status": "panel_ready", "eligible": eligible[:PANEL_TARGET]}
    if invocations_used >= INVOCATION_CAP:
        return {"status": "protocol_invalid", "eligible": eligible}
    return {"status": "need_more", "eligible": eligible}


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
        return phase418.classify_completed_panel(panel["eligible"], evaluator=evaluator)
    except (AssertionError, ValueError, TypeError) as exc:
        return {"outcome": "protocol_invalid", "protocol_invalid_reason": str(exc)}


def invocation_task_name(invocation_number):
    if not isinstance(invocation_number, int) or isinstance(invocation_number, bool):
        raise TypeError("invocation number must be a plain integer")
    if not 1 <= invocation_number <= INVOCATION_CAP:
        raise ValueError("invocation number is outside the frozen 1..8 cap")
    return f"phase420_invocation_{invocation_number}"


def _submission(display="fixture"):
    return {
        "bootstrap_read_used": True,
        "other_tool_used": False,
        "reasoning_text": "packet-local reconstruction reasoning",
        "candidates": [{
            "display": display,
            "derivation": "derived only from disclosed solved components",
            "rank": 1,
        }],
    }


def _record(display="fixture", telemetry=True):
    return {
        "submission": _submission(display),
        "tool_telemetry_available": telemetry,
        "recorded_tool_calls": [EXPECTED_RECORDED_CALL] if telemetry else [],
    }


def self_test():
    prompt, prompt_digest = build_prompt()
    launcher, launcher_digest = build_launcher()
    packet, packet_digest = phase418.build_evidence_packet()
    assert packet_digest == phase418.SEALED_EVIDENCE_PACKET_SHA256
    assert packet in prompt
    assert len(prompt.splitlines()) == PROMPT_LINE_COUNT <= 260
    assert launcher == LAUNCHER_TEXT and PERMITTED_COMMAND in launcher

    good = _record()
    ok, parsed = validate_invocation_record(good)
    assert ok and len(parsed) == 1

    missing = _record()
    missing["submission"]["bootstrap_read_used"] = False
    assert validate_invocation_record(missing)[0] is False
    other = _record()
    other["submission"]["other_tool_used"] = True
    assert validate_invocation_record(other)[0] is False
    extra = _record()
    extra["recorded_tool_calls"].append({"tool": "exec_command", "command": "pwd"})
    assert validate_invocation_record(extra)[0] is False
    wrong = _record()
    wrong["recorded_tool_calls"] = [{"tool": "exec_command", "command": "cat prompt"}]
    assert validate_invocation_record(wrong)[0] is False
    contradiction = _record()
    contradiction["recorded_tool_calls"] = []
    assert validate_invocation_record(contradiction)[0] is False
    self_attested = _record(telemetry=False)
    assert validate_invocation_record(self_attested)[0] is True

    records = {
        f"inv-{index}": _record("shared" if index <= 2 else f"unique-{index}")
        for index in range(1, 6)
    }
    panel = evaluate_panel(records, 5)
    assert panel["status"] == "panel_ready" and len(panel["eligible"]) == 5
    promoted = promote_candidates(panel["eligible"])
    assert len(promoted) == 1
    calls = []

    def negative_evaluator(material):
        calls.append(material)
        return {
            "material_sha256": hashlib.sha256(material).hexdigest(),
            "outcome": "negative",
            "records": [],
        }

    result = close_phase(records, 5, evaluator=negative_evaluator)
    assert result["outcome"] == "novel_convergence_negative"
    assert calls == [b"shared"]
    assert close_phase({}, INVOCATION_CAP + 1)["outcome"] == "protocol_invalid"
    assert invocation_task_name(1) == "phase420_invocation_1"
    assert invocation_task_name(8) == "phase420_invocation_8"

    return {
        "prompt_length": len(prompt),
        "prompt_sha256": prompt_digest,
        "prompt_line_count": len(prompt.splitlines()),
        "launcher_length": len(launcher),
        "launcher_sha256": launcher_digest,
        "evidence_packet_sha256": packet_digest,
        "phase270_base_candidates": len(phase418.phase270_inventory()["base_values"]),
        "phase270_materials": len(phase418.phase270_inventory()["materials"]),
        "solver_invocations": 0,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--show-digests", action="store_true")
    args = parser.parse_args()
    if args.write_artifacts or args.show_digests:
        report = write_artifacts() if args.write_artifacts else {
            "prompt_length": len(_render_prompt()[0]),
            "prompt_sha256": _render_prompt()[1],
            "prompt_line_count": len(_render_prompt()[0].splitlines()),
            "launcher_length": len(LAUNCHER_TEXT),
            "launcher_sha256": hashlib.sha256(LAUNCHER_TEXT.encode()).hexdigest(),
        }
    else:
        report = self_test()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
