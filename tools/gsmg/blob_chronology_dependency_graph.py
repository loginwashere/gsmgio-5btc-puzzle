"""Seed 5 (Phase 344): blob chronology / dependency graph.

Frozen per the user's explicit scope for seed 5: nodes are the four tracked
blobs (SALPH/COSMIC/P32TRAILING/URLBLOB), the three solved boundaries
(puzzle Phase 2/3/3.2), page revisions, Telegram artifacts, repository
appearances, and a handful of directly-relevant clues; only three edge
types (`contains`, `published_before`, `same_authenticated_object`); three
separate date fields per node (`observed_at`, `probably_authored_at`,
`first_publicly_seen`) so a directly-observed capture time is never
conflated with an inferred authorship bound; and no guessed timestamp
anywhere -- every date or bound below is copied verbatim from an existing
FINDINGS.md phase or doc/GSMG_*.md audit, cited on the node/edge itself.
This is a synthesis pass over already-documented facts, not a new
cryptanalytic or provenance investigation: it does not decode anything and
touches no password material.

IMPORTANT disambiguation this module is careful about throughout: "puzzle
Phase 2/3/3.2" (the three solved AES-256-CBC boundaries, per
doc/GSMG_PUZZLE.md) is completely unrelated to this project's own sequential
FINDINGS.md phase numbering (e.g. "FINDINGS Phase 25", "FINDINGS Phase
244"). Node ids use `solved_phaseN` for the former; every citation string
below spells out "FINDINGS Phase N" for the latter to keep the two apart.

Per the user's explicit instruction: the restored (2026-08) live gsmg.io
deployment is modeled as a `page_revision` node with `attribution="unknown"`
-- FINDINGS Phase 329 explicitly left operator identity unresolved -- never
as a creator-attributed node, even though its content matches prior
archived material.

Phase 345 correction: Phase 344's original "new adjacency" finding (a
proposed 17-month gap between tg_hint_zeroed_out and the earliest ARCHIVED
SalPhaseIon capture) conflated "earliest Wayback/urlscan capture" with
"earliest public sighting". This repo's own git history -- commits
9d99692 (2021-03-20), 99bd811 and 8382341 (2021-05-07), all independently
re-verified via `git show` and an independent sha256 re-hash of the
screenshot -- documents the live page nearly two years earlier than the
2023-05-31 Wayback capture, and about 7 months BEFORE the hint, not after
it. The proposed gap is withdrawn; see repo_readme_hint_2021_03 and
repo_route_hash_2021_05 below.
"""
import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

NODE_TYPES = {"blob", "solved_boundary", "page_revision", "telegram_artifact",
              "repo_appearance", "clue"}
ATTRIBUTIONS = {"creator", "community", "this_project", "unknown"}
EDGE_TYPES = {"contains", "published_before", "same_authenticated_object"}


def _date_field_ok(value):
    if value is None or isinstance(value, str):
        return True
    if isinstance(value, dict):
        return set(value.keys()) <= {"not_before", "not_after"} and any(value.values())
    return False


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

