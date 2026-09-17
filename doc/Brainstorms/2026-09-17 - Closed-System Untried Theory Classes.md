# 2026-09-17 — Closed-system brainstorm: untried theory classes

Date: 2026-09-17

Status: Tier 1 (items 1a, 1b, 1c, 6, 4-primary, 10b) and Tier 2 (items 8, 9,
7) have been **executed and closed negative** — see
[GSMG_PHASE517_CLOSED_SYSTEM_THEORY_BATCH_AUDIT](../GSMG_PHASE517_CLOSED_SYSTEM_THEORY_BATCH_AUDIT.md)
for the full results, including item 9's structural elimination of the
literal "zeroed out" reading and item 1a's noticed length-coincidence
failing its own declared consistency test. Items 2, 5, 1b's CSP pass, and
the wider tiers of 4/7 remain unexecuted (deferred, not dropped — see the
audit doc's disposition section for exactly what was and wasn't run).
The rest of this document is the original ideation pass, preserved as
written: nothing below was executed at the time it was drafted, and no
hypothesis here changed any gap's disposition on its own. The only
computation done while writing was measuring the objects each item names
(lengths, counts, sums) so the candidates are stated exactly rather than
approximately; those measurements are listed in §6 and
are facts about the inputs, not test outcomes.

Scope: closed system only — the page, the solved-stage texts and boards, the
creator's already-catalogued hints, and sources this project has already
frozen by hash. No new source sweeps.

## 0. Bird's-eye: what 516 phases share, and where the untried room is

Nearly every closed cell in
[GSMG_TECHNIQUE_TARGET_COVERAGE_MATRIX](../GSMG_TECHNIQUE_TARGET_COVERAGE_MATRIX.md)
rests on the same eight working assumptions. The genuinely untried room is
not "another cipher family" (the bird-view reassessment already said so);
it is in *inverting one assumption at a time* while keeping everything else
the project has validated.

| # | Assumption shared by (almost) all closed work | Inverted by |
|---|---|---|
| A1 | `DBBI` and `FAED` are both checkerboard ciphertext of *text* | items 1a, 4, 6, 10c |
| A2 | that text is English (Dutch/spaced-English already closed) | — (nothing new proposed) |
| A3 | the board is a 25-slot bijection | 1a (homophonic *digits*, forced by 19 code types) |
| A4 | the two streams are decoded independently, then combined | 1, 2 (one stream *describes* or *keys* the other) |
| A5 | the instruction words are instructions *to the solver* | 1 (they are *labels naming what the adjacent stream is*) |
| A6 | the three unresolved AES blobs are byte-intact | 9 |
| A7 | the a–i digit convention is `a0i8` or `a1i9` | 7 |
| A8 | every one of the 91/570 symbols is payload | 6 |

Explicitly **not re-proposed** (closed, or set aside on argument): Dutch or
spaced-English plaintext models and keyword-keyed transposition (2026-09-03
scratchpad, negative); single-escape hex checkerboard (dead by counting);
BTCSEED alphabet completion (Phase 429–441, `16!` exhausted); the three
borrowed-string cribs and the 31-character selection as a crib (Phase 512;
this session's provenance trace); more escape-pair statistics without a
selector (Phase 449/460); generic prime-zeroing sweeps without a selector
(bird-view reassessment); anagram search over the 31 characters; any
Telegram/web/source sweep. Also set aside on argument, not evidence: a
*homophonic* board for `FAED` — homophony pushes code-IC *below* the
plaintext's letter IC, but `FAED {g,i}` sits *above* English (0.0743 vs
≈0.065), so it explains the wrong direction.

Items are ranked by (page licensing) × (exactness of bar) × (cost).

---

## 1. Reading A of the page order: the instruction words are *labels*, not instructions

**New assumption.** `DBBI [matrixsumlist] FAED [lastwordsbeforearchichoice] [thispassword]`
is a labelled listing, the way a solver's own notes would read:
*"DBBI — matrix sum list. FAED — last words before the Architect's choice.
This password → enter."* Under this reading each stream has an exact,
page-licensed plaintext, and the endgame password is the decoded `FAED`
text (or its own last words).

