#!/usr/bin/env python3
"""VIC-cipher-style chain-addition sweep against dbbi/faed (Plan A, item 1).

Tests whether either target carries an *additive* keystream (VIC cipher's real
mechanism: a short keyword-derived seed extended via lagged digit addition,
d[i] = (d[i-1]+d[i-2]) % base) layered on top of the already-validated
{b,e}/pad25/top_first checkerboard model -- independent of, and in addition to,
guessing the checkerboard's own alphabet keyword.

Two modes, both tried for every (alphabet_candidate, keystream_candidate) pair:
  - "pre":  dechain the raw 9-symbol ciphertext (mod 9) BEFORE checkerboard decode
  - "post": checkerboard-decode as usual, THEN dechain the resulting letters (mod 26)

Motivated by doc/GSMG_PUZZLE.md's Kasiski/Friedman finding (2026-07-14): dbbi's IC
sits squarely inside the native single-layer-checkerboard range (no smoothing
evidence), while faed's IC is significantly below it (z=-3.1) -- consistent with
either raw ciphertext payload (leading theory) or a checkerboard+keystream mix.
This sweep is the concrete, cheap test of the latter for both targets.

Hardened 2026-07-28 (doc/GSMG_PHASE_REOPENING_REASSESSMENT.md) before the FAED
{g,i} reopening run, then further hardened after that run completed per an
external code review (both rounds independently verified against this file,
not taken on faith):

- the old `--alpha-skip` mechanism was not an exact checkpoint (workers
  process chunks out of order, so a resume value had to be a conservative
  margin, not an exact cutoff). Replaced with a fingerprinted, per-alphabet-
  candidate JSONL checkpoint (`--checkpoint`) -- exact resume by digest,
  invalidated automatically if the driver, cb_common, data.py,
  binary_key_material_backfill.py, extended_cipher_recheck.py, the installed
  Python/cryptography versions, or the candidate/escape scope changes;
- a dangling final checkpoint line (an interrupted write -- append_jsonl
  always writes payload+newline in one call, so any line lacking its
  trailing newline can only be that) is now physically truncated away the
  moment it's detected, not just skipped in memory -- the previous version
  only quarantined it for that one load, so a second interrupted write later
  could merge onto the same dangling fragment and eventually corrupt a
  now-non-final line beyond recovery;
- hits are written as mode-0600 JSONL (`append_jsonl(..., sensitive=True)`),
  each record carrying a compact fingerprint subset (`alpha_digest`,
  `key_digest`, `driver_sha256`) for provenance, and deduplicated by a
  deterministic `hit_id` against what's already in the hits file -- closes a
  window where a crash between writing a hit and writing its corresponding
  checkpoint line could otherwise duplicate that hit on resume;
- the hits file gets the exact same dangling-final-line physical repair as
  the checkpoint (both now share `_read_and_repair_jsonl`) -- a second
  review round reproduced real corruption in an earlier version that only
  tolerated a dangling hits line without truncating it, silently losing a
  hit's `hit_id` out of the dedup set on the next reload;
- every worker chunk's result set is validated against what was submitted
  before anything is written -- a chunk that comes back with a missing/
  duplicate/extra entry is treated as a whole failure (nothing checkpointed)
  rather than partially trusted;
- an exclusive, non-blocking `flock` on the checkpoint and hits paths
  refuses a second concurrent invocation sharing either file rather than
  letting their writes interleave undetected;
- the fingerprint pins the actual linked OpenSSL version string, not just
  `cryptography.__version__` -- the same review round pointed out the
  package version alone can't detect a relinked/rebuilt OpenSSL underneath
  an unchanged `cryptography` version.

The parent process is the only thing that ever writes the checkpoint or hits
file -- workers only compute. One inherited exception, not introduced by this
hardening and not unique to this script: `cb_common.aes_try_open()`'s
weak-candidate logging (`_log_candidate`, gated by `PRINTABLE_Z_WEAK_
THRESHOLD`) writes directly to the shared `weak_candidates_log.txt` from
whichever process calls it, including worker processes under `--workers`
`>1`. That side-channel is a property of the shared oracle every
multiprocessing sweep script in this project inherits, not something scoped
by (or fixable within) this driver alone.

Usage:
    python3 tools/gsmg/chain_addition_sweep.py --self-test
    python3 tools/gsmg/chain_addition_sweep.py --targets faed --faed-escapes g,i
    python3 tools/gsmg/chain_addition_sweep.py --alphabet-wordlist wordlists/gsmg/chat_mined_words.txt
"""
import argparse
import fcntl
import hashlib
import json
import multiprocessing
import os
import platform
import sys
import tempfile
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cryptography  # noqa: E402
from cryptography.hazmat.backends.openssl.backend import backend as _openssl_backend  # noqa: E402
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa: E402

import binary_key_material_backfill  # noqa: E402
import cb_common  # noqa: E402
import data  # noqa: E402
import extended_cipher_recheck  # noqa: E402
from binary_key_material_backfill import append_jsonl  # noqa: E402
from cb_common import (  # noqa: E402
    aes_try_open, answer_forms, build_board_9ary, dechain_9ary, dechain_letters,
    decode_9ary, evp_bytes_to_key, keystr_forms, keyword_to_seed, pad25,
)
from data import DBBI, FAED  # noqa: E402
from extended_cipher_recheck import candidate_list_digest  # noqa: E402

TARGETS = {"dbbi": DBBI, "faed": FAED}

# Per-target escape-pair defaults. dbbi's own decisive pair is {b,e} (frequency
# analysis). faed had never been tested under its OWN established hypotheses in
# this script -- every historical run here only ever exercised faed under dbbi's
# {b,e} pair (see doc/GSMG_SCRIPT_CODE_REVIEW.md and FINDINGS.md Phase 16).
# {g,i} is faed's own best-fit frequency pair; {h,e} is the mirror of dbbi's
# pair under the mirror9 symbol complement. Both now covered by default, both
# orders each. Pass --faed-escapes b,e to reproduce the exact historical scope.
DEFAULT_DBBI_ESCAPES = "b,e"
DEFAULT_FAED_ESCAPES = "g,i;h,e"
SIGNS = (-1, 1)


