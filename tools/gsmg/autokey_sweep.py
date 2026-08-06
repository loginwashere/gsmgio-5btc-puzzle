#!/usr/bin/env python3
"""Autokey-cipher sweep against dbbi/faed (Plan A, option D).

Tests whether either target carries an *autokey* keystream -- a short
priming seed whose key stream is extended not by a fixed recursion (that's
chain_addition_sweep.py's hypothesis) but by feeding the stream's own past
values back in as the key. Two classic variants, both tried:
  - ciphertext autokey: key extends using past CIPHERTEXT digits (decryptable
    non-sequentially, since the full ciphertext is already known upfront)
  - plaintext autokey: key extends using past RECOVERED plaintext digits
    (decrypted sequentially)

Purely thematic motivation (never mentioned anywhere in this project's prior
history, so a genuinely untested mechanism): autokey's self-referential key
extension echoes "duality" more directly than an arbitrary external keyword.

Same "pre" (dechain raw 9-symbol stream before checkerboard decode) / "post"
(dechain decoded letters after checkerboard decode) structure as
chain_addition_sweep.py, and the same curated candidate sets.

Usage:
    python3 tools/gsmg/autokey_sweep.py
"""
import argparse
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import islice
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    aes_try_open, answer_forms, autokey_dechain_9ary, autokey_dechain_letters,
    decode_9ary, keystr_forms, keyword_to_seed, pad25,
)
from data import DBBI, FAED  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}

# Per-target escape-pair defaults -- see chain_addition_sweep.py's identical
# comment; this script had the same gap (faed only ever tested under dbbi's
# {b,e}, never its own {g,i} best-fit or the {h,e} mirror).
DEFAULT_DBBI_ESCAPES = "b,e"
DEFAULT_FAED_ESCAPES = "g,i;h,e"
SIGNS = (-1, 1)
MODES = ("ciphertext", "plaintext")


def parse_escape_pairs(spec: str):
    """"b,e" -> [(b,e),(e,b)]; "g,i;h,e" -> [(g,i),(i,g),(h,e),(e,h)] -- every
    listed pair expanded to both escape/digit orders."""
    pairs = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        e1, e2 = [c.strip().lower() for c in chunk.split(",")]
        if len(e1) != 1 or len(e2) != 1 or e1 == e2:
            raise ValueError(f"invalid escape pair {chunk!r} in {spec!r}")
        pairs.append((e1, e2))
        pairs.append((e2, e1))
    if not pairs:
        raise ValueError(f"no escape pairs parsed from {spec!r}")
    return pairs

CURATED_WORDLISTS = [
    "wordlists/gsmg/riddle_combinations.txt",
    "wordlists/gsmg/matrix_trilogy.txt",
    "wordlists/gsmg/discovered_paths.txt",
    "wordlists/gsmg/last_command.txt",
    "wordlists/gsmg/salphaseion_own_keywords_combined.txt",
]


def _check_answer(ans, alpha_cand, key_cand, target, stage, mode, sign, escapes, hits):
    for form in answer_forms(ans):
        if not form:
            continue
        for keystr in keystr_forms(form):
            r = aes_try_open(keystr)
            if r:
                tag, body, digest_name, key_len = r
                hits.append({
                    "alphabet_candidate": alpha_cand,
                    "keystream_candidate": key_cand,
                    "target": target,
                    "stage": stage,
                    "autokey_mode": mode,
                    "sign": sign,
                    "escapes": escapes,
                    "answer": ans,
                    "form": form,
                    "keystr": keystr,
                    "blob": tag,
                    "kdf": f"{digest_name}/aes{key_len * 8}",
                    "plaintext": body[:500],
                })


def test_pair(alpha_candidate: str, key_candidate: str, target_escapes: dict):
    hits = []
    alphabet = pad25(alpha_candidate)
    if len(alphabet) != 25:
        return hits
    seed9 = keyword_to_seed(key_candidate, 9)
    seed26 = keyword_to_seed(key_candidate, 26)

    for target_name, target_str in TARGETS.items():
        if target_name not in target_escapes:
            continue
        escape_orders = target_escapes[target_name]
        # PRE: autokey-dechain the raw ciphertext (mod 9), then checkerboard-decode.
        if len(seed9) >= 1:
            for mode in MODES:
                for sign in SIGNS:
                    dechained = autokey_dechain_9ary(target_str, seed9, mode, sign)
                    for e1, e2 in escape_orders:
                        ans = decode_9ary(dechained, alphabet, e1, e2)
                        if "?" not in ans:
                            _check_answer(ans, alpha_candidate, key_candidate, target_name,
                                          "pre", mode, sign, (e1, e2), hits)

        # POST: checkerboard-decode as usual, then autokey-dechain the letters (mod 26).
        if len(seed26) >= 1:
            for e1, e2 in escape_orders:
                ans = decode_9ary(target_str, alphabet, e1, e2)
                if "?" in ans:
                    continue
                for mode in MODES:
                    for sign in SIGNS:
                        dechained_ans = autokey_dechain_letters(ans, seed26, mode, sign)
                        _check_answer(dechained_ans, alpha_candidate, key_candidate, target_name,
                                      "post", mode, sign, (e1, e2), hits)
    return hits


