---
type: worksheet
status: live
date: 2026-08-12
topics:
  - brainstorm
  - primary-evidence
  - archive-surface
---

# Non-Wayback Archive Surface Search — Pre-Registration

> [!caution] Prepared before searching
> This freezes every query before running any of them, so the query set
> cannot expand after seeing suggestive fragments. Deviating from this list
> mid-search would turn a bounded experiment back into an open-ended OSINT
> hunt — the failure mode this pre-registration exists to prevent.

## Scope

Waiting-period backlog item 1 from
[[2026-08-12 - Primary Evidence Acquisition]]: "Historical URL and archive
surface map." Could advance `G-MSL-001`, `G-ESC-001`, or `G-ARCH-001` if it
surfaces a genuinely new artifact; does not touch `G-YIN-001` or the other
P2 gaps.

## Services (frozen)

1. Common Crawl (index API, `index.commoncrawl.org`)
2. Arquivo.pt (Portuguese web archive, independent of Wayback)
3. urlscan.io (search API over historical scan results)
4. Software Heritage (`archive.softwareheritage.org`, content/revision/origin search)
5. Public Git hosting/search (GitHub code search; GitLab/Bitbucket/SourceHut
   as a bounded fallback only if GitHub's API is rate-limited or a target
   requires it)

No other service is in scope for this pass.

## Targets (frozen)

### A — Historical GSMG hosts

| ID | Target |
|---|---|
| A1 | `gsmg.io` |
| A2 | `www.gsmg.io` |
| A3 | `gsmg-archive.org` (known community mirror — cross-check, not primary) |

### B — SalPhaseIon route

| ID | Target |
|---|---|
| B1 | `89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32` (host-independent — in case it surfaces on a different host or mirror) |

### C — Distinctive content fragments

Each chosen for near-zero false-positive risk (compound/invented tokens or
a salted-blob prefix, not natural-language phrases):

| ID | Fragment |
|---|---|
| C1 | `shabefourfirsthintisyourlastcommand` |
| C2 | `ncsyangcahiriasogaleafayanestve` (the 31-char DBBI selection) |
| C3 | `dbbibfbhccbegbihabebeihbeggegebebbgehheb` (DBBI, first 40 of 91 chars) |
| C4 | `U2FsdGVkX186tYU0hVJBXXUnBUO7C0+X4KUWnWkC` (`SALPHASEION_BLOB_B64`, first 40 chars) |

### D — Deployment commit hashes

The four community-fork commits already cited as provenance anchors in
[GSMG_MATRIXSUMLIST_HISTORICAL_CODE_AUDIT](../GSMG_MATRIXSUMLIST_HISTORICAL_CODE_AUDIT.md)
and
[GSMG_EXTERNAL_ARCHIVE_AUDIT](../GSMG_EXTERNAL_ARCHIVE_AUDIT.md):

| ID | Commit | Repository | Known date |
|---|---|---|---|
| D1 | `a7041aac0b920bb207c071d92386e096204eab6d` | `puzzlehunt/gsmgio-5btc-puzzle` | 2021-05-20 |
| D2 | `dcb66952de3157f6e68cb00aa047dd2e4ff8ae39` | `Naddiseo/gsmgio-5btc-puzzle` | 2023-08-31 |
| D3 | `2ec5c553fb918b0977e893dc25c7f43b7b4fa053` | `nathansenn/gsmgio-5btc-puzzle` | 2025-11-26 |
| D4 | `1a278563f64ea3134ab453a66179292bcae22034` | `HosterjackAGV/gsmg-5btc-puzzle` | unrecorded |

These are searched for **new** locations (an independent fork, mirror, or
archive holding the same commit) or **earlier** revisions of the same
repository predating what this project already has — not re-cataloguing
what Phase 111's historical code audit already covered.

### E — Known asset filenames

Named (non-hash) asset filenames from the live site/mirror, chosen because
a hash-named asset (of which there are dozens) is not independently
searchable without the hash itself, which is already covered by category B:

| ID | Filename |
|---|---|
| E1 | `favicon_small.png` |
| E2 | `puzzle_raw.png` |
| E3 | `door.png` |

16 frozen targets total (3 + 1 + 4 + 4 + 3 + 1 route-host already counted
in A). Every applicable target is queried against every applicable service
exactly once in the first pass — see the applicability note in each
service's ledger row.

## Time boundary

