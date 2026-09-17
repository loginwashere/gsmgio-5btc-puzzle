---
type: audit
phase: 520
date: 2026-09-17
status: complete
result: no-calibrated-joint-coherence
disposition: corroboration-only-no-gap-closure
script: tools/gsmg/phase520_dbbi_faed_joint_splice_hypothesis_audit.py
---

# GSMG Phase 520 — DBBI+FAED Joint-Splice Hypothesis

## Question

DBBI and FAED are confirmed (Phase 101, 243/244) to share one text node
with no markup boundary between them, joined only by the `matrixsumlist`
instruction span — structurally identical to a PEM/base64 blob whose
payload is broken by an inline marker. Has treating `matrixsumlist` purely
as a splice marker (not a real instruction) and decoding `DBBI + FAED` as
one continuous 661-symbol raw checkerboard stream — the way one would strip
a PEM header/footer and rejoin base64 lines before decoding — been tested?

This is distinct from every prior cross-stream test: Phase 412 compared
shared-vs-independent statistical *parameters*, not a literal joint decode;
Phase 371 checked whether either adjacent instruction *embeds* the other
stream's content, not whether the streams themselves splice; Phase 518
tested proportional-block positional correspondence, not literal
concatenation decodability.

## Method

`tools/gsmg/phase520_dbbi_faed_joint_splice_hypothesis_audit.py`. Three
checks, cheapest first, no plaintext/password/oracle used at any stage:

1. **Structural**: is `len(DBBI) + len(FAED) = 661` prime? This project's
   own established convention (used for DBBI = 7×13 and every one of
   FAED's admitted divisor pairs) requires a nontrivial rectangular
   transposition grid to have a nontrivial factor pair.
2. **Code-IC joint-fit gate**: for each of the 36 escape pairs, the single
   best code-index-of-coincidence fit (distance from the 0.067 English
   reference) of the spliced stream, calibrated against 20,000-replicate
   matched nulls reusing Phase 459/460's exact validated Euler-traversal
   and endpoint-fixed-shuffle surrogate generators (applied independently
   to DBBI and FAED, then concatenated) — does the real splice fit one pair
   distinctly better than chance splices of two unrelated streams would?
3. **Board-anneal coherence** (run since gate 2 did not look decisively
   negative going in): substitution-only decode (no transposition, per the
   structural finding) of the spliced stream at its own single best pair,
   using the same annealing solver validated in Phase 516 (60,000 iterations
   × 30 restarts), compared against each stream's own already-established
   best-pair decode at the identical budget.

## Results

**1. Structural.** `661` is prime (confirmed by direct factor search up to
`sqrt(661)≈25.7`); it has zero nontrivial factor pairs. No rectangular
transposition grid applies to the full spliced stream under this project's
own convention — a single-transposition-grid reading of the full splice is
structurally excluded, independent of any other result below.

**2. Code-IC joint-fit gate.**

| Stream | Best pair | Loss (distance from 0.067) |
|---|---|---:|
| DBBI alone | `be` (standing) | `0.0000763` |
| FAED alone | `gi` (standing) | `0.0072908` |
| `DBBI+FAED` spliced | `eg` | `0.0100807` |
| `FAED+DBBI` spliced (reverse order) | `gi` | `0.0122263` |

The spliced stream's own best joint pair fits **worse** than *either*
individual stream's own optimum, converging on neither `be` nor `gi` in
the page-order splice — exactly the signature two genuinely different
per-stream frequency profiles produce when concatenated, and exactly what
Phase 412's independent-profile finding predicts.

| Null | Extreme count / 20,000 | One-sided p | Median |
|---|---:|---:|---:|
| Euler-traversal (primary) | 8,596 | `p=0.429829` | `0.010245` |
| Endpoint-fixed shuffle (sensitivity) | 19,473 | `p=0.973651` | `0.006948` |

The real observed loss (`0.010081`) sits almost exactly on the primary
null's median (statistically unremarkable, `p=0.43`) and is *worse* than
97% of the sensitivity null's replicates. **Decision: `no_calibrated_joint_coherence`.**

**3. Board-anneal coherence.**

| Candidate | Pair | Tokens | Normalized quadgram score | Preview |
|---|---|---:|---:|---|
| DBBI alone | `be` | 63 | `-4.754` | `NGTOFIIASHEPAATEASSURRYWEREELDONEALLING...` |
| FAED alone | `gi` | 436 | `-5.572` | `OIERDEEROATRITSSDAIRAOERRNRLYPIERDZOIEA...` |
| `DBBI+FAED` spliced | `eg` | 511 | `-5.714` | `NSSESISTOOSYSETASXHTSYLLSXSLTTXTTISASIN...` |
| `FAED+DBBI` spliced | `gi` | 515 | `-5.570` | `OIERDEEROATRITSSDAIRAOERRNRLYPIERDZOIEA...` |

Neither splice order produces a normalized quadgram score better than
decoding each stream separately at its own established best pair; the
`DBBI+FAED` page-order splice is the *worst* of the four. None of the four
previews are English or word-like.

## Disposition

All three checks close negative, in a mutually reinforcing way: the splice
is structurally incompatible with a single-transposition-grid reading
(prime length), shows no calibrated statistical joint-coherence advantage
over chance concatenation of unrelated streams, and does not decode more
coherently than treating the two streams separately. This is **corroboration_only**
and does not select a `matrixsumlist` reading, does not reopen or close
`G-YIN-001` or `G-MSL-001`, and does not repeat or supersede Phase 412
(shared-vs-independent statistical parameters), Phase 371 (instruction-embeds-content
check), or Phase 518 (proportional positional correspondence) — this
tests a fourth, genuinely distinct, literal-splice reading none of those
covered.

This does not rule out every version of a "single underlying construction"
idea — only the literal, no-transposition, single-global-escape-pair
splice reading tested here. A construction where each half keeps its own
separate transposition/escape-pair treatment and only some other operation
(not raw concatenation) relates them is a different hypothesis, already
covered by the ~50 cross-stream coupling models in Phases 271–321 and the
independent-consumer analysis in Phase 371.

## Facts affected

None.

## Supersedes/corrects

None.

## Artifacts

- `tools/gsmg/phase520_dbbi_faed_joint_splice_hypothesis_audit.py` —
  implementation, self-test.
- `tools/gsmg/test_phase520_dbbi_faed_joint_splice_hypothesis_audit.py` —
  5 tests (<1s, excludes the expensive null/board-anneal run).
- `tools/gsmg/phase520_result.json` — full real-data result (structural
  check, code-IC fit table, both null summaries, board-anneal coherence
  table).

## Reopen condition

Only on a new primary source or authenticated selector specifically
licensing a literal DBBI+FAED concatenation reading (e.g. a creator
statement that `matrixsumlist` is a formatting/display artifact rather
than a real instruction) — not on re-running this same construction again
with a different escape-pair search budget or board-anneal parameters.
