#!/usr/bin/env python3
"""Token-preserving (code-level) shuffled-null check for the FAED
monoalphabetic hill-climb (faed_monoalphabetic_sweep.py), for a chosen
ordered escape pair -- (h,e) by default, generalized (Phase 112) to also
support (g,i) after a real bug in checkerboard_code_ic_oracle.py (ranking by
largest code-IC instead of distance from English's 0.067) was corrected and
the corrected statistic independently ranked (g,i) 1st of 36 pairs for FAED.
Phase 43 only ever ran this null check under (h,e); this generalization adds
the (g,i) case rather than duplicating the file.

The first null attempt in this investigation shuffled FAED's raw a-i
SYMBOLS before re-segmenting -- the same class of bug this project's own
FINDINGS.md already flagged once (Phase 19, dual-quinary): shuffling
pre-segmentation symbols changes segmentation itself, so the null draws
solved a DIFFERENT-shaped problem than the real ciphertext (verified:
469/25 real vs 474/24, 472/25, and one outright dangling-escape failure
across 3 draws -- not even the same code count/type profile, let alone
random-within-cipher rearrangements of it).

This module segments FAED into its real 469 codes under (h,e) ONCE, then
shuffles the CODE LIST itself (not raw symbols) and rejoins by
concatenation. Since every code is a self-terminating unit under (h,e)'s
segmentation rule (an escape symbol always consumes exactly the following
symbol, regardless of what it is), concatenating codes in ANY order
re-segments to the exact same multiset -- every null draw is guaranteed
469 codes / 25 types by construction, not just approximately so (checked,
not assumed: an external independent re-check found 1000/1000 exact across
1000 shuffles).

Per the reviewed recommendation: one canonical variant ((h,e,top_first) --
matches the already-validated 3.2.2 layout and is, per the proven
variant-isomorphism, exchangeable with the other 3 anyway), same total
800-restart budget as the real run, run as one job per trial rather than
split across variants.

**Optimizer-seed symmetry** (fixed after a second review round): the
OPTIMIZER's random-restart seed schedule is identical across the real run
and every null trial -- only the SHUFFLE seed (which permutation of the
469 codes a given trial searches) varies. Without this, a null trial's
score reflects two combined sources of variance (shuffle + optimizer luck)
while the real run reflects neither, which folds optimizer variance
asymmetrically into the resulting p-value.

**Checkpointing**: each trial's (shuffle_seed, score, decode) is appended to
a JSONL file as soon as it completes, and a rerun with the same
--checkpoint path skips shuffle seeds already recorded there -- an
interrupted hour-long run doesn't lose completed trials.

**Checkpoint fingerprinting** (added after a third review round -- the
first fingerprint-less version could silently reuse results from an
incompatible run: different iters/restarts/workers/optimizer-seed produce a
different search, and a stale checkpoint left in place after a config
change would be loaded without any check). The first line of a checkpoint
file is a header record covering everything that affects what a trial's
score means: FAED's own content hash (catches data.py drift), the escape
pair/topology, optimizer seed, iters, restarts, worker count (changes the
per-chunk restart-seed schedule -- see run_one_trial), and this module's
SCHEMA_VERSION (bump on any change to segmentation/scoring/shuffle logic).
A checkpoint whose header doesn't match the current run's config is
rejected outright (raises), never silently loaded or silently ignored. A
truncated final line (e.g. from a crash mid-write) is dropped with a
warning, not treated as a fatal error.

**Staged significance design + gated AES escalation** (added after a review
round): trial counts are no longer a free CLI parameter -- they follow the
pre-registered staged design (STAGE_1_TRIALS, extending to STAGE_2_TRIALS
only on zero exceedances; see staged_null_test()) so escalation decisions
can't be tuned post-hoc by rerunning with a different n_trials. The full
pipeline (run_gated_recovery()) persists a gate-decision record, then (only
if it passes) a deduped top-N candidate list from the EXACT real search used
for the null comparison, then per-candidate AES-oracle completion records,
each written before the next step begins -- see escalation_fingerprint()/
load_escalation_state() for the same fingerprint-or-refuse discipline as the
null checkpoint.

Usage:
    python3 tools/gsmg/faed_token_null_check.py [restarts] [iters] [workers] --pair g,i
    python3 tools/gsmg/faed_token_null_check.py --self-test
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import platform
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import FAED  # noqa: E402
from prefix_boundary_sweep import segment_codes  # noqa: E402
import prefix_boundary_sweep  # noqa: E402
import quadgram_solver  # noqa: E402
from quadgram_solver import hillclimb, QUADGRAM_FILE  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    answer_forms,
    keystr_forms,
)
import cb_common  # noqa: E402

REAL_CODE_COUNTS = {
    ("h", "e"): 469,  # Phase 43
    ("g", "i"): 436,  # Phase 43's corrected exhaustive scan
}
REAL_TYPE_COUNT = 25
DEFAULT_PAIR = ("h", "e")
CANONICAL_VARIANT = (DEFAULT_PAIR[0], DEFAULT_PAIR[1], "top_first")  # backward compatibility
OPTIMIZER_SEED = 2000  # fixed for every trial, real and null alike -- see module docstring
DEFAULT_CHECKPOINT = SCRIPT_DIR / "faed_token_null_checkpoint.jsonl"
SCHEMA_VERSION = 2  # bumped: added source/data hashes + python_version to config_fingerprint
FAED_HASH = hashlib.sha256(FAED.encode()).hexdigest()[:16]

# Staged, pre-registered significance design (see module docstring "Staged
# significance design" section): fixed BEFORE any trial's result is known,
# so extending past stage 1 is never a post-hoc "it looked promising, keep
# going" decision -- it fires only on the single pre-declared condition
# (zero exceedances at n=100), which is checked mechanically.
STAGE_1_TRIALS = 100
STAGE_2_TRIALS = 1000
SIGNIFICANCE_P = 0.005


def _hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


# Every file whose content affects what a trial's SCORE means: the scoring
# table itself (a change to quadgram frequencies changes every score), the
# segmentation rule, the hillclimb/search implementation, and this module's
# own shuffle/trial-orchestration logic. FAED_HASH (the ciphertext data)
# is tracked separately below since it's a different kind of dependency
# (input data, not code/scoring-table).
SEARCH_SOURCE_FILES = {
    "quadgram_solver.py": Path(quadgram_solver.__file__),
    "prefix_boundary_sweep.py": Path(prefix_boundary_sweep.__file__),
    "faed_token_null_check.py": Path(__file__),
    "english_quadgrams.txt": Path(QUADGRAM_FILE),
}
SOURCE_HASHES = {name: _hash_file(path) for name, path in SEARCH_SOURCE_FILES.items()}
PYTHON_VERSION = platform.python_version()


def checkpoint_path_for_pair(pair, base=DEFAULT_CHECKPOINT):
    """(h,e) keeps the original filename (backward compatible with any
    existing checkpoint on disk); any other pair gets its own suffixed file
    so two pairs' trial runs can never be silently mixed into one
    checkpoint."""
    if pair == DEFAULT_PAIR:
        return base
    return base.with_name(f"{base.stem}_{pair[0]}{pair[1]}{base.suffix}")


def config_fingerprint(iters, restarts, workers, optimizer_seed=OPTIMIZER_SEED, pair=DEFAULT_PAIR):
    e1, e2 = pair
    return {
        "schema_version": SCHEMA_VERSION,
        "faed_hash": FAED_HASH,
        "escape_pair": [e1, e2],
        "topology": "top_first",
        "optimizer_seed": optimizer_seed,
        "iters": iters,
        "restarts": restarts,
        "workers": workers,
        "source_hashes": SOURCE_HASHES,
        "python_version": PYTHON_VERSION,
    }


def real_codes(pair=DEFAULT_PAIR):
    e1, e2 = pair
    codes = segment_codes(FAED, e1, e2)
    expected_count = REAL_CODE_COUNTS[pair]
    assert len(codes) == expected_count and len(set(codes)) == REAL_TYPE_COUNT
    return codes


def shuffled_ciphertext(codes, rng, pair=DEFAULT_PAIR):
    """Shuffles the CODE LIST (not raw symbols) and rejoins by concatenation.
    Guaranteed to re-segment to the same code count/type profile -- verified
    by the caller's own assertion, not assumed."""
    e1, e2 = pair
    shuffled = codes[:]
    rng.shuffle(shuffled)
    rejoined = "".join(shuffled)
    check = segment_codes(rejoined, e1, e2)
    assert check == shuffled, (
        "rejoined string did not re-segment to the shuffled code list -- "
        "code-boundary assumption violated"
    )
    return rejoined


