# Telegram update review — 2026-09-28

September 29 follow-up: Phase 547 has since completed negative within its
declared census. [Phase 548](GSMG_PHASE548_FAED_DISTRIBUTION_BOUNDARY.md)
adds a bounded negative distribution-boundary test and a native-source check
on `ANTIYBCORETNT`. Recommendations below describe the September 28 state.

The new export contains one concrete construction worth a bounded audit:
DBBI column sums selecting Architect word initials yield `ANTIYBCORETNT`.
It is reproducible, but not validated as an intended instruction. No new
authenticated creator clue or independently verified blob decryption was found.

## Coverage and source

Source: `/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-09-28/result.json`.
SHA-256: `2ca4773e0661fcb6e56a0d2c9cdf4bcd7368767026e60e595b8bc803cd7975b6`.
Group name/id verified as `GSMG Puzzle Solvers` / `1166734859`.

The export has 1,394 rows, ids 72247–73868. Compared with the September 19
export's maximum id 72416, it adds 1,227 rows: 1,190 regular messages and 37
service events, ids 72417–73868. All new message text was read, including
replies, rather than only searching clue keywords. Eight overlapping messages
have changed export records; their latest text was also read. There are zero
new posts from the known creator account `user9815232`.

All 36 new photo attachments were visually inspected. The game video at
72502 was sampled, and the only new text/code file at 73847 was read without
execution. The other 61 file attachments are videos/animations/stickers;
their metadata and conversation context were reviewed, not every frame.
Deleted messages absent from the export cannot be recovered by this review.

Local extraction, metadata, overlap records, photo sheets and replay results
are in `_work/telegram_2026_09_28/`. Exact checks are recorded in
`technical_replay.json`. No new password search or shuffled statistical
calibration was performed.

## 1. DBBI → ANTIYBCORETNT: shortlist for a small audit

Message **73793**, Андрей Александрович, supplies a complete recipe:

1. Number DBBI's symbols by first appearance: `d=0,b=1,i=2,f=3,h=4,c=5,e=6,g=7,a=8`.
2. Fill a 7×13 rectangle in row-major order and sum its columns.
3. Use the sums as zero-based backward word indices into the solved Architect
   speech ending immediately before the first `SELECT`.
4. Take the selected words' first letters.

Independent replay against the repository's DBBI and solved speech gives:

```text
column sums: 19 27 26 34 13 38 11 31 25 37 18 27 33
words:       A NOW TO IT YOU BECOME CARRY OF RETURN EXCEEDINGLY TEMPORARY NOW THE
initials:    ANTIYBCORETNT
```

The exact output includes `TNT`; truncating it to `ANTIYBCORE` is an additional
interpretive choice. The author associates ANTI with anti-diagonals, YB with
yellow/blue and CORE with an 84-cell interior. Those associations do not yet
specify a downstream operation, its coordinates or its consumer.

The post claims random-shuffle controls, but supplies no code, null counts,
statistic, candidate family or trial history. This review verifies the
extraction only, not that significance claim. Neighboring index conventions
do not retain the prefix; their complete outputs are preserved in the replay
record, without treating that sensitivity as evidence for or against design.
Message 73856 reports another solver considered it noise, without a method.

Prior overlap: Phase 469 tested different symbol values and direct renderings
of matrix sums. Phase 535 tested image-positioned sums against film/screenplay
words before CHOICE. Neither result directly rejects this first-appearance
mapping plus modified-speech-before-SELECT composition. No exact `ANTIYBCORE`
construction was found in the existing local notes/scripts.

**Next action:** give this recipe a short, separate audit before expanding
it. Preserve the complete output and distinguish the proposed reading from
the mechanics. A continuation must fix its input, operation and complete
output test before inspection, and predict something beyond the prefix used
to invent it. Establish any calibration family independently; an exact-prefix
shuffle count chosen now cannot account for the undisclosed discovery search.
Do not enumerate new layouts/word boundaries until an attractive fragment
appears. This is a new testable hypothesis, not a replacement for Phase 547's
already-declared census or a closure of `G-MSL-001`.

## 2. Seven RGBA colors as a private key: real samples, missing rule

Message **73787**, E, proposes concatenating:

```text
FFFFFFFF 000000FF 3F48CCFF FFF200FF FEFEFEFF ED1C24FF F5F5F5FF ????????
```

