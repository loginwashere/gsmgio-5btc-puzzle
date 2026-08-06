"""Quadgram-fitness hill-climbing / simulated-annealing attack on dbbi's straddling
checkerboard, independent of guessing the actual riddle sentence.

Rationale (see doc/GSMG_PUZZLE.md + memory): every attempt so far has been top-down
(guess a riddle sentence -> derive an alphabet -> decode -> test). This attacks the
*key* directly: search the space of 25-symbol-to-letter assignments using standard
English quadgram statistics as a fitness function (the classic technique for solving
homophonic/straddling-checkerboard ciphers ciphertext-only), then check the top
ranked candidates with the AES plausibility oracle.

dbbi is short (91 symbols, ~50-70 decoded letters) -- on the low end for blind
substitution-key recovery to guarantee a unique answer in one run. Mitigated with
many random restarts across all 4 structural variants (escape-pair role x topology)
and by retaining every local optimum before ranking.
"""
import math
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from cb_common import aes_try_open, build_board_9ary, keystr_forms
from data import DBBI

QUADGRAM_FILE = SCRIPT_DIR / "data_files" / "english_quadgrams.txt"

ALPHABET26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def load_quadgrams(path=QUADGRAM_FILE):
    counts = {}
    total = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            quad, cnt = line.split()
            cnt = int(cnt)
            counts[quad] = cnt
            total += cnt
    floor = math.log10(0.01 / total)
    logp = {q: math.log10(c / total) for q, c in counts.items()}
    return logp, floor


LOGP, FLOOR = load_quadgrams()


def score(text):
    """Sum of log10-probabilities of every 4-letter sliding window."""
    s = 0.0
    for i in range(len(text) - 3):
        s += LOGP.get(text[i:i + 4], FLOOR)
    return s


def decode_with_key(seq, key26, e1, e2, topology):
    """key26: list of 26 letters; first 25 are the assigned alphabet, last is unused
    (the 'dropped' letter for this state). Builds the board directly (avoids the
    pad25()/drop-letter machinery -- here we search the raw assignment)."""
    alphabet25 = "".join(key26[:25])
    bd = build_board_9ary(alphabet25, e1, e2, topology)
    out = []
    i = 0
    n = len(seq)
    while i < n:
        ch = seq[i]
        if ch in (e1, e2):
            if i + 1 >= n:
                out.append("?")
                break
            out.append(bd.get(seq[i:i + 2], "?"))
            i += 2
        else:
            out.append(bd.get(ch, "?"))
            i += 1
    return "".join(out)


def hillclimb(seq, e1, e2, topology, iters=2500, restarts=150, seed=None, T0=2.5, cool=0.9995):
    rng = random.Random(seed)
    best_overall = (-1e18, None, None)
    results = []  # (score, decode, key26) for each restart's local optimum
    for r in range(restarts):
        key = list(ALPHABET26)
        rng.shuffle(key)
        cur_decode = decode_with_key(seq, key, e1, e2, topology)
        cur_score = score(cur_decode)
        T = T0
        for it in range(iters):
            i, j = rng.sample(range(26), 2)
            key[i], key[j] = key[j], key[i]
            cand_decode = decode_with_key(seq, key, e1, e2, topology)
            cand_score = score(cand_decode)
            delta = cand_score - cur_score
            if delta >= 0 or rng.random() < math.exp(delta / max(T, 1e-6)):
                cur_score, cur_decode = cand_score, cand_decode
            else:
                key[i], key[j] = key[j], key[i]  # revert
            T *= cool
        results.append((cur_score, cur_decode, key[:]))
        if cur_score > best_overall[0]:
            best_overall = (cur_score, cur_decode, key[:])
    return best_overall, results


def run_all_variants(seq, seq_name, iters, restarts, seed_base=0, base_pair=("b", "e")):
    e1_, e2_ = base_pair
    variants = [
        (e1_, e2_, "top_first"), (e2_, e1_, "top_first"),
        (e1_, e2_, "escapes_first"), (e2_, e1_, "escapes_first"),
    ]
    all_results = []
    for vi, (e1, e2, topo) in enumerate(variants):
        best, results = hillclimb(seq, e1, e2, topo, iters=iters, restarts=restarts,
                                   seed=seed_base + vi)
        print(f"[{seq_name} {e1}/{e2} {topo}] best score={best[0]:.1f}  decode={best[1]!r}")
        for s_, d_, k_ in results:
            all_results.append((s_, d_, (e1, e2, topo), k_))
    all_results.sort(key=lambda x: -x[0])
    return all_results


def _worker(args):
    seq, e1, e2, topo, iters, count, seed = args
    best, results = hillclimb(seq, e1, e2, topo, iters=iters, restarts=count, seed=seed)
    return [(s_, d_, (e1, e2, topo), k_) for s_, d_, k_ in results]


def run_all_variants_parallel(seq, seq_name, iters, restarts_per_variant, workers=16,
                               seed_base=0, base_pair=("b", "e")):
    import concurrent.futures as cf
    e1_, e2_ = base_pair
    variants = [
        (e1_, e2_, "top_first"), (e2_, e1_, "top_first"),
        (e1_, e2_, "escapes_first"), (e2_, e1_, "escapes_first"),
    ]
    jobs = []
    per_worker = max(1, restarts_per_variant // workers)
    seed = seed_base
    for (e1, e2, topo) in variants:
        remaining = restarts_per_variant
        while remaining > 0:
            n = min(per_worker, remaining)
            jobs.append((seq, e1, e2, topo, iters, n, seed))
            seed += 1
            remaining -= n
    print(f"[{seq_name}] dispatching {len(jobs)} jobs across {workers} workers "
          f"({restarts_per_variant} restarts/variant x {len(variants)} variants x {iters} iters)...")
    all_results = []
    done = 0
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_worker, jobs):
            all_results.extend(res)
            done += 1
            if done % max(1, len(jobs) // 10) == 0:
                print(f"  {done}/{len(jobs)} jobs done")
    all_results.sort(key=lambda x: -x[0])
    return all_results


if __name__ == "__main__":
    ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2500
    RESTARTS = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    TOPN = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    WORKERS = int(sys.argv[4]) if len(sys.argv) > 4 else 1

    print(f"Loaded {len(LOGP)} quadgrams. Running dbbi hillclimb: iters={ITERS} restarts={RESTARTS} workers={WORKERS}...")
    if WORKERS > 1:
        dbbi_results = run_all_variants_parallel(DBBI, "dbbi", ITERS, RESTARTS, workers=WORKERS, seed_base=1000)
    else:
        dbbi_results = run_all_variants(DBBI, "dbbi", ITERS, RESTARTS, seed_base=1000)

    print(f"\nTop {min(10, len(dbbi_results))} dbbi decodes by quadgram score:")
    for s_, d_, variant, k_ in dbbi_results[:10]:
        print(f"  {s_:9.1f}  {variant}  {d_!r}")

    print(f"\nChecking top {TOPN} dbbi candidates with the AES plausibility oracle "
          f"(both blobs, all 6 KDF variants, raw/sha256/double-sha256 forms)...")
    hits = []
    tested = set()
    for s_, d_, variant, k_ in dbbi_results[:TOPN]:
        if d_ in tested:
            continue
        tested.add(d_)
        for keystr in keystr_forms(d_):
            r = aes_try_open(keystr)
            if r:
                hits.append((d_, variant, keystr, r))
    print(f"Tested {len(tested)} unique decodes ({len(tested)*3} keystr-tests). Hits: {len(hits)}")
    for h in hits:
        print("  HIT:", h)

    print("\nDone.")
