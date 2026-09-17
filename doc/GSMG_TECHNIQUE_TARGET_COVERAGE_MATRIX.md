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

## Headline finding: near-total saturation; both flagged asymmetries now resolved

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

Two genuinely untried, well-motivated cells survived scrutiny at the time
this survey was written (most candidates considered and rejected, e.g.
"Roman numeral projection x secp256k1 scalar," are non-sequitur pairings,
not real gaps — see the "Adding a gap" discipline in
[GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md)). Both have since been
resolved — one executed and closed negative, one discarded on deeper
tracing before any real run:

1. **CLOSED (Phase 516, 2026-09-17).** The unrestricted-order
   transposition/CSP solver line had only ever been pointed at `FAED`;
   `DBBI`'s own transposition work stopped at Phase 319's small fixed-route
   family. [GSMG_PHASE516_DBBI_WIDTH7_UNRESTRICTED_AUDIT](GSMG_PHASE516_DBBI_WIDTH7_UNRESTRICTED_AUDIT.md)
   ran a genuinely exhaustive order search (all `7! = 5,040` orders — the
   only order-tractable width, since `91 = 7 x 13` — across all 36 escape
   pairs) with a calibrated null comparison: the real winner scored below
   all 3 shuffled-`DBBI` null trials. Closed negative. Width 13
   (`13! ~= 6.2e9` orders) remains open, gated on a different search
   architecture, not this survey's flagged asymmetry.
2. **DISCARDED before execution.** `DBBI`'s own established 31-character
   `matrixsumlist` selection (`ncsyangcahiriasogaleafayanestve`) was
   initially proposed as a better-motivated exact-crib target than Phase
   512's three borrowed strings, on the theory that it is licensed by
   `G-YIN-001`'s own question (does `FAED` reference `DBBI`'s output).
   Tracing its actual provenance (`denis_prime_extraction_audit.py`,
   `flo_prime_walk_provenance_audit.py`) found this doesn't hold: the string
   is not a substring of `DBBI` at all — it's extracted from `SOURCE`, a
   *different*, already-solved 91-character earlier-stage plaintext, using
   an index-selection pattern derived from `DBBI` that the project's own
   44-rule sweep never reproduced and whose own reconstruction is explicitly
   caveated as "not... a discovery p-value." That makes it closer in kind to
   the three already-rejected borrowed-string cribs than to a genuine
   `DBBI`-content test. No script was run against real `FAED` for this cell.

## Scope and limits

This survey classifies phases by their one-line disposition in
`GSMG_PHASE_INDEX.md` and the corresponding `findings/P*.md` entry; it does
not re-read the full `tools/gsmg/FINDINGS.md` prose for every phase, so a
technique/target pairing that was tested only as an unrecorded aside inside a
differently-titled phase could in principle be missed. Treat the two flagged
cells as the best candidates found at the time, not a formal proof that
nothing else is open — and re-derive this matrix rather than trust it
verbatim once enough new phases have landed. The clearest remaining
frontier this survey identified, `DBBI` at width 13 under a genuinely
different (non-brute-enumeration) order-search architecture, is not itself
a new empty cell so much as an engineering prerequisite Phase 516 left
explicitly open.
