#!/usr/bin/env python3
"""Phase 402: executes Priority 6 (the final ranked item) of the
2026-08-25 BTCSEED/P91/Z continuation brainstorm -- treating `Q472`'s
236 `[control, data]` digraphs as a small, closed family of control/data
combining machines, rather than reading only the control rail alone
(Priority 1, Phase 397) or leaving the data rail unused.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`, Priority 6, frozen by the user as an exact contract before
this script was written:

- `Q472 = decoded[98:]` (472 chars) splits into 236 `[control, data]`
  digraphs: `control = Q472[0::2]` (236 symbols, confirmed all in
  `{B,C,D,E}`), `data = Q472[1::2]` (236 symbols, the full grid alphabet,
  `J->I` normalized per the established Bifid convention);
- zero-based coordinates: `control = (cr, cc)` from the control letter's
  own position in the DBBI-keyed 5x5 square (each in `{0,1}`, since
  `B,C,D,E` occupy exactly the square's upper-left 2x2); `data = (dr, dc)`
  from the data letter's own position (each in `{0..4}`);
  `q_row = 2*cr+cc`, `q_col = 2*cc+cr`, `data_index = 5*dr+dc`;
- exactly ten labeled machines, closed and enumerated before any output
  is inspected:
  1. selector: `digit = dc if cr==1 else dr`, then mod-5 complement
     (`digit = (5-digit)%5`) when `cc==1`;
  2. same selector with the control-axis roles exchanged: `digit = dc if
     cc==1 else dr`, complemented when `cr==1`;
  3. rotate `(dr,dc)` clockwise by `q_row` quarter-turns in the 5x5 grid;
  4. rotate `(dr,dc)` clockwise by `q_col` quarter-turns;
  5. `(dr+cr, dc+cc) mod 5`;
  6. `(dr-cr, dc-cc) mod 5`;
  7. `25*q_row + data_index` (byte, range 0..99);
  8. `25*q_col + data_index`;
  9. `4*data_index + q_row`;
  10. `4*data_index + q_col`;
  the two selector machines (1, 2) emit one digit per digraph -- 236
  digits, paired into 118 letters via the same `(row,col)->grid letter`
  lookup; machines 3-6 emit one letter per digraph (236 letters each);
  machines 7-10 emit one byte per digraph (236-byte streams, values
  0..99 by construction -- too narrow to ever literally reproduce an
  ASCII magic header such as `Salted__`, which is exactly why the planted
  fixture below is constructed independently of the coordinate formulas);
- evaluation: frozen keyword scan (`phase396.TARGET_KEYWORDS`) plus
  Phase 387's own `quadgram_mean` (average log-probability per quadgram,
  not the raw sum -- needed so the 118-letter selector outputs and the
  236-letter geometric outputs are scored on a comparable scale) for the
  six letter machines; strict typed/container/key-format scanners only
  (`typed_decode_parse_ladder_audit.validate_structural`/`validate_full`/
  `is_parser_valid`, no printability-only promotion) for the four raw-byte
  machines; a 100,000-trial deterministic Monte Carlo that shuffles the
  **data rail only** (control rail held fixed) and recomputes all six
  letter machines' family-max `quadgram_mean` per trial; a blob oracle
  (uppercase/lowercase x literal/SHA-256/double-SHA-256, exact materials
  deduplicated before counting) for the six letter outputs only; a
  direct-secp256k1-scalar/P2PKH address check (binary SHA-256 of every
  unique letter-case output, and of each raw-byte stream directly, no
  BIP32 tree) against the exact prize address.

**Method:** wrote this script, reusing Phase 386's own `build_grid()`,
Phase 387's `load_quadgrams()`/`quadgram_mean()`, Phase 394's
`base58_decode()`/`hash160()`/`public_key()`/`SECP256K1_ORDER`/
`TARGET_ADDRESS`, Phase 396's `TARGET_KEYWORDS`, `cb_common`'s oracle
families/`keystr_forms()` (the same 480-effective-attempts-per-material
unit used in Phases 396/401), and
`typed_decode_parse_ladder_audit.validate_structural`/`validate_full`/
`is_parser_valid` verbatim -- no primitive re-derived. Six self-test
fixtures prove the pipeline actually fires before trusting a negative
result: a synthetic control/data rail engineered so the selector machine
(machine 1) recovers a planted phrase (`SEED`) through the real
digit-pairing logic; a synthetic rail engineered so the rotation machine
(machine 3, at the non-trivial `q_row=1` case) recovers a planted phrase
(`KEY`); a synthetic 32-byte string (`Salted__` + salt + padding,
independent of the coordinate formulas, which can never emit byte values
above 99 and therefore can never spell an ASCII magic header) that trips
the raw-byte evaluator's `Salted__` detector; a known scalar/address pair
that trips the direct-key detector; explicit assertions that every real
hit list (oracle, letter direct-key, byte direct-key, byte-machine
parser-valid flags) is empty.

**Result:** see `self_test()`'s asserted counts and values for the exact
pinned manifest (236-symbol rails, 10 machine outputs at their frozen
lengths), oracle/direct-key tallies, and Monte Carlo family-wise rate.

**Disposition:** decided strictly by the frozen promotion rule -- an
exact parser, blob, or address hit, or a family-wise `p <= 0.005`,
promotes; otherwise Priority 6 closes negative. Per the user's own
instruction accompanying this contract, a negative result here closes
the brainstorm's entire ranked verification queue (Priorities 1-6, all
now executed as Phases 397-402) -- it does not open a Priority 7.
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
from typed_decode_parse_ladder_audit import (  # noqa: E402
    base64_trigger_variant,
    is_der_trigger,
    is_gzip_trigger,
    is_hex_trigger,
    is_salted_header_trigger,
    is_zip_trigger,
    is_zlib_trigger,
    is_parser_valid,
    validate_full,
    validate_structural,
)

MONTE_CARLO_TRIALS = 100_000
MONTE_CARLO_SEED = 0x402
GRID_SIZE = 5

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def normalize_letter(ch):
    ch = ch.upper()
    return "I" if ch == "J" else ch


def rotate_cw(r, c, n, size=GRID_SIZE):
    n = n % 4
    for _ in range(n):
        r, c = c, size - 1 - r
    return r, c


def digraph_coords(control_ch, data_ch, pos):
    cr, cc = pos[control_ch]
    dr, dc = pos[normalize_letter(data_ch)]
    return cr, cc, dr, dc


def rails_to_coords(control_rail, data_rail, pos):
    return [digraph_coords(cch, dch, pos) for cch, dch in zip(control_rail, data_rail)]


# ---------------------------------------------------------------------------
# The ten frozen machines
# ---------------------------------------------------------------------------

def machine_selector1(cr, cc, dr, dc):
    digit = dc if cr == 1 else dr
    if cc == 1:
        digit = (5 - digit) % 5
    return digit


def machine_selector2(cr, cc, dr, dc):
    digit = dc if cc == 1 else dr
    if cr == 1:
        digit = (5 - digit) % 5
    return digit


def pair_digits_to_letters(digits, grid):
    assert len(digits) % 2 == 0
    return "".join(grid[(digits[i], digits[i + 1])] for i in range(0, len(digits), 2))


def machine_rotate_qrow(cr, cc, dr, dc):
    q_row = 2 * cr + cc
    return rotate_cw(dr, dc, q_row)


def machine_rotate_qcol(cr, cc, dr, dc):
    q_col = 2 * cc + cr
    return rotate_cw(dr, dc, q_col)


def machine_add(cr, cc, dr, dc):
    return (dr + cr) % 5, (dc + cc) % 5


def machine_sub(cr, cc, dr, dc):
    return (dr - cr) % 5, (dc - cc) % 5


def byte_qrow_plus_index(cr, cc, dr, dc):
    return 25 * (2 * cr + cc) + (5 * dr + dc)


def byte_qcol_plus_index(cr, cc, dr, dc):
    return 25 * (2 * cc + cr) + (5 * dr + dc)


def byte_index_plus_qrow(cr, cc, dr, dc):
    return 4 * (5 * dr + dc) + (2 * cr + cc)


def byte_index_plus_qcol(cr, cc, dr, dc):
    return 4 * (5 * dr + dc) + (2 * cc + cr)


def compute_letter_family(coords, grid):
    digits1 = [machine_selector1(*c) for c in coords]
    digits2 = [machine_selector2(*c) for c in coords]
    return {
        "M1_selector_cr_complement_cc": pair_digits_to_letters(digits1, grid),
        "M2_selector_cc_complement_cr": pair_digits_to_letters(digits2, grid),
        "M3_rotate_qrow": "".join(grid[machine_rotate_qrow(*c)] for c in coords),
        "M4_rotate_qcol": "".join(grid[machine_rotate_qcol(*c)] for c in coords),
        "M5_add_control": "".join(grid[machine_add(*c)] for c in coords),
        "M6_sub_control": "".join(grid[machine_sub(*c)] for c in coords),
    }


def compute_byte_family(coords):
    return {
        "B7_25qrow_plus_index": bytes(byte_qrow_plus_index(*c) for c in coords),
        "B8_25qcol_plus_index": bytes(byte_qcol_plus_index(*c) for c in coords),
        "B9_4index_plus_qrow": bytes(byte_index_plus_qrow(*c) for c in coords),
        "B10_4index_plus_qcol": bytes(byte_index_plus_qcol(*c) for c in coords),
    }


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def score_letters(letters_dict, logs, floor):
    scores = {}
    for label, text in letters_dict.items():
        keyword_hits = [kw for kw in TARGET_KEYWORDS if kw in text.upper()]
        scores[label] = {
            "text": text,
            "length": len(text),
            "quadgram_mean": quadgram_mean(text, logs, floor),
            "keyword_hits": keyword_hits,
        }
    return scores


def evaluate_raw_bytes(data):
    triggers = {
        "hex": is_hex_trigger(data),
        "base64": base64_trigger_variant(data) is not None,
        "gzip": is_gzip_trigger(data),
        "zlib": is_zlib_trigger(data),
        "zip": is_zip_trigger(data),
        "der": is_der_trigger(data),
        "salted_header": is_salted_header_trigger(data),
    }
    structural = validate_structural(data)
    validation = validate_full(data)
    return {
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "magic_triggers": triggers,
        "structural": {
            "der_ec": structural["der_ec"] is not None,
            "psbt": structural["psbt"] is not None,
            "bitcoin_tx": structural["bitcoin_tx"] is not None,
            "salted_header": structural["salted_header"],
        },
        "key_format_matches": validation["key_format_matches"],
        "exact_target_hit": validation["exact_target_hit"],
        "parser_valid": is_parser_valid(validation),
    }


def oracle_sweep(letters_dict):
    hits = []
    attempts = 0
    materials_tried = 0
    for label, text in letters_dict.items():
        case_variants = {}
        for case_label, variant in ((label + "_as_decoded", text), (label + "_lower", text.lower())):
            case_variants.setdefault(variant, case_label)
        for variant, case_label in case_variants.items():
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


def direct_key_sweep_letters(letters_dict, targets):
    hits = []
    digests_tried = 0
    for label, text in letters_dict.items():
        for case_label, variant in ((label + "_as_decoded", text), (label + "_lower", text.lower())):
            digests_tried += 1
            digest = hashlib.sha256(variant.encode("utf-8")).digest()
            value = int.from_bytes(digest, "big")
            if not (1 <= value < SECP256K1_ORDER):
                continue
            for match in address_matches(value, targets):
                hits.append({"root": case_label, **match})
    return {"digests_tried": digests_tried, "address_checks": digests_tried * 2, "hits": hits}


def direct_key_sweep_bytes(byte_streams, targets):
    hits = []
    digests_tried = 0
    for label, data in byte_streams.items():
        digests_tried += 1
        digest = hashlib.sha256(data).digest()
        value = int.from_bytes(digest, "big")
        if not (1 <= value < SECP256K1_ORDER):
            continue
        for match in address_matches(value, targets):
            hits.append({"root": label, **match})
    return {"digests_tried": digests_tried, "address_checks": digests_tried * 2, "hits": hits}


# ---------------------------------------------------------------------------
# Planted positives
# ---------------------------------------------------------------------------

def planted_selector_phrase_positive(grid, pos):
    """A synthetic digraph rail with cr=cc=0 throughout (control letter
    'D') -- selector machine 1 then reduces to `digit = dr`, unmodified.
    Choosing each data letter's row/col in sequence as the digit stream
    lets a target phrase be planted and recovered through the real
    digit-pairing logic, proving machines 1/2's pairing pipeline is
    correct, not just that it runs."""
    target = "SEED"
    digits = []
    for ch in target:
        r, c = pos[normalize_letter(ch)]
        digits.append(r)
        digits.append(c)
    coords = [(0, 0, d, 0) for d in digits]
    recovered = pair_digits_to_letters([machine_selector1(*c) for c in coords], grid)
    return {"target": target, "recovered": recovered, "matches": recovered == target}


def planted_rotation_phrase_positive(grid, pos):
    """A synthetic digraph rail with control letter 'B' (cr=0, cc=1, so
    q_row=1 -- the non-trivial one-quarter-turn case, not the identity
    n=0 case) -- each digraph's data coordinate is the algebraic pre-
    image of a target letter's coordinate under one clockwise turn, so
    machine 3 recovers the planted phrase exactly, proving the rotation
    machine's direction/pre-image algebra is correct."""
    target = "KEY"
    control_ch = "B"
    cr, cc = pos[control_ch]
    assert (cr, cc) == (0, 1)
    coords = []
    for ch in target:
        tr, tc = pos[normalize_letter(ch)]
        dr, dc = GRID_SIZE - 1 - tc, tr
        coords.append((cr, cc, dr, dc))
    recovered = "".join(grid[machine_rotate_qrow(*c)] for c in coords)
    return {"target": target, "recovered": recovered, "matches": recovered == target}


