# GSMG Puzzle — Compact Stage, Clue, Input, and Output Ledger

## Scope

This file is a compact map of the GSMG puzzle from its first image to the
current unsolved boundary. It records:

- the load-bearing creator clues and authenticated puzzle artifacts;
- each stage's input, operation, and output;
- which conclusions are verified, reconstructed, provisional, or closed;
- the exact point at which the solved chain currently stops.

It intentionally omits most abandoned candidate strings, implementation
details, and individual negative runs. Those remain in
[`tools/gsmg/FINDINGS.md`](../tools/gsmg/FINDINGS.md).

### Status labels

- **Verified** — independently reproduced from a primary puzzle artifact.
- **Reconstructed** — exact mechanics reproduced, although not all intent is
  creator-confirmed.
- **Checkpoint** — a real relation that does not yet determine the next step.
- **Open** — required operation or plaintext is unknown.
- **Closed negative** — a specific tested interpretation failed; broader
  interpretations may remain open.
- **Quarantined** — authentic-looking data with weaker puzzle provenance.

---

## One-Page Chain

```text
Stage-0 14×14 image
  -> binary spiral
  -> gsmg.io/theseedisplanted

Stage-1 icon rebus + song lyric
  -> theflowerblossomsthroughwhatseemstobeaconcretesurface
  -> Phase-2/3 page

Phase-2 riddle
  -> causality
  -> SHA-256 password

Phase-3 seven exact answers
  -> concatenation
  -> SHA-256 password
  -> Phase 3.2

Phase-3.2 three clue answers
  -> concatenation
  -> SHA-256 password
  -> EBCDIC/Beaufort/VIC material

Phase-3.2.1
  -> EBCDIC 1141 + Beaufort(THEMATRIXHASYOU)
  -> Architect-style instructions and [23,16,7]

Phase-3.2.2
  -> keyed 9-ary/VIC checkerboard
  -> IN CASE YOU MANAGE TO CRACK THIS ...
     THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF ...

first-page title + prize address
  -> SHA-256
  -> SalPhaseIon / Cosmic Duality page

authenticated endgame stream
  -> DBBI
  -> binary(matrixsumlist)
  -> FAED
  -> decimal(lastwordsbeforearchichoice)
  -> decimal(thispassword)
  -> "sha256 our first hint is your last command"
  -> SALPH encrypted blob, split by binary(enter)
  -> raw "shabefanstoo"

first-piece colors + FEFE marker + sequential primes
  -> exact 31-position DBBI selector
  -> ncsyangcahiriasogaleafayanestve
  -> final two events touch the opening of matrixsumlist

CURRENT BOUNDARY
  -> determine what matrixsumlist does with the 31 selected characters
  -> solve DBBI and FAED together / recognize the yin-yang state
  -> open the remaining encrypted private-key material
```

---

## Stage Ledger

### Compact Creator-Clue Index

This is the minimal creator-authored clue set needed to understand the current
chain; it is not a transcript of every creator message.

| Clue | Established role |
|---|---|
| “Follow the white rabbit” | Selects the Stage-0 grid/spiral route |
| “Roses...” | Matches the blue=`1`/yellow=`0` color value `F73D92` |
| “Yellow and blue number,” “return [to] the first piece” | Reopens the original 24 colored endpoints |
| “First or zero” | Supports treating the colors as binary polarity |
| “Using prime numbers is required” | Supports the sequential-prime event walk |
| “Some characters need to be zeroed out” | Establishes a plural character-selection/zeroing clue, although its final consumer remains unknown |
| “There is 1 pixel here”; `{1,4,21}`; `R=18/A=1/B=2 ... bit` | Locates FEFE and gives the `RABBIT` rebus |
| “The rabbit's nest may contain a whole lot more [doors]” | Motivates inspection of the central nest; no additional door has been decoded |
| Reversed 1,288-bit message | Fixes the macro order from `yellowblueprimes` through `promised` |
| “Yin-yang” is the next/reached phase | Supports a state or relationship, not necessarily a literal password |
| “It's in front of your eyes but you're not seeing it” | Authenticated endgame instruction; exact operand remains unresolved |
| “Very last step is a true giveaway” | Final-ease/recognition cue. The former `VAT` subset was post-hoc (Phase 217), while `T -> SaltPhaseIon` is independently resonant but not source-unique among literal `true`-letter insertions (Phase 222). |
| “Regular Bitcoin Private key” | Fixes the final output type |

### Stage 0 — Follow the White Rabbit

