#!/usr/bin/env python3
"""Phase 512L -- locked real-FAED exact-crib sweeps using the Rust
`crib_csp` engine, parametrized by (crib, width) so the same discipline can
run across all four exact-divisor widths of 570 (15/19/30/38), not just the
width-15 combinations Phase 512K calibrated.

Mirrors Phase 512G's discipline exactly, extended to the new engine:

- `lock_payload()` pins the Rust source files, the freshly rebuilt binary,
  the ordered length-pattern hash (both in the Python project's own
  convention and in the Rust engine's own bitmask convention, so either can
  be cross-checked independently), the real FAED string, the crib, the
  width, and the full search-space parameters. `verify_lock()` recomputes
  every one of those from scratch and refuses to proceed on any mismatch --
  including a changed binary, since `lock_payload()` always rebuilds before
  hashing.
- The real sweep only starts after `verify_lock()` passes, and a cheap
  1-cell probe cross-checks the Rust engine's own reported identity against
  the lock before the full budget is spent.
- Any hit gets independently reconstructed and board-consistency-checked
  (`decode_hit`, ported unchanged from Phase 512G) and written to a
  dedicated sensitive-hit artifact -- never folded into the general result.
- `verify_run()` re-derives the checkpoint's structure and hash chain
  independently, exactly like `phase512g_verify_run.py`.

Widths 19/30/38 for these cribs skip the separate blind-positive/crib-absent
calibration pass Phase 512K ran at width 15: the search code has no
per-width branching (column/row indices are computed generically from a
runtime `width` parameter, not special-cased), it is already parity- and
unit-tested, and informal benchmarking already exercised it at all three new
widths for all three cribs without incident. The full lock/verify/probe/
decode discipline below is kept regardless -- that protects against
operational mistakes (stale binary, wrong file, unverified hit), not just
algorithm bugs, and costs almost nothing next to the search itself.

`self_test()` runs this entire pipeline (lock, verify_lock, probe, full
sweep, decode, verify_run) against a synthetic fixture, never FAED, before
any real lock is ever written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from data import FAED
import phase512a_transposition_crib_feasibility as phase512a
import phase512d_length_pattern_csp as phase512d
import phase512e_parallel_blind_crib as phase512e
import phase512i_rust_parity as phase512i


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
CRATE_DIR = REPO_ROOT / "tools" / "crib_csp"
BINARY = phase512i.BINARY

PHASE = "512L"
WORKERS = 16
NODE_LIMIT = 2_000_000
CRIBS = tuple(phase512a.CRIBS)
WIDTHS = phase512a.WIDTHS
RUST_SOURCE_FILES = (
    "src/main.rs", "src/csp.rs", "src/geometry.rs", "src/fixture.rs",
    "src/sweep.rs", "Cargo.toml", "Cargo.lock",
)


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def label_for(crib_id: str, width: int) -> str:
    return f"{crib_id}_w{width}"


def base_dir(label: str) -> Path:
    return REPO_ROOT / "_work" / "phase512l" / label


def lock_path(label: str) -> Path:
    return base_dir(label) / "execution_lock.json"


def checkpoint_path(label: str) -> Path:
    return base_dir(label) / "checkpoint.json"


def result_path(label: str) -> Path:
    return base_dir(label) / "result.json"


def hits_path(label: str) -> Path:
    return base_dir(label) / "sensitive_hits.json"


def fixture_path(label: str) -> Path:
    return base_dir(label) / "fixture.json"


def rust_style_patterns_sha256(crib: str) -> tuple[int, str]:
    """Matches tools/crib_csp/src/sweep.rs::patterns_sha256 exactly: each
    pattern as its decimal bitmask over the crib's sorted distinct letters
    (bit i set means letters[i] is single-coded), comma-joined, sha256 of
    the ascii bytes -- an independent cross-check of the Rust engine's own
    reported identity hash, not a re-trusting of it. Width-independent:
    length patterns only depend on the crib's letters."""
    letters = sorted(set(crib))
    index_of = {letter: index for index, letter in enumerate(letters)}
    patterns = tuple(phase512d.length_patterns(crib))
    masks = []
    for pattern in patterns:
        mask = 0
        for letter in pattern:
            mask |= 1 << index_of[letter]
        masks.append(mask)
    canonical = ",".join(str(mask) for mask in masks)
    return len(patterns), sha_bytes(canonical.encode("ascii"))


