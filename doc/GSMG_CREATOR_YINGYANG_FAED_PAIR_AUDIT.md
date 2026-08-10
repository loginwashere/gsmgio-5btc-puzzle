# GSMG Creator `YING/YANG` → FAED Pair Audit

Phase 225 tests a narrow visible-wording hypothesis without running a decoder
or AES oracle: does the creator's spelling `YING/YANG` explain FAED's otherwise
unbound `{g,i}` escape pair?

Reproduce it with:

```bash
python3 tools/gsmg/creator_yingyang_faed_pair_audit.py --self-test
```

## Exact alignment

The only two plain-language creator messages naming the state are 9599 and
39224. Both spell it `ying yang`/`yingyang`. Filtering the equal-length words
to the page's native `a-i` alphabet gives:

```text
YING -> IG
YANG -> AG
```

`I` and `A` are the endpoints of the exact `mirror9` involution. `G` is
shared, although it is not a fixed point (`G ↔ C`). Independently, the
alphabet-free code-IC audit ranks `{g,i}` first and `{a,g}` fifth among the
clean FAED segmentations. Under the bounded control family `(I,s)/(A,s)` for
shared `s` in `b..h`, `G` is the unique best valid suffix by both worst rank
and rank sum: ranks `1+5`, versus the next-best `8+18` for `E`.

The effect is target-specific. On DBBI, the same `G` pairs rank only 13th and
10th; shared `B`, not `G`, is the best control suffix.

## Why it is not promoted

Two primary facts prevent treating the extra `G` as an authenticated operator:

- creator message 1806 predates both plain-language uses and explicitly says
  there are no clues in the puzzle's typos;
- the creator's authenticated reversed-binary macro uses the standard spelling
  `yinyang`, not `yingyang`.

The nearby “Both?” also cannot select the `IG` and `AG` halves. It immediately
follows a community question asking “hit or hint?” and has no Telegram reply
edge to reinterpret it more narrowly. Its source-context referent is those two
words.

## Verdict

Retain `YING → IG` as a compact possible explanation for why FAED's independent
code-IC result prefers `{g,i}`. Do not call it recovered binding: the spelling
is explicitly covered by the creator's typo caveat, `G` is not a mirror fixed
point, and no instruction selects a decoder or combines the `IG`/`AG` parses.
Consequently Phase 225 authorizes no `{a,g}` or dual-pair brute force.
