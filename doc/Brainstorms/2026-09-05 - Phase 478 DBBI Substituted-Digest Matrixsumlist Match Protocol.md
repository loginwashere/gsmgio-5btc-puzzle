# Phase 478 DBBI `{b,g}` substituted-digest matrixsumlist match protocol

Date frozen: 2026-09-05. Discovery lock issued (`tools/gsmg/phase478_discovery_lock.json`).

## Provenance and motivation (not evidence)

An unauthenticated `PROGRESS.md` file, attached to Telegram message id
`70983` (`date: 2026-09-04T22:13:05`, `from: X`, `from_id:
user497668740` -- not the creator's `user9815232`) in a newly-exported
chat window (`ChatExport_2026-09-05/files/PROGRESS.md`), self-disclosed
as "first output from GPT-6 Astra with Ultra thinking" in the immediately
following message, observed that DBBI segmented under escape pair `{b,g}`
yields exactly 64 tokens with exactly 16 distinct code types -- the shape
of a lowercase-hex SHA-256 digest -- and proposed testing candidate
`matrixsumlist` serializations against the digest's position-equality
pattern.

**Motivation-input hashes** (pinned in the discovery lock; these files
are excluded from candidate generation by the historical-cutoff rule
below, but their exact identity is itself a provenance fact this protocol
depends on and must not leave unpinned):

- `ChatExport_2026-09-05/result.json`: SHA-256
  `7cd3f979ddcc620ce0940bb6328441d38bb56c751753003dda50e6e5a3d678d8`.
- `ChatExport_2026-09-05/files/PROGRESS.md`: SHA-256
  `e93f34e8b8f611190eb91f68f7ce1265fcc27b0744775028c29818005f8efa7a`.

This document treats that file as motivation only, per this project's
standing discipline for non-creator sources. Every fact this protocol relies
on has been independently re-derived from this project's own pinned data,
not taken from `PROGRESS.md` on trust:

- `segment_codes(DBBI, "b", "g")` (`tools/gsmg/data.py`'s `DBBI` constant,
  `checkerboard_code_ic_oracle.segment_codes` convention) yields 64 tokens,
  16 distinct types. Independently re-run and confirmed.
- `{b,g}` is the unique pair, among all 36 escape-pair hypotheses on DBBI's
  9-symbol alphabet, that yields exactly `(64, 16)`. Independently swept and
  confirmed (see Limits: this uniqueness is a real postselection fact, not
  extra evidence).
- The first-occurrence equality pattern of those 64 tokens is
  `01234556728966286abc61c88b48de3086dd501d5557d6bab5605233df7bbb96`.
  Independently recomputed and confirmed byte-for-byte against
  `PROGRESS.md`'s own claimed string.
- `{b,g}` ranks 2nd of 29 valid pairs under this project's own established
  `checkerboard_code_ic_oracle.ic_by_escape_pair` statistic (IC `0.0709`
  against English `0.067`), immediately behind the project's existing
  `{b,e}` pick (IC `0.0671`, rank 1). Independently recomputed. This is
  corroborating context for why `{b,g}` is worth a dedicated test, not part
  of the digest hypothesis itself.

`PROGRESS.md`'s own significance claim (10,000 letter-count-preserving
shuffles; `{b,g}` alone hits `(64,16)` in ~0.03-0.05%) was independently
reproduced with an independent RNG seed and independent script: 3/10,000 and
29/10,000 (any-pair), matching within noise. Not asserted as this protocol's
own statistic -- the exact-match test below supersedes it -- but recorded as
a second successful independent reproduction of the source material.

## Question

Is DBBI, segmented under escape pair `{b,g}` into a 64-token, 16-type
sequence, a monoalphabetically-substituted lowercase-hex SHA-256 digest of
some byte string this project has already constructed, in some prior phase,
as a candidate serialization or output of `matrixsumlist`?

## Model under test

```text
some already-constructed candidate string C
  -> SHA-256(C), rendered as 64 lowercase hex characters
  -> unknown bijection: 16 hex-digit values -> DBBI's 16 {b,g} code types
  -> DBBI (as segmented under {b,g})
```

The test never guesses the bijection. It compares the *position-equality
pattern* of DBBI's 64 tokens (which positions share a code, which differ)
against the position-equality pattern of `SHA256(C)`'s 64 hex characters
(which positions share a digit, which differ). This is exactly the
substitution-invariant technique this project already uses for the
checkerboard code-IC oracle (Phase 112) and the transposition family's
coincidence statistic (Phase 477A) -- no candidate alphabet or key is ever
required to compute it.

## Frozen segmentation (self-test, asserted on import)

```text
DBBI = data.DBBI  # tools/gsmg/data.py, 91 characters
tokens = segment_codes(DBBI, "b", "g")
assert len(tokens) == 64
assert len(set(tokens)) == 16
pattern = equality_pattern(tokens)  # label by first occurrence, hex-render
assert pattern == "01234556728966286abc61c88b48de3086dd501d5557d6bab5605233df7bbb96"
```