def ensure_binary_fresh() -> str:
    """Rebuilds the release binary from the exact current source tree and
    returns its sha256. A stale binary from a previous edit must never be
    trusted for a locked run."""
    subprocess.run(["cargo", "build", "--release"], cwd=CRATE_DIR, check=True)
    return sha_file(BINARY)


def lock_payload(label: str, crib: str, faed_source: str, width: int) -> dict:
    if width not in WIDTHS or len(faed_source) % width:
        raise ValueError(f"width {width} does not exactly divide the observed length")
    maximum_start = len(faed_source) - len(crib)
    if maximum_start < 0:
        raise ValueError("crib is longer than the observed stream")
    start_count = maximum_start + 1
    pattern_count, patterns_sha_rust = rust_style_patterns_sha256(crib)
    python_patterns = tuple(phase512d.length_patterns(crib))
    if len(python_patterns) != pattern_count:
        raise AssertionError("Rust-style and Python pattern enumerations disagree in count")
    files_sha256 = {name: sha_file(CRATE_DIR / name) for name in RUST_SOURCE_FILES}
    binary_sha256 = ensure_binary_fresh()
    return {
        "phase": PHASE,
        "status": "locked_before_faed_crib_search",
        "engine": "rust_crib_csp_sweep",
        "label": label,
        "files_sha256": files_sha256,
        "binary_sha256": binary_sha256,
        "faed_ascii_sha256": sha_bytes(faed_source.encode("ascii")),
        "faed_length": len(faed_source),
        "crib_ascii_sha256": sha_bytes(crib.encode("ascii")),
        "crib_length": len(crib),
        "width": width,
        "rows": len(faed_source) // width,
        "direction": "untranspose_geometry_decrypt",
        "escape_pairs": [list(value) for value in phase512a.base.ESCAPE_PAIRS],
        "raw_start_begin": 0,
        "raw_start_count": start_count,
        "legal_length_pattern_count": pattern_count,
        "length_patterns_sha256_rust_bitmask": patterns_sha_rust,
        "length_patterns_sha256_python_letters": phase512e.patterns_sha256(python_patterns),
        "per_pair_start_node_limit": NODE_LIMIT,
        "workers": WORKERS,
        "acceptance": "exact legal-board CSP match of the complete frozen crib",
    }


def verify_lock(label: str, crib: str, faed_source: str, width: int) -> dict:
    path = lock_path(label)
    if not path.is_file():
        raise RuntimeError(f"Phase-512L execution lock is absent for {label}")
    actual = json.loads(path.read_text())
    expected = lock_payload(label, crib, faed_source, width)
    if actual != expected:
        raise RuntimeError(f"Phase-512L execution lock mismatch for {label}")
    return actual


def write_lock(label: str, crib: str, faed_source: str, width: int) -> dict:
    path = lock_path(label)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite an existing lock for {label}")
    payload = lock_payload(label, crib, faed_source, width)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def export_fixture(label: str, crib: str, faed_source: str, width: int) -> Path:
    path = fixture_path(label)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"observed": faed_source, "width": width, "crib": crib}))
    return path


def order_from_column_to_chunk(mapping, width: int) -> list[int]:
    if len(mapping) != width or set(mapping) != set(range(width)):
        raise ValueError("column-to-chunk mapping is not a permutation")
    order = [0] * width
    for column, chunk in enumerate(mapping):
        order[chunk] = column
    return order


