---
type: index
status: live
date: 2026-09-29
topics:
  - salphaseion
  - endgame
  - operand-binding
  - coverage
---

# Endgame operand-and-consumer map

2026-09-29. A map of every instruction-like phrase on the final (SalPhaseIon / Cosmic Duality) page:
what it literally says, what it could refer to, what would consume it, what exact bytes have been
tested, and what evidence would tell the alternatives apart. It is **not** a candidate wordlist and
runs no search.

Why this exists: every solved stage paired a **recognition** (a lyric, a riddle answer, a person, a
product, a pun naming a method) with an **exact computation** (spiral bits, SHA-256, EBCDIC,
Beaufort, checkerboard). Most frontier work since Phase 8 computed on DBBI and FAED. This map asks
whether a missed *referent* could be blocking the final page. It also stops tested guesses from being
relabeled as new ones.

Rules for using it:

1. An identification is written into this map, with exact bytes, **before** it is checked.
2. No reinterpretation after seeing a hash or oracle result.
3. Every coverage claim cites a phase whose findings file was read.

## Page, byte-exact

From `page_structure_audit.py` on the authenticated mirror (`89727c59...html`), SalPhaseIon
textarea, 1,075 logical characters:

| Pos | Segment | Transport | Decoded |
|---|---|---|---|
| 0-91 | DBBI | nine symbols `a-i` | — |
| 91-195 | instruction | binary `a/b` | `matrixsumlist` |
| 195-765 | FAED | nine symbols `a-i` | — |
| 765 | separator | `z` | — |
| 766-829 | instruction | decimal `a-i,o` | `lastwordsbeforearchichoice` |
| 830-859 | instruction | decimal | `thispassword` |
| 860-895 | literal | `befour` = `b,e,f` -> `2,5,6` + `our` | `shabefourfirsthintisyourlastcommand` -> "sha256 our first hint is your last command" |
| 895-1063 | SALPH | Base64, split by binary `enter` into 64 + 64 characters | OpenSSL `Salted__`, 96 bytes |
| 1063-1075 | literal | `bef` -> `256` | `shabefanstoo` -> "sha256" + unresolved `anstoo` |

The separate `Cosmic Duality` textarea holds COSMIC: 1,344 bytes, 28 lines of 64 characters.

Only `shabef -> sha256` is mechanical. `anstoo -> "answer too"` is a community interpretation
(Phase 101 correction).

## Consumers

| Consumer | Type | Status |
|---|---|---|
| SALPH | 96-byte OpenSSL envelope, adjacent to both SHA phrases | open |
| COSMIC | 1,344-byte OpenSSL envelope, own textarea | open |
| P32TRAILING | 96-byte blob at the end of the Phase 3.2 plaintext | open |
| URLBLOB | quarantined | open |
| Final | "Regular Bitcoin Private key" (creator, msg 20223); two keys, "half and better half" (3.2.2 plaintext) | — |

Solved-chain conventions to apply to any new operand (reproduced 2026-09-28): lowercase hex SHA-256
of the answer is the OpenSSL passphrase, with `EVP_BytesToKey`-SHA-256; answers are letters only,
without spaces, and lowercase unless annotated.

## Map

### M1 — "sha256 our first hint is your last command"

- **Answer type:** a string whose SHA-256 (hex) is a passphrase, or a prior hash state that composes
  with an answer.
- **Nearest consumer:** SALPH (it immediately follows). Checks have included all four blobs.
- **Creator evidence:** the only direct request (msg 20222) was answered with a zipper emoji
  (20224). "Who is 'our'?" (20226) was never answered. No creator use of the phrase (Phase 102).

