#!/usr/bin/env python3
"""Seed 2 from doc/Brainstorms/2026-08-20 - Post-Phase-340 Future Search
Portfolio.md: "typed decode-and-parse ladder," scoped per the user's exact
2026-08-20 freeze (quoted in full so a later reader does not have to dig
through chat history to see what was actually authorized):

  - Reuse the same 42-candidate, 12,128-body retained corpus from Phases
    336-338. Add no candidates, KDFs, ciphers, or scoring changes.
  - Allow strict hex, Base64/Base64URL, gzip/zlib/ZIP, and DER decoding.
  - Validate outputs with complete parsers: EC/PKCS#8, PSBT, Bitcoin
    transaction, key formats, or exact target relations.
  - Use whole-body, line, and token scopes only -- no arbitrary substring
    tree.
  - Depth one only.
  - Treat a nested Salted__ object as a structural hit, but do not decrypt
    it until second-layer password semantics are separately defined.
  - Include planted end-to-end positives, malformed near-positives, random
    length-matched controls, decompression limits, and exact
    trigger/decode/parser counts.
  - Keep parser-valid unrelated objects as review findings, not puzzle
    solutions.

Percent-decoding was in the brainstorm's own draft registry but is
deliberately dropped here (the user's scope list does not include it, and
per the brainstorm's own connections section, a decoder without an actual
retained trigger is a menu item, not evidence).

Why this is not a rerun of Phase 338 (A3): Phase 338's key-format scanner
(hex64/WIF/BIP39/decimal-scalar/SEC1/xprv-xpub) already ran directly
against every retained body with no decode step, and came back negative --
rerunning that alone here would add nothing. This pilot's actual new
surface is (a) a body that is only key-shaped, DER-shaped, or a valid
Bitcoin/PSBT object *after* one hex/Base64/gzip/zlib/ZIP decode, invisible
to every prior detector in this project's lineage, and (b) DER/PSBT/
Bitcoin-transaction structural recognition applied directly to raw
retained bodies too, since Phase 338 explicitly scoped DER out and no
prior phase ever built a PSBT or transaction parser at all. To avoid
duplicating Phase 338's own already-negative direct-body key-format scan,
`classify_body_extended` (the key-format validator) only runs on
POST-DECODE bytes here, never directly on a raw retained body; DER/PSBT/
Bitcoin-tx/Salted__ run on both raw bodies and post-decode bytes, since
none of those were ever checked directly before this phase.

Registry (each row: trigger -> one permitted decode -> required output
validation; DER's "decode" and "validation" are the same DER-parse call;
Salted__ has no decode step at all, per the scope freeze above):

  | trigger                                    | decode          | validation |
  |---------------------------------------------|-----------------|------------|
  | whole segment is even-length ASCII hex       | hex -> bytes    | full validator set |
  | strict Base64/Base64URL, canonical re-encode | base64 -> bytes | full validator set |
  | gzip magic + CM=deflate                      | inflate (capped)| full validator set |
  | zlib CMF/FLG header, checksum valid          | inflate (capped)| full validator set |
  | ZIP local header + central directory         | extract 1 member (capped) | full validator set |
  | DER outer SEQUENCE, exact consumed length     | (is the parse)  | secp256k1 OID / 32-byte scalar |
  | exact `Salted__` header, block-aligned body   | none            | structural hit only |

"Full validator set" = DER-EC/PKCS8, PSBT, Bitcoin transaction, Salted__,
plus (post-decode only) the key-format scanner and an exact-target check
on any 32-byte candidate scalar it finds. A "parser-valid" result is a
review finding, never counted as a puzzle solution by itself; only an
exact match against the prize address or a Phase-331 known target counts
as a hit (see module docstring's "Keep parser-valid unrelated objects as
review findings, not puzzle solutions").
"""

import argparse
import base64
import hashlib
import json
import sys
import zipfile
import zlib
from io import BytesIO
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from half_better_half_algebra_audit import (  # noqa: E402
    BLOBS,
    EXPECTED_CANDIDATE_DIGEST,
    KNOWN_TARGET_HASH160S,
    PRIZE_HASH160_HEX,
    candidate_list_digest,
    check_scalar,
    frozen_candidates,
    frozen_candidates_with_provenance,
    passphrase_forms,
    raw_cbc_bodies,
    raw_ecb_bodies,
    raw_stream_bodies,
)
from embedded_key_format_scanner_audit import classify_body_extended  # noqa: E402


# ---------------------------------------------------------------------------
# Corpus reuse -- identical to Phase 336/337/338, not re-selected here.
# ---------------------------------------------------------------------------

