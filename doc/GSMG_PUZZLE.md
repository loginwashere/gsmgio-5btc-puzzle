# GSMG.io 5 BTC Puzzle — Research Summary (2026-07-03)

Survey + hands-on cryptanalysis of the GSMG.io puzzle, done while scanning for viable
new targets alongside puzzles #71/#135. **Conclusion: parked, not pursued** — see
[Assessment](#assessment-worth-diverting-the-rig) at the bottom.

---

## 1. Overview

- Created 2019 by a creator known on Telegram/forums as **"Jrk Bgrt"**; announced via
  `gsmg.io/puzzle`.
- Total original prize: 5 BTC. On-chain balance re-verified live during this session:
  **~1.256 BTC still unclaimed** at the puzzle's funding address — no *solver* has ever
  swept it, despite years of "SOLVED"/"breakthrough" claims filed as GitHub issues.
- Multi-stage puzzle: image steganography → keyword extraction → chained classical
  ciphers → currently stuck at the final phase, referred to by the community as
  **"Cosmic Duality"** / **SalPhaseIon**.
- Not an ECDLP/keyspace problem at any stage — no *bounded* interval is involved (see
  "Prize address mechanics" below for why this holds even though the pubkey is now
  on-chain). This is classical cryptanalysis (steganography, substitution/transposition
  ciphers), not something kangaroo or brute-force GPU search applies to.

### Prize address mechanics (2026-07-12)

The balance shrank from 5 BTC to ~1.256 BTC via **two deliberate self-spends by whoever
holds the key** (the creator, since day one) — not a solver draining it. Checked on-chain
directly (all 125 txs on `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`, paginated):

- **2020-05-11** (the exact day of the first Bitcoin halving): spent the original 5 BTC
  → 2.5 BTC out to `17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa`, ~2.498 BTC back to the same
  GSMG address.
- **2024-04-24** (days after the second halving): spent that remainder → 1.25 BTC out to
  the *same* external address again, ~1.253 BTC back to GSMG.

A deliberate, self-administered "halve the prize each Bitcoin halving" policy. The
recipient address is pure cold storage (43 incoming txs, 0 ever spent, ~3.7505 BTC
total received — of which 3.75 BTC / 99.985% is exactly these two withdrawals) —
consistent with a personal savings wallet, not an exchange.

This does expose the address's public key on-chain (extracted from both spends'
scriptSig, same uncompressed key each time):
`04f4d1bbd91e65e2a019566a17574e97dae908b784b388891848007e4f55d5a4649c73d25fc5ed8fd7227cab0be4e576c0c6404db5aa546286563e4be12bf33559`.
**Kangaroo/BSGS still doesn't apply**: those methods need a *bounded* search interval
(the #71-160 puzzle series works only because each key is deliberately constructed
within a known small bit-range). GSMG's key is the output of decoding a chain of
classical ciphers into an ordinary Bitcoin private key — no reason to think it's
confined to anything smaller than the full ~256-bit keyspace. Exposed pubkey without a
bounded range is computationally the same as attacking any random Bitcoin address.

---

## 2. Solve chain (verified / independently reproduced)

### Stage 0 — image analysis
- `gsmg.io/puzzle` hosts a grid-pattern image plus a "follow the white rabbit" hint image.
- Fetched both via Wayback Machine (WebFetch cannot reach `web.archive.org`; used `curl`
  directly). Confirmed byte-identical across 2020/2023/2026 snapshots.
- Copied into [doc/img/gsmg_puzzle_stage1.png](img/gsmg_puzzle_stage1.png) and
  [doc/img/gsmg_rabbit_hint.png](img/gsmg_rabbit_hint.png) for reference.
