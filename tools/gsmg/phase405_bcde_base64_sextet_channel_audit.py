#!/usr/bin/env python3
"""Phase 405: tests the BCDE control rail as a Base64 sextet channel --
three raw control symbols packed into one 6-bit value read as a standard
Base64 character, over the two natural boundaries Phase 397/404 never
covered (the full-decode control rail and the P91-scoped control rail).

**Origin:** identified as a residual after Phase 404 closed the native
`Q472` data rail negative. `{B,C,D,E}` supplies exactly 2 bits per
symbol; three symbols supply 6 bits, matching one Base64 character
exactly. This is mathematically another representation of Phase 397's
2-bit control packing (same grid-native mappings, same bit content), but
it tests two boundaries Phase 397 explicitly excluded: the full
285-symbol control rail (`decoded[0::2]`) and the P91-scoped 45-symbol
control rail (`decoded[7:98][1::2]`). `Q472`'s own 236-symbol control
rail is excluded here -- not divisible by three, and already byte-packed
in Phase 397.

**Frozen contract (proposed and approved before this script was
written):**

- exactly two sources: `FULL_CONTROL = decoded[0::2]` (285 symbols, 95
  sextets) and `P91_CONTROL = decoded[7:98][1::2]` (45 symbols, 15
  sextets); both asserted to contain exactly `{B,C,D,E}`;
- exactly two symbol->2-bit mappings, the same grid-native pair Phase
  397/398 use: row-major (`D,B,C,E -> 0,1,2,3`) and column-major
  (`D,C,B,E -> 0,1,2,3`);
- `index = v0<<4 | v1<<2 | v2` per triple, read through the standard
  Base64 alphabet only; native forward direction only, no reversal;
  generated Base64 case preserved exactly (no case-folding);
- 2 sources x 2 mappings = **4 labeled candidates**, closed and
  enumerated before any output is inspected;
- append exactly the mathematically required single `=` (both sources'
  sextet counts are `4n+3`, so padding to the next multiple of 4 always
  costs exactly one `=`); decode via standard Base64 -- 71 bytes for the
  95-sextet source, 11 bytes for the 15-sextet source, with 2 discarded
  terminal bits in both cases (95*6=570 bits vs. 71*8=568; 15*6=90 bits
  vs. 11*8=88); report those discarded bits and whether each decoding is
  canonical Base64 (`b64encode(b64decode(s)) == s`);
- consumer/scanner calls deduplicated by unique decoded-byte value (not
  by label -- all four labels are still reported individually);
- evaluation: strict magic/container/key-format parsing only (DER, PSBT,
  Bitcoin transaction, `Salted__`, compressed-format magic bytes,
  WIF/extended-key/SEC1/decimal-scalar/hex64/BIP39-word-run matches, and
  an exact target-address hit) -- no English scoring, no keyword scan
  (the Base64 alphabet is constructed by definition, not evidence of
  language); no SHA-256-scalar or BIP32 consumer (71 bytes is outside
  BIP32's standard 16-64-byte seed range and is not a raw 32-byte
  scalar; 11 bytes is too short for either);
- planted round-trip and typed-parser positives required;
- Base64 syntax validity or zero discarded padding bits, on their own,
  are not promotion signals -- only an exact parser/key-format/target-
  address hit promotes.

**Method:** wrote this script, reusing Phase 397's `ROW_MAJOR`/
`COLUMN_MAJOR` mappings and Phase 402's `evaluate_raw_bytes()` (the same
strict-scanner wrapper around
`typed_decode_parse_ladder_audit.validate_structural`/`validate_full`/
`is_parser_valid`) verbatim -- no primitive re-derived. A planted
round-trip positive inverse-maps a known Base64 string (`base64.
b64encode(b"BTC")`) back through row-major to a synthetic control-symbol
sequence, then re-runs the real forward sextet-packing function and
confirms it reproduces the original Base64 string exactly. A planted
typed-parser positive (the same independent 32-byte `Salted__` fixture
Phase 402 uses, since the coordinate-derived byte range here can equally
never spell an ASCII magic header on its own) confirms the strict
scanner fires.

**Result:** see `self_test()`'s asserted counts and values for the exact
pinned 4-candidate manifest, discarded-bit counts, and scanner results.

**Disposition:** decided strictly by the contract above -- absent an
exact parser, key-format, or target-address hit, this closes the sextet
family negative without adding reversal, URL-safe variants, alternative
alphabets, or `Q472` remainder handling.
"""

