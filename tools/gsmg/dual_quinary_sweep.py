#!/usr/bin/env python3
"""Dual-quinary structural sweep for the GSMG Cosmic Duality endgame.

The earlier dual-ternary work (dual_ternary_sweep.py) factors each raw a-i
*symbol* into a 3x3 coordinate. This is a different representation: it factors
each complete *checkerboard code* (a segmented unit -- one single-symbol code,
or one escape-symbol-plus-digit pair) into a 5x5 coordinate, since a fixed
escape pair always yields exactly 25 possible code types (7 single-symbol +
9 first-escape + 9 second-escape codes). The natural index 0..24 a code
occupies is intrinsic to the checkerboard's structure -- it's the same offset
scheme cb_common.build_board_9ary() uses -- and is independent of any guessed
plaintext alphabet.

Verified (2026-07-24): dbbi segments into 63 codes under {b,e} (19 of 25 types
used); faed segments into 436 codes under {g,i} (all 25 types used) and 469
codes under {b,e}/{h,e} (also all 25 types). Using every code type makes a
base-25/5x5 payload interpretation materially different from treating either
target as raw base-9 symbols.

Bounded scope, per doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md's "Dual-Quinary
Decomposition" section:
  - three motivated unordered escape hypotheses (dbbi {b,e}; faed {g,i} and
    {h,e}), both escape orders, two board topologies;
  - row/column/interleaved/sum/difference/equality streams over the 5x5
    coordinates;
  - whole-base-5, whole-base-25, fixed-five-bit, and byte-aligned-coordinate
    packings;
  - signature/printability/entropy ranking, AES-oracle verification;
  - a shuffle-based null-model gate (same code-multiset, random order) that
    must be cleared before any ranking or signature is treated as a lead --
    do not combine with a keyword corpus unless this gate fires first.

Usage:
    python3 tools/gsmg/dual_quinary_sweep.py --self-test
    python3 tools/gsmg/dual_quinary_sweep.py --target both --top 20
    python3 tools/gsmg/dual_quinary_sweep.py --no-aes --json-out /tmp/dq.json
    python3 tools/gsmg/dual_quinary_sweep.py --shuffle-gate --trials 20000 --workers 16
"""
import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import aes_try_open, answer_forms, keystr_forms  # noqa: E402
from data import DBBI, FAED  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}
NINE_SYMS = "abcdefghi"

# Three motivated unordered escape hypotheses -- both orders tested for each.
TARGET_ESCAPE_PAIRS = {
    "dbbi": [("b", "e")],
    "faed": [("g", "i"), ("h", "e")],
}
TOPOLOGIES = ("top_first", "escapes_first")

MAGIC_SIGNATURES = {
    b"Salted__": "openssl-salted",
    b"\x1f\x8b": "gzip",
    b"BZh": "bzip2",
    b"\xfd7zXZ\x00": "xz",
    b"PK\x03\x04": "zip",
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"%PDF-": "pdf",
    b"\x7fELF": "elf",
    b"SQLite format 3\x00": "sqlite",
    b"-----BEGIN ": "pem-or-armored",
}


def escape_orders(pairs):
    return [order for e1, e2 in pairs for order in ((e1, e2), (e2, e1))]


def natural_code_index(e1, e2, topology):
    """code string ("c" or "e1c2") -> its intrinsic 0..24 board position, using
    the exact offset scheme cb_common.build_board_9ary() uses -- independent of
    any guessed alphabet."""
    tops = [c for c in NINE_SYMS if c not in (e1, e2)]
    if topology == "top_first":
        top_off, e1_off, e2_off = 0, 7, 16
    else:
        e1_off, e2_off, top_off = 0, 9, 18
    index = {}
    for k, c in enumerate(tops):
        index[c] = top_off + k
    for k, c2 in enumerate(NINE_SYMS):
        index[e1 + c2] = e1_off + k
    for k, c2 in enumerate(NINE_SYMS):
        index[e2 + c2] = e2_off + k
    return index


def segment_codes(s, e1, e2):
    """Split raw ciphertext into codes, or return None for a dangling escape."""
    codes = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in (e1, e2):
            if i + 1 >= len(s):
                return None
            codes.append(s[i:i + 2])
            i += 2
        else:
            codes.append(ch)
            i += 1
    return codes


def code_indices(codes, index_map):
    return [index_map[c] for c in codes]


@dataclass(frozen=True)
class Candidate:
    target: str
    escapes: str
    topology: str
    operation: str
    decoder: str
    offset: int
    length: int
    printable_ratio: float
    entropy: float
    longest_printable_run: int
    signature: str
    score: float
    hex_preview: str
    text_preview: str


