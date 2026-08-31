#!/usr/bin/env python3
"""Continue the rotation-derived second prime through ``matrixsumlist``.

The candidate universe is frozen before the blob oracle runs. Structural
claims and the complete six-digit-prime null are available without an oracle;
``--oracle`` adds the project's existing CBC/ECB/stream/Key-Wrap checks.
"""

import argparse
from collections import Counter

import cb_common
from cb_common import (
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
    answer_forms,
)
from denis_rotation_grille_audit import audit as rotation_audit
from first_piece_color_reconstruction import is_prime
from prime_matrixsum_reconstruction import (
    bounded_indexings,
    edge_letters,
    load_architect_words,
)


EXPECTED_SECOND_PRIME = 311027
EXPECTED_FIRST_SUM_LIST = (23, 16, 7)
EXPECTED_MATRIX = ((3, 1, 1), (0, 2, 7))
EXPECTED_SUM_LIST = (14, 5, 9)
EXPECTED_COMBINED_MATRIX = ((8, 8, 5), (0, 8, 8))
EXPECTED_COMBINED_SUM_LIST = (37, 21, 16)
EXPECTED_WORDS = ("flaw", "last", "of")
EXPECTED_INITIALS = "flo"
EXPECTED_ENDINGS = "wtf"
EXPECTED_REVERSED_ENDINGS = "ftw"
EXPECTED_SIX_DIGIT_PRIMES = 68906
EXPECTED_WTF_PRIMES = 78
EXPECTED_ABSTRACT_TRIPLES = 729
EXPECTED_FRAMES = ("buth", "flow", "true")
EXPECTED_CANDIDATE_FORMS = 40
CBC_VARIANTS = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS)


def matrix_sum_list(number):
    digits = tuple(int(character) for character in str(number))
    if len(digits) != 6:
        raise ValueError("expected a six-digit number")
    matrix = (digits[:3], digits[3:])
    return matrix, (sum(digits), sum(matrix[0]), sum(matrix[1]))


def selected_words(tokens, indices):
    if min(indices) < 1 or max(indices) > len(tokens):
        raise ValueError("one-based index is outside the frozen source")
    return tuple(tokens[index - 1] for index in indices)


def framed_edges(words, frame_index=0):
    """Frame row-word initials with the total-word beginning and end."""
    if len(words) != 3:
        raise ValueError("the framed rule expects total plus two row words")
    if frame_index not in range(3):
        raise ValueError("frame index must be 0, 1, or 2")
    frame = words[frame_index]
    inner = [word for index, word in enumerate(words) if index != frame_index]
    return frame[0] + "".join(word[0] for word in inner) + frame[-1]


def abstract_sumlist_hits(tokens, target=EXPECTED_ENDINGS):
    """Enumerate every positive row-sum pair achievable by three digits.

    Each three-digit row has sum 0..27. Zero cannot be a one-based word index,
    leaving the complete 27 x 27 family; total is row1 + row2.
    """
    hits = []
    for row1 in range(1, 28):
        for row2 in range(1, 28):
            indices = (row1 + row2, row1, row2)
            words = selected_words(tokens, indices)
            if edge_letters(words)[1] == target:
                hits.append((indices, words))
    return tuple(hits)


def combined_frame_hits(tokens):
    """Complete fixed-first-prime family for FLOW and combined TRUE."""
    hits = []
    indexable = 0
    for row1 in range(1, 28):
        for row2 in range(1, 28):
            second = (row1 + row2, row1, row2)
            combined = (
                EXPECTED_FIRST_SUM_LIST[0] + row1 + row2,
                EXPECTED_FIRST_SUM_LIST[1] + row1,
                EXPECTED_FIRST_SUM_LIST[2] + row2,
            )
            if max((*second, *combined)) > len(tokens):
                continue
            indexable += 1
            second_frame = framed_edges(selected_words(tokens, second))
            combined_frame = framed_edges(selected_words(tokens, combined))
            if (second_frame, combined_frame) == ("flow", "true"):
                hits.append(((row1, row2), second, combined))
    return indexable, tuple(hits)


def frame_role_sweep(tokens, frame_index):
    """Count FLOW/TRUE hits for one of the three possible frame roles."""
    counts = Counter()
    joint_hits = []
    for row1 in range(1, 28):
        for row2 in range(1, 28):
            second = (row1 + row2, row1, row2)
            combined = (
                EXPECTED_FIRST_SUM_LIST[0] + row1 + row2,
                EXPECTED_FIRST_SUM_LIST[1] + row1,
                EXPECTED_FIRST_SUM_LIST[2] + row2,
            )
            if max((*second, *combined)) > len(tokens):
                continue
            counts["indexable"] += 1
            second_frame = framed_edges(
                selected_words(tokens, second), frame_index
            )
            combined_frame = framed_edges(
                selected_words(tokens, combined), frame_index
            )
            flow = second_frame == "flow"
            true = combined_frame == "true"
            counts["flow"] += flow
            counts["true"] += true
            counts["joint"] += flow and true
            if flow and true:
                joint_hits.append(((row1, row2), second, combined))
    return counts, tuple(joint_hits)


