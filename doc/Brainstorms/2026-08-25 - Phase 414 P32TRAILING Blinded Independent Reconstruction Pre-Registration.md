---
type: worksheet
status: live
date: 2026-08-25
topics:
  - brainstorm
  - p32trailing
  - blinded-experiment
  - external-solvers
  - evidence-acquisition
  - theory-registry
---

# Phase 414 — P32TRAILING Blinded Independent Reconstruction Pre-Registration

> [!caution] Prepared before any solver is invoked
> This is a **methodology change, not another internal transform**. It
> targets `P32TRAILING` — an authenticated OpenSSL blob appended directly
> to the solved Phase 3.2 plaintext (no DBBI/FAED topology assumption
> required) — with independently-derived candidate passwords from
> agents that have never seen this project's hypothesis history, rather
> than another algorithm invented from inside that history. No candidate
> is tested, and no solver is invoked, before this document and the
> evidence packet's pinned bytes are both frozen and committed.

## Why this target, why now

`P32TRAILING` is authenticated (corroborated by the official puzzle
repository, confirmed by its own salt against the two other tracked
blobs) and locally verifiable without any network lookup. `FINDINGS.md`
already records well over a hundred prior negative results against it,
spanning direct clue phrases, the full legacy/PBKDF2/ECB/stream/keywrap
oracle sweep, checkerboard-keyword families, sibling-output
constructions, and a 5,040-permutation sweep of Phase 3's own seven
password parts. Phase 410 established that Phase 2, Phase 3, and Phase
3.2 all share one consistent password-construction profile (below).
Given that density of internal search, the next useful bit of
information is more likely to come from a reader who has never seen any
of it than from one more transform invented inside it.

**Exclusions (unchanged from every prior phase):** no plaintext
generation beyond what this protocol licenses, no DBBI/FAED
combinator, no new cipher/mode/KDF family beyond what is explicitly
named below, no fund movement, no broadcasting, no network lookups. No
raw private key bytes, WIF strings, or full decrypted plaintext bytes
are ever printed, logged, or committed by any script in this phase —
see the redaction contract under Testing protocol.

## The evidence packet (frozen, exhaustive — nothing else is given to solvers)

Built deterministically by `build_evidence_packet()` in
`tools/gsmg/phase414_p32trailing_blinded_reconstruction_audit.py`,
sourced directly from `tools/gsmg/data.py` (no manual retyping of any
security-sensitive fixed string). Its exact bytes and SHA-256 are
pinned in a **separate pre-execution commit**, after this document's
corrections are committed and before any solver runs. It contains
exactly four items and nothing else:

1. **The exact, complete Phase 3.2 plaintext (2,422 bytes) and the
   trailing ciphertext.** The plaintext is reproduced byte-for-byte:
   the opening English passage, the embedded EBCDIC/Beaufort ciphertext
   sub-block (non-ASCII — rendered as a labeled hex dump so the packet
   stays valid UTF-8, with its exact byte offsets and length stated),
   the 149-digit checkerboard numeric string, the Phase 3.2.2 clue
   sentence, and finally the literal base64 `P32_TRAILING_BLOB_B64` two
   lines — which is `P32TRAILING` itself, already sitting at the very
   end of this plaintext exactly as decrypted, not a separate exhibit.
   Solvers are told explicitly: everything up to the final base64 block
   is confirmed, already-decrypted puzzle output, labeled with its
   originating stage numbers (Phase 2 / Phase 3 / Phase 3.2 — see
   below); the final base64 block is the sole unsolved target.
2. **Three solved AES boundaries, as worked calibration examples**
   (Phase 2, Phase 3, Phase 3.2 itself — the boundary that produced the
   plaintext in item 1):

   | Stage | Exact preimage (verbatim; case selected by the local instruction — no subsequent normalization) | SHA-256 hex digest (= the literal AES password) |
   |---|---|---|
   | Phase 2 | `causality` | `eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf` |
   | Phase 3 | `causality` + `Safenet` + `Luna` + `HSM` + `11110` + `0x736B6E61622072...` (one long hex token) + `B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1` (a chess FEN, not a hex token) — seven parts total, raw concatenation, no separators, each token's own case as fixed by its originating stage | `1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5` |
   | Phase 3.2 | `jacquefresco` + `giveit` + `justonesecond` + `heisenbergsuncertaintyprinciple` — raw concatenation, no separators; Phase 3.2's own instruction explicitly forces all-lowercase | `250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c` |

   Each row's full preimage strings are given verbatim in the actual
   packet file (the middle Phase-3 token is abbreviated in this table
   only). All three follow the identical recipe in item 3. Note: **case
   is never a free choice for a solver** — it is fixed by whatever
   in-packet instruction produced that token, exactly as the Phase 3.2
   example's forced-lowercase instruction shows. A candidate that
   invents a case change not licensed by an in-packet instruction does
   not qualify for single-derivation closure (see promotion rule).