NODES = {
    # -- blobs -----------------------------------------------------------
    "blob_salph": {
        "type": "blob", "label": "SALPH (SalPhaseIon embedded AES blob)",
        "containing_artifact": "SalPhaseIon page textarea",
        "attribution": "creator",
        "observed_at": None, "first_publicly_seen": None, "probably_authored_at": None,
        "note": "Literal base64 Salted__ AES blob embedded directly in the SalPhaseIon "
                "page text, no checkerboard decode needed to reach it.",
        "citation": "tools/gsmg/data.py:SALPHASEION_BLOB_B64 comment",
    },
    "blob_cosmic": {
        "type": "blob", "label": "COSMIC (Cosmic Duality embedded AES blob)",
        "containing_artifact": "Cosmic Duality page textarea",
        "attribution": "creator",
        "observed_at": None, "first_publicly_seen": None, "probably_authored_at": None,
        "note": "Larger AES ciphertext referenced by the community as the eventual "
                "endgame target once dbbi/faed are decoded.",
        "citation": "tools/gsmg/data.py:COSMIC_BLOB_B64 comment",
    },
    "blob_p32trailing": {
        "type": "blob", "label": "P32TRAILING (tail of solved Phase 3.2 plaintext)",
        "containing_artifact": "Phase 3.2 solved plaintext (embedded at its end)",
        "attribution": "creator",
        "observed_at": None,
        "first_publicly_seen": {"not_after": "2023-08"},
        "probably_authored_at": None,
        "note": "80-byte OpenSSL blob embedded at the end of the already-solved Phase "
                "3.2 plaintext (salt b45a5e3d827593ca). first_publicly_seen upper-bounded "
                "by the HosterjackAGV fork's 2023-08 push, which already documented it in "
                "detail as p32_trailing; not documented is when it first entered chat.",
        "citation": "FINDINGS Phase 25 (2026-07-24)",
    },
    "blob_urlblob": {
        "type": "blob", "label": "URLBLOB (hex-encoded blob in a gsmg.io URL path)",
        "containing_artifact": "gsmg.io URL PATH itself (not the response body)",
        "attribution": "unknown",
        "observed_at": None, "first_publicly_seen": None, "probably_authored_at": None,
        "note": "QUARANTINED provenance: no official-README or solved-plaintext "
                "corroboration; the sourcing fork itself calls it 'orphaned' and reports "
                "no tested key decrypts it.",
        "citation": "tools/gsmg/data.py:URLBLOB_B64 comment; FINDINGS Phase 27 (2026-07-24)",
    },
    # -- solved boundaries -------------------------------------------------
    "solved_phase2": {
        "type": "solved_boundary", "label": "Puzzle Phase 2 boundary ('causality')",
        "containing_artifact": "gsmg.io Phase 2/3 combined page (Thevenin/Norton riddle)",
        "attribution": "creator",
        "observed_at": None, "first_publicly_seen": None,
        "probably_authored_at": {"not_before": "2019-04-20"},
        "note": "This project did not originally solve this boundary -- reconstructed "
                "from the community fork's public README and independently re-derived "
                "end-to-end (rank 1, no ciphertext consulted until ranking frozen) in "
                "FINDINGS Phase 341.",
        "citation": "doc/GSMG_PUZZLE.md:90,103; FINDINGS Phase 341 (2026-08-20)",
    },
    "solved_phase3": {
        "type": "solved_boundary", "label": "Puzzle Phase 3 boundary (7-part chain)",
        "containing_artifact": "gsmg.io Phase 2/3 combined page (chess FEN + parts 2-7)",
        "attribution": "creator",
        "observed_at": None, "first_publicly_seen": None,
        "probably_authored_at": {"not_before": "2019-04-20"},
        "note": "Same reconstruction/re-verification note as solved_phase2.",
        "citation": "doc/GSMG_PUZZLE.md:90,104,107; FINDINGS Phase 341 (2026-08-20)",
    },
    "solved_phase3_2": {
        "type": "solved_boundary", "label": "Puzzle Phase 3.2 boundary (Beaufort THEMATRIXHASYOU)",
        "containing_artifact": "gsmg.io Phase 3.2 clue-answer + Beaufort stage",
        "attribution": "creator",
        "observed_at": None, "first_publicly_seen": None,
        "probably_authored_at": {"not_before": "2019-04-20"},
        "note": "Same reconstruction/re-verification note as solved_phase2.",
        "citation": "doc/GSMG_PUZZLE.md:108-109; FINDINGS Phase 341 (2026-08-20)",
    },
    # -- page revisions ------------------------------------------------------
    "page_favicon_2019": {
        "type": "page_revision", "label": "favicon_small.png, sole Wayback capture",
        "containing_artifact": "https://www.gsmg.io/img/favicon_small.png",
        "attribution": "unknown",
        "observed_at": "2019-04-28T23:47:09Z",
        "first_publicly_seen": "2019-04-28T23:47:09Z",
        "probably_authored_at": {"not_after": "2019-04-28"},
        "note": "SHA-256 934f46d6a0a168a7ca2af725604d7e1dab8ee825ad0d7c682dbb252cc2be1423; "
                "8 days after the documented 2019-04-20 puzzle launch. Only one capture "
                "exists, so branding-vs-puzzle-era origin is not chronologically decidable.",
        "citation": "FINDINGS Phase 241 (2026-08-11); doc/GSMG_FACT_LEDGER.md F-FAV-005",
    },
    "page_salph_v1": {
        "type": "page_revision", "label": "SalPhaseIon/Cosmic Duality HTML variant 1",
        "containing_artifact": "gsmg.io SalPhaseIon+Cosmic Duality page",
        "attribution": "unknown",
        "observed_at": "2023-05-31T02:49:16Z",
        "first_publicly_seen": "2023-05-31T02:49:16Z",
        "probably_authored_at": {"not_after": "2023-05-31"},
        "note": "sha256 18a8369df1364911d5e94fcac341ef85480ff194f4500f509fbed34f19e6308b, "
                "4556 bytes. Earliest of 16 known ARCHIVED capture events (5 Wayback + 11 "
                "urlscan) -- not the earliest public sighting overall: repo_route_hash_2021_05 "
                "(2021-05-07, this repo's own git history) documents the live page, "
                "screenshot and exact route, ~2 years earlier. Corrected by Phase 345 after "
                "Phase 344 conflated 'earliest archived capture' with 'earliest sighting'. "
                "Original authorship date remains undocumented either way.",
        "citation": "FINDINGS Phase 244, 249 (2026-08-11/12); doc/GSMG_FACT_LEDGER.md F-OBJ-003",
    },
    "page_salph_v2": {
        "type": "page_revision", "label": "SalPhaseIon/Cosmic Duality HTML variant 2",
        "containing_artifact": "gsmg.io SalPhaseIon+Cosmic Duality page",
        "attribution": "unknown",
        "observed_at": {"not_before": "2023-11-27T18:19:47Z", "not_after": "2024-04-16"},
        "first_publicly_seen": "2023-11-27T18:19:47Z",
        "probably_authored_at": None,
        "note": "sha256 ed6c395890553a2ef3e156f91111ef0ab503951c631717cb60ab1f72858459af, "
                "4556 bytes. Only diff from variant 1: an H1/h1 heading-case change; the "
                "dbbi/faed textarea span is byte-identical.",
        "citation": "FINDINGS Phase 244, 249 (2026-08-11/12)",
    },
    "page_salph_v3": {
        "type": "page_revision", "label": "SalPhaseIon/Cosmic Duality HTML variant 3",
        "containing_artifact": "gsmg.io SalPhaseIon+Cosmic Duality page",
        "attribution": "unknown",
        "observed_at": {"not_before": "2024-12-04T00:00:00Z", "not_after": "2026-04-05T15:42:27Z"},
        "first_publicly_seen": "2024-12-04",
        "probably_authored_at": None,
        "note": "sha256 0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0. "
                "Diffs from variant 2 are head-section whitespace and a Cloudflare "
                "analytics script version-token rotation only; the dbbi/faed textarea "
                "span remains byte-identical. 7 of 11 urlscan captures match this variant, "
                "through 2026-04-05 (the local mirror).",
        "citation": "FINDINGS Phase 244, 249 (2026-08-11/12)",
    },
    "page_urlblob_capture1": {
        "type": "page_revision", "label": "URLBLOB URL-path capture, complete (112 bytes)",
        "containing_artifact": "gsmg.io URL path (Wayback CDX)",
        "attribution": "unknown",
        "observed_at": "2026-01-05T01:59:08Z",
        "first_publicly_seen": "2026-01-05T01:59:08Z",
        "probably_authored_at": None,
        "note": "Complete capture: Salted__ + salt 74c974e3f92e64b5 + 96-byte ciphertext "
                "(6 clean AES blocks). Independently re-verified against the live Wayback "
                "CDX API, not just a fork's own docs.",
        "citation": "tools/gsmg/data.py:URLBLOB_B64 comment (2026-07-24 re-verification)",
    },
    "page_urlblob_capture2": {
        "type": "page_revision", "label": "URLBLOB URL-path capture, truncated duplicate (40 bytes)",
        "containing_artifact": "gsmg.io URL path (Wayback CDX)",
        "attribution": "unknown",
        "observed_at": "2026-02-07T19:00:55Z",
        "first_publicly_seen": "2026-02-07T19:00:55Z",
        "probably_authored_at": None,
        "note": "Truncated duplicate of the same path -- only 40 raw bytes (header + salt "
                "+ a 24-byte non-block-aligned remainder). The sourcing fork's docs cite "
                "this later, truncated capture as THE capture timestamp; this project's "
                "re-verification caught and corrects that inaccuracy.",
        "citation": "tools/gsmg/data.py:URLBLOB_B64 comment (2026-07-24 re-verification)",
    },
    "page_gsmgio_restored_2026": {
        "type": "page_revision", "label": "gsmg.io live restoration (2026-08)",
        "containing_artifact": "gsmg.io (Contabo/Dynadot deployment)",
        "attribution": "unknown",
        "observed_at": {"not_before": "2026-08-15T23:16:41Z", "not_after": "2026-08-17T16:09:49Z"},
        "first_publicly_seen": {"not_before": "2026-08-14", "not_after": "2026-08-15T23:16:41Z"},
        "probably_authored_at": None,
        "note": "FINDINGS Phase 329 explicitly left operator identity UNRESOLVED (fresh "
                "HTML reconstruction around known archived content, not a byte-for-byte "
                "restore of the original container; no cryptographic or fresh creator-"
                "identity signature found). Per the user's explicit instruction this node "
                "is deliberately attribution='unknown', not 'creator', regardless of how "
                "closely its content matches prior archives -- self-test enforces this.",
        "citation": "FINDINGS Phase 329 (2026-08-20)",
    },
    # -- telegram artifacts -----------------------------------------------
    "tg_genesis_post": {
        "type": "telegram_artifact", "label": "Creator genesis post ('Here is the GSMG Puzzle!')",
        "containing_artifact": "Telegram support group, messages 25986-25988",
        "attribution": "creator",
        "observed_at": "2019-04-01",
        "first_publicly_seen": "2019-04-01",
        "probably_authored_at": "2019-04-01",
        "note": "Pre-rabbit April-Fools puzzle caption + two binary payloads, from creator "
                "user9815232. Earliest documented creator-authored puzzle artifact.",
        "citation": "doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md:79",
    },
    "tg_hint_1_4_21": {
        "type": "telegram_artifact", "label": "Creator hint: 'another door on {1},{4},{21}'",
        "containing_artifact": "Telegram creator message",
        "attribution": "creator",
        "observed_at": "2021-04-01",
        "first_publicly_seen": "2021-04-01",
        "probably_authored_at": "2021-04-01",
        "note": "Describes what looks like a separate, still-open sub-puzzle, not "
                "obviously the same thing as dbbi/faed.",
        "citation": "FINDINGS.md line ~68-69 (Phase 2 writeup, 2026-07-03)",
    },
    "tg_hint_zeroed_out": {
        "type": "telegram_artifact", "label": "Creator hint: primes + 'zeroed out' characters",
        "containing_artifact": "Telegram creator message 8000 (lead-in message 7998, 2021-12-26T22:11:26)",
        "attribution": "creator",
        "observed_at": "2021-12-26",
        "first_publicly_seen": "2021-12-26",
        "probably_authored_at": "2021-12-26",
        "note": "Follow-up to tg_hint_1_4_21.",
        "citation": "doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md:213; FINDINGS.md Phase 2 writeup",
    },
    "tg_nonchat_artifact": {
        "type": "telegram_artifact", "label": "Creator-authored non-chat raw bit string",
        "containing_artifact": "Telegram, 2023-02-24T01:20:03, reply=None",
        "attribution": "creator",
        "observed_at": "2023-02-24T01:20:03Z",
        "first_publicly_seen": "2023-02-24T01:20:03Z",
        "probably_authored_at": "2023-02-24T01:20:03Z",
        "note": "A community member independently reacted to it one day later "
                "(message 8448, 2023-02-25).",
        "citation": "doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md:233-238,252",
    },
    # -- repository appearances --------------------------------------------
    "repo_naddiseo": {
        "type": "repo_appearance", "label": "Naddiseo/gsmgio-5btc-puzzle (community fork)",
        "containing_artifact": "cb2.py, joint_attack.py, faed_base9.py",
        "attribution": "community",
        "observed_at": None, "first_publicly_seen": None, "probably_authored_at": None,
        "note": "This project's own SALPH/COSMIC/DBBI/FAED constants were re-extracted "
                "programmatically (not retyped) from this fork's source, described as "
                "'the community's most rigorous public effort' at the time this project "
                "started. No publish date documented in this repo.",
        "citation": "tools/gsmg/data.py module docstring",
    },
    "repo_puzzlehunt_official": {
        "type": "repo_appearance", "label": "puzzlehunt/gsmgio-5btc-puzzle (official community repo)",
        "containing_artifact": "README.md",
        "attribution": "community",
        "observed_at": None, "first_publicly_seen": None, "probably_authored_at": None,
        "note": "This project's decoder was originally ported from this repo. Its README "
                "documents P32TRAILING verbatim.",
        "citation": "FINDINGS Phase 25 (2026-07-24)",
    },
    "repo_hosterjackagv": {
        "type": "repo_appearance", "label": "HosterjackAGV/gsmg-5btc-puzzle (actively-growing fork)",
        "containing_artifact": "docs/ATTEMPTS.md, docs/WALKTHROUGH.md, demos.js",
        "attribution": "community",
        "observed_at": None,
        "first_publicly_seen": {"not_after": "2023-08"},
        "probably_authored_at": None,
        "note": "Pushed 2023-08 (as of Phase 25), 109 stars / 76 forks, ~1.5M+ logged "
                "attempts. Per this project's own standing guidance this fork is "
                "actively-growing and re-mined periodically but treated with skepticism, "
                "not as a primary source.",
        "citation": "FINDINGS Phase 25 (2026-07-24)",
    },
    "repo_readme_hint_2021_03": {
        "type": "repo_appearance",
        "label": "puzzlehunt/gsmgio-5btc-puzzle README: SalPhaseIon/Cosmic Duality named",
        "containing_artifact": "README.md",
        "attribution": "community",
        "observed_at": "2021-03-20",
        "first_publicly_seen": "2021-03-20",
        "probably_authored_at": "2021-03-20",
        "note": "Commit adds: 'Hashing the text gets you to the next phase, SalPhaseIon & "
                "Cosmic Duality. Which text to hash, and which door to insert it into is not "
                "currently public knowledge...' -- names the phase but not yet its exact "
                "reachable route. Author Richard Eames ('Naddiseo'), a community researcher "
                "per doc/GSMG_PUZZLE.md, not the puzzle creator.",
        "citation": "this repo's own git history, commit 9d99692 (2021-03-20 14:24:27 -0600), "
                    "'Update README.md'; verified directly via `git show 9d99692`",
    },
    "repo_route_hash_2021_05": {
        "type": "repo_appearance",
        "label": "puzzlehunt/gsmgio-5btc-puzzle README: exact SalPhaseIon route + screenshot",
        "containing_artifact": "README.md, SalPhaselonCosmicDuality.png",
        "attribution": "community",
        "observed_at": "2021-05-07",
        "first_publicly_seen": "2021-05-07",
        "probably_authored_at": "2021-05-07",
        "note": "Two commits 13 minutes apart record the live page's exact reachable state. "
                "99bd811 (10:37:57 -0400) adds a 668x619 screenshot, sha256 "
                "a3810ba24250c5a04908e1281c2202e73f7487f9d19f41bfd2c3e55fa9be57ed -- "
                "independently re-hashed directly from this repo's git history, and the same "
                "hash doc/GSMG_SALPHASEION_RESPONSIVE_WRAP_AUDIT.md already cites and used "
                "for DBBI/FAED pixel-offset analysis (FAED ending at logical offset 765). "
                "8382341 (10:50:27 -0400) records 'SHA256(GSMGIO5BTCPUZZLECHALLENGE1"
                "GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe) = 89727c59...52f6a32' and the resulting "
                "live URL reaching 'the SalPhaseIon and Cosmic Duality phase'. This is the "
                "earliest documented public sighting of the live page in substantially its "
                "current DBBI/FAED form -- predating tg_hint_zeroed_out by ~7 months, not "
                "postdating it as Phase 344 originally reported.",
        "citation": "this repo's own git history, commits 99bd811 and 8382341 (2021-05-07); "
                    "verified directly via `git show` and independent sha256 re-hash; "
                    "corroborated by doc/GSMG_SALPHASEION_RESPONSIVE_WRAP_AUDIT.md",
    },
    # -- clues ---------------------------------------------------------------
    "clue_book_pages_57_58": {
        "type": "clue", "label": "Cosmic Duality book, physical pages 57-58",
        "containing_artifact": "Physical 'Cosmic Duality: Mysteries of the Unknown' book",
        "attribution": "community",
        "observed_at": "2026-08-13",
        "first_publicly_seen": "2026-08-13",
        "probably_authored_at": None,
        "note": "Recovered and reviewed: no operational numeric schema on either page; "
                "G-MSL-001's seven G3 fields still 0/7 fixed. Corrects an earlier draft "
                "of tools/gsmg/coverage_ledger.py that described these pages as still "
                "unrecovered (fixed the same day, FINDINGS Phase 343).",
        "citation": "FINDINGS Phase 259 (2026-08-13)",
    },
}


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------