def _restart_chunk(args):
    """One worker's share of ONE trial's restarts -- restarts is split across
    workers WITHIN a trial (not one worker per trial), since a single-process
    800-restart/4000-iter climb is the slow path (timed at >300s serial vs.
    ~45s at a 16-way split for the same 800 total restarts elsewhere in this
    investigation). Only returns the FULL per-restart results list (not just
    this chunk's winner) when collect_all is set -- otherwise every one of
    the ~100-1000 null trials would pickle every restart's full decode
    string back across the process boundary for no reason (they only ever
    need a single score), adding IPC/memory cost with nothing to show for
    it. collect_all is True only for the single real-ciphertext call that
    actually needs every local optimum for candidate selection."""
    ct, e1, e2, topo, iters, count, seed, collect_all = args
    best, results = hillclimb(ct, e1, e2, topo, iters=iters, restarts=count, seed=seed)
    if collect_all:
        return best[0], best[1], best[2], results
    return best[0], best[1], best[2], None


def run_one_trial(ct, iters, restarts, seed, workers, pair=DEFAULT_PAIR, collect_all=False):
    """Runs the pair's top_first hill-climb against `ct` with a total restart
    budget of `restarts`, split across `workers` processes, using `seed` as
    the base for the internal per-chunk restart-seed schedule. Returns
    (best_score, best_decode, best_key) by default, or
    (best_score, best_decode, best_key, all_results) if collect_all=True,
    where all_results is the (score, decode, key26) tuple for EVERY restart
    across every worker -- not just each worker's own winner. Callers that
    want optimizer-seed symmetry across trials must pass the SAME `seed`
    every time -- only `ct` should vary between the real run and null
    trials."""
    e1, e2, topo = pair[0], pair[1], "top_first"
    if workers <= 1:
        best, results = hillclimb(ct, e1, e2, topo, iters=iters, restarts=restarts, seed=seed)
        if collect_all:
            return best[0], best[1], best[2], results
        return best[0], best[1], best[2]

    per_worker = max(1, restarts // workers)
    jobs = []
    remaining = restarts
    s = seed
    while remaining > 0:
        n = min(per_worker, remaining)
        jobs.append((ct, e1, e2, topo, iters, n, s, collect_all))
        s += 1
        remaining -= n
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        chunk_outputs = list(ex.map(_restart_chunk, jobs))
    best_score, best_decode, best_key, _ = max(chunk_outputs, key=lambda c: c[0])
    if collect_all:
        all_results = [r for _, _, _, results in chunk_outputs for r in results]
        return best_score, best_decode, best_key, all_results
    return best_score, best_decode, best_key


def real_best_score(iters, restarts, workers=1, optimizer_seed=OPTIMIZER_SEED, pair=DEFAULT_PAIR,
                     collect_all=False):
    """Same canonical-variant / same-total-restarts search on the REAL
    ciphertext, for a same-procedure comparison point (not the 4-variant/
    800-total-restart number from faed_monoalphabetic_sweep.py, which split
    budget across provably-isomorphic variants -- this is the single-variant
    equivalent so trial and real runs use literally the same code path).
    Uses the same OPTIMIZER_SEED as every null trial -- see module docstring.
    collect_all=True additionally returns every restart's local optimum
    (for deduped top-N candidate selection FROM THIS EXACT SEARCH, rather
    than from faed_monoalphabetic_sweep.py's separate 4-variant sweep, which
    would silently change optimizer exposure and candidate provenance)."""
    return run_one_trial(FAED, iters, restarts, optimizer_seed, workers, pair=pair,
                          collect_all=collect_all)


def dedup_top_n(results, top_n):
    """Dedupes (score, decode, key26) tuples by decode string, keeping the
    highest score seen for each unique decode, then returns the top_n
    entries ordered deterministically by (-score, decode) -- independent of
    worker-completion order or dict/set iteration order. Mirrors the
    dedup-before-slicing lesson from faed_monoalphabetic_sweep.py's
    escalation loop (Phase 43): slicing to top_n BEFORE deduping was found
    to lose real candidates to duplicate near-isomorphic decodes."""
    best_by_decode = {}
    for score_, decode, key in results:
        prior = best_by_decode.get(decode)
        if prior is None or score_ > prior[0]:
            best_by_decode[decode] = (score_, decode, key)
    ordered = sorted(best_by_decode.values(), key=lambda r: (-r[0], r[1]))
    return ordered[:top_n]


class CheckpointMismatch(Exception):
    pass


def load_checkpoint(path, expected_fingerprint):
    """seed -> (score, decode) already recorded, if the file exists and its
    header fingerprint matches expected_fingerprint exactly. Raises
    CheckpointMismatch (never silently ignores or silently loads) if the
    file exists but its header doesn't match or is missing/malformed -- the
    caller decides what to do (this module's CLI refuses to proceed).
    A truncated final line (crash mid-write) is dropped with a warning."""
    done = {}
    if not path.exists():
        return done
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]
    if not lines:
        return done
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError:
        raise CheckpointMismatch(f"{path}: header line is not valid JSON -- refusing to load")
    if header != {"header": True, **expected_fingerprint}:
        raise CheckpointMismatch(
            f"{path}: checkpoint header does not match the current run's config.\n"
            f"  checkpoint header: {header}\n"
            f"  expected:          {{'header': True, **{expected_fingerprint}}}\n"
            f"Refusing to reuse it -- delete or move the file, or use a different "
            f"--checkpoint path, if this config change is intentional."
        )
    for i, line in enumerate(lines[1:], start=2):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            print(f"[!] {path}: line {i} is truncated/invalid JSON (likely a crash "
                  f"mid-write) -- dropping it, not treating as fatal")
            continue
        done[rec["shuffle_seed"]] = (rec["score"], rec["decode"])
    return done