**Why it is genuinely different.** Every prior phase treated
`matrixsumlist` as an operation to *apply* (to the 31-character selection —
T4 in the theory registry, gap `G-MSL-001`, 7/7 fields unbound) and
`lastwordsbeforearchichoice` as a *selector* over the Architect text (the
`[23,16,7]` → `BOTH/ULTIMATELY/THE` → mirror chain, `G-ARCH-001`). Neither
was ever tried as a *description of the adjacent ciphertext's content*. This
is also the only crib construction that answers the objection raised
against Phase 512's cribs ("why would FAED contain that string?"): because
the page says so, adjacent to the stream.

### 1a. `DBBI` is the checkerboard encoding of `matrixsumlist(FAED)`

*Candidate universe (closed, pre-declared):* `FAED` laid out row-major at
every exact rectangular factorization of 570 (`2×285, 3×190, 5×114, 6×95,
10×57, 15×38, 19×30` and their transposes — 14 layouts) × sum type ∈ {row
sums, column sums, main-diagonal sums, anti-diagonal sums} × digit
convention ∈ {`a0i8`, `a1i9`} = 112 digit strings; × `DBBI` escape pair ∈
the 29 pairs that validly segment it. **3,248 cells.**

*Minimal test, exact bar:* for a cell to pass, the digit string's length
must equal `DBBI`'s token count under that pair, **and** the map
`code → digit` must be consistent: every occurrence of the same code type
carries the same digit (equal codes ⇒ equal digits). This is the surjective
homomorphism test; `DBBI {b,e}` has 63 tokens over 19 code types, so at
least 44 positions are constrained and a random 63-digit string passes with
probability ≈ 10⁻⁴⁴ — no multiple-testing concern across 3,248 cells.
Serialization variants are also closed: fixed-width zero-padded vs. minimal
digits (×2). Optionally a separator symbol (×2).

*Measured while writing (fact, not a result):* exactly one of the 112 digit
strings has length 63 — `FAED` as **19×30, column sums, `a0i8`** — and 63 is
`DBBI`'s token count under its own independently rank-1 pair `{b,e}`. The
other lengths are 30, 45, 57, 62, 76, 77, 79, 80, 114. This coincidence was
*noticed after* computing all 112 lengths, so it is a post-hoc first gate,
not evidence; the consistency test above is the test, and the correction
family is the full 3,248-cell grid, in which this cell is merely first.
Two honest tensions: (i) a digit plaintext with 19 code types implies a
homophonic digit board, unlike the near-bijective 3.2.2 house style; (ii)
`DBBI {b,e}` code-IC is 0.0671 (English-like), which a skewed sum-digit
string would not naturally produce unless homophony flattens it. The test
decides; neither tension is grounds to skip it.

*Stop rule:* no consistent cell → closed: "`DBBI` is not a checkerboard
encoding of any exact-rectangular sum list of `FAED`." Do not extend to
ragged/padded layouts or to the 31-character selection.

*Cost:* seconds.

### 1b. `FAED` is the checkerboard encoding of the last words before the Architect's "choice"

