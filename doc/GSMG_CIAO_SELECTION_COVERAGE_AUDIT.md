# GSMG CIAO Selection-and-Coverage Audit

> **Phase-237 closure note:** the checkerboard-keyword gap this historical
> Phase-234 report leaves open for P32TRAILING/URLBLOB is now closed and
> negative for the combined CIAO/BELLA/BYE and KEY/NOTE/SELF families. See
> `GSMG_CHECKERBOARD_KEYWORD_BLOB_GAP_AUDIT.md`.

Phase 234 asks two narrow questions about the `HYE -> BYE -> CIAO BELLA O`
recognition chain (Phases 232-233): did the creator ever select this reading,
and which CIAO/BELLA-family candidates are actually untested? It replaces an
earlier, over-broad `BELLA -> {b,e}` reading with a disciplined coverage
census. It does not index song lyrics against `[23,16,7]` and does not launch
an autokey/chain-addition sweep.

Reproduce it with:

```bash
python3 tools/gsmg/ciao_selection_coverage_audit.py --self-test
```

## Why the `{b,e}` reading was withdrawn

Filtering `BELLA` to the page's native `a-i` alphabet gives three distinct
letters, `bea`, not a pair. Picking `{b,e}` out of the three because it
happens to match DBBI's already-known best pair (rank 1/36 by code-IC, fixed
many phases ago) is a post-hoc selection, not a mechanical two-letter output.
It is not a third independent convergence and is not used below.

## Two-corpus creator search

Phase 233 searched the puzzle-solvers export only. This phase adds the
support-group export (Phase 230's pinned second corpus) and widens the term
list to `ciao`, `bella`, `bye`, `goodbye`, `yin`, `yang`, `yinyang`, and
`password`.

Already-established hits are unchanged:

- solver export: three ordinary `ciao` sign-offs (`9632`, `32773`, `66609`);
- solver export: two plain `ying yang` mentions (`9599`, `39224`, Phase 225).

The wider search surfaces four additional hits, all irrelevant on inspection:

| Message | Corpus | Text | Why it doesn't count |
|---|---|---|---|
| `4272` | solver | `/goodbye off` | bot command, not a farewell |
| `66909` | solver | BIP 360 wallet explainer | unrelated trading content |
| `58072` | support | "Bye bye scammer c*nt" | dismissal of a scammer |
| `52876` | support | "used the correct password?" | ordinary account-support question |

The support-group export contributes **no** new `ciao`, `bella`, or
`yin`/`yang` mention at all. The creator-selection gate remains closed on
both corpora.

## Coverage census

| Candidate | Checkerboard keyword (`pad28`) | Direct blob password | Autokey/chain-addition seed |
|---|---:|---:|---:|
| `ciao` | no | no (until this phase) | no |
| `bella` | no | no (until this phase) | no |
| `ciaobellao` | **yes** | no (until this phase) | no |
| `obellaciao` | no | no (until this phase) | no |
| `bellaciao` | no | no (until this phase) | no |

`ciaobella`/`ciaobellao` were already tested as checkerboard keywords twice:
once in the Phase-2 dictionary sweep (`cosmic_sweep.py`'s default wordlist
includes `wordlists/gsmg/phrases.txt:34-35`; real `pad28 -> decode -> AES`
oracle against **SALPH and COSMIC only**, since P32TRAILING/URLBLOB were not
yet tracked), and once directly in `alphabet_hypothesis_check.py:31`, which
checks `pad28(candidate) == ALPHA_322` and finds no match. The other three
candidates never appear as a standalone entry in any tracked wordlist or
script; they only exist embedded inside long chat-mined sentence blobs, which
were never fed through a decoder.

None of the five candidates had ever been tested as a literal direct blob
password (the same bounded pattern Phase 232 used for `bye`) before this
phase.

## Bounded direct-password check (genuinely missing coverage only)

Ran the Phase-232 pattern — `answer_forms` + `keystr_forms` (18 keystring
forms per candidate: raw, `SHA256`, double-`SHA256`, newline variants) against
CBC, ECB, stream, and Key Wrap AES routes — for all five candidates against
all four tracked blobs (SALPH, COSMIC, P32TRAILING, URLBLOB):

```text
90 keystrings x 4 blobs, 0 hits
```

This closes the direct-password gap cleanly and negatively.

## Explicitly not run

- **Song-lyric indexing under `[23,16,7]`.** Those indices are bound to the
  Architect passage by the macro's literal `lastwordsbeforearchichoice`
  token. There is no equivalent creator instruction binding them to *Bella
  Ciao*, which also has multiple verse versions. Doing this now would be
  post-hoc.
- **Autokey/chain-addition seeding.** "Keyword" alone is too broad a
  specification; this needs a frozen algorithm and normalization convention
  before it can be run as a bounded test, not attempted here.
- **Checkerboard-keyword route against P32TRAILING/URLBLOB.** The Phase-2
  sweep that covers `ciaobella`/`ciaobellao` predates those two blobs. This
  residual gap is flagged, not closed.

## Verdict

Neither creator corpus selects CIAO or BYE as the yin-yang state, and the
support-group export adds nothing new. The `{b,e}` semantic argument for
`BELLA` does not survive scrutiny and is withdrawn. Of the five candidates,
only `ciaobella`/`ciaobellao` had prior coverage (checkerboard keyword,
SALPH+COSMIC only); the rest had none. The newly-run bounded direct-password
check is negative across all five candidates and all four blobs. No password,
decoder, or autokey oracle is authorized beyond what is documented here.