- Independently reproduced the community's decode from scratch: my own pixel-sampled
  14×14 grid extraction + spiral-read algorithm → `gsmg.io/theseedisplanted` (the next
  stage's URL). Note: my own grid differed from the community's transcription by exactly
  one cell (row 8), but the final decoded string matched either way — treated as a minor
  sampling artifact, not a methodological error.

### Site map / URL derivations (2026-07-08 addition)

Compiled by walking every link on the live/archived pages plus the browser URL bars
visible in this project's own screenshot images — done to check whether those
screenshots (previously assumed to show "already-transcribed" content, per the
Phase 5 forensic audit below) actually had been verified against a real source. They
hadn't; this closes that gap.

| Page | URL | Notes |
|---|---|---|
| Stage 0 | `gsmg.io/puzzle` | Not HTML — a bare 1048×1556 PNG served directly (confirmed via `curl`; browser tab title is literally `puzzle (1048×1556)`). |
| Stage 1 | `gsmg.io/theseedisplanted` | Real HTML page. Has a hidden `<form>` POSTing to `gsmg.io/phase1verification` and 8 icon images (`img/black_banking - war.png`, `blue_ca.png`, `blue_dig_i.png`, `blue_lock_lo.png`, `red_crypto_gic.png`, `red_n_you.png`, `red_open_lock_n_ing.png`, `red_t.png`). **Visible rebus, corrected 2026-07-26:** `WAR`+`NING` and `LO` inserted into `CRYPTO`/`GIC` identify **The Warning by Logic**; the remaining fragments spell **CAN YOU DIG IT**, matching the previous-stage prompt. A historical 2021 solution records the same title/artist mechanic and the lyric-derived form password already listed below. **Symbol layer, audited 2026-08-13:** closed/open lock, `+/-`, banking/crypto, and the red/blue split positively illustrate the song's “opposites attract” line and cue cross-group joining, but do not select a second string; a 16-candidate four-blob oracle check was clean. The separate 2026-07-12 forensic result still stands: the PNG containers/LSBs contain no additional hidden payload, no FEFE-style planted pixel occurs, and their anti-aliasing colors are ordinary. `tools/gsmg/phase1_icon_rebus_audit.py` also finds no distinctive number in naïve white-region overlap. |
| Phase 2/3 | `gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself` | URL slug is itself a Merovingian/*Matrix Reloaded* quote. Shown in [doc/img/gsmg_phase2.png](img/gsmg_phase2.png)/[gsmg_phase3.png](img/gsmg_phase3.png). Contains a Thévenin/Norton-theorem-themed riddle about historical rulers, a chess FEN position (`B5KR/1r5B/6R1/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 w - - 0 1`) requiring the "buddhist's" — bishop's — non-mate move, and a `/(aBa, connected enf)` convention (`aBa` = preserve casing, `enf` = remove whitespace). **Verified this exact text is already fully documented and solved in the fork's public `README.md` (lines 92-205)** — genuinely not new, despite how elaborate it looks. |
| SalPhaseIon + Cosmic Duality | `gsmg.io/89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32` | Shown in [doc/img/gsmg_salphaseion_cosmicduality.png](img/gsmg_salphaseion_cosmicduality.png). The hash is `SHA256("GSMGIO5BTCPUZZLECHALLENGE" + "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe")` — recomputed independently, matches exactly (also documented in the fork's README). **This is the verified real source of this project's `dbbi`/`faed` data** — good confirmation the starting data is legitimate, not a transcription error. |
| Misc | `help.gsmg.io` | A subdomain referenced once on the SalPhaseIon page; not followed up. |

### Solved-Chain Provenance Ledger

The primary public `puzzlehunt/gsmgio-5btc-puzzle` README documents these exact
artifacts and their use. Keep both chess positions distinct: the first is the
prompt; the second is the required post-move answer.

| Artifact | Verified value |
|---|---|
| Phase 1 form password | `theflowerblossomsthroughwhatseemstobeaconcretesurface` |
| Phase 2 answer/hash | `causality` → `eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf` |
| Phase 3 parts 2–5 | `Safenet`, `Luna`, `HSM`, `11110` |
| Chess prompt | `B5KR/1r5B/6R1/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 w - - 0 1` |
| Chess post-move answer | `B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1` |
| Phase 3 seven-part hash | `1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5` |
| Phase 3.2 clue-answer hash | `250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c` |
| Phase 3.2.1 Beaufort key | `THEMATRIXHASYOU` |
| SalPhaseIon entry hash | `89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32` |

**Hidden-path hunt (2026-07-08): dead end, confirmed.** Queried Wayback's CDX API for
every URL ever archived under `gsmg.io` (601 total). Beyond the pages above, every
other path -- including evocative guesses like `final_stage`, `puzzle/stage5`,
`phase3_2_2_2`, `whiterose`/`whiteroseredqueen`, `eps3.4_runtime-error.r00`,
`door.png`, `youarewrongaboutdirhunt`, the 8 icon-filename paths (`banking-war`,
`crypto-gic`, etc.), and a dozen 64-hex-char paths -- all resolve to the **same
generic Vue SPA catch-all shell** (`<title>GSMG</title>`, `<div id="app"></div>`,
~11800-13000 bytes), verified by direct fetch+diff (identical modulo a random CSRF
token). Every *real* puzzle page carries `<title>GSMG Puzzle</title>` (two words) --
none of these do. Since this SPA returns HTTP 200 for any undefined route, the large
URL list mostly reflects other researchers' (or bots') speculative path-guessing, not
real hidden content. Directory/path discovery is not a viable lever here -- don't
re-attempt.

**Net effect:** no new lever on the actual open blocker (`dbbi`/`faed`). This is
site-map bookkeeping and a legitimacy check on already-used data, not a new
cryptanalytic lead — filed here so it doesn't get re-discovered/re-verified from
scratch in a future session.

### Local Wayback mirror (2026-07-12)

`gsmg.io` itself has since gone down for real — the live domain now serves a
domain-parking redirect page (fingerprinting + bounce to a tracking URL), not the
actual site. Mirrored every archived URL from the Wayback CDX API (394 unique URLs,
~59MB) to `/home/loginwashere/projects/gsmg-site-mirror/` so the site can be browsed
without depending on Wayback or the (now-dead) live domain.

**To view it:**
```
cd /home/loginwashere/projects/gsmg-site-mirror && python3 -m http.server 8080
```
It's a client-rendered Vue SPA with no backend anymore, so most routes just show an
empty loading shell. Only these 3 pages have real content baked directly into the
static HTML and are actually worth opening:

| Page | Local link |
|---|---|
| Stage 1 ("the seed is planted") | [localhost:8080/theseedisplanted.html](http://localhost:8080/theseedisplanted.html) |
| Phase 2/3 (Thévenin/Norton riddle) | [localhost:8080/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html](http://localhost:8080/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html) |
| SalPhaseIon + Cosmic Duality (the endgame — `dbbi`/`faed`/both AES blobs) | [localhost:8080/89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32.html](http://localhost:8080/89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32.html) |
| Phase 0 raw puzzle image (grid + red bar + QR code + branding, 1048×1556) | [localhost:8080/puzzle_raw.png](http://localhost:8080/puzzle_raw.png) |

**Gotcha:** the exact URL `gsmg.io/puzzle` (no trailing slash) is what the live server
returned this raw PNG for directly — but the mirror fetch failed on it
(`[Errno 21] Is a directory`, since a directory already exists at that path holding
`puzzle/index.html`/`puzzle/stage5.html` from the *uppercase* `/Puzzle` Vue-rendered
sub-pages — can't have a file and a directory with the same name). So
`localhost:8080/puzzle/` only ever shows the Vue-app shell, which embeds just the small
350×350 `follow_the_white_rabbit.png` (grid only, no red bar/QR/branding) — not the
real server-generated image. Copied the genuine asset in from the community fork's own
repo checkout (`gsmgio-5btc-puzzle/puzzle.png`, verified identical dimensions/content)
to `puzzle_raw.png` so it's actually viewable locally.

Everything else under `gsmg-site-mirror/` (the ~136 `phase1.html`/`login.html`/etc.
"friendly"-named routes and every bot-guessed hash path) is the identical generic
Vue-SPA shell — real content there was always fetched client-side from the live
backend API, which no longer exists. Static assets (`img/*`, `fonts/*`, `pdf/*`,
`css/app.css`, `js/app.js`) are real and render fine; a handful of paths have a
misleading extension but actually contain the generic shell (`css/puzzle.css`,
`img/puzzle.png`, `.well-known/assetlinks.json`, `feeds/all.atom.xml`) — don't trust
those by filename alone. Full per-URL provenance (original URL, Wayback timestamp,
local path) is in `gsmg-site-mirror/_manifest.json`.

**Gotcha for any future re-mirror**: the root `/` URL's *latest* Wayback snapshot is
the dead-domain parking page, not the real site — had to manually pick the last
pre-death snapshot (2026-04-18) instead of the newest one. Also, `urllib`/plain `curl`
don't auto-decompress Wayback's `br`/gzip/zstd `Content-Encoding` — must use
`curl --compressed` (or equivalent) or you'll save raw compressed bytes under a
misleading `.html` name.

---

### Phase 3.2.1 / 3.2.2 — validated
- Cipher: **straddling checkerboard / VIC cipher** over a keyed 28-symbol alphabet
  (26 letters + `.` used twice as column/row separators).
- Community decoder (`cb2.py`, from the `halbgott29a/gsmgio-5btc-puzzle` fork) reproduces
  the known answer exactly. I ran it myself and confirmed:
  ```
  INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE
  ```
- This validates the cipher family (straddling checkerboard) as the correct tool for the
  still-unsolved text further down the chain.

---

## 3. Current blocker — "Cosmic Duality" endgame

Two undecoded strings remain, embedded in the SalPhaseIon page source (9-symbol
alphabet, `a`–`i`):

| String | Length | Index of Coincidence | Character |
|---|---|---|---|
| `dbbi` | 91 symbols | 0.151 | structured / key-like |
| `faed` | 570 symbols | 0.118 | ~uniform / high-entropy encrypted payload |

A trailing plaintext fragment is appended after the `faed` block in the raw page text:
`...zshabefourfirsthintisyourlastcommand` — a likely hint about process/tooling, not yet
cracked.

**Hypothesis** (cipher family validated by reproducing 3.2.2): same
straddling-checkerboard/VIC scheme, but requires **four unknowns to align simultaneously**:

1. the 28-symbol keyed alphabet (driven by an unknown keyword)
2. the `a`–`i` → digit mapping (`a0i8` vs `a1i9`)
3. the escape-digit pair (2 of 10 digits reserved for two-digit codes)
4. a transposition / over-encryption keystream layered on top

**The "verification problem"** (documented in the community's `FINDINGS.md`, and
independently confirmed by my own sweep below): there is no partial-credit signal. A
completely wrong guess and a completely right guess both just look like noise or
coincidentally score well on English-word heuristics — the only trustworthy oracle is
whether `sha256(answer)` actually opens the final AES-CBC blob. This makes naive
hill-climbing / word-scoring unreliable by design, not just unlucky.

---

## 4. What's been tried

### Community (`halbgott29a/gsmgio-5btc-puzzle` fork — most rigorous *data*, but its
analysis layer is AI-assisted, not organic multi-year community consensus — see
correction below)
- `FINDINGS.md` + `joint_attack.py`: ~20 keyword alphabets × 2 digit-mappings ×
  3 transpositions × 3 over-encryption schemes × 3 escape pairs × 6 answer-normalization
  forms = **4904 decode-forms tested against the real AES oracle** (`sha256(answer)` as
  OpenSSL passphrase against the SalPhaseIon/Cosmic CBC blobs) → **0 hits**.
- Also falsified, with specifics: steganography (none found in the images), book cipher
  (0/27 and 1/27 hit rates against candidate source texts), and the "matrixsumlist
  triangle" geometric hypothesis (shown to be apophenia via a 38k-random-string
  null-model test — random strings "find" the same triangle at the same rate).
- Creator's Telegram export (`creator_jrk.txt`, 411 messages / 1,283 text lines,
  2019–2026): creator
  acknowledges the community GitHub repo's legitimacy and progress ("I checked a certain
  GitHub yesterday... You guys are really getting close") but as of Nov 2024 states
  flatly there is no further hint coming ("No clue Friday. Every Saturday.").

### My own additions this session
- Verified `cb2.py`'s decoder correctness by re-running the 3.2.2 validation myself.
- Re-ran the fork's own 7-keyword sweep against `dbbi` — confirmed **0 candidates**
  score ≥10 (matches the fork's documented negative result; not a discrepancy).
- Wrote `my_sweep.py` (reusing `cb2.py`'s validated `build()`/`decode()`), testing **~24
  fresh candidate keywords** not in the fork's own lists — pulled from the puzzle's own
  lore/chat (`ARCHITECT`, `MEROVINGIAN`, `HALFANDBETTERHALF`, `BETTERHALF`, `CIAOBELLA`,
  `THEONE`, `GSMGIO5BTCPUZZLECHALLENGE`, the creator's own handle, direct creator quotes
  like `GOODPUZZLESDONTNEEDHINTS`, etc.) — against both `dbbi` and `faed`, both digit
  mappings, all escape pairs, scored by weighted English-word content:
  - **`dbbi`**: 284 candidates scored >0; top score only **10** (noise-level — these
    turned out to be filtered re-derivations of the *already-known* 3.2.2 answer under
    different keep/drop rules, not new decodes).
  - **`faed`**: 1130 candidates scored >0; top score **33**, still clearly gibberish
    (coincidental substring hits like "ONE"/"THE" scattered in otherwise-random output).
  - Net result: no candidate beats noise. This is a genuine additional negative result,
    not just a repeat of the community's — and it further corroborates their "verification
    problem" diagnosis, since my own heuristic visibly overfit on short strings exactly
    as they warned.
- Confirmed via GitHub API (`gh api` was flaky; fell back to plain `curl` against
  `api.github.com`) that several "SOLVED"/"breakthrough" issues filed against
  `puzzlehunt/gsmgio-5btc-puzzle`, plus unrelated planted comments on a closed `pybtc`
  issue, are very likely **fabricated/AI-generated misinformation**: confident jargon,
  no falsification attempts (unlike the honest fork's writeups, which report negative
  IoC/hit-count results in detail), isolated additions to old closed threads from
  otherwise-inactive accounts, and none reproduce independently. Cross-checked against
  the live on-chain balance (still unmoved) as the ground truth.

### Still open / unresolved — reassessed 2026-07-04, likely a dead end
- GitHub issue #92 (researcher "marcofortina") raises a `cosmic_A`/`ca` operand
  referenced in `k_new = cc[833:865] XOR ca[280:312]`, with no public definition found
  after an extensive OSINT sweep (65 forks, 82 issues, Wayback CDX). This was previously
  flagged here as "the single most targeted unresolved thread." Tracing the terminology
  back changes that assessment:
  - `cosmic_A`/`ca` and the `k_new = cc XOR ca` framing originate from a small number of
    comments by a single account (`GalloClaudio64`, 2 comments total in the repo — on
    issue #68, and on **issue #69**, which this doc already flagged as a fake "SOLVED"
    post recycling the public 3.2.2 validation number). GalloClaudio64's own claims are
    all hand-wavy ("the only way out will be an XOR triangle... I haven't solved the
    part that comes after that (yet)") — no code, no reproducible artifact, ever shown.
  - The same "CHAIN 1/2/3"/`cosmic_A` breakdown gets reposted verbatim by unrelated
    accounts months apart (including a Portuguese translation reposted back into English
    four months later) — the amplification pattern of spam/bot accounts, not independent
    corroboration.
  - **Naddiseo** (the same researcher whose early notebook is cited above as a legitimate
    source) directly and publicly dismissed a closely related "Complete Solution" post in
    the same thread as *"soup. Complete Nonsense,"* adding: *"Repeat after me: Large
    Language Models like ChatGPT and Claude cannot solve this puzzle."*
  - A separate, carefully-hedged post (issue #82, `vadiksh85-pixel`) independently tested
    every plausible transformation class over the public artifacts and concluded no
    reproducible function yields a key matching the real prize address — an honest
    negative that's consistent with `cosmic_A` not corresponding to anything real.

  **Updated read: this isn't a well-defined gap waiting to be closed — it's most likely
  fabricated terminology that good-faith researchers (marcofortina, ektemfg) have been
  chasing in good faith. Not recommended as a lead.**

  **The fabrication-provenance evidence remains material.** Issue #88 grew into a
  six-account mutually-citing thread (`andersonbig`, `WabiLipa`, `marcofortina`,
  `valleytainment`, `robotixcoder`, `zemnovodnuy`) layering `Chain4`, `row1-4`,
  `Door-2 LCP7`, and similar terms onto the same root. Within that thread nobody
  supplied derivation code; the recurring pattern was “I've confirmed X, how did you
  get Y?” The same checkpoint hash, XOR result, and two claimed addresses recur across
  at least issues #55, #69, #72, #79, #80, #81, #88, #91, #92 and the associated
  bitcointalk post. That is one dependent citation network, not independent
  convergence. In issue #17, `pawel-mar` independently warned that “a lot of the code
  shared here was implemented by LLMs” and that “no one has actually decrypted the
  AES.” Those observations are not negated merely because one published construction
  can regenerate its own checkpoint.

  **Correction (2026-08-09): the checkpoint is reproducible; the 2026-07-12
  falsification was a password-representation error.** The earlier audit passed the
  64-character hexadecimal rendering of `a795de11...e50735` as password text. The
  published construction uses those 32 values as raw binary password bytes and the
  legacy MD5 `EVP_BytesToKey` KDF. Re-running the authenticated 1,344-byte COSMIC
  envelope under that exact interpretation gives valid one-byte PKCS#7 padding, a
  1,327-byte payload, and the quoted SHA-256
  `4f7a1e4efe4bf6c5581e32505c019657cb7b030e90232d33f011aca6a5e9c081`.
  Its first 10,609 bits, read MSB-first into a 103x103 matrix, also reproduce the
  published `S=5193`, one-based `Wr=268603`, and `Wc=268828`. Telegram messages
  `68249`/`68259` exposed the raw-versus-hex mistake; this project then reproduced it
  independently in `tools/gsmg/cosmic_raw_digest_checkpoint_audit.py`. Full report:
  [doc/GSMG_COSMIC_RAW_DIGEST_CHECKPOINT_AUDIT.md](GSMG_COSMIC_RAW_DIGEST_CHECKPOINT_AUDIT.md). The original public commit
  `8f47839251a8b49e67a41ecb8d964fddd5e9270c` explicitly uses `unhexlify()` before
  MD5, confirming that raw bytes were part of the published implementation rather
  than a later repair.

  This retracts **only** “the checkpoint cannot be reproduced.” Reproducibility does
  not rebut fabrication: a construction selected for a padding-valid result should
  reproduce once its exact bytes and KDF are known. Here the output is high-entropy
  binary garbage (7.87 bits/byte; 38.8847% strict ASCII), valid padding occurs about
  once per 255 random decryptions, MD5 conflicts with the SHA-256 KDF used by the
  verified phase, and every later hash/invariant descends from that same output rather
  than an independent target.

  The complete public downstream construction also reproduces: seven leftover bits
  give `p_big=58`/`p_little=46`; shift-7 row-plus-column sums fill base-38 digits
  `0..37`; the 68-byte result splits into two 32-byte values plus four trailing bytes;
  and those values reproduce `1JG648ya...` and `145ZQ9si...`. Crucially, Phase 156
  independently identifies those exact addresses as the dominant input signers behind
  88 of 105 third-party OP_RETURN spam transactions sent to the genuine GSMG addresses.
  The spam includes the literal bait
  `matrixsumlistenterlastwordsbeforearchichoicethispassword`, mechanically linking the
  campaign to this construction's token vocabulary. Zero of those transactions was
  signed by a creator-controlled key. Thus the corrected overall verdict is:
  **mechanically reproducible, but still strongly supported as a fabricated/community
  spam construction rather than a creator-authenticated puzzle solution.** The actual
  prize address remains untouched.

---

## 5. Key resources

- [doc/img/gsmg_puzzle_stage1.png](img/gsmg_puzzle_stage1.png),
  [doc/img/gsmg_rabbit_hint.png](img/gsmg_rabbit_hint.png) — puzzle images (Wayback
  Machine, byte-identical 2020/2023/2026).
- `Naddiseo/gsmgio-5btc-puzzle` — early community notebook (`salphaseion.ipynb`),
  documents Phase 3.2.1/3.2.2 but stops before Cosmic Duality.
- `halbgott29a/gsmgio-5btc-puzzle` (fork) — most rigorous public effort: `FINDINGS.md`,
  `cb2.py` (validated decoder), `joint_attack.py` (AES-oracle-verified joint search),
  `creator_jrk.txt` (Telegram export).
- `puzzlehunt/gsmgio-5btc-puzzle` — main community repo; hosts many issues, a
  non-trivial fraction of which are unreliable/fabricated "solved" claims (see above).

---

## Assessment: worth diverting the rig?

**No.** This isn't an ECDLP/keyspace-search problem — no kangaroo or brute-force GPU
advantage applies at any stage. It's pure classical cryptanalysis (small discrete
alphabet-parameter space, cipher-family guessing), CPU-only, and already exhaustively
attempted by a large, technically serious community for 5+ years (thousands of Telegram
messages, dedicated GitHub repos with rigorous negative-result writeups, a systematic
4904-combination joint attack) without success. The remaining prize (~1.256 BTC) doesn't
justify new dedicated tooling given how thoroughly picked-over the interpretive parameter
space already is.

**Update (2026-07-03): the dictionary-scale sweep has now been built and run.**
`tools/gsmg/` implements it — `cb_common.py`/`data.py` (ported, byte-verified decoder +
AES oracle), `lastcommand_probe.py` and `alphabet_hypothesis_check.py` (Phase 0 cheap
probes), and `cosmic_sweep.py` (the sweep engine, parallelized via
`ProcessPoolExecutor`), fed by a new curated wordlist (`scripts/wordlist-gsmg.py` →
`wordlists/gsmg/`) plus this repo's existing mid-size lists. Full results in
[tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md); summary:

- The "your last command" hint (found in an early community notebook, describing a
  literal AES blob embedded directly in the page) was probed directly: **0/28 hits**.
- Whether the assumed `pad28(keyword)` alphabet-construction rule even reproduces the
  one known-good alphabet (Phase 3.2.2) was checked across all 49 previously-tried
  keywords: **no match** — that model remains unverified, not just unlucky.
- The full sweep — 338,905 unique candidates (curated puzzle lore + cypherpunk +
  bitcoin-historical + Gutenberg-derived phrases + three system dictionaries) × both
  digit-mappings × all 45 escape pairs × both `dbbi`/`faed` targets, verified against
  the real AES-decrypt oracle — **677,810 keyword-tests, 0 hits**, ~25 min on 16 cores.

That's roughly 140× the candidate-keyword coverage of the community's own joint attack,
still coming back clean.

**Update (2026-07-03, follow-up): the alphabet-derivation gap is now resolved — and it
explains the negative result.** Tracing exactly how the one ground-truth alphabet
(3.2.2's `FUBCDORA.LETHINGKYMVPS.JQZXW`) was actually built (via the community fork's
`README.md`) shows it comes from hand-parsing a **riddle sentence** — *"A fubcd-king &
oracle-queen, thingky mvps, on a sad board but as wide as the first one seen"* — not
from any keyword run through a generic formula. Mechanically reproducing that riddle's
derivation reproduces 23/28 characters of the real alphabet exactly, including both of
its structurally-placed `.` characters, at positions `pad28()` could never have
produced (verified byte-for-byte: real dots at index 8/22, `pad28()` always emits 8/18).
The community's own `FINDINGS.md` independently reaches the same conclusion in their own
words: *"the alphabet is a 26! space... the endgame is computationally unbreakable from
our position"* without the correct interpretation.

This means **the two big keyword sweeps (community's 4904-test + this session's
677,810-test) were never a coverage problem — the model itself was wrong**, and a bigger
wordlist (rockyou/Pwdb) would not have changed the odds. That follow-up sweep is no
longer recommended.

**Update (2026-07-04): the "another door" / prime / neo's-passport hints also checked
out negative.** Pulled the full 181k-line community chat export (not just the filtered
creator-only excerpt) to get the exact chronology: *"another door might be found on
{1},{4},{21}"* (2021-04-01), a clarification that *"prime numbers... [are] required"*
and *"some characters need to be 'zeroed out'"* (2021-12-26), and *"the expiry date of
neo's passport"* — September 11, 2001, a well-documented *Matrix* (1999) prop Easter
egg. This exact thread is the single most-discussed unresolved hint in the community
chat (298 mentions), but the fork's own tools only tested it two ways — both since
falsified or inconclusive (see [tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md)
Phase 4 for detail). Neither tried these hints as **direct AES passphrases** or as a
**prime-position zeroing transform on the validated (non-triangle) decode pipeline** —
both cheap and untried, so both were run: 31 direct-passphrase candidates (62
keystring attempts) and 12 zeroing-decode-forms, verified only via the real AES
oracle. **0 hits either way.**

**Update (2026-07-04, same day): independent image forensic audit also came back
clean.** The fork's "no steganography" claim was only ever made about the earlier-
stage images (`puzzle.png`, `theseedisplanted.png`) — never explicitly re-checked for
the Cosmic-Duality-era ones. Pulled all six puzzle images fresh and audited them
directly: full PNG chunk walk + CRC check, trailing-bytes-after-IEND, text/EXIF
chunk dump, and R-channel LSB check. Clean across the board — no hidden data
anywhere. Turns out `SalPhaselonCosmicDuality.png`, `phase2.png`, and `phase3.png`
are literal **browser screenshots of the puzzle's own webpages** (URL bar visible in
each) — there's nothing encoded in them to find, because everything they show is
already plaintext, already transcribed. This also explains why their color palettes
looked nothing like `puzzle.png`'s (which genuinely does use a small set of pure
blue/yellow pixels for its spiral-read binary counter — confirmed by contrast).

**Update (2026-07-04, continued): checked for genuine recent progress and read every
creator message end-to-end.** The fork's `FINDINGS.md` and its chat export were both
added in the same commit (2026-06-13) — barely three weeks old, so there's little
gap in that data to re-scan. What could be checked: the wider community repo's
GitHub activity since then. Result: a burst of new issues, **all of which are
fabricated or spam** on inspection (fake "proof" addresses that aren't the real
puzzle address, an unfilled template placeholder left in a "breakthrough" post,
recycled already-public keywords dressed up with unverifiable hex) — matching this
doc's earlier-documented pattern exactly. On-chain balance is unchanged
(confirms nothing real happened). The one serious, ongoing thread (the `cosmic_A`/
`ca` gap, already flagged above) remains unanswered as of mid-June, per two
independent researchers hitting the same wall.

Separately, read all 411 of the creator's own messages in full (not just keyword
search) looking for another riddle like the 3.2.2 one. Found two previously-
undecoded binary-encoded messages — one reveals already-known keywords
(`yellowblueprime`, `matrixsumlist`, `lastwordsbeforearchichoice`, `yinyang`, all
already tried), the other is an elaborate multi-year-running **Rick-Roll troll**
from the creator (a Caesar-cipher riddle that leads to a base64-encoded link to
Rick Astley's video — confirmed by the community back in 2024). No new riddle-style
hint was found anywhere in the full export.

Six independent lines of attack have now come back negative: the dictionary sweep,
the alphabet-construction model itself, the creator's two most-discussed open hints
read literally, the image forensic audit, the check for recent genuine progress, and
the full message read-through. None of it was a coverage gap — every cheap,
well-motivated hypothesis available has been tried. What's left needs either a new
creator hint or an interpretive leap nobody (community or this project) has found
yet.

**Update (2026-07-07): a native base-9 checkerboard model, structurally narrowed via
frequency analysis, was tried and also came back negative.** All prior sweeps assumed
`dbbi`/`faed`'s `a`-`i` alphabet was a lossy stand-in for decimal digits (`MAPS`'
`a0i8`/`a1i9`), requiring a brute-force search over both mappings x all 45 escape-digit
pairs. Comparing `dbbi`'s symbol frequencies against the *known* escape-digit character
share from the already-solved 3.2.2 stage (70/149 = 47.0%) singled out `{b,e}` as the
escape pair with no close second (47.25% combined share vs. 38.5% for the next-best
pair, out of all 36 possible pairs) — and it segments `dbbi` cleanly. That collapses the
mapping+escape search from 90 combinations/keyword down to 2 (just `e1`/`e2` order), and
forces a 7-top + 9 + 9 = 25-symbol code table (`pad25()`, a classic I/J-merged
Polybius-style alphabet) rather than `pad28()`'s 26-letters-plus-2-dots.

New tooling: `tools/gsmg/cosmic_sweep_9ary.py` + `pad25`/`build_board_9ary`/
`decode_9ary` in `tools/gsmg/cb_common.py`. Results, all AES-oracle-verified:
- Default wordlist set (338,905 candidates, both targets, drop=J): **0 hits**, in 24s
  (vs. 1517s for the old model on the same set — confirms the ~45x combinatoric
  reduction).
- Hedge against the I/J-merge-letter assumption (drop in {J,Q,X,Z}, same wordlists):
  **0 hits**.
- Large password-list sweep (rockyou + Pwdb-10M + xato-10M + ignis-10M = 25,438,264
  unique candidates, `dbbi` only, drop=J, both escape orders): **0 hits**, 697s.

**Caution for future sessions:** the first attempt at the large sweep OOM-killed the
whole machine (kernel logged a *global* OOM, severe enough to also kill Chrome and
VSCode) — the bug was submitting all ~25M jobs to `ProcessPoolExecutor` individually
and upfront instead of in bounded batches. Fixed by chunking candidates (2000/task)
and capping in-flight futures to a small window; verified the fix reproduces identical
results while cutting memory from 19.6GB to ~84MB. If extending this sweep further,
keep the batching in place.

**Net effect:** the escape-pair/mapping unknowns are now resolved (or at least reduced
to a single well-evidenced hypothesis with a cheap 2-way order check), but a
large-scale password/dictionary sweep under this corrected model is now *also*
exhausted, same as the old model. This reinforces rather than overturns the
already-documented conclusion: the missing piece is very likely a hand-parsed riddle
sentence (as with 3.2.2's "A fubcd-king & oracle-queen..."), not a dictionary word or
leaked password, regardless of which checkerboard-model variant is used. A GPU port
of the AES-oracle check was considered and is technically straightforward (SHA-256 +
AES-CBC are ideal GPU workloads), but was not pursued: the bottleneck here is candidate
*generation* (finding riddle-shaped phrase candidates), not throughput on the
25-40M-candidate scale already covered on CPU in minutes.

**Update (2026-07-07, continued): audited the oracle's own assumptions — also
negative.** The AES-oracle's KDF digest (SHA-256) and key size (AES-256) were never
independently confirmed against either blob (no known-plaintext crib exists for them,
unlike the checkerboard cipher's `VALIDATION_NUM`); classic `openssl enc` actually
defaulted to MD5 pre-OpenSSL-3.0 (2021), after this puzzle's 2019 launch. Added
`KDF_VARIANTS` (SHA-256/MD5/SHA1 x AES-256/AES-128) to `cb_common.py`'s
`aes_try_open`, and reran everything under all 6 combos: default wordlists, the 51
hand-combined riddle candidates, and the full 25.4M-candidate password-list sweep
(rockyou/Pwdb/xato/ignis) — **0 hits, all configurations.** Also tested `faed` under
its own best-fit escape pair `{g,i}` (new `--escapes` flag) instead of assuming it's
pure payload — also negative. This specifically rules out "oracle was silently
miscalibrated" as an explanation for the negative results, which is a stronger
conclusion than another wordlist miss.

**Update (2026-07-07, continued): the remaining lower-priority structural variants
(tail-fill order, board topology, exhaustive drop-letters) also came back negative at
full dictionary scale.** Added `tail_fill` (forward/reverse/keyboard) to `pad25()` and
`topology` (top_first/escapes_first) to `build_board_9ary()`/`decode_9ary()` in
`cb_common.py`, plus `--tail-fills`/`--topologies`/`--all-drop-letters`/`--escapes`
flags to `cosmic_sweep_9ary.py`. A quick curated-vocabulary pass (520 candidates:
GSMG/cypherpunk/bitcoin-historical lore + the riddle combinations, all variants
combined) came back clean in 27s. The full default dictionary set (338,905
candidates x both targets = 677,810 keyword-tests, each covering all 26 drop-letters
x 2 topologies x 3 tail-fills x 2 escape orders internally, ~211.5M total decode
attempts) also came back clean: **0 hits, 15,917s (~4.4h)**, memory stable throughout
(fixed batching held).

Note this run used the default KDF (SHA-256/AES-256) only, not the full 6-variant KDF
sweep (already separately exhausted at 25M-candidate scale) — combining both axes
would have taken ~27h. `faed` under its own best-fit escape pair `{g,i}` was also only
checked at the smaller curated/default scale, not this full one.

**Update (2026-07-08, continued): generic transposition sweep at full scale, also
negative.** All 7x7=49 identity/reverse/col2-6 input x output transform combinations,
338,905 candidates x both targets (677,810 keyword-tests), ~1h51m, 0 hits. Combined
with the keyed-columnar sweep (matrixsumlist/lastwordsbeforearchichoicethispassword,
both directions) and the exact-grid-dimension unkeyed column reads (col7/13/15/38),
every transposition/keystream hypothesis raised this session has now been tested at
full dictionary scale. Also tested the "discovered path names" from a full Wayback
hidden-path hunt (whiterose, eps3.4_runtime-error.r00, the icon words, etc. — see
site-map section above) as candidates: negative too.

**Update (2026-07-08, continued): three targeted gap-closing checks, all
negative/clarifying.**

1. **`shabefanstoo` mechanically decoded — no hit.** This is the last 12 characters
   of the SalPhaseIon `<textarea>`, right after the embedded AES blob. It doesn't
   parse under the same `a`–`i`/`o` digit model that turned `shabef` into `sha256`
   (the letters `n`/`s`/`t` aren't valid digits in that alphabet), so every plausible
   mechanical reading was generated and tested directly against the AES oracle:

   | # | Candidate | Derivation |
   |---|---|---|
   | 1 | `shabefanstoo` | literal, as-is |
   | 2 | `sha256anstoo` | `sha` literal + digit-map `b,e,f`→`2,5,6`, rest literal |
   | 3 | `sh12561nstoo` | digit-map `a,b,e,f`→`1,2,5,6`, rest literal |
   | 4 | `s812561nst00` | full `a`-`i`/`o` digit-map wherever valid, rest literal |
   | 5 | `198125611419201515` | full a1z26 per-letter, concatenated |
   | 6 | `19-8-1-2-5-6-1-14-19-20-15-15` | full a1z26 per-letter, hyphen-separated |
   | 7 | `befanstoo` | `sha` prefix dropped |
   | 8 | `answertoo` | guessed English target (if letters were meant to compress it) |
   | 9 | `answer too` | same, spaced |
   | 10 | `sha256answertoo` | `sha256` + guessed target, joined |
   | 11 | `sha256 answer too` | `sha256` + guessed target, spaced |
   | 12 | `anstoo` | tail only, `sha`/digit-prefix dropped |

   Also ran an anagram search (exact 12-letter multiset match) against the full
   chat-mined wordlist and both system dictionaries — no match beyond the literal
   string itself (mined from chat because someone had quoted the puzzle). **0/12
   AES-oracle hits, 0 anagram hits.** Stays a genuine unexplained fragment, not a
   coverage gap — don't re-derive the same candidates again without a new idea for
   *how* it's meant to decode.

2. **`faed`'s own escape pair, properly re-derived — weakens the "faed has its own
   escape pair" premise rather than fixing it.** Redid the same frequency-share
   analysis that validated `dbbi`'s `{b,e}` (47.13% share, ~9-point gap to 2nd place —
   a decisive, unambiguous winner) on `faed` alone: top candidate `{g,i}` is only
   32.16%, with `{e,g}` 30.92%, `{g,h}` 29.15%, `{f,g}` 28.80%, `{a,g}` 28.27% all
   bunched close behind — no decisive winner. This is new evidence (not just another
   0-hit sweep) that `faed` is genuinely high-entropy payload/ciphertext, consistent
   with its already-noted low IoC (0.118, ~uniform), rather than an independently
   checkerboard-encoded string with its own escape digits. Reinforces the standing
   model (only `dbbi` is meant to be checkerboard-decoded into a password; `faed` is
   what that password unlocks) rather than opening a new "find faed's real escape
   pair" lever.

3. **Fresh raw-HTML re-read of the SalPhaseIon page, all 6 Wayback snapshots
   (2023-06 through 2026-04) — confirmed byte-identical, no hidden riddle
   sentence.** Diffed the actual page source (not the community README's
   letter-spaced transcription) across every archived capture — only cosmetic
   differences (`<h1>` capitalization, whitespace, Cloudflare analytics beacon
   tokens). Confirms the entire SalPhaseIon `<textarea>` is one single continuous
   string with nothing else anywhere on the page: `dbbi` + abba(`matrixsumlist`) +
   `faed` + z-segment(`lastwordsbeforearchichoice`) + z-segment(`thispassword`) +
   literal `shabefourfirsthintisyourlastcommand` + the AES blob (with embedded
   abba→`enter`) + trailing `shabefanstoo`. There is no separate riddle-sentence
   hiding elsewhere on this specific page the way 3.2.2's alphabet-seed sentence sat
   in the *previous* stage's plaintext — if one exists, it must be somewhere else
   entirely, not on this page as currently fully transcribed.

**Update (2026-07-11): fresh hunt for the missing riddle sentence — one real new fact
(the "Cosmic Duality" book), everything else confirmed exhausted.**

Reverse-engineered exactly how 3.2.2's riddle sentence produces its alphabet, since the
prior write-up only recorded the end result. It's not naive first-occurrence letter
extraction across the sentence — it's a compound-word trick: `FUBCD` (from "fubcd") +
first 3 *new* letters of "oracle" (`ORA`) = row 1 (8 letters); leftover `LE` + all of
`THINGKY` + `MVPS` = row 2 (13 letters). The `-king`/`-queen` suffixes are pure
chess-metaphor tags contributing zero letters — spotting *which words count* is the
actual trick, not mechanical dedup. This matters because it sets the bar for what an
equivalent Cosmic-Duality riddle would need to look like.

Fetched the community fork's actual creator-only Telegram export (`_work/creator_jrk.txt`,
411 substantive messages — same file referenced in Phase 7, re-fetched directly from
GitHub rather than relying on old notes) and scanned it for that exact signature
(non-dictionary coined words, unusual hyphenated compounds à la `fubcd-king`). **Zero
hits at every threshold tried**, including the loosest (a single 5+-letter non-dictionary
word). Also confirmed the 3.2.2 riddle sentence itself was never typed by the creator in
chat at all — a community member ("Legik") found it "in the hints section" and pasted it
into chat on 2021-04-21; it was never Jrk's own words. This closes off "creator chat
hides a parallel riddle" with a real full-corpus negative, not just a spot-check.

Also re-fetched the full 181k-line all-participants chat export (`_work/chat_transcript.txt`,
matches the "181k-line" figure cited in Phase 8 — our locally mined `chat_mined_lines.txt`
is a filtered subset of this) and ran the same coined-word scan across it: only 6 lines
anywhere in the whole export have 2+ non-dictionary words, and all 6 are people pasting/
discussing already-known cipher strings (Vernam attempts, the Phase 2/3 URL) — not a
hidden riddle. Consistent with, and independently reproduces, Phase 8's hyphenated-word-pair
sweep (1,145 pairs, all mundane) via a different method.

**New fact, not previously documented anywhere in this project or FINDINGS.md: "Cosmic
Duality" is a real book** — Time-Life's *Mysteries of the Unknown: Cosmic Duality* (1991,
ISBN 0809465175, archive.org id `cosmicdualitymys0000time`). Confirmed via the chat
export: on 2022-12-11 Jrk Bgrt reacted to an image posted by community member "barrystyle"
with "That is very specific", and on 2023-01-08 wrote "@barrystyle, provided a very
specific hint already." — genuine, dated, twice-repeated creator confirmation that
something barrystyle found is real and significant. Multiple other community members
(semaj: "honestly, i just searched for cosmic duality: mysteries of the unknown"; others
independently) converged on the same book without prompting.

**Important correction, logged so a future session doesn't repeat my mistake**: a 2025-06-13
message from community member "Diego Schmidt" attaches the label "(Cosmic Duality Book
Page - Life and Death)" to the Jan 2023 Jrk quote above — but Diego's own message frames
this as *his* retrospective attempt to "piece together some of JRK's lines to see if
anything fits", not a verbatim creator statement. The actual Jrk message has no book/page/
title mentioned at all. I initially presented this label with more confidence than it
deserves; it is unconfirmed community speculation, not a verified fact.

**The specific content barrystyle found is not recoverable from available sources.**
Telegram images aren't transcribed in the text export, barrystyle never speaks under that
handle anywhere in the 51,177-message corpus (only ever `@`-mentioned by others, never the
author of a captured message), and there's no Telegram API access available to pull the
original media. Community members who separately read the book in full or scanned its
index (searching for yin-yang/duality mentions) did not extract anything conclusive either
— this has already been tried, by multiple people, over roughly three years.

**Net effect:** the book connection is real and worth keeping on record (it explains the
stage's name/imagery and has genuine, repeated creator engagement), but it is not
currently actionable — there is no recovered page, quote, or number to test against the
oracle, and the community's own multi-year effort on this exact book came up empty. If
this is ever revisited, it needs either the original 2022-12-11 image (not obtainable
without Telegram access to that specific chat) or a fresh, disciplined read of the book's
actual text (available via archive.org's lending program, or a purchased copy — ISBN
above) — not more chat archaeology, which is now genuinely exhausted on this specific
question.

**Important correction (2026-07-12): the `halbgott29a` fork's "rigorous community
analysis" is AI-assisted, not organic multi-year consensus — reweight accordingly.**
Checked the fork's git history directly (`gh api .../commits`): it has genuine organic
history from 2020-2021 (real early-puzzle documentation commits — "known info", "Add
additional hint", the 2021 SalPhaseIon-phase commit), consistent with the repo owner
being a real long-standing community member. But `FINDINGS.md`, `cb2.py`, `joint_attack.py`,
and every other script in `_work/` — everything this project has been citing as "the
community's most rigorous public effort" — were all added in a single burst of 3 commits
on **2026-06-13, spanning 14 minutes**, and the commit messages are explicitly
**"Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"**. So when this doc has said
things like "the fork's FINDINGS.md independently reaches the same conclusion," that
independence is weaker than it sounds — it's a different Claude instance analyzing
similar data, not a separate multi-year human research effort arriving at the same place.

This does **not** mean the underlying data is fake: `chat_transcript.txt`, `creator_jrk.txt`,
the blob values, and the images appear to be genuine artifacts the repo owner actually
had access to (we've independently cross-verified chunks of this — byte-identical
Wayback re-fetches, the 3.2.2 validation number, the SHA256 URL derivation, the real
on-chain balance). It's specifically the **analysis/narrative layer** — `FINDINGS.md`'s
prose, the specific hypotheses the scripts test, and speculative additions like
`_work/gameoflogic_ocr.txt` (a full OCR of Lewis Carroll's 1886 *The Game of Logic* —
thematically plausible given the rabbit/Alice-in-Wonderland connection, but never
referenced anywhere in `FINDINGS.md` or tested by any script; almost certainly an
untested breadcrumb from that same AI session, not a vetted community lead) — that
should be understood as AI-generated and re-weighted as roughly equivalent to this
project's own analysis, not stronger independent corroboration of it.

**How to apply going forward:** keep using the raw data (chat export, creator messages,
blobs) as a primary source — it's real. Treat `FINDINGS.md`'s specific conclusions the
same way you'd treat a re-run of your own analysis, not as an independent second
opinion. `gameoflogic_ocr.txt` is untested, not previously-vetted-and-abandoned; if
pursued, treat it as a fresh idea (this project's own, same as the Cosmic Duality book
detour), not a lead someone already tried and gave up on.

**Update (2026-08-13): recovered and boundedly triaged.** The exact file was
recovered from upstream commit `8d043ad1` (90,139 bytes; SHA-256
`e269153ec9d502dc25986e54169a1c211841a4f7256b460e4a017bae3242a002`).
It genuinely contains the visually suggestive mechanics “nine counters,” “four
red and five grey,” and repeated half/smaller/larger diagrams, but contains zero
instances of the registered puzzle-specific vocabulary. No creator source selects
the book. Phase 252 therefore retains it as thematic/structural recognition only,
not as a decoder or candidate-string source.

**Update (2026-07-12): full audit of the fork's `_work/` scripts, ~9,000 more
keystr-tests, all negative.** Cloned the fork locally (`/home/loginwashere/projects/
gsmgio-5btc-puzzle`) and read every script. Found several (`cosmic_attack.py`,
`cosmic_concat.py`, `decrypt.py`, `parse_chat.py`, `blueyellow_attack.py` as originally
written, `hillclimb.py`) reference a hardcoded `D:\tmp\gsmgio-5btc-puzzle\...` Windows
path for the Cosmic blob or training corpus — meaning they could never have actually run
against the Cosmic blob (or with a real corpus) as committed. Read `FINDINGS.md`'s
claims as "SalPhaseIon was tested this thoroughly," not necessarily Cosmic.

Identified 3 genuinely novel mechanisms plus 3 scripts that ran but only under partial
KDF coverage, and re-verified all of them through this project's own validated
`aes_try_open` (full 6-KDF-variant oracle, both blobs):
- `matrixsum.py` (stage-0 grid row/col sums used as an index/selector over dbbi's raw
  letters, not digit-decoded): 180 keystr-tests, 0 hits.
- `blueyellow_attack.py` (blue/yellow-tagged characters of the stage-0 URL
  "gsmg.io/theseedisplanted" as candidate keys/alphabet seeds — fixed its broken
  Cosmic-blob path and tested properly): 7,770 keystr-tests, 0 hits.
- `faed_base9.py` (faed reinterpreted as a raw base-9 bignum → bytes, skipping
  checkerboard decode entirely): no `Salted__` prefix in any reinterpretation, no
  genuine high-ASCII result.
- `dbbi_full.py`/`dbbi_internal.py`/`dbbi_transpose.py` (dbbi combined arithmetically
  with the already-solved 3.2.2 plaintext: Vigenère/Beaufort, prime/b-position
  selection-zeroing, segment+aggregate, grid transpositions — previously only verified
  under SHA256/MD5): re-ran under the full 6-KDF oracle, 1,035 keystr-tests, 0 hits.
- `decrypt2.py`'s grid-sums-as-literal-passphrase idea (distinct from matrixsum.py's
  index-selector use of the same sums): 18 keystr-tests, 0 hits.

The rest of `_work/` (`cb9.py`, `checkerboard.py`, `columnar.py`, `vic_full.py`,
`cosmic_attack.py`, `cosmic_concat.py`, `decrypt.py`, `decrypt3.py`, `hillclimb.py`,
`prime_theory.py`/`prime2.py`, `matrixtri.py`/`triangle_zero.py`) either duplicates
models this project's own tooling already supersedes and has tested far more
exhaustively, or is heuristic-only/already-falsified — not re-run.

**Bottom line:** GSMG is parked as "explored, not pursued" — same disposition given to
the other puzzles surveyed this session (Bitaps SSS bounty, Ballet BIP38 CTF). Project
stays focused on puzzles #71/#135 kangaroo/brute-force work.

**Update (2026-07-12): user obtained the actual physical "Cosmic Duality" book from
San Mateo Public Library and photographed all 144 pages — full manual page-by-page
visual review completed, negative result.** This directly addresses the "not currently
actionable... needs a fresh, disciplined read of the book's actual text" gap noted above.

Reviewed all 73 screenshots (cover through back cover, every page in between) looking
for anything analogous to 3.2.2's riddle-sentence seed: hidden/added text, unusual
marginalia, highlighter marks, planted anomalies (in the spirit of the earlier-found
254,254,254 pixel-grid anomaly), or an unusual caption/title. Confirmed the book's real
structure matches the ToC exactly (essay "The Unity of Opposites" p.6 → Ch.1 "Dualities
As Old As Time" p.16 → essay "The Dark Side of Fairy Tales" p.41 → Ch.2 "The Battle of
the Sexes" p.48 → essay "Driving the Devil Out" p.71 → Ch.3 "In the Grasp of Ageless
Evil" p.78 → essay "Paths of Righteousness" p.98 → Ch.4 "The Triumph of Good" p.106 →
essay "Hark! Heaven's Winged Host" p.129 → Acknowledgments/Picture Credits/Bibliography
p.138 → Index p.140 → colophon p.144).

Found and resolved the "Diego Schmidt (Life and Death)" ambiguity flagged in the
2026-07-11 entry above: there are two genuine, ordinary "Life and Death" occurrences in
the book itself — "Life and Death in an Endless Cycle" (pp.12-13, a section within the
opening essay) and "LE MIROIR DE LA VIE ET DE LA MORT" / "The Mirror of Life and Death"
(p.39, caption for a 17th-century French engraving). Both are unremarkable existing book
content, not hidden puzzle material — this confirms Diego's label was pointing at real
text (not a fabrication) but was never more than his own retrospective pattern-match, as
already correctly caveated.

One ambiguous detail spotted (p.40, an orange/yellow highlighter-style mark near a
paragraph) but not distinguishable from ordinary prior-patron highlighting — nothing in
its position or the marked text ties it to the puzzle, no follow-up warranted.

**No hidden content, planted anomaly, or candidate riddle sentence found anywhere in
the book.** This closes out the one remaining actionable lead from the 2026-07-11 entry
— the book itself, read in full, is clean. Combined with the exhausted chat-archaeology
and fork-script re-verification above, the Cosmic Duality endgame has now had every
concretely-pursuable angle tried. Remaining options are strictly passive (wait for a new
creator hint) or low-probability (barrystyle's original 2022 Telegram image, if ever
obtainable). Disposition unchanged: parked as "explored, not pursued."

**Update (2026-07-12): quadgram-fitness hill-climb against `dbbi`'s checkerboard key,
independent of guessing the riddle sentence — negative.** Rather than continuing to
guess candidate riddle sentences top-down, attacked the substitution key directly:
standard ciphertext-only cryptanalysis technique (English quadgram log-probability as
fitness, simulated-annealing hill-climb over the 25-letter-to-symbol key space), run
across all 4 structural variants (`{b,e}` escape-role x `top_first`/`escapes_first`
topology) with 15,000 random restarts x 5,000 iterations each (60,000 restarts / 300M
decode+score calls total, parallelized across 16 cores, ~10min wall time).

Result: overwhelming convergence to a single dominant local optimum across every
variant and restart — top 300 candidates collapsed to just 2 unique decodes, best
score −285.3 (`top_first`, `b`/`e`) for `PLANDSSETURBEEARETTWOOFCRORRIGNPREIISPLISSST
NEWTHEPSANNITATEMBE`. Calibrated the scorer against known-real plaintext (the solved
3.2.2 sentence, 65 chars, scores −262.3, i.e. ~−4.03/char) — the best `dbbi` decode
found scores ~−4.39/char, worse than real English, and reads as noise with only
scattered fragments ("OF", "NEW", "THE"). Zero AES-oracle hits among all candidates
tested.

The strength of convergence (thousands of independent restarts landing on the *same*
key) means this is very likely at or near the global optimum for quadgram fitness in
this search space — so this isn't a case of "didn't search enough," it's a genuine
negative: the best-scoring key under this checkerboard construction still isn't
English. Most likely explanations: (a) `dbbi` isn't a straddling checkerboard over
plain English under this alphabet-construction scheme (`build_board_9ary`'s
topology/escape assumptions may not match the real cipher), or (b) 65 decoded letters
is simply too short for reliable ciphertext-only substitution-key recovery regardless
of compute. This lever is now closed; the riddle-sentence-first approach (or a fresh
external hint) remains the only path back into `dbbi`.

**Update (2026-07-12): sliding-window sweep of all 3 Matrix screenplays as riddle-
sentence candidates — negative.** Motivated by this session's finding that Phase 2/3's
page (`choiceisanillusion...iwroteitmyself`) reuses verbatim Merovingian dialogue, and
by the 3.2.2 precedent riddle ("A fubcd-king & oracle-queen...", 18 words/91 chars) —
tested the hypothesis that the Cosmic Duality riddle might likewise be a **verbatim
15-20-word excerpt** from the trilogy scripts (`wordlists/matrix/*.pdf`, extracted via
`pdftotext -layout`, 80,695 words total). Generated every unique contiguous 15-20-word
window across all 3 scripts (`wordlists/gsmg/matrix_script_windows.txt`, 464,586
candidates) and ran them through `cosmic_sweep_9ary.py`'s standard pipeline (default
`{b,e}` model, `top_first` topology, both `dbbi`/`faed`, primary KDF) — **929,172
keyword-tests in 206s, 0 hits.**

**Caveat that matters more than the negative result**: this only tests "the riddle is
a verbatim script excerpt." The two confirmed real examples (3.2.2's riddle, and Phase
2/3 itself) show the creator doesn't actually do that — he takes **short** (2-8 word)
verbatim fragments and glues them together with his **own original wordplay** (e.g.
inserting "private" before "keymaker" as a pun on "private key"; the `-king`/`-queen`
chess-metaphor tags; the coined word "fubcd"). A blind long-window sweep structurally
can't land on a half-original sentence like that. So this closes off a cheap, worth-
trying hedge — not a meaningful update to the odds that hand-composed riddle-hunting
is still the only real lever. Don't re-run this exact sweep; if extending the idea,
the un-tried step is generating *candidate original riddle sentences* (short quotes +
invented connective wordplay, following the demonstrated pattern) rather than more
verbatim-excerpt window sizes.

**Update (2026-07-13): the un-tried step above was attempted — found and closed a real
tooling gap along the way, but the concrete result is negative, and the exercise
sharpens (rather than removes) the reason to expect this lever is fundamentally
unguessable.**

First, precisely re-derived *how* 3.2.2's riddle sentence maps onto its alphabet, since
the earlier write-up only stated the result. Feeding the riddle's **full raw sentence**
through `pad28()` (strip non-letters, dedupe in first-occurrence order across the whole
string) does *not* reproduce the known-good alphabet — confirmed again here. It only
works if every non-content word (articles, conjunctions, prepositions, and the
`-king`/`-queen` chess-metaphor suffixes) is dropped *first*, leaving just the four
content-bearing tokens ("fubcd", "oracle", "thingky", "mvps") concatenated in sentence
order — that reproduces the real alphabet exactly. **This means every prior sweep that
fed a whole prose sentence (book passages, Matrix script windows, chat lines) through
`pad25()`/`pad28()` as-is was testing a mechanism that structurally cannot reproduce
the real construction rule, independent of whether the sentence's wording was right.**
That gap had never been made explicit or tooled for before this session.

Built `tools/gsmg/riddle_content_words.py` (stopword-filter + concatenate) to close it,
and hand-composed 24 original candidate riddle sentences in the creator's demonstrated
style — short clauses built only from already-verified duality/yin-yang/chess/Matrix
lore (the book's own "seed of its opposite" language, Shiva/yin-yang imagery, the
3.2.2 board/king/queen motif reused with a duality twist, `theflowerblossoms...`,
`choiceisanillusion...`, etc.) — **deliberately using only real dictionary words, not
invented portmanteaus like "fubcd"/"thingky"/"mvps"**, since those are fundamentally
unguessable from any wordlist and there's no way to search for them. Generated 236
candidates total (raw + content-filtered forms of the book pp.8-9 text, the 24 hand-
composed originals, and `matrix_trilogy.txt`) and ran them through the full validated
pipeline:
- Checkerboard decode, `{b,e}` model (both topologies, all 3 tail-fills, 4 drop-letters,
  newline variants): 472 keyword-tests, **0 hits**.
- `faed` under its own two candidate escape pairs (`{g,i}` best-fit, `{h,e}` mirror of
  `dbbi`'s): 472 more keyword-tests, **0 hits**.
- All 236 candidates as direct AES passphrases (bypassing the checkerboard entirely):
  5,922 forms, **0 hits**.
- The full 161-character creator-hint chain (`yellowblueprimes...promised`) tested as
  **one single unified alphabet seed** for the first time (previously only tested in
  disjoint fragments) across every structural hedge (4 drop-letters × 3 tail-fills × 2
  topologies × 3 escape-pair hypotheses × both targets × newline variants): 5,184
  tests, **0 hits**.

**How to apply**: the tooling gap itself (whole-sentence dedup ≠ real construction rule)
is a genuine, reusable finding — `riddle_content_words.py` is available for any future
prose-source sweep. But the concrete outcome sharpens the pre-existing pessimism about
this lever rather than opening it up: 3.2.2's own precedent used coined nonsense
words specifically (not real ones) as its content anchors, and there's no principled
reason to expect the creator switched strategies for the harder, later stage. If that
precedent holds, no wordlist- or lore-based sentence search — content-filtered or not —
can ever succeed here, because the winning tokens were never real words to begin with.
This doesn't prove that's the case, but it's the most likely explanation for why an
increasingly thorough, well-motivated search of this shape keeps coming back empty.

**Update (2026-07-12): "yin-yang" structural hypothesis (halfswap/mirror9 transforms)
— negative.** Confirmed via the fork's chat archive that "yinyang" is a genuine,
creator-endorsed clue (a direct 2023-02-23 creator remark, independently recognized by
the community as pointing at the *Cosmic Duality* book's own theme — duality =
yin-yang), not just an inferred connection. It was already keyword-tested exhaustively
(standalone and combined with `yellowblueprime`/`matrixsumlist`/
`lastwordsbeforearchichoice`, see `wordlists/gsmg/riddle_combinations.txt`) — all 0
hits. To test the *structural* reading of "duality" instead of more keyword variants,
added two new transforms to `cb_common.py`'s `transpose()`: `halfswap` (swap the
string's first/second halves — the two "eyes" of a taiji trading places) and `mirror9`
(complement each a-i symbol around e: a↔i, b↔h, c↔g, d↔f, e fixed — a symbol-level
duality rather than a positional one). Ran both against `dbbi`/`faed`: the full
default dictionary (677,810 keyword-tests, 477s) and the curated GSMG-specific
wordlists (chat-mined words/lines, riddle combinations, Matrix vocabulary, discovered
paths, "last command" candidates, SalPhaseIon's own keywords — 178,126 keyword-tests,
331s). **0 hits, both runs.** `halfswap`/`mirror9` are now permanent additions to
`TRANSFORM_KINDS` (available via `--input-transforms`/`--output-transforms` on future
sweeps) but this specific hypothesis is closed — don't re-run against these same
wordlists.

**Update (2026-07-12, continued): two more "duality" readings, applied to specific
artifacts on the page rather than the payload strings generically — both
negative.** Enumerated how a yin-yang/duality framing could apply to *every* piece of
the SalPhaseIon blob (`dbbi` + abba→`matrixsumlist` + `faed` +
z-seg→`lastwordsbeforearchichoice` + z-seg→`thispassword` + literal
`shabefourfirsthintisyourlastcommand` + AES-blob-with-embedded-abba→`enter` + trailing
`shabefanstoo`), then built and ran the two ideas that were both new (not already
covered by an existing sweep) and cheap:

1. **`faed`'s escape pair = mirror of `dbbi`'s, not an independent frequency fit.**
   `dbbi`'s decisive escape pair is `{b,e}`; under `mirror9` (a↔i, b↔h, c↔g, d↔f, e
   fixed) that maps to `{h,e}`. Ran the curated GSMG wordlists (89,063 candidates)
   against `faed` with `--escapes h,e`: **0 hits, 22s.**
2. **The abba→`enter` embedded in the AES blob as a literal "press-Enter" instruction**
   — i.e. the passphrase should have a trailing `\n`/`\r\n` appended before hashing
   (the `echo "x" | sha256sum` vs `echo -n` gotcha). Added an opt-in
   `newline_variants` parameter to `cb_common.py`'s `keystr_forms()` (triples the
   passphrase forms tried: raw/sha256/sha256² of the base form, the form+`\n`, and the
   form+`\r\n`) and a matching `--newline-variants` flag on `cosmic_sweep_9ary.py`.
   Also directly patched `lastcommand_probe.py`'s curated "last command" candidate list
   (28 literal readings of `shabefourfirsthintisyourlastcommand`) to try all three
   newline variants — negative, 0/168 forms. Then ran the full curated GSMG wordlist
   set (both targets, default escapes) with `--newline-variants`: **0 hits, 178,126
   keyword-tests, 119s.**

Everything else in the artifact-by-artifact duality enumeration was either already
closed by a prior sweep (symbol/positional transforms on `dbbi`/`faed`; the
"matrixsumlist triangle" geometric reading; the mechanical `shabefanstoo` derivations)
or judged too low-plausibility to build (a `shabefanstoo`-as-mirror-echo-of-the-front-
literal reading — lengths don't correspond cleanly). One proposed idea (an odd/even
"riffle" interleave transform) turned out to be mathematically identical to the
existing `col2` transform (`s[0::2] + s[1::2]`), already tested negative at full scale
in the 2026-07-08 generic-transposition sweep — not rebuilt.

**Update (2026-07-12, continued): `dbbi`→`faed` chain hypothesis (the two "eyes" as a
coupled pair, not independent targets) — negative.** Every prior sweep decodes `dbbi`
and `faed` independently, each under its own wordlist keyword. This tests a different
reading: `dbbi` is the small/structured half whose *decoded plaintext* becomes the
keyword that builds the board `faed` (the large/high-entropy half) is decoded with —
new script `tools/gsmg/chain_sweep.py` (candidate → pad25 board → decode `dbbi` → that
plaintext (all `answer_forms()`) → new pad25 board → decode `faed` → `answer_forms()` →
`keystr_forms()` → AES oracle), using `dbbi`'s own decisive escape pair (`{b,e}`, both
orders) at both stages. Ran the curated GSMG wordlists (89,063 candidates, 84s) and the
full default dictionary (338,905 candidates, 315s) — **0 hits, both runs.**
`chain_sweep.py` is now a reusable script for this specific "one target's plaintext
seeds the other's board" hypothesis, but it's closed for `dbbi`→`faed` under `{b,e}`.

**Update (2026-07-12, continued): the book's own most explicit yin-yang page (pp.8-9,
"Harmony from a Divided Universe" sidebar + the mother-of-pearl yin-yang inlay/parti-
colored Shiva images) — transcribed and tested directly, negative.** The 2026-07-12
full-book photo review (see above) was a *visual* anomaly scan (hidden text,
marginalia, planted content) — it never extracted this page's actual prose as candidate
cipher-seed material the way 3.2.2's real riddle sentence was used. This page is the
single most on-the-nose "yin-yang in both picture and text" spot in the entire book, so
it's the natural next candidate even though the full-book scan already came back clean.
Transcribed the full essay/caption text (`wordlists/gsmg/cosmic_duality_book_p8_9.txt`,
36 candidate phrases/sentences, both the pp.8-9 sidebar and the pp.6-7 "Unity of
Opposites" essay it continues from) and tested it two ways:
1. As checkerboard riddle-sentence candidates (`cosmic_sweep_9ary.py`, all
   input/output transforms) against `dbbi` and `faed` under all three escape-pair
   hypotheses considered so far (`{b,e}` default, `{g,i}` faed's own best-fit, `{h,e}`
   the `mirror9` pair) — 36 keyword-tests each, **0 hits, all four runs.**
2. As direct literal AES passphrases (bypassing the checkerboard entirely, the same
   way `shabefourfirsthintisyourlastcommand`'s candidates were tested) — every phrase
   through `answer_forms()` × `keystr_forms(newline_variants=True)`, **0 hits out of
   1,620 forms.**
Closes out this specific page as a lead under every mechanism this project has for
turning text into a candidate. The rest of the book (index entry, other essays,
Chapter 1 "Dualities As Old As Time") remains only visually reviewed, not
content-extracted this way — a possible next step if this angle is revisited.

**Update (2026-07-12, continued): "yin-yang = the puzzle looping back to phase 0"
hypothesis — the real connection already exists and is already tested; the specific
untested sub-idea (a hidden 3rd color channel) doesn't hold up on inspection.**
`follow_the_white_rabbit.png`'s black/white channel decodes to `theseedisplanted`
(phase 1's URL). Its blue/yellow squares are commonly *associated* with the keyword
`yellowblueprime` (first of the four chained keywords ending in `...yinyang...`), and a
community member independently stated the parallel ("since theseedisplanted was solved
using binary black&white, the next clue is YIN-YANG blue-yellow"). **Correction: that
association is weaker than my initial phrasing implied** — `yellowblueprime` was
actually extracted from the reversed-binary message on the *SalPhaseIon* page, a
different location entirely; the community never conclusively derived it back out of
this grid image. Direct quotes spanning years: *"I believe I have the solution for
yellowblueprimes... I just have no idea where to apply it"* (2023-09-26), *"now yellow
blue prime is already solved leaving us trying how to get the word 'yellowblueprimes'
from dbbi"* (2023). One person even argued it's not a derivable string at all —
*"yellowblueprimes = the picture"*, i.e. a pointer back to "go re-examine this image,"
not a specific extraction. So the "first phase and current phase are the same duality
trick, reapplied" reading is plausible but unconfirmed, not established fact. The
keyword itself, combined with the other three, has still been exhaustively swept
against both targets (`riddle_combinations.txt`), and `theseedisplanted`/
`followthewhiterabbit` standalone are both in the default dictionary that already got
the full 677,810-test sweep. All negative regardless.

**Update (2026-07-13): exact characterization of the blue/yellow diagonal placement —
confirmed precisely, but the fine-grained selection rule stays unresolved.** Extracted
the actual 14×14 color grid from `follow_the_white_rabbit.png` and confirmed: **all 24
blue/yellow cells satisfy `(row − col) ≡ 3 (mod 4)`, with zero exceptions** — one
specific diagonal family out of 4 possible, more precise than any existing chat
reference (closest: a 2024-11-14 message tracing a spiral-step-7 path that "hits yellow
and blue" at certain diagonals, same underlying regularity via a different method,
never formalized). That diagonal family has 49 cells total, of which only these 24 are
colored — so lying on the diagonal is necessary but not sufficient. Tried to find the
finer selection rule two ways, neither produced a clean match:
1. **Index-based**: primality of row, column, row+col, and four different linear-index
   schemes (raster order, column-major order, position-within-the-diagonal-family,
   position-within-one-diagonal-line), 1- and 0-indexed — best result was noise-level
   (~50% match), no scheme cleanly separated colored from uncolored cells.
2. **Content-correlation**: aligned the 24 colored cells (in 4 traversal
   orders × forward/reversed) 1:1 against the 24 characters of `gsmg.io/theseedisplanted`
   (24 cells = 24 characters — itself a real, exact count match worth keeping in mind),
   checked whether blue-vs-yellow correlates with each character's ASCII-value
   primality or LSB parity — best was 16/24, also chance-level.
Matches the community's own multi-year inability to resolve this. The mod-4
characterization itself is a genuine, reusable, more-precise-than-prior-art fact; the
"why these 24 of 49" question is a real open gap, not one this session closed.

**Update (2026-07-13): the "why these 24 of 49" gap is now fully closed — tautological,
not a hidden signal.** Built `tools/gsmg/grid_spiral.py`, an independently-verified
implementation of the community's documented reading rule ("start from upper left square
and go counterclockwise in a spiral," from the fork's `README.md`), using the corrected
bit rule also stated there but not previously applied in this project's own extraction:
**black/blue cells = bit 1, white/yellow cells = bit 0** (blue and yellow are colored
*variants* of black and white, not a separate channel). Brute-forced all 8 corner/
chirality combinations to confirm exactly one (start top-left, first move down, turn
left/CCW) reproduces `gsmg.io/theseedisplanted` byte-for-byte from the raw pixels (own
fresh extraction, not the README's hand-transcribed matrix — which itself differs from
this pixel-verified one by exactly the same single cell flagged in this doc's Stage-0
section, row 8/1-indexed, confirming that was a transcription slip, not an extraction
bug on our side).

With the correct spiral pinned down: **the 24 blue/yellow cells are exactly the spiral
positions `i % 8 == 7`** — i.e. the last (least-significant) bit of each of the 24
decoded ASCII characters — **and the color at each one exactly equals that bit's value**
(blue = 1 = odd ASCII, yellow = 0 = even ASCII), with zero exceptions across all 24.
Verified this reproduces the previously-found `(row-col) % 4 == 3` diagonal exactly, as a
byproduct of the spiral's geometry landing every 8th step on that diagonal family — not
an independent selection rule layered on top.

**Correction (2026-07-25): the colored positions carry no additional positional
information, but the color polarity does carry creator-clued semantic information.**
The 24 colors in the already-validated spiral order are
`BBBBYBBBYYBBBBYBBYYBYYBY`. Reading blue=1/yellow=0 gives
`111101110011110110010010` = **`0xF73D92`**, an RGB rose/pink color
`(247,61,146)`, matching the creator's opening “Roses…” line. Reversing the two
color values gives `000010001100001001101101` = **`0x08C26D` = `574061`**,
which is prime. The order was fixed independently by the known
`gsmg.io/theseedisplanted` decode before either property was tested, so this is
not a traversal search fitted to primality. `tools/gsmg/first_piece_color_
reconstruction.py` reproduces the result directly from the archived PNG and
asserts every intermediate.

Thus `yellowblueprime` now has a concrete, exact reconstruction: the same 24
yellow/blue cells provide two complementary numbers, one rose-colored and the
other prime. The earlier statement that this was “not a hint pointing to
anything else” was too strong. What remains unresolved is how `574061` (and
possibly `F73D92`) feeds the next creator-authored instruction,
`matrixsumlist`; this result does not by itself open `dbbi`/`faed`.

**Update (2026-07-13): verified the creator's 2023-02-23 binary hint from raw bits (not
just trusting the community's transcription), then ran a known-plaintext ("crib")
attack against `dbbi`/`faed` using it — new technique, still negative.**

Independently re-decoded the creator's `00100110 10100110...` binary chat message from
scratch: 1288 bits, 161 bytes, reverse-whole-bitstream (the documented trap for this
puzzle's binary messages — per-byte reversal gives garbage, whole-stream reversal is
required) gives exactly `yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang
wewontgiveawaythepassworditsinfrontofyoureyesbutyourenotseeingitverylaststepisatruegive
awaypromised` (161 chars, matching the byte count exactly — no leftover bits, no hidden
extra data). Checked surrounding context in `creator_jrk.txt`: preceded by the creator
disclaiming an unrelated community joke thread ("I'm staying out of this one"), followed
8 days later by a solitary 🐰 emoji — thematically consistent with `yellowblueprime`
pointing at the rabbit image, but not confirmation of anything.

A community member claimed *"dbbi is a good match for yellowblueprimes... faed is a
good match for the yinyang... string... both encrypted strings are roughly 5 times
larger than the plaintext."* Checked quantitatively: `yellowblueprimematrixsumlist` (29
chars) vs `dbbi` (91 symbols) = 3.14×; the remainder (132 chars) vs `faed` (570 symbols)
= 4.32×. Same order of magnitude but not a consistent ratio, and a straddling
checkerboard can only expand text 1-2× (7 single-symbol + 18 double-symbol codes per
letter) — so if either fragment really is embedded, it can only be a *partial* crib
inside longer plaintext, not the whole thing.

That reframes the whole hint as a **known-plaintext attack target** rather than another
keyword guess. Built `tools/gsmg/crib_drag.py`: for a fixed escape pair, `decode_9ary`'s
1-vs-2-symbol segmentation of the raw ciphertext depends only on which characters equal
`e1`/`e2`, not on the alphabet — so a hypothesized plaintext crib's *letter-repetition
pattern* must exactly match the *code-repetition pattern* of some contiguous run of
codes, with zero knowledge of the actual substitution alphabet required. Verified the
matching logic against a synthetic encode/decode round-trip before trusting it (found
the correct single match with the correct forced code→letter mapping). Ran every
information-rich crib (`yellowblueprimesmatrixsumlist` + variants/reversal against
`dbbi` under `{b,e}`; the full tail phrase + several sub-phrases + reversals against
`faed` under all three escape-pair hypotheses `{b,e}`/`{g,i}`/`{h,e}`) — **zero matches,
any target, any escape pair.** (Short/low-repetition words like "yellow" or "password"
did produce dozens of matches each, but that's chance noise from weak constraints, not
signal — excluded from the final candidate list after confirming this.)

Net: the creator hint's own text is now independently verified byte-for-byte, and the
"embedded crib" reading of it has been tested with a fundamentally different and more
rigorous technique than keyword-guessing — still negative. `crib_drag.py` is a reusable
tool for testing any future crib hypothesis this way.

Checked the one piece of this that looked genuinely untested: whether the image has a
*third* hidden duality channel (paralleling black/white and blue/yellow), motivated by
chat mentions of a "5th color." Directly inspected the image
(`gsmg-site-mirror/img/follow_the_white_rabbit.png`, 350×350, 14×14 grid of 25px
cells) — confirmed exactly 5 distinct RGB values, but the "5th" (`(254,254,254)`, near-
white) is confined to **exactly one cell** (row 7, col 4 — 625 pixels = one cell
exactly), not a parallel bitstream. There's no room for a third full channel; the
hypothesis doesn't hold structurally once actually measured. This single-cell anomaly
("FEFE", by its hex nickname) is itself multi-year, well-documented community lore,
including one exchange explicitly linking it to "it's in front of your eyes" — never
resolved. The literal string `fefe` is already in `chat_mined_words.txt`, part of
nearly every curated sweep run this session — already tested against both targets,
negative.

**Update (2026-07-12, continued): the full `puzzle.png` (grid + red bar + QR code +
branding, 1048×1556 — the actual `gsmg.io/puzzle` raw image, recovered from the
community fork's repo and copied into the local mirror as `puzzle_raw.png`) — the red
bar and the QR code, both checked, both clean.**
- **Red bar** (15px strip directly under the grid): solid `(237,28,36)` except a
  1px-wide white column at the image's literal right edge (x=1047, all 15 rows) — a
  trivial rendering-boundary artifact, not a planted pattern.
- **QR code**: installed `opencv-python-headless` (no system zbar available) and
  decoded it directly — `https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`,
  matching the printed address exactly. Standard Version 4 (33×33 modules), decodes
  cleanly, appropriately sized for the URL length.
- The community found and argued about a real anomaly here back in **May 2020**: near-
  black pixels (`151515`/`161616` instead of `000000`) in the QR's finder-pattern
  squares, never conclusively resolved (one member, nieods, guessed "QR generation
  artifact" and reproduced it in an online generator, but this wasn't independently
  confirmed at the time). Re-verified directly against the actual image: found 252
  such pixels (`(15,15,15)`/`(16,16,16)`, matching their reported values almost
  exactly), but mapped their exact positions — they form perfectly straight,
  single-pixel-wide vertical lines along the left/right edges of **all three** finder-
  pattern squares, symmetrically (x=1/43 for the top-left and bottom-left patterns,
  x=183/225 for the top-right one). That's the signature of an image-scaling/
  anti-aliasing seam, not a planted marker (a real marker wouldn't be uniform across
  all three otherwise-identical finder patterns). Confirms nieods' 2020 guess with
  actual measurement. Both closed, nothing hidden in either.

**Update (2026-07-13, continued): fresh candidate variants of
`yellowblueprimesmatrixsumlist` — also negative, 100 checkerboard-tests + 567 direct
AES-passphrase forms.** Beyond the crib-drag attempt above, generated a focused set of
candidates not already covered by `riddle_combinations.txt` (which only had all-4-words
combos, never `yellowblueprime`+`matrixsumlist` alone): word-order permutations,
underscore/hyphen/camelCase separator variants (`wordlists/gsmg/
yellowblueprime_matrixsumlist_variants.txt`), and concrete numeric candidates derived
directly from the grid's blue/yellow cell positions (linear indices 0- and 1-based,
their prime subset, digit-concatenations, and sums — computed from the same pixel
extraction as the mod-4 diagonal finding above). Ran all 25 candidates through
`cosmic_sweep_9ary.py` (all transforms, `--newline-variants`) against `dbbi` and `faed`
under all three escape-pair hypotheses (100 keyword-tests) and directly as literal AES
passphrases (`answer_forms()` × `keystr_forms(newline_variants=True)`, 567 forms) —
**0 hits, everywhere.** The prime-subset of blue/yellow linear indices was small and
unconvincing on its own (2-4 primes out of 24 cells depending on indexing), consistent
with the mod-4-diagonal update's finding that no simple indexing scheme cleanly
explains the cell selection — this doesn't newly refute that, just adds one more
concrete (if low-confidence) numeric derivation to the already-tested pile.

**Update (2026-07-24): raw page-structure path resolved.** Added
`tools/gsmg/page_structure_audit.py` and verified the archived HTML directly. The
SalPhaseIon textarea is one 1,075-character logical stream with one space between
characters and **no authored newlines**, so its screenshot rows are browser soft-wraps
and not usable geometry. The Cosmic textarea is deliberately hard-wrapped as 28 lines
of 64 Base64 characters. Most notably, the abba-encoded `enter` marker splits the
small SalPhaseIon AES blob into two exact 64-character halves. This strongly identifies
`enter` as an in-band line-break instruction restoring the author's Base64 format,
rather than evidence for appending a newline to the password. Removing it reproduces
the already-known valid OpenSSL `Salted__` blob, so this clarifies the page grammar but
does not provide a new decryption key. Exact offsets and the reproducible command are
recorded in [doc/GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md](GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md).
