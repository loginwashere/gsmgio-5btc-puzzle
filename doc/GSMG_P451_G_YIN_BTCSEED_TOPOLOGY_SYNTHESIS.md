---
type: audit
phase: 451
date: 2026-08-29
updated: 2026-08-30
status: complete
result: no-contradiction-refiling-only
disposition: synthesis
script: tools/gsmg/phase451_g_yin_btcseed_topology_synthesis.py
---

# Phase 451 — G-YIN-001 / BTCSEED Topology Synthesis

## Question

Does the BTCSEED branch (Phases 386-408: a Bifid square keyed from `DBBI`
applied to decrypt `FAED`) materially change the prior DBBI/FAED
independent-consumer and topology assessment (Phase 371;
[GSMG_TOPOLOGY_AUDIT](GSMG_TOPOLOGY_AUDIT.md); Phase 412/413) underlying
`G-YIN-001`? Separately, is that evidence correctly filed against the
Topology Audit's T0-T8 taxonomy?

Protocol:
[Phase 451 G-YIN-001 BTCSEED Topology Synthesis Protocol](Brainstorms/2026-08-29%20-%20Phase%20451%20G-YIN-001%20BTCSEED%20Topology%20Synthesis%20Protocol.md).
This is pure synthesis: no new decoder, statistical test, cipher search, or
oracle call. `phase451_g_yin_btcseed_topology_synthesis.py` machine-verifies
every quoted claim below is byte-present in its source phase's own
findings-store entry.

## 1. Contradiction audit

