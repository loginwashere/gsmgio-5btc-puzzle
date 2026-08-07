# GSMG Fresh Brainstorm — 2026-08-06

Date: 2026-08-06. Status: **raw brainstorm, explicitly unverified.** Per instruction,
this pass prioritizes breadth over rigor — generate many candidate paths and clues,
review/falsify later. Nothing here should be treated as a finding until it goes
through the project's usual null-model / oracle discipline. Ideas are grouped by
theme; each is flagged `[FRESH]` (not covered by existing docs/FINDINGS.md as far as
this pass could tell), `[NEW ANGLE]` (touches a known object but from an angle not
yet tried), or `[REVISIT]` (previously closed, but worth a narrow reopen for a stated
reason).

Source context for this pass: `doc/GSMG_BIRD_VIEW_REASSESSMENT.md`,
`doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md`, and a research-agent summary of the
remaining docs + `tools/gsmg/FINDINGS.md` (147 phases) + wordlists/tooling inventory.

## 1. The `SalPhaseIon` heading — a new anagram, not yet pursued

**Status update (2026-08-06): tested same day, closed negative, all three
proposed sub-checks now covered.** See `tools/gsmg/FINDINGS.md` Phases 148
and 153, and `tools/gsmg/salphaseion_aphelion_anagram_audit.py`. The anagram
itself is real, but a base-rate check found `APHELION` is only 1 of 9
equally-valid 8-letter dictionary sub-anagrams of the heading's letters
(unlike the `VAT` rebus, which is a unique string difference) — not
distinguishing. Zero mentions of `aphelion`/`perihelion` anywhere in the
creator's corpus. Oracle check (126 keystrings x 4 blobs) came back 0 hits.
The doc's own "15 letters" claim below for `Cosmic Duality` was wrong (it's
13); `perihelion` does not fit that multiset either (missing `p`, both
`e`s, `r`, `h`, `n`) — checked in Phase 153. Retained below for the record;
do not re-pursue this specific reading.

`[FRESH]` All prior heading work (Phases 96-99) tried the elemental parse
(`SALPHATION`/`SALVATION`) and the `VAT` letter-replacement rebus. Neither tried a
**plain anagram against the page's own theme** ("Cosmic Duality"). Checked directly
in this session:

```text
SALPHASEION (11 letters: s,a,l,p,h,a,s,e,i,o,n)
- APHELION    (a,p,h,e,l,i,o,n)   uses 8 of the 11 letters exactly once each
= leftover: s, s, a  ->  "SAS" or "ASS"
```

