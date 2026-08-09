# GSMG First-Piece Event-Rail Preservation Audit

**Date:** 2026-08-09  
**Status:** `14/8/1` token inventory verified; one-blue-per-row mapping rejected.

## Two related inventories

Points 2 and 4 had begun to mix two different source objects. This audit keeps
them separate.

### Complete URL endpoint mask

All 24 URL characters have one colored LSB endpoint:

```text
BBBBYBBBYYBBBBYBBYYBYYBY
15 blue / 9 yellow
```

Partitioning the complete URL gives:

```text
blue:   gsmgio/eseeisae   (15)
yellow: .thdplntd         (9)
```

### DBBI-fitting event prefix

The spatial prime walk inserts FEFE as its own event and retains the complete
23-event prefix that fits DBBI:

```text
BBBBYBBBYYBBBBYBBYYBFYY
14 blue / 8 yellow / 1 FEFE
```

Preserving event boundaries gives:

| Class | Events | Source characters | Required DBBI tokens | Token symbols |
|---|---:|---|---|---:|
| Blue | 14 | `gsmgio/eseeisa` | 14 × `b` | 14 |
| Yellow | 8 | `.thdplnt` | 8 × `be` | 16 |
| FEFE | 1 | `n` | 1 × `b` | 1 |

The token-symbol total is therefore:

```text
14 + 2*8 + 1 = 31
```

That length is forced by the event profile and `b`/`be` grammar; it is not an
independent occurrence of 31.

The fitted prefix represents only 22 distinct URL endpoint objects. FEFE is an
additional internal cell inside source character `n`, whose normal LSB
endpoint is itself a yellow event. Consequently `n` occurs in both the yellow
and FEFE groups. The `14/8/1` structure is an event partition, not a
23-character partition of the URL.

Flattening the token sequence also destroys information: blue and FEFE both
require literal `b`. Only event metadata preserves the distinction between the
14 blue singleton events and the exceptional FEFE singleton.

## Do 14 blue events map one-to-one onto 14 rows?

No. Projecting the fitted blue events back to authenticated grid coordinates
gives these row indices in blue-event order:

```text
8, 14, 14, 9, 1, 5, 13, 2, 2, 10, 12, 3, 7, 4
```

They cover 12 distinct rows:

```text
missing:    6, 11
duplicated: 2, 14
```

Thus there is no geometric one-blue-event-per-row mapping. Zipping the 14 blue
events to rows 1–14 by event order would be a newly invented traversal that
ignores their actual coordinates.

### Fixed-position calibration

Keep the 22 fitted non-FEFE positions fixed and choose which 14 are blue, the
same `C(22,8)=319,770` profile family used by the prime-sum calibration.

```text
blue coverage = all 14 rows: 256 / 319770
                            = 128/159885 ≈ 0.000801

blue coverage = observed 12 rows: 65856 / 319770
                                ≈ 0.20595
```

A one-per-row assignment is possible and would have been unusual in this
bounded family, but the observed labels do not have it. The actual 12-row
coverage is ordinary. This is a clean falsification of the proposed mapping,
not a near miss.

The eight yellow events happen to occupy eight distinct rows, but 88,720 of
319,770 fixed-profile assignments do so (`≈0.27745`), so that property is also
ordinary.

## Native all-event row buckets

Using every fitted event—not only blue—does cover all 14 rows. In native row
order the bucket sizes are:

```text
2, 2, 1, 1, 2, 1, 2, 3, 1, 2, 1, 1, 2, 2
```

Full row coverage is first reached at event 20, before FEFE at event 21. This
is a parameter-free spatial organization and remains a valid structured input.
It does not yet specify how to combine multiple events within a row or how to
consume the resulting 14 buckets.

## Literal two-stream MUX

Point 2 proposed using the complete 24-endpoint color mask to pull the next
character from DBBI on blue and FAED on yellow. The exact output is:

```text
B -> DBBI, Y -> FAED:
dbbifbfbaehccbdegggbeeid

B -> FAED, Y -> DBBI:
faeddggebbedfcibdbfabhbc
```

Both outputs self-label their chosen blue rail in the first four characters
because the mask begins `BBBB`, while the streams begin `dbbi` and `faed`.
Neither output continues as plaintext after that copied prefix, and the prefix
does not select a polarity because both assignments reproduce the name of
whichever stream was assigned to blue.

More importantly, this two-stream MUX uses the complete `15/9` endpoint mask.
It cannot preserve the distinct FEFE class from the fitted `14/8/1` inventory
without either introducing a third stream or explicitly folding FEFE into one
color. Folding it into blue reproduces the literal token `b` but erases the
exception that is load-bearing for `400/401/73`.

## Verdict

Promote:

1. the exact distinction between the `15/9` endpoint mask and `14/8/1` fitted
   event profile;
2. the token-preserving blue/yellow/FEFE inventories and source strings;
3. the forced 31-symbol flattened length and its information loss;
4. the native all-event 14-row buckets as a valid unconsumed structure;
5. the two exact literal MUX outputs as negative/non-language controls.

Reject the proposed one-blue-event-per-row architecture. Also reject a
two-stream MUX as a FEFE-preserving consumer unless a new clue supplies a
third rail or explicitly authorizes folding the exception. No oracle follows.

## Reproduction

```bash
python3 tools/gsmg/first_piece_event_rail_preservation_audit.py --self-test
```
