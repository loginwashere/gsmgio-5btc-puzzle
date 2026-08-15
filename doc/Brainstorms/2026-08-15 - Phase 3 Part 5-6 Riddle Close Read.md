---
type: hypothesis
status: live
date: 2026-08-15
topics:
  - brainstorm
  - phase3
  - norton
  - mcafee
  - overlord
  - riddle
---

# Phase 3 Part 5-6 Riddle Close Read

> [!info] Scope
> A sentence-by-sentence close read of the two prose paragraphs sitting
> between Phase 2 and Phase 3 in the source HTML mirror
> (`doc/html/choiceisanillusion....html:36-49`) -- the riddle text that
> produces password parts 5 and 6 of the solved 7-part Phase 3 concatenation.
> Goal: identify whether any sentence encodes password material that isn't
> already accounted for by the established answers (`11110` for part 5, the
> genesis coinbase hex for part 6). No oracle calls were made in this pass --
> pure textual/historical analysis, cross-checked against three
> AI-generated competing readings the user supplied mid-session and two live
> web-search rounds.

## Bottom line

**No new password material found.** Every sentence in paragraph 1 that
resolves cleanly turns out to be narrative justification for the single
already-used, already-verified value `11110` (JFK's Executive Order
11110) -- not a second extractable fragment. Paragraph 2 is even more
linear: every sentence funnels toward the single already-used part-6 value
(the genesis coinbase scriptSig hex, `main.cpp` line 1616). Unlike
X2SH4Y0QB15's Q/B/H/S sub-clues, which each carry an explicit "compute
this value" instruction, neither paragraph has a comparable extraction
step attached to its one unresolved line -- which is itself a signal that
line may be flavor/misdirection rather than a hidden payload. See
"Open item" below for the one thread still worth testing.

## Paragraph 1, sentence by sentence

Source text (`doc/html/choiceisanillusion....html:36-44`):

> There's a guy who theorised the idea that 'Any linear electrical network
> with voltage and current sources and only resistances can be replaced at
> terminals A-B by an equivalent current source Ino in parallel connection
> with an equivalent resistance Rno'. He might have been insecure. His
> competition might have been that as well. However, after enough belikins
> this competition tried to become a ruler of a piece of land that's
> technically the poorest of the entire planet. 4 rulers have shared the
> first name of the competition. 2 had the firstname in the surname. One of
> the rulers had a number, and dirty too. Another had a resemblance to
> Carrey, James Gates, also Simulacra and Simulation. Another ruler was at
> some point a floating zerg house while being under control of the dirty
> one.. too. The one after died too soon. Moral: never execute an order
> that revokes the highest power or you might suddenly get killed. The
> 5binary code is a part of the piece of this puzzle.