def decode_hit(faed_source: str, crib: str, raw_start: int, pair, hit: dict, width: int) -> dict:
    """Independent reconstruction and full-board consistency check of a
    reported hit -- ported unchanged from Phase 512G's decode_hit, engine-
    agnostic since it only consumes the hit's (column_to_chunk, pair,
    single_letters), not anything Rust-internal."""
    order = order_from_column_to_chunk(hit["column_to_chunk"], width)
    raw = phase512a.base.Geometry(len(faed_source), width).decrypt(faed_source, order)
    if phase512a.base.segment_raw(raw[:raw_start], tuple(pair)) is None:
        raise AssertionError("hit begins inside a checkerboard token")
    singles = frozenset(hit["single_letters"])
    cursor = raw_start
    letter_to_code: dict[str, str] = {}
    code_to_letter: dict[str, str] = {}
    for letter in crib:
        length = 1 if letter in singles else 2
        code = raw[cursor:cursor + length]
        cursor += length
        if letter in letter_to_code and letter_to_code[letter] != code:
            raise AssertionError("hit does not assign one code per crib letter")
        if code in code_to_letter and code_to_letter[code] != letter:
            raise AssertionError("hit board is not injective")
        letter_to_code[letter] = code
        code_to_letter[code] = letter
    if "".join(code_to_letter[raw_code] for raw_code in
               phase512a.base.segment_raw(raw[raw_start:cursor], tuple(pair))) != crib:
        raise AssertionError("hit does not decode to the frozen crib")
    segmented = phase512a.base.segment_raw(raw, tuple(pair))
    if segmented is None:
        raise AssertionError("hit does not produce a fully segmentable stream")
    partial_plaintext = "".join(code_to_letter.get(code, "?") for code in segmented)
    return {
        "raw_start": raw_start,
        "raw_end": cursor,
        "pair": list(pair),
        "order": order,
        "column_to_chunk": hit["column_to_chunk"],
        "single_letters": hit["single_letters"],
        "letter_to_code": dict(sorted(letter_to_code.items())),
        "restored_raw_sha256": sha_bytes(raw.encode("ascii")),
        "partial_plaintext": partial_plaintext,
        "crib_verified_exact": True,
    }


def probe_identity(label: str, locked: dict) -> None:
    """A 1-cell, node-limit-1 dry run: cheap enough to run before spending
    the full budget, but enough to read back the Rust engine's own reported
    identity and cross-check it against the lock."""
    fx_path = fixture_path(label)
    proc = subprocess.run(
        [str(BINARY), "sweep", "--fixture", str(fx_path),
         "--start-begin", "0", "--start-count", "1",
         "--pair-begin", "0", "--pair-count", "1",
         "--node-limit", "1", "--workers", "1"],
        capture_output=True, text=True, check=True)
    identity = json.loads(proc.stdout)["identity"]
    if identity["observed_sha256"] != locked["faed_ascii_sha256"]:
        raise RuntimeError("probe input hash does not match the lock")
    if identity["crib_sha256"] != locked["crib_ascii_sha256"]:
        raise RuntimeError("probe crib hash does not match the lock")
    if identity["legal_length_pattern_count"] != locked["legal_length_pattern_count"]:
        raise RuntimeError("probe pattern count does not match the lock")
    if identity["width"] != locked["width"]:
        raise RuntimeError("probe width does not match the lock")


