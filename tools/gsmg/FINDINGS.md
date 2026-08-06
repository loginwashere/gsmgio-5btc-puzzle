# GSMG.io "Cosmic Duality" — Dictionary-Scale Sweep: Findings

Run date: 2026-07-03. Companion to [doc/GSMG_PUZZLE.md](../../doc/GSMG_PUZZLE.md).

## TL;DR

**Negative result across every phase.** No candidate — hand-picked or dictionary-scale —
opened either the `SALPH` or `COSMIC` AES blob. This corroborates the community's own
`FINDINGS.md` conclusion: the endgame is not a simple missing-keyword problem.

## Phase 0.1 — "your last command" direct probe

`lastcommand_probe.py`: tested 28 curated candidates (derived from the decoded hint
"our first hint is your last command" — prior-stage URLs, literal command phrasings,
the hint text itself, the known 3.2.2 answer) directly against the literal embedded
`SALPHASEION` blob.

**Result: 0/28 hits.**

## Phase 0.2 — alphabet-derivation hypothesis check

`alphabet_hypothesis_check.py`: ran all 49 keywords ever tried (by the community fork
and by this project) through `pad28()` and checked for an exact match against the
known-good 3.2.2 alphabet (`FUBCDORA.LETHINGKYMVPS.JQZXW`).

**Result: no match.** The "keyword → `pad28` → alphabet" model that `joint_attack.py`
(and by extension `cosmic_sweep.py`) assumes for new candidates is **not verified**
against the one ground-truth case available. This doesn't disprove the model — the
3.2.2 keyword may simply not be in the tried list, or may use a different construction
rule entirely — but it means every negative result below should be read as "this model,
swept hard, found nothing," not "no keyword-based decode exists."

## Phase 2 — dictionary-scale sweep

`cosmic_sweep.py --target both`, curated + mid-size wordlists (no rockyou/Pwdb — those
stay opt-in for a follow-up run per the implementation plan):

| Wordlist | Candidates |
|---|---|
| `wordlists/gsmg/phrases.txt` + `phrases-joined.txt` | 108 |
| `wordlists/cypherpunk/phrases.txt` + `phrases-joined.txt` | 213 |
| `wordlists/bitcoin-historical/phrases.txt` + `phrases-joined.txt` | 166 |
| `wordlists/gutenberg/phrases.txt` + `phrases-joined.txt` | 218,415 |
| `/usr/share/dict/american-english`, `british-english`, `cracklib-small` | 262,591 |
| **Total unique candidates** | **338,905** |

Each candidate was swept across both digit-mappings × all 45 escape-digit pairs ×
both targets (`dbbi`, `faed`) × several answer-normalization forms × both blobs —
**677,810 total keyword-tests**, run in 1517s (~25 min) on 16 cores at ~447/s.

**Result: 0 hits.**

## What this does and doesn't tell us

- It's a genuine, much larger negative result than anything previously public — the
  community's own joint attack covered ~20 keywords (4904 decode-forms); this covers
  ~339k keywords (677,810 keyword-tests) — roughly 140× the candidate-keyword coverage.
- It does **not** mean the checkerboard-keyword hypothesis is wrong. Per Phase 0.2, the
  `pad28()` alphabet-construction model itself is unverified, so a real keyword could
  still fail to produce a hit here simply because the alphabet-building rule is
  different from what's assumed (e.g. a different padding/ordering scheme, or a
  transposition/over-encryption layer this sweep didn't also vary per-candidate).
- `faed`'s flat IoC (~0.118, ≈ uniform over 9 symbols) continues to look like
  high-entropy data rather than checkerboard-enciphered text — sweeping it was cheap
  insurance, not a strong hypothesis.
- Two creator hints surfaced in this pass that nobody's automated scripts appear to
  target: the 2021-04-01 **"another door might be found on {1},{4},{21}"** hint and its
  2021-12-26 follow-up (prime numbers + "some characters need to be zeroed out"), plus
  the "neo's passport" Matrix Easter-egg reference. These describe what looks like a
  *separate*, still-open sub-puzzle, not obviously the same thing as `dbbi`/`faed` — not
  chased further here, but worth a dedicated look if this is revisited.

## Phase 3 — resolving the alphabet-derivation gap (2026-07-03, follow-up)

Phase 0.2 left the `pad28(keyword) → alphabet` model unverified. This phase closes that
gap by tracing exactly how the one ground-truth alphabet (3.2.2's
`FUBCDORA.LETHINGKYMVPS.JQZXW`) was actually produced, using the community fork's
`README.md` (`halbgott29a/gsmgio-5btc-puzzle`, fetched fresh via `gh api` — not
previously pulled into this repo's scratchpad).

**Finding: `pad28()`'s construction rule is provably wrong, and the real mechanism is
not a formula at all.**

1. Direct inspection of the ground-truth alphabet string shows its two literal `.`
   characters sit at raw indices **8 and 22**. `pad28()`/`cb2.py`'s `pad()` always
   produces dots at indices **8 and 18** (`s[:8]+"."+s[8:17]+"."+s[17:26]`) — a
   structural mismatch that means `pad28()` could never have reproduced the real
   alphabet from *any* input string, keyword or otherwise.
2. The fork's `README.md` documents the real derivation directly: the 3.2.2 alphabet
   comes from a **riddle sentence**, not a keyword —
   *"A fubcd-king & oracle-queen, thingky mvps, on a sad board but as wide as the first
   one seen."* A human reader extracts `FUBCD`, `ORACLE`, `THINGKY`, `MVPS` from the
   wordplay (`-king`/`-queen` are decorative, not literal), dedupes letters in reading
   order (a `.` marks each real collision — `ORACLE`'s second `C` collides with `FUBCD`'s
   `C`), then appends the leftover unused alphabet letters after one more separator dot.
3. Mechanically reproducing exactly these steps in Python yields
   `FUBCDORA.LETHINGKYMVPS.J{QWXZ perm}` — **23 of 28 characters match the ground truth
   exactly, including both dot positions** (8 and 22); only the internal order of the 5
   left-over tail letters (`JQZXW` vs `JQWXZ`) differs, evidently a manual/arbitrary
   choice made when typing the string into dcode.fr's tool, not a governed rule.
4. The community's own `FINDINGS.md` (fetched alongside the README) independently
   reaches the identical conclusion, in their own words: *"the checkerboard alphabet is
   one of the natural keyword candidates — it isn't. The alphabet is a 26! space... ⇒
   Without the correct interpretation that fixes the alphabet (the 'first hint'), the
   endgame is computationally unbreakable from our position."* Their own joint 4-parameter
   attack (~16 keyword alphabets) was explicitly framed as low-probability for this exact
   reason — not an oversight we're the first to catch, but independently re-derived and
   now confirmed at the byte level in this repo.

**What this changes:** every negative result in Phase 2 (and the community's 4904-test
joint attack before it) is now explained, not just observed. `pad28(candidate)` was
never capable of producing a puzzle-real alphabet — for *any* candidate, dictionary-scale
or otherwise — because these alphabets are hand-built from a specific riddle sentence's
wordplay, not generated by a reusable formula. This means the deferred rockyou/Pwdb
follow-up sweep (338,905 → 14M+ candidates) would **not** meaningfully improve the odds:
the problem was never coverage, it was the model. Pulling that lever further is not
recommended.

**What would actually move this:** per both this analysis and the community's own
conclusion, the missing ingredient is an **analogous riddle/interpretive sentence for
the Cosmic Duality stage** — something in the style of "A fubcd-king & oracle-queen..."
that a human would need to recognize and hand-parse into a 26-28 symbol alphabet, the
same way 3.2.2's was solved. This is a fundamentally different kind of task (pattern-
recognition over existing hint text/images/chat, not keyword brute-forcing) and is where
the previously-flagged, still-unexplored "another door {1},{4},{21}" / primes / "zeroed
out" hint and the "neo's passport" reference become newly relevant — those are exactly
the kind of wordplay-riddle candidates worth re-reading with this lens, rather than any
new dictionary sweep.

## Phase 4 — the "another door" / prime / neo's-passport hints (2026-07-04)

Phase 3 pointed at the creator's still-unresolved 2021 hints as the most promising
lead. Pulling the full 181k-line community chat export (`chat_transcript.txt`, fetched
via raw.githubusercontent.com — the GitHub contents API only inlines base64 for files
under ~1MB, and this one is 7.2MB) surfaced the exact chronological sequence, richer
than the previously-extracted `creator_jrk.txt` filtering:

| Date | Message |
|---|---|
| 2021-04-01 | *"Hint: 'another door might be found on {1},{4},{21}'"* (posted on April Fools' — the creator's 2021-04-18 follow-up, "Do you know what usually happens on the first of april?", casts some doubt on it) |
| 2021-12-02 | *"There is / Another / D O O R"* (spelled one word per message — reaffirms it's real, 8 months later) |
| 2021-12-26 | *"...We've seen prime numbers being mentioned; well, that is definitely an aspect which is required to proceed. Furthermore, along the way, some characters need to be 'zeroed out'..."* |
| 2021-12-31 | *"The only date I give away is the expiry date of neo's passport."* — confirmed via web search: Neo's passport in *The Matrix* (1999) shows an expiry date of **September 11, 2001**, a well-documented prop Easter egg. |

**This exact hint thread is heavily discussed by the community (298 mentions in the
chat) but was only partially tested by the fork's own tools:**
- `prime_theory.py`/`prime2.py` tested whether dbbi's letter `b` correlates with
  prime *string positions* — inconclusive, not re-litigated here.
- `triangle_zero.py`/`matrixtri.py` tested prime/blue/yellow-cell zeroing *within the
  "matrixsumlist triangle" framework* (dbbi as a 14×14 triangle, faed row-sums XOR'd
  against it) — this whole framework was separately falsified as apophenia (see
  Phase 2's "what this does and doesn't tell us"), so no further motivation there.
- **Neither tests these hints as direct AES passphrases, nor as a "zero the digit at
  prime positions" transform applied directly to the *validated* checkerboard-decode
  pipeline** (as opposed to the falsified triangle/XOR pipeline). That gap is what
  `tools/gsmg/door_prime_passport_probe.py` fills.

Tested:
1. **31 direct-AES-passphrase candidates** (raw + sha256-hex, both blobs): literal
   `"1421"`/`"142001"` forms, the 1st/4th/21st primes (2, 7, 73) in several encodings,
   and the passport date (`09112001`, `911`, `20010911`, etc.) alone and combined.
   **Result: 0/31 (62 keystring attempts).**
2. **Prime-position zeroing on the real decoder**: zero the digit at every prime
   (1-indexed) position, at every non-prime position, and at exactly positions
   `{1,4,21}`, in dbbi's and faed's digit-stream (both `a0i8`/`a1i9` mappings, escapes
   1,4 — the community's own frequency-based escape-digit conclusion), decoded
   against the one alphabet we can actually verify (`ALPHA_322`, since no other
   alphabet has ever been confirmed). **Result: 12 decode-forms tested, 0 hits.**

(Aside, not evidence: dbbi's characters at positions 1, 4, 21 happen to spell "d",
"i", "e" — noted only because it's the kind of coincidence the fork's FINDINGS.md
warns produces false confidence in a 9-symbol alphabet; not pursued further.)

**Caveat that keeps this from being a clean falsification:** `ALPHA_322` is almost
certainly the *wrong* alphabet for dbbi/faed (Phase 3 established each stage's
alphabet is hand-built from its own riddle sentence) — so the prime-zeroing test in
particular is weak evidence either way. The direct-passphrase test is the more
solid negative of the two.

## Phase 5 — independent image forensic audit (2026-07-04)

The fork's steganography claim ("no trailing data after IEND, no text chunks in any
PNG") was made in the context of the *earlier*-stage images (`puzzle.png`,
`theseedisplanted.png`) — never explicitly re-confirmed for the Cosmic-Duality-era
images (`SalPhaselonCosmicDuality.png`, `phase2.png`, `phase3.png`). Rather than take
that on faith, pulled all six puzzle images fresh from the fork repo and audited them
directly (`tools/gsmg/` scratchpad script, not committed — see below): full PNG chunk
walk with CRC verification, trailing-bytes-after-IEND check, tEXt/zTXt/iTXt/eXIf
chunk dump, JPEG EXIF dump, and an R-channel LSB printable-ratio check on all six.

**Result: clean across the board.** No CRC mismatches, no trailing data, no
ancillary text/EXIF chunks, no LSB-plaintext signal (printable ratio 0.000–0.042,
consistent with noise) in any of the six images — extending the fork's claim to
cover the Cosmic-Duality-specific images explicitly, not just the earlier ones.

A color-palette comparison also confirms *why* there's nothing to find: `puzzle.png`
(the one image with a confirmed visible-encoding mechanic — blue/yellow special
squares read via 14×14 spiral) has a small palette dominated by a few pure saturated
colors (`(63,72,204)` blue, `(255,242,0)` yellow at 5.1%/3.1% of pixels). The three
Cosmic-Duality-era images instead have smooth anti-aliased gradient palettes with no
comparable pure-color cluster — and viewing them directly confirms why: all three are
literal **browser screenshots of the puzzle's own webpages** (URL bar and browser
chrome visible in-frame), not puzzle-native encoded assets. Everything in them
(the Phase 2/3 riddles, the chess FEN, the AES blobs) is plaintext already
transcribed into the fork's README and this project's `data.py` — there is no
additional hidden layer to extract, because there's nothing encoded in the images
themselves to begin with.

## Phase 6 — checking for genuine post-fork progress (2026-07-04)

The fork's `FINDINGS.md` and its 181k-line chat export were both added in the *same*
commit, 2026-06-13 — three weeks before this check, not years. There's essentially no
gap in the chat data itself to re-scan. What *can* be checked is whether anything has
happened since on the wider community's GitHub activity:

- The fork repo (`halbgott29a/gsmgio-5btc-puzzle`) has had exactly one commit since
  2026-06-13 (the PR merge that added the FINDINGS.md itself) — no further activity.
- The main community repo (`puzzlehunt/gsmgio-5btc-puzzle`) has a burst of new issues
  in the last month, several from the last few days. On inspection, **all of the
  "solved"/"breakthrough" ones are fabricated or spam**, matching the exact pattern
  already documented in `doc/GSMG_PUZZLE.md`'s "What's been tried" section:
  - **#97 "Prize Claim" (2026-07-02)**: "proves" ownership of two addresses
    (`1JG648y...`, `145ZQ9s...`) that are **not the actual puzzle address**
    (`1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`), then asks for the prize to be sent to a
    *third*, unrelated address. Classic bait — signing a message for an address you
    already control proves nothing about solving anything else.
  - **#91 "[BREAKTHROUGH] Phase 6+ Solved" (2026-06-29)**: contains a literal
    unfilled template placeholder (*"SHA-256 of complete address list: [hash dos 12
    endereços concatenados]"*) and offers a 10% bounty to whoever "finishes" the
    solve for them — not a real result.
  - **#94 "flag{8KJ}" (2026-06-13)** and **#96 (French, 2026-06-18)**: both recycle
    the *exact same* already-public candidate-keyword list
    (`matrixsumlist, enter, lastwordsbeforearchichoice, thispassword, matrixsumlist
    [duplicated], yourlastcommand, secondanswer`) dressed up with confident-looking
    but unverifiable hex values. `#94`'s script has mixed Indonesian comments and a
    CTF-style `flag{}` output that doesn't match this puzzle's actual reward format
    (a raw private key, not a flag string).
  - **#69 "SOLVED" (2025-12-27)**: its "new solution key" numeric stream is just the
    already-known, already-published Phase 3.2.2 validation number (`VALIDATION_NUM`
    in this repo's own `data.py`) relabeled as if newly derived.
  - **#88 (2026-03-29)**: re-dresses the "XOR triangle" idea as a fresh insight — this
    is the same "matrixsumlist triangle" hypothesis this project's Phase 2 writeup
    already noted was independently falsified as apophenia (38k-random-string
    null-model test, see the fork's own `FINDINGS.md`).
  - Ground truth check: the puzzle address's **on-chain balance is unchanged**
    (1.2563451 BTC, last movement 2026-05-16 — before any of these issues existed).
    Nothing has actually been solved.
  - **#92 "Seeking reproducible definition of ca / cosmic_A..." (2026-06-04,
    marcofortina)** looked like the one genuine, serious thread — a well-defined
    `cosmic_A`/`ca` XOR-operand gap, already flagged in `doc/GSMG_PUZZLE.md`'s "still
    open" section. Follow-up comments (through 2026-06-11) show marcofortina ran a
    broad OSINT sweep (65 forks, 82 issues, Wayback CDX) and found **no public
    reproducible definition** of `ca`/`cosmic_A`/`row1-row4`/`K_I1`. A second
    researcher (ektemfg) independently hit the identical wall on 2026-06-15.
    **Tracing the terminology back (2026-07-04) changes the assessment**: `cosmic_A`
    originates from exactly one account (`GalloClaudio64`, 2 comments total in the
    repo — one of them on issue #69, already flagged above as a fake "SOLVED" post)
    making unverifiable, hand-wavy claims with no code or artifact ever shown, then
    amplified verbatim by other accounts months apart. Naddiseo (a credible source
    cited elsewhere in `doc/GSMG_PUZZLE.md`) publicly dismissed a closely related post
    in the same thread as *"soup. Complete Nonsense"* and warned *"Large Language
    Models like ChatGPT and Claude cannot solve this puzzle."* A separate, carefully
    hedged post (issue #82) independently found no transformation over the public
    artifacts produces the real prize key. **Updated read: `cosmic_A`/`ca` is most
    likely fabricated terminology, not a real gap — marcofortina and ektemfg's
    diligence is genuine, but the thing they're chasing probably isn't real.**

**Net: no genuine new findings anywhere in the last month, on any front.**

## Phase 7 — full read-through of all 411 creator messages (2026-07-04)

Rather than only keyword-searching the creator's Telegram export (as Phase 4 did for
door/prime/passport), read all 411 of his messages end-to-end looking for any other
riddle-style wordplay in the style of the 3.2.2 alphabet hint ("A fubcd-king &
oracle-queen..."). This surfaced two raw binary-encoded messages not present in any
of this project's or the fork's tracked material — both traced to ground and found to
be already-resolved, not new leads:

1. **A 2023-02-23 space-separated binary message.** Decoding requires reversing the
   *entire* 1288-bit stream as one unit (not per-byte) before regrouping into bytes —
   worth noting because a naive per-byte bit-reversal produces mostly-printable
   characters but in backwards byte order, which looks like a clean decode until you
   read it. Correct decode: *"yellowblueprime matrixsumlist lastwordsbeforearchichoice
   yinyang we wont give away the password its in front of your eyes but you're not
   seeing it very last step is a true giveaway promised."* Checked against the chat:
   the community decoded this same message years ago (line 20392 of the export) and
   all four named terms are already in the fork's and this project's tested-keyword
   lists. Not new.
2. **A 31.03.2019 binary message** (three weeks *before* the puzzle's public launch),
   reposted/quoted at least 8 separate times through 2025. Decodes (direct byte
   grouping, no reversal needed) to a reversed-text riddle plus a Caesar-shifted
   fragment: *"HOW DID CAESAR SEND HIS MESSAGES? AND WHAT IF 13 IS DEFAULT AND THE
   NUMBER C IS THE 2ND HINT?"* followed by `uhpryhwkhfruuhfwklqwwrsurfhhgwrwkhqhawvwdjh`.
   Brute-forcing all 26 Caesar shifts gives a clean hit at **shift 3**: *"REMOVE THE
   CORRECT HINT TO PROCEED TO THE NEXT STAGE."* (A 2025-10-10 chat post already tried
   to solve this but used the wrong shift and got a non-answer — "heprove the correct
   hint..." — so this corrected phrase had never actually been tested as a candidate
   anywhere.) Chased it anyway: the very next part of the same message is a base64
   string that decodes to a **literal Rick-Roll YouTube URL**
   (`dQw4w9WgXcQ`). The community fully resolved this as a troll back on 2024-03-16
   (chat: *"idk but all is solved in the rick roll one"*) — the entire "Caesar cipher"
   chain is an elaborate joke from the creator, not a real hint, predating the puzzle
   itself. Confirmed, not pursued as a candidate.
3. A third binary message (2025-12-31, New Year's) decodes cleanly to *"Happy new
   year! Make the best of everything. Oh, and here's a 'tiny hint' <3."* — the scare
   quotes are the tell; no cipher or keyword content follows. Pure holiday banter.

**No previously-unflagged riddle-style hint was found anywhere in the full 411-message
set.** Everything else in the export is either already-documented material (the Roses
poem, "another door"/prime/passport, the repeated "no hints" refrain) or non-technical
chatter (holidays, personal life, trolling). This closes out the "read every message"
lever as thoroughly as it can be closed.

## Phase 8 — chasing the alphabet directly: raw text, chat structure, and the
Decentraland audio (2026-07-04)

Spent additional time specifically hunting for the missing Cosmic Duality riddle
sentence (analogous to 3.2.2's "A fubcd-king & oracle-queen..."), beyond the
message-by-message read-through in Phase 7:

- **Raw SalPhaseIon page text** (`salph_raw.txt`): re-read in full. Contains only the
  already-known encoded strings and the "your last command" trailer — no embedded
  natural-language riddle.
- **Structural scan of the full chat** for the *style* of the known riddle (rare
  hyphenated word-pairs, since "fubcd-king"/"oracle-queen" are invented compounds):
  extracted and counted all 1,145 hyphenated word-pairs in the 181k-line export. Every
  one is mundane technical/community jargon (`straddle-checkerboard`, `baby-step
  giant-step`, `diffie-hellman`, etc.) — nothing resembling the riddle's style.
- **The Decentraland audio** (`puzzlepiece.mp3`, coordinates `-41,-17` — confirmed
  against the creator's own "Only -41,-17 matters" chat message): downloaded via a
  direct IPFS content-addressed link posted in chat (content-addressed storage, so
  still fetchable), confirmed to be the genuine original (has the "Logic Pro X 10.4.1"
  encoder tag a chat message flagged as missing from a suspect re-hosted copy).
  Independently re-derived the community's documented process (split stereo, invert
  one channel, mix, spectrogram) with a from-scratch numpy STFT (not just trusting
  ffmpeg's renderer or the community's claim) — reproduces a real, structured signal
  (not a downscaling artifact: survives a careful from-scratch re-implementation,
  though the letter shapes are genuinely hard to read cleanly by eye). Consistent with
  the community's documented "HASHTHETEXT" answer. **This is moot either way**: per
  the fork's own README, this hint is listed separately from the main solve chain and
  only ever functioned as a process instruction ("hash the text") toward *reaching*
  the SalPhaseIon page — it predates Cosmic Duality and cannot contain that stage's
  alphabet riddle even if perfectly decoded.

**No analogous riddle sentence for the Cosmic Duality alphabet was found anywhere in
the material available** — not in the creator's messages (Phase 7), not in the raw
page text, not in the wider chat's structural patterns, and the one remaining
unverified channel (audio) turns out to be scoped to an earlier stage regardless.
This is as thorough a search as is practical without new external information (e.g.
a genuine new creator hint, or access to something not currently archived anywhere
accessible).

## Bottom line

**Six independent lines of attack have now returned negative on this endgame:** the
dictionary-scale keyword sweep (Phase 2), the alphabet-derivation model itself
(Phase 3 — confirmed structurally wrong, explaining Phase 2's result), the creator's
two most-discussed still-open hints read literally (Phase 4), an independent image
forensic audit (Phase 5), a check for genuine post-fork community progress (Phase 6
— found only fabricated "solved" spam, on-chain balance unchanged), and a full
read-through of every creator message the export contains (Phase 7 — two previously
undecoded binary messages found, both traced to already-resolved dead ends: known
keywords and a Rick-Roll troll). None of this is a coverage problem — every
hypothesis cheap enough to be worth trying, tried or re-verified, has come back
empty. What's missing, per both this analysis and the community fork's own formal
conclusion, is either a genuinely new creator hint, or an interpretive leap (an
as-yet-unrecognized riddle sentence for Cosmic Duality, analogous to 3.2.2's) that
nobody — community or this project — has found. GSMG stays parked; there is no cheap
lever left to pull.

## Phase 8 — Architect/Gnostic synonym sweep (2026-07-15)

Prompted by a user question: since the creator's own Telegram export has him saying,
unprompted, *"the mid age enc tech, mathematic, art and gnostic context are really
matter"* (`chat_mined_lines.txt:5311`) and separately laying out Gnostic/Manichaean
dualism (dual gods, one of matter, one of light — `chat_mined_lines.txt:5431-5436`),
checked whether "Demiurge" and the wider Gnostic vocabulary behind The Architect had
ever been tried. They hadn't — every prior sweep had `ARCHITECT` itself and the
in-script Matrix character roster (Oracle, Merovingian, Keymaker, Twins, Trainman,
Persephone, Seraph, Niobe, Hamann, Sati, Deus Ex Machina, Logos, Nebuchadnezzar,
Gnosis, etc. — all present in `wordlists/gsmg/matrix_trilogy.txt` and covered by the
2026-07-12 curated-wordlist sweep), but nothing from outside the movie scripts.

Surveyed the Matrix wiki's Architect page and its linked character/concept pages
(Oracle, Merovingian, Persephone, Seraph, Trainman, Keymaker, Twins, Niobe, Hamann,
Lock, Sati, Rama-Kandra, Deus Ex Machina, the Kid, Bane, the Source, 01/Machine City,
the Zion fleet's ship-name meanings) via web search (direct `matrix.fandom.com`
fetches 402'd through the fetch tool — domain-wide, not page-specific) for vocabulary
that exists only in fan-wiki/mythological commentary, not in the movies' actual
dialogue (and therefore wasn't caught by the script-based sliding-window sweep):
Gnostic Demiurge's three names (Yaldabaoth, Saklas, Samael), Manichaeism, Sophia,
Pleroma, Archon, Aeon; the Oracle's Pythia/Delphic/"Temet Nosce" framing; Seraph's
Seraphim/"burning ones" etymology; the *Resurrections*-only ships/terms (Mnemosyne,
Synthient) and the *Enter the Matrix* game-only ship (Brahma); and Architect-speech
compounds not elsewhere tested as tight no-space keywords (`integralanomaly`,
`pathoftheone`, `machinegod`, `persephoneskiss`, etc.).

Built `wordlists/gsmg/architect_gnostic_synonyms.txt` (47 candidates, all confirmed
absent from every existing tested wordlist first) and ran the real `cosmic_sweep.py`
pipeline (both digit-mappings x all 45 escape pairs x all normalization forms) against
both `dbbi` and `faed`: **0 hits, 94 keyword-tests.** Also flagged but did not chase
(out of scope for this pass — not Architect/Gnostic-related): two creator lines from
the same chat block that have never been analyzed anywhere in this project, *"Look at
divisor of 504."* and *"To whom all matters are returned."*

Net: genuine new negative result, not a re-test. Closes the Gnostic-vocabulary gap
specifically; doesn't change the Phase 7 bottom line.

**Continued (2026-07-15, same session): actually followed the wiki's own hyperlinks,
not just search-summary guesses.** The first pass used a web-search tool as a
workaround for `matrix.fandom.com` 402'ing through the direct page-fetch tool
(confirmed domain-wide, not page-specific) — search summaries are good for "what are
this character's key facts" but don't surface a page's full link list or its
deep-trivia sections. Found that direct `curl` to the Wayback Machine (`web.archive.org`)
works even though the fetch tool itself refuses that domain, so re-pulled full raw text
for The Architect, The Oracle, The Merovingian, Paradise Matrix, Nightmare Matrix, and
Monsters, and extracted the Architect page's actual `<a href>` list rather than
guessing which characters it links to. That surfaced pages not found by search alone:
Paradise Matrix / Nightmare Matrix (the two failed proto-Matrices), Monsters (in-world
"supernatural" exiles), Councillor West (real name Cornel West, cites his 1982 book
*Prophesy Deliverance* + Freemasonry's "Great Architect" + Hindu Brahma/Kali Ma as
Architect/Oracle parallels), Zionites (Matrix Online faction — checked, filler MMO
server-name list, no signal).

New terms this pass, not caught by the first Gnostic-synonym batch or any prior sweep:
Freemasonry's "Great Architect", Kali Ma / "Goddess of Time" (Oracle's Hindu parallel),
Cornel West / *Prophesy Deliverance*, "dangerous game" (Architect's own phrase for the
Oracle's gambit), redpills, seventh version (per *Resurrections* retcon — the Oracle
now "responsible for the key principles behind the 7th 'current' version"), Club Hell,
Le Vrai (the restaurant), Cain, The Effectuator, The General, "Holy Blood, Holy Grail"
(the Merovingian-dynasty-as-Jesus'-bloodline book referenced in his trivia section),
Dionysus, "Operating System" (Kid's description of the pre-Exile Merovingian),
Paradise Matrix, Nightmare Matrix, Baelroth, Garden of Eden, Kurt Gödel/incompleteness
(cited in the Paradise Matrix page's philosophical-interpretation section — Gödel's
"consistent or complete, not both" mapped onto Architect-vs-Oracle), Vamp Prime, and
Seraph's own self-description "protects that which matters most" (notable for
echoing, thematically, the still-unanalyzed creator line "To whom all matters are
returned" — flagged, not chased, still out of scope for this pass).

Built `wordlists/gsmg/architect_wiki_deepdive.txt` (35 candidates, confirmed absent
from every existing wordlist), ran the same `cosmic_sweep.py` oracle pipeline against
both `dbbi` and `faed`: **0 hits, 70 keyword-tests.** Combined with the first batch:
**129 new Architect/Gnostic/Matrix-wiki keyword-tests this session, 0 hits total.**

**Continued further (2026-07-15): automated the `riddle_combinations.txt` pattern
instead of hand-picking.** That file already established, by hand, that combining the
confirmed creator-hint anchors (`yellowblueprime`/`matrixsumlist`/
`lastwordsbeforearchichoice`/`yinyang`/`goodpuzzlesdontneedhints`, etc.) with one extra
word — concatenated or space-joined, either order — is the project's best-validated
combination idiom; it had only ever been done for a handful of manually-picked lines
(55 total). Automated it: crossed the 16 known creator-hint anchor tokens (the ones
listed in `alphabet_hypothesis_check.py`'s `joint_attack.py`/`cb2.py` provenance,
excluding generic non-riddle-specific tries like `NEO`/`THEONE`) against the 82
Architect/Gnostic/wiki terms gathered this session (both orders, concatenated + spaced
= 4 forms each), plus the same 82 terms prepended/appended to the confirmed 4-anchor
decode block (`yellowblueprimematrixsumlistlastwordsbeforearchichoiceyinyang` and its
spaced form). `wordlists/gsmg/anchor_x_vocab_combos.txt`, 5,576 unique candidates.
Ran the real `cosmic_sweep.py` oracle (both digit-mappings x all 45 escape pairs x all
normalization forms) against both `dbbi` and `faed`: **0 hits, 11,152 keyword-tests**
(171s total). Deliberately did *not* do a blind cross-product of the large mined
wordlists (`chat_mined_words.txt` is 20k+ lines — crossing two such lists is ~10⁸
candidates, hours of oracle time for near-zero expected signal per this project's own
prior overfitting warnings); this stayed targeted to the validated anchor-based idiom.

**Continued further (2026-07-15): the in-franchise yin-yang connection, distinct from
the puzzle's own "Cosmic Duality" book angle.** User asked how "yinyang" connects to
The Matrix specifically. This project had only ever tied `yinyang` to the *puzzle's*
Cosmic Duality book (Time-Life's *Mysteries of the Unknown*, exhaustively tested,
0 hits, 2026-07-12) — never to the franchise's own yin-yang symbolism. Checked: it's
real and filmmaker-placed, not fan inference — the Oracle wears actual yin-yang
earrings on screen (most visible in *Revolutions*), the Architect/Oracle pairing is
explicitly "Father"/"Mother" of the Matrix (balance vs. unbalance the equations), and
a film-analysis essay (wylfing.net's Reloaded/Revolutions breakdowns) has a section
literally titled "The Yin and Yang of Neo": Neo/Smith as "opposite sides of the same
character," Neo as Christ in films 1/3 and "the Serpent" in film 2, resolved by
stepping into "the middle path between the opposites" ("the light and the dark are
one. The One."). Built `wordlists/gsmg/yinyang_matrix_symbolism.txt` (20 candidates:
`yinyangearrings`, `theyinandyangofneo`, `middlepath`, `thelightandthedarkareone`,
etc.), confirmed all absent from every existing wordlist, ran the real oracle against
both `dbbi`/`faed`: **0 hits, 40 keyword-tests.**

Running total this session: **~11,340 keyword-tests across four targeted batches**
(Gnostic-synonym, wiki-deepdive, anchor-cross, yin-yang-in-franchise), all against the
real AES oracle, 0 hits. Doesn't change the Phase 7 bottom line.

**Correction + continuation (2026-07-15, same session): all four batches above used
the wrong tool — re-ran under the current model.** All four had used `cosmic_sweep.py`
(`pad28()`, brute-forces all 45 decimal escape-pairs x 2 digit-mappings), but this
project's own 2026-07-07 finding established that model as structurally superseded for
`dbbi`/`faed` specifically: frequency analysis locked the escape pair to `{b,e}` and
forces a 25-symbol `pad25()` board, and `cosmic_sweep_9ary.py` is the tool that
replaced it. Re-ran all four wordlists (`architect_gnostic_synonyms.txt`,
`architect_wiki_deepdive.txt`, `anchor_x_vocab_combos.txt`,
`yinyang_matrix_symbolism.txt` — 5,678 unique candidates combined) through
`cosmic_sweep_9ary.py` against `dbbi` (default `b,e`) and `faed` (both its mirrored
escape pair `h,e`, per the 2026-07-12 finding, and the unmirrored default `b,e` for
completeness): **0 hits, 17,034 keyword-tests** (dbbi 5,678 + faed×2 11,356), all under
1s each thanks to the ~45x combinatoric reduction the 9-ary model gives.

**Then tested the Architect/Oracle duality structurally, not just as vocabulary.**
Split this session's Architect/Gnostic/wiki vocabulary into two themed sublists —
`wordlists/gsmg/architect_coded.txt` (31 terms: Demiurge/Yaldabaoth/Saklas/Samael,
"Father of the Matrix", Prime Program, Great Architect, Brahma, Deus Ex Machina,
causality, Gnosticism/Manichaeism — order/creation/balance-themed) and
`wordlists/gsmg/oracle_coded.txt` (26 terms: Pythia, Temet Nosce, Seraphim, Kali
Ma/"Goddess of Time", Persephone's Kiss, Sophia/Pleroma/Aeon, redpills, "dangerous
game", Mnemosyne, the yin-yang/middle-path terms — change/choice/unbalance-themed) —
then tested each *only* against its themed blob (Architect-coded to `dbbi`, Oracle-
coded to `faed`) instead of the usual symmetric everything-vs-both. Also tested the
reverse polarity (Architect-coded to `faed`, Oracle-coded to `dbbi`), since which blob
is "his" and which is "hers" is itself an unverified assumption. All four
combinations, both faed escape-pair hypotheses where applicable: **0 hits, 171
keyword-tests.**

Running total this session: **~28,500 keyword-tests**, spanning both the deprecated
and current cipher models, symmetric and asymmetric blob-assignment, all against the
real AES oracle. All negative. Doesn't change the Phase 7 bottom line.

**Continued (2026-07-15): tail-fill/drop-letter/topology axis sweep — the correct
"option 2", after a self-correction.** Initially proposed re-testing an "asymmetric
segment-split" board (mirroring 3.2.2's real dot positions at string index 8/22
vs. `pad28()`'s always-8/18) for the *current* 9-ary model. On inspection this doesn't
actually apply: the dot/filler-position question is specific to the deprecated
28-symbol decimal model, which has 2 "wasted" slots (26 real letters can't evenly fill
8+10+10=28) requiring literal `.` placeholders. `pad25()`'s 25-symbol board has no
such waste — 25 real letters exactly fill 7+9+9=25 slots, no dots, nothing to
mis-place. The actually-analogous open variable, per `pad25()`'s own docstring, is the
**tail-fill order**: even in the one validated case, "3.2.2's real tail order, `JQZXW`,
didn't match `pad28()`'s formula-generated `JQWXZ`" — an already-flagged, already-
tooled (`--tail-fills`, `--all-drop-letters`, `--topologies` on `cosmic_sweep_9ary.py`)
gap that every sweep this session had left at defaults (`drop=J`, `tail_fill=forward`,
`topology=top_first`).

Ran the full combined vocabulary (same 5,678 candidates as the tool-correction re-run)
across all 26 drop-letters x all 3 tail-fill orders x both topologies (156 board
variants per candidate) against `dbbi` and `faed` (`h,e`): **0 hits, 5,678 candidates
x 156 variants x 2 targets ≈ 1.77M board configurations checked**, ~553s + ~601s.

Running total this session: **~28,500 keyword-level tests plus a ~1.77M-configuration
structural axis sweep**, all against the real AES oracle, all negative. This closes
out the drop-letter/tail-fill/topology axis for this vocabulary specifically (not
exhaustively for all wordlists — the broader curated set was already covered on
2026-07-07/12 under narrower axis settings). Doesn't change the Phase 7 bottom line.

**Closed as a non-lead (2026-07-15): "Look at divisor of 504" / "To whom all matters
are returned" — debunked, not just untested.** These two lines (`chat_mined_lines.txt`
4526-4527) sit in a block mixing Thelema, tarot, and Cicada 3301 references, which
also contains the already-tested `UNBALANCEDEQUATION` line — so it read plausibly
creator-flavored. Pulled the real speaker-attributed source
(`halbgott29a/gsmgio-5btc-puzzle`'s `_work/chat_transcript.txt`, not just the locally
flattened/speaker-stripped mining) and checked: the whole block was posted 2021-01-18
by a community member named **"Saber ^:)> (---}> ¿¡×( ;) <><"** (769 messages,
active Oct 2020-Mar 2024) — it does not appear anywhere in `creator_jrk.txt` (the
creator-only export). The community immediately suspected impersonation ("wtf is with
saber?" / "I think he is puzzle creator fake account"). **Saber himself denies being
the creator** ("im not creator of this puzzle... not even creators fav player"), and
**the real creator (Jrk Bgrt) explicitly disavows it three messages later** ("I can
solemnly promise you I'm not using any other accounts besides my own"). Not a hint —
a community member's mystical-troll performance, denied by its own author and
disavowed by the creator. Closed; do not re-test.

**Lead 2 — real chat phrases instead of synthetic combos (2026-07-15).** Rather than
re-run the already-negative 2026-07-11 whole-corpus coined-word/hyphenated-compound
scan, scoped this narrowly: pulled the real speaker-attributed 51,177-message export
(`halbgott29a/gsmgio-5btc-puzzle`'s `_work/chat_transcript.txt`) and extracted every
line mentioning any of this session's Architect/Oracle/Gnostic/Matrix-character theme
words (architect, oracle, gnostic, demiurge, merovingian, yin-yang, duality, seraph,
keymaker, trainman, persephone, brahma, kali), excluding "Saber" (per the lead-1
debunk above) — 1,412 unique lines. Checked the creator's own messages specifically
first: only one, dated 2025-04-28 — *"Did anyone found yingyang? I don't think so,
you guys are so smart, when yingyang is reached, 2 hours max."* — already present in
the locally-mined `chat_mined_lines.txt` (not a new discovery) and consistent with,
not adding to, the already-established understanding that yin-yang is the final gate.

Ran the 1,412 theme-lines through `riddle_content_words.py` (the same raw +
stopword-filtered content-word extraction validated by reproducing 23/28 characters of
the real 3.2.2 alphabet) to get 2,622 candidates, then through `cosmic_sweep_9ary.py`
(default axis settings) against `dbbi` and both `faed` escape-pair hypotheses: **0
hits, 7,866 keyword-tests.**

Session grand total: **~28,500 keyword-level tests + a ~1.77M-configuration axis sweep
+ 7,866 chat-phrase tests**, all against the real AES oracle. All negative. One
non-lead conclusively debunked (Saber). Doesn't change the Phase 7 bottom line — GSMG
stays parked; nothing found this session moves the needle on the endgame.

**New axis added + tested (2026-07-15): `pad25()`'s merge direction.** Auditing
`pad25()` surfaced a gap distinct from the already-swept drop-letter/tail-fill/
topology axes: the dropped letter's occurrences always folded into the alphabetically
*preceding* letter (`J`->`I`), and the *following*-letter direction (`J`->`K`) was
never even exposed as a parameter, let alone tested. Added `merge_direction` to
`pad25()` (`cb_common.py`) and `--merge-directions` to `cosmic_sweep_9ary.py`,
defaulting to `backward` (prior behavior unchanged for every other script that imports
`pad25()`). Re-ran the full drop-letter x tail-fill x topology sweep with both merge
directions (312 board variants/candidate, double the prior 156) on the same
5,678-candidate combined vocabulary against `dbbi` and `faed` (`h,e`): **0 hits,
11,356 keyword-tests** (~1,114s + ~1,208s). Combined with the prior axis sweep, this
vocabulary has now been checked across every currently-implemented structural
parameter of the 9-ary model.

**Side investigation, now resolved: `pad25()`'s `tail_fill` order is provably
unconstrained for the one ground-truth example, not an undiscovered rule.** Initially
tried to reverse-engineer what produced 3.2.2's real leftover-letter order (`JQZXW`,
from the 5 letters never used in `FUBCDORA`/`LETHINGKYMVPS`) — none of the three
implemented presets (forward/reverse/keyboard) reproduce it, nor do ~25 additional
named orderings tested programmatically against the same 21-letter used-pool (English
letter frequency, Scrabble tile score, Morse code length, QWERTY/DVORAK/AZERTY
keyboard scans, T9 keypad, Atbash, NATO phonetic word length, spoken letter-name
length, low/high alternating merge). Closest partial matches: morse-length-descending
and low/high-alternating each get 4 of 5 letters right, not all 5. One purely
mechanical rule (ascending alphabetical with everything from the 3rd position reversed)
matches exactly, but with only 5 letters (120 possible permutations) an exact accidental
match from ~25 tried rules isn't strong evidence.

**The actual resolution: checked whether the real 91-character 3.2.2 answer
(`INCASEYOUMANAGE...FUNDSTOLIVE`) uses any of J/Q/X/Z/W at all — it uses none of
them** (full letter set: `ABCDEFGHIKLMNOPRSTUVY`, exactly rows 1+2, nothing from row
3). Since those board cells are never read by this message's digit-codes, **all 120
possible orderings of the tail would have decoded it identically** — there is no rule
to find because the order has zero effect on this example. This also explains why the
community's own README shows the derivation ending in "(adding the rest of the
alphabet)" with no justification for the specific order chosen: it didn't need one.
(Confirmed via the source repo directly — `halbgott29a/gsmgio-5btc-puzzle`'s
`README.md` lines 323-340 — which also confirmed the escape digits `1,4` were never
brute-forced either: they're spelled out directly in an earlier decrypted layer,
"One for one, four for one." The literal phrase "BRUTE FORCING MIGHT BE REQUIRED"
does appear in the creator's own decrypted text, but describes a later, unrelated
step — selecting the right private key from "over twenty-three ciphers... seven
intertwined passwords" — not the alphabet or escape-digit derivation.)

Two adjacent questions resolved along the way: (1) why the board is sized 25/26 at
all when only 21 letters are used — because a keyed substitution alphabet is a
complete, message-independent codebook built once from the keyword (covering the
full English alphabet), not a table sized to whatever a specific plaintext happens to
need; the "unused" slots are required scaffolding for the cipher to be well-defined
for arbitrary input, not evidence of anything message-specific. (2) A `/` separator
appearing once in the README's walkthrough (`...MVPS/JQZXW`) is just informal prose
notation for "here's the appended leftover part," not a competing cipher convention —
the very next line's actual tool input reverts to `.` for both separators, matching
`ALPHA_322` exactly.

**Practical takeaway for `cosmic_sweep_9ary.py`'s `--tail-fills` axis**: still worth
sweeping (a candidate whose true answer needs a rare tail letter would be sensitive to
this parameter, and that can't be predicted in advance), but it is not a puzzle to
solve in the abstract — for any candidate whose real answer avoids J/Q/X/Z/W, every
tail-fill preset is functionally identical, exactly as observed for 3.2.2 itself.
`pad25()` and `cosmic_sweep_9ary.py`'s docstrings/help text updated to reflect this
(2026-07-15) — no longer describe it as an open mystery.

## Phase 10 — full OCR transcription of the physical "Cosmic Duality" book (2026-07-15)

The 2026-07-12 book review (see `doc/GSMG_PUZZLE.md`) was a manual visual scan for
hidden/planted content (anomalies, marginalia) across 73 photographed pages and
concluded negative. It never produced a machine-readable transcript, so the book's
*normal* text had never been mechanically mined for candidate riddle phrases the way
chat lines and wiki pages were. The 73 photos turned out to still exist locally
(`~/Pictures/Screenshots/`, dated 2026-07-12, missed by an earlier filesystem search
due to a bad `-newer` comparison) and were transcribed page-by-page via vision
(front cover through back cover, all 144 pages) into
`wordlists/gsmg/cosmic_duality_book_full_text.txt` (1,270 lines / ~13,400 words) —
essay/chapter body text, all image captions, the full bibliography, and the complete
index (an alphabetized list of every proper noun/concept in the book — high-value
mining material in its own right).

Ran the transcript through `riddle_content_words.py` (the same raw + stopword-filtered
extraction validated against 3.2.2's real alphabet) to get 2,091 candidates
(`wordlists/gsmg/cosmic_duality_book_candidates.txt`), then through
`cosmic_sweep_9ary.py`:
- Default axis settings, both targets, both `faed` escape hypotheses: **0 hits, 6,273
  keyword-tests**.
- Full structural axis sweep (all 26 drop-letters x 3 tail-fills x 2 merge-directions x
  2 topologies = 312 board variants/candidate) across `dbbi` and both `faed` escape
  hypotheses — the most thorough treatment given to any vocabulary batch this session,
  justified because this is the actual primary source material, not synthetic
  wiki-derived vocabulary: **0 hits, 2,091 candidates x 312 variants x 3 target-configs
  ≈ 652K board configurations checked** (1,110s + 1,213s + 1,203s).

Cross-referenced the transcript against the puzzle's own established keyword corpus by
hand. Found the book independently uses the word "demiurge" in its own Gnosticism
section (p.28-29) — corroborating, not just coincidental with, this session's earlier
Gnostic-vocabulary batch (already tested, 0 hits). The strongest *new* thematic lead:
the already-solved 3.2.2 answer's closing phrase "HALF AND BETTER HALF" (tested early
in this project as one literal string, 0 hits) turns out to echo pervasive "other half"
imagery throughout the book (Plato's Symposium — "each of us... is always looking for
his other half" — plus Zurvan's twins, Shiva/Shakti, hermaphroditic Adam, Ymir).
Built `wordlists/gsmg/other_half_candidates.txt` (22 fresh candidates: `otherhalf`,
`lookingforhisotherhalf`, `desireandpursuitofthewhole`, `indentureofaman`,
`shivawithoutshaktiisacorpse`, the book's own chapter/essay titles, etc.), confirmed
none previously tested, ran against both blobs: **0 hits, 66 keyword-tests**.

Also noted, for calibration: no chess imagery, prime numbers, or Matrix-specific
vocabulary anywhere in the book — it supplies the "duality" conceptual scaffold only,
not the Matrix-lore layer, consistent with the existing two-source understanding of
this puzzle stage.

Session grand total: **~30,700 keyword-level tests + a ~2.4M-configuration structural
sweep + 7,866 chat-phrase tests**, all against the real AES oracle, all negative. This
is the first time the book's actual text (not just its imagery) has been mechanically
tested — closes that specific gap. Doesn't change the Phase 7 bottom line.

**Transcription gap audit (2026-07-15, same phase).** A spot-check found pp.6-11 had
been read via vision but never actually written to the file (lost across a
content-filter interruption earlier in the session) — inserted properly this time. A
full sequential audit of every `## p.` header against expected page coverage found:
pp.14-15 turned out to already be present (written during the earlier content-filter
testing, just not yet audited); pp.20-21 and pp.112-113 were false alarms — content
already present but merged under a neighboring header, now relabeled; four single-page
gaps (39, 67, 81, 84) not yet checked, low priority. **pp.57-58 confirmed as a real,
currently-unrecoverable gap**: the photo spanning that spot shows page 56 flowing
directly into page 59 with continuous body text (consistent with a closed gatefold
insert bound into the spine), but the page-56 text itself contains an explicit
cross-reference — "...to the Virgin Mary *(page 58)*" — proving page 58 has its own
real content (likely more on the Virgin Mary/Mother Goddess connection), not blank
filler. Not recoverable without physically unfolding and re-photographing that page in
the actual book; confirmed no online scan/reprint has it either.

Re-mined the corrected file: 219 new candidates from the pp.6-11 insertion not in the
earlier 2,091-candidate batch. Ran default-axis (0 hits, 657 keyword-tests) and the
full structural axis sweep (26 drop-letters x 3 tail-fills x 2 merge-directions x 2
topologies, all 3 target-configs: 0 hits, 219 x 312 x 3 ≈ 205K board configurations,
117s + 128s + 125s). **0 hits throughout.**

**One more angle from Plato's Symposium (p.48-49), user-flagged**: the passage's exact
wording — "the sexes were not two as they are now, but originally three in number;
there was man, woman, and the union of the two" — introduces the number **three**, not
yet tested (the earlier "other half" batch only covered the downstream "other half"
conclusion, not this specific sentence). Built 12 candidates (`threeinnumber`,
`manwomanandtheunionofthetwo`, `theunionofthetwo`, etc.), confirmed all new, ran
against both blobs: **0 hits, 36 keyword-tests.**

**Hegel/Marx/Engels dialectical materialism (p.40), user-flagged as another possible
yin-yang-adjacent angle**: thesis/antithesis/synthesis as a duality-resolution
structure, plus the passage's own explicit Ohrmazd/Ahriman comparison. Built 14
candidates (`thesisantithesissynthesis`, `dialecticalmaterialism`,
`bourgeoisieproletariat`, `ohrmazdandahriman`, etc.), confirmed new, ran against both
blobs: **0 hits, 42 keyword-tests.**

**The "third entity" structural question (user-prompted, 2026-07-15): is `dbbi`/`faed`
really a two-part duality, or does Plato's "man, woman, and the union of the two"
suggest a missing third component?** This turns out to already be a tested hypothesis,
just never run against this session's new vocabulary. `chain_sweep.py` (built
2026-07-12) tests exactly this reading: not two independent targets, but `dbbi`'s
*decoded plaintext* becoming the keyword that builds the board `faed` is decoded
with — `faed` as "the union," dependent on `dbbi`, not a separate target. Originally
run against the old curated+dictionary wordlists only (429K candidates, 0 hits).
Combined every candidate wordlist generated this session (Gnostic/Architect vocab,
wiki deep-dive, anchor-cross, yin-yang-in-franchise, the book transcript + all
follow-up batches — 8,036 unique candidates,
`wordlists/gsmg/session_combined_for_chain.txt`) and ran it through `chain_sweep.py`
for the first time: **0 hits, 8,036 chained candidates** (10s). Closes this specific
gap — the union/chain hypothesis has now been tested against essentially all of this
session's vocabulary, not just the old wordlists.

## Phase 11 — hash duality as command-state composition (2026-07-23)

Tested the page's `our first hint is your last command` / `shabef ans too` wording as
an instruction to combine the previous SHA-256 command state with `SHA256(answer)`,
rather than merely hashing the answer twice.

Added `tools/gsmg/hash_duality_sweep.py` and a byte-safe
`cb_common.aes_try_open_bytes()` oracle. For every candidate answer from the clue set
and matrix-instruction pipeline, it tests binary and hexadecimal variants of:

- SHA-256 over both concatenation orders;
- XOR with `SHA256(answer)` and SHA-256 of the XOR;
- HMAC-SHA256 in both directions;
- direct concatenation of the two hash values in both orders;
- raw, LF, and CRLF passphrase forms.

**Provenance re-audit (same day):** a local-notes-only audit briefly misclassified
three authentic values (`phase2_causality`, `phase3_parts`, `phase32_clues`) as
fabricated. The primary public `puzzlehunt/gsmgio-5btc-puzzle` README explicitly
documents each exact preimage, hash, and subsequent OpenSSL use. Restored the four
actual command states: those three plus the `89727...` SalPhaseIon-entry hash.
Removed two hashes newly derived from URL slugs, because those hashes were never
commands in the solved chain.

Corrected full result: **11,899 candidate answers, 4 verified prior hashes,
1,427,880 byte-exact passphrase attempts, 0 AES hits, 25.4s.** The hash-duality
interpretation cannot rescue any currently generated answer candidate under any of
the four real prior-hash states. A genuinely new decoded answer could still use
this grammar, but the final hash-combination axis itself is now implemented and
closed for the present candidate pool.

## Phase 12 — reverse and raw cross-target coupling (2026-07-23)

Added `tools/gsmg/cross_target_coupling_sweep.py` to close the remaining bounded
`dbbi`/`faed` coupling variants.

The reverse chain tests candidate → decode `faed` → derived board → decode `dbbi` →
AES across the full 8,036-candidate session vocabulary. Both stages cover all ordered
forms of `{b,e}`, `{g,i}`, and mirrored `{h,e}`. Result: **1,735,776 passphrase
attempts, 0 hits**.

The content-independent raw mode builds 42 derived streams by folding `faed` to 91
positions or repeating `dbbi` over 570 positions, then applying mod-9 addition, both
subtraction directions, and prime/even/nonzero selectors. It checks raw symbols,
numeric mappings, whole-base-9 bytes, base-9 hex, both checkerboard topologies,
clue-derived alphabets, and all ordered escape assignments. Result: **30,660
passphrase attempts, 0 hits**.

Combined result: **1,766,436 attempts, 0 AES hits**. Reverse chaining, folded masks,
repeated mod-9 keystreams, and mirrored/opposite escape coupling are closed for these
bounded models.

## Phase 13 — cross-phase prime/color linkage (2026-07-23) — DEBUNKED, see correction

Reviewed the solved chain from Phase 0 rather than treating Cosmic Duality in
isolation, claiming a reproducible ordered pipeline:

`yellow blue primes → matrix sum list → last words before archi choice → yin yang`.

The Phase 0 counter-clockwise spiral's blue/yellow byte-boundary order was used to
drive a constrained `b`/`be` parse of `dbbi`; the `#fefefe` cell acted as a single
`b`. Using the resulting 23 token positions as a mask over the exactly 91-character
Phase 3.2.2 answer extracted `ncsyangcahirivasoalbefayanestve`, whose literal `yang`
was claimed as internal verification, alongside a claimed match to the Architect
plaintext's 23/16/7 counts (23 matched groups, 16 yellow characters, seven blue
digraphs).

A now-removed `tools/gsmg/phase_linkage_sweep.py` reproduced: **444 unique
candidates, 357 alphabets, 8,568 checkerboard decodes, 161,510 unique passphrase
attempts, 0 AES hits.**

**Correction (same day, before this entry was committed): the cross-phase bridge is
not real — it's apophenia, checked with the same rigor already applied to the
community's own debunked "matrixsumlist triangle."**

1. An independently repeated null-model test (deterministic seed, 200,000 random
   shuffles of the same 15×`B`/9×`BE`/1×`G` token multiset, same extraction
   algorithm) produces `"yang"` **7,360 times = 3.68%** — an ordinary rate, not a striking coincidence, especially given the
   ~30 different mask variants tried in the same sweep.
2. The blue/yellow "spiral order" used isn't independent evidence — it's mechanically
   identical to the LSB-parity sequence of the public string
   `"gsmg.io/theseedisplanted"`, which this project's own 2026-07-13 research already
   concluded "carries zero information beyond what black/white already show" and
   explicitly retired.
3. A subsequent claim that the carried-forward phase facts were fabricated was
   itself false. The primary public README documents `causality`, Safenet/Luna/HSM,
   `11110`, Jacque Fresco, Heisenberg, `THEMATRIXHASYOU`, and both hashes. It also
   shows that `.../6R1/... w ...` is the pre-move chess prompt while
   `.../2R5/... b ...` is the required post-move answer used in the hash. Authentic
   inputs do not rescue a construction whose output fails the null model.

The AES-oracle negative result above is genuine and stands (no false hit was ever
claimed). Both premise-derived sweep files were removed after falsification. What's
corrected is the narrative: this is not a real cross-phase discovery, and the
"seven sequential cipher stages" follow-up is not recommended — it would build a
more elaborate construction on top of an already-debunked one.

## Phase 14 — AES oracle false-negative fix: printable-ratio gate was too strict (2026-07-24)

`cb_common.aes_try_open_bytes()` required decrypted plaintext to be >85% printable
ASCII before counting a valid-PKCS7-padded decrypt as a real hit. That threshold was
never checked against a known-positive vector — there wasn't one available before
this session fetched the primary community README fresh via `gh api`.

The README inlines the real Phase 3.2 AES blob and its documented password
(`SHA256("jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple")`).
Decrypting it with this project's own code (base64 → `Salted__` header → legacy
`EVP_BytesToKey` → AES-256-CBC → PKCS7 unpad) reproduces the community's documented
plaintext byte-for-byte — the first true end-to-end ground-truth validation of this
pipeline in the project's history. **Its printable ratio is only ~0.598** — it
legitimately embeds a CP437/high-bit-set garbled sub-block as part of the puzzle's
own multi-stage design (readable English, then binary-looking bytes, then a plain
decimal number, then more English, all in one decrypted message). The old `>0.85`
gate would have silently rejected this exact, byte-for-byte-correct decryption.

Fixed by replacing the flat threshold with a null-model z-score
(`cb_common.printable_z_score()`): how many standard deviations the observed
printable-byte count sits above the random-byte baseline (98/256 ≈ 37.1%, the
share of byte values counted as "printable"). This scales correctly with plaintext
length instead of penalizing short and long bodies by the same fixed ratio. Default
threshold `z > 5.0` — comfortably clears the real Phase 3.2 case (z ≈ 22) while
keeping the compound false-accept rate (combined with the ~1/255 valid-padding
prior) at roughly 1e-9 per attempt. Verified empirically: 0 false positives across
200,000 random-word attempts against the real, still-open SALPH/COSMIC blobs.

The known-positive Phase 3.2 blob is now baked into `data.py`
(`PHASE32_BLOB_B64`/`PHASE32_PASSWORD`/`PHASE32_PLAINTEXT_PREFIX`) and
`cb_common.py`'s startup self-test permanently re-verifies the full pipeline
end-to-end on every import — the same way `VALIDATION_NUM` guards the checkerboard
decoder. It is *not* added to the production `BLOBS` dict (would add dead-weight
per-candidate work to every real sweep); `aes_try_open_bytes()` gained an optional
`blobs=` override so the self-test can check it without touching the two real
open targets.

**Why this matters project-wide**: every sweep script in this project shares this
one oracle function. Re-ran the cheap/high-confidence pools already available this
session — `matrix_instruction_sweep.py` (11,889 candidates), `hash_duality_sweep.py`
(11,899 × 4 hashes, 1,427,880 attempts), `cross_target_coupling_sweep.py`,
`dual_ternary_sweep.py`, `lastcommand_probe.py` (28), `door_prime_passport_probe.py`
(12), `chain_sweep.py` (89,063, validated `pad25`/`{b,e}` model) — all still **0
hits** under the corrected oracle. Sweeps built on the `pad28()` keyword model
(e.g. `cosmic_sweep.py`'s 677,810-test dictionary sweep) are lower priority to
re-run: that alphabet-construction model is independently already known incapable
of reproducing the real 3.2.2 alphabet (Phase 3, above), so its candidates were
wrong for an unrelated reason regardless of the oracle fix. Larger validated-model
sweeps not yet re-run under the corrected oracle: `cosmic_sweep_9ary.py`'s several
historical invocations (~1M+ tests using the validated `pad25` construction),
`autokey_sweep.py` tier-2 (partial, ~956K/5.76M), `chain_addition_sweep.py`
(~5.84M pairs) — flagged as the next tier to re-run, not yet done.

## Phase 15 — Cosmic Duality book: complete OCR transcript vs. the incomplete curated one (2026-07-24)

The 2026-07-12 book transcription (`cosmic_duality_book_full_text.txt`, cited above
as "front cover through back cover, all 144 pages") turned out to be overstated.
Ran the 73 source screenshots through a proper OCR pipeline
(`tools/gsmg/extract_cosmic_duality_screenshots.py`: per-page splitting, contrast/
inversion, targeted high-res crops for 6 problem pages, Tesseract) into
`wordlists/gsmg/cosmic_duality_book_screenshot_ocr.txt` (raw, OCR errors preserved,
gitignored like other wordlist data).

**Comparison**: the existing curated file is only ~27.5% of the OCR's word volume
(13,689 vs 49,698 words, independently recounted) — most content past p.15 turned
out to be summarized/paraphrased rather than transcribed verbatim. Checked the
missing content for anything puzzle-shaped: no `matrix`/`architect`/`password`/
`last words`/`better half` anywhere in the full OCR; `choice`/`command`/`prime`
occurrences are all ordinary Zoroastrianism/mythology narrative. No new Cosmic
Duality solution instruction found in the previously-missing text.

**Re-ran the default-axis dictionary sweep against the corrected, complete source**
(the earlier 652K-configuration structural sweep at line ~666 above was built from
the incomplete/paraphrased 2,091-candidate set — paraphrase matters a lot for this
puzzle, since the one validated real riddle depended on exact original wording, not
summary). Regenerated candidates from the full OCR via the same validated
`riddle_content_words.py` tool: 12,313 candidates (vs. 2,091 before). Ran
`cosmic_sweep_9ary.py`'s default-axis pass (both targets at `{b,e}`, plus `{g,i}`
for `faed`) — using the also-newly-fixed AES oracle (Phase 14, above):

- `{b,e}`, both targets: 24,626 keyword-tests, 0 hits (5.6s).
- `{g,i}`, `faed`: 12,313 keyword-tests, 0 hits (2.9s).
- **Total: 36,939 keyword-tests, 0 hits.**

Negative, but on much more solid footing than before — this is the first time this
specific candidate source has been tested both (a) from the complete verbatim text
rather than a partial paraphrase, and (b) through an AES oracle proven not to
reject a real hit. The full structural axis sweep (312 board variants/candidate,
~11,750 candidates → ~11M configurations, ~10-11h at the prior rate) has not been
run against the new candidate set — flagged as the next tier if this is revisited,
not yet done.

**Book-motivated transform subset (2026-07-24, same day)**: rather than the full
312-variant sweep, ran a small, specifically-motivated set of transforms tied to
the book's own "duality" theme — `identity`/`reverse`/`halfswap` ("yin/yang halves"
swapping)/`mirror9` ("complement": a↔i, b↔h, c↔g, d↔f, e fixed)/`col2` (this
project's own established mathematically-equivalent form of an "interleave"
transform) — as both input and output transforms (25 combinations), against the
complete 12,313-candidate OCR set, both escape hypotheses:

- `{b,e}`, both targets: 24,626 candidate-target pairs (25x more underlying AES
  attempts per pair than the plain default-axis pass) — 0 hits.
- `{g,i}`, `faed`: 12,313 candidate-target pairs — 0 hits.

**Found and fixed a real bug along the way**: the `{g,i}` run first came back with
1 hit — investigated immediately rather than accepted, and it was a false positive.
Root cause: `cosmic_sweep_9ary.py`'s `KDF_VARIANTS_OVERRIDE` defaulted to `None`,
which `cb_common.aes_try_open_bytes()` silently expands to **all 6 KDF variants**
(sha256/md5/sha1 × 256/128-bit) — not "just the primary sha256/aes256" the old
comment claimed. Every plain invocation of this script (this session and all
historical runs back to 2026-07-08) was therefore testing 6x more KDF combinations
than documented, at 6x the true attempt volume and false-positive exposure. The
specific hit used `sha1` (never validated against anything) on a 430-character
decoded "answer" that was pure letter-soup, not English — exactly what the
statistical false-accept analysis (Phase 14, ~1e-9/attempt) predicts becomes
non-negligible once the true attempt count is 6x larger than the reported
"keyword-tests" figure implies. Fixed `KDF_VARIANTS_OVERRIDE` to genuinely default
to `[("sha256", 32)]` (matching the 2026-07-08 log's stated original intent — "used
the default KDF (SHA-256/AES-256) only... combining both axes would have taken
~27h"), only expanding to all 6 with `--all-kdf`. Re-ran both passes under the fix:
same 0 hits, ~5.5x faster (23.9s/12.2s vs. 130.9s/66.8s), confirming the false
positive is gone and every prior "0 hits" conclusion from this script still stands
(more KDF coverage than documented was never a correctness problem, just an
undocumented/underestimated compute cost and false-positive-rate difference).

## Phase 16 — code review of all 25 tools/gsmg/*.py scripts (2026-07-24)

Reviewed every script for correctness bugs (not just result validity, already the
subject of earlier corrections this session). Found 3 issues:

1. **`cosmic_sweep_9ary.py`'s KDF-variant default regression — already covered and
   fixed above (Phase 15).**
2. **`chain_addition_sweep.py`'s progress/ETA math used the wrong denominator**
   (line ~216): `done` accumulated in units of (alphabet, keystream) *pairs*, but
   was compared against `len(alpha_candidates)` (a much smaller count) instead of
   `total_pairs`. On any real run this makes the progress bar exceed 100%
   immediately and the ETA go negative for the rest of the run. Purely cosmetic —
   the underlying hit-detection logic was unaffected, so no past "0 hits" result
   changes — but the tool's own progress output was meaningless. Fixed to compare
   `done` against `total_pairs` and relabeled the printed unit from
   "alpha-candidates processed" to "pairs processed".
3. **`autokey_sweep.py` and `chain_addition_sweep.py` both hardcode dbbi's `{b,e}`
   escape pair for *both* targets** (`ESCAPE_ORDERS = [("b","e"),("e","b")]` at
   module scope, no CLI override), unlike `cosmic_sweep_9ary.py` (`--escapes` flag)
   and `cross_target_coupling_sweep.py` (explicitly tests `{b,e}`/`{g,i}`/`{h,e}`).
   This means every historical "0 hits" result from these two scripts' faed-side
   sweeps only ever tested faed under dbbi's escape pair, never faed's own
   established best-fit `{g,i}` pair or the `{h,e}` mirror hypothesis — despite
   both scripts' docstrings claiming to test "either target." **Not fixed yet** —
   doing so means re-running both sweeps under the additional escape pairs, a
   real compute commitment (autokey tier-2 is already only ~17% complete from an
   earlier session); flagged for a decision rather than silently expanded.

Everything else reviewed clean: `cb_common.py` (build_board/decode/pad25/
pad28/decode_9ary/autokey and chain-add primitives all independently re-verified
correct), `data.py`, `chain_sweep.py`, `crib_drag.py`, `grid_spiral.py`,
`kasiski_friedman.py`, `quadgram_solver.py`, `alphabet_hypothesis_check.py`,
`door_prime_passport_probe.py`, `image_audit.py`, `extract_cosmic_duality_
screenshots.py`, `riddle_content_words.py`. `page_structure_audit.py` (the other
agent's raw-page-structure work) was directly re-run rather than just read —
succeeded with zero exceptions, independently confirming its exact byte-level
reconstruction of the real archived page structure
(`dbbi + abba(matrixsumlist) + faed + z-separators + decimal-transports +
hash-literals + AES-blob-split-around-abba(enter)`, 1,075 characters, exact match).

## Phase 17 — independent verification of a second, deeper code-review pass (2026-07-24)

Another agent ran a broader review (`doc/GSMG_SCRIPT_CODE_REVIEW.md`) covering all
25 scripts and fixed 7 categories of issue: dangling-escape silent truncation,
explicit-empty-scope-expands-to-default (same class as the Phase 15 KDF bug),
invalid-option silent fallbacks, fork-vs-spawn global-mutation fragility, an
OpenSSL digest-history correction, AES-hit terminology (plausibility candidate,
not authenticated positive), plus per-script fixes (chain_addition_sweep.py
progress math -- same bug independently caught in Phase 16;
lastcommand_probe.py blob over-scoping; dual_ternary_sweep.py duplicate
periodicity streams; quadgram_solver.py doc/path issues; door_prime_passport_
probe.py hits-file collision with cosmic_sweep.py; matrix_instruction_sweep.py
dedup-scope labeling; grid_spiral.py path portability). Added
`tools/gsmg/test_cb_common.py` (9 tests) as permanent regression coverage.

**Independently verified rather than accepted at face value**:

- **Dangling-escape fix**: confirmed real. Checked whether it affects dbbi's
  primary `{b,e}` hypothesis -- it does not (empirically, `{b,e}`/`{e,b}` never
  produces a dangling escape for dbbi's actual ciphertext). It does affect dbbi
  under `{h,e}`/`{e,h}`, exercised by `cross_target_coupling_sweep.py`'s
  reverse-chain mode. Re-ran that sweep under the fix: 1,157,184 attempts (down
  from 1,735,776, correctly excluding now-invalid candidates), still 0 hits --
  conclusion unchanged, more rigorously earned.
- **Fork/spawn fix**: confirmed this environment's actual multiprocessing
  default is `fork` (verified directly), and nothing in the sweep scripts
  overrides it -- so this was a real defensive/portability fix, but it did NOT
  actually corrupt any of today's real results on this system.
- **Empty-KDF/blob-scope fix**: verified via the new test suite and direct
  code inspection (`is None` checks replace truthy `or` checks).
- **dual_ternary_sweep.py duplicate streams**: re-ran the periodicity gate
  myself -- test count dropped 1,600→560 for faed, Bonferroni threshold
  adjusted 4.16→3.92 accordingly, apophenia conclusion unchanged (max z=3.05,
  still short).
- **All smaller claims** (lastcommand_probe.py blob scoping, hits-file rename,
  grid_spiral.py/quadgram_solver.py path portability, matrix_instruction_
  sweep.py dedup labeling) verified accurate by direct code inspection.
- All 25 scripts re-verified to import cleanly; all 9 new tests pass;
  `compileall`/`git diff --check` both clean.

**Not addressed by this pass**: the Phase 16 finding that `autokey_sweep.py`/
`chain_addition_sweep.py` still only test faed under dbbi's `{b,e}` escape pair,
never faed's own `{g,i}`/`{h,e}` -- still open.

This is a genuinely high-quality, thorough review -- every claim independently
checked held up under scrutiny. No new puzzle solution hit was found.

## Phase 18 — fixed the faed escape-pair coverage gap; recorded autokey tier-2's exact old/new boundary, NOT yet resumed (2026-07-24)

Fixed the Phase 16 finding: `autokey_sweep.py` and `chain_addition_sweep.py` both
now take per-target escape configuration instead of one shared pair applied to
both targets. New defaults: dbbi `{b,e}` (both orders, unchanged), faed `{g,i}`
+ `{h,e}` (both orders each, new). `--dbbi-escapes`/`--faed-escapes` accept
`"e1,e2"` or `;`-separated lists; passing `--faed-escapes b,e` exactly
reproduces the historical scope for reproducibility. A new `--targets
dbbi,faed` filter allows testing a subset -- e.g. `--targets faed` to backfill
only faed's new coverage over an alpha range already completed for dbbi.

Both scripts smoke-tested (tiny runs, both new-default and legacy-reproduction
modes) and confirmed correct: 216 vs 144 attempts for the same 9 pairs
(autokey/chain-addition), exactly the expected 1.5x multiplier (dbbi 2 + faed 4
= 6 escape units, vs the old shared 2+2=4).

**Autokey tier-2's exact old/new coverage boundary** (this is the specific
in-progress run affected -- 338,905 alpha candidates x 17 keystream candidates
= 5,761,385 total pairs, `wordlists/gsmg/single_fragments.txt` as keystream
source, stopped earlier this session at 956,250/5,761,385 pairs, ~16.6%):

| Region | Alpha range | Pairs | Coverage so far | Coverage needed |
|---|---|---:|---|---|
| Backfill | `[0, 54,250)` | 922,250 | dbbi `{b,e}` + faed `{b,e}` (old scope) | faed `{g,i}`+`{h,e}` only (`--targets faed`) |
| Continuation | `[54,250, 338,905)` | 4,839,135 | none | full new scope (both targets) |

(54,250 is the previously-recorded safe `--alpha-skip` value -- a margin below
the naive 956,250÷17≈56,250 boundary, accounting for out-of-order chunk
completion across 16 parallel workers.)

**Workload, measured fresh today (16 workers, not estimated from memory)**:
backfill ~242 pairs/s -> ~1.06h; continuation ~166 pairs/s -> ~8.11h; **total
~9.2h additional compute**. For reference, continuing the old (never-fixed)
scope for the same remaining region would have measured ~257 pairs/s -> ~5.24h
-- so the fix adds roughly +3.9h total, not an open-ended reopening.

**Not yet launched** -- recording the boundary and workload first, per
instruction, before committing to either the backfill or continuation run.

## Phase 19 — model-changing paths after coverage saturation (2026-07-24)

Reviewed the now-exhausted branches specifically to find mechanisms not equivalent
to another keyword, static transposition, raw base-9 packing, or raw-symbol
dual-ternary transform.

Two concrete representation gaps remain:

1. **Dual-quinary/base-25 after checkerboard segmentation.** A native 9-ary
   checkerboard produces 25 complete code types. `faed` uses all 25 under each
   motivated escape hypothesis, but no current script factors those code indices
   into 5×5 coordinates or packs the segmented stream as base 25.
2. **Self-derived matrix-sum permutations.** Existing tools calculate matrix sums
   as candidate strings/selectors and separately test literal clue phrases as
   columnar keys. They do not derive a row/column ordering from a ciphertext's own
   sums and apply that ordering back to the ciphertext.

Also identified two bounded follow-ups: standard 5×5 digraphic ciphers over the
segmented code alphabet, and a synthetic-control calibration harness for the
63-character `{b,e}` checkerboard hill climb.

Ran a frequency-preserving permutation period scan (periods 2-40, 3,000 shuffles)
to gate further repeating-key work. `dbbi`'s best period was 13 (`z=2.52`) but the
max-statistic empirical `p≈0.34`; `faed`'s best corrected `p≈0.80`. No period is
significant, so the rough old Friedman estimate near 9 is not evidence for more
autokey/Vigenère expansion.

Detailed scopes, null-model requirements, and stopping conditions are recorded in
`doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md`. No new AES hit was found in this
planning/statistical phase.

### Phase 19 implementation audit and corrected result

The first dual-quinary shuffle runs reported a stable `dbbi` anomaly
(`p≈0.020` at seed 0/2,000 trials and `p≈0.0219` at seed 12345/10,000 trials).
The replication was real for the implementation, but review found the
implementation did not match its stated null: it shuffled raw `a`-`i` symbols,
then re-segmented them, rather than preserving the complete checkerboard-code
multiset. It also mislabeled direct index bytes as whole-base-25 conversion.

Fixed both issues, rejected dangling code tails, and added deterministic parallel
trials. Under the corrected complete-code null:

- `dbbi`, seed 12345, 10,000 trials: 2,305 at least as good,
  **family-wise empirical p=0.23058**;
- `faed`, seed 12345, 2,000 trials: 1,902 at least as good,
  **family-wise empirical p=0.95102**.

The dual-quinary path is negative. The prior `p≈0.02` is retired as a
null-implementation artifact.

### Autokey faed escape-pair backfill result

The `[0,54,250)` faed-only `{g,i}`/`{h,e}` backfill completed. Its append-only
artifact contains **two**, not one, AES plausibility candidates (the second record
has no final newline, so `wc -l` reports one):

| Blob/KDF | Body length | Printable ratio | z | Longest printable run | UTF-8 |
|---|---:|---:|---:|---:|---|
| SALPH / SHA-256 AES-128 | 79 | 0.6582 | 5.0362 | 8 | no |
| COSMIC / MD5 AES-128 | 1,327 | 0.4499 | 5.0268 | 9 | no |

Both plaintexts are incoherent binary noise and barely clear the current
`z>5` filter. They are false positives; the backfill produced **zero credible
hits**.

### Weak/strong AES oracle tiers implemented (2026-07-24, after backfill completion)

Implemented once the autokey backfill above finished (deliberately not touched
while it ran, to preserve one consistent oracle configuration for that run's
results). `cb_common.aes_try_open_bytes()` now gates on two thresholds instead
of one:

- `z >= PRINTABLE_Z_STRONG_THRESHOLD` (8): returned as a hit, same as before.
- `PRINTABLE_Z_WEAK_THRESHOLD` (5) `<= z < 8`: logged to
  `tools/gsmg/weak_candidates_log.txt` (JSON-per-line; gitignored like other
  run output) but NOT returned as a hit -- suppresses noisy alerts at the
  scale a large sweep produces without silently discarding borderline
  decryptions.
- `z < 5`: neither logged nor returned, unchanged.

Each log record captures z-score, printable ratio/count, plaintext length,
longest printable run, UTF-8 validity, blob/KDF, the passphrase (hex), and a
plaintext hex preview. Verified: re-tested the exact first autokey false
positive -- now correctly returns `None` (not a hit) while being fully logged
as `tier: "weak"`; the known-positive Phase 3.2 vector is still returned as a
strong candidate (z=21.77, matching the previously-established ~22).

**Verification correction:** the reported 50,000-passphrase stress run claimed
21 weak candidates, but its script/output was not preserved in the repository.
The current append-only log contains 47 records: 46 repeated Phase 3.2 strong
self-test records caused by import-time validation, and one unique weak record
(the known 79-byte autokey false positive). Strong candidates no longer write
to the weak log, preventing future import-time pollution. The 21 random stress
cases have no clue provenance and are not puzzle leads, but their claimed rate
should not be called “expected” without a reproducible benchmark: it is much
higher than the simple padding-plus-binomial null predicts. All 25 scripts
re-verified importing cleanly; `compileall`, the 9-test suite, dual-quinary
self-tests, and `git diff --check` all pass.

**Review tooling added:** `tools/gsmg/review_weak_candidates.py` reads the
JSONL log, dedupes by `(blob, kdf, passphrase_hex)` (keeping the first-seen
copy of each -- later repeats are re-discoveries, not new information), and
prints a z-score-sorted table. Defaults to `--tier weak`, so the 46 stale
strong-tier self-test lines are excluded without needing to touch the
append-only file. Verified against the live log: `--tier weak` (default)
correctly shows only the one real candidate (SALPH, z=5.036); `--tier all`
shows both it and the Phase 3.2 self-test row (z=21.772). Note: the backfill's
second false positive (COSMIC/MD5-AES128, z=5.0268, recorded earlier in this
file) predates this logging existing, so it was never written to the log --
it was only ever caught by the older print-based hit reporting. Not a bug,
just a provenance gap for anyone re-deriving candidates from the log alone.

### Autokey continuation: recorded, NOT launched (2026-07-24)

Deliberately not launched -- this is coverage bookkeeping (finishing a scope
already deemed low-probability), not a strengthened lead, and a cheaper path
(matrixsumlist self-derived permutation) takes priority. Confirmed exact
boundary directly against the loaded candidate lists (not from memory):
338,905 total alpha candidates x 17 keystream candidates. Backfill covered
exactly `alpha[0:54250]` (922,250 pairs, done). Continuation needs exactly
`alpha[54250:338905]` = 284,655 candidates x 17 = **4,839,135 pairs** (~8.11h
at the previously-measured ~166 pairs/s).

Exact command to resume later:

```bash
python3 tools/gsmg/autokey_sweep.py \
  --alphabet-wordlist wordlists/gsmg/phrases.txt \
  --alphabet-wordlist wordlists/gsmg/phrases-joined.txt \
  --alphabet-wordlist wordlists/cypherpunk/phrases.txt \
  --alphabet-wordlist wordlists/cypherpunk/phrases-joined.txt \
  --alphabet-wordlist wordlists/bitcoin-historical/phrases.txt \
  --alphabet-wordlist wordlists/bitcoin-historical/phrases-joined.txt \
  --alphabet-wordlist wordlists/gutenberg/phrases.txt \
  --alphabet-wordlist wordlists/gutenberg/phrases-joined.txt \
  --alphabet-wordlist /usr/share/dict/american-english \
  --alphabet-wordlist /usr/share/dict/british-english \
  --alphabet-wordlist /usr/share/dict/cracklib-small \
  --keystream-wordlist wordlists/gsmg/single_fragments.txt \
  --workers 16 --chunk-size 50 \
  --alpha-skip 54250 \
  --targets dbbi,faed \
  --hits-out tools/gsmg/hits_autokey_continuation.txt
```

`--alpha-skip 54250` is exact here (not the earlier conservative-margin value)
because the backfill's own `--alpha-limit 54250` deterministically consumed
`alpha[0:54250]` from the identical wordlist list/order -- skip and limit are
exact complements against the same list, no out-of-order-chunk ambiguity like
the original mid-run stop. Queue as unattended/overnight compute after the
matrixsumlist permutation path is resolved, not before.

## Phase 19 — `matrixsumlist` self-derived permutation: implemented, CLOSED NEGATIVE (2026-07-24)

Prioritized over the autokey continuation per instruction (cheaper, and a
genuinely untested reading vs. coverage bookkeeping on an already-low-probability
scope). `tools/gsmg/matrixsum_permutation_sweep.py` implements the doc's bounded
plan exactly: applies each ciphertext's own row/column-sum-derived order as a
PERMUTATION KEY back onto itself (not onto a different text), for the three
clue-supported matrix factorizations only -- raw `dbbi` (7x13/13x7), `{b,e}`-
segmented `dbbi` (7x9/9x7, 63 complete codes), raw `faed` (15x38/38x15; no
segmented-code matrix for faed, since neither 436 nor 469 codes has a
clue-supported factor pair). Ten bounded permutations per shape (row/column
ascending/descending, row-then-column, and the inverse/scatter of each gather
form) -- self-test round-trips every gather/scatter pair and confirms every
permuted output is an exact rearrangement of the same ciphertext content (same
multiset). Verified exactly: raw-dbbi column sums
`[21,31,35,30,17,26,8,27,28,32,19,26,31]` and ascending order
`[6,4,10,0,5,11,7,8,3,1,12,9,2]` (matching the doc's own numbers); a=1..i=9
changes sums but not order (checked, not separately swept, per the doc's
stated invariant). Each permuted stream feeds both the checkerboard path
(decode_9ary, a small clue-motivated alphabet/escape set, real AES oracle) and
a direct-byte path (digit/index stream packed directly, signature/printability
check).

**Found and fixed a real bug via the shuffle gate itself, before trusting any
result**: the byte-oriented score (printable ratio + longest run, reused from
the dual-ternary/dual-quinary scripts) is trivially saturated for the
checkerboard path, since `decode_9ary` output is always pure A-Z letters --
printable ratio is always 1.0 and the longest run always spans the whole
string. First shuffle-gate run showed `real_best == null_mean == null_max ==
160.0` (the exact byte-score ceiling) for BOTH targets -- not evidence of a
clean negative, evidence the statistic couldn't discriminate anything at all.
Fixed by scoring checkerboard-path text candidates with real language-content
scoring (a `COMMON_WORDS` bonus, same idea as `matrix_instruction_sweep.py`)
instead of byte-level printable-ratio stats; the direct-byte path keeps its
original byte-oriented score, since that content genuinely varies.

**Corrected result** (5,000 trials, seed 2024, 16 workers, ~43s total):

| Target | Real best score | Null mean | Empirical p |
|---|---:|---:|---:|
| `dbbi` | 57.5 | 63.85 | **0.85963** |
| `faed` | 125 | 128.93 | **0.48490** |

Both clearly negative -- real scores sit inside (dbbi actually below) the null
bulk. Direct sweep (both targets, real AES oracle, no shuffling): 784 unique
outputs for `dbbi`, 678 for `faed`, 4,224 + 3,828 AES keystrings tested, **0
hits**. This path is closed.

## Phase 20 -- Checkerboard recovery calibration harness (2026-07-24)

Autokey continuation stays paused. Priority per user instruction: determine
whether the 2026-07-12 quadgram-hillclimb negative on `dbbi` (see
doc/GSMG_PUZZLE.md) is actually *meaningful*, before pursuing the bounded
5x5 digraphic-cipher path (doc item #3) any further. `dbbi` decodes to only
63 letters using 19/25 code types under `{b,e}` -- confirmed directly
(`segment_codes`/`natural_code_index` on the real `DBBI` string) -- a genuinely
hard regime for ciphertext-only substitution recovery, so a negative score
there isn't automatically informative.

Built `tools/gsmg/checkerboard_recovery_calibration.py`: imports
`quadgram_solver.hillclimb`/`run_all_variants_parallel` **unchanged**, feeds
them synthetic 63-letter ciphertexts built by encoding real English text
(Matrix screenplay / Cosmic Duality book / puzzle chat archive -- the same
corpora already mined elsewhere for candidate riddle sentences) through a
freshly random 25-of-26-letter board each trial (dropping a letter confirmed
absent from that trial's plaintext, so the encode is a clean bijection with
no merge distortion), using the same `{b,e}`/`top_first` construction dbbi's
own attack assumes. Verified the encode/decode round-trip reproduces the
input plaintext exactly before trusting any result.

**24 trials (8 each: Matrix/book/chat), 2,000 restarts/variant x 4,000 iters x
4 structural variants (8,000 restarts/trial -- roughly 1/7.5 the restart count
of the original 15,000/variant real-dbbi run, ~16 workers, ~25 min total):**

| Metric | Result |
|---|---:|
| Top-1-by-quadgram-score exact recovery | 3/24 (12.5%) |
| Top-1-by-quadgram-score near-exact (<=6/63 mismatches) | 12/24 (50.0%) |
| Search visited the true key at some local optimum (any restart) | 12/24 (50.0%) |
| Search visited a near-exact key at some local optimum | 23/24 (95.8%) |

**Diagnosis: this is a ranking/scoring failure, not a search-coverage
failure.** The hill-climb's own restarts land on the true key (or within 6
characters of it) in 23/24 trials -- but the plain quadgram score picks a
*different*, wrong local optimum as the top-1 answer 21/24 times, because
some wrong decode almost always scores higher under quadgram log-probability
alone (median ~400+ wrong local optima per trial outscore the true plaintext;
one outlier trial had 8,000/8,000). Confirmed with a targeted sanity check
before trusting the aggregate: for one trial, the true plaintext (quadgram
score -274.4) lost top-1 to a wrong decode (-273.0, 35/63 mismatches) under
plain scoring, but a `dictionary_word_length^2` bonus at weight as low as 0.3
correctly flipped the ranking back to the true plaintext.

**The metric that actually validated the original 2026-07-12 negative --
achievable best-score ceiling vs a real-English reference -- holds up and is
*strengthened*, not undermined, by this calibration.** Recomputed both
figures directly rather than trusting the older doc prose: the real dbbi run's
reported best decode (`PLANDSSETURBEE...`, 63 chars) scores -285.3
(-4.529/char); the 3.2.2 known-real reference decode scores -367.9 over 91
chars (-4.043/char) -- both recomputed exactly matching the historical
figures, confirming no drift in the quadgram model. Across all 24 calibration
trials, the **best score the hill-climb found for ANY trial** (i.e. the
easiest case to beat) was still only -4.386/char (one deliberately-hard chat
outlier; every other trial's ceiling ranged -3.66 to -4.32/char) -- real
dbbi's -4.529/char falls outside (worse than) the full range spanned by all
24 genuine-English synthetic controls, including the single hardest one. If
`dbbi` really were a `{b,e}`/`build_board_9ary`-style checkerboard over
English, the hill-climb should have reached at least the score ceiling its
worst synthetic control reached -- it didn't, despite ~7.5x more restarts
than any calibration trial used. This is the correct, now-validated
calibration for the metric the original conclusion actually relied on.

**Follow-up in progress**: since the failure is specifically in top-1
ranking (not search coverage), added a bounded word-level rescoring layer
(`word_bonus()`: dictionary-substring-length^2 bonus, `/usr/share/dict/
american-english`, no changes to the hill-climb itself) and reran the
identical 24 trials, reranking the SAME already-explored local optima at
several bonus weights.

### Correction: two claims above did not hold up (external review, 2026-07-24)

Two claims from the pass above were checked and found wrong before being
relied on further -- flagged by review, independently verified rather than
taken on faith:

1. **"Reranking the SAME already-explored local optima" was false.** The
   second run called `run_all_variants_parallel()` fresh for every trial
   (`checkerboard_recovery_calibration.py:209` at the time) -- nothing was
   persisted from the first run, so the second run silently redid the entire
   hill-climb from scratch (~25 more minutes of real compute) rather than
   reranking cached candidates. Confirmed directly: no result-cache artifact
   existed anywhere in the repo at that point.
2. **The 24 controls did not match dbbi's structural profile.** dbbi is 91
   raw 9-ary symbols / 63 codes / 19 distinct types under `{b,e}` (35
   single-symbol "top" codes + 28 double-symbol "escape" codes -- confirmed
   directly against the real `DBBI` string). The 24 controls only fixed the
   63-code count (by construction, since plaintext length was fixed at 63);
   their actual raw lengths ranged 97-122 symbols, only 5/24 landed on 19
   types, and **0/24 matched both** -- verified by regenerating the same 24
   trials deterministically and checking. A harder/easier synthetic regime
   than the real target undermines exactly the comparison the harness exists
   to make.
3. Selecting the hybrid bonus weight by looking at recovery rate on the same
   24 trials being used to report the result risks overfitting the weight to
   its own test set (a real methodological gap, independent of 1-2 above).

**Fixes, in order:**

- **Persistence**: `get_local_optima()` now checks a `calibration_cache/`
  JSONL cache (keyed by a hash of `ciphertext|iters|restarts|seed_base`)
  before calling the hill-climb; a rerun of an already-computed trial now
  genuinely loads from disk (verified: second identical invocation logs
  `loaded N cached local optima ... (no hill-climb compute)` for every
  trial, cache file count unchanged).
- **Profile-matched controls**: `build_profile_matched_board()` selects, for
  each candidate 63-char plaintext, a subset of its own distinct letters
  (`find_top_subset()`, exhaustive size-<=7 subset-sum search over that
  plaintext's own letter-frequency histogram) that sums to exactly 35 --
  dbbi's exact top-code count -- then places those letters in the board's 7
  top slots and the rest in the 18 escape slots, so the resulting ciphertext
  reproduces 91 raw symbols / 63 codes / 19 types **exactly**, not just
  approximately. Verified feasible before committing to the design: ~26% of
  63-char English windows across the 3 corpora have exactly 19 distinct
  letters, and ~99% of those admit an exact subset-sum-35 partition (2,311/
  2,334 in a 9,000-window probe) -- plenty of supply (matrix: 36,870
  non-overlapping windows, book: 1,114, chat: 49,279).
- **A real bug surfaced while building the fix**: the first version of
  `build_profile_matched_board()` iterated over `present` (a Python `set`)
  directly to build `escape_present`, before shuffling it with the seeded
  RNG. Set iteration order is hash-randomized per-process (`PYTHONHASHSEED`),
  so the pre-shuffle list order -- and therefore the shuffle's output --
  silently differed across separate script invocations despite a fixed RNG
  seed, which is exactly why the cache never hit in initial testing (every
  run produced different ciphertexts, hence different cache keys). Fixed by
  anchoring the iteration to `ALPHABET26`'s fixed string order instead of the
  raw set. Verified deterministic across 3 separate fresh process
  invocations before trusting the cache again.
- **Tuning/holdout split**: `run_calibration()` now builds two disjoint
  trial sets (profile-matched controls drawn without replacement from the
  same corpora, so tuning and holdout never share a text window) --
  `hybrid_weights` are compared and the best one selected using the tuning
  set's near-exact recovery rate only; the reported recovery rate and the
  score-ceiling comparison against real dbbi both come from the holdout set
  alone, never used for weight selection.

Rerun launched at the original compute budget (12 tuning + 12 holdout
trials, 2,000 restarts/variant x 4,000 iters x 4 variants, same as before).

### Corrected, methodologically sound result (2026-07-24)

All 24 trials now match dbbi's exact profile (verified via an assertion in
`make_profile_matched_trials()` that fired on none of them: 91 raw symbols /
63 codes / 19 types, every trial). Genuine caching confirmed working
(identical rerun logs `loaded N cached local optima ... (no hill-climb
compute)` for all 24 trials; cache directory holds exactly 24 files after
both the tuning and holdout passes).

**TUNING (12 trials, used only to pick the hybrid weight):**

| Metric | Result |
|---|---:|
| Top-1-by-quadgram-score exact | 0/12 (0.0%) |
| Top-1-by-quadgram-score near-exact (<=6 mismatches) | 3/12 (25.0%) |
| Search visited the true key at some local optimum | 3/12 (25.0%) |
| Search visited a near-exact key at some local optimum | 9/12 (75.0%) |

Weight=0.3 selected (best near-exact rate on tuning: 4/12 vs 3/12 baseline --
a marginal difference, honestly weak evidence for picking 0.3 specifically,
but it's the best of the candidates tried and the only one selected using
tuning data).

**HOLDOUT (12 disjoint trials, never used for weight selection):**

| Metric | Baseline (quadgram only) | Hybrid (weight=0.3, tuned elsewhere) |
|---|---:|---:|
| Exact recovery | 3/12 (25.0%) | 3/12 (25.0%) |
| Near-exact recovery | 7/12 (58.3%) | 8/12 (66.7%) |

**Honest read: the hybrid word-bonus does NOT robustly improve recovery.**
The exact-match count is unchanged (3/12 either way) -- and it isn't even the
*same* 3 trials: the hybrid fixed one trial (14 mismatches -> 0) but broke
another that quadgram-only already had exactly right (0 mismatches -> 2), and
in a third trial made a near-exact case much worse at higher weights (2 ->
17 mismatches at weight>=1.0). Near-exact rate improved only marginally (58%
-> 67%, one trial). This is a wash, not a validated fix -- the earlier,
methodologically-flawed run's apparent clean win was an artifact of testing
on the same data used to pick the weight. Per the doc's own criterion ("only
re-run real dbbi once the improved solver reliably recovers synthetic
controls"), the word-bonus fix does NOT clear that bar and shouldn't be
treated as making top-1 selection trustworthy.

**But the metric that actually matters -- achievable best-score ceiling on a
profile-matched holdout -- is now unambiguous and stronger than before:**

Holdout best-score-per-char, all 12 trials, sorted worst to best:
`-4.248, -4.232, -4.184, -4.065, -3.970, -3.959, -3.943, -3.919, -3.864,
-3.840, -3.829, -3.819`.

Real dbbi's best decode (recomputed): **-4.529/char**. Every single one of
the 12 profile-matched holdout controls -- built from real English text
under the *exact* 91-raw/63-code/19-type/{b,e} construction dbbi's own
attack assumes, no easier and no harder -- reached a better (less negative)
score ceiling than real dbbi did, despite dbbi's original attack using ~7.5x
more restarts. The gap to even the single hardest holdout control is
**0.282/char** (-4.248 vs -4.529) -- nearly double the 0.143/char gap the
flawed, non-profile-matched first pass showed, because those earlier
controls were inadvertently making the problem easier than dbbi's real
regime (they averaged more raw symbols and often fewer effective types,
which softens the substitution-recovery difficulty).

**Verdict: the corrected calibration corroborates the original 2026-07-12
dbbi negative more strongly, not less, than the first (flawed) pass
suggested.** If dbbi really were a `{b,e}`/`build_board_9ary`-style
checkerboard over English at this exact difficulty profile, the hill-climb
should have reached at least the score ceiling every one of 12 matched real-
English controls reached -- it fell short of all twelve, by a wider margin
than previously estimated. Top-1 recovery rate stays weak in this regime
(25% exact / 58-67% near-exact even on holdout) -- consistent with the doc's
warning that this is "a difficult regime for blind substitution recovery" --
but that is a different, stricter metric than the one the original
conclusion actually relies on, and it was never the bar that needed
clearing.

No further scoring-improvement investment is planned: the word-bonus attempt
was tried, honestly evaluated on a genuine holdout, and didn't clear the bar
-- but the metric that actually validates the original negative already has
its answer, more robustly than before. Per the agreed sequencing, next is
the bounded 5x5 digraphic-cipher path (doc item #3).

## Phase 21 -- Digraphic cipher over the 25-code alphabet: implemented, CLOSED NEGATIVE (2026-07-24)

Doc item #3 (doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md): tests whether a
second digraphic layer (Playfair, Two-square, Four-square, or Bifid -- the
four standard 5x5-square families) was applied over the 25-code alphabet,
which would explain monoalphabetic quadgram hill-climbing failing even if
checkerboard segmentation is correct. Built `tools/gsmg/digraphic_sweep.py`,
kept deliberately bounded per the doc's own instruction:

- escape pairs: `{b,e}` both orders for dbbi, `{g,i}`/`{h,e}` both orders for
  faed (`TARGET_ESCAPES`, same convention as matrixsum_permutation_sweep.py/
  dual_quinary_sweep.py).
- 14 clue-motivated keywords (`CORE_KEYWORDS`): the established
  `CORE_ALPHABET_SEEDS` set, plus "matrix" and "duality" (the two words the
  doc names as this path's own motivation) and the one verified, already-
  confirmed-genuine screenplay extraction (the Phase 2/3 URL slug -- real
  Merovingian/*Matrix Reloaded* dialogue). Not a dictionary sweep.
- topology fixed to `top_first` (the one validated layout) -- not swept.
- odd-length (63/436/469-code) digraph pairing: exactly the 2 alignments
  the doc allows (pad-at-end, pad-at-start), single filler letter `X`. Bifid
  doesn't pair codes at all (whole-sequence fractionation), so this axis
  doesn't apply to it.

**A real bug caught by the script's own round-trip self-test before trusting
any result**: `assemble()`'s filler-half selection was inverted (returned the
injected filler character instead of the real letter for both alignments).
The `make_pairs`/`assemble` round-trip self-test failed immediately
(`AssertionError` on first run) rather than silently producing wrong
candidates -- fixed (swapped which half each alignment keeps) and reverified.
Also fixed a tautological placeholder assertion in the same self-test suite
(`segment_codes(...) is None or True`, always vacuously true) that would have
masked a real segmentation error; replaced with concrete, independently-
computed expected outputs.

**Sweep sizes** (escape hypotheses x keywords, all families): dbbi 1,652
candidates (2 x 14), faed 3,304 candidates (4 x 14) -- all deterministic
transforms, no hill-climbing, so both run in well under a second.

**Shuffle/null gate** (per user instruction: no readable-looking output gets
promoted without this check first) -- same max-statistic permutation-test
pattern as dual_quinary_sweep.py: shuffles each escape hypothesis's own
COMPLETE-CODE multiset (not raw a-i symbols), reruns the identical bounded
sweep on the shuffled codes, 5,000 trials each:

| Target | Real best (quadgram score) | Null mean | Null max | Empirical p |
|---|---:|---:|---:|---:|
| dbbi | -367.9 | -376.5 | -338.9 | 0.13597 |
| faed | -2943.7 | -2917.4 | -2817.3 | **0.85863** |

Neither is statistically exceptional. faed's real score is actually *worse*
than its own null mean (real -2943.7 vs. null mean -2917.4) -- unremarkable
by every measure. dbbi sits inside the null bulk, not even close to its own
5% tail. Total runtime: dbbi ~3.6ms/trial, faed ~48.1ms/trial (longer
ciphertext x more escape hypotheses), ~4m20s combined for both targets'
full sweep + 5,000-trial gates.

**AES**: per the doc ("send only statistically exceptional decodes to AES"),
did not broadly escalate -- only the single top-scoring real candidate per
target was checked as a cheap, unconditional sanity check (both: no hit).
Since neither target cleared the significance threshold, no further
candidates were escalated.

**Verdict: path closed negative.** Combined with Phase 20's calibration
result (plain monoalphabetic substitution under `{b,e}` is robustly
disconfirmed, not just weakly suggested), this rules out the two most
natural single-layer and two-layer checkerboard hypotheses for dbbi under
this construction. Remaining doc items ("Calibrated Recovery of the Raw
Checkerboard Alphabet" is now done; "Recover Missing Primary Evidence" --
the physical book's pages 57-58 gatefold -- remains the only genuinely
unexplored lead, gated on physical access) are lower priority than the
paused autokey continuation, which stays queued as unattended/overnight
compute per its original scope.

### Phase 21 correction: standard variants and calibration (2026-07-24)

The first Phase 21 verdict above was reviewed before being relied on and was
not methodologically sufficient:

1. It injected `X` into an odd-length **ciphertext** stream, decrypted the
   resulting pair, then discarded one output half as if it corresponded only
   to the injected symbol. Digraphic transforms mix both halves; plaintext
   padding does not make an odd ciphertext valid. The accompanying
   `assemble(make_pairs(text))` test was unable to catch this because it
   applied no cipher between the operations.
2. It omitted common bounded variants: period-based Bifid (including period
   5) and Two-square orientation/same-line conventions.
3. It ran a permutation null but did not perform the synthetic recovery and
   detection-power calibration explicitly required by the investigation
   plan.
4. Two-square and Four-square had no independent encrypt/decrypt round-trip
   tests.

`tools/gsmg/digraphic_sweep.py` was corrected accordingly:

- Playfair, Two-square, and Four-square now run only on even complete-code
  streams. No unsupported missing-token repair is invented. `dbbi` has 63
  codes under both `{b,e}` orderings, so standard pair ciphers are
  structurally incompatible with it; only Bifid is tested there.
- Bifid now tests periods 5, 7, 9, 13, and full-message.
- Two-square now tests horizontal and vertical layouts, each with rectangle
  and same-line-identity conventions.
- Independent round trips cover Playfair, every Two-square mode,
  Four-square, and every Bifid period.
- End-to-end controls encrypt natural English, convert the ciphertext letters
  back into complete checkerboard codes, run the real bounded sweep, and
  require exact plaintext recovery. The Playfair control first performs
  standard repeated-digraph filler preprocessing, so it does not validate only
  a relaxed nonstandard variant. Their max-statistic permutation gates use the
  same escape-hypothesis scope as the corresponding real target.
- AES escalation now occurs only after a statistically exceptional real gate,
  as the plan specified.

**Synthetic calibration** (500 trials/family, seed 20260724, 16 workers):

| Family | Code length | Escape hypotheses | Truth score | Null mean | Empirical p |
|---|---:|---:|---:|---:|---:|
| Playfair | 436 | 4 | -1992.7 | -3104.2 | 0.00200 |
| Two-square | 436 | 4 | -1903.5 | -3067.8 | 0.00200 |
| Four-square | 436 | 4 | -1903.5 | -3013.9 | 0.00200 |
| Bifid period 5 | 63 | 2 | -259.6 | -429.4 | 0.00200 |

All four exact plaintexts were recovered as the top-scoring candidate and
cleared the permutation gate at its 500-trial resolution floor. The corrected
sweep therefore has demonstrated power against in-scope synthetic examples.

**Corrected real gates** (5,000 trials/target, seed 20260724, 16 workers):

| Target | In-scope candidates | Real best | Null mean | Empirical p |
|---|---:|---:|---:|---:|
| `dbbi` | 140 (Bifid only) | -392.0 | -391.1 | 0.50590 |
| `faed` | 2,268 | -2933.0 | -2898.1 | 0.94261 |

Neither target is exceptional; no candidate was sent to AES. The earlier
numbers (-367.9/-2943.7 and p=0.136/0.859) are retained above only as an audit
trail for the flawed transform set and must not be cited as the final result.

**Corrected verdict:** the bounded, now-calibrated Bifid path is closed
negative for `dbbi`; standard Playfair/Two-square/Four-square are ruled out
there by odd ciphertext-token parity rather than by fabricated padding.
For `faed`, all four corrected bounded families are closed negative under the
tested escape pairs, keys, Bifid periods, and Two-square conventions.

## Phase 22 -- Broadened cipher/KDF oracle + staged SALPH->COSMIC pipeline (2026-07-24)

Every prior sweep in this project (all 21 phases above) tested passphrase
candidates against SALPH/COSMIC using only AES-128/256-CBC with the legacy
MD5/SHA1/SHA256 `EVP_BytesToKey` derivation -- the original `joint_attack.py`
assumption, never revisited. `Salted__` identifies the OpenSSL container, not
which cipher/KDF produced it: a correct passphrase against the wrong
cipher/KDF is indistinguishable from a wrong passphrase, so this was the
single most consequential untested premise underlying every "0 hits" result
to date.

**Path 1 -- extended cipher/KDF coverage.** `tools/gsmg/cb_common.py` gained:

- AES-192-CBC (the one AES key size the original `KDF_VARIANTS` omits).
- 3DES-CBC at all three `cryptography`-supported key sizes (24/16/8 bytes ==
  3-key / 2-key / single-key "EDE" 3DES, i.e. OpenSSL's
  des-ede3-cbc/des-ede-cbc/des-cbc under the same Salted__ container).
- PBKDF2-HMAC-SHA256, bounded to OpenSSL's own fixed default of 10000
  iterations (not an open-ended `-iter` sweep -- unbounded iteration-count
  search has no principled stopping point).

`aes_try_open_bytes` is now cipher-aware (block/IV size differs for 3DES:
8 bytes, not AES's 16 -- the exact bug class a generalization like this
invites if the pad-length bound or IV length stays hardcoded to 16). The new
`EXTENDED_CIPHER_VARIANTS` (18 combos) is strictly additive and opt-in: the
original `KDF_VARIANTS` (6 combos) is untouched, so every existing sweep
script's cost and behavior is unaffected. Six synthetic known-positive
vectors (one per new combo) were added as self-tests, since there is no real
puzzle blob to validate the new code paths against the way Phase 3.2 already
validates the original AES path.

**Path 2 -- staged SALPH->COSMIC pipeline.** `tools/gsmg/staged_pipeline.py`
implements the page-grammar reading (derive password -> open SALPH -> hash
its answer -> open COSMIC; "sha256 ans too" already motivates
`keystr_forms()`'s single/double-SHA256 forms). `derive_chain_forms()` pulls
candidate next-stage passphrases from a SALPH plaintext: the whole text, each
non-empty line, and any substring following a "password"/"answer"/"key"
label (the exact phrasing Phase 3.2's real, already-solved plaintext uses).
Necessarily dormant right now -- SALPH has never been opened, so there is
nothing real to chain -- so it was validated against a synthetic scenario
instead: a fake SALPH plaintext with an embedded "password: X" line correctly
chains into a fake COSMIC ciphertext encrypted with PBKDF2+3DES-192 keyed on
SHA-256(X), recovered end-to-end without the test telling the chain function
the answer directly. Wired into `extended_cipher_recheck.py` so any future
SALPH hit auto-triggers the COSMIC chain rather than requiring a human to
notice and manually re-run one.

**Recheck of curated candidates** (`tools/gsmg/extended_cipher_recheck.py`).
Per "recheck curated candidates first" (cheap, bounded), ran every one of
this project's small, already-distilled candidate lists (18 files -- e.g.
`last_command.txt`, `salphaseion_own_keywords_combined.txt`,
`discovered_paths.txt`, `phrases.txt`, the architect/oracle/riddle candidate
lists -- deliberately excluding the raw multi-megabyte mined corpora like
`chat_mined_lines.txt`/`matrix_script_windows.txt`, which would turn a cheap
recheck into a new large sweep) plus `CORE_ALPHABET_SEEDS` and
`VALIDATION_ANSWER`, through `answer_forms()` x `keystr_forms(newline_variants=True)`
x all 18 `EXTENDED_CIPHER_VARIANTS`, against both SALPH and COSMIC:

- 568 unique candidates after dedup.
- 14,715 keystring attempts (~530,000 total decrypt attempts across variants
  and blobs), ~7 minutes.
- **0 hits, 0 weak candidates logged.**

**Verdict:** the cipher/KDF blind spot is now closed for this project's
existing curated candidate material -- none of it opens SALPH or COSMIC
under AES-192, 3DES (any key size), or PBKDF2-HMAC-SHA256 at OpenSSL's
default iteration count, in addition to the original AES-128/256/legacy-KDF
coverage. This does not rule out the broadened cipher/KDF space against
candidates not yet curated (the raw mined corpora, or new candidate
generation), nor a non-default PBKDF2 iteration count -- both are now
cheap to test with `EXTENDED_CIPHER_VARIANTS` if a future investigation
motivates expanding scope further.

## Phase 23 -- Exact command-provenance recheck (path 3, 2026-07-24)

`wordlists/gsmg/last_command.txt` is a normalized approximation (confirmed:
spaces, dashes, and quoting all stripped). Rather than attempt open-ended
"exact command reconstruction" with no principled stopping point, this
grepped the raw, unnormalized mined chat archive
(`wordlists/gsmg/chat_mined_lines.txt`, 63,741 lines) directly for real
`openssl enc ... pass:X` and `echo ... | sha256sum`-style command lines --
if a real command was ever typed verbatim by a community member, it should
already be sitting there byte-for-byte.

**Notable find (not previously tracked in this project)**: a
`U2FsdGVkX186tYU0hVJBXXUnBUO7C0+X4KUWnWkC...` base64 fragment posted in chat
(line 36986 and neighbors) is byte-for-byte identical to the first 63
characters of this project's actual `SALPHASEION_BLOB_B64` (verified via
direct string comparison against `cb_common.BLOBS["SALPH"]`) -- confirming
two community members' password guesses nearby (`93de0175...`, `e24bd2c0...`,
`baff7ec4...`) were genuine historical attempts against the real SALPH
ciphertext, not fabricated examples. The chat itself reports these as
bad-decrypt/padding errors under AES-256-CBC specifically (a missing
trailing base64 separator, not necessarily the password). A separate
base64 fragment ("the unsolved one from the previous stage", same message
thread) does NOT match SALPH, COSMIC, or the solved Phase 3.2 blob at all
(113/128 base64 characters differ from SALPH even though both are exactly
96 raw bytes) -- an untracked third blob with no associated password in the
mined chat, flagged here but not actionable without visiting the live puzzle
page again.

`tools/gsmg/command_provenance_recheck.py` collected every non-placeholder,
non-truncated literal from these real command lines (13 candidates after
dedup -- including the 3 SALPH-fragment attempts above, a 3DES-specific
suggestion for `cosmic_duality.txt`, an explicit MD5-KDF concatenated-keyword
guess targeting a file literally named `salph.aes`, a "ZION" thematic guess,
and the exact-newline-semantics form of `echo theflowerblossoms | sha256sum`
without `-n`) and tested every one against both real blobs under the full
`KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS` coverage from Phase 22.

**Result: 0 hits.** This closes the "did we ever verbatim-preserve and fully
retest a real community password attempt, including under ciphers/KDFs the
original attempt didn't try" question for every such command this project's
raw chat archive actually contains.

## Phase 24 -- Prefix/header boundary hypothesis (path 4, 2026-07-24)

`dbbi` and `faed` are literally the first 4 symbols of their own streams.
That naming convention is confirmed legitimate (doc/GSMG_PUZZLE.md), but does
not by itself confirm or rule out the same 4 symbols also being functionally
special within the cipher (a header/selector) -- no prior sweep tested this.

`tools/gsmg/prefix_boundary_sweep.py` tested two bounded, mechanically
well-defined variants: **DROP4** (payload = `stream[4:]`, decoded under the
established escape pairs x this project's existing clue-motivated keyword
alphabets x both topologies x the existing pad25 tail-fill/merge-direction
axes) and **PREFIX_AS_KEY** (payload = `stream[4:]`, alphabet seeded directly
from the 4-symbol prefix itself -- already valid input, no transform
needed). Both variants first confirmed the prefix-dropped stream still
segments cleanly under each escape pair (no dangling escape) before any
decode was attempted.

**Synthetic-control calibration**: for each (family, target, topology)
combination, encoded a real English sample (from the book corpus) under a
known configuration matching the exact mechanic being tested, and asserted
the true plaintext is recovered as the single top-scoring candidate --
passed for all combinations.

**Real gate** (2000-trial max-statistic shuffle gate per target, same
complete-code-multiset-shuffle pattern as Phases 20/21):

| Target | Best escape pair | Real best | Null mean | Null max | Empirical p |
|---|---|---:|---:|---:|---:|
| `dbbi` | `be` | -364.4 | -360.1 | -323.6 | 0.65367 |
| `faed` | `gi` | -2848.6 | -2847.1 | -2738.3 | 0.51074 |

Neither target is statistically exceptional; no candidate was escalated to
AES (matching this project's established escalation discipline). **Verdict:
the prefix/header-boundary hypothesis is closed negative** under both tested
mechanics (discard-as-header, prefix-as-key), for both targets.

## Phase 25 -- Provenance triage of the untracked base64 fragment: confirmed real, third target added (2026-07-24)

Phase 23 flagged a base64 fragment repeated throughout the raw chat archive
that did not match SALPH, COSMIC, or the solved Phase 3.2 blob. Per the
user's explicit triage protocol (decode/record exact bytes -> inspect chat
context -> search for overlapping fragments -> compare against every
recorded blob -> only then check external sources -> add as a target only if
provenance is established), this was investigated to a conclusion rather
than assumed either way.

**Exact bytes**: `U2FsdGVkX1+0Wl49gnWTyiimluu7V3+vl7st0gUt9sWDzNLxDmlPMsDSiuW2a46zgKlIi8aaqY5gpJPPEzW1n9n3/26qs4zstWtPKF8Zs/BTNN4IiEh4qu18mdC0NAv4`
(128 base64 chars / 96 raw bytes) decodes to header `Salted__`, salt
`b45a5e3d827593ca`, 80-byte ciphertext -- divisible by both 8 (DES/3DES) and
16 (AES) block sizes, same total size as SALPH but a different salt from
all three previously known blobs (SALPH `3ab585348552415d`, COSMIC
`2d3f6fe06dc950e6`, Phase 3.2 `eefc4c5befc1656a`).

**Chat context**: appears verbatim across ~25 independent lines throughout
`chat_mined_lines.txt` (e.g. 7179, 23843, 25872, 28815, 37037, 58825),
explicitly labeled "3.2.3" and "PHASE3_3.2_CYPHERTEXT_BLOB_AES" by multiple
different community members over what the message content implies is a long
span of chat history. One message (line 58825) is a comprehensive community
summary of every unsolved puzzle piece, listing this blob first and
separately listing SalPhaseIon (dbbi/faed + the SALPH aes blob) and Cosmic
Duality (COSMIC) as distinct entries -- confirming the three are understood
as separate targets by the community itself, not a mis-transcription of one
another. No sender/timestamp metadata survives in the mined archive (it was
stripped before this project received it), so poster identity/exact
timestamps could not be recovered from this source.

**Overlapping-fragment search**: every occurrence's first 128 base64
characters is byte-identical across all ~10 full-length postings. One
apparent divergence (line 52276) was traced to a different user explicitly
constructing a deliberate "what if the two blobs are interleaved" thought
experiment (triple-quoted, clearly labeled as speculation) by splicing this
blob's first half with SALPH's second half -- not corruption or a real
distinct blob.

**External verification**: confirmed via two independent primary sources
outside this project's own chat archive:
- The blob appears verbatim in the **official** community repository
  `puzzlehunt/gsmgio-5btc-puzzle`'s README (the same repo this project's
  decoder was originally ported from).
- The actively-maintained fork `HosterjackAGV/gsmg-5btc-puzzle` (pushed
  2023-08, 109 stars, 76 forks, extensive `docs/ATTEMPTS.md`/`WALKTHROUGH.md`)
  documents it in detail as **`p32_trailing`**: an 80-byte OpenSSL blob
  **embedded at the end of the already-solved Phase 3.2 plaintext** (salt
  `b45a5e3d827593ca` -- exact match). That fork's README states the endgame
  (dbbi/faed + Cosmic Duality) is "genuinely OPEN" and its own catalog
  (~1.5M+ dictionary/thematic/structural attempts across `p32_trailing`,
  `salph_inner` [= this project's SALPH, salt-confirmed identical], `cosmic`,
  and a fourth, still-unfamiliar-to-this-project blob `urlblob`) reports it
  unsolved as of the fork's latest state. Notably, that fork's own catalog
  independently flags **"universally assumed to be aes-256-cbc"** as an
  unverified premise for this exact blob and specifically raises an
  AES-KEY-WRAP (`-id-aes256-wrap-pad`) hypothesis as untested -- corroborating
  this project's own Phase 22 finding of the same cipher/KDF blind spot,
  discovered independently before either side was aware of the other's work.

**Verdict: GSMG provenance confirmed.** Added as a third default target,
`P32TRAILING`, in `cb_common.BLOBS` (`data.P32_TRAILING_BLOB_B64`) --
every sweep script using the default blob set now automatically includes it.

**Recheck against the new target** (re-running Phase 22/23's exact same
candidate sets, now against 3 blobs instead of 2):
- `command_provenance_recheck.py` (13 real chat-mined command literals):
  **0 hits.**
- `extended_cipher_recheck.py` (568 curated candidates x 18 extended
  cipher/KDF variants x 3 blobs, 14,715 keystring attempts, ~10 minutes):
  **0 hits.**

**Not pursued here** (out of scope for triage, noted for a future session):
the fourth blob `urlblob` this same external research surfaced (found via a
hex-encoded Wayback/CDX URL path, salt `74c974e3f92e64b5`, 96-byte
ciphertext) is not yet in this project's data at all -- a further candidate
for the same triage-then-add treatment if pursued later. The AES-KEY-WRAP
cipher mode (distinct from CBC, RFC 3394) flagged by the external fork is
also not yet covered by `EXTENDED_CIPHER_VARIANTS` -- pursued next, see
Phase 26.

## Phase 26 -- AES Key Wrap (RFC 3394 / RFC 5649) hypothesis test: closed negative (2026-07-24)

Prioritized directly from Phase 25's external corroboration: the
independently-maintained fork's own catalog flags `-id-aes256-wrap-pad` as
an untested cipher-*mode* hypothesis for the same blob this project tracks
as P32TRAILING -- structurally different from every prior sweep's CBC-only
assumption (no CBC IV, wraps key material rather than arbitrary plaintext,
and carries its own built-in integrity check rather than relying on the
PKCS7-padding heuristic).

**Independent audit correction (same date):** the first implementation
tested only the strict RFC default AIVs. That did **not** reproduce the
specific OpenSSL `enc -id-aes256-wrap-pad` hypothesis that motivated this
path: OpenSSL derives a custom 8-byte IV for `wrap` or 4-byte prefix for
`wrap-pad` after the KEK. The original synthetic tests were internally
consistent but circular because both encryption and decryption used
`cryptography`'s default-AIV helpers. The first 0-hit result therefore did
not close the cited OpenSSL mode.

**Implementation** (`cb_common.py`, `aes_key_wrap_sweep.py`):
- `KEY_WRAP_KDF_VARIANTS` (12 combos: legacy sha256/md5/sha1 x {16,24,32}-byte
  KEK, plus PBKDF2-HMAC-SHA256 @10000 iter x {16,24,32}) reuses the *same*
  `evp_bytes_to_key`/`pbkdf2_bytes_to_key` derivation already validated for
  the CBC path. It tests both strict RFC default AIVs and OpenSSL `enc`'s
  derived 8-byte/4-byte custom wrap IVs.
- `aes_keywrap_try_open_bytes()` tries both RFC 3394 (`aes_key_unwrap`) and
  RFC 5649/padded (`aes_key_unwrap_with_padding`) **separately**, wherever
  the blob body's length permits (>=24 bytes for 3394's stricter minimum,
  >=16 for 5649), via `cryptography.hazmat.primitives.keywrap` (already
  available in this environment -- confirmed before writing any code).
- `raw_key_try_open()` treats a successful unwrap's output as **key
  material first**: tries it directly as an AES/3DES key (zero IV, no
  passphrase derivation) against every blob. `aes_key_wrap_sweep.py`'s
  `chain_unwrapped()` additionally tries the unwrapped bytes' text/hex forms
  as ordinary *passphrases* through the normal EVP_BytesToKey/PBKDF2+CBC
  path -- covering both plausible interpretations, only ever run after a
  real unwrap succeeds (never speculatively).
- Every branch validated against synthetic known-positive vectors before
  touching the real blobs: `cb_common._self_test_keywrap()` round-trips
  both RFC 3394 and RFC 5649 for all 12 KDF variants AND includes a
  **negative control** (wrong passphrase -> wrong KEK must NOT unwrap) --
  worth calling out specifically, since Key Wrap's whole value as an oracle
  here rests on its integrity check actually discriminating, not just on
  the happy path decrypting cleanly. `aes_key_wrap_sweep.py --self-test`
  separately validates the *sweep script's own* chaining logic end-to-end
  with a synthetic two-stage scenario (KEK-derive -> RFC-3394-wrap a raw
  AES key -> that raw key zero-IV-decrypts a second synthetic blob),
  confirming `sweep()` finds the unwrap and `chain_unwrapped()` recovers the
  second-stage plaintext, without being told either answer in advance.
- Four fixed vectors generated independently by OpenSSL 3.0.13 validate
  legacy/PBKDF2 x wrap/wrap-pad interoperability and prevent the original
  default-AIV-only mistake from passing self-test again.
- `urlblob` deliberately **not** added -- per the task's explicit
  instruction, it needs its own exact-archived-byte-and-provenance
  verification first (the same triage discipline Phase 25 used for
  P32TRAILING), out of scope here.

**Result**:

```
python3 tools/gsmg/aes_key_wrap_sweep.py
```

```
[*] loaded 568 curated candidates
[*] 12 KEK-derivation variants x 3 blobs (SALPH, COSMIC, P32TRAILING) x {rfc3394, rfc5649} x {default-AIV, OpenSSL-IV}
[*] 14,715 KEK-deriving passphrase attempts
[*] 2,118,960 effective unwrap operations
[*] no candidate's derived KEK unwrapped any blob under RFC 3394 or RFC 5649
```

(~23m21s real time for the corrected four-mode run.)

**Verdict: closed negative.** No candidate in this project's curated set
derives a KEK (under any of the 12 legacy/PBKDF2 variants) that
successfully AES-Key-Wrap-unwraps any of the three tracked blobs, under
either RFC algorithm with either strict default or OpenSSL-derived wrap
IV semantics. Since the underlying candidates are the exact
same 568 already tested under CBC (Phase 22), this specifically rules out
"right passphrase, CBC assumed but Key Wrap was the real mode" for that
candidate set -- it does not rule out Key Wrap with a *different*,
untested passphrase, nor does it touch `urlblob` (not yet added) or the
still-unadded fourth blob's own provenance question.

## Phase 27 -- `urlblob` provenance verification, quarantine, and sweep: closed negative (2026-07-24)

Per the user's explicit 6-step instruction: verify `urlblob`'s exact
archived bytes and provenance before touching it at all, add it only as a
quarantined target, then rerun the extended-CBC and corrected Key-Wrap
sweeps against it.

**Provenance re-verification (steps 1-3)** -- deliberately went further than
trusting the HosterjackAGV fork's own citation:
- Fetched the real Internet Archive Wayback CDX API directly:
  `curl "http://web.archive.org/cdx/search/cdx?url=gsmg.io&matchType=domain
  &output=json&limit=100000&fl=original,timestamp"`. This located the exact
  archived URL myself, independent of the fork's docs.
- Two captures of the same gsmg.io URL path exist:
  - **2026-01-05 01:59:08** -- the COMPLETE path. Decoding its hex yields
    112 raw bytes: `Salted__` + salt `74c974e3f92e64b5` + a 96-byte (6
    clean AES blocks) ciphertext.
  - **2026-02-07 19:00:55** -- a TRUNCATED duplicate of the same path: only
    40 raw bytes (header + salt + a 24-byte, non-block-aligned remainder).
  - The fork's own docs (`docs/ATTEMPTS.md`) cite the **2026-02-07** date as
    the capture timestamp -- that is the truncated one, not the complete
    one. This project's own re-verification caught and corrects that.
- The complete-capture bytes were independently cross-checked two ways and
  matched exactly: (a) decoding the CDX-returned hex URL path directly, and
  (b) the fork's own `content/demos.js`, which embeds the identical blob as
  a UI-demo base64 literal -- byte-for-byte identical to (a).
- Fetched both captures' actual page bodies (via
  `web.archive.org/web/<ts>id_/<url>`) and confirmed they are the site's
  ordinary ~36KB SPA shell, differing only in a per-request CSRF token --
  i.e. the payload really does live only in the URL path, never in the
  response body, as the fork's docs claimed.

**Quarantine, not a peer default (step 4)** -- unlike `P32TRAILING` (Phase
25: corroborated by the official README + a solved-plaintext location),
`urlblob` has no official-README or solved-plaintext corroboration -- the
source fork itself calls it "orphaned" and reports no tested key decrypts
it. Added `data.URLBLOB_B64` (full provenance comment, including the
timestamp correction above) and `cb_common.QUARANTINED_BLOBS` (kept
separate from the default `BLOBS` every other sweep touches). Added an
explicit `--include-quarantined` opt-in flag to both
`extended_cipher_recheck.py` and `aes_key_wrap_sweep.py`; every existing
script's default behavior is unchanged. `sweep()`/`chain_unwrapped()` in
both scripts now thread a `blobs` parameter through rather than relying on
cb_common's default.

**Recheck against `urlblob` (step 5)**:

```
python3 tools/gsmg/extended_cipher_recheck.py --include-quarantined
```
```
[*] loaded 568 curated candidates from 18 files + seed lists
[*] 14,715 attempts across 18 extended cipher/KDF variants x 4 blobs (SALPH, COSMIC, P32TRAILING, URLBLOB)
[*] no candidate opened any blob under any extended cipher/KDF variant
```
(~14m03s real time.)

```
python3 tools/gsmg/aes_key_wrap_sweep.py --include-quarantined
```
```
[*] loaded 568 curated candidates
[*] 12 KEK-derivation variants x 4 blobs (SALPH, COSMIC, P32TRAILING, URLBLOB) x {rfc3394, rfc5649} x {default-AIV, OpenSSL-IV}
[*] 14,715 KEK-deriving passphrase attempts
[*] 2,825,280 effective unwrap operations
[*] no candidate's derived KEK unwrapped any blob under RFC 3394 or RFC 5649
```
(~27m18s real time.)

**Verdict: closed negative** for this candidate set. `urlblob`'s exact
bytes and provenance are now independently confirmed (more rigorously than
the source fork's own citation, which this pass corrected), it's tracked as
a quarantined target, and the same 568 curated candidates already exhausted
against SALPH/COSMIC/P32TRAILING under both CBC (extended cipher/KDF
coverage) and AES Key Wrap (RFC 3394/5649, strict and OpenSSL-IV) also open
nothing against it. Does not rule out a different, untested passphrase, nor
any cipher/KDF hypothesis not yet covered by `EXTENDED_CIPHER_VARIANTS` or
Key Wrap. Per the user's step 6, the bounded adjacent-difference/
self-synchronizing DBBI transform hypothesis is the next queued path --
not yet designed or implemented as of this phase.

## Phase 28 -- Puzzle-address split and blockchain metadata candidates (2026-07-24)

Investigated whether the prize address itself provides a bounded
`half`/`better half` reading rather than treating arbitrary blockchain fields
as passwords.

- The address is directly connected to the final phase: the verified
  SalPhaseIon URL is SHA-256 of `GSMGIO5BTCPUZZLECHALLENGE` concatenated with
  `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`.
- `1GSMG1` is a deliberately vanity-mined visible unit. The leading `1`
  represents the P2PKH version byte; the second `1` is part of the chosen
  vanity prefix.
- Both the prize address and repeated halving recipient are exactly 34
  Base58 characters, allowing one clue-bounded split at 17+17. This is
  consistent with, but does not prove, a connection to the verified Phase
  3.2 plaintext `THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF`.
- Base58Check decoding was independently recomputed. Prize HASH160/checksum:
  `a9553269572a317e39f0f518cb87c1a0ee1dbae4` / `b6fcbf65`; recipient:
  `4bc468447fe1b048ad030a2f9a125478eabc4ed6` / `86aa25d1`.
- Live transaction verification confirmed the two creator spends and exact
  outputs. Repeated dust values and block heights were not promoted: they
  introduce open-ended transaction numerology, and the 666-satoshi inputs
  originated as external deposits rather than values authored inside the
  spending transactions.

Added 14 bounded candidates to
`wordlists/gsmg/blockchain_metadata_candidates.txt`: the vanity components,
network-prefix-stripped tail, exact halves and swapped-half forms for the two
relevant addresses, and canonical HASH160/checksum components.

Focused recheck of only these additions:

```
CBC: 14 candidates, 576 unique passphrase forms,
     24 original+extended cipher/KDF variants x 4 blobs: 0 hits
Key Wrap: 14 candidates, 612 generated passphrase attempts,
          12 KEK variants x 4 blobs x 4 wrap semantics: 0 hits
```

**Verdict:** the address is genuinely connected to the final-phase entry
mechanism, and the exact 17+17 split is a defensible bounded candidate source,
but none of these direct forms opens a tracked blob. Do not expand into
arbitrary transaction fields without a new creator clue.

## Phase 29 -- Adjacent-difference / self-synchronizing-cipher hypothesis: screen-negative, not advanced (2026-07-24)

Tested whether each observed raw dbbi/faed symbol is a function of itself and
its immediate neighbor (a lag-1 differential/self-synchronizing encoding) --
a question no prior sweep had tested, all of which assumed each position is
an independent code. Explicitly bounded per instruction ("evidence is
weak"): 4 base transforms (`diff`, `sum`, `inv_diff`, `inv_sum`) x direction
(forward/reverse), **linear boundary only** -- circular boundary is
mathematically ambiguous (a 9-way additive-offset family of solutions for
`diff`; parity-dependent solvability for `sum`, dbbi-odd/faed-even) and was
explicitly deferred, not attempted.

This module (`tools/gsmg/adjacent_diff_sweep.py`) went through three rounds
of external review before implementation, each catching a real issue:
circular-boundary math was wrong (dropped); the established escape pairs
({b,e}/{g,i}/{h,e}) were derived by frequency analysis of the *original*
streams and don't transfer to a transformed stream (re-derived fresh per
transformed stream instead, inside every null trial, since the selection is
part of the fitted model); `quadgram_solver.score()` is an unnormalized sum
biased toward length (normalized per-quadgram throughout); escape pairs are
*ordered* (both `(e1,e2)`/`(e2,e1)` tested); the 47%-density reference
(Phase 3.2.2's own escape share) is a heuristic specific to that
plaintext/keyword, not intrinsic to the cipher, so pair selection uses a
hedged top-`k` (filtered for clean segmentation *before* ranking, not after)
with `k` **calibrated as a hard gate against fixed synthetic controls only**
-- the real sweep does not run unless the pipeline first recovers its own
known pair+plaintext at some `k` in {3,5,7,9}; testing both targets at
p<0.01 each risked a combined false-positive rate near 0.02, corrected to
p<0.005 per target (Bonferroni); the staged 500-then-5000-trial design uses
a fully independent seed for the confirmation batch, so Stage 1 is never
pooled into the reported result (avoiding optional-stopping bias).

**Calibration**: failed at k=3 and k=5 specifically for `faed`'s
`escapes_first` topology across all 4 bases x 2 directions (8 failures each
time) -- genuinely discriminating, not vacuously passing at the first `k`
tried. Passed at **k=7**, frozen for the real sweep.

**Result**:
```
[stage 1 screen] dbbi: real_best=-5.8336 null_mean=-5.7474 null_max=-5.3046 p_500=0.77246 (500 trials)
[*] dbbi: not advanced beyond screening (p_500=0.77246 >= 0.02)
[stage 1 screen] faed: real_best=-6.3225 null_mean=-6.2643 null_max=-6.1005 p_500=0.87824 (500 trials)
[*] faed: not advanced beyond screening (p_500=0.87824 >= 0.02)
```
(~2m20s real time, k=7 calibration.) Both targets' real-data best
normalized score was actually *below* their null mean (not merely
non-significant) -- as clean a negative as this design can produce. Neither
target cleared the cheap Stage-1 screen, so Stage 2's expensive independent
5,000-trial confirmation batch was correctly never run, and nothing was
escalated to any AES oracle.

**Verdict: screen-negative and operationally deprioritized**, scoped
precisely: no evidence for lag-1 differential/self-synchronizing encoding
(both directions, linear boundary) under the top-7 closest-to-47%-density
structurally-valid escape pairs (both orderings) x the existing
`CORE_ALPHABET_SEEDS`/`TAIL_FILLS`/`MERGE_DIRS`/`TOPOLOGIES` axes. Per the
pre-registered design, neither target advanced beyond the 500-trial screen,
so this is not a Stage-2-confirmed negative and should not be phrased as
mathematically ruling the family out. It is also not an exhaustive search of
all 36 possible escape pairs (k=7 is a deliberate, non-exhaustive ceiling),
the circular-boundary variant (separately scoped, not attempted), or any lag
beyond adjacency. The separate, non-gating transition-mask/run-length
diagnostic (`--diagnostics-only`) also found nothing exceptional after fixing
its two-sided transition-rate statistic to center on the permutation null
mean rather than an unrelated 0.5 baseline (dbbi transition-rate p~0.76,
max-run p~0.90; faed transition-rate p~0.40, max-run p~0.14).

## Phase 30 -- Creator-authored clue-to-operation ledger (2026-07-25)

Re-audited the creator-only Telegram export and restored conversational context
from the full transcript without treating community interpretations as clues.
Corrected a provenance-count error in earlier documentation: the export has
**411 creator-message headers**; 1,283 is its line count, and the previously
stated 444-message count was incorrect.

The resulting ledger is in
`doc/GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md`. Its central finding is that the
creator's statements form a dependency chain rather than a wordlist:

```
first/zero puzzle piece
 -> yellow/blue numeric values
 -> 18-1-2 + BIT = RABBIT / first-piece grid
 -> {1,4,21}: one FEFE cell, bit 4, character 21
 -> zero-based position 163 (prime), marked bit value 0
 -> required prime operation
 -> characters zeroed out
 -> matrixsumlist
 -> lastwordsbeforearchichoice
 -> recognizable yin-yang next phase
 -> short final solve
```

The exact placement of zeroing inside the middle of the chain remains
unspecified. Existing direct-passphrase, generic prime-position, generic
complement, and adjacent-difference negatives do not identify that missing
source object or transition.

At this point the highest-value unresolved item appeared non-computational:
on 2022-12-11 the creator called a missing post “very specific,” and on
2023-01-08 explicitly said `@barrystyle` had already provided a very specific
hint. Phase 36 later recovered the post's semantic identity as the *Cosmic
Duality* book discovery; it was not an unknown prime diagram. Improving or
rerunning the adjacent-difference sweep remains unsupported without new
creator-authored evidence pointing to a differential transform.

## Phase 31 -- Exact first-piece yellow/blue reconstruction (2026-07-25)

Reconstructed all 24 colored objects directly from the byte-verified archived
`follow_the_white_rabbit.png`, using the already-validated Stage-0 order
(top-left counter-clockwise spiral). The order was therefore fixed by the
known plaintext `gsmg.io/theseedisplanted` before testing any numeric
property.

The colored sequence is:

```
BBBBYBBBYYBBBBYBBYYBYYBY
```

It has an exact complementary interpretation:

```
blue=1, yellow=0:
111101110011110110010010 = F73D92 = RGB(247,61,146)

yellow=1, blue=0:
000010001100001001101101 = 08C26D = 574061 (prime)
```

This concretely explains the creator-authored sequence “Roses…” then
`yellowblueprimes`: the original polarity forms a rose/pink RGB value and the
inverse polarity forms a prime. It also corrects the earlier overstatement
that the colors had no clue value. Their *positions* are redundant with the
URL's ASCII LSBs, but the creator-clued polarity interpretation is not.

Added assertion-backed
`tools/gsmg/first_piece_color_reconstruction.py` and the complete provenance
table in `doc/GSMG_FIRST_PIECE_COLOR_RECONSTRUCTION.md`. Directly applying
`{1,4,21}` to the 24 objects gives `ggn`/`BBY` (one-based) or `s.t`/`BYY`
(zero-based), neither self-validating; that later hint's indexed object
remains unresolved.

Saved 20 exact, bounded forms (bitstrings, hex, decimal, RGB, and exact source
cell colors) to `wordlists/gsmg/first_piece_color_candidates.txt`. Focused
oracle recheck across all three authenticated blobs plus quarantined URLBLOB:

```
CBC: 261 unique keystrings x 24 original+extended variants x 4 blobs, 0 hits
Key Wrap: 540 generated passphrase attempts x 4 blobs, 0 unwrap hits
```

**Verdict:** `yellowblueprimes` now supplies the concrete prime
**574061**, with complementary rose value **F73D92**. These are intermediate
outputs, not direct blob passwords. The next unresolved creator-authored edge
is `574061 -> matrixsumlist`. Phase 36 later identifies the supposedly
missing creator-validated `barrystyle` post as the already-investigated
*Cosmic Duality* book lead, so it does not independently constrain this edge.

## Phase 32 -- `574061 -> matrixsumlist` checkpoint (2026-07-25)

The six decimal digits of the reconstructed prime form a natural 2x3 matrix:

```
5 7 4
0 6 1
```

Its row sums are `16,7`; its total is `23`. This reproduces exactly, and in
order, the conspicuous values in the already-solved Architect plaintext:
`twenty-three ciphers, sixteen encryptions ... seven intertwined passwords`.
Unlike the previously debunked 23/16/7 cross-phase mask, this derivation uses
only the creator's sequential clue chain and does not depend on the
statistically ordinary `yang` match.

This is a strong checkpoint, not yet a complete solve. The next operation,
`lastwordsbeforearchichoice`, still needs the exact Architect transcript frozen
and a bounded forward/backward, zero/one-based extraction with indices
`23,16,7`. Full checkpoint and next-test rules:
`doc/GSMG_MATRIXSUMLIST_CHECKPOINT.md`.

## Phase 33 -- Architect-choice extraction: `BUT/HYE -> EOL` (2026-07-25)

Frozen the source to the local *Matrix Reloaded* screenplay PDF and extracted
only the Architect's dialogue blocks before `choice`, excluding screenplay
labels and stage directions. Applied `23,16,7` under exactly four
preregistered conventions:

```
forward one-based:  BOTH ULTIMATELY THE -> initials BUT, endings HYE
forward zero-based: BEGINNING EXPRESSED MOMENT
backward one-based: YOUR TO AS
backward zero-based: TO MATRIX SPECIES
```

The forward one-based convention has an objective, unique check: `BUT` is
exactly the Architect's first spoken word after `choice`. The source sentence
also contains the explicit “both beginning and end” language, supporting the
two word-edge rails. Adding the matrix sum list directly to the end rail gives:

```
HYE + [23,16,7] = EOL
```

`EOL` (“end of line”) independently matches the page's embedded `enter` and
newline-sensitive command grammar. Added assertion-backed
`tools/gsmg/prime_matrixsum_reconstruction.py`; it also confirms
`forward_2x3_rows` is the only bounded digit orientation producing ordered
row sums `16,7`.

Focused direct-oracle check of 12 selected-phrase/edge/EOL forms against all
four tracked blobs: 216 unique keystrings x 24 CBC variants, 0 hits; 306 Key
Wrap passphrase attempts, 0 unwrap hits. `BUT/HYE/EOL` are therefore
intermediate validation/operations, not direct passwords under current
coverage.

**Current chain:** `574061 -> [23,16,7] -> BOTH/ULTIMATELY/THE ->
BUT/HYE -> EOL -> Enter/newline`. This is much more constrained than the old,
debunked 23/16/7 mask narrative and does not reuse its apophenic `yang`
validation. It remains an incomplete solve because no blob or private key has
opened.

## Phase 34 -- `BUT/HYE` yin-yang rail audit (2026-07-25)

The selected word edges supply an objective 9-ary polarity:

```
B <-> H    mirror9 opposites
E -> E     fixed center
```

Filtering `BUT/HYE` to the puzzle's `a-i` symbols yields `B/HE`, directly
deriving the mirrored `{b,e}` and `{h,e}` escape hypotheses. This is stronger
than the old generic mirror9 motivation because the symbols now come from the
creator's exact clue chain.

The rail order `HYE BUT` also parses as `H | YE | BUT`: `H` is in front of
the initials of “your eyes,” followed by literal `BUT`, matching the next
creator-authored clause “…in front of your eyes but…”. Alphabetically ordering
the end rail by beginning-key `BUT` gives the secondary standard-columnar
output `HEY`.

Added exact source-internal enumeration to
`prime_matrixsum_reconstruction.py`. Among all 357,840 ordered triples:
160 match boundary word `BUT`; 24 match observed shifted marker `EOL`; 4 match
both; and 12 match `BUT` plus observed keyed-end word `HEY`. The independently
derived `(23,16,7)` is present in both joint sets. These counts are descriptive,
not formal p-values, because `EOL`/`HEY` were recognized after extraction.

Bounded checks were negative:

- direct extended-CBC and Key-Wrap tests of newly implied `H` against all four
  tracked blobs: 0 hits;
- SHA-256 routes for `H`, `HEY`, `HYE`, and `HYEBUT`: absent from the local
  mirror and path inventory;
- 17 exact Architect-derived seeds under `dbbi/{b,e}` and `faed/{h,e}`, both
  escape orders/topologies, 26 drop letters, three tail fills, two merge
  directions, and six standard AES KDF variants (10,608 structural
  configurations per target): 0 hits.
- full curated `{h,e}` product backfills: chain-addition, 280 x 280 = 78,400
  pairs / 627,200 decode attempts, 0 hits in 90.4s; autokey, the same 78,400
  pairs, 0 hits in 181.8s. Both tested FAED only and both `{h,e}` orders.

**Verdict:** `BUT/HYE` likely is the promised recognizable yin-yang state, not
another literal password. It grounds `{h,e}` as FAED's priority mirror pair
and implies a one-character `H` rebus, but neither opens a tracked blob or a
known local hash route. The small/curated `{h,e}` coverage is now closed; only
the recorded large-dictionary autokey continuation remains. Next work should
identify the intended non-blob lock before spending hours on that coverage
expansion; broad new transforms remain unjustified.

## Phase 35 -- non-blob `H` lock, zeroing, and Cosmic-boundary audit (2026-07-25)

Traced every authenticated archived puzzle page. Only the hidden Stage-1
`POST /phase1verification` password field is interactive. The known password
returns a 302 to the documented `choiceisanillusion...` page; no archived
response, creator statement, route artifact, or source code supports a second
password selecting another destination. This remains community speculation,
not a testable recovered lock.

Added `first_hint_hash_audit.py`. It validates Bitcoin address derivation
against the private-key-1 compressed/uncompressed vectors, reproduces the
known SalPhaseIon route hash from the normalized visible banner plus prize
address, then checks five exact first-hint materials as P2PKH private keys, CBC
passphrases, Key-Wrap passphrases, and direct cipher keys. Result: zero matches
against the prize/halving addresses and zero cryptographic hits. `H = hash`
explains an already-solved transition but adds no new key.

Added `hush_zero_sweep.py` for the exact creator-grounded pole operations:
delete, replace with `a` (`a=0`), or collapse to center `e`; DBBI pole `b`,
FAED pole `h`. Across 19 exact Architect-derived seeds and every bounded board
axis: 71,136 structural configurations, 0 hits, 0 new weak candidates.

The naturally segmented creator clause has 27 words, matching Cosmic's 27
authored line boundaries. Added `cosmic_boundary_word_audit.py` with four fixed
readings (word-length parity chooses boundary side; word length indexes inward
from either side) and a word-multiset shuffle max gate. Results:

- 10,000 trials, seed 20260725: p=0.056494;
- 50,000 trials, seed 12345: p=0.049399.

The winning decode is non-language binary
`7620fe87a93e5231f466702e6ee8c342545b66ce`. The nominal p≈0.05 is not
promoted: segmentation was selected after noticing the boundary count, the
project-wide multiple-testing burden is unaccounted for, and there is no
semantic or cryptographic validation. No AES escalation.

Full reasoning and exact scopes:
`doc/GSMG_NON_BLOB_LOCK_AUDIT.md`.

**Verdict:** local creator-grounded interpretations of `H` are exhausted
without a new lock. At this point primary-evidence recovery of the purportedly
missing creator-validated `barrystyle` artifact appeared to dominate further
transform invention; Phase 36 substantially closes that gap.

## Phase 36 -- barrystyle provenance and 196-cell yellow-mask prime (2026-07-25)

The missing Telegram media itself was not recovered, but the conversation
recovers its semantic identity with high confidence:

- on 2022-12-11 `semaj` says he Googled a phrase he assumed belonged to a
  hint, immediately after the creator calls the omitted post “very specific”;
- on 2023-01-08 the creator names `@barrystyle` as the person who supplied
  that very specific hint;
- on 2024-08-01 a participant asks `@barrystyle` what he searched “to get to
  the book,” and `semaj` answers `cosmic duality: mysteries of the unknown`.

These are pinned to the raw export rather than inferred from the ledger:
`_work/chat_transcript.txt:20027`, `:20070`, `:71524`, and `:71527` in the
companion `gsmgio-5btc-puzzle` repository. The pages 57-58 gap is a separate
image-inventory finding, not something inferred from those chat lines: the
photographed page 56 directly cross-references real content on page 58, while
the available photos continue at page 59.

This establishes that `semaj` is the displayed sender corresponding to
`@barrystyle`, and that the creator-validated missing post was the *Cosmic
Duality: Mysteries of the Unknown* book discovery. It was not an unidentified
prime image. The exact media bytes remain unavailable, but the operational
evidence gap is substantially closed because the book screenshots and OCR
have already been audited. The associated physical gap remains pages 57-58.

A separate September 2023 discussion records barrystyle's own later
yellow-grid observation. He describes the full 14x14 picture as a 196-bit
yellow occupancy array, read left-to-right, then reversed and inverted.
`tools/gsmg/first_piece_full_mask_audit.py` reproduces the exact result:

```
100433436204244105573859228564110291168344943733122168512511
```

It is a 60-decimal-digit probable prime. This is distinct from the 24 colored
LSB sequence's `574061`: it uses all 196 cell positions as a sparse color
mask and requires both reversal and inversion.

The original chat treated primality as strong confirmation, but a correct
profile-preserving family-wise null does not support that interpretation.
The null keeps the 24 colored character-boundary cells fixed, shuffles the
observed 9 yellow/15 blue labels, and tests the same eight-member family
(`yellow`/`blue` x original/reversed x indicator/inverted):

```
50,000 trials, seed 20260725: p=0.060099
200,000 trials, seed 12345:   p=0.059445
```

The observation is reproducible but not statistically exceptional after its
small transform family is included. It is community-derived rather than
creator-authored and remains **unpromoted**. It neither invalidates the more
compact `574061 -> [23,16,7]` chain nor supplies evidence for replacing it.

For completeness, five exact representations of the reproduced large prime
(decimal, lower/upper hexadecimal, `0x` hexadecimal, and 196-bit binary) were
checked against all three authenticated blobs plus quarantined URLBLOB:
144 extended-CBC candidate attempts and 144 Key-Wrap candidate attempts,
0 hits in both cases.

## Phase 37 -- `{1},{4},{21}` and the FEFE prime zero (2026-07-25)

The creator-only ledger had incorrectly treated `{1},{4},{21}` as three free
indices. Original context and exact image geometry resolve it much more
tightly:

- the message was posted on `01.04.2021`, camouflaging the values as an
  April-Fools date;
- later the same day, after discussion of the special rabbit-grid pixel and
  the 15 blue/9 yellow/1 exceptional-cell profile, the creator writes
  `R=18, A=1, B=2` and “1812 bit”;
- `18-1-2 + BIT` is the A1Z26 rebus `RABBIT`, fixing the target object;
- the rabbit grid contains exactly **one** `FEFE` cell, at the **4th bit** of
  the **21st character** of `gsmg.io/theseedisplanted`.

The located cell is the zero bit inside character `n`. In the already
validated spiral its zero-based position is **163**, which is prime; the
one-based position 164 is composite. This is an unusually dense checkpoint:
`{1,4,21}`, “first or zero,” prime importance, and zeroing all converge on the
same source cell without a free transform.

`first_piece_color_reconstruction.py` now asserts the complete descriptor.
Historical flat indexing of the 24 color cells is retained only as negative
bookkeeping. A bounded local route audit checked `FEFEFE`, `163`, `n`,
`1812bit`, and zero/remove/flip forms of character 21, with raw and SHA-256
path forms. No puzzle route matched. The mirror's literal `/0` capture is a
2025 generic SPA shell, not the 2021 puzzle door.

The same ten exact forms were checked against all three authenticated blobs
plus quarantined URLBLOB: 252 extended-CBC candidate attempts and 252
Key-Wrap candidate attempts, 0 hits. Applying the newly grounded zero-based
prime set directly to the 196-bit spiral also failed semantically:
zeroing every prime-indexed bit gives
`Bc,b*(k+d(e3 a$hc hanpad`; extracting the 44 prime-indexed bits gives binary
`bafba69efe15` (or reversed `a87f796df5d`). None is a readable next-stage
instruction, so this literal prime-bit branch is closed.

**Current unresolved edge:** what consumes the marked prime-zero cell. The
next branch should use only `163`, `n`, bit `0`, or `FEFEFE`; it should not
return to arbitrary `{1,4,21}` indexing.

## Phase 38 -- bounded convergence of the prime-matrix and FEFE threads (2026-07-25)

Added `thread_convergence_audit.py` to test only relations fixed before the
run:

1. the FEFE byte's relationship to the 24 yellow/blue LSB markers;
2. whether FEFE's zero-based grid coordinate is a directed orthogonal
   adjacency in the fixed `[[5,7,4],[0,6,1]]` matrix;
3. whether FEFE's spiral index is a decimal concatenation of one fixed
   sum-list value and one fixed matrix dimension, testing all values,
   dimensions, and both orders;
4. whether `{1,4,21,163}` directly and uniquely selects the three-character
   `BUT/HYE/HEY/EOL` rails.

The exact same-byte overlap is:

```
character 21 = n = 01101110
FEFE marks bit 4 = 0
the same byte's LSB marker is yellow = 0
```

The yellow overlap alone is ordinary: 9/24 character-boundary markers are
yellow. The stronger structural intersections both hold:

```
FEFE coordinate0 = (7,4)
(7,4) is a directed adjacent pair in matrix row [5,7,4]

FEFE spiral0 = 163
163 = 16 || 3
16 is the first matrix-row sum; 3 is the matrix width
```

An exhaustive null moved the one FEFE anomaly over the 172 cells not already
occupied by the 24 fixed blue/yellow boundaries. It retained the full
directed matrix-adjacency family and all sum-list/matrix-dimension
concatenations:

```
coordinate-family matches: 12/172 = 0.069767
index-family matches:       9/172 = 0.052326
joint matches:              1/172 = 0.005814
joint cell:                 spiral0=163, row0=7, column0=4
```

This is descriptive, not a formal discovery p-value: the two relation
families were recognized after the underlying artifacts were known, and the
project-wide search burden is not represented by 172 cells. Still, the
intersection is exact and unique inside this bounded family, supporting that
the `574061 -> matrixsumlist` and `{1,4,21} -> FEFE` threads describe
composable facts about the same first-piece construction rather than
unrelated paths.

No downstream operation follows uniquely. Direct one-based selection on each
three-character rail leaves only selector `1`, yielding `B/H/H/E` depending
on the chosen rail; `4`, `21`, and `163` do not fit. No AES escalation was
performed.

The closed arithmetic family requested during review was then added before
computing it: for each of `23,16,7`, test subtraction, modulo, and GCD against
163; additionally test decimal digit sum and modulo the total `46`. A hit had
to equal the frozen nontrivial target set
`{2,3,4,5,6,7,8,16,21,23}` from the matrix dimensions/digits, sum list,
FEFE descriptor, and `B/E/H` A1Z26 values. Real matches were:

```
163 mod 23 = 2
163 mod 16 = 3
163 mod 7  = 2
```

They are not exceptional. Under the same 172-cell eligible-index null,
115/172 positions produce at least three family hits (`0.668605`). This
arithmetic branch is closed. A matrix-to-byte transform was explicitly not
run: six matrix digits cannot map to eight byte bits without an ungrounded
padding, truncation, or wraparound choice.

Although `163` is a Heegner number and is associated with the famous
near-integer involving `e^(pi*sqrt(163))`, no creator clue connects this
number-theory fact to GSMG. It is explicitly excluded as an unbounded trivia
branch.

**Verdict:** convergence is real but remains an addressing/checkpoint result.
The next operation must explain why matrix suffix `(7,4)` and `16||3` should
be read as an address, rather than merely observing that both identify FEFE.

## Phase 39 -- matrix-row self-addressing grammar (2026-07-25)

Searched creator-authored messages for an addressing instruction before
adding another transform. No creator message says “coordinate,” “row,”
“column,” “append,” or “concatenate.” Three creator-grounded pieces do exist:

- `matrixsumlist` in the creator's reversed-binary message permits treating
  each matrix row as a list and summing it;
- `R=18, A=1, B=2 ... 1812 bit` explicitly demonstrates variable-width
  decimal concatenation (`18||1||2`);
- “First or zero” independently supports the zero-based grid convention
  because FEFE is prime only at spiral index 163, not one-based 164.

This motivates one strict row-list grammar, applied symmetrically to both
matrix rows rather than selecting the successful row:

```
coordinate0 = tail(row)
spiral0     = decimal_concat(sum(row), len(row))
```

Results:

```
row [5,7,4]:
  tail coordinate = (7,4)
  sum||length = 16||3 = 163
  actual spiral index of (7,4) = 163  MATCH (FEFE)

row [0,6,1]:
  tail coordinate = (6,1)
  sum||length = 7||3 = 73
  actual spiral index of (6,1) = 57   NO MATCH
```

Across all 720 permutations of the fixed six-digit multiset, 12 contain a
self-consistent row under that strict grammar; all 12 point to FEFE
(`12/720 = 0.016667`).

However, `tail` is not independently creator-specified. Head/tail,
forward/reversed coordinate order, and `sum||length`/`length||sum` are eight
genuinely comparable readings. Keeping all eight inside the family raises the
exact permutation-null rate to:

```
any self-consistent address: 48/720 = 0.066667
FEFE address:                48/720 = 0.066667
```

The phrase immediately following `matrixsumlist` is
`lastwordsbeforearchichoice`, but using its word `last` retroactively to pick
the list tail would be post-hoc double use; it is already a separate,
successfully reconstructed instruction. Therefore it is not accepted as a
tail selector.

**Verdict:** the strict grammar is the clearest explanation yet for both
`(7,4)` and `163`, and its concatenation step has genuine creator precedent.
At this stage it remained an **unpromoted addressing hypothesis** because the
only decisive choice—tail rather than head—lacked independent support, and
the honest eight-variant family was not exceptional. Phase 40 subsequently
finds independent visual support for the tail selector. No downstream
transform or AES test was justified here.

## Phase 40 -- independent tail-selector audit (2026-07-25)

Searched all creator-only uses of `tail/head/last/end/beginning/left/right`,
then inspected the exact first artifact rather than borrowing
`lastwordsbeforearchichoice` a second time.

Most creator uses of “last” are ordinary phase/timing language. The apparent
exception, “You only need the last number of pi,” is explicitly a joke in its
raw 2024 conversation: participants immediately discuss pi's infinite digits
and “searching for nothing.” It is not accepted as a matrix-tail instruction.

The first artifact itself supplies better, independent evidence. A rabbit is
drawn centrally over the 14x14 grid. Its ears/head are visibly on the left and
its small tail is on the right. This is the same object independently fixed by:

- the original creator instruction about the “rabbits nest”;
- the source filename/known instruction `follow_the_white_rabbit`;
- the creator's same-day `R=18, A=1, B=2 ... 1812 bit` rebus, which spells
  `RAB` + `BIT`.

Therefore “take the row tail” can be selected from the artifact's literal
rabbit anatomy: use the right-hand end of each left-to-right matrix row. This
does not reuse the later Architect “last words” clue.

With that selector, the strict grammar is:

```
row-list:        [5,7,4]
rabbit tail:     rightmost pair -> (7,4)
matrix address:  standard (row,column), zero-based
sum/list:        sum(row)=16, len(row)=3
concatenation:   16||3=163, following the creator's 18||1||2 precedent
```

Both address channels identify the same FEFE cell. The second row remains a
negative control. This materially strengthens the semantic justification for
the strict `12/720 = 0.016667` result.

It does not turn that number into a formal discovery p-value. The rabbit-tail
interpretation was recognized after the numerical match, project-wide
multiple testing remains large, and `len(row)` is natural but not explicitly
spelled out by the creator. The rule is upgraded from an unsupported tail
choice to the **best-supported matrix-to-FEFE addressing explanation**, not to
a solved downstream operation.

**Verdict:** the matrix likely serves as a redundant address/checksum for the
already-located FEFE prime-zero cell:

```
matrix row [5,7,4]
 -> rabbit-tail coordinate (7,4)
 -> sum||length index 163
 -> FEFE / character 21 / bit 4 / zero
```

The addressing question is provisionally answered. The next unresolved
question is what the puzzle expects after reaching that marked zero cell.

## Phase 41 -- bounded FEFE zero-operation audit (2026-07-25)

Added `tools/gsmg/fefe_zero_operation_audit.py`, importing the asserted image
reconstruction rather than independently changing any address convention. It
freezes four literal interpretations of “zeroing” the already-addressed
character:

```
set marked bit to zero:             gsmg.io/theseedisplanted  (no change)
delete marked character:            gsmg.io/theseedisplated
replace marked character with "0":  gsmg.io/theseedispla0ted
replace marked character with NUL:  gsmg.io/theseedispla\x00ted
```

The addressed bit is already zero, so setting that bit to zero is an
information-free no-op. Literal-zero and NUL replacement do not form a
language instruction. Deleting the preselected character `n`, however,
changes:

```
the seed is planted
        zero n
the seed is plated
```

The anomalous pixel independently supplies `FEFEFE`, exactly three `FE`
bytes—one per RGB channel. Case-normalized `Fe` is the chemical symbol for
iron, so the two fixed observations form a compact rebus:

```
zero/delete the addressed n + FEFEFE
 -> the seed is plated + Fe
 -> the seed is Fe-plated
```

This is descriptive calibration, not a discovery p-value. The marked
character was selected before looking at deletion results, and its deletion
gives the uniquely **thematically coherent** result `theseedisplated`: deleting
the following `t` also yields the dictionary-valid `theseedisplaned`, but
“planed” has no identified connection to `FE`, iron, or plating. Interpreting
a hex byte as an element symbol was recognized after the fact, and no
creator-authored metal, iron, or plating instruction was found. Generic
occurrences in mined chat, screenplay, and book corpora do not supply
independent support.

A second bounded cross-phase reading also exists: restoring the removed `N`
to each `FE` channel gives `FEN FEN FEN`, and FEN is an authenticated earlier
chess artifact. This is weaker because broadcasting one `N` into all three
channels is an extra operation with no creator instruction. It is recorded
as a possible checksum, not used to select the deletion or justify a sweep.

Direct routes/hashes for `theseedisplated`, literal-zero, deletion, and bit
variants were already negative in Phase 37. They are not rerun, and this
semantic result does not justify AES escalation.

**Verdict:** deletion is the only bounded zeroing interpretation that produces
a coherent instruction, and `FEFEFE` makes **“the seed is Fe-plated”** the
leading explanation of what consumes the addressed `n`. This provisionally
resolves the local operation, but not what physical or cryptographic “plated
seed” object the puzzle intends. Any next branch must identify that object
from existing creator-authored or on-chain evidence; it must not expand into
an open-ended metal, element, or seed-product wordlist.

## Phase 42 -- bounded plated-seed referent audit (2026-07-25)

Checked whether “the seed is Fe-plated” identifies a physical/on-chain object
or a tighter textual operation.

The creator-only archive supplies two important constraints:

- on 2023-11-24 the creator says internet access is no longer required;
- on 2024-01-26 the expected prize is a “Regular Bitcoin Private key.”

The same 411-message creator corpus contains no `seed`, `planted`, `plate`,
`plated`, `iron`, `metal`, `steel`, engraving, stamping, backup, or storage
instruction relevant to this branch. This weighs against selecting a branded
metal seed-backup product or an external catalog entry. The two old full-chat
occurrences of `seedisplatedw` / `theseedisplated` occur in untrusted,
disputed community claims and read as mistypings of `seedisplanted`; they are
not creator corroboration.

The authenticated blockchain candidate inventory also provides no structural
referent. Of its 22 exact values, only the recipient HASH160 contains one
internal lowercase `fe` substring:

```
4bc468447fe1b048ad030a2f9a125478eabc4ed6
         ^^
```

It is neither repeated nor aligned with an authored boundary, and promoting
it would be arbitrary transaction-field mining of the kind Phase 28
explicitly excluded.

The remaining bounded interpretation treats `SEED` as the literal object and
`FE` as its exterior coating. Four forms were frozen before decryption in
`wordlists/gsmg/fefe_plated_seed_candidates.txt`:

```
FESEEDFE                 minimal symmetric coating
FESEEDFEFE               all three FE channels split 1+2
FEFESEEDFE               all three FE channels split 2+1
FEFEFESEEDFEFEFE         complete RGB unit on both sides
```

No metal synonyms, atomic values, product names, arbitrary affixes, or
blockchain fields were added. Focused results against all three authenticated
blobs plus quarantined `urlblob`:

```
extended CBC: 72 generated keystrings, 0 hits
AES Key Wrap: 72 generated keystrings, 0 unwraps
direct key:   8 case-normalized text forms -> SHA-256 private scalars,
              16 compressed/uncompressed P2PKH addresses, 0 matches to the
              prize or repeated-halving address
```

The four candidates are now part of the curated recheck inventory so future
cipher-oracle changes will cover them without regenerating this hypothesis.

**Verdict:** no authenticated evidence identifies a physical “seed plate,”
and the complete bounded literal-coating family is negative. Do not add seed
plate brands, alloys, element tables, or transaction numerology. The
`planted -> plated` / `FEFEFE -> Fe` result remains a strong local semantic
checksum for the zeroed `n`, but currently does not supply the final private
key or blob passphrase. Further work should return to a creator-specified
unresolved edge rather than elaborate this rebus.

## Phase 43 -- FAED ciphertext-only monoalphabetic recovery under (h,e), corrected (2026-07-25)

Motivation: the `BUT`-keyed reordering of `HYE` into `HEY` (Phase 34) argues
for the ordered escape pair `(h,e)`, and FAED (570 raw symbols) segments
under `(h,e)` into 469 codes touching all 25 of 25 code types -- a far
richer regime for `quadgram_solver.py`'s ciphertext-only hill-climb than
`DBBI` (63 codes / 19 of 25 types), which the existing
`checkerboard_recovery_calibration.py` had already shown is underpowered.

This phase was substantially revised after an external review caught two
real methodological errors in the first pass, three reporting imprecisions,
and an unimplemented piece of the approved plan. Each was independently
re-verified (not taken on trust) before correcting; one review claim was
checked and found to already be handled correctly. Corrected version below.

**Structural mismatch (escape-density/top-fraction), corrected numbers.**
Building profile-matched synthetic controls the way `checkerboard_recovery_
calibration.py` already does for DBBI (exact match to a target top-code sum)
requires a real-English window whose top-7 letter-counts sum to FAED's
actual top-code total:

```
FAED under (h,e): 368 of 469 codes (78.46%) in the 7 "top" single-symbol slots
DBBI under {b,e}:  35 of  63 codes (55.6%) in the 7 "top" single-symbol slots
Phase 3.2.2's one validated real decode: ~53% top / 47% escape (70/149 escape density)
```

An **exhaustive** scan (corrected from an initial 500-window/one-corpus
pilot that underestimated this) of every non-overlapping 469-char window
across all three corpora, keeping only windows with exactly 25 distinct
letters, gives real maxima of 66.7% (matrix, 784 eligible windows), 64.6%
(book, 32 windows), 70.1% (chat, 2017 windows) -- **64.6-70.1%, not the
56-60% first reported.** Still well short of FAED's 78.46% -- no subset of
7 letters from real English prose at this length reaches it, confirmed
exhaustively rather than assumed. Of the 36 possible escape pairs for FAED,
**29 segment cleanly (7 produce a dangling final escape and were correctly
excluded, not "all 36" as first written)**; every one of those 29 falls
between 69.3% and 82.2% top-fraction.

**Correction: "none of the 29 valid pairs are reachable by real prose" was
overstated.** `{g,i}` (436 codes, target top-sum 302, 69.27%) was re-checked
at its *own* matched window length (436, not FAED's 469) rather than reused
from the 469-length scan -- windows need to be the right length for the
pair being tested, since achievable concentration is length-dependent. At
436 characters, the chat corpus has 7 of 2029 eligible windows that reach or
exceed 302 (max 322, 73.85%) -- rare (0.34%) but genuinely real-English-
reachable, not impossible. `(h,e)` remains far outside reach at its own
matched length (469, already the scan above) under any corpus checked. The
escape-density argument therefore rules out `(h,e)` specifically and most
but not all of the 29 valid pairs, not the blanket "none of them" first
claimed -- `{g,i}` (already separately tested and negative via chain-
addition/autokey, Phase 16/38) is the one clear exception.

By this project's own escape-*character*-density heuristic (target 47%,
`doc/GSMG_PUZZLE.md:452-458`, itself a raw-character-frequency metric,
confirmed from source -- not the same thing as the 21.54% escape-*code*-
fraction figure, which is a related but distinct statistic): `{b,e}`
matches DBBI almost exactly (47.3%); FAED's best pair `{g,i}` only reaches
31.9%; `(h,e)` specifically is one of the weaker fits at 22.28%. This
structural evidence against `(h,e)` stands on its own, independent of any
hill-climb.

**What an exact profile-matched calibration would need, and why it wasn't
built that way.** The review correctly noted that an *exact* match to
FAED's 78.46% top-fraction is not the only way to calibrate -- an
approximate-match control (same code/type count, relaxed top-sum) is
buildable and would still be informative. **An earlier version of this
section additionally claimed that a more concentrated true profile "should
only make ciphertext-only recovery easier, not harder," making an
approximate-match calibration a conservative lower bound -- a second review
round correctly flagged this as unsupported and it is retracted, not just
softened.** Greater concentration in the 7 top slots means the 18 escape
slots share a proportionally smaller remainder, which could make those
specific mappings *harder* to pin down (less data per rare code = more
statistical noise), not easier -- the net direction isn't obvious and
wasn't checked. It wasn't built here because a more direct check was
available and was run instead (next section): rather than asking "does the
solver have power on English text with a similar-but-not-identical
profile," directly ask "does FAED's own real symbol arrangement score
better than the same symbols scrambled, under the identical search." That
sidesteps the profile-matching (and the easier/harder) question entirely.

**Real hill-climb + a proper same-budget, token-preserving null control.**
`tools/gsmg/faed_monoalphabetic_sweep.py` (new; thin driver reusing
`quadgram_solver.py`'s `hillclimb`/`decode_with_key`/`score`/
`run_all_variants_parallel`, generalized by a `base_pair` parameter -- see
bugs below). 4 variants (`(h,e)`/`(e,h)` x `top_first`/`escapes_first`),
4000 iters x 200 restarts each (800 restarts):

```
real FAED:        best=-2544.1  (-5.4244/char)  variant=(h,e,top_first)
```

**The first version of this phase compared that score to a real-English
sample and to one *unoptimized* shuffle of the same letters -- an
apples-to-oranges comparison the review correctly rejected.** A second
version compared it to 3 draws that shuffled FAED's raw a-i *symbols*
before re-segmenting -- the same class of bug this project's own Phase 19
(dual-quinary) had already flagged once: shuffling pre-segmentation symbols
changes the segmentation itself, so those null draws solved a
different-shaped problem than the real ciphertext (verified: 474/24,
472/25, and one outright dangling-escape failure across the 3 draws --
not even the same code count/type profile as the real 469/25, let alone a
random-within-cipher rearrangement of it). A further review round caught
this and it was rejected in turn.

The corrected null (`tools/gsmg/faed_token_null_check.py`) segments FAED
into its real 469 codes under `(h,e)` **once**, then shuffles the CODE LIST
itself (not raw symbols) and rejoins by concatenation -- since every code
is self-terminating under `(h,e)`'s segmentation rule, concatenating codes
in any order re-segments to the exact same 469/25 multiset by construction
(checked, not assumed: verified for all 100 draws actually run). The
canonical variant `(h,e,top_first)` is used for both the real run and every
null trial (proven substitution-isomorphic to the other 3, so this loses no
coverage), at the real run's full 800-restart/4000-iter budget, with the
optimizer's own random-restart seed schedule held **fixed** across every
trial -- only the shuffle (which permutation of the 469 codes a given trial
searches) varies. Without this seed symmetry a null trial's score reflects
two combined sources of variance (shuffle + optimizer luck) while the real
run reflects only one, folding optimizer variance asymmetrically into the
resulting p-value -- a fourth review round caught this too, independently
verified, and fixed.

100 trials (resolvable p floor `1/101 = 0.00990`), run via
`python3 tools/gsmg/faed_token_null_check.py 100 800 4000 16`:

```
real FAED:        best=-2544.1  (-5.4244/char)
null (n=100):      min=-2578.5  max=-2490.5  median=-2539.0
null >= real:      63/100
empirical p = (63+1)/(100+1) = 0.63366
```

FAED's real score sits almost exactly at the shuffled-null median (real
-2544.1 vs. null median -2539.0 -- the real ciphertext scores *worse*, not
better) and 63% of independent code-shuffles score at least as well. This
is about as unambiguous a negative as an empirical p-value gets; the
`n=100` resolution floor (`p_min~0.0099`) is irrelevant here since the
result isn't anywhere near that floor -- more trials would sharpen the
estimate but couldn't plausibly flip the qualitative conclusion.

One more real bug, caught and fixed after this run completed (does not
affect its validity): `faed_token_null_check.py`'s checkpoint file existed
but was empty (0 bytes) when this 100-trial run started, and
`append_checkpoint`'s `is_new = not path.exists()` check treats an
existing-but-empty file as "not new," so no header record was ever written
-- silently defeating the config-fingerprint protection (Phase 43's own
prior review round 3 fix) for any *future* resume against that file. This
run's own 100 records are unaffected (verified: all 100 trials used one
consistent config throughout, contiguous shuffle seeds `20260726..20260825`
matching `seed_base + i` with no gaps or foreign seeds, and
`load_checkpoint`'s separate `if not lines: return done` path correctly
treated the empty file as "nothing done yet" -- there was nothing
mismatched to protect against on this specific run). Fixed to
`not path.exists() or path.stat().st_size == 0`, with a regression test
added to `self_test()`.

**The "no separation between the 4 variants" claim in the first version of
this phase was wrong, not just weak, and is retracted.** Traced through
`cb_common.build_board_9ary` directly: segmentation of the raw ciphertext
into codes depends only on the *set* `{e1,e2}` (membership test, symmetric
in order), and swapping `e1`/`e2` order or `topology` is exactly a
relabeling of which of the 25 board positions each code maps to. Since the
hill-climb's 25-letter permutation search already explores every relabeling
independently for each variant, the four variants are provably
**substitution-isomorphic** -- for any key achievable under one variant,
swapping two contiguous 9-symbol blocks (or a 7/9/9 block) of the same
key26 reproduces the identical decode under another variant. The four
variants converging to the same score is therefore a mathematical necessity
of the search design, not empirical evidence of anything. It does not
invalidate the shuffled-null comparison above (which compares real vs.
scrambled *ciphertext* under the same procedure, not variant-to-variant),
but it is removed as an independent line of evidence.

**Bugs caught and fixed, not just profile-config changes:**

1. `quadgram_solver.py`'s `run_all_variants`/`run_all_variants_parallel`
   hardcoded the `("b","e")` symbol pair internally. Generalized to a
   `base_pair` parameter (default `("b","e")`, so DBBI's existing behavior
   is unchanged) -- without this, `checkerboard_recovery_calibration.py
   --target faed` would have silently searched the wrong 9-ary symbols.
2. `checkerboard_recovery_calibration.py`'s `find_top_subset` had
   `target_sum=TARGET_TOP_SUM` as a default argument -- Python binds default
   values at function-definition time, so this default was permanently
   frozen at DBBI's 35 regardless of which profile `apply_profile()` later
   activated. Fixed to resolve `TARGET_TOP_SUM` inside the function body at
   call time. Also fixed a hardcoded `assert ... == 6` in
   `build_profile_matched_board` (was `26 - 19 - 1`, DBBI-specific) to
   `26 - TARGET_N_TYPES - 1`.
3. The same class of bug, a third time, in this session's own new driver
   script: `faed_monoalphabetic_sweep.py`'s parallel-workers path called
   `run_all_variants_parallel` without passing `base_pair`, so the first
   real run silently searched `b`/`e` against FAED data for 45 CPU-minutes
   before being caught by inspecting the winning variant labels, not by any
   automated check. Fixed; a self-test assertion was added that specifically
   checks the parallel path's variant set (the serial path alone would never
   catch this class of bug, since it doesn't call `run_all_variants_parallel`).
4. **The AES-escalation path (never actually executed -- no run crossed the
   escalation gate) did not match the approved plan**: it called
   `keystr_forms()` directly on the raw hill-climb decode without
   `answer_forms()` first (missing case-variant coverage), and only tested
   `EXTENDED_CIPHER_VARIANTS`, never the original `KDF_VARIANTS`
   (`kdf_variants=None`) -- `cb_common.py`'s own comment states the two are
   deliberately disjoint, not a superset relationship. Both fixed. This had
   zero effect on any reported result since escalation never ran, but is a
   real gap against the approved plan and is fixed for correctness going
   forward.
5. **Checked and found already correct**: the calibration cache key
   (`cache_path_for`) omits escape-pair/profile identity. Verified this
   isn't a practical collision risk -- ciphertext content (and length: 91 vs.
   570 chars) differs across profiles by construction, so no dbbi/faed cache
   collision is reachable -- and changing it would have invalidated the
   ~24 real DBBI trials already cached. Left as-is, now with an explicit
   comment recording this reasoning.

`checkerboard_recovery_calibration.py --target dbbi` was smoke-tested after
the refactor (tiny budget, real end-to-end run, no assertion failures) to
confirm the profile-parameterization didn't regress DBBI's existing path;
`calibration_cache/`'s ~24 real DBBI trial files were left untouched.

**Verdict:** **No evidence that FAED under the fixed escape pair `(h,e)` is
a single-layer monoalphabetic English substitution.** Two independent lines
of evidence agree: the escape-density/top-fraction structural mismatch
(FAED's 78.46% top-fraction under `(h,e)` is unreachable by real English at
its own matched window length, in every corpus checked) and a properly
token-preserving, seed-symmetric, 100-trial same-budget null comparison
(the real ciphertext scores at the shuffled-null median, `p=0.634`, nowhere
close to exceptional). Not escalated to AES -- no top-ranked decode is
readable, and the real score doesn't clear the null.

This verdict is deliberately narrow in scope, not a blanket close-out of
FAED: it rules out `(h,e)` specifically as a plain checkerboard
substitution, not transposition, multi-layer, digraphic, non-prose
plaintext, or any other escape pair. The escape-density structural argument
does generalize somewhat -- 28 of FAED's 29 cleanly-segmenting pairs fall
outside real English's reachable top-fraction range at their own matched
lengths, `{g,i}` (69.27%, separately tested and independently negative via
chain-addition/autokey, Phase 16/38) being the one confirmed exception --
but only `(h,e)` has now been tested by both the structural argument *and*
a full ciphertext-only hill-climb plus rigorous null. Do not re-run this
specific hill-climb hoping for a different result without new evidence
changing the escape-pair hypothesis; a different cipher-layer hypothesis
for FAED would need its own dedicated test, not a rerun of this one.

## Phase 44 -- corrected “in front of your eyes” transition audit (2026-07-25)

Audited the raw creator/community transcript and archived page mechanics
instead of extending the speculative `B <-> H` rail. The first version of
this phase made a serious attribution error by starting its bounded transcript
window at 20:27 and conflating two separate exchanges:

1. At 20:22 Denis asks whether “in front of your eyes” recommends
   *Looking Forward*. The creator replies, “Maybe, Cartman's quote about
   chatroulette fits too,” followed by `🤐`.
2. At 20:27 the creator points at gnomad; gnomad repeats only the
   “in front of your eyes” phrase; the creator replies `Bingo`.

Gnomad never names the book. `Bingo` directly confirms the phrase matters,
not the community's *Looking Forward* expansion. The original headline
“creator-confirmed Looking Forward” is retracted.

The relevant book discussion, under “Open Eyes and Open Minds,” concerns
polar-opposite language, black/white judgments, shades between extremes, and
thinking in degrees. This aligns with the already-verified first artifact:
black/white structure, blue/yellow overlays whose archived RGB hues are
`179.229036°` apart, and the unique `#FEFEFE` pixel differing from white by
exactly `(1,1,1)`. This is a thematic fit from a creator-hedged community
lead, not primary confirmation. The blue/yellow values are standard MS Paint
colors, so their near-opposition is corroborative rather than a new number
to mine.

`tools/gsmg/yin_yang_transition_audit.py` makes the evidence reproducible. It
asserts the exact transcript messages/order, imports the existing first-piece
reconstruction, and parses the archived HTML. The site exposes one hidden POST
form at `theseedisplanted.html`, but the later Phase 2/3 and
SalPhaseIon/Cosmic pages are static ciphertext textareas with no form or input.
There is no demonstrated web transition contract after the first form, so
route/form brute force is not justified.

As a deliberately bounded sanity check,
`wordlists/gsmg/looking_forward_candidates.txt` initially contained nine
exact title/passage phrases. The next-edge review noticed a stronger
cover-level rebus that had never entered any project wordlist: coauthor
**Kenneth S. Keyes, Jr.** is literally printed in front of the reader, and
`Keyes` sounds like “keys.” Added only exact printed byline forms and the
single homophone `keys`, not free combinations.
`yin_yang_transition_audit.py --oracle` then generated 264 unique
raw/SHA-256/double-SHA-256 keystrings from 19 candidates and tested all four
tracked blobs under legacy CBC, opt-in extended CBC, and AES Key Wrap:
**0 hits**.
This is not promoted as a password hypothesis; the expected negative does not
weaken the semantic pointer.

**Corrected verdict:** neither *Looking Forward* nor `H|YE|BUT` is
creator-confirmed. The rails are a reproducible algebraic construction on
authenticated puzzle output; the book is a thematically fitting community
suggestion with a hedged creator response. Keep both unpromoted. Only “in
front of your eyes” is directly confirmed by `Bingo`. Do not use either
interpretation to license downstream transforms without independent artifact
evidence.

### Phase 44 continuation -- bounded next-edge closure

Extracted the exact *Looking Forward* PDF locally (SHA-256
`59c9d888a0c6f5f45cfe6ef874b88d9f29b520f396ce613d93b241ed79996e85`).
PDF page 37's “Open Eyes and Open Minds” passage is more specific than the
initial summary: it says apparently identical things reveal differences
under closer inspection, immediately before discussing polar opposites,
degrees, and black/white labels. This strongly explains how the lone
`#FEFEFE` cell could be noticed among nominally white cells. This remains a
thematic mapping from an unconfirmed book lead, not creator evidence.

External review correctly noted that the PDF digest/page-content claim was
not reproducible from repository code. Added
`tools/gsmg/looking_forward_source_audit.py`: with `--download` it fetches
the frozen source URL, verifies the exact SHA-256, extracts all pages through
`pdftotext`, and asserts six short page-37 anchors covering the stated
difference/degrees/opposites/black-white content. Re-running it against the
fetched source verifies 122 extracted pages and all anchors. The source fact
is now reproducible; its puzzle relevance remains explicitly unconfirmed.

Built `tools/gsmg/yin_yang_next_edge_audit.py` to freeze the small operation
family suggested by “Looking Forward” and the creator's remaining “very last
step is a true give away” wording. Results:

- true/false applied to the 24 colored last bits reproduces the already-known
  `F73D92`/`574061` dual result;
- selecting source characters at those true/false LSB positions gives
  `gsmgio/eseeisae` / `.thdplntd`;
- reading from the exact FEFE bit or the following bit produces misaligned
  non-text bytes;
- advancing to the next byte yields only the existing suffix `ted`.

No interpretation supplies a new transition. This closes literal
forward-from-FEFE and last/true selection without expanding into arbitrary
transforms.

**Correction:** the 2021-12-26 creator clue says “some characters” need to
be zeroed out. The single FEFE bit is a genuine zero-valued marker but cannot
fully explain a plural instruction. The locator remains solved; the larger
prime-selected character-zeroing operation remains open and is now the
strongest creator-grounded next edge.

The historical `door_prime_passport_probe.py` result does **not** close this
revised edge. It maps raw `a-i` symbols into decimal digits, overwrites
selected raw positions with decimal `0`, then decodes using the old
Phase-3.2 28-symbol alphabet and `(1,4)` escapes. That test predates the
native 9-symbol model and target-specific `{b,e}` / `{g,i}` / `{h,e}`
segmentation. The corrected next experiment must define zeroing on either
native raw symbols or complete native codes and put the entire selector/
transform choice inside a profile-preserving null; re-running the old script
would not answer the current question.

## Phase 45 -- native prime/character-zeroing sweep, corrected (2026-07-25)

Built the corrected next experiment named at the end of Phase 44:
`tools/gsmg/native_prime_zeroing_sweep.py` tests DBBI under `{b,e}` and FAED
under both `{g,i}` and `{h,e}`, retaining only raw-symbol or complete-code
units at prime-numbered positions (0- or 1-based) or their complement,
across both escape orders, both board topologies, and 33 deduped
clue-motivated keyword alphabets (`CORE_ALPHABET_SEEDS` x tail-fill x
merge-direction, same list `matrixsum_permutation_sweep.py` uses). "Zeroed
out" is interpreted as masked/removed from the retained stream, not
replaced by native `a` (an ordinary decodable code, not an absence marker)
-- this tests one precise scope, not every possible zeroing interpretation.
Every candidate is scored with the existing quadgram scorer and gated by a
two-stage, branch-matched shuffle null: raw-unit family members are compared
against a raw-symbol-shuffle null, code-unit family members against a
complete-code-shuffle null, both drawn per trial and combined with the real
family via the same max-statistic (500-trial Stage-1 screen at `p<0.02`,
independent 5,000-trial Stage-2 confirmation at `p<0.005`) before any
AES/AES-Key-Wrap escalation.

**Five real bugs found and fixed before any real run was trusted**, three
self-caught via the synthetic-control self-test, two caught by external
review and independently verified before being applied:

1. `encoded_prefix_for_raw_slots()` built raw-symbol controls by walking a
   single fixed book sample and requiring the encoded length to land exactly
   on the target slot count; since letters encode to 1 or 2 symbols, the
   greedy walk could jump straight past the target and simply gave up. Caught
   immediately: `--self-test` crashed with `AssertionError: could not build
   exact 24-raw-symbol control` on the very first control case. Fixed to be
   exact by construction: walk normally, and if the only remaining gap is
   exactly 1 symbol, close it with a guaranteed single-symbol top-row letter
   instead of the natural next book character (`build_board_9ary()` always
   assigns exactly 7 top-row codes for any alphabet/pair/topology, so a
   closing letter always exists).
2. Added an explicit `assert len(encoded_units) == len(retained_indices)`
   immediately before the `zip()` that plants known codes into the control
   stream, so any future weakening of either branch's length guarantee fails
   loudly instead of silently leaving prime-indexed positions un-filled.
3. The self-test originally only required the known plaintext to appear
   *somewhere* in the candidate family (`any(decoded == plaintext ...)`),
   weaker than the max-statistic the real run and the shuffle gate actually
   use. Strengthened to require **top-1** recovery (`ranked[0][1] ==
   plaintext`) after sorting the real candidate family by score -- all 24
   controls (3 pairs x 2 units x 2 index-bases x 2 polarities) pass at this
   stronger bar.
4. External review caught that `unique_top_candidates()` sorted raw
   `(score, decoded, metadata_dict)` tuples with `sorted(..., reverse=True)`:
   on a score+decode tie (routine here, given 33 alphabets x 2 escape orders
   x 2 topologies), Python falls through to comparing the metadata `dict`s,
   which aren't orderable. Independently reproduced: calling
   `unique_top_candidates()` directly raised `TypeError: '<' not supported
   between instances of 'dict' and 'dict'` for *both* targets. Fixed by
   sorting on score alone (`key=lambda item: item[0]`); reran directly
   post-fix and confirmed 20 unique candidates return cleanly for both.
5. External review also caught that `SEED_BASE_1 = 202607251` and
   `SEED_BASE_2 = 202607252` are one apart: at the default trial counts,
   Stage 1's seed range `[202607251, 202607750]` and Stage 2's
   `[202607252, 202612251]` overlap in 499 of Stage 1's 500 seeds --
   `random.Random(seed)` is deterministic, so Stage 2 would have silently
   rerun 499 of Stage 1's exact null trials rather than drawing an
   independent sample. Independently confirmed via direct set intersection.
   Fixed by moving `SEED_BASE_2` to `202607252000` (~202.4 billion seeds of
   headroom) and adding two guards: a `seed_ranges_overlap()` runtime check
   wired into `run_target()` ahead of Stage 2, evaluated against the actual
   `--trials-1`/`--trials-2` values so a future CLI override can't silently
   collide, plus a fixed-count self-test regression check for the defaults.

**Result: clean negative for both targets, both stopped at Stage 1.**

```
[stage 1] dbbi: real=-5.899453 null_mean=-5.445673 null_max=-4.483568 p=0.956088 (478/500)
[stage 1] faed: real=-6.049761 null_mean=-5.893017 null_max=-5.403997 p=0.898204 (449/500)
```

Neither target's real best score is remotely exceptional against its own
branch-matched null (`p=0.956` / `p=0.898`, both far above the `p<0.02`
Stage-1 threshold) -- most shuffled nulls score *better* than the real
streams. Neither best decode is readable English (DBBI:
`KKBADINTHHHRRYWEA`; FAED: `UTOIANACTEAATTETIPRTSQTRFACBOCIATERTXFWHATE...`).
The pipeline correctly stopped after Stage 1 for both targets; Stage 2 and
AES/Key-Wrap escalation never ran (nothing to escalate). Full run:
`python3 tools/gsmg/native_prime_zeroing_sweep.py --target both --workers 16`,
25.7s wall clock.

**Scope of this negative:** it covers masking/removal of prime-indexed (or
complementary) raw-symbol or complete-code positions, under `{b,e}`/`{g,i}`/
`{h,e}`, both escape orders, both topologies, and this project's existing
33 clue-motivated alphabets -- not replacement with native `a`, and not any
zeroing interpretation outside that family. The plural "some characters...
zeroed out" clue (Phase 44 continuation) remains only partially addressed:
the FEFE bit is a real singular zero-marker, and this phase closes the most
natural "prime-position mask/remove" reading of the plural instruction as a
plain checkerboard operation, but does not rule out zeroing combined with a
different underlying cipher layer, a non-prime selection rule, or a
non-masking transform.

## Phase 46 -- exact uniform-subset base-rate audit of Denis Golovkin's "yang" extraction (2026-07-25)

A community lead (`chat_transcript.txt`, lines 168547-168675) claimed that
applying "specific prime indexes" to the known 91-character plaintext
`incaseyoumanagetocrackthistheprivatekeysbelongtohalfandbetterhalfand
theyalsoneedfundstolive` extracts ~30-31 characters containing "ying yang"
and "salvation" -- directly targeting the creator-confirmed "in front of
your eyes" phrase. Denis Golovkin's concrete posted extraction (20:39:06
UTC-05:00) is `ncsyangcahiriasogaleafayanestve` (31 chars). His clearest
method description is a later message (20:57:30, lines 168663-168675):
*"We took 'yellow blue primes' of dbbi to filter indexes that match B or BE
chars vs indexes that don't match... And once we apply chosen indexes to
these last words, we see that selected 31 (or 30) characters includes a
'ying yang'."*

**What's real vs. not, checked directly against the exact posted string:**
`"yang"` **is** a literal substring. `"ying"` and `"salvation"` are **not**
-- neither appears anywhere in it, which already contradicts Denis's own
20:57:30 summary claim that the selection "includes a 'ying yang'." His
20:48:31 follow-up explains the discrepancy: he posts sentences explicitly
labeled "**Here are some manually crafted:**" -- hand-built anagram
sentences from the same 31-letter multiset (e.g. "reach a safe ying yang
salvation case"). So "ying"/"salvation" are anagram-letter-subset claims,
not found substrings -- far weaker and far more coincidence-prone. At
20:41:57 Denis says himself: *"Might be a phrase anagram. I've
brute-forced few trillions of anagrams, but didn't find em to be the key to
proceed."* This is a large but **far from exhaustive** search: the
31-letter multiset has `31!/(7!3!3!3!2!2!2!2!) ~= 4.72e26` distinct
anagrams (computed exactly), so "a few trillion" covers roughly `10^-14` of
that space.

**Rule reconstruction, attempted and bounded-negative.** The "guide to
yellow-blue-primes" image Denis references (20:36:01: *"Notice that 'B' for
blue and both 'BE' for yellow participate"*) is missing from this text
transcript -- no attachment marker appears near that message, unlike other
points in the transcript where attachments *are* referenced by filename.
`tools/gsmg/denis_prime_extraction_audit.py`'s `RULE_FAMILY` enumerates 44
named selection rules a person could plausibly build from "B for blue, BE
for yellow" x primality against the real `DBBI` string -- `{0,1}`-based
indexing x `{b, be, e}`-membership x
`{AND, OR, XOR, filter-then-take-primes-of-the-filtered-subsequence}` x
prime/nonprime polarity. All 44 produce distinct outputs (44/44 unique, no
redundant formulations collapsing the family) but **none reproduce Denis's
exact 31-character string, and none even reproduce the "yang" substring hit
on the real data at all**. The rule was not recovered within this declared
44-rule family -- a bounded negative about that specific family, not proof
no reconstruction exists (the missing image, or a differently parameterized
family, might still work).

**Recovered position masks.** Since Denis's string is an *exact* target,
the set of source positions that could produce it is directly countable:
`recover_position_masks()` (DP + backtracking) finds precisely **4** sets
of 31 increasing source positions whose characters reproduce
`"ncsyangcahiriasogaleafayanestve"` exactly. All 4 agree on 29 of 31
positions and differ only at two independent binary choices, both at
locally-repeated letter runs in the source: 1-based position **57 vs. 60**,
and **78 vs. 79**. This narrows what "the exact source string, mask,
indexing convention" could be far more than the 44-rule search space,
despite the missing image, and is recorded here for any future
reconstruction attempt.

**Exact uniform-subset base rates** (dynamic programming over a
KMP-automaton state x source position x subset-size-used x found-flag --
not sampled, not a p-value for Denis's actual non-uniform rule, only a
calibration point: how common is a "yang"/"ying" hit among *all*
equally-likely order-preserving k-subsets of this specific source):

```
target=yang, k=31 (PRIMARY, the one mechanically verified hit): rate=0.002579127
target=yang, k=30 (secondary):                                  rate=0.002403975
target=ying, k=31 (counterfactual only -- never in the real extraction): rate=2.323839e-10
target=ying, k=30 (counterfactual only):                                 rate=4.938532e-10
```

At the primary rate, `ceil(ln(0.5)/ln(1-0.002579127)) = 269` independent
order-preserving 31-subsets would give a 50% chance of at least one "yang"
hit, and `892` would give 90%. **This is not a claim about how many
extraction rules Denis actually tried** -- that count is genuinely unknown,
and his "trillions of anagrams" statement is about post-extraction
anagram-sentence search, not about how many candidate 31-position subsets
were tried to land on this one. These attempt-counts are reported only as
"this is how easily a hit like this happens if many subsets were tried",
not as a claim about what actually happened.

**Verdict:** a bounded base-rate audit of a community-derived lead, not
evidence for or against the creator's intended mechanism either way, and
not a closed door on reconstruction via a rule outside the tested 44-member
family. `"yang"` is a real, low-but-not-negligible-probability
(~0.26%) literal hit in one specific 31-of-91 order-preserving selection of
already-public plaintext; `"ying"` and `"salvation"` are not literal hits
at all, only anagram-letter-subset material that the lead's own author
searched roughly `10^-14` of and found nothing conclusive in. No AES or
further cipher escalation is justified by this -- there is no recovered
plaintext or key candidate here, only a base-rate question about one
already-known public string.

## Phase 47 -- first-piece color sequence / Denis-mask convergence audit (2026-07-25)

**Superseded by Phase 48:** this phase omitted FEFE from the ordered event
stream and then removed color object 21, creating an artificial distance-2
swap. Inserting FEFE at its real spiral position before color object 21
reproduces the compatible mask exactly. The calculations below remain
reproducible for the older, incorrect model but are not the current verdict.

Phase 46 recovered exactly four possible source-position masks for Denis
Golovkin's posted 31-character extraction, but did not reconstruct his
selection rule. `tools/gsmg/yellow_blue_mask_convergence_audit.py` checks a
new intersection with the independently verified first-piece color artifact,
using only operations already fixed before this comparison:

1. `first_piece_color_reconstruction.py` supplies the exact 24-object sequence
   `BBBBYBBBYYBBBBYBBYYBYYBY` (`15 B`, `9 Y`);
2. FEFE addresses character/object 21, which is yellow and contains the marked
   zero bit;
3. Denis's own transcript wording supplies `blue -> B`, `yellow -> BE`;
4. Phase 46 supplies all four possible masks, with family selection retained
   inside every comparison.

Removing the already-addressed yellow object 21 leaves:

```
BBBBYBBBYYBBBBYBBYYBYBY       (15 B, 8 Y)
```

Encoding `B -> b`, `Y -> be` gives a 31-symbol stream:

```
bbbbbebbbbebebbbbbebbbebebbebbe
```

Exactly **one** of the four recovered masks selects only `b/e` symbols from
the real DBBI string. Its composition is also exactly `23 b + 8 e`, matching
the color encoding's forced composition:

```
mask DBBI pattern: bbbbbebbbbebebbbbbebbbebebbbebe
decoded as colors: BBBBYBBBYYBBBBYBBYYBBYY
```

The two 31-symbol streams have Hamming distance **2**. At the color-token
level, they differ only by exchanging adjacent reduced positions 21 and 22:

```
first piece after object-21 removal: ...YYBYBY
compatible recovered mask:          ...YYBBYY
                                         ^^
```

Equivalently, swapping original color objects 22 (`Y`) and 23 (`B`) makes
the streams match exactly. This adjacent swap was recognized only after the
comparison and no creator-authored ordering operation currently supports it.
It is therefore an unresolved discrepancy, not an applied transform.

**Exact conditioned calibration.** To avoid treating the compatible mask as
preselected, the statistic is the minimum Hamming distance across all four
recovered masks. The null conditions on the fixed facts required to produce
a 31-symbol stream: object 21 is the addressed yellow and is removed, leaving
all `C(23,8) = 490,314` arrangements of `15 B + 8 Y`. Every arrangement is
encoded with the same `B -> b`, `Y -> be` mapping and compared against the
same four-mask family:

```
minimum-distance distribution:
  0:       1
  2:      89
  4:    1,770
  6:   13,932
  8:   54,596
 10:  119,466
 12:  152,813
 14:  110,749
 16:   36,898

distance <= real distance 2:
  90 / 490,314 = 0.000183556
```

This is an exact family-wise base rate for the frozen construction, not a
formal discovery p-value: the convergence was noticed after extensive prior
puzzle exploration, and the adjacent-swap description was noticed after
viewing the mismatch. The result is nevertheless substantially more
structured than the Phase 46 `"yang"` substring alone: the creator-derived
color inventory, creator-derived FEFE address, community-described `B/BE`
mapping, extraction length, symbol composition, and 29 fixed source positions
all converge within one unsupported adjacent transposition.

**Verdict:** this is now the strongest bounded reconstruction of Denis's
missing yellow-blue-primes guide, but it is not exact. The next valid step is
evidence recovery: find the missing guide image or a creator-supported
ordering convention that independently predicts the object-22/object-23
exchange. Do not search arbitrary swaps/permutations, and do not escalate
this near-match to AES, Key Wrap, hashes, or private-key derivation.

### Phase 47 continuation -- both evidence-recovery paths checked, one closed computationally (2026-07-25)

Checked feasibility of the two evidence-recovery paths named above before
attempting either. Denis's missing "guide to yellow-blue-primes" image is
not recoverable from anything in this environment: `chat_transcript.txt`
was generated by `gsmgio-5btc-puzzle/_work/parse_chat.py` from a raw
Telegram HTML export (`D:\tmp\gsmgio-5btc-puzzle\ChatExport\messages*.html`)
on a separate machine, and that parser only ever extracts `<div
class="text">` -- it never captured `<div class="media">`/photo blocks, so
even if the image was attached it was never pulled into this repo. No trace
of the raw export or any Telegram media directory exists on this machine.
The book's physical pages 57-58 likewise need physical access neither
available here.

The third possibility -- that our own reading-order convention for the
first-piece grid is one arbitrary choice among several equally-valid ones,
and a different one might independently predict the object-22/23 exchange
without needing Denis's image -- was checked directly rather than assumed
closed. `tools/gsmg/reading_order_uniqueness_audit.py` tests 8
pre-registered traversal conventions (the established counterclockwise
top-left spiral in both rotation directions from all 4 corners, plus
row-major, column-major, and boustrophedon/zigzag order) against the same
grid, checking which ones decode the known 24-character text
(`gsmg.io/theseedisplanted`) exactly. Result: **only 1 of 7 distinct
underlying paths decodes correctly** (2 of the 8 named conventions collapse
to the same path, since starting top-left heading left is immediately
out-of-bounds and forces an identical first turn to starting top-left
heading down -- not a real ambiguity). Every other convention -- clockwise,
alternate starting corners, row-major, column-major, boustrophedon --
produces unreadable bytes.

This means the object-ordinal -> pixel mapping is not a free parameter on
our side; it is uniquely forced by the requirement to decode readable text,
and there is no principled alternate convention available to explain the
object-22/23 discrepancy. All three avenues named in Phase 47's verdict are
now closed for the time being: the missing image and the physical book
pages both require external access this environment doesn't have, and the
one avenue that was checkable here (alternate reading order) is ruled out.
The object-22/23 discrepancy remains genuinely unresolved. No AES/cipher
escalation is justified by this null result either.

### Phase 47 continuation -- reconciling "consume" across Phase 41 and Phase 47 (2026-07-25)

The creator-authored dependency chain's "consume the marked prime/zero
object" step had acquired two operational readings that were never
cross-referenced against each other: Phase 41 deletes the addressed
*character* (`n`) from the 24-character decoded text, giving `gsmg.io/
theseedisplated` -> "the seed is Fe-plated"; Phase 47 removes the addressed
object's *color* from the 24-item B/Y sequence before the `B->b, Y->be`
encoding. Read in isolation these look like two competing hypotheses about
what "consume" means.

`tools/gsmg/consume_reconciliation_audit.py` checks this directly rather
than assuming either reading is independent of the other: both phases
derive the addressed index from the same dynamic
`reconstruction["fefe"]["character_0"]` field, never a hardcoded `21` --
confirmed by inspection of both scripts, so neither violates Phase 37's
caution against "arbitrary `{1,4,21}` indexing". Removing that single
FEFE-addressed object (index 20, ordinal 21, character `n`, color yellow)
**once** from the shared 24-item object list and reading off both
projections reproduces both prior results simultaneously:

```
text-channel projection  (Phase 41's operation): 'gsmg.io/theseedisplated'
color-channel projection (Phase 47's operation): 'BBBBYBBBYYBBBBYBBYYBYBY'
```

**Reconciled: "consume the marked object" is one well-defined operation
(remove the FEFE-addressed object from the 24-item list) with two
independent, already-recorded readouts -- the decoded-text channel and the
color channel -- not two competing interpretations.** This does not by
itself strengthen either downstream result (Fe-plated remains an
unconfirmed semantic reading; the mask convergence remains an unresolved
near-match), and it does **not** resolve Phase 47's own residual
object-22/23 discrepancy, which is untouched by this check and remains
genuinely open. Its value is narrower: it removes one apparent
inconsistency in the project's own reasoning, so future work can treat
"consume" as settled and build on either or both channels without
re-litigating which one is "correct".

### Phase 47 continuation -- narrowing (not resolving) the object-22/23 discrepancy (2026-07-25)

Four further, narrower checks on the residual gap, via
`tools/gsmg/object_swap_locality_audit.py`:

1. **Our own encoded color string is not findable in the source plaintext
   at all** (`recover_position_masks` on it returns 0 matches). The
   convergence is specifically tied to Denis's exact posted 31-character
   string, not something independently recoverable from the source without
   his transcription.
2. **The two mismatched output positions (28, 29) trace back to source
   positions 85/86 -- characters `s` and `t`, which are directly adjacent
   in the source plaintext.** Any order-preserving mask is necessarily
   forced to read `s` before `t`, since they are neighbors. This rules out
   "a different selection rule would fix it": no order-preserving selection
   of the source could ever produce them in the other order, so the
   explanation has to be a transcription-level event (or something specific
   to this one boundary in our own reconstruction), not a selection-rule
   artifact.
3. **The mismatch spans two distinct color-objects** (reduced-sequence
   indices 20 and 21, one `Y` and one `B`), not a single object's
   two-character `be` code read in the wrong internal order. It is a
   whole-object swap, consistent with Phase 47's original framing, not a
   token-boundary encoding quirk.
4. **The mismatch does not overlap the `"yang"` substring** (output
   positions 4-7 in Denis's string) -- whichever explanation is correct, it
   does not threaten the one mechanically confirmed fact from Phase 46.

**This narrows but does not resolve the gap.** The most plausible reading
consistent with all four checks is a two-character transcription slip when
Denis typed his message (a mundane error, and the kind that swapping two
adjacent characters produces), rather than a cipher-relevant discrepancy --
but that cannot be distinguished computationally from an error in the
source image at that exact boundary without Denis's original notes or
image. No further computational test is expected to distinguish these
without that external evidence; this closes the productive computational
angle on this specific residual gap.

## Phase 48 -- Flo prime-walk provenance recovers Denis's mask and resolves the FEFE boundary (2026-07-26)

`tools/gsmg/flo_prime_walk_provenance_audit.py` corrects an initially faulty
transcript search and audits Flo Sku's April 2026 community construction
against the primary archive. The previously missed evidence is real:

* Flo posts the literal highlighted DBBI string at
  `chat_transcript.txt:171498`;
* Mahfooz identifies changed `BE` tokens at
  `chat_transcript.txt:171515`;
* Flo answers that the two `Be` values are blue and to "ignore the e" at
  `chat_transcript.txt:171548`;
* Artem reports seven misses at `chat_transcript.txt:171554`;
* Denis describes a perfect match specifically for the first 20 bits at
  `chat_transcript.txt:171575`.

The audit asserts every quoted artifact and their chronological order. It
also corrects another provenance error: Denis's yellow-blue-primes exchange
on 2026-03-03 predates Flo's 2026-04-13 description, not the reverse.

**Exact mask identity.** Flo's highlighted string lowercases byte-for-byte
to DBBI and contains exactly 31 capitalized raw positions:

```
2, 3, 5, 7, 11, 12, 14, 18, 20, 24, 25, 31, 32, 34, 40, 44,
46, 50, 51, 57, 63, 65, 66, 72, 73, 77, 79, 85, 86, 90, 91
```

Selecting those same positions from the aligned 91-character
`incaseyoumanage...` plaintext reproduces Denis's exact 31-character
extraction, `ncsyangcahiriasogaleafayanestve`. The set is exactly mask 2
of the four masks recovered in Phase 46 and the sole B/BE-compatible mask
identified in Phase 47. This is a genuine provenance advance: Flo's literal
artifact reconstructs Denis's previously missing position mask exactly.

It is **not three independent confirmations**. Phase 47's mask is recovered
from Denis's output, and the recurrence below formalizes Flo's description.
Flo and Denis also participated in the same public community thread, so
independence between their derivations cannot be established.

**Initial omitted-FEFE model, corrected during the next-step audit.** Applying
the recurrence to only the 24 blue/yellow byte endpoints makes color object
21 appear to be the first failure:

```
n=21, prime=73, prior yellows=6, raw position=79,
color=yellow, required=be, actual=bf
```

That is not Flo's stated construction and not the real spatial event order.
FEFE is at spiral index 163, between color object 20's endpoint at 159 and
color object 21's endpoint at 167. It is therefore an inserted 21st event,
not a replacement for color object 21. Sorting all 24 colored endpoints plus
FEFE by the validated spiral gives:

```
BBBBYBBBYYBBBBYBBYYB F YYBY
```

Representing FEFE as the single `b` explicitly described by Flo makes event
21 land on prime 73 / adjusted raw position 79 exactly. Events 22 and 23
then consume the two following yellow `be` pairs at raw positions 85-86 and
90-91. DBBI ends there; event 24 would begin at raw position 97, outside its
91 characters. Thus all **23 events that fit inside DBBI match exactly** and
produce all 31 of Flo's capitalized positions. No adjacent object swap or
post-hoc deletion is needed.

The exact fitted walk imposes 31 distinct constraints (`23 b + 8 e`), whose
positions are byte-for-byte identical to Flo's capitalized mask. Under a
uniformly shuffled copy of DBBI's exact multiset, the exact joint rate is:

```
(25)_23 * (18)_8 / (91)_31
  = 1 / 1,187,431,764,520,631,732,537,526
  = 8.42153654533e-25
```

The implementation computes this as an exact rational and verifies the
falling-factorial formula against exhaustive enumeration on three small
synthetic multisets. A real-case Monte Carlo check is deliberately omitted
because it could not resolve a rate this small.

**Correction to Phase 47:** its distance-2 “object-22/23 swap” resulted from
removing color object 21 rather than inserting FEFE immediately before it.
The spatially ordered 25-event model reproduces the compatible mask exactly,
so the proposed swap and the later locality analysis are superseded. The
text-channel `n` deletion / Fe-plated rebus remains a separate semantic
hypothesis; it is not needed for this color/prime reconstruction.

**Verdict:** the community construction is now exact through DBBI's end:
Flo's literal artifact recovers Denis's mask, and FEFE/73 is the inserted
single-`b` event that allows the walk to continue. Contemporary objections
remain relevant provenance for how ambiguous the explanation appeared, but
they do not defeat the now-explicit recurrence. The exact rate is still
descriptive calibration for a non-preregistered community finding, not a
formal discovery p-value. The next unresolved edge is what consumes the
selected 31-character plaintext and why the final two image events lie beyond
DBBI, not how to repair FEFE/73. No AES or arbitrary `zero73` transform is
justified yet.

## Phase 49 -- bounded consumption audit of the exact 31-position mask (2026-07-26)

**Boundary statement superseded by Phase 50:** events 24-25 are beyond DBBI
but not beyond the authenticated logical page stream; they enter the
immediately following binary `matrixsumlist` segment.

`tools/gsmg/prime_walk_output_consumption_audit.py` checks the immediate
outputs of Phase 48 under a frozen family derived only from existing clue
language: selected/complement rails (`yin yang`), literal zero replacement
(`characters ... zeroed out`), the exact `7x13` and `13x7` factorizations of
the 91-position mask with row/column reads and sums (`matrix sum list`), and
the two image events left after DBBI ends. It deliberately excludes
reversals, rotations, arbitrary transpositions, ciphers, hashes, and language
optimization.

The fixed textual artifacts are:

```
selected 31:
ncsyangcahiriasogaleafayanestve

complement 60:
iaeoumaetorcktsthepvtekeybelntohfandbtterhlndthelsoedfundoli

23 event-start characters:
ncsyagcahrasogaeafynesv

blue rail (14):   ncsygcaasogean
yellow rail (16): anhirialfayastve
FEFE rail (1):    e
```

Only `"yang"` is a literal clue-word hit, and only in the already-known
selected output. Neither `"yin"` nor `"salvation"` occurs literally in the
selected output, complement, or event-start output.

The 91-bit selection mask was decoded as thirteen 7-bit values under both
matrix shapes, row/column order, and both selected-bit polarities. None
contains a literal `yin`, `yang`, `seed`, or `key` marker, and none is
readable text. Direct row/column sum lists likewise produce no instruction.
One post-hoc temptation is the `7x13` row-sum A1Z26 rendering `FECECDE`,
which starts with `FE`; it is recorded but not promoted because `FE` was
noticed only after inspecting the output and the rest is non-language.

The two image endpoints beyond DBBI are mechanically:

```
image characters: e, d
event types:       B, Y
event primes:      89, 97
adjusted positions: 97, 105
```

Together they spell `ed` only because they are the final two characters of
the already-known word `planted`; no new instruction follows from that
suffix. There is also no aligned DBBI material at adjusted positions 97 or
105.

**Verdict:** the exact Phase 48 mask is a real structural recovery, but its
immediate selected/complement, zeroed, matrix, sum-list, and rail outputs do
not specify the next operation. No statistical gate is needed because no
nonliteral score-based finding is promoted; this is a deterministic
inventory with no readable candidate. Further transforms would require a
new creator-supported clue or recovered community guide, not expansion of
this closed family, and no AES escalation is justified.

## Phase 50 -- residual prime-walk events cross the real DBBI/matrixsumlist page boundary (2026-07-26)

The historical-boundary re-audit caught an assumption embedded in Phases
48-49: adjusted positions 97 and 105 were described as lying “beyond DBBI”
and therefore treated as unused. DBBI is not isolated in the authenticated
page stream. `tools/gsmg/page_structure_audit.py` proves the normalized
SalPhaseIon textarea begins:

```
DBBI[0:91] + abba("matrixsumlist")[91:195] + FAED ...
```

`tools/gsmg/prime_walk_page_boundary_audit.py` continues the already-fixed
25-event walk over this exact logical boundary without changing either prime
positions or event order:

```
event 24: blue, prime 89, adjusted global position 97
          -> matrixsumlist local offset 6
          -> bit 6 of byte 1, "m": b = 1  MATCH

event 25: yellow, prime 97, adjusted global position 105
          -> matrixsumlist local offset 14
          -> bit 6 of byte 2, "a": a = 0  MATCH
```

Thus the complete 25-event walk does not end in empty space: its final two
events enter the immediately following binary-encoded instruction, land at
the same bit position of its first two bytes, and reproduce the established
blue/yellow polarity `1,0`. Their containing decoded characters are `ma`, the
first two letters of `matrixsumlist`.

This is structurally aligned with the authenticated clue order
`yellowblueprimes -> matrixsumlist`, but the color-bit match is not rare.
The matrix segment contains 56 `b` and 48 `a` symbols; preserving that exact
profile, two fixed positions matching ordered `b,a` has exact rate:

```
56/104 * 48/103 = 336/1339 = 0.250934
```

It was also noticed after inspecting the page boundary. The result therefore
does **not** validate a new cipher or password. Its narrower value is that it
corrects the Phase 49 boundary statement and identifies a concrete place
where two formerly “unused” events touch the next authored instruction.

**Verdict:** retain as a transition checkpoint, not a discovery claim. The
prime walk now spans all 25 first-piece events across the exact
DBBI/`matrixsumlist` boundary. The first 23 events provide the exact 31-place
DBBI mask; the last two point into the opening bytes of `matrixsumlist`.
What operation `matrixsumlist` applies to the selected 31-character output
remains unresolved, and no AES escalation follows from an ordinary two-bit
match.

## Phase 51 -- `matrixsumlist` consumer feasibility audit: profile checkpoint, no unique operation (2026-07-26)

`tools/gsmg/matrixsumlist_31_feasibility_audit.py` tests whether the exact
31-character output can be consumed by any already-established
`matrixsumlist` mechanic without inventing dimensions or padding. The family
was frozen before inspecting outputs:

1. exact matrix factorization of the 31-character input;
2. the reconstructed `574061 -> [[5,7,4],[0,6,1]] -> [23,16,7]` list as
   forward/reverse, zero/one-based indices;
3. repeated Caesar add and both subtraction directions using `[23,16,7]`;
4. classical keyed-columnar encrypt/decrypt under literal key
   `matrixsumlist`;
5. comparison of `[23,16,7]` with the corrected prime-walk event/rail profile.

**Mechanical results:**

- `31` is prime, so its only exact rectangular shapes are `1x31` and `31x1`.
  No nontrivial matrix is fixed by the input itself.
- The 13-character key produces a ragged `31 mod 13 = 5` columnar layout.
  Both standard directions are reversible but non-language.
- The four bounded index reads are `ygc`, `aog`, `csy`, and `aoa`.
- The three repeated Caesar outputs and two keyed-columnar outputs are
  non-language and contain none of the fixed clue markers
  `yin/yang/matrix/sum/list/seed/key/enter/password`.
- The binary instruction has a natural `13x8 = 104` shape, but no
  authenticated operation maps those 104 bits onto 31 characters.

One exact old observation is restored under the corrected model:

```
matrix sum list: [23,16,7]
corrected walk:  23 fitted events,
                 16 yellow-rail characters,
                  7 blue-rail digraphs
```

This was part of Phase 13's rejected narrative. Phase 48 makes the underlying
walk exact, so the equality is real rather than an artifact of an ad hoc
parse. It is not statistically distinctive, however. Keeping FEFE fixed at
its real insertion point and shuffling the observed 9 yellow / 15 blue labels
over the 24 endpoint slots, the same profile occurs whenever the final two
endpoint slots contain one color of each:

```
C(22,8) * C(2,1) / C(24,9) = 45/92 = 0.489130
```

The equality is therefore a coherent shared-inventory checkpoint, not an
independent confirmation or a uniquely specified operation.

**Verdict:** the highest-priority feasibility audit stops negative. Existing
evidence fixes the inputs and produces a meaningful `[23,16,7]` profile
match, but it does not choose among indexing, Caesar use, columnar use, or an
unknown matrix operation. Direct bounded outputs are non-language. Do not
expand the transform family or escalate to AES; transition-evidence recovery
is now the highest-priority foreground task. The autokey continuation remains
valid unattended coverage work only.

## Phase 52 -- transition-evidence recovery: no archived post-selection operator (2026-07-26)

> **Evidence status superseded later on 2026-07-26:** a fresh Telegram JSON
> export preserves reply metadata absent from the old plain-text transcript.
> Denis's guide caption (message `60325`) replies to message `39937`, whose
> attached image is
> `photos/photo_1300@01-05-2025_00-12-58.jpg`
> (`sha256=475456f9ecf8fd56ef6247f081ba8ee0796eef3f6ed3be0ca01c4a5ee0bfb85a`).
> The image specifies a concrete 14x14 placement and row-sum operation yielding
> `IZLKESEEDQPPEN`. Therefore the claim below that the guide is unrecoverable is
> false. The narrower claim that no creator confirmation follows Denis's
> concrete extraction remains true. The recovered operation is being audited
> separately before any downstream promotion.

`tools/gsmg/transition_evidence_recovery_audit.py` reconstructs the complete
2026-03-03 transcript chronology around Denis Golovkin's 31-character output
and separates claims made before and after the concrete reveal.

The load-bearing order is:

1. Denis asks abstractly whether a 30-31-byte prime-index extraction containing
   `"ying yang"` and `"salvation"` would count.
2. The creator replies only that he needs to watch the address and that reaching
   the next phase would take the prize quickly.
3. Denis posts the recovered-guide caption while the creator is still present.
   Three seconds later the creator answers an unrelated question, then leaves
   before Denis posts the exact extraction, literal-`yang` observation,
   anagram proposal, or chain interpretation. This is silence, not
   confirmation of the guide.
4. Denis posts `ncsyangcahiriasogaleafayanestve`; only `yang` is a literal
   substring. `yin`, `ying`, `salvation`, and `everything` are absent.
5. Denis proposes a phrase anagram and immediately reports that trillions of
   attempted anagrams did not yield the key needed to proceed.
6. Four later phrases labeled `"manually crafted"` are exact 31-letter
   multiset anagrams, but the transcript supplies no rule selecting one.

The creator-only transcript contains neither the selected string nor the word
`anagram`. The earlier 2026 `"Bingo"` also cannot serve as confirmation: the
existing assertion-backed audit proves it answers gnomad's repetition of
`"in front of your eyes"`, not the later extraction or *Looking Forward*.

There is a real provenance limit. `_work/parse_chat.py`, which generated the
plain-text archive, executes `continue` when a Telegram message lacks a text
node. Media-only messages are omitted. Denis's `"Here was a guide..."` caption
contains no filename or attachment marker, the underlying Telegram HTML/media
export is absent locally, and a public exact-phrase/artifact search found no
indexed copy. The missing guide could contain additional visual instructions;
the present archive cannot establish them.

**Verdict:** no creator-supported post-selection operator is recoverable from
the archived text. The evidence supports applying the exact mask and inspecting
its output, but not anagramming it or feeding it into another invented
`matrixsumlist` transform. The assumption that all 31 characters require a
consumer is therefore downgraded: the string may instead be a terminal
recognition/checkpoint artifact. Literal `yang` remains plausible but is not
the creator's exact `"ying yang"` phrase and is not a password. Further work on
this edge is evidence-gated on recovering the original Telegram media/export.

## Phase 53 -- recovered Telegram yellow-blue-primes guide and corrected FEFE audit (2026-07-26)

A fresh Telegram Desktop JSON export restores the reply graph that the old
plain-text parser discarded. `tools/gsmg/telegram_yellow_blue_guide_audit.py`
verifies the complete provenance chain:

```
group: GSMG Puzzle Solvers (private_supergroup), 57,729 messages
guide: message 39937, Nik, 2025-05-01T00:12:58
file:  photos/photo_1300@01-05-2025_00-12-58.jpg
sha256: 475456f9ecf8fd56ef6247f081ba8ee0796eef3f6ed3be0ca01c4a5ee0bfb85a
reply: message 60325, Denis Golovkin, 2026-03-04T03:36:01
       reply_to_message_id = 39937
```

The recovered image is the missing “yellow-blue-primes” guide. Its historical
mechanic is now exactly reproducible:

1. split DBBI into 23 chunks ending at successive prime-token positions;
2. treat `b` as blue/value 2 and `be` as yellow/value 25;
3. map the remaining `a`-`i` symbols with A1Z26 values;
4. place the chunks counter-clockwise in a 14x14 matrix near the corresponding
   first-piece color endpoints;
5. sum rows modulo 26 with `A=0`.

The published matrix contains 83 nonzero cells whose spiral-filtered values
exactly reproduce the guide's DBBI tokens. Its row sums are:

```
[34,51,37,36,30,44,56,56,55,42,41,15,56,13]
 -> IZLKESEEDQPPEN
```

Thus `SEED` is a genuine output of a real historical construction, not a later
paraphrase. Two limitations are preserved rather than repaired:

- the `b` versus `be` segmentation is not independently derived. When Tobi
  asks whether inconsistent choices were made “just to match the pattern,”
  Denis answers exactly: `To match all prime positions` (messages
  `39987 -> 39989`);
- prime-token colors disagree with the 24-color sequence at events 21 and 23,
  exactly as the image states;
- prime-token 23 is placed at spiral index 70 rather than its colored endpoint
  71. This is the only endpoint-placement mismatch. Moving it to 71 preserves
  the same matrix row and therefore leaves every row sum and the output
  unchanged.

The canonical rule “place each chunk backward ending at its color endpoint”
also reproduces the exact historical row sums and output, despite seven
row-preserving cell differences from the published layout. This supplies a
fixed baseline for the corrected model without treating the unexplained
within-row placements as signal.

`tools/gsmg/telegram_yellow_blue_fefe_sweep.py` then inserts FEFE at its
verified spiral index 163 and continues the exact 25-event walk across the real
DBBI/`abba(matrixsumlist)` page boundary. The resulting final chunks are:

```
event 21: F, prime 73, DBBI "fb", endpoint 163
event 22: Y, prime 79, DBBI "ffgigbe", endpoint 167
event 23: Y, prime 83, DBBI "eeabe", endpoint 175
event 24: B, prime 89, matrix bits "abbabb", endpoint 183
event 25: Y, prime 97, matrix bits "ababbaaa", endpoint 191
```

Events 21 and 22 require two overlapping cells. Three policies were fixed
before scoring and included together in the null:

```
later_wins:    IZLKHMELLRPPEN  score=-6.817502
earlier_wins:  IZLKHMEHLRPPEN  score=-7.355309
skip_occupied: IZLKNSEHLRPPEN  score=-7.510440
```

The endpoint-assignment null preserves all 25 chunks, chunk boundaries,
endpoint geometry, row-sum operation, and the complete three-policy family,
but permutes which chunk is assigned to each endpoint. English quadgram
fitness is evaluated with a family-wise max statistic.

The initial pre-registered run and an independent larger replication agree:

```
corrected: seed 20260726,  5,000 trials: 400/5000,  p=0.080184
corrected: seed 424242,   20,000 trials: 1635/20000, p=0.081796
```

As a power check, the same gate applied to the known historical `SEED` output
is weakly exceptional but not strong by this project's stricter standards:

```
historical: seed 20260726, 5,000 trials: 196/5000, p=0.039392
historical: seed 424242, 20,000 trials: 767/20000, p=0.038398
```

**Verdict:** the Telegram artifact and historical `IZLKESEEDQPPEN` output are
verified primary community evidence. The bounded corrected-FEFE collision
family is negative: its best result is not exceptional and the result
replicates. Because the historical positive control clears only a loose 5%
threshold, this closes only these three collision policies under this
canonical placement and statistic. It does not prove the old guide's complete
placement rule, promote `SEED` to a password, justify AES escalation, or
license broader collision/transform searches.

## Phase 54 -- Denis Golovkin's own narrated chain, in the complete Telegram export (2026-07-26)

Stage 1 of the fresh Telegram JSON export analysis (`tools/gsmg/telegram_export_keyword_sweep.py`)
swept all 57,729 messages against a pre-registered keyword list. The raw sweep
matched 1,828 messages -- common puzzle-chat words like `dbbi`/`faed`/`guide`
turned out to be used constantly over seven years, not a narrow signal -- so
the reviewable set was narrowed to two bounded slices: keyword hits authored
by Denis Golovkin/Flo Sku, plus hits on the genuinely rare terms (`31
characters`, `ncsyang`, `consume`, `yellow-blue`). 68 messages total, all read
in full.

The most complete result is message `60352` (Denis Golovkin, 2026-03-04
03:57:30 -- 18 minutes 24 seconds after his `60333` extraction reveal, in the
same conversation):

```
yellow blue primes matrix sum list last words before acrhi choice ying yang

We took "yellow blue primes" of dbbi to filter indexes that match B or BE
chars vs indexes that don't match

Then we leaf through a puzzle book until the "matrix sum list" (i.e. a list
that contains text from matrix movie about your life is the sum)

On the "matrix sum list" we look for "last words before archi choice", i.e.
"last words before huge choice". I believe that AES password is pretty huge
choice, so these words could be "incaseyoumanagetocrackthis..."

And once we apply chosen indexes to these last words, we see that selected 31
(or 30) characters includes a "ying yang".

This way the password is pretty "in front of your eyes" but we didn't saw it.
```

This is Denis's own complete narration of the chain, previously only visible
in fragments across the plain-text archive. Two things in it are new
evidence, and one is a testable claim that was checked directly:

1. **Superseded by Phase 56:** Denis's “Matrix sum list” narration points to
   the already-solved Phase 3.2.1 Matrix-parody plaintext beginning `YOUR LIFE
   IS THE SUM...`, not to missing Cosmic Duality book pages. The zero book-OCR
   matches are therefore expected, not an unresolved physical-page gap.
2. **The anagram dead end is now confirmed by the original discoverer, not
   just this project's own null model.** In the same exchange (messages
   `60334`-`60340`), Denis observes literal `yang`, then says `ying`,
   `salvation`, and `everything` are “here as well” in the context of a phrase
   anagram. They are not literal substrings of the selected 31 characters.
   Denis then reports:
   "I've brute-forced few trillions of anagrams, but didn't find em to be the
   key to proceed." Primary-source confirmation, not just this project's
   negative.
3. **A community member's theory of the endgame** (bitkek, message `60359`,
   2026-03-04 15:06:16): "half = phase 3.2.2 AES / better half = cosmic
   duality / solve salph -> enter cosmic duality yin yang -> solve 3.2.2 with
   cosmic duality solution" -- i.e. the recovered string should work directly
   as an AES password. Tested directly against the project's existing,
   validated oracle (`cb_common.aes_try_open`, the corrected z-score gate from
   Phase 14) with no new script needed:

   ```
   >>> aes_try_open("ncsyangcahiriasogaleafayanestve")
   None
   >>> aes_try_open("incaseyoumanagetocrackthistheprivatekeysbelongtohalfandbetterhalfandtheyalsoneedfundstolive")
   None
   ```

   Both cleanly negative against SALPH/COSMIC/P32TRAILING -- no false
   positive, no weak-tier log entry.

**Verdict:** stronger provenance for the same chain this project already
reconstructed mechanically (Phase 48), a primary-source confirmation that
anagramming is a dead end, and one clean new AES negative. Nothing here
overturns Phase 52's verdict that no creator-supported post-selection
operator is recoverable, or Phase 53's negative on the corrected-FEFE `SEED`
construction. Phase 56 fixes the Matrix-passage source as the authenticated
Phase 3.2.1 plaintext, but still finds no unique operation connecting it to
the later `last words before archi choice` clue.

## Phase 55 -- recovered-guide Telegram neighborhood audit (2026-07-26)

`tools/gsmg/telegram_guide_neighborhood_audit.py` audits only the recovered
guide's direct reply neighborhood and two explicitly linked media artifacts.
It does not perform another corpus-wide keyword search.

The most important correction is an explicit admission about segmentation.
Tobi asks why some `b`+`e` boundaries are merged and others are not, ending:

```
is there a reason or just to match the pattern of the matrix?
```

Denis replies:

```
To match all prime positions
```

(messages `39987 -> 39989`). The historical guide's 23-prime alignment is
therefore a fitted construction, not a rule independently selecting every
`b`/`be` boundary. Its shuffle/control rates must not be interpreted as
discovery p-values.

The local replies add four narrower constraints:

- Nik says FAED's positions/characters do not have the same pattern
  (`39940 -> 39941`).
- Nik says the guide led to “nothing more” despite believing DBBI positions
  matter (`39942 -> 39944`).
- A community member contemporaneously suggests that the mismatch on the
  differently colored square means “we will use the hidden box too”
  (`40048`). This anticipates FEFE, but supplies no placement or collision
  operation.
- Denis later labels the guide image message `39937` as `One` (`60886`) and
  his own exact 31-character-mask image message `54430` as `Two` (`60887`).
  The second image is preserved as
  `photos/photo_1872@04-01-2026_10-00-07.jpg`,
  SHA-256
  `efdf08b8268f883eafb136a5a37a9e04d236374ebcf95900f71b99d0c1172671`.
  This is real community-artifact pairing, not creator confirmation.

The JSON timestamps also correct Phase 52's chronology:

```
60325 03:36:01 Denis: recovered-guide caption
60326 03:36:04 creator: unrelated reply to message 60323
60327 03:37:14 creator: goodbye
60333 03:39:06 Denis: exact 31-character extraction
```

The creator was present for 73 seconds after the guide caption but never
responded to it. He left before the extraction and all proposed
post-selection operations. Silence is neither rejection nor confirmation.

Finally, Denis's narrated chain in message `60352` follows the extraction by
1,104 seconds (18 minutes 24 seconds), not 21 seconds. Only `yang` is a literal
substring of the selected output; `yin`, `ying`, `salvation`, and
`everything` belong to the subsequent anagram discussion.

**Verdict:** the complete export strengthens provenance linking the historical
guide and exact mask, but weakens claims of independent statistical support.
The segmentation was explicitly fitted, FEFE was noticed without a consuming
rule, FAED was rejected by the guide author, and neither the creator nor the
community recovered a downstream operation. The direct reply/media
neighborhood is exhausted. Do not broaden collision policies or treat
`IZLKESEEDQPPEN`, `SEED`, or the 31-character output as an AES password without
new primary evidence.

## Phase 56 -- “matrix sum list” passage provenance: Phase 3.2.1, not the Cosmic book (2026-07-26)

`tools/gsmg/telegram_matrix_sum_passage_audit.py` traces Denis's message
`60352` claim that solvers should leaf through a “puzzle book” to a passage
about “your life is the sum.” The exact phrase has a much earlier and fully
authenticated source:

```
5595 2021-01-16  "understand the 3.2 text first. what is the matrix text..."
5596              posts the opening of the decrypted Phase 3.2 text
5597              "this and YOUR LIFE IS THE SUM OF A REMAINDER ...."
```

The public walkthrough's solved Phase 3.2.1 Beaufort plaintext begins:

```
YOUR LIFE IS THE SUM OF A REMAINDER OF AN UNBALANCED EQUATION
INHERENT TO THE PROGRAMMING OF THIS PUZZLE
```

and ends `HOPE YOURE THE ONE CIAO BELLA O`. The audit extracts that exact
block mechanically from the walkthrough rather than relying on chat
paraphrases. It contains 336 words, exactly one `SUM`, zero literal `MATRIX`,
and zero literal `CHOICE`.

Both complete local Cosmic Duality book extractions contain zero instances of
`your life is the sum`, `unbalanced equation`, `matrix sum list`, or
`matrixsumlist`. This is no longer an inconclusive missing-pages issue:
the phrase already has a known, authenticated Phase 3.2.1 source.

A later community interpretation in message `10721` explicitly proposes:

```
Matrixsumlist = focus on the scene between Architect and Neo
```

but that is not creator-authored. It also mixes two distinct texts:

- the custom Phase 3.2.1 parody supplies the exact `SUM` phrase but has no
  `CHOICE`;
- the real *Matrix Reloaded* Architect screenplay supplies the `choice`
  boundary used by `prime_matrixsum_reconstruction.py`.

Denis's 2026 narration bridges them by interpreting the AES password as a
“huge choice” and choosing `incaseyoumanagetocrackthis...` as the candidate
words. That is a coherent community theory, not an operation fixed by either
source text.

**Verdict:** retract Phase 54's suggestion that missing Cosmic Duality pages
may contain the Matrix-sum passage. The source is solved Phase 3.2.1 material.
What remains unresolved is narrower: whether `matrixsumlist` means to sum or
index that custom plaintext, use the original screenplay, or merely identify
the Matrix-themed phase. Since the custom plaintext lacks a literal `choice`
boundary and no creator message selects a bridge, no new extraction or AES
test is justified from this wording alone.

## Phase 58 -- exact Architect-dialogue counts and the recovered `[23,16,7]` list (2026-07-26)

`tools/gsmg/matrix_dialogue_count_audit.py` tests Telegram message `10721`'s
specific interpretation:

> throughout the scene, the word Matrix was mentioned 9 times
> the word sum was only mentioned once
> the word enter was only mentioned ... “she entered the matrix”

The complete control-room scene is extracted from the local *Matrix Reloaded*
screenplay PDF with fixed boundaries from `I am the Architect` through
`We won't`. It contains ten `Matrix` tokens in total:

- exactly nine are spoken by the Architect;
- one occurs only in stage direction.

The nine spoken contexts are each unique. In their dialogue order:

```
2nd Matrix context: "Your life is the sum ... programming of the Matrix"
6th Matrix context: "select from the Matrix twenty three individuals,
                     sixteen female, seven male"
8th Matrix context: "she entered the Matrix"
```

The fixed scene contains one exact `SUM`, one direction-only exact `ENTER`,
and one spoken `ENTERED`. Thus message `10721`'s intended dialogue scope is
correct even though its wording conflates the exact word with its inflected
form.

The sixth spoken Matrix context supplies the unique numerical list:

```
[23,16,7], sum = 46
```

That list has a three-way provenance chain:

1. the real screenplay: 23 individuals / 16 female / 7 male;
2. the authenticated Phase 3.2.1 parody: over 23 ciphers / 16 encryptions /
   7 intertwined passwords;
3. the first-piece prime `574061` arranged as `[[5,7,4],[0,6,1]]`, whose
   total and row sums are exactly `[23,16,7]`.

The first two are intentionally related texts, so they are not independent
statistical confirmations. The first-piece arithmetic is a separate
mechanical encoding of the same list. This materially strengthens
`[23,16,7]` as an intended carried-forward value and validates the Architect
dialogue as the relevant source behind `matrixsumlist`/`enter`.

No unique consumer follows. Plausible operations still include indexing with
the three values, summing to 46, treating them as counts, or using the three
corresponding Matrix-context ordinals `(2,6,8)`. No creator or authenticated
page instruction selects among them, and Phase 51 already tested the bounded
direct indexing/Caesar uses against the 31-character extraction without
language output.

**Verdict:** promote `[23,16,7]` from a merely coherent reconstruction to the
best-supported numerical value at this transition. Do not promote `46`,
`268`, or another derived transform: those require an additional operation
not present in the dialogue/count clue. No AES escalation follows.

## Phase 59 -- Stage 3 OCR pass over the Stage 2 media shortlist (2026-07-26)

`tools/gsmg/telegram_shortlist_ocr.py` processed all 50 items frozen in
`doc/GSMG_TELEGRAM_MEDIA_SHORTLIST.md` (40 images OCR'd via the same
grayscale/autocontrast/invert-if-dark preprocessing as
`extract_cosmic_duality_screenshots.py`, 7 text attachments read directly, 3
MIDI/video files logged out of scope). No item supplies a creator-authored
post-selection operation beyond what Phases 53-56 already establish.

Two results are worth recording:

- **id `62292`**'s caption already gave a literal constructed password
  attempt, `matrixsumlistenterlastwordsbeforearchichoicethispasswordmatrixsumlist`,
  tried by a community member against `salph.aes` via raw `openssl` with
  `-nopad`. Tested properly through this project's own oracle
  (`cb_common.aes_try_open`, all 6 KDF variants, all three default blobs):
  negative. The screenshot's own hexdump output (`9fa9 db91 a9de ...`) is
  visually uniform noise, not decoded plaintext -- independent visual
  confirmation of the same negative, not merely a second test of it.
- **id `60353`** is Denis Golovkin's own 280,718-character OCR of the
  complete Cosmic Duality book (shared in-chat as "OCR with errors"), a third
  independent transcription alongside this project's own screenshot OCR and
  the earlier curated file. It contains zero instances of `your life is the
  sum`, `matrix`, or `sum of`, consistent with (and additional evidence for)
  Phase 56's finding that the phrase is Phase 3.2.1 material, not a Cosmic
  Duality book passage on the missing pages.

**Verdict:** Stage 3 is exhausted for this shortlist. Nothing here reopens
any closed phase or promotes a new candidate; it independently corroborates
Phase 54/56's negatives from a different angle (direct visual/OCR inspection
rather than text-only citation).

## Phase 60 -- Phase 36's missing barrystyle media recovered (2026-07-26)

Phase 36 (2026-07-25) established that `@barrystyle` (displayed as `semaj`)
supplied the "very specific" hint the creator referenced on 2023-01-09, and
that the hint was the *Cosmic Duality: Mysteries of the Unknown* book
discovery -- but the exact media bytes were unavailable at the time and the
finding rested on inference from surrounding text.

The complete Telegram JSON export recovers the exact post. Message `8310`
(semaj, 2022-12-11T01:09:18) carries an image attachment,
`files/image_2022-12-11_07-09-14.png`
(`sha256=3a9b0a6ecacef83e1ef9f688303105570b3dcae95fd82be75f1fcbd2f5fddd04`),
with no caption. Message `8311` (the creator's "That is very specific") has
`reply_to_message_id = 8310`, directly confirming this exact image is what
the creator called specific -- not an inference from nearby chronology.

The image is a photograph of the physical book's front cover: the *Time-Life
Books "Mysteries of the Unknown"* series title, "Cosmic Duality," and the
same yin-yang-with-stars artwork already known from this project's own book
photographs. No interior pages, no additional text, and no other attachment
appears in the surrounding messages (checked `8309`-`8329`).

**Verdict:** this closes Phase 36's media gap completely. It confirms the
existing account exactly -- the "very specific hint" was barrystyle finding
the physical book, not an unidentified prime image or anything else -- and
supplies no new operational content. The missing physical pages 57-58 remain
the only unresolved evidence gap from this thread.

## Phase 61 -- Telegram `[23,16,7]` operation audit: a partition profile, not an arithmetic key (2026-07-26)

`tools/gsmg/telegram_23167_operation_audit.py` searches the complete Telegram
JSON export for messages containing all three standalone numerals and then
audits a frozen, message-ID-scoped set of records that explicitly propose an
arithmetic, logical, cryptographic, or structural use. There are 56
list-bearing messages, mostly quotations of the Architect dialogue or the
Phase 3.2.1 parody.

The operation-bearing community proposals include:

- decimal digit sums (`6115`);
- `16+7=23` (`16726`);
- XOR (`22530`, which evaluates to `23 ^ 16 ^ 7 = 0`);
- AND/OR or subtraction readings (`26922`, `34076`; the latter explicitly
  says it was LLM-aided);
- decimal concatenation to prime `23167` (`36002`);
- imported BIP38 mechanics (`45848`, `45849`, `47688`);
- sums `39`, `46`, or `186` (`45849`, `60893`, `46522`);
- `1327 = 23*57+16` after an alleged seven-pass XOR (`50381`);
- a separate URL-length profile `24/16/7`, not `23/16/7` (`66395`).

None of those frozen operation messages is creator-authored, none has a
creator reply, and none carries attached media specifying a missing operation.
They are therefore provenance records for community hypotheses, not
instructions.

One message is mechanically stronger. Denis Golovkin writes in message
`53997`:

> But, please, consider 83=b, 84=e
>
> You get pretty 7 / 16 / 23 then

This is exactly reproducible from the recovered yellow-blue-primes guide. Its
23 chunks contain 83 tokens while the final `be` remains one token. Splitting
that final token makes token 83 `b` and token 84 `e`; treating token 83 as the
last chunk endpoint changes the guide's endpoint inventory to:

```
23 total endpoints = 16 blue + 7 yellow
```

That directly mirrors the Architect's nested count:

```
23 individuals = 16 female + 7 male
```

The match should not be assigned a discovery p-value. The guide's ambiguous
`b`/`be` segmentation was explicitly fitted “to match all prime positions,”
and Denis's observation is community-authored. Its value is interpretive:
`[23,16,7]` is consumed naturally as the selector's total-and-partition
profile, not as an arithmetic key requiring another transform.

**Verdict:** close sum/XOR/concatenation/BIP38/subtraction as unsupported
transition operators. Keep `[23,16,7]` as an intended structural checkpoint:
23 selected guide endpoints partitioned 16/7 by color. This removes the need
to keep searching for an arithmetic consumer of the list. The unresolved edge
remains what consumes the resulting exact 31-character selection; this audit
does not authorize another transform or AES escalation.

## Phase 62 -- backend consistency audit: old transcript vs. complete JSON export (2026-07-26)

Dozens of scripts cite `chat_transcript.txt` (old, HTML-regex-parsed) by
exact line number, while the newer `telegram_export_*`/`telegram_yellow_blue_*`
scripts read the complete 2026-07-26 JSON export directly. This audits
whether the two actually agree, rather than assuming it.

`tools/gsmg/telegram_backend_comparison_audit.py` converts all 51,177 old
timestamps (explicit `UTC-05:00`) to epoch seconds and pairs records against
the JSON export by **both** absolute timestamp and normalized text. This is
important because multiple messages can share one second; pairing only the
first same-second candidate slightly overcounts text and sender differences.
The JSON's displayed `date` is local export-device time, while
`date_unixtime` is the stable comparison field.

Results:

```
old flat-text records:                         51,177
new records through the old cutoff:            55,987
new nonempty-text records through cutoff:      51,166
strict timestamp+normalized-text matches:      50,755
old-parser formatting-only differences:           411
relaxed timestamp+text matches:                51,166
old-only deleted messages:                         11
new nonempty messages lacking old counterpart:      0

new records after the old cutoff:               1,742
new nonempty messages after cutoff:              1,589
structured replies through cutoff:              13,137
media records through cutoff:                    4,083
captionless media omitted by old transcript:     3,108
```

The differences are fully bounded:

- **11 epoch-missing messages** (all April 2026, senders `R` and `Sparky`)
  are the only genuine content difference -- consistent with those messages
  being deleted between captures. They contain community discussion of
  address casing/private keys and one participant giving up; none is
  creator-authored or supplies a puzzle operation.
- **411 strict text differences** all disappear under a closed cleanup of the
  old parser's `[]`, rendered URL, `tel:`, and `mailto:` annotations. This was
  verified over the complete mismatch set, not a sample.
- **10,172 sender-nulls** are accounts Telegram no longer resolves a display
  name for. The old transcript is useful for those historical display names,
  while the JSON still preserves stable `from_id` values.
- **518 named sender differences** combine account renames with an old-parser
  weakness around forwarded/quoted content. Fifty-seven old sender labels
  contain an embedded date, and 33 `Jrk Bgrt ...`-like labels actually belong
  to non-creator user IDs. Generic old-transcript sender attribution must
  therefore be checked against JSON before being used as provenance.

The critical creator-only source survives this audit. All **411** old records
whose header is exactly `Jrk Bgrt` map to the stable creator ID
`user9815232`; none is lost or misattributed. The five non-literal text
differences are only empty-link artifacts. The new export adds 55 later
creator messages beyond the old cutoff.

**Verdict:** the two backends are consistent where they overlap. The JSON
export is authoritative for reply graphs, media, stable user IDs, and the
post-2026-06-12 extension. Retain the old transcript as a supplement for the
11 now-deleted messages and historical display names. Existing exact
creator-only citations remain valid; important generic community attribution
should be migrated to JSON message IDs/from IDs when revisited.

## Phase 63 -- consolidated creator clue, confirmation, and praise index (2026-07-26)

The existing `doc/GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md` is an analytical
dependency ledger, not a complete message-ID lookup. In particular, it does
not centrally list creator replies such as `Good point`, `very specific`,
`getting close`, `Bingo`, explicit refutations, or the creator's July 2026
return after the old transcript cutoff.

Added:

- `doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md`;
- `tools/gsmg/telegram_creator_clue_index_audit.py`.

The JSON-backed audit starts from the stable creator ID `user9815232` and
validates a bounded semantic index of **71 puzzle-relevant creator records**:

```
19 operational hints
12 confirmations
11 praise/progress statements
 5 recognition hints
 9 negative caveats
12 prize/validity meta statements
 2 historical corrections
 1 low-priority meta statement
```

All required text fragments and 24 preserved direct-reply edges are asserted.
The document also distinguishes direct JSON replies from adjacent joined
messages and states what each praise/confirmation does *not* validate.

One genuinely new cluster is now recorded. On 2026-07-13 the creator says the
actual answer remains on a hidden laptop (`66568`), says some chat members can
find him (`66571`), says close friends have the best chance (`66573`), and
then explicitly writes `NOTE: that is a hint` (`66574`). This is a real hint,
but its safest scope is physical/social proximity to the creator or retained
ground truth. Nothing in the wording licenses using `closefriends`, laptop,
or a location name as a cipher key.

**Follow-up classification check (2026-07-26).** The recommended bounded
question was already asked publicly and verbatim. Message `66874`, directly
replying to `66574`, asks: “Does the close-friends hint apply to a specific
public puzzle artifact? If so which artifact?” It received one direct reply,
`66875`, a sarcastic community comment—not a creator answer. The creator
subsequently posted 24 messages (`66884` through `66976`) without replying
to the question or its reply chain; the export continues through message
`67267`. Later community debate (`67044`–`67082`) supplies competing social
interpretations but no first-party classification. Therefore the question is
**explicitly asked and unanswered** in the complete export. Do not ask it
again merely to duplicate the existing record, and do not select a public
artifact from silence.

The index also locks the correct narrow scopes of frequently overextended
creator reactions:

- `7418` (`Good point`) supports returning to the first image, not every
  proposed hash detail;
- `8311`/`8315` validate the exact book-cover media as “specific,” not missing
  interior pages;
- `8352` praises general repository/progress quality, not every conclusion;
- `60312` (`Bingo`) confirms only the phrase “in front of your eyes but
  you're not seeing it,” not *Looking Forward*.

**Verdict:** use the new index as the primary creator-message lookup and the
older ledger as the dependency-chain interpretation. New creator evidence
must be added by stable message/user ID with its exact reply parent and a
statement of scope before it can influence a transform or cipher search.

## Phase 64 -- a 2020 diagram independently corroborates FEFE and names the "nest" cells (2026-07-26)

A 2020-03-24 community diagram (old `chat_transcript.txt:6848`; recovered in
the complete Telegram export as message `2899`, sender anonymized, photo
`photos/photo_41@25-03-2020_01-44-49.jpg`,
sha256=`550f34830161baea93414ce116f07407c164657ffaa3fc9061a149324238f9ee`) was
never previously cross-checked against this project's own reconstruction --
Phase 40 cited only the recurring "rabbits nest" catchphrase, not this
specific artifact. Its caption:

```
1. rabbit hole marked (rabbit looking to this point).
2. usual spiral solve showed.
3. rabbit nest is white box at center.
```

`tools/gsmg/rabbit_hole_nest_audit.py` reads the diagram's marked cells at
pixel precision (row 8, column 5 for the "hole"; rows 7-8/columns 7-8 for the
"nest") and checks both against `first_piece_color_reconstruction.py`'s
output -- a completely independent method (RGB pixel classification of the
real puzzle image, not hand transcription):

- **The "rabbit hole" cell is exactly the FEFE marker.** Its spiral position
  (163) maps to grid coordinate (8,5), an exact match to the diagram, and the
  real pixel there is `(254,254,254)` -- FEFE's own color.
- **The "rabbit nest" box is exactly the 4 cells the spiral traversal visits
  but the 192-bit/24-character decode never consumes** (positions 192-195 of
  196, after `24*8=192`). Their real colors are white/black/white/white --
  ordinary background, no additional signal.

**Verdict:** this is genuine independent corroboration, from a source
five years older than this project's own reconstruction, of a fact already
established through unrelated means (Phase 31/48's FEFE identification). It
does not supply a new operation -- FEFE's role is already fixed, and the
nest cells carry no hidden color signal. Filed as provenance strengthening,
not a new lead.

## Phase 65 -- rabbit-nest leftover nibble: exact `4/B` checksum, direct bit-4 zeroing negative (2026-07-26)

Phase 64 identified the diagram's central “rabbit nest” as the four spiral
cells left after the 192-bit/24-byte `gsmg.io/theseedisplanted` decode.
`tools/gsmg/rabbit_nest_nibble_audit.py` preserves their **ordered** values
instead of treating them only as a color census.

Under the already-validated Stage-0 polarity (`black/blue=1`,
`white/yellow/FEFE=0`):

```
nest bits:       0100 = 4
complement bits: 1011 = 11 = hex B
```

This is mechanically interesting because both values were fixed before the
nibble was inspected:

- `{1,4,21}` addresses one FEFE cell at the fourth one-based bit of character
  21;
- the creator's `R=18 / A=1 / B=2` follow-up and yellow/blue vocabulary make
  `B` an established symbol.

It is not statistically exceptional. Across all four-bit strings there are
eight complement pairs, so the specific unordered `{4,B}` pair has descriptive
rate `1/8 = 12.5%`; the connection was also recognized after recovering the
diagram.

The nibble nevertheless fixes one narrow previously-untested reading of
“some characters need to be zeroed out”: clear the fourth one-based bit
(ASCII weight `0x10`) in every character selected by the exact 31-position
mask. The result is:

```
selected:
ncciangcahibiacogaleafaianecdfe

full 91-character plaintext:
incaceioumanagetocrackthisthepbivatekeycbelongtohalfandbetterhalfandtheialsoneedfundcdolife
```

Neither is language and neither introduces a new literal clue word. The
existing `key` substring in the full stream is inherited unchanged from the
source. No cipher/AES escalation follows.

**Verdict:** retain `4/B` as a compact checksum linking the named rabbit nest
to the established fourth-bit/blue vocabulary. The direct exact-mask
bit-four-zeroing operation is negative. Do not rotate the nibble, try every
bit plane, or expand into ciphers without new creator evidence.

## Phase 66 -- creator clue index expanded to 80 records; one real provenance upgrade (2026-07-26)

A systematic review of all 395 creator text messages not covered by Phase
63's index (out of 482 total) added eight further records and one
correction to `doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md` and
`tools/gsmg/telegram_creator_clue_index_audit.py` (71 -> 80 records). Most
promising-looking candidates did not survive reading their surrounding
conversation and were excluded: `"Only -41,-17 matters"` (an unrelated
interactive game, not the puzzle), `"You have to be in your prime for
that"` (a joke in a thread about whether 2 is a "real" prime), and `"it's
hidden in a room with a hidden door"` (banter continuing the already-indexed
`66568` hidden-laptop bit, not new content).

**The one real upgrade**: the reversed-binary artifact
(`yellowblueprimes/matrixsumlist/lastwordsbeforearchichoice/...`) was
previously documented as "an authored puzzle artifact rather than a
Telegram message," with message `8483`'s weak emoji reaction as its only
chat linkage. Message `8446` (Jrk Bgrt, 2023-02-24T01:20:03, `reply=None`)
is the raw bit string itself, posted directly by the creator a full day
before any community member decoded it (message `8448`, 2023-02-25,
anonymized sender). Independently decoded here (reversed, 8-bit ASCII):
confirmed byte-for-byte identical to the already-documented text. This is
strictly stronger provenance -- a first-party creator Telegram post, not a
third-hand citation of an external page.

Seven smaller additions: an earlier (2019) precedent for the extra-door
theme; a hedge-then-affirm pair ("too much of a hint" / "there must at
least be something hidden in there") from the same thread as the Phase 64
rabbit-hole diagram, about whether the PK is inside the final decoded 3.2
cipher; an earlier (2020) private-key output-format confirmation; the
7-minutes-earlier lead-in to the already-indexed `{1,4,21}` hint; an
explicit wallet-emptiness solved/unsolved heuristic; a cross-reference to
Phase 40's already-closed "last number of pi" joke, recorded here only for
this index's own completeness; and a 2026-01-01 forward-encoded (not
reversed) binary reading "Happy new year! Make the best of everything. Oh,
and here's a 'tiny hint' <3." -- self-labeled a hint, but its content is a
festive greeting, not an operation.

**Verdict:** the index is more complete and one artifact's provenance is
materially stronger, but nothing here changes the project's current
boundary -- no new operation, transform, or password candidate follows from
any of these eight records.

## Phase 67 -- full 2020 rabbit-diagram transcription audit (2026-07-26)

Phase 64 checked only the two annotated locations in Telegram message
`2899`'s diagram: the highlighted “rabbit hole” and central “rabbit nest.”
`tools/gsmg/rabbit_diagram_full_audit.py` now checks the complete artifact
against the independently pixel-reconstructed first puzzle piece.

The audit is tied to the exact 781x433 JPEG
(`sha256=550f34830161baea93414ce116f07407c164657ffaa3fc9061a149324238f9ee`).
For every one of the **196** left-panel cells it classifies the center glyph
from pixels and compares it with the real grid's expected transcription:

```
black -> *
white -> blank
blue  -> b
yellow -> y
FEFE -> highlighted blank
```

The central four-cell nest is intentionally blank, including its one real
black cell. All 196 diagram symbols match exactly. The sole strong orange
highlight in the panel is row 8, column 5 -- the independently established
FEFE cell.

The red-line audit scans every internal cell edge in both panels rather than
checking only declared locations. Each panel has exactly **23** red
separators, with no missing or extra edge. They are precisely the boundaries
after bytes 1 through 23 in the validated top-left counterclockwise spiral.
The byte-24 boundary, between spiral positions 191 and 192, is not red:
it is the black outline of the central nest. Thus the diagram's separator
geometry independently encodes the same 24-byte grouping and deliberately
stops at the four unused center cells.

The right panel was manually transcribed at 4x from this exact hash (not
presented as OCR). Its three eight-character rings read:

```
gsmg.io/
theseedi
splanted
```

The display spells punctuation as `dot` and `slash`; concatenating the
characters gives the exact validated Stage-0 route
`gsmg.io/theseedisplanted`.

**Verdict:** the diagram is a complete and exact independent explanation of
the known spiral solve, not merely a rough community sketch. It materially
strengthens the provenance of “rabbit hole” = FEFE and “rabbit nest” = the
four cells outside the 192-bit payload. It does not expose an additional
payload or operation: the center remains ordinary `0100` under the known
polarity (Phase 65), and all visible diagram symbols are fully consumed by
the already-validated route.

## Phase 68 -- reaction-signal and success-claim sweeps of the complete export (2026-07-26)

Two further, independent axes over the full 57,729-message export, neither
keyword- nor anchor-based like every prior Telegram-export phase.

**`tools/gsmg/telegram_reaction_signal_audit.py`** ranks messages by total
Telegram reaction count (105 messages at >=5, a natural knee in the
distribution -- 523 at >=3 -- chosen before reviewing content) as a
community-significance signal independent of our own keyword list. The
signal is validated before being trusted: the single highest-reacted message
in the entire export is `53342`, already independently found and indexed in
Phase 66 (the New Year "tiny hint" binary). Of the other 104, all but a
handful are ordinary banter, moderation, or holiday greetings -- but several
external community resources surfaced that were not previously catalogued:

- Flo Sku's own puzzle-archive site, `https://gsmg-archive.org/` (message
  `63542`);
- a community-maintained guide and solve-attempt log, including a page
  specifically listing who tried what and how,
  `https://hosterjackagv.github.io/gsmg-5btc-puzzle/#/tried` (messages
  `66000`, `66489`);
- a community member's own creator-message extraction script and compiled
  output (`42827`, `42828`) -- superseded by this project's own
  message-ID-verified 80-record index (Phase 66), not a new source of facts.

None of these three have been fetched/reviewed for content in this pass;
they are recorded as known external resources, not yet audited.

One reaction-flagged message resolved a real gap in this project's own
prior analysis. Message `1837` ("Only -41,-17 matters", 2020-02-22) was
previously read as referring to an unrelated interactive game and set aside.
It is not unrelated: `-41,-17` are coordinates in the Decentraland virtual
world, part of the already-solved Phase 3 "Decentraland" puzzle piece
(confirmed via `_work/chat_transcript.txt:12204`, a creator-sourced hint
describing coordinates leading to an audio file whose hidden message,
recovered by stereo-channel steganography, is `HASHTHETEXT`). The correction
is scoped narrowly: `-41,-17` names a real, but already-resolved, historical
stage -- not a currently open lead.

A related, still-unresolved community thread (message `49536`, k1ng,
2025-09-24) analyzes PNG scanline filter-bytes of an unspecified image
("the QR code") and finds a single anomalous filter-byte whose line position
it tries to connect back to those same Decentraland coordinates. The
message ends "Let me know if anyone have any ideas!" with no follow-up
resolution found in the export. Recorded as an open community thread, not
independently verified or pursued further here.

**`tools/gsmg/telegram_success_claim_sweep.py`** searches the complete
export for a pre-registered list of solve-claim phrases (`"solved salph"`,
`"cracked cosmic"`, `"found the private key"`, etc.) -- 61 matches. Every
one was read in context. None is a genuine, verified solve:

- the great majority are rhetorical questions ("has nobody solved
  Salphaseion?") or the community explicitly denying/mocking a claim;
- one is a deliberately self-revealed hoax: message `48325` (Denis Golovkin,
  2025-08-30) posts "Congratulate me! I've solved Salph and Cosmic duality"
  immediately labelled "Scam spoiler... It's a hoax... cheating," linking a
  fake GitHub repo (`CoruNethron/salph-cosmic-great-solution`) as a
  deliberately-planted example of a false solution, not a real one;
- a separate, unrelated hoax from a different user ("Conner," messages
  `33136`/`33337`) posts a fabricated "Congratulations! You have solved the
  Cosmic Duality challenge" message; a third party (`43573`) explicitly
  rebuts it as an inexperienced solver misreading ordinary output.

A separate, concrete claim was checked mechanically rather than read as
prose: message `48598` posts a specific 32-byte hex string as a "cosmic
decrypt" key, followed immediately by its own poster writing "critical
thinking is noice btw" and "Dont believe everything you read or see" --
i.e. a self-revealed test, not a real claim. Tested anyway, as a literal
passphrase, against all three default blobs under all 6 KDF variants via
`cb_common.aes_try_open`: negative, consistent with the poster's own
admission and with Mahfooz's contemporaneous reply identifying the
underlying flaw ("you can use XOR and generate anything you want like
this").

**Verdict:** both sweeps corroborate, from two more independent angles, this
project's standing conclusion: nothing in the complete 7-year archive is a
verified solve of SalPhaseIon or Cosmic Duality, and the community's own
repeated, explicit consensus is the same. No new operation, transform, or
password candidate follows from either sweep. The three cataloged external
resources are a legitimate follow-up (reading them, not re-deriving
anything) if this thread is picked up again.

## Phase 69 -- calibrating the `-41+-17=-58` coincidence: base rate is not low (2026-07-26)

Following up on Phase 68's Decentraland correction, checked whether
`-41 + -17 = -58` -- landing on `58`, the confirmed real Cosmic Duality book
page cross-referenced from page 56 (Phase 8/36) -- is a meaningful
connection or an expected coincidence, before treating it either way.

`tools/gsmg/small_number_coincidence_calibration.py` pre-registers an
18-number pool of every small integer this project has independently
established as a real, cited puzzle-derived value (DBBI's matrix dimensions,
the `[23,16,7]` partition and its sum, the recovered mask length, the
Decentraland coordinates, the confirmed book page, and the five prime-walk
event primes) and checks all 153 pairs for sums landing on a different pool
member.

Result: **12 of 153 pairs (7.8%) coincidentally sum to another pool
member**, not the rare hit a first guess might suggest. One (`7+16=23`) is
tautological (`[23,16,7]`'s own definition, blue+yellow=total, not
independent). Excluding it: 11 of 152 (7.2%). `41+17=58` is one of eleven,
not a distinguished outlier.

**Verdict:** the base rate is high enough that this coincidence carries no
weight. This is the same failure mode already flagged in Phase 13 (debunked
apophenia) and Phase 36 (a genuinely prime number that failed its
profile-preserving null test) -- a puzzle this dense with small derived
numbers produces this kind of pairwise overlap routinely. No creator or
community source links Decentraland coordinates to a book page number;
this calibration gives no reason to promote one. Closed negative.

## Phase 70 -- `{b,e}` x `7x13/13x7` historical-coverage audit (2026-07-26)

Following the possible descriptive reuse of Decentraland's signed
coordinates (`-41 mod 9 = e`, `-17 mod 9 = b`; and prime ordinals
`41 -> 13`, `17 -> 7`), audited whether the resulting `{b,e}` plus
`7x13/13x7` configuration identifies an untested historical scope.

`tools/gsmg/dbbi_be_matrix_provenance_audit.py` separates reshaping from
reordering and compares the executable stream families directly.

The central fact is simple but important: placing the 91 raw DBBI symbols
row-major into either `7x13` or `13x7` leaves the byte stream unchanged.
Both labels produce exact identity DBBI. The natural coordinate-derived
reading therefore reduces to the already-tested identity checkerboard:

```
{b,e} and {e,b}
x
top_first and escapes_first
= 4 structural variants
```

Those four variants were attacked directly by the calibrated
monoalphabetic-recovery work (the original 60,000-restart run and the later
profile-matched calibration). Large candidate vocabularies also covered the
identity stream through the real AES oracle, including full board-structure
axes for the strongest curated sources.

Other matrix work is not interchangeable with that result:

| Family | Matrix coverage | Checkerboard coverage |
|---|---|---|
| Natural row-major display | `7x13`, `13x7` (same identity stream) | `{b,e}` both orders, both topologies |
| Self-derived matrixsum permutations | 10 permutations x 2 shapes = 20 streams | both orders, `top_first` only; shuffle gate negative |
| Dual-ternary routes | 8 routes x 2 shapes = 16 declarations / 15 unique streams | no `{b,e}` decode; trit representation only |

The audit also calculates the exact optional expansion that has **not** been
run as a composed checkerboard operation. Excluding the shared row-major
identity leaves 14 distinct non-row-major route streams (row-block reversal,
serpentine, column-major, and reversed variants for each shape). None equals
any existing common checkerboard transform or any matrixsum-derived
permutation. Crossing those streams with two escape orders and two
topologies would create 56 structural cells.

**Verdict:** the natural `{b,e}` x `7x13/13x7` interpretation is already
covered; no rerun is needed. The 56 untested cells are not a provenance bug:
they require adding an extra matrix-route operation that neither the
coordinates nor another creator clue specifies. Keep them as an explicitly
known optional transform expansion, not as queued compute. Reopen only if
primary evidence selects row reversal, serpentine reading, or column-major
reading.

## Phase 71 -- Stage-1 icon overlap + visible-rebus correction (2026-07-26)

The user asked whether combining the 8 small Stage-1 icons
(`doc/img/gsmg_icon_*.png`) could yield a number from colliding white
regions. The first audit also tested the icons' visible text, but
mis-transcribed lowercase `lo` as uppercase `IO` and therefore reported a
false 3-clean/1-broken split. This section supersedes that result.

**1. Pixel-overlap number hypothesis (still negative, with a corrected
control).** The original audit resized every image and compared the four
intended pairs with all C(8,2)=28 pairs. That control was not
exchangeable: the page supplies four black/blue left fragments and four red
right fragments, so the relevant null is the 4!=24 perfect matchings between
those two sets. The corrected audit center-pads the original pixels without
resizing, thresholds white at `R,G,B > 200`, and sums the four overlaps for
each matching. The intended matching scores 279 and is tied at ranks 19-20
of 24; 6/24 matchings score at least as high. Thresholds 160-240 and
left/center/right padding keep it between ranks 19 and 23, never uniquely
extreme. Raw overlap area is not a distinctive number source. This narrow
branch remains closed.

**1b. Colored/white/red width hypothesis (not covered by the first
audit).** Telegram-export message `670` contains the exact 189x323 montage
shown in the follow-up
(`sha256=8d0f0e9346d78f39da0e5a2d2fb0b84394ede34d965468e8d9bb2c165e7db16e`).
Its provenance sharply limits what can be inferred from its layout: Alex, a
community member, posted it after another member noticed the opposite-side
white strips, then wrote **“Here with borders”** (message `672`) and **“Not
sure if the sequence is right ..”** (`673`). Its black borders, spacing, and
row order are therefore not creator-authored evidence.

The white strips themselves are real source-PNG geometry. Measuring the
original lossless icons, rather than Alex's borders or JPEG pixels, gives
these colored-left/combined-white/colored-right widths in his montage order:

```
LO + CRYPTO/GIC   66, 28, 67
WAR + N/ING       70, 24, 66
CA + N/YOU        70, 21, 67
DIG/I/+ + T/-     70, 19, 67
```

The middle widths genuinely descend `28,24,21,19`, with successive
differences `-4,-3,-2`. This regularity was missed by the overlap audit and
should not be described as random or “no clean arithmetic step.” It still
does not recover a value or instruction: direct ASCII/A1Z26 readings are
invalid; row totals are `161,160,158,156`; and the most obvious balancing
expression, `left+right-white`, gives printable but meaningless `iptv`.
Moreover, 6/24 right-side assignments produce strictly descending middle
widths, and Alex explicitly disclaimed confidence in the chosen row order.
Without creator support for an operation, searching more formulas would be
post-hoc. Record the pattern; do not promote a width-derived route.

**2. Visible text is a deliberate rebus (positive correction).** The
archived source PNG is named `blue_lock_lo.png`, its rendered text is
lowercase **`lo`**, and its SHA-256 matches the local mirror byte-for-byte.
Rearranging the four black/blue images with the four red images gives:

- `WAR` + `N`/`ING` = **WARNING**;
- `LO` inserted into `CRYPTO`/`GIC` = **CRYPTOLOGIC**, i.e. `(crypto)` +
  **LOGIC**;
- `CA` + `N`/`YOU` = **CAN YOU**;
- `DIG`/`I`/`+` + `T`/`-` = **DIG IT**.

This is independently corroborated by the historical 2021 solution in
`halbgott29a/gsmgio-5btc-puzzle`, which explicitly records
`war + ning` and `LO + (crypto) gic` as identifying the song **The Warning
by Logic**. The remaining images reproduce the already-established prompt
**“Can you dig it?”** The known Stage-1 form answer is the lyric-derived
`theflowerblossomsthroughwhatseemstobeaconcretesurface`, already recorded
in the solved-chain ledger.

**Verdict:** Phase 71's overall “closed negative / ordinary stock assets”
conclusion was wrong. The icons contain an intentional, already-solved
visible rebus; only the proposed white-overlap *number* mechanism is
negative. Testing these Stage-1 labels against the much later
SALPH/COSMIC/P32TRAILING AES blobs was a category error and provides no
evidence about the rebus. Corrected and self-tested in
`tools/gsmg/phase1_icon_rebus_audit.py`.

## Phase 72 -- Stage-1 icon row band widths: superseded by Phase 71's 1b (2026-07-26)

Follow-up user question against the same chat screenshot: each row visually
splits into three flat color bands (blue/black, white, red) side by side --
does that width triple encode anything, and was it actually checked?

Measured this independently before realizing a concurrent pass had already
covered the same ground in Phase 71's "1b" section with better sourcing
(it traces the montage to Telegram-export message `670`, with the row-order
caveat from Alex's own messages `672`/`673` -- independently re-verified
here: message `670`'s photo is `photos/photo_15@08-05-2019_17-54-34.jpg`,
sha256 `8d0f0e9346d78f39da0e5a2d2fb0b84394ede34d965468e8d9bb2c165e7db16e`,
189x323, matching Phase 71's citation exactly, and `672`/`673` do read "Here
with borders" / "Not sure if the sequence is right ..").

The measured widths in both passes are identical: `66,28,67` / `70,24,66` /
`70,21,67` / `70,19,67`. This pass's own first draft additionally
mischaracterized the white-band sequence `28,24,21,19` as varying by an
"inconsistent step" -- it is not: the successive differences are
`-4,-3,-2`, a constant *second* difference of `+1`, i.e. a clean quadratic
progression. Phase 71's 1b already caught and corrected this same error
("This regularity ... should not be described as random or 'no clean
arithmetic step'"). Independently re-verified here, along with its
`left+right-white` = `'iptv'` computation (105/112/116/118 -> `i`/`p`/`t`/`v`)
and its claim that 6 of the 24 possible right-side assignments produce a
strictly descending middle-width sequence -- both reproduce exactly.

**Verdict:** no new result. Phase 71's 1b is the authoritative writeup of
this question (real quadratic pattern in the gap widths, but no
creator-supported operation recovers a value from it -- `iptv` is a
printable but meaningless artifact of one arbitrarily chosen formula out of
many that could be tried, the same post-hoc-formula-search trap flagged in
Phase 69). This section exists only to record that the independent
re-derivation matches and the "inconsistent step" framing in this pass's
own first draft was wrong.

## Phase 73 -- Stage-0 PNG filter-byte anomaly (message `49536`) fully reproduced, calibrated negative (2026-07-26)

Telegram message `49536` (k1ng, 2025-09-24) claims the raw PNG scanline
filter bytes of "the image" (not attached to the message, but immediate
context -- messages `49502`-`49514` -- is entirely about `gsmg.io/puzzle`,
the Stage-0 PNG) have an anomaly: exactly one row uses filter `0x00` among
1556 rows, its row number connects to the already-solved Decentraland
coordinates via a digit-split-and-reverse trick, and it lands 127/128 lines
into the image's embedded literal QR code, where 127 is the max 7-bit ASCII
value.

Every numeric claim was independently recomputed from
`doc/img/gsmg_puzzle_stage1.png` (1048x1556, confirmed the same file cited
elsewhere in this project) using a from-scratch PNG chunk/zlib/scanline
parser, not trusted from the message text:

- **Exact artifact and encoding are now pinned.** The source PNG's SHA-256 is
  `38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830`;
  its chunk CRCs, terminal `IEND`, decompressed byte count, and full IHDR are
  asserted. It is 8-bit RGBA with standard compression/filter methods and
  interlace method `0`.
- **Filter-byte histogram reproduces exactly**: `0x00=1, 0x01=91, 0x02=1464,
  0x03=0, 0x04=0`, and the lone `0x00` row is at index `1416` (0-indexed) /
  `1417` (1-indexed) -- exactly as claimed.
- **QR position reproduces exactly, via an independent method.** The image
  really does contain a literal QR code (bottom-left of the page, below the
  logo/title) -- detected here with OpenCV's `QRCodeDetector`, entirely
  independent of the message's own numbers. Its top edge is pixel row `1289`
  (0-indexed). `1416 - 1289 = 127`, matching the message's
  `counting_from_0 = 127` exactly.
- **The digit trick reproduces exactly.** Splitting `1417` into `14`/`17`
  and reversing the first half gives `41`/`17`, matching the real
  Decentraland `-41,-17` coordinate pair from the already-solved Phase 3
  audio-steganography stage (`HASHTHETEXT`).
- **The QR code itself decodes cleanly** (after perspective-rectifying the
  detected quad and re-detecting on the padded, thresholded crop) to
  `https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`
  -- the expected, visible prize-address explorer link. No hidden secondary
  payload; the QR's own logical content is mundane.
- **No valid module-boundary inference:** an initial audit draft treated the
  detected quad's 231px top-edge width as its height and assigned the
  horizontal scanline one module fraction. That was invalid: the QR is
  perspective-skewed, its two vertical edges have different spans, and one
  source-image row crosses changing module phase across the quad. The QR is
  version 4 (33x33 modules, confirmed from OpenCV's straight-QR output), but
  no unique "mid-module" or boundary classification follows from row 1416.
  This spatial argument is retracted and carries no weight in the verdict.
- **The immediate Adam7 follow-up is directly inapplicable.** Message `49537`
  speculates that PNG's optional seven-pass Adam7 scheme might connect to
  "seven intertwined passwords." The archived Stage-0 PNG's asserted IHDR
  interlace method is `0`, not Adam7 (`1`), so this specific file was never
  encoded through seven interlacing passes. The analogy supplies no hidden
  ordering or additional scanline stream here.
- **Checked one mundane explanation directly**: do `0x01`-filtered rows
  correlate with rows that pass through a blue/yellow grid cell (a plausible
  reason an encoder would pick a different filter)? Weak correlation only
  (14 of 91 `0x01` rows also touch a colored cell, out of 1047 rows that
  touch color at all) -- inconclusive, neither confirms nor rules out a
  mundane cause.

**Verdict:** the underlying technical claim is 100% real and reproducible
-- this is not a mistranscription or a fabricated chat post. But the two
"meanings" (Decentraland coordinates; max-ASCII position) are two different
post-hoc numerological readings of the *same single* anomalous row number,
not independent corroborating signals -- exactly the pattern Phase 69
calibrated and found unremarkable at this puzzle's density of small derived
numbers. Combined with the QR itself carrying no hidden content, there is no
recovered operation here, only a genuinely curious, fully-verified artifact.
Self-tested in `tools/gsmg/stage0_png_filter_anomaly_audit.py`. Closed
negative; message `49536` itself ends "Let me know if anyone have any
ideas!" with no chat follow-up resolving it either.

## Phase 74 -- External archive audit: no missing primary media; `YOUWON` retained with corrected evidential weight (2026-07-26)

Audited `gsmg-archive.org` and HosterjackAGV's
`gsmg-5btc-puzzle` at commit
`1a278563f64ea3134ab453a66179292bcae22034`.

- All ten puzzle images referenced by `gsmg-archive.org` hash-match local
  files exactly. The mirror adds no missing primary media or page content.
- Hosterjack's 158-entry attempt catalog is useful but mixes primary,
  community, and project-derived claims. Many of its open/stated conclusions
  are already covered or superseded here.
- The catalog surfaced one worthwhile omission: DBBI minus the 91-character
  solved VIC plaintext modulo 26 genuinely contains `YOUWON` at zero-based
  offset 21, leaving a 64-character tail. The original source is community
  message `23912` (2024-04-07), not a creator message.
- Under uniform shuffles of DBBI's exact symbol multiset, with the operation
  and target fixed, offset 21 is the only feasible `YOUWON` window and its
  exact probability is about 1 in 296,251. This is noteworthy but not a
  discovery p-value because the historical transform/word search is unknown.
- The catalog's “three independent signals” framing is wrong. `YOUWON`
  forces six consecutive underflow bits itself; the seven-one borrow run adds
  one bit, and the VIC-width run shares the sole feasible alignment. These
  are dependent corroborations, not three probabilities to combine.
- The colored prime positions also reproduce exactly as
  blue `{7,23,31,47,103,127}` and yellow
  `{71,79,151,167,191}`, all A007522. But A007522 was posted by community
  member gnomad in message `49487`, not creator-confirmed as the external
  catalog claims. Because all colored objects are character-LSB markers, the
  congruence `index = 7 mod 8` is structurally forced; the OEIS label is not
  independent evidence.

Full provenance, caveats, and source-inventory results are in
`doc/GSMG_EXTERNAL_ARCHIVE_AUDIT.md`. Mechanical assertions are encoded in
`tools/gsmg/external_archive_lead_audit.py`.

**Verdict:** external-archive recovery is complete and yielded no missing
primary artifact. Retain `YOUWON` as a plausible engineered community find,
not a key and not a solved DBBI decode. A bounded follow-up may investigate
whether the creator-supported offset 21 / `21|6|64` partition selects an
operation on DBBI's residual information; broad transform or passphrase
spraying is not justified.

## Phase 75 -- `YOUWON` partition audit: row geometry is real; downstream operation remains absent (2026-07-26)

The Phase 74 recommendation contained an indexing error: `YOUWON` begins at
**zero-based** offset 21, hence one-based character 22. It does not directly
match the creator's `{1},{4},{21}` character-21 locator. The historical
`21 | YOUWON | 64` framing is community-authored, not creator-supported.

There is nevertheless a stronger, non-arbitrary geometry. DBBI and the solved
VIC plaintext are both 91 characters, and DBBI's exact `13x7`/`7x13`
factorizations are independently established. Laying the subtraction output
as 13 rows of 7 gives:

```text
VOZIJBD
TIQBRGV
EOMZNBC
YOUWONX
CPKWGBN
AXDGJGD
UNNVMPA
BTAFPAA
XMJYLZB
UWERDNX
YDESKUO
BXCAMVD
JLQTSGA
```

Thus offset 21 is exactly the start of the fourth row, and the complete row is
`YOUWONX`. The grid-native partition is `21 | 7 | 63`, not `21 | 6 | 64`.
Calling `X` padding is tempting but unsupported: no insertion occurred, and
`X` is simply the next deterministic subtraction character.

This permits a tempting retrospective gloss on `{1},{4},{21}` as “one row,
fourth row, zero-based start 21,” while the grid dimensions `13x7` are both
prime. Neither is promoted: the gloss mixes a count, one-based row number,
and zero-based offset, and it was constructed after finding the row. The
original FEFE interpretation remains the direct, mechanically verified use
of `{1},{4},{21}`; these grid relations are secondary corroboration at most.

Exact DBBI-multiset calibration with the plaintext and operation fixed:

- `YOUWON` can occur at only one of all 86 starts: offset 21, with exact
  probability `375/111093983 = 3.37552035e-6` (about 1 in 296,251);
- restricting starts to the 13 seven-column row boundaries changes nothing,
  because offset 21 is the sole alphabet-feasible placement;
- exact row `YOUWONX` has probability
  `75/111093983 = 6.75104069e-7` (about 1 in 1.48 million), but that stronger
  number is descriptive only because the trailing `X` was noticed after the
  six-letter word.

Telegram reply-graph verification finds no creator-authored `YOUWON` post and
no direct creator reply to any exact `YOUWON` post. Message `23926` reports a
solver had found it two years earlier and reached a dead end. The 64-character
tail is not hexadecimal (43 characters lie outside `0-9A-F`), so its length
alone does not make it a private key.

Tested only the directly implied CBC candidates under all default and extended
cipher/KDF variants against SALPH/COSMIC/P32TRAILING: `YOUWON`, `YOUWONX`,
the 21-character prefix, 64- and 63-character tails, the output with row 4
removed, row 4 replaced by `AAAAAAA` (`A=0` in the output alphabet), row 4
replaced by literal zeroes, and the full output. All normalized case forms:
zero hits.

Reproduced and asserted by `tools/gsmg/youwon_partition_audit.py`.

Follow-up quarantine exhaustion: tested exactly `YOUWON` and `YOUWONX`
(upper/lower case forms) against `URLBLOB` as well, under the same 24 CBC
cipher/KDF variants. Zero hits. This does not promote URLBLOB's provenance;
it only closes these two newly surfaced passphrases against the quarantined
target.

**Verdict:** promote the fourth-row alignment as a plausible designed
easter-egg geometry, not as a solve. Demote the `64 = hex private key` reading
and retract “creator-supported offset 21.” The obvious remove/zero/direct-key
consumers are closed. No creator evidence selects a subsequent read order,
cipher, or transform, so this branch stops here unless new transition
evidence explicitly consumes `YOUWONX` or row 4.

## Phase 76 -- Telegram path diagram audit: useful history, unsupported convergence (2026-07-26)

Audited Telegram image
`photos/photo_2136@27-04-2026_23-29-08.jpg`
(`sha256=a47eb168ad3a312e0b55ec126d21f10e6fe4d5ef176cf2dfc3d286cec4a8792f`),
posted as message `62041` by community member `A`
(`user1165419324`, 2026-04-27). The post has no caption, no direct replies,
and no creator message in the checked `62041`-`62250` window. Its arrows are
therefore a community model, not creator-confirmed architecture.

What the diagram gets right:

- the genesis image is the common starting artifact;
- the ordinary icon/Logic -> Phase 2 -> Phase 3 -> Phase 3.2 chain is real;
- an extra-door/second route is creator-confirmed, and the Decentraland
  `HASHTHETEXT` route genuinely reaches the SalPhaseIon page;
- DBBI and FAED remain undecoded;
- open encrypted material exists on both sides.

What is inaccurate or stronger than the evidence:

- “Path A solved” is only true through the known Phase 3.2 plaintext. That
  plaintext contains the still-unopened `P32TRAILING` blob.
- “Cosmic Duality: 5 decoded segments” compresses a more complicated,
  byte-verified soup. Besides decoded labels, it contains DBBI, FAED,
  `shabefourfirsthintisyourlastcommand`, `shabefanstoo`, the embedded SALPH
  blob, and the separate COSMIC ciphertext.
- “both paths must converge here (yin/yang)” is a hypothesis. Creator evidence
  confirms yin-yang as a next reached phase/state, but does not identify Path
  A and Path B as the two halves, require cross-blob combination, or say that
  their ciphertexts share a passphrase.
- “Phase 3.2 AES + SalPhaseIon AES” is outdated and undercounts the
  authenticated targets. The current set is `P32TRAILING`, `SALPH`, and
  `COSMIC`; URLBLOB remains quarantined separately.

The evidence-safe map is:

```text
genesis
  |-- ordinary solved chain -> Phase 3.2 plaintext -> P32TRAILING (open)
  `-- extra-door / Decentraland -> SalPhaseIon page
                                  |-- DBBI / FAED (undecoded)
                                  |-- SALPH (open)
                                  `-- COSMIC (open)
```

The creator-authored macro clue orders first-piece values, `matrixsumlist`,
`lastwordsbeforearchichoice`, and then `yinyang`, so the branches may
eventually interact semantically. Their exact consumer, direction, and
cryptographic relationship remain unknown.

**Verdict:** preserve the image as a historical orientation diagram, but do
not use its dashed convergence arrow as a solving premise. It provides no
new operation and does not justify cross-keying or combining blobs.

## Phase 77 -- Legacy-CBC backfill for P32TRAILING and URLBLOB: coverage gap closed (2026-07-26)

P32TRAILING and URLBLOB were added after the original curated-candidate
sweeps. Both had received the 18 extended cipher/KDF variants and corrected
AES-Key-Wrap coverage, but the full curated corpus had not been independently
backfilled against the six original fast variants:

```text
EVP_BytesToKey {sha256,md5,sha1} x AES-{256,128}-CBC
```

Added `tools/gsmg/legacy_cbc_backfill.py`, reusing
`extended_cipher_recheck.py`'s candidate loader, `answer_forms()`,
`keystr_forms()` including newline variants, and the validated two-tier
oracle. The target set is fixed to P32TRAILING plus quarantined URLBLOB.

The current curated corpus is larger than the historical 568-candidate
snapshot because later focused wordlists were added:

```text
628 curated candidates
ordered candidate-list digest: 670f47c3184207a4
14,209 unique normalized/keystring forms
6 variants x 2 blobs = 170,508 decrypt operations
0 strong hits
0 new weak candidates
```

The weak-candidate review still contains only the pre-existing SALPH
autokey false positive (`z=5.036`); this backfill added nothing.

**Verdict:** the identified bookkeeping gap is fully closed for the current,
superset curated corpus. Neither P32TRAILING nor URLBLOB opens under any
original or extended CBC/KDF variant, or under the corrected Key-Wrap modes,
for these candidates. This remains candidate-set exhaustion, not proof
against an unknown passphrase.

## Phase 78 -- Binary-key-material CBC/ECB oracle gap fixed and backfilled negative (2026-07-26)

The shared CBC oracle had a distinct false-negative class not covered by the
printable-plaintext calibration: a correct decrypt whose output is binary key
material. This matters specifically because the authenticated 91-character
instruction says the private keys belong to “half and better half,” while
SALPH and P32TRAILING each contain exactly 80 ciphertext bytes. Under AES, two
raw 32-byte private keys form a 64-byte plaintext followed by one complete
PKCS7 block of sixteen `0x10` bytes.

Previously, `aes_try_open_bytes()` accepted that padding and then discarded the
body unless its printable-byte z-score reached the weak/strong language gates.
It could therefore silently reject the exact output shape the clue suggests.
The oracle now retains:

```text
AES + 80-byte ciphertext + exact 0x10 x 16 padding + 64-byte body
```

regardless of printability. A random wrong decrypt reproduces that complete
padding block with probability `256^-16 = 2^-128`, so the structural condition
is independently much stronger than the readable-text heuristic. A synthetic
known-positive regression uses a deliberately non-printable 64-byte body and
asserts successful recovery under both CBC and ECB; wrong-passphrase controls
remain negative.

AES-ECB was added as a separate bounded mode family because OpenSSL `enc`
produces the same `Salted__` envelope for ECB while deriving no IV. The new
`tools/gsmg/binary_key_material_backfill.py` tests SALPH and P32TRAILING
against:

```text
24 CBC/KDF variants + 12 AES-ECB/KDF variants
```

For a structural hit, the driver preserves the plaintext and WIFs only in a
mode-`0600` sensitive JSONL file, splits the body into `half | better_half`,
derives compressed and uncompressed P2PKH addresses, compares the two
established GSMG addresses, checks the repository's existing Rust-compatible
`BLMCACHE`, and places only address/hash160 metadata into a separate resumable
API-verification queue. Private keys, WIFs, and passphrases never enter that
queue. API verification distinguishes a currently funded address, a real but
now-empty used address, and a true Bloom false positive. Bloom misses do not
invalidate a structurally authenticated decrypt.

The real resumable run completed:

```text
648 curated candidates; digest 2d233645ef49a141
14,551 unique normalized/keystring forms
2 targets x (24 CBC + 12 ECB) = 72 operations/keystring
1,047,672 decrypt operations
0 readable hits
0 structural 64-byte hits
0 Bloom/API queue entries
```

The checkpoint contains exactly 14,551 unique indexes and 14,551 unique
keystring hashes, all with zero hits. A smoke run also caught and fixed an
initial resume bug before trusting the real result: `answer_forms()` returns a
set whose process-randomized order made index-only checkpoints unstable.
Forms are now sorted and completion identity is the keystring SHA-256 itself;
an immediate rerun adds no checkpoint records.

**Verdict:** the current curated corpus does not open SALPH or P32TRAILING as
readable AES-CBC/ECB plaintext or as the clue-supported raw `32|32` private-key
shape under the 36 bounded KDF/mode variants. This closes the oracle blind
spot, not the unknown-passphrase problem. No address was derived because no
cryptographically strong decrypt occurred, so the absence of a Bloom/API
queue is the correct result rather than missing downstream coverage.

## Phase 79 -- creator macro-clue fragments added to the corpus; CFB/OFB/CTR cipher-mode gap closed (2026-07-26)

Two genuinely untested, well-motivated gaps identified while reviewing what
"try next" actually meant (not more generic wordlist volume, which is
already saturated):

**1. Missing creator-chain fragments.** The message-`8446` decoded macro-clue
chain (`yellowblueprimes matrixsumlist lastwordsbeforearchichoice yinyang
wewontgiveawaythepassword itsinfrontofyoureyesbutyourenotseeingit
verylaststepisatruegiveaway promised`, Phase 66) was only partially in the
curated corpus: `yellowblueprimes`, `matrixsumlist`,
`lastwordsbeforearchichoice`, and `yinyang` were present standalone, but
`wewontgiveawaythepassword`, `itsinfrontofyoureyesbutyourenotseeingit`,
`verylaststepisatruegiveaway`, and the full combined chain were not (verified
directly against `extended_cipher_recheck.load_curated_candidates()` before
writing anything). Added
`wordlists/gsmg/full_macro_clue_chain_candidates.txt` -- every individual
fragment, adjacent pair, cumulative prefix/suffix, and the full chain (41
lines) -- registered in `CURATED_FILES`. Corpus grew 628 -> 648.

**2. Cipher block mode.** Every sweep to date (`KDF_VARIANTS`,
`EXTENDED_CIPHER_VARIANTS`, AES Key Wrap) only ever tries CBC.
`Salted__`/EVP_BytesToKey/PBKDF2 look identical for `openssl enc -aes-*-cfb`/
`-ofb`/`-ctr` -- the same category of blind spot that motivated Key Wrap
(Phase 26). Added `cb_common.STREAM_CIPHER_VARIANTS` (36: AES-128/192/256 x
legacy sha256/md5/sha1 + PBKDF2-sha256-i10000, x CFB/OFB/CTR) and
`aes_try_open_stream_bytes`/`aes_try_open_stream`, reusing the same
printable-z-score thresholds (justified in the new function's docstring:
the STRONG threshold was already derived purely from printable-byte
statistics, independent of padding). Self-tested with synthetic
known-positive vectors plus a wrong-passphrase negative control for all 36
variant combinations (`_self_test_stream_ciphers`, registered at module
load).

Re-ran the full curated corpus (now 648 candidates) against every existing
oracle plus the new one:

```text
legacy_cbc_backfill.py:   648 candidates, 14,551 keystrings,
                          6 legacy CBC variants x 2 blobs (P32TRAILING,
                          URLBLOB) = 174,612 ops, 0 hits
extended_cipher_recheck.py: 648 candidates, 17,037 keystrings,
                          18 extended cipher/KDF variants x 3 blobs
                          (SALPH, COSMIC, P32TRAILING), 0 hits
stream_mode_cipher_sweep.py: 648 candidates, 14,551 keystrings,
                          36 CFB/OFB/CTR variants x 4 blobs
                          (SALPH, COSMIC, P32TRAILING, URLBLOB)
                          = 2,095,344 ops, 0 hits
```

The weak-candidate log gained nothing new from any of these three runs --
still only the pre-existing SALPH autokey false positive (`z=5.036`).

**Verdict:** both gaps are now closed for the current candidate corpus. No
candidate -- including the creator's own decoded macro-clue chain -- opens
any tracked blob under CBC, extended CBC/KDF, Key Wrap, or CFB/OFB/CTR.
This is candidate-set-and-mode exhaustion for what has been tried, not proof
against an unknown passphrase or an untested mode (GCM/CCM are not covered:
OpenSSL's legacy `enc` command does not support authenticated modes under
the plain `Salted__` container, so they are out of scope for this oracle
family, not merely untested).

## Phase 80 -- structural binary-plaintext oracle gate: independent re-verification (2026-07-26)

Phase 78 (same date, filed concurrently) already covers this fix, its
reasoning, and its 0-hit backfill result in full; this section records only
the independent re-verification done before trusting or committing that
work, not a duplicate write-up.

Built a fresh synthetic test using `os.urandom(64)` (confirmed non-printable
first: z=-1.67, below even the weak-log threshold of 5), padded to an
80-byte AES-CBC blob under a known passphrase -- not reusing Phase 78's own
test vectors. `aes_try_open_bytes` recovered the exact random body under the
right passphrase and correctly rejected a wrong one. Also confirmed both
real target blobs (SALPH, P32TRAILING) are exactly 80 ciphertext bytes,
matching the shape the hypothesis assumes. `test_cb_common.py`'s
`test_binary_structural_gate_is_exact` (pad=15, 3DES, and body-length-63 all
correctly fail the gate) was also checked and holds.

**Verdict:** Phase 78's fix and its 0-hit backfill result both check out
independently. `.gitignore` updated for the new checkpoint/hits/queue output
files, since neither was covered by any existing rule (the hits file would
contain sensitive key material at 0600 if ever populated; none exists in
this run).

## Phase 81 -- provenance-tiered medium candidate corpus built, not launched (2026-07-26)

The 648-candidate direct-blob corpus is tiny relative to the approximately
575,248 additional unique lines under `wordlists/gsmg`, but the raw count is
misleading: 464,586 lines are overlapping 15-word Matrix screenplay windows,
63,565 are unrestricted community chat lines, and several other files are
different reductions of the same underlying text.

Added `tools/gsmg/build_medium_curated_candidates.py`, which keeps the
existing default unchanged and generates three disjoint, provenance-tracked
tiers:

```text
tier 1 primary/high-confidence: 24,554 base candidates
tier 2 puzzle-derived:          10,590 base candidates
tier 3 filtered broad:          31,297 base candidates
combined:                       66,441 unique candidates
ordered digest:                 d5cedf48b254d195
```

Tier 1 contains the existing 648, complete book OCR line/content reductions,
all 80 indexed creator messages, their directly-confirmed reply targets, and
bounded one-to-six-content-word n-grams. Tier 2 contains the project's
already-generated anchor/book/theme/chain combinations. Tier 3 admits clean
dictionary/cross-source chat and Matrix vocabulary, puzzle-anchored community
lines, and only a fixed non-overlapping partition of clue-scene screenplay
windows rather than all 15 near-duplicates around every word.

The combined and provenance files reproduce byte-identically across separate
process runs. There are 13,978 multi-source candidates. The same passphrase
expansion used by the binary-material backfill yields 525,436 cumulative
keystrings for Tier 1, 733,264 through Tier 2, and 1,397,158 through Tier 3.
At the measured 72-operation throughput, those boundaries are approximately
5.9h, 8.3h, and 15.7h respectively.

`binary_key_material_backfill.py` now accepts `--candidate-file`, so each tier
can use its own checkpoint/hit/API-queue files without modifying the
648-candidate loader or colliding with Phase 78's completed checkpoint.
Full methodology and exact hashes are in
`doc/GSMG_MEDIUM_CANDIDATE_CURATION.md`.

**Verdict:** this is a bounded expansion plan, not evidence that all 66,441
strings are equally plausible. Tier 1 is the next defensible unattended
coverage job; Tier 2 follows only if clean; Tier 3 remains broad bookkeeping.
The full screenplay-window and unrestricted-chat corpora stay excluded unless
new evidence selects them.

## Phase 82 -- pre-Tier-1 checkpoint and API hardening complete (2026-07-26)

A post-run audit regenerated the 648-candidate corpus and all normalized
passphrases independently. The completed Phase 78 checkpoint contains exactly
the same 14,551 unique keystring hashes, with no missing or extra values and
zero hits. Its historical index order differs for 9,097 entries because the
run began before deterministic form ordering was fixed, but set coverage is
exact; current hash-based resume skips all entries and appends nothing.

Before using the much larger Phase 81 tiers:

- binary-material checkpoints now include SHA-256 fingerprints of both
  `cb_common.py` and the driver, in addition to candidate/blob/variant
  fingerprints;
- `stream_mode_cipher_sweep.py` now has deterministic keystring generation,
  per-key checkpoints, exact source/config fingerprints, literal
  `--candidate-file` input, separate target testing, protected hit output,
  and resume support;
- both drivers reject a checkpoint whose source fingerprint changes;
- the Python API queue verifier is now tested without external network access
  through a full mock of both outcomes: `confirmed_funded` and
  `bloom_false_positive`;
- a stream smoke run resumes without adding records, and all 36 stream
  variants retain synthetic positive/wrong-passphrase controls.

**Verdict:** the known pre-expansion reproducibility gaps are closed. Future
code edits cannot silently inherit prior checkpoint coverage, stream runs no
longer depend on terminal-only completion, and Bloom positives have a tested
address-only verification path. No Tier-1 expansion was launched.

## Phase 83 -- Tier-1 binary-material expansion complete, clean negative (2026-07-27)

Ran the Phase 81 Tier-1 primary/high-confidence corpus against SALPH and
P32TRAILING under the exact Phase 78 binary-material scope: 24 CBC plus 12 ECB
KDF/cipher variants per target, or 72 decrypt operations per normalized
keystring.

```text
base candidates:       24,554
normalized keystrings: 525,436
decrypt operations:    37,831,392
started:               2026-07-26 19:45:03 +0300
finished:              2026-07-27 01:57:03 +0300
wall time:             6h 12m
structural/readable hits: 0
Bloom/API queue entries: 0
```

The completed checkpoint was audited rather than inferred from the final
progress line: it contains one header plus exactly 525,436 result records,
525,436 unique keystring hashes, and 525,436 unique indices covering
`0..525435`, with every record reporting zero hits. No hits file or API queue
file was created.

The absence of Bloom positives is expected and does not mean every random
decrypt was Bloom-tested. Address derivation occurs only after the strict
binary64 gate: an 80-byte AES decrypt must end in a complete sixteen-byte
`0x10` PKCS7 block, leaving exactly two 32-byte key candidates. A random
wrong-passphrase decrypt satisfies that exact padding shape with probability
approximately `256^-16` (`2^-128`).

**Verdict:** Tier 1 is a clean negative for the standard padded
64-byte-key-material interpretation under the tested CBC/ECB variant family.
It does not test an OpenSSL `-nopad` interpretation in which fixed 32-byte
windows are extracted from every 80-byte decrypt and checked through the
Bloom/API pipeline; that is a separate, substantially more expensive
hypothesis. Tier 2 remains optional coverage rather than evidence selected by
this result.

## Phase 84 -- `-nopad` window sweep built and validated; not yet launched (2026-07-27)

Implements the `-nopad` gap Phase 83 explicitly flagged as untested. `-nopad`
does not change CBC decryption itself -- it only means all 80 decrypted bytes
are retained instead of requiring/removing PKCS7 padding, so the `2**-128`
padding-based signal Phase 78-83 rely on does not exist here. The only
usable filter is address-based.

New self-contained script, `tools/gsmg/nopad_window_sweep.py`: only
*imports* from `cb_common.py` and `binary_key_material_backfill.py`, never
edits them, so neither file's SHA-256 changes -- confirmed by mtime (both
predate this script by hours) and by the fact Tier 2's checkpoint (actively
running throughout this work, confirmed via its own live-updating mtime)
was never touched.

Scope, deliberately bounded rather than an open search:

- four 16-byte-block-aligned 32-byte windows, offsets `{0, 16, 32, 48}` --
  covering the full 80 bytes with 50% overlap; no arbitrary sliding;
- known-address exact match (`PRIZE_ADDRESS`/`HALVING_ADDRESS`) checked
  first; the funded-address Bloom filter is secondary discovery only, and
  every Bloom hit is queued for mandatory API verification rather than
  treated as confirmed;
- if no individual window matches, exactly one clue-supported two-key
  combination is tested: offsets 0 and 32 (the non-overlapping pair
  spanning the first 64 bytes, matching the same "two 32-byte keys" shape
  already established under the padded interpretation) as a scalar sum mod
  the curve order and both orderings of a SHA-256 concatenation hash. No
  other pairing (there are six possible from four windows) is tested --
  the other five have no clue support, only combinatorial coverage;
- targets SALPH and P32TRAILING (both exactly 80 bytes -- COSMIC and
  URLBLOB are different lengths and don't fit this window scheme), under
  the same 24 CBC + 12 ECB variant family as Phase 78-83, so KDF derivation
  and decryption happen once per (keystring, variant, blob) and all four
  windows plus the combo check are read from that single decrypt, not
  re-derived per window.

Self-tested: window extraction and known/Bloom/none classification;
synthetic positives at all 4 offsets across 3 representative cipher/KDF
combinations (legacy-SHA256-AES256-CBC, PBKDF2-AES192-CBC,
legacy-MD5-AES256-ECB) in both compressed and uncompressed address forms;
the clue-supported combo recovering a key from two individually-unmatched
halves; a Bloom-only hit routing to the mandatory-verification queue file
(not the confirmed-hits file, and never carrying the private key) while a
known-address hit routes to the sensitive 0600 hits file; a negative
control; and the same checkpoint-fingerprint source guard used elsewhere.
One real bug was caught and fixed before trusting this: `ECB_CIPHER_VARIANTS`
is a 3-tuple (`kdf_kind, kdf_param, key_len`, AES-only), not the CBC path's
4-tuple -- the self-test's own synthetic vectors didn't exercise this exact
shape (they construct cipher operations directly rather than iterating the
real variant list), so a `--limit 5` smoke run against the real 648-candidate
corpus is what actually surfaced the `ValueError`. Both self-test and the
smoke run pass now.

Measured throughput: ~5.1 keystrings/sec (`--limit 50`, 10.8s), against the
padded sweep's ~24.7/sec -- about 4.8x slower, because EC point derivation
now runs on every window of every decrypt (no free structural pre-filter
exists without padding), not only on rare hits. A full Tier-1-scope run
(525,436 keystrings) would take on the order of 29 hours, versus Tier 1's
actual 6h12m under the padded oracle.

**Verdict:** the script is built, self-tested, and smoke-tested; not
launched against the real candidate corpus yet, per explicit instruction to
wait for the currently-running Tier-2 binary-material sweep to finish
first, and given the real cost (~29h at Tier-1 scope) warrants launching
deliberately rather than immediately.

## Phase 85 -- `-nopad` sweep: two real ordering/routing bugs found and fixed pre-launch (2026-07-27)

A review caught two bugs in Phase 84's `nopad_window_sweep.py` before the
expensive sweep launched -- both independently re-verified by re-reading the
actual code (not just accepting the report), then fixed and covered by a
new regression test.

**Bug 1 -- a Bloom false positive could suppress the real known-address
combo.** `check_decrypt()` checked the 4 windows individually first and
returned immediately if any of them got even a provisional Bloom
classification, before ever reaching the 3 combo candidates. A Bloom false
positive on any one window (a real possibility, not a hypothetical -- the
filter's designed false-accept rate is non-zero per lookup) would silently
prevent testing the one clue-supported combination, even if that
combination was the actual known-address match. This defeats the entire
purpose of testing combinations at all.

**Bug 2 -- Bloom routing was broader than the prior summary claimed.** Two
distinct issues: (a) a Bloom-only candidate's private key was written to
the sensitive hits file, contradicting what was reported in-chat (the
"safe order" review clarified this is actually the *correct* behavior --
private keys belong in the mode-0600 file regardless of classification, in
case a Bloom hit is later API-confirmed and the key is needed to spend it
-- so no code change here, the prior chat claim was simply wrong and is
corrected by this entry); (b) `record_hit()` queued *both* address formats
(compressed and uncompressed) whenever Bloom flagged only one of them,
because `classify_key()` returned a coarse classification with no record of
*which* address_type actually matched.

**Fix:** `classify_key()` was replaced with two functions,
`known_address_matches()` and `bloom_matches()`, each returning the specific
matched `address_type`(s) rather than a single classification string.
`check_decrypt()` was restructured to the safe order: derive all 4 windows
and all 3 combos unconditionally, check all 7 against the exact known-address
set first with zero Bloom lookups in that pass, and only run the Bloom pass
if pass 1 found nothing. `record_hit()` now queues only the address_type(s)
actually returned by the match, never the untested other format.

**New regression test** (`self_test()`, case 5): window@0 is a real Bloom
false positive (its hash160 is in the test Bloom filter, but it is not a
known address), while window@0 and window@32's scalar sum equals the known
key. Asserts the combo is still found and classified "known", and that
window@0's Bloom-positive status is correctly never even recorded (the
known-address pass finds the combo first, so the Bloom pass never runs).
Building this test surfaced a second, self-caught bug in the test itself
(reused `key_b`, which was paired with `key_a=7`, when pairing with
`bloom_key=12345` instead -- the sums didn't match): caught by the test
correctly failing with the actual wrong hit set, not by inspection.

Also replaced `os.urandom(80)` filler in several self-test bodies with a
fixed deterministic 80-byte sequence: an unrelated random combo derived from
`os.urandom` noise chanced into a real Bloom-filter false positive during
one run (the ~0.01%-per-lookup false-accept rate applies to any 20-byte
hash160, not just the ones under test), which would have made the test
suite flaky. This is what actually surfaced Bug 2's test-data pairing
mistake -- the spurious extra hit exposed that the expected hit set was
already wrong.

Re-validated: self-test passes (7 numbered cases plus the checkpoint guard),
`--limit 5` smoke run against the real 648-candidate corpus completes
cleanly, `py_compile`, the 9-test suite, and `git diff --check` all pass.
Confirmed again that `cb_common.py` and `binary_key_material_backfill.py`
remain byte-for-byte unmodified (mtimes predate this work) and Tier-2's
checkpoint continued updating live throughout (57,273 records at last
check, up from 45,834), undisturbed.

**Verdict:** still not launched. The script is now correctness-reviewed
twice (once at build, once by this fix pass) before committing ~29 hours of
compute to it -- exactly the point of validating before launching.

## Phase 86 -- `-nopad` sweep: checkpoint fingerprint gap closed + terminology correction (2026-07-27)

A third review pass on Phase 84/85's `nopad_window_sweep.py` raised two
points, both confirmed real by re-reading the code directly:

1. **Checkpoint fingerprint was incomplete.** `run_fingerprint()` hashed
   only this driver and `cb_common.py`, but the sweep's actual behavior also
   depends on `binary_key_material_backfill.py` (source of
   `private_key_details`/`append_jsonl`/etc., imported directly),
   `aes_key_wrap_sweep.py` (source of `ALL_CBC_VARIANTS`), the
   `KNOWN_GSMG_ADDRESSES` set, and whether a Bloom cache is active at all
   (`--no-bloom`) -- none of which invalidated a stale checkpoint if
   changed. (The sibling `binary_key_material_backfill.py` driver has this
   same narrower gap in its own `run_fingerprint()`; out of scope here since
   this project's convention is to only ever *import* from that file, never
   edit it.) Fixed by adding `binary_key_material_sha256`,
   `aes_key_wrap_sha256`, and `known_addresses_sha256` fields, plus
   `bloom_enabled`/`bloom_identity` (the live `BloomCache.identity` --
   path/size/mtime_ns/m/k -- when Bloom is active, `None` under
   `--no-bloom`). This required moving Bloom construction in `sweep()` to
   happen *before* fingerprinting (previously fingerprinted first, Bloom
   opened after) so its identity can be included. Added five new checkpoint-
   guard self-test cases, one per new field, each asserting that mutating
   just that field alone is enough to make `load_checkpoint()` reject a
   checkpoint -- not merely that the field is present in the dict.

2. **Terminology: "Bloom false positive" overstated what the regression
   test actually demonstrates.** The Phase 85 regression test's `bloom_key`
   has its hash160 deliberately inserted into a synthetic test-only Bloom
   filter (`_make_test_bloom`) so it reliably registers a Bloom match --
   this exercises the *code path* (a provisional Bloom hit on one window
   must not suppress a real known-address combo found elsewhere), but it is
   not an instance of the real Bloom filter's actual ~1.07x10^-8
   algorithmic false-positive rate (a separate, correctly-computed estimate
   from the review: over Tier-1's ~529.6M lookups, roughly 6 real false
   positives are statistically expected, not "tens of thousands"). Reworded
   the self-test comments and the closing summary print to say "simulated
   Bloom hit" rather than "false positive" for this specific test case. The
   general design-property language in `check_decrypt()`'s docstring and
   the flakiness-fix comment (`os.urandom` risking a real, unforced Bloom
   collision) is left as "false positive" since those describe the actual
   phenomenon, not a stand-in for it.

Re-validated: self-test passes (7 numbered cases, now including 5 fingerprint-
field-mismatch guards instead of 1), `--limit 5` smoke run against the real
648-candidate corpus completes cleanly with the real Bloom cache now
constructed before fingerprinting, `py_compile`, the 10-test suite, and
`git diff --check` all pass. `cb_common.py` and
`binary_key_material_backfill.py` remain byte-for-byte unmodified. Tier-2's
checkpoint continued updating live throughout this work, reaching 74,260 /
209,178 records (35.5%), still zero hits.

**Verdict:** still not launched. Checkpoint provenance now covers every
actual dependency, so a future edit to any of the imported modules (or a
Bloom cache swap) cannot silently reuse coverage computed under different
code -- the last known gap between this script's claimed and actual
correctness is closed.

## Phase 87 -- `-nopad` sweep: profiled speed investigation, two validated levers found, not yet applied (2026-07-27)

Phase 84's ~29-hour Tier-1-scope estimate was flagged as too long. Profiled
`nopad_window_sweep.py` with `cProfile` (`--limit 30`, no changes to the
real script) rather than guessing:

```
ncalls  cumtime  function
  2160    6.709  check_decrypt
 15120    6.101  private_key_details        <- 75% of total runtime
 15120    3.999  {EC_POINT_mul}             <- the single largest line
   540    1.184  {pbkdf2_hmac}              <- next largest block
```

`check_decrypt` calls `private_key_details()` unconditionally on all 7
window/combo candidates per variant, for all 36 CBC/ECB variants per
keystring per blob (`2 blobs x (24 CBC + 12 ECB) x 7 = 504` calls, i.e. 504
EC derivations, per keystring -- matching the profiled 15,120 calls / 30
keystrings = 504 exactly). Correction to an arithmetic slip in the first
version of this entry, caught on review: it originally said "1,008 calls",
which double-counted. 1,008 is real but describes a different quantity --
the worst-case count of Bloom *lookups* per keystring, not
`private_key_details` calls: each of the 504 EC derivations yields both a
compressed and an uncompressed address, and `bloom_matches()` checks both
against the filter (504 x 2 = 1,008), but only when pass 1 (known-address
check) found nothing for that keystring/blob/variant. There is no cheap
structural pre-filter under `-nopad` the way Phase 78-83's padded oracle has
(a ~2^-128 padding coincidence), so the 504 EC derivations are
architecturally unavoidable without changing what `private_key_details`
costs per call. Two independent, already-measured fixes target the two
largest lines:

1. **EC backend swap (`cryptography`/OpenSSL -> `coincurve`/libsecp256k1).**
   `private_key_details()` uses `cryptography`'s generic
   `ec.derive_private_key(...).public_key()`, which calls OpenSSL's
   general-purpose `EC_POINT_mul` -- correct for any curve, not optimized for
   this one. `coincurve` wraps Bitcoin Core's own `libsecp256k1`, which uses a
   fixed-base comb/window method specific to secp256k1. Isolated microbenchmark
   over 20,000 random keys: 3,434 keys/sec (`cryptography`) vs 30,802 keys/sec
   (`coincurve`) -- a 9x difference. Correctness-checked: a `coincurve`-based
   reimplementation of `private_key_details()` (using
   `coincurve.PrivateKey(key).public_key.format(compressed=True/False)` in
   place of manual x/y reconstruction) produced byte-identical output to the
   existing implementation across 500 random 32-byte keys.
   `coincurve` is not currently a project dependency; installed to a scratch
   user site-packages dir for this benchmark only
   (`pip install --user --break-system-packages coincurve`), not added to any
   requirements file or committed anywhere.

2. **PBKDF2 derivation caching.** All 9 PBKDF2-kind entries across
   `ALL_CBC_VARIANTS` (6) and `ECB_CIPHER_VARIANTS` (3) share the identical
   `kdf_param = ('sha256', 10000)`; only `key_len`/`block` (hence requested
   `dklen`) differ. `cb_common.pbkdf2_bytes_to_key()` calls
   `hashlib.pbkdf2_hmac(..., dklen=key_len+iv_len)` fresh every time, so the
   current driver runs the same 10,000-iteration derivation from scratch 9
   times per blob per keystring (18 total) where 1 would do. Verified the
   underlying reason this is safe: PBKDF2's output for a given
   (password, salt, iterations, digest) is a strict byte-prefix relationship
   across `dklen` values (`pbkdf2_hmac(dklen=48)[:16] ==
   pbkdf2_hmac(dklen=16)`, confirmed directly against `hashlib`) -- not an
   assumption, a property of the RFC 8018 construction (`T_i` blocks are
   computed independently of the requested output length). So deriving once
   at the maximum `dklen` any variant needs (48 bytes here) and slicing for
   the other 8 is exactly equivalent to calling `pbkdf2_bytes_to_key`
   separately for each, just without repeating the expensive part.

Combined effect, measured end-to-end by monkeypatching both fixes into an
in-memory copy of the real `sweep()` (the actual file on disk was not
modified): **4.63 -> 22.42 keystrings/sec, single-threaded** (4.8x). Applied
to the real Tier-1-scope count (525,436 keystrings), that moves the estimate
from ~29h to **~6.5h**.

A third, larger lever exists but was not pursued further this pass: the
workload is purely CPU-bound and embarrassingly parallel across keystrings
(confirmed via `ps`: `user` time == `real` time on the current single-
threaded runs). A `multiprocessing.Pool` benchmark using both fixes above
measured 23.4 keystrings/sec at 1 worker (consistent with the single-
threaded number), 129.8/sec at 8 workers, and 181.5/sec at 16 workers on
this machine's 16 logical cores -- sublinear scaling (7.75x at 16 workers,
not 16x) partly explained by Tier-2's `binary_key_material_backfill.py`
process independently consuming ~1 full core throughout this benchmark
(confirmed via `ps -eo pcpu`), leaving 15 contended cores rather than 16
free ones. Projected against Tier-1 scope: **~48 minutes**. This was
deliberately not built into the real driver: unlike the two fixes above (a
backend swap and a pure caching layer, both provably output-preserving and
each checked against the unmodified implementation), multiprocessing
requires redesigning concurrent-safe writes to the checkpoint/hits/queue
files -- new surface area of exactly the kind that produced the real
ordering/routing bugs in Phase 85 and the fingerprint gap in Phase 86.

Presented all three options to the user (single-threaded fix only /
also build multiprocessing / report only, implement later); the user chose
**report only for now** -- nothing in the shipped `nopad_window_sweep.py`,
`cb_common.py`, or `binary_key_material_backfill.py` was changed by this
investigation. `coincurve` is not a project dependency yet. Re-confirmed
after the benchmarking: `py_compile`, the 10-test suite, and
`git diff --check` all still pass against the unmodified tree; Tier-2's
checkpoint continued advancing throughout (still zero hits).

**Verdict:** two of the three speed levers are validated and ready to apply
whenever the user wants them (low-risk single-threaded fix: 29h -> ~6.5h;
optional higher-risk multiprocessing layer on top: -> ~48min). Neither has
been applied. The `-nopad` sweep itself remains unlaunched.

An independent review of this entry confirmed the profiling conclusions,
projected times, and the two fixes' mechanical validity, and caught the
504-vs-1,008 arithmetic slip fixed above. It also set requirements for
*whenever* these levers are actually applied (not done in this pass):

- pin `coincurve` as a real dependency (requirements file + Docker build),
  and fingerprint its version/backend into the checkpoint, the same way
  `oracle_sha256`/`driver_sha256`/etc. already bind the checkpoint to
  `cb_common.py` and this driver's own source (Phase 86) -- a silent
  `coincurve` upgrade changing behavior must invalidate stale coverage too,
  not just a source-file edit;
- add the `coincurve`-vs-`cryptography` parity check (currently a throwaway
  500-random-key check run once in this investigation) to the permanent
  self-test, not just this session's scratch benchmark;
- if multiprocessing is built, workers must only compute -- a single parent
  process must own all checkpoint/hits/queue writes, rather than each worker
  writing its own files (this benchmark's throwaway per-PID output files
  were fine for a timing measurement but are not the shape of a real,
  resumable, single-source-of-truth checkpoint).

## Phase 88 -- Jacque Fresco's broader body of work: sourced, bounded wordlist built and swept, clean negative (2026-07-27)

Prompted by confirming (via direct code reading, not memory) that Fresco is
CONFIRMED relevant to this puzzle -- "jacquefresco" is one of the three
normalized clue answers concatenated into the verified, already-solved
Phase 3.2 AES password (`data.py` `VERIFIED_PRIOR_COMMAND_HASHES
["phase32_clues"]` / `PHASE32_BLOB_B64`) -- while only his one specific
book, *Looking Forward*, had ever gotten a dedicated candidate list
(`wordlists/gsmg/looking_forward_candidates.txt`, 19 candidates, itself an
unconfirmed community lead per `doc/GSMG_YIN_YANG_TRANSITION_AUDIT.md`).
His other books, documentaries, and coined terms had never been turned into
candidates at all -- confirmed by grepping the whole repo for "fresco"
before starting, which found real mentions only inside raw community-chat
wordlist files (people happened to type "Venus Project" in chat) and the
existing Looking-Forward-scoped material, nothing purpose-built.

Researched Fresco's actual bibliography/filmography/terminology via direct
web lookups (WebSearch + WebFetch, not recalled from training data) rather
than guessing exact titles, since a single wrong character breaks a
password-candidate string:

- en.wikipedia.org/wiki/Jacque_Fresco -- coined terms (resource-based
  economy, sociocyberneering), book list, documentary list, one directly
  quoted attribution ("Because I can't get to anybody");
- goodreads.com/author/list/1080140.Jacque_Fresco -- full 11-title
  bibliography with co-author credits;
- frescofoundation.org/library -- cross-check (mostly his recommended
  reading, not his own work, so less useful than expected).

Two sources disagreed on one title's exact wording ("The Venus Project: The
Redesign of a Culture" vs "...Redesign of Culture") -- included both rather
than guessing. A handful of quote fragments came only from secondary
quote-aggregator search results rather than a primary transcript; kept them
in as lower-confidence entries but labeled that distinction directly in the
wordlist file's own comments, rather than presenting all entries as equally
verified.

Built `wordlists/gsmg/jacque_fresco_candidates.txt` (33 candidates after
the standalone-name + book + documentary + term + quote sections, each
section citing its source) and, following the same precedent
`looking_forward_candidates.txt` already set, kept it OUT of
`extended_cipher_recheck.CURATED_FILES` -- both lists are unconfirmed
speculative leads, not creator-grounded curated material, so neither joins
the default 648-candidate corpus.

Built `tools/gsmg/jacque_fresco_wordlist_audit.py`, mirroring
`yin_yang_transition_audit.py --oracle`'s bounded-check pattern but with
broader coverage: that script only ever tested CBC (legacy + extended) and
AES Key Wrap, because ECB and the CFB/OFB/CTR stream-mode oracles didn't
exist yet when it was written. This new script tests all four families
(CBC legacy+extended, ECB, stream, Key Wrap) against all four blobs
(SALPH, COSMIC, P32TRAILING, and quarantined URLBLOB) -- giving this newer
lead the same full coverage the main curated corpus already gets, since the
extra compute is trivial at this candidate-list size. Self-test covers: the
comment/blank/dedup candidate loader, one real encrypt-then-find round trip
per oracle family (CBC/ECB/stream/Key-Wrap, each independently proving that
family's wiring rather than trusting cb_common's own already-validated
self-tests to cover this script's argument-passing too), and a negative
control. Self-test passed clean on first run.

Real sweep: 33 candidates -> 549 unique keystrings (raw/SHA-256/double-
SHA-256 forms of each normalized answer) x all four oracle families x all
four blobs, in 2m47s. **0 hits** across CBC, ECB, stream, and Key Wrap.

**Verdict:** clean negative, same as the Looking Forward lead it extends.
Consistent with this project's established pattern for community-suggested,
non-creator-confirmed leads: cheap and worth ruling out, but not expected
to be the answer on its own. Fresco's own confirmed relevance was already
fully consumed by the (different, already-solved) Phase 3.2 stage; nothing
found here reopens that connection for the still-unsolved endgame blobs.

## Phase 89 -- Fresco wordlist: review caught real coverage gaps and titles; corrected re-run still negative (2026-07-27)

A review of Phase 88 confirmed the 549-keystring run itself was valid (exact
reproducing counts, correct wiring, credible zero-hit result for that
scope), but flagged "broader Fresco lead closed" as premature on three
points, all independently re-verified before acting on them:

1. **`keystr_forms(answer)` used the default `newline_variants=False`.**
   Confirmed by grepping the actual main sweeps: `legacy_cbc_backfill.py`,
   `stream_mode_cipher_sweep.py`, `binary_key_material_backfill.py`, and
   `extended_cipher_recheck.py`'s own default all pass
   `newline_variants=True`. This script's first version did not, so it
   never gave the Fresco lead the same coverage the main corpus gets.
2. **Two official titles were missing entirely**: "Structural Systems and
   Systems of Structure" and "And The World Will Be One", both on
   thevenusproject.com/jacque-fresco/. Re-fetched that page directly rather
   than trusting the review's claim -- confirmed both, and found the review
   itself had UNDER-counted: the same page also lists "Designing the
   Future: A Cybernetic City for the Next Century", "Science in 1980", and
   "Project Americana: Man in the World of Tomorrow", none of which either
   the first version of this file or the review mentioned. All five added.
3. **Two Goodreads titles had been shortened.** Confirmed against this
   session's own earlier WebFetch output (not re-fetched, since the exact
   text was already on hand): "Do You Speak Future?: Jacque Fresco Book of
   Insights" and "The Zeitgeist Movement: Observations and Responses -
   Activist Orientation Guide" are the real full titles; the file had only
   the truncated forms. Both full forms added alongside the existing
   shortened ones (kept, not replaced -- either could be how the puzzle-
   setter typed it, if either is relevant at all).

Fixing point 1 (enabling `newline_variants=True`) immediately broke the
self-test's negative control: an assertion failure, not a silent pass.
Investigated rather than loosened -- the control blob was
`hashlib.sha256(b"x").digest() * 5`, i.e. one real 32-byte digest repeated
five times to fill 160 (5x16) ciphertext bytes. Under ECB, repeated
ciphertext blocks decrypt to repeated plaintext blocks under any key, so
this collapsed to only 32 bytes of actual randomness, then repeated
whatever printable-looking coincidence occurred in those 32 bytes five
times over -- a pseudo-replication bug that inflates the printable
z-score's apparent sample size fivefold beyond the real underlying
randomness. It measured z=8.02 against this project's z>=8.0 strong-hit
threshold, an accidental hit confirmed by direct computation
(`cb_common.printable_z_score`), not a fluke to shrug off. Replaced with a
non-repeating deterministic SHA-256 hash chain of the same total length --
verified stable across three repeated self-test runs.

Re-ran the real sweep with all fixes applied: 40 candidates (up from 33) x
newline-variant-inclusive keystring forms -> 2,025 unique keystrings (up
from 549) x all four oracle families x all four blobs, in 10m19s.
**0 hits.**

**Verdict:** still a clean negative, now on a materially more complete
bounded candidate set and with equivalent coverage to the main curated
corpus. The review's core two title suggestions were correct, and directly
re-verifying its cited source surfaced three more the review itself missed
-- consistent with this project's standing rule to verify a claim against
the primary source rather than stopping at confirming the claim as stated.

## Phase 90 -- Fresco wordlist: 14 more sourced candidates added and swept, still negative; Tier-2 completes clean (2026-07-27)

A follow-up request supplied 14 more candidates across four categories
(official Fresco-page film/screenplay titles, Roxanne Meadows filmography
credits, a named core-concept term, and two directly attributed quotes),
each with a specific cited URL. Every one independently re-fetched and
confirmed directly against its cited page before being added -- none taken
on the strength of the request alone:

- thevenusproject.com/jacque-fresco/ -- confirmed "The Future and Beyond",
  "Welcome To The Future", "Cities In The Sea", "Self-erecting Structures"
  (that page's own casing), "Zeitgeist: Addendum", "Zeitgeist: Moving
  Forward", each with exact quoted context (film/screenplay listings on the
  same page the earlier book list came from, in a section the first two
  passes over that page hadn't surfaced);
- thevenusproject.com/the-venus-project/roxanne-meadows/ -- confirmed "The
  Venus Project Tour" and "A Conversation with Social Innovator & Futurist
  Jacque Fresco" as her own credited productions; also noticed "Self-
  Erecting Structures" is capitalized differently here than on the Fresco
  page, so both casings were kept rather than picking one; also noticed
  "Engineering the Impossible" (2002) on the same page (a documentary she
  was featured in) but did NOT add it -- outside the requested 14 and the
  request's own explicit bound against unrestricted additions, so flagged
  to the user rather than added unilaterally;
- thevenusproject.com/board-of-directors/ -- confirmed "Global Resource
  Based Economy" as Fresco's own named term for his core concept (kept
  distinct from the lowercase "resource-based economy" phrase already in
  the file from Phase 88);
- thevenusproject.com/multimedia/tvps_greatest_hits/ -- confirmed "If you
  do nothing, I can assure you nothing will happen." as a direct attributed
  quote at the top of the page, and "The choice is ours, my friend" as the
  refrain of a named poetic section on the same page;
- thevenusproject.com/major-motion-picture-history-progress-report/ --
  confirmed "Bright Tomorrow" as Fresco's lost 1950s screenplay and "a
  documentary history of the future" as its own quoted subtitle.

Added as 15 wordlist lines (14 requested items; "Self-erecting/Self-
Erecting Structures" kept as two casings rather than picking one), bringing
`jacque_fresco_candidates.txt` to 55 total candidates.

Per the request, ran a supplemental sweep scoped to only the 15 new lines
(not a full 55-candidate re-sweep of already-negative material) with
`newline_variants=True` already in place from Phase 89's fix: 15 candidates
-> 720 unique keystrings x all four oracle families x all four blobs, in
3m37s. **0 hits.**

Independently, `binary_key_material_backfill.py`'s Tier-2 sweep (launched
by a concurrent process, tracked since Phase 83/85/86/87/88/89 as it ran)
finished during this same window: checkpoint audited directly -- exactly
209,178 records, indices 0-209177 with zero duplicates, `hits` field sums
to exactly 0, no `binary_key_material_backfill.py` process still running.
The current code/candidate/blob/variant/source fingerprint recomputes to the
checkpoint header exactly, so this is not stale coverage. The run used 10,590
Tier-2 base candidates, expanded to 209,178 unique keystrings and
15,060,816 CBC/ECB decrypt operations, from 2026-07-27 09:09:12 +0300 to
11:34:22 +0300 (2h25m10s). No hits or API-queue file exists.

Tier-1/Tier-2 checkpoint sets overlap by 1,350 normalized keystring hashes:
the two standalone runs executed 734,614 keystrings total, while their exact
union is the documented 733,264 cumulative unique keystrings. Therefore the
combined executed total is 52,892,208 decrypt operations; the net unique
Tier-1-plus-Tier-2 coverage is 52,795,008 operations, with 97,200 harmless
repeat operations. Clean negative, matching Tier-1.

**Verdict:** the Fresco lead remains a clean negative across every form
tested so far (33 -> 40 -> 55 candidates, CBC/ECB/stream/Key-Wrap, all four
blobs, newline variants included). Tier-1 and Tier-2 of the separate
medium-curated-corpus binary-key-material sweep are both now complete and
clean as well.

## Phase 91 -- `-nopad` sweep: Phase 87's speed levers implemented (single-threaded only, per explicit scope) (2026-07-27)

Phase 87 identified and benchmarked two provable speed fixes for
`nopad_window_sweep.py` (29h -> ~6.5h Tier-1-scope estimate) but explicitly
did not apply them, pending a decision on scope. Asked again before
implementing: single-threaded fix only vs. also building the
multiprocessing layer -- chose single-threaded only (the multiprocessing
layer's new concurrent-checkpoint-write surface area stays deferred).

Implemented directly in `nopad_window_sweep.py` (not in
`binary_key_material_backfill.py` or `cb_common.py` -- both remain
byte-for-byte unmodified, confirmed by `stat` mtimes predating this work):

1. **`private_key_details` overridden with a coincurve-based
   implementation**, shadowing the name imported from
   `binary_key_material_backfill.py` (kept as
   `_reference_private_key_details` for the permanent parity test) via
   ordinary Python name resolution -- every existing call site
   (`check_decrypt`, `self_test`, etc.) picks up the fast version with no
   other code changes. `coincurve` is a genuinely new dependency this one
   script needs; no apt package exists, so it's pip-installed
   (`pip3 install --user --break-system-packages coincurve==21.0.0`,
   version 21.0.0) -- documented in the new `tools/gsmg/requirements.txt`,
   including the note that this contradicts `cb_common.py`'s own docstring
   ("this environment has no pip"), which is empirically outdated but was
   left alone (out of scope, and editing shared files remains something
   this investigation deliberately avoids). `requirements.txt` needed its
   own `.gitignore` fix: the blanket `*.txt` wordlist-exclusion rule was
   silently catching it too (a real dependency file, not generated wordlist
   data) -- added `!tools/gsmg/requirements.txt` alongside the existing
   `!README*.txt` exception, caught by checking `git status` before
   assuming the new file would actually be tracked.
2. **PBKDF2 derivation caching**, scoped to a fresh dict per keystring
   (not a module-level cache -- entries are keyed by (kdf_param, salt,
   passwd) so they're never reused across keystrings anyway; per-keystring
   scoping just avoids the dict growing unboundedly over a 525,436-keystring
   run, a design detail the Phase 87 throwaway benchmark didn't need to get
   right). `derive_key_iv` gained an optional `pbkdf2_cache` parameter
   defaulting to `None` (meaning "derive fresh, exactly the original
   behavior"), so `self_test`'s existing direct calls needed no changes.
3. **Checkpoint fingerprint extended** with a `coincurve` field (version +
   SHA-256 of the compiled `_libsecp256k1` backend .so), so a coincurve
   upgrade -- or a rebuilt backend under the same version string --
   invalidates a stale checkpoint the same way Phase 86 already made an
   edit to any source file do. Fingerprint version bumped 2 -> 3 (informational; `load_checkpoint`'s exact-dict-equality check would have
   caught the new field regardless).
4. **Parity tests promoted from Phase 87's throwaway benchmark into the
   permanent `self_test()`**, per the explicit pre-implementation
   requirement: `private_key_details` (coincurve) vs
   `_reference_private_key_details` (cryptography/OpenSSL) compared over 5
   edge cases (0, `SECP256K1_ORDER`, `SECP256K1_ORDER+1` all invalid; 1,
   `SECP256K1_ORDER-1` the valid boundary) plus 200 deterministic
   pseudorandom keys (a SHA-256 hash chain, not `os.urandom`, matching this
   file's established reproducibility preference from Phase 85's FILLER
   fix); and PBKDF2 cached-vs-direct output compared for *every* real
   variant in `ALL_CBC_VARIANTS`/`ECB_CIPHER_VARIANTS` (36 total), not a
   spot check.

Self-test passed clean on the first run after all changes. Re-validated:
`--limit 100` smoke run against the real 648-candidate corpus in 4.75s ->
21.07 keystrings/sec (vs. Phase 84's original 4.63/s baseline and Phase
87's 22.42/s benchmark projection -- consistent within normal run-to-run
variance). Projected against the real Tier-1 scope (525,436 keystrings):
**~6.93 hours**, matching Phase 87's ~6.5h estimate. `py_compile`, the
10-test suite, and `git diff --check` all pass.

**Verdict:** the single-threaded speed fix is implemented, self-tested, and
ready -- not yet launched against the real corpus (still no explicit
instruction to launch the actual multi-hour `-nopad` sweep, consistent with
this investigation's standing pattern of validating before committing
compute). Multiprocessing remains deliberately unbuilt.

## Phase 92 -- `-nopad` sweep: multiprocessing implemented, benchmarked, parity-verified (2026-07-27)

Built the multiprocessing layer Phase 87/91 deliberately deferred, per a
plan that went through an Explore pass (existing `multiprocessing` patterns
in this repo), a Plan-agent critique, and two rounds of direct user review
before implementation began -- each caught a real design gap, all folded
into the final approved plan (`~/.claude-personal/plans/reactive-conjuring-
engelbart.md`) before any code was written. Implemented entirely in
`nopad_window_sweep.py`; `cb_common.py`/`binary_key_material_backfill.py`/
`aes_key_wrap_sweep.py` remain byte-for-byte unmodified throughout
(confirmed via `stat` mtimes predating this work).

**Refactor first, verified behavior-preserving before adding anything new.**
`check_decrypt`'s classification logic was split into `evaluate_body`
(pure, returns hit dicts) and `evaluate_keystring` (the full 72-decrypt
inner loop for one keystring, pure) -- `check_decrypt` itself became a thin
wrapper calling `evaluate_body` then `record_hit`, so every existing
self-test call site needed no changes beyond threading `known_addresses`
explicitly (never read from the `KNOWN_GSMG_ADDRESSES` module global inside
these functions -- see below for why). Ran a semantic before/after diff
(`--limit 100`, comparing the *set* of completed `keystr_sha256` values,
since the checkpoint header's `driver_sha256` necessarily changes with any
source edit): identical. `sweep()`'s sequential path (`--workers 1`,
default) now calls the same `evaluate_keystring` the parallel path uses --
the two paths share one implementation of "what does the oracle check for
a keystring," so they cannot silently diverge.

**Every worker-relevant value is explicit data (`WorkerConfig`), never a
module global**, generalizing the exact lesson already learned once in
this repo (`test_cb_common.py::MultiprocessingTests.
test_9ary_config_survives_spawn`: an earlier `cosmic_sweep_9ary.py`
applied CLI config via global mutation before pool creation, which worked
under `fork` but silently used stale defaults under `spawn`). Bundles
`bloom_cache_path`, `bloom_identity`, `known_addresses`, `target_blobs`,
`cbc_variants`, `ecb_variants` -- stricter than strictly required for the
latter three (nothing mutates those after import today) but included so
the worker's computation has zero implicit dependency on module state
surviving any start method, and so a self-test can exercise a deliberately
*different* `known_addresses` through the real worker path. Production
runs under **explicit `spawn`** (not just tests, per direct user
instruction) via `ProcessPoolExecutor(mp_context=multiprocessing.
get_context("spawn"), initializer=_worker_init, initargs=(config,))` --
negligible one-time cost against a multi-hour run, removes an entire axis
of fork-vs-spawn reasoning.

**Bloom identity is verified inside each worker, not just assumed.**
`_worker_init` opens its own `BloomCache` (confirmed safe: read-only mmap,
multiple processes mapping the same file share physical pages via the OS
page cache, no locking needed) and compares its `.identity` against what
the parent already fingerprinted before the pool was created, raising if
they differ -- closes a race where the Bloom file could be replaced
between parent-side fingerprinting and a worker actually starting up.

**Structural chunk validation, not just trusting worker output.**
`_apply_chunk_results` compares the *set* of `(index, keystr_digest)` pairs
a worker actually returned against what was submitted -- same count, no
missing/duplicate/unexpected entries -- before writing anything; any
mismatch fails the whole chunk (nothing checkpointed, every digest logged)
rather than partially trusting an already-inconsistent result. Caught a
real bug in the first draft during design review: a naive per-keystring
loop inside `_process_chunk` would lose an *entire* chunk's otherwise-good
results if any single item raised, since nothing was ever returned. Fixed
by wrapping each keystring's own `evaluate_keystring` call in its own
try/except, always returning one `(index, keystr_digest, hits, error)`
entry per input item.

**Two distinct failure classes, handled differently, factored into
independently-testable helpers** (`_handle_future_result`,
`_apply_chunk_results`, `_drain_interrupted`) rather than inlined in the
dispatch loop:
- an ordinary per-item or whole-future failure -- logged (exception class
  name only, never `str(exc)`, since some library call could in principle
  echo a password candidate; never the raw keystring itself, only its
  digest), that item/chunk not checkpointed, the pool continues;
- `BrokenProcessPool` (the executor itself is dead, e.g. every worker's
  initializer failed) -- categorically different, caught separately: stop
  submitting, drain what's pending, exit non-zero, never treated as "just
  this chunk failed."

**Idempotent writes across resumes, per-artifact not per-hit.**
`record_hit` now accepts `seen_hit_ids`/`seen_queue_ids` (loaded once at
startup via `load_seen_ids`) and checks each independently -- a prior crash
could have written the sensitive hit record but not its queue entry (or
vice versa), so "hit_id already seen -> skip everything" would silently
leave a missing queue entry unrepaired on resume. Applies to *both* the
sequential and parallel paths (this idempotency gap already existed
single-threaded; multiprocessing just made it easier to hit, not new).

**Graceful interruption**: `KeyboardInterrupt` stops new submissions,
cancels every not-yet-started future (dropped silently -- a
`CancelledError` from a future *we* intentionally cancelled must never be
logged as a computation failure), and *drains* (waits for, then processes
normally) whatever was already running rather than discarding
completed-but-unwritten work, since chunks are short (~4.7s at the default
size). `_drain_interrupted`'s own self-test needed a real
`multiprocessing.Manager().Event()` to deterministically prove a
still-queued chunk stays cancellable -- an earlier version used a fixed
`time.sleep` delay and was observed to flake across repeated runs once
timing shifted; a bare `multiprocessing.Event()` (not Manager-backed) was
tried first and failed outright (`RuntimeError: Condition objects should
only be shared between processes through inheritance` -- confirmed
directly, not assumed), since `ProcessPoolExecutor` hands arguments to an
already-spawned worker via ordinary pickling, not the special bootstrap
`fork` inheritance relies on.

**Self-test additions** (all under real `ProcessPoolExecutor`s where the
property being tested requires one, not mocked): sequential-vs-parallel
parity on a synthetic known-hit scenario (compares full hit dicts,
including the coincurve-derived address itself, not just counts);
idempotent-write coverage (duplicate-hit and missing-queue-entry cases);
chunk-result-set validation (missing/duplicate/extra entries, each
independently); per-item chunk-error isolation (siblings of a failed
keystring still checkpointed); whole-future failure (a function that
raises before returning anything); broken-pool (a failing initializer,
correctly re-raised as `BrokenProcessPool` rather than an ordinary
failure); Bloom-identity mismatch (a real spawned worker refusing to
proceed); cancellation-vs-failure (a genuinely deterministic version, not
timing-dependent). Also caught and fixed, during implementation, a real
bug unrelated to any of the above: `_process_chunk` originally did
`dict(config.target_blobs)` where `target_blobs` is a tuple of 3-tuples
`(tag, salt, ciphertext)` -- `dict()` requires 2-tuples, raising
`ValueError` on every single chunk. Caught immediately by a `--workers 2`
smoke test before it ever reached the self-test suite; fixed by
precomputing the dict form once in `_worker_init` (also avoids
reconverting it on every one of a worker's many chunks over a long run).

**Benchmarked for real** (not assumed from the Phase 87 throwaway
estimate), same 5,000-keystring slice of the real 648-candidate corpus at
each worker count, run one at a time to avoid cross-run CPU contention:

| Workers | Time | Keystrings/sec | Speedup |
|---|---:|---:|---:|
| 1 | 219.1s | 22.82 | 1.00x |
| 4 | 57.3s | 87.26 | 3.82x |
| 16 | 29.6s | 169.04 | 7.41x |

16-worker scaling (7.41x) closely matches Phase 87's earlier ~7.75x
estimate -- confirming sublinear scaling at this core count is the real,
expected result on this machine, not a regression to chase. Projected
against the full Tier-1 scope (525,436 keystrings) at 16 workers: **~51.8
minutes**, matching the original ~48min projection. Checkpoint completion
sets were compared across all three runs and are byte-for-byte identical
(5,000/5,000 matching `keystr_sha256` values); all three produced zero
hits, consistent with every prior sweep against this corpus.

`python3 -m py_compile tools/gsmg/*.py`, the 10-test suite, and
`git diff --check` all pass.

**Verdict:** the multiprocessing layer is implemented, self-tested, and
benchmarked -- ready to launch the real Tier-1-scope `-nopad` sweep at
~52 minutes instead of ~29 hours (single-threaded) or ~7 hours
(single-threaded, optimized). Still not launched against the real corpus --
no instruction to commit that compute has been given yet, consistent with
this investigation's standing pattern.

## Phase 93 -- `-nopad` sweep multiprocessing: review caught two real dispatch-loop bugs and a test gap (2026-07-27)

A review of Phase 92 confirmed the core design sound (parent-only writes,
Bloom identity checks, worker config, result validation, cryptographic
parity) but flagged five issues in the dispatch loop itself. All five
independently re-verified by directly reading the actual code (and, for the
two substantive bugs, by reproducing them) before fixing anything.

1. **Missing replenishment on ordinary failure (Moderate, confirmed real).**
   `submit_next()` was only called after a successful chunk (inside the
   branch reached by `continue`-ing past `if chunk_results is None`), never
   after an ordinary whole-future failure. Enough failures could shrink
   `pending` to empty while chunks remained undispatched in `chunk_iter`,
   silently ending the sweep early. Fixed by moving `submit_next()` to run
   unconditionally after every completed future (success or ordinary
   failure alike) rather than being skipped by an early `continue`.
2. **Interruption drained only `pending`, not all of `future_to_chunk`
   (Moderate, confirmed real).** `KeyboardInterrupt` can land at any
   bytecode boundary, including mid-iteration over the `done` set from
   `wait()`. If it arrives after some futures in that batch were already
   popped and processed but before others were, those remaining ones are
   still keys in `future_to_chunk` yet are NOT in `pending` (which only
   reflects the not-yet-done set from the *last* `wait()` call) --
   `_drain_interrupted(pending, ...)` would silently lose their
   already-computed results. Fixed by draining `set(future_to_chunk)` (a
   superset of `pending` that also covers this window) instead.
3. **Double-shutdown-through-SystemExit in the broken-pool path (Low,
   plausible, fixed defensively).** `executor.shutdown(wait=False,
   cancel_futures=True)` followed by `sys.exit(1)` *inside* the `with
   ProcessPoolExecutor(...)` block means the `with` block's own `__exit__`
   performs a second `shutdown(wait=True)` on the way out. A direct repro
   (a real pool with a failing initializer, catching `BrokenProcessPool`,
   calling `shutdown(wait=False, cancel_futures=True)` then exiting the
   `with` block) did not reproduce a hang on this system, but the pattern
   is fragile regardless. Restructured: the broken-pool branch now
   re-raises `BrokenProcessPool` to unwind out of the `with` block cleanly
   (letting `__exit__` perform the one shutdown it always does), caught by
   a new `except BrokenProcessPool` wrapping the `with` block, which prints
   the summary and exits *after* the block has already closed.
4. **Stale module docstring (Low, confirmed).** Still said "Multiprocessing
   ... was explicitly NOT built" after Phase 92 built it. Updated.
5. **Test gap (confirmed, and instructive).** The self-test's failure
   coverage tested `_apply_chunk_results`/`_handle_future_result`/
   `_drain_interrupted` in isolation, never the real `_sweep_parallel`
   dispatch loop end-to-end -- exactly why bug 1 escaped. Fixed by
   refactoring `_sweep_parallel` to accept an optional `worker_fn`
   (defaulting to the real `_process_chunk`) and adding a genuine
   integration test that calls `_sweep_parallel` itself with a test-only
   `_process_chunk_test_intermittent` worker across many small chunks.

   Building this test surfaced two more of its own design mistakes, each
   caught by deliberately reintroducing bug 1 in a scratch copy and
   confirming the test's behavior changed as expected -- a discipline that
   paid off twice over:
   - First attempt: `_process_chunk_test_intermittent` returned per-item
     error markers within an otherwise-normal chunk result. That is NOT a
     whole-future failure -- it flows entirely through
     `_apply_chunk_results`, which was never the buggy code path. The test
     passed identically whether the bug was present or not (60/30 either
     way) -- a false sense of coverage. Fixed by making the function raise
     for the *entire* chunk instead, genuinely producing
     `chunk_results is None`.
   - Second attempt (still with a 2-in-3 success ratio, chunk_size=3,
     n_total=90): still passed with the bug reintroduced. The reason:
     `max_in_flight` (workers*4=16) primes 16 chunks upfront, and with
     enough *successful* completions among any dispatched batch, their own
     (correctly-firing) `submit_next()` calls end up pulling in every
     remaining chunk anyway, masking a bug that only skips replenishment on
     *failures*. Fixed by lowering the success ratio to 1-in-4 with an
     explicit assertion (`successful_chunks < total_chunks -
     max_in_flight`) documenting and enforcing the exact condition needed
     for the bug to be mathematically guaranteed to manifest, not left to
     chance. With this corrected, the test passes against the fixed code
     (24 completed, matching `8 successful chunks x 3`) and fails cleanly
     against a scratch copy with bug 1 reintroduced (18 vs expected 24,
     `AssertionError` on the exact line designed to catch it).

Re-validated: self-test passes, run 5 times in a row with no flakiness;
`python3 -m py_compile tools/gsmg/*.py`, the 10-test suite, and
`git diff --check` all pass; a real `--limit 500 --workers 4` run against
the actual corpus completes cleanly (500/500, 0 errors) in 9.3s.
`cb_common.py`/`binary_key_material_backfill.py`/`aes_key_wrap_sweep.py`
remain byte-for-byte unmodified.

**Verdict:** both real dispatch-loop bugs are fixed and now have dedicated
regression coverage that has been proven (not assumed) to catch them --
built by making the same mistake twice while writing the test itself, and
catching both by insisting on demonstrating the test against a
deliberately-reintroduced bug rather than trusting a passing run at face
value. Still not launched against the real corpus.

## Phase 94 -- `-nopad` Tier-1 sweep: real launch (clean negative) + vanity-substring classification added (2026-07-27)

Efficiency-vs-throughput tradeoff (per-worker efficiency drops from ~95.6%
at 4 workers to ~46.3% at 16, even as raw throughput keeps rising) led to
launching the real sweep at `--workers 8` rather than 16.

Launched the real, full Tier-1-scope sweep: `wordlists/gsmg/
medium_curated_tier1_primary.txt` (24,554 candidates -> 525,436 keystrings),
`--workers 8`, default checkpoint/hits/queue paths. Caught, before
launching, that the *default* candidate corpus (no `--candidate-file`) is
only 648 candidates / 14,551 keystrings -- a completely different, much
smaller set than "Tier-1 scope" -- confirmed directly via
`load_candidates(None)` vs `load_candidates(medium_curated_tier1_primary.txt)`
before committing to the real run.

**Result: 525,436/525,436 completed, 0 errors.** 6 Bloom-classification
hits surfaced during the run (`catalhiyikarchaeologistjamesmellaartwrote`,
`shoutingstoppreachingtorture`, `5456, and gypeans, $0 6; and Eve`,
`"as duality, 4, and gender, #9: and`, `unbelievable`, `imagehashtext`) --
all 6 verified via live Blockstream lookup
(`binary_key_material_backfill.py --verify-queue --queue
tools/gsmg/nopad_window_api_queue.jsonl`, reusing the existing generic
queue-verification tool rather than building a new one) as
`bloom_false_positive`: zero transaction history on every derived address.
Clean negative for the full pre-registered Tier-1 `-nopad` scope.

**Follow-up: vanity-substring classification.** The confirmed prize address
(`1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`) is a deliberately vanity-mined
address -- "GSMG1" right after the version byte (Phase 28). The existing
two-tier classification (known-address exact match, then Bloom membership)
has a blind spot: Bloom only covers addresses with real on-chain history,
so a never-funded vanity-mined target would be invisible to both checks.
Added a third, independent classification pass -- `VANITY_SUBSTRINGS =
("gsmg",)` / `vanity_matches()` -- run unconditionally (no Bloom cache
needed) on every one of the 7 window/combo candidates whenever no
known-address hit was found, alongside (not instead of) the Bloom pass.
Vanity hits are queued for the same mandatory API verification as Bloom
hits (neither is definitive alone) via `record_hit`'s `classification in
("bloom", "vanity")` queuing condition.

Rated this a plausible-but-unlikely bonus signal, not a strong prior:
vanity-mining the one final, known, publicly-reveal prize address is a
cheap one-time branding move; vanity-mining whatever key happens to fall
out of correctly decrypting SALPH/P32TRAILING would require the puzzle
author to have searched across passphrase/derivation combinations until
one produced a "gsmg"-containing address -- a much bigger imposition, not
needed since correctness there is already verified by hitting the known
address or a real funded one. Given the check is nearly free (the address
string is already computed; just an unindexed substring test), added it
anyway as a no-cost hedge rather than skipping it outright.

Added test coverage: since deriving a *real* key whose address genuinely
contains "gsmg" would require actual vanity mining, `self_test()` (section
4b) temporarily monkeypatches `private_key_details` (module-global
shadowing, restored both inline and in the shared `finally`, mirroring the
existing `KNOWN_GSMG_ADDRESSES` override pattern) to graft a synthetic
vanity-looking address onto one specific test key's real derivation,
exercising the classification/queuing logic itself rather than a mining
search. Verified: `evaluate_body` returns exactly one `"vanity"`-classified
hit for that key, and `check_decrypt` routes it to both the hits file and
the API queue with only the matching address_type. Explicitly scoped by
user decision to apply going forward only, not retroactively rescan the
525,436 keystrings the Tier-1 launch already completed under the
two-classification code (would cost another ~1h rerun for a
speculative-only signal). `python3 -m py_compile tools/gsmg/*.py` and the
full self-test suite (including the pre-existing multiprocessing
integration tests) pass.

## Phase 95 -- `-nopad` sweep: broader output-interpretation revision + reliability improvements (2026-07-27)

User-driven review of what could be improved in the sweeper, covering both
output-format gaps and operational reliability. Assessed each proposal
against the actual code before implementing rather than taking the list at
face value -- one item (vanity classification) turned out to require
replacing what Phase 94 had just shipped, not extending it.

**Vanity classification replaced, not extended.** Phase 94's `vanity_matches`
checked for "gsmg" as an unanchored substring anywhere in the address
(case-insensitive). Replaced with `VANITY_STRONG_RE = re.compile(r"^1GSMG1")`
and `VANITY_WEAK_RE = re.compile(r"^1GSMG[1-9]")`, anchored right after the
fixed "1" P2PKH version-byte character -- exactly how the real prize
address (`1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`) was actually vanity-mined
(prefix mining is what standard tools search for; an arbitrary embedded
substring is a categorically more expensive, non-standard search).
Classifications renamed `vanity_strong`/`vanity_weak`; both still queued
for mandatory API verification like a Bloom hit (neither tier is treated
as confirmed on its own). Since this was never run against the real
corpus (Phase 94's `--don't rerun the completed portion` scope decision
meant the substring version never actually executed against Tier-1
data), there was nothing to invalidate by swapping it out.

A follow-up review caught a real arithmetic error in this phase's initial
base-rate estimate for the anchored check: the first draft used "~7.35M
candidate x address_type checks" as the Tier-1 scale, which only accounts
for one check per keystring and omits the x72 decrypts/keystring factor
entirely. The correct volume is per DECRYPT: 525,436 keystrings x 72
decrypts/keystring x 8 always-present structural candidates (4 windows + 4
combos) x 2 address formats = **~605.3M address checks** -- independently
re-derived and confirmed to match the review's own figure exactly. At that
real volume, expected coincidental hits are far from negligible: strong
("^1GSMG1") = 605.3M x 58**-5 ~= **0.92** (a ~60% chance of at least one
across a full run); weak-only ("^1GSMG[2-9]") = 605.3M x 8/58**5 ~= **7.38**.
Corrected in both `FINDINGS.md` and the `VANITY_STRONG_RE`/`VANITY_WEAK_RE`
code comment. Practical consequence: neither tier is independently
compelling at this volume -- a strong- or weak-tier hit surfacing during
the real run is a candidate filter requiring passphrase/context review,
not confirmed evidence, exactly like a Bloom match (the anchored redesign
is still a real improvement over the unanchored version -- which would
have had a substantially higher rate still and was never run against the
real corpus -- just not the "near-zero" reduction originally claimed).

The same review caught two further real bugs, both fixed and independently
reproduced before and after the fix:

* **WIF compression semantics were ignored.** A WIF string's compression
  flag is an assertion about which pubkey format it is for -- real wallet
  software given a compressed WIF only ever derives the compressed
  address. `evaluate_body` was checking BOTH address types regardless of
  which the WIF candidate's own encoding specified. Reproduced directly: a
  compressed WIF embedded in a synthetic body matched a KNOWN
  *uncompressed* address (of the same underlying scalar) and was reported
  as a "known" hit -- a real false-positive-classification risk, since a
  holder of that literal WIF text would never have derived that address at
  all. Fixed via a new `_allowed_address_types(source)` helper: for
  `wif@offset:compressed`/`wif@offset:uncompressed` sources, matching is
  now restricted to only that address_type (the full `details` dict is
  still stored in the hit record for context; only the match/classification
  logic is restricted). Re-verified: the same repro now correctly produces
  no hit, while the matching-compression-type and matching-address-format
  cases still correctly fire.
* **Vanity hits were mislabeled during API verification.** The shared
  `binary_key_material_backfill.verify_pending_queue` has no concept of
  "vanity" -- it labels any address with no on-chain history
  `bloom_false_positive`. For a vanity-tier hit this is actively
  misleading: a vanity-mined address is *expected* to often be unfunded
  (mining costs nothing; funding is a separate, optional step), so "no
  transaction history" is not evidence the vanity match itself is wrong
  the way it is for an actual Bloom coincidence. Fixed by (a) adding a
  `classification` field to the queue record (`record_hit`) so a vanity-
  sourced entry is traceable downstream, and (b) a new
  `relabel_vanity_verifications(queue_path)` function (exposed via
  `--relabel-vanity-queue`) that, run AFTER the shared verify-queue tool,
  rewrites any vanity-classified entry currently showing
  `bloom_false_positive` to `unfunded` via a new append (matching the
  existing append-only/latest-wins queue convention) -- it makes no API
  calls of its own, only relabels an already-recorded result. Real
  funded/used-empty findings are left untouched either way. The CLI path
  (`main()`'s `--relabel-vanity-queue` branch) acquires the same
  `acquire_run_lock` on the queue file `sweep()` would -- a review pass
  flagged that the initial version didn't, leaving a real window for a
  concurrent sweep or a second relabel invocation to interleave writes to
  the same queue file; verified fixed (a lock held on the queue path
  correctly makes a concurrent `--relabel-vanity-queue` invocation refuse
  to start, exit code 1).

**Operational note for the eventual Tier-1 rerun**: must use new,
Phase-95-specific checkpoint/hits/queue paths, not the defaults -- the
existing default checkpoint carries the pre-Phase-95 driver fingerprint
(so it would be rejected/rebuilt anyway) and the existing default hits
file contains the 6 Phase-94 false-positive records, which would
contaminate the classification-count totals in the new run's summary
footer if reused.

**Lock scope**: `acquire_run_lock` originally protected only the
checkpoint path. Since a checkpoint/hits/queue trio is not required to
share a common path prefix, two runs using different checkpoint paths but
the same hits/queue file could still interleave writes to those. Fixed:
`acquire_run_lock` now accepts all three paths, locks each distinct one
(so a collision on any single shared artifact is caught, not just an
identical checkpoint path), and releases all of them together.

**Two new encoded-key candidate sources**, closing genuine format gaps in
the prior raw-binary-window-only reading:

* `hex_window_candidates(body)`: recognizes a private key written out as 64
  ASCII hex characters, at the two 16-byte-block-aligned offsets (0, 16)
  that can fit a 64-byte span in the 80-byte body. Not a sliding scan --
  bounded to those two positions, and the ASCII-hex charset requirement is
  itself a strict structural filter (all 64 bytes must decode as hex
  digits, probability ~(22/256)**64 by chance).
* `wif_window_candidates(body)`: recognizes a private key written out as a
  Base58Check WIF string (51 chars uncompressed / 52 compressed). Scans
  every fixed-length ASCII substring of the 80-byte body (<=59 positions,
  not open-ended) and keeps only the ones whose Base58Check checksum
  actually verifies (~2**-32 false-accept rate) -- the checksum, not the
  scan itself, is the real bound, playing exactly the role the removed
  PKCS7 pad used to play for the padded hypothesis. Required writing a
  `base58check_decode`/`BASE58_ALPHABET` pair from scratch -- no decode
  counterpart existed anywhere in this codebase (only `base58check`
  encoders, in `first_hint_hash_audit.py` and via
  `binary_key_material_backfill.base58check`).

Both wired into `evaluate_body`'s `all_candidates` list, so they flow
through the existing known/vanity/Bloom classification pipeline unchanged.
Verified round-trip against a real key (encoded as WIF at an arbitrary
offset, and as hex at both block-aligned offsets) before writing formal
self-tests, and added dedicated self-test coverage (section 3c) reusing
the existing "known key" override technique to confirm `evaluate_body`
correctly classifies a hex- or WIF-encoded known key as `"known"`.

**One new combo candidate**: `combo_candidates` gained `"xor"` (bytewise
XOR of the two clue-supported windows) alongside the existing
`scalar_sum`/`concat_hash_ab`/`concat_hash_ba`. Rated more directly tied to
this investigation's repeatedly-recurring "half and better half"/binary-
duality framing than the existing combos, and costs nothing extra to
compute. Deliberately not extended to a broader bitwise/arithmetic family
without a specific clue, to keep this bounded (per explicit scope
instruction: "avoid additional ciphers, sliding binary windows, arbitrary
masks, or broad key-combination families").

**Reliability improvements**, addressing gaps confirmed against the actual
code (not assumed from the proposal alone):

* `acquire_run_lock(*paths)`: exclusive, non-blocking `flock` on a dedicated
  sibling `.lock` file for EACH distinct path given (not the paths
  themselves, so it works even before those files exist), held for the
  run's duration via the returned handle -- the OS releases every flock
  automatically on process exit, however the process exits. `sweep()`
  passes all three of checkpoint/hits/queue (not just the checkpoint),
  since a shared hits or queue file across two different checkpoint paths
  is exactly the kind of collision locking only the checkpoint would miss
  -- see the "Lock scope" note below. Confirmed nothing previously stopped
  two `sweep()` invocations against the same output files from
  interleaving writes; verified experimentally (a real background sweep +
  a concurrent second invocation against the same checkpoint correctly
  refused with a clear error and exit code 1) as well as via dedicated
  self-tests (single-path acquire/reject/release/reacquire; multi-path
  collision on a shared hits file despite different checkpoint paths;
  duplicate-path dedup; partial-acquisition release on failure).
* `load_checkpoint` now tolerates exactly one truncated/malformed line --
  and only if it is the very last line: a hard kill (OOM, power loss,
  `kill -9`) mid-write can only ever leave a fragment at the tail, since
  every earlier line was already a completed, flushed `append_jsonl()`
  call before that one started. Corruption anywhere else still raises.
  Self-tested both branches (a truncated final line is quarantined with a
  warning; the same corruption placed mid-file still raises `ValueError`).
* `audit_completion(checkpoint_path, keystrings)` and
  `classification_counts(hits_path)`, plus a `sweep()`-level completion
  summary (fingerprint, elapsed time, resumed/session/missing/duplicate
  counts, classification tallies) printed after every run -- including
  runs that exit non-zero (errors, or an interrupt): `sweep()` now catches
  the `SystemExit` `_sweep_parallel` raises on those paths, prints the
  summary anyway (this is exactly when it's most useful), and re-raises
  the original exit code afterward, rather than skipping the summary on
  any non-clean exit. `audit_completion` counts digests rather than
  collapsing them into a set, so a duplicate (never expected in normal
  operation) is detected instead of silently hidden.
* Progress reporting (`_format_progress`, shared by both the sequential and
  parallel dispatch paths) now reports percentage of total scope (resumed +
  session, not just this session's slice), session-only throughput and
  ETA (resumed items are excluded from the rate calculation -- they were
  not redone this run, so counting them would inflate it), and an explicit
  resumed/session split.

Verified end-to-end, not just via unit tests: a real `--limit 300`
sequential vs. 4-worker run produced byte-for-byte identical checkpoint
completion sets (parity intact after adding the new candidate sources); a
real 3,000-keystring single-threaded benchmark measured 19.4 keystrings/sec
(down from Phase 91/92's 21-22/sec baseline -- an honest ~10% cost from the
added WIF/hex scanning per body, a reasonable tradeoff for closing genuine
format gaps, not a regression to investigate).

`python3 -m py_compile tools/gsmg/*.py` and the full self-test suite
(including the new sections 3b/3c/8/9/10 and the pre-existing
multiprocessing integration tests) pass.

**Not implemented, per explicit scope instruction**: no additional ciphers,
no sliding search over raw binary windows, no arbitrary bitmasks, no
broader key-combination families beyond the one XOR addition. This was
implemented as one bounded revision and not yet re-run against the full
Tier-1 corpus (the recommended next step, per the proposal that motivated
this phase) -- left for a deliberate follow-up run, not folded into this
same session.

## Phase 96 -- case-sensitive `SalPhaseIon -> SalVATIon -> SALVATION` rebus audit (2026-07-27)

The bird-view review identified a typography-level relation that previous
lowercased candidate and cipher sweeps had not documented:

```text
Sal PHASE Ion
Sal VAT   Ion
SALVATION
```

`tools/gsmg/salphaseion_title_rebus_audit.py` verifies the load-bearing
sources independently:

- the archived HTML heading is exactly case-sensitive `SalPhaseIon`;
- creator message `8446` is a complete 1,288-bit stream whose whole-stream
  reversal decodes exactly to the authenticated macro clue, including
  `verylaststepisatruegiveawaypromised`;
- the string difference from `SALPHASEION` to `SALVATION` uniquely fixes
  `PHASE -> VAT`, rather than selecting `VAT` from a dictionary;
- the frozen screenplay contains all five connected phrases:
  `both beginning and end`, `salvation of Zion`, `the problem is choice`,
  post-choice `But`, and being blinded from the simple and obvious truth.

The final clause was evaluated under one declared four-reading family:

```text
full initials:                         VLSIATG
full finals:                           YTPSAEY
Very + A True Giveaway initials:       VATG
same, obeying literal "give away" G:   VAT
```

Only the self-referential final reading produces the replacement fixed
independently by the title difference. This is a coherent rebus, but its
reading family was motivated after noticing the title relation; it is not a
formal discovery p-value or proof that the output is a password.

A focused oracle check kept the candidate family fixed to:

```text
VAT
SalVATIon
SALVATION
SALVATION OF ZION
THE SALVATION OF ZION
```

Through `answer_forms()` and `keystr_forms(newline_variants=True)`, these
produce 117 unique raw, SHA-256, double-SHA-256, LF, and CRLF keystrings.
Tested against SALPH, COSMIC, P32TRAILING, and quarantined URLBLOB under:

- original and extended CBC/KDF variants;
- AES-ECB;
- AES-CFB/OFB/CTR;
- RFC 3394/5649 AES Key Wrap, including the existing OpenSSL-IV branches.

Result: **zero hits in every family**.

**Verdict:** promote `PHASE -> VAT -> SALVATION` as the strongest currently
available case-sensitive recognition/transition rebus. Do not promote it as a
direct blob password: that bounded interpretation is now cleanly negative.
The remaining question is what typed page operation or rail choice consumes
the recognized `SALVATION` state. The next foreground audit should therefore
model instruction/operand binding in the authenticated SalPhaseIon stream,
not expand the password or cipher family.

## Phase 97 -- elemental `SALPHATION -> SALVATION` reproduces `[23,16,7]` exactly (2026-07-27)

Follow-up on Phase 96 found a much stronger, matrix-connected route and caught
an existing community error.

Telegram message `55462` (community member `X`, 2026-01-10) claimed:

```text
SalPhaseIon = S Al P H As Se I O N
```

That parse is invalid: concatenating those symbols gives
`SALPHASSEION`, with an extra `S`. Exhaustive dynamic-programming
segmentation over all 118 current element symbols confirms that the exact
archived heading `SalPhaseIon` has **zero** complete element parses.

The creator's own exact wording in message `6497` is different:

```text
Breaking salphation, should be giving the feeling of the phase's name.
```

Both the creator's `SALPHATION` and the target `SALVATION` have unique,
complete elemental parses:

```text
SALPHATION = S  Al P  H At I  O N
numbers     = 16 13 15 1 85 53 8 7   (sum 198)

SALVATION  = S  Al V  At I  O N
numbers     = 16 13 23 85 53 8 7     (sum 205)
```

The transformation is exactly `PH -> V`. Its atomic-number accounting is:

```text
new middle:      V = 23
old middle:  P + H = 15 + 1 = 16
difference:     23 - 16 = 7
```

Therefore:

```text
[new, old, difference] = [23,16,7]
```

This is the exact `matrixsumlist` independently reconstructed in Phase 32
from the first-piece prime `574061`, in the same order. No alphabet search,
indexing convention, or score optimization is involved.

Two adjacent page dimensions also line up:

```text
SALVATION element count  = 7;  7 x Al(13) = 91  = raw DBBI length
SALPHATION element count = 8;  8 x Al(13) = 104 = binary("matrixsumlist") length
```

The second equality partly reflects the already-authenticated 13-character
instruction encoded as eight bits per character, so it is supporting
geometry rather than an independent probability claim. The load-bearing
finding is the unique `PH -> V` element substitution reproducing the already
fixed `[23,16,7]` list exactly.

`tools/gsmg/salphaseion_title_rebus_audit.py` now asserts:

- the invalid historical title parse remains impossible;
- both creator-word and target parses are unique;
- `P+H -> V` yields `[23,16,7]`;
- `7x13=91` and `8x13=104` match the authenticated adjacent stream lengths.

**Verdict:** this supersedes the VAT-only route as the strongest mechanical
explanation of what `matrixsumlist` consumes. The two readings still converge:

```text
visible title:  Sal[PHASE]Ion -> Sal[VAT]Ion -> SALVATION
creator phrase: SAL[PH]ATION  -> SAL[V]ATION   -> SALVATION
```

The atomic route removes the weakest part of the title rebus: `V` is selected
by the already-reconstructed `[23,16,7]`, not merely recognized in the final
clue wording. Phase 96 already proves `SALVATION` and its immediate phrase
forms do not directly open any tracked blob under current CBC/ECB/stream/Key
Wrap coverage. Treat `SALVATION` as a now-strongly-grounded reached state or
typed operand. The next question is where the page grammar applies that state,
not how to generate more password spellings.

## Phase 98 -- creator-corpus base-rate audit downgrades the atomic-number match (2026-07-27)

Phase 97's exact string and element parses are valid, but its evidentiary
wording was too strong. The `[23,16,7]` match was recognized after that target
was already known, so the generic atomic-number component required a base-rate
audit before it could count as corroboration.

`tools/gsmg/salphaseion_title_rebus_audit.py` now exhaustively audits every
distinct alphabetic word type in all 482 creator messages from the Telegram
export. It uses the complete set of 118 element symbols and exact dynamic
programming segmentation. The primary unit is a deduplicated word type, so
repeated creator vocabulary does not inflate the rates.

| Corpus profile | Element-parsable | Any contiguous sum-16 span | Exact consecutive `P,H` | `PH -> V` gives fixed `SALVATION` |
|---|---:|---:|---:|---:|
| All lengths | 313 / 1,312 | 107 / 313 (34.185%) | 6 / 313 (1.917%) | 1 (`salphation`) |
| Exact length 10 | 5 / 50 | 2 / 5 (40.000%) | 1 / 5 (20.000%) | 1 (`salphation`) |
| Length 8--12 | 29 / 266 | 18 / 29 (62.069%) | 1 / 29 (3.448%) | 1 (`salphation`) |

The generic `P+H=16`-shaped arithmetic is common in this corpus and cannot be
used as independent confirmation. The exact consecutive `P,H` event is much
narrower, and the complete lexical transformation to the independently fixed
word `SALVATION` is unique in the audited creator vocabulary. That uniqueness
is descriptive rather than a formal discovery p-value because the target word
and operation were recognized post hoc.

**Corrected verdict:** retain the exact
`SALPHATION -> SALVATION` lexical convergence and both unique element parses
as a suggestive creator-linked rebus. Downgrade the `[23,16,7]` arithmetic from
a strong mechanical explanation to a post-recognition checksum. Phase 96's
zero-hit oracle result is unchanged, and this audit does not justify a new
password, cipher, or transform sweep.

## Phase 99 -- scheme sensitivity and the degenerate creator-word control (2026-07-27)

A follow-up proposed applying the same split-and-difference operation to other
element-parsable creator words. Exhaustive enumeration reveals why that is not
an independent arithmetic null: all six creator word types containing the
exact consecutive elemental tokens `P,H` are:

```text
ciphers  cypher  phone  phrases  salph  salphation
```

Under the proposed `PH -> V` operation, every one necessarily gives the same
atomic arithmetic:

```text
P + H = 16; V = 23; delta = 7
```

The word choice therefore cannot vary the numeric result once both the
periodic-table scheme and `PH -> V` substitution have been selected. Their
literal replacements are `civers`, `cyver`, `vone`, `vrases`, `salv`, and
`salvation`; only the last reaches the independently fixed target word. This
supports the lexical specificity already reported in Phase 98, but does not
create six independent confirmations of the arithmetic.

A separate, pre-declared sensitivity family applied five common letter-value
schemes to the exact same fixed split:

| Scheme | `P+H` | `V` | `V-(P+H)` | Exact `[23,16,7]` |
|---|---:|---:|---:|---:|
| Atomic number | 16 | 23 | 7 | yes |
| A1Z26 | 24 | 22 | -2 | no |
| Uppercase ASCII | 152 | 86 | -66 | no |
| English Scrabble | 7 | 4 | -3 | no |
| Phone keypad | 11 | 8 | -3 | no |

This rules out the narrow objection that any standard letter-value convention
would reproduce the tuple. It does **not** establish a discovery probability:
the space of possible encodings is open-ended, and no creator-authored
chemistry or periodic-table clue has yet been identified.

**Verdict:** the atomic scheme is distinctive within this small conventional
family, while the exact lexical transformation remains unique in the complete
creator corpus. Neither result removes the post-hoc scheme-selection cost.
Keep the route suggestive and bounded; do not promote it to an established
operation or launch another oracle sweep without independent chemistry
provenance.

## Phase 100 -- Tier-1 `-nopad` queue verified; zero funded or known addresses (2026-07-27)

The completed Phase-95-scope rerun was independently resumed through
`nopad_window_sweep.py` using its original candidate, checkpoint, hits, and
queue paths. Its own fingerprint and completion audit reports:

```text
candidates=24,554
keystrings=525,436
operations/key=72
resumed=525,436
total=525,436
missing=0
duplicate_digests=0
classifications: bloom=6, vanity_strong=3, vanity_weak=14
```

All 23 unique queued addresses were then checked through the live Blockstream
API using the existing mandatory verification path:

- all 6 Bloom classifications were confirmed `bloom_false_positive`;
- all 3 strong and 14 weak anchored vanity classifications were unfunded;
- none matched an established prize or halving address.

The vanity records were relabeled from the shared verifier's generic
`bloom_false_positive` status to `unfunded`, preserving the distinction
between a real Bloom collision and a merely unused vanity-shaped address.
Final latest-state counts are:

```text
6  bloom / bloom_false_positive
3  vanity_strong / unfunded
14 vanity_weak / unfunded
```

**Verdict:** Tier-1 is a complete clean negative for the bounded no-padding
window, encoded-key, and clue-supported combination family. The observed
Bloom and vanity counts are candidate-filter events, not decryptions or puzzle
hits; mandatory blockchain verification rejects every one.

## Phase 101 -- typed page grammar remains underdetermined; `anstoo` correction (2026-07-27)

`tools/gsmg/salphaseion_operand_binding_audit.py` imports the authenticated
byte-exact segmentation from `page_structure_audit.py` and audits operand
scope without running transforms or using AES success as a selector.

The fixed local facts are:

```text
DBBI [matrixsumlist] FAED
FAED [lastwordsbeforearchichoice] [thispassword]
[sha256 our first hint is your last command] [SALPH blob]
[shabefanstoo]
```

Binary `enter` uniquely reconstructs the two 64-character Base64 halves and is
treated as formatting, as established previously. The remaining instruction
roles are not unique:

- `matrixsumlist`: postfix to DBBI, prefix to FAED, or infix between both;
- `lastwords...` / `thispassword`: password for FAED, FAED answer labeled as
  password, or password for the following SALPH blob;
- SHA operand: explicit `first hint == last command`, preceding password
  result, or preceding phase answer;
- suffix: literal unresolved `anstoo`, or community-expanded `answer too`.

This closed family contains `3 x 3 x 3 x 2 = 54` models. Twenty-seven are
structurally total only if `anstoo -> answer too` is accepted. None is strictly
supported without either leaving `anstoo` unresolved or adding an unsupported
operand override.

This audit also caught an existing metadata overstatement:
`page_structure_audit.py` labeled the suffix decode as `sha256 answer too`.
Only `shabef -> sha256` is mechanical under the established mixed
letter/digit convention. The remaining raw bytes spell `anstoo`; “answer too”
is a community guess. The structure metadata now records
`sha256 + unresolved literal anstoo`.

The full creator export contains no creator-authored occurrence of `anstoo`,
`answer too`, `shabef`, “our first hint,” or “your last command.” The only
creator reply directly tied to a request about the last-command clue is message
`20224`: `🤐`. Community messages propose several incompatible readings,
including “answer too,” Neo's response, concatenation with the Architect
phrase, and octal. None selects a grammar.

Finally, `SALVATION`, `VAT`, and `SalPhaseIon` do not occur in the decoded
textarea instructions. The Phase-96--99 rebus therefore cannot be inserted as
a typed operand from local page syntax.

**Verdict:** no unique typed program is recovered. The next foreground task is
provenance recovery for literal `anstoo` and the SHA operand relationship, not
another transform family or an AES-selected choice among the 54 models.

## Phase 102 -- `anstoo`/SHA-operand provenance audit: no new lever, genuinely unresolved (2026-07-27)

`tools/gsmg/anstoo_provenance_audit.py` follows up on Phase 101 directly. It
runs no transform, cipher, or AES check; it only verifies, fresh against the
complete 2026-07-26 Telegram export, what the creator and the community have
actually said about `anstoo` and the SHA-prefix operand.

**Creator engagement is a single, explicit non-answer.** Message `20222`
(Charlie Craig, 2024-01-26) directly asks the creator for a hint on "our
first hint is your last command." The creator's reply chain is:

- `20223`: "Regular Bitcoin Private key" (answers a different question, about
  final answer format, asked immediately prior in `20221`);
- `20224`: a bare zipper-mouth emoji, in direct reply to `20222` -- an
  explicit decline, not a missed message;
- `20226` (Charlie Craig, immediately after): asks who "our" refers to in the
  hint. **Never answered anywhere in the export.**

Across the complete 57,729-message export, the creator's own account
(`user9815232`) never once uses the word `anstoo` and never discusses "first
hint" or "last command" outside this single decline. This is checked by full
scan, not sampling.

**93 community messages mention `anstoo`**, none creator-confirmed. Surveyed
readings: literal expansion (`answer too` / `answer to` / `at soon`), direct
AES passphrase attempts (`sha256("MatrixSumList\nAnsToo")`, self-reported bad
decrypt), A1Z26/OEIS lookup (Denis Golovkin, message `50651`:
`isAlphation("anstoo") -> "a 14 19 20 o o" -> oeis.org/A141920`), a BB84
numerology reading (Robby, message `60177`: A1Z26 sum `=84`), an anagram
claim (Cereal Killer, message `52238`: "BATH OF ONE ASS"), and a structural
21-row grid-split claim. None carries independent creator-authored
motivation for its specific encoding scheme, matching this project's
standing base-rate concern about post-hoc letter-value schemes (Phase 98/99).

**The one structurally concrete claim was already challenged and walked back
inside the community itself**, without this project's involvement. Vasilis
Dragon (message `66727`, 2026-07-13) claims the (already-established)
`{1,4,21}` "second door" hint splits SalPhaseIon into exactly 21 rows, with
row 1 = `dbbi`, row 21 = `anstoo`, row 4 = a `faed` sub-range. Rafael Gomes
(message `66744`) immediately asks for the exact rule producing all 21 row
boundaries, noting his own source has only 3 logical lines and that "row 4"
isn't stable without one. Vasilis Dragon's reply (`66747`) backs off the
strong reading: "dbbi and anstoo aren't page/verifier hits, they're
already-decoded salphaseion components... not verified receivers" -- i.e.
concedes there is no 21-row split, only two already-known decoded fragments.
No rule was ever supplied. This audit records that exchange rather than
attempting to reconstruct a 21-row grid no one -- including its proposer --
can specify.

**One real, checkable structural fact confirmed:** Diego Schmidt's
(messages `65298`, `66365`) claim that concatenating the six known decoded
instruction fragments --
`matrixsumlist`+`lastwordsbeforearchichoice`+`thispassword`+
`shabefourfirsthintisyourlastcommand`+`enter`+`shabefanstoo` -- gives exactly
**103 characters** is arithmetically exact (13+26+12+35+5+12=103), verified
directly, not from the quoted claim alone. His further claim that this lands
"precisely at FEFEFE when filled row by row" was not independently
verifiable: it depends on an unspecified grid width/fill rule he never made
explicit, unlike the already-established, exactly-specified spiral read from
Phase 0. Recorded as a real but currently untestable structural observation,
not pursued further absent a concrete rule.

**Verdict:** no new operand-scope or `anstoo` lever survives this audit.
`anstoo` remains a genuinely unresolved literal -- the creator export
supplies no confirmation either way, and the one concrete-looking community
claim was already falsified for lack of a reproducible rule by another
community member's own scrutiny. This closes the provenance-recovery task
Phase 101 recommended; it does not open a new transform or AES sweep. If
revisited, the only legitimate next input would be a real, independently
specified rule for the 103-character/196-cell geometry Diego Schmidt
observed, not another guess at what `anstoo` "should" mean.

## Phase 103 -- `SALVATION` functional-role audit: two roles closed, one bounded negative, one open (2026-07-27)

Phase 101 found `SALVATION`/`VAT`/`SalPhaseIon` absent from the decoded
textarea instructions, so the rebus cannot be inserted as a literal operand
from local page syntax. `tools/gsmg/salphaseion_salvation_role_audit.py`
asks a narrower question instead: independent of literal occurrence, could
the *recognized state* `SALVATION` still function as one of four named
grammatical roles? No new cipher, transform, or password sweep was run; each
role either reduces to an already-completed result or a structural fact
verified directly against the archived page.

- **replacement_state** (direct password/passphrase input): re-verifies
  Phase 96's candidate set still covers `SALVATION`/`VAT` and cites its
  already-completed result -- 117 keystrings, 4 blobs, **0 hits**. Closed
  negative.
- **sha_operand** (the value the explicit SHA command hashes, feeding the
  SALPH AES halves): verifies structurally that `salphaseion_aes_prefix` and
  `salphaseion_aes_suffix` are exactly the first and second 64-character
  halves of the one already-tracked SALPH blob. This role targets identical
  ciphertext to `replacement_state`, so it inherits the same 0-hit result
  rather than requiring a new test. Closed negative.
- **rail_selector** (choosing between the `BUT`/`HYE` rails from Phase
  33/34): a plain letter-presence check, no oracle needed. `SALVATION`
  shares zero letters with `HYE` and only `T` with `BUT` -- no subsequence,
  anagram, or literal-presence rule can use it to select between the two
  rails. **Bounded negative for that declared family only.** This does not
  exclude an independently specified numeric or semantic selector.
- **checksum** (the decrypted SALPH plaintext should read like "salvation",
  matching message `6497`'s "breaking salphation should be giving the
  feeling of the phase's name" -- SALVATION as a recognition signal on the
  *output*, not a typed input): honestly reported as **open and currently
  unfalsifiable**, not promising. Confirming or denying it requires already
  having the correct SALPH password to inspect the resulting plaintext, and
  no decrypted SALPH plaintext exists on record. This is a property that
  could only ever be noticed after an unrelated password is found by other
  means -- it does not itself justify a new sweep.

**Verdict:** two roles close under the exact Phase-96 tested forms
(`replacement_state`, `sha_operand`), the literal rail-selector family is a
bounded negative, and checksum remains open/untestable. No chemistry,
numerology, or new AES coverage was needed or added. This does not establish
that every conceivable selector or checksum role is closed.

## Phase 104 -- dual-channel consistency audit: a real dependency chain, but not one conserved dual channel (2026-07-27)

`tools/gsmg/dual_channel_consistency_audit.py` tests the bird-view document's
promoted priority-#1 question: does one consistent left/right or
beginning/end assignment survive the seven listed "dual" artifacts (yellow/
blue, the two matrix rows, `16+7`, `BUT`/`HYE`, the two SALPH Base64 halves,
"half and better half", and the two textareas), or does the model fail? No
new cipher, transform, or password sweep was run. Each pair's poles were
re-derived fresh from already-verified code (`page_structure_audit.py`,
`prime_matrixsum_reconstruction.py`, `first_piece_color_reconstruction.py`),
and cross-links between pairs were checked only against citable FINDINGS.md
phases, never invented.

**Result: four real dependency edges exist, but they do not preserve two
poles.** Yellow-one yields prime `574061`; that prime yields matrix rows
`[5,7,4]`/`[0,6,1]`; their sums and total yield `23/16/7`; those positions
select `BOTH`/`ULTIMATELY`/`THE`, whose beginnings/endings yield `BUT`/`HYE`.
The complementary blue-one rose value has no established consumer, and
both rails use all three selected positions, so this is a real chain but not
a conserved yellow/blue or row-1/row-2 channel.

The fourth edge is the already-established rail-to-escape relationship:
filtering `BUT`/`HYE` to `a`-`i` symbols gives `b`/`he`;
`mirror9('b') == 'h'` with `e` as the fixed center (Phase 34, re-verified
here). `b` is `dbbi`'s real, decisively-fitted escape pair `{b,e}`; `h`
gives `faed`'s *mirror-hypothesis* pair `{h,e}` -- not `faed`'s own
best-fit pair, which is `{g,i}`. So `B` consistently associates with `dbbi`
and `H` with `faed`'s mirror hypothesis specifically, and this does not flip
anywhere in its own derivation chain.

**"Half and better half" is not one settled pair -- it has two incompatible
prior readings in this project's own history.** Phase 78 (currently
operational in the binary-key-material sweep machinery) reads it as two
32-byte private keys packed into one 80-byte decrypted plaintext -- an
internal structure of a single blob, not a SalPhaseIon/Cosmic pairing.
A separate community theory (bitkek, message `60359`: "half = phase 3.2.2
AES / better half = cosmic duality") was tested directly as an AES
passphrase in Phase 54 and came back negative. Adopting the second reading
to bridge this pair to the `SalPhaseIon`/`Cosmic Duality` textarea pair
would mean preferring an already-falsified reading over the one this
project's own tooling currently operates on.

**Verdict:** the dual-channel model, as framed across all seven pairs,
fails because the established dependency chain is asymmetric and
many-to-many rather than one stable two-pole mapping. This does not license
inventing bridges to the SALPH halves, “half and better half,” or the two
textareas. No further chemistry, numerology, or password sweep follows from
this audit alone.

## Phase 105 -- `SALVATION` as a 3x3 letter matrix: real structural fact, oracle negative (2026-07-27)

User-proposed extension of the title/rebus thread: `SALVATION` has exactly
9 letters, splitting evenly into three 3-letter rows `SAL`/`VAT`/`ION`.
`tools/gsmg/salvation_3x3_matrix_audit.py` checks this and a small, bounded
family of natural readings of the resulting 3x3 grid, then tests them as
direct AES passphrases -- reusing the existing validated oracle exactly as
Phase 96 did, not a new cipher family.

**Real structural fact, confirmed by direct computation, not asserted:** the
archived title `SalPhaseIon` (11 letters) splits `SAL`/`PHASE`/`ION` =
`(3, 5, 3)` -- uneven. `SALVATION` (9 letters) splits `SAL`/`VAT`/`ION` =
`(3, 3, 3)` -- even. This is orthogonal to the periodic-table numerology
already closed in Phase 97-99: it is plain letter-counting, and it is a
genuine property that only emerges after the `PHASE -> VAT` substitution,
not present in the original title. Worth keeping on record as mild,
non-numerological support for the rebus.

**Eight natural matrix readings tested**, including the one reading order
with genuine independent precedent in this puzzle rather than an invented
convention: the exact top-left/counter-clockwise spiral already validated
for the Stage-0 grid image (`grid_spiral.py`'s `spiral_tl_ccw`, reused
directly, not reimplemented) applied to this 3x3 letter grid:

```text
row_major              SALVATION
row_major_reversed     NOITAVLAS
column_major           SVIAAOLTN
column_major_reversed  NTLOAAIVS
main_diagonal          SAN
anti_diagonal          LAI
boustrophedon          SALTAVION
spiral_tl_ccw          SVIONTLAA
```

All eight through `answer_forms()` x `keystr_forms(newline_variants=True)`:
144 unique keystrings, tested against all four tracked/quarantined blobs
under CBC (original + extended KDF), ECB, CFB/OFB/CTR, and AES Key Wrap:
**zero hits, every reading, every family.**

**Verdict:** the 3-3-3/9-letter structural observation is real and worth
keeping alongside the rebus, but none of the natural ways to read the
resulting grid -- including the one with actual precedent in this puzzle,
the established spiral order -- produce a working password. This closes
the 3x3-matrix reading of `SALVATION` as a direct-passphrase hypothesis; it
does not reopen the periodic-table numerology or license a broader
transposition search over the grid.

## Phase 106 -- a calibrated partial oracle for the checkerboard escape pair: real idea, real calibration, real negative (2026-07-27)

> **Superseded by Phase 112.** This phase ranked candidates by largest IC
> even though its own stated model requires IC *closest to* English prose
> (`0.067`). The historical numbers and negative verdict below are retained
> for auditability but are invalid.

Every attack on `dbbi`/`faed` to date has needed a full candidate alphabet
before producing any signal (quadgram fitness, AES success) -- a wrong
alphabet and a right one both look like noise until everything lines up.
This tests a genuinely new idea: whether the Index of Coincidence (IC) of
the SEGMENTED CODE stream (not the raw `a`-`i` symbols, already checked and
unremarkable) can identify the correct escape pair without any alphabet at
all. IC is invariant under monoalphabetic substitution, so a correctly
segmented real-English checkerboard should show a code-level IC close to
English prose's own (~0.067) regardless of which candidate alphabet is
used -- in principle a real alphabet-independent oracle. Topology has no
effect on this statistic (it only changes which code maps to which letter,
never which raw substrings count as one code), so only the 36 escape pairs
were tested, not escape pair x topology. `tools/gsmg/checkerboard_code_ic_oracle.py`
implements and calibrates it.

**Calibration, reusing `checkerboard_recovery_calibration.py`'s validated
corpora (Matrix screenplay / Cosmic Duality book / puzzle chat) and its
profile-matched board construction for `dbbi`:**

| Profile | Trials | True-pair rank-1 rate | True-pair mean rank | Null mean rank |
|---|---:|---:|---:|---:|
| `dbbi` (91 raw / 63 codes) | 200 | 0.000 | 29.07 / 36 | 15.49 / 36 |
| `faed` (~570 raw / ~469 codes) | 100 | 0.020 | 28.78 / 36 | 16.42 / 36 |

`faed`'s exact historical top/escape-split profile turned out to be
impractical to hit by random sampling even with a fast memoized subset-sum
DP (0 successes in 3,000+ attempts, replacing the exhaustive-combinations
search which would have taken far longer for the same 0 hits) -- English
text this long essentially never has a 7-letter subset summing to exactly
that historical value. `faed`'s calibration instead uses a disclosed
approximation: a fully random (not profile-matched) 25-letter alphabet with
adaptive plaintext-length search, accepting any resulting raw ciphertext
length within +/-3% of the real target. Code-level IC does not depend on
which letters sit in the top vs escape rows, so this changes construction
cost, not what is being measured.

**Result: this specific oracle has no discriminating power at either
length -- if anything, negative power.** The true escape pair's mean rank
(~29/36) is worse than a uniformly random pair's mean rank under pure noise
(~15.5-16.5/36, close to the null's own theoretical mean of 18.5). Rank-1
hit rate for the true pair is ~0-2%, at or below the 1/36 (2.8%) chance
rate. Longer ciphertext (`faed`) did not help, ruling out "just a small-
sample problem, more data would fix it."

**Mechanistic explanation, not just a null result.** Under any two-symbol
escape pair, 7 of the 9 raw `a`-`i` symbols remain single-symbol codes
regardless of which 2 are designated escapes. Those 7 symbols' individual
frequencies are inherited directly from the ciphertext's own raw-symbol
distribution -- the same elevated skew that already gave `dbbi` its raw IC
of 0.1509 (well above the 1/9=0.111 uniform baseline) by the original,
different method (Phase 8's direct raw-symbol frequency match against
3.2.2's known escape-density). Re-segmenting under a WRONG escape pair
still inherits most of that same single-symbol skew, so most candidate
pairs look almost as "structured" as the true one -- the two-symbol escape
codes contribute too small a share of the statistic to isolate the correct
pair from the other 35. This is a real, mechanistic reason code-level IC
cannot cleanly separate escape-pair hypotheses here, not just an artifact
of these specific corpora or seed.

**Real-data application, for completeness, correctly not treated as
evidence either way:** ranking all 36 pairs by code IC on the real streams
puts `dbbi`'s established `{b,e}` outside the top 10 (top 5: `ci`, `cd`,
`dh`, `hi`, `ch`) and `faed`'s candidates (`{g,i}`, `{h,e}`, `{b,e}`)
outside its top 10 too (top 5: `bf`, `df`, `ab`, `bd`, `ad`). Per the
calibration above, this is expected and uninformative either way -- it does
not weaken the original, differently-derived `{b,e}` finding (Phase 8's raw
frequency match, still the only decisive result on this question), and it
is not evidence for any of the top-ranked pairs either.

**Verdict:** the underlying idea -- a partial, alphabet-independent oracle
for checkerboard sub-hypotheses -- was worth building and calibrating
properly rather than dismissing on priors, and code-level IC specifically
does not deliver it, for a real structural reason rather than bad luck.
This closes the code-IC approach to the escape pair; it does not close the
broader question of whether *some* alphabet-independent partial oracle
exists (e.g. something that isolates only the 2-symbol escape codes rather
than the whole code multiset might avoid this specific confound, though
that would face an even smaller-sample problem than the one already shown
to fail here).

## Phase 107 -- `l`/`I` homoglyph reading of `SalPhaseIon`: real mechanical fact, oracle negative (2026-07-27)

User-proposed hypothesis: lowercase `l` and uppercase `I` can be visually
similar in some fonts, and the archived title is deliberately mixed-case.
In the actual archived/default bold-serif rendering they remain
distinguishable, so the visual premise is suggestive rather than an
authenticated marker. Removing the title's one `l` and one `I` leaves
`SaPhaseon`, readable as `Sa`/`Phase`/`on` -- mechanically distinct from
the Phase 96-99 `SALPHATION` word (a real creator-authored term, differing
from the title by a `PH`-vs-`T` swap, not by dropping `l`/`I`; the two must
not be conflated). This also fits a recurring, independently-motivated
theme in this puzzle -- characters flagged and removed/"zeroed out" to
reveal an underlying signal (the "zeroed out" thread; `enter` removed to
reconstitute the SalPhaseIon AES blob) -- so it was worth testing directly
rather than judged on priors alone.

`tools/gsmg/salphaseion_li_homoglyph_audit.py` verifies the removal
mechanically against the archived title (`SalPhaseIon` minus `l`/`I` =
`SaPhaseon`, confirmed by direct computation, not asserted) and generates a
small, bounded family of 8 case/spacing/separator variants (`SaPhaseon`,
`Sa Phase on`, `Sa_Phase_on`, `Sa-Phase-on`, and their upper/lower forms).

Through `answer_forms()` x `keystr_forms(newline_variants=True)`: 108
unique keystrings, tested against all four tracked/quarantined blobs under
CBC (original + extended KDF), ECB, CFB/OFB/CTR, and AES Key Wrap: **zero
hits, every variant, every family.**

**Verdict:** the user-selected deletion is mechanically reproducible and
cheap to keep on record, but the actual rendering does not establish a
homoglyph instruction, and the resulting reading is not a direct
password under current oracle coverage. Closes this specific hypothesis;
does not reopen the `SALVATION`/`SALPHATION` numerology (Phase 97-99,
already closed) or license removing other letter pairs from other
fragments without a similar, independently-motivated reason.

**Follow-up (same day): combining with Phase 97's `PH -> V`.** User-proposed
extension: apply the already-established `PH -> V` element-pair
substitution (Phase 97, there derived from `SALPHATION` -> `SALVATION`) to
`SaPhaseon` instead of to `SALPHATION`. `Phase` minus its leading `Ph` plus
`V` gives `Vase` -- a real English word -- so the remainder becomes
`SaVaseon`, readable as `Sa`/`Vase`/`on`. Verified mechanically (not
asserted): `"SalPhaseIon".replace("l","").replace("I","").replace("Ph","V")
== "SaVaseon"`.

This reuses an existing, independently-motivated substitution rather than
inventing a new one, but is flagged in the code and here as no stronger
than the letter-value schemes Phase 98-99 already cautioned about: English
is dense enough that a real word turning up inside a short remainder after
a chosen 2-for-1 substitution is not on its own strong evidence.

Extended `tools/gsmg/salphaseion_li_homoglyph_audit.py` (not a new script)
to cover both the original 8-candidate family and this combined 8-candidate
family (`SaVaseon`, `Sa Vase on`, `Sa_Vase_on`, `Sa-Vase-on`, and
upper/lowercase forms) together. Through `answer_forms()` x
`keystr_forms(newline_variants=True)` against all four tracked/quarantined
blobs under CBC (original + extended KDF), ECB, CFB/OFB/CTR, and AES Key
Wrap: 16 total candidates, 216 unique keystrings, **zero hits, every
variant, every family.**

**Verdict:** a real, verified word (`VASE`) emerges from a real, verified
mechanical combination of two already-motivated operations -- worth
recording and worth the cheap direct test -- but it is not a password
under current oracle coverage either. Closes this specific combined
hypothesis.

**Second follow-up (same day): the full title-rebus `Phase -> VAT`
substitution, plus a phonetic neighbor.** User-proposed: instead of the
element-pair `Ph -> V`, apply the original Phase 96 title-rebus
substitution (`Phase -> VAT`, the whole 5-letter word for 3 letters) to
`SaPhaseon`. Verified mechanically:
`"SalPhaseIon".replace("l","").replace("I","").replace("Phase","VAT") ==
"SaVATon"`, splitting as `Sa`/`VAT`/`on`. The user also noted `"Sa VAT on"`
is close, spoken aloud, to **Sabaton** -- the Swedish power-metal band --
which was checked directly too (not previously present anywhere in this
project's chat-mined wordlists or FINDINGS.md; confirmed genuinely new).

Extended `tools/gsmg/salphaseion_li_homoglyph_audit.py` with this third
candidate family (`SaVATon`, `Sa VAT on`, `Sa_VAT_on`, `Sa-VAT-on`, case
variants) plus the literal `Sabaton` candidate (its own case variants
generated automatically by the existing `answer_forms()` normalization, no
extra code needed).

All three families together (original `SaPhaseon` family, `PH->V`
`SaVaseon` family, `Phase->VAT`/`Sabaton` family): 25 candidates, 351
unique keystrings through `answer_forms()` x
`keystr_forms(newline_variants=True)`, tested against all four
tracked/quarantined blobs under CBC (original + extended KDF), ECB,
CFB/OFB/CTR, and AES Key Wrap: **zero hits, every variant, every family.**

**Verdict:** both the `VAT`-combination and the `Sabaton` phonetic
neighbor are real, cheaply-checked ideas worth having tested directly
rather than judged on priors, and both are now closed negative under
current oracle coverage. This closes the full `l`/`I`-homoglyph thread
(original, `PH->V`, and `Phase->VAT` variants) pending any new,
independently-motivated reason to revisit it.

## Phase 108 -- `SPI`/`CD`: capital-letter initials of both textareas, oracle negative (2026-07-27)

User-proposed observation: `SalPhaseIon`'s capital letters are exactly `S`,
`P`, `I` -- the same word-boundary capitals Phase 96 already established as
`Sal|Phase|Ion` -- and `Cosmic Duality`'s are `C`, `D` (its two words).
Verified mechanically, not asserted:
`"".join(c for c in "SalPhaseIon" if c.isupper()) == "SPI"` and the same
for `"Cosmic Duality"` gives `"CD"`. This is a genuinely new angle on the
`SalPhaseIon`/`Cosmic Duality` textarea pair Phase 104's dual-channel audit
already confirmed is real -- that audit only checked DOM order, never
capitalization-derived initials.

`tools/gsmg/spi_cd_initials_audit.py` surveys, honestly, what `SPI`/`CD`
could connect to:

- Structurally this is just each heading's own initials -- unsurprising on
  its own; what would matter is whether the combined result means
  something further.
- Common-usage readings (`SPI` = Serial Peripheral Interface, or a
  homophone of "spy"; `CD` = Compact Disc, or the element symbol Cadmium)
  connect to no independently-established theme here.
- Elemental-symbol reading (Phase 97's convention): `spi` parses uniquely
  as S+P+I (16+15+53=84); `cd` parses uniquely as Cd (48). `84` recurs
  elsewhere in this project only via Robby's unrelated, never-endorsed
  `anstoo`/BB84 numerology (Phase 102) -- an independent derivation, not
  corroboration; treated as coincidental absent a reason to think
  otherwise, per the same base-rate caution Phase 98-99 already applied.
- Noted but deliberately NOT promoted to a test candidate: `SPICD` minus
  `P` anagrams to `DISC`. Dropping a letter with no stated reason is
  exactly the unmotivated-operation pattern this project has repeatedly
  found to be apophenia.

Only the direct, unmodified concatenation was tested (10 candidates:
`SPICD`, `SPI CD`, `SPI-CD`, `SPI_CD`, the reversed `CDSPI`/`CD SPI`, and
case variants). Through `answer_forms()` x
`keystr_forms(newline_variants=True)`: 108 unique keystrings, tested
against all four tracked/quarantined blobs under CBC (original + extended
KDF), ECB, CFB/OFB/CTR, and AES Key Wrap: **zero hits.**

**Verdict:** the capitalization fact is real and worth keeping alongside
Phase 104's dual-channel inventory as another way this specific pair has
now been examined, but `SPI`/`CD` is not a password under current oracle
coverage. Closes this hypothesis; does not license chasing the `DISC`
anagram or further elemental-sum readings without independent motivation.

**Follow-up (same day): a real namesake debunked, and a phonetic reading
tested.** User supplied `github.com/raszi/spicd` -- checked directly via
the GitHub API: it's "Sony Vaio SPIC control daemon" (`SPIC` = Sony
Programmable I/O Controller, `d` = the standard Unix daemon suffix, 2010,
2 stars). An unrelated coincidental namesake, not a puzzle connection --
any short pronounceable string is likely to already be someone's project
name, which is not on its own evidence of anything.

Separately, `SPICD` read aloud is one letter short of the real English word
`SPICED` -- verified mechanically:
`"SPICED".replace("E", "", 1) == "SPICD"`, with the missing letter sitting
exactly where a reader would supply an
epenthetic vowel pronouncing an unfamiliar consonant cluster. Added
`SPICED`/`spiced` to `tools/gsmg/spi_cd_initials_audit.py`'s candidate
family (12 candidates total now). Through `answer_forms()` x
`keystr_forms(newline_variants=True)`: 126 unique keystrings against all
four tracked/quarantined blobs under CBC, ECB, CFB/OFB/CTR, and AES Key
Wrap: **zero hits.**

**Verdict:** the GitHub namesake is closed as coincidental (real but
unrelated), and the `SPICED` phonetic reading -- worth the cheap direct
test given it's a real word one letter away -- is now also closed negative.

## Phase 109 -- bird's-eye re-sweep of the SalPhaseIon page's own artifacts (2026-07-27)

User asked to brainstorm broadly again (per the creator's own framing: the
answer should be "in front of your eyes"), looking at what this project
already has from a different angle rather than reaching for a new cipher
family. Eight candidate angles were generated; each was investigated for
real before any oracle sweep, and only cheap/direct checks were run.

**1. The `H1`/`h1` tag-case discrepancy has real history, and it points the
opposite way from a same-day typo.** Fetched all 5 distinct-digest Wayback
captures of the SalPhaseIon page via the CDX API
(`20230601`, `20231127`, `20241123`, `20251031`, `20260405`) and decoded
them (several were gzip-encoded, requiring `gunzip` before diffing). The
**earliest** capture (2023-06-01) reads `<h1> SalPhaseIon </H1>` -- the
opening and closing tags of the *same element* disagree with each other.
Every capture from 2023-11-27 onward reads `<H1> SalPhaseIon </H1>` --
internally consistent, both uppercase. A byte-level diff between the two
earliest captures shows **exactly one changed line, nothing else on the
whole page**: the opening tag went from `<h1>` to `<H1>`. Someone touched
this one tag, once, between June and November 2023, and made it more
uppercase, not less -- the opposite of what a casual cleanup pass
normalizing toward lowercase HTML convention would do. `Cosmic Duality`'s
`<h1>...</h1>` never changes across any capture. This is a real, dateable
edit event, not an artifact of transcription.

**2. Style-fingerprint check flips which heading looks like the outlier.**
Compared markup conventions across all three real static (non-Vue-shell)
pages in the local mirror. `choiceisanillusion...iwroteitmyself.html` --
the other page with `h1` tags -- has **two `<H1>` tags, both uppercase,
correctly matched** (confirmed via exact tag/content extraction, not just
counts). Both `theseedisplanted.html` and the choice page share an
identical Cloudflare Web Analytics beacon script (single-quoted
`data-cf-beacon` JSON attribute) that the SalPhaseIon page lacks entirely --
likely CDN/infrastructure-level, not creator-authored, so not weighted as
meaningful on its own. But combined with fact 1: this creator's own
checkable habit, on the one other page where it's checkable, is uppercase
`H1` -- both instances, correctly matched. That makes `SalPhaseIon`'s
(now-uppercase) heading match the established convention and
`Cosmic Duality`'s lowercase heading the actual deviation from it, which is
the reverse of how this was framed in the prior session's answer.

**3. Rendered-pixel check: no CSS-hiding tricks.** Screenshotted the local
mirror of the SalPhaseIon page with headless Chrome
(`google-chrome --headless --screenshot`). Both headings render
identically (browser default CSS treats `h1`/`H1` case-insensitively, per
the HTML spec) -- confirms the anomaly is purely a source-byte artifact,
not a rendering trick, and rules out hidden/positioned/color-matched text
as a competing explanation for finding #6.

**4. `thSeedisplanted` filename ruled out.** The bare-lowercase-with-one-
capital variant found in the mirror directory (`thSeedisplanted.html`,
36,123 bytes) is byte-identical in size to the confirmed generic Vue-shell
page (`TheArchitectChoice.html`, also 36,123 bytes, checked directly and
confirmed to be nothing but `<title>GSMG</title>` / `<div id="app"></div>`
boilerplate) -- a bot/crawler-guessed URL variant resolving to the empty
shell, not a real archived page with content. No internal-capital-letter
significance to chase here, unlike `SalPhaseIon`'s.

**5. No HTML comments, `title=`/`alt=` attributes, or non-ASCII bytes**
anywhere in the SalPhaseIon page's raw source (checked directly). Nothing
hidden in markup metadata.

**6. Cross-application of dbbi/faed roles across blobs already happened
implicitly.** Considered testing values derived from one stream (e.g. the
Architect-derived `SALVATION`) against the *other* stream's specific blob
(`COSMIC`, confirmed a real, separate tracked blob from `SALPH` in
`cb_common.BLOBS`) rather than against the pooled default set. Checked: every
existing sweep script already tests against the full `BLOBS` dict (both
`SALPH` and `COSMIC` together) by default, so this cross-application has
already been happening on every single candidate tested across this whole
project -- not a new lever. Likewise, the `{h,e}` mirror-hypothesis escape
pair for `faed` (the literal cross-stream analogy from `dbbi`'s `{b,e}`) has
already been sweep-tested extensively (chain-addition, VIC, autokey; see
Phases referencing `{h,e}` throughout this file) -- also not new.

**7. `promised` (the macro clue's final word) tested standalone for the
first time.** Every other macro-clue fragment has an established reading;
`promised` had only ever been consumed as part of the full concatenated
clue string. `tools/gsmg/promised_standalone_audit.py`: 3 unique candidates
(`promised`/`PROMISED`/`Promised` via case forms), 27 unique
keystrings via `answer_forms()` x `keystr_forms(newline_variants=True)`,
tested against all four tracked/quarantined blobs under CBC (original +
extended KDF), ECB, CFB/OFB/CTR, and AES Key Wrap: **zero hits.**

**8. Widened the physical-evidence search past the Telegram export.**
Web-searched for the missing book pp. 57-58, the Neo passport-date clue,
and the original `barrystyle` interior image outside Telegram (Reddit,
Bitcointalk, general web). Found no new primary source for any of them --
confirms rather than closes the bird-view doc's standing conclusion that
this is a genuine evidence-availability gap, not a lead this session could
open. Also directly checked (via `gh api search/issues`) whether the
`puzzlehunt/gsmgio-5btc-puzzle` GitHub repo's issues mention "book pages,"
"passport," or "barrystyle" anywhere: zero matches.

**Important side-finding, not physical evidence but worth flagging
explicitly:** the search surfaced GitHub issue #69, titled as a "SOLVED"
comprehensive solution submission (dated "December 28, 2025"). Read the
full issue body directly. It is not credible: internally inconsistent
(auto-linkified phone-number artifacts inside what are claimed to be hex
hashes, indicating sloppy copy-paste), invokes fabricated-sounding
machinery ("IBM EBCDIC 1141," a Decentraland/audio-steganography chain not
corroborated anywhere in this project's own from-source verification work),
and ends by asking the puzzle owners to let the submitter "perform the
dusting transaction trigger... or receive the reward directly" -- the
classic shape of a solicitation, not a solution. Issue #56 (a "walkthrough"
with a donation address and a contact email for "material requests") reads
the same way. Neither should be treated as evidence of anything, including
that the puzzle has been solved by someone else.

**Verdict:** one genuinely new, well-dated source-history fact (the 2023
tag-case edit, and the corrected framing of which heading is the outlier),
several honest ceilings confirmed (rendering, filenames, markup metadata,
cross-application, physical evidence), and one more macro-clue fragment
closed negative as a password. No new AES-oracle lever. The tag-case edit is
a concrete, dateable source anomaly, but the archive does not establish who
made it or whether it was intentional; calling it “creator-touched” would
overstate its provenance. HTML tag case has no rendered effect, and the
community had already noticed the casing while remaining skeptical.

**Follow-up (same day): the community already found this, and already
disagreed about it.** Searched the complete Telegram export (any sender,
not just the creator) for `h1`/`H1` mentions. It was independently noticed
twice, months apart, and both times the room leaned skeptical: on
2025-06-01 an anonymous user flagged the exact same `<H1>`/`<h1>` pair
("i wonder if this is a clue or simply a typo"), and within minutes another
user ran the *identical* cross-page check this project ran today (comparing
against the `choiceisanillusion...` page's own `H1` tags) and concluded
"makes no difference, style preference mostly but could mean something." On
2026-01-23 "WILL" re-raised it independently, pairing it with a
`SALT`/`PHRASE`/`ION`-XOR reading; "Whore Amazing" rebutted with the same
null-model point ("In the phases 2/3 page, both `<H1>` are uppercase, didn't
affect anything") and called the idea "far-fetched." Neither exchange
mentions the Wayback edit-history finding above (the one-tag, one-line,
2023 edit) -- that part is new relative to the chat record, even though the
raw casing fact itself is not.

**Follow-up (same day): Wayback raw-byte integrity check.** Before trusting
any more byte-level anomaly-hunting on this page, verified Wayback's `id_`
raw-fetch mode is faithful: an independent fetch of the 2026-04-05 capture
today reproduced the local mirror file byte-for-byte (5,092 bytes, identical
hash) despite being fetched in a separate session. Also swept all 5 real
captures for hidden/invisible Unicode (NBSP, zero-width space/joiner/
non-joiner, BOM, word joiner, etc.), CRLF, and stray tabs: **zero non-ASCII
bytes anywhere, in any capture** -- the page is pure 7-bit ASCII throughout
its entire history. The tag-case discrepancy is not sitting alongside some
other invisible-character trick.

**Follow-up (same day): `h`/`H` as a marker/selector, motivated by the tag
case.** Chat question: does changing `h1` -> `H1` imply some `h` inside the
textarea itself should also become `H`? Checked directly before assuming
this is executable: `h` is not rare inside `dbbi`/`faed` -- it is one of
the ordinary 9 alphabet letters both streams use, appearing 8 times in
`dbbi` and 58 times in `faed` (66 total, plus a handful more in the plain
instruction words). And the one place case is actually load-bearing on this
page -- the two Base64 halves of the real embedded SALPH ciphertext -- already
contains one lowercase `h` and one uppercase `H`, both already verified
byte-for-byte correct against the known-good `SALPHASEION_BLOB_B64`
constant. So there is no single, well-defined `h` to promote, and blanket-
uppercasing would corrupt already-correct ciphertext rather than reveal
anything.

What *is* independently motivated: `h` is already established (Phase 34/104,
via `mirror9('b') == 'h'` from the `BUT`/`HYE` Architect-dialogue selection
-- a completely different derivation chain than this tag observation) as
`faed`'s mirror-hypothesis escape-pair partner. `tools/gsmg/
h_marker_selector_audit.py` tests this two ways: (1) direct transform --
`dbbi`/`faed` with every `h` uppercased, tested as literal passphrases;
(2) position-selector -- `faed`'s 58 `h` positions (mod `len(dbbi)==91`)
used to index into `dbbi`, and symmetrically `dbbi`'s 8 `h` positions (mod
`len(faed)==570`) into `faed`, producing two short derived strings. 5
candidates, 117 unique keystrings via `answer_forms()` x
`keystr_forms(newline_variants=True)`, tested against all four tracked/
quarantined blobs under CBC (original + extended KDF), ECB, CFB/OFB/CTR,
and AES Key Wrap: **zero hits.**

## Phase 110 -- re-swept the full export for other raw-binary creator posts (2026-07-28)

Chat question: the 2023-02-23 macro-clue message was cracked by reversing its
entire 1,288-bit stream as one unit before rechunking into bytes (Phase 7);
could the same "whole-stream reversal" decode apply to some other, still-
unsolved binary post? Swept all 57,729 messages (not just the creator's, in
case of an unnoticed repost) for near-pure `0`/`1`/whitespace text of length
>= 40: 25 hits. All but two are reposts/quotes of the already-known 2023-02-23
message, or of an unrelated 4096+1272-bit pair posted four times by user `X`
(2024-2025) that decodes to ordinary already-public discussion text, not a
creator artifact.

`tools/gsmg/binary_message_export_audit.py` now makes the load-bearing
inventory reproducible: it asserts 25 qualifying messages and creator-authored
IDs exactly `(8446, 53342)`, then byte-decodes `53342` directly.

The only creator (`Jrk Bgrt`) binary post not already catalogued by Phase 7 is
message `53342`, **2026-01-01T05:20:03**, 616 bits. Decoded directly (forward,
no reversal -- confirmed by the immediate community reply "Not even reversed
smh"): *"Happy new year! Make the best of everything. Oh, and here's a 'tiny
hint' <3."* The chat's own next replies treat this as a self-referential joke
(the "hint" is that there is no hint) and move on within minutes -- already
publicly resolved the same day, not a new lead.

**Conclusion:** no uncatalogued raw-binary creator message remains that the
reversal trick could be newly applied to. For the actual unsolved artifacts
(`dbbi`/`faed`, the AES blobs), the trick doesn't directly transfer anyway --
they are not raw ASCII `0`/`1` text -- but the generalized lesson ("don't
trust a decode without testing the reversed order too") is already a
present in dedicated structural transform sweeps: `cb_common.py`'s
`TRANSFORM_KINDS` includes `"reverse"` alongside `identity`/`col2..col6`.
It is **not** used by every GSMG driver (several default to identity or use
their own bounded families), so the earlier “every candidate across the
entire sweep history” wording was false. Raw reversal is nevertheless not an
untouched gap because dedicated full-transform sweeps covered it broadly.

## Phase 111 -- acrostic/telestich on the macro clue's constituent words (2026-07-28)

Chat question: split the macro clue into its actual English words (not just
the 8 known fragments) and check first-letter/last-letter sequences. Grepped
FINDINGS.md for `acrostic`/`first letter`/`last letter` first: zero prior
hits, so this was genuinely untried at the word level.

`tools/gsmg/macro_clue_acrostic_audit.py` declares an explicit word split for
each of the 8 fragments (reusing `promised_standalone_audit.MACRO_CLUE` for
the fragment strings) and asserts each split's concatenation reproduces the
fragment exactly before using it. The final fragment
(`verylaststepisatruegiveaway`) is ambiguous between "giveaway" (compound
noun) and "give away" (verb phrase, matching some of the chat's own manual
transcriptions) -- both segmentations (38 vs. 39 words) are tested rather
than picking one. Four word-level strings plus 2 coarser fragment-level ones
(first/last letter of the 8 fragments themselves) give 6 candidates:

```
word acrostic  (compound): ybpmsllwbacyywwgatpiifoyebynsivlsiatgp
word telestich (compound): wesxmttseiengeteyedsntfrstetgtytpsaeyd
word acrostic  (split):    ybpmsllwbacyywwgatpiifoyebynsivlsiatgap
word telestich (split):    wesxmttseiengeteyedsntfrstetgtytpsaeeyd
fragment acrostic (8):     ymlywivp
fragment telestich (8):    stegdtyd
```

108 unique keystrings via `answer_forms()` x `keystr_forms(newline_variants=
True)`, tested against all four tracked/quarantined blobs under CBC
(original + extended KDF), ECB, CFB/OFB/CTR, and AES Key Wrap: **zero hits.**

## Phase 112 -- review correction: code-IC is a strong partial escape-pair oracle (2026-07-28)

Independent review found a load-bearing bug in Phase 106:
`checkerboard_code_ic_oracle.py` correctly stated that a valid segmented
English stream should have code IC **close to** `0.067`, but ranked pairs by
the **largest** IC. That optimized the opposite objective. Tie ranks were
also enumeration-biased. The script now ranks by
`abs(IC - 0.067)` ascending and assigns the average rank to exact ties.

Three independent 1,000-trial calibrations reproduce a large separation:

| Seed | Profile | True rank-1 | True top-5 | True mean rank | Null rank-1 | Null top-5 | Null mean rank |
|---:|---|---:|---:|---:|---:|---:|---:|
| 20260727 | DBBI | 0.427 | 0.855 | 2.69 | 0.031 | 0.181 | 15.19 |
| 12345 | DBBI | 0.467 | 0.868 | 2.55 | 0.030 | 0.173 | 15.01 |
| 8675309 | DBBI | 0.412 | 0.849 | 2.77 | 0.036 | 0.142 | 15.54 |
| 20260727 | FAED | 0.926 | 0.976 | 1.52 | 0.039 | 0.177 | 15.19 |
| 12345 | FAED | 0.914 | 0.967 | 1.53 | 0.042 | 0.173 | 15.56 |
| 8675309 | FAED | 0.929 | 0.977 | 1.51 | 0.029 | 0.172 | 15.09 |

Applying the corrected statistic to the real streams:

- DBBI: `{b,e}` ranks **1/36**, IC `0.06708`, distance `0.00008`.
- FAED: `{g,i}` ranks **1/36**, IC `0.07429`, distance `0.00729`.
- FAED's `{h,e}` mirror hypothesis ranks 16th; inherited `{b,e}` ranks 17th.

This independently recovers DBBI's already-established `{b,e}` pair and
selects FAED's independently frequency-fitted `{g,i}` pair without an
alphabet keyword. The FAED synthetic calibration remains disclosed as
length-matched rather than exact-profile-matched, but the effect is stable
across seeds and far above its random-noise control.

**Verdict:** Phase 106's negative is reversed. Code IC is a useful partial
oracle, and `{g,i}` is now the best-supported FAED escape pair by two
different mechanisms. The highest-value computational follow-up is the
calibrated blind monoalphabetic FAED recovery under `{g,i}`. The existing
Phase-43 hill-climb tested only fixed `(h,e)`; direct keyword, autokey, and
chain sweeps under `{g,i}` do not substitute for a ciphertext-only
monoalphabetic recovery under that pair.

## Phase 113 -- calibrated FAED monoalphabetic recovery under `{g,i}`: closed negative (2026-07-28)

Executed Phase 112's own stated follow-up: generalized `faed_monoalphabetic_
sweep.py` and `faed_token_null_check.py` (both previously hardcoded to
`(h,e)`) to accept an arbitrary ordered escape pair, verified via self-test
against both `(h,e)` (no regression) and `(g,i)` (436 codes, all 25 types,
serial + parallel hillclimb paths).

**Important clarification on what the Phase 112 calibration is, and isn't.**
Phase 112's "rank-1 in three 1000-trial calibrations" result is recovery-
*power* measured against a control built from **uniform random raw symbols**
-- a different, complementary check from the **token-preserving code-shuffle
null** this phase's actual significance test uses (same shuffle mechanism as
Phase 43's `(h,e)` test: segment once, shuffle the CODE LIST, rejoin --
guaranteed to preserve the real code count/type profile by construction).
Conflating the two would overstate what Phase 112 established; a docstring
in `faed_monoalphabetic_sweep.py` that had done exactly this was corrected.

**Pre-registered staged significance design**, agreed before any trial ran
(closes an optional-stopping-bias risk): 100 null trials first; if any
trial ties or beats the real score (exceedances > 0), stop and report
negative at that resolution (`p_min` at n=100 is `1/101~=0.0099`, already
above the project's `p<0.005` bar, so this outcome is always "fail"
regardless of the exact count). Only zero exceedances at n=100 would
trigger an automatic extension to 1000 trials to get enough resolution to
actually test `p<0.005`.

**Result:** real FAED under `(g,i)`, single canonical variant
(`g,i,top_first`), 800 restarts/4000 iters (matching Phase 43's real-run
budget): best score **-2419.47** (-5.5492/char for that canonical variant).
100-trial token-
preserving null (same optimizer seed/budget, only the shuffle varies):
range -2499.7 to -2412.0, standard median -2451.8. **3 of 100 null trials tied or
beat the real score -- exceedances=3, empirical p=0.0396.** Per the
pre-registered rule this stops at n=100: **decision=FAIL, no AES escalation.**

This is a softer negative than Phase 43's `(h,e)` result (real sat almost
exactly at the null median, p=0.634) -- `(g,i)`'s real score beats 97/100
null draws -- but it does not clear the pre-declared bar, and the design
exists specifically to prevent treating "looks more promising than last
time" as license to keep sampling until it does.

**Hardening, added after a real review round** (the built-in self-test
initially missed both High-severity issues below despite passing):
- `config_fingerprint()` now also hashes `quadgram_solver.py`,
  `prefix_boundary_sweep.py`, `english_quadgrams.txt`, and this module
  itself, plus records the Python version -- a future resume after any code
  or scoring-data edit is rejected, not just a config-parameter change.
- New `escalation_fingerprint()` binds `top_n`, the blob set + content
  hash, `include_quarantined`, the cipher/KDF families actually tested
  (`cbc_legacy`/`cbc_extended`/`keywrap` -- Key Wrap is its own family, not
  folded into "extended"), the `answer_forms`/`keystr_forms` policy
  (`newline_variants=False`, matching Phase 43's own escalation loop
  exactly), the significance bar and staged trial counts, `cb_common.py`'s
  hash, and (review-caught gap) **`seed_base`** -- previously absent, which
  would have let a rerun with a different null-shuffle sequence silently
  reuse a decision computed under a different one.
- The gate-decision record also carries a **`checkpoint_content_hash`**
  (review-caught gap), re-verified on every load against the checkpoint
  file's current on-disk hash -- catches a checkpoint that changed after
  the gate was recorded even when every config field still matches.
- **Review-reproduced crash, fixed:** resuming after the gate record was
  written but before the candidates record was (interrupted mid-write)
  threw `TypeError: 'NoneType' object is not iterable`. Fixed by
  regenerating candidates via a fresh, deterministic (same-seed) real
  search rather than crashing -- the underlying `real_results` were never
  persisted (only used transiently), so this recomputes rather than losing
  data.
- **Review-caught IPC waste:** every worker chunk was unconditionally
  pickling its full per-restart results list back to the parent, even
  though null trials only ever need a single score -- now gated behind the
  same `collect_all` flag the real-search candidate-collection path uses.
- Result artifact writes a header, then a gate-decision record, then
  (only if `decision==pass`) deduped top-N candidates (score/decode/key,
  ordered `(-score, decode)` for determinism) from the **same real search**
  used for the null comparison -- not `faed_monoalphabetic_sweep.py`'s
  separate 4-variant sweep, which would silently change optimizer exposure
  and candidate provenance -- then one `candidate_completion` record per
  candidate (`hits`, `attempts`, even when zero) as escalation proceeds, so
  an interruption can tell "tested, zero hits" apart from "not yet reached."
  `.gitignore` updated for the new checkpoint/backup/escalation-result
  filename patterns; a duplicate `dedup_top_n` definition and a stale
  CLI-usage docstring line were also removed.

**Provenance caveat, worth being precise about:** the actual completed run
above was launched *before* the five review fixes landed on disk -- Python
had already imported the old module version, so its in-memory source hash
for this file is frozen at `984f5f838c5d2f04` (confirmed via the written
artifact header), while the current file hashes to `092ebf5a3a1767e4`.
Current code will correctly refuse to resume or reuse that artifact as a
native match (by design). This matters not at all for the actual
conclusion here, though: none of the five fixes touch `hillclimb`,
`segment_codes`, or the scoring table, so the null-trial statistics
themselves (real score, null distribution, exceedances, p) are unaffected,
and since the gate failed, the escalation code path the fixes protect never
ran in this execution at all. Label this run's artifact as produced under
the pre-review-fix module version, not as evidence the fully-hardened
escalation path was ever exercised end-to-end on real data (self-test
coverage is what actually exercises that path).

**Verdict:** `{g,i}` FAED monoalphabetic recovery is closed negative under
the project's pre-declared `p<0.005` bar. This run does not provide
project-threshold evidence of English under this pair via ciphertext-only
hill-climbing, despite `{g,i}` remaining the best-supported escape pair by
code-IC and frequency-fit. Do not rerun this specific test hoping for a
different result absent new evidence changing the escape-pair hypothesis
itself.

## Phase 114 -- late-stage reproducibility hardening (2026-07-28)

Added `test_recent_audits.py` as permanent regression coverage for the
corrected Phase-106/112 IC objective and real top pairs (`dbbi={b,e}`,
`faed={g,i}`), the deduplicated three-form `promised` family, the exact
`SPICED - E = SPICD` relation, the four SALVATION-role statuses, the
seven-pair/four-edge scope of the dual-channel audit, the Telegram binary
inventory, and the archived-page mirror hash. Tests that depend on the
external Telegram export or sibling page mirror skip explicitly when those
primary artifacts are unavailable rather than silently substituting data.

Expanded `binary_message_export_audit.py` from a count-only check into a
complete 25-record inventory. Each qualifying message now records its
source ID, bit length, full SHA-256 payload digest, and a mechanically
bounded category: creator macro, creator New Year message, exact repost of
one of those, repeated non-creator payload, or unique non-creator payload.
The audit freezes all 25 message IDs and reports five exact duplicate
payload groups; it does not assign speculative meanings to the remaining
community messages.

Added `salphaseion_wayback_history_audit.py`, freezing the five distinct
Wayback captures of the exact puzzle route from 2023-06-01 through
2026-04-05 with CDX digest, raw-byte SHA-256, byte count, and exact heading
capitalization. The downloaded captures reproduce exactly. The only
difference between the first two captures is the one-line change
`<h1> SalPhaseIon </H1>` to `<H1> SalPhaseIon </H1>`; the latest capture
is byte-identical to the local sibling-repository mirror. The script
supports offline capture-directory verification and an explicit optional
live CDX/raw-capture recheck.

**Verdict:** these changes do not introduce a new solving hypothesis or
alter any cipher result. They turn several recent, corrected conclusions
and two external-source claims into repeatable checks so later edits cannot
silently restore the already-fixed errors.

## Phase 115 -- creator handle `SoWut`: authentic identity, unsupported clue, direct-oracle negative (2026-07-28)

Audited the creator's Telegram username after it was proposed as possible
puzzle material. The complete export establishes that `@SoWut` refers to
the same account recorded under stable creator ID `user9815232` and display
name `Jrk Bgrt`; the earliest surviving explicit mention is community
message 853 (2019-05-14), `@SoWut give me the solution`. This proves the
handle is authentic and early, but not that it was created for the puzzle:
the first occurrence is a community address, not a creator-authored reveal,
and no creator message in the export explains or selects the handle.

The community itself raised exactly this possibility in messages
16460-16462 (2023-11-12): "the creator's telegram username is `SoWut`" /
"do you think it might means something?" The following response says only
that someone had asked about `Jrk` and received "no hints"; there is no
direct creator confirmation in that exchange. Treating the mixed capitals
as `SW`, the spelling as "so what", or the reversal as an operation would
therefore require an additional selector not present in creator-authored
evidence.

`sowut` was not wholly untested: it appears in
`medium_curated_tier1_primary.txt`, so the completed padded and `-nopad`
binary-key-material sweeps already covered its normalized candidate forms.
Added `sowut_nickname_audit.py` to close the narrower direct-textual gap
across a declared family: literal `SoWut`, spaced `So Wut`, expanded
`so what`, punctuated `so what?`, and reversed `tuWoS`, with case,
answer-normalization, SHA forms, and newline variants. Result: **21 literal
candidates, 189 unique keystrings, four blobs, zero hits across CBC
(legacy+extended), ECB, stream modes, and AES Key Wrap.**

**Verdict:** `SoWut` may simply be a stylized "so what" handle and could
thematically fit the creator's deliberately noncommittal chat persona, but
that is interpretation rather than puzzle evidence. Literal password use is
closed negative under the project's current oracle families. Do not derive
compass, reversal, initials, or other transforms from the capitalization
without a new creator-authored clue selecting the username or an operation.

## Phase 116 -- historical SafeNet/Luna HSM terminology audit: real thematic overlap, no transition rule, oracle negative (2026-07-28)

Followed up the authenticated solved-chain sequence `SafeNet` / `Luna` /
`HSM` using source-era product documentation rather than current branding
or an unconstrained web-derived wordlist. Added
`wordlists/gsmg/safenet_luna_hsm_candidates.txt`: 62 exact terms from
SafeNet Network HSM 6.3 documentation (2017), the documented
Luna-to-SafeNet product rename table, and Thales's Gemalto acquisition.
No role/color/product cross-products are generated.

The timing is real and stronger than "Thales owns it now": Thales completed
its Gemalto acquisition on **2019-04-02**, 18 days before the puzzle's
2019-04-20 launch. The source-era vocabulary also genuinely overlaps later
puzzle themes:

- PED roles use blue (HSM SO), red (cloning domain), black (Partition
  Owner/Crypto Officer), gray (Crypto User), white (Auditor), orange
  (Remote PED), and purple (Secure Recovery) key labels.
- The documentation uses `MofN` split-secret authentication, dual control,
  cloning domains, partitions, challenge secrets, and private/secret-key
  wrapping, unwrapping, masking, and cloning.
- The first-piece palette overlaps blue/black/white but has unmatched
  yellow; the Stage-1 icon palette overlaps blue/red/black/white, while
  gray/orange/purple remain unused. Color overlap alone therefore does not
  recover an ordered role mapping or operation.

`safenet_luna_hsm_audit.py` freezes those boundaries and checks the complete
Telegram export using the stable creator ID. There are **zero**
creator-authored messages containing the bounded product/mechanics terms
(`SafeNet`, `Luna`, `HSM`, `Thales`, `Gemalto`, `PED`, `MofN`, cloning
domain, dual control, or split knowledge). Community discussion had already
noticed Thales and the old Rotterdam-area business location, but no creator
reply promotes that discussion into an endgame instruction.

Ran the exact list through the full direct-textual oracle:

```text
candidates=62
unique_keystrings=2583
blobs=4
CBC legacy+extended=0 hits
ECB=0 hits
stream modes=0 hits
AES Key Wrap=0 hits
```

**Verdict:** the product family is historically legitimate and its
M-of-N/dual-control/private-key vocabulary is a better thematic resemblance
than a random modern product association. It still supplies no mechanically
selected transition: yellow has no PED role, no puzzle artifact establishes
the PED role order, and the creator never invokes this glossary after the
already-solved phase. Exact terminology is closed negative as direct key
material. Keep `MofN`, dual control, and cloning-domain semantics as
recognition checks if future primary evidence points back to the HSM, but do
not launch generated phrase combinations or reinterpret current ciphertext
without such evidence.

## Phase 117 -- Phase-4 door/date re-audit: date-format role strengthened, exact inscription gap closed (2026-07-28)

Revisited the original Phase-4 evidence against the complete Telegram export
instead of the older text-only archive. `phase4_date_door_reaudit.py` pins the
relevant messages, reply edges, and recovered media by ID and hash.

The strongest new relationship is exact and non-numerological:

```text
creator message 6884 date: 2021-04-01
creator hint values:         {1}, {4}, {21}
```

Thus the three values are the post's own European-style
day/month/two-digit-year date. This does not replace their independently
reconstructed mechanical role from Phase 37 (one FEFE cell, fourth bit,
twenty-first character); it explains why the creator chose a date-shaped
presentation and posted it on April Fools' Day.

The Neo-passport evidence is more nuanced than Phase 4 reported. Message
8048, `"The only date I give away is the expiry date of neo's passport"`,
is a direct reply to a community member asking the creator's age, marital
status, and the puzzle private key. In isolation it is a playful refusal,
not an operational hint. It cannot simply be discarded, however: in 2023
the creator deliberately returned to the same detail in message 8516,
replying to the archived Matrix interrogation/mouth-sealing clip:
`"Still remarkable that scene. Especially the expiration date of his
passport"`. The recovered clip is pinned at
SHA-256 `31a9e572c213748a59f7807882c7fa36113d44138238dcf8acdc85f77fd9f2cb`.
The clip does not display the passport itself; the creator supplies that
association.

The conservative interpretation is therefore **date syntax / recognition**,
not “use 20010911 as a password.” The prop's exact visible rendering is
`11 SEP 01`; applying the same `DD MON YY` rendering to the creator post gives
`01 APR 21`. The historical `door_prime_passport_probe.py` tested several
numeric and long-month forms but none of these exact inscriptions. Closed
that small gap under the complete current textual oracle:

```text
base candidates:
  11 SEP 01, 11SEP01, 11-SEP-01, 11/SEP/01
  01 APR 21, 01APR21, 01-APR-21, 01/APR/21

answer/key forms: 180 unique keystrings
targets: SALPH, COSMIC, P32TRAILING, quarantined URLBLOB
CBC legacy+extended: 0
ECB:                 0
stream modes:        0
AES Key Wrap:        0
```

The export also recovers a previously untracked community artifact directly
about the Phase-4 operation: message 8088 replies to `"How do you open the
D O O R?"` with a 776x297 image of the modified Phase-3.2.1 Architect text
and says to compare it against the real Matrix text, remove the extra
characters, and think about primes. The exact image is
`photos/photo_268@12-04-2022_14-58-09.jpg`,
SHA-256 `c33d732ce237f7c493292c4b3aacb44a713a5b6017499cf726763193bcde2fa9`.
This is community-authored, not creator-confirmed, and it does not specify a
unique character alignment or prime operation. It is nevertheless the first
recovered evidence that directly binds all three Phase-4 verbs to a concrete
source text, so it is a better narrowly bounded follow-up than another
passphrase sweep.

**Verdict:** the old Phase-4 passphrase framing is demoted. `{1,4,21}` is both
an exact FEFE locator and the hint post's exact date; Neo's passport most
plausibly reinforces reading dates in `DD MON YY` form. Exact inscription
forms are closed negative as direct keys. The remaining actionable Phase-4
question is not another date encoding: it is whether the recovered message
8088 comparison can be reconstructed under one fixed, auditable alignment of
the custom Architect paragraph to the screenplay. No arbitrary prime mask or
AES escalation is justified until that comparison yields a uniquely defined
character stream.

## Phase 118 -- recovered Matrix-text difference instruction: fixed alignment and prime family negative (2026-07-28)

Implemented the narrowly reopened Phase-4 comparison from message 8088 in
`phase4_matrix_text_difference_audit.py`. The source scope is fixed before
any output is inspected:

- custom side: the exact solved Phase-3.2.1 plaintext mechanically extracted
  from the public walkthrough;
- reference side: only the spoken screenplay lines corresponding to that
  custom passage, excluding stage directions and unrelated intercut scenes;
- screenplay:
  `wordlists/matrix/the-matrix-reloaded-2003.pdf`, SHA-256
  `2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4`;
- every nontrivial manually scoped dialogue segment is assertion-checked
  against `pdftotext` output, with the PDF's literal `EVENTUALITV` typo
  normalized to `EVENTUALITY`;
- comparison: deterministic word-level longest common subsequence, with one
  fixed tie-break (skip the custom word on equal-length alternatives);
- character stream: letters from aligned words only. Spaces, punctuation,
  and line breaks are excluded because the recovered image's wrapping is a
  rendering artifact, not authored indexing.

The comparison yields:

```text
canonical words: 200
custom words:    336
shared words:    172
custom-only:     164
canonical-only:   28

custom-only letters: 709
shared letters:      830
```

The custom-only words are not a hidden sentence newly produced by the
comparison; they are the already-visible puzzle parody and instructions,
including `PUZZLE`, `PRIVATE KEY`, `GSMG`, `CIPHERS`, `ENCRYPTIONS`,
`PASSWORDS`, `BRUTE FORCING`, and `WILLPOWER`. This confirms what message
8088 means by “extra,” but does not itself select a password.

Applied the complete literal prime-character family to both mechanically
defined streams:

```text
stream in {custom-only, shared}
index base in {zero, one}
output in {prime-indexed characters, non-prime complement}
```

Neither prime-indexed output is readable. Three contain no clue marker from
the predeclared family (`door`, `prime`, `zero`, `matrix`, `sum`, `list`,
`yin`, `yang`, `password`, `key`, `enter`, `source`, `code`, `choice`,
`salvation`). The zero-based custom-only prime stream contains one literal
`list` inside otherwise non-language text:

```text
...oentamarocndeeplistiieulio...
```

Calibrated that observation rather than promoting it. The statistic is the
maximum matched marker length across all four prime-retained outputs. In
5,000 seeded shuffles preserving each source stream's exact character
multiset, 132 trials score at least as well:

```text
real maximum marker length: 4
null maximum counts: {0: 4329, 3: 539, 4: 120, 5: 12}
family-wise empirical p: 133/5001 = 0.02659468
```

The null produces a five-letter hit 12 times, stronger than real. The result
fails this project's `p<0.005` bar. Non-prime complements are printed but
deliberately excluded from the marker statistic because retaining most
characters necessarily preserves source words (`password`, `key`, `code`,
`sum`, `source`) and cannot constitute independent recovery.

**Verdict:** message 8088 is authentic recovered community evidence and its
strongest fixed implementation cleanly isolates the custom puzzle prose, but
does not recover a prime/zeroed instruction. The lone `list` is an ordinary
family-wise coincidence. No AES escalation ran. This closes word-aligned,
letters-only prime retention/removal under both index bases; it does not claim
to close an unspecified character-level edit alignment, prime-word indexing,
or punctuation-sensitive scheme. Those alternatives lack a creator-supported
selector and should not be searched without new evidence.

## Phase 119 -- full enumeration of barrystyle's media attachments: no second book photo (2026-07-28)

Phase 36/60 established that `@barrystyle` (`semaj`, `user925838121`) posted
the physical book's front-cover photo in message `8310` (2022-12-11), directly
confirmed by the creator's `reply_to_message_id`-linked "That is very
specific" reaction. That prior work only checked the immediate neighborhood
of that one message (`8309`-`8329`) for other attachments, not this account's
full posting history -- a real, previously-unclosed completeness gap, since
the bird's-eye reassessment doc still lists an "original `barrystyle` interior
image, if it exists at all" as an open evidence-availability question.

Enumerated every message from `user925838121` across the complete Telegram
JSON export (580 ordinary messages plus one service record). It carries
**23 media attachments**
spanning 2022-07-01 to 2025-08-09 (photos, PNG files, two video files, and two
source files -- `prime.py`, `blueyellow.cpp`). All 23 referenced files exist
on disk in the downloaded export (verified directly, not inferred from the
JSON manifest alone).

Review verification added `tools/gsmg/telegram_barrystyle_media_audit.py`,
which freezes the exact 23 message IDs, hashes every referenced file, verifies
all files exist, and reproduces the zero page-57/page-58 text matches. A
separate visual contact-sheet audit covered all 19 still-image attachments,
and representative frames were extracted from both videos. The two source
files were read directly.

The notable non-cover attachments are:

- `files/image_2023-09-03_20-33-54.png` -- a C++ brute-force snippet filling
  12 mnemonic slots from 12 macro-clue words. The nested loops permit
  repetition, so this is combinations with replacement, not permutations
  (matching its context: "there are *too many* valid mnemonics").
- `files/image_2023-09-10_10-00-10.png` (105KB) -- an unrelated
  Pepsi/Coke meme.
- `photos/photo_550@07-02-2024_07-13-54.jpg` -- a screenshot of the already
  known message-8310 cover post and the creator's replies, not a second
  physical-book image or an interior page.
- `photos/photo_1550@09-08-2025_19-13-22.jpg` (513KB, the actual largest
  still-image attachment) -- an AES/brute-force terminal screenshot.

Every other attachment's surrounding text is unambiguous: color-spiral
position questions, prime-digit-count discussion ("Barry... your prime has
182 binary digits, doesn't it?"), a base-9/checkerboard-table demo, the two
source files, meme/animation videos, and (2025) general AES-bruteforce
banter. None resembles a physical book page. Also re-scanned all of
barrystyle's messages for literal "page 57"/"page 58"/"pp. 57" text: zero
matches.

**Verdict:** this closes the completeness gap, not the evidence gap. The only
distinct physical-book content from this account remains the single
2022-12-11 front-cover photo already found in Phase 60; the 2024 screenshot
merely embeds that same post. The interior pages 57-58 do not appear as an
attachment anywhere in this account's currently retained complete export --
the physical-evidence gap stands, now on a fully enumerated basis rather than
an inference from one message's neighborhood. Deleted historical posts, if
any, are necessarily outside what a current Telegram export can prove.

## Phase 120 -- barrystyle attachment follow-up: one exact provenance artifact, no new transition clue (2026-07-28)

Audited the potentially puzzle-relevant remainder of Phase 119 rather than
treating all non-book media as equally uninteresting.

The strongest item is `files/blueyellow.cpp` (message `14943`). Compiling and
running the archived source prints exactly 196 bits. Parsing its literal
`yellow[]` array gives 196 entries with nine ones, byte-for-byte identical to
the real image's row-major yellow occupancy mask. Its code then reverses and
inverts that mask, reproducing Phase 36's exact 60-digit value:

```text
100433436204244105573859228564110291168344943733122168512511
```

This is useful provenance: Phase 36's large-prime observation is now tied to
the user's original source file rather than reconstructed from prose alone.
It does not reopen the path. Phase 36 already put the complete eight-member
color/order/inversion family inside a profile-preserving null (`p~=0.059`)
and tested exact representations against the textual oracles with zero hits.

`files/prime.py` is only a naive sequential-prime/binary printer. The adjacent
image is its terminal output; the chat explicitly says it is off-topic
visualization. It contributes no selector.

The BIP39 screenshot/video uses this fixed 12-slot pool:

```text
yellow blue matrix before give away front very step true give away
```

The visible C++ has 12 independent loops over all 12 entries, permitting
repeats rather than enumerating a permutation. It therefore defines
`12^12` slot assignments before the mnemonic checksum filter, with no
creator-confirmed ordering or derivation path. The surrounding conversation
itself records the combinatorial explosion and a contemporaneous objection
that the known vanity address does not make these words recoverable. Preserve
this as community exploration; do not launch a BIP39 search from it.

The previously untracked screenshot in message `8220` visibly points to
`github.com/barrystyle/b58`. A fresh bounded repository audit found the
public repository still available at commit
`6f0e3ad39d1fe078acc43b5f5f17bb46955e2d7b` (19 commits). Its README states
that it is a scanner for the unrelated public Bitcoin Puzzle #64, and its
complete history contains no `GSMG`, `SalPhaseIon`, `Cosmic`, rabbit,
yellow/blue, or matrix material. This is not a hidden GSMG source archive.

Finally, the complete export contains only two creator replies to this
account: message `8311` validating the book-cover attachment, and message
`8438`, a casual joke unrelated to puzzle mechanics. No other source file,
prime visualization, BIP39 attempt, or AES screenshot received creator
validation.

**Verdict:** `blueyellow.cpp` is worth preserving as exact community-source
provenance for an already-audited Phase-36 observation. Nothing else in this
account's attachments supplies a new creator-supported operation, target, or
candidate family. No further sweep is justified from this media set.

## Phase 121 -- binary-hint operand audit: one real coverage gap closed negative (2026-07-28)

Revisited the authenticated SalPhaseIon stream as a typed program, using
creator message `8446` as evidence about operand identity rather than as
another arbitrary bit mask.

Three facts jointly motivate one small, closed family:

1. message `8446` is creator-authored and only decodes after reversing its
   complete 1,288-bit stream; its plaintext begins
   `yellowblueprimesmatrixsumlist...`;
2. `yellowblueprimes` identifies creator message `1710`, the first formal
   2020 hint, and its mechanically recovered result `574061`;
3. the exact 31-character result recovered by following that chain,
   `ncsyangcahiriasogaleafayanestve`, had previously been checked only as a
   raw passphrase. It was absent from the project wordlists and had never been
   tested as the operand of the page's explicit SHA command.

`tools/gsmg/binary_hint_operand_audit.py` freezes nine exact operands:

```text
message 8446 exactly as transported (spaced bits)
message 8446 as compact bits
message 8446 packed into its 161 posted bytes
the whole-stream-reversed decoded macro
message 1710 exact text
message 1710 with whitespace collapsed
message 1710 letters-only
the first-hint result 574061
the exact 31-character selected result
```

For each it tests no-newline/LF/CRLF source forms, then only the literal,
SHA-256 raw digest, lowercase/uppercase SHA-256 hex, and the established
`ans too`-style second SHA over the first hexadecimal command output. This
produces 162 unique byte materials. All were checked against SALPH, COSMIC,
P32TRAILING, and quarantined URLBLOB under legacy and extended CBC, ECB,
CFB/OFB/CTR, and RFC 3394/5649 Key Wrap: **zero hits**.

The binary clue still contributes important grammar, just not a password:

- it fixes the high-level order
  `yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice -> yinyang`;
- it grounds “our first hint” in the yellow/blue-prime branch rather than an
  unlimited family of prior commands;
- its own plaintext explicitly says `wewontgiveawaythepassword`, arguing
  against treating the macro as a literal secret;
- whole-stream reversal is a transport property of this message, not evidence
  that the authenticated page program should be executed right-to-left. The
  decoded macro's forward order already agrees with the page's forward
  high-level order, and the creator's other binary message (`53342`) decodes
  normally without reversal.

**Verdict:** close the newly identified exact-SHA coverage gap. The creator's
binary hint should remain an ordering/type constraint and recognition guide,
not a license for broader bit permutations or password variants. The
remaining unresolved edge is still semantic: what concrete artifact counts
as reaching `yinyang` after the fixed matrix/last-words chain.

## Phase 122 -- community "found the yin yang" photo (message 10102): confirmed non-lead (2026-07-28)

While surveying every chat mention of `yin`/`yang` (459 messages) for the
`yinyang` artifact-identification effort, message `10102` (`Jerry`,
2023-08-16) posts a photo captioned "Found the yin yang"
(`photos/photo_310@16-08-2023_08-17-39.jpg`). Viewed directly: a generic
123RF stock photo of a Bitcoin coin split black/white in a yin-yang pattern,
watermarked, no visible puzzle-specific content (visual inspection only --
no steganographic/byte-level analysis was performed, nor is one warranted
given what closes this below). Jerry is not the creator (`from_id`
`user786391896`, distinct from the creator's `user9815232`).

Confirmed as a self-disclaimed joke, not a real lead, from Jerry's own two
immediate follow-ups: message `10103` ("It was there all the entire time on
Google images") and, after ArchOptic (`user6057219919`) asks what makes it
puzzle-relevant (`10104`), message `10105`: **"Just a joke nothing
related."** Closing this explicitly so it doesn't get re-flagged as an
unexamined lead in a future pass.

Also corrects an overstated claim made earlier in conversation (not in this
file): messages `10137` and `10738` -- both floating "yin-yang comes after
dbbi/faed are solved" -- are the **same person** (ArchOptic,
`user6057219919`) making the same point twice, not two independent
community members. Message `10739` (a third, unrelated user) is a generic
"yin and yang can't exist without each other" statement, not an independent
endorsement of the dbbi/faed-joint-solve theory. That theory therefore has
exactly one community proponent repeating himself -- not the multi-source
corroboration it was initially described as.

The creator's own messages (`9599`: "Once you hit a 'ying yang', you'll be
able to solve it the same day"; `39224`: "when yingyang is reached, 2 hours
max" / "It's the next phase" -- both already in
`doc/GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md`) establish only that reaching
yin-yang is a recognizable milestone shortly before completion. Neither
message, nor any other creator text found so far, connects yin-yang to
jointly solving DBBI and FAED specifically -- that link is the community's
(ArchOptic's) inference alone, not creator-sourced.

## Phase 123 -- FAED `{g,i}` VIC-style chain-addition reopening: full scope run, CLOSED NEGATIVE (2026-07-28)

Executed the highest-priority reopening identified in
`doc/GSMG_PHASE_REOPENING_REASSESSMENT.md`: whether FAED, segmented under its
own best-fit escape pair `{g,i}` (Phase 112: rank 1/36 by corrected code-IC),
carries a VIC-cipher-style additive keystream layered on top of the
checkerboard decode -- independent of, and in addition to, guessing the
checkerboard's own alphabet keyword. Phase 113 had already closed a *plain*
monoalphabetic substitution under `{g,i}` (softer negative, `p=0.0396`,
still fails the pre-registered `p<0.005` bar); this tests the different,
not-yet-closed question of an additive layer on top of it.

**Scope, exactly matching the reassessment doc's narrowing:** target FAED
only, `{g,i}` in both escape/digit orders only (not the `{h,e}` mirror, not
DBBI), the established 338,905-candidate alphabet wordlist set and the
17-candidate `wordlists/gsmg/single_fragments.txt` keystream seeds, both the
pre-checkerboard (raw 9-symbol) and post-checkerboard (decoded-letters)
chain-addition branches, both signs. `338,905 x 17 = 5,761,385` pairs,
`~46,091,080` decode-attempts.

**Before running:** hardened `tools/gsmg/chain_addition_sweep.py` to this
project's current standard (full detail in the driver's own docstring and
verified via its `--self-test`): fingerprinted exact per-alphabet-candidate
JSONL checkpoint/resume (replacing the old `--alpha-skip` conservative-
margin skip) with physical repair of a dangling interrupted-write line
rather than just in-memory quarantine, mode-0600 hits with per-hit
fingerprint provenance and hit-id dedup, `flock`-based run locking, whole-
chunk result-set validation, and deterministic synthetic positives for both
the pre and post branches round-tripped through the real AES oracle.

An external code review caught real gaps across two rounds, both
independently reproduced before accepting them. Round one (before this
result was logged): the original truncated-tail handling only quarantined a
dangling checkpoint line in memory without truncating it from disk, so a
second interrupted write later could merge onto the same fragment and
eventually corrupt a now-non-final line beyond recovery (reproduced
exactly, fixed by physical truncation on every load); no run lock existed;
hits carried no fingerprint provenance despite the docstring claiming
otherwise; a crash between writing a hit and writing its checkpoint line
could duplicate that hit on resume; the fingerprint omitted two imported
modules and the Python/cryptography versions; and the "workers only
compute" claim didn't scope out `cb_common`'s shared weak-candidate-log
side-channel (a pre-existing property of the oracle inherited by every
multiprocessing sweep script in this project, not introduced here). Round
two (after this result was already logged, applied retroactively as a
documentation/hardening-only pass): the same truncated-tail bug existed
independently in the hits-file loader (reproduced: a dangling hit line
merged with a later write, silently losing that hit's dedup id), and the
fingerprint's `cryptography.__version__` field can't detect a
relinked/rebuilt OpenSSL under an unchanged package version (now also pins
the linked OpenSSL version string directly). One second-round claim was
initially checked against the wrong field (this log's `plaintext_length`
and a literal blob name `FAED`, neither of which is how a FAED-derived
candidate would show up -- `FAED` is a checkerboard ciphertext, not an AES
blob tag) and appeared not to hold up; re-checking the correct field found
it does: six records (lines 65, 66, 69, 71, 72, 75 in
`weak_candidates_log.txt` at the time of this writing) have `passphrase_hex`
exactly 872 or 944 hex characters -- i.e. a 436- or 472-byte raw passphrase,
matching FAED's own checkerboard-decode lengths under `{g,i}`/`{h,e}`
(Phase 113's "436 codes"). Their timing is compatible with this run, but
the shared log carries no candidate/keystream/mode/run fields at all, so
attribution to this sweep specifically -- as opposed to any other script or
session that also calls `aes_try_open()` against the same three blobs --
cannot be established from the log alone. All accepted fixes were
re-verified (self-test, `py_compile`, `git diff --check`, the full
`test_cb_common` suite, and a live smoke test confirming the run lock
actually rejects a concurrent second invocation) before this entry was
finalized.

Measured real throughput before committing to the full run (16 workers):
~45-48 alphabet-candidates/sec, matching the ~2h actual wall-clock time
below -- not an estimate carried over from a different script's numbers.

**Result:** `338,905/338,905` alphabet candidates completed, **0 errors, 0
hits** (both branches, both signs, both escape/digit orders, all curated
keystream seeds), directly confirmed against the run's own checkpoint
(338,905 unique candidate digests, clean newline termination) and the
absence of any hits file. `weak_candidates_log.txt` did grow during this
run's execution window, and six of its records have 436/472-byte
passphrases matching FAED's own checkerboard-decode lengths -- consistent
with (not proof of) this sweep's own weak-tier decodes. Whether those six
records actually came from this run, a different script, or a concurrent
session is **unverifiable**: the shared log carries no per-run provenance
(no candidate/keystream/mode/source fields) to attribute any record to a
specific caller. This has no bearing on the strong-tier 0-hit conclusion
above, which is verified directly from the sweep's own checkpoint and hits
file, not from the shared log.

**Provenance note:** the completed checkpoint's header records
`driver_sha256=5d2d2b808e55f87c`, `version=1` -- the schema in place when
this run was launched. The hardening rounds above (both orchestration/
correctness fixes, not decoding logic) advanced the driver to `version=3`
under a different hash, so the current script will refuse to reuse this
checkpoint file (by design -- see its fingerprint-mismatch guard). This is
expected and requires no rerun: the checkpoint's own record of 338,905/
338,905 completed with 0 errors was independently confirmed above, and
none of the hardening changed how a candidate is decoded or tested.

**Verdict:** this closes the additive-keystream-layer reading of FAED under
`{g,i}` at full documented scope. Combined with Phase 113's closure of plain
monoalphabetic substitution under the same pair, FAED under `{g,i}` is now
negative under both the leading structural hypotheses this project has
tested. Per the reassessment doc's recommended order, next in line (lower
priority, not yet run) is the `-nopad` Tier-2 binary-key-material sweep as
background coverage; the FAED `{g,i}` autokey continuation remains lower
priority still, motivated only thematically.

## Phase 124 -- bounded yin-yang artifact inventory: no promotable artifact (2026-07-28)

Implemented Phases 1-2 of
`doc/GSMG_YINYANG_ARTIFACT_IDENTIFICATION_PLAN.md` as
`tools/gsmg/yinyang_artifact_inventory_audit.py`. The script runs no cipher
oracle and freezes exactly seven pre-registered families: `BUT/HYE`,
selected/complement text, paired page objects, first-piece polarity, the
*Cosmic Duality* book, the community `One`/`Two` pair, and hypothetical SALPH
private-key halves.

The inventory is assertion-backed rather than a prose checklist. It imports
the established first-piece, prime/matrix, Flo/Denis-mask, and page-structure
reconstructions; verifies the complete Telegram export's required message
IDs, senders, reply edges, and retained media; and pins SHA-256 hashes for the
rabbit image, Matrix screenplay PDF, archived SalPhaseIon page, complete book
OCR, creator-confirmed book-cover attachment, and both community guide images.
Any source or reconstruction drift fails the run.

The pre-registered qualification table uses four mandatory gates -- primary
provenance, visible before decryption, genuine dual structure, and correct
transition boundary -- plus an independent discriminator. Results:

| Artifact | Core gates | Independent discriminator | Local mechanics eligible |
|---|---|---|---|
| `BUT/HYE` rails | all pass | pass | **yes** |
| selected/complement | boundary fails | pass | no |
| paired page objects | duality and boundary fail | fails | no |
| first-piece polarity | boundary fails | pass | no |
| *Cosmic Duality* book | boundary fails | pass | no |
| community `One`/`Two` | provenance and boundary fail | fails | no |
| SALPH key halves | visibility and boundary fail | pass | no |

`BUT/HYE` is the only transition-adjacent qualifying artifact: it is the
immediate output of `lastwordsbeforearchichoice`, `BUT` matches the first
screenplay word after the fixed boundary, and `B <-> H` around fixed `E` is a
real native-`a-i` dual relation. It is still **not promoted**. Its complete
bounded local family was already audited -- alignment/columns, native-symbol
filtering, `H | YE | BUT`, direct password/route/hash forms, and `{h,e}`
monoalphabetic/autokey/chain-addition models -- without producing one
deterministic next object, lock, route, passphrase, or output shape.

The completed FAED `{g,i}` chain-addition negative (Phase 123) does not make
simultaneous DBBI/FAED readability more likely and cannot establish the
community working hypothesis that yin-yang emerges only after both are
solved. The inventory therefore stops under its declared rule: **no retained
artifact currently satisfies both the full evidence qualification and a
surviving deterministic downstream operation.** No new cipher sweep follows.
Full output and boundaries are recorded in
`doc/GSMG_YINYANG_ARTIFACT_INVENTORY.md`.

## Phase 125 -- black-rabbit negative-space audit: corrected adjacent pattern (2026-07-28)

Implemented `tools/gsmg/black_rabbit_negative_space_audit.py` after a visual
suggestion that the black cells below and right of the explicit white rabbit
form a second rabbit. The script writes an annotated copy to
`doc/img/gsmg_rabbit_hint_black_candidate_annotated.png`; it never modifies
the source image.

The first implementation of this audit was wrong in exactly the way a visual
review exposed: it retained only the visible rabbit's largest connected
contour, excluding two disconnected marks in the white cell beneath its
head/body. That produced a misleading 80x50 template and selected an unrelated
placement farther down the image. The implementation and annotation were
replaced rather than patched around that result.

The corrected cyan annotation retains **every** visible rabbit pixel. The
source is an exact 14x14 flat-color grid, so rebuilding those cell colors and
subtracting them from the PNG isolates exactly 1,250 deliberately changed
pixels in the complete bounding box `(150,150)-(230,215)`, including the
disconnected lower marks.

The proposed black shape is now the exact local object the visual observation
identified: rows 8-10, columns 8-12 (1-indexed), immediately below/right of
the visible rabbit. Its complete black/non-black 3x5 pattern is:

```text
...#.
#####
.##..
```

It contains eight black cells: one upper protrusion to the rabbit's right, a
five-cell body directly beneath/across it, and two lower cells. Searching the
whole 14x14 board for this complete pattern under all eight rotations/
reflections finds exactly one occurrence -- the proposed location. Even the
weaker black-cells-only subset check has no second occurrence.

For scale, the exact fixed-location probability under a uniform
87-black/109-non-black board is `2.53255e-5` (about 1 in 39,486). That is not
the honest discovery rate because the region and rabbit interpretation were
chosen after seeing the image. A 100,000-trial, seed-`20260728` shuffle gate
therefore asks the broader family-wise question: does the pattern or any of
its eight dihedral variants occur anywhere? It does in 2,446/100,000 shuffled
boards, empirical `p=0.024470`. This is suggestive but does not satisfy the
project's stricter pre-registered bars, and post-selection makes even that
number descriptive rather than confirmatory.

The Telegram export contains a relevant community post, message `3994` by
Legik, with the text `black rabbit` and an attached unannotated copy of the
puzzle image (`photos/photo_92@16-05-2020_19-14-16.jpg`, SHA-256
`9159091069cb6345b1dd23b8903d165d5ceba9a563aac1f7ce6db4f386a2e1e7`).
Its message date is 2020-05-16, but Telegram records it as edited on
2024-01-09, so the export cannot prove that the phrase itself was present in
2020. No creator confirmation was found.

**Verdict:** the correction materially improves the observation. The adjacent
black cells form a unique, compact, rabbit-like block pattern rather than the
first audit's non-unique distant template match. Retain it as a real visual
lead and possible white/black dual artifact, but not as creator-confirmed or
as an operation. Nothing here alone justifies a cipher/password sweep.

## Phase 126 -- user-drawn lower rabbit: partial transformed-sprite overlap (2026-07-28)

The Phase 125 cell pattern was not the user's intended shape. Their
`doc/img/gsmg_rabbit_hint_254marker_fullres_edited.png` proposes a second
line-art rabbit/face directly beneath and right of the explicit profile
rabbit, selectively drawing white over black cells and black over white cells.
Implemented `tools/gsmg/black_rabbit_drawn_overlay_audit.py` to compare that
specific hypothesis with the mechanically recovered explicit-rabbit mask.

The edit changes 26,333 pixels inside bounding box
`(566,560)-(779,752)`. At the source/full-resolution scale (`3.0x`), the best
of the eight rotations/reflections is a **180-degree rotation** at
`(522,556)`. It places 76.61% of the transformed explicit-rabbit pixels inside
the user's drawn mask, but explains only 32.73% of the drawn mask
(`F1=0.458665`). Allowing the small exploratory scale family `2.5x..3.5x`
selects the same 180-degree orientation at `3.5x`, but improves F1 only to
`0.473670`.

The comparison image
`doc/img/gsmg_rabbit_hint_black_drawn_fit_audit.png` marks overlap green,
user-edit-only pixels magenta, and transformed-template-only pixels cyan. It
shows a real partial alignment, especially around the central face/body, but
also shows that most of the proposed second rabbit is supplied by the manual
drawing rather than recovered by a simple source-image transform.

**Verdict:** this is a better qualitative description of the proposed
white/black dual-rabbit visual than Phase 125's 3x5 block, and the preferred
simple fit being a 180-degree rotation is thematically compatible with
duality. It is still an interpretive completion, not a mechanically revealed
hidden image: no fixed inversion, rotation, reflection, or scale reconstructs
the full drawing. Keep as a visual hypothesis requiring creator/media support,
not as a downstream operation.

## Phase 127 -- cell-classifier fix: single center-pixel sample collided with rabbit ink (2026-07-28)

Direct visual inspection of the Phase 126 comparison image caught a real bug:
the magenta-highlighted "black" rabbit-nest cell (row 8, column 7, 1-indexed)
is visibly mostly white, with only a thin rabbit-ink stroke crossing it --
not majority black as every prior audit had classified it.

**Root cause.** `first_piece_color_reconstruction.load_grid` and
`grid_spiral.load_grid` both classified each of the 14x14 grid's cells by
sampling a single pixel at the cell's exact center. Reading the real pixel
histogram for that one cell: 475/625 pixels (76.0%) are white background,
150/625 (24.0%) are black rabbit-ink; the center pixel itself happens to be
one of the ink pixels. A full board scan confirms this is the **only**
cell in the entire 196-cell grid where center-sample and majority-color
disagree -- every one of the 192 cells consumed by the validated
`gsmg.io/theseedisplanted` decode already agreed, so that decode, the
`yellowblueprime` reconstruction, and the FEFE/`{1,4,21}` result are all
completely unaffected.

**Fix.** Both `load_grid` implementations now classify each cell by majority
pixel color across the whole cell block instead of one sample point.
Verified no other cell's classification changed anywhere on the board.

**Downstream corrections, both re-verified by rerunning their audits:**

- `rabbit_hole_nest_audit.py` (Phase 64/98's cross-check of the 2020
  community diagram): the "rabbit nest" 2x2 box is now correctly **4/4
  white** -- an exact match to the diagram's own original claim ("rabbit
  nest is white box at center"), not the previously reported 3-white/1-black.
- `rabbit_nest_nibble_audit.py`: the nest nibble is now the trivial
  `0000`/hex `0` (complement `1111`/hex `F`), not `0100`/`4` (complement
  `1011`/`B`). The earlier "4/B is a real leftover-nibble checksum" claim is
  **retracted** -- it was an artifact of the sampling bug, not a genuine
  property of the grid. This sub-line of investigation is now fully closed:
  an all-zero nibble carries no signal.
- `black_rabbit_negative_space_audit.py` (Phase 125): the visible-rabbit-pixel
  mask drops from the previously reported 1,250 px to the correct **925 px**
  (the flat reconstruction no longer wrongly treats that cell's true white
  background as "different from itself"). The candidate 3x5 black pattern at
  rows 8-10/columns 8-12 does not touch column 7, so its shape, its single
  occurrence, and its qualitative verdict are unchanged; only the board's
  total black count (87 -> 86) and the resulting fixed-probability
  (2.5326e-5 -> 2.4560e-5) shift slightly. Shuffle-family empirical p stays
  in the same 0.02-0.03 band (0.023560).
- `black_rabbit_drawn_overlay_audit.py` (Phase 126): the cropped source
  rabbit template shrinks from (65,80) to the correct (65,70). Under the
  corrected crop, the previously reported "180-degree rotation, F1=0.4587"
  best fit **no longer holds as stated**: rotate_180 and rotate_270 now tie
  exactly (F1=0.3757, precision=0.7820, recall=0.2472) at the primary scale,
  and the small exploratory scale family's best (F1=0.3763, scale=3.1,
  rotate_180) is barely different. There is no single preferred orientation
  once corrected, so the earlier "thematically compatible with duality"
  framing for a unique 180-degree fit does not survive.

**Verdict:** a real, narrow, well-isolated bug, caught by eye rather than by
any automated check, that changed the numeric details of two speculative
visual leads (Phases 125/126) without touching any validated result. Both
leads keep their prior qualitative status (real-but-unconfirmed visual
observations, not creator-confirmed, not an operation) -- only their exact
statistics changed, and in Phase 126's case the correction weakens the
finding (no unique orientation) rather than strengthens it. All affected
self-tests, `python3 -m unittest discover -s tools/gsmg -p "test_*.py"`
(19/19), `compileall`, and `git diff --check` pass after the fix.

## Phase 128 -- rabbit-nest binary maze: real structure, calibrated, closed as a lead (2026-07-28)

A user hypothesis, prompted by creator message `1710` ("the rabbits nest may
contain a whole lot more" [doors]) and the already-established black/blue=1,
white/yellow/FEFE=0 partition: treat the partition itself as a maze (walls
vs. open space) and ask whether the FEFE marker cell connects through open
cells to the board's edge. Implemented `tools/gsmg/rabbit_nest_maze_audit.py`
and independently reproduced every structural claim before accepting it.

The exact clue says “one door” and “the rabbits nest may contain a whole lot
more,” not “several holes.” Although Telegram records message `1710` as
edited in 2024, creator messages `4094/4096` explicitly pointed back to it in
2020 as the official hint omitted from GitHub, so the clue itself has strong
first-party provenance. The user's
`doc/img/gsmg_grid_bit1_bit0_split.png` is a useful visualization of the
already-established binary partition, but adds no new data to it.

**Exactly reproduced, cell-for-cell:**

- From FEFE (`(8,5)`, 1-indexed), exactly **3 border cells** are reachable
  through open (bit=0) space: `(1,10)` at distance 14, `(7,14)` at distance
  18, and `(8,14)` at distance 19 -- two of the three are adjacent along the
  right edge, so this is genuinely "three cells, two boundary openings."
- The route to `(1,10)` is the **unique** shortest path (verified by dynamic
  -programming path count, not just BFS distance: exactly 1 shortest path
  exists) and its exact move string is `RRUULUURRRURUU` (14 moves).
- Cell `(6,7)` (1-indexed) is genuinely colored **yellow**, lies on that
  path, and removing it disconnects the FEFE cell from **all three**
  reachable border cells, not merely the nearest one -- a true cut vertex,
  not a coincidental bottleneck on one route only.

**Not exactly reproduced:** the reported "comparable random grids satisfy
this about 9.8% of the time" calibration. A fixed-FEFE-position,
count-preserving reshuffle of the other 195 cells, scored by the same
three-part criterion (unique shortest border route + a yellow cell on it +
that cell cutting off all reachable border cells), gives **8.2%** over
100,000 trials here (seed 20260728) -- the same rough order of magnitude,
not an exact match. The discrepancy most likely traces to an unstated
methodological difference (e.g. whether FEFE's own position is held fixed
or also reshuffled). Neither figure is precise enough, on its own, to
support a specific significance claim; both agree this configuration is
unremarkable at roughly 1-in-10-to-12, not rare.

Annotated maze at `doc/img/gsmg_rabbit_nest_maze_audit.png`: green marks the
unique shortest route, orange and cyan the two longer alternate exits
(sharing most of the same corridor), magenta marks the mandatory yellow
gateway, red marks the FEFE start.

The direct, bounded readings of the unique shortest route are all
non-language:

```text
directions: RRUULUURRRURUU
turns:      SLSLRSRSSLRLS
H/V bits:   11001001110100 = 12916
path text:  ne??deeaaaaiisi
exit text:  i..
```

The `?` positions are the two nest cells beyond the 192-bit payload. The
border cells necessarily lie on the outer spiral's URL prefix, so `i..` is
not independent confirmation.

As a sensitivity check on the null-model discrepancy, a second 50,000-trial
calibration fixed both FEFE and all four known nest cells as zeros, preserved
the real 95-zero/101-one and nine-yellow counts, and required a unique nearest
path, white-only disconnection, and a mandatory yellow gateway. It returned
`7.850%` (seed `20260728`), consistent with the first audit's `8.2%`. The
methodological choice therefore does not affect the conclusion.

**Verdict:** every exact structural claim holds and is now independently
verified and self-tested, not merely asserted. But per this project's own
standing bar, an ~8-10%-of-the-time-by-chance qualitative property, a
non-language move string, and no creator text that names a maze, route, or
direction operation are not enough to promote this to a solved "extra door."
It joins Phases 125-127 as a real, retained, unconfirmed visual/structural
lead. Per the user's own stated boundary, this does not license expanding
into arbitrary alternative path encodings or a new cipher/password sweep.

## Phase 129 -- rabbit-nest maze sensitivity check: opening blue too is a dead end (2026-07-28)

Follow-up to Phase 128: what if blue cells are opened up as well, not just
yellow -- i.e. wall = black only, instead of black+blue? Implemented
`tools/gsmg/rabbit_nest_maze_blue_open_audit.py`, reusing Phase 128's BFS/
path-count/reconstruction helpers directly rather than duplicating them.

Opening blue does not reveal a cleaner second structure; it floods the maze
and destroys the one property Phase 128 calibrated:

- Open cells rise from 95 to **110**; reachable border cells rise from 3 to
  **9**.
- Route uniqueness collapses: **0 of the 9** routes are uniquely shortest
  anymore (each has 2 to 32 tied shortest paths), versus Phase 128's exactly
  1 uniquely-shortest route out of 1 reachable-by-shortest-distance target.
  A new, much shorter (7-move) exit to `(5,1)` even appears, itself tied two
  ways.
- A dedicated shuffle calibration (20,000 trials, fixed FEFE position, seed
  20260728) shows both of those facts are individually unremarkable:
  reaching >=9 border cells happens in **44.4%** of random comparably-sized
  grids, and having zero uniquely-shortest routes happens in **43.4%** --
  both close to a coin flip, nothing like Phase 128's ~8% rate for its
  stricter three-part criterion.

**Verdict:** this confirms, rather than undermines, Phase 128's premise --
the black+blue=1 / white+yellow+FEFE=0 polarity is doing real work because
it is the same convention the validated Stage-0 spiral decode already uses,
not an arbitrary choice. Relaxing it by opening blue does not sharpen the
"extra door" hypothesis, it dissolves it into an unremarkable, highly
redundant maze. Closed negative; do not test further wall/open recombinations
without a new creator-backed reason to pick a specific one.

## Phase 130 -- `SAL[PHASE I]ON` and Phase-One "opposites attract": exact decomposition, back-reference unconfirmed, native-symbol coupling negative (2026-07-28)

A user observation gives the archived title an exact nested decomposition:

```text
SAL [PHASE I] ON
```

The inner contiguous substring is `PhaseI`; removing it leaves the outer
letters `Sal` + `on` = `Salon`, without changing or reordering any letter.
`Phase I` does have a real earlier referent in the puzzle, rather than being
merely a modern project label. The authenticated `theseedisplanted` page posts
to `/phase1verification`, and its identified song, Logic's *The Warning*,
literally labels its first stanza `Phase one` before:

```text
The seed is planted when opposites attract
Can you dig it?
It takes the physical to create the physical
```

This does **not** establish that the final title intentionally points back to
that earlier page. Creator message `6497` must not be used as support for that
claim: it explicitly contrasts “the first stage” (already cracked) with later
“salphation” (still in progress), treating them as separate stages. The
complete Telegram export shows that community user Legik independently
noticed `salphase i on` in message `8069` on 2022-04-09, but there is no
creator reply confirming that split and no exact `Salon Phase I` discussion.
The decomposition is therefore a structural observation and candidate
cross-phase reference, not creator-grounded rebus evidence. `SALON` is not an
established password, object, or instruction.

Implemented `tools/gsmg/phase_one_opposites_attract_audit.py` to test one
bounded consequence selected by the authenticated wording, rather than
reopening broad coupling transforms. At the visible native `a-i` symbol
level, it:

1. fixes the complement to `a<->i, b<->h, c<->g, d<->f, e<->e`;
2. compares mirrored DBBI against every contiguous 91-symbol FAED window;
3. includes both orientations and all 480 offsets per orientation in one
   max statistic;
4. shuffles FAED's raw symbols while preserving its exact multiset and
   repeats the complete search inside the null.

The real maximum is **21/91** complement matches, tied at forward FAED
offsets 324 and 333. Applying those two match masks to the already-aligned
91-character Phase-3.2.2 plaintext gives:

```text
offset 324 -> SECACKTPROGAFBTEREYDT
offset 333 -> AOANCAELGOANETERAEEFL
```

Neither is language. Identity alignment, reported only as a diagnostic,
maxes at 19/91.

Primary calibration:

```text
trials=20,000
seed=20260728
real_max=21
null_mean=20.532
null_median=20
null_q95=23
null_max=28
exceedances=9,176
empirical_p=0.458827
```

A second seed reproduces the result (`10,000` trials, seed `12345`,
`p=0.454655`). The synthetic self-test plants and exactly recovers a complete
nine-symbol complement alignment before either real run.

**Verdict:** `SAL[PHASE I]ON -> SALON + PHASE I` is exact, and the earlier
Phase-One stanza independently contains “opposites attract,” but no primary
source connects those facts. Treat the proposed back-reference as plausible
and unconfirmed, weaker than the creator-supported `SalVATIon -> SALVATION`
reading. The one direct raw-symbol consequence actually tested here -- align
DBBI and FAED where their native symbols are opposites -- is decisively
ordinary under its full offset/orientation null and is closed. The broader
semantic “opposites attract” angle remains open for eventual DBBI/FAED
plaintexts. Do not extend the raw result into arbitrary folds, offsets, or
password forms: Phase 12 already closed the broader raw add/subtract and
fold/repeat coupling families.

## Phase 131 -- selected-text thematic cluster: `yang`, `a leaf`, and `a nest`, with FEFE supplying the `e` (2026-07-28)

> **Significance interpretation superseded by Phase 132.** The literal words
> and event mapping remain exact, but the broad pre-existing-dictionary
> control classifies the cluster as ordinary under the load-bearing null.

A direct reread of the exact Phase-48 selected text found that the compact
ledger's “only `yang` is word-like” summary was too strong:

```text
ncsyangcahiriasogaleafayanestve
ncs YANG cahiriasog A LEAF ay A NEST ve
```

Implemented `tools/gsmg/selected_text_thematic_cluster_audit.py` to make the
observation reproducible rather than relying on visual word spotting. It maps
each word onto the exact 23-event prime walk:

```text
yang -> output[3:7],  events 4-6,   colors B/Y/B
leaf -> output[18:22], events 15-18, colors Y/B/B/Y
nest -> output[25:29], events 20-22, colors B/F/Y
```

The strongest mechanical detail is `nest`: event 20 supplies `n`, the
inserted FEFE event 21 supplies **`e`**, and yellow event 22 supplies `st`.
Thus the exceptional FEFE insertion that repairs the color/prime walk also
completes the literal rabbit-clue word `nest`. `a leaf` echoes the opening
seed/flower language; `a nest` echoes the creator's rabbit-nest clue; `yang`
matches the later reached-state vocabulary.

Exact dynamic programming over all uniformly weighted, order-preserving
31-of-91 subsets of the fixed Phase-3.2.2 plaintext gives:

```text
yang: 0.00257912677865
leaf: 0.000333089719151
nest: 0.00249011832942

all three jointly:
4,004,246,800,477,440 / 1,975,970,989,680,606,309,094,704
= 2.02647043979e-9
~= 1 in 493,468,832
```

The joint DP is self-tested against exhaustive enumeration on three small
synthetic sources. These values are **not** formal discovery p-values: `leaf`
and `nest` were noticed after inspecting the output, and no complete
creator-themed dictionary or family-wise statistic was pre-registered. The
uniform-subset model also does not represent the exact deterministic
prime/color selection process; it is the same descriptive calibration frame
used for the earlier `yang` audit.

One provenance distinction is essential. Phase 46's `0/44` result did not
leave TARGET mechanically unexplained forever; it was superseded by Phase 48,
which recovers the exact 31-position mask from Flo's literal capitalization
artifact and reproduces all 23 fitting events with the corrected
FEFE-insertion recurrence. Denis's “few trillions” statement concerns
**anagrams after extraction**, not trillions of candidate masks, so it cannot
by itself show that TARGET was selected by searching subsets for words.
However, Flo and Denis worked in the same community thread, the recurrence
was reconstructed after their result was known, and no creator reply confirms
the mask or its words. Mechanical community provenance is therefore strong;
blind-discovery provenance and creator intent remain unverified.

**Original Phase-131 verdict, now superseded:** the cluster was provisionally
retained as a low-confidence recognition checkpoint pending a family-wise
test. Phase 132 supplies that test and demotes it to preserve-only. The
`1 in 493 million` exact-three-word figure does not correct for post-hoc
choice from a broad vocabulary and must not drive a downstream
cipher/password sweep.

## Phase 132 -- family-wise selected-text calibration: interesting cluster, fails the broad-word promotion bar (2026-07-29)

Implemented `tools/gsmg/selected_text_familywise_null_audit.py` to perform
the family-wise test requested by Phase 131. Because `yang`, `leaf`, and
`nest` were already visible before this test was designed, it cannot make
their discovery preregistered. Instead it freezes two explicit controls and
states what each can and cannot establish.

### Declared creator-clue families

The first control uses five deliberately generous semantic families:

```text
plant:
  seed planted flower blossom blossoms rose leaf root stem
rabbit:
  rabbit nest door hole burrow
polarity:
  yellow blue prime primes yin yang duality opposite opposites attract
matrix:
  matrix sum list choice architect
lock:
  password key keys hash enter command answer eyes giveaway promised
```

The real string hits three families (`leaf`, `nest`, `yang`). Exact dynamic
programming over all uniformly weighted order-preserving 31-of-91 subsets
counts strings hitting at least three declared families:

```text
7,130,314,388,820,524,573
/
1,975,970,989,680,606,309,094,704
= 3.60851167657e-6
~= 1 in 277,123
```

This is much less extreme than the Phase-131 three-exact-word rate because
it correctly places the alternatives inside each declared clue family.
It still cannot carry discovery significance: the vocabulary and family
grouping were designed after seeing the three real hits.

### Broad common-English control

The safer multiple-comparisons control loads the repository's existing
`wordlists/xkcd/words.txt` (`7,887` normalized words), freezes word lengths
to 4-12, and scores the number of distinct literal dictionary substrings.
The real selection has score four:

```text
gale, leaf, nest, yang
```

The statistic allows overlapping words (`gale` and `leaf` overlap) in both
real and null strings. One million uniform order-preserving 31-of-91 subset
trials, seed `20260729`, give:

```text
5,469 / 1,000,000 at least as good
empirical p = 0.005469995
```

A separate 500,000-trial replication, seed `12345`, gives:

```text
2,750 / 500,000
empirical p = 0.005501989
```

Both settle just above this project's pre-existing `p < 0.005` promotion
bar. The secondary fixed-mask/source-shuffle control is lower
(`p=0.000836999`, replicated at `p=0.000769998`), but it destroys the
source plaintext's English order before applying the mask and is therefore
an easier null to beat. The order-preserving subset model is the conservative
load-bearing comparison for a result made of literal English substrings.

The exact family DP is self-tested against exhaustive enumeration on three
small sources. The broad-word result records the wordlist's SHA-256, both
seeds, the full score histograms, and uses the same statistic for real and
null strings.

**Verdict:** FEFE's exact role as the `e` in `nest` remains a mechanically
true descriptive fact, but the `yang`/`gale`/`leaf`/`nest` cluster is
**ordinary under the load-bearing broad-word control**. An equally word-rich
selection occurs about `0.55%` of the time -- narrowly but reproducibly
failing the project's promotion threshold even before accounting for the
many other analyses performed across this investigation. Demote the cluster
to preserve-only. Do not change the chain, declare the 31 characters
terminal, or launch a downstream sweep from it. This branch stops pending
creator evidence or an independently specified consumer.

## Phase 133 -- bounded “half / better half” key-operation audit: completed negative (2026-07-29)

The creator's two later uses of “better half” do not justify investigating
the partner's identity or constructing personal-name passwords. The
2025-04-28 use is nevertheless a plausible callback to the solved Phase
3.2.2 plaintext: immediately after describing yin-yang as the next phase,
the creator wrote `the "better half" is hungry`, echoing `THE PRIVATE KEYS
BELONG TO HALF AND BETTER HALF AND THEY ALSO NEED FUNDS TO LIVE`. This
supports a bounded audit of the two-key output interpretation, not a new
passphrase family.

`tools/gsmg/nopad_window_sweep.py` already tested the two direct 32-byte
windows, scalar sum, both ordered concatenation hashes, and XOR. The
remaining clue-supported family is now explicit, all on the same fixed
non-overlapping pair `(offset 0, offset 32)`:

```text
direct halves (already covered)
scalar sum
scalar difference a-b / b-a
scalar additive inverse -a / -b
SHA256(a||b) / SHA256(b||a)
bytewise XOR
exact relation b == -a mod secp256k1 order
exact relation a XOR b == FF...FF
public-point coordinates X||Y / Y||X
```

No other window pair, sliding offset, multiplication/division, byte
rotation, or arbitrary hash family is admitted. Both compressed and
uncompressed P2PKH addresses are checked for every scalar or valid public
point. Exact known-address checks remain first; Bloom and anchored GSMG
vanity classifications remain secondary and require external verification.
The two exact 256-bit pair relations are retained as structural hits even
when neither address is known or funded.

Synthetic controls cover every added operation, both public-point
orderings, and both exact relation detectors. The existing multiprocessing,
single-parent writer, checkpoint fingerprint, sensitive-hit storage, and
resume logic are reused unchanged. The full self-test and a real
100-keystring/4-worker smoke run completed cleanly.

The production Tier-1 corpus run was launched with 8 workers against
`525,436` keystrings and both SALPH/P32TRAILING blobs under the same 72
CBC/ECB decryptions per keystring. It uses fresh artifacts:

```text
tools/gsmg/nopad_half_better_half_checkpoint.jsonl
tools/gsmg/nopad_half_better_half_hits.jsonl
tools/gsmg/nopad_half_better_half_queue.jsonl
```

**Completed result:** `525,436 / 525,436` keystrings, zero worker errors,
zero missing or duplicate checkpoint digests, elapsed 5,260 seconds. No
`pair_relation`, `known`, or `known_public_point` classification occurred:
the exact scalar-additive-inverse relation, exact bitwise-complement
relation, and both X/Y public-point interpretations all produced zero
structural/known-address hits. Secondary classifications were:

```text
bloom=10
vanity_strong=4
vanity_weak=25
```

With explicit user approval, all 39 derived addresses were sent to the
Blockstream address API for mandatory external verification. Every record
was negative: the 10 Bloom classifications were confirmed as
`bloom_false_positive`, while all 4 strong and 25 weak anchored-GSMG vanity
classifications were relabeled `unfunded`. There were zero funded addresses
and zero known-address matches. The bounded two-key-operation family is
therefore closed negative at full Tier-1 scope.

## Phase 134 -- self-referential "our first hint" literal-string sweep: negative (2026-07-29)

Follow-up to Phase 101/102's `sha256 our first hint is your last command`
gap. Rather than an external artifact (banner, prize address, Stage-0/rabbit
images -- all already negative in `first_hint_hash_audit.py`), this tests
the self-referential reading: hash the literal words of the clue phrase
itself.

Two provenance corrections first. The often-cited 2021-01-09 chat line "my
first hint might be your last command" is **not creator-authored** --
`from_id` is `user370469246`, not the creator's fixed `user9815232` -- so it
is a community member's joke, not a creator statement, even though the
phrase does separately and genuinely appear inside the authenticated final
page (Phase 101/102 already establish that half). Separately, the early
hash the creator posted on 2019-04-22 (`5ac40783...`) was confirmed by
community reply (message `230`) to be a self-check hash for the
already-solved Phase-1 password, not an unexplored lock.

Extended `tools/gsmg/first_hint_hash_audit.py`'s `source_materials()` with
seven literal-phrase candidates: `"our first hint"` (plain, with trailing
newline, capitalized, with trailing period), `"first hint"` alone, the full
phrase `"our first hint is your last command"`, and the full phrase with
its `"sha256 "` prefix included literally. All five plain-word hash values
an AI assistant had supplied for these (pasted by the user) were
independently reverified byte-for-byte with `hashlib.sha256` before use --
all five matched exactly, so no hallucinated-hash risk carried into the
test.

Ran the existing oracle unchanged (`BLOBS` + `QUARANTINED_BLOBS`, i.e. every
open blob including SALPH/P32TRAILING/urlblob/COSMIC, both digest-raw and
digest-hex passphrase forms, CBC across `ALL_CBC_VARIANTS`, AES Key Wrap,
raw-key P2PKH derivation against the prize/halving addresses):

```text
totals: address=0 cbc=0 wrap=0 raw_key=0
```

An additional provenance review proposed the already-solved Phase-1 password
itself as the most literal `first hint` operand. That candidate was not
actually new: the exact plaintext already appears in
`lastcommand_probe.py`'s SALPH list and in the Tier-1 curated corpus. It was
nevertheless added explicitly to `first_hint_hash_audit.py`, with a
self-test fixing its byte spelling against the creator-posted digest:

```text
sha256(theflowerblossomsthroughwhatseemstobeaconcretesurface)
= 5ac407837447fba24ba2802e4d1e9aecb4580aa29fef1088cc387c180b746f75
```

That digest reproduces compressed P2PKH address
`1AD2wfwXukZ1kUAy848hTQQ72aSBZPB75r`, the already-documented Phase-1
self-check address. Against the final prize/halving addresses and every
tracked/quarantined blob under the audit's CBC, Key-Wrap, and raw-key paths,
it produces zero hits. This is useful negative evidence: the hash is real
and cryptographically consumed by the solved early stage, but does not
bridge to the open endgame targets under the established oracle families.

All thirteen candidates now tried (five original + seven self-referential +
the solved Phase-1 password) are clean endgame negatives.

**Verdict:** the self-referential "hash the clue's own words" reading is a
well-motivated, cheap-to-test idea (fits this puzzle's established taste for
wordplay, and needs no external artifact), but it does not open any
tracked blob under any established KDF/cipher combination. Does not reopen
Phase 101/102's standing verdict: the SHA operand's exact material and
binding remain unresolved, and the next foreground task is still provenance
recovery (the true "first hint," if it predates this Telegram export, may
not be recoverable from chat-mining at all), not another transform sweep.

## Phase 135 -- original-announcement provenance correction: main Telegram channel and original JPEG remain missing (2026-07-29; superseded by Phase 137)

An external-origin audit correctly established that BitcoinTalk topic
`5151725` is secondary: its 2019-06-07 opening post says “Found this on
reddit” and links Reddit post `bf7siz`. The community GitHub README likewise
labels `https://gsmg.io/puzzle` as hint 1, confirming that the first puzzle
artifact is the 14x14 grid rather than a separately documented textual
teaser.

However, calling the original-announcement candidate closed was premature.
The still-live Reddit post supplies two primary provenance details that were
missed: its body labels itself “just repost,” and the poster says the puzzle
was originally posted in the Telegram main channel `t.me/GSMG_Bot`.

This project's 57,729-message export is **not that channel**. Its metadata is
`GSMG Puzzle Solvers`, a `private_supergroup` with ID `1166734859`. Its own
earliest discussion explicitly distinguishes the sources: message `94`
says the puzzle “was posted in the main GSMG channel,” while message `101`
later supplies `https://www.gsmg.io/puzzle` as the official image URL.
References to `t.me/GSMG_Bot` remain in later messages, further confirming
that it is a separate Telegram source.

The Reddit post also records an artifact-version distinction: on
2019-06-05 the puzzle picture changed to PNG “for better hidden things
quality.” Therefore `first_hint_hash_audit.py`'s current
`full_stage0_png` candidate tests the later PNG, not necessarily the literal
original attachment. The earliest JPEG in the solver export is not that
attachment; direct inspection shows it is a 260x280 Shutterstock pixel-rabbit
reference forwarded by a community member.

**Verdict:** candidate 7 remains open as a sharply bounded provenance task,
not as an invitation to more transforms. Recover/export `@GSMG_Bot` around
2019-04-20 and preserve the exact announcement text, original image bytes,
timestamp, sender, filename, caption, forwarding metadata, and any
creator-authored follow-up explicitly identifying the first hint. Until
those bytes are obtained, do not equate the later PNG's negative hash test
with a negative test of the original first artifact.

**First `@GSMG_Bot` export attempt:** inspected
`ChatExport_2026-07-29`. It is the plausible source group (`GSMG - Community
& support group`, public supergroup ID `1246576180`), but its exported range
contains only 22,400 messages from 2018-04-17 through **2019-03-17**.
All exported media dates stop on 2019-03-17 as well. Consequently it cannot
contain either the April 2019 announcement or the 2019-06-05 JPEG-to-PNG
replacement. No split JSON/HTML file or later-dated media exists in the
export directory. Re-export this same group for at least
`2019-04-15..2019-06-10`, with photos/files enabled and JSON output.

**Superseded:** the completed re-export and original JPEG were recovered in
Phase 137. The observations about the first truncated export remain accurate;
the provenance gap does not.

## Phase 136 -- pre-rabbit “first GSMG puzzle” recovered and decoded: exact hash family negative (2026-07-29)

The user recovered a creator-forwarded announcement dated
`2019-04-01 03:55` (the Phase-7 record's `2019-03-31` date is compatible
with a timezone boundary):

```text
Here is the GSMG Puzzle! First to crack the code and retrieve a private key
may keep the hidden bitcoins. Good luck to you all!
```

It is followed by two binary-only messages totaling 5,368 bits. Exact
copies already exist in the solver export as Telegram forwards whose
`forwarded_from` field is `Jrk Bgrt` (for example messages `21403..21405`),
so the payload and creator attribution do not depend on manually transcribed
text. Community context at messages `21406..21410` explicitly distinguishes
this old puzzle from the later `gsmg.io/puzzle` rabbit puzzle.

`tools/gsmg/first_puzzle_announcement_audit.py` reconstructs the complete
chain with hard assertions:

1. concatenate the two binary messages and decode 8-bit bytes;
2. reverse the leading text to obtain
   `HOW_DID_CAESAR_SEND_HIS_MESSAGES?...THE_NUMBER_C_IS_THE_2ND_HINT?`;
3. Caesar-decode with shift 3 to obtain
   `removethecorrecthinttoproceedtothenextstage`;
4. Caesar-decode the trailing `hvuhyhu`, then reverse it to obtain
   `reverse`;
5. reverse the inner bitstream and decode it to
   `BASE64aHR0...`;
6. Base64-decode the payload to
   `https://www.youtube.com/watch?v=dQw4w9WgXcQ`.

The terminal result is the Rick Astley URL already noted in Phase 7.
What changes is its provenance relevance: the caption genuinely calls this
the GSMG puzzle, so it is a reasonable literal candidate for “our first
hint,” even though it is an April-Fools-style troll and predates the rabbit
puzzle.

The audit freezes ten mechanical source states—no case/punctuation variants
or song-title associations:

```text
announcement caption
exact 5,368-character binary payload
671-byte outer binary decode
literal Caesar question
decoded Caesar instruction
literal reverse command
reversed-inner BASE64 text
literal BASE64 command
Base64 payload
final URL
```

For each state, SHA-256 raw bytes and hex text were tested against every
tracked/quarantined blob through the established extended CBC and AES
Key-Wrap oracles; the 32-byte digest was also tested as a direct raw key and
against the final prize/halving addresses:

```text
totals: address=0 cbc=0 wrap=0 raw_key=0
```

**Verdict:** the pre-rabbit first puzzle is now a recovered, reproducible
artifact rather than a vague missing-announcement theory. Its exact
mechanical states do not satisfy the endgame `sha256 our first hint...`
lock under established oracle families. This does not test post-hoc external
metadata such as the song title or artist, and none is justified by the
payload's own command chain. The later rabbit-puzzle announcement and
original JPEG were still a separate provenance gap at this point; Phase 137
subsequently closes it.

## Phase 137 -- complete public support-group export and original rabbit JPEG recovered (2026-07-29)

The completed Telegram Desktop export at
`ChatExport_2026-07-29 (2)` is the full `GSMG - Community & support group`
history (public supergroup ID `1246576180`):

```text
52,851 messages
50,249 message / 2,602 service records
2018-04-17T17:53:43 through 2026-07-28T18:06:33
5,419 records from creator ID user9815232
```

`tools/gsmg/support_group_export_delta_audit.py` verifies those invariants,
the bounded creator evidence below, and two important cross-export controls:

1. every one of the earlier truncated export's 22,400 messages has an exact
   matching signature in the full export;
2. original support-group messages `25986..25988` are byte-identical to the
   creator-attributed forwards in solver-group messages `21403..21405`
   (text lengths `127/4096/1272`).

The first rabbit-puzzle post is now primary evidence. Creator message `28507`
on 2019-04-19 attaches
`photos/photo_962@19-04-2019_20-36-30.jpg` with the caption “Well, good luck I
guess.” The exported attachment is preserved as:

```text
doc/img/gsmg_stage0_original_telegram.jpg
JPEG, 862x1280
sha256 9e2a1473933636ea041581e4e0d795c75298b3a8fac52a21cc048e40e9d903a3
```

It has the same visible Stage-0 grid/banner/address composition as the later
1048x1556 PNG, but the formats and bytes are distinct. Community message
`28927` explicitly noticed the JPEG/PNG distinction. The reply “doesnt
matter, no steg in it” at `28930` is community-authored, not creator
confirmation.

The exact JPEG bytes were added to `first_hint_hash_audit.py`. Its SHA-256,
tested as raw/hex passphrase through extended CBC and AES Key Wrap, as a
direct raw key, and as a secp256k1 key against the known addresses, produced:

```text
address=0 cbc=0 wrap=0 raw_key=0
```

This closes Phase 135's exact-original-attachment SHA gap under the
established oracle family. It does not establish that Telegram's recompressed
photo bytes equal the creator's pre-upload local file, and it does not justify
new image-steganography transforms.

The export also restores previously undocumented primary context:

- `28522`, replying directly to “when hint?”, says “Follow the white rabbit”;
- `28526..28527` says the GSMG vanity generation took seconds, involved “Only
  4 chars,” and that the `1`s take longer;
- `28534` and `28571` fix the output as one private key;
- `28703` explains the changing Stage-1 form token as anti-bruteforce;
- `28812` says the puzzle page contains all required information;
- `29123` describes Phase-3 success detection as hash-like, while `29132`
  explicitly says another supplied hash after Stage 2 would not help.

These statements improve provenance and constrain historical web behavior,
but reveal no new operation at the current DBBI/FAED boundary. The full export
therefore closes a major evidence gap without reopening another broad cipher
or image-transform search.

## Phase 138 -- full creator-message hint review: two literal gaps closed; simplicity boundary strengthened (2026-07-29)

Reviewed all `5,419` creator-ID records in the complete public support-group
export through three bounded lenses: explicit puzzle/clue vocabulary, creator
replies to puzzle-related parent messages, and creator-attached media with
their surrounding thread. Candidate statements were then compared against
the solver-group clue index rather than treated as independent merely because
they occur in another group.

Two exact “first hint” candidates had genuinely escaped the earlier audits.

First, support-group message `26065` is explicitly labeled by the creator:

```text
First external hint:
http://lmgtfy.com/?q=How+did+caesar+send+his+messages%3F
```

Phase 136 tested the announcement's decoded states but not this literal URL
or its exact decoded query, `How did caesar send his messages?`. Both were
added to `first_puzzle_announcement_audit.py` without case, punctuation, or
URL variants. Each SHA-256 failed known-address, extended-CBC, AES-Key-Wrap,
and raw-key checks against all tracked/quarantined blobs.

Second, message `28522` is a direct creator reply to “when hint?”:
`Follow the white rabbit. 😉`. `first_hint_hash_audit.py` now tests the closed
three-member family fixed by creator text:

```text
Follow the white rabbit. 😉
Follow the white rabbit
followthewhiterabbit
```

The final form is not an invented normalization: the creator posts that exact
concatenated token at support messages `35283` and `36714`. All three are
negative under the same known-address/CBC/Key-Wrap/raw-key coverage. Combined
with Phase 137's exact-JPEG negative, the obvious literal rabbit-first-hint
SHA family is now closed.

Several additional messages improve interpretation but do not select a new
endgame operation:

- `28866`, in the original rabbit discussion, says “I can only show you the
  door.” This is early first-party Matrix/door framing, consistent with the
  later “another door” clues but not a new transform.
- `28961` says there may be a tiny rabbit-phase hint in GSMG's Slack music
  channel. The exact Slack post is unavailable because the free Slack history
  expired; the clue most naturally points to the already-solved *The Warning*
  song/lyrics route.
- `28794` says scanning GSMG generally “Won't work,” while `28812` says the
  puzzle page contains all necessary information. This argues against broad
  website archaeology without a creator-selected artifact.
- `42540` says the creator contributed but did not make it entirely alone.
  The 2026 retrospective at `67741` is more specific: JRK was inspired by
  other crypto puzzles and spent “two sloppy days throwing one together,”
  with grammatical mistakes and little polish.
- The same retrospective uses “better half” naturally for the creator's
  partner. That phrase remains real in the Phase-3.2.2 plaintext, but its
  recurrence is not by itself evidence of a special personal-name key.

One tempting short reply remains unusable: `28548` says “Depends how you look
at it,” but replies to deleted message `28547`. Without the proposition, it
cannot confirm any interpretation.

**Verdict:** no hidden creator reply or media attachment supplies the missing
DBBI/FAED operation. The strongest new methodological evidence is the
creator's own description of a quickly assembled, imperfect puzzle. Future
work should prefer short, visible, clue-selected mechanics—especially the
literal `matrixsumlist` transition—over elaborate multi-layer constructions
that require treating every typo or coincidence as intentional.

## Phase 139 -- literal yellow/blue prime-list sums: a secondary 401/400 observation, no downstream instruction (2026-07-29)

Reassessed only simple list/matrix operations directly selected by the
authenticated ordering `yellowblueprimes -> matrixsumlist`. Prior work had
already covered reshaping the 31 selected characters, the 91-bit mask as
`7x13`/`13x7`, row/column sums and reads, `[23,16,7]` indexing, repeated
Caesar operations, and keyed permutations.

One alternative literal operation had not been recorded: group the sequential
event primes by the established event colors over the mechanically fixed first
23 events that fit inside DBBI, then sum each list:

```text
B: 2,3,5,7,13,17,19,31,37,41,43,53,59,71 -> 401
Y: 11,23,29,47,61,67,79,83                -> 400
F: 73                                      -> 73
```

The blue/yellow sums differ by exactly one. An exact exhaustive null over all
`C(22,8)=319,770` assignments of those same 22 non-FEFE primes to 8 yellow
and 14 blue positions finds `813` assignments with absolute difference at
most one:

```text
813 / 319770 = 0.0025424524
```

This clears the project's usual `0.005` descriptive threshold under that
narrow family, but it is not presented as a formal discovery p-value because
the relation was noticed after inspecting an already heavily studied stream.
More importantly, the recovered historical Telegram guide already selects a
different operation: placing the DBBI chunks into a `14x14` matrix and summing
its rows to obtain `IZLKESEEDQPPEN`. The `401/400` relation is therefore not
the leading interpretation of the guide.
Its boundary choices are explicit and load-bearing:

- FEFE is kept separate because its actual pixel is neither yellow nor blue
  and the clue names only yellow/blue; folding it into blue gives `474` vs
  `400`, difference `74`;
- events 24 and 25 are excluded because they no longer fit inside DBBI and
  already land in the bytes of `matrixsumlist`; including all 25 gives
  `490` vs `497`, difference `7`.

The immediate next-clue consumer was tested without adding transforms.
The complete screenplay scene through the Architect's `choice` contains
1,326 words. One-based forward/backward indexing at `401`, `400`, and `73`
yields no readable instruction; the backward words are respectively
`it`, `INT`, and `truth`. The established Architect-spoken extraction has
only 72 words, so it cannot consume 400/401 at all.

Implemented `tools/gsmg/matrixsumlist_color_prime_audit.py`, including an
exact combinatorial calibration checked against brute-force synthetic cases
and assertions for both boundary alternatives.

**Verdict:** `401/400` is a notable but unselected secondary observation. It
does not supersede Phase 53's recovered matrix-row-sum guide, recover what
consumes the DBBI selection, or produce a password. Do not promote HTTP status
codes, digit sums, modular reductions, or cipher operations without
creator-backed evidence selecting them.

## Phase 140 -- recovered-guide row/column family: calibrated negative (2026-07-29)

Closed the only equally literal matrix direction not included in Phase 53.
`tools/gsmg/telegram_yellow_blue_matrix_direction_audit.py` applies the
historical guide's exact modulo-26 sum rendering to a fixed four-member family:

```text
rows forward:     IZLKESEEDQPPEN
rows reverse:     NEPPQDEESEKLZI
columns forward:  GBCXQOGEDMHFEV
columns reverse:  VEFHMDEGOQXCBG
```

The two main diagonal sums are `35` and `83`, rendering as `JF` (or `FJ` in
reverse). They are reported but excluded from language scoring because a
two-character quadgram statistic is not meaningful.

The endpoint-assignment null preserves the complete historical DBBI chunk
multiset, fixed first-piece endpoints, canonical placement rule, and all four
row/column directions inside one max statistic. The original row direction
remains the real best output, but is ordinary once the complete family is
accounted for:

```text
seed 20260729,  5,000 trials:  592/5000,  p=0.118576
seed 424242,   20,000 trials: 2382/20000, p=0.119144
```

The independent replication is effectively identical. A permanent regression
in `tools/gsmg/test_recent_audits.py` fixes the four outputs, both diagonal
orders, and the real best direction.

**Verdict:** the literal row/column extension of the recovered guide is closed
negative. The visible `SEED` substring remains a historical community
observation, not an exceptional output under the family-wise null. No further
matrix orientations, diagonal families, permutations, typo repairs, password
tests, or cipher escalation are justified without new primary evidence.

## Phase 141 -- recovered-guide Caesar extension: decisively negative (2026-07-29)

Tested the remaining bounded suggestion that the matrix output needs a Caesar
shift. Reversal was already inside Phase 140. The extension places every
uniform Caesar shift of all four row/column directions inside the same
endpoint-assignment max statistic: `4 x 26 = 104` outputs per real or shuffled
assignment.

The best real member is not readable:

```text
rows_forward +4 -> MDPOIWIIHUTTIR
score=-6.289683
```

The complete family is substantially worse than ordinary shuffled assignments:

```text
seed 20260729,  5,000 trials:  3565/5000,  p=0.713057
seed 424242,   20,000 trials: 14275/20000, p=0.713764
```

Implemented as the reproducible `--caesar` option in
`tools/gsmg/telegram_yellow_blue_matrix_direction_audit.py`; zero shift is
included, so the original and reversed outputs remain controls inside the
same family.

**Verdict:** Caesar, reversal, and Caesar-plus-reversal are closed negative for
the recovered guide's literal row/column outputs. Do not add affine shifts,
Vigenere keys, typo repairs, or password tests without a new clue selecting
them.

## Phase 142 -- `401 symbols / 400 spaces` SalPhaseIon boundary audit: identity, no selected span (2026-08-01)

Checked whether Phase 139's blue/yellow prime sums select a natural region in
the original SalPhaseIon textarea. The archived source is exactly:

```text
1,075 logical symbols + 1,074 single spaces = 2,149 source characters
```

Therefore any contiguous rendering of 401 logical symbols necessarily has 400
internal spaces. In particular, the prefix through the 401st symbol has source
length `401 + 400 = 801`, but this is an identity of single-space-separated
formatting rather than independent corroboration.

`tools/gsmg/salphaseion_401_span_audit.py` tests the bounded direct readings:

- no pair of established segment boundaries encloses exactly 401 logical
  symbols;
- the 401-symbol prefix is `91 DBBI + 104 matrixsumlist bits + 206 FAED`, so
  its FAED endpoint is not otherwise selected;
- one-based logical indexing at blue `401`, yellow `400`, and FEFE `73` gives
  `EIE` forward and `AF0` backward;
- treating symbols and spaces as separate ranked channels places the 400th
  space at raw position 800 immediately before the 401st symbol at raw position
  801. That selects only FAED-local symbol 206, `e`;
- 14 one-sided 401-symbol windows can be anchored at an established boundary,
  but none has both endpoints established, leaving the other endpoint as an
  unconstrained choice.

**Verdict:** the 401/400 balance accurately describes the textarea's alternating
rendering, but does not select a unique span, boundary, instruction, or key.
The direct page application is closed; do not score or decrypt arbitrary
401-symbol windows without new evidence choosing an anchor.

## Phase 143 -- Cosmic Duality last-column base64 decode: real structure, oracle negative (2026-08-04)

An externally-sourced writeup (not produced by this project's own tooling)
claimed that taking the literal final character of each of Cosmic Duality's
28 authored 64-character lines and base64-decoding the result yields a byte
string starting `7a20fe`, echoing the unique `FEFEFE` first-piece marker
color. Because the writeup also contained citations that did not check out
(a `FINDINGS.md` quote attributed to the wrong line, a "0 hits" test claim
for unrelated `SALVATION` letter-arithmetic with no corresponding script or
log anywhere in this repo, and a claim that the creator's `3901`/`3902`/`3923`
Telegram messages newly justify the SalPhaseIon/Cosmic-Duality half/better-half
pairing when that exact pairing, using that exact creator-quote
justification, was already closed negative in Phase 133), the last-column
claim itself was independently re-derived from the live site mirror rather
than trusted:

```text
last characters (28 lines): eiD+h6o+bjh0Zn/PxujDQlRRZs4G
base64-decoded (21 bytes):  7a20fe87aa3e6e3874667fcfc6e8c342545166ce06
```

This part is real and mechanically reproducible. Tested the bounded,
clue-motivated follow-up the writeup itself proposed -- the raw 21-byte
string, its hex form, and the single `FE` (0xfe, the byte immediately
following the `7a20` prefix) mutated to `AA` (base64 zero value) as a
control -- against all tracked blobs via both `cb_common.aes_try_open`
(password/KDF forms) and `cb_common.raw_key_try_open` (direct key
material): 0 hits for original and mutated forms alike.

**Verdict:** the last-column decode is a genuine, previously-unflagged
structural fact about Cosmic Duality's authored line lengths, but it is not
a password or key by itself under the supported oracle families. Do not
trust unverified test claims from outside writeups without re-deriving them
against this repo's actual files first -- this one was roughly half real
(structure, Telegram quotes) and half fabricated or already-closed
(citation, SALVATION test claim, half/better-half "new evidence" framing).

Generalized and closed the same line-column idea completely rather than
leaving only the last column tested:

- All 64 column positions (28 chars each, evenly divisible by 4, so every
  column decodes without padding ambiguity) were extracted and base64
  -decoded independently. None shows a printable/English signal above noise
  (`cb_common.printable_z_score` max 1.78 across all 64, vs. this project's
  z>=8 strong-hit gate); column 63 (the one above) is not even the top
  scorer. All 64, tried as password/hex/raw-key forms against every tracked
  blob: 192 attempts, 0 hits.
- Column-major concatenation (the full matrix transpose, flattened
  column-by-column into one 1792-character string, then base64-decoded as a
  single blob) was tested in three orientations (top-to-bottom,
  bottom-to-top, right-to-left columns): none starts with the `Salted__`
  OpenSSL header, none shows printable signal, 0 oracle hits.

This last result has a structural explanation, not just bad luck: the
established row-major concatenation (`page_structure_audit.py:166,172`,
newlines stripped, whole textarea decoded as one blob) is the one that
produces the `Salted__` header and matches the project's real known
ciphertext (`matches_known_blob: True`). That confirms the text was
authored and pasted in plain reading order; AES-CBC ciphertext is
byte-order-sensitive, so any transpose of it is expected to decode to noise
rather than an alternate valid message, absent a specific claim that line
-wrap position itself is a second covert channel -- which the per-column
scan above already tested and closed.

**Both the per-column and column-major-transpose branches of this idea are
now closed negative.** Do not re-run row/column permutations of Cosmic
Duality's line-wrapped text without new evidence pointing at a specific
different permutation rule.

Two smaller follow-up checks, both negative:

- **Row decoding is not an independent axis.** Because each line is exactly
  64 characters (a multiple of 4), per-row base64 decoding is byte-identical
  to chopping the real, already-known whole-blob decode into 28 pieces of 48
  bytes -- confirmed directly (`b''.join(base64.b64decode(l) for l in
  lines) == base64.b64decode(''.join(lines))`). Row 0's `Salted__` header is
  therefore the real ciphertext header, not a new signal; there was never a
  distinct "per-row" hypothesis to test, unlike columns.
- **Columns are not SHA-1 digests.** Every column decodes to 21 bytes (28
  base64 chars is fixed at 21 bytes exactly); SHA-1 digests are always 20
  bytes, so no column can be a raw digest as-is. Trimmed by one byte from
  either end and compared against SHA-1 of this investigation's 21 most
  established clue strings (`gsmg.io/theseedisplanted`, `574061`,
  `matrixsumlist`, `BUT`/`HYE`/`EOL`/`HEY`, `SALVATION`, etc.): 128
  comparisons, 0 matches.

A full ASCII dump of all 28 row and 64 column decodes is saved at
`tools/gsmg/cosmic_row_col_ascii_dump.md` for reference. One surface
coincidence noted there (column 32 contains the literal bytes `MD5`) was
checked against chance (`(1/256)^3` per position x 1216 tested positions =
~7x10^-5 expected) and is locally unusual, but given 140+ prior phases of
exactly this kind of pattern-hunting across this project (and two prior
confirmed instances of the same trap, the `yang` cross-phase claim), it is
noted rather than treated as a lead; it is already covered by the negative
oracle sweep above.

This one is thematically closer to home than an arbitrary word would be --
`md5` is a real KDF digest option this project's own oracle has always
tested (`cb_common.KDF_VARIANTS`, `sha256`/`md5`/`sha1`), because `openssl
enc`'s default digest was MD5 until OpenSSL 1.1.0, before this puzzle's 2019
launch (`doc/GSMG_SCRIPT_CODE_REVIEW.md:66-68`). It still does not clear the
bar for a lead, for two independent reasons: (1) unlike `EOL`->column 63,
which was selected by an independent derivation chain before anyone looked
at the data, column 32 has no such justification -- it was noticed only
after brute-enumerating all 64, the exact pattern this project's `yang`
precedent warns about; (2) MD5-KDF coverage is not gated behind this
observation at all -- every password candidate against every blob is
already tried under all three KDF digests by default, and the specific
combination `COSMIC / MD5-AES128` was already run across the full candidate
corpus and logged as a below-threshold false positive (`FINDINGS.md:1161`,
z=5.0268, z>=8 required for a strong hit). There is no new candidate or KDF
choice this observation unlocks that was not already being tested.

## Phase 144 -- `-nopad` Tier-2 binary-key-material sweep: completed, clean negative (2026-08-05)

Executes the one remaining bounded coverage item from
`doc/GSMG_PHASE_REOPENING_REASSESSMENT.md` ("Secondary Background Coverage"):
the `-nopad` fixed-window sweep over the frozen Tier-2 puzzle-derived
candidate set, which had completed only Tier 1 (Phase 100).

Run (`tools/gsmg/nopad_window_tier2_run.log`, dedicated fingerprinted
checkpoint/hits/queue files `nopad_window_tier2_*.jsonl`):

```bash
python3 nopad_window_sweep.py \
  --candidate-file ../../wordlists/gsmg/medium_curated_tier2_derived.txt \
  --checkpoint nopad_window_tier2_checkpoint.jsonl \
  --hits nopad_window_tier2_hits.jsonl \
  --queue nopad_window_tier2_api_queue.jsonl \
  --workers 16 --chunk-size 100
```

Scope self-reported by the driver and matching the pre-registered Tier-2
figures exactly: 10,590 candidates -> 209,178 unique keystrings, 72
operations/key (windows [0,16,32,48], combo pair [0,32], hex offsets [0,16],
WIF lengths [51,52], all CBC/ECB cipher-KDF variants against all tracked
blobs). Completed 209,178/209,178 in 1,891s at ~110 keystrings/s, 0 errors,
0 missing, 0 duplicate digests on the completion audit.

Result: 16 structural hits, all resolved via Blockstream API verification
(`binary_key_material_backfill.py --verify-queue`, then
`--relabel-vanity-queue`):

- 6 Bloom hits: all filter false positives.
- 10 vanity-prefix (`1GSMG...`) hits (1 strong / 9 weak): all unfunded --
  consistent with the driver's own coincidence expectation at this scale,
  not with vanity mining.

**Zero known or funded addresses.** Combined with padded Tier-1/Tier-2
(Phase 90) and `-nopad` Tier-1 (Phase 100), the `PRIVATE KEYS BELONG TO HALF
AND BETTER HALF` output-shape hypothesis is now exhausted over the full
three-tier curated candidate corpus under both padded and `-nopad` window
models. Do not re-run this tier without a new candidate source or a new
window/offset rule.

Remaining unrun compute after this phase: only the FAED `{g,i}` large-
dictionary autokey continuation `[54,250,338,905)`, which stays deprioritized
(thematic motivation only; driver still lacks fingerprinted exact-resume
hardening per `doc/GSMG_PHASE_REOPENING_REASSESSMENT.md`).

## Phase 145 -- non-standard N-escape checkerboard topology (N=3, N=4): calibrated, closed negative (2026-08-06)

Tests whether dbbi/faed use more than 2 escape leaders (3 or 4, out of the 9
raw a-i symbols) instead of the validated N=2 `{b,e}`/`{g,i}` model -- raised
in discussion as a way a "non-standard bounded topology" (6 direct + 3 rows
of 6 = 24 letters, or 5 direct + 4 rows of 5 = 25) might explain the
quadgram-hillclimb failure under the N=2 model.

`tools/gsmg/n_escape_topology_audit.py` generalizes
`checkerboard_code_ic_oracle.py`'s (Phase 106/112) `segment_codes()`/
`code_ic()` alphabet-independent escape-pair oracle from pairs to escape SETS
of arbitrary size, using the classical unrestricted construction (any of the
9 symbols, including another escape leader, may follow an escape leader).
Self-test reproduces Phase 106/112's N=2 result exactly (dbbi -> `{b,e}`,
faed -> `{g,i}`, both rank 1/36) via this script's own generalized segmenter
before trusting any N=3/N=4 output.

**Raw result looked promising at first glance** -- several N=3/N=4 escape
sets land IC even closer to English (0.067) than the established N=2
winners, especially for faed (N=3 best dist=0.00017 vs. N=2's 0.00729).
**This is fully an artifact of multiple testing, not signal.** With C(9,3)=84
combos tried at N=3 (vs. 36 at N=2) and C(9,4)=126 at N=4, landing close to
English by chance alone gets easier purely from trying more candidates.
Calibrated directly: 1000 shuffles of each target's own raw symbol multiset
(preserves exact per-symbol frequency, destroys any real checkerboard
structure), re-running the identical "best of C(9,N) combos" search on each
shuffle. Sanity check first: N=2 dbbi reproduces the known-real result
(p=0.017, beats the null, as expected). Then N=3/N=4, both targets:

- dbbi N=3 p=0.105, N=4 p=0.075
- faed N=3 p=0.375, N=4 p=0.400

None beat the null -- not exceptional versus multiple-testing noise alone.

**Separately, and independent of the statistics**: every top-ranked
candidate at N=3/N=4, for both targets, contains at least one code in the
real ciphertext whose second digit is itself an escape leader
(escape-follows-escape). The specific "restricted" 6+3x6/5+4x5 topology
proposed in discussion -- which requires forbidding escape-following-escape
to land on a round total code count -- is therefore structurally
**impossible** to construct for every one of those candidates regardless of
any statistical result. That restriction also has no precedent in classical
straddling-checkerboard design or in this puzzle's own validated N=2
construction (which happily allows escape-following-escape: dbbi's own
`{b,e}` has 15 such codes).

**Verdict: closed negative on both grounds.** Don't re-run at N=3/N=4 without
a new, differently-motivated construction rule -- this exact idea (more
escape leaders, optionally with a no-escape-follows-escape restriction) is
exhausted.

## Phase 146 -- short-period Bifid/Trifid-style block fractionation: calibrated, closed negative (2026-08-06)

Tests whether dbbi/faed carry a short-period, Bifid/Trifid-style
cross-symbol fractionation layer -- raised in discussion as "true Trifid."
Clarified first: a literal 3-coordinate/27-cell Trifid cube doesn't map onto
a 9-symbol raw alphabet without inventing a third coordinate that doesn't
exist in the data (each raw symbol only supplies 2 ternary digits via the
established dual-ternary factorization, [[dual_ternary_sweep.py]]'s
identity-symmetry mapping -- a 2D/Bifid-style factorization, not 3D). What
that earlier dual-ternary work never tested is Bifid's actual distinguishing
mechanic: a short, FIXED period block (its own whole-message matrix routes
matched dbbi/faed's own full dimensions, effectively one giant block, not
short periods the way Bifid/Trifid are classically used, often tied to a
short keyword length).

`tools/gsmg/block_fractionation_audit.py` implements the classic Bifid block
mechanic over this project's 3x3 symbol square: per block of L raw symbols,
write the L row-trits then L col-trits as one flat 2L-digit sequence,
re-chunk into L new (row,col) pairs by taking two consecutive digits at a
time, map back to raw symbols. `decrypt_block` (what you'd apply to
ciphertext to undo a fractionation layer) is the exact inverse of
`encrypt_block` -- round-trip self-tested across 200 random streams x 6
periods before trusting anything downstream.

**Power calibration first** (does this test even detect fractionation when
it's really there?): built real English-checkerboard-encoded synthetic
ciphertexts (reusing `checkerboard_code_ic_oracle.py`'s `length_matched_trial`
for faed, whose exact 25/25-type profile is impractical to hit directly --
already established in that module's own docstring) and fractionated them at
several short periods. Confirmed real, detectable degradation: dbbi's clean
code-IC (0.072) shifts to 0.062-0.087 depending on period; faed's clean
code-IC (0.116) shifts to 0.083-0.091. The test has genuine power.

**Real dbbi/faed, periods 2-15, un-fractionating (decrypt_block) then
re-scoring code-IC under each target's established best escape pair**: for
BOTH targets, the raw UNFRACTIONATED stream is already at or near the best
fit to English among every period tested -- undoing fractionation at any
period either makes the fit worse or is statistically indistinguishable from
noise. Null-calibrated the same way as Phase 145 (500 shuffles of each
target's own symbols, best-of-14-periods each): dbbi p=0.7785, faed p=0.4680
-- neither beats multiple-testing noise.

This is also a clean result on independent logical grounds, matching this
project's existing precedent for ruling out VIC-style additive keystreams on
`dbbi` via IC smoothing (`doc/GSMG_PUZZLE.md`'s Kasiski/Friedman work): a
genuinely fractionated ciphertext should show a *degraded/scrambled* code-IC
relative to a clean one, and both targets' raw code-IC is already
essentially optimal under their established escape pairs (Phase 106/112) --
that is evidence against a fractionation layer being present, not merely an
absence of evidence for one.

**Verdict: closed negative, calibrated on both statistical and mechanistic
grounds.** Don't re-run short-period block fractionation without a
genuinely different transform -- this idea, and the closely-related
whole-message dual-ternary streams it was checked against, are both
exhausted now.

Remaining unrun compute after these two phases is unchanged from Phase 144:
only the FAED `{g,i}` large-dictionary autokey continuation
`[54,250,338,905)`, still deprioritized. Both structural alternatives raised
in the discussion that prompted these two phases are now closed on the same
calibrated footing as everything else in the project -- the single
highest-priority open item remains recovering the physical *Cosmic Duality*
book's pages 57-58 (a copy has been ordered as of this writing, ETA
1-2 weeks).

## Phase 147 -- `YOUWON` tail direct-key decode: external-catalog reading tested, closed negative (2026-08-06)

An external write-up re-raised `doc/GSMG_EXTERNAL_ARCHIVE_AUDIT.md`'s
`YOUWON` finding (Phase 74/75), proposing that the 64-character tail after
`YOUWON` is a raw private key under an unspecified "custom 16-character
alphabetic hex mapping (A-P or A-Z mod 16)" -- without running the
character-set audit it itself proposed as the first verification step.

Running that audit first: the tail has 24 distinct letters (missing only H
and I), immediately incompatible with a bijective 16-letter alphabet such as
A-P -- Q through Z all appear in the payload. That specific framing is dead
on arrival. The only coherent surviving reading is a non-bijective modulo-16
mapping (all 26 letters wrap onto the 16 hex digits), which is a genuinely
different test from Phase 75's: that phase tested the tail only as CBC/KDF
**passphrase** text, never as a directly **decoded** raw key.

`tools/gsmg/youwon_direct_key_derivation_audit.py` derives the payload from
[[youwon_partition_audit.py]] itself (not a hardcoded copy, so it can't drift
from Phase 75's established value), self-tests the 24-unique-letter count,
then builds five 32-byte candidates: three modulo-16 nibble-pairing variants
(0-indexed hi/lo, 0-indexed lo/hi, 1-indexed hi/lo) plus two SHA-256-of-
payload seed controls. Each candidate is checked three ways: (1) directly as
a secp256k1 private key, comparing compressed/uncompressed P2PKH addresses
against the known prize and halving addresses; (2) as a raw (non-KDF)
AES-256 key against SALPH/P32TRAILING via `cb_common.raw_key_try_open` --
the "private key | private key" raw-key reading
`binary_key_material_backfill.py`'s docstring describes; (3) optionally,
live against the Blockstream API for any on-chain transaction history at
all, independent of matching a *known* GSMG address.

All three checks are negative for all five candidates: no known-address
match, no raw-key AES hit, and zero transaction history on every one of the
ten derived addresses (rerun live via `--verify-api`).

**Verdict:** the external catalog's specific reading is refuted by its own
proposed check, and the one part of it that was structurally coherent (a
modulo-16 direct decode, as opposed to passphrase use) is now also closed.
This does not reopen or add weight to `YOUWON` itself -- Phase 75's status
stands: plausible engineered community find, downstream operation
unresolved. Don't re-run this specific hex/key-decode reading without a
new, differently-motivated mapping.
