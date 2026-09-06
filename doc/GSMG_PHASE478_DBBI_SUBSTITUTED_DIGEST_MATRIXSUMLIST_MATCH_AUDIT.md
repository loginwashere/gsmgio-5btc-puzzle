# Phase 478: DBBI `{b,g}` substituted-digest matrixsumlist match

## Question

Is DBBI, segmented under escape pair `{b,g}` into a 64-token, 16-type
sequence, a monoalphabetically-substituted lowercase-hex SHA-256 digest of
some byte string this project has already constructed, in some prior
phase, as a candidate serialization or output of `matrixsumlist`? Full
motivation, provenance, and frozen construction are in the protocol:
`doc/Brainstorms/2026-09-05 - Phase 478 DBBI Substituted-Digest
Matrixsumlist Match Protocol.md`. This document reports execution and
result only.

## Execution facts

**First discovery lock**, SHA-256
`649c4f9710c8ddae2c26b2c92d22d51d878a59d0d4c7cbd1c058e050c50eb039`,
was superseded after real-harvest diagnostics surfaced a capture-completeness
gap, a dependency-isolation gap, several under-timed recipes, two broken
recipes, and the final `zero_candidate_policy` set — see the protocol's
own amendment history for the full account. No Phase 478 digest-match
statistic was computed at any point during that diagnostic work.

**Final discovery lock** (`tools/gsmg/phase478_discovery_lock.json`) pins
23 `generator+oracle` files at cutoff commit `64f8063939d1d4d89402b87f88aa22b8fb956a7b`.
The real harvest (`tools/gsmg/phase478_run_harvest.py`) produced
`tools/gsmg/phase478_raw_capture.jsonl`: all 23 locked files ran to
`status: ok`; the 5 files carrying a locked `zero_candidate_policy`
(`adjacent_diff_sweep.py`, `digraphic_sweep.py`,
`native_prime_zeroing_sweep.py`, `prefix_boundary_sweep.py` under
`historical_significance_gate_closed`, and `faed_monoalphabetic_sweep.py`
under `historical_escalation_never_executed_no_frozen_threshold`) each
produced exactly 0 candidates, matching their frozen policy; the other 18
produced real candidates. Total: **1,749,878 candidates**.

**Manifest construction** (`tools/gsmg/phase478_build_manifest.py`,
17/17 synthetic self-tests) consumed the raw capture and
`tools/gsmg/phase478_manifest_annotations.json` — per-file
`construction_label`/`transformation`/`phase`/`eligible` annotations
written by direct reading of all 18 candidate-bearing source files at the
pinned cutoff commit (confirmed byte-identical to the working tree via
`git diff` for every one of them), matching call sites to constructions by
caller line number alone. This is a provenance/classification step; no
candidate SHA-256 or equality pattern was computed here.

