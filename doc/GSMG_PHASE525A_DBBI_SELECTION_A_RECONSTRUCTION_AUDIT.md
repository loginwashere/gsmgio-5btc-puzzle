# Phase 525A - DBBI Selection-A reconstruction and novelty audit

Date: 2026-09-19  
Disposition: **mechanically reproduced; oracle-free inventory complete**

## Question

Does the Atlas's newly reported DBBI Selection A survive independent
reconstruction from this project's existing DBBI stream and canonical Stage-0
image, and does it define exact serialized objects absent from the two largest
machine-readable historical candidate corpora?

This phase does not ask whether Selection A is intended by the creator or is a
password. The motivating Atlas is unauthenticated community analysis.

## Frozen method

The protocol was written before the audit run at
`doc/Brainstorms/2026-09-19 - Phase 525 DBBI Selection A Reconstruction Protocol.md`.
The implementation:

1. exhaustively parses DBBI under the prime-host grammar;
2. reconstructs the 24 colored byte endpoints and FEFE event directly from the
   canonical 14x14 image;
3. tests every order-preserving 23-of-25 event selection against each complete
   parse's host colors;
4. verifies the Selection-A one-source-byte-per-event invariant;
5. emits a frozen 25-record representation inventory; and
6. checks exact byte membership against Phase 478's 1,749,878 submitted oracle
   materials and Phase 523's 133,657 not-all-covered bases.

No encrypted blob, FAED string, password oracle, language model, or statistical
score is imported or queried.

## Reconstructed facts

The 91 raw DBBI symbols have exactly two complete grammar parses:

| Logical length | Prime hosts | `b` | `be` | Non-prime symbols | Host colors |
|---:|---:|---:|---:|---:|---|
| 83 | 23 | 15 | 8 | 60 | `BBBBYBBBYYBBBBYBBYYBBYY` |
| 84 | 23 | 16 | 7 | 61 | `BBBBYBBBYYBBBBYBBYYBBYB` |

The picture reconstructs 25 spiral-ordered events with colors
`BBBBYBBBYYBBBBYBBYYBFYYBY`, where `F` is the FEFE cell at event rank 21,
one-based spiral position 164, source byte 21. FEFE is read as blue only for
the guide's binary color comparison.

The 83-token parse has three color-compatible omissions: `{22,24}`, `{23,24}`,
and `{24,25}`. None represents source bytes 1-23 exactly once.

The 84-token parse has exactly two color-compatible omissions:

| Selection | Omitted ranks | Distinct source bytes | Bytes 1-23 once each |
|---|---|---:|---|
| A | `{22,25}` | 23 | yes |
| B | `{23,25}` | 22 | no |

Selection A omits byte 21's ordinary endpoint (spiral position 168) and byte
24's endpoint (192), retaining the FEFE cell as byte 21's representative. Its
text projection is the exact 23-character prefix
`gsmg.io/theseedisplante`; its guide-color projection is
`BBBBYBBBYYBBBBYBBYYBBYB` (blue=1 bits
`11110111001111011001101`).

## Selection-A coordinate outputs

The strongest genuinely Selection-A-specific objects are its coordinates:

- zero-based spiral positions:
  `7,15,23,31,39,47,55,63,71,79,87,95,103,111,119,127,135,143,151,159,163,175,183`
  (sum `2181`);
- one-based spiral positions:
  `8,16,24,32,40,48,56,64,72,80,88,96,104,112,120,128,136,144,152,160,164,176,184`
  (sum `2204`);
- one-based row values sum to `172`; columns sum to `171`; the flattened
  row/column stream sums to `343`.

The result JSON preserves the complete event table and all 25 frozen
serializations, including compact and comma-list forms.

## Exact novelty result

All 25 representation bytes are absent from both named comparators:

| Comparator | Records scanned | Exact matches |
|---|---:|---:|
| Phase 478 actually-submitted oracle materials | 1,749,878 | 0 |
| Phase 523 not-all-covered bases | 133,657 | 0 |

This is a narrow machine-membership result, not a claim that all 25 ideas are
semantically new. In particular:

- the full URL, color-bit, and related 16/7 families have extensive prior
  coverage, so the 23-character truncation and 23-bit string are not promoted
  merely because their exact bytes are absent;
- the source-byte vector `1..23` is a tautological consequence of the chosen
  criterion;
- event-rank encodings mostly restate `{22,25}`;
- the **16 coordinate-derived records** (spiral, row, column, flattened
  coordinates, and explicit pairs) are the clearest new bounded family because
  their values depend specifically on Selection A, which earlier phases had not
  constructed.

## Verification

- Seven focused tests pass.
- The module self-test passes four load-bearing checks.
- Result SHA-256:
  `82a46dc6c4077ee5626d0578d465ebaf64e141d6627e94848ef34483d02e9253`.
- The exact external-input hashes match the frozen protocol.

## Interpretation

The Atlas claim is mechanically correct: Selection A is not an arithmetic or
transcription error, and it is uniquely distinguished from the other
84-token color match by the one-representative-per-source-byte criterion.
That criterion remains conditional because the creator never states it.

The phase therefore advances one object from community speculation to a
reproducible project fact while keeping the intendedness claim separate. The
finite coordinate family is suitable for a later exact-validator experiment,
but this phase does not choose an encrypted consumer or authorize password
expansion.

## Next gate

A Phase 525B protocol may take only the 16 coordinate-derived bases, apply the
project's already-established solved-boundary password forms, and test a named
consumer under an execution lock. It must first diff the expanded materials,
not just the bases, against prior submitted material. No extra reversals,
permutations, encodings, or separators are licensed by this result.

## Limits

This does not prove that Selection A is creator-intended, that
`matrixsumlist` consumes it, that DBBI's 61-symbol residue is payload, or that
any encrypted blob uses it. It does not retire Selection B or the 83-token
parse outside the frozen one-byte-representative criterion.
