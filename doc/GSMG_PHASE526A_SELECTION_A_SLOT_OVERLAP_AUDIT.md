# Phase 526A - Selection-A coordinate slot-extension overlap audit

Date: 2026-09-19  
Disposition: **large genuinely new material family; execution not yet run**

## Question

If Phase 525A's 16 Selection-A-specific coordinate representations are added
only to the existing `matrixsumlist` slot, how much of the resulting frozen
macro-password grammar has already been submitted to an oracle?

## Method

The oracle-free protocol was frozen before the full run. It reused Phase 523's
slot order, 26 subset/join cells, original values in the other three slots, and
standard newline-enabled form expansion. It generated only bases containing
one of the 16 new coordinate values.

Expanded materials were compared against the union of:

- Phase 523's 18 historical SALPH-scoped sources;
- every base executed in Phase 524, reproduced under the same standard
  expansion; and
- Phase 478's 1,749,878 actually submitted byte strings.

No cipher, encrypted blob, FAED string, or password oracle was accessed.

## Result

| Quantity | Result |
|---|---:|
| Frozen coordinate values | 16 |
| Candidate bases | 112,624 |
| Exact base duplicates | 0 |
| Expanded forms represented by the audit | 5,136,688 |
| Candidate unique material keys | 2,401,721 |
| Prior-union material keys | 7,212,949 |
| Unique genuinely fresh material keys | **2,384,208** |
| Retained covering bases | **112,624 / 112,624** |
| Oracle calls | 0 |

Each coordinate source contributes exactly 7,039 bases, and every one of those
bases retains at least one fresh material. The output base list is 9,660,503
bytes with SHA-256
`800e7a181a015416725d399059e8369c556a4f9e4e2fffe9e71f18f9fcd7ea36`.

The native GPU tool will emit 5,137,056 forms: the audit count plus one empty
letters-only form for each of 368 digit-only bases, matching the known Phase
524 accounting behavior. At Phase 524's measured rate this projects to about
1 hour 55 minutes.

## Interpretation

This is not a marginal formatting residue. Selection A supplies a large,
mostly new extension of the exact house-style password grammar. The result does
not establish that any coordinate is intended or that the grammar is correct;
it establishes that testing it would not merely repeat Phase 524.

The 64-bit membership key cannot create an execution coverage omission here:
all 112,624 bases were retained, so the later tool will regenerate every form
from the complete closed base universe even if a theoretical hash collision
occurred during classification.

## Verification

- Six focused tests pass, including the Phase-523 dictionary-to-set regression
  caught during the first pre-result attempt.
- All three pinned input hashes match.
- The successful overlap run took 23.5 seconds and peaked at approximately
  948 MB RSS.
- `_work/phase526/report.json` SHA-256:
  `e05f22a887326af7cc76f123b86d03bd5ab19fd1df2402f81e184041ba6bf7b6`.

## Disposition

Prepare a separately locked execution with SALPH as the primary consumer. The
other tracked blobs may ride along only if the fixed GPU oracle cannot restrict
its blob set, as in Phase 524. A zero-hit result closes exactly these 16 values,
the frozen macro grammar, and its standard expansion; it does not license new
coordinate encodings.

Execution has not started. At the end of this audit the NVIDIA driver was not
visible to the shell, so no CPU fallback was attempted.

## Artifacts

- `tools/gsmg/phase526_selection_a_slot_overlap.py`
- `tools/gsmg/test_phase526_selection_a_slot_overlap.py`
- `_work/phase526/bases.txt`
- `_work/phase526/report.json`
- frozen Phase 526A Brainstorms protocol

## Limits

Selection A remains conditional community reasoning. This phase neither
authenticates the selector nor studies the 61-symbol DBBI residue.