def append_checkpoint(path, shuffle_seed, score, decode, fingerprint):
    # not path.exists() alone misses the case where the file exists but is
    # empty (e.g. created by `touch`, or truncated by an interrupted prior
    # run) -- that left an in-the-wild checkpoint with 100 trial records and
    # ZERO header lines, silently defeating the config-fingerprint check for
    # any future resume against that file.
    is_new = not path.exists() or path.stat().st_size == 0
    with open(path, "a") as f:
        if is_new:
            f.write(json.dumps({"header": True, **fingerprint}) + "\n")
        f.write(json.dumps({"shuffle_seed": shuffle_seed, "score": score, "decode": decode}) + "\n")


def run_null_trials(n_trials, iters, restarts, seed_base, workers=1,
                     optimizer_seed=OPTIMIZER_SEED, checkpoint_path=None, pair=DEFAULT_PAIR):
    codes = real_codes(pair=pair)
    code_count = REAL_CODE_COUNTS[pair]
    fingerprint = config_fingerprint(iters, restarts, workers, optimizer_seed, pair=pair)
    done = load_checkpoint(checkpoint_path, fingerprint) if checkpoint_path else {}
    scores = []
    for i in range(n_trials):
        shuffle_seed = seed_base + i
        if shuffle_seed in done:
            s, _ = done[shuffle_seed]
            scores.append(s)
            print(f"  [{i + 1}/{n_trials}] (from checkpoint) shuffle_seed={shuffle_seed} "
                  f"score={s:.1f} per_char={s / code_count:.4f}")
            continue
        rng = random.Random(shuffle_seed)
        ct = shuffled_ciphertext(codes, rng, pair=pair)
        # Fixed optimizer_seed on every trial -- only `ct` (the shuffle) varies.
        s, d, _key = run_one_trial(ct, iters, restarts, optimizer_seed, workers, pair=pair)
        scores.append(s)
        if checkpoint_path:
            append_checkpoint(checkpoint_path, shuffle_seed, s, d, fingerprint)
        print(f"  [{i + 1}/{n_trials}] shuffle_seed={shuffle_seed} "
              f"score={s:.1f} per_char={s / code_count:.4f}")
    return scores


def empirical_p(real_score, null_scores):
    at_least_as_good = sum(1 for s in null_scores if s >= real_score)
    return at_least_as_good, (at_least_as_good + 1) / (len(null_scores) + 1)


def staged_null_test(iters, restarts, seed_base, workers, checkpoint_path, pair=DEFAULT_PAIR,
                      stage_1_trials=STAGE_1_TRIALS, stage_2_trials=STAGE_2_TRIALS,
                      significance_p=SIGNIFICANCE_P):
    """Pre-registered staged significance design: run stage_1_trials null
    trials first. If ANY null trial ties or beats the real score
    (exceedances > 0), stop here and report negative at this resolution --
    at the production n=100 the best possible p is 1/101~=0.0099, already
    above the project's default p<0.005 bar, so that case can never pass
    regardless. Only if stage 1 produces ZERO exceedances (hitting that
    resolution floor) does the design extend to stage_2_trials total trials
    (same checkpoint, continuing the shuffle-seed sequence, so no completed
    work is repeated) to get enough resolution to actually test the
    significance bar. This is a single fixed rule evaluated mechanically,
    not a judgment call made after seeing results -- that is what keeps it
    free of optional-stopping bias. stage_1_trials/stage_2_trials/
    significance_p default to the frozen production design (100/1000/0.005)
    but are parameterized so self_test can exercise both branches with a
    tiny synthetic budget instead of waiting on a real multi-hour run.

    Returns a dict: real_score, real_decode, real_key, real_results (every
    restart's local optimum from the SAME real search, for candidate
    selection), trial_count, exceedances, empirical_p, decision, null_scores."""
    real_score, real_decode, real_key, real_results = real_best_score(
        iters=iters, restarts=restarts, workers=workers, pair=pair, collect_all=True
    )

    stage1_scores = run_null_trials(stage_1_trials, iters, restarts, seed_base, workers,
                                     checkpoint_path=checkpoint_path, pair=pair)
    exceedances, p = empirical_p(real_score, stage1_scores)
    trial_count = stage_1_trials
    null_scores = stage1_scores

    if exceedances == 0:
        stage2_scores = run_null_trials(stage_2_trials, iters, restarts, seed_base, workers,
                                         checkpoint_path=checkpoint_path, pair=pair)
        exceedances, p = empirical_p(real_score, stage2_scores)
        trial_count = stage_2_trials
        null_scores = stage2_scores

    decision = "pass" if p < significance_p else "fail"
    return {
        "real_score": real_score,
        "real_decode": real_decode,
        "real_key": "".join(real_key),
        "real_results": real_results,
        "trial_count": trial_count,
        "exceedances": exceedances,
        "empirical_p": p,
        "decision": decision,
        "null_scores": null_scores,
    }