All seven colors exist in the authenticated `puzzle.png`; they are precisely
its seven most frequent RGBA values. Their pixel counts are saved in the
replay record. The whole image actually contains 453 distinct values, so
"seven main colors" is a selection of dominant flat colors, not the complete
color inventory. Alpha is constant FF, as established by the earlier
[PNG audit](GSMG_FIRST_PIECE_PNG_PALETTE_PROVENANCE_AUDIT.md).

The proposal does not select concatenation order or explain the eighth word.
Its stated seven-color permutation plus arbitrary missing 32 bits contains
`7! × 2^32 = 21,646,635,171,840` candidates. No independently selected key
assembly rule or address match accompanies it. Preserve as a hypothesis;
it does not currently justify that brute-force search.

## 3. Rabbit-mask XOR: reproduced arithmetic, no bound consumer

Messages **73300–73301** pair adjacent three-bit groups of `F73D92`, XOR them,
and produce `2500`, alongside `1344` as the Cosmic envelope length.
The supplied command reproduces `2500`. These are binary three-bit groups,
not ternary trits. The actual Cosmic envelope is 1,344 bytes including header
and salt, with 1,328 ciphertext bytes. No exact downstream check selects
`2500` or this XOR rule. This does not modify the Phase 547 trit model.

## Claims that should not redirect the search

- **P32 / Chain-4 breakthrough, 72431–72432 and following discussion.** The
  screenshot shows `pad_ok` and a claimed `+-` header, but no replayable
  password, complete plaintext, derivation, independent parser specification
  or known-address match. The full public recipe cannot be reconstructed from
  the available messages. Padding alone is already known to give false
  positives; a header would be additional evidence only if its expectation
  and the subsequent structure were established independently. No verified
  decryption is reported here.
- **Emails, 72475/72497/72540.** The screenshots say emailing is not a solve
  route, decline to answer the SSH question, and say no hints. Declining an
  answer is not confirmation that SSH is required. Screenshots do not provide
  authenticated headers or establish sender continuity with the creator.
  The restored domain's ownership was already unverified in
  [Phase 329](../tools/gsmg/findings/P00329.md). Current homepage inspection
  reproduces the already-recorded shutdown presentation, not a new clue:
  [gsmg.io](https://gsmg.io/).
- **NOTEZ/game footage, 72502–72505.** The sampled video is game-console
  footage with a social-video overlay. No creator-authenticated connection or
  primary GSMG artifact containing NOTEZ.TXT is supplied in this thread.
- **Private hint in `nadd_hints/`, 72897.** No image or primary evidence
  accompanies the claim. It cannot establish a missing private ingredient.
- **Forwarded creator remark, 73195.** The text about five BTC being a tiny
  fraction matches historical creator message **66593**; not a new hint.
- **URLBLOB discussion, 73162–73174.** This is the already-known quarantined
  URL artifact, not a newly discovered creator-posted January blob. The
  speaker corrects the original attribution within the thread.
- **New short AES envelopes, 73442–73487.** Posted by a solver; each is a
  32-byte Salted__ envelope with one ciphertext block and salt
  `32656fe06dc950e6`. Later messages describe the post as serving its purpose.
  No provenance connects these bytes to original puzzle artifacts. Keep
  separate from the tracked puzzle blobs.
- **Third-door address, 73835.** `1NULY7DhzuNvSDtPkFzNo6oRTZQWBqXNE9` already
  occurs in the July baseline at ids 5241, 8658, 21682, 25779, 47066 and
  56452. It is not a new door or address discovery.
- **Bare numeric pairs, 73708/73710; other claimed solves.** No derivation
  or independent validator is supplied. Preserve the statements as claims,
  not inputs licensed for another broad search.

The new creator-message archive link at 73043 and the walkthrough link at
73808 are organizational resources, not new creator evidence. Both links
were unavailable through the web tool during this review; this review does
not claim to have checked their current page contents.

## Disposition

Only the exact `ANTIYBCORETNT` composition earns a new concrete audit slot.
The color recipe and XOR identity remain unselected hypotheses. Nothing in
this export establishes that the existing puzzle corpus is insufficient or
that the puzzle has been solved. Phase 547 remains an executable next step;
this review adds one narrowly testable alternative rather than reopening the
closed search families wholesale.