def parse_escape_pairs(spec: str):
    """"b,e" -> [(b,e),(e,b)]; "g,i;h,e" -> [(g,i),(i,g),(h,e),(e,h)] -- every
    listed pair expanded to both escape/digit orders."""
    pairs = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        e1, e2 = [c.strip().lower() for c in chunk.split(",")]
        if len(e1) != 1 or len(e2) != 1 or e1 == e2:
            raise ValueError(f"invalid escape pair {chunk!r} in {spec!r}")
        pairs.append((e1, e2))
        pairs.append((e2, e1))
    if not pairs:
        raise ValueError(f"no escape pairs parsed from {spec!r}")
    return pairs

# Small, curated, high-confidence GSMG-specific candidate sets -- deliberately NOT
# the big system dictionaries, since this is a product-space sweep (alphabet x
# keystream) and needs to stay tractable. These are the same fragments used
# throughout this project's other curated sweeps.
CURATED_WORDLISTS = [
    "wordlists/gsmg/riddle_combinations.txt",
    "wordlists/gsmg/matrix_trilogy.txt",
    "wordlists/gsmg/discovered_paths.txt",
    "wordlists/gsmg/last_command.txt",
    "wordlists/gsmg/salphaseion_own_keywords_combined.txt",
]


def _check_answer(ans, alpha_cand, key_cand, target, mode, sign, escapes, hits):
    for form in answer_forms(ans):
        if not form:
            continue
        for keystr in keystr_forms(form):
            r = aes_try_open(keystr)
            if r:
                tag, body, digest_name, key_len = r
                hits.append({
                    "alphabet_candidate": alpha_cand,
                    "keystream_candidate": key_cand,
                    "target": target,
                    "mode": mode,
                    "sign": sign,
                    "escapes": escapes,
                    "answer": ans,
                    "form": form,
                    "keystr": keystr,
                    "blob": tag,
                    "kdf": f"{digest_name}/aes{key_len * 8}",
                    "plaintext": body[:500].decode("utf-8", errors="replace"),
                })


def test_pair(alpha_candidate: str, key_candidate: str, target_escapes: dict):
    hits = []
    alphabet = pad25(alpha_candidate)
    if len(alphabet) != 25:
        return hits
    seed9 = keyword_to_seed(key_candidate, 9)
    seed26 = keyword_to_seed(key_candidate, 26)

    for target_name, target_str in TARGETS.items():
        if target_name not in target_escapes:
            continue
        escape_orders = target_escapes[target_name]
        # PRE: dechain raw ciphertext (mod 9), then checkerboard-decode.
        if len(seed9) >= 2:
            for sign in SIGNS:
                dechained = dechain_9ary(target_str, seed9, sign)
                for e1, e2 in escape_orders:
                    ans = decode_9ary(dechained, alphabet, e1, e2)
                    if "?" not in ans:
                        _check_answer(ans, alpha_candidate, key_candidate, target_name,
                                      "pre", sign, (e1, e2), hits)

        # POST: checkerboard-decode as usual, then dechain the letters (mod 26).
        if len(seed26) >= 2:
            for e1, e2 in escape_orders:
                ans = decode_9ary(target_str, alphabet, e1, e2)
                if "?" in ans:
                    continue
                for sign in SIGNS:
                    dechained_ans = dechain_letters(ans, seed26, sign)
                    _check_answer(dechained_ans, alpha_candidate, key_candidate, target_name,
                                  "post", sign, (e1, e2), hits)
    return hits


def load_wordlist(path: str):
    p = Path(path)
    if not p.exists():
        print(f"[!] wordlist not found, skipping: {path}", file=sys.stderr)
        return []
    out, seen = [], set()
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                out.append(line)
    return out


def load_candidates(paths):
    out, seen = [], set()
    for wl in paths:
        for c in load_wordlist(wl):
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


# --- Fingerprinted, exact per-alphabet-candidate checkpoint -----------------
#
# Unlike the old --alpha-skip (a manual, conservative-margin cutoff -- workers
# process chunks out of order, so a resume value had to sit comfortably behind
# the last reported progress count), this checkpoints by exact candidate
# digest: a chunk's alphabet candidates are only ever marked done once its
# ENTIRE result set has been validated against what was submitted. Every
# behavior-relevant input (driver source, cb_common, data.py, the candidate
# scope, and the escape configuration) is folded into a fingerprint that must
# match exactly before an existing checkpoint file is reused.


def _alpha_sha256(alpha_candidate: str) -> str:
    return hashlib.sha256(alpha_candidate.encode()).hexdigest()


def _module_sha256(module) -> str:
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()[:16]


def run_fingerprint(alpha_candidates, key_candidates, target_escapes):
    """Every behavior-relevant input this driver depends on. Originally
    covered only the driver itself, cb_common, and data.py; a code review
    after the first FAED {g,i} run pointed out this also imports
    binary_key_material_backfill.py (for append_jsonl) and
    extended_cipher_recheck.py (for candidate_list_digest) without
    fingerprinting either -- a behavior change in either module could
    silently reuse a checkpoint produced under different behavior, the same
    class of gap nopad_window_sweep.py's own fingerprint already guards
    against for its own imports. Also pins the installed Python and
    cryptography versions, mirroring nopad's coincurve fingerprint -- a
    rebuilt/upgraded crypto backend under the same version string is exactly
    the kind of silent behavior change a checkpoint must not survive. A
    second review round correctly pointed out that `cryptography.__version__`
    alone cannot detect that specific case (a relinked/rebuilt OpenSSL under
    an unchanged `cryptography` package version), so the actual linked
    OpenSSL version string is pinned too."""
    return {
        "version": 3,
        "alpha_digest": candidate_list_digest(alpha_candidates),
        "alpha_count": len(alpha_candidates),
        "key_digest": candidate_list_digest(key_candidates),
        "key_count": len(key_candidates),
        "targets": sorted(target_escapes),
        "escapes": {
            name: [list(pair) for pair in pairs]
            for name, pairs in target_escapes.items()
        },
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16],
        "cb_common_sha256": _module_sha256(cb_common),
        "data_sha256": _module_sha256(data),
        "binary_key_material_backfill_sha256": _module_sha256(binary_key_material_backfill),
        "extended_cipher_recheck_sha256": _module_sha256(extended_cipher_recheck),
        "python_version": platform.python_version(),
        "cryptography_version": cryptography.__version__,
        "openssl_version": _openssl_backend.openssl_version_text(),
    }


