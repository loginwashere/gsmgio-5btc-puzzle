#!/usr/bin/env python3
"""Audit Telegram message 8088's Matrix-text / extra-character / prime route.

The recovered community message says to compare the modified Phase-3.2.1
Architect text with the real Matrix text, remove extra characters, and think
about primes. This script gives that under-specified suggestion its strongest
bounded implementation without choosing an output for readability:

1. Freeze the local screenplay PDF and the exact solved custom plaintext.
2. Compare a fixed spoken-dialogue transcription with the custom plaintext by
   a deterministic word-level longest-common-subsequence alignment.
3. Flatten the aligned custom-only and shared words to character streams.
4. Retain prime-indexed characters under both zero- and one-based indexing.
5. Search a closed clue-marker family and calibrate the maximum marker length
   across the complete four-output family under character-multiset shuffles.

The mostly-retained non-prime complements are printed for auditability but are
not scored: they necessarily inherit long words from the source and would make
the marker statistic invalid.
"""

import argparse
import hashlib
import random
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase4_date_door_reaudit import (  # noqa: E402
    COMMUNITY_COMPARE_ID,
    audit_provenance,
)
from telegram_matrix_sum_passage_audit import (  # noqa: E402
    DEFAULT_WALKTHROUGH,
    extract_phase_plaintext,
)

PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "matrix"
    / "the-matrix-reloaded-2003.pdf"
)
PDF_SHA256 = "2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4"
DEFAULT_TRIALS = 5_000
DEFAULT_SEED = 20260728

# Spoken lines corresponding to the custom text in message 8088's image.
# Stage directions and unrelated intercut scenes are excluded. Every nontrivial
# segment is asserted against the pinned PDF after explicit OCR normalization.
CANONICAL_SEGMENTS = (
    """
    Your life is the sum of a remainder of an unbalanced equation inherent to
    the programming of the Matrix.
    """,
    """
    You are the eventuality of an anomaly that, despite my sincerest efforts, I
    have been unable to eliminate from what is otherwise a harmony of
    mathematical precision. While it remains a burden assiduously avoided, it
    is not unexpected and thus not beyond a measure of control which has led
    you inexorably.
    """,
    "Here.",
    "You haven't answered my question.",
    "Quite right. Interesting. That was quicker than the others.",
    "Bullshit.",
    """
    Denial is the most predictable of all human responses but rest assured this
    will be the sixth time we have destroyed it and we have become exceedingly
    efficient at it.
    """,
    """
    The function of the One is to now return to the Source, allowing a temporary
    dissemination of the code you carry, reinserting the prime program after
    which you will be required to select from the Matrix twenty three
    individuals, sixteen female, seven male, to rebuild Zion.
    """,
    """
    Failure to comply with this process will result in a cataclysmic system
    crash, killing everyone connected to the Matrix, which coupled with the
    extermination of Zion will ultimately result in the extinction of the
    entire human race.
    """,
)
CANONICAL_DIALOGUE = "\n".join(CANONICAL_SEGMENTS)

MARKERS = (
    "door",
    "prime",
    "zero",
    "matrix",
    "sum",
    "list",
    "yin",
    "yang",
    "password",
    "key",
    "enter",
    "source",
    "code",
    "choice",
    "salvation",
)


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(text):
    return re.findall(r"[A-Z]+", text.upper().replace("TWENTY-THREE", "TWENTY THREE"))


def verify_canonical_segments(pdf_path=PDF_PATH):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    pdf_words = words(completed.stdout)
    pdf_words = [
        "EVENTUALITY" if word == "EVENTUALITV" else word
        for word in pdf_words
    ]
    normalized_pdf = " ".join(pdf_words)
    missing = []
    for segment in CANONICAL_SEGMENTS:
        normalized_segment = " ".join(words(segment))
        if len(words(segment)) > 1 and normalized_segment not in normalized_pdf:
            missing.append(normalized_segment)
    if missing:
        raise AssertionError(
            f"canonical dialogue segments not found in pinned PDF: {missing}"
        )
    return tuple(
        " ".join(words(segment))
        for segment in CANONICAL_SEGMENTS
    )


