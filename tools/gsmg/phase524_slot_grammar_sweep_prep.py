#!/usr/bin/env python3
"""Phase 524 -- execution of the Phase 523 pre-registered slot-grammar sweep:
preparation and result-verification helpers.

`--prepare` freezes the exact GPU input; the sweep itself is run with
`tools/gpu_oracle` (see doc/GSMG_PHASE524_SLOT_GRAMMAR_SWEEP.md); `--verify`
summarizes the GPU output against the frozen input; `--classify-weak`
re-derives each weak-tier hit's body from its recorded (passphrase, KDF, blob)
row -- the GPU tool never stores weak bodies -- confirms the recomputed
z-score matches the GPU's, and runs `key_shape_classifier.classify_body` over
it. That step decrypts only the rows already recorded; it is a review of
existing hits, not a candidate search, and no search oracle function is
imported here.

Preparation steps (all deterministic, no parameter chosen after any result):

1. Load Phase 523's `not_all_covered_bases.txt` and check its SHA-256 against
   the digest Phase 523 recorded. The file is JSON-lines (one JSON string per
   line) -- it MUST be decoded, because the GPU tool reads plain lines and
   would otherwise test every candidate with literal quote characters.
2. Rebuild Phase 523's tested-material map and drop redundant bases: a base
   is kept only if its standard expansion contains at least one material that
   is neither already tested against SALPH nor already scheduled by an
   earlier kept base (many bases collapse to identical letters-only strings
   under `answer_forms()`). Assert the kept list schedules exactly the same
   set of untested materials as the full list would.
3. Write a plain one-base-per-line wordlist and record its digest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
WORK_DIR = REPO_ROOT / "_work" / "phase524"
P523_DIR = REPO_ROOT / "_work" / "phase523"
sys.path.insert(0, str(SCRIPT_DIR))

import phase523_slot_grammar_overlap_audit as p523  # noqa: E402

RECORDED_NOT_ALL_COVERED_SHA256 = "ff5e80e9ba199fd6046a655c8b45c2f3a6ac0b88aa62ab8422075fc0cd092a18"
RECORDED_NOT_ALL_COVERED_COUNT = 133_657


def load_phase523_bases():
    path = P523_DIR / "not_all_covered_bases.txt"
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != RECORDED_NOT_ALL_COVERED_SHA256:
        raise SystemExit(f"Phase 523 base list digest mismatch: {digest}")
    bases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    if len(bases) != RECORDED_NOT_ALL_COVERED_COUNT:
        raise SystemExit(f"Phase 523 base count mismatch: {len(bases)}")
    for base in bases:
        if base != base.strip() or not base or base.startswith("#") or "\n" in base:
            raise SystemExit(f"base is not safe for the plain-line GPU wordlist: {base!r}")
    return bases


def prepare(write=True):
    bases = load_phase523_bases()
    tested, source_summary = p523.build_tested(p523.COVERAGE_SOURCES)

    scheduled = set()
    kept = []
    forms_emitted = 0
    for base in bases:
        materials = p523.expand_std(base, True)
        fresh = [m for m in materials if p523._mkey(m) not in tested and p523._mkey(m) not in scheduled]
        if fresh:
            kept.append(base)
            forms_emitted += len(materials)
            scheduled.update(p523._mkey(m) for m in fresh)

    # Equivalence check: the full list schedules exactly the same untested set.
    full_untested = set()
    for base in bases:
        for m in p523.expand_std(base, True):
            k = p523._mkey(m)
            if k not in tested:
                full_untested.add(k)
    if full_untested != scheduled:
        raise SystemExit("dedupe changed the set of untested materials; refusing to write")

    text = "\n".join(kept) + "\n"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    report = {
        "phase": 524,
        "phase523_base_list_sha256": RECORDED_NOT_ALL_COVERED_SHA256,
        "phase523_bases": len(bases),
        "kept_bases": len(kept),
        "gpu_forms_emitted": forms_emitted,
        "unique_untested_materials": len(scheduled),
        "tested_material_keys": len(tested),
        "wordlist_sha256": digest,
        "sources": len(source_summary),
    }
    if write:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        (WORK_DIR / "bases.txt").write_text(text, encoding="utf-8")
        (WORK_DIR / "prepare_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def summarize_output(path):
    """Count GPU output records by kind; no plaintext is printed."""
    counts = {"weak": 0, "strong": 0, "structural": 0, "other": 0}
    notable = []
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                counts["other"] += 1
                continue
            kind = rec.get("hit_kind", "other")
            counts[kind if kind in counts else "other"] += 1
            if kind in ("strong", "structural"):
                notable.append({k: rec.get(k) for k in ("hit_kind", "blob_tag", "kdf", "candidate_source", "z_score")})
    return counts, notable


def verify(hits_path, keyshape_path, checkpoint_path, expected_forms):
    counts, notable = summarize_output(hits_path)
    keyshape_records = 0
    ks = Path(keyshape_path)
    if ks.exists():
        keyshape_records = sum(1 for line in ks.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
    done = 0
    cp = Path(checkpoint_path)
    if cp.exists():
        lines = [l for l in cp.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        done = max(0, len(lines) - 1)  # first line is the fingerprint header
    return {
        "hits": counts,
        "strong_or_structural": notable,
        "keyshape_records": keyshape_records,
        "checkpointed_lines": done,
        "expected_forms": expected_forms,
    }


_LABEL = re.compile(r"^(legacy-(md5|sha1|sha256)|pbkdf2-sha256-(\d+))/aes-(\d+)-(cbc|ecb|cfb|ofb|ctr)$")


def _derive_body(passphrase, kdf_label, blob_tag):
    """Recompute one recorded (passphrase, variant, blob) decrypt body with
    cb_common's own KDF helpers and `cryptography`'s AES modes."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    import cb_common as cb

    m = _LABEL.match(kdf_label)
    if not m:
        raise ValueError(f"unrecognized variant label: {kdf_label}")
    key_len = int(m.group(4)) // 8
    mode_name = m.group(5)
    salt, ciphertext = cb.BLOBS[blob_tag]
    passwd = passphrase.encode("utf-8") if isinstance(passphrase, str) else passphrase
    if m.group(3):
        key, iv = cb.pbkdf2_bytes_to_key(passwd, salt, int(m.group(3)), "sha256", key_len, 16)
    else:
        key, iv = cb.evp_bytes_to_key(passwd, salt, m.group(2), key_len, 16)
    mode = {"cbc": modes.CBC(iv), "ecb": modes.ECB(), "cfb": modes.CFB(iv),
            "ofb": modes.OFB(iv), "ctr": modes.CTR(iv)}[mode_name]
    body = Cipher(algorithms.AES(key), mode).decryptor().update(ciphertext)
    if mode_name in ("cbc", "ecb"):
        pad = body[-1]
        if not 1 <= pad <= 16 or body[-pad:] != bytes([pad]) * pad:
            return None
        body = body[:-pad]
    return body


