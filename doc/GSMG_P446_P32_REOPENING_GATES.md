---
type: audit
phase: 446
date: 2026-08-29
status: complete
result: one-finite-runnable-residual-all-other-reopenings-gated
disposition: synthesis
script: tools/gsmg/phase446_p32_reopening_gate_synthesis.py
---

# Phase 446 — P32 Family Coverage and Reopening Gates

## Bottom line

The project has tested 15 materially distinct P32TRAILING families. There is
only one bounded residual already runnable without new puzzle evidence:
Phase 163's Tier-1 `-nopad --whitespace-variants` backfill, roughly 700,000
keystrings and historically estimated at 1–2 CPU hours.

Everything else that remains untested is either conditional on a concrete
prerequisite, blocked for lack of a selector, or requires genuinely new
evidence. “Not enumerated” does not by itself make a variant a live backlog
item.

## Compact family table

| ID | Tested family and result | What is genuinely untested | Evidence required to license it | Key phases |
|---|---|---|---|---|
| F01 | Envelope/KDF/cipher/detector coverage: authenticated `Salted__`, solved legacy-EVP/SHA-256/AES-CBC profile, declared CBC/ECB/stream/legacy/Key-Wrap and binary/key detectors; no hit | Custom KDFs and some large-corpus mode widenings; Phase 374 Stage 4 was costed, not run | Authenticated cipher/KDF/toolchain clue, new solved-vector precedent, or separately preregistered finite widening with a clear information-gain case | 25–26, 77–80, 83, 94, 192–193, 257, 323, 327, 331, 368, 385, 410 |
| F02 | Curated vocabulary/direct clues/broad text corpora: current authenticated core, bounded, and medium candidate universes; no hit | Only changed source material; arbitrary dictionaries/formats are not a genuine residual | New creator artifact, changed authenticated corpus, or exact independent P32 candidate | 54, 77, 83, 88, 94, 117, 121, 133–134, 147–150, 163, 167, 179, 182, 184, 186, 189, 191, 227, 234, 237, 256–257, 323, 374 |
| F03 | Eight-fragment macro clue: literals and every direct P(8,k), k=1..8, plus converged macro-panel readings; negative/recognition-only | Unauthored separators, wrappers, and new semantics are conceivable but unselected | Ninth creator fragment or primary evidence fixing grammar, operator, and P32 consumer | 79, 121, 158, 292, 317, 322, 334, 423–424 |
| F04 | Solved Phase 2/3/3.2 prose and prior-password reuse: sentences, blocks, seven-part orders, X2SH route, boundary grammar; no hit/new material | Arbitrary subsets, splices, and normalization combinations | Local instruction fixing boundary, order, normalization, and consumer | 265–269, 314, 317, 341, 370 |
| F05 | Phase-3.2 sibling/operator-data constructions: whole answers, prime/Stage-0 readings, parameters, parent prefix, split-guide consumers, calibrated panel promotions; negative | Half/interleave/restored-whitespace and unrestricted salient-part compositions | Evidence selecting one source, exact boundary/order, transform, and consumer | 270, 370, 416, 421 |
| F06 | Architect `PRIME BASICS`, 16/7 rails, and transport: two exact letter sources, precedent prime rule, blue/yellow/blue→yellow/intertwined rails; negative; two carriers/no binding | Yellow-first, reversal, other weave/source/rule, or answer→consumer transform | Primary evidence fixing source, direction/serialization, unique carrier, consumer, and transform | 434–440, 442–445 |
| F07 | Page-local rebuses and DBBI/FAED derivatives: YOUWON, title/checkerboard readings, numeric/binary transports, nibble packing, routes and classical probes; no P32 hit | The actual FAED decoder/DBBI relationship and Family-10 ordering-key reading | Authenticated decoder, named ordering rule, or demonstrated page-local edge to P32 | 71, 75–76, 96, 133, 147–150, 169–170, 179, 186, 189, 191, 227–228, 237, 272–273, 290, 292, 319–321, 368, 374, 382, 389, 394, 419 |
| F08 | Binary/input-byte forms and raw assets: raw digests/keys/chunks, whitespace bases, page-native transports, 83 pinned assets, source-encoding applicability; negative | Historical scripts/CSS/maps and assets/media excluded for scope, chronology, or provenance | Frozen raw-response family plus pre-P32 provenance/authorship, or newly authenticated single-file addition | 78, 83, 94, 163–164, 272–273, 378–381, 392 |
| **F09** | **Tier-1 nopad whitespace coverage: base nopad and smaller curated whitespace scopes negative** | **Tier-1 `--whitespace-variants`, about 700,000 keystrings** | **Already licensed; only an explicit compute decision is needed** | **84, 94, 163** |
| F10 | Cross-blob salts/envelope/concordance: salt/block inventory, salt operands, ~35k independent constructions, exact multi-blob concordance; no signal | Arbitrary salt arithmetic/offsets/shared-password theories and `Salt|Phase|Ion` structural roles | Source selecting the exact relation, offset, shared structure, or consumer | 169–171, 192, 271, 348 |
| F11 | Numeric/temporal metadata: 69 authenticated IDs, heights, times, integers, and ISO/HTTP dates; no hit | Other numbers, widths, and date renderings | New authenticated milestone plus fixed serialization and P32 role | 117, 344, 391 |
| F12 | Bitcoin/on-chain/key/container family: signer provenance, transaction graph/fingerprint, EC neighbors, key shapes and exact secret-container parsers; no route/key/object hit | Larger classifier/parser corpus, one-error repair without a near-valid object, raw transaction bytes as passwords | Near-valid object, authenticated key/container clue, selected transaction-byte use, or separately authorized bounded scale-up | 156, 327, 331, 342, 350, 383, 390, 394 |
| F13 | External repos/community/chronology/code archaeology: bounded search and provenance filtering; no independent candidate or hidden route | Future fork/archive/media/DNS evidence or exact external candidates | Changed authenticated artifact or reproducible independent claim | 156, 271, 344, 383, 390, 409 |
| F14 | Blinded reconstruction panels: valid surface, solution-complete, and macro-augmented conditions; every promotion negative | More samples/providers/models or arbitrary packet rewrites are instrument variants, not puzzle evidence | Primary-evidence packet delta or preregistered instrument with distinct expected information gain | 414–417, 420–423 |
| F15 | Historical `SOURCE CODES` referents/comments: 11 referents gated and 32 comment prime/complement readings; no executable referent | Raw responses or comment pair used in downstream password constructions | Evidence fixing referent, stable bytes, unit/boundary, operator, serialization, and P32 consumer | 436–440 |