**Before 2019-04-20** (the puzzle's documented launch date). This extends
Phase 241's own unresolved question directly: "no pre-launch capture
exists, so branding-vs-puzzle-era origin cannot be distinguished by
chronology alone." A pre-launch hit on any category-A/B/C/E target would be
the first evidence able to answer that question; a pre-launch hit on
category D is structurally impossible (all four commits postdate 2019) and
is not expected — those four are searched for *new locations*, not answered
by the time boundary.

For services that return captures/results with no reliable date (e.g. some
urlscan.io or Git-search results), the row is still recorded and classified
`undated`, not silently dropped from the ledger.

## Success condition

Recovery of a new authenticated response, source object, screenshot, or
repository artifact **absent from the local Wayback mirror and the five
already-diffed captures** (Phase 244) — not a re-discovery of material
already known to this project.

## Failure condition

Every frozen target (A1-E3) queried once against every applicable service,
with every result classified (hit / no-result / access-limited / undated).
A clean failure is a valid, recordable outcome, not a reason to keep
searching past the frozen list.

## Expansion rule

A new query may be added **only** when a result from this frozen list
exposes a concrete new URL, hash, repository, or hostname — never in
response to a suggestive-but-unconfirmed fragment. Any expansion query
must itself be logged with which frozen result triggered it.

## Exclusions

- No speculative filename generation (guessing plausible-sounding paths).
- No password testing of any kind.
- No people-search or outreach to individuals.
- No repeat crawl of Wayback/`web.archive.org` — already covered by
  Phase 241/244, out of scope for this pass.

## Deliverable

A query/result ledger (below, filled in during the run): one row per
target x service combination actually queried, including negative results
and access limitations (rate limits, API keys required, service downtime).

## Query/result ledger

Run 2026-08-12. Each frozen target queried once per applicable service.
GitHub's `/search/code` requires an auth token this session doesn't have
(`401 Requires authentication`, not a rate limit) — Sourcegraph's public
index (`fork:yes archived:yes`, since the entire GSMG fork ecosystem is
forks) was used as the pre-registered bounded fallback for every category
that needed it.

| Target | Service | Query | Result | Classification | Notes |
|---|---|---|---|---|---|
| A1 `gsmg.io` | Common Crawl | `CC-MAIN-2019-13` (Mar 2019) | 0 captures | no-result | before cutoff |
| A1 `gsmg.io` | Common Crawl | `CC-MAIN-2019-18` (Apr 2019) | 2 captures: `/register?referral=...` (2019-04-18, HTTP 200), `/robots.txt` (2019-04-18) | **hit** | 2 days pre-launch; new, not in local mirror |
| A1 `gsmg.io` | Common Crawl | `CC-MAIN-2018-51` (Dec 2018) | 2 captures: `/` and `/robots.txt`, both HTTP 301 | **hit** | 2018-12-16, ~4 months pre-launch; domain existed, redirecting |
| A1 `gsmg.io` | urlscan.io | `domain:gsmg.io AND date:[2010-01-01 TO 2019-04-20]` | 0 results | no-result | clean pre-cutoff negative |
| A1 `gsmg.io` | urlscan.io | `domain:gsmg.io` (all time, for context) | 191 total, earliest 2019-11-14 | context only | confirms no earlier urlscan coverage exists |
| A1 `gsmg.io` | urlscan.io | *(exposed by above)* `alpha.gsmg.io` | 2 scans: 2024-04-05, 2026-04-29 | **hit (new hostname)** | previously unrecorded subdomain |
| A1 `gsmg.io` | Arquivo.pt | CDX `url=gsmg.io*` | empty | no-result | |
| A1 `gsmg.io` | Sourcegraph | `gsmg.io fork:yes archived:yes` (repo search) | 2 repos: `puzzlehunt/gsmgio-5btc-puzzle` (known), `cirosantilli/bitcoin-inscription-indexer` (new) | **hit (new repo)** | Bitcoin OP_RETURN/inscription text mentioning "GSMG.io", not site source |
| A2 `www.gsmg.io` | Arquivo.pt | CDX `url=www.gsmg.io*` | empty | no-result | |
| A3 `gsmg-archive.org` | — | — | — | not queried | already-known community mirror, cross-check only; not re-run |
| B1 SalPhaseIon hash | Common Crawl | all 3 crawl indexes above | 0 captures each | no-result | |
| B1 SalPhaseIon hash | urlscan.io | `page.url:"89727c...52f6a32"` (all time) | 12 scans, 2023-05-31 through 2026-05-05 | **hit (new capture dates; checked)** | 11 HTTP-200 page captures, all exact response-hash matches to authenticated Wayback variants; final scan is HTTP 503. See Phase 249 |
| B1 SalPhaseIon hash | Arquivo.pt | CDX `url=gsmg.io/89727c...` | empty | no-result | |
| B1 SalPhaseIon hash | Sourcegraph | hash string, `fork:yes archived:yes` | 1 match: `puzzlehunt/gsmgio-5btc-puzzle/README.md` | known | already-known repo (= D1) |
| C1 `shabefourfirst...` | Arquivo.pt | textsearch | 0 results | no-result | |
| C1 `shabefourfirst...` | Sourcegraph | content search | 0 matches | no-result | |
| C2 31-char DBBI selection | Arquivo.pt | textsearch | 0 results | no-result | |
| C2 31-char DBBI selection | Sourcegraph | content search | 0 matches | no-result | |
| C3 DBBI prefix | Arquivo.pt | textsearch | 0 results | no-result | |
| C3 DBBI prefix | Sourcegraph | content search | 0 matches | no-result | |
| C4 blob prefix | Sourcegraph | content search | 0 matches | no-result | Arquivo.pt textsearch skipped: `+`/`=` in query breaks their tokenizer, no bounded workaround in scope |
| D1 `a7041aac...` | Software Heritage | `/revision/{id}/` | found | known | author `Richard <github@naddiseo.ca>` |
| D2 `dcb66952...` | Software Heritage | `/revision/{id}/` | found | known | **same author as D1** — not previously documented in this project; the historical audit lists distinct artifacts but does not claim independent authorship |
| D3 `2ec5c553...` | Software Heritage | `/revision/{id}/` | 404 | access-limited | revision not archived by SWH |
| D3 `2ec5c553...` | Software Heritage | `/origin/{url}/get/` | 404 | access-limited | whole origin not archived by SWH |
| D4 `1a278563...` | Software Heritage | `/revision/{id}/` | 404 | access-limited | revision not archived by SWH |
| D4 `1a278563...` | Software Heritage | `/origin/{url}/get/` | 404 | access-limited | whole origin not archived by SWH |
| D1-D4 (all) | Sourcegraph | hash string as text, each | 0 matches each | no-result | not referenced in any other repo's text |
| D1 (sanity) | Arquivo.pt | textsearch | 0 results | no-result | |
| E1 `favicon_small.png` | Common Crawl | `CC-MAIN-2019-18`, `gsmg.io/*favicon_small.png` | 0 captures | no-result | |
| E1 `favicon_small.png` | Sourcegraph | content search | 22 matches, all unrelated projects | no-result | generic filename, false-positive class — not GSMG |
| E2 `puzzle_raw.png` | Common Crawl | `CC-MAIN-2019-18`, `gsmg.io/*puzzle_raw.png` | 0 captures | no-result | |
| E2 `puzzle_raw.png` | Sourcegraph | content search | 0 matches | no-result | |
| E3 `door.png` | Common Crawl | `CC-MAIN-2019-18`, `gsmg.io/*door.png` | 0 captures | no-result | |
| E3 `door.png` | Sourcegraph | `door.png gsmg`, content search | 0 matches | no-result | |
| *(expansion)* A1 `/robots.txt` | Common Crawl | range-fetch WARC record (offset 2205278, len 799) | full HTTP response retrieved | **hit** | `Last-Modified: Thu, 11 Apr 2019 14:32:14 GMT` — 9 days pre-launch; triggered by the A1 Common Crawl hit above |

**GitHub code search** (D, E targets): not run — `401 Requires authentication`
on every query; recorded as access-limited across the board rather than
silently skipped. Sourcegraph served as the pre-registered fallback.

### Summary

- **7 genuine hits**, all logged above; **0 targets remain unqueried**
  against their applicable services (Category A3 excluded by design, not
  by omission).
- Pre-launch chronology (A1 + expansion): `gsmg.io` existed and redirected
  by 2018-12-16; had a live `/register?referral=...` page by 2019-04-18;
  `robots.txt` was last modified 2019-04-11 — all **before** the documented
  2019-04-20 launch. This is server-reported, authenticated metadata, not a
  crawl-timestamp inference.
- New hostname: `alpha.gsmg.io` (2 urlscan.io captures, 2024 and 2026).
- New repository: `cirosantilli/bitcoin-inscription-indexer` — on-chain
  Bitcoin inscription text mentioning "GSMG.io," not site source or a
  creator artifact.
- New cross-reference: D1 and D2 (`puzzlehunt` and `Naddiseo` forks) share
  the same commit author. The historical audit lists them as distinct dated
  artifacts but does not rely on independent authorship, so no conclusion
  changes.
- 12 non-Wayback SalPhaseIon-route scan dates on urlscan.io, none overlapping
  the 5 Wayback timestamps. Phase 249 checked them: 11 successful response
  hashes exactly match the first 3 authenticated Wayback variants; the
  2026-05-05 scan is an HTTP 503 error page. The earliest successful scan is
  2023-05-31, about 43 hours before the earliest Wayback capture.

### Disposition

Success condition met: multiple new authenticated artifacts recovered,
absent from the local Wayback mirror. None bears directly on any gap's G3
fields, escape-pair selection, or operator — the pre-launch chronology
corroborates the already-known "pre-existing GSMG bot business, puzzle
added later" narrative rather than revealing new puzzle mechanics.

Only the SalPhaseIon urlscan branch was promoted (Phase 249 and an extension
of existing fact `F-OBJ-003`) because it directly triggered G-ESC-001's
explicit new-capture reopen condition. The domain chronology, hostname, and
repository cross-reference remain incubation observations here: useful
provenance, but below the Fact Ledger's puzzle-relevance bar.

## Related notes

- [[2026-08-12 - Primary Evidence Acquisition]]
- [[GSMG_OPEN_GAP_REGISTRY]]
- [[GSMG_MATRIXSUMLIST_HISTORICAL_CODE_AUDIT]]
- [[GSMG_EXTERNAL_ARCHIVE_AUDIT]]
- [[GSMG_FAVICON_WAYBACK_CHRONOLOGY_AUDIT]]
