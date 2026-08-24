#!/usr/bin/env python3
"""Phase 391: bounded numeric/temporal material against P32TRAILING.

Tests only numbers and dates this project has already authenticated and
named as milestones -- no open-ended date/number generation. Two closed
sources feed the manifest, each cited to the exact phase/constant it comes
from:

  - Telegram milestone message IDs and their dates, from Phase 386/387's
    own constants (`JRK_QUOTE_MESSAGE_ID`/`JRK_QUOTE_DATE`,
    `ORIGIN_MESSAGE_ID`/`ORIGIN_DATE`, `NAMED_RESULT_MESSAGE_ID`,
    `ORIGIN_MESSAGE_ID` for message 66722's 2026-07-13 KMODEST
    derivation) plus message 61439 (the media-shortlist caption, FINDINGS
    Phase 156/386 provenance section).
  - Bitcoin block heights and block times, from Phase 383/390's
    cross-source-verified transaction cache (the two creator-signed
    self-spends' confirmation heights and epoch timestamps).
  - The Wayback/HTTP capture dates from FINDINGS.md's `gsmg.io/puzzle`
    provenance section: the archived HTTP `Last-Modified` header
    (2020-10-21) and two Wayback capture dates (2020-11-12, 2025-05-20).

Each number is tried in four forms only, per the declared scope: decimal,
lowercase hex (no prefix), zero-padded decimal, and zero-padded hex (pad
width is the longest value's own natural width within its category --
not an arbitrary fixed width). Each date is tried as its own literal ISO
form(s) already used in this project's code/docs, plus (for the one HTTP
date) the literal RFC 1123 string itself. No arbitrary combination,
concatenation, arithmetic, or derived offset is tested.

Scoped to P32TRAILING only, per the declared question -- not a re-run of
the four-blob sweep Phase 389/390 already performed.
"""

import argparse
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
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
)

TARGET_BLOB = {"P32TRAILING": BLOBS["P32TRAILING"]}

CBC_KDF_VARIANTS = KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS
KEYWRAP_FORMS_PER_CONFIG = 4

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, CBC_KDF_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, KEYWRAP_FORMS_PER_CONFIG),
)

# (category, label, value) -- every value cited above.
NUMERIC_FACTS = (
    ("telegram_message_id", "jrk_quote_8774", 8774),
    ("telegram_message_id", "sycorax_origin_43248", 43248),
    ("telegram_message_id", "result_naming_43671", 43671),
    ("telegram_message_id", "media_shortlist_caption_61439", 61439),
    ("telegram_message_id", "kmodest_derivation_66722", 66722),
    ("block_height", "self_spend_2020_630001", 630001),
    ("block_height", "self_spend_2024_840725", 840725),
    ("block_time_epoch", "self_spend_2020_epoch_1589227370", 1589227370),
    ("block_time_epoch", "self_spend_2024_epoch_1713995247", 1713995247),
    ("date_yyyymmdd", "jrk_quote_date_20230803", 20230803),
    ("date_yyyymmdd", "sycorax_origin_date_20250612", 20250612),
    ("date_yyyymmdd", "kmodest_derivation_date_20260713", 20260713),
    ("date_yyyymmdd", "puzzle_image_http_last_modified_20201021", 20201021),
    ("date_yyyymmdd", "wayback_capture_20201112", 20201112),
    ("date_yyyymmdd", "wayback_capture_20250520", 20250520),
)

# (label, literal ISO/RFC-1123 string) -- reproduced exactly as already
# recorded, not reformatted.
DATE_LITERAL_FACTS = (
    ("jrk_quote_datetime", "2023-08-03T22:51:33"),
    ("jrk_quote_date_only", "2023-08-03"),
    ("sycorax_origin_datetime", "2025-06-12T03:30:31"),
    ("sycorax_origin_date_only", "2025-06-12"),
    ("kmodest_derivation_date_only", "2026-07-13"),
    ("wayback_capture_date_only_1", "2020-11-12"),
    ("wayback_capture_date_only_2", "2025-05-20"),
    ("puzzle_image_http_last_modified_iso", "2020-10-21"),
    ("puzzle_image_http_last_modified_rfc1123", "Wed, 21 Oct 2020 15:52:41 GMT"),
)