def iter_retained_bodies(blobs=None, candidates=None):
    """Yields (candidate_index, model, label, candidate_sha256, form_kind,
    variant_label, blob_tag, body) for every retained body in the exact
    same 42-candidate x 2-form x 54-variant x 4-blob corpus Phase 336/337/
    338 used -- same functions, same call shape, no new candidates/KDFs/
    ciphers."""
    active_blobs = BLOBS if blobs is None else blobs
    cand_records = (frozen_candidates_with_provenance() if candidates is None
                     else [(i, "external", f"candidate_{i}", text) for i, text in enumerate(candidates)])
    for index, model, label, text in cand_records:
        candidate_sha256 = hashlib.sha256(text.encode()).hexdigest()
        for form_kind, form_text in zip(("literal", "sha256"), passphrase_forms(text)):
            passwd = form_text.encode()
            bodies = (raw_cbc_bodies(passwd, active_blobs)
                      + raw_ecb_bodies(passwd, active_blobs)
                      + raw_stream_bodies(passwd, active_blobs))
            for variant_label, tag, body in bodies:
                yield index, model, label, candidate_sha256, form_kind, variant_label, tag, body


# ---------------------------------------------------------------------------
# Three explicit scopes -- no arbitrary substring scan.
# ---------------------------------------------------------------------------

def extract_scopes(body: bytes):
    lines = [ln for ln in body.split(b"\n") if ln]
    tokens = [tok for tok in body.split() if tok]
    segments = {}  # segment bytes -> set of scope names it appeared under
    for scope_name, parts in (("whole_body", [body]), ("line", lines), ("token", tokens)):
        for part in parts:
            segments.setdefault(part, set()).add(scope_name)
    return segments


# ---------------------------------------------------------------------------
# Decoders (trigger predicate + bounded decode)
# ---------------------------------------------------------------------------

MAX_DECOMPRESSED_SIZE = 1_000_000  # generous relative to 64-1,328-byte bodies; caps a bomb
MAX_COMPRESSION_RATIO = 500
MAX_ZIP_MEMBER_SIZE = 1_000_000

_HEX_ALPHABET = frozenset(b"0123456789abcdefABCDEF")
_B64_STD_ALPHABET = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
_B64_URL_ALPHABET = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")


def is_hex_trigger(seg: bytes) -> bool:
    return len(seg) >= 2 and len(seg) % 2 == 0 and all(c in _HEX_ALPHABET for c in seg)


def decode_hex(seg: bytes):
    try:
        return bytes.fromhex(seg.decode("ascii"))
    except ValueError:
        return None


def base64_trigger_variant(seg: bytes):
    """Returns 'standard', 'urlsafe', or None. Requires 4-byte-aligned
    length and canonical padding depth -- the cheap structural half of the
    "canonical re-encoding agrees" check; decode_base64 does the rest."""
    if len(seg) < 4 or len(seg) % 4 != 0:
        return None
    pad = len(seg) - len(seg.rstrip(b"="))
    if pad > 2:
        return None
    has_std_only = b"+" in seg or b"/" in seg
    has_url_only = b"-" in seg or b"_" in seg
    if has_std_only and has_url_only:
        return None
    if has_url_only:
        return "urlsafe" if all(c in _B64_URL_ALPHABET for c in seg) else None
    return "standard" if all(c in _B64_STD_ALPHABET for c in seg) else None


def decode_base64(seg: bytes, variant: str):
    try:
        if variant == "standard":
            raw = base64.b64decode(seg, validate=True)
            reenc = base64.b64encode(raw)
        else:
            raw = base64.urlsafe_b64decode(seg)
            reenc = base64.urlsafe_b64encode(raw)
    except Exception:
        return None
    if reenc != seg:
        return None  # non-canonical encoding: reject rather than guess intent
    return raw


def is_gzip_trigger(seg: bytes) -> bool:
    return len(seg) >= 18 and seg[:2] == b"\x1f\x8b" and seg[2] == 0x08


def is_zlib_trigger(seg: bytes) -> bool:
    if len(seg) < 6:
        return False
    b0, b1 = seg[0], seg[1]
    return (b0 & 0x0F) == 8 and ((b0 << 8) + b1) % 31 == 0


def _bounded_inflate(seg: bytes, wbits: int):
    """Decompress with a hard output-size cap so a planted or accidental
    decompression bomb cannot be materialized -- the checksum/trailer
    validation (Adler32 for zlib, CRC32+size for gzip) is enforced by
    zlib's own decompressobj once `eof` is reached, not bolted on after."""
    d = zlib.decompressobj(wbits)
    out = b""
    remaining = seg
    try:
        while True:
            budget = MAX_DECOMPRESSED_SIZE + 1 - len(out)
            if budget <= 0:
                return None
            chunk = d.decompress(remaining, budget)
            out += chunk
            remaining = d.unconsumed_tail
            if len(out) > MAX_DECOMPRESSED_SIZE:
                return None
            if d.eof:
                break
            if not remaining and not chunk:
                return None  # stalled: incomplete/malformed stream
        out += d.flush()
    except zlib.error:
        return None
    if len(out) > MAX_DECOMPRESSED_SIZE:
        return None
    if len(seg) and len(out) / len(seg) > MAX_COMPRESSION_RATIO:
        return None
    return out


