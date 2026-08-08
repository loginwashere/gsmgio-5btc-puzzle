#!/usr/bin/env python3
"""Path 3 from the 2026-07-24 "Best Remaining Paths" review: exact
command-provenance reconstruction, narrowed to a cheap, bounded form after
review found the open-ended version ("recover the exact command byte-for-
byte") has no principled stopping point unless a verbatim source already
exists to recover it FROM.

`wordlists/gsmg/last_command.txt` is a NORMALIZED approximation (spaces,
dashes, quoting all stripped -- confirmed by inspection). But
`wordlists/gsmg/chat_mined_lines.txt` is the raw, unnormalized mined chat
archive -- if a real command was ever typed verbatim by a community member,
it should already be sitting in there byte-for-byte. So instead of inventing
command reconstructions, this greps that raw archive for real
`openssl enc ... pass:X` invocations and real `echo ... | sha256sum`-style
hash pipelines, extracts their EXACT literal arguments (preserving whatever
quoting/spacing/typos the original poster actually used -- including at
least one real missing-dash typo, see COMMAND_LINES below), and tests them
against every open/default blob (cb_common.BLOBS, now four -- see below) under the
full cipher/KDF coverage (KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS from
path 1).

This also recovered something not previously known to this project: a
`U2FsdGVkX186tYU0hVJBXXUnBUO7C0+X4KUWnWkC...` fragment posted in chat is
byte-for-byte a real prefix of this project's actual SALPHASEION_BLOB_B64
(verified in cb_common.BLOBS) -- meaning the passwords two community members
posted alongside it were genuine historical attempts against the REAL SALPH
ciphertext, not a fabricated example. Both were reported in the same chat
thread as producing a "bad decrypt" / padding error under AES-256-CBC
specifically -- worth retesting under the broadened cipher/KDF set in case
the password was right and only the cipher assumption was wrong, but not
expected to newly succeed since the errors were reported for the base64
content itself (a missing trailing "z" separator), not just the password.

Follow-up (2026-07-24): a DIFFERENT base64 fragment repeated dozens of times
throughout the same chat archive (also seen in this thread) was triaged
separately and its GSMG provenance independently confirmed via the official
community repo (puzzlehunt/gsmgio-5btc-puzzle README) and an actively-
maintained fork's detailed documentation (HosterjackAGV/gsmg-5btc-puzzle,
where it's called "p32_trailing" -- an 80-byte OpenSSL blob embedded at the
end of the already-solved Phase 3.2 plaintext, genuinely distinct from SALPH/
COSMIC by salt). Added to cb_common.BLOBS as "P32TRAILING" -- see
data.P32_TRAILING_BLOB_B64. Every sweep in this module now runs against all
four open/default blobs automatically.

Usage:
    python3 tools/gsmg/command_provenance_recheck.py
    python3 tools/gsmg/command_provenance_recheck.py --self-test
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import BLOBS, EXTENDED_CIPHER_VARIANTS, KDF_VARIANTS, aes_try_open  # noqa: E402

ALL_VARIANTS = list(KDF_VARIANTS) + list(EXTENDED_CIPHER_VARIANTS)

# Every real `pass:VALUE` literal found by `grep -inE "pass:" chat_mined_lines.txt`
# (26 lines total -- small enough to hand-triage), excluding: generic
# placeholders ("pass: xxxxxx", "pass:$pass", "pass:$2"), visibly truncated
# scrollback ("pass: edaa8bc3853e1f941ec479f2ad.....", 19-hex-char fragment
# "f34b72e14fb250dbed"), and the already-solved Phase 3.2 password
# (sha256("causality"), which this project already has as PHASE32_PASSWORD).
# Source line numbers refer to chat_mined_lines.txt as of 2026-07-24.
COMMAND_PASS_LITERALS = {
    # line 23004: real chat suggestion to ENCRYPT cosmic_duality.txt with
    # -des3 (3DES) using this password -- worth testing as a decrypt password
    # against COSMIC under 3DES regardless of the encrypt/decrypt direction
    # framing, since a symmetric cipher's key recovers either direction.
    "864c9a220f7b99db99cc3c28f9bde60991f041411b98d83de0338602a95b346d": "3des-cosmic-suggestion",
    # lines 36718/36721/36983/36986: real historical decrypt attempts
    # against a chat-posted fragment independently confirmed to be a byte-
    # for-byte prefix of the real SALPHASEION_BLOB_B64 -- see module
    # docstring. Chat itself reports these as bad-decrypt/padding errors
    # under AES-256-CBC; retested here under the full cipher/KDF set.
    "93de0175aa3d0a6a2768ba650009a35a36530fa31898da6f3c46757a693f108f": "salph-attempt",
    "e24bd2c0fd454632f9fdd26cbdc210597f79e9fca9719c126a6d30cb41ef0238": "salph-attempt",
    "baff7ec4a1686de56f065d9c72a557eec5977a94c155a18dd78ee833e0ab6f9b": "salph-attempt",
    # lines 27554/27557: literal keyword guesses.
    "SalPhaseIon": "literal-keyword",
    "salphaseion": "literal-keyword",
    # line 61201: explicit concatenated-keyword guess with an explicit
    # non-default `-md md5` KDF digest, targeting a file literally named
    # "salph.aes" -- genuinely untested combination (keyword content +
    # non-default digest) as far as this project's history shows.
    "matrixsumlistenterlastwordsbeforearchichoicethispasswordmatrixsumlist": "salph-md5-guess",
    # line 59313: thematic ("Matrix") guess against an unlabeled
    # "zion_blob.txt" -- untested against our real blobs specifically.
    "ZION": "thematic-guess",
    # line 53253: sha256(' ') demo value -- cheap to include even though the
    # surrounding context is a general padding illustration, not a real
    # attempt against our targets.
    hashlib.sha256(b" ").hexdigest(): "sha256-of-space",
}

# line 14285: `echo theflowerblossoms | sha256sum` -- no `-n` flag, so the
# real hash input includes a trailing newline. "theflowerblossoms" (short
# form, without the "throughwhatseemstobeaconcretesurface" suffix used
# elsewhere) tested here in both its raw and hashed forms, with and without
# the trailing newline the exact command implies -- the nuance this path is
# specifically about (byte-for-byte command semantics, not a normalized
# guess).
ECHO_SHA_CANDIDATES = ["theflowerblossoms"]


def build_candidates():
    """Every literal to test, exactly as it would reach the passphrase
    argument for real -- no answer_forms()-style case/punctuation
    normalization, since that would defeat the point of testing what was
    actually typed."""
    out = dict(COMMAND_PASS_LITERALS)
    for word in ECHO_SHA_CANDIDATES:
        out[word] = "echo-sha-raw"
        out[word + "\n"] = "echo-sha-raw-with-newline"
        out[hashlib.sha256(word.encode()).hexdigest()] = "echo-sha-hashed"
        out[hashlib.sha256((word + "\n").encode()).hexdigest()] = "echo-sha-hashed-with-newline"
    return out


def sweep(candidates):
    hits = []
    for literal, source in candidates.items():
        result = aes_try_open(literal, kdf_variants=ALL_VARIANTS)
        if result:
            tag, body, kdf_label, key_len = result
            hits.append({
                "literal": literal,
                "source": source,
                "blob": tag,
                "kdf": kdf_label,
                "key_bits": key_len * 8,
                "plaintext": body[:500],
            })
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    candidates = build_candidates()

    if args.self_test:
        assert len(candidates) >= 12, (
            f"self-test FAILED: expected >=12 candidates, got {len(candidates)}"
        )
        assert "ZION" in candidates, "self-test FAILED: expected literal 'ZION' missing"
        hits = sweep({"ZION": candidates["ZION"]})
        print(f"[*] self-test OK ({len(candidates)} total candidates, "
              f"1-candidate probe ran cleanly, {len(hits)} hits)")
        return

    print(f"[*] {len(candidates)} real chat-mined command-provenance candidates "
          f"x {len(ALL_VARIANTS)} cipher/KDF variants x {len(BLOBS)} blobs "
          f"({', '.join(BLOBS)})")
    hits = sweep(candidates)
    if not hits:
        print("[*] no candidate opened any blob")
        return
    for hit in hits:
        print(f"\n[+++ HIT] literal={hit['literal']!r} source={hit['source']} "
              f"blob={hit['blob']} kdf={hit['kdf']}/{hit['key_bits']}bit")
        print(f"    plaintext: {hit['plaintext']!r}")


if __name__ == "__main__":
    main()
