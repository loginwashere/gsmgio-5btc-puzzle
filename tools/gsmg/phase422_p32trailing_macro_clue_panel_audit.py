#!/usr/bin/env python3
"""Phase 422: macro-clue augmentation of the working Phase 421 panel.

This module renders and verifies the frozen packet, prompt, launcher, and
prior-evaluation comparator.  It never invokes a solver.
"""

import hashlib
import itertools
import json
import sys
from functools import lru_cache
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import macro_clue_permutation_combinations as macro_perms  # noqa: E402
import minimal_macro_chain_audit as macro_chain  # noqa: E402
import phase418_p32trailing_solution_complete_blinded_reconstruction_audit as phase418  # noqa: E402
import phase420_p32trailing_one_file_bootstrap_panel_audit as phase420  # noqa: E402
import phase421_execution_replay as phase421_replay  # noqa: E402
import phase421_p32trailing_escalated_bootstrap_panel_audit as phase421  # noqa: E402
import salphaseion_title_rebus_audit as title_rebus  # noqa: E402
from cb_common import answer_forms, keystr_forms  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402


INVOCATION_CAP = phase421.INVOCATION_CAP
PANEL_TARGET = phase421.PANEL_TARGET
MAX_SOLVER_CANDIDATES = phase420.MAX_SOLVER_CANDIDATES
parse_submission = phase421.parse_submission
validate_submission_schema = phase421.validate_submission_schema
promote_candidates = phase421.promote_candidates

EXPORT_PATH = DEFAULT_EXPORT_DIR / "result.json"
EVIDENCE_PACKET_PATH = SCRIPT_DIR / "phase422_sealed_evidence_packet.txt"
PROMPT_PATH = SCRIPT_DIR / "phase422_frozen_solver_prompt.txt"
LAUNCHER_PATH = SCRIPT_DIR / "phase422_frozen_launcher.txt"

MACRO_MESSAGE_ID = 8446
MACRO_CREATOR_ID = "user9815232"
MACRO_RAW_BIT_COUNT = 1288
MACRO_RAW_BITS_SHA256 = "f57865d4211d8541c5e6b9b3fe72831e64d7fa81d57137d928ea39b7baa5d2fc"
MACRO_FRAGMENTS = macro_perms.MACRO_CLUE
MACRO_TEXT = "".join(MACRO_FRAGMENTS)
MACRO_TEXT_SHA256 = "d13afe77dd6969a438e2020cc3df22e0e7d589ae88196caa9162c9168e25a018"

PHASE270_COMPARATOR_COUNT = 50
PHASE270_COMPARATOR_SHA256 = "2a374072d2cb565654b60983429b0385042a2f64ca0aa3fecdbe5fb929b70e01"
PHASE421_COMPARATOR_COUNT = 8
PHASE421_COMPARATOR_SHA256 = "846ba6a59c65ebf6b63b4b342b5beb26859ec7cf5cfb186a73ebd31dcb2c5e00"
MACRO_COMPARATOR_COUNT = 1_972_800
MACRO_COMPARATOR_SHA256 = "3c8ae04b290fd50db73ed5b787c653ae5418292ed81fc6dbd55a692c06267568"
COMPARATOR_UNION_COUNT = 1_972_858
COMPARATOR_UNION_SHA256 = "7490b960c9add8373394dd91e42e4f85289d071d6f655ea4cf5a81b2668a9c21"

EVIDENCE_PACKET_LENGTH = 14082
EVIDENCE_PACKET_SHA256 = "ba01a36ddb12de49236f364106d1dcf34c8e94e6574e0bb7bf74a0db7acbe834"
PROMPT_LENGTH = 16551
PROMPT_SHA256 = "f97756c690ad5172780a71152dae1bf705bf4cbe63c3eebcd0746d27ce728dc3"
PROMPT_LINE_COUNT = 257
LAUNCHER_LENGTH = 672
LAUNCHER_SHA256 = "050ab622f7e6cd355df71ebf5d819e334db7c206972c08a39e68a7c5672ab200"

