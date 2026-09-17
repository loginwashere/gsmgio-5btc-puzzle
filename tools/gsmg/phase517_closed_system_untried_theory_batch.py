#!/usr/bin/env python3
"""Phase 517 -- batch execution of the Tier 1/Tier 2 closed-system theories
scoped in `doc/Brainstorms/2026-09-17 - Closed-System Untried Theory
Classes.md`. Nine items, all deterministic/cheap (no stochastic search, no
execution-lock ceremony needed -- every candidate universe is small, fixed,
and enumerated in full).

Items covered (doc section numbers): 1a, 1b, 1c, 6, 4-primary, 10b (Tier 1);
8, 9, 7 (Tier 2).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

from data import (  # noqa: E402
    COSMIC_BLOB_B64,
    DBBI,
    FAED,
    P32_TRAILING_BLOB_B64,
    SALPHASEION_BLOB_B64,
    VALIDATION_ANSWER,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
)
from phase484a_raw_symbol_vic_solver import segment_raw, slot_codes  # noqa: E402
from binary_key_material_backfill import (  # noqa: E402
    SECP256K1_ORDER,
    private_key_details,
    hash160,
    base58check,
)
from first_hint_hash_audit import PRIZE_ADDRESS, HALVING_ADDRESS  # noqa: E402
from nibble_packing_audit import SIGNATURES, analyze_body, evaluate_materials  # noqa: E402
from cb_common import aes_try_open_bytes, _load_blob, BLOBS  # noqa: E402
import raw_asset_byte_password_audit as raa  # noqa: E402
import p1a_sentinel_backfill as p1a  # noqa: E402

KNOWN_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}
SRT_PATH = REPO_ROOT / "wordlists" / "matrix" / "the-matrix-reloaded-2003.en.srt"


def _divisor_pairs(n):
    return [(d, n // d) for d in range(2, n) if n % d == 0]


def _grid(s, cols):
    return [s[i:i + cols] for i in range(0, len(s), cols)]


def _sums_all(s, rows, cols, base):
    g = _grid(s, cols)
    val = lambda ch: ord(ch) - 97 + base
    return {
        "row": [sum(val(ch) for ch in r) for r in g],
        "col": [sum(val(g[i][j]) for i in range(rows)) for j in range(cols)],
        "anti": [sum(val(g[i][j]) for i in range(rows) for j in range(cols) if i + j == k)
                 for k in range(rows + cols - 1)],
        "main": [sum(val(g[i][j]) for i in range(rows) for j in range(cols) if j - i == k)
                 for k in range(-(rows - 1), cols)],
    }


def _valid_pairs(raw):
    out = {}
    for p in itertools.combinations("abcdefghi", 2):
        t = segment_raw(raw, p)
        if t is not None:
            out["".join(p)] = t
    return out


def _homomorphism_violations(keys, values):
    """Count positions where a repeated `keys` entry maps to a different
    `values` entry than its first occurrence did. Keys by the FIRST
    argument -- for a many-to-one "is B a coarse image of A" test (item
    10b's "is DBBI a 9-class image of VALIDATION_ANSWER"), pass the
    finer-grained sequence (more distinct values, e.g. 25-letter text)
    first and the coarser one (fewer distinct values, e.g. DBBI's 9
    symbols) second."""
    m, v = {}, 0
    for c, x in zip(keys, values):
        if c in m and m[c] != x:
            v += 1
        else:
            m[c] = x
    return v


def _bijection_violations(codes, letters):
    c2l, l2c, v = {}, {}, 0
    for c, l in zip(codes, letters):
        if c in c2l and c2l[c] != l:
            v += 1
        else:
            c2l[c] = l
        if l in l2c and l2c[l] != c:
            v += 1
        else:
            l2c[l] = c
    return v


def _architect_letters_before_choice():
    """The film Architect scene, already frozen by this project (see
    GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT.md). Returns (all_letters_full,
    letters_before_the_one_post-anchor_'choice')."""
    srt = SRT_PATH.read_text(encoding="utf-8", errors="replace")
    lines = [l.strip() for l in srt.splitlines()]
    text = re.sub(r"<[^>]+>", "", " ".join(l for l in lines if l and not l.isdigit() and "-->" not in l))
    low = text.lower()
    anchor = low.find("which brings us at last")
    choice_pos = next(m.start() for m in re.finditer(r"\bchoice\b", low) if m.start() > anchor)
    before_choice = re.sub(r"[^A-Za-z]", "", text[:choice_pos]).upper().replace("J", "I")
    full = re.sub(r"[^A-Za-z]", "", text).upper().replace("J", "I")
    return full, before_choice


def _loshu_maps():
    base = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]

    def rot90(g):
        return [list(row) for row in zip(*g[::-1])]

    def flip(g):
        return [row[::-1] for row in g]

    grids = {}
    g = base
    for r in range(4):
        grids[f"rot{r*90}"] = g
        grids[f"rot{r*90}_flip"] = flip(g)
        g = rot90(g)
    assert len(grids) == 8
    return {
        name: {s: v for s, v in zip("abcdefghi", [grid[i][j] for i in range(3) for j in range(3)])}
        for name, grid in grids.items()
    }


def _giant_decimal_body(source, table_map):
    table = str.maketrans({symbol: str(value) for symbol, value in table_map.items()})
    digits = source.translate(table)
    value = int(digits, 10)
    hexadecimal = f"{value:x}"
    if len(hexadecimal) % 2:
        return None
    return bytes.fromhex(hexadecimal)


# --- Item 1a --------------------------------------------------------------

def test_1a():
    faed_layouts = _divisor_pairs(len(FAED))
    digit_strings = {}
    for (r, c) in faed_layouts:
        for base, conv in ((0, "a0i8"), (1, "a1i9")):
            s = _sums_all(FAED, r, c, base)
            for kind, vals in s.items():
                digit_strings[f"FAED_{r}x{c}_{kind}_{conv}"] = "".join(str(v) for v in vals)
    assert len(digit_strings) == len(faed_layouts) * 2 * 4 == 112

    dbbi_pairs = _valid_pairs(DBBI)
    by_len = {}
    for pair, tokens in dbbi_pairs.items():
        by_len.setdefault(len(tokens), []).append((pair, tokens))

    matches = [(k, v) for k, v in digit_strings.items() if len(v) in by_len]
    cells = []
    for name, dstr in matches:
        for pair, tokens in by_len[len(dstr)]:
            v = _homomorphism_violations(tokens, dstr)
            cells.append({"faed_cell": name, "dbbi_pair": pair, "length": len(dstr), "violations": v})
    return {
        "total_faed_sumlist_cells": len(digit_strings),
        "length_matched_faed_cells": len(matches),
        "tested_cells": cells,
        "any_consistent": any(c["violations"] == 0 for c in cells),
    }


# --- Items 1b/1c ------------------------------------------------------------

def test_1b_1c():
    _, before_choice = _architect_letters_before_choice()
    out = {"letters_available": len(before_choice), "dbbi": [], "faed": []}
    for pair, tokens in _valid_pairs(DBBI).items():
        n = len(tokens)
        v = _bijection_violations(tokens, before_choice[-n:]) if n <= len(before_choice) else None
        out["dbbi"].append({"pair": pair, "n": n, "violations": v})
    for pair, tokens in _valid_pairs(FAED).items():
        n = len(tokens)
        v = _bijection_violations(tokens, before_choice[-n:]) if n <= len(before_choice) else None
        out["faed"].append({"pair": pair, "n": n, "violations": v})
    out["any_consistent"] = any(
        (r["violations"] == 0) for r in out["dbbi"] + out["faed"] if r["violations"] is not None
    )
    return out


# --- Item 6 -----------------------------------------------------------------

def test_6():
    stripped = DBBI.replace("a", "")
    assert len(stripped) == 88
    digits = [ord(c) - ord("b") for c in stripped]
    assert all(0 <= d <= 7 for d in digits)

    def pack_bits(digits, msb_first):
        bits = []
        for d in digits:
            order = (2, 1, 0) if msb_first else (0, 1, 2)
            bits.extend((d >> k) & 1 for k in order)
        assert len(bits) == 264
        val = 0
        for b in bits:
            val = (val << 1) | b
        return val.to_bytes(33, "big")

    field_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    results = []
    for order_name, msb in (("MSB-first", True), ("LSB-first", False)):
        raw33 = pack_bits(digits, msb)

        b0 = raw33[0]
        on_curve = False
        if b0 in (2, 3):
            x = int.from_bytes(raw33[1:], "big")
            rhs = (pow(x, 3, field_p) + 7) % field_p
            on_curve = pow(rhs, (field_p - 1) // 2, field_p) == 1
        results.append({"order": order_name, "reading": "compressed_pubkey_direct",
                        "leading_byte": b0, "structurally_valid": b0 in (2, 3), "on_curve": on_curve})

        for reading, pk in (
            ("privkey_first32_flag_end", raw33[:32]),
            ("privkey_last32_flag_start", raw33[1:]),
        ):
            det = private_key_details(pk)
            hit = bool(det) and any(v["address"] in KNOWN_ADDRESSES for v in det.values())
            results.append({"order": order_name, "reading": reading, "valid_key": bool(det), "hit": hit})

        scalar = int.from_bytes(raw33, "big") % SECP256K1_ORDER or SECP256K1_ORDER
        det = private_key_details(scalar.to_bytes(32, "big"))
        hit = bool(det) and any(v["address"] in KNOWN_ADDRESSES for v in det.values())
        results.append({"order": order_name, "reading": "scalar_mod_n", "valid_key": bool(det), "hit": hit})

    return {"candidates": results, "any_hit": any(r.get("hit") for r in results)}


# --- Item 4-primary -----------------------------------------------------------

def test_4_primary():
    def to_int(s, base):
        val = 0
        for ch in s:
            val = val * 9 + (ord(ch) - ord("a") + base)
        return val

    variants = {}
    for base, conv in ((0, "a0i8"), (1, "a1i9")):
        for direction, s in (("forward", FAED), ("reversed", FAED[::-1])):
            variants[f"{conv}_{direction}"] = to_int(s, base)

    candidates = []
    for name, val in variants.items():
        mb = val.to_bytes((val.bit_length() + 7) // 8, "big")
        for order in ("big", "little"):
            for pad_name, length in (("minimal", len(mb)), ("padded226", 226)):
                if length < len(mb):
                    continue
                b = val.to_bytes(length, order)
                hits = [name for name, magic in SIGNATURES.items() if b.startswith(magic)]
                candidates.append({"variant": f"{name}_{order}_{pad_name}", "head_hex": b[:12].hex(), "header_hits": hits})
    return {"candidates": candidates, "any_header_hit": any(c["header_hits"] for c in candidates)}


# --- Item 10b -----------------------------------------------------------------

def test_10b():
    out = {}
    out["dbbi_vs_validation_answer"] = _homomorphism_violations(VALIDATION_ANSWER, DBBI)

    import base64
    raw = base64.b64decode(PHASE32_BLOB_B64)
    p = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-md", "sha256", "-pass", f"pass:{PHASE32_PASSWORD}"],
        input=raw, capture_output=True,
    )
    phase32_letters = re.sub(r"[^A-Za-z]", "", p.stdout.decode("utf-8", "replace")).upper().replace("J", "I")
    if len(phase32_letters) >= 91:
        best = min(range(len(phase32_letters) - 91 + 1),
                   key=lambda off: _homomorphism_violations(phase32_letters[off:off + 91], DBBI))
        out["dbbi_vs_phase32_plaintext_best"] = _homomorphism_violations(phase32_letters[best:best + 91], DBBI)
    else:
        out["dbbi_vs_phase32_plaintext_best"] = None

    architect_full, _ = _architect_letters_before_choice()
    n_windows = len(architect_full) - 570 + 1
    best = min(range(n_windows), key=lambda off: _homomorphism_violations(architect_full[off:off + 570], FAED))
    out["faed_vs_architect_full_best"] = _homomorphism_violations(architect_full[best:best + 570], FAED)
    out["faed_vs_architect_windows_tested"] = n_windows
    out["any_consistent"] = any(
        v == 0 for v in (out["dbbi_vs_validation_answer"], out["dbbi_vs_phase32_plaintext_best"],
                        out["faed_vs_architect_full_best"]) if v is not None
    )
    return out


# --- Item 8 -----------------------------------------------------------------

def test_8():
    targets = {name: BLOBS[name] for name in ("SALPH", "COSMIC", "URLBLOB")}
    report = raa.run(blobs=targets)
    return report


# --- Item 9 -----------------------------------------------------------------

def test_9():
    position_sets = {"1_4_21": (1, 4, 21), "2_7_73": (2, 7, 73)}

    def apply_b64(s, positions, mode):
        s = "".join(s.split())
        idx = sorted((p - 1) for p in positions if 0 <= p - 1 < len(s))
        if not idx:
            return None
        chars = list(s)
        if mode == "delete":
            for i in sorted(idx, reverse=True):
                del chars[i]
        elif mode == "set_A":
            for i in idx:
                chars[i] = "A"
        elif mode == "set_0":
            for i in idx:
                chars[i] = "0"
        return "".join(chars)

    def try_load_b64(b64_str):
        import base64
        try:
            raw = base64.b64decode(b64_str, validate=False)
        except Exception:
            return None
        if raw[:8] != b"Salted__" or len(raw) < 16:
            return None
        return raw[8:16], raw[16:]

    blobs_b64 = {"SALPH": SALPHASEION_BLOB_B64, "COSMIC": COSMIC_BLOB_B64, "P32TRAILING": P32_TRAILING_BLOB_B64}
    candidates = p1a.eligible_candidates()
    forms = list(dict.fromkeys(f for _, _, text in candidates for f in p1a.passphrase_forms(text)))

    b64_variants_tested = 0
    b64_valid = 0
    b64_attempts = 0
    b64_hits = []
    for blob_name, b64 in blobs_b64.items():
        for pset_name, positions in position_sets.items():
            for mode in ("delete", "set_A", "set_0"):
                b64_variants_tested += 1
                modified = apply_b64(b64, positions, mode)
                loaded = try_load_b64(modified) if modified else None
                if loaded is None:
                    continue
                b64_valid += 1
                salt, ct = loaded
                for form in forms:
                    b64_attempts += 1
                    if aes_try_open_bytes(form.encode(), blobs={"x": (salt, ct)}):
                        b64_hits.append((blob_name, pset_name, mode, form))

    blobs_raw = {
        "SALPH": _load_blob(SALPHASEION_BLOB_B64),
        "COSMIC": _load_blob(COSMIC_BLOB_B64),
        "P32TRAILING": _load_blob(P32_TRAILING_BLOB_B64),
    }

    def apply_bytes(ct, positions, mode):
        idx = sorted((p - 1) for p in positions if 0 <= p - 1 < len(ct))
        if not idx:
            return None
        b = bytearray(ct)
        if mode == "delete":
            for i in sorted(idx, reverse=True):
                del b[i]
        elif mode == "set_0x00":
            for i in idx:
                b[i] = 0x00
        elif mode == "set_0x41":
            for i in idx:
                b[i] = 0x41
        return bytes(b)

    byte_variants_tested = 0
    byte_block_aligned = 0
    byte_attempts = 0
    byte_hits = []
    for blob_name, (salt, ct) in blobs_raw.items():
        for pset_name, positions in position_sets.items():
            for mode in ("delete", "set_0x00", "set_0x41"):
                byte_variants_tested += 1
                modified_ct = apply_bytes(ct, positions, mode)
                if modified_ct is None or len(modified_ct) == 0 or len(modified_ct) % 16 != 0:
                    continue
                byte_block_aligned += 1
                for form in forms:
                    byte_attempts += 1
                    if aes_try_open_bytes(form.encode(), blobs={"x": (salt, modified_ct)}):
                        byte_hits.append((blob_name, pset_name, mode, form))

    return {
        "sentinel_candidate_count": len(candidates),
        "sentinel_form_count": len(forms),
        "base64_text_position_reading": {
            "variants_tested": b64_variants_tested,
            "variants_parsed_as_valid_blob": b64_valid,
            "decrypt_attempts": b64_attempts,
            "hits": b64_hits,
        },
        "ciphertext_byte_position_reading": {
            "variants_tested": byte_variants_tested,
            "variants_block_aligned": byte_block_aligned,
            "decrypt_attempts": byte_attempts,
            "hits": byte_hits,
        },
    }


# --- Item 7 -----------------------------------------------------------------

def test_7():
    maps = _loshu_maps()
    rows = []
    rejected = []
    for source_name, source in (("DBBI", DBBI), ("FAED", FAED)):
        for map_name, table_map in maps.items():
            body = _giant_decimal_body(source, table_map)
            label = f"{source_name}/{map_name}"
            if body is None:
                rejected.append(label)
                continue
            analysis = analyze_body(body)
            rows.append({"label": label, "body": body, "analysis": analysis})

    header_hits = []
    for row in rows:
        for sig_name, magic in SIGNATURES.items():
            if row["body"].startswith(magic):
                header_hits.append((row["label"], sig_name))

    registry = {}
    for row in rows:
        body = row["body"]
        digest = hashlib.sha256(body).digest()
        for material in (body, digest, digest.hex().encode("ascii")):
            registry.setdefault(material, []).append(row["label"])
    materials = [{"material": m, "sources": s} for m, s in registry.items()]
    oracle_hits = evaluate_materials(materials, run_oracles=True)

    return {
        "bodies_built": len(rows),
        "rejected_odd_hex_length": rejected,
        "printable_ratios": {r["label"]: r["analysis"]["printable_ratio"] for r in rows},
        "header_hits": header_hits,
        "unique_password_materials": len(materials),
        "oracle_hits": oracle_hits,
    }


# --- self-test + main --------------------------------------------------------

def self_test():
    assert len(DBBI) == 91 and len(FAED) == 570
    assert sum(v for row in _loshu_maps()["rot0"].values() for v in [row]) == 45
    for m in _loshu_maps().values():
        assert sorted(m.values()) == list(range(1, 10))
    assert len(p1a.eligible_candidates()) == 42
    full, before = _architect_letters_before_choice()
    assert len(before) > 30000 and len(full) > len(before)
    assert _homomorphism_violations("aab", "XXY") == 0
    assert _homomorphism_violations("aab", "XYY") == 1
    # Regression guard: caught a real argument-order bug during development
    # (keying by the coarse side instead of the fine side gave 79, not 59).
    assert _homomorphism_violations(VALIDATION_ANSWER, DBBI) == 59
    return {"ok": True}


def audit():
    return {
        "1a": test_1a(),
        "1b_1c": test_1b_1c(),
        "6": test_6(),
        "4_primary": test_4_primary(),
        "10b": test_10b(),
        "8": test_8(),
        "9": test_9(),
        "7": test_7(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
        print(json.dumps(result))
        return 0 if result["ok"] else 1
    if args.run:
        report = audit()
        if args.json:
            print(json.dumps(report, indent=2, default=lambda o: o.hex() if isinstance(o, bytes) else str(o)))
        else:
            for key, val in report.items():
                if isinstance(val, dict) and "any_hit" in val:
                    print(f"[{key}] any_hit={val['any_hit']}")
                elif isinstance(val, dict) and "any_consistent" in val:
                    print(f"[{key}] any_consistent={val['any_consistent']}")
                elif isinstance(val, dict) and "total_hits" in val:
                    print(f"[{key}] total_hits={val['total_hits']}")
                elif isinstance(val, dict) and "hits" in val and isinstance(val["hits"], list) and key in ("7",):
                    print(f"[{key}] oracle_hits={len(val['oracle_hits'])} header_hits={val['header_hits']}")
                elif key == "9":
                    print(f"[9] b64_hits={val['base64_text_position_reading']['hits']} "
                          f"byte_hits={val['ciphertext_byte_position_reading']['hits']}")
                else:
                    print(f"[{key}] done")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
