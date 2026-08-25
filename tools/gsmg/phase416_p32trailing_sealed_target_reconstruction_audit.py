#!/usr/bin/env python3
"""Phase 416: sealed-target blinded reconstruction of P32TRAILING.

See ``doc/Brainstorms/2026-08-25 - Phase 416 P32TRAILING Sealed-Target
Blinded Reconstruction Pre-Registration.md`` for the frozen protocol this
module implements. Supersedes Phase 415
(``phase415_p32trailing_blinded_reconstruction_audit``), which closed
``protocol_invalid`` for two independent reasons:

1. A schema false positive: the `"..."` residue marker fired on ordinary
   ellipsis punctuation (including punctuation appearing literally in
   the evidence packet's own quoted plaintext), wholesale-rejecting two
   otherwise clean, non-tool-using submissions.
2. A prompt-only tool restriction is not an adequate safety boundary:
   invocation 4 disclosed running roughly 1,600 local candidate tests
   via Bash/OpenSSL directly against the REAL `P32TRAILING` ciphertext
   -- decoding its actual salt and running the full legacy-EVP/AES-256-
   CBC/PKCS7 pipeline outside this project's redaction wrapper. "Do not
   look up this puzzle" reads as an anti-lookup rule, not a prohibition
   on local self-testing against a target the prompt itself handed over.

Phase 416 corrects both, the second architecturally rather than by
prompt wording alone:

- `RESIDUE_MARKERS` drops `"..."` entirely; `placeholder`/`todo`/`fixme`
  remain.
- **The real ciphertext and the real prize address are never placed in
  the evidence packet or prompt text.** The packet's Item 1 replaces the
  final base64 ciphertext block with its position, format, length, and
  SHA-256 commitments of the real salt and ciphertext bytes; Item 4
  replaces the literal prize address with a SHA-256 commitment of the
  address string. Both real values remain available to the ORCHESTRATOR
  (this module, via `cb_common.BLOBS` and
  `first_hint_hash_audit.PRIZE_ADDRESS` imported normally) for redacted
  testing after promotion. This is **packet-level sealing**: a solver
  that only reads what it is given cannot decrypt, verify, or self-test
  against either target, because the prompt simply does not contain
  them. It is NOT filesystem or tool isolation -- a solver invoked with
  its own shell/file-read access, in an environment where this
  repository (and `BLOBS["P32TRAILING"]`/`PRIZE_ADDRESS` within it) is
  reachable, could in principle locate and read the real values directly,
  the same class of capability invocation 4 used against Phase 415's
  prompt-only restriction, just aimed at the filesystem instead of the
  prompt. This phase's actual invocation mechanism (the `Agent` tool,
  `subagent_type: "general-purpose"`, full tool access) does not provide
  that isolation; see "Threat model and residual exposure" in this
  phase's pre-registration for what is and is not defended against, and
  what mitigation is used instead (the `tool_used` mechanical exclusion,
  retained as defense in depth, catches a solver that discloses using
  any tool at all -- honestly or not -- but cannot stop a solver that
  uses a tool and lies about it). This is generator/evaluator
  separation: solvers propose hypotheses; only the orchestrator can run
  the experiment.
- The frozen prompt's tool prohibition is broadened from "do not look
  this puzzle up" to an explicit, blanket ban on ANY tool use for ANY
  purpose -- file access, shell commands, hashing, encryption or
  decryption, or any attempt to test a candidate -- stated as
  reinforcement of the sealed design, not as its only safeguard.
- The submission schema drops `closure` entirely (not merely leaves its
  allowlist empty, as Phase 414/415 did). This is a preregistered
  simplification of the promotion rule, not a claim that a closure
  argument is impossible under a sealed target -- an instruction can in
  principle uniquely determine a preimage without the solver ever
  touching the ciphertext, so closure-style reasoning is not logically
  ruled out here. It is dropped because this phase deliberately commits
  to convergence as its sole, simpler promotion discipline. Convergence
  (>=2 eligible submissions independently producing the byte-identical
  `preimage_utf8_hex`) is the sole promotion path.

Everything else -- calibration examples, the assembly recipe, the
invocation-identity/cap machinery, blinding checks, the redacted
oracle-testing pipeline and its stop-at-first-hit discipline, the
structural-tier classifier -- is reused unchanged, by direct import,
from ``phase414_p32trailing_blinded_reconstruction_audit``.

Invocation 4's actual transcript from Phase 415 is quarantined: nothing
from it is reproduced, referenced, or embedded in this module. Its
Phase-415 disposition (excluded via the frozen `tool_used` gate) is
recorded only in ``FINDINGS.md`` and the Phase 415 pre-registration's own
closure note, as aggregate metadata, never as content.
"""

import base64
import hashlib
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase414_p32trailing_blinded_reconstruction_audit as phase414  # noqa: E402
from cb_common import BLOBS  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402
from p32_sibling_password_audit import decrypt_phase32_bytes, extract_phase32_components  # noqa: E402

# ── Re-exported unchanged from Phase 414 (see this phase's preregistration's
#    "Deliverable" section for the full list of what is reused as-is) ───────

