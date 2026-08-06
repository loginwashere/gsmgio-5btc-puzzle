#!/usr/bin/env python3
"""Backfill the original six CBC/KDF variants against late-added blobs.

P32TRAILING and URLBLOB were added after the project's original curated
candidate sweeps. They received the 18 extended cipher/KDF variants and the
Key-Wrap sweep, but the current curated corpus had not been independently
rerun against the original fast matrix:

    EVP_BytesToKey {sha256, md5, sha1} x AES-{256,128}-CBC

This script closes only that bookkeeping gap. It deliberately targets
P32TRAILING and URLBLOB, reusing the exact candidate loading, normalization,
newline handling, and validated oracle used by extended_cipher_recheck.py.
"""

from cb_common import (
    BLOBS,
    KDF_VARIANTS,
    QUARANTINED_BLOBS,
    aes_try_open,
    answer_forms,
    keystr_forms,
)
from extended_cipher_recheck import (
    candidate_list_digest,
    load_curated_candidates,
)

TARGET_BLOBS = {
    "P32TRAILING": BLOBS["P32TRAILING"],
    "URLBLOB": QUARANTINED_BLOBS["URLBLOB"],
}


def sweep(candidates):
    tested = set()
    hits = []
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=True):
                if keystr in tested:
                    continue
                tested.add(keystr)
                result = aes_try_open(
                    keystr,
                    kdf_variants=KDF_VARIANTS,
                    blobs=TARGET_BLOBS,
                )
                if result:
                    hits.append(
                        {
                            "candidate": candidate,
                            "form": form,
                            "keystr": keystr,
                            "result": result,
                        }
                    )
    return {"keystrings": len(tested), "hits": hits}


def main():
    candidates = load_curated_candidates()
    digest = candidate_list_digest(candidates)
    result = sweep(candidates)
    operations = result["keystrings"] * len(KDF_VARIANTS) * len(TARGET_BLOBS)
    print(
        f"[*] {len(candidates):,} curated candidates; digest={digest}; "
        f"{result['keystrings']:,} unique keystrings"
    )
    print(
        f"[*] {len(KDF_VARIANTS)} legacy CBC/KDF variants x "
        f"{len(TARGET_BLOBS)} blobs = {operations:,} decrypt operations"
    )
    if not result["hits"]:
        print("[*] no candidate opened P32TRAILING or URLBLOB")
        return
    for hit in result["hits"]:
        tag, plaintext, kdf_label, key_len = hit["result"]
        print(
            f"[+++ HIT] candidate={hit['candidate']!r} form={hit['form']!r} "
            f"keystr={hit['keystr']!r} blob={tag} "
            f"kdf={kdf_label}/{key_len * 8}bit plaintext={plaintext[:500]!r}"
        )


if __name__ == "__main__":
    main()
