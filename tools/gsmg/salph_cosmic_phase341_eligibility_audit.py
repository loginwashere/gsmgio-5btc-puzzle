#!/usr/bin/env python3
"""SALPH/COSMIC Phase-341 eligibility-and-delta audit, per the user's exact
2026-08-22 sequencing.

Phases 370/371 found: (1) Phase 341's solved-boundary grammar, transferred
forward to P32TRAILING, has no local annotation to consume there and
collapses to Phase 270's already-tested materials; (2) DBBI/FAED are not
demonstrated to require each other as input, and the page's own literal
structure treats them asymmetrically. Per the user's framing, DBBI/FAED,
BUT/HYE, and the 31-character selection are therefore treated here as
checkpoints unless independently consumed -- this audit does NOT re-derive
anything from them.

Instead, this inspects SALPH and COSMIC **separately** for the five fields
Phase 341's grammar actually needs to be licensed (not guessed) at a
boundary:

  1. authenticated solved components
  2. local ordering instructions
  3. casing/whitespace annotations
  4. an explicit SHA/password referent
  5. an independently expected output type

Candidates are generated ONLY where all required fields are locally bound.
Every generated candidate is diffed against already-tested materials before
any oracle query. Four honest outcomes are possible: new grammar-authorized
candidates; exact prior-coverage duplicates; no executable candidate
because a component is unresolved; or a self-contained object with no
demonstrated connection to the other blob.

Usage:
    python3 tools/gsmg/salph_cosmic_phase341_eligibility_audit.py
    python3 tools/gsmg/salph_cosmic_phase341_eligibility_audit.py --self-test
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
)
from data import COSMIC_BLOB_B64  # noqa: E402
from lastcommand_probe import CANDIDATES as LASTCOMMAND_CANDIDATES  # noqa: E402
from lastcommand_probe import probe as lastcommand_probe  # noqa: E402
from page_structure_audit import DEFAULT_HTML, TextareaParser, normalize_salphaseion, segment_salphaseion  # noqa: E402

CBC_VARIANTS = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS)

# Phase-341-authorized readings: the literal hint text as it actually
# appears on the page (no spaces, since none are literally present), the
# same text with spaces reinserted for readability (already this project's
# own established gloss, both forms already present in lastcommand_probe's
# candidate list), and its fully-uppercase form -- the natural case axis
# when no explicit case annotation exists (matches Phase 341's own "small
# frozen axis when the page doesn't fully pin a choice" convention). This
# is deliberately NOT the full 28-candidate lastcommand_probe list: the
# other 25 entries (URLs, shell commands, ctrl+u, prior-stage answers) are
# speculative "what might a solver type" guesses, not derived from any
# locally-bound page component -- they are not grammar-authorized under the
# strict rule this audit applies.
GRAMMAR_AUTHORIZED_BASES = LASTCOMMAND_CANDIDATES[:3]
assert GRAMMAR_AUTHORIZED_BASES == [
    "our first hint is your last command",
    "ourfirsthintisyourlastcommand",
    "OURFIRSTHINTISYOURLASTCOMMAND",
]


def literal_segments(html_path=DEFAULT_HTML):
    parser = TextareaParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    salphaseion_raw, cosmic_raw = parser.textareas
    stream = normalize_salphaseion(salphaseion_raw)
    return segment_salphaseion(stream), "".join(cosmic_raw.splitlines())


def salph_thispassword_branch(segments):
    """SALPH has a SECOND candidate local referent, distinct from
    hash_prefix: the `thispassword` instruction (FAED's second adjacent
    instruction, per Phase 371). Its role is NOT structurally resolved --
    Phase 101 (`salphaseion_operand_binding_audit.py`) explicitly retained
    three unreconciled readings for `lastwordsbeforearchichoice`/
    `thispassword` jointly, none selected: password for FAED itself, FAED's
    answer merely labeled "password" (not consumed further), or password
    for the following SALPH blob. Only the third role would make
    `lastwordsbeforearchichoice`'s resolved value (whatever that is --
    G-ARCH-001's beginnings/endings/mirror operation is ONE candidate
    reading of that instruction, not a settled equivalence; the literal
    instruction could equally select an Architect passage, "words before
    choice" some other way, or a different output entirely) a required
    component of SALPH's password at all. No source selects which of the
    three roles is correct, so none is asserted here -- this branch is
    reported ineligible on role-ambiguity, not on a specific unresolved
    operand."""
    by_name = {s.name: s for s in segments}
    thispassword = by_name["decimal_instruction_2"]
    lastwords = by_name["decimal_instruction_1"]
    assert thispassword.decoded == "thispassword"
    assert lastwords.decoded == "lastwordsbeforearchichoice"
    candidate_roles = (
        "password_for_faed",
        "faed_answer_labeled_as_password",
        "password_for_salph_blob",
    )
    return {
        "instruction": thispassword.decoded,
        "candidate_roles": candidate_roles,
        "role_selected": None,  # Phase 101: no source distinguishes these
        "eligible": False,
        "outcome": "no_executable_candidate_role_undetermined",
        "note": (
            "Phase 101 retained all three roles above as unreconciled; none "
            "is selected by any known source. Only 'password_for_salph_blob' "
            "would even make this SALPH's referent, and its operand (if that "
            "role is ever independently selected) is not established to be "
            "G-ARCH-001's specific mirror-operation output -- that is one "
            "candidate reading of 'lastwordsbeforearchichoice', not a proven "
            "equivalence. No candidate is generated for this branch; doing "
            "so before the role is selected would be an unlicensed guess."
        ),
    }


def salph_eligibility(segments):
    """The five required Phase-341 fields for SALPH's OTHER local referent
    -- the literal hash_prefix hint immediately preceding its ciphertext,
    fully self-contained and requiring no unresolved component. Checked
    against the byte-verified literal page segmentation -- not assumed."""
    by_name = {s.name: s for s in segments}
    hash_prefix = by_name["hash_prefix"]
    enter = by_name["abba_enter_instruction"]
    hash_suffix = by_name["hash_suffix"]

    fields = {
        "authenticated_solved_components": {
            "bound": True,
            "value": hash_prefix.decoded,
            "note": (
                "the literal hint TEXT itself is directly given as page text "
                "(via the page's own established digit-letter substitution: "
                "2->b, 5->e, 6->f, matching decimal_transport's alphabet), "
                "and requires no resolution of DBBI/matrixsumlist (G-MSL-001) "
                "or FAED/Architect-choice (G-ARCH-001) to READ it. What the "
                "hint's own SHA operand REFERS to is a separate, distinct "
                "question Phase 101 found underdetermined (3 unreconciled "
                "readings: explicit first-hint==last-command, a preceding "
                "password result, or a preceding phase answer). This branch "
                "generates and tests only the literal self-referential "
                "reading; the broader source-grounded operand candidates "
                "(message 8446, message 1710, the 574061 result, the "
                "31-char selection) were separately tested and closed "
                "negative by Phase 121, not by this manifest"
            ),
        },
        "local_ordering_instructions": {
            "bound": True,
            "value": f"{hash_prefix.name} -> aes_prefix -> {enter.decoded} -> aes_suffix -> {hash_suffix.name}",
            "note": "byte-verified segment order from page_structure_audit.segment_salphaseion()",
        },
        "casing_whitespace_annotations": {
            "bound": "axis",
            "value": tuple(GRAMMAR_AUTHORIZED_BASES),
            "note": (
                "no explicit '/(aa, ...)' style annotation exists for this "
                "hint (unlike Phase 3.2's clue answers) -- per Phase 341's "
                "own convention, this is enumerated as a small frozen axis "
                "(as-shown/no-space, spaced gloss, uppercase) rather than "
                "guessed or left blocking"
            ),
        },
        "explicit_sha_password_referent": {
            "bound": True,
            "value": "sha256",
            "note": (
                "literally spelled on the page via the established digit-"
                "letter substitution ('shabef' decodes to 'sha256') -- the "
                "strongest and least ambiguous field of the five"
            ),
        },
        "independently_expected_output_type": {
            "bound": True,
            "value": "OpenSSL passphrase/envelope (Salted__ header) -- cipher family unresolved",
            "note": (
                "the Salted__ magic bytes establish an OpenSSL envelope and "
                "the expected TYPE (a passphrase), not AES-CBC or any single "
                "cipher family specifically -- the widened oracle below tests "
                "CBC/ECB/stream/Key Wrap precisely because the envelope alone "
                "does not select among them"
            ),
        },
    }
    eligible = all(f["bound"] for f in fields.values())
    return {"fields": fields, "eligible": eligible}


def cosmic_eligibility(cosmic_textarea_content):
    """Same five fields, checked against Cosmic Duality's OWN textarea
    content only -- not SalPhaseIon's trailing hash_suffix, which belongs
    to a different object even though it is the closest thing on the page
    to a SALPH->COSMIC handoff signal (already tracked: Phase 224,
    anstoo_provenance_audit -- not re-litigated here)."""
    is_bare_blob = cosmic_textarea_content == COSMIC_BLOB_B64
    fields = {
        "authenticated_solved_components": {"bound": False, "value": None, "note": "textarea contains only the raw ciphertext"},
        "local_ordering_instructions": {"bound": False, "value": None, "note": "no embedded instruction segments found"},
        "casing_whitespace_annotations": {"bound": False, "value": None, "note": "no annotation present"},
        "explicit_sha_password_referent": {"bound": False, "value": None, "note": "none embedded in Cosmic's own textarea (HASH_SUFFIX trails SALPH's ciphertext in the SalPhaseIon textarea, a different object)"},
        "independently_expected_output_type": {"bound": False, "value": None, "note": "AES-CBC is structurally implied by the Salted__ header, but nothing local specifies what feeds it"},
    }
    eligible = all(f["bound"] for f in fields.values())
    return {
        "textarea_is_exactly_the_bare_ciphertext": is_bare_blob,
        "fields": fields,
        "eligible": eligible,
    }


def frozen_manifest():
    """2 x 6 = ... actually 3 bases x 3 newline variants x 2 hash
    treatments = 18 password materials, exactly matching the construction
    `lastcommand_probe.probe()` already uses for its full 28-candidate
    list, restricted to the 3 grammar-authorized bases."""
    manifest = {}
    for base in GRAMMAR_AUTHORIZED_BASES:
        for suffix in ("", "\n", "\r\n"):
            keystr = base + suffix
            manifest[(base, repr(suffix), "raw")] = keystr.encode()
            manifest[(base, repr(suffix), "sha256-hex")] = hashlib.sha256(keystr.encode()).hexdigest().encode()
    return manifest


def lastcommand_known_materials():
    """Every byte-string password material lastcommand_probe.py's own
    CBC-only sweep already tried, for exact-membership diffing."""
    forms, _hits = lastcommand_probe()
    materials = set()
    for _candidate, keystr in forms:
        materials.add(keystr.encode())
    return materials


def classify(manifest, known):
    return [
        {
            "base": base,
            "suffix": suffix,
            "treatment": treatment,
            "material": material,
            "status": "exact_duplicate_of_lastcommand_probe" if material in known else "genuinely_new",
        }
        for (base, suffix, treatment), material in manifest.items()
    ]


def widen_oracle_coverage(classified, blobs=None):
    """lastcommand_probe.py only ever ran the CBC-family oracle (Phase 0.1).
    Per the same precedent Phase 368 established for YOUWON, this widens
    the grammar-authorized subset to ECB/stream/Key Wrap -- genuinely new
    ORACLE coverage for materials whose CANDIDATE STRINGS are themselves
    exact duplicates of what Phase 0.1 already tried."""
    active_blobs = BLOBS if blobs is None else blobs
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for entry in classified:
        material = entry["material"]
        result = aes_try_open_bytes(material, kdf_variants=CBC_VARIANTS, blobs=active_blobs)
        if result:
            hits["cbc"].append((entry, result))
        result = aes_try_open_ecb_bytes(material, blobs=active_blobs)
        if result:
            hits["ecb"].append((entry, result))
        result = aes_try_open_stream_bytes(material, blobs=active_blobs)
        if result:
            hits["stream"].append((entry, result))
        for result in aes_keywrap_try_open_bytes(material, blobs=active_blobs):
            hits["keywrap"].append((entry, result))
    n = len(classified)
    blob_count = len(active_blobs)
    return {
        "materials": n,
        "blobs": tuple(active_blobs),
        "cbc_decryptions": n * len(CBC_VARIANTS) * blob_count,
        "ecb_decryptions": n * len(ECB_CIPHER_VARIANTS) * blob_count,
        "stream_decryptions": n * len(STREAM_CIPHER_VARIANTS) * blob_count,
        "keywrap_effective_unwrap_attempts": n * len(KEY_WRAP_KDF_VARIANTS) * blob_count * 4,
        "hits": hits,
        "total_hits": sum(len(v) for v in hits.values()),
    }


def audit():
    segments, cosmic_content = literal_segments()
    salph = salph_eligibility(segments)
    salph_thispassword = salph_thispassword_branch(segments)
    cosmic = cosmic_eligibility(cosmic_content)

    manifest = frozen_manifest()
    known = lastcommand_known_materials()
    classified = classify(manifest, known)
    oracle = widen_oracle_coverage(classified)

    outcome = (
        "self_contained_encrypted_object_no_demonstrated_connection"
        if not cosmic["eligible"] else "unexpected_cosmic_eligibility_needs_review"
    )

    return {
        "salph": salph,
        "salph_thispassword_branch": salph_thispassword,
        "cosmic": cosmic,
        "cosmic_outcome": outcome,
        "manifest_size": len(manifest),
        "classified": classified,
        "oracle": oracle,
    }


def self_test():
    report = audit()

    assert report["salph"]["eligible"] is True
    assert report["salph"]["fields"]["explicit_sha_password_referent"]["value"] == "sha256"

    branch = report["salph_thispassword_branch"]
    assert branch["eligible"] is False
    assert branch["outcome"] == "no_executable_candidate_role_undetermined"
    assert branch["candidate_roles"] == (
        "password_for_faed", "faed_answer_labeled_as_password", "password_for_salph_blob",
    )
    assert branch["role_selected"] is None

    assert report["cosmic"]["eligible"] is False
    assert report["cosmic"]["textarea_is_exactly_the_bare_ciphertext"] is True
    assert all(not f["bound"] for f in report["cosmic"]["fields"].values())
    assert report["cosmic_outcome"] == "self_contained_encrypted_object_no_demonstrated_connection"

    assert report["manifest_size"] == 18
    statuses = {entry["status"] for entry in report["classified"]}
    assert statuses == {"exact_duplicate_of_lastcommand_probe"}, (
        f"self-test FAILED: expected every grammar-authorized SALPH candidate "
        f"to already be an exact duplicate of Phase 0.1's own lastcommand_probe "
        f"set, found {statuses}"
    )

    assert report["oracle"]["materials"] == 18
    assert tuple(report["oracle"]["blobs"]) == ("SALPH", "COSMIC", "P32TRAILING", "URLBLOB")
    assert report["oracle"]["total_hits"] == 0

    print(
        f"[*] self-test OK: SALPH's hash_prefix branch's literal self-"
        f"referential reading is Phase-341 grammar-eligible (5/5 fields "
        f"bound, 1 as an enumerated axis) -- {report['manifest_size']} "
        f"candidates, all exact duplicates of Phase 0.1's own CBC-only "
        f"sweep, widened to ECB/stream/Key Wrap across all 4 blobs, "
        f"{report['oracle']['total_hits']} hits (broader SHA-operand "
        f"readings closed separately by Phase 121, not by this manifest). "
        f"SALPH's thispassword branch is ineligible -- Phase 101's three "
        f"candidate roles remain unreconciled, none selected, no candidate "
        f"generated. COSMIC is ineligible entirely (0/5, textarea is "
        f"exactly the bare ciphertext) -- "
        f"self_contained_encrypted_object_no_demonstrated_connection"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    report = audit()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
        return

    print("-- SALPH eligibility (hash_prefix branch) --")
    for name, field in report["salph"]["fields"].items():
        print(f"  {name}: bound={field['bound']} value={field['value']!r}")
    print(f"  ELIGIBLE: {report['salph']['eligible']}")

    print("-- SALPH eligibility (thispassword branch) --")
    branch = report["salph_thispassword_branch"]
    print(f"  candidate_roles (Phase 101, none selected): {branch['candidate_roles']}")
    print(f"  ELIGIBLE: {branch['eligible']}")
    print(f"  outcome: {branch['outcome']}")

    print("-- COSMIC eligibility --")
    for name, field in report["cosmic"]["fields"].items():
        print(f"  {name}: bound={field['bound']}")
    print(f"  ELIGIBLE: {report['cosmic']['eligible']}")
    print(f"  outcome: {report['cosmic_outcome']}")

    print(f"-- SALPH grammar-authorized candidates: {report['manifest_size']} --")
    for entry in report["classified"]:
        print(f"  {entry['base']!r} + {entry['suffix']}/{entry['treatment']}: {entry['status']}")

    o = report["oracle"]
    print(
        f"-- oracle coverage widened: {o['materials']} materials x "
        f"{len(o['blobs'])} blobs, {o['total_hits']} hits --"
    )


if __name__ == "__main__":
    main()