PERMITTED_COMMAND = (
    "sed -n '1,320p' "
    "/home/loginwashere/projects/gsmgio-5btc-puzzle/tools/gsmg/"
    "phase422_frozen_solver_prompt.txt"
)
PERMITTED_WORKDIR = phase421.PERMITTED_WORKDIR
SANDBOX_PERMISSIONS = phase421.SANDBOX_PERMISSIONS
JUSTIFICATION = phase421.JUSTIFICATION

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

INVOCATION_CONFIGURATION = {
    **phase421.INVOCATION_CONFIGURATION,
    "cmd": PERMITTED_COMMAND,
}
EXPECTED_RECORDED_CALL = {"tool": "exec_command", "command": PERMITTED_COMMAND}


def validate_invocation_record(record):
    """Apply Phase 420's record contract with Phase 422's exact command."""
    if not isinstance(record, dict) or set(record) != phase420.REQUIRED_RECORD_KEYS:
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
    if phase420.phase416.blinding_violations(
        phase420.phase416.submission_full_text(submission)
    ):
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


def _framed_digest(values):
    """Digest an ordered byte sequence with unambiguous 8-byte lengths."""
    digest = hashlib.sha256()
    count = 0
    for value in values:
        if not isinstance(value, bytes):
            raise TypeError("comparator values must be bytes")
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
        count += 1
    return count, digest.hexdigest()


def _macro_materials():
    """Reproduce Phase 322/334's 18 unique tested strings per base value."""
    for base in itertools.chain(macro_perms.generate(), macro_perms.generate_k8()):
        forms = sorted(answer_forms(base))
        emitted = set()
        for form in forms:
            for keystring in keystr_forms(form, newline_variants=True):
                material = keystring.encode("utf-8")
                if material not in emitted:
                    emitted.add(material)
                    yield material
        if len(emitted) != 18:
            raise AssertionError("macro base no longer expands to 18 unique materials")


def _phase270_materials():
    inventory = phase418.phase270_inventory()
    return tuple(sorted(inventory["materials"]))


def _phase421_evaluated_materials():
    rows = phase421_replay.candidate_rows()
    expected = {
        item["candidate_sha256"]
        for item in json.loads(phase421_replay.RESULT_PATH.read_text(encoding="utf-8"))["evaluations"]
    }
    resolved = {}
    for displays in rows.values():
        for display in displays:
            material = display.encode("utf-8")
            digest = hashlib.sha256(material).hexdigest()
            if digest in expected:
                resolved[digest] = material
    if set(resolved) != expected or len(resolved) != PHASE421_COMPARATOR_COUNT:
        raise AssertionError("Phase 421 evaluation digests did not resolve to replay bytes")
    return tuple(resolved[digest] for digest in sorted(resolved))


@lru_cache(maxsize=1)
def comparator_manifest():
    phase270_values = _phase270_materials()
    phase421_values = _phase421_evaluated_materials()
    phase270 = _framed_digest(phase270_values)
    phase421_values_digest = _framed_digest(phase421_values)
    macro = _framed_digest(_macro_materials())

    if set(phase270_values) & set(phase421_values):
        raise AssertionError("Phase 270 and evaluated Phase 421 comparator sets overlap")

    # The macro stream is too large to retain.  Verify disjointness of the two
    # small components and compute the canonical union digest in source order.
    small = set(phase270_values) | set(phase421_values)
    overlap = set()
    union_digest = hashlib.sha256()
    union_count = 0
    for material in itertools.chain(phase270_values, phase421_values, _macro_materials()):
        if union_count >= len(small) and material in small:
            overlap.add(material)
        union_digest.update(len(material).to_bytes(8, "big"))
        union_digest.update(material)
        union_count += 1
    if overlap:
        raise AssertionError("macro comparator overlaps a small comparator component")

    manifest = {
        "phase270": {"count": phase270[0], "sha256": phase270[1]},
        "phase421_evaluated": {
            "count": phase421_values_digest[0],
            "sha256": phase421_values_digest[1],
        },
        "macro_phase322_334": {"count": macro[0], "sha256": macro[1]},
        "union": {"count": union_count, "sha256": union_digest.hexdigest()},
    }
    return manifest


