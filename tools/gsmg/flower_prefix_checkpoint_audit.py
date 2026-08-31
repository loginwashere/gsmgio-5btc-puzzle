#!/usr/bin/env python3
"""Audit FLOW + reversed even(TRUE) -> FLOWER -> THEFLOWER.

The target predates this construction: THEFLOWER is the exact prefix of the
verified Phase-1 password. The audit enumerates every base direction, TRUE
parity rail, rail direction, join side, selected-word affix, and row-sum pair.
"""

import argparse
import hashlib
from collections import Counter

import cb_common
from cb_common import (
    BLOBS,
    ECB_CIPHER_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    answer_forms,
)
from first_hint_hash_audit import PHASE1_PASSWORD, PHASE1_PASSWORD_SHA256
from prime_matrixsum_reconstruction import load_architect_words
from second_prime_matrixsumlist_audit import (
    CBC_VARIANTS,
    EXPECTED_FIRST_SUM_LIST,
    audit as matrix_audit,
    framed_edges,
    selected_words,
)


EXPECTED_CORE = "flower"
EXPECTED_PREFIX = "theflower"
EXPECTED_PHASE1_PASSWORD = (
    b"theflowerblossomsthroughwhatseemstobeaconcretesurface"
)
EXPECTED_PHASE1_SHA256 = (
    "5ac407837447fba24ba2802e4d1e9aecb4580aa29fef1088cc387c180b746f75"
)
EXPECTED_CANDIDATE_FORMS = 6


def parity_compositions(base, control):
    """Complete direction x parity x direction x join-side family."""
    results = []
    for base_direction, base_value in (
        ("forward", base),
        ("reverse", base[::-1]),
    ):
        for parity, rail in (
            ("odd", control[0::2]),
            ("even", control[1::2]),
        ):
            for rail_direction, rail_value in (
                ("forward", rail),
                ("reverse", rail[::-1]),
            ):
                for join_side in ("append", "prepend"):
                    value = (
                        base_value + rail_value
                        if join_side == "append"
                        else rail_value + base_value
                    )
                    results.append(
                        {
                            "base_direction": base_direction,
                            "parity": parity,
                            "rail_direction": rail_direction,
                            "join_side": join_side,
                            "value": value,
                        }
                    )
    return tuple(results)


def affix_family(compositions, words):
    results = []
    for composition in compositions:
        core = composition["value"]
        for word_index, word in enumerate(words):
            for side in ("prefix", "suffix"):
                value = word + core if side == "prefix" else core + word
                results.append(
                    {
                        "composition": composition,
                        "word_index": word_index,
                        "word": word,
                        "side": side,
                        "value": value,
                    }
                )
    return tuple(results)


def complete_row_sum_sweep(tokens, first_words):
    counts = Counter()
    hits = []
    for row1 in range(1, 28):
        for row2 in range(1, 28):
            second_indices = (row1 + row2, row1, row2)
            combined_indices = (
                EXPECTED_FIRST_SUM_LIST[0] + row1 + row2,
                EXPECTED_FIRST_SUM_LIST[1] + row1,
                EXPECTED_FIRST_SUM_LIST[2] + row2,
            )
            if max((*second_indices, *combined_indices)) > len(tokens):
                counts["unindexable_pairs"] += 1
                continue
            counts["indexable_pairs"] += 1
            second_words = selected_words(tokens, second_indices)
            combined_words = selected_words(tokens, combined_indices)
            second_frame = framed_edges(second_words)
            combined_frame = framed_edges(combined_words)
            compositions = parity_compositions(second_frame, combined_frame)
            counts["compositions"] += len(compositions)
            counts["flower_cores"] += sum(
                item["value"] == EXPECTED_CORE for item in compositions
            )
            affixes = affix_family(
                compositions, first_words + second_words + combined_words
            )
            counts["affix_variants"] += len(affixes)
            for item in affixes:
                if item["value"] != EXPECTED_PREFIX:
                    continue
                counts["prefix_hits"] += 1
                hits.append(
                    {
                        "row_sums": (row1, row2),
                        "second_indices": second_indices,
                        "combined_indices": combined_indices,
                        **item,
                    }
                )
    return counts, tuple(hits)


def derived_candidates():
    candidates = {
        "core": "flower",
        "authenticated_prefix": "theflower",
        "authenticated_prefix_spaced": "the flower",
    }
    seen = set()
    forms = []
    for label, candidate in candidates.items():
        for form in sorted(answer_forms(candidate)):
            material = form.encode()
            if not material or material in seen:
                continue
            seen.add(material)
            forms.append((label, form, material))
    return candidates, tuple(forms)


def audit():
    matrix = matrix_audit(run_null=False)
    tokens, _ = load_architect_words()
    base = matrix["frames"][1]
    control = matrix["frames"][2]
    compositions = parity_compositions(base, control)
    selected_word_occurrences = (
        matrix["first_words"] + matrix["words"] + matrix["combined_words"]
    )
    affixes = affix_family(compositions, selected_word_occurrences)
    sweep_counts, sweep_hits = complete_row_sum_sweep(
        tokens, matrix["first_words"]
    )
    _, candidate_forms = derived_candidates()
    return {
        "base": base,
        "control": control,
        "odd_rail": control[0::2],
        "even_rail": control[1::2],
        "compositions": compositions,
        "core_hits": tuple(
            item for item in compositions if item["value"] == EXPECTED_CORE
        ),
        "selected_word_occurrences": selected_word_occurrences,
        "affixes": affixes,
        "affix_unique_values": len({item["value"] for item in affixes}),
        "prefix_hits": tuple(
            item for item in affixes if item["value"] == EXPECTED_PREFIX
        ),
        "sweep_counts": sweep_counts,
        "sweep_hits": sweep_hits,
        "phase1_password": PHASE1_PASSWORD,
        "phase1_password_sha256": PHASE1_PASSWORD_SHA256,
        "candidate_forms": candidate_forms,
    }