def decode_gzip(seg: bytes):
    return _bounded_inflate(seg, 16 + zlib.MAX_WBITS)


def decode_zlib(seg: bytes):
    return _bounded_inflate(seg, zlib.MAX_WBITS)


def is_zip_trigger(seg: bytes) -> bool:
    return seg[:4] == b"PK\x03\x04"


def decode_zip(seg: bytes):
    try:
        zf = zipfile.ZipFile(BytesIO(seg))
        if zf.testzip() is not None:
            return None
        names = zf.namelist()
        if not names:
            return None
        info = zf.getinfo(names[0])
        if info.file_size > MAX_ZIP_MEMBER_SIZE:
            return None
        return zf.read(names[0])
    except Exception:
        return None


DECODERS = {
    "hex": (is_hex_trigger, lambda seg: decode_hex(seg)),
    "base64": (lambda seg: base64_trigger_variant(seg) is not None,
               lambda seg: decode_base64(seg, base64_trigger_variant(seg))),
    "gzip": (is_gzip_trigger, decode_gzip),
    "zlib": (is_zlib_trigger, decode_zlib),
    "zip": (is_zip_trigger, decode_zip),
}


# ---------------------------------------------------------------------------
# DER / PKCS8 / EC structural validator
# ---------------------------------------------------------------------------

SECP256K1_OID_DER = bytes.fromhex("06052B8104000A")  # OID 1.3.132.0.10, DER-encoded


def _der_parse_length(data, pos):
    if pos >= len(data):
        return None
    first = data[pos]
    if first < 0x80:
        return first, pos + 1
    n = first & 0x7F
    if n == 0 or pos + 1 + n > len(data):
        return None  # indefinite-length (BER, not DER) or truncated
    return int.from_bytes(data[pos + 1:pos + 1 + n], "big"), pos + 1 + n


def _der_parse_tlv(data, pos):
    if pos >= len(data):
        return None
    tag = data[pos]
    length_result = _der_parse_length(data, pos + 1)
    if length_result is None:
        return None
    length, value_start = length_result
    value_end = value_start + length
    if value_end > len(data):
        return None
    return tag, length, value_start, value_end


def _der_children(data, start, end, max_children=64):
    children = []
    pos = start
    while pos < end and len(children) < max_children:
        parsed = _der_parse_tlv(data, pos)
        if parsed is None:
            return None
        tag, _length, vstart, vend = parsed
        if vend > end:
            return None
        children.append((tag, data[vstart:vend]))
        pos = vend
    return children if pos == end else None


def is_der_trigger(seg: bytes) -> bool:
    outer = _der_parse_tlv(seg, 0)
    return outer is not None and outer[0] == 0x30 and outer[3] == len(seg)


def parse_der_ec_key(data: bytes, _depth=0):
    """Bounded structural parser: confirms `data` is exactly one consumed
    outer DER SEQUENCE, then looks (one extra bounded hop for PKCS8's
    OCTET-STRING-wraps-another-SEQUENCE shape) for the secp256k1 OID and a
    32-byte OCTET STRING scalar -- matches RFC5915 and PKCS8 EC private-key
    shapes closely enough to be decisive, not a full ASN.1 grammar."""
    outer = _der_parse_tlv(data, 0)
    if outer is None:
        return None
    tag, _length, vstart, vend = outer
    if tag != 0x30 or vend != len(data):
        return None

    found_oid = SECP256K1_OID_DER in data
    candidate_scalar = None
    children = _der_children(data, vstart, vend)
    if children is not None:
        for child_tag, value in children:
            if child_tag == 0x04 and len(value) == 32:
                candidate_scalar = value
                break
        if candidate_scalar is None and _depth == 0:
            for child_tag, value in children:
                if child_tag == 0x04:
                    inner = parse_der_ec_key(value, _depth=1)
                    if inner is not None:
                        found_oid = found_oid or inner["secp256k1_oid_found"]
                        if inner["candidate_scalar"] is not None:
                            candidate_scalar = inner["candidate_scalar"]
                            break

    return {"secp256k1_oid_found": found_oid, "candidate_scalar": candidate_scalar, "outer_consumed_exact": True}


# ---------------------------------------------------------------------------
# PSBT structural validator
# ---------------------------------------------------------------------------

PSBT_MAGIC = bytes.fromhex("70736274ff")


