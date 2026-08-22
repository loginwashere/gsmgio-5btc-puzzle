#!/usr/bin/env python3
"""Phase 374: corrected-oracle backfill for Phase 11's frozen hash-duality
candidate family, per the user's exact 2026-08-22 staged sequencing.

Phase 11 (2026-07-23) tested 11,899 candidate answers x 4 verified prior
command hashes -> 1,427,880 byte-exact passphrase materials against
`cb_common.aes_try_open_bytes`, and reported 0 hits, 25.4s. Two coverage
defects have since been identified, independent of this project's later
topology work (Phases 369-373):

  1. `aes_try_open_bytes` is a shared, LIVE function -- Phase 11's original
     run on 2026-07-23 used whatever printability gate and blob set existed
     that day, not today's. P32TRAILING was added to `cb_common.BLOBS` on
     2026-07-24 (one day after Phase 11 ran) and URLBLOB was folded in by
     Phase 192; Phase 78's printability-gate fix (moving from a binary
     ratio cutoff that could reject a valid non-ASCII-heavy plaintext to a
     two-tier z-score gate) came later still. This is exactly the
     stale-oracle pattern Phase 368 found and closed for Phase 75's
     YOUWON/YOUWONX set -- but at genuine scale here, not Phase 368's small
     candidate pool: ~11,899 x 4 x 16 x 2 = ~1.4M materials, not ~18.
  2. Phase 11's own write-up claims "raw, LF, and CRLF passphrase forms"
     were tested, but the recorded count (1,427,880) exactly matches
     `material_forms(..., newline_variants=False)` (2 forms/material: raw,
     hex) -- NOT the `newline_variants=True` path (up to 6 forms/material).
     Enabling newline variants yields 4,283,640 materials (confirmed by
     direct regeneration in self_test()). The LF/CRLF forms were never
     actually run against the oracle.

Per the user's exact staged plan, this script keeps these bounded and
separately costed rather than folding them into one "oracle fix" claim:

  Stage 1 -- freeze_manifest(): regenerate and digest the exact 11,899
    candidates, 4 prior hashes, and 1,427,880 historical no-newline
    materials, asserting they match Phase 11's recorded counts exactly.
    Protects against silently regenerating a DIFFERENT candidate set under
    the same phase number if upstream generation ever drifts.
  Stage 2 -- run_corrected_cbc_backfill(): those exact frozen materials
    through the CURRENT CBC oracle (`cb_common.KDF_VARIANTS`, 6 combos,
    deliberately AES-CBC-only) across all 4 current default blobs (SALPH/
    COSMIC/P32TRAILING/URLBLOB), passed explicitly so this stage's scope
    cannot silently drift with a future cb_common default change. This
    directly repairs the demonstrated Phase-78/blob-set false-negative
    surface, still CBC-only.
  Stage 3 -- run_newline_delta_backfill(): separately runs ONLY the
    materials `newline_variants=True` adds beyond Stage 2's frozen set,
    under the identical corrected CBC oracle. Recorded separately so the
    original overstatement is documented, not silently absorbed into
    Stage 2's count.
  Stage 4 -- NOT executed here. ECB/stream/AES-Key-Wrap widening on top of
    this ~4.28M-material family is a separately costed experiment (~480M+
    nominal decrypt combinations at full width) and must be preregistered
    on its own, per this project's own P0A/P1A "bounded, disclosed
    contract" convention (doc/Brainstorms/2026-08-15 - Passphrase Oracle
    False-Negative Surface.md, "Reopening rules": endpoint contracts must
    be bounded, counted, and separately authorized -- not silently
    absorbed into an unrelated fix).

Topology caveat (preserved per the user's explicit instruction): a
negative result here closes the FROZEN hash-duality candidate family's
oracle coverage. It says nothing about, and does not validate, the
inherited linear-chain topology edge this candidate family's own
generation logic assumes (doc/GSMG_TOPOLOGY_AUDIT.md) -- Phases 369-373
already established that edge as unresolved/a tie (most recently, Phase
373's corrected verdict left `thispassword`'s own attachment a genuine,
uncalibrated three-way tie). Nothing here changes that.

Usage:
    python3 tools/gsmg/hash_duality_corrected_oracle_backfill.py --self-test
    python3 tools/gsmg/hash_duality_corrected_oracle_backfill.py --run
"""
import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import islice
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cb_common import BLOBS, KDF_VARIANTS, aes_try_open_bytes  # noqa: E402
from hash_duality_sweep import (  # noqa: E402
    collect_candidates,
    material_forms,
    operation_materials,
    selected_prior_hashes,
)

