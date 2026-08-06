"""Digraphic-cipher-over-the-25-code-alphabet path
(doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md, item #3), run after the checkerboard
recovery calibration (see FINDINGS.md Phase 20) corroborated that plain
monoalphabetic substitution under `{b,e}`/`build_board_9ary` is very unlikely to
be dbbi's construction. Existing checkerboard solvers assume each complete code
maps independently to one plaintext letter; this tests whether a second
digraphic layer -- Playfair, Two-square, Four-square, or Bifid, the four
standard 5x5-square families -- was applied over the 25-code alphabet, which
would explain why monoalphabetic quadgram hill-climbing fails even if the
checkerboard segmentation itself is correct.

Kept deliberately bounded, per the doc's explicit instruction to stop after
these four families and a small clue-motivated keyword set (not a general
dictionary-keyed Playfair sweep, which would repeat the already-saturated
keyword problem):

- escape pairs: only `{b,e}` (both orders) for dbbi, `{g,i}`/`{h,e}` (both
  orders) for faed -- the same TARGET_ESCAPES convention already established
  in matrixsum_permutation_sweep.py / dual_quinary_sweep.py.
- keys: CORE_KEYWORDS below -- the same clue-motivated seed list used
  elsewhere in this project, plus "matrix" and "duality" (the two words the
  doc calls out by name as this path's own motivation) and the one verified,
  already-confirmed-genuine screenplay extraction (the Phase 2/3 URL slug,
  itself a real Merovingian/Matrix Reloaded quote -- see doc/GSMG_PUZZLE.md).
- topology fixed to `top_first` (the one validated 3.2.2 layout) -- not swept.
- standard pair ciphers require an even number of ciphertext symbols. Odd
  segmented streams are therefore not repaired by injecting a ciphertext
  filler: that would not model plaintext padding, because both decrypted
  letters depend on both ciphertext letters. Playfair/Two-square/Four-square
  are skipped for odd streams; Bifid remains valid at any length.
- Bifid periods: 5, 7, 9, 13, and the full message. Period 5 is the common
  5x5-square default; 7/9/13 are the bounded clue/matrix dimensions already
  motivated elsewhere in this investigation.
- Two-square: horizontal and vertical square orientations, each with both
  same-line conventions (identity vs. rectangle transform).

Each candidate decode is scored with quadgram_solver.score() (the same metric
this project's other checkerboard work uses). End-to-end synthetic controls
exercise every family before real results are trusted, and a shuffle/null gate
(the same max-statistic permutation-test pattern already established in
dual_quinary_sweep.py: shuffle each escape hypothesis's own COMPLETE-CODE
multiset, not raw symbols) is required before any output is promoted to AES.
"""
import argparse
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import aes_try_open, build_board_9ary, keystr_forms, pad25
from data import DBBI, FAED, VALIDATION_ANSWER
from quadgram_solver import score as quadgram_score

CORE_KEYWORDS = (
    "matrixsumlist", "lastwordsbeforearchichoice", "thispassword", "yinyang",
    "cosmicduality", "salphaseion", "causality", "architect", "choice",
    "enter", VALIDATION_ANSWER, "matrix", "duality",
    "choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecial"
    "dessertiwroteitmyself",
)
TARGET_ESCAPES = {
    "dbbi": [("b", "e"), ("e", "b")],
    "faed": [("g", "i"), ("i", "g"), ("h", "e"), ("e", "h")],
}
TARGETS = {"dbbi": DBBI, "faed": FAED}
TOPOLOGY = "top_first"
BIFID_PERIODS = (5, 7, 9, 13, None)
TWO_SQUARE_MODES = (
    ("horizontal", False),
    ("horizontal", True),
    ("vertical", False),
    ("vertical", True),
)

PLAIN_ALPHABET25 = pad25("")  # standard, unkeyed order -- the two "plain" squares
# in a classic four-square cipher.
PLAIN_POS = {c: divmod(i, 5) for i, c in enumerate(PLAIN_ALPHABET25)}


def segment_codes(s, e1, e2):
    """Returns the list of complete codes, or None on a dangling trailing
    escape (matches the established, previously-bug-fixed convention -- never
    silently truncate)."""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in (e1, e2):
            if i + 1 >= n:
                return None
            out.append(s[i:i + 2])
            i += 2
        else:
            out.append(c)
            i += 1
    return out


