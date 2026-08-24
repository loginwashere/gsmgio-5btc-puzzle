---
type: index
status: live
topics:
  - brainstorm-backlog
  - frontier-assumption-ledger
  - topology-audit
---

# GSMG Brainstorm Backlog Ledger

**Purpose.** Brainstorm documents in `doc/Brainstorms/` record their own
execution status inline (`[!info] Executed...` callouts, status tables,
checkboxes), but that status frequently goes stale the moment a *later*
phase or a *different* brainstorm document closes an item — the item's own
file is never revisited to say so. This ledger cross-references every
still-relevant brainstorm item against `tools/gsmg/FINDINGS.md` so a
checkbox never has to be trusted at face value again: each row here is
independently verified against the phase it claims closes it, not copied
from the brainstorm doc's own claim.

**Scope.** This ledger covers the P32-trailing attack-surface families,
the post-Phase-340 search portfolio seeds, and the P0A canonical-sentinel
backfill — the frontier-relevant brainstorm material, i.e. everything
feeding the currently open P0/P1 gaps (`G-MSL-001`, `G-ESC-001`,
`G-YIN-001`, `G-ARCH-001`). QR-texture and creator-profile brainstorm
lines were spot-checked (all closed through Phase 365 with no stale
checkboxes found) and are not itemized below since they carry no open
backlog item.

**Status values:**
- `executed` — run to completion, disposition recorded, verified against
  FINDINGS.md.