import argparse
import base64
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402
from phase397_p91z_priority1_control_channel_audit import (  # noqa: E402
    COLUMN_MAJOR,
    ROW_MAJOR,
)
from phase402_p91z_priority6_control_data_digraph_machine_audit import (  # noqa: E402
    evaluate_raw_bytes,
)

STANDARD_B64_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/"
)
assert len(STANDARD_B64_ALPHABET) == 64

MAPPINGS = (("row_major", ROW_MAJOR), ("column_major", COLUMN_MAJOR))


def triples_to_base64(symbols, mapping):
    assert len(symbols) % 3 == 0
    out = []
    for i in range(0, len(symbols), 3):
        v0, v1, v2 = (mapping[s] for s in symbols[i : i + 3])
        index = (v0 << 4) | (v1 << 2) | v2
        out.append(STANDARD_B64_ALPHABET[index])
    return "".join(out)


def pad_and_decode(b64_string):
    pad_needed = (-len(b64_string)) % 4
    padded = b64_string + "=" * pad_needed
    decoded_bytes = base64.b64decode(padded, validate=True)
    return padded, decoded_bytes, pad_needed


def build_candidates(full_control, p91_control):
    sources = {"FULL": full_control, "P91": p91_control}
    candidates = {}
    for source_label, symbols in sources.items():
        assert len(symbols) % 3 == 0
        for mapping_label, mapping in MAPPINGS:
            label = f"{source_label}_{mapping_label}"
            b64 = triples_to_base64(symbols, mapping)
            padded, decoded_bytes, pad_needed = pad_and_decode(b64)
            discarded_bits = len(b64) * 6 - len(decoded_bytes) * 8
            canonical = base64.b64encode(decoded_bytes).decode("ascii") == padded
            candidates[label] = {
                "source": source_label,
                "mapping": mapping_label,
                "sextet_count": len(b64),
                "base64_unpadded": b64,
                "pad_added": pad_needed,
                "base64_padded": padded,
                "decoded_length": len(decoded_bytes),
                "decoded_bytes": decoded_bytes,
                "discarded_terminal_bits": discarded_bits,
                "canonical_base64": canonical,
            }
    return candidates


def evaluate_candidates(candidates):
    unique_bytes = {}
    for label, entry in candidates.items():
        unique_bytes.setdefault(entry["decoded_bytes"], []).append(label)
    unique_results = {data: evaluate_raw_bytes(data) for data in unique_bytes}
    results = {label: unique_results[entry["decoded_bytes"]] for label, entry in candidates.items()}
    return results, len(unique_bytes)


def planted_roundtrip_positive():
    """A known Base64 string (`b64encode(b"BTC")`, which needs no padding
    -- 3 bytes -> exactly 4 clean Base64 characters) inverse-mapped back
    through row-major into a synthetic control-symbol sequence, then
    re-run through the real forward `triples_to_base64()` -- proves the
    sextet-packing pipeline round-trips correctly, not just that it
    runs."""
    target_bytes = b"BTC"
    target_b64 = base64.b64encode(target_bytes).decode("ascii")
    assert "=" not in target_b64 and len(target_b64) == 4
    inverse_row_major = {v: k for k, v in ROW_MAJOR.items()}
    symbols = []
    for ch in target_b64:
        index = STANDARD_B64_ALPHABET.index(ch)
        v0 = (index >> 4) & 0b11
        v1 = (index >> 2) & 0b11
        v2 = index & 0b11
        symbols.extend(inverse_row_major[v] for v in (v0, v1, v2))
    recovered_b64 = triples_to_base64(symbols, ROW_MAJOR)
    return {
        "target_bytes": target_bytes.hex(),
        "target_b64": target_b64,
        "recovered_b64": recovered_b64,
        "matches": recovered_b64 == target_b64,
    }


