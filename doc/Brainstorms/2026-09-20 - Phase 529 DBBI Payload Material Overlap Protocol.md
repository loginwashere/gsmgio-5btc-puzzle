# Phase 529 — DBBI 84-parse payload material overlap protocol

Date: 2026-09-20  
Status: oracle-free bounded inventory

## Question

Do the exact payload objects isolated by Phase 528 produce genuinely untested
password materials under the project's already-established solved-boundary
form grammar?

## Frozen bases

Exactly five bases are admitted from Phase 528:

1. the 61-symbol full non-host residue;
2. the 35-symbol `b`-host payload rail;
3. the 25-symbol `be`-host payload rail;
4. `b` rail followed immediately by `be` rail; and
5. `be` rail followed immediately by `b` rail.

The historical 60-symbol residue is excluded because Phase 528 did not promote
it as a new 84-parse consequence. No reversal, separator, XOR, numeric list,
base conversion, rail interleaving, or tail-placement hedge is allowed.

## Expansion

Each base is passed unchanged to Phase 523's `expand_std(base, True)`, which
reuses the solved-boundary form registry: literal upper/lower case and the
existing raw/SHA-256-hex/double-SHA-256-hex forms with none/LF/CRLF suffixes.
Because all five bases contain letters only, alpha-stripped forms collapse to
the literal family. The expected scope is 18 forms per base and 90 unique
materials total.

## Comparators

Exact material membership is checked against:

- Phase 523's frozen historical coverage sources;
- standard expansions of every base actually executed in Phase 524;
- standard expansions of every base actually executed in Phase 527 (the
  Phase 526 base file); and
- Phase 478's actually submitted byte manifest.

Phase 523's 64-bit material key may be used as a rejection filter: unequal
keys prove unequal bytes. Any matching key must be rechecked against exact
material bytes before it counts as coverage.

## Stop rule

This phase performs no decryption. If zero fresh materials remain, close the
family as already covered. If fresh materials remain, record their exact
count and stop; a later phase must name and lock its consumer before any
oracle call. No result from this overlap audit licenses expanding the grammar.

