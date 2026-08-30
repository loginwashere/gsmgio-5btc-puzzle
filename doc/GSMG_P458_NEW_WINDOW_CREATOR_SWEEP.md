---
type: audit
phase: 458
date: 2026-08-30
status: complete
result: no-creator-activity-in-window
disposition: rejected-new-window-selector-across-five-selected-gaps
script: tools/gsmg/phase458_new_window_creator_sweep.py
---

# Phase 458 — New Telegram Export Window Creator Sweep

## Question and scope

`GSMG_OPEN_GAP_REGISTRY`'s standing reopen trigger for `G-ARCH-001`,
`G-YIN-001`, `G-ESC-001`, and `G-MSL-001` is "a new Telegram export or
genuinely new page artifact surfaces." `G-PRIME-001` shares the same kind of
corpus dependency via Phase 450's sweep. The reproducible view now extends
past every previously-checked cutoff:
[GSMG_TELEGRAM_EXPORT_OVERLAY_BASELINE](GSMG_TELEGRAM_EXPORT_OVERLAY_BASELINE.md)
merges `ChatExport_2026-07-26` (the pinned complete baseline, through id
67267), `ChatExport_2026-08-09 (1)`, and `ChatExport_2026-08-30` into one
deduplicated view through id 70186.

**Scope is five gaps, not every parked gap.** This phase covers
`G-ARCH-001`, `G-YIN-001`, `G-ESC-001`, `G-MSL-001`, and `G-PRIME-001` only —
the gaps whose registry rows depend on Telegram-corpus coverage. The
registry's other four parked gaps — `G-MATPROD-001`, `G-KIT-001`,
`G-GGN-001`, `G-X2SH-001` — are not Telegram-corpus-blocked in the same way
and are explicitly out of scope here; their rows are untouched by this
phase.

**The span is not uniformly new.** Phase 247
(`architect_mirror_selector_audit.py`) already checked messages beyond its
`INDEXED_SOLVER_MAX_ID = 67263` — but only against `ChatExport_2026-08-09
(1)` (ids 67269–68343, 952 messages) and only for `G-ARCH-001`'s three
narrower lanes. The genuinely unswept tail is ids 68344–70186 (1,564
messages), from `ChatExport_2026-08-30`, which has never been checked
against any gap, and never checked for new creator-authored media at all.
This phase re-sweeps the full 67269–70186 span — including the 952-message
overlap with Phase 247 — because widening that overlap to the four
additional gaps' vocabulary is new work even though the message set itself
is not.

This phase closes that coverage gap with one bounded, frozen pass: does the
full span (ids 67263 exclusive through 70186) contain any creator-authored
message, creator-authored media, or non-creator message with a creator
reply, under the union of these five gaps' vocabularies?

This is a corpus-existence check. It invents no new decoder and follows the
same creator-or-creator-reply licensing discipline Phases 247/450 already
use; see the vocabulary-provenance note below for which patterns are reused
versus newly assembled.

## Frozen inputs

- `telegram_export_overlay_manifest.merge_exports()` over its three default
  export directories (see the overlay baseline doc for row counts and
  provenance), restricted to `type == "message"` and `id > 67263`.