PHASE32_PLAINTEXT_SHA256 = phase414.PHASE32_PLAINTEXT_SHA256
MAX_SOLVER_CANDIDATES = phase414.MAX_SOLVER_CANDIDATES
FAMILY_PROMOTION_THRESHOLD = phase414.FAMILY_PROMOTION_THRESHOLD
INVOCATION_CAP = phase414.INVOCATION_CAP
PANEL_TARGET = phase414.PANEL_TARGET
PHASE410_EXACT_VARIANT = phase414.PHASE410_EXACT_VARIANT
FORBIDDEN_VOCAB = phase414.FORBIDDEN_VOCAB
FORBIDDEN_PHASE_RE = phase414.FORBIDDEN_PHASE_RE
ALLOWED_PHASE_NUMBERS = phase414.ALLOWED_PHASE_NUMBERS
GITHUB_URL_RE = phase414.GITHUB_URL_RE
STRUCTURAL_TIERS = phase414.STRUCTURAL_TIERS
DEFAULT_TARGET_ADDRESSES = phase414.DEFAULT_TARGET_ADDRESSES

_collect_strings = phase414._collect_strings
submission_full_text = phase414.submission_full_text
blinding_violations = phase414.blinding_violations
classify_plaintext = phase414.classify_plaintext
_is_hit = phase414._is_hit
test_material_cbc = phase414.test_material_cbc
test_material_ecb = phase414.test_material_ecb
test_material_stream = phase414.test_material_stream
test_material_secondary_families = phase414.test_material_secondary_families
test_candidate = phase414.test_candidate
_promotion_sort_key = phase414._promotion_sort_key
parse_submission = phase414.parse_submission
JSON_FENCE_RE = phase414.JSON_FENCE_RE
_reject_duplicate_keys = phase414._reject_duplicate_keys

# `promote_candidates`, `validate_closure`, and
# `QUALIFYING_CLOSURE_INSTRUCTION_SPANS` are intentionally NOT reused: Phase
# 416's schema accepts no `closure` field at all (see below), so that
# promotion path does not exist here. `promote_candidates()` below is
# Phase-416-local and convergence-only.


# ── Sealed-target commitments ────────────────────────────────────────────
#
# The real ciphertext and the real prize address are held here, imported
# normally, for the ORCHESTRATOR's own use -- they are never placed in the
# evidence packet solvers receive. Only their SHA-256 commitments (and, for
# the ciphertext, its length/shape) go into the packet.

SALT_LENGTH_BYTES = 8
CIPHERTEXT_LENGTH_BYTES = 80  # 5 AES-128-block-size (16-byte) blocks
SALT_COMMITMENT_SHA256 = "6a466725507fbd85afa11f4dedd438e6e7a2ee3079338ebe623f49a4b68546e2"
CIPHERTEXT_COMMITMENT_SHA256 = "cbbf945223b0c7a60e31b6ba7f5dfbc17f68f545bec059e937c11e7465d0117b"
ADDRESS_COMMITMENT_SHA256 = "951209e1cf5a1feff85eea755e16b3481c174a75f45ddbbb35b67b92b46bfde2"
SEALED_EVIDENCE_PACKET_SHA256 = "21786b66ebd6312622c581338fc124127a998d70974fb4c4eca34126546e62d5"

RESIDUE_MARKERS = ("placeholder", "todo", "fixme")


def _verify_commitments():
    """Never trust the pinned commitment constants blindly -- recompute
    from the actual current BLOBS/PRIZE_ADDRESS values every time the
    packet is built, so a change to either (or a stale pin) raises loudly
    instead of silently sealing the wrong target."""
    salt, ciphertext = BLOBS["P32TRAILING"]
    if len(salt) != SALT_LENGTH_BYTES:
        raise AssertionError("P32TRAILING salt length no longer matches the pinned shape")
    if len(ciphertext) != CIPHERTEXT_LENGTH_BYTES:
        raise AssertionError("P32TRAILING ciphertext length no longer matches the pinned shape")
    if hashlib.sha256(salt).hexdigest() != SALT_COMMITMENT_SHA256:
        raise AssertionError("P32TRAILING salt no longer matches the pinned commitment")
    if hashlib.sha256(ciphertext).hexdigest() != CIPHERTEXT_COMMITMENT_SHA256:
        raise AssertionError("P32TRAILING ciphertext no longer matches the pinned commitment")
    if hashlib.sha256(PRIZE_ADDRESS.encode("utf-8")).hexdigest() != ADDRESS_COMMITMENT_SHA256:
        raise AssertionError("prize address no longer matches the pinned commitment")


# ── Evidence packet (sealed) ─────────────────────────────────────────────

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