3. **The solved-stage assembly instructions (the recipe, stated once,
   generically):**
   - A candidate preimage is one or more tokens, concatenated in a
     fixed order with **no separator characters** between them, in
     whatever case each token's own originating instruction fixes.
   - The AES password actually used is **not** that preimage's raw
     bytes — it is the **lowercase hex SHA-256 digest string of the
     preimage**, itself treated as an ASCII string (e.g. for Phase 2,
     the literal 64-character string `eb3efb51...5bf` is what gets fed
     into the next step, not the word `causality`).
   - That hex-digest string is the password argument to OpenSSL's
     **legacy `EVP_BytesToKey`** key derivation (digest = SHA-256,
     32-byte key + 16-byte IV) against the blob's own salt.
   - The blob itself is base64 of `"Salted__"` + 8-byte salt +
     ciphertext, standard OpenSSL CLI format; decrypt with
     **AES-256-CBC**, then remove standard **PKCS#7** padding.
   - This exact five-step recipe (concatenate, SHA-256, hex-encode,
     legacy-EVP, AES-256-CBC) is the **only** licensed combination
     shape for a single-derivation promotion (see promotion rule
     below) — it is the one thing all three worked examples actually
     demonstrate, not an invented generalization.
4. **The prize address and output requirement, verbatim from the
   puzzle's own creator description:** the creator explicitly
   described the final result as **"a regular Bitcoin private key"**;
   the known prize address is `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`.

**Nothing else is included or referenced.** The packet is
self-contained; a solver needs nothing outside it.

## Solver protocol

**Population target: 5 eligible submissions**, from clean-context agent
invocations — fresh conversational context with **no inherited turns**
from this project's history, so nothing here contaminates them. (The
concrete mechanism used to obtain a clean-context invocation is an
implementation detail of this environment, not part of the frozen
protocol.) Each invocation receives only the frozen prompt below; none
sees another's output before submitting.

**"Independent" is qualified, not claimed outright.** Clean-context
invocations of the same underlying model family are **operationally
isolated replicates**, not statistically independent observers in the
epistemic sense — they may share systematic priors or blind spots
purely from being the same model. Convergence between two such
replicates is used here strictly as a **promotion signal** (a reason to
spend a bounded number of oracle tests on a candidate), never as
independent confirmation that the derivation itself is correct — that
distinction is preserved through to `FINDINGS.md`/registry write-up
regardless of outcome. Heterogeneous models are preferred where
available; if only one model family is available, that limitation is
stated plainly in the results write-up rather than glossed over.

**Blinding is by instruction and disclosure, not sandboxing.** These
agents retain full tool access — there is no way in this environment to
strip that from a spawned agent. The frozen prompt instructs them not
to use any tool to look up this puzzle, this repository, GSMG, or
Bitcoin puzzle solutions, and to disclose at the top of their answer if
they used any tool for any reason. Two independent backstops:

- **Disclosed-tool-use exclusion:** any submission that admits tool use
  for lookup purposes is excluded from promotion before its candidates
  are even read for content.
- **Post-hoc blinding check (forbidden vocabulary, precise):** a
  submission is excluded if **any free text it authored** — its overall
  reasoning, or any individual candidate's display string, derivation,
  or closure instruction quote — contains, case-insensitive, any of:
  `DBBI`, `FAED`, `SALPH`, `SALPHASEION`, `SalPhaseIon`,
  `Cosmic Duality`, `URLBLOB`, `BTCSEED`, `KMODEST`, `yin-yang`,
  `yinyang`, `FINDINGS.md`, `GSMG_SCIENTIFIC_THEORY_REGISTRY`,
  `Naddiseo`, `HosterjackAGV`, `halbgott`, `puzzlehunt/gsmgio`, any
  `github.com` URL, or a `Phase`/`phase` token immediately followed by
  any number other than `2`, `3`, or `3.2` (regex:
  `phase\s*(\d+(\.\d+)?)` with the captured number outside
  `{2, 3, 3.2}`). **Referencing Phase 2, Phase 3, or Phase 3.2, or
  quoting any string that literally appears in the packet, is expected
  and is not leakage** — only material absent from the packet counts.
  This list is necessary but not sufficient: every submission is also
  read in full before promotion, and any submission whose reasoning
  clearly draws on GSMG-specific facts not present in the packet (even
  without matching a listed string) is excluded on the same basis.