def classify_weak(hits_path, tolerance=0.05):
    import cb_common as cb
    import key_shape_classifier as ksc

    if not ksc.self_test():
        pass  # self_test raises on failure; return value is informational
    rows = []
    with open(hits_path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rec = json.loads(line)
                if rec.get("hit_kind") == "weak":
                    rows.append(rec)
    reconstructed = mismatches = unpadded_fail = 0
    key_shaped = []
    by_blob = {}
    for rec in rows:
        body = _derive_body(rec["candidate"], rec["kdf"], rec["blob_tag"])
        if body is None:
            unpadded_fail += 1
            continue
        reconstructed += 1
        if abs(cb.printable_z_score(body) - rec["z_score"]) > tolerance:
            mismatches += 1
        found = ksc.classify_body(body)
        by_blob[rec["blob_tag"]] = by_blob.get(rec["blob_tag"], 0) + 1
        if found:
            key_shaped.append({"blob": rec["blob_tag"], "kdf": rec["kdf"], "source": rec.get("candidate_source"),
                               "matches": [str(f)[:40] for f in found][:3]})
    return {"weak_rows": len(rows), "reconstructed": reconstructed, "padding_reconstruct_failures": unpadded_fail,
            "z_mismatches": mismatches, "key_shaped_matches": len(key_shaped), "key_shaped": key_shaped,
            "reconstructed_by_blob": by_blob}


def self_test():
    checks = {}
    checks["digest_constants"] = len(RECORDED_NOT_ALL_COVERED_SHA256) == 64
    checks["json_decoding_needed"] = json.loads('"a b"') == "a b" and '"a b"' != "a b"
    checks["p523_export_is_json"] = (P523_DIR / "not_all_covered_bases.txt").read_text(encoding="utf-8").startswith('"')
    return {"ok": all(checks.values()), "checks": checks}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--classify-weak", action="store_true")
    ap.add_argument("--hits", default=str(REPO_ROOT / "tools/gpu_oracle/output/phase524.hits.jsonl"))
    ap.add_argument("--keyshape", default=str(REPO_ROOT / "tools/gpu_oracle/output/phase524.keyshape.jsonl"))
    ap.add_argument("--checkpoint", default=str(REPO_ROOT / "tools/gpu_oracle/checkpoints/phase524.checkpoint"))
    args = ap.parse_args()
    if args.self_test:
        r = self_test()
        print(json.dumps(r, indent=2))
        return 0 if r["ok"] else 1
    if args.prepare:
        print(json.dumps(prepare(), indent=2))
        return 0
    if args.verify:
        report = json.loads((WORK_DIR / "prepare_report.json").read_text())
        print(json.dumps(verify(args.hits, args.keyshape, args.checkpoint, report["gpu_forms_emitted"]), indent=2))
        return 0
    if args.classify_weak:
        print(json.dumps(classify_weak(args.hits), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