EDGES = [
    # contains
    {"src": "page_salph_v1", "dst": "blob_salph", "type": "contains",
     "citation": "tools/gsmg/data.py:SALPHASEION_BLOB_B64 comment; FINDINGS Phase 244"},
    {"src": "page_salph_v1", "dst": "blob_cosmic", "type": "contains",
     "citation": "FINDINGS Phase 329: 'two textareas on the SalPhaseIon/Cosmic Duality page'"},
    {"src": "solved_phase3_2", "dst": "blob_p32trailing", "type": "contains",
     "citation": "tools/gsmg/data.py:P32_TRAILING_BLOB_B64 comment; FINDINGS Phase 25"},
    {"src": "repo_puzzlehunt_official", "dst": "blob_p32trailing", "type": "contains",
     "citation": "FINDINGS Phase 25"},
    {"src": "repo_hosterjackagv", "dst": "blob_p32trailing", "type": "contains",
     "citation": "FINDINGS Phase 25"},
    {"src": "repo_hosterjackagv", "dst": "blob_urlblob", "type": "contains",
     "citation": "tools/gsmg/data.py:URLBLOB_B64 comment (fork's demos.js)"},
    {"src": "page_urlblob_capture1", "dst": "blob_urlblob", "type": "contains",
     "citation": "tools/gsmg/data.py:URLBLOB_B64 comment"},
    {"src": "repo_naddiseo", "dst": "blob_salph", "type": "contains",
     "citation": "tools/gsmg/data.py module docstring"},
    {"src": "repo_naddiseo", "dst": "blob_cosmic", "type": "contains",
     "citation": "tools/gsmg/data.py module docstring"},

    # published_before (well-dated pairs)
    {"src": "tg_genesis_post", "dst": "page_favicon_2019", "type": "published_before",
     "citation": "2019-04-01 < 2019-04-28"},
    {"src": "page_favicon_2019", "dst": "page_salph_v1", "type": "published_before",
     "citation": "2019-04-28 < 2023-05-31"},
    {"src": "tg_hint_1_4_21", "dst": "tg_hint_zeroed_out", "type": "published_before",
     "citation": "2021-04-01 < 2021-12-26"},
    {"src": "tg_hint_zeroed_out", "dst": "page_salph_v1", "type": "published_before",
     "citation": "2021-12-26 < 2023-05-31 -- 2023-05-31 is the earliest ARCHIVED (Wayback/"
                 "urlscan) HTML capture only, not the earliest public sighting; see "
                 "repo_route_hash_2021_05 (2021-05-07), which predates this hint by ~7 "
                 "months. Phase 344's original 'gap' reading of this edge was withdrawn by "
                 "Phase 345 -- see repo_readme_hint_2021_03 and repo_route_hash_2021_05"},
    {"src": "repo_readme_hint_2021_03", "dst": "repo_route_hash_2021_05", "type": "published_before",
     "citation": "2021-03-20 < 2021-05-07"},
    {"src": "repo_route_hash_2021_05", "dst": "tg_hint_zeroed_out", "type": "published_before",
     "citation": "2021-05-07 < 2021-12-26 -- the live SalPhaseIon/Cosmic Duality page, "
                 "screenshot-documented with its exact reachable route, predates "
                 "tg_hint_zeroed_out; Phase 345 correction, this repo's own git history"},
    {"src": "page_salph_v1", "dst": "page_salph_v2", "type": "published_before",
     "citation": "2023-05-31 < 2023-11-27"},
    {"src": "page_salph_v2", "dst": "page_salph_v3", "type": "published_before",
     "citation": "2023-11-27 < 2024-12-04"},
    {"src": "page_salph_v3", "dst": "page_gsmgio_restored_2026", "type": "published_before",
     "citation": "2026-04-05 < 2026-08-15"},
    {"src": "page_urlblob_capture1", "dst": "page_urlblob_capture2", "type": "published_before",
     "citation": "2026-01-05 < 2026-02-07"},

    # published_before (solved-chain positive control -- structural/logical
    # ordering per doc/GSMG_PUZZLE.md's stage design, not date-based: no
    # exact authorship date is documented for any of the three, so the
    # consistency checker must accept this without treating missing dates
    # as a violation)
    {"src": "solved_phase2", "dst": "solved_phase3", "type": "published_before",
     "citation": "doc/GSMG_PUZZLE.md: Phase 3 content is reached only via the Phase 2 "
                 "answer -- structural dependency, no independent authorship dates documented"},
    {"src": "solved_phase3", "dst": "solved_phase3_2", "type": "published_before",
     "citation": "doc/GSMG_PUZZLE.md: Phase 3.2 is reached only via Phase 3 -- structural "
                 "dependency, no independent authorship dates documented"},
    {"src": "solved_phase3_2", "dst": "blob_p32trailing", "type": "published_before",
     "citation": "P32TRAILING is embedded inside the Phase 3.2 plaintext itself, so it "
                 "cannot have been authored before that plaintext existed"},

    # same_authenticated_object
    {"src": "page_salph_v1", "dst": "page_salph_v2", "type": "same_authenticated_object",
     "citation": "FINDINGS Phase 244: dbbi/faed textarea span byte-identical",
     "note": "dbbi_faed_span_only, not the whole HTML container"},
    {"src": "page_salph_v2", "dst": "page_salph_v3", "type": "same_authenticated_object",
     "citation": "FINDINGS Phase 244: dbbi/faed textarea span byte-identical",
     "note": "dbbi_faed_span_only, not the whole HTML container"},
    {"src": "page_salph_v3", "dst": "page_gsmgio_restored_2026", "type": "same_authenticated_object",
     "citation": "FINDINGS Phase 329: textareas byte-identical to the repository's archived "
                 "payload after whitespace normalization",
     "note": "normalized text content only -- Phase 329 explicitly found the restored HTML "
             "container itself is a fresh reconstruction, NOT a byte-for-byte restore"},
    {"src": "blob_salph", "dst": "repo_hosterjackagv", "type": "same_authenticated_object",
     "citation": "FINDINGS Phase 25: fork's 'salph_inner', salt-confirmed identical "
                 "(3ab585348552415d)"},
    {"src": "blob_p32trailing", "dst": "repo_hosterjackagv", "type": "same_authenticated_object",
     "citation": "FINDINGS Phase 25: fork's 'p32_trailing', salt-confirmed identical "
                 "(b45a5e3d827593ca)"},
    {"src": "blob_urlblob", "dst": "repo_hosterjackagv", "type": "same_authenticated_object",
     "citation": "tools/gsmg/data.py:URLBLOB_B64 comment: byte-for-byte match against the "
                 "fork's demos.js literal, independently cross-checked"},
    {"src": "repo_route_hash_2021_05", "dst": "page_salph_v1", "type": "same_authenticated_object",
     "citation": "doc/GSMG_SALPHASEION_RESPONSIVE_WRAP_AUDIT.md: pixel analysis of the same "
                 "screenshot locates FAED ending at logical offset 765, matching the known "
                 "DBBI/FAED structure",
     "note": "content correspondence only (screenshot vs. archived raw HTML bytes), not a "
             "byte-identical claim -- the screenshot is a rendered PNG, page_salph_v1 is the "
             "captured HTML source"},
]


