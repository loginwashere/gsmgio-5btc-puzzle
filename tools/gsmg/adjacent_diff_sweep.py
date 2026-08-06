#!/usr/bin/env python3
"""Adjacent-difference / self-synchronizing-cipher hypothesis test for
dbbi/faed, prioritized 2026-07-24 per explicit instruction: "evidence is
weak," so this is deliberately bounded, not an open-ended search.

Hypothesis: each observed raw a-i symbol is a function of itself and its
immediate neighbor (a lag-1 differential/self-synchronizing encoding), rather
than an independent per-position code -- a question no prior sweep in this
project has tested (every other hypothesis has been about framing,
segmentation, or an additive keystream, never adjacency in the raw stream
itself).

Four base transforms on the full raw stream (mapped a-i -> 0-8), LINEAR
boundary only this pass (circular boundary is mathematically ambiguous --
diff has a 9-way additive-offset family of solutions, sum's solvability
depends on stream-length parity -- and is out of scope, a separately-scoped
follow-up if this pass shows signal):
  - diff:     d[i] = (s[i]-s[i-1]) % 9        -- direct adjacent difference
  - sum:      d[i] = (s[i]+s[i-1]) % 9        -- direct adjacent sum
  - inv_diff: true[0]=s[0] (seed retained -- an encoder doing lag-1
              difference encoding must transmit the first symbol
              un-encoded, since diff[0] has no predecessor), true[i] =
              (true[i-1]+s[i]) % 9            -- recovers a plaintext-index
              stream assuming s IS ALREADY a difference-encoding of it
  - inv_sum:  true[0]=s[0], true[i] = (s[i]-true[i-1]) % 9
each x direction (forward / reverse-then-reverse-back). Forward/reverse
`sum` are PROVABLY IDENTICAL (addition commutes), so the implementation
deduplicates transformed streams by exact string value rather than assuming
which pairs collide.

This module went through three rounds of external review before
implementation; each caught a real issue:
  - Round 1: circular-boundary math was wrong (see above) -> dropped.
  - Round 2: escape pairs ({b,e}/{g,i}/{h,e}) were derived by FREQUENCY
    ANALYSIS of the ORIGINAL streams and cannot be assumed to transfer to a
    transformed stream (whose symbol frequencies differ) -- this module
    re-derives a fresh escape pair per transformed stream instead (see
    candidate_pairs()), and re-runs that derivation inside every null
    permutation trial (since the selection is part of the fitted model, not
    fixed background knowledge). quadgram_solver.score() is an unnormalized
    sum, biased toward longer text -- this module normalizes by length.
  - Round 3: escape pairs are ORDERED ((e1,e2) vs (e2,e1) assign different
    alphabet rows) -- both orders are tested. The 47% escape-density
    reference (from the one known-good decoded example, Phase 3.2.2) is a
    property of THAT plaintext/keyword, not the cipher scheme in general --
    treated as a hedged heuristic (top-k candidates, not top-1), with the
    heuristic's calibration a HARD GATE: the real sweep does not run unless
    synthetic controls (fixed, never tuned to pass) recover their own known
    pair/plaintext at some k in {3,5,7,9}; k=9 is a deliberate, NON-exhaustive
    ceiling (36 unordered pairs exist in total), not "every valid pair."
    Testing both dbbi and faed at p<0.01 each gives combined false-positive
    risk near 0.02 -- Bonferroni-corrected to p<0.005 per target. A staged
    500-then-5000-trial design needs the confirmation batch to be drawn with
    an independent seed from the screening batch, or the two-stage procedure
    itself is an optional-stopping bug.

Escalation (only if a target's independent Stage-2 p<0.005): top 20 UNIQUE
decoded strings (by normalized score) tested against every oracle this
project has validated -- the original legacy CBC path, EXTENDED_CIPHER_VARIANTS
(AES-192/3DES/PBKDF2), and the AES Key Wrap oracle (RFC 3394/5649, both AIV
modes) with its raw-key/passphrase chaining -- against the default BLOBS,
with QUARANTINED_BLOBS (urlblob) opt-in only via --include-quarantined. No
manual "credible language" gate -- the AES oracle itself is the real
ground-truth check (a real passphrase need not resemble English).

A separate, non-gating diagnostic (transition-mask / run-length distribution
of the raw streams) is reported but never feeds the escalation decision.

Usage:
    python3 tools/gsmg/adjacent_diff_sweep.py --self-test
    python3 tools/gsmg/adjacent_diff_sweep.py --diagnostics-only
    python3 tools/gsmg/adjacent_diff_sweep.py
    python3 tools/gsmg/adjacent_diff_sweep.py --include-quarantined
"""
import argparse
import collections
import itertools
import multiprocessing
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    NINE_SYMS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    answer_forms,
    build_board_9ary,
    decode_9ary,
    keystr_forms,
    pad25,
)
from aes_key_wrap_sweep import chain_unwrapped  # noqa: E402
from data import DBBI, FAED  # noqa: E402
from prefix_boundary_sweep import (  # noqa: E402
    CORE_ALPHABET_SEEDS,
    MERGE_DIRS,
    TAIL_FILLS,
    TOPOLOGIES,
    _clean_book_sample,
    encode_9ary,
    segment_codes,
)
from quadgram_solver import score as quadgram_score  # noqa: E402