def planted_salted_header_byte_positive():
    """A synthetic 32-byte string, built independently of the coordinate
    formulas (which can only ever emit values 0..99 and so can never
    literally spell an ASCII magic header like 'Salted__' -- 'l' alone is
    108), fed through the identical raw-byte evaluator the four real
    machine outputs use -- proves the strict Salted__ detector fires."""
    data = b"Salted__" + bytes(range(8)) + bytes(range(16))
    assert len(data) == 32
    return {"data_hex": data.hex(), "result": evaluate_raw_bytes(data)}


def planted_direct_key_positive():
    scalar_bytes = (1).to_bytes(32, "big")
    own_hash160 = hash160(public_key(1, compressed=True))
    value = int.from_bytes(scalar_bytes, "big")
    assert 1 <= value < SECP256K1_ORDER
    return {"hits": address_matches(value, {own_hash160})}


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def build_rails(q472):
    assert len(q472) == 472
    control_rail = q472[0::2]
    data_rail = q472[1::2]
    assert len(control_rail) == 236
    assert len(data_rail) == 236
    assert set(control_rail) == set("BCDE")
    return control_rail, data_rail


def audit():
    decoded = btcseed_audit()["decoded"]
    q472 = decoded[98:]
    control_rail, data_rail = build_rails(q472)

    grid_keyword, grid, pos = build_grid(DBBI[:13])

    coords = rails_to_coords(control_rail, data_rail, pos)
    letters = compute_letter_family(coords, grid)
    byte_streams = compute_byte_family(coords)

    logs, floor = load_quadgrams()
    letter_scores = score_letters(letters, logs, floor)
    real_family_max = max(entry["quadgram_mean"] for entry in letter_scores.values())
    real_keyword_hits = {
        label: entry["keyword_hits"] for label, entry in letter_scores.items() if entry["keyword_hits"]
    }

    byte_results = {label: evaluate_raw_bytes(data) for label, data in byte_streams.items()}

    rng = random.Random(MONTE_CARLO_SEED)
    data_letters = list(data_rail)
    shuffle_maxes = []
    for _ in range(MONTE_CARLO_TRIALS):
        rng.shuffle(data_letters)
        shuffled_data_rail = "".join(data_letters)
        shuffled_coords = rails_to_coords(control_rail, shuffled_data_rail, pos)
        shuffled_letters = compute_letter_family(shuffled_coords, grid)
        shuffled_scores = score_letters(shuffled_letters, logs, floor)
        shuffle_maxes.append(max(entry["quadgram_mean"] for entry in shuffled_scores.values()))
    ge_count = sum(1 for v in shuffle_maxes if v >= real_family_max)
    family_wise_rate = ge_count / MONTE_CARLO_TRIALS

    oracle_result = oracle_sweep(letters)
    targets = {target_hash160()}
    letter_direct = direct_key_sweep_letters(letters, targets)
    byte_direct = direct_key_sweep_bytes(byte_streams, targets)

    return {
        "control_rail_length": len(control_rail),
        "data_rail_length": len(data_rail),
        "control_rail_alphabet": "".join(sorted(set(control_rail))),
        "letters": dict(letters),
        "letter_scores": letter_scores,
        "real_family_max_quadgram_mean": real_family_max,
        "real_keyword_hits": real_keyword_hits,
        "byte_streams_hex": {label: data.hex() for label, data in byte_streams.items()},
        "byte_results": byte_results,
        "trials": MONTE_CARLO_TRIALS,
        "shuffle_ge_count": ge_count,
        "family_wise_rate": family_wise_rate,
        "oracle": oracle_result,
        "letter_direct_key": letter_direct,
        "byte_direct_key": byte_direct,
        "planted_selector_phrase_positive": planted_selector_phrase_positive(grid, pos),
        "planted_rotation_phrase_positive": planted_rotation_phrase_positive(grid, pos),
        "planted_salted_header_byte_positive": planted_salted_header_byte_positive(),
        "planted_direct_key_positive": planted_direct_key_positive(),
    }


