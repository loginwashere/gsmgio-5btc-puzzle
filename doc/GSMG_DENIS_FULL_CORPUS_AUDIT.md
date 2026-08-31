# GSMG Denis Golovkin Full Telegram Corpus Audit

**Date:** 2026-08-31  
**Account:** `user398109413`  
**Display name:** `Denis Golovkin`

## Result

The current three-export Telegram overlay was swept exhaustively for the
account id `user398109413`, including every message, reply edge, edit marker,
photo, file, archive, animation, and video. This is an identity-safe community
corpus audit: Denis Golovkin is **not** the puzzle creator account
`user9815232` (`Jrk Bgrt`), even though Denis's display name is the creator's
real-world name.

No creator-confirmed transition or successful decryption appears in Denis's
corpus. The sweep reproduces the known DBBI yellow/blue-prime construction,
its fitted segmentation, the `IZLKESEEDQPPEN` row-sum output, the later
31-character extraction, and Denis's own reported anagram failure.

One exact relation was not previously indexed in this project:

```text
rabbit LSB color mask:       F73D92
integer half:                7B9EC9
add Trinity (3):             7B9ECC
DBBI prime-endpoint mask:    7B9ECC
```

The equality is real but not independent confirmation. Once the already-known
20-bit common prefix is fixed, it says only that the remaining three-bit tail
changes from `001` (1) to `100` (4), whose difference is necessarily 3.
`Trinity` was attached after both masks were known, and no creator-authored
message independently prescribes this operation.

## Frozen scope

The audit merges, with later exports winning on edited/reaction-updated rows:

- `ChatExport_2026-07-26`;
- `ChatExport_2026-08-09 (1)`;
- `ChatExport_2026-08-30`.

The merged group corpus contains 60,375 rows through message id `70186`.
Selection uses `from_id == "user398109413"`, never the display name.

### Corpus accounting

| Item | Count |
|---|---:|
| Denis messages | 1,492 |
| Date range | 2024-11-29 through 2026-08-30 |
| Edited messages (latest state available) | 651 |
| Outgoing reply edges | 982 |
| Denis messages receiving replies | 481 |
| Incoming reply edges | 580 |
| Messages with attachments | 144 |
| Available attachments | 144 |
| Unique attachment SHA-256 values | 137 |
| Still images | 103 |
| Videos/animations | 27 |
| Direct text files | 12 |
| XZ archives | 2 |

All 144 referenced attachments are present locally. Six duplicate-hash groups
reduce them to 137 unique byte streams. The two archives are byte-identical;
the three `canihaveallhint` uploads are byte-identical; two screenshots and
one animation were each reposted.

## Method

`tools/gsmg/denis_full_corpus_audit.py`:

1. merges the pinned exports and retains source-export provenance;
2. selects Denis by Telegram account id;
3. records full text, dates, edit markers, outgoing parents, incoming replies,
   URLs, long tokens, and topic memberships;
4. resolves and SHA-256 hashes every attachment;
5. reads text/HTML/patch files directly;
6. lists XZ archive members and reads bounded textual members without
   extracting paths to disk;
7. OCRs every still image using the established grayscale/autocontrast flow;
8. samples every video at five fixed fractions and OCRs each sampled frame.

All 103 still images were additionally reviewed in five generated contact
sheets. The 27 videos consist primarily of reaction clips; the substantive
screen recordings show terminal brute-force output, the SalPhaseIon Matrix
animation, a Telegram scrollback, and a JS Paint experiment. No unindexed
primary-source clue was visible.

Machine-readable outputs:

- `_work/denis_full_corpus/messages.jsonl` — all 1,492 messages;
- `_work/denis_full_corpus/attachments.json` — all extraction/hash results;
- `_work/denis_full_corpus/summary.json` — counts and topic indexes;
- `_work/denis_full_corpus/attachment_index.tsv` — compact media index;
- `_work/denis_full_corpus/image_contact_sheet_01.jpg` through `_05.jpg`.

## Findings

### 1. Denis's yellow/blue-prime model is DBBI-first, not `574061`

Across all 1,492 messages, Denis never posts `574061`. His color-number path
uses the blue-one mask `F73D92`:

```text
message 60575, 2026-03-12:
F73D92 / 2 = 7B9EC9
7B9EC9 + 3 = 7B9ECC
"Look, we have dbbi primes now!"
```

He repeats the construction in message `68819` on 2026-08-16. A week later,
message `69525` explicitly retreats to uncertainty: “Probably it's not about
0/1 LSB number. But who knows.”

This matters for provenance. The project's complementary-polarity
`574061` prime reconstruction is an independent later finding; it is not
something inherited from Denis's guide or messages.

### 2. Exact scope of the half-plus-three identity

The two masks are:

```text
rabbit 24 bits: 111101110011110110010010 = F73D92
after /2:       11110111001111011001001  = 7B9EC9
DBBI 23 bits:   11110111001111011001100  = 7B9ECC
```

The shifted rabbit mask and DBBI mask share their first 20 bits. Their tails
are `001` and `100`, so:

