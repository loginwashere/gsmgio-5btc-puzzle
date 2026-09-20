# Phase 525A - DBBI 84-token Selection-A reconstruction and novelty audit

Status: frozen oracle-free protocol. This phase reconstructs and inventories an
object; it does not submit passwords, decrypt a blob, score FAED, or promote a
community interpretation to creator-authenticated fact.

## Motivation and provenance

The community-authored *GSMG IO ATLAS*, second edition, identifies a previously
unrecorded consequence of the recovered yellow/blue-prime guide: under the
prime-host grammar, DBBI has two complete parses (83 and 84 logical tokens).
The 84-token parse has 23 prime hosts, split into 16 `b` and 7 `be` hosts. Its
host colors match two order-preserving 23-of-25 selections from the Stage-0
picture events. Selection A omits event ranks `{22,25}` and is the only one of
the two that represents source bytes 1 through 23 exactly once, with the FEFE
cell representing byte 21 instead of byte 21's ordinary endpoint.

This is community analysis, not an authenticated creator instruction. The
experiment tests its mechanical claims and records the finite object it defines.

Pinned external inputs:

- Telegram export `result.json`: SHA-256
  `e17ae0de8411ce63caf1ff77f1ffd0f111503c9b6a120fac9e7770849288e8ec`.
- `files/GSMG IO ATLAS.pdf`: SHA-256
  `b21dffa6be14661c0060e9a3d36fe6befd6e1ed9e48e1e971a5342dc9a8c9c14`.
- Canonical Stage-0 image `doc/img/gsmg_rabbit_hint.png`: SHA-256
  `5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f`.

## Frozen reconstruction

1. Enumerate every complete parse of the 91-character DBBI stream. At prime
   logical positions the token must be `b` or `be`; at non-prime positions it
   is exactly one `a`-through-`i` symbol. Consume every raw character.
2. Reconstruct the 24 ordinary colored byte-endpoint events from the canonical
   14x14 image using `first_piece_color_reconstruction.py`, then insert the
   unique FEFE cell in spiral order. Treat FEFE as blue only for matching the
   guide's binary host-color alphabet.
3. Compare every complete parse's prime-host color sequence against every
   order-preserving 23-of-25 event selection.
4. Selection A is defined mechanically as omitted event ranks `{22,25}`. Verify
   that its retained events represent source-byte ordinals 1 through 23 exactly
   once. Selection B (`{23,25}`) is retained as a negative structural control.

## Frozen representation inventory

The audit records, without asserting that any is a password:

- retained event colors and blue=1/yellow=0 bits;
- represented source bytes (the exact 23-character URL prefix);
- selected event ranks and source-byte ordinals;
- zero- and one-based spiral positions;
- one-based row sequence, column sequence, flattened row/column coordinates,
  and explicit `row,column` pairs.

For each numeric vector, the finite `matrixsumlist`-style serialization menu is
exactly: decimal sum, delimiter-free decimal list, and comma-separated decimal
list. The explicit coordinate-pair record is semicolon-separated pairs. No
case, reversal, permutation, padding, base conversion, or separator sweep is
allowed in Phase 525A.

## Novelty comparators

Exact candidate bytes are compared against:

1. the Phase-478 manifest of 1,749,878 bytes actually submitted to an oracle;
2. Phase-523's 133,657 not-all-covered slot-grammar bases, which Phase 524 later
   exhausted under the standard form expansion.

The comparison is exact byte membership. A miss does not prove that no older
phase constructed a semantically equivalent object; it establishes novelty
only against these two named, machine-readable corpora. Existing documentation
claims that the color-bit and URL-prefix families are spent; those records stay
descriptive and are not re-promoted merely because an exact formatting differs.

## Outputs and stop rule

Phase 525A writes one deterministic JSON result containing the two DBBI parses,
all picture-compatible selections, the Selection-A event table, the frozen
representations, and named-corpus membership results.

- If the mechanical Selection-A claims fail, stop and reject the Atlas result.
- If they pass but every representation is already present in a named
  comparator, close the novelty lane without an oracle phase.
- If new representations remain, stop after inventory. Any password/oracle use
  requires a separate Phase 525B protocol and execution lock that selects a
  consumer and expansion rules before decrypting anything.

## Limits

This phase does not authenticate the one-representative-per-byte criterion, show
that `matrixsumlist` consumes Selection A, explain the 61 non-prime tokens, test
the competing 83-token parse as a password source, or establish that any
serialization is meaningful. It does not touch FAED or any encrypted blob.