DEFAULT_ESCALATION_RESULT = SCRIPT_DIR / "faed_escalation_result.jsonl"
CB_COMMON_HASH = _hash_file(Path(cb_common.__file__))
# Matches faed_monoalphabetic_sweep.py's existing escalation loop (Phase 43)
# exactly: keystr_forms(form) called WITHOUT newline_variants=True (unlike
# some other scripts in this project that do pass True) -- recorded
# explicitly here so the policy is bound, not just implicit.
NEWLINE_VARIANTS_POLICY = False
CIPHER_FAMILIES = ["cbc_legacy", "cbc_extended", "keywrap"]


def escalation_result_path_for_pair(pair, base=DEFAULT_ESCALATION_RESULT):
    if pair == DEFAULT_PAIR:
        return base
    return base.with_name(f"{base.stem}_{pair[0]}{pair[1]}{base.suffix}")


def _hash_blobs(blob_dict):
    parts = [tag.encode() + salt + ct for tag, (salt, ct) in sorted(blob_dict.items())]
    return hashlib.sha256(b"".join(parts)).hexdigest()[:16]


def escalation_fingerprint(top_n, include_quarantined, null_fingerprint, seed_base,
                            stage_1_trials=STAGE_1_TRIALS, stage_2_trials=STAGE_2_TRIALS,
                            significance_p=SIGNIFICANCE_P):
    """seed_base is bound explicitly here (not just folded into
    null_config_fingerprint, which never included it) -- config_fingerprint()
    covers what makes a single TRIAL's score meaningful (iters/restarts/
    workers/pair/optimizer_seed/source hashes), but two runs with identical
    config and DIFFERENT seed_base draw a completely different null sequence
    and can legitimately produce a different real-vs-null outcome. Without
    this, a gate artifact computed under one seed_base could be silently
    reused by a later invocation that only changed seed_base -- the exact
    review-caught gap this closes. See run_gated_recovery for the separate,
    complementary checkpoint-content-hash check bound into the gate_decision
    record itself (this fingerprint alone can't catch a checkpoint that was
    corrupted/hand-edited between runs without also changing seed_base)."""
    blobs = {**BLOBS, **QUARANTINED_BLOBS} if include_quarantined else dict(BLOBS)
    return {
        "top_n": top_n,
        "blob_tags": sorted(blobs),
        "blob_hash": _hash_blobs(blobs),
        "include_quarantined": include_quarantined,
        "cipher_families": CIPHER_FAMILIES,
        "answer_forms": "cb_common.answer_forms",
        "keystr_forms_newline_variants": NEWLINE_VARIANTS_POLICY,
        "significance_p": significance_p,
        "stage_trial_counts": [stage_1_trials, stage_2_trials],
        "seed_base": seed_base,
        "null_config_fingerprint": null_fingerprint,
        "cb_common_hash": CB_COMMON_HASH,
        "python_version": PYTHON_VERSION,
    }


class EscalationMismatch(Exception):
    pass


def load_escalation_state(path, expected_header):
    """Returns (gate_record, candidates, completed) from an existing
    escalation-result artifact, or (None, None, {}) if it doesn't exist yet.
    completed maps decode -> its candidate_completion record (hits+attempts),
    so a resumed run can tell "tested, zero hits" apart from "not yet
    reached." Raises EscalationMismatch (never silently reused) if the file
    exists but its header doesn't match expected_header -- same discipline
    as the null checkpoint's own fingerprint check."""
    gate_record, candidates, completed = None, None, {}
    if not path.exists() or path.stat().st_size == 0:
        return gate_record, candidates, completed
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]
    if not lines:
        return gate_record, candidates, completed
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError:
        raise EscalationMismatch(f"{path}: header line is not valid JSON -- refusing to load")
    if header != {"record": "header", **expected_header}:
        raise EscalationMismatch(
            f"{path}: escalation result header does not match the current run's config.\n"
            f"  file header: {header}\n"
            f"  expected:    {{'record': 'header', **{expected_header}}}\n"
            f"Refusing to reuse it -- delete or move the file, or use a different "
            f"path, if this config change is intentional."
        )
    for i, line in enumerate(lines[1:], start=2):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            print(f"[!] {path}: line {i} is truncated/invalid JSON -- dropping it, not treating as fatal")
            continue
        if rec.get("record") == "gate_decision":
            gate_record = rec
        elif rec.get("record") == "candidates":
            candidates = rec["candidates"]
        elif rec.get("record") == "candidate_completion":
            completed[rec["decode"]] = rec
    return gate_record, candidates, completed


def append_escalation_record(path, record, header):
    is_new = not path.exists() or path.stat().st_size == 0
    with open(path, "a") as f:
        if is_new:
            f.write(json.dumps({"record": "header", **header}) + "\n")
        f.write(json.dumps(record) + "\n")


def _serialize_cbc_hit(tag, body, kdf_label, key_len, family):
    return {"family": family, "tag": tag, "kdf_label": kdf_label, "key_len": key_len,
            "plaintext_hex": body.hex()}


def _serialize_keywrap_hit(tag, wrap_kind, kdf_label, key_len, unwrapped):
    return {"family": "keywrap", "tag": tag, "wrap_kind": wrap_kind, "kdf_label": kdf_label,
            "key_len": key_len, "unwrapped_hex": unwrapped.hex()}