# ---------------------------------------------------------------------------
# Chronology helpers
# ---------------------------------------------------------------------------

def _date_only(value):
    """Best-effort single comparable date (YYYY-MM-DD) for a node's date field,
    preferring the most concrete evidence. Returns None if nothing concrete."""
    if value is None:
        return None
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, dict):
        # A bound alone isn't a concrete instant; callers that need strict
        # ordering treat this as "no comparable date" (see _node_date below).
        return None
    return None


def _node_date(node):
    for field in ("observed_at", "first_publicly_seen"):
        d = _date_only(node.get(field))
        if d is not None:
            return d
    pa = node.get("probably_authored_at")
    if isinstance(pa, str):
        return pa[:10]
    return None


# ---------------------------------------------------------------------------
# Validation / reporting
# ---------------------------------------------------------------------------

def validate_structure():
    errors = []
    for node_id, node in NODES.items():
        if node["type"] not in NODE_TYPES:
            errors.append(f"{node_id}: bad type {node['type']!r}")
        if node["attribution"] not in ATTRIBUTIONS:
            errors.append(f"{node_id}: bad attribution {node['attribution']!r}")
        for field in ("observed_at", "first_publicly_seen", "probably_authored_at"):
            if not _date_field_ok(node.get(field)):
                errors.append(f"{node_id}: bad {field} value {node.get(field)!r}")
        for required in ("label", "containing_artifact", "note", "citation"):
            if not node.get(required):
                errors.append(f"{node_id}: missing {required}")
    node_ids = set(NODES)
    for i, edge in enumerate(EDGES):
        if edge["src"] not in node_ids:
            errors.append(f"edge {i}: unknown src {edge['src']!r}")
        if edge["dst"] not in node_ids:
            errors.append(f"edge {i}: unknown dst {edge['dst']!r}")
        if edge["type"] not in EDGE_TYPES:
            errors.append(f"edge {i}: bad type {edge['type']!r}")
        if not edge.get("citation"):
            errors.append(f"edge {i}: missing citation")
    return errors


