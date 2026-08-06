# GSMG Creator Clue and Confirmation Index

## Purpose

This is the single lookup document for puzzle-relevant Telegram messages
authored by creator **Jrk Bgrt**. It combines:

- explicit and accidental hints;
- confirmations or refutations of concrete community claims;
- praise/progress statements such as “very specific,” “getting close,” and
  `Bingo`;
- caveats that prevent jokes, hedges, or silence from becoming false clues;
- prize, validity, and solvability statements relevant to the final phase.

The primary source for the solver-group IDs used throughout this document is
the complete Telegram Desktop JSON export:

`/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26/result.json`

Creator identity is fixed by Telegram user ID `user9815232`, not by mutable
display names. `tools/gsmg/telegram_creator_clue_index_audit.py` validates all
indexed message IDs, text fragments, and preserved direct-reply edges.

A second complete export now supplies the original public support-group
provenance:

`/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)/result.json`

It is independently validated by
`tools/gsmg/support_group_export_delta_audit.py`. Message IDs in that group
belong to a different Telegram namespace and are therefore kept in a
separate table below rather than mixed with solver-group IDs.

The export contains 482 creator records: 466 have text, 148 have reply
metadata, and 145 of those replies contain text. This document indexes 80
puzzle-relevant records under the bounded criteria above; ordinary chat,
greetings, moderation, finance discussion, and generic encouragement are
excluded.

## Evidence Labels

- **Hint:** creator supplies or accidentally reveals an operation, value, or
  target state.
- **Confirmation:** creator affirms or refutes a concrete claim.
- **Praise/progress:** creator signals that an artifact or solving state is
  useful, without necessarily validating the proposed method.
- **Recognition:** describes what a correct intermediate state should feel or
  look like.
- **Caveat:** prevents a weak response, joke, or hedge from being promoted.
- **Meta/prize:** constrains validity, solvability, timing, or prize status but
  supplies no direct transform.

## Original Public Support-Group Evidence

The full `GSMG - Community & support group` export contains `52,851`
messages from 2018-04-17 through 2026-07-28 and `5,419` records authored by
creator ID `user9815232`. The earlier 22,400-message export is an exact,
message-for-message prefix of this one.

| Support-group IDs | Evidence | Meaning and limit |
|---|---|---|
| `25986`–`25988` | Creator posts the 2019-04-01 “Here is the GSMG Puzzle!” caption and two binary payloads. | Primary originals of the pre-rabbit April-Fools puzzle. Their text is byte-identical to the later creator-attributed forwards in solver messages `21403`–`21405`. |
| `26065`, `26083` | Calls the Caesar query the “First external hint”; later says decoded `esrever` should be applied to the second binary block. | Confirms the exact Caesar/reversal chain reconstructed in Phase 136. This is the first puzzle, not the later rabbit puzzle. |
| `28507` | Posts the original rabbit-puzzle JPEG with “Well, good luck I guess.” | Primary Stage-0 attachment, now archived as `doc/img/gsmg_stage0_original_telegram.jpg`. It is distinct in bytes and resolution from the later PNG. |
| `28512`, `28534`, `28571` | Says the on-chain address shows whether it is solved, that one private key is hidden, and that the puzzle ends in a private key. | Primary output/progress framing. Does not identify the derivation. |
| `28522` | Direct reply to “when hint?”: “Follow the white rabbit.” | Earliest recovered primary instance of the Stage-0 route clue. |
| `28526`, `28527` | Says generating the GSMG vanity address took seconds: “Only 4 chars. The 1’s take more time somehow.” | Supports the visible `GSMG`/`1` vanity construction. It does not make another derived GSMG-looking address a valid solution; funding or exact-address evidence is still required. |
| `28703` | Says the changing web token was an anti-bruteforce measure and instructs solvers to find the correct next hint. | Explains historical form behavior; does not imply a cryptographic transform. |
| `28794`, `28812` | Says scanning GSMG generally “Won’t work”; later gives `gsmg.io/puzzle` followed by “All the info you need is there.” | Confirms the rabbit puzzle was intended to be self-contained and argues against broad site archaeology without a selected artifact. |
| `28866` | In the initial rabbit thread: “Well, I can only show you the door.” | Early Matrix/door vocabulary and route framing. It is thematic support, not a newly specified door operation. |
| `28961` | Says there may be a tiny rabbit-phase hint in GSMG’s Slack music channel. | Most naturally points to the already-solved *The Warning* music/lyrics transition. The exact Slack post is not retained, so do not infer additional content. |
| `29066` | Supplies `5ac407...6f75` when asked for the first solved answer’s hash. | Exact creator-provided Phase-1 verification hash, already reproduced from the solved lyric password. |
| `29123` | “Success detection of unlocking phase 3 is the same as you’d crack any other hash.” | Confirms a hash-equality gate at that solved boundary, not a hash oracle for the current endgame. |
| `29132` | Says that after Stage 2, another supplied hash “won’t help you anyhow.” | Prevents treating every historical phase as having a creator-provided verification hash. |
| `31990`, `32043`, `32044` | Original Phase-III typo correction, progress praise, and promise of a final 2020 hint if needed. | Primary provenance for records already known through the solver group; no new endgame operation. |
| `42540`, `67741`, `67742` | Says he contributed to but did not entirely make the puzzle; the later retrospective says JRK assembled it in “two sloppy days,” with grammatical mistakes and little polish, and confirms it remains unsolved. | Strong methodological boundary: prioritize short, clue-selected mechanics and tolerate implementation mistakes; do not assume every irregularity encodes a deep secondary layer. |