| Field | Value |
|---|---|
| Input | Creator-posted JPEG `doc/img/gsmg_stage0_original_telegram.jpg`; later webpage PNG `doc/img/gsmg_puzzle_stage1.png`, both containing the same 14×14 colored grid |
| Primary clue | Rabbit artwork and “follow the white rabbit” framing |
| Operation | Classify black/blue as `1`, white/yellow as `0`; read from the top-left in the established counter-clockwise spiral |
| Output | `gsmg.io/theseedisplanted` |
| Status | **Verified** |

Important retained details:

- The grid contains 24 colored bit endpoints: **15 blue** and **9 yellow**.
- One exceptional pixel is RGB `(254,254,254)` / hex `FEFEFE`.
- The central 2×2 “rabbit nest” is all white under the corrected
  majority-cell classifier; the earlier `0100 = 4` reading was a sampling bug.
- Treating the binary partition as a maze produces a real but statistically
  ordinary route from FEFE to the border. Its unique shortest route is
  `RRUULUURRRURUU`; direct readings are non-language. This is retained as an
  unconfirmed structural observation, not a solved door.
- Opening blue cells as well (`wall = black only`) floods the graph from 3 to
  9 reachable border cells and removes all uniquely-shortest routes. Both
  effects occur in roughly 44% of matched random grids, so further wall/open
  recombinations are closed unless a creator clue selects one.

### Stage 1 — The Seed Is Planted

| Field | Value |
|---|---|
| Input | `gsmg.io/theseedisplanted` and eight colored icon fragments |
| Clues | `WAR + NING`, `LO` inside `CRYPTO/GIC`, and `CAN YOU DIG IT` |
| Identification | “The Warning” by Logic |
| Operation | Use the identified lyric as the form password |
| Output | `theflowerblossomsthroughwhatseemstobeaconcretesurface` |
| Status | **Verified** |

The icon files contain no additional established steganographic payload.

### Stage 2 — Causality

| Field | Value |
|---|---|
| Input | The long Phase-2/3 URL and its Matrix-themed riddle |
| Main clue | “Choice is an illusion created between those with power and those without” |
| Answer | `causality` |
| Operation | SHA-256 of the exact answer |
| Output | `eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf` |
| Use | AES-256-CBC passphrase for the next encrypted material |
| Status | **Verified** |

### Stage 3 — Seven-Part Password

The seven exact pieces are concatenated with preserved case and no whitespace,
then hashed with SHA-256.

| Part | Clue or source | Output |
|---|---|---|
| 1 | Previous stage | `causality` |
| 2 | Security-product clue | `Safenet` |
| 3 | Product-family clue | `Luna` |
| 4 | Hardware type | `HSM` |
| 5 | Binary/number clue | `11110` |
| 6 | Hexadecimal text artifact | `0x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E697262206E6F20726F6C6C65636E61684320393030322F6E614A2F33302073656D695420656854` |
| 7 | Required post-move chess FEN | `B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1` |

| Field | Value |
|---|---|
| Final SHA-256 | `1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5` |
| Status | **Verified** |

The original chess prompt and the post-move answer are different positions;
substituting the prompt FEN is incorrect.

### Stage 3.2 — Three-Clue AES Gateway

| Part | Clue | Output |
|---|---|---|
| 1 | Jacque Fresco identification | `jacquefresco` |
| 2 | White Rabbit quotation plus the earlier correction | `giveitjustonesecond` |
| 3 | Physics clue | `heisenbergsuncertaintyprinciple` |

Concatenating the three answers and hashing them gives:

```text
250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c
```

This opens the Phase-3.2 material. **Status: Verified.**

### Stage 3.2.1 — EBCDIC and Beaufort

| Field | Value |
|---|---|
| Input | Decrypted Phase-3.2.1 ciphertext |
| First operation | Decode with EBCDIC code page 1141 |
| Second operation | Beaufort cipher |
| Beaufort key | `THEMATRIXHASYOU` |
| Output | An Architect-style instruction text beginning `YOUR LIFE IS THE SUM...` |
| Important values | `23 ciphers`, `16 encryptions`, `7 passwords` |
| Status | **Verified** |

The numbers `[23,16,7]` recur in three mechanically real places:

1. the Phase-3.2.1 parody text;
2. the Architect scene's `23 individuals / 16 female / 7 male`;
3. the first-piece prime walk's profile: 23 selecting events, 16 blue-like
   single-character selections, and 7 yellow digraph selections.

