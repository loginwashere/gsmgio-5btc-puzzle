# GSMG Cosmic Duality — Unexplored Investigation Paths

Date: 2026-07-23. Updated 2026-07-24. Status as of end of day: dual-ternary, Second Path (instruction
program), Third Path (hash duality — after a provenance re-audit, see its section),
the "Alternative Target Coupling" path, and the Fourth Path (raw page structure) are
all closed or narrowed and independently re-verified. A later same-day addition,
"Cross-Phase Review," claimed a new
cross-phase cryptographic bridge — **independently checked and debunked as
apophenia** (see that section's correction) using the same null-model rigor that
already falsified the community's "matrixsumlist triangle" claim; its AES-oracle
negative result stands, but the narrative around it does not.

The 2026-07-24 follow-up below reopens a small number of **model-changing**, bounded
paths. These are not more keyword or transform expansion. They reinterpret the
25 checkerboard codes, or execute `matrixsumlist` in a way not covered by the
existing instruction pipeline.

## Assessment

The investigation has largely saturated the **keyword/checkerboard search space**, not
the puzzle itself.

The most important existing finding is that the validated Phase 3.2.2 alphabet was
constructed by interpreting a riddle, rather than by passing a keyword through a
generic alphabet generator. Consequently, larger dictionaries and more keyword
combinations are unlikely to solve the endgame.

No credible, independently reproducible public solution was found. Public GitHub issues
contain multiple solution claims, but several depend on invalid cryptographic
verification, such as accepting random valid AES padding or repairing arbitrary binary
until it resembles another file format.

## Reopened Paths After the Full Audit (2026-07-24)

### 1. Dual-Quinary Decomposition After Checkerboard Segmentation

This is the strongest new path.

The earlier dual-ternary work factors each raw `a`-`i` symbol into a 3×3 coordinate.
It does **not** factor the checkerboard's 25 complete codes into a 5×5 coordinate.
Those are different representations.

For an ordered escape pair, the native checkerboard has exactly 25 code types:

```text
7 single-symbol codes + 9 first-escape codes + 9 second-escape codes
```

Under `{b,e}`, `dbbi` segments into **63 complete codes** with 19 distinct code
types. Under `{g,i}`, `faed` segments into **436 complete codes** and uses all 25
code types; under `{b,e}` or `{h,e}`, it produces 469 codes and also uses all 25.
The use of every code type makes a base-25/5×5 payload interpretation materially
different from treating `faed` as raw base 9.

Bounded first pass:

1. Assign each complete code its natural checkerboard index `0..24`, independently
   of any guessed plaintext alphabet.
2. Factor that index into `(row, column)` over a 5×5 square.
3. Test row, column, interleaved, sum, difference, equality, reverse, and mirror
   streams.
4. Pack as whole-base-5, whole-base-25, fixed five-bit units, and byte-aligned
   coordinate streams.
5. Check file/compression signatures, entropy, printable runs, and AES passphrase
   forms.
6. Compare every ranking statistic against shuffled **code-token** streams with
   the same multiset before interpreting any apparent word or signature.

This should be cheap: only three motivated unordered escape hypotheses, both escape
orders, two board topologies, and a small fixed transform set. Do not combine it
with a large keyword corpus unless the content-agnostic gate produces a real anomaly.

Stop if no output survives a multiple-testing-corrected shuffle baseline and no
recognized byte signature appears.

#### Implemented gate and verification correction

`tools/gsmg/dual_quinary_sweep.py` implements this path. Its first reported
`dbbi` result (`p≈0.020`, then `p≈0.0219` with seed 12345/10,000 trials) was
reproducible for the code as written, but an independent code audit found that
the null shuffled raw `a`-`i` symbols and then re-segmented them. That does not
preserve the complete-code multiset required by the plan. The same audit also
found that “whole base-25” stored each index as one byte rather than converting
the whole radix-25 integer.

The implementation now:

- shuffles complete checkerboard codes separately for each motivated escape
  hypothesis;
- rejects dangling escapes instead of truncating them;
- implements actual whole-base-5 and whole-base-25 integer conversion;
- retains direct index bytes under an accurate label;
- supports deterministic parallel shuffle trials.

Corrected max-statistic results:

| Target | Seed | Trials | At least as good | Empirical p |
|---|---:|---:|---:|---:|
| `dbbi` | 12345 | 10,000 | 2,305 | **0.23058** |
| `faed` | 12345 | 2,000 | 1,902 | **0.95102** |

The same unreadable `dbbi` candidate remains the top printable output, but it is
ordinary under the correct code-token null. This path is therefore negative and
closed; the earlier `p≈0.02` anomaly is retired as a null-model implementation
error, not retained as evidence.

### 2. `matrixsumlist` as a Self-Derived Permutation

The implemented instruction pipeline computes row/column sums and turns them into
candidate text or selectors over the known Phase 3.2.2 answer. The existing
transposition sweeps use literal keys such as `matrixsumlist`. Neither applies the
**sum list itself as the permutation key over the ciphertext that generated it**.

There are two exact, clue-supported matrices:

- raw `dbbi`: 91 symbols = 7×13 or 13×7;
- `{b,e}`-segmented `dbbi`: 63 complete codes = 7×9 or 9×7.

For raw `dbbi`, `a=0..i=8` gives column sums:

```text
21,31,35,30,17,26,8,27,28,32,19,26,31
```

and the stable ascending column order:

```text
6,4,10,0,5,11,7,8,3,1,12,9,2
```

Adding one to every symbol changes the sums but not this order. That makes the
permutation stable across the usual zero/one-based ambiguity.

Bounded test:

1. Derive row and column orders from raw 7×13 and segmented 7×9 forms.
2. Apply ascending/descending row, column, row-then-column, and inverse
   permutations to `dbbi`.
3. Repeat only the corresponding exact-factor operations for `faed` (15×38 and
   38×15), without inventing arbitrary dimensions.
4. Feed transformed streams through existing checkerboard and direct-byte paths.
5. Compare language/AES-candidate counts with shuffled-symbol matrices processed
   by the identical procedure.

The permutation-corrected period scan run during this review found `dbbi`'s best
period at 13 (`z=2.52`) but a max-statistic empirical `p≈0.34`; the dimension is
therefore clue-motivated, not statistically discovered. For `faed`, the best
period had corrected `p≈0.80`. Any output from this path still needs independent
validation.

Stop after the exact matrix factors and their inverses. Do not generalize to
arbitrary matrix dimensions.

### 3. Digraphic Cipher Over the 25 Code Alphabet

Existing checkerboard solvers assume each complete code maps independently to one
plaintext letter. Autokey and chain-addition add symbol-wise keystreams, but no
current script tests a second **digraphic** layer over the 25 code symbols.

A 25-symbol alphabet plus the explicit words `matrix` and `duality` gives bounded
motivation for Playfair, Two-square, Four-square, or Bifid-style mechanisms. This
would explain why monoalphabetic quadgram hill climbing fails even if checkerboard
segmentation is correct.

Keep this constrained:

- use only `{b,e}` for `dbbi` and `{g,i}`/`{h,e}` for `faed`;
- use exact clue phrases and verified screenplay extractions as square keys;
- test both pair alignments and only beginning/end padding for odd token counts;
- calibrate recovery and false-positive rates on synthetic ciphertexts of the same
  length before trusting English scores;
- send only statistically exceptional decodes to AES.

Stop after the four standard 5×5 families and the bounded clue-key set. A general
dictionary-keyed Playfair sweep would repeat the already-saturated keyword problem.

**Status (corrected 2026-07-24): bounded path tested negative.** The first
implementation's odd-ciphertext filler handling and lack of synthetic calibration
were invalid and are retired in `tools/gsmg/FINDINGS.md`. The corrected sweep:

- treats odd complete-code counts as incompatible with standard pair ciphers
  instead of injecting a ciphertext filler;
- tests Bifid periods 5, 7, 9, 13, and full-message;
- tests horizontal/vertical Two-square with both same-line conventions;
- passes independent round trips and end-to-end synthetic recovery controls for
  all four families;
- detects every synthetic control at the 500-trial permutation floor (`p=0.002`);
- finds no real exception (`dbbi` Bifid-only `p=0.50590`; `faed` full bounded
  scope `p=0.94261`, 5,000 trials each).

Thus standard pair ciphers are structurally incompatible with `dbbi`'s odd
63-code stream absent a clue-supported missing-token rule, and the valid Bifid
scope is negative. The complete corrected methodology and audit trail are in
Phase 21 of `tools/gsmg/FINDINGS.md`.

### 4. Calibrated Recovery of the Raw Checkerboard Alphabet

The old quadgram solver's negative score is not a proof that `dbbi` is not a
checkerboard ciphertext. `{b,e}` yields only 63 plaintext symbols and 19 observed
code types, a difficult regime for blind substitution recovery.

Before spending more hill-climbing compute, build a calibration harness:

1. Generate English samples of exactly 63 characters from Matrix/book/chat corpora.
2. Encode them with random 25-symbol checkerboards while matching `dbbi`'s observed
   code-use pattern as closely as possible.
3. Run the current solver unchanged and measure exact/near-exact recovery rate.
4. Add word-level scoring or simulated annealing changes only if the baseline fails.
5. Re-run real `dbbi` only after the improved solver reliably recovers synthetic
   controls at this length.

This path is valuable even if negative: it determines whether the prior hill-climb
actually had power to reject the model.

### 5. Recover Missing Primary Evidence

The book transcription still has a proven physical gap at pages 57-58, likely a
closed gatefold, plus a few low-priority single-page audit gaps. This is the only
known source material that is genuinely unavailable to the current text-mining
pipeline.

If the physical book is accessible, photograph the gatefold fully opened, hash the
new images, transcribe them into a separate file, and run only the established
content-word and exact-phrase candidate pipeline. Also preserve provenance for any
original 2022 Telegram image if it becomes available.

This evidence-recovery path outranks speculative large brute-force runs, but the
book's already-reviewed ordinary content means expectations should remain modest.

### 6. Broadened Cipher/KDF Oracle + Staged SALPH→COSMIC Pipeline

**Status (2026-07-24): implemented, closed negative on curated candidates.**
See FINDINGS.md Phase 22 for full detail. Every prior sweep in this project
tested candidates only against AES-128/256-CBC with the legacy MD5/SHA1/SHA256
`EVP_BytesToKey` derivation. `Salted__` identifies the OpenSSL container, not
the cipher/KDF, so a correct passphrase under a different cipher would have
been indistinguishable from a wrong one in every prior result.

Added (opt-in, additive -- default oracle behavior for every existing sweep
script is unchanged): AES-192-CBC, 3DES-CBC (3-key/2-key/single-key), and
PBKDF2-HMAC-SHA256 at OpenSSL's fixed default of 10000 iterations (not an
open-ended `-iter` sweep, which has no principled bound). Also added a staged
pipeline that, given a SALPH plaintext, automatically derives and tests
next-stage passphrase forms against COSMIC (the "derive password → open
SALPH → hash its answer → open COSMIC" page-grammar reading) -- necessarily
dormant since SALPH has never been opened, so validated against a synthetic
scenario instead.

Ran all 18 of this project's small, already-curated candidate lists (568
unique candidates) through the broadened oracle: 14,715 keystring attempts,
~530,000 total decrypt attempts, **0 hits, 0 weak candidates**. This closes
the cipher/KDF blind spot for existing curated material; it does not rule out
the broadened space against the raw mined corpora (not yet rechecked, by
design -- see Phase 22) or a non-default PBKDF2 iteration count.

