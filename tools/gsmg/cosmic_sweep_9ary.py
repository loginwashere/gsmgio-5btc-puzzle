#!/usr/bin/env python3
"""Phase 9 -- dictionary-scale sweep of the "native base-9 checkerboard" hypothesis
for the GSMG.io "Cosmic Duality" endgame (dbbi/faed).

Unlike cosmic_sweep.py (which translates a-i into decimal digits via MAPS, then
brute-forces all 45 decimal escape-pairs x 2 mappings), this sweep is built on a
structural finding: escape-share frequency analysis (comparing dbbi's symbol
frequencies against the known-good 3.2.2 escape-digit character share) singles out
{b,e} as the escape pair with no close second (47.25% combined share vs the 46.98%
precedent; next-best candidate pair is 38.5%), and it's the only pair (among the very
few that segment dbbi cleanly) with that quality of match. That collapses the
mapping+escape-pair search from 90 combinations per keyword down to 2 (just the
e1/e2 order), and forces a 7-top + 9 + 9 = 25 symbol code table (pad25(), a classic
I/J-merged Polybius-style alphabet) instead of pad28()'s 26-letters-plus-2-dots.

See doc/GSMG_PUZZLE.md's "Cosmic Duality" section for the full derivation.

Usage:
    python3 tools/gsmg/cosmic_sweep_9ary.py --wordlist wordlists/gsmg/phrases.txt
    python3 tools/gsmg/cosmic_sweep_9ary.py --target both --workers 16
"""
import argparse
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import islice
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    KDF_VARIANTS,
    TRANSFORM_KINDS,
    aes_try_open,
    answer_forms,
    decode_9ary,
    keystr_forms,
    pad25,
    transpose,
)
from data import DBBI, FAED  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}


class SweepConfig(NamedTuple):
    escape_orders: tuple
    drop_letters: tuple
    topologies: tuple
    tail_fills: tuple
    merge_directions: tuple
    kdf_variants: tuple
    input_transforms: tuple
    output_transforms: tuple
    newline_variants: bool


DEFAULT_CONFIG = SweepConfig(
    escape_orders=(("b", "e"), ("e", "b")),
    drop_letters=("J",),
    topologies=("top_first",),
    tail_fills=("forward",),
    merge_directions=("backward",),
    kdf_variants=(("sha256", 32),),
    input_transforms=("identity",),
    output_transforms=("identity",),
    newline_variants=False,
)

DEFAULT_WORDLISTS = [
    "wordlists/gsmg/phrases.txt",
    "wordlists/gsmg/phrases-joined.txt",
    "wordlists/cypherpunk/phrases.txt",
    "wordlists/cypherpunk/phrases-joined.txt",
    "wordlists/bitcoin-historical/phrases.txt",
    "wordlists/bitcoin-historical/phrases-joined.txt",
    "wordlists/gutenberg/phrases.txt",
    "wordlists/gutenberg/phrases-joined.txt",
    "/usr/share/dict/american-english",
    "/usr/share/dict/british-english",
    "/usr/share/dict/cracklib-small",
]


def test_batch(chunk, targets, config):
    """Process a whole chunk of candidates x targets in one worker call, so the
    main process only ever tracks (total_candidates / CHUNK_SIZE) futures instead
    of one per (candidate, target) pair -- submitting 25M+ individual futures is
    what OOM-killed the earlier run (19.6GB RSS before the kernel killed it)."""
    hits = []
    for candidate in chunk:
        for target in targets:
            hits.extend(test_keyword(candidate, target, config))
    return hits


def test_keyword(candidate: str, target: str, config=DEFAULT_CONFIG):
    hits = []
    for in_xf in config.input_transforms:
        target_str = transpose(TARGETS[target], in_xf)
        for drop in config.drop_letters:
            for tail_fill in config.tail_fills:
                for merge_direction in config.merge_directions:
                    alphabet = pad25(candidate, drop=drop, tail_fill=tail_fill,
                                      merge_direction=merge_direction)
                    if len(alphabet) != 25:
                        continue
                    for topology in config.topologies:
                        for e1, e2 in config.escape_orders:
                            ans = decode_9ary(target_str, alphabet, e1, e2, topology)
                            if "?" in ans:
                                continue
                            for out_xf in config.output_transforms:
                                ans_xf = transpose(ans, out_xf)
                                for form in answer_forms(ans_xf):
                                    if not form:
                                        continue
                                    for keystr in keystr_forms(
                                        form,
                                        config.newline_variants,
                                    ):
                                        r = aes_try_open(keystr, config.kdf_variants)
                                        if r:
                                            tag, body, digest_name, key_len = r
                                            hits.append({
                                                "candidate": candidate,
                                                "target": target,
                                                "input_transform": in_xf,
                                                "output_transform": out_xf,
                                                "drop": drop,
                                                "tail_fill": tail_fill,
                                                "merge_direction": merge_direction,
                                                "topology": topology,
                                                "escapes": (e1, e2),
                                                "answer": ans_xf,
                                                "form": form,
                                                "keystr": keystr,
                                                "blob": tag,
                                                "kdf": f"{digest_name}/aes{key_len * 8}",
                                                "plaintext": body[:500],
                                            })
    return hits


