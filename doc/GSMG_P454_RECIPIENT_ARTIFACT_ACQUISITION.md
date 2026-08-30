---
type: audit
phase: 454
date: 2026-08-29
status: complete
result: two-recipient-copies-known-bytes-no-new-primary-artifact
disposition: provenance-upgrade-no-gap-closure
script: tools/gsmg/phase454_recipient_artifact_acquisition.py
---

# Phase 454 — Recipient-Side Artifact Acquisition

## Question

Can a bounded search of recipient-controlled surfaces recover a primary GSMG
artifact or genuinely new bytes capable of reopening an evidence-blocked P0
gap?

Protocol:
[Phase 454 Recipient-Side Artifact Acquisition Protocol](Brainstorms/2026-08-29%20-%20Phase%20454%20Recipient-Side%20Artifact%20Acquisition%20Protocol.md).

This phase is acquisition and provenance work. It does not treat a community
claim, an exact-looking construction, or a newly discovered URL as a puzzle
answer. Every candidate was classified before semantic interpretation under
Phase 409's fabrication controls.

## Frozen scope

The protocol fixed five lanes before searching:

1. all local Git refs, reflogs, unreachable objects, historical paths, and LFS;
2. four exact GitHub repository queries followed by branches, tags, releases,
   forks, and only new path/digest deltas;
3. four Internet Archive metadata queries, excluding another Wayback page
   sweep;
4. two canonical Reddit posts, one Bitcointalk topic, the canonical GitHub
   issue tracker, and Hosterjack's compendium; and
5. eight exact search-engine queries with one-hop expansion only for a concrete
   URL, repository, commit, attachment, archive identifier, digest, or path.

No outreach, private login, people search, form submission, rolling query
expansion, decryption, password generation, or oracle was allowed.

The frozen evidence manifest is:

    tools/gsmg/phase454_acquisition_manifest.json
    SHA-256 0a3ccbedbf0d5b4e68d4a6e02594eedc74af23aef0a341fd39eae5404b230b44

## Results by lane

### Local Git recovery

The pre-network snapshot contained 7 refs and 454 reflog entries. `git fsck`
reported 400 unreachable blobs:

- 397 map to paths in an unreachable tree;
- the remaining three are two sealed evidence-packet variants and the Phase
  418 panel script;
- exactly one blob is binary, PNG object
  `968bf89351284262be1f72adca7bceee46f2bf15`; and
- three separate trees name that PNG
  `gsmg_puzzle_stage1_383838_highlighted_red.png`.

The PNG is an older analytical annotation, not a recipient copy of creator
material. All other unreachable objects are generated code, reports,
registries, or prior project snapshots. No LFS pointer or hidden historical
source bundle was found.

### GitHub repositories, forks, refs, and releases

