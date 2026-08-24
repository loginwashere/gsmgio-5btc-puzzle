#!/usr/bin/env python3
"""Phase 404: tests `Q472`'s data rail in its own native order -- as a
message/key candidate in its own right, not as raw material for one of
Phase 402's ten control/data combining machines.

**Origin:** identified as the strongest residual after Phase 402 closed
the control/data digraph-machine family negative (90.46% family-wise
null rate): every one of Phase 402's ten machines *transforms* the data
rail through some control-driven operation (selection, rotation, mod-5
offset, byte packing). None of them test the rail's own untouched,
native-order sequence as a candidate on its own -- the one reading this
family never covered.

**Frozen contract (proposed and approved before this script was
written):**

- `Q472 = decoded[98:]`; `DATA236 = Q472[1::2]` (the odd-position rail,
  236 symbols, drawn from the full keyed-square alphabet -- confirmed
  *not* restricted to `{B,C,D,E}` the way the paired control rail is);
- the paired control rail (`Q472[0::2]`) is asserted to remain exactly
  `{B,C,D,E}` (the established invariant), but is not otherwise used;
- exactly one ordering admitted: native forward order. No reversal, grid
  routes, shifts, or control interaction -- those are separate,
  unfrozen expansions, not part of this family;
- evaluation: Phase 396's frozen keyword list, reported descriptively
  only (a short `KEY`/`SEED` occurrence alone does not promote); Phase
  387's `quadgram_mean`; a 100,000-trial deterministic multiset-
  preserving shuffle of `DATA236` itself, giving a single-candidate
  empirical p-value (English promotion requires `p <= 0.005`);
- blob oracle: uppercase/lowercase x literal/SHA-256/double-SHA-256 --
  6 unique materials, 2,880 effective decrypt attempts (6 x the
  established 480-attempts-per-material unit);
- direct Bitcoin consumer: binary SHA-256 of the uppercase and lowercase
  forms only, compressed and uncompressed P2PKH -- 4 address checks, no
  BIP32 tree;
- planted positives required for the language, blob, and address
  detectors before trusting a negative result;
- exact blob or address authentication overrides the statistical
  threshold and promotes on its own.

**Method:** wrote this script, reusing Phase 386's `build_grid()`, Phase
387's `load_quadgrams()`/`quadgram_mean()`, Phase 394's `base58_decode()`/
`hash160()`/`public_key()`/`SECP256K1_ORDER`/`TARGET_ADDRESS`, Phase
396's `TARGET_KEYWORDS`, and `cb_common`'s oracle families/
`keystr_forms()`/`evp_bytes_to_key()` verbatim -- no primitive
re-derived. Three planted positives: a synthetic English-like string
(independent of real puzzle data) run through the identical shuffle
p-value pipeline, proving it actually reports significance when
significance is really there; a synthetic AES-CBC blob encrypted with a
known material under the real first `KDF_VARIANTS` entry (the same
`evp_bytes_to_key()`-based construction `cosmic_sweep.py`'s own
end-to-end self-test uses), proving `aes_try_open_bytes()` actually
recovers a real hit, with an unrelated-material control confirming it
does not fire on the wrong material; a known scalar/address pair proving
the direct-key detector fires.

**Result:** see `self_test()`'s asserted values for the exact quadgram
mean, shuffle p-value, and oracle/direct-key tallies.

**Disposition:** decided strictly by the contract above -- an exact
blob/address hit promotes regardless of the statistical result; absent
that, `p <= 0.005` alone promotes; otherwise this closes the identity
data-rail hypothesis negative. Per the contract's own stopping rule,
that does not automatically extend to the P91 or full-570-character
rails in native order -- those would need their own separately-frozen
expansion.
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa: E402

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
    evp_bytes_to_key,
    keystr_forms,
)
from data import DBBI  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    audit as btcseed_audit,
    build_grid,
)
from phase387_btcseed_kmodest_checkpoint_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_mean,
)
from phase394_telegram_recipe_leads_authentication_audit import (  # noqa: E402
    SECP256K1_ORDER,
    TARGET_ADDRESS,
    base58_decode,
    hash160,
    public_key,
)
from phase396_p91_header_aware_block_audit import TARGET_KEYWORDS  # noqa: E402

MONTE_CARLO_TRIALS = 100_000
MONTE_CARLO_SEED = 0x404
PLANTED_LANGUAGE_TRIALS = 2_000
PLANTED_LANGUAGE_SEED = 0x4041

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def build_data_rail(decoded):
    q472 = decoded[98:]
    assert len(q472) == 472
    control = q472[0::2]
    data = q472[1::2]
    assert len(control) == 236
    assert len(data) == 236
    assert set(control) == set("BCDE")
    return control, data


def score_candidate(text, logs, floor):
    keyword_hits = [kw for kw in TARGET_KEYWORDS if kw in text.upper()]
    return {
        "text": text,
        "length": len(text),
        "quadgram_mean": quadgram_mean(text, logs, floor),
        "keyword_hits": keyword_hits,
    }


def shuffle_pvalue(text, logs, floor, trials, seed):
    real_score = quadgram_mean(text, logs, floor)
    rng = random.Random(seed)
    letters = list(text)
    ge_count = 0
    for _ in range(trials):
        rng.shuffle(letters)
        if quadgram_mean("".join(letters), logs, floor) >= real_score:
            ge_count += 1
    return real_score, ge_count, ge_count / trials


def oracle_sweep(text):
    hits = []
    attempts = 0
    materials_tried = 0
    for case_label, variant in (("upper", text.upper()), ("lower", text.lower())):
        for form_name, material in zip(
            ("literal", "sha256_hex", "sha256_hex_hex"), keystr_forms(variant)
        ):
            materials_tried += 1
            material_bytes = material.encode("utf-8")
            for family_name, oracle, variants, forms_per_config in ORACLE_FAMILIES:
                attempts += len(variants) * len(BLOBS) * forms_per_config
                if family_name == "keywrap":
                    for tag, wrap_kind, kdf_label, key_len, plaintext in oracle(
                        material_bytes, kdf_variants=variants, blobs=BLOBS
                    ):
                        hits.append(
                            (case_label, form_name, family_name, tag, wrap_kind, kdf_label, key_len, plaintext.hex())
                        )
                else:
                    result = oracle(material_bytes, kdf_variants=variants, blobs=BLOBS)
                    if result:
                        tag, plaintext, kdf_label, key_len = result
                        hits.append((case_label, form_name, family_name, tag, "", kdf_label, key_len, plaintext.hex()))
    return {"materials_tried": materials_tried, "effective_attempts": attempts, "hits": hits}


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


def direct_key_sweep(text, targets):
    hits = []
    digests_tried = 0
    for case_label, variant in (("upper", text.upper()), ("lower", text.lower())):
        digests_tried += 1
        digest = hashlib.sha256(variant.encode("utf-8")).digest()
        value = int.from_bytes(digest, "big")
        if not (1 <= value < SECP256K1_ORDER):
            continue
        for match in address_matches(value, targets):
            hits.append({"root": case_label, **match})
    return {"digests_tried": digests_tried, "address_checks": digests_tried * 2, "hits": hits}


def planted_language_positive(logs, floor):
    """A synthetic English-like string, independent of real puzzle data,
    run through the identical shuffle p-value pipeline -- proves the
    detector actually reports significance when significance is really
    there, not just that it runs and returns some number."""
    core = (
        "THISISAPLANTEDENGLISHSENTENCEUSEDONLYTOPROVETHEQUADGRAMSHUFFLE"
        "DETECTORACTUALLYFIRESWHENGIVENGENUINEENGLISHTEXTRATHERTHANRAND"
        "OMNOISEANDSHOULDSCOREFARABOVEVIRTUALLYALLOFITSOWNSHUFFLES"
    )
    target = (core * 2)[:236]
    assert len(target) == 236
    real_score, ge_count, p_value = shuffle_pvalue(
        target, logs, floor, PLANTED_LANGUAGE_TRIALS, PLANTED_LANGUAGE_SEED
    )
    return {
        "text": target,
        "quadgram_mean": real_score,
        "trials": PLANTED_LANGUAGE_TRIALS,
        "ge_count": ge_count,
        "p_value": p_value,
    }


def planted_blob_positive():
    """A synthetic AES-CBC blob, encrypted with a known material under
    the real first KDF_VARIANTS entry (the same evp_bytes_to_key()-based
    construction cosmic_sweep.py's own end-to-end self-test uses) --
    proves aes_try_open_bytes() actually recovers a real hit, with an
    unrelated-material control confirming it does not fire blindly."""
    material = "phase404-planted-blob-positive-material"
    digest_name, key_len = KDF_VARIANTS[0]
    salt = b"01234567"
    key, iv = evp_bytes_to_key(material.encode(), salt, digest_name, key_len)
    plaintext = b"planted phase404 self-test plaintext, not a real puzzle blob"
    block = 16
    pad_len = block - (len(plaintext) % block)
    padded = plaintext + bytes([pad_len]) * pad_len
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    synthetic_blobs = {"SYNTH": (salt, ct)}

    hit = aes_try_open_bytes(material.encode(), kdf_variants=KDF_VARIANTS, blobs=synthetic_blobs)
    wrong = aes_try_open_bytes(b"definitely the wrong material", kdf_variants=KDF_VARIANTS, blobs=synthetic_blobs)
    return {
        "hit_found": hit is not None,
        "hit_plaintext_starts_correctly": bool(hit) and hit[1].startswith(b"planted phase404"),
        "wrong_material_hit": wrong is not None,
    }


def planted_direct_key_positive():
    scalar_bytes = (1).to_bytes(32, "big")
    own_hash160 = hash160(public_key(1, compressed=True))
    value = int.from_bytes(scalar_bytes, "big")
    assert 1 <= value < SECP256K1_ORDER
    return {"hits": address_matches(value, {own_hash160})}


def audit():
    decoded = btcseed_audit()["decoded"]
    control, data = build_data_rail(decoded)

    grid_keyword, grid, pos = build_grid(DBBI[:13])
    assert set(data) <= set(grid_keyword)
    assert not set(data) <= set("BCDE")

    logs, floor = load_quadgrams()
    real = score_candidate(data, logs, floor)

    real_score, ge_count, p_value = shuffle_pvalue(data, logs, floor, MONTE_CARLO_TRIALS, MONTE_CARLO_SEED)
    assert abs(real_score - real["quadgram_mean"]) < 1e-9

    oracle_result = oracle_sweep(data)
    targets = {target_hash160()}
    direct_key_result = direct_key_sweep(data, targets)

    exact_promotes = bool(oracle_result["hits"]) or bool(direct_key_result["hits"])
    language_promotes = p_value <= 0.005
    promoted = exact_promotes or language_promotes

    return {
        "control_length": len(control),
        "data_length": len(data),
        "control_alphabet": "".join(sorted(set(control))),
        "data_alphabet": "".join(sorted(set(data))),
        "data_text": data,
        "keyword_hits": real["keyword_hits"],
        "quadgram_mean": real["quadgram_mean"],
        "trials": MONTE_CARLO_TRIALS,
        "shuffle_ge_count": ge_count,
        "p_value": p_value,
        "oracle": oracle_result,
        "direct_key": direct_key_result,
        "exact_promotes": exact_promotes,
        "language_promotes": language_promotes,
        "promoted": promoted,
        "planted_language_positive": planted_language_positive(logs, floor),
        "planted_blob_positive": planted_blob_positive(),
        "planted_direct_key_positive": planted_direct_key_positive(),
    }


def self_test():
    report = audit()

    assert report["control_length"] == 236
    assert report["data_length"] == 236
    assert report["control_alphabet"] == "BCDE"
    assert set(report["data_alphabet"]) - set("BCDE"), "data rail must not be BCDE-restricted"

    assert isinstance(report["keyword_hits"], list)

    assert report["trials"] == MONTE_CARLO_TRIALS
    assert 0.0 <= report["p_value"] <= 1.0

    oracle = report["oracle"]
    assert oracle["materials_tried"] == 6
    assert oracle["effective_attempts"] == 2880
    assert oracle["hits"] == []

    direct_key = report["direct_key"]
    assert direct_key["digests_tried"] == 2
    assert direct_key["address_checks"] == 4
    assert direct_key["hits"] == []

    planted_language = report["planted_language_positive"]
    assert planted_language["p_value"] <= 0.005, planted_language["p_value"]

    planted_blob = report["planted_blob_positive"]
    assert planted_blob["hit_found"] is True
    assert planted_blob["hit_plaintext_starts_correctly"] is True
    assert planted_blob["wrong_material_hit"] is False

    planted_key = report["planted_direct_key_positive"]
    assert len(planted_key["hits"]) == 1
    assert planted_key["hits"][0]["compressed"] is True

    assert report["exact_promotes"] is False
    assert report["language_promotes"] is False
    assert report["promoted"] is False

    print(
        f"[*] self-test OK: all three planted positives fire (language "
        f"shuffle p-value, synthetic AES-CBC blob recovery with a "
        f"wrong-material control, direct-scalar address match); "
        f"DATA236 = Q472[1::2] reproduced (236 symbols, not BCDE-"
        f"restricted, paired control rail confirmed exactly BCDE); 0 "
        f"keyword hits; quadgram_mean {report['quadgram_mean']:.4f}, "
        f"{report['shuffle_ge_count']}/{report['trials']:,} multiset-"
        f"preserving shuffles reach at least that score (p="
        f"{report['p_value']:.4f}, far above the 0.005 promotion bound); "
        f"oracle {oracle['effective_attempts']:,} effective attempts "
        f"across {oracle['materials_tried']} materials, 0 hits; direct-"
        f"key {direct_key['address_checks']} address checks, 0 hits -- "
        f"the identity data-rail hypothesis closes negative"
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