EXPECTED_CANDIDATE_COUNT = 11_899
EXPECTED_PRIOR_HASH_COUNT = 4
EXPECTED_NO_NEWLINE_MATERIAL_COUNT = 1_427_880
EXPECTED_WITH_NEWLINE_MATERIAL_COUNT = 4_283_640


def frozen_candidates_and_hashes():
    """Regenerates today's live candidate/prior-hash set and asserts it
    still matches Phase 11's recorded counts -- if upstream candidate
    generation (matrix_instruction_sweep.py) ever drifts, this fails loudly
    instead of silently rerunning a different set under Phase 11's name."""
    candidate_map = collect_candidates("all")
    candidates = [(label, value) for value, label in candidate_map.items()]
    prior_hashes = selected_prior_hashes(False)
    if len(candidates) != EXPECTED_CANDIDATE_COUNT:
        raise AssertionError(
            f"candidate generation drifted since Phase 11: "
            f"{len(candidates)} != {EXPECTED_CANDIDATE_COUNT}"
        )
    if len(prior_hashes) != EXPECTED_PRIOR_HASH_COUNT:
        raise AssertionError("prior-hash count drifted since Phase 11")
    return candidates, prior_hashes


# Pinned same-day (user review): a matching COUNT is not evidence of a
# matching CANDIDATE SET -- a changed generator that happens to still
# produce 11,899 candidates (e.g. a swapped or reordered subset) would
# pass a count-only check while genuinely testing a different manifest
# under Phase 11's name. This exact digest was computed and verified once,
# from the real Stage 2/3 run recorded in FINDINGS.md Phase 374
# (2026-08-22), and is now the actual freeze.
EXPECTED_MATERIAL_DIGEST_SHA256 = (
    "425860df33d961d39c2116b5ac477249ceb043ff1ac744e130da55a2b13106ae"
)


def freeze_manifest():
    """Stage 1: regenerate and digest the frozen no-newline material set
    (single-process, streamed -- no need to hold ~1.4M materials in memory
    at once just to count and hash them). Asserts against the exact pinned
    digest, not merely the material count."""
    candidates, prior_hashes = frozen_candidates_and_hashes()
    digest = hashlib.sha256()
    count = 0
    for candidate_label, answer in candidates:
        tested = set()
        for prior_label, previous_hex in prior_hashes:
            for operation, material in operation_materials(previous_hex, answer).items():
                for _representation, passphrase in material_forms(material, False):
                    if passphrase in tested:
                        continue
                    tested.add(passphrase)
                    digest.update(passphrase)
                    digest.update(b"|")
                    count += 1
    if count != EXPECTED_NO_NEWLINE_MATERIAL_COUNT:
        raise AssertionError(
            f"no-newline material count drifted since Phase 11: "
            f"{count} != {EXPECTED_NO_NEWLINE_MATERIAL_COUNT}"
        )
    digest_hex = digest.hexdigest()
    if digest_hex != EXPECTED_MATERIAL_DIGEST_SHA256:
        raise AssertionError(
            f"material digest drifted since Phase 374 despite matching count "
            f"({count}): {digest_hex} != {EXPECTED_MATERIAL_DIGEST_SHA256} -- "
            "the candidate SET changed even though its size did not"
        )
    return {
        "candidate_count": len(candidates),
        "prior_hash_count": len(prior_hashes),
        "no_newline_material_count": count,
        "material_digest_sha256": digest_hex,
    }


def delta_forms(material):
    """The forms `newline_variants=True` adds beyond `False` for one
    material: raw_lf, raw_crlf, hex_lf, hex_crlf -- deduped against the
    raw/hex forms Stage 2 already covers, and against each other."""
    base = {body for _label, body in material_forms(material, False)}
    return [
        (label, body)
        for label, body in material_forms(material, True)
        if body not in base
    ]


# ---------------------------------------------------------------------------
# Stage 2: corrected CBC oracle over the frozen no-newline materials.
# Mirrors hash_duality_sweep.py's own candidate-batched worker architecture
# (proven fast: 1.4M materials in 25.4s under the ORIGINAL, narrower blob
# set) rather than pre-materializing a multi-million-entry list.
# ---------------------------------------------------------------------------