*Candidate universe:* the film Architect scene, already frozen by this
project (`wordlists/matrix/the-matrix-reloaded-2003.en.srt`, SHA-256 in
[GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT](../GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT.md));
the puzzle's own Phase 3.2 plaintext was checked and contains no "choice",
so the film text is the only Architect-choice source, as that audit already
assumed. For each `FAED` escape pair `p` (29 valid) with token count `N_p`
(436–484), the crib is the **last `N_p` letters before "choice"** (J→I, 25
letters; every such suffix uses all 25 letters). Variants: the four "choice"
tokens inside the scene (primary: the Architect's own *"the problem is
choice"*); with/without a space symbol counted as a slot (×2). ≈ 29×4×2 =
232 cribs.

*Minimal test, exact bar:* identity order first — bijection consistency
between the 25 code types and the 25 letters over the full length (equal
codes ⇔ equal letters), microseconds per crib. Then Model B (transposition
before checkerboard) through the **already-built Phase 512 exact-crib CSP**
at widths 15/19/30 — the machinery exists and was validated on synthetic
plants; width 38 stays gated as before. Note the boundary audit's scope 1
("Which brings us at last…" → choice) is only 290 letters, below any `FAED`
token count (≥ 436), so the *whole scope* cannot be `FAED`; only a suffix
of the longer speech can — which is exactly what "last words" says.

*Stop rule:* no consistent crib at identity and none at widths 15/19/30 →
closed; the page's label does not describe `FAED`'s literal content.

*Cost:* identity pass seconds; CSP widths hours (same as Phase 512G/512L).

### 1c. Mirror reading (cheap to add): `DBBI` as the last words

Same test as 1b with `DBBI`'s token counts (63–84): e.g. under `{b,e}` the
crib is the last 63 letters,
`MATRIXTOHERANDTHEENDOFYOURSPECIESASYOUADEQUATELYPUTTHEPROBLEMIS`.
Included only because it costs nothing and disambiguates which stream each
label attaches to (the postpositive-label question Phase 101/372 left open).

---

## 2. `DBBI`'s sum list as the *transposition key* for `FAED` (cross-stream, page-order licensed)

**New assumption.** `DBBI [matrixsumlist] FAED` reads left-to-right as a
pipeline: `DBBI` (a 7×13 matrix) → its sum list → the key that unscrambles
`FAED`.

**Why different.** Phase 19-B ran the self-derived-permutation idea, but
only *within* a stream (`DBBI`'s row/column sums permuting `DBBI`; `FAED`'s
own sums permuting `FAED` at 15×38/38×15 only) and only row/column sums.
Never `DBBI → FAED`, never diagonals, never the 19×30 shape the solver line
later standardized on. Phase 516 exhaustively closed *every* width-7 key
on `DBBI`, so `DBBI`'s 7 row sums keying `DBBI` are already covered.

*The structural fit:* a 7×13 matrix has exactly **19** diagonals (7+13−1),
and 19 is a `FAED` width (570 = 19×30). Rows (7) and columns (13) give no
`FAED` divisor; diagonals are the only `DBBI` sum list whose length is one.
The 19 anti-diagonal sums under `a0i8` are
`[3,2,15,20,19,23,19,25,19,27,31,21,31,27,15,22,2,6,4]` (see §6 for all
four variants). Because diagonals differ in length, `a0i8` vs `a1i9` changes
the *ranking*, unlike columns — both are in scope.

*Candidate universe:* {7×13, 13×7} × {anti-, main-diagonal} × {`a0i8`,
`a1i9`} × {ascending, descending rank} × {2 tie-break conventions} ×
{apply as encrypt-order, as decrypt-order} = **64 fixed keys** × 29 `FAED`
pairs.

*Minimal test, bar:* for each (key, pair), decrypt the 19×30 columnar
transposition, then run the existing width-19 board anneal at the Phase
504 budget; bar = the Phase 113 protocol (100 same-budget shuffled-symbol
nulls, one-sided p ≤ 0.005) applied to the *family maximum* over the 1,856
cells, not to the best cell alone. Two exact side-tests at zero extra cost:
the same 19 numbers as a Nihilist additive key mod 9 over `FAED` (19 cycles
exactly 30 times over 570), and the 13 per-letter popcounts of the page's
own binary rendering of `matrixsumlist` — `[5,3,4,4,4,4,5,5,5,4,4,5,4]`, the
only literal "matrix sum list" physically on the page — as a width-13 key
over `DBBI` and as an additive key cycling exactly 7 times over 91.

*Stop rule:* family maximum fails the null → closed for fixed sum-derived
keys. Do not widen to arbitrary numeric keys.

*Cost:* ≈ 1,856 board anneals ≈ 2–3 hours at Phase 504 budget; side-tests
minutes.

---

## 3. Observation: the creator's `{1},{4}` are the 3.2.2 board's escape digits — and under `a0i8` they are `{b,e}`

Not a test; a selector observation that is **unrecorded anywhere in the
clue ledger, fact ledger, or gap registry** (grep-confirmed while writing).
The solved 3.2.2 checkerboard used `VALIDATION_ESCAPES = (1, 4)`. The
2021-04-01 hint reads *"another door might be found on {1},{4},{21}"*. Under
`a0i8` (a=0, b=1, …, e=4), digits 1 and 4 are **`b` and `e`** — `DBBI`'s
independently rank-1 escape pair. The clue ledger currently consumes the
hint on the rabbit bit grid ("one FEFE cell, bit 4, character 21"); that
reading and this one are not exclusive.

*What it licenses (all cheap, all closed):*
- prefer `a0i8` over `a1i9` when a tie must be broken (relevant: item 1a's
  63-length cell is `a0i8`-only);
- run items 1b and 2 with **`{b,e}` as the pre-registered primary `FAED`
  pair** (Phase 460 found no calibrated evidence that `FAED` needs a pair
  different from `DBBI`'s; `FAED {b,e}` segments to 469 tokens);
- one chronology check: whether the 3.2.2 escapes were public before
  2021-04-01 — if so, the hint may be *describing* them and "21" is the
  next parameter. Closed readings of "21": the 21st prime (73 — the `FEFE`
  sum already in `G-PRIME-001`), slot 21 of `ALPHA_322` (`S`), and raw
  position 21. Nothing else.

*Stop rule:* this item promotes nothing on its own; it only orders the
execution of items 1–2. Present as unconfirmed.

---

## 4. `FAED` is base-9-encoded *binary*, not text (the "raw ciphertext payload" theory, finally tested as a payload)

**New assumption.** 570 base-9 digits carry ≈ 1,807 bits ≈ 226 bytes of a
binary object with a recognizable header.

**Why different.** `chain_addition_sweep.py`'s own docstring calls "raw
ciphertext payload" the *leading* explanation of `FAED`'s low IC, yet the
only execution (Phase 318) tested the base-9 integer as a *key* (mod-N
address check) and as passphrase forms — never as a *payload* with a
header. Phase 342's header/format ladder ran over decoded P0A/P1A bodies,
not over base-9(`FAED`). Thematically on-style: the creator's other stages
are `openssl enc` outputs, and the Architect text advertises nested
encryptions.

*Candidate universe (primary):* Phase 318's own 4 integers (`a0i8`/`a1i9`
× forward/reversed) × {big-, little-endian} × {minimal bytes, zero-padded
to 226} = 16 byte strings. *Header set (exact):* `Salted__`, gzip
`1f8b08`, zlib `78{01,5e,9c,da}`, DER `30 81/30 82`, zip `504b0304`, PGP
packet tags, PNG, `-----BEGIN`. *Secondary tier, still exact and
pre-declared:* all 9! symbol→digit maps × 2 byte orders (725,760 strings)
against ≥ 6-byte headers only, so expected false positives stay ≈ 0.

*Bar:* header match plus the format's own structural validity (e.g.
`Salted__` → 8-byte salt + length ≡ 0 mod 16; zlib → inflates). A hit does
not open anything by itself; the inner key universe would then be `DBBI`'s
decode / `thispassword`, a separate stage.

