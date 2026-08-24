#!/usr/bin/env python3
"""Phase 385: finishes Post-Phase-340 Seed 10 (`doc/Brainstorms/
2026-08-20 - Post-Phase-340 Future Search Portfolio.md`, section 10).

Seed 10's 2026-08-20 investigation pass built only the CBC/PKCS#7 row of
its own declared matrix (unpadded plaintext length in `[C-16, C-1]` for a
block-aligned ciphertext of `C` bytes) and explicitly flagged the rest as
open: "compression and stream modes change the inference, so every row
must name its cipher/mode/padding assumptions explicitly." This script
builds the two rows that were left unrun.

**Row 2 -- stream mode (CTR/CFB/OFB/RC4/ChaCha20/Salsa20, no padding):**
plaintext length equals ciphertext length exactly, not a 16-byte window.
This is a strictly stricter constraint than CBC's -- so it can only ever
exclude a role the CBC row admitted, never newly admit one.

**Row 3 -- compression before encryption:** the CBC row's exclusions
implicitly assume the plaintext fed to the cipher IS the literal role
text/bytes. A compression layer between the role object and the cipher
breaks that assumption in general. This project does not adopt an
unbounded "try every compressor" search; the bounded, closed set tested
here is the four general-purpose compressors in the Python standard
library (zlib/raw DEFLATE, gzip, bz2, lzma/xz) at maximum settings,
against one deterministic, reproducible representative string per role
(derived from SHA-256 counter-mode expansion, not `random`, so results are
exactly pinned and re-derivable by anyone re-running this script).

Roles tested (byte length of the role's own literal text/binary form, the
same convention Seed 10's CBC row used): WIF compressed (52), WIF
uncompressed (51), BIP38 (58), mini-key 22 and 30, xprv/xpub (111), hex64
as ASCII hex text (64), and two raw 32-byte binary chunks concatenated
(64, binary not text).

Blobs and their exact ciphertext byte lengths (`cb_common.BLOBS`, unchanged
since Seed 10's pass): SALPH=80, P32TRAILING=80, URLBLOB=96, COSMIC=1328.

This is pure arithmetic and standard-library compression over fixed,
declared inputs -- no oracle sweep, no new cipher/KDF axis, no candidate
search against the blobs' actual ciphertext bytes.

**Result, corrected from an initial wrong hand-check:** compression does
change Seed 10's CBC exclusion table, but not by shrinking base58 text --
DEFLATE cannot compress a 58-symbol alphabet at all (every base58 role
variant is equal or larger than its raw length under all 4 compressors).
Instead, gzip/bz2/lzma's fixed container overhead (headers/trailers)
pushes several roles that were originally too SHORT for the short blobs'
64-79-byte CBC window UP across its floor: BIP38 (58->66/78), mini-key 22
(22->64) and 30 (30->72), and both WIF forms (51/52->71/72) all become
CBC-admissible for SALPH/P32TRAILING under at least one compressor, purely
from container-size arithmetic, with zero bearing on whether the role's
actual content is plausible. xprv/xpub (raw 111, already above every
short-blob window) is never rescued -- nothing shrinks it. One coincidental
stream-mode exact-length hit also appears: mini-key 22 under lzma's `.xz`
container lands on exactly 80 bytes, matching SALPH/P32TRAILING's ciphertext
length precisely.
"""

import hashlib
import json

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

BLOB_CIPHERTEXT_BYTES = {
    "SALPH": 80,
    "P32TRAILING": 80,
    "URLBLOB": 96,
    "COSMIC": 1328,
}


def deterministic_bytes(label, n):
    out = b""
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(f"{label}:{counter}".encode()).digest()
        counter += 1
    return out[:n]


def map_to_alphabet(raw, alphabet):
    return "".join(alphabet[b % len(alphabet)] for b in raw)


