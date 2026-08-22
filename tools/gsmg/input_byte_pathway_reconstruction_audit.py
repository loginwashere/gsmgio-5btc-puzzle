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
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_key_wrap,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    derive_kek,
    keystr_forms,
)
from extended_cipher_recheck import candidate_list_digest  # noqa: E402
from p1a_sentinel_backfill import eligible_candidates  # noqa: E402

EXPECTED_CANDIDATE_COUNT = 42
EXPECTED_CANDIDATE_DIGEST = "51afdf5ce033500a"  # same manifest as Phase 290/335
EXPECTED_NEW_FORMS_PER_CANDIDATE = 18
EXPECTED_NEW_MATERIALS = EXPECTED_CANDIDATE_COUNT * EXPECTED_NEW_FORMS_PER_CANDIDATE

# Corrected 2026-08-23 (same-day review): the original run used bare
# KDF_VARIANTS for CBC, silently omitting the project's established
# full-oracle convention of KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS
# (AES-192-CBC, 3DES-CBC at 3 key sizes, PBKDF2/CBC) -- 18 configurations.
# This constant is now the correct, complete CBC set for any *fresh* full
# run of this script. The 18 EXTENDED_CIPHER_VARIANTS configurations
# already missing from the completed Phase 378 run were instead covered by
# a separate delta (see run_cbc_extended_delta below) rather than
# repeating the 6-variant portion Phase 378 already ran and confirmed
# negative.
CBC_KDF_VARIANTS = KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS

# Key Wrap's oracle function has a materially different contract from the
# other three families: it returns a *list* of (tag, wrap_kind, kdf_label,
# key_len, unwrapped_bytes) 5-tuples -- every successful unwrap, not one
# best candidate -- instead of a single 4-tuple or None. It also tries 4
# distinct unwrap forms per (KDF variant, blob) pair (RFC 3394 default IV,
# RFC 3394 OpenSSL custom IV, RFC 5649 default IV, RFC 5649 OpenSSL custom
# IV), so counting it as "1 configuration = 1 attempt" the way CBC/ECB/
# stream are counted undercounts its real cryptographic work by 4x. Both
# facts are handled explicitly in run() below rather than folded into the
# uniform (name, fn, variants) family shape the other three share.
KEYWRAP_FORMS_PER_CONFIG = 4

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, CBC_KDF_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, KEYWRAP_FORMS_PER_CONFIG),
)

# The 18-configuration CBC delta Phase 378 omitted, run on its own against
# the same frozen 756 materials without repeating the 6-variant KDF_VARIANTS
# portion Phase 378 already completed and confirmed negative.
CBC_EXTENDED_DELTA_FAMILIES = (
    ("cbc_extended_delta", aes_try_open_bytes, EXTENDED_CIPHER_VARIANTS, 1),
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


def run(blobs=None, families=None):
    """`families` defaults to ORACLE_FAMILIES (the full, corrected oracle).
    Pass CBC_EXTENDED_DELTA_FAMILIES to run only the 18-configuration CBC
    delta Phase 378 omitted, without repeating already-completed work."""
    active_blobs = BLOBS if blobs is None else blobs
    active_families = ORACLE_FAMILIES if families is None else families
    candidates = eligible_candidates()
    texts = [c[2] for c in candidates]

    variant_config_count = 0
    effective_attempts = 0
    hits = []
    for model, label, text in candidates:
        for form_kind, material in new_material_forms(text):
            for family_name, oracle_fn, variants, forms_per_config in active_families:
                variant_config_count += 1
                effective_attempts += len(variants) * len(active_blobs) * forms_per_config
                if family_name.startswith("keywrap"):
                    # aes_keywrap_try_open_bytes returns a LIST of 5-tuples
                    # (tag, wrap_kind, kdf_label, key_len, unwrapped), one
                    # per successful unwrap -- not a single 4-tuple/None
                    # like the other three families.
                    for tag, wrap_kind, kdf_label, key_len, unwrapped in oracle_fn(
                        material, kdf_variants=variants, blobs=active_blobs,
                    ):
                        hits.append({
                            "model": model,
                            "label": label,
                            "form": form_kind,
                            "family": family_name,
                            "blob": tag,
                            "kdf": f"{kdf_label}/aes{key_len * 8}/{wrap_kind}",
                            "plaintext_hex": unwrapped.hex(),
                        })
                else:
                    result = oracle_fn(material, kdf_variants=variants, blobs=active_blobs)
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

    new_materials = variant_config_count // len(active_families)
    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(texts),
        "new_materials": new_materials,
        "blobs": tuple(active_blobs),
        "oracle_families": [name for name, _, _, _ in active_families],
        "total_variant_configs": sum(len(v) for _, _, v, _ in active_families),
        "effective_decrypt_attempts": effective_attempts,
        "hits": hits,
        "total_hits": len(hits),
    }