### 7. Exact Command-Provenance Reconstruction

**Status (2026-07-24): implemented (narrowed scope), closed negative.** See
FINDINGS.md Phase 23. Narrowed from open-ended "reconstruct the exact
command" (no principled stopping point if no verbatim source exists) to:
grep the raw, unnormalized mined chat archive directly for real commands a
community member actually typed, since `last_command.txt`'s normalized
approximations already confirmed the gap.

Notable non-obvious find: a chat-posted base64 fragment is byte-for-byte a
real prefix of this project's actual SALPH ciphertext, confirming two nearby
password guesses were genuine historical attempts against the real target
(both self-reported as bad-decrypt in chat). A separate, different base64
fragment in the same thread ("the unsolved one from the previous stage")
matches neither SALPH, COSMIC, nor the solved Phase 3.2 blob at first glance
-- its provenance was triaged to a conclusion and it was added as a
confirmed third target; see item 8.

13 real, non-placeholder command-derived literals tested against both blobs
under the full broadened cipher/KDF coverage from item 6: **0 hits.**

### 8. Third Target Confirmed: P32TRAILING (formerly "the untracked base64 fragment")

**Status (2026-07-24): provenance CONFIRMED, added as a third target, recheck closed negative.** See FINDINGS.md Phase 25. A base64 fragment flagged during path 3 (item 7) as "matches no known blob" was triaged to a conclusion per an explicit protocol: decode exact bytes -> inspect chat context -> search for overlapping fragments -> compare against every recorded blob -> check external sources -> add only if provenance is established.

Result: real, and already well-known to the wider public solving community (just not previously tracked by this project). Confirmed via the *official* `puzzlehunt/gsmgio-5btc-puzzle` README and the actively-maintained fork `HosterjackAGV/gsmg-5btc-puzzle`, which calls it **`p32_trailing`** -- an 80-byte OpenSSL blob (salt `b45a5e3d827593ca`) embedded at the end of the already-solved Phase 3.2 plaintext, distinct from SALPH/COSMIC. That fork's own extensive catalog (~1.5M+ attempts) reports it still unsolved, and independently flags the same "universally assumed AES-256-CBC" blind spot this project's own Phase 22 found separately -- a striking independent corroboration.