def _read_and_repair_jsonl(path, kind):
    """Read every complete JSON line from `path`, operating on raw bytes
    (not `str.splitlines()`) so a dangling final fragment can be identified
    and repaired precisely. Shared by load_checkpoint and load_seen_hit_ids
    -- both files are written exclusively by append_jsonl and are subject to
    the exact same interrupted-write failure mode.

    `append_jsonl` always writes `payload + "\\n"` in a single call, so a
    fully-written file can only ever end in `\\n` -- anything after the last
    real newline is therefore, by construction, an interrupted write (a hard
    kill: OOM, power loss, `kill -9`), never a normal record. That dangling
    fragment is dropped from the returned records AND physically truncated
    from the file right here, before returning -- not just skipped in
    memory. A prior version (for the checkpoint, and originally not applied
    to the hits file at all) only did the in-memory skip: a second
    interrupted write later would then append onto that same dangling
    fragment, merging two records onto one unparseable line that (once a
    third write pushed it out of the final-line position) became permanent,
    unrecoverable corruption -- and for the hits file specifically, silently
    losing a previously-recorded hit_id out of the dedup set. Repairing the
    file on every load closes that window entirely for both files -- there
    is never more than one dangling fragment to reason about, and it never
    survives past this function returning.

    Corruption anywhere in the file's COMPLETE lines (i.e. not the dangling
    tail) is never expected from normal operation and still raises -- this
    is deliberately narrow resilience for one specific, well-understood
    failure mode, not a general tolerance for a corrupt file."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    raw = path.read_bytes()
    last_nl = raw.rfind(b"\n")
    if last_nl == len(raw) - 1:
        dangling = None
        body = raw[:-1]
    else:
        dangling = raw[last_nl + 1:]
        body = raw[:last_nl] if last_nl != -1 else b""
    lines = body.split(b"\n") if body else []
    records = []
    for i, line_bytes in enumerate(lines):
        line = line_bytes.decode("utf-8")
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            raise ValueError(
                f"{path}: corrupt {kind} line {i} (not the dangling final "
                f"fragment, so not attributable to an interrupted write) -- "
                f"refusing to guess: {line[:80]!r}"
            )
    if dangling is not None:
        good_length = last_nl + 1
        print(
            f"[!] {path}: quarantining and truncating a dangling final line "
            f"(no trailing newline -- an interrupted write): {dangling[:80]!r}"
        )
        with open(path, "r+b") as f:
            f.truncate(good_length)
    return records


def load_checkpoint(path, fingerprint):
    """Load the set of already-completed alpha_sha256 digests. See
    _read_and_repair_jsonl for the dangling-tail repair this relies on."""
    records = _read_and_repair_jsonl(path, "checkpoint")
    if not records:
        return set()
    expected_header = {"header": True, **fingerprint}
    if records[0] != expected_header:
        raise ValueError(f"{path}: checkpoint header does not match this run's "
                          f"fingerprint; use a new --checkpoint path")
    return {record["alpha_sha256"] for record in records[1:] if "alpha_sha256" in record}


def ensure_checkpoint_header(path, fingerprint):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        append_jsonl(path, {"header": True, **fingerprint})


class _RunLock:
    """Wraps however many distinct-path flocks acquire_run_lock ends up
    holding, so the caller releases all of them via a single .close()
    regardless of how many there were."""

    def __init__(self, lock_files):
        self._lock_files = lock_files

    def close(self):
        for lock_file in self._lock_files:
            lock_file.close()


def acquire_run_lock(*paths):
    """Exclusive, non-blocking flock on a dedicated sibling `.lock` file for
    EACH distinct path given (not the paths themselves, so this works even
    before those files exist) -- closes the gap where nothing previously
    stopped two invocations against the same checkpoint/hits paths from
    running at once and interleaving writes. Locking only the checkpoint is
    not enough since the two paths need not share a prefix.

    Held for the run's duration via the returned object's open file handles;
    the OS releases each flock automatically whenever this process exits,
    however it exits. If any one of the requested locks is unavailable,
    every lock already acquired in this same call is released before
    raising -- a partial lock set is never left held."""
    distinct_paths = sorted({str(path) for path in paths})
    acquired = []
    try:
        for path in distinct_paths:
            lock_path = Path(path + ".lock")
            lock_file = open(lock_path, "w")
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_file.close()
                raise SystemExit(
                    f"another chain_addition_sweep run is already active against "
                    f"{path} (lock held on {lock_path}) -- refusing to start a "
                    f"second one"
                )
            acquired.append(lock_file)
    except SystemExit:
        for lock_file in acquired:
            lock_file.close()
        raise
    return _RunLock(acquired)


# --- Hit fingerprinting and idempotent dedup ---------------------------------
#
# A crash between writing a hit and writing its corresponding checkpoint
# line would otherwise cause that alphabet candidate to be reprocessed on
# resume and its hit written a second time. Deduplicating by a deterministic
# hit_id (computed from the fields that make a hit unique, independent of
# write order or timing) closes that window regardless of exactly where a
# crash lands relative to the two writes.


def compute_hit_id(hit):
    key = "\0".join((
        hit["alphabet_candidate"], hit["keystream_candidate"], hit["target"],
        hit["mode"], str(hit["sign"]), "|".join(hit["escapes"]), hit["blob"],
        hit["kdf"], hit["keystr"],
    ))
    return hashlib.sha256(key.encode()).hexdigest()


def load_seen_hit_ids(hits_path):
    """A code review reproduced real corruption in an earlier version that
    only tolerated (did not repair) a dangling final hits line: a second
    interrupted write later merged onto that fragment, and the merged,
    permanently-unparseable line silently dropped its hit's hit_id out of
    the returned set on the next reload -- defeating the dedup this
    function exists to support. Now shares load_checkpoint's physical
    repair via _read_and_repair_jsonl instead of a separate, weaker
    tolerate-and-skip path."""
    records = _read_and_repair_jsonl(hits_path, "hits")
    return {record["hit_id"] for record in records if "hit_id" in record}


def write_hit(hits_path, hit, run_fp, seen_hit_ids):
    """The only place a hit is ever appended to `hits_path`. Stamps a
    deterministic `hit_id` (for cross-resume dedup) and a compact
    fingerprint subset (for provenance -- which run/scope produced this hit,
    without needing a separate header convention the way the checkpoint
    has one) onto every record."""
    hit_id = compute_hit_id(hit)
    if hit_id in seen_hit_ids:
        return False
    record = dict(hit, hit_id=hit_id, run_fingerprint={
        "alpha_digest": run_fp["alpha_digest"],
        "key_digest": run_fp["key_digest"],
        "driver_sha256": run_fp["driver_sha256"],
    })
    print(f"\n[+++ HIT] {record}\n")
    append_jsonl(hits_path, record, sensitive=True)
    seen_hit_ids.add(hit_id)
    return True


# --- Worker-side compute (parallel path) ------------------------------------


class WorkerConfig(NamedTuple):
    key_candidates: tuple
    target_escapes: dict


_worker_config = None


def _worker_init(config: WorkerConfig):
    global _worker_config
    _worker_config = config


def _process_chunk(alpha_chunk):
    """Pure compute -- no file I/O. Returns one (alpha, alpha_sha256, hits,
    error) tuple per candidate in the chunk; a failure in one candidate does
    not affect its chunk-mates. `error` is the exception class name only --
    never the exception text, since some library call could in principle
    echo input data."""
    results = []
    for alpha in alpha_chunk:
        digest = _alpha_sha256(alpha)
        try:
            hits = []
            for key in _worker_config.key_candidates:
                hits.extend(test_pair(alpha, key, _worker_config.target_escapes))
            results.append((alpha, digest, hits, None))
        except Exception as exc:
            results.append((alpha, digest, None, type(exc).__name__))
    return results


def _apply_chunk_results(original_chunk, chunk_results, hits_path, checkpoint_path,
                          run_fp, seen_hit_ids):
    """Validate the returned digest set against what was submitted -- on any
    mismatch (missing, duplicate, or unexpected extra entry) the WHOLE chunk
    is treated as failed rather than partially trusted; this is independent
    of trusting _process_chunk's own implementation to always behave, the
    same way this project's other hardened sweeps guard against a future
    refactor silently dropping or double-emitting an item. Only once
    validation passes does this write anything -- the only place either the
    hits file or checkpoint is ever written, satisfying "workers only
    compute, single parent writes" by construction. Returns
    (num_completed, num_errors)."""
    expected = {_alpha_sha256(a) for a in original_chunk}
    actual = [digest for _, digest, _, _ in chunk_results]
    if len(actual) != len(expected) or set(actual) != expected:
        for a in original_chunk:
            print(f"[!] malformed chunk result (set mismatch) alpha_sha256={_alpha_sha256(a)}")
        return 0, len(original_chunk)

    num_completed = 0
    num_errors = 0
    for _alpha, digest, hits, error in chunk_results:
        if error is not None:
            print(f"[!] alphabet-candidate failure alpha_sha256={digest} error={error}")
            num_errors += 1
            continue
        for hit in hits:
            write_hit(hits_path, hit, run_fp, seen_hit_ids)
        append_jsonl(checkpoint_path, {"alpha_sha256": digest})
        num_completed += 1
    return num_completed, num_errors


def _run_sequential(alpha_candidates, key_candidates, target_escapes, hits_path, checkpoint_path, fingerprint):
    completed = load_checkpoint(checkpoint_path, fingerprint)
    ensure_checkpoint_header(checkpoint_path, fingerprint)
    seen_hit_ids = load_seen_hit_ids(hits_path)
    todo = [a for a in alpha_candidates if _alpha_sha256(a) not in completed]
    resumed_count = len(alpha_candidates) - len(todo)
    total = len(alpha_candidates)
    total_completed = 0
    error_count = 0
    start = time.time()
    last_print = 0.0
    for alpha in todo:
        digest = _alpha_sha256(alpha)
        try:
            hits = []
            for key in key_candidates:
                hits.extend(test_pair(alpha, key, target_escapes))
        except Exception as exc:
            print(f"[!] alphabet-candidate failure alpha_sha256={digest} error={type(exc).__name__}")
            error_count += 1
            continue
        for hit in hits:
            write_hit(hits_path, hit, fingerprint, seen_hit_ids)
        append_jsonl(checkpoint_path, {"alpha_sha256": digest})
        total_completed += 1
        now = time.time()
        if now - last_print >= 1.0:
            last_print = now
            done_total = resumed_count + total_completed
            rate = total_completed / max(now - start, 1e-9)
            eta = (total - done_total) / max(rate, 1e-9)
            print(f"\r[*] {done_total:,}/{total:,} alphabet candidates "
                  f"(resumed={resumed_count:,} session={total_completed:,} "
                  f"errors={error_count}) rate={rate:.1f}/s eta={eta:.0f}s   ",
                  end="", flush=True)
    print(f"\n[*] final: {total_completed:,} completed this session "
          f"({resumed_count + total_completed:,}/{total:,} total), {error_count} errors")
    if error_count:
        sys.exit(1)


def _run_parallel(alpha_candidates, key_candidates, target_escapes, hits_path, checkpoint_path,
                   fingerprint, workers, chunk_size):
    completed = load_checkpoint(checkpoint_path, fingerprint)
    ensure_checkpoint_header(checkpoint_path, fingerprint)
    seen_hit_ids = load_seen_hit_ids(hits_path)
    todo = [a for a in alpha_candidates if _alpha_sha256(a) not in completed]
    resumed_count = len(alpha_candidates) - len(todo)
    total = len(alpha_candidates)
    if not todo:
        print(f"[*] no unfinished work remains -- {resumed_count:,} alphabet candidates already checkpointed")
        return

    chunks = [todo[i:i + chunk_size] for i in range(0, len(todo), chunk_size)]
    config = WorkerConfig(key_candidates=tuple(key_candidates), target_escapes=target_escapes)
    max_in_flight = max(workers * 4, 8)
    total_completed = 0
    error_count = 0
    start = time.time()
    last_print = 0.0

    mp_context = multiprocessing.get_context("spawn")
    try:
        with ProcessPoolExecutor(
            max_workers=workers, mp_context=mp_context,
            initializer=_worker_init, initargs=(config,),
        ) as executor:
            chunk_iter = iter(chunks)
            future_to_chunk = {}

            def submit_next():
                nxt = next(chunk_iter, None)
                if nxt is None:
                    return False
                fut = executor.submit(_process_chunk, nxt)
                future_to_chunk[fut] = nxt
                return True

            for _ in range(max_in_flight):
                if not submit_next():
                    break

            try:
                while future_to_chunk:
                    done, _ = wait(future_to_chunk, return_when=FIRST_COMPLETED)
                    for fut in done:
                        chunk = future_to_chunk.pop(fut)
                        try:
                            chunk_results = fut.result()
                        except BrokenProcessPool:
                            error_count += len(chunk)
                            for remaining in future_to_chunk.values():
                                error_count += len(remaining)
                            print("[!] process pool broken -- stopping, not dispatching further work")
                            raise
                        except Exception as exc:
                            for a in chunk:
                                print(f"[!] chunk failure alpha_sha256={_alpha_sha256(a)} "
                                      f"error={type(exc).__name__}")
                            error_count += len(chunk)
                        else:
                            completed_n, errors_n = _apply_chunk_results(chunk, chunk_results, hits_path, checkpoint_path, fingerprint, seen_hit_ids)
                            total_completed += completed_n
                            error_count += errors_n
                        submit_next()
                        now = time.time()
                        if now - last_print >= 1.0 or not future_to_chunk:
                            last_print = now
                            done_total = resumed_count + total_completed
                            rate = total_completed / max(now - start, 1e-9)
                            eta = (total - done_total) / max(rate, 1e-9)
                            print(f"\r[*] {done_total:,}/{total:,} alphabet candidates "
                                  f"(resumed={resumed_count:,} session={total_completed:,} "
                                  f"errors={error_count}) rate={rate:.1f}/s eta={eta:.0f}s   ",
                                  end="", flush=True)
            except KeyboardInterrupt:
                print("\n[!] interrupted -- cancelling queued work, draining in-flight chunks...")
                still_running = [fut for fut in list(future_to_chunk) if not fut.cancel()]
                for fut in still_running:
                    chunk = future_to_chunk.pop(fut)
                    try:
                        chunk_results = fut.result()
                    except Exception as exc:
                        for a in chunk:
                            print(f"[!] chunk failure alpha_sha256={_alpha_sha256(a)} "
                                  f"error={type(exc).__name__}")
                        error_count += len(chunk)
                        continue
                    completed_n, errors_n = _apply_chunk_results(chunk, chunk_results, hits_path, checkpoint_path, fingerprint, seen_hit_ids)
                    total_completed += completed_n
                    error_count += errors_n
                raise
    except BrokenProcessPool:
        print(f"\n[*] final: {total_completed:,} completed this session, {error_count} errors")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n[*] interrupted: {total_completed:,} completed this session, {error_count} errors")
        sys.exit(130)

    print(f"\n[*] final: {total_completed:,} completed this session "
          f"({resumed_count + total_completed:,}/{total:,} total), {error_count} errors")
    if error_count:
        sys.exit(1)


# --- Self-test ---------------------------------------------------------------


def self_test():
    """Verifies, in order:

    1. Deterministic synthetic positives for BOTH the "pre" (dechain before
       checkerboard decode) and "post" (dechain after) branches, round-tripped
       through the real test_pair() and the real AES oracle (cb_common.BLOBS
       swapped for a synthetic blob, restored afterward) -- not a reimplemented
       parallel check of the logic. Asserts the exact sign and escape order
       each branch resolves through, not just that some hit occurred.
    2. The fingerprint/checkpoint mechanism: header round-trip, exact resume
       (an already-checkpointed candidate is skipped), and refusal to reuse a
       checkpoint whose candidate scope has changed.
    3. Physical repair of a dangling (interrupted-write) final checkpoint
       line, including that a SECOND interrupted write after the first
       repair still repairs cleanly rather than compounding corruption --
       the exact failure mode a code review found in an earlier version that
       only quarantined the dangling line in memory without truncating it.
    4. Hit-id dedup: the same hit written twice is recorded once; a hit
       already present in the hits file is not re-appended by a later
       _apply_chunk_results call for the same alpha candidate.
    5. Sequential vs. parallel parity on a tiny real (non-synthetic)
       candidate scope: both dispatch paths must reach the same checkpoint
       completion set and the same (zero) hit count, exercising the actual
       ProcessPoolExecutor/spawn dispatch loop rather than only its helper
       functions in isolation.
    """
    passphrase = "THEQUICKBROWNFOX"
    plaintext = b"the quick brown fox jumps over the lazy dog several times today"
    salt = b"01234567"
    key, iv = evp_bytes_to_key(passphrase.encode(), salt, "sha256", 32)
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len]) * pad_len
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    synthetic_blobs = {"SYNTH": (salt, ct)}

    # These two 9-symbol strings were hand-derived (and independently
    # verified via direct round-trip through cb_common's own primitives)
    # so that, for alphabet_candidate="ROSEBUD"/keystream_candidate="LANTERN"
    # under escape pair {g,i}:
    #   - "pre"-mode:  dechain_9ary(TARGET_PRE, seed9, sign=-1) then
    #     decode_9ary(...) == "THEQUICKBROWNFOX"
    #   - "post"-mode: decode_9ary(TARGET_POST, ...) == "FISKZAQQVRIQBNKB",
    #     and dechain_letters("FISKZAQQVRIQBNKB", seed26, sign=-1) ==
    #     "THEQUICKBROWNFOX"
    target_pre = "cecgiihbhcefiddffiadiaegga"
    target_post = "gcgfcggiigaicicieagficeiagge"

    original_blobs = cb_common.BLOBS
    original_targets = dict(TARGETS)
    try:
        cb_common.BLOBS = synthetic_blobs

        TARGETS.clear()
        TARGETS.update(original_targets)
        TARGETS["synth_pre"] = target_pre
        hits_pre = test_pair("ROSEBUD", "LANTERN", {"synth_pre": [("g", "i")]})
        assert any(
            h["target"] == "synth_pre" and h["mode"] == "pre" and h["blob"] == "SYNTH"
            and h["answer"] == passphrase and h["sign"] == -1
            and tuple(h["escapes"]) == ("g", "i")
            for h in hits_pre
        ), f"PRE-mode synthetic positive did not round-trip with the expected sign/escapes: {hits_pre}"

        TARGETS.clear()
        TARGETS.update(original_targets)
        TARGETS["synth_post"] = target_post
        hits_post = test_pair("ROSEBUD", "LANTERN", {"synth_post": [("g", "i")]})
        assert any(
            h["target"] == "synth_post" and h["mode"] == "post" and h["blob"] == "SYNTH"
            and h["answer"] == passphrase and h["sign"] == -1
            and tuple(h["escapes"]) == ("g", "i")
            for h in hits_post
        ), f"POST-mode synthetic positive did not round-trip with the expected sign/escapes: {hits_post}"
    finally:
        cb_common.BLOBS = original_blobs
        TARGETS.clear()
        TARGETS.update(original_targets)

    print("[*] self-test OK: PRE and POST chain-addition synthetic positives "
          "round-trip through the real AES oracle")

    with tempfile.TemporaryDirectory() as tmp:
        ckpt = Path(tmp) / "checkpoint.jsonl"
        fp = run_fingerprint(["alpha1", "alpha2", "alpha3"], ["key1"], {"dbbi": [("b", "e")]})
        ensure_checkpoint_header(ckpt, fp)
        assert load_checkpoint(ckpt, fp) == set()

        append_jsonl(ckpt, {"alpha_sha256": _alpha_sha256("alpha1")})
        assert load_checkpoint(ckpt, fp) == {_alpha_sha256("alpha1")}

        # A changed candidate scope must refuse to reuse this checkpoint
        # rather than silently mixing two different runs' completion state.
        fp_changed = run_fingerprint(
            ["alpha1", "alpha2", "alpha3", "alpha4"], ["key1"], {"dbbi": [("b", "e")]}
        )
        try:
            load_checkpoint(ckpt, fp_changed)
            raise AssertionError("expected a fingerprint mismatch to raise ValueError")
        except ValueError:
            pass

        # A single alpha-candidate result set validates cleanly end to end
        # through _apply_chunk_results and is reflected in the checkpoint.
        hits_path = Path(tmp) / "hits.jsonl"
        seen_hit_ids = set()
        chunk = ["alpha2"]
        chunk_results = [("alpha2", _alpha_sha256("alpha2"), [], None)]
        completed_n, errors_n = _apply_chunk_results(chunk, chunk_results, hits_path, ckpt, fp, seen_hit_ids)
        assert (completed_n, errors_n) == (1, 0)
        assert _alpha_sha256("alpha2") in load_checkpoint(ckpt, fp)

        # A malformed result set (missing entry) must be rejected wholesale.
        bad_chunk = ["alpha3"]
        bad_results = []
        completed_n, errors_n = _apply_chunk_results(bad_chunk, bad_results, hits_path, ckpt, fp, seen_hit_ids)
        assert (completed_n, errors_n) == (0, 1)
        assert _alpha_sha256("alpha3") not in load_checkpoint(ckpt, fp)

    print("[*] self-test OK: checkpoint fingerprint/exact-resume/malformed-result-set guards verified")

    # --- Truncated-tail checkpoint repair ------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        ckpt = Path(tmp) / "checkpoint.jsonl"
        fp = run_fingerprint(["alpha1", "alpha2"], ["key1"], {"dbbi": [("b", "e")]})
        ensure_checkpoint_header(ckpt, fp)
        append_jsonl(ckpt, {"alpha_sha256": _alpha_sha256("alpha1")})
        good_size_1 = ckpt.stat().st_size

        # Simulate a hard kill mid-write: a fragment with no trailing newline.
        with open(ckpt, "a") as f:
            f.write('{"alpha_sha256": "deadbeef')
        assert ckpt.stat().st_size > good_size_1

        completed = load_checkpoint(ckpt, fp)
        assert completed == {_alpha_sha256("alpha1")}
        # The dangling fragment must be physically gone, not just skipped in
        # memory -- the file should be back to exactly its pre-corruption size.
        assert ckpt.stat().st_size == good_size_1, (
            "dangling final line was not physically truncated from the checkpoint"
        )

        # A resumed write lands cleanly (no merge onto stale garbage), and a
        # SECOND interrupted write later must repair just as cleanly -- this
        # is the exact scenario a prior version corrupted permanently: a
        # second dangling fragment appended after the first, which then only
        # gets caught (and would previously have raised, being no longer the
        # final line) once a THIRD write pushes it out of tail position.
        append_jsonl(ckpt, {"alpha_sha256": _alpha_sha256("alpha2")})
        good_size_2 = ckpt.stat().st_size
        with open(ckpt, "a") as f:
            f.write('{"alpha_sha256": "beefcafe')
        completed = load_checkpoint(ckpt, fp)
        assert completed == {_alpha_sha256("alpha1"), _alpha_sha256("alpha2")}
        assert ckpt.stat().st_size == good_size_2

        append_jsonl(ckpt, {"alpha_sha256": _alpha_sha256("alpha3")})
        completed = load_checkpoint(ckpt, fp)
        assert completed == {
            _alpha_sha256("alpha1"), _alpha_sha256("alpha2"), _alpha_sha256("alpha3"),
        }

    print("[*] self-test OK: dangling final checkpoint line is physically repaired, "
          "including across repeated interruptions")

    # --- Hit-id dedup ---------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        hits_path = Path(tmp) / "hits.jsonl"
        fake_fp = {"alpha_digest": "aaaa", "key_digest": "bbbb", "driver_sha256": "cccc"}
        fake_hit = {
            "alphabet_candidate": "x", "keystream_candidate": "y", "target": "faed",
            "mode": "pre", "sign": -1, "escapes": ("g", "i"), "answer": "Z",
            "form": "Z", "keystr": "Z", "blob": "SYNTH", "kdf": "sha256/aes256",
            "plaintext": "irrelevant",
        }
        seen = set()
        assert write_hit(hits_path, fake_hit, fake_fp, seen) is True
        assert write_hit(hits_path, fake_hit, fake_fp, seen) is False
        assert len(hits_path.read_text().splitlines()) == 1, (
            "the same hit was written more than once in a single process"
        )

        # A fresh process reloading seen_hit_ids from disk must recognize the
        # same hit as already-seen -- the actual cross-resume dedup path.
        reloaded = load_seen_hit_ids(hits_path)
        assert reloaded == seen
        assert write_hit(hits_path, fake_hit, fake_fp, reloaded) is False
        assert len(hits_path.read_text().splitlines()) == 1, (
            "a hit already present in the hits file was duplicated after reload "
            "-- the crash-between-hit-and-checkpoint-write window is not closed"
        )

    print("[*] self-test OK: hit-id dedup prevents duplicate hits within and across runs")

    # --- Truncated-tail repair on the HITS file specifically -------------------
    # A code review reproduced real corruption here: an earlier version only
    # tolerated (skipped, never truncated) a dangling final hits line, so a
    # second interrupted write later merged onto it, permanently losing that
    # hit's hit_id out of the dedup set on the next reload. Mirrors the
    # checkpoint-repair test above but specifically exercises
    # load_seen_hit_ids' now-shared use of _read_and_repair_jsonl.
    with tempfile.TemporaryDirectory() as tmp:
        hits_path = Path(tmp) / "hits.jsonl"
        fake_fp = {"alpha_digest": "aaaa", "key_digest": "bbbb", "driver_sha256": "cccc"}
        hit_a = {
            "alphabet_candidate": "a", "keystream_candidate": "y", "target": "faed",
            "mode": "pre", "sign": -1, "escapes": ("g", "i"), "answer": "ZA",
            "form": "ZA", "keystr": "ZA", "blob": "SYNTH", "kdf": "sha256/aes256",
            "plaintext": "irrelevant",
        }
        hit_b = dict(hit_a, alphabet_candidate="b", answer="ZB", form="ZB", keystr="ZB")
        seen = set()
        write_hit(hits_path, hit_a, fake_fp, seen)
        good_size = hits_path.stat().st_size

        with open(hits_path, "a") as f:
            f.write('{"hit_id": "deadbeef')
        assert hits_path.stat().st_size > good_size

        reloaded = load_seen_hit_ids(hits_path)
        assert reloaded == seen, "hit_a's hit_id was lost across the dangling-line repair"
        assert hits_path.stat().st_size == good_size, (
            "dangling final line was not physically truncated from the hits file"
        )

        # A resumed write lands cleanly; a second interruption later must
        # still repair cleanly rather than compounding corruption.
        write_hit(hits_path, hit_b, fake_fp, reloaded)
        good_size_2 = hits_path.stat().st_size
        with open(hits_path, "a") as f:
            f.write('{"hit_id": "cafefeed')
        reloaded2 = load_seen_hit_ids(hits_path)
        assert reloaded2 == reloaded
        assert hits_path.stat().st_size == good_size_2

    print("[*] self-test OK: dangling final hits line is physically repaired, "
          "including across repeated interruptions")

    # --- Sequential vs. parallel parity (real dispatch loops) ------------------
    # Uses ordinary English words, not the synthetic vectors above -- these
    # are expected to produce zero hits against the real DBBI/FAED targets and
    # real BLOBS (matching every other sweep in this project's history), so
    # this exercises the actual ProcessPoolExecutor/spawn dispatch loop
    # end-to-end rather than only its helper functions in isolation.
    parity_alpha = ["apple", "orange", "banana", "cherry", "damson"]
    parity_key = ["lantern", "compass"]
    parity_escapes = {"dbbi": [("b", "e")]}
    with tempfile.TemporaryDirectory() as tmp:
        seq_ckpt = Path(tmp) / "seq_checkpoint.jsonl"
        seq_hits = Path(tmp) / "seq_hits.jsonl"
        par_ckpt = Path(tmp) / "par_checkpoint.jsonl"
        par_hits = Path(tmp) / "par_hits.jsonl"
        fp = run_fingerprint(parity_alpha, parity_key, parity_escapes)

        _run_sequential(parity_alpha, parity_key, parity_escapes, seq_hits, seq_ckpt, fp)
        _run_parallel(parity_alpha, parity_key, parity_escapes, par_hits, par_ckpt, fp,
                      workers=2, chunk_size=2)

        seq_completed = load_checkpoint(seq_ckpt, fp)
        par_completed = load_checkpoint(par_ckpt, fp)
        assert seq_completed == par_completed == {_alpha_sha256(a) for a in parity_alpha}
        assert not seq_hits.exists() and not par_hits.exists(), (
            "expected zero hits from ordinary English words against the real targets"
        )

    print("[*] self-test OK: sequential and parallel dispatch loops reach identical "
          "checkpoint completion on a real (non-synthetic) scope")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alphabet-wordlist", action="append", default=None,
                     help="wordlist(s) for the checkerboard alphabet keyword (repeatable). "
                          "Defaults to the curated GSMG set.")
    ap.add_argument("--keystream-wordlist", action="append", default=None,
                     help="wordlist(s) for the chain-addition seed keyword (repeatable). "
                          "Defaults to the curated GSMG set.")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--alpha-limit", type=int, default=None)
    ap.add_argument("--key-limit", type=int, default=None)
    ap.add_argument("--alpha-skip", type=int, default=0,
                     help="skip this many alphabet candidates from the front of the "
                          "(deduped, wordlist-order) list -- legacy manual scope-narrowing "
                          "flag, kept for reproducing historically-documented invocations. "
                          "New runs should rely on --checkpoint for exact resume instead: "
                          "this flag only narrows the candidate scope up front, it is not "
                          "itself an exact checkpoint.")
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--hits-out", default=str(Path(__file__).parent / "hits_chain_addition.jsonl"),
                     help="JSONL hits file (mode 0600 -- may contain recovered passphrase-"
                          "adjacent plaintext)")
    ap.add_argument("--checkpoint", default=str(Path(__file__).parent / "checkpoint_chain_addition.jsonl"),
                     help="fingerprinted, exact per-alphabet-candidate resume checkpoint")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument(
        "--dbbi-escapes", default=DEFAULT_DBBI_ESCAPES,
        help="dbbi escape pair, 'e1,e2' (default: %(default)r; both orders tested)",
    )
    ap.add_argument(
        "--faed-escapes", default=DEFAULT_FAED_ESCAPES,
        help="faed escape pair(s), 'e1,e2' or ';'-separated list of pairs "
             "(default: %(default)r -- faed's own best-fit {g,i} plus the {h,e} "
             "mirror of dbbi's pair; both orders tested for each. Pass 'b,e' to "
             "reproduce this script's historical scope, which only ever tested "
             "faed under dbbi's pair)",
    )
    ap.add_argument(
        "--targets", default="dbbi,faed",
        help="comma-separated subset of dbbi,faed to test (default: both) -- "
             "e.g. --targets faed to backfill only faed's new escape coverage "
             "over an alpha range already completed for dbbi under the old scope",
    )
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    requested_targets = {t.strip() for t in args.targets.split(",") if t.strip()}
    unknown = requested_targets - set(TARGETS)
    if unknown:
        raise SystemExit(f"unknown --targets entries: {sorted(unknown)}")
    target_escapes = {
        name: parse_escape_pairs(spec)
        for name, spec in (("dbbi", args.dbbi_escapes), ("faed", args.faed_escapes))
        if name in requested_targets
    }

    if args.workers < 1:
        raise SystemExit(f"--workers must be >= 1, got {args.workers}")
    if args.chunk_size < 1:
        raise SystemExit(f"--chunk-size must be >= 1, got {args.chunk_size}")

    alpha_candidates = load_candidates(args.alphabet_wordlist or CURATED_WORDLISTS)
    key_candidates = load_candidates(args.keystream_wordlist or CURATED_WORDLISTS)
    if args.alpha_skip:
        alpha_candidates = alpha_candidates[args.alpha_skip:]
        print(f"[*] scope: skipped first {args.alpha_skip:,} alphabet candidates")
    if args.alpha_limit:
        alpha_candidates = alpha_candidates[:args.alpha_limit]
    if args.key_limit:
        key_candidates = key_candidates[:args.key_limit]

    total_pairs = len(alpha_candidates) * len(key_candidates)
    escape_work_units = sum(len(v) for v in target_escapes.values()) * 2 * 2
    total_tests = total_pairs * escape_work_units
    print(f"[*] {len(alpha_candidates):,} alphabet candidates x {len(key_candidates):,} "
          f"keystream candidates = {total_pairs:,} pairs (~{total_tests:,} decode-attempts), "
          f"{args.workers} worker(s), chunk size {args.chunk_size}")
    print(f"[*] targets: {sorted(target_escapes)}  escapes: {target_escapes}")

    fingerprint = run_fingerprint(alpha_candidates, key_candidates, target_escapes)
    print(f"[*] fingerprint: alpha_digest={fingerprint['alpha_digest']} "
          f"key_digest={fingerprint['key_digest']} driver_sha256={fingerprint['driver_sha256']}")

    lock = acquire_run_lock(args.checkpoint, args.hits_out)
    try:
        if args.workers == 1:
            _run_sequential(alpha_candidates, key_candidates, target_escapes,
                             args.hits_out, args.checkpoint, fingerprint)
        else:
            _run_parallel(alpha_candidates, key_candidates, target_escapes,
                          args.hits_out, args.checkpoint, fingerprint,
                          args.workers, args.chunk_size)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
