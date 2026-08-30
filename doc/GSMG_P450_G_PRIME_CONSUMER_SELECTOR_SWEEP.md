---
type: audit
phase: 450
date: 2026-08-29
status: complete
result: remains_unconsumed
disposition: parked
script: tools/gsmg/phase450_g_prime_consumer_selector_audit.py
---

# Phase 450 — G-PRIME-001 Consumer/Selector Sweep

## Question

Does any evidence already authenticated in this repository, or newly
recoverable from the complete Telegram export by a bounded pre-registered
search, supply a consumer for the fitted prime sums `401/400/73`, an
independent selector for the winning Roman-rail construction
([GSMG_ROMAN_RAIL_PRIME_SUM_AUDIT](GSMG_ROMAN_RAIL_PRIME_SUM_AUDIT.md)), or
an account of FEFE's fitted sum `73`?

Protocol:
[Phase 450 G-PRIME-001 Consumer-Selector Sweep Protocol](Brainstorms/2026-08-29%20-%20Phase%20450%20G-PRIME-001%20Consumer-Selector%20Sweep%20Protocol.md).

## Check 1 — naive extension of the winning rule to FEFE

The winning rail configuration applies one rule with no per-token choice:
project onto canonical Roman letters, then prefix the title's `C`. Applying
that exact rule to FEFE itself (no new decision):

```text
roman(FEFE) = ""          (F and E are not Roman-numeral letters)
C + ""      = "C" = 100
```

`100 != 73`. The winning rule, extended to FEFE with no new choice, does not
reproduce FEFE's fitted sum. This sharpens Phase 263's "FEFE/73 remains
unexplained" into a checked negative: the specific mechanism that produces
401/400 does not also produce 73 without inventing a different rule for the
third token.

## Check 2 — Telegram corpus sweep

A fixed, pre-registered sweep of the complete export (55,963 non-service
messages) for:

- both target Roman forms `CDI` and `CD` as standalone tokens in the same
  message: **0 hits**;
- the phrase `roman numeral(s)` or `title initial`: **2 hits**, both
  unrelated and non-creator — id `36711` speculates about a different clue
  entirely ("Probably there is not letter, there is Roman numeral one"), and
  id `50210` discusses ROT-cipher arithmetic ("100 is roman numeral C : 100
  rot-22 zero-based index"), neither mentioning DBBI, FAED, the title, or the
  fitted sums;
- all three standalone target numerals `401`, `400`, `73` in one message:
  **2 hits**, both non-creator and both coincidental — id `11756` is a
  generic pasted prime-number reference table (1–700) that necessarily
  contains most three-digit primes including all three targets, and id
  `11771` is an unrelated community member's own letter-position frequency
  count over the raw FAED stream (unconnected to the recovered guide's prime
  lists or the Roman-rail construction).

No hit is creator-authored or has a creator reply. Full text of every hit was
read in full, not summarized past its content.

## Verdict

`remains_unconsumed`. No consumer for `401/400/73` together, no independent
selector for Roman-letter projection or title `C`, and FEFE's `73` is now
checked-negative under the one mechanism that would otherwise be the natural
candidate to explain it. `G-PRIME-001` stays parked at P2, unchanged from
`GSMG_OPEN_GAP_REGISTRY.md`.

This does not mean no consumer or selector could ever exist — only that none
was found among the corpus terms and the one naive extension checked here.

## Stop rules honored

No new cipher menu, decoder, password generation, blob/address oracle, brute
force, GPU, Docker, network, or external agent. No per-hit follow-up search
beyond each matched message's own thread.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase450_g_prime_consumer_selector_audit.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase450_g_prime_consumer_selector_audit.py \
  --json-out /tmp/phase450_result.json
```
