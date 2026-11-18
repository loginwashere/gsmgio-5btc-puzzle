# Telegram update review — 2026-11-04

There is no new creator-account post or independently verified decryption in this export.
The registered 21-string candidate set and posted WIF/address checks were negative. This
is a bounded check, not an exhaustive test of every concrete string or interpretation in
the window. Disclosed short-chain constructions reproduce without independent validation;
undisclosed openings remain unverifiable.

**Independent verification, November 4:** see
[verification and additions](GSMG_TELEGRAM_INDEPENDENT_VERIFICATION_2026_11_04.md)
for the source comparison, additional literal/password tests, attachment audit, and
corrections to the strength of the original conclusions below.

## Coverage and source

Source: `~/Downloads/Telegram Desktop/ChatExport_2026-11-04/result.json`
(SHA-256 `eaf63cfe31a48bb243b2f85683408b84686a91c56f8f6de952215b1a0bb6a0b3`), group
`GSMG Puzzle Solvers` / `1166734859`.

- 2,828 rows, ids 75556-78805. New since the 2026-10-07 export (max id 75648): 2,777 rows, observed ids
  75651-78805, 2026-10-07 13:17 to 2026-11-04 10:58. That is 136 service events and 2,641 messages:
  2,379 text, 112 photos, 19 files, 5 audio, 7 videos, 67 animations, 52 stickers.
- The 51 overlapping messages have unchanged text. Five message objects have changes in
  other fields; the independent verification records those separately.