def load_wordlist(path: str):
    p = Path(path)
    if not p.exists():
        print(f"[!] wordlist not found, skipping: {path}", file=sys.stderr)
        return []
    out = []
    seen = set()
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wordlist", action="append", default=None,
                     help="wordlist file (repeatable). Defaults to the curated+mid-size set.")
    ap.add_argument("--target", choices=["dbbi", "faed", "both"], default="dbbi")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--drop-letters", default="J",
                     help="comma-separated letters to try as the merged/dropped 26th "
                          "letter (default: J, the classic Polybius choice)")
    ap.add_argument("--escapes", default="b,e",
                     help="the 2 escape symbols, comma-separated (default: b,e -- "
                          "dbbi's own best-fit pair; pass g,i to test faed's own "
                          "best-fit pair as its own hypothesis instead of assuming "
                          "faed is pure payload)")
    ap.add_argument("--topologies", default="top_first",
                     help="comma-separated board layouts to try: top_first "
                          "(mirrors the validated 3.2.2 layout), escapes_first "
                          "(untested reversal), or 'both'")
    ap.add_argument("--tail-fills", default="forward",
                     help="comma-separated leftover-letter fill orders to try: "
                          "forward, reverse, keyboard, or 'all'. Confirmed "
                          "unconstrained for 3.2.2 itself (its real JQZXW tail is "
                          "never read by that answer's 91 characters, so all 3 "
                          "presets decode it identically) -- only matters for a "
                          "candidate whose true answer needs a rare tail letter, "
                          "which can't be known in advance, hence still swept")
    ap.add_argument("--all-drop-letters", action="store_true",
                     help="try all 26 possible drop/merge letters instead of --drop-letters")
    ap.add_argument("--merge-directions", default="backward",
                     help="comma-separated directions the dropped letter folds in: "
                          "backward (J->I, the only direction ever tested before), "
                          "forward (J->K), or 'both'")
    ap.add_argument("--all-kdf", action="store_true",
                     help="try all 6 KDF variants (default: just sha256/aes256, since "
                          "the KDF axis was already exhaustively checked separately)")
    ap.add_argument("--input-transforms", default="identity",
                     help="comma-separated transforms applied to the raw target "
                          "string before decoding: identity, reverse, col2..col6, "
                          "halfswap, mirror9, or 'all'")
    ap.add_argument("--output-transforms", default="identity",
                     help="comma-separated transforms applied to the decoded answer "
                          "before hashing: identity, reverse, col2..col6, halfswap, "
                          "mirror9, or 'all'")
    ap.add_argument("--newline-variants", action="store_true",
                     help="also try every passphrase form with a trailing \\n/\\r\\n "
                          "appended, testing the 'enter' (abba-encoded word embedded "
                          "in the AES blob) as a press-Enter/terminal-newline instruction")
    ap.add_argument("--hits-out", default=str(Path(__file__).parent / "hits_9ary.txt"))
    ap.add_argument("--chunk-size", type=int, default=2000,
                     help="candidates per worker task (bounds in-flight futures)")
    args = ap.parse_args()

    if args.all_drop_letters:
        drop_letters = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    else:
        drop_letters = tuple(
            c.strip().upper() for c in args.drop_letters.split(",") if c.strip()
        )
    merge_directions = ("backward", "forward") if args.merge_directions == "both" \
        else tuple(d.strip().lower() for d in args.merge_directions.split(",") if d.strip())
    escapes = tuple(c.strip().lower() for c in args.escapes.split(","))
    topologies = ("top_first", "escapes_first") if args.topologies == "both" \
        else tuple(t.strip() for t in args.topologies.split(",") if t.strip())
    tail_fills = ("forward", "reverse", "keyboard") if args.tail_fills == "all" \
        else tuple(t.strip() for t in args.tail_fills.split(",") if t.strip())
    input_transforms = tuple(TRANSFORM_KINDS) if args.input_transforms == "all" \
        else tuple(t.strip() for t in args.input_transforms.split(",") if t.strip())
    output_transforms = tuple(TRANSFORM_KINDS) if args.output_transforms == "all" \
        else tuple(t.strip() for t in args.output_transforms.split(",") if t.strip())

    if not drop_letters or any(len(c) != 1 or c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                               for c in drop_letters):
        ap.error("--drop-letters must contain one or more comma-separated A-Z letters")
    if len(escapes) != 2 or escapes[0] == escapes[1] or any(
        len(c) != 1 or c not in "abcdefghi" for c in escapes
    ):
        ap.error("--escapes must contain two distinct comma-separated a-i symbols")
    if not merge_directions or not set(merge_directions) <= {"backward", "forward"}:
        ap.error("--merge-directions must use backward, forward, or both")
    if not topologies or not set(topologies) <= {"top_first", "escapes_first"}:
        ap.error("--topologies must use top_first, escapes_first, or both")
    if not tail_fills or not set(tail_fills) <= {"forward", "reverse", "keyboard"}:
        ap.error("--tail-fills must use forward, reverse, keyboard, or all")
    if not input_transforms or not set(input_transforms) <= set(TRANSFORM_KINDS):
        ap.error(f"--input-transforms must use {', '.join(TRANSFORM_KINDS)}, or all")
    if not output_transforms or not set(output_transforms) <= set(TRANSFORM_KINDS):
        ap.error(f"--output-transforms must use {', '.join(TRANSFORM_KINDS)}, or all")

    config = SweepConfig(
        escape_orders=(escapes, escapes[::-1]),
        drop_letters=drop_letters,
        topologies=topologies,
        tail_fills=tail_fills,
        merge_directions=merge_directions,
        kdf_variants=tuple(KDF_VARIANTS) if args.all_kdf else (("sha256", 32),),
        input_transforms=input_transforms,
        output_transforms=output_transforms,
        newline_variants=args.newline_variants,
    )

    wordlist_paths = args.wordlist or DEFAULT_WORDLISTS
    candidates = []
    seen = set()
    for wl in wordlist_paths:
        for c in load_wordlist(wl):
            if c not in seen:
                seen.add(c)
                candidates.append(c)
    if args.limit:
        candidates = candidates[:args.limit]

    targets = ["dbbi", "faed"] if args.target == "both" else [args.target]

    total = len(candidates) * len(targets)
    chunk_size = args.chunk_size
    chunks = [candidates[i:i + chunk_size] for i in range(0, len(candidates), chunk_size)]
    print(f"[*] {len(candidates):,} unique candidates x {len(targets)} target(s) "
          f"= {total:,} keyword-tests, {args.workers} workers, "
          f"{len(chunks):,} chunks of {chunk_size}")
    print(f"[*] wordlists: {wordlist_paths}")

    start = time.time()
    done = 0
    all_hits = []
    # Bounded in-flight window: submitting all chunks upfront (or worse, one future
    # per candidate) is what OOM-killed the earlier run. Keep only ~4x worker-count
    # chunks queued at a time and refill as they complete.
    max_in_flight = max(args.workers * 4, 8)

    last_print = 0.0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        chunk_iter = iter(chunks)
        in_flight = {}
        for c in islice(chunk_iter, max_in_flight):
            in_flight[ex.submit(test_batch, c, targets, config)] = len(c)

        while in_flight:
            completed, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for fut in completed:
                n = in_flight.pop(fut)
                done += n * len(targets)
                hits = fut.result()
                if hits:
                    all_hits.extend(hits)
                    for h in hits:
                        print(f"\n[+++ HIT] {h}\n")
                    with open(args.hits_out, "a") as hf:
                        for h in hits:
                            hf.write(f"{h}\n")
                nxt = next(chunk_iter, None)
                if nxt is not None:
                    in_flight[ex.submit(test_batch, nxt, targets, config)] = len(nxt)

            now = time.time()
            if now - last_print >= 1.0 or not in_flight:
                last_print = now
                rate = done / max(now - start, 1e-9)
                eta = (total - done) / max(rate, 1e-9)
                print(f"\r[*] {done:,}/{total:,} ({rate:.1f}/s, ETA {eta:.0f}s) "
                      f"hits={len(all_hits)}   ", end="", flush=True)
    print()

    elapsed = time.time() - start
    print(f"\n[*] done in {elapsed:.1f}s. {len(all_hits)} hit(s) out of {total:,} keyword-tests.")
    if not all_hits:
        print("[*] negative result -- no candidate opened either AES blob.")


if __name__ == "__main__":
    main()