TARGET_STREAMS = {"dbbi": DBBI, "faed": FAED}
NINE_IDX = {c: i for i, c in enumerate(NINE_SYMS)}

# Escape-density reference: the escape-digit share (70/149) measured from the
# one known-good decoded example (Phase 3.2.2). Property of THAT plaintext/
# keyword's letter-frequency-driven 7-single/18-double code assignment, not
# an intrinsic constant of the cipher scheme -- used as a hedged heuristic
# prior (top-k candidates), not assumed exact.
ESCAPE_DENSITY_REFERENCE = 70 / 149

BASES = ("diff", "sum", "inv_diff", "inv_sum")
DIRECTIONS = ("forward", "reverse")

# Fixed, deterministic synthetic-control configuration -- never tuned to
# force calibration to pass (see run_self_tests/calibrate_k).
SYNTH_ESCAPES = {"dbbi": ("b", "e"), "faed": ("g", "i")}
SYNTH_SEED = "matrixsumlist"
SYNTH_TAIL_FILL, SYNTH_MERGE_DIRECTION = "forward", "backward"

SEED_BASE_1 = 20260724     # Stage 1 (screen) -- 500 trials
SEED_BASE_2 = 202607241    # Stage 2 (confirm) -- independent, 5000 trials


# ---------------------------------------------------------------------------
# 1. Transform definitions (linear boundary only)
# ---------------------------------------------------------------------------

def _diff_linear(idx):
    return [(idx[i] - idx[i - 1]) % 9 for i in range(1, len(idx))]


def _sum_linear(idx):
    return [(idx[i] + idx[i - 1]) % 9 for i in range(1, len(idx))]


def _inv_diff_linear(idx):
    true = [idx[0]]
    for i in range(1, len(idx)):
        true.append((true[-1] + idx[i]) % 9)
    return true


def _inv_sum_linear(idx):
    true = [idx[0]]
    for i in range(1, len(idx)):
        true.append((idx[i] - true[-1]) % 9)
    return true


_BASE_FUNCS = {
    "diff": _diff_linear,
    "sum": _sum_linear,
    "inv_diff": _inv_diff_linear,
    "inv_sum": _inv_sum_linear,
}


def _idx_to_stream(idx_list):
    return "".join(NINE_SYMS[v] for v in idx_list)


def apply_variant(stream, base, direction):
    """Apply one of the 4 base transforms, in forward or reverse direction."""
    src = stream if direction == "forward" else stream[::-1]
    idx = [NINE_IDX[c] for c in src]
    out_idx = _BASE_FUNCS[base](idx)
    out = _idx_to_stream(out_idx)
    if direction == "reverse":
        out = out[::-1]
    return out


def all_variant_streams(stream):
    """All 8 nominal (base,direction) transforms, deduplicated by exact
    string value (forward/reverse `sum` are provably identical; the
    dedup is by direct comparison rather than hardcoding that fact, so any
    other unexpected collision is also caught)."""
    seen = {}
    out = []
    for base in BASES:
        for direction in DIRECTIONS:
            t = apply_variant(stream, base, direction)
            if t not in seen:
                seen[t] = (base, direction)
                out.append((base, direction, t))
    return out