`equality_pattern` is defined once, here, and reused unchanged for scoring
every candidate's digest: label positions by order of first occurrence of
their value (`0` for the first distinct value seen, `1` for the second,
...), render each label as one lowercase hex digit
(`"0123456789abcdef"[label]`). This is well-defined for **any** sequence of
length 64 using at most 16 distinct values -- which every 64-character
lowercase-hex digest satisfies unconditionally, since hex has exactly 16
possible characters. A digest that happens to use *fewer* than 16 distinct
hex digits (a normal, unremarkable occurrence) still produces a perfectly
well-defined pattern over however many distinct labels it actually needs;
that pattern is compared for ordinary string equality against DBBI's
16-label target exactly like every other candidate, and a coarser pattern
simply cannot equal a target that requires 16 distinct labels in specific
positions -- this is a **normal, definite mismatch**, not a special case,
not "undefined," and not skipped. The function's only actual guard (return
`None` above 16 distinct values) exists purely as generic library
robustness; it is mathematically unreachable for a 64-character hex-digest
input and never fires in this protocol.

## Two-lock design

A single lock (this project's usual pattern, e.g. Phase 477A) is not enough
here because candidate *discovery* and candidate *scoring* are two
different failure surfaces: if scope were re-examined after seeing which
candidates exist, the universe could be quietly widened toward a match; if
scope were re-examined after seeing scores, a near-miss could be quietly
promoted. Two locks close both:

**Discovery lock** (issued before the harvester touches any candidate
content): pins this protocol's SHA-256, the harvester script's SHA-256, the
exact eligible source-file inventory (path + git blob hash, see below), and
the historical-cutoff commit. Issued *before* the harvester is run for
real, after its self-tests pass on synthetic fixtures. Nothing about
candidate count, content, or scores may influence any choice made up to and
including this lock.

**Oracle lock** (issued after the harvester produces the manifest, before
any SHA-256 of any candidate byte string is computed): pins the manifest
file's SHA-256, the frozen DBBI pattern above, and the matcher script's
SHA-256. Manifest inspection between the two locks is limited to
*structural* review -- candidate count, provenance completeness, eligibility
flag counts and reasons, encoding sanity -- never to computing or previewing
any digest or any equality pattern of any candidate. The matcher script
itself is written and self-tested only against synthetic fixtures (not the
real manifest) before this lock.

This ordering means: if a hit occurs, it occurred against a universe that
was closed twice, once before anyone had seen what was in it and once
before anyone had seen any score -- the strongest evidentiary posture this
project's own discipline can produce for an unsolicited external lead.

## Historical cutoff

Eligible candidate-generating code must already exist, unchanged, before
this protocol's own triggering observation. Cutoff is pinned to git commit
`64f8063939d1d4d89402b87f88aa22b8fb956a7b` (2026-09-05, "Phases 461-477:
closed-system frontier audits..." -- the repository HEAD at the start of
this investigation, predating any Phase 478 file). Every eligible source
file is identified by `(path, git blob hash at this commit)`, not by
filename or current working-tree content, because the working tree is not
guaranteed clean at execution time (`_work/` is untracked in the current
tree, unrelated to `tools/gsmg/`, but the principle is general). The
harvester reads each eligible file's content via its pinned blob hash
(`git cat-file` / `git show <commit>:<path>`), never via a live filesystem
read, so a later accidental edit to any of these files cannot silently
change what is harvested without also changing the discovery lock's
manifest of hashes.

Explicitly excluded regardless of content: every file introduced by Phase
478 itself (this protocol, the harvester, the manifest, the matcher, this
protocol's own audit doc), and the entire `ChatExport_2026-09-05` export
and `PROGRESS.md`. No candidate may originate from material created at or
after the moment the `{b,g}` hypothesis was observed.

## Eligible source-file inventory

`git grep -lI -i matrixsumlist 64f8063... -- 'tools/gsmg/*.py'` at the
cutoff commit returns 96 files (independently confirmed). This is the
discovery superset, not the final eligible set -- each file is then
classified exactly once, by manual read, into one of:

- **generator+oracle**: the file constructs one or more candidate byte
  strings in connection with `matrixsumlist` and submits at least one of
  them to one of this project's established cryptographic oracle
  entrypoints (`cb_common.aes_try_open_bytes`,
  `aes_try_open_stream_bytes`, `aes_try_open_ecb_bytes`,
  `aes_keywrap_try_open_bytes`, `raw_key_try_open`, or the `str`-argument
  wrappers that forward to them). Eligible for harvesting via interception
  (below), **and** requires a frozen invocation recipe (below) before it
  can be harvested for real.
- **structural/no-oracle**: the file discusses or manipulates a
  `matrixsumlist`-related construction but never submits anything to a
  recognized oracle entrypoint (e.g. a pure geometry/structure audit).
  Contributes zero candidates by this protocol's operational definition of
  "candidate" (below); recorded in the manifest's coverage notes as
  `zero_candidates: no oracle call`, not silently omitted from the file
  inventory.
- **direct-crypto-bypass**: the file submits password material to a raw
  cryptography-library call (e.g. `cryptography`/`pycryptodome` directly)
  without going through a recognized `cb_common` entrypoint. There is no
  manual-extraction path for these files -- a judgment-based, unscripted
  transcription of "what this file submitted" is exactly the kind of
  unlocked step the two-lock design exists to prevent. A
  `direct-crypto-bypass` file is either (a) given its own small, explicit,
  locked, reviewed adapter script before the discovery lock -- itself
  another `generator+oracle`-equivalent input with its own invocation
  recipe -- in which case it is harvested exactly like any other eligible
  file (see "Dedicated adapters" below), or (b) declared `excluded:
  direct-crypto-bypass, no adapter written` and contributes nothing. No
  third option. Likewise, a `generator+oracle` file whose historical code
  depends on a hardcoded, unpinned path outside the repository is either
  (a) given a dependency-remap adapter substituting the pinned snapshot's
  own tracked, independently byte-verified equivalent, or (b) `excluded:
  unpinned absolute-path dependency`.
- **reference-only**: `doc/*.md` / `tools/gsmg/findings/*.md` write-ups are
  not executed; they are used only to attach phase numbers and human-
  readable construction descriptions to candidates already harvested from
  their corresponding `.py` file, never as an independent candidate
  source. Every such reference file actually used for `phase`,
  `eligible`/`eligible_reason`, or `construction_label` attribution is
  itself pinned by `(path, git blob hash)` at the cutoff commit -- the
  same sweep (`git grep -lI -i matrixsumlist 64f8063... -- 'doc/*.md'`,
  76 files; `... -- 'tools/gsmg/findings/*.md'`, 81 files; both
  independently confirmed) is run and recorded alongside the `.py`
  inventory, so a fact used to decide `eligible: false` is itself
  traceable to a specific pinned document version, not to whatever that
  document currently says.

This classification, and its stated reason per file, is itself part of the
discovery-lock manifest.

## Invocation recipe (required for every `generator+oracle` file)

Several `matrixsumlist`-related scripts gate their oracle-submitting code
path behind `argparse` flags (e.g. `matrixsumlist_title_and_iteration_audit.py`
and `matrixsumlist_self_fold_consumer_audit.py` both require `--oracle`);
running such a file with no arguments does not skip the gate, it exits
through `argparse` before reaching the oracle call at all -- silently
producing a spurious "zero candidates" result indistinguishable, without
this recipe, from a genuine `structural/no-oracle` file. To prevent that,
classification of a `generator+oracle` file is not complete until it
carries a frozen recipe:

```yaml
mode: cli | call
argv: [<exact argv list -- for mode: cli, or for mode: call when the
  entry function itself parses sys.argv, e.g. via argparse>]
entry_function: <name, only if mode: call -- a function reachable without
  triggering `if __name__ == "__main__":`>
driver: <script filename, only if this file needs a dedicated adapter
  instead of the standard driver -- see "Dedicated adapters">
attr_overrides: {<module-level attribute name>: <repository-relative
  path string>, only if mode: call and this file needs a dependency
  remapped before entry_function runs -- see "Dedicated adapters">}
env: {<any required environment variables, else empty>}
timeout_s: <fixed per-file timeout>
```

`mode: cli` runs the file exactly as `python <file> <argv...>` would (the
harvester sets `sys.argv` accordingly before execution); use this when the
file's own command line, as documented or as read from its `argparse`
setup, is sufficient to reach the oracle call. `mode: call` instead
executes the file as an importable module (so its own
`if __name__ == "__main__":` block does *not* fire, sidestepping
`argparse` entirely) and then calls `entry_function()` directly -- use
this when no CLI invocation cleanly isolates the oracle-submitting code
from unrelated side effects (report-printing, unrelated sweeps in the same
`main()`, etc.), or when a dependency needs remapping first (below). A
file with neither a working `cli` recipe nor an identifiable entry point
is not given a recipe and is recorded as `excluded: no viable invocation
recipe`, not run with guessed arguments.

Recipes are written once, during classification, and become part of the
discovery lock -- they are not something the harvester infers at run time.

## Dedicated adapters

Two files this project's own house pattern doesn't reach are covered by
small, locked, synthetically-tested adapters rather than exclusion --
this is the last point before the discovery lock at which adding them is
methodologically safe, since a file added *after* seeing what candidates
exist elsewhere would undermine the discovery lock's own guarantee.

**Dependency-remap, via `attr_overrides` (generic driver feature).**
`matrixsumlist_title_and_iteration_audit.py` hardcodes `ARCHITECT_PDF_PATH
= Path("/home/loginwashere/projects/key-seeker/wordlists/matrix/
the-matrix-reloaded-2003.pdf")` -- a path outside this repository,
unpinned by the commit snapshot. Independently verified: that external
file and this repository's own tracked `wordlists/matrix/
the-matrix-reloaded-2003.pdf` are byte-identical (SHA-256
`2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4`, both
recomputed directly, not taken from either party's claim). The standard
driver's `mode: call` gained an `attr_overrides` field: after importing
the target (without running its `__main__` guard) and before calling
`entry_function`, it substitutes the named module-level attribute with
`<snapshot_root>/<repository-relative path>` -- so `ARCHITECT_PDF_PATH`
resolves to the pinned snapshot's own tracked copy, never the external
one, and every downstream candidate-generating call proceeds on the
target's completely unmodified historical code. Recipe:
`{"mode": "call", "entry_function": "main", "argv": ["--oracle"],
"attr_overrides": {"ARCHITECT_PDF_PATH":
"wordlists/matrix/the-matrix-reloaded-2003.pdf"}}`.

Implementing this surfaced a real bug, caught only by a synthetic test
deliberately designed to fail loudly, not by inspection:
`runpy.run_path`'s returned namespace is a **copy** of the dict the
target's functions were actually defined against -- mutating that
returned copy is silently invisible to every function in the target, which
keeps reading the original. The fix reaches through a function object's
own `__globals__` (`entry_func.__globals__[attr_name] = ...`) instead of
the namespace `run_path` returns. `test_without_attr_overrides_the_
unpinned_path_fails_closed` (confirming the fixture genuinely depends on
the override, not some coincidental other path) and
`test_attr_overrides_remaps_dependency_to_pinned_snapshot_file` both
pin this against regression.

**Local-oracle-boundary adapter, `phase478_adapter_cosmic_raw_digest.py`.**
`cosmic_raw_digest_checkpoint_audit.py` is the sole `direct-crypto-bypass`
file: it decrypts directly via `cryptography.hazmat`
(`Cipher(algorithms.AES(key), modes.CBC(iv))`) inside its own local
`decrypt(password, digest_name)` function, never through any recognized
`cb_common` entrypoint. A dedicated adapter script is registered via the
recipe's `driver` field (`{"driver":
"phase478_adapter_cosmic_raw_digest.py"}`) and copied into every snapshot
alongside the standard driver. It patches the target's own `decrypt`
(again via a function's `__globals__`, not `run_path`'s returned copy --
the same bug, caught by the same class of test: the fixture's own stub
`decrypt` raises `AssertionError` if the real one is ever actually
reached) to a pure recorder capturing `(password, digest_name,
caller_file, caller_line, caller_function)`, no AES, no candidate
re-hashing. It then reproduces -- does not reinterpret -- exactly two
pieces of the file's own historical logic, called directly rather than
through `audit()`/`main()`: the two default password forms
(`xor_sha256_digests()`'s raw 32 bytes and its hex64 rendering, each
historically submitted under both `digest_name` values), and the complete
frozen 210-member "published uniqueness family"
(`published_uniqueness_family_report()`, `7 x 5 x 6` over
`P5/P6/P7_CANDIDATES`). `audit()` itself is deliberately never called: it
also runs `downstream_report()`/`matrix_report()`/`compressed_p2pkh()` on
the decrypted payload, which would raise on this adapter's necessarily
empty stub payload (invalid EC scalar derivation, empty-bitstream
indexing) -- and since `audit()` calls `published_uniqueness_family_
report()` only after that chain, a crash there would silently drop all
210 uniqueness-family candidates, not just fail loudly. The file's own
internal `hashlib.sha256` calls inside `xor_sha256_digests` (hashing each
of the 7 TOKENS to build the XOR) are historical candidate-CONSTRUCTION
logic, not Phase 478 scoring, and are left untouched.

Both adapters are self-tested against synthetic fixtures (never the real
files) before being registered, exactly like the standard driver, and
their scripts' hashes are pinned in the discovery lock alongside the
standard driver's.

## Zero-candidate policy

The operational definition of "candidate" below (bytes actually submitted
to an oracle) has a real consequence: some historical files gate their
own AES escalation behind a condition that a clean, faithful run of the
exact locked recipe can legitimately fail to satisfy, producing zero
candidates without anything being broken. Zero candidates is fatal for
every locked file *except* the exact set carrying a locked
`zero_candidate_policy`, under exactly one of two frozen reasons -- found
by running every one of the 23 locked files for real and reading each
zero-candidate result's own control flow, never assumed or extrapolated:

- **`historical_significance_gate_closed`** --
  `adjacent_diff_sweep.py`, `digraphic_sweep.py`,
  `native_prime_zeroing_sweep.py`, `prefix_boundary_sweep.py`. Each gates
  AES escalation behind a frozen, deterministic shuffle-based
  significance test (fixed seed, fixed trial budget); run against real
  DBBI/FAED data under the exact locked recipe, none of the four gates
  clears (real p-values, all comfortably above their own 0.05 threshold,
  captured verbatim as each result's `gate_witness`). This is the file's
  own historical logic working as designed, not a broken recipe.
- **`historical_escalation_never_executed_no_frozen_threshold`** --
  `faed_monoalphabetic_sweep.py` alone. This file's escalation requires an
  explicit `--escalate-if-above <threshold>` CLI value with no default.
  Per Phase 43 (`tools/gsmg/findings/P00043.md`, independently
  re-verified, not taken on trust), no historical run of this file ever
  crossed that gate, and no calibrated threshold was ever frozen -- Phase
  43's own verdict rests entirely on a separate, complete 100-trial
  token-preserving null test (`real=-2544.1`, `null median=-2539.0`,
  `p=0.63366`) that never requires running the AES escalation at all.
  Deriving a threshold now, solely to force this file into the positive
  bucket, would be a **new** Phase 478 candidate-generating experiment
  outside the closed historical harvest -- not a lock formality -- and is
  deliberately not done. This file's zero is authorized on the historical
  record exactly as it stands.

A `zero_candidate_policy` never excuses a non-`"ok"` status -- a crashed
or timed-out run on one of these five files is exactly as fatal as on any
other locked file. The runner verifies the set of policy-granted paths
equals this five-path set exactly, and that each one's `reason_code`
matches the one it is actually assigned above, before accepting any
result as authorized. This exact set was not the protocol's original
guess: discovery of the first two files' shared pattern in review led
directly to running the *other* 21 for real, which is what surfaced the
other three -- two more `historical_significance_gate_closed` cases and
the one `historical_escalation_never_executed_no_frozen_threshold` case.

## Operational definition of "candidate"

A **candidate** is the exact byte string that a `generator+oracle` file, at
the cutoff commit, actually passed as the `passwd`/`keystr` argument to a
recognized oracle entrypoint, in a code path connected to that file's
`matrixsumlist` handling. Not every string a script's generator function
could in principle emit -- only strings the historical code, as written,
actually submitted for testing. This is deliberately the narrower of the
two definitions considered (raw generator output vs. actually-submitted
oracle input) because it is mechanically unambiguous: no judgment call is
needed about which generator outputs "count," and a script that generates
336 candidates internally but only ever tests a filtered subset of them
contributes exactly that subset, not the internal superset. It may still
run into the thousands across the classified file set (KDF/cipher-variant
fan-out happens inside `cb_common`'s own oracle functions, over a single
captured argument, and is invisible to the harvester -- it is never a
source of multiplication here); hashing thousands of short strings is
computationally trivial, so this costs nothing at scoring time.

**Extraction mechanism**: for each `generator+oracle` file, the harvester
runs that file's frozen invocation recipe (above) in a subprocess against
a complete repository snapshot materialized from the pinned cutoff commit
(`git archive <commit> | tar -x` into a fresh temporary directory, once
per harvest run, deleted afterward) -- not merely the target file. This
matters because a target file's own imports (`cb_common`, `data`, shared
wordlist/data-file reads relative to `__file__`) must themselves come
from the pinned commit; running only the target file against the live
working tree's `cb_common`/`data` would silently mix pinned and unpinned
code. This bounds what the target file can *import*, not what it can
*do*: the subprocess is a plain OS process, not a sandbox -- it can still
read or write an absolute path outside the snapshot, or make a network
call, if its own code does so. Classification therefore includes an
explicit side-effect review per file (does it read/write any absolute
path, does it perform any network call) as part of assigning its
invocation recipe; a file whose review turns up either is not given a
plain `cli`/`call` recipe without first neutralizing it (e.g. an
environment override, or exclusion). Every recognized `cb_common` oracle
entrypoint is monkeypatched, inside that same isolated subprocess, to a
pure recorder -- append the candidate bytes and its originating call
site's file/line/function (walked from the call stack past cb_common's
own str-argument wrapper frames to the frame that actually invoked them,
not merely "which entrypoint name") to a list, perform no cryptography,
return a fixed negative result immediately. Recipe `mode: cli` then runs
the file exactly as its own command line would; `mode: call` imports it
without triggering its `__main__` guard and calls the named entry
function. No new candidate logic is written; the harvester only observes
what already-existing code, executed exactly as it was written, already
does.

**Exit-status discipline**: a file's run is `ok` only if it completes with
no exception, or exits via `SystemExit(0)` / bare `sys.exit()`. Any other
`SystemExit` (a nonzero code, or a non-integer code such as an `argparse`
usage-error message) is `harvest_failed`, exactly like an uncaught
exception -- an `argparse` exit code of `2` from a missing required flag
must never be recorded as a successful zero-candidate run, since that
would be indistinguishable from a genuine `structural/no-oracle`
classification. Candidates captured before a failing exit or exception are
still retained (a script that fails on its 40th candidate after
successfully submitting 39 has still submitted those 39).

**Determinism**: every harvester subprocess runs with `PYTHONHASHSEED=0`
and a `PYTHONPATH` cleared of anything from the live tree, so encounter
order is not an artifact of hash randomization. Within the manifest,
files are sorted by path, candidates within a file are sorted by
`bytes_b64` (lexicographic), and call sites within a candidate are sorted
by `(caller_file, caller_line)` -- the manifest is a canonical, byte-stable
function of the pinned inputs, not of iteration order.

## Manifest schema

One entry per distinct `(source_file, byte string)` pair (the same bytes
recurring across files are recorded once per originating file, since
provenance differs; exact-duplicate bytes from the same file collapse to
one entry). Each entry:

```yaml
bytes_b64: <candidate bytes, base64, exact -- never re-encoded or normalized>
source_file: <path>
source_blob_sha: <git blob hash at the cutoff commit>
call_sites: [{entrypoint: <name>, caller_file: <path>, caller_line: <int>, caller_function: <name>}, ...]
phase: <phase number if the source file/doc identifies one, else "unknown">
construction_label: <one-line human description of how this string was built>
transformation: <normalization already applied by the source code itself, e.g. "raw", "sha256-hex-of-literal", "case-folded", "LF-stripped" -- verbatim from the source, never invented here>
eligible: true | false
eligible_reason: <required when eligible: false -- the documented retraction/supersession this project's own docs already state, e.g. "GSMG_MATRIXSUMLIST_CHECKPOINT.md: superseded, circular H+initials rebus", or "excluded: direct-crypto-bypass, no adapter written">
```

**No `sha256` field.** The manifest deliberately does not carry a
per-candidate digest. `SHA256(bytes)` is trivial to compute from
`bytes_b64` alone, by anyone, at any time -- this is not a secrecy
mechanism, and does not pretend to prevent the match from being
discovered early by someone who chooses to compute it. What it protects
is procedural: the harvester itself (the discovery-side pipeline that
this protocol locks) never performs the scoring precursor, so *this
process's own output*, as produced and reviewed between the two locks, is
never a scored result -- only a candidate inventory. `bytes_b64` is
sufficient for deduplication, and the manifest file's own SHA-256 (pinned
at the oracle lock) protects its integrity as a whole. Every candidate's
digest is computed for the first time, by this process, only after the
oracle lock, by the matcher, against the locked manifest.

Retracted or superseded constructions are harvested and recorded with
`eligible: false` and their documented reason, never dropped silently --
per this project's own discipline, a judgment-based exclusion must remain
auditable in the record, not disappear from it. `eligible: false` entries
are excluded from scoring (below) but included in every count reported in
the audit doc.

## Matching test

For each `eligible: true` manifest entry, compute `SHA256(bytes).hexdigest()`
(64 lowercase hex characters, the standard rendering already used
throughout this project), then compute that digest's own equality pattern
with the identical `equality_pattern` function frozen above, and compare it
character-for-character to DBBI's frozen pattern. Each candidate is hashed
and scored exactly once; no additional normalization axis (case, whitespace,
double-hashing, alternate encodings) is introduced beyond what the source
code itself already applied, per the historical-cutoff principle -- this
tests what this project already built, not what this project could build.

## Stop rule

Only a full 64-position exact match to
`01234556728966286abc61c88b48de3086dd501d5557d6bab5605233df7bbb96` counts as
positive. Any partial match, near-miss, or match under a relaxed criterion
is negative for that candidate; there is no threshold, no top-N reporting
beyond the single best-matching-position count for descriptive purposes,
and no second attempt with a loosened rule.

**Combinatorial specificity of a hit.** A uniformly random 64-character
lowercase-hex string reproduces one specific, fully-specified 16-class
partition of 64 positions with probability
`16! / 16**64 = 20,922,789,888,000 / 16**64 ~= 1.807e-64`. This is the
count of raw hex strings that canonicalize to the target pattern (exactly
`16!`, one for **any** of the `16!` possible bijections from the 16
abstract equality-classes to the 16 concrete hex-digit values -- each
bijection substitutes a distinct hex digit for every class and yields one
matching raw string, so all `16!` of them succeed, not just one specific
assignment) divided by `16**64` equally likely raw strings. Even a manifest
in the low
thousands of eligible candidates keeps the total accidental-match budget
around `1e-60`. This is described as **overwhelming combinatorial
specificity**, not as unfalsifiable proof: an exact hit would still require
(a) independent recomputation of the match from the pinned manifest and
DBBI pattern, by a process separate from the one that first reported it,
(b) verification that the matched candidate's manifest entry is
`eligible: true` with intact provenance back to its originating phase, and
(c) recovery and sanity-check of the implied 16-symbol bijection (does it
map to a coherent hex digest, and does that digest then need to be
consumed by something -- this protocol does not itself specify what a
confirmed digest would be used for).

## Postselection

`{b,g}` was selected for this test because it is the unique pair, among all
36 escape-pair hypotheses on DBBI's alphabet, producing the `(64, 16)`
shape -- not chosen freely and not the only pair examined. The worst-case
simple multiplicity correction for having examined all 36 pairs before
settling on one is a factor of 36, which does not materially weaken an
exact match at `~1.8e-64` (`36 x 1.807e-64 ~= 6.5e-63`, still overwhelming).
It is recorded here as a limit of interpretation, not folded into the
stop rule.

## Sequencing

1. This protocol is frozen (this document).
2. Harvester script is written and self-tested against synthetic fixture
   files with known, hand-verified oracle-call sites, known expected
   captured candidates, `argparse`-gating behavior, and isolated-execution
   behavior -- never against any real `tools/gsmg/*.py` file at this
   stage.
3. Eligible source-file inventory is generated (`git grep` superset over
   `.py` and reference `.md` files at the cutoff commit), manually
   classified per file with reasons, and every `generator+oracle` file is
   given a frozen invocation recipe (or `excluded: no viable invocation
   recipe`). Every `direct-crypto-bypass` file is either given a locked
   adapter or `excluded: direct-crypto-bypass, no adapter written`.
4. **Discovery lock** is issued: protocol hash, harvester hash, every
   adapter script's hash, per-file classification, recipes, and blob
   hashes (`.py` and reference `.md`), cutoff commit.
5. Harvester is run for real against every `generator+oracle` file,
   producing the manifest.
6. Manifest is inspected structurally only (counts, provenance
   completeness, eligibility-reason completeness, encoding sanity) --
   no candidate is hashed or pattern-matched at this stage.
7. Matcher script is written and self-tested against synthetic fixtures
   (planted positive and negative manifests), independent of the real
   manifest's content.
8. **Oracle lock** is issued: manifest hash, DBBI pattern, matcher hash.
9. Matcher is run once against the locked manifest. Result is reported
   exactly as produced; no re-run with adjusted scope.

## Bounding the result

A miss (the expected and default outcome) closes exactly:

> DBBI `{b,g}` as a monoalphabetically-substituted lowercase-hex SHA-256
> digest of every `eligible: true` byte string in the locked harvested
> manifest.

The locked manifest's executable universe is 23 `generator+oracle`
inputs, all fully accounted for, none excluded: 18 produce real
candidates (16 via the standard driver plus `matrixsumlist_title_and_
iteration_audit.py` and `cosmic_raw_digest_checkpoint_audit.py`, both
covered through their own dedicated adapters above), and 5 legitimately
produce zero under the frozen `zero_candidate_policy` above.

It does not close: any meaning of `matrixsumlist` this project has not
already constructed as an oracle-submitted candidate; any
`direct-crypto-bypass` file left `excluded` for lack of a locked adapter
(see Eligible source-file inventory -- there is no manually-extracted
middle ground); any `generator+oracle` file left `excluded: no viable
invocation recipe`; any normalization not already present in the source
code (double-hashing, alternate case/whitespace forms, non-hex or
uppercase-hex rendering); the `{b,e}` segmentation or any other escape
pair; or any non-digest reading of DBBI. Phase 477B (raw-digit VIC/ADFGVX
order over FAED) and the P32TRAILING no-padding-oracle crypto-profile
widening remain queued, deprioritized behind this phase per explicit
instruction, untouched by this protocol.

## Required checks

- `equality_pattern` self-test reproduces DBBI's frozen `{b,g}` pattern
  from `tools/gsmg/data.py`'s `DBBI` constant, independent of any value
  copied from `PROGRESS.md`; a separate check confirms a candidate digest
  using fewer than 16 distinct hex digits produces a well-defined,
  non-matching pattern rather than being treated as a special case.
- Harvester interception self-test: a synthetic fixture script with known
  oracle-call sites yields exactly the expected captured candidate set,
  byte-for-byte, including recorded `call_sites` matching the fixture's
  actual caller file/line/function. KDF/cipher-variant fan-out happens
  inside `cb_common`'s own oracle functions (iterated internally, over a
  single captured argument) and is invisible to the recorder by
  construction; the dedup case actually exercised is identical bytes
  submitted from two or more genuinely distinct call sites, which must
  collapse to one candidate while preserving every distinct site, versus
  one call site invoked repeatedly (e.g. inside a loop), which must not
  inflate the site list.
- Harvester isolation self-test: a fixture importing a sibling module whose
  content differs between a "live" location and a "pinned" location must
  resolve against the pinned one when run inside the harvester's isolated
  snapshot, even when a same-named live module is reachable elsewhere --
  proving the execution environment, not merely the target file, is
  pinned.
- Harvester recipe self-test: a synthetic `argparse`-gated fixture (i)
  reaches its oracle call under `mode: cli` with the correct `argv` and
  (ii) is `harvest_failed` (not a false zero-candidate `ok`) under
  `mode: cli` with no `argv`, via a `SystemExit(2)`; and (iii) reaches its
  oracle call under `mode: call` via a plain entry function without
  needing any `argv` at all.
- Exit-status self-test: `SystemExit(0)` and a bare `sys.exit()` are `ok`;
  `SystemExit(1)`, `SystemExit(2)`, and `SystemExit("some message")` are
  all `harvest_failed`, with any candidates captured before that exit
  still present in the result.
- Dependency-remap adapter self-test: `attr_overrides` correctly
  substitutes a pinned-snapshot file for a fixture's own unreachable
  hardcoded path, with a companion test confirming the SAME fixture
  fails closed (a real `FileNotFoundError`, not a false pass) absent the
  override -- proving the override, not some other path, is what made it
  work.
- Local-oracle-boundary adapter self-test (`phase478_adapter_cosmic_raw_digest.py`):
  against a synthetic stand-in for `cosmic_raw_digest_checkpoint_audit.py`
  whose own `decrypt()` body raises if ever actually reached, the adapter
  must capture every default-form and uniqueness-family candidate (with
  the exact deduplication expected when a family member coincides with a
  default form) while the target's real `decrypt()` never executes --
  `status: ok`, not `harvest_failed`, is itself the pass condition.
- Both new adapters were built against a real, reproducible bug, not a
  hypothetical one: `runpy.run_path`'s returned namespace is a copy, and
  mutating it is silently invisible to the target's own functions, which
  keep reading the dict they were actually defined against
  (`entry_func.__globals__`). The synthetic tests above caught this
  before any real file was touched; both adapters go through
  `__globals__`, never the returned namespace, for every mutation.
- Harvester never executes real cryptography: recorder functions perform
  no AES/SHA computation beyond what the manifest schema itself requires
  post-hoc; wall-clock cost of a full harvest pass over the classified
  file set is bounded and reported.
- No network access, no modification of any pinned blob's source file
  (the isolated snapshot is a disposable copy), no address derivation, no
  Bitcoin endpoint contact anywhere in this phase.
- Manifest completeness: every `generator+oracle`-classified file with a
  recipe contributes at least one manifest entry or is explicitly flagged
  `harvest_failed` with its exception -- never silently absent. Every
  reference document actually used for `phase`/`eligible`/
  `construction_label` attribution is listed with its own pinned blob
  hash.
- Determinism: re-running the harvester against the same pinned commit,
  the same file classification, and the same recipes reproduces an
  identical manifest (same sorted content, same hash), independent of
  `PYTHONHASHSEED` before it is fixed.

## Limits of the conclusion

This phase tests one escape pair (`{b,g}`), one hash construction
(single SHA-256, lowercase hex, exactly as historically applied), and one
closed candidate universe (byte strings this project has already
mechanically submitted to a recognized oracle entrypoint in connection
with `matrixsumlist`, as of the pinned cutoff commit). It says nothing
about `{b,e}` or any other pair, about FAED, about non-hex or
uppercase-hex digest renderings, about double-hashed or otherwise
re-transformed digests, about candidates this project only ever
structurally discussed without oracle-submitting, or about any
`direct-crypto-bypass` or recipe-less file left `excluded` for lack of a
locked adapter or invocation recipe. The
36-pair postselection (see above) is a real but small correction that does
not threaten the interpretation of an exact hit. No password material,
address derivation, or Bitcoin endpoint check is performed at any point in
this phase; only DBBI's own already-public segmentation and this project's
own already-constructed candidate strings are touched.

## Development notes (non-scientific, for the record)

Two harmless documentary discrepancies from this protocol's own drafting
process, recorded rather than silently smoothed over:

- This document's header read "draft; discovery lock not yet issued"
  until the discovery lock it now points at was actually issued in a
  later revision of this same file.
- The synthetic self-test suite was reported as "17/17 passing" at the
  point the harvester and its first two synthetic-only tests existed;
  by the time the two dedicated adapters (and the path-mapping and
  wrapper-provenance regression tests a review round added before that)
  were built and locked, the same suite runs 23/23. Neither number was
  wrong for what existed at the moment it was reported -- the suite grew
  across the build, the reports did not silently omit tests that already
  existed at each point.

## Amendment history

**First discovery lock**, SHA-256
`649c4f9710c8ddae2c26b2c92d22d51d878a59d0d4c7cbd1c058e050c50eb039`,
preserved here by reference (not by keeping the file itself) rather than
silently overwritten.

**What happened between the first lock and the replacement.** Attempting
the real, locked harvest under the first lock surfaced a genuine
capture-completeness gap (`concurrent.futures.ProcessPoolExecutor`-based
files silently losing every candidate a forked worker submitted), a
dependency-isolation gap (`page_structure_audit.DEFAULT_HTML` walking
outside the repository via `__file__`-relative arithmetic), several
under-timed recipes, two broken recipes missing a required CLI argument,
and the four additional `zero_candidate_policy` cases described above.
Diagnosing and fixing all of this necessarily involved running real
targets against the real pinned commit, repeatedly, while the fixes were
built and verified. This is disclosed plainly rather than left implicit:

> Implementation corrections were driven solely by capture completeness,
> dependency isolation, multiprocessing visibility, runtime, and
> historical gate behavior; no Phase 478 digest-match statistic was
> computed or inspected.

This is methodologically harmless specifically because the first
discovery lock had already closed the 23-file candidate universe before
any of this diagnostic execution began, and at no point did any of it
compute a candidate's SHA-256 or equality pattern -- the oracle lock,
which alone would expose that comparison, was never issued against the
first lock and is not issued against this one until the harvest below
completes and is inspected structurally only.
