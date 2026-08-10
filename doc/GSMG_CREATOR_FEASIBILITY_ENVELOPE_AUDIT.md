# GSMG Creator Feasibility-Envelope Audit

Phase 226 verifies the creator statements commonly paraphrased as “offline,”
“already in front of us,” “moderate brute force,” and “built in a couple of
days.” The audit uses the complete Telegram export and separates exact claims
from stronger recollections.

Reproduce it with:

```bash
python3 tools/gsmg/creator_feasibility_envelope_audit.py --self-test
```

## Verified constraints

- Message 16624 asks whether internet is still required “given the available
  knowledge”; the creator answers `Nope`.
- Message 9607 directly replies to a request for another URL with `No need.
  You have all the info.`
- Message 9639 distinguishes solving from claiming: internet is technically
  needed only to claim the prize at the end.
- The reversed-binary macro contains `itsinfrontofyoureyesbutyourenotseeingit`.
  In messages 60309–60312, the creator points at a user who repeats only that
  phrase and then answers `Bingo`. This confirms the phrase, not a particular
  book or artifact.
- Message 32579 says one further “microstep” would likely lead to same-day
  completion. This constrains work after the missing transition; it does not
  say the missing microstep is easy.

Together these favor an already-present, offline-reproducible operand or
structural realization. They reject a necessary new URL or broad web search.

## Claims not reproduced

There are zero creator-authored `brute`/`bruteforce` mentions in the complete
export. The word appears in community questions and computations, including
the question to which “You have all the info” replies, but the creator does not
endorse moderate brute force as the intended method.

The creator does describe the puzzle as a spur-of-the-moment idea and says he
can enter a frenzy where a day later he barely understands what he did
(messages 66559 and 66561). Earlier messages also call mistakes rushed. But no
creator message says the puzzle was completed in one day, two days, or “a
couple of days.” The rapid-construction evidence is qualitative, not a duration
bound, and does not establish a maximum number of layers.

## Search policy

A new branch should require authenticated/already-present operands, offline
reproducibility, and either an explicit binding or a rare controlled structural
match. Do not admit a brute-force family based on a nonexistent creator
endorsement, and do not discard a layered reading solely because of an
unstated two-day construction claim.