def lcs_alignment(canonical_words, custom_words):
    """Return deterministic LCS pairs.

    On equal-length alternatives, skip the custom word. This conservative
    tie-break prevents repeated source words from being opportunistically
    absorbed into the shared stream merely because they occur later.
    """
    canonical_count = len(canonical_words)
    custom_count = len(custom_words)
    lengths = [
        [0] * (custom_count + 1)
        for _ in range(canonical_count + 1)
    ]
    for canonical_index in range(canonical_count - 1, -1, -1):
        for custom_index in range(custom_count - 1, -1, -1):
            if canonical_words[canonical_index] == custom_words[custom_index]:
                lengths[canonical_index][custom_index] = (
                    1 + lengths[canonical_index + 1][custom_index + 1]
                )
            else:
                lengths[canonical_index][custom_index] = max(
                    lengths[canonical_index + 1][custom_index],
                    lengths[canonical_index][custom_index + 1],
                )

    pairs = []
    canonical_index = 0
    custom_index = 0
    while canonical_index < canonical_count and custom_index < custom_count:
        if (
            canonical_words[canonical_index] == custom_words[custom_index]
            and lengths[canonical_index][custom_index]
            == 1 + lengths[canonical_index + 1][custom_index + 1]
        ):
            pairs.append(
                (
                    canonical_index,
                    custom_index,
                    canonical_words[canonical_index],
                )
            )
            canonical_index += 1
            custom_index += 1
        elif (
            lengths[canonical_index][custom_index + 1]
            >= lengths[canonical_index + 1][custom_index]
        ):
            custom_index += 1
        else:
            canonical_index += 1
    return pairs


def is_prime(value):
    if value < 2:
        return False
    return all(
        value % divisor
        for divisor in range(2, int(value ** 0.5) + 1)
    )


def prime_mask(length, index_base):
    return tuple(
        index
        for index in range(length)
        if is_prime(index + index_base)
    )


def select_indices(stream, indices):
    return "".join(stream[index] for index in indices)


def marker_hits(stream):
    return tuple(marker for marker in MARKERS if marker in stream)


def max_marker_length(outputs):
    return max(
        (
            len(marker)
            for output in outputs
            for marker in marker_hits(output)
        ),
        default=0,
    )


def build_alignment(walkthrough_path=DEFAULT_WALKTHROUGH):
    canonical = words(CANONICAL_DIALOGUE)
    custom = words(extract_phase_plaintext(walkthrough_path))
    pairs = lcs_alignment(canonical, custom)
    shared_canonical = {canonical_index for canonical_index, _, _ in pairs}
    shared_custom = {custom_index for _, custom_index, _ in pairs}
    shared = [word for _, _, word in pairs]
    extra = [
        word
        for custom_index, word in enumerate(custom)
        if custom_index not in shared_custom
    ]
    missing = [
        word
        for canonical_index, word in enumerate(canonical)
        if canonical_index not in shared_canonical
    ]
    return {
        "canonical": canonical,
        "custom": custom,
        "shared": shared,
        "extra": extra,
        "missing": missing,
        "pairs": pairs,
    }


def transform_family(alignment):
    streams = {
        "extra": "".join(alignment["extra"]).lower(),
        "shared": "".join(alignment["shared"]).lower(),
    }
    outputs = {}
    for label, stream in streams.items():
        for index_base in (0, 1):
            indices = prime_mask(len(stream), index_base)
            outputs[f"{label}_base{index_base}_prime"] = select_indices(
                stream,
                indices,
            )
            prime_set = set(indices)
            outputs[f"{label}_base{index_base}_nonprime"] = "".join(
                character
                for index, character in enumerate(stream)
                if index not in prime_set
            )
    return streams, outputs