**Phase 371 vs. BTCSEED:** no contradiction. Phase 371 tests what the
page's own literal instruction-token adjacency licenses
(`either_stream_requires_the_other_as_input = False` — no page evidence
requires DBBI's content to feed FAED). BTCSEED tests a specific,
unlicensed, community-proposed construction executed directly against the
raw streams. Both find no creator-authenticated consumer; they test
different evidence classes and reach compatible negatives, not opposing
claims about the same proposition.

**Phase 412/413 vs. a T4-shaped (asymmetric) construction:** no bearing.
Phase 412 rejects only the narrow shared/pooled-distribution null (registry
T2 / topology T3) and its own text explicitly disclaims that this "does not
disprove every asymmetric joint generator." A directional keying relation
like BTCSEED's is outside what that comparison tested.

## 2. Topology re-filing

BTCSEED's actual construction — de-duplicate `DBBI[:13]` into a Bifid key
square, then decrypt `FAED` as ciphertext — is a directional, asymmetric
relation: DBBI supplies key material, FAED is the operand. That is exactly
[GSMG_TOPOLOGY_AUDIT](GSMG_TOPOLOGY_AUDIT.md)'s **T4** ("DBBI instructs
FAED — DBBI is the operator, FAED the operand"), not its **T3** ("DBBI/FAED
combine symmetrically — peers, joint decode object").

Neither `GSMG_TOPOLOGY_AUDIT.md` nor `GSMG_SCIENTIFIC_THEORY_REGISTRY.md`
previously made this cross-mapping explicit. The Topology Audit's own T4
row (dated 2026-08-22, predating Phase 386 by two days) currently reads:

> No phase directly tests this vs. T5. Weak, low-confidence lean *toward*
> T4 from the escape-pair asymmetry ... — my own inference from the ledger,
> not a project finding

This is now stale: Phases 386-408 directly executed a T4-shaped
construction. The outcome does not promote T4 — the checkpoint survives
only under the single period used to discover it (Phase 408,
`period_robust = False`), and twelve frozen consumer families found zero
hits (Phases 397-407) — but "no phase directly tests this" is no longer
accurate, and the row should say so.

## 3. G-YIN-001 disposition

**Unchanged: parked, P0.** No creator-selected operator exists under either
the symmetric (T3) or asymmetric (T4) framing. BTCSEED supplies one
concretely executed, mechanically real T4-shaped candidate, but its own
experiment already concluded stopped/not-promoted for want of an
independently selected period and a downstream consumer — the same bar
every one of the ~45 T3-shaped candidates (Phases 272-321) already failed.
Phase 386's own disposition states this directly: "Does not reopen or
narrow any existing gap." This synthesis corrects a documentation gap
(BTCSEED was never cross-filed against the T0-T8 taxonomy) — it does not
change G-YIN-001's evidentiary status or closure condition.

## 4. External corroboration (2026-08-30 addendum)

> **Update (2026-08-30):** an independent solver reached the same T4-shaped
> construction publicly and it was combinatorially rebutted in the same
> thread. Recorded here as corroboration; it does not change section 3's
> disposition and was not machine-verified by
> `phase451_g_yin_btcseed_topology_synthesis.py` (external source, not this
> project's findings store).

[`Naddiseo/gsmgio-5btc-puzzle` issue #13](https://github.com/Naddiseo/gsmgio-5btc-puzzle/issues/13)
(opened 2026-08-24, closed out 2026-08-26) independently proposes exactly
this project's Phase 386 construction: de-duplicate `DBBI` into a Bifid key
square and decrypt `FAED` as ciphertext at the full-length period, producing
a plaintext beginning `BTCSEED` with a single `z` later in the stream.

The thread's own rebuttal (`etheral-dev`) goes beyond this project's Phase
408 period-fragility finding. Because the DBBI-derived alphabet's first nine
letters are exactly `FAED`'s own alphabet, every ciphertext letter falls in
the grid's first two rows, which forces every odd-position plaintext letter
into `{B, C, D, E}` and pins the lone `z` to whichever of `{G, H}` lands in
column 4 — properties of the cipher's forced structure, not of the
plaintext. An exhaustive enumeration of all `9! = 362,880` permutations of
the nine-letter key alphabet (same `FAED` ciphertext, period, and
row-column reading) found exactly 8 permutations reproduce the `BTCSEED`
head — matching the average yield of *any* achievable 7-character head
under this construction (73,097 distinct achievable heads across the same
362,880 keys, mean 4.96 keys per head), not a rate specific to `BTCSEED`.
A companion argument holds the creator's own stated decode-success marker
is `yinyang` (the fourth ingredient token from the 2023-02-23 binary), not
`BTCSEED`. Thread consensus, including the original poster, converged on:
not worth prioritizing further.

This is independent, external, purely combinatorial corroboration of
section 3's "stopped/not-promoted" verdict — it sharpens *why* Phase 408's
`period_robust = False` result holds (the construction's apparent hits are
priced by the cipher's own structural degrees of freedom, not by anything
in the plaintext) but does not change `G-YIN-001`'s disposition, which was
already unchanged before this addendum.

## Applied corrections

- `GSMG_TOPOLOGY_AUDIT.md`: T4 row's evidence cell updated to cite Phases
  386-408; closing verdict paragraph's "T4/T5/T6/T7 don't have enough
  direct evidence" qualified to carve out T4.
- `GSMG_SCIENTIFIC_THEORY_REGISTRY.md`: T3 (BTCSEED) section given an
  explicit "Corresponds to Topology Audit's T4, not T3" cross-reference,
  matching the existing convention already used in its T2 section.
- `GSMG_OPEN_GAP_REGISTRY.md`: `G-YIN-001` row given a Phase 451 note
  recording that BTCSEED was reviewed, found T4-shaped and non-contradictory,
  and does not change the gap's disposition.

## Stop rules honored

No new cipher menu, decoder, password generation, blob/address oracle,
brute force, GPU, Docker, network, or external agent. No re-scoring or
re-running of Phase 386/408/412/413's own experiments — only citation
verification against their stored text. The 2026-08-30 addendum likewise
runs nothing new: it cites a public GitHub thread's own combinatorial
result verbatim rather than re-deriving it.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase451_g_yin_btcseed_topology_synthesis.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase451_g_yin_btcseed_topology_synthesis.py \
  --json-out tools/gsmg/phase451_result.json
```
