#!/usr/bin/env python3
"""Bounded audit of OpenSSL salts as selectors rather than key material.

Each authenticated eight-byte salt selects eight items from four already-fixed
sources.  The family contains only the conventional zero/one-based modular
index readings, forward/reversed sources, and original/ascending/descending
salt-byte orders.  Outputs are tried verbatim as passphrases against the blob
that supplied the salt.  No hashing, padding, XOR folding, raw-key conversion,
or cross-blob pooling is performed.

Phase 3.2 remains an end-to-end AES oracle positive control, but is not called
a selector calibration: no authenticated source-to-password selector relation
is known for that solved stage.  Selector mechanics are instead checked with
synthetic fixtures, while deterministic random salts provide a descriptive
quadgram-score null for every structural rule.
"""

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    _load_blob,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
)
from data import (  # noqa: E402
    DBBI,
    FAED,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
)
from salt_phase_ion_audit import SELECTED  # noqa: E402


SCENE_WORDS_PATH = REPO_ROOT / "wordlists/gsmg/matrix_architect_scene_through_choice_words.txt"
QUADGRAM_PATH = SCRIPT_DIR / "data_files/english_quadgrams.txt"
EXPECTED_SCENE_WORDS = 1326
EXPECTED_SCENE_NORMALIZED_SHA256 = "167a7e20028f0eae6089e5e9731c4ac25d86e36f646a2097105e88d1eb75a6d2"
NULL_TRIALS_DEFAULT = 2000


def load_scene_words(path=SCENE_WORDS_PATH):
    lines = [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    tokens = " ".join(lines).split()
    if len(tokens) != EXPECTED_SCENE_WORDS:
        raise AssertionError(
            f"cached Architect scene has {len(tokens)} words, expected {EXPECTED_SCENE_WORDS}"
        )
    if tokens[:4] != ["i", "am", "the", "architect"] or tokens[-1] != "choice":
        raise AssertionError("cached Architect-scene boundaries changed")
    normalized_hash = hashlib.sha256(" ".join(tokens).encode("ascii")).hexdigest()
    if normalized_hash != EXPECTED_SCENE_NORMALIZED_SHA256:
        raise AssertionError("cached Architect-scene normalized hash changed")
    return tuple(tokens)


def sources():
    return {
        "DBBI_chars": tuple(DBBI),
        "FAED_chars": tuple(FAED),
        "selection31_chars": tuple(SELECTED.decode("ascii")),
        "matrix_scene1326_words": load_scene_words(),
    }


def salted_targets():
    phase32 = _load_blob(PHASE32_BLOB_B64)
    result = dict(BLOBS)
    result["PHASE32_SOLVED"] = phase32
    if len(result) != 5:
        raise AssertionError(
            f"expected four open/default salts plus solved calibration, found {len(result)}"
        )
    return result


def ordered_bytes(salt, order):
    if len(salt) != 8:
        raise ValueError("selector requires an eight-byte salt")
    indexed = list(enumerate(salt))
    if order == "original":
        return tuple(salt)
    if order == "ascending":
        return tuple(value for _index, value in sorted(indexed, key=lambda item: (item[1], item[0])))
    if order == "descending":
        return tuple(value for _index, value in sorted(indexed, key=lambda item: (-item[1], item[0])))
    raise ValueError(f"unknown salt-byte order: {order}")


def select_items(source, salt, index_rule, orientation, byte_order):
    if not source:
        raise ValueError("cannot select from an empty source")
    sequence = tuple(source if orientation == "forward" else reversed(source))
    values = ordered_bytes(salt, byte_order)
    if index_rule == "zero_mod_n":
        indices = tuple(value % len(sequence) for value in values)
    elif index_rule == "one_mod_n":
        indices = tuple((value - 1) % len(sequence) for value in values)
    else:
        raise ValueError(f"unknown index rule: {index_rule}")
    return indices, tuple(sequence[index] for index in indices)


def structural_specs():
    for index_rule in ("zero_mod_n", "one_mod_n"):
        for orientation in ("forward", "reverse"):
            for byte_order in ("original", "ascending", "descending"):
                yield index_rule, orientation, byte_order


def material_forms(source_name, selected):
    if source_name.endswith("_words"):
        return {
            "spaced": " ".join(selected).encode("ascii"),
            "compact": "".join(selected).encode("ascii"),
        }
    material = "".join(selected).encode("ascii")
    return {"exact": material}


def load_quadgrams(path=QUADGRAM_PATH):
    counts = {}
    total = 0
    for line in Path(path).read_text(encoding="ascii").splitlines():
        gram, count_text = line.split()
        count = int(count_text)
        counts[gram] = count
        total += count
    log_probs = {gram: math.log10(count / total) for gram, count in counts.items()}
    return log_probs, math.log10(0.01 / total)


def quadgram_score(material, model):
    log_probs, floor = model
    text = "".join(chr(byte) for byte in material if 65 <= byte <= 90 or 97 <= byte <= 122).upper()
    if len(text) < 4:
        return floor
    return sum(log_probs.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)


def seed_for(label):
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "big")


