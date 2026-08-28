---
type: preregistration
status: frozen
date: 2026-08-28
phase: 435
topics:
  - phase-3.2.1
  - architect
  - operator-selector
  - repeated-phrase
---

# Phase 435 — `BE REQUIRED` Operator-Selector Audit Protocol

Frozen before implementing or running the Phase 435 audit.

## Question

Does the twice-occurring phrase `BE REQUIRED` in the Phase 3.2.1 Architect
monologue select a new, source-grounded operation, or is it only a distinctive
repetition created by one inherited Matrix sentence and one creator-added
sentence?

This is a textual-structure and provenance audit. It does not generate password
material, query any encrypted blob, inspect the live Phase 430 leader, or use
the GPU.

## Frozen sources

1. Phase 3.2.1 is freshly derived from the authenticated Phase 3.2 AES
   plaintext through the repository's CP1141/Beaufort path.
2. Word boundaries come from the README transcription only after its letters
   are asserted byte-for-byte equivalent to the freshly derived connected
   plaintext. The cryptographic output itself authenticates letters and order,
   not spaces.
3. The Matrix film wording is checked against
   `wordlists/matrix/the-matrix-reloaded-2003.en.srt`.
4. Existing registered `{B,E}` mechanisms are read from repository code and
   findings; they are comparators, not candidate generators.

## Frozen measurements

The audit will report and assert:

- zero- and one-based connected-letter offsets of every `BEREQUIRED`;
- README word indices of every whole-word `BE REQUIRED`;
- counts of whole-word `BE`, raw connected-text `BE`, and `BE REQUIRED`;
- every repeated README word bigram and every repeated word trigram;
- whether `BE REQUIRED` is the only repeated content-bearing bigram whose two
  occurrences divide into one Matrix-inherited occurrence and one
  creator-added occurrence;
- provenance of each occurrence: the first belongs to the film-derived
  `AFTER WHICH YOU WILL BE REQUIRED TO SELECT` skeleton; the second belongs to
  creator-added `BRUTE FORCING MIGHT BE REQUIRED`, which has no film match;
- a comparison with the four already registered nearby mechanisms:
  Phase 3.2.2 escapes `(1,4)`, DBBI `B/BE` tokenization, split-final-`BE`, and
  Architect `BUT/HYE` choice extraction;
- whether any registered unresolved consumer independently requires exactly
  two `BE` markers.

## Frozen decision rule

Promote `BE REQUIRED` as a selector only if all of the following hold:

1. the repetition is exact under the README segmentation and its connected
   letters are authenticated by fresh derivation;
2. the two occurrences define an unambiguous operation without choosing a new
   source string, boundary convention, direction, or index base;
3. that operation maps to a registered unresolved consumer which independently
   requires two markers or two rails; and
4. the resulting operation is not identical to a mechanism already covered by
   Phases 33, 61, 70, or 270.

If only item 1 is satisfied, classify the phrase as a real textual feature but
not an actionable selector. If items 1 and 2 are satisfied but no consumer is
independently fixed, record an underdetermined operator and stop.

## Explicit exclusions

- no blob/password oracle;
- no passphrase, hash, KDF, cipher, or permutation generation;
- no extraction of arbitrary text between the two occurrences;
- no treating README whitespace as cryptographically authenticated;
- no retrofitting `2 BE` to the split-final-`BE` guide merely because both use
  the letters B and E;
- no source-bound `AND/OR` blue/yellow string experiment unless this audit or
  the separate Phase 434 coverage matrix independently fixes its source,
  sequence, direction, and boundary.

## Stop condition

The phase ends after emitting the structural report and applying the frozen
decision rule. Any promoted consumer would require a separate preregistration
before candidate generation. A non-promotion closes this exact doubled-phrase
reading; it does not prove that the wider Architect passage has no operational
content.