def _read_compact_size(buf, p):
    if p >= len(buf):
        return None
    first = buf[p]
    if first < 0xFD:
        return first, p + 1
    sizes = {0xFD: 2, 0xFE: 4, 0xFF: 8}
    n = sizes[first]
    if p + 1 + n > len(buf):
        return None
    return int.from_bytes(buf[p + 1:p + 1 + n], "little"), p + 1 + n


def _read_kv_map(buf, p):
    count = 0
    while True:
        if p >= len(buf):
            return None
        if buf[p] == 0x00:
            return p + 1, count
        r = _read_compact_size(buf, p)
        if r is None:
            return None
        keylen, p = r
        if keylen == 0 or p + keylen > len(buf):
            return None
        p += keylen
        r = _read_compact_size(buf, p)
        if r is None:
            return None
        vallen, p = r
        if p + vallen > len(buf):
            return None
        p += vallen
        count += 1


def parse_psbt(data: bytes):
    if data[:5] != PSBT_MAGIC:
        return None
    p = 5
    maps = []
    while p < len(data):
        r = _read_kv_map(data, p)
        if r is None:
            return None
        p, count = r
        maps.append(count)
    if p != len(data) or not maps:
        return None
    return {"map_count": len(maps), "entries_per_map": maps}


# ---------------------------------------------------------------------------
# Bitcoin transaction structural validator (legacy + segwit)
# ---------------------------------------------------------------------------

def parse_bitcoin_transaction(data: bytes):
    pos = 0

    def take(n):
        nonlocal pos
        if pos + n > len(data):
            raise ValueError("truncated")
        chunk = data[pos:pos + n]
        pos += n
        return chunk

    def varint():
        first = take(1)[0]
        if first < 0xFD:
            return first
        if first == 0xFD:
            return int.from_bytes(take(2), "little")
        if first == 0xFE:
            return int.from_bytes(take(4), "little")
        return int.from_bytes(take(8), "little")

    try:
        version = int.from_bytes(take(4), "little")
        segwit = data[pos:pos + 2] == b"\x00\x01"
        if segwit:
            take(2)
        in_count = varint()
        if in_count == 0 and not segwit:
            return None  # ambiguous with the segwit marker; not a normal tx
        if in_count > 100_000:
            return None
        for _ in range(in_count):
            take(32)  # prevout hash
            take(4)   # prevout index
            take(varint())  # scriptSig
            take(4)   # sequence
        out_count = varint()
        if out_count > 100_000:
            return None
        for _ in range(out_count):
            take(8)  # value
            take(varint())  # scriptPubKey
        if segwit:
            for _ in range(in_count):
                witness_count = varint()
                for _ in range(witness_count):
                    take(varint())
        locktime = int.from_bytes(take(4), "little")
    except ValueError:
        return None
    if pos != len(data):
        return None  # must consume the entire segment exactly
    return {"version": version, "input_count": in_count, "output_count": out_count,
            "locktime": locktime, "segwit": segwit}


# ---------------------------------------------------------------------------
# Salted__ structural trigger -- detection only, per the explicit scope
# freeze: no decrypt attempt, no password-guessing for the nested object.
# ---------------------------------------------------------------------------

def is_salted_header_trigger(seg: bytes) -> bool:
    return (len(seg) > 16 and seg[:8] == b"Salted__"
            and (len(seg) - 16) % 16 == 0)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_structural(data: bytes) -> dict:
    """DER/PSBT/Bitcoin-tx/Salted__ only -- safe to run on RAW retained
    bodies too, since none of these were ever checked directly on a body
    by any prior phase in this project (Phase 338 explicitly left DER out;
    PSBT/tx parsers did not exist before this phase)."""
    result = {"der_ec": None, "psbt": None, "bitcoin_tx": None, "salted_header": False}
    if is_salted_header_trigger(data):
        result["salted_header"] = True
    der = parse_der_ec_key(data)
    if der is not None:
        result["der_ec"] = der
    psbt = parse_psbt(data)
    if psbt is not None:
        result["psbt"] = psbt
    tx = parse_bitcoin_transaction(data)
    if tx is not None:
        result["bitcoin_tx"] = tx
    return result