Community message `28927` explicitly notices that the creator-posted image is
JPEG while the webpage image is PNG. Message `28930` replies that there is no
steganography, but it is not creator-authored and received no creator
confirmation. Preserve the format distinction without promoting that
community assertion.

One unresolved support-group record is deliberately not promoted: message
`28548` says “Depends how you look at it” in the first rabbit-thread window,
but its reply parent `28547` was deleted before export. With the proposition
gone, the reply cannot validate any specific puzzle interpretation.

## Historical Corrections

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `866`, `867` | Creator admits a Phase III error and gives `giveit = givetit`. | Genuine correction for an earlier solved phase, not a Cosmic Duality clue. |
| `879` | Praises the team’s unexpectedly rapid post-correction progress. | Progress signal only. |
| `881` | Says a final hint would arrive in 2020 if needed and the key was recoverable without it. | Establishes intended solvability, not an operation. |
| `1806` | Explicitly says rushed typos contain no clues. | Closes typo-mining. |

## First Piece and Extra Door

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `1710` | “Yellow has a number and so does Blue”; return to the first puzzle piece; rabbits’ nest may contain more than one door. | Primary first-piece color/door clue. |
| `3338` | Says one team found something others had not. | Progress signal; no method disclosed. |
| `3391` | Explicitly says a nearby comment is “not a hint.” | Do not mine that joke. |
| `4094`, `4096` | Confirms the January hint was missing from GitHub and points back to message `1710`. | Locks the intended official hint text. |
| `4102`, `4105` | “answer is there”; “First or zero.” | Confirms the other-door answer is in the first/zero puzzle piece; does not define every use of first/zero. |
| `4590` | Asks why nobody found the “extra door.” | Confirms another door is literal progression. |
| `4688`, `4694`, `4696` | Says the hints make the path “pretty obvious,” one club passed, and confirms it is the next stage of the second route. | Strong route/progress confirmation, but no extraction rule. |
| `5966`, `5969` | “You are at the prime part already???” followed by “That might have been a hint.” | Prime use is intended. |
| `6497` | Breaking SalPhaseIon should give the feeling of the phase name. | Recognition cue, not an algorithm. |
| `6509` | In reply to a request for a `matrixsumlist` hint, says an unforeseen hint was already given. | Most naturally points to the immediately preceding prime disclosure; does not specify matrix mechanics. |
| `6884` | Formal hint: another door might be found on `{1},{4},{21}`. | Exact first-piece FEFE locator after reconstruction. |
| `6913` | `R=18 / A=1 / B=2`; “Could also be 21 or 1812 bit.” | Supplies the R-A-B + BIT → RABBIT pointer and bit-grid framing. |
| `7418` | Replies “Good point” to advice to return to the first image and hash its text, while warning that “text” is picky. | Praise is real, but it does not uniquely confirm every part of the community prescription. |
| `7529` | Responds to “is the April 1 hint real?” by asking what usually happens on April 1. | Caveat: the date disguises the clue; this is not a clean yes/no confirmation by itself. |
| `7914` | Replies to a hint request with vertically emphasized “There is Another D O O R.” | Reconfirms the extra-door branch. |
| `8000` | Formal mini-hint: another door remains relevant, primes are required, and some characters must be “zeroed out.” | Strongest creator description of the unresolved operation; plural characters remain important. |
| `8048`, `8516` | Gives and later re-emphasizes Neo’s passport expiry date. | Deliberate value; role/format remain unspecified. |

