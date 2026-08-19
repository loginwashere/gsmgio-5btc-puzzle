---
type: hypothesis
status: live
date: 2026-08-17
topics:
  - brainstorm
  - creator-provenance
  - telegram
  - synthesis
---

# Creator Profile Synthesis

> [!info] Scope
> Consolidates everything this project has established about the creator
> ("Jrk Bgrt" / `@SoWut`, stable ID `user9815232`) across
> `GSMG_CREATOR_PERSONAL_DISCLOSURES_AUDIT.md`,
> `GSMG_CREATOR_FEASIBILITY_ENVELOPE_AUDIT.md`,
> `GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md`, this session's "Close
> Friends Hint" close read, and new primary-source material pulled directly
> from the pinned Telegram exports this session. Purpose: build a single
> reference for *puzzle-design priors* -- what this profile implies about
> how the puzzle is likely constructed -- not a biography. Explicitly does
> **not** attempt to identify the real person, their partner, or any
> specific institution/employer/location beyond what the creator has
> publicly disclosed himself. See "Scope boundary" at the end.

## Verified facts

| Fact | Evidence | Source |
|---|---|---|
| Netherlands-based, in his own words, repeatedly 2018-2022 | 20 creator messages self-identifying as NL-based | `GSMG_CREATOR_PERSONAL_DISCLOSURES_AUDIT.md` |
| Fluent Dutch speaker; team is majority Dutch ("most devs are Dutch, indeed") | Direct quote, msg `15526` | this session, raw export |
| Casual/recreational substance references (ketamine, MDMA, LSD, alcohol); comfortable discussing this openly in the solver chat | 7 messages, 2021-2026 | `GSMG_CREATOR_PERSONAL_DISCLOSURES_AUDIT.md` |
| Puzzle created 2019, in "two sloppy days," explicitly inspired by other crypto puzzles (names Cicada 3301 by category) | msg `67741` (2026 retrospective), msg `7152` | `doc/GSMG_PUZZLE.md:11`, `GSMG_CREATOR_FEASIBILITY_ENVELOPE_AUDIT.md` |
| GSMG.io itself (the trading bot) originated in **2017 in Sydney**, built in 9 days during a personal trip, "zero high-end programming skills," using Siemens PLC code, HTML, Quake 3 scripting, and Pascal -- "no functions, no classes" | Full retrospective, msg `67741` | this session, raw export (see below) |
| Original bot name: **MR. ROIbot**; first live order hit Poloniex ~10 June, ~08:30 | msg `67741` | this session, raw export |
| Founding team beyond JRK: **d0d** (co-founder, present from day one), **Darky** (infrastructure), **Greengras** (first server space), **Bloctite** (rewrote the entire codebase in Python/Cython -- the team's actual trained software engineer) | msg `67741` | this session, raw export |
| Motivation: JRK and d0d were burned by a scam bot run by "fuzzyhobbit," decided to build something honest instead | msg `67741` | this session, raw export |
| GSMG = "**G**lobally **S**upporting **M**y **G**eneration," reused from an old friend's group name | msg `67741` | `tools/gsmg/FINDINGS.md` Phase 155 |
| "Half and better half" / "the better half is hungry" are the creator's own ordinary idiom for his real romantic partner, used twice independently (2025, 2026) | msgs, 2 separate occasions | `tools/gsmg/FINDINGS.md` Phase 133, Phase 155 |
| Dutch drinking-culture proverb, used unprompted: *"'s avonds een vent, 's ochtends een vent"* ("a man at night, a man in the morning" -- can drink hard and still function), which he jokes he fails ("...'s ochtends absent") | msg `16978`, 2019-01-28 | this session, raw export |
| Genuine, explicitly-flagged hint (2026-07-13): close friends have the best social/physical access to him but "don't have the skills some of you do" | msgs `66568`/`66571`/`66573`/`66574` | [[2026-08-17 - Close Friends Hint Full Context Close Read\|Close Friends Hint — Full Context Close Read]] |
| No creator endorsement of brute force; explicitly anti-bruteforce design intent; "you have all the info," no further URL needed; one more "microstep" would likely finish it | msgs `9607`/`9639`/`16624`/`28703`/`32579` | `GSMG_CREATOR_FEASIBILITY_ENVELOPE_AUDIT.md` |

## Full text: the 2017 Sydney origin story (msg `67741`, 2026-04-13)

Quoted in full since it's the single richest primary-source block found this
session and several rows above cite only fragments of it:

> "It all started in 2017. JRK was visiting Sydney with the better half.
> Instead of playing tourist like a normal person, he locked himself in a
> living room for nine straight days. Zero high-end programming skills.
> Just Siemens PLC code, some HTML, Quake 3 scripting and a bit of Pascal.
> He built the entire bot from scratch as one single terrifying,
> never-ending script. No functions. No classes. Just pure chaos and hope.
> On June 10th at around 8:30 in the morning, the first order actually hit
> Poloniex servers... The very first name for this script was MR. ROIbot.
> ... A little later, JRK got inspired by other crypto puzzles and spent two
> sloppy days throwing one together. Full of grammatical mistakes and zero
> polish."

## Interpretive synthesis: technical-background category and puzzle-design priors

This is explicitly interpretation, not a new fact row -- included because it
sharpens existing, already-adopted priors rather than replacing them.

**Category of background: applied/vocational technical training, not
computer science.** Siemens PLC (ladder logic/STEP 7) is taught in
electrical engineering, industrial automation, and mechatronics programs,
not CS curricula. Pascal as a baseline fits the same applied/technical
track common in Dutch MBO/HBO education through the 1990s-2000s. Quake 3
scripting and HTML are self-taught hobbyist layers on top. "Zero high-end
programming skills... no functions, no classes" is his own literal
description of unstructured, non-OOP procedural code -- consistent with a
PLC/ladder-logic mental model (sequential rungs, not modular abstraction)
carried into general scripting. The team's actual trained software
engineer is a different named person (Bloctite), who rewrote the codebase
from scratch.

**What this implies, and why it's corroborating rather than new:**

1. **Reinforces the existing "recognition gap, not novel cipher" prior**
   (first established independently in `tools/gsmg/FINDINGS.md` Phase 154
   from Telegram meta-commentary analysis). Someone without formal
   CS/cryptography training, working in "two sloppy days," reaches for
   well-known off-the-shelf primitives -- exactly what's observed at every
   solved stage (Vigenère/Beaufort, VIC/checkerboard, AES via the OpenSSL
   CLI). Lowers the prior that DBBI/FAED/P32TRAILING hide a custom
   cryptographic construction; raises the prior that the blocker is an
   unspotted *reference*, matching his own repeated "one more microstep"
   framing.
2. **Reinforces "assembled found material, not authored content."** A
   grab-whatever-tool-you-already-know style (PLC + Pascal + Quake 3
   scripting, mixed with no apparent concern for consistency) matches what's
   independently confirmed about the puzzle's own construction: a reused
   internet chess puzzle, a misattributed quote, a real newspaper headline,
   a vendor spec sheet -- found material, not invented content.
3. **Mild support for linear, non-modular structure.** "No functions, no
   classes" as a description of his coding style is consistent with the
   puzzle's own observed phase-to-phase linear password-chaining
   architecture, rather than a deliberately branching/modular design.

None of this is promoted to a Fact Ledger row -- it's a corroborating prior
from an independent fact set (skills disclosure), not new cryptanalytic
evidence, and it doesn't change any open gap's status.

## Idiolect evidence: dual-register vocabulary and spelling patterns in the Phase 3.2 monologue (2026-08-18)

Cross-reference: `2026-08-17 - Architect Monologue vs Film Substitution Table.md`
catalogs the decrypted Phase 3.2 Architect monologue (`README.md:302-320`) as
a close paraphrase of *The Matrix Reloaded*'s Architect scene, with several
fully puzzle-original insertions (that doc's rows 6, 7, 8, 9, 13a-15) that
have no film counterpart at all. Those insertions are pure creator voice --
not constrained by matching a film line -- and are the right place to look
for idiolect evidence. This folds in that doc's ideas 6 and 7 plus one new
synthesis point this pass adds.

**"Prices" for "prizes" (row 9) is plausibly a Dutch false-friend, not just a
stray typo.** The substitution table hedges this as "an eye-skip typo, or...
exactly the word a trader would reach for." A third reading fits the
already-verified fact above that the creator is a fluent Dutch speaker on a
majority-Dutch team: Dutch uses a single word, *prijs*, for both English
"price" and "prize" -- there is no lexical distinction in the source
language, and confusing the two in English is a known, specific
Dutch-English (and German *Preis*) interference pattern, distinct from a
generic spelling slip. This doesn't override the trader-register reading
(idea 6 in that doc) -- both can be true of the same word choice at once.

**"Hundred fourty" (row 7) is consistent with a literal Dutch numeral
calque.** Standard English requires an article and a conjunction here ("**a**
hundred **and** forty"); the puzzle text has neither. Dutch numerals compound
directly with no equivalent word -- "honderdveertig" ("hundred-forty") is
written/spoken as one unit, with no article and no "and." "Worth hundred
fourty of the investment" reads as what a Dutch speaker produces translating
that construction literally. This is independent support for the same
Dutch-L1 idiolect that the "fourty" misspelling alone only weakly implied.

**Rare/formal vocabulary and basic spelling errors coexist in the same short
passage -- a signature in combination, not just two separate observations.**
The substitution table separately notes "sedulously" (row 3, replacing the
film's "assiduously") and "entireness" (row 13b, replacing the film's plain
"entire") as a "rarer-vocabulary habit," while rows 7/9 carry "fourty,"
"throphies," "waisting." Reaching for uncommon words (plausibly via a
thesaurus or translation lookup) while still misspelling common ones
("forty," "trophies," "wasting") is a specific combination -- consistent
with, and reinforcing, this doc's existing "applied/vocational technical
training, not native English, not a professional writer" prior (see
Interpretive synthesis above), rather than either a native English speaker's
ordinary typos or a non-fluent speaker's uniformly simple vocabulary.

**Weaker/secondary notes, logged but not leaned on:**
- Apostrophes are dropped on "youve" (rows 6, 8) and "youre" (row 14) but
  kept on "you'll" (row 8), "I'm" (row 8), and "that's" (row 7) -- an
  inconsistent pattern, more likely fast/careless typing than a
  language-specific tell; flagged for completeness, not proposed as idiolect
  evidence.
- A dedicated re-read of rows 6-9 and 13a-15 turned up no further
  dual-register (finance/Matrix) vocabulary beyond what the substitution
  table already flagged (row 1-2's "equation"/"mathematical precision," row
  7's "investment," row 9's "prices"/"throphies"/"worthless," row 13a's
  "system crash"). "Earned it" (row 6) and "help us build it" (row 7) are
  marginal candidates -- both read naturally in either register -- but are
  thin enough (a single ambiguous word/phrase, no clear forced second
  meaning) not to add as named evidence.

None of the above is proposed as password/cipher material -- per this doc's
existing scope boundary, it stays interpretive: priors about how the puzzle
is likely constructed and who likely built it, not a new cryptanalytic lead.

## Scope boundary

This document deliberately stops at:

- what the creator has disclosed about himself, in his own public words;
- the *category* of technical background those disclosures imply, and what
  that category implies about puzzle-design style.

It deliberately does **not**:

- name or guess a specific school, employer, or institution;
- attempt to identify the creator's real name, location beyond
  "Netherlands," or his partner's identity;
- treat any of the above as password/cipher material without an
  independent, authenticated selector (per every existing closed thread on
  "half and better half," `SYDNEY`, etc. -- see
  [[2026-08-15 - GSMG Media and Citation Inventory|GSMG Media and Citation Inventory]] and `GSMG_CREATOR_PERSONAL_DISCLOSURES_AUDIT.md`
  for what's already been tested and closed).

## Connections

- [[2026-08-17 - Close Friends Hint Full Context Close Read|Close Friends Hint — Full Context Close Read]]
- [[2026-08-15 - GSMG Media and Citation Inventory|GSMG Media and Citation Inventory]]
- [[2026-08-17 - Architect Monologue vs Film Substitution Table|Architect Monologue vs Film Substitution Table]]
- `GSMG_CREATOR_PERSONAL_DISCLOSURES_AUDIT.md`
- `GSMG_CREATOR_FEASIBILITY_ENVELOPE_AUDIT.md`
- `GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md`
