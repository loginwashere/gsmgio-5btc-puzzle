#!/usr/bin/env python3
"""Phase 2 — dictionary-scale sweep of the checkerboard-keyword parameter for the
GSMG.io "Cosmic Duality" endgame (dbbi/faed), verified against the real AES-decrypt
oracle rather than an English-word heuristic (which is known-unreliable — see
doc/GSMG_PUZZLE.md's "verification problem" section).

For every candidate line in the given wordlist(s):
    pad28(candidate) -> alphabet
    for each of 2 digit-mappings x all 45 escape-digit pairs:
        decode(target) -> candidate answer
        for each answer-normalization form:
            test as AES passphrase (raw + SHA-256 + double-SHA-256 hex)
            against both known blobs

A reported hit has valid PKCS7 padding and printability far above the random-byte
baseline. It is a plausibility result requiring inspection, not authenticated proof.
Any hit is printed immediately and logged; the sweep keeps running afterward.

Usage:
    python3 tools/gsmg/cosmic_sweep.py --wordlist wordlists/gsmg/phrases.txt
    python3 tools/gsmg/cosmic_sweep.py \\
        --wordlist wordlists/gsmg/phrases.txt \\
        --wordlist wordlists/gsmg/phrases-joined.txt \\
        --wordlist wordlists/cypherpunk/phrases-joined.txt \\
        --target dbbi --workers 8 --limit 1000
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import ALL_ESCAPE_PAIRS, MAPS, aes_try_open, answer_forms, decode, keystr_forms, pad28  # noqa: E402
from data import DBBI, FAED  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}

# Default wordlist order for the "curated + mid-size" pass (no rockyou/Pwdb here —
# those are opt-in via extra --wordlist flags, per doc/GSMG_PUZZLE.md's plan).
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


def test_keyword(candidate: str, target: str):
    """Test one candidate keyword against `target` (dbbi/faed). Returns a list of
    hit-dicts (almost always empty)."""
    target_str = TARGETS[target]
    alphabet = pad28(candidate)
    if len(alphabet) != 28:
        return []
    hits = []
    for map_name, mapping in MAPS.items():
        digits = "".join(mapping[c] for c in target_str)
        for e1, e2 in ALL_ESCAPE_PAIRS:
            ans = decode(digits, alphabet, e1, e2)
            if "?" in ans:
                continue
            for form in answer_forms(ans):
                if not form:
                    continue
                for keystr in keystr_forms(form):
                    r = aes_try_open(keystr)
                    if r:
                        tag, body, digest_name, key_len = r
                        hits.append({
                            "candidate": candidate,
                            "target": target,
                            "map": map_name,
                            "escapes": (e1, e2),
                            "answer": ans,
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
    ap.add_argument("--target", choices=["dbbi", "faed", "both"], default="dbbi",
                     help="which undecoded string to sweep (default: dbbi — the "
                          "structured/key-like one; faed's flat IoC suggests it's "
                          "high-entropy payload, not checkerboard text)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--limit", type=int, default=None, help="cap total candidates (for a timing dry-run)")
    ap.add_argument("--hits-out", default=str(Path(__file__).parent / "hits.txt"))
    args = ap.parse_args()

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
    print(f"[*] {len(candidates):,} unique candidates x {len(targets)} target(s) "
          f"= {total:,} keyword-tests, {args.workers} workers")
    print(f"[*] wordlists: {wordlist_paths}")

    start = time.time()
    done = 0
    all_hits = []
    jobs = [(c, t) for c in candidates for t in targets]

    last_print = 0.0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(test_keyword, c, t): (c, t) for c, t in jobs}
        for fut in as_completed(futures):
            done += 1
            hits = fut.result()
            if hits:
                all_hits.extend(hits)
                for h in hits:
                    print(f"\n[+++ HIT] {h}\n")
                with open(args.hits_out, "a") as hf:
                    for h in hits:
                        hf.write(f"{h}\n")
            now = time.time()
            if now - last_print >= 1.0 or done == total:
                last_print = now
                rate = done / max(now - start, 1e-9)
                eta = (total - done) / max(rate, 1e-9)
                print(f"\r[*] {done:,}/{total:,} ({rate:.1f}/s, ETA {eta:.0f}s) "
                      f"hits={len(all_hits)}   ", end="", flush=True)
    print()

    elapsed = time.time() - start
    print(f"\n[*] done in {elapsed:.1f}s. {len(all_hits)} hit(s) out of {total:,} keyword-tests.")
    if not all_hits:
        print("[*] negative result — no candidate opened either AES blob.")


if __name__ == "__main__":
    main()
