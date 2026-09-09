# Phase 482A — FAED plaintext frequency-signature audit

## Question

Is FAED's 436-token {g,i} plaintext a verbatim passage in the project's
closed local text corpus?

Under Phase 477A Model A, the checkerboard only renames plaintext symbols and
the transposition only reorders them. Both preserve the complete sorted
frequency vector. This supplies a necessary test that does not require the
unknown checkerboard, width, direction or column order.

The frozen protocol is
doc/Brainstorms/2026-09-06 - Phase 482A FAED Plaintext Frequency Signature Protocol.md.

## Frozen target

FAED segmented under ordered escapes {g,i} into 436 tokens touching all 25
code types. Its descending count signature was:

    54,45,45,42,40,38,38,21,11,10,10,10,9,8,8,7,6,5,5,5,5,4,4,4,2

Only exact equality of all 25 counts could promote a passage. Near matches
were neither retained nor inspected.

## Closed corpus

Six logical documents were frozen and kept separate:

- solved Phase-2 and Phase-3 plaintexts, freshly decrypted from the pinned
  authenticated Wayback artifact;
- solved Phase-3.2 plaintext up to the P32 encrypted envelope;
- the independently reproduced Phase-3.2.1 Architect answer;
- the locally stored Matrix Architect screenplay scene;
- the existing local Cosmic Duality transcription with Phase 477A's
  prose-only section filter.

Telegram, project analysis prose, password dictionaries, generic wordlists and
new OCR were excluded. The unresolved ciphertext strings were not admitted as
plaintext. The execution lock pinned every extraction dependency and each
normalized document's length and SHA-256.

Two lanes were searched: uppercase letters with classical J→I, and raw
uppercase A–Z where a matching window must naturally contain exactly 25
positive letter classes. Windows were exactly 436 normalized symbols and
could not cross source boundaries.

## Controls and lock

The implementation asserted the FAED geometry and signature, reproduced all
six sources deterministically, compared rolling counts with brute-force counts
at the first/middle/last windows, demonstrated invariance under a deterministic
relabeling and permutation, and distinguished the two alphabet lanes on a
J-bearing fixture.

The execution-lock SHA-256 is
0fc4d04c6d81e19f01bc2f5c477cb2813e24864f889fa59e978c91779b658417.

## Result

    logical documents:                  6
    normalization lanes:                2
    windows per lane:              65,343
    total source/lane windows:     130,686
    exact match locations:              0
    unique matching passages:           0
    decision: bounded_negative_no_exact_passage

The largest within-source frequency-signature multiplicity was 11, in the
book corpus. No source/lane contained FAED's exact signature. Because there
was no candidate passage, the separately planned Phase 482B exact
board/transposition reconstruction did not run.

The fail-closed verifier checked all locked hashes and reproduced the complete
scan. Result SHA-256:
4297cde13ea3fb02bb9c8617c7d7b312ac6a6784729e68bf17f53183b27e6834.
All five Phase-482A tests passed.

## Disposition

Bounded negative for FAED {g,i} as a monoalphabetically renamed and
transposed verbatim 436-symbol passage from these six sources under the two
frozen alphabet conventions.

This does not reject Model A for newly composed plaintext or material outside
the corpus. It also leaves spaces/punctuation as encoded symbols, other
alphabet merges, spelling changes, non-English plaintext and Model B raw-digit
transposition outside the conclusion.

## Artifacts

- frozen protocol and phase482a_execution_lock.json;
- phase482a_faed_frequency_signature_audit.py;
- phase482a_result.json;
- fail-closed verifier and verification record;
- two unittest modules.
