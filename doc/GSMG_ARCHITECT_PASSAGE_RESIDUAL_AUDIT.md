# GSMG Architect-Passage Residual Audit

Phase 235 closes three small, bounded items left open by the Phase 3.2.1
brainstorm thread (Phase 118, 232-234): where the custom passage's wording
actually traces to (screenplay vs. film), whether `key`/`note`/`self`/
`keynote` have real test coverage, and whether the creator ever commented on
this specific passage's tone. It does not reopen any closed hypothesis.

Reproduce it with:

```bash
python3 tools/gsmg/architect_passage_residual_audit.py --self-test
```

## Screenplay-vs-film provenance

Two content words in the custom passage trace to the **screenplay draft**,
not the film soundtrack:

- `...ALLOWING A TEMPORARY DISSEMINATION OF THE CODE...` — the screenplay PDF
  reads "a temporary dissemination of the code you carry"; the film's actual
  line (SRT) is "allowing a dissemination of the code you carry", no
  `temporary`.
- `...WILL ULTIMATELY RESULT IN THE EXTINCTION...` — the screenplay reads
  "will ultimately result in the extinction"; the film's line is "will result
  in the extinction", no `ultimately`.

One word-order choice traces the other way:

- the puzzle reads `...THE FUNCTION OF THE YOU IS NOW TO RETURN TO THE SOURCE
  CODES...`, matching the film's "is now to return"; the screenplay instead
  reads "is to now return".

The creator's wording is therefore not uniformly sourced from either fixed
document. This is consistent with recollection blended from both the
screenplay and the film, not evidence of a single pinned source text, and
fits the already-established two-sloppy-days construction (Phase 230). It
does not revive the source-reinsertion hypothesis, which failed stability
under exactly this kind of screenplay/film divergence.

## KEY / NOTE / SELF / KEYNOTE coverage

None of `key`, `note`, `self`, or `keynote` appear in the GSMG-specific
curated wordlists (`phrases.txt` etc.), but all four are ordinary dictionary
words present in `/usr/share/dict/american-english`, one of Phase 2's default
`cosmic_sweep.py` wordlists. They were therefore already tested as
checkerboard keywords (`pad28 -> decode(dbbi/faed) -> AES try`, SALPH+COSMIC
only) as a matter of course. None had ever been tested as a literal direct
blob password, and the literal contiguous run `selfself` (from the
authenticated `...yourselfselfgoodluck...` letter stream) had no coverage of
any kind.

A bounded direct-password check (the same 18-keystring-form pattern used in
Phases 232 and 234) for all five forms against all four tracked blobs:

```text
90 keystrings x 4 blobs, 0 hits
```

## Creator commentary on passage tone

Searched both creator export corpora for `architect`, `3.2.1`, and `matrix
text`: **zero hits in either corpus.** The creator never references this
passage by name or description anywhere in either export.

A wider search for `joke`, `kidding`, `dramatic`, `theatric*`, `exaggerat*`,
`parody`, and `caricature` turns up 18 distinct creator messages across both
corpora, all inspected directly and all unrelated on inspection (a personal
safety aside, ASCII trivia, IT jokes, a joked-about bitconnect promo-video
parody idea, and similar). None concerns the Architect text, brute-forcing
language, or the cipher-count threat.

The "theatrical misdirection" reading from the brainstorm report therefore
remains an inference from the creator's *general* anti-bruteforce guidance
(Phase 226/230), not a documented statement about this specific passage.

## Verdict

The provenance split is a real, verified texture but not a password or
operand. The KEY/NOTE/SELF/KEYNOTE family's direct-password gap is now
closed and negative. The theatrical-misdirection reading is correctly
labeled as inference, not creator confirmation. No decoder, autokey, or new
blob-oracle branch is authorized.
