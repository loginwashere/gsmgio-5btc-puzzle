# First-Piece `BaTcH` / BATCH Gate Audit

## Scope

This audit tests Point 14's construction separately from its promotion gate:

```text
#383838 channel value 56 -> atomic symbol Ba
#383838 pixel count   43 -> atomic symbol Tc
Architect end rail   hye -> initial H
                              BaTcH -> BATCH
```

The source quantities and Architect rails are reconstructed from the same
authenticated inputs used by the preceding audits. No password, word-list, or
ciphertext oracle is run.

## Exact reconstruction

The independently selected shadow layer is `#383838`. Its repeated channel
byte is `0x38 = 56`, and its two sampled rows contain 25 and 18 pixels, for an
exact total of 43. In atomic-number order:

```text
56 -> Ba
43 -> Tc
```

The established `[23,16,7]` forward-one Architect indexing gives beginnings
`but` and endings `hye`. Taking the initial `h` of the latter and promoting it
to the exact element symbol `H` gives:

```text
Ba + Tc + H = BaTcH
casefold(BaTcH) = batch
```

The same end rail still reconstructs `hye + [23,16,7] -> eol`, so BATCH has a
natural computing-language association with the separately decoded `enter`
instruction. That association is semantic; the authenticated decoded
instruction vocabulary contains `matrixsumlist`, `enter`, the two decimal
instructions, and the SHA phrases, but no literal `batch`.

## Ordering calibration

The three symbols have six distinct orders. Exactly one casefolds to `batch`:

```text
BaTcH  batch    BaHTc  bahtc
TcBaH  tcbah    TcHBa  tchba
HBaTc  hbatc    HTcBa  htcba
```

This is a fixed-target rate of `1/6`, not a post-hoc p-value. If artifact stage
order is allowed to force `H` last, only `BaTcH` and `TcBaH` remain, so the
rate is `1/2`; however, no clue chooses channel value before pixel count.

## What later `OCBe` evidence changes

The exact-case G-shadow consumer independently yields `OCBe`, uniquely parsed
as `O, C, Be` and mapped to atomic numbers `8,6,4`. This establishes that
chemical element symbols are genuine native puzzle vocabulary. It improves
the plausibility of Point 14 relative to when it was first proposed.

It does **not** select the reverse operator used here. `OCBe` starts with
symbols and reads their atomic numbers; Point 14 starts with two integers and
chooses to turn them into symbols. Every integer from 1 through 118 has such a
symbol, so the conversions `56 -> Ba` and `43 -> Tc` are guaranteed once that
operator is chosen. The word-forming order is the informative part.

## Strict gate

| Requirement | Result |
|---|---:|
| Source quantities are exact | pass |
| Element vocabulary exists elsewhere | pass |
| A clue selects inverse atomic-number lookup | fail |
| A clue selects value before count | fail |
| A clue selects only the initial `H` from `hye` | fail |
| A clue selects BATCH as execution grammar | fail |

## Verdict

`BaTcH -> BATCH` is an exact and attractive rebus, now supported by genuine
element-symbol vocabulary elsewhere in the same phase. It remains **closed as
an executable instruction** because its three critical operators—numeric
inversion, source order, and singleton-H extraction—are not selected. Retain
it as a high-quality recognition/checkpoint hypothesis. Reopen it only if a
new clue explicitly asks for atomic numbers/elements in the inverse direction,
orders value before count, isolates H, or names batch/command execution.

Reproduce with:

```bash
python3 tools/gsmg/first_piece_batch_rebus_gate_audit.py --self-test
```
