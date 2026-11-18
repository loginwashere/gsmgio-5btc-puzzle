#!/usr/bin/env python3
"""Exact checks of concrete strings posted in the 2026-10-07 Telegram export (ids 73869-75648).

Closed set, fixed from the messages before checking:
  74075/74079 (Draikoon)  zion0101, Z1ON0101
  74539       (UNKNOW)    ZION
  74863       (Mohamad)   leavethematrix, yourlastcommand, hereismysecret, isolveditwithanabacus, secondanswer
Same forms and oracles as endgame_map_u1_u5_check.py.

Plus one replay of a specific claim (74719, Boulayo): the passphrase sha256hex("followthewhiterabbit")
followed by "adipfBrr" gives "a 5 bytes valid padding" on COSMIC. The replay reports the padding
under both legacy KDF digests; it is a description, not an oracle hit.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa: E402

import endgame_map_u1_u5_check as base  # noqa: E402
from cb_common import evp_bytes_to_key  # noqa: E402
from data import COSMIC_BLOB_B64  # noqa: E402

RESULT = Path(__file__).resolve().parent / "telegram_2026_10_07_claims_result.json"
REGISTRY = {
    "draikoon_74075": ["zion0101", "Z1ON0101"],
    "unknow_74539": ["ZION"],
    "mohamad_74863": ["leavethematrix", "yourlastcommand", "hereismysecret", "isolveditwithanabacus",
                      "secondanswer"],
}


def boulayo_replay():
    raw = base64.b64decode(COSMIC_BLOB_B64)
    salt, ct = raw[8:16], raw[16:]
    out = {}
    for label, pw in (("hex+suffix", hashlib.sha256(b"followthewhiterabbit").hexdigest() + "adipfBrr"),
                      ("HEX+suffix", hashlib.sha256(b"followthewhiterabbit").hexdigest().upper() + "adipfBrr")):
        for dg in ("md5", "sha256"):
            key, iv = evp_bytes_to_key(pw.encode(), salt, dg)
            pt = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor().update(ct)
            n = pt[-1]
            valid = 1 <= n <= 16 and pt[-n:] == bytes([n]) * n
            printable = sum(32 <= b < 127 or b in (9, 10, 13) for b in pt) / len(pt)
            out[f"{label}/{dg}"] = {"last_bytes": pt[-8:].hex(), "valid_pad": valid,
                                    "pad_len": n if valid else 0, "printable_ratio": round(printable, 3)}
    return out


def main():
    base.REGISTRY = REGISTRY
    base.RESULT = RESULT
    base.main()
    report = json.loads(RESULT.read_text())
    report["boulayo_74719_replay"] = boulayo_replay()
    RESULT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["boulayo_74719_replay"], indent=1))


if __name__ == "__main__":
    main()
