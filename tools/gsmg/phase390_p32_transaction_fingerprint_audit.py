#!/usr/bin/env python3
"""Phase 390: P32 Family 9 -- transaction serialization / wallet-style
fingerprint audit.

Phase 383 (P32 Family 2) closed the on-chain graph negative but pinned exact
raw bytes for the only two transactions a known GSMG seed address ever
signs (`doc/evidence/GSMG_P32_FAMILY2_SIGNED_TRANSACTION_CACHE.json`,
independently cross-source verified there). This phase parses those two raw
transactions directly (no external library -- both are legacy version-2,
non-SegWit, P2PKH-only transactions, small enough to hand-parse) and
examines exactly the objective, closed set of wallet-fingerprint facts:

  - ECDSA `r` values across all signing inputs, checked for repetition
    (repetition would let the private key be recovered directly -- a real
    cryptographic break, not a heuristic).
  - Strict DER encoding and low-S normalization of every signature.
  - SIGHASH flag and public-key encoding (compressed vs. uncompressed) on
    every input.
  - `version`, `sequence`, and `nLockTime`.
  - Input/output ordering, fee, and change-output behavior.

This is deliberately narrow: it draws no inference beyond these six
concrete fields, and does not attempt address clustering, wallet-software
fingerprinting via heuristics libraries, or any password/key derivation
from the results.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from first_hint_hash_audit import SECP256K1_ORDER  # noqa: E402

CACHE_PATH = (
    SCRIPT_DIR.parent.parent
    / "doc" / "evidence" / "GSMG_P32_FAMILY2_SIGNED_TRANSACTION_CACHE.json"
)

HALF_ORDER = SECP256K1_ORDER // 2


def _read_varint(data, offset):
    first = data[offset]
    if first < 0xFD:
        return first, offset + 1
    if first == 0xFD:
        return int.from_bytes(data[offset + 1:offset + 3], "little"), offset + 3
    if first == 0xFE:
        return int.from_bytes(data[offset + 1:offset + 5], "little"), offset + 5
    return int.from_bytes(data[offset + 1:offset + 9], "little"), offset + 9


def parse_legacy_transaction(raw_hex):
    """Hand-parses a legacy (non-SegWit) transaction. Both Phase 383
    transactions are version 2, P2PKH-only, with no `0001` SegWit marker
    (verified by `self_test()` against their known input/output counts)."""
    data = bytes.fromhex(raw_hex)
    offset = 0
    version = int.from_bytes(data[offset:offset + 4], "little")
    offset += 4

    vin_count, offset = _read_varint(data, offset)
    vins = []
    for _ in range(vin_count):
        prev_txid = data[offset:offset + 32][::-1].hex()
        offset += 32
        prev_vout = int.from_bytes(data[offset:offset + 4], "little")
        offset += 4
        script_len, offset = _read_varint(data, offset)
        script_sig = data[offset:offset + script_len]
        offset += script_len
        sequence = int.from_bytes(data[offset:offset + 4], "little")
        offset += 4
        vins.append({
            "prev_txid": prev_txid,
            "prev_vout": prev_vout,
            "script_sig": script_sig,
            "sequence": sequence,
        })

    vout_count, offset = _read_varint(data, offset)
    vouts = []
    for _ in range(vout_count):
        value = int.from_bytes(data[offset:offset + 8], "little")
        offset += 8
        script_len, offset = _read_varint(data, offset)
        script_pubkey = data[offset:offset + script_len]
        offset += script_len
        vouts.append({"value": value, "script_pubkey": script_pubkey.hex()})

    locktime = int.from_bytes(data[offset:offset + 4], "little")
    offset += 4
    assert offset == len(data), (offset, len(data))

    return {
        "version": version,
        "vin": vins,
        "vout": vouts,
        "locktime": locktime,
    }


def split_p2pkh_script_sig(script_sig):
    """P2PKH scriptSig is exactly `<push:sig><push:pubkey>`. Both pushes here
    are short (<0x4c bytes) so the push opcode is a literal length byte."""
    offset = 0
    sig_len = script_sig[offset]
    offset += 1
    sig = script_sig[offset:offset + sig_len]
    offset += sig_len
    pubkey_len = script_sig[offset]
    offset += 1
    pubkey = script_sig[offset:offset + pubkey_len]
    offset += pubkey_len
    assert offset == len(script_sig), (offset, len(script_sig))
    return sig, pubkey


def parse_der_ecdsa_sig(sig_with_sighash):
    """Splits a DER-encoded ECDSA signature (with a trailing 1-byte SIGHASH
    flag) into (r, s, sighash, strict_der). `strict_der` checks BIP66's
    exact grammar: 0x30 <total-len> 0x02 <r-len> <r> 0x02 <s-len> <s>, no
    extra bytes, minimal-length integers, no leading 0x00 on a positive
    integer unless required to avoid a negative sign bit."""
    sighash = sig_with_sighash[-1]
    der = sig_with_sighash[:-1]

    def minimal_int_ok(b):
        if len(b) == 0:
            return False
        if b[0] & 0x80:
            return False  # would be interpreted as negative; must be padded
        if len(b) > 1 and b[0] == 0x00 and not (b[1] & 0x80):
            return False  # non-minimal zero-padding
        return True

    strict = True
    if len(der) < 9 or der[0] != 0x30:
        strict = False
    total_len = der[1] if strict else 0
    if strict and total_len != len(der) - 2:
        strict = False
    if strict and der[2] != 0x02:
        strict = False
    r_len = der[3] if strict else 0
    r = der[4:4 + r_len] if strict else b""
    if strict and not minimal_int_ok(r):
        strict = False
    s_marker_off = 4 + r_len
    if strict and (s_marker_off >= len(der) or der[s_marker_off] != 0x02):
        strict = False
    s_len = der[s_marker_off + 1] if strict else 0
    s = der[s_marker_off + 2:s_marker_off + 2 + s_len] if strict else b""
    if strict and not minimal_int_ok(s):
        strict = False
    if strict and s_marker_off + 2 + s_len != len(der):
        strict = False

    if not strict:
        # Fall back to a lenient parse (still splits r/s) so the fields are
        # still reported even if DER strictness itself is what's being
        # measured -- but every real-world Bitcoin Core-relayed transaction
        # (both of these, per Phase 383's cross-source confirmation) is
        # DER-strict by consensus rule (BIP66, active well before 2020), so
        # this branch is not expected to trigger.
        r_len = der[3]
        r = der[4:4 + r_len]
        s_len = der[4 + r_len + 1]
        s = der[4 + r_len + 2:4 + r_len + 2 + s_len]

    r_int = int.from_bytes(r, "big")
    s_int = int.from_bytes(s, "big")
    return {
        "r_hex": r.hex(),
        "s_hex": s.hex(),
        "r_int": r_int,
        "s_int": s_int,
        "sighash": sighash,
        "strict_der": strict,
        "low_s": s_int <= HALF_ORDER,
    }


def pubkey_encoding(pubkey):
    if len(pubkey) == 65 and pubkey[0] == 0x04:
        return "uncompressed"
    if len(pubkey) == 33 and pubkey[0] in (0x02, 0x03):
        return "compressed"
    return f"unknown({len(pubkey)}b,prefix=0x{pubkey[0]:02x})"


def analyze_transaction(txid, raw_hex):
    parsed = parse_legacy_transaction(raw_hex)
    inputs = []
    for i, vin in enumerate(parsed["vin"]):
        sig_with_sighash, pubkey = split_p2pkh_script_sig(vin["script_sig"])
        der = parse_der_ecdsa_sig(sig_with_sighash)
        inputs.append({
            "index": i,
            "prev_txid": vin["prev_txid"],
            "prev_vout": vin["prev_vout"],
            "sequence": vin["sequence"],
            "pubkey_encoding": pubkey_encoding(pubkey),
            "pubkey_hex": pubkey.hex(),
            **der,
        })
    outputs = [
        {"index": i, "value": vout["value"], "script_pubkey": vout["script_pubkey"]}
        for i, vout in enumerate(parsed["vout"])
    ]
    return {
        "txid": txid,
        "version": parsed["version"],
        "locktime": parsed["locktime"],
        "inputs": inputs,
        "outputs": outputs,
    }


def load_cache():
    with open(CACHE_PATH) as f:
        return json.load(f)


def audit():
    cache = load_cache()
    txs = [
        analyze_transaction(tx["normalized_transaction"]["txid"], tx["raw_hex"])
        for tx in cache["transactions"]
    ]

    all_r_values = [
        (tx["txid"], inp["index"], inp["r_hex"])
        for tx in txs for inp in tx["inputs"]
    ]
    r_only = [r for _, _, r in all_r_values]
    repeated_r = len(r_only) != len(set(r_only))

    return {
        "transactions": txs,
        "total_signing_inputs": len(all_r_values),
        "all_r_values": all_r_values,
        "repeated_r": repeated_r,
        "all_strict_der": all(inp["strict_der"] for tx in txs for inp in tx["inputs"]),
        "all_low_s": all(inp["low_s"] for tx in txs for inp in tx["inputs"]),
        "sighash_flags": sorted({inp["sighash"] for tx in txs for inp in tx["inputs"]}),
        "pubkey_encodings": sorted({
            inp["pubkey_encoding"] for tx in txs for inp in tx["inputs"]
        }),
        "versions": sorted({tx["version"] for tx in txs}),
        "sequences": sorted({inp["sequence"] for tx in txs for inp in tx["inputs"]}),
        "locktimes": sorted({tx["locktime"] for tx in txs}),
    }


def self_test():
    result = audit()
    assert result["total_signing_inputs"] == 6, result["total_signing_inputs"]
    assert result["repeated_r"] is False
    assert result["all_strict_der"] is True
    assert result["all_low_s"] is True
    assert result["sighash_flags"] == [1]  # SIGHASH_ALL only
    assert result["pubkey_encodings"] == ["uncompressed"]
    assert result["versions"] == [2]
    assert result["sequences"] == [4294967293]  # 0xfffffffd, RBF-signaling
    assert result["locktimes"] == [629998, 840003]

    tx0, tx1 = result["transactions"]
    assert tx0["txid"] == "2aa9a4a90be819d5122d70c993280785a0508f163521e7b38cebb4db0b071b13"
    assert len(tx0["inputs"]) == 3
    assert len(tx0["outputs"]) == 2
    assert tx1["txid"] == "88cdb3cdca12b471551b1b26188508a14ca5fd8a415223ffb7c190381c9b9df3"
    assert len(tx1["inputs"]) == 3
    assert len(tx1["outputs"]) == 2

    # Every input across both transactions uses the same public key (one
    # private key signs everything) -- confirms Phase 383's "every input
    # address is the prize address itself" from the pubkey level, not just
    # the address level.
    pubkeys = {inp["pubkey_hex"] for tx in result["transactions"] for inp in tx["inputs"]}
    assert len(pubkeys) == 1, pubkeys

    print(
        "[*] self-test OK: 6 signing inputs, 0 repeated r, all strict-DER, "
        "all low-S, SIGHASH_ALL only, single uncompressed pubkey throughout"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(audit(), indent=2, default=str))


if __name__ == "__main__":
    main()
