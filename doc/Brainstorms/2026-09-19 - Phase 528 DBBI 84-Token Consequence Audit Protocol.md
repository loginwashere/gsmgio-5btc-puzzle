# Phase 528 — DBBI 84-token consequence audit protocol

Date: 2026-09-19  
Status: bounded oracle-free audit

## Question

What changes mechanically when DBBI is parsed as the independently
reconstructed 84-token prime-host object rather than the historical 83-token
guide, and which earlier results actually require correction?

## Scope

The audit will:

1. reconstruct both complete prime-host parses directly from `data.DBBI`;
2. split each parse into its 23 prime-terminated groups plus any unhosted tail;
3. compare group payloads, endpoint colors, residues, and `b`/`be` payload rails;
4. inventory prior project consumers by whether the change invalidates,
   strengthens, or leaves them unchanged;
5. rerun the one identified tail-dependent structural statistic: Phase 177's
   within-group-versus-split literal-`be` comparison, with the terminal `be`
   correctly split by the 84-token parse; and
6. check the exact textual objects against the named Phase 478 submitted-byte
   corpus and Phase 523 base corpus.

No AES, FAED, password expansion, language scoring, permutation search, or new
transform family is permitted. Numerical group lengths and sums are recorded
as measurements, not promoted as passwords.

## Frozen constructions

- A prime logical position consumes either raw `b` or raw `be`.
- A non-prime logical position consumes one raw `a`–`i` symbol.
- A group consists of the non-prime tokens after the preceding host and before
  the current prime-position host. The host itself labels the group but is not
  part of its payload.
- Symbols after the 23rd host are an unhosted tail.
- `b` and `be` rails concatenate group payloads in original group order.
- Letter sums use the native `a=1, ..., i=9` values already used by the guide.

## Corrected Phase-177 cell

Only Phase 177's `merge_gap` statistic is rerun. Its 105 insertion positions,
two orientations, source bits, 2,000 token-profile-preserving shuffle trials,
and seed 177 remain unchanged. The positive class becomes the seven literal
`be` pairs merged as 84-parse prime-host tokens; the negative class becomes
the three split pairs, including the terminal raw `be` whose `b` is host 23
and whose `e` is the unhosted tail. No other Phase-177 metric is repeated.

## Decision rule

- An earlier negative is invalidated only if its tested object or class labels
  change under the 84-token parse and it did not already include that exact
  branch.
- Exact byte absence is novelty evidence only, not evidence of intendedness.
- A corrected `merge_gap` result is descriptive unless its fixed familywise
  upper-tail p-value is below the project's 0.005 promotion bar.
- The output is an inventory and corrected structural result. It cannot
  authorize an oracle run by itself.
