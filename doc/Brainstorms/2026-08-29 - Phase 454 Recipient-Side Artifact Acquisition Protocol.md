---
type: hypothesis
phase: 454
date: 2026-08-29
status: frozen
topics:
  - primary-evidence
  - recipient-side
  - provenance
  - external-search
  - archive
---

# Phase 454 — Recipient-Side Artifact Acquisition Protocol

> [!caution] Frozen before searching
> This is a bounded acquisition pass, not another candidate/password search.
> Search terms, surfaces, provenance gates, expansion rules, and stop rules are
> fixed below before any external query is run.

## Question

Do recipient-controlled surfaces preserve any original GSMG puzzle bytes,
saved pages, screenshots, forwarded media, source bundles, or historical
repository objects that are absent from the project's authenticated artifact
inventory and capable of changing a P0/P1 gap's source object, operator,
boundary, or chronology?

This implements item 6 in
[Post-Phase-452 Scientific Experiment Portfolio](2026-08-29%20-%20Post-Phase-452%20Scientific%20Experiment%20Portfolio.md).

## Scope separation

Already exhausted and excluded:

- generic external P32 candidate mining (Phase 409);
- another Wayback or SalPhaseIon page-capture diff (Phases 241/243/244/249);
- known Telegram media and thumbnails (creator-media completeness audits);
- known Naddiseo notebooks/attachments and HosterjackAGV catalog trees;
- broad source-code archaeology over already-audited canonical revisions;
- password, decryption, or blob-oracle work.

This phase looks for copies preserved by recipients, not another semantic
interpretation of known bytes.

## Frozen surfaces

### L — Local Git object recovery

Read-only inspection of this repository's complete Git object store:

1. every reachable commit/tree/blob under all refs;
2. reflogs and `git fsck --full --unreachable --no-reflogs`;
3. unreachable blob size/type/signature inventory;
4. historical paths suggesting images, archives, saved HTML, Telegram exports,
   notebooks, source maps, or puzzle assets;
5. Git LFS pointer inventory.

Unreachable objects remain in place. Candidate bytes may be copied only to a
temporary quarantine directory for hashing/type inspection; no checkout,
prune, repack, gc, reset, or object-store mutation.

### G — GitHub recipient repositories

Use GitHub's public repository/fork/ref/release APIs and public web pages for
exactly four repository-search strings:

1. `gsmgio-5btc-puzzle`
2. `gsmg-5btc-puzzle`
3. `SalPhaseIon`
4. `theseedisplanted`

For every repository result:

- classify known versus new repository;
- enumerate public forks, branches, tags, and releases;
- record default-branch head, creation/update times, owner, fork parent, and
  tree identity where exposed;
- inspect only files whose paths or digests are absent from the local known
  repository inventories;
- inspect release assets and repository ZIP contents only when present.

Known repositories remain useful as graph roots, not as permission to re-read
already-audited files.

### I — Internet Archive item metadata, excluding Wayback

Run exactly four Internet Archive metadata/full-text queries:

1. `"gsmg.io"`
2. `"theseedisplanted"`
3. `"SalPhaseIon"`
4. `title:("5 BTC puzzle") AND gsmg`

Inspect item file manifests only for returned items. The Wayback CDX/web
collection is excluded. A metadata-only mention is not an artifact.

### F — Fixed discussion-page attachment extraction

Inspect only attachment/media/download URLs exposed by these already-known
discussion roots:

1. the two Reddit posts linked by the repository README;
2. Bitcointalk topic `5532424.0` from Phase 409;
3. the canonical `puzzlehunt/gsmgio-5btc-puzzle` issue tracker;
4. the public HosterjackAGV compendium pages already identified by Phase 409.

Extract external image, attachment, raw-file, ZIP, gist, paste, and download
links. Ordinary hyperlinks to known puzzle pages or explanatory websites are
not attachment candidates.

