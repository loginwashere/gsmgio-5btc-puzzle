#!/usr/bin/env python3
"""Offline verification of the 2026-11-04 Naddiseo fork review.

Reads the saved GitHub API snapshot, never executes downloaded code, and
reproduces only the specific public claims reviewed in the accompanying note.
Run from any directory; JSON is emitted to stdout.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from data import (
    COSMIC_BLOB_B64, DBBI, FAED, P32_TRAILING_BLOB_B64,
    PHASE32_BLOB_B64, PHASE32_PASSWORD, SALPHASEION_BLOB_B64,
)
from phase386_btcseed_bifid_faed_decode_audit import build_grid, bifid_decrypt
from phase546_prefix_selectivity_curve import arm_a_perms, prefix_codes, encode
from phase515_ternary_decomposition_square_matrix_audit import expand

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "doc/evidence/NADDISEO_UPDATE_REVIEW_2026_11_04.json"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
TARGETS = {"1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe", "17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_encode(body):
    data = body + hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    number, output = int.from_bytes(data, "big"), ""
    while number:
        number, digit = divmod(number, 58)
        output = B58[digit] + output
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + output


def wif(key, compressed=False):
    return check_encode(b"\x80" + key + (b"\x01" if compressed else b""))


def addresses(key):
    point = ec.derive_private_key(int.from_bytes(key, "big"), ec.SECP256K1()).public_key().public_numbers()
    x, y = point.x.to_bytes(32, "big"), point.y.to_bytes(32, "big")
    result = {}
    for kind, pub in [("compressed", bytes([2 + (point.y & 1)]) + x), ("uncompressed", b"\x04" + x + y)]:
        h160 = hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest()
        result[kind] = check_encode(b"\x00" + h160)
    return result


def decrypt(blob, password, digest="md5"):
    raw = base64.b64decode(blob, validate=True)
    assert raw[:8] == b"Salted__" and len(raw[16:]) % 16 == 0
    material, previous = b"", b""
    while len(material) < 48:
        previous = hashlib.new(digest, previous + password + raw[8:16]).digest()
        material += previous
    return decrypt_raw(raw[16:], material[:32], material[32:48])


def decrypt_raw(ciphertext, key, iv):
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    return dec.update(ciphertext) + dec.finalize()


def inspect(plaintext):
    pad = plaintext[-1]
    valid = 1 <= pad <= 16 and plaintext[-pad:] == bytes([pad]) * pad
    body = plaintext[:-pad] if valid else plaintext
    counts = Counter(body)
    return {
        "valid_pkcs7": valid, "last_byte": pad,
        "body_length": len(body), "body_sha256": sha(body),
        "ascii_printable_with_whitespace": sum(32 <= v < 127 or v in (9, 10, 13) for v in body) / len(body),
        "empirical_entropy_bits_per_byte": -sum((n / len(body)) * math.log2(n / len(body)) for n in counts.values()),
    }


def coverage(snapshot):
    threads = snapshot["issues_and_pr_threads"]
    assert len(threads) == 17
    mismatches = [{"issue": t["number"], "advertised": t["comments"], "returned": len(t["thread"])}
                  for t in threads if len(t["thread"]) != t["comments"]]
    assert mismatches == [{"issue": 2, "advertised": 2, "returned": 1}]
    assert sum(len(t["thread"]) for t in threads) == 36
    assert len({c["id"] for t in threads for c in t["thread"]}) == 36
    prs = snapshot["pull_requests"]
    assert len(prs) == 7 and all(len(p["files"]) == p["changed_files"] for p in prs)
    assert all(p["state"] == "closed" for p in prs)
    old = {x["path"]: x["sha"] for x in snapshot["baseline_tree"]["tree"] if x["type"] == "blob"}
    new = {x["path"]: x["sha"] for x in snapshot["current_tree"]["tree"] if x["type"] == "blob"}
    assert not snapshot["baseline_tree"]["truncated"] and not snapshot["current_tree"]["truncated"]
    changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
    added = sorted(new.keys() - old.keys())
    assert changed == ["README.md", "unverified/README.md"]
    assert added == ["index.html", "unverified/11110.md", "unverified/phase0_fefefe_parity.md", "unverified/phase0_yellow_blue_counts.md"]
    return {"head": snapshot["head"], "baseline_files": len(old), "current_files": len(new),
            "unchanged_blobs": sum(old[k] == new[k] for k in old.keys() & new.keys()),
            "modified": changed, "added": added, "deleted": sorted(old.keys() - new.keys()),
            "commits_since_baseline": snapshot["compare"]["ahead_by"],
            "open_ordinary_issues": [t["number"] for t in threads if not t["pull_request"] and t["state"] == "open"],
            "ordinary_issues": sum(not bool(t["pull_request"]) for t in threads),
            "accessible_conversation_comments": 36, "comment_count_mismatches": mismatches,
            "closed_prs": len(prs),
            "merged_prs": [p["number"] for p in prs if p["merged"]]}


def main():
    snapshot = json.loads(SNAPSHOT.read_text())
    # Independent controls before inspecting unknown plaintext.
    known = inspect(decrypt(PHASE32_BLOB_B64, PHASE32_PASSWORD.encode(), "sha256"))
    assert known["body_sha256"] == "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"
    assert addresses((1).to_bytes(32, "big")) == {
        "compressed": "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
        "uncompressed": "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm"}
    chain1 = decrypt(SALPHASEION_BLOB_B64, snapshot["claim_inputs"]["chain1_password"].encode())
    c1 = inspect(chain1)
    assert c1["valid_pkcs7"] and c1["last_byte"] == 1
    assert c1["body_sha256"] == snapshot["claim_inputs"]["chain1_expected_sha256"]
    chain2 = decrypt(P32_TRAILING_BLOB_B64, wif(chain1[:32]).encode())
    c2 = inspect(chain2)
    assert c2["valid_pkcs7"] and c2["last_byte"] == 1
    assert c2["body_sha256"] == snapshot["claim_inputs"]["chain2_expected_sha256"]
    issue17 = next(t for t in snapshot["issues_and_pr_threads"] if t["number"] == 17)
    assert chain2[:32].hex() in issue17["body"] and chain2[32:64].hex() in issue17["body"]
    assert chain2[64:79].hex() in issue17["body"]
    candidates = {"C1": chain1[:32], "C2": chain1[32:64], "S1": chain2[:32], "S2": chain2[32:64]}
    address_checks = {name: addresses(key) for name, key in candidates.items()}
    assert not any(TARGETS.intersection(a.values()) for a in address_checks.values())
    continuations = []
    for name in ["C2", "S1", "S2"]:
        for compressed in [False, True]:
            pw = wif(candidates[name], compressed)
            continuations.append({"key": name, "compressed": compressed,
                                  "wif": pw, **inspect(decrypt(COSMIC_BLOB_B64, pw.encode()))})
    assert not any(r["valid_pkcs7"] for r in continuations)
    # Closed issue #6's follow-up supplied these exact AES parameters.
    bad_cosmic = inspect(decrypt_raw(base64.b64decode(COSMIC_BLOB_B64)[16:],
        bytes.fromhex("6ac438facf366702b60d6dfcebd39815b582f19b591b3fdf69240c6966f4fc23"),
        bytes.fromhex("c6ff2e39d98843bc3c26b8a33a15b5c9")))
    assert bad_cosmic["body_sha256"] == "4f7a1e4efe4bf6c5581e32505c019657cb7b030e90232d33f011aca6a5e9c081"
    assert bad_cosmic["last_byte"] == 1 and bad_cosmic["body_length"] == 1327
    alphabet, grid, pos = build_grid(DBBI)
    decoded = bifid_decrypt(FAED, pos, grid)
    assert decoded.startswith("BTCSEED") and decoded.count("Z") == 1 and decoded.index("Z") == 97
    assert set(decoded[::2]) == set("DBCE")
    perms = arm_a_perms()
    codes = prefix_codes(perms)
    matches = ["".join("ABCDEFGHI"[int(i)] for i in row[:9]) for row in perms[codes == encode("BTCSEED")]]
    assert len(matches) == 8 and len(np.unique(codes)) == 73097
    colour_bits = "".join(str(ord(c) & 1) for c in "gsmg.io/theseedisplanted")
    assert colour_bits == "111101110011110110010010"
    expansion_sizes = {"DBBI": len(expand(DBBI)), "FAED": len(expand(FAED))}
    assert expansion_sizes == {"DBBI": 169, "FAED": 1225}
    result = {
        "snapshot_sha256": sha(SNAPSHOT.read_bytes()), "coverage": coverage(snapshot),
        "controls": {"phase32_exact_plaintext": known, "secp256k1_scalar_1": "pass"},
        "issue17": {"chain1": c1, "chain2": c2, "chain1_first_key_wif": wif(chain1[:32]),
                    "address_checks": address_checks, "cosmic_wif_md5_continuations": continuations,
                    "disposition": "Public bytes reproduce; neither 79-byte body has independent structure or a target-address match. Repeated derived hashes are not independent authentication."},
        "issue6_exact_key_iv": bad_cosmic,
        "issue13": {"alphabet": alphabet, "length": len(decoded), "output_sha256": sha(decoded.encode()),
                    "z_zero_based": decoded.index("Z"), "odd_one_based_output_symbols": sorted(set(decoded[::2])),
                    "prefix_permutations": len(perms), "btcseed_matching_keys": matches,
                    "distinct_prefixes": len(np.unique(codes)),
                    "disposition": "Reproduces existing Phase 386/546 results; no new tail decode supplied in thread."},
        "issue14_expanded_sizes": expansion_sizes,
        "pr16": {"colour_bits": colour_bits,
                 "11110_zero_based_offsets": [i for i in range(len(colour_bits) - 4) if colour_bits[i:i+5] == "11110"],
                 "fe_low_five_bits": format(0xfe & 31, "05b"),
                 "fe_rotate_left_three": format(((0xfe << 3) | (0xfe >> 5)) & 255, "08b"),
                 "disposition": "Arithmetic holds for a left rotation; no tap polynomial is specified for a feedback shift. EO11110 is already discussed in local README; no new endgame operand follows."},
        "limitations": ["Only the six stated WIF/EVP-MD5 Cosmic continuations were replayed, not issue17's unspecified wider sweep.",
                        "PR15's campaign totals and broad closure claims were reviewed as claims, not independently rerun.",
                        "A short arbitrary binary payload is not disproved by low printability alone; these outputs lack independent confirmation."]}
    print(json.dumps(result, indent=2) )


if __name__ == "__main__":
    main()
