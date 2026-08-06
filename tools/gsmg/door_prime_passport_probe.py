#!/usr/bin/env python3
"""Phase 4 — direct probe of three creator hints that the community's own fork never
tested against the real AES oracle (per its FINDINGS.md's tested-hypothesis list):

    2021-04-01  "another door might be found on {1},{4},{21}"
    2021-12-26  "...prime numbers being mentioned... some characters need to be
                 zeroed out..." (clarifying the same "another door" hint)
    2021-12-31  "The only date I give away is the expiry date of neo's passport."
                 (= September 11, 2001 — a well-known Matrix (1999) prop Easter egg)

Two things ARE already covered by the fork's own tools and are deliberately NOT
repeated here:
  - The "matrixsumlist triangle" framework with prime/blue/yellow zeroing predicates
    (`triangle_zero.py`, `matrixtri.py`) — falsified as apophenia via a 38k-random-
    string null-model test (see doc/GSMG_PUZZLE.md).
  - Whether dbbi's letter 'b' sits at prime string-positions (`prime_theory.py`,
    `prime2.py`) — inconclusive, not re-litigated here.

What IS untested: whether these hints, read literally, work as direct AES
passphrases, or as a "zero out the digit at prime positions" transform applied
directly to the *validated* checkerboard-decode pipeline (not the alternate
triangle/XOR framework). Both are cheap and well-motivated, so both are tried here,
verified only via the real oracle (`aes_try_open`) — never English-word scoring.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import MAPS, aes_try_open, answer_forms, decode  # noqa: E402
from data import ALPHA_322, DBBI, FAED  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}


def is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            return False
    return True


def nth_prime(n):
    count = 0
    x = 1
    while count < n:
        x += 1
        if is_prime(x):
            count += 1
    return x


# ---- candidate strings, direct AES passphrases ----------------------------------
P1, P4, P21 = nth_prime(1), nth_prime(4), nth_prime(21)  # 2, 7, 73
assert (P1, P4, P21) == (2, 7, 73)

CANDIDATES = [
    # literal "{1},{4},{21}"
    "1421", "142001", "1,4,21", "1 4 21", "1-4-21", "142100121",
    "anotherdoor1421", "anotherdoormightbefoundon1421",
    "anotherdoormightbefoundon142001",
    # 1st/4th/21st primes: 2, 7, 73
    "273", "2773", str(P1) + str(P4) + str(P21),
    "prime1prime4prime21", "2 7 73",
    # neo's passport expiry date (The Matrix, 1999) = September 11, 2001
    "09112001", "9112001", "11092001", "091101", "110901", "911", "9112001911",
    "September 11 2001", "september112001", "20010911", "010911",
    "neospassport09112001", "neospassport911",
    # combinations of the two hints (per the Dec-2021 message linking them)
    "1421september112001", "primes1421zeroedout", "zeroedout1421",
    "anotherdoorprimeszeroedout",
]


def probe_direct_passphrases():
    print(f"[*] Phase 4.1: {len(CANDIDATES)} direct-AES-passphrase candidates "
          f"(raw + sha256-hex, both blobs)")
    hits = []
    for c in CANDIDATES:
        for keystr in (c, hashlib.sha256(c.encode()).hexdigest()):
            r = aes_try_open(keystr)
            if r:
                hits.append((c, keystr, r))
                print(f"\n[+++ HIT] candidate={c!r} keystr={keystr!r} -> {r}\n")
    if not hits:
        print("    0 hits.")
    return hits


def zero_positions(digits, positions):
    positions = set(positions)
    return "".join("0" if i in positions else d for i, d in enumerate(digits))


def probe_prime_zeroing():
    """Zero the digit at every prime (1-indexed) position, and separately at just
    positions {1,4,21}, directly in the validated checkerboard digit-stream (escapes
    1,4, the only known-good alphabet ALPHA_322 — the sole alphabet we can verify
    the decoder against), then run the result through the real AES oracle."""
    print("\n[*] Phase 4.2: prime-position zeroing on the validated decode pipeline")
    hits = []
    tested = 0
    for tname, tstr in TARGETS.items():
        n = len(tstr)
        prime_pos = [i for i in range(n) if is_prime(i + 1)]
        variants = {
            "zero_primes": prime_pos,
            "zero_nonprimes": [i for i in range(n) if i not in prime_pos],
            "zero_1_4_21": [0, 3, 20] if n > 20 else [],
        }
        for vname, positions in variants.items():
            if not positions:
                continue
            for map_name, mapping in MAPS.items():
                digits = "".join(mapping[c] for c in tstr)
                zdigits = zero_positions(digits, positions)
                for e1, e2 in ((1, 4),):
                    ans = decode(zdigits, ALPHA_322, e1, e2)
                    if "?" in ans:
                        continue
                    tested += 1
                    for form in answer_forms(ans):
                        if not form:
                            continue
                        for keystr in (form, hashlib.sha256(form.encode()).hexdigest()):
                            r = aes_try_open(keystr)
                            if r:
                                hits.append((tname, vname, map_name, ans, form, r))
                                print(f"\n[+++ HIT] target={tname} variant={vname} "
                                      f"map={map_name} answer={ans!r} -> {r}\n")
    print(f"    {tested} decode-forms tested, {len(hits)} hit(s).")
    return hits


def main():
    all_hits = probe_direct_passphrases() + probe_prime_zeroing()
    print(f"\n[*] done. {len(all_hits)} hit(s) total.")
    if not all_hits:
        print("[*] negative result — none of the door/prime/passport readings opened "
              "either AES blob.")
    hits_out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "hits_door_prime_passport.txt",
    )
    if all_hits:
        with open(hits_out, "a") as f:
            for h in all_hits:
                f.write(f"{h}\n")


if __name__ == "__main__":
    main()