def _build_and_write_candidates(escalation_path, esc_fp, real_results, top_n):
    top = dedup_top_n(real_results, top_n)
    candidates = [
        {"rank": i + 1, "score": s, "decode": d, "key": "".join(k)}
        for i, (s, d, k) in enumerate(top)
    ]
    append_escalation_record(
        escalation_path, {"record": "candidates", "candidates": candidates}, esc_fp
    )
    return candidates


def run_gated_recovery(iters, restarts, seed_base, workers, pair=DEFAULT_PAIR,
                        checkpoint_path=None, escalation_path=None,
                        top_n=20, include_quarantined=False,
                        stage_1_trials=STAGE_1_TRIALS, stage_2_trials=STAGE_2_TRIALS,
                        significance_p=SIGNIFICANCE_P):
    """End-to-end: staged null test -> gate-decision record -> (only if
    pass) deduped top-N candidates from the EXACT real search used for the
    null comparison -> idempotent AES-oracle escalation of those unchanged
    candidates. Every step is persisted before the next begins, so an
    interruption at any point leaves an auditable, resumable record.
    stage_1_trials/stage_2_trials/significance_p default to the frozen
    production design; overriding them is for self_test's synthetic-budget
    coverage only, and the override is itself part of esc_fp below, so a
    real run can never silently reuse an artifact produced under different
    staging parameters.

    The gate_decision record also carries a checkpoint_content_hash --
    esc_fp alone binds the CONFIG that was intended (seed_base included),
    but not the actual on-disk null-checkpoint DATA a resumed run reads;
    re-verifying this hash on every load catches a checkpoint that was
    corrupted, hand-edited, or replaced between runs even when esc_fp still
    matches bit-for-bit."""
    checkpoint_path = checkpoint_path or checkpoint_path_for_pair(pair)
    escalation_path = escalation_path or escalation_result_path_for_pair(pair)

    null_fp = config_fingerprint(iters, restarts, workers, OPTIMIZER_SEED, pair=pair)
    esc_fp = escalation_fingerprint(top_n, include_quarantined, null_fp, seed_base,
                                     stage_1_trials, stage_2_trials, significance_p)

    gate_record, candidates, completed = load_escalation_state(escalation_path, esc_fp)

    if gate_record is None:
        staged = staged_null_test(iters, restarts, seed_base, workers, checkpoint_path, pair=pair,
                                   stage_1_trials=stage_1_trials, stage_2_trials=stage_2_trials,
                                   significance_p=significance_p)
        gate_record = {
            "record": "gate_decision",
            "real_score": staged["real_score"],
            "exceedances": staged["exceedances"],
            "trial_count": staged["trial_count"],
            "empirical_p": staged["empirical_p"],
            "decision": staged["decision"],
            "checkpoint_content_hash": _hash_file(checkpoint_path),
        }
        append_escalation_record(escalation_path, gate_record, esc_fp)
        print(f"[*] gate decision: {gate_record}")

        if staged["decision"] == "pass":
            candidates = _build_and_write_candidates(
                escalation_path, esc_fp, staged["real_results"], top_n
            )
    else:
        print(f"[*] gate decision already recorded: {gate_record}")
        current_hash = _hash_file(checkpoint_path)
        if current_hash != gate_record["checkpoint_content_hash"]:
            raise EscalationMismatch(
                f"{escalation_path}: recorded gate_decision was computed against a "
                f"null checkpoint whose content hash was {gate_record['checkpoint_content_hash']!r}, "
                f"but {checkpoint_path} currently hashes to {current_hash!r}. Refusing to "
                f"reuse this gate decision -- the checkpoint was modified, corrupted, or "
                f"replaced since it was computed."
            )
        if gate_record["decision"] == "pass" and candidates is None:
            # Resumed after the gate record was written but before the
            # candidates record was -- real_results themselves were never
            # persisted (only used transiently to build candidates), so
            # regenerate them via a fresh real search. Deterministic: same
            # iters/restarts/workers/pair/OPTIMIZER_SEED reproduces the
            # identical real_score/real_results, so this is not a silent
            # re-decision, just recomputing data that was never written.
            print("[*] gate passed but the candidates record is missing (interrupted "
                  "between the two writes) -- recomputing the real search "
                  "(deterministic, same seed) to regenerate candidates...")
            _, _, _, real_results = real_best_score(
                iters=iters, restarts=restarts, workers=workers, pair=pair,
                optimizer_seed=OPTIMIZER_SEED, collect_all=True,
            )
            candidates = _build_and_write_candidates(escalation_path, esc_fp, real_results, top_n)

    if gate_record["decision"] != "pass":
        print("[*] gate FAILED -- no AES escalation performed.")
        return gate_record, candidates, []

    blobs = {**BLOBS, **QUARANTINED_BLOBS} if include_quarantined else dict(BLOBS)
    all_hits = []
    for cand in candidates:
        decode = cand["decode"]
        if decode in completed:
            prior = completed[decode]
            print(f"[*] candidate rank={cand['rank']} already tested "
                  f"(hits={len(prior['hits'])}, attempts={prior['attempts']})")
            all_hits.extend(prior["hits"])
            continue
        hits = []
        attempts = 0
        for form in sorted(answer_forms(decode)):
            for keystr in keystr_forms(form, newline_variants=NEWLINE_VARIANTS_POLICY):
                attempts += 1
                for kdf_variants, family in ((None, "cbc_legacy"), (EXTENDED_CIPHER_VARIANTS, "cbc_extended")):
                    r = aes_try_open(keystr, kdf_variants=kdf_variants, blobs=blobs)
                    if r:
                        hits.append(_serialize_cbc_hit(r[0], r[1], r[2], r[3], family))
                for r2 in aes_keywrap_try_open_bytes(keystr.encode(), blobs=blobs):
                    hits.append(_serialize_keywrap_hit(r2[0], r2[1], r2[2], r2[3], r2[4]))
        completion = {
            "record": "candidate_completion", "rank": cand["rank"], "decode": decode,
            "hits": hits, "attempts": attempts,
        }
        append_escalation_record(escalation_path, completion, esc_fp)
        if hits:
            escalation_path.chmod(0o600)
        completed[decode] = completion
        all_hits.extend(hits)
        print(f"[*] candidate rank={cand['rank']} tested: attempts={attempts} hits={len(hits)}")

    return gate_record, candidates, all_hits