This recurrence makes `[23,16,7]` an intended checkpoint, but no creator source
specifies a further arithmetic operation on the numbers.

### Stage 3.2.2 — Keyed 9-Ary / VIC Checkerboard

| Field | Value |
|---|---|
| Input | The long decimal digit stream from Phase 3.2.1 |
| Keyed alphabet | `FUBCDORA.LETHINGKYMVPS.JQZXW` |
| Escape digits | `{1,4}` |
| Operation | Validated straddling-checkerboard/VIC decode |
| Output | `IN CASE YOU MANAGE TO CRACK THIS THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF AND THEY ALSO NEED FUNDS TO LIVE` |
| Normalized length | 91 characters |
| Status | **Verified** |

This plaintext is the strongest direct clue to the final payload shape:
two Bitcoin private keys, described as “half and better half.”

### Route to SalPhaseIon / Cosmic Duality

| Field | Value |
|---|---|
| Input | `GSMGIO5BTCPUZZLECHALLENGE` plus prize address `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe` |
| Operation | SHA-256 of the exact concatenation |
| Output | `89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32` |
| Use | URL of the final authenticated puzzle page |
| Status | **Verified** |

---

## Phase 4 / Final Page: Authenticated Input Structure

The page's meaningful stream is:

```text
DBBI
+ binary("matrixsumlist")
+ FAED
+ decimal("lastwordsbeforearchichoice")
+ decimal("thispassword")
+ literal("sha256 our first hint is your last command")
+ first half of SALPH
+ binary("enter")
+ second half of SALPH
+ raw("shabefanstoo")
```

### Transport decodes

| Encoded segment | Decoded text | Status |
|---|---|---|
| Binary block after DBBI | `matrixsumlist` | **Verified** |
| Decimal block after FAED | `lastwordsbeforearchichoice` | **Verified** |
| Following decimal block | `thispassword` | **Verified** |
| Binary separator inside SALPH | `enter` | **Verified** |
| Reversed binary creator message | `yellowblueprimes matrixsumlist lastwordsbeforearchichoice yinyang wewontgiveawaythepassword itsinfrontofyoureyesbutyourenotseeingit verylaststepisatruegiveaway promised` | **Verified creator clue order** |

The macro message fixes an order of concepts. It does not state the missing
operation between every pair.

---

## Endgame Reconstruction

### `yellowblueprimes`

The original 24 colored endpoints have two natural polarity assignments:

| Assignment | Result |
|---|---|
| blue=`1`, yellow=`0` | RGB-like hex `F73D92` |
| yellow=`1`, blue=`0` | binary value `574061`, which is prime |

The prime-valued polarity is the stronger reading. **Status: Reconstructed.**

### FEFE and `{1,4,21}`

Creator clues and the real image jointly establish:

- there is exactly one `(254,254,254)` / `FEFEFE` pixel;
- its grid coordinate is `(row 8, column 5)` in 1-based notation;
- its zero-based spiral index is `163`, which is prime;
- it lies in character 21 (`n`) of `theseedisplanted`;
- it is bit position 4 of that character and its bit value is zero.

The creator's `R=18`, `A=1`, `B=2`, plus `BIT`, also mechanically forms
`RABBIT`. FEFE's established operational role is insertion into the ordered
prime/color event sequence; the older `planted -> plated` deletion is only a
secondary rebus.

### Exact Prime Walk

1. Order the 24 blue/yellow endpoint events by their actual spiral positions.
2. Insert FEFE at its own spiral position before color object 21.
3. Walk the first 25 sequential primes across the event colors.
4. Interpret blue-like events as one-character selections and yellow events
   as two-character selections.

The first 23 events select exactly 31 positions from DBBI's aligned plaintext:

```text
ncsyangcahiriasogaleafayanestve
```

The previously audited fixed clue vocabulary found literal `yang`, but a
later direct review also exposes two additional thematic phrases:

```text
ncs YANG cahiriasog A LEAF ay A NEST ve
```

