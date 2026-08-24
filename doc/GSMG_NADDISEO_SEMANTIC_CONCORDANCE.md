---
type: index
status: live
date: 2026-08-24
topics:
  - naddiseo
  - concordance
  - semantic-comparison
aliases:
  - Semantic Concordance
---

# Naddiseo-versus-local semantic concordance

The full-repository audit (`doc/GSMG_NADDISEO_REPOSITORY_FULL_AUDIT.md`) was
file-complete: it confirmed nothing is hidden or missing. It was not
claim-by-claim complete: it did not check whether every *interpretive step*
the fork's notebooks take matches the step this project independently took
for the same clue. This document is that comparison, one clue at a time.
Each row records the exact source clue, the fork's interpretation, this
project's interpretation, the resulting value each side used, what
downstream work consumed that value, and a confidence/alternatives note.

Differences that change a password, key-material candidate, or other
consumed input outrank differences that only confirm an already-shared
result -- those get investigated (and, where cheap, re-tested) first.

## Entry 1 — `X2SH4Y0QB15`: the `B` and `H` variable resolution

**Exact source clue** (Phase 2 decrypted plaintext, `README.md`; identical
in both projects, byte-verified):

```text
# X 2 S H 4 Y 0 Q B 15 #
Q -> extend the name of a hackers' swordless fish, the I and W are below.
B -> ((BV80605001911AP)- (sqrt(-1)))^2
H -> (Answer to only this puzzle but nothing else) * -1
S -> cha' + (vagh * jav)
Ok kid, on the highway, let put it in the worst gear.
```

Both projects agree: `S = 32` (Klingon numerals) and `Q = 82` (Mr. Robot's
fish "Qwerty" extended to the keyboard row `QWERTYUIOP`; digits above `I`
and `W`, in that order). No discrepancy on these two.

### `B`

- **Fork interpretation** (`phase2.ipynb`, cell 4, commit `15b43fc`): the
  clue's `BV80605001911AP` is an Intel Core i5-750 processor model number.
  Read as "`i5` minus `i`", two parses are both grammatically available:
  `(5i - i)^2 = (4i)^2 = -16` ("choice 1"), or `(i5` *with* `i` removed`)^2
  = 5^2 = 25` ("choice 2"). The notebook explicitly holds both open
  ("we'll figure out which of the two choices we need later") and resolves
  it two sections down using the *output domain*: applying the `-16`
  reading inside the "worst gear" (reverse) instruction produces a
  string that parses as `61` minutes in a geographic DMS coordinate --
  not a valid sexagesimal value (minutes must be `< 60`) -- while `25`
  produces `52` minutes, valid. The fork picks `B = 25` on that basis.
- **Our interpretation** (`tools/gsmg/x2sh4y0qb15_p32_candidate_audit.py`,
  Phase 269): `RESOLVED = {..., "B": -16, ...}`, stated as "previously
  established" with no citation of the `25` alternative, the DMS-validity
  argument, or any other stated reason for preferring `-16`.
- **Resulting value:** fork `B = 25`; this project `B = -16`.
- **Downstream dependency:** this project's `B = -16` was carried into (a)
  `G-X2SH-001`'s Decentraland four-point candidate coordinates
  (`doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md`, `(-42,-16)` as one of
  the four pairs) and (b) Phase 269's full X2SH4Y0QB15 password-candidate
  sweep against all 4 tracked blobs (`COSMIC`, `P32TRAILING`, `SALPH`,
  `URLBLOB`) -- meaning that sweep never actually tested any material built
  from `B = 25`.

### `H`

- **Fork interpretation:** "`* -1`" is read as *already accomplished* by
  the semantic negation used to reach the answer: negating "answer to only
  this puzzle but nothing else" gives "answer to everything," which *is*
  the Hitchhiker's Guide's `42` -- i.e., the phrase-level negation already
  performs the instructed `* -1`, so the notebook uses `H = 42` with no
  further arithmetic step.
- **Our interpretation:** `RESOLVED = {..., "H": -42, ...}` -- the
  Hitchhiker's-Guide `42` is derived the same way, then a second, literal
  arithmetic `* -1` is applied on top of that number, giving `-42`.
- **Resulting value:** fork `H = 42`; this project `H = -42`.
- **Downstream dependency:** same two consumers as `B` above -- both used
  `H = -42` throughout.

### Confidence and unresolved alternatives

The fork's resolution is better-supported on its own terms: it has an
explicit, checkable tie-breaker for `B` (DMS-minute validity) that this
project's own docs implicitly rely on without recording -- `doc/
GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md` already calls "the
established SafeNet reading" (one global reversal producing "one standard
geographic coordinate") authoritative enough to be preferred over the
Decentraland reading, but that exact coordinate (`51°52'28.0"N
4°24'23.2"E`, near a real SafeNet/Thales facility) only reproduces under
`B = 25, H = 42` -- values this project's own scripts never used. This is
an internal inconsistency, not merely a difference of opinion: the doc
defers to a reading its own candidate-generation script doesn't test.

