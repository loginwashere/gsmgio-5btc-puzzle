# Authenticated `THEFLOWER` Prefix Checkpoint

**Date:** 2026-09-01  
**Verdict:** strong closed-loop recognition checkpoint; not a new password

## Result

The two-prime matrix chain gives the framed outputs:

```text
second prime:       FLOW
elementwise sum:    TRUE
```

Treating `yinyang` as a binary odd/even split gives:

```text
TRUE odd positions:   TU
TRUE even positions:  RE
reverse even rail:    ER

FLOW + ER = FLOWER
```

The first-prime Architect selection is:

```text
BOTH / ULTIMATELY / THE
```

Using its literal selected word `THE` as a prefix gives:

```text
THE + FLOWER = THEFLOWER
```

This target was fixed years before the present construction. It is the exact
opening of the verified Phase-1 credential:

```text
theflowerblossomsthroughwhatseemstobeaconcretesurface
```

The credential's exact SHA-256 is independently pinned as:

```text
5ac407837447fba24ba2802e4d1e9aecb4580aa29fef1088cc387c180b746f75
```

This creates a closed loop from the later creator macro back to an earlier
authenticated solved-stage output. It is consistent with
`itsinfrontofyoureyesbutyourenotseeingit`: the result points to material the
solver has already seen, rather than supplying an unseen blob password.

## Frozen composition family

No single favorable orientation is considered alone. For `FLOW` and `TRUE`,
the audit exhausts:

- `FLOW` forward or reversed (`WOLF`);
- odd or even positions of `TRUE`;
- each parity rail forward or reversed;
- rail appended to or prepended before the base.

This gives 16 distinct cores:

```text
FLOWTU  TUFLOW  FLOWUT  UTFLOW
FLOWRE  REFLOW  FLOWER  ERFLOW
WOLFTU  TUWOLF  WOLFUT  UTWOLF
WOLFRE  REWOLF  WOLFER  ERWOLF
```

Exactly one is `FLOWER`: forward `FLOW`, reversed even rail `ER`, appended.

The affix family then uses every one of the nine selected Architect-word
occurrences from the first-prime, second-prime, and combined selections, on
both the prefix and suffix side. That gives 288 labeled variants, representing
256 unique strings. Exactly one is `THEFLOWER`: the first selection's literal
`THE` prefixed to `FLOWER`.

## Complete row-sum control

The same family was run over all 729 positive second-matrix row-sum pairs.
Fifteen pairs are explicitly unindexable because their combined total exceeds
the frozen 72-token Architect source; 714 remain.

For every indexable pair the audit generates:

```text
16 parity/reversal/join cores
x 9 selected word occurrences
x 2 affix sides
= 288 labeled variants
```

The complete result is:

| Quantity | Count |
|---|---:|
| Indexable row-sum pairs | 714 |
| Unindexable pairs | 15 |
| Core variants | 11,424 |
| `FLOWER` core hits | 1 |
| Affixed labeled variants | 205,632 |
| `THEFLOWER` hits | 1 |

The sole hit is the actual second-prime row split `(5,9)`.

These counts are descriptive controls, not preregistered probabilities. The
odd/even/reversal/affix family was formalized after noticing `FLOW`, `TRUE`,
and the known flower credential. The result should be promoted as a strong
recognition checkpoint because the target is authenticated and pre-existing,
not treated as a discovery p-value.

## Direct consumer control

The six project-standard case/spacing forms of `FLOWER`, `THEFLOWER`, and
`THE FLOWER` were tested against SALPH, COSMIC, P32TRAILING, and URLBLOB:

| Family | Attempts | Hits |
|---|---:|---:|
| CBC | 576 | 0 |
| ECB | 288 | 0 |
| Stream modes | 864 | 0 |
| AES Key Wrap | 1,152 | 0 |

This negative is expected for a loop back to an already-used credential. It
does not weaken the prefix match, but it rules out treating the short prefix
as a demonstrated password for the current open blobs.

## Reproduction

```bash
python3 tools/gsmg/flower_prefix_checkpoint_audit.py
python3 tools/gsmg/flower_prefix_checkpoint_audit.py --oracle
python3 -m unittest discover -s tools/gsmg -p 'test_flower_prefix_checkpoint_audit.py'
```