def find_cycles():
    """DAG check over published_before edges only."""
    graph = {}
    for e in EDGES:
        if e["type"] == "published_before":
            graph.setdefault(e["src"], []).append(e["dst"])
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in NODES}
    cycles = []

    def visit(n, stack):
        color[n] = GRAY
        stack.append(n)
        for nxt in graph.get(n, []):
            if color[nxt] == GRAY:
                cycles.append(stack[stack.index(nxt):] + [nxt])
            elif color[nxt] == WHITE:
                visit(nxt, stack)
        stack.pop()
        color[n] = BLACK

    for n in NODES:
        if color[n] == WHITE:
            visit(n, [])
    return cycles


def chronology_violations(edges=None):
    """published_before edges where BOTH endpoints have a concrete comparable
    date and those dates are inverted (dst before src). Missing dates on
    either side are silently skipped -- absence of data is not a
    contradiction."""
    violations = []
    for e in (edges if edges is not None else EDGES):
        if e["type"] != "published_before":
            continue
        src_date = _node_date(NODES[e["src"]])
        dst_date = _node_date(NODES[e["dst"]])
        if src_date is None or dst_date is None:
            continue
        if src_date > dst_date:
            violations.append({"src": e["src"], "dst": e["dst"],
                                "src_date": src_date, "dst_date": dst_date})
    return violations