Result: **1,749,878 manifest entries**, one per raw candidate (the
harvester's own per-file capture already deduplicated by bytes; the
manifest step introduced no further collapsing). Structural review (counts,
encoding sanity, eligibility completeness — no candidate content hashed):
all 1,749,878 entries `eligible: true` (no documented retraction or
supersession was found, on an explicit search of `doc/*.md` and
`tools/gsmg/findings/*.md`, naming any of the 18 constructions); 3,913
entries matched more than one construction (the same bytes legitimately
produced by two historical code paths — concentrated in
`salph_cosmic_phase341_eligibility_audit.py`, whose `widen_oracle_coverage`
transitively invokes Phase 0.1's own `lastcommand_probe.probe()`); 0 base64
decoding failures; phase attribution recovered for 2 of the 18 files
(`door_prime_passport_probe.py` → 4, `salph_cosmic_phase341_eligibility_audit.py`
→ 341), `unknown` for the remaining 16 (no phase number was discoverable
from the source file's own docstring or a matching `findings/P*.md`, and
none was guessed).

**Matcher** (`tools/gsmg/phase478_run_matcher.py`, 12/12 synthetic
self-tests, using a real SHA-256 of a chosen fixture literal scored
against its own genuinely-computed pattern for positive cases — never a
searched preimage of an arbitrary target, and never DBBI's real pattern)
computes `SHA256(bytes).hexdigest()` and compares its `equality_pattern`
(frozen in `tools/gsmg/phase478_common.py`, self-tested against DBBI's
target on import) to the target, for every `eligible: true` entry only.

**Oracle lock** (`tools/gsmg/phase478_oracle_lock.json`) pins the
manifest's SHA-256 (`0952c327a310b8956fd128d6b6c82581bfdc217188a4d4043fbe19779b4c0145`),
the frozen DBBI pattern, and the matcher script's own SHA-256, issued
before any candidate digest was computed.

## Result

The matcher was run once, against the locked manifest, per the protocol's
stop rule — reported exactly as produced, no re-run with adjusted scope.

```json
{
  "eligible_scored": 1749878,
  "target_pattern": "01234556728966286abc61c88b48de3086dd501d5557d6bab5605233df7bbb96",
  "match_found": false
}
```

**No match.** Best miss (descriptive only, not a criterion):
`tools/gsmg/hash_duality_sweep.py`, 24/64 matching positions. This is
descriptive only: no family-maximum null calibration was preregistered, so
no significance is assigned to the value.

## Disposition

Bounded negative. This closes exactly:

> DBBI `{b,g}` as a monoalphabetically-substituted lowercase-hex SHA-256
> digest of every `eligible: true` byte string in the locked harvested
> manifest (1,749,878 entries across the 23-file closed candidate universe).

It does not close, per the protocol's own "Bounding the result" section:
any meaning of `matrixsumlist` not already constructed as an
oracle-submitted candidate by this project as of the cutoff commit; any
candidate-generating source outside the frozen 96-file discovery superset;
any normalization not already present in the source code (double-hashing,
alternate case/whitespace, non-hex or uppercase-hex rendering); the
`{b,e}` segmentation or any other escape pair; or any non-digest reading
of DBBI. No classified direct-crypto-bypass or recipe-less file remained
excluded inside the frozen superset: the COSMIC direct-crypto path was
covered by its locked adapter. The 36-pair postselection correction (worst
case ×36) does not apply to this negative result — it was relevant only to
how strong a *hit* would have been.

## Post-run verification qualification

The locked matcher verifies the manifest hash, DBBI pattern, and its own
script hash before scoring. Although the oracle lock also pins
`phase478_common.py`, the locked matcher does not itself enforce that
module's hash before importing its `equality_pattern` implementation. The
current module's hash was independently checked against the oracle lock and
matched exactly; the saved report was then reproduced byte-for-byte by the
locked matcher. `tools/gsmg/phase478_verify_run.py` makes that external
enforcement explicit: it checks every file hash named by the oracle lock,
imports the matcher only after those checks pass, recomputes the result, and
requires exact equality with the saved report. This is a verifier-enforcement
omission in the original locked matcher, not a change to the result.

## Verification

```
cd tools/gsmg
python3 test_phase478_matrixsumlist_candidate_harvester.py   # 31/31
python3 test_phase478_run_harvest.py                          # 28/28
python3 test_phase478_build_manifest.py                       # 17/17
python3 test_phase478_run_matcher.py                          # 12/12
python3 test_phase478_verify_run.py                             # 8/8
python3 phase478_verify_run.py phase478_oracle_lock.json phase478_match_report.json /tmp/verification.json
```

Re-running the matcher reproduces `phase478_match_report.json` exactly
(deterministic manifest order, no randomness in scoring).

## Artifacts

`doc/Brainstorms/2026-09-05 - Phase 478 DBBI Substituted-Digest
Matrixsumlist Match Protocol.md` (frozen protocol), this audit doc,
`tools/gsmg/phase478_discovery_lock.json`, `phase478_oracle_lock.json`,
`phase478_common.py`, `phase478_matrixsumlist_candidate_harvester.py`,
`phase478_harvest_driver.py`, `phase478_adapter_cosmic_raw_digest.py`,
`phase478_run_harvest.py`, `phase478_raw_capture.jsonl`,
`phase478_manifest_annotations.json`, `phase478_build_manifest.py`,
`phase478_manifest.jsonl`, `phase478_run_matcher.py`,
`phase478_match_report.json`, `phase478_verify_run.py`,
`phase478_verification.json`, the five
`test_phase478_*.py` modules, and `phase478_artifact_checksums.json`
(96/96 passing). The raw capture and annotated manifest are reproducible
generated artifacts kept outside ordinary Git because of their size; their
hashes are retained in the checksum record (and, for the manifest, the
oracle lock).
