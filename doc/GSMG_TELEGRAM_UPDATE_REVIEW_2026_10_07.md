# Telegram update review — 2026-10-07

There is no new creator post, no verified decryption, and no new authenticated clue. Seven concrete
strings and one specific padding claim were checked exactly: all negative or explained. One
untested cipher axis (Rabbit, via CryptoJS) is recorded as a hypothesis. It is not run here.

## Coverage and source

Source: `~/Downloads/Telegram Desktop/ChatExport_2026-10-07/result.json`
(SHA-256 `cde17d9b67e88e174a9472331bb46cb159e5d8618bb6d08a6e0aeea7c51ea58f`), group
`GSMG Puzzle Solvers` / `1166734859`.

- 1,517 rows, ids 73817-75648. New since the 2026-09-28 export (max id 73868): 1,481 rows, ids
  73869-75648, 2026-09-28 17:12 to 2026-10-07 10:27. That is 39 service events, 1,384 text
  messages, 42 photos, 4 files, 27 stickers and 24 animations.
- No overlapping message changed text.
- **Zero posts from the creator account `user9815232`.** A solver's claim that the creator "posted 7
  days ago" (75484) is not reflected in this group.
- All new message text was read in full. All 42 photos were inspected visually on contact sheets.
  The three new text attachments were read without execution. The extract and sheets are in
  `_work/telegram_2026_10_07/`.

## Exact checks

Script: `tools/gsmg/telegram_2026_10_07_claims_check.py`; result:
`telegram_2026_10_07_claims_result.json`. Forms and oracles are as in the endgame map's U1-U5 check:
raw / SHA-256 digest / hex lower and upper / double SHA, each with no newline, LF and CRLF. The
oracles are CBC with all KDF variants, stream, ECB, key wrap, raw key, and the prize and halving
addresses, over all four blobs.

| Msg | Claim | Exact material | Result |
|---|---|---|---|
| 74075/74079 | "zion0101" / "Z1ON0101" (Draikoon, from a Mr Robot screen) | both strings | 0 |
| 74539 | "ZION" decrypts SALPH (later called a false positive) | `ZION` | 0 |
| 74863 | five phrases (Mohamad) | `leavethematrix`, `yourlastcommand`, `hereismysecret`, `isolveditwithanabacus`, `secondanswer` | 0 |
| 74719 | `sha256(followthewhiterabbit)+adipfBrr` gives a 5-byte valid padding on COSMIC (Boulayo, "probably noise") | hex + `adipfBrr`, SHA-256 KDF | **reproduces**: last bytes `0505050505`; printable 0.386, equal to random. Explained as a mined suffix (a 5-byte pad is about a 2^-40 event; an 8-character mixed-case suffix fits a search). Not an opening. |

`zion` (plain) was already in the curated tested corpus.

## Claims checked against existing records

- **"I decrypted the 3.2.2 blob (P32TRAILING); 158 hex characters"** (Cebotari, 74724-74802).
  The screenshots show the tool reporting "not UTF-8" and a binary body starting `d098dde9...`, and
  a gsmg.io URL built from it returning `Hello :-)`. A 79-byte non-text body under a valid pad is
  the expected padding false positive. No password was disclosed, so there is nothing to replay.
- **"Decoded Cosmic Duality: 2 keys and a tail"** (75029-75054). The poster says none derives a
  known address, and lists four unrelated addresses. This is consistent with a padding hit. The
  poster and Draikoon both call it a wrong key.
- **`74c974e3...` "envelope, the only author one left"** (Marc, 75315). That is the salt of our
  **quarantined URLBLOB**. Marc's own map (75550) retires it as a community artifact, agreeing with
  our records (Phase 25).
- **Marc's map: "`fourfirsthintisyourlastcommand` comes from OP_RETURN, not an author route."**
  This is **contradicted by authenticated bytes.** `shabefourfirsthintisyourlastcommand` sits at
  positions 860-895 of the SalPhaseIon textarea (`page_structure_audit.py`), which is byte-identical
  across 16 archive captures (F-OBJ-003). OP_RETURN copies exist (Phase 156), but the phrase is on
  the page.
- **DBBI "off-center mirrors"** as a 13x7 grid aligning with `theprivatekey` / `andbetterhalf`
  (Flo Sku, Boulayo; photos 74731, 75455). This is post hoc, with no null given. Marc's map reports
  it as weaker than the best random control. Not pursued.
- **"Barend: the automated system doesn't work since the website migration"** (75139). New account
  (`user12919314`) with no prior messages. No basis.
