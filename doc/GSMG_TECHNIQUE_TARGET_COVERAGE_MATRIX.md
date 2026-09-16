---
type: index
status: live
topics:
  - coverage-matrix
  - closed-system
---

# GSMG Technique x Target Coverage Matrix

A read-only survey of the closed-system research program, cross-tabulating
*technique class* against *target artifact/relationship* to find genuinely
untried, well-motivated combinations — as opposed to combinations that sound
plausible from memory but turn out to duplicate already-closed phases. Built
2026-09-16 from [GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) (493 formalized
phases at the time of writing, plus ~35 then-uncommitted brainstorm docs for
phases 490-512M) and the `tools/gsmg/findings/P*.md` per-phase store.

This is a planning aid, not a findings phase: it makes no new experimental
claims, runs no new code, and closes no gap. Re-run/extend it whenever the
phase count grows enough that the shortlist below might be stale, rather than
re-deriving candidate techniques from memory.

## Technique taxonomy observed in use

1. Statistical/frequency scoring (IoC, quadgram, code-IC)
2. Columnar/keyed transposition — both the small fixed-route family
   (spiral/boustrophedon/row/col) and the newer unrestricted-order
   CSP/annealing solver (Phase 477-504, 512-515)
3. Checkerboard escape-pair monoalphabetic substitution recovery
4. Bifid/Trifid/polybius-family keying
5. Classical running-key ciphers (Nihilist, Bellaso, Gronsfeld, ADFGVX,
   Vigenere)
6. Exact-crib / CSP constraint search (new in Phase 512)
7. Numeric/arithmetic combination (sums, products, Roman numerals, modular
   arithmetic)
8. Structural/route/graph/geometric reading (grid traversal, spiral,
   canonicalization)
9. Brute-force wordlist/password search (Pwdb, curated corpora, GPU oracle)
10. Provenance/creator-clue corpus sweep (Telegram, media, web, external
    forks)
11. False-discovery / null-calibration methodology (Phase 453 family)
12. GPU/compute-scale search (Bifid 16!, AES/KDF oracle)
13. secp256k1/Bitcoin-address consumption checks

## Target taxonomy

`DBBI` (raw stream alone), `FAED` (raw stream alone), the `DBBI<->FAED`
relationship, `matrixsumlist` consumption (the 31-character DBBI selection),
`thispassword`/`lastwordsbeforearchichoice` consumption, the Architect mirror
operation, the rotated-prime pair / `THEFLOWER`, `FEFE`/`{1,4,21}`/`ggn`/
secp256k1 scalar, prime sums `401`/`400`/`73`, matrix product `FF67`, `KIT`,
`X2SH4Y0QB15`/Decentraland route, the `SALPH`/`COSMIC`/`P32TRAILING` blobs,
the *Cosmic Duality* book text, and the Telegram/creator corpus itself —
these track the [GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md)'s nine
named gaps plus the raw streams they gate.

## Headline finding: near-total saturation, with one clear asymmetry

Every `(technique, target)` cell involving classical/keyed ciphers, numeric
combination, structural/route reading, and provenance sweeps is covered —
often 5-15x over — for both `DBBI` and `FAED` individually, and for the
`DBBI<->FAED` relationship (Phases 271-321 alone ran ~50 cross-stream
coupling models: transition matrices, mirror9 substitution, positional
co-occurrence, GF(9)/base-27/base-81, an FSM model, sequence alignment,
Bacon, Nihilist, Bellaso, ADFGVX, Gronsfeld/progressive shifts — see
[GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md)).
The community `BTCSEED` Bifid line (`DBBI[:13]` keys a square decrypting
`FAED`) got both a full pre-registered family-wide significance test (Phase
425, `p=0.0001`, positive-checkpoint-only) and a full `16!` alphabet-
completion GPU search (Phase 429-441), both closed — the latter also
surfacing a general methodological finding (Phase 433) that quadgram-score
chasing over a large enough relabeling space produces spurious high scorers
independent of real plaintext.

Two genuinely untried, well-motivated cells survived scrutiny (most
candidates considered and rejected, e.g. "Roman numeral projection x
secp256k1 scalar," are non-sequitur pairings, not real gaps — see the
"Adding a gap" discipline in
[GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md)):

1. **The unrestricted-order transposition/CSP solver line has only ever been
   pointed at `FAED`.** Grep-confirmed zero mentions of `DBBI` in
   `tools/gsmg/findings/P00477.md`, `P00484.md`,
   [GSMG_PHASE477A_TOKEN_COLUMNAR_TRANSPOSITION_AUDIT](GSMG_PHASE477A_TOKEN_COLUMNAR_TRANSPOSITION_AUDIT.md),
   or
   [GSMG_PHASE484B_POWERED_SMALL_WIDTH_RAW_SYMBOL_VIC_AUDIT](GSMG_PHASE484B_POWERED_SMALL_WIDTH_RAW_SYMBOL_VIC_AUDIT.md).
   `DBBI`'s own transposition-shaped work stopped at Phase 319 (fixed
   spiral/boustrophedon/row/col routes over `DBBI`'s established 7x13
   factorization, closed negative, shuffle-gate clean) — a much smaller
   hypothesis space than the genuinely unknown-order CSP/annealing search
   `FAED` received starting Phase 477. `DBBI`'s independently-best escape
   pair (`{b,e}`, established by the same code-IC methodology that selected
   `FAED`'s `{g,i}` — see `G-YIN-001`'s registry text) has never been run
   through the unrestricted solver. Motivated because `DBBI` and `FAED` are
   the same cipher construction on the same page: if pre-decode transposition
   is real for this scheme at all, it should be checked on both streams, not
   only one. Would bear on `G-ESC-001` from the `DBBI` side.
2. **`DBBI`'s own established 31-character `matrixsumlist` selection has
   never been used as an exact crib against `FAED`**, transposition-aware or
   not. `crib_drag.py`'s `CRIB_CANDIDATES_DBBI`/`CRIB_CANDIDATES_FAED` lists
   are all guessed English phrases (e.g. `"yellowblueprimematrixsumlist"`),
   never `DBBI`'s actual selected output string; Phase 512A's three frozen
   exact-crib targets (the 3.2.2 validation answer, the Phase-1 credential,
   the creator macro message) are all borrowed from unrelated puzzle stages,
   not `DBBI` itself. This is a materially better-motivated test than those
   three, because it is licensed directly by `G-YIN-001`'s own open
   question — does `FAED` reference `DBBI`'s output — rather than by "which
   string are we most certain is authentic."

Both reuse tooling that already exists and is already validated
(`crib_drag.py`, the Phase 512 CSP architecture, the unrestricted-board
solver); neither requires new machinery, only pointing existing machinery at
`DBBI` instead of exclusively at `FAED`.

## Scope and limits

This survey classifies phases by their one-line disposition in
`GSMG_PHASE_INDEX.md` and the corresponding `findings/P*.md` entry; it does
not re-read the full `tools/gsmg/FINDINGS.md` prose for every phase, so a
technique/target pairing that was tested only as an unrecorded aside inside a
differently-titled phase could in principle be missed. Treat the two flagged
cells as the current best candidates, not a formal proof that nothing else is
open — and re-derive this matrix rather than trust it verbatim once enough
new phases (particularly any that touch `DBBI` directly) have landed.
