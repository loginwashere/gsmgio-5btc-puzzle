#!/usr/bin/env python3
"""Test the capital-letter initials of both textarea headings: `SPI`/`CD`.

User-proposed observation: `SalPhaseIon`'s capital letters are exactly
`S`, `P`, `I` (the same word-boundary capitals Phase 96 already established
as `Sal|Phase|Ion`), and `Cosmic Duality`'s capital letters are `C`, `D`
(trivially, its two words). This is a genuinely new angle on a pair Phase
104's dual-channel audit already confirmed is real (the two textareas,
`SalPhaseIon` before `Cosmic Duality` in DOM order) but never tested via
capitalization-derived initials specifically -- Phase 104 only checked DOM
order, not this.

Broad-light survey of what `SPI`/`CD` could connect to, kept honest about
which parts are solid and which are speculative:

- Structurally, this is just each heading's initials -- true of any
  multi-word capitalized title, so the mechanical fact alone is not
  surprising. What would matter is whether the combined result means
  something on its own.
- Common-usage readings: `SPI` (Serial Peripheral Interface; also a
  homophone of "spy") and `CD` (Compact Disc; also the two-letter element
  symbol Cadmium) don't connect to any independently-established theme in
  this puzzle.
- Elemental-symbol reading (Phase 97's convention, same caution applies as
  Phase 98-99 gave that convention generally): `spi` parses uniquely as
  S+P+I (16+15+53=84); `cd` parses uniquely as the single element Cd
  (48). `84` recurs elsewhere in this project only as Robby's unrelated,
  already-unendorsed `anstoo=1+14+19+20+15+15=84`/"BB84" numerology (see
  Phase 102's provenance survey) -- an independent derivation, not
  corroboration; treated here as coincidental, not connected, absent a
  reason to think otherwise.
- An anagram curiosity, explicitly NOT promoted to a test candidate: `SPICD`
  minus `P` rearranges to `DISC`. This requires dropping a letter with no
  stated reason, which is exactly the kind of unmotivated operation this
  project has repeatedly found to be apophenia -- noted, not tested.
- Checked and DEBUNKED: `github.com/raszi/spicd` (a real repository) is
  "Sony Vaio SPIC control daemon" -- `SPIC` (Sony Programmable I/O
  Controller) + `d` (the standard Unix daemon suffix, as in `sshd`), 2010,
  2 stars. An unrelated coincidental namesake, not a puzzle connection --
  any short pronounceable string is likely to already be someone's project
  name; that alone is not evidence of anything.
- `SPICD` read aloud is one letter short of `SPICED` (a real English word)
  -- `SPICD` is exactly `SPICED` with the interior `E` dropped, which is
  where a reader would naturally supply an epenthetic vowel pronouncing an
  unfamiliar consonant cluster. Tested directly below, same as every other
  cheap candidate in this thread.

Only the direct, unmodified concatenation and the `SPICED` phonetic reading
are tested as passwords, matching this investigation's standing practice of
testing cheap candidates directly rather than debating plausibility
indefinitely.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

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
from salphaseion_title_rebus_audit import EXPECTED_TITLE  # noqa: E402

COSMIC_DUALITY_TITLE = "Cosmic Duality"
EXPECTED_SPI = "SPI"
EXPECTED_CD = "CD"
PHONETIC_READING = "SPICED"


def capital_letters(text):
    return "".join(character for character in text if character.isupper())


def candidate_family(spi, cd):
    joined = spi + cd
    reversed_joined = cd + spi
    return (
        joined,
        joined.lower(),
        f"{spi} {cd}",
        f"{spi} {cd}".lower(),
        f"{spi}-{cd}",
        f"{spi}_{cd}",
        reversed_joined,
        reversed_joined.lower(),
        f"{cd} {spi}",
        f"{cd} {spi}".lower(),
        PHONETIC_READING,
        PHONETIC_READING.lower(),
    )


def audit():
    spi = capital_letters(EXPECTED_TITLE)
    cd = capital_letters(COSMIC_DUALITY_TITLE)
    if spi != EXPECTED_SPI:
        raise AssertionError(f"unexpected SalPhaseIon capitals: {spi!r}")
    if cd != EXPECTED_CD:
        raise AssertionError(f"unexpected Cosmic Duality capitals: {cd!r}")
    candidates = candidate_family(spi, cd)
    joined = spi + cd
    missing = {"e"}
    if PHONETIC_READING.replace("E", "", 1) != joined:
        raise AssertionError(
            "SPICD is no longer exactly SPICED with its single E removed"
        )
    return {
        "spi": spi,
        "cd": cd,
        "candidates": candidates,
        "phonetic_reading": PHONETIC_READING,
        "phonetic_gap": missing,
    }


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


def print_report(report):
    print(f"[*] SalPhaseIon capitals: {report['spi']}")
    print(f"[*] Cosmic Duality capitals: {report['cd']}")
    print(
        f"[*] phonetic reading {report['phonetic_reading']!r}: "
        f"SPICD is exactly SPICED minus {sorted(report['phonetic_gap'])}"
    )
    print("[*] candidates:")
    for candidate in report["candidates"]:
        print(f"    {candidate!r}")


def self_test():
    report = audit()
    assert report["spi"] == "SPI"
    assert report["cd"] == "CD"
    assert "SPICD" in report["candidates"]
    assert "SPI CD" in report["candidates"]
    assert report["phonetic_reading"] == "SPICED"
    assert report["phonetic_gap"] == {"e"}
    assert "SPICED" in report["candidates"]
    print("[*] self-test OK: capital-letter extraction + candidate family + SPICED phonetic reading verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit()
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(report["candidates"], blobs)
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