def build_sealed_evidence_packet():
    """Deterministically render the sealed evidence packet: identical to
    Phase 414/415's packet, EXCEPT (1) the final base64 ciphertext block in
    Item 1 is replaced by its position/format/length and a SHA-256
    commitment of the real ciphertext bytes -- never the bytes themselves
    -- and (2) Item 4's literal prize address is replaced by a SHA-256
    commitment of the address string -- never the address itself. Both
    withheld values are located and verified structurally (the trailing
    paragraph must decode to a "Salted__"-prefixed blob of the expected
    length whose ciphertext hashes to the pinned commitment), not sliced
    out at a hardcoded offset.

    Returns (packet_text, sha256_hex)."""
    _verify_commitments()
    from phase3_sevenpart_permutation_audit import PHASE3_PARTS
    from data import VERIFIED_PRIOR_COMMAND_HASHES

    plaintext = decrypt_phase32_bytes()
    if hashlib.sha256(plaintext).hexdigest() != PHASE32_PLAINTEXT_SHA256:
        raise AssertionError("Phase 3.2 plaintext no longer matches the pinned hash")
    components = extract_phase32_components(plaintext)
    off = components["offsets"]
    prefix = plaintext[:off["encoded_321_start"]]
    middle = plaintext[off["encoded_321_start"]:off["encoded_321_end"]]
    full_suffix = plaintext[off["encoded_321_end"]:].decode("ascii")
    _assert_clean_ascii("prefix", prefix)

    # The suffix is blank-line-separated paragraphs; the LAST paragraph is
    # the base64 ciphertext blob. Located structurally, not by hardcoded
    # offset: it must decode to a "Salted__" header of the expected total
    # length whose ciphertext hashes to the pinned commitment.
    paragraphs = full_suffix.split("\r\n\r\n")
    blob_paragraph = paragraphs[-1]
    compact_b64 = blob_paragraph.replace("\r\n", "").replace("\n", "")
    raw = base64.b64decode(compact_b64)
    if raw[:8] != b"Salted__" or len(raw) != 8 + SALT_LENGTH_BYTES + CIPHERTEXT_LENGTH_BYTES:
        raise AssertionError("trailing paragraph is not the expected Salted__ ciphertext blob")
    located_salt = raw[8:8 + SALT_LENGTH_BYTES]
    if hashlib.sha256(located_salt).hexdigest() != SALT_COMMITMENT_SHA256:
        raise AssertionError("located salt does not match the pinned commitment")
    if hashlib.sha256(raw[16:]).hexdigest() != CIPHERTEXT_COMMITMENT_SHA256:
        raise AssertionError("located ciphertext does not match the pinned commitment")

    blob_offset_start = off["encoded_321_end"] + full_suffix.index(blob_paragraph)
    blob_offset_end = len(plaintext)
    safe_suffix = full_suffix[:full_suffix.index(blob_paragraph)].rstrip("\r\n")

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
    parts.append("ITEM 1 -- Exact Phase 3.2 plaintext (2422 bytes total) up to the final")
    parts.append("ciphertext block, which is DELIBERATELY WITHHELD (see the sealed-target")
    parts.append("note at its position below). Everything else below is confirmed,")
    parts.append("already-decrypted output from earlier, SOLVED stages of this puzzle")
    parts.append("(Phase 2 through Phase 3.2).")
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
    parts.append(f"[bytes {off['encoded_321_end']}-{blob_offset_start}, literal text]")
    parts.append(safe_suffix)
    parts.append("")
    parts.append(
        f"[bytes {blob_offset_start}-{blob_offset_end} -- SEALED TARGET, WITHHELD.\n"
        "This is where the final unsolved ciphertext block sits in the confirmed\n"
        "plaintext, immediately after the text above. Its bytes are deliberately\n"
        "NOT included in this packet. What you are told instead:\n"
        "  - format: base64 encoding of OpenSSL's standard \"Salted__\" + 8-byte\n"
        "    salt + ciphertext layout (the same format named in ITEM 3 below);\n"
        f"  - length: {CIPHERTEXT_LENGTH_BYTES} bytes of raw ciphertext after the "
        f"\"Salted__\"+salt header ({CIPHERTEXT_LENGTH_BYTES // 16} AES blocks of "
        "16 bytes each);\n"
        "  - a SHA-256 commitment of the 8-byte salt (not the ciphertext):\n"
        f"    {SALT_COMMITMENT_SHA256}\n"
        "  - a SHA-256 commitment of the raw ciphertext bytes (not the base64 "
        "text, not the header, not the salt):\n"
        f"    {CIPHERTEXT_COMMITMENT_SHA256}\n"
        "You cannot verify any candidate against either commitment yourself -- "
        "they are one-way hashes, given only so the withheld material's identity "
        "is fixed and auditable. Do not attempt to guess, reconstruct, or "
        "brute-force the salt or ciphertext bytes from these hashes; propose a "
        "preimage candidate instead, exactly as instructed below.]"
    )
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
    parts.append("ITEM 4 -- Output requirement, verbatim from the puzzle's own creator")
    parts.append("description. The prize address itself is SEALED TARGET, WITHHELD --")
    parts.append("only its commitment is given.")
    parts.append("=" * 78)
    parts.append("")
    parts.append('  The creator explicitly described the final result as "a regular')
    parts.append('  Bitcoin private key". The address that key controls is withheld;')
    parts.append("  its SHA-256 commitment (of the address string itself) is:")
    parts.append(f"  {ADDRESS_COMMITMENT_SHA256}")
    parts.append("  You cannot verify any candidate against this commitment yourself.")
    parts.append("")

    packet_text = "\n".join(parts)
    return packet_text, hashlib.sha256(packet_text.encode("utf-8")).hexdigest()


