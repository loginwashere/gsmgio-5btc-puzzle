---
type: audit
phase: 264
date: 2026-08-13
status: closed
result: partial
disposition: recognition-only
evidence_level: authenticated-artifact
topics:
  - phase-2
  - decentraland
  - coordinates
  - safenet
  - external-evidence
related_phases:
  - 8
  - 69
  - 70
aliases:
  - Phase 264
---

# GSMG `X2SH4Y0QB15` Decentraland Coordinate Audit

## Question

Could the solved variables in

```text
# X 2 S H 4 Y 0 Q B 15 #
```

encode Decentraland coordinates in addition to the established reversed-string
geographic coordinate near SafeNet/Thales? The walkthrough places this
plaintext under numbered stage 3, while its image is named `phase2.png`; this
audit uses the literal token name to avoid that phase-numbering ambiguity.

Using the literal mathematical values already recovered for the variables gives:

```text
S = 32
H = -42
Q = 82
B = -16

X row: 2, 32, -42, 4
Y row: 0, 82, -16, 15

paired: (2,0), (32,82), (-42,-16), (4,15)
```

The non-arithmetic `Q=82` step is keyboard-based, not an A1Z26 value of a
cipher name. `Qwerty` is the fish's name in *Mr. Robot*; “extend the name”
gives the keyboard row `QWERTYUIOP`. On the number row, `I` is below `8` and
`W` is below `2`; preserving the clue's explicit `I`-then-`W` order gives
`82`. This explanation is repeatedly present in the solver corpus (for
example the mined lines around `4059-4060` and `7671-7675`), although it is a
community derivation rather than a separate creator confirmation.

This audit checked those points, relevant reversals and neighbors against the
public Decentraland Content Server's active-entity and historical-deployment
APIs on 2026-08-13. Scene entity IDs and content hashes are immutable; which
entity is active at a pointer is not.

## Results

| Reading | Historical content | Assessment |
|---|---|---|
| `(2,0)` | central Genesis Plaza/spawn region; a Genesis Plaza deployment covered the pointer by 2020-02-22 | good broad match |
| `(32,82)` | Mini Mall from 2020-04-19, then the art-oriented Outbox Artisan scene from 2020-04-21 | real art/gallery match, but it postdates the clue |
| `(-42,-16)` | no deployment returned | not an exact hit |
| neighboring `(-41,-16)` / `(-41,-17)` | the creator's `GSMG.io Puzzle piece`, deployed 2020-02-20, containing `sounds/puzzlepiece.mp3` | strong one-parcel adjacency to the known side quest |
| `(4,15)` | no deployment until 2021-01-18 | unavailable during the clue period |
| reversed `(15,4)` | `Street Theatre`, deployed 2020-02-06 | real pre-clue scene |
| neighboring `(14,4)` | HTC Exodus scene assets explicitly include `HTC_ZionLogo`, `HTC_Phone`, `HTC_Vault`, `HTC_Portal`, and `HTC_Cube` | strong ZION adjacency after applying “worst gear” as reversal |

The community's later descriptions are therefore substantially grounded in
real scenes: spawn, art/gallery, GSMG audio, and ZION were not fabricated.
That does not establish an authored route. The exact construction is irregular:
it combines a broad central-region match, an exact art-scene point, two
one-parcel adjacencies, and a coordinate swap for only the final pair.

## Chronology and provenance

Chronology is the main objection to treating the four-point route as the
original solution:

- the full clue is independently preserved in the puzzle's decrypted
  `X2SH4Y0QB15` plaintext and was reposted in solver chat by Legik on
  2020-03-24 (message
  `2834`); this is an earliest-observed-chat statement, not a claim that the
  clue originated or was first published on that date;
- the `(32,82)` Mini Mall/Outbox scene first appeared on 2020-04-19, after
  that clue record;
