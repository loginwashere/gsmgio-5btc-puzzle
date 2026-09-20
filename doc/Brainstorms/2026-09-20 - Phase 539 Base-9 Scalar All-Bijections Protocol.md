# Phase 539 — DBBI and its payload as base-9 private-key scalars under every digit bijection

Status at creation: protocol, written before any real target was scanned. No
scan of the real DBBI or payload strings against the target hashes exists yet.
Everything below is frozen by the execution lock described at the end.

## Claim and novelty

Phase 318 read the whole 91-symbol DBBI as a base-9 integer under exactly two
fixed digit maps (`a0i8`: a=0..i=8; `a1i9`: a=1..i=9) and two directions, then
checked each as a secp256k1 scalar (reduced mod the curve order) against the
prize address and the halving-recipient address. It closed only that
four-integer set. Two things follow that it did not test:

1. The digit map is a free choice: any of the 9! = 362,880 bijections of `a..i`
   onto nine distinct digit values could be the intended one.
2. DBBI's prime-host structure (Phases 525-537) separates 31 host characters
   from a 60- or 61-symbol non-host payload that no scalar test has used. The
   payload is about 190 bits, DBBI as a whole about 288 bits.

Related but different work: Phase 536 (numeric text generators, not scalars),
Phases 529-530 (payload strings as passwords), Phase 537 (payload as a
function of position), `synthesis_action_paths_audit` path D (canonical base-9
DBBI and FAED integers added mod n). None scans all digit bijections, and
none uses the payload as a scalar.

This is an exploratory hypothesis, not a creator-selected recipe. Its prior is
low: a 190-bit payload is not a natural 256-bit key, and it assumes the key is
written in `a..i` digits at all. The reason to run it is that the validator is
exact: a scalar either reproduces one of eleven known hash160s or it does not.

## Targets (three strings)

- `P83`: the 60 non-host DBBI symbols of the 83-token prime-host parse, in
  stream order.
- `P84`: the 61 non-host symbols of the 84-token parse (including the
  unhosted final `e`), in stream order.
- `DBBI`: all 91 symbols.

Payload strings come from the masks of Phase 538 (`M31`, `M30` complements)
applied to the exact repository DBBI.

## Candidate family (closed): 4,354,560 scalars

For each target: 2 directions (forward, most-significant symbol first; reversed)
x 2 digit conventions x 9! bijections `sigma` of `a..i` onto digits.

- Convention `D0`: digits `sigma(c)` in `0..8`, value `v = sum sigma(c_i) 9^(L-1-i)`.
- Convention `D1`: digits `sigma(c) + 1` in `1..9` (Phase 318's `a1i9` shape),
  value `v + (9^L - 1)/8`.

The scalar is `k = v mod n` (`n` the secp256k1 order), skipped if zero. The
payload strings are below `n` without reduction; whole DBBI is reduced. No
hash, truncation, byte reversal, other radix, non-bijective digit map, or
other packing is added.

## Exact bar

For each scalar compute the compressed and uncompressed public keys and their
hash160. **Exact hit:** either hash160 is in the target set of eleven:

- the prize address `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe` (uncompressed
  hash160) and the prize public key's compressed hash160;
- the halving-recipient address `17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa`;
- the eight EC neighbors of the prize public key (`P+G`, `P-G`, `P/2`, `2P`,
  each compressed and uncompressed), derived independently in this phase from
  the prize public key and cross-checked against the Phase 331 constants.

A hit is a candidate private key. It is never printed: records go to a
mode-0600 file under `_work/phase539/` (gitignored), and only counts enter the
committed result. If one occurs, stop and tell the user before anything else.
There is no statistical arm and no weak tier.

## Controls (run before any real target is scanned)

1. **Validator.** `k = 1` reproduces the known compressed and uncompressed
   hash160 of the generator; the prize public key's uncompressed hash160
   equals the prize address payload; the eight independently derived neighbor
   hash160s equal the Phase 331 constants.
2. **Planted recovery.** For each of the 12 target x direction x convention
   cells, choose a bijection with a fixed seed, build the scalar, put its two
   hash160s into a synthetic target set, and run the identical full 362,880
   scan. Requirement: exactly one bijection matches per cell, equal to the
   planted one, in the right encoding. Failure stops the phase.
3. **Digit arithmetic.** The Phase 318 conventions are reproduced: for the
   identity bijection, `D0` equals Phase 318's `a0i8` integer and `D1` equals its
   `a1i9` integer on the exact DBBI in both directions.

## Stop rule

Zero exact hits closes only this family: three strings, two directions, two
digit conventions, all bijections. Do not add FAED or the host string, other
radices (for example decimal), alternate packings or truncations, hashing of the
integer, non-bijective maps, or partial windows after seeing the result.

## Non-claims

Nothing here says the key is a base-9 number. A negative changes no fact about
any blob, key, or address, and does not bear on the checkerboard or Bifid
hypotheses.

## Execution lock

`--prepare` writes `tools/gsmg/phase539_base9_scalar_lock.json` pinning: this
protocol's hash, the script and test, `data.py`, the Phase 537 and 538 scripts
the masks come from, the `known_targets.rs` constants file, the three target
strings' digests, the eleven target hash160s, the candidate count, and the
results of the controls. `--run` recomputes and compares the whole lock before
scanning any real target.

## Reproduction

```bash
python3 tools/gsmg/phase539_base9_scalar_all_bijections.py --self-test
python3 tools/gsmg/phase539_base9_scalar_all_bijections.py --prepare
python3 tools/gsmg/phase539_base9_scalar_all_bijections.py --run
```