def shuffle_gate(streams, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    masks = {
        label: {
            index_base: prime_mask(len(stream), index_base)
            for index_base in (0, 1)
        }
        for label, stream in streams.items()
    }

    real_outputs = [
        select_indices(stream, masks[label][index_base])
        for label, stream in streams.items()
        for index_base in (0, 1)
    ]
    real_max = max_marker_length(real_outputs)

    rng = random.Random(seed)
    working = {label: list(stream) for label, stream in streams.items()}
    exceedances = 0
    null_counts = {}
    for _ in range(trials):
        trial_outputs = []
        for label, characters in working.items():
            rng.shuffle(characters)
            for index_base in (0, 1):
                trial_outputs.append(
                    select_indices(characters, masks[label][index_base])
                )
        null_max = max_marker_length(trial_outputs)
        null_counts[null_max] = null_counts.get(null_max, 0) + 1
        if null_max >= real_max:
            exceedances += 1

    return {
        "real_max_marker_length": real_max,
        "trials": trials,
        "seed": seed,
        "exceedances": exceedances,
        "empirical_p": (exceedances + 1) / (trials + 1),
        "null_counts": dict(sorted(null_counts.items())),
    }


def audit(
    walkthrough_path=DEFAULT_WALKTHROUGH,
    trials=DEFAULT_TRIALS,
    seed=DEFAULT_SEED,
):
    provenance = audit_provenance()
    if sha256_file(PDF_PATH) != PDF_SHA256:
        raise AssertionError("Matrix Reloaded screenplay PDF bytes changed")
    verify_canonical_segments()
    if provenance["compare_reply_to"] is None:
        raise AssertionError("message 8088 lost its door-question reply edge")

    alignment = build_alignment(walkthrough_path)
    streams, outputs = transform_family(alignment)
    gate = shuffle_gate(streams, trials, seed)
    prime_hits = {
        label: marker_hits(output)
        for label, output in outputs.items()
        if label.endswith("_prime")
    }
    return {
        "message_id": COMMUNITY_COMPARE_ID,
        "alignment": alignment,
        "streams": streams,
        "outputs": outputs,
        "prime_hits": prime_hits,
        "gate": gate,
    }


def self_test():
    canonical = ["A", "B", "A", "C"]
    custom = ["A", "X", "B", "A", "C"]
    pairs = lcs_alignment(canonical, custom)
    assert [word for _, _, word in pairs] == canonical
    assert prime_mask(10, 0) == (2, 3, 5, 7)
    assert prime_mask(10, 1) == (1, 2, 4, 6)

    alignment = build_alignment()
    assert len(verify_canonical_segments()) == len(CANONICAL_SEGMENTS)
    assert len(alignment["canonical"]) == 200
    assert len(alignment["custom"]) == 336
    assert len(alignment["shared"]) == 172
    assert len(alignment["extra"]) == 164
    assert len(alignment["missing"]) == 28

    streams, outputs = transform_family(alignment)
    assert len(streams["extra"]) == 709
    assert len(streams["shared"]) == 830
    assert marker_hits(outputs["extra_base0_prime"]) == ("list",)
    assert not marker_hits(outputs["extra_base1_prime"])
    assert not marker_hits(outputs["shared_base0_prime"])
    assert not marker_hits(outputs["shared_base1_prime"])
    print(
        "[*] self-test OK: fixed source counts, deterministic LCS, prime "
        "masks, and real marker inventory verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--walkthrough", type=Path, default=DEFAULT_WALKTHROUGH)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.walkthrough, args.trials, args.seed)
    alignment = report["alignment"]
    print(
        f"[*] words: canonical={len(alignment['canonical'])} "
        f"custom={len(alignment['custom'])} shared={len(alignment['shared'])} "
        f"extra={len(alignment['extra'])} missing={len(alignment['missing'])}"
    )
    print("[*] custom-only words:")
    print("    " + " ".join(alignment["extra"]))
    print("[*] canonical-only words:")
    print("    " + " ".join(alignment["missing"]))
    for label, output in report["outputs"].items():
        hits = marker_hits(output)
        print(f"[*] {label}: len={len(output)} markers={hits}")
        print(f"    {output}")
    gate = report["gate"]
    print(
        f"[*] shuffle gate: real_max_marker_length="
        f"{gate['real_max_marker_length']} trials={gate['trials']} "
        f"seed={gate['seed']} exceedances={gate['exceedances']} "
        f"empirical_p={gate['empirical_p']:.8f} "
        f"null_counts={gate['null_counts']}"
    )
    print(
        "[*] verdict: the fixed comparison isolates the custom puzzle prose, "
        "but no prime-indexed stream is readable; the lone 'list' marker "
        "does not clear the family-wise shuffle gate"
    )


if __name__ == "__main__":
    main()
