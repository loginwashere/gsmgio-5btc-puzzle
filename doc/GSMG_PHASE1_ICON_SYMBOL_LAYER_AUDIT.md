# Phase-1 icon symbol-layer audit

Date: 2026-08-13  
Script: `tools/gsmg/phase1_icon_symbol_layer_audit.py`

## Result

The extra symbols are meaningful, but the evidence supports an
**instruction/confirmation layer**, not a second recoverable password.

The creator-authored PNGs contain three natural contrasts:

| Left motif | Right motif | Relation |
|---|---|---|
| closed lock | open lock | opposite states |
| `+` | `-` | opposite signs |
| banking | crypto | traditional/cryptocurrency contrast |

The blue/red division adds the familiar visual language of two magnetic
poles. Together these motifs illustrate the song's Phase-One line, “the seed
is planted when opposites attract,” and cue the solver to bring fragments from
the two sides together.

They do not define another complete textual matching. The word solution pairs
`WAR` with `N/ING` and `LO` with `CRYPTO/GIC`, while the semantic-symbol pairs
are banking/crypto and closed/open lock. In other words, those first two
symbol pairs are crossed to produce `WARNING` and `CRYPTOLOGIC`; pairing the
icons only by their visual semantics leaves broken text. The `+/-` cards do
agree with the `DIG I` + `T` word pairing, but that supplies no additional
character or ordering rule. No creator-authored operation selects a residual
string after the known song/artist/prompt are removed.

## Artifact and provenance boundary

The supplied JPEG is Telegram export message `670`:

```text
photos/photo_15@08-05-2019_17-54-34.jpg
189x323
sha256 8d0f0e9346d78f39da0e5a2d2fb0b84394ede34d965468e8d9bb2c165e7db16e
```

It is a community reconstruction by Alex, not an original page image. Message
`672` says “Here with borders,” and `673` says “Not sure if the sequence is
right ..”. Therefore its black borders, gaps, four rows, and row order cannot
select a second decode. The eight underlying PNGs are authentic: the archived
HTML lists the four black/blue files followed by the four red files, without a
creator-defined 4x2 pairing layout.

The same question arose contemporaneously. Message `685` explicitly calls out
banking, crypto, `+/-`, and the locks as apparently unused. In a later replay
of the question, message `8909` connects plus/minus to “opposites attract,” and
message `8914` reads `+/-` and red/blue as magnet poles. These are community
interpretations, not creator confirmation, but they predate this audit and fit
the authentic symbol inventory without adding an arbitrary transform.

## Image-forensic checks

The original files are only 506–1,642 bytes. Two are RGB and six are RGBA, but
every alpha sample in all six RGBA files is exactly `255`: the nominal alpha
channels contain zero transparent or partly transparent pixels. This directly
rejects a historical speculation that differing alpha-channel presence hides
a second layer.

The flat blue and red are `#3F48CC` and `#ED1C24`, ordinary MS Paint palette
colors. They are not RGB complements (`255-blue = #C0B733`, not red), and their
hues are about 122 degrees apart rather than 180. The magnet-pole reading is
therefore semantic/iconographic, not a selected numerical color operation.
Phase 71's prior container, LSB, white-overlap, and band-width negatives remain
unchanged.

## Bounded candidate check

The current V2 registry contains `theseedisplanted`, but none of the 16 exact
lyric/symbol readings in this audit. That is a registry-scope observation, not
evidence for a missing password: most are names for an already-consumed clue.
To avoid leaving a real oracle-coverage ambiguity, the audit tested only:

```text
opposites attract
the seed is planted when opposites attract
plus minus
red blue
closed open
lock unlock
locked unlocked
closed lock open lock
bank crypto
banking crypto
magnet
magnetic
magnetism
polarity
positive negative
north south
```

Standard answer/case/joined/newline handling produced 504 unique passphrases
(candidate digest `11a7607d7b59242a`). Against SALPH, COSMIC, P32TRAILING, and
URLBLOB, the complete current CBC/ECB/stream/Key-Wrap menu performed 282,240
effective operations: **zero hits**. A separate literal raw-key check made 220
attempts: **zero hits**.

## Verdict

Promote the symbol layer to **positive interpretive evidence** for
“opposites attract” and for joining the two color groups. Do not promote it to
a second key, hidden-image payload, row-order selector, or numerical color
route. The most defensible new word is `magnet`, but it is an explanatory noun,
not a creator-selected output, and its bounded oracle test is clean.

Reproduce the fast structural checks:

```bash
python3 tools/gsmg/phase1_icon_symbol_layer_audit.py --self-test
```

Re-run the approximately two-minute oracle check:

```bash
python3 tools/gsmg/phase1_icon_symbol_layer_audit.py --run --json
```