`a leaf` echoes the seed/flower language, while `a nest` echoes the rabbit
nest. The `e` in `nest` is supplied specifically by the inserted FEFE event.
For uniformly random order-preserving 31-of-91 subsets, the exact joint rate
of containing `yang`, `leaf`, and `nest` is about `2.03e-9` (roughly one in
493 million). This is descriptive rather than a discovery p-value because
the words were noticed after inspecting the output and the broader thematic
word family was not pre-registered. Phase 48 mechanically reproduces the
community mask, but does not prove blind discovery or creator intent. Treat
the cluster as a provisional, low-confidence recognition checkpoint. A later
family-wise control against 7,887 common English words finds equally
word-rich order-preserving selections about `0.55%` of the time
(`p=0.00547`, replicated at `p=0.00550`), narrowly failing the project's
`p<0.005` promotion bar. Under that load-bearing broad-word control, the
cluster is ordinary and retained only as a descriptive fact. It is not a
recognition checkpoint, password, downstream operation, or basis for another
broad sweep.

The final two events cross the real page boundary:

| Event | Prime | Adjusted page position | Landing |
|---|---:|---:|---|
| 24, blue | 89 | 97 | bit 6 of `m`, first byte of `matrixsumlist` |
| 25, yellow | 97 | 105 | bit 6 of `a`, second byte of `matrixsumlist` |

Their color-bit match has an ordinary base rate of about 25%, so this is a
boundary checkpoint rather than proof of the intended consumer operation.

### `matrixsumlist`

A newly audited alternative is to keep the mechanically established first 23
prime-walk events as three lists:

```text
blue primes   -> 14 values -> sum 401
yellow primes ->  8 values -> sum 400
FEFE event    ->  1 value  -> 73
```

Thus the named yellow/blue lists balance to within one. Across all
`C(22,8)=319,770` assignments preserving the same 14-blue/8-yellow profile,
only `813` have an absolute sum difference at most one (`0.2542%`). This is
statistically notable but was discovered after inspecting the established
walk, so it is a constrained checkpoint rather than a formal discovery
p-value.

This is **not** the leading historical interpretation. The recovered Telegram
guide (`photo_1300@01-05-2025_00-12-58.jpg`) explicitly places DBBI token
chunks into a `14x14` matrix and sums its 14 rows, producing
`IZLKESEEDQPPEN`. Phase 53 reproduced that construction and found its
corrected-FEFE family negative. The `401/400` balance is retained only as an
unselected alternative observation.

The remaining direct matrix direction is also closed. Applying the same
modulo-26 rendering to columns gives `GBCXQOGEDMHFEV` (reverse
`VEFHMDEGOQXCBG`); reversing the historical row output gives
`NEPPQDEESEKLZI`. With all four row/column directions inside one
endpoint-assignment max-statistic null, the historical row output is ordinary
(`p=0.1186`, replicated at `p=0.1191`). The two main diagonal sums render only
`JF`/`FJ` and are too short for meaningful language scoring.

Uniform Caesar shifts do not rescue the family. Testing all `4x26=104`
row/column-direction-plus-shift outputs inside the same null gives
`p=0.7131`, replicated at `p=0.7138`; the best real member is the non-language
`MDPOIWIIHUTTIR`. Caesar, reversal, and their combination are therefore closed
for this guide.

The interpretation is sensitive in an informative way: folding FEFE into
blue changes the difference to `74`, while including events 24–25—which have
already crossed into the bytes of `matrixsumlist`—changes it to `7`. Keeping
FEFE separate follows its real non-blue/non-yellow color and the literal
`yellowblueprimes` wording, but remains load-bearing.

The immediate bounded consumer test did not solve the transition. Using
`401`, `400`, and `73` as one-based forward/backward indices in the complete
screenplay scene before the Architect's `choice` yields no instruction
(backward: `it`, `INT`, `truth`). The narrower Architect-spoken source has
only 72 words and cannot accept 400/401. No HTTP-status, digit-sum, modular,
or cipher interpretation is justified by this result.

The SalPhaseIon textarea supplies a visually related but non-selective
identity: its 1,075 logical symbols are separated by exactly 1,074 spaces, so
any 401-symbol rendering necessarily contains 400 internal spaces. No two
established page-segment boundaries are 401 symbols apart. Direct indexing
selects only `EIE` forward, `AF0` backward, or FAED-local symbol 206 (`e`), so
this does not recover a natural 401-symbol region.

One exact numerical reconstruction is:

```text
574061
-> [[5,7,4],[0,6,1]]
-> matrix sums/list
-> [23,16,7]
```

The Architect dialogue then supplies:

```text
23 -> BOTH
16 -> ULTIMATELY
 7 -> THE
```

Beginnings give `BUT`; endings give `HYE`. A B↔H mirror around E resembles a
yin-yang/polarity checkpoint, but no creator-authored operation confirms it,
and the associated FAED `{h,e}` monoalphabetic hypothesis is negative.

