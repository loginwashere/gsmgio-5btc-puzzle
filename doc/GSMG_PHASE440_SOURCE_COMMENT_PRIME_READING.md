---
type: experiment
phase: 440
date: 2026-08-28
status: complete
result: only-inherited-or-flavor-tokens
classification: exploratory-not-instruction-licensed
script: tools/gsmg/phase440_source_comment_prime_reading.py
---

# Phase 440 — Source-Comment Prime Reading

The smallest natural prime-index family over the two historical source-only
comments produces no new instruction token and no structural collision.

The source is re-extracted from the Phase-439-pinned raw HTML. `global` joins
the comments before indexing; `reset` restarts positions in each comment.
`P` retains prime positions and `N` retains non-prime positions. Direction is
applied before indexing. Bases are the numeric values assigned to the first unit.

## Character-unit table

Only ASCII letters are retained and uppercased before indexing.

| Boundary | Base | Dir | Rail | Selected/90 | Output |
|---|---:|---|---|---:|---|
| global | 0 | F | P | 24 | `CEOEURDOUTEHEYAOXSOCLBYR` |
| global | 0 | F | N | 66 | `NITSEYOAOUNGODLCKLITLBUNNYUNTROUMDEITTTHENETTEPGODLUKITTLEUNNHUNTE` |
| global | 0 | R | P | 24 | `TNHNETKUOTETDMRYLTLGNOSN` |
| global | 0 | R | N | 66 | `REUYNUBLTILCLDOGPETSXNEHTOTIEAUOYETNUHNNUBETILKCUDOODUORAUYEEOTECI` |
| global | 1 | F | P | 24 | `ICTSOANGLTLYTRMTETOUKENE` |
| global | 1 | F | N | 66 | `NEOEEYUROUDOODUCKLITEBUNNHUNEYOUADEITOTHENXSTEPGODLCLITTLBUNYHUNTR` |
| global | 1 | R | P | 24 | `ETUYBLLCOSXOEAYHETUODUEI` |
| global | 1 | R | N | 66 | `RNHNNUETTIKULDOGPETTENEHTTTIDMUORETNUYNNUBLTILKCLDOGNUORAOYESOTECN` |
| reset | 0 | F | P | 27 | `CEOEURDOUTEHEUMDITETTOKIUHN` |
| reset | 0 | F | N | 63 | `NITSEYOAOUNGODLCKLITLBUNNYUNTRYOAETTOHNEXSEPGODLUCLTTLEBNNYUTER` |
| reset | 0 | R | P | 27 | `TNHNETKUORUOITNHNETKUOTETDM` |
| reset | 0 | R | N | 63 | `REUYNUBLTILCLDOGDNUOAOYEESTECNREUYNUBLTILCLDOGPETSXNEHTOTIEAUOY` |
| reset | 1 | F | P | 29 | `ICTSOANGLTLYTROUAEOHXSGCLBYUR` |
| reset | 1 | F | N | 61 | `NEOEEYUROUDOODUCKLITEBUNNHUNEYMDITTTENETTEPOODLUKITTLEUNNHNTE` |
| reset | 1 | R | P | 29 | `ETUYBLLCOOASCNETUYBLLCOSXOEAY` |
| reset | 1 | R | N | 61 | `RNHNNUETTIKULDOGDNURUOYEEOTEIRNHNNUETTIKULDOGPETTENEHTTTIDMUO` |

The lone fixed-vocabulary hit is `STEP` inside global/base-1/forward/non-prime.
It is inherited from the source phrase `NEXT STEP`, not a newly formed
instruction. None of the seven predeclared instruction tokens occurs.

## Word-unit table

Words are maximal ASCII alphabetic tokens. These outputs remain partly readable
by construction because the selection unit is a complete source word.

| Boundary | Base | Dir | Rail | Selected/22 | Output |
|---|---:|---|---|---:|---|
| global | 0 | F | P | 8 | `SEE YOU GOOD LITTLE MADE TO GOOD LITTLE` |
| global | 0 | F | N | 14 | `NICE TO AROUND LUCK BUNNY HUNTER YOU IT THE NEXT STEP LUCK BUNNY HUNTER` |
| global | 0 | R | P | 8 | `LITTLE LUCK STEP THE YOU BUNNY AROUND SEE` |
| global | 0 | R | N | 14 | `HUNTER BUNNY GOOD NEXT TO IT MADE HUNTER LITTLE LUCK GOOD YOU TO NICE` |
| global | 1 | F | P | 8 | `TO SEE AROUND LUCK YOU IT STEP LUCK` |
| global | 1 | F | N | 14 | `NICE YOU GOOD LITTLE BUNNY HUNTER MADE TO THE NEXT GOOD LITTLE BUNNY HUNTER` |
| global | 1 | R | P | 8 | `BUNNY LITTLE GOOD NEXT MADE HUNTER GOOD YOU` |
| global | 1 | R | N | 14 | `HUNTER LUCK STEP THE TO IT YOU BUNNY LITTLE LUCK AROUND SEE TO NICE` |
| reset | 0 | F | P | 9 | `SEE YOU GOOD LITTLE IT TO NEXT GOOD HUNTER` |
| reset | 0 | F | N | 13 | `NICE TO AROUND LUCK BUNNY HUNTER YOU MADE THE STEP LUCK LITTLE BUNNY` |
| reset | 0 | R | P | 9 | `LITTLE LUCK AROUND SEE LITTLE LUCK STEP THE YOU` |
| reset | 0 | R | N | 13 | `HUNTER BUNNY GOOD YOU TO NICE HUNTER BUNNY GOOD NEXT TO IT MADE` |
| reset | 1 | F | P | 9 | `TO SEE AROUND LUCK MADE IT THE STEP BUNNY` |
| reset | 1 | F | N | 13 | `NICE YOU GOOD LITTLE BUNNY HUNTER YOU TO NEXT GOOD LUCK LITTLE HUNTER` |
| reset | 1 | R | P | 9 | `BUNNY LITTLE GOOD YOU BUNNY LITTLE GOOD NEXT MADE` |
| reset | 1 | R | N | 13 | `HUNTER LUCK AROUND SEE TO NICE HUNTER LUCK STEP THE TO IT YOU` |

Every vocabulary match here is one of the already-present flavor/progress words
`GOOD`, `LUCK`, `RABBIT`, `HUNTER`, `NEXT`, or `STEP`. (`RABBIT` itself is not
selected intact in these rows.) There is no new `SOURCE`, `CODE`, `PRIME`,
`KEY`, `PASSWORD`, `BLUE`, or `YELLOW`.

## Controls

- 32/32 predeclared rows were emitted.
- Prime and non-prime rails partition every source exactly.
- No two distinct outputs are exactly equal.
- No two distinct outputs are reverses of one another.
- Character-output vowel fractions range from 0.2083 to 0.5185 and IoC from
  0.0394 to 0.0912; these descriptive values do not select a row.
- Full SHA-256, vowel fraction, IoC, vocabulary counts, and selected-word arrays
  for every row are retained in `phase440_result.json`.

## Verdict

Disposition: `only_inherited_or_flavor_tokens`.

The table supplies no evidence that the comments are the intended operand and
no reason to promote one base, direction, boundary, or rail. Phase 439 remains
gated.

No password material, oracle call, Docker action, or GPU interaction occurred.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase440_source_comment_prime_reading.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase440_source_comment_prime_reading.py \
  --output tools/gsmg/phase440_result.json
```
