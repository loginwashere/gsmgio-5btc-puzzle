# FEFE as a control event: investigation results

Date: 2026-09-30. Exploratory local investigation; no new canonical phase number.

## Result

The tested resets, reversals, color/decoder switches, and immediate switches to FAED fail the established token constraints. A concrete source-byte rule survives:

> FEFE represents its marked source byte through an exceptional `b` host. Suppress that byte's later ordinary colored endpoint, and advance the prime clock only for retained events.

This reproduces DBBI's **84-token parse / Selection A** exactly. It is a possible operational meaning of the marker, not a new decipherment: Selection A was already reconstructed in Phase 525 and its matrix consumers were tested in Phases 535, 542, and 543.

The new counterfactual inventory provides a narrower observation. Among all 82 eligible internal-zero marker locations, this rule matches a complete DBBI parse only at source byte 21's two internal zeros. Combining that with the already-known **zero-based prime-index** criterion leaves the actual marker, spiral index 163 / character 21 / bit 4. This conjunction is descriptive and conditional, not a discovery p-value or independent proof of creator intent. The reference insertion also remains compatible with the real marker.

## Inputs and what was fixed

The [main protocol](Brainstorms/2026-09-30%20-%20FEFE%20Control%20Event%20Protocol.md) was written before execution. It specifies 18 models, their addressing conventions, complete output retention, and the counterfactual-location inventory. The [prime-location follow-up](Brainstorms/2026-09-30%20-%20FEFE%20Prime%20Location%20Followup.md) was written after the main results and before the follow-up arithmetic; it is explicitly adaptive.

The implementation reconstructs the image from [the canonical grid crop](img/gsmg_rabbit_hint.png) and uses canonical DBBI, FAED, and the solved Stage-3.2.2 answer. It imports the exhaustive prime-host parser, but neither the old Flo walk implementation nor any ciphertext oracle. Input and protocol digests are retained in the result.

Established inputs, rather than fresh claims:

- 24 colored URL-byte endpoints plus one internal FEFE event, sorted in the solved spiral;
- blue=`b`, yellow=`be`, exceptional FEFE=`b` in the community prime walk;
- successive primes as host locations, shifted in the raw stream by earlier digraph widths;
- FEFE at zero-based spiral index 163, inside source byte 21 (`n`), before that byte's usual endpoint at 167;
- two complete DBBI parses under the prime-host grammar: 83 and 84 logical tokens.

The exceptional FEFE=`b` rule is inherited from community reconstruction. It does **not** follow mechanically from FEFE's zero-valued image bit. That distinction limits how strongly any result can be interpreted as the creator's instruction. Sources: [Phase 37](../tools/gsmg/findings/P00037.md), [Phase 48](../tools/gsmg/findings/P00048.md), [Phase 525](GSMG_PHASE525A_DBBI_SELECTION_A_RECONSTRUCTION_AUDIT.md).

## What the control rule does

The local event sequence is:

```text
ordinary endpoint for byte 20 ('a')
FEFE inside byte 21 ('n')
ordinary endpoint for byte 21 ('n')
ordinary endpoint for byte 22 ('t')
ordinary endpoint for byte 23 ('e')
ordinary endpoint for byte 24 ('d')
```

The reference treats FEFE and byte 21's endpoint as separate hosts. The source-byte control rule treats FEFE as the representative of byte 21, so its later endpoint is redundant.

| Image event | Source byte | Reference insertion | Consume-byte-once rule |
|---|---:|---|---|
| 21, FEFE at spiral 163 | 21, `n` | prime 73; raw 79; `b` | same |
| 22, yellow endpoint at 167 | 21, `n` | prime 79; raw 85–86; `be` | suppress; no clock advance |
| 23, yellow endpoint at 175 | 22, `t` | prime 83; raw 90–91; `be` | prime 79; raw 85–86; `be` |
| 24, blue endpoint at 183 | 23, `e` | prime 89; raw 97; outside DBBI | prime 83; raw 90; `b` |
| 25, yellow endpoint at 191 | 24, `d` | prime 97; raw 105; outside DBBI | prime 89; raw 96; outside DBBI |

