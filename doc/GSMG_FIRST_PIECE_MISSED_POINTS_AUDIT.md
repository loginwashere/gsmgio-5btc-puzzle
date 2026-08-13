# GSMG First-Piece Missed-Points Audit

## Scope

This closes the three executions left open in
`GSMG_FIRST_PIECE_PIXEL_BRAINSTORM.md`: Points 7, 8, and 15. The families
were fixed before inspection of their outputs, and no blob oracle or private-
key search was run.

## Point 7 — repeated-gray channel values

The Phase-149 numeric registry now includes the two independently established
channel bytes:

```text
#FEFEFE -> 254 -> 0xFE (not printable ASCII)
#383838 ->  56 -> 0x38 -> ASCII "8"
```

The exact operation family is unchanged: sum, absolute difference, product,
both decimal concatenations, and exact integer division. Algebraic
restatements of one additive or multiplicative triple count once. Against the
fixed original 20-number registry:

```text
254: 91 + 163 = 254
 56:  7 +  56 = 63
      24 +  56 = 80
```

Calibration over every possible byte value `0..255` is negative. At least one
deduplicated relation occurs for 147/256 byte values; at least two occur for
70/256. Thus `254`'s one relation has byte-family tail rate `147/256 ≈ 0.574`,
and `56`'s two have `70/256 ≈ 0.273`. The anticipated `254-163=91` is exact,
but not distinctive in this comparison family.

Executable audit:
`tools/gsmg/first_piece_marker_numeric_control_audit.py`.

## Point 8 — native 14×14 matrix sum lists

Using the already-fixed bit rule `black/blue=1`,
`white/yellow/FEFE=0`, the literal matrix gives:

```text
rows:    6 10 8 7 6 6 5 4 9 9 7 8 7 9
A1Z26:   F  J H G F F E D I I G H G I

columns: 8 10 8 10 8 7 3 6 7 5 9 6 6 8
A1Z26:   H  J H  J H G C F G E I F F H

total: 101
```

The total is simply the popcount of the already-decoded 24-byte URL and is
therefore not independent evidence. All eight D4 orientations only swap or
reverse the same row/column data, yielding four directed lists. Neither native
list is plaintext, and no clue selects a later consumer. The exact lists are
retained as source facts; the proposed alternative `matrixsumlist` route is
closed pending an explicit consumer.

Executable audit:
`tools/gsmg/first_piece_native_matrixsumlist_audit.py`.

## Point 15 — `G` as secp256k1 generator/operator

The exact `#383838`-selected rails and G-removed operands are:

```text
GSGO5BCPUCG -> SO5BCPUC   (row-local G count 4)
GMGC9g2cPBe -> MC9g2cPBe  (row-local G count 2)
```

Neither operand is a complete decimal or hexadecimal scalar. The original
text has five uppercase-G anchors; only the two in the Bitcoin address touch
a digit, both touching the address's literal `1`. In the selected streams no
G has a numeric neighbor. There is therefore no consistent infix/prefix
scalar grammar.

The predeclared count uses give:

```text
selectors, zero-/one-based: banner C/B; address 9/C
chunks: SO5B | CPUC; MC | 9g | 2c | PB | e
stride family: 64 unique joined outputs, zero established clue-term hits
```

Treating only the independently measured counts as literal secp256k1 scalars
produces ordinary keys:

```text
2G compressed address:   1cMh228HTCiwS8ZsaakH8A8wze1JR5ZsP
2G uncompressed address: 1LagHJk2FyCV2VzrNHVqg3gYG4TSYwDV4m
4G compressed address:   1JtK9CQw1syfWj1WtFMWomrYdV3W2tWBF9
4G uncompressed address: 1MnyqgrXCmcWJHBYEsAWf7oMyqJAS81eC
```

None equals the Stage-0 address
`1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`. Arbitrary character-to-scalar folding,
new scalar combinations, or private-key search would exceed the proposed
family. Point 15 is therefore closed pending an explicit scalar syntax or
curve-operation instruction.

Executable audit:
`tools/gsmg/first_piece_g_operator_gate_audit.py`.

## Verdict

All 25 numbered points in the first-piece pixel brainstorm now have a bounded
disposition. These final three checks are negative and produce no candidate
that earns a ciphertext oracle. Reopen them only with a new external clue
selecting a numeric relation, a native-matrix consumer, or a scalar/curve
grammar.