def split_54(indices):
    """0..24 -> (row, col) over a 5x5 square."""
    rows = [i // 5 for i in indices]
    cols = [i % 5 for i in indices]
    return rows, cols


def combine_streams(rows, cols):
    return {
        "row": rows,
        "col": cols,
        "interleave_row_col": [v for pair in zip(rows, cols) for v in pair],
        "interleave_col_row": [v for pair in zip(cols, rows) for v in pair],
        "sum_mod5": [(r + c) % 5 for r, c in zip(rows, cols)],
        "row_minus_col_mod5": [(r - c) % 5 for r, c in zip(rows, cols)],
        "col_minus_row_mod5": [(c - r) % 5 for r, c in zip(rows, cols)],
        "equal": [int(r == c) for r, c in zip(rows, cols)],
    }


def pack_base125(values, offset):
    """Pack three base-5 digits per byte; 5**3=125 fits in one byte."""
    usable = values[offset:]
    return bytes(
        usable[index] * 25 + usable[index + 1] * 5 + usable[index + 2]
        for index in range(0, len(usable) - 2, 3)
    )


def pack_whole_radix(values, radix):
    """Interpret the complete digit stream as one big-endian radix-N integer."""
    value = 0
    for digit in values:
        value = value * radix + digit
    byte_length = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(byte_length, "big")


def pack_index_bytes(indices):
    """Store each base-25 digit directly in one byte."""
    return bytes(indices)


def pack_fixed_five_bit(values, offset):
    """Pack a stream of 0..24 (needs 5 bits) values as a contiguous 5-bit
    bitstream, byte-aligned only at the very start -- a fixed-width analogue
    of dual_ternary_sweep.py's pack_bits(), generalized from 1 bit to 5."""
    usable = values[offset:]
    bits = []
    for v in usable:
        bits.extend((v >> (4 - k)) & 1 for k in range(5))
    return bytes(
        sum(bit << (7 - k) for k, bit in enumerate(bits[i:i + 8]))
        for i in range(0, len(bits) - 7, 8)
    )


def pack_byte_coordinates(values, offset):
    """Pair up consecutive 0..4-range stream values into one byte each
    (v0*5+v1) -- the "byte-aligned coordinate stream" reading. Only meaningful
    for streams whose values are already 0..4 (row/col/sum_mod5/etc, not the
    raw 0..24 code-index stream itself)."""
    usable = values[offset:]
    return bytes(
        usable[i] * 5 + usable[i + 1]
        for i in range(0, len(usable) - 1, 2)
        if usable[i] < 5 and usable[i + 1] < 5
    )


def decode_stream(stream_values):
    """Packings that apply to any single derived 0..4-ish stream (row, col,
    sum_mod5, interleaved forms, etc)."""
    decoded = []
    for offset in range(3):
        body = pack_base125(stream_values, offset)
        if body:
            decoded.append(("base125", offset, body))
    decoded.append(("whole_base5", 0, pack_whole_radix(stream_values, 5)))
    for offset in range(2):
        body = pack_byte_coordinates(stream_values, offset)
        if body:
            decoded.append(("byte_coord", offset, body))
    for offset in range(5):
        body = pack_fixed_five_bit(stream_values, offset)
        if body:
            decoded.append(("bits5", offset, body))
    return decoded


def decode_raw_index_stream(indices):
    """Packings that apply to the original 0..24 code-index stream."""
    return [
        ("index_bytes", 0, pack_index_bytes(indices)),
        ("whole_base25", 0, pack_whole_radix(indices, 25)),
    ]


def shannon_entropy(body):
    if not body:
        return 0.0
    counts = Counter(body)
    return -sum(
        (count / len(body)) * math.log2(count / len(body))
        for count in counts.values()
    )


def printable_ratio(body):
    if not body:
        return 0.0
    return sum(byte in (9, 10, 13) or 32 <= byte < 127 for byte in body) / len(body)


def longest_printable_run(body):
    runs = re.findall(rb"[ -~]{2,}", body)
    return max((len(run) for run in runs), default=0)


def signature_name(body):
    for signature, name in MAGIC_SIGNATURES.items():
        if body.startswith(signature):
            return name
    return ""


def text_preview(body, limit=96):
    return "".join(chr(byte) if 32 <= byte < 127 else "." for byte in body[:limit])


def score_output(body):
    ratio = printable_ratio(body)
    run = longest_printable_run(body)
    signature = signature_name(body)
    score = ratio * 100 + min(run, 40) * 1.5
    if signature:
        score += 1000
    return score, ratio, run, signature


def make_candidate(metadata, decoder, offset, body):
    score, ratio, run, signature = score_output(body)
    return Candidate(
        **metadata,
        decoder=decoder,
        offset=offset,
        length=len(body),
        printable_ratio=round(ratio, 6),
        entropy=round(shannon_entropy(body), 6),
        longest_printable_run=run,
        signature=signature,
        score=round(score, 6),
        hex_preview=body[:48].hex(),
        text_preview=text_preview(body),
    )


def try_aes(body, metadata, tested_keystrings):
    if printable_ratio(body) < 0.85:
        return []
    try:
        text = body.decode("ascii")
    except UnicodeDecodeError:
        return []
    hits = []
    for form in answer_forms(text):
        if not form:
            continue
        for keystring in keystr_forms(form):
            if keystring in tested_keystrings:
                continue
            tested_keystrings.add(keystring)
            result = aes_try_open(keystring)
            if result:
                tag, plaintext, digest_name, key_len = result
                hits.append({
                    **metadata,
                    "answer": text,
                    "form": form,
                    "keystring": keystring,
                    "blob": tag,
                    "kdf": f"{digest_name}/aes{key_len * 8}",
                    "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                })
    return hits


OPERATIONS = (
    "row", "col", "interleave_row_col", "interleave_col_row",
    "sum_mod5", "row_minus_col_mod5", "col_minus_row_mod5", "equal",
)


def sweep_target(target_name, ciphertext, use_aes=True):
    results_by_body = {}
    hits = []
    tested_keystrings = set()

    for e1, e2 in escape_orders(TARGET_ESCAPE_PAIRS[target_name]):
        codes = segment_codes(ciphertext, e1, e2)
        if codes is None:
            continue
        for topology in TOPOLOGIES:
            index_map = natural_code_index(e1, e2, topology)
            indices = code_indices(codes, index_map)
            rows, cols = split_54(indices)
            streams = combine_streams(rows, cols)

            base_metadata = {"target": target_name, "escapes": f"{e1}{e2}", "topology": topology}
            for decoder, offset, body in decode_raw_index_stream(indices):
                metadata = {**base_metadata, "operation": "raw_index"}
                candidate = make_candidate(metadata, decoder, offset, body)
                previous = results_by_body.get(body)
                if previous is None or candidate.score > previous.score:
                    results_by_body[body] = candidate
                if use_aes:
                    hits.extend(try_aes(body, {**metadata, "decoder": decoder, "offset": offset}, tested_keystrings))

            for operation in OPERATIONS:
                metadata = {**base_metadata, "operation": operation}
                for decoder, offset, body in decode_stream(streams[operation]):
                    candidate = make_candidate(metadata, decoder, offset, body)
                    previous = results_by_body.get(body)
                    if previous is None or candidate.score > previous.score:
                        results_by_body[body] = candidate
                    if use_aes:
                        hits.extend(try_aes(
                            body,
                            {**metadata, "decoder": decoder, "offset": offset},
                            tested_keystrings,
                        ))

    ranked = sorted(
        results_by_body.values(),
        key=lambda c: (c.score, c.printable_ratio, c.longest_printable_run),
        reverse=True,
    )
    stats = {
        "unique_outputs": len(ranked),
        "aes_keystrings": len(tested_keystrings),
        "aes_hits": len(hits),
    }
    return ranked, hits, stats


def print_candidate(candidate, rank):
    flags = []
    if candidate.signature:
        flags.append(f"signature={candidate.signature}")
    flags.append(f"print={candidate.printable_ratio:.3f}")
    flags.append(f"entropy={candidate.entropy:.3f}")
    flags.append(f"run={candidate.longest_printable_run}")
    print(
        f"[{rank:3d}] score={candidate.score:7.2f} {candidate.target} "
        f"{{{candidate.escapes}}}/{candidate.topology} "
        f"{candidate.operation}/{candidate.decoder}@{candidate.offset} "
        f"len={candidate.length} {' '.join(flags)}"
    )
    print(f"      text: {candidate.text_preview}")
    print(f"      hex:  {candidate.hex_preview}")


def top_signal_stat_for_codes(codes, e1, e2):
    """Best structural score for one fixed complete-code ordering."""
    best = -1e18
    for topology in TOPOLOGIES:
        index_map = natural_code_index(e1, e2, topology)
        indices = code_indices(codes, index_map)
        rows, cols = split_54(indices)
        streams = combine_streams(rows, cols)
        for _, _, body in decode_raw_index_stream(indices):
            best = max(best, score_output(body)[0])
        for operation in OPERATIONS:
            for _, _, body in decode_stream(streams[operation]):
                best = max(best, score_output(body)[0])
    return best


def top_signal_stat(ciphertext, target_name):
    """Single scalar summary used by the shuffle gate: the best (highest) score
    seen across every escapes/topology/operation/decoder/offset combination for
    this ciphertext. Comparing the REAL ciphertext's value of this exact
    statistic against its own null distribution (from shuffles of the same
    complete-code multisets) is a max-statistic permutation test -- it already
    accounts for the multiple-comparisons burden of the whole structural
    search, unlike a per-cell Bonferroni correction."""
    best = -1e18
    for e1, e2 in escape_orders(TARGET_ESCAPE_PAIRS[target_name]):
        codes = segment_codes(ciphertext, e1, e2)
        if codes is not None:
            best = max(best, top_signal_stat_for_codes(codes, e1, e2))
    return best


def _trial_best(args):
    pair_codes, trial_seed = args
    rng = random.Random(trial_seed)
    best = -1e18
    for e1, e2, codes in pair_codes:
        shuffled_codes = list(codes)
        rng.shuffle(shuffled_codes)
        best = max(
            best,
            top_signal_stat_for_codes(shuffled_codes, e1, e2),
            top_signal_stat_for_codes(shuffled_codes, e2, e1),
        )
    return best


def shuffle_gate(target_name, ciphertext, trials, seed=0, workers=1):
    """Shuffle each motivated segmentation's complete-code multiset `trials`
    times and count how often a random ordering matches or beats the real
    ciphertext's best structural score.
    This is the null model the doc's plan requires before trusting any
    apparent word or signature from the main sweep. The empirical p-value here
    is a genuine family-wise / max-statistic permutation test: each shuffle's
    own maximum score across every escapes/topology/operation/decoder/offset
    combination is what's compared against the real ciphertext's maximum, so
    the multiple-comparisons burden of the whole structural search is already
    accounted for -- no separate Bonferroni correction is needed on top."""
    import time as _time

    start = _time.time()
    real_best = top_signal_stat(ciphertext, target_name)
    real_elapsed = _time.time() - start
    _, _, real_stats = sweep_target(target_name, ciphertext, use_aes=False)
    unique_outputs = real_stats["unique_outputs"]

    pair_codes = []
    for e1, e2 in TARGET_ESCAPE_PAIRS[target_name]:
        codes = segment_codes(ciphertext, e1, e2)
        if codes is not None:
            pair_codes.append((e1, e2, tuple(codes)))

    rng = random.Random(seed)
    trial_args = [
        (pair_codes, rng.getrandbits(64))
        for _ in range(trials)
    ]
    trial_start = _time.time()
    if workers == 1:
        null_bests = [_trial_best(args) for args in trial_args]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            null_bests = list(
                executor.map(
                    _trial_best,
                    trial_args,
                    chunksize=max(1, trials // (workers * 8)),
                )
            )
    trial_elapsed = _time.time() - trial_start
    at_least_as_good = sum(score >= real_best for score in null_bests)
    p_value = (at_least_as_good + 1) / (trials + 1)  # add-one smoothing
    return {
        "target": target_name,
        "seed": seed,
        "trials": trials,
        "workers": workers,
        "null_unit": "segmented_checkerboard_codes",
        "unique_outputs_after_dedup": unique_outputs,
        "real_best_score": round(real_best, 4),
        "null_mean": round(sum(null_bests) / len(null_bests), 4),
        "null_max": round(max(null_bests), 4),
        "at_least_as_good_count": at_least_as_good,
        "empirical_p_family_wise": round(p_value, 5),
        "seconds_per_trial": round(trial_elapsed / trials, 4),
        "real_stat_compute_seconds": round(real_elapsed, 4),
        "total_shuffle_seconds": round(trial_elapsed, 2),
    }


def run_self_tests():
    order = escape_orders([("b", "e")])
    assert order == [("b", "e"), ("e", "b")]

    idx_top_first = natural_code_index("b", "e", "top_first")
    assert idx_top_first["a"] == 0  # first non-escape symbol, top row
    assert idx_top_first["ba"] == 7  # e1='b'-led row starts at offset 7
    assert idx_top_first["ea"] == 16  # e2='e'-led row starts at offset 16
    assert sorted(idx_top_first.values()) == list(range(25))

    idx_escapes_first = natural_code_index("b", "e", "escapes_first")
    assert idx_escapes_first["ba"] == 0
    assert idx_escapes_first["ea"] == 9
    assert idx_escapes_first["a"] == 18

    assert segment_codes("abbe", "b", "e") is None
    codes2 = segment_codes("aeb", "b", "e")
    assert codes2 == ["a", "eb"]

    assert segment_codes(DBBI, "b", "e").__len__() == 63
    assert len(set(segment_codes(DBBI, "b", "e"))) == 19
    assert len(segment_codes(FAED, "g", "i")) == 436
    assert len(set(segment_codes(FAED, "g", "i"))) == 25
    assert len(segment_codes(FAED, "b", "e")) == 469
    assert len(set(segment_codes(FAED, "b", "e"))) == 25

    rows, cols = split_54([0, 5, 24, 12])
    assert rows == [0, 1, 4, 2]
    assert cols == [0, 0, 4, 2]

    streams = combine_streams([1, 2], [3, 4])
    assert streams["sum_mod5"] == [4, 1]
    assert streams["row_minus_col_mod5"] == [(1 - 3) % 5, (2 - 4) % 5]
    assert streams["equal"] == [0, 0]

    assert pack_base125([0, 0, 0], 0) == b"\x00"
    assert pack_base125([4, 4, 4], 0) == bytes([4 * 25 + 4 * 5 + 4])
    assert pack_whole_radix([1, 0], 5) == b"\x05"
    assert pack_whole_radix([1, 0], 25) == b"\x19"
    assert pack_index_bytes([0, 24, 12]) == bytes([0, 24, 12])
    assert pack_byte_coordinates([1, 2, 3, 4], 0) == bytes([1 * 5 + 2, 3 * 5 + 4])
    packed_bits = pack_fixed_five_bit([31, 31], 0)
    assert len(packed_bits) == 1  # 10 bits -> 1 full byte, 2 leftover bits dropped

    assert signature_name(b"Salted__x") == "openssl-salted"

    print("[*] dual-quinary self-tests passed")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", choices=("dbbi", "faed", "both"), default="both")
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--no-aes", action="store_true")
    parser.add_argument("--json-out")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--shuffle-gate", action="store_true",
        help="run the shuffle-based null-model gate instead of the main sweep",
    )
    parser.add_argument("--trials", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="shuffle-gate workers (results are worker-count invariant)",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()

    selected = TARGETS if args.target == "both" else {args.target: TARGETS[args.target]}

    if args.shuffle_gate:
        for target_name, ciphertext in selected.items():
            result = shuffle_gate(
                target_name,
                ciphertext,
                args.trials,
                args.seed,
                args.workers,
            )
            print(f"[*] {target_name}: seed={result['seed']} trials={result['trials']:,}")
            print(
                f"    null_unit={result['null_unit']} workers={result['workers']}"
            )
            print(f"    unique_outputs_after_dedup={result['unique_outputs_after_dedup']:,}")
            print(f"    real_best_score={result['real_best_score']}")
            print(
                f"    null_mean={result['null_mean']} null_max={result['null_max']} "
                f"at_least_as_good={result['at_least_as_good_count']}/{result['trials']}"
            )
            print(f"    empirical_p_family_wise={result['empirical_p_family_wise']}")
            print(
                f"    seconds_per_trial={result['seconds_per_trial']} "
                f"(real_stat={result['real_stat_compute_seconds']}s, "
                f"total_shuffle={result['total_shuffle_seconds']}s)"
            )
        return

    report = {}
    total_hits = 0
    for target_name, ciphertext in selected.items():
        print(f"\n[*] sweeping {target_name}: {len(ciphertext)} symbols")
        ranked, hits, stats = sweep_target(target_name, ciphertext, use_aes=not args.no_aes)
        print(
            f"[*] {stats['unique_outputs']:,} unique decoded outputs, "
            f"{stats['aes_keystrings']:,} AES keystrings, {stats['aes_hits']} hits"
        )
        for rank, candidate in enumerate(ranked[:args.top], 1):
            print_candidate(candidate, rank)
        for hit in hits:
            print(f"\n[+++ AES HIT] {hit}\n")
        total_hits += len(hits)
        report[target_name] = {
            "stats": stats,
            "hits": hits,
            "candidates": [asdict(c) for c in ranked],
        }

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\n[*] wrote JSON report to {output_path}")

    if total_hits == 0:
        print("\n[*] no candidate opened either AES blob")


if __name__ == "__main__":
    main()