def self_test():
    report = audit()

    assert report["control_rail_length"] == 236
    assert report["data_rail_length"] == 236
    assert report["control_rail_alphabet"] == "BCDE"

    assert set(report["letters"].keys()) == {
        "M1_selector_cr_complement_cc", "M2_selector_cc_complement_cr",
        "M3_rotate_qrow", "M4_rotate_qcol", "M5_add_control", "M6_sub_control",
    }
    assert len(report["letters"]["M1_selector_cr_complement_cc"]) == 118
    assert len(report["letters"]["M2_selector_cc_complement_cr"]) == 118
    for label in ("M3_rotate_qrow", "M4_rotate_qcol", "M5_add_control", "M6_sub_control"):
        assert len(report["letters"][label]) == 236, label

    assert set(report["byte_streams_hex"].keys()) == {
        "B7_25qrow_plus_index", "B8_25qcol_plus_index",
        "B9_4index_plus_qrow", "B10_4index_plus_qcol",
    }
    for label, hexdata in report["byte_streams_hex"].items():
        data = bytes.fromhex(hexdata)
        assert len(data) == 236, (label, len(data))
        assert all(0 <= b <= 99 for b in data), label

    assert report["real_keyword_hits"] == {}

    assert report["trials"] == MONTE_CARLO_TRIALS
    assert 0.0 <= report["family_wise_rate"] <= 1.0

    for label, result in report["byte_results"].items():
        assert not any(result["magic_triggers"].values()), (label, result["magic_triggers"])
        assert not any(result["structural"].values()), (label, result["structural"])
        assert result["key_format_matches"] == [], (label, result["key_format_matches"])
        assert result["exact_target_hit"] is None, (label, result["exact_target_hit"])
        assert result["parser_valid"] is False, (label, result["parser_valid"])

    oracle = report["oracle"]
    assert oracle["materials_tried"] == 36
    assert oracle["effective_attempts"] == 17280
    assert oracle["hits"] == []

    letter_direct = report["letter_direct_key"]
    assert letter_direct["digests_tried"] == 12
    assert letter_direct["address_checks"] == 24
    assert letter_direct["hits"] == []

    byte_direct = report["byte_direct_key"]
    assert byte_direct["digests_tried"] == 4
    assert byte_direct["address_checks"] == 8
    assert byte_direct["hits"] == []

    selector_positive = report["planted_selector_phrase_positive"]
    assert selector_positive["matches"] is True

    rotation_positive = report["planted_rotation_phrase_positive"]
    assert rotation_positive["matches"] is True

    salted_positive = report["planted_salted_header_byte_positive"]
    assert salted_positive["result"]["magic_triggers"]["salted_header"] is True
    assert salted_positive["result"]["structural"]["salted_header"] is True
    assert salted_positive["result"]["parser_valid"] is True

    direct_key_positive = report["planted_direct_key_positive"]
    assert len(direct_key_positive["hits"]) == 1
    assert direct_key_positive["hits"][0]["compressed"] is True

    promoted = (
        bool(oracle["hits"])
        or bool(letter_direct["hits"])
        or bool(byte_direct["hits"])
        or any(result["parser_valid"] for result in report["byte_results"].values())
        or report["family_wise_rate"] <= 0.005
    )
    assert promoted is False

    print(
        f"[*] self-test OK: all four planted positives fire (selector-"
        f"machine phrase recovery, rotation-machine phrase recovery at "
        f"q_row=1, Salted__ byte-fixture detection, direct-scalar address "
        f"match); pinned 10-machine manifest (6 letter outputs at their "
        f"frozen 118/236 lengths, 4 raw-byte streams at 236 bytes each, "
        f"values 0..99) reproduced from the real 236-symbol control/data "
        f"rails; 0 real keyword hits; real family-max quadgram_mean "
        f"{report['real_family_max_quadgram_mean']:.4f}, "
        f"{report['shuffle_ge_count']}/{report['trials']:,} data-rail-only "
        f"shuffles reach at least that score (family-wise rate "
        f"{report['family_wise_rate']:.4f}); oracle "
        f"{oracle['effective_attempts']:,} effective attempts across "
        f"{oracle['materials_tried']} materials, 0 hits; direct-key "
        f"{letter_direct['address_checks'] + byte_direct['address_checks']} "
        f"address checks (letters + raw bytes), 0 hits; 0 raw-byte "
        f"machines parser-valid -- Priority 6 closes negative, exhausting "
        f"the brainstorm's ranked verification queue (Priorities 1-6, "
        f"Phases 397-402)"
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
