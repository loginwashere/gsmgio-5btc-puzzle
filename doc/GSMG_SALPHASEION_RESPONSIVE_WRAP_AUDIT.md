# GSMG SalPhaseIon responsive-wrap audit

## Question

Could the SalPhaseIon textarea's intentionally spaced content and monospace
browser rendering create a width-dependent second layer, even though the HTML
contains no authored newlines?

Phase 220 answered the fixed-column question correctly but stated the broader
conclusion too strongly. Browser-generated rows are not source-authored, yet a
responsive or manually resized grid could still be intentional. Phase 229
tests that possibility without choosing a width from an output.

## Authenticated presentation

The raw page supplies:

- exactly one ASCII space between all 1,075 logical symbols;
- one `<textarea>` text node with zero newlines;
- inline `width: 100%; height: 200px`;
- no `cols`, `rows`, `wrap`, class, ID, or textarea font rule;
- only `body { font-family: 'arial'; }` as authored CSS.

The screenshot's monospace textarea appearance is therefore browser-default
form-control rendering, not an explicit creator font declaration. Viewport,
font metrics, zoom, and resizing can change the number of logical symbols per
visual row.

## Historical screenshot recovery

The retained `668x619` screenshot has SHA-256
`a3810ba24250c5a04908e1281c2202e73f7487f9d19f41bfd2c3e55fa9be57ed`.
It entered the public solver repository in commit `99bd811` on 2021-05-07;
it is evidence of a real historical rendering, not a creator-authored viewport.

Pixel analysis of the first three SalPhaseIon rows independently finds 45
monospaced glyph positions in each row. The normalized stream therefore renders
at that width as:

```text
23 complete rows x 45 symbols
1 final row x 40 symbols
= 1,075 symbols total
```

One exact alignment is real: FAED ends at logical offset `765 = 17x45`, so the
following `z` begins row 18, column 1.

## Boundary controls

Width 45 is not uniquely selected by that alignment. Across the predeclared
feasible family 20–100, FAED's endpoint lies on a row boundary at exactly:

```text
45, 51, 85
```

Other widths similarly align other known segment endpoints—for example width
91 aligns DBBI, while widths 39 and 65 align the matrix instruction. Boundary
alignment is expected whenever a chosen width divides an existing offset; it
cannot by itself identify a read direction or consumer.

## Responsive vocabulary test

Before inspecting grid output, the audit froze 25 words of length at least four
from the authenticated creator macro. Short words were excluded because the
`a-i` streams make two- and three-letter matches uninformative.

For every width 20–100 it searched:

- vertical columns;
- diagonals down-right;
- diagonals down-left;
- forward and reverse orientations.

Horizontal reads were excluded because they merely reproduce the source. The
matched null shuffles characters independently inside each of the thirteen
authenticated page segments, preserving segment lengths, character profiles,
case, and the complete width/direction search. The predeclared score is the
lexicographic tuple:

```text
(longest target word, number of distinct target words, total hits)
```

Result:

```text
real score:                 (0, 0, 0)
width-45 target hits:       0
all-width target hits:      0
segment-shuffle trials:     500
null maximum:               (5, 3, 7)
null >= real:               500/500
empirical p:                1.0
```

The real responsive grids contain no vertical or diagonal occurrence of any
frozen macro target at any tested width. Shuffled controls regularly generate
more apparent signal.

## Verdict

The user's presentation observation is mechanically correct and improves the
model: the authored spaces plus browser textarea behavior create real
width-dependent grids, and the historical screenshot fixes one concrete
45-column rendering. Phase 220 should not be read as proving that visual wraps
cannot matter in principle.

The tested consequence is nevertheless negative. Width 45 is community-
viewport evidence rather than a creator-fixed parameter, its FAED boundary
alignment has two rivals, and the complete bounded vertical/diagonal macro-
vocabulary family contains zero hits (`p=1.0`). No decoder or blob oracle is
authorized.

Reopen the responsive-layout branch only if primary evidence fixes a viewport,
column count, resize action, or a different exact read direction/output target.
Merely resizing until a word appears would select both the width and result
post hoc.

## Reproduction

```bash
python3 tools/gsmg/salphaseion_responsive_wrap_audit.py --self-test
python3 -m unittest tools/gsmg/test_recent_audits.py
```