The immediate unresolved question remains:

> What exact, creator-supported operation does `matrixsumlist` apply to the
> recovered 31-character DBBI selection?

### `lastwordsbeforearchichoice`

This points to the last words before the Architect's choice in the relevant
Matrix dialogue. It supports the `[23,16,7]` / `BOTH`, `ULTIMATELY`, `THE`
checkpoint above. Attempts to turn flexible beginnings/endings, rails, or
permutations into a unique downstream instruction have not survived
calibration.

### `yinyang`

Creator wording describes yin-yang as a **reached state**, not necessarily a
literal password. Current evidence supports treating it as recognition of a
duality/polarity relationship involving DBBI and FAED, rather than as the
string `yinyang` to hash.

Neither DBBI nor FAED is currently solved:

- DBBI's exact prime/color mask is known, but its selected text has no known
  consumer.
- FAED's best-supported escape pair is `{g,i}`. It ranks first among all
  pairs by corrected code-IC, but calibrated monoalphabetic recovery
  (`p=0.0396`, threshold `p<0.005`) and a full VIC-style chain-addition sweep
  of 5,761,385 candidate pairs both failed.
- FAED `{h,e}` as a monoalphabetic-English interpretation is also negative
  (`p=0.634`).

### SalPhaseIon / SALVATION

The title also has an exact nested decomposition:

```text
SAL [PHASE I] ON
```

The contiguous inner text is `PHASE I`; the remaining outer letters form
`SALON`. `PHASE I` is not merely a modern label: the authenticated Stage-1
form posts to `/phase1verification`, and the identified song's first stanza
is explicitly headed “Phase one” before “The seed is planted when opposites
attract.” These are separate facts: no creator source says the final title
points back to that earlier stage. Creator message `6497` actually contrasts
the already-cracked “first stage” with later “salphation,” so it cannot
support the proposed link. The decomposition remains a plausible,
unconfirmed cross-phase reading. A full-offset, both-orientation
native-symbol complement alignment of DBBI against FAED is negative
(`p=0.459`, replicated at `p=0.455`), and `SALON` has no creator-confirmed
referent or operation.

The title admits the following historical textual rebus:

```text
SalPhaseIon
replace PHASE with VAT
-> SalVATIon
-> SALVATION
```

Phase 217 corrected the evidentiary status: `VAT` drops three of the seven
words with no source-selected subset and was motivated after the title target
was noticed, so it is not treated as supplied by the clue. The creator typo
`salphation` can also be element-parsed so that `PH -> V` yields the familiar
`[23,16,7]` atomic-number relation, but chemistry lacks an independent
creator clue. Treat the atomic-number reading as suggestive, not established.
Direct SALVATION-derived passphrases were negative.

---

## Encrypted Targets

| Target | Provenance | Current status |
|---|---|---|
| `SALPH` | Embedded in the authenticated SalPhaseIon page, with binary `enter` between its halves | **Open** |
| `COSMIC` | Embedded in the authenticated Cosmic Duality page | **Open**; complete community raw-digest/MD5/103x103/base-38 construction reproducible, but spam-linked and not creator-authenticated |
| `P32TRAILING` | OpenSSL `Salted__` blob appended to the solved Phase-3.2 plaintext and corroborated by the official puzzle repository | **Open** |
| `URLBLOB` | Complete Wayback-recovered OpenSSL blob, but described by its source as orphaned and lacking equivalent official corroboration | **Quarantined / open** |

The creator explicitly described the final result as a regular Bitcoin private
key. The known prize address is:

```text
1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe
```

The 80-byte encrypted payload shape of SALPH and P32TRAILING is compatible
with 64 bytes of key material plus a full PKCS#7 padding block, but exhaustive
tested candidate sets have not opened either blob.

---

## Major Tested Interpretations That Remain Closed

These are closures of specific models, not proof that the underlying artifact
is meaningless:

