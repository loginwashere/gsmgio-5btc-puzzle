---
type: index
status: live
generated_from: tools/gsmg/FINDINGS.md
generator: tools/gsmg/phase_citation_graph.py
---

# GSMG Phase Citation Graph

Ranks FINDINGS.md phases by **in-degree**: the number of *other*
phases whose body text cites them (`Phase N` / `Phases N, M`). This
is a heuristic text-mining pass over inline cross-references, not a
semantic dependency analysis -- an edge means "phase A's text
mentions phase B", not necessarily "phase A's result requires
phase B's result". Use it to sequence review work (start from the
most heavily cited phases and work outward to leaves), not as a
citation-accuracy claim.

Regenerate with `python3 tools/gsmg/phase_citation_graph.py` after
adding phases. Raw graph data: [phase_citation_graph.json](../tools/gsmg/phase_citation_graph.json).

## Hub phases (highest in-degree first)

| Rank | Phase | Stable ID | Subject | In-degree | Out-degree | Cited by |
|---|---|---|---|---|---|---|
| 1 | 296 | P296 | QR finder-ring texture | 10 | 0 | P293, P298, P300, P301, P302, P304, P305, P354, P359, P365 |
| 2 | 96 | P096 | case-sensitive `SalPhaseIon -> SalVATIon -> SALVATION` rebus audit | 9 | 0 | P103, P107, P159, P169, P217, P218, P007, P097, P098 |
| 3 | 7 | P007 | full read-through of all 411 creator messages | 7 | 2 | P010, P110, P136, P259, P295, P008-B, P008-A |
| 4 | 48 | P048 | Flo prime-walk provenance recovers Denis's mask and resolves the FEFE boundary | 7 | 1 | P131, P157, P047, P049, P050, P051, P064 |
| 5 | 97 | P097 | elemental `SALPHATION -> SALVATION` reproduces `[23,16,7]` exactly | 7 | 2 | P105, P107, P108, P149, P179, P185, P098 |
| 6 | 98 | P098 | creator-corpus base-rate audit downgrades the atomic-number match | 7 | 2 | P102, P105, P107, P108, P127, P149, P099 |
| 7 | 127 | P127 | cell-classifier fix | 7 | 4 | P124, P125, P126, P128, P063, P064, P065 |
| 8 | 336 | P336 | B1 "half and better half" combine algebra, bounded pilot | 7 | 2 | P337, P338, P339, P340, P342, P348, P350 |
| 9 | 33 | P033 | Architect-choice extraction | 6 | 0 | P103, P166, P181, P185, P218, P330 |
| 10 | 34 | P034 | `BUT/HYE` yin-yang rail audit | 6 | 0 | P103, P104, P160, P166, P185, P043 |
| 11 | 36 | P036 | barrystyle provenance and 196-cell yellow-mask prime | 6 | 0 | P119, P120, P240, P035, P060, P069 |
| 12 | 112 | P112 | review correction | 6 | 1 | P105, P106, P113, P145, P146, P166 |
| 13 | 331 | P331 | GPU oracle | 6 | 5 | P332, P334, P336, P337, P340, P342 |
| 14 | 2 | P002 | dictionary-scale sweep | 5 | 0 | P003, P344, P351, P006, P008-A |
| 15 | 51 | P051 | `matrixsumlist` consumer feasibility audit | 5 | 2 | P150, P153, P160, P178, P058 |
| 16 | 64 | P064 | a 2020 diagram independently corroborates FEFE and names the "nest" cells | 5 | 4 | P127, P330, P065, P066, P067 |
| 17 | 84 | P084 | `-nopad` window sweep built and validated; not yet launched | 5 | 0 | P259, P085, P086, P087, P091 |
| 18 | 85 | P085 | `-nopad` sweep | 5 | 1 | P259, P086, P087, P090, P091 |
| 19 | 148 | P148 | `SalPhaseIon -> APHELION` sub-anagram | 5 | 0 | P149, P151, P155, P159, P168 |
| 20 | 300 | P300 | QR finder-ring texture | 5 | 3 | P301, P302, P303, P304, P305 |
| 21 | 301 | P301 | QR finder-ring texture | 5 | 3 | P302, P303, P304, P305, P306 |
| 22 | 302 | P302 | QR finder-ring texture | 5 | 6 | P303, P304, P305, P306, P354 |
| 23 | 322 | P322 | GPU AES/KDF oracle built and validated; creator-authored macro-clue fragment combinations swept | 5 | 0 | P326, P328, P331, P334, P346 |
| 24 | 328 | P328 | GPU oracle | 5 | 3 | P163, P331, P332, P333, P337 |
| 25 | 356 | P356 | QR `#FAFAFA` texture is locked to one native 7x7-pixel module | 5 | 2 | P357, P358, P359, P360, P365 |
| 26 | 5 | P005 | independent image forensic audit | 4 | 0 | P161, P162, P297, P008-A |
| 27 | 21 | P021 | Digraphic cipher over the 25-code alphabet | 4 | 1 | P152, P157, P159, P024 |
| 28 | 44 | P044 | corrected “in front of your eyes” transition audit | 4 | 0 | P157, P250, P259, P045 |
| 29 | 46 | P046 | exact uniform-subset base-rate audit of Denis Golovkin's "yang" extraction | 4 | 0 | P131, P157, P159, P047 |
| 30 | 53 | P053 | recovered Telegram yellow-blue-primes guide and corrected FEFE audit | 4 | 0 | P139, P140, P171, P059 |
| 31 | 78 | P078 | Binary-key-material CBC/ECB oracle gap fixed and backfilled negative | 4 | 0 | P151, P080, P081, P082 |
| 32 | 86 | P086 | `-nopad` sweep | 4 | 2 | P259, P087, P090, P091 |
| 33 | 87 | P087 | `-nopad` sweep | 4 | 3 | P259, P090, P091, P092 |
| 34 | 88 | P088 | Jacque Fresco's broader body of work | 4 | 0 | P159, P259, P089, P090 |
| 35 | 99 | P099 | scheme sensitivity and the degenerate creator-word control | 4 | 1 | P102, P105, P107, P108 |
| 36 | 102 | P102 | `anstoo`/SHA-operand provenance audit | 4 | 2 | P108, P134, P158, P283 |
| 37 | 164 | P164 | brainstorm item 2 | 4 | 1 | P165, P166, P167, P170 |
| 38 | 253 | P253 | bounded Blowfish/Camellia/SEED OpenSSL-container recheck | 4 | 0 | P255, P256, P257, P326 |
| 39 | 259 | P259 | physical Cosmic Duality book pages 57-58 recovered | 4 | 11 | P261, P262, P343, P344 |
| 40 | 267 | P267 | Full Phase 2/3/3.2 decrypted-text sentence sweep against all four blobs | 4 | 0 | P269, P307, P308, P314 |
| 41 | 298 | P298 | QR finder-ring texture | 4 | 1 | P299, P300, P302, P305 |
| 42 | 305 | P305 | QR finder-ring texture | 4 | 9 | P306, P354, P360, P361 |
| 43 | 323 | P323 | GPU oracle backfill | 4 | 2 | P163, P327, P328, P331 |
| 44 | 327 | P327 | key-shape classifier (hex64/WIF/BIP39) swept against the core candidate corpus | 4 | 2 | P333, P336, P338, P346 |
| 45 | 4 | P004 | the "another door" / prime / neo's-passport hints | 3 | 1 | P117, P297, P008-A |
| 46 | 22 | P022 | Broadened cipher/KDF oracle + staged SALPH->COSMIC pipeline | 3 | 0 | P151, P023, P026 |
| 47 | 37 | P037 | `{1},{4},{21}` and the FEFE prime zero | 3 | 0 | P117, P157, P047 |
| 48 | 40 | P040 | independent tail-selector audit | 3 | 0 | P157, P064, P066 |
| 49 | 43 | P043 | FAED ciphertext-only monoalphabetic recovery under (h,e), corrected | 3 | 3 | P113, P157, P166 |
| 50 | 47 | P047 | first-piece color sequence / Denis-mask convergence audit | 3 | 4 | P157, P159, P048 |
| 51 | 66 | P066 | creator clue index expanded to 80 records; one real provenance upgrade | 3 | 3 | P256, P068, P079 |
| 52 | 83 | P083 | Tier-1 binary-material expansion complete, clean negative | 3 | 1 | P259, P323, P090 |
| 53 | 90 | P090 | Fresco wordlist | 3 | 6 | P144, P259, P323 |
| 54 | 94 | P094 | `-nopad` Tier-1 sweep | 3 | 1 | P163, P165, P095 |
| 55 | 106 | P106 | a calibrated partial oracle for the checkerboard escape pair | 3 | 3 | P112, P145, P146 |
| 56 | 125 | P125 | black-rabbit negative-space audit | 3 | 1 | P126, P127, P128 |
| 57 | 132 | P132 | family-wise selected-text calibration | 3 | 1 | P131, P178, P236 |
| 58 | 137 | P137 | complete public support-group export and original rabbit JPEG recovered | 3 | 0 | P135, P136, P138 |
| 59 | 151 | P151 | Trinity resurrection-speech "half and better half" reading | 3 | 3 | P152, P153, P155 |
| 60 | 155 | P155 | second Telegram corpus discovered ("Community & support group"), rechecked, new first-party context, bounded oracle test negative | 3 | 4 | P156, P158, P163 |
| 61 | 163 | P163 | creator's own recommended hash-checking tool identified and its exact whitespace behavior tested against the curated corpus | 3 | 5 | P164, P165, P167 |
| 62 | 189 | P189 | exploratory G-shadow-count consumer | 3 | 0 | P190, P191, P209 |
| 63 | 218 | P218 | post-yinyang dataflow ranking | 3 | 4 | P219, P220, P223 |
| 64 | 260 | P260 | Cosmic Duality title page's C/D initials | 3 | 1 | P261, P262, P263 |
| 65 | 261 | P261 | Phase 260 correction | 3 | 2 | P259, P262, P263 |
| 66 | 265 | P265 | Phase 3.2 monologue's own residual vocabulary against all four blobs | 3 | 1 | P268, P308, P314 |
| 67 | 274 | P274 | Exact six-lane FAED/DBBI geometry and 24-symbol endpoint tail | 3 | 0 | P285, P290, P291 |
| 68 | 276 | P276 | GF(9) linear complexity, recurrence transfer, and seven-row rank | 3 | 0 | P290, P291, P293 |
| 69 | 297 | P297 | Joint DBBI x FAED positional co-occurrence matrix | 3 | 3 | P301, P302, P305 |
| 70 | 299 | P299 | QR Code Monkey full eye-style catalog sweep | 3 | 1 | P300, P302, P305 |
| 71 | 310 | P310 | Nihilist-cipher additive-key hypothesis on DBBI/FAED | 3 | 1 | P311, P320, P321 |
| 72 | 337 | P337 | A1+A2 sliding raw-key windows and byte-order transforms, bounded pilot | 3 | 3 | P338, P339, P342 |
| 73 | 343 | P343 | Seed 4 (ledger half only) | 3 | 2 | P344, P346, P347 |
| 74 | 354 | P354 | QR `#FAFAFA` mask is predicted by one global 7x7 tile | 3 | 3 | P355, P356, P360 |
| 75 | 3 | P003 | resolving the alphabet-derivation gap | 2 | 1 | P004, P008-A |
| 76 | 8 | P008-A | chasing the alphabet directly | 2 | 6 | P106, P286 |
| 77 | 8 | P008-B | Architect/Gnostic synonym sweep | 2 | 1 | P106, P286 |
| 78 | 13 | P013 | cross-phase prime/color linkage (2026-07-23) — DEBUNKED, see correction | 2 | 0 | P051, P069 |
| 79 | 16 | P016 | code review of all 25 tools/gsmg/*.py scripts | 2 | 1 | P017, P018 |
| 80 | 20 | P020 | Checkerboard recovery calibration harness | 2 | 0 | P021, P024 |
| 81 | 25 | P025 | Provenance triage of the untracked base64 fragment | 2 | 0 | P257, P026 |
| 82 | 28 | P028 | Puzzle-address split and blockchain metadata candidates | 2 | 0 | P042, P094 |
| 83 | 31 | P031 | Exact first-piece yellow/blue reconstruction | 2 | 0 | P166, P064 |
| 84 | 32 | P032 | `574061 -> matrixsumlist` checkpoint | 2 | 0 | P185, P097 |
| 85 | 41 | P041 | bounded FEFE zero-operation audit | 2 | 0 | P157, P047 |
| 86 | 54 | P054 | Denis Golovkin's own narrated chain, in the complete Telegram export | 2 | 0 | P182, P059 |
| 87 | 56 | P056 | “matrix sum list” passage provenance | 2 | 0 | P181, P059 |
| 88 | 69 | P069 | calibrating the `-41+-17=-58` coincidence | 2 | 2 | P161, P072 |
| 89 | 71 | P071 | Stage-1 icon overlap + visible-rebus correction | 2 | 0 | P258, P072 |
| 90 | 73 | P073 | Stage-0 PNG filter-byte anomaly (message `49536`) fully reproduced, calibrated negative | 2 | 0 | P353, P363 |
| 91 | 74 | P074 | External archive audit | 2 | 0 | P147, P075 |
| 92 | 79 | P079 | creator macro-clue fragments added to the corpus; CFB/OFB/CTR cipher-mode gap closed | 2 | 1 | P166, P256 |
| 93 | 89 | P089 | Fresco wordlist | 2 | 1 | P259, P090 |
| 94 | 91 | P091 | `-nopad` sweep | 2 | 4 | P092, P095 |
| 95 | 92 | P092 | `-nopad` sweep | 2 | 2 | P093, P095 |
| 96 | 95 | P095 | `-nopad` sweep | 2 | 3 | P163, P093 |
| 97 | 101 | P101 | typed page grammar remains underdetermined; `anstoo` correction | 2 | 0 | P134, P238 |
| 98 | 126 | P126 | user-drawn lower rabbit | 2 | 2 | P127, P128 |
| 99 | 136 | P136 | pre-rabbit “first GSMG puzzle” recovered and decoded | 2 | 2 | P138, P007 |
| 100 | 139 | P139 | literal yellow/blue prime-list sums | 2 | 1 | P174, P181 |
| 101 | 144 | P144 | `-nopad` Tier-2 binary-key-material sweep | 2 | 2 | P146, P219 |
| 102 | 150 | P150 | `matrixsumlist` self/fold consumer pairings + literal-index probe | 2 | 1 | P160, P185 |
| 103 | 153 | P153 | audit for missed sub-tasks in items 1 and 2, three residual checks closed | 2 | 2 | P160, P329 |
| 104 | 154 | P154 | creator idiolect/OSINT pass | 2 | 0 | P155, P308 |
| 105 | 156 | P156 | on-chain/DNS forensics sweep (item 4) | 2 | 1 | P210, P329 |
| 106 | 161 | P161 | item 3 | 2 | 3 | P162, P352 |
| 107 | 162 | P162 | did Phase 161 fetch fresh from Wayback? No -- real gap for 4 files, moot for the other 3, found 7 genuinely new never-checked assets | 2 | 2 | P239, P352 |
| 108 | 169 | P169 | `SalPhaseIon + T -> SaltPhaseIon` | 2 | 2 | P170, P222 |
| 109 | 179 | P179 | remaining structural avenues | 2 | 1 | P184, P265 |
| 110 | 182 | P182 | trilogy-wide major Neo-choice boundary phrases | 2 | 1 | P183, P184 |
| 111 | 186 | P186 | Stage-0 footer `#383838` layer | 2 | 1 | P188, P209 |
| 112 | 187 | P187 | repeated-byte grayscale claim (`CECECE -> CE`, `FEFEFE -> FE`) | 2 | 0 | P209, P239 |
| 113 | 188 | P188 | annotator's "G in the shadows and the text" clarification | 2 | 1 | P195, P209 |
| 114 | 190 | P190 | G-consumer comparison without annotator confirmation | 2 | 1 | P205, P209 |
| 115 | 191 | P191 | bounded Stage-0 convergence | 2 | 2 | P204, P209 |
| 116 | 192 | P192 | URLBLOB promoted into the default target registry; post-quarantine coverage inventory and bounded rerun | 2 | 1 | P191, P193 |
| 117 | 195 | P195 | first-piece Hamming/control-language audit | 2 | 1 | P196, P251 |
| 118 | 202 | P202 | FEFE PNG palette/alpha provenance | 2 | 0 | P363, P364 |
| 119 | 216 | P216 | `BUT/HYE` survives a film-vs-screenplay stress test; literal seven-word boundary phrase is oracle-negative | 2 | 1 | P217, P218 |
| 120 | 217 | P217 | minimal creator-macro chain reaches `yinyang` via the six-digit prime; VAT/SALVATION and an invented "H|YE|BUT" reading removed after review | 2 | 3 | P218, P221 |
| 121 | 223 | P223 | BUT/HYE survives, but its partial mirror does not mechanically establish `yinyang` | 2 | 1 | P216, P217 |
| 122 | 226 | P226 | exact creator feasibility envelope | 2 | 1 | P230, P235 |
| 123 | 230 | P230 | corrected two-chat feasibility and presentation-vocabulary envelope | 2 | 1 | P226, P235 |
| 124 | 236 | P236 | macro-model comparison reclassifies the selected 31 as a structural checkpoint | 2 | 1 | P238, P308 |
| 125 | 239 | P239 | native favicon shadow audit | 2 | 2 | P241, P242 |
| 126 | 254 | P254 | curated-candidate corpus provenance audit | 2 | 0 | P255, P256 |
| 127 | 255 | P255 | excluded-wordlist coverage matrix | 2 | 2 | P256, P326 |
| 128 | 266 | P266 | Phase 3's seven-part construction reused as a P32 password candidate | 2 | 0 | P268, P317 |
| 129 | 268 | P268 | X2SH4Y0QB15's own text (literal, substituted, coordinate, and three reversal scopes) against all four blobs | 2 | 2 | P269, P351 |
| 130 | 271 | P271 | external fork re-audit (family 6, blob-literal/code-context archaeology) | 2 | 1 | P291, P292 |
| 131 | 273 | P273 | DBBI/FAED through the page's exact decimal transport inverse | 2 | 0 | P290, P291 |
| 132 | 275 | P275 | Canonical 9x9 DBBI/FAED transition matrices | 2 | 0 | P290, P291 |
| 133 | 277 | P277 | Three-trit base-27 decoding | 2 | 0 | P290, P291 |
| 134 | 278 | P278 | Move-to-front structural gate | 2 | 0 | P290, P291 |
| 135 | 279 | P279 | Natural base-81 digraph tokens | 2 | 0 | P290, P291 |
| 136 | 280 | P280 | Factoradic/Lehmer records at n=6 and n=9 | 2 | 0 | P290, P291 |
| 137 | 281 | P281 | Crib-solved low-order recurrences | 2 | 0 | P290, P291 |
| 138 | 282 | P282 | DBBI probability model / FAED arithmetic code | 2 | 0 | P290, P291 |
| 139 | 283 | P283 | `anstoo` / asymmetric-numeral-system feasibility | 2 | 1 | P290, P291 |
| 140 | 284 | P284 | Canonical DBBI `81+10` finite-state machine | 2 | 0 | P290, P291 |
| 141 | 285 | P285 | Indel-tolerant DBBI/FAED sequence alignment | 2 | 1 | P290, P291 |
| 142 | 286 | P286 | DBBI/FAED canonical tone renders | 2 | 2 | P290, P291 |
| 143 | 287 | P287 | DBBI/FAED matrix-barcode rendering | 2 | 0 | P290, P291 |
| 144 | 288 | P288 | DBBI/FAED continued fractions | 2 | 0 | P290, P291 |
| 145 | 289 | P289 | DBBI/FAED as authenticated-string selectors | 2 | 0 | P290, P291 |
| 146 | 303 | P303 | QR finder-ring texture | 2 | 3 | P304, P305 |
| 147 | 311 | P311 | Cosmic Duality book text as a running key over DBBI/FAED | 2 | 1 | P320, P321 |
| 148 | 325 | P325 | genesis-block adjacent unused fields (timestamp/nBits/height/nonce) as password material | 2 | 1 | P328, P332 |
| 149 | 326 | P326 | SEED-CBC ported to the GPU oracle; closes the medium-curated 66,433-candidate SEED gap | 2 | 3 | P327, P331 |
| 150 | 329 | P329 | live `gsmg.io` restoration and ownership-provenance audit | 2 | 2 | P344, P347 |
| 151 | 330 | P330 | Hosterjack interactive compendium delta audit | 2 | 3 | P331, P347 |
| 152 | 333 | P333 | Phase-328's 43 weak hits swept through the key-shape classifier | 2 | 3 | P332, P338 |
| 153 | 338 | P338 | A3 unconditional embedded key-format scanner, bounded pilot | 2 | 4 | P339, P342 |
| 154 | 340 | P340 | C1 BIP32 paths from authenticated numbers, tightly bounded pilot | 2 | 2 | P343, P346 |
| 155 | 342 | P342 | Seed 2 | 2 | 4 | P348, P350 |
| 156 | 347 | P347 | Seed-6-first tradeoff resolved | 2 | 4 | P348, P349 |
| 157 | 355 | P355 | exhaustive Braille readings of QR `#FAFAFA` mask and Phase-354 residual | 2 | 1 | P356, P360 |
| 158 | 360 | P360 | six-variant QR `#FAFAFA` atlas | 2 | 4 | P361, P362 |
| 159 | 6 | P006 | checking for genuine post-fork progress | 1 | 1 | P008-A |
| 160 | 14 | P014 | AES oracle false-negative fix | 1 | 0 | P015 |
| 161 | 15 | P015 | Cosmic Duality book | 1 | 1 | P016 |
| 162 | 18 | P018 | fixed the faed escape-pair coverage gap; recorded autokey tier-2's exact old/new boundary, NOT yet resumed | 1 | 1 | P219 |
| 163 | 19 | P019-A | model-changing paths after coverage saturation | 1 | 0 | P043 |
| 164 | 19 | P019-B | `matrixsumlist` self-derived permutation | 1 | 0 | P043 |
| 165 | 27 | P027 | `urlblob` provenance verification, quarantine, and sweep | 1 | 0 | P192 |
| 166 | 38 | P038 | bounded convergence of the prime-matrix and FEFE threads | 1 | 0 | P157 |
| 167 | 39 | P039 | matrix-row self-addressing grammar | 1 | 0 | P157 |
| 168 | 42 | P042 | bounded plated-seed referent audit | 1 | 1 | P157 |
| 169 | 45 | P045 | native prime/character-zeroing sweep, corrected | 1 | 1 | P157 |
| 170 | 49 | P049 | bounded consumption audit of the exact 31-position mask | 1 | 2 | P050 |
| 171 | 50 | P050 | residual prime-walk events cross the real DBBI/matrixsumlist page boundary | 1 | 2 | P049 |
| 172 | 52 | P052 | transition-evidence recovery | 1 | 0 | P055 |
| 173 | 55 | P055 | recovered-guide Telegram neighborhood audit | 1 | 1 | P059 |
| 174 | 60 | P060 | Phase 36's missing barrystyle media recovered | 1 | 1 | P119 |
| 175 | 61 | P061 | Telegram `[23,16,7]` operation audit | 1 | 0 | P171 |
| 176 | 63 | P063 | consolidated creator clue, confirmation, and praise index | 1 | 1 | P066 |
| 177 | 65 | P065 | rabbit-nest leftover nibble | 1 | 2 | P067 |
| 178 | 68 | P068 | reaction-signal and success-claim sweeps of the complete export | 1 | 1 | P161 |
| 179 | 75 | P075 | `YOUWON` partition audit | 1 | 1 | P147 |
| 180 | 77 | P077 | Legacy-CBC backfill for P32TRAILING and URLBLOB | 1 | 0 | P257 |
| 181 | 81 | P081 | provenance-tiered medium candidate corpus built, not launched | 1 | 1 | P083 |
| 182 | 100 | P100 | Tier-1 `-nopad` queue verified; zero funded or known addresses | 1 | 0 | P144 |
| 183 | 113 | P113 | calibrated FAED monoalphabetic recovery under `{g,i}` | 1 | 2 | P123 |
| 184 | 115 | P115 | creator handle `SoWut` | 1 | 0 | P245 |
| 185 | 118 | P118 | recovered Matrix-text difference instruction | 1 | 0 | P307 |
| 186 | 119 | P119 | full enumeration of barrystyle's media attachments | 1 | 2 | P120 |
| 187 | 123 | P123 | FAED `{g,i}` VIC-style chain-addition reopening | 1 | 1 | P124 |
| 188 | 124 | P124 | bounded yin-yang artifact inventory | 1 | 2 | P166 |
| 189 | 128 | P128 | rabbit-nest binary maze | 1 | 3 | P129 |
| 190 | 131 | P131 | selected-text thematic cluster | 1 | 3 | P132 |
| 191 | 140 | P140 | recovered-guide row/column family | 1 | 1 | P141 |
| 192 | 143 | P143 | Cosmic Duality last-column base64 decode | 1 | 0 | P194 |
| 193 | 145 | P145 | non-standard N-escape checkerboard topology (N=3, N=4) | 1 | 2 | P146 |
| 194 | 146 | P146 | short-period Bifid/Trifid-style block fractionation | 1 | 4 | P219 |
| 195 | 152 | P152 | Trinity resurrection reading, remaining two roles (KDF context, checkerboard seed) | 1 | 2 | P155 |
| 196 | 157 | P157 | repo-wide palette-anomaly sweep (item 8) | 1 | 13 | P186 |
| 197 | 158 | P158 | `promised` provenance | 1 | 2 | P165 |
| 198 | 159 | P159 | has `SALVATION` itself ever been anagrammed? Real gap, found and closed negative by base rate | 1 | 6 | P168 |
| 199 | 165 | P165 | brainstorm item 3 | 1 | 4 | P166 |
| 200 | 170 | P170 | Phase 3.2 calibration gate + literal SALT/PHRASE/ION XOR audit | 1 | 2 | P176 |
| 201 | 171 | P171 | COSMIC's exact 83/84 guide alignment and 6/84/6 salted-envelope geometry | 1 | 2 | P172 |
| 202 | 174 | P174 | OpenSSL salt bytes as bounded selectors/permutations | 1 | 1 | P181 |
| 203 | 178 | P178 | synthesis action paths | 1 | 2 | P184 |
| 204 | 181 | P181 | movie-transcript-vs-shooting-script check on the `[23,16,7]` source text | 1 | 4 | P183 |
| 205 | 183 | P183 | movie-transcript-vs-shooting-script check, part 2 | 1 | 3 | P184 |
| 206 | 184 | P184 | Smith/Neo "equation" scene | 1 | 4 | P183 |
| 207 | 196 | P196 | independent `400/401/73` reconstruction and selector-free FE composition | 1 | 1 | P260 |
| 208 | 214 | P214 | chronological `matrixsumlist` code audit | 1 | 0 | P308 |
| 209 | 215 | P215 | creator/operator vocabulary inventory | 1 | 0 | P330 |
| 210 | 220 | P220 | authenticated presentation layer contains no DBBI/FAED binding | 1 | 1 | P229 |
| 211 | 222 | P222 | macro tail does not uniquely supply `T`; SaltPhaseIon retained as bounded recognition | 1 | 1 | P169 |
| 212 | 227 | P227 | visible-referent delta | 1 | 0 | P228 |
| 213 | 232 | P232 | full endings rail partially mirrors from HYE to BYE | 1 | 0 | P233 |
| 214 | 233 | P233 | BYE has an independently prior semantic bridge to CIAO BELLA O | 1 | 1 | P234 |
| 215 | 235 | P235 | Architect-passage residual audit | 1 | 2 | P307 |
| 216 | 243 | P243 | DBBI/FAED boundary page-selector audit | 1 | 0 | P244 |
| 217 | 244 | P244 | DBBI/FAED cross-capture stability | 1 | 1 | P344 |
| 218 | 245 | P245 | creator personal-disclosures audit | 1 | 1 | P248 |
| 219 | 247 | P247 | Architect beginnings/endings/B<->H mirror selector audit | 1 | 0 | P248 |
| 220 | 249 | P249 | SalPhaseIon urlscan history audit | 1 | 0 | P344 |
| 221 | 256 | P256 | candidate-level V2 registry | 1 | 6 | P257 |
| 222 | 257 | P257 | V2 residual oracle backfill | 1 | 4 | P256 |
| 223 | 269 | P269 | Phase 268 corrective closure | 1 | 2 | P351 |
| 224 | 270 | P270 | P32 trailing blob as the Phase 3.2 sibling-output payload | 1 | 0 | P271 |
| 225 | 290 | P290 | P1A | 1 | 17 | P335 |
| 226 | 292 | P292 | Candidate family 10 executed | 1 | 1 | P325 |
| 227 | 293 | P293 | `mirror9` direct substitution on full DBBI/FAED | 1 | 2 | P297 |
| 228 | 295 | P295 | Full Phase 3.2.1 plaintext reversal | 1 | 1 | P307 |
| 229 | 304 | P304 | QR finder-ring texture | 1 | 5 | P305 |
| 230 | 307 | P307 | Architect monologue, forward, as one unbroken block against all four blobs | 1 | 4 | P314 |
| 231 | 308 | P308 | Architect monologue "wiseman"/"140" identity research and token-level oracle closure | 1 | 5 | P314 |
| 232 | 321 | P321 | ADFGVX-style keyed columnar transposition on DBBI/FAED | 1 | 2 | P310 |
| 233 | 332 | P332 | retroactively documented | 1 | 4 | P333 |
| 234 | 334 | P334 | the omitted k=8 macro-clue permutation case run | 1 | 2 | P346 |
| 235 | 344 | P344 | Seed 5 | 1 | 6 | P345 |
| 236 | 345 | P345 | correction to Phase 344 | 1 | 1 | P347 |
| 237 | 357 | P357 | QR module-tile scale-history inversion | 1 | 1 | P358 |
| 238 | 358 | P358 | repository-wide exact 7x7 QR tile fingerprint | 1 | 2 | P362 |
| 239 | 359 | P359 | constant-fill QR finder renderer calibration | 1 | 2 | P364 |
| 240 | 362 | P362 | all-six QR module-variant fingerprint | 1 | 2 | P363 |
| 241 | 363 | P363 | QR-eye PNG scanline provenance | 1 | 3 | P364 |

**126** of **367** phases have in-degree 0 (leaves: not cited by any other phase's body text -- terminal work, or work whose citations use phrasing this heuristic missed).

## Ambiguous mentions (excluded from the graph above)

Bare `Phase 2` / `Phase 3` (no `solved`/`puzzle` prefix) collide with
the unrelated puzzle Phase 2/3/3.2 AES boundary numbering and are not
resolved automatically. Manually check these before trusting any
in-degree count for Phase 2 or Phase 3 themselves.

None found.

## Dangling number mentions (no matching phase heading)

`Phase N` text where N does not match any FINDINGS.md heading (likely a typo, a sub-numbered reference like "Phase 8's second half", or a mention of a non-FINDINGS numbering scheme).

| Number | Mentions |
|---|---|
| 324 | 4 |
| 2026 | 3 |
| 0 | 2 |
| 1 | 1 |
