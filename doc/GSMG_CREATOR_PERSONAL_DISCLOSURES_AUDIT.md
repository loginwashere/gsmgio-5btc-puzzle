---
type: audit
phase: 245
date: 2026-08-12
status: closed
result: positive
disposition: provenance-only
evidence_level: creator-primary
topics:
  - creator-provenance
  - telegram
  - netherlands
  - substances
related_phases:
  - 115
  - 116
script: tools/gsmg/creator_personal_disclosures_audit.py
aliases:
  - Phase 245
---

# GSMG Creator Personal-Disclosures Audit

Two off-puzzle facts about the creator account (`Jrk Bgrt` / `@SoWut`,
stable ID `user9815232` — the same identity in both the solver-group and
support-group Telegram exports; see
[GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX](GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md)):
Netherlands residency/nationality, and casual references to recreational and
psychedelic substance use. Neither is puzzle mechanics — both are recorded
as background/provenance, not operative steps.

Reproduce with:

```bash
python3 tools/gsmg/creator_personal_disclosures_audit.py --self-test
python3 tools/gsmg/creator_personal_disclosures_audit.py   # full report
```

## Method

A bounded, frozen message-ID index (not a live regex sweep alone) checked
against the raw `result.json` export at run time: each entry names an exact
message ID, which export it lives in, and a required text fragment. The
script asserts the message exists, is authored by the stable creator ID, and
contains the fragment verbatim — a summary can't silently drift from source.
Weak/ambiguous hits found by the initial keyword sweep were deliberately
excluded from the frozen index rather than folded in as supporting evidence
(see "Deliberately excluded" below).

## Netherlands residency/nationality

20 creator-authored messages, 2018–2022 (19 in the support-group export, 1
in the solver-group export), directly or near-directly self-identifying as
Netherlands-based:

- **"I'm in the Netherlands even."** (msg `41557`, 2020-04-05)
- "Was in Slovenia a few weeks ago... Currently back in the NL." (msg
  `59061`, 2022-09-17)
- "It's considered as daytrading in the netherlands for as far as my legal
  knowledge reaches." (msg `29295`, 2019-04-23)
- "The dutch law doesn't even a legal framework for us to register as how
  we're operating" (msg `25644`, 2019-03-29)
- Repeated offers to converse in Dutch by PM (msgs `1076`, `1708`, `5515`,
  `11423`, `42934`, `44210`)
- An unprompted Dutch-language grammar note: *"Something is 'iets' in Dutch.
  Iets is het tegenovergestelde van niets..."* (msg `41268`, 2020-03-25)
- Locally-specific detail: Albert Heijn/Jumbo supermarkets (msg `42511`), an
  `abnamro.nl` (Dutch bank) link (msg `16082`), "utc not cet" (msg `22482`)
- "Not everybody is Dutch but most of us are indeed." (msg `52684`,
  2021-03-02) — see caveat below
- `geestveruimend` ("mind-expanding," Dutch slang for psychedelics), used
  fluently and unprompted (msg `66976`, 2026-07-17)

Supporting, non-indexed signal: the Dutch-English "ofcourse" (one word)
spelling tell appears in **28** creator-authored support-group messages and
**2** solver-group messages — frequent enough to be a real pattern, but not
indexed message-by-message since it's individually weak.

**Caveat:** msg `52684` ("not everybody is Dutch but most of us are
indeed") uses "we"/"us" framing, consistent with a small Dutch-based team
rather than proof the individual puzzle designer is personally Dutch. What
is established without qualification is that the Telegram identity behind
`@SoWut`/`Jrk Bgrt` — the same identity that authored the puzzle-solver-group
messages — is Netherlands-based, in its own first-person words, repeatedly,
across 2018–2022.

**Deliberately excluded:** msg `32695` ("Pimeyes leads me to a festival
thingy in the Netherlands. Is this a puzzle?") is commentary on a
reverse-image-search result, not self-disclosure. Msg `49176` (Dutch carrot
history trivia) is a shared fact, not a personal claim. Neither is required
by the self-test.

## Substance references

7 creator-authored messages, solver-group export only (2 keyword hits in the
support-group export were false positives — "took a hit" about BTC price,
"high on the to-do list" — and are excluded):

- 2021-03-27 (`6846`), 2024-03-26 (`23152`), and 2026-07-13 (`66606`) are
  isolated one-off jokes in unrelated threads.
- 2026-07-17 01:16–02:47 is one extended late-night session where the
  creator discusses regular drug use candidly in response to another
  member's joke: "ketamine is immune to me by now" (`66940`); "I think I do
  have the answer to an nearly optimal drug setup" (`66944`); "What about
  70mq lsd, 100 mg mdma and bit of ket on the end?" (`66969`); "And in Dutch
  its called 'geestveruimend'. Implying those who dont take drugs are...
  simpleminded..." (`66976`).

None of the 7 are framed as clues, hints, or puzzle-design commentary — they
read as ordinary banter that happens to include drug references. One
adjacent, non-indexed line from the same session is worth naming without
overweighting it: msg `66938` ("I've been doing this life enjoying project
for a while. Quite ego-centric. But in a matrix cypher kinda way I like
it.") sits inside the same conversation and is thematically adjacent to the
already-central Architect/Matrix motif, but it is self-description of
enjoying the project, not clue language — treat any connection as
recognition-only at best, same caution as `F-CHAIN-009`'s community-echo
distinction.

## Verdict

Both facts are real, creator-primary, and reproducible, but neither is
puzzle mechanics. Filed as `disposition: provenance-only` — background
context for interpreting the creator's chat persona and possible
wordlist/geographic angles in future work, not a chain step. No candidate
wordlist, transform, or oracle run is authorized by this audit alone.

## Reopen condition

A creator statement directly tying either fact to puzzle content (a
Dutch-language clue, a substance-referenced hint) would reopen this into an
operative question. None currently exists.
