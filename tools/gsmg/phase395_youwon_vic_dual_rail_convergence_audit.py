#!/usr/bin/env python3
"""Phase 395: joint-significance test of Telegram 66722's "two rails, same
index" claim, extending Phase 75's own DBBI-shuffle model.

**Origin:** message `66722` (Vasilis Dragon, 2026-07-13) was already audited
by Phase 387/389, but only its back half (the `KMODEST`/`BE MODEST` Bifid
steps). Its front half claims two *additional*, apparently independent
constructions both land on the same index (21) as Phase 75's already-known
`YOUWON` hit:

1. a "borrow rail" -- the underflow bit of `DBBI - VALIDATION_ANSWER mod 26`
   (1 where `dbbi_i < answer_i`) -- whose only run of length >= 7 in the
   whole 91-bit string starts at 21, spelling byte 127 (`DEL`);
2. a "vic rail" -- 0 for `VALIDATION_ANSWER` characters in `ALPHA_322`'s
   single-digit top row (`FUBCDORA`), 1 otherwise -- whose longest run (9)
   also starts at 21.

Eyeballing "three things point at 21" overstates independence. This audit
checks each claim on its own terms rather than taking the framing at face
value.

**Result 1 -- the borrow rail is not independent evidence.** Phase 75's own
`exact_target_probability()` already computes the exact DBBI values required
for `YOUWON` (offsets 21-26) and for the full `YOUWONX` row (offsets 21-27,
probability 75/111093983, already registered). This audit shows the borrow
bit at each of those 7 offsets is *mathematically entailed* by those already-
required values (`dbbi_i < answer_i` is fully determined once `dbbi_i` is
pinned by the match requirement) -- confirmed by computing forced borrow bits
straight from the required values and asserting they equal the real DBBI's
actual borrow bits. The "run of exactly 7" claim therefore adds only two free
bits beyond Phase 75/Phase 389's own already-registered `YOUWONX` figure: the
boundary bits at offsets 20 and 28 (both 0, confirmed against real `DBBI`),
which stop the run from running longer. It is not a second independent line
converging on 21; it is close to a restatement of one Phase 75 already made,
worth roughly two bits, not a whole new rail.

**Result 2 -- the vic rail is real but far weaker than presented in
isolation, and is calibrated under a different (weaker) null.** Unlike the
borrow rail, the vic rail depends only on `VALIDATION_ANSWER` (already-
authenticated Phase 3.2 plaintext) and `ALPHA_322` (the already-authenticated
Phase 3.2.2 VIC alphabet) -- not on `DBBI` at all. There is no principled
DBBI-shuffle null for it. The only calibration available is to permute
`VALIDATION_ANSWER`'s own 91-character multiset (the same convention Phase
75 applies to `DBBI`) and ask how often the resulting rail's longest run
reaches length >= 9 (this project's own established bar: 100,000 trials,
fixed seed, reused verbatim in Phase 387/389/394). At `VALIDATION_ANSWER`'s
own 64% "wide-codeword" letter density, a run of length >= 9 appears
*somewhere* in 40.8% of shuffles -- unremarkable on its own. Requiring it to
start at the specific, already-famous offset 21 (public since 2024, four
Telegram years before this message) drops that to 0.47% (about 1 in 212) --
real, but nowhere near Phase 75's `YOUWONX` figure, and measured under a
plaintext-shuffle null this project would not normally accept as meaningful
(`VALIDATION_ANSWER` is real, solved, authenticated text, not scrambled
ciphertext-like material -- shuffling it is a calibration convenience, not a
claim that its letters could plausibly have been otherwise).

**Result 3 -- selection.** Offset 21 was not a blind target: `YOUWON` at 21
has been community-known since 2024 (message `23912`; the `YOUWON`
provenance chain Phase 74/75 already trace in full). The vic rail was
constructed and reported *after* that fact was already famous, with no
declared universe of alternative rails that were tried and failed. This is
exactly the look-elsewhere pattern this project's brainstorm-discipline
standard exists to catch, and the 1-in-212 figure above should be read with
that firmly in mind, not as a blind pre-registered hit rate.

**Result 4 -- authentication.** The message's own final synthesis
(`YOUWONBEMODEST`, from `YOUWON` + Phase 387's already-downgraded `BE
MODEST`) and seven case/spacing variants, literal + SHA-256 + double-SHA-256,
are run against all four tracked blobs under the full CBC/ECB/stream/Key
Wrap oracle. Zero hits.

**Disposition:** the "three-way convergence" collapses mostly into Phase
75's own long-registered `YOUWONX` figure (~1 in 1.48 million, already
tested negative for passphrase material) plus one modest, un-pre-registered,
likely post-hoc-searched addition (~1 in 212, vic rail). Neither changes
Phase 75/387/389's verdicts. No registered gap closes; `YOUWON`/`KMODEST`/
`YOUWONBEMODEST` remain closed negative.
"""

