# Phase 508 FAED depth-6 real-versus-null audit

Date: 2026-09-15

## Outcome

The Phase-506A depth-6 escape-pair selector fails its locked real-versus-null
diagnostic. The previously observed real FAED family maximum was
`-4.130477473427148`. Exact raw-symbol-multiset shuffles were each searched
over all 36 escape pairs with the same model, schedule, unrestricted-board
objective, and family-maximum statistic.

The first eight null maxima were below the real maximum. Null trial 8 scored
`-4.1205108615565855`, which is higher than the real value, and triggered the
pre-registered futility stop after 9 complete trials and 324 pair cells.

One tie-inclusive exceedance means that even if trials 9 through 199 all fell
below the real value, the best possible fixed-200 add-one value would be
`2/201 = 0.009950248756218905`. It cannot meet the project's strict
`p < 0.005` promotion bar. The descriptive add-one value at the stopping point
is `2/10 = 0.2`; because this was a sequential futility stop and the real
statistic had already been observed before the protocol, it is not presented
as a pristine confirmatory p-value.

## Frozen test

- Real statistic: Phase-506A maximum across all 36 pairs.
- Null: PCG32 Fisher-Yates shuffles preserving FAED's exact 570-symbol
  multiset, with seeds derived from `0x508A11` and the trial index.
- Per null: the unchanged Phase-505E pair-balanced model, depth-6 schedule,
  unrestricted 25-slot board fit, all 36 pairs, and their maximum score.
- Ties counted as exceedances.
- Stop at the first exceedance, or after 200 complete null trials.

The lock pins the protocol, Phase-508 script, six imported implementation
modules, Phase-506A lock and result, trained-model hash, FAED hash, and CUDA
binary hash.

## Trial maxima

| trial | null maximum | winning pair | exceeds real |
|---:|---:|:---:|:---:|
| 0 | -4.1930508233 | `{c,g}` | no |
| 1 | -4.1991343288 | `{g,i}` | no |
| 2 | -4.1439850683 | `{f,g}` | no |
| 3 | -4.1331493965 | `{g,i}` | no |
| 4 | -4.1563355270 | `{a,c}` | no |
| 5 | -4.1754465518 | `{e,g}` | no |
| 6 | -4.1566370622 | `{a,i}` | no |
| 7 | -4.1563983933 | `{d,e}` | no |
| 8 | -4.1205108616 | `{e,i}` | yes |

## Verification

All 324 pair checkpoints were reloaded fail-closed and checked against the
execution lock, shuffled-stream identity, trained-model identity, pair index,
and pair value. Each of the nine trial summaries was then recomputed from its
36 cells and compared byte-for-structure with the saved result. Six focused
unit tests pass.

- Execution-lock SHA-256:
  `8cd192d46b73bea0f83c2b0f32217bf7301e394bfe4996c4513b83a25b965858`
- Result SHA-256:
  `67b4e318166a10c5f48a2a4ab205995a54eb779e52fe30f2838f8b07553a94a0`

## Disposition and limits

This is a bounded negative for the Phase-505E/506A shallow pair-ranking proxy.
It means the Phase-506A ranking must not be used to prioritize further real
FAED pairs as though it were calibrated: an exact-multiset shuffle can attain
a higher 36-pair family maximum.

This is **not** a test or rejection of Model B. It does not evaluate a full
order recovery, plaintext decoding, other widths or directions, other board
objectives, or non-prose consumers. Phase 508 did not perform a new FAED
decode; it compared null searches with the already-recorded Phase-506A real
maximum. The result therefore supports stopping the width-19 top-pair sweep,
not extrapolating a negative to the other 30 pairs.

