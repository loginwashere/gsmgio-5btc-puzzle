---
type: audit
status: closed
topics:
  - dbbi
  - faed
  - closed-system
---

# GSMG Phase 517 — Closed-System Untried Theory Batch (Tier 1 + Tier 2)

Date: 2026-09-17

## Question

[doc/Brainstorms/2026-09-17 - Closed-System Untried Theory Classes.md](Brainstorms/2026-09-17%20-%20Closed-System%20Untried%20Theory%20Classes.md)
scoped nine deterministic, closed-universe theories, each with an exact bar
and a stop rule, deliberately deferring execution. This phase executes the
cheap ones (Tier 1: seconds each; Tier 2: minutes each), in one pass, with
no parameter tuning after seeing any result.

## Method

All nine items are deterministic and exhaustive over a small, pre-declared
candidate universe — no stochastic search, so none of them need the
execution-lock/checkpoint machinery Phase 516's annealing search required.
Implemented as `tools/gsmg/phase517_closed_system_untried_theory_batch.py`,
one function per item, reusing existing validated primitives
(`phase484a_raw_symbol_vic_solver.segment_raw`, `binary_key_material_backfill.private_key_details`,
`nibble_packing_audit.evaluate_materials`, `raw_asset_byte_password_audit.run`,
`p1a_sentinel_backfill.eligible_candidates`, `cb_common.aes_try_open_bytes`).

**A real bug was caught and fixed during development, not after publishing
results**: the first draft's generic homomorphism-violation helper keyed by
the wrong side of the comparison (the coarse 9-symbol alphabet instead of
the fine 25-letter alphabet) for item 10b, silently changing the reported
violation counts (79/70/485 instead of the correct 59/49/449) without
changing the negative disposition. Caught by cross-checking the refactored
script's output against the original interactive numbers rather than
trusting the refactor — the fix is now pinned as a regression assertion in
`self_test()`.

## Results

**Tier 1**

| Item | Test | Result |
|---|---|---|
| 1a | DBBI as the checkerboard encoding of FAED's row/column/diagonal sum list (112 sum-list cells; 5 length-matched DBBI-pair cells, including the noticed FAED-19×30-column/`a0i8` = 63-digit coincidence) | All 5 length-matched cells fail the exact homomorphism bar (41–57 violations against a required 0) |
| 1b | FAED as the last words before the Architect's "choice" (29 valid escape pairs) | 746–853 bijection violations, every pair |
| 1c | DBBI as the same, mirrored | 82–122 violations, every pair |
| 6 | DBBI minus its zero-digit (`a`) as a 33-byte key/pubkey, 8 candidates (2 byte orders × 4 readings) | Compressed-pubkey reading fails structurally (leading byte `0x40`, not `0x02`/`0x03`) before any address check; 0 hits on the other 3 readings against the known address set |
| 4-primary | FAED as base-9 binary with a real file/crypto header, 16 byte-string candidates | 0 header matches (`Salted__`, gzip, zlib ×4, DER ×2, zip, PNG, PEM all absent) |
| 10b | Letter-class homomorphism: DBBI vs. `VALIDATION_ANSWER` and the decrypted Phase-3.2 plaintext; FAED vs. every 570-letter window of the full 34,833-letter Architect scene (34,264 windows) | 59, 49, and 449 violations respectively (need 0) |

**Tier 2**

| Item | Test | Result |
|---|---|---|
| 8 | Phase 381's 83-candidate frozen manifest (7 site assets + 76 creator-media payloads, 3 byte forms each), previously scoped to `P32TRAILING` only, now run against `SALPH`/`COSMIC`/`URLBLOB` | Self-test confirmed the manifest reproduces Phase 381 exactly; 89,640 effective decrypt attempts, 0 hits |
| 9 | "Some characters need to be zeroed out" applied literally to the three AES blobs at positions `{1,4,21}`/`{2,7,73}` × 3 modes (delete/set-`A`/set-`0`) | The literal base64-character-position reading is **structurally impossible**: 0 of 18 variants even parse as a valid `Salted__` blob, because those positions fall inside the base64 encoding of the 8-byte header itself. The ciphertext-byte-offset reading (bypassing the header): 12 of 18 variants stay AES-block-aligned; 1,008 decrypt attempts against the frozen 42-sentinel password set, 0 hits |
| 7 | The Lo Shu magic square as a third, thematically-selected a–i digit convention (8 symmetries), re-run against Phase 513's giant-decimal trick and the item-4 header check | 11 of 16 bodies valid (5 rejected on the same odd-hex-length structural gate Phase 513 uses); printable ratios in the same 34–53% noise range as prior closed cells; 0 header matches; 0 blob-oracle hits across 33 unique password materials |

Zero hits, zero consistent cells, zero header matches across all nine items.

## Disposition

All nine items close negative under their pre-declared exact bars. Item 9's
literal reading is eliminated structurally, not merely by a failed search —
a stronger and more informative negative than the others. Item 1a's noticed
length coincidence (FAED's 19×30 column sums = 63 digits, matching DBBI's
`{b,e}` token count) does not survive the actual consistency test, a
concrete demonstration of why the brainstorm doc treated it as a "first
gate to run," not evidence. None of the nine items reopen or close any
entry in [GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md); they remove
nine specific closed-system possibilities the coverage matrix and the
2026-09-17 brainstorm had flagged as genuinely untried.

Not run in this pass (explicitly deferred, not silently dropped): item 1b's
Phase-512 CSP pass at widths 15/19/30 (hours-scale); item 2 (DBBI's
diagonal sums as FAED's transposition key, hours-scale); item 5 (the
23/16/7 cipher-census bookkeeping, a reading task, not compute); item 7's
full re-sweep of item 1a's 112-cell family under all 8 Lo Shu symmetries
(low expected value — item 1a already failed decisively under both
existing conventions, and changing only the digit *values* is unlikely to
rescue a homomorphism-consistency failure of this size); item 4's
secondary tier (725,760-string blind alphabet-map sweep).

## Facts affected

None.

## Supersedes/corrects

None (the argument-order bug described above was caught and fixed before
any result was reported or committed).

## Artifacts

- `tools/gsmg/phase517_closed_system_untried_theory_batch.py` — all nine
  tests, self-test with a pinned regression assertion.
- `tools/gsmg/test_phase517_closed_system_untried_theory_batch.py` — full
  test suite (9 tests, ~90s, dominated by items 8/9's oracle sweeps).
- [doc/Brainstorms/2026-09-17 - Closed-System Untried Theory Classes.md](Brainstorms/2026-09-17%20-%20Closed-System%20Untried%20Theory%20Classes.md) —
  the pre-registration this phase executes.

## Reopen condition

Any of the nine items only reopens on a new creator source, primary
artifact, or authenticated selector specific to that item's own
construction (a different Architect-scene boundary, a different zeroing
convention with page support, a different digit-convention selector, etc.)
— not on re-running the same construction again.
