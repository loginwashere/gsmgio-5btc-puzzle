# Macro-tail title-insertion audit

Phase 169 observed that inserting `T` after `Sal` changes `SalPhaseIon` into
`SaltPhaseIon`, naturally read as `Salt | Phase | Ion`. This audit asks whether
the creator's literal macro tail uniquely supplies that edit.

It does not. The reversed binary decodes in lowercase, including
`atruegiveaway`; the capital `T` used in the earlier explanation was editorial.
The bounded source-neutral family is therefore every distinct letter of
`true` inserted at every one of the twelve title positions: 48 candidates.

Against the frozen 104,334-line system dictionary, six candidates have exact
three-word segmentations:

```text
t at 3 -> salt | phase  | ion
r at 5 -> sal  | phrase | ion
r at 9 -> sal  | phase  | iron
u at 2 -> saul | phase  | ion
e at 1 -> seal | phase  | ion
e at 3 -> sale | phase  | ion
```

Even restricting insertion to the original `Sal | Phase` CamelCase boundary
does not make the operation unique: both `Salt | Phase | Ion` and
`Sale | Phase | Ion` survive. Selecting the first letter of `true` would fix
`t`, but the macro does not say “initial,” and using that convention after the
Phase-217 circular-initials correction would require explicit source support.

Salt nevertheless has stronger independent recognition than the five rivals:
the three authenticated ciphertext envelopes all decode from their visible
Base64 prefix to OpenSSL `Salted__` plus an eight-byte salt; quarantined
URLBLOB has the same envelope form. Thus the title reading is
not random noise; it is a bounded, independently resonant recognition found
within a six-member family. But recognition does not specify what the salt
does. Phases 169–175 already closed literal salt passwords/keys, simple XOR,
salt-derived selectors, guide-strip consumers, and adjacent fixed structural
families.

Verdict: retain `Salt | Phase | Ion` as a strong recognition clue, but
downgrade “the macro gives T” from an exact instruction to a post-enumeration
selection. It cannot bind FAED, DBBI, or a blob decoder without a new rule that
selects both the `t`/position and a concrete salt consumer.