def _check_comparator_pins():
    manifest = comparator_manifest()
    expected = {
        "phase270": (PHASE270_COMPARATOR_COUNT, PHASE270_COMPARATOR_SHA256),
        "phase421_evaluated": (PHASE421_COMPARATOR_COUNT, PHASE421_COMPARATOR_SHA256),
        "macro_phase322_334": (MACRO_COMPARATOR_COUNT, MACRO_COMPARATOR_SHA256),
        "union": (COMPARATOR_UNION_COUNT, COMPARATOR_UNION_SHA256),
    }
    for label, (count, digest) in expected.items():
        if manifest[label] != {"count": count, "sha256": digest}:
            raise AssertionError(f"{label} comparator commitment drifted")
    return manifest


def classify_comparator_membership(materials):
    """Classify a small set of exact candidate bytes in one macro-stream pass."""
    if any(not isinstance(value, bytes) for value in materials):
        raise TypeError("candidate material must be bytes")
    _check_comparator_pins()
    wanted = set(materials)
    matched = wanted & (set(_phase270_materials()) | set(_phase421_evaluated_materials()))
    remaining = wanted - matched
    if remaining:
        for value in _macro_materials():
            if value in remaining:
                matched.add(value)
                remaining.remove(value)
                if not remaining:
                    break
    return {
        value: (
            "exact_duplicate_in_frozen_comparator"
            if value in matched else "not_in_frozen_comparator"
        )
        for value in wanted
    }


def recover_macro_state():
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    message = next(row for row in payload["messages"] if row.get("id") == MACRO_MESSAGE_ID)
    if message.get("from_id") != MACRO_CREATOR_ID:
        raise AssertionError("message 8446 creator identity drifted")
    raw = title_rebus.flatten_text(message.get("text", ""))
    bits = "".join(raw.split())
    if len(bits) != MACRO_RAW_BIT_COUNT or hashlib.sha256(bits.encode()).hexdigest() != MACRO_RAW_BITS_SHA256:
        raise AssertionError("message 8446 raw bitstream drifted")
    decoded = title_rebus.decode_reversed_bitstream(raw)
    if decoded != MACRO_TEXT:
        raise AssertionError("message 8446 decoded text drifted")
    if hashlib.sha256(decoded.encode()).hexdigest() != MACRO_TEXT_SHA256:
        raise AssertionError("decoded macro commitment drifted")

    chain = macro_chain.audit(EXPORT_PATH)
    expected_chain = {
        "prime": 574061,
        "matrix": [[5, 7, 4], [0, 6, 1]],
        "sum_list": (23, 16, 7),
        "selected_words": ("both", "ultimately", "the"),
        "edge_rails": ("but", "hye"),
    }
    for key, value in expected_chain.items():
        if chain[key] != value:
            raise AssertionError(f"macro-chain {key} drifted")
    if chain["scope_comparison"]["minimal_prime_operand"]["reaches_macro_yinyang"]:
        raise AssertionError("macro chain unexpectedly claims to reach yinyang")

    title = title_rebus.load_title(title_rebus.DEFAULT_HTML)
    replacement = title_rebus.split_replacement(title, title_rebus.TARGET_WORD)
    readings = title_rebus.clue_readings()
    if title != "SalPhaseIon" or replacement != {
        "prefix": "SAL", "source_middle": "PHASE", "target_middle": "VAT", "suffix": "ION",
    }:
        raise AssertionError("bounded title replacement drifted")
    if readings["give_away_g"] != "VAT":
        raise AssertionError("final-clause VAT reading drifted")
    return {"decoded": decoded, "chain": chain, "title": title}


def _macro_supplement():
    state = recover_macro_state()
    fragments = "\n".join(f"  {index}. {value}" for index, value in enumerate(MACRO_FRAGMENTS, 1))
    return f"""
==============================================================================
ITEM 6 -- Controlled creator macro-clue augmentation.
==============================================================================

Primary creator artifact (Telegram message 8446), decoded by reversing the
complete 1,288-bit stream and reading ASCII. It fixes these exact ordered
fragments, but does not by itself prove a password or strict program:

{fragments}

Bounded project state, with evidence levels kept distinct:

  * Default community-derived working grammar (three visible judgment calls):
    yellowblueprimes -> 574061 -> [[5,7,4],[0,6,1]] -> [23,16,7]
    -> BOTH / ULTIMATELY / THE -> BUT / HYE.
  * Parked recognition hypothesis: a mixed edge/mirror reading can produce BYE,
    but no source authenticates that operation or identifies its consumer.
  * Unresolved: yinyang and the referent of
    itsinfrontofyoureyesbutyourenotseeingit remain unverified.
  * Bounded researcher-established title rebus: archived title {state['title']}
    -> SalVATIon -> SALVATION. This is structural, not creator-confirmed
    P32TRAILING password provenance.
  * Prior negative: all direct order-sensitive concatenations of 1-8 distinct
    macro fragments were already tested. Hidden exact-byte duplicate filtering
    occurs only after the panel closes; do not omit an otherwise strong answer.

Use this supplement only to propose exact packet-supported preimages. Clearly
distinguish creator-authored text from community-derived and parked readings.
"""