def _cbc_test_candidate(candidate, prior_hashes):
    candidate_label, answer = candidate
    tested = set()
    attempts = 0
    hits = []
    for prior_label, previous_hex in prior_hashes:
        for operation, material in operation_materials(previous_hex, answer).items():
            for representation, passphrase in material_forms(material, False):
                if passphrase in tested:
                    continue
                tested.add(passphrase)
                attempts += 1
                result = aes_try_open_bytes(passphrase, kdf_variants=KDF_VARIANTS, blobs=BLOBS)
                if result:
                    tag, plaintext, digest_name, key_len = result
                    hits.append({
                        "candidate_label": candidate_label, "answer": answer,
                        "prior_hash": prior_label, "operation": operation,
                        "representation": representation,
                        "passphrase_hex": passphrase.hex(), "blob": tag,
                        "kdf": f"{digest_name}/aes{key_len * 8}",
                        "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                    })
    return attempts, hits


def _delta_test_candidate(candidate, prior_hashes):
    """Tests only the materials `newline_variants=True` adds beyond what
    Stage 2 already covers for this candidate. Uses one running `tested`
    set across ALL of the candidate's operations/prior-hashes -- not
    `delta_forms()` per material in isolation -- because a small number of
    materials collide byte-for-byte across DIFFERENT operations within the
    same candidate (this is exactly why the true with-newline total,
    4,283,640, is less than the naive 761,536 x 4 = 3,046,144 upper bound;
    see self_test()). Skipping that candidate-wide dedup would both
    over-count attempts and, more importantly, could silently miss that a
    "new" delta form was already tested as a Stage-2 base form under a
    different operation's name."""
    candidate_label, answer = candidate
    tested = set()
    for prior_label, previous_hex in prior_hashes:
        for operation, material in operation_materials(previous_hex, answer).items():
            for _representation, passphrase in material_forms(material, False):
                tested.add(passphrase)

    attempts = 0
    hits = []
    for prior_label, previous_hex in prior_hashes:
        for operation, material in operation_materials(previous_hex, answer).items():
            for representation, passphrase in material_forms(material, True):
                if passphrase in tested:
                    continue
                tested.add(passphrase)
                attempts += 1
                result = aes_try_open_bytes(passphrase, kdf_variants=KDF_VARIANTS, blobs=BLOBS)
                if result:
                    tag, plaintext, digest_name, key_len = result
                    hits.append({
                        "candidate_label": candidate_label, "answer": answer,
                        "prior_hash": prior_label, "operation": operation,
                        "representation": representation,
                        "passphrase_hex": passphrase.hex(), "blob": tag,
                        "kdf": f"{digest_name}/aes{key_len * 8}",
                        "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                    })
    return attempts, hits


def _batch(worker_fn, batch, prior_hashes):
    attempts = 0
    hits = []
    for candidate in batch:
        candidate_attempts, candidate_hits = worker_fn(candidate, prior_hashes)
        attempts += candidate_attempts
        hits.extend(candidate_hits)
    return len(batch), attempts, hits


def _cbc_batch(batch, prior_hashes):
    return _batch(_cbc_test_candidate, batch, prior_hashes)


def _delta_batch(batch, prior_hashes):
    return _batch(_delta_test_candidate, batch, prior_hashes)


def _run_staged(label, batch_fn, candidates, prior_hashes, workers=None, chunk_size=20):
    workers = workers or min(os.cpu_count() or 4, 16)
    chunks = [candidates[i:i + chunk_size] for i in range(0, len(candidates), chunk_size)]
    print(f"[*] {label}: {len(candidates):,} candidates, {workers} workers")
    start = time.time()
    completed = 0
    attempts = 0
    hits = []
    max_in_flight = max(workers * 4, 8)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        chunk_iter = iter(chunks)
        in_flight = {}
        for chunk in islice(chunk_iter, max_in_flight):
            future = executor.submit(batch_fn, chunk, prior_hashes)
            in_flight[future] = len(chunk)
        while in_flight:
            done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in done:
                in_flight.pop(future)
                count, batch_attempts, batch_hits = future.result()
                completed += count
                attempts += batch_attempts
                hits.extend(batch_hits)
                for hit in batch_hits:
                    print(f"\n[+++ AES HIT] {hit}\n")
                nxt = next(chunk_iter, None)
                if nxt is not None:
                    nf = executor.submit(batch_fn, nxt, prior_hashes)
                    in_flight[nf] = len(nxt)
            elapsed = time.time() - start
            rate = completed / max(elapsed, 1e-9)
            print(
                f"\r[*] {label}: {completed:,}/{len(candidates):,} candidates "
                f"({rate:.1f}/s), {attempts:,} passphrases, hits={len(hits)}   ",
                end="", flush=True,
            )
    print()
    elapsed = time.time() - start
    return {
        "label": label, "candidate_count": len(candidates),
        "passphrase_attempts": attempts, "hits": hits,
        "elapsed_seconds": round(elapsed, 3),
    }


def run_corrected_cbc_backfill(candidates, prior_hashes, workers=None):
    """Stage 2."""
    return _run_staged("stage2_corrected_cbc", _cbc_batch, candidates, prior_hashes, workers)


def run_newline_delta_backfill(candidates, prior_hashes, workers=None):
    """Stage 3."""
    return _run_staged("stage3_newline_delta", _delta_batch, candidates, prior_hashes, workers)


def full_run(workers=None):
    manifest = freeze_manifest()
    candidates, prior_hashes = frozen_candidates_and_hashes()
    stage2 = run_corrected_cbc_backfill(candidates, prior_hashes, workers)
    stage3 = run_newline_delta_backfill(candidates, prior_hashes, workers)
    return {
        "manifest": manifest,
        "stage2_corrected_cbc": stage2,
        "stage3_newline_delta": stage3,
        "stage4_ecb_stream_keywrap": "NOT RUN -- separately costed, ~480M+ nominal decrypt combinations, requires its own preregistered contract",
        "topology_caveat": (
            "Closes oracle coverage for the frozen hash-duality candidate "
            "family only. Does not validate the inherited linear-chain "
            "topology edge (doc/GSMG_TOPOLOGY_AUDIT.md); Phases 369-373 "
            "leave that edge unresolved/a tie."
        ),
    }


def self_test():
    # 1. Manifest freeze reproduces Phase 11's recorded counts exactly.
    manifest = freeze_manifest()
    assert manifest["candidate_count"] == EXPECTED_CANDIDATE_COUNT
    assert manifest["prior_hash_count"] == EXPECTED_PRIOR_HASH_COUNT
    assert manifest["no_newline_material_count"] == EXPECTED_NO_NEWLINE_MATERIAL_COUNT

    # 2. The newline-coverage discrepancy is a checked fact, not a claim:
    #    regenerating with newline_variants=True yields exactly 4,283,640,
    #    matching the user's independent computation, and the delta is
    #    exactly the newline-suffixed forms (2,855,760 = 4,283,640 -
    #    1,427,880).
    candidates, prior_hashes = frozen_candidates_and_hashes()
    with_newline_total = 0
    delta_total = 0
    for candidate_label, answer in candidates:
        tested = set()
        for prior_label, previous_hex in prior_hashes:
            for operation, material in operation_materials(previous_hex, answer).items():
                for _label, body in material_forms(material, True):
                    if body not in tested:
                        tested.add(body)
                        with_newline_total += 1
        # delta_total mirrors _delta_test_candidate()'s own two-pass logic
        # exactly (base set first, across ALL operations, THEN count new
        # with-newline forms) -- NOT a per-material sum of delta_forms(),
        # which would over-count whenever two different operations for the
        # same candidate happen to produce byte-identical material (see the
        # docstring on _delta_test_candidate for why that happens here).
        base = set()
        for prior_label, previous_hex in prior_hashes:
            for operation, material in operation_materials(previous_hex, answer).items():
                for _label, body in material_forms(material, False):
                    base.add(body)
        seen = set(base)
        for prior_label, previous_hex in prior_hashes:
            for operation, material in operation_materials(previous_hex, answer).items():
                for _label, body in material_forms(material, True):
                    if body not in seen:
                        seen.add(body)
                        delta_total += 1
    assert with_newline_total == EXPECTED_WITH_NEWLINE_MATERIAL_COUNT
    assert delta_total == EXPECTED_WITH_NEWLINE_MATERIAL_COUNT - EXPECTED_NO_NEWLINE_MATERIAL_COUNT

    # 3. delta_forms() never re-tests a raw/hex form (no double-counting
    #    between Stage 2 and Stage 3 on a real run).
    sample_material = operation_materials(prior_hashes[0][1], "causality")["binary/sha256(previous+answer)"]
    delta = delta_forms(sample_material)
    base = {body for _label, body in material_forms(sample_material, False)}
    assert all(body not in base for _label, body in delta)
    assert len(delta) == 4  # raw_lf, raw_crlf, hex_lf, hex_crlf -- no collisions for this material

    # 4. Oracle-call wiring: stage functions pass KDF_VARIANTS/BLOBS
    #    explicitly by name, not implicit defaults -- but a source-text
    #    check alone only proves the NAMES are referenced; it would still
    #    pass if `cb_common.KDF_VARIANTS`/`BLOBS` themselves later changed
    #    contents while keeping their names. Pin the actual CONTENT: the
    #    exact 6 (digest, key_len) tuples, and a sha256(salt+ciphertext)
    #    fingerprint for all 4 blobs, so a future oracle/blob-set edit
    #    trips this test even though it wouldn't touch this file at all.
    import inspect
    cbc_source = inspect.getsource(_cbc_test_candidate)
    delta_source = inspect.getsource(_delta_test_candidate)
    for source in (cbc_source, delta_source):
        assert "kdf_variants=KDF_VARIANTS" in source
        assert "blobs=BLOBS" in source

    assert KDF_VARIANTS == [
        ("sha256", 32), ("md5", 32), ("sha1", 32),
        ("sha256", 16), ("md5", 16), ("sha1", 16),
    ], "Phase 374's pinned CBC oracle contract (6 legacy KDF/keysize combos) changed"

    EXPECTED_BLOB_FINGERPRINTS_SHA256 = {
        "SALPH": "d11e65409bc5d47ae6fef79d0d1d91d1582000fcf225886c93fc72ad47608c9c",
        "COSMIC": "6447f7891498fff6a1812ac967bab5153dfd599009f4c9afd431e67b4a7ecb63",
        "P32TRAILING": "20335e1ed391d87601d8916bcd61f03c00776b25b3253ed2efb80301010b712f",
        "URLBLOB": "fc4a742795679b71eda020983c88dd3f6c7ded545daa1b6ba749e01b501c4ab7",
    }
    assert set(BLOBS) == set(EXPECTED_BLOB_FINGERPRINTS_SHA256)
    for tag, (salt, ciphertext) in BLOBS.items():
        fingerprint = hashlib.sha256(salt + ciphertext).hexdigest()
        assert fingerprint == EXPECTED_BLOB_FINGERPRINTS_SHA256[tag], (
            f"blob {tag!r} content changed since Phase 374's run: "
            f"{fingerprint} != {EXPECTED_BLOB_FINGERPRINTS_SHA256[tag]}"
        )

    print(
        "[*] self-test OK: Phase 11's manifest reproduces exactly "
        f"({manifest['candidate_count']:,} candidates x "
        f"{manifest['prior_hash_count']} prior hashes -> "
        f"{manifest['no_newline_material_count']:,} no-newline materials, "
        f"digest {manifest['material_digest_sha256'][:16]}...); "
        f"newline_variants=True regenerates exactly "
        f"{with_newline_total:,} materials (matches the user's independent "
        f"computation), delta = {delta_total:,} materials never previously "
        "tested despite Phase 11's write-up claiming LF/CRLF coverage; "
        "Stage 2/3 oracle calls are pinned to KDF_VARIANTS/BLOBS explicitly"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="execute Stage 1-3 for real")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--json-out")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.run:
        print("[*] pass --self-test or --run")
        return

    report = full_run(workers=args.workers)
    print(f"\n[*] manifest: {report['manifest']}")
    print(f"[*] stage2 (corrected CBC): {report['stage2_corrected_cbc']['passphrase_attempts']:,} attempts, "
          f"{len(report['stage2_corrected_cbc']['hits'])} hits, {report['stage2_corrected_cbc']['elapsed_seconds']}s")
    print(f"[*] stage3 (newline delta): {report['stage3_newline_delta']['passphrase_attempts']:,} attempts, "
          f"{len(report['stage3_newline_delta']['hits'])} hits, {report['stage3_newline_delta']['elapsed_seconds']}s")
    print(f"[*] stage4: {report['stage4_ecb_stream_keywrap']}")
    print(f"[*] topology caveat: {report['topology_caveat']}")

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=repr), encoding="utf-8")
        print(f"[*] wrote JSON report to {output_path}")


if __name__ == "__main__":
    main()
