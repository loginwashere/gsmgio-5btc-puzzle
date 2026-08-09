# GSMG First-Piece `ggn` Distinctiveness Audit

**Date:** 2026-08-09  
**Status:** Exact extraction verified; secp256k1 interpretation remains unforced.

## Question

The unique `#FEFEFE` cell has the independently verified hierarchical
descriptor:

```text
1  = number of FEFE cells
4  = its one-based bit position in the byte
21 = its one-based character position in gsmg.io/theseedisplanted
```

Flattening those three quantities into peer indices of the 24-character URL
produces `ggn` under one-based indexing. This audit asks whether that output is
distinctive enough to support the proposed `G,G,n -> secp256k1` reading.

The audit script is
`tools/gsmg/first_piece_ggn_distinctiveness_audit.py`. It uses no word list,
curve-symbol dictionary, password oracle, or Bitcoin-address oracle.

## Exact extraction

The two indexing conventions give:

| Convention | URL text | Colors | Blue=1 bits |
|---|---|---|---|
| One-based | `ggn` | `BBY` | `110` |
| Zero-based | `s.t` | `BYY` | `100` |

Thus `ggn` is exact, but it is convention-dependent. The hierarchical FEFE
descriptor independently uses one-based bit and character positions, which
makes one-based flattening reasonable; it does not prove that the three
hierarchical quantities should be flattened into peer URL indices at all.

## Bounded triple family

The clean comparison family is every increasing three-position choice from
the same 24-character URL:

```text
C(24,3) = 2,024 triples
```

The complete enumeration gives:

| Property | Count | Rate |
|---|---:|---:|
| Distinct emitted strings | 988 | — |
| Triple emits a string occurring at only one index triple | 519 | 25.64% |
| First two characters equal, third different (`xxy`) | 85 | 4.20% |
| Exactly two of three characters equal, any placement | 271 | 13.39% |
| First pair equal and third character globally unique in URL | 36 | 1.78% |
| Exact `ggn` | 1 | 0.0494% |

The sole exact `ggn` occurrence is `{1,4,21}` because the URL contains exactly
two `g` characters, at positions 1 and 4, and one `n`, at position 21.

The exact `1/2,024` rate would be appropriate only if `ggn` had been declared
as the target before inspecting the extraction. It was recognized afterward,
so that number is a descriptive fixed-target rate, not a discovery p-value.
Exact-output uniqueness is itself common: 519 of 2,024 triples, just over one
quarter, emit a three-character subsequence not emitted by any other triple.

The broader repeated-first-symbol structure is less common at 85/2,024, but
that pattern was also selected after observing `ggn`. Requiring the third
character to be globally unique lowers the count to 36, but “unique third” is
again a retrospective property and must not be treated as an independent
filter.

## Color channel does not confirm the choice

Across the same 2,024 increasing triples of the 15-blue/nine-yellow color
sequence:

```text
BBY occurs 546 times
BYY occurs 311 times
```

Therefore the one-based `BBY` and zero-based `BYY` outputs are ordinary color
patterns, not independent selectors for the text convention.

## What the curve reading adds

Turning literal lowercase `ggn` into the proposed curve construction requires
all of the following:

1. flatten the hierarchical FEFE descriptor into three peer URL indices;
2. choose one-based rather than zero-based indexing;
3. promote lowercase `g` to the conventional point symbol `G`;
4. parse the repeated `g` characters as two group operations;
5. interpret `n` specifically as the order of `G`;
6. introduce a scalar `k`, which is absent from `ggn`;
7. choose secp256k1 rather than the generic cyclic-group meaning.

The mathematical relation itself is correct:

```text
(n-k)G = -kG, when G has order n
```

But it is not specific to secp256k1; it holds in any cyclic group with
generator order `n`. The proposed two points also require the absent tokens
`k` and subtraction. Consequently, verifying the geometry would verify a
standard group identity, not show that `ggn` instructs the solver to use it.

## Verdict

Promote as exact facts:

1. the creator-grounded hierarchical tuple `{1,4,21}`;
2. the one-based flat extraction `ggn` and zero-based alternative `s.t`;
3. the unique location of exact `ggn` among increasing triples;
4. the complete bounded calibration above.

Do not promote `ggn` as a secp256k1 instruction, `kG/(n-k)G` as a selected
operation, or `1/2,024` as a valid post-hoc p-value. Keep the curve reading as
a narrative hypothesis awaiting an independent Bitcoin/curve operator clue
that supplies `k` or explicitly selects negation/order arithmetic.

## Reproduction

```bash
python3 tools/gsmg/first_piece_ggn_distinctiveness_audit.py --self-test
```