def restored_site_attribution_check():
    """Mechanically enforce the user's explicit instruction: the restored
    gsmg.io node must never be attribution='creator'."""
    node = NODES["page_gsmgio_restored_2026"]
    return node["attribution"] != "creator"


def report():
    errors = validate_structure()
    cycles = find_cycles()
    violations = chronology_violations()
    by_type = {}
    for node in NODES.values():
        by_type[node["type"]] = by_type.get(node["type"], 0) + 1
    return {
        "node_count": len(NODES),
        "edge_count": len(EDGES),
        "nodes_by_type": by_type,
        "structural_errors": errors,
        "cycles_found": cycles,
        "chronology_violations": violations,
        "restored_site_correctly_unattributed": restored_site_attribution_check(),
        "success_criteria": {
            "anachronistic_source_ruled_out": {
                "checked_edges": sum(1 for e in EDGES if e["type"] == "published_before"),
                "violations_found": len(violations),
                "note": "No suspected anachronistic candidate source was named going in; "
                        "this reports that zero contradictions were found among the "
                        "published_before edges that do carry concrete dates -- a checked, "
                        "bounded negative, not a claim that this rules out anachronism in "
                        "general.",
            },
            "new_adjacency_found": {
                "finding": "WITHDRAWN by Phase 345. Phase 344 originally reported "
                           "tg_hint_zeroed_out (2021-12-26) as preceding the earliest "
                           "documented public sighting of the SalPhaseIon page, treating "
                           "page_salph_v1's 2023-05-31 Wayback capture as that earliest "
                           "sighting. That conflated 'earliest ARCHIVED capture' with "
                           "'earliest public sighting': this repo's own git history "
                           "(commits 9d99692, 2021-03-20; 99bd811 and 8382341, 2021-05-07) "
                           "documents the live page -- named, screenshotted, and its exact "
                           "reachable route recorded -- about 7 months BEFORE the hint, not "
                           "17 months after it. See repo_readme_hint_2021_03 and "
                           "repo_route_hash_2021_05. No open chronology question remains "
                           "here; the apparent gap was a research gap in Phase 344's own "
                           "source coverage, not a puzzle fact.",
            },
        },
    }


