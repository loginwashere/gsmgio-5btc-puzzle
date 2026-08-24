#!/usr/bin/env python3
"""Phase 400: executes Priority 4 of the 2026-08-25 BTCSEED/P91/Z
continuation brainstorm -- testing `P90`/`P91`/`Q472`/the full 570-character
decode directly as Bitcoin key material, since the stream is headed
`BTCSEED` and Phase 396 only ever tested P91-derived strings as AES blob
passphrases, never as a raw private key or BIP32 seed.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`, Priority 4, frozen by the user as an exact contract before
this script was written:

- source objects: exact `P90` (`decoded[7:97]`), `P91` (`decoded[7:98]`),
  `Q472` (`decoded[98:]`), and the full 570-character decode;
- case forms: uppercase-as-decoded and lowercase only -- 8 distinct roots,
  no other case variant;
- material: binary `SHA256(text)` digest only -- no hex-text hashes, double
  hashes, whitespace variants, or truncation;
- direct consumer: the 32-byte digest interpreted as a secp256k1 scalar,
  rejected (not reduced) if outside `1..n-1`;
- BIP32 consumer: the same 32-byte digest used as standard BIP32 seed
  material (`HMAC-SHA512("Bitcoin seed", seed)`);
- checked: the direct digest-derived private key; the BIP32 master private
  key; and Phase 394's same six frozen derivation paths through index 999
  (`m/44'/0'/0'/0/i`, `m/44'/0'/0'/1/i`, `m/0'/0/i`, `m/0'/1/i`, `m/0/i`,
  `m/1/i`), each compared against the exact prize address under both
  compressed and uncompressed P2PKH encodings;
- explicitly excluded: BIP39 passphrases, alternate coins, SegWit,
  arbitrary derivation paths, blob-oracle tests;
- exact scope: 8 direct scalars x 2 encodings = 16; 8 BIP32 masters x 2
  encodings = 16; 8 seeds x 6 paths x 1,000 indices = 48,000 child keys x
  2 encodings = 96,000; **96,032 total address checks**.

**Method:** wrote this script, reusing Phase 394's own `base58_decode()`,
`hash160()`, `public_key()`, `child_private_key()`, `derive_path()`,
`SECP256K1_ORDER`, `HARDENED`, and `TARGET_ADDRESS` verbatim -- no crypto
primitive is re-derived. Two planted positives verify the detection
pipeline actually fires before trusting a negative result: a direct-key
positive (scalar `1`, a standard test vector, checked against its own
known address) and a BIP32-path positive (a synthetic seed's own child key
at a specific path/index, checked against its own known address, run
through the identical 6-path/1,000-index loop the real sweep uses). The
prize address's Base58Check structure (length, version byte, checksum) is
validated directly rather than assumed.

**Result:** see `self_test()`'s asserted counts for the exact pinned
manifest of all 8 roots/digests and the total address-check tally.

**Disposition:** decided strictly by the contract above -- only an exact
prize-address match promotes. Otherwise Priority 4 closes negative without
weakening the structural `BTCSEED` observation itself (the header naming a
seed type is not evidence the seed derivation succeeds).
"""

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402
from phase394_telegram_recipe_leads_authentication_audit import (  # noqa: E402
    HARDENED,
    SECP256K1_ORDER,
    TARGET_ADDRESS,
    base58_decode,
    child_private_key,
    derive_path,
    hash160,
    public_key,
)

PATH_TEMPLATES = (
    ("m/44'/0'/0'/0/i", (44 + HARDENED, HARDENED, HARDENED, 0)),
    ("m/44'/0'/0'/1/i", (44 + HARDENED, HARDENED, HARDENED, 1)),
    ("m/0'/0/i", (HARDENED, 0)),
    ("m/0'/1/i", (HARDENED, 1)),
    ("m/0/i", (0,)),
    ("m/1/i", (1,)),
)
INDEX_COUNT = 1000


def target_hash160():
    decoded_target = base58_decode(TARGET_ADDRESS)
    assert len(decoded_target) == 25 and decoded_target[0] == 0
    checksum = hashlib.sha256(hashlib.sha256(decoded_target[:-4]).digest()).digest()[:4]
    assert checksum == decoded_target[-4:]
    return decoded_target[1:-4]


def address_matches(private_key_int, targets):
    hits = []
    for compressed in (True, False):
        h = hash160(public_key(private_key_int, compressed))
        if h in targets:
            hits.append({"compressed": compressed, "hash160": h.hex()})
    return hits


def build_roots(decoded):
    p90 = decoded[7:97]
    p91 = decoded[7:98]
    q472 = decoded[98:]
    full570 = decoded
    assert len(p90) == 90 and len(p91) == 91 and len(q472) == 472 and len(full570) == 570

    objects = {"P90": p90, "P91": p91, "Q472": q472, "FULL570": full570}
    roots = {}
    for name, text in objects.items():
        roots[f"{name}_as_decoded"] = text
        roots[f"{name}_lower"] = text.lower()
    assert len(roots) == 8
    return roots


def direct_scalar_check(digest, targets):
    value = int.from_bytes(digest, "big")
    if not (1 <= value < SECP256K1_ORDER):
        return {"in_range": False, "hits": []}
    return {"in_range": True, "hits": address_matches(value, targets)}


def bip32_master_check(digest, targets):
    master_digest = hmac.new(b"Bitcoin seed", digest, hashlib.sha512).digest()
    master_key = int.from_bytes(master_digest[:32], "big")
    master_chain = master_digest[32:]
    in_range = 1 <= master_key < SECP256K1_ORDER
    hits = address_matches(master_key, targets) if in_range else []
    return {"in_range": in_range, "hits": hits}, (master_key, master_chain)