Added as `cb_common.BLOBS["P32TRAILING"]`. Re-ran the path 3 command-provenance candidates (13) and the path 1 curated recheck (568 candidates x 18 extended cipher/KDF variants) against it: **0 hits both.**

The same external research surfaced a **fourth** blob, `urlblob` (salt `74c974e3f92e64b5`, found via a Wayback/CDX-archived gsmg.io URL). The AES-KEY-WRAP cipher-mode hypothesis also flagged by that research was pursued next; see item 10. `urlblob`'s own provenance verification and sweep is item 11.

### 9. Prefix/Header Boundary Hypothesis

**Status (2026-07-24): implemented, closed negative.** See FINDINGS.md
Phase 24. `dbbi`/`faed` are literally the first 4 symbols of their own
streams (a confirmed, legitimate naming mnemonic per doc/GSMG_PUZZLE.md) --
untested until now whether those same 4 symbols are ALSO functionally
special (header/selector) within the cipher itself.

Tested two bounded mechanics: discard the prefix as a header (payload =
`stream[4:]`, decoded under existing keyword alphabets) and use the prefix
itself as the key (payload = `stream[4:]`, alphabet seeded from the prefix).
Both passed synthetic-control recovery calibration (true plaintext recovered
as top scorer in every configuration tested) before the real gate. Real
2000-trial shuffle gate: `dbbi` p=0.654, `faed` p=0.511 -- neither
exceptional. **Closed negative** for both tested mechanics.

### 10. AES Key Wrap (RFC 3394 / RFC 5649) Cipher-Mode Hypothesis

**Status (2026-07-24): implemented, closed negative.** See FINDINGS.md
Phase 26. Flagged by item 8's external corroboration: an independently-
maintained fork's own attempt catalog lists `-id-aes256-wrap-pad` as an
untested cipher-*mode* hypothesis for P32TRAILING -- structurally different
from every prior sweep's CBC assumption (no CBC IV, wraps key material
rather than arbitrary plaintext, and its own built-in integrity check rather
than CBC's PKCS7-padding heuristic).

Tested both RFC 3394 and RFC 5649/padded separately under both strict RFC
default AIVs and OpenSSL `enc`'s password-derived custom wrap IVs, with KEKs
derived through the existing EVP_BytesToKey/PBKDF2 machinery (12 variants),
against all three tracked blobs and the 568 curated candidates. Every branch
-- including a negative
control confirming a wrong passphrase's KEK is actually rejected, not just
that the happy path decrypts -- was validated against synthetic
known-positive vectors first. A successful unwrap was designed to be
treated as key material first (tried as a raw AES/3DES key, then as
passphrase text/hex) rather than assumed to be plaintext, chained
automatically but only after a real unwrap, never speculatively.

An independent audit caught that the first run's internally-generated tests
covered only default AIVs and therefore did not reproduce the motivating
OpenSSL CLI mode. Four fixed OpenSSL-generated interoperability vectors were
added and the corrected four-mode sweep rerun:
14,715 passphrase forms, 2,118,960 effective unwrap operations: **0 hits.**
**Closed negative** for this candidate
set -- rules out "right passphrase, wrong cipher mode assumed" for the same
568 candidates already exhausted under CBC, but not Key Wrap under an
untested passphrase. `urlblob`'s own verification and recheck (both under
CBC and this Key Wrap sweep) is item 11.

### 11. `urlblob` Provenance Verification and Quarantine

**Status (2026-07-24): implemented, closed negative.** See FINDINGS.md
Phase 27. Per explicit instruction, verified `urlblob`'s exact archived
bytes and provenance before touching it at all, went further than the
source fork's own citation: fetched the live Wayback CDX API directly and
found the fork's docs cite the wrong capture -- the 2026-02-07 date they
give is a truncated 40-byte duplicate, while the actual complete 112-byte
capture (`Salted__` + salt `74c974e3f92e64b5` + 96-byte ciphertext) is from
2026-01-05. Cross-checked the complete capture's bytes against the fork's
own `demos.js` UI-demo literal -- byte-for-byte identical. Confirmed both
captures' page bodies are the ordinary SPA shell (payload lives only in the
URL path, never the response), matching the fork's claim.

Added as `cb_common.QUARANTINED_BLOBS["URLBLOB"]` -- deliberately NOT a peer
default like P32TRAILING, since (unlike P32TRAILING) no official README or
solved-plaintext corroborates it as a genuine puzzle artifact; the source
fork itself calls it "orphaned." `extended_cipher_recheck.py` and
`aes_key_wrap_sweep.py` both gained an explicit `--include-quarantined` opt-in
flag; default behavior of every existing script is unchanged.

Reran both the extended-CBC recheck (568 candidates x 18 cipher/KDF variants)
and the corrected four-mode Key Wrap sweep (12 KEK variants x {rfc3394,
rfc5649} x {default-AIV, OpenSSL-IV}) against `urlblob` alongside the other
three blobs: **0 hits, both.** **Closed negative** for this candidate set --
does not rule out a different, untested passphrase, nor any cipher/KDF
hypothesis not yet covered. Per the user's own follow-on instruction, the
bounded adjacent-difference/self-synchronizing DBBI transform hypothesis is
the next queued path; see item 12.

### 12. Adjacent-Difference / Self-Synchronizing-Cipher Hypothesis

**Status (2026-07-24): implemented, screen-negative and not advanced.** See FINDINGS.md
Phase 29. Tested whether each raw dbbi/faed symbol is a function of itself
and its neighbor (lag-1 differential encoding) via 4 base transforms
(`diff`, `sum`, `inv_diff`, `inv_sum`) x direction, **linear boundary only**
-- circular boundary deferred (mathematically ambiguous: a 9-way additive-
offset family for `diff`, parity-dependent solvability for `sum`).

