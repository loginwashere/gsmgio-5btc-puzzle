#!/usr/bin/env python3
"""Phase 10 -- "dbbi/faed as a coupled pair, not two independent targets" hypothesis.

Every prior sweep (cosmic_sweep_9ary.py) treats `dbbi` and `faed` as two independent
checkerboard targets, each decoded under its own candidate keyword pulled straight
from a wordlist. This sweep tests a different, "yin-yang" reading instead: `dbbi` is
the small/structured "eye" that decodes into the *keyword* for the larger "eye"
(`faed`) -- i.e. chain the decode: candidate -> pad25 board -> decode(dbbi) -> that
plaintext becomes the new pad25 board's seed -> decode(faed) -> test as AES passphrase.

Usage:
    python3 tools/gsmg/chain_sweep.py --wordlist wordlists/gsmg/riddle_combinations.txt
"""
import argparse
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import islice
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import aes_try_open, answer_forms, decode_9ary, keystr_forms, pad25  # noqa: E402
from data import DBBI, FAED  # noqa: E402

STAGE1_ESCAPES = [("b", "e"), ("e", "b")]  # dbbi's own decisive pair, both orders
STAGE2_ESCAPES = [("b", "e"), ("e", "b")]  # same pair for the derived faed board

DEFAULT_WORDLISTS = [
    "wordlists/gsmg/chat_mined_words.txt",
    "wordlists/gsmg/chat_mined_lines.txt",
    "wordlists/gsmg/riddle_combinations.txt",
    "wordlists/gsmg/matrix_trilogy.txt",
    "wordlists/gsmg/discovered_paths.txt",
    "wordlists/gsmg/last_command.txt",
    "wordlists/gsmg/salphaseion_own_keywords_combined.txt",
]


def test_keyword(candidate: str):
    hits = []
    alphabet1 = pad25(candidate)
    if len(alphabet1) != 25:
        return hits
    stage2_keywords = set()
    for e1, e2 in STAGE1_ESCAPES:
        dbbi_decoded = decode_9ary(DBBI, alphabet1, e1, e2)
        if "?" in dbbi_decoded:
            continue
        for form in answer_forms(dbbi_decoded):
            if form:
                stage2_keywords.add(form)
    for kw2 in stage2_keywords:
        alphabet2 = pad25(kw2)
        if len(alphabet2) != 25:
            continue
        for e1b, e2b in STAGE2_ESCAPES:
            faed_decoded = decode_9ary(FAED, alphabet2, e1b, e2b)
            if "?" in faed_decoded:
                continue
            for form2 in answer_forms(faed_decoded):
                if not form2:
                    continue
                for keystr in keystr_forms(form2):
                    r = aes_try_open(keystr)
                    if r:
                        tag, body, digest_name, key_len = r
                        hits.append({
                            "candidate": candidate,
                            "stage2_keyword": kw2,
                            "escapes2": (e1b, e2b),
                            "answer": form2,
                            "keystr": keystr,
                            "blob": tag,
                            "kdf": f"{digest_name}/aes{key_len * 8}",
                            "plaintext": body[:500],
                        })
    return hits


def test_batch(chunk):
    hits = []
    for candidate in chunk:
        hits.extend(test_keyword(candidate))
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wordlist", action="append", default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--chunk-size", type=int, default=500)
    ap.add_argument("--hits-out", default=str(Path(__file__).parent / "hits_chain.txt"))
    args = ap.parse_args()

    wordlist_paths = args.wordlist or DEFAULT_WORDLISTS
    candidates, seen = [], set()
    for wl in wordlist_paths:
        for c in load_wordlist(wl):
            if c not in seen:
                seen.add(c)
                candidates.append(c)
    if args.limit:
        candidates = candidates[:args.limit]

    total = len(candidates)
    chunk_size = args.chunk_size
    chunks = [candidates[i:i + chunk_size] for i in range(0, len(candidates), chunk_size)]
    print(f"[*] {total:,} unique candidates (dbbi-decode -> faed-keyword chain), "
          f"{args.workers} workers, {len(chunks):,} chunks of {chunk_size}")
    print(f"[*] wordlists: {wordlist_paths}")

    start = time.time()
    done = 0
    all_hits = []
    max_in_flight = max(args.workers * 4, 8)
    last_print = 0.0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        chunk_iter = iter(chunks)
        in_flight = {}
        for c in islice(chunk_iter, max_in_flight):
            in_flight[ex.submit(test_batch, c)] = len(c)

        while in_flight:
            completed, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for fut in completed:
                n = in_flight.pop(fut)
                done += n
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
                    in_flight[ex.submit(test_batch, nxt)] = len(nxt)

            now = time.time()
            if now - last_print >= 1.0 or not in_flight:
                last_print = now
                rate = done / max(now - start, 1e-9)
                eta = (total - done) / max(rate, 1e-9)
                print(f"\r[*] {done:,}/{total:,} ({rate:.1f}/s, ETA {eta:.0f}s) "
                      f"hits={len(all_hits)}   ", end="", flush=True)
    print()

    elapsed = time.time() - start
    print(f"\n[*] done in {elapsed:.1f}s. {len(all_hits)} hit(s) out of {total:,} candidates.")
    if not all_hits:
        print("[*] negative result -- no chained dbbi->faed candidate opened either AES blob.")


if __name__ == "__main__":
    main()
