# GSMG Second `matrixsumlist` and `KIT` Audit

**Date:** 2026-08-09  
**Status:** `[43,25,18]` verified; subtraction exact; `KIT` remains a semantic fold.

## Source reconstruction

The independently selected `#383838` footer layer contains two ordered rows of
11 glyph-pixel counts:

```text
banner:  4 1 4 4 2 1 1 1 2 1 4   sum 25
address: 2 1 2 2 1 3 1 1 1 2 2   sum 18
                                      ----
                                      total 43
```

Applying the established `matrixsumlist` grammar—total followed by ordered row
sums—gives:

```text
[43,25,18]
```

`tools/gsmg/first_piece_second_matrixsumlist_audit.py` resamples the exact
Stage-0 PNG and fixed glyph boxes. It does not import the proposed triple as a
constant. The source image digest, `#383838` selector, selected glyph strings,
per-glyph counts, row widths, sums, and total are all assertion-backed.

This makes `[43,25,18]` a natural second use of the same grammar, although no
creator text explicitly says that `matrixsumlist` must be applied twice.

## Componentwise comparison

The first-piece decimal-digit matrix supplies the established list:

```text
[23,16,7]
```

Subtracting it componentwise from the shadow list gives:

```text
[43,25,18] - [23,16,7] = [20,9,11]
```

All three numbers have exact source-internal counterparts:

```text
20 = number of colored events before FEFE, which is event 21
 9 = number of yellow endpoints
11 = number of selected glyphs in each #383838 shadow row
```

This is striking constructor coherence, but not three independent
confirmations. The event and yellow counts come from the first-piece source
that also produces `[23,16,7]`; the row width comes from the shadow source that
also produces `[43,25,18]`.

The checksum:

```text
20 = 9 + 11
```

adds no evidence at all. It is algebraically forced because both source lists
already have the form `[a+b,a,b]`; subtracting two such lists must produce
another triple with the same additive identity.

## `TIK` and `KIT`

Direct A1Z26 gives:

```text
[20,9,11] -> TIK
```

Reversing the result gives:

```text
[11,9,20] -> KIT
```

`kit` is a correct term for a young rabbit, making it thematically apt for the
rabbit-grid puzzle. But reaching it requires three operations not locally
selected by either source:

1. componentwise subtraction;
2. A1Z26 interpretation;
3. reversal.

The puzzle's broader yin-yang/reversal language makes reversal plausible, but
does not uniquely select it here.

## Bounded order calibration

Keeping totals first, independently allowing each source's two rows to retain
or swap order, and reading each difference directly or reversed produces eight
outputs:

```text
TIK / KIT
TBR / RBT
TRB / BRT
TKI / IKT
```

Exact `KIT` appears once in eight. Permuting the three native difference
components freely gives six A1Z26 strings, again with `KIT` once. These are
descriptive fixed-target rates, not valid discovery p-values: `KIT`, reversal,
and the young-rabbit interpretation were recognized after inspecting the
result.

## Secondary observations

Several source numbers have additional exact descriptions:

- `25` equals the complete 24-endpoint-plus-FEFE event inventory;
- `43` is the 14th prime, echoing the 14x14 grid;
- `18` is `R` under the creator's `R=18, A=1, B=2` rabbit wordplay.

These remain post-hoc semantic echoes. They should not be added as independent
probability multipliers.

## Verdict

Promote:

1. the sampled 2x11 count matrix;
2. its natural `[43,25,18]` total/row-sum list;
3. the exact difference `[20,9,11]`;
4. its exact `(20 events before FEFE, 9 yellow, 11 row width)` correspondence;
5. the direct `TIK` and reversed `KIT` A1Z26 reads as reproducible outputs.

Treat `[43,25,18]` as a strong second structural checkpoint. Keep `KIT` as a
good constructor-style recognition hypothesis, not a password or selected
downstream instruction. No oracle follows until another clue explicitly
selects subtraction/reversal or asks for the name of a young rabbit.

## Reproduction

```bash
python3 tools/gsmg/first_piece_second_matrixsumlist_audit.py --self-test
```
