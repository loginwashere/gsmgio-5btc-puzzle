# Phase 546 — selectivity curve for the BTCSEED prefix over Bifid squares

Status at creation: protocol, written before any prefix-class rate was computed for the real
FAED. Option 2 of the
[BTCSEED tail options brainstorm](2026-09-21%20-%20BTCSEED%20Tail%20Decoding%20Options%20Brainstorm.md).
Everything below is frozen by the execution lock at the end.

## Claim and novelty

Phase 425 showed that, with the target `BTCSEED` fixed in advance, the prefix is unusual under
FAED shuffles inside a 12-square, 1,536-configuration family (p = 1/10001). It did not vary the
square over a wide population while allowing any comparably notable prefix. The target was chosen
after looking, so the relevant question is about **selection**: how often does a Bifid square
decode FAED to some prefix that a reader could call meaningful?

This phase keeps FAED and the decoder fixed (whole 570-symbol block, row-column, forward) and
varies only the 25-letter square. It is a **calibration gate**, not a decoder: it asks whether
the prefix, as evidence, can separate "designed" from "picked after looking". It says nothing
about the tail.

## Populations

- **Arm A, exact.** All 9! = 362,880 squares whose first nine cells hold the FAED symbols
  `A..I` in any order, followed by `K..Z` alphabetically (`J` merged into `I`). The DBBI-keyed
  square `DBIFHCEGAKLMNOPQRSTUVWXYZ` is one of them. This is the natural family of
  keyword-derived squares whose keyword contains the nine stream symbols. Gating arm.
- **Arm B, sample.** 20,000,000 uniformly random 25-letter squares (numpy `default_rng(546)`).
  Robustness only; not gated. If its E3 rate differs from Arm A's by more than a factor of 10 the
  difference is reported, not resolved.

For each square only the first seven decoded letters matter; they depend on FAED symbols
0-3 and 285-288.

## Prefix classes (nested, frozen)

Lexicon: `/usr/share/dict/words` (resolved file hash pinned), ASCII alphabetic entries,
uppercased, without `J`.

- **E1**: prefix equals `BTCSEED`.
- **E2**: prefix is a 7-letter dictionary word.
- **E3**: E2, or a 3-letter token followed by a 4-letter dictionary word, or the reverse.
  3-letter tokens are the dictionary 3-letter words plus `BTC`.

E3 is the class that contains the observation (`BTC` + `SEED`). It is deliberately broad: it is
what a reader could call meaningful at seven letters by splitting into two words.

## Statistic and gate

`k1, k2, k3` = the number of Arm A squares whose prefix is in E1, E2, E3. Also reported: Arm B
counts with Wilson 95% intervals; the probability that at least one of `T` independent squares
lands in E3 for `T` in {12, 1,248, 10,000, 1,000,000}; the ten most frequent E3 prefixes in Arm A;
the number of distinct Arm A prefixes; the prefix of the real DBBI ordering.

Declared assumption: at most `T_max = 10,000` squares/configurations were plausibly tried by the
community and this project (12 squares and 1,536 configurations in Phase 425 alone; no source
fixes the true number). Gate on `k3`:

- **cherry_pickable**: `k3 >= 37` (rate >= 1e-4; at least one E3 prefix is expected among
  `T_max` squares). Prefix-level evidence cannot separate a designed prefix from one picked
  after looking.
- **selective**: `k3 <= 3` (rate <= 8.3e-6; at most about 0.08 E3 prefixes expected among
  `T_max` squares). The prefix stays a serious, if still unpromoted, checkpoint.
- **indeterminate**: otherwise.

Because the real ordering is in Arm A, `k1 >= 1` and `k3 >= 1` by construction.

## Controls (before the lock; none reports a real class rate)

1. **Fast vs full decode.** The vectorised prefix equals the first seven letters of the full
   Bifid decode for 400 random squares and 200 Arm A squares.
2. **Real square.** The DBBI ordering gives `BTCSEED`, matches `build_grid(DBBI[:13])`, and its full
   decode hashes to Phase 425's SHA-256.
3. **Class machinery.** `BTCSEED` is in E1 and E3 but not E2; E2 is a subset of E3; `ZZZZZZZ` is not in E3.
4. **Counting.** Toy classes made from prefixes of random squares (non-vacuous): exact Arm A
   count versus a 1,000,000-square Monte Carlo within 4 sigma, and the batch path equals a plain
   per-square path on 3,000 random squares.

## Disclosures and limits

- Class sizes are data-independent and were seen (E2 11,534; E3 6,126,148); no class rate
  for the real FAED was computed before the lock.
- E3 is broad by design: the dictionary includes proper names, and `BTC` was added because the
  observation contains it. The classification therefore measures how easily a post hoc reading
  of this prefix could arise, not how "special" the exact string is; E1 is reported as the exact
  count.
- `T_max` is an assumption, not a measurement.
- Only the first seven letters, only the community decode, only squares. A `cherry_pickable`
  result would not say `BTCSEED` is accidental, and does not change Phase 425's fixed-target
  p-value; `selective` would not promote anything. Neither says anything about the tail.

## Stop rule

One run. Do not add classes, thresholds, populations, prefix lengths, decoders or dictionaries
after seeing the result.

## Execution lock

`--prepare` runs the controls and writes `tools/gsmg/phase546_selectivity_lock.json` pinning this
protocol, the script, test, `data.py`, the Phase 386 script, the dictionary hash, class sizes and
digests, sample size, seed, thresholds and control results. `--run` verifies the lock, then
computes both arms once.

## Reproduction

```bash
python3 tools/gsmg/phase546_prefix_selectivity_curve.py --self-test
python3 tools/gsmg/phase546_prefix_selectivity_curve.py --prepare
python3 tools/gsmg/phase546_prefix_selectivity_curve.py --run
```
