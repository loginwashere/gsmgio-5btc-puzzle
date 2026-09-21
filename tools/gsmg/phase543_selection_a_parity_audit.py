#!/usr/bin/env python3
"""Phase 543: close bounded parity gaps for Selection A's two row outputs.

This audit has three independently reported arms:

* rebuild the incomplete and terminal-e-completed matrices and evaluate the
  same row/column/reversal/Caesar families used for the historical guide;
* run both exact row outputs through the historical direct-passphrase cipher
  families (AES/3DES CBC, AES ECB/CFB/OFB/CTR, AES Key Wrap, and the bounded
  Blowfish/Camellia/SEED CBC menu gap);
* freeze the targeted Phase-524 slot-grammar delta obtained by substituting
  each new row output for the historical matrixsumlist value.

The matrix null shuffles the already-fixed DBBI groups over Selection A's
fixed endpoints and conditions on the same collision-free placement property.
For the completed matrix it additionally conditions on the terminal-e cell
remaining empty before that fixed completion is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    OPENSSL_MENU_GAP_CIPHER_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    answer_forms,
    keystr_forms,
)
from data import DBBI  # noqa: E402
from phase523_slot_grammar_overlap_audit import (  # noqa: E402
    SLOT_ORDER,
    enumerate_bases,
    expand_std,
    slot_values,
)
from phase525_dbbi_selection_a_reconstruction import (  # noqa: E402
    enumerate_complete_parses,
    parse_record,
    picture_events,
    compatible_selections,
)
from phase528_dbbi_84_token_consequence_audit import grouped_parse  # noqa: E402
from phase535_selection_a_matrix_composition import run as phase535_run  # noqa: E402
from telegram_yellow_blue_fefe_sweep import place_chunks  # noqa: E402
from telegram_yellow_blue_guide_audit import output_from_row_sums, token_value  # noqa: E402
from telegram_yellow_blue_matrix_direction_audit import (  # noqa: E402
    best_family_score,
    directional_outputs,
    expanded_outputs,
    matrix_from_spiral,
)


CANDIDATES = ("IZLKESKGGIPPEN", "IZLKEXKGGIPPEN")
OLDER_CBC_VARIANTS = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS)
RESULT_PATH = SCRIPT_DIR / "phase543_selection_a_parity_result.json"
WORK = ROOT / "_work" / "phase543"
SLOT_BASES_PATH = WORK / "slot_bases.txt"


def _selection_a_components():
    prior = phase535_run()
    selection = next(
        row for row in prior["rows"]
        if row["logical_length"] == 84
        and row["represents_source_bytes_1_through_23_once"]
    )
    tokens = next(
        parsed for parsed in enumerate_complete_parses(DBBI)
        if len(parsed) == 84
    )
    groups = grouped_parse(tokens)
    chunks = [
        tuple(token_value(ch) for ch in group["payload"]) + (token_value(group["host"]),)
        for group in groups["groups"]
    ]
    events = picture_events()
    matches = compatible_selections(events, parse_record(tokens)["host_colors"])
    match = next(row for row in matches if row["represents_source_bytes_1_through_23_once"])
    endpoints = [
        event["spiral_0"] for event in events
        if event["event_rank"] not in match["omitted_event_ranks"]
    ]
    terminal_destination = next(
        event["spiral_0"] for event in events if event["event_rank"] == 25
    )
    cells = tuple(selection["variants"][0]["spiral_cells"])
    assert groups["tail"] == "e" and len(chunks) == len(endpoints) == 23
    assert sum(map(len, chunks)) == 83 and sum(bool(x) for x in cells) == 83
    assert cells[terminal_destination] == 0
    return chunks, endpoints, terminal_destination, cells


def _matrix_record(cells):
    family = directional_outputs(matrix_from_spiral(cells))
    base_label, base_scores = best_family_score(family["outputs"])
    caesar_outputs = expanded_outputs(family["outputs"], True)
    caesar_label, caesar_scores = best_family_score(caesar_outputs)
    return {
        "occupied_cells": sum(bool(x) for x in cells),
        "row_sums": family["row_sums"],
        "column_sums": family["column_sums"],
        "diagonal_sums": family["diagonal_sums"],
        "outputs": family["outputs"],
        "diagonals": family["diagonals"],
        "best_direction": base_label,
        "best_direction_score": base_scores[base_label],
        "best_caesar_member": caesar_label,
        "best_caesar_output": caesar_outputs[caesar_label],
        "best_caesar_score": caesar_scores[caesar_label],
    }


def structural_audit(trials=20_000, seed=20260921):
    chunks, endpoints, destination, incomplete = _selection_a_components()
    complete = list(incomplete)
    complete[destination] = token_value("e")
    real = {
        "incomplete": _matrix_record(incomplete),
        "complete": _matrix_record(tuple(complete)),
    }
    assert real["incomplete"]["outputs"]["rows_forward"] == CANDIDATES[0]
    assert real["complete"]["outputs"]["rows_forward"] == CANDIDATES[1]

    rng = random.Random(seed)
    indices = list(range(len(chunks)))
    counts = {
        "incomplete": {"direction": 0, "caesar": 0},
        "complete": {"direction": 0, "caesar": 0},
    }
    accepted = {"incomplete": 0, "complete": 0}
    draws = 0
    max_draws = max(100_000, trials * 100)
    while min(accepted.values()) < trials:
        if draws >= max_draws:
            raise RuntimeError(f"null acceptance too low after {draws} draws: {accepted}")
        draws += 1
        rng.shuffle(indices)
        shuffled = [chunks[i] for i in indices]
        cells, collisions = place_chunks(shuffled, endpoints, "later_wins")
        if collisions:
            continue
        if accepted["incomplete"] < trials:
            rec = _matrix_record(tuple(cells))
            accepted["incomplete"] += 1
            counts["incomplete"]["direction"] += (
                rec["best_direction_score"] >= real["incomplete"]["best_direction_score"]
            )
            counts["incomplete"]["caesar"] += (
                rec["best_caesar_score"] >= real["incomplete"]["best_caesar_score"]
            )
        if cells[destination] == 0 and accepted["complete"] < trials:
            completed = list(cells)
            completed[destination] = token_value("e")
            rec = _matrix_record(tuple(completed))
            accepted["complete"] += 1
            counts["complete"]["direction"] += (
                rec["best_direction_score"] >= real["complete"]["best_direction_score"]
            )
            counts["complete"]["caesar"] += (
                rec["best_caesar_score"] >= real["complete"]["best_caesar_score"]
            )

    return {
        "seed": seed,
        "trials_per_matrix": trials,
        "permutation_draws": draws,
        "conditioning": (
            "shuffle 23 fixed DBBI groups over Selection A endpoints; accept collision-free; "
            "completed arm also requires the fixed event-25 cell empty before placing e"
        ),
        "matrices": {
            name: {
                **real[name],
                "direction_at_least_as_good": counts[name]["direction"],
                "direction_empirical_p": (counts[name]["direction"] + 1) / (trials + 1),
                "caesar_at_least_as_good": counts[name]["caesar"],
                "caesar_empirical_p": (counts[name]["caesar"] + 1) / (trials + 1),
            }
            for name in ("incomplete", "complete")
        },
    }


def unique_passphrases(candidates=CANDIDATES):
    seen = set()
    out = []
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystr in keystr_forms(form, newline_variants=True):
                material = keystr.encode()
                if material not in seen:
                    seen.add(material)
                    out.append(material)
    return tuple(out)


def _safe_hit(value):
    return repr(value)[:1000]


def direct_cipher_audit():
    materials = unique_passphrases()
    hits = {"older_cbc": [], "ecb": [], "stream": [], "keywrap": [], "menu_gap_cbc": []}
    for material in materials:
        for label, fn, variants in (
            ("older_cbc", aes_try_open_bytes, OLDER_CBC_VARIANTS),
            ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS),
            ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS),
            ("menu_gap_cbc", aes_try_open_bytes, OPENSSL_MENU_GAP_CIPHER_VARIANTS),
        ):
            result = fn(material, kdf_variants=variants, blobs=BLOBS)
            if result:
                hits[label].append(_safe_hit((material, result)))
        wrapped = aes_keywrap_try_open_bytes(material, blobs=BLOBS)
        if wrapped:
            hits["keywrap"].append(_safe_hit((material, wrapped)))
    n = len(materials)
    return {
        "candidates": CANDIDATES,
        "unique_passphrase_materials": n,
        "blobs": tuple(BLOBS),
        "variants": {
            "older_cbc": len(OLDER_CBC_VARIANTS),
            "ecb": len(ECB_CIPHER_VARIANTS),
            "stream": len(STREAM_CIPHER_VARIANTS),
            "keywrap_kdf": len(KEY_WRAP_KDF_VARIANTS),
            "menu_gap_cbc": len(OPENSSL_MENU_GAP_CIPHER_VARIANTS),
        },
        "effective_operations": (
            n * len(BLOBS) * (
                len(OLDER_CBC_VARIANTS)
                + len(ECB_CIPHER_VARIANTS)
                + len(STREAM_CIPHER_VARIANTS)
                + len(OPENSSL_MENU_GAP_CIPHER_VARIANTS)
            )
            + n * len(BLOBS) * len(KEY_WRAP_KDF_VARIANTS) * 4
        ),
        "hits": hits,
        "total_hits": sum(map(len, hits.values())),
    }


def prepare_slot_delta(write=True):
    original = slot_values()
    bases = []
    per_candidate = {}
    for candidate in CANDIDATES:
        values = {slot: list(items) for slot, items in original.items()}
        values["matrixsumlist"] = [(candidate, "Phase 543 Selection A row output")]
        selected = [
            base for _cell, base, _provenance in enumerate_bases(values)
            if candidate in base
        ]
        per_candidate[candidate] = len(selected)
        bases.extend(selected)
    bases = list(dict.fromkeys(bases))
    materials = set()
    for base in bases:
        materials.update(expand_std(base, True))
    body = "\n".join(bases) + "\n"
    if write:
        WORK.mkdir(parents=True, exist_ok=True)
        SLOT_BASES_PATH.write_text(body, encoding="utf-8")
    return {
        "slot_order": SLOT_ORDER,
        "substituted_slot": "matrixsumlist",
        "candidates": CANDIDATES,
        "bases_per_candidate": per_candidate,
        "unique_bases": len(bases),
        "base_list_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "unique_standard_materials": len(materials),
        "expected_gpu_forms": sum(len(expand_std(base, True)) for base in bases),
        "wordlist": str(SLOT_BASES_PATH.relative_to(ROOT)),
        "oracle_status": "prepared-not-run",
    }


def verify_slot_delta(hits_path):
    from phase524_slot_grammar_sweep_prep import classify_weak

    path = Path(hits_path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    kinds = {kind: sum(row.get("hit_kind") == kind for row in rows)
             for kind in ("weak", "strong", "structural")}
    weak_review = classify_weak(path)
    return {
        "oracle_status": "complete-cpu-deduplicated-materials",
        "variant_table": "4 KDFs x 3 AES key sizes x CBC/ECB/CFB/OFB/CTR",
        "blobs": tuple(BLOBS),
        "materials_tested": 381_672,
        "effective_decryptions": 381_672 * 60 * len(BLOBS),
        "hit_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "hit_rows": len(rows),
        "hit_kinds": kinds,
        "max_weak_z": max((row["z_score"] for row in rows), default=None),
        "weak_review": weak_review,
    }


def self_test():
    structural = structural_audit(trials=20, seed=1)
    assert structural["matrices"]["incomplete"]["outputs"]["rows_forward"] == CANDIDATES[0]
    assert structural["matrices"]["complete"]["outputs"]["rows_forward"] == CANDIDATES[1]
    assert len(unique_passphrases()) == 36
    slot = prepare_slot_delta(write=False)
    assert slot["bases_per_candidate"] == {candidate: 7039 for candidate in CANDIDATES}
    assert slot["unique_bases"] == 14078
    return {"structural": "ok", "passphrase_materials": 36, "slot_bases": 14078}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--structural", action="store_true")
    parser.add_argument("--direct", action="store_true")
    parser.add_argument("--prepare-slots", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trials", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--slot-hits")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return
    do_all = args.all or not (args.structural or args.direct or args.prepare_slots)
    report = {"phase": 543, "candidates": CANDIDATES}
    if do_all or args.structural:
        report["structural"] = structural_audit(args.trials, args.seed)
    if do_all or args.direct:
        report["direct_cipher"] = direct_cipher_audit()
    if do_all or args.prepare_slots:
        report["slot_delta"] = prepare_slot_delta(write=True)
        if args.slot_hits:
            report["slot_delta"].update(verify_slot_delta(args.slot_hits))
    report["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.write:
        RESULT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