# Construction (forward direction): given a target true-index sequence,
# build a raw index sequence such that apply_variant(raw, base, "forward")
# recovers it exactly. These are the algebraic inverses of the four
# recovery formulas above.

def _construct_diff(true_idx):
    raw = [0]
    for t in true_idx:
        raw.append((raw[-1] + t) % 9)
    return raw


def _construct_sum(true_idx):
    raw = [0]
    for t in true_idx:
        raw.append((t - raw[-1]) % 9)
    return raw


def _construct_inv_diff(true_idx):
    raw = [true_idx[0]]
    for i in range(1, len(true_idx)):
        raw.append((true_idx[i] - true_idx[i - 1]) % 9)
    return raw


def _construct_inv_sum(true_idx):
    raw = [true_idx[0]]
    for i in range(1, len(true_idx)):
        raw.append((true_idx[i] + true_idx[i - 1]) % 9)
    return raw


_CONSTRUCT_FUNCS = {
    "diff": _construct_diff,
    "sum": _construct_sum,
    "inv_diff": _construct_inv_diff,
    "inv_sum": _construct_inv_sum,
}


def construct_variant(base, direction, true_idx):
    """Inverse of apply_variant: build a raw index sequence such that
    apply_variant(stream_from(raw), base, direction) == stream_from(true_idx).
    `reverse` reuses the forward recipe via string-reverse symmetry."""
    if direction == "forward":
        return _CONSTRUCT_FUNCS[base](true_idx)
    raw_rev = _CONSTRUCT_FUNCS[base](true_idx[::-1])
    return raw_rev[::-1]


# ---------------------------------------------------------------------------
# 2. Escape-pair derivation -- filter first, then rank, then hedge
# ---------------------------------------------------------------------------

def segments_cleanly(stream, e1, e2):
    return segment_codes(stream, e1, e2) is not None


def candidate_pairs(stream, k):
    """Filter-then-rank-then-hedge escape-pair derivation. Returns up to 2k
    ORDERED pairs: for the top-k structurally-valid unordered pairs by
    closeness to ESCAPE_DENSITY_REFERENCE, both orderings (e1,e2)/(e2,e1)
    (build_board_9ary assigns a different alphabet row to each)."""
    n = len(stream)
    valid = []
    for a, b in itertools.combinations(NINE_SYMS, 2):
        if not segments_cleanly(stream, a, b):     # filter FIRST
            continue
        share = (stream.count(a) + stream.count(b)) / n
        distance = abs(share - ESCAPE_DENSITY_REFERENCE)
        valid.append((distance, (a, b)))
    valid.sort(key=lambda x: (x[0], x[1]))          # deterministic tie-break
    out = []
    for _, (a, b) in valid[:k]:
        out.append((a, b))
        out.append((b, a))
    return out


# ---------------------------------------------------------------------------
# 3. Scoring -- normalized (quadgram_solver.score() is an unnormalized sum,
# biased toward longer text; different variants/escape-configs/topologies
# produce different decoded-text lengths)
# ---------------------------------------------------------------------------

def normalized_score(text):
    return quadgram_score(text) / max(1, len(text) - 3)


# ---------------------------------------------------------------------------
# 4. Candidate generation
# ---------------------------------------------------------------------------

def candidates_for_variant(transformed, topology, k):
    out = []
    for e1, e2 in candidate_pairs(transformed, k):
        for seed in CORE_ALPHABET_SEEDS:
            for tail_fill in TAIL_FILLS:
                for merge_direction in MERGE_DIRS:
                    alphabet25 = pad25(seed, tail_fill=tail_fill, merge_direction=merge_direction)
                    decoded = decode_9ary(transformed, alphabet25, e1, e2, topology)
                    if "?" in decoded:
                        continue
                    out.append((normalized_score(decoded), decoded,
                                (e1, e2, seed, tail_fill, merge_direction, topology)))
    return out


def all_candidates(stream, k):
    out = []
    for base, direction, transformed in all_variant_streams(stream):
        for topology in TOPOLOGIES:
            for score_val, decoded, meta in candidates_for_variant(transformed, topology, k):
                out.append((score_val, decoded, (base, direction) + meta))
    return out


def best_score(stream, k):
    cands = all_candidates(stream, k)
    return max((c[0] for c in cands), default=float("-inf"))


