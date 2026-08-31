# Second-Prime `matrixsumlist` Audit

**Date:** 2026-08-31  
**Verdict:** strong recognition candidate; direct password oracles negative

## Fixed continuation

The rotation-grille audit independently fixes the second inverse prime as
`311027`. Reusing the existing six-digit-prime `matrixsumlist` grammar gives:

```text
311027
-> [[3,1,1],
    [0,2,7]]
-> total followed by row sums
-> [14,5,9]
```

Forward one-based indexing into the frozen Architect speech before `choice`
then gives:

```text
14 = FLAW
 5 = LAST
 9 = OF

initial letters = FLO
last letters    = WTF
reverse         = FTW
```

This consumes the creator macro unusually cleanly:

```text
yellowblueprimes
-> 574061 and 311027
matrixsumlist
-> [23,16,7] and [14,5,9]
lastwordsbeforearchichoice
-> last letters of FLAW / LAST / OF = WTF
yinyang
-> WTF <-> FTW
```

`WTF` and `FTW` are exact reversals, and their conventional readings have
opposing negative/positive valence. The semantic interpretation remains a
recognition judgment, not creator-authored text. Neither acronym or expansion
appears in the creator's Telegram corpus.

The words at positions 5, 9, and 14 all lie in the first Architect block,
which the existing source audit found word-for-word stable between the frozen
screenplay and the independently checked film quotation.

## Complete bounded controls

For two rows of three decimal digits, each positive row sum can be `1..27`.
The complete one-based family therefore has `27 x 27 = 729` triples:

```text
(row1 + row2, row1, row2)
```

Exactly one of those 729 triples selects Architect words whose final letters
are `WTF`:

```text
[14,5,9] -> FLAW / LAST / OF -> WTF
```

Across the complete population of 68,906 six-digit primes, 78 have decimal
digit row sums `[14,5,9]`, a descriptive exact-target rate of:

```text
78 / 68,906 = 0.001131977
```

This cannot be treated as a preregistered p-value: `WTF` and its `FTW`
reversal were recognized after deriving `311027`. The result is strong enough
to retain as a recognition checkpoint, not to declare the chain solved.

## One rule across both primes and their sum

Adding the two digit matrices elementwise introduces no decimal carries:

```text
5 7 4     3 1 1     8 8 5
0 6 1  +  0 2 7  =  0 8 8

574061 + 311027 = 885088
combined matrix sum list = [37,21,16]
```

A single hierarchical edge rule can now be applied to all three matrices:
use the total-selected word's beginning and end as an outer frame, with the
two row-selected word beginnings inside it.

| Input | Sum list | Architect words | Framed output |
|---|---|---|---|
| 574061 | `[23,16,7]` | BOTH / ULTIMATELY / THE | `B + UT + H = BUTH` |
| 311027 | `[14,5,9]` | FLAW / LAST / OF | `F + LO + W = FLOW` |
| their sum | `[37,21,16]` | TAKE / REVEALED / ULTIMATELY | `T + RU + E = TRUE` |

This consolidates rather than discards prior observations:

- `BUTH` segments naturally as the established boundary `BUT` plus `H`;
- `FLOW` reverses to the ordinary word `WOLF`, another literal yin-yang
  reversal alongside `WTF <-> FTW`;
- `TRUE` is exact creator vocabulary from
  `verylaststepisatruegiveaway`, rather than an inferred synonym.

Across all 729 positive row-sum pairs for the second matrix, 714 keep both the
second and combined lists within the frozen Architect source. Exactly one pair,
`(5,9)`, produces both second-frame `FLOW` and combined-frame `TRUE`.
Across the complete six-digit-prime population this is the same 78/68,906
family as the `WTF` result, so the echoes are linked consequences rather than
independent p-values. Only forward one-based indexing gives these words.

The frame role is also exhaustively controlled. Keeping the two inner words
in their original order, each of the three selected words was assigned the
outer-frame role:

| Frame role | 574061 output | 311027 output | Combined output | FLOW/TRUE joint hits across 729 |
|---|---|---|---|---:|
| total word | `BUTH` | `FLOW` | `TRUE` | 1 |
| row 1 word | `UBTY` | `LFOT` | `RTUD` | 0 |
| row 2 word | `TBUE` | `OFLF` | `UTRY` | 0 |

The row-1 frame role produces `TRUE` once elsewhere, at row sums `(3,9)`,
but its corresponding second-prime frame is `UTOS`, not `FLOW`; it therefore
has no joint hit. The row-2 role produces neither target. This makes the
total-word frame assignment uniquely successful within the complete
three-role family, while retaining the caveat that this family was formalized
after the outputs were observed.

## Direct consumer test

The candidate family was frozen to direct outputs and their reversals:

- `FLO` / `OLF`;
- `WTF` / `FTW`;
- `FLAWLASTOF` / `OFLASTFLAW`;
- `WHAT THE FUCK` / `FOR THE WIN`;
- `311027`, `04BEF3`, and `1459`;
- `BUTH` / `BUT H`, `FLOW` / `WOLF`, and `TRUE`;
- `BUTHFLOWTRUE` and its spaced form.

Project-standard case/spacing normalization gives 40 unique byte forms.
Against all four tracked blobs—SALPH, COSMIC, P32TRAILING, and URLBLOB—the
existing oracle families ran:

| Family | Attempts | Hits |
|---|---:|---:|
| CBC | 3,840 | 0 |
| ECB | 1,920 | 0 |
| Stream modes | 5,760 | 0 |
| AES Key Wrap | 7,680 | 0 |

Therefore the framed and `WTF`/`FTW` outputs should currently be treated as
control flow or recognition checkpoints, not demonstrated blob passwords.

## Reproduction

```bash
python3 tools/gsmg/second_prime_matrixsumlist_audit.py
python3 tools/gsmg/second_prime_matrixsumlist_audit.py --oracle
python3 -m unittest discover -s tools/gsmg -p 'test_second_prime_matrixsumlist_audit.py'
```