import argparse
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    keystr_forms,
)
from data import ALPHA_322, DBBI, VALIDATION_ANSWER  # noqa: E402
from external_archive_lead_audit import runs, subtract_mod26  # noqa: E402
from youwon_partition_audit import (  # noqa: E402
    ROW_TEXT,
    WORD,
    exact_target_probability,
)

SOURCE_MESSAGE_ID = 66722
TOP_ROW = frozenset("FUBCDORA")
MONTE_CARLO_TRIALS = 100_000
MONTE_CARLO_SEED = 0x395

FINAL_CANDIDATES = (
    "YOUWONBEMODEST", "youwonbemodest", "YouWonBeModest",
    "YOU WON - BE MODEST", "YOU WON BE MODEST", "youwon bemodest",
    "YOUWON-BEMODEST", "YOUWONXBEMODEST",
)

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def borrow_bits(dbbi, answer):
    return [
        1 if (ord(d) - ord("a")) < (ord(a) - ord("a")) else 0
        for d, a in zip(dbbi, answer.lower())
    ]


def vic_bits(text):
    return [0 if ch.upper() in TOP_ROW else 1 for ch in text]


def max_run(rail):
    hits = runs(rail, value=1)
    if not hits:
        return 0, None
    start, length = max(hits, key=lambda item: item[1])
    return length, start


def borrow_rail_report():
    rail = borrow_bits(DBBI, VALIDATION_ANSWER)
    long_runs = [r for r in runs(rail, value=1) if r[1] >= 7]

    row_hits = exact_target_probability(ROW_TEXT)
    assert len(row_hits) == 1
    row_start, row_required, row_probability = row_hits[0]
    m91_vals = [ord(c) - ord("a") for c in VALIDATION_ANSWER.lower()]
    forced = [
        1 if row_required[i] < m91_vals[row_start + i] else 0
        for i in range(len(row_required))
    ]
    actual = rail[row_start : row_start + len(row_required)]

    return {
        "rail": "".join(str(b) for b in rail),
        "runs_len_ge7": long_runs,
        "row_start": row_start,
        "row_required_dbbi_values": row_required,
        "row_probability": float(row_probability),
        "forced_borrow_from_row_requirement": forced,
        "actual_borrow_at_row": actual,
        "forced_matches_actual": forced == actual,
        "boundary_before": rail[row_start - 1],
        "boundary_after": rail[row_start + len(row_required)],
    }


def vic_rail_report():
    rail = vic_bits(VALIDATION_ANSWER)
    density = sum(rail) / len(rail)
    all_runs = sorted(runs(rail, value=1), key=lambda r: -r[1])
    length, start = max_run(rail)

    rng = random.Random(MONTE_CARLO_SEED)
    letters = list(VALIDATION_ANSWER)
    ge_len_anywhere = 0
    ge_len_at_start = 0
    for _ in range(MONTE_CARLO_TRIALS):
        rng.shuffle(letters)
        shuffled_bits = vic_bits("".join(letters))
        trial_length, trial_start = max_run(shuffled_bits)
        if trial_length >= length:
            ge_len_anywhere += 1
            if trial_start == start:
                ge_len_at_start += 1

    return {
        "rail": "".join(str(b) for b in rail),
        "density": density,
        "all_runs_sorted": all_runs,
        "max_run_length": length,
        "max_run_start": start,
        "second_longest": all_runs[1][1] if len(all_runs) > 1 else 0,
        "trials": MONTE_CARLO_TRIALS,
        "p_len_ge_anywhere": ge_len_anywhere / MONTE_CARLO_TRIALS,
        "p_len_ge_at_start": ge_len_at_start / MONTE_CARLO_TRIALS,
    }