def _render_packet():
    base, digest = phase418.build_evidence_packet()
    if digest != phase418.SEALED_EVIDENCE_PACKET_SHA256:
        raise AssertionError("Phase 418 base packet drifted")
    packet = base + "\n" + _macro_supplement()
    phase418._assert_solver_visible_content(packet, phase418.recover_solution_state())
    return packet, hashlib.sha256(packet.encode()).hexdigest()


def _render_prompt():
    base_prompt = phase420.PROMPT_PATH.read_text(encoding="utf-8")
    base_packet, _ = phase418.build_evidence_packet()
    packet, _ = _render_packet()
    if base_prompt.count(base_packet) != 1:
        raise AssertionError("Phase 420 packet replacement boundary drifted")
    if base_prompt.count(phase420.PERMITTED_COMMAND) != 1:
        raise AssertionError("Phase 420 bootstrap command replacement boundary drifted")
    prompt = base_prompt.replace(base_packet, packet).replace(
        phase420.PERMITTED_COMMAND, PERMITTED_COMMAND
    )
    prompt = prompt.replace(
        "The evidence packet contains the already-decrypted parent\nplaintext, all currently solved nested outputs, three worked solved boundaries,",
        "The evidence packet contains the already-decrypted parent\nplaintext, all currently solved nested outputs, the controlled creator macro-clue\naugmentation, three worked solved boundaries,",
    )
    prompt = prompt.replace(
        "Explain which disclosed source or solved value and which\noperation licenses every byte.",
        "Explain which disclosed source, solved value, or macro item and which\noperation licenses every byte; preserve the packet's evidence labels.",
    )
    _assert_solver_visible_content(prompt)
    return prompt, hashlib.sha256(prompt.encode()).hexdigest()


def _assert_solver_visible_content(text):
    phase418._assert_solver_visible_content(text, phase418.recover_solution_state())
    required = (*MACRO_FRAGMENTS, "574061", "[23,16,7]", "BUT / HYE", "SalVATIon", "SALVATION")
    for value in required:
        if value not in text:
            raise AssertionError(f"required macro supplement value absent: {value!r}")
    # Some Phase 421 candidates were verbatim source values already present in
    # the Phase 418/420 baseline (for example the solved 91-byte answer).  They
    # are not response leakage.  Reject only a long candidate newly introduced
    # beyond that byte-identical baseline.
    baseline = phase420.PROMPT_PATH.read_text(encoding="utf-8")
    rows = phase421_replay.candidate_rows()
    for displays in rows.values():
        for display in displays:
            if (
                len(display.encode("utf-8")) >= 40
                and display in text
                and display not in baseline
            ):
                raise AssertionError("Phase 421-only candidate leaked into solver-visible material")
    for secret in (PRIZE_ADDRESS, HALVING_ADDRESS):
        if secret in text:
            raise AssertionError("target address leaked into solver-visible material")


def write_artifacts():
    packet, packet_digest = _render_packet()
    prompt, prompt_digest = _render_prompt()
    EVIDENCE_PACKET_PATH.write_bytes(packet.encode("utf-8"))
    PROMPT_PATH.write_bytes(prompt.encode("utf-8"))
    LAUNCHER_PATH.write_bytes(LAUNCHER_TEXT.encode("utf-8"))
    return {
        "packet_length": len(packet), "packet_sha256": packet_digest,
        "prompt_length": len(prompt), "prompt_sha256": prompt_digest,
        "prompt_line_count": len(prompt.splitlines()),
        "launcher_length": len(LAUNCHER_TEXT),
        "launcher_sha256": hashlib.sha256(LAUNCHER_TEXT.encode()).hexdigest(),
        "comparator": comparator_manifest(),
    }


