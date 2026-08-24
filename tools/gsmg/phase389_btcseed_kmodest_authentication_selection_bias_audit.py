#!/usr/bin/env python3
"""Phase 389: authenticate BTCSEED/KMODEST against the real blobs, and
calibrate Phase 387's KMODEST checkpoint against the full extraction family
it was drawn from rather than against itself alone.

Two independent parts, both declared closed families -- no open-ended
search:

Part 1 -- direct authentication. Tests only the two literal strings this
project has actually derived and mechanically reproduced: `BTCSEED` (Phase
386, the Bifid-decoded FAED output's first 7 characters) and `KMODEST`
(Phase 387, the reproducible second-rail/7x7/reversed-row-1 checkpoint).
Each is tried in its natural uppercase form and a lowercase variant, each
case run through `cb_common.keystr_forms()`'s three established passphrase
forms (literal, single SHA-256 hex, double SHA-256 hex) -- 2 candidates x 2
cases x 3 forms = 12 materials. Each material goes through this project's
full current oracle (CBC with the 24-configuration KDF_VARIANTS +
EXTENDED_CIPHER_VARIANTS set, ECB, the three stream modes, and AES Key Wrap
with/without padding, both IV conventions) against all four tracked blobs
(SALPH, COSMIC, P32TRAILING, URLBLOB) -- the same "current full oracle"
convention `input_byte_pathway_reconstruction_audit.py` (Phase 378) used.

Explicitly EXCLUDED from Part 1, per this project's closed-candidate-
universe discipline: `MODEST`, `BE MODEST` (Phase 387 already marks this
continuation post-hoc, not reproducible, and not promoted), any
concatenation of BTCSEED/KMODEST with each other or with other project
strings, coordinate reinterpretations, BIP39/mnemonic generation from either
word, and any further Bifid-grid variation. None of those is the "sole new
signal" Phase 387/388 actually produced; testing them here would silently
reopen the open-ended search this phase exists to avoid.

Part 2 -- family-wise selection-bias calibration. Phase 387's Monte Carlo
already showed the *specific* fixed extraction (98-char prefix, second
digraph rail, row 1 reversed) scores at or above KMODEST's quadgram score in
only 603/100000 multiset-preserving shuffles. But that fixed extraction was
itself picked, after the fact, from a small family of equally natural
extractions of the same 7x7 geometry: 2 digraph rails (first/second) x the
8 square symmetries (identity, 3 rotations, 2 mirrors, 2 diagonal
reflections) x 7 rows + 7 columns per transformed grid = 224 candidate
strings per decode. "Reverse row 1" is exactly one member of this family
(second rail, horizontal-mirror symmetry, row 0). This part computes, for
every trial, the *maximum* quadgram score across all 224 family members and
compares the real decode's family maximum against that same statistic under
multiset-preserving shuffles -- the correct look-elsewhere-corrected test,
not a re-run of the single-extraction test Phase 387 already reported.
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
from data import DBBI, FAED  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    audit as btcseed_audit,
    bifid_decrypt,
    build_grid,
)
from phase387_btcseed_kmodest_checkpoint_audit import (  # noqa: E402
    TARGET,
    load_quadgrams,
    quadgram_score,
)

CANDIDATES = ("BTCSEED", "KMODEST")
CASES = ("upper", "lower")
FORM_LABELS = ("literal", "sha256_hex", "sha256_hex_hex")

CBC_KDF_VARIANTS = KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS
KEYWRAP_FORMS_PER_CONFIG = 4

ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, CBC_KDF_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, KEYWRAP_FORMS_PER_CONFIG),
)

EXPECTED_MATERIAL_COUNT = len(CANDIDATES) * len(CASES) * len(FORM_LABELS)  # 12


# ---------------------------------------------------------------------------
# Part 1: direct authentication.
# ---------------------------------------------------------------------------

def candidate_materials():
    out = []
    for word in CANDIDATES:
        for case_label in CASES:
            case_form = word.upper() if case_label == "upper" else word.lower()
            for form_label, form_text in zip(FORM_LABELS, keystr_forms(case_form)):
                out.append((word, case_label, form_label, form_text.encode()))
    return out


def run_oracle(blobs=None, families=None):
    active_blobs = BLOBS if blobs is None else blobs
    active_families = ORACLE_FAMILIES if families is None else families
    materials = candidate_materials()

    total_attempts = 0
    hits = []
    for word, case_label, form_label, material in materials:
        for family_name, oracle_fn, variants, forms_per_config in active_families:
            total_attempts += len(variants) * len(active_blobs) * forms_per_config
            if family_name == "keywrap":
                for tag, wrap_kind, kdf_label, key_len, unwrapped in oracle_fn(
                    material, kdf_variants=variants, blobs=active_blobs,
                ):
                    hits.append({
                        "word": word, "case": case_label, "form": form_label,
                        "family": family_name, "blob": tag,
                        "kdf": f"{kdf_label}/aes{key_len * 8}/{wrap_kind}",
                        "plaintext_hex": unwrapped.hex(),
                    })
            else:
                result = oracle_fn(material, kdf_variants=variants, blobs=active_blobs)
                if result:
                    tag, body, kdf_label, key_len = result
                    hits.append({
                        "word": word, "case": case_label, "form": form_label,
                        "family": family_name, "blob": tag,
                        "kdf": f"{kdf_label}/aes{key_len * 8}",
                        "plaintext_hex": body.hex(),
                    })

    return {
        "material_count": len(materials),
        "blobs": tuple(active_blobs),
        "oracle_families": [name for name, _, _, _ in active_families],
        "total_variant_configs": sum(len(v) for _, _, v, _ in active_families),
        "effective_decrypt_attempts": total_attempts,
        "hits": hits,
        "total_hits": len(hits),
    }


# ---------------------------------------------------------------------------
# Part 2: family-wise selection-bias calibration.
# ---------------------------------------------------------------------------

SIDE = 7
LINE_NAMES = tuple(f"row{r}" for r in range(SIDE)) + tuple(f"col{c}" for c in range(SIDE))


def _rot90(g):
    n = len(g)
    return tuple("".join(g[n - 1 - j][i] for j in range(n)) for i in range(n))


def _rot180(g):
    return tuple(row[::-1] for row in g[::-1])


def _rot270(g):
    n = len(g)
    return tuple("".join(g[j][n - 1 - i] for j in range(n)) for i in range(n))


def _flip_h(g):
    return tuple(row[::-1] for row in g)


def _flip_v(g):
    return tuple(g[::-1])


def _transpose(g):
    n = len(g)
    return tuple("".join(g[r][c] for r in range(n)) for c in range(n))


def _anti_transpose(g):
    return _rot180(_transpose(g))


SYMMETRIES = {
    "identity": lambda g: g,
    "rot90": _rot90,
    "rot180": _rot180,
    "rot270": _rot270,
    "flip_h": _flip_h,
    "flip_v": _flip_v,
    "transpose": _transpose,
    "anti_transpose": _anti_transpose,
}


def _grid_lines(g):
    n = len(g)
    rows = list(g)
    cols = ["".join(row[c] for row in g) for c in range(n)]
    return rows + cols


def family_candidates(decoded):
    """(rail, symmetry, line) -> 49-char rail's 7x7 grid, all 8 square
    symmetries, every row and column -- 2 rails x 8 symmetries x 14 lines
    = 224 candidate strings. `reverse row 1` (Phase 387's fixed extraction)
    is exactly (rail='second', symmetry='flip_h', line='row0')."""
    prefix = decoded[:98]
    assert len(prefix) == 98
    rails = {"first": prefix[0::2], "second": prefix[1::2]}
    out = []
    for rail_name, rail in rails.items():
        assert len(rail) == 49
        grid = tuple(rail[i:i + SIDE] for i in range(0, SIDE * SIDE, SIDE))
        for sym_name, sym_fn in SYMMETRIES.items():
            sym_grid = sym_fn(grid)
            for line_name, line in zip(LINE_NAMES, _grid_lines(sym_grid)):
                out.append((rail_name, sym_name, line_name, line))
    return out


def family_max(decoded, logs, floor):
    cands = family_candidates(decoded)
    scored = [(quadgram_score(line, logs, floor), rail, sym, ln, line)
              for rail, sym, ln, line in cands]
    return max(scored, key=lambda t: t[0])


def observed_family_report():
    phase386 = btcseed_audit()
    decoded = phase386["decoded"]
    logs, floor = load_quadgrams()
    cands = family_candidates(decoded)
    target_score = quadgram_score(TARGET, logs, floor)
    target_hits = [(r, s, l) for r, s, l, line in cands if line == TARGET]
    best_score, best_rail, best_sym, best_line, best_text = family_max(decoded, logs, floor)
    return {
        "family_size": len(cands),
        "target_score": target_score,
        "target_hits": target_hits,
        "family_max_score": best_score,
        "family_max_rail": best_rail,
        "family_max_symmetry": best_sym,
        "family_max_line": best_line,
        "family_max_text": best_text,
    }


def family_monte_carlo(trials, seed):
    _keyword, grid, pos = build_grid(DBBI[:13])
    logs, floor = load_quadgrams()
    observed = observed_family_report()
    real_family_max_score = observed["family_max_score"]
    target_score = observed["target_score"]

    rng = random.Random(seed)
    chars = list(FAED)

    family_score_ge = 0
    family_exact = 0
    for _ in range(trials):
        rng.shuffle(chars)
        decoded = bifid_decrypt(chars, pos, grid)
        cands = family_candidates(decoded)
        trial_max_score = max(quadgram_score(line, logs, floor) for *_, line in cands)
        family_score_ge += trial_max_score >= real_family_max_score
        family_exact += any(line == TARGET for *_, line in cands)

    return {
        "trials": trials,
        "seed": seed,
        "target_score": target_score,
        "real_family_max_score": real_family_max_score,
        "family_score_ge_target_family_max": family_score_ge,
        "family_wise_rate": family_score_ge / trials,
        "family_exact": family_exact,
        "family_exact_rate": family_exact / trials,
    }


def audit(trials=100_000, seed=0x389):
    return {
        "oracle": run_oracle(),
        "observed_family": observed_family_report(),
        "family_monte_carlo": family_monte_carlo(trials, seed),
    }


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def self_test():
    materials = candidate_materials()
    assert len(materials) == EXPECTED_MATERIAL_COUNT == 12
    assert {(w, c, f) for w, c, f, _ in materials} == {
        (word, case, form)
        for word in CANDIDATES for case in CASES for form in FORM_LABELS
    }
    # BTCSEED/KMODEST are already all-uppercase as extracted; the lowercase
    # case is the genuinely new form.
    assert dict((w, c) for w, c, _, m in materials if c == "upper" and w == "BTCSEED")
    upper_literal = next(m for w, c, f, m in materials if (w, c, f) == ("BTCSEED", "upper", "literal"))
    assert upper_literal == b"BTCSEED"
    lower_literal = next(m for w, c, f, m in materials if (w, c, f) == ("KMODEST", "lower", "literal"))
    assert lower_literal == b"kmodest"

    oracle_result = run_oracle()
    assert oracle_result["material_count"] == 12
    assert oracle_result["blobs"] == ("SALPH", "COSMIC", "P32TRAILING", "URLBLOB")
    assert oracle_result["total_hits"] == 0, oracle_result["hits"]

    # 8 square symmetries form a closed group: 4 rotations return to start,
    # and every one of the 8 outputs differs on an asymmetric probe grid.
    probe = tuple(f"{r}abcdef" for r in range(7))
    seen = {sym_fn(probe) for sym_fn in SYMMETRIES.values()}
    assert len(seen) == 8, len(seen)
    assert _rot90(_rot90(_rot90(_rot90(probe)))) == probe
    assert _transpose(_transpose(probe)) == probe

    observed = observed_family_report()
    assert observed["family_size"] == 224
    # KMODEST is not unique within the family: the dihedral group has order
    # 8 but only 4 "distinct positions" among the 14 lines of a 7x7 grid are
    # fixed under any nontrivial symmetry pairing for an edge row/column, so
    # the same physical string (row 0 read backward) also appears as
    # rot180's row 6, rot270's col 0, and anti_transpose's col 6.
    assert observed["target_hits"] == [
        ("second", "rot180", "row6"),
        ("second", "rot270", "col0"),
        ("second", "flip_h", "row0"),
        ("second", "anti_transpose", "col6"),
    ], observed["target_hits"]
    # KMODEST is NOT the family maximum: "second"/identity/col0 ("TAKISSU")
    # scores higher under the frozen quadgram table. This is the whole point
    # of the family-wise comparison -- the single "reverse row 1" extraction
    # Phase 387 reported was not even the best-scoring option within its own
    # declared family, which is direct evidence against treating KMODEST's
    # earlier single-extraction Monte Carlo result as free of post-hoc
    # selection.
    assert observed["family_max_line"] != TARGET
    assert observed["family_max_text"] == "TAKISSU"
    assert observed["family_max_rail"] == "second"
    assert observed["family_max_symmetry"] == "identity"
    assert observed["family_max_score"] > observed["target_score"]

    control = family_monte_carlo(trials=200, seed=0x389)
    assert control["trials"] == 200
    assert 0 <= control["family_score_ge_target_family_max"] <= 200
    assert 0 <= control["family_exact"] <= 200
    print(
        "[*] self-test OK: 12 candidate materials, 0 oracle hits against all "
        "4 blobs; among 224 natural row/column/symmetry extractions of both "
        "digraph rails, KMODEST is NOT the family maximum ('TAKISSU' scores "
        "higher) -- direct evidence of post-hoc selection in Phase 387's "
        "single-extraction framing"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=0x389)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(audit(args.trials, args.seed), indent=2))


if __name__ == "__main__":
    main()