def build_role_representatives():
    roles = {}
    roles["wif_compressed"] = (
        "L" + map_to_alphabet(deterministic_bytes("wif_compressed", 51), BASE58_ALPHABET)
    ).encode()
    roles["wif_uncompressed"] = (
        "5" + map_to_alphabet(deterministic_bytes("wif_uncompressed", 50), BASE58_ALPHABET)
    ).encode()
    roles["bip38"] = (
        "6P" + map_to_alphabet(deterministic_bytes("bip38", 56), BASE58_ALPHABET)
    ).encode()
    roles["minikey22"] = (
        "S" + map_to_alphabet(deterministic_bytes("minikey22", 21), BASE58_ALPHABET)
    ).encode()
    roles["minikey30"] = (
        "S" + map_to_alphabet(deterministic_bytes("minikey30", 29), BASE58_ALPHABET)
    ).encode()
    roles["xprv_xpub"] = (
        "xprv" + map_to_alphabet(deterministic_bytes("xprv_xpub", 107), BASE58_ALPHABET)
    ).encode()
    roles["hex64_text"] = deterministic_bytes("hex64_text", 32).hex().encode()
    roles["raw32x2"] = deterministic_bytes("raw32x2", 64)
    return roles


def compress_all(data):
    import bz2
    import gzip
    import lzma
    import zlib

    return {
        "raw": data,
        "zlib": zlib.compress(data, 9),
        "gzip": gzip.compress(data, compresslevel=9),
        "bz2": bz2.compress(data, 9),
        "lzma": lzma.compress(data),
    }


def cbc_admissible(length, ciphertext_bytes):
    return ciphertext_bytes - 16 <= length <= ciphertext_bytes - 1


def stream_admissible(length, ciphertext_bytes):
    return length == ciphertext_bytes


def audit():
    roles = build_role_representatives()
    lengths = {}
    matrix = {}
    newly_admitted = []
    newly_excluded = []

    for role_name, data in roles.items():
        variants = compress_all(data)
        lengths[role_name] = {variant: len(payload) for variant, payload in variants.items()}
        for blob_name, ciphertext_bytes in BLOB_CIPHERTEXT_BYTES.items():
            for variant, payload in variants.items():
                length = len(payload)
                cbc_ok = cbc_admissible(length, ciphertext_bytes)
                stream_ok = stream_admissible(length, ciphertext_bytes)
                matrix[(role_name, variant, blob_name)] = {
                    "length": length,
                    "cbc_admissible": cbc_ok,
                    "stream_admissible": stream_ok,
                }
                raw_length = lengths[role_name]["raw"]
                raw_cbc_ok = cbc_admissible(raw_length, ciphertext_bytes)
                if variant != "raw":
                    if cbc_ok and not raw_cbc_ok:
                        newly_admitted.append((role_name, variant, blob_name, "cbc"))
                    if raw_cbc_ok and not cbc_ok:
                        newly_excluded.append((role_name, variant, blob_name, "cbc"))
                if stream_ok:
                    # Stream mode has no "raw" baseline in Seed 10's own
                    # investigation pass (it only built the CBC row), so
                    # every stream hit is reported directly, not as a delta.
                    newly_admitted.append((role_name, variant, blob_name, "stream"))

    return {
        "roles": sorted(roles),
        "blobs": BLOB_CIPHERTEXT_BYTES,
        "lengths": lengths,
        "newly_admitted": sorted(set(newly_admitted)),
        "newly_excluded": sorted(set(newly_excluded)),
    }


