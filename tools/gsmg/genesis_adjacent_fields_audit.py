#!/usr/bin/env python3
"""Genesis-block adjacent unused fields, as password material (2026-08-19).

Closes the one sub-item of Phase 292's Lead 3 (`p32_family10_fork_leads_audit.py`)
that was named in the lead's description but never actually executed: "adjacent
unused data (the date, block height, `nBits` 486604799)" from the genesis
coinbase. Phase 292 tested only the *decoded headline text itself* (raw/upper/
letters-only forms) -- it never touched the block header's own timestamp,
`nBits`, height, or nonce fields as literal password material. This script
closes that specific residual, using the same public, immutable, well-known
genesis block header values (block 0):

    timestamp = 1231006505  (Unix)   -> 2009-01-03T18:15:05Z
    nBits     = 486604799   (decimal) = 0x1d00ffff (compact target)
    height    = 0
    nonce     = 2083236893

Bounded exactly like Lead 3: literal + sha256-hex forms only, against the
standard CBC oracle across all four tracked blobs -- no open-ended sweep, no
ECB/stream/keywrap, no combination with other clue fragments (no
independently-sourced rule exists for that).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS, aes_try_open_bytes  # noqa: E402

TIMESTAMP_UNIX = 1231006505
NBITS_DECIMAL = 486604799
NBITS_HEX = "1d00ffff"
HEIGHT = 0
NONCE = 2083236893


def adjacent_field_candidates():
    forms = {
        "timestamp_unix": str(TIMESTAMP_UNIX),
        "timestamp_iso": "2009-01-03T18:15:05Z",
        "timestamp_date_only": "2009-01-03",
        "nbits_decimal": str(NBITS_DECIMAL),
        "nbits_hex": NBITS_HEX,
        "nbits_hex_0x": f"0x{NBITS_HEX}",
        "height": str(HEIGHT),
        "nonce": str(NONCE),
    }
    return [
        {"lead": "lead3b_genesis_adjacent_fields", "label": name, "text": value}
        for name, value in forms.items()
    ]


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    candidates = adjacent_field_candidates()
    attempts = []
    hits = []
    for candidate in candidates:
        text = candidate["text"]
        forms = (text, hashlib.sha256(text.encode()).hexdigest())
        for form_kind, form_text in zip(("literal", "sha256"), forms):
            result = aes_try_open_bytes(form_text.encode(), blobs=active_blobs)
            attempts.append({"label": candidate["label"], "form": form_kind})
            if result:
                tag, body, kdf_label, key_len = result
                hits.append({
                    "label": candidate["label"],
                    "form": form_kind,
                    "blob": tag,
                    "kdf": f"{kdf_label}/aes{key_len * 8}",
                    "plaintext_hex": body.hex(),
                })
    return {
        "candidate_count": len(candidates),
        "passphrase_attempts": len(attempts),
        "blobs": tuple(active_blobs),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    candidates = adjacent_field_candidates()
    assert len(candidates) == 8
    by_label = {c["label"]: c["text"] for c in candidates}
    assert by_label["nbits_decimal"] == "486604799"
    assert by_label["nbits_hex"] == "1d00ffff"
    assert by_label["timestamp_unix"] == "1231006505"
    print(f"[*] self-test OK: {len(candidates)} genesis-adjacent-field candidates")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.run:
        for candidate in adjacent_field_candidates():
            print(candidate)
        return
    report = run()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