def build_square(keyword, e1, e2, topology=TOPOLOGY):
    alphabet25 = pad25(keyword)
    board = build_board_9ary(alphabet25, e1, e2, topology)  # code -> letter
    grid_pos = {letter: divmod(i, 5) for i, letter in enumerate(alphabet25)}
    return alphabet25, board, grid_pos


def codes_to_letters(codes, board):
    return "".join(board.get(c, "?") for c in codes)


def make_pairs(letters):
    if len(letters) % 2:
        return None
    return [(letters[i], letters[i + 1]) for i in range(0, len(letters), 2)]


def assemble(decrypted_pairs):
    return "".join(ch for pair in decrypted_pairs for ch in pair)


def playfair_decrypt_pair(l1, l2, alphabet25, grid_pos):
    r1, c1 = grid_pos[l1]
    r2, c2 = grid_pos[l2]
    if r1 == r2:
        return alphabet25[r1 * 5 + (c1 - 1) % 5], alphabet25[r2 * 5 + (c2 - 1) % 5]
    if c1 == c2:
        return alphabet25[((r1 - 1) % 5) * 5 + c1], alphabet25[((r2 - 1) % 5) * 5 + c2]
    return alphabet25[r1 * 5 + c2], alphabet25[r2 * 5 + c1]


def two_square_decrypt_pair(
        l1, l2, alphaA, posA, alphaB, posB,
        orientation="horizontal", same_line_identity=False):
    r1, c1 = posA[l1]
    r2, c2 = posB[l2]
    if orientation == "horizontal":
        if same_line_identity and r1 == r2:
            return l1, l2
        return alphaA[r1 * 5 + c2], alphaB[r2 * 5 + c1]
    if orientation == "vertical":
        if same_line_identity and c1 == c2:
            return l1, l2
        return alphaA[r2 * 5 + c1], alphaB[r1 * 5 + c2]
    raise ValueError(f"unknown Two-square orientation: {orientation!r}")


def four_square_decrypt_pair(l1, l2, keyA_alpha, posA, keyB_alpha, posB):
    r1, c2 = posA[l1]
    r2, c1 = posB[l2]
    return PLAIN_ALPHABET25[r1 * 5 + c1], PLAIN_ALPHABET25[r2 * 5 + c2]


def _bifid_decrypt_block(letters, alphabet25, grid_pos):
    n = len(letters)
    interleaved = []
    for ch in letters:
        r, c = grid_pos[ch]
        interleaved.append(r)
        interleaved.append(c)
    orig_rows, orig_cols = interleaved[:n], interleaved[n:]
    return "".join(alphabet25[orig_rows[i] * 5 + orig_cols[i]] for i in range(n))


def bifid_decrypt(letters, alphabet25, grid_pos, period=None):
    block_size = len(letters) if period is None else period
    return "".join(
        _bifid_decrypt_block(letters[i:i + block_size], alphabet25, grid_pos)
        for i in range(0, len(letters), block_size)
    )


def sweep_codes(codes, e1, e2, keywords=CORE_KEYWORDS):
    """Runs the full bounded family x keyword x alignment sweep against one
    already-segmented code list (real or shuffled). Returns a list of
    (family, params, candidate_text) tuples."""
    out = []
    for keyword in keywords:
        alphabet25, board, grid_pos = build_square(keyword, e1, e2)
        letters = codes_to_letters(codes, board)

        pairs = make_pairs(letters)
        if pairs is not None:
            decrypted = [playfair_decrypt_pair(l1, l2, alphabet25, grid_pos)
                         for l1, l2 in pairs]
            out.append(("playfair", (keyword,), assemble(decrypted)))

        for period in BIFID_PERIODS:
            out.append(("bifid", (keyword, period),
                        bifid_decrypt(letters, alphabet25, grid_pos, period)))

    if len(codes) % 2 == 0:
        for kwA in keywords:
            alphaA, boardA, posA = build_square(kwA, e1, e2)
            lettersA = codes_to_letters(codes, boardA)
            pairsA = make_pairs(lettersA)
            for kwB in keywords:
                alphaB, boardB, posB = build_square(kwB, e1, e2)
                lettersB = codes_to_letters(codes, boardB)
                pairsB = make_pairs(lettersB)
                paired_halves = [(a[0], b[1]) for a, b in zip(pairsA, pairsB)]

                for orientation, same_line_identity in TWO_SQUARE_MODES:
                    decrypted = [
                        two_square_decrypt_pair(
                            l1, l2, alphaA, posA, alphaB, posB,
                            orientation, same_line_identity)
                        for l1, l2 in paired_halves
                    ]
                    out.append((
                        "two_square",
                        (kwA, kwB, orientation, same_line_identity),
                        assemble(decrypted),
                    ))

                decrypted4 = [
                    four_square_decrypt_pair(l1, l2, alphaA, posA, alphaB, posB)
                    for l1, l2 in paired_halves
                ]
                out.append(("four_square", (kwA, kwB), assemble(decrypted4)))
    return out


