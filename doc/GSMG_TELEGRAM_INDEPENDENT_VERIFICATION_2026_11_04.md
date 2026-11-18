# Telegram independent verification — 2026-11-04

The previous review's central result holds: this export supplies **no newly
verified puzzle opening and no new post from the creator account**. Its saved
315-material checker result reproduces exactly. Additional finite checks are
negative. However, its claims of exhaustive candidate coverage and its dismissal
of J's undisclosed opening were too strong; those statements have been corrected.

This review reads the actual November export and attachments, independently
reconstructs the relevant bytes and structures, and checks the prior analysis.
No downloaded Python, HTML, or document-contained code was executed.

## Inputs and reproducibility

- Export: `/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-11-04/result.json`.
- SHA-256: `eaf63cfe31a48bb243b2f85683408b84686a91c56f8f6de952215b1a0bb6a0b3`.
- Comparator: October 7 export, SHA-256
  `cde17d9b67e88e174a9472331bb46cb159e5d8618bb6d08a6e0aeea7c51ea58f`.
- [Scope frozen before supplemental oracle results](Brainstorms/2026-11-04%20-%20Telegram%20Independent%20Verification%20Scope.md).
- [Verifier](../tools/gsmg/telegram_2026_11_04_independent_verify.py) and
  [machine-readable result](../tools/gsmg/telegram_2026_11_04_independent_result.json).
- [Previous review, with corrections](GSMG_TELEGRAM_UPDATE_REVIEW_2026_11_04.md).

The result retains attachment hashes, message IDs, full overlap-field changes,
the supplemental registry/results, structural witnesses, PDF-entry index, and
the independently queried chain state. Working extracts and source comparisons
are under `_work/telegram_2026_11_04_verification/`.

## Coverage verified

| Check | Result |
| --- | --- |
| Export identity | GSMG Puzzle Solvers, group `1166734859`; exact expected hash |
| Total rows | 2,828 |
| New since max ID 75648 | 2,777: 2,641 messages and 136 service events |
| Actual first/last new rows | 75651, October 7 13:17:56; 78805, November 4 10:58:33, as displayed in the export |
| New photos | 112, reviewed on all 13 existing contact sheets |
| File-bearing rows | 19 documents, five audio files, seven videos, 67 animations, 52 stickers |
| Referenced media | All locally available; hashes recorded |
| Creator account `user9815232` | Zero messages in this export |
| Text overlap | All 51 overlapping texts identical |
| Full message overlap | Five objects differ: reactions, display name, edit timestamps, or export-local media paths |

The earlier `75649–78805` description was the logical ID window after the old
maximum, not the actual first available row. IDs 75649 and 75650 are absent.
The five changed objects are 75611, 75614, 75627, 75646, and 75648. Their texts
are unchanged. This does not provide the contents or causes of absent/deleted
messages, nor prove there were no creator communications elsewhere.

All messages were machine-indexed. The manual pass reviewed the substantive
long messages, candidate-bearing short messages and their reply context,
the 112-photo contact sheets, text/code attachments and both Word containers.
This is not a frame-by-frame review of every video/animation or a listening
audit of every audio file.

## Old result replay and additional tests

The original checker contains 21 registered strings, each expanded to 15 forms:
raw text, SHA-256 digest, lower/upper SHA-256 hex, and SHA-256 of the hex,
each without newline, with LF, and with CRLF. Its full output, including
WIF/address checks, **matches the saved JSON exactly**.

Its coverage is finite. In particular, posted WIFs had been tested as private
keys but not as password text, even where a poster called one the level-3
password. Two long posted strings and a quoted ASCII result were also absent
from that registry.

The supplemental set was frozen before testing:

| Source | Exact additional material |
| --- | --- |
| 76367 | Quoted `2iyGJ!4@?uebzY` |
| 77024 | Complete 104-character uppercase post, unchanged |
| 77045 | Complete mixed-case/digit post, unchanged |
| 77049 | `Wh 173 R4b B17` and its space-free rendering |
| 76333 | The posted 12-word zoo/winner mnemonic, unchanged |
| 77069, 77071, 77253, 77646 | All four distinct password/WIF-shaped strings as literal password text, including malformed WIFs |
| 76360 | The known first-chain-key WIF as an additional password control |

Results:

- **11 registered strings / 165 forms**, zero accepted CBC, stream, ECB,
  key-wrap, raw-digest-key, or target-address hits over the four tracked blobs.
- All 165 supplemental materials are distinct within this set. Rabbit and
  RabbitLegacy × MD5/SHA-256 × four blobs: **2,640 attempts**, zero hits at
  the existing 64/80 printable screen and zero weak rows at 56/80.
