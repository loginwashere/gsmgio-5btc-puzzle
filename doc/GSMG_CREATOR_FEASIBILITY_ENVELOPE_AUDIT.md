# GSMG Creator Feasibility-Envelope Audit

> **Phase-230 correction:** Phase 226 called the puzzle-solvers export
> “complete,” but it was complete for only one Telegram chat. The corrected
> audit requires both that export and the separate complete public support-group
> export. This changes the construction-time and brute-force inventories.

Reproduce it with:

```bash
python3 tools/gsmg/creator_feasibility_envelope_audit.py --self-test
```

## Pinned corpus scope

The audit refuses to run if either source changes:

| Chat | Messages | ID | SHA-256 of `result.json` |
|---|---:|---:|---|
| `GSMG Puzzle Solvers` | 57,729 | `1166734859` | `09fa513506ded392d56894424f6e019297781d8d669c27c3c0e9f62f3a31a084` |
| `GSMG - Community & support group` | 52,851 | `1246576180` | `6e616bfe72d81c9d9134c0631781b594d9abf9bc7d2f6de3518f9e75b5dad9fd` |

The support source is specifically
`ChatExport_2026-07-29 (2)/result.json`, the largest of three differently
sized snapshots. It contains 5,419 creator-authored records. Pinning its file
hash, group identity, total count, and creator count prevents a smaller
snapshot or later re-export from silently changing a negative inventory.

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
  say recovering that transition is easy.

Together these favor an already-present, offline-reproducible operand or
structural realization and reject a necessary new URL.

## Two sloppy construction days: verified retrospectively

Support-group message 67741 is creator-authored and dated 2026-04-13. In a
farewell/origin retrospective it says JRK was inspired by other crypto puzzles
and spent “two sloppy days” throwing one together, with grammatical mistakes
and zero polish. The following sentence says that puzzle is still running,
fixing the referent as the unsolved 5 BTC puzzle.

This is first-party evidence, but it is a **2026 retrospective**, not a
contemporaneous 2019 construction log. It supports prioritizing short,
clue-selected mechanics and tolerating implementation mistakes. It does not
mathematically cap the number of layers or prove that every irregularity is a
clue.

## Brute-force inventory

The puzzle-solvers chat contains zero creator-authored brute-force matches.
The complete support-group export contains exactly three:

| ID | Context | Classification |
|---:|---|---|
| `12697` | iCloud security anecdote | Unrelated |
| `28703` | Changing puzzle tokens made testing difficult; creator says protection was needed against brute-forcing and to find the right next hint | Puzzle-specific, explicitly anti-bruteforce |
| `54419` | Trading-bot historical-price backtest | Unrelated |

Message 28703 has no Telegram reply edge. It immediately follows messages
28699/28701 about alternating tokens and difficulty testing. Message 28704—not
28703—directly replies to the adjacent “how many stages?” question at 28702.

Therefore “zero creator brute-force mentions” was false across both chats, but
the important operational conclusion survives more strongly: there is no
creator endorsement of moderate endgame brute force. The only puzzle-specific
use describes an anti-bruteforce mechanism and points solvers toward the right
hint.

## Presentation-vocabulary inventory

Phase 230 also formalizes the source check requested after the responsive-wrap
audit. Across all creator records in both pinned corpora, the frozen vocabulary
includes screen/display/monitor, resolution/width/resize/zoom/wrap,
line-break/newline/row/column, scroll/textarea/font/monospace, browser/window,
mobile/desktop, layout, and alignment forms.

It returns 27 messages: two in the puzzle-solvers chat and twenty-five in the
support chat. The two puzzle-chat matches are `display of words` in the typo
disclaimer (1806) and `monitor the puzzlers progress` using *monitor* as a verb
(6497). All twenty-five support-chat matches concern the trading product, devices,
browsers, database layout, or ordinary conversation.

Result: zero creator puzzle instructions select resizing, wrapping, rows,
columns, viewport, font, textarea, zoom, or screen geometry. This is a bounded
vocabulary negative, not proof that responsive layout is impossible. It means
the historical 45-column screenshot remains a community viewport unless new
primary evidence fixes a presentation parameter.

## Search policy

A new branch should require authenticated/already-present operands, offline
reproducibility, and either an explicit binding or a rare controlled structural
match. Prefer short, locally selected mechanics; tolerate rough implementation.
Do not admit a brute-force family based on a nonexistent endorsement, or a
responsive grid without a creator-selected geometry or read rule.
