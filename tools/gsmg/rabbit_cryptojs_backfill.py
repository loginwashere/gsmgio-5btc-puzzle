#!/usr/bin/env python3
"""Rabbit / CryptoJS cipher-axis backfill over the existing candidate corpus.

Recorded as a hypothesis in doc/GSMG_TELEGRAM_UPDATE_REVIEW_2026_10_07.md (photo 75068). No candidate is
added: the corpus is the project's existing one, frozen by digest:
  extended_cipher_recheck.load_curated_candidates() (curated tier)
  + wordlists/gsmg/medium_curated_all.txt + wordlists/gsmg/last_command.txt
  + the four verified prior command hashes.
Forms: answer_forms(candidate) x keystr_forms(form, newline_variants=True), deduplicated (the project's
standard sweep forms).
Cipher axis: CryptoJS Rabbit and RabbitLegacy, x EVP_BytesToKey MD5 (CryptoJS default) and SHA-256.
Targets: SALPH, COSMIC, P32TRAILING, URLBLOB (first 80 plaintext bytes each).

A stream cipher has no padding. Hit rule (frozen): at least 64 of the first 80 bytes printable
(ASCII 32-126, TAB, LF, CR). Under a wrong key the count is Binomial(80, 98/256): mean 30.6, sd 4.3,
so 64 is z ~ 7.7. Rows with at least 56 are logged as weak, not hits.
Positive control: four CryptoJS 4.1.1 envelopes (Rabbit / RabbitLegacy, passphrases `causality` and
its SHA-256 hex) run as extra targets through the same pipeline. All four must be recovered.
"""
from __future__ import annotations

import base64
import hashlib
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rabbit_cryptojs as rc  # noqa: E402
from cb_common import answer_forms, keystr_forms  # noqa: E402
from data import COSMIC_BLOB_B64, P32_TRAILING_BLOB_B64, SALPHASEION_BLOB_B64, URLBLOB_B64  # noqa: E402
from data import VERIFIED_PRIOR_COMMAND_HASHES  # noqa: E402
from extended_cipher_recheck import load_curated_candidates  # noqa: E402
from test_rabbit_cryptojs import ENVELOPE_VECTORS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULT = Path(__file__).resolve().parent / "rabbit_cryptojs_backfill_result.json"
NBYTES, HIT, WEAK = 80, 64, 56
WORKERS = min(16, mp.cpu_count())
CHUNK = 4000
PRINTABLE = np.zeros(256, dtype=bool)
PRINTABLE[32:127] = True
PRINTABLE[[9, 10, 13]] = True


def corpus():
    seen, out = set(), []
    for c in (list(load_curated_candidates())
              + (ROOT / "wordlists/gsmg/medium_curated_all.txt").read_text(encoding="utf-8", errors="replace").splitlines()
              + (ROOT / "wordlists/gsmg/last_command.txt").read_text(encoding="utf-8").splitlines()
              + list(VERIFIED_PRIOR_COMMAND_HASHES.values())):
        c = c.strip()
        if c and not c.startswith("#") and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def materials(cands):
    seen = set()
    for c in cands:
        for form in answer_forms(c):
            for k in keystr_forms(form, newline_variants=True):
                b = k.encode("utf-8")
                if b and b not in seen:
                    seen.add(b)
                    yield b


def targets():
    t = {}
    for name, b64 in (("SALPH", SALPHASEION_BLOB_B64), ("COSMIC", COSMIC_BLOB_B64),
                      ("P32TRAILING", P32_TRAILING_BLOB_B64), ("URLBLOB", URLBLOB_B64)):
        raw = base64.b64decode(b64)
        t[name] = (raw[8:16], np.frombuffer(raw[16:16 + NBYTES], np.uint8))
    for i, e in enumerate(ENVELOPE_VECTORS):
        raw = base64.b64decode(e["b64"])
        t[f"PLANTED{i}_{e['alg']}"] = (raw[8:16], np.frombuffer(raw[16:16 + NBYTES], np.uint8))
    return t


TARGETS = targets()


def _work(chunk):
    rows = []
    stats = 0
    for name, (salt, ct) in TARGETS.items():
        n = min(NBYTES, len(ct))
        for digest in ("md5", "sha256"):
            kv = [rc.evp_key_iv(m, salt, digest) for m in chunk]
            keys = np.frombuffer(b"".join(k for k, _ in kv), np.uint8).reshape(-1, 16)
            ivs = np.frombuffer(b"".join(v for _, v in kv), np.uint8).reshape(-1, 8)
            for legacy in (False, True):
                ks = rc.keystream(keys, ivs, n, legacy=legacy)
                score = PRINTABLE[ks ^ ct[:n]].sum(axis=1)
                stats += len(chunk)
                for j in np.flatnonzero(score >= WEAK):
                    pt = (ks[j] ^ ct[:n]).tobytes()
                    rows.append({"target": name, "kdf": digest, "alg": "RabbitLegacy" if legacy else "Rabbit",
                                 "material": chunk[j].decode("utf-8", "replace"), "printable": int(score[j]),
                                 "plaintext_prefix": pt[:48].decode("latin-1")})
    return stats, rows


def main():
    cands = corpus()
    digest = hashlib.sha256("\n".join(cands).encode()).hexdigest()
    mats = list(materials(cands))
    print(f"candidates {len(cands)} digest {digest[:16]} materials {len(mats)}", flush=True)
    chunks = [mats[i:i + CHUNK] for i in range(0, len(mats), CHUNK)]
    total, rows = 0, []
    with mp.get_context("fork").Pool(WORKERS) as pool:
        for k, (s, r) in enumerate(pool.imap_unordered(_work, chunks)):
            total += s
            rows += r
            if k % 50 == 0:
                print(f"  chunk {k + 1}/{len(chunks)}", flush=True)
    real = [r for r in rows if not r["target"].startswith("PLANTED")]
    planted = {r["target"] for r in rows if r["target"].startswith("PLANTED") and r["printable"] >= HIT}
    result = {"candidates": len(cands), "corpus_digest": digest, "materials": len(mats),
              "trials": total, "hit_threshold": HIT, "weak_threshold": WEAK,
              "planted_recovered": sorted(planted), "planted_expected": len(ENVELOPE_VECTORS),
              "real_hits": [r for r in real if r["printable"] >= HIT],
              "real_weak": [r for r in real if WEAK <= r["printable"] < HIT]}
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("real_weak",)}, indent=1))
    print("weak rows:", len(result["real_weak"]))


if __name__ == "__main__":
    main()