The control rule retains source bytes 1–23 once each. Its matching host sequence is exactly the 84-token parse's 23 hosts: 16 single `b` hosts and seven `be` hosts. The reference matches the 83-token parse's 15 `b` and eight `be` hosts.

This changes the event-to-source-byte correspondence substantially, but changes the aligned answer mask only at its final position: the reference selects raw positions 90–91 together; the replacement selects 90, leaving 91 as payload. The resulting 30-character selected answer is the old 31-character output without its final `e`. It does not supply a new recognizable instruction.

Both models exhaust the **prime-host** inventory before representing the final image byte. In the 84-token parse, the remaining raw terminal `e` is an unhosted payload token. The rule does not make it another matching prime host. Phase 542 already placed that tail as the 24th matrix object using the same source-byte conservation assumption; that conditional completion did not yield an instruction.

## Exact model results

“Prefix hosts / symbols” counts matching constraints before the first mismatch or range failure. A silent event removes a constraint; a stop shortens the test. Neither should be rewarded for avoiding failures.

| Model | Prefix hosts / symbols | First failure or limitation |
|---|---:|---|
| Reference | 23 / 31 | exact 83-token hosts; next host beyond DBBI |
| Delimiter only | 23 / 31 | same constraints and parse as reference |
| Stop after FEFE | 21 / 27 | simply discards the remaining tests |
| Ignore marker | 20 / 26 | next yellow requires `be` at raw 79; actual `bf` |
| Silent prime slot | 22 / 30 | same later timing, but omits the FEFE host constraint |
| FEFE as `be` | 20 / 26 | marker requires `be` at raw 79; actual `bf` |
| Swap blue/yellow after marker | 22 / 28 | image event 23 requires `b` at raw 89; actual `a` |
| Mirror token alphabet after marker | 21 / 27 | next yellow requires `he` at raw 85; actual `be` |
| Binary mode after marker | 21 / 27 | next yellow requires `a` at raw 85; actual `b` |
| Reset digraph-width correction | 21 / 27 | next host rereads raw 79; requires `be`, actual `bf` |
| Restart DBBI from beginning | 21 / 27 | next host rereads raw 2–3; requires `be`, actual `bb` |
| Restart in remaining DBBI suffix | 21 / 27 | requires `be` at raw 81; actual `fg` |
| Reverse remaining suffix | 21 / 27 | descending raw 90–89 gives `ba`, requires `be` |
| Switch to FAED, keep clock | 21 / 27 | requires `be` at FAED raw 85; actual `ga` |
| Switch to FAED, fresh clock | 21 / 27 | requires `be` at FAED raw 2; actual `ae` |
| Consume marked byte once | 23 / 30 | exact 84-token hosts; next host beyond DBBI |
| Suppress endpoint but keep its prime slot | 21 / 27 | requires `be` at raw 89; actual `ab` |
| Remove marker and its byte's endpoint | 20 / 26 | requires `be` at raw 79; actual `bf` |

These failures exclude the **specified rules**, not every possible control operation. In particular, the data do not support an immediate ordinary reset or stream switch at FEFE under this addressing model.

The delimiter-only projection is:

```text
before: ncsyangcahiriasogaleafayan
marker: e
after:  stve
```

That adds no decoding information. The known `nest` substring spans the split (`n` + `e` + `st`); FEFE is not an ordinary word separator. Earlier thematic-word observations and their demotion remain unchanged ([Phases 131–132](../tools/gsmg/findings/P00131.md)).

## Counterfactual marker locations

To avoid testing only the cell whose importance was already known, the audit moves the exceptional marker label to every zero-valued **internal** bit of the decoded URL. Colored LSB endpoints and the four central leftovers are excluded. Underlying URL bits remain unchanged.

There are 82 eligible locations. Each is tested under both reference insertion and marked-byte replacement: 164 location/model cases.