def write_sealed_evidence_packet(path):
    packet_text, digest = build_sealed_evidence_packet()
    Path(path).write_bytes(packet_text.encode("utf-8"))
    return digest


# ── Frozen solver prompt (mechanically built, byte-exact) ────────────────
#
# Phase 414's own history is why this exists: its prompt was hand-copied
# into the pre-registration doc and then mutated between invocations
# without any mechanical check catching it. Phase 416 instead builds the
# prompt with one function, pins its hash as a constant, and commits the
# exact rendered bytes as a repo artifact that `self_test()` diffs against
# -- so "the frozen prompt" means one authoritative value, not a
# hand-maintained copy inside a Markdown document that can drift.

SOLVER_PROMPT_SHA256 = "8c6744db05ad5d7fdfb8027186d88a269e129e3740854ef5371a8dfcfc79afca"
SOLVER_PROMPT_LENGTH = 13059
FROZEN_PROMPT_ARTIFACT_PATH = SCRIPT_DIR / "phase416_frozen_solver_prompt.txt"

_SOLVER_PROMPT_TEMPLATE = """You are looking at a real, currently-unsolved piece of an authenticated
cryptographic puzzle. Below is the evidence you have: an already-decrypted
plaintext from earlier, solved stages of the same puzzle (labeled Phase 2,
Phase 3, Phase 3.2), three fully worked examples of how those earlier
stages each turned some piece of solved text into the next stage's AES
password, and the final output requirement. The actual ciphertext for the
one remaining unsolved block, and the actual address the resulting key
must control, are DELIBERATELY NOT INCLUDED IN THIS PROMPT -- you are
given only their position, format, length, and a one-way cryptographic
commitment (a SHA-256 hash) of each. Do not attempt to retrieve either
value from any local file, this or any other repository, an environment
variable, or any other source outside this prompt -- doing so is a tool-
use violation under the prohibition below regardless of whether you
succeed.

{packet}

Your task: propose up to 10 candidate PREIMAGES for the withheld
ciphertext block described above. A preimage is the string you believe
should be SHA-256 hashed to become the actual AES password -- per the
recipe above, the password itself is H = sha256(P).hexdigest(), not P.
Do not submit an already-hashed string as a candidate; submit P, the
thing to be hashed. You cannot verify your guess from the material
included in this prompt -- the ciphertext and address appear only as
commitments here -- so submit your best reasoned candidates without
expecting confirmation.

Respond with EXACTLY ONE JSON object and nothing else -- no prose
before or after it, and no markdown fence around it unless that fence
wraps only the JSON itself. It must match this exact shape (only these
keys, at both levels -- there is no "closure" field in this version):

{{
  "tool_used": <true or false, REQUIRED and explicit -- never omit this>,
  "reasoning_text": "<your overall reasoning, as plain text>",
  "candidates": [
    {{
      "display": "<the exact preimage string P -- exact characters, exact case; this is the ONLY place you write P -- do not also hash or hex-encode it yourself, and do not repeat it in hex>",
      "derivation": "<one paragraph: how you got from the evidence to this exact string, and which of Phase 2, Phase 3, or Phase 3.2 licenses each step>",
      "rank": <integer, 1 = most confident; across ALL your candidates the ranks must be exactly 1..n with no duplicates or gaps, fixed now>
    }}
  ]
}}

Every field you write must be your actual, final, complete answer.
Never leave a placeholder, a "TODO", or a "FIXME" in any field -- if you
are not confident in a candidate, either omit it entirely or give it a
worse (higher-number) rank, rather than submitting an incomplete one.

Include at most 10 entries in "candidates". Do not add any field not
shown above, at either the top level or inside a candidate object -- in
particular, do not add a "closure" field; it is not part of this
version's schema.

Do not use any tool, for any purpose, at any point while answering this:
no file access, no shell or terminal commands, no code execution, no
calculator, no hashing (SHA-256 or otherwise), no encryption or
decryption, no attempt to test, verify, or decrypt any candidate against
anything, no reading or searching any local file or repository, no
reading environment variables, and no web search, web fetch, or lookup
of this puzzle, "GSMG", gsmg.io, Bitcoin puzzle solutions, or any
external source. Neither the ciphertext nor the address is included in
this prompt; do not attempt to locate either one anywhere else -- on
disk, in any repository, in your environment, or externally -- and do
not treat a tool's ability to search your surroundings as license to use
it here. Reason and answer using only your own understanding of the
material given above. If you used any tool for any reason while
answering, set "tool_used" to true and explain why in "reasoning_text"
-- such a submission will not be scored, but honest disclosure is still
required."""


