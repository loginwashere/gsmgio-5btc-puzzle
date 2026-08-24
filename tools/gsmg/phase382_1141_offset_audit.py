#!/usr/bin/env python3
"""Phase 382: closes the ad-hoc, unlogged "1141-offset" candidate family
(FINDINGS Phase 378, 2026-08-23) with a real, executed, falsifiable test.

Background: Naddiseo/gsmgio-5btc-puzzle's `unverified/phase3.2_1141.md`
(community, added 2026-04-16) hypothesizes that `sha256(plaintext[1141:x])`
-- a slice of the already-authenticated Architect/Cosmic-Duality plaintext
starting at character offset 1141 -- is password/key material, with `x`
left unfixed. Their own attempt (target and `x` range unspecified) reports
"Nothing found." This project's own Phase 378 separately mentions an
unrelated, unlogged "1141-offset check discussed 2026-08-23" that left no
other trace anywhere in this repo. Rather than trust either party's thin
prior attempt, this script gives the idea one real, reproducible test.

New assumption, not previously tested in this project: `plaintext[1141:x]`
-- the exact already-authenticated Architect plaintext this project already
tracks via `telegram_matrix_sum_passage_audit.extract_phase_plaintext`,
flattened to lowercase-no-punctuation (the same normalization this
project's wordlists already use) -- is checkerboard password material for
DBBI and/or FAED, for every valid end offset `x`. This is a closed,
pre-declared, exhaustively-bounded 398-candidate family: `x` ranges over
every integer from 1142 to 1539 inclusive (the flattened plaintext is 1539
characters long), giving every non-empty suffix slice starting at 1141 --
not an open-ended search.

Minimal falsifiable test: run all 398 candidates through the already-
validated `cosmic_sweep_9ary.py` oracle, once per target under that
target's own already-established escape pair -- dbbi `{b,e}`, faed `{g,i}`
(its best-fit pair), and faed `{h,e}` (the explicitly unreconciled mirror
hypothesis, Gap G-ESC-001) -- using every other axis at that tool's own
calibrated defaults (topology, tail-fill, merge-direction, drop-letter,
KDF). No parameter tuning after seeing a result.

Stop rule: exactly these 3 target/escape-pair runs, report hit/no-hit for
each, and stop -- no follow-up parameter sweep regardless of outcome.
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from telegram_matrix_sum_passage_audit import (  # noqa: E402
    DEFAULT_WALKTHROUGH,
    extract_phase_plaintext,
)

OFFSET = 1141
WORDLIST_PATH = (
    SCRIPT_DIR.parents[1] / "wordlists" / "gsmg" / "phase382_1141_offset_candidates.txt"
)

# Fixed reference for the flattened Architect plaintext, so a future edit to
# README.md's Phase 3.2.1 text (or a bug in extract_phase_plaintext) is
# caught rather than silently changing which candidates get tested.
EXPECTED_FLAT_LENGTH = 1539
EXPECTED_FLAT_SHA256 = "90829b510c3697569da47d2817f545f1e2a1cddd78e45f821dafcdab3dc0c281"
EXPECTED_SLICE_AT_OFFSET = "toselectfr"  # flat[1141:1151], cross-checked
# byte-for-byte against Naddiseo/gsmgio-5btc-puzzle's own quoted slice.

TARGET_ESCAPE_RUNS = (
    ("dbbi", "b,e"),
    ("faed", "g,i"),
    ("faed", "h,e"),
)


def flatten_plaintext(walkthrough_path=DEFAULT_WALKTHROUGH):
    text = extract_phase_plaintext(walkthrough_path)
    return re.sub(r"[^A-Za-z]", "", text).lower()


def verify_flat(flat):
    assert len(flat) == EXPECTED_FLAT_LENGTH, (
        f"flattened plaintext length changed: {len(flat)} != {EXPECTED_FLAT_LENGTH}"
    )
    assert hashlib.sha256(flat.encode()).hexdigest() == EXPECTED_FLAT_SHA256, (
        "flattened plaintext content changed since this script was written"
    )
    assert flat[OFFSET:OFFSET + 10] == EXPECTED_SLICE_AT_OFFSET


def build_candidates(flat):
    return [flat[OFFSET:x] for x in range(OFFSET + 1, len(flat) + 1)]


def write_wordlist(candidates, path=WORDLIST_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(candidates) + "\n")
    return path


def run_sweep(wordlist_path, target, escapes, hits_out):
    cmd = [
        sys.executable, str(SCRIPT_DIR / "cosmic_sweep_9ary.py"),
        "--wordlist", str(wordlist_path),
        "--target", target,
        "--escapes", escapes,
        "--hits-out", str(hits_out),
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def self_test():
    flat = flatten_plaintext()
    verify_flat(flat)

    candidates = build_candidates(flat)
    assert len(candidates) == EXPECTED_FLAT_LENGTH - OFFSET == 398
    assert candidates[0] == flat[OFFSET:OFFSET + 1] == "t"
    assert candidates[-1] == flat[OFFSET:]
    assert len(candidates[-1]) == EXPECTED_FLAT_LENGTH - OFFSET
    assert len(set(candidates)) == len(candidates), "candidates must be pairwise distinct"
    # Every candidate is a genuine prefix-extension of the shortest one.
    for c in candidates:
        assert c.startswith(candidates[0])

    assert TARGET_ESCAPE_RUNS == (
        ("dbbi", "b,e"), ("faed", "g,i"), ("faed", "h,e"),
    )

    print("[*] self-test OK: flattened plaintext matches the pinned reference "
          f"({EXPECTED_FLAT_LENGTH} chars, sha256 {EXPECTED_FLAT_SHA256[:12]}...); "
          "398 candidates built, pairwise-distinct, all prefix-extensions of the "
          "shortest; 3 declared target/escape-pair runs confirmed")


def main():
    if "--self-test" in sys.argv:
        self_test()
        return

    flat = flatten_plaintext()
    verify_flat(flat)
    candidates = build_candidates(flat)
    wl_path = write_wordlist(candidates)
    print(f"[*] wrote {len(candidates)} candidates (offset {OFFSET}, closed range) to {wl_path}")

    any_hit = False
    for target, escapes in TARGET_ESCAPE_RUNS:
        hits_out = SCRIPT_DIR / f"phase382_hits_{target}_{escapes.replace(',', '')}.txt"
        hits_out.unlink(missing_ok=True)
        print(f"[*] sweeping target={target} escapes={escapes} ...")
        completed = run_sweep(wl_path, target, escapes, hits_out)
        print(completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else "(no output)")
        if completed.returncode != 0:
            print(completed.stderr[-2000:], file=sys.stderr)
        if hits_out.exists() and hits_out.read_text().strip():
            any_hit = True
            print(f"[+++] HITS recorded in {hits_out}")

    if not any_hit:
        print("[*] negative result -- no candidate in the 1141-offset family "
              "(398 suffix slices of the Architect plaintext starting at "
              "character 1141) opened dbbi or faed under any of the 3 declared "
              "target/escape-pair runs.")


if __name__ == "__main__":
    main()