```text
100₂ - 001₂ = 4 - 1 = 3
```

Therefore `/2 + 3` elegantly packages three observed facts—the 24/23 length
difference, the 20-bit prefix, and the two tail mismatches—but does not supply
a fourth independent check. The focused executable audit is
`tools/gsmg/denis_half_trinity_relation_audit.py`.

### 3. The historical guide is reproduced, including its defects

Denis's messages `60050`, `60325`, `60884`, `60888`, and `61489` describe the
community guide:

- tokenize DBBI with `b = 2` and selected `be = 25 = Y`;
- make `b`/`be` land at successive prime token positions through prime 83;
- compare those endpoint colors to the rabbit LSB colors.

The guide produces:

```text
DBBI:    BBBBYBBBYYBBBBYBBYYBBYY  (23 bits)
rabbit:  BBBBYBBBYYBBBBYBBYYBYYBY (24 bits)
```

The first 20 bits agree. Events 21 and 23 disagree. The published 14x14
placement also shifts event 9 one spiral cell early. Message `39989` is the
key methodological admission: when asked whether ambiguous `b`/`be`
boundaries were chosen merely to match the matrix, Denis answers, **“To match
all prime positions.”** This makes the historical rate descriptive, not a
discovery significance claim.

The guide's row sums still reproduce exactly:

```text
34, 51, 37, 36, 30, 44, 56, 56, 55, 42, 41, 15, 56, 13
-> modulo 26, A=0
-> IZLKESEEDQPPEN
```

The centered `SEED` is real, but the output is not authenticated and opens no
known target. The FEFE-adjusted image posted by Denis at message `61488`
preserves a `SEED`-like center while changing surrounding letters; the
project's pre-registered corrected collision family remains negative.

### 4. The later 31-character extraction remains a recognition checkpoint

Messages `60333` through `60352` provide Denis's complete narrated chain:

```text
ncsyangcahiriasogaleafayanestve
```

It visibly contains `yang`. Denis proposes phrase anagrams and then reports
that he brute-forced “few trillions of anagrams” without finding a key to
proceed. His full narration treats `matrixsumlist` as the already-decoded
Matrix-parody text and “last words before archi choice” as the
`incaseyoumanagetocrackthis...` tail. No creator message confirms that scope,
matrix operation, or consumer.

The complete Denis corpus supplies no later message retracting that negative
or showing a successful authenticated transition.

### 5. Attachment disposition

The substantive files are accounted for:

- `puzzle.png` has SHA-256
  `38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830`,
  byte-identical to `doc/img/gsmg_puzzle_stage1.png`;
- `Cosmic (1).txt` is Denis's 280,718-character OCR with errors, already known
  and containing no missing `matrixsumlist` operation;
- `Jrksplain.txt` and the three identical `canihaveallhint` files are
  community compilations of creator statements, not newly authenticated
  creator artifacts;
- `bifidPlaygroundV5.html` preserves Denis's Bifid experiment but supplies no
  successful FAED decode;
- `matrix-animation.patch` only changes presentation of the Matrix-rain page;
- `cd.b64.txt`, `p3.b64.txt`, `p32b.b64.txt`, and `sa.b64.txt` are copies of
  known ciphertexts;
- the two identical `archive.tar.xz` files contain a compact mirror of known
  puzzle HTML/images, not a new recipient artifact;
- `bytes.txt` and the Samsung Notes screenshot document the already-known
  code-page/Beaufort experiment;
- the remaining images/videos are experiments, terminal output, diagrams,
  chat screenshots, source-page photos, password-list screenshots, and
  reaction media. None carries a creator-authored missing operator.

### 6. Corpus-wide disposition

Denis consistently distinguishes speculation from proof. His own messages
label the Bifid `btcseed` output a coincidence, reject padding-only AES
“successes,” report failed anagrams, and acknowledge uncertainty about the
LSB-number interpretation. There is no claim in the full account corpus that
survives as an authenticated solve.

The useful retained evidence is therefore:

1. the exact historical DBBI/rabbit construction and its provenance;
2. the exact `F73D92 // 2 + 3 = 7B9ECC` identity, classified as a compact
   restatement rather than an independent confirmation;
3. strong negative provenance for the anagram/direct-password continuation;
4. complete attachment accounting with no overlooked primary-source file.

## Limitations

- Telegram exports preserve only the latest visible form of edited messages,
  not edit history. The 651 edit markers cannot recover earlier text.
- OCR can miss small or stylized text. Contact-sheet review mitigates this for
  all still images, and fixed-frame sampling mitigates it for videos, but this
  audit does not claim a pixel-level steganographic analysis of every meme or
  screenshot.
- Denis is a community researcher. His messages can establish provenance for
  community methods and reported negatives, not creator intent.

## Reproduction

```bash
python3 tools/gsmg/denis_full_corpus_audit.py
python3 tools/gsmg/denis_half_trinity_relation_audit.py
python3 -m unittest \
  tools/gsmg/test_denis_full_corpus_audit.py \
  tools/gsmg/test_denis_half_trinity_relation_audit.py
```