# ---------------------------------------------------------------------------
# 5. Synthetic-control calibration -- a HARD GATE, not a report-only check
# ---------------------------------------------------------------------------

def build_synthetic_control(base, direction, target, topology):
    """Fixed, never-tuned synthetic control: real English text encoded under
    a KNOWN configuration matching the exact mechanic being tested, then
    inverse-transformed to produce a synthetic raw stream."""
    stream_len = len(TARGET_STREAMS[target])
    e1, e2 = SYNTH_ESCAPES[target]
    alphabet25 = pad25(SYNTH_SEED, tail_fill=SYNTH_TAIL_FILL, merge_direction=SYNTH_MERGE_DIRECTION)
    board = build_board_9ary(alphabet25, e1, e2, topology)
    rev = {v: k2 for k2, v in board.items()}

    encoded_target_len = stream_len - 1 if base in ("diff", "sum") else stream_len
    sample = _clean_book_sample(encoded_target_len)
    encoded_len, cut = 0, 0
    for i, ch in enumerate(sample):
        encoded_len += len(rev[ch])
        cut = i + 1
        if encoded_len >= encoded_target_len:
            break
    plaintext = sample[:cut]
    encoded = encode_9ary(plaintext, alphabet25, e1, e2, topology)
    if len(encoded) > encoded_target_len:
        plaintext = plaintext[:-1]
        encoded = encode_9ary(plaintext, alphabet25, e1, e2, topology)

    true_idx = [NINE_IDX[c] for c in encoded]
    raw_idx = construct_variant(base, direction, true_idx)
    raw_stream = _idx_to_stream(raw_idx)
    return {
        "plaintext": plaintext,
        "encoded": encoded,
        "raw_stream": raw_stream,
        "e1": e1,
        "e2": e2,
    }


def _check_calibration(k):
    failures = []
    for target in TARGET_STREAMS:
        for topology in TOPOLOGIES:
            for base in BASES:
                for direction in DIRECTIONS:
                    ctrl = build_synthetic_control(base, direction, target, topology)
                    transformed = apply_variant(ctrl["raw_stream"], base, direction)
                    if transformed != ctrl["encoded"]:
                        failures.append(
                            f"{target}/{topology}/{base}/{direction}: construction/recovery "
                            f"algebra mismatch (internal error, not a calibration failure)"
                        )
                        continue
                    pairs = candidate_pairs(transformed, k)
                    if (ctrl["e1"], ctrl["e2"]) not in pairs:
                        failures.append(
                            f"{target}/{topology}/{base}/{direction}: true escape pair "
                            f"({ctrl['e1']},{ctrl['e2']}) not among candidate_pairs at k={k}"
                        )
                        continue
                    # The real statistic maximizes across every transform and
                    # topology, so calibration must prove the truth survives
                    # that same full-model competition rather than checking
                    # only the already-known generating transform in isolation.
                    cands = all_candidates(ctrl["raw_stream"], k)
                    if not cands:
                        failures.append(
                            f"{target}/{topology}/{base}/{direction}: no candidates produced at k={k}"
                        )
                        continue
                    best = max(cands, key=lambda c: c[0])
                    if best[1] != ctrl["plaintext"]:
                        failures.append(
                            f"{target}/{topology}/{base}/{direction}: true plaintext not top "
                            f"scorer at k={k} (got {best[1][:40]!r})"
                        )
    return (len(failures) == 0), failures


def calibrate_k():
    """Widen k (3,5,7,9) using SYNTHETIC CONTROLS ONLY until every check
    passes; freeze and return that k. Real DBBI/FAED data is never consulted
    while choosing k. k=9 is a deliberate, non-exhaustive ceiling (36
    unordered pairs exist in total) -- if it still fails, ABORT rather than
    silently widen further or tune the synthetic sample."""
    for k in (3, 5, 7, 9):
        ok, failures = _check_calibration(k)
        if ok:
            print(f"[*] calibration PASSED at k={k} (frozen for the real sweep)")
            return k
        print(f"[*] calibration FAILED at k={k} ({len(failures)} failures); widening k...")
        for f in failures[:10]:
            print(f"      {f}")
    raise SystemExit(
        "[!] top-nine escape-pair heuristic failed calibration -- ABORTING, real sweep NOT run. "
        "Widening to k=36 (fully exhaustive) would be a separate, explicitly-scoped escalation, "
        "not silently substituted here."
    )