## Residual register

The machine-readable classification is:

| Residual class | Families | Meaning |
|---|---:|---|
| `finite_unrun` | 1 | F09 is implementation-ready and requires no new clue |
| `conditional_unrun` | 4 | F01, F08, F12, and F15 have concrete possible deltas but require authorization, provenance, or a prerequisite object |
| `unselected_variants` | 6 | F04–F07, F10, and F14 describe possible variations without a source-selected construction |
| `new_evidence_only` | 4 | F02, F03, F11, and F13 reopen only when their source universe changes |

The most important distinction is between F09 and everything else. F09 is a
real coverage debt. By contrast, reversal, yellow-first, another interleave,
another cipher, another model sample, or another sentence splice is merely an
available analyst choice until independent evidence fixes it.

## Universal reopening gate

A future proposal should change at least one load-bearing field through
evidence independent of its output:

1. source object/authenticated bytes;
2. operand boundary and normalization;
3. operation, KDF/cipher, direction, or order;
4. downstream consumer/output role; or
5. target or independently fixed validator.

If none changes, the proposal is a parameter expansion of existing coverage,
not a reopened family.

## Verdict

Disposition: `one_finite_runnable_residual_all_other_reopenings_gated`.

This synthesis generated no password material and made no oracle call. Docker,
GPU, network, and external agents were untouched.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase446_p32_reopening_gate_synthesis.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase446_p32_reopening_gate_synthesis.py \
  --output tools/gsmg/phase446_result.json
```