*Stop rule:* no header at either tier → closed for direct base-9 payload.
Base-9 *after* a transposition is unbounded and is not proposed.

*Cost:* primary seconds; secondary minutes.

---

## 5. Census: "23 ciphers / 16 encryptions / 7 intertwined passwords" as a progress meter

**New assumption.** The Architect's counts describe the *whole* puzzle, so
subtracting what is already accounted for bounds how many layers the
endgame still has — which constrains topology before any decrypt is run
(e.g. whether item 4's inner AES + `SALPH` + `COSMIC` is even arithmetically
possible).

**Why different.** Phase 265 tested these phrases as *passphrases*; nobody
has used them as *numbers to reconcile against the solved chain*.

*Test:* pure bookkeeping — enumerate every cipher instance (Beaufort,
checkerboards, Bifid claims, base64, SHA rails…) and every AES encryption in
Phases 1–3.2 plus the page; report the residual against 23/16/7 under two
counting conventions (per-stage vs per-artifact). Exact bar: an integer
residual, not an interpretation.

*Stop rule:* if the residual is negative or non-integer under both
conventions, the counts are rhetoric and the item closes.

*Cost:* zero compute; an afternoon of reading.

---

## 6. "Zeroed out" as *deletion of the zero digit*: `DBBI` minus `a` is 33 bytes

