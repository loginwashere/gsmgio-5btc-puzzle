# Phase 539 — DBBI and its payload as base-9 scalars under every digit bijection

2026-09-20. Result: **bounded negative; 0 exact hits in 4,354,560 scalars**.

## Question

Phase 318 read the whole 91-symbol DBBI as a base-9 integer under two fixed digit
maps (`a0i8`, `a1i9`) and two directions, and checked each as a secp256k1
scalar against the prize and halving addresses. It closed only those four
integers. Does any digit bijection, applied to DBBI or to its 60- or 61-symbol
non-host payload (Phases 525-537), give a scalar that matches a known target?
Exploratory, not a creator-selected recipe; its prior is low (a 190-bit payload is
not a natural 256-bit key). Protocol:
[doc/Brainstorms/2026-09-20 - Phase 539 ... Protocol.md](Brainstorms/2026-09-20%20-%20Phase%20539%20Base-9%20Scalar%20All-Bijections%20Protocol.md),
written and locked before any real target was scanned.

## Frozen family

Three strings: `P83` (60 non-host symbols, 83-token parse), `P84` (61 symbols,
84-token parse, including the unhosted final `e`), whole `DBBI`. Two directions.
Two digit conventions: `D0` digits `0..8`, `D1` digits `1..9` (Phase 318's
`a1i9` shape, value plus `(9^L-1)/8`). All 9! = 362,880 bijections of `a..i`
onto digits. Scalar `k = v mod n` (payloads are below `n`). **4,354,560
scalars.** No hashing, truncation, other radix, non-bijective map or packing.

Exact bar: compressed or uncompressed hash160 equals one of eleven targets: the
prize address and the prize public key's compressed form, the halving-recipient
address, and the eight EC neighbors of the prize public key (independently
derived; equal to the Phase 331 constants).

## Controls (before any real target was scanned)

- Validator: generator hash160s correct; the prize public key's hash160 equals
  the prize address payload; the eight derived neighbors equal the Phase 331
  constants; eleven distinct targets.
- Digit arithmetic: the identity bijection reproduces Phase 318's `a0i8` and
  `a1i9` integers in both directions.
- Planted recovery: for each of the 12 string x direction x convention cells, a
  seeded bijection's two hash160s were put in a synthetic target set and the
  identical full 362,880 scan recovered exactly the planted bijection in both
  encodings (12/12).

One pre-scan defect is disclosed: the first lock failed verification because the
target list was stored as tuples, which JSON turns into lists. The field format was
fixed and the lock regenerated before any real target was scanned.

## Result

| String | Forward D0 | Forward D1 | Reversed D0 | Reversed D1 |
|---|---:|---:|---:|---:|
| `P83` | 0 / 362,880 | 0 / 362,880 | 0 / 362,880 | 0 / 362,880 |
| `P84` | 0 / 362,880 | 0 / 362,880 | 0 / 362,880 | 0 / 362,880 |
| `DBBI` | 0 / 362,880 | 0 / 362,880 | 0 / 362,880 | 0 / 362,880 |

4,354,560 scalars, 8,709,120 hash160 comparisons against eleven targets, no
match. No match file was written. The run took 11 s on 16 cores.

## Scope and stop

Neither DBBI nor its payload, read as a base-9 number under any digit bijection,
in either direction, with digits `0..8` or `1..9`, is a private key for the prize
address, the halving address, or the prize public key's four EC neighbors. This
closes that family, not the possibility that the key is encoded some other way.
FAED, the host string, decimal readings, hashing of the integer, other
packings and partial windows were outside the family and do not become next
steps because it failed. No fact about any blob, key or address changes.

## Reproduction

```bash
python3 tools/gsmg/phase539_base9_scalar_all_bijections.py --self-test
python3 tools/gsmg/phase539_base9_scalar_all_bijections.py --run   # verifies the lock first
python3 tools/gsmg/run_frontier_tests.py --start 539 --end 539
```

Files: `tools/gsmg/phase539_base9_scalar_all_bijections.py`,
`test_phase539_base9_scalar_all_bijections.py` (8 tests),
`phase539_base9_scalar_lock.json`, `phase539_base9_scalar_result.json` (counts
only, no key material).
