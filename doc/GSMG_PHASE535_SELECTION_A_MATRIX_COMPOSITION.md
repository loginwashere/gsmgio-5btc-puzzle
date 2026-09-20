# Phase 535 — Selection A composed with the historical matrix rule

2026-09-20. Structural reconstruction; no decoded instruction or password.

## Previously untested composition

Phase 525 reconstructed Selection A; Phases 526–527 tested its coordinate
serializations as passwords. Phase 528 assessed several parse dependencies.
Neither implementation composes Selection A's **new endpoint assignment** with
Phase 53's **old chunk placement and row-sum operation**. The latter was tested
with the historical endpoints and the 25-event FEFE-insertion family, which
are different inputs.

This is a concrete omitted composition in the inspected implementations, not a
claim that the entire community has never tried it. Phase 528's inventory was
incomplete in this respect; its recorded negative experiments remain valid for
their own exact inputs.

## Fixed reconstruction

Reproduce both complete parses and all five color-compatible 23-of-25 event
selections from Phase 525. End each prime-hosted chunk at its selected spiral
endpoint and place the chunk backwards, using the existing 14×14 spiral,
`a=1..i=9`, `be=25`, row sums, and A0/mod26 output. Retain all three existing
collision policies; do not select one by apparent readability. Do not invent a
placement for the 84-token parse's unhosted terminal `e`.

The old `IZLKESEEDQPPEN` baseline reproduces exactly.

| Parse | Omitted event ranks | Contiguous collisions | Later-wins output |
|---|---|---:|---|
| 83 | 22,24 | 0 | `IZLKESKFEIPPEN` |
| 83 | 23,24 | 2 | `IZLKFLBCFRPPEN` |
| 83 | 24,25 | 2 | `IZLKEHBHFRPPEN` |
| 84 / Selection A | 22,25 | **0** | `IZLKESKGGIPPEN` |
| 84 / Selection B | 23,25 | 2 | `IZLKFLBDHRPPEN` |

Selection A puts all 83 hosted tokens in separate cells. All three collision
policies yield the identical matrix. Its row sums are:

```text
34, 51, 37, 36, 30, 44, 62, 58, 32, 34, 41, 15, 56, 13
```

The unhosted final `e` remains unplaced. Consequently this is not a complete
84-token decoder. Collision freedom also does not uniquely select A across the
whole family: one 83-token mapping is collision-free too.

## Literal downstream check

After reconstructing the matrix, test one small exploratory consumer: use
Selection A's raw row sums as one-based backward word indices before literal
`choice`, in the already-frozen `moment_to_choice` film and screenplay scopes.
No new scope, modular reduction, forward-index family or password oracle is
introduced. Existing source hashes are checked.

| Source | Selected words | Initials / endings |
|---|---|---|
| Film | leads the to your and end moment the the leads two to flaw and | `lttyaemttlttfa` / `seorddteesoowd` |
| Screenplay | to as will take the two wherein is source to door her expressed to | `tawtttwistdhet` / `osleeonseorrdo` |

Neither supplies a clear instruction, and they disagree across sources.
This is a direct observation, not a calibrated language significance test.

## Bounded zeroing follow-up

Before viewing its results, the dated reassessment specified one further
comparison motivated by the existing zeroing clue: keep Selection A's positions
fixed and zero either the host cells or the payload cells. Use the identical
row-sum rendering and two backward-word consumers; keep final `e` unplaced.
This differs from Phase 45's deletion of raw-prime or checkerboard-code units.

The host-only cells sum to `16*2 + 7*25 = 207`; payload-only cells sum to 336.
Their cellwise addition reproduces the original matrix exactly. Payload-only
row sums are `7,47,35,34,3,19,35,29,28,32,16,13,29,9`, rendering
`HVJIDTJDCGQNDJ`. Neither partition supplies a clear instruction through either
source's fixed word consumer. Full vectors and outputs are retained in JSON.
Recognizable words such as `salvation` are inherited from the source passage
and are not a recovered instruction. No new significance or intendedness claim.

## What this changes

The older FEFE collision objection does not apply to Selection A. The old
row-sum rendering still fails to turn this repaired placement into clear text.
The distinct missing steps are now visible: what to do with the tail `e`, what
the numeric cell values represent, and what consumes the resulting matrix or
sum list. Testing coordinates as passwords did not test those questions.

No fact about FAED, any private key, or any encrypted blob changes. No widening
to Caesar shifts, arbitrary anagrams or additional cipher layers was performed.

```bash
python3 tools/gsmg/phase535_selection_a_matrix_composition.py
```

The script records all five mappings, all 15 policy results, complete matrices,
input hashes, the zeroing comparison, six word-index outputs, and zero oracle calls in
`phase535_selection_a_matrix_result.json`.