Went through three rounds of external review before implementation. Key
corrections: escape pairs are re-derived fresh per transformed stream
(filtered for clean segmentation before ranking by closeness to the 47%
escape-density reference, both orderings tested), with `k` (how many
candidate pairs to hedge across) calibrated as a **hard gate against fixed
synthetic controls only** -- genuinely discriminating (failed at k=3/k=5 for
faed's `escapes_first` topology, passed at k=7) rather than trivially
passing; scores normalized per-quadgram (not raw sums, which bias toward
longer text); both targets tested at a Bonferroni-corrected p<0.005 (not
p<0.01, to control the combined two-target false-positive rate); a staged
500-then-5000-trial design with a fully independent confirmation seed,
avoiding optional-stopping bias.

**Result**: neither target cleared the cheap Stage-1 screen (dbbi
p=0.77246, faed p=0.87824 -- both real scores actually below their null
means), so the expensive Stage-2 confirmation batch correctly never ran,
and nothing escalated to any AES oracle. **Screen-negative and operationally
deprioritized**, scoped to linear-boundary lag-1 differencing under the top-7
(non-exhaustive) escape-pair candidates x existing alphabet/topology axes;
not a Stage-2-confirmed exclusion. A separate, non-gating transition-mask/
run-length diagnostic also found nothing exceptional in either stream's raw
adjacency structure.

### Path Explicitly Deprioritized: Repeating-Key Period Search

A frequency-preserving permutation scan over periods 2-40 was run during this
review. It corrects the old uniform-random Kasiski baseline by shuffling each
ciphertext's actual symbol multiset and comparing the maximum period score:

| Target | Best period | Nominal z | Max-corrected empirical p |
|---|---:|---:|---:|
| `dbbi` | 13 | 2.52 | ~0.34 |
| `faed` | 37 | 1.67 | ~0.80 |

No period is significant. In particular, `faed` does not support the earlier rough
Friedman estimate near period 9. Do not prioritize Vigenère/autokey expansion solely
from that estimate; complete the already-defined escape-pair backfill for coverage,
but treat it as bookkeeping rather than a newly strengthened lead.

## Highest-Priority Path: Dual-Ternary Encoding

Treat each `a`–`i` symbol not as one atomic base-9 digit, but as a pair of ternary
coordinates:

```text
a=00  b=01  c=02
d=10  e=11  f=12
g=20  h=21  i=22
```

This is materially different from the existing base-9 bignum and native 9-ary
checkerboard investigations.

### Motivation

- Nine symbols naturally form a 3×3 Cartesian product.
- Every symbol contains two components, giving a literal structural interpretation of
  **Cosmic Duality** and yin-yang.
- `dbbi` becomes 182 trits.
- `faed` becomes 1,140 trits.
- `faed`'s 1,140 trits divide exactly into 228 groups of five trits, each representing
  a base-243 value.
- Preliminary decomposition shows that `dbbi`'s two component streams have noticeably
  different distributions, while `faed`'s streams remain comparatively flat. This is
  compatible with a structured instruction/key half and an encrypted payload half,
  although it is not proof.

### Proposed Search

Enumerate the following constrained transformations:

1. The eight geometric symmetries of the 3×3 symbol square.
2. Swap the first and second trit streams.
3. Complement either stream with `x → 2-x`.
4. Reverse either stream independently.
5. Read the ciphertexts using their exact matrix dimensions:
   - `dbbi`: 7×13 and 13×7.
   - `faed`: 15×38 and 38×15.
6. Combine the streams using:
   - mod-3 addition;
   - mod-3 subtraction in both directions;
   - equality/inequality masks;
   - alternating or interleaved reads.
7. Decode using:
   - five-trit base-243 units;
   - whole base-3 integers;
   - independently packed component streams;
   - ternary-to-binary threshold mappings.
8. Search outputs for:
   - readable text;
   - file and compression signatures;
   - `Salted__`;
   - hashes or fixed-length key material;
   - output that verifies through the real AES oracle.

This is a small structural search and should be attempted before any additional
dictionary-scale work.

## Second Path: Execute the Clues as a Program

The page contains the decoded fragments:

```text
matrixsumlist
lastwordsbeforearchichoice
thispassword
enter
our first hint is your last command
ans too
```

Most existing work uses these fragments as keywords, candidate passphrases, or
transposition-key strings. A stronger interpretation is that they form an ordered
instruction language.

### Proposed Interpretation

1. Place `dbbi` into a 7×13 matrix.
2. Place the known 91-character Phase 3.2.2 plaintext into a parallel 7×13 matrix.
3. Convert one or both matrices to numeric values.
4. Execute `matrix sum list` literally:
   - calculate row and column sums;
   - calculate elementwise sums and differences;
   - rank rows or columns by their sums;
   - use sums as indices into the parallel matrix;
   - use one matrix as a selector or mask over the other.
5. Interpret `lastwordsbeforearchichoice` positionally:
   - find occurrences of `Architect` and `choice` in the preceding decrypted text and
     relevant Matrix dialogue;
   - extract the words immediately before those occurrences;
   - preserve their source order rather than deduplicating them into a generic keyed
     alphabet.
6. Treat the extracted output as `thispassword`.
7. Apply the `enter` instruction, including newline-sensitive forms where appropriate.
8. Interpret the trailing `shabefanstoo`. Only `shabef -> sha256` is
   mechanical; `anstoo -> answer too` is a community expansion and must not be
   assumed as decoded page text.

Individual components—triangle sums, standard columnar transposition, clue-word
passphrases, and candidate alphabets—have been tested. No existing tool appears to
execute this complete instruction sequence as one composed pipeline.

### Implemented Instruction Pipeline

`tools/gsmg/matrix_instruction_sweep.py` now implements this bounded interpretation:

- pairs `dbbi` cell-for-cell with the known 91-character Phase 3.2.2 answer;
- evaluates both 7×13 and 13×7 matrix orientations;
- tests `a=0..i=8` and `a=1..i=9`;
- calculates row and column sums for both matrices;
- converts sum lists to letters, decimal strings, and global selectors;
- ranks and reads plaintext rows/columns by the `dbbi` sums;
- applies row-local, column-local, and cell-local selections;
- tests elementwise mod-26 addition and both subtraction directions;
- extracts one to thirteen words before `choice`, `select`, `architect`, or `archi`;
- composes matrix outputs with positional extractions in both orders;
- uses extraction letters as zero- and one-based indices into matrix outputs;
- applies raw, SHA-256, double-SHA-256, LF, and CRLF passphrase forms through the real
  AES oracle.

Run:

```bash
python3 tools/gsmg/matrix_instruction_sweep.py --self-test
python3 tools/gsmg/matrix_instruction_sweep.py --top 30
python3 tools/gsmg/matrix_instruction_sweep.py \
  --source-file extra_corpus.txt \
  --json-out /tmp/matrix-instructions.json
```

### Instruction-Pipeline Result

| Candidate stage | Unique outputs |
|---|---:|
| Paired-matrix operations | 151 |
| Positional text extractions | 54 |
| Composed instruction outputs | 11,684 |
| Combined candidates | 11,889 |
| AES keystring forms | 271,692 |
| Verified AES hits | **0** |

The highest-scoring matrix outputs are reordered fragments of the already-known
Phase 3.2.2 plaintext. Their English appearance is therefore expected and is not new
signal. None of the literal sums, selectors, elementwise combinations, positional
extractions, or composed passphrases opened either AES blob.

This closes the second path for the implemented bounded grammar with hand-typed
paraphrase quotes. It does not rule out a different source corpus for
`lastwordsbeforearchichoice`; the script accepts repeatable `--source-file` inputs so
an exact archived page transcript or verified film script can be tested without
changing the matrix logic.

### Real-Screenplay Follow-Up — RESOLVED, NEGATIVE (2026-07-23)

The three built-in quotes above were paraphrases from memory, not verbatim dialogue.
The real screenplay PDFs (`wordlists/matrix/the-matrix-1999.pdf`,
`the-matrix-reloaded-2003.pdf`, `the-matrix-revolutions-2003.pdf`, 80,695 words total
via `pdftotext -layout`) were already on disk from an earlier, unrelated, already-
negative test (the 2026-07-12 verbatim-riddle-excerpt sliding-window sweep — see
`doc/GSMG_PUZZLE.md`) but had never been fed into this instruction pipeline.

The AES-check stage was single-threaded and could not finish against a real 25-28k-
word-per-script corpus in reasonable time (timed out at 100s even capped to
`--max-words 4`). Parallelized `check_aes` over a `ProcessPoolExecutor` (same chunked
pattern as `cosmic_sweep.py`/`autokey_sweep.py`; new `--workers` flag, default
`os.cpu_count()`), which brought a `--max-words 4` run down to 46s.

Full run at the doc's original `--max-words 13` scope, all three real scripts,
`choice`/`select`/`architect`/`archi` markers:

```bash
python3 tools/gsmg/matrix_instruction_sweep.py --workers 16 \
  --source-file the-matrix-1999.txt \
  --source-file the-matrix-reloaded-2003.txt \
  --source-file the-matrix-revolutions-2003.txt
```

| Candidate stage | Unique outputs |
|---|---:|
| Paired-matrix operations | 151 |
| Positional text extractions (real dialogue) | 1,890 |
| Composed instruction outputs | 391,022 |
| Combined candidates | 393,063 |
| AES keystring forms | 9,288,576 |
| Verified AES hits | **0** |

**This closes the Second Path's instruction-pipeline interpretation against the real
source text, not just the paraphrased approximation.** The top-scoring composed
candidates are, as before, matrix-derived reorderings of the known Phase 3.2.2
plaintext concatenated with real Architect-scene dialogue fragments — plausible-
looking by construction, not new signal.

**Deliberately not done**: expanding the marker set beyond `choice`/`select`/
`architect`/`archi` (e.g. adding `half`, `prime`) — that drifts back toward open-ended
keyword-style expansion, which memory already flags as low-value for this puzzle.
Would only be worth a bounded, clearly-motivated one-shot pass, not a default.

## Third Path: Hash Duality Instead of Double Hashing

The current answer-normalization pipeline tests forms equivalent to:

```text
answer
SHA256(answer)
SHA256(SHA256(answer).hex)
```

The page may instead describe two distinct hashes:

1. `your last command` refers to the previous SHA-256 command or its output—the hash
   used to reach the SalPhaseIon page;
2. `ans too` instructs the solver to hash the newly decoded answer as well;
3. `duality` instructs the solver to combine the two hashes.

For each plausible decoded answer, test:

```text
SHA256(previous_hash || answer)
SHA256(answer || previous_hash)
previous_hash XOR SHA256(answer)
SHA256(previous_hash XOR SHA256(answer))
HMAC-SHA256(previous_hash, answer)
HMAC-SHA256(SHA256(answer), previous_hash)
```

Both the 32-byte binary hashes and their 64-character hexadecimal representations
should be tested. This axis is not equivalent to the existing double-SHA-256 form.

### Implemented Hash-Duality Sweep

`tools/gsmg/hash_duality_sweep.py` tests this interpretation using
`data.VERIFIED_PRIOR_COMMAND_HASHES` — four SHA-256 states explicitly computed and
used by the solved puzzle chain. A same-day audit briefly and incorrectly removed
the first three after searching only this repository's local notes. Rechecking the
primary public `puzzlehunt/gsmgio-5btc-puzzle` README confirmed every exact preimage,
hash, and subsequent OpenSSL use:

| State | SHA-256 | Derivation |
|---|---|---|
| Phase 2 `causality` | `eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf` | `SHA256("causality")`, explicitly used as the Phase 2 AES password |
| Phase 3 seven parts | `1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5` | SHA-256 of the documented exact-case seven-part concatenation, explicitly used for Phase 3 |
| Phase 3.2 clue answers | `250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c` | SHA-256 of the documented normalized three-answer concatenation, explicitly used for Phase 3.2 |
| SalPhaseIon page-entry command | `89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32` | `SHA256("GSMGIO5BTCPUZZLECHALLENGE" + puzzle BTC address)` — the literal URL slug used to reach this page, recomputed and confirmed byte-for-byte against `doc/GSMG_PUZZLE.md`'s site-map |

The `89727...` value is the strongest literal reading of `your last command` (it IS
the hash-as-command used to navigate here). The other three are earlier real hash
outputs used directly in OpenSSL commands. The sweep tests all four states
against:

- SHA-256 of `previous || answer` and `answer || previous`;
- `previous XOR SHA256(answer)`;
- SHA-256 of that XOR result;
- HMAC-SHA256 in both key/message directions;
- concatenation of `previous` and `SHA256(answer)` in both orders;
- binary-digest and hexadecimal-text input contexts;
- raw-byte and hexadecimal passphrase representations;
- unchanged, LF-appended, and CRLF-appended forms.

The AES oracle now has a byte-oriented entry point,
`cb_common.aes_try_open_bytes()`, so NUL and non-UTF-8 bytes from XOR/HMAC operations
reach OpenSSL's KDF unchanged.

Run:

```bash
python3 tools/gsmg/hash_duality_sweep.py --self-test --scope core
python3 tools/gsmg/hash_duality_sweep.py --scope all --workers 16
python3 tools/gsmg/hash_duality_sweep.py \
  --scope all \
  --workers 16 \
  --newline-variants
```

### Hash-Duality Result

| Axis | Coverage |
|---|---:|
| Candidate answers | 11,899 |
| Verified prior command hashes | 4 |
| Dual-hash constructions per pair | 16 |
| Binary/hex passphrase representations | Both |
| `enter` forms | Raw, LF (CRLF available via `--newline-variants`) |
| Unique passphrase attempts | 1,427,880 |
| Verified AES hits | **0** |
| Wall time (16 workers) | 25.4s |

No construction opened either AES blob, under any of the four real prior-hash
states. This closes the third path for the candidate answer pool produced by the
first two investigations. The result does not disprove the hash-combination grammar
if the real decoded answer is absent from that pool, but it does show that changing
only the final hash/KDF interpretation cannot rescue any currently plausible answer.

## Fourth Path: Reconstruct Raw Page Structure

This path tests whether flattening the archived page discarded authored ordering,
line breaks, whitespace, CSS position, or adjacency that should control the final
phase.

### Reproducible Audit

`tools/gsmg/page_structure_audit.py` parses the raw archived HTML rather than the
community transcription or screenshot. It preserves both textarea bodies, verifies
every known segment at an exact offset, and fails if any character remains
unclassified.

Run:

```bash
python3 tools/gsmg/page_structure_audit.py
python3 tools/gsmg/page_structure_audit.py --json
```

The default capture is the local Wayback mirror documented in `doc/GSMG_PUZZLE.md`;
another capture can be supplied with `--html`.

### Exact Structure

The SalPhaseIon textarea has **1,075 logical characters, zero authored line breaks,
and exactly one ASCII space between every character**. Its apparent rows in the
screenshot are therefore browser soft-wraps and carry no stable row/column geometry.
The complete normalized stream partitions with no remainder:

| Half-open offset | Length | Segment |
|---:|---:|---|
| `0:91` | 91 | `dbbi` |
| `91:195` | 104 | abba binary → `matrixsumlist` |
| `195:765` | 570 | `faed` |
| `765:766` | 1 | `z` separator |
| `766:829` | 63 | decimal/base-16 transport → `lastwordsbeforearchichoice` |
| `829:830` | 1 | `z` separator |
| `830:859` | 29 | decimal/base-16 transport → `thispassword` |
| `859:860` | 1 | `z` separator |
| `860:895` | 35 | `shabefourfirsthintisyourlastcommand` |
| `895:959` | 64 | first half of the SalPhaseIon AES Base64 |
| `959:999` | 40 | abba binary → `enter` |
| `999:1063` | 64 | second half of the SalPhaseIon AES Base64 |
| `1063:1075` | 12 | `shabefanstoo` |

The Cosmic Duality textarea is structurally different: its **1,792 Base64
characters have 27 authored newlines, forming exactly 28 lines of 64 characters**.
Both textareas use the same inline CSS (`width: 100%; height: 200px`); the page has no
positioned elements, hidden text, data attributes, or layout stylesheet capable of
encoding another read order. DOM order is simply SalPhaseIon, then Cosmic Duality.

### New Structural Inference

The strongest result is local and exact: the encoded `enter` is inserted at byte-text
offset 64 of the 128-character SalPhaseIon Base64 blob. Removing the 40-character
abba marker produces two 64-character lines—the same line width explicitly authored
for every line of the Cosmic ciphertext below it. Both reconstructed strings decode
cleanly to OpenSSL `Salted__` payloads.

This makes **`enter` as an in-band line-break/formatting instruction** substantially
better supported than `enter` as a newline appended to an AES passphrase. It explains
the marker's exact location without adding cryptographic degrees of freedom. The
newline-passphrase variants were still tested previously and were negative.

### Outcome

- Retire screenshot row/column routes over the SalPhaseIon text; their boundaries
  change with viewport width.
- Retire CSS-position and hidden-DOM hypotheses for this capture.
- Preserve the authored order as an instruction stream: `dbbi`, postfix
  `matrixsumlist`, `faed`, postfix password-selection clues, then the small AES object,
  followed by the separate large Cosmic AES object.
- Treat the two AES blobs as the only meaningful page-level dual objects. Their
  vertical adjacency supports a staged relationship, but supplies no new key or
  direction by itself.
- Interpret `enter` primarily as reconstructing conventional Base64 formatting. This
  is a real clarification, but it reproduces the already-tested SalPhaseIon blob and
  therefore does not itself open either ciphertext.

Path 4 is thus **resolved as a useful grammar correction, not a cryptanalytic hit**.
The remaining actionable question is what operation `matrixsumlist` and
`lastwordsbeforearchichoice thispassword` apply to—not page geometry.

## Lower-Priority Path: Alternative Target Coupling

The existing coupled-target implementation tests:

```text
candidate alphabet → decode dbbi → use result as faed alphabet → decode faed
```

It uses the `{b,e}` escape hypothesis at both stages. Remaining coupling variants
include:

- `faed → dbbi`;
- folding `faed` into 91 positions and using it as a mask or selector for `dbbi`;
- repeating or folding `dbbi` as a mod-9 or mod-3 keystream over `faed`;
- using mirrored or opposite escape pairs for the two halves;
- combining the two ternary component streams across targets.

This is lower priority because `faed` appears high-entropy, but it becomes cheap once
the dual-ternary representation exists.

### Implemented Cross-Target Coupling

`tools/gsmg/cross_target_coupling_sweep.py` implements the remaining bounded variants
without reopening the statistically negative dual-ternary branch.

The **reverse-chain** mode tests:

```text
candidate alphabet
→ decode faed
→ use each normalized faed result as a new 25-letter board
→ decode dbbi
→ AES oracle
```

It uses the full 8,036-candidate session vocabulary and all ordered forms of the three
escape-pair hypotheses considered in this investigation:

- `{b,e}` from `dbbi`;
- `{g,i}` from `faed`'s own frequency fit;
- `{h,e}` as the mirror of `{b,e}`.

The **raw-coupling** mode tests:

- six ways to fold `faed` from 570 to 91 symbols:
  residue sums, contiguous sums, first/last member of contiguous groups, first 91, and
  last 91;
- mod-9 addition and both subtraction directions with `dbbi`;
- prime, even, and nonzero folded-value selectors over `dbbi`;
- forward and reversed repetition of `dbbi` across all 570 `faed` positions;
- mod-9 addition and both subtraction directions over those repeated streams;
- raw symbols, `a=0..i=8`, `a=1..i=9`, whole-base-9 bytes, and base-9 hex;
- both checkerboard topologies, clue-derived alphabets, and all six ordered escape
  assignments.

Run:

```bash
python3 tools/gsmg/cross_target_coupling_sweep.py --self-test --mode raw
python3 tools/gsmg/cross_target_coupling_sweep.py --mode reverse --workers 16
python3 tools/gsmg/cross_target_coupling_sweep.py --mode both --workers 16
```

### Cross-Target Result

| Mode | Coverage | Passphrase attempts | Hits |
|---|---:|---:|---:|
| Fold/repeat raw coupling | 42 derived streams | 30,660 | 0 |
| Reverse `faed → dbbi` chain | 8,036 candidate alphabets | 1,735,776 | 0 |
| **Total** | | **1,766,436** | **0** |

No folded mask, repeated keystream, mirrored escape assignment, or reverse chained
board opened either AES blob. This closes the lower-priority coupling gap for the
bounded mod-9/checkerboard interpretations.

## Cross-Phase Review: DEBUNKED — apophenia, not a connection (2026-07-23)

**Correction, written the same day this section was added.** The claims below were
independently checked with the same scrutiny already applied to
`hash_duality_sweep.py`'s command-state provenance, and to the community's own
already-debunked "matrixsumlist triangle" hypothesis. This section does not hold up:

1. **The internal "yang" validation is statistically unremarkable.** A null-model
   test — 200,000 random shuffles of the same 15×`B`/9×`BE`/1×`G` token multiset,
   run through the exact same extraction algorithm — produces `"yang"` in the
   result **3.68% of the time** (`7,360/200,000`, roughly 1-in-27), while every other tested
   thematic word (`yin`, `half`, `love`, `east`, `best`, ...) never appears. A ~1-in-27
   base rate is not a striking coincidence, especially when weighed against the
   ~30 different mask/extraction variants tried in the same sweep. This is the exact
   apophenia pattern already caught once for the "matrixsumlist triangle" — the
   community's own null-model test showed random strings "find" that triangle at
   the same rate, and the same logic applies here.
2. **`PHASE0_SPECIAL_ORDER` is not new evidence.** It is mechanically identical to
   the LSB-parity sequence of the already-public string `"gsmg.io/theseedisplanted"`
   (verified: removing the grey marker and mapping `BE`→0/`B`→1 reproduces
   `ord(ch) & 1` for every character of that string, exactly). This project's own
   2026-07-13 research already concluded that parity sequence "carries zero
   information beyond what black/white already show at those same 24 cells... not
   a second data channel," and explicitly retired this sub-thread. Treating it as a
   fresh scaffold to walk `dbbi` with contradicts that already-settled analysis
   rather than building on it.
3. **A follow-up provenance accusation was itself wrong.** The primary public
   investigation README explicitly documents `causality`, `Safenet`, `Luna`, `HSM`,
   `11110`, Jacque Fresco, Heisenberg's uncertainty principle,
   `THEMATRIXHASYOU`, and both disputed SHA-256 values. It also distinguishes the
   pre-move chess prompt
   (`B5KR/1r5B/6R1/... w ...`) from the required post-move answer
   (`B5KR/1r5B/2R5/... b ...`) used in the seven-part hash. These are authentic
   solved-phase artifacts, not fabrications. Their authenticity does not rescue the
   color-mask linkage, which already fails points 1 and 2.

**What still stands**: the historical AES-oracle sweep itself (444 candidates, 357 alphabets,
8,568 checkerboard decodes, 161,510 passphrase attempts, 0 hits) is mechanically
sound — no false hit was ever claimed, and that negative result is genuine. The
premise-derived script was removed after falsification to prevent reuse. What's wrong is the surrounding
narrative that this constitutes a real cross-phase discovery. It doesn't, and the
proposed "seven sequential cipher stages" next step is **not recommended** — it's
built on a premise (the specific 23/16/7 split, the "yang" match) that doesn't
survive the null-model test above.

<details>
<summary>Original claim (kept for the record, not endorsed)</summary>

**2026-07-26 correction:** Phase 48 recovered the exact literal mask later
posted by Flo Sku and found the missing deterministic detail: FEFE is an
inserted event at its real spiral position between colored endpoints 20 and
21. With `F -> b`, all 23 events that fit before DBBI ends reproduce the
31-position mask exactly. This supersedes the old ad hoc 23-marker parse and
its unsupported rail/count narrative; it does not restore the seven-stage
cipher recommendation or make `"yang"` a password.

A reconstruction from Phase 0 onward found one substantially stronger connection
than thematic keyword reuse. The final creator hint should be read as an ordered
program:

```text
yellow blue primes
→ matrix sum list
→ last words before archi choice
→ yin yang
```

The components come from different solved phases:

| Component | Earlier phase | Operational role |
|---|---|---|
| Yellow/blue spiral cells | Phase 0 | Supplies an ordered color mask at byte boundaries |
| Prime basics / return to source | Phase 3.2.1 | Instructs reuse of the Phase 0 source and sequential primes |
| `dbbi` | SalPhaseIon | Supplies the `b` / `be` token scaffold |
| 91-character answer | Phase 3.2.2 | Supplies the cell-aligned plaintext to extract from |
| `matrixsumlist` / Architect choice | Phase 3.2.1 and final page | Identifies the Matrix/Architect text and positional operation |
| `yin yang` | Final hint | Confirms the extracted dual rails and likely specifies their next combination |

### Independently Reproduced Prime Scaffold

Reading the Phase 0 image counter-clockwise from the upper-left produces the known
`gsmg.io/theseedisplanted` URL. Its 24 blue/yellow cells are exactly the 24 byte
boundaries. Blue represents a terminal `1`; yellow represents a terminal `0`.

Using that same color order to consume the next matching `b` (blue) or `be` (yellow)
token in `dbbi`, while treating the anomalous `#fefefe` cell as a single `b`, gives a
23-marker parse. Applying those token positions to the exactly 91-character Phase
3.2.2 answer:

```text
INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALF
ANDTHEYALSONEEDFUNDSTOLIVE
```

extracts:

```text
ncsyangcahirivasoalbefayanestve
```

The literal `yang` is an internal confirmation that this is not a generic
English-scoring accident. The two color rails are:

```text
blue:   ncsygcavasoben       (14 characters = seven digraphs)
yellow: anhirialfayastve     (16 characters = eight digraphs)
grey:   e
```

This also gives a notable structural match to Phase 3.2.1's otherwise unexplained
instruction:

- **23** successfully matched color/token groups;
- **16** yellow-rail characters;
- **7** blue-rail digraphs available to intertwine pairwise.

That relationship is stronger than the separate observation that the 161-character
creator hint is `7 × 23`. The latter was still tested, but should now be treated as
secondary evidence rather than the main route.

### Implemented Linkage Sweep

The now-removed `tools/gsmg/phase_linkage_sweep.py` tested:

- `7×23` and `23×7` routes through the 161-character creator hint;
- row/column sums under the stated remainder moduli;
- prime-index selections;
- exact Phase 1–3.2.2 passwords, hashes, source hex, decoded Genesis headline, FEN,
  Architect tail, and validation answer;
- original-position, sequential-prime, expanded-prime, blue, yellow, grey, selected,
  and complement masks;
- all four direct pairwise interleavings of the seven blue and first seven yellow
  digraphs, with the remaining yellow digraph as prefix/suffix;
- every result directly, hashed, newline-terminated, and as a base-9 checkerboard
  alphabet seed against both real AES blobs.

The implementation was removed after its premise failed the null model; the
historical coverage and negative result are retained here for auditability.

Result:

| Coverage | Count |
|---|---:|
| Unique structural/carry-forward candidates | 444 |
| Unique checkerboard alphabets | 357 |
| Checkerboard decodes | 8,568 |
| Unique passphrase attempts | 161,510 |
| AES hits | **0** |

The earlier phases therefore **do** connect, but the extracted rails are not a direct
passphrase, direct hash preimage, or checkerboard keyword under these bounded forms.

### Best Next Path — NOT RECOMMENDED (see correction above)

~~Treat the seven four-character blue/yellow interleavings as seven sequential cipher
keys or stages...~~ Not recommended: this whole path is downstream of the debunked
23/16/7 split and the statistically unremarkable "yang" match. Building a seven-stage
cipher cascade on top of an apophenia artifact would just be more elaborate
apophenia. If this specific idea (short sequential cipher stages keyed by
fragments of the creator hint) is worth testing at all, it should be re-derived from
a construction that survives its own null-model check first, not this one.

</details>

The earlier phases therefore **do** connect at the level of shared vocabulary and
theme (matching what's already documented elsewhere in this project), but the
specific mask/color/prime construction above does not establish a new cryptographic
bridge — see the correction at the top of this section.

## Additional Negative Check

A focused direct-passphrase probe was performed against the real AES oracle using:

- exact prior OpenSSL command lines;
- shell-history forms such as `!!`, `$_`, `history 1`, and `fc -ln -1`;
- likely Architect/choice phrases;
- raw, case-normalized, SHA-256, and double-SHA-256 forms;
- trailing LF and CRLF variants.

Result: **531 unique AES attempts, zero hits**.

This makes it unlikely that `your last command` is simply the literal AES passphrase.
It is more plausibly an instruction to reuse an operation, output, state, or command
structure.

## Paths Not Worth Repeating

- Larger keyword dictionaries using the same keyed-alphabet constructor.
- Generic English-scored hill climbing on `dbbi`.
- The `matrixsumlist` triangle result without a null model.
- Direct clue phrases as AES passphrases.
- Newline-only interpretations of `enter`.
- Re-running the same checkerboard sweeps with additional thematic vocabulary.
- Accepting valid AES padding without coherent and reproducible plaintext.
- (2026-07-23) Any further dual-ternary stream/symmetry/route permutations, or the
  instruction-program/cross-target extensions gated on them — the periodicity null
  model below closed this direction negative; see "Recommended Next Extension" for
  the numbers.
- (2026-07-23) Re-running the matrix-instruction pipeline (Second Path) with the same
  matrix operations/marker words against the same or other Matrix-trilogy text — both
  the paraphrased and the real full-screenplay corpus are exhausted at
  `--max-words 13`; see "Real-Screenplay Follow-Up" for the numbers.
- (2026-07-23) The Phase 0 color-order / dbbi-prime-token / 23-16-7 "cross-phase
  linkage" construction (the removed `phase_linkage_sweep.py`),
  or any "seven sequential cipher stages" idea built on it — debunked as apophenia
  (`7,360/200,000 = 3.68%` chance rate for the internal `yang` validation, while
  the color sequence is only the known URL's terminal-bit parity); see the "Cross-Phase Review"
  correction for the full case. Any future cross-phase construction should run its
  own null-model check *before* being written up as a finding, not after.
- Trusting either a claimed finding or a claimed debunking without checking the
  primary source. Here the linkage failed statistically, but the subsequent claim
  that its solved-phase constants were fabricated was disproved by the public
  README. Validate both positive and negative assertions independently.

## Implemented First Pass

`tools/gsmg/dual_ternary_sweep.py` now implements the first constrained search:

- factors `a`–`i` into two ternary coordinates;
- enumerates all eight 3×3 square symmetries;
- supports row, column, reversed, and serpentine matrix routes;
- uses the exact 7×13/13×7 and 15×38/38×15 dimensions;
- tests component, interleaved, mod-3 sum/difference, and equality streams;
- decodes base-243 groups, whole base-3 integers, and binary masks;
- ranks outputs by signatures, printability, entropy, and printable runs;
- sends highly printable candidates to the existing AES oracle;
- supports JSON output for deeper offline inspection.

Run:

```bash
python3 tools/gsmg/dual_ternary_sweep.py --self-test
python3 tools/gsmg/dual_ternary_sweep.py --target dbbi --top 50
python3 tools/gsmg/dual_ternary_sweep.py --no-aes --json-out /tmp/dual-ternary.json
```

### First Baseline Result

The complete first-pass sweep was run against both targets:

```bash
python3 tools/gsmg/dual_ternary_sweep.py --target both --top 10
```

Results:

| Target | Unique matrix routes | Unique decoded outputs | AES keystrings | Hits |
|---|---:|---:|---:|---:|
| `dbbi` | 15 | 24,002 | 0 | 0 |
| `faed` | 15 | 20,802 | 0 | 0 |

No output began with a recognized file, compression, PEM, OpenSSL, or executable
signature. No output met the strict all-ASCII/high-printability gate required before
AES passphrase testing.

The highest-ranked `dbbi` outputs are short, high-printability accidents without
linguistic continuity. The highest-ranked `faed` outputs mostly come from packing the
binary equality stream into base-243 units. That operation has an inherently restricted
value distribution, so its elevated printability is a representation bias rather than
evidence of plaintext.

This baseline is negative for direct dual-ternary decoding, but the representation
remains useful for the next discriminating test: compare its statistics against
shuffled ciphertexts before attempting cross-target or instruction-program extensions.

## Recommended Next Extension — RESOLVED, GATE FAILED (2026-07-23)

`dual_ternary_sweep.py --periodicity` implements the null-model gate: for each target,
each of the 8 symmetries, and 5 derived streams (`first`, `second`, `sum_mod3`,
`first_minus_second_mod3`, `equal`), it computes the closed-form expected coincidence
rate (the IC, which depends only on symbol frequencies) and compares it against the
observed match rate at every lag 1–40, converting to a z-score. This is order-sensitive
(unlike the raw-symbol Kasiski/Friedman pass already on record as clean), so it is a
genuinely new test of the trit factorization, not a repeat.

Result — **gate failed, do not proceed to instruction-program or cross-target
extensions**:

```
python3 tools/gsmg/dual_ternary_sweep.py --periodicity --target both
```

| Target | Tests run | Bonferroni threshold (α=0.05) | Max \|z\| observed | Survivors |
|---|---:|---:|---:|---:|
| `dbbi` | 1,600 | 4.16 | 2.36 | 0 |
| `faed` | 1,600 | 4.16 | 3.05 | 0 |

`faed`'s top hit (lag=15, `equal` stream, z=3.05) is suggestively at the row-count of
its 15×38 shape, but a z of ~3 is unremarkable noise across 1,600 tests (expected
count of \|z\|≥3 by chance alone is ~4). No stream, symmetry, or lag shows structure
beyond what symbol frequency alone predicts.

This closes the dual-ternary direction as a **negative result**: the trit-factored
streams are statistically indistinguishable from random given their frequencies, so
there is no periodic/keystream feature for an instruction-program pipeline or
cross-target fold to exploit. Per the gating condition stated below, those two
extensions are **not warranted** and should not be built.

## Local References

- `doc/GSMG_PUZZLE.md`
- `tools/gsmg/FINDINGS.md`
- `tools/gsmg/cb_common.py`
- `tools/gsmg/chain_sweep.py`
- `tools/gsmg/lastcommand_probe.py`
- `tools/gsmg/cosmic_sweep_9ary.py`
- `tools/gsmg/cross_target_coupling_sweep.py`
- `tools/gsmg/hash_duality_sweep.py`
- `tools/gsmg/matrix_instruction_sweep.py`
- `tools/gsmg/autokey_sweep.py`

## Public References

- [Original community investigation](https://github.com/puzzlehunt/gsmgio-5btc-puzzle)
- [Rigorous falsification-oriented fork](https://github.com/halbgott29a/gsmgio-5btc-puzzle)
- [Public issue tracker](https://github.com/puzzlehunt/gsmgio-5btc-puzzle/issues)