**Frozen prompt (verbatim, sent unmodified to all invocations):**

```text
You are looking at a real, currently-unsolved piece of an authenticated
cryptographic puzzle. Below is the complete evidence you have: an
already-decrypted plaintext from earlier, solved stages of the same
puzzle (labeled Phase 2, Phase 3, Phase 3.2), three fully worked
examples of how those earlier stages each turned some piece of solved
text into the next stage's AES password, and the final output
requirement.

[EVIDENCE PACKET INSERTED HERE VERBATIM]

Your task: propose up to 10 candidate PREIMAGES for the one remaining
encrypted block (the final base64 block in the plaintext above). A
preimage is the string you believe should be SHA-256 hashed to become
the actual AES password -- per the recipe above, the password itself is
H = sha256(P).hexdigest(), not P. Do not submit an already-hashed
string as a candidate; submit P, the thing to be hashed.

Respond with EXACTLY ONE JSON object and nothing else -- no prose
before or after it, and no markdown fence around it unless that fence
wraps only the JSON itself. It must match this exact shape (only these
keys, at both levels):

{
  "tool_used": <true or false, REQUIRED and explicit -- never omit this>,
  "reasoning_text": "<your overall reasoning, as plain text>",
  "candidates": [
    {
      "display": "<the exact preimage string P -- exact characters, exact case>",
      "preimage_utf8_hex": "<the UTF-8 bytes of that exact same string, as lowercase hex -- must round-trip to display exactly; this field, not display, is authoritative>",
      "derivation": "<one paragraph: how you got from the evidence to this exact string, and which of Phase 2, Phase 3, or Phase 3.2 licenses each step>",
      "rank": <integer, 1 = most confident; across ALL your candidates the ranks must be exactly 1..n with no duplicates or gaps, fixed now>,
      "closure": null
    }
  ]
}

Include at most 10 entries in "candidates". Only set "closure" to
something other than null if you believe every parameter of that one
candidate's derivation is fixed by an explicit instruction elsewhere in
the packet with zero remaining alternatives -- in that case, replace it
with an object of exactly this shape: {"instruction_offset_start":
<int>, "instruction_offset_end": <int>, "instruction_quote": "<the
verbatim text at that exact character range in the packet above>",
"token_spans": [[<start>, <end>], ...], "zero_alternatives": true}.
Otherwise leave "closure" as null. Do not add any field not shown
above, at either the top level or inside a candidate or closure object.

Do not use any tool (file access, shell commands, web search, web
fetch, or any other tool) to look up this puzzle, "GSMG", gsmg.io,
Bitcoin puzzle solutions, or any external source. Work only from the
material given above. If you used any tool for any reason while
answering, set "tool_used" to true and explain why in "reasoning_text"
-- such a submission will not be scored, but honest disclosure is still
required.
```

**Parsing the response (mechanical only, never a semantic
reinterpretation).** `parse_submission()` first tries `json.loads()` on
the entire (stripped) raw response text directly; if that fails, it
treats the entire response as a single fenced ` ```json ... ``` ` block
and parses the inside of that — using an exact full-string match, not a
search, so a fence with **any** prose before or after it (a common
failure mode: "Here is my answer:\n```json\n{...}\n```") is a rejection,
not something to strip away. Both parses reject **any duplicate key at
any nesting level** (e.g. `{"tool_used":true,"tool_used":false,...}`,
which `json.loads()` would otherwise silently resolve to `False` — the
last value wins by default) rather than letting the parser's own
tie-break decide the content. Anything else — prose, multiple JSON
objects, no parseable JSON at all — yields no submission at all: it is
never coerced, guessed at, or manually rewritten into the expected
shape, since doing so would itself violate the no-coercion rule this
document sets for every other step. An unparseable response still
consumes one of the 8 invocation-cap slots below; it just never enters
`invocation_records` and never counts toward the panel.

**Invocation identity.** Every invocation is assigned a fresh, unique
invocation ID by the orchestrator **before** it is spawned — never
derived from, or influenced by, anything in the solver's own JSON
output. Collected submissions live in a dict keyed by that ID, never a
bare list: replaying the same submission (whether by accident or
adversarially) under the *same* ID can never contribute a second vote,
since a dict key can only ever hold one value, while two genuinely
different invocations that happen to converge on identical content
still count as two — that distinction is the entire point of the
convergence rule, and it is enforced structurally, not by comparing
content. Panel size, `invocations_used`, and the 8-invocation cap below
are all counted against this same ID-keyed ledger, never against a
list's length.