The `H` question is softer -- both semantic negation *of the phrase* and a
subsequent literal negation *of the resulting number* are defensible
readings of "(...) * -1" in isolation. The fork's reading is preferred here
only because it's the one that, combined with `B = 25`, reproduces a
verified real-world coordinate; this project's `-42` was never
independently checked against that same target.

Neither project treats `X2SH4Y0QB15` as consumed into the real,
already-solved 7-part password (`README.md` calls its use "unclear," and
the fork's own notebook only uses the coordinate as thematic confirmation
of the SafeNet/Luna/HSM reading already reached by other clues, not as
password material). So this discrepancy does not touch anything
already-solved. It only matters for still-open candidate-generation work
downstream of `X2SH4Y0QB15` -- which is exactly what Phase 269 is.

**Action taken:** Phase 384 (`tools/gsmg/x2sh4y0qb15_fork_resolution_delta_audit.py`)
reruns Phase 269's exact declared transform family under `B = 25, H = 42`
instead of `B = -16, H = -42`, against all 4 tracked blobs: 26 candidates,
650 unique key materials, **0 hits**. See `FINDINGS.md` Phase 384 for the
full result.

## Entry 2 — `phase0.ipynb`: Stage 0 spiral-grid decode

**Exact source clue:** the 14x14 colored-square matrix (`follow_the_white_rabbit.png`,
Stage 0's initial image; the fork's local mirror is `puzzle.png`, byte-identical
subject matter). Both projects work from the same rendered grid.

- **Fork interpretation** (`phase0.ipynb`, cells 1-6, commit `15b43fc`): reading
  order is a hand-coded spiral built from four rotating helper functions
  (`left`, `bottom`, `right`, `top`) applied in the fixed cycle
  `ordering = [left, bottom, right, top]`, each call peeling one edge off the
  shrinking matrix until it's exhausted. Blue (`b`) vs. yellow (`y`) is left
  ambiguous by the black/white channel alone (every decoded byte's *last* bit
  is the one carried by blue/yellow, so ASCII-prefix matching alone can't
  resolve it) and is instead fixed post-hoc: the notebook picks `blue=1,
  yellow=0` because that is the assignment under which the decoded bytes read
  `"gsmg.io"` as a leading substring.
- **Our interpretation** (`tools/gsmg/grid_spiral.py`, `spiral_tl_ccw()`):
  documented as "counterclockwise spiral from the top-left corner, matching
  the community README's reading order"; `bitval()` maps black/blue to `1`
  and white/yellow/FEFE to `0`. `doc/GSMG_FIRST_PIECE_COLOR_RECONSTRUCTION.md`
  independently records the same `blue=1, yellow=0` assignment, tied to the
  same "must decode to `gsmg.io`" tie-breaker, and adds a fact the fork's
  notebook doesn't state: the 24 blue/yellow cells fall exactly on spiral
  position `i % 8 == 7` (the LSB of each decoded byte) with color equal to
  that bit's parity — meaning the blue/yellow channel is fully redundant with
  black/white, not independent information.
- **Resulting value:** identical. Both projects decode to
  `"gsmg.io/theseedisplanted"`. The fork's raw cell output carries one
  trailing NUL byte (`\x00`) after that string — an artifact of the 196-bit
  grid not dividing evenly into 8-bit bytes (24 full bytes plus a leftover
  4-bit nibble, which `int('0000', 2).to_bytes(1, 'little')` turns into a
  null character); this project's `TARGET` constant is the clean 24-character
  string with no trailing byte. Not a discrepancy — same spare nibble, just
  handled differently (fork lets it decode to a stray NUL and print it; this
  project's target string simply doesn't include it).
- **Downstream dependency:** this is the puzzle's first bridge — both
  projects use the decoded URL identically to move to Phase 1
  (`gsmg.io/theseedisplanted`).

### Confidence and unresolved alternatives

No discrepancy. The two reading-order algorithms are textually different
(fork: four rotating edge-peel functions; ours: a single directional-turn
spiral walker) but verified to produce the same coordinate sequence and
decoded string — `grid_spiral.py`'s own docstring already cites this as
matching "the community README's documented reading order," so the
equivalence was already implicitly checked before this entry formalized it.
The blue/yellow resolution logic is convergent by construction: both sides
use the identical tie-breaker (decoded text must read `gsmg.io`), and this
project separately derived *why* that tie-breaker is safe (the LSB-parity
redundancy), which the fork doesn't state but is fully consistent with.

**Action taken:** none required — this entry documents full agreement, not a
discrepancy requiring rerun.

## Entry 3 — `phase1.ipynb`: icon rebus, song identification, form password

**Exact source clue:** the `theseedisplanted` page's 8 icon images
(`img/black_banking - war.png`, `blue_ca.png`, `blue_dig_i.png`,
`blue_lock_lo.png`, `red_crypto_gic.png`, `red_n_you.png`,
`red_open_lock_n_ing.png`, `red_t.png`) plus the page's hidden `<form>`
POSTing to `gsmg.io/phase1verification`.

