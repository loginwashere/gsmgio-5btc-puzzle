# Naddiseo repository full audit

Date: 2026-08-24  
Source: `https://github.com/Naddiseo/gsmgio-5btc-puzzle`  
Frozen commit: `15b43fc859c33170d7c45b9fe41789d77b7af974`  
Frozen tree: `0cd1e900038246a4ff3f1b5817f34fa212c49d92`

## Result

The repository has now been checked manifest-completely, not merely sampled or
covered by topic. All **85 tracked files** at the frozen commit were read and
classified. All seven notebooks were inspected cell by cell, all saved outputs
were read, all 32 embedded notebook attachments were decoded, and all 66 images
were visually inspected and checked at the container/metadata level.

This pass found **no new puzzle clue, password, operator, or transition** beyond
the evidence already represented in this project. It does strengthen the
negative statement: there is no overlooked notebook cell, saved error, orphaned
attachment, image trailer, or obvious metadata payload in this upstream tree.

The machine-readable 85-file ledger is
[`doc/evidence/NADDISEO_REPOSITORY_FULL_AUDIT.json`](evidence/NADDISEO_REPOSITORY_FULL_AUDIT.json).
The reproducer is
[`tools/gsmg/naddiseo_repository_full_audit.py`](../tools/gsmg/naddiseo_repository_full_audit.py).

## Coverage accounting

| Class | Files | Review performed |
| --- | ---: | --- |
| Hint images | 34 | Original-resolution visual review, authorship context, digest, metadata, file boundary |
| Other walkthrough images | 32 | Original-resolution visual review, digest, metadata, file boundary, notebook-attachment comparison |
| Notebooks | 7 | Every markdown/code cell, saved output, attachment, dependency, and side effect |
| Text / Markdown | 7 | Full text, relationships between ciphertext/plaintext/notebook output, digest |
| Encrypted text payloads | 3 | Base64 envelope, digest, safe replay where the password is solved |
| Audio | 1 | Codec/stream metadata, channel-difference spectrogram, digest |
| Placeholder | 1 | Empty tracked `.gitkeep`, presence and digest |
| **Total** | **85** | **Every tracked path has a `reviewed` ledger row** |

There are no duplicate standalone tracked blobs by SHA-256. The 32 images
embedded in notebook markdown all have byte-exact standalone matches; there are
no missing or mismatched notebook attachments.

## Notebook review

| Notebook | Code | Markdown | Saved outputs | Attachments | Disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| `decentraland.ipynb` | 5 | 6 | 5 | 3 | Stereo difference reproduces the visible hex rail `48 41 53 48 54 48 45 54 45 58 54`, or `HASHTHETEXT`. |
| `phase0.ipynb` | 3 | 5 | 3 | 0 | Spiral/color transform reproduces `gsmg.io/theseedisplanted` followed by a terminal NUL from the final four-bit fragment. |
| `phase1.ipynb` | 1 | 2 | 1 | 3 | Historical live form-submission helper; source and saved output reviewed, network cell deliberately not rerun. |
| `phase2.ipynb` | 3 | 10 | 3 | 14 | Both solved decryptions reproduce the checked-in Phase 2.1 and Phase 3 plaintext bytes exactly. |
| `phase3.ipynb` | 1 | 7 | 1 | 4 | Solved decryption reproduces `phase3.2.txt` byte-for-byte. |
| `phase3.2.ipynb` | 7 | 13 | 7 | 7 | High-byte extraction, frequency experiments, codec scan, CP1141 text, and Beaufort work fully reviewed. The `ebcdic` package is an external dependency, so that historical codec-discovery cell was not executed in the audit environment. |
| `salphaseion.ipynb` | 6 | 8 | 7 | 1 | Reproduces `matrixsumlist`, `enter`, `lastwordsbeforearchichoice`, and `thispassword`; the notebook still stops before decoding DBBI/FAED. |
| **Total** | **26** | **51** | **27** | **32** | No saved exception outputs and no hidden extra cells. |

### Execution hazards found

These are code-review findings, not puzzle evidence:

- `phase1.ipynb` initializes `tries = 0` but never increments it. A connection
  failure or HTTP 520 can therefore retry forever.
- The same cell tests a text literal against `resp.content`, which is bytes in
  `requests`; that branch can raise a type error. It also tests text membership
  against the `Response` object rather than explicit response text.