## Book, Prime, Matrix, and Ordered Chain

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `8311`, `8315` | Replies “That is very specific” to semaj’s attached image, then says its specificity will be clear after solving. | Direct creator validation of the exact recovered *Cosmic Duality* book-cover image, not missing interior pages. |
| `8328` | Says `@barrystyle` already supplied a very specific hint. | Confirms the same book discovery as an intended lead. |
| `8330` | “At least prime number is very important to get any further.” | Strong prime confirmation. |
| `8352` | Praises a community GitHub and says “You guys are really getting close.” | Genuine progress praise; it does not validate every claim in that repository. |
| `8354` | Theory of everything remains a valid path to the private key. | Broad thematic path, not a bounded transform. |
| `8360` | Says the puzzle is solvable and the remaining BTC is deserved. | Solvability/prize meta only. |
| `8385` | Answers `42` when asked how much math is involved. | Low-priority humorous/meta statement; do not treat as an operation. |
| `8483` | Replies `👆🤷‍♂` to message `8448`, which posts the reversed binary text beginning `yellowblueprimesmatrixsumlist...`. | Weak acknowledgment of the recovered page text; the authenticated page bytes, not the emoji, carry the evidentiary weight. |

## Near-Final Recognition and Progress

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `8795`, `8796` | Says solvers got “really really far” and “the hardest part is done.” | Strong progress signal, but not a method confirmation. |
| `9599` | “Probably the last hint”: once a “ying yang” is hit, the puzzle can be solved the same day. | Yin-yang is a reached state/phase, not automatically a literal password. |
| `9603` | Asked whether “hit” was meant as “hint,” replies “Both?” | Wordplay/recognition cue; not an operation. |
| `9607` | Rejects the need for another URL: “You have all the info.” | Search-boundary guidance against inventing external dependencies. |
| `9615` | “My hat off to you, and you know why.” | Private/contextual praise; unusable as public method confirmation. |
| `9621` | Says another hint would probably be a giveaway and likely is unnecessary. | Solvability/meta only. |
| `9627` | “Something was solved rather... remarkable.” | Progress signal without identifying which public claim is correct. |
| `9639` | Confirms no internet is needed for solving, except ultimately claiming the prize. | Supports a self-contained solution. |
| `12653` | Replies `Correct` to the claim that blockchain messages were not his and are not part of the puzzle. | Closes those messages as creator clues. |
| `20223` | Says the target is a regular Bitcoin private key. | Confirms output format only. |
| `20224` | Replies `🤐` to a request for help with “our first hint is your last command.” | Silence, not confirmation of the requester’s interpretation. |
| `23151` | Asked which old hints remain relevant, replies “Technically yes but Nope.” | Too ambiguous to reopen or close any specific clue. |
| `32579` | Says one more “microstep” would likely lead to a same-day solve. | Prioritizes a local transition over another broad cipher search. |
| `39224`, `39237` | Says reaching ying-yang leaves at most two hours and explicitly calls it “the next phase.” | Strong confirmation that yin-yang is the next reached phase. |