def self_test():
    global run_null_trials
    codes = real_codes()
    rng = random.Random(1)
    ct = shuffled_ciphertext(codes, rng)
    assert ct != "".join(codes), "shuffle produced the identity permutation (astronomically unlikely, check rng)"
    reseg = segment_codes(ct, "h", "e")
    assert len(reseg) == REAL_CODE_COUNTS[DEFAULT_PAIR] and len(set(reseg)) == REAL_TYPE_COUNT, (
        f"self-test FAILED: shuffled-rejoined ciphertext does not preserve "
        f"the real profile: codes={len(reseg)} types={len(set(reseg))}"
    )
    real_score, real_decode, _real_key = real_best_score(iters=20, restarts=2)
    assert len(real_decode) == REAL_CODE_COUNTS[DEFAULT_PAIR]

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        ckpt = Path(tmp) / "ckpt.jsonl"
        null_scores = run_null_trials(n_trials=2, iters=20, restarts=2, seed_base=1,
                                       workers=1, checkpoint_path=ckpt)
        assert len(null_scores) == 2
        assert ckpt.exists()
        # Resume: rerunning with the same checkpoint must reproduce identical
        # scores from disk, not recompute (checkpoint round-trip check).
        resumed_scores = run_null_trials(n_trials=2, iters=20, restarts=2, seed_base=1,
                                          workers=1, checkpoint_path=ckpt)
        assert resumed_scores == null_scores, "checkpoint resume did not reproduce identical scores"

        # A config change (different restarts) against the SAME checkpoint
        # path must be REJECTED, not silently loaded or silently recomputed.
        try:
            run_null_trials(n_trials=2, iters=20, restarts=4, seed_base=1,
                             workers=1, checkpoint_path=ckpt)
        except CheckpointMismatch:
            pass
        else:
            raise AssertionError("self-test FAILED: mismatched-config checkpoint was not rejected")

        # A truncated final line (simulated crash mid-write) must be dropped
        # with a warning, not crash the load or silently corrupt scores.
        with open(ckpt, "a") as f:
            f.write('{"shuffle_seed": 999, "score": -1.0, "dec')  # deliberately truncated, no newline
        truncated_done = load_checkpoint(ckpt, config_fingerprint(20, 2, 1, OPTIMIZER_SEED))
        assert 999 not in truncated_done, "self-test FAILED: truncated line was not dropped"
        assert len(truncated_done) == 2, "self-test FAILED: truncated line handling corrupted valid records"

        # An existing-but-EMPTY checkpoint file (e.g. `touch`ed or truncated
        # by an interrupted run) must still get a header on first append --
        # path.exists() alone is True for an empty file too.
        empty_ckpt = Path(tmp) / "empty.jsonl"
        empty_ckpt.touch()
        assert empty_ckpt.exists() and empty_ckpt.stat().st_size == 0
        run_null_trials(n_trials=1, iters=20, restarts=2, seed_base=1,
                         workers=1, checkpoint_path=empty_ckpt)
        first_line = json.loads(empty_ckpt.read_text().splitlines()[0])
        assert first_line.get("header") is True, (
            "self-test FAILED: no header written when starting from an "
            "existing-but-empty checkpoint file"
        )

    hits, p = empirical_p(real_score, null_scores)
    assert 0 <= p <= 1

    # (g,i) pair (Phase 112): a smaller, targeted check that the generalized
    # path actually works end-to-end -- not a full duplicate of every
    # checkpoint-edge-case test above, which is pair-agnostic machinery
    # already covered once.
    gi_codes = real_codes(pair=("g", "i"))
    assert len(gi_codes) == REAL_CODE_COUNTS[("g", "i")]
    gi_rng = random.Random(1)
    gi_ct = shuffled_ciphertext(gi_codes, gi_rng, pair=("g", "i"))
    gi_reseg = segment_codes(gi_ct, "g", "i")
    assert len(gi_reseg) == REAL_CODE_COUNTS[("g", "i")] and len(set(gi_reseg)) == REAL_TYPE_COUNT
    with tempfile.TemporaryDirectory() as tmp:
        gi_ckpt = Path(tmp) / "gi_ckpt.jsonl"
        gi_real_score, gi_real_decode, _gi_real_key = real_best_score(iters=20, restarts=2, pair=("g", "i"))
        assert len(gi_real_decode) == REAL_CODE_COUNTS[("g", "i")]
        gi_null_scores = run_null_trials(n_trials=2, iters=20, restarts=2, seed_base=1,
                                          workers=1, checkpoint_path=gi_ckpt, pair=("g", "i"))
        assert len(gi_null_scores) == 2
        # A checkpoint fingerprinted for (h,e) must be rejected under (g,i)
        # (different escape_pair in the fingerprint) -- pairs must never be
        # silently mixed into the same checkpoint file.
        mismatched_pair_ckpt = Path(tmp) / "mismatched_pair.jsonl"
        run_null_trials(n_trials=1, iters=20, restarts=2, seed_base=1,
                         workers=1, checkpoint_path=mismatched_pair_ckpt, pair=DEFAULT_PAIR)
        try:
            run_null_trials(n_trials=1, iters=20, restarts=2, seed_base=1,
                             workers=1, checkpoint_path=mismatched_pair_ckpt, pair=("g", "i"))
        except CheckpointMismatch:
            pass
        else:
            raise AssertionError("self-test FAILED: cross-pair checkpoint reuse was not rejected")

    # dedup_top_n: duplicate decodes keep only their highest score, ordering
    # is (-score, decode) regardless of input order.
    fake_results = [
        (-100.0, "AAA", list("keyA")),
        (-50.0, "BBB", list("keyB1")),
        (-60.0, "BBB", list("keyB2")),  # worse duplicate of BBB -- must be dropped
        (-50.0, "CCC", list("keyC")),   # ties BBB's score -- decode breaks the tie
    ]
    top = dedup_top_n(fake_results, top_n=10)
    assert [d for _, d, _ in top] == ["BBB", "CCC", "AAA"], (
        f"self-test FAILED: dedup_top_n ordering/dedup wrong: {top}"
    )
    assert dedup_top_n(fake_results, top_n=1) == [(-50.0, "BBB", list("keyB1"))]

    # Staged design branching, via a monkeypatched run_null_trials (safe
    # here: staged_null_test never crosses a process boundary itself, only
    # hillclimb's own workers>1 path does, and this sub-test forces
    # workers=1) -- exercises BOTH pre-registered branches deterministically
    # without waiting on a real 100/1000-trial run.
    _orig_run_null_trials = run_null_trials
    try:
        # Case A: stage 1 (n=2) has an exceedance -> must stop at
        # trial_count=2, decision=fail, stage 2 (n=4) never invoked.
        def _fake_exceedance(n_trials, iters, restarts, seed_base, workers=1,
                              optimizer_seed=OPTIMIZER_SEED, checkpoint_path=None, pair=DEFAULT_PAIR):
            assert n_trials == 2, "stage 2 must not be invoked when stage 1 has an exceedance"
            return [1e9, 1e9]  # far above any real quadgram score -> exceedances=2

        globals()["run_null_trials"] = _fake_exceedance
        result_a = staged_null_test(iters=20, restarts=2, seed_base=1, workers=1,
                                     checkpoint_path=None, pair=DEFAULT_PAIR,
                                     stage_1_trials=2, stage_2_trials=4, significance_p=0.4)
        assert result_a["trial_count"] == 2, "self-test FAILED: stage 1 exceedance did not stop at n=2"
        assert result_a["exceedances"] == 2
        assert result_a["decision"] == "fail"

        # Case B: stage 1 (n=2) has ZERO exceedances -> must extend to stage
        # 2 (n=4), and the FINAL decision must come from stage 2's p, not
        # stage 1's.
        stage_calls = []

        def _fake_extend(n_trials, iters, restarts, seed_base, workers=1,
                          optimizer_seed=OPTIMIZER_SEED, checkpoint_path=None, pair=DEFAULT_PAIR):
            stage_calls.append(n_trials)
            return [-1e9] * n_trials  # far below any real score -> exceedances=0 at both stages

        globals()["run_null_trials"] = _fake_extend
        result_b = staged_null_test(iters=20, restarts=2, seed_base=1, workers=1,
                                     checkpoint_path=None, pair=DEFAULT_PAIR,
                                     stage_1_trials=2, stage_2_trials=4, significance_p=0.3)
        assert stage_calls == [2, 4], f"self-test FAILED: expected stage1 then stage2 calls, got {stage_calls}"
        assert result_b["trial_count"] == 4
        assert result_b["exceedances"] == 0
        assert result_b["empirical_p"] == 1 / 5
        assert result_b["decision"] == "pass"  # p=0.2 < significance_p=0.3
        assert len(result_b["real_results"]) >= 1, "collect_all did not return per-restart results"
    finally:
        globals()["run_null_trials"] = _orig_run_null_trials

    # Escalation artifact: header/gate/candidates/completion round-trip,
    # cross-config rejection, and idempotent "already tested" skip -- using
    # a forced synthetic "pass" so the candidate/oracle path is actually
    # exercised (the real (g,i) run itself failed the gate, so production
    # use never reaches this code without a synthetic override here).
    with tempfile.TemporaryDirectory() as tmp:
        esc_path = Path(tmp) / "esc.jsonl"
        ckpt_path = Path(tmp) / "esc_ckpt.jsonl"
        gate_record, candidates, hits = run_gated_recovery(
            iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
            checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
            stage_1_trials=2, stage_2_trials=2, significance_p=1.1,  # 1.1: any p<=1 "passes", forcing escalation
        )
        assert gate_record["decision"] == "pass"
        assert esc_path.exists()
        assert 1 <= len(candidates) <= 3
        assert hits == [], "self-test FAILED: synthetic candidates unexpectedly hit a real blob"

        # Resume against the SAME artifact must reuse the recorded gate
        # decision and candidates, not recompute them (idempotent resume).
        gate_record_2, candidates_2, hits_2 = run_gated_recovery(
            iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
            checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
            stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
        )
        assert gate_record_2 == gate_record, "self-test FAILED: resume recomputed the gate decision"
        assert candidates_2 == candidates
        assert hits_2 == hits

        # A config change (different top_n) against the SAME artifact path
        # must be REJECTED, matching the checkpoint's own discipline.
        try:
            run_gated_recovery(
                iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
                checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=5,
                stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
            )
        except EscalationMismatch:
            pass
        else:
            raise AssertionError("self-test FAILED: mismatched escalation config was not rejected")

        # Verify every candidate got a candidate_completion record with
        # hits+attempts (not just silently skipped) -- resumability requires
        # telling "tested, zero hits" apart from "not yet reached."
        _, _, completed = load_escalation_state(
            esc_path,
            escalation_fingerprint(3, False, config_fingerprint(20, 2, 1, OPTIMIZER_SEED, pair=DEFAULT_PAIR),
                                    1, 2, 2, 1.1),
        )
        assert len(completed) == len(candidates)
        for cand in candidates:
            rec = completed[cand["decode"]]
            assert "hits" in rec and "attempts" in rec and rec["attempts"] > 0

    # seed_base is bound into the fingerprint -- a DIFFERENT seed_base
    # against the SAME artifact must be rejected, not silently reused
    # (review-caught gap: seed_base previously had no effect on esc_fp at
    # all, so a rerun with a different null-shuffle sequence could silently
    # inherit a decision computed under a different one).
    with tempfile.TemporaryDirectory() as tmp:
        esc_path = Path(tmp) / "esc.jsonl"
        ckpt_path = Path(tmp) / "esc_ckpt.jsonl"
        run_gated_recovery(
            iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
            checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
            stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
        )
        try:
            run_gated_recovery(
                iters=20, restarts=2, seed_base=2, workers=1, pair=DEFAULT_PAIR,
                checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
                stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
            )
        except EscalationMismatch:
            pass
        else:
            raise AssertionError("self-test FAILED: different seed_base against the same "
                                  "artifact was not rejected")

    # checkpoint_content_hash catches a null checkpoint that changed on disk
    # between runs even when esc_fp itself still matches bit-for-bit.
    with tempfile.TemporaryDirectory() as tmp:
        esc_path = Path(tmp) / "esc.jsonl"
        ckpt_path = Path(tmp) / "esc_ckpt.jsonl"
        run_gated_recovery(
            iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
            checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
            stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
        )
        with open(ckpt_path, "a") as f:
            f.write(json.dumps({"shuffle_seed": 99999, "score": -1.0, "decode": "TAMPERED"}) + "\n")
        try:
            run_gated_recovery(
                iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
                checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
                stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
            )
        except EscalationMismatch:
            pass
        else:
            raise AssertionError("self-test FAILED: a checkpoint that changed on disk after "
                                  "the gate was recorded was not caught")

    # Interruption between writing the gate record and writing the
    # candidates record must be resumable, not crash (review-reproduced
    # TypeError: 'NoneType' object is not iterable).
    with tempfile.TemporaryDirectory() as tmp:
        esc_path = Path(tmp) / "esc.jsonl"
        ckpt_path = Path(tmp) / "esc_ckpt.jsonl"
        null_fp2 = config_fingerprint(20, 2, 1, OPTIMIZER_SEED, pair=DEFAULT_PAIR)
        esc_fp2 = escalation_fingerprint(3, False, null_fp2, 1, 2, 2, 1.1)
        # Populate a real checkpoint first (needed for its content hash) via
        # the same staged design the real pipeline would use.
        staged2 = staged_null_test(iters=20, restarts=2, seed_base=1, workers=1,
                                    checkpoint_path=ckpt_path, pair=DEFAULT_PAIR,
                                    stage_1_trials=2, stage_2_trials=2, significance_p=1.1)
        assert staged2["decision"] == "pass"
        # Simulate a crash: write ONLY the header + gate_decision, never the
        # candidates record -- exactly the interruption window that crashed
        # before this fix.
        gate_only = {
            "record": "gate_decision", "real_score": staged2["real_score"],
            "exceedances": staged2["exceedances"], "trial_count": staged2["trial_count"],
            "empirical_p": staged2["empirical_p"], "decision": staged2["decision"],
            "checkpoint_content_hash": _hash_file(ckpt_path),
        }
        append_escalation_record(esc_path, gate_only, esc_fp2)
        gate_record3, candidates3, hits3 = run_gated_recovery(
            iters=20, restarts=2, seed_base=1, workers=1, pair=DEFAULT_PAIR,
            checkpoint_path=ckpt_path, escalation_path=esc_path, top_n=3,
            stage_1_trials=2, stage_2_trials=2, significance_p=1.1,
        )
        assert candidates3 is not None and len(candidates3) >= 1, (
            "self-test FAILED: resume after gate-but-no-candidates did not regenerate candidates"
        )
        _, candidates_on_disk, _ = load_escalation_state(esc_path, esc_fp2)
        assert candidates_on_disk == candidates3, (
            "self-test FAILED: regenerated candidates were not persisted to disk"
        )

    print(f"[*] self-test OK (real={real_score:.1f}, null={null_scores}, p={p:.4f}, "
          f"checkpoint resume verified, (g,i) pair path verified, cross-pair "
          f"checkpoint rejection verified, dedup_top_n verified, staged design "
          f"both branches verified, escalation artifact round-trip/resume/"
          f"mismatch-rejection/completion-tracking verified, seed_base binding "
          f"verified, checkpoint-content-hash tamper detection verified, "
          f"gate-without-candidates resume verified)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("restarts", type=int, nargs="?", default=800)
    ap.add_argument("iters", type=int, nargs="?", default=4000)
    ap.add_argument("workers", type=int, nargs="?", default=16)
    ap.add_argument("--seed-base", type=int, default=20260726)
    ap.add_argument("--checkpoint", type=Path, default=None,
                     help="defaults to a pair-specific filename (see checkpoint_path_for_pair)")
    ap.add_argument("--escalation-result", type=Path, default=None,
                     help="defaults to a pair-specific filename (see escalation_result_path_for_pair)")
    ap.add_argument(
        "--pair", type=str, default="h,e",
        help="ordered escape pair to test, as 'e1,e2' (default h,e; Phase 112 also supports g,i)",
    )
    ap.add_argument("--top-n", type=int, default=20)
    ap.add_argument("--include-quarantined", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    pair = tuple(args.pair.split(","))
    if pair not in REAL_CODE_COUNTS:
        raise SystemExit(
            f"--pair {pair} has no known expected code count -- add it to "
            f"REAL_CODE_COUNTS after verifying via segment_codes() first"
        )
    checkpoint = args.checkpoint if args.checkpoint is not None else checkpoint_path_for_pair(pair)
    escalation_path = (
        args.escalation_result if args.escalation_result is not None
        else escalation_result_path_for_pair(pair)
    )

    print(f"[*] pair={pair} restarts={args.restarts} iters={args.iters} workers={args.workers} "
          f"optimizer_seed={OPTIMIZER_SEED} checkpoint={checkpoint} escalation_result={escalation_path}")
    print(f"[*] staged design: stage1={STAGE_1_TRIALS} trials, extend to stage2="
          f"{STAGE_2_TRIALS} only if stage1 has 0 exceedances; significance bar p<{SIGNIFICANCE_P}")

    gate_record, candidates, hits = run_gated_recovery(
        args.iters, args.restarts, args.seed_base, args.workers, pair=pair,
        checkpoint_path=checkpoint, escalation_path=escalation_path,
        top_n=args.top_n, include_quarantined=args.include_quarantined,
    )

    print(f"\n[*] final gate decision: {gate_record}")
    if gate_record["decision"] == "pass":
        print(f"[*] {len(candidates)} candidates escalated, {len(hits)} total hits")
    else:
        print("[*] closed negative -- no escalation.")


if __name__ == "__main__":
    main()
