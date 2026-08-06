"""Synthetic-control calibration harness for quadgram_solver.py's checkerboard
recovery hill-climb (doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md, path #4:
"Calibrated Recovery of the Raw Checkerboard Alphabet").

Question: the 2026-07-12 hill-climb against real `dbbi` (60,000 restarts x
5,000 iters across all 4 structural variants) came back negative -- best
decode scored worse than real English and read as noise. But `dbbi` only
decodes to 63 letters using 19 of 25 possible code types under `{b,e}` (91 raw
9-ary symbols: 35 single-symbol "top" codes + 28 double-symbol "escape"
codes), a difficult regime for ciphertext-only substitution recovery. A
negative result there could mean either "dbbi isn't a plain checkerboard
under this construction" OR "the solver has no power at this length
regardless of the true answer" -- those need to be told apart before the
negative is trusted as informative.

This answers that WITHOUT modifying quadgram_solver.py: imports its
hillclimb()/run_all_variants_parallel() unchanged, and feeds them synthetic
ciphertexts built by encoding real English text (Matrix screenplay / Cosmic
Duality book / puzzle chat archive) through a board CONSTRUCTED to match
dbbi's exact profile -- not just 63 codes, but exactly 91 raw symbols (35
top / 28 escape) and exactly 19 distinct code types -- since raw length and
type count both change how hard ciphertext-only recovery is.

Two corrections versus the first version of this harness (both from an
external review, verified before acting on them):

1. The first version called run_all_variants_parallel() fresh inside
   run_calibration() every time it ran -- there was no persisted artifact, so
   a claim of "reusing already-explored candidates, no new hill-climb
   compute" was false whenever the process was invoked more than once. Local
   optima are now cached to disk (calibration_cache/, JSONL) keyed by the
   exact (ciphertext, iters, restarts, seed) that produced them, so re-running
   an already-computed trial (e.g. to test another hybrid weight) is genuinely
   compute-free.
2. The first version's 24 controls had 97-122 raw symbols and only 5/24 hit
   19 types; none matched dbbi's exact 91/63/19 profile, and the hybrid
   bonus weight was chosen and reported on the SAME 24 trials (a tuning/
   evaluation split was needed to avoid overfitting the weight to its own
   test set). Controls are now built to match 91/63/19 exactly via a
   subset-sum search over each candidate plaintext's own letter-frequency
   histogram (see find_top_subset()), and trials are split into disjoint
   tuning/holdout sets: the hybrid weight is selected on tuning only, then
   evaluated once on holdout.
"""
import argparse
import hashlib
import itertools
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CACHE_DIR = SCRIPT_DIR / "calibration_cache"
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import NINE_SYMS, build_board_9ary
from quadgram_solver import ALPHABET26, run_all_variants_parallel, score

DICT_PATH = Path("/usr/share/dict/american-english")
WORD_MIN_LEN, WORD_MAX_LEN = 3, 12

# Per-target ciphertext profile. Each entry's plaintext_len/raw_len/n_types/
# top_sum were verified directly against the real string (dbbi: FINDINGS.md
# Phase 20; faed: this session, segment_codes(FAED, "h", "e")). MAX_TOP_SIZE
# is board-structural (7 top slots, fixed regardless of profile), not
# per-target. Module-level PLAINTEXT_LEN/TARGET_N_TYPES/TARGET_TOP_SUM/
# RAW_LEN/ENCODE_E1/ENCODE_E2/ENCODE_TOPOLOGY are set from PROFILES[target]
# by apply_profile() before any calibration runs -- every function below
# still just reads the module globals, so dbbi's behavior (the default) is
# byte-identical to before this refactor.
PROFILES = {
    "dbbi": {
        # {b,e}: 63 codes, 91 raw 9-ary symbols, split 35 single-symbol "top"
        # codes + 28 double-symbol "escape" codes, touching 19 of 25 slots.
        "plaintext_len": 63,
        "raw_len": 91,
        "target_n_types": 19,
        "target_top_sum": 35,
        "encode_e1": "b",
        "encode_e2": "e",
        "encode_topology": "top_first",
    },
    "faed": {
        # (h,e): 469 codes, 570 raw 9-ary symbols, touching all 25 of 25
        # slots (368 in the 7 top codes, 101 in the 18 escape codes).
        "plaintext_len": 469,
        "raw_len": 570,
        "target_n_types": 25,
        "target_top_sum": 368,
        "encode_e1": "h",
        "encode_e2": "e",
        "encode_topology": "top_first",
    },
}
MAX_TOP_SIZE = 7  # the board only has 7 top slots -- can't assign more distinct
# letters there regardless of the target sum or profile.