# ---------------------------------------------------------------------------
# 6. Null model and staged trial budget
# ---------------------------------------------------------------------------

def _shuffle_trial(args):
    stream_chars, k, seed = args
    rng = random.Random(seed)
    shuffled = list(stream_chars)
    rng.shuffle(shuffled)
    return best_score("".join(shuffled), k)


def shuffle_gate(stream, k, trials, seed_base, workers=16):
    real_best = best_score(stream, k)
    rng = random.Random(seed_base)
    jobs = [(list(stream), k, rng.getrandbits(64)) for _ in range(trials)]
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as ex:
        null_scores = list(ex.map(_shuffle_trial, jobs, chunksize=max(1, trials // (workers * 4))))
    at_least_as_good = sum(1 for s in null_scores if s >= real_best)
    p = (at_least_as_good + 1) / (trials + 1)
    return {
        "real_best": real_best,
        "null_mean": sum(null_scores) / len(null_scores),
        "null_max": max(null_scores),
        "p": p,
        "trials": trials,
    }


def run_staged_gate(target, k, workers=16, trials_1=500, trials_2=5000):
    stream = TARGET_STREAMS[target]
    gate1 = shuffle_gate(stream, k, trials=trials_1, seed_base=SEED_BASE_1, workers=workers)
    print(f"[stage 1 screen] {target}: real_best={gate1['real_best']:.4f} "
          f"null_mean={gate1['null_mean']:.4f} null_max={gate1['null_max']:.4f} "
          f"p_500={gate1['p']:.5f} ({trials_1} trials) -- screening only, NOT a confirmed result")
    if gate1["p"] >= 0.02:
        print(f"[*] {target}: not advanced beyond screening (p_500={gate1['p']:.5f} >= 0.02)")
        return {"target": target, "advanced": False, "gate1": gate1, "gate2": None, "significant": False}

    gate2 = shuffle_gate(stream, k, trials=trials_2, seed_base=SEED_BASE_2, workers=workers)
    print(f"[stage 2 confirm] {target}: real_best={gate2['real_best']:.4f} "
          f"null_mean={gate2['null_mean']:.4f} null_max={gate2['null_max']:.4f} "
          f"p_5000={gate2['p']:.5f} ({trials_2} trials, INDEPENDENT seed) -- this is the reported result")
    significant = gate2["p"] < 0.005
    print(f"[*] {target}: {'SIGNIFICANT' if significant else 'not significant'} at "
          f"Bonferroni-corrected p<0.005 (p_5000={gate2['p']:.5f})")
    return {"target": target, "advanced": True, "gate1": gate1, "gate2": gate2, "significant": significant}


# ---------------------------------------------------------------------------
# 7. Escalation
# ---------------------------------------------------------------------------

def escalate(target, k, blobs=None):
    stream = TARGET_STREAMS[target]
    cands = all_candidates(stream, k)
    best_for_decoded = {}
    for score_val, decoded, meta in cands:
        if decoded not in best_for_decoded or score_val > best_for_decoded[decoded][0]:
            best_for_decoded[decoded] = (score_val, meta)
    uniq = sorted(best_for_decoded.items(), key=lambda kv: -kv[1][0])[:20]

    print(f"[*] {target}: escalating top {len(uniq)} unique decoded candidates "
          f"against every validated oracle (baseline, extended CBC/KDF, Key Wrap)")
    any_hit = False
    for decoded, (score_val, meta) in uniq:
        for form in answer_forms(decoded):
            for keystr in keystr_forms(form):
                r = aes_try_open(keystr, blobs=blobs)
                if r:
                    print(f"[+++ AES HIT - baseline] {meta} keystr={keystr!r} -> {r}")
                    any_hit = True
                r_ext = aes_try_open(keystr, kdf_variants=EXTENDED_CIPHER_VARIANTS, blobs=blobs)
                if r_ext:
                    print(f"[+++ AES HIT - extended] {meta} keystr={keystr!r} -> {r_ext}")
                    any_hit = True
                for tag, wrap_kind, kdf_label, key_len, unwrapped in aes_keywrap_try_open_bytes(
                    keystr.encode(), blobs=blobs
                ):
                    print(f"[+++ KEYWRAP UNWRAP] {meta} keystr={keystr!r} -> "
                          f"{tag}/{wrap_kind}/{kdf_label}/{key_len * 8}bit "
                          f"unwrapped={unwrapped.hex()}")
                    any_hit = True
                    raw_hits, pass_hits = chain_unwrapped(unwrapped, tag, blobs=blobs)
                    if raw_hits or pass_hits:
                        print(f"    [+++ CHAINED HIT] raw={raw_hits} passphrase={pass_hits}")
    if not any_hit:
        print(f"[*] {target}: no hit among escalated candidates under any oracle")
    return any_hit


# ---------------------------------------------------------------------------
# 8. Transition-mask / run-length diagnostic -- separate, non-gating
# ---------------------------------------------------------------------------

def transition_mask(s):
    return [1 if s[i] != s[i - 1] else 0 for i in range(1, len(s))]


def run_lengths(s):
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(j - i)
        i = j
    return out


def diagnostic_report(target, trials=20000, seed=20260724):
    s = TARGET_STREAMS[target]
    obs_rate = sum(transition_mask(s)) / (len(s) - 1)
    obs_runs = run_lengths(s)
    obs_max_run = max(obs_runs)

    rng = random.Random(seed)
    null_rates, null_max_runs = [], []
    for _ in range(trials):
        shuffled = list(s)
        rng.shuffle(shuffled)
        shuffled_s = "".join(shuffled)
        null_rates.append(sum(transition_mask(shuffled_s)) / (len(shuffled_s) - 1))
        null_max_runs.append(max(run_lengths(shuffled_s)))

    null_rate_mean = sum(null_rates) / trials
    p_rate = (
        sum(
            1 for rate in null_rates
            if abs(rate - null_rate_mean) >= abs(obs_rate - null_rate_mean)
        )
        + 1
    ) / (trials + 1)
    p_max_run = (sum(1 for m in null_max_runs if m >= obs_max_run) + 1) / (trials + 1)
    hist = dict(sorted(collections.Counter(obs_runs).items()))
    print(f"[diagnostic, non-gating] {target}: transition_rate={obs_rate:.4f} "
          f"(null_mean={null_rate_mean:.4f}) p~{p_rate:.4f}; "
          f"max_run={obs_max_run} (null_mean={sum(null_max_runs) / trials:.2f}) p~{p_max_run:.4f}")
    print(f"[diagnostic, non-gating] {target}: run_length_histogram={hist}")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def run_self_tests():
    print("[*] algebraic round-trip checks (construct -> apply_variant recovers input)...")
    test_true_idx = [NINE_IDX[c] for c in (DBBI[:50])]
    for base in BASES:
        for direction in DIRECTIONS:
            raw_idx = construct_variant(base, direction, test_true_idx)
            raw_stream = _idx_to_stream(raw_idx)
            recovered = apply_variant(raw_stream, base, direction)
            recovered_idx = [NINE_IDX[c] for c in recovered]
            assert recovered_idx == test_true_idx, (
                f"self-test FAILED: algebraic round-trip broken for "
                f"base={base} direction={direction}"
            )
    print("[*] algebraic round-trip OK for all 4 bases x 2 directions")

    k = calibrate_k()
    print(f"[*] self-test OK (algebraic round-trip + calibration frozen at k={k})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                     help="verify transform algebra + run the calibration gate, then exit")
    ap.add_argument("--diagnostics-only", action="store_true",
                     help="print the non-gating transition-mask/run-length report and exit")
    ap.add_argument("--include-quarantined", action="store_true",
                     help="also target cb_common.QUARANTINED_BLOBS (urlblob) on escalation")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--stage1-trials", type=int, default=500)
    ap.add_argument("--stage2-trials", type=int, default=5000)
    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        return

    if args.diagnostics_only:
        for target in TARGET_STREAMS:
            diagnostic_report(target)
        return

    k = calibrate_k()
    blobs = {**BLOBS, **QUARANTINED_BLOBS} if args.include_quarantined else None

    for target in TARGET_STREAMS:
        result = run_staged_gate(
            target, k, workers=args.workers,
            trials_1=args.stage1_trials, trials_2=args.stage2_trials,
        )
        if result["advanced"] and result["significant"]:
            escalate(target, k, blobs=blobs)


if __name__ == "__main__":
    main()
