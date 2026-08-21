#!/usr/bin/env python3
"""Phase 351: does the authenticated, live-fetched Phase 2/Phase 3 AES-CBC
plaintext contain real 0x08 (backspace) control bytes?

Motivation: FINDINGS Phase 268/269 found that a 2025 Telegram repost (message
38301) appends eight literal `\\b` text characters after the "worst gear"
line, while the earliest preserved 2020 repost (message 2834) does not -- so
those chat-transcription artifacts were correctly never treated as
authenticated puzzle bytes. A follow-up hypothesis asked a different, sharper
question: not about a chat repost, but about the actual creator-authored
ciphertext itself -- if real 0x08 bytes existed inside the genuine ,
decrypted Phase 2 plaintext (as opposed to a community's markdown
transcription of it, which could silently normalize control characters)
they would be authenticated and specific enough to be worth pursuing as
executable terminal semantics (cursor-left, prompt overwrite, etc.).

This module answers that directly against the primary source rather than a
transcription: it fetches the live gsmg.io Phase 2 page (same one-GET, no-JS
safety boundary as tools/gsmg/provenance_monitor.py), extracts the raw
ciphertext straight out of the HTML <textarea>, decrypts it with this
project's own established KDF convention (tools/gsmg/cb_common.py's
evp_bytes_to_key with digest "sha256", not the community README's undecorated
`openssl enc` invocation, which uses whatever the local machine's OpenSSL
default digest is and does not reproduce the solve), and inspects every byte
of the recovered plaintext -- not just the tail -- for 0x08 or any other
non-CRLF control byte. The same check runs on Phase 3's ciphertext (leads
into Phase 3.2) as an adjacent comparison point.

Not stored: no password, private key, or WIF anywhere in this file or its
output. The two AES passwords used here (SHA-256("causality") and Phase 3's
already-published seven-part concatenation digest) are long-public creator
clues, identical to what's already in tools/gsmg/data.py and README.md.
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cb_common import evp_bytes_to_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PHASE2_URL = (
    "https://gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerand"
    "thosewithoutaveryspecialdessertiwroteitmyself"
)
USER_AGENT = "gsmg-puzzle-research-control-byte-audit/1.0 (read-only GET; no JS/forms executed)"

PHASE2_PASSWORD = "eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf"
PHASE3_PASSWORD = "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5"

# Pinned 2026-08-20 live observation. If the live fetch's ciphertext digest
# ever differs from these, that is itself new evidence (a page change) and
# is reported as such rather than silently re-verified against stale values.
PINNED = {
    "phase2": {
        "ciphertext_b64_sha256": "f61214da332901a86dfca3f8ab6b7b8b281af27d979c2d1f5acdc727ed047443",
        "plaintext_sha256": "e2f9dd65604a3231f8b3301724e8d713a88fffc4b6c7c4aeeb20f58a582b593a",
        "plaintext_len": 648,
    },
    "phase3": {
        "ciphertext_b64_sha256": "09bd77184746fa3daff13bbfcccf348fe0f22a67252c8cb4d36def8adc016dbc",
        "plaintext_len": 4090,
    },
}

# A short, self-contained fixture (independent of the real puzzle) used only
# by self_test() to prove the decrypt+scan pipeline actually detects a
# planted 0x08 byte, so a clean self-test can't be a vacuous "always zero"
# check. Built at self-test time, not hardcoded ciphertext.


def extract_textareas(html):
    return re.findall(r"<textarea[^>]*>(.*?)</textarea>", html, re.S)


def clean_b64(raw_textarea_text):
    return re.sub(r"[^A-Za-z0-9+/=]", "", raw_textarea_text)


def fetch_live(url, timeout=20):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="strict")


def openssl_decrypt(b64_blob, password_hex_string, digest="sha256"):
    """Reproduces `openssl enc -aes-256-cbc -d -a -pass pass:<hex>` using this
    project's own already-verified KDF convention (cb_common.evp_bytes_to_key
    with digest='sha256'), not a fresh reimplementation."""
    raw = __import__("base64").b64decode(b64_blob, validate=True)
    if not raw.startswith(b"Salted__"):
        raise ValueError("not an OpenSSL Salted__ blob")
    salt, ct = raw[8:16], raw[16:]
    if len(ct) == 0 or len(ct) % 16 != 0:
        raise ValueError("ciphertext is not a whole number of AES blocks")
    key, iv = evp_bytes_to_key(password_hex_string.encode(), salt, digest, 32, 16)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    pad = padded[-1]
    if not (1 <= pad <= 16) or padded[-pad:] != bytes([pad]) * pad:
        raise ValueError("invalid PKCS7 padding -- wrong password, KDF, or ciphertext")
    return padded[:-pad]


def control_byte_report(plaintext):
    positions_0x08 = [i for i, b in enumerate(plaintext) if b == 0x08]
    other_control = [
        (i, b) for i, b in enumerate(plaintext)
        if b < 0x20 and b not in (0x0D, 0x0A) and b != 0x08
    ]
    return {
        "length": len(plaintext),
        "sha256": hashlib.sha256(plaintext).hexdigest(),
        "backspace_0x08_count": len(positions_0x08),
        "backspace_0x08_positions": positions_0x08,
        "other_control_byte_count": len(other_control),
        "tail_hex": plaintext[-24:].hex(),
        "tail_repr": repr(plaintext[-24:]),
    }


def audit_page(html):
    areas = extract_textareas(html)
    if len(areas) < 2:
        raise AssertionError(f"expected >=2 textareas (Phase 2, Phase 3), found {len(areas)}")

    results = {}
    for name, area, password in (
        ("phase2", areas[0], PHASE2_PASSWORD),
        ("phase3", areas[1], PHASE3_PASSWORD),
    ):
        blob = clean_b64(area)
        blob_digest = hashlib.sha256(blob.encode()).hexdigest()
        pinned = PINNED[name]
        digest_changed = blob_digest != pinned["ciphertext_b64_sha256"]
        plaintext = openssl_decrypt(blob, password, digest="sha256")
        report = control_byte_report(plaintext)
        report["ciphertext_b64_sha256"] = blob_digest
        report["ciphertext_digest_changed_since_pin"] = digest_changed
        results[name] = report
    return results


def self_test():
    import base64

    # 0. Network isolation for the entire self-test: patched here and only
    #    restored at the very end, so every check below is proven to never
    #    reach the network (fetch_live() is only ever called from --run).
    original_urlopen = urllib.request.urlopen

    def exploding_urlopen(*args, **kwargs):
        raise AssertionError("self_test() must not touch the network")

    urllib.request.urlopen = exploding_urlopen

    # 1. Exact frozen source citations.
    assert PHASE2_URL == (
        "https://gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerand"
        "thosewithoutaveryspecialdessertiwroteitmyself"
    )
    assert PHASE2_PASSWORD == hashlib.sha256(b"causality").hexdigest()
    from data import VERIFIED_PRIOR_COMMAND_HASHES
    assert PHASE3_PASSWORD == VERIFIED_PRIOR_COMMAND_HASHES["phase3_parts"]

    # 2. extract_textareas / clean_b64 round-trip on a synthetic two-textarea
    #    page, including noise (whitespace, a stray non-b64 char) that a real
    #    HTML response could plausibly contain.
    fake_html = (
        "<html><body>"
        "<textarea>\n  U2Fs dGVk \n  X1++/==  </textarea>"
        "<textarea>second-blob-content</textarea>"
        "</body></html>"
    )
    areas = extract_textareas(fake_html)
    assert len(areas) == 2
    assert clean_b64(areas[0]) == "U2FsdGVkX1++/=="
    assert clean_b64(areas[1]) == "secondblobcontent"

    # 3. Real decrypt/pad-check machinery, proven against a locally built
    #    fixture (not the real puzzle) with a KNOWN password and salt, so
    #    correctness doesn't depend on network access or on the real puzzle
    #    files staying unchanged.
    def build_fixture(plaintext_bytes, password_hex_string, salt=b"01234567"):
        key, iv = evp_bytes_to_key(password_hex_string.encode(), salt, "sha256", 32, 16)
        pad = 16 - (len(plaintext_bytes) % 16)
        padded = plaintext_bytes + bytes([pad]) * pad
        encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        ct = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(b"Salted__" + salt + ct).decode()

    fixture_password = "deadbeef" * 8  # 64 hex chars, same shape as the real passwords
    clean_plaintext = b"no control bytes here, just an ordinary sentence."
    clean_blob = build_fixture(clean_plaintext, fixture_password)
    recovered = openssl_decrypt(clean_blob, fixture_password, digest="sha256")
    assert recovered == clean_plaintext
    clean_report = control_byte_report(recovered)
    assert clean_report["backspace_0x08_count"] == 0
    assert clean_report["other_control_byte_count"] == 0

    # 4. Planted-positive control: prove the scanner actually finds 0x08 when
    #    it is really there, so a clean real-run result can't be a silently
    #    broken/vacuous check.
    dirty_prefix = b"trailing seven backspaces next"
    dirty_plaintext = dirty_prefix + b"\x08" * 7
    dirty_blob = build_fixture(dirty_plaintext, fixture_password)
    dirty_recovered = openssl_decrypt(dirty_blob, fixture_password, digest="sha256")
    dirty_report = control_byte_report(dirty_recovered)
    assert dirty_report["backspace_0x08_count"] == 7
    assert dirty_report["backspace_0x08_positions"] == list(range(len(dirty_prefix), len(dirty_prefix) + 7))

    # 5. Wrong-password control: decrypting with the wrong password must
    #    raise (invalid padding), not silently return garbage as if valid.
    threw = False
    try:
        openssl_decrypt(clean_blob, "ffffffff" * 8, digest="sha256")
    except ValueError:
        threw = True
    assert threw, "wrong password did not raise on invalid padding"

    # 6. Reproduce the actual 2026-08-20 live finding from a pinned, offline
    #    copy of the real Phase 2 ciphertext (public creator-authored
    #    ciphertext, not a secret) -- proves the full real pipeline, still
    #    with no network call in self_test().
    real_phase2_b64 = (
        "U2FsdGVkX18GKGYS1D7X7VjxWz6uUyPFszr8dVvtOIrJqioWHgT69JJnzJGDVOvF"
        "QYWh5BEZxFPXmMq1cbyy3dVVDgLhF050xlDy2J5grtKw9jUOO4oFNRgoD+1dlukX"
        "pd8ccg++kkXgE9mGBP6lQbukDiSjY4mnR2Mv6ydIncrRqacQNVEmEgM4fGTi1ANz"
        "nHsGn7mP+P3UyrJCRbuFmpZJc4CNdPj6YuxwR4HkHkqcfxh0L5CaEu4VbY70+fmk"
        "qgZQyMJqiUlaV9KC4UPuRVj0r7MYbVRazkhsjeIcogmdJGEeBwD47lEB7X9PNKWm"
        "ojTvRZg6R+sZzRZE26VLaF+s9cpTo4Y8PZUxKvQ86HXC8QIavUgDfw7HxIxkTatv"
        "CW2yq3ZOXl5naR6oSNxdX9alyhTzB+/2623oGdlWev5Oo8xHJqUi7QjVP+mNC8BA"
        "+Cg0DJwcOFGO5K7g8Rm06+sLogwntdIgTo70X3FegAtipHboeUNKefiAguvkDoIf"
        "8iMPc+83PygvlZPDNQCOKugwDEUimhHwQrMsmalRNoFEQEb+ZIC+na15cPoRAlOD"
        "NJfXIJ96ihAy9wWis39mQW6JFqZmUags4xoP3lJ35bCrXsNOPFZ4WH+f4YC/Ov8C"
        "QW5bjtxno8GG4b/wBWevhcRVMK6KmRJj8NBCssnrlz0sQ70rMNkiN2wiSPcwX3Ad"
        "JgLs8vQAUM59x9fkKFFzD4+Sc1sJztUTB7CMGGfpZOA8W33VZnEdmGcoaHlDsR8G"
        "vAkZ+jg+QJs9ZNHqWE1+1zgm/6NsWWgWH8OI2PPCfXHxDbfDk8uD/Zibr/yjSKvu"
        "Sb8OecflOT2hw37WL49uADgeWgnp2bzkfGIq7EYS7OImjZZwY5h4sfcPfhvQ9kOV"
    )
    assert hashlib.sha256(real_phase2_b64.encode()).hexdigest() == PINNED["phase2"]["ciphertext_b64_sha256"]
    real_plain = openssl_decrypt(real_phase2_b64, PHASE2_PASSWORD, digest="sha256")
    real_report = control_byte_report(real_plain)
    assert real_report["length"] == PINNED["phase2"]["plaintext_len"] == 648
    assert real_report["sha256"] == PINNED["phase2"]["plaintext_sha256"]
    assert real_report["backspace_0x08_count"] == 0
    assert real_report["other_control_byte_count"] == 0
    assert real_plain.endswith(b"the worst gear.")
    assert b"# X 2 S H 4 Y 0 Q B 15 #" in real_plain

    # 7. No candidate literal or WIF-shaped string in this module's own
    #    source text (standard mechanical scan used by every sibling phase).
    import re as _re
    source = Path(__file__).read_text()
    assert not _re.search(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b", source)

    urllib.request.urlopen = original_urlopen

    print("[*] self-test OK (network-isolated): URL/password citations verified; "
          "textarea/base64 extraction proven on synthetic noisy HTML; decrypt+pad-check "
          "proven correct on a local fixture with a wrong-password control; planted "
          "7x0x08 control detected exactly at its true positions (not vacuous); the "
          "pinned real 2026-08-20 Phase 2 ciphertext decrypts, offline, to the exact "
          "expected 648-byte/known-SHA-256 plaintext with zero 0x08 and zero other "
          "control bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="Live fetch + decrypt + control-byte scan.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if args.run:
        html = fetch_live(PHASE2_URL)
        results = audit_page(html)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for name, report in results.items():
                print(f"[*] {name}: len={report['length']} sha256={report['sha256']} "
                      f"0x08_count={report['backspace_0x08_count']} "
                      f"other_control={report['other_control_byte_count']} "
                      f"digest_changed_since_pin={report['ciphertext_digest_changed_since_pin']}")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