| Rule | Locations matching complete parse hosts | Source bytes | With zero-based prime-index requirement |
|---|---:|---|---|
| Reference insertion | 7 | 20 or 21 | 157 and 163 |
| Consume marked byte once | 2 | 21 only | 163 only |

The replacement's two compatible locations are:

| Spiral index, zero-based | Source byte | Bit, one-based | Index prime? |
|---:|---|---:|---|
| 160 | 21, `n` | 1 | no |
| 163 | 21, `n` | 4 | yes; actual FEFE |

At byte level, the replacement is equivalent to assigning the marked byte an exceptional single-host type. It cannot distinguish locations inside the same byte. The independent verifier derives the same counterfactual matches directly from ASCII parity and the two complete parses' host colors, without running the state machine again.

The prime-index conjunction uses a property already recorded in Phase 37. Ten of the 82 eligible internal zero cells have prime zero-based indices. The corresponding one-based criterion has 23 eligible cells, keeps no replacement match, and does not accept the actual marker because 164 is composite. Both indexing conventions are disclosed; no alternative arithmetic predicates were searched.

This is useful specificity: the source-byte rule plus the existing zero-based prime-location reading selects the actual cell. It is **not** an independent confirmation. The marker was known before the rule family was proposed, the prime property was known, and the real cell fits both the reference and replacement. Smaller counterfactual survivor counts alone do not establish which operation the creator intended.

## Where this path leads, and where it stops

The control interpretation reaches an existing fork in the analysis:

```text
FEFE as extra host
  -> retain its byte's ordinary endpoint too
  -> 83-token DBBI parse / historical insertion

FEFE as that byte's exceptional representative
  -> suppress its ordinary endpoint
  -> 84-token DBBI parse / Selection A
```

This explains how a marker could choose a **grouping rule** instead of supplying a number to hash. It does not establish that the second branch is intended, nor reveal a new consumer.

The straightforward continuation is already covered:

- [Phase 535](GSMG_PHASE535_SELECTION_A_MATRIX_COMPOSITION.md): Selection A's backward matrix placement is collision-free but its row sums and Architect-word consumer produce no clear instruction.
- [Phase 542](GSMG_PHASE542_TERMINAL_E_COMPLETION_AUDIT.md): source-byte conservation fixes the unhosted terminal `e` placement; the completed output remains unrecognized.
- [Phase 543](../tools/gsmg/findings/P00543.md): direction/Caesar, direct cipher parity, and the declared password-slot expansion were negative.

Repeating those tests would not advance this route. The remaining concrete question is whether **a sourced instruction selects single representation per byte, or a different consumer uses that grouping**. The actual image revision and its original posting context could help distinguish such a rule. An arbitrary new transformation of Selection A would introduce another unexplained choice.

## Verification and artifacts

- Synthetic checks distinguish skipped versus silent slots, endpoint suppression versus retained timing, forward versus reverse suffix origins, alphabet mirroring, and fresh-stream resets.
- Both exhaustive DBBI parses round-trip to all 91 raw symbols.
- An independent coordinate check verifies every recorded fitting token, including reversed and reused positions.
- Independently reconstructed parse host positions reproduce both exact masks and aligned answer projections.
- Direct ASCII-parity calculations reproduce all 164 counterfactual parse-match decisions and within-byte equivalence classes.
- Deterministic rerun produces the same primary JSON digest: `3a8281bcfb0d6e4ae3cd27bb878c6c38a08bc4b72cc9a0a4ce7d1a88756dd2ad`.
- No ciphertext oracle or password generator was called.

Reproduce the main audit, verification, and explicitly adaptive follow-up:

```bash
python3 tools/gsmg/fefe_control_event_audit.py --prime-followup
```

[Implementation](../tools/gsmg/fefe_control_event_audit.py), [full primary results](../tools/gsmg/fefe_control_event_result.json), [prime-location follow-up results](../tools/gsmg/fefe_control_prime_location_followup.json).
