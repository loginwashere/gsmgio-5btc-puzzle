#!/usr/bin/env python3
"""Exact checks of concrete material posted in the 2026-11-04 Telegram export (ids 75649-78805).

Closed set, fixed from the messages before checking. Strings use the same forms and oracles as
endgame_map_u1_u5_check.py (raw / SHA-256 digest / hex / double SHA, no newline, LF, CRLF; CBC with
all KDF variants, stream, ECB, key wrap, raw key, prize and halving addresses; all blobs).

"derived" entries are literal concatenations of a poster's described recipe, not strings they posted.

Keys: every WIF posted is decoded and its compressed and uncompressed P2PKH addresses are compared
with the prize and halving addresses. The two 25-byte hex strings (77617/77618) are checked as raw
version+hash160+checksum address payloads.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import endgame_map_u1_u5_check as base  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS, p2pkh_addresses  # noqa: E402
from key_shape_classifier import wif_to_private_key  # noqa: E402

RESULT = Path(__file__).resolve().parent / "telegram_2026_11_04_claims_result.json"
REGISTRY = {
    "cs_76101": ["THEPRIVATEKEYSBELONGSTOHALFINNEYE", "theprivatekeysbelongstohalfinneye"],
    "ekodama_75884": ["yellowblueprimesmatrixsumlistyinyangzlastwordsbeforearchichoicezthispasswordz",
                      "yellowblueprimesmatrixsumlistyinyanglastwordsbeforearchichoicethispassword"],
    "tommy_76100": ["yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang"],
    "b58_alex_78613": ["giveityinyang", "giveityingyang", "Giveityingyang"],
    "draikoon_78422": ["yangyangjin", "YangYangJin", "chandlerguolovesyangyangjin",
                       "Chandler Guo loves YangYang Jin"],
    "andrey_78513": ["cryptoio", "crypto.io"],
    "draikoon_78517": ["protect ironic magic me, sight. which still 4 due",
                       "protectironicmagicmesightwhichstill4due"],
    "draikoon_77850_derived": ["secondanswerenterthispassword", "secondanswerthispassword"],
    "alex_75911": ["obellaciao", "abcdefghio"],
    "mohamad_76188": ["MSG"],
}
WIFS = {
    "tommy_77069": "5J79uwWzUdSz1AY6rYZNZSJFbK9j7iYMpFRYqhM8Wv4A8ak4wU",
    "tommy_77071": "5J79uwWzUdSz1AY6rYZNZSJFbK9j7iYMpFRYqhM8Wv4A8ak4wUz",
    "tommy_77646": "5J79uWwZdSz1AY6rYZNZSJFbK9j7iYmpFRYqhM8Wv4A8ak4wU",
    "tommy_77253": "Ky1xCg4yS4PCToPsxPQpC662W9mJhcoyibX1rmb1iTzrQro3mb2M",
    "christo_76360": "5K2byJMssxFKuTgnk9YQjpBz5FhkwwF2LaZoAyTus8HjGEpz8AT",
}
HEX25 = {
    "tommy_77617": "a0af5be609f571de1c8e48e4df4aaeadfa3602d8ecf94b88fc",
    "tommy_77618": "ba8e5190ee1753b94f0bf4c86b1f62ba033105f3b8e6c10271",
}
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + s


def key_checks():
    targets = {PRIZE_ADDRESS, HALVING_ADDRESS}
    out = {}
    for k, w in WIFS.items():
        key = wif_to_private_key(w)
        if key is None:
            out[k] = {"valid_wif": False}
            continue
        addrs = p2pkh_addresses(key)
        out[k] = {"valid_wif": True, "addresses": addrs, "target_hit": bool(targets & set(addrs.values()))}
    for k, h in HEX25.items():
        b = bytes.fromhex(h)
        ok = hashlib.sha256(hashlib.sha256(b[:21]).digest()).digest()[:4] == b[21:]
        out[k] = {"bytes": len(b), "version": b[0], "checksum_valid": ok, "as_base58": b58encode(b),
                  "target_hit": b58encode(b) in targets}
    return out


def main():
    base.REGISTRY = REGISTRY
    base.RESULT = RESULT
    base.main()
    report = json.loads(RESULT.read_text())
    report["key_checks"] = key_checks()
    RESULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["key_checks"], indent=1))


if __name__ == "__main__":
    main()