def self_test():
    report = audit()

    assert report["lengths"]["wif_compressed"] == {
        "raw": 52, "zlib": 60, "gzip": 72, "bz2": 90, "lzma": 108,
    }
    assert report["lengths"]["wif_uncompressed"] == {
        "raw": 51, "zlib": 59, "gzip": 71, "bz2": 94, "lzma": 108,
    }
    assert report["lengths"]["bip38"] == {
        "raw": 58, "zlib": 66, "gzip": 78, "bz2": 97, "lzma": 116,
    }
    assert report["lengths"]["minikey22"] == {
        "raw": 22, "zlib": 30, "gzip": 42, "bz2": 64, "lzma": 80,
    }
    assert report["lengths"]["minikey30"] == {
        "raw": 30, "zlib": 38, "gzip": 50, "bz2": 72, "lzma": 88,
    }
    assert report["lengths"]["xprv_xpub"] == {
        "raw": 111, "zlib": 115, "gzip": 127, "bz2": 140, "lzma": 172,
    }
    assert report["lengths"]["hex64_text"] == {
        "raw": 64, "zlib": 58, "gzip": 70, "bz2": 78, "lzma": 120,
    }
    assert report["lengths"]["raw32x2"] == {
        "raw": 64, "zlib": 75, "gzip": 87, "bz2": 132, "lzma": 120,
    }

    # Ground truth (pinned exactly, not eyeballed -- an initial hand check
    # while writing this script wrongly assumed no base58 role could enter
    # a CBC window under compression; that assumption failed this
    # self-test on first run and was replaced with the real, computed set
    # below, exactly the "verify, don't assume" discipline this project
    # already applies elsewhere).
    expected_newly_admitted = sorted({
        ("bip38", "gzip", "P32TRAILING", "cbc"),
        ("bip38", "gzip", "SALPH", "cbc"),
        ("bip38", "zlib", "P32TRAILING", "cbc"),
        ("bip38", "zlib", "SALPH", "cbc"),
        ("minikey22", "bz2", "P32TRAILING", "cbc"),
        ("minikey22", "bz2", "SALPH", "cbc"),
        ("minikey22", "lzma", "P32TRAILING", "stream"),
        ("minikey22", "lzma", "SALPH", "stream"),
        ("minikey22", "lzma", "URLBLOB", "cbc"),
        ("minikey30", "bz2", "P32TRAILING", "cbc"),
        ("minikey30", "bz2", "SALPH", "cbc"),
        ("minikey30", "lzma", "URLBLOB", "cbc"),
        ("raw32x2", "gzip", "URLBLOB", "cbc"),
        ("wif_compressed", "bz2", "URLBLOB", "cbc"),
        ("wif_compressed", "gzip", "P32TRAILING", "cbc"),
        ("wif_compressed", "gzip", "SALPH", "cbc"),
        ("wif_uncompressed", "bz2", "URLBLOB", "cbc"),
        ("wif_uncompressed", "gzip", "P32TRAILING", "cbc"),
        ("wif_uncompressed", "gzip", "SALPH", "cbc"),
    })
    expected_newly_excluded = sorted({
        ("hex64_text", "lzma", "P32TRAILING", "cbc"),
        ("hex64_text", "lzma", "SALPH", "cbc"),
        ("hex64_text", "zlib", "P32TRAILING", "cbc"),
        ("hex64_text", "zlib", "SALPH", "cbc"),
        ("raw32x2", "bz2", "P32TRAILING", "cbc"),
        ("raw32x2", "bz2", "SALPH", "cbc"),
        ("raw32x2", "gzip", "P32TRAILING", "cbc"),
        ("raw32x2", "gzip", "SALPH", "cbc"),
        ("raw32x2", "lzma", "P32TRAILING", "cbc"),
        ("raw32x2", "lzma", "SALPH", "cbc"),
    })
    assert report["newly_admitted"] == expected_newly_admitted
    assert report["newly_excluded"] == expected_newly_excluded

    # Causal check: every rescue happens via container/header overhead
    # pushing an originally too-short role UP into a window from below
    # (raw length < window floor), never via a compressor actually
    # shrinking a role that was originally too long. xprv/xpub (raw 111,
    # already above every short-blob window) never appears in either set
    # under any of the 4 compressors -- DEFLATE-family algorithms cannot
    # shrink a 58-symbol (~5.858 bit/char) base58 alphabet at all; every
    # rescued role's raw length was below the window it gets rescued into.
    windows = {"SALPH": (64, 79), "P32TRAILING": (64, 79), "URLBLOB": (80, 95)}
    for role_name, variant, blob_name, mode in report["newly_admitted"]:
        if mode != "cbc":
            continue
        raw_length = report["lengths"][role_name]["raw"]
        floor, _ceiling = windows[blob_name]
        assert raw_length < floor, (role_name, variant, blob_name, raw_length, floor)
    assert not any(row[0] == "xprv_xpub" for row in report["newly_admitted"])

    # No representative reaches anywhere near COSMIC's 1312-1327 CBC
    # window or its 1328-byte stream-mode exact length under any tested
    # compressor -- the largest observed output is xprv_xpub/lzma at 172.
    assert all(
        length < 1312
        for role_lengths in report["lengths"].values()
        for length in role_lengths.values()
    )

    print(
        f"[*] self-test OK: {len(report['roles'])} roles x 5 length variants "
        f"(raw + 4 compressors) x {len(report['blobs'])} blobs; "
        f"{len(report['newly_admitted'])} newly-admitted rows, "
        f"{len(report['newly_excluded'])} newly-excluded rows vs Seed 10's "
        f"CBC-only baseline"
    )
    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