def six_digit_prime_null(tokens):
    limit = 1_000_000
    sieve = bytearray(b"\x01") * limit
    sieve[:2] = b"\x00\x00"
    for prime in range(2, int(limit ** 0.5) + 1):
        if not sieve[prime]:
            continue
        start = prime * prime
        sieve[start:limit:prime] = b"\x00" * (((limit - 1 - start) // prime) + 1)

    counts = Counter()
    examples = []
    target_seen = False
    for number in range(100000, limit):
        if not sieve[number]:
            continue
        counts["six_digit_primes"] += 1
        _, indices = matrix_sum_list(number)
        words = selected_words(tokens, indices)
        if edge_letters(words)[1] != EXPECTED_ENDINGS:
            continue
        counts["wtf_primes"] += 1
        target_seen |= number == EXPECTED_SECOND_PRIME
        if len(examples) < 10:
            examples.append(number)
    return counts, tuple(examples), target_seen


def derived_candidates():
    """Closed candidate family implied directly by the two three-word rails."""
    candidates = {
        "initials": "flo",
        "initials_reversed": "olf",
        "endings": "wtf",
        "endings_reversed": "ftw",
        "words": "flawlastof",
        "words_reversed": "oflastflaw",
        "endings_expanded": "what the fuck",
        "endings_reversed_expanded": "for the win",
        "prime_decimal": "311027",
        "prime_hex": "04BEF3",
        "sum_list": "1459",
        "first_frame": "buth",
        "first_frame_split": "but h",
        "second_frame": "flow",
        "second_frame_reversed": "wolf",
        "combined_frame": "true",
        "framed_sequence": "buthflowtrue",
        "framed_sequence_spaced": "but h flow true",
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


def audit(run_null=True):
    rotation = rotation_audit()
    second_prime = rotation["inverse_values"][1]
    matrix, sum_list = matrix_sum_list(second_prime)
    tokens, boundary_word = load_architect_words()
    words = selected_words(tokens, sum_list)
    initials, endings = edge_letters(words)
    first_words = selected_words(tokens, EXPECTED_FIRST_SUM_LIST)
    combined_matrix = tuple(
        tuple(left + right for left, right in zip(left_row, right_row))
        for left_row, right_row in zip(((5, 7, 4), (0, 6, 1)), matrix)
    )
    combined_sum_list = (
        sum(sum(row) for row in combined_matrix),
        *(sum(row) for row in combined_matrix),
    )
    combined_words = selected_words(tokens, combined_sum_list)
    frames = (
        framed_edges(first_words),
        framed_edges(words),
        framed_edges(combined_words),
    )
    frame_role_outputs = (
        tuple(framed_edges(first_words, role) for role in range(3)),
        tuple(framed_edges(words, role) for role in range(3)),
        tuple(framed_edges(combined_words, role) for role in range(3)),
    )
    frame_indexable, frame_hits = combined_frame_hits(tokens)
    frame_role_sweeps = tuple(frame_role_sweep(tokens, role) for role in range(3))
    second_frame_indexings = {
        mode: framed_edges(mode_words)
        for mode, mode_words in bounded_indexings(tokens, sum_list).items()
    }
    combined_frame_indexings = {
        mode: framed_edges(mode_words)
        for mode, mode_words in bounded_indexings(tokens, combined_sum_list).items()
    }
    abstract_hits = abstract_sumlist_hits(tokens)
    null_counts, null_examples, target_seen = (
        six_digit_prime_null(tokens)
        if run_null
        else (Counter(), (), False)
    )
    candidates, candidate_forms = derived_candidates()
    return {
        "second_prime": second_prime,
        "second_prime_is_prime": is_prime(second_prime),
        "matrix": matrix,
        "sum_list": sum_list,
        "words": words,
        "first_words": first_words,
        "combined_matrix": combined_matrix,
        "combined_sum_list": combined_sum_list,
        "combined_words": combined_words,
        "frames": frames,
        "frame_role_outputs": frame_role_outputs,
        "second_frame_reversed": frames[1][::-1],
        "frame_indexable": frame_indexable,
        "frame_hits": frame_hits,
        "frame_role_sweeps": frame_role_sweeps,
        "second_frame_indexings": second_frame_indexings,
        "combined_frame_indexings": combined_frame_indexings,
        "initials": initials,
        "endings": endings,
        "reversed_initials": initials[::-1],
        "reversed_endings": endings[::-1],
        "boundary_word": boundary_word,
        "abstract_hits": abstract_hits,
        "null_counts": null_counts,
        "null_examples": null_examples,
        "target_seen_in_null": target_seen,
        "candidates": candidates,
        "candidate_forms": candidate_forms,
    }


def oracle_audit():
    """Run the fixed candidate forms without mutating the shared weak-hit log."""
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
        "blob_count": blob_count,
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
    result = audit(run_null=True)
    assert result["second_prime"] == EXPECTED_SECOND_PRIME
    assert result["second_prime_is_prime"]
    assert result["matrix"] == EXPECTED_MATRIX
    assert result["sum_list"] == EXPECTED_SUM_LIST
    assert result["words"] == EXPECTED_WORDS
    assert result["combined_matrix"] == EXPECTED_COMBINED_MATRIX
    assert result["combined_sum_list"] == EXPECTED_COMBINED_SUM_LIST
    assert result["frames"] == EXPECTED_FRAMES
    assert result["frame_role_outputs"] == (
        ("buth", "ubty", "tbue"),
        ("flow", "lfot", "oflf"),
        ("true", "rtud", "utry"),
    )
    assert result["second_frame_reversed"] == "wolf"
    assert result["frame_indexable"] == 714
    assert result["frame_hits"] == (
        ((5, 9), EXPECTED_SUM_LIST, EXPECTED_COMBINED_SUM_LIST),
    )
    assert result["frame_role_sweeps"] == (
        (
            Counter(indexable=714, flow=1, true=1, joint=1),
            (((5, 9), EXPECTED_SUM_LIST, EXPECTED_COMBINED_SUM_LIST),),
        ),
        (Counter(indexable=714, true=1), ()),
        (Counter(indexable=714), ()),
    )
    assert result["second_frame_indexings"] == {
        "forward_one": "flow",
        "forward_zero": "itts",
        "backward_one": "aayd",
        "backward_zero": "hyor",
    }
    assert result["combined_frame_indexings"] == {
        "forward_one": "true",
        "forward_zero": "yaeu",
        "backward_one": "wltl",
        "backward_zero": "rlmt",
    }
    assert result["initials"] == EXPECTED_INITIALS
    assert result["endings"] == EXPECTED_ENDINGS
    assert result["reversed_endings"] == EXPECTED_REVERSED_ENDINGS
    assert result["abstract_hits"] == ((EXPECTED_SUM_LIST, EXPECTED_WORDS),)
    assert result["null_counts"] == Counter(
        six_digit_primes=EXPECTED_SIX_DIGIT_PRIMES,
        wtf_primes=EXPECTED_WTF_PRIMES,
    )
    assert result["target_seen_in_null"]
    assert len(result["candidate_forms"]) == EXPECTED_CANDIDATE_FORMS
    if run_oracle:
        oracle = oracle_audit()
        assert oracle["total_hits"] == 0, oracle["hits"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", action="store_true")
    args = parser.parse_args()
    self_test(run_oracle=False)
    result = audit(run_null=True)
    print(f"second prime: {result['second_prime']} (prime=True)")
    print(f"matrix: {result['matrix']}")
    print(f"matrix sum list: {result['sum_list']}")
    print(f"Architect words: {' / '.join(word.upper() for word in result['words'])}")
    print(
        f"initials/endings: {result['initials'].upper()} / "
        f"{result['endings'].upper()}"
    )
    print(
        f"yin-yang reversal: {result['endings'].upper()} <-> "
        f"{result['reversed_endings'].upper()}"
    )
    print(
        "framed outputs: "
        f"{result['frames'][0].upper()} / {result['frames'][1].upper()} / "
        f"{result['frames'][2].upper()}"
    )
    print(
        f"second-frame reversal: {result['frames'][1].upper()} <-> "
        f"{result['second_frame_reversed'].upper()}"
    )
    print(
        "framing null: "
        f"{len(result['frame_hits'])}/{EXPECTED_ABSTRACT_TRIPLES} pairs give "
        "FLOW and combined TRUE"
    )
    print("alternate frame roles:")
    for role, outputs in enumerate(zip(*result["frame_role_outputs"])):
        counts, _ = result["frame_role_sweeps"][role]
        print(
            f"  role {role}: {' / '.join(value.upper() for value in outputs)}; "
            f"FLOW={counts['flow']} TRUE={counts['true']} "
            f"joint={counts['joint']}"
        )
    print(
        "abstract sum-list null: "
        f"{len(result['abstract_hits'])}/{EXPECTED_ABSTRACT_TRIPLES} exact WTF rails"
    )
    counts = result["null_counts"]
    print(
        "six-digit-prime null: "
        f"{counts['wtf_primes']}/{counts['six_digit_primes']} "
        f"= {counts['wtf_primes'] / counts['six_digit_primes']:.9f}"
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