def run_cbc_extended_delta(blobs=None):
    """The 18-configuration CBC delta Phase 378 omitted (see
    CBC_EXTENDED_DELTA_FAMILIES): AES-192-CBC, 3DES-CBC (3 key sizes), and
    PBKDF2/CBC, against the same frozen 756 materials. Does not repeat the
    6-variant KDF_VARIANTS portion of CBC, ECB, stream, or Key Wrap, all of
    which Phase 378 already ran and confirmed negative."""
    return run(blobs=blobs, families=CBC_EXTENDED_DELTA_FAMILIES)


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

    # Corrected 2026-08-23: the full oracle's CBC leg is KDF_VARIANTS (6) +
    # EXTENDED_CIPHER_VARIANTS (18) = 24, matching this project's
    # established full-oracle convention (not the bare 6 Phase 378 used).
    assert len(CBC_KDF_VARIANTS) == 24, len(CBC_KDF_VARIANTS)
    total_full_configs = sum(len(v) for _, _, v, _ in ORACLE_FAMILIES)
    assert total_full_configs == 84, total_full_configs  # 24+12+36+12
    delta_configs = sum(len(v) for _, _, v, _ in CBC_EXTENDED_DELTA_FAMILIES)
    assert delta_configs == 18, delta_configs
    assert EXPECTED_NEW_MATERIALS * delta_configs * 4 == 54432

    _self_test_keywrap_hit_handling()

    print(
        f"[*] self-test OK: {EXPECTED_CANDIDATE_COUNT} candidates (digest "
        f"{EXPECTED_CANDIDATE_DIGEST}), {EXPECTED_NEW_FORMS_PER_CANDIDATE} new "
        f"forms/candidate, {EXPECTED_NEW_MATERIALS} new materials planned, "
        f"{total_full_configs} full-oracle configs (24 CBC + 12 ECB + 36 "
        f"stream + 12 keywrap), {delta_configs}-config CBC-extended delta "
        f"verified, Key Wrap 5-tuple-list hit handling verified"
    )


def _self_test_keywrap_hit_handling():
    """Confirms run()'s Key Wrap branch actually produces a correctly
    shaped hit from a planted positive, rather than merely confirming (as
    Phase 378's zero-hit run did) that an empty list doesn't crash. Mirrors
    cb_common._self_test_keywrap's fixture construction."""
    # Must match a form new_material_forms() actually produces -- the bare
    # literal is one of the 2 already-tested forms it deliberately excludes
    # (see already_tested_forms), so the KEK is derived from the
    # "trailing_space/literal" form (candidate text + " ") instead, which
    # run() really does try.
    candidate_text = eligible_candidates()[0][2]
    salt = b"01234567"
    variant = KEY_WRAP_KDF_VARIANTS[0]
    kdf_kind, kdf_param, key_len = variant
    kek = derive_kek(kdf_kind, kdf_param, salt, (candidate_text + " ").encode(), key_len)
    key_material = b"0123456789ABCDEF"  # 16 bytes: minimum RFC 3394 accepts
    wrapped = aes_key_wrap(kek, key_material)

    synth_family = (("keywrap", aes_keywrap_try_open_bytes, [variant], KEYWRAP_FORMS_PER_CONFIG),)
    report = run(blobs={"SYNTH": (salt, wrapped)}, families=synth_family)
    assert report["total_hits"] >= 1, "planted Key Wrap hit was not recorded"
    hit = report["hits"][0]
    assert hit["blob"] == "SYNTH"
    assert hit["plaintext_hex"] == key_material.hex()
    assert "rfc3394-default" in hit["kdf"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--delta", action="store_true",
        help="run only the 18-config CBC-extended delta, not the full oracle",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.delta:
        report = run_cbc_extended_delta()
    elif args.run:
        report = run()
    else:
        report = {"note": "pass --run (full oracle) or --delta (CBC-extended only)"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
