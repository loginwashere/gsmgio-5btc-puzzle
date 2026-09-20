# Phase 537 — DBBI payload as a function of its own position

2026-09-20. Result: **bounded negative; no exact match and no calibrated lead**.

## Question

DBBI's prime hosts sit at prime logical positions. Is the remaining payload
(60 symbols in the 83-token parse, 61 including the final `e` in the 84-token
parse) an arithmetic function of its own coordinate? Phase 536 tested it as an
encoding of existing text, Phases 529-530 as password material, Phase 45 zeroed
prime positions, and Phases 319 and 321 applied fixed layouts. None tested a
position function. Exploratory; not a creator-selected recipe. Protocol:
[doc/Brainstorms/2026-09-20 - Phase 537 ... Protocol.md](Brainstorms/2026-09-20%20-%20Phase%20537%20Prime%20Scaffold%20Payload%20Position%20Function%20Protocol.md),
written before any real-payload result.

## Frozen family

Nineteen arithmetic functions (identity, square, cube, triangular, divisor
count and sum, totient, prime-factor counts, smallest and greatest prime
factor, Möbius, prime-counting, back and forward prime distance, prime span,
bit count and length, decimal digit sum) on three coordinates: logical index,
raw 1-based offset, and payload ordinal. Four 7 x 13 geometry functions on the
raw offset. Two variants each, `g` when it has at most nine distinct values and
`g mod 9`. Any bijective relabeling to `a..i` is free through equality-pattern
matching. After collapsing duplicate class vectors: **59 distinct cells per
parse, 15 with nine classes** (only those can be exact).

## Controls

Run before the real payload was scored. Exact recovery: for eight cells spread
over the three coordinates, plants with no noise were recovered as exact under
the correct cell in 20 of 20 trials, on both parses (16 cell-parse entries,
all passed). Calibrated-gate power, 83-token coordinates, 1,000 shuffles:
every one of the eight cells was flagged in 20 of 20 trials at both 10% and
25% noise. That detection sits at the smallest attainable tail (1/1,001), so
it shows the gate is not blind to family members with substantial noise, not a
fine power curve. On 2,000 shuffled real payloads per parse, none was exact in
any cell.

## Results

| Parse | Exact cells | Family-max z | Add-one tail (5,000 shuffles) | Lead |
|---|---:|---:|---:|---|
| 83 tokens, 60 symbols | 0 | 2.53 | 0.451 | no |
| 84 tokens, 61 symbols | 0 | 2.87 | 0.252 | no |

Top cells were raw-offset quotient by 7 mod 9 (purity 0.417 and 0.426), payload
ordinal prime-count mod 9, and logical prime span; their z-scores are within
what shuffled payloads produce as a family maximum. For context only, the
final `e` of the 84-token parse was predicted by the raw-offset cell (fit on
the other 60 symbols) and missed by the other two top cells. With three
tries and chance of about 1/9 each, that is unremarkable and was never used to
rescue a cell.

## Scope and stop

The payload is not a bijective relabeling of any listed function of its
logical index, raw offset or ordinal, and its best partial fits are not
distinguishable from shuffles. This rejects only this finite family. Other
moduli, argument shifts and scalings, functions of two coordinates,
non-injective symbol maps, and structure across payload symbols (for example
running sums or differences between neighbours) are outside it and do not
become next steps because this one failed. The registered stop rule is reached.

## Correction disclosed

The first version of the planting-cell picker returned five cells instead of
the protocol's eight. It was corrected to eight before any real payload was
scored, and its self-test check was pointed at the real coordinates after it
first failed on synthetic ones. The protocol text was amended once before any
run to fix value conventions and to state the power-trial shuffle count.

## Reproduction

```bash
python3 -m unittest tools.gsmg.test_phase537_payload_position_function
python3 tools/gsmg/phase537_payload_position_function.py --self-test
python3 tools/gsmg/phase537_payload_position_function.py --run
```

The result JSON records protocol, script and DBBI hashes, all seeds, every
control, and zero oracle calls. No encrypted blob, password or candidate list
is involved. The parser is independent and is cross-checked against Phase 525's
in the self-test. Nothing here needs the Downloads artifacts.