- **Fork interpretation** (`phase1.ipynb`, cells 0-1, commit `15b43fc`):
  rearranges the icons into six phrase fragments — `"warning"`, `"crypto"`,
  `"logic"`, `"can you"`, `"dig it"`, `"+ -"` — and notes that dropping
  `"crypto"` from the search makes "The Warning" by Logic surface. It then
  brute-forces `check_password()` against `/phase1verification` over
  case/whitespace/punctuation variations of all 15 lyric lines from that
  song, and gets a `302` redirect on
  `theflowerblossomsthroughwhatseemstobeaconcretesurface` (lowercased,
  despaced line 6, "The flower blossoms through what seems to be a concrete
  surface").
- **Our interpretation** (`doc/GSMG_PUZZLE.md` Stage-1 row, corrected
  2026-07-26; symbol layer audited 2026-08-13): names the same song/artist
  and assigns each icon fragment to a specific source file — `WAR`+`NING`
  (`black_banking - war.png` + `red_open_lock_n_ing.png`) and `LO` inserted
  into `CRYPTO`/`GIC` (`blue_lock_lo.png` + `red_crypto_gic.png`) spell "The
  Warning by Logic"; the remaining fragments (`blue_ca.png`, `blue_dig_i.png`,
  `red_n_you.png`, `red_t.png`) spell "CAN YOU DIG IT" — matching the
  previous stage's own closing prompt. `tools/gsmg/phase1_icon_rebus_audit.py`
  additionally checked the icon PNGs' containers/LSBs for a second hidden
  payload (none found) and ran a 16-candidate oracle check on the
  open/closed-lock and `+/-` symbolism against all 4 tracked blobs (clean).
- **Resulting value:** identical — both projects land on the password
  `theflowerblossomsthroughwhatseemstobeaconcretesurface` and the same
  downstream URL,
  `gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself`.
- **Downstream dependency:** this is the puzzle's second bridge (Stage 1 →
  Phase 2/3 page); `doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`'s one-page chain
  already records this exact input/output pair.

### Confidence and unresolved alternatives