- The Phase 2 and Phase 3 decrypt helpers open their destination plaintext with
  `w+` before OpenSSL success is known. A wrong password can truncate an existing
  plaintext. The audit therefore captured OpenSSL stdout in memory and never ran
  those notebook cells in place.
- `decentraland.ipynb` writes `(-1**i) * x`. Python precedence makes this `-x`
  for every sample, not an alternating sign. That is consistent with the cell's
  stated goal of inverting one complete channel, but the expression is misleading.

## Deterministic replay

The following operations were independently rerun without mutating the upstream
clone:

- Phase 0 spiral/color decoding: exact expected URL plus the saved terminal NUL.
- SalPhaseIon binary and decimal-to-hex islands: all four saved strings matched.
- Phase 2 AES with the SHA-256 of `causality`: plaintext SHA-256
  `e2f9dd65604a3231f8b3301724e8d713a88fffc4b6c7c4aeeb20f58a582b593a`.
- Phase 3 AES with the notebook's seven-part password: plaintext SHA-256
  `c4ad94559a44a927c1032cc0e024515f9510a0806a2d14458dbf4a360af9865f`.
- Phase 3.2 AES with the Jacque Fresco / one-second / uncertainty-principle
  password: plaintext SHA-256
  `b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34`.
- Decentraland MP3: MP3, 44.1 kHz, stereo, about 5.20 seconds; subtracting the
  right channel from the left visibly reproduces the notebook's hex message.

The Phase 1 POST loop was not rerun because it is network-active, historically
targeted a live verification endpoint, and is unnecessary to validate its saved
result. The CP1141 discovery cell was not rerun because its third-party `ebcdic`
module is absent; its source, saved ranking, saved decoded text, and downstream
Beaufort screenshots were all inspected.

## Hint and media review

All 34 files under `hints/` were opened at original resolution. The review
confirmed the already-documented themes: the colored-number poem, Decentraland,
the additional door, prime-number/zeroing guidance, SalPhaseIon hashing,
reverse-binary guidance, yin-yang language, the Cosmic Duality book, halvings,
and the 2026 messages. None adds text that is missing from the current project
documentation.

All 32 other walkthrough images were also opened. They document the known route:
phase-source/form details, Google-query derivations, SafeNet/Luna/HSM and chess
components, Matrix dialogue, CP1141/Beaufort work, and the SalPhaseIon/Cosmic
page. No related block, annotation, or screenshot-only string was found beyond
the walkthrough narrative.

Container checks found 65 PNGs and one JPEG, all valid. Every PNG ends at its
`IEND` chunk and the JPEG ends at its EOI marker; **zero files have trailing
bytes**. Metadata consists of ordinary screenshot timestamps/software, DPI,
gamma/sRGB/ICC data, and one `Created with GIMP` comment. No metadata value is a
puzzle payload.

Authorship remains an important boundary. Several screenshots reproduce
community or deleted-account messages, and screenshot capture metadata is often
from 2023 rather than the date named in the filename. The repository's filename
and “official” labels are therefore secondary community curation, not standalone
proof of creator authorship or original posting date. This audit preserves the
message content but does not promote those labels into primary evidence.

## Unverified material

The `unverified/` directory contains only its README, an empty `.gitkeep`, a
sample placeholder attempt, and the already-known `yourlife[1141:]` hypothesis.
The latter reports no AES hit. There are no notebooks, generated results, or
additional candidate files hidden in that directory.

## Effect on live gaps

No gap closes and no new attack is promoted:

- DBBI/FAED remains undecoded in the upstream notebook as well as here.
- No DBBI/FAED operator is selected.
- `matrixsumlist`, `lastwordsbeforearchichoice`, and `thispassword` are decoded
  labels/instructions, but the upstream code supplies no missing binding rule.
- The prime, repeated-block, and letter-frequency observations receive no new
  creator-authenticated selector from the repository.

The strongest conclusion is coverage, not a new solve: the full current
Naddiseo tree has now been exhausted as a source of overlooked local evidence.

## Reproduction

From this project, against a checkout at the pinned commit:

```bash
python3 tools/gsmg/naddiseo_repository_full_audit.py \
  --repo /path/to/Naddiseo/gsmgio-5btc-puzzle
```

Expected summary:

```text
PASS: 85 files; 7 notebooks; 66 images; 32 exact notebook attachments; deterministic replays matched
```

Use `--json` to regenerate the complete ledger. The script rejects a different
commit, tree, or tracked-file count so that later upstream changes cannot be
silently mistaken for this frozen audit.