def _render_solver_prompt():
    """Pure rendering, no pinned-value checks -- the frozen template above
    with the sealed evidence packet substituted in verbatim. Used only by
    `write_solver_prompt()` to (re)generate the committed artifact after an
    intentional template change; never call this where a prompt is about
    to be sent to a solver -- use `build_solver_prompt()` for that, which
    fails closed instead of silently returning drifted text. Returns
    (prompt_text, sha256_hex)."""
    packet_text, packet_digest = build_sealed_evidence_packet()
    assert packet_digest == SEALED_EVIDENCE_PACKET_SHA256, packet_digest
    prompt_text = _SOLVER_PROMPT_TEMPLATE.format(packet=packet_text)
    return prompt_text, hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def build_solver_prompt():
    """The only function that should ever be called to obtain the text to
    actually send to a solver invocation. Fails closed: raises
    AssertionError if the rendered prompt's length or hash no longer
    matches the pinned `SOLVER_PROMPT_LENGTH`/`SOLVER_PROMPT_SHA256`
    constants, or if it no longer matches the committed
    `FROZEN_PROMPT_ARTIFACT_PATH` artifact byte-for-byte -- a drifted
    template (whether from an edit to `_SOLVER_PROMPT_TEMPLATE` or to the
    underlying packet data) must never silently produce a sendable prompt.
    Returns (prompt_text, sha256_hex) only if all three checks pass."""
    prompt_text, digest = _render_solver_prompt()
    if len(prompt_text) != SOLVER_PROMPT_LENGTH:
        raise AssertionError(
            f"rendered prompt length {len(prompt_text)} != pinned SOLVER_PROMPT_LENGTH "
            f"{SOLVER_PROMPT_LENGTH} -- the template or packet has drifted; re-pin "
            "deliberately via write_solver_prompt() if this is an intentional change"
        )
    if digest != SOLVER_PROMPT_SHA256:
        raise AssertionError(
            f"rendered prompt sha256 {digest} != pinned SOLVER_PROMPT_SHA256 "
            f"{SOLVER_PROMPT_SHA256} -- the template or packet has drifted; re-pin "
            "deliberately via write_solver_prompt() if this is an intentional change"
        )
    committed_bytes = FROZEN_PROMPT_ARTIFACT_PATH.read_bytes()
    if committed_bytes != prompt_text.encode("utf-8"):
        raise AssertionError(
            f"rendered prompt no longer matches the committed artifact at "
            f"{FROZEN_PROMPT_ARTIFACT_PATH} byte-for-byte -- re-run "
            "write_solver_prompt() deliberately if this is an intentional change"
        )
    return prompt_text, digest


def write_solver_prompt(path):
    """Regenerate the committed prompt artifact after an intentional
    template or packet change. Uses the unchecked private renderer, not
    `build_solver_prompt()`, since the whole point of calling this is to
    produce a NEW pinned value -- comparing against the old one first
    would be circular. After running this, `SOLVER_PROMPT_LENGTH` and
    `SOLVER_PROMPT_SHA256` must be updated by hand to match the printed
    digest, or every subsequent `build_solver_prompt()` call will (by
    design) refuse to return anything."""
    prompt_text, digest = _render_solver_prompt()
    Path(path).write_bytes(prompt_text.encode("utf-8"))
    return digest


# ── Corrected, simplified strict submission schema ──────────────────────
#
# No `closure` key is permitted at all. This is a preregistered choice to
# make convergence the sole, simpler promotion discipline in this phase --
# not a claim that closure-style reasoning is incoherent under a sealed
# target (an instruction can in principle uniquely determine a preimage
# without the solver ever touching the ciphertext). Convergence is the
# sole promotion path here by design. `"..."` is removed from residue
# detection (it fired on ordinary ellipsis punctuation, including
# punctuation appearing literally in the packet's own quoted plaintext);
# `placeholder`/`todo`/`fixme` remain.

REQUIRED_SUBMISSION_KEYS = phase414.REQUIRED_SUBMISSION_KEYS
REQUIRED_CANDIDATE_KEYS = frozenset({"display", "derivation", "rank"})
ALLOWED_CANDIDATE_KEYS = REQUIRED_CANDIDATE_KEYS  # closure is NOT an allowed key


def _residue_violation(text):
    lowered = text.lower()
    for marker in RESIDUE_MARKERS:
        if marker in lowered:
            return marker
    return None


