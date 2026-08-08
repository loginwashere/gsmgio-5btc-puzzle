#!/usr/bin/env python3
"""Audit the bounded residue of four proposed structural avenues.

The atomic relation and P32TRAILING focus mostly repeat established coverage.
This module isolates only exact strings absent from the focused corpus, and
tests the exact 31-character selection as a repeating/autokey mod-9 seed.

For the keystream branch the conversion is the project's existing numeric-seed rule:
letters -> A1Z26 values modulo 9.  The selected string is also the fixed
classic-J pad25 alphabet, avoiding a second unknown keyword.  The maximum
English score over all declared modes, targets, escape orders, and board
topologies is calibrated against shuffled versions of the same 31 seed digits.
AES escalation is prohibited unless the familywise gate reaches p < 0.005.
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
    NINE_SYMS,
    answer_forms,
    autokey_dechain_9ary,
    decode_9ary,
    keystr_forms,
    keyword_to_seed,
    pad25,
)
from color_mask_full_stream_audit import passphrase_hits  # noqa: E402
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
from denis_prime_extraction_audit import TARGET  # noqa: E402
from salt_selector_permutation_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
)


ATOMIC_CANDIDATES = (
    "Vanadium",
    "Sulfur",
    "Nitrogen",
    "VSN",
    "23167",
    "V16S7N",
    "VanadiumSulfurNitrogen",
)
BOOK_CANDIDATES = (
    "Mother Goddess",
    "Virgin Mary",
    "Divine Feminine",
)
P32_CANDIDATES = (
    VALIDATION_ANSWER,
    "incaseyoumanagetocrackthis",
    "theprivatekeysbelongtohalfandbetterhalf",
    "halfandbetterhalf",
)
TARGETS = {
    "DBBI": (DBBI, (("b", "e"), ("e", "b"))),
    "FAED": (FAED, (("g", "i"), ("i", "g"))),
}
TOPOLOGIES = ("top_first", "escapes_first")
REPEATING_MODES = ("cipher_minus_key", "cipher_plus_key", "key_minus_cipher")
AUTOKEY_MODES = ("ciphertext", "plaintext")
SIGNS = (-1, 1)
MARKERS = ("private", "bitcoin", "password", "matrix", "choice", "salvation")
DEFAULT_TRIALS = 2000
NINE_INDEX = {char: index for index, char in enumerate(NINE_SYMS)}


def material_family(candidates, blobs):
    materials = {}
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form):
                materials.setdefault(keystr.encode("utf-8"), set()).add(candidate)
    hits = []
    for material, sources in sorted(materials.items()):
        for hit in passphrase_hits(material, blobs):
            hits.append({
                "sources": tuple(sorted(sources)),
                "material_hex": material.hex(),
                **hit,
            })
    return {
        "candidate_count": len(candidates),
        "unique_material_count": len(materials),
        "hits": hits,
    }


def repeat_transform(stream, seed, mode):
    output = []
    for index, char in enumerate(stream):
        cipher = NINE_INDEX[char]
        key = seed[index % len(seed)]
        if mode == "cipher_minus_key":
            value = cipher - key
        elif mode == "cipher_plus_key":
            value = cipher + key
        elif mode == "key_minus_cipher":
            value = key - cipher
        else:
            raise ValueError(f"unknown repeating mode: {mode}")
        output.append(NINE_SYMS[value % 9])
    return "".join(output)


def keystream_rows(seed, model):
    alphabet = pad25(TARGET)
    rows = []
    for target_name, (stream, escape_orders) in TARGETS.items():
        transforms = []
        for mode in REPEATING_MODES:
            transforms.append((f"repeating/{mode}", repeat_transform(stream, seed, mode)))
        for mode in AUTOKEY_MODES:
            for sign in SIGNS:
                transforms.append((
                    f"autokey/{mode}/sign_{sign:+d}",
                    autokey_dechain_9ary(stream, seed, mode=mode, sign=sign),
                ))
        for transform_name, transformed in transforms:
            for escapes in escape_orders:
                for topology in TOPOLOGIES:
                    decoded = decode_9ary(
                        transformed,
                        alphabet,
                        *escapes,
                        topology=topology,
                    )
                    if "?" in decoded:
                        continue
                    rows.append({
                        "target": target_name,
                        "transform": transform_name,
                        "escapes": escapes,
                        "topology": topology,
                        "decoded": decoded,
                        "score": quadgram_score(decoded.encode("ascii"), model),
                        "marker_hits": tuple(
                            marker for marker in MARKERS if marker in decoded.lower()
                        ),
                    })
    return rows


def keystream_audit(model, trials, seed_value):
    seed = keyword_to_seed(TARGET, 9)
    real_rows = keystream_rows(seed, model)
    best = max(real_rows, key=lambda row: row["score"])
    rng = random.Random(seed_value)
    null_maxima = []
    shuffled = list(seed)
    for _ in range(trials):
        rng.shuffle(shuffled)
        rows = keystream_rows(tuple(shuffled), model)
        null_maxima.append(max(row["score"] for row in rows))
    familywise_p = (
        1 + sum(value >= best["score"] for value in null_maxima)
    ) / (trials + 1)
    marker_rows = [
        {
            "target": row["target"],
            "transform": row["transform"],
            "escapes": row["escapes"],
            "topology": row["topology"],
            "markers": row["marker_hits"],
        }
        for row in real_rows
        if row["marker_hits"]
    ]
    oracle = {
        "escalated": familywise_p < 0.005,
        "unique_material_count": 0,
        "hits": [],
    }
    if oracle["escalated"]:
        material_report = material_family(
            tuple(row["decoded"] for row in real_rows), BLOBS
        )
        oracle.update(material_report)
    return {
        "keyword": TARGET,
        "seed_rule": "A1Z26 modulo 9",
        "seed_digits": tuple(seed),
        "alphabet": pad25(TARGET),
        "row_count": len(real_rows),
        "best": {
            key: value
            for key, value in best.items()
            if key != "decoded"
        },
        "best_decoded_sha256": hashlib.sha256(
            best["decoded"].encode("ascii")
        ).hexdigest(),
        "best_decoded_preview": best["decoded"][:160],
        "marker_rows": marker_rows,
        "null_trials": trials,
        "null_seed": seed_value,
        "familywise_upper_tail_p": familywise_p,
        "oracle": oracle,
    }


def rotation_scope():
    return {
        "requested_rotations": (23, 16, 7),
        "distinct_mod9_rotations": tuple(
            sorted({value % 9 for value in (23, 16, 7)})
        ),
        "reason_not_expanded": (
            "ROT23/16/7 collapse to ROT5/7 in base 9; rotating the escape pair "
            "with the alphabet is only a code-label permutation, while leaving "
            "the escape pair fixed introduces an unsupported mismatch"
        ),
    }


def audit(trials=DEFAULT_TRIALS, seed=179):
    if trials < 1:
        raise ValueError("trials must be positive")
    model = load_quadgrams()
    return {
        "atomic_provenance": {
            "established_transition": "V=23, P+H=16, V-(P+H)=7",
            "alternative_vsn_reading": "V=23, S=16, N=7 is reordered/selective",
            "independent_chemistry_clue": False,
        },
        "atomic_candidates": material_family(ATOMIC_CANDIDATES, BLOBS),
        "rotation_scope": rotation_scope(),
        "selected_keystream": keystream_audit(model, trials, seed),
        "p32_focus": {
            "status": "previously_default_target",
            "bound_blob": "P32TRAILING",
            **material_family(P32_CANDIDATES, {"P32TRAILING": BLOBS["P32TRAILING"]}),
        },
        "book_vocabulary": material_family(BOOK_CANDIDATES, BLOBS),
    }


def self_test():
    assert keyword_to_seed("AI", 9) == [1, 0]
    assert repeat_transform("abc", (1,), "cipher_minus_key") == "iab"
    assert repeat_transform("abc", (1,), "cipher_plus_key") == "bcd"
    assert repeat_transform("abc", (1,), "key_minus_cipher") == "bai"
    scope = rotation_scope()
    assert scope["distinct_mod9_rotations"] == (5, 7)
    assert pad25(TARGET) == "NCSYAGHIROLEFTVBDKMPQUWXZ"
    print(
        "[*] self-test OK: A1Z26-mod9 seed, repeating modes, rotation collapse, "
        "and fixed selected-text alphabet"
    )


def print_report(report):
    atomic = report["atomic_candidates"]
    print(
        f"[*] atomic exact strings: {atomic['candidate_count']} candidates / "
        f"{atomic['unique_material_count']} materials / {len(atomic['hits'])} hits"
    )
    print(f"[*] rotations: {report['rotation_scope']}")
    stream = report["selected_keystream"]
    print(
        f"[*] selected keystream: {stream['row_count']} decodes; "
        f"best_score={stream['best']['score']:.6f}; "
        f"familywise_p={stream['familywise_upper_tail_p']:.6f}; "
        f"marker_rows={len(stream['marker_rows'])}; "
        f"AES_escalated={stream['oracle']['escalated']}"
    )
    print(
        f"    best={stream['best']} sha256={stream['best_decoded_sha256']} "
        f"preview={stream['best_decoded_preview']}"
    )
    p32 = report["p32_focus"]
    print(
        f"[*] P32 focus: {p32['candidate_count']} candidates / "
        f"{p32['unique_material_count']} materials / {len(p32['hits'])} hits"
    )
    book = report["book_vocabulary"]
    print(
        f"[*] book vocabulary: {book['candidate_count']} candidates / "
        f"{book['unique_material_count']} materials / {len(book['hits'])} hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=179)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit(trials=args.trials, seed=args.seed)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
