#!/usr/bin/env python3
"""Direct-key decode of the DBBI/INCASE ``YOUWON`` 64-character tail.

Phase 75 (``youwon_partition_audit.py``) tested the ``YOUWON`` word, the
``YOUWONX`` row, the 21-character prefix, and the 64/63-character tails only
as CBC/KDF PASSPHRASE text against the tracked blobs, and explicitly demoted
the "64 = hex private key" reading because the tail contains 43 characters
outside ``0-9A-F``.

An external catalog re-raised the tail as a directly hex-DECODED private key
under an unspecified "custom 16-character alphabetic hex mapping (A-P or A-Z
mod 16)", without running the character-set audit it itself proposed. Running
it first: the tail has 24 distinct letters (self-tested below), immediately
incompatible with a bijective 16-letter alphabet such as A-P -- Q through Z
all appear. The only coherent surviving reading is a non-bijective modulo-16
mapping (all 26 letters wrap onto the 16 hex digits), which this script tests
properly -- as a directly DECODED 32-byte key, not as passphrase text, which
is the one angle Phase 75 did not cover.

Three modulo-16 nibble-pairing variants are tested (0-indexed hi/lo,
0-indexed lo/hi, 1-indexed hi/lo), plus two SHA-256-of-payload-as-seed
controls. Each 32-byte candidate is checked three ways:

* directly as a secp256k1 private key -- P2PKH compressed/uncompressed
  addresses compared against the known prize and halving addresses;
* as a raw (non-KDF) 32-byte AES-256 key against SALPH/P32TRAILING (and, with
  --include-quarantined, the quarantined blobs) via
  cb_common.raw_key_try_open -- the same "private key | private key" raw-key
  reading binary_key_material_backfill.py's docstring describes;
* optionally (--verify-api, off by default and rate-limited) against the
  Blockstream API for any on-chain transaction history at all, independent
  of whether the derived key matches a *known* GSMG address.

Usage: python3 tools/gsmg/youwon_direct_key_derivation_audit.py [--verify-api] [--include-quarantined]
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import private_key_details  # noqa: E402
from cb_common import BLOBS, QUARANTINED_BLOBS, raw_key_try_open  # noqa: E402
from first_hint_hash_audit import (  # noqa: E402
    HALVING_ADDRESS,
    PRIZE_ADDRESS,
    SECP256K1_ORDER,
)
from youwon_partition_audit import audit as youwon_audit  # noqa: E402

KNOWN_GSMG_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}
DEFAULT_API_BASE = "https://blockstream.info/api/address"
EXPECTED_UNIQUE_LETTERS = 24


def mod16_nibble_pairs(text, base_ord=ord("A"), swap=False):
    values = [(ord(character) - base_ord) % 16 for character in text]
    pairs = list(zip(values[0::2], values[1::2]))
    if swap:
        pairs = [(lo, hi) for hi, lo in pairs]
    return bytes((hi << 4) | lo for hi, lo in pairs)


def derive_candidates(payload):
    return {
        "mod16_0idx_hilo": mod16_nibble_pairs(payload),
        "mod16_0idx_lohi": mod16_nibble_pairs(payload, swap=True),
        "mod16_1idx_hilo": mod16_nibble_pairs(payload, base_ord=ord("A") - 1),
        "sha256_payload": hashlib.sha256(payload.encode()).digest(),
        "sha256_payload_lower": hashlib.sha256(payload.lower().encode()).digest(),
    }


def check_api_tx_count(address, api_base=DEFAULT_API_BASE, timeout=15.0):
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/{address}",
        headers={"User-Agent": "key-seeker-gsmg-audit/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    chain = payload.get("chain_stats", {})
    mempool = payload.get("mempool_stats", {})
    return int(chain.get("tx_count", 0)) + int(mempool.get("tx_count", 0))


def audit(run_api=False, include_quarantined=False, api_interval=0.4):
    youwon_result = youwon_audit(run_oracle=False)
    payload = youwon_result["candidates"]["tail64"]
    assert len(payload) == 64
    unique_letters = sorted(set(payload))
    assert len(unique_letters) == EXPECTED_UNIQUE_LETTERS, (
        "payload alphabet drifted from the audited 24-letter set -- "
        "re-check the A-P/16-letter framing before trusting downstream results"
    )

    blobs = {**BLOBS, **QUARANTINED_BLOBS} if include_quarantined else BLOBS
    findings = []
    for label, key_bytes in derive_candidates(payload).items():
        entry = {"label": label, "key_hex": key_bytes.hex()}
        value = int.from_bytes(key_bytes, "big")
        if not 1 <= value < SECP256K1_ORDER:
            entry["privkey_valid"] = False
            findings.append(entry)
            continue
        entry["privkey_valid"] = True
        details = private_key_details(key_bytes)
        entry["addresses"] = {form: info["address"] for form, info in details.items()}
        entry["known_address_hit"] = any(
            info["address"] in KNOWN_GSMG_ADDRESSES for info in details.values()
        )
        entry["raw_key_hit"] = bool(raw_key_try_open(key_bytes, blobs=blobs))
        if run_api:
            entry["api_tx_counts"] = {}
            for form, info in details.items():
                try:
                    entry["api_tx_counts"][form] = check_api_tx_count(info["address"])
                except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
                    entry["api_tx_counts"][form] = f"error: {exc}"
                time.sleep(api_interval)
        findings.append(entry)

    assert not any(finding.get("known_address_hit") for finding in findings)
    assert not any(finding.get("raw_key_hit") for finding in findings)
    if run_api:
        assert all(
            count == 0 or isinstance(count, str)
            for finding in findings
            for count in finding.get("api_tx_counts", {}).values()
        )

    return {"payload": payload, "unique_letters": len(unique_letters), "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-api",
        action="store_true",
        dest="run_api",
        help="also check each derived address against Blockstream for any tx history",
    )
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()
    result = audit(run_api=args.run_api, include_quarantined=args.include_quarantined)
    print(f"payload: {result['payload']} ({result['unique_letters']} unique letters)")
    for entry in result["findings"]:
        if not entry["privkey_valid"]:
            print(f"{entry['label']}: out-of-range as a secp256k1 scalar")
            continue
        line = (
            f"{entry['label']}: comp={entry['addresses']['compressed']} "
            f"uncomp={entry['addresses']['uncompressed']} "
            f"known_hit={entry['known_address_hit']} raw_key_hit={entry['raw_key_hit']}"
        )
        if "api_tx_counts" in entry:
            line += f" api_tx_counts={entry['api_tx_counts']}"
        print(line)


if __name__ == "__main__":
    main()
