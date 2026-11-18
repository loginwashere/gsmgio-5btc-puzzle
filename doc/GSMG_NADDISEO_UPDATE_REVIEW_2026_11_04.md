# Naddiseo fork update review — 2026-11-04

The fork has **no newly verified endgame opening**. Since our August full-file
audit it gained seven commits, a visual walkthrough, and three unverified notes.
The October chain claim reproduces as arithmetic, but supplies no independent
validation. The BTCSEED and square-matrix discussions do not supersede our
existing investigations.

## Sources and coverage

Live source: [Naddiseo/gsmgio-5btc-puzzle](https://github.com/Naddiseo/gsmgio-5btc-puzzle).
Public REST API retrieved on **2026-11-04 at 08:58:54–08:58:57 UTC**;
additional PR-file pagination and baseline tree retrieved at 08:59:44–45 UTC.
The API is newer than the cached web commit/PR pages, which omitted September
changes. Use the saved API snapshot for the counts below.

| Surface | Coverage |
| --- | --- |
| Default branch | `master`, HEAD `9e61693404ef74e8e681598116d371924f399ffa`, last pushed 2026-09-29 |
| Branches / tags | One branch; no tags |
| History | All 27 commits listed; seven commits after baseline `15b43fc859c33170d7c45b9fe41789d77b7af974` |
| Trees | Complete baseline and current trees compared by Git blob IDs; 85 → 89 files |
| Ordinary issues | All 10, open and closed; five open |
| Pull requests | All seven, open and closed; zero open, four merged, three closed unmerged |
| Conversation comments | All 36 publicly returned issue/PR comments, with every thread fetched separately and IDs cross-checked against the repository-wide comment list |
| Other discussion | One inline review comment, one submitted review, one commit comment |
| PR files | Every PR's changed-file list; #15 required two pages, 100 + 93 files |
| Source inspection | Current added walkthrough and notes; PR diffs and selected rejected-PR source/materials downloaded and read; no downloaded code executed |

**Coverage exception:** old issue #2 advertises two comments, but both the
per-issue endpoint and repository-wide endpoint expose only one for that issue.
The missing advertised comment was not available; its content is unknown.

Evidence: [API snapshot and download digests](evidence/NADDISEO_UPDATE_REVIEW_2026_11_04.json).
Verification: [offline reproducer](../tools/gsmg/naddiseo_update_review_2026_11_04.py)
and [results](../tools/gsmg/naddiseo_update_review_2026_11_04_result.json).
The previous [full-file audit](GSMG_NADDISEO_REPOSITORY_FULL_AUDIT.md) remains
correct for its pinned August tree; its statement about the current upstream
tree should now be read with this update.

## What changed in master

[Exact comparison against the August audit](https://github.com/Naddiseo/gsmgio-5btc-puzzle/compare/15b43fc859c33170d7c45b9fe41789d77b7af974...9e61693404ef74e8e681598116d371924f399ffa).

| Date | Commit | Change and significance |
| --- | --- | --- |
| Aug 25 | `5267efd763ae` | Adds yellow/blue-count and FEFE-parity notes in `unverified/` |
| Aug 25 | `cd44b37322e1` | Removes a solver's name from the FEFE note; retains community attribution |
| Aug 26 | `207e1e185ba7` | Documents the existing title-plus-address SHA-256 route to SalPhaseIon; printed URL has `gmsg.io`, a transposition typo |
| Sep 5 | `81f68e5073a7` | Adds advice requiring verifiable output structure; no new puzzle bytes |
| Sep 27 | `03bc4b7154ae` | Adds `index.html`, an interactive visual explanation of the known route and statistical false-positive pitfalls |
| Sep 29 | `375c78931b27` | Adds `unverified/11110.md` |
| Sep 29 | `9e61693404ef` | Links the `11110` note from the unverified index |

Only `README.md` and `unverified/README.md` changed among the original 85 files.
All **83 other pre-existing blobs are identical**, including all seven notebooks,
the puzzle image, hint images, audio, and encrypted payload files. Four paths
were added, none deleted. This is a complete tree comparison, not an inference
from commit titles.

The new HTML contains runnable educational visualizations: spiral decoding,
Beaufort/checkerboard demonstrations, audio cancellation, soup decoding, and
statistical experiments. Source review found no newly claimed DBBI/FAED decode
or working final password. The page itself still marks the endgame open.
Its period-1–40 statistical display cannot establish that all possible structure
or methods have been exhausted. I did not run its browser interactions.

## Merged PR #16: the `11110` connection

[PR #16](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/16), by `sha256ppy`,
merged September 29. Two files, 49 added lines, no discussion comments or reviews.
Its proposed connection is the image's colour-bit stream → `11110`, plus the
low five bits of `FE` and a three-step feedback shift.

Independent arithmetic checks:

- The 24 colour bits are `111101110011110110010010`, exactly the low bits of
  `gsmg.io/theseedisplanted`, already documented locally.
- `11110` occurs at zero-based offsets **0 and 10** in those bits.
- `0xFE & 31` is indeed binary `11110`.
- An **eight-bit left rotation** of `FE` by three yields `F7`, matching the
  colour stream's first byte. A feedback shift register would require a tap
  rule that the note does not specify; the operation is ambiguous as written.

This is a reproducible relationship to an already-known answer, not a new
decryption. The local [README](../README.md) already discusses JFK/EO11110 in
the part-5 explanation. The new image association supplies neither an
independent selector for the rotation nor a new endgame operand. Keep it as
an unverified origin hypothesis for the old five-bit component. The fork's
visualization's broad claim that no intended reasoning has been published is
stronger than the evidence: proposed reasoning exists, but is not established.

## October issue #17: chain claim and the comments that qualify it

[Issue #17](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/17), opened
October 5 by `dz17ghost-create`, is the newest issue. Read all three comments,
including the October 15 follow-up.

The claimed construction is reproducible:

1. SALPH, EVP-MD5/AES-256-CBC, password
   `matrixsumlistenterlastwordsbeforearchichoicethispasswordmatrixsumlist`
   → 79 bytes, SHA-256
   `1449a2178eea7c0e3fabac8c1ad2afa294be4fc1800c594a025a056e88c626bf`.
2. Encode its first 32 bytes as uncompressed WIF and use that text as
   P32TRAILING's EVP-MD5/AES-256-CBC password → 79 bytes, SHA-256
   `b40fce72ef5638e4f79b3233e653f8a5dbdb0d4ae2009d2d3da2c98b70f4d004`.
3. The second result reproduces the issue's two 32-byte chunks and 15-byte tail.

**What this does not establish:** both plaintexts have a single `01` padding
byte, roughly **39% and 46%** printable bytes with whitespace, and no independent
format/checksum requirement. Splitting arbitrary 79 bytes into 32 + 32 + 15
does not validate that interpretation. Deriving compressed and uncompressed
addresses from all four putative scalars yields **zero matches** to the two
tracked addresses.

The six direct Cosmic continuations, WIF of C2/S1/S2 in both compression modes
under EVP-MD5/AES-256-CBC, all fail padding. This independently repeats that
bounded part of the issue; its larger unspecified candidate/KDF sweep was not
rerun. For a uniformly random final AES block, the chance of any valid PKCS#7
padding is `(1 - 256^-16)/255`, about 1 in 255; a one-byte `01` specifically costs
1 in 256. The thread supplies no predeclared search size that would let us price
the chain's post-selection evidence.

Important comment outcomes:

- [Naddiseo, Oct 5, first reply](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/17#issuecomment-5996075225):
  readable output is his inference from solvable puzzle design, **not a new
  private confirmation from the creator**. He provides no missing password rule.
- [Naddiseo, Oct 5, second reply](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/17#issuecomment-5996117956):
  rejects the purported independently documented validation anchor.
- [sha256ppy, Oct 15](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/17#issuecomment-6200057255):
  identifies the one-byte-padding issue and the inevitable 80 → 79-byte shape.

The same chain outputs occur in an [older May community write-up](https://github.com/VtotheN/GSMG-PUZZLE-WORK/blob/main/BRIEFING_GSMG_5BTC_PUZZLE_2026-05-26.md),
and the starting password appears in [puzzlehunt issue #88](https://github.com/puzzlehunt/gsmgio-5btc-puzzle/issues/88).
Recomputing those same outputs is not independent authentication of their
intended meaning. **Disposition: mechanically reproduced, unvalidated as a
puzzle step.** Low printability alone cannot disprove an intended binary payload.

I also replayed the exact key/IV supplied in the follow-up to old
[issue #6](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/6). It does produce
the often-cited `4f7a1e4e…c081` hash, but only a 1327-byte body with a one-byte
pad, **40.2%** printability and **7.870 bits/byte** empirical entropy. This
resolves the comment's key-versus-passphrase objection without accepting its
claim of a meaningful Cosmic decode.

## Issue #13: BTCSEED, including corrections and follow-ups

[Issue #13](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/13) has 11
comments. It proposes DBBI first-occurrence order → Bifid square → FAED
whole-block decryption. The output starts `BTCSEED`; it remains a proposal.

The substantive discussion progresses beyond the initial favorable response:

- Naddiseo initially considers it worth pursuing and asks about hashes and keys.
- The early probability discussion is later corrected to distinguish a fixed
  seven-character **prefix** from words occurring anywhere in the output.
- The exhaustive nine-letter key-order test gives **8 / 362,880** matching
  `BTCSEED` prefixes. I reran this: all eight keys and **73,097** distinct
  achievable seven-character heads reproduce, agreeing with local Phase 546.
- All odd one-based output positions are restricted to `{D,B,C,E}` by the
  square's first two rows. The single `Z` at position 98 is produced by the
  relevant H/H column pairing; it is not independent evidence of a separator.
- The discussion ends without a coherent tail decode. One commenter lowers
  its priority. The September 23 comment reports dead paste/anonymous links,
  but supplies neither a replacement artifact nor a new computation.

Already covered by [Phase 386](../tools/gsmg/phase386_btcseed_bifid_faed_decode_audit.py),
[Phase 546](GSMG_PHASE546_PREFIX_SELECTIVITY_CURVE.md), and subsequent local tail
tests. Our wider predefined dictionary class has 4,948 qualifying heads among
the 362,880 squares; it is a different acceptance set from the issue's narrower
thematic examples. Do not interchange their rates. The exact phrase is rare,
but rarity after observing it is not a continuation or proof of intentionality.

Also preserve the attribution boundary: a comment interprets `yinyang` as a
required decode output from these blocks. That is the commenter's proposed
binding. Our [creator clue index](GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md)
records the creator's reached-phase language without proving that exact source
assignment.

## Issue #14 and the other issue threads

[Issue #14](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/14): the expansion
still reproduces **169 = 13²** and **1225 = 35²**. The new October 5 comment
reports negative row/column/snake/spiral/reversal and trit interpretations,
with no script or outputs attached. Our
[Phase 515](../tools/gsmg/findings/P00515.md) already tested its declared
eight-route/two-convention family with no oracle hit. The comment mentions
spirals and trit-group alphabets beyond that exact local family; record those
as community-reported negatives, not independently reproduced exclusions.
No new selector or plaintext appears.

| Other issue | Comments reviewed and outcome |
| --- | --- |
| [#11](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/11), provenance | Three comments. Author withdraws the missing-chat and private-only-secret concerns after finding the export; Naddiseo challenges the unchanged-site claim; author distinguishes the new homepage wrapper from byte-matching puzzle artifacts. Vanity generation does not logically prevent a key being encrypted into artifacts. No new missing page supplied. |
| [#3](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/3), `shabef` | Three comments. `sha256` remains a plausible reading; September 16 reply rejects the claimed Cosmic decode. No new result. |
| [#6](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/6), claimed Cosmic decode | Two comments; exact corrected AES parameters replayed above. Closed; no validated plaintext. |
| [#2](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/2), glyph blob | One accessible comment explains recovering bytes and the established codec route. Second advertised comment unavailable. |
| [#4](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/4) | One reply invites posting the claimed discovery; no public discovery follows. |
| [#5](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/5) | Two replies; author concedes fake data and inability to decode DBBI. |
| [#7](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/7) | One reply points to the Telegram invitation already in the README. |

The only commit comment is an April request for private conversation, not a
published finding.

## PR #15 and the complete PR inventory

[PR #15](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/15) is potentially
useful as a research archive, but **was closed without merging** on September 26.
It proposes **193 files, 168,496 additions**, and no PR description. Its head
repository is now absent from the API, but the preserved commit
`1e913fdbd42b8d5bd7d0a0cf3406d6abdd33142a` remains readable through the fork
network. Naddiseo's sole comment declines reviewing its size; that is not
validation or technical refutation of every file.

I inspected its complete changed-path inventory and downloaded its analysis
notes, Python harnesses, and selected material files, including `neo/LEDGER.md`,
`NEXT_PASS.md`, `aes_try.py`, and the provenance/false-decryption notes.

Useful implementation details:

- Pins the SALPH/P32TRAILING/Cosmic envelopes to the same bytes used here.
- Contains EVP-MD5/SHA1/SHA256, AES-128/256, additional PBKDF2 campaigns, address
  checks, and solved-phase positive controls.
- Recognizes the same false-positive problem in `4f7a1e4e…` Cosmic output and
  explicitly quarantines several Drive/chain-derived files.
- Supplies readable campaign inventories and identifies previous pool and
  padding-gate coverage gaps, followed by claimed negative rechecks.

Limits that prevent importing its conclusions wholesale:

- `Harness.n` counts actual decryptions, while campaign log files record only
  selected padding-valid results. JSONL line counts do not prove total coverage.
- `check_pt` accepts padding of at least four bytes by itself, or short magic /
  printability thresholds. That is a screen requiring calibration to search
  size, not categorical proof of correctness.
- A negative bounded phrase/transform family does not establish that all
  soup operators or all published-material derivations are exhausted.
- Its creator-log scope labels are editorial annotations. For example, its
  discussion treats `First or zero` as previously unused, whereas our clue
  index and earlier phases already track message 4105. Its suggestion of
  moving effort externally is not a newly authenticated requirement.
- I did not independently rerun all campaigns, download all large JSONL logs,
  validate all on-chain assertions, or follow its proposed future searches.

| PR | Final state | Result |
| --- | --- | --- |
| [#16](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/16) | Merged Sep 29 | `11110` unverified note, assessed above |
| [#15](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/15) | Closed, unmerged Sep 26 | Large negative-search archive; no demonstrated solve |
| [#12](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/12) | Merged Aug 25 | Two Phase-0 notes; three discussion comments, one review and one inline attribution correction keep them explicitly unverified/community-authored |
| [#10](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/10) | Merged Aug 22 | Fixes the truncated full-FEN password; already included in our August baseline |
| [#9](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/9) | Closed, unmerged Jun 16 | Reorganized solver material; one owner reply questions purpose; no new accepted solve |
| [#8](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/8) | Closed, unmerged Jun 12 | Bifid/YOUWON and other hypotheses labeled as breakthroughs without final validation; no discussion comments |
| [#1](https://github.com/Naddiseo/gsmgio-5btc-puzzle/pull/1) | Merged Aug 2023 | Historical notebook/walkthrough reorganization; no new activity |

## Effect on the investigation

No frontier gap closes. Keep the existing DBBI/FAED/lock work as the frontier.
The most useful update is firmer triage: the October chain is a repeated,
unvalidated construction; `11110` is an old-answer association; BTCSEED has no
new continuation; PR #15 offers overlapping negative-search coverage that
must be compared family by family before repeating or adopting it.

There is **no new creator-authenticated hint** in these fork updates.
Naddiseo's statement about readable output is explicitly an inference. A new
independently checkable format, target-address match, source-selected operation,
or coherent continuation would change this assessment; repeated hashes of
the same derived bytes do not.

Reproduce the bounded checks offline:

```bash
python3 tools/gsmg/naddiseo_update_review_2026_11_04.py
```

The runner validates the saved coverage/tree delta, a known solved AES
plaintext, a known secp256k1 address vector, both alleged short-chain decrypts,
four extracted-key address checks, six direct Cosmic WIF continuations, issue
#6's exact key/IV, the 9! Bifid-prefix enumeration, expansion lengths, and the
`11110` bit identities. It does not rerun the rejected PR's search campaign.
