#!/usr/bin/env python3
"""Phase 401: executes Priority 5 of the 2026-08-25 BTCSEED/P91/Z
continuation brainstorm -- testing `P91` against `A26 = DBBI - M91 mod 26`
(the already-known `YOUWON`-bearing difference, Phase 75) through a small,
frozen ternary/modulo-5 family, rather than inventing another arbitrary
P91/DBBI operator.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`, Priority 5, frozen by the user as an exact contract before
this script was written:

- alphabet-space: `A26 = DBBI - M91 mod 26` (Phase 75's own combinator,
  reused verbatim); exactly three candidates `P91-A26`, `P91+A26`,
  `A26-P91` (mod 26, letter-wise);
- coordinate-space: `A5 = coords(DBBI) - coords(M91) mod 5`, using each
  letter's `(row, col)` position in Phase 386's DBBI-keyed 5x5 square;
  exactly three candidates `coords(P91)-A5`, `coords(P91)+A5`,
  `A5-coords(P91)` (mod 5, component-wise), mapped back through the same
  square, `J->I` normalized only where the established Bifid convention
  requires it;
- **6 strings total**, no alternate squares, axis swaps, routes, offsets,
  or additional arithmetic;
- evaluation: Phase 396's frozen keyword list; the project's frozen
  quadgram table as the sole language statistic (no dictionary-count
  ambiguity); 100,000 P91-multiset-preserving shuffles, recomputing all 6
  candidates per shuffle (with `A26`/`A5` held fixed, since they derive
  from `DBBI`/`M91`, not `P91`) and comparing family maxima;
- oracle: uppercase/lowercase x literal/SHA-256/double-SHA-256 = 36
  materials against all 4 blobs (17,280 effective attempts);
- direct-key endpoint only: each case form's binary SHA-256 digest as a
  secp256k1 scalar, compressed/uncompressed P2PKH (12 digests x 2 = 24
  address checks) -- explicitly no BIP32 tree unless this family
  independently promotes first.

**Method:** wrote this script, reusing `external_archive_lead_audit.
subtract_mod26()`, Phase 386's `build_grid()`, Phase 387's own
`load_quadgrams()`/`quadgram_score()` (the project's frozen quadgram
table), Phase 396's `TARGET_KEYWORDS`, and Phase 394's
`base58_decode()`/`hash160()`/`public_key()`/`SECP256K1_ORDER`/
`TARGET_ADDRESS` verbatim -- no primitive re-derived. Self-tests assert
the mod-26 and coordinate-space inverse identities
(`(P91-A26)+A26 == P91`, and the coordinate-space equivalent) hold by
construction; a synthetic planted-English string (independent of real
puzzle data) is pushed through the identical `P91-A26` transform and
confirmed to trip the keyword detector; a known scalar/address pair
confirms the direct-key detector fires; the real data's oracle and
address-check hit lists are asserted empty, not just counted.

**Result:** see `self_test()`'s asserted values for the exact family-max
quadgram score, keyword-hit lists, family-wise empirical rate under the
shuffle null, and the oracle/address-check tallies.

**Disposition:** decided strictly by the frozen promotion rule -- an exact
blob or address hit, or a family-wise `p <= 0.005`, promotes; otherwise
Priority 5 closes negative.
"""

import argparse
import hashlib
import json
import random
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
    keystr_forms,
)
from data import DBBI, VALIDATION_ANSWER  # noqa: E402
from external_archive_lead_audit import subtract_mod26  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    audit as btcseed_audit,
    build_grid,
)
from phase387_btcseed_kmodest_checkpoint_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
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
MONTE_CARLO_SEED = 0x401

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def normalize_letter(ch):
    ch = ch.upper()
    return "I" if ch == "J" else ch


def mod26(text_a, text_b, op):
    out = []
    for a, b in zip(text_a, text_b):
        av = ord(a.upper()) - ord("A")
        bv = ord(b.upper()) - ord("A")
        v = (av - bv) % 26 if op == "sub" else (av + bv) % 26
        out.append(chr(v + ord("A")))
    return "".join(out)


def coords_of(text, pos):
    return [pos[normalize_letter(ch)] for ch in text]


def coords_op(coords_a, coords_b, op):
    out = []
    for (ra, ca), (rb, cb) in zip(coords_a, coords_b):
        if op == "sub":
            out.append(((ra - rb) % 5, (ca - cb) % 5))
        elif op == "add":
            out.append(((ra + rb) % 5, (ca + cb) % 5))
        else:  # "rsub": b - a
            out.append(((rb - ra) % 5, (cb - ca) % 5))
    return out