def oracle_audit():
    _, passphrases = derived_candidates()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    original_logger = cb_common._log_candidate
    cb_common._log_candidate = lambda *args, **kwargs: None
    try:
        for label, form, material in passphrases:
            result = aes_try_open_bytes(
                material, kdf_variants=CBC_VARIANTS, blobs=BLOBS
            )
            if result:
                hits["cbc"].append((label, form, result))
            result = aes_try_open_ecb_bytes(material, blobs=BLOBS)
            if result:
                hits["ecb"].append((label, form, result))
            result = aes_try_open_stream_bytes(material, blobs=BLOBS)
            if result:
                hits["stream"].append((label, form, result))
            for result in aes_keywrap_try_open_bytes(material, blobs=BLOBS):
                hits["keywrap"].append((label, form, result))
    finally:
        cb_common._log_candidate = original_logger

    count = len(passphrases)
    blob_count = len(BLOBS)
    return {
        "passphrase_count": count,
        "cbc_decryptions": count * len(CBC_VARIANTS) * blob_count,
        "ecb_decryptions": count * len(ECB_CIPHER_VARIANTS) * blob_count,
        "stream_decryptions": count * len(STREAM_CIPHER_VARIANTS) * blob_count,
        "keywrap_effective_unwrap_attempts": (
            count * len(KEY_WRAP_KDF_VARIANTS) * blob_count * 4
        ),
        "hits": hits,
        "total_hits": sum(len(entries) for entries in hits.values()),
    }


def self_test(run_oracle=False):
    result = audit()
    assert (result["base"], result["control"]) == ("flow", "true")
    assert (result["odd_rail"], result["even_rail"]) == ("tu", "re")
    assert len(result["compositions"]) == 16
    assert len({item["value"] for item in result["compositions"]}) == 16
    assert result["core_hits"] == (
        {
            "base_direction": "forward",
            "parity": "even",
            "rail_direction": "reverse",
            "join_side": "append",
            "value": "flower",
        },
    )
    assert len(result["selected_word_occurrences"]) == 9
    assert len(result["affixes"]) == 288
    assert result["affix_unique_values"] == 256
    assert len(result["prefix_hits"]) == 1
    prefix_hit = result["prefix_hits"][0]
    assert (
        prefix_hit["word_index"],
        prefix_hit["word"],
        prefix_hit["side"],
        prefix_hit["value"],
    ) == (2, "the", "prefix", "theflower")
    assert result["sweep_counts"] == Counter(
        indexable_pairs=714,
        unindexable_pairs=15,
        compositions=11424,
        flower_cores=1,
        affix_variants=205632,
        prefix_hits=1,
    )
    assert len(result["sweep_hits"]) == 1
    assert result["sweep_hits"][0]["row_sums"] == (5, 9)
    assert result["phase1_password"] == EXPECTED_PHASE1_PASSWORD
    assert result["phase1_password"].startswith(EXPECTED_PREFIX.encode())
    assert result["phase1_password_sha256"] == EXPECTED_PHASE1_SHA256
    assert hashlib.sha256(result["phase1_password"]).hexdigest() == (
        EXPECTED_PHASE1_SHA256
    )
    assert len(result["candidate_forms"]) == EXPECTED_CANDIDATE_FORMS
    if run_oracle:
        oracle = oracle_audit()
        assert oracle["total_hits"] == 0, oracle["hits"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", action="store_true")
    args = parser.parse_args()
    self_test(run_oracle=False)
    result = audit()
    print(f"frames: {result['base'].upper()} / {result['control'].upper()}")
    print(
        f"TRUE rails: odd={result['odd_rail'].upper()} "
        f"even={result['even_rail'].upper()}"
    )
    core = result["core_hits"][0]
    print(
        "unique core: "
        f"{result['base'].upper()} + reverse(even(TRUE)) = "
        f"{core['value'].upper()}"
    )
    print(
        f"fixed affix family: 1/{len(result['affixes'])} labeled variants -> "
        f"{result['prefix_hits'][0]['value'].upper()}"
    )
    counts = result["sweep_counts"]
    print(
        f"complete sweep: {counts['prefix_hits']}/{counts['affix_variants']} "
        f"THEFLOWER hits; row sums={result['sweep_hits'][0]['row_sums']}"
    )
    print(
        "authenticated password prefix:",
        result["phase1_password"].decode(),
    )
    print(f"candidate forms: {len(result['candidate_forms'])}")
    if args.oracle:
        oracle = oracle_audit()
        assert oracle["total_hits"] == 0, oracle["hits"]
        print(
            "oracle attempts: "
            f"CBC={oracle['cbc_decryptions']}, "
            f"ECB={oracle['ecb_decryptions']}, "
            f"stream={oracle['stream_decryptions']}, "
            f"KeyWrap={oracle['keywrap_effective_unwrap_attempts']}"
        )
        print(f"oracle hits: {oracle['total_hits']}")


if __name__ == "__main__":
    main()
