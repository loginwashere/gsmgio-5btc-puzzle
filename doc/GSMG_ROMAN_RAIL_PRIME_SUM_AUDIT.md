# GSMG Roman Rail Prime-Sum Audit

Date: 2026-08-13  
Script: `tools/gsmg/roman_rail_prime_sum_audit.py`  
Status: exact bounded correspondence; corroboration only

## Observation

Keeping only canonical Roman-numeral letters from the two authenticated
stream prefixes and prefixing the title's `C` gives:

```text
DBBI -> DI; C + DI -> CDI = 401
FAED -> D;  C + D  -> CD  = 400
```

The resulting values preserve the fitted color-prime ordering: blue `401`,
yellow `400`.

## Bounded family

The audit tests both DBBI/FAED color polarities and seven nonredundant title
contexts: no title letters, or every nonempty order-preserving subset of `CD`
as a prefix or suffix. Strict canonical Roman syntax is required.

Exactly one of 14 configurations produces ordered `(401,400)`: DBBI/FAED
with `C` prefixed, yielding `CDI/CD`.

## Sensitivity control

Across 13 disclosed authenticated/high-salience labels, all 156 ordered token
pairs, and the same seven title contexts (1,092 configurations), two hits
occur:

```text
DBBI / FAED    + prefix C  -> CDI / CD -> 401 / 400
yinyang / FEFE + prefix CD -> CDI / CD -> 401 / 400
```

The second result occurs because `roman(yinyang)=I` and `roman(FEFE)` is
empty. These counts describe the bounded search; they are not chance
probabilities because the control vocabulary is salient rather than random.

## Verdict

The DBBI/FAED construction is exact and is the strongest Roman-numeral lead
found so far, but it is not a solved transition:

- no creator clue selects Roman-letter filtering;
- no clue selects title `C` alone;
- a second relevant-token construction produces the same numeral pair;
- FEFE's fitted value `73` remains unexplained.

G-PRIME-001 therefore remains parked. Reopen if evidence selects the Roman
projection and title `C`, or if the same mechanism accounts for FEFE/73.
