# GSMG Architect-Choice Boundary Audit

## Question

Which strict reading of
`matrixsumlist -> lastwordsbeforearchichoice -> yinyang` survives comparison
between the performed film subtitles and the frozen draft screenplay?

## Frozen sources

- `the-matrix-reloaded-2003.en.srt`, SHA-256
  `5bea91bed444377b81e1734f994e91a21d3d893cdca52be426b094c3cb014a18`
- `the-matrix-reloaded-2003.pdf`, SHA-256
  `2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4`

The audit excludes screenplay stage directions and compares three natural
spoken scopes:

1. “Which brings us at last…” through the literal word `choice`;
2. the two-door speech through `choice`;
3. the final sentence immediately preceding `choice`.

Within a scope, `[23,16,7]` is used only as:

- forward/backward, zero/one-based word indices; or
- literal nested tail lengths of 23, 16, and 7 words.

No semantic scoring, cipher oracle, added transcript window, or password
generation participates in selecting the result.

## Result

The broad spoken scope contains 69 words in the film subtitles and 72 in the
draft screenplay because the performed two-door wording differs from the
draft. Despite that drift, the forward one-based positions are identical:

```text
23 -> BOTH
16 -> ULTIMATELY
 7 -> THE
```

Their edges are:

```text
beginnings -> BUT
endings    -> HYE
```

`BUT` is exactly the first Architect word after the fixed `choice` boundary.
That is an external boundary check unavailable to the other conventions.
The alternative forward-zero, backward-one, and backward-zero outputs differ
or lose stability across the two sources.

Literal tail readings do not produce a comparable marker. The exact final
sentence before `choice` is source-stable and contains seven words:

```text
AS YOU ADEQUATELY PUT THE PROBLEM IS [CHOICE]
```

Its initials/finals are `AYAPTPI/SUYTEMS`, not a short recognition state.
Because seven is the last member of `[23,16,7]`, the exact seven-word phrase
was retained as a strict alternate password hypothesis. Its spaced and joined
forms generated 36 keystrings and were tested against four tracked blobs under
the established CBC, ECB, stream, and Key-Wrap families: **zero hits**.

## Binding result

The existing dual-channel audit was re-run after the boundary result. It
confirms one real downstream association:

```text
BUT filtered to a-i -> B
HYE filtered to a-i -> H,E
mirror9(B) = H; E is fixed
```

This maps naturally to DBBI's fitted `{b,e}` escape pair and the mirrored
FAED `{h,e}` hypothesis. However, `{h,e}` is not FAED's independently best
pair (`{g,i}` is), and its bounded monoalphabetic, chain-addition, and autokey
models are already negative. No conserved polarity connects `BUT/HYE` to the
two SALPH AES halves, the two page textareas, or “half/better half.”

Therefore:

- `BUT/HYE` survives as a strong reconstruction of the boundary;
- it does not yet identify a deterministic consumer;
- the literal seven-word alternative is direct-oracle negative;
- forcing all visible pairs into one yin-yang channel is rejected.

## Reproduction

```bash
python3 tools/gsmg/architect_choice_boundary_audit.py --self-test
python3 tools/gsmg/architect_choice_literal_password_audit.py \
  --self-test --oracle --include-quarantined
python3 tools/gsmg/dual_channel_consistency_audit.py --self-test
```

## Consequence

Do not launch the planned orientation/polarity brute force: its required
operand binding was not recovered. The next useful investigation must explain
why FAED prefers `{g,i}` while the Architect mirror produces `{h,e}`, or find
a different visible object at the immediate boundary that independently
selects one of those pairs.

One tempting visual observation must not be promoted: `g-h-i` are consecutive
alphabetical letters, but this is **not** the `mirror9` relation used above.
Under the actual `a-i` involution, `g <-> c`, `i <-> a`, `b <-> h`, and `e`
is fixed. Therefore alphabetical adjacency around `h` supplies no mechanical
explanation for FAED's `{g,i}` preference. Any future reconciliation must be
selected independently by authenticated page structure or wording.