def write_json(path):
    payload = {"nodes": NODES, "edges": EDGES, "report": report()}
    Path(path).write_text(json.dumps(payload, indent=2, default=repr))
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    # 1. Structural validity: every node/edge well-formed, no dangling refs.
    errors = validate_structure()
    assert not errors, errors
    assert len(NODES) >= 20
    assert len(EDGES) >= 20

    # 2. No duplicate node ids (dict keys guarantee this structurally; assert
    #    the label set is also distinct as a sanity check on the content itself).
    labels = [n["label"] for n in NODES.values()]
    assert len(set(labels)) == len(labels)

    # 3. published_before edges form a DAG (no cycles).
    cycles = find_cycles()
    assert not cycles, cycles

    # 4. Chronology consistency: the well-dated pairs in the frozen graph
    #    produce zero violations.
    violations = chronology_violations()
    assert not violations, violations

    # 5. The solved-chain positive control exists as edges and does NOT
    #    trip a false violation despite carrying no exact authorship dates
    #    (missing data must not be treated as a contradiction).
    chain_edges = [(e["src"], e["dst"]) for e in EDGES if e["type"] == "published_before"]
    assert ("solved_phase2", "solved_phase3") in chain_edges
    assert ("solved_phase3", "solved_phase3_2") in chain_edges
    assert ("solved_phase3_2", "blob_p32trailing") in chain_edges
    for src, dst in [("solved_phase2", "solved_phase3"), ("solved_phase3", "solved_phase3_2"),
                      ("solved_phase3_2", "blob_p32trailing")]:
        assert _node_date(NODES[src]) is None or _node_date(NODES[dst]) is None or \
               _node_date(NODES[src]) <= _node_date(NODES[dst])

    # 6. The restored-site attribution rule is enforced mechanically, not
    #    just by convention -- flip it and confirm the checker actually
    #    catches the violation (non-vacuousness proof).
    assert restored_site_attribution_check()
    original = NODES["page_gsmgio_restored_2026"]["attribution"]
    NODES["page_gsmgio_restored_2026"]["attribution"] = "creator"
    try:
        assert not restored_site_attribution_check()
    finally:
        NODES["page_gsmgio_restored_2026"]["attribution"] = original

    # 7. A deliberately inverted published_before edge IS caught -- proves
    #    the chronology checker isn't vacuously passing.
    poison_edges = list(EDGES) + [{"src": "page_salph_v3", "dst": "page_favicon_2019",
                                    "type": "published_before", "citation": "planted negative control"}]
    poisoned = chronology_violations(poison_edges)
    assert len(poisoned) == 1
    assert poisoned[0]["src"] == "page_salph_v3"

    # 8. No password material anywhere: no node/edge text field contains a
    #    real frozen candidate literal or a WIF-shaped string.
    import re
    from half_better_half_algebra_audit import frozen_candidates
    real_candidates = frozen_candidates()
    wif_like = re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])(?:5[1-9A-HJ-NP-Za-km-z]{50}|[KL][1-9A-HJ-NP-Za-km-z]{51})(?![1-9A-HJ-NP-Za-km-z])")
    text_blobs = []
    for node in NODES.values():
        text_blobs.extend(str(v) for v in node.values())
    for edge in EDGES:
        text_blobs.extend(str(v) for v in edge.values())
    for text in text_blobs:
        for cand in real_candidates:
            assert cand not in text, f"leaked candidate literal in {text!r}"
        assert not wif_like.search(text), f"WIF-shaped string in {text!r}"

    # 9. Phase 345 correction: the repo-git-history evidence is dated earlier
    #    than tg_hint_zeroed_out, not later, and the DAG/chronology checker
    #    accepts the corrected edge direction without violation.
    assert _node_date(NODES["repo_readme_hint_2021_03"]) == "2021-03-20"
    assert _node_date(NODES["repo_route_hash_2021_05"]) == "2021-05-07"
    assert _node_date(NODES["repo_route_hash_2021_05"]) < _node_date(NODES["tg_hint_zeroed_out"])
    corrected_edge = [(e["src"], e["dst"]) for e in EDGES if e["type"] == "published_before"]
    assert ("repo_route_hash_2021_05", "tg_hint_zeroed_out") in corrected_edge
    assert not chronology_violations([e for e in EDGES if e["type"] == "published_before"
                                       and e["src"] == "repo_route_hash_2021_05"])

    # 10. JSON round-trip.
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        write_json(tmp_path)
        reloaded = json.loads(Path(tmp_path).read_text())
        assert len(reloaded["nodes"]) == len(NODES)
        assert len(reloaded["edges"]) == len(EDGES)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    print(f"[*] self-test OK: {len(NODES)} nodes / {len(EDGES)} edges validated, "
          f"published_before edges form a DAG, zero chronology violations among "
          f"well-dated pairs, solved-chain positive control present and consistent "
          f"despite carrying no exact dates, restored-gsmg.io node mechanically "
          f"pinned to attribution='unknown' (flip-and-catch proven), a planted "
          f"inverted-date edge is correctly caught, Phase 345's repo-git-history "
          f"correction dates verified in the right order, no candidate literal or "
          f"WIF-shaped string anywhere, JSON round-trip clean")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--write-json", metavar="PATH")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if args.write_json:
        path = write_json(args.write_json)
        print(f"[*] wrote {path}")
        return

    output = report() if args.report else {"nodes": NODES, "edges": EDGES, "report": report()}
    print(json.dumps(output, indent=2, default=repr))


if __name__ == "__main__":
    main()