def null_scores(source_name, source, spec, model, trials):
    index_rule, orientation, byte_order = spec
    rng = random.Random(seed_for(":".join((source_name, *spec))))
    scores = []
    for _ in range(trials):
        salt = bytes(rng.randrange(256) for _ in range(8))
        _indices, selected = select_items(source, salt, index_rule, orientation, byte_order)
        # Compact is the common representation across character and word sources.
        material = "".join(selected).encode("ascii")
        scores.append(quadgram_score(material, model))
    return tuple(scores)


def evaluate_passphrase(material, blob):
    blobs = {"bound": blob}
    families = (
        ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS),
        ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS),
        ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS),
        ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS),
    )
    hits = []
    for family, oracle, variants in families:
        result = oracle(material, kdf_variants=variants, blobs=blobs)
        # CBC/stream/ECB return None on failure; Key Wrap returns an empty
        # list.  Truthiness is therefore the common success contract.
        if result:
            hits.append({"family": family, "result": repr(result)})
    return hits


def phase32_positive_control(blob):
    return aes_try_open_bytes(PHASE32_PASSWORD.encode("ascii"), blobs={"PHASE32": blob}) is not None


def audit(null_trials=NULL_TRIALS_DEFAULT, run_oracles=True):
    if null_trials < 1:
        raise ValueError("null_trials must be positive")
    source_map = sources()
    targets = salted_targets()
    model = load_quadgrams()
    null_cache = {
        (source_name, spec): null_scores(source_name, source, spec, model, null_trials)
        for source_name, source in source_map.items()
        for spec in structural_specs()
    }

    rows = []
    unique_bound_materials = set()
    hits = []
    phase32_selector_password_hits = []
    for target_name, blob in targets.items():
        salt, _ciphertext = blob
        for source_name, source in source_map.items():
            for spec in structural_specs():
                indices, selected = select_items(source, salt, *spec)
                forms = material_forms(source_name, selected)
                compact = forms["compact"] if "compact" in forms else forms["exact"]
                score = quadgram_score(compact, model)
                control = null_cache[(source_name, spec)]
                upper_tail = (1 + sum(value >= score for value in control)) / (len(control) + 1)
                row_hits = []
                for form_name, material in forms.items():
                    unique_bound_materials.add((target_name, material))
                    if target_name == "PHASE32_SOLVED" and material == PHASE32_PASSWORD.encode("ascii"):
                        phase32_selector_password_hits.append((source_name, spec, form_name))
                    candidate_hits = evaluate_passphrase(material, blob) if run_oracles else ()
                    for hit in candidate_hits:
                        item = {
                            "target": target_name,
                            "source": source_name,
                            "spec": spec,
                            "form": form_name,
                            "material_hex": material.hex(),
                            **hit,
                        }
                        hits.append(item)
                        row_hits.append(item)
                rows.append({
                    "target": target_name,
                    "salt": salt.hex(),
                    "source": source_name,
                    "index_rule": spec[0],
                    "orientation": spec[1],
                    "byte_order": spec[2],
                    "indices": indices,
                    "selected": selected,
                    "forms": {name: value.decode("ascii") for name, value in forms.items()},
                    "quadgram_score": score,
                    "null_upper_tail_p": upper_tail,
                    "hits": row_hits,
                })

    phase32_blob = targets["PHASE32_SOLVED"]
    best_rows = sorted(rows, key=lambda row: row["null_upper_tail_p"])
    minimum_p = best_rows[0]["null_upper_tail_p"]
    return {
        "source_lengths": {name: len(value) for name, value in source_map.items()},
        "salt_count": len(targets),
        "structural_spec_count": sum(1 for _ in structural_specs()),
        "structural_output_count": len(rows),
        "unique_bound_passphrase_count": len(unique_bound_materials),
        "null_trials_per_rule": null_trials,
        "phase32_oracle_positive": phase32_positive_control(phase32_blob),
        "phase32_selector_known_password_hits": phase32_selector_password_hits,
        "selector_known_answer_available": False,
        "minimum_null_upper_tail_p": minimum_p,
        "bonferroni_minimum_p": min(1.0, minimum_p * len(rows)),
        "best_rows": best_rows[:12],
        "hits": hits,
        "rows": rows,
    }


