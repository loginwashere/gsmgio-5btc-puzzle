#!/usr/bin/env python3
"""Audit the non-letter symbols in the Stage-1 icon rebus.

The visible word layer was closed in Phase 71.  This follow-up keeps the
creator-authored PNGs separate from the community-made four-row montage and
asks a narrower question: do the locks, +/- signs, colors, and banking/crypto
icons contain a second message?

The symbols form three natural contrasts (closed/open lock, plus/minus, and
banking/crypto).  Together with the red/blue split they strongly illustrate
the song line "opposites attract" and cue pieces from opposite sides to be
joined.  The semantic matching is not a second textual matching, however:
the banking/crypto and closed/open pairs must be crossed to obtain WARNING
and CRYPTOLOGIC.  No deterministic residual string remains.

``--run`` performs a bounded four-blob CBC/ECB/stream/Key-Wrap and literal
raw-key check of only the exact lyric and natural names of those visible
contrasts.  It is intentionally not a new broad wordlist sweep.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    OPENSSL_MENU_GAP_CIPHER_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    answer_forms,
    keystr_forms,
)
from extended_cipher_recheck import candidate_list_digest  # noqa: E402
from literal_raw_key_material_audit import raw_key_forms, sweep as raw_key_sweep  # noqa: E402

ICON_DIR = SCRIPT_DIR.parents[1] / "doc" / "img"

ICON_FACTS = {
    "gsmg_icon_black_banking_war.png": ((78, 70), "RGBA", 996, "907b489f6e77a828"),
    "gsmg_icon_blue_ca.png": ((78, 70), "RGB", 627, "e59d42e85997d395"),
    "gsmg_icon_blue_dig_i.png": ((77, 70), "RGBA", 1030, "a6889a2e090d3292"),
    "gsmg_icon_blue_lock_lo.png": ((82, 70), "RGBA", 783, "60b01e5bc4181ed4"),
    "gsmg_icon_red_crypto_gic.png": ((79, 70), "RGBA", 1642, "8aad87b987ee7d8e"),
    "gsmg_icon_red_n_you.png": ((80, 70), "RGB", 863, "89a81a1b30cc399c"),
    "gsmg_icon_red_open_lock_n_ing.png": ((82, 70), "RGBA", 963, "ea1cd545040c051a"),
    "gsmg_icon_red_t.png": ((79, 70), "RGBA", 506, "86fb2eff01d3b4f2"),
}

BLUE = (63, 72, 204)
RED = (237, 28, 36)

WORD_MATCHING = {
    "bank_war": ("openlock_n_ing", "WARNING"),
    "lock_lo": ("crypto_gic", "CRYPTOLOGIC"),
    "ca": ("n_you", "CANYOU"),
    "dig_i_plus": ("t_minus", "DIGIT"),
}

SYMBOL_MATCHING = {
    "bank_war": ("crypto_gic", "banking/crypto"),
    "lock_lo": ("openlock_n_ing", "closed/open lock"),
    "dig_i_plus": ("t_minus", "plus/minus"),
}

# Exact lyric plus only the natural labels of motifs actually visible in the
# eight PNGs.  Joined/case/newline variants come from the standard oracle.
SYMBOL_CANDIDATES = (
    "opposites attract",
    "the seed is planted when opposites attract",
    "plus minus",
    "red blue",
    "closed open",
    "lock unlock",
    "locked unlocked",
    "closed lock open lock",
    "bank crypto",
    "banking crypto",
    "magnet",
    "magnetic",
    "magnetism",
    "polarity",
    "positive negative",
    "north south",
)

CBC_VARIANTS = (
    tuple(KDF_VARIANTS)
    + tuple(EXTENDED_CIPHER_VARIANTS)
    + tuple(OPENSSL_MENU_GAP_CIPHER_VARIANTS)
)

EXPECTED_CANDIDATE_DIGEST = "11a7607d7b59242a"
EXPECTED_UNIQUE_PASSPHRASES = 504
EXPECTED_EFFECTIVE_OPERATIONS = 282_240
EXPECTED_RAW_KEY_ATTEMPTS = 220


def icon_report():
    report = {}
    for name in ICON_FACTS:
        path = ICON_DIR / name
        with Image.open(path) as image:
            size = image.size
            mode = image.mode
            nonopaque = 0
            alpha_values = 0
            if "A" in image.getbands():
                counts = Counter(image.getchannel("A").getdata())
                alpha_values = len(counts)
                nonopaque = sum(
                    count for alpha, count in counts.items() if alpha != 255
                )
        report[name] = {
            "size": size,
            "mode": mode,
            "file_bytes": path.stat().st_size,
            "sha256_prefix": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
            "alpha_value_count": alpha_values,
            "nonopaque_pixels": nonopaque,
        }
    return report


def unique_passphrases():
    seen = set()
    ordered = []
    for candidate in SYMBOL_CANDIDATES:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                material = keystring.encode()
                if material not in seen:
                    seen.add(material)
                    ordered.append(material)
    return tuple(ordered)


def raw_key_attempt_count():
    keys = set()
    for candidate in SYMBOL_CANDIDATES:
        for form in answer_forms(candidate):
            keys.update(raw_key_forms(form).values())
    return len(keys)


def scope_report():
    passphrases = unique_passphrases()
    operations_per_passphrase_blob = (
        len(CBC_VARIANTS)
        + len(ECB_CIPHER_VARIANTS)
        + len(STREAM_CIPHER_VARIANTS)
        + 4 * len(KEY_WRAP_KDF_VARIANTS)
    )
    return {
        "candidate_count": len(SYMBOL_CANDIDATES),
        "candidate_digest": candidate_list_digest(SYMBOL_CANDIDATES),
        "unique_passphrases": len(passphrases),
        "blobs": tuple(BLOBS),
        "cbc_variants": len(CBC_VARIANTS),
        "ecb_variants": len(ECB_CIPHER_VARIANTS),
        "stream_variants": len(STREAM_CIPHER_VARIANTS),
        "keywrap_kdf_variants": len(KEY_WRAP_KDF_VARIANTS),
        "effective_operations": len(passphrases)
        * len(BLOBS)
        * operations_per_passphrase_blob,
        "raw_key_attempts": raw_key_attempt_count(),
    }


def run():
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for passphrase in unique_passphrases():
        result = aes_try_open_bytes(passphrase, kdf_variants=CBC_VARIANTS, blobs=BLOBS)
        if result:
            hits["cbc"].append((passphrase, result))
        result = aes_try_open_ecb_bytes(passphrase, blobs=BLOBS)
        if result:
            hits["ecb"].append((passphrase, result))
        result = aes_try_open_stream_bytes(passphrase, blobs=BLOBS)
        if result:
            hits["stream"].append((passphrase, result))
        for result in aes_keywrap_try_open_bytes(passphrase, blobs=BLOBS):
            hits["keywrap"].append((passphrase, result))

    raw_attempts, raw_hits = raw_key_sweep(SYMBOL_CANDIDATES)
    report = scope_report()
    report.update({
        "hits": hits,
        "total_hits": sum(len(values) for values in hits.values()),
        "raw_key_attempts": raw_attempts,
        "raw_key_hits": raw_hits,
    })
    return report


def self_test():
    facts = icon_report()
    for name, (size, mode, file_bytes, digest_prefix) in ICON_FACTS.items():
        actual = facts[name]
        assert actual["size"] == size
        assert actual["mode"] == mode
        assert actual["file_bytes"] == file_bytes
        assert actual["sha256_prefix"] == digest_prefix
        assert actual["nonopaque_pixels"] == 0

    assert sum(f["mode"] == "RGB" for f in facts.values()) == 2
    assert sum(f["mode"] == "RGBA" for f in facts.values()) == 6
    assert tuple(255 - value for value in BLUE) != RED
    assert WORD_MATCHING["bank_war"][0] == SYMBOL_MATCHING["lock_lo"][0]
    assert WORD_MATCHING["lock_lo"][0] == SYMBOL_MATCHING["bank_war"][0]
    assert WORD_MATCHING["dig_i_plus"][0] == SYMBOL_MATCHING["dig_i_plus"][0]

    report = scope_report()
    assert report["candidate_count"] == 16
    assert report["candidate_digest"] == EXPECTED_CANDIDATE_DIGEST
    assert report["unique_passphrases"] == EXPECTED_UNIQUE_PASSPHRASES
    assert report["effective_operations"] == EXPECTED_EFFECTIVE_OPERATIONS
    assert report["raw_key_attempts"] == EXPECTED_RAW_KEY_ATTEMPTS
    print(
        "[*] self-test OK: authentic symbol layer has three natural contrasts; "
        "all six RGBA files are fully opaque; bounded oracle scope is "
        "16 candidates / 504 passphrases / 282,240 effective operations"
    )


def jsonable(value):
    if isinstance(value, bytes):
        return value.decode(errors="backslashreplace")
    return repr(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else scope_report()
    report["icon_facts"] = icon_report()
    report["word_matching"] = WORD_MATCHING
    report["symbol_matching"] = SYMBOL_MATCHING
    if args.json:
        print(json.dumps(report, indent=2, default=jsonable))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