def validate_submission_schema(submission):
    """Returns (True, parsed_candidates) or (False, reason). Never
    normalizes anything -- a submission either matches the frozen shape
    exactly or the whole thing is rejected."""
    if not isinstance(submission, dict) or set(submission.keys()) != REQUIRED_SUBMISSION_KEYS:
        return False, "unexpected or missing top-level keys"
    if not isinstance(submission["tool_used"], bool):
        return False, "tool_used must be an explicit boolean"
    if not isinstance(submission["reasoning_text"], str):
        return False, "reasoning_text must be a string"
    residue = _residue_violation(submission["reasoning_text"])
    if residue:
        return False, f"reasoning_text contains unfinished template residue ({residue!r})"

    raw_candidates = submission["candidates"]
    if not isinstance(raw_candidates, list) or not (1 <= len(raw_candidates) <= MAX_SOLVER_CANDIDATES):
        return False, f"candidates must be a list of 1..{MAX_SOLVER_CANDIDATES} raw entries (before dedup)"

    parsed, ranks, seen_material = [], [], set()
    for candidate in raw_candidates:
        if not isinstance(candidate, dict) or set(candidate.keys()) != REQUIRED_CANDIDATE_KEYS:
            return False, "candidate has unexpected or missing keys (closure is not permitted in Phase 416)"

        display = candidate["display"]
        if not isinstance(display, str) or not display:
            return False, "display must be a non-empty string"
        residue = _residue_violation(display)
        if residue:
            return False, f"display contains unfinished template residue ({residue!r})"

        derivation = candidate["derivation"]
        if not isinstance(derivation, str) or not derivation:
            return False, "derivation must be a non-empty string"
        residue = _residue_violation(derivation)
        if residue:
            return False, f"derivation contains unfinished template residue ({residue!r})"

        try:
            material = display.encode("utf-8")
        except UnicodeEncodeError:
            return False, "display is not valid UTF-8-encodable text"
        hex_value = material.hex()

        rank = candidate["rank"]
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            return False, "rank must be a positive integer"
        ranks.append(rank)

        if material in seen_material:
            return False, "duplicate candidate within one submission (display encodes to identical bytes)"
        seen_material.add(material)
        parsed.append({**candidate, "preimage_utf8_hex": hex_value, "material": material})

    if sorted(ranks) != list(range(1, len(raw_candidates) + 1)):
        return False, "ranks must be exactly a 1..n permutation with no duplicates or gaps"

    return True, parsed


def eligible_submissions(invocation_records):
    """Identical in logic to Phase 414/415's version -- redefined only
    because it must call THIS module's `validate_submission_schema()`."""
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
    """Identical in logic to Phase 414/415's version -- redefined only
    because it calls this module's own `eligible_submissions()`."""
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


def promote_candidates(eligible):
    """Convergence-only promotion (the sole path in Phase 416 -- no
    closure field exists to gate a second path). Returns a dict
    hex -> {"path": "convergence", "votes": int, "ranks": [...]}."""
    votes = {}
    for submission in eligible:
        for candidate in submission["accepted"]:
            votes.setdefault(candidate["preimage_utf8_hex"], []).append(candidate)

    promoted = {}
    for hex_value, candidates in votes.items():
        if len(candidates) >= FAMILY_PROMOTION_THRESHOLD:
            ranks = [c["rank"] for c in candidates]
            promoted[hex_value] = {"path": "convergence", "votes": len(candidates), "ranks": ranks}
    return promoted


def test_candidates(promoted, blob_key="P32TRAILING"):
    """Batch-tests every promoted candidate in the frozen deterministic
    order, stopping the whole batch at the first terminal or structural
    hit. Identical logic to Phase 414's version, redefined only because
    Phase 416's `promoted` dicts never carry a `"path": "closure"` entry
    (there is no closure path), which does not otherwise change the
    ordering or stopping behavior."""
    results = {}
    for hex_value, promotion in sorted(promoted.items(), key=_promotion_sort_key):
        material = bytes.fromhex(hex_value)
        result = test_candidate(material, blob_key)
        results[hex_value] = {**promotion, **result}
        if result["outcome"] in ("terminal_hit", "structural_hit"):
            break
    return results


def run_solvers():
    """See `phase414_p32trailing_blinded_reconstruction_audit.run_solvers`'s
    docstring -- identical contract, this phase's own `parse_submission()`
    and `evaluate_panel()` drive the same external spawn loop."""
    raise NotImplementedError(
        "run_solvers() cannot spawn agents from inside this script -- see its "
        "docstring. Use parse_submission() and evaluate_panel() to drive the "
        "external spawn loop."
    )


# ── Self-test ─────────────────────────────────────────────────────────────

def _valid_submission(candidates):
    return {"tool_used": False, "reasoning_text": "reasoning", "candidates": candidates}


def _candidate(display, rank):
    return {"display": display, "derivation": f"derivation for {display!r}", "rank": rank}


