# Phase 432 — Phase-430 Live Candidate Reviewer

## Purpose

Phase 432 implements the CPU-only reviewer frozen in the Phase-432 protocol.
It snapshots an atomically written Phase-430 checkpoint, validates every
fingerprint field, independently decodes retained ranks, collapses exact
decoded-string duplicates, and reviews only `decoded[7:]`. It does not alter
the running GPU search or call a downstream oracle.

## Review channels

For at most 25 score-leading distinct retained decodes, the tool reports:

- exact dictionary hits and maximum-weight non-overlapping segmentation;
- separate 200-trial exact-multiset-shuffle calibrations for both dictionary
  measures;
- a fixed Bitcoin/puzzle keyword list;
- index of coincidence and strongest match fractions at lags 1–40;
- longest repeated substring and strongest repeated 4–12-grams;
- optional leader/new/departed deltas against an earlier report.

The full decoded SHA-256 is the deduplication identity. Identical decodes must
have equal GPU scores or the review fails. `BTCSEED` is removed before all
semantic and structural metrics.

## First live snapshot

- checkpoint SHA-256:
  `32e6df6cdf7f3886980d9562b6a3d43c63605d4e5c8c253283b862fcd5f3b35f`;
- checkpoint next rank: `7,960,654,774,272` (`38.04776904459444%` of `16!`);
- retained ranks: 1,000;
- distinct decoded strings: 2;
- duplicate retained rows collapsed: 998.

The leader at this snapshot is rank `6,734,809,711,440`, score
`-3507.5981`, square `DBIFKCENAMUHOGPLRSTQVWXYZ`. It begins:

```text
BTCSEEDDHTHRNEEAIBITNBIEBDCSIEUCOAORUTNBCRDICIBLEEBDDBUSDSBDORDNORDOUSCS
```

Its tail has no fixed Bitcoin/puzzle keyword. Its sole dictionary substring
of length at least five is `SERER`; substring-count `p=0.8059701493` and
segmentation `p=0.2935323383` under their deterministic same-multiset nulls.
The maximum-weight segmentation covers 57/563 characters (`10.12%`) with
isolated short words, not a phrase. Its longest repeated substring is five.

The second distinct decode is the previous rank `4,113,233,954,640` leader,
score `-3519.4343`. It also has no fixed keyword, longest repeat five,
substring-count `p=0.1741293532`, and segmentation `p=0.3482587065`.

## Interpretation

No reviewed signal is semantically interesting. The higher quadgram leader is
still structured nonsense, and both dictionary channels are null-like.

The extreme `1000 -> 2` collapse is operationally important. Phase 430's first
retained row remains the exact maximum over completed ranks, but its remaining
rows are block-winner samples rather than an exact top-K. Equivalent ranks can
crowd semantically different lower-scoring outputs out of the retained list.
Phase 432 therefore accurately describes the available shortlist but cannot
claim that it reviewed every interesting near-leader. Future quotient-aware
searches should deduplicate by decoded output or canonical class before host
retention.

## Usage

```bash
cd tools/gsmg
python3 phase432_bifid16_candidate_reviewer.py \
  --checkpoint ../bifid_gpu_search16/checkpoints/bifid_16factorial.json \
  --output phase432_live_review_next.json \
  --previous phase432_live_review.json
```

## Artifacts

- `doc/Brainstorms/2026-08-27 - Phase 432 Live Bifid16 Candidate Reviewer Protocol.md`
- `tools/gsmg/phase432_bifid16_candidate_reviewer.py`
- `tools/gsmg/test_phase432_bifid16_candidate_reviewer.py`
- `tools/gsmg/phase432_live_review.json`