def final_candidate_oracle_report():
    hits = []
    attempts = 0
    materials_tried = 0
    for root in FINAL_CANDIDATES:
        for form_name, material in zip(
            ("literal", "sha256_hex", "sha256_hex_hex"), keystr_forms(root)
        ):
            materials_tried += 1
            material_bytes = material.encode("utf-8")
            for family_name, oracle, variants, forms_per_config in ORACLE_FAMILIES:
                attempts += len(variants) * len(BLOBS) * forms_per_config
                if family_name == "keywrap":
                    for tag, wrap_kind, kdf_label, key_len, plaintext in oracle(
                        material_bytes, kdf_variants=variants, blobs=BLOBS
                    ):
                        hits.append(
                            (root, form_name, family_name, tag, wrap_kind, kdf_label, key_len, plaintext.hex())
                        )
                else:
                    result = oracle(material_bytes, kdf_variants=variants, blobs=BLOBS)
                    if result:
                        tag, plaintext, kdf_label, key_len = result
                        hits.append((root, form_name, family_name, tag, "", kdf_label, key_len, plaintext.hex()))

    return {
        "materials_tried": materials_tried,
        "effective_attempts": attempts,
        "hits": hits,
        "total_hits": len(hits),
    }


def audit(run_oracle=True):
    subtraction = subtract_mod26(DBBI, VALIDATION_ANSWER)
    assert subtraction.index(WORD) == 21

    report = {
        "source_message_id": SOURCE_MESSAGE_ID,
        "subtraction_output": subtraction,
        "borrow_rail": borrow_rail_report(),
        "vic_rail": vic_rail_report(),
    }
    if run_oracle:
        report["final_candidate_oracle"] = final_candidate_oracle_report()
    return report


def self_test(run_oracle=False):
    report = audit(run_oracle=run_oracle)

    borrow = report["borrow_rail"]
    assert borrow["runs_len_ge7"] == [(21, 7)]
    assert borrow["row_start"] == 21
    assert abs(borrow["row_probability"] - 6.751040693175975e-07) < 1e-15
    assert borrow["forced_matches_actual"] is True
    assert borrow["forced_borrow_from_row_requirement"] == [1, 1, 1, 1, 1, 1, 1]
    assert borrow["boundary_before"] == 0
    assert borrow["boundary_after"] == 0

    vic = report["vic_rail"]
    assert abs(vic["density"] - 0.6373626373626373) < 1e-12
    assert vic["max_run_length"] == 9
    assert vic["max_run_start"] == 21
    assert vic["second_longest"] == 6
    assert vic["trials"] == MONTE_CARLO_TRIALS
    assert 0.35 < vic["p_len_ge_anywhere"] < 0.46
    assert 0.001 < vic["p_len_ge_at_start"] < 0.02

    if run_oracle:
        final = report["final_candidate_oracle"]
        assert final["materials_tried"] == 24
        assert final["effective_attempts"] == 11520
        assert final["total_hits"] == 0

    print(
        f"[*] self-test OK: Telegram {SOURCE_MESSAGE_ID}'s borrow-rail run of 7 "
        f"at offset 21 is mathematically forced by Phase 75's own already-"
        f"registered YOUWONX row requirement (p={borrow['row_probability']:.3e}) "
        f"-- confirmed identical to the real DBBI's actual borrow bits, adding "
        f"only 2 free boundary bits; the vic-rail's length-9 run at offset 21 "
        f"is real but unremarkable in isolation (length>=9 anywhere in "
        f"{vic['p_len_ge_anywhere']:.1%} of {vic['trials']:,} answer-letter "
        f"shuffles) and only ~1-in-"
        f"{1/vic['p_len_ge_at_start']:.0f} to land at the specific, already-"
        f"community-famous offset 21; {report.get('final_candidate_oracle', {}).get('effective_attempts', 'skipped')} "
        f"effective decrypt attempts against YOUWONBEMODEST and 7 variants -- "
        f"{report.get('final_candidate_oracle', {}).get('total_hits', 'n/a')} hits"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skip-oracle", action="store_true")
    args = parser.parse_args()
    report = (
        self_test(run_oracle=not args.skip_oracle)
        if args.self_test
        else audit(run_oracle=not args.skip_oracle)
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