## “In Front of Your Eyes” Exchange

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `60306` | Responds “Maybe” plus a Cartman joke to Denis’s *Looking Forward* suggestion. | Explicit hedge; the book title is not confirmed. |
| `60309` | Responds to a demand for direction by pointing at gnomad. | Sets up the following confirmation. |
| `60312` | Says `Bingo` immediately after gnomad repeats only “it’s in front of your eyes but you’re not seeing it.” | Confirms the phrase-level pointer, not *Looking Forward*. |
| `60314` | Says reaching the next phase means the prize is taken “in no-time.” | Final transition is short; no algorithm disclosed. |
| `60326` | Replies “Nope” to whether binary contact information on `jrk.agency` is related. | Closes that external-site lead. |
| `63957` | When the sites go offline, confirms “The puzzle is still valid!” | Solving does not depend on the removed live sites. |

## July 2026 Creator Return

These messages postdate the older flat transcript and are only present in the
complete JSON export.

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `66568` | Says the actual answer is on a hidden laptop untouched for years. | Establishes retained ground truth, not a cryptographic clue by itself. |
| `66571`, `66573`, `66574` | Says some chat members can find him, close friends have the best chance, then explicitly states: “NOTE: that is a hint.” | Genuine new hint cluster. The safest reading is physical/social proximity to the creator or hidden laptop; no wording licenses converting “close friends” into a cipher key. A community member later asked the exact bounded classification question—whether this applies to a specific public puzzle artifact (`66874`, replying to `66574`). It received only one sarcastic community reply (`66875`), no creator reply, despite 24 later creator messages before the creator's last message `66976`; the export continues through `67267`. Treat the question as explicitly asked and unanswered, not as a prompt to infer an artifact. |
| `66584` | Notes the original URL/puzzle is “gone.” | Historical-status statement. |
| `66586` | Says “Nope” after Denis asks whether a previously posted list contains the new hint. | Closes that particular list, though missing reply metadata makes the adjacent context less strong than a direct JSON reply. |
| `66588`, `66589` | Answers yes that SalPhaseIon is fully solvable and says he verified the puzzle after earlier mistakes. | Strong solvability confirmation; the qubit comment is humorous insurance, not the intended method. |
| `66592` | Says he held a secret he wanted to share with those who could understand it. | Meta/thematic statement; no bounded operation. |
| `66593`, `66595` | Says the 5 BTC was only a small part of the “actual prize,” while confirming the BTC remains available. | Prize framing, not a puzzle operation. |
| `66600` | Says some people already found “it” and understood not to risk it. | Ambiguous safety/meta claim. It does not establish that anyone solved Cosmic Duality or obtained the key. |

## Additional Records From a Full-Export Review (2026-07-26)

A systematic pass over all 395 previously-unindexed creator text messages
(out of 482 total) surfaced eight further records meeting the bounded
criteria. Most candidate messages that looked promising out of context
(`"Only -41,-17 matters"`, `"You have to be in your prime for that"`,
`"it's hidden in a room with a hidden door"`) turned out, once their
surrounding conversation was read, to be about an unrelated interactive
game, a joke about even primes, and continued banter on the already-indexed
`66568` hidden-laptop bit respectively -- excluded for the same reason
ordinary conversation is excluded elsewhere in this document.