def validate_full(data: bytes, known_targets=None) -> dict:
    """Structural validators plus the key-format scanner and an exact-
    target check -- reserved for POST-DECODE bytes only, so this never
    duplicates Phase 338's already-negative direct-body key-format scan.
    `known_targets` is taken as an explicit parameter (not read off the
    module-level KNOWN_TARGET_HASH160S global) so a caller -- notably this
    module's own self-test -- can inject a planted target without relying
    on rebinding another module's attribute, which does not propagate
    through an already-executed `from x import y` binding."""
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets
    result = validate_structural(data)
    result["key_format_matches"] = []
    exact_target_hit = None

    if result["der_ec"] is not None and result["der_ec"]["candidate_scalar"] is not None:
        hit = check_scalar(result["der_ec"]["candidate_scalar"], None, targets)
        if hit is not None:
            exact_target_hit = {"source": "der_ec", **hit}

    key_matches, _curve_valid_diag = classify_body_extended(data, bloom=None, known_targets=targets)
    result["key_format_matches"] = [kind for kind, _payload in key_matches]
    if exact_target_hit is None:
        for kind, payload in key_matches:
            if (kind in ("sec1_compressed", "sec1_uncompressed")
                    and isinstance(payload, tuple) and payload[2] == "known_target"):
                exact_target_hit = {"source": kind, "target_label": payload[3]}
                break
            if isinstance(payload, (bytes, bytearray)) and len(payload) == 32:
                hit = check_scalar(payload, None, targets)
                if hit is not None:
                    exact_target_hit = {"source": kind, **hit}
                    break

    if exact_target_hit is None and len(data) == 32:
        hit = check_scalar(data, None, targets)
        if hit is not None:
            exact_target_hit = {"source": "raw_32byte_scalar", **hit}

    result["exact_target_hit"] = exact_target_hit
    return result


