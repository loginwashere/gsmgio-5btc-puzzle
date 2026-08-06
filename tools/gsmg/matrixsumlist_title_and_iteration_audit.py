#!/usr/bin/env python3
"""Follow-up audit on item 2 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md`
section 2), prompted by a direct chat question ("did we check all 4
points?") that caught two real gaps Phase 153 either shortcut or missed
entirely:

1. Item 2's first bullet named three places to index `[23,16,7]`: the DBBI
   selection, the macro-clue token list, and "the ordered phase title list
   (8 items)". Phase 150 covered the first; Phase 153 covered the second
   but then asserted -- without checking -- that the third "is the same
   object" as the second. It isn't: the puzzle has its own genuine, sourced
   sequence of stage/phase names (`doc/GSMG_PUZZLE.md`'s solve chain),
   distinct from the macro clue's 8 decoded fragments. This module tests
   the real list.

2. Item 2's third bullet proposed `[23,16,7]` as "iteration/round counts"
   with three named readings: 23 rounds of a keystream, 16-byte AES block
   alignment, and a Caesar/ROT shift on the `BUT`/`HYE` rails. Phase 153
   only ever tested the third (single, non-iterated shifts of +-23/16/7).
   The other two were never touched. This module closes both: (a) confirms
   16-byte block alignment is not a new lever at all -- every candidate
   this entire project has ever tested already sweeps AES-128 (16-byte
   key) alongside AES-256/192, per `cb_common.py`'s `key_len` variants --
   and (b) tests the one bounded, creator-motivated reading of "N rounds of
   a simple keystream": repeated single-letter Caesar shifts are additive,
   so "23 rounds of a shift-7 keystream" is mathematically identical to one
   shift of `7*23 mod 26` -- tested for every round-count x shift-amount
   pair drawn only from `{23,16,7}` (the numbers actually in evidence),
   never an invented parameter.
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
DOC_PATH = SCRIPT_DIR.parent.parent / "doc" / "GSMG_PUZZLE.md"

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from denis_prime_extraction_audit import TARGET  # noqa: E402
from prime_matrixsum_reconstruction import (  # noqa: E402
    DEFAULT_IMAGE,
    EXPECTED_PRIME,
    bounded_indexings,
    edge_letters,
    load_architect_words,
    matrixsumlist,
)
from first_piece_color_reconstruction import reconstruct  # noqa: E402

# This checkout doesn't have the repo's own wordlists/matrix/ populated;
# reuse the same key-seeker path other Matrix-screenplay scripts fall back
# to this session (see trinity_resurrection_half_audit.py).
ARCHITECT_PDF_PATH = Path(
    "/home/loginwashere/projects/key-seeker/wordlists/matrix/the-matrix-reloaded-2003.pdf"
)

INDICES = (23, 16, 7)

# The puzzle's own real, sourced stage/phase progression -- distinct from
# the macro clue's 8 decoded fragments (already tested in Phase 153).
# Each label is asserted against doc/GSMG_PUZZLE.md at run time, not
# hardcoded from memory alone.
PHASE_TITLES = (
    "Stage 0",
    "Stage 1",
    "Phase 2",
    "Phase 3",
    "Phase 3.2",
    "Phase 3.2.1",
    "Phase 3.2.2",
    "SalPhaseIon",
)
REQUIRED_DOC_SNIPPETS = (
    "Stage 0",
    "Stage 1",
    "Phase 2/3",
    "Phase 3.2.1 / 3.2.2",
    "SalPhaseIon",
)


def verify_phase_titles_sourced(doc_path=DOC_PATH):
    text = doc_path.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_DOC_SNIPPETS if s not in text]
    if missing:
        raise AssertionError(f"expected phase-title snippets not found in doc: {missing}")
    return True


def normalize(label):
    return re.sub(r"[^A-Za-z0-9]", "", label).upper()


def direct_index(items, indices):
    return tuple(items[i - 1] if 1 <= i <= len(items) else None for i in indices)


def wraparound_index(items, indices):
    n = len(items)
    return tuple(items[((i - 1) % n)] for i in indices)


def title_list_candidates():
    direct = direct_index(PHASE_TITLES, INDICES)
    wrapped = wraparound_index(PHASE_TITLES, INDICES)

    selections = []
    direct_valid = tuple(t for t in direct if t is not None)
    if direct_valid:
        selections.append(("direct", direct_valid))
    selections.append(("wraparound", wrapped))

    candidates = set()
    for _, items in selections:
        unique_items = tuple(dict.fromkeys(items))
        normalized = [normalize(t) for t in unique_items]
        candidates.add("".join(normalized))
        candidates.add("".join(reversed(normalized)))
        for t in unique_items:
            candidates.add(normalize(t))
    candidates.discard("")
    return {
        "direct": direct,
        "wraparound": wrapped,
        "candidates": tuple(sorted(candidates)),
    }


def but_hye_rails():
    color_result = reconstruct(DEFAULT_IMAGE)
    if color_result["prime_value"] != EXPECTED_PRIME:
        raise AssertionError("first-piece prime no longer matches expected value")
    _, sum_list = matrixsumlist(color_result["prime_value"])
    architect_words, _ = load_architect_words(ARCHITECT_PDF_PATH)
    selected = bounded_indexings(architect_words, sum_list)["forward_one"]
    first_edges, last_edges = edge_letters(selected)
    if (first_edges, last_edges) != ("but", "hye"):
        raise AssertionError(f"unexpected rails: {first_edges!r}/{last_edges!r}")
    return first_edges, last_edges


def caesar_shift(text, shift):
    return "".join(
        chr((ord(ch) - ord("a") + shift) % 26 + ord("a")) if ch.isalpha() else ch
        for ch in text.lower()
    )


def iteration_candidates():
    but, hye = but_hye_rails()
    targets = {"BUT": but, "HYE": hye, "TARGET31": TARGET}

    net_shifts = sorted({(rounds * amount) % 26 for rounds in INDICES for amount in INDICES})

    outputs = {}
    for name, text in targets.items():
        for shift in net_shifts:
            outputs[f"{name}_+{shift}"] = caesar_shift(text, shift).upper()
            outputs[f"{name}_-{shift}"] = caesar_shift(text, -shift).upper()
    return {
        "but": but,
        "hye": hye,
        "net_shifts": net_shifts,
        "outputs": outputs,
    }


def block_alignment_note():
    return (
        "16-byte AES block alignment is not a new lever: cb_common.py's "
        "CBC (key_len 32/24/16), stream (key_len 32/24/16), and Key-Wrap "
        "(KEY_WRAP_KEY_LENS = 16/24/32) variant sets already sweep the "
        "16-byte / AES-128 case for every single candidate this entire "
        "project has ever tested, including every candidate in this "
        "module. Confirmed by direct inspection of cb_common.py, not "
        "re-tested with new code."
    )


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((candidate, keystring, result))
                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))
                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))
                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((candidate, keystring, result))
    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def self_test():
    assert verify_phase_titles_sourced()
    title_result = title_list_candidates()
    assert title_result["wraparound"] == ("Phase 3.2.2", "SalPhaseIon", "Phase 3.2.2")
    but, hye = but_hye_rails()
    assert (but, hye) == ("but", "hye")
    it = iteration_candidates()
    assert it["net_shifts"] == sorted({(a * b) % 26 for a in INDICES for b in INDICES})
    print("[*] self-test OK: phase-title list sourced, wraparound indices reproduced, BUT/HYE rails re-derived live")
    return title_result, it


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    title_result = title_list_candidates()
    print(f"[*] phase-title list: {PHASE_TITLES}")
    print(f"[*] direct 1-based [23,16,7]: {title_result['direct']}")
    print(f"[*] mod-8 wraparound [23,16,7]: {title_result['wraparound']}")
    print(f"[*] candidates ({len(title_result['candidates'])}): {title_result['candidates']}")

    print()
    print(f"[*] {block_alignment_note()}")

    print()
    it = iteration_candidates()
    print(f"[*] BUT={it['but']!r} HYE={it['hye']!r} TARGET31={TARGET!r}")
    print(f"[*] net shifts from round-count x shift-amount over {{23,16,7}}: {it['net_shifts']}")
    print(f"[*] iteration candidates: {len(it['outputs'])}")

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)

        all_candidates = list(title_result["candidates"]) + list(it["outputs"].values())
        result = oracle_check(all_candidates, blobs)
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"\n[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
