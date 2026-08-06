#!/usr/bin/env python3
"""Dual-ternary structural sweep for the GSMG Cosmic Duality endgame.

The existing native-base-9 work treats each a-i symbol as one atomic digit. This
script tests a different representation: nine symbols are the Cartesian product
of two ternary coordinates, so every symbol carries a pair of trits:

    a=00 b=01 c=02
    d=10 e=11 f=12
    g=20 h=21 i=22

It enumerates only clue-motivated structural axes:

  - the eight symmetries of the 3x3 symbol square;
  - row/column/serpentine routes over dbbi's 7x13 and faed's 15x38 matrices;
  - independent reversal of the two component streams;
  - component, interleaved, mod-3 sum/difference, and equality streams;
  - five-trit base-243 packing, whole-base-3 conversion, and binary masks.

Outputs are ranked by file signatures, printability, and printable runs. Highly
printable candidates are also checked with the project's real AES oracle.

Usage:
    python3 tools/gsmg/dual_ternary_sweep.py
    python3 tools/gsmg/dual_ternary_sweep.py --target dbbi --top 50
    python3 tools/gsmg/dual_ternary_sweep.py --no-aes --json-out /tmp/dual.json
    python3 tools/gsmg/dual_ternary_sweep.py --self-test
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import aes_try_open, answer_forms, keystr_forms  # noqa: E402
from data import DBBI, FAED  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}
TARGET_SHAPES = {
    "dbbi": ((7, 13), (13, 7)),
    "faed": ((15, 38), (38, 15)),
}
SYMBOLS = "abcdefghi"

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


@dataclass(frozen=True)
class Candidate:
    target: str
    shape: str
    route: str
    symmetry: str
    reverse_first: bool
    reverse_second: bool
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


def square_symmetries():
    """Return the eight D4 symmetries of a 3x3 coordinate square."""
    return {
        "identity": lambda row, col: (row, col),
        "rot90": lambda row, col: (col, 2 - row),
        "rot180": lambda row, col: (2 - row, 2 - col),
        "rot270": lambda row, col: (2 - col, row),
        "mirror_vertical": lambda row, col: (row, 2 - col),
        "mirror_horizontal": lambda row, col: (2 - row, col),
        "mirror_diagonal": lambda row, col: (col, row),
        "mirror_antidiagonal": lambda row, col: (2 - col, 2 - row),
    }


def coordinate_map(symmetry):
    transform = square_symmetries()[symmetry]
    return {
        symbol: transform(index // 3, index % 3)
        for index, symbol in enumerate(SYMBOLS)
    }


def route_text(text, rows, cols, route):
    if rows * cols != len(text):
        raise ValueError(f"shape {rows}x{cols} does not fit length {len(text)}")
    matrix = [text[index:index + cols] for index in range(0, len(text), cols)]
    if route == "rows":
        return "".join(matrix)
    if route == "rows_reverse":
        return "".join(reversed(matrix))
    if route == "snake_rows":
        return "".join(
            row if index % 2 == 0 else row[::-1]
            for index, row in enumerate(matrix)
        )
    if route == "snake_rows_reverse":
        return "".join(
            row if index % 2 == 0 else row[::-1]
            for index, row in enumerate(reversed(matrix))
        )
    if route == "columns":
        return "".join(matrix[row][col] for col in range(cols) for row in range(rows))
    if route == "columns_reverse":
        return "".join(
            matrix[row][col]
            for col in range(cols - 1, -1, -1)
            for row in range(rows)
        )
    if route == "snake_columns":
        out = []
        for col in range(cols):
            row_order = range(rows) if col % 2 == 0 else range(rows - 1, -1, -1)
            out.extend(matrix[row][col] for row in row_order)
        return "".join(out)
    if route == "snake_columns_reverse":
        out = []
        for route_index, col in enumerate(range(cols - 1, -1, -1)):
            row_order = range(rows) if route_index % 2 == 0 else range(rows - 1, -1, -1)
            out.extend(matrix[row][col] for row in row_order)
        return "".join(out)
    raise ValueError(f"unknown route: {route}")


ROUTES = (
    "rows",
    "rows_reverse",
    "snake_rows",
    "snake_rows_reverse",
    "columns",
    "columns_reverse",
    "snake_columns",
    "snake_columns_reverse",
)


def split_trits(text, symmetry):
    mapping = coordinate_map(symmetry)
    first, second = zip(*(mapping[symbol] for symbol in text))
    return list(first), list(second)


def combine_streams(first, second):
    return {
        "first": first,
        "second": second,
        "interleave_first_second": [
            value for pair in zip(first, second) for value in pair
        ],
        "interleave_second_first": [
            value for pair in zip(second, first) for value in pair
        ],
        "sum_mod3": [(left + right) % 3 for left, right in zip(first, second)],
        "first_minus_second_mod3": [
            (left - right) % 3 for left, right in zip(first, second)
        ],
        "second_minus_first_mod3": [
            (right - left) % 3 for left, right in zip(first, second)
        ],
        "equal": [int(left == right) for left, right in zip(first, second)],
    }


def pack_base243(trits, offset):
    usable = trits[offset:]
    return bytes(
        sum(value * (3 ** (4 - inner)) for inner, value in enumerate(usable[index:index + 5]))
        for index in range(0, len(usable) - 4, 5)
    )


def pack_whole_base3(trits):
    value = 0
    for trit in trits:
        value = value * 3 + trit
    byte_length = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(byte_length, "big")


def pack_bits(bits, offset):
    usable = bits[offset:]
    return bytes(
        sum(bit << (7 - inner) for inner, bit in enumerate(usable[index:index + 8]))
        for index in range(0, len(usable) - 7, 8)
    )


def decode_stream(operation, trits):
    decoded = []
    for offset in range(5):
        body = pack_base243(trits, offset)
        if body:
            decoded.append((f"base243", offset, body))
    decoded.append(("whole_base3", 0, pack_whole_base3(trits)))

    masks = {
        "is_zero": [int(value == 0) for value in trits],
        "is_one": [int(value == 1) for value in trits],
        "is_two": [int(value == 2) for value in trits],
        "nonzero": [int(value != 0) for value in trits],
    }
    if operation == "equal":
        masks["direct_bits"] = trits
    for mask_name, bits in masks.items():
        for offset in range(8):
            body = pack_bits(bits, offset)
            if body:
                decoded.append((f"bits_{mask_name}", offset, body))
    return decoded


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
    return sum(
        byte in (9, 10, 13) or 32 <= byte < 127
        for byte in body
    ) / len(body)


def longest_printable_run(body):
    runs = re.findall(rb"[ -~]{2,}", body)
    return max((len(run) for run in runs), default=0)


def signature_name(body):
    for signature, name in MAGIC_SIGNATURES.items():
        if body.startswith(signature):
            return name
    return ""


def text_preview(body, limit=96):
    return "".join(
        chr(byte) if 32 <= byte < 127 else "."
        for byte in body[:limit]
    )


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


def try_aes(body, metadata, newline_variants, tested_keystrings):
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
        for keystring in keystr_forms(form, newline_variants):
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


def sweep_target(target_name, ciphertext, use_aes=True, newline_variants=False):
    results_by_body = {}
    hits = []
    tested_keystrings = set()
    routed_seen = set()

    for rows, cols in TARGET_SHAPES[target_name]:
        for route in ROUTES:
            routed = route_text(ciphertext, rows, cols, route)
            route_key = routed
            if route_key in routed_seen:
                continue
            routed_seen.add(route_key)

            for symmetry in square_symmetries():
                first, second = split_trits(routed, symmetry)
                for reverse_first in (False, True):
                    first_variant = first[::-1] if reverse_first else first
                    for reverse_second in (False, True):
                        second_variant = second[::-1] if reverse_second else second
                        operations = combine_streams(first_variant, second_variant)
                        for operation, trits in operations.items():
                            metadata = {
                                "target": target_name,
                                "shape": f"{rows}x{cols}",
                                "route": route,
                                "symmetry": symmetry,
                                "reverse_first": reverse_first,
                                "reverse_second": reverse_second,
                                "operation": operation,
                            }
                            for decoder, offset, body in decode_stream(operation, trits):
                                body_key = body
                                candidate = make_candidate(metadata, decoder, offset, body)
                                previous = results_by_body.get(body_key)
                                if previous is None or candidate.score > previous.score:
                                    results_by_body[body_key] = candidate
                                if use_aes:
                                    hits.extend(try_aes(
                                        body,
                                        {
                                            **metadata,
                                            "decoder": decoder,
                                            "offset": offset,
                                        },
                                        newline_variants,
                                        tested_keystrings,
                                    ))

    ranked = sorted(
        results_by_body.values(),
        key=lambda candidate: (
            candidate.score,
            candidate.printable_ratio,
            candidate.longest_printable_run,
        ),
        reverse=True,
    )
    stats = {
        "routes": len(routed_seen),
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
        f"{candidate.shape}/{candidate.route}/{candidate.symmetry} "
        f"rev={int(candidate.reverse_first)}{int(candidate.reverse_second)} "
        f"{candidate.operation}/{candidate.decoder}@{candidate.offset} "
        f"len={candidate.length} {' '.join(flags)}"
    )
    print(f"      text: {candidate.text_preview}")
    print(f"      hex:  {candidate.hex_preview}")


def coincidence_rate(stream):
    """Index of coincidence for a stream over any finite alphabet (order-independent —
    depends only on value frequencies, so it doubles as the null/expected match rate
    for the lag test below)."""
    n = len(stream)
    if n < 2:
        return 0.0
    counts = Counter(stream)
    return sum(count * (count - 1) for count in counts.values()) / (n * (n - 1))


def lag_match_rate(stream, lag):
    n = len(stream)
    total = n - lag
    if total <= 0:
        return None
    matches = sum(1 for i in range(total) if stream[i] == stream[i + lag])
    return matches, total


def normal_two_tailed_p(z):
    return math.erfc(abs(z) / math.sqrt(2))


def bonferroni_z(num_tests, alpha=0.05):
    """Smallest z whose two-tailed p survives Bonferroni correction, found by bisection
    (no scipy in this environment)."""
    target_p = alpha / num_tests
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if normal_two_tailed_p(mid) > target_p:
            lo = mid
        else:
            hi = mid
    return hi


STREAM_NAMES_FOR_PERIODICITY = (
    "first", "second", "sum_mod3", "first_minus_second_mod3", "equal",
)


def periodicity_report(target_name, ciphertext, max_lag=40):
    """Heuristic Kasiski/Friedman-style coincidence test over unique derived trit
    streams. Exact duplicates created by square symmetries are tested once. The
    binomial z-score is approximate because lag comparisons overlap, so this ranks
    periodicity leads rather than proving a formal null-model result."""
    findings = []
    tests_run = 0
    seen_streams = set()
    for symmetry in square_symmetries():
        first, second = split_trits(ciphertext, symmetry)
        streams = combine_streams(first, second)
        for stream_name in STREAM_NAMES_FOR_PERIODICITY:
            stream = streams[stream_name]
            stream_key = tuple(stream)
            if stream_key in seen_streams:
                continue
            seen_streams.add(stream_key)
            expected_p = coincidence_rate(stream)
            n = len(stream)
            for lag in range(1, min(max_lag, n - 1) + 1):
                result = lag_match_rate(stream, lag)
                if result is None:
                    continue
                matches, total = result
                if total < 20 or not (0 < expected_p < 1):
                    continue
                observed_p = matches / total
                se = math.sqrt(expected_p * (1 - expected_p) / total)
                if se == 0:
                    continue
                z = (observed_p - expected_p) / se
                tests_run += 1
                findings.append({
                    "target": target_name,
                    "symmetry": symmetry,
                    "stream": stream_name,
                    "lag": lag,
                    "observed": round(observed_p, 4),
                    "expected": round(expected_p, 4),
                    "z": round(z, 3),
                    "n_pairs": total,
                })
    findings.sort(key=lambda f: -abs(f["z"]))
    return findings, tests_run


def run_self_tests():
    symmetries = square_symmetries()
    assert len(symmetries) == 8
    maps = []
    for name in symmetries:
        mapping = coordinate_map(name)
        assert set(mapping) == set(SYMBOLS)
        assert set(mapping.values()) == {
            (row, col) for row in range(3) for col in range(3)
        }
        maps.append(tuple(mapping[symbol] for symbol in SYMBOLS))
    assert len(set(maps)) == 8
    assert coordinate_map("identity")["a"] == (0, 0)
    assert coordinate_map("identity")["i"] == (2, 2)

    sample = "abcdef"
    for route in ROUTES:
        routed = route_text(sample, 2, 3, route)
        assert len(routed) == len(sample)
        assert Counter(routed) == Counter(sample)

    first, second = split_trits("abcdefghi", "identity")
    assert first == [0, 0, 0, 1, 1, 1, 2, 2, 2]
    assert second == [0, 1, 2, 0, 1, 2, 0, 1, 2]
    assert pack_base243([0, 0, 0, 0, 0], 0) == b"\x00"
    assert pack_base243([2, 2, 2, 2, 2], 0) == b"\xf2"
    assert pack_whole_base3([1, 0, 0]) == b"\x09"
    assert pack_bits([1, 0, 1, 0, 1, 0, 1, 0], 0) == b"\xaa"
    assert signature_name(b"Salted__payload") == "openssl-salted"

    assert coincidence_rate([0, 0, 0]) == 1.0
    assert coincidence_rate([]) == 0.0
    assert lag_match_rate([0, 1, 0, 1], 2) == (2, 2)
    assert lag_match_rate([0, 1], 5) is None
    assert normal_two_tailed_p(0.0) == 1.0
    assert bonferroni_z(1, alpha=0.05) > 1.9  # ~1.96 for a single test
    findings, tests_run = periodicity_report("dbbi", "ab" * 45 + "a")  # period-2 stream
    assert tests_run > 0
    assert any(f["lag"] % 2 == 0 and f["z"] > 5 for f in findings[:5])

    print("[*] dual-ternary self-tests passed")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        choices=("dbbi", "faed", "both"),
        default="both",
    )
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument(
        "--no-aes",
        action="store_true",
        help="skip AES-oracle checks for highly printable outputs",
    )
    parser.add_argument(
        "--newline-variants",
        action="store_true",
        help="include LF/CRLF passphrase variants in AES checks",
    )
    parser.add_argument(
        "--json-out",
        help="write ranked candidates, statistics, and AES hits to this JSON file",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic transform/packing tests before the sweep",
    )
    parser.add_argument(
        "--periodicity",
        action="store_true",
        help="run the trit-stream coincidence/periodicity null-model gate instead of "
             "the full structural sweep (recommended before instruction-program or "
             "cross-target extensions)",
    )
    parser.add_argument("--max-lag", type=int, default=40)
    parser.add_argument(
        "--periodicity-top", type=int, default=15,
        help="how many highest-|z| findings to print per target",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()

    selected = TARGETS if args.target == "both" else {args.target: TARGETS[args.target]}

    if args.periodicity:
        for target_name, ciphertext in selected.items():
            findings, tests_run = periodicity_report(target_name, ciphertext, max_lag=args.max_lag)
            crit_z = bonferroni_z(tests_run) if tests_run else float("inf")
            print(f"\n[*] {target_name}: {tests_run:,} coincidence tests run "
                  f"(exact duplicate derived streams removed; up to {args.max_lag} lags)")
            print(f"[*] Heuristic Bonferroni threshold: |z| >= {crit_z:.2f} "
                  f"(alpha=0.05; overlapping lag pairs make z approximate)")
            survivors = [f for f in findings if abs(f["z"]) >= crit_z]
            print(f"[*] {len(survivors)} finding(s) survive correction; "
                  f"top {args.periodicity_top} by |z| shown below regardless:")
            for f in findings[:args.periodicity_top]:
                flag = " ** SURVIVES BONFERRONI **" if abs(f["z"]) >= crit_z else ""
                print(f"    z={f['z']:7.3f} lag={f['lag']:3d} {f['stream']:<24} "
                      f"{f['symmetry']:<20} observed={f['observed']:.4f} "
                      f"expected={f['expected']:.4f} n={f['n_pairs']}{flag}")
        return

    report = {}
    total_hits = 0
    for target_name, ciphertext in selected.items():
        print(f"\n[*] sweeping {target_name}: {len(ciphertext)} symbols")
        ranked, hits, stats = sweep_target(
            target_name,
            ciphertext,
            use_aes=not args.no_aes,
            newline_variants=args.newline_variants,
        )
        print(
            f"[*] {stats['routes']} unique routes, "
            f"{stats['unique_outputs']:,} unique decoded outputs, "
            f"{stats['aes_keystrings']:,} AES keystrings, "
            f"{stats['aes_hits']} hits"
        )
        for rank, candidate in enumerate(ranked[:args.top], 1):
            print_candidate(candidate, rank)
        for hit in hits:
            print(f"\n[+++ AES HIT] {hit}\n")
        total_hits += len(hits)
        report[target_name] = {
            "stats": stats,
            "hits": hits,
            "candidates": [asdict(candidate) for candidate in ranked],
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
