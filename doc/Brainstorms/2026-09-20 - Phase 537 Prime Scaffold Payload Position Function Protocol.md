# Phase 537 — is DBBI's non-host payload a function of its position?

Status at creation: protocol, written before any real-payload result is computed.
No oracle, password, or blob is involved.

## Claim and novelty

DBBI's hosts sit at prime *logical* positions (tokens 2, 3, 5, 7, ...). If the
string was built by rule, the remaining symbols may also be a rule of position,
for example a function of the composite index. Phase 536 tested the payload as
an encoding of existing text. Phases 529-530 tested it as password material.
Phase 45 zeroed prime positions. Phases 319 and 321 applied fixed layouts.
None tests the payload as an arithmetic function of its own coordinate. This is
an exploratory hypothesis, not a creator-selected recipe.

## Targets

Both complete prime-host parses of the exact DBBI string, parsed by an
independent solver in the Phase 537 script (cross-checked against Phase 525's
parser in a test): the 83-token parse gives 60 payload symbols, the 84-token
parse gives 61 including the final `e`. The two parses are separate targets.

For each payload symbol, three coordinates are recorded: the logical token
index `n`, the 1-based raw character offset `r`, and the payload ordinal `k`
(1..60 or 1..61, hosts skipped).

## Closed family

Base functions `g`, each evaluated on a coordinate value:

- identity, square, cube, triangular number
- divisor count, divisor sum, Euler totient
- prime factors with multiplicity, distinct prime factors, smallest prime
  factor, greatest prime factor, Möbius
- prime-counting function, distance back to the previous prime (0 for a
  prime), distance forward to the next prime, and the span from the greatest
  prime below the value to the least prime above it
- bit count, bit length, decimal digit sum
- raw coordinate only, four geometry functions on `r-1`: quotient and remainder
  by 13, quotient and remainder by 7 (DBBI is 7 x 13)

Value conventions, fixed here: d(1)=sigma(1)=phi(1)=1; Omega(1)=omega(1)=0;
spf(1)=gpf(1)=1; mu(1)=1; the greatest prime below 1 is 0, so the back
distance at 1 is 1 and the span at 1 is 2; the prime-counting function counts
primes up to and including the value.

Two variants per function: `g` itself, kept only if it takes at most nine
distinct values on the target, and `g mod 9`. Class vectors with at most nine
classes only. Coordinates: `n`, `r`, `k`; geometry on `r` only. Duplicate
class vectors within a target are collapsed and reported. No other moduli,
argument shifts or scalings, functions of two coordinates, or reversed order.
Any bijective relabeling of classes to `a..i` is allowed for free, by
equality-pattern matching, so shifts and multipliers of `g mod 9` are covered.

Payload alphabet is the nine symbols `a..i`; all nine occur in both payloads.

## Acceptance and stop rule

**Exact hit:** a class vector whose equality pattern equals the payload's
exactly (same partition of positions, nine classes, one bijection). Report
every exact cell. An exact hit is a candidate construction that would explain
all 91 raw symbols with the frozen hosts; it is not a solved password or proof
of intention. If found, freeze it for a separate downstream validation.

**Calibrated lead (weaker):** per cell, purity is the sum over classes of the
largest symbol count inside the class, divided by payload length. Standardize
each cell against its own histogram-preserving shuffle null, take the maximum
over the family, and compare with the same statistic recomputed on shuffled
payloads (family maximum per shuffle). A lead needs an add-one tail
at most 0.001 within a parse, and its class-to-symbol majority map must then
predict the 84-token parse's final `e` from a map fit on positions up to 83
(that check has chance about 1/9 and is reported, never used to rescue a
weak cell). A lead is not a promotion.

Zero exact hits and no lead in either parse closes only this family. Stop; do
not widen the function list, moduli, coordinates, or gate after seeing results.

## Controls

Null: 5,000 shuffles per parse, fixed seeds, histogram preserved.

Planted recovery, run before the real payload is scored: for eight
representative cells, spread over the three coordinates and both variants,
plant a payload from the function under a random bijective relabeling and
score it with the identical pipeline. Noise levels 0%, 10% and 25% of
positions replaced by uniform symbols, 20 fixed-seed trials each. Requirement:
every 0%-noise plant is an exact hit, and no plant fails to be indexed under
its own cell. Detection rate of the calibrated gate at 10% and 25% noise is
reported as power, not required. If the 0% requirement fails, stop without
scoring the real payload.

Power trials use 1,000 shuffles per scoring and the 83-token parse's
coordinates; the 0%-noise exact-recovery requirement is checked on both
parses. The real payload uses the 5,000-shuffle null. The shuffle null
standardizes each cell with its own shuffle mean and standard deviation and
the family maximum uses the same shuffles, which is slightly generous to the
null and disclosed here rather than corrected.

Also report, for context only, how many of 2,000 histogram-preserving
shuffles of the real payload are exact in some family cell (expected zero).

## Reproduction

```bash
python3 tools/gsmg/phase537_payload_position_function.py --self-test
python3 tools/gsmg/phase537_payload_position_function.py --run
```
