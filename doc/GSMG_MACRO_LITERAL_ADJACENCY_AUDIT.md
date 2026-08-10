# GSMG Macro Literal-Adjacency Audit

## Question

Does the simplest reading of the creator-confirmed visibility clause reveal a
password or referent through literal source order alone?

Phase 231 uses the byte-exact 161-character creator macro and both word
segmentations already registered by the acrostic audit. It permits only:

- unique contiguous anchors;
- characters between anchors;
- immediate preceding/following words;
- the literal final fragment.

It does not run a password, cipher, or blob oracle.

## Raw adjacency

The exact local source is:

```text
...thepassworditsinfrontofyoureyesbutyourenotseeingit...
```

Mechanical spans give:

```text
after password, before youreyes:  itsinfrontof
after password, before eyes:      itsinfrontofyour
immediately before youreyes:      of
immediately after youreyes:       but
after truegiveaway:               promised
```

`but` occurs exactly once. Neither `hye` nor `hyebut` occurs in the macro.

## Word-level controls

Both the compound `giveaway` and split `give away` segmentations agree around
the relevant clause:

```text
the -> password -> its
your -> eyes -> but
eyes -> but -> youre
between password and eyes: its / in / front / of / your
literal three-word sequence: your / eyes / but
initials: YEB
```

Thus literal adjacency independently strengthens the already-real `BUT`
boundary: it appears immediately after `your eyes`. It does not produce HYE.
Recovering `H | YE | BUT` still requires importing the known HYE target and an
unselected initials/splitting rule, exactly the circular construction removed
in Phase 217.

The final fragment is deterministically `promised`, but that is existing
coverage: its standalone direct-password family was already tested negative.

## Verdict

The shortest literal reading is informative but not a solution. It confirms
two visible boundary facts—`BUT` after the eyes phrase and `PROMISED` last—yet
the text around `password` contains only the grammatical statement that the
password is in front of the reader. It supplies no non-placeholder password
value and no independently fixed consumer.

No oracle expansion is authorized. Reopen this branch only if another primary
artifact specifies how many characters/words “in front” selects or identifies
the object to which the pointer refers.

## Reproduction

```bash
python3 tools/gsmg/macro_literal_adjacency_audit.py --self-test
python3 -m unittest tools/gsmg/test_recent_audits.py
```