**Invocation cap and panel validity.** Up to 8 total invocations may be
spawned to backfill submissions excluded by either blinding backstop or
rejected under the strict schema below, predeclared here so replacement
is not a post-hoc decision. If 5 eligible, well-formed submissions are
not obtained within that cap, the phase is classified `protocol_invalid`
(see interpretation rules) — **not** evidence of non-identifiability. A
"no convergence" result is interpretable only from a full panel of 5
eligible submissions. **The cap is enforced before panel readiness is
even considered**: if `evaluate_panel()` is ever called with more
invocations already used than the cap allows, that is a bug in the
calling orchestration loop, not a phase result — it raises rather than
reporting `panel_ready` just because 5 eligible records already happen
to be present, and an over-cap or otherwise structurally inconsistent
ledger must never be allowed to look like a clean success.

## Strict submission schema (frozen; reject wholesale, never coerce)

A submission is validated as a whole. Any violation — anywhere in it —
voids the **entire submission**, not just the offending candidate:
there is no per-candidate salvage, and no silent coercion of a
near-miss into the expected shape (no case-folding a hex string, no
defaulting a missing field, no discarding "extra" candidates to get
back under a limit).

- **Top level**: exactly the keys `tool_used` (a JSON boolean, never
  defaulted if absent — a missing field is a schema violation, not an
  implicit "no tool used"), `reasoning_text` (a string), and
  `candidates` (a list of **1 to 10 raw entries, counted before any
  deduplication** — an 11th raw candidate voids the whole submission
  even if it duplicates one already present). No other top-level key is
  permitted.
- **Each candidate**: exactly the keys `display`, `preimage_utf8_hex`,
  `derivation`, `rank`, and optionally `closure`. `preimage_utf8_hex`
  must be non-empty, even-length, and **strictly lowercase** hex — an
  uppercase or mixed-case hex string is a schema violation, not
  something this phase's tooling normalizes on the submitter's behalf.
  `display` must round-trip (UTF-8-encode) to exactly that hex.
  `derivation` must be non-empty. `rank` must be a positive integer, and
  across one submission's full candidate list the set of ranks must be
  **exactly `{1, ..., n}`** (`n` = that submission's raw candidate
  count) — no duplicates, no gaps. **No two candidates within one
  submission may share the same `preimage_utf8_hex`** — a repeated
  preimage voids the submission; it is never silently collapsed into
  one vote. If present, `closure` must have exactly the keys
  `instruction_offset_start`, `instruction_offset_end`,
  `instruction_quote`, `token_spans`, and `zero_alternatives` — checked
  as strictly as everything else, on both type and value: both offsets
  must be **nonnegative** plain integers (a JSON boolean is rejected
  even though Python's `int` would otherwise accept it, since `bool` is
  an `int` subclass), with `instruction_offset_start <
  instruction_offset_end`; `instruction_quote` a **non-empty** string;
  `zero_alternatives` the **literal boolean `true`** — not merely
  "a boolean" — since a `closure` object is *itself* the claim of zero
  remaining alternatives, so `zero_alternatives: false` is
  self-contradictory and voids the submission the same as a missing or
  wrong-typed field would, not a weaker or merely-unpromoted closure;
  and `token_spans` a non-empty list of `[start, end]` pairs of
  **nonnegative** plain integers with `start < end` in each — not a bare
  list, not `null` entries, not a dict standing in for an offset. A
  closure that satisfies the key-set check but fails any of these checks
  voids the whole submission here, at the schema gate, rather than
  surviving to `validate_closure()` later (which also independently
  guards against the same malformed and out-of-range shapes,
  defensively, in case it is ever called on data that skipped this
  gate).
- **Leakage scanning is recursive over every string value** the
  submission contains — not a fixed list of known fields — so a
  leak hidden in an unrecognized field would be caught even if the
  strict key-set check above did not already reject it outright.

## Canonicalization and convergence rule

**`preimage_utf8_hex` is the sole authoritative encoding.** No
whitespace stripping, no case-folding, no separator normalization, no
Unicode normalization-form conversion. Two candidates converge only if
their `preimage_utf8_hex` values are byte-identical, drawn only from
schema-valid submissions.

## Promotion rule (frozen; exactly two paths, no others)