def _checked(text, path, length, digest, label):
    actual = hashlib.sha256(text.encode()).hexdigest()
    if len(text) != length or actual != digest or path.read_bytes() != text.encode():
        raise AssertionError(f"{label} artifact commitment drifted")
    return text, actual


def build_evidence_packet():
    text, digest = _render_packet()
    return _checked(text, EVIDENCE_PACKET_PATH, EVIDENCE_PACKET_LENGTH, EVIDENCE_PACKET_SHA256, "packet")


def build_prompt():
    text, digest = _render_prompt()
    if len(text.splitlines()) != PROMPT_LINE_COUNT or PROMPT_LINE_COUNT > 320:
        raise AssertionError("prompt line-count/read-range invariant drifted")
    packet, _ = build_evidence_packet()
    if packet not in text:
        raise AssertionError("checked packet is not embedded byte-exactly")
    return _checked(text, PROMPT_PATH, PROMPT_LENGTH, PROMPT_SHA256, "prompt")


def build_launcher():
    required = (PERMITTED_COMMAND, PERMITTED_WORKDIR, SANDBOX_PERMISSIONS, JUSTIFICATION)
    if any(value not in LAUNCHER_TEXT for value in required) or "prefix_rule" in LAUNCHER_TEXT:
        raise AssertionError("launcher execution envelope drifted")
    return _checked(LAUNCHER_TEXT, LAUNCHER_PATH, LAUNCHER_LENGTH, LAUNCHER_SHA256, "launcher")


def _redacted_promotion(material, promotion, disposition):
    return {
        "candidate_length": len(material),
        "candidate_sha256": hashlib.sha256(material).hexdigest(),
        "path": promotion["path"], "votes": promotion["votes"],
        "ranks": list(promotion["ranks"]), "best_rank": min(promotion["ranks"]),
        "comparator_disposition": disposition,
    }


def classify_completed_panel(eligible, evaluator=None):
    if len(eligible) != PANEL_TARGET:
        raise ValueError("outcome classification requires exactly five eligible submissions")
    evaluator = phase418.evaluate_candidate if evaluator is None else evaluator
    promoted = promote_candidates(eligible)
    all_materials = {
        candidate["material"] for submission in eligible for candidate in submission["accepted"]
    }
    dispositions = classify_comparator_membership(
        [bytes.fromhex(value) for value in promoted]
    )
    manifest, new = [], []
    for hex_value, promotion in sorted(promoted.items(), key=phase418._promotion_sort_key):
        material = bytes.fromhex(hex_value)
        disposition = dispositions[material]
        manifest.append(_redacted_promotion(material, promotion, disposition))
        if disposition == "not_in_frozen_comparator":
            new.append((material, promotion))

    evaluations, stop = [], None
    for material, promotion in new:
        evaluation = evaluator(material)
        phase418._assert_evaluation_redacted(evaluation)
        if evaluation.get("material_sha256") not in (None, hashlib.sha256(material).hexdigest()):
            raise AssertionError("evaluator material digest disagrees with candidate")
        evaluations.append({
            **_redacted_promotion(material, promotion, "not_in_frozen_comparator"),
            "evaluation": evaluation,
        })
        if evaluation["outcome"] in {"terminal_hit", "structural_hit"}:
            stop = evaluation["outcome"]
            break

    if stop:
        outcome = stop
    elif new:
        outcome = "comparison_new_convergence_negative"
    elif manifest:
        outcome = "duplicate_only_convergence"
    else:
        outcome = "no_convergence"
    return {
        "outcome": outcome, "eligible_count": len(eligible),
        "distinct_candidate_count": len(all_materials), "promoted_count": len(manifest),
        "duplicate_promoted_count": sum(
            row["comparator_disposition"] == "exact_duplicate_in_frozen_comparator"
            for row in manifest
        ),
        "comparison_new_promoted_count": len(new), "evaluated_new_count": len(evaluations),
        "unevaluated_new_after_stop": len(new) - len(evaluations),
        "promoted": manifest, "evaluations": evaluations, "protocol_invalid_reason": None,
    }