| Referent reading | Exact material tested | Phase | Result |
|---|---|---|---|
| literal phrase / "your last command" / renderings of solved commands (28) | `lastcommand_probe.py` list | 0.1 | 0 |
| entry command `sha256(GSMGIO5BTCPUZZLECHALLENGE+address)`: input, output, CLI renderings (16) | `last_command.txt` | 0.1, chain sweeps | 0 |
| prior command states (`causality`, Phase 3, Phase 3.2, entry hash) combined with 11,899 answers: concat, XOR, HMAC, raw/LF/CRLF | `hash_duality_sweep.py` | 11, 374 | 0 of 4.28M |
| banner, prize address, both, original JPEG, stage PNG, rabbit PNG | `first_hint_hash_audit.py` | 134 | 0 |
| literal "our first hint" variants, full phrase with and without "sha256" | same | 134 | 0 |
| solved Phase-1 password (spelling fixed by the creator's 2019 self-check hash) | same | 134 | 0 |
| creator's first rabbit hint "Follow the white rabbit" (3 exact forms) | same | 138 | 0 |
| "First external hint" lmgtfy URL and its query | `first_puzzle_announcement_audit.py` | 138 | 0 |
| pre-rabbit first GSMG puzzle, 10 mechanical states | same | 136 | 0 |
| first formal 2020 hint (msg 1710, `yellowblueprimes`), msg 8446 forms, `574061`, 31-char selection; x newline x raw/hex/`ans too` double SHA (162 materials) | `binary_hint_operand_audit.py` | 121 | 0 |

**Status:** densely covered. Every grounded referent found so far is negative. **Distinguishing
evidence:** who "our" is (team vs. creator vs. page), and whether "last command" means the SHA
operation, its input or its output. Neither is fixed by any source.

### M2 — `shabefanstoo`

- **Readings:** "sha256 answer too" (community); ANS entropy coding (Phase 283; only the universal
  zero sink round-trips); A1Z26 / anagram / numerology claims (Phase 102, none creator-grounded).
- **Tested:** bare `sha256` and its variants (167); double-SHA "ans too" forms inside Phase 121; the
  hash-duality family (11 / 374).
- **Status:** the operand ("which answer?") depends on M3 and M4. There is nothing to test until one
  of them yields an answer. **Distinguishing evidence:** none on the page (Phase 101: 54 grammar
  models, none strictly supported).

### M3 — `lastwordsbeforearchichoice`

- **Answer type:** words from the Architect scene (or a Matrix "choice" scene), used as a password,
  a key, or a selector.
- **Nearest consumer:** FAED (immediately before it) or SALPH, via M4.

"Choice" occurs **four times** in the scene (shooting script, rebuilt 2026-09-29, 1,455 words from
"I am the Architect" to "We won't"):

| # | Context | Speaker | Last words before it | Tested? |
|---|---|---|---|---|
| c1 | "Choice. The problem is choice." | **Neo** | stage direction "...quietly realizing the truth" | no direct test found |
| c2, c3 | "...as long as they were given a choice even if they were only aware of the choice..." | Architect | "...as long as they were given a" | no direct test found |
| c4 | "As you adequately put, the problem is choice." | Architect | `AS YOU ADEQUATELY PUT THE PROBLEM IS` | **216: 0** (36 keystrings) |
| — | `[23,16,7]` word indices before c4 -> `BOTH/ULTIMATELY/THE` -> `BUT/HYE` (-> `EOL`, -> `BYE`) | Architect | — | 33, 216, 232: 0 as passwords |
| — | trilogy-wide "big choice" phrases (7 strings, 78 materials) | various | — | 182: 0 |

Then **the actual choice**: after the Architect's last line Neo walks to a door. The scene's final
exchange is Neo: "If I were you, I would hope that we don't meet again." Architect: **"We won't."**

- **"We won't" as the last words before Neo's (Architect-offered) choice: no direct test found.**
  A grep of the findings, docs and wordlists finds it only inside mined chat lines, a
  non-creator community message (msg 67789, "we won't -> we will -> rockyou"), and Phase 58's scene
  boundary.
- Coincidence to disclose, not evidence: the creator's macro message contains
  `wewontgiveawaythepassword`. "We won't" is ordinary English, and the link was noticed after the
  macro was known.

**Distinguishing evidence:** whether "archi choice" means the Architect's line about choice (c4)
or the choice the Architect offers (the doors). Film and screenplay agree on the c4 sentence
(Phase 216). The door exchange's wording in the released film has not been checked here.

### M4 — `thispassword`

Three roles survive every typed, topological and semantic test: password *for* FAED; FAED's answer
*is* the password; password for SALPH (Phases 101, 373, 377, 455, 467). **Distinguishing evidence:**
an authenticated consumer accepting one role. This lives downstream of M3.

### M5 — `matrixsumlist` (between DBBI and FAED)

- **Referents with provenance:** `[23,16,7]` (triple-sourced, F-CHAIN-002); the recovered guide's
  14x14 DBBI row sums -> `IZLKESEEDQPPEN` (Phases 53, 535); `401/400/73` (Phase 139).
- **Status:** 7 of 7 matrix fields unbound (G-MSL-001). Heavily searched; no consumer.
- **Distinguishing evidence:** a source fixing dimensions, traversal, value map, aggregation and
  serialization.

### M6 — `enter`

Solved as formatting: it splits SALPH at a unique 64 / 64 (Phase 228). `EOL` links to the Architect
edges (Phase 33). No open referent.

### M7 — creator macro (msg 8446, reversed binary)

`yellowblueprimes` (solved -> `574061`) -> `matrixsumlist` (M5) -> `lastwordsbeforearchichoice` (M3)
-> `yinyang` (state, G-YIN-001) -> `wewontgiveawaythepassword` -> `itsinfrontofyoureyesbutyourenotseeingit`
(Phase 366) -> `verylaststepisatruegiveaway` (Phases 217, 222) -> `promised` (Phase 158). The order
is fixed; the operations between steps are not.

## Untested identifications, registered before any check

Each item gives exact bytes. Every item, when checked, gets the standard forms: raw; SHA-256 raw
digest; SHA-256 lowercase and uppercase hex; SHA-256(hex) (the "ans too" double hash); with no
newline, LF and CRLF. These go against all four blobs, with the full CBC, ECB, stream and key-wrap
oracles and the raw-key address check. A hit counts only if decryption is exact (valid padding plus
structured plaintext) or a key reproduces a known address.

| ID | Row | Exact base strings |
|---|---|---|
| U1 | M3, "We won't" | `We won't`, `We won't.`, `we won't`, `wewont`, `WEWONT`, `we wont` |
| U2 | M3, Neo's line before the door | `If I were you, I would hope that we don't meet again`, `ifiwereyouiwouldhopethatwedontmeetagain` |
| U3 | M3, the whole final exchange | `ifiwereyouiwouldhopethatwedontmeetagainwewont` |
| U4 | M3, c1 (Neo's own words) | `Choice. The problem is choice.`, `choicetheproblemischoice` |
| U5 | M3, c2 last words | `as long as they were given a`, `aslongastheyweregivena` |

U2-U5 are listed because they belong to the same closed set (the last words before each occurrence
of choice, and before the door choice). **The set is closed:** no other scenes, no paraphrases, no
case variants beyond those listed.

### U1-U5 outcome (2026-09-29)

Checked after the registry above was fixed (map SHA-256 `f9e9d4a8...ce2ab2`), by
`tools/gsmg/endgame_map_u1_u5_check.py`; results in `endgame_map_u1_u5_result.json`.

- 13 base strings gave 195 materials.
- Oracles: full CBC over all KDF variants, stream, ECB and key wrap, against SALPH, COSMIC,
  P32TRAILING and URLBLOB. Each digest was also tried as a raw AES key and as a private key against
  the prize and halving addresses.
- `cb_common`'s import-time self-test reproduces the solved Phase 3.2 decryption and the 3.2.2
  decode.

**Result: 0 hits in every oracle.** M3's closed set of "last words before a choice" in the
Architect scene is now covered for direct password use. The row remains open only for other roles
(a key for FAED, or a selector) and for non-Architect scenes beyond Phase 182.

## What would change the picture

- A creator answer to "who is 'our'?" (msg 20226), or to which "choice" is meant.
- A hit from U1-U5 that satisfies the exact-hit rule.
- Otherwise, the rows stay as they are: dense negative coverage on M1, and M2 / M4 blocked
  downstream of M3 and M5.