def self_test():
    source = tuple("abcdef")
    salt = bytes((0, 5, 1, 4, 2, 3, 3, 2))
    indices, selected = select_items(source, salt, "zero_mod_n", "forward", "original")
    assert indices == (0, 5, 1, 4, 2, 3, 3, 2)
    assert "".join(selected) == "afbecddc"
    _indices, selected = select_items(source, salt, "one_mod_n", "forward", "original")
    assert "".join(selected) == "feadbccb"
    _indices, selected = select_items(source, salt, "zero_mod_n", "reverse", "original")
    assert "".join(selected) == "faebdccd"
    assert ordered_bytes(bytes((2, 1, 2, 0, 1, 0, 2, 1)), "ascending") == (0, 0, 1, 1, 1, 2, 2, 2)
    assert ordered_bytes(bytes((2, 1, 2, 0, 1, 0, 2, 1)), "descending") == (2, 2, 2, 1, 1, 1, 0, 0)
    assert len(load_scene_words()) == EXPECTED_SCENE_WORDS
    report = audit(null_trials=32, run_oracles=False)
    assert report["source_lengths"] == {
        "DBBI_chars": 91,
        "FAED_chars": 570,
        "selection31_chars": 31,
        "matrix_scene1326_words": 1326,
    }
    assert report["salt_count"] == 5
    assert report["structural_spec_count"] == 12
    assert report["structural_output_count"] == 240
    assert 0.0 < report["minimum_null_upper_tail_p"] <= 1.0
    assert report["minimum_null_upper_tail_p"] <= report["bonferroni_minimum_p"] <= 1.0
    assert report["phase32_oracle_positive"]
    assert not report["phase32_selector_known_password_hits"]
    print("[*] self-test OK: selector mechanics, cached source, 240-case scope, and Phase 3.2 oracle control")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--null-trials", type=int, default=NULL_TRIALS_DEFAULT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report = audit(null_trials=args.null_trials)
    print(
        f"[*] scope: {report['salt_count']} salts x 4 sources x "
        f"{report['structural_spec_count']} rules = {report['structural_output_count']} outputs"
    )
    print(
        f"[*] exact bound passphrases after formatting/dedup: "
        f"{report['unique_bound_passphrase_count']}"
    )
    print(
        f"[*] Phase 3.2 AES positive={report['phase32_oracle_positive']}; "
        f"selector known-password hits={len(report['phase32_selector_known_password_hits'])}; "
        "known-answer selector calibration unavailable"
    )
    print(f"[*] random-salt null trials per rule: {report['null_trials_per_rule']}")
    print(
        f"[*] best uncorrected null tail={report['minimum_null_upper_tail_p']:.6f}; "
        f"Bonferroni across {report['structural_output_count']} outputs="
        f"{report['bonferroni_minimum_p']:.6f}"
    )
    for row in report["best_rows"]:
        printable = row["forms"].get("compact", row["forms"].get("exact"))
        print(
            f"    p={row['null_upper_tail_p']:.6f} {row['target']}/"
            f"{row['source']}/{row['index_rule']}/{row['orientation']}/"
            f"{row['byte_order']}: {printable!r}"
        )
    print(f"[*] exact oracle hits: {len(report['hits'])}")
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