def close_phase(invocation_records, invocations_used, evaluator=None):
    try:
        panel = evaluate_panel(invocation_records, invocations_used)
        if panel["status"] == "protocol_invalid":
            return {"outcome": "protocol_invalid", "protocol_invalid_reason": "five eligible submissions not obtained within eight invocations", "eligible_count": len(panel["eligible"])}
        if panel["status"] == "need_more":
            return {"outcome": "need_more", "eligible_count": len(panel["eligible"])}
        return classify_completed_panel(panel["eligible"], evaluator=evaluator)
    except (AssertionError, ValueError, TypeError) as exc:
        return {"outcome": "protocol_invalid", "protocol_invalid_reason": str(exc)}


def invocation_task_name(number):
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("invocation number must be a plain integer")
    if not 1 <= number <= INVOCATION_CAP:
        raise ValueError("invocation number is outside the frozen 1..8 cap")
    return f"phase422_invocation_{number}"


def _records(shared):
    return {
        f"inv-{index}": phase420._record(shared if index <= 2 else f"unique-{index}", telemetry=False)
        for index in range(1, 6)
    }


def self_test():
    packet, packet_digest = build_evidence_packet()
    prompt, prompt_digest = build_prompt()
    launcher, launcher_digest = build_launcher()
    comparator = _check_comparator_pins()
    assert phase418.build_evidence_packet()[0] in packet
    assert packet in prompt and PERMITTED_COMMAND in prompt and PERMITTED_COMMAND in launcher
    assert invocation_task_name(1) == "phase422_invocation_1"
    assert invocation_task_name(8) == "phase422_invocation_8"
    assert close_phase({}, INVOCATION_CAP + 1)["outcome"] == "protocol_invalid"
    assert parse_submission is phase421.parse_submission
    assert validate_submission_schema is phase421.validate_submission_schema
    assert promote_candidates is phase421.promote_candidates

    telemetry_record = phase420._record("telemetry-fixture", telemetry=True)
    telemetry_record["recorded_tool_calls"] = [EXPECTED_RECORDED_CALL]
    assert validate_invocation_record(telemetry_record)[0] is True
    old_command_record = phase420._record("old-command-fixture", telemetry=True)
    assert validate_invocation_record(old_command_record)[0] is False
    self_attested_record = phase420._record(
        "self-attested-fixture", telemetry=False
    )
    assert validate_invocation_record(self_attested_record)[0] is True

    duplicate = MACRO_FRAGMENTS[0]
    calls = []
    result = close_phase(_records(duplicate), 5, evaluator=lambda value: calls.append(value))
    assert result["outcome"] == "duplicate_only_convergence" and not calls

    def evaluator(outcome):
        def run(material):
            calls.append(material)
            return {"material_sha256": hashlib.sha256(material).hexdigest(), "outcome": outcome, "records": []}
        return run

    calls.clear()
    result = close_phase(_records("comparison-new-fixture"), 5, evaluator=evaluator("negative"))
    assert result["outcome"] == "comparison_new_convergence_negative" and calls == [b"comparison-new-fixture"]
    calls.clear()
    assert close_phase(_records("terminal-fixture"), 5, evaluator=evaluator("terminal_hit"))["outcome"] == "terminal_hit"
    calls.clear()
    assert close_phase(_records("structural-fixture"), 5, evaluator=evaluator("structural_hit"))["outcome"] == "structural_hit"
    no_convergence = {
        f"inv-{index}": phase420._record(f"only-{index}", telemetry=False)
        for index in range(1, 6)
    }
    assert close_phase(no_convergence, 5)["outcome"] == "no_convergence"

    return {
        "packet_length": len(packet), "packet_sha256": packet_digest,
        "prompt_length": len(prompt), "prompt_sha256": prompt_digest,
        "prompt_line_count": len(prompt.splitlines()),
        "launcher_length": len(launcher), "launcher_sha256": launcher_digest,
        "comparator": comparator, "solver_invocations": 0,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--show-digests", action="store_true")
    args = parser.parse_args()
    report = write_artifacts() if (args.write_artifacts or args.show_digests) else self_test()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
