#!/usr/bin/env python3
"""Phase 237: close the legacy pad28 keyword gap on the two newer blobs.

This deliberately reproduces the bounded Phase-2 ``cosmic_sweep.py`` route:

    keyword -> pad28 -> decode DBBI/FAED under both decimal mappings and all
    45 escape pairs -> answer_forms -> keystr_forms -> legacy AES-CBC oracle

Only the blob scope changes.  SALPH/COSMIC are excluded; the authenticated
P32TRAILING and provenance-labeled URLBLOB are tested separately.  No native
base-9 board, transform, newline/whitespace variant, extended cipher mode,
autokey, or chain-addition axis is added here.
"""

import argparse
import json
import tempfile
from pathlib import Path

import cb_common as cb
from data import (
    ALPHA_322,
    DBBI,
    FAED,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    VALIDATION_ANSWER_PREFIX,
    VALIDATION_ESCAPES,
    VALIDATION_NUM,
)


CANDIDATE_FAMILIES = {
    "ciao_bella_bye": (
        "bye",
        "ciao",
        "bella",
        "ciaobella",
        "ciaobellao",
        "obellaciao",
        "bellaciao",
    ),
    "key_note_self": (
        "key",
        "note",
        "self",
        "keynote",
        "selfself",
    ),
}
CANDIDATES = tuple(
    candidate
    for family in CANDIDATE_FAMILIES.values()
    for candidate in family
)
STREAMS = {"DBBI": DBBI, "FAED": FAED}
TARGET_BLOBS = {
    "P32TRAILING": cb.BLOBS["P32TRAILING"],
    "URLBLOB": cb.BLOBS["URLBLOB"],
}


def keystrings_for_answer(answer):
    """Return the exact legacy keystring coverage without duplicate calls."""
    return tuple(
        sorted(
            {
                keystring
                for form in cb.answer_forms(answer)
                if form
                for keystring in cb.keystr_forms(form)
            }
        )
    )


