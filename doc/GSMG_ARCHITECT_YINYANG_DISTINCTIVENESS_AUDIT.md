# Architect yin-yang distinctiveness audit

The `[23,16,7]` Architect extraction has two logically separate parts. The
first is unusually well checked: forward-one indexing is stable across the
different film and screenplay wording, selects `BOTH / ULTIMATELY / THE`, and
their initials `BUT` equal the literal next spoken word after `choice`.

The second part formerly filtered `BUT/HYE` to the native `a-i` alphabet,
giving `B/HE`, and called `{b,h,e}` a yin-yang state because `b <-> h` while
`e` is fixed. This audit measures that second claim independently.

A strict positional involution cannot map the rails: after filtering they have
different lengths (`B` versus `HE`). The historical reading therefore needs a
special rule: map the one retained initial to the first retained final, then
treat the extra final `e` as a fixed point. That rule does fit the selected
output, but it is not distinctive.

The film and screenplay share identical words at 34 of the first 69 positions.
Across all 35,904 ordered triples of distinct shared positions, 48 have
initials `BUT`. Among those 48:

```text
exact finals HYE:                         5 / 48
mirror-closed filtered letter set:       18 / 48
historical mirrored-pair-plus-fixed-E:   10 / 48
strict positional mirror:                 6 / 48
```

The fixed words provide a second control. Every one of their six permutations
retains the same mirror-closed set, three satisfy the historical partial rule,
and none satisfies a strict positional mirror. Thus mirror-set closure cannot
validate the `[23,16,7]` serialization or the BUT order; it is invariant under
the very ordering choice it was supposed to help recognize.

Verdict: retain the exact BUT/HYE boundary reconstruction, especially its
literal post-`choice` BUT check. Downgrade the claim that it mechanically
reaches `yinyang`. Filtering to `a-i` and accepting a partial pair plus a fixed
point is a plausible visual interpretation, but too common and insufficiently
specified to establish the next phase. Consequently, FAED-as-`thispassword`
remains a useful page-order hypothesis only conditional on a transition that
has not yet been recovered.