- `(4,15)` had no recorded scene until 2021-01-18;
- the four-waypoint explanation first appears in the reviewed solver export
  in February-March 2021 (`5828`-`5950`, then `6595`-`6609`);
- the creator's exact GSMG audio deployment at `(-41,-17)` predates the clue,
  as do the HTC/ZION scenes near reversed `(15,4)`.

The deployments also belong to different addresses:

```text
GSMG puzzle piece       0x5d801b2b0b216790a49898b322246282547b546b
HTC/ZION area           0x1337e0507EB4aB47E08a179573ED4533d9E22a7b
32,82 gallery           0x7979dbb8001e49561dda0d9731d86250f71d8014
```

This rules out the simplest version of a single creator deliberately placing
all four scenes. It does not rule out the creator selecting already-known
locations, but the post-clue deployment at `(32,82)` makes that explanation
chronologically weak.

The retained April 2020 `(32,82)` manifests verify an art-oriented scene but
do not contain a named `Clubbed to Death` audio asset. The relevant old script
hash is still listed in the deployment record, but its content has been
garbage-collected from the normal peer. The song claim therefore remains a
community observation rather than independently recovered primary content.

## Relationship to the known Decentraland side quest

Telegram JSON identifies message `1837`, `Only -41,-17 matters`, as authored
by `Jrk Bgrt` (`from_id=user9815232`) on 2020-02-22. However, its surrounding
messages are explicitly about Decentraland's interactive mode and whether the
account has one parcel. The project's creator-clue index therefore excluded it
as ordinary contextual/gameplay conversation, not as a standalone puzzle clue.
It must not be used as independent evidence that the `X2SH4Y0QB15` row was
intended to encode four Decentraland waypoints.

Separately, the immutable deployment itself proves that `(-41,-17)` is one
half of the two-parcel `GSMG.io Puzzle piece` scene and that clicking its cube
plays `sounds/puzzlepiece.mp3`. The already-reproduced stereo inversion and
spectrogram operation yields the community's `HASHTHETEXT` instruction.

That exact scene and audio are creator-controlled artifacts. Message `1837`
provides context for navigating the scene but is not a clue-level selector.
The four coordinates derived from the `X2SH4Y0QB15` row are a different,
later interpretive layer with no creator confirmation found.

## Verdict

Retain the Decentraland reading as an unverified secondary correspondence:

```text
(2,0)       -> spawn / Genesis Plaza region
(32,82)     -> art/gallery scene
(-42,-16)   -> one parcel west of the GSMG scene's northern parcel
(4,15)      -> reverse to (15,4), beside an explicit HTC ZION scene
```

Do **not** promote it over the established SafeNet reading. The latter uses
one global operation -- reverse the complete character stream -- and produces
one standard geographic coordinate. The Decentraland reading changes its
matching rule between points and contains a material chronology problem.

Tracked as `G-X2SH-001` in the
[Open Gap Registry](GSMG_OPEN_GAP_REGISTRY.md) so this fragment isn't
re-litigated from scratch: parked, P2, closes only on a creator statement
selecting this reading or a resolution of the chronology conflict.

Disposition: **recognition-only, unverified secondary route**. Calling it an
authored Easter egg would overstate the evidence. It explains why the row
resembles XY data and why several later solvers found striking virtual-world
associations, but chronology and inconsistent matching prevent confirmation;
it supplies no new password, cipher selector, or transition beyond the
already-solved `HASHTHETEXT` side quest.

## Reproducible public endpoints

- [Decentraland Catalyst API reference](https://decentraland.github.io/catalyst-api-specs/)
- [`(2,0)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=2%2C0)
- [`(32,82)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=32%2C82)
- [`(4,15)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=4%2C15)
- [`(15,4)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=15%2C4)
- [`(14,4)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=14%2C4)
- [`(-42,-16)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=-42%2C-16)
- [`(-41,-17)` deployments](https://peer.decentraland.org/content/deployments?entityType=scene&pointer=-41%2C-17)