### S — Fixed saved-copy/screenshot search

Run exactly eight search-engine queries:

1. `"gsmg.io" "saved page"`
2. `"gsmg.io" "saved webpage"`
3. `"gsmg.io" screenshot puzzle`
4. `"SalPhaseIon" screenshot`
5. `"SalPhaseIon" zip`
6. `"theseedisplanted" screenshot`
7. `"theseedisplanted" zip`
8. `"gsmg.io" mirror download`

Only inspect results containing a concrete file, attachment, repository, or
saved-page bundle. Search snippets and recollections are leads, not evidence.

## Expansion rule

One-hop expansion is allowed only when a frozen result exposes a concrete new:

- repository/fork URL;
- branch, tag, release, or commit identifier;
- attachment/download URL;
- archive item identifier;
- content digest; or
- historical hostname/path embedded in recovered bytes.

Every expansion must record its parent frozen query/result. No synonym,
username, desired-clue, or interpretation-driven expansion is allowed.

## Phase 409 provenance gate

Every surfaced object is quarantined before semantic review and receives:

1. exact original URL/object ID and acquisition timestamp;
2. raw bytes where publicly retrievable without authentication;
3. byte length, media type, and SHA-256;
4. earliest defensible timestamp and what supplied it;
5. creator/community/unattributed classification;
6. claimant history and provenance continuity;
7. spam/fabrication checks against the Phase 156/409 address and account
   clusters;
8. duplication check against local artifact and repository manifests;
9. independent corroboration status;
10. explicit reason it can or cannot bear on a registered gap.

Known Phase 409 spam payer addresses:

- `1JG648yaB7Wp2dpUfcZoRSD4q35oq47vCu`
- `145ZQ9siLrsXBKf465wjdyQYAP5dRwhRhQ`

Known fabricated-SOLVED account cluster:

- `GalloClaudio64`
- `andersonbig`
- `WabiLipa`
- `valleytainment`
- `robotixcoder`
- `zemnovodnuy`

A source is not promoted merely because it contains desired language. A
creator-authored or independently preserved original byte object is stronger
than a later solver transcription; an unattributed screenshot may establish
historical display state but not creator intent.

## Classifications

Every result receives exactly one:

- `new_primary_artifact`
- `new_recipient_copy_known_bytes`
- `new_community_derivative`
- `known_duplicate`
- `metadata_or_recollection_only`
- `fabricated_or_spam`
- `access_limited`
- `no_result`

Only `new_primary_artifact` can directly satisfy a gap's primary-source closure
condition. Other classes may improve chronology or provenance but cannot be
silently upgraded.

## Success condition

At least one byte-bearing object absent from existing local manifests survives
the provenance gate as `new_primary_artifact` or
`new_recipient_copy_known_bytes`.

## Failure condition

All frozen surfaces are exhausted and every result is classified, with no
surviving new byte-bearing object. A clean negative closes this bounded pass,
not the possibility that a private recipient copy exists elsewhere.

## Required outputs

- machine-readable query/result ledger;
- Git object/repository/ref inventories;
- quarantined-object ledger with hashes and provenance classifications;
- explicit expansion-parent relationships;
- coverage totals and access limitations;
- gap-bearing decision for every surviving object;
- complete negative accounting if nothing survives.

## Stop rules

- No outreach, messaging, people-search, account login, form submission, wallet
  action, script execution from recovered content, or private-source access.
- Passive public GET/API/search only.
- No passwords, decryption, candidate generation, blob/address oracle, GPU,
  Docker, or external agents.
- Do not execute or render active HTML/JavaScript from recovered bundles.
- Do not mutate Git objects or repository history.
- Stop when all L/G/I/F/S rows and licensed one-hop expansions are classified.

## Reopen condition

Reopen only for a newly identified recipient, repository, archive item,
attachment, content digest, or public source not available in this pass—not a
periodic rerun of unchanged queries.