`aphelion` (a body's farthest point from the sun) is the natural cosmic-duality
counterpart to `perihelion` (nearest point) — a genuine astronomical duality pair,
thematically tighter than the chemistry reading and not yet tested at all. Worth
enumerating:

- Does `perihelion` fit any other on-page string (it needs an `r`, which
  `SalPhaseIon` lacks — check `Cosmic Duality`'s own letters instead)? **Checked
  (Phase 153): `Cosmic Duality` is 13 letters, not 15 as originally stated
  here; `perihelion` does not fit it either (missing `p`, both `e`s, `r`, `h`,
  `n`).**
- What is `SAS`/`ASS` for — a leftover discard (like `VAT`'s source sentence), a
  three-letter key fragment, or noise that kills the hypothesis? Moot — the
  base-rate downgrade in Phase 148 already closes the whole reading regardless
  of what the leftover would have meant.
- Does `aphelion` recur anywhere in the Telegram export, the Cosmic Duality book, or
  community chat (creator confirmation check, same protocol as the `VAT` rebus)?
  **Checked (Phase 148): zero mentions.**

**2026-08-06 addendum — has `SALVATION` itself ever been anagrammed?** A
direct chat question caught a real gap: every prior `SALVATION` phase
(96-105) either derives the word from the heading or applies a fixed
reading to its own letters; none ever ran an open-ended anagram search of
`SALVATION`'s own 9 letters. See `tools/gsmg/FINDINGS.md` Phase 159 and
`tools/gsmg/salvation_anagram_audit.py`. Result: `SALVATION` is the
**only** dictionary word with its exact 9-letter multiset (a clean,
newly-confirmed uniqueness fact) — but 253 dictionary words fit as
sub-anagrams and 105 dictionary-word *pairs* form exact two-word full
anagrams, far too large and undifferentiated a space to mine (the same
base-rate trap as the `APHELION` reading above, one step further). Closed
negative without an oracle run — no single candidate clears the bar to
test.

## 2. `matrixsumlist` consumer problem (the single most concrete open item)

**Status update (2026-08-06): closed, but the "all four bullets tested"
claim below was premature — caught by a direct chat audit and now actually
true.** See `tools/gsmg/FINDINGS.md` Phases 150, 153, and **160**. While
scoping this, found that Phase 51 (`matrixsumlist_31_feasibility_audit.py`)
already tests `[23,16,7]` as indices into the 31-char selection *and* as
repeated-Caesar shift values over it. Two clauses inside the first two
bullets were initially glossed over rather than tested, caught on a later
audit pass (Phase 153): `[23,16,7]` as indices into the 8-item macro-clue
token list (1-based-mod-8 wraparound gives a repeated, degenerate 2-of-3
selection, not escalated) and `[23,16,7]` as a Caesar shift applied
specifically to the `BUT`/`HYE` rails (12 non-language outputs, 216
keystrings, 0 hits) rather than only to the 31-char `TARGET`. The
self-digit-sum sweep was separately absorbed into Phase 149's registry
check. The REVISIT bullet (DBBI-vs-itself and DBBI-vs-FAED-folded-to-91
through the matrix-sum-select grammar, plus extending Phase 51's
literal-index probe to the full 91-char DBBI/plaintext inputs) is closed via
Phase 150: 352 candidates, 3,744 keystrings, 4 blobs, 0 hits.

**2026-08-06 correction (Phase 160):** the "all four bullets" claim above
was wrong on two counts. (1) Phase 153 asserted without checking that "the
macro-clue token list" and "the ordered phase title list (8 items)" (both
named in bullet 1) are the same object — they aren't; the puzzle has its
own real, sourced 8-stage progression (Stage 0 … SalPhaseIon) distinct from
the macro clue's 8 decoded fragments, and it was never actually tested.
(2) bullet 3 named three iteration/round-count readings of `[23,16,7]`;
only the Caesar-shift-on-`BUT`/`HYE` one had been tested — "23 rounds of a
keystream" and "16-byte AES block alignment" were untouched. Both closed
now: the phase-title-list indexing gives a non-degenerate pair
(`Phase 3.2.2`, `SalPhaseIon` — the real endpoints of the known solve
chain, unlike the degenerate macro-token repeat), and "N rounds of a
shift-K keystream" reduces to one shift of `N*K mod 26` for every
round/amount pair drawn from `{23,16,7}`. 40 candidates, 666 keystrings,
0 hits. 16-byte block alignment was confirmed already-covered by every
candidate this project has ever tested (`cb_common.py` always sweeps
AES-128/192/256), not a gap at all. The consumer question narrows but
remains open — see Phase 150's closing note on what's still genuinely
untried.

The recovered 31-character DBBI selection has no confirmed consumer. New framings,
none of which require re-opening the closed feasibility sweep (Phase 51) since they
change *what* is fed in, not just how it's read:

- `[FRESH]` Read "matrix sum list" as **three separate literal words/operations**
  rather than one compound noun: (1) build a matrix, (2) sum it, (3) *list* the
  result — i.e. the output is meant to be read positionally as a **list of
  indices**, not a string. Try using `[23,16,7]` as 1-based indices into the DBBI
  selection itself, into the macro-clue token list, or into the ordered phase title
  list (8 items) rather than into Architect dialogue.
- `[FRESH]` Self-referential digit-sum check: `574061` digit-sums to `5+7+4+0+6+1=23`
  — already equal to the row-sum total. That's either a nice internal consistency
  check or a coincidence; worth systematically digit-summing every other
  creator-confirmed number in the chain (`163`, `91`, `570`, `1075`, `104`) and
  looking for more matches before trusting any one of them as signal.
- `[NEW ANGLE]` Treat `[23,16,7]` as **iteration/round counts** rather than
  selectors — e.g. 23 rounds of a simple keystream, 16-byte (AES block) alignment,
  7 as a Caesar/ROT shift applied to something already decoded (the `BUT`/`HYE`
  rails, or the 31-char selection itself).
- `[REVISIT]` The matrix-instruction pipeline (Phase-tested, 0 hits) always paired
  DBBI against the *Phase-3.2.2 answer* or *Architect dialogue*. It never paired
  DBBI against **itself** (autocorrelation: DBBI matrix summed against a
  row/column-shuffled copy of DBBI) or against **FAED folded to 91** (already built
  in `cross_target_coupling_sweep.py`'s fold modes, but not through the
  matrix-sum-then-select grammar specifically).

## 3. Steganography / metadata pass on the repo's own image files

**2026-08-06 follow-up (Phase 162): a direct question ("did you fetch from
Wayback first?") caught a real gap for 4 of the 7 files.** `phase2.png`/
`phase3.png`/`SalPhaseIonCosmicDuality.png`/`theseedisplanted.png` were
never independently re-verified against Wayback (Phase 5 pulled them from
a community fork repo) -- but re-fetching wouldn't have helped: they're
browser screenshots of HTML pages, not served image assets, so there's
nothing standalone for Wayback to have archived. `puzzle.png` and
`gsmg_rabbit_hint.png` *are* now confirmed byte-identical to genuinely
served/mirrored copies. More usefully, the question prompted checking the
local Wayback mirror's `img/` directory for real served assets never
examined at all: found 7 (`background-full.jpg`, `background-full-1440.jpg`,
`bg-tablet-left.jpg`, `logo_medium.png`, `background-center.png`,
`favicon_small.png`, `popup_img_error.png`). Two contain a real (not just
theoretical) `iTXt` chunk -- the first non-empty metadata anywhere in this
project's image history -- but both are the identical, completely empty
generic Adobe XMP export boilerplate. All closed negative; see Phase 162.

**Status update (2026-08-06): all four bullets tested, all closed
negative.** See `tools/gsmg/FINDINGS.md` Phase 161 and
`tools/gsmg/image_stego_metadata_audit.py`. No `exiftool`/`zsteg`/`binwalk`
binaries are installed here and there's no root to add them; used the
pure-Python `exifread` package instead (verified it actually works before
trusting a negative result) and reimplemented zsteg's/binwalk's core
techniques directly (multi-channel/multi-bit-order LSB scoring;
magic-byte signature scan). Both JPEGs have 0 EXIF tags, including the
genuine 2019 creator original (`gsmg_stage0_original_telegram.jpg`,
traced to community-export message 28507 and confirmed byte-identical --
Telegram strips photo metadata server-side, not an anomaly). LSB
printable-ratios are all <=5.4% across every channel/bit-order/PNG, no
tEXt/zTXt/iTXt/eXIf chunks, no trailing bytes after any IEND. A handful of
incidental 2-byte GZIP/BMP magic-byte matches inside compressed PNG data
were checked and confirmed to be base-rate noise (count matches
filesize/65536, no valid header follows), not real embedded files. First
corrected a scope error in the bullet below: `photo_2020-04-26_09-24-30.jpg`
isn't rabbit-grid content, it's a Decentraland screenshot of the
already-solved `-41,-17` puzzle piece — its filename date has no corpus
corroboration either way and doesn't even match Telegram's own export
naming convention, most plausibly just a personal device save timestamp.

`[FRESH]` — genuinely doesn't appear anywhere in the summarized docs, which focus on
manually-parsed pixel colors (the spiral mask) rather than generic stego tooling.
This repo has `puzzle.png`, `phase2.png`, `phase3.png`, `SalPhaseIonCosmicDuality.png`,
`theseedisplanted.png`, and `photo_2020-04-26_09-24-30.jpg` sitting at the repo root.
Cheap, standard, not yet logged as done:

- Run `exiftool` on every image (especially the JPG — cameras/screenshot tools embed
  timestamps, GPS, software strings, and sometimes comment fields the creator forgot
  to strip).
- Run `zsteg` (PNG/BMP LSB steganography) and `binwalk` (embedded-file/archive
  carving) on every PNG.
- Run `strings` over each file looking for accidental plaintext in metadata chunks
  (tEXt/zTXt/iTXt PNG chunks, JPEG COM segments).
- The JPG filename itself encodes a date, `2020-04-26` — check whether that date is
  independently meaningful (a Telegram post date, a BTC block timestamp, an
  anniversary) rather than just a phone's auto-naming.

## 4. On-chain / DNS forensics — channels not covered by any doc summary

**Status update (2026-08-06): all four bullets tested, all closed
negative — but the first one surfaced a real trap worth flagging.** See
`tools/gsmg/FINDINGS.md` Phase 156 and
`tools/gsmg/onchain_op_return_provenance_audit.py`. The OP_RETURN check
found 105 previously-undocumented text messages on the two known
creator-controlled addresses — and the content is suspiciously on-the-nose
for this project's own vocabulary (`SalPhaseIon`,
`matrixsumlistenterlastwordsbeforearchichoicethispassword`, etc.), which
is exactly the shape a fabricated/injected result would take. Verified
genuinely on-chain across three independent explorer backends, but then
checked *who signed* each transaction (an OP_RETURN only proves authorship
by the input signer, not by whoever a payment output happens to be sent
to): zero of the 105 come from either genuine creator address. 88 of them
trace to the exact two addresses `GSMG_PUZZLE.md`'s existing scam-thread
writeup already flagged as a single fabricated "solution" recycled across
10+ GitHub issues — on-chain graffiti from that same campaign, not creator
content. CT-log enumeration found one new subdomain (`beta.gsmg.io`, plus
`slack-invite.gsmg.io`), both now just the same expired-domain parking
page as the root, and the one non-parking capture found on `beta.gsmg.io`
(a `/puzzle` PNG) hashed byte-identical to the already-known `puzzle.png`.
Historical DNS TXT records aren't obtainable with the free tools
available here (noted as a capability gap, not tested-negative).
Wayback's original HTTP headers for the 2020 puzzle-page capture are
ordinary Laravel/Cloudflare boilerplate, nothing hidden.

`[FRESH]`

- **OP_RETURN / dust transactions** on the puzzle's known BTC addresses (the prize
  address and any solved-phase addresses). Puzzle creators occasionally leave
  messages via `OP_RETURN` or tiny "dust" sends with a note in the accompanying
  service (some explorers show attached messages). Worth a scripted check via a
  block explorer API even if this searches wide.
- **Certificate Transparency logs** (`crt.sh`) for `gsmg.io` and `*.gsmg.io` — the
  existing audit ruled out `help.gsmg.io` as a puzzle dependency via page content,
  but a CT-log subdomain enumeration is a different, broader technique that could
  surface subdomains never crawled by Wayback at all.
- **Historical DNS TXT records** for the domain (via any archived `dig`/DNS history
  service) — some puzzle setups hide a hint or hash in a TXT record.
- **HTTP response headers** from the Wayback capture (`ETag`, `Last-Modified`,
  custom `X-` headers) — not mentioned as reviewed anywhere in the doc summary;
  Wayback's raw capture metadata can preserve these.

## 5. Idiolect / OSINT on the creator

**Status update (2026-08-06, revised): initial pass only covered ONE of two
local Telegram exports — see the correction below.** See
`tools/gsmg/FINDINGS.md` Phases 154 and 155,
`tools/gsmg/community_shutdown_retrospective_audit.py`. A second export,
"GSMG - Community & support group" (52,851 messages, 5,419 from the
creator — 10x the puzzle-solvers corpus every prior phase used), was found
sitting unused on the same machine. It enforces a "no puzzle talk" house
rule throughout (confirmed, not a hidden clue trove), but contains the most
candid message the creator has ever posted: an April 2026 company-shutdown
retrospective confirming, in their own words, that the puzzle really was
"inspired by other crypto puzzles" (no specific one named) and built in
"two sloppy days... zero polish" — direct first-party confirmation of Phase
154's inferred framing. It also reveals the literal GSMG acronym
("Globally Supporting My Generation") and the phrase "the better half" used
autobiographically — see item 7's update for why that matters and why it
was deliberately not pursued further. 7 candidates drawn from this message
(`SYDNEY`, `THEBETTERHALF`, `GLOBALLYSUPPORTINGMYGENERATION`, etc.) tested
0 hits. No second puzzle/ARG/CTF by this handle was found anywhere online.
The handle `Jrk Bgrt`/`gsmg-jrkbgrt` does correspond to a real GSMG.io Help
Center support-content author account — the creator most plausibly reads as
an actual GSMG.io team member running one personal side-project, not a
professional ARG designer with a reusable "house style." Deliberately did
not chase coincidental "jrkbgrt" hits on unrelated platforms
(Kaggle/YouTube/Wikimedia/Xbox) — a bare handle
collision isn't evidence of common identity, and pursuing it would cross
from handle-level research into unfounded identity-linking.

`[FRESH]`

- Search whether the creator (handle-level, not doxxing) has authored or
  participated in *other* puzzles/CTFs under the same or a linked handle — puzzle
  authors often reuse a personal "encoding signature" (favorite cipher families,
  favorite books, favorite misdirection style). If a second puzzle by the same
  author exists with a published writeup, its solution mechanics could be a strong
  structural prior for this one.
- Full-text search the Telegram export (already mined for content) specifically for
  *meta* commentary about their own design process — e.g. any offhand remark about
  "the way I always do X" or a favorite reference work, rather than in-puzzle clue
  text. This is a different extraction target than prior passes (which pulled
  clue-relevant lines, not authorial-style lines).

## 6. `SalPhaseIon` / spiral-image CSS and page-source micro-structure

`[NEW ANGLE]` The spiral-image color-order trick (Phase 0) proves this creator does
hide sub-channel information in per-pixel/per-character styling. That technique has
never been pointed at the **text page itself**:

- Audit the archived HTML/CSS for the `SalPhaseIon` and `Cosmic Duality` headings
  for any per-character `<span>` wrapping, inline `style=`, non-default font,
  `letter-spacing`, or color that a naive text-extraction pass would flatten away
  (exactly the class of thing `page_structure_audit.py` checked for the textarea
  bodies, but apparently not for the headings/labels themselves).
- Check computed CSS class names, not just literal styles — class names can
  themselves be a hidden token (`class="phase-7-marker"` style leaks).
- Check the page `<title>`, meta description, and favicon file for anything besides
  the obvious.

## 7. "half and better half" — an unexplored *semantic* reading

**Status update (2026-08-06): all three proposed roles now tested, all closed
negative — but surfaced a real, unresolved convergence with item 11.** See
`tools/gsmg/FINDINGS.md` Phases 151-152 and
`tools/gsmg/trinity_resurrection_half_audit.py`. No literal "other half" line
exists between Neo and Trinity in the real screenplay, but Trinity's
resurrection speech verifiably opens with "I promised to tell you the rest" —
the word `promised` is also the still-unused final token of the creator's own
macro clue (item 11 below). Role 1 (literal passphrase, Phase 151): 9
quote-derived candidates, 0 hits. Role 2 (KDF salt/context, Phase 152): 2,700
combined materials via the same construction `hash_duality_sweep.py` already
uses for prior command hashes, 0 hits. Role 3 (checkerboard alphabet seed,
Phase 152): confirmed genuinely untested first (bare `neo`/`trinity` are
absent from every wordlist the checkerboard sweeps actually draw from), then
15 decodes across 5 seeds x established escape pairs, 0 oracle hits (a few
isolated clue words inside gibberish, treated as expected noise per this
project's own Phase 21 base-rate precedent, not signal). The `promised`
convergence itself is retained as an interesting but unquantified
coincidence, not a finding — see Phase 151 for why it wasn't pushed further.

**2026-08-06 addendum — the Matrix-literary framing may be the wrong prior
entirely.** Phase 155 (item 5's follow-up) found the creator uses the exact
phrase "the better half" *autobiographically*, for a real romantic partner,
in an unrelated April 2026 company retrospective — not quoting or alluding to
the Matrix. That doesn't reopen the negative AES results above (those tested
specific candidate families regardless of interpretation), but it's a real
update to the prior: "half and better half" may simply be the creator's own
natural phrase for "myself and my partner," not a literary rebus at all. This
project's scope explicitly stops at public phrases the creator chose to post
— it does not and will not attempt to identify the partner or any other real
personal detail, which would be doxxing regardless of puzzle relevance. If
this angle is revisited, it should be reframed around that boundary, not
around finding more Matrix-adjacent quotes.

`[NEW ANGLE]` Current treatment (Phase 78) is purely structural: split an 80-byte
blob into two 32-byte keys. Not tried: a **thematic** reading tied to the Matrix
source material already established as load-bearing (Architect scene, `choice`,
`salvation of Zion`). In the trilogy, Trinity is repeatedly framed as Neo's
counterpart/"other half." If the creator is working the Architect scene this
directly elsewhere, it's worth at least checking (cheaply) whether `NEO`/`TRINITY`,
or the exact screenplay line where that framing occurs, feeds either half as a KDF
salt/context string or a checkerboard alphabet seed — bounded to a handful of exact
quotes, not a dictionary expansion.

## 8. Re-examine "zeroed out" as genuinely plural

**Status update (2026-08-06): tested same day via full palette enumeration,
closed negative.** See `tools/gsmg/FINDINGS.md` Phase 157 and
`tools/gsmg/repo_wide_palette_anomaly_audit.py`. Extracted the complete
color histogram of every image in the repo (27 files, root + `doc/img/`)
and flagged minority near-white/near-black grayscale colors — the same
structural shape as the original FEFEFE marker. Along the way, resolved a
mislabeling: `puzzle.png` isn't a separate image from the "rabbit hint"
grid, it *is* the full original asset (grid + rabbit silhouette + a footer
below a red divider bar); every `gsmg_rabbit_hint*` file is a crop of it,
which also explains away what looked like a second red-pixel anomaly (it's
the genuine divider bar caught at a crop edge). Restricting to images that
are actually flat/computer-generated graphics (the only class where a
minority-color test is diagnostic), `#FEFEFE` is the **only** anomaly,
confirmed present at every resolution/crop of the grid image this repo
has, and nowhere else. The Cosmic-Duality-era screenshots do show a tiny
(2-20 pixel) near-white antialiasing residue at identical counts across
different-content images — checked directly to rule out a script bug, real
but almost certainly shared browser/font rendering chrome, categorically
smaller and differently-shaped than FEFEFE's solid 625-pixel grid-cell
block. Verdict: FEFEFE remains the sole marker; the plural reading isn't
supported by anything currently in the repo.

`[NEW ANGLE]` Only one `FEFEFE` marker has been resolved as a "zeroing" event
(Phase 48). If the creator's phrasing is plural ("some characters need to be zeroed
out"), search systematically for **other** anomalous/out-of-palette hex values across
every image in the repo (not just the spiral), the same way FEFEFE was found —
i.e., extract every distinct color actually used per image and diff against the
expected 2-3-color palette, rather than assuming the spiral image is the only place
such a marker could occur.

## 9. Numeric coincidence sweep as a triage tool, not a proof

**Status update (2026-08-06): built and run same day, no signal above noise.**
See `tools/gsmg/FINDINGS.md` Phase 149 and
`tools/gsmg/numeric_coincidence_triage.py`. A first draft including sum/product
mod 9 small primes was itself a methodological error (132 pigeonhole-guaranteed
"hits" on the value 7 alone) and was removed. The corrected exact-arithmetic-only
run reproduces the two already-known relationships (`23=16+7`, `91=7x13`) as a
sanity check, plus 8 new but individually unremarkable coincidences that don't
clear the bar for a dedicated follow-up. Kept as reusable infrastructure for when
new numbers get added to the registry.

`[FRESH]` Build one small script that takes every creator-confirmed "load-bearing"
number in the project (`574061`, `23`, `16`, `7`, `163`, `91`, `570`, `1075`, `104`,
`80`, `31`, `21`) and checks pairwise arithmetic relationships (sum, difference,
digit-sum, product mod small primes, concatenation) automatically, purely to
generate a ranked shortlist of "suspicious" relationships for a human to look at —
explicitly not to promote any hit without the usual null-model gate. This turns
ad hoc noticing (like the `574061` digit-sum match in section 2) into a repeatable
triage step instead of one-off pattern spotting.

## 10. Physical book — widen beyond content search once the replacement copy arrives

`[NEW ANGLE]` The completed review found no *readable* hidden content in the 1991
Time-Life "Cosmic Duality" book, but that pass was a content/OCR sweep. Physical
puzzle hides sometimes aren't in the printed content at all:

- Bibliographic/paratextual data: exact ISBN, LCCN, Dewey number, print-run/edition
  code on the copyright page, price printed on the dust jacket — try these as raw
  candidate strings, not just book *content*.
- Physical inscription/marking on the creator's actual copy (dedication, stamp,
  underlining, dog-ear, or a loose insert) — only detectable from the real object,
  not a generic OCR of the text; worth explicitly asking whoever inspects the
  replacement copy to check for this before OCR-only triage.
- Gatefold pages 57-58 specifically: confirm on arrival whether they're a genuine
  fold-out (more physical page than the rest of the book) before assuming it's just
  two more ordinary pages worth of text.

## 11. `promised` — the very last macro-clue token, functionally unused

**Status update (2026-08-06): closed — both halves of the bullet now
covered, and the provenance half surfaces a reframe of the premise.** The
operational half was already done before this pass (`tools/gsmg/
FINDINGS.md` Phase 109: literal passphrase, 0 hits; Phase 151/152: KDF
context and checkerboard-seed roles via the Trinity-quote convergence, 0
hits). This session closed the other half — "check whether the creator
ever explains, gets asked about, or reuses the literal word `promised`
elsewhere in the export," the same treatment `anstoo` got in Phase 102 —
via `tools/gsmg/promised_provenance_audit.py` (Phase 158). Read every
community mention across both Telegram corpora individually (not just
counted): the creator never engages with it as a keyword; most community
mentions just re-paste the known macro-clue string; and the one genuine
piece of community theorizing found (message 48341, Pomyk, previously
unlogged) reads `promised` as a colloquial grammatical tag on "a true
giveaway" rather than a discrete 8th instructional token. That's not a
proof, but it's the best-supported reading on record, and it's consistent
with all three negative oracle results rather than in tension with them —
if `promised` was never meant to be extracted as a standalone unit, three
separate ways of trying to consume it as one would be expected to fail.
Do not re-open without a new source (community or creator) treating
`promised` as a keyword rather than a sentence ending.

`[FRESH]` The eight-item macro clue ends on `promised`, and prior work has treated
the chain as ending at `verylaststepisatruegiveaway`. Check whether `promised` has
been given an actual operational role anywhere, or whether it's been implicitly
absorbed into "promised land"/Zion flavor text without a concrete test. If unused,
it's worth a narrow pass: same treatment as `anstoo` got in Phase 102 — check whether
the creator ever explains, gets asked about, or reuses the literal word `promised`
elsewhere in the export.

## 12. Deliberately not re-litigated here

To keep this pass additive rather than repetitive, the following are *not*
reproposed, per the closed-path ledger in `GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md` and
`GSMG_BIRD_VIEW_REASSESSMENT.md`: generic keyword/dictionary expansion, monoalphabetic
DBBI/FAED recovery under already-tested escape pairs, the elemental `SALVATION`
rebus as a direct password, dual-ternary/periodicity routes, hash-duality
constructions over the four known prior hashes, cross-phase "yang" color-mask
linkage, and any additional CBC/KDF/Key-Wrap cipher-mode sweep against the existing
curated candidate lists (that oracle axis is exhausted for current candidates; new
candidates from sections above would still need to go through it once produced).

## Suggested next step (not taken in this pass)

Per the user's instruction this round was breadth-first and explicitly unverified.
A future pass should pick 2-3 of the `[FRESH]` items above — the anagram (§1), the
image stego/metadata pass (§3), and the numeric-coincidence triage script (§9) are
the cheapest to actually execute — and run them for real, then fold verified
results (or closures) back into `FINDINGS.md` following the project's existing
phase-numbering convention.
