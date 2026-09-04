# Phase 476 — P91 as a second Bifid key over Q472

Date: 2026-09-03  
Outcome: `closed_negative`

## Conclusion

The natural ordered cascade does not reveal plaintext or unusual English
structure:

```text
FAED
  -- DBBI-derived square, decrypt as period 570 --> BTCSEED | P91 | Q472
  -- P91-derived square, decrypt Q472 as period 472 --> candidate
```

The real candidate scores `-3790.6207793` under the frozen whole-string
English quadgram statistic. It performs worse than most controls:

| Control | At least as English-like | Add-one p |
|---|---:|---:|
| Upstream FAED shuffle; regenerate P91 square and Q472 together | 78,038 / 100,000 | 0.7803821962 |
| Fixed observed P91 square; shuffle Q472 order | 67,581 / 100,000 | 0.6758132419 |

The primary frozen promotion threshold was `0.005`. Neither result is close.
No frozen Phase-396 target keyword occurs in the output.

## Exact construction

The first DBBI-derived square remains:

```text
DBIFH
CEGAK
LMNOP
QRSTU
VWXYZ
```

Phase 386 supplies the already-frozen P91:

```text
DEOEMCKEADHBSCHDKBDCSDKDVBXCPCOCHCRDICIBQEEBDDBCNDSBDCPDGCPDNCNCSESCGDDCLENBMCUDUCQCACDELDZ
```

Deduplicating all of it in first-occurrence order and appending unused no-J
letters gives this exact second keyed alphabet:

```text
DEOMCKAHBSVXPRIQNGLUZFTWY
```

or square:

```text
DEOMC
KAHBS
VXPRI
QNGLU
ZFTWY
```

Q472 was then Bifid-decrypted as one complete 472-character block using the
same row-column convention. Its output begins:

```text
DSGGDZMNEBTBEMFBDAAWDCMXDETLDFHMKNZWDFLWKQFUKQAADKBWKNWNKULKEBDGDSEODKBKDDMPALPNDFRPKUUXKULCDFDX
```

The full output SHA-256 is
`4aa436b32f4b01a27245b9ab1327967b1f5628f66887b8514b37b4345071e95b`.

## What the two controls establish

The primary control preserves the construction's dependency: each exact-FAED-
multiset permutation is first decoded through the fixed DBBI square, after
which its synthetic P91 creates its own second square and its coupled Q472 is
decoded. The observed candidate lies only around the 22nd percentile for
English-likeness under this pipeline.

The secondary control holds the observed P91 square fixed while randomizing
only Q472's exact letters. It asks the narrower message/key question. The real
Q472 ordering still lies only around the 32nd percentile. Thus neither the
whole layered construction nor Q472's order given the proposed key shows a
positive signal.

## Scope boundary

This closes idea-bank item 83 and the single non-circular ordered schedule
selected by the data: DBBI first, then the P91 that the DBBI pass creates.
It does not claim to execute the underspecified full item 84 phrase “apply
DBBI, M91, and P91 as three ordered key schedules.” No source defines its
operand, whether each stage encrypts or decrypts, its periods, or whether all
six permutations are intended. Adding those axes after this result would be a
new search family requiring an independent selector and fresh control.

The result also remains conditional on Phase 386's selected full-period
decoder and the post-observation P91/Q472 boundary. Upstream controls were not
conditioned on reproducing `BTCSEED` and terminal `Z`.

## Verification

- Phase 386 P91 and Q472 are reproduced byte for byte.
- The dynamic vectorized square equals scalar `build_grid(P91)`.
- Vectorized and scalar second-pass outputs and quadgram scores agree.
- Bifid encryption returns the exact original Q472.
- A planted 472-character English/SATOSHI second pass round-trips and scores.
- No password, ciphertext-oracle, or Bitcoin endpoint calls were made.

Artifacts:

- `tools/gsmg/phase476_p91_second_bifid_key_audit.py`
- `tools/gsmg/test_phase476_p91_second_bifid_key_audit.py`
- `tools/gsmg/phase476_result.json`
- `doc/Brainstorms/2026-09-03 - Phase 476 P91 Second Bifid Key Protocol.md`
