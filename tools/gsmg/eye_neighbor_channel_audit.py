#!/usr/bin/env python3
"""Extract immediate neighbors of every literal ``i`` in DBBI and FAED.

The title-level I/eye observation is extended with no free positional choices:
for each internal ``i`` preserve its immediate left/right pair, then render the
two rails as left, right, alternating LR/RL, or concatenated L||R/R||L.  Exact
outputs and only their SHA-256/first-32/last-32 forms reach the established
oracles.  A fixed-position shuffle null checks whether either paired channel is
more language-like or more equal/mirror9-correlated than ordinary neighbors.
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS, aes_try_open_bytes, raw_key_try_open  # noqa: E402
from color_mask_full_stream_audit import passphrase_hits, scalar_hits  # noqa: E402
from data import DBBI, FAED, PHASE32_BLOB_B64, PHASE32_PASSWORD  # noqa: E402
from salt_selector_permutation_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
)
from cb_common import _load_blob  # noqa: E402


SOURCES = {"DBBI": DBBI, "FAED": FAED}
MARKERS = ("seed", "yang", "salvation", "bitcoin", "privatekey", "matrix", "choice")
NULL_TRIALS_DEFAULT = 2000


def neighbor_pairs(text):
    positions = tuple(
        index
        for index, char in enumerate(text)
        if char.lower() == "i" and 0 < index < len(text) - 1
    )
    return positions, tuple((text[index - 1], text[index + 1]) for index in positions)


def channel_forms(pairs):
    left = "".join(pair[0] for pair in pairs)
    right = "".join(pair[1] for pair in pairs)
    return {
        "left": left,
        "right": right,
        "alternating_lr": "".join(a + b for a, b in pairs),
        "alternating_rl": "".join(b + a for a, b in pairs),
        "rails_lr": left + right,
        "rails_rl": right + left,
    }


def mirror9_pair(left, right):
    return left in "abcdefghi" and right in "abcdefghi" and (
        ord(left) + ord(right) == ord("a") + ord("i")
    )


def pair_metrics(pairs):
    return {
        "equal_pairs": sum(left == right for left, right in pairs),
        "mirror9_pairs": sum(mirror9_pair(left, right) for left, right in pairs),
    }


def shuffled_preserving_i(text, rng):
    movable_positions = [index for index, char in enumerate(text) if char.lower() != "i"]
    movable = [text[index] for index in movable_positions]
    rng.shuffle(movable)
    result = list(text)
    for index, char in zip(movable_positions, movable):
        result[index] = char
    return "".join(result)


def null_calibration(source_name, text, model, trials):
    positions, real_pairs = neighbor_pairs(text)
    real_forms = channel_forms(real_pairs)
    real_metrics = pair_metrics(real_pairs)
    seed = int.from_bytes(hashlib.sha256(source_name.encode("ascii")).digest()[:8], "big")
    rng = random.Random(seed)
    form_scores = {name: [] for name in real_forms}
    metric_values = {name: [] for name in real_metrics}
    for _ in range(trials):
        shuffled = shuffled_preserving_i(text, rng)
        shuffled_positions, pairs = neighbor_pairs(shuffled)
        if shuffled_positions != positions:
            raise AssertionError("fixed-i shuffle changed eye positions")
        for name, value in channel_forms(pairs).items():
            form_scores[name].append(quadgram_score(value.encode("ascii"), model))
        for name, value in pair_metrics(pairs).items():
            metric_values[name].append(value)
    form_report = {}
    for name, value in real_forms.items():
        score = quadgram_score(value.encode("ascii"), model)
        form_report[name] = {
            "score": score,
            "upper_tail_p": (
                1 + sum(control >= score for control in form_scores[name])
            ) / (trials + 1),
        }
    metric_report = {
        name: {
            "value": value,
            "upper_tail_p": (
                1 + sum(control >= value for control in metric_values[name])
            ) / (trials + 1),
        }
        for name, value in real_metrics.items()
    }
    return form_report, metric_report


def derived_forms(material):
    encoded = material.encode("ascii")
    forms = {"sha256": hashlib.sha256(encoded).digest()}
    if len(encoded) >= 32:
        forms["first32"] = encoded[:32]
        forms["last32"] = encoded[-32:]
    return forms


def title_control():
    headings = ("SalPhaseIon", "Cosmic Duality")
    rows = {}
    all_pairs = []
    for heading in headings:
        positions, pairs = neighbor_pairs(heading)
        all_pairs.extend((left.lower(), right.lower()) for left, right in pairs)
        rows[heading] = {
            "positions_zero_based": positions,
            "pairs": tuple(left.lower() + right.lower() for left, right in pairs),
            "left": "".join(left.lower() for left, _right in pairs),
            "right": "".join(right.lower() for _left, right in pairs),
        }
    combined = channel_forms(tuple(all_pairs))
    return {"headings": rows, "combined": combined}


def octal_feasibility(text):
    """Check the literal OCT reading without offsets, padding, or digit remaps."""
    without_i = text.replace("i", "")
    values = []
    for offset in range(0, len(without_i) - 2, 3):
        group = without_i[offset:offset + 3]
        values.append(sum((ord(char) - ord("a")) * 8 ** (2 - index) for index, char in enumerate(group)))
    segment_lengths = tuple(len(segment) for segment in text.split("i"))
    return {
        "removed_i_length": len(without_i),
        "removed_i_mod3": len(without_i) % 3,
        "complete_triples": len(values),
        "byte_range_triples": sum(value <= 0xFF for value in values),
        "separator_segment_lengths": segment_lengths,
        "empty_separator_segments": sum(length == 0 for length in segment_lengths),
        "all_separator_segments_are_triples": bool(segment_lengths) and all(
            length == 3 for length in segment_lengths
        ),
    }


def phase32_oracle_positive():
    blob = _load_blob(PHASE32_BLOB_B64)
    return aes_try_open_bytes(PHASE32_PASSWORD.encode("ascii"), blobs={"PHASE32": blob}) is not None


def audit(null_trials=NULL_TRIALS_DEFAULT, run_oracles=True):
    if null_trials < 1:
        raise ValueError("null_trials must be positive")
    model = load_quadgrams()
    reports = []
    exact_material_count = 0
    derived_form_count = 0
    derived_materials = set()
    hits = []
    all_form_p = []
    for source_name, text in SOURCES.items():
        positions, pairs = neighbor_pairs(text)
        forms = channel_forms(pairs)
        form_null, metric_null = null_calibration(
            source_name, text, model, null_trials
        )
        form_reports = {}
        for form_name, material in forms.items():
            exact_material_count += 1
            exact_hits = passphrase_hits(material.encode("ascii"), BLOBS) if run_oracles else []
            all_form_p.append(form_null[form_name]["upper_tail_p"])
            derived_report = {}
            for derived_name, value in derived_forms(material).items():
                derived_form_count += 1
                derived_materials.add(value)
                pass_hits = passphrase_hits(value, BLOBS) if run_oracles else []
                raw_hits = [repr(item) for item in raw_key_try_open(value)] if run_oracles else []
                address_hits = scalar_hits(value) if run_oracles else []
                for family, rows in (
                    ("exact_passphrase", exact_hits),
                    (f"{derived_name}_passphrase", pass_hits),
                    (f"{derived_name}_raw_key", raw_hits),
                    (f"{derived_name}_scalar", address_hits),
                ):
                    for row in rows:
                        hits.append({
                            "source": source_name,
                            "form": form_name,
                            "consumer": family,
                            "result": row,
                        })
                derived_report[derived_name] = {
                    "hex": value.hex(),
                    "passphrase_hits": pass_hits,
                    "raw_key_hits": raw_hits,
                    "scalar_hits": address_hits,
                }
            form_reports[form_name] = {
                "material": material,
                "length": len(material),
                "marker_hits": tuple(marker for marker in MARKERS if marker in material),
                "null": form_null[form_name],
                "exact_passphrase_hits": exact_hits,
                "derived": derived_report,
            }
        reports.append({
            "source": source_name,
            "source_length": len(text),
            "i_count": text.count("i"),
            "internal_i_count": len(positions),
            "positions_zero_based": positions,
            "pair_metrics": metric_null,
            "forms": form_reports,
        })
    minimum_p = min(all_form_p)
    return {
        "title_control": title_control(),
        "octal_feasibility": {
            source_name: octal_feasibility(text)
            for source_name, text in SOURCES.items()
        },
        "phase32_oracle_positive": phase32_oracle_positive(),
        "null_trials_per_source": null_trials,
        "source_count": len(SOURCES),
        "layout_count_per_source": 6,
        "exact_output_count": exact_material_count,
        "derived_32byte_form_count": derived_form_count,
        "unique_derived_32byte_material_count": len(derived_materials),
        "minimum_language_tail_p": minimum_p,
        "bonferroni_language_p": min(1.0, minimum_p * exact_material_count),
        "reports": reports,
        "hits": hits,
    }


def self_test():
    positions, pairs = neighbor_pairs("aibic")
    assert positions == (1, 3)
    assert pairs == (("a", "b"), ("b", "c"))
    assert channel_forms(pairs) == {
        "left": "ab",
        "right": "bc",
        "alternating_lr": "abbc",
        "alternating_rl": "bacb",
        "rails_lr": "abbc",
        "rails_rl": "bcab",
    }
    titles = title_control()
    assert titles["headings"]["SalPhaseIon"]["pairs"] == ("eo",)
    assert titles["headings"]["Cosmic Duality"]["pairs"] == ("mc", "lt")
    assert titles["combined"]["left"] == "eml"
    assert titles["combined"]["right"] == "oct"
    assert octal_feasibility(DBBI)["removed_i_mod3"] == 2
    assert octal_feasibility(FAED)["removed_i_mod3"] == 0
    report = audit(null_trials=32, run_oracles=False)
    assert [(row["i_count"], row["internal_i_count"]) for row in report["reports"]] == [
        (5, 5),
        (75, 75),
    ]
    assert report["exact_output_count"] == 12
    assert report["derived_32byte_form_count"] == 24
    assert report["unique_derived_32byte_material_count"] == 20
    assert report["phase32_oracle_positive"]
    print("[*] self-test OK: title/synthetic extraction, 5/75 eyes, six layouts, null and oracle wiring")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--null-trials", type=int, default=NULL_TRIALS_DEFAULT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report = audit(null_trials=args.null_trials)
    print(f"[*] title control combined channels: {report['title_control']['combined']}")
    print(f"[*] literal OCT feasibility: {report['octal_feasibility']}")
    for source in report["reports"]:
        print(
            f"[*] {source['source']}: length={source['source_length']} "
            f"i={source['i_count']} internal={source['internal_i_count']} "
            f"equal={source['pair_metrics']['equal_pairs']} "
            f"mirror9={source['pair_metrics']['mirror9_pairs']}"
        )
        for form_name, form in source["forms"].items():
            print(
                f"    {form_name} ({form['length']}): {form['material']} "
                f"p={form['null']['upper_tail_p']:.6f}"
            )
    print(
        f"[*] language null minimum={report['minimum_language_tail_p']:.6f}; "
        f"Bonferroni across 12={report['bonferroni_language_p']:.6f}"
    )
    print(
        f"[*] exact outputs={report['exact_output_count']} "
        f"derived32={report['derived_32byte_form_count']} forms/"
        f"{report['unique_derived_32byte_material_count']} unique "
        f"Phase3.2 AES positive={report['phase32_oracle_positive']} "
        f"oracle hits={len(report['hits'])}"
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