def _category_pad_widths():
    dec_width = {}
    hex_width = {}
    for category, _label, value in NUMERIC_FACTS:
        dec_width[category] = max(dec_width.get(category, 0), len(str(value)))
        hex_width[category] = max(hex_width.get(category, 0), len(format(value, "x")))
    return dec_width, hex_width


def numeric_materials():
    dec_width, hex_width = _category_pad_widths()
    out = []
    for category, label, value in NUMERIC_FACTS:
        decimal = str(value)
        hexform = format(value, "x")
        zdec = decimal.zfill(dec_width[category])
        zhex = hexform.zfill(hex_width[category])
        for form_label, text in (
            ("decimal", decimal),
            ("hex", hexform),
            ("zero_padded_decimal", zdec),
            ("zero_padded_hex", zhex),
        ):
            out.append((category, label, form_label, text.encode()))
    return out


def date_materials():
    return [(label, "iso_or_rfc1123", text.encode()) for label, text in DATE_LITERAL_FACTS]


def run_oracle(blobs=None, families=None):
    active_blobs = TARGET_BLOB if blobs is None else blobs
    active_families = ORACLE_FAMILIES if families is None else families
    materials = [
        (category, label, form_label, material)
        for category, label, form_label, material in numeric_materials()
    ] + [
        ("date", label, form_label, material)
        for label, form_label, material in date_materials()
    ]

    total_attempts = 0
    hits = []
    for category, label, form_label, material in materials:
        for family_name, oracle_fn, variants, forms_per_config in active_families:
            total_attempts += len(variants) * len(active_blobs) * forms_per_config
            if family_name == "keywrap":
                for tag, wrap_kind, kdf_label, key_len, unwrapped in oracle_fn(
                    material, kdf_variants=variants, blobs=active_blobs,
                ):
                    hits.append({
                        "category": category, "label": label, "form": form_label,
                        "family": family_name, "blob": tag,
                        "kdf": f"{kdf_label}/aes{key_len * 8}/{wrap_kind}",
                        "plaintext_hex": unwrapped.hex(),
                    })
            else:
                result = oracle_fn(material, kdf_variants=variants, blobs=active_blobs)
                if result:
                    tag, body, kdf_label, key_len = result
                    hits.append({
                        "category": category, "label": label, "form": form_label,
                        "family": family_name, "blob": tag,
                        "kdf": f"{kdf_label}/aes{key_len * 8}",
                        "plaintext_hex": body.hex(),
                    })

    return {
        "material_count": len(materials),
        "numeric_fact_count": len(NUMERIC_FACTS),
        "date_fact_count": len(DATE_LITERAL_FACTS),
        "blobs": tuple(active_blobs),
        "oracle_families": [name for name, _, _, _ in active_families],
        "total_variant_configs": sum(len(v) for _, _, v, _ in active_families),
        "effective_decrypt_attempts": total_attempts,
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    materials = numeric_materials()
    assert len(materials) == 15 * 4 == 60, len(materials)
    dates = date_materials()
    assert len(dates) == 9, len(dates)

    # Spot-check padding: telegram_message_id widths are 4 (8774) vs 5
    # (43248/43671/61439/66722), so 8774 is the only value padded.
    m = {(c, l, f): t for c, l, f, t in materials}
    assert m[("telegram_message_id", "jrk_quote_8774", "zero_padded_decimal")] == b"08774"
    assert m[("telegram_message_id", "sycorax_origin_43248", "zero_padded_decimal")] == b"43248"
    assert m[("telegram_message_id", "jrk_quote_8774", "decimal")] == b"8774"
    assert m[("telegram_message_id", "jrk_quote_8774", "hex")] == b"2246"
    assert m[("block_height", "self_spend_2020_630001", "hex")] == b"99cf1"

    result = run_oracle()
    assert result["material_count"] == 60 + 9 == 69
    assert result["blobs"] == ("P32TRAILING",)
    assert result["total_hits"] == 0, result["hits"]
    print(
        "[*] self-test OK: 69 numeric/date materials (15 numbers x 4 forms + "
        "9 literal date/HTTP-date forms), 0 hits against P32TRAILING"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(run_oracle(), indent=2))


if __name__ == "__main__":
    main()
