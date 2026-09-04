---
type: audit
phase: 464
date: 2026-09-01
status: closed
result: negative
disposition: parked
evidence_level: authenticated-artifact
topics:
  - rotated-prime
  - theflower
  - creator-provenance
  - telegram
related_phases:
  - 246
  - 248
  - 461
  - 462
script: tools/gsmg/phase464_rotated_prime_provenance_audit.py
---

# Phase 464 Rotated-Prime Creator-Provenance Audit

## Question and preregistration

Does creator-authored evidence independent of Denis's 2026-06-25 rotation
proposal select the load-bearing operations in the `311027 -> THEFLOWER`
chain, or does an authenticated downstream consumer accept its output?

The protocol was frozen before inspecting the evidence in
`doc/Brainstorms/2026-09-01 - Phase 464 Rotated-Prime Creator-Provenance Audit Protocol.md`.
It fixed seven selectors: a 90-degree turn of the 24 colored apertures;
complement/inverse polarity; two six-digit primes as 2x3 decimal matrices;
`[total,row1,row2]`; total word as outer frame; reverse-even extraction from
`TRUE`; and prefixing with `THE`. It also prohibited new ciphers, password
permutations, `BLOSSOMS` fitting, and 49-cell-grille work.

Promotion required one of:

1. an exact independent creator reference to `311027` or `04BEF3`;
2. creator selection of the 90-degree turn plus a second load-bearing
   operation in first-piece context; or
3. an authenticated downstream consumer accepting the result.

## Frozen corpus and method

The manifest pins four Telegram export JSON files by SHA-256, creator ID
`user9815232`, and the solver independence cutoff `<65935`. The merged solver
corpus contains 60,375 messages; support contains 52,851. The audit examined
all 482 solver-group and 5,419 support-group creator messages, creator reply
parents, and all 88 creator-media records (83 unique payloads, zero missing).

Text matching is deliberately broad and produces contexts for manual review,
not automatic evidence. Media were content-hashed and freshly extracted by
OCR; five fixed frames were sampled from each video. The complete media set
was also checked against Phase 248's labeled native-byte contact-sheet review,
which visually reviewed the same 88 records and all videos. A frozen manual
review file must exactly cover every generated multi-selector candidate and
every media keyword hit before the result can carry a verdict.

## Results

| Measure | Result |
|---|---:|
| Creator messages audited | 5,901 |
| Licensed creator/reply contexts with any broad selector | 586 |
| Exact `311027` / `04BEF3` references | **0** |
| Automated rotation-plus-second-selector candidates | 14 |
| Creator media records / unique payloads / missing | 88 / 83 / 0 |
| Media keyword hits | 2 |
| Password candidates / oracle calls | **0 / 0** |

All 14 text candidates fail contextual review:

- solver parent `60282` uses “turning inward” and Matrix as a philosophical
  metaphor; creator `60285` replies only with a salute;
- post-discovery creator `66540` jokes about turning in his grave;
- eleven support candidates are ordinary trading-bot, engine, order-pair,
  or subscription language;
- support parent `63425` praises the puzzle and invokes Matrix thematically;
  creator `63428` offers a private message but publishes no operation. The
  unavailable private content is not affirmative evidence;
- support `67741` is the GSMG trading-service shutdown retrospective, whose
  common prose creates dense but irrelevant keyword overlap.

The two media keyword hits also fail. Solver `32561` is the already-reviewed
Merovingian action/reaction clip: “Matrix” is thematic, with no turn, matrix
construction, frame, parity, or prefix instruction. Support `39276` is a
product dashboard whose OCR contains “Total account value.” Neither is a
selector.

Two controls matter. Creator messages `1710` and the reply at `4096`
authenticate the rose/yellow/blue/first-piece clue, but not rotation or any
second operation. Support messages `26108` and `26113` demonstrate a genuine
older Caesar/`esrever` rotation precedent, but explicitly for the solved
pre-rabbit stage—not a physical 90-degree turn of the colored apertures.
Post-discovery creator messages were reviewed separately and contain no
endorsement of the rotation proposal or `THEFLOWER` chain.

## Gate decisions

| Promotion gate | Decision |
|---|---|
| Exact independent `311027` / `04BEF3` | fail |
| Creator-selected 90-degree turn plus second operation | fail |
| Authenticated downstream consumer | fail |

## Verdict

The preregistered provenance audit is **negative**. `THEFLOWER` remains a
strong recognition checksum, but the transition stays parked. Phase 464 adds
no license to extend toward `BLOSSOMS`, generate password permutations, or
return to the 49-cell grille.

Reopen only for a genuinely new creator source or pre-discovery artifact that
selects the quarter-turn and another load-bearing operation, an exact
`311027`/`04BEF3` reference, an authenticated consumer, or a preregistered
continuation that predicts unseen material.

## Reproduction

```bash
python3 tools/gsmg/phase464_rotated_prime_provenance_audit.py --extract-media
python3 -m unittest tools/gsmg/test_phase464_rotated_prime_provenance_audit.py
```

Artifacts: the protocol and manifest, `tools/gsmg/phase464_manual_review.json`,
`tools/gsmg/phase464_result.json`, and the audit/test scripts. Contact sheets
and full media extraction detail are reproducible scratch outputs under
`_work/` and are not canonical evidence by themselves.