The four frozen repository queries returned counts `3`, `5`, `0`, and `0`,
with five unique repositories. The [canonical repository](https://github.com/puzzlehunt/gsmgio-5btc-puzzle)
reported 83 forks; the public API returned 73. It has one branch and no tags or
releases. Newly created unmodified forks point exactly at upstream commit
`fb92dd15487c6e2d275adb8c923698b7166c328e`.

Three deltas merited inspection:

| Source | Reproducible contents | Classification | Disposition |
|---|---|---|---|
| [BESCLLC fork](https://github.com/BESCLLC/gsmgio-5btc-puzzle), branch `claude/rbb-aoi-final-steps-lrhddw`, commit `1764ae61` | 58 historical paths: solver code, negative logs, copied puzzle material, and a `yellowblueprimes -> (-41,-17)` interpretation | `new_community_derivative` | Its claimed hand-retrieved SalPhaseIon stream equals the authenticated local first textarea byte-for-byte after removing one terminal LF. The coordinate interpretation is post-hoc community analysis, not new source bytes. |
| [Naddiseo fork](https://github.com/Naddiseo/gsmgio-5btc-puzzle), `15b43fc..207e1e1` | 3 commits, 4 changed paths: FEFE parity, yellow/blue counts, and the known SalPhaseIon route | `known_duplicate` | Repeats observations already held by this project and supplies no recipient artifact. |
| [mkno03 repository](https://github.com/mkno03/GSMG-5BTC-Crypto-Puzzle-Solver), commit `a9ea57b2` | 12 paths containing scripts, reports, chat transcripts, and a purported final plaintext | repository: `new_community_derivative`; final claim: `metadata_or_recollection_only` | The claimed `blob.b64` and `HIT_blob.bin` inputs are absent, so its final chain cannot be reproduced. The material includes copied public plaintext and self-described chat output, not primary evidence. |

The known [Hosterjack compendium](https://github.com/HosterjackAGV/gsmg-5btc-puzzle)
remains at commit `28d33ccb`, with three branches, no tags, and no releases. Its
two non-default branches contain only game/arcade code relative to the already
audited main history.

### Internet Archive metadata

The exact metadata queries for `"gsmg.io"`, `"theseedisplanted"`,
`"SalPhaseIon"`, and `title:("5 BTC puzzle") AND gsmg` each returned zero
items from the [Internet Archive advanced-search API](https://archive.org/advancedsearch.php).
This is `no_result`; it does not restate the already-exhausted Wayback finding.

### Fixed discussion roots and attachments

The two canonical Reddit discussions
([2019 challenge announcement](https://www.reddit.com/r/bitcoinpuzzles/comments/bf7siz/gsmgio_5_btc_puzzle_challenge/),
[2019 solver thread](https://www.reddit.com/r/bitcoinpuzzles/comments/dfwcqk/gsmgio_5_btc_puzzle/))
and the fixed [Bitcointalk topic](https://bitcointalk.org/index.php?topic=5532424.0)
contained no new downloadable artifact link.

The [canonical GitHub issue tracker](https://github.com/puzzlehunt/gsmgio-5btc-puzzle/issues)
contained 95 issues and 65 unique uploaded-attachment URLs:

| Disposition | URLs | Unique downloaded digests |
|---|---:|---:|
| `new_community_derivative` | 15 | 15 |
| `fabricated_or_spam` | 49 | 21 within that class |
| `access_limited` | 1 | 0 |
| **Downloaded total** | **64** | **35 globally** |

The large collapse from 64 files to 35 digests comes mainly from the same
terminal and spectrogram screenshots being re-uploaded under fresh attachment
UUIDs. Attachments in issues 37, 38, 39, 40, 41, 44, 46, 55, 67, and 69 were quarantined under the
already-documented reconstructed/fabricated claim networks; other uploads are
solver annotations, screenshots, recollections, and transformed puzzle images.
None is creator-authored or a byte-level recipient copy of a missing source.

Every URL, occurrence, author, issue, retrieval status, SHA-256, byte count,
format, dimensions, and classification is pinned in:

    tools/gsmg/phase454_attachment_ledger.json
    SHA-256 0d251386762fc84628197700d6b7e05b4a25d3d9066480109892386cb0d4dadb

### Search-engine lane: two real provenance upgrades

The eight exact queries produced two defensible recipient-copy confirmations.

First, a [urlscan capture of `theseedisplanted`](https://urlscan.io/result/1d6c83ab-a73e-4177-b70e-627d57072839/)
records a manual scan at `2019-11-14T08:27:53Z`, a main-response digest
`51b2d93b...68f856d3`, the hidden page's resource topology, and eight image
digests. All eight image SHA-256 values exactly match this project's eight
local Stage-1 icons. The old DOM, content, and screenshot payload endpoints
now return 403/404, so no new bytes can be acquired from them.

Second, a [server-daten report for `theseedisplanted`](https://check-your-website.server-daten.de/?q=gsmg.io%2Ftheseedisplanted)
preserves three screenshots created at `2025-07-12T11:47:30Z`, confirms the
known POST target `https://gsmg.io/phase1verification`, and enumerates the
same eight icon paths. The recovered screenshot digests are:

- mobile: `7b7a4dc4...23be92fc`;
- mobile landscape: `0a13a7bd...2a02c0ee`; and
- desktop: `72d2ebc5...9e4c25e6`.

Both captures are classified `new_recipient_copy_known_bytes`. They
independently strengthen chronology and byte provenance for a solved Stage-1
page. They contain no new clue, route, page state, selector, or consumer.

## Provenance and fabrication gate

Before interpretation, every claimant-bearing source was checked against:

- Phase 409's two spam payer addresses;
- the six-account mutually citing fabrication cluster;
- reproducibility from present bytes rather than prose;
- claimant continuity and chronology;
- independence from already-copied public material; and
- whether a source existed before the claimed discovery.

No candidate in Phase 454 passed as `new_primary_artifact`. The two recipient
copies passed as genuine but known-byte provenance. Community results were not
fed into a cryptographic oracle.

## Disposition

`provenance_upgraded_no_new_clue_content`.

- new primary artifacts: `0`;
- new recipient copies of known bytes: `2`;
- gap closures: `0`;
- oracle calls: `0`;
- password materials generated: `0`; and
- external outreach: `false`.

`G-MSL-001`, `G-ESC-001`, and `G-YIN-001` remain parked at P0. Their closure
conditions require a source that supplies a missing operation, selector,
consumer, interaction, or genuinely new authenticated variant. Better
provenance for already-solved Stage 1 does not meet those conditions.

The deterministic result artifact is:

    tools/gsmg/phase454_result.json
    SHA-256 58b46ae96afc5d7d0ef36015edbe36ab45cab7cd559b95e20b12b4d414bc654e

Reproduce the offline evidence checks:

    python3 tools/gsmg/phase454_recipient_artifact_acquisition.py --self-test
    python3 -m unittest tools/gsmg/test_phase454_recipient_artifact_acquisition.py
    python3 tools/gsmg/phase454_recipient_artifact_acquisition.py --report

## Reopen condition

Reopen acquisition only for a concrete new repository/ref/release, attachment,
archive identifier, source-map route, recipient bundle, or independently
verifiable digest. Do not rerun the same eight search queries or repeat the
same fixed-root attachment inventory on a schedule. A changed artifact must
start a versioned protocol and pass the same provenance gate before clue
analysis.