def self_test():
    global SOLVER_PROMPT_SHA256, SOLVER_PROMPT_LENGTH, _SOLVER_PROMPT_TEMPLATE
    # -- Sealed packet: pinned hash, and the real secrets never appear --
    packet_text, digest = build_sealed_evidence_packet()
    assert digest == SEALED_EVIDENCE_PACKET_SHA256, digest
    assert PRIZE_ADDRESS not in packet_text
    assert HALVING_ADDRESS not in packet_text
    salt, ciphertext = BLOBS["P32TRAILING"]
    import base64 as _b64
    full_blob_b64 = _b64.b64encode(b"Salted__" + salt + ciphertext).decode()
    assert full_blob_b64 not in packet_text
    # every 40-character contiguous slice of the real base64 blob is absent
    # (every starting offset, not a sampled subset -- absence of every
    # length-40 window also implies absence of every longer contiguous one)
    for i in range(len(full_blob_b64) - 40 + 1):
        assert full_blob_b64[i:i + 40] not in packet_text
    assert SALT_COMMITMENT_SHA256 in packet_text
    assert CIPHERTEXT_COMMITMENT_SHA256 in packet_text
    assert ADDRESS_COMMITMENT_SHA256 in packet_text
    assert "DBBI" not in packet_text and "FAED" not in packet_text

    # -- Frozen prompt: mechanically built, pinned hash, matches the
    #    committed repo artifact byte-for-byte (no hand-copy drift) --
    prompt_text, prompt_digest = build_solver_prompt()
    assert prompt_digest == SOLVER_PROMPT_SHA256, prompt_digest
    assert len(prompt_text) == SOLVER_PROMPT_LENGTH, len(prompt_text)
    committed_bytes = FROZEN_PROMPT_ARTIFACT_PATH.read_bytes()
    assert committed_bytes == prompt_text.encode("utf-8"), (
        "committed phase416_frozen_solver_prompt.txt no longer matches "
        "build_solver_prompt()'s output -- re-run write_solver_prompt() "
        "and re-pin SOLVER_PROMPT_SHA256/SOLVER_PROMPT_LENGTH if this is "
        "an intentional change, or investigate drift if it is not"
    )
    # the prompt must not claim a solver has no access to the withheld
    # targets -- the actual invocation mechanism grants shell/file access
    # to this shared repository, so the prompt only claims non-inclusion
    lowered_prompt = prompt_text.lower()
    assert "not included in this prompt" in lowered_prompt
    assert "even if" not in lowered_prompt
    assert "you have neither" not in lowered_prompt

    # -- build_solver_prompt() fails closed on drift: it must never return
    #    a prompt whose length/hash/artifact-match has silently diverged
    #    from the pinned values, whether the template or a pinned constant
    #    changed. `_render_solver_prompt()` (unchecked) still renders the
    #    drifted text; only the checked, execution-facing builder refuses --
    original_template = _SOLVER_PROMPT_TEMPLATE
    original_sha = SOLVER_PROMPT_SHA256
    original_length = SOLVER_PROMPT_LENGTH
    try:
        _SOLVER_PROMPT_TEMPLATE = original_template + "\nDRIFTED"
        try:
            build_solver_prompt()
            raise AssertionError("build_solver_prompt() must raise on a drifted template")
        except AssertionError as exc:
            assert "SOLVER_PROMPT" in str(exc) or "drifted" in str(exc), exc
    finally:
        _SOLVER_PROMPT_TEMPLATE = original_template

    try:
        SOLVER_PROMPT_SHA256 = "0" * 64
        try:
            build_solver_prompt()
            raise AssertionError("build_solver_prompt() must raise when the pinned hash is stale")
        except AssertionError as exc:
            assert "sha256" in str(exc), exc
    finally:
        SOLVER_PROMPT_SHA256 = original_sha

    try:
        SOLVER_PROMPT_LENGTH = -1
        try:
            build_solver_prompt()
            raise AssertionError("build_solver_prompt() must raise when the pinned length is stale")
        except AssertionError as exc:
            assert "length" in str(exc), exc
    finally:
        SOLVER_PROMPT_LENGTH = original_length

    # sanity: build_solver_prompt() succeeds again once constants are restored
    build_solver_prompt()

    # -- Commitments cover the salt too, not just the ciphertext: changing
    #    the salt while leaving the ciphertext hash untouched must fail --
    tampered_salt = bytes((salt[0] ^ 0xFF,)) + salt[1:]
    original_blobs_entry = BLOBS["P32TRAILING"]
    BLOBS["P32TRAILING"] = (tampered_salt, ciphertext)
    rejected = False
    try:
        _verify_commitments()
    except AssertionError as exc:
        rejected = True
        assert "salt" in str(exc), exc
    finally:
        BLOBS["P32TRAILING"] = original_blobs_entry
    assert rejected, "_verify_commitments() must reject a tampered salt"

    # -- Schema: no closure key permitted at all --
    with_closure = _valid_submission([
        {**_candidate("x", 1), "closure": {
            "instruction_offset_start": 0, "instruction_offset_end": 1,
            "instruction_quote": "x", "token_spans": [[0, 1]], "zero_alternatives": True,
        }}
    ])
    ok, reason = validate_submission_schema(with_closure)
    assert not ok and "closure" in reason, (ok, reason)

    # -- preimage_utf8_hex computed, not accepted --
    submission = _valid_submission([_candidate("onefortwoforthree", 1)])
    ok, parsed = validate_submission_schema(submission)
    assert ok, parsed
    assert parsed[0]["preimage_utf8_hex"] == "onefortwoforthree".encode("utf-8").hex()

    # -- "..." is no longer residue; placeholder/todo/fixme still are --
    ellipsis_ok = _valid_submission([
        {**_candidate("cleandisplay", 1),
         "derivation": "quoting the packet's own '... am I here? Wake up, you...' text verbatim"}
    ])
    ok, reason = validate_submission_schema(ellipsis_ok)
    assert ok, reason

    for marker in ("placeholder", "TODO", "FiXmE"):
        bad = _valid_submission([_candidate(f"candidate with {marker} inside", 1)])
        ok, reason = validate_submission_schema(bad)
        assert not ok and "residue" in reason, (marker, ok, reason)

    # -- No implicit normalization --
    ok1, p1 = validate_submission_schema(_valid_submission([_candidate("causality ", 1)]))
    ok2, p2 = validate_submission_schema(_valid_submission([_candidate("causality", 1)]))
    assert ok1 and ok2 and p1[0]["preimage_utf8_hex"] != p2[0]["preimage_utf8_hex"]

    # -- Duplicate detection, rank permutation, top-level checks --
    dup = _valid_submission([_candidate("same", 1), _candidate("same", 2)])
    ok, reason = validate_submission_schema(dup)
    assert not ok and "duplicate" in reason

    bad_ranks = _valid_submission([_candidate("a", 1), _candidate("b", 1)])
    ok, reason = validate_submission_schema(bad_ranks)
    assert not ok and "rank" in reason

    missing_tool_used = {"reasoning_text": "x", "candidates": [_candidate("a", 1)]}
    ok, reason = validate_submission_schema(missing_tool_used)
    assert not ok and "top-level" in reason

    # -- tool_used excludes regardless of purpose (defense in depth, retained) --
    tool_used_true = _valid_submission([_candidate("a", 1)])
    tool_used_true["tool_used"] = True
    eligible = eligible_submissions({"inv-x": tool_used_true})
    assert len(eligible) == 0

    # -- Panel / cap behavior matches Phase 414/415 --
    good_records = {f"inv-{i}": _valid_submission([_candidate(f"candidate-{i}", 1)]) for i in range(5)}
    result = evaluate_panel(good_records, 5)
    assert result["status"] == "panel_ready" and len(result["eligible"]) == 5

    try:
        evaluate_panel(good_records, INVOCATION_CAP + 1)
        raise AssertionError("evaluate_panel() must raise past the invocation cap")
    except ValueError:
        pass

    partial = dict(list(good_records.items())[:2])
    assert evaluate_panel(partial, 2)["status"] == "need_more"
    assert evaluate_panel(partial, INVOCATION_CAP)["status"] == "protocol_invalid"

    # -- Invocation-identity: replay under the same id never inflates votes --
    single_key = {"inv-1": good_records["inv-0"]}
    assert len(eligible_submissions(single_key)) == 1
    two_ids_same_content = {"inv-1": good_records["inv-0"], "inv-2": good_records["inv-0"]}
    assert len(eligible_submissions(two_ids_same_content)) == 2

    # -- End-to-end smoke test: convergence promotion + real oracle pipeline
    #    against a SYNTHETIC blob (never the real P32TRAILING blob) --
    converging_records = {
        "inv-a": _valid_submission([_candidate("sharedguess", 1)]),
        "inv-b": _valid_submission([_candidate("sharedguess", 1)]),
    }
    eligible = eligible_submissions(converging_records)
    promoted = promote_candidates(eligible)
    shared_hex = "sharedguess".encode("utf-8").hex()
    assert shared_hex in promoted and promoted[shared_hex]["votes"] == 2

    import hashlib as _hashlib
    body = b"synthetic phase416 smoke-test plaintext, not a real secret"
    synth_salt, synth_ct = phase414._make_cbc_blob(
        _hashlib.sha256(b"sharedguess").hexdigest().encode("ascii"), body
    )
    result = test_candidate(b"sharedguess", blob=(synth_salt, synth_ct))
    assert result["outcome"] == "structural_hit", result
    assert result["records"][0]["structural_tier"] == "strong_text", result

    # test_candidates() batch-stops on first hit, over the promoted dict,
    # using the synthetic blob's own key (not the real BLOBS default).
    def _test_candidates_on_blob(promoted_dict, blob):
        results = {}
        for hex_value, promotion in sorted(promoted_dict.items(), key=_promotion_sort_key):
            material = bytes.fromhex(hex_value)
            r = test_candidate(material, blob=blob)
            results[hex_value] = {**promotion, **r}
            if r["outcome"] in ("terminal_hit", "structural_hit"):
                break
        return results

    batch_result = _test_candidates_on_blob(promoted, blob=(synth_salt, synth_ct))
    assert batch_result[shared_hex]["outcome"] == "structural_hit"

    print("phase416_p32trailing_sealed_target_reconstruction_audit.self_test(): all checks passed")


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-packet", metavar="PATH")
    parser.add_argument("--write-prompt", metavar="PATH")
    args = parser.parse_args()

    if args.write_packet:
        digest = write_sealed_evidence_packet(args.write_packet)
        print(f"wrote {args.write_packet} sha256={digest}")
        return

    if args.write_prompt:
        digest = write_solver_prompt(args.write_prompt)
        print(f"wrote {args.write_prompt} sha256={digest}")
        return

    self_test()


if __name__ == "__main__":
    main()