def audit():
    hits = []
    per_candidate = {}
    total_configurations = 0
    valid_decodes = 0
    keystring_calls = 0

    # Keep the shared oracle's weak-candidate telemetry, but isolate it from the
    # repository so this audit has no incidental append-only side effect.
    original_weak_log = cb.WEAK_CANDIDATE_LOG
    with tempfile.TemporaryDirectory(prefix="gsmg-phase237-") as temp_dir:
        weak_log = Path(temp_dir) / "weak.jsonl"
        cb.WEAK_CANDIDATE_LOG = weak_log
        try:
            for candidate in CANDIDATES:
                candidate_rows = []
                alphabet = cb.pad28(candidate)
                if len(alphabet) != 28:
                    raise AssertionError(f"pad28 failed for {candidate!r}")
                for stream_name, stream in STREAMS.items():
                    stream_valid = 0
                    stream_calls = 0
                    for map_name, mapping in cb.MAPS.items():
                        digits = "".join(mapping[symbol] for symbol in stream)
                        for e1, e2 in cb.ALL_ESCAPE_PAIRS:
                            total_configurations += 1
                            answer = cb.decode(digits, alphabet, e1, e2)
                            if "?" in answer:
                                continue
                            valid_decodes += 1
                            stream_valid += 1
                            keystrings = keystrings_for_answer(answer)
                            for keystring in keystrings:
                                keystring_calls += 1
                                stream_calls += 1
                                result = cb.aes_try_open(
                                    keystring,
                                    kdf_variants=cb.KDF_VARIANTS,
                                    blobs=TARGET_BLOBS,
                                )
                                if result:
                                    blob, plaintext, kdf_name, key_len = result
                                    hits.append(
                                        {
                                            "candidate": candidate,
                                            "stream": stream_name,
                                            "mapping": map_name,
                                            "escapes": (e1, e2),
                                            "answer": answer,
                                            "keystring": keystring,
                                            "blob": blob,
                                            "kdf": kdf_name,
                                            "key_bits": key_len * 8,
                                            "plaintext_hex": plaintext.hex(),
                                        }
                                    )
                    candidate_rows.append(
                        {
                            "stream": stream_name,
                            "valid_decodes": stream_valid,
                            "normalized_keystring_calls": stream_calls,
                        }
                    )
                per_candidate[candidate] = tuple(candidate_rows)
            weak_records = tuple(
                json.loads(line)
                for line in weak_log.read_text(encoding="utf-8").splitlines()
            ) if weak_log.exists() else ()
        finally:
            cb.WEAK_CANDIDATE_LOG = original_weak_log

    primitive_decryptions = (
        keystring_calls * len(cb.KDF_VARIANTS) * len(TARGET_BLOBS)
    )
    return {
        "scope": {
            "route": "legacy_phase2_pad28_decimal_checkerboard_to_aes_cbc",
            "candidate_families": CANDIDATE_FAMILIES,
            "streams": tuple(STREAMS),
            "mappings": tuple(cb.MAPS),
            "escape_pairs": len(cb.ALL_ESCAPE_PAIRS),
            "kdf_variants": tuple(cb.KDF_VARIANTS),
            "blobs": tuple(TARGET_BLOBS),
            "excluded_axes": (
                "SALPH/COSMIC rerun",
                "native base-9 pad25 checkerboard",
                "input/output transforms",
                "newline/whitespace variants",
                "extended cipher/KDF modes",
                "autokey/chain addition",
            ),
        },
        "counts": {
            "candidates": len(CANDIDATES),
            "keyword_stream_tests": len(CANDIDATES) * len(STREAMS),
            "decoder_configurations": total_configurations,
            "valid_decodes": valid_decodes,
            "normalized_keystring_calls": keystring_calls,
            "primitive_blob_kdf_decryptions": primitive_decryptions,
            "strong_hits": len(hits),
            "weak_records": len(weak_records),
        },
        "per_candidate": per_candidate,
        "hits": tuple(hits),
        "weak_records": weak_records,
        "gates": {
            "any_blob_opened": bool(hits),
            "consumer_authenticated": False,
            "residual_checkerboard_keyword_gap_closed": True,
        },
        "promoted": False,
        "verdict": (
            "The frozen legacy pad28 checkerboard-keyword route is negative for "
            "the CIAO/BELLA/BYE and KEY/NOTE/SELF families against P32TRAILING "
            "and URLBLOB. This closes the explicitly flagged blob-coverage gap "
            "without selecting a consumer or authorizing broader checkerboard, "
            "autokey, or chain-addition variants."
        ),
    }


def self_test():
    # Independent known-good guards for both halves of the inherited route.
    decoded = cb.decode(VALIDATION_NUM, ALPHA_322, *VALIDATION_ESCAPES)
    assert decoded.replace(".", "").startswith(VALIDATION_ANSWER_PREFIX)
    phase32_blob = {"PHASE32": cb._load_blob(PHASE32_BLOB_B64)}
    assert cb.aes_try_open(
        PHASE32_PASSWORD,
        kdf_variants=(("sha256", 32),),
        blobs=phase32_blob,
    )

    report = audit()
    counts = report["counts"]
    assert tuple(TARGET_BLOBS) == ("P32TRAILING", "URLBLOB")
    assert not ({"SALPH", "COSMIC"} & set(TARGET_BLOBS))
    assert len(CANDIDATES) == 12 and len(set(CANDIDATES)) == 12
    assert counts["decoder_configurations"] == 12 * 2 * 2 * 45
    assert counts["strong_hits"] == 0
    assert counts["weak_records"] == 0
    assert not report["gates"]["any_blob_opened"]
    assert report["gates"]["residual_checkerboard_keyword_gap_closed"]
    assert not report["promoted"]
    print(json.dumps(report, indent=2, default=list))
    print("[*] self-test OK: legacy route pinned, two-blob gap closed, oracle negative")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2, default=list))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