def test_batch(alpha_chunk, key_candidates, target_escapes):
    hits = []
    for alpha in alpha_chunk:
        for key in key_candidates:
            hits.extend(test_pair(alpha, key, target_escapes))
    return hits


def load_wordlist(path: str):
    p = Path(path)
    if not p.exists():
        print(f"[!] wordlist not found, skipping: {path}", file=sys.stderr)
        return []
    out, seen = [], set()
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                out.append(line)
    return out


def load_candidates(paths):
    out, seen = [], set()
    for wl in paths:
        for c in load_wordlist(wl):
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alphabet-wordlist", action="append", default=None)
    ap.add_argument("--keystream-wordlist", action="append", default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--alpha-limit", type=int, default=None)
    ap.add_argument("--key-limit", type=int, default=None)
    ap.add_argument("--alpha-skip", type=int, default=0)
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--hits-out", default=str(Path(__file__).parent / "hits_autokey.txt"))
    ap.add_argument(
        "--dbbi-escapes", default=DEFAULT_DBBI_ESCAPES,
        help="dbbi escape pair, 'e1,e2' (default: %(default)r; both orders tested)",
    )
    ap.add_argument(
        "--faed-escapes", default=DEFAULT_FAED_ESCAPES,
        help="faed escape pair(s), 'e1,e2' or ';'-separated list (default: "
             "%(default)r -- faed's own best-fit {g,i} plus the {h,e} mirror; "
             "both orders tested each. Pass 'b,e' to reproduce this script's "
             "historical scope, which only ever tested faed under dbbi's pair)",
    )
    ap.add_argument(
        "--targets", default="dbbi,faed",
        help="comma-separated subset of dbbi,faed to test (default: both) -- "
             "e.g. --targets faed to backfill only faed's new escape coverage "
             "over an alpha range already completed for dbbi under the old scope",
    )
    args = ap.parse_args()

    requested_targets = {t.strip() for t in args.targets.split(",") if t.strip()}
    unknown = requested_targets - set(TARGETS)
    if unknown:
        raise SystemExit(f"unknown --targets entries: {sorted(unknown)}")
    target_escapes = {
        name: parse_escape_pairs(spec)
        for name, spec in (("dbbi", args.dbbi_escapes), ("faed", args.faed_escapes))
        if name in requested_targets
    }

    alpha_candidates = load_candidates(args.alphabet_wordlist or CURATED_WORDLISTS)
    key_candidates = load_candidates(args.keystream_wordlist or CURATED_WORDLISTS)
    if args.alpha_skip:
        alpha_candidates = alpha_candidates[args.alpha_skip:]
        print(f"[*] resuming: skipped first {args.alpha_skip:,} alphabet candidates")
    if args.alpha_limit:
        alpha_candidates = alpha_candidates[:args.alpha_limit]
    if args.key_limit:
        key_candidates = key_candidates[:args.key_limit]

    total_pairs = len(alpha_candidates) * len(key_candidates)
    chunk_size = args.chunk_size
    chunks = [alpha_candidates[i:i + chunk_size] for i in range(0, len(alpha_candidates), chunk_size)]
    print(f"[*] {len(alpha_candidates):,} alphabet candidates x {len(key_candidates):,} "
          f"keystream candidates = {total_pairs:,} pairs, {args.workers} workers, "
          f"{len(chunks):,} chunks of {chunk_size}")
    print(f"[*] targets: {sorted(target_escapes)}  escapes: {target_escapes}")

    start = time.time()
    done_pairs = 0
    all_hits = []
    max_in_flight = max(args.workers * 4, 8)
    last_print = 0.0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        chunk_iter = iter(chunks)
        in_flight = {}
        for c in islice(chunk_iter, max_in_flight):
            in_flight[ex.submit(test_batch, c, key_candidates, target_escapes)] = len(c)

        while in_flight:
            completed, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for fut in completed:
                n = in_flight.pop(fut)
                done_pairs += n * len(key_candidates)
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
                    in_flight[ex.submit(test_batch, nxt, key_candidates, target_escapes)] = len(nxt)

            now = time.time()
            if now - last_print >= 1.0 or not in_flight:
                last_print = now
                rate = done_pairs / max(now - start, 1e-9)
                eta = (total_pairs - done_pairs) / max(rate, 1e-9)
                print(f"\r[*] {done_pairs:,}/{total_pairs:,} pairs ({rate:.1f}/s, ETA {eta:.0f}s) "
                      f"hits={len(all_hits)}   ", end="", flush=True)
    print()

    elapsed = time.time() - start
    print(f"\n[*] done in {elapsed:.1f}s. {len(all_hits)} hit(s) out of {total_pairs:,} pairs.")
    if not all_hits:
        print("[*] negative result -- no (alphabet, keystream-seed) pair opened either AES blob.")


if __name__ == "__main__":
    main()
