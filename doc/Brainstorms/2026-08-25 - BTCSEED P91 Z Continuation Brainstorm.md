---
type: hypothesis
status: parked
date: 2026-08-25
topics:
  - brainstorm
  - btcseed
  - dbbi
  - faed
  - bifid
  - p91
  - polybius
  - bip39
  - bitcoin
  - matrix
  - control-rails
---

# BTCSEED / P91 / Z Continuation Brainstorm

> [!caution] Unverified continuation portfolio
> This document deliberately favors breadth and creativity. It is not a
> finding, candidate promotion, or authorization to run an adaptive search.
> Arithmetic and already-reproduced inputs are separated from interpretations.
> Every executable direction below needs a frozen candidate family, controls,
> success criteria, and stop rule before it can become a phase.

> [!info] Ranked queue exhausted (2026-08-25)
> All six ranked priorities below were executed as Phases 397--402, all
> closed negative -- see each priority's own callout and the `## Outcome`
> section at the bottom. Per this document's own promotion contract, that
> does not authorize widening any closed family; it also does not close
> the remaining 100-item idea bank, which was never itself ranked or
> frozen. A follow-up survey of that bank (2026-08-25, not part of this
> document) identified one well-grounded coverage gap -- Phase 397's raw
> 59-byte control-channel outputs, never consumed as BIP32 seed material
> -- as the strongest remaining candidate. That gap was itself frozen and
> executed as [Phase 403](../../tools/gsmg/FINDINGS.md#phase-403----phase-397s-raw-59-byte-control-channel-outputs-as-bip32-seed-material-closed-negative-2026-08-25):
> 96,016 address checks against the exact prize address, zero hits,
> planted positive fires. A second identified residual -- `Q472`'s data
> rail (`Q472[1::2]`) in its own native order, never tested as a
> candidate on its own since Phase 402's ten machines only ever
> transform it -- was likewise frozen and executed as
> [Phase 404](../../tools/gsmg/FINDINGS.md#phase-404----q472s-native-order-data-rail-as-an-identity-messagekey-candidate-closed-negative-2026-08-25):
> quadgram-shuffle p=0.859 (nowhere near the 0.005 bound), 2,880 oracle
> attempts and 4 address checks, zero hits, all three planted positives
> fire. A third residual -- the `{B,C,D,E}` control rail read as a
> Base64 sextet channel (three symbols = 6 bits = one Base64 character)
> over the two boundaries Phase 397 never covered, the full 285-symbol
> rail and the P91-scoped 45-symbol rail -- was frozen and executed as
> [Phase 405](../../tools/gsmg/FINDINGS.md#phase-405----bcde-control-rail-as-a-base64-sextet-channel-closed-negative-2026-08-25):
> 4 candidates (2 sources x 2 grid-native mappings), zero magic-byte,
> structural, key-format, or target-address hits, both planted positives
> fire. A fourth residual -- the full 285-symbol control rail split into
> four 128-symbol/256-bit windows, each anchored to an existing
> structural boundary (stream start, first control symbol after the
> `BTCSEED` header, first control symbol after the stream's unique `Z`,
> end-aligned) rather than an arbitrary offset -- was frozen and executed
> as [Phase 406](../../tools/gsmg/FINDINGS.md#phase-406----four-structurally-anchored-256-bit-windows-of-the-full-control-rail-closed-negative-2026-08-25):
> 16 candidates (4 windows x 2 grid-native mappings x 2 bit-packings, all
> 16 byte-distinct), consumed as both a direct scalar and raw BIP32 seed
> material through Phase 400's six frozen paths, 192,064 address checks,
> zero hits, all three planted positives fire. A fifth residual --
> "Idea bank E" items 80-81, `P91` repeated as a Vigenere-style key over
> `Q472` in both the standard alphabet index and the DBBI-keyed square's
> native coordinate space -- was frozen and executed as
> [Phase 407](../../tools/gsmg/FINDINGS.md#phase-407----p91-repeated-as-a-vigenere-style-key-over-q472-idea-bank-items-80-81-closed-negative-2026-08-25):
> 6 candidates (3 alphabet-space x 3 coordinate-space, mirroring Phase
> 401's own `P91`/`A26`/`A5` construction with `P91REP` in place of the
> fixed difference), family-wise rate 43.41% (far above the 0.5% bound),
> 17,280 oracle attempts and 24 address checks, zero hits, all three
> planted positives fire. Per the user's own request, the next step was
> a branch-level gate rather than another idea-bank item: does the
> `BTCSEED` checkpoint itself (Phase 386) survive alternate Bifid
> block/period conventions, or does it exist only under the single-
> 570-character-block reading Phase 386 happened to use? Executed as
> [Phase 408](../../tools/gsmg/FINDINGS.md#phase-408----bifid-period-robustness-audit-of-the-btcseed-checkpoint-full-block-convention-dependent-not-disproven-2026-08-25):
> 8 block schedules (the 7 standard periods `7,13,49,91,98,472,570` plus
> a custom `[98,472]` Z-boundary schedule), all round-tripping correctly
> against both the real ciphertext and a synthetic planted positive.
> Only period 570 produces output starting with `BTCSEED`, with `Z`
> uniquely at index 97; every other schedule's longest common prefix
> with `BTCSEED` is 0-1 characters (chance, given `B`'s high frequency
> in this skewed alphabet). Result: the checkpoint is classified
> **full-block-convention-dependent, not disproven** -- real and
> reproducible at period 570 (the whole-ciphertext boundary), but its
> `BTCSEED`/`Z@97`/rail-alternation package does not independently
> reappear under any other tested period. Per the contract's own
> interpretation rule, idea-bank items 82-89 (autokey seeding,
> deduplicated second squares, ordered key schedules -- all constructions
> that would need this checkpoint to be period-robust to motivate
> spending further effort on them) are parked unless an independent clue
> specifically selects one of them. The remaining ~95 idea-bank items
> (82-89 in the same "P91 as a key" section, plus idea banks A-D and F)
> are still untested and still require their own fresh, separately-
> frozen contracts.

## Executive result

The most productive continuation is to stop treating the 570-character Bifid
output as failed plaintext and instead ask whether it is a typed stream:

```text
BTCSEED | P91 ending in Z | Q472
    7          91             472
```

The strongest structural direction identified at the time this document was
written was a control/data interpretation: one alternating rail contains only
`B,C,D,E`, exactly the upper-left `2x2` of the keyed Bifid square. After `Z`,
the 472-character suffix divides into 236 control/data digraphs. The 236
four-symbol controls can encode exactly 472 bits, or 59 bytes. That
byte-perfect boundary was the first test run (Phase 397, Priority 1) and
closed negative as a typed-container/key-format search; see the "ranked queue
exhausted" note above for the one identified follow-up (raw-byte BIP32 seed
consumption) it did not cover.

Three other high-value directions follow:

1. the Telegram BIP39 construction's mapping is exactly the column-major order
   of the keyed square's upper-left `2x2`, so its mapping may be less arbitrary
   than Phase 394 assumed, although its window offset remains unselected;
2. the 98-character `BTCSEED + P91` prefix supplies 196 Polybius coordinates,
   exactly enough to form a `14x14` matrix; and
3. Phase 396 tested P91-derived strings as blob passphrases, not as direct
   Bitcoin private keys or BIP32 seed bytes, even though the header says
   `BTCSEED`.

## Verified starting facts

These are inherited from Phases 386--396 and are not new claims made by this
brainstorm:

- the DBBI-keyed Bifid square is:

  ```text
  D B I F H
  C E G A K
  L M N O P
  Q R S T U
  V W X Y Z
  ```

- decrypting FAED as one 570-character Bifid block reproduces a stream beginning
  `BTCSEED`;
- the stream contains one `Z`, at zero-based index 97;
- `decoded[7:98]` is exactly 91 characters and ends in `Z`;
- `decoded[98:]` is exactly 472 characters;
- the even-position rail of the full output contains only `B,C,D,E`;
- Phase 387's first-98-character digraph construction mechanically produces
  `KMODEST` under its declared read;
- Phase 389's family-wide control downgrades `KMODEST` as a selected English-like
  extraction;
- Phase 394 reproduces the posted checksum-valid 24-word BIP39 mnemonic, but its
  declared 3,696 mapping/window family produces 13 valid checksums and no prize
  address hit; and
- Phase 396 closes its declared P91/mod-26/blob-passphrase family negative. It
  does not close the distinct typed-consumer ideas below.

Relevant records:

- [Phase 386 implementation](../../tools/gsmg/phase386_btcseed_bifid_faed_decode_audit.py)
- [Phase 394 implementation](../../tools/gsmg/phase394_telegram_recipe_leads_authentication_audit.py)
- [Phase 396 implementation](../../tools/gsmg/phase396_p91_header_aware_block_audit.py)
- [canonical phase findings](../../tools/gsmg/FINDINGS.md)

## Mechanical observations

These relations follow directly from the registered lengths and square. At
the time this document was written none had a dedicated regression test or
null calibration; Phases 397 (control rail), 398 (BIP39 mapping), and 399
(14x14 matrix) now cover the three below, each closed negative -- see the
matching "### Priority N" section for the executed result. The relations
themselves remain mechanically correct; only their status as untested is
stale.

### The four-symbol rail is a square-native object

The set `{B,C,D,E}` is exactly the upper-left `2x2` of the keyed square:

```text
D B
C E
```

Two especially natural numeric orders exist:

```text
row-major:    D, B, C, E -> 0, 1, 2, 3
column-major: D, C, B, E -> 0, 1, 2, 3
```

The posted BIP39 mapping is recorded as:

```text
B,C,D,E -> 2,1,0,3
```

which is the same as column-major `D,C,B,E -> 0,1,2,3`. This does not by
itself select column-major reading or offset 30. It does suggest that a future
recalibration should distinguish two grid-native mappings from the other 22
permutations rather than treating all 24 as equally grounded.

### The post-Z control rail is exactly byte-aligned

Because Q472 starts at global even index 98, its local even-position rail is
the four-symbol rail:

```text
control = Q472[0::2]  # 236 symbols, alphabet B/C/D/E
data    = Q472[1::2]  # 236 general keyed-square letters
```

Each control symbol can carry two bits under either grid-native `2x2` order:

```text
236 symbols x 2 bits = 472 bits = 59 bytes
```

This is the cleanest new consumer boundary in the branch.

### The prefix has exact Stage-0-sized coordinate geometry

The first 98 letters can be written as a `14x7` rectangle: one `BTCSEED`
header row followed by P91's thirteen rows. Each Bifid letter has two
coordinates:

```text
98 letters x 2 coordinates = 196 values = 14 x 14
```

A natural construction is to turn each seven-letter row into fourteen cells
by appending its seven row coordinates and seven column coordinates. Whether
any binary reduction matches the authenticated Stage-0 `14x14` matrix remains
untested.

## Idea bank A: boundary and geometry

1. Parse the stream as `BTCSEED | P91 | Q472`, with `BTCSEED` as a type label.
2. Treat `Z` as a terminator included in P91.
3. Treat `Z` as a delimiter excluded from P90.
4. Treat `Z` as an opcode meaning reverse, swap rails, or reset.
5. Treat `Z=(5,5)` as an end marker because it occupies the last square cell.
6. Test whether `Z` is a checksum determined by the preceding 90 letters.
7. Under an explicitly selected Atbash interpretation, test whether `Z -> A`
   behaves as zero padding.
8. Lay P91 out as `13x7`, placing `Z` in the bottom-right cell.
9. Place `BTCSEED` above P91 as the first row of a `14x7` rectangle.
10. Transpose that rectangle to `7x14` and treat each column as a channel.
11. Convert each `14x7` row into seven row coordinates followed by seven
    column coordinates, producing a `14x14` value matrix.
12. Try only square-native binary reductions of that matrix: coordinate parity,
    `<=2` versus `>2`, and corner versus non-corner.
13. Compare those reductions with the authenticated Stage-0 binary matrix.
14. Use each Stage-0 bit to choose row or column coordinate from the
    corresponding coordinate pair.
15. Inspect whether the FEFE position maps to an exceptional coordinate cell.
16. Treat the two Phase-387 `7x7` digraph rails as image planes rather than
    word-bearing rows.
17. Overlay those planes cellwise as coordinate pairs.
18. Restrict route reads to paths already demonstrated in GSMG: row, column,
    transpose, reverse, spiral, boustrophedon, and authenticated checkerboard
    polarity.

## Idea bank B: control/data stream

19. Deinterleave Q472 into a 236-symbol BCDE control rail and a 236-letter data
    rail.
20. Map controls by column-major square order and pack them into 59 bytes.
21. Repeat under row-major square order as the one principal negative/control
    alternative.
22. Test forward/reverse byte order.
23. Test MSB-first/LSB-first packing within bytes.
24. Apply strict typed recognizers to the resulting 59 bytes: printable text,
    hex, Base64, gzip/zlib/ZIP, `Salted__`, DER, WIF, Bitcoin transactions, and
    known file signatures.
25. Treat the 59 bytes as ciphertext and the broad rail as key material.
26. Pack or hash the broad rail and XOR it with the 59 control bytes.
27. Group four control/data digraphs at a time; `236 = 59 x 4` makes each group
    one control byte plus four data letters.
28. Map each digraph into a base-100 value as `25*control + data`.
29. Test the opposite radix nesting `4*data + control`.
30. Interpret in-range base-100 values as direct bytes/ASCII.
31. Let the control select one of four rotations of the paired data letter in
    the keyed square.
32. Let it select a cardinal move: up, right, down, left.
33. Let its two bits select `row`, `column`, `6-row`, or `6-column` from the
    paired data letter.
34. Pair the resulting 1--5 digits and map them back through the keyed square.
35. Use one control bit for row/column and the other for normal/reversed
    coordinate.
36. Use control values as small shifts of the paired data index modulo 25.
37. Use controls as a four-operation selector: add, subtract, swap coordinates,
    or leave unchanged.
38. Analyze the broad data rail alone after stripping the mechanical carrier.
39. Convert the full 285-symbol BCDE rail into 570 bits, exactly one mask bit
    per decoded character.
40. Split those values into two 285-bit planes representing the local row and
    column bits of the `2x2` control square.
41. Reshape the 285-bit planes as `15x19` and `19x15` images.
42. Reshape the combined 570 bits as `30x19` or `19x30`.
43. Group the 285 controls in threes, yielding 95 six-bit/Base64 indices.
44. Decode the resulting 95-character Base64-like channel only under the two
    grid-native mappings and mathematically required padding.
45. Isolate P91's 45 BCDE positions; groups of three yield exactly fifteen
    six-bit values, potentially a short instruction token.
46. Parse P91 as 45 `[data, control]` records followed by `Z`, and Q472 as 236
    `[control, data]` records. Under this model, `Z` switches record order.

## Idea bank C: BTCSEED as a typed consumer

47. Treat the text following `BTCSEED` as entropy or key material, not prose.
48. Use SHA-256 of exact P91 bytes as a raw secp256k1 scalar.
49. Test lowercase and uppercase P91 hashes against the prize address under
    compressed and uncompressed public-key encodings.
50. Repeat the same direct-key check for P90, Q472, and the complete 570-letter
    stream.
51. Take the first or last 128 grid-mapped BCDE symbols as 256-bit raw key
    material.
52. Admit other 128-symbol windows only when an authenticated boundary selects
    them: stream start, after `BTCSEED`, after `Z`, offset 21, or a grid edge.
53. Recalibrate the posted 24-word BIP39 construction under the two grid-native
    mappings separately from the complete 24-permutation family.
54. Search for a source-grounded explanation of the posted offset 30 before
    giving the mnemonic additional weight.
55. Test the other standard BIP39 lengths: 12, 15, 18, and 21 words in addition
    to the already-tested 24-word form.
56. Permit the mathematically necessary one-bit alignment for BIP39 lengths not
    divisible by two, without widening any other axis.
57. Feed P91 or the 59-byte channel directly into BIP32's `Bitcoin seed`
    HMAC-SHA512 construction.
58. Apply only a frozen small family of standard BIP32 derivation paths.
59. Test old and modern Electrum seed recognition because `BTCSEED` does not
    necessarily mean BIP39.
60. Apply strict WIF and Base58Check recognition to packed channels.
61. Check whether the 59-byte channel contains a 32-byte scalar plus checksum,
    IV, chain fragment, or instruction trailer.
62. Inspect whether the full 570-bit control encoding resembles a DER signature
    or signed-message payload after the unavoidable two-bit remainder is
    accounted for.
63. Use literal `BTCSEED` as a domain separator or PBKDF salt with P91 as input.
64. Keep casing bounded: Bifid does not encode case, so uppercase/lowercase are
    valid byte representations but invented mixed-case forms are not.

## Idea bank D: three aligned 91-character objects

The branch now has three exact-length objects:

```text
DBBI
M91
P91
```

65. Define `A = DBBI - M91`, the already-known `YOUWON`-bearing subtraction,
    then test `P91-A`, `P91+A`, and `A-P91`.
66. Repeat the same ternary relations in keyed-square coordinates modulo 5
    rather than alphabet values modulo 26.
67. Operate on corresponding row and column coordinates independently.
68. Cross-splice `row(P91)` with `column(DBBI)` and the reverse.
69. Cross-splice P91 and M91 coordinates in both directions.
70. Stack all three `13x7` grids as `13x21`.
71. Stack them as `39x7`.
72. Build exact-character equality masks for each pair.
73. Build row-coordinate and column-coordinate equality masks separately.
74. At each position take the majority, minority, minimum, maximum, or median
    coordinate, with the operation frozen before word inspection.
75. Use the `YOUWONX` row at offsets 21--27 to select the corresponding P91
    row.
76. Apply the borrow and VIC rails as selectors over P91 rather than treating
    them solely as corroborations of offset 21.
77. Use the complete `DBBI-M91` stream as a repeating key over Q472.
78. Remove, reverse, or transpose only the P91 row aligned to `YOUWONX`.
79. Compare row and column summaries across the three `13x7` grids, permitting
    a route only when it is uniquely selected.

## Idea bank E: P91 as a key for Q472

80. Repeat P91 over Q472 as a Vigenere-style key.
81. Repeat it in native modulo-5 coordinates instead of modulo 26.

> [!info] Items 80-81 executed as Phase 407 (2026-08-25); items 82-89 parked
> Items 80-81 closed negative -- see the "Ranked queue exhausted"
> callout above. Items 82-89 below (autokey seeding, deduplicated
> second squares, ordered key schedules, block partitioning) were then
> gated by Phase 408, a Bifid period-robustness audit of the Phase 386
> `BTCSEED` checkpoint itself: only period 570 (the whole-ciphertext
> block) reproduces `BTCSEED`/`Z@97`/the rail alternation; no other
> tested period or the custom Z-boundary schedule does. Per the
> contract's own interpretation rule, items 82-89 are parked unless an
> independent clue specifically selects one of these constructions --
> they are unexecuted, not disproven.

82. Use P91 as an autokey seed.
83. Deduplicate P91 into a new keyed square and decode Q472 with it.
84. Apply DBBI, M91, and P91 as three ordered key schedules.
85. Partition Q472 as five full 91-character blocks plus a 17-character
    remainder.
86. Treat the remainder as a checksum or trailer only if the five full blocks
    produce a coherent common operation.
87. Apply the same P91 operation independently to each complete block and test
    for cross-block agreement.
88. Transpose the five blocks into 91 vertical channels.
89. Use terminal `Z` as a direction change before applying P91 to Q472.

## Idea bank F: Bifid continuation rules

90. Reset the Bifid period at the `Z` boundary.
91. Restrict alternate periods to the observed factors/boundaries `7,13,49,91,
    98,472,570`.
92. Decode the first 98 ciphertext characters as one block and the remainder
    as another.
93. Use row-column mode before `Z` and column-row mode after it.
94. Swap the two coordinate rails after `Z`.
95. Reverse coordinate order after `Z`.
96. Interpret `Z=(5,5)` as selecting reversal of both axes.
97. Re-encrypt P91 to expose and inspect its exact coordinate rails.
98. Permit a second Bifid pass on Q472 only if a boundary supplies the period.
99. Use `BTCSEED` as the keyword source for a second square.
100. Use P91's deduplicated alphabet as the keyword source, treating P91
     literally as a seed.

## Ranked verification queue

### Priority 1: post-Z 59-byte channel

> [!info] Executed as Phase 397 (2026-08-25)
> All 8 frozen candidates (2 mappings x 2 directions x 2 packings) tested
> zero magic-byte triggers, zero structural parses, zero key-format
> matches, zero exact target-address hits. Closed negative as scoped. See
> [Phase 397](../../tools/gsmg/FINDINGS.md#phase-397----btcseedp91z-brainstorm-priority-1-post-z-59-byte-control-channel-closed-negative-2026-08-25)
> and [its implementation](../../tools/gsmg/phase397_p91z_priority1_control_channel_audit.py).
> Does not close the other five priorities or the idea bank at large.

Freeze:

- Q472 exactly as `decoded[98:]`;
- control as Q472 even positions;
- the row-major and column-major `2x2` mappings only;
- forward/reverse and MSB/LSB as separately counted axes; and
- strict typed recognizers, not English scoring.

The best positive result would be a parser-valid container, exact key/address,
or coherent plaintext with a checksum. Printability alone is insufficient.

### Priority 2: coordinate-selected BIP39 recalibration

> [!info] Executed as Phase 398 (2026-08-25)
> 308 trials (2 mappings x 154 windows), expected 1.203. Exactly 1
> checksum-valid mnemonic reproduces -- the same previously-posted one,
> under column-major at offset 30; row-major produces zero hits. Offset 30
> matches none of 6 pre-declared natural-boundary candidates. Closed per
> this section's own stated criterion: the mnemonic is within the expected
> count and offset 30 remains unselected. See
> [Phase 398](../../tools/gsmg/FINDINGS.md#phase-398----btcseedp91z-brainstorm-priority-2-bip39-checksum-recalibration-under-the-two-grid-native-mappings-closed-negative-2026-08-25)
> and [its implementation](../../tools/gsmg/phase398_p91z_priority2_bip39_recalibration_audit.py).

Separate two questions:

1. does the keyed square genuinely reduce the 24 mappings to two natural
   mappings; and
2. does any source select the posted offset 30?

The checksum should be recalibrated under the reduced family, but the mnemonic
must still authenticate through an address/key or independently fixed semantic
structure.

### Priority 3: 98 letters to 14x14 coordinates

> [!info] Executed as Phase 399 (2026-08-25)
> Planted positive fires exactly. On the real data, best of 6 frozen
> reductions reaches only 107/196 cell agreement (barely above the 98/196
> chance baseline), no exact match. 47,060/100,000 (47.06%) multiset-
> preserving shuffles reach at least that agreement -- squarely
> unremarkable, nowhere near the 0.5% promotion threshold. Closed negative.
> See [Phase 399](../../tools/gsmg/FINDINGS.md#phase-399----btcseedp91z-brainstorm-priority-3-98-letter-to-14x14-coordinate-matrix-closed-negative-2026-08-25)
> and [its implementation](../../tools/gsmg/phase399_p91z_priority3_coordinate_matrix_audit.py).

Pre-register the one direct construction—seven row coordinates followed by
seven column coordinates for each letter row—and a small binary-reduction
family. Compare against the authenticated Stage-0 matrix and shuffled controls.

### Priority 4: direct Bitcoin consumers of P91

> [!info] Executed as Phase 400 (2026-08-25)
> 96,032 total address checks (16 direct scalars + 16 BIP32 masters +
> 96,000 child addresses across 48,000 derived keys, 8 roots x 6 paths x
> 1,000 indices) against the exact prize address. Both planted positives
> fire exactly. Zero hits. Closed negative per the contract's own
> promotion rule. See
> [Phase 400](../../tools/gsmg/FINDINGS.md#phase-400----btcseedp91z-brainstorm-priority-4-p90p91q472full-stream-as-direct-bitcoin-key-material-closed-negative-2026-08-25)
> and [its implementation](../../tools/gsmg/phase400_p91z_priority4_direct_bitcoin_consumer_audit.py).

Test exact P91/P90/Q472/full-stream byte forms as raw SHA-derived scalars and
BIP32 seeds. Do not confuse a Phase-396 AES-blob negative with an address/key
negative.

### Priority 5: P91 against the YOUWON-bearing difference

> [!info] Executed as Phase 401 (2026-08-25)
> Both planted positives fire. Real data: zero keyword hits, family-max
> quadgram score -649.21, 6,007/100,000 (6.01%) shuffles reach at least
> that score -- far above the 0.5% promotion bound. Oracle: 17,280
> attempts, zero hits. Direct-key: 24 address checks, zero hits. Closed
> negative per the contract's own promotion rule. See
> [Phase 401](../../tools/gsmg/FINDINGS.md#phase-401----btcseedp91z-brainstorm-priority-5-p91-against-the-youwon-bearing-dbbi-m91-difference-closed-negative-2026-08-25)
> and [its implementation](../../tools/gsmg/phase401_p91z_priority5_youwon_difference_algebra_audit.py).

Freeze `A=DBBI-M91` and test only the small ternary/modulo-5 family named above.
This is more grounded than inventing another arbitrary P91/DBBI operator.

### Priority 6: control/data digraph machine

> [!info] Executed as Phase 402 (2026-08-25)
> All four planted positives fire (selector-machine phrase recovery,
> rotation-machine phrase recovery at q_row=1, Salted__ byte-fixture
> detection, direct-scalar address match). Real data: zero keyword hits
> across all 6 letter machines; family-max quadgram_mean -7.5621;
> 90,459/100,000 (90.46%) of data-rail-only shuffles reach at least that
> score -- nowhere near the 0.5% promotion bound. Zero raw-byte machines
> parser-valid. Oracle: 17,280 attempts, zero hits. Direct-key: 32
> address checks, zero hits. Closed negative per the contract's own
> promotion rule -- exhausting the ranked queue. See
> [Phase 402](../../tools/gsmg/FINDINGS.md#phase-402----btcseedp91z-brainstorm-priority-6-final-controldata-digraph-machine-closed-negative-2026-08-25)
> and [its implementation](../../tools/gsmg/phase402_p91z_priority6_control_data_digraph_machine_audit.py).

Start with operations supplied by the geometry of two control bits and one
5x5 data coordinate. Rank typed outputs and exact authentication above English
likeness.

## Risks and failure modes

- The BCDE alternation is partly a mechanical consequence of the Bifid input
  alphabet and may support many accidental encodings.
- Attractive factorization is plentiful: `91=7x13`, `98=2x7x7`,
  `472=8x59`, and `570=2x3x5x19`. Geometry alone is not authentication.
- The column-major BIP39 mapping can be square-native while the selected window
  remains post-hoc.
- A checksum-valid mnemonic is expected when many mappings/windows are tried.
- English scoring is particularly vulnerable because earlier work selected
  `KMODEST` after inspecting several equivalent rails.
- Direct-key tests must count every case, mapping, endian, boundary, path, and
  public-key encoding.
- A valid padding result is not cryptographic authentication unless an exact
  plaintext structure or checksum also validates.
- The `14x14` relation may be a factorization coincidence unless it predicts
  the authenticated matrix substantially better than controls.
- Case is not carried by Bifid; arbitrary mixed-case expansion would be pure
  search-space inflation.

## Promotion contract

Before executing any item:

- [ ] name the exact source slice and byte normalization;
- [ ] freeze mappings, endian choices, routes, offsets, and consumers;
- [ ] count the complete family before observing outputs;
- [ ] include a planted positive test for every parser or address checker;
- [ ] define a shuffled/random control where a structural score is used;
- [ ] require an exact parser, checksum, address, decrypt, or independently
      predicted structure for promotion; and
- [ ] stop the family on a negative result rather than adding another mapping
      because an output looked close.

## Outcome

- Status: Priorities 1--6 (the entire ranked verification queue)
  executed and closed negative; the 100-item idea bank beyond this
  ranked queue remains an untested portfolio, but per this contract's
  own instruction, closing Priority 6 negative does not open a
  Priority 7
- Promoted phases: [Phase 397](../../tools/gsmg/FINDINGS.md#phase-397----btcseedp91z-brainstorm-priority-1-post-z-59-byte-control-channel-closed-negative-2026-08-25)
  (Priority 1), [Phase 398](../../tools/gsmg/FINDINGS.md#phase-398----btcseedp91z-brainstorm-priority-2-bip39-checksum-recalibration-under-the-two-grid-native-mappings-closed-negative-2026-08-25)
  (Priority 2), [Phase 399](../../tools/gsmg/FINDINGS.md#phase-399----btcseedp91z-brainstorm-priority-3-98-letter-to-14x14-coordinate-matrix-closed-negative-2026-08-25)
  (Priority 3), [Phase 400](../../tools/gsmg/FINDINGS.md#phase-400----btcseedp91z-brainstorm-priority-4-p90p91q472full-stream-as-direct-bitcoin-key-material-closed-negative-2026-08-25)
  (Priority 4), [Phase 401](../../tools/gsmg/FINDINGS.md#phase-401----btcseedp91z-brainstorm-priority-5-p91-against-the-youwon-bearing-dbbi-m91-difference-closed-negative-2026-08-25)
  (Priority 5), [Phase 402](../../tools/gsmg/FINDINGS.md#phase-402----btcseedp91z-brainstorm-priority-6-final-controldata-digraph-machine-closed-negative-2026-08-25)
  (Priority 6)
- Canonical findings changed: Phases 397--402 added; no prior phase
  retracted
- Highest-value next experiment: none within this contract's scope --
  the ranked queue is exhausted. Any further work on the 100-item idea
  bank requires a fresh, separately-frozen contract, not a quiet
  extension of this one.

