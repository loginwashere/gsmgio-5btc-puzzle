# `BLOSSOMS` Derivation Boundary Audit

**Date:** 2026-09-01  
**Verdict:** the authenticated next word is visible only through an unbounded,
target-driven walk; it is not derived by the present matrix grammar

## Why test `BLOSSOMS`

The verified Phase-1 credential begins:

```text
THEFLOWERBLOSSOMS...
```

The two-prime chain independently recovers `THEFLOWER`. The natural next test
is whether its matrix operations also force the already-authenticated next
word `BLOSSOMS`.

They do not under the established grammar. The three frame values are:

```text
BUTH / FLOW / TRUE
```

These values, their reversals, and every odd/even rail have no letter `S`.
Consequently, no composition restricted to that closed family can spell
`BLOSSOMS`.

## Smallest matrix-native extension

Column sums are the smallest natural extension of the already-used total and
row sums. Reading total, rows, and columns through the same frozen Architect
word list gives:

| Matrix | Indices: total / rows / columns | Selected words | Initials | Endings |
|---|---|---|---|---|
| `574061` | `23 / 16 7 / 5 13 5` | BOTH / ULTIMATELY / THE / LAST / FUNDAMENTAL / LAST | BUTLFL | HYETLT |
| `311027` | `14 / 5 9 / 3 3 8` | FLAW / LAST / OF / US / US / MOMENT | FLOUUM | WTFSST |
| elementwise sum | `37 / 21 16 / 8 16 13` | TAKE / REVEALED / ULTIMATELY / MOMENT / ULTIMATELY / FUNDAMENTAL | TRUMUF | EDYTYL |

The second matrix's column endings finally supply `S`, but that observation
alone does not define an ordered extraction rule.

## Bounded no-reuse endpoint sweep

The audit tests the minimal cross-matrix node set capable of supplying both
the initial `B` and the new `S`:

```text
first total:     BOTH
second rows:     LAST / OF
second columns:  US / US / MOMENT
```

It exhausts:

- all six orders of the total, rows, and columns blocks;
- both row directions;
- all six labeled column permutations;
- every choice of two of the six words to emit both endpoints;
- both directions for those two endpoint pairs;
- initial or ending for each remaining word.

Exactly two words must emit two letters because six non-repeated words must
produce the eight-letter target. The full labeled count is:

```text
6 x 2 x 6 x C(6,2) x 2^2 x 2^4 = 69,120
```

The 69,120 labeled variants collapse to 31,264 distinct strings. Result:
**zero `BLOSSOMS` hits**.

## Why the hand spelling is not a result

Once the target is known, it is easy to manufacture this walk:

```text
BOTH[B] LAST[L] OF[O] US[S] US[S] OF[O] MOMENT[M] US[S]
= BLOSSOMS
```

But it visits `OF` twice and `US` three times, chooses endpoints one by one,
and supplies no matrix-defined traversal that demands those revisits. This is
precisely the extra freedom excluded by the bounded sweep. Reporting the walk
as a derivation would therefore be circular: the known target determines the
path.

## Denis-corpus control

A text sweep of all 1,492 indexed Denis messages found no independent
instruction that fixes this traversal or permits node reuse. The superficially
relevant matches do not do that:

- message `38137`, “This is how to revisit it,” refers to replaying the solved
  URL/decryption process;
- in message `68058`, “sum rows and columns” is quoted text from another user;
  Denis's own response is only “Wow, code golf!”;
- message `68873` riffs on “a flower blossoms” after the Phase-1 credential was
  already public in the same corpus.

These are not a preregistered ordering rule for `BOTH / LAST / OF / US / US /
MOMENT`.

## Conclusion

`THEFLOWER` remains a strong authenticated closed-loop checkpoint. The current
chain does not continue mechanically to `BLOSSOMS`. A legitimate continuation
would need an independently motivated traversal or reuse instruction fixed
without reference to the password; absent that, this is the correct stopping
boundary.

## Reproduction

```bash
python3 tools/gsmg/blossoms_boundary_audit.py
python3 -m unittest discover -s tools/gsmg -p 'test_blossoms_boundary_audit.py'
```
