---
type: audit
phase: 232
date: 2026-08-10
status: partial
disposition: recognition-only
topics:
  - architect
  - macro-chain
  - bye
related_phases:
  - 216
  - 217
  - 233
  - 234
  - 236
script: tools/gsmg/architect_hye_bye_audit.py
aliases:
  - Phase 232
---

# GSMG Architect HYE → BYE Audit

## Result

The full endings rail has a compact consequence that earlier audits missed:

```text
HYE
mirror a-i symbols, preserve outside symbols
BYE
```

Under the already-established nine-symbol involution, `H → B`, `E → E`, and
the out-of-alphabet `Y` passes through unchanged. This uses the full rail
rather than discarding `Y`.

## Controls

The operation was calibrated over every ordered triple of word positions that
is identical in the film and screenplay sources. Among the 48 triples whose
initials spell `BUT`:

```text
distinct partial-mirror finals: 18
dictionary-output rows:          5
distinct dictionary outputs:     BYE only
exact BYE rows:                   5
```

The five rows all have literal finals `HYE`; repeated occurrences come from
the same `BOTH / ULTIMATELY / THE|THERE` word identities at multiple stable
positions. Across all 35,904 ordered stable triples, 36 produce transformed
finals `BYE`. The independently fixed `[23,16,7]` row is one of the five `BUT`
rows.

Permuting the three fixed positions gives six transformed outputs. Only the
authored `[23,16,7]` order produces a dictionary word.

## Evidentiary limit

`BYE` is a strong recognition candidate, not proof that yin-yang has been
mechanically reached. Two conventions remain unauthenticated:

1. preserve `Y` while applying mirror9 only to `a–i` symbols;
2. transform the non-English endings rail while retaining the independently
   validated beginnings rail `BUT`.

The page’s phrase `your last command` gives `BYE` a natural termination
association, and the authenticated Phase 3.2.1 plaintext ends `CIAO BELLA O`.
Neither fact explicitly selects this operation or a command environment. The
creator’s 2026 goodbye was an ordinary sign-off before the extraction and is
not treated as confirmation.

## Bounded oracle

Because `BYE` is the sole dictionary result in the complete 48-row control,
the audit admits one exact candidate family: raw, SHA-256, double-SHA-256,
case, LF, and CRLF forms already defined by the project. No new cipher mode or
wordlist was introduced.

```text
candidate:       BYE
keystrings:      18
tracked blobs:   4
CBC/ECB/stream/Key-Wrap hits: 0
```

## Verdict

Retain `HYE → BYE` as the strongest new full-rail recognition result. It
explains the awkward `Y` more economically than discarding it and survives a
useful control, but the operation’s polarity/pass-through convention is not
creator-authenticated and its bounded password family is negative. It does not
yet open FAED, DBBI, SALPH, or another blob.

```bash
python3 tools/gsmg/architect_hye_bye_audit.py --self-test
python3 -m unittest tools/gsmg/test_recent_audits.py
```