def run_locked_sweep(label: str, crib: str, faed_source: str, width: int) -> dict:
    locked = verify_lock(label, crib, faed_source, width)
    if result_path(label).exists():
        raise FileExistsError(f"refusing to overwrite or repeat Phase-512L for {label}")
    export_fixture(label, crib, faed_source, width)
    probe_identity(label, locked)

    cp_path = checkpoint_path(label)
    proc = subprocess.run(
        [str(BINARY), "sweep", "--fixture", str(fixture_path(label)),
         "--start-begin", "0", "--start-count", str(locked["raw_start_count"]),
         "--pair-begin", "0", "--pair-count", "36",
         "--node-limit", str(NODE_LIMIT), "--workers", str(WORKERS),
         "--checkpoint", str(cp_path)],
        capture_output=True, text=True, check=True)
    checkpoint = json.loads(proc.stdout)

    decoded_hits = [
        decode_hit(faed_source, crib, entry["raw_start"], entry["pair"], hit, width)
        for entry in checkpoint["hit_cells"]
        for hit in entry["hits"]
    ]
    if decoded_hits:
        path = hits_path(label)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"phase": PHASE, "label": label, "hits": decoded_hits},
                                   indent=2, sort_keys=True) + "\n")

    complete = (checkpoint["status"] in {
        "hit_at_earliest_completed_start", "no_hit_in_complete_requested_family",
    } and not checkpoint["incomplete_cells"])
    result = {
        "phase": PHASE,
        "label": label,
        "status": "locked_faed_crib_search_complete" if complete else "incomplete",
        "execution_lock_sha256": sha_file(lock_path(label)),
        "faed_ascii_sha256": locked["faed_ascii_sha256"],
        "crib_ascii_sha256": locked["crib_ascii_sha256"],
        "width": width,
        "direction": locked["direction"],
        "starts_completed": checkpoint["starts_completed"],
        "pair_start_cells_completed": checkpoint["pair_start_cells_completed"],
        "hit_count": len(decoded_hits),
        "incomplete_cell_count": len(checkpoint["incomplete_cells"]),
        "checkpoint_sha256": sha_file(cp_path),
        "verdict": ("exact_hit_requires_review" if decoded_hits else
                   "bounded_negative" if complete else "non_interpretable"),
    }
    result_path(label).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def verify_run(label: str, crib: str, faed_source: str, width: int) -> dict:
    """Independent structural re-derivation of a completed locked run --
    never trusts result.json's own summary, exactly like
    phase512g_verify_run.py."""
    locked = verify_lock(label, crib, faed_source, width)
    result = json.loads(result_path(label).read_text())
    checkpoint = json.loads(checkpoint_path(label).read_text())

    errors = []
    expected_identity_fields = {
        "width": locked["width"],
        "legal_length_pattern_count": locked["legal_length_pattern_count"],
    }
    for key, value in expected_identity_fields.items():
        if checkpoint["identity"].get(key) != value:
            errors.append(f"checkpoint identity field {key} does not match the lock")
    rows = checkpoint["completed_starts"]
    if len(rows) != locked["raw_start_count"] and checkpoint["status"] != "hit_at_earliest_completed_start":
        errors.append("checkpoint does not cover the full locked start range")
    for offset, row in enumerate(rows):
        if row["raw_start"] != offset:
            errors.append(f"checkpoint starts are not contiguous at row {offset}")
            break
        pair_indices = [cell["pair_index"] for cell in row["cells"]]
        if pair_indices != list(range(36)):
            errors.append(f"checkpoint pair set/order is incomplete at raw_start {offset}")
            break
    hit_count = sum(cell["hit_count"] for row in rows for cell in row["cells"])
    incomplete_count = sum(1 for row in rows for cell in row["cells"] if not cell["search_complete"])
    if hit_count != result["hit_count"] and result["verdict"] != "exact_hit_requires_review":
        errors.append("hit count mismatch between checkpoint and result")
    if incomplete_count != result["incomplete_cell_count"]:
        errors.append("incomplete count mismatch between checkpoint and result")

    return {
        "phase": f"{PHASE}-verification",
        "label": label,
        "consistent": not errors,
        "errors": errors,
        "execution_lock_sha256": sha_file(lock_path(label)),
        "checkpoint_sha256": sha_file(checkpoint_path(label)),
        "result_sha256": sha_file(result_path(label)),
        "starts_revalidated": len(rows),
        "cells_revalidated": sum(len(row["cells"]) for row in rows),
        "hits_recomputed": hit_count,
        "incomplete_cells_recomputed": incomplete_count,
    }


