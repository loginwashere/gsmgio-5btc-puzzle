#!/usr/bin/env python3
"""P1A: bounded statistical-gate sentinel backfill.

Executes P1A from
doc/Brainstorms/2026-08-15 - Passphrase Oracle False-Negative Surface.md,
against the manifest built in
doc/Brainstorms/2026-08-15 - Canonical Sentinel Inventory (P0A).md.

P0A identified 40 strings/digests, across three of the sixteen fresh
DBBI/FAED brainstorm models (arithmetic/range coding, continued fractions,
authenticated-string selectors), that are fully materialized, deterministic,
free of any unauthored choice, and had never reached the AES blob oracle --
only self-referential equality checks against their own source data, which is
a materially weaker test.

Per that document's own "Next step" and this scope's Lane B declaration, the
material treatment is fixed in advance to exactly two forms per candidate:
the literal string, and the hex SHA-256 digest of that literal string (the
project's standard "hash as password" hypothesis, per cb_common.keystr_forms'
doctring). No case-folding, no alpha-only stripping, no additional KDF/cipher
family beyond cb_common's default CBC oracle -- adding any of those now would
be exactly the kind of after-the-fact scope expansion Lane B's five criteria
exist to prevent. Every attempt is counted; there is no adaptive follow-up
regardless of outcome, per the stop-rule policy both documents share.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    KDF_VARIANTS,
    aes_try_open_bytes,
)
from extended_cipher_recheck import candidate_list_digest  # noqa: E402

import dbbi_faed_arithmetic_model_audit as _m9  # noqa: E402
import dbbi_faed_authenticated_selector_audit as _m16  # noqa: E402
import dbbi_faed_continued_fraction_audit as _m15  # noqa: E402
import dbbi_faed_fsm_audit as _m11  # noqa: E402

# Phase 335: model 11 (81+10 FSM) added its 2 candidates once
# `dbbi_faed_fsm_audit.py` was fixed to expose the full output string
# (previously only a 160-char prefix was retained) -- the "report-plumbing
# fix" P0A/Phase 290 explicitly deferred. Count/digest/attempts below cover
# all 42; the original 40 (Phase 290) are unchanged candidates, re-run here
# alongside the 2 new ones rather than split into a second script, since the
# combined run is still trivially cheap (84 passphrase attempts).
EXPECTED_CANDIDATE_COUNT = 42
EXPECTED_CANDIDATE_DIGEST = "51afdf5ce033500a"
EXPECTED_FORM_COUNT = 2
EXPECTED_PASSPHRASE_ATTEMPTS = 84


def eligible_candidates():
    """The frozen P0A manifest: (model, label, text) in report order.

    Every value here is read directly off each audit script's existing
    report object -- no new transform is run and no interpretive choice
    (index, alphabet, gap rule) is made here."""
    out = []

    r9 = _m9.audit()
    for row in r9["rows"]:
        source = "DBBI" if row["output_length"] == 91 else "FAED"
        out.append((
            "model9_arithmetic",
            f"{source}/{row['model']}/decoded_text",
            row["decoded_text"],
        ))
        out.append((
            "model9_arithmetic",
            f"{source}/{row['model']}/canonical_codeword",
            row["canonical_codeword"],
        ))

    r15 = _m15.audit()
    for row in r15["rows"]:
        out.append((
            "model15_continued_fraction",
            f"{row['source']}/{row['map']}/numerator_sha256",
            row["numerator_sha256"],
        ))
        out.append((
            "model15_continued_fraction",
            f"{row['source']}/{row['map']}/denominator_sha256",
            row["denominator_sha256"],
        ))

    r16 = _m16.audit()
    for row in r16["rows"]:
        out.append((
            "model16_authenticated_selector",
            f"{row['source']}/{row['target']}/{row['mode']}",
            row["output"],
        ))

    # Phase 335: model 11's 2 candidates -- the full 570-symbol FSM output
    # string and its 10-symbol trailer -- both already fully computed by
    # `audit()`, now exposed in the report (see dbbi_faed_fsm_audit.py's
    # `output_text` field). No new transform, same single canonical
    # serialization the script's own docstring commits to.
    r11 = _m11.audit()
    out.append(("model11_fsm", "output_text", r11["output_text"]))
    out.append(("model11_fsm", "trailer_text", r11["trailer_text"]))

    return out


def passphrase_forms(text):
    """Exactly the two forms declared in advance: literal, and hex SHA-256
    of the literal. Order matters for the attempt log, not for the result."""
    literal = text
    digest = hashlib.sha256(text.encode()).hexdigest()
    return (literal, digest)


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]

    attempts = []
    hits = []
    for model, label, text in candidates:
        for form_kind, form_text in zip(("literal", "sha256"), passphrase_forms(text)):
            result = aes_try_open_bytes(form_text.encode(), blobs=active_blobs)
            attempts.append({
                "model": model,
                "label": label,
                "form": form_kind,
            })
            if result:
                tag, body, kdf_label, key_len = result
                hits.append({
                    "model": model,
                    "label": label,
                    "form": form_kind,
                    "blob": tag,
                    "kdf": f"{kdf_label}/aes{key_len * 8}",
                    "plaintext_hex": body.hex(),
                })

    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(texts),
        "form_count": 2,
        "blobs": tuple(active_blobs),
        "kdf_variants": len(KDF_VARIANTS),
        "passphrase_attempts": len(attempts),
        "effective_decrypt_attempts": len(attempts) * len(KDF_VARIANTS) * len(active_blobs),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]
    assert len(candidates) == EXPECTED_CANDIDATE_COUNT
    assert candidate_list_digest(texts) == EXPECTED_CANDIDATE_DIGEST
    assert len(set(texts)) == EXPECTED_CANDIDATE_COUNT, "duplicate candidate text found"
    assert len(passphrase_forms(texts[0])) == EXPECTED_FORM_COUNT
    assert EXPECTED_CANDIDATE_COUNT * EXPECTED_FORM_COUNT == EXPECTED_PASSPHRASE_ATTEMPTS
    assert tuple(BLOBS) == ("SALPH", "COSMIC", "P32TRAILING", "URLBLOB")
    print(
        f"[*] self-test OK: {EXPECTED_CANDIDATE_COUNT} P0A candidates, "
        f"digest {EXPECTED_CANDIDATE_DIGEST}, "
        f"{EXPECTED_PASSPHRASE_ATTEMPTS} passphrase attempts planned"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else {"note": "pass --run to execute against the oracle"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