**New assumption.** Under `a0i8`, `a` is the digit 0; "some characters
need to be zeroed out" means *remove them*. `DBBI` has 3 `a`s; the
remaining 88 symbols over 8 values are octal digits: **88 × 3 = 264 bits =
exactly 33 bytes** — the length of a compressed secp256k1 public key, or a
32-byte private key plus one flag byte. (`FAED` minus `a` = 516 symbols =
1,548 bits, not byte-aligned; minus its most frequent symbol `g` = 463 —
also not. This is a `DBBI`-only fit.)

**Why different.** `hush_zero_sweep.py` neutralized the *escape* symbols
(`b`/`h`), never the zero digit; Phase 318 packed *base-9* over all 91
symbols (36 bytes, which it noted does not land on 32). Nobody has deleted
`a` and read base-8.

*Candidate universe:* remove `a` only; `b…i → 0…7` in order; MSB-first /
LSB-first; four readings: compressed pubkey (first byte ∈ {02,03} and
on-curve — a structural bar before any address check), privkey+flag with
the flag at either end, plain 264-bit scalar mod n. **8 candidates**, each
against the frozen 10-address target set.

*Stop rule:* no structural/address hit → closed. Do not extend to deleting
other symbols or other radices.

*Cost:* seconds.

---

## 7. A third, *selected* digit convention: the Lo Shu magic square

**New assumption.** The puzzle's yin-yang / *Cosmic Duality* framing points
at the Lo Shu square — the archetypal 3×3 matrix whose every row, column and
diagonal *sum list* is constant (15). Read a–i onto the square in its
canonical row-major order: `a=4 b=9 c=2 d=3 e=5 f=7 g=8 h=1 i=6`, plus the
square's 8 symmetries.

**Why different.** Every numeric phase used `a0i8`/`a1i9` (the "four
unknowns" list in `GSMG_PUZZLE.md`); no themed convention was ever
selected, and 9! maps were treated as fishing. This is one map (×8
symmetries) with a stated selector, weaker than page adjacency but real.

*Test:* re-run only the already-closed *cheap* numeric cells under the 8
conventions — Phase 318's key/passphrase checks, Phase 513's giant-decimal
trick, item 4's header check, item 1a's sums. Bars inherited unchanged.

*Stop rule:* all inherited bars fail → closed; no further conventions.

*Cost:* minutes.

---

## 8. Page-artifact bytes and hashes as `SALPH`/`COSMIC` passwords (a deliberately deferred cell)

**Why different.** Phase 381 froze an 83-candidate manifest (7 site assets
with pre-2023 provenance + 76 creator-authored Telegram payloads, 3 byte
forms each) and ran it against **`P32TRAILING` only**, with
`SALPH`/`COSMIC`/`URLBLOB` "deliberately out of scope per the source
document." The universe is already closed and digest-pinned; the other
three targets were never queried. Self-referential members (each blob's own
bytes and SHA-256, `DBBI`, `FAED`, the binary word) should be confirmed
present.

*Bar:* the standard oracle's PKCS7-valid decrypt. *Stop rule:* negative →
closed. *Cost:* ≈ 30k decrypts, minutes.

---

## 9. Blob integrity under the only creator-stated operation

**New assumption.** No unresolved blob has ever had its byte-integrity
confirmed (only successful decrypts confirm it, and there are none). The
creator's one explicit *operation* — "some characters need to be zeroed
out" — combined with `{1},{4},{21}` and the project's own accepted reading
that the puzzle zeroes a `FEFE` bit (a proven mechanism), licenses a bounded
check that the blobs' base64 is meant to be edited before decryption.

*Candidate universe:* 3 blobs × position sets {1,4,21}, {2,7,73} (the
n-th primes; 73 is `FEFE`'s sum) × modes {delete, set to `A` (base64
zero), set to `0`} = 18 variants; × the frozen 42-sentinel password set
from Phases 336–338 × the oracle's KDF variants.