def planted_typed_parser_positive():
    """A synthetic 32-byte string, independent of the sextet-derived
    byte ranges (71/11 bytes here), fed through the identical raw-byte
    evaluator the four real candidates use -- proves the strict
    Salted__ detector fires."""
    data = b"Salted__" + bytes(range(8)) + bytes(range(16))
    assert len(data) == 32
    return {"data_hex": data.hex(), "result": evaluate_raw_bytes(data)}


def audit():
    decoded = btcseed_audit()["decoded"]

    full_control = decoded[0::2]
    assert len(full_control) == 285
    assert set(full_control) == set("BCDE")

    p91 = decoded[7:98]
    assert len(p91) == 91
    p91_control = p91[1::2]
    assert len(p91_control) == 45
    assert set(p91_control) == set("BCDE")

    candidates = build_candidates(full_control, p91_control)
    assert len(candidates) == 4

    results, unique_candidate_count = evaluate_candidates(candidates)

    report_candidates = {
        label: {
            "source": entry["source"],
            "mapping": entry["mapping"],
            "sextet_count": entry["sextet_count"],
            "base64_unpadded": entry["base64_unpadded"],
            "pad_added": entry["pad_added"],
            "base64_padded": entry["base64_padded"],
            "decoded_length": entry["decoded_length"],
            "decoded_hex": entry["decoded_bytes"].hex(),
            "discarded_terminal_bits": entry["discarded_terminal_bits"],
            "canonical_base64": entry["canonical_base64"],
        }
        for label, entry in candidates.items()
    }

    return {
        "full_control_length": len(full_control),
        "p91_control_length": len(p91_control),
        "candidate_count": len(candidates),
        "unique_candidate_count": unique_candidate_count,
        "candidates": report_candidates,
        "results": results,
        "any_parser_valid": any(r["parser_valid"] for r in results.values()),
        "any_exact_target_hit": any(r["exact_target_hit"] is not None for r in results.values()),
        "planted_roundtrip_positive": planted_roundtrip_positive(),
        "planted_typed_parser_positive": planted_typed_parser_positive(),
    }


def self_test():
    report = audit()

    assert report["full_control_length"] == 285
    assert report["p91_control_length"] == 45
    assert report["candidate_count"] == 4
    assert set(report["candidates"].keys()) == {
        f"{s}_{m}" for s in ("FULL", "P91") for m, _ in MAPPINGS
    }

    for label, entry in report["candidates"].items():
        expected_sextets = 95 if entry["source"] == "FULL" else 15
        expected_decoded = 71 if entry["source"] == "FULL" else 11
        assert entry["sextet_count"] == expected_sextets, (label, entry["sextet_count"])
        assert entry["pad_added"] == 1, (label, entry["pad_added"])
        assert entry["base64_padded"].endswith("="), label
        assert entry["decoded_length"] == expected_decoded, (label, entry["decoded_length"])
        assert entry["discarded_terminal_bits"] == 2, (label, entry["discarded_terminal_bits"])

    for label, result in report["results"].items():
        assert not any(result["magic_triggers"].values()), (label, result["magic_triggers"])
        assert not any(result["structural"].values()), (label, result["structural"])
        assert result["key_format_matches"] == [], (label, result["key_format_matches"])
        assert result["exact_target_hit"] is None, (label, result["exact_target_hit"])
        assert result["parser_valid"] is False, (label, result["parser_valid"])

    assert report["any_parser_valid"] is False
    assert report["any_exact_target_hit"] is False

    roundtrip = report["planted_roundtrip_positive"]
    assert roundtrip["matches"] is True

    typed_positive = report["planted_typed_parser_positive"]
    assert typed_positive["result"]["magic_triggers"]["salted_header"] is True
    assert typed_positive["result"]["parser_valid"] is True

    print(
        f"[*] self-test OK: both planted positives fire (Base64 sextet "
        f"round-trip, Salted__ typed-parser fixture); 4 candidates (2 "
        f"sources x 2 grid-native mappings) reproduced at their pinned "
        f"95/15-sextet, 71/11-byte, 2-discarded-bit lengths; "
        f"{report['unique_candidate_count']}/{report['candidate_count']} "
        f"unique decoded-byte payloads; zero magic-byte triggers, "
        f"structural parses, key-format matches, or target-address hits "
        f"across all 4 candidates -- Phase 405 closes negative"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