- Creator identity fixed by Telegram user id `user9815232`, unchanged from
  every prior creator-sweep phase — **never the display name**. 143
  messages in this window show `from: "Denis Golovkin"`, the creator's real
  name, but they belong to a distinct Telegram account, `user398109413`. The
  creator's only observed display name across the entire corpus is `Jrk
  Bgrt`. Every authorship check in this phase uses `from_id`, not `from`,
  specifically to avoid this collision.
- Vocabulary, by provenance:
  - **Reused verbatim from an already-frozen phase:** `G-ARCH-001` —
    `architect_mirror_selector_audit.py`'s
    `MIRROR_KEYWORDS`/`ARCHITECT_WORD`/`HYE_WORD`/`SELECTOR_LANGUAGE` terms
    (Phase 247); `G-PRIME-001` —
    `phase450_g_prime_consumer_selector_audit.py`'s standalone
    `401`/`400`/`73`, `CDI`/`CD`, and `roman numeral(s)`/`title initial`
    phrases (Phase 450).
  - **Newly assembled for this phase, not previously frozen elsewhere:**
    `G-YIN-001` (`yin`, `yang`, `yin-yang`/`yinyang`, `dbbi`, `faed`);
    `G-ESC-001` (`escape`, `mirror9`, `checkerboard`, the literal pair
    tokens `{g,i}` / `{h,e}`); `G-MSL-001` (`matrixsumlist`, matrix+dimension,
    `traversal`) — each drawn directly from that gap's own registry
    description. No prior phase pre-registered a vocabulary for these
    three, so treat their coverage as this phase's own construction rather
    than reuse of an established protocol. This does not weaken the result
    below, since zero creator activity in the window makes vocabulary choice
    immaterial to the verdict — but it is a different evidentiary claim than
    "reusing an already-frozen protocol," which only genuinely applies to
    `G-ARCH-001` and `G-PRIME-001` here.

## Method

`tools/gsmg/phase458_new_window_creator_sweep.py`:

1. lists every creator-authored message in the span;
2. lists every creator-authored photo/file in the span — every one of
   Phase 248's 88 frozen creator-media ids is below the cutoff, so any hit
   here is unconditionally new, not a re-hit of an already-reviewed record;
3. searches every message in the span against the union of the five
   vocabularies above, keeping a hit only if it is creator-authored or a
   non-creator message that received a creator reply.

A `real_corpus_self_test()` asserts the exact frozen real-corpus counts
below (window size, min/max id, creator-message count, creator-media count,
and per-gap hit count all zero) in addition to the synthetic-mechanics
`self_test()`, so a future corpus change that silently alters this result
is caught by regression rather than only by re-running the script manually.

No message content outside these frozen patterns is interpreted; no oracle,
decoder, or password attempt is run.

## Result

Independently reproduced:

- The span covers ids 67269–70186: 2,516 messages total, of which 952
  (ids 67269–68343) duplicate Phase 247's already-checked span and 1,564
  (ids 68344–70186) are genuinely new.
- Every message has a `from_id`.
- `creator_message_count = 0` — no creator-authored message exists anywhere
  in this span. The creator's last message in the entire corpus remains id
  66976, unchanged from before this phase.
- `any_creator_media = False` — no creator-authored photo or file exists in
  this span, and therefore zero creator-reply-licensed hits are even
  possible from that channel.
- `any_gap_hit = False` — zero hits under any of the five vocabularies,
  whether creator-authored or creator-reply-licensed, across the full span
  including the genuinely new tail.
- `verdict = no_creator_activity_in_window`.
- 143 messages display as "Denis Golovkin" but belong to `user398109413`,
  confirmed distinct from the creator's `user9815232`.

The creator account is silent for the entire 67269–70186 span, superseding
Phase 247's narrower finding ("952 new messages, zero creator-authored"),
which covered only up to id 68343 and only `G-ARCH-001`'s lanes.

## Disposition

Rejected, for a new-window creator-clue selector across `G-ARCH-001`,
`G-YIN-001`, `G-ESC-001`, `G-MSL-001`, and `G-PRIME-001`. No gap's priority,
state, or closure condition changes — each remains `parked`, and each gap's
registry row already conditions reopening on exactly this kind of check
turning up positive, which it did not. `G-MATPROD-001`, `G-KIT-001`,
`G-GGN-001`, and `G-X2SH-001` are untouched by this phase and are not
described as re-checked.

## Facts affected

None. This is a negative existence check, not a new established claim.

## Supersedes/corrects

Extends, without changing, Phase 247's negative finding to the full current
span and to four additional gaps' vocabularies it never checked — three of
which (`G-YIN-001`, `G-ESC-001`, `G-MSL-001`) use vocabulary assembled for
this phase rather than an already-frozen protocol; see the vocabulary
provenance note above.

## Reopen condition

A future Telegram export extending past id 70186 that contains a
creator-authored message, creator-authored media, or a creator reply to a
message matching any of the five vocabularies above would reopen the
corresponding gap's "new export surfaces" trigger. None currently exists.

## Artifacts

- `tools/gsmg/phase458_new_window_creator_sweep.py` (synthetic `self_test()`
  plus `real_corpus_self_test()` against the live overlay)
- `tools/gsmg/test_phase458_new_window_creator_sweep.py`
- `tools/gsmg/phase458_result.json`