- `superseded` — closed by a broader external or later result without
  itself being run (e.g. the fork's independent sweep).
- `partially-executed` — the core question was answered but a declared
  sub-part (an artifact, a formalization, a corpus) was deliberately
  deferred, not forgotten.
- `parked` — deliberately deferred pending a named precondition (a policy
  decision, new evidence), not simply unscheduled.
- `genuinely-unrun` — no execution recorded anywhere; still a live backlog
  candidate.

```yaml
item: "P32 Family 1 -- residual cross-blob salt-relationship audit"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: superseded
verified_against: "FINDINGS.md Phase 271"
note: "closed by the independent HosterjackAGV fork's own ~35,000-combination salt/cross-blob sweep, strictly broader than this family's pre-registered table; not run locally"
```

```yaml
item: "P32 Family 2 -- transaction-graph trace beyond the first hop"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "GSMG_P32_FAMILY2_TRANSACTION_GRAPH_AUDIT.md (Phase 383)"
note: "three-source authenticated trace over 125 prize-address and 44 halving-address transactions (164 unique): only the two pre-existing 2020/2024 halving self-spends are signed by a seed address; both use only prize-address inputs and output only to the prize/halving addresses; 0 direct co-input candidates, 0 new output addresses, 0 new route. Exact raw bytes for both signed transactions are pinned for Family 9"
```

```yaml
item: "P32 Family 3 -- raw binary asset bytes as password material"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "FINDINGS.md Phase 381"
note: "83-candidate pinned manifest (7 site assets with pre-2023 provenance -- favicon_small.png independently confirmed against a live Wayback CDX capture, the other 6 asserted by the local mirror tool's own manifest and pinned in a committed PROVENANCE.json rather than independently re-verified -- 3 already committed, 4 newly copied into doc/img/site_mirror/ -- + 76 unique creator-authored Telegram payloads dated before P32TRAILING's own chronology-graph bound, content-pinned by a canonical payload-set digest enforced on both self-test and the real --run path, drawn from Phase 248's frozen 88-record/83-unique-payload universe -- corrected three times same-day: round 1 fixed 4 miscategorized browser screenshots and 11 live-2026 site-mirror fetches, round 2 fixed round 1's own image-only mirror filter missing 3 pre-cutoff images plus 1 font and added the content digest pin, round 3 enforced that digest pin in the actual run path (previously self-test-only) and fixed a 55-vs-53 excluded-entry miscount), 3 byte forms each (literal, raw SHA-256 digest, hex SHA-256), P32TRAILING only per the source doc's own initial-scope rule, full current-oracle convention (84 configs), 29,880 effective decrypt attempts, 0 hits"
```

```yaml
item: "P32 Family 4 -- numeric/temporal metadata as password material"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: genuinely-unrun
verified_against: n/a
note: "exact and bounded (declared decimal/hex/ISO-date serializations only) but poorly selected -- no clue names a specific number as password material, so this is a coverage sweep, not a targeted test"
```

```yaml
item: "P32 Family 5 -- external community candidate mining, fabrication-checked"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: genuinely-unrun
verified_against: n/a
note: "lowest priority in source doc (9 of 8+1); high noise given this project's own demonstrated spam/fabrication history (debunked GitHub/bitcointalk campaign), but cheap and bounded if run with the declared provenance discipline"
```

```yaml
item: "P32 Family 6 -- exact blob-literal and code-context archaeology"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "FINDINGS.md Phase 271"
note: "run against the pinned HosterjackAGV fork tree; no hidden decrypt call/ordering/parameter found beyond what this project already knows; surfaced family 10's four leads"
```

```yaml
item: "P32 Family 7 -- authoring-toolchain calibration from solved stages"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: partially-executed
verified_against: "Post-Phase-340 Future Search Portfolio.md, Seed 3 investigation pass (2026-08-20, not a separate FINDINGS phase)"
note: "core cryptographic finding complete: all three solved AES boundaries (Phase 2/3/3.2) share one observable profile -- SHA-256 digest as lowercase hex text, legacy single-round EVP_BytesToKey/SHA-256, AES-256-CBC, PKCS#7, OpenSSL Salted__ Base64. NOT yet consolidated into a standalone, complete provenance audit artifact -- genuinely unrun as a dedicated deliverable"
```

```yaml
item: "P32 Family 8 -- blob-centric first-appearance and co-occurrence graph"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "FINDINGS.md Phase 344 (run as Post-Phase-340 Seed 5)"
note: "22 nodes, 26 edges across contains/published-before/same-authenticated-object; zero chronology violations among 11 well-dated edges; one new adjacency surfaced (2021-12-26 hint precedes earliest SalPhaseIon capture by ~17 months), flagged as a scoping candidate only"
```

```yaml
item: "P32 Family 9 -- transaction serialization and wallet-style fingerprint"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: genuinely-unrun
verified_against: n/a
note: "version/nLockTime/sequence/pubkey-encoding/sighash-style/repeated-ECDSA-r comparison; Family 2's prerequisite is now satisfied by the exact two-transaction raw cache in doc/evidence/GSMG_P32_FAMILY2_SIGNED_TRANSACTION_CACHE.json, so this family is unblocked"
```

```yaml
item: "P32 Family 10 -- fork-surfaced residual leads"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "FINDINGS.md Phase 292"
note: "4 leads (VIC alphabet alternate reconstruction, Safenet/Luna/HSM digit-glued fragments, genesis coinbase headline decoded, orphan CIAO-BELLA-O token), 15 candidates, 720 effective decrypt attempts, 0/4 hits on every lead. Lead 2's 'ordering key' reading remains formally unexecuted (no independently-sourced reordering rule exists), not disproven"
```

```yaml
item: "P32 Family 11 -- hexadecimal-nibble packing of the 9-ary streams"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "FINDINGS.md Phase 272"
note: "closed negative; FAED yields eight exact 285-byte bodies, DBBI always leaves an unpaired nibble; 0 signatures, 0 decompressions, 0 oracle hits from 24 materials"
```

```yaml
item: "P32 Family 12 -- exact inverse of the page's decimal transport"
source: "2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md"
status: executed
verified_against: "FINDINGS.md Phase 273"
note: "closed negative; both known-instruction positive controls round-trip correctly, but DBBI/FAED outputs under all 8 variants are binary noise with 0 oracle hits"
```

```yaml
item: "Post-Phase-340 Seed 1 -- solved-boundary rule audit with leave-one-out stress tests"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 341"
note: "all 3 known AES boundaries (Phase 2/3/3.2) recover their exact preimage at rank 1 under a frozen instruction-parsing rule engine; positive/calibration-only disposition, not puzzle progress by itself. Forward-transferred to P32TRAILING by Phase 370 -- 0 genuinely new candidates"
```

```yaml
item: "Post-Phase-340 Seed 2 -- typed decode-and-parse ladder"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 342"
note: "150,141 segments across the full Phase 336-338 corpus; 0 structural findings, 0 exact-target hits. Percent-decoding and nested-Salted__-decrypt were explicitly out of scope"
```

```yaml
item: "Post-Phase-340 Seed 3 -- solved-vector authoring-toolchain calibration"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: partially-executed
verified_against: "in-document investigation pass, 2026-08-20 (same item as P32 Family 7 above)"
note: "duplicate of P32 Family 7 -- see that row for status detail"
```

```yaml
item: "Post-Phase-340 Seed 4 -- content-addressed decrypt transcript and coverage ledger"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: parked
verified_against: "FINDINGS.md Phase 343"
note: "coverage-ledger half built (tools/gsmg/coverage_ledger.py); the raw-body plaintext-transcript half was intentionally deferred pending a sensitive-data storage policy decision -- not forgotten, blocked on a named precondition"
```

```yaml
item: "Post-Phase-340 Seed 5 -- blob chronology and dependency graph"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 344"
note: "duplicate of P32 Family 8 above -- see that row"
```

```yaml
item: "Post-Phase-340 Seed 6 -- multi-blob concordance before aggregate language scoring"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 348"
note: "18,144 pair hypotheses, real maximum 0 events, 1,000-trial permutation null also 0, p=1.0; closes only this exact structural-concordance registry, does not license D1's weak aggregate-language scoring"
```

```yaml
item: "Post-Phase-340 Seed 7 -- input-byte pathway reconstruction"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 378, corrected/completed by Phase 379, closed by Phase 392"
note: "evidence-backed subset run: raw SHA-256 digest bytes (COSMIC precedent) and trailing space/LF/CRLF bases (Phase 163 hash-tool finding), 756 new materials against the frozen 42-candidate P0A/P1A corpus, 0 hits. Phase 378 understated as full-oracle (missed 18 CBC-extended configs) and had an unexercised Key Wrap result-handling bug; Phase 379 fixed the bug (with a synthetic positive-path regression) and ran the missing 54,432-application delta, still 0 hits -- 362,880 effective decrypt attempts total across CBC+ECB+stream+Key Wrap. The remaining three pathways (textContent-vs-selection, HTML entity decoding, JS UTF-16/low-byte conversion) were left genuinely unrun pending evidence; Phase 392 checked the actual authenticated SalPhaseIon source directly and found zero HTML entities, zero non-ASCII bytes, zero inline scripts (one external Cloudflare beacon only), and zero nested child tags inside either DBBI/FAED textarea -- all three pathways are inapplicable to this source, so no encoding sweep was run. Seed 7 is now fully closed."
```

```yaml
item: "Post-Phase-340 Seed 8 -- remaining exact secret-container formats"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 350"
note: "executed as a strict Phase-342 delta -- BIP38, Casascius mini keys, all 12 SLIP-132 versions, output descriptors, Bitcoin Core key/ckey/mkey records; 750,895 validator invocations, 0 structurally valid containers, 0 exact-target hits"
```

```yaml
item: "Post-Phase-340 Seed 9 -- checksum-guided one-error repair"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: parked
verified_against: n/a
note: "gated on a near-valid object existing first (WIF/extended-key/Bech32/mini-key/BIP39 with a checksum-decidable single-error repair); no such near-valid object is currently on record, so there is nothing to run this against yet"
```

```yaml
item: "Post-Phase-340 Seed 10 -- ciphertext-length and output-role compatibility matrix"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phase 385"
note: "CBC/PKCS#7 row from the 2026-08-20 pass, plus stream-mode (exact-length) and compression (zlib/gzip/bz2/lzma) rows added by Phase 385: compression cannot shrink base58 role text, but container overhead alone rescues several short-form roles (BIP38, mini-key, WIF) into the short blobs' CBC window, so length-only exclusion for SALPH/P32TRAILING must name its compression assumption. Framed/variable-length objects (prefix/suffix/label/JSON/container) remain permanently non-excludable by length alone, same as DER/mnemonic phrases -- not a residual task, an inherent limit of this technique"
```

```yaml
item: "Post-Phase-340 Seed 11 -- new-evidence diff watch"
source: "2026-08-20 - Post-Phase-340 Future Search Portfolio.md"
status: executed
verified_against: "FINDINGS.md Phases 347, 349"
note: "three-URL passive baseline established (347), made repeat-safe with a monthly read-only heartbeat (349); passive GETs only, no forms/wallet actions/scripts; the only item in this ledger that could directly reopen the evidence-blocked P0 gaps without a cryptographic hit"
```

```yaml
item: "P0A Model 11 (81+10 FSM) sentinel backfill"
source: "2026-08-15 - Canonical Sentinel Inventory (P0A).md"
status: executed
verified_against: "FINDINGS.md Phase 335"
note: "report-plumbing fix closed (output_text field added, no new transform); 42-candidate corpus, 2,016 effective decrypt attempts, 0 hits, model 11's 2 candidates verified separately from the original 40"
```

```yaml
item: "Phase 163 Tier-1 --whitespace-variants nopad rerun"
source: "tools/gsmg/FINDINGS.md (not a brainstorm document)"
status: genuinely-unrun
verified_against: n/a
note: "~700,000 keystrings, estimated 1-2 hours; source-grounded coverage gap but low expected value and unlikely to resolve the topology. User declined to run it (2026-08-22)"
```

```yaml
item: "Raw-key chunk audit over Phase 378/379's byte-pathway materials"
source: "preregistered during Phase 378/379 review (2026-08-23), not from a brainstorm document"
status: executed
verified_against: "FINDINGS.md Phase 380"
note: "tests whether the right password in the existing 756-material corpus could produce binary secp256k1 key material the printable-text/structural-binary gate discards; first-two-32-byte-chunk convention ported from doc/GSMG_GPU_ORACLE.md; 72 non-Key-Wrap configs, 109,317 bodies, 218,634 chunks, frozen 10-address known-target set (PRIZE_ADDRESS/HALVING_ADDRESS + 8 EC-derived neighbors), 0 hits"
```

```yaml
item: "P32 Family 3 raw-asset-byte manifest, excluded-file classes"
source: "FINDINGS.md Phase 381 (2026-08-23, corrected same-day)"
status: parked
verified_against: n/a
note: "Phase 381 (twice-corrected version) excludes: 4 confirmed browser screenshots (phase2/phase3/theseedisplanted/SalPhaseIonCosmicDuality.png, Phase 162); favicon.png + both favicon SVGs + 8 icon crops + lato-regular-webfont.woff2 + every other non-/shared/ mirror entry with a 2025/2026 fetch timestamp, confirmed live fetches of the operator-unresolved restored site, not puzzle-era (6 image/font entries WITH pre-cutoff timestamps -- favicon_small.png, logo_medium.png, background-full.jpg, front_bg_1920.svg, front_bittrex.svg, lato-regular-webfont.woff -- are included, not excluded); 53 non-image/font pre-cutoff mirror entries (register-referral pages, app.js/vendor.js bundles, app.css, .js.map -- out of Family 3's declared image/font scope); all 55 /shared/ mirror entries (dynamically-generated preview artifacts); favicon.ico (empty); photo_2020-04-26_09-24-30.jpg (G-X2SH-001's chronology conflict); 33 Telegram shortlist community images + thumbnails; 3 annotated vovam-thread images; 7 creator-media records dated on/after 2023-09. All by provenance/chronology/scope reasoning, not by evidence disproving them -- if a future phase establishes pre-P32TRAILING provenance for any excluded file, it becomes a single-file manifest addition, not a reason to redo Phase 381"
```

## Reading this ledger

Every `genuinely-unrun` row above is a live backlog candidate; every other
status is closed as far as this ledger currently knows and should not be
independently re-derived from a brainstorm document's own checkboxes
without checking this ledger (or `git log`/`FINDINGS.md`) first, since
those checkboxes are demonstrably prone to going stale across documents.

## Recommended next bounded experiment

**P32 Family 3 (raw authenticated asset bytes)** was executed 2026-08-23
as Phase 381 — negative, see that row above. Its own source document's
bounding rules (2026-08-14) were applied as written: only two provenance
classes (authenticated site-response bytes, one creator-posted Telegram
original) as core candidates, exclude thumbnails/OCR/renders/research-
generated files, deduplicate by SHA-256, exactly three byte forms
(literal file bytes, binary SHA-256, lowercase SHA-256 hex), `P32TRAILING`
only, and a chronology exclusion for assets tied to later-reached puzzle
stages. This closes the family as scoped — it does not reopen without new
evidence about one of the excluded files' provenance (see the
`P32 Family 3 raw-asset-byte manifest, excluded-file classes` row above).

**P32 Family 2 (transaction-graph trace)** was executed as Phase 383. The
125+44 histories contain only two seed-signed transactions, both already-known
halving self-spends, with zero additional co-input or output addresses. Its
negative result closes the evidence-acquisition family and produces the exact
raw-transaction cache that unblocks Family 9 (transaction serialization
fingerprint).

## Related documents

- [GSMG Frontier Assumption Ledger](GSMG_FRONTIER_ASSUMPTION_LEDGER.md)
- [GSMG Topology Audit](GSMG_TOPOLOGY_AUDIT.md)
- [GSMG Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md)
- [P32 New Attack Surfaces Beyond Text Recombination](Brainstorms/2026-08-14%20-%20P32%20New%20Attack%20Surfaces%20Beyond%20Text%20Recombination.md)
- [Post-Phase-340 Future Search Portfolio](Brainstorms/2026-08-20%20-%20Post-Phase-340%20Future%20Search%20Portfolio.md)
- [Canonical Sentinel Inventory (P0A)](Brainstorms/2026-08-15%20-%20Canonical%20Sentinel%20Inventory%20%28P0A%29.md)