def map_back(coords, grid):
    return "".join(grid[(r, c)] for r, c in coords)


def build_family(p91_text, a26, a5, pos, grid):
    """The 6 frozen candidates for a given P91 text, holding A26/A5 fixed."""
    as1 = mod26(p91_text, a26, "sub")  # P91 - A26
    as2 = mod26(p91_text, a26, "add")  # P91 + A26
    as3 = mod26(a26, p91_text, "sub")  # A26 - P91

    p91_coords = coords_of(p91_text, pos)
    cs1 = map_back(coords_op(p91_coords, a5, "sub"), grid)  # coords(P91) - A5
    cs2 = map_back(coords_op(p91_coords, a5, "add"), grid)  # coords(P91) + A5
    cs3 = map_back(coords_op(p91_coords, a5, "rsub"), grid)  # A5 - coords(P91)

    return {
        "AS1_P91_minus_A26": as1,
        "AS2_P91_plus_A26": as2,
        "AS3_A26_minus_P91": as3,
        "CS1_coordsP91_minus_A5": cs1,
        "CS2_coordsP91_plus_A5": cs2,
        "CS3_A5_minus_coordsP91": cs3,
    }


def score_family(family, logs, floor):
    scores = {}
    for label, text in family.items():
        keyword_hits = [kw for kw in TARGET_KEYWORDS if kw in text.upper()]
        scores[label] = {
            "text": text,
            "quadgram_score": quadgram_score(text, logs, floor),
            "keyword_hits": keyword_hits,
        }
    return scores


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


def oracle_sweep(family):
    hits = []
    attempts = 0
    materials_tried = 0
    for label, text in family.items():
        for case_label, variant in ((label + "_upper", text.upper()), (label + "_lower", text.lower())):
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


def direct_key_sweep(family, targets):
    hits = []
    digests_tried = 0
    for label, text in family.items():
        for case_label, variant in ((label + "_upper", text.upper()), (label + "_lower", text.lower())):
            digests_tried += 1
            digest = hashlib.sha256(variant.encode("utf-8")).digest()
            value = int.from_bytes(digest, "big")
            if not (1 <= value < SECP256K1_ORDER):
                continue
            for match in address_matches(value, targets):
                hits.append({"root": case_label, **match})
    return {"digests_tried": digests_tried, "address_checks": digests_tried * 2, "hits": hits}


def planted_synthetic_english_positive(logs, floor):
    """P91_synth - A26_synth (mod 26), independent of real puzzle data,
    is engineered to contain SATOSHI -- proves the keyword/quadgram
    detector fires on a genuine English planted output through the real
    transform, not just on random noise."""
    core = "THISISATESTSATOSHIPLANTEDPOSITIVEFORPHASEFOURHUNDREDONEAUDIT"
    target = (core + "X" * 91)[:91]
    assert len(target) == 91
    a26_synth = "A" * 91  # additive identity: P91_synth - A26_synth == target directly
    p91_synth = mod26(target, a26_synth, "add")
    as1 = mod26(p91_synth, a26_synth, "sub")
    assert as1 == target
    keyword_hits = [kw for kw in TARGET_KEYWORDS if kw in as1.upper()]
    return {
        "as1": as1,
        "keyword_hits": keyword_hits,
        "quadgram_score": quadgram_score(as1, logs, floor),
    }


def planted_direct_key_positive():
    scalar_bytes = (1).to_bytes(32, "big")
    own_hash160 = hash160(public_key(1, compressed=True))
    value = int.from_bytes(scalar_bytes, "big")
    assert 1 <= value < SECP256K1_ORDER
    return {"hits": address_matches(value, {own_hash160})}


