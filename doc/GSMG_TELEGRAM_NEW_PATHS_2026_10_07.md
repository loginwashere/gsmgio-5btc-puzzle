# Telegram new paths and structural checks — 2026-10-07

The export adds several solver hypotheses, but no authenticated creator post
or independently verified endgame decryption. The most useful additions are
a concrete DBBI mirror recipe, an independently reproducible five-byte
padding claim, and a possible missing Rabbit cipher check. The mirrors do
not become strong evidence under prime-scaffold controls. The padding claim
deserves a provenance question about its suffix, rather than being counted
as either a solve or an ordinary one-byte padding hit.

This supplements the [export review](GSMG_TELEGRAM_UPDATE_REVIEW_2026_10_07.md)
with structural replays, source checks and a prioritized follow-up list.

## Coverage

Source: `/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-10-07/result.json`.
SHA-256: `cde17d9b67e88e174a9472331bb46cb159e5d8618bb6d08a6e0aeea7c51ea58f`.
Group verified: `GSMG Puzzle Solvers`, id `1166734859`.

Compared with the September 28 export's maximum id 73868:

- 1,481 new rows, ids 73869–75648: 1,442 messages and 39 service events;
- dates September 28, 17:12:21 through October 7, 10:27:09, as recorded by Telegram;
- zero new messages from known creator account `user9815232`;
- 36 overlapping rows; six records differ, but no overlapping message text differs;
- 42 photo attachment records and 55 file attachment records, all locally available.

All new message text was reviewed in context. All 42 photo records were
inspected on contact sheets, with readable diagrams checked against their
claimed constructions. Three text/code attachments were read without
execution. The attached book PDF was identified by its digest. Other file
records are animations/stickers: their metadata and posting contexts were
reviewed, not every frame. Deleted or private messages outside this export
remain unavailable. A solver's statement that Jrk posted seven days earlier
does not establish a new post in this group.

Extraction, overlap differences, media inventory and results are retained in
[_work/telegram_2026_10_07](../_work/telegram_2026_10_07/summary.json).
The existing analysis files were retained.

## 1. DBBI mirrors: reproducible, substantially explained by the scaffold

Flo Sku's 74731/75455 diagrams duplicate the seven-row, thirteen-column DBBI
rectangle. The two pictured horizontal axes are rows 2 and 4, zero-based.
They align with `THEPRIVATEKEY` and `ANDBETTERHALF` in the similarly wrapped
solved Stage-3.2.2 answer. Duplication repeats the evidence; it adds no
independent symbols or comparisons.

For each pictured axis, compare matching columns in the two row pairs on
either side. Include the other eligible five-row window, centered on row 3,
to avoid comparing only the selected centers. Each axis has 26 comparisons.

| Center, zero-based | Equal symbols | Aligned solved-answer row |
|---|---:|---|
| 2 | 11 / 26 | `THEPRIVATEKEY` |
| 3 | 3 / 26 | `SBELONGTOHALF` |
| 4 | 6 / 26 | `ANDBETTERHALF` |

These are partial equalities, not complete reflection symmetries. The
family statistic is the sum of the two largest counts, here **17**. Under
9,999 controls per model:

| Null model | Add-one fraction with statistic ≥17 | Mean | Maximum |
|---|---:|---:|---:|
| Shuffle all 91 symbols, preserving their histogram | 0.0028 | 9.31 | 20 |
| Shuffle only residual symbols; preserve 83-token prime hosts | 0.0678 | 13.61 | 22 |
| Shuffle only residual symbols; preserve 84-token prime hosts | 0.0726 | 13.68 | 23 |

The raw shuffle makes this look unusually strong. Preserving the already
established host positions and widths changes that conclusion. The actual
pair lies around the upper seven percent of these conditional controls,
and stronger witnesses exist in both models. These are exploratory tail
fractions for a declared small family, not original discovery p-values.
They do not account for every layout, radius or visual pattern that might
have been inspected before publication.

Including the omitted third pair cyclically gives only 15/39 and 11/39 at
the two pictured centers. The diagram's apparent strength partly depends
on leaving two rows unused. This does not invalidate the word alignment;
it limits the evidence for a new intended mirror operation.

The [protocol](Brainstorms/2026-10-07%20-%20Telegram%20DBBI%20Mirror%20Replay%20Protocol.md)
was fixed before counting. Planted controls, an independent pair-enumeration
check, histogram preservation and host retention passed. No password
oracle was used. [Replay script](../tools/gsmg/telegram_2026_10_07_structural_replay.py),
[full results](../_work/telegram_2026_10_07/structural_replay.json).

