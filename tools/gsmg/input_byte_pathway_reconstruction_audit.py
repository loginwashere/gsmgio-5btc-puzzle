#!/usr/bin/env python3
"""Input-byte pathway reconstruction audit (Post-Phase-340 Seed 7).

Executes the "genuinely-unrun" item recorded in
doc/GSMG_BRAINSTORM_BACKLOG_LEDGER.md ("Post-Phase-340 Seed 7 -- input-byte
pathway reconstruction"), scoped down from that entry's open-ended concept
list to only the byte-pathway hypotheses this project has actual evidence
for, per the calibration rule discussed 2026-08-23: retain a pathway only if
it either (a) reproduces a real, previously-demonstrated false-negative
class in this project, or (b) is explicitly evidenced by puzzle-era
code/instructions. Concretely:

  - Raw SHA-256 digest BYTES (not the 64-char hex string) as password
    material. Justified by doc/GSMG_COSMIC_RAW_DIGEST_CHECKPOINT_AUDIT.md:
    the community COSMIC construction was falsely rejected when tested as
    hex text and only reproduced when the raw 32 digest bytes were fed
    directly to the KDF. Raw double-SHA-256 (digest of the raw digest
    bytes) is included as the natural symmetric extension of the same class.
  - Trailing space, LF, and CRLF appended before hashing. Justified by
    FINDINGS.md Phase 163: the creator's own recommended hash tool
    (passwordsgenerator.net/sha256-hash-generator/, linked by the creator
    personally in the Telegram export) strips a literal "\\r" from its input
    textarea and nothing else -- a stray trailing space or a terminal Enter
    keypress becomes part of the hashed string with no warning. These three
    forms were available in cb_common.keystr_forms() but were deliberately
    left OFF in the original P0A/P1A sentinel run (FINDINGS.md Phase 290)
    to keep that run's declared scope minimal; adding them now for the same
    frozen candidate set is a scope *widening* of an already-justified
    axis, not a new one.

Explicitly EXCLUDED, and why: UTF-16 (LE/BE, with/without BOM), Latin-1/
CP1252, leading whitespace, HTML-entity decoding, and echo-vs-printf as a
distinct axis. None of these has any puzzle-era evidence in this project --
grepping FINDINGS.md and doc/GSMG_PUZZLE.md for "UTF-16" returns zero hits,
despite that exact possibility being named in the Seed 7 brainstorm entry's
"concept only" scope. Adding them without evidence would be exactly the
unbounded "try every encoding" sweep this audit exists to avoid. Latin-1 is
additionally moot here on its own terms: every one of the 42 candidate
strings below is pure ASCII, where Latin-1/CP1252/UTF-8 are byte-identical.

Candidate universe: the frozen 42-item P0A/P1A sentinel manifest (same
candidates, same order, same digest as p1a_sentinel_backfill.py) -- no new
candidate text is introduced here. Only 2 of the ~20 forms this script
tests per candidate were already run against the oracle (Phase 290/335):
the bare literal and its single hex SHA-256 digest. Every other form here
is newly tested. Full oracle (CBC + ECB + stream + AES Key Wrap), all 4
tracked blobs, per this project's standard "current full oracle" convention.
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
    ECB_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    keystr_forms,
)
from extended_cipher_recheck import candidate_list_digest  # noqa: E402
from p1a_sentinel_backfill import eligible_candidates  # noqa: E402

EXPECTED_CANDIDATE_COUNT = 42
EXPECTED_CANDIDATE_DIGEST = "51afdf5ce033500a"  # same manifest as Phase 290/335
EXPECTED_NEW_FORMS_PER_CANDIDATE = 18
EXPECTED_NEW_MATERIALS = EXPECTED_CANDIDATE_COUNT * EXPECTED_NEW_FORMS_PER_CANDIDATE

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS),
)


def already_tested_forms(text):
    """The exact 2 forms Phase 290/335 already ran for this candidate."""
    literal = text
    digest_hex = hashlib.sha256(text.encode()).hexdigest()
    return {literal, digest_hex}


def new_material_forms(text):
    """New byte-pathway forms for one candidate: (kind, bytes) pairs.

    Built from 4 bases (literal, +space, +LF, +CRLF); for each base, the
    hex-SHA and double-hex-SHA text forms plus the raw-digest-bytes and
    raw-double-digest-bytes forms. Already-tested forms (bare literal, bare
    hex-SHA) are excluded here so counts reflect genuinely new attempts."""
    already = already_tested_forms(text)
    bases = (text, text + " ", text + "\n", text + "\r\n")
    base_labels = ("base", "trailing_space", "lf", "crlf")

    out = []
    for base, label in zip(bases, base_labels):
        h1 = hashlib.sha256(base.encode()).hexdigest()
        h2 = hashlib.sha256(h1.encode()).hexdigest()
        d1 = hashlib.sha256(base.encode()).digest()
        d2 = hashlib.sha256(d1).digest()

        if base not in already:
            out.append((f"{label}/literal", base.encode()))
        if h1 not in already:
            out.append((f"{label}/sha256_hex", h1.encode()))
        out.append((f"{label}/sha256_hex_hex", h2.encode()))
        out.append((f"{label}/sha256_raw_bytes", d1))
        out.append((f"{label}/sha256_raw_bytes_raw_bytes", d2))
    return out


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]

    attempts = []
    hits = []
    for model, label, text in candidates:
        for form_kind, material in new_material_forms(text):
            for family_name, oracle_fn, variants in ORACLE_FAMILIES:
                result = oracle_fn(material, kdf_variants=variants, blobs=active_blobs)
                attempts.append({
                    "model": model,
                    "label": label,
                    "form": form_kind,
                    "family": family_name,
                })
                if result:
                    tag, body, kdf_label, key_len = result
                    hits.append({
                        "model": model,
                        "label": label,
                        "form": form_kind,
                        "family": family_name,
                        "blob": tag,
                        "kdf": f"{kdf_label}/aes{key_len * 8}",
                        "plaintext_hex": body.hex(),
                    })

    total_variants = sum(len(v) for _, _, v in ORACLE_FAMILIES)
    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(texts),
        "new_materials": len(attempts) // len(ORACLE_FAMILIES),
        "blobs": tuple(active_blobs),
        "oracle_families": [name for name, _, _ in ORACLE_FAMILIES],
        "total_variant_configs": total_variants,
        "effective_decrypt_attempts": sum(
            len(new_material_forms(text)) * len(variants) * len(active_blobs)
            for text in texts
            for _, _, variants in ORACLE_FAMILIES
        ),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]
    assert len(candidates) == EXPECTED_CANDIDATE_COUNT
    assert candidate_list_digest(texts) == EXPECTED_CANDIDATE_DIGEST
    assert len(set(texts)) == EXPECTED_CANDIDATE_COUNT, "duplicate candidate text found"

    forms0 = new_material_forms(texts[0])
    assert len(forms0) == EXPECTED_NEW_FORMS_PER_CANDIDATE, len(forms0)
    # Every candidate string in this manifest is pure ASCII, so Latin-1/
    # CP1252 would be byte-identical to UTF-8 here -- confirms the doc
    # comment's claim, not just asserts it.
    for text in texts:
        assert all(ord(ch) < 128 for ch in text), f"non-ASCII candidate: {text!r}"
    # Already-tested forms (Phase 290/335: bare literal, bare hex-SHA) are
    # excluded both by label and by exact material bytes.
    already_bytes = {t.encode() for t in already_tested_forms(texts[0])}
    form_labels = {kind for kind, _ in forms0}
    assert "base/literal" not in form_labels
    assert "base/sha256_hex" not in form_labels
    for _, material in forms0:
        assert material not in already_bytes
    assert tuple(BLOBS) == ("SALPH", "COSMIC", "P32TRAILING", "URLBLOB")
    total_new = sum(len(new_material_forms(t)) for t in texts)
    assert total_new == EXPECTED_NEW_MATERIALS, total_new
    print(
        f"[*] self-test OK: {EXPECTED_CANDIDATE_COUNT} candidates (digest "
        f"{EXPECTED_CANDIDATE_DIGEST}), {EXPECTED_NEW_FORMS_PER_CANDIDATE} new "
        f"forms/candidate, {EXPECTED_NEW_MATERIALS} new materials planned"
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