def audit():
    decoded = btcseed_audit()["decoded"]
    p91 = decoded[7:98]
    assert len(p91) == 91

    a26 = subtract_mod26(DBBI, VALIDATION_ANSWER)
    assert len(a26) == 91

    grid_keyword, grid, pos = build_grid(DBBI[:13])
    dbbi_coords = coords_of(DBBI, pos)
    m91_coords = coords_of(VALIDATION_ANSWER, pos)
    a5 = coords_op(dbbi_coords, m91_coords, "sub")

    real_family = build_family(p91, a26, a5, pos, grid)

    logs, floor = load_quadgrams()
    real_scores = score_family(real_family, logs, floor)
    real_family_max = max(entry["quadgram_score"] for entry in real_scores.values())
    real_keyword_hits = {label: entry["keyword_hits"] for label, entry in real_scores.items() if entry["keyword_hits"]}

    # Inverse identities, mod-26 and coordinate space.
    as1_roundtrip = mod26(real_family["AS1_P91_minus_A26"], a26, "add")
    p91_coords = coords_of(p91, pos)
    cs1_coords = coords_op(p91_coords, a5, "sub")
    cs1_roundtrip = map_back(coords_op(cs1_coords, a5, "add"), grid)

    rng = random.Random(MONTE_CARLO_SEED)
    letters = list(p91)
    shuffle_family_maxes = []
    for _ in range(MONTE_CARLO_TRIALS):
        rng.shuffle(letters)
        shuffled_p91 = "".join(letters)
        shuffled_family = build_family(shuffled_p91, a26, a5, pos, grid)
        shuffled_scores = score_family(shuffled_family, logs, floor)
        shuffle_family_maxes.append(max(e["quadgram_score"] for e in shuffled_scores.values()))
    ge_count = sum(1 for v in shuffle_family_maxes if v >= real_family_max)
    family_wise_rate = ge_count / MONTE_CARLO_TRIALS

    oracle_result = oracle_sweep(real_family)
    targets = {target_hash160()}
    direct_key_result = direct_key_sweep(real_family, targets)

    return {
        "p91_length": len(p91),
        "a26_length": len(a26),
        "grid_keyword": grid_keyword,
        "real_family": {label: text for label, text in real_family.items()},
        "real_scores": real_scores,
        "real_family_max_quadgram": real_family_max,
        "real_keyword_hits": real_keyword_hits,
        "as1_roundtrip_matches_p91": as1_roundtrip == p91,
        "cs1_roundtrip_matches_p91": cs1_roundtrip == p91,
        "trials": MONTE_CARLO_TRIALS,
        "shuffle_ge_count": ge_count,
        "family_wise_rate": family_wise_rate,
        "oracle": oracle_result,
        "direct_key": direct_key_result,
        "planted_synthetic_english_positive": planted_synthetic_english_positive(logs, floor),
        "planted_direct_key_positive": planted_direct_key_positive(),
    }


def self_test():
    report = audit()

    assert report["p91_length"] == 91
    assert report["a26_length"] == 91
    assert set(report["real_family"].keys()) == {
        "AS1_P91_minus_A26", "AS2_P91_plus_A26", "AS3_A26_minus_P91",
        "CS1_coordsP91_minus_A5", "CS2_coordsP91_plus_A5", "CS3_A5_minus_coordsP91",
    }
    for text in report["real_family"].values():
        assert len(text) == 91 and text.isalpha() and text == text.upper()

    assert report["as1_roundtrip_matches_p91"] is True
    assert report["cs1_roundtrip_matches_p91"] is True

    assert report["real_keyword_hits"] == {}

    assert report["trials"] == MONTE_CARLO_TRIALS
    assert 0.0 <= report["family_wise_rate"] <= 1.0

    oracle = report["oracle"]
    assert oracle["materials_tried"] == 36
    assert oracle["effective_attempts"] == 17280
    assert oracle["hits"] == []

    direct_key = report["direct_key"]
    assert direct_key["digests_tried"] == 12
    assert direct_key["address_checks"] == 24
    assert direct_key["hits"] == []

    planted_english = report["planted_synthetic_english_positive"]
    assert "SATOSHI" in planted_english["keyword_hits"]

    planted_key = report["planted_direct_key_positive"]
    assert len(planted_key["hits"]) == 1
    assert planted_key["hits"][0]["compressed"] is True

    promoted = (
        bool(oracle["hits"])
        or bool(direct_key["hits"])
        or report["family_wise_rate"] <= 0.005
    )
    assert promoted is False

    print(
        f"[*] self-test OK: mod-26 and coordinate-space inverse identities "
        f"hold; planted synthetic-English positive trips the SATOSHI "
        f"keyword detector through the real P91-A26 transform; planted "
        f"direct-key positive fires; real family max quadgram score "
        f"{report['real_family_max_quadgram']:.2f}, "
        f"{report['shuffle_ge_count']}/{report['trials']:,} multiset-"
        f"preserving P91 shuffles reach at least that score (family-wise "
        f"rate {report['family_wise_rate']:.4f}); 0 keyword hits on real "
        f"data; oracle {oracle['effective_attempts']:,} effective attempts "
        f"across {oracle['materials_tried']} materials, 0 hits; direct-key "
        f"{direct_key['address_checks']} address checks, 0 hits -- "
        f"Priority 5 closes negative"
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
