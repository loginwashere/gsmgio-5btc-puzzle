# GSMG First-Piece Prime-Sum Verification

**Date:** 2026-08-09  
**Status:** `400/401/73` independently reconstructed; uniform FE composition verified but not statistically independent.

## Exact definition of the prime walk

The `400/401/73` values do not come from prime-valued token counts or from
interpreting color values as primes. The frozen construction is:

1. reconstruct the 24 yellow/blue LSB endpoints from the authenticated rabbit
   image;
2. insert the unique FEFE cell at its real spiral position;
3. sort all 25 events by zero-based spiral position;
4. assign the first 25 sequential primes by event ordinal;
5. under the sourced community grammar, blue and FEFE require one `b` symbol,
   while yellow requires the two-symbol token `be`;
6. place each token at `prime + number of prior yellow events` in DBBI;
7. keep the complete prefix that fits the 91-symbol DBBI stream.

`tools/gsmg/first_piece_prime_sum_reconstruction.py` implements this without
importing the existing Flo/Denis or color-prime sum audits.

## Reconstructed event boundary

The authenticated spatial event sequence is:

```text
BBBBYBBBYYBBBBYBBYYBFYYBY
```

Events 1 through 23 fit and match the required DBBI `b`/`be` tokens. Event 23
occupies positions 90–91. Event 24 begins at position 97, outside DBBI.
Therefore the 23-event cutoff is supplied by the independently fixed DBBI
boundary, not chosen after observing the sums.

The same cutoff would hold for a hypothetical consumer length from 91 through
96; this is a boundary interval, not a single-pixel numerical coincidence.

## Exact lists and sums

```text
Blue events (14):
2, 3, 5, 7, 13, 17, 19, 31, 37, 41, 43, 53, 59, 71
sum = 401

Yellow events (8):
11, 23, 29, 47, 61, 67, 79, 83
sum = 400

FEFE event (1):
73
sum = 73
```

FEFE is event 21, so its assigned value is mechanically the 21st prime, 73.
Across every prefix of the 25-event walk, prefix 23 is the only one whose
blue/yellow sum difference is at most one.

Including all 25 events changes the sums to:

```text
Blue = 490
Yellow = 497
FEFE = 73
```

Folding FEFE into blue instead of retaining its real third color changes the
fitted split to `474/400`, so keeping FEFE distinct is load-bearing.

## Fixed-profile calibration

Keep the first 23 primes and FEFE at its authenticated event 21, then shuffle
the observed eight yellow and fourteen blue labels over the other 22 primes.
Exactly 813 of `C(22,8)=319,770` assignments have `|blue-yellow| <= 1`:

```text
813 / 319770 = 271 / 106590 ~= 0.002542452
```

This reproduces the earlier calibration. It is descriptive because the
balance was noticed after the walk was reconstructed, not preregistered as a
target statistic.

## Selector-free FE-mask composition

Phase 195 verifies that repeated `FE` is a bytewise LSB-clearing mask. Apply
that same operation to every member of the list, selecting no value or byte:

```text
401 = 0x0191  AND 0xFEFE = 0x0090 = 144
400 = 0x0190  AND 0xFEFE = 0x0090 = 144
 73 = 0x0049  AND 0xFEFE = 0x0048 =  72
```

Thus:

```text
401 / 400 / 73
      FE mask
144 / 144 / 72
```

The two color rails become equal, and the exceptional FEFE channel becomes
exactly half of either rail. The output is invariant under:

- minimal-width versus fixed two- or three-byte encoding;
- big-endian versus little-endian byte order.

Clearing only the integer's single terminal bit, rather than applying FE to
every byte, gives the control output `400/400/72`. Therefore `144/144/72`
specifically uses the authenticated repeated-byte semantics of FEFEFE.

## Composition calibration

With FEFE fixed at prime 73, the uniform-mask relation holds for exactly the
same 813 color assignments that produce the `400/401` near-balance:

```text
masked blue = masked yellow = 2 x masked FEFE
```

Consequently `144/144/72` adds **no independent statistical support** beyond
the already-observed balance. It is a deterministic normalization of that
same structure.

As a descriptive expanded family, let FEFE occupy any of the 23 prime
positions and preserve the 14/8/1 event profile. Only FEFE at prime 73 admits
the relation; 813 of `23*C(22,8)=7,354,710` assignments succeed. This is not
the primary calibration because FEFE's position was independently fixed by
the image and should not be treated as freely selected.

## Verdict

Promote these facts:

1. `400/401/73` is accurately transcribed and independently reproducible.
2. The cutoff comes from DBBI exhaustion, not from selecting a balanced
   prefix.
3. The result depends on the sourced successive-prime `b`/`be` grammar and on
   retaining FEFE as a separate event type.
4. Uniform FE masking produces `144/144/72` without a byte/value selector.
5. The composition is encoding-robust but statistically equivalent to the
   original `400/401` balance when conditioned on the fixed FE event.

Do not promote `144/144/72` as a password or as a second confirmation. Its
best current interpretation is a mechanically valid normalization: FE makes
the two color halves equal and leaves its own channel at half their value.

## Reproduction

```bash
python3 tools/gsmg/first_piece_prime_sum_reconstruction.py --self-test
python3 tools/gsmg/prime_sum_fefe_mask_composition_audit.py --self-test
```