def sweep_target(target_name, ciphertext, keywords=CORE_KEYWORDS):
    all_candidates = []
    for e1, e2 in TARGET_ESCAPES[target_name]:
        codes = segment_codes(ciphertext, e1, e2)
        if codes is None:
            continue
        for family, params, text in sweep_codes(codes, e1, e2, keywords):
            all_candidates.append((family, (e1, e2) + params, text, quadgram_score(text)))
    return all_candidates


def top_signal_stat(target_name, ciphertext, keywords=CORE_KEYWORDS):
    candidates = sweep_target(target_name, ciphertext, keywords)
    return max(c[3] for c in candidates) if candidates else -1e18


def _trial_best(args):
    pair_codes, trial_seed, keywords = args
    rng = random.Random(trial_seed)
    best = -1e18
    for e1, e2, codes in pair_codes:
        shuffled = list(codes)
        rng.shuffle(shuffled)
        for family, params, text in sweep_codes(shuffled, e1, e2, keywords):
            best = max(best, quadgram_score(text))
    return best


def permutation_gate(pair_codes, real_best, trials, seed=0, workers=1,
                     keywords=CORE_KEYWORDS):
    rng = random.Random(seed)
    trial_args = [
        (pair_codes, rng.getrandbits(64), keywords)
        for _ in range(trials)
    ]
    trial_start = time.time()
    if workers == 1:
        null_bests = [_trial_best(args) for args in trial_args]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            null_bests = list(ex.map(
                _trial_best,
                trial_args,
                chunksize=max(1, trials // (workers * 8)),
            ))
    trial_elapsed = time.time() - trial_start
    at_least_as_good = sum(value >= real_best for value in null_bests)
    return {
        "trials": trials,
        "at_least_as_good": at_least_as_good,
        "p_value": (at_least_as_good + 1) / (trials + 1),
        "null_mean": sum(null_bests) / len(null_bests),
        "null_max": max(null_bests),
        "trial_elapsed_s": trial_elapsed,
        "per_trial_s": trial_elapsed / trials,
    }


def shuffle_gate(target_name, ciphertext, trials, seed=0, workers=1):
    """Shuffles each motivated escape hypothesis's own COMPLETE-CODE multiset
    (not raw a-i symbols -- the established fix for the bug class found
    earlier this project in dual_quinary_sweep.py) and reruns the identical
    bounded sweep on the shuffled codes, `trials` times. The empirical p-value
    compares each shuffle's own max-statistic (same structure as the real
    computation) against the real ciphertext's max -- a genuine family-wise
    permutation test, no separate Bonferroni correction needed."""
    start = time.time()
    real_best = top_signal_stat(target_name, ciphertext)
    real_elapsed = time.time() - start

    pair_codes = []
    for e1, e2 in TARGET_ESCAPES[target_name]:
        codes = segment_codes(ciphertext, e1, e2)
        if codes is not None:
            pair_codes.append((e1, e2, tuple(codes)))

    gate = permutation_gate(pair_codes, real_best, trials, seed, workers)
    return {
        "target": target_name,
        "real_best": real_best,
        "real_elapsed_s": real_elapsed,
        **gate,
    }


def playfair_encrypt_pair(l1, l2, alphabet25, grid_pos):
    r1, c1 = grid_pos[l1]
    r2, c2 = grid_pos[l2]
    if r1 == r2:
        return alphabet25[r1 * 5 + (c1 + 1) % 5], alphabet25[r2 * 5 + (c2 + 1) % 5]
    if c1 == c2:
        return alphabet25[((r1 + 1) % 5) * 5 + c1], alphabet25[((r2 + 1) % 5) * 5 + c2]
    return alphabet25[r1 * 5 + c2], alphabet25[r2 * 5 + c1]


def four_square_encrypt_pair(l1, l2, keyA_alpha, keyB_alpha):
    r1, c1 = PLAIN_POS[l1]
    r2, c2 = PLAIN_POS[l2]
    return keyA_alpha[r1 * 5 + c2], keyB_alpha[r2 * 5 + c1]


def _bifid_encrypt_block(letters, alphabet25, grid_pos):
    coords = [grid_pos[ch] for ch in letters]
    flat = [r for r, _ in coords] + [c for _, c in coords]
    return "".join(
        alphabet25[flat[2 * i] * 5 + flat[2 * i + 1]]
        for i in range(len(letters))
    )


def bifid_encrypt(letters, alphabet25, grid_pos, period=None):
    block_size = len(letters) if period is None else period
    return "".join(
        _bifid_encrypt_block(letters[i:i + block_size], alphabet25, grid_pos)
        for i in range(0, len(letters), block_size)
    )


def letters_to_codes(letters, board):
    inverse = {letter: code for code, letter in board.items()}
    return [inverse[letter] for letter in letters]


def paired_letters_to_codes(letters, boardA, boardB):
    inverseA = {letter: code for code, letter in boardA.items()}
    inverseB = {letter: code for code, letter in boardB.items()}
    return [
        (inverseA if index % 2 == 0 else inverseB)[letter]
        for index, letter in enumerate(letters)
    ]


def synthetic_plaintext(length, offset=0):
    path = SCRIPT_DIR.parent.parent / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
    letters = "".join(ch for ch in path.read_text(errors="ignore").upper() if ch.isalpha())
    letters = letters.replace("J", "I")
    if len(letters) < offset + length:
        raise RuntimeError(
            f"synthetic corpus has only {len(letters)} letters, "
            f"need offset={offset} + length={length}")
    return letters[offset:offset + length]


def prepare_playfair_plaintext(letters, output_length):
    prepared = []
    index = 0
    while len(prepared) < output_length:
        first = letters[index]
        if index + 1 >= len(letters):
            second = "X" if first != "X" else "Q"
            index += 1
        elif letters[index + 1] == first:
            second = "X" if first != "X" else "Q"
            index += 1
        else:
            second = letters[index + 1]
            index += 2
        prepared.extend((first, second))
    return "".join(prepared[:output_length])


def build_synthetic_control(family):
    target_name = "dbbi" if family == "bifid" else "faed"
    e1, e2 = TARGET_ESCAPES[target_name][0]
    keywordA, keywordB = "matrix", "duality"
    alphaA, boardA, posA = build_square(keywordA, e1, e2)
    alphaB, boardB, posB = build_square(keywordB, e1, e2)
    length = 63 if family == "bifid" else 436
    for offset in range(1000):
        if family == "playfair":
            source = synthetic_plaintext(length * 2, offset)
            plaintext = prepare_playfair_plaintext(source, length)
            encrypted_pairs = [
                playfair_encrypt_pair(l1, l2, alphaA, posA)
                for l1, l2 in make_pairs(plaintext)
            ]
            ciphertext_letters = assemble(encrypted_pairs)
            codes = letters_to_codes(ciphertext_letters, boardA)
            expected_params = (keywordA,)
        elif family == "two_square":
            plaintext = synthetic_plaintext(length, offset)
            orientation, same_line_identity = "horizontal", True
            encrypted_pairs = [
                two_square_decrypt_pair(
                    l1, l2, alphaA, posA, alphaB, posB,
                    orientation, same_line_identity)
                for l1, l2 in make_pairs(plaintext)
            ]
            ciphertext_letters = assemble(encrypted_pairs)
            codes = paired_letters_to_codes(ciphertext_letters, boardA, boardB)
            expected_params = (keywordA, keywordB, orientation, same_line_identity)
        elif family == "four_square":
            plaintext = synthetic_plaintext(length, offset)
            encrypted_pairs = [
                four_square_encrypt_pair(l1, l2, alphaA, alphaB)
                for l1, l2 in make_pairs(plaintext)
            ]
            ciphertext_letters = assemble(encrypted_pairs)
            codes = paired_letters_to_codes(ciphertext_letters, boardA, boardB)
            expected_params = (keywordA, keywordB)
        elif family == "bifid":
            plaintext = synthetic_plaintext(length, offset)
            period = 5
            ciphertext_letters = bifid_encrypt(plaintext, alphaA, posA, period)
            codes = letters_to_codes(ciphertext_letters, boardA)
            expected_params = (keywordA, period)
        else:
            raise ValueError(f"unknown synthetic family: {family!r}")
        ciphertext = "".join(codes)
        if all(
                segment_codes(ciphertext, pair_e1, pair_e2) is not None
                for pair_e1, pair_e2 in TARGET_ESCAPES[target_name]):
            break
    else:
        raise RuntimeError(
            f"could not build an all-escape-valid synthetic {family} control")

    return {
        "family": family,
        "params": expected_params,
        "plaintext": plaintext,
        "codes": codes,
        "ciphertext": ciphertext,
        "target_name": target_name,
        "e1": e1,
        "e2": e2,
    }


def run_synthetic_calibration(trials=500, seed=20260724, workers=16):
    results = []
    for index, family in enumerate(("playfair", "two_square", "four_square", "bifid")):
        control = build_synthetic_control(family)
        candidates = []
        pair_codes = []
        for e1, e2 in TARGET_ESCAPES[control["target_name"]]:
            codes = segment_codes(control["ciphertext"], e1, e2)
            if codes is None:
                continue
            pair_codes.append((e1, e2, tuple(codes)))
            for candidate_family, params, text in sweep_codes(
                    codes, e1, e2, CORE_KEYWORDS):
                candidates.append((candidate_family, (e1, e2) + params, text))
        matches = [
            text for candidate_family, params, text in candidates
            if candidate_family == family
            and params == (control["e1"], control["e2"]) + control["params"]
        ]
        assert matches == [control["plaintext"]], (
            f"{family} end-to-end control did not recover its plaintext")
        real_best = max(quadgram_score(text) for _, _, text in candidates)
        truth_score = quadgram_score(control["plaintext"])
        assert real_best == truth_score, (
            f"{family} control plaintext was recovered but did not rank first: "
            f"truth={truth_score}, best={real_best}")
        gate = permutation_gate(
            pair_codes,
            real_best,
            trials,
            seed + index,
            workers,
        )
        result = {
            "family": family,
            "length": len(control["codes"]),
            "escape_hypotheses": len(pair_codes),
            "truth_score": truth_score,
            "real_best": real_best,
            **gate,
        }
        results.append(result)
        print(
            f"{family:11s} length={result['length']:3d} "
            f"escapes={result['escape_hypotheses']} "
            f"truth={truth_score:8.1f} best={real_best:8.1f} "
            f"null_mean={gate['null_mean']:8.1f} p={gate['p_value']:.5f}"
        )
    return results


def run_self_tests():
    # Playfair decrypt is the inverse of the standard encrypt rule.
    alphabet25 = pad25("PLAYFAIREXAMPLE")
    grid_pos = {letter: divmod(i, 5) for i, letter in enumerate(alphabet25)}

    for l1, l2 in [("H", "I"), ("D", "A"), ("N", "V")]:
        c1, c2 = playfair_encrypt_pair(l1, l2, alphabet25, grid_pos)
        d1, d2 = playfair_decrypt_pair(c1, c2, alphabet25, grid_pos)
        assert (d1, d2) == (l1, l2), f"playfair round-trip failed: {l1}{l2} -> {c1}{c2} -> {d1}{d2}"

    plaintext = "ATTACKATDAWN"
    for period in BIFID_PERIODS:
        ct = bifid_encrypt(plaintext, alphabet25, grid_pos, period)
        pt_back = bifid_decrypt(ct, alphabet25, grid_pos, period)
        assert pt_back == plaintext, (
            f"bifid round-trip failed at period={period}: "
            f"{plaintext} -> {ct} -> {pt_back}")

    alphaB = pad25("SECOND SQUARE")
    posB = {letter: divmod(i, 5) for i, letter in enumerate(alphaB)}
    for orientation, same_line_identity in TWO_SQUARE_MODES:
        for l1, l2 in [("H", "I"), ("D", "A"), ("N", "V")]:
            c1, c2 = two_square_decrypt_pair(
                l1, l2, alphabet25, grid_pos, alphaB, posB,
                orientation, same_line_identity)
            d1, d2 = two_square_decrypt_pair(
                c1, c2, alphabet25, grid_pos, alphaB, posB,
                orientation, same_line_identity)
            assert (d1, d2) == (l1, l2), (
                f"two-square round-trip failed for "
                f"{orientation}/{same_line_identity}: {l1}{l2} -> {c1}{c2} -> {d1}{d2}")

    for l1, l2 in [("H", "I"), ("D", "A"), ("N", "V")]:
        c1, c2 = four_square_encrypt_pair(l1, l2, alphabet25, alphaB)
        d1, d2 = four_square_decrypt_pair(
            c1, c2, alphabet25,
            {letter: divmod(i, 5) for i, letter in enumerate(alphabet25)},
            alphaB, posB)
        assert (d1, d2) == (l1, l2), (
            f"four-square round-trip failed: {l1}{l2} -> {c1}{c2} -> {d1}{d2}")

    assert make_pairs("ABCDEFGHIJ") is not None
    assert make_pairs("ABCDEFGHIJK") is None

    # segment_codes rejects a dangling escape instead of silently truncating.
    assert segment_codes("abbec", "b", "e") == ["a", "bb", "ec"]  # non-dangling: valid
    assert segment_codes("abbe", "b", "e") is None  # trailing 'e' (escape) with nothing after
    assert segment_codes("ab", "b", "e") is None  # trailing 'b' (escape) with nothing after

    for family in ("playfair", "two_square", "four_square", "bifid"):
        control = build_synthetic_control(family)
        candidates = [
            (candidate_family, (control["e1"], control["e2"]) + params, text)
            for candidate_family, params, text in sweep_codes(
                control["codes"], control["e1"], control["e2"], CORE_KEYWORDS)
        ]
        assert any(
            candidate_family == family
            and params == (control["e1"], control["e2"]) + control["params"]
            and text == control["plaintext"]
            for candidate_family, params, text in candidates
        ), f"{family} end-to-end sweep control failed"

    odd_candidates = sweep_codes(["a"] * 63, "g", "i", ("matrix",))
    assert {family for family, _, _ in odd_candidates} == {"bifid"}

    print("All self-tests passed.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--calibration-trials", type=int, default=500)
    ap.add_argument("--target", choices=["dbbi", "faed", "both"], default="both")
    ap.add_argument("--shuffle-trials", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20260724)
    ap.add_argument("--significance", type=float, default=0.05)
    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        return
    if args.calibrate:
        run_self_tests()
        results = run_synthetic_calibration(
            args.calibration_trials, args.seed, args.workers)
        if any(result["p_value"] >= args.significance for result in results):
            raise SystemExit(
                "synthetic calibration failed to clear the significance gate")
        return

    targets = ["dbbi", "faed"] if args.target == "both" else [args.target]
    for target_name in targets:
        ciphertext = TARGETS[target_name]
        candidates = sweep_target(target_name, ciphertext)
        candidates.sort(key=lambda c: -c[3])
        print(f"\n=== {target_name}: {len(candidates)} candidates across "
              f"{len(TARGET_ESCAPES[target_name])} escape hypotheses x "
              f"{len(CORE_KEYWORDS)} keywords ===")
        print("Top 5 by quadgram score:")
        for family, params, text, sc in candidates[:5]:
            print(f"  {sc:8.1f}  {family:11s} {params}  {text!r}")

        gate = shuffle_gate(target_name, ciphertext, args.shuffle_trials,
                             seed=args.seed, workers=args.workers)
        print(f"\nShuffle gate ({gate['trials']} trials, seed={args.seed}): "
              f"real_best={gate['real_best']:.1f} null_mean={gate['null_mean']:.1f} "
              f"null_max={gate['null_max']:.1f} p={gate['p_value']:.5f} "
              f"({gate['per_trial_s']*1000:.1f}ms/trial)")

        if gate["p_value"] < args.significance:
            print(f"STATISTICALLY EXCEPTIONAL (p={gate['p_value']:.5f} < "
                  f"{args.significance}) -- escalating top candidates to AES.")
            tested = 0
            for family, params, text, sc in candidates:
                if sc < gate["real_best"] - 5:  # only genuinely top-tier candidates
                    break
                for keystr in keystr_forms(text):
                    tested += 1
                    r = aes_try_open(keystr)
                    if r:
                        print(f"  HIT: {family} {params} {text!r} -> {r}")
            print(f"  ({tested} additional keystr-tests)")
        else:
            print(f"Not statistically exceptional (p={gate['p_value']:.5f} >= "
                  f"{args.significance}) -- not escalating further candidates to AES.")


if __name__ == "__main__":
    main()