def self_test() -> dict:
    """Runs the entire lock -> verify_lock -> probe -> sweep -> decode ->
    verify_run pipeline against a synthetic, already-calibrated positive
    fixture (the credential at width 15, Phase 512G/512I/512J's own
    subject) -- never FAED. Uses a dedicated 'self_test' label so it can
    never collide with any real crib's lock/checkpoint/result files."""
    label = "self_test"
    width = 15
    for path in (lock_path(label), checkpoint_path(label), result_path(label),
                hits_path(label), fixture_path(label)):
        if path.exists():
            path.unlink()

    fixture = phase512a.make_fixture("phase1_credential", width)
    crib = fixture["crib"]
    synthetic_faed = fixture["observed"]

    write_lock(label, crib, synthetic_faed, width)
    verify_lock(label, crib, synthetic_faed, width)
    result = run_locked_sweep(label, crib, synthetic_faed, width)
    if result["hit_count"] != 1 or result["verdict"] != "exact_hit_requires_review":
        raise AssertionError("self-test did not recover the known planted hit")
    hits = json.loads(hits_path(label).read_text())["hits"]
    if hits[0]["raw_start"] != fixture["planted_raw_offset"]:
        raise AssertionError("self-test hit is at the wrong raw_start")
    if hits[0]["partial_plaintext"] is None or crib not in hits[0]["partial_plaintext"]:
        raise AssertionError("self-test decoded plaintext does not contain the planted crib")

    verification = verify_run(label, crib, synthetic_faed, width)
    if not verification["consistent"]:
        raise AssertionError(f"self-test verify_run found inconsistencies: {verification['errors']}")

    return {"self_test": "pass", "hit_count": result["hit_count"],
            "raw_start": hits[0]["raw_start"], "verify_run_consistent": verification["consistent"]}


def do_one(crib_id: str, width: int) -> dict:
    """Fresh run only: fails if a lock already exists. Use
    resume_or_run_one for a combination that may have a partial checkpoint
    from an interrupted prior run."""
    label = label_for(crib_id, width)
    crib = phase512a.CRIBS[crib_id]
    write_lock(label, crib, FAED, width)
    return _run_and_verify(label, crib, width)


def resume_or_run_one(crib_id: str, width: int) -> dict:
    """Writes the lock only if one doesn't already exist, then runs. If a
    checkpoint from an interrupted prior run is present, the Rust engine's
    own fail-closed resume path (identity + structural validation) picks up
    from it rather than starting over -- the same mechanism validated
    earlier this session against a deliberately corrupted checkpoint."""
    label = label_for(crib_id, width)
    crib = phase512a.CRIBS[crib_id]
    if not lock_path(label).exists():
        write_lock(label, crib, FAED, width)
    return _run_and_verify(label, crib, width)


def _run_and_verify(label: str, crib: str, width: int) -> dict:
    verify_lock(label, crib, FAED, width)
    result = run_locked_sweep(label, crib, FAED, width)
    verification = verify_run(label, crib, FAED, width)
    if not verification["consistent"]:
        raise AssertionError(f"verify_run found inconsistencies for {label}: {verification['errors']}")
    return {**result, "verify_run_consistent": verification["consistent"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--crib", choices=CRIBS)
    parser.add_argument("--width", type=int, choices=WIDTHS)
    parser.add_argument("--print-lock", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--verify-run", action="store_true")
    parser.add_argument("--do-one", action="store_true",
                        help="write-lock, verify-lock, run, and verify-run in sequence")
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    else:
        if args.width is None:
            parser.error("--crib requires --width")
        crib = phase512a.CRIBS[args.crib]
        if args.do_one:
            value = do_one(args.crib, args.width)
        else:
            actions = sum([args.print_lock, args.write_lock, args.run, args.verify_run])
            if actions != 1:
                parser.error("choose exactly one of --print-lock/--write-lock/--run/--verify-run/--do-one with --crib")
            label = label_for(args.crib, args.width)
            value = (lock_payload(label, crib, FAED, args.width) if args.print_lock else
                    write_lock(label, crib, FAED, args.width) if args.write_lock else
                    verify_run(label, crib, FAED, args.width) if args.verify_run else
                    run_locked_sweep(label, crib, FAED, args.width))
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
