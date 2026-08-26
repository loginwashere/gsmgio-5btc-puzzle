#!/usr/bin/env python3
"""Phase 421: escalated one-file delivery correction for Phase 420.

This module does not invoke panel solvers. It freezes the exact exec_command
envelope proven by the excluded pre-registration diagnostic and otherwise
imports Phase 420's prompt, schema, panel, and result logic unchanged.
"""

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase420_p32trailing_one_file_bootstrap_panel_audit as phase420  # noqa: E402


INVOCATION_CAP = phase420.INVOCATION_CAP
PANEL_TARGET = phase420.PANEL_TARGET
PROMPT_PATH = phase420.PROMPT_PATH
LAUNCHER_PATH = SCRIPT_DIR / "phase421_frozen_launcher.txt"
PERMITTED_COMMAND = phase420.PERMITTED_COMMAND
PERMITTED_WORKDIR = "/home/loginwashere/projects/gsmgio-5btc-puzzle"
SANDBOX_PERMISSIONS = "require_escalated"
JUSTIFICATION = (
    "May I perform the preregistered read-only prompt bootstrap outside the "
    "unavailable sandbox?"
)

LAUNCHER_TEXT = f"""Read the complete solver prompt using exactly one exec_command tool call with
these parameters and no other tool call:
- cmd: {PERMITTED_COMMAND}
- workdir: {PERMITTED_WORKDIR}
- sandbox_permissions: {SANDBOX_PERMISSIONS}
- justification: {JUSTIFICATION}

The read above is the only permitted bootstrap action. Follow the file exactly.
Return only the JSON object it requests. Do not inspect any other file, run any
other command, use any other tool, or retrieve external information.
"""

# Mechanically generated and pinned before the implementation commit.
LAUNCHER_LENGTH = 672
LAUNCHER_SHA256 = "3bf3c9cb0b21b1afab89e4d8e9f4ce7b50d6d8b1fc8a164f68da7fffd261cc82"

INVOCATION_CONFIGURATION = {
    "agent_class": "general-purpose",
    "fork_turns": "none",
    "model_override": None,
    "reasoning_effort_override": None,
    "service_configuration": "default",
    "delivery": "escalated_one_file_bootstrap",
    "cmd": PERMITTED_COMMAND,
    "workdir": PERMITTED_WORKDIR,
    "sandbox_permissions": SANDBOX_PERMISSIONS,
    "justification": JUSTIFICATION,
    "prefix_rule": None,
}

# Reuse the complete post-delivery protocol by identity.
parse_submission = phase420.parse_submission
validate_submission_schema = phase420.validate_submission_schema
validate_invocation_record = phase420.validate_invocation_record
eligible_submissions = phase420.eligible_submissions
evaluate_panel = phase420.evaluate_panel
promote_candidates = phase420.promote_candidates
classify_completed_panel = phase420.classify_completed_panel
close_phase = phase420.close_phase


def write_artifact():
    LAUNCHER_PATH.write_bytes(LAUNCHER_TEXT.encode("utf-8"))
    return {
        "launcher_length": len(LAUNCHER_TEXT),
        "launcher_sha256": hashlib.sha256(LAUNCHER_TEXT.encode("utf-8")).hexdigest(),
    }


def build_launcher():
    encoded = LAUNCHER_TEXT.encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    if len(LAUNCHER_TEXT) != LAUNCHER_LENGTH:
        raise AssertionError("Phase 421 launcher length drifted")
    if digest != LAUNCHER_SHA256:
        raise AssertionError("Phase 421 launcher SHA-256 drifted")
    if LAUNCHER_PATH.read_bytes() != encoded:
        raise AssertionError("Phase 421 launcher differs from committed artifact")
    required = (
        PERMITTED_COMMAND,
        f"- workdir: {PERMITTED_WORKDIR}",
        f"- sandbox_permissions: {SANDBOX_PERMISSIONS}",
        f"- justification: {JUSTIFICATION}",
    )
    for value in required:
        if value not in LAUNCHER_TEXT:
            raise AssertionError(f"required execution parameter absent: {value!r}")
    if "prefix_rule" in LAUNCHER_TEXT:
        raise AssertionError("launcher must not request a prefix rule")
    return LAUNCHER_TEXT, digest


def build_prompt():
    prompt, digest = phase420.build_prompt()
    if PROMPT_PATH != phase420.PROMPT_PATH:
        raise AssertionError("Phase 420 prompt path drifted")
    if len(prompt.splitlines()) != 219 or len(prompt.splitlines()) > 260:
        raise AssertionError("imported prompt no longer fits the fixed read")
    return prompt, digest


def invocation_task_name(invocation_number):
    if not isinstance(invocation_number, int) or isinstance(invocation_number, bool):
        raise TypeError("invocation number must be a plain integer")
    if not 1 <= invocation_number <= INVOCATION_CAP:
        raise ValueError("invocation number is outside the frozen 1..8 cap")
    return f"phase421_invocation_{invocation_number}"


def self_test():
    launcher, launcher_digest = build_launcher()
    prompt, prompt_digest = build_prompt()

    assert parse_submission is phase420.parse_submission
    assert validate_submission_schema is phase420.validate_submission_schema
    assert validate_invocation_record is phase420.validate_invocation_record
    assert eligible_submissions is phase420.eligible_submissions
    assert evaluate_panel is phase420.evaluate_panel
    assert promote_candidates is phase420.promote_candidates
    assert classify_completed_panel is phase420.classify_completed_panel
    assert close_phase is phase420.close_phase
    assert invocation_task_name(1) == "phase421_invocation_1"
    assert invocation_task_name(8) == "phase421_invocation_8"
    assert close_phase({}, INVOCATION_CAP + 1)["outcome"] == "protocol_invalid"

    records = {
        f"inv-{index}": phase420._record(
            "shared-new-fixture" if index <= 2 else f"unique-{index}",
            telemetry=False,
        )
        for index in range(1, 6)
    }
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
    assert calls == [b"shared-new-fixture"]

    original_length = globals()["LAUNCHER_LENGTH"]
    try:
        globals()["LAUNCHER_LENGTH"] = -1
        try:
            build_launcher()
            raise AssertionError("drifted launcher length was accepted")
        except AssertionError as exc:
            assert "length drifted" in str(exc)
    finally:
        globals()["LAUNCHER_LENGTH"] = original_length
    build_launcher()

    return {
        "launcher_length": len(launcher),
        "launcher_sha256": launcher_digest,
        "prompt_length": len(prompt),
        "prompt_sha256": prompt_digest,
        "prompt_line_count": len(prompt.splitlines()),
        "diagnostic_invocations_excluded": 1,
        "panel_invocations": 0,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifact", action="store_true")
    args = parser.parse_args()
    report = write_artifact() if args.write_artifact else self_test()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