**Disposition:** retain the diagram as a concrete solver construction; do
not reopen broad mirror/XOR searches on visual strength alone. A specified
consumer or a prediction beyond the two already-visible phrases would
make a different follow-up possible.

## 2. BTCSEED indices and the undisclosed ten-character result

Boulayo supplies 18 indices in message 75172:

```text
51 49 43 45 32 50 36 12 44 14 40 34 41 43 20 30 56 52
```

Applying them to the established full-period Bifid decode, with square
`DBIFHCEGAKLMNOPQRSTUVWXYZ`, gives complete outputs:

```text
zero-based: DEIIBBCCCECCRICDDD
one-based:  BEDCVEPMIKHXCDSKND
```

Neither is a readable instruction. The post does not specify a second
operation or index convention, so these are bounded extraction checks,
not a rejection of an undisclosed method.

Messages 75244/75265/75267 claim ten contiguous meaningful characters in
the first quarter, excluding the first ten characters. No exact output,
start position or recipe is disclosed. This cannot currently be replayed.
Track it as a request for a complete construction; do not invent a
transform to fit the claimed length.

## 3. Five-byte padding: the claim is real; its provenance is unresolved

Message 74719 proposes the lowercase SHA-256 hex of
`followthewhiterabbit`, followed by `adipfBrr`, as a Cosmic passphrase.
Independent AES-256-CBC replay under the legacy SHA-256 KDF reproduces
five bytes `05 05 05 05 05`. The decrypted bytes have a printable fraction
of 0.386 and no demonstrated readable or exact structural payload. MD5
and the uppercase-hash alternatives do not reproduce the padding.

For one independently chosen wrong key, this exact padding has probability
2^-40. It is therefore different from the much more common one-byte pad.
However, the suffix's derivation and search history are not supplied. An
eight-letter mixed-case search has 52^8 possible suffixes, which is ample
room to mine such a padding event. That is a possible explanation, not a
verified account of what the poster did. The poster also describes it as
probably noise.

**Useful next question for the public record:** was `adipfBrr` derived from
an independently named puzzle artifact, or optimized against the ciphertext?
An independently sourced derivation would justify examining the full
plaintext structure. Padding alone supplies no partial-progress score
for password edits. No new suffix search was run.

[Independent padding/source replay](../_work/telegram_2026_10_07/source_and_padding_replay.json).

## 4. Rabbit/CryptoJS: a new compatibility hypothesis, with weak selection

