#!/usr/bin/env python3
"""Exact check of the endgame map's registered identifications U1-U5.

Registry: doc/GSMG_ENDGAME_OPERAND_CONSUMER_MAP.md, section "Untested identifications,
registered before any check" (map SHA-256 f9e9d4a8792c6f2f024e74e5b0a0eab3d6e7b082a7a224e96e9880ac60ce2ab2
when the check was first run). Base strings and forms are exactly the registered ones: no case
variants, no scenes, no paraphrases beyond the list.

Forms per base string, each with no newline / LF / CRLF: raw; SHA-256 raw digest; SHA-256 hex
(lowercase and uppercase); SHA-256 of the lowercase hex ("ans too"). Oracles: full CBC (all KDF
variants), stream, ECB and AES key wrap over SALPH, COSMIC, P32TRAILING and URLBLOB; each SHA-256
digest as a raw AES key and as a private key against the prize and halving addresses.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aes_key_wrap_sweep import ALL_CBC_VARIANTS  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    raw_key_try_open,
)
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS, p2pkh_addresses  # noqa: E402

MAP = Path(__file__).resolve().parents[2] / "doc/GSMG_ENDGAME_OPERAND_CONSUMER_MAP.md"
RESULT = Path(__file__).resolve().parent / "endgame_map_u1_u5_result.json"

REGISTRY = {
    "U1": ["We won't", "We won't.", "we won't", "wewont", "WEWONT", "we wont"],
    "U2": ["If I were you, I would hope that we don't meet again",
           "ifiwereyouiwouldhopethatwedontmeetagain"],
    "U3": ["ifiwereyouiwouldhopethatwedontmeetagainwewont"],
    "U4": ["Choice. The problem is choice.", "choicetheproblemischoice"],
    "U5": ["as long as they were given a", "aslongastheyweregivena"],
}


def materials(base):
    out = {}
    for nl_label, nl in (("none", ""), ("lf", "\n"), ("crlf", "\r\n")):
        s = (base + nl).encode("utf-8")
        d = hashlib.sha256(s).digest()
        h = d.hex()
        out[f"raw/{nl_label}"] = s
        out[f"sha_digest/{nl_label}"] = d
        out[f"sha_hex_lower/{nl_label}"] = h.encode()
        out[f"sha_hex_upper/{nl_label}"] = h.upper().encode()
        out[f"double_sha_hex/{nl_label}"] = hashlib.sha256(h.encode()).hexdigest().encode()
    return out


def main():
    blobs = {**BLOBS, **QUARANTINED_BLOBS}
    targets = {PRIZE_ADDRESS, HALVING_ADDRESS}
    report = {"map_sha256": hashlib.sha256(MAP.read_bytes()).hexdigest(), "items": {}, "totals": {}}
    totals = dict(materials=0, cbc=0, stream=0, ecb=0, wrap=0, raw_key=0, address=0)
    for uid, bases in REGISTRY.items():
        rows = []
        for base in bases:
            mats = materials(base)
            hits = []
            for label, m in mats.items():
                totals["materials"] += 1
                if aes_try_open_bytes(m, kdf_variants=ALL_CBC_VARIANTS, blobs=blobs):
                    hits.append(("cbc", label)); totals["cbc"] += 1
                if aes_try_open_stream_bytes(m, blobs=blobs):
                    hits.append(("stream", label)); totals["stream"] += 1
                if aes_try_open_ecb_bytes(m, blobs=blobs):
                    hits.append(("ecb", label)); totals["ecb"] += 1
                for _ in aes_keywrap_try_open_bytes(m, blobs=blobs):
                    hits.append(("wrap", label)); totals["wrap"] += 1
                if label.startswith("sha_digest/"):
                    for _ in raw_key_try_open(m, blobs=blobs):
                        hits.append(("raw_key", label)); totals["raw_key"] += 1
                    if targets & set(p2pkh_addresses(m).values()):
                        hits.append(("address", label)); totals["address"] += 1
            rows.append({"base": base, "materials": len(mats), "hits": hits})
        report["items"][uid] = rows
    report["totals"] = totals
    RESULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["totals"]))
    for uid, rows in report["items"].items():
        print(uid, [(r["base"], len(r["hits"])) for r in rows])


if __name__ == "__main__":
    main()