| Telegram IDs | Evidence | Meaning and limit |
|---|---|---|
| `1487` | "There may indeed a piece be found outside the main puzzle." | Earliest (2019-09-26) precedent for the extra-piece/extra-door theme, predating `4590`. |
| `2910`, `2918` | In the same thread as message `2899` (the rabbit hole/nest diagram, see `rabbit_hole_nest_audit.py`), replies "Answering that would be too much of a hint" to whether the PK is in the final decoded 3.2 cipher, then "There must at least be something hidden in there." | A hedge immediately followed by an affirmative-leaning statement: something is confirmed hidden in the final decoded cipher text. Does not specify what or where. |
| `4624` | Answers "a private key" (2020-08-09). | Same output-format confirmation as `20223`, four years earlier. |
| `7998` | "Oh well, why not. A mini mini hint. Ready 🐰?" (2021-12-26T22:11:26, 7 minutes before the already-indexed `8000`). | The lead-in to the `{1,4,21}`/"zeroed out" hint, not separate content. |
| `32535` | "If wallet != empty, puzzle not solved. (Most likely)." | States the on-chain solved/unsolved heuristic explicitly. |
| `32671` | "You only need the last number of pi and it might get you somewhere." | Already independently closed as an explicit joke by `tools/gsmg/FINDINGS.md` Phase 40 (participants immediately discuss pi's infinite digits and "searching for nothing"); recorded here only so this document's own coverage is complete. |
| `53342` | A forward-encoded (not reversed) binary posted 2026-01-01T05:20:03, decoding to: "Happy new year! Make the best of everything. Oh, and here's a 'tiny hint' <3." | Self-labeled a hint, but its content is a festive greeting; "everything" echoes the word Denis separately claimed (unverified) to see near the recovered 31-character extraction. No operation follows from this alone. |

## Praise and Confirmation Quick List

These are the creator reactions most likely to be mistakenly quoted as broad
validation. Their scope should remain narrow.

| Message | Reaction | What it actually validates |
|---|---|---|
| `7418` | `Good point` | Returning to the first image is sensible; not every proposed hashing detail. |
| `8311`, `8315` | `very specific` / `scary specific` | The exact book-cover media at parent message `8310`. |
| `8352` | `nicely done` / `really getting close` | General repository/progress quality, not every repository conclusion. |
| `8795`, `8796` | `really really far` / `hardest part is done` | Overall solving position at that date. |
| `9615` | `My hat off to you` | Private/contextual achievement, method unspecified. |
| `9627` | `Something was solved rather... remarkable` | Some progress, artifact unspecified. |
| `60312` | `Bingo` | Only the phrase “in front of your eyes but you’re not seeing it.” |

## Creator-Authored Non-Chat Artifact

**Correction (2026-07-26):** this was previously understated. The reversed
binary itself is a direct creator Telegram post, not merely an external page
artifact with weak chat acknowledgment. Message `8446` (Jrk Bgrt,
2023-02-24T01:20:03, `reply=None`) is the raw bit string, independently
decoded here (reversed, 8-bit ASCII) to confirm it is exactly:

```text
yellowblueprimes
matrixsumlist
lastwordsbeforearchichoice
yinyang
wewontgiveawaythepassword
itsinfrontofyoureyesbutyourenotseeingit
verylaststepisatruegiveaway
promised
```

A community member (message `8448`, anonymized sender, 2023-02-25, one day
later) posted the same plain-text decode with the caption "reversed binary:
...". Message `8483` (creator, `reply=8448`, six weeks later) is a weak
`👆🤷‍♂️` acknowledgment of *that* decode -- but the primary source is `8446`
itself, authored by the creator, fixing the macro dependency order with the
strongest possible provenance (a first-party post, not a third-hand
citation).

## Current High-Confidence Boundary

Taken together, the creator evidence supports:

```text
first/zero rabbit piece
  -> yellow/blue numbers
  -> another door
  -> prime selection
  -> {1,4,21} / R-A-B + BIT
  -> some characters zeroed out
  -> matrix sum/list
  -> last words before Architect choice
  -> yin-yang next phase
  -> short final solve
```

It does **not** currently select:

- sum, XOR, concatenation, BIP38, or another arithmetic use of `[23,16,7]`;
- *Looking Forward* as the meaning of `Bingo`;
- `yang` as a password;
- a specific AES/KDF family;
- a broad new transform family for DBBI/FAED;
- the July “close friends” phrase as a textual cipher key.

## Maintenance Rule

When a new creator message is proposed as evidence:

1. verify `from_id == user9815232`;
2. record the Telegram message ID and exact reply parent;
3. distinguish direct reply metadata from mere adjacency;
4. quote only the smallest necessary text;
5. classify it as hint, confirmation, praise, caveat, or meta;
6. state explicitly what it does **not** validate;
7. add it to `telegram_creator_clue_index_audit.py` so future exports can detect
   deletion, text drift, or reply-graph changes.