A candidate is tested against `P32TRAILING` if, and only if:

- **(a) Convergence** — at least 2 of the 5 eligible submissions
  independently produce the byte-identical `preimage_utf8_hex`; **or**
- **(b) Single-derivation closure (tightened)** — one submission's
  derivation:
  1. names an **exact byte-offset range** within the evidence packet
     for **every** token it selects, and
  2. quotes an **explicit instruction sentence, verbatim, appearing
     within the packet itself**, that fixes — with **zero remaining
     alternatives** — which tokens are selected, their order, any
     omissions, their case, and that they are combined by raw
     concatenation only, and
  3. uses no token, separator, case change, or combination shape not
     licensed by that instruction.

  This is gated on **two independent checks, neither of which trusts
  the solver's own claim**:

  1. **A preregistered allowlist.** The declared instruction span must
     match one of a fixed set of packet spans this document commits to,
     before any solver runs, as spans that actually qualify as a
     zero-alternative selector instruction. Byte-offset math can prove
     text exists and that spans reconstruct a candidate; it cannot
     prove that text *instructs* selection with no other reading — only
     a human, committing in advance, can make that call. **This
     allowlist is empty for Phase 414**: nothing in the packet names a
     construction instruction for `P32TRAILING` itself (see the note
     below). A solver's own `zero_alternatives` assertion is never, on
     its own, sufficient to add a span to it.
  2. **Mechanical offset verification**, only reached if (1) passes: the
     declared instruction quote must appear verbatim in the packet at
     its declared offsets, and concatenating the declared token spans
     (also checked against the packet at their declared offsets) must
     reconstruct the candidate's own bytes exactly.

  With an empty allowlist, closure can never promote a candidate in
  this phase — which is intended, not a bug: a "perfect" candidate that
  merely quotes item 4's prize address verbatim and asserts
  `zero_alternatives: true`, for instance, must still fail, since
  quoting an address is not the same as being instructed to build a
  password from it.

  A derivation that is well-argued, evidence-grounded, but not fixed to
  a single reading by an explicit in-packet instruction (e.g. "this
  seems like the natural next password given the pattern") does **not**
  qualify under this path — it needs a second independent convergence
  instead. In practice this path is expected to rarely or never fire
  for `P32TRAILING` itself, since (unlike the three calibration
  examples, whose underlying instructions are not included in the
  packet) nothing in the given plaintext explicitly names a
  password-construction instruction for the trailing blob. That is a
  deliberate, expected consequence of the tightened rule, not a defect
  in it.

**No merging pieces from different submissions after seeing failures.**
Each promoted candidate is tested exactly as submitted (or as
convergently agreed) — never recombined post-hoc.

## Candidate testing order (frozen)

If more than one candidate is promoted, they are tested in a
deterministic order, not dictionary/insertion order and not left
unspecified: sort by (1) the **best (lowest = most confident) rank**
any contributing eligible submission gave that candidate, ascending;
(2) vote count, descending (more convergence tested first on a rank
tie); (3) the `preimage_utf8_hex` string itself, as a final tie-break so
the order is always fully determined. Solver ranks are inputs to this
ordering, not decoration — a candidate no solver ranked first is never
tested ahead of one some solver did, purely by accident of dict
iteration. Testing still stops at the first terminal or structural hit
across the whole ordered list (see below), so this ordering also
determines which candidates get tested at all if an early one hits.

## Testing protocol (frozen)

For each promoted candidate preimage `P` (bytes from its
`preimage_utf8_hex`), tested in the order above:

```text
H = sha256(P).hexdigest().encode("ascii")

1. Phase-410 exact profile: legacy EVP_BytesToKey(H, salt,
   digest="sha256", key_len=32) -> AES-256-CBC -> PKCS7 unpad,
   against BLOBS["P32TRAILING"].
2. Frozen broad oracle against H: the same legacy/PBKDF2 x
   AES-CBC/stream/ECB variant lists already used project-wide (no new
   cipher, mode, or KDF family) plus Key-Wrap, against
   BLOBS["P32TRAILING"] only. CBC and Key-Wrap reuse the existing
   crypto functions directly; ECB and stream are re-implemented against
   the same frozen variant lists rather than calling
   `aes_try_open_ecb_bytes()`/`aes_try_open_stream_bytes()` directly --
   both log the raw password material and a plaintext preview to
   `weak_candidates_log.txt` for any 5<=z<8 decrypt, which the
   redaction contract below forbids. Step 1's exact variant is skipped
   here if it would otherwise repeat (deduplicated, not re-run).
3. Frozen broad oracle against P itself (the raw preimage, not its
   hex digest) -- the same "exact two forms" precedent already used
   for the Phase 3 seven-part concatenation.
```

**Stop granularity (frozen, exact).** "Stop at the first hit" applies at
every level, not just between steps 1-3 above:

- Within a single CBC, ECB, or stream sweep, the loop over KDF/cipher
  variants stops the moment one variant produces a terminal or
  structural hit -- it does not keep decrypting remaining variants
  "for completeness."
- Within step 2's broad pass, families are tried in the order
  CBC → ECB → stream → Key-Wrap, and a hit in an earlier family means
  later families in that same step are **never invoked at all** (not
  merely excluded from the report) -- an ECB hit means stream and
  Key-Wrap are not called for that material.
- **One documented exception:** Key-Wrap's underlying unwrap function
  has no incremental/early-exit interface -- it always completes its
  full internal variant sweep (a small space, ~12 combinations, with no
  logging side effect to avoid) before this module regains control.
  This module still only ever reports up to and including the first
  keywrap hit in its own output, but the underlying attempts for any
  variants after that hit have, unavoidably, already run by the time
  this module sees the result. This is an accepted, disclosed exception
  to atomic stopping, not an oversight.

`BLOBS["P32TRAILING"]` (the `cb_common.BLOBS` dict entry, a
`(salt, ciphertext)` tuple) is passed explicitly by name, not a raw
base64 string list.

**Redaction contract (replaces unmodified `passphrase_hits()` reuse).**
`passphrase_hits()` returns `repr(result)`, which contains decrypted
plaintext bytes — that violates the no-private-material rule, so this
phase does not call it as-is. A wrapper implemented in this phase's own
script performs the decrypt/unpad itself for each variant and records
only:

- the KDF/cipher variant label (public metadata, e.g.
  `"legacy-sha256-aes256"`),
- whether PKCS#7 padding validated at all (boolean),
- the **padding tier**: `full_block` (see below) / `ordinary_valid` /
  `invalid`,
- decrypted-plaintext **length and shape** only (byte length; whether
  it is a multiple of 32; printable-ASCII ratio as a float — never the
  bytes themselves),
- `hashlib.sha256(candidate_material_bytes).hexdigest()` — a digest of
  the tested password material, not the material's own printed value,
  for later exact reproducibility without re-exposing it in logs,
- any derived **address** (public, safe) from the structural check
  below — never a WIF string, never raw key bytes, never the plaintext.

Raw decrypted plaintext, if a structural or terminal hit occurs, is
held **in memory only** for the duration of the address check and is
never written to any file the phase's own tooling creates, with one
narrow exception: if a human follow-up genuinely requires the bytes
(e.g. to hand-verify a WIF), they may be written once to a file created
with mode `0600` outside version control (reusing
`binary_key_material_backfill.append_jsonl(..., sensitive=True)`'s
existing 0600 convention) — never committed, never printed to a log
this phase's automation reads back.

**Padding-probability correction.** *Any* valid PKCS#7 padding occurs
under a uniformly random wrong key with probability
`sum(256**-k for k in range(1, 17)) ≈ 1/255` — a weak signal on its
own, informational only, not sufficient to promote or stop on. Only an
**exact full 16-byte `0x10` padding block** (i.e. the last AES block is
sixteen `0x10` bytes, meaning the true plaintext is exactly a multiple
of 16 bytes shorter than the ciphertext by one full block — for this
80-byte/5-block ciphertext, exactly 64 bytes of real content) has the
much stronger probability `256**-16` under a wrong key. This tier is
called `full_block` above and is the padding-only trigger for the
structural-hit branch.

**Structural-hit check (independent of the padding tier).** A
uniformly random 32-byte value is a valid secp256k1 scalar with
probability effectively 1 (the curve order is within `2**-128` of
`2**256`) — so "is this chunk a valid in-range scalar" carries no
evidential weight on its own and is **not** one of the signals below.
Raw 32-byte chunks are used **only** for the address-match check; the
independently meaningful structural tiers are limited to properties
that are genuinely rare under a wrong key:

- **Address match (terminal), checked unconditionally.** If length is a
  positive multiple of 32, split into 32-byte chunks and run each
  through `binary_key_material_backfill.private_key_details()` — **strip
  the `"wif"` field before recording anything**; keep only `"address"`.
  If any derived address equals `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe` (or
  `HALVING_ADDRESS`, `17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa`, checked on the
  same terms): **terminal hit**.
- **`full_block`** — the padding tier itself (see above), independent of
  content.
- **`valid_wif`** — a checksum-valid WIF substring, decoded via
  `key_shape_classifier.wif_to_private_key()` / `find_wif()` (not a bare
  shape regex — the checksum is what makes this rare, not the shape).
- **`hex64_shape`** — a 64-hex-character substring (via
  `key_shape_classifier.find_hex64()`), embedded within a larger body if
  necessary; rare under random bytes regardless of the resulting
  scalar's range.
- **`keywrap_integrity`** — the AES-Key-Wrap family succeeds (no
  integrity-check exception), run regardless of whether the CBC path
  above produced anything (`~2**-64` false-accept). Structural, not
  terminal, unless the unwrapped bytes also produce an address match.
- **`strong_text`** — the existing project printable-z-score STRONG tier
  (`z >= 8`), for a plausible "next-stage instruction" plaintext; only
  promoted if nothing else already claimed a tier for that decrypt.

Any of the last five tiers, absent an address match, is a **structural
hit, not yet address-matched** — execution stops for manual review
rather than continuing to grind further candidates.

## Interpretation rules (exact, five-way)

- **Terminal hit** — a derived address matches the known prize (or
  halving) address. Immediate report to you before any further action;
  execution stops. No fund movement or broadcast without your explicit
  authorization.
- **Structural hit, not yet address-matched** — one of `full_block`,
  `valid_wif` (checksum-valid), `hex64_shape`, `keywrap_integrity`, or
  `strong_text`, without a matching address (raw scalar validity alone
  never qualifies — see above). Execution **stops** and this is
  reported as an **authenticated/strong stage advancement candidate**
  for your review — explicitly **not** classified as a negative result,
  even though it isn't yet a confirmed solve.
- **Independent convergence or single-derivation closure, but only
  `invalid`/`ordinary_valid`-tier padding and no structural signal.**
  That specific construction is falsified; recorded as a closed
  negative in `FINDINGS.md`, same as every other tested family. A new
  promotion requires a new independent convergence or closure event,
  not a tweak of a failed one.
- **`protocol_invalid`** — fewer than 5 eligible, well-formed
  submissions were obtained within the 8-invocation cap. Recorded as a
  methodology note, not a result about `P32TRAILING`; the experiment
  may be re-run with a corrected invocation procedure, and this does
  **not** count toward the "no convergence" evidence below.
- **No promoted candidates, from a full 5-submission panel, and no
  `protocol_invalid`.** This is the phase's actual negative result:
  independent, evidence-only readers cannot identify `P32TRAILING`'s
  password from its local textual context under this protocol, given
  that they are operationally-isolated replicates of one model family
  (stated as a caveat on the strength of this conclusion, per the
  "independent" qualification above). Per your original instruction,
  this is the trigger to move to targeted archival acquisition rather
  than another transform. Many unconverged candidates with no
  convergence pattern are treated identically — explicitly **not** a
  trigger to start combining, ranking, or bulk-testing them as a new
  combinatorial sweep.

**Regardless of branch:** no outcome here licenses a new DBBI/FAED
combinator, a new cipher/KDF family beyond what is named above, or
plaintext generation beyond the branches themselves.

## Deliverable

`tools/gsmg/phase414_p32trailing_blinded_reconstruction_audit.py`:
`build_evidence_packet()` (deterministic, pinned SHA-256, committed
separately before any solver runs); `parse_submission()`, which
mechanically extracts JSON from a raw response (direct parse, or a
single fenced code block) and returns `None` -- never a guessed-at
reinterpretation -- for anything else; `validate_submission_schema()`,
which rejects a submission wholesale on any deviation from the frozen
shape (unexpected/missing keys at either level, non-boolean
`tool_used`, an 11th raw candidate, non-lowercase hex, a
display/hex round-trip mismatch, a non-1..n rank permutation, a
duplicate `preimage_utf8_hex` within one submission, or a closure with
a non-integer/boolean offset or a malformed `token_spans` entry) rather
than salvaging individual candidates or coercing a near-miss into
shape; `_collect_strings()` / `submission_full_text()` /
`blinding_violations()` / `eligible_submissions()`, the last of which
takes a **dict keyed by orchestrator-assigned invocation ID** (never a
bare list, so replaying one invocation's output under its own ID can
never inflate its vote count) and scans every string value in each
submission recursively (not a fixed field list) for leakage;
`validate_closure()`, gated first on the frozen, preregistered
`QUALIFYING_CLOSURE_INSTRUCTION_SPANS` allowlist (empty for this phase)
and only then on mechanical offset/reconstruction verification -- so a
solver's own `zero_alternatives` claim, however internally consistent,
can never by itself promote a candidate -- and defensively typed
throughout so a malformed closure (e.g. `None` inside `token_spans`, or
a `bool` where an offset is expected) is rejected rather than raising;
`evaluate_panel()`, the pure decision function implementing the
predeclared 8-invocation cap and `protocol_invalid` branch, counted
against the same ID-keyed dict (actually spawning clean-context
invocations is necessarily done by the orchestrating agent outside this
process -- `run_solvers()` documents that contract and raises
`NotImplementedError` rather than pretending to spawn agents itself);
`classify_plaintext()`, which reports only evidentially meaningful
structural tiers (`full_block`, `valid_wif` via
`key_shape_classifier.find_wif()`, `hex64_shape` via `find_hex64()`,
`strong_text`, `keywrap_integrity`) against a `target_addresses`
parameter (defaulting to the real prize/halving addresses, overridable
for a planted-address fixture) and deliberately never treats raw
in-curve-range scalar validity alone as a signal;
`test_material_ecb()`/`test_material_stream()`, local re-implementations
of the existing ECB/stream variant sweeps that never call
`cb_common._log_candidate()` (the reused black-box versions do, for any
5<=z<8 decrypt, writing the raw password material and a plaintext
preview to `weak_candidates_log.txt`) and that -- like
`test_material_cbc()` -- stop their own internal variant loop
immediately on the first hit, not merely between broad-pass steps;
`test_material_secondary_families()`, which additionally stops calling
the *next* family at all once an earlier one in the same call already
hit (an ECB hit means stream and Key-Wrap are never invoked, not merely
excluded from the report -- the one disclosed exception being
Key-Wrap's own black-box unwrap function, which has no early-exit
interface and always completes its small internal sweep before this
module regains control); `test_candidate()`, implementing the frozen
`H-exact -> H-remaining-broad -> P-broad` order with an immediate stop
on the first terminal or structural hit at every level; and
`test_candidates()`, which orders promoted candidates deterministically
by solver rank (`_promotion_sort_key()`, not dict/insertion order) and
stops the whole batch (not just the current candidate) on the same
terms. `self_test()` exercises all of the above against synthetic
fixtures -- including `parse_submission()` on direct/fenced/unparseable
input, an invocation-identity case proving a replayed ID never inflates
votes while two distinct IDs converging on identical content still
count as two, poison-variant cases proving each family's loop truly
stops mid-sweep (a reachable poison entry would raise), a mocked case
proving an ECB hit prevents `test_material_stream()` and
`aes_keywrap_try_open_bytes()` from being called at all, closure
type-safety cases (boolean/dict offsets, a `null` span entry) rejected
without crashing, wholesale-rejection cases for every other schema
violation above, a recursive-leakage case where the leak is hidden
inside a candidate's own derivation, an allowlist-gate case proving a
mechanically-perfect closure (quoting the prize address itself) still
fails until its span is (hypothetically, via patching) allowlisted, a
rank-based ordering case where hex-only ordering would give the wrong
answer, a before/after byte comparison of `weak_candidates_log.txt`
proving the ECB/stream paths never write to it, a planted-address
terminal-hit fixture (the real prize address's key is, definitionally,
unavailable to build a genuine one), real encrypt/decrypt round-trips
for the full-block/strong-text/WIF/hex64/Key-Wrap-integrity tiers, a
call-count check (via patching) that a genuine negative still runs all
three steps, and a byte-exact (not text-mode) comparison against the
committed packet file, which must exist -- plus a real end-to-end
negative against the actual `P32TRAILING` blob. Results are recorded in
`tools/gsmg/FINDINGS.md` as Phase 414, with the redacted (never raw)
solver submissions saved alongside for auditability. A regression test
is added to `tools/gsmg/test_recent_audits.py`. The theory registry is
updated only if a branch above actually changes a tracked theory's
status.

## Related notes

- [P32 Trailing Sibling-Output Password Path](2026-08-14%20-%20P32%20Trailing%20Sibling-Output%20Password%20Path.md)
- [Solved Vector Toolchain Provenance Audit](../GSMG_SOLVED_VECTOR_TOOLCHAIN_PROVENANCE_AUDIT.md) (Phase 410)
- [GSMG Scientific Theory Registry](../GSMG_SCIENTIFIC_THEORY_REGISTRY.md)
