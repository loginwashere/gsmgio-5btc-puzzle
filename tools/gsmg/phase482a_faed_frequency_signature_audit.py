#!/usr/bin/env python3
"""Phase 482A: exact FAED frequency-signature scan of a closed text corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common  # noqa: E402
import phase410_solved_vector_toolchain_provenance_audit as p410  # noqa: E402
import p32_sibling_password_audit as p32  # noqa: E402
from checkerboard_code_ic_oracle import segment_codes  # noqa: E402
from data import FAED  # noqa: E402

PHASE = 482
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 482A FAED Plaintext Frequency Signature Protocol.md"
DEFAULT_LOCK = SCRIPT_DIR / "phase482a_execution_lock.json"
DEFAULT_RESULT = SCRIPT_DIR / "phase482a_result.json"
WINDOW = 436
EXPECTED_RAW_LENGTH = 570
EXPECTED_SIGNATURE = (54, 45, 45, 42, 40, 38, 38, 21, 11, 10, 10, 10, 9,
                      8, 8, 7, 6, 5, 5, 5, 5, 4, 4, 4, 2)
LANES = ("ji_merged", "raw_az_25_present")
MATRIX_FILE = REPO_ROOT / "wordlists/gsmg/matrix_architect_scene_through_choice_words.txt"
BOOK_FILE = REPO_ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
NON_PROSE_PATTERNS = (
    r"^Table of Contents", r"INDEX", r"Acknowledgments", r"colophon",
    r"^Back matter", r"^End of transcription", r"^Front matter",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(text: str, lane: str) -> str:
    letters = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
    if lane == "ji_merged":
        return letters.replace("J", "I")
    if lane == "raw_az_25_present":
        return letters
    raise ValueError(f"unknown lane: {lane}")


def signature(text: str) -> tuple[int, ...]:
    return tuple(sorted(Counter(text).values(), reverse=True))


def solved_plaintext(key: str) -> bytes:
    spec = p410.VECTORS[key]
    if spec["textarea_index"] is None:
        raise ValueError(f"{key} is not a Wayback textarea vector")
    textareas = p410.extract_wayback_textareas(p410.WAYBACK_ARTIFACT_PATH)
    raw_b64 = textareas[spec["textarea_index"]]
    salt, ciphertext = cb_common._load_blob(raw_b64.decode("ascii"))
    password = hashlib.sha256(spec["preimage"].encode("utf-8")).hexdigest().encode("ascii")
    _, _, plaintext = p410.decrypt_container(salt, ciphertext, password, "sha256")
    if plaintext is None or not plaintext.startswith(spec["expected_plaintext_prefix"]):
        raise AssertionError(f"lost solved {key} plaintext")
    return plaintext


def book_prose() -> str:
    keep = True
    chunks = []
    for line in BOOK_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:]
            keep = not any(re.search(pattern, name) for pattern in NON_PROSE_PATTERNS)
            continue
        if line.startswith("#") or not keep:
            continue
        chunks.append(line)
    return "\n".join(chunks)


def source_documents() -> list[dict]:
    phase32_plaintext = p32.decrypt_phase32_bytes()
    components = p32.extract_phase32_components(phase32_plaintext)
    derived = p32.derive_sibling_outputs(phase32_plaintext)
    matrix_lines = [
        line for line in MATRIX_FILE.read_text(encoding="utf-8").splitlines()
        if not line.startswith("#")
    ]
    docs = [
        ("phase2_plaintext", "puzzle_native", solved_plaintext("phase2").decode("latin-1")),
        ("phase3_plaintext", "puzzle_native", solved_plaintext("phase3").decode("latin-1")),
        ("phase32_pre_p32_plaintext", "puzzle_native",
         phase32_plaintext[:components["offsets"]["p32_start"]].decode("latin-1")),
        ("phase321_architect_answer", "puzzle_native", derived["answer_321"]),
        ("matrix_architect_scene", "referenced_text", "\n".join(matrix_lines)),
        ("cosmic_duality_book_prose", "book", book_prose()),
    ]
    return [
        {
            "name": name,
            "tier": tier,
            "text": text,
            "extracted_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        for name, tier, text in docs
    ]


def faed_signature() -> tuple[int, ...]:
    codes = segment_codes(FAED, "g", "i")
    if codes is None:
        raise AssertionError("FAED no longer segments under {g,i}")
    if len(FAED) != EXPECTED_RAW_LENGTH or len(codes) != WINDOW or len(set(codes)) != 25:
        raise AssertionError("FAED geometry drift")
    result = tuple(sorted(Counter(codes).values(), reverse=True))
    if result != EXPECTED_SIGNATURE:
        raise AssertionError(f"FAED signature drift: {result}")
    return result


def iter_window_signatures(text: str):
    if len(text) < WINDOW:
        return
    counts = Counter(text[:WINDOW])
    yield 0, tuple(sorted(counts.values(), reverse=True))
    for start in range(1, len(text) - WINDOW + 1):
        outgoing = text[start - 1]
        incoming = text[start + WINDOW - 1]
        counts[outgoing] -= 1
        if counts[outgoing] == 0:
            del counts[outgoing]
        counts[incoming] += 1
        yield start, tuple(sorted(counts.values(), reverse=True))


def source_manifest() -> list[dict]:
    rows = []
    for document in source_documents():
        lane_rows = {}
        for lane in LANES:
            text = normalize(document["text"], lane)
            lane_rows[lane] = {
                "length": len(text),
                "sha256": hashlib.sha256(text.encode("ascii")).hexdigest(),
                "window_count": max(0, len(text) - WINDOW + 1),
            }
        rows.append({
            "name": document["name"],
            "tier": document["tier"],
            "extracted_sha256": document["extracted_sha256"],
            "lanes": lane_rows,
        })
    return rows


def self_test() -> bool:
    target = faed_signature()
    assert sum(target) == WINDOW and len(target) == 25
    docs = source_documents()
    assert len(docs) == 6 and len({row["name"] for row in docs}) == 6
    assert source_manifest() == source_manifest()
    for document in docs:
        for lane in LANES:
            text = normalize(document["text"], lane)
            windows = len(text) - WINDOW + 1
            if windows <= 0:
                continue
            starts = sorted({0, windows // 2, windows - 1})
            rolling = dict(iter_window_signatures(text))
            for start in starts:
                assert rolling[start] == signature(text[start:start + WINDOW])

    fixture = normalize(docs[-1]["text"], "ji_merged")[:WINDOW]
    assert len(fixture) == WINDOW
    relabel = {ch: chr(65 + index) for index, ch in enumerate(sorted(set(fixture)))}
    renamed = "".join(relabel[ch] for ch in fixture)
    permuted = renamed[::2] + renamed[1::2]
    assert signature(fixture) == signature(renamed) == signature(permuted)
    assert normalize("JIGSAW", "ji_merged") != normalize("JIGSAW", "raw_az_25_present")
    assert normalize("FAED", "ji_merged") == normalize("FAED", "raw_az_25_present")
    return True


def lock_payload() -> dict:
    tracked = {
        "protocol": PROTOCOL,
        "audit_script": Path(__file__),
        "verifier": SCRIPT_DIR / "phase482a_verify_run.py",
        "cb_common": SCRIPT_DIR / "cb_common.py",
        "data": SCRIPT_DIR / "data.py",
        "segmenter": SCRIPT_DIR / "checkerboard_code_ic_oracle.py",
        "phase410": SCRIPT_DIR / "phase410_solved_vector_toolchain_provenance_audit.py",
        "p32_sibling": SCRIPT_DIR / "p32_sibling_password_audit.py",
        "wayback_phase23": p410.WAYBACK_ARTIFACT_PATH,
        "readme": REPO_ROOT / "README.md",
        "matrix_scene": MATRIX_FILE,
        "book_transcription": BOOK_FILE,
    }
    return {
        "phase": PHASE,
        "status": "locked-before-real-scan",
        "files_sha256": {name: sha256_file(path) for name, path in tracked.items()},
        "escape_pair": ["g", "i"],
        "raw_length": EXPECTED_RAW_LENGTH,
        "window": WINDOW,
        "target_signature": list(faed_signature()),
        "lanes": list(LANES),
        "source_manifest": source_manifest(),
        "match_rule": "exact equality of all sorted positive symbol counts",
        "near_matches_promote": False,
    }


def write_json_atomic(path: Path, value: dict) -> None:
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def verify_lock(path: Path) -> dict:
    locked = json.loads(Path(path).read_text(encoding="utf-8"))
    if locked != lock_payload():
        raise RuntimeError("execution lock does not match current code, protocol or sources")
    return locked


def issue_lock(path: Path) -> dict:
    self_test()
    payload = lock_payload()
    write_json_atomic(path, payload)
    verify_lock(path)
    return payload


def run(lock_path: Path, result_path: Path) -> dict:
    lock = verify_lock(lock_path)
    target = tuple(lock["target_signature"])
    manifest_by_name = {row["name"]: row for row in lock["source_manifest"]}
    matches = []
    diagnostics = []
    for document in source_documents():
        expected = manifest_by_name[document["name"]]
        for lane in LANES:
            text = normalize(document["text"], lane)
            signatures = Counter()
            for start, current in iter_window_signatures(text):
                signatures[current] += 1
                if current == target:
                    passage = text[start:start + WINDOW]
                    matches.append({
                        "source": document["name"],
                        "tier": document["tier"],
                        "lane": lane,
                        "normalized_start": start,
                        "passage_sha256": hashlib.sha256(passage.encode("ascii")).hexdigest(),
                        "passage": passage,
                    })
            diagnostics.append({
                "source": document["name"],
                "tier": document["tier"],
                "lane": lane,
                "normalized_length": len(text),
                "window_count": expected["lanes"][lane]["window_count"],
                "distinct_signature_count": len(signatures),
                "repeated_signature_count": sum(count > 1 for count in signatures.values()),
                "maximum_signature_multiplicity": max(signatures.values(), default=0),
                "exact_match_count": signatures[target],
            })
    unique_passages = {row["passage_sha256"] for row in matches}
    result = {
        "phase": PHASE,
        "lock_sha256": sha256_file(lock_path),
        "source_count": len(lock["source_manifest"]),
        "lane_count": len(LANES),
        "total_windows": sum(row["window_count"] for row in diagnostics),
        "matches": matches,
        "match_location_count": len(matches),
        "unique_passage_count": len(unique_passages),
        "diagnostics": diagnostics,
        "decision": "trigger_phase482b" if matches else "bounded_negative_no_exact_passage",
    }
    write_json_atomic(result_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--issue-lock", action="store_true")
    action.add_argument("--run", action="store_true")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 482A self-test passed")
    elif args.issue_lock:
        print(json.dumps(issue_lock(args.lock), indent=2, sort_keys=True))
    else:
        print(json.dumps(run(args.lock, args.result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
