# Phase 530 — DBBI 84-parse payload oracle protocol

Date: 2026-09-20  
Status: prepared for execution lock; no result inspected

## Candidate universe

The only inputs are Phase 529's five frozen bases and their exact 90 standard
forms. The GPU tool must regenerate the forms from the five-line base file with
`--newline-variants`; its startup count must equal 90.

## Consumer and oracle

Reuse the unchanged, already self-tested Phase-527 GPU oracle:

- four tracked encrypted blobs: SALPH, COSMIC, P32TRAILING, URLBLOB;
- 60 AES variants = four fixed KDFs × three AES key sizes × five modes;
- strong printable, exact structural, raw-key Bloom/API, and eight known-target
  address detectors; and
- mandatory GPU/CPU parity self-test before the real candidates.

The container image, GPU UUID, Bloom cache, protocol, runner, Phase-529 result,
and base list must be pinned in an execution lock before the oracle runs.

## Execution and stop rule

Run once, resumably, with a fresh Phase-530 checkpoint and output files. Any
strong, structural, funded, or known-target hit requires manual positive
review. Weak printable rows are descriptive and must be CPU-rederived before
interpretation. Zero decisive hits closes exactly these five bases under the
standard expansion and the fixed oracle. No mutation, retry seed, added form,
SEED-CBC side lane, or consumer expansion is licensed.