| Interpretation | Result |
|---|---|
| Literal `yinyang`, `yang`, SALVATION, Fresco titles/quotes, and established clue phrases as AES passwords | No credible hit |
| Legacy/extended CBC, ECB, CFB/OFB/CTR, 3DES, PBKDF2 variants, and AES Key Wrap over curated candidates | No credible hit |
| Padded two-private-key binary-material hypothesis over the completed medium curated tiers | No hit |
| Fixed-window no-padding Tier-1 search | All 23 queued Bloom/vanity classifications were externally checked: six Bloom false positives and 17 unfunded vanity-shaped addresses; no known/funded hit |
| Padded binary-key-material Tier 1 and Tier 2 | 733,264 unique normalized keystrings and 52,795,008 unique CBC/ECB operations; no hit |
| DBBI single-layer monoalphabetic/checkerboard and bounded digraphic families | Negative under calibrated models |
| FAED `{h,e}` monoalphabetic recovery | Negative, `p=0.634` |
| FAED `{g,i}` monoalphabetic recovery | Negative at the registered threshold, `p=0.0396` versus `p<0.005` |
| FAED `{g,i}` VIC chain-addition reopening | 5,761,385 candidate pairs, zero hits |
| Adjacent-difference lag-1, dual-ternary, dual-quinary, matrixsumlist permutation, and prime-zeroing bounded families | Calibrated negative |
| Phase-One “opposites attract” as direct native-symbol DBBI/FAED complement alignment | Real maximum 21/91; ordinary under the complete offset/orientation null (`p=0.459`, replicated) |
| Rabbit-nest maze route encodings | The creator-consistent binary partition has real geometry, but direct outputs are non-language and its strict structure occurs in roughly 8–10% of matched random grids; opening blue cells reduces the result to ordinary ~44% properties |

Do not interpret this table as proof that the blobs all use the same cipher or
that every possible password length has been exhausted. The results only close
the exact candidate families, transformations, modes, and validation rules
that were run.

---

## Current Boundary and Best Next Evidence

### What is known exactly

```text
yellowblueprimes
-> ordered colors + FEFE + sequential primes
-> exact 31-position DBBI selection
-> ncsyangcahiriasogaleafayanestve
-> boundary contact with matrixsumlist
```

### What is still missing

1. The operation that consumes the 31 selected characters.
2. The relationship that makes DBBI and FAED jointly recognizable as the
   creator's “yin-yang” state.
3. The correct passphrase/key material and cipher interpretation for the open
   encrypted blobs.

### Highest-value missing evidence

- Creator/community media or replies that explicitly explain what to do after
  the 31-character selection.
- The unavailable physical *Cosmic Duality* book pages 57–58.
- Any independently preserved copy or photograph of book pages 57–58. The
  exact `barrystyle` media was already recovered and is only the book's front
  cover; a complete audit of his 23 retained attachments found no interior
  book image.
- A new creator hint that selects an operation, rather than another large
  unconstrained transform family.

All proposed transitions are now governed by the five-gate admission and
promotion rules in `doc/GSMG_STRICT_TRANSITION_WORKSHEET.md`. In particular,
the worksheet keeps the exact 31-character DBBI selection live while parking
`KIT`, `ggn`, `BATCH`, `igecabdfh`, overlays, DNA, and RGB-vector consumers
until new evidence fixes their missing operations.

The dedicated provenance refresh in
`doc/GSMG_MATRIXSUMLIST_PROVENANCE_REFRESH.md` extends that evidence check
through the 2026-08-09 Telegram export. It found no creator-authored fixing
instruction: the recovered guide uses row sums on a different DBBI object, a
2024 community attachment defines row-plus-column sums on a different input,
and the newest posts add only incompatible community theories. The transition
therefore remains blocked specifically at G3.

---

## Primary Project References

- [`doc/GSMG_PUZZLE.md`](GSMG_PUZZLE.md) — main verified solve record.
- [`doc/GSMG_STRICT_TRANSITION_WORKSHEET.md`](GSMG_STRICT_TRANSITION_WORKSHEET.md) —
  five-gate admission, promotion, calibration, and reopening rules for every
  proposed transition.
- [`doc/GSMG_MATRIXSUMLIST_PROVENANCE_REFRESH.md`](GSMG_MATRIXSUMLIST_PROVENANCE_REFRESH.md) —
  source-by-source audit of the remaining G3 operation gap through 2026-08-09.
- [`doc/GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md`](GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md) —
  creator-only clues and their current interpretation.
- [`doc/GSMG_PHASE_BOUNDARY_REAUDIT.md`](GSMG_PHASE_BOUNDARY_REAUDIT.md) —
  conclusions superseded or narrowed by later findings.
- [`doc/GSMG_BIRD_VIEW_REASSESSMENT.md`](GSMG_BIRD_VIEW_REASSESSMENT.md) —
  current high-level assessment and priority changes.
- [`tools/gsmg/FINDINGS.md`](../tools/gsmg/FINDINGS.md) — detailed chronological
  experiments, corrections, null models, and negative results.