*Bar:* PKCS7-valid decrypt. *Stop rule:* negative → closed; do not widen
positions or passwords. *Cost:* minutes.

---

## 10. Small exact closures (each a one-liner, each cheap)

- **10a.** `DBBI‖FAED` and `FAED‖DBBI` as one 661-symbol checkerboard
  stream (the instruction words as removed interleaves): 36 pairs × the
  Phase 113 protocol. Phase 413/459/460 pooled or split the streams; none
  decoded the concatenation.
- **10b.** Letter-class homomorphism: is `DBBI` a *nine-class* image of
  `VALIDATION_ANSWER` (equal letters ⇒ equal symbols, for a free
  letter→symbol map)? The yellow/blue audits tested only two-class masks;
  this is the general form of the Denis idea and subsumes keypad/T9
  readings. Likewise `FAED` vs every 570-letter window of the Phase 2, 3,
  3.2 and film-Architect texts. Microseconds; exact.
- **10c.** Documented scale-up debt: Phases 336–338 (half-and-better-half
  combine algebra, sliding raw-key windows, embedded key-format scanner)
  were bounded pilots whose own writeups defer "full-corpus/GPU scale" to
  a future phase that never ran. Not a theory — a ledger item.

---

## 11. Measurements taken while writing (inputs, not results)

- `DBBI` counts: a3 b25 c8 d4 e18 f10 g10 h8 i5 (91). `FAED` counts: a54
  b49 c52 d49 e69 f57 g107 h58 i75 (570).
- Token counts / code-IC: `DBBI {b,e}` 63 tokens, 0.0671 (nearest
  English); `FAED {g,i}` 436, 0.0743 (nearest English among 29 valid
  pairs); `FAED {b,e}` 469, 0.0988. Minimum `FAED` token count over valid
  pairs: 436.
- `FAED` sum-list digit-string lengths (row/col × 14 layouts × 2
  conventions): only **19×30 / columns / `a0i8` = 63**; others 30, 45, 57,
  62, 76, 77, 79, 80, 114.
- `DBBI` 7×13 anti-diagonal sums `a0i8`:
  `[3,2,15,20,19,23,19,25,19,27,31,21,31,27,15,22,2,6,4]`; main-diagonal
  `[1,9,14,15,30,23,26,23,12,23,15,25,24,30,21,15,9,10,6]`; 13×7 anti
  `[3,8,11,25,15,19,28,21,20,22,28,24,22,25,18,22,9,7,4]`; 13×7 main
  `[1,9,7,15,11,20,29,32,27,32,29,24,24,18,18,17,11,6,1]` (`a1i9` variants
  are these plus the per-diagonal lengths).
- `matrixsumlist` per-letter popcounts: `[5,3,4,4,4,4,5,5,5,4,4,5,4]`.
- Film Architect scene: scope 1 (boundary audit) = 69 words / 290 letters;
  the last 63 letters before "choice" are
  `MATRIXTOHERANDTHEENDOFYOURSPECIESASYOUADEQUATELYPUTTHEPROBLEMIS`; every
  suffix of length 436–484 uses all 25 letters. The puzzle's Phase 3.2
  plaintext (2,422 bytes) contains no "choice".
- `VALIDATION_ESCAPES = (1, 4)`; `ALPHA_322` has 28 slots; `VALIDATION_NUM`
  has 4 zeros in 149 digits.
- `DBBI` minus `a` = 88 symbols = 264 bits = 33 bytes.

## 12. Suggested execution order (for the later, separate pass)

1a and 1c (seconds) → 6, 4-primary, 10b (seconds) → 1b identity pass
(seconds) → 8, 9, 7 (minutes) → 2 and 1b-CSP (hours) → 5 (reading) → 4-secondary,
10a. Each item's stop rule is final for that item; a pass on any exact bar
is reported as a checkpoint, not a solve, and goes through the worksheet's
G1–G5 gates like everything else.