- The three valid posted WIF scalars have no direct raw-key hit and no target
  address match. Invalid WIFs were retained as password text; checksum failure
  alone would not justify rejecting that separate use.
- Four claimed level-3 password strings × 15 forms were also checked against
  the **three solved encrypted stages**, with zero accepted outputs. Each
  actual solved-stage password first passed its positive control.
- The zoo/winner mnemonic fails its BIP39 checksum, independently confirming
  the poster's own observation. Its literal text was still included above.

These are negative results for exactly those materials, derivations, consumers,
and acceptance screens. They do not exclude every binary output format, cipher,
or interpretation. The original registry's phrase “every concrete string” has
been removed. No new typo repair or open-ended word search was performed.

## Important correction: J's undisclosed opening

[Message 78605](https://t.me/c/1166734859/78605), November 3, says its
SalPhaseIon AES output has a prime number of bytes and promises a follow-up.
It supplies **no actual length, password, KDF, plaintext, or validation**.

For the known 80-byte ciphertext under AES-CBC with strict PKCS#7, plaintext
length is 64–79 bytes. The prime possibilities are:

| Plaintext bytes | Required padding bytes |
| ---: | ---: |
| 67 | 13 |
| 71 | 9 |
| 73 | 7 |
| 79 | 1 |

The previous review assumed 79 without evidence. That was incorrect. A long
padding match would need a different statistical assessment, including how
the password was selected; it still would not establish intended meaning
by itself. Conversely, 79 bytes alone would be weak evidence.

**Disposition: unverified and worth checking if the promised public details
arrive.** Pawel's separate experiment on token combinations does not test J's
undisclosed password. No message was sent to J or anyone else.

Draikoon's closing-phone-speech claim is also undisclosed. The posted quote
cannot itself fill the 1,312–1,327 plaintext bytes implied by the full Cosmic
AES-CBC ciphertext, but the poster alleges another layer. Without the actual
password/output, that allegation cannot be reproduced or rejected solely from
the quote's length. It is not a verified Cosmic opening.

## Attachment verification and errors worth retaining

### Canonical artifacts are unchanged

- `CosmicDuality.txt` decodes to our exact Cosmic envelope.
- `live_salphaseion.txt` has 1,075 logical symbols, exact DBBI/FAED slices,
  and the same reassembled SALPH envelope.
- `phase3.2-monologue-corrected.txt` has the **same 1,539 letters** as a fresh
  codec/Beaufort replay from the native solved plaintext. Its spacing is a
  community reconstruction; it introduces no new authored letters. Word-count
  claims such as 255/256 therefore require an explicitly chosen spacing rule.
- `puzzlepiece.mp3` is byte-identical to the existing Decentraland audio.
- `cosmic-duality_compress.pdf` is byte-identical to the book PDF in the
  October 7 export. It is not a newly discovered book variant.

### The alleged verified Cosmic plaintext is the known arbitrary body

`cosmic_decrypted_verified.bin` is exactly the 1,327-byte `4f7a1e4e…c081`
body already replayed in the Naddiseo review: 40.2% printable with whitespace,
empirical entropy 7.870 bits/byte, and a one-byte pad in that construction.
Its filename supplies no new authentication.

I rebuilt the posted issue-110 address recipe independently:
take bytes 16–31 of each of the first 39 32-byte blocks, append the block
index as four big-endian bytes, and Base58Check-encode that payload with
version zero. The result **exactly reproduces `cosmic_correct_12addrs.txt`**.
Despite the filename, that file contains **39** concatenated addresses. None
is a tracked target. Constructing checksum-valid addresses this way is
automatic and does not validate the underlying plaintext or address recipe.

### The deep-analysis attachment overstates Bifid constraints

Message 76144's markdown says every keyworded Bifid square confines A–I to
the first two rows and therefore only a hand-placed square could avoid that.
This is false as a universal statement. Under the already-established keyword
`THEMATRIXHASYOU`, zero-based rows for B/C/D are 2 and for F/G are 3.

Confinement holds for squares whose initial cells specifically contain all
nine source symbols, including the DBBI-derived square. It does not hold for
arbitrary keywords. This corrects the attachment's claimed exclusion; it is
not a new keyword search or positive Bifid lead.

The same attachment promotes the chain's derived 15-byte `E_S` into a
120-bit validation target and demands a short phrase hashing to it. No source
establishes that hash relationship. A tail is 120 bits long without being an
independently specified 120-bit checksum. The mechanically reproduced chain
does not license that additional assumption.

### The knight-walk code has a structural impossibility

`knight_walk.py` requires an injective mapping from stream symbols to eight
knight moves. Every declared DBBI/FAED slice still contains **nine distinct
symbols**, including the proposed skipped-prefix variants. The injection
cannot exist, independently of the start cell, board orientation, or DFS
budget. The so-called spare letter is not removed from those input slices.

`knight_walkV2.docx` contains only a multiprocessing wrapper around that DFS;
it does not fix this contradiction. No downloaded search was run. This closes
the literal posted model, not different coordinate, stay-put, or variable-code
models for which the attachment supplies no selected construction.

`UTXO.docx` contains HTML dashboard source. Its displayed signed transaction
comes from a `mockElectrumSignedHex` string, with a fixed average input value;
it does not contain a demonstrated puzzle decryption or actual signing result.

## The large PDF is an archive of attempts

Message 76813's `gsmgio_json.pdf` has **25,442 pages** and **238 named JSON
entries**. I extracted and indexed every entry and inspected relevant result,
scope, source, and integrity summaries. Representative scope pages 883–884
were also rendered and visually checked. The result retains each entry's
name, page, extracted size, and parse status.

Only 30 entries parse directly as JSON after removing page breaks. Many other
entries have layout-induced wraps inside strings; I did not silently repair
them or infer corruption of their original source files from extraction errors.
The PDF is a printed archive, not a complete executable reproduction package.

The inspected summaries report bounded negatives, not a new opening:

- `cipher_catalogue_23_16_7_audit.json` explicitly limits itself to its fixed
  Beaufort/VIC/chess-hint family and reports no legible/prize hits.
- `matrixsumlist_audit.json` and `matrixsumlist_instruction_audit.json` describe
  finite list/reduction families; they do not show every use of a sum list
  has been tested.
- `s570_seven_matrix_fold_audit.json` limits its negative to a declared
  seven-block fold/weave family and explicitly excludes transpositions.
- `universal_regate.json` reports testing a finite inventory of scalar-shaped
  tokens. Its title does not make that inventory exhaustive over constructions.
- Integrity assertions and positive controls are useful claimed evidence,
  but this verification did not independently rerun those hundreds of files.

Messages 78536–78537 extrapolate from such negative searches to a required
private personal secret. That conclusion does not follow from the tested
families or from the creator's friends remark. This export supplies no new
creator reply selecting that interpretation. The existing source-derived
transposition gaps remain open.

## Image and homepage claims

The three native QR finder crops remain byte-identical, reproducing an
existing local result. New chat renderings and bit-grid transcriptions do
not independently establish a hidden third door; the native texture already
has dedicated local audits. This check does not claim to have identified the
original renderer or exhausted all possible interpretations.

Messages 76711 and 76348 discuss `#fefefe`, `carrier anomaly`, and `finalGrid`
in the homepage code. I fetched the current homepage and the preserved
August 19 capture copy in rejected PR #15. Both are **35,785 identical bytes**,
SHA-256 `2f896807a859e2f71a2f6e1e8277986af73b80dc0dd79a685a67c7f7f8c3303b`.
Those markers are not new October site changes. Equality to that saved copy
does not independently establish who authored or currently operates the wrapper.
The old `little bunny hunter` comment is also already present in the local
Phase-1 HTML; it supplies no demonstrated Terraria connection.

## Prize-state claim independently checked

The two public APIs agree on **125,649,674 confirmed satoshis** at the prize
address at retrieval time. The 125,324,300-satoshi output from April 24, 2024
remains in the UTXO set. Thus the chat claims of a zero balance or completed
sweep are contradicted by current chain state.
[Mempool address API](https://mempool.space/api/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe),
[Blockstream address API](https://blockstream.info/api/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe),
[Blockstream UTXO API](https://blockstream.info/api/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe/utxo).

The complete responses and UTC retrieval timestamp are saved in the result.
An unspent prize does not prove that nobody privately knows a solution; it
does refute the specific assertion that this output has already been swept.

## Effect on priorities

No newly disclosed recipe here warrants promoting another brute-force campaign.
The useful follow-up is J's promised exact recipe if it becomes public. The
large archive may save duplicated bounded searches, but it does not close
the separately documented DBBI-derived column-order experiments. There is no
basis in this export to abandon those tests for a required private secret.

Reproduce all local checks:

```bash
python3 tools/gsmg/telegram_2026_11_04_independent_verify.py
```

The old and supplemental oracle runs completed before a missing solved-stage
file path stopped the first verification run. The path was corrected to the
canonical archived HTML; the completed oracle JSON was equality/registry
checked and reused, then the three solved-stage controls and remaining tests
completed. `--reuse-completed-oracles` exposes that exact resume behavior.
The original checker and its saved result were not modified.