def is_parser_valid(validation: dict) -> bool:
    return bool(validation.get("der_ec") or validation.get("psbt") or validation.get("bitcoin_tx")
                or validation.get("salted_header") or validation.get("key_format_matches"))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run(blobs=None, candidates=None, known_targets=None):
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets
    counters = {
        "bodies_checked": 0,
        "segments_evaluated": 0,
        "raw_der_trigger": 0, "raw_der_parser_valid": 0,
        "raw_psbt_trigger": 0, "raw_bitcoin_tx_trigger": 0,
        "salted_header_trigger": 0,
    }
    decoder_counters = {name: {"trigger": 0, "decode_ok": 0, "parser_valid": 0} for name in DECODERS}
    unique_decoded_outputs = {name: set() for name in DECODERS}

    structural_findings = []
    exact_target_hits = []

    attempts = 0
    for index, model, label, candidate_sha256, form_kind, variant_label, tag, body in iter_retained_bodies(blobs, candidates):
        counters["bodies_checked"] += 1
        segments = extract_scopes(body)
        provenance = {
            "candidate_index": index, "candidate_model": model, "candidate_label": label,
            "candidate_sha256": candidate_sha256, "candidate_form": form_kind,
            "variant": variant_label, "blob": tag,
        }

        for segment, scope_names in segments.items():
            counters["segments_evaluated"] += 1

            # -- Raw-segment structural checks (DER/PSBT/tx/Salted__ only;
            #    never the key-format scanner here, see validate_structural). --
            if is_der_trigger(segment):
                counters["raw_der_trigger"] += 1
            raw_validation = validate_structural(segment)
            if raw_validation["der_ec"] is not None:
                counters["raw_der_parser_valid"] += 1
            if raw_validation["psbt"] is not None:
                counters["raw_psbt_trigger"] += 1
            if raw_validation["bitcoin_tx"] is not None:
                counters["raw_bitcoin_tx_trigger"] += 1
            if raw_validation["salted_header"]:
                counters["salted_header_trigger"] += 1
                structural_findings.append({
                    **provenance, "scopes": sorted(scope_names), "trigger": "salted_header",
                    "segment_length": len(segment), "segment_sha256": hashlib.sha256(segment).hexdigest(),
                })
            for key, label_name in (("der_ec", "der_ec_raw"), ("psbt", "psbt_raw"), ("bitcoin_tx", "bitcoin_tx_raw")):
                if raw_validation[key] is not None:
                    structural_findings.append({
                        **provenance, "scopes": sorted(scope_names), "trigger": label_name,
                        "segment_length": len(segment), "segment_sha256": hashlib.sha256(segment).hexdigest(),
                        "detail": raw_validation[key],
                    })

            # -- Decode-then-validate (depth one; full validator set). --
            for decoder_name, (trigger_fn, decode_fn) in DECODERS.items():
                if not trigger_fn(segment):
                    continue
                decoder_counters[decoder_name]["trigger"] += 1
                decoded = decode_fn(segment)
                if decoded is None:
                    continue
                decoder_counters[decoder_name]["decode_ok"] += 1
                unique_decoded_outputs[decoder_name].add(hashlib.sha256(decoded).hexdigest())

                validation = validate_full(decoded, targets)
                if is_parser_valid(validation):
                    decoder_counters[decoder_name]["parser_valid"] += 1

                exact_target_hit = validation.get("exact_target_hit")
                record = {
                    **provenance, "scopes": sorted(scope_names), "decoder": decoder_name,
                    "segment_length": len(segment), "decoded_length": len(decoded),
                    "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
                }
                if exact_target_hit is not None:
                    exact_target_hits.append({**record, **exact_target_hit})
                elif is_parser_valid(validation):
                    structural_findings.append({**record, "validation": {
                        k: v for k, v in validation.items() if k != "exact_target_hit"
                    }})
        attempts += 1

    return {
        "candidate_count": len(frozen_candidates() if candidates is None else candidates),
        "candidate_digest": candidate_list_digest(frozen_candidates() if candidates is None else candidates),
        "bodies_checked": counters["bodies_checked"],
        "segments_evaluated": counters["segments_evaluated"],
        "raw_segment_structural": {
            "der_trigger": counters["raw_der_trigger"],
            "der_parser_valid": counters["raw_der_parser_valid"],
            "psbt_parser_valid": counters["raw_psbt_trigger"],
            "bitcoin_tx_parser_valid": counters["raw_bitcoin_tx_trigger"],
            "salted_header_trigger": counters["salted_header_trigger"],
        },
        "decoders": {
            name: {**decoder_counters[name], "unique_decoded_outputs": len(unique_decoded_outputs[name])}
            for name in DECODERS
        },
        "structural_findings": structural_findings,
        "structural_findings_count": len(structural_findings),
        "exact_target_hits": exact_target_hits,
        "total_exact_target_hits": len(exact_target_hits),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    # 1. Hex: planted positive + malformed near-positive.
    payload = b"the quick brown fox"
    hex_seg = payload.hex().encode()
    assert is_hex_trigger(hex_seg)
    assert decode_hex(hex_seg) == payload
    bad_hex = hex_seg[:-1] + b"g"  # 'g' is not a hex digit
    assert not is_hex_trigger(bad_hex)
    odd_hex = hex_seg[:-1]
    assert not is_hex_trigger(odd_hex)

    # 2. Base64 standard + URL-safe: planted positive, non-canonical near-positive.
    b64 = base64.b64encode(payload)
    assert base64_trigger_variant(b64) == "standard"
    assert decode_base64(b64, "standard") == payload
    b64url_payload = bytes(range(64))  # forces both +/ and -_ absent, but non-canonical padding below
    b64url = base64.urlsafe_b64encode(b64url_payload)
    assert base64_trigger_variant(b64url) == "urlsafe"
    assert decode_base64(b64url, "urlsafe") == b64url_payload
    non_canonical = b"AB==" + b64[4:]  # forcibly wrong padding pattern spliced in
    variant = base64_trigger_variant(non_canonical)
    if variant is not None:
        assert decode_base64(non_canonical, variant) is None, "non-canonical base64 must be rejected"

    # 3. zlib/gzip: planted positive, corrupted near-positive, decompression-bomb cap.
    zlib_seg = zlib.compress(payload)
    assert is_zlib_trigger(zlib_seg)
    assert decode_zlib(zlib_seg) == payload
    corrupted_zlib = zlib_seg[:-1] + bytes([zlib_seg[-1] ^ 0xFF])  # flips the Adler32 trailer
    assert decode_zlib(corrupted_zlib) is None, "checksum-corrupted zlib stream must be rejected"

    co = zlib.compressobj(9, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    gzip_seg = co.compress(payload) + co.flush()
    assert is_gzip_trigger(gzip_seg)
    assert decode_gzip(gzip_seg) == payload

    bomb_source = b"\x00" * 50_000_000  # 50MB of zeros compresses to a few KB
    bomb = zlib.compress(bomb_source, 9)
    assert len(bomb) < 100_000
    assert is_zlib_trigger(bomb)
    assert decode_zlib(bomb) is None, "a decompression bomb must be rejected by the size/ratio cap, not materialized"
    del bomb_source

    # 4. ZIP: planted positive, truncated near-positive.
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("m", payload)
    zip_seg = zip_buf.getvalue()
    assert is_zip_trigger(zip_seg)
    assert decode_zip(zip_seg) == payload
    truncated_zip = zip_seg[:-5]
    assert decode_zip(truncated_zip) is None, "a truncated ZIP must be rejected"

    # 5. DER: planted RFC5915-shaped EC private key (real secp256k1 scalar +
    #    OID), malformed (truncated) near-positive.
    scalar = (12345).to_bytes(32, "big")
    # SEQUENCE { INTEGER 1, OCTET STRING scalar, [0] OID secp256k1 }
    version_tlv = bytes([0x02, 0x01, 0x01])
    privkey_tlv = bytes([0x04, 0x20]) + scalar
    oid_inner = SECP256K1_OID_DER
    curve_tlv = bytes([0xA0, len(oid_inner)]) + oid_inner
    body = version_tlv + privkey_tlv + curve_tlv
    der_seg = bytes([0x30, len(body)]) + body
    assert is_der_trigger(der_seg)
    parsed = parse_der_ec_key(der_seg)
    assert parsed is not None and parsed["secp256k1_oid_found"] and parsed["candidate_scalar"] == scalar

    malformed_der = der_seg[:-3]  # breaks the declared outer length vs actual consumed length
    assert not is_der_trigger(malformed_der)

    # PKCS8-shaped: SEQUENCE { INTEGER 0, SEQUENCE{...}, OCTET STRING <- wraps der_seg }
    pkcs8_inner_oid_seq = bytes([0x30, 2, 0x05, 0x00])  # dummy inner algorithm SEQUENCE
    pkcs8_body = bytes([0x02, 1, 0x00]) + pkcs8_inner_oid_seq + bytes([0x04, len(der_seg)]) + der_seg
    pkcs8_seg = bytes([0x30, len(pkcs8_body)]) + pkcs8_body
    assert is_der_trigger(pkcs8_seg)
    pkcs8_parsed = parse_der_ec_key(pkcs8_seg)
    assert pkcs8_parsed is not None and pkcs8_parsed["candidate_scalar"] == scalar, \
        "PKCS8-wrapped RFC5915 scalar must be recovered via the one bounded extra hop"

    # 6. PSBT: minimal valid structure (magic + one empty-ish global map +
    #    zero further maps, exact consumption), corrupted near-positive.
    def compact_size(n):
        return bytes([n]) if n < 0xFD else (b"\xFD" + n.to_bytes(2, "little"))

    global_map = compact_size(1) + b"\x00" + compact_size(4) + b"\xAA\xBB\xCC\xDD" + b"\x00"
    psbt_seg = PSBT_MAGIC + global_map
    assert parse_psbt(psbt_seg) is not None
    assert parse_psbt(psbt_seg[:-1]) is None, "a PSBT missing its map terminator must be rejected"
    assert parse_psbt(b"not-psbt-magic-----") is None

    # 7. Bitcoin transaction: minimal valid legacy tx (1 in, 1 out), truncated near-positive.
    tx_seg = (
        (1).to_bytes(4, "little")            # version
        + compact_size(1)                     # input count
        + b"\x11" * 32 + (0).to_bytes(4, "little")  # prevout hash + index
        + compact_size(0)                     # empty scriptSig
        + b"\xFF" * 4                          # sequence
        + compact_size(1)                     # output count
        + (5000).to_bytes(8, "little")        # value
        + compact_size(0)                     # empty scriptPubKey
        + (0).to_bytes(4, "little")            # locktime
    )
    assert parse_bitcoin_transaction(tx_seg) is not None
    assert parse_bitcoin_transaction(tx_seg[:-1]) is None, "a truncated transaction must be rejected"
    assert parse_bitcoin_transaction(tx_seg + b"\x00") is None, "trailing garbage must be rejected (exact consumption)"

    # 8. Salted__ structural trigger: block-aligned positive, misaligned negative.
    salted_ok = b"Salted__" + b"\x01" * 8 + b"\x02" * 32  # 16 + 32 = block-aligned
    assert is_salted_header_trigger(salted_ok)
    salted_misaligned = b"Salted__" + b"\x01" * 8 + b"\x02" * 5  # not a multiple of 16
    assert not is_salted_header_trigger(salted_misaligned)

    # 9. Scope extraction: whole-body/line/token, deduped, tagged correctly.
    multi = b"tokenA tokenB\ntokenC"
    scopes = extract_scopes(multi)
    assert scopes[multi] == {"whole_body"}
    assert scopes[b"tokenA tokenB"] == {"line"}
    assert scopes[b"tokenC"] == {"line", "token"}  # last line has no trailing content, also a lone token
    assert scopes[b"tokenA"] == {"token"} and scopes[b"tokenB"] == {"token"}

    # 10. End-to-end planted positive through the REAL decrypt pipeline: a
    #     synthetic body whose token-scope segment is Base64 of a DER/PKCS8
    #     structure carrying a scalar that matches a planted known target.
    import cb_common
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    target_scalar = (999_983).to_bytes(32, "big")  # distinct from the DER unit test's scalar
    target_privkey_tlv = bytes([0x04, 0x20]) + target_scalar
    target_body = version_tlv + target_privkey_tlv + curve_tlv
    target_der = bytes([0x30, len(target_body)]) + target_body
    target_b64 = base64.b64encode(target_der)
    from binary_key_material_backfill import private_key_details
    target_addrs = private_key_details(target_scalar)
    synthetic_target = {bytes.fromhex(target_addrs["compressed"]["hash160"]): "planted/compressed"}

    filler = b"noise_filler_bytes_padding_out_to_size_"
    synth_body = filler + b" " + target_b64 + b" " + filler  # token-scope isolates target_b64 exactly
    assert len(synth_body) >= 64

    synth_passwd = b"seed2-self-test-password"
    synth_salt = b"seed2slt"
    key, iv = cb_common.evp_bytes_to_key(synth_passwd, synth_salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    ct = encryptor.update(synth_body) + encryptor.finalize()
    synthetic_blobs = {"SYNTH": (synth_salt, ct)}

    report = run(blobs=synthetic_blobs, candidates=[synth_passwd.decode()],
                 known_targets={**KNOWN_TARGET_HASH160S, **synthetic_target})

    assert report["total_exact_target_hits"] >= 1, "planted Base64(DER-EC-scalar) hit was not found end-to-end"
    hit = next(h for h in report["exact_target_hits"] if h["decoder"] == "base64" and h["source"] == "der_ec")
    assert hit["candidate_index"] == 0
    assert hit["candidate_sha256"] == hashlib.sha256(synth_passwd).hexdigest()
    assert "token" in hit["scopes"]

    # 11. Negative control: an unrelated password against the same
    #     synthetic blob must not produce any exact-target hit.
    wrong_report = run(blobs=synthetic_blobs, candidates=["definitely-not-the-password"])
    assert wrong_report["total_exact_target_hits"] == 0

    # 12. Random length-matched controls: trigger noise on tiny tokens is
    #     expected (short byte runs can land in the hex/base64 alphabets by
    #     chance), but parser-valid and exact-target counts must be zero --
    #     the actual claim this control needs to support.
    import random
    rng = random.Random(20260820)
    random_bodies = [bytes(rng.randrange(256) for _ in range(rng.choice([64, 80, 96, 128])))
                      for _ in range(200)]
    random_report_findings = 0
    random_report_hits = 0
    for rb in random_bodies:
        for segment in extract_scopes(rb):
            structural = validate_structural(segment)
            if is_parser_valid(structural):
                random_report_findings += 1
            for decoder_name, (trigger_fn, decode_fn) in DECODERS.items():
                if not trigger_fn(segment):
                    continue
                decoded = decode_fn(segment)
                if decoded is None:
                    continue
                validation = validate_full(decoded)
                if validation.get("exact_target_hit") is not None:
                    random_report_hits += 1
                elif is_parser_valid(validation):
                    random_report_findings += 1
    assert random_report_hits == 0, "random length-matched controls must never produce an exact-target hit"
    assert random_report_findings == 0, (
        "random length-matched controls must never produce a parser-valid structural finding "
        f"(got {random_report_findings}) -- DER/PSBT/tx/key-format/Salted__ are all checksum- or "
        "structure-gated specifically so chance noise cannot pass them"
    )

    # 13. Frozen-corpus contract (same pin as every sibling script).
    cands = frozen_candidates()
    assert len(cands) == 42
    assert candidate_list_digest(cands) == EXPECTED_CANDIDATE_DIGEST

    # 14. Bounded-scope sanity: the real corpus reuse produces the exact
    #     same body count Phase 336/337/338 already reported (12,128) --
    #     confirms this pilot did not silently change the crypto scope.
    body_count = sum(1 for _ in iter_retained_bodies())
    assert body_count == 12_128, f"expected the Phase 336/337/338 corpus size 12,128, got {body_count}"

    print("[*] self-test OK: hex/base64/zlib/gzip/zip decoders each verified with a planted positive "
          "and a malformed/corrupted near-positive; a 50MB decompression bomb rejected by the size/"
          "ratio cap; DER (including one-hop PKCS8-wrapped RFC5915) and PSBT and Bitcoin-transaction "
          "parsers each verified with a minimal valid structure and a truncated/corrupted rejection; "
          "Salted__ block-alignment trigger checked both ways; scope extraction (whole-body/line/"
          "token) tagging verified; a planted Base64(DER-EC-scalar) hit recovered end-to-end through "
          "the real AES pipeline with full provenance and correct scope tagging; wrong-password "
          "control clean; 200 random length-matched controls produced zero parser-valid findings and "
          f"zero exact-target hits; frozen-corpus digest {EXPECTED_CANDIDATE_DIGEST} enforced; exact "
          "12,128-body corpus-reuse count confirmed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else {"note": "pass --run to execute the audit"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            if key in ("structural_findings", "exact_target_hits"):
                continue
            print(f"{key}: {value}")
        for finding in report.get("structural_findings", [])[:20]:
            print("FINDING:", finding)
        for hit in report.get("exact_target_hits", []):
            print("HIT:", hit)


if __name__ == "__main__":
    main()