def apply_profile(name):
    """Sets the module-level PLAINTEXT_LEN/RAW_LEN/TARGET_N_TYPES/
    TARGET_TOP_SUM/ENCODE_E1/ENCODE_E2/ENCODE_TOPOLOGY globals from
    PROFILES[name]. Must be called before any calibration function runs."""
    global PLAINTEXT_LEN, RAW_LEN, TARGET_N_TYPES, TARGET_TOP_SUM
    global ENCODE_E1, ENCODE_E2, ENCODE_TOPOLOGY
    profile = PROFILES[name]
    PLAINTEXT_LEN = profile["plaintext_len"]
    RAW_LEN = profile["raw_len"]
    TARGET_N_TYPES = profile["target_n_types"]
    TARGET_TOP_SUM = profile["target_top_sum"]
    ENCODE_E1 = profile["encode_e1"]
    ENCODE_E2 = profile["encode_e2"]
    ENCODE_TOPOLOGY = profile["encode_topology"]


apply_profile("dbbi")  # default -- matches this file's pre-refactor behavior

CORPUS_SOURCES = {
    # (path, dedup stride). matrix_script_windows.txt is a 15-word SLIDING window
    # (stride 1) over the 3 Matrix screenplays -- taking every 15th line reconstructs
    # the underlying continuous script text without the massive line-to-line overlap
    # a stride-1 read would otherwise introduce (verified: line[i] and line[i+15]
    # share no words).
    "matrix": (REPO_ROOT / "wordlists/gsmg/matrix_script_windows.txt", 15),
    "book": (REPO_ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt", None),
    "chat": (REPO_ROOT / "wordlists/gsmg/chat_mined_lines.txt", None),
}


def load_letters(path, stride):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if stride:
        lines = lines[::stride]
    text = " ".join(lines)
    return re.sub(r"[^A-Za-z]", "", text).upper()


def load_word_set(path=DICT_PATH, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN):
    words = set()
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.strip().upper()
            if w.isalpha() and min_len <= len(w) <= max_len:
                words.add(w)
    return words


def word_bonus(text, words, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN):
    """Sum of (matched-word-length)^2 over every dictionary-word substring found
    (overlaps allowed -- this is a comparative signal, not a segmentation)."""
    n = len(text)
    bonus = 0.0
    for i in range(n):
        for length in range(min_len, max_len + 1):
            if i + length > n:
                break
            if text[i:i + length] in words:
                bonus += length * length
    return bonus


def natural_code_index(code, e1, e2, topology):
    tops = [c for c in NINE_SYMS if c not in (e1, e2)]
    if len(code) == 1:
        off = 0 if topology == "top_first" else 18
        return off + tops.index(code)
    e1c, d = code[0], NINE_SYMS.index(code[1])
    if topology == "top_first":
        off = 7 if e1c == e1 else 16
    else:
        off = 0 if e1c == e1 else 9
    return off + d


def code_type_stats(ciphertext, e1, e2, topology):
    i, codes = 0, []
    n = len(ciphertext)
    while i < n:
        if ciphertext[i] in (e1, e2):
            codes.append(ciphertext[i:i + 2])
            i += 2
        else:
            codes.append(ciphertext[i])
            i += 1
    types = {natural_code_index(c, e1, e2, topology) for c in codes}
    return len(codes), len(types)


def find_top_subset(letter_counts, target_sum=None, max_size=MAX_TOP_SIZE):
    """letter_counts: dict letter->count for the distinct letters present in a
    plaintext sample. Finds a subset of size <= max_size whose counts sum to
    exactly target_sum -- the letters that would need to sit in the board's 7
    "top" (single-symbol-code) slots for this plaintext to reproduce the
    active profile's top/escape split. Returns the subset (list of letters)
    or None if no exact combination exists for this plaintext's histogram.

    target_sum defaults to the CURRENT value of the module-global
    TARGET_TOP_SUM, read at call time (not baked in at def time) -- callers
    that don't pass target_sum explicitly (build_profile_matched_board)
    must see whichever profile apply_profile() last activated, not whatever
    was active when this function was defined."""
    if target_sum is None:
        target_sum = TARGET_TOP_SUM
    items = list(letter_counts.items())
    n = len(items)
    for k in range(0, max_size + 1):
        for combo in itertools.combinations(range(n), k):
            if sum(items[i][1] for i in combo) == target_sum:
                return [items[i][0] for i in combo]
    return None


def build_profile_matched_board(plaintext, rng):
    """Builds a 25-letter board (top_first layout: [7 top][9 e1-row][9 e2-row])
    that reproduces dbbi's exact 63-code/91-raw/19-type/35-top/28-escape
    profile for this specific plaintext, if possible. Returns None if the
    plaintext doesn't have exactly 19 distinct letters, or no top-subset
    summing to TARGET_TOP_SUM exists for its histogram."""
    counts = Counter(plaintext)
    if len(counts) != TARGET_N_TYPES:
        return None
    top_subset = find_top_subset(dict(counts))
    if top_subset is None:
        return None
    present = set(counts)
    # exactly 26-TARGET_N_TYPES letters are absent from this plaintext; one is
    # dropped entirely, the rest pad out the top/escape slots not already
    # filled by `present`. For dbbi (19 types) that's 1 dropped + 6 filler;
    # for faed (25 types, all 25 board slots used) it's 1 dropped + 0 filler.
    absent = [c for c in ALPHABET26 if c not in present]
    rng.shuffle(absent)
    drop_letter, filler = absent[0], absent[1:]

    # Anchored to ALPHABET26's fixed order, not `present` (a set) directly -- set
    # iteration order is hash-randomized per process (PYTHONHASHSEED), which would
    # silently make the pre-shuffle list order (and therefore rng.shuffle()'s
    # output) non-reproducible across separate invocations despite a fixed seed.
    escape_present = [c for c in ALPHABET26 if c in present and c not in top_subset]
    top_pad_needed = 7 - len(top_subset)
    escape_pad_needed = 18 - len(escape_present)
    assert top_pad_needed + escape_pad_needed == len(filler) == 26 - TARGET_N_TYPES - 1

    top_slots = list(top_subset) + filler[:top_pad_needed]
    escape_slots = list(escape_present) + filler[top_pad_needed:]
    rng.shuffle(top_slots)
    rng.shuffle(escape_slots)
    alphabet25 = "".join(top_slots + escape_slots)
    assert len(alphabet25) == 25 and len(set(alphabet25)) == 25
    return alphabet25


def encode(plaintext, alphabet25, e1, e2, topology):
    """Inverse of build_board_9ary/decode_9ary: plaintext letter -> ciphertext code."""
    bd = build_board_9ary(alphabet25, e1, e2, topology)
    inv = {v: k for k, v in bd.items()}
    out = []
    for ch in plaintext:
        code = inv.get(ch)
        if code is None:
            return None
        out.append(code)
    return "".join(out)


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


def make_profile_matched_trials(counts_needed, rng):
    """counts_needed: dict source_name -> number of profile-matched trials to
    build. Scans non-overlapping 63-char windows (independent samples, not a
    sliding scan) per source, in random order, keeping the first ones whose
    plaintext admits an exact dbbi-profile board (build_profile_matched_board
    returns non-None). Consumes windows across sources without replacement, so
    calling this twice with disjoint RNG state (or slicing the combined pool)
    gives disjoint tuning/holdout sets by construction."""
    trials = []
    for source_name, (path, stride) in CORPUS_SOURCES.items():
        n_needed = counts_needed[source_name]
        if n_needed == 0:
            continue
        letters = load_letters(path, stride)
        windows = [letters[i:i + PLAINTEXT_LEN]
                   for i in range(0, len(letters) - PLAINTEXT_LEN + 1, PLAINTEXT_LEN)]
        order = list(range(len(windows)))
        rng.shuffle(order)
        made = 0
        for idx in order:
            if made >= n_needed:
                break
            plaintext = windows[idx]
            alphabet25 = build_profile_matched_board(plaintext, rng)
            if alphabet25 is None:
                continue
            ct = encode(plaintext, alphabet25, ENCODE_E1, ENCODE_E2, ENCODE_TOPOLOGY)
            if ct is None:
                continue
            n_codes, n_types = code_type_stats(ct, ENCODE_E1, ENCODE_E2, ENCODE_TOPOLOGY)
            assert len(ct) == RAW_LEN and n_codes == PLAINTEXT_LEN and n_types == TARGET_N_TYPES, (
                f"profile-matched board failed to reproduce the target profile: "
                f"raw={len(ct)} codes={n_codes} types={n_types}")
            trials.append({
                "source": source_name,
                "plaintext": plaintext,
                "ciphertext": ct,
                "alphabet25": alphabet25,
                "n_codes": n_codes,
                "n_types": n_types,
            })
            made += 1
        if made < n_needed:
            print(f"WARNING: only found {made}/{n_needed} profile-matched trials "
                  f"for source={source_name} (pool exhausted or too strict)")
    return trials


def cache_path_for(ciphertext, iters, restarts, seed_base):
    # Deliberately NOT keyed on ENCODE_E1/ENCODE_E2/target profile: adding
    # them would invalidate the real DBBI calibration compute already cached
    # here (2026-07-24, ~24 trials). Safe because ciphertext content itself
    # differs across profiles (different alphabet/length), so no cross-
    # profile collision is possible in practice.
    key = f"{ciphertext}|{iters}|{restarts}|{seed_base}"
    h = hashlib.sha256(key.encode()).hexdigest()[:20]
    return CACHE_DIR / f"optima_{h}.jsonl"


def load_cached_optima(path):
    if not path.exists():
        return None
    results = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            results.append((rec["score"], rec["decode"], tuple(rec["variant"]), None))
    return results


def save_optima_cache(path, all_results):
    CACHE_DIR.mkdir(exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        for s_, d_, variant, _k in all_results:
            f.write(json.dumps({"score": s_, "decode": d_, "variant": list(variant)}) + "\n")
    tmp.rename(path)


def get_local_optima(trial, ti, iters, restarts_per_variant, workers, seed):
    """Cache-checked wrapper around run_all_variants_parallel -- a rerun with the
    exact same (ciphertext, iters, restarts, seed) loads from disk instead of
    recomputing the hill-climb."""
    ct = trial["ciphertext"]
    seed_base = seed + 1000 * (ti + 1)
    path = cache_path_for(ct, iters, restarts_per_variant, seed_base)
    cached = load_cached_optima(path)
    if cached is not None:
        print(f"[{trial['source']}-{ti}] loaded {len(cached)} cached local optima "
              f"from {path.name} (no hill-climb compute)")
        return cached
    all_results = run_all_variants_parallel(
        ct, f"calib-{trial['source']}-{ti}", iters, restarts_per_variant,
        workers=workers, seed_base=seed_base, base_pair=(ENCODE_E1, ENCODE_E2))
    save_optima_cache(path, all_results)
    return all_results


def evaluate_trial(trial, all_results, near_exact_max_mismatch, words, hybrid_weights):
    pt = trial["plaintext"]
    true_score = score(pt)
    best_score, best_decode, best_variant, _ = all_results[0]
    mism = hamming(best_decode, pt)

    best_mism_any = min(hamming(d_, pt) for _, d_, _, _ in all_results)
    n_better_scoring_wrong = sum(
        1 for s_, d_, _, _ in all_results if s_ > true_score and hamming(d_, pt) > 0)

    bonuses = [word_bonus(d_, words) for _, d_, _, _ in all_results]
    hybrid_mism = {}
    for w in hybrid_weights:
        best_i = max(range(len(all_results)), key=lambda i: all_results[i][0] + w * bonuses[i])
        hybrid_mism[w] = hamming(all_results[best_i][1], pt)

    return {
        **{k: v for k, v in trial.items() if k != "ciphertext"},
        "true_score": true_score,
        "best_score": best_score,
        "best_decode": best_decode,
        "best_variant": best_variant,
        "mismatches": mism,
        "exact": mism == 0,
        "near_exact": mism <= near_exact_max_mismatch,
        "best_mism_any": best_mism_any,
        "any_exact": best_mism_any == 0,
        "any_near_exact": best_mism_any <= near_exact_max_mismatch,
        "n_local_optima_outscoring_truth": n_better_scoring_wrong,
        "hybrid_mism": hybrid_mism,
    }


def print_trial(ti, total, r, near_exact_max_mismatch, hybrid_weights):
    hybrid_str = "  ".join(f"w={w}:mism={r['hybrid_mism'][w]:2d}" for w in hybrid_weights)
    print(f"[{ti+1}/{total}] {r['source']:6s} codes={r['n_codes']} types={r['n_types']:2d}  "
          f"true_score={r['true_score']:8.1f} best_score={r['best_score']:8.1f}  "
          f"mismatches={r['mismatches']:2d}/{PLAINTEXT_LEN}  "
          f"top1_exact={r['exact']} top1_near={r['near_exact']}  "
          f"search_found_truth(mism={r['best_mism_any']})={r['any_exact']}  "
          f"wrong_optima_outscoring_truth={r['n_local_optima_outscoring_truth']}  {hybrid_str}")


def summarize(results, near_exact_max_mismatch, label):
    n = len(results)
    n_exact = sum(r["exact"] for r in results)
    n_near = sum(r["near_exact"] for r in results)
    n_any_exact = sum(r["any_exact"] for r in results)
    n_any_near = sum(r["any_near_exact"] for r in results)
    mism_dist = Counter(r["mismatches"] for r in results)
    print(f"\n=== {label} summary ({n} trials) ===")
    print(f"Top-1-by-score exact recovery:      {n_exact}/{n} ({100*n_exact/n:.1f}%)")
    print(f"Top-1-by-score near-exact (<= {near_exact_max_mismatch} mismatches): {n_near}/{n} ({100*n_near/n:.1f}%)")
    print(f"Search ever visited the true key (any local optimum): {n_any_exact}/{n} ({100*n_any_exact/n:.1f}%)")
    print(f"Search ever visited a near-exact key:                 {n_any_near}/{n} ({100*n_any_near/n:.1f}%)")
    print(f"Mismatch-count histogram (top-1-by-score): {dict(sorted(mism_dist.items()))}")
    return {"n": n, "n_exact": n_exact, "n_near": n_near,
            "n_any_exact": n_any_exact, "n_any_near": n_any_near}


def run_calibration(per_source_tuning=4, per_source_holdout=4, iters=4000,
                     restarts_per_variant=2000, workers=16, near_exact_max_mismatch=6,
                     seed=20260724, hybrid_weights=(0.0, 0.3, 0.5, 1.0, 2.0)):
    master_rng = random.Random(seed)
    needed = {s: per_source_tuning for s in CORPUS_SOURCES}
    tuning_trials = make_profile_matched_trials(needed, master_rng)
    needed_holdout = {s: per_source_holdout for s in CORPUS_SOURCES}
    holdout_trials = make_profile_matched_trials(needed_holdout, master_rng)

    words = load_word_set()
    print(f"Built {len(tuning_trials)} tuning + {len(holdout_trials)} holdout "
          f"profile-matched trials (target: {PLAINTEXT_LEN} codes / {RAW_LEN} raw / "
          f"{TARGET_N_TYPES} types). Loaded "
          f"{len(words)} dictionary words for hybrid rescoring.\n")

    def run_set(trials, seed_offset, label):
        results = []
        for ti, trial in enumerate(trials):
            all_results = get_local_optima(trial, ti + seed_offset, iters,
                                            restarts_per_variant, workers, seed)
            r = evaluate_trial(trial, all_results, near_exact_max_mismatch, words,
                                hybrid_weights)
            results.append(r)
            print_trial(ti, len(trials), r, near_exact_max_mismatch, hybrid_weights)
        summarize(results, near_exact_max_mismatch, label)
        return results

    tuning_results = run_set(tuning_trials, 0, "TUNING")

    print("\n--- Selecting hybrid weight on TUNING set only ---")
    best_weight, best_near = hybrid_weights[0], -1
    for w in hybrid_weights:
        n_near = sum(1 for r in tuning_results if r["hybrid_mism"][w] <= near_exact_max_mismatch)
        n_exact = sum(1 for r in tuning_results if r["hybrid_mism"][w] == 0)
        print(f"  weight={w}: exact {n_exact}/{len(tuning_results)}, "
              f"near-exact {n_near}/{len(tuning_results)}")
        if n_near > best_near:
            best_near, best_weight = n_near, w
    print(f"Selected weight={best_weight} (best near-exact rate on tuning set)")

    holdout_results = run_set(holdout_trials, len(tuning_trials), "HOLDOUT")

    n = len(holdout_results)
    n_hy_exact = sum(1 for r in holdout_results if r["hybrid_mism"][best_weight] == 0)
    n_hy_near = sum(1 for r in holdout_results if r["hybrid_mism"][best_weight] <= near_exact_max_mismatch)
    print(f"\n=== HOLDOUT result at tuning-selected weight={best_weight} (unbiased estimate) ===")
    print(f"Hybrid exact recovery:      {n_hy_exact}/{n} ({100*n_hy_exact/n:.1f}%)")
    print(f"Hybrid near-exact recovery: {n_hy_near}/{n} ({100*n_hy_near/n:.1f}%)")

    # The metric that actually validates/invalidates the original dbbi negative:
    # achievable best-score ceiling, on the HELD-OUT set only (never used to pick
    # anything), matched to dbbi's exact 91/63/19 profile.
    holdout_best_scores = [r["best_score"] for r in holdout_results]
    holdout_per_char = sorted(s / PLAINTEXT_LEN for s in holdout_best_scores)
    print(f"\nHoldout best-score-per-char distribution (n={len(holdout_per_char)}): "
          f"min={holdout_per_char[0]:.3f} max={holdout_per_char[-1]:.3f} "
          f"median={holdout_per_char[len(holdout_per_char)//2]:.3f}")

    return {"tuning": tuning_results, "holdout": holdout_results,
            "selected_weight": best_weight, "holdout_per_char_scores": holdout_per_char}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", choices=sorted(PROFILES), default="dbbi",
                     help="which PROFILES entry to calibrate against (default: %(default)s)")
    ap.add_argument("--per-source-tuning", type=int, default=4)
    ap.add_argument("--per-source-holdout", type=int, default=4)
    ap.add_argument("--iters", type=int, default=4000)
    ap.add_argument("--restarts", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--near-exact-max-mismatch", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20260724)
    args = ap.parse_args()
    apply_profile(args.target)
    run_calibration(per_source_tuning=args.per_source_tuning,
                     per_source_holdout=args.per_source_holdout,
                     iters=args.iters, restarts_per_variant=args.restarts,
                     workers=args.workers,
                     near_exact_max_mismatch=args.near_exact_max_mismatch, seed=args.seed)
