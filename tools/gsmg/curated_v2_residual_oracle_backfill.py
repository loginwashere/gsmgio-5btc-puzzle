#!/usr/bin/env python3
"""Close the exact residual oracle gaps introduced by the V2 registry.

Two scopes are intentionally different:

* ``SEED`` and ``IZLKESEEDQPPEN`` were absent from the historical 648 and
  Phase 253 tested them only under Blowfish/Camellia/SEED-CBC.  They need the
  older AES/3DES CBC family plus AES-ECB, AES-CFB/OFB/CTR, and AES Key Wrap.
* The 19 Looking Forward candidates received current CBC coverage in Phase
  256 and Phase 44 already tested non-newline Key-Wrap forms, but the dedicated
  audit predates stream-mode support and did not use newline forms.  Rechecking
  newline-aware ECB/stream/Key-Wrap against the current four blobs is cheap and
  removes the remaining qualification.

Fresco (55) and SafeNet/Luna (62) are not rerun: their recorded dedicated
audits already cover newline-aware CBC, ECB, stream, and Key Wrap against all
four blobs.  This is a 21-candidate residual, not a full V2 sweep.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    answer_forms,
    keystr_forms,
)
from curated_candidate_corpus_audit import active_lines  # noqa: E402
from extended_cipher_recheck import (  # noqa: E402
    OPENSSL_MENU_GAP_EXACT_CANDIDATES,
    WORDLIST_DIR,
    candidate_list_digest,
)


LOOKING_FORWARD_FILE = "looking_forward_candidates.txt"
OLDER_CBC_VARIANTS = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS)

EXPECTED_SEED_CANDIDATES = 2
EXPECTED_SEED_DIGEST = "10da6a91233b3292"
EXPECTED_LOOKING_CANDIDATES = 19
EXPECTED_LOOKING_DIGEST = "bf5116a99829c05f"
EXPECTED_ALL_CANDIDATES = 21
EXPECTED_ALL_DIGEST = "537635ec6fa1ce0f"
EXPECTED_SEED_UNIQUE_PASSPHRASES = 36
EXPECTED_LOOKING_UNIQUE_PASSPHRASES = 792
EXPECTED_ALL_UNIQUE_PASSPHRASES = 828


def scopes():
    seed = tuple(OPENSSL_MENU_GAP_EXACT_CANDIDATES)
    looking = tuple(dict.fromkeys(active_lines(WORDLIST_DIR / LOOKING_FORWARD_FILE)))
    return seed, looking


def unique_passphrases(candidates):
    seen = set()
    ordered = []
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                material = keystring.encode()
                if material not in seen:
                    seen.add(material)
                    ordered.append(material)
    return tuple(ordered)


def scope_report(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    seed, looking = scopes()
    seed_passphrases = unique_passphrases(seed)
    looking_passphrases = unique_passphrases(looking)
    all_candidates = seed + looking
    all_passphrases = tuple(dict.fromkeys(seed_passphrases + looking_passphrases))
    blob_count = len(active_blobs)
    keywrap_derivations = (
        len(all_passphrases) * len(KEY_WRAP_KDF_VARIANTS) * blob_count
    )
    # Every tracked ciphertext is >=24 bytes and divisible by 8, so each KEK
    # derivation attempts RFC3394/default, RFC3394/OpenSSL-IV,
    # RFC5649/default, and RFC5649/OpenSSL-IV.
    keywrap_unwrap_attempts = keywrap_derivations * 4
    return {
        "seed_candidates": seed,
        "seed_candidate_digest": candidate_list_digest(seed),
        "looking_forward_candidates": looking,
        "looking_forward_candidate_digest": candidate_list_digest(looking),
        "all_candidate_count": len(all_candidates),
        "all_candidate_digest": candidate_list_digest(all_candidates),
        "seed_unique_passphrases": len(seed_passphrases),
        "looking_forward_unique_passphrases": len(looking_passphrases),
        "all_unique_passphrases": len(all_passphrases),
        "blobs": tuple(active_blobs),
        "older_cbc_variants": len(OLDER_CBC_VARIANTS),
        "ecb_variants": len(ECB_CIPHER_VARIANTS),
        "stream_variants": len(STREAM_CIPHER_VARIANTS),
        "keywrap_kdf_variants": len(KEY_WRAP_KDF_VARIANTS),
        "cbc_decryptions": len(seed_passphrases) * len(OLDER_CBC_VARIANTS) * blob_count,
        "ecb_decryptions": len(all_passphrases) * len(ECB_CIPHER_VARIANTS) * blob_count,
        "stream_decryptions": len(all_passphrases) * len(STREAM_CIPHER_VARIANTS) * blob_count,
        "keywrap_kdf_blob_derivations": keywrap_derivations,
        "keywrap_effective_unwrap_attempts": keywrap_unwrap_attempts,
        "effective_operations": (
            len(seed_passphrases) * len(OLDER_CBC_VARIANTS) * blob_count
            + len(all_passphrases) * len(ECB_CIPHER_VARIANTS) * blob_count
            + len(all_passphrases) * len(STREAM_CIPHER_VARIANTS) * blob_count
            + keywrap_unwrap_attempts
        ),
        "_seed_passphrases": seed_passphrases,
        "_all_passphrases": all_passphrases,
    }


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    report = scope_report(active_blobs)
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}

    for passphrase in report["_seed_passphrases"]:
        result = aes_try_open_bytes(
            passphrase, kdf_variants=OLDER_CBC_VARIANTS, blobs=active_blobs,
        )
        if result:
            hits["cbc"].append((passphrase, result))

    for passphrase in report["_all_passphrases"]:
        result = aes_try_open_ecb_bytes(passphrase, blobs=active_blobs)
        if result:
            hits["ecb"].append((passphrase, result))
        result = aes_try_open_stream_bytes(passphrase, blobs=active_blobs)
        if result:
            hits["stream"].append((passphrase, result))
        for result in aes_keywrap_try_open_bytes(passphrase, blobs=active_blobs):
            hits["keywrap"].append((passphrase, result))

    report = {key: value for key, value in report.items() if not key.startswith("_")}
    report["hits"] = hits
    report["total_hits"] = sum(map(len, hits.values()))
    return report


def self_test():
    report = scope_report()
    assert (len(report["seed_candidates"]), report["seed_candidate_digest"]) == (
        EXPECTED_SEED_CANDIDATES, EXPECTED_SEED_DIGEST,
    )
    assert (
        len(report["looking_forward_candidates"]),
        report["looking_forward_candidate_digest"],
    ) == (EXPECTED_LOOKING_CANDIDATES, EXPECTED_LOOKING_DIGEST)
    assert (report["all_candidate_count"], report["all_candidate_digest"]) == (
        EXPECTED_ALL_CANDIDATES, EXPECTED_ALL_DIGEST,
    )
    assert report["seed_unique_passphrases"] == EXPECTED_SEED_UNIQUE_PASSPHRASES
    assert report["looking_forward_unique_passphrases"] == EXPECTED_LOOKING_UNIQUE_PASSPHRASES
    assert report["all_unique_passphrases"] == EXPECTED_ALL_UNIQUE_PASSPHRASES
    assert tuple(report["blobs"]) == tuple(BLOBS)
    assert report["older_cbc_variants"] == 24
    assert report["ecb_variants"] == 12
    assert report["stream_variants"] == 36
    assert report["keywrap_kdf_variants"] == 12
    assert report["cbc_decryptions"] == 3456
    assert report["ecb_decryptions"] == 39744
    assert report["stream_decryptions"] == 119232
    assert report["keywrap_kdf_blob_derivations"] == 39744
    assert report["keywrap_effective_unwrap_attempts"] == 158976
    assert report["effective_operations"] == 321408
    print("[*] self-test OK: 21-candidate V2 residual scope, 321,408 effective operations")


def printable_report(report):
    return {key: value for key, value in report.items() if not key.startswith("_")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else printable_report(scope_report())
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            if key != "hits":
                print(f"{key}: {value}")
        if "hits" in report:
            print(f"hits: {report['hits']}")


if __name__ == "__main__":
    main()
