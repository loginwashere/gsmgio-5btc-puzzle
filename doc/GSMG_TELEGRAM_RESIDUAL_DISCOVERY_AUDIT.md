# Telegram residual-discovery audit

Date: 2026-08-24

## Scope and corrected counts

The original Stage-1 keyword sweep contains exactly 1,828 messages.  Its
closely reviewed Phase-54 subset was 68 messages, not 56: 56 anchor-sender
hits plus every hit for `31 characters`, `consume`, `yellow-blue`, and
`ncsyang`.  The exact residual is therefore 1,760 messages.

`telegram_stage1_residual_classification_audit.py` freezes that complement at
message level.  Every row records source ID, timestamp, sender, matched terms,
the SHA-256 of its complete untruncated text, disposition, and reason:

| Disposition | Count |
| --- | ---: |
| Covered by an existing phase/family | 381 |
| Noise, question, repost, or unbound claim | 1,378 |
| New reproducible lead | 1 |
| **Total** | **1,760** |

The sole new lead is message `66722`, now Phase 387.  Its `KMODEST`
checkpoint reproduces exactly; its proposed continuation to `BE MODEST` is
post-hoc and was not promoted.  The manual review included all 132
code/formula/explicit-structure candidates, all 260 further explicit-result
messages, and all 77 messages from the independent technique-plus-surprise
intersection.  Lower-signal rows were classified from their complete text by
the frozen rules in the ledger audit.  “Covered” means the named operation
family already has a project phase; it does not claim each poster's personal
implementation was rerun byte-for-byte.

## Generalized context clustering

The two-hour same-sender window was generalized from the old anchor-media
scope to every Stage-1 hit:

| Set | Total | New beyond Stage 1 |
| --- | ---: | ---: |
| Complete two-hour expansion | 11,407 | 10,078 |
| Bounded technical/media review lane | 2,365 | 1,036 |

The bounded lane retains a non-hit neighbor when it contains a declared
technique/surprise token, carries media, or contains at least 500 characters.
It automatically recovers BTCSEED follow-ups `43258`, `43441`, and `43442`.
The latter two are reached through nearby Stage-1 seed `43440`; no 26-hour
window expansion is needed.

## Technique-plus-surprise axis

The separate token-aware sweep avoids bare-substring errors such as matching
`wif` inside `wifi`.  It reports:

| Axis | Hits |
| --- | ---: |
| Cryptographic technique | 1,629 |
| Surprise/probability language | 827 |
| Both (primary review set) | 77 |

All 77 intersection messages were read in full.  The axis catches the
BTCSEED origin (`43248`) and immediate Bifid/Trifid discussion (`43258`,
`43274`) without relying on the puzzle-object words `dbbi` or `faed`.
It found no second authenticated result.  The strongest uncatalogued items
were unbound scripts (for example message `43697` omits the two QR inputs),
ordinary-base-rate coincidences (a 12-word BIP39 checksum succeeds about one
time in 16), or later rail claims that omit the defining input/derivation.

## Reaction-threshold gap

Phase 68's reaction cutoff remains unchanged: at least five reactions is the
preselected natural knee (105 messages, versus 523 at three or more).  The
BTCSEED thread did not enter that set.  Lowering the threshold now merely to
capture a known miss would be post-selection.  The documented limitation is
instead structural: low-engagement technical threads are invisible to the
reaction axis, and are covered by the independent technique/surprise and
context-cluster axes above.

## Artifacts

- `tools/gsmg/telegram_stage1_residual_classification_audit.py`
- `tools/gsmg/telegram_export_all_hit_context_clusters.py`
- `tools/gsmg/telegram_export_technique_surprise_sweep.py`
- `tools/gsmg/phase387_btcseed_kmodest_checkpoint_audit.py`

