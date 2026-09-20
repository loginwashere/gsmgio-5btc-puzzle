# Phase 536 — prime scaffold around substituted numeric text

Status at creation: protocol, written before candidate outputs are inspected.

## Claim and novelty

DBBI may be constructed by inserting its observed prime hosts into a numeric
encoding of a passage already available in the closed corpus. This is an
exploratory hypothesis, not a creator-selected operation. Phase 318 tested the
whole raw stream as a base-9 integer; Phases 529–530 tested residue strings as
passwords. Neither tests the exact encoding-and-reinsertion generator below.

The six-document corpus recipe is reused from Phase 482A. Add three explicit
solved strings: Phase 3.2.2's 91-letter answer, `gsmg.io/theseedisplanted`, and
the solved Stage-1 flower credential. Preserve document boundaries. Normalize
each to ASCII letters only, once uppercase and once lowercase, without J/I
merging. Frozen extracted-source hashes and candidate counts are recorded in an
execution lock before the real residue matcher is run. The corpus includes
encoded sub-blocks inherited from earlier solved plaintext and is not all prose.

## Closed generators

For every contiguous 16–40-character normalized source window:

1. **R9**: ASCII bytes → unsigned big-endian integer → minimal ordinary base 9.
2. **D10**: same byte integer → minimal decimal digits (nearby page precedent).
3. **B9**: each ASCII byte → exactly three base-9 digits, concatenate.

Allow one fixed injective digit-to-`a..i` relabeling per complete window. This
allows all 9! maps for R9/B9 and all choices of nine decimal digits for D10,
without brute force: exact equality patterns determine the map or reject it.
All nine residue symbols occur, so eligible encodings must use exactly nine
distinct digits. No varying mappings, reverse order, offsets, cipher layers,
hashes, external corpus expansion, or anagrams.

Two targets only: all 60 non-host symbols in the 83-token parse; all 61 non-host
symbols including the final `e` in the 84-token parse. Never drop the 84th token.
Digit-string lengths must be exact. Use monotone minimum/maximum ASCII bounds
to exclude impossible window lengths before enumeration, while retaining every
length whose bounds overlap the target length.

## Acceptance and stop rule

An exact hit must match every symbol under one bijection, decode to the entire
source window, and reproduce all 91 raw DBBI symbols when the frozen hosts are
reinserted. Report every matching location and every successful model, not just
a preferred one. A hit is a candidate construction, not a solved password or
proof of intention. Reinsertion is a consistency check, not independent proof.

Zero full matches rejects only this finite generator/corpus/normalization
family. Partial words, high language scores, and near matches are not retained.
Stop on completion; do not query encrypted blobs or enlarge the family after a
negative. If a candidate exists, preserve it for a separately specified
downstream validation. Stop without testing real residues if controls fail.

## Planted recovery gate

For every model × case × target-length cell whose numeric bounds allow a
window, generate one fixed-seed synthetic letters-only message producing the
required digit length and nine distinct digits (at most 20,000 attempts per
cell). Rename digits using a deterministic shuffled alphabet, insert the real
23-host profile for that logical length, then use the same full window matcher
on a synthetic corpus containing the message with prefix/suffix distractors.
Require recovery of the exact source window, mapping, and full generated raw
stream for every eligible cell. Impossible cells are reported, not resampled.
Test one-symbol pattern corruption, digit aliasing, and incomplete tail rejection.

These are exact-algorithm completeness checks, not statistical estimates of
power for unknown English or noisy encodings. No language-scoring/null threshold
is needed for this equality test; it makes no calibrated significance claim.

## Execution record

Lock script, protocol, extraction dependencies, raw source files, target hashes,
normalized corpus hashes, candidate counts, and successful planted gate before
the real match. Recompute and compare the lock at execution. Do not modify old
phase scripts or locks to make this run reproducible.
