# Phase 505C-D shallow pair-screen results

Date: 2026-09-14
Status: development lanes complete; shallow selector closed

## Phase 505C

The locked exhaustive depth-4 pilot scored all `19P4 = 93,024` paths for all
36 assumed escape pairs in each of three synthetic rows. It completed 108 GPU
cells in approximately 103 seconds. The true-pair results were:

| true pair index | pair | rank | true minus best wrong |
|---:|:---:|---:|---:|
| 0 | `{a,b}` | 28/36 | -1.0485015312 |
| 17 | `{c,f}` | 24/36 | -0.9936736776 |
| 35 | `{h,i}` | 11/36 | -0.7163329892 |

All three winning wrong pairs achieved the identical normalized score
`-2.505883470978432` using exactly one quadgram window. The best paths under
the true pair used 8, 7, and 4 windows respectively. This localized the first
failure to a small-sample extreme-value effect, but did not establish that it
was the only problem.

Result SHA-256:
`f805de21b719f51b213271c3844c7496d7b8bceadc4bf569c17488fc83dc3bcb`.

## Phase 505D

The locked follow-up repeated the same 108 cells while preserving per-path
quadgram-window counts. It reranked all pairs at every minimum-window threshold
from 1 through 30.

- best rank-1 recovery at any threshold: 1/3 rows;
- best top-three recovery at any threshold: 1/3 rows;
- no threshold put all three true pairs in the top three;
- from 22 windows onward, at least one true pair had no eligible path.

The best isolated points were still inconsistent: at 15 windows pair index 17
ranked first while indices 0 and 35 ranked 7 and 23; at 16 windows index 0
ranked second while indices 17 and 35 ranked 15 and 11. This is not a stable
threshold region and cannot license a selector.

Result SHA-256:
`e0c604e6126ce37ffcf747bd4a416dd1af17534cdf98f759ed849c833c67ca8e`.
Its embedded execution-lock SHA-256
`bc197b909bc59eac80b5f34ef3ae44d67c342d0949344221907cd20b9d38678b`
matches the lock file exactly.

## Disposition

The exhaustive depth-4 maximum and its complete minimum-window correction
family are closed as blind escape-pair selectors. No FAED inference may be
drawn from their pair rankings.

The next bounded candidate is a depth-6-only selector. In the one completed
Phase-505B true-pair cell, the planted fragment ranked first under the
unrestricted-board objective at depth 6. A depth-6 selector would retain the
pair-balanced invariant path through depth 6 and stop before Phase 505B's
13.6-million-candidate depth-7 expansion. It requires its own timing cell and
three-row synthetic pilot before any broader matrix.
