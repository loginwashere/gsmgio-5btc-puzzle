#!/usr/bin/env python3
"""Phase 397: executes Priority 1 of the 2026-08-25 BTCSEED/P91/Z
continuation brainstorm -- the post-`Z` control/data channel's byte-aligned
boundary.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`. `decoded[98:]` (`Q472`, 472 characters) splits into 236
digraphs. Its even-position "control" rail (236 symbols) is drawn from the
same `{B,C,D,E}` alphabet as the keyed square's upper-left `2x2`:

```text
D B
C E
```

Two grid-native readings assign that 2x2 a 2-bit value per symbol; 236
symbols x 2 bits = 472 bits = 59 bytes exactly -- the one boundary in this
branch that lines up byte-perfectly rather than merely factoring attractively
(see the brainstorm's own "Risks" section on that distinction).

**Frozen family (exactly as the brainstorm's Priority 1 section declares,
no additions):**

- `Q472 = decoded[98:]` exactly (not `decoded[97:]` or any other offset);
- `control = Q472[0::2]` (236 symbols) -- the only rail packed here; the
  paired "data" rail (`Q472[1::2]`) is out of scope for this phase (that is
  idea 25/26's separate ciphertext/key-material framing, not frozen for
  Priority 1);
- exactly two symbol->2-bit mappings: row-major (`D,B,C,E -> 0,1,2,3`) and
  column-major (`D,C,B,E -> 0,1,2,3`, the form matching Phase 394's posted
  BIP39 mapping) -- no other permutation of the remaining 22 is admitted;
- exactly two processing directions: forward (control read in its native
  left-to-right order) and reverse (`control[::-1]`, processed through the
  identical grouping/packing procedure) -- a reversed final byte string is
  not a separate axis, since it is byte-reversal of the forward-MSB output,
  already covered structurally;
- exactly two intra-byte packings: MSB-first (`byte = v0<<6 | v1<<4 |
  v2<<2 | v3`, earliest symbol in the highest bits) and LSB-first (`byte =
  v3<<6 | v2<<4 | v1<<2 | v0`, earliest symbol in the lowest bits);
- 2 x 2 x 2 = **8 candidate byte strings, closed and enumerated before any
  output is inspected**;
- strict typed recognizers only, reusing this project's own existing
  scanner modules verbatim (`typed_decode_parse_ladder_audit.validate_full`
  -- DER/PSBT/Bitcoin-tx/`Salted__`/key-format/exact-target-address -- plus
  the module's own hex/base64/gzip/zlib/zip magic-byte triggers). No English
  scoring, no dictionary word search, no manual "looks like X" judgment.

**Result:** all 8 candidates reproduce with correct lengths (59 bytes each).
None trigger any of the five raw structural checks (DER, PSBT, Bitcoin
transaction, `Salted__` header) or the five decode-then-validate checks
(hex, base64, gzip, zlib, zip); none contain a `classify_body_extended`
key-format match (WIF, extended key, SEC1 pubkey, decimal scalar, hex64,
BIP39 word run); none produce an exact target-address hit. `is_parser_valid`
is `False` for all 8.

**Disposition:** the byte-perfect `472=59*8` boundary does not, on its own
current frozen reading, produce a recognizable typed container or key
material. This closes Priority 1 as scoped -- negative. Per the brainstorm's
own promotion contract, this stops the family rather than widening it (e.g.
admitting the other 22 symbol mappings, splicing in the data rail, or
scoring outputs by printability/English-likeness); any such widening would
need its own fresh promotion, not a quiet extension of this one.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402
from typed_decode_parse_ladder_audit import (  # noqa: E402
    base64_trigger_variant,
    is_der_trigger,
    is_gzip_trigger,
    is_hex_trigger,
    is_salted_header_trigger,
    is_zip_trigger,
    is_zlib_trigger,
    validate_full,
    validate_structural,
    is_parser_valid,
)

# D B
# C E
ROW_MAJOR = {"D": 0, "B": 1, "C": 2, "E": 3}
COLUMN_MAJOR = {"D": 0, "C": 1, "B": 2, "E": 3}
MAPPINGS = (("row_major", ROW_MAJOR), ("column_major", COLUMN_MAJOR))
DIRECTIONS = ("forward", "reverse")
PACKINGS = ("msb_first", "lsb_first")


def pack_bits(symbols, mapping, packing):
    assert len(symbols) % 4 == 0
    values = [mapping[symbol] for symbol in symbols]
    out = bytearray()
    for i in range(0, len(values), 4):
        v0, v1, v2, v3 = values[i : i + 4]
        if packing == "msb_first":
            byte = (v0 << 6) | (v1 << 4) | (v2 << 2) | v3
        else:
            byte = (v3 << 6) | (v2 << 4) | (v1 << 2) | v0
        out.append(byte)
    return bytes(out)


def build_candidates(control):
    assert len(control) == 236
    candidates = {}
    for mapping_name, mapping in MAPPINGS:
        for direction in DIRECTIONS:
            symbols = control if direction == "forward" else control[::-1]
            for packing in PACKINGS:
                label = f"{mapping_name}_{direction}_{packing}"
                candidates[label] = pack_bits(symbols, mapping, packing)
    return candidates


def evaluate_candidate(data):
    triggers = {
        "hex": is_hex_trigger(data),
        "base64": base64_trigger_variant(data) is not None,
        "gzip": is_gzip_trigger(data),
        "zlib": is_zlib_trigger(data),
        "zip": is_zip_trigger(data),
        "der": is_der_trigger(data),
        "salted_header": is_salted_header_trigger(data),
    }
    structural = validate_structural(data)
    validation = validate_full(data)
    return {
        "length": len(data),
        "sha256": __import__("hashlib").sha256(data).hexdigest(),
        "magic_triggers": triggers,
        "structural": {
            "der_ec": structural["der_ec"] is not None,
            "psbt": structural["psbt"] is not None,
            "bitcoin_tx": structural["bitcoin_tx"] is not None,
            "salted_header": structural["salted_header"],
        },
        "key_format_matches": validation["key_format_matches"],
        "exact_target_hit": validation["exact_target_hit"],
        "parser_valid": is_parser_valid(validation),
    }


def audit():
    decoded = btcseed_audit()["decoded"]
    q472 = decoded[98:]
    assert len(q472) == 472
    control = q472[0::2]
    assert len(control) == 236
    assert set(control) == set("BCDE")

    candidates = build_candidates(control)
    results = {label: evaluate_candidate(data) for label, data in candidates.items()}

    return {
        "q472_length": len(q472),
        "control_length": len(control),
        "candidate_count": len(candidates),
        "candidates": results,
        "any_parser_valid": any(r["parser_valid"] for r in results.values()),
        "any_exact_target_hit": any(r["exact_target_hit"] is not None for r in results.values()),
    }


def self_test():
    report = audit()

    assert report["q472_length"] == 472
    assert report["control_length"] == 236
    assert report["candidate_count"] == 8
    assert set(report["candidates"].keys()) == {
        f"{m}_{d}_{p}" for m in ("row_major", "column_major") for d in DIRECTIONS for p in PACKINGS
    }

    for label, result in report["candidates"].items():
        assert result["length"] == 59, (label, result["length"])
        assert not any(result["magic_triggers"].values()), (label, result["magic_triggers"])
        assert not any(result["structural"].values()), (label, result["structural"])
        assert result["key_format_matches"] == [], (label, result["key_format_matches"])
        assert result["exact_target_hit"] is None, (label, result["exact_target_hit"])
        assert result["parser_valid"] is False, (label, result["parser_valid"])

    assert report["any_parser_valid"] is False
    assert report["any_exact_target_hit"] is False

    print(
        f"[*] self-test OK: Priority 1's frozen 8-candidate family "
        f"(2 grid-native mappings x 2 directions x 2 bit-packings) all "
        f"reproduce as 59-byte strings from Q472's 236-symbol control rail; "
        f"zero magic-byte triggers (hex/base64/gzip/zlib/zip/DER/Salted__), "
        f"zero structural parses (DER/PSBT/Bitcoin-tx/Salted__), zero "
        f"key-format matches (WIF/extended-key/SEC1/decimal-scalar/hex64/"
        f"BIP39), zero exact target-address hits across all 8 candidates -- "
        f"Priority 1 closes negative as scoped"
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