| Clue | Reading | Confidence |
|---|---|---|
| Norton's theorem statement | Edward Lawry Norton, Bell Labs (unpublished 1926 memo) | Established (README) |
| "He might have been insecure" | Pun pivot: Norton -> Norton Antivirus ("insecure" security software) | New this session, unverified, but independently reproduced by 2 of 3 pasted AI analyses |
| "His competition might have been that as well" | Norton Antivirus's market rival, McAfee | Same status |
| "after enough belikins... ruler of a piece of land... poorest of the entire planet" | Belikin = Belize's national beer; John McAfee lived in Belize, ran an armed compound, fled a murder investigation, later ran for US President (Libertarian Party, 2016 & 2020) | New this session, unverified. **Open fork**: does "piece of land" = Belize (fits McAfee's literal on-the-ground behavior) or the USA (fits the README's own pre-existing gloss, "Probably the USA due to foreign debt")? Not resolved -- both can't be the intended referent. |
| "4 rulers... shared the first name of the competition" / "2 had the firstname in the surname" | Set = {John Adams, John Quincy Adams, John Tyler, JFK} + {Andrew Johnson, LBJ}. "First name = John" only makes sense if "the competition" is a person named John (John McAfee fits; no other candidate found). | Established set membership (README); the *why-John* derivation is new/unverified |
| "One of the rulers had a number, and dirty too" | JFK, via Executive Order 11110. Confirmed independently: EO 11110 explicitly amends EO 10289 (Truman, 1951) -- verified via live source check, [Executive Order 11110 -- The American Presidency Project](https://www.presidency.ucsb.edu/documents/executive-order-11110-amendment-executive-order-no-10289-amended-relating-the-performance). Whether "dirty" is a "Dirty Harry"/Harry Truman pun on top of that real EO link is unverified wordplay, not confirmed. | Established (number/EO), speculative (dirty/wordplay) |
| "Another had a resemblance to Carrey, James Gates, also Simulacra and Simulation" | **Unresolved.** See "Open item" below. | Open |
| "Another ruler was... a floating zerg house while being under control of the dirty one" | Overlord = StarCraft's flying Zerg transport unit ("floating... house"); also literally "one who rules over other rulers." Best fit: LBJ, who served under JFK as VP ("under control of the dirty one") before succeeding him. Independently reproduced by 2 of 3 pasted AI analyses. | Plausible, not confirmed |
| "The one after died too soon" | Revised mid-session: this is JFK's *own* death, flowing directly into the next line ("Moral: never execute an order... or you might suddenly get killed"), not a separate ruler reached via a Harrison-died-in-31-days -> Tyler detour (an earlier, weaker hypothesis of mine that required outside trivia the text never actually cues). Independently reproduced by 2 of 3 pasted AI analyses. | Fairly confident |
| "5binary code is a part of the piece of this puzzle" | `11110` itself is the 5-character binary-like string that is part 5 of the password, used literally. **A competing claim that this decodes via Baudot/ITA2 code into a letter (e.g. "V") which is the "real" password material is disproven** -- the project's own already-*working* Phase 3 solve uses the literal string `11110` directly in the verified SHA-256 concatenation (`README.md:192`), not a Baudot-decoded letter. | Established (contradicts a specific wrong claim tested this session) |

## Paragraph 2, sentence by sentence

Source text (`doc/html/choiceisanillusion....html:45-49`):

> Years later the idea of this _green_ came _back_. Looking at the current
> state of nature not quickly enough. Afraid for random magic pieces of
> metal, that moved in directions that science couldn't and still can't
> explain, coming from places where inspiring papers used to be deposited,
> a chancellor awaiting banks to be bailed out decided to write an
> anarchist digital answer to this worlds' misery. Its' raw data after 4 on
> row 1616 to be one of the last pieces of this part required in order to
> continue this riddle.

| Clue | Reading | Confidence |
|---|---|---|
| "this _green_ came _back_" | The separately-italicized "green" and "back" concatenate to **greenback** (US paper currency slang) -- bridges paragraph 1's currency/Fed-power theme into paragraph 2's Bitcoin material. Not documented anywhere in this project before this session (checked, zero prior hits). | New this session, plausible, low-risk reading (pure connective wordplay, no candidate-construction implications) |
| "current state of nature not quickly enough" | Scene-setting (Hobbesian "state of nature," i.e. pre-institutional/regulatory condition); read as narration about slow regulatory response ahead of the 2008 crisis, not a separate extractable clue | Low confidence, likely pure flavor |
| "magic pieces of metal... science couldn't... explain... inspiring papers... deposited" | Two competing unresolved readings: (a) gold-standard imagery (irrational market behavior, old bank-vault reserves); (b) cypherpunk imagery (coins/Bitcoin, foundational cryptography-mailing-list papers like Hashcash/b-money). Neither confirmed; likely atmospheric scene-setting rather than a discrete answer, since paragraph 2 lacks the mathematical-extraction structure paragraph 1's Q/B/H/S-style clues have elsewhere in this puzzle. | Open, low-priority |
| "raw data after 4 on row 1616" | Genesis block coinbase scriptSig, `main.cpp` line 1616 -- part 6 of the password, confirmed and already in the working formula | Established (README) |

## Ruled-out competing theories (logged so they aren't re-tested)

Three AI-generated analyses were pasted into this session and cross-checked;
their genuinely new/correct contributions are folded into the tables above.
What was checked and specifically **rejected**:

- **Hans Ferdinand Mayer as "the competition"** -- real historical figure
  (independently derived an equivalent of Norton/Thevenin's theorem in
  Germany, 1926), but his first name is Hans, not John, so this reading
  cannot actually produce the required "first name John" without silently
  substituting in McAfee anyway. Doesn't explain "belikins" at all.
- **Jekyll Island / Rockefeller-Morgan-founded-the-Fed as "the competition
  = John"** -- real history (1910 secret meeting that produced the Federal
  Reserve Act), but neither Rockefeller nor Morgan personally attended that
  meeting (actual attendees: Aldrich, Vanderlip, Davison, Strong, Warburg,
  Piatt Andrew -- none named John), and the theory never engages with
  "belikins" or the literal-ruler-of-a-piece-of-land phrasing at all. Rejected
  for failing to explain the puzzle's actual specific wording, only its
  general theme.
- **"Dirty" = "Dirty Harry" (Clint Eastwood film) referencing Harry Truman
  as JFK's immediate predecessor** -- factually wrong on its face (Truman
  was two presidents before JFK, not his direct predecessor; Eisenhower was
  in between). The *separate*, real fact underneath it (EO 11110 amends
  Truman's EO 10289) survives and is logged in the table above; the "Dirty
  Harry" pun bridge itself remains unconfirmed wordplay.
- **"11110" decodes via 5-bit Baudot/ITA2 code to a letter (e.g. "V"),
  which is the true password material** -- directly contradicted by this
  project's own working, already-verified Phase 3 solve, which uses the
  literal digit string `11110`. Not a hypothesis to revisit; simply wrong.
- **"John Quincy Adams or John Adams" for the Carrey/James Gates line** --
  asserted with no supporting derivation in the source analysis (just
  restates what Carrey/Gates/Baudrillard mean thematically, then guesses a
  name). Not treated as evidence; see open item below.

## Open item -- Carrey/James Gates/Simulacra line

Still fully unresolved after five independent web-search angles this
session (direct Carrey-president resemblance, James-Gates-to-Andrew-Johnson,
GSMG-specific community discussion, nickname/lookalike search, portrait
memes) plus three cross-checked AI-generated readings, none of which
produced or defended a specific, evidenced identification. The only
adjacent real fact surfaced: Andrew Johnson is a well-known visual lookalike
for actor **Tommy Lee Jones**, not Jim Carrey -- a near-miss, not a hit.

No extraction mechanism (no "compute X" instruction, unlike X2SH4Y0QB15's
sub-clues) is attached to this sentence, so even a correct identification
may not yield password material. Two live possibilities, not distinguished:
pure misdirection (same category as Phase 1's four unused icon fragments),
or a forward-pointing hint aimed at one of the still-locked blobs rather
than at Phase 3 itself.

## Next step (not yet executed)

Bounded, disciplined oracle test matching this project's established
residual-vocabulary pattern (e.g. FINDINGS.md Phase 265): run the raw
sentence text (and its no-whitespace/lowercase mechanical variants, plus
`sha256(...)` of each) as literal passphrases against all four locked
blobs (SALPH, COSMIC, P32_TRAILING, URLBLOB). Zero interpretation required,
cheap, and closes out whether this specific disclosed-but-unused fragment
has ever actually been tried -- it hasn't, in any form, per repo-wide grep.
Not yet built or run; pending approval.