- **Zero posts from the creator account `user9815232`.** The only creator text in the window is a
  re-posted screenshot of an old message (photo 76545, 2023-04-15: "It can be solved … not planning
  to release any new hints soon").
- All new message text was read in full. All 112 photos were inspected on contact sheets. Text
  attachments were read without executing them. The extract and sheets are in `_work/telegram_2026_11_04/`.

## Exact checks

Script: `tools/gsmg/telegram_2026_11_04_claims_check.py`; result:
`telegram_2026_11_04_claims_result.json`. String forms and oracles are the same as the 10-07 check:
raw / SHA-256 digest / hex lower and upper / double SHA, each with no newline, LF and CRLF. The oracles
are CBC with all KDF variants, stream, ECB, key wrap, raw key, and the prize and halving addresses,
over all blobs. That gives 315 materials and **0 hits on every oracle**.

| Msg | Poster | Material | Result |
|---|---|---|---|
| 76101 | CS | `THEPRIVATEKEYSBELONGSTOHALFINNEYE` (upper, lower) | 0 |
| 75884 | Ekodama | `yellowblueprimes·matrixsumlist·yinyang·z·lastwordsbeforearchichoice·z·thispassword·z` (with and without `z`) | 0 |
| 76100 | Tommy Walker | `yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang` | 0 |
| 78611/78613 | B58, Alex | `giveityinyang`, `giveityingyang`, `Giveityingyang` | 0 |
| 78422-78425 | Draikoon | `yangyangjin`, `YangYangJin`, `chandlerguolovesyangyangjin`, `Chandler Guo loves YangYang Jin` (block 420000 coinbase text) | 0 |
| 78513 | Andrey | `cryptoio`, `crypto.io` | 0 |
| 78517 | Draikoon | `protect ironic magic me, sight. which still 4 due` (spaced, compact) | 0 |
| 77848-77850 | Draikoon | *derived* from his recipe: `secondanswerenterthispassword`, `secondanswerthispassword` (`secondanswer` alone was already tested) | 0 |
| 75911 | Alex | `obellaciao`, `abcdefghio` | 0 |
| 76188 | Mohamad | `MSG` | 0 |

Keys and addresses, checked against the prize (`1GSMG1…`) and halving (`17ucy1…`) addresses:

| Msg | Material | Result |
|---|---|---|
| 77069 / 77076 | `5J79uwWz…Wv4A8ak4wU` "the level 3 password" | not a valid WIF (50 chars, one short; the 51-char form with `z` is below) |
| 77071 | the same with a trailing `z` | valid WIF → `1BBp2cx…`/`15ERKFB…`; not a target |
| 77646 | `5J79uWwZ…` variant | not a valid WIF |
| 77253 | `Ky1xCg4y…mb2M` | valid WIF → `1HUy7Ue…`/`1BPMLzH…`; not a target |
| 76360 | `5K2byJMs…8AT` (from the "zoo … winner" mnemonic) | valid WIF → `1GKJzHQ…`/`14zJ3RH…`; not a target |
| 77617/77618 | two 25-byte hex strings | bad checksums, version bytes 0xa0/0xba; not addresses |

Tommy Walker's 77646 claim that the prize balance is 0 is false. On 2026-11-04 mempool.space and
blockstream.info both show 125,649,674 sat, with the 1.253243 BTC output from 2024-04-24 unspent.

## Claims checked against existing records

- **Draikoon, "Cosmic solved", with the plaintext being Neo's closing phone speech from *The Matrix***
  (77759-77861, 78073). No password was disclosed, so there is nothing to replay. A correct
  decryption of COSMIC would give about 1,327 bytes. The quoted speech is 356 bytes. He says the rest
  is "another cipher… onion style", "rot13, then base64, then Caesar", but shows none of it. His
  recipe hint (`secondanswer` as the last words, then `enter`, then `thispassword`) was replayed
  above: 0.
- **J (78605), "reproducible solve of the SalPhaseIon AES, prints a prime number of bytes."**
  No length, password, output, or validation is disclosed. Under the 80-byte AES-CBC/PKCS#7
  model, the prime plaintext lengths are 67, 71, 73, and 79; only 79 corresponds to a
  one-byte pad. The message therefore cannot be identified with the known 79-byte false
  positive. Pawel (76033) separately reports 36 padding-valid outputs from 3,340
  combinations × 2 KDFs, against about 26 expected by chance; that does not test J's claim.
- **`cosmic_decrypted_verified.bin` (76420) and the 39/12-address lists (#110 construction).**
  1,327 bytes, entropy 7.87 bits/byte, 39% printable. That is random, i.e. the same 1-byte-pad
  false positive already recorded in the Naddiseo review. Naddiseo says this directly in 76464-76470.
  `CosmicDuality.txt` (76458) is byte-identical to our `COSMIC_BLOB_B64`.
- **`live_salphaseion.txt` (75840).** It contains our `DBBI` (91) and `FAED` (570) exactly, and its
  blob halves agree. Nothing new.
- **Marc's chain "prize → 79 B → WIF → inner → 79 B" (76032, 76822).** His own passphrase gives
  random 79 B, and he concedes (76034) that it is not the real password. Unchanged from the 10-07 note.
- **QR finder-pattern "third door" (Belgvr 75848, Boulayo 77161, 3.14 77184 bit grid).** Already on
  record in `GSMG_PUZZLE.md`, under the finder-pattern dark-gray pixels and edge lines, and in the
  2026-08-21 `#FAFAFA` brainstorm. 3.14 reports the three eyes are identical. No new operand.
- **`gsmg.io/robots.txt` ASCII rabbit (76148, 76845, 78804)** and the "rabbits face opposite ways"
  remark (78804/78805). The file is already recorded in P00329. It has no extra paths.
- **DBBI ↔ URL LSB parity (Pawel 76036, Heisenberg 76145/76225, Kacper 78308).** This is the known
  identity: the prime-index markers equal the URL character LSBs, which equal the poster colours. Two
  posters disagree on whether marker 21 is an inserted or a flipped bit (the 83- vs 84-token parse),
  and RB (76354) cannot reproduce either. Pawel's split of the remaining payload b's into 19|16|23
  was found after the fact, and he gives it about 0.3% himself. Neither is new structure.
- **Pawel's FAED statistics (76019-76028).** `g` occurs 107 times against about 57 for each other
  letter. Pair statistics show no difference between alignments. A Bifid on the DBBI key forces every
  second letter into {b,c,d,e}. All of this agrees with our FAED generator work (Phases 548-550).
- **Numerology without a selector:** the 255/256 words up to "TO SELECT" (Boulayo 76039, recounted by
  Pawel). Pawel tested 1-bit-per-word readings against both addresses and blobs: null. Also: the 24
  primes summing to 479/484 with "privatekey" at index 479 (Marc 75874); 23/16/7 as host/path lengths
  (Marc 76294); `faed[j]+faed[j+285] mod 9` containing "fefefe" (Boulayo 76945, about 4% by chance);
  BEER/NSTEP in a FAED grid (76832); "DIE" from DBBI letters 1/4/21. None of these is pursued.
- **Undisclosed or unsupported "progress":** "DBBI is decrypted" (RaMA2vandama 78136), "at yin yang"
  (B58 78381, 78619), and "solved, prize swept to 17ucy" (christo 78045). The last is false: the prize
  output is unspent. None of these gave anything checkable.
- **Off-topic:** two other puzzles (ZDEN "HALV" crypto.haluska.sk, "Securing wealth in poetry"), a
  Binance/EIP-7702 incident, a spam/doxxing troll, and an invite link to a splinter group (77201).

## Bottom line

No verified advance was found in this window. The unresolved steps include what
`matrixsumlist` does to DBBI/FAED, and the 3.2.2 / SalPhaseIon-small / COSMIC passwords.
Draikoon's COSMIC claim and J's promised follow-up become testable with exact input bytes,
password/KDF, output, and independent validation. Until then, classify them as unverified
rather than assigning them to a particular padding artifact. These negatives do not
exhaust the closed-system search.