Photo 75068 shows Rabbit selected in a community cipher-tool menu. This
is not creator evidence. It nevertheless identifies a concrete algorithm
worth comparing with our cipher coverage: Rabbit uses a 128-bit key and
64-bit IV, and CryptoJS exposes passphrase-based Rabbit encryption under
its shared OpenSSL-style formatter. The `Salted__` prefix alone therefore
cannot distinguish AES from every other compatible cipher.
[RFC 4503](https://www.rfc-editor.org/info/rfc4503/),
[CryptoJS documentation](https://cryptojs.gitbook.io/docs).

CryptoJS's shared default EVP derivation uses MD5 with one iteration;
the source separates this derivation from the chosen cipher. These facts
make a Rabbit compatibility test technically well defined, without
establishing that GSMG used it.
[KDF implementation](https://raw.githubusercontent.com/brix/crypto-js/develop/src/evpkdf.js),
[formatter and passphrase implementation](https://raw.githubusercontent.com/brix/crypto-js/develop/src/cipher-core.js).

The existing solved-blob AES/SHA-256 precedent weighs against this change.
Repository search and the [current export review](GSMG_TELEGRAM_UPDATE_REVIEW_2026_10_07.md)
identify no existing Rabbit oracle. This audit did not implement or run one.
A sensible bounded follow-up would validate an implementation with the RFC
vectors and an independently generated CryptoJS fixture, then replay a
fixed existing candidate set with MD5 and SHA-256 derivations. Require
readable instructions or an exact independently selected payload grammar:
Rabbit has no PKCS#7 padding signal. Keep URLBLOB's quarantine separate.

## 5. Source corrections that affect which paths deserve attention

**The new book PDF is old material.** The attachment at 75518 is
byte-identical to the July full-book PDF. Both SHA-256 digests are
`38e28dbd72976ef17c5d4ffdafe4475689f47300da5e2c98e0cb77b578547b04`.
The page-119 flower discussion and yin/yang seed imagery are thematic
readings of an already available source, not newly recovered pages.

**The public map incorrectly retires a genuine instruction.** Marc's map
at 75550 attributes `fourfirsthintisyourlastcommand` to community OP_RETURN
material. Our authenticated SalPhaseIon segmentation independently
reproduces the native hash-prefix instruction at normalized positions
860–895. Copies on-chain cannot remove its page provenance. Preserve that
instruction in the source-consumption work.
[Operand-binding audit](../tools/gsmg/findings/P00101.md).

**MELT MY SECONDANSWER uses an assembled list.** Message 75476 moves
`enter` near the start, repeats `matrixsumlist`, and expands unresolved
`anstoo` to `secondanswer`. Native page order instead puts `enter` between
the two 64-character AES portions, positions 959–999 in the normalized
stream. There is only one `matrixsumlist` segment. The assembled acrostic
cannot select a native operation without an independently sourced rule
for those changes. Base64 line wrapping itself does not insert an extra
ciphertext byte.

**The linked SOLVED issue is an older claim.** Issue 69 was opened in
December 2025. Its seven-token SHA-256/XOR recipe does reproduce the
posted `818af53d…` value; the repeated `matrixsumlist` cancels in the XOR.
That arithmetic does not reproduce a claimed Cosmic plaintext, fix an
IV, or validate a dusting mechanism. The reported half/better-half text
already exists in the solved Stage-3.2.2 answer. No independently
replayable new endgame opening follows from this link.
[Issue 69](https://github.com/puzzlehunt/gsmgio-5btc-puzzle/issues/69).

**Historical creator citations remain historical.** Original message
32719 is the 2024 remark about staying alive until 2145; interpreting it
as a port number is a solver addition. Original 66559 discusses the
puzzle's origin; 66600 is a reply concerning the broader claimed prize.
The new thread's alter-ego, race-condition and automated-trigger readings
are not explicit operations in those messages.

## Remaining claims and follow-up priority

| Thread / messages | What is new | What would make it executable |
|---|---|---|
| Prime shifts → `FILM` / `A Clue Way`, 73948, 75255–75258 | Repeated solver output claims | Exact input, shifts, indexing and complete output; currently undisclosed |
| 35 `+-` blocks, invalid curve x values “one off”, 74001–74002 | Numeric claim with an uncertain count | The 35 exact blocks, their authenticated decryption, and selected ± rule; none supplied here |
| Inverted logo / FEFE complement, 74004–74005, 74059 | Solver interpretation | Historical asset comparison and a bound consumer; present site appearance cannot alone select intent |
| SYSTEM FAILURE “same bytes as Genesis image”, 74007 | Exact-sounding identity claim | Named images, digests and definition of equality; screenshot/text gives no byte comparison |
| Jaden Smith / zero `i`, 74914–74916 | A mechanically possible zeroing instruction | Independently selected values, layout and output consumer; dimensions and name length are associations |
| DBBI starts with 422 and sums to 422, 74498 | Exact arithmetic, independently reproduced | A sourced consumer for 422; the identity itself supplies no transform |
| ANDOR / Stardust, 75070 | New solver thematic association | Provenance selecting the film/term beyond `and/or`; the existing Phase 444 audit covers a different, explicit rail family |
| Chess / `oneforonefourforone`, 75378–75406 | Reinterpretation of known board and CP1141 clue | A distinct, fully specified extraction; guesses about password order do not overturn the solved encoding precedent |
| ESLJAPKMEDAKL, 75411 | A bare proposed key | Exact derivation and purported plaintext; not independently verified by this structural audit |
| Testnet dialogue, 75249–75278 | Rediscovered community chain messages | Creator-authenticated connection; new thread itself challenges the attribution |
| SalPhaseIon / Cosmic openings, 74525–74541, 74724–74802, 75029–75054 | Claims, some explicitly retracted | Full bytes, password/KDF, derivation and independent plaintext validator |
| Community game/CTF links and bots, 75321–75350, 75561 onward | New community activity | No authenticated puzzle connection established; bot commands and lore are not puzzle instructions |

For the `+-` claim, curve membership by itself is a weak discriminator:
about half of arbitrary field x values admit a secp256k1 point, as already
accounted for in [Phase 338](../tools/gsmg/findings/P00338.md). “A neighboring
value works” is not enough to select a correction algorithm.

Priority is to obtain the complete published recipes for `FILM` and the
ten-character BTCSEED claim, establish the padding suffix's provenance,
and consider a bounded Rabbit compatibility test. None requires reviving
unbounded color permutations, arbitrary matrix transforms or key searches.
The [FEFE control-event result](GSMG_FEFE_CONTROL_EVENT_INVESTIGATION_2026_09_30.md)
and [existing solve routes](GSMG_NEXT_SOLVE_ROUTES_2026_09_29.md) remain the
more firmly specified internal experiments. This review sends no messages,
changes no live site state and makes no transaction.

Reproduce the structural checks:

```bash
python3 tools/gsmg/telegram_2026_10_07_structural_replay.py
```
