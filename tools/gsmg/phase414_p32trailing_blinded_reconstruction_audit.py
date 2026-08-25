#!/usr/bin/env python3
"""Phase 414: blinded independent reconstruction of P32TRAILING.

See ``doc/Brainstorms/2026-08-25 - Phase 414 P32TRAILING Blinded
Independent Reconstruction Pre-Registration.md`` for the frozen protocol
this module implements. Summary: build a self-contained evidence packet
(exactly the Phase 3.2 plaintext, three solved-boundary calibration
examples, the assembly recipe, and the prize-address requirement -- no
project hypothesis history), hand it to clean-context solver invocations,
apply a frozen convergence/closure promotion rule to their candidates,
and test only promoted candidates through a redacting oracle wrapper that
never returns raw plaintext, WIF strings, or private key bytes.

This module intentionally does NOT call ``passphrase_hits()``
(``color_mask_full_stream_audit.py``) unmodified -- that function returns
``repr(result)``, which contains decrypted plaintext bytes. It also does
NOT call ``aes_try_open_ecb_bytes()``/``aes_try_open_stream_bytes()``
unmodified -- both call ``cb_common._log_candidate()`` internally for
any "weak" (5 <= z < 8) decrypt, which appends the raw password material
and a 200-byte plaintext preview to ``weak_candidates_log.txt`` on disk,
regardless of what this module's own caller does with the return value.
ECB and stream decryption are re-implemented locally (same frozen
variant lists, same crypto) with no such side effect. Everything here
that touches a candidate decrypt keeps the plaintext in a local variable
only long enough to classify it, then discards it.

Actually spawning clean-context solver invocations is done by the
orchestrating agent (outside this process, via whatever agent-spawning
mechanism its environment provides) -- see `run_solvers()`'s docstring.
This module owns the decision logic (panel validity, promotion,
testing), not the spawning itself.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa: E402
from cryptography.hazmat.primitives.keywrap import aes_key_wrap  # noqa: E402

from binary_key_material_backfill import private_key_details  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    CIPHER_BLOCK_SIZES,
    CIPHER_CLASSES,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    PRINTABLE_Z_STRONG_THRESHOLD,
    PRINTABLE_Z_WEAK_THRESHOLD,
    STREAM_CIPHER_VARIANTS,
    STREAM_MODE_CLASSES,
    WEAK_CANDIDATE_LOG,
    _kdf_label,
    _normalize_variant,
    aes_keywrap_try_open_bytes,
    derive_kek,
    evp_bytes_to_key,
    is_structural_binary_plaintext,
    pbkdf2_bytes_to_key,
    printable_z_score,
)
from data import VERIFIED_PRIOR_COMMAND_HASHES
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402
from key_shape_classifier import find_hex64, find_wif  # noqa: E402
from p32_sibling_password_audit import decrypt_phase32_bytes, extract_phase32_components  # noqa: E402
from phase3_sevenpart_permutation_audit import PHASE3_PARTS  # noqa: E402


PHASE32_PLAINTEXT_SHA256 = "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"
EVIDENCE_PACKET_SHA256 = "70286ecd5795671733452cdce1d64bda57cd863191ada1f4fa561f17e3341aa8"

MAX_SOLVER_CANDIDATES = 10
FAMILY_PROMOTION_THRESHOLD = 2  # convergence: at least this many eligible submissions
INVOCATION_CAP = 8
PANEL_TARGET = 5

# The exact Phase-410 profile: legacy EVP_BytesToKey, SHA-256, AES-256 --
# the first entry KDF_VARIANTS already names, tested here in isolation and
# then excluded from the "remaining" broad sweep so it is never run twice.
PHASE410_EXACT_VARIANT = ("sha256", 32)

# Preregistered allowlist of (packet_text) character-offset spans that
# qualify as a "selector instruction with zero remaining alternatives"
# for single-derivation closure promotion. Byte-offset verification alone
# can only prove that some text EXISTS at a span and that concatenating
# spans reconstructs a candidate's bytes -- it cannot prove that text
# actually INSTRUCTS token selection with no other reading. That is a
# semantic judgment this code cannot make, so closure is gated on this
# frozen, preregistered allowlist instead of on any solver's own claim.
# It is empty: nothing in the Phase 414 packet actually names a
# construction instruction for P32TRAILING itself (only the three
# ALREADY-SOLVED calibration examples do, and their instructions are
# deliberately not included in the packet -- see the preregistration's
# own note that this path is expected to rarely or never fire). Adding a
# span here is a new preregistration decision, never something this
# module does at runtime based on a solver's assertion.
QUALIFYING_CLOSURE_INSTRUCTION_SPANS = ()

FORBIDDEN_VOCAB = (
    "DBBI", "FAED", "SALPH", "SALPHASEION", "SalPhaseIon", "Cosmic Duality",
    "URLBLOB", "BTCSEED", "KMODEST", "yin-yang", "yinyang", "FINDINGS.md",
    "GSMG_SCIENTIFIC_THEORY_REGISTRY", "Naddiseo", "HosterjackAGV",
    "halbgott", "puzzlehunt/gsmgio",
)
FORBIDDEN_PHASE_RE = re.compile(r"phase\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
ALLOWED_PHASE_NUMBERS = {"2", "3", "3.2"}
GITHUB_URL_RE = re.compile(r"github\.com", re.IGNORECASE)

# Structural tiers that are meaningful on their own (per the corrected
# protocol: raw in-curve-range scalar validity alone is NOT one of these --
# a uniformly random 32-byte value is a valid secp256k1 scalar with
# probability effectively 1, so it carries no evidential weight by itself).
STRUCTURAL_TIERS = ("full_block", "valid_wif", "hex64_shape", "strong_text", "keywrap_integrity")


# ── Evidence packet ──────────────────────────────────────────────────────

def _hex_dump(data, bytes_per_line=32):
    return "\n".join(
        data[i:i + bytes_per_line].hex() for i in range(0, len(data), bytes_per_line)
    )


def _assert_clean_ascii(label, chunk):
    if not all(byte in (9, 10, 13) or 32 <= byte < 127 for byte in chunk):
        raise AssertionError(f"evidence packet segment {label!r} is not clean ASCII")


PHASE3_PART_LABELS = (
    "part 1 (Phase 2's own solved password)",
    "part 2", "part 3", "part 4", "part 5",
    "part 6 (hex token)", "part 7 (chess FEN)",
)


def build_evidence_packet():
    """Deterministically render the frozen, exhaustive evidence packet.

    Returns (packet_text, sha256_hex). Sourced only from data.py /
    decrypt_phase32_bytes() -- no manually retyped security-sensitive
    string."""
    plaintext = decrypt_phase32_bytes()
    if hashlib.sha256(plaintext).hexdigest() != PHASE32_PLAINTEXT_SHA256:
        raise AssertionError("Phase 3.2 plaintext no longer matches the pinned hash")
    components = extract_phase32_components(plaintext)
    off = components["offsets"]
    prefix = plaintext[:off["encoded_321_start"]]
    middle = plaintext[off["encoded_321_start"]:off["encoded_321_end"]]
    suffix = plaintext[off["encoded_321_end"]:]
    _assert_clean_ascii("prefix", prefix)
    _assert_clean_ascii("suffix", suffix)
    if len(prefix) + len(middle) + len(suffix) != len(plaintext):
        raise AssertionError("evidence packet segmentation does not cover the full plaintext")

    phase3_preimage = "".join(PHASE3_PARTS)
    phase3_hash = hashlib.sha256(phase3_preimage.encode("utf-8")).hexdigest()
    if phase3_hash != VERIFIED_PRIOR_COMMAND_HASHES["phase3_parts"]:
        raise AssertionError("Phase 3 seven-part preimage no longer matches the pinned hash")
    phase2_preimage = "causality"
    phase2_hash = hashlib.sha256(phase2_preimage.encode("utf-8")).hexdigest()
    if phase2_hash != VERIFIED_PRIOR_COMMAND_HASHES["phase2_causality"]:
        raise AssertionError("Phase 2 preimage no longer matches the pinned hash")
    phase32_preimage = (
        "jacquefresco" + "giveit" + "justonesecond" + "heisenbergsuncertaintyprinciple"
    )
    phase32_hash = hashlib.sha256(phase32_preimage.encode("utf-8")).hexdigest()
    if phase32_hash != VERIFIED_PRIOR_COMMAND_HASHES["phase32_clues"]:
        raise AssertionError("Phase 3.2 preimage no longer matches the pinned hash")

    parts = []
    parts.append("=" * 78)
    parts.append("ITEM 1 -- Exact Phase 3.2 plaintext (2422 bytes total) and trailing")
    parts.append("ciphertext. Everything below up to (not including) the final base64")
    parts.append("block is confirmed, already-decrypted output from earlier, SOLVED")
    parts.append("stages of this puzzle (Phase 2 through Phase 3.2). The final base64")
    parts.append("block is the sole unsolved target.")
    parts.append("=" * 78)
    parts.append("")
    parts.append(f"[bytes 0-{off['encoded_321_start']}, literal text]")
    parts.append(prefix.decode("ascii"))
    parts.append("")
    parts.append(
        f"[bytes {off['encoded_321_start']}-{off['encoded_321_end']}, "
        f"{len(middle)} bytes, an embedded ciphertext sub-block from an earlier "
        "solved stage -- non-ASCII, rendered as hex, 32 bytes per line, so this "
        "packet stays valid UTF-8]"
    )
    parts.append(_hex_dump(middle))
    parts.append("")
    parts.append(f"[bytes {off['encoded_321_end']}-{len(plaintext)}, literal text, includes the")
    parts.append("final unsolved base64 block at the very end]")
    parts.append(suffix.decode("ascii"))
    parts.append("")
    parts.append("=" * 78)
    parts.append("ITEM 2 -- Three solved AES boundaries, worked calibration examples.")
    parts.append("Case in each preimage is fixed by that stage's own instruction, not a")
    parts.append("free choice -- e.g. Phase 3.2's instruction forces all-lowercase.")
    parts.append("=" * 78)
    parts.append("")
    parts.append("Phase 2:")
    parts.append(f"  preimage (exact):  {phase2_preimage}")
    parts.append(f"  SHA-256 hex digest (= the literal AES password): {phase2_hash}")
    parts.append("")
    parts.append("Phase 3 (seven parts, concatenated in this exact order, no separators):")
    for label, part in zip(PHASE3_PART_LABELS, PHASE3_PARTS):
        parts.append(f"  {label}: {part}")
    parts.append(f"  full preimage (exact): {phase3_preimage}")
    parts.append(f"  SHA-256 hex digest (= the literal AES password): {phase3_hash}")
    parts.append("")
    parts.append("Phase 3.2 (four parts, concatenated in this exact order, no separators,")
    parts.append("all lowercase per that stage's own instruction):")
    parts.append(f"  preimage (exact): {phase32_preimage}")
    parts.append(f"  SHA-256 hex digest (= the literal AES password): {phase32_hash}")
    parts.append("")
    parts.append("=" * 78)
    parts.append("ITEM 3 -- The solved-stage assembly instructions (the recipe, stated")
    parts.append("once, generically -- all three examples above follow it exactly):")
    parts.append("=" * 78)
    parts.append("")
    parts.append("  1. A candidate preimage is one or more tokens, concatenated in a")
    parts.append("     fixed order with NO separator characters between them, in")
    parts.append("     whatever case that token's own originating instruction fixes.")
    parts.append("  2. The AES password actually used is NOT the preimage's raw bytes --")
    parts.append("     it is the LOWERCASE HEX SHA-256 DIGEST STRING of the preimage,")
    parts.append("     itself treated as an ASCII string.")
    parts.append("  3. That hex-digest string is the password argument to OpenSSL's")
    parts.append("     legacy EVP_BytesToKey key derivation (digest = SHA-256, 32-byte")
    parts.append("     key + 16-byte IV) against the blob's own salt.")
    parts.append("  4. The blob is base64 of \"Salted__\" + 8-byte salt + ciphertext,")
    parts.append("     standard OpenSSL CLI format; decrypt with AES-256-CBC, then")
    parts.append("     remove standard PKCS#7 padding.")
    parts.append("")
    parts.append("=" * 78)
    parts.append("ITEM 4 -- Prize address and output requirement, verbatim from the")
    parts.append("puzzle's own creator description.")
    parts.append("=" * 78)
    parts.append("")
    parts.append('  The creator explicitly described the final result as "a regular')
    parts.append('  Bitcoin private key". The known prize address is:')
    parts.append(f"  {PRIZE_ADDRESS}")
    parts.append("")

    packet_text = "\n".join(parts)
    return packet_text, hashlib.sha256(packet_text.encode("utf-8")).hexdigest()


def write_evidence_packet(path):
    packet_text, digest = build_evidence_packet()
    Path(path).write_bytes(packet_text.encode("utf-8"))
    return digest


# ── Strict submission schema ──────────────────────────────────────────────
#
# "Reject wholesale" means exactly that: any schema violation anywhere in
# a submission (an unrecognized field, a wrong type, too many/few raw
# candidates, a non-contiguous rank permutation, non-lowercase hex, a
# duplicate preimage within one solver's own list) voids the ENTIRE
# submission, not just the offending candidate. There is no per-candidate
# salvage and no silent coercion (e.g. no case-folding a submitted hex
# string into shape) -- a submission either matches the frozen shape
# exactly, or it does not count.

REQUIRED_SUBMISSION_KEYS = frozenset({"tool_used", "reasoning_text", "candidates"})
REQUIRED_CANDIDATE_KEYS = frozenset({"display", "preimage_utf8_hex", "derivation", "rank"})
ALLOWED_CANDIDATE_KEYS = REQUIRED_CANDIDATE_KEYS | {"closure"}
REQUIRED_CLOSURE_KEYS = frozenset({
    "instruction_offset_start", "instruction_offset_end",
    "instruction_quote", "token_spans", "zero_alternatives",
})
LOWERCASE_HEX_RE = re.compile(r"[0-9a-f]+")


def validate_submission_schema(submission):
    """Returns (True, parsed_candidates) or (False, reason). Never
    normalizes anything (no case-folding, no defaulting of missing
    fields) -- a submission either matches the frozen shape exactly or
    the whole thing is rejected."""
    if not isinstance(submission, dict) or set(submission.keys()) != REQUIRED_SUBMISSION_KEYS:
        return False, "unexpected or missing top-level keys"
    if not isinstance(submission["tool_used"], bool):
        return False, "tool_used must be an explicit boolean"
    if not isinstance(submission["reasoning_text"], str):
        return False, "reasoning_text must be a string"

    raw_candidates = submission["candidates"]
    if not isinstance(raw_candidates, list) or not (1 <= len(raw_candidates) <= MAX_SOLVER_CANDIDATES):
        return False, f"candidates must be a list of 1..{MAX_SOLVER_CANDIDATES} raw entries (before dedup)"

    parsed, ranks, seen_hex = [], [], set()
    for candidate in raw_candidates:
        if not isinstance(candidate, dict) or not (REQUIRED_CANDIDATE_KEYS <= set(candidate.keys()) <= ALLOWED_CANDIDATE_KEYS):
            return False, "candidate has unexpected or missing keys"

        hex_value = candidate["preimage_utf8_hex"]
        if not isinstance(hex_value, str) or not LOWERCASE_HEX_RE.fullmatch(hex_value) or len(hex_value) % 2:
            return False, "preimage_utf8_hex must be non-empty, even-length, strictly lowercase hex"
        material = bytes.fromhex(hex_value)
        try:
            if material.decode("utf-8") != candidate["display"]:
                return False, "display does not round-trip to preimage_utf8_hex"
        except UnicodeDecodeError:
            return False, "preimage_utf8_hex is not valid UTF-8"
        if not isinstance(candidate["display"], str) or not candidate["display"]:
            return False, "display must be a non-empty string"
        if not isinstance(candidate["derivation"], str) or not candidate["derivation"]:
            return False, "derivation must be a non-empty string"

        rank = candidate["rank"]
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            return False, "rank must be a positive integer"
        ranks.append(rank)

        closure = candidate.get("closure")
        if closure is not None:
            if not isinstance(closure, dict) or set(closure.keys()) != REQUIRED_CLOSURE_KEYS:
                return False, "closure has unexpected or missing keys"
            # A closure object IS, by definition, a claim of zero remaining
            # alternatives -- `zero_alternatives` must therefore be the
            # literal boolean True whenever the object is present at all;
            # `false` (or any non-bool truthy/falsy value) is a
            # self-contradictory closure, not a weaker one, and voids the
            # whole submission here rather than merely failing to promote
            # later.
            if closure["zero_alternatives"] is not True:
                return False, "closure.zero_alternatives must be the literal boolean true whenever present"
            if not isinstance(closure["instruction_quote"], str) or not closure["instruction_quote"]:
                return False, "closure.instruction_quote must be a non-empty string"
            for offset_key in ("instruction_offset_start", "instruction_offset_end"):
                offset_value = closure[offset_key]
                if not isinstance(offset_value, int) or isinstance(offset_value, bool) or offset_value < 0:
                    return False, f"closure.{offset_key} must be a nonnegative plain integer"
            if closure["instruction_offset_start"] >= closure["instruction_offset_end"]:
                return False, "closure.instruction_offset_start must be < instruction_offset_end"
            spans = closure["token_spans"]
            if not isinstance(spans, list) or not spans:
                return False, "closure.token_spans must be a non-empty list"
            for span in spans:
                if not isinstance(span, (list, tuple)) or len(span) != 2:
                    return False, "closure.token_spans entries must be exactly [start, end]"
                start, end = span
                if (
                    not isinstance(start, int) or isinstance(start, bool) or start < 0
                    or not isinstance(end, int) or isinstance(end, bool)
                    or start >= end
                ):
                    return False, (
                        "closure.token_spans entries must be nonnegative integer [start, end] pairs "
                        "with start < end"
                    )

        if hex_value in seen_hex:
            return False, "duplicate preimage_utf8_hex within one submission"
        seen_hex.add(hex_value)
        parsed.append({**candidate, "material": material})

    if sorted(ranks) != list(range(1, len(raw_candidates) + 1)):
        return False, "ranks must be exactly a 1..n permutation with no duplicates or gaps"

    return True, parsed


def _collect_strings(value, out):
    """Recursively collect every string leaf in a JSON-like structure --
    deliberately generic rather than a hardcoded field list, so an
    unrecognized field (which the schema check above would in any case
    already reject) or a nested one still gets scanned as defense in
    depth."""
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            _collect_strings(item, out)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _collect_strings(item, out)


def submission_full_text(submission):
    out = []
    _collect_strings(submission, out)
    return "\n".join(out)


def blinding_violations(text):
    hits = []
    lowered = text.lower()
    for term in FORBIDDEN_VOCAB:
        if term.lower() in lowered:
            hits.append(term)
    if GITHUB_URL_RE.search(text):
        hits.append("github.com URL")
    for match in FORBIDDEN_PHASE_RE.finditer(text):
        if match.group(1) not in ALLOWED_PHASE_NUMBERS:
            hits.append(f"phase {match.group(1)}")
    return hits


# Anchored for `fullmatch()`, not `search()` -- a fenced block found
# ANYWHERE inside surrounding prose is not the same as the ENTIRE
# response being (nothing but) a single fenced JSON block, and the
# frozen prompt requires the latter.
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


def _reject_duplicate_keys(pairs):
    """`object_pairs_hook` for `json.loads()`. Python's default JSON
    object construction silently lets a later duplicate key overwrite an
    earlier one (`{"tool_used":true,"tool_used":false}` -> `False`) --
    this hook raises instead, at every nesting level (the hook is
    invoked by the parser for every `{...}` it encounters, not just the
    top level), so a submission that relies on that silent-overwrite
    ambiguity is treated as unparseable, not resolved by whichever
    reading `json.loads()` happened to pick."""
    seen = set()
    result = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key {key!r}")
        seen.add(key)
        result[key] = value
    return result


def parse_submission(raw_text):
    """Mechanical, content-preserving extraction only -- never a semantic
    reinterpretation of malformed output (that would itself violate the
    no-coercion rule). Tries direct JSON parsing first; if that fails,
    tries treating the ENTIRE (stripped) response as a single fenced
    ```json code block and parsing that -- `fullmatch`, not `search`, so
    prose surrounding the fence is a rejection, not something to strip
    away. Anything else -- prose, multiple JSON objects, a duplicate key
    at any nesting level, no parseable JSON at all -- returns None: an
    unparseable response is never coerced into shape; it simply fails to
    produce a submission, still consumes an invocation-cap slot, and
    never counts toward the panel."""
    if not isinstance(raw_text, str):
        return None
    stripped = raw_text.strip()
    try:
        return json.loads(stripped, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    match = JSON_FENCE_RE.fullmatch(stripped)
    if match:
        try:
            return json.loads(match.group(1), object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def eligible_submissions(invocation_records):
    """`invocation_records`: a dict mapping orchestrator-assigned,
    unique invocation ID -> raw (untrusted) submission dict (already
    parsed by `parse_submission()`; a failed parse is simply never added
    to this dict). Keying by invocation ID -- never by list position or
    submission content -- is the whole point: an ID can appear at most
    once by construction (it is a dict key), so replaying the same
    submission object under the SAME id can never inflate its vote
    count, while two genuinely different invocations that happen to
    converge on identical content (the intended, real convergence
    signal) still count as two. The invocation ID is never present
    inside the solver-authored JSON itself -- it is assigned by
    whichever code collects the raw response, before this function ever
    sees it.

    Returns only schema-valid, non-tool-using, leak-free ones, each
    annotated with its own invocation ID and parsed candidate list."""
    eligible = []
    for invocation_id, submission in invocation_records.items():
        ok, parsed_or_reason = validate_submission_schema(submission)
        if not ok:
            continue
        if submission["tool_used"]:
            continue
        if blinding_violations(submission_full_text(submission)):
            continue
        eligible.append({"invocation_id": invocation_id, **submission, "accepted": parsed_or_reason})
    return eligible


def evaluate_panel(invocation_records, invocations_used):
    """Predeclared panel-validity decision (frozen invocation cap / panel
    target). `invocation_records` is the dict described in
    `eligible_submissions()` -- every successfully-parsed submission
    collected so far, keyed by its unique invocation ID.
    `invocations_used` is how many clean-context invocations have been
    spawned so far (>= len(invocation_records), since an invocation can
    fail to even produce a parseable submission -- `parse_submission()`
    returning None -- and such a failure still counts against the cap
    without ever entering `invocation_records`).

    Returns {"status": "panel_ready"|"need_more"|"protocol_invalid",
    "eligible": [...]}. `protocol_invalid` must be reported as a
    methodology note, never as evidence of non-identifiability.

    Ledger consistency is checked, and the cap is enforced, BEFORE panel
    readiness is even considered -- an over-cap or otherwise
    structurally inconsistent ledger is a bug in the calling
    orchestration loop (which must never spawn past the cap in the
    first place), not a phase result, so it raises rather than silently
    reporting "panel_ready" just because 5 eligible records happen to
    already be present."""
    if invocations_used < len(invocation_records):
        raise ValueError("invocations_used cannot be smaller than the number of collected records")
    if invocations_used > INVOCATION_CAP:
        raise ValueError(
            f"invocations_used ({invocations_used}) exceeds the frozen cap ({INVOCATION_CAP}) -- "
            "the orchestrator must never call evaluate_panel() past the cap; this is a ledger bug, "
            "not a phase result, and must not be allowed to reach panel_ready"
        )
    eligible = eligible_submissions(invocation_records)
    if len(eligible) >= PANEL_TARGET:
        return {"status": "panel_ready", "eligible": eligible[:PANEL_TARGET]}
    if invocations_used >= INVOCATION_CAP:
        return {"status": "protocol_invalid", "eligible": eligible}
    return {"status": "need_more", "eligible": eligible}


def run_solvers():
    """Spawning clean-context solver invocations is the orchestrating
    agent's job (done through whatever agent-spawning mechanism its own
    environment provides), not this in-process script's -- there is no
    portable, importable Python API for it here. The orchestrating agent
    must, for each invocation: assign it a fresh, unique invocation ID
    from its own side (never taken from or influenced by the solver's
    own output), call `parse_submission()` on the raw response text, and
    -- if that produced a dict, not None -- record it in a running
    `{invocation_id: parsed_submission}` dict. After each invocation, it
    must call `evaluate_panel(invocation_records, invocations_used)` and
    stop spawning once that returns "panel_ready" or "protocol_invalid".
    This function exists only as the documented anchor for that
    contract; calling it directly is a usage error."""
    raise NotImplementedError(
        "run_solvers() cannot spawn agents from inside this script -- see its "
        "docstring. Use parse_submission() and evaluate_panel() to drive the "
        "external spawn loop."
    )


# ── Closure validation ───────────────────────────────────────────────────

def validate_closure(closure, packet_text, material):
    """Mechanically verifies the tightened single-derivation-closure path.
    Two independent gates, both required:

    1. The declared instruction span must be on the frozen, preregistered
       QUALIFYING_CLOSURE_INSTRUCTION_SPANS allowlist -- byte-offset
       verification alone can prove text exists and that spans
       reconstruct the candidate, but it cannot prove that text
       INSTRUCTS token selection with zero remaining alternatives; only
       a human, pre-committing before any solver runs, can make that
       call, so a solver's own "zero_alternatives" claim is never
       sufficient on its own.
    2. Every declared token span and the instruction quote must exist at
       their declared offsets in the actual packet text, and
       concatenating the declared spans in order must reconstruct the
       candidate's own material exactly.

    With an empty allowlist, this path can never fire -- which is the
    intended, documented behavior for Phase 414 (see the allowlist's own
    comment), not a bug.

    Defensive against malformed/adversarial shapes throughout (never
    raises on bad input -- e.g. a `None` entry inside `token_spans`,
    or a `bool` masquerading as an offset since `bool` is an `int`
    subclass in Python) even though `validate_submission_schema()`
    should already have rejected such a candidate before this is ever
    called; this is defense in depth, not the primary gate."""
    if not isinstance(closure, dict) or closure.get("zero_alternatives") is not True:
        return False

    def _plain_int(value):
        return isinstance(value, int) and not isinstance(value, bool)

    quote = closure.get("instruction_quote")
    q_start, q_end = closure.get("instruction_offset_start"), closure.get("instruction_offset_end")
    if not isinstance(quote, str) or not quote or not _plain_int(q_start) or not _plain_int(q_end):
        return False
    if not (0 <= q_start < q_end <= len(packet_text)):
        return False
    if (q_start, q_end) not in QUALIFYING_CLOSURE_INSTRUCTION_SPANS:
        return False
    if packet_text[q_start:q_end] != quote:
        return False
    spans = closure.get("token_spans")
    if not isinstance(spans, list) or not spans:
        return False
    reconstructed = ""
    for span in spans:
        if not isinstance(span, (list, tuple)) or len(span) != 2:
            return False
        start, end = span
        if not (_plain_int(start) and _plain_int(end) and 0 <= start < end <= len(packet_text)):
            return False
        reconstructed += packet_text[start:end]
    try:
        reconstructed_bytes = reconstructed.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return reconstructed_bytes == material


def promote_candidates(eligible, packet_text):
    """Implements the frozen two-path promotion rule. Returns a dict
    hex -> {"path": "convergence"|"closure", "votes": int, "ranks": [...]}.
    `ranks` (every contributing submission's rank for this candidate) is
    carried through so `test_candidates()` can order deterministically
    instead of relying on dict/insertion order."""
    votes = {}
    for submission in eligible:
        for candidate in submission["accepted"]:
            votes.setdefault(candidate["preimage_utf8_hex"], []).append(candidate)

    promoted = {}
    for hex_value, candidates in votes.items():
        ranks = [c["rank"] for c in candidates]
        if len(candidates) >= FAMILY_PROMOTION_THRESHOLD:
            promoted[hex_value] = {"path": "convergence", "votes": len(candidates), "ranks": ranks}
            continue
        for candidate in candidates:
            if validate_closure(candidate.get("closure"), packet_text, candidate["material"]):
                promoted[hex_value] = {"path": "closure", "votes": 1, "ranks": ranks}
                break
    return promoted


# ── Redacted structural classification ───────────────────────────────────

DEFAULT_TARGET_ADDRESSES = (PRIZE_ADDRESS, HALVING_ADDRESS)


def classify_plaintext(body, padding_tier=None, target_addresses=DEFAULT_TARGET_ADDRESSES):
    """Redacted structural classification. Never returns raw body/WIF/key
    bytes -- only shape facts and any matched public address.

    Deliberately does NOT treat "is a valid in-curve-range secp256k1
    scalar" as a structural signal on its own: nearly every uniformly
    random 32-byte value is a valid scalar (the curve order is ~2^256),
    so that property alone carries essentially no evidential weight. Raw
    32-byte chunks are used only for the address-match check; the
    reported structural tiers are limited to properties that ARE rare
    under a wrong key: an exact full-block PKCS7 pad, a checksum-valid
    WIF, a 64-hex-char shape, Key-Wrap integrity, or strong printable
    text.

    `target_addresses` defaults to the real prize/halving addresses;
    self-test fixtures override it with a synthetic planted address,
    since the real prize address's private key is, definitionally, not
    available to plant a genuine terminal-hit fixture with."""
    record = {
        "length": len(body),
        "printable_ratio": round(
            sum(1 for byte in body if 32 <= byte < 127 or byte in (9, 10, 13)) / len(body), 4
        ) if body else 0.0,
        "printable_z": round(printable_z_score(body), 4) if body else 0.0,
        "structural_tier": None,
        "address_match": None,
    }

    def _note_tier(tier):
        if record["structural_tier"] is None:
            record["structural_tier"] = tier

    def _check_address(key32):
        details = private_key_details(key32)
        if not details:
            return
        for form in details.values():
            if form["address"] in target_addresses:
                record["address_match"] = form["address"]

    if padding_tier == "full_block":
        _note_tier("full_block")

    if body and len(body) % 32 == 0:
        for i in range(0, len(body), 32):
            _check_address(body[i:i + 32])

    for _kind, key in find_wif(body):
        _note_tier("valid_wif")
        _check_address(key)

    for _kind, key in find_hex64(body):
        _note_tier("hex64_shape")
        _check_address(key)

    if record["structural_tier"] is None and record["printable_z"] >= PRINTABLE_Z_STRONG_THRESHOLD:
        _note_tier("strong_text")

    return record


def _is_hit(record):
    return bool(record.get("address_match")) or record.get("structural_tier") in STRUCTURAL_TIERS


def _cbc_material_variants(passwd, salt, variants):
    """Every (legacy + PBKDF2) x cipher x key_len hypothesis in `variants`,
    generalized across all cipher classes those entries cover (not just
    AES) -- the same coverage `aes_try_open_bytes` provides, re-derived
    here so plaintext bodies stay visible to `classify_plaintext`
    regardless of printability."""
    for kdf_kind, kdf_param, cipher, key_len in (_normalize_variant(v) for v in variants):
        block = CIPHER_BLOCK_SIZES[cipher]
        derived_len = key_len + block
        if kdf_kind == "legacy":
            material, _ = evp_bytes_to_key(passwd, salt, kdf_param, derived_len, 0)
        else:
            digest_name, iterations = kdf_param
            material, _ = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, derived_len, 0)
        key = material[:key_len]
        iv = material[key_len:key_len + block]
        label = f"{kdf_kind}-{kdf_param}-{cipher}{key_len * 8}"
        yield label, cipher, block, key, iv


def test_material_cbc(passwd, blob_key="P32TRAILING", variants=None, blob=None,
                       target_addresses=DEFAULT_TARGET_ADDRESSES):
    """CBC pass over `variants` (default: KDF_VARIANTS+EXTENDED_CIPHER_VARIANTS)
    across every cipher class those lists name, classifying every valid-pad
    body (not gated by printability), never returning raw plaintext.
    Stops at the first terminal/structural hit -- does not keep sweeping
    remaining variants once one is found. `passwd` is the material bytes
    actually fed to the KDF (either the SHA-256 hex digest bytes, or the
    raw preimage). `blob`, if given, overrides the `BLOBS[blob_key]`
    lookup (used by self-test fixtures)."""
    if variants is None:
        variants = list(KDF_VARIANTS) + list(EXTENDED_CIPHER_VARIANTS)
    salt, ciphertext = blob if blob is not None else BLOBS[blob_key]
    records = []
    for label, cipher, block, key, iv in _cbc_material_variants(passwd, salt, variants):
        if not ciphertext or len(ciphertext) % block != 0:
            continue
        decryptor = Cipher(CIPHER_CLASSES[cipher](key), modes.CBC(iv)).decryptor()
        try:
            padded = decryptor.update(ciphertext) + decryptor.finalize()
        except Exception:
            continue
        pad = padded[-1]
        if not (1 <= pad <= block and padded[-pad:] == bytes([pad]) * pad):
            continue
        body = padded[:-pad]
        if not body:
            continue
        padding_tier = "full_block" if is_structural_binary_plaintext(cipher, block, pad, body) else "ordinary_valid"
        classification = classify_plaintext(body, padding_tier=padding_tier, target_addresses=target_addresses)
        record = {"kdf_label": label, "padding_tier": padding_tier, **classification}
        records.append(record)
        del body, padded  # never retained past this iteration
        if _is_hit(record):
            break
    return records


def test_material_ecb(passwd, blob_key="P32TRAILING", blob=None, variants=None,
                       target_addresses=DEFAULT_TARGET_ADDRESSES):
    """Re-implementation of `aes_try_open_ecb_bytes`'s exact variant space
    and crypto (`ECB_CIPHER_VARIANTS`, unmodified -- `variants` overrides
    only for self-test injection, never in production use), classifying
    every valid-pad body directly instead of going through that
    function's own printability gate -- which, on a "weak" (5 <= z < 8)
    decrypt, calls `cb_common._log_candidate()` and appends the raw
    password material plus a 200-byte plaintext preview to
    `weak_candidates_log.txt`. No such logging happens here. Stops at
    the first hit, same as `test_material_cbc`."""
    if variants is None:
        variants = ECB_CIPHER_VARIANTS
    salt, ciphertext = blob if blob is not None else BLOBS[blob_key]
    records = []
    if not ciphertext or len(ciphertext) % 16:
        return records
    for kdf_kind, kdf_param, key_len in variants:
        if kdf_kind == "legacy":
            key, _ = evp_bytes_to_key(passwd, salt, kdf_param, key_len, 0)
        else:
            digest_name, iterations = kdf_param
            key, _ = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, 0)
        decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
        try:
            padded = decryptor.update(ciphertext) + decryptor.finalize()
        except Exception:
            continue
        pad = padded[-1]
        if not (1 <= pad <= 16 and padded[-pad:] == bytes([pad]) * pad):
            continue
        body = padded[:-pad]
        if not body:
            continue
        padding_tier = "full_block" if is_structural_binary_plaintext("aes", 16, pad, body) else "ordinary_valid"
        label = f"{_kdf_label(kdf_kind, kdf_param, 'aes')}+ecb"
        record = {
            "kdf_label": label, "padding_tier": padding_tier,
            **classify_plaintext(body, padding_tier=padding_tier, target_addresses=target_addresses),
        }
        records.append(record)
        del body, padded
        if _is_hit(record):
            break
    return records


def test_material_stream(passwd, blob_key="P32TRAILING", blob=None, variants=None,
                          target_addresses=DEFAULT_TARGET_ADDRESSES):
    """Re-implementation of `aes_try_open_stream_bytes`'s exact variant
    space and crypto (`STREAM_CIPHER_VARIANTS`, unmodified -- `variants`
    overrides only for self-test injection, never in production use) --
    same no-logging rationale as `test_material_ecb`. CFB/OFB/CTR have no
    padding to validate, so every decrypt is classified regardless of
    tier. Stops at the first hit, same as `test_material_cbc`."""
    if variants is None:
        variants = STREAM_CIPHER_VARIANTS
    salt, ciphertext = blob if blob is not None else BLOBS[blob_key]
    records = []
    if not ciphertext:
        return records
    for kdf_kind, kdf_param, key_len, stream_mode in variants:
        block = 16
        mode_class = STREAM_MODE_CLASSES[stream_mode]
        if kdf_kind == "legacy":
            key, iv = evp_bytes_to_key(passwd, salt, kdf_param, key_len, block)
        else:
            digest_name, iterations = kdf_param
            key, iv = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, block)
        decryptor = Cipher(algorithms.AES(key), mode_class(iv)).decryptor()
        try:
            body = decryptor.update(ciphertext) + decryptor.finalize()
        except Exception:
            continue
        if not body:
            continue
        label = f"{_kdf_label(kdf_kind, kdf_param, 'aes')}+{stream_mode}"
        record = {"kdf_label": label, **classify_plaintext(body, target_addresses=target_addresses)}
        records.append(record)
        del body
        if _is_hit(record):
            break
    return records


def test_material_secondary_families(passwd, blob_key="P32TRAILING", blob=None,
                                      target_addresses=DEFAULT_TARGET_ADDRESSES):
    """ECB + stream (re-implemented locally, no logging side effect) +
    Key-Wrap (reused as-is). Stops calling the next family at all once an
    earlier one already hit within this same call -- an ECB hit means
    stream and Key-Wrap are never invoked here, not merely uncounted.

    Key-Wrap's own underlying `aes_keywrap_try_open_bytes()` is a
    black-box function with no incremental/early-exit interface -- it
    always completes its full internal variant sweep before returning
    (unlike the ECB/stream re-implementations above, which this module
    controls directly). Its variant space is small (~12 KDF/key-length
    combinations) and it has no logging side effect to avoid, so that
    internal sweep is an accepted, documented exception to "stop at the
    first hit": this function still only ever APPENDS records up to and
    including the first keywrap hit, never reporting (or relying on)
    anything found after it, even though the underlying unwrap attempts
    for later variants did already run by the time control returns
    here."""
    salt, ciphertext = blob if blob is not None else BLOBS[blob_key]
    records = [{"family": "ecb", **r} for r in test_material_ecb(passwd, blob_key, blob=(salt, ciphertext), target_addresses=target_addresses)]
    if any(_is_hit(r) for r in records):
        return records

    records += [{"family": "stream", **r} for r in test_material_stream(passwd, blob_key, blob=(salt, ciphertext), target_addresses=target_addresses)]
    if any(_is_hit(r) for r in records):
        return records

    blobs = {blob_key: (salt, ciphertext)}
    for tag, wrap_kind, kdf_label, _key_len, unwrapped in aes_keywrap_try_open_bytes(passwd, blobs=blobs):
        classification = classify_plaintext(unwrapped, target_addresses=target_addresses)
        if classification["structural_tier"] is None:
            # A clean unwrap is already a strong integrity signal on its own
            # (~2**-64 false-accept) -- but only "structural", not terminal,
            # unless the address check above already matched.
            classification["structural_tier"] = "keywrap_integrity"
        record = {"family": "keywrap", "kdf_label": f"{kdf_label}+{wrap_kind}", **classification}
        records.append(record)
        del unwrapped
        if _is_hit(record):
            break

    return records


def _finalize(material_digest, records):
    terminal = [r for r in records if r.get("address_match")]
    structural = [r for r in records if not r.get("address_match") and r.get("structural_tier") in STRUCTURAL_TIERS]
    if terminal:
        outcome = "terminal_hit"
    elif structural:
        outcome = "structural_hit"
    else:
        outcome = "negative"
    return {"material_sha256": material_digest, "outcome": outcome, "records": records}


def test_candidate(preimage_bytes, blob_key="P32TRAILING", blob=None,
                    target_addresses=DEFAULT_TARGET_ADDRESSES):
    """Full frozen testing protocol for one promoted candidate, in the
    frozen order H-exact -> H-remaining-broad -> P-broad, stopping at the
    first hit (terminal or structural). Returns a fully redacted record --
    safe to store/print/commit."""
    material_digest = hashlib.sha256(preimage_bytes).hexdigest()
    hex_material = material_digest.encode("ascii")
    all_variants = list(KDF_VARIANTS) + list(EXTENDED_CIPHER_VARIANTS)
    remaining_variants = [
        v for v in all_variants
        if _normalize_variant(v) != _normalize_variant(PHASE410_EXACT_VARIANT)
    ]

    records = []

    def _extend(step, material_form, new_records):
        for r in new_records:
            records.append({"step": step, "material_form": material_form, **r})
        return any(_is_hit(r) for r in new_records)

    exact = test_material_cbc(hex_material, blob_key, variants=[PHASE410_EXACT_VARIANT], blob=blob, target_addresses=target_addresses)
    if _extend("phase410_exact", "sha256_hexdigest", exact):
        return _finalize(material_digest, records)

    remaining_cbc = test_material_cbc(hex_material, blob_key, variants=remaining_variants, blob=blob, target_addresses=target_addresses)
    if _extend("broad_H", "sha256_hexdigest", remaining_cbc):
        return _finalize(material_digest, records)
    secondary_h = test_material_secondary_families(hex_material, blob_key, blob=blob, target_addresses=target_addresses)
    if _extend("broad_H", "sha256_hexdigest", secondary_h):
        return _finalize(material_digest, records)

    cbc_p = test_material_cbc(preimage_bytes, blob_key, variants=all_variants, blob=blob, target_addresses=target_addresses)
    if _extend("broad_P", "raw_preimage", cbc_p):
        return _finalize(material_digest, records)
    secondary_p = test_material_secondary_families(preimage_bytes, blob_key, blob=blob, target_addresses=target_addresses)
    _extend("broad_P", "raw_preimage", secondary_p)

    return _finalize(material_digest, records)


def _promotion_sort_key(item):
    """Deterministic testing order, using solver ranks: best (lowest =
    most confident) rank any contributing submission gave the candidate,
    ascending; ties broken by vote count descending (more convergence
    first); final tie-break on the hex string itself so the order is
    fully determined regardless of dict/insertion order."""
    hex_value, promotion = item
    return (min(promotion["ranks"]), -promotion["votes"], hex_value)


def test_candidates(promoted, blob_key="P32TRAILING"):
    """Batch-tests every promoted candidate in the frozen deterministic
    order (see `_promotion_sort_key`), stopping the whole batch (not just
    the current candidate) at the first terminal or structural hit --
    both interpretation branches call for a pause, not continued
    grinding."""
    results = {}
    for hex_value, promotion in sorted(promoted.items(), key=_promotion_sort_key):
        material = bytes.fromhex(hex_value)
        result = test_candidate(material, blob_key)
        results[hex_value] = {**promotion, **result}
        if result["outcome"] in ("terminal_hit", "structural_hit"):
            break
    return results


# ── Self-test ─────────────────────────────────────────────────────────────

def _make_cbc_blob(password_material, plaintext_body, digest="sha256", key_len=32):
    salt = os.urandom(8)
    key, iv = evp_bytes_to_key(password_material, salt, digest, key_len, 16)
    pad = 16 - (len(plaintext_body) % 16)
    padded = plaintext_body + bytes([pad]) * pad
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return salt, encryptor.update(padded) + encryptor.finalize()


def _make_ecb_blob(password_material, plaintext_body, digest, key_len):
    salt = os.urandom(8)
    key, _ = evp_bytes_to_key(password_material, salt, digest, key_len, 0)
    pad = 16 - (len(plaintext_body) % 16)
    padded = plaintext_body + bytes([pad]) * pad
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return salt, encryptor.update(padded) + encryptor.finalize()


def _make_stream_blob(password_material, plaintext_body, digest, key_len, stream_mode):
    salt = os.urandom(8)
    key, iv = evp_bytes_to_key(password_material, salt, digest, key_len, 16)
    encryptor = Cipher(algorithms.AES(key), STREAM_MODE_CLASSES[stream_mode](iv)).encryptor()
    return salt, encryptor.update(plaintext_body) + encryptor.finalize()


def _weak_tier_body(max_len=400):
    """A printable-ASCII body whose z-score lands in the WEAK band
    (PRINTABLE_Z_WEAK_THRESHOLD <= z < PRINTABLE_Z_STRONG_THRESHOLD) --
    long enough to be "surprising" but not enough to be a STRONG hit.
    z grows with length for constant-printable-ratio content, so this
    just walks length upward until it lands in the band."""
    for n in range(1, max_len):
        body = bytes((65 + (i % 26)) for i in range(n))
        z = printable_z_score(body)
        if PRINTABLE_Z_WEAK_THRESHOLD <= z < PRINTABLE_Z_STRONG_THRESHOLD:
            return body
    raise AssertionError("could not construct a weak-tier body for the leak-check fixture")


def _well_formed_submission(tool_used, reasoning_text, candidate_specs):
    """candidate_specs: list of (display, derivation, rank, closure_or_None).
    Builds a schema-conformant submission dict for self-test fixtures."""
    candidates = []
    for display, derivation, rank, closure in candidate_specs:
        candidate = {
            "display": display,
            "preimage_utf8_hex": display.encode("utf-8").hex(),
            "derivation": derivation,
            "rank": rank,
        }
        if closure is not None:
            candidate["closure"] = closure
        candidates.append(candidate)
    return {"tool_used": tool_used, "reasoning_text": reasoning_text, "candidates": candidates}


def _records(*submissions):
    """Wraps bare submission dicts into the invocation-ID-keyed dict shape
    `eligible_submissions()`/`evaluate_panel()` require, using fresh
    sequential integer IDs -- fine for self-test fixtures, where each
    positional argument represents one genuinely distinct invocation."""
    return {index: submission for index, submission in enumerate(submissions)}


def self_test():
    import unittest.mock as _mock
    module = sys.modules[__name__]

    packet_text, digest = build_evidence_packet()
    assert len(packet_text) > 0
    assert digest == EVIDENCE_PACKET_SHA256, (
        f"evidence packet changed: expected {EVIDENCE_PACKET_SHA256}, got {digest} "
        "-- if this is an intentional packet change, re-pin the doc/evidence file "
        "and this constant together, and treat any already-spawned solvers as void"
    )

    # Packet-file equality must be checked byte-for-byte (not via text-mode
    # read, which silently normalizes \r\n -> \n and would mask a real
    # mismatch) -- and the file must actually exist, not be silently skipped.
    packet_path = SCRIPT_DIR.parents[1] / "doc" / "evidence" / "GSMG_PHASE414_P32TRAILING_EVIDENCE_PACKET.txt"
    assert packet_path.exists(), f"pinned evidence packet file is missing at {packet_path}"
    assert packet_path.read_bytes() == packet_text.encode("utf-8"), (
        "on-disk evidence packet no longer matches build_evidence_packet()"
    )

    # ── Strict schema: wholesale rejection, no per-candidate salvage ──
    good = _well_formed_submission(False, "plain reasoning", [("hello world", "concatenated two packet tokens", 1, None)])
    assert validate_submission_schema(good)[0], "a well-formed submission must validate"
    good_hex = good["candidates"][0]["preimage_utf8_hex"]

    too_many = _well_formed_submission(False, "ok", [(f"c{i}", "d", i + 1, None) for i in range(11)])
    assert not validate_submission_schema(too_many)[0], "11 raw candidates must be rejected wholesale, even before dedup"

    dup_ranks = _well_formed_submission(False, "ok", [("a", "d", 1, None), ("b", "d", 1, None)])
    assert not validate_submission_schema(dup_ranks)[0], "duplicate ranks must be rejected wholesale"

    gap_ranks = _well_formed_submission(False, "ok", [("a", "d", 1, None), ("b", "d", 3, None)])
    assert not validate_submission_schema(gap_ranks)[0], "non-contiguous ranks must be rejected wholesale"

    dup_preimage = _well_formed_submission(False, "ok", [("same", "d1", 1, None), ("same", "d2", 2, None)])
    assert not validate_submission_schema(dup_preimage)[0], (
        "a duplicate preimage within one submission must be rejected wholesale, not silently collapsed to one vote"
    )

    unrecognized_top_level = {**good, "notes": "DBBI"}
    assert not validate_submission_schema(unrecognized_top_level)[0], "an unrecognized top-level field must be rejected wholesale"

    missing_tool_used = {k: v for k, v in good.items() if k != "tool_used"}
    assert not validate_submission_schema(missing_tool_used)[0], "a missing tool_used must be rejected, never defaulted to False"

    uppercase_hex = {**good, "candidates": [{**good["candidates"][0], "preimage_utf8_hex": good["candidates"][0]["preimage_utf8_hex"].upper()}]}
    assert not validate_submission_schema(uppercase_hex)[0], "uppercase hex must be rejected, never silently lowercased"

    unrecognized_candidate_field = {**good, "candidates": [{**good["candidates"][0], "notes": "DBBI"}]}
    assert not validate_submission_schema(unrecognized_candidate_field)[0], "an unrecognized candidate field must be rejected wholesale"

    bad_roundtrip = {**good, "candidates": [{**good["candidates"][0], "display": "hello"}]}
    assert not validate_submission_schema(bad_roundtrip)[0], "a display/hex round-trip mismatch must be rejected"

    missing_derivation = {**good, "candidates": [{**good["candidates"][0], "derivation": ""}]}
    assert not validate_submission_schema(missing_derivation)[0], "an empty derivation must be rejected"

    # ── Full-submission recursive leakage scan (not just reasoning_text, and
    # not limited to a hardcoded field list) ──
    leaking_in_derivation = _well_formed_submission(
        False, "plain reasoning", [("hello world", "this follows from Phase 410's established profile", 1, None)],
    )
    assert not eligible_submissions(_records(leaking_in_derivation)), (
        "leakage inside a candidate's own derivation text must exclude the submission"
    )

    # ── Eligibility / convergence promotion ──
    submissions = _records(
        _well_formed_submission(False, "plain reasoning", [("hello world", "concatenated two packet tokens", 1, None)]),
        _well_formed_submission(False, "plain reasoning", [("hello world", "concatenated two packet tokens", 1, None)]),
        _well_formed_submission(True, "used web search", [("hello world", "concatenated two packet tokens", 1, None)]),
        _well_formed_submission(False, "mentions DBBI leakage", [("hello world", "concatenated two packet tokens", 1, None)]),
        _well_formed_submission(False, "cites Phase 410 leakage", [("hello world", "concatenated two packet tokens", 1, None)]),
    )
    elig = eligible_submissions(submissions)
    assert len(elig) == 2, f"expected exactly 2 eligible submissions, got {len(elig)}"
    promoted = promote_candidates(elig, packet_text)
    assert good_hex in promoted and promoted[good_hex]["path"] == "convergence"
    assert promoted[good_hex]["ranks"] == [1, 1]

    unique = _well_formed_submission(False, "ok", [("only one", "a guess", 1, None)])
    elig2 = eligible_submissions(_records(unique))
    promoted2 = promote_candidates(elig2, packet_text)
    assert not promoted2, "single unclosed candidate must not be promoted"

    # ── Invocation identity: replaying the SAME invocation ID must never
    # inflate votes, even with the same content submitted repeatedly under
    # that one ID; two genuinely DIFFERENT IDs converging on identical
    # content must still count as real convergence. ──
    lone_submission = _well_formed_submission(False, "ok", [("replay probe", "d", 1, None)])
    replay_hex = lone_submission["candidates"][0]["preimage_utf8_hex"]
    replayed_records = {0: lone_submission}
    for _ in range(5):
        replayed_records[0] = lone_submission  # re-assigning the SAME key -- never adds a second entry
    assert len(replayed_records) == 1
    replay_panel = evaluate_panel(replayed_records, 5)
    assert replay_panel["status"] == "need_more", (
        "one invocation ID replayed under itself must count as exactly one eligible submission, "
        "never five, and must not reach panel_ready"
    )
    promoted_replay = promote_candidates(eligible_submissions(replayed_records), packet_text)
    assert not promoted_replay, "a single invocation ID can never produce a 2-vote convergence by itself"

    genuinely_two_ids = {0: lone_submission, 1: lone_submission}  # two DIFFERENT ids, same content
    promoted_two_ids = promote_candidates(eligible_submissions(genuinely_two_ids), packet_text)
    assert promoted_two_ids.get(replay_hex, {}).get("path") == "convergence", (
        "two distinct invocation IDs converging on identical content is real convergence, "
        "not the replay bug -- dedup is by ID, never by content"
    )

    # ── Closure validation: preregistered-allowlist gate + mechanical offset
    # verification. Byte-offset math alone can prove text exists and that
    # spans reconstruct a candidate -- it cannot prove that text INSTRUCTS
    # selection with zero alternatives, so a perfectly self-consistent
    # closure must still fail unless its span is pre-approved. ──
    real_start = packet_text.index(PRIZE_ADDRESS)
    real_end = real_start + len(PRIZE_ADDRESS)
    real_closure = {
        "instruction_offset_start": real_start, "instruction_offset_end": real_end,
        "instruction_quote": PRIZE_ADDRESS,
        "token_spans": [[real_start, real_end]],
        "zero_alternatives": True,
    }
    assert not validate_closure(real_closure, packet_text, PRIZE_ADDRESS.encode("utf-8")), (
        "a closure must fail when its span is not on the preregistered (currently empty) allowlist, "
        "even when its offsets and reconstruction are perfectly self-consistent -- the prize address "
        "itself is not an instruction, and no other span is preapproved either"
    )
    with _mock.patch.object(module, "QUALIFYING_CLOSURE_INSTRUCTION_SPANS", ((real_start, real_end),)):
        assert validate_closure(real_closure, packet_text, PRIZE_ADDRESS.encode("utf-8")), (
            "an allowlisted span with consistent offsets and reconstruction must validate -- proving the "
            "mechanical checks underneath the allowlist gate still work"
        )
        fabricated_quote = {**real_closure, "instruction_quote": "this text was never in the packet"}
        assert not validate_closure(fabricated_quote, packet_text, PRIZE_ADDRESS.encode("utf-8")), (
            "a fabricated instruction quote must be rejected even on an allowlisted span"
        )
        mismatched_reconstruction = {**real_closure, "token_spans": [[real_start, real_end - 1]]}
        assert not validate_closure(mismatched_reconstruction, packet_text, PRIZE_ADDRESS.encode("utf-8")), (
            "a closure whose reconstructed bytes don't match the candidate must be rejected"
        )
    closed_submission = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "quoted directly from item 4", 1, real_closure)])
    elig3 = eligible_submissions(_records(closed_submission))
    promoted3 = promote_candidates(elig3, packet_text)
    assert not promoted3, "closure promotion must be impossible under the frozen (empty) allowlist for this phase"

    # ── Closure schema type-safety: adversarial/malformed shapes must be
    # rejected by validate_submission_schema() itself (not merely survive
    # to crash validate_closure() later). ──
    bool_offset_closure = {**real_closure, "instruction_offset_start": True}
    bad_offset_type = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, bool_offset_closure)])
    assert not validate_submission_schema(bad_offset_type)[0], "a boolean offset (bool is an int subclass) must be rejected"

    dict_offset_closure = {**real_closure, "instruction_offset_start": {"not": "an int"}}
    bad_offset_dict = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, dict_offset_closure)])
    assert not validate_submission_schema(bad_offset_dict)[0], "a dict offset must be rejected"

    null_span_closure = {**real_closure, "token_spans": [None]}
    bad_span_null = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, null_span_closure)])
    assert not validate_submission_schema(bad_span_null)[0], "token_spans: [null] must be rejected wholesale"
    # Even if it somehow reached validate_closure() directly, it must not crash.
    assert validate_closure(null_span_closure, packet_text, PRIZE_ADDRESS.encode("utf-8")) is False

    list_span_closure = {**real_closure, "token_spans": [[real_start, "not an int"]]}
    bad_span_type = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, list_span_closure)])
    assert not validate_submission_schema(bad_span_type)[0], "a non-integer span element must be rejected"

    negative_offset_closure = {
        **real_closure, "instruction_offset_start": -5, "instruction_offset_end": 10,
        "token_spans": [[-5, 10]],
    }
    bad_negative_offset = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, negative_offset_closure)])
    assert not validate_submission_schema(bad_negative_offset)[0], "a negative offset must be rejected"
    assert validate_closure(negative_offset_closure, packet_text, PRIZE_ADDRESS.encode("utf-8")) is False

    negative_span_closure = {**real_closure, "token_spans": [[-1, real_end]]}
    bad_negative_span = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, negative_span_closure)])
    assert not validate_submission_schema(bad_negative_span)[0], "a negative span start must be rejected"

    empty_quote_closure = {**real_closure, "instruction_quote": ""}
    bad_empty_quote = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, empty_quote_closure)])
    assert not validate_submission_schema(bad_empty_quote)[0], "an empty instruction_quote must be rejected"
    assert validate_closure(empty_quote_closure, packet_text, PRIZE_ADDRESS.encode("utf-8")) is False

    false_zero_alternatives_closure = {**real_closure, "zero_alternatives": False}
    bad_false_zero_alt = _well_formed_submission(False, "ok", [(PRIZE_ADDRESS, "d", 1, false_zero_alternatives_closure)])
    assert not validate_submission_schema(bad_false_zero_alt)[0], (
        "zero_alternatives: false is a self-contradictory closure (the object's whole point is "
        "claiming zero alternatives) and must be rejected, not merely deprioritized at promotion time"
    )
    assert validate_closure(false_zero_alternatives_closure, packet_text, PRIZE_ADDRESS.encode("utf-8")) is False

    violations = blinding_violations("this references Phase 410 and DBBI directly")
    assert "phase 410" in violations and "DBBI" in violations
    assert not blinding_violations("this references Phase 2 and Phase 3.2 only")

    # ── Panel validity ──
    five_eligible = _records(*[_well_formed_submission(False, "ok", [(f"guess {i}", "x", 1, None)]) for i in range(5)])
    assert evaluate_panel(five_eligible, 5)["status"] == "panel_ready"
    two_eligible = {k: five_eligible[k] for k in list(five_eligible)[:2]}
    assert evaluate_panel(two_eligible, 3)["status"] == "need_more"
    assert evaluate_panel(two_eligible, INVOCATION_CAP)["status"] == "protocol_invalid"

    # An over-cap ledger must never reach panel_ready, even with 5 eligible
    # records already in hand -- it is a bug in the calling orchestration
    # loop, not a phase result, so it must raise rather than silently
    # reporting success.
    try:
        evaluate_panel(five_eligible, INVOCATION_CAP + 1)
    except ValueError:
        pass
    else:
        raise AssertionError("evaluate_panel() must raise when invocations_used exceeds the frozen cap")

    # ── Deterministic candidate ordering, using solver ranks (not dict/
    # insertion order). "zzzlow" is ranked most-confident (1) by two
    # submissions; "aaahigh" is ranked least-confident (3 of 3) by two
    # submissions. Hex-fallback order alone would put aaahigh first
    # (lexicographically smaller) -- the frozen order must put zzzlow
    # first instead, because rank is checked before the hex tie-break. ──
    zzzlow_hex = "zzzlow".encode("utf-8").hex()
    aaahigh_hex = "aaahigh".encode("utf-8").hex()
    assert aaahigh_hex < zzzlow_hex, "sanity check: hex-only ordering would put aaahigh first"
    ordering_submissions = _records(
        _well_formed_submission(False, "ok", [("zzzlow", "d", 1, None)]),
        _well_formed_submission(False, "ok", [("zzzlow", "d", 1, None)]),
        _well_formed_submission(False, "ok", [("padA", "d", 1, None), ("padB", "d", 2, None), ("aaahigh", "d", 3, None)]),
        _well_formed_submission(False, "ok", [("padC", "d", 1, None), ("padD", "d", 2, None), ("aaahigh", "d", 3, None)]),
    )
    elig_order = eligible_submissions(ordering_submissions)
    promoted_order = promote_candidates(elig_order, packet_text)
    assert promoted_order[zzzlow_hex]["ranks"] == [1, 1]
    assert promoted_order[aaahigh_hex]["ranks"] == [3, 3]
    ordered_hexes = [h for h, _ in sorted(promoted_order.items(), key=_promotion_sort_key)]
    assert ordered_hexes.index(zzzlow_hex) < ordered_hexes.index(aaahigh_hex), (
        "the best-rank candidate must be ordered before a lower-confidence one, overriding hex fallback order"
    )

    # ── ECB/stream re-implementations must never write to
    # weak_candidates_log.txt (the reused black-box oracles do, for any
    # 5 <= z < 8 decrypt, including the raw password material and a
    # plaintext preview) ──
    weak_body = _weak_tier_body()
    weak_z = printable_z_score(weak_body)
    assert PRINTABLE_Z_WEAK_THRESHOLD <= weak_z < PRINTABLE_Z_STRONG_THRESHOLD
    fixture_preimage_weak = b"phase414-fixture-weak-tier-no-log"
    hex_weak = hashlib.sha256(fixture_preimage_weak).hexdigest().encode("ascii")
    ecb_kdf_kind, ecb_kdf_param, ecb_key_len = ECB_CIPHER_VARIANTS[0]
    stream_kdf_kind, stream_kdf_param, stream_key_len, stream_mode = STREAM_CIPHER_VARIANTS[0]
    ecb_digest = ecb_kdf_param if ecb_kdf_kind == "legacy" else "sha256"
    stream_digest = stream_kdf_param if stream_kdf_kind == "legacy" else "sha256"
    salt_ecb, ct_ecb = _make_ecb_blob(hex_weak, weak_body, ecb_digest, ecb_key_len)
    salt_stream, ct_stream = _make_stream_blob(hex_weak, weak_body, stream_digest, stream_key_len, stream_mode)
    log_before = WEAK_CANDIDATE_LOG.read_bytes() if WEAK_CANDIDATE_LOG.exists() else None
    test_material_ecb(hex_weak, blob=(salt_ecb, ct_ecb))
    test_material_stream(hex_weak, blob=(salt_stream, ct_stream))
    log_after = WEAK_CANDIDATE_LOG.read_bytes() if WEAK_CANDIDATE_LOG.exists() else None
    assert log_before == log_after, (
        "test_material_ecb()/test_material_stream() must never write to weak_candidates_log.txt "
        "(the reused black-box oracles do, leaking password material and a plaintext preview)"
    )

    # ── parse_submission(): mechanical extraction only, never semantic
    # reinterpretation. ──
    assert parse_submission(json.dumps(good)) == good, "direct JSON must parse"
    bare_fence = "```json\n" + json.dumps(good) + "\n```"
    assert parse_submission(bare_fence) == good, "a fence wrapping ONLY the JSON must be unwrapped and parsed"
    fence_with_leading_prose = "Here is my answer:\n```json\n" + json.dumps(good) + "\n```"
    assert parse_submission(fence_with_leading_prose) is None, (
        "a fence preceded by prose must be rejected, not have the prose silently stripped away"
    )
    fence_with_trailing_prose = "```json\n" + json.dumps(good) + "\n```\nThanks."
    assert parse_submission(fence_with_trailing_prose) is None, (
        "a fence followed by prose must be rejected, not have the prose silently stripped away"
    )
    assert parse_submission("this is not JSON at all") is None, "unparseable prose must yield None, never a guess"
    assert parse_submission("") is None
    assert parse_submission(None) is None

    # Duplicate JSON keys must be rejected outright, not silently resolved
    # by whichever value json.loads() would otherwise keep (the last one) --
    # at any nesting level, since object_pairs_hook fires for every {...}.
    duplicate_top_level = '{"tool_used":true,"tool_used":false,"reasoning_text":"x","candidates":[]}'
    assert parse_submission(duplicate_top_level) is None, (
        "a duplicate top-level key must make the whole response unparseable, "
        "never silently resolve to whichever value json.loads() would have kept"
    )
    duplicate_nested = (
        '{"tool_used":false,"reasoning_text":"x","candidates":'
        '[{"display":"a","display":"b","preimage_utf8_hex":"61","derivation":"d","rank":1}]}'
    )
    assert parse_submission(duplicate_nested) is None, "a duplicate key nested inside a candidate must also be rejected"

    # ── Immediate stop WITHIN a single family's own variant loop, not just
    # between broad-pass steps. Each poison entry is a variant that would
    # raise (KeyError / ValueError) if this module's own loop ever reached
    # it -- constructed to sit right after a guaranteed hit in the variant
    # list, so an unhandled exception here means the "stop at first hit"
    # loop kept going past it. ──
    fixture_preimage_midloop = b"phase414-fixture-mid-loop-stop"
    hex_midloop = hashlib.sha256(fixture_preimage_midloop).hexdigest().encode("ascii")

    salt_cbc_mid, ct_cbc_mid = _make_cbc_blob(hex_midloop, bytes(64))  # full_block hit under PHASE410_EXACT_VARIANT
    cbc_poison_variants = [PHASE410_EXACT_VARIANT, ("legacy", "sha256", "not-a-real-cipher", 32)]
    cbc_mid_result = test_material_cbc(hex_midloop, variants=cbc_poison_variants, blob=(salt_cbc_mid, ct_cbc_mid))
    assert len(cbc_mid_result) == 1 and cbc_mid_result[0]["structural_tier"] == "full_block", (
        "test_material_cbc must stop at the first hit within its own variant loop -- reaching the "
        "poison variant afterward would have raised KeyError on 'not-a-real-cipher'"
    )

    ecb_hit_variant = ECB_CIPHER_VARIANTS[0]
    ecb_digest_mid = ecb_hit_variant[1] if ecb_hit_variant[0] == "legacy" else "sha256"
    salt_ecb_mid, ct_ecb_mid = _make_ecb_blob(hex_midloop, bytes(64), ecb_digest_mid, ecb_hit_variant[2])
    ecb_poison_variants = [ecb_hit_variant, ("bogus_kind", "sha256", 32)]
    ecb_mid_result = test_material_ecb(hex_midloop, blob=(salt_ecb_mid, ct_ecb_mid), variants=ecb_poison_variants)
    assert len(ecb_mid_result) == 1 and ecb_mid_result[0]["structural_tier"] == "full_block", (
        "test_material_ecb must stop at the first hit -- the poison variant's kdf_kind would have "
        "raised ValueError trying to unpack a bare digest name as (digest_name, iterations)"
    )

    stream_hit_variant = STREAM_CIPHER_VARIANTS[0]
    stream_digest_mid = stream_hit_variant[1] if stream_hit_variant[0] == "legacy" else "sha256"
    strong_stream_body = b"THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG " * 4  # strong_text tier
    salt_stream_mid, ct_stream_mid = _make_stream_blob(
        hex_midloop, strong_stream_body, stream_digest_mid, stream_hit_variant[2], stream_hit_variant[3],
    )
    stream_poison_variants = [stream_hit_variant, ("bogus_kind", "sha256", 32, "cfb")]
    stream_mid_result = test_material_stream(hex_midloop, blob=(salt_stream_mid, ct_stream_mid), variants=stream_poison_variants)
    assert len(stream_mid_result) == 1 and stream_mid_result[0]["structural_tier"] == "strong_text", (
        "test_material_stream must stop at the first hit -- the poison variant would have raised "
        "ValueError the same way as the ECB case"
    )

    # ── Inter-family short-circuit: an ECB hit must prevent stream and
    # Key-Wrap from being invoked AT ALL (not merely "uncounted") --
    # reproduces the exact reported counterexample. ──
    salt_secondary, ct_secondary = _make_ecb_blob(hex_midloop, bytes(64), ecb_digest_mid, ecb_hit_variant[2])
    with _mock.patch.object(module, "test_material_stream") as stream_spy, \
         _mock.patch.object(module, "aes_keywrap_try_open_bytes") as keywrap_spy:
        secondary_result = module.test_material_secondary_families(hex_midloop, blob=(salt_secondary, ct_secondary))
    assert secondary_result and secondary_result[-1]["structural_tier"] == "full_block"
    stream_spy.assert_not_called()
    keywrap_spy.assert_not_called()

    # ── Planted terminal-address fixture. The real prize address's key is,
    # definitionally, unknown -- so this plants a synthetic target address
    # via `target_addresses` to prove the terminal_hit path actually fires
    # end-to-end, rather than only ever being exercised by structural
    # (non-address-matching) fixtures. ──
    planted_scalar = (424242).to_bytes(32, "big")
    planted_address = private_key_details(planted_scalar)["compressed"]["address"]
    fixture_preimage_terminal = b"phase414-fixture-terminal"
    hex_terminal = hashlib.sha256(fixture_preimage_terminal).hexdigest().encode("ascii")
    salt_terminal, ct_terminal = _make_cbc_blob(hex_terminal, planted_scalar, digest="sha1", key_len=16)
    result_terminal = test_candidate(
        fixture_preimage_terminal, blob=(salt_terminal, ct_terminal), target_addresses=(planted_address,),
    )
    assert result_terminal["outcome"] == "terminal_hit"
    assert any(r["address_match"] == planted_address for r in result_terminal["records"])

    # ── Structural classifier + full pipeline fixtures (real crypto, synthetic blobs) ──
    zero_scalar = classify_plaintext(bytes(32))
    assert zero_scalar["structural_tier"] is None, "raw scalar validity alone must not be a structural signal"

    probe_scalar = (12345).to_bytes(32, "big")
    classification = classify_plaintext(probe_scalar)
    assert classification["structural_tier"] is None
    assert classification["address_match"] is None

    # full_block: exact profile against H must hit at step 1 and stop immediately.
    fixture_preimage_a = b"phase414-fixture-full-block"
    hex_a = hashlib.sha256(fixture_preimage_a).hexdigest().encode("ascii")
    salt_a, ct_a = _make_cbc_blob(hex_a, bytes(64))
    result_a = test_candidate(fixture_preimage_a, blob=(salt_a, ct_a))
    assert result_a["outcome"] == "structural_hit"
    assert result_a["records"][0]["step"] == "phase410_exact"
    assert len(result_a["records"]) == 1, "must stop at the first hit, not keep sweeping"
    assert result_a["records"][0]["structural_tier"] == "full_block"

    # strong_text: printable English long enough for a strong z-score, via a
    # non-exact-profile variant so it is only found in the broad-H sweep.
    fixture_preimage_b = b"phase414-fixture-strong-text"
    hex_b = hashlib.sha256(fixture_preimage_b).hexdigest().encode("ascii")
    text_body = b"THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG " * 4
    salt_b, ct_b = _make_cbc_blob(hex_b, text_body, digest="md5")  # not the exact profile
    result_b = test_candidate(fixture_preimage_b, blob=(salt_b, ct_b))
    assert result_b["outcome"] == "structural_hit"
    assert any(r["structural_tier"] == "strong_text" for r in result_b["records"])
    assert all(r["step"] != "broad_P" for r in result_b["records"]), "must stop before reaching the raw-preimage sweep"

    # WIF shape (checksum-valid, not the real prize/halving address).
    wif_scalar = (98765).to_bytes(32, "big")
    wif_string = private_key_details(wif_scalar)["compressed"]["wif"]
    fixture_preimage_c = b"phase414-fixture-wif"
    hex_c = hashlib.sha256(fixture_preimage_c).hexdigest().encode("ascii")
    salt_c, ct_c = _make_cbc_blob(hex_c, wif_string.encode("ascii"), digest="sha1")
    result_c = test_candidate(fixture_preimage_c, blob=(salt_c, ct_c))
    assert result_c["outcome"] == "structural_hit"
    assert any(r["structural_tier"] == "valid_wif" for r in result_c["records"])
    assert all(r["address_match"] is None for r in result_c["records"])

    # hex64 shape. Wrapped in non-hex filler so the body's total length isn't
    # exactly 64 bytes -- a bare 64-hex-char body would also always trip the
    # full_block tier (any exact-64-byte plaintext does, regardless of
    # content), which would make this fixture ambiguous between the two
    # tiers instead of isolating hex64_shape.
    hex64_body = b"***" + wif_scalar.hex().encode("ascii") + b"###"
    fixture_preimage_d = b"phase414-fixture-hex64"
    hex_d = hashlib.sha256(fixture_preimage_d).hexdigest().encode("ascii")
    salt_d, ct_d = _make_cbc_blob(hex_d, hex64_body, digest="sha256", key_len=16)
    result_d = test_candidate(fixture_preimage_d, blob=(salt_d, ct_d))
    assert result_d["outcome"] == "structural_hit"
    assert any(r["structural_tier"] == "hex64_shape" for r in result_d["records"])

    # Key-Wrap integrity (structural, not terminal, absent an address match).
    fixture_preimage_e = b"phase414-fixture-keywrap"
    hex_e = hashlib.sha256(fixture_preimage_e).hexdigest().encode("ascii")
    salt_e = os.urandom(8)
    kek = derive_kek("legacy", "sha256", salt_e, hex_e, 32)
    wrapped = aes_key_wrap(kek, bytes(32))
    result_e = test_candidate(fixture_preimage_e, blob=(salt_e, wrapped))
    assert result_e["outcome"] == "structural_hit"
    assert any(r["structural_tier"] == "keywrap_integrity" for r in result_e["records"])
    assert all(r["address_match"] is None for r in result_e["records"])

    # A genuine negative: no hit anywhere, all three steps must still run to
    # completion. Random ciphertext could, by the ~1/255 valid-pad chance,
    # happen to produce zero records in every step regardless of whether
    # later steps actually ran -- so this checks call counts (via patching),
    # not record contents, to verify the frozen step order/no-early-stop
    # contract deterministically rather than depending on padding luck.
    fixture_preimage_f = b"phase414-fixture-negative"
    salt_f = os.urandom(8)
    ct_f = os.urandom(80)  # 80 bytes so the CBC sweep runs the same shape as the real blob
    with _mock.patch.object(module, "test_material_cbc", wraps=test_material_cbc) as cbc_spy, \
         _mock.patch.object(module, "test_material_secondary_families", wraps=test_material_secondary_families) as secondary_spy:
        result_f = module.test_candidate(fixture_preimage_f, blob=(salt_f, ct_f))
    assert result_f["outcome"] == "negative"
    assert cbc_spy.call_count == 3, f"expected 3 CBC sweeps (H-exact, H-remaining, P), got {cbc_spy.call_count}"
    assert secondary_spy.call_count == 2, f"expected 2 secondary-family sweeps (H, P), got {secondary_spy.call_count}"

    # Real end-to-end negative against the actual P32TRAILING blob.
    real_negative = test_candidate("causality".encode("utf-8"))
    assert real_negative["outcome"] == "negative"

    print(
        f"[*] self-test OK: evidence packet {len(packet_text)} chars, sha256 {digest}; "
        "strict-schema rejection, recursive leakage scan, allowlist-gated closure, "
        "panel-validity, rank-based ordering, no-weak-log-leak, planted-terminal, and "
        "full decrypt-pipeline fixtures (full_block/strong_text/valid_wif/hex64_shape/"
        "keywrap_integrity/negative) all pass"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-packet", metavar="PATH")
    args = parser.parse_args()
    if args.self_test or not args.write_packet:
        self_test()
    if args.write_packet:
        digest = write_evidence_packet(args.write_packet)
        print(f"[*] evidence packet written to {args.write_packet}, sha256 {digest}")


if __name__ == "__main__":
    main()
