---
type: hypothesis
status: live
date: 2026-08-15
topics:
  - brainstorm
  - media-citations
  - provenance
  - phase1
  - phase2
  - phase3
  - phase3.2
---

# GSMG Media and Citation Inventory

> [!info] Scope
> A reference compilation, not a new cryptanalytic lead: every book, movie, TV
> series, song, article, quote, or named work already connected to the
> puzzle's documented solve chain, plus a few newly-traced sources (chess
> puzzle origin, Heisenberg text origin, Mr. Robot references) found while
> answering direct user questions on 2026-08-15. Sourced from `README.md`,
> `doc/GSMG_PUZZLE.md`, `doc/GSMG_FACT_LEDGER.md`,
> `doc/GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md`, `tools/gsmg/FINDINGS.md`, and two
> live web lookups (cited inline). Confidence tiers are preserved from each
> source document's own hedging -- nothing here is upgraded past what the
> underlying doc actually claims.

## Established / verified

Used directly in a solved answer, or explicitly confirmed in this project's
docs.

| Title / reference | Type | Connection | Citation |
|---|---|---|---|
| *The Matrix Reloaded* (2003) -- Merovingian's "Choice is an illusion..." speech | Movie | Phase 2/3 URL slug; solved answer `causality` | `README.md:92-105` |
| *The Matrix Reloaded* -- Architect scene ("23/16/7") | Movie | Indexing selects `BOTH/ULTIMATELY/THE`; verified identical in shooting script and film | `tools/gsmg/FINDINGS.md` Phase 181/183; fact ledger F-CHAIN-003 |
| *The Matrix* (1999) -- "The Matrix has you" | Movie | Beaufort cipher key `THEMATRIXHASYOU`, Phase 3.2.1 | `README.md:289-299` |
| "The Warning" -- **Logic** (artist) | Song | Phase 1 icon rebus (`war`+`ning`, `LO`+`gic`); lyric gives form password `theflowerblossomsthroughwhatseemstobeaconcretesurface` | `README.md:83-90` |
| Alice in Wonderland -- "How long is forever?" exchange | Quote | Builds `giveitjustonesecond`, one of 3 Phase 3.2 answer parts | `README.md:263,266` |
| Jacque Fresco (quote: "The future is fluid...") | Author/quote | Author ID gives `jacquefresco`, another Phase 3.2 answer part | `README.md:262,266` |
| Klingon numerals (*Star Trek*) | TV/franchise | "S is Klingon numbers 2+(5x6)=32" in Phase 2's `X2SH4Y0QB15` reasoning | `README.md:122` |
| *Mr. Robot* -- "Qwerty" (Elliot's pet fish) | TV series | "extend the name of a hackers' swordless fish" -> `QWERTYUIOP`, gives `Q=82` in `X2SH4Y0QB15` | `doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md:53`; `tools/gsmg/FINDINGS.md:16478` |
| *The Times* (UK newspaper), 3 Jan 2009 headline "Chancellor on brink of second bailout for banks" | Newspaper article | Phase 3 part 6, via Bitcoin's genesis-block coinbase text (`main.cpp` line 1616) | `README.md:150-156` |
| Thales / SafeNet Luna HSM product documentation | Technical docs | Phase 2/3 "2name/3Moon/4How so mate" -> password parts 2-4 (`Safenet`, `Luna`, `HSM`) | `README.md:123` |
| Norton's theorem (Edward Lawry Norton) | Engineering concept | Opens the Phase 3 part-5 riddle | `README.md:127-128`. Note: like Heisenberg below, this is a named *concept*, not a citable paper -- Norton's 1926 result was an unpublished internal Bell Labs memo, never public. |
| Intel i5 processor model `BV80605001911AP` | Product spec | Phase 2 `X2SH4Y0QB15` derivation (`B=-16`) | `README.md:116,122` |
| US presidential history (4 presidents named John; 2 Johnsons; JFK; Executive Order 11110) | Historical record | Phase 3 part 5 (`11110`) | `README.md:130-148`, with Wikipedia links in-line |
| Chess puzzle "White to play and NOT mate" | Internet chess puzzle (not a famous tournament game) | Phase 3 part 7 | See "Newly traced this session" below |

## Noted, real, but not actionable

| Title | Type | Status |
|---|---|---|
| *Cosmic Duality: Mysteries of the Unknown* (Time-Life, 1991, ISBN 0809465175) | Book | Names the final stage; creator twice acknowledged a community find as significant. Both a photographed physical copy and a full OCR were reviewed end-to-end -- no hidden content or riddle sentence found. |
| Neo's passport prop (expiry 9/11/2001) | Movie prop detail | Real, well-documented Easter egg; most-discussed unresolved community hint (298 mentions) -- tested directly as AES passphrases, 0 hits. |
| "Never Gonna Give You Up" -- Rick Astley | Song | Real creator-authored Caesar+base64 message decodes to this; confirmed multi-year Rickroll troll, not a clue. |
| "Follow the white rabbit" | Alice in Wonderland/Matrix imagery | Established framing for Stage 0's route; thematic only, not a decoded string. |
| *Mr. Robot* -- "Whiterose" / "whiteroseredqueen" | TV series character name | Tried as a guessed hidden Wayback URL path; resolves to the generic Vue SPA shell like every other guessed path -- dead end, not real puzzle content. |
| *Simulacra and Simulation* (Jean Baudrillard, 1981) | Book | Named explicitly, verbatim, in the Phase 2 decrypted riddle text ("...also Simulacra and Simulation"). Real book, famous as the hollow prop Neo hides disks in in *The Matrix*. The README's own walkthrough never explains what this reference is *for* in deriving the password -- see open gap below. |

## Speculative / explicitly tested negative

- Lewis Carroll, *The Game of Logic* (1886) -- an untested AI-session breadcrumb sitting in a fork, never actually referenced or run against anything.
- *Looking Forward* (Fresco/Keyes) and Fresco's wider bibliography (*Designing the Future*, *The Venus Project*, etc.) -- creator's own reply was a hedge ("Maybe... Cartman's chatroulette quote fits too"), not confirmation; all swept, 0 hits.
- *Holy Blood, Holy Grail*; Cornel West's *Prophesy Deliverance* -- sourced only from Matrix-fandom-wiki trivia pages, never from actual film dialogue; 0 hits.
- Large negative-result vocabulary sweeps from Matrix-universe lore beyond the films themselves: Gnostic/Manichaean terms (Demiurge, Yaldabaoth, Sophia, Archon), Freemasonry's "Great Architect," Matrix Wiki character/place names -- all tested, all negative.

## Newly traced this session (2026-08-15)

**Chess puzzle (Phase 3 part 7) is not a famous tournament game.** Checked
directly via WebFetch against the live source: the position
`B5KR/1r5B/6R1/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 w - - 0 1` was first
posted by user "BobbyG" on the RedHotPawn chess forum, 31 August 2007,
titled "White to play and NOT mate in one move!" -- a novelty puzzle (find a
checking move that does *not* deliver mate), not a position from any
recorded grandmaster or tournament game. It became a recurring
reposted-many-times puzzle across chess forums afterward, matching the
README's own vague "fairly well known problem in chess." Solution:
`Rc6+`. Source: [Redhotpawn thread](https://www.redhotpawn.com/forum/posers-and-puzzles/white-to-play-and-not-mate.76061).

**Heisenberg's uncertainty principle (Phase 3.2 clue 3) is not attributed to
a specific paper or book in the puzzle text.** The puzzle's own phrase
("The fundamental limit to the precision with which certain pairs of
physical properties are know[n]") closely matches Wikipedia's current lead
sentence for "Uncertainty principle" ("there is a limit to the precision
with which certain pairs of physical properties, such as position and
momentum, can be simultaneously known") -- not Heisenberg's actual 1927
paper (in German, framed mathematically, reads nothing like this). The
puzzle cites the *concept*, phrased like a generic encyclopedia definition,
not a traceable specific source. Source: [Uncertainty principle -- Wikipedia](https://en.wikipedia.org/wiki/Uncertainty_principle).

## Open gap -- not solved, flagged honestly

The Phase 3 part-5 riddle text, right after the JFK material, reads:

> "Another had a resemblance to Carrey, James Gates, also Simulacra and
> Simulation. Another ruler was at some point a floating zerg house while
> being under control of the dirty one.. too."

This is **never explained anywhere** in this project's docs, the README's
own walkthrough, or `FINDINGS.md` -- grepped for "Carrey," "James Gates,"
"zerg," and "Simulacra" across every doc and found nothing beyond the bare
Simulacra name-drop noted above. The README simply skips these lines and
jumps straight to the JFK/executive-order answer, implying this may be
flavor text similar to the Phase 1 icon rebus's 4 unused fragments -- but
unlike those, nobody in this project has actually traced or ruled on it.

Untested, unverified guesses only (not to be treated as findings): "Carrey"
possibly Jim Carrey; "James Gates" possibly physicist S. James Gates Jr.
(known for simulation-hypothesis-adjacent work on error-correcting codes in
string theory); "zerg" possibly a *StarCraft* (Blizzard) reference. None of
these have been checked against any candidate/oracle test. If pursued, this
needs a fresh, disciplined read of exactly which US president(s) or ruler(s)
this paragraph is describing before any candidate can be constructed --
not more keyword guessing.

## Additional findings, round 2 (deeper sweep: full texts, hypothesis docs, Telegram)

A follow-up sweep re-read `README.md` and `doc/GSMG_PUZZLE.md` in full, grepped
`tools/gsmg/FINDINGS.md` (~18k lines) and all `doc/Brainstorms/*.md` for
media-adjacent terms, and checked the project's existing Telegram tooling/docs
(`doc/GSMG_TELEGRAM_MEDIA_SHORTLIST.md`,
`doc/GSMG_TELEGRAM_CREATOR_MEDIA_COMPLETENESS_AUDIT.md`,
`doc/telegram_shortlist_fullsize/`, `doc/telegram_vovam_deleted_thread/`). No raw
local copy of the full Telegram chat export exists in this repo -- worked from
what's already extracted/documented. The full README re-read and the second half
of `GSMG_PUZZLE.md` turned up nothing new (that material is almost entirely
cryptanalytic log, not textual/media reference). Everything below is new.

| Title | Type | Connection | Confidence | Citation |
|---|---|---|---|---|
| "Bella Ciao" (Italian folk/protest song) | Song | Phase 3.2.1 plaintext ends `"...CIAO BELLA O"`; community has tied this to the song since 2020 (reversed word order), also to the Architect-word-mirror chain's derived `BYE` | Noted, real, community-sourced association -- **not** creator-confirmed (only 3 creator "ciao" messages, all ordinary sign-offs); `ciaobella`/variants tested as literal passphrases, 0 hits; song-lyric indexing itself never run (open gap) | `doc/GSMG_BYE_CIAO_PROVENANCE_AUDIT.md:23-91`; `doc/GSMG_FACT_LEDGER.md:51` (F-CHAIN-008) |
| "Clubbed to Death" (Rob Dougan) | Song | Claimed as a named audio asset in a Decentraland scene tied to a speculative `X2SH4Y0QB15` four-waypoint route | Speculative/unconfirmed -- retained scene manifests do **not** contain this asset; original script content is unrecoverable (garbage-collected); "a community observation, not independently recovered primary content" | `doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md:114-118`; `tools/gsmg/FINDINGS.md:16504` (Phase 264) |
| "The Yin and Yang of Neo" (Wylfing.net Matrix-analysis essay) | Essay | Tested whether SalPhaseIon's "yinyang" hint traces to this essay's reading of Matrix yin-yang imagery (Oracle's earrings, Architect/Oracle as Father/Mother) | Speculative/tested negative -- 20 candidates, 0 hits | `tools/gsmg/FINDINGS.md:467-482` |
| Plato's *Symposium* | Book, directly quoted | The Cosmic Duality book (p.48-49) quotes Symposium's "man, woman, and the union of the two" passage; tested as riddle-sentence-candidate source | Speculative/tested negative -- 0 hits (36 + 66 keyword-tests across two framings) | `tools/gsmg/FINDINGS.md:685,724-730` |
| Hegel/Marx/Engels dialectical materialism; Zoroastrian Ohrmazd/Ahriman duality | Philosophical framework (concept, not single work -- same caveat as Norton's theorem) | Another duality-framing angle from the Cosmic Duality book (p.40), tested as riddle vocabulary | Speculative/tested negative -- 0 hits, 42 keyword-tests | `tools/gsmg/FINDINGS.md:732-737` |
| *The Hitchhiker's Guide to the Galaxy* (Douglas Adams) | Book/franchise | Two community members separately invoke "42"/"hitchhiker's guide" while discussing the `X2SH4Y0QB15` "guide" wording | Speculative, untested -- throwaway chat asides only, no evidence anyone mechanically pursued or tested this | `doc/GSMG_TELEGRAM_MEDIA_SHORTLIST.md:55,61` (Telegram messages 51960, 59659) |
| Extended Fresco/Venus Project bibliography and filmography (*The Venus Project: The Redesign of a Culture*, "Zeitgeist: Addendum", "Zeitgeist: Moving Forward", *Bright Tomorrow* screenplay, "Engineering the Impossible" (2002 doc), "sociocyberneering", etc.) | Books/documentaries | Expands the already-listed generic "Fresco's wider bibliography" entry with the individual titles actually swept | Speculative/tested negative -- same bucket as the existing Fresco entry above, all 0 hits | `tools/gsmg/FINDINGS.md:5925-6109` (Phases 88, 90) |
| "Sabaton" (Swedish power-metal band) | Band name | User-proposed phonetic reading of "SalPhaseIon" as "Sa VAT on" | Speculative/tested negative -- 0 hits | `tools/gsmg/FINDINGS.md:7408-7437` (Phase 107 follow-up) |

## Not media, listed only for completeness

- Heisenberg's uncertainty principle, Norton's theorem -- physics/engineering
  concepts, not citable single works (see notes above).
- US Executive Order 11110 -- a real historical government document, not
  media in the book/film/TV/song sense.