No discrepancy on the password or the song identification. This project's
icon decomposition is more granular than the fork's — it names which
specific icon file contributes which letters, rather than treating the
rebus as six loose phrases — but the two readings are consistent, not
competing: the fork's phrase list (`"warning"`, `"crypto"`, `"logic"`,
`"can you"`, `"dig it"`, `"+ -"`) is exactly what this project's
finer-grained per-file decomposition collapses into. This project goes
further by treating the `+/-` and open/closed-lock icons as carrying
thematic meaning ("opposites attract," matching the song's own lyric) and by
independently testing (negative) whether that symbolism selects a second
password beyond the lyric line, which the fork's notebook doesn't attempt.

**Action taken:** none required — this entry documents full agreement, not a
discrepancy requiring rerun.

## Entry 4 — `phase3.ipynb`: Jacque Fresco / White Rabbit / Heisenberg three-clue gateway

**Exact source clue:** the plaintext unlocked by the seven-part password (a
riddle mentioning "the merovingian," a "1name" digit-word blank, a Cheshire
Cat / "how long is forever" quotation with a "giveit" prefix instruction, a
physics one-liner, and a note that "Phase 3.2 is ciphered with
aes-256-cbc base64 and a sha256 pw"), plus the attached
`phase3.2-aes.txt` blob.

- **Fork interpretation** (`phase3.ipynb`, cells 2-6, commit `15b43fc`):
  identifies "the thinker" as Jacque Fresco via the Venus Project film *The
  Choice Is Ours*; identifies the Cheshire Cat quotation as "Sometimes, just
  one second," strips the leading "Sometimes," and prepends "giveit" to get
  `giveitjustonesecond`; identifies the physics clue as Heisenberg's
  uncertainty principle. Builds the password as
  `lower_connected("Jacque Fresco") + lower_connected("give it just one
  second") + lower_connected(candidate)`, live-brute-forces the third part
  over four phrasing variants against the real `openssl aes-256-cbc`
  decrypt of `phase3.2-aes.txt`, and gets a successful decrypt on
  `jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple` (SHA-256:
  `250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c`).
- **Our interpretation** (`doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`, "Stage
  3.2 — Three-Clue AES Gateway"): records the identical three parts —
  `jacquefresco`, `giveitjustonesecond`, `heisenbergsuncertaintyprinciple` —
  concatenated and hashed to the identical value
  `250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c`, marked
  **Verified**.
- **Resulting value:** identical on every part and the final hash.
- **Downstream dependency:** this hash is the AES-256-CBC passphrase that
  opens Phase 3.2's content in both projects.

### Confidence and unresolved alternatives

No discrepancy. The only difference is staging labels, not content: the
fork calls this notebook "Phase 3," while this project's stage table calls
the same three-clue gateway "Stage 3.2" (reserving "Stage 3" for the
separate, earlier seven-part SafeNet/Luna/HSM/chess-FEN password covered by
the fork's `phase2.ipynb` and this project's Phase 269/384 work, see Entry
1). Both projects independently derive the same wording corrections (the
Cheshire Cat quote needs "Sometimes," stripped before the "giveit" prefix
makes grammatical sense) and reach a byte-identical SHA-256, so this is a
genuine confirmation, not merely a coincidental final hash.

**Action taken:** none required — this entry documents full agreement, not a
discrepancy requiring rerun.

## Entry 5 — `phase3.2.ipynb`: EBCDIC/Beaufort, VIC checkerboard, P32TRAILING provenance

**Exact source clue:** the plaintext unlocked by Stage 3.2's three-clue
password — a Matrix-Architect-style monologue containing a badly-encoded
byte block, a long decimal digit string, a second riddle
(`"fubcd-king & oracle-queen, thingky mvps"`), and a trailing base64
`Salted__` AES blob.

- **Fork interpretation** (`phase3.2.ipynb`, cells 1-18, commit `15b43fc`):
  (a) isolates the byte block, brute-forces character encodings, and finds
  IBM EBCDIC code page 1141 gives 100%-ASCII output (cross-checked live via
  a CyberChef recipe link), hinted at by the "one for one, four for one"
  line in the prose; (b) recognizes the still-gibberish EBCDIC output needs
  a further classical cipher (hinted by "I've designed you a beautiful
  strategic **position**" → Beaufort), brute-forces the key and finds
  `THEMATRIXHASYOU` (from the movie's "Wake up... the Matrix has you"
  line) produces the full Architect-parody plaintext beginning `"your life
  is the sum of a remainder..."`; (c) builds a straddling-checkerboard
  alphabet from the second riddle by hand — de-duplicating letters in
  `"fubcd oracle thingky mvps"`, discovering the riddle's duplicate `c` in
  "oracle" needs to become a literal `/` board symbol rather than being
  dropped, and appending the five unused letters (`z,j,q,w,x`) plus a
  trailing `.` — yielding alphabet `fubcdora/lethingkymvpszjqwx.` with
  escape digits `1` and `4`, which decodes the digit string to `"IN CASE
  YOU MANAGE TO CRACK THIS THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF
  AND THEY ALSO NEED FUNDS TO LIVE"`; (d) states plainly that, at the time
  of writing (end of 2019), the trailing AES blob (`U2FsdGVkX1+0Wl49gnWTyi
  imluu7V3+vl7st0gUt9sWDzNLxDmlPMsDSiuW2a46zgKlIi8aaqY5gpJPPEzW1n9n3/26qs4z
  stWtPKF8Zs/BTNN4IiEh4qu18mdC0NAv4`) is unsolved and the notebook stops
  there.
- **Our interpretation** (`doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`,
  "Stage 3.2.1 — EBCDIC and Beaufort" and "Stage 3.2.2 — Keyed 9-Ary / VIC
  Checkerboard"; `tools/gsmg/data.py`'s `ALPHA_322`/`VALIDATION_*`
  constants; `tools/gsmg/data.py`'s `P32_TRAILING_BLOB_B64`): records the
  identical EBCDIC-1141 → Beaufort(`THEMATRIXHASYOU`) chain and the
  identical Architect-plaintext output (this project's summary additionally
  flags the recurring `[23, 16, 7]` figures from that text — "23 ciphers,
  16 encryptions, 7 passwords" — as matching the Architect *film* scene's
  "23 individuals... 16 female, 7 male" and this project's own first-piece
  prime-walk profile, a cross-artifact recurrence the fork's notebook
  doesn't note). For the checkerboard, this project's `ALPHA_322 =
  "FUBCDORA.LETHINGKYMVPS.JQZXW"` (28 symbols, cited in code comments as
  "hardcoded in the community's `cb2.py`," a *different* historical fork
  script, not independently re-derived from the riddle text in this
  session) with escapes `(1, 4)` is a differently-laid-out but
  board-equivalent alphabet: decoding this project's `VALIDATION_NUM` with
  either alphabet string through this project's own `build_board`/`decode`
  functions was checked directly in this session and produces the exact
  same output,
  `"INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE"`,
  confirming the two textual alphabets are the same 25-cell board under a
  different transcription, not competing hypotheses. Separately, this
  project already tracks the trailing AES blob as `P32TRAILING` — one of
  the four actively-swept ciphertext targets in `cb_common.BLOBS` — with
  provenance previously attributed to two independent sources (the official
  `puzzlehunt/gsmgio-5btc-puzzle` README and the actively-maintained
  `HosterjackAGV/gsmg-5btc-puzzle` fork's `p32_trailing` label), still
  unsolved as of this fork's own most recent update.
- **Resulting value:** identical on the EBCDIC/Beaufort plaintext, and
  board-equivalent (verified by direct decode, not just visual inspection)
  on the checkerboard plaintext. The trailing AES blob's exact bytes are
  also byte-identical to this project's already-tracked `P32TRAILING`
  target.
- **Downstream dependency:** this entry adds a *third* independent primary
  source for `P32TRAILING`'s exact byte content and its precise
  provenance location — directly following the VIC-decoded "private keys
  belong to half and better half" line in the Naddiseo fork's own primary
  transcription of the puzzle, matching this project's "80-byte OpenSSL
  blob embedded at the end of the already-solved Phase 3.2 plaintext"
  description exactly, independent of the official-README/HosterjackAGV
  sources already cited. No password/candidate material changes.

### Confidence and unresolved alternatives

No discrepancy. The checkerboard-alphabet difference initially looked like
it might be one (the two transcriptions' tail orderings are not visually
identical) but direct decode through this project's own `cb_common.decode`
confirmed both alphabet strings produce a byte-identical 25-cell board —
this is a case where surface-text disagreement had to be checked
computationally rather than trusted from inspection, and turned out to
be no disagreement at all. The `P32TRAILING` corroboration is a genuine
addition (a third confirming source), not a correction to anything.

**Action taken:** none required — this entry documents full agreement plus
one additional corroborating provenance source; no rerun needed since
`P32TRAILING` is already an actively-tracked oracle target.

## Entry 6 — `salphaseion.ipynb`: SalPhaseIon page transcription and the `shabef → sha256` gap

**Exact source clue:** the SalPhaseIon page's single continuous `<textarea>`
stream — `DBBI` (91 symbols) + an `a/b`-binary block + `FAED` (570 symbols) +
two `z`-delimited `a`-`i`/`o` decimal blocks + literal text + a base64
`Salted__` AES blob (with a second `a/b`-binary block embedded inside it) +
a trailing 12-character fragment.

- **Fork interpretation** (`salphaseion.ipynb`, cells 0-13, commit
  `15b43fc`): transcribes the full raw stream verbatim in cell 0; decodes
  the first `a/b` block (8-bit groups, `a=0,b=1`) to `"matrixsumlist"`
  (cell 3) and the second to `"enter"` (cell 5); notices the `z`-delimited
  segments use an extended `a`-`i` plus `o` alphabet, maps `a-i,o →
  1-9,0` (cell 9), and converts each resulting decimal string through
  `hex()` then `binascii.a2b_hex(...).decode()` to recover
  `"lastwordsbeforearchichoice"` (cell 11) and `"thispassword"` (cell 12);
  identifies and corrects a line-length artifact in the base64 blob (cell
  6) to recover the exact AES ciphertext. The notebook explicitly stops
  there: cell 13 ("Remaining sections") states plainly, **"So far the
  `dbbi` and `faed` strings haven't been decoded"** — it never attempts a
  checkerboard/9-ary decode of either stream, and it never revisits the
  literal-looking `"shabefourfirsthintisyourlastcommand"` /
  `"shabefanstoo"` text segments beyond quoting them as-is; no digit-remap
  is applied to the embedded `bef` substring.
- **Our interpretation** (`doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`'s
  one-page macro-message chain and "Transport decodes" table;
  `doc/GSMG_PUZZLE.md`'s 2026-07-08 gap-closing updates;
  `tools/gsmg/data.py`'s `DBBI`/`FAED`/`SALPHASEION_BLOB_B64` constants):
  records the identical macro structure — `DBBI + binary("matrixsumlist")
  + FAED + decimal("lastwordsbeforearchichoice") + decimal("thispassword")
  + literal(...) + first half of SALPH + binary("enter") + second half of
  SALPH + raw("shabefanstoo")` — with all four transport decodes
  (`matrixsumlist`, `enter`, `lastwordsbeforearchichoice`,
  `thispassword`) matching exactly. Where this project goes further:
  `doc/GSMG_PUZZLE.md` notices that the literal-looking text segment
  isn't fully literal — under the *same* `a`-`i`/`o` digit alphabet used
  for the two decimal blocks, the embedded `b,e,f` letters inside
  `"shabef..."` read as digits `2,5,6`, turning `"shabef"` into
  `"sha256"` and the full segment into `"sha256 our first hint is your
  last command"` — a real algorithm name (SHA-256) the fork's raw
  transcription doesn't surface. This project then ran a documented,
  12-candidate negative sweep on the still-unresolved trailing
  `"shabefanstoo"` fragment (literal, `sha256`-prefixed variants,
  full-digit-map variants, `a1z26` variants, guessed-target variants) —
  0/12 AES-oracle hits, 0 anagram hits — explicitly kept open as "a
  genuine unexplained fragment, not a coverage gap." `DBBI` and `FAED`
  remain fully open in this project too, matching the fork's own stopping
  point (this project's Phase 386 Bifid decode of `FAED` and the still-open
  `DBBI` checkerboard question are separate, later work not attempted in
  this notebook at all).
- **Resulting value:** identical on `DBBI`, `FAED`, `matrixsumlist`,
  `enter`, `lastwordsbeforearchichoice`, `thispassword`, and the AES blob
  bytes. This project's `sha256` reading is a genuine addition beyond
  where the fork's own analysis stopped, not a contradiction of it — the
  fork's raw transcript contains the exact same `b,e,f` characters, it
  just never re-applies the digit alphabet to that specific span.
- **Downstream dependency:** `tools/gsmg/data.py`'s
  `SALPHASEION_BLOB_B64` constant's code comment already cites this exact
  notebook cell (Naddiseo `salphaseion.ipynb` cell 6) as its provenance
  source — this entry is a direct re-verification of an already-cited
  source, not a new discovery of it. The `sha256` reading doesn't change
  the tracked `SALPH` blob or its oracle candidates; it only resolves what
  the literal instruction text says.

### Confidence and unresolved alternatives

No discrepancy. Every mechanically decoded value matches byte-for-byte.
The one place this project's record is more advanced than the fork's is
recovering `sha256` from the `shabef` fragment — the fork's notebook was
written before that substitution was noticed (or the notebook's author
simply didn't try it), and its own "remaining sections" note candidly
flags `dbbi`/`faed` as unsolved, so this isn't a case of the fork getting
something wrong — it's a case of this project's later, more exhaustive
pass finding one more layer in the same literal text the fork already
transcribed correctly.

**Action taken:** none required — this entry documents full agreement on
every mechanically decoded value, re-verifies an already-cited provenance
source, and records that this project's `sha256` reading is a downstream
extension the fork's notebook didn't reach, not a disagreement with it.

## Entry 7 — `decentraland.ipynb`: puzzlepiece audio side quest → `HASHTHETEXT`

**Exact source clue:** a 2020-02-20 Telegram hint screenshot from inside the
Decentraland virtual world showing a large question mark at coordinates
`-41,-17`, interactive there, playing an audio file
(`sounds/puzzlepiece.mp3`, content id
`QmeRy5MjmEZ2W6J3DwhQfht5HKBKXBFpoGzSkzmjeGKiDK`).

- **Fork interpretation** (`decentraland.ipynb`, cells 0-10, commit
  `15b43fc`): navigates to the parcel in-world, uses the Decentraland CLI
  (`dcl status -41,-17`) to find the audio file's content id, downloads it
  via the Content API, reads the stereo MP3, inverts one channel
  (`(-1**i)*x`, alternating-sign per sample), sums the channels back to
  mono, and plots a spectrogram — revealing a run of values between `0x29`
  and `0x3A` (41-58 decimal), recognized as the hex range covering `'A'`-`'Z'`.
  Reading the eleven hex byte values `['48','41','53','48','54','48','45',
  '54','45','58','54']` as ASCII gives `HASHTHETEXT`. The notebook ends
  there with no further interpretation.
- **Our interpretation** (`doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md`):
  independently cites "the creator's exact GSMG audio deployment at
  `(-41,-17)`," playing `sounds/puzzlepiece.mp3`, and states that "the
  already-reproduced stereo inversion and spectrogram operation yields the
  community's `HASHTHETEXT` instruction" — the identical method (channel
  invert → mono sum → spectrogram → hex-range ASCII read) and identical
  result. This project treats `HASHTHETEXT` as an "already-solved side
  quest" and a keyword already tried (unsuccessfully) against the Phase
  3.2.2 checkerboard-alphabet derivation in
  `tools/gsmg/alphabet_hypothesis_check.py`'s `ALL_TRIED_KEYWORDS` list.
- **Resulting value:** identical — `HASHTHETEXT`, from the identical
  coordinate, audio file, and signal-processing method.
- **Downstream dependency:** this project's own Decentraland coordinate
  audit (`doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md`, also the
  subject of Entry 1's `X2SH4Y0QB15` discussion) uses this exact
  confirmed deployment as one anchor point for evaluating an unrelated,
  still-open four-point coordinate hypothesis
  (`doc/GSMG_OPEN_GAP_REGISTRY.md`'s `G-X2SH-001`) — that hypothesis
  remains unconfirmed for reasons unconnected to this entry (a chronology
  conflict among the other three points), not anything raised here.

### Confidence and unresolved alternatives

No discrepancy. One cosmetic note: the fork's own "Observations" bullet
in cell 0 states the screenshot coordinates as `-41,17` (missing the
second minus sign), but its own worked "Solving" instructions two
paragraphs later correctly use `/goto -41,-17` — an internal typo within
the fork's notebook, not a disagreement with this project, which cites
`(-41,-17)` throughout and matches the fork's actually-used coordinate.

**Action taken:** none required — this entry documents full agreement;
`HASHTHETEXT` was already recorded as an already-solved community result
in this project's own docs before this entry re-verified it against the
fork's primary derivation.

## Entry 8 — `phase2.ipynb`'s "Phase 2.1" section: SafeNet/Luna/HSM identification

**Exact source clue** (the "Phase 2.1" markdown cell in `phase2.ipynb`,
distinct from the "Phase 2.1 Equation" cell — `X2SH4Y0QB15` — already
covered by Entry 1):

```text
The ironic 2name of the keymakers trying to protect the current digital
powers which are still in severe danger due to the keymaker's way of
security by hiding, nearly unprotected, in plain sight.
{eps3.4_[in one of the valleys of Phillip]runtime-error.r00., where
daughters hit magic keypads} When this fails.. Crypto finally to the
latin 3Moon? Tell me, 4How so mate?
```

- **Fork interpretation** (`phase2.ipynb`, cell 3, commit `15b43fc`):
  identifies `eps3.4_runtime-error.r00` as *Mr. Robot* Season 3 Episode 5;
  identifies "Phillip" as Phillip Price (E Corp CEO) and "daughters" as his
  daughter Angela Moss, who in that episode's plot "tampers with the HSM
  in the secure room" during a Stage-2 attack — matching "the keymaker's
  way of security by hiding... where daughters hit magic keypads." From
  there, a Google image search on "mr robot hsm" surfaces "SafeNet Luna
  G5" hardware, giving part 2 = `SafeNet` (manufacturer), part 3 = `Luna`
  (Latin `luna` = "moon," matching "the latin 3Moon"), and part 4 = `HSM`
  (from "4**H**ow **S**o **M**ate" as a leading-letter acrostic).
- **Our interpretation** (`doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`, "Stage
  3 — Seven-Part Password" table): records the identical three values —
  part 2 `Safenet`, part 3 `Luna`, part 4 `HSM` — marked **Verified** as
  part of the seven-piece concatenated password whose SHA-256
  (`1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5`) is
  also independently confirmed. `doc/GSMG_PUZZLE.md` separately lists
  `eps3.4_runtime-error.r00` among known Mr.-Robot-themed reference strings
  already tried (negatively) as a hidden-path candidate elsewhere on the
  site — a different, unrelated use of the same episode reference, not a
  contradiction of its role here.
- **Resulting value:** identical — `Safenet`, `Luna`, `HSM`, feeding the
  same seven-part password and the same final SHA-256.
- **Downstream dependency:** same as Entry 1's Part-2 finding — this
  three-part identification feeds directly into the already-Verified
  Stage-3 password hash in both projects.

### Confidence and unresolved alternatives

No discrepancy. Both projects reach the acrostic reading of "**H**ow **S**o
**M**ate" for part 4 and the same Mr.-Robot episode/character chain for
parts 2-3 independently.

**Action taken:** none required — this entry documents full agreement and
closes out the "`phase2.1`'s embedded content" item named in the original
remaining-work list (the notebook's separate "Phase 2.1 Equation" cell,
i.e. `X2SH4Y0QB15`, was already covered by Entry 1).

## Entry 9 — the 34 `hints/` images and their `README.md` captions

**Exact source clue:** the 34 dated Telegram/Discord hint screenshots under
`hints/`, most captioned in the fork's top-level `README.md` (not a
notebook) with a one- or two-sentence gloss; a handful carry an actual
transcription or decode alongside the image.

Unlike Entries 1-8, this isn't a single clue with one interpretive step on
each side — it's 34 mostly-independent items, most of which carry no
decode at all (progress-announcement or provenance screenshots only). This
project's own `doc/GSMG_NADDISEO_REPOSITORY_FULL_AUDIT.md` already opened
all 34 files at original resolution and reported: "the review confirmed
the already-documented themes... None adds text that is missing from the
current project documentation." That audit was file-complete, not
claim-by-claim, so this entry checks the *readings* the fork's captions
attach to the handful of images that carry one:

| Hint (date) | Fork's reading (`README.md`) | This project's independent record | Match |
|---|---|---|---|
| `2021-05-06-salph instructions.png` | "hash the text on the image" → `sha256("GSMGIO5BTCPUZZLECHALLENGE" + address)` → `89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32` | `doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`, "Route to SalPhaseIon / Cosmic Duality" — identical inputs and identical output hash | Exact match |
| `2023-02-23.png` | binary decode: `"yellow blue primes matrix sumlist last words before archichoice yinyang we wont give away thepassword its in front of your eyes but youre not seeing it very last step is a true give away promised"` | `doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`'s "Transport decodes" table, reversed-binary creator message row — same word sequence (word-spacing only differs) | Exact match |
| `2026-01-01-new-year-hint.png` | binary decode: `"Happy new year! Make the best of everything. Oh, and here's a 'tiny hint' <3."` | Not separately re-derived in this project's docs (flavor/morale text, no operation or password material attached in either project) | No conflict — this project simply hasn't re-transcribed it, since the fork's own notebook-equivalent commentary already marks it ambiguous ("what the hint is referring to is ambiguous") |
| `2023-08-03-2.png` ("the hardest part is done") | Fork's `README.md` speculatively reinterprets the puzzle's recurring `"..."` token as `"key"`, i.e. "Look for the key" | `doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md` tracks the same source message (Telegram `8795`/`8796`, "hardest part is done") but only as a general progress/morale signal — it does **not** adopt the `"..." → "key"` reading | Genuine but minor interpretive difference — see below |

### Confidence and unresolved alternatives

The `"..." → "key"` reading is the one place this entry found daylight
between the two projects, and it's thin on both sides: the fork's own
`README.md` hedges it as a reinterpretation ("might be replaced with
`key`"), not an asserted solve, and this project's clue ledger doesn't
mention that specific ellipsis-substitution hypothesis at all — it simply
never adopted it, not that it tested and rejected it. Per this project's
own brainstorm-discipline standard (closed candidate universes, no
open-ended new-candidate generation without strong justification), this
is not a finding that motivates new testing: it's an unconfirmed,
speculative reading on the fork's own side that this project has neither
confirmed nor needed, since `"..."` already has better-supported
resolutions in context at each place it actually appears (Phase 3's
`"1name"`/`"...` -> `causality`, Phase 3.2's `"why"` for the Architect
quote — both context-derived, not from this generic substitution rule).
The remaining 30 images carry provenance/timeline value (first SalPhaseIon
mention, halving confirmations, "additional door" mentions, spelling-error
disclaimer, "prime part" confirmation) already covered by this project's
own creator-clue ledgers and confirmed content-complete by the full
repository audit; none of them carry a decode this entry could compare
against an independent reading.

**Action taken:** none required. No password/candidate material changes;
the one minor interpretive difference found (`"..." → "key"`) is recorded
as an unadopted, unconfirmed reading on both sides, not a disagreement
requiring resolution.

## Entry 10 — `phase2.ipynb`'s "Phase 2.2" section: parts 5-7 and the final Stage-3 hash

**Exact source clue:** three remaining riddle fragments after parts 1-4
(Entries 1 and 8) — a long rambling paragraph pointing at JFK-era
executive orders ("5binary code"), a line pointing at Bitcoin's genesis
block source comment ("Part 6"), and a chess position requiring one legal
non-mating move ("Part 7").

- **Fork interpretation** (`phase2.ipynb`, cells 5-11, commit `15b43fc`):
  for part 5, chains a sequence of trivia identifications (Norton's
  theorem; U.S. presidents named John/Johnson; JFK/Jim Carrey/Jim Gates
  parallels; "the one after died too soon" = LBJ succeeding the
  assassinated JFK) to conclude the answer is a 5-bit binary Nixon-era
  executive order number, but the riddle text itself narrows this only to
  a list of 8 candidates (`11000`-`11111`), not a single value — the
  notebook says outright "We have 8 choices to choose from for part 5."
  For part 6, identifies "row 1616" of Bitcoin's original `main.cpp` as
  the genesis-block `scriptSig` comment and extracts the hex string after
  the literal `4` token in that comment. For part 7, solves the chess
  position (white to move, no legal move may deliver checkmate) via
  `nextchessmove.com`, finding `Rc6` is the unique non-mating move, and
  records the resulting FEN. It then brute-forces the concatenation of all
  seven parts (fixed parts 1/6/7, all 8 candidates for part 5, and
  lower/upper/title case for parts 2-4) against the real Phase-3 AES blob
  via live `openssl` calls, and gets a successful decrypt at
  `causalitySafenetLunaHSM11110` + the part-6 hex string + the part-7 FEN,
  SHA-256 `1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5`.
- **Our interpretation** (`doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`, "Stage
  3 — Seven-Part Password" table): records the identical final three
  parts — part 5 `11110`, part 6 the identical genesis-block hex string,
  part 7 the identical post-move FEN — and the identical final SHA-256
  `1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5`,
  marked **Verified**. This project's summary also independently notes
  "the original chess prompt and the post-move answer are different
  positions; substituting the prompt FEN is incorrect" — the same
  pre-move/post-move distinction the fork's notebook makes by explicitly
  labeling its answer "the next situation," not the position as given.
- **Resulting value:** identical on every part and the final hash.
- **Downstream dependency:** this hash is the already-Verified SHA-256
  passphrase opening the seven-part-password-gated Phase 3 material in
  both projects (the plaintext that, per Entry 4, instructs solving the
  three-clue `jacquefresco`/`giveitjustonesecond`/`heisenberg` gateway).

### Confidence and unresolved alternatives

No discrepancy. Worth noting explicitly: neither project has a clean
textual derivation that narrows part 5 to `11110` specifically from the
riddle prose alone — the riddle only narrows it to 8 same-length
candidates, and both projects settle on `11110` the same way, empirically,
by brute-forcing the small candidate set against the real AES ciphertext
rather than deducing it from the text. This is a shared methodological
trait, not a gap unique to either side, and this project's table already
marks part 5 **Verified** on that same empirical basis.

**Action taken:** none required — this entry documents full agreement and
closes out the last uncovered section of `phase2.ipynb`, completing the
walk of all six fork notebooks plus their embedded sub-sections.

## Entries 11+ — not yet built

Every notebook and named sub-section from the fork's repository has now
been walked (Entries 1-10). The 34 `hints/` images were surveyed at the
caption level in Entry 9; a full per-image walk was judged unnecessary
given `doc/GSMG_NADDISEO_REPOSITORY_FULL_AUDIT.md`'s existing
file-complete review. If new fork content appears (a repository update,
or discovery of interpretive material this pass missed), extend this
document following the same schema as Entries 1-10, ranking
password/input-altering discrepancies above confirmation-only ones.
