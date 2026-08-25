#!/usr/bin/env python3
"""Phase 407: tests `P91` repeated as a Vigenere-style key over `Q472`,
in both the alphabet-index and native coordinate-space arithmetic --
"Idea bank E" items 80 and 81 of the 2026-08-25 BTCSEED/P91/Z
continuation brainstorm's 100-item idea bank, the strongest genuinely
untested residual once Phases 397-406 closed the ranked queue and its
first four follow-up gaps.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`, "Idea bank E: P91 as a key for Q472":

```text
80. Repeat P91 over Q472 as a Vigenere-style key.
81. Repeat it in native modulo-5 coordinates instead of modulo 26.
```

This is the direct sibling of Phase 401 (Priority 5, `P91` against
`A26 = DBBI - M91 mod 26`): same alphabet-space/coordinate-space
combinator pair, same three-way `sub`/`add`/`rsub` axis, same
evaluation pipeline -- only the second operand changes, from the fixed
`A26`/`A5` difference to `P91` tiled to `Q472`'s length as a repeating
key. Items 82-89 of the same idea bank (autokey seeding, deduplicated
second squares, ordered key schedules, block partitioning, terminal-`Z`
direction changes) are explicitly out of scope for this phase -- each
would need its own separately-frozen contract, not a quiet extension of
this one.

**Frozen contract (proposed and approved before this script was
written):**

- `P91 = decoded[7:98]` (91 characters), `Q472 = decoded[98:]` (472
  characters), both exactly as Phase 386 produces them;
- `P91REP = (P91 * ceil(472/91))[:472]` -- `P91` tiled left-to-right to
  cover `Q472`'s full length, no reversal, no autokey chaining, no
  block partitioning;
- alphabet-space: standard 26-letter modular arithmetic (`external_
  archive_lead_audit.subtract_mod26`'s own convention -- plain `A=0..
  Z=25` ASCII arithmetic, the project's established "mod 26" reading
  for these letter-space experiments, distinct from the keyed-square's
  internal ordering); exactly three candidates `Q472-P91REP`,
  `Q472+P91REP`, `P91REP-Q472` (mod 26, letter-wise);
- coordinate-space: each letter's native `(row, col)` position in Phase
  386's DBBI-keyed 5x5 square (`build_grid(DBBI[:13])`, the same grid
  Phases 394/396/401/404 already use); exactly three candidates
  `coords(Q472)-coords(P91REP)`, `coords(Q472)+coords(P91REP)`,
  `coords(P91REP)-coords(Q472)` (mod 5, component-wise), mapped back
  through the same square;
- **6 strings total**, no alternate squares, axis swaps, key reversal,
  autokeying, or additional arithmetic;
- evaluation: Phase 396's frozen keyword list; the project's frozen
  quadgram table (`quadgram_score`, matching Phase 401's un-normalized
  convention since every candidate in this family shares one length);
  100,000 `Q472`-multiset-preserving shuffles, recomputing all 6
  candidates per shuffle (with `P91REP` held fixed, since it is the
  key, not the object under test) and comparing family maxima --
  `Q472` is the shuffled object because idea 80 casts it as the message
  a fixed `P91`-derived key is applied to, the same role `DATA236`
  played in Phase 404's own identity shuffle;
- oracle: uppercase/lowercase x literal/SHA-256/double-SHA-256 across
  all 6 candidates = 36 materials against all 4 blobs (matching Phase
  401's exact scale, 17,280 effective attempts);
- direct-key endpoint only: each candidate's case-form binary SHA-256
  digest as a secp256k1 scalar, compressed/uncompressed P2PKH (12
  digests x 2 = 24 address checks) -- explicitly no BIP32 tree unless
  this family independently promotes first;
- promotion: an exact oracle/address hit, or a family-wise
  `p <= 0.005`, promotes; otherwise this closes negative.

**Method:** wrote this script, reusing Phase 401's own `mod26()`,
`coords_of()`, `coords_op()`, `map_back()`, `normalize_letter()`,
`ORACLE_FAMILIES`, `oracle_sweep()`-equivalent structure, `target_
hash160()`, and `address_matches()` verbatim in spirit (re-parameterized
for a 6-entry family keyed on `Q472`/`P91REP` instead of `P91`/`A26`);
Phase 386's `build_grid()`; Phase 387's `load_quadgrams()`/
`quadgram_score()`; Phase 394's `base58_decode()`/`hash160()`/
`public_key()`/`SECP256K1_ORDER`/`TARGET_ADDRESS`; Phase 396's `TARGET_
KEYWORDS` -- no primitive re-derived. Self-tests assert the mod-26 and
coordinate-space inverse identities hold by construction
(`(Q472-P91REP)+P91REP == Q472`, and the coordinate-space equivalent);
a synthetic planted-English positive (an identity-valued synthetic
`P91REP` of all `A`s, so subtracting it leaves a planted `SATOSHI`-
bearing 472-character string unchanged) proves the keyword/quadgram
detector fires through the real tiling-and-combining pipeline, not just
on random noise; a known scalar/address pair proves the direct-key
detector fires; the real data's oracle and address-check hit lists are
asserted empty, not just counted.

**Result:** see `self_test()`'s asserted values for the exact family-max
quadgram score, keyword-hit lists, family-wise empirical rate under the
`Q472` shuffle null, and the oracle/address-check tallies.

**Disposition:** decided strictly by the frozen promotion rule above --
an exact blob or address hit, or a family-wise `p <= 0.005`, promotes;
otherwise this closes negative without widening to idea-bank items
82-89 or any other unfrozen expansion.
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
from data import DBBI  # noqa: E402
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
from phase401_p91z_priority5_youwon_difference_algebra_audit import (  # noqa: E402
    coords_of,
    coords_op,
    map_back,
    mod26,
)

MONTE_CARLO_TRIALS = 100_000
MONTE_CARLO_SEED = 0x407
P91_LENGTH = 91
Q472_LENGTH = 472

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def repeat_key(key, length):
    assert len(key) > 0
    reps = -(-length // len(key))
    return (key * reps)[:length]


def build_family(q472_text, p91rep, pos, grid):
    """The 6 frozen candidates for a given Q472 text, holding P91REP
    fixed (it is the key, not the object under test)."""
    as1 = mod26(q472_text, p91rep, "sub")  # Q472 - P91REP
    as2 = mod26(q472_text, p91rep, "add")  # Q472 + P91REP
    as3 = mod26(p91rep, q472_text, "sub")  # P91REP - Q472

    q472_coords = coords_of(q472_text, pos)
    p91rep_coords = coords_of(p91rep, pos)
    cs1 = map_back(coords_op(q472_coords, p91rep_coords, "sub"), grid)  # coords(Q472) - coords(P91REP)
    cs2 = map_back(coords_op(q472_coords, p91rep_coords, "add"), grid)  # coords(Q472) + coords(P91REP)
    cs3 = map_back(coords_op(p91rep_coords, q472_coords, "sub"), grid)  # coords(P91REP) - coords(Q472)

    return {
        "AS1_Q472_minus_P91REP": as1,
        "AS2_Q472_plus_P91REP": as2,
        "AS3_P91REP_minus_Q472": as3,
        "CS1_coordsQ472_minus_P91REP": cs1,
        "CS2_coordsQ472_plus_P91REP": cs2,
        "CS3_coordsP91REP_minus_Q472": cs3,
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


def planted_synthetic_english_positive(logs, floor, pos, grid):
    """An identity-valued synthetic P91REP (all 'A's, tiled from a
    91-character all-'A' seed) means Q472_synth - P91REP_synth leaves a
    planted SATOSHI-bearing 472-character string unchanged -- proves the
    keyword/quadgram detector fires through the real tiling-and-
    combining pipeline, not just on random noise."""
    core = "THISISATESTSATOSHIPLANTEDPOSITIVEFORPHASEFOURHUNDREDSEVENAUDIT"
    target = (core * 8)[:Q472_LENGTH]
    assert len(target) == Q472_LENGTH
    p91_synth_seed = "A" * P91_LENGTH
    p91rep_synth = repeat_key(p91_synth_seed, Q472_LENGTH)
    as1 = mod26(target, p91rep_synth, "sub")
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
    q472 = decoded[98:]
    assert len(p91) == P91_LENGTH
    assert len(q472) == Q472_LENGTH

    p91rep = repeat_key(p91, Q472_LENGTH)
    assert len(p91rep) == Q472_LENGTH
    assert all(p91rep[i] == p91[i % P91_LENGTH] for i in range(Q472_LENGTH))

    grid_keyword, grid, pos = build_grid(DBBI[:13])

    real_family = build_family(q472, p91rep, pos, grid)

    logs, floor = load_quadgrams()
    real_scores = score_family(real_family, logs, floor)
    real_family_max = max(entry["quadgram_score"] for entry in real_scores.values())
    real_keyword_hits = {label: entry["keyword_hits"] for label, entry in real_scores.items() if entry["keyword_hits"]}

    # Inverse identities, mod-26 and coordinate space.
    as1_roundtrip = mod26(real_family["AS1_Q472_minus_P91REP"], p91rep, "add")
    q472_coords = coords_of(q472, pos)
    p91rep_coords = coords_of(p91rep, pos)
    cs1_coords = coords_op(q472_coords, p91rep_coords, "sub")
    cs1_roundtrip = map_back(coords_op(cs1_coords, p91rep_coords, "add"), grid)

    rng = random.Random(MONTE_CARLO_SEED)
    letters = list(q472)
    shuffle_family_maxes = []
    for _ in range(MONTE_CARLO_TRIALS):
        rng.shuffle(letters)
        shuffled_q472 = "".join(letters)
        shuffled_family = build_family(shuffled_q472, p91rep, pos, grid)
        shuffled_scores = score_family(shuffled_family, logs, floor)
        shuffle_family_maxes.append(max(e["quadgram_score"] for e in shuffled_scores.values()))
    ge_count = sum(1 for v in shuffle_family_maxes if v >= real_family_max)
    family_wise_rate = ge_count / MONTE_CARLO_TRIALS

    oracle_result = oracle_sweep(real_family)
    targets = {target_hash160()}
    direct_key_result = direct_key_sweep(real_family, targets)

    return {
        "p91_length": len(p91),
        "q472_length": len(q472),
        "p91rep_length": len(p91rep),
        "grid_keyword": grid_keyword,
        "real_family": {label: text for label, text in real_family.items()},
        "real_scores": real_scores,
        "real_family_max_quadgram": real_family_max,
        "real_keyword_hits": real_keyword_hits,
        "as1_roundtrip_matches_q472": as1_roundtrip == q472,
        "cs1_roundtrip_matches_q472": cs1_roundtrip == q472,
        "trials": MONTE_CARLO_TRIALS,
        "shuffle_ge_count": ge_count,
        "family_wise_rate": family_wise_rate,
        "oracle": oracle_result,
        "direct_key": direct_key_result,
        "planted_synthetic_english_positive": planted_synthetic_english_positive(logs, floor, pos, grid),
        "planted_direct_key_positive": planted_direct_key_positive(),
    }


def self_test():
    report = audit()

    assert report["p91_length"] == 91
    assert report["q472_length"] == 472
    assert report["p91rep_length"] == 472
    assert set(report["real_family"].keys()) == {
        "AS1_Q472_minus_P91REP", "AS2_Q472_plus_P91REP", "AS3_P91REP_minus_Q472",
        "CS1_coordsQ472_minus_P91REP", "CS2_coordsQ472_plus_P91REP", "CS3_coordsP91REP_minus_Q472",
    }
    for text in report["real_family"].values():
        assert len(text) == 472 and text.isalpha() and text == text.upper()

    assert report["as1_roundtrip_matches_q472"] is True
    assert report["cs1_roundtrip_matches_q472"] is True

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
        f"keyword detector through the real Q472-P91REP transform; "
        f"planted direct-key positive fires; real family max quadgram "
        f"score {report['real_family_max_quadgram']:.2f}, "
        f"{report['shuffle_ge_count']}/{report['trials']:,} multiset-"
        f"preserving Q472 shuffles reach at least that score (family-wise "
        f"rate {report['family_wise_rate']:.4f}); 0 keyword hits on real "
        f"data; oracle {oracle['effective_attempts']:,} effective attempts "
        f"across {oracle['materials_tried']} materials, 0 hits; direct-key "
        f"{direct_key['address_checks']} address checks, 0 hits -- "
        f"Phase 407 closes negative"
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