- **Testnet "dialogue"** at the testnet form of 1GSMG's hash160 (75249-75278). Naddiseo
  relays that the creator said the on-chain messages were not his (75296). This is consistent with
  Phase 156.
- **Undisclosed private findings:** "10 meaningful characters in the first quarter of the BTCSEED
  decode" (Boulayo, 75244), "`label -> FILM`" (Draikoon), "who the wise man is" (Cebotari). Nothing
  checkable was given.
- Numerology (DBBI digit string "starts with 422 and sums to 422", 74498), the "Jaden Smith / zero
  the I's" chain (74914-74916), chess readings of "one for one, four for one", and "MELT MY
  SECONDANSWER" (a joke) carry no selector. Not pursued.

## Attachments

- `Hint MR.Robot.txt`: two ChatGPT-sourced links to an unrelated 2019 r2con CTF. Not relevant.
- `braille-logic.py`: maps braille digits `a-i -> 1-9`, `j/o -> 0`. This matches the page's known
  decimal transport; nothing new.
- `GSMG PUBLIC MAP EXPLICATION.md`: a community status map. Its method rules agree with ours.
  One factual claim is wrong (above).
- `vdoc.pub_cosmic-duality.pdf`: a full scan of the *Cosmic Duality* book. Could be used to verify
  our transcription; not needed now.
- The Russian `.txt` in the export's files folder is an unrelated Ethereum transaction-monitor bot.
  It belongs to no new message.

## One untested axis, recorded as a hypothesis

Photo 75068 shows a cipher tool's menu (RC2, RC4, **Rabbit**, S-AES, S-DES, SM4). Rabbit is an
eSTREAM stream cipher (RFC 4503). CryptoJS's `Rabbit.encrypt(msg, passphrase)` emits the same
OpenSSL `Salted__` Base64 envelope (`U2FsdGVkX1...`) as the puzzle's blobs, with an MD5
`EVP_BytesToKey` (128-bit key, 64-bit IV). A grep of the repository finds no Rabbit or CryptoJS
oracle; Phase 519 closed only CAST5 and RC4 for the OpenSSL menu.

- **For:** "follow the white rabbit" is the creator's first hint; the envelope format is compatible;
  the oracle has never covered it.
- **Against:** every solved blob was AES-256-CBC with the **SHA-256** KDF (the OpenSSL 1.1+ CLI);
  MD5, the CryptoJS default, fails on them (verified 2026-09-28). A stream cipher has no padding,
  so a check needs a plaintext-structure detector.
- **If run:** implement Rabbit against the RFC 4503 test vectors and add a CryptoJS-compatible MD5
  KDF (and SHA-256 for completeness). Then replay the existing curated candidate corpus once,
  without new candidates, against all four blobs, with a printable / Base64 / WIF structure gate.
  Calibrate it on a planted CryptoJS-style envelope.

### Rabbit / CryptoJS backfill: run 2026-10-07, negative

- **Port.** `tools/gsmg/rabbit_cryptojs.py` ports crypto-js 4.1.1 `rabbit.js` and `rabbit-legacy.js`
  line for line, batched with numpy. `test_rabbit_cryptojs.py` freezes 10 vectors produced by the
  real library: keystreams for both variants at three key/IV pairs, and four full passphrase
  envelopes. All match exactly.
- **Run.** `tools/gsmg/rabbit_cryptojs_backfill.py`, result in
  `rabbit_cryptojs_backfill_result.json`. Existing corpus only: 66,436 candidates (curated tier,
  `medium_curated_all.txt`, `last_command.txt`, the 4 verified prior hashes); corpus digest
  `52b6c35e...`. Standard forms give 1,397,054 materials. These were run under {Rabbit,
  RabbitLegacy} x {MD5, SHA-256 KDF} against SALPH, COSMIC, P32TRAILING and URLBLOB.
  44,705,728 trials, including the planted targets.
- **Control.** All 4 CryptoJS-made planted envelopes were recovered (80/80 printable).
- **Result.** **0 hits** (at least 64 of 80 bytes printable) and **0 weak rows** (at least 56) on the
  real blobs. The Rabbit/CryptoJS axis is closed for the existing corpus. A new candidate would still
  have to be checked on this axis.

## Disposition

No creator evidence, verified decryption, or new authenticated artifact. Nothing in this export
changes the endgame map (`GSMG_ENDGAME_OPERAND_CONSUMER_MAP.md`). The only new testable item is the
Rabbit/CryptoJS cipher axis above, which is optional and low prior.
