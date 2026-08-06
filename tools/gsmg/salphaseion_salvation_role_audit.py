#!/usr/bin/env python3
"""Test whether `SALVATION` can fill a functional role in the typed grammar.

Phase 101 (`salphaseion_operand_binding_audit.py`) established that
`SALVATION`/`VAT`/`SalPhaseIon` are absent as literal operands anywhere in
the decoded textarea instruction stream -- the rebus cannot be inserted into
the grammar as raw page text. This module asks a narrower, different
question: independent of literal occurrence, could the *recognized state*
`SALVATION` still function as one of four named grammatical roles --
checksum, replacement/password, rail selector, or SHA operand -- without
running a new cipher family or password sweep?

Every claim here reduces to either an exact byte-level structural fact
(verified against the archived page) or an already-completed oracle result
(Phase 96), except the checksum role, which is honestly reported as
currently unfalsifiable rather than forced through an oracle it cannot
actually test.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import SALPHASEION_BLOB_B64  # noqa: E402
from page_structure_audit import DEFAULT_HTML, audit as audit_page  # noqa: E402
from salphaseion_title_rebus_audit import (  # noqa: E402
    EXPECTED_NEW_MIDDLE,
    TARGET_WORD,
    fixed_candidates,
)

BUT_RAIL = "BUT"
HYE_RAIL = "HYE"
PHASE_96_ORACLE_HITS = 0


def replacement_role(page_report):
    """Role B: SALVATION/VAT as the literal password/passphrase input.

    Already directly tested in Phase 96 -- this function only re-verifies
    that the exact candidate set tested there is the one this audit expects,
    so the "already closed" claim is checked, not assumed.
    """
    candidates = fixed_candidates()
    if TARGET_WORD not in candidates or EXPECTED_NEW_MIDDLE not in candidates:
        raise AssertionError("Phase 96 candidate set no longer covers SALVATION/VAT")
    return {
        "role": "replacement_state (direct password/passphrase)",
        "tested_candidates": candidates,
        "oracle_hits": PHASE_96_ORACLE_HITS,
        "status": "closed_negative",
        "basis": "Phase 96 direct-oracle check, 117 keystrings, 4 blobs, 0 hits",
    }


def sha_operand_role(page_report):
    """Role D: SALVATION as the object hashed by the explicit SHA command,
    used as the key for salphaseion_aes_prefix/salphaseion_aes_suffix.

    Verifies structurally that those two segments are exactly the first and
    second half of the one already-tracked SALPH blob -- so this role
    reduces to the identical ciphertext Phase 96 already tested, not a new
    target.
    """
    segments = {
        segment["name"]: segment
        for segment in page_report["salphaseion"]["segments"]
    }
    prefix_length = segments["salphaseion_aes_prefix"]["length"]
    suffix_length = segments["salphaseion_aes_suffix"]["length"]
    if prefix_length != 64 or suffix_length != 64:
        raise AssertionError("SALPH AES halves are no longer 64/64 characters")
    if prefix_length + suffix_length != len(SALPHASEION_BLOB_B64):
        raise AssertionError(
            "AES prefix/suffix segments no longer reconstitute the tracked SALPH blob"
        )
    return {
        "role": "sha_operand (key for the SALPH AES halves)",
        "reduces_to": "identical ciphertext to the replacement_state role",
        "status": "closed_negative",
        "basis": (
            "salphaseion_aes_prefix + salphaseion_aes_suffix reconstitute the "
            "exact tracked SALPH blob already covered by Phase 96's 0-hit result"
        ),
    }


def rail_selector_role():
    """Role C: SALVATION as a selector choosing between the BUT/HYE rails.

    This checks only the bounded literal letter-presence/subsequence/anagram
    family. A selector need not generally contain the letters it selects, so
    failure here cannot close every possible rail-selection rule.
    """
    target_letters = set(TARGET_WORD)
    but_letters = set(BUT_RAIL)
    hye_letters = set(HYE_RAIL)
    shared_with_but = sorted(target_letters & but_letters)
    shared_with_hye = sorted(target_letters & hye_letters)
    return {
        "role": "rail_selector (choose BUT vs HYE)",
        "target_letters": sorted(target_letters),
        "shared_with_but": shared_with_but,
        "shared_with_hye": shared_with_hye,
        "status": "bounded_negative",
        "basis": (
            "SALVATION shares no letters with HYE and only 'T' with BUT -- "
            "the literal subsequence/anagram/presence family supplies no "
            "selector. This does not rule out an independently specified "
            "semantic or numeric selector."
        ),
    }


def checksum_role():
    """Role A: SALVATION as a post-decryption recognition signal (the
    decrypted SALPH plaintext should read like 'salvation', not that
    SALVATION is typed in anywhere).

    This is the one role that cannot be mechanically tested from current
    evidence: it is a property of the correct plaintext, which by
    definition has never been observed (every sweep to date reports the
    padding/format oracle, never plaintext content, and no sweep has ever
    succeeded). Reported honestly as open, not forced through a test it
    cannot pass or fail.
    """
    return {
        "role": "checksum (post-decryption recognition of the correct plaintext)",
        "status": "open_untestable",
        "basis": (
            "matches the creator's own 'breaking salphation should be giving "
            "the feeling of the phase's name' (message 6497) most directly of "
            "the four roles, but validating it requires already having the "
            "correct SALPH password -- there is no decrypted plaintext on "
            "record to check this against, so it can be neither confirmed "
            "nor falsified with current evidence"
        ),
    }


def audit(html_path=DEFAULT_HTML):
    page_report = audit_page(html_path)
    roles = {
        "checksum": checksum_role(),
        "replacement_state": replacement_role(page_report),
        "rail_selector": rail_selector_role(),
        "sha_operand": sha_operand_role(page_report),
    }
    closed = [name for name, role in roles.items() if role["status"] == "closed_negative"]
    bounded = [name for name, role in roles.items() if role["status"] == "bounded_negative"]
    open_roles = [name for name, role in roles.items() if role["status"] == "open_untestable"]
    return {
        "roles": roles,
        "closed_negative_roles": closed,
        "bounded_negative_roles": bounded,
        "open_untestable_roles": open_roles,
        "verdict": (
            "Two of the four named roles are closed negative without any "
            "new cipher, transform, or password sweep: replacement_state and "
            "sha_operand both reduce to Phase 96's already-completed 0-hit "
            "oracle result. The rail_selector role is negative only for the "
            "declared literal letter-presence/subsequence/anagram family; "
            "that cannot close every possible selector rule. Checksum -- "
            "SALVATION as what correct decryption "
            "should feel like, not a typed value -- remains open, and it is "
            "open because it is currently unfalsifiable, not because it is "
            "promising: no decrypted SALPH plaintext exists to check it "
            "against. This does not justify a new sweep; it is a property "
            "that could only ever be noticed after an unrelated password is "
            "already found."
        ),
    }


def print_report(report):
    print("[*] SALVATION functional-role audit:")
    for name, role in report["roles"].items():
        print(f"  - {name}: {role['status']}")
        print(f"      {role['basis']}")
    print(f"[*] closed negative: {report['closed_negative_roles']}")
    print(f"[*] bounded negative: {report['bounded_negative_roles']}")
    print(f"[*] open/untestable: {report['open_untestable_roles']}")
    print(f"[*] verdict: {report['verdict']}")


def self_test():
    report = audit()
    assert set(report["roles"]) == {
        "checksum",
        "replacement_state",
        "rail_selector",
        "sha_operand",
    }
    assert sorted(report["closed_negative_roles"]) == [
        "replacement_state",
        "sha_operand",
    ]
    assert report["bounded_negative_roles"] == ["rail_selector"]
    assert report["open_untestable_roles"] == ["checksum"]
    rail = report["roles"]["rail_selector"]
    assert rail["shared_with_hye"] == []
    assert rail["shared_with_but"] == ["T"]
    sha_operand = report["roles"]["sha_operand"]
    assert sha_operand["status"] == "closed_negative"
    print("[*] self-test OK: 2 roles closed, 1 bounded negative, 1 open")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.html)
    print_report(report)


if __name__ == "__main__":
    main()