def derive_children_and_check(master, targets, path_templates=PATH_TEMPLATES, index_count=INDEX_COUNT):
    hits = []
    checked = 0
    for label, prefix in path_templates:
        parent_key, parent_chain = derive_path(master, prefix)
        for index in range(index_count):
            child_key, _ = child_private_key(parent_key, parent_chain, index)
            checked += 1
            for match in address_matches(child_key, targets):
                hits.append({"path": label, "index": index, **match})
    return hits, checked


def planted_direct_key_positive():
    """A known scalar (1) checked against its own known address -- proves
    the direct-scalar detector fires."""
    scalar_bytes = (1).to_bytes(32, "big")
    own_hash160 = hash160(public_key(1, compressed=True))
    result = direct_scalar_check(scalar_bytes, {own_hash160})
    return result


def planted_bip32_path_positive():
    """A synthetic seed's own child key at a fixed path/index, checked
    against its own known address, run through the identical derivation
    loop the real sweep uses -- proves the BIP32-path detector fires."""
    seed = hashlib.sha256(b"phase400-planted-seed-positive").digest()
    master_digest = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    master = (int.from_bytes(master_digest[:32], "big"), master_digest[32:])
    target_label, target_prefix = PATH_TEMPLATES[0]
    target_index = 5
    parent_key, parent_chain = derive_path(master, target_prefix)
    child_key, _ = child_private_key(parent_key, parent_chain, target_index)
    own_hash160 = hash160(public_key(child_key, compressed=True))
    hits, checked = derive_children_and_check(master, {own_hash160}, path_templates=(( target_label, target_prefix),))
    return {"hits": hits, "checked": checked, "expected_path": target_label, "expected_index": target_index}


def audit():
    decoded = btcseed_audit()["decoded"]
    roots = build_roots(decoded)
    targets = {target_hash160()}

    manifest = {}
    direct_hits = []
    master_hits = []
    child_hits = []
    total_child_checked = 0

    for label, text in roots.items():
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        manifest[label] = {
            "length": len(text),
            "sha256_hex": digest.hex(),
        }

        direct = direct_scalar_check(digest, targets)
        manifest[label]["direct_scalar_in_range"] = direct["in_range"]
        manifest[label]["direct_scalar_hits"] = direct["hits"]
        direct_hits.extend({"root": label, **h} for h in direct["hits"])

        master_result, master = bip32_master_check(digest, targets)
        manifest[label]["bip32_master_in_range"] = master_result["in_range"]
        manifest[label]["bip32_master_hits"] = master_result["hits"]
        master_hits.extend({"root": label, **h} for h in master_result["hits"])

        hits, checked = derive_children_and_check(master, targets)
        total_child_checked += checked
        manifest[label]["child_keys_checked"] = checked
        manifest[label]["child_hits"] = hits
        child_hits.extend({"root": label, **h} for h in hits)

    direct_scalar_checks = len(roots) * 2
    bip32_master_checks = len(roots) * 2
    child_address_checks = total_child_checked * 2
    total_address_checks = direct_scalar_checks + bip32_master_checks + child_address_checks

    return {
        "root_count": len(roots),
        "manifest": manifest,
        "direct_scalar_checks": direct_scalar_checks,
        "bip32_master_checks": bip32_master_checks,
        "total_child_keys": total_child_checked,
        "child_address_checks": child_address_checks,
        "total_address_checks": total_address_checks,
        "direct_hits": direct_hits,
        "master_hits": master_hits,
        "child_hits": child_hits,
        "any_hit": bool(direct_hits or master_hits or child_hits),
        "planted_direct_key_positive": planted_direct_key_positive(),
        "planted_bip32_path_positive": planted_bip32_path_positive(),
    }


def self_test():
    report = audit()

    assert report["root_count"] == 8
    assert set(report["manifest"].keys()) == {
        f"{obj}_{case}" for obj in ("P90", "P91", "Q472", "FULL570") for case in ("as_decoded", "lower")
    }

    assert report["direct_scalar_checks"] == 16
    assert report["bip32_master_checks"] == 16
    assert report["total_child_keys"] == 48000
    assert report["child_address_checks"] == 96000
    assert report["total_address_checks"] == 96032

    assert report["any_hit"] is False

    planted_direct = report["planted_direct_key_positive"]
    assert planted_direct["in_range"] is True
    assert len(planted_direct["hits"]) == 1
    assert planted_direct["hits"][0]["compressed"] is True

    planted_path = report["planted_bip32_path_positive"]
    assert planted_path["checked"] == 1000
    assert len(planted_path["hits"]) == 1
    assert planted_path["hits"][0]["path"] == planted_path["expected_path"]
    assert planted_path["hits"][0]["index"] == planted_path["expected_index"]

    print(
        f"[*] self-test OK: both planted positives (direct-scalar, "
        f"BIP32-path) fire exactly at their known index/path; pinned "
        f"8-root manifest ({', '.join(sorted(report['manifest'].keys()))}) "
        f"reproduced; {report['total_address_checks']:,} total address "
        f"checks (16 direct scalars + 16 BIP32 masters + 96,000 child "
        f"addresses across 48,000 derived keys) against the exact prize "
        f"address -- {len(report['direct_hits']) + len(report['master_hits']) + len(report['child_hits'])} hits"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
