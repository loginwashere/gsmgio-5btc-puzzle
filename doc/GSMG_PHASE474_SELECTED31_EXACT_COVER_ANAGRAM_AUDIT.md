---
type: audit
phase: 474
date: 2026-09-02
status: technical_inconclusive
---

# Phase 474 — Selected-31 Exact-Cover Anagram Audit

## Outcome

The target-only inventory is complete at the frozen scope, but the registered
200-control calibration is not. Phase 474 is therefore **technical
inconclusive**, not positive and not bounded negative.

The independent decision tier used the fixed BIP-39 English list plus `a` and
`i`. The exact 31-letter multiset requires at least six words. One exact
minimum bag is:

```text
again / can / category / essay / leaf / vanish
```

This is an exact cover but supplies no natural sentence, unique ordering, or
puzzle-selected semantics.

The broader chat-derived discovery tier reaches four words, but its lexicon is
contaminated by the same discussion and includes typos, fragments, and joined
tokens. The twenty serialized minimum bags are correspondingly degenerate;
examples include:

```text
aaa / faceless / versionchat / yinagyang
aaaah / averaging / consistency / safely
caaef / salvation / searches / yinagyang
```

These are useful as a failure demonstration: minimizing word count in a noisy
lexicon optimizes for artifacts rather than meaningful phrases.

All four historical hand-built phrases are exact multiset covers and all their
tokens occur in the contaminated discovery lexicon:

```text
reach a safe ying yang salvation case
a safe ying yang race salvation chase
yingyang salvation each caesar safe
a canonical saga say everything safe
```

That validates their letter arithmetic only. The search supplies no rule that
selects one of them.

## Calibration failure

The preregistration required exact minimum word count through eight words for
the target and 200 random 31-position selections from the same 91-character
plaintext. Three locked pure-Python implementations were attempted. The first
two were interrupted before any result returned after 1,084.75 and 314.85
seconds. The third used exact meet-in-the-middle joins through four words and
exact DFS through eight; it was stopped at the predeclared practical cutoff
after 4,032.20 seconds while evaluating a control's five-to-eight-word
fallback. No complete control set, p-value, or decision-bearing result exists.

The separate target-only rerun is descriptive and cannot substitute for the
missing null calibration. No phrase is promoted.

## Disposition

The reproducible inventory reinforces the existing dead-end assessment:

- a clean lexicon gives a six-word but semantically arbitrary cover;
- a noisy puzzle/chat lexicon produces shorter covers by exploiting junk;
- the attractive historical sentences remain human-selected from a vast
  underconstrained space;
